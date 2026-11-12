"""Run metadata recorded with every pipeline output."""

from __future__ import annotations

import hashlib
import subprocess
from typing import Any

from astraquant.config import CONFIG_DIR, REPO_ROOT


def _git(*args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    return done.stdout.strip()


def config_digest() -> str:
    """Short hash of the config files a run used."""
    digest = hashlib.sha256()
    for name in ("assets.yaml", "settings.yaml"):
        digest.update((CONFIG_DIR / name).read_bytes())
    return digest.hexdigest()[:16]


def run_metadata(seed: int) -> dict[str, Any]:
    """Git commit, dirty flag (tracked files only), config digest and seed."""
    return {
        "git_commit": _git("rev-parse", "HEAD") or "unknown",
        "git_dirty": bool(_git("status", "--porcelain", "--untracked-files=no")),
        "config_digest": config_digest(),
        "seed": seed,
    }
