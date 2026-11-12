"""Naive baselines."""

from __future__ import annotations

import numpy as np
import pandas as pd


class ZeroModel:
    """Always predicts zero."""

    def fit(self, train: pd.DataFrame, history: pd.DataFrame) -> None:
        """Nothing to learn."""

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        """Zeros."""
        return np.zeros(len(rows))


class HistoricalMeanModel:
    """Each symbol's mean label over the training window.

    A symbol with no labelled history in the window falls back to the mean of
    all labels in the window.
    """

    def __init__(self) -> None:
        self.by_symbol: dict[str, float] = {}
        self.overall = float("nan")

    def fit(self, train: pd.DataFrame, history: pd.DataFrame) -> None:
        """Store per-symbol and overall means of the label."""
        self.by_symbol = history.groupby("symbol")["y"].mean().to_dict()
        self.overall = float(history["y"].mean())

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        """The symbol's historical mean."""
        return rows["symbol"].map(self.by_symbol).fillna(self.overall).to_numpy(dtype=float)


class TrailingFeatureModel:
    """Predicts the current value of one feature (trailing realised volatility)."""

    def __init__(self, column: str) -> None:
        self.column = column

    def fit(self, train: pd.DataFrame, history: pd.DataFrame) -> None:
        """Nothing to learn."""

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        """The feature's value at the origin."""
        return rows[self.column].to_numpy(dtype=float)
