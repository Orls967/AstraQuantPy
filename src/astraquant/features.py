"""Features (blueprint section 7).

Every feature at session ``t`` uses only rows at or before ``t`` of a series
indexed by the full session grid. Windows are counted in sessions. A window
that touches a missing bar gives NaN; nothing is filled or shifted. All
features are scale-free so tickers can be pooled.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def trailing_return(close: pd.Series, window: int) -> pd.Series:
    """Price return over the last ``window`` sessions."""
    return close / close.shift(window) - 1.0


def realised_vol(close: pd.Series, window: int, annualisation: int) -> pd.Series:
    """Annualised std of the last ``window`` daily log returns."""
    log_return = np.log(close).diff()
    return log_return.rolling(window, min_periods=window).std() * np.sqrt(annualisation)


def ma_distance(close: pd.Series, window: int) -> pd.Series:
    """Close relative to its ``window``-session simple moving average, minus 1."""
    return close / close.rolling(window, min_periods=window).mean() - 1.0


def rsi(close: pd.Series, window: int) -> pd.Series:
    """RSI with simple averages (Cutler), 0 to 100.

    The simple-average form has a finite window, so a missing bar affects
    exactly ``window`` sessions. Wilder's smoothing has infinite memory and
    would carry a gap forward indefinitely. NaN when there was no movement.
    """
    change = close.diff()
    gain = change.clip(lower=0.0).rolling(window, min_periods=window).mean()
    loss = (-change).clip(lower=0.0).rolling(window, min_periods=window).mean()
    total = gain + loss
    return 100.0 * gain / total.where(total > 0)


def drawdown(close: pd.Series, window: int) -> pd.Series:
    """Close relative to its ``window``-session high, minus 1 (zero or negative)."""
    return close / close.rolling(window, min_periods=window).max() - 1.0


def relative_volume(volume: pd.Series, short: int, long: int) -> pd.Series:
    """Mean volume over ``short`` sessions divided by mean over ``long`` sessions."""
    recent = volume.rolling(short, min_periods=short).mean()
    base = volume.rolling(long, min_periods=long).mean()
    return recent / base.where(base > 0)


def feature_columns(spec: dict[str, Any]) -> list[str]:
    """Names of all feature columns for a feature spec, in a fixed order."""
    rv = spec["relative_volume"]
    return [
        *(f"ret_{w}" for w in spec["return_windows"]),
        *(f"rvol_{w}" for w in spec["volatility_windows"]),
        *(f"ma_dist_{w}" for w in spec["ma_windows"]),
        f"rsi_{spec['rsi_window']}",
        f"drawdown_{spec['drawdown_window']}",
        f"rel_volume_{rv['short']}_{rv['long']}",
        *(f"mkt_ret_{w}" for w in spec["market_windows"]),
        *(f"mkt_rvol_{w}" for w in spec["market_windows"]),
        *(f"fx_ret_{w}" for w in spec["fx_windows"]),
    ]


def build_features(
    close: pd.Series,
    volume: pd.Series,
    index_close: pd.Series,
    fx_close: pd.Series | None,
    spec: dict[str, Any],
    annualisation: int,
) -> pd.DataFrame:
    """All features for one asset.

    ``close``, ``volume`` and ``index_close`` share the asset's session grid.
    ``fx_close`` is on the same grid and already lagged to what was known at
    each session's close, or ``None`` for markets without an FX feature (the
    FX columns are then NaN).
    """
    out: dict[str, pd.Series] = {}
    for w in spec["return_windows"]:
        out[f"ret_{w}"] = trailing_return(close, w)
    for w in spec["volatility_windows"]:
        out[f"rvol_{w}"] = realised_vol(close, w, annualisation)
    for w in spec["ma_windows"]:
        out[f"ma_dist_{w}"] = ma_distance(close, w)
    out[f"rsi_{spec['rsi_window']}"] = rsi(close, spec["rsi_window"])
    out[f"drawdown_{spec['drawdown_window']}"] = drawdown(close, spec["drawdown_window"])
    rv = spec["relative_volume"]
    out[f"rel_volume_{rv['short']}_{rv['long']}"] = relative_volume(volume, rv["short"], rv["long"])
    for w in spec["market_windows"]:
        out[f"mkt_ret_{w}"] = trailing_return(index_close, w)
    for w in spec["market_windows"]:
        out[f"mkt_rvol_{w}"] = realised_vol(index_close, w, annualisation)
    for w in spec["fx_windows"]:
        out[f"fx_ret_{w}"] = (
            trailing_return(fx_close, w)
            if fx_close is not None
            else pd.Series(np.nan, index=close.index)
        )
    return pd.DataFrame(out, index=close.index)[feature_columns(spec)]
