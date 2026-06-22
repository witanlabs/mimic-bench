#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_FILE = (
    REPO_ROOT
    / "source-corpus"
    / "proposed-function-formula-simulations"
    / "combined-proposed-function-formula-simulations.md"
)
DEFAULT_TASKS_DIR = REPO_ROOT / "tasks"
DEFAULT_TEMPLATE_TASK = REPO_ROOT / "template-task"
DEFAULT_QUERY_BUDGET = 256


SECTION_HEADING_RE = re.compile(r"^## ([A-Z][A-Z0-9._]*)\s*$", re.MULTILINE)
TABLE_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|")


def function_slug(function_name: str) -> str:
    slug = function_name.lower().replace(".", "-").replace("_", "-")
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug


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


def split_excel_args(text: str) -> list[str]:
    args: list[str] = []
    start = 0
    depth = 0
    in_string = False
    index = 0
    while index < len(text):
        char = text[index]
        if in_string:
            if char == '"':
                if index + 1 < len(text) and text[index + 1] == '"':
                    index += 1
                else:
                    in_string = False
        elif char == '"':
            in_string = True
        elif char in "({[":
            depth += 1
        elif char in ")}]":
            depth -= 1
            if depth < 0:
                raise ValueError(f"unbalanced delimiters in {text!r}")
        elif char == "," and depth == 0:
            args.append(text[start:index].strip())
            start = index + 1
        index += 1

    if in_string or depth != 0:
        raise ValueError(f"unterminated string or delimiter in {text!r}")
    args.append(text[start:].strip())
    if not all(args):
        raise ValueError(f"empty argument in {text!r}")
    return args


def arities_for_lambda(lambda_body: str) -> list[int]:
    prefix = "LAMBDA("
    if not lambda_body.upper().startswith(prefix) or not lambda_body.endswith(")"):
        raise ValueError("not a LAMBDA expression")

    parts = split_excel_args(lambda_body[len(prefix) : -1])
    if len(parts) < 2:
        raise ValueError("LAMBDA must have at least one parameter and a body")

    params = parts[:-1]
    required = sum(
        1
        for param in params
        if not (param.startswith("[") and param.endswith("]"))
    )
    return list(range(required, len(params) + 1))


def parse_markdown(source_file: Path) -> list[dict[str, Any]]:
    text = source_file.read_text()
    headings = list(SECTION_HEADING_RE.finditer(text))
    sections = []
    for index, heading in enumerate(headings):
        function_name = heading.group(1)
        body_start = heading.end()
        body_end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[body_start:body_end]

        formula_match = re.search(r"```excel\n(.*?)\n```", body, re.DOTALL)
        if not formula_match:
            raise ValueError(f"missing excel implementation for {function_name}")
        definition = formula_match.group(1).strip()
        prefix = f"{function_name} :="
        if not definition.startswith(prefix):
            raise ValueError(f"implementation for {function_name} does not start with {prefix!r}")
        lambda_body = definition[len(prefix) :].strip()
        if not lambda_body.upper().startswith("LAMBDA("):
            raise ValueError(f"implementation for {function_name} is not a LAMBDA")

        rows = []
        for line in body.splitlines():
            if not TABLE_ROW_RE.match(line):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) != 3:
                raise ValueError(f"bad markdown table row for {function_name}: {line}")
            case_id, input_args, expected_output = cells
            input_args = input_args.strip("`")
            expected_output = expected_output.strip("`")
            rows.append(
                {
                    "case_id": f"c{int(case_id):03d}",
                    "args": split_excel_args(input_args),
                    "expected": expected_output,
                }
            )

        if not rows:
            raise ValueError(f"no rows for {function_name}")
        sections.append(
            {
                "function": function_name,
                "lambda_body": lambda_body,
                "arities": arities_for_lambda(lambda_body),
                "rows": rows,
            }
        )

    if not sections:
        raise ValueError(f"no proposed functions found in {source_file}")
    return sections


