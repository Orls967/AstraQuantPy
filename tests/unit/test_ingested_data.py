"""Checks on real ingested data. Skipped when ``data/`` has not been built."""

from __future__ import annotations

import pandas as pd
import pytest

from astraquant.config import load_assets, load_settings
from astraquant.data.validation import check_split

SETTINGS = load_settings()
PRICES = SETTINGS.processed_dir / "prices"
ASSETS = {a.symbol: a for a in load_assets()}

pytestmark = [
    pytest.mark.data,
    pytest.mark.skipif(not PRICES.exists(), reason="run scripts/ingest.py first"),
]


def _load(symbol: str) -> pd.DataFrame:
    return pd.read_parquet(PRICES / f"{ASSETS[symbol].file_stem}.parquet")


def test_split_checks_cover_both_markets():
    markets = {ASSETS[c.symbol].market for c in SETTINGS.split_checks}
    assert {"US", "ID"} <= markets


@pytest.mark.parametrize("check", SETTINGS.split_checks, ids=lambda c: c.symbol)
def test_close_is_split_adjusted_but_not_dividend_adjusted(check):
    result = check_split(
        _load(check.symbol),
        pd.Timestamp(check.date),
        check.ratio,
        SETTINGS.max_abs_daily_return,
    )
    assert result["passed"], result


@pytest.mark.parametrize("symbol", list(ASSETS))
def test_processed_file_is_sorted_unique_and_positive(symbol):
    bars = _load(symbol)
    assert bars["date"].is_monotonic_increasing and bars["date"].is_unique
    assert (bars[["open", "high", "low", "close"]] > 0).all().all()
    assert (bars["date"].dt.day_of_week < 5).all()
