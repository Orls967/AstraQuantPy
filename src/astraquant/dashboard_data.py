"""Read-only data access for the dashboard.

Nothing here writes, fits or downloads. Streamlit is not imported, so these
functions are tested like the rest of the package.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from astraquant import calendars
from astraquant.config import REPO_ROOT, Asset, Settings
from astraquant.evaluation.intervals import interval_summary
from astraquant.evaluation.metrics import summarise, yearly_comparison
from astraquant.outcomes import join_outcomes, outcome_summary

__all__ = ["join_outcomes", "outcome_summary"]

LIMITATIONS = [
    "The 11 names were chosen with hindsight; results carry selection bias and do not "
    "generalise to stocks in general.",
    "Small sample: about four quarterly observations per stock per year, from highly "
    "correlated names.",
    "Prices come from Yahoo Finance through yfinance: unofficial data, prototyping only.",
    "Research and decision support only. Not investment advice.",
]


def _read_json(path: Path) -> dict[str, Any] | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def read_ledger(path: Path) -> pd.DataFrame:
    """All forecasts in a ledger file, opened read-only. Empty if the file is absent."""
    if not path.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return pd.read_sql_query("SELECT * FROM forecasts ORDER BY forecast_id", conn)
    finally:
        conn.close()


def read_outcomes(path: Path) -> pd.DataFrame:
    """All recorded outcomes in a ledger file, opened read-only.

    Empty if the file is absent or was created before outcomes existed.
    """
    if not path.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return pd.read_sql_query("SELECT * FROM outcomes ORDER BY outcome_id", conn)
    except pd.errors.DatabaseError:
        return pd.DataFrame()
    finally:
        conn.close()


def load_outcomes(settings: Settings, rehearsal: bool = False) -> pd.DataFrame:
    """Recorded outcomes from the ledger, or from the rehearsal database."""
    cfg = settings.forecast
    if rehearsal:
        return read_outcomes(REPO_ROOT / cfg["dry_run_dir"] / "ledger.sqlite")
    return read_outcomes(REPO_ROOT / cfg["ledger_path"])


def load_forecasts(settings: Settings, rehearsal: bool = False) -> pd.DataFrame:
    """Stored forecasts from the ledger, or from the rehearsal database."""
    cfg = settings.forecast
    if rehearsal:
        return read_ledger(REPO_ROOT / cfg["dry_run_dir"] / "ledger.sqlite")
    return read_ledger(REPO_ROOT / cfg["ledger_path"])


def run_summary(forecasts: pd.DataFrame) -> pd.DataFrame:
    """One row per stored run, oldest first."""
    if forecasts.empty:
        return pd.DataFrame()
    return (
        forecasts.groupby("run_id", sort=True)
        .agg(
            created_at_utc=("created_at_utc", "first"),
            target_type=("target_type", "first"),
            model=("model_name", "first"),
            forecasts=("ticker", "size"),
            git_commit=("git_commit", "first"),
        )
        .reset_index()
    )


def first_run_of_type(forecasts: pd.DataFrame, target_type: str) -> pd.DataFrame:
    """Rows of the earliest run with this target type: the frozen forecast.

    Later runs of the same type are kept in the ledger but never replace it.
    """
    own = forecasts[forecasts["target_type"] == target_type]
    if own.empty:
        return own
    return own[own["run_id"] == own["run_id"].min()].reset_index(drop=True)


def load_evaluation(settings: Settings) -> dict[str, Any] | None:
    """The stored evaluation manifest (``results.json``), or ``None`` if not run yet."""
    return _read_json(REPO_ROOT / settings.evaluation["output_dir"] / "results.json")


def evaluation_tables(settings: Settings, target: str, selection: dict[str, Any]) -> dict:
    """Metric tables for one target, recomputed from its stored predictions."""
    base = REPO_ROOT / settings.evaluation["output_dir"] / target
    predictions = pd.read_parquet(base / "predictions.parquet")
    intervals = pd.read_parquet(base / "intervals.parquet")
    names = [c.removeprefix("pred_") for c in predictions.columns if c.startswith("pred_")]
    baseline = selection["baseline"]
    return {
        "overall": summarise(predictions, names, baseline).drop(columns="group"),
        "by_market": summarise(predictions, names, baseline, "market"),
        "yearly": yearly_comparison(predictions, names, baseline),
        "coverage": interval_summary(intervals, "market"),
        "folds": pd.read_parquet(base / "folds.parquet"),
        "checks": pd.DataFrame(selection["checks"]),
    }


def freshness(assets: list[Asset], settings: Settings, now: pd.Timestamp) -> pd.DataFrame:
    """Per market: data-through date and how many completed sessions it is behind."""
    manifest = _read_json(settings.processed_dir / "manifest.json")
    if manifest is None:
        return pd.DataFrame()
    codes = {a.market: a.calendar for a in assets if a.role == "target"}
    rows = []
    for market, code in codes.items():
        through = pd.Timestamp(manifest["data_through"][market])
        holidays = settings.holidays_for(code)
        latest = calendars.last_completed_session(code, now, holidays)
        later = calendars.sessions(code, through + pd.Timedelta(days=1), latest, holidays)
        rows.append(
            {
                "market": market,
                "calendar": code,
                "data_through": through,
                "last_completed_session": latest,
                "sessions_behind": len(later),
            }
        )
    return pd.DataFrame(rows)


def pipeline_status(settings: Settings) -> pd.DataFrame:
    """When each pipeline stage last ran and on which commit."""
    stages = {
        "ingest": (settings.processed_dir / "manifest.json", "retrieved_at_utc"),
        "dataset": (settings.dataset_dir / "manifest.json", "built_at_utc"),
        "evaluation": (
            REPO_ROOT / settings.evaluation["output_dir"] / "results.json",
            "run_at_utc",
        ),
    }
    rows = []
    for stage, (path, key) in stages.items():
        manifest = _read_json(path)
        rows.append(
            {
                "stage": stage,
                "last_run_utc": manifest[key][:19] if manifest else "never",
                "git_commit": manifest["git_commit"][:7] if manifest else "",
                "config_digest": manifest["config_digest"] if manifest else "",
            }
        )
    return pd.DataFrame(rows)


def quality_summary(settings: Settings) -> pd.DataFrame:
    """Counts of data-quality issues by check and severity from the last ingest."""
    path = settings.processed_dir / "quality_issues.parquet"
    if not path.exists():
        return pd.DataFrame()
    issues = pd.read_parquet(path)
    return issues.groupby(["severity", "check"]).size().rename("issues").reset_index()
