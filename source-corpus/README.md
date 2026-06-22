# Source Corpus

This directory contains source inputs used to generate checked-in Harbor tasks.

The generated task eval files store function names, arities, and argument lists as Excel formula literals. They do not store expected outputs; verifiers compute expected outputs with the trusted Excel-compatible formula engine at grading time.

Current corpus:

- `function-test-args-literalized-augmented-v3/`: real Excel-compatible `fn-*` tasks.
- `proposed-function-formula-simulations/`: proposed-function `pfn-*` tasks with task-local LAMBDA oracle implementations.

The rows are filtered from literalized spreadsheet-function test cases and retain source/provenance fields where available. Volatile functions and unsupported artifacts are filtered by `scripts/generate_function_tasks.py` when tasks are regenerated.

To regenerate tasks from these corpora:

```bash
python scripts/generate_function_tasks.py --replace
python scripts/generate_proposed_function_tasks.py --replace
python scripts/sync_shared.py
uv run harbor add tasks/fn-* --to dataset.toml
uv run harbor add tasks/pfn-* --to datasets/proposed-functions/dataset.toml
```
