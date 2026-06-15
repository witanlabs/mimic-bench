# Source Corpus

This directory contains source inputs used to generate the checked-in `tasks/fn-*` Harbor tasks.

The corpus stores function names, arities, and argument lists as Excel formula literals. It does not store expected outputs; verifiers compute expected outputs with the trusted Excel-compatible formula engine at grading time.

Current corpus:

- `function-test-args-literalized-augmented-v3/`

The rows are filtered from literalized spreadsheet-function test cases and retain source/provenance fields where available. Volatile functions and unsupported artifacts are filtered by `scripts/generate_function_tasks.py` when tasks are regenerated.

To regenerate tasks from this corpus:

```bash
python scripts/generate_function_tasks.py --replace
python scripts/sync_shared.py
uv run harbor add tasks --scan --to dataset.toml
```
