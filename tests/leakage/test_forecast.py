"""The stored forecast uses nothing after the cutoff and matches the pinned dates."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from astraquant.dataset import build_daily, build_quarterly
from astraquant.forecast import forecast_quarter, is_late, readiness_problems

QUARTER = "2021Q3"
BASELINE = {"selected": "historical_mean", "baseline": "historical_mean"}


@pytest.fixture
def quarterly(panel_assets, panel, settings) -> pd.DataFrame:
    daily = build_daily(panel_assets, panel, settings)
    return build_quarterly(daily, panel_assets, settings)


def _predictions(quarterly: pd.DataFrame) -> pd.DataFrame:
    """Fake walk-forward predictions: every realised row, forecast of zero."""
    frame = quarterly.dropna(subset=["q_return"])
    out = frame[["symbol", "market", "target_end_date"]].copy()
    out["y"] = frame["q_return"]
    for name in ("zero", "historical_mean", "ridge", "lightgbm"):
        out[f"pred_{name}"] = 0.0
    return out


def test_baseline_forecast_is_the_mean_of_realised_quarters(quarterly, panel_assets, settings):
    out = forecast_quarter(
        quarterly, _predictions(quarterly), BASELINE, panel_assets, settings, QUARTER
    )
    assert sorted(out["ticker"]) == ["AAA", "BBB", "CCC.JK", "DDD.JK"]
    cutoff = out.attrs["cutoff"]
    assert cutoff == out["forecast_origin_date"].min()
    for row in out.itertuples():
        own = quarterly[(quarterly["symbol"] == row.ticker)]
        realised = own[(own["target_end_date"] <= cutoff) & own["q_return"].notna()]
        assert row.point_estimate == pytest.approx(realised["q_return"].mean())
        assert row.history_rows == len(realised)
        origin = own[own["quarter"] == QUARTER].iloc[0]
        assert row.target_start_date == origin["target_start_date"]
        assert row.target_end_date == origin["target_end_date"]
        assert row.target_start_price == origin["target_start_price"]
        assert row.interval_lower < row.point_estimate < row.interval_upper
    us = out[out["market"] == "US"].iloc[0]
    past = _predictions(quarterly)
    past = past[(past["market"] == "US") & (past["target_end_date"] <= cutoff)]
    assert us["interval_lower"] == pytest.approx(us["point_estimate"] + past["y"].quantile(0.10))
    assert us["interval_upper"] == pytest.approx(us["point_estimate"] + past["y"].quantile(0.90))


@pytest.mark.parametrize("model", ["historical_mean", "ridge", "lightgbm"])
def test_forecast_ignores_everything_after_the_cutoff(quarterly, panel_assets, settings, model):
    selection = {"selected": model, "baseline": "historical_mean"}
    predictions = _predictions(quarterly)
    base = forecast_quarter(quarterly, predictions, selection, panel_assets, settings, QUARTER)
    cutoff = base.attrs["cutoff"]

    rng = np.random.default_rng(5)
    changed = quarterly.copy()
    later = changed["target_end_date"] > cutoff
    changed.loc[later, "q_return"] = rng.normal(3.0, 2.0, int(later.sum()))
    after_origin = changed["target_start_date"] > base["forecast_origin_date"].max()
    for column in ("ret_5", "ret_20", "rvol_20"):
        changed.loc[after_origin, column] = rng.normal(0.0, 5.0, int(after_origin.sum()))
    changed_predictions = predictions.copy()
    late_rows = changed_predictions["target_end_date"] > cutoff
    changed_predictions.loc[late_rows, "y"] = 9.0

    again = forecast_quarter(
        changed, changed_predictions, selection, panel_assets, settings, QUARTER
    )
    columns = ["point_estimate", "interval_lower", "interval_upper"]
    pd.testing.assert_frame_equal(base[columns], again[columns])
    assert np.isfinite(base[columns].to_numpy()).all()


def test_a_label_ending_after_the_earliest_origin_is_not_used(quarterly, panel_assets, settings):
    # 2021Q1: IDX closed 2020 on 30 Dec, NYSE on 31 Dec. The US 2020Q4 label is excluded.
    predictions = _predictions(quarterly)
    out = forecast_quarter(quarterly, predictions, BASELINE, panel_assets, settings, "2021Q1")
    assert out.attrs["cutoff"] == pd.Timestamp("2020-12-30")
    us = quarterly[(quarterly["symbol"] == "AAA") & quarterly["q_return"].notna()]
    kept = us[us["target_end_date"] <= pd.Timestamp("2020-12-30")]
    assert "2020Q4" not in kept["quarter"].tolist() and "2020Q3" in kept["quarter"].tolist()
    point = out.loc[out["ticker"] == "AAA", "point_estimate"].iloc[0]
    assert point == pytest.approx(kept["q_return"].mean())


def test_a_quarter_whose_origin_has_no_data_is_refused(quarterly, panel_assets, settings):
    with pytest.raises(ValueError, match="no origin row"):
        forecast_quarter(
            quarterly, _predictions(quarterly), BASELINE, panel_assets, settings, "2027Q1"
        )
    short = quarterly[~((quarterly["symbol"] == "BBB") & (quarterly["quarter"] == QUARTER))]
    with pytest.raises(ValueError, match="BBB"):
        forecast_quarter(short, _predictions(short), BASELINE, panel_assets, settings, QUARTER)


def test_readiness_checks_prices_and_pinned_dates(quarterly, panel_assets, settings):
    out = forecast_quarter(
        quarterly, _predictions(quarterly), BASELINE, panel_assets, settings, QUARTER
    )
    pinned = {
        "XNYS": {"start": pd.Timestamp("2021-06-30").date(), "end": pd.Timestamp("2021-09-30")},
        "XIDX": {"start": pd.Timestamp("2021-06-30").date(), "end": pd.Timestamp("2021-09-30")},
    }
    assert readiness_problems(out, settings, pinned) == []
    wrong = {**pinned, "XIDX": {"start": "2021-06-29", "end": "2021-09-30"}}
    assert any("XIDX: origin differs" in p for p in readiness_problems(out, settings, wrong))
    assert any(
        "no pinned" in p for p in readiness_problems(out, settings, {"XNYS": pinned["XNYS"]})
    )
    broken = out.copy()
    broken.loc[0, "target_start_price"] = np.nan
    assert any("no closing price" in p for p in readiness_problems(broken, settings, pinned))
    # The real Q1 2027 pins cannot match a 2021 quarter.
    assert readiness_problems(out, settings, settings.targets["q1_2027"])


def test_late_flag(quarterly, panel_assets, settings):
    out = forecast_quarter(
        quarterly, _predictions(quarterly), BASELINE, panel_assets, settings, QUARTER
    )
    assert not is_late(out, {"US": "2021-06-30", "ID": "2021-06-30"})
    assert is_late(out, {"US": "2021-07-01", "ID": "2021-06-30"})
