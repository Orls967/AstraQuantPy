"""Common model interface.

``fit`` receives two frames from the same training window:

- ``train``: rows with a label and a complete feature vector. Ridge and
  LightGBM learn from these.
- ``history``: every labelled row in the window, complete or not. The
  historical-mean baseline uses these, because it needs no features.

Both frames carry the label in column ``y``. Nothing outside the training
window is ever passed to ``fit``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np
import pandas as pd


class Model(Protocol):
    """A fitted-on-train, predict-on-rows forecaster."""

    def fit(self, train: pd.DataFrame, history: pd.DataFrame) -> None:
        """Learn from the training window."""
        ...

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        """Point forecasts for ``rows``."""
        ...


@dataclass(frozen=True)
class ModelSpec:
    """A named model with an optional hyperparameter grid.

    ``factory`` builds a fresh model from one parameter dict. With more than
    one entry in ``grid`` the walk-forward tunes inside the training window.
    """

    name: str
    factory: Callable[..., Model]
    grid: tuple[dict[str, Any], ...] = field(default_factory=lambda: ({},))
