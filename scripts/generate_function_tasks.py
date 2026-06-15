#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = Path(
    REPO_ROOT / "source-corpus" / "function-test-args-literalized-augmented-v3"
)
DEFAULT_TASKS_DIR = REPO_ROOT / "tasks"
DEFAULT_TEMPLATE_TASK = REPO_ROOT / "template-task"
DEFAULT_QUERY_BUDGET = 256
EXCLUDED_FUNCTIONS = {"RAND", "RANDARRAY", "RANDBETWEEN", "NOW", "TODAY"}
CSHARP_MARKER_RE = re.compile(r"ToInvariantString|\.ToString\(|nameof\(|\$\"")
BACKEND_CRASH_ARGS = {
    ("CONVERT", ("1", '"Ym2"', '"m2"')),
    ("CONVERT", ("1", '"Zm2"', '"m2"')),
    ("CONVERT", ("1", '"Em2"', '"m2"')),
    ("CONVERT", ("1", '"Pm2"', '"m2"')),
    ("CONVERT", ("1", '"Ym3"', '"m3"')),
    ("CONVERT", ("1", '"Zm3"', '"m3"')),
    ("CONVERT", ("1", '"Em3"', '"m3"')),
    ("CONVERT", ("1", '"Pm3"', '"m3"')),
    ("CONVERT", ("1", '"Tm3"', '"m3"')),
}


def function_slug(function_name: str) -> str:
    slug = function_name.lower().replace(".", "-")
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug


def excluded_task_dirs(tasks_dir: Path) -> list[Path]:
    paths = []
    for function_name in EXCLUDED_FUNCTIONS:
        paths.extend(tasks_dir.glob(f"fn-{function_slug(function_name)}*"))
    return sorted(paths)


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def has_unsupported_csharp_marker(row: dict[str, Any]) -> bool:
    parts = [
        str(row.get("formula", "")),
        str(row.get("call", "")),
        " ".join(str(arg) for arg in row.get("args") or []),
    ]
    return bool(CSHARP_MARKER_RE.search(" ".join(parts)))


def is_backend_crash_case(row: dict[str, Any]) -> bool:
    return (row.get("function"), tuple(row.get("args") or [])) in BACKEND_CRASH_ARGS


def supported_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, int]:
    kept = []
    dropped_csharp = 0
    dropped_backend = 0
    for row in rows:
        if has_unsupported_csharp_marker(row):
            dropped_csharp += 1
        elif is_backend_crash_case(row):
            dropped_backend += 1
        else:
            kept.append(row)
    return kept, dropped_csharp, dropped_backend


def copy_static_files(template_task: Path, task_dir: Path) -> None:
    files = [
        "environment/Dockerfile",
        "environment/docker-compose.yaml",
        "environment/oracle-service/Dockerfile",
        "tests/Dockerfile",
        "tests/test.sh",
    ]
    for relative in files:
        source = template_task / relative
        destination = task_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def copy_shared_files(template_task: Path, task_dir: Path) -> None:
    for source in sorted(template_task.rglob("shared_*")):
        if not source.is_file():
            continue
        destination = task_dir / source.relative_to(template_task)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def render_instruction(function_name: str, arities: list[int]) -> str:
    arity_text = ", ".join(str(arity) for arity in arities)
    return f"""You need to infer and implement the Excel-compatible behavior of `{function_name}`.

The oracle evaluates `={function_name}(...)` with the arguments you provide.

Accepted arities: {arity_text}.

Each argument is an Excel formula literal encoded as a JSON string. Examples include `\"1\"`, `\"\\\"text\\\"\"`, `\"DATE(2020,1,1)\"`, and `\"{{1;2;3}}\"`.

The oracle query budget is configured by the benchmark runner and exposed as `QUERY_BUDGET`; when unset, it defaults to {DEFAULT_QUERY_BUDGET}.

Query the operator with:

```bash
oracle-query < inputs.jsonl
```

Each input line must be JSON:

```json
{{"args":["1","\\\"kg\\\"","\\\"lbm\\\""]}}
```

Each oracle output line is JSON:

```json
{{"value":0.45359237,"error":null}}
{{"value":null,"error":"#VALUE!"}}
```

Protocol errors, such as exceeding the query budget, are not part of the operator behavior.
The oracle is backed by an Excel-compatible formula engine; match the observed oracle behavior exactly, including error codes, coercions, and array-shaped values.

Create an executable at:

```bash
/app/solution/solve
```

It must read JSONL inputs from stdin and write one JSONL output per input to stdout using the same output format as the oracle.

When finished, package your solution for grading:

```bash
mkdir -p /logs/artifacts
tar -czf /logs/artifacts/submission.tgz -C /app solution
```

The grader will run your submitted CLI on fixed hidden evaluation inputs and compute expected outputs with its own trusted oracle. The rollout oracle service will not be reachable during grading.
"""


