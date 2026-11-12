"""Features (blueprint section 7).

Every feature at session ``t`` uses only rows at or before ``t`` of a series
indexed by the full session grid. Windows are counted in sessions and all
features are scale-free so tickers can be pooled.

Missing data (DECISIONS.md Q-13, Q-17, Q-18):

- Windows shorter than ``long_window.min_window`` are strict: a window that
  touches a missing bar or a price break gives NaN.
- Longer windows tolerate a small share of missing bars in the middle of the
  window. Both ends of the window must have a bar. The statistic is computed
  on the bars that exist; nothing is filled or shifted.
- A price break is a session whose close-to-close return is not trustworthy
  (an unrecorded provider adjustment at a rights-issue ex-date). That one
  return is treated as missing: it counts as one missing bar, and prices before
  it are rebased so that no feature mixes the two price scales.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def trailing_return(close: pd.Series, window: int) -> pd.Series:
    """Price return over the last ``window`` sessions (NaN if either end is missing)."""
    return close / close.shift(window) - 1.0


def realised_vol(close: pd.Series, window: int, annualisation: int) -> pd.Series:
    """Annualised std of the last ``window`` daily log returns (strict)."""
    log_return = np.log(close).diff()
    return log_return.rolling(window, min_periods=window).std() * np.sqrt(annualisation)


def ma_distance(close: pd.Series, window: int) -> pd.Series:
    """Close relative to its ``window``-session simple moving average, minus 1 (strict)."""
    return close / close.rolling(window, min_periods=window).mean() - 1.0


def rsi(close: pd.Series, window: int) -> pd.Series:
    """RSI with simple averages (Cutler), 0 to 100 (strict).

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
    """Close relative to its ``window``-session high, minus 1 (strict)."""
    return close / close.rolling(window, min_periods=window).max() - 1.0


def relative_volume(volume: pd.Series, short: int, long: int) -> pd.Series:
    """Mean volume over ``short`` sessions divided by mean over ``long`` sessions (strict)."""
    recent = volume.rolling(short, min_periods=short).mean()
    base = volume.rolling(long, min_periods=long).mean()
    return recent / base.where(base > 0)


def break_flags(index: pd.DatetimeIndex, breaks: tuple = ()) -> pd.Series:
    """Boolean series, True on each price-break session."""
    return pd.Series(index.isin(pd.to_datetime(list(breaks))), index=index)


def rebase_across_breaks(close: pd.Series, is_break: pd.Series) -> pd.Series:
    """Rescale prices before each break so the break-day return is removed.

    Prices from the last break onwards are unchanged. The series is only used
    inside ratios, so the common scale does not matter.
    """
    if not is_break.any():
        return close
    log_jump = pd.Series(0.0, index=close.index)
    for day in close.index[is_break.to_numpy()]:
        position = close.index.get_loc(day)
        before = close.iloc[position - 1] if position > 0 else np.nan
        if np.isnan(close.loc[day]) or np.isnan(before):
            raise ValueError(
                f"price break on {day.date()} needs a bar on that session and the one before"
            )
        log_jump.loc[day] = np.log(close.loc[day] / before)
    # sum of the jumps strictly after each session
    later = log_jump[::-1].cumsum()[::-1] - log_jump
    return close * np.exp(later)


def missing_budget(window: int, tolerance: dict[str, Any]) -> int:
    """How many missing bars a window of this nominal length may contain."""
    if window < int(tolerance["min_window"]):
        return 0
    return math.floor(float(tolerance["max_missing_share"]) * window)


def _window_ok(
    present: pd.Series, is_break: pd.Series, lookback: int, budget: int, count_bars: bool
) -> pd.Series:
    """Validity of the window of bars ``t - lookback .. t``.

    Both end bars must exist. Breaks among the ``lookback`` returns of the
    window, plus (when ``count_bars``) missing interior bars, must not exceed
    ``budget``.
    """
    ends = present & present.shift(lookback, fill_value=False)
    used = is_break.astype(float).rolling(lookback, min_periods=lookback).sum()
    if count_bars and lookback > 1:
        absent = (~present).astype(float)
        used = used + absent.rolling(lookback - 1, min_periods=lookback - 1).sum().shift(1)
    return ends & (used <= budget)


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
    breaks: tuple = (),
) -> pd.DataFrame:
    """All features for one asset.

    ``close``, ``volume`` and ``index_close`` share the asset's session grid.
    ``fx_close`` is on the same grid and already lagged to what was known at
    each session's close, or ``None`` for markets without an FX feature (the
    FX columns are then NaN). ``breaks`` lists the asset's price-break dates.
    """
    tolerance = spec["long_window"]
    present = close.notna()
    is_break = break_flags(close.index, breaks)
    price = rebase_across_breaks(close, is_break)
    log_return = np.log(price).diff().mask(is_break)
    scale = np.sqrt(annualisation)
    out: dict[str, pd.Series] = {}

    def ok(lookback: int, window: int, count_bars: bool = True) -> pd.Series:
        return _window_ok(
            present, is_break, lookback, missing_budget(window, tolerance), count_bars
        )

    for w in spec["return_windows"]:
        # Only the two end prices enter, so missing bars in between do not count.
        out[f"ret_{w}"] = (price / price.shift(w) - 1.0).where(ok(w, w, count_bars=False))
    for w in spec["volatility_windows"]:
        out[f"rvol_{w}"] = (log_return.rolling(w, min_periods=2).std() * scale).where(ok(w, w))
    for w in spec["ma_windows"]:
        mean = price.rolling(w, min_periods=1).mean()
        out[f"ma_dist_{w}"] = (price / mean - 1.0).where(ok(w - 1, w))
    w = spec["rsi_window"]
    out[f"rsi_{w}"] = rsi(price, w).where(ok(w, w))
    w = spec["drawdown_window"]
    out[f"drawdown_{w}"] = (price / price.rolling(w, min_periods=1).max() - 1.0).where(ok(w - 1, w))

    rv = spec["relative_volume"]
    short, long = int(rv["short"]), int(rv["long"])
    recent = volume.rolling(short, min_periods=short).mean()
    base = volume.rolling(long, min_periods=1).mean()
    # The provider rescales volume at a break as well, so a volume window must not span one.
    no_break = is_break.astype(float).rolling(long - 1, min_periods=1).sum() == 0
    volume_ok = ok(long - 1, long) & no_break & volume.notna()
    out[f"rel_volume_{short}_{long}"] = (recent / base.where(base > 0)).where(volume_ok)

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
