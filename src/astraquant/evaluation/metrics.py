"""Forecast metrics. ``R2_oos`` is the primary metric (blueprint section 8)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def r2_oos(y: np.ndarray, pred: np.ndarray, baseline: np.ndarray) -> float:
    """Out-of-sample R squared against a baseline: ``1 - SSE_model / SSE_baseline``."""
    sse_model = float(((y - pred) ** 2).sum())
    sse_base = float(((y - baseline) ** 2).sum())
    return float("nan") if sse_base == 0 else 1.0 - sse_model / sse_base


def directional_accuracy(y: np.ndarray, pred: np.ndarray) -> float:
    """Share of rows where forecast and outcome have the same sign.

    Rows where either is exactly zero are left out; NaN if none remain (for
    example the zero-return model).
    """
    keep = (y != 0) & (pred != 0)
    return float((np.sign(y[keep]) == np.sign(pred[keep])).mean()) if keep.any() else float("nan")


def summarise(
    predictions: pd.DataFrame,
    models: list[str],
    baseline: str,
    by: str | None = None,
    reference: str | None = None,
) -> pd.DataFrame:
    """Metrics per model, optionally split by a column such as ``market`` or ``symbol``.

    ``r2_oos`` is measured against ``baseline``. With ``reference`` (a second
    baseline, for example the zero-return model) an ``r2_vs_<reference>``
    column is added; it is reported only and never used for selection.
    """
    groups = [("all", predictions)] if by is None else list(predictions.groupby(by, sort=True))
    rows = []
    for key, frame in groups:
        y = frame["y"].to_numpy(float)
        base = frame[f"pred_{baseline}"].to_numpy(float)
        for model in models:
            pred = frame[f"pred_{model}"].to_numpy(float)
            row = {
                (by or "group"): key,
                "model": model,
                "n": len(frame),
                "r2_oos": r2_oos(y, pred, base),
                "mae": float(np.abs(y - pred).mean()),
                "rmse": float(np.sqrt(((y - pred) ** 2).mean())),
                "directional_accuracy": directional_accuracy(y, pred),
            }
            if reference is not None:
                ref = frame[f"pred_{reference}"].to_numpy(float)
                row[f"r2_vs_{reference}"] = r2_oos(y, pred, ref)
            rows.append(row)
    return pd.DataFrame(rows)


def yearly_comparison(predictions: pd.DataFrame, models: list[str], baseline: str) -> pd.DataFrame:
    """Per test year: SSE of each model and whether it beats the baseline."""
    rows = []
    for year, frame in predictions.groupby("test_year", sort=True):
        y = frame["y"].to_numpy(float)
        sse_base = float(((y - frame[f"pred_{baseline}"].to_numpy(float)) ** 2).sum())
        row = {"test_year": int(year), "n": len(frame), f"sse_{baseline}": sse_base}
        for model in models:
            if model == baseline:
                continue
            sse = float(((y - frame[f"pred_{model}"].to_numpy(float)) ** 2).sum())
            row[f"sse_{model}"] = sse
            row[f"beats_{model}"] = sse < sse_base
        rows.append(row)
    return pd.DataFrame(rows)
