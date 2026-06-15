#!/usr/bin/env python3

import argparse
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

import oracle_task
from shared_oracle_runtime import expected_outputs


def load_cases(path):
    cases = []
    for line in Path(path).read_text().splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def count_queries(path):
    query_log = Path(path)
    if not query_log.exists():
        return None
    return sum(1 for line in query_log.read_text().splitlines() if line.strip())


def extract_submission(submission_path, destination):
    submission = Path(submission_path)
    if not submission.exists():
        raise FileNotFoundError(f"missing submission artifact: {submission}")
    with tarfile.open(submission, "r:gz") as tar:
        def is_safe(member):
            target = (destination / member.name).resolve()
            return str(target).startswith(str(destination.resolve()))

        for member in tar.getmembers():
            if not is_safe(member):
                raise ValueError(f"unsafe tar path: {member.name}")
        tar.extractall(destination, filter="data")


def run_solution(solution_path, inputs):
    stdin = "".join(json.dumps({"args": case["args"]}) + "\n" for case in inputs)
    result = subprocess.run(
        [str(solution_path)],
        input=stdin,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    if result.returncode != 0:
        return None, {
            "runtime_failure": 1,
            "stderr": result.stderr[-4000:],
            "returncode": result.returncode,
        }

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

    return outputs, {"runtime_failure": 0, "malformed_outputs": malformed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, default=Path("/logs/artifacts/submission.tgz"))
    parser.add_argument("--eval-inputs", type=Path, default=Path("/tests/eval_inputs.jsonl"))
    parser.add_argument("--query-log", type=Path, default=Path("/var/log/oracle/queries.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("/logs/verifier/reward.json"))
    args = parser.parse_args()

    cases = load_cases(args.eval_inputs)

    if not args.submission.exists():
        reward = {
            "reward": 0.0,
            "accuracy": 0.0,
            "missing_submission": 1,
            "budget": oracle_task.QUERY_BUDGET,
        }
        details = {"family": oracle_task.TASK_FAMILY}
    else:
        expected = expected_outputs(cases)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            extract_submission(args.submission, tmp_path)
            solution_path = tmp_path / "solution" / "solve"
            if not solution_path.exists():
                reward = {
                    "reward": 0.0,
                    "accuracy": 0.0,
                    "missing_solution": 1,
                    "budget": oracle_task.QUERY_BUDGET,
                }
                details = {"family": oracle_task.TASK_FAMILY}
            else:
                solution_path.chmod(solution_path.stat().st_mode | 0o111)
                app_root = Path("/app")
                if app_root.exists():
                    shutil.copytree(tmp_path / "solution", app_root / "solution", dirs_exist_ok=True)
                outputs, run_meta = run_solution(solution_path, cases)
                if outputs is None:
                    reward = {
                        "reward": 0.0,
                        "accuracy": 0.0,
                        "budget": oracle_task.QUERY_BUDGET,
                        **run_meta,
                    }
                    details = {"family": oracle_task.TASK_FAMILY}
                else:
                    match_count = sum(
                        1
                        for index, expected_output in enumerate(expected)
                        if index < len(outputs) and outputs[index] == expected_output
                    )
                    malformed = run_meta.get("malformed_outputs", 0)
                    penalty = min(1.0, malformed / max(1, len(cases)))
                    accuracy = match_count / len(expected) if expected else 0.0
                    reward_value = max(0.0, accuracy - penalty)
                    reward = {
                        "reward": reward_value,
                        "budget": oracle_task.QUERY_BUDGET,
                        "eval_cases": len(cases),
                        "match_count": match_count,
                        "accuracy": accuracy,
                        **run_meta,
                    }
                    queries_used = count_queries(args.query_log)
                    if queries_used is not None:
                        reward["queries_used"] = queries_used
                    details = {"family": oracle_task.TASK_FAMILY}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reward, indent=2, sort_keys=True) + "\n")
    details_output = args.output.with_name("reward-details.json")
    details_output.write_text(json.dumps(details, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
