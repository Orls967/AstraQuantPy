"""Price providers. The pipeline depends on the protocol, not on yfinance."""

from __future__ import annotations

import time
from datetime import date
from typing import Protocol

import pandas as pd

# Columns every provider must return, indexed by a ``Date`` DatetimeIndex.
RAW_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
    "Volume",
    "Dividends",
    "Stock Splits",
]


class PriceProvider(Protocol):
    """Source of daily bars."""

    name: str

    def fetch(self, symbol: str, start: date) -> pd.DataFrame:
        """Return daily bars from ``start`` to the latest available bar."""
        ...

    def version(self) -> str:
        """Provider library version, recorded in the run manifest."""
        ...


class YFinanceProvider:
    """Daily bars from Yahoo Finance through ``yfinance`` (unofficial source).

    ``auto_adjust=False`` keeps ``Close`` split-adjusted but not
    dividend-adjusted, which is the price-return series the project targets.
    """

    name = "yfinance"

    def __init__(self, max_retries: int = 3, pause_seconds: float = 1.0) -> None:
        self.max_retries = max_retries
        self.pause_seconds = pause_seconds

    def version(self) -> str:
        """Installed yfinance version."""
        import yfinance

        return yfinance.__version__

    def fetch(self, symbol: str, start: date) -> pd.DataFrame:
        """Download daily bars; raises if the provider returns nothing usable."""
        import yfinance

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                frame = yfinance.Ticker(symbol).history(
                    start=start.isoformat(),
                    interval="1d",
                    auto_adjust=False,
                    actions=True,
                    repair=False,
                )
                missing = [c for c in RAW_COLUMNS if c not in frame.columns]
                if frame.empty or missing:
                    raise ValueError(f"empty frame or missing columns {missing}")
                time.sleep(self.pause_seconds)
                return frame[RAW_COLUMNS]
            except Exception as error:  # noqa: BLE001 - retried, then re-raised
                last_error = error
                time.sleep(self.pause_seconds * attempt)
        raise RuntimeError(f"{symbol}: download failed after {self.max_retries} attempts") from (
            last_error
        )
