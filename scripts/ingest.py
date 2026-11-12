"""Re-ingest every configured symbol and write the data-quality report.

Usage: python scripts/ingest.py
"""

from __future__ import annotations

import hashlib
import subprocess
import sys

import pandas as pd

from astraquant.config import CONFIG_DIR, REPO_ROOT, load_assets, load_settings
from astraquant.data.ingest import run_ingest
from astraquant.data.provider import YFinanceProvider
from astraquant.data.report import render_report


def _git(*args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    return done.stdout.strip()


def _config_digest() -> str:
    digest = hashlib.sha256()
    for name in ("assets.yaml", "settings.yaml"):
        digest.update((CONFIG_DIR / name).read_bytes())
    return digest.hexdigest()[:16]


def main() -> int:
    """Run the ingest and return a process exit code (1 if any error-level issue)."""
    assets = load_assets()
    settings = load_settings()
    if settings.provider != "yfinance":
        raise SystemExit(f"unsupported provider: {settings.provider}")
    provider = YFinanceProvider(settings.max_retries, settings.request_pause_seconds)
    meta = {
        "git_commit": _git("rev-parse", "HEAD") or "unknown",
        "git_dirty": bool(_git("status", "--porcelain", "--untracked-files=no")),
        "config_digest": _config_digest(),
        "seed": settings.seed,
    }
    result = run_ingest(assets, settings, provider, pd.Timestamp.now(tz="UTC"), meta)

    settings.report_path.parent.mkdir(parents=True, exist_ok=True)
    settings.report_path.write_text(render_report(result, assets), encoding="utf-8")

    print(result.summary.to_string(index=False))
    print(f"\nraw:    {result.raw_dir}")
    print(f"report: {settings.report_path}")
    errors = int((result.issues["severity"] == "error").sum())
    splits_ok = all(check.get("passed") for check in result.split_checks)
    print(f"errors: {errors}; split checks passed: {splits_ok}")
    return 0 if errors == 0 and splits_ok else 1


if __name__ == "__main__":
    sys.exit(main())
