"""Expanding-window walk-forward with yearly test blocks (blueprint section 8).

The input is a ``samples`` frame with one row per forecast origin:

``symbol, market, origin_date, target_end_date, test_year, y, complete`` plus
feature columns. ``complete`` marks rows every model can use.

For test year ``Y`` the cutoff of each market is the last trading session of
year ``Y - 1``:

- test rows: ``test_year == Y``, labelled and complete;
- training rows: labelled, with ``target_end_date <= cutoff``. A training
  label is therefore fully realised before any test origin, which leaves a gap
  of at least ``h`` sessions between the last training origin and the first
  test origin (the embargo), and no training label overlaps the test block.

Hyperparameters are chosen inside the training window by the same scheme: the
last few years of the window are each predicted from the data before them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from astraquant.models.base import ModelSpec

REQUIRED = ["symbol", "market", "origin_date", "target_end_date", "test_year", "y", "complete"]


@dataclass
class Fold:
    """Training and test rows for one test year."""

    year: int
    train: pd.DataFrame
    history: pd.DataFrame
    test: pd.DataFrame


def training_mask(samples: pd.DataFrame, cutoffs: dict[str, pd.Timestamp]) -> pd.Series:
    """Labelled rows whose label was fully realised by their market's cutoff."""
    cutoff = samples["market"].map(cutoffs)
    return samples["y"].notna() & (samples["target_end_date"] <= cutoff)


def make_fold(samples: pd.DataFrame, year: int, cutoffs: dict[str, pd.Timestamp]) -> Fold:
    """Split ``samples`` for one test year given each market's cutoff date."""
    history = samples[training_mask(samples, cutoffs)]
    test = samples[(samples["test_year"] == year) & samples["y"].notna() & samples["complete"]]
    return Fold(year, history[history["complete"]], history, test)


def _sse(model, train, history, test) -> float:
    model.fit(train, history)
    return float(((test["y"].to_numpy(float) - model.predict(test)) ** 2).sum())


def choose_params(
    spec: ModelSpec,
    fold: Fold,
    cutoffs_by_year: dict[int, dict[str, pd.Timestamp]],
    inner_years: int,
    min_inner_train_rows: int,
) -> dict[str, Any]:
    """Pick the grid entry with the lowest validation error inside the training window.

    Each of the last ``inner_years`` years before the test year is predicted
    from the training rows realised before it. Only ``fold.history`` is used.
    """
    if len(spec.grid) == 1:
        return spec.grid[0]
    errors = np.zeros(len(spec.grid))
    used = 0
    for year in range(fold.year - inner_years, fold.year):
        if year not in cutoffs_by_year:
            continue
        inner = make_fold(fold.history, year, cutoffs_by_year[year])
        if len(inner.train) < min_inner_train_rows or inner.test.empty:
            continue
        used += 1
        for i, params in enumerate(spec.grid):
            errors[i] += _sse(spec.factory(**params), inner.train, inner.history, inner.test)
    return spec.grid[int(np.argmin(errors))] if used else spec.grid[0]


def run_walk_forward(
    samples: pd.DataFrame,
    specs: list[ModelSpec],
    test_years: list[int],
    cutoffs_by_year: dict[int, dict[str, pd.Timestamp]],
    inner_years: int,
    min_inner_train_rows: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run every model through the same folds.

    Returns ``(predictions, folds)``. ``predictions`` has one row per test row
    and one ``pred_<model>`` column per model. ``folds`` records the sizes and
    chosen hyperparameters of each fold.
    """
    missing = [c for c in REQUIRED if c not in samples.columns]
    if missing:
        raise ValueError(f"samples is missing columns {missing}")
    outputs, log = [], []
    for year in test_years:
        fold = make_fold(samples, year, cutoffs_by_year[year])
        if fold.test.empty or fold.train.empty:
            continue
        if fold.train["target_end_date"].max() > fold.test["origin_date"].min():
            raise AssertionError(f"{year}: a training label ends after the first test origin")
        out = fold.test[["symbol", "market", "origin_date", "target_end_date", "test_year", "y"]]
        out = out.copy()
        entry: dict[str, Any] = {
            "test_year": year,
            "train_rows": len(fold.train),
            "history_rows": len(fold.history),
            "test_rows": len(fold.test),
            "train_last_label_end": fold.train["target_end_date"].max(),
            "test_first_origin": fold.test["origin_date"].min(),
        }
        for spec in specs:
            params = choose_params(spec, fold, cutoffs_by_year, inner_years, min_inner_train_rows)
            model = spec.factory(**params)
            model.fit(fold.train, fold.history)
            out[f"pred_{spec.name}"] = model.predict(fold.test)
            if len(spec.grid) > 1:
                entry[f"params_{spec.name}"] = str(params)
        outputs.append(out)
        log.append(entry)
    return pd.concat(outputs, ignore_index=True), pd.DataFrame(log)
