"""Feature functions: hand-checked values and strict missing-bar behaviour."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from astraquant import calendars, features
from astraquant.config import load_settings

SETTINGS = load_settings()
GRID = calendars.sessions("XNYS", "2024-01-02", "2024-03-28")
RNG = np.random.default_rng(7)
CLOSE = pd.Series(100 * np.exp(np.cumsum(RNG.normal(0, 0.01, len(GRID)))), index=GRID)


def test_trailing_return():
    got = features.trailing_return(CLOSE, 5)
    assert got.iloc[5] == pytest.approx(CLOSE.iloc[5] / CLOSE.iloc[0] - 1)
    assert got.iloc[:5].isna().all()


def test_realised_vol_matches_manual_and_needs_full_window():
    got = features.realised_vol(CLOSE, 20, 252)
    manual = np.log(CLOSE).diff().iloc[1:21].std(ddof=1) * np.sqrt(252)
    assert got.iloc[20] == pytest.approx(manual)
    assert got.iloc[:20].isna().all()


def test_ma_distance_and_drawdown():
    assert features.ma_distance(CLOSE, 10).iloc[9] == pytest.approx(
        CLOSE.iloc[9] / CLOSE.iloc[:10].mean() - 1
    )
    dd = features.drawdown(CLOSE, 10)
    assert dd.iloc[9] == pytest.approx(CLOSE.iloc[9] / CLOSE.iloc[:10].max() - 1)
    assert (dd.dropna() <= 0).all()


def test_rsi_simple_average_form():
    close = pd.Series([10.0, 11, 12, 11, 13, 13, 12], index=GRID[:7])
    # changes: +1 +1 -1 +2 0 -1 ; last 4 changes: -1 +2 0 -1 -> gains 2, losses 2
    assert features.rsi(close, 4).iloc[6] == pytest.approx(50.0)
    # changes 1..4: +1 +1 -1 +2 -> gains 4, losses 1
    assert features.rsi(close, 4).iloc[4] == pytest.approx(80.0)
    flat = pd.Series(5.0, index=GRID[:7])
    assert features.rsi(flat, 4).isna().all()


def test_relative_volume():
    volume = pd.Series(np.arange(1.0, 31.0), index=GRID[:30])
    got = features.relative_volume(volume, 5, 20)
    assert got.iloc[19] == pytest.approx(np.mean(np.arange(16, 21)) / np.mean(np.arange(1, 21)))
    assert got.iloc[:19].isna().all()


def test_missing_bar_makes_touching_windows_nan_without_shifting():
    """A gap at position 30 blanks exactly the windows that include it."""
    gappy = CLOSE.copy()
    gappy.iloc[30] = np.nan
    full, got = features.trailing_return(CLOSE, 5), features.trailing_return(gappy, 5)
    assert np.isnan(got.iloc[30]) and np.isnan(got.iloc[35])
    keep = [i for i in range(5, len(GRID)) if i not in (30, 35)]
    assert got.iloc[keep].equals(full.iloc[keep])

    vol_full, vol = features.realised_vol(CLOSE, 20, 252), features.realised_vol(gappy, 20, 252)
    # daily returns at 30 and 31 are missing -> windows ending at 30..50 are NaN
    assert vol.iloc[30:51].isna().all()
    # rolling sums restart after a NaN, so compare to float precision, not bit for bit
    np.testing.assert_allclose(vol.iloc[51:], vol_full.iloc[51:], rtol=1e-10)
    assert vol.iloc[20:30].equals(vol_full.iloc[20:30])


def test_build_features_has_the_configured_columns_and_nan_fx_without_fx():
    names = features.feature_columns(SETTINGS.features)
    assert len(names) == len(set(names)) == 19
    volume = pd.Series(1000.0, index=GRID)
    out = features.build_features(CLOSE, volume, CLOSE * 2, None, SETTINGS.features, 252)
    assert list(out.columns) == names
    assert out[[c for c in names if c.startswith("fx_")]].isna().all().all()
    with_fx = features.build_features(CLOSE, volume, CLOSE * 2, CLOSE * 3, SETTINGS.features, 252)
    assert with_fx["fx_ret_20"].iloc[20] == pytest.approx(CLOSE.iloc[20] / CLOSE.iloc[0] - 1)
    # market features come from the index series, and scale does not matter
    assert out["mkt_ret_20"].equals(out["ret_20"])
