from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
COMMON_ITEMS = [
    "common",
    "requirements.txt",
    "alembic",
    "alembic.ini",
    "README.md",
]

SERVICE_ITEMS = {
    "landings": ["landings", "Dockerfile.landings"],
    "core": ["core", "Dockerfile.core"],
}


def infer_service_name(deploy_dir: Path) -> str:
    name = deploy_dir.name.lower()
    if "landings" in name:
        return "landings"
    if "core" in name:
        return "core"
    raise RuntimeError(
        f"Cannot infer service type from folder '{deploy_dir.name}'. "
        "Use folder names containing 'landings' or 'core'."
    )


def copy_item(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def clean_directory_except_git(target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    def on_rm_error(func, path, _exc_info):
        os.chmod(path, 0o666)
        func(path)

    for item in target_dir.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.rmtree(item, onexc=on_rm_error)
        else:
            item.unlink(missing_ok=True)


def sync_target(deploy_dir: Path, service: str) -> int:
    clean_directory_except_git(deploy_dir)
    copied = 0
    for item in COMMON_ITEMS + SERVICE_ITEMS[service]:
        src = ROOT / item
        if not src.exists():
            raise RuntimeError(f"Missing source item: {src}")
        destination_name = "Dockerfile" if src.name.startswith("Dockerfile.") else src.name
        dst = deploy_dir / destination_name
        copy_item(src, dst)
        copied += 1
    return copied


def run_git_command(deploy_dir: Path, args: list[str]) -> None:
    try:
        subprocess.run(args, cwd=deploy_dir, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        if "detected dubious ownership" in stderr:
            safe_path = deploy_dir.as_posix()
            raise RuntimeError(
                f"Git blocked access to {deploy_dir} due to ownership checks.\n"
                f"Run this once and retry deploy:\n"
                f"git config --global --add safe.directory {safe_path}"
            ) from exc
        raise RuntimeError(
            f"Git command failed in {deploy_dir}: {' '.join(args)}\n{stderr or exc}"
        ) from exc


def commit_and_push(deploy_dir: Path, message: str) -> None:
    if not (deploy_dir / ".git").exists():
        raise RuntimeError(f"{deploy_dir} is not a git repository (missing .git).")

    run_git_command(deploy_dir, ["git", "add", "."])

    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=deploy_dir,
        check=False,
    )
    if status.returncode == 0:
        print(f"No changes to commit in {deploy_dir.name}.")
        return

    run_git_command(deploy_dir, ["git", "commit", "-m", message])
    run_git_command(deploy_dir, ["git", "push"])


def discover_targets() -> list[Path]:
    targets: list[Path] = []
    for child in ROOT.iterdir():
        if not child.is_dir():
            continue
        if not child.name.lower().startswith("huggingface-deploy"):
            continue
        # Skip generic deploy repos that do not encode a service name.
        if "landings" not in child.name.lower() and "core" not in child.name.lower():
            continue
        if (child / ".git").exists():
            targets.append(child)
    if not targets:
        raise RuntimeError(
            "No deploy git folders found. Create folders like "
            "'huggingface-deploy-landings' and 'huggingface-deploy-core' with their own .git."
        )
    return sorted(targets, key=lambda p: p.name)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Sync files from root to deploy git folders, set service Dockerfile as Dockerfile, "
            "then commit and push inside each deploy folder."
        ),
    )
    parser.add_argument(
        "-m",
        "--message",
        default=f"chore: deploy sync {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}",
        help="Commit message for each deploy repository.",
    )
    args = parser.parse_args()

    try:
        targets = discover_targets()
        for target in targets:
            service = infer_service_name(target)
            copied_count = sync_target(target, service)
            print(f"[{target.name}] Synced {copied_count} items for service '{service}'.")
            commit_and_push(target, args.message)
            print(f"[{target.name}] Push complete.")
        print("Deploy sync complete for all folders.")
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
