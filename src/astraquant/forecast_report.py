"""Markdown report for one stored forecast run (blueprint section 9, Milestone 4)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from astraquant.evaluation.intervals import interval_summary
from astraquant.evaluation.metrics import summarise, yearly_comparison
from astraquant.evaluation.report import table


def _pct(value: float) -> str:
    return f"{value:+.1%}"


def _forecast_table(stored: pd.DataFrame) -> pd.DataFrame:
    price = stored["target_start_price"]
    return pd.DataFrame(
        {
            "ticker": stored["ticker"],
            "currency": stored["currency"],
            "origin": stored["forecast_origin_date"],
            "target end": stored["target_end_date"],
            "start price": price.map(lambda v: f"{v:,.2f}"),
            "point": stored["point_estimate"].map(_pct),
            "lower": stored["interval_lower"].map(_pct),
            "upper": stored["interval_upper"].map(_pct),
            "price at lower": (price * (1 + stored["interval_lower"])).map(lambda v: f"{v:,.2f}"),
            "price at upper": (price * (1 + stored["interval_upper"])).map(lambda v: f"{v:,.2f}"),
        }
    )


def render_forecast_report(
    stored: pd.DataFrame,
    run: dict[str, Any],
    evaluation: dict[str, Any],
    predictions: pd.DataFrame,
    intervals: pd.DataFrame,
    title: str,
    official: bool,
) -> str:
    """Report for the forecasts of one run, as read back from the ledger.

    ``evaluation`` is the stored ``results.json``; ``predictions`` and
    ``intervals`` are the walk-forward outputs of the quarterly target.
    """
    selection = evaluation["selection"][evaluation["primary_target"]]
    chosen, baseline = selection["selected"], selection["baseline"]
    names = [c.removeprefix("pred_") for c in predictions.columns if c.startswith("pred_")]
    level = float(stored["interval_level"].iloc[0])
    overall = summarise(predictions, names, baseline, reference="zero").drop(columns="group")
    by_market = summarise(predictions, names, baseline, "market", "zero")
    yearly = yearly_comparison(predictions, names, baseline)
    coverage = interval_summary(intervals[intervals["model"] == chosen], "market")
    through = ", ".join(f"{m} {d}" for m, d in run["data_through"].items())
    types = ", ".join(f"`{t}`" for t in sorted(stored["target_type"].unique()))
    if chosen == baseline:
        verdict = (
            f"**No model beat the baseline in the walk-forward evaluation. The forecast below "
            f"is the baseline (`{baseline}`) with empirical prediction intervals.**"
        )
    else:
        verdict = f"**`{chosen}` met the selection rule and replaces the baseline `{baseline}`.**"
    status = (
        "Stored in the append-only ledger. These rows are frozen."
        if official
        else "**REHEARSAL ONLY. Not a forecast, not in the ledger. Do not use these numbers.**"
    )
    lines = [
        f"# {title}",
        "",
        status,
        "",
        "Research and decision support only. Not investment advice.",
        "",
        f"- Run `{run['run_id']}`, created {run['created_at_utc']}; target type {types}.",
        f"- Git commit: `{run['git_commit']}`; config digest `{run['config_digest']}`; "
        f"seed {run['seed']}.",
        f"- Data through: {through}. Source: Yahoo Finance through yfinance. "
        "**Unofficial data, prototyping only.**",
        "",
        "## Forecast",
        "",
        verdict,
        "",
        f"Price return in local currency from the origin close to the target-end close, "
        f"with {level:.0%} prediction intervals.",
        "",
        table(_forecast_table(stored)),
        "The two price columns are the start price moved by the interval bounds. They are "
        "not price targets.",
        "",
        "## Method",
        "",
        "- Target: `close[target end] / close[origin] - 1` on split-adjusted, not "
        "dividend-adjusted, closes. Origin and end are the last sessions of the previous "
        "quarter and of the quarter on each exchange's own calendar.",
        "- Models compared, in this order: zero return, historical mean, Ridge, LightGBM. "
        "Expanding-window walk-forward with yearly test blocks; training labels fully "
        "realised before each test block; scaling and tuning inside the training window.",
        "- Selection rule, fixed before any model was run: a model replaces the baseline "
        "only if pooled `R2_oos > 0` and it beats the baseline in more than half of the "
        "test years.",
        f"- Point estimate: `{chosen}` fitted on quarters realised by the cutoff "
        f"({run['cutoff']}, the earliest origin across exchanges).",
        f"- Interval: point estimate plus the {(1 - level) / 2:.0%} and "
        f"{1 - (1 - level) / 2:.0%} quantiles of that model's walk-forward residuals, "
        "per market.",
        "- Details: `docs/PROJECT_BLUEPRINT.md` section 8 and `docs/DECISIONS.md` "
        "sections 8 and 9.",
        "",
        "## Walk-forward results on the quarterly target",
        "",
        "Selection rule checks:",
        "",
        table(pd.DataFrame(selection["checks"])),
        f"Pooled metrics (`r2_oos` against `{baseline}`):",
        "",
        table(overall),
        "By market:",
        "",
        table(by_market),
        "By test year (sum of squared errors):",
        "",
        table(yearly),
        "## How well the intervals worked in the past",
        "",
        f"Out-of-sample coverage of the {level:.0%} interval of `{chosen}` in the "
        "walk-forward (each year's interval built from earlier years only):",
        "",
        table(coverage),
        f"Coverage below {level:.0%} means the interval was too narrow in the past. The "
        "method was not adjusted after seeing this.",
        "",
        "## Limitations",
        "",
        "- **Selection bias.** The 11 names were chosen with hindsight because they are "
        "today's winners. Their historical mean return is high for that reason, and the "
        "forecast inherits it. Results do not generalise to stocks in general.",
        "- **Small sample.** About four quarterly observations per stock per year, from "
        "highly correlated names.",
        "- **Unofficial data.** Yahoo Finance prices, including unrecorded adjustments at "
        "Indonesian rights-issue dates (`docs/DECISIONS.md` 6.3).",
        "- **Intervals assume the future resembles the past.** They are prediction "
        "intervals from past forecast errors, not guarantees.",
        "- No fundamentals, macro data or news are used.",
        "",
    ]
    return "\n".join(lines)
