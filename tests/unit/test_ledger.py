"""The forecast ledger is append-only and stores full metadata."""

from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from astraquant import ledger


def _run(run_id: str = "r1") -> dict:
    return {
        "run_id": run_id,
        "created_at_utc": "2026-12-31T22:00:00+00:00",
        "kind": "official",
        "git_commit": "abc123",
        "git_dirty": False,
        "config_digest": "d1",
        "seed": 1,
        "data_through": {"US": "2026-12-31", "ID": "2026-12-30"},
        "note": "test",
    }


def _forecast(run_id: str = "r1", ticker: str = "AAA", **changes) -> dict:
    row = {
        "run_id": run_id,
        "ticker": ticker,
        "exchange": "XNYS",
        "currency": "USD",
        "target_type": "q1_2027_price_return",
        "forecast_origin_date": pd.Timestamp("2026-12-31"),
        "data_through_date": "2026-12-31",
        "target_start_date": pd.Timestamp("2026-12-31"),
        "target_start_price": 100.0,
        "target_end_date": pd.Timestamp("2027-03-31"),
        "point_estimate": 0.03,
        "interval_level": 0.8,
        "interval_lower": -0.15,
        "interval_upper": 0.22,
        "model_name": "historical_mean",
        "model_version": "1",
        "feature_set_version": "v2",
        "git_commit": "abc123",
        "created_at_utc": "2026-12-31T22:00:00+00:00",
    }
    return {**row, **changes}


@pytest.fixture
def conn(tmp_path):
    connection = ledger.connect(tmp_path / "ledger" / "test.sqlite")
    yield connection
    connection.close()


def test_append_and_read_back_with_every_blueprint_field(conn):
    assert ledger.append_run(conn, _run(), [_forecast(), _forecast(ticker="BBB")]) == 2
    stored = ledger.read_forecasts(conn)
    assert stored["ticker"].tolist() == ["AAA", "BBB"]
    assert set(ledger.FORECAST_FIELDS) <= set(stored.columns)
    first = stored.iloc[0]
    assert first["forecast_origin_date"] == "2026-12-31"
    assert first["target_end_date"] == "2027-03-31"
    assert first["point_estimate"] == 0.03
    assert stored[ledger.FORECAST_FIELDS].notna().all().all()


def test_update_and_delete_are_refused_by_the_database(conn):
    ledger.append_run(conn, _run(), [_forecast()])
    for statement in (
        "UPDATE forecasts SET point_estimate = 0.5",
        "DELETE FROM forecasts",
        "UPDATE runs SET note = 'x'",
        "DELETE FROM runs",
    ):
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            conn.execute(statement)
    assert ledger.read_forecasts(conn)["point_estimate"].tolist() == [0.03]


def test_the_rule_survives_reopening_with_a_plain_connection(tmp_path):
    path = tmp_path / "test.sqlite"
    first = ledger.connect(path)
    ledger.append_run(first, _run(), [_forecast()])
    first.close()
    plain = sqlite3.connect(path)
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        plain.execute("DELETE FROM forecasts")
    plain.close()


def test_a_second_run_appends_and_never_replaces(conn):
    ledger.append_run(conn, _run("r1"), [_forecast("r1")])
    ledger.append_run(conn, _run("r2"), [_forecast("r2", point_estimate=0.05)])
    stored = ledger.read_forecasts(conn)
    assert stored["point_estimate"].tolist() == [0.03, 0.05]
    assert ledger.read_forecasts(conn, "r2")["run_id"].tolist() == ["r2"]
    with pytest.raises(sqlite3.IntegrityError):
        ledger.append_run(conn, _run("r1"), [_forecast("r1")])  # a run id cannot be reused
    assert len(ledger.read_forecasts(conn)) == 2


def test_incomplete_or_inconsistent_records_are_rejected_whole(conn):
    with pytest.raises(ValueError, match="missing"):
        ledger.append_run(conn, _run(), [_forecast(model_name=None)])
    with pytest.raises(ValueError):
        ledger.append_run(conn, _run(), [])
    with pytest.raises(sqlite3.IntegrityError):  # point estimate outside its interval
        ledger.append_run(conn, _run(), [_forecast(), _forecast(interval_lower=0.10)])
    with pytest.raises(sqlite3.IntegrityError):  # NaN price is stored as NULL and refused
        ledger.append_run(conn, _run(), [_forecast(target_start_price=float("nan"))])
    assert ledger.read_forecasts(conn).empty  # nothing from the failed runs was kept
    assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0


def test_export_writes_the_whole_ledger(conn, tmp_path):
    ledger.append_run(conn, _run(), [_forecast(), _forecast(ticker="BBB")])
    target = tmp_path / "out" / "ledger.csv"
    assert ledger.export_csv(conn, target) == 2
    assert pd.read_csv(target)["ticker"].tolist() == ["AAA", "BBB"]
