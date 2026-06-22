# Mimic Bench

Mimic Bench is a coding-agent benchmark for measuring how well agents can use external feedback to solve underspecified programming tasks.

In many real engineering workflows, the human does not know every edge case up front. A useful agent should be able to make progress anyway: form hypotheses, run experiments, observe trustworthy feedback, revise its implementation, and continue until the artifact matches the target behavior. Agents that can do this reliably can run longer with less supervision and produce higher-quality outputs in domains where prose specs and static tests are incomplete.

Mimic Bench isolates that capability. Each task gives an agent an underspecified implementation target and a queryable black-box oracle. The agent can ask the oracle for outputs on inputs it chooses during rollout, then must submit an executable CLI. A hidden verifier checks whether the submitted program matches the same trusted Excel-compatible engine on fixed evaluation inputs.

The point is not spreadsheet knowledge by itself. Excel-compatible functions and charts are convenient benchmark substrates: they have many edge cases, deterministic answers, cheap oracle queries, and an exact compatibility target. The checked-in corpus currently contains 106 `fn-*` tasks and a separate chart-rendering dataset with 16 `chart-*` tasks.

The formula engine used as the oracle is measured against Microsoft Excel on real-world workbook corpora in [xlsx-corpus-bench](https://github.com/witanlabs/xlsx-corpus-bench).

The benchmark uses the [Harbor framework](https://harborframework.com/) for task packaging, sandboxed execution, agent runners, and result collection.

## Results

Current baseline over the checked-in `fn-*` corpus, run with a rollout query budget of 256 and concurrency 10.

| agent | model | effort | timeout | accuracy |
|---|---|---:|---:|---:|
| Codex | gpt-5.5 | high | 30m | 49.1% |

Accuracy is exact task success: 52 solved out of 106 tasks. The same run had one timeout and a mean dense reward of 0.863, where dense reward is the held-out case match rate used for partial-credit diagnostics.

Current baseline over the checked-in `chart-*` corpus, run with a rollout query budget of 64 and concurrency 10.

| agent | model | effort | timeout | accuracy | mean reward |
|---|---|---:|---:|---:|---:|
| Codex | gpt-5.5 | high | 90m | 0.0% | 0.670 |

Chart accuracy is exact task success: 0 solved out of 16 tasks. The run completed without verifier errors, runtime failures, or malformed outputs. Mean reward is mean full-image MS-SSIM against hidden oracle PNGs; it is a progress diagnostic, not a solved threshold.

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

Function tasks live under `tasks/fn-*` and are listed in the root `dataset.toml`.

Each task targets one Excel-compatible function as-is. Arguments are encoded as Excel formula literals in JSON strings, and the oracle evaluates the corresponding function call against the provided arguments. Examples:

```json
{"args":["1"]}
{"args":["\"kg\"","\"lbm\""]}
{"args":["DATE(2020,1,1)"]}
{"args":["{1;2;3}"]}
```

Volatile functions such as `RAND`, `RANDARRAY`, `RANDBETWEEN`, `NOW`, and `TODAY` are excluded from the corpus. Expected outputs are not stored in the repo; the verifier computes them from the oracle at grading time.

Chart-rendering tasks live under `tasks/chart-*` and are listed in `datasets/chart-rendering/dataset.toml`. These tasks give the agent JSON workbook data plus a JSON chart spec. The oracle renders the chart to a PNG at dpr 1 and zoom 1, and the verifier compares submitted PNGs against hidden oracle renders.

The current chart dataset covers column, bar, line, area, pie, doughnut, scatter, bubble, radar, surface, stock, funnel, waterfall, histogram, Pareto, and box-and-whisker charts.

## Layout

```text
dataset.toml
datasets/
  chart-rendering/
    dataset.toml
pyproject.toml
template-fn-task/
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
template-chart-task/
  environment/
  tests/
tasks/
  fn-*/
    instruction.md
    task.toml
    environment/
    tests/
  chart-*/
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

The task-agnostic helper files for `fn-*` tasks are sourced from `template-fn-task/` and copied into every function task. Chart task helpers are sourced from `template-chart-task/`. The `shared_*` names are deliberately explicit, while Harbor/Docker-required filenames such as `Dockerfile`, `docker-compose.yaml`, and `tests/test.sh` keep their conventional names.

After editing a template, sync helper files and refresh task digests:

```bash
python scripts/sync_shared.py
python scripts/sync_shared.py --template-task template-chart-task --task-prefix chart-
uv run harbor add tasks --scan --to dataset.toml
uv run harbor add tasks/chart-* --to datasets/chart-rendering/dataset.toml
```

## Protocol

During the agent phase, every task exposes:

```bash
oracle-query < inputs.jsonl
```

For `fn-*` tasks, input lines are JSON objects with an `args` array:

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

For `chart-*` tasks, input lines contain `sheets` plus a `chart` object. Oracle and solution output lines are JSON objects containing `contentType`, `pixelWidth`, `pixelHeight`, and base64 PNG `data`.

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

Primary fields for `fn-*` tasks:

- `accuracy`: exact 0/1 task success. It is `1` only when every eval case matches exactly and the submission has no malformed outputs.
- `reward`: dense partial-credit score. It is the per-case match rate minus a malformed-output penalty, with missing submissions and runtime failures scored as `0`.

Diagnostic fields include `match_count`, `eval_cases`, `malformed_outputs`, `runtime_failure`, `missing_submission`, `budget`, and `queries_used` when available.

There are no wrapper-added result types, numeric tolerances, or separate wrong-type/wrong-value grading buckets.

For `chart-*` tasks, `reward` is the mean full-image MS-SSIM against hidden oracle PNGs, with malformed-output penalties. `accuracy` is still a strict solved flag: it is `1` only when every hidden case clears the task threshold and the submission has no malformed outputs.

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

Run one chart-rendering task:

```bash
QUERY_BUDGET=64 uv run harbor run \
  -p tasks/chart-column \
  -a codex \
  -m gpt-5.5 \
  --agent-env 'OPENAI_API_KEY=${OPENAI_API_KEY}' \
  --env-file .envrc \
  -n 1 \
  --yes
```

Function tasks currently use a 30 minute agent timeout. Chart-rendering tasks currently use a 90 minute agent timeout. The rollout query budget is controlled by `QUERY_BUDGET`; if unset, function-task helpers default to 256 queries and chart-task helpers default to 64.

## Future Work

Future task families should keep the same benchmark shape: the agent gets a task, can query a trusted oracle during rollout, and is graded against oracle outputs on held-out inputs.

Natural directions:

- Broaden beyond formula functions to other domains with credible programmatic oracles.
- Add harder formula tasks, such as composed formulas or hidden function identity, as separate task families.
- Add richer chart-rendering tasks, such as multi-group chart combinations, more formatting surfaces, and chart families whose oracle output is an OOXML-derived image.
- Add task families with richer artifacts than a JSONL CLI, while preserving a simple verifier contract.

New families should stay separate from the current `fn-*` corpus so results remain interpretable.
