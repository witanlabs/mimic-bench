#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageCms
from scipy.ndimage import gaussian_filter

import oracle_task
from shared_oracle_runtime import expected_outputs, query_budget


ACCURACY_THRESHOLD = float(getattr(oracle_task, "ACCURACY_THRESHOLD", 0.99))
SCRUBBED_ENV_KEYS = {"ORACLE_URL", "WITAN_API_KEY", "WITAN_API_URL"}


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def count_queries(path: Path) -> int | None:
    if not path.exists():
        return None
    return sum(1 for line in path.read_text().splitlines() if line.strip())


def extract_submission(submission_path: Path, destination: Path) -> None:
    if not submission_path.exists():
        raise FileNotFoundError(f"missing submission artifact: {submission_path}")
    with tarfile.open(submission_path, "r:gz") as tar:
        def is_safe(member):
            target = (destination / member.name).resolve()
            return str(target).startswith(str(destination.resolve()))

        for member in tar.getmembers():
            if not is_safe(member):
                raise ValueError(f"unsafe tar path: {member.name}")
        tar.extractall(destination, filter="data")


def scrubbed_solution_env(solution_dir: Path) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in SCRUBBED_ENV_KEYS and not key.startswith("WITAN_")
    }
    path_parts = [
        str(solution_dir / "node_modules" / ".bin"),
        str(solution_dir / ".venv" / "bin"),
        env.get("PATH", ""),
    ]
    env["PATH"] = ":".join(part for part in path_parts if part)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_dependency_command(command: list[str], solution_dir: Path) -> tuple[bool, dict[str, Any], dict[str, Any]]:
    result = subprocess.run(
        command,
        cwd=solution_dir,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
        env=scrubbed_solution_env(solution_dir),
    )
    if result.returncode == 0:
        return True, {}, {}
    return False, {
        "dependency_failure": 1,
        "dependency_manager": command[0],
        "returncode": result.returncode,
    }, {
        "dependency_command": command,
        "dependency_stdout": result.stdout[-4000:],
        "dependency_stderr": result.stderr[-4000:],
    }


def install_solution_dependencies(solution_dir: Path) -> tuple[bool, dict[str, Any], dict[str, Any]]:
    if (solution_dir / "package.json").exists():
        npm_command = ["npm", "ci"] if (solution_dir / "package-lock.json").exists() else ["npm", "install"]
        ok, meta, details = run_dependency_command(npm_command, solution_dir)
        if not ok:
            return ok, meta, details
    if (solution_dir / "pyproject.toml").exists():
        uv_command = ["uv", "sync", "--frozen"] if (solution_dir / "uv.lock").exists() else ["uv", "sync"]
        ok, meta, details = run_dependency_command(uv_command, solution_dir)
        if not ok:
            return ok, meta, details
    return True, {}, {}


def run_solution(solution_path: Path, inputs: list[dict[str, Any]]) -> tuple[list[Any] | None, dict[str, Any], dict[str, Any]]:
    stdin = "".join(json.dumps(case, sort_keys=True) + "\n" for case in inputs)
    result = subprocess.run(
        [str(solution_path)],
        cwd=solution_path.parent,
        input=stdin,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
        env=scrubbed_solution_env(solution_path.parent),
    )
    if result.returncode != 0:
        return None, {"runtime_failure": 1, "returncode": result.returncode}, {"stderr": result.stderr[-4000:]}

    outputs = []
    malformed = 0
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        try:
            outputs.append(json.loads(line))
        except json.JSONDecodeError:
            malformed += 1

    if len(outputs) != len(inputs):
        malformed += abs(len(outputs) - len(inputs))

    return outputs, {"runtime_failure": 0, "malformed_outputs": malformed}, {}


