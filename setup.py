from __future__ import annotations

import os
import subprocess
from pathlib import Path

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _maybe_raise(require_models: bool, message: str) -> None:
    if require_models:
        raise RuntimeError(message)
    print(message)


def _maybe_pull_lfs_models() -> None:
    require_models = _as_bool(os.getenv("MATTERGEN_REQUIRE_LFS_MODELS"), default=True)

    if not _as_bool(os.getenv("MATTERGEN_PULL_LFS_MODELS"), default=True):
        print("[mattergen] MATTERGEN_PULL_LFS_MODELS disabled; skipping Git LFS pull.")
        return

    if _as_bool(os.getenv("MATTERGEN_SKIP_LFS_DOWNLOAD"), default=False):
        print("[mattergen] MATTERGEN_SKIP_LFS_DOWNLOAD enabled; skipping Git LFS pull.")
        return

    repo_root = Path(__file__).resolve().parent
    checkpoints_dir = repo_root / "checkpoints"
    git_dir = repo_root / ".git"

    if not checkpoints_dir.exists():
        # In isolated wheel/sdist builds, checkpoints are usually not present.
        print("[mattergen] checkpoints directory not found; skipping Git LFS pull.")
        return

    if not git_dir.exists():
        # In isolated wheel/sdist builds, `.git` metadata is often missing.
        print("[mattergen] .git directory not found; skipping Git LFS pull.")
        return

    try:
        subprocess.run(["git", "lfs", "version"], check=True, cwd=repo_root)
    except Exception:
        _maybe_raise(require_models, "[mattergen] Git LFS not available; skipping model pull.")
        return

    print("[mattergen] Pulling all checkpoint models via Git LFS...")
    try:
        subprocess.run(
            ["git", "lfs", "pull", "-I", "checkpoints/", "--exclude="],
            check=True,
            cwd=repo_root,
        )
        print("[mattergen] Git LFS model pull completed.")
    except subprocess.CalledProcessError as exc:
        _maybe_raise(require_models, f"[mattergen] Git LFS model pull failed: {exc}")


class InstallWithLFS(install):
    def run(self):
        super().run()
        _maybe_pull_lfs_models()


class DevelopWithLFS(develop):
    def run(self):
        super().run()
        _maybe_pull_lfs_models()


setup(
    cmdclass={
        "install": InstallWithLFS,
        "develop": DevelopWithLFS,
    }
)
