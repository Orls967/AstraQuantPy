"""Realised outcomes of stored forecasts (blueprint section 9, Milestone 6).

The realised return is the label of the quarterly dataset, so it follows the
same definition as every label the models were evaluated on: split-adjusted
close on the calendar's boundary sessions, NaN if a boundary bar is missing or
a configured price break falls inside the quarter.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_outcomes(
    forecasts: pd.DataFrame,
    quarterly: pd.DataFrame,
    daily: pd.DataFrame,
    data_through: dict[str, str],
    tolerance: float,
) -> tuple[pd.DataFrame, list[str]]:
    """Outcome of each stored forecast, plus the reasons any cannot be computed.

    ``forecasts`` are ledger rows. ``data_through`` maps an exchange code to the
    last completed session in the dataset. If the returned list of problems is
    not empty nothing should be recorded.

    Both prices of the realised return come from the same, current data. A
    stock split during the quarter rescales the whole history, so the start
    price in today's data then differs from the one stored with the forecast.
    That is flagged in ``start_price_changed``; the return itself stays correct.
    """
    close = daily.set_index(["symbol", "date"])["close"]
    rows, problems = [], []
    for fc in forecasts.to_dict("records"):
        ticker = fc["ticker"]
        start, end = pd.Timestamp(fc["target_start_date"]), pd.Timestamp(fc["target_end_date"])
        through = pd.Timestamp(data_through[fc["exchange"]])
        if through < end:
            problems.append(
                f"{ticker}: the quarter has not ended (target end {end.date()}, "
                f"data through {through.date()})"
            )
            continue
        match = quarterly[
            (quarterly["symbol"] == ticker)
            & (quarterly["target_start_date"] == start)
            & (quarterly["target_end_date"] == end)
        ]
        if len(match) != 1:
            problems.append(
                f"{ticker}: the dataset has no quarter from {start.date()} to {end.date()}; "
                "the trading calendar differs from the one the forecast was made with"
            )
            continue
        label = match.iloc[0]
        if pd.isna(label["q_return"]):
            problems.append(
                f"{ticker}: no realised return (a boundary bar is missing or a price break "
                "falls inside the quarter)"
            )
            continue
        realised = float(label["q_return"])
        start_now = float(label["target_start_price"])
        stored = float(fc["target_start_price"])
        rows.append(
            {
                "forecast_id": int(fc["forecast_id"]),
                "target_end_date": end,
                "end_price": float(close.loc[(ticker, end)]),
                "start_price_stored": stored,
                "start_price_now": start_now,
                "start_price_changed": bool(abs(start_now / stored - 1.0) > tolerance),
                "realised_return": realised,
                "error": realised - float(fc["point_estimate"]),
                "inside_interval": bool(fc["interval_lower"] <= realised <= fc["interval_upper"]),
                "data_through_date": through,
            }
        )
    return pd.DataFrame(rows), problems


def join_outcomes(forecasts: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    """Forecast rows with their first recorded outcome (rows without one are dropped)."""
    if forecasts.empty or outcomes.empty:
        return pd.DataFrame()
    first = outcomes.sort_values("outcome_id").drop_duplicates("forecast_id")
    # Forecast columns keep their names; outcome columns that would clash are renamed.
    first = first.drop(columns=["target_end_date"]).rename(
        columns={
            "run_id": "outcome_run_id",
            "git_commit": "outcome_git_commit",
            "data_through_date": "outcome_data_through_date",
        }
    )
    return forecasts.merge(first, on="forecast_id", how="inner", validate="one_to_one")


def outcome_summary(joined: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    """Interval coverage and error of the stored forecast against a zero-return forecast."""
    groups = [("all", joined)] if by is None else list(joined.groupby(by, sort=False))
    rows: list[dict[str, Any]] = []
    for key, part in groups:
        realised = part["realised_return"].to_numpy(float)
        error = part["error"].to_numpy(float)
        point = part["point_estimate"].to_numpy(float)
        sse, sse_zero = float((error**2).sum()), float((realised**2).sum())
        rows.append(
            {
                (by or "group"): key,
                "n": len(part),
                "inside_interval": int(part["inside_interval"].sum()),
                "coverage": float(part["inside_interval"].mean()),
                "nominal": float(part["interval_level"].iloc[0]),
                "mae_forecast": float(np.abs(error).mean()),
                "mae_zero": float(np.abs(realised).mean()),
                "rmse_forecast": float(np.sqrt((error**2).mean())),
                "rmse_zero": float(np.sqrt((realised**2).mean())),
                "r2_vs_zero": float("nan") if sse_zero == 0 else 1.0 - sse / sse_zero,
                "same_sign": int((np.sign(point) == np.sign(realised)).sum()),
            }
        )
    return pd.DataFrame(rows)
