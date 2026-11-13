"""Milestone 6: outcomes are append-only and computed from the dataset label."""

from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd
import pytest

from astraquant import dashboard_data, ledger
from astraquant.outcome_report import render_outcome_report
from astraquant.outcomes import compute_outcomes, join_outcomes, outcome_summary
from tests.unit.test_ledger import _forecast, _run

START, END = pd.Timestamp("2026-12-31"), pd.Timestamp("2027-03-31")
THROUGH = {"XNYS": "2027-03-31"}


def _data(end_close: float = 110.0, start_close: float = 100.0, q_return=None):
    quarterly = pd.DataFrame(
        {
            "symbol": ["AAA", "BBB"],
            "target_start_date": [START, START],
            "target_end_date": [END, END],
            "target_start_price": [start_close, 50.0],
            "q_return": [end_close / start_close - 1 if q_return is None else q_return, -0.30],
        }
    )
    daily = pd.DataFrame(
        {
            "symbol": ["AAA", "AAA", "BBB", "BBB"],
            "date": [START, END, START, END],
            "close": [start_close, end_close, 50.0, 35.0],
        }
    )
    return quarterly, daily


@pytest.fixture
def conn(tmp_path):
    connection = ledger.connect(tmp_path / "ledger.sqlite")
    ledger.append_run(
        connection, _run(), [_forecast(), _forecast(ticker="BBB", target_start_price=50.0)]
    )
    yield connection
    connection.close()


def _record(conn, run_id="o1", **data_kwargs) -> int:
    quarterly, daily = _data(**data_kwargs)
    outcomes, problems = compute_outcomes(
        ledger.read_forecasts(conn), quarterly, daily, THROUGH, 1e-4
    )
    assert problems == []
    rows = [
        {**row, "run_id": run_id, "recorded_at_utc": "2027-04-01T00:00:00+00:00",
         "git_commit": "abc123"}
        for row in outcomes.to_dict("records")
    ]  # fmt: skip
    run = {**_run(run_id), "kind": "outcome", "created_at_utc": "2027-04-01T00:00:00+00:00"}
    return ledger.append_outcomes(conn, run, rows)


def test_outcome_values(conn):
    quarterly, daily = _data()
    outcomes, problems = compute_outcomes(
        ledger.read_forecasts(conn), quarterly, daily, THROUGH, 1e-4
    )
    assert problems == []
    a, b = outcomes.iloc[0], outcomes.iloc[1]
    assert a["realised_return"] == pytest.approx(0.10) and a["end_price"] == 110.0
    assert a["error"] == pytest.approx(0.10 - 0.03)
    assert a["inside_interval"] and not a["start_price_changed"]  # interval is -15% to +22%
    assert b["realised_return"] == pytest.approx(-0.30) and not b["inside_interval"]


def test_nothing_is_computed_before_the_quarter_ends(conn):
    quarterly, daily = _data()
    outcomes, problems = compute_outcomes(
        ledger.read_forecasts(conn), quarterly, daily, {"XNYS": "2027-03-30"}, 1e-4
    )
    assert outcomes.empty and len(problems) == 2
    assert all("has not ended" in p for p in problems)


def test_missing_label_and_changed_calendar_are_reported_not_guessed(conn):
    quarterly, daily = _data(q_return=np.nan)
    _, problems = compute_outcomes(ledger.read_forecasts(conn), quarterly, daily, THROUGH, 1e-4)
    assert len(problems) == 1 and "no realised return" in problems[0]
    quarterly["target_end_date"] = pd.Timestamp("2027-03-30")
    _, problems = compute_outcomes(ledger.read_forecasts(conn), quarterly, daily, THROUGH, 1e-4)
    assert len(problems) == 2 and all("trading calendar differs" in p for p in problems)


def test_split_during_the_quarter_is_flagged_and_the_return_stays_right(conn):
    """A 2:1 split halves every historical price in the new data."""
    quarterly, daily = _data(end_close=55.0, start_close=50.0)
    outcomes, problems = compute_outcomes(
        ledger.read_forecasts(conn), quarterly, daily, THROUGH, 1e-4
    )
    a = outcomes.iloc[0]
    assert problems == [] and a["start_price_changed"]
    assert a["start_price_stored"] == 100.0 and a["start_price_now"] == 50.0
    assert a["realised_return"] == pytest.approx(0.10)


