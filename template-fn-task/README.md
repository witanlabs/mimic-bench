# Template Task

This directory is the source of truth for copied task-agnostic helper files.
Generated tasks copy both `shared_*` files and the static Harbor/Docker shims
from here.
It is not a runnable Harbor task and should not be listed in `dataset.toml`.

Run `python scripts/sync_shared.py` from the repo root after changing files here.