def render_task_toml(function_name: str, task_name: str, arities: list[int]) -> str:
    arities_toml = ", ".join(str(arity) for arity in arities)
    tags = ['"oracle"', '"black-box"', '"spec-inference"', '"excel-function"']
    return f"""schema_version = "1.3"
artifacts = []

[task]
name = "oracle-bench/{task_name}"
description = "Infer and implement the Excel-compatible {function_name} function with a runtime-configured oracle query budget."
authors = [{{ name = "Nuno" }}]
keywords = ["oracle", "spec-inference", "jsonl", "excel-function"]

[metadata]
difficulty = "medium"
category = "programming"
tags = [{", ".join(tags)}]
family = "witan-function"
function = "{function_name}"
arities = [{arities_toml}]

[agent]
timeout_sec = 1800.0
user = "agent"

[verifier]
timeout_sec = 180.0
environment_mode = "separate"
network_mode = "public"

[verifier.env]
WITAN_API_URL = "${{WITAN_API_URL}}"
WITAN_API_KEY = "${{WITAN_API_KEY}}"
QUERY_BUDGET = "${{QUERY_BUDGET}}"

[verifier.environment]
network_mode = "public"
cpus = 1
memory_mb = 1024
storage_mb = 2048

[environment]
build_timeout_sec = 600.0
network_mode = "public"
cpus = 1
memory_mb = 1024
storage_mb = 4096
gpus = 0

[environment.env]
WITAN_API_URL = "${{WITAN_API_URL}}"
WITAN_API_KEY = "${{WITAN_API_KEY}}"
QUERY_BUDGET = "${{QUERY_BUDGET}}"
"""


def render_oracle_task(function_name: str, arities: list[int]) -> str:
    arities_python = "(" + ", ".join(str(arity) for arity in arities)
    if len(arities) == 1:
        arities_python += ","
    arities_python += ")"
    return f'''from __future__ import annotations

from typing import Any


FUNCTION_NAME = {function_name!r}
TASK_FAMILY = "witan-function"
ARG_MODE = "formula_literals"
ARITIES = {arities_python}


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    return f"={{FUNCTION_NAME}}(" + ",".join(args) + ")"
'''


def write_eval_inputs(path: Path, rows: list[dict[str, Any]]) -> None:
    output_rows = []
    for index, row in enumerate(rows, start=1):
        output_rows.append(
            {
                "args": row["args"],
                "case_id": row.get("case") or f"c{index:03d}",
            }
        )
    write_text(
        path,
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in output_rows),
    )


def generate_task(
    source_file: Path,
    tasks_dir: Path,
    template_task: Path,
    replace: bool,
) -> tuple[str, int, int, int] | None:
    all_rows = load_rows(source_file)
    rows, dropped_csharp, dropped_backend = supported_rows(all_rows)
    if not rows:
        raise ValueError(f"no rows in {source_file}")
    function_names = {row.get("function") for row in rows}
    if len(function_names) != 1:
        raise ValueError(f"mixed function names in {source_file}: {function_names}")

    function_name = function_names.pop()
    if not isinstance(function_name, str) or not function_name:
        raise ValueError(f"missing function name in {source_file}")
    if function_name.upper() in EXCLUDED_FUNCTIONS:
        return None

    arities = sorted({int(row["arity"]) for row in rows})
    task_name = f"fn-{function_slug(function_name)}"
    task_dir = tasks_dir / task_name

    if task_dir.exists():
        if not replace:
            raise FileExistsError(f"{task_dir} already exists; pass --replace")
        shutil.rmtree(task_dir)

    copy_static_files(template_task, task_dir)
    copy_shared_files(template_task, task_dir)
    write_text(task_dir / "instruction.md", render_instruction(function_name, arities))
    write_text(task_dir / "task.toml", render_task_toml(function_name, task_name, arities))
    write_text(task_dir / "tests" / "oracle_task.py", render_oracle_task(function_name, arities))
    write_eval_inputs(task_dir / "tests" / "eval_inputs.jsonl", rows)
    return task_name, len(rows), dropped_csharp, dropped_backend


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate function-as-is Harbor tasks from literalized Witan test JSONL files."
    )
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--tasks-dir", type=Path, default=DEFAULT_TASKS_DIR)
    parser.add_argument("--template-task", type=Path, default=DEFAULT_TEMPLATE_TASK)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    source_files = sorted(
        path
        for path in args.source_dir.glob("*.jsonl")
        if not path.name.startswith("_")
    )
    if not source_files:
        raise SystemExit(f"no JSONL function files found under {args.source_dir}")

    for task_dir in excluded_task_dirs(args.tasks_dir):
        if task_dir.exists():
            shutil.rmtree(task_dir)

    generated = []
    total_kept = 0
    total_dropped_csharp = 0
    total_dropped_backend = 0
    for source_file in source_files:
        result = generate_task(
            source_file=source_file,
            tasks_dir=args.tasks_dir,
            template_task=args.template_task,
            replace=args.replace,
        )
        if result is None:
            continue
        task_name, kept, dropped_csharp, dropped_backend = result
        generated.append((task_name, kept, dropped_csharp, dropped_backend))
        total_kept += kept
        total_dropped_csharp += dropped_csharp
        total_dropped_backend += dropped_backend

    print(f"generated {len(generated)} function tasks")
    print(
        f"kept {total_kept} cases; "
        f"dropped {total_dropped_csharp} unsupported C# interpolation rows; "
        f"dropped {total_dropped_backend} backend-crashing rows"
    )
    for task_name, kept, dropped_csharp, dropped_backend in generated:
        suffix = f" ({kept} cases"
        dropped = dropped_csharp + dropped_backend
        if dropped:
            suffix += f", dropped {dropped}"
        suffix += ")"
        print(task_name + suffix)


if __name__ == "__main__":
    main()
