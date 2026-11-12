"""Store the calendar-quarter forecast in the append-only ledger and write the report.

Usage:
  python scripts/forecast.py                              # official run (after the origin close)
  python scripts/forecast.py --dry-run --quarter 2026Q4   # rehearsal, never touches the ledger

Run scripts/ingest.py, scripts/build_dataset.py and scripts/evaluate.py first.
"""

from __future__ import annotations

import argparse
import json
import sys

import pandas as pd

from astraquant import ledger
from astraquant.config import REPO_ROOT, load_assets, load_settings
from astraquant.forecast import forecast_quarter, is_late, readiness_problems
from astraquant.forecast_report import render_forecast_report
from astraquant.runmeta import run_metadata


def main() -> int:
    """Forecast, check, append to the ledger, export and report."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="rehearse outside the ledger")
    parser.add_argument("--quarter", help="quarter to rehearse, for example 2026Q4 (dry run only)")
    args = parser.parse_args()
    if args.quarter and not args.dry_run:
        parser.error("--quarter is only allowed together with --dry-run")

    assets = load_assets()
    settings = load_settings()
    cfg = settings.forecast
    quarter = args.quarter or cfg["quarter"]
    eval_dir = REPO_ROOT / settings.evaluation["output_dir"]
    for needed in (settings.dataset_dir / "manifest.json", eval_dir / "results.json"):
        if not needed.exists():
            raise SystemExit(f"{needed} not found; run build_dataset.py and evaluate.py first")
    dataset = json.loads((settings.dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    evaluation = json.loads((eval_dir / "results.json").read_text(encoding="utf-8"))
    primary = evaluation["primary_target"]
    quarterly = pd.read_parquet(settings.dataset_dir / "quarterly.parquet")
    predictions = pd.read_parquet(eval_dir / primary / "predictions.parquet")
    intervals = pd.read_parquet(eval_dir / primary / "intervals.parquet")
    meta = run_metadata(settings.seed)

    forecasts = forecast_quarter(
        quarterly, predictions, evaluation["selection"][primary], assets, settings, quarter
    )

    problems = []
    if evaluation["dataset_built_at_utc"] != dataset["built_at_utc"]:
        problems.append("the evaluation was run on a different dataset build; rerun evaluate.py")
    if evaluation["config_digest"] != meta["config_digest"]:
        problems.append("the config changed since the evaluation; rerun evaluate.py")
    if not args.dry_run:
        if meta["git_dirty"]:
            problems.append("tracked files have uncommitted changes")
        problems += readiness_problems(forecasts, settings, settings.targets[cfg["target_key"]])
    elif forecasts["target_start_price"].isna().any():
        problems.append("a ticker has no closing price on the origin session")
    if problems:
        print("Not stored:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    late = is_late(forecasts, dataset["data_through"])
    if args.dry_run:
        target_type = f"dry_run_{quarter}_price_return"
        base = REPO_ROOT / cfg["dry_run_dir"]
        ledger_path, report_path = base / "ledger.sqlite", base / f"{quarter}.md"
        title = f"Rehearsal: {quarter} price-return forecast"
    else:
        target_type = cfg["target_type"] + ("_late" if late else "")
        ledger_path, report_path = REPO_ROOT / cfg["ledger_path"], REPO_ROOT / cfg["report_path"]
        title = f"{quarter} price-return forecast"

    now = pd.Timestamp.now(tz="UTC")
    run_id = now.strftime("%Y%m%dT%H%M%S%fZ")
    run = {
        "run_id": run_id,
        "created_at_utc": now.isoformat(),
        "kind": "dry_run" if args.dry_run else "official",
        "git_commit": meta["git_commit"],
        "git_dirty": meta["git_dirty"],
        "config_digest": meta["config_digest"],
        "seed": meta["seed"],
        "data_through": dataset["data_through"],
        "note": f"{quarter}; evaluation run {evaluation['run_at_utc']}; "
        f"model {forecasts['model_name'].iloc[0]} {forecasts.attrs['params']}",
    }
    records = []
    for row in forecasts.to_dict("records"):
        records.append(
            {
                **row,
                "run_id": run_id,
                "target_type": target_type,
                "data_through_date": dataset["data_through"][row["market"]],
                "model_version": str(cfg["model_version"]),
                "feature_set_version": dataset["feature_set_version"],
                "git_commit": meta["git_commit"],
                "created_at_utc": now.isoformat(),
            }
        )

    conn = ledger.connect(ledger_path)
    try:
        written = ledger.append_run(conn, run, records)
        stored = ledger.read_forecasts(conn, run_id)
        if not args.dry_run:
            total = ledger.export_csv(conn, REPO_ROOT / cfg["export_path"])
            print(f"ledger export: {total} rows -> {REPO_ROOT / cfg['export_path']}")
    finally:
        conn.close()

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_run = {**run, "cutoff": forecasts.attrs["cutoff"].date().isoformat()}
    report_path.write_text(
        render_forecast_report(
            stored, report_run, evaluation, predictions, intervals, title, not args.dry_run
        ),
        encoding="utf-8",
    )
    if late and not args.dry_run:
        print("WARNING: data extends past the origin; stored with the late target type.")
    print(f"{written} forecasts appended as {target_type} (run {run_id}) -> {ledger_path}")
    print(f"report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
