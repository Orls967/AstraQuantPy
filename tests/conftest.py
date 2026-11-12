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
