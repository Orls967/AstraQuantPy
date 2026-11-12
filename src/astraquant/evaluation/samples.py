"""Turn the research datasets into walk-forward sample frames.

A sample frame has one row per forecast origin with the columns the
walk-forward needs: ``symbol, market, origin_date, target_end_date,
test_year, y, complete`` plus the model features.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

KEYS = ["symbol", "market", "origin_date", "target_end_date", "test_year", "y", "complete"]


def complete_mask(
    frame: pd.DataFrame, features: list[str], fx_markets: Iterable[str], fx_prefix: str = "fx_"
) -> pd.Series:
    """Rows with a full feature vector.

    FX features are required only for markets that have an FX series; for the
    other markets they are NaN by design.
    """
    fx = [c for c in features if c.startswith(fx_prefix)]
    common = [c for c in features if c not in fx]
    ok = frame[common].notna().all(axis=1)
    if fx:
        needs_fx = frame["market"].isin(list(fx_markets))
        ok &= ~needs_fx | frame[fx].notna().all(axis=1)
    return ok


def quarterly_samples(
    quarterly: pd.DataFrame, features: list[str], fx_markets: Iterable[str]
) -> pd.DataFrame:
    """Samples for the calendar-quarter return. The test year is the quarter's year."""
    out = quarterly[["symbol", "market", "quarter", *features]].copy()
    out["origin_date"] = quarterly["target_start_date"]
    out["target_end_date"] = quarterly["target_end_date"]
    out["test_year"] = quarterly["quarter"].str[:4].astype(int)
    out["y"] = quarterly["q_return"]
    out["complete"] = complete_mask(out, features, fx_markets)
    return out.reset_index(drop=True)


def origin_grid(sessions: pd.DatetimeIndex, horizon: int) -> pd.DatetimeIndex:
    """Every ``horizon``-th session, so labels of consecutive origins do not overlap."""
    if horizon < 1:
        raise ValueError("horizon must be at least 1 session")
    return sessions[::horizon]


def daily_samples(
    daily: pd.DataFrame,
    target: str,
    horizon: int,
    grids: dict[str, pd.DatetimeIndex],
    features: list[str],
    fx_markets: Iterable[str],
) -> pd.DataFrame:
    """Samples for a forward target at non-overlapping origins.

    ``grids`` maps each market to its origin grid (see ``origin_grid``). The
    test year is the year of the origin.
    """
    parts = [
        daily[(daily["market"] == market) & daily["date"].isin(grid)]
        for market, grid in grids.items()
    ]
    rows = pd.concat(parts)
    out = rows[["symbol", "market", *features]].copy()
    out["origin_date"] = rows["date"]
    out["target_end_date"] = rows[f"target_end_date_{horizon}"]
    out["test_year"] = rows["date"].dt.year
    out["y"] = rows[target]
    out["complete"] = complete_mask(out, features, fx_markets)
    return out.dropna(subset=["target_end_date"]).reset_index(drop=True)
