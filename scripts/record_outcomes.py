"""Record the realised returns of stored forecasts next to them in the ledger.

Usage:
  python scripts/record_outcomes.py                              # official (after the quarter ends)
  python scripts/record_outcomes.py --dry-run --quarter 2026Q3   # rehearsal ledger only

Run scripts/ingest.py and scripts/build_dataset.py first. Stored forecasts are
never changed; outcomes are appended as new rows.
"""

from __future__ import annotations

import argparse
import json
import sys

import pandas as pd

from astraquant import ledger
from astraquant.config import REPO_ROOT, load_assets, load_settings
from astraquant.outcome_report import render_outcome_report
from astraquant.outcomes import compute_outcomes, join_outcomes
from astraquant.runmeta import run_metadata


def main() -> int:
    """Compute, check, append to the ledger, export and report."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="work on the rehearsal ledger")
    parser.add_argument("--quarter", help="rehearsed quarter, for example 2026Q3 (dry run only)")
    args = parser.parse_args()
    if bool(args.quarter) != args.dry_run:
        parser.error("--dry-run and --quarter must be given together")

    assets = load_assets()
    settings = load_settings()
    cfg, out_cfg = settings.forecast, settings.outcomes
    if args.dry_run:
        base = REPO_ROOT / cfg["dry_run_dir"]
        ledger_path, report_path = base / "ledger.sqlite", base / f"{args.quarter}_outcome.md"
        types = [f"dry_run_{args.quarter}_price_return"]
        title = f"Rehearsal: {args.quarter} realised outcomes"
    else:
        ledger_path = REPO_ROOT / cfg["ledger_path"]
        report_path = REPO_ROOT / out_cfg["report_path"]
        types = [cfg["target_type"], cfg["target_type"] + "_late"]
        title = f"{cfg['quarter']} realised outcomes"
    manifest_path = settings.dataset_dir / "manifest.json"
    for needed in (ledger_path, manifest_path):
        if not needed.exists():
            raise SystemExit(f"{needed} not found")
    dataset = json.loads(manifest_path.read_text(encoding="utf-8"))
    quarterly = pd.read_parquet(settings.dataset_dir / "quarterly.parquet")
    daily = pd.read_parquet(settings.dataset_dir / "daily.parquet")
    through = {a.calendar: dataset["data_through"][a.market] for a in assets if a.role == "target"}
    meta = run_metadata(settings.seed)

    conn = ledger.connect(ledger_path)
    try:
        stored = ledger.read_forecasts(conn)
        stored = stored[stored["target_type"].isin(types)]
        done = set(ledger.read_outcomes(conn)["forecast_id"])
        pending = stored[~stored["forecast_id"].isin(done)]
        if stored.empty:
            print(f"Nothing to record: no stored forecast of type {types} in {ledger_path}")
            return 1
        if pending.empty:
            print("Nothing to record: every stored forecast of this type already has an outcome.")
            return 0

        outcomes, problems = compute_outcomes(
            pending, quarterly, daily, through, float(out_cfg["start_price_tolerance"])
        )
        if meta["git_dirty"] and not args.dry_run:
            problems.append("tracked files have uncommitted changes")
        if problems:
            print("Not recorded:")
            for problem in problems:
                print(f"  - {problem}")
            return 1

        now = pd.Timestamp.now(tz="UTC")
        run_id = now.strftime("%Y%m%dT%H%M%S%fZ")
        run = {
            "run_id": run_id,
            "created_at_utc": now.isoformat(),
            "kind": "dry_run_outcome" if args.dry_run else "outcome",
            "git_commit": meta["git_commit"],
            "git_dirty": meta["git_dirty"],
            "config_digest": meta["config_digest"],
            "seed": meta["seed"],
            "data_through": dataset["data_through"],
            "note": f"outcomes for {', '.join(types)}; ingest run {dataset['ingest_run_id']}; "
            f"dataset build {dataset['built_at_utc']}",
        }
        records = [
            {**row, "run_id": run_id, "recorded_at_utc": now.isoformat(),
             "git_commit": meta["git_commit"]}
            for row in outcomes.to_dict("records")
        ]  # fmt: skip
        written = ledger.append_outcomes(conn, run, records)
        if not args.dry_run:
            total = ledger.export_outcomes_csv(conn, REPO_ROOT / out_cfg["export_path"])
            print(f"outcome export: {total} rows -> {REPO_ROOT / out_cfg['export_path']}")
        joined = join_outcomes(stored, ledger.read_outcomes(conn))
    finally:
        conn.close()

    # The frozen forecast is the first run of the official type (or of the rehearsed type).
    primary = joined[joined["target_type"] == types[0]]
    frozen = primary[primary["run_id"] == primary["run_id"].min()].reset_index(drop=True)
    if frozen.empty:
        frozen = joined[joined["run_id"] == joined["run_id"].min()].reset_index(drop=True)
    other_runs = stored["run_id"].nunique() - 1
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        render_outcome_report(frozen, run, title, not args.dry_run, other_runs), encoding="utf-8"
    )
    flagged = int(outcomes["start_price_changed"].sum())
    if flagged:
        print(f"WARNING: start price changed for {flagged} forecast(s); see the report.")
    print(f"{written} outcomes appended (run {run_id}) -> {ledger_path}")
    print(f"report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
