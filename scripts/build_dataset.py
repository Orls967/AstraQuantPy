"""Build the daily and quarterly research datasets from processed bars.

Usage: python scripts/build_dataset.py   (run scripts/ingest.py first)
"""

from __future__ import annotations

import json
import sys

import pandas as pd

from astraquant.config import load_assets, load_settings
from astraquant.dataset import build_daily, build_quarterly, data_through
from astraquant.dataset_report import render_dataset_report
from astraquant.features import feature_columns
from astraquant.runmeta import run_metadata


def main() -> int:
    """Write the datasets, their manifest and the coverage report."""
    assets = load_assets()
    settings = load_settings()
    prices_dir = settings.processed_dir / "prices"
    if not prices_dir.exists():
        raise SystemExit("no processed prices found; run scripts/ingest.py first")
    prices = {a.symbol: pd.read_parquet(prices_dir / f"{a.file_stem}.parquet") for a in assets}
    ingest = json.loads((settings.processed_dir / "manifest.json").read_text(encoding="utf-8"))

    daily = build_daily(assets, prices, settings)
    quarterly = build_quarterly(daily, assets, settings)

    settings.dataset_dir.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(settings.dataset_dir / "daily.parquet", index=False)
    quarterly.to_parquet(settings.dataset_dir / "quarterly.parquet", index=False)
    manifest = {
        "built_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "feature_set_version": settings.dataset["feature_set_version"],
        "features": feature_columns(settings.features),
        "ingest_run_id": ingest["run_id"],
        "source": ingest["source"],
        "source_note": ingest["source_note"],
        "data_through": data_through(daily),
        "rows": {"daily": len(daily), "quarterly": len(quarterly)},
        "dataset_spec": settings.dataset,
        "feature_spec": settings.features,
        **run_metadata(settings.seed),
    }
    (settings.dataset_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )
    settings.dataset_report_path.parent.mkdir(parents=True, exist_ok=True)
    settings.dataset_report_path.write_text(
        render_dataset_report(daily, quarterly, manifest, settings), encoding="utf-8"
    )
    print(f"daily:     {len(daily):>6} rows -> {settings.dataset_dir / 'daily.parquet'}")
    print(f"quarterly: {len(quarterly):>6} rows -> {settings.dataset_dir / 'quarterly.parquet'}")
    print(f"report:    {settings.dataset_report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
