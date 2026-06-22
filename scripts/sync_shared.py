#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_TASK = REPO_ROOT / "template-fn-task"
DEFAULT_TASKS_DIR = REPO_ROOT / "tasks"
STATIC_TEMPLATE_FILES = [
    Path("environment/Dockerfile"),
    Path("environment/docker-compose.yaml"),
    Path("environment/oracle-service/Dockerfile"),
    Path("tests/Dockerfile"),
    Path("tests/test.sh"),
]


def shared_paths(root: Path) -> list[Path]:
    return sorted(root.rglob("shared_*"))


def shared_files(root: Path) -> list[Path]:
    return [path for path in shared_paths(root) if path.is_file()]


def template_owned_files(root: Path) -> list[Path]:
    files = shared_files(root)
    files.extend(root / relative for relative in STATIC_TEMPLATE_FILES)
    return sorted(files)


def task_dirs(tasks_dir: Path, task_prefix: str | None) -> list[Path]:
    return [
        path
        for path in sorted(tasks_dir.iterdir())
        if path.is_dir() and (path / "task.toml").is_file()
        and (task_prefix is None or path.name.startswith(task_prefix))
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


def remove_static_paths(task_dir: Path) -> int:
    removed = 0
    for relative_path in STATIC_TEMPLATE_FILES:
        path = task_dir / relative_path
        if path.exists() or path.is_symlink():
            path.unlink()
            removed += 1
    return removed


def sync_task(template_task: Path, task_dir: Path, template_files: list[Path]) -> tuple[int, int]:
    removed = remove_shared_paths(task_dir) + remove_static_paths(task_dir)
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
        description="Sync template-owned helper files into every task under tasks/."
    )
    parser.add_argument("--template-task", type=Path, default=DEFAULT_TEMPLATE_TASK)
    parser.add_argument("--tasks-dir", type=Path, default=DEFAULT_TASKS_DIR)
    parser.add_argument(
        "--task-prefix",
        default="fn-",
        help="Only sync tasks whose directory name starts with this prefix. Use an empty string for all tasks.",
    )
    args = parser.parse_args()

    template_task = args.template_task.resolve()
    tasks_dir = args.tasks_dir.resolve()
    template_files = template_owned_files(template_task)
    task_prefix = args.task_prefix if args.task_prefix else None
    tasks = task_dirs(tasks_dir, task_prefix)

    if not template_task.exists():
        raise SystemExit(f"missing template task: {template_task}")
    missing_files = [path for path in template_files if not path.is_file()]
    if missing_files:
        missing = ", ".join(str(path.relative_to(template_task)) for path in missing_files)
        raise SystemExit(f"missing template-owned files under {template_task}: {missing}")
    if not tasks:
        raise SystemExit(f"no matching task.toml-bearing tasks found under {tasks_dir}")

    for task_dir in tasks:
        removed, copied = sync_task(template_task, task_dir, template_files)
        print(f"{task_dir.relative_to(REPO_ROOT)}: removed {removed}, copied {copied}")


if __name__ == "__main__":
    main()
