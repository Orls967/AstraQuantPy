"""The walk-forward never lets a model see the test block or anything after it."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from astraquant.config import load_settings
from astraquant.evaluation import protocol
from astraquant.evaluation.walkforward import make_fold, run_walk_forward
from astraquant.models import HistoricalMeanModel, ModelSpec, RidgeModel
from tests.synthetic import cutoffs, quarterly_frame

FEATURES = ["ret_5", "ret_20", "fx_ret_20", "is_id"]
YEARS = list(range(2016, 2021))


class Recorder:
    """Records the latest label end and row count of everything passed to ``fit``."""

    seen: list[tuple[pd.Timestamp, int]] = []
    predicted: list[int] = []

    def __init__(self, shift: float = 0.0) -> None:
        self.shift = shift

    def fit(self, train: pd.DataFrame, history: pd.DataFrame) -> None:
        Recorder.seen.append((history["target_end_date"].max(), len(train)))
        assert set(train.index) <= set(history.index)

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        Recorder.predicted.extend(sorted(rows["test_year"].unique()))
        return np.full(len(rows), self.shift)


def _specs() -> list[ModelSpec]:
    grid = ({"alpha": 1.0}, {"alpha": 100.0})
    return [
        ModelSpec("historical_mean", HistoricalMeanModel),
        ModelSpec("ridge", lambda **p: RidgeModel(FEATURES, **p), grid),
    ]


def _run(samples: pd.DataFrame, specs: list[ModelSpec] | None = None):
    return run_walk_forward(samples, specs or _specs(), YEARS, cutoffs(range(2011, 2022)), 3, 8)


def test_training_rows_end_before_the_test_block_with_an_embargo():
    samples = quarterly_frame(FEATURES)
    all_cutoffs = cutoffs(range(2011, 2022))
    for year in YEARS:
        fold = make_fold(samples, year, all_cutoffs[year])
        cutoff = all_cutoffs[year]["US"]
        assert fold.history["target_end_date"].max() <= cutoff
        assert fold.test["origin_date"].min() >= cutoff
        assert (fold.test["test_year"] == year).all()
        # Embargo of one quarter: the last training origin is a full label earlier.
        assert fold.history["origin_date"].max() < cutoff - pd.Timedelta(days=80)
        # No training label overlaps the test block, in either market.
        assert not set(fold.history.index) & set(fold.test.index)
    # Expanding window: every fold contains the previous one.
    sizes = [len(make_fold(samples, y, all_cutoffs[y]).history) for y in YEARS]
    assert sizes == sorted(sizes) and len(set(sizes)) == len(sizes)


def test_a_us_label_ending_after_the_idx_year_end_is_not_trained_on():
    samples = quarterly_frame(FEATURES)
    fold = make_fold(samples, 2016, cutoffs(range(2016, 2017))[2016])
    us_last = fold.history.loc[fold.history["market"] == "US", "target_end_date"].max()
    assert us_last == pd.Timestamp("2015-09-30")  # Q4 2015 ends 31 Dec, after the IDX close
    id_last = fold.history.loc[fold.history["market"] == "ID", "target_end_date"].max()
    assert id_last == pd.Timestamp("2015-12-30")


def test_fit_never_receives_rows_from_the_test_year_even_while_tuning():
    samples = quarterly_frame(FEATURES)
    Recorder.seen = []
    Recorder.predicted = []
    spec = ModelSpec("recorder", Recorder, ({"shift": 0.0}, {"shift": 0.1}))
    _run(samples, [spec])
    assert Recorder.seen
    latest = max(end for end, _ in Recorder.seen)
    assert latest <= cutoffs(range(2020, 2021))[2020]["US"]
    # The last test year is predicted exactly once: by the final model, never while tuning.
    assert Recorder.predicted.count(YEARS[-1]) == 1
    assert Recorder.predicted.count(YEARS[0]) > 1  # earlier years do serve as validation
    # Inner tuning fits happen on strictly smaller windows than the outer fit.
    assert len({rows for _, rows in Recorder.seen}) > len(YEARS)


def test_predictions_do_not_change_when_the_future_is_replaced():
    samples = quarterly_frame(FEATURES)
    base, base_folds = _run(samples)

    rng = np.random.default_rng(99)
    changed = samples.copy()
    future = changed["test_year"] >= 2019
    changed.loc[future, "y"] = rng.normal(5.0, 3.0, int(future.sum()))
    for column in ("ret_5", "ret_20"):
        changed.loc[future, column] = rng.normal(0.0, 10.0, int(future.sum()))
    again, again_folds = _run(changed)

    early = base["test_year"] < 2019
    columns = ["pred_historical_mean", "pred_ridge"]
    pd.testing.assert_frame_equal(
        base.loc[early, columns], again.loc[again["test_year"] < 2019, columns]
    )
    early_folds = base_folds["test_year"] < 2019
    assert (
        base_folds.loc[early_folds, "params_ridge"].tolist()
        == again_folds.loc[again_folds["test_year"] < 2019, "params_ridge"].tolist()
    )
    # The replaced data does reach later folds, so the check above is not vacuous.
    assert not np.allclose(
        base.loc[base["test_year"] == 2020, "pred_ridge"],
        again.loc[again["test_year"] == 2020, "pred_ridge"],
    )


def test_test_labels_are_not_used_for_their_own_forecast():
    samples = quarterly_frame(FEATURES)
    base, _ = _run(samples)
    changed = samples.copy()
    changed.loc[changed["test_year"] == 2020, "y"] += 10.0
    again, _ = _run(changed)
    columns = ["pred_historical_mean", "pred_ridge"]
    pd.testing.assert_frame_equal(base[columns], again[columns])


def test_incomplete_rows_are_scored_by_no_model_but_feed_the_mean():
    samples = quarterly_frame(FEATURES)
    drop = (samples["symbol"] == "AAA") & (samples["test_year"] <= 2014)
    samples.loc[drop, "complete"] = False
    samples.loc[drop, "ret_5"] = np.nan
    fold = make_fold(samples, 2016, cutoffs(range(2016, 2017))[2016])
    assert len(fold.history) - len(fold.train) == int((drop).sum())
    assert fold.train["complete"].all()
    predictions, _ = _run(samples)  # Ridge would raise if it received a NaN feature
    assert predictions[["pred_historical_mean", "pred_ridge"]].notna().all().all()


def test_walk_forward_rejects_a_training_label_that_ends_inside_the_test_block():
    samples = quarterly_frame(FEATURES)
    loose = {year: dict.fromkeys(["US", "ID"], pd.Timestamp(f"{year}-06-30")) for year in YEARS}
    with pytest.raises(AssertionError):
        run_walk_forward(samples, _specs(), YEARS, loose, 3, 8)


def test_full_protocol_runs_all_four_models_on_identical_rows():
    settings = load_settings()
    features = protocol.model_features(settings)
    samples = quarterly_frame(features, last_year=2019)
    cfg = {**settings.evaluation, "first_test_year": 2016}
    target = protocol.target_specs(settings)[0]
    plan = protocol.model_plan(target, replace(settings, evaluation=cfg))
    result = protocol.evaluate_target(
        samples, plan, cutoffs(range(2011, 2021)), replace(settings, evaluation=cfg)
    )
    predictions = result["predictions"]
    assert sorted(predictions["test_year"].unique()) == [2016, 2017, 2018, 2019]
    names = ["zero", "historical_mean", "ridge", "lightgbm"]
    assert predictions[[f"pred_{n}" for n in names]].notna().all().all()
    assert result["overall"]["n"].nunique() == 1
    assert result["overall"].set_index("model").loc["historical_mean", "r2_oos"] == 0.0
    assert result["selection"]["selected"] in {"historical_mean", "ridge", "lightgbm"}
    assert {c["model"] for c in result["selection"]["checks"]} == {"ridge", "lightgbm"}
    assert set(result["intervals"]["model"]) == set(names)

    again = protocol.evaluate_target(
        samples, plan, cutoffs(range(2011, 2021)), replace(settings, evaluation=cfg)
    )
    pd.testing.assert_frame_equal(predictions, again["predictions"])  # fixed seed
