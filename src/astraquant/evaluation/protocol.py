"""The fixed evaluation protocol (blueprint section 8, DECISIONS.md section 8).

This module wires config to the walk-forward: which targets are evaluated,
which models run on each, where the fold cutoffs are, and what is computed
from the predictions. It contains no tunable choice of its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any

import pandas as pd

from astraquant import calendars
from astraquant.config import Asset, Settings
from astraquant.evaluation.intervals import add_intervals, interval_summary
from astraquant.evaluation.metrics import summarise, yearly_comparison
from astraquant.evaluation.selection import apply_selection_rule
from astraquant.evaluation.walkforward import run_walk_forward
from astraquant.features import feature_columns
from astraquant.models import (
    HistoricalMeanModel,
    LightGBMModel,
    ModelSpec,
    RidgeModel,
    TrailingFeatureModel,
    ZeroModel,
)


@dataclass(frozen=True)
class TargetSpec:
    """One evaluated target."""

    name: str  # "q_return", "fwd_ret_20", "fwd_vol_60", ...
    kind: str  # "return" or "volatility"
    horizon: int | None  # sessions; None for the calendar quarter
    primary: bool = False


@dataclass(frozen=True)
class ModelPlan:
    """Models for one target, with their roles in the selection rule."""

    specs: list[ModelSpec]
    baseline: str
    candidates: list[str]
    reference: str | None  # second baseline, reported only
    signed: bool = True  # False for targets that are always positive (no direction)

    @property
    def names(self) -> list[str]:
        """Model names in run order."""
        return [s.name for s in self.specs]


def target_specs(settings: Settings) -> list[TargetSpec]:
    """The quarterly target first, then the configured secondary targets."""
    spec = settings.dataset
    out = [TargetSpec("q_return", "return", None, primary=True)]
    out += [TargetSpec(f"fwd_ret_{h}", "return", int(h)) for h in spec["return_horizons"]]
    out += [TargetSpec(f"fwd_vol_{h}", "volatility", int(h)) for h in spec["volatility_horizons"]]
    return out


def model_features(settings: Settings) -> list[str]:
    """Model inputs: the configured features plus the market indicator."""
    return [*feature_columns(settings.features), "is_id"]


def fx_markets(settings: Settings) -> list[str]:
    """Markets whose rows carry FX features."""
    return [market for market, ctx in settings.context.items() if "fx" in ctx]


def model_plan(target: TargetSpec, settings: Settings) -> ModelPlan:
    """The four models for a target, built from config."""
    cfg = settings.evaluation
    features = model_features(settings)
    ridge_grid = tuple({"alpha": float(a)} for a in cfg["ridge"]["alphas"])
    lgbm = cfg["lightgbm"]
    keys = list(lgbm["grid"])
    lgbm_grid = tuple(
        {**lgbm["fixed"], **dict(zip(keys, values, strict=True))}
        for values in product(*(lgbm["grid"][k] for k in keys))
    )
    learned = [
        ModelSpec("ridge", lambda **p: RidgeModel(features, **p), ridge_grid),
        ModelSpec(
            "lightgbm", lambda **p: LightGBMModel(features, seed=settings.seed, **p), lgbm_grid
        ),
    ]
    mean = ModelSpec("historical_mean", HistoricalMeanModel)
    if target.kind == "return":
        specs = [ModelSpec("zero", ZeroModel), mean, *learned]
        return ModelPlan(specs, "historical_mean", ["ridge", "lightgbm"], "zero")
    if target.kind == "volatility":
        column = f"rvol_{target.horizon}"
        if column not in features:
            raise ValueError(f"{target.name}: no trailing feature {column} for the baseline")
        trailing = ModelSpec("trailing_vol", lambda: TrailingFeatureModel(column))
        return ModelPlan(
            [trailing, mean, *learned], "trailing_vol", ["ridge", "lightgbm"], None, signed=False
        )
    raise ValueError(f"unknown target kind {target.kind!r}")


def fold_cutoffs(
    assets: list[Asset], settings: Settings, years: list[int]
) -> dict[int, dict[str, pd.Timestamp]]:
    """Training cutoff per test year: the earliest last session of the year before.

    The same date is used for every market, so no training label of one market
    ends after a test origin of another (DECISIONS.md D-32).
    """
    codes = {a.market: a.calendar for a in assets if a.role == "target"}
    out = {}
    for year in years:
        cutoff = min(
            calendars.last_session_of_year(code, year - 1, settings.holidays_for(code))
            for code in codes.values()
        )
        out[year] = dict.fromkeys(codes, cutoff)
    return out


def evaluate_target(
    samples: pd.DataFrame,
    plan: ModelPlan,
    cutoffs: dict[int, dict[str, pd.Timestamp]],
    settings: Settings,
) -> dict[str, Any]:
    """Run the walk-forward for one target and compute every reported table."""
    cfg = settings.evaluation
    first = int(cfg["first_test_year"])
    last = int(samples.loc[samples["y"].notna(), "test_year"].max())
    predictions, folds = run_walk_forward(
        samples,
        plan.specs,
        list(range(first, last + 1)),
        cutoffs,
        int(cfg["inner_validation_years"]),
        int(cfg["min_inner_train_rows"]),
    )
    names = plan.names

    def metrics(by: str | None = None) -> pd.DataFrame:
        table = summarise(predictions, names, plan.baseline, by, plan.reference)
        return table if plan.signed else table.drop(columns="directional_accuracy")

    overall = metrics()
    yearly = yearly_comparison(predictions, names, plan.baseline)
    level = float(cfg["interval"]["level"])
    intervals = pd.concat(
        [
            add_intervals(predictions, name, level, int(cfg["interval"]["min_prior_test_years"]))
            for name in names
        ],
        ignore_index=True,
    )
    return {
        "predictions": predictions,
        "folds": folds,
        "overall": overall,
        "yearly": yearly,
        "by_market": metrics("market"),
        "by_symbol": metrics("symbol"),
        "intervals": intervals,
        "interval_overall": interval_summary(intervals),
        "interval_by_market": interval_summary(intervals, "market"),
        "selection": apply_selection_rule(overall, yearly, plan.candidates, plan.baseline),
    }
