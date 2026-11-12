"""Checks on real bar excerpts in ``tests/fixtures`` (always run, no ``data/`` needed)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from astraquant import calendars
from astraquant.config import load_assets, load_settings
from astraquant.data.ingest import PROCESSED_COLUMNS
from astraquant.data.validation import check_split, validate_prices

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "prices"
SETTINGS = load_settings()
ASSETS = {a.symbol: a for a in load_assets()}
SYMBOLS = sorted(p.stem for p in FIXTURES.glob("*.csv"))


def load_fixture(symbol: str) -> pd.DataFrame:
    """Read one fixture file in the processed schema."""
    return pd.read_csv(FIXTURES / f"{symbol}.csv", parse_dates=["date"])


def test_every_configured_split_check_has_a_fixture_in_both_markets():
    checked = {c.symbol for c in SETTINGS.split_checks}
    assert checked <= set(SYMBOLS)
    assert {ASSETS[s].market for s in checked} >= {"US", "ID"}


@pytest.mark.parametrize("check", SETTINGS.split_checks, ids=lambda c: c.symbol)
def test_close_is_split_adjusted_but_not_dividend_adjusted(check):
    result = check_split(
        load_fixture(check.symbol),
        pd.Timestamp(check.date),
        check.ratio,
        SETTINGS.max_abs_daily_return,
    )
    assert result["passed"], result
    assert result["dividends_before_split"] and result["close_differs_from_adj_close"]


@pytest.mark.parametrize("symbol", SYMBOLS)
def test_fixture_matches_schema_and_trading_calendar(symbol):
    bars = load_fixture(symbol)
    asset = ASSETS[symbol]
    assert list(bars.columns) == PROCESSED_COLUMNS
    expected = calendars.sessions(
        asset.calendar,
        bars["date"].min(),
        bars["date"].max(),
        SETTINGS.holidays_for(asset.calendar),
    )
    assert list(bars["date"]) == list(expected)
    issues = validate_prices(
        bars,
        symbol,
        expected,
        max_abs_daily_return=SETTINGS.max_abs_daily_return,
        check_volume=True,
    )
    assert issues.empty, issues
