"""Run the fixed walk-forward evaluation for every target.

Usage: python scripts/evaluate.py   (run scripts/build_dataset.py first)
"""

from __future__ import annotations

import json
import sys

import pandas as pd

from astraquant import calendars
from astraquant.config import REPO_ROOT, load_assets, load_settings
from astraquant.evaluation import protocol
from astraquant.evaluation.report import render_evaluation_report, results_table
from astraquant.evaluation.samples import daily_samples, origin_grid, quarterly_samples
from astraquant.runmeta import run_metadata


def main() -> int:
    """Evaluate all targets and write predictions, tables and the report."""
    assets = load_assets()
    settings = load_settings()
    cfg = settings.evaluation
    if not (settings.dataset_dir / "manifest.json").exists():
        raise SystemExit("no dataset found; run scripts/build_dataset.py first")
    dataset = json.loads((settings.dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    daily = pd.read_parquet(settings.dataset_dir / "daily.parquet")
    quarterly = pd.read_parquet(settings.dataset_dir / "quarterly.parquet")

    features = protocol.model_features(settings)
    fx = protocol.fx_markets(settings)
    codes = {a.market: a.calendar for a in assets if a.role == "target"}
    sessions = {
        market: calendars.sessions(
            code, settings.start_date, daily["date"].max(), settings.holidays_for(code)
        )
        for market, code in codes.items()
    }
    years = list(range(settings.start_date.year + 1, int(daily["date"].dt.year.max()) + 1))
    cutoffs = protocol.fold_cutoffs(assets, settings, years)

    out_dir = REPO_ROOT / cfg["output_dir"]
    report_dir = REPO_ROOT / cfg["report_dir"]
    results = {}
    primary = ""
    for target in protocol.target_specs(settings):
        if target.horizon is None:
            samples = quarterly_samples(quarterly, features, fx)
            primary = target.name
        else:
            grids = {m: origin_grid(s, target.horizon) for m, s in sessions.items()}
            samples = daily_samples(daily, target.name, target.horizon, grids, features, fx)
        plan = protocol.model_plan(target, settings)
        result = protocol.evaluate_target(samples, plan, cutoffs, settings)
        results[target.name] = result
        target_dir = out_dir / target.name
        target_dir.mkdir(parents=True, exist_ok=True)
        for part in ("predictions", "folds", "intervals"):
            result[part].to_parquet(target_dir / f"{part}.parquet", index=False)
        chosen = result["selection"]["selected"]
        print(f"{target.name:<11} test rows {len(result['predictions']):>5}  selected: {chosen}")

    manifest = {
        "run_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "dataset_built_at_utc": dataset["built_at_utc"],
        "dataset_git_commit": dataset["git_commit"],
        "feature_set_version": dataset["feature_set_version"],
        "features": features,
        "source": dataset["source"],
        "data_through": dataset["data_through"],
        "evaluation_spec": cfg,
        "primary_target": primary,
        "selection": {name: result["selection"] for name, result in results.items()},
        **run_metadata(settings.seed),
    }
    (out_dir / "results.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )
    report_dir.mkdir(parents=True, exist_ok=True)
    results_table(results).to_csv(report_dir / "results.csv", index=False)
    (report_dir / "summary.md").write_text(
        render_evaluation_report(results, manifest, primary), encoding="utf-8"
    )
    print(f"published model (rule on {primary}): {results[primary]['selection']['selected']}")
    print(f"report: {report_dir / 'summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
