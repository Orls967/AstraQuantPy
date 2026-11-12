"""Target builders: hand-checked values and calendar-based dates."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from astraquant import calendars, targets
from astraquant.config import load_settings

SETTINGS = load_settings()
GRID = calendars.sessions("XNYS", "2024-03-01", "2024-03-28")


def test_forward_return_values_and_tail():
    close = pd.Series(np.arange(100.0, 100.0 + len(GRID)), index=GRID)
    got = targets.forward_return(close, 5)
    assert got.iloc[0] == pytest.approx(105 / 100 - 1)
    assert got.iloc[3] == pytest.approx(108 / 103 - 1)
    assert got.iloc[-5:].isna().all() and got.iloc[:-5].notna().all()


def test_forward_return_is_nan_when_either_end_is_missing_and_is_not_shifted():
    close = pd.Series(np.arange(100.0, 100.0 + len(GRID)), index=GRID)
    full = targets.forward_return(close, 5)
    gappy = close.copy()
    gappy.iloc[8] = np.nan
    got = targets.forward_return(gappy, 5)
    assert np.isnan(got.iloc[3]) and np.isnan(got.iloc[8])
    others = [i for i in range(len(GRID) - 5) if i not in (3, 8)]
    assert got.iloc[others].equals(full.iloc[others])


def test_forward_realised_vol_matches_manual_calculation():
    rng = np.random.default_rng(1)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, len(GRID)))), index=GRID)
    got = targets.forward_realised_vol(close, 5, 252)
    log_returns = np.log(close).diff()
    manual = log_returns.iloc[3:8].std(ddof=1) * np.sqrt(252)  # sessions t+1..t+5 for t=2
    assert got.iloc[2] == pytest.approx(manual)
    assert got.iloc[-5:].isna().all()


def test_forward_realised_vol_needs_every_return_in_the_window():
    close = pd.Series(np.linspace(100, 120, len(GRID)), index=GRID)
    close.iloc[10] = np.nan
    got = targets.forward_realised_vol(close, 5, 252)
    # returns at positions 10 and 11 are missing, so origins 5..10 are NaN
    assert got.iloc[5:11].isna().all()
    assert got.iloc[:5].notna().all() and got.iloc[11:-5].notna().all()


@pytest.mark.parametrize("code", ["XNYS", "XIDX"])
@pytest.mark.parametrize("horizon", [5, 20, 60])
def test_target_end_date_counts_exchange_sessions(code, horizon):
    grid = calendars.sessions(code, "2025-10-01", "2026-06-30", SETTINGS.holidays_for(code))
    end = targets.target_end_date(grid, horizon)
    assert list(end.iloc[:-horizon]) == list(grid[horizon:])
    assert end.iloc[-horizon:].isna().all()


def test_idx_horizon_skips_the_2026_lebaran_closure():
    grid = calendars.sessions("XIDX", "2026-03-01", "2026-04-30", SETTINGS.holidays_for("XIDX"))
    end = targets.target_end_date(grid, 5)
    # 5 sessions after Mon 16 March 2026: 17, then closed 18-24, then 25, 26, 27, 30.
    assert end[pd.Timestamp("2026-03-16")] == pd.Timestamp("2026-03-30")


@pytest.mark.parametrize("code", ["XNYS", "XIDX"])
def test_q1_2027_quarter_boundaries_match_the_confirmed_dates(code):
    pinned = SETTINGS.targets["q1_2027"][code]
    bounds = targets.quarter_boundaries(
        code, pd.Timestamp("2027-01-01"), pd.Timestamp("2027-03-31"), SETTINGS.holidays_for(code)
    )
    assert list(bounds["quarter"]) == ["2027Q1"]
    row = bounds.iloc[0]
    assert row["target_start_date"] == pd.Timestamp(pinned["start"])
    assert row["target_end_date"] == pd.Timestamp(pinned["end"])
    assert row["n_sessions"] == pinned["sessions"]


@pytest.mark.parametrize("code", ["XNYS", "XIDX"])
def test_quarter_boundaries_are_true_last_sessions_and_chain(code):
    holidays = SETTINGS.holidays_for(code)
    bounds = targets.quarter_boundaries(
        code, pd.Timestamp("2010-01-01"), pd.Timestamp("2027-03-31"), holidays
    )
    assert len(bounds) == 69
    grid = calendars.sessions(code, "2009-12-01", "2027-04-30", holidays)
    for row in bounds.itertuples():
        period = pd.Period(row.quarter, freq="Q")
        after_end = grid[grid > row.target_end_date][0]
        after_start = grid[grid > row.target_start_date][0]
        assert row.target_end_date in grid and row.target_start_date in grid
        assert pd.Period(row.target_end_date, freq="Q") == period
        assert pd.Period(after_end, freq="Q") == period + 1
        assert pd.Period(after_start, freq="Q") == period
    # each quarter starts where the previous one ended
    assert list(bounds["target_start_date"][1:]) == list(bounds["target_end_date"][:-1])


def test_quarterly_returns_use_boundary_closes_only():
    grid = calendars.sessions("XNYS", "2023-12-01", "2024-07-31")
    close = pd.Series(np.arange(1.0, len(grid) + 1), index=grid)
    bounds = targets.quarter_boundaries(
        "XNYS", pd.Timestamp("2024-01-01"), pd.Timestamp("2024-06-30")
    )
    out = targets.quarterly_returns(close, bounds)
    q1 = out.iloc[0]
    assert q1["target_start_date"] == pd.Timestamp("2023-12-29")
    assert q1["target_end_date"] == pd.Timestamp("2024-03-28")  # 29 March is Good Friday
    expected = close[pd.Timestamp("2024-03-28")] / close[pd.Timestamp("2023-12-29")] - 1
    assert q1["q_return"] == pytest.approx(expected)
    assert q1["target_start_price"] == close[pd.Timestamp("2023-12-29")]

    close[pd.Timestamp("2024-03-28")] = np.nan
    out = targets.quarterly_returns(close, bounds)
    assert np.isnan(out.iloc[0]["q_return"])  # Q1 lost its end price
    assert np.isnan(out.iloc[1]["q_return"])  # Q2 lost its start price