def load_rgb_from_response(response: Any) -> np.ndarray:
    if not isinstance(response, dict):
        raise ValueError("output_not_object")
    if response.get("contentType") != "image/png":
        raise ValueError("content_type_not_png")
    data = response.get("data")
    if not isinstance(data, str):
        raise ValueError("missing_data")
    image_bytes = base64.b64decode(data)
    with Image.open(BytesIO(image_bytes)) as image:
        expected_width = response.get("pixelWidth")
        expected_height = response.get("pixelHeight")
        if image.size != (expected_width, expected_height):
            raise ValueError("declared_dimensions_do_not_match_png")
        icc_profile = image.info.get("icc_profile")
        if icc_profile:
            try:
                source_profile = ImageCms.ImageCmsProfile(BytesIO(icc_profile))
                srgb_profile = ImageCms.createProfile("sRGB")
                image = ImageCms.profileToProfile(image, source_profile, srgb_profile, outputMode="RGBA")
            except Exception:
                image = image.convert("RGBA")
        else:
            image = image.convert("RGBA")
        rgba = np.asarray(image, dtype=np.float64)
    alpha = rgba[..., 3:4] / 255.0
    return rgba[..., :3] * alpha + 255.0 * (1.0 - alpha)


def downsample2(x: np.ndarray) -> np.ndarray:
    h = x.shape[0] - (x.shape[0] % 2)
    w = x.shape[1] - (x.shape[1] % 2)
    if h < 2 or w < 2:
        return x
    x = x[:h, :w]
    return (x[0::2, 0::2] + x[1::2, 0::2] + x[0::2, 1::2] + x[1::2, 1::2]) / 4.0


def msssim_channel(a: np.ndarray, b: np.ndarray) -> float:
    weights = np.array([0.0448, 0.2856, 0.3001, 0.2363, 0.1333], dtype=np.float64)
    k1 = 0.01
    k2 = 0.03
    data_range = 255.0
    c1 = (k1 * data_range) ** 2
    c2 = (k2 * data_range) ** 2
    mcs = []
    x = a
    y = b
    for scale in range(len(weights)):
        ux = gaussian_filter(x, sigma=1.5, mode="reflect")
        uy = gaussian_filter(y, sigma=1.5, mode="reflect")
        ux2 = ux * ux
        uy2 = uy * uy
        uxy = ux * uy
        vx = gaussian_filter(x * x, sigma=1.5, mode="reflect") - ux2
        vy = gaussian_filter(y * y, sigma=1.5, mode="reflect") - uy2
        vxy = gaussian_filter(x * y, sigma=1.5, mode="reflect") - uxy
        luminance = (2 * uxy + c1) / (ux2 + uy2 + c1)
        contrast_structure = (2 * vxy + c2) / (vx + vy + c2)
        ssim = float(np.mean(luminance * contrast_structure))
        cs = float(np.mean(contrast_structure))
        if scale == len(weights) - 1:
            ssim = max(0.0, min(1.0, ssim))
            return float(np.prod(np.power(np.maximum(mcs, 0.0), weights[:-1])) * (ssim ** weights[-1]))
        mcs.append(max(0.0, min(1.0, cs)))
        x = downsample2(x)
        y = downsample2(y)
    raise AssertionError("unreachable")


