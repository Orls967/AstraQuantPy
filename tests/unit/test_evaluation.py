"""Metrics, selection rule, intervals, sample builders and models."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from astraquant.config import load_assets, load_settings
from astraquant.dataset import build_daily, build_quarterly
from astraquant.evaluation import protocol
from astraquant.evaluation.intervals import add_intervals, interval_summary
from astraquant.evaluation.metrics import directional_accuracy, r2_oos, summarise, yearly_comparison
from astraquant.evaluation.samples import (
    complete_mask,
    daily_samples,
    origin_grid,
    quarterly_samples,
)
from astraquant.evaluation.selection import apply_selection_rule
from astraquant.models import HistoricalMeanModel, LightGBMModel, RidgeModel, TrailingFeatureModel
from tests.synthetic import quarterly_frame


def test_r2_oos_and_direction():
    y = np.array([1.0, -1.0, 2.0])
    base = np.zeros(3)
    assert r2_oos(y, y, base) == 1.0
    assert r2_oos(y, base, base) == 0.0
    assert r2_oos(y, -y, base) == pytest.approx(1 - 4.0)
    assert np.isnan(r2_oos(y, y, y))
    assert directional_accuracy(y, np.array([0.5, 0.5, 0.0])) == 0.5
    assert np.isnan(directional_accuracy(y, base))


def _predictions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["A", "A", "B", "B"],
            "market": ["US", "US", "ID", "ID"],
            "test_year": [2016, 2017, 2016, 2017],
            "y": [0.10, -0.10, 0.20, 0.00],
            "pred_base": [0.0, 0.0, 0.0, 0.0],
            "pred_good": [0.10, -0.05, 0.10, 0.00],
            "pred_bad": [-0.10, 0.10, 0.00, 0.10],
        }
    )


def test_summarise_and_yearly():
    frame = _predictions()
    overall = summarise(frame, ["base", "good", "bad"], "base", reference="base")
    good = overall.set_index("model").loc["good"]
    assert good["r2_oos"] == pytest.approx(1 - (0.05**2 + 0.10**2) / (0.01 + 0.01 + 0.04))
    assert good["r2_vs_base"] == pytest.approx(good["r2_oos"])
    assert overall.set_index("model").loc["base", "r2_oos"] == 0.0
    by_market = summarise(frame, ["good"], "base", by="market")
    assert sorted(by_market["market"]) == ["ID", "US"]
    yearly = yearly_comparison(frame, ["base", "good", "bad"], "base")
    assert yearly["beats_good"].tolist() == [True, True]
    assert yearly["beats_bad"].tolist() == [False, False]


def _rule(r2: dict[str, float], wins: dict[str, list[bool]]) -> dict:
    overall = pd.DataFrame({"model": list(r2), "r2_oos": list(r2.values())})
    yearly = pd.DataFrame({f"beats_{k}": v for k, v in wins.items()})
    return apply_selection_rule(overall, yearly, list(r2), "base")


def test_selection_rule_needs_both_conditions():
    half = [True, True, False, False]
    most = [True, True, True, False]
    assert _rule({"m": 0.05}, {"m": half})["selected"] == "base"  # exactly half is not enough
    assert _rule({"m": -0.01}, {"m": most})["selected"] == "base"
    assert _rule({"m": 0.0}, {"m": most})["selected"] == "base"
    assert _rule({"m": 0.05}, {"m": most})["selected"] == "m"
    both = _rule({"m": 0.05, "n": 0.08}, {"m": most, "n": most})
    assert both["selected"] == "n"
    assert [c["qualifies"] for c in both["checks"]] == [True, True]


def test_intervals_use_earlier_years_of_the_same_market():
    rng = np.random.default_rng(0)
    frame = pd.DataFrame(
        {
            "symbol": "A",
            "market": np.tile(["US", "ID"], 40),
            "test_year": np.repeat([2016, 2017, 2018, 2019], 20),
            "y": rng.normal(size=80),
            "pred_m": 0.0,
        }
    )
    out = add_intervals(frame, "m", 0.80, min_prior_years=2)
    assert out.loc[out["test_year"] < 2018, ["lower", "upper"]].isna().all().all()
    assert out.loc[out["test_year"] >= 2018, ["lower", "upper"]].notna().all().all()
    past = frame[(frame["test_year"] < 2018) & (frame["market"] == "US")]["y"]
    row = out[(out["test_year"] == 2018) & (out["market"] == "US")].iloc[0]
    assert row["lower"] == pytest.approx(past.quantile(0.10))
    assert row["upper"] == pytest.approx(past.quantile(0.90))

    changed = frame.copy()
    changed.loc[changed["test_year"] >= 2018, "y"] += 100.0
    again = add_intervals(changed, "m", 0.80, min_prior_years=2)
    is_2018 = out["test_year"] == 2018
    pd.testing.assert_series_equal(out.loc[is_2018, "lower"], again.loc[is_2018, "lower"])
    summary = interval_summary(out)
    assert summary["n"].iloc[0] == 40
    assert 0.0 <= summary["coverage"].iloc[0] <= 1.0


def test_complete_mask_requires_fx_only_where_it_exists():
    frame = pd.DataFrame(
        {
            "market": ["US", "ID", "ID", "US"],
            "ret_5": [0.1, 0.1, 0.1, np.nan],
            "fx_ret_20": [np.nan, 0.1, np.nan, np.nan],
        }
    )
    assert complete_mask(frame, ["ret_5", "fx_ret_20"], ["ID"]).tolist() == [
        True,
        True,
        False,
        False,
    ]


def test_origin_grid_labels_do_not_overlap():
    sessions = pd.bdate_range("2020-01-01", periods=50)
    grid = origin_grid(sessions, 20)
    assert list(grid) == [sessions[0], sessions[20], sessions[40]]
    with pytest.raises(ValueError):
        origin_grid(sessions, 0)


def test_sample_builders_on_the_synthetic_panel(panel_assets, panel, settings):
    daily = build_daily(panel_assets, panel, settings)
    quarterly = build_quarterly(daily, panel_assets, settings)
    features = protocol.model_features(settings)
    fx = protocol.fx_markets(settings)
    assert fx == ["ID"]

    q = quarterly_samples(quarterly, features, fx)
    assert len(q) == len(quarterly)
    assert (q["test_year"] == q["target_end_date"].dt.year).all()
    assert (q["origin_date"] < q["target_end_date"]).all()
    assert q["complete"].any() and not q["complete"].all()  # first year lacks long windows

    grids = {
        market: origin_grid(pd.DatetimeIndex(sorted(part["date"].unique())), 20)
        for market, part in daily.groupby("market")
    }
    d = daily_samples(daily, "fwd_ret_20", 20, grids, features, fx)
    for _, own in d.groupby("symbol"):
        own = own.sort_values("origin_date")
        # Each label ends exactly where the next origin starts: no overlap.
        assert (own["target_end_date"].iloc[:-1].to_numpy() == own["origin_date"].iloc[1:]).all()
    assert (d["test_year"] == d["origin_date"].dt.year).all()


def test_model_plans_follow_the_blueprint():
    settings = load_settings()
    targets = protocol.target_specs(settings)
    assert [t.name for t in targets if t.primary] == ["q_return"]
    assert len(targets) == 6
    plan = protocol.model_plan(targets[0], settings)
    assert plan.names == ["zero", "historical_mean", "ridge", "lightgbm"]
    assert (plan.baseline, plan.candidates) == ("historical_mean", ["ridge", "lightgbm"])
    vol = protocol.model_plan(next(t for t in targets if t.kind == "volatility"), settings)
    assert vol.names == ["trailing_vol", "historical_mean", "ridge", "lightgbm"]
    assert vol.baseline == "trailing_vol"
    assert len(plan.specs[2].grid) == 6 and len(plan.specs[3].grid) == 4


def test_fold_cutoff_is_the_earlier_exchange_close():
    settings = load_settings()
    cutoffs = protocol.fold_cutoffs(load_assets(), settings, [2016, 2027])
    # IDX closed 2015 on 30 Dec, NYSE on 31 Dec; IDX closes 2026 on 30 Dec (DECISIONS 2.1).
    assert cutoffs[2016] == {"US": pd.Timestamp("2015-12-30"), "ID": pd.Timestamp("2015-12-30")}
    assert cutoffs[2027]["US"] == pd.Timestamp("2026-12-30")


def test_historical_mean_per_symbol_with_fallback():
    history = pd.DataFrame({"symbol": ["A", "A", "B"], "y": [0.1, 0.3, -0.2]})
    model = HistoricalMeanModel()
    model.fit(history.iloc[:0], history)
    rows = pd.DataFrame({"symbol": ["A", "B", "NEW"]})
    assert model.predict(rows) == pytest.approx([0.2, -0.2, 0.2 / 3])


def test_trailing_feature_model_returns_the_feature():
    rows = pd.DataFrame({"rvol_20": [0.2, 0.4]})
    assert TrailingFeatureModel("rvol_20").predict(rows).tolist() == [0.2, 0.4]


def test_ridge_scales_on_train_only_and_zeroes_fx_for_other_markets():
    features = ["ret_5", "fx_ret_20", "is_id"]
    frame = quarterly_frame(features)
    train = frame[frame["test_year"] < 2018]
    test = frame[frame["test_year"] == 2018]
    model = RidgeModel(features, alpha=1.0)
    model.fit(train, train)
    assert model.mean["ret_5"] == pytest.approx(train["ret_5"].mean())
    local = train.loc[train["market"] == "ID", "fx_ret_20"]
    assert model.mean["fx_ret_20"] == pytest.approx(local.mean())
    scaled = model._transform(test)
    assert (scaled[(test["market"] != "ID").to_numpy(), 1] == 0.0).all()
    assert np.isfinite(model.predict(test)).all()
    # A forecast does not depend on which other rows are predicted with it.
    assert model.predict(test.iloc[:1])[0] == pytest.approx(model.predict(test)[0], abs=1e-12)

    broken = test.copy()
    broken.loc[broken.index[0], "ret_5"] = np.nan
    with pytest.raises(ValueError):
        model.predict(broken)


def test_lightgbm_is_deterministic_and_accepts_missing_fx():
    features = ["ret_5", "ret_20", "fx_ret_20", "is_id"]
    frame = quarterly_frame(features)
    train, test = frame[frame["test_year"] < 2019], frame[frame["test_year"] >= 2019]
    params = {"n_estimators": 20, "num_leaves": 3, "min_child_samples": 5}
    first = LightGBMModel(features, seed=1, **params)
    second = LightGBMModel(features, seed=1, **params)
    first.fit(train, train)
    second.fit(train, train)
    assert np.array_equal(first.predict(test), second.predict(test))
    assert np.isfinite(first.predict(test)).all()
