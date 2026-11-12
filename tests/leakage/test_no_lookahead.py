"""Leakage tests.

Features at session ``t`` must not change when anything after ``t`` changes,
and must equal what would have been computed had the data ended at ``t``.
Targets must depend only on the future they are defined on.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from astraquant.config import load_settings
from astraquant.dataset import build_daily, build_quarterly
from astraquant.features import feature_columns

SETTINGS = load_settings()
NAMES = [*feature_columns(SETTINGS.features), "is_id"]
CUT = pd.Timestamp("2021-03-10")
PRICE_COLUMNS = ["open", "high", "low", "close", "adj_close", "volume"]


def _scramble_after(panel: dict[str, pd.DataFrame], cut: pd.Timestamp) -> dict[str, pd.DataFrame]:
    """Replace every value after ``cut`` in every series with unrelated numbers."""
    rng = np.random.default_rng(999)
    out = {}
    for symbol, bars in panel.items():
        changed = bars.copy()
        future = changed["date"] > cut
        noise = rng.uniform(0.2, 5.0, int(future.sum()))
        for column in PRICE_COLUMNS:
            changed[column] = changed[column].astype(float)
            changed.loc[future, column] = changed.loc[future, column].to_numpy() * noise
        out[symbol] = changed
    return out


def _truncate(panel: dict[str, pd.DataFrame], cut: pd.Timestamp) -> dict[str, pd.DataFrame]:
    return {s: bars[bars["date"] <= cut].reset_index(drop=True) for s, bars in panel.items()}


def _features(daily: pd.DataFrame, cut: pd.Timestamp) -> pd.DataFrame:
    past = daily[daily["date"] <= cut]
    return past.set_index(["symbol", "date"])[NAMES]


def test_features_do_not_change_when_future_rows_are_altered(panel, panel_assets):
    base = build_daily(panel_assets, panel, SETTINGS)
    altered = build_daily(panel_assets, _scramble_after(panel, CUT), SETTINGS)
    pd.testing.assert_frame_equal(_features(base, CUT), _features(altered, CUT), check_exact=True)
    # the test has power: features after the cut do change
    after = base["date"] > CUT
    assert not base.loc[after, "ret_5"].equals(altered.loc[after, "ret_5"])


def test_features_equal_those_computed_on_data_truncated_at_the_origin(panel, panel_assets):
    base = build_daily(panel_assets, panel, SETTINGS)
    truncated = build_daily(panel_assets, _truncate(panel, CUT), SETTINGS)
    pd.testing.assert_frame_equal(_features(base, CUT), _features(truncated, CUT), check_exact=True)
    assert _features(base, CUT).notna().any().all()  # every feature is exercised


def test_quarterly_features_use_nothing_after_the_origin(panel, panel_assets):
    """For each quarter, scramble everything after its origin and rebuild."""
    daily = build_daily(panel_assets, panel, SETTINGS)
    base = build_quarterly(daily, panel_assets, SETTINGS).set_index(["symbol", "quarter"])
    for quarter in ["2020Q3", "2021Q1", "2021Q4"]:
        for market in ["US", "ID"]:
            rows = base[(base["market"] == market)].xs(quarter, level="quarter")
            origin = rows["origin_date"].iloc[0]
            scrambled = _scramble_after(panel, origin)
            rebuilt = build_quarterly(
                build_daily(panel_assets, scrambled, SETTINGS), panel_assets, SETTINGS
            ).set_index(["symbol", "quarter"])
            again = rebuilt[rebuilt["market"] == market].xs(quarter, level="quarter")
            pd.testing.assert_frame_equal(rows[NAMES], again[NAMES], check_exact=True)
            assert (rows["target_start_price"] == again["target_start_price"]).all()
            assert not np.allclose(rows["q_return"], again["q_return"])  # label is the future


def test_fx_bar_dated_on_the_origin_is_not_used(panel, panel_assets):
    """A Yahoo FX bar dated D closes after the IDX close on D."""
    day = pd.Timestamp("2021-03-16")  # an IDX session, and so is the next weekday
    base = build_daily(panel_assets, panel, SETTINGS)
    changed = {s: b.copy() for s, b in panel.items()}
    fx = changed["IDR=X"]
    fx.loc[fx["date"] == day, "close"] *= 3.0
    altered = build_daily(panel_assets, changed, SETTINGS)

    def fx_at(frame, date):
        rows = frame[(frame["symbol"] == "CCC.JK") & (frame["date"] == date)]
        return rows[["fx_ret_20", "fx_ret_60"]].to_numpy()

    following = base.loc[(base["symbol"] == "CCC.JK") & (base["date"] > day), "date"].iloc[0]
    assert np.array_equal(fx_at(base, day), fx_at(altered, day))
    assert not np.array_equal(fx_at(base, following), fx_at(altered, following))


@pytest.mark.parametrize("horizon", SETTINGS.dataset["return_horizons"])
def test_forward_targets_depend_only_on_their_own_window(panel, panel_assets, horizon):
    base = build_daily(panel_assets, panel, SETTINGS)
    altered = build_daily(panel_assets, _scramble_after(panel, CUT), SETTINGS)
    end = base[f"target_end_date_{horizon}"]
    inside = end <= CUT
    column = f"fwd_ret_{horizon}"
    assert inside.sum() > 0 and base.loc[inside, column].equals(altered.loc[inside, column])
    crossing = (base["date"] <= CUT) & (end > CUT)
    assert crossing.sum() == 4 * horizon  # 4 symbols, `horizon` origins each
    assert (base.loc[crossing, column] != altered.loc[crossing, column]).all()


def test_missing_bar_gives_nan_and_leaves_other_rows_untouched(panel, panel_assets):
    """Q-13 rule: horizons follow the calendar; nothing shifts to fill a gap."""
    base = build_daily(panel_assets, panel, SETTINGS)
    gap = pd.Timestamp("2021-03-10")
    holed = {s: b.copy() for s, b in panel.items()}
    holed["CCC.JK"] = holed["CCC.JK"][holed["CCC.JK"]["date"] != gap].reset_index(drop=True)
    got = build_daily(panel_assets, holed, SETTINGS)

    a = base[base["symbol"] == "CCC.JK"].reset_index(drop=True)
    b = got[got["symbol"] == "CCC.JK"].reset_index(drop=True)
    assert list(a["date"]) == list(b["date"])  # the session grid is unchanged
    i = int(a.index[a["date"] == gap][0])
    assert not b.loc[i, "has_bar"]
    assert list(a["target_end_date_5"].dropna()) == list(b["target_end_date_5"].dropna())
    # labels: the origin 5 sessions before the gap and the gap itself are NaN
    assert np.isnan(b.loc[i - 5, "fwd_ret_5"]) and np.isnan(b.loc[i, "fwd_ret_5"])
    assert b.loc[i - 4, "fwd_ret_5"] == a.loc[i - 4, "fwd_ret_5"]
    # features: ret_5 is NaN at the gap and 5 sessions later, unchanged next to them
    assert np.isnan(b.loc[i, "ret_5"]) and np.isnan(b.loc[i + 5, "ret_5"])
    assert b.loc[i + 4, "ret_5"] == a.loc[i + 4, "ret_5"]
    assert b.loc[i + 6, "ret_5"] == a.loc[i + 6, "ret_5"]
    # other symbols are untouched
    other = ["AAA", "BBB", "DDD.JK"]
    pd.testing.assert_frame_equal(
        base[base["symbol"].isin(other)].reset_index(drop=True),
        got[got["symbol"].isin(other)].reset_index(drop=True),
    )
