"""LightGBM regressor. Missing feature values are passed through as NaN."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor


class LightGBMModel:
    """Pooled gradient-boosted trees, single-threaded and deterministic."""

    def __init__(self, features: list[str], seed: int, **params: Any) -> None:
        self.features = features
        self.model = LGBMRegressor(
            objective="regression",
            random_state=seed,
            deterministic=True,
            force_row_wise=True,
            num_threads=1,
            verbose=-1,
            **params,
        )

    def fit(self, train: pd.DataFrame, history: pd.DataFrame) -> None:
        """Fit on ``train``."""
        self.model.fit(train[self.features].to_numpy(dtype=float), train["y"].to_numpy(float))

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        """Forecasts."""
        return self.model.predict(rows[self.features].to_numpy(dtype=float))
