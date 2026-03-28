from __future__ import annotations

import os
import subprocess
from pathlib import Path

from setuptools.build_meta import *  # noqa: F401,F403
from setuptools.build_meta import build_editable as _build_editable
from setuptools.build_meta import build_sdist as _build_sdist
from setuptools.build_meta import build_wheel as _build_wheel


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
        print("[mattergen-build] MATTERGEN_PULL_LFS_MODELS disabled; skipping Git LFS pull.")
        return

    if _as_bool(os.getenv("MATTERGEN_SKIP_LFS_DOWNLOAD"), default=False):
        print("[mattergen-build] MATTERGEN_SKIP_LFS_DOWNLOAD enabled; skipping Git LFS pull.")
        return

    repo_root = Path(__file__).resolve().parent
    checkpoints_dir = repo_root / "checkpoints"
    git_dir = repo_root / ".git"

    if not checkpoints_dir.exists() or not git_dir.exists():
        _maybe_raise(
            require_models,
            "[mattergen-build] source checkout not detected; skipping Git LFS pull.",
        )
        return

    try:
        subprocess.run(["git", "lfs", "version"], check=True, cwd=repo_root)
    except Exception:
        _maybe_raise(
            require_models,
            "[mattergen-build] Git LFS not available; skipping model pull.",
        )
        return

    print("[mattergen-build] Pulling model checkpoints via Git LFS...")
    try:
        subprocess.run(
            ["git", "lfs", "pull", "-I", "checkpoints/", "--exclude="],
            check=True,
            cwd=repo_root,
        )
        print("[mattergen-build] Git LFS pull completed.")
    except subprocess.CalledProcessError as exc:
        _maybe_raise(
            require_models,
            f"[mattergen-build] Git LFS pull failed: {exc}",
        )


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    _maybe_pull_lfs_models()
    return _build_wheel(
        wheel_directory=wheel_directory,
        config_settings=config_settings,
        metadata_directory=metadata_directory,
    )


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    _maybe_pull_lfs_models()
    return _build_editable(
        wheel_directory=wheel_directory,
        config_settings=config_settings,
        metadata_directory=metadata_directory,
    )


def build_sdist(sdist_directory, config_settings=None):
    _maybe_pull_lfs_models()
    return _build_sdist(sdist_directory=sdist_directory, config_settings=config_settings)
