"""Ridge regression on standardised features."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge


class RidgeModel:
    """Pooled Ridge with scaling fitted on the training window only.

    FX features exist only for Indonesian rows (DECISIONS.md Q-19): their mean
    and standard deviation come from the Indonesian training rows, and rows of
    other markets get zero after scaling. A feature with no variation in the
    training window is set to zero.
    """

    def __init__(self, features: list[str], alpha: float, fx_prefix: str = "fx_") -> None:
        self.features = features
        self.alpha = alpha
        self.fx = [c for c in features if c.startswith(fx_prefix)]
        self.mean: pd.Series | None = None
        self.std: pd.Series | None = None
        self.model: Ridge | None = None

    def _stats(self, train: pd.DataFrame) -> None:
        self.mean = train[self.features].mean()
        self.std = train[self.features].std(ddof=0)
        local = train.loc[train["market"] == "ID", self.fx]
        if self.fx:
            self.mean[self.fx] = local.mean() if len(local) else 0.0
            self.std[self.fx] = local.std(ddof=0) if len(local) else 0.0
        self.mean = self.mean.fillna(0.0)
        self.std = self.std.fillna(0.0)

    def _transform(self, rows: pd.DataFrame) -> np.ndarray:
        usable = self.std > 0
        scaled = (rows[self.features] - self.mean) / self.std.where(usable, 1.0)
        scaled.loc[:, ~usable] = 0.0
        if self.fx:
            scaled.loc[rows["market"] != "ID", self.fx] = 0.0
        if scaled.isna().any().any():
            raise ValueError("Ridge received a missing feature value")
        return scaled.to_numpy(dtype=float)

    def fit(self, train: pd.DataFrame, history: pd.DataFrame) -> None:
        """Fit scaler statistics and coefficients on ``train``."""
        self._stats(train)
        self.model = Ridge(alpha=self.alpha, fit_intercept=True)
        self.model.fit(self._transform(train), train["y"].to_numpy(dtype=float))

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        """Forecasts using the training-window scaler."""
        return self.model.predict(self._transform(rows))