def test_outcomes_are_append_only_and_leave_forecasts_untouched(conn):
    before = ledger.read_forecasts(conn)
    assert _record(conn) == 2
    pd.testing.assert_frame_equal(before, ledger.read_forecasts(conn))
    stored = ledger.read_outcomes(conn)
    assert stored["forecast_id"].tolist() == before["forecast_id"].tolist()
    for statement in (
        "UPDATE outcomes SET realised_return = 0",
        "DELETE FROM outcomes",
        "UPDATE forecasts SET point_estimate = 0",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute(statement)
    assert len(ledger.read_outcomes(conn)) == 2


def test_outcome_must_point_at_a_stored_forecast_and_be_complete(conn):
    run = {**_run("o9"), "kind": "outcome"}
    quarterly, daily = _data()
    outcomes, _ = compute_outcomes(ledger.read_forecasts(conn), quarterly, daily, THROUGH, 1e-4)
    row = {**outcomes.iloc[0].to_dict(), "run_id": "o9", "recorded_at_utc": "x",
           "git_commit": "abc"}  # fmt: skip
    with pytest.raises(sqlite3.IntegrityError):
        ledger.append_outcomes(conn, run, [{**row, "forecast_id": 999}])
    with pytest.raises(ValueError, match="missing"):
        ledger.append_outcomes(conn, run, [{**row, "end_price": None}])
    with pytest.raises(ValueError):
        ledger.append_outcomes(conn, run, [])
    assert ledger.read_outcomes(conn).empty  # failed attempts wrote nothing, not even the run
    assert pd.read_sql_query("SELECT * FROM runs", conn)["run_id"].tolist() == ["r1"]


def test_join_summary_report_and_csv(conn, tmp_path):
    _record(conn)
    joined = join_outcomes(ledger.read_forecasts(conn), ledger.read_outcomes(conn))
    assert len(joined) == 2 and joined["run_id"].eq("r1").all()  # forecast run id is kept
    summary = outcome_summary(joined).iloc[0]
    assert summary["n"] == 2 and summary["inside_interval"] == 1 and summary["coverage"] == 0.5
    assert summary["rmse_zero"] == pytest.approx(np.sqrt((0.10**2 + 0.30**2) / 2))
    assert summary["rmse_forecast"] == pytest.approx(np.sqrt((0.07**2 + 0.33**2) / 2))
    assert summary["same_sign"] == 1
    assert outcome_summary(joined, "exchange")["n"].tolist() == [2]

    run = {**_run("o1"), "created_at_utc": "2027-04-01T00:00:00+00:00"}
    official = render_outcome_report(joined, run, "Q1 2027 realised outcomes", True, 0)
    assert "1 of 2 realised returns fell inside the 80% prediction interval" in official
    assert "Outside the interval: BBB." in official and "confidence" not in official.lower()
    assert "REHEARSAL ONLY" in render_outcome_report(joined, run, "x", False, 0)

    assert ledger.export_outcomes_csv(conn, tmp_path / "out" / "outcomes.csv") == 2
    assert len(pd.read_csv(tmp_path / "out" / "outcomes.csv")) == 2


def test_dashboard_reads_outcomes_read_only_and_tolerates_old_ledgers(conn, tmp_path):
    path = tmp_path / "ledger.sqlite"
    assert dashboard_data.read_outcomes(tmp_path / "absent.sqlite").empty
    assert dashboard_data.read_outcomes(path).empty
    _record(conn)
    conn.commit()
    assert len(dashboard_data.read_outcomes(path)) == 2
    old = tmp_path / "old.sqlite"
    legacy = sqlite3.connect(old)
    legacy.execute("CREATE TABLE forecasts (forecast_id INTEGER)")
    legacy.commit()
    legacy.close()
    assert dashboard_data.read_outcomes(old).empty
