"""Calendar-quarter forecast with the model the evaluation selected.

Nothing is chosen here. The model comes from the stored selection, the
training rows follow the walk-forward cutoff rule, and the interval comes
from that model's walk-forward residuals (DECISIONS.md section 9).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from astraquant.config import Asset, Settings
from astraquant.evaluation import protocol
from astraquant.evaluation.samples import quarterly_samples
from astraquant.evaluation.walkforward import Fold, choose_params, training_mask


def forecast_quarter(
    quarterly: pd.DataFrame,
    predictions: pd.DataFrame,
    selection: dict[str, Any],
    assets: list[Asset],
    settings: Settings,
    quarter: str,
) -> pd.DataFrame:
    """One forecast row per target asset for ``quarter`` (for example ``"2027Q1"``).

    ``predictions`` are the walk-forward test predictions of the quarterly
    target; ``selection`` is the stored outcome of the selection rule. Only
    rows realised by the cutoff (the earliest origin of the quarter across
    exchanges) are used, for fitting and for the residuals.
    """
    cfg = settings.evaluation
    quarterly = quarterly.reset_index(drop=True)
    targets = [a for a in assets if a.role == "target"]
    samples = quarterly_samples(
        quarterly, protocol.model_features(settings), protocol.fx_markets(settings)
    )
    rows = samples[samples["quarter"] == quarter]
    absent = sorted({a.symbol for a in targets} - set(rows["symbol"]))
    if absent:
        raise ValueError(f"{quarter}: no origin row for {absent}; the origin session has no data")

    cutoff = rows["origin_date"].min()
    history = samples[training_mask(samples, dict.fromkeys(samples["market"].unique(), cutoff))]
    year = int(quarter[:4])
    fold = Fold(year, history[history["complete"]], history, rows)

    name = selection["selected"]
    plan = protocol.model_plan(protocol.target_specs(settings)[0], settings)
    spec = next(s for s in plan.specs if s.name == name)
    if name in plan.candidates and not rows["complete"].all():
        lacking = rows.loc[~rows["complete"], "symbol"].tolist()
        raise ValueError(f"{name} needs a complete feature vector; missing for {lacking}")
    years = list(range(int(samples["test_year"].min()) + 1, year + 1))
    params = choose_params(
        spec,
        fold,
        protocol.fold_cutoffs(assets, settings, years),
        int(cfg["inner_validation_years"]),
        int(cfg["min_inner_train_rows"]),
    )
    model = spec.factory(**params)
    model.fit(fold.train, fold.history)
    point = model.predict(rows)

    level = float(cfg["interval"]["level"])
    past = predictions[predictions["target_end_date"] <= cutoff]
    residual = (past["y"] - past[f"pred_{name}"]).groupby(past["market"])
    low = residual.quantile((1 - level) / 2)
    high = residual.quantile(1 - (1 - level) / 2)
    unknown = sorted(set(rows["market"]) - set(low.index))
    if unknown:
        raise ValueError(f"no walk-forward residuals for markets {unknown}")

    detail = quarterly.loc[rows.index, ["currency", "target_start_price"]]
    by_symbol = {a.symbol: a for a in targets}
    out = pd.DataFrame(
        {
            "ticker": rows["symbol"].to_numpy(),
            "market": rows["market"].to_numpy(),
            "exchange": [by_symbol[s].calendar for s in rows["symbol"]],
            "currency": detail["currency"].to_numpy(),
            "forecast_origin_date": rows["origin_date"].to_numpy(),
            "target_start_date": rows["origin_date"].to_numpy(),
            "target_start_price": detail["target_start_price"].to_numpy(),
            "target_end_date": rows["target_end_date"].to_numpy(),
            "point_estimate": point,
            "interval_level": level,
            "interval_lower": point + rows["market"].map(low).to_numpy(),
            "interval_upper": point + rows["market"].map(high).to_numpy(),
            "model_name": name,
            "history_rows": rows["symbol"].map(history.groupby("symbol").size()).to_numpy(),
            "residual_rows": rows["market"].map(residual.size()).to_numpy(),
        }
    )
    out.attrs["cutoff"] = cutoff
    out.attrs["params"] = params
    return out.reset_index(drop=True)


def readiness_problems(
    forecasts: pd.DataFrame, settings: Settings, pinned: dict[str, dict[str, Any]]
) -> list[str]:
    """Reasons the forecasts cannot be stored as the official record (empty if none)."""
    problems = []
    no_price = forecasts.loc[forecasts["target_start_price"].isna(), "ticker"].tolist()
    if no_price:
        problems.append(f"no closing price on the origin session for {no_price}")
    for exchange, part in forecasts.groupby("exchange"):
        want = pinned.get(exchange)
        if want is None:
            problems.append(f"no pinned target dates for {exchange}")
            continue
        start, end = pd.Timestamp(want["start"]), pd.Timestamp(want["end"])
        if not (part["target_start_date"] == start).all():
            problems.append(f"{exchange}: origin differs from the pinned {start.date()}")
        if not (part["target_end_date"] == end).all():
            problems.append(f"{exchange}: target end differs from the pinned {end.date()}")
    return problems


def is_late(forecasts: pd.DataFrame, data_through: dict[str, str]) -> bool:
    """True when the dataset already holds a session after some market's origin."""
    origin = forecasts.groupby("market")["forecast_origin_date"].max()
    return any(pd.Timestamp(data_through[market]) > day for market, day in origin.items())
