#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_TASK = REPO_ROOT / "template-task"
DEFAULT_TASKS_DIR = REPO_ROOT / "tasks"


def shared_paths(root: Path) -> list[Path]:
    return sorted(root.rglob("shared_*"))


def shared_files(root: Path) -> list[Path]:
    return [path for path in shared_paths(root) if path.is_file()]


def task_dirs(tasks_dir: Path) -> list[Path]:
    return [
        path
        for path in sorted(tasks_dir.iterdir())
        if path.is_dir() and (path / "task.toml").is_file()
    ]


def remove_shared_paths(task_dir: Path) -> int:
    removed = 0
    for path in sorted(shared_paths(task_dir), key=lambda item: len(item.parts), reverse=True):
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
            removed += 1
        elif path.exists() or path.is_symlink():
            path.unlink()
            removed += 1
    return removed


def sync_task(template_task: Path, task_dir: Path, template_files: list[Path]) -> tuple[int, int]:
    removed = remove_shared_paths(task_dir)
    copied = 0
    for source in template_files:
        relative_path = source.relative_to(template_task)
        destination = task_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied += 1
    return removed, copied


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync template-task shared_* files into every task under tasks/."
    )
    parser.add_argument("--template-task", type=Path, default=DEFAULT_TEMPLATE_TASK)
    parser.add_argument("--tasks-dir", type=Path, default=DEFAULT_TASKS_DIR)
    args = parser.parse_args()

    template_task = args.template_task.resolve()
    tasks_dir = args.tasks_dir.resolve()
    template_files = shared_files(template_task)
    tasks = task_dirs(tasks_dir)

    if not template_task.exists():
        raise SystemExit(f"missing template task: {template_task}")
    if not template_files:
        raise SystemExit(f"no shared_* files found under {template_task}")
    if not tasks:
        raise SystemExit(f"no task.toml-bearing tasks found under {tasks_dir}")

    for task_dir in tasks:
        removed, copied = sync_task(template_task, task_dir, template_files)
        print(f"{task_dir.relative_to(REPO_ROOT)}: removed {removed}, copied {copied}")


if __name__ == "__main__":
    main()
