# Oracle Bench

Oracle Bench is a Harbor-style benchmark/training-environment seed for active black-box specification inference.

Each task gives an agent an anonymous operator, an input schema, and a limited query budget. The agent may query an oracle during its rollout, then must submit an executable CLI that matches the hidden oracle behavior on fixed verifier inputs.

The initial MVP is intentionally small: Harbor-compatible vertical-slice tasks with Witan-backed rollout oracles, query-budgeted JSONL protocol, and separate Witan-backed verifiers.

## Layout

```text
template-task/
  environment/
    shared_oracle_query.py
    oracle-service/
      shared_oracle_service.py
  tests/
    shared_test.sh
    shared_grader.py
    shared_oracle_runtime.py
scripts/
  sync_shared.py
tasks/
  op001-k016/
    ...
  op002-k016/
    instruction.md
    task.toml
    environment/
      Dockerfile
      docker-compose.yaml
      shared_oracle_query.py
      oracle-service/
        Dockerfile
        shared_oracle_service.py
    tests/
      Dockerfile
      test.sh
      oracle_task.py
      shared_test.sh
      shared_grader.py
      shared_oracle_runtime.py
      eval_inputs.jsonl
```

Current tasks:

- `op001-k016`: numeric Excel-coercion operator.
- `op002-k016`: mixed text/numeric Excel-coercion operator.

## Protocol

During the agent phase, the task exposes:

```bash
oracle-query < inputs.jsonl
```

Input lines are JSON:

```json
{"args":[3, "4"]}
```

Output lines are JSON:

```json
{"value":11.5,"error":null}
{"value":null,"error":"#VALUE!"}
```

The final submitted program must be:

```bash
/app/solution/solve < inputs.jsonl > outputs.jsonl
```

The agent must package it for the separate verifier:

```bash
mkdir -p /logs/artifacts
tar -czf /logs/artifacts/submission.tgz -C /app solution
```

The oracle sidecar and verifier install the released PyPI `witan` package and use its `Workbook` SDK, which is backed by `witan xlsx rpc`, against the configured Witan API. Query arguments are written into worksheet input cells and the hidden task formula references those cells directly; JSON `null` is treated as a blank cell. Evaluation inputs are fixed per task, but expected outputs are computed by the verifier oracle at grading time. Runtime credentials live in a local `.envrc` file and are loaded by Harbor with `--env-file .envrc`.

The output protocol is intentionally just a minimal projection of Witan's formula result: `value` and Excel error code. There are no wrapper-added result types, numeric tolerances, or separate wrong-type/wrong-value grading buckets.

The sidecar is deliberately thin: it does not implement spreadsheet semantics. It only hides Witan credentials and the hidden task formula from the agent container, enforces the rollout query budget, and exposes the task-local `oracle-query` CLI.

The per-task unique surface is intentionally small:

- `task.toml`
- `instruction.md`
- `tests/eval_inputs.jsonl`
- `tests/oracle_task.py`, which defines the hidden cell-reference formula and task metadata

The source of truth for copied task-agnostic code lives in `template-task/`.
Inside each task archive, generated copies are prefixed with `shared_`:

- `environment/shared_oracle_query.py`, installed in the agent image as the protocol command `oracle-query`
- `environment/oracle-service/shared_oracle_service.py`
- `tests/shared_oracle_runtime.py`
- `tests/shared_grader.py`
- `tests/shared_test.sh`

The Harbor-conventional `Dockerfile` and `docker-compose.yaml` names are left unprefixed, but their contents should also remain task-agnostic where possible. This keeps every task archive self-contained under Harbor's packaging model while making the copied code obvious.
The verifier keeps a tiny unprefixed `tests/test.sh` shim because Harbor invokes that path directly; it only execs `shared_test.sh`.

After editing `template-task/`, regenerate all per-task shared copies with:

```bash
python scripts/sync_shared.py
```

The sync script removes every `shared_*` file or directory from each `tasks/*/` task before copying the template files back by relative path.

Required local env file:

```bash
export WITAN_API_URL=https://api.dev.witanlabs.com
export WITAN_API_KEY=...
```

## Local Smoke Check

Harbor is installed through the repo-local `pyproject.toml`:

```bash
uv sync
```

When Harbor is installed, run agent smoke checks with:

```bash
uv run harbor run -p tasks/op001-k016 -a codex -m gpt-5.5 --env-file .envrc
uv run harbor run -p tasks/op001-k016 -a claude-code -m claude-opus-4-8 --env-file .envrc
uv run harbor run -p tasks/op002-k016 -a codex -m gpt-5.5 --env-file .envrc
uv run harbor run -p tasks/op002-k016 -a claude-code -m claude-opus-4-8 --env-file .envrc
```

## Next Build Steps

1. Add budget variants: `op001-k000`, `op001-k004`, `op001-k064`, `op001-k256`.
2. Add mechanism-disjoint tasks before running frontier model baselines.
3. Keep primitive Excel functions as eval anchors, not the main train stream.
4. Pin or deliberately bump the `WITAN_PACKAGE` Docker build arg as the API/client surface evolves.
