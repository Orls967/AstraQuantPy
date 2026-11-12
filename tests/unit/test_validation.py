"""Each data-quality check fires on the defect it targets, and only then."""

from __future__ import annotations

import pandas as pd

from astraquant import calendars
from astraquant.data.ingest import clean_bars
from astraquant.data.validation import check_split, validate_prices
from tests.conftest import make_raw

SESSIONS = calendars.sessions("XNYS", "2024-03-01", "2024-03-28")
CUTOFF = SESSIONS[-1]


def _bars(us_asset, raw=None) -> pd.DataFrame:
    raw = make_raw(SESSIONS) if raw is None else raw
    return clean_bars(raw, us_asset, CUTOFF, SESSIONS)[0]


def _checks(bars, **kwargs) -> set[str]:
    params = {"max_abs_daily_return": 0.25, "check_volume": True} | kwargs
    return set(validate_prices(bars, "TEST", SESSIONS, **params)["check"])


def test_clean_data_has_no_issues(us_asset):
    assert _checks(_bars(us_asset)) == set()


def test_duplicate_date(us_asset):
    bars = _bars(us_asset)
    bars = pd.concat([bars, bars.iloc[[3]]], ignore_index=True)
    assert "duplicate_date" in _checks(bars)


def test_missing_session_is_flagged_not_filled(us_asset):
    raw = make_raw(SESSIONS).drop(index=make_raw(SESSIONS).index[5])
    bars = _bars(us_asset, raw)
    assert len(bars) == len(SESSIONS) - 1
    issues = validate_prices(bars, "TEST", SESSIONS, max_abs_daily_return=0.25, check_volume=True)
    missing = issues[issues["check"] == "missing_session"]
    assert list(missing["date"]) == [SESSIONS[5]]


def test_bar_with_volume_on_closed_day_is_kept_and_flagged(us_asset):
    saturday = pd.DatetimeIndex(["2024-03-09"])
    raw = pd.concat([make_raw(SESSIONS), make_raw(saturday)]).sort_index()
    bars, counts = clean_bars(raw, us_asset, CUTOFF, SESSIONS)
    assert counts["dropped_closed_day"] == 0
    assert "unexpected_bar" in _checks(bars)


def test_zero_volume_placeholder_on_closed_day_is_dropped(us_asset):
    placeholder = make_raw(pd.DatetimeIndex(["2024-03-09"]))
    placeholder["Volume"] = 0
    raw = pd.concat([make_raw(SESSIONS), placeholder]).sort_index()
    bars, counts = clean_bars(raw, us_asset, CUTOFF, SESSIONS)
    assert counts["dropped_closed_day"] == 1
    assert pd.Timestamp("2024-03-09") not in set(bars["date"])
    assert _checks(bars) == set()


def test_non_positive_price_and_zero_volume(us_asset):
    bars = _bars(us_asset)
    bars.loc[2, "low"] = 0.0
    bars.loc[4, "volume"] = 0
    found = _checks(bars)
    assert {"non_positive_price", "zero_volume"} <= found
    assert "zero_volume" not in _checks(bars, check_volume=False)


def test_jump_without_split_is_a_warning(us_asset):
    bars = _bars(us_asset)
    bars.loc[10:, ["open", "high", "low", "close"]] *= 2.0
    issues = validate_prices(bars, "TEST", SESSIONS, max_abs_daily_return=0.25, check_volume=True)
    assert list(issues["check"]) == ["jump"]
    assert list(issues["date"]) == [bars.loc[10, "date"]]


def test_unadjusted_split_is_an_error(us_asset):
    """A 10:1 split left unadjusted in close shows up as a -90% day with a split."""
    bars = _bars(us_asset)
    bars.loc[10:, ["open", "high", "low", "close"]] /= 10.0
    bars.loc[10, "stock_splits"] = 10.0
    issues = validate_prices(bars, "TEST", SESSIONS, max_abs_daily_return=0.25, check_volume=True)
    assert set(issues["check"]) == {"split_discontinuity"}
    assert set(issues["severity"]) == {"error"}


def test_check_split_passes_for_adjusted_and_fails_for_unadjusted(us_asset):
    bars = _bars(us_asset)
    bars.loc[10, "stock_splits"] = 10.0
    bars.loc[3, "dividends"] = 0.5
    day = bars.loc[10, "date"]
    good = check_split(bars, day, 10, 0.25)
    assert good["passed"] and good["implied_unadjusted_prev_close"] == bars.loc[9, "close"] * 10

    unadjusted = bars.copy()
    unadjusted.loc[10:, "close"] /= 10.0
    assert not check_split(unadjusted, day, 10, 0.25)["passed"]

    dividend_adjusted = bars.copy()
    dividend_adjusted["adj_close"] = dividend_adjusted["close"]
    assert not check_split(dividend_adjusted, day, 10, 0.25)["passed"]

    assert not check_split(bars, day, 4, 0.25)["passed"]


def test_zero_volume_bar_on_a_session_is_treated_as_missing_for_targets(us_asset):
    """Q-13: a stale provider row is dropped, so the session shows up as missing."""
    raw = make_raw(SESSIONS)
    raw.iloc[6, raw.columns.get_loc("Volume")] = 0
    bars, counts = clean_bars(raw, us_asset, CUTOFF, SESSIONS)
    assert counts["dropped_stale"] == 1 and counts["dropped_closed_day"] == 0
    assert SESSIONS[6] not in set(bars["date"])
    assert _checks(bars) == {"missing_session"}


def test_zero_volume_is_not_stale_for_context_series(us_asset):
    from dataclasses import replace

    raw = make_raw(SESSIONS)
    raw["Volume"] = 0
    bars, counts = clean_bars(raw, replace(us_asset, role="context"), CUTOFF, SESSIONS)
    assert counts["dropped_stale"] == 0 and len(bars) == len(SESSIONS)


def test_configured_exclusion_drops_only_that_bar(us_asset):
    bars, counts = clean_bars(make_raw(SESSIONS), us_asset, CUTOFF, SESSIONS, (SESSIONS[3].date(),))
    assert counts["dropped_excluded"] == 1
    assert SESSIONS[3] not in set(bars["date"]) and len(bars) == len(SESSIONS) - 1
