from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEPLOY_DIR = ROOT / "huggingface-deploy"

EXCLUDE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "venv",
    ".venv",
    "env",
    "huggingface-deploy",
}

EXCLUDE_PATTERNS = (
    ".env",
    ".env.*",
    "*.pyc",
    "*.pyo",
    "*.log",
)


def is_excluded(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    for part in rel.parts:
        if part in EXCLUDE_DIRS:
            return True
    return any(fnmatch.fnmatch(rel.name, pattern) for pattern in EXCLUDE_PATTERNS)


def collect_source_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if is_excluded(path):
            continue
        files.append(path)
    return files


def clean_deploy_dir() -> None:
    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)

    def on_rm_error(func, path, exc_info):
        # Windows may keep readonly bit on copied files.
        os.chmod(path, 0o666)
        func(path)

    for item in DEPLOY_DIR.iterdir():
        # Keep deploy repo metadata if huggingface-deploy is a separate git repo.
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.rmtree(item, onexc=on_rm_error)
        else:
            item.unlink(missing_ok=True)


def sync_files() -> int:
    clean_deploy_dir()
    source_files = collect_source_files()

    for src in source_files:
        rel = src.relative_to(ROOT)
        dst = DEPLOY_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    return len(source_files)


def run_git_command(args: list[str]) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def commit_and_push(message: str) -> None:
    run_git_command(["git", "add", "."])

    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=ROOT,
        check=False,
    )
    if status.returncode == 0:
        print("No staged changes to commit.")
        return

    run_git_command(["git", "commit", "-m", message])
    run_git_command(["git", "push"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync files to huggingface-deploy and push all git changes.",
    )
    parser.add_argument(
        "-m",
        "--message",
        default=f"chore: deploy sync {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}",
        help="Commit message.",
    )
    args = parser.parse_args()

    synced_count = sync_files()
    print(f"Synced {synced_count} files to {DEPLOY_DIR}.")

    commit_and_push(args.message)
    print("Deploy sync complete.")


if __name__ == "__main__":
    main()
