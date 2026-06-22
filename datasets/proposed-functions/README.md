# mimic-bench/proposed-functions

Harbor dataset manifest for the `pfn-*` proposed-function tasks.

These tasks ask agents to infer plausible upcoming Excel-compatible functions that do not currently exist in public Excel. Each task uses the same JSONL CLI protocol as the real `fn-*` tasks, but the oracle defines the function with a task-local Excel `LAMBDA` implementation before evaluating calls.

Local run example:

```bash
QUERY_BUDGET=256 uv run harbor run \
  -p tasks \
  -i 'pfn-*' \
  -a codex \
  -m gpt-5.5 \
  --agent-env 'OPENAI_API_KEY=${OPENAI_API_KEY}' \
  --env-file .envrc \
  -n 10 \
  --yes
```
