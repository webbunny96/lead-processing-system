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
    "deploy.py",
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

    def on_rm_error(func, path, _exc_info):
        os.chmod(path, 0o666)
        func(path)

    for item in DEPLOY_DIR.iterdir():
        # Preserve deploy repository metadata.
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
    try:
        subprocess.run(args, cwd=DEPLOY_DIR, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        if "detected dubious ownership" in stderr:
            safe_path = DEPLOY_DIR.as_posix()
            raise RuntimeError(
                "Git blocked access to huggingface-deploy due to ownership checks.\n"
                f"Run this once and retry deploy:\n"
                f"git config --global --add safe.directory {safe_path}"
            ) from exc
        raise RuntimeError(
            f"Git command failed: {' '.join(args)}\n{stderr or exc}"
        ) from exc


def commit_and_push(message: str) -> None:
    if not (DEPLOY_DIR / ".git").exists():
        raise RuntimeError("huggingface-deploy is not a git repository (missing .git).")

    run_git_command(["git", "add", "."])

    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=DEPLOY_DIR,
        check=False,
    )
    if status.returncode == 0:
        print("No changes to commit in huggingface-deploy.")
        return

    run_git_command(["git", "commit", "-m", message])
    run_git_command(["git", "push"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync project to huggingface-deploy and push using huggingface-deploy git remote.",
    )
    parser.add_argument(
        "-m",
        "--message",
        default=f"chore: deploy sync {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}",
        help="Commit message for huggingface-deploy repository.",
    )
    args = parser.parse_args()

    try:
        synced_count = sync_files()
        print(f"Synced {synced_count} files to {DEPLOY_DIR}.")

        commit_and_push(args.message)
        print("Deploy sync complete.")
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
