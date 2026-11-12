"""Dataset assembly on a synthetic panel."""

from __future__ import annotations

import numpy as np
import pandas as pd

from astraquant import calendars
from astraquant.config import load_settings
from astraquant.dataset import build_daily, build_quarterly, lagged_on_grid, to_session_grid
from astraquant.features import feature_columns

SETTINGS = load_settings()
NAMES = feature_columns(SETTINGS.features)


def test_session_grid_keeps_gaps_as_nan_rows(panel):
    bars = panel["AAA"].drop(index=10).reset_index(drop=True)
    sessions = calendars.sessions("XNYS", bars["date"].min(), bars["date"].max())
    grid = to_session_grid(bars, sessions)
    assert len(grid) == len(sessions) == len(bars) + 1
    assert np.isnan(grid["close"].iloc[10]) and grid["close"].notna().sum() == len(bars)


def test_lagged_on_grid_is_an_exact_date_lookup():
    days = pd.bdate_range("2024-03-01", "2024-03-15")
    fx = pd.Series(np.arange(len(days), dtype=float), index=days).drop(pd.Timestamp("2024-03-07"))
    sessions = pd.DatetimeIndex(["2024-03-04", "2024-03-08", "2024-03-11"])
    got = lagged_on_grid(fx, sessions, 1)
    assert got[pd.Timestamp("2024-03-04")] == fx[pd.Timestamp("2024-03-01")]  # Monday <- Friday
    assert np.isnan(got[pd.Timestamp("2024-03-08")])  # 7 March missing: NaN, not 6 March
    assert got[pd.Timestamp("2024-03-11")] == fx[pd.Timestamp("2024-03-08")]


def test_daily_dataset_shape_and_market_columns(panel, panel_assets):
    daily = build_daily(panel_assets, panel, SETTINGS)
    assert set(daily["symbol"]) == {"AAA", "BBB", "CCC.JK", "DDD.JK"}
    assert not daily.duplicated(["symbol", "date"]).any()
    us, idn = daily[daily["market"] == "US"], daily[daily["market"] == "ID"]
    assert (us["is_id"] == 0).all() and (idn["is_id"] == 1).all()
    assert us[["fx_ret_20", "fx_ret_60"]].isna().all().all()
    assert idn["fx_ret_20"].notna().sum() > 400
    for symbol, group in daily.groupby("symbol"):
        calendar = "XIDX" if symbol.endswith(".JK") else "XNYS"
        expected = calendars.sessions(
            calendar, group["date"].min(), group["date"].max(), SETTINGS.holidays_for(calendar)
        )
        assert list(group["date"]) == list(expected)
    # the last row of every series has features but no forward target
    last = daily.groupby("symbol").tail(1)
    assert last["ret_250"].notna().all() and last["fwd_ret_5"].isna().all()


def test_quarterly_dataset_joins_features_at_the_origin(panel, panel_assets):
    daily = build_daily(panel_assets, panel, SETTINGS)
    quarterly = build_quarterly(daily, panel_assets, SETTINGS)
    assert not quarterly.duplicated(["symbol", "quarter"]).any()
    row = quarterly[(quarterly["symbol"] == "CCC.JK") & (quarterly["quarter"] == "2021Q1")].iloc[0]
    assert row["origin_date"] == row["target_start_date"] == pd.Timestamp("2020-12-30")
    assert row["target_end_date"] == pd.Timestamp("2021-03-31")
    own = daily[daily["symbol"] == "CCC.JK"].set_index("date")
    start, end = own.loc[row["target_start_date"]], own.loc[row["target_end_date"]]
    assert row["q_return"] == end["close"] / start["close"] - 1
    assert row["target_start_price"] == start["close"]
    pd.testing.assert_series_equal(
        row[NAMES].astype(float), start[NAMES].astype(float), check_names=False
    )
    # a quarter whose origin is in the data but which has not ended has a NaN label
    unlabelled = quarterly[quarterly["q_return"].isna()]
    assert set(unlabelled["quarter"]) == {"2022Q1"} and len(unlabelled) == 4
    assert set(quarterly["quarter"]) >= {"2019Q2", "2021Q4"}
    assert "2019Q1" not in set(quarterly["quarter"])  # its origin predates the data
