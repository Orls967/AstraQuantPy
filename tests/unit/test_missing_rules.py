"""Q-17 and Q-18: long-window tolerance and price breaks."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from astraquant import calendars, features, targets
from astraquant.config import load_settings

SPEC = load_settings().features
GRID = calendars.sessions("XNYS", "2022-01-03", "2023-12-29")
RNG = np.random.default_rng(11)
CLOSE = pd.Series(100 * np.exp(np.cumsum(RNG.normal(0.0002, 0.012, len(GRID)))), index=GRID)
VOLUME = pd.Series(RNG.integers(1_000, 9_000, len(GRID)).astype(float), index=GRID)
T = 400  # origin position used throughout


def build(close=CLOSE, volume=VOLUME, breaks=()):
    return features.build_features(close, volume, CLOSE, None, SPEC, 252, breaks)


def with_gaps(positions) -> tuple[pd.Series, pd.Series]:
    close, volume = CLOSE.copy(), VOLUME.copy()
    close.iloc[list(positions)] = np.nan
    volume.iloc[list(positions)] = np.nan
    return close, volume


def test_budget_is_two_percent_for_long_windows_only():
    tol = SPEC["long_window"]
    assert [features.missing_budget(w, tol) for w in (5, 20, 60, 120, 200, 250)] == [
        0, 0, 0, 2, 4, 5,
    ]  # fmt: skip


def test_without_gaps_tolerant_features_equal_the_strict_formulas():
    out = build()
    assert out["rvol_120"].equals(features.realised_vol(CLOSE, 120, 252))
    assert out["ret_250"].equals(features.trailing_return(CLOSE, 250))
    pd.testing.assert_series_equal(
        out["ma_dist_200"], features.ma_distance(CLOSE, 200), check_names=False
    )
    pd.testing.assert_series_equal(
        out["drawdown_250"], features.drawdown(CLOSE, 250), check_names=False
    )
    pd.testing.assert_series_equal(
        out["rel_volume_20_120"], features.relative_volume(VOLUME, 20, 120), check_names=False
    )


def test_one_missing_bar_mid_window_is_tolerated_for_long_windows_only():
    close, volume = with_gaps([T - 50])
    out = build(close, volume).iloc[T]
    # strict windows that include the gap are NaN
    assert np.isnan(out["rvol_60"])
    # long windows are computed on the bars that exist
    log_return = np.log(close).diff().iloc[T - 119 : T + 1]
    assert log_return.isna().sum() == 2
    assert out["rvol_120"] == pytest.approx(log_return.std() * np.sqrt(252))
    window = close.iloc[T - 199 : T + 1]
    assert out["ma_dist_200"] == pytest.approx(close.iloc[T] / window.mean() - 1)
    assert out["drawdown_250"] == pytest.approx(
        close.iloc[T] / close.iloc[T - 249 : T + 1].max() - 1
    )
    assert out["rel_volume_20_120"] == pytest.approx(
        volume.iloc[T - 19 : T + 1].mean() / volume.iloc[T - 119 : T + 1].mean()
    )
    # returns only need their two ends
    assert out["ret_60"] == pytest.approx(CLOSE.iloc[T] / CLOSE.iloc[T - 60] - 1)


def test_too_many_missing_bars_gives_nan():
    close, volume = with_gaps([T - 50, T - 51, T - 52])  # 3 > budget of 2 for 120
    out = build(close, volume).iloc[T]
    assert np.isnan(out["rvol_120"]) and np.isnan(out["rel_volume_20_120"])
    assert not np.isnan(out["ma_dist_200"])  # budget 4
    assert not np.isnan(out["drawdown_250"])  # budget 5
    six = build(*with_gaps(range(T - 60, T - 54))).iloc[T]
    assert np.isnan(six["ma_dist_200"]) and np.isnan(six["drawdown_250"])


@pytest.mark.parametrize(
    ("gap", "blanked"),
    [
        (T, ["rvol_120", "ma_dist_200", "drawdown_250", "rel_volume_20_120", "ret_250"]),
        (T - 120, ["rvol_120", "ret_120"]),
        (T - 119, ["rel_volume_20_120"]),
        (T - 199, ["ma_dist_200"]),
        (T - 249, ["drawdown_250"]),
        (T - 250, ["ret_250"]),
    ],
)
def test_both_ends_of_a_long_window_must_exist(gap, blanked):
    out = build(*with_gaps([gap])).iloc[T]
    assert out[blanked].isna().all()


def test_price_break_is_one_missing_return_for_features():
    day = GRID[T - 30]
    jumped = CLOSE.copy()
    jumped.iloc[: T - 30] *= 0.9  # provider rescaled everything before the break
    out = build(jumped, breaks=(day,)).iloc[T]
    # strict windows crossing the break are NaN; those after it are untouched
    assert np.isnan(out["ret_60"]) and np.isnan(out["rvol_60"]) and np.isnan(out["ma_dist_50"])
    clean = build().iloc[T]
    assert out["ret_20"] == clean["ret_20"] and out["rsi_14"] == clean["rsi_14"]
    # long windows skip the break-day return and never mix the two price scales
    r = np.log(CLOSE).diff()
    skipped = r.iloc[T - 119 : T + 1].drop(day)
    assert out["rvol_120"] == pytest.approx(skipped.std() * np.sqrt(252))
    assert out["ret_120"] == pytest.approx(np.exp(r.iloc[T - 119 : T + 1].drop(day).sum()) - 1)
    rebased = CLOSE.copy()
    rebased.iloc[: T - 30] *= CLOSE.iloc[T - 30] / CLOSE.iloc[T - 31]
    assert out["ma_dist_200"] == pytest.approx(
        rebased.iloc[T] / rebased.iloc[T - 199 : T + 1].mean() - 1
    )
    assert np.isnan(out["rel_volume_20_120"])  # volume windows never span a break
    # the size of the provider's rescaling does not matter
    other = CLOSE.copy()
    other.iloc[: T - 30] *= 0.5
    again = build(other, breaks=(day,)).iloc[T]
    np.testing.assert_allclose(
        out[["ret_120", "ret_250", "rvol_120", "ma_dist_200", "drawdown_250"]].astype(float),
        again[["ret_120", "ret_250", "rvol_120", "ma_dist_200", "drawdown_250"]].astype(float),
        rtol=1e-9,
    )


def test_labels_that_cross_a_price_break_are_nan():
    day = GRID[T]
    clean = targets.forward_return(CLOSE, 20)
    got = targets.forward_return(CLOSE, 20, (day,))
    assert got.iloc[T - 20 : T].isna().all()  # windows t+1..t+20 that include the break
    assert got.iloc[T] == clean.iloc[T] and got.iloc[T - 21] == clean.iloc[T - 21]
    vol = targets.forward_realised_vol(CLOSE, 20, 252, (day,))
    assert vol.iloc[T - 20 : T].isna().all() and not np.isnan(vol.iloc[T])

    bounds = targets.quarter_boundaries("XNYS", GRID[0], GRID[-1])
    quarter = str(pd.Period(day, freq="Q"))
    out = targets.quarterly_returns(CLOSE, bounds, (day,)).set_index("quarter")
    plain = targets.quarterly_returns(CLOSE, bounds).set_index("quarter")
    assert np.isnan(out.loc[quarter, "q_return"]) and not np.isnan(plain.loc[quarter, "q_return"])
    others = out.index != quarter
    assert out.loc[others, "q_return"].equals(plain.loc[others, "q_return"])


def test_configured_breaks_are_real_sessions_of_configured_symbols():
    from astraquant.config import load_assets

    settings = load_settings()
    assets = {a.symbol: a for a in load_assets()}
    assert sum(len(v) for v in settings.price_breaks.values()) == 5
    for symbol, days in settings.price_breaks.items():
        cal = assets[symbol].calendar
        for day in days:
            assert pd.Timestamp(day) in calendars.sessions(
                cal, day, day, settings.holidays_for(cal)
            )