def render_instruction(function_name: str, arities: list[int]) -> str:
    arity_text = ", ".join(str(arity) for arity in arities)
    return f"""You need to infer and implement the Excel-compatible behavior of proposed upcoming function `{function_name}`.

This function is not currently a public Excel function. Treat it as a plausible proposed Excel function whose exact behavior is defined by the oracle.

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
{{"args":["1","\\\"text\\\""]}}
```

Each oracle output line is JSON:

```json
{{"value":3,"error":null}}
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
    tags = ['"oracle"', '"black-box"', '"spec-inference"', '"proposed-excel-function"']
    return f"""schema_version = "1.3"
artifacts = []

[task]
name = "mimic-bench/{task_name}"
description = "Infer and implement the Excel-compatible proposed {function_name} function with a runtime-configured oracle query budget."
authors = [{{ name = "Nuno" }}]
keywords = ["oracle", "spec-inference", "jsonl", "proposed-excel-function"]

[metadata]
difficulty = "medium"
category = "programming"
tags = [{", ".join(tags)}]
family = "proposed-function"
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


def render_oracle_task(function_name: str, lambda_body: str, arities: list[int]) -> str:
    arities_python = "(" + ", ".join(str(arity) for arity in arities)
    if len(arities) == 1:
        arities_python += ","
    arities_python += ")"
    return f'''from __future__ import annotations

from typing import Any


FUNCTION_NAME = {function_name!r}
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = {arities_python}
LAMBDA_BODY = {lambda_body!r}


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{{FUNCTION_NAME}}(" + ",".join(args) + ")"
    return f"=LET({{FUNCTION_NAME}},{{LAMBDA_BODY}},{{call}})"
'''


def write_eval_inputs(path: Path, rows: list[dict[str, Any]]) -> None:
    output_rows = [
        {
            "args": row["args"],
            "case_id": row["case_id"],
        }
        for row in rows
    ]
    write_text(
        path,
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in output_rows),
    )


def generate_task(
    section: dict[str, Any],
    tasks_dir: Path,
    template_task: Path,
    replace: bool,
) -> tuple[str, int]:
    function_name = section["function"]
    rows = section["rows"]
    arities = section["arities"]
    task_name = f"pfn-{function_slug(function_name)}"
    task_dir = tasks_dir / task_name

    if task_dir.exists():
        if not replace:
            raise FileExistsError(f"{task_dir} already exists; pass --replace")
        shutil.rmtree(task_dir)

    copy_static_files(template_task, task_dir)
    copy_shared_files(template_task, task_dir)
    write_text(task_dir / "instruction.md", render_instruction(function_name, arities))
    write_text(task_dir / "task.toml", render_task_toml(function_name, task_name, arities))
    write_text(
        task_dir / "tests" / "oracle_task.py",
        render_oracle_task(function_name, section["lambda_body"], arities),
    )
    write_eval_inputs(task_dir / "tests" / "eval_inputs.jsonl", rows)
    return task_name, len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate proposed-function Harbor tasks from markdown LAMBDA simulations."
    )
    parser.add_argument("--source-file", type=Path, default=DEFAULT_SOURCE_FILE)
    parser.add_argument("--tasks-dir", type=Path, default=DEFAULT_TASKS_DIR)
    parser.add_argument("--template-task", type=Path, default=DEFAULT_TEMPLATE_TASK)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    sections = parse_markdown(args.source_file)
    generated = []
    total_cases = 0
    for section in sections:
        task_name, kept = generate_task(
            section=section,
            tasks_dir=args.tasks_dir,
            template_task=args.template_task,
            replace=args.replace,
        )
        generated.append((task_name, kept))
        total_cases += kept

    print(f"generated {len(generated)} proposed-function tasks")
    print(f"kept {total_cases} cases")
    for task_name, kept in generated:
        print(f"{task_name} ({kept} cases)")


if __name__ == "__main__":
    main()
