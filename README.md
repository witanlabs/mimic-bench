# Mimic Bench

Mimic Bench is a coding-agent benchmark for measuring how well agents can use external feedback to solve underspecified programming tasks.

In many real engineering workflows, the human does not know every edge case up front. A useful agent should be able to make progress anyway: form hypotheses, run experiments, observe trustworthy feedback, revise its implementation, and continue until the artifact matches the target behavior. Agents that can do this reliably can run longer with less supervision and produce higher-quality outputs in domains where prose specs and static tests are incomplete.

Mimic Bench isolates that capability. Each task gives an agent a function name, accepted arities, and a queryable black-box oracle. The agent can ask the oracle for outputs on inputs it chooses during rollout, then must submit an executable CLI. A hidden verifier checks whether the submitted program matches the same trusted Excel-compatible formula engine on fixed evaluation inputs.

The point is not spreadsheet knowledge by itself. Excel-compatible functions are a convenient benchmark substrate: they have many edge cases, deterministic answers, cheap oracle queries, and an exact compatibility target. The checked-in corpus currently contains 106 `fn-*` tasks and no other task families.

The formula engine used as the oracle is measured against Microsoft Excel on real-world workbook corpora in [xlsx-corpus-bench](https://github.com/witanlabs/xlsx-corpus-bench).

The benchmark uses the [Harbor framework](https://harborframework.com/) for task packaging, sandboxed execution, agent runners, and result collection.

## Results

Temporary baseline, from an interrupted run. This is included only as a provisional reference point; it was run before the current 30 minute timeout setting and before the corpus was reduced to `fn-*` tasks only.

| agent | model | effort | timeout | accuracy |
|---|---|---:|---:|---:|
| Codex | gpt-5.5 | high | 10m | 29.5% |

Accuracy is exact task success on scored tasks: 13 solved out of 44 scored trials. The interrupted job reached 49 of 108 scheduled trials before being stopped, with 59 trials still pending.

## What It Measures

Mimic Bench measures whether an agent can independently close the gap between an underspecified interface and a correct implementation using feedback it obtains during the task.

A successful agent needs to:

- choose informative oracle queries within the rollout budget
- infer behavior from examples rather than relying only on public documentation or prior knowledge
- distinguish task behavior from protocol errors
- implement a robust CLI in any language it chooses
- package the implementation for a separate verifier
- generalize from rollout queries to held-out evaluation inputs

The benchmark is intentionally strict about the contract. The correct answer is exact oracle compatibility on the pinned evaluation inputs, not a plausible interpretation of a public spec.

## Task Corpus

Tasks live under `tasks/fn-*` and are listed in `dataset.toml`.

Each task targets one Excel-compatible function as-is. Arguments are encoded as Excel formula literals in JSON strings, and the oracle evaluates the corresponding function call against the provided arguments. Examples:

```json
{"args":["1"]}
{"args":["\"kg\"","\"lbm\""]}
{"args":["DATE(2020,1,1)"]}
{"args":["{1;2;3}"]}
```

Volatile functions such as `RAND`, `RANDARRAY`, `RANDBETWEEN`, `NOW`, and `TODAY` are excluded from the corpus. Expected outputs are not stored in the repo; the verifier computes them from the oracle at grading time.

## Layout

```text
dataset.toml
pyproject.toml
template-task/
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
    shared_test.sh
    shared_grader.py
    shared_oracle_runtime.py
tasks/
  fn-*/
    instruction.md
    task.toml
    environment/
    tests/
source-corpus/
  function-test-args-literalized-augmented-v3/
scripts/
  sync_shared.py
```

The task-specific files are:

- `task.toml`
- `instruction.md`
- `tests/eval_inputs.jsonl`
- `tests/oracle_task.py`

The task-agnostic helper files are sourced from `template-task/` and copied into every task. The `shared_*` names are deliberately explicit, while Harbor/Docker-required filenames such as `Dockerfile`, `docker-compose.yaml`, and `tests/test.sh` keep their conventional names.

After editing `template-task/`, sync helper files and refresh task digests:

```bash
python scripts/sync_shared.py
uv run harbor add tasks --scan --to dataset.toml
```

## Protocol

During the agent phase, the task exposes:

```bash
oracle-query < inputs.jsonl
```

Input lines are JSON objects with an `args` array:

```json
{"args":["1","2"]}
```

Oracle output lines are JSON:

```json
{"value":3,"error":null}
{"value":null,"error":"#VALUE!"}
```

The submitted solution must provide:

```bash
/app/solution/solve
```

It must read JSONL inputs from stdin and write one JSONL output per input to stdout using the same `{value, error}` format as the oracle.

At the end of the rollout, the agent packages the solution for the verifier:

```bash
mkdir -p /logs/artifacts
tar -czf /logs/artifacts/submission.tgz -C /app solution
```

The rollout oracle is not available during grading.

## Oracle

Both the rollout oracle sidecar and the verifier call an Excel-compatible formula engine API.

The sidecar is intentionally thin. It hides API credentials from the agent container, enforces the rollout query budget, logs oracle queries, and exposes the task-local `oracle-query` command. Spreadsheet semantics stay inside the formula engine.

Runtime credentials are read from a local `.envrc` file. Keep it gitignored and pass it to Harbor with `--env-file .envrc`.

## Scoring

The verifier writes `/logs/verifier/reward.json`.

Primary fields:

- `accuracy`: exact 0/1 task success. It is `1` only when every eval case matches exactly and the submission has no malformed outputs.
- `reward`: dense partial-credit score. It is the per-case match rate minus a malformed-output penalty, with missing submissions and runtime failures scored as `0`.

Diagnostic fields include `match_count`, `eval_cases`, `malformed_outputs`, `runtime_failure`, `missing_submission`, `budget`, and `queries_used` when available.

There are no wrapper-added result types, numeric tolerances, or separate wrong-type/wrong-value grading buckets.

## Running

Install dependencies:

```bash
uv sync
```

Smoke-test one task:

```bash
QUERY_BUDGET=256 uv run harbor run \
  -p tasks/fn-gauss \
  -a codex \
  -m gpt-5.5 \
  --agent-env 'OPENAI_API_KEY=${OPENAI_API_KEY}' \
  --env-file .envrc \
  -n 1 \
  --yes
```

Run the full checked-in corpus with Codex at concurrency 10:

```bash
QUERY_BUDGET=256 uv run harbor run \
  -p tasks \
  -a codex \
  -m gpt-5.5 \
  --agent-env 'OPENAI_API_KEY=${OPENAI_API_KEY}' \
  --env-file .envrc \
  --job-name codex-gpt55-fn-all-q256-c10 \
  -n 10 \
  --yes
```

The current task configs set a 30 minute agent timeout. The rollout query budget is controlled by `QUERY_BUDGET`; if unset, helper code defaults it to 256.

## Future Work

Future task families should keep the same benchmark shape: the agent gets a task, can query a trusted oracle during rollout, and is graded against oracle outputs on held-out inputs.

Natural directions:

- Broaden beyond formula functions to other domains with credible programmatic oracles.
- Add harder formula tasks, such as composed formulas or hidden function identity, as separate task families.
- Add rendering tasks where equality is replaced by an oracle-derived visual comparison. For example, give the agent an OOXML chart spec plus a chart-rendering oracle that produces the reference PNG, then ask it to implement an equivalent renderer for that chart subset.
- Add task families with richer artifacts than a JSONL CLI, while preserving a simple verifier contract.

New families should stay separate from the current `fn-*` corpus so results remain interpretable.
