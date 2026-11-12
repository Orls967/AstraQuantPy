"""Empirical prediction intervals from walk-forward out-of-sample residuals."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_intervals(
    predictions: pd.DataFrame, model: str, level: float, min_prior_years: int
) -> pd.DataFrame:
    """Attach a prediction interval to each test row of one model.

    For test year ``Y`` and each market, the interval is the forecast plus the
    lower and upper empirical quantiles of that model's out-of-sample residuals
    in test years before ``Y``, in the same market. Rows with fewer than
    ``min_prior_years`` earlier test years get no interval. Coverage measured
    on these rows is therefore out of sample too.
    """
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    frame = predictions[["symbol", "market", "test_year", "y", f"pred_{model}"]].copy()
    frame = frame.rename(columns={f"pred_{model}": "pred"})
    frame["residual"] = frame["y"] - frame["pred"]
    frame["lower"] = np.nan
    frame["upper"] = np.nan
    years = sorted(frame["test_year"].unique())
    for position, year in enumerate(years):
        if position < min_prior_years:
            continue
        for market in frame["market"].unique():
            past = frame[(frame["test_year"] < year) & (frame["market"] == market)]["residual"]
            now = (frame["test_year"] == year) & (frame["market"] == market)
            if past.empty or not now.any():
                continue
            frame.loc[now, "lower"] = frame.loc[now, "pred"] + past.quantile(lo_q)
            frame.loc[now, "upper"] = frame.loc[now, "pred"] + past.quantile(hi_q)
    frame["model"] = model
    return frame


def interval_summary(with_intervals: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    """Coverage and mean width of the intervals, per model and optional group."""
    have = with_intervals.dropna(subset=["lower", "upper"]).copy()
    have["covered"] = (have["y"] >= have["lower"]) & (have["y"] <= have["upper"])
    have["width"] = have["upper"] - have["lower"]
    keys = ["model"] if by is None else ["model", by]
    return (
        have.groupby(keys, sort=False)
        .agg(n=("covered", "size"), coverage=("covered", "mean"), mean_width=("width", "mean"))
        .reset_index()
    )
