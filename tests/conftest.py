"""Shared fixtures. Unit tests never touch the network."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import numpy as np
import pandas as pd
import pytest

from astraquant.config import Asset, Settings, load_settings
from astraquant.data.provider import RAW_COLUMNS


def make_raw(dates: pd.DatetimeIndex, tz: str | None = "America/New_York") -> pd.DataFrame:
    """Provider-shaped frame with a smooth, strictly positive price path."""
    n = len(dates)
    close = 100 + np.arange(n, dtype=float)
    frame = pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Adj Close": close * 0.9,
            "Volume": np.full(n, 1_000, dtype="int64"),
            "Dividends": 0.0,
            "Stock Splits": 0.0,
        },
        index=pd.DatetimeIndex(dates, name="Date"),
    )[RAW_COLUMNS]
    if tz is not None:
        frame.index = frame.index.tz_localize(tz)
    return frame


class FakeProvider:
    """In-memory provider returning prepared frames."""

    name = "fake"

    def __init__(self, frames: dict[str, pd.DataFrame]) -> None:
        self.frames = frames

    def fetch(self, symbol: str, start: date) -> pd.DataFrame:
        """Return the prepared frame for ``symbol``."""
        return self.frames[symbol].copy()

    def version(self) -> str:
        """Fixed version string."""
        return "0.0-test"


@pytest.fixture
def us_asset() -> Asset:
    """A US equity on the NYSE calendar."""
    return Asset("TEST", "Test Corp", "US", "target", "XNYS", "USD", "America/New_York")


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Project settings with all output paths redirected to a temp directory."""
    base = load_settings()
    return replace(
        base,
        start_date=date(2024, 1, 1),
        raw_dir=tmp_path / "raw",
        processed_dir=tmp_path / "processed",
        report_path=tmp_path / "reports" / "data_quality.md",
        split_checks=(),
    )


PANEL_START, PANEL_END = "2019-01-01", "2021-12-31"


def _walk(dates: pd.DatetimeIndex, seed: int, start: float) -> pd.DataFrame:
    """Processed-schema bars following a seeded random walk on the given dates."""
    rng = np.random.default_rng(seed)
    close = start * np.exp(np.cumsum(rng.normal(0.0003, 0.015, len(dates))))
    return pd.DataFrame(
        {
            "date": dates,
            "open": close * 0.999,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "adj_close": close * 0.95,
            "volume": rng.integers(1_000, 5_000, len(dates)).astype("int64"),
            "dividends": 0.0,
            "stock_splits": 0.0,
        }
    )


@pytest.fixture
def panel_assets() -> list[Asset]:
    """Two US names, two Indonesian names and the three context series."""
    us = ("US", "XNYS", "USD", "America/New_York")
    idn = ("ID", "XIDX", "IDR", "Asia/Jakarta")

    def asset(symbol, role, spec):
        market, calendar, currency, tz = spec
        return Asset(symbol, symbol, market, role, calendar, currency, tz)

    return [
        asset("AAA", "target", us),
        asset("BBB", "target", us),
        asset("CCC.JK", "target", idn),
        asset("DDD.JK", "target", idn),
        asset("^GSPC", "context", us),
        asset("^JKSE", "context", idn),
        Asset("IDR=X", "USD/IDR", "FX", "context", None, "IDR", "UTC"),
    ]


@pytest.fixture
def panel(panel_assets) -> dict[str, pd.DataFrame]:
    """Synthetic processed bars for ``panel_assets`` on the real calendars."""
    from astraquant import calendars

    base = load_settings()
    out = {}
    for i, asset in enumerate(panel_assets):
        if asset.calendar is None:
            dates = pd.bdate_range(PANEL_START, PANEL_END)
        else:
            dates = calendars.sessions(
                asset.calendar, PANEL_START, PANEL_END, base.holidays_for(asset.calendar)
            )
        out[asset.symbol] = _walk(dates, seed=100 + i, start=50.0 * (i + 1))
    return out