def ms_ssim(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        raise ValueError(f"dimension mismatch: oracle={a.shape}, render={b.shape}")
    scores = [msssim_channel(a[..., channel], b[..., channel]) for channel in range(3)]
    return float(sum(scores) / len(scores))


def blank_baseline_score(expected_rgb: np.ndarray) -> float:
    return ms_ssim(expected_rgb, np.full_like(expected_rgb, 255.0))


def corrected_score(raw_score: float, blank_score: float) -> float:
    if blank_score >= 1.0:
        return 0.0
    return (raw_score - blank_score) / (1.0 - blank_score)


def score_output(expected: dict[str, Any], actual: Any) -> tuple[dict[str, float], str | None]:
    try:
        expected_rgb = load_rgb_from_response(expected)
        actual_rgb = load_rgb_from_response(actual)
        if actual.get("pixelWidth") != expected.get("pixelWidth") or actual.get("pixelHeight") != expected.get("pixelHeight"):
            raise ValueError("dimension_mismatch")
        raw_score = ms_ssim(expected_rgb, actual_rgb)
        blank_score = blank_baseline_score(expected_rgb)
        corrected = corrected_score(raw_score, blank_score)
        return {
            "ms_ssim": raw_score,
            "blank_ms_ssim": blank_score,
            "corrected_ms_ssim": corrected,
            "reward": max(0.0, min(1.0, corrected)),
        }, None
    except Exception as exc:
        return {
            "ms_ssim": 0.0,
            "blank_ms_ssim": 0.0,
            "corrected_ms_ssim": 0.0,
            "reward": 0.0,
        }, f"{type(exc).__name__}: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, default=Path("/logs/artifacts/submission.tgz"))
    parser.add_argument("--eval-inputs", type=Path, default=Path("/tests/eval_inputs.jsonl"))
    parser.add_argument("--query-log", type=Path, default=Path("/var/log/oracle/queries.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("/logs/verifier/reward.json"))
    args = parser.parse_args()

    cases = load_cases(args.eval_inputs)
    budget = query_budget()

    if not args.submission.exists():
        reward = {
            "reward": 0.0,
            "accuracy": 0,
            "missing_submission": 1,
            "budget": budget,
        }
        details = {"family": oracle_task.TASK_FAMILY}
    else:
        expected = expected_outputs(cases)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            extract_submission(args.submission, tmp_path)
            submitted_solution_dir = tmp_path / "solution"
            submitted_solution_path = submitted_solution_dir / "solve"
            if not submitted_solution_path.exists():
                reward = {
                    "reward": 0.0,
                    "accuracy": 0,
                    "missing_solution": 1,
                    "budget": budget,
                }
                details = {"family": oracle_task.TASK_FAMILY}
            else:
                submitted_solution_path.chmod(submitted_solution_path.stat().st_mode | 0o111)
                app_root = Path("/app")
                if app_root.exists():
                    solution_dir = app_root / "solution"
                    if solution_dir.exists():
                        shutil.rmtree(solution_dir)
                    shutil.copytree(submitted_solution_dir, solution_dir)
                else:
                    solution_dir = submitted_solution_dir
                solution_path = solution_dir / "solve"
                ok, install_meta, install_details = install_solution_dependencies(solution_dir)
                if not ok:
                    reward = {"reward": 0.0, "accuracy": 0, "budget": budget, **install_meta}
                    details = {"family": oracle_task.TASK_FAMILY, **install_details}
                    outputs = None
                else:
                    solution_path.chmod(solution_path.stat().st_mode | 0o111)
                    outputs, run_meta, run_details = run_solution(solution_path, cases)
                if outputs is None:
                    if ok:
                        reward = {"reward": 0.0, "accuracy": 0, "budget": budget, **run_meta}
                        details = {"family": oracle_task.TASK_FAMILY, **run_details}
                else:
                    per_case = []
                    for index, expected_output in enumerate(expected):
                        actual_output = outputs[index] if index < len(outputs) else None
                        scores, error = score_output(expected_output, actual_output)
                        per_case.append({
                            "case_index": index,
                            **scores,
                            "error": error,
                        })
                    malformed = run_meta.get("malformed_outputs", 0)
                    reward_value = sum(item["reward"] for item in per_case) / len(per_case) if per_case else 0.0
                    if malformed:
                        reward_value = max(0.0, reward_value - min(1.0, malformed / max(1, len(cases))))
                    passed_cases = sum(1 for item in per_case if item["reward"] >= ACCURACY_THRESHOLD)
                    accuracy = int(passed_cases == len(per_case) and malformed == 0)
                    reward = {
                        "reward": reward_value,
                        "accuracy": accuracy,
                        "budget": budget,
                        "eval_cases": len(cases),
                        "passed_cases": passed_cases,
                        "accuracy_threshold": ACCURACY_THRESHOLD,
                        **run_meta,
                    }
                    queries_used = count_queries(args.query_log)
                    if queries_used is not None:
                        reward["queries_used"] = queries_used
                    details = {"family": oracle_task.TASK_FAMILY, "cases": per_case, **run_details}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reward, indent=2, sort_keys=True) + "\n")
    args.output.with_name("reward-details.json").write_text(json.dumps(details, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
