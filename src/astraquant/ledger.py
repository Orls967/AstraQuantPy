"""Append-only SQLite forecast ledger (blueprint 3.3).

Rows can be inserted and read. ``UPDATE`` and ``DELETE`` are aborted by
triggers inside the database, so the rule holds for any client, not only for
this module.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

RUN_FIELDS = [
    "run_id",
    "created_at_utc",
    "kind",
    "git_commit",
    "git_dirty",
    "config_digest",
    "seed",
    "data_through",
    "note",
]

FORECAST_FIELDS = [
    "run_id",
    "ticker",
    "exchange",
    "currency",
    "target_type",
    "forecast_origin_date",
    "data_through_date",
    "target_start_date",
    "target_start_price",
    "target_end_date",
    "point_estimate",
    "interval_level",
    "interval_lower",
    "interval_upper",
    "model_name",
    "model_version",
    "feature_set_version",
    "git_commit",
    "created_at_utc",
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    created_at_utc TEXT NOT NULL,
    kind TEXT NOT NULL,
    git_commit TEXT NOT NULL,
    git_dirty INTEGER NOT NULL,
    config_digest TEXT NOT NULL,
    seed INTEGER NOT NULL,
    data_through TEXT NOT NULL,
    note TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS forecasts (
    forecast_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    ticker TEXT NOT NULL,
    exchange TEXT NOT NULL,
    currency TEXT NOT NULL,
    target_type TEXT NOT NULL,
    forecast_origin_date TEXT NOT NULL,
    data_through_date TEXT NOT NULL,
    target_start_date TEXT NOT NULL,
    target_start_price REAL NOT NULL,
    target_end_date TEXT NOT NULL,
    point_estimate REAL NOT NULL,
    interval_level REAL NOT NULL,
    interval_lower REAL NOT NULL,
    interval_upper REAL NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    feature_set_version TEXT NOT NULL,
    git_commit TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    CHECK (interval_lower <= point_estimate AND point_estimate <= interval_upper),
    CHECK (target_start_date < target_end_date)
);
CREATE TRIGGER IF NOT EXISTS forecasts_no_update BEFORE UPDATE ON forecasts
BEGIN SELECT RAISE(ABORT, 'the forecast ledger is append-only'); END;
CREATE TRIGGER IF NOT EXISTS forecasts_no_delete BEFORE DELETE ON forecasts
BEGIN SELECT RAISE(ABORT, 'the forecast ledger is append-only'); END;
CREATE TRIGGER IF NOT EXISTS runs_no_update BEFORE UPDATE ON runs
BEGIN SELECT RAISE(ABORT, 'the run log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS runs_no_delete BEFORE DELETE ON runs
BEGIN SELECT RAISE(ABORT, 'the run log is append-only'); END;
"""


def connect(path: Path) -> sqlite3.Connection:
    """Open the ledger, creating the file, tables and triggers if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    return conn


def _text(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    if isinstance(value, bool):
        return int(value)
    return value


def append_run(
    conn: sqlite3.Connection, run: dict[str, Any], forecasts: list[dict[str, Any]]
) -> int:
    """Append one run and its forecasts in a single transaction.

    Every field of ``RUN_FIELDS`` and ``FORECAST_FIELDS`` must be present.
    Returns the number of forecasts written.
    """
    if not forecasts:
        raise ValueError("a run must contain at least one forecast")
    for name, fields, rows in (
        ("run", RUN_FIELDS, [run]),
        ("forecast", FORECAST_FIELDS, forecasts),
    ):
        for row in rows:
            missing = [f for f in fields if row.get(f) is None]
            if missing:
                raise ValueError(f"{name} record is missing {missing}")
    with conn:
        conn.execute(
            f"INSERT INTO runs ({', '.join(RUN_FIELDS)}) "
            f"VALUES ({', '.join('?' for _ in RUN_FIELDS)})",
            [_text(run[f]) for f in RUN_FIELDS],
        )
        conn.executemany(
            f"INSERT INTO forecasts ({', '.join(FORECAST_FIELDS)}) "
            f"VALUES ({', '.join('?' for _ in FORECAST_FIELDS)})",
            [[_text(row[f]) for f in FORECAST_FIELDS] for row in forecasts],
        )
    return len(forecasts)


def read_forecasts(conn: sqlite3.Connection, run_id: str | None = None) -> pd.DataFrame:
    """All stored forecasts in insertion order, or those of one run."""
    query = "SELECT * FROM forecasts"
    params: tuple[str, ...] = ()
    if run_id is not None:
        query += " WHERE run_id = ?"
        params = (run_id,)
    return pd.read_sql_query(query + " ORDER BY forecast_id", conn, params=params)


def export_csv(conn: sqlite3.Connection, path: Path) -> int:
    """Write the whole ledger to CSV (the copy kept in Git). Returns the row count."""
    frame = read_forecasts(conn)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return len(frame)
