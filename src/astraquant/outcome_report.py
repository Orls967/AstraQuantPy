"""Markdown report of realised outcomes (blueprint section 9, Milestone 6)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from astraquant.evaluation.report import table
from astraquant.outcomes import outcome_summary


def _pct(value: float) -> str:
    return f"{value:+.1%}"


def _per_stock(joined: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticker": joined["ticker"],
            "currency": joined["currency"],
            "start": joined["target_start_date"],
            "start price": joined["start_price_now"].map("{:,.2f}".format),
            "end": joined["target_end_date"],
            "end price": joined["end_price"].map("{:,.2f}".format),
            "forecast": joined["point_estimate"].map(_pct),
            "interval": [
                f"{_pct(lo)} to {_pct(hi)}"
                for lo, hi in zip(joined["interval_lower"], joined["interval_upper"], strict=True)
            ],
            "realised": joined["realised_return"].map(_pct),
            "error": joined["error"].map(_pct),
            "inside interval": joined["inside_interval"].map({1: "yes", 0: "no"}),
        }
    )


def _summary_table(summary: pd.DataFrame) -> pd.DataFrame:
    out = summary.copy()
    out["coverage"] = [
        f"{k} of {n} ({c:.0%})"
        for k, n, c in zip(out["inside_interval"], out["n"], out["coverage"], strict=True)
    ]
    for column in ("mae_forecast", "mae_zero", "rmse_forecast", "rmse_zero"):
        out[column] = out[column].map("{:.1%}".format)
    out["r2_vs_zero"] = out["r2_vs_zero"].map("{:+.3f}".format)
    out["same_sign"] = [f"{k} of {n}" for k, n in zip(out["same_sign"], out["n"], strict=True)]
    return out.drop(columns=["inside_interval", "nominal"])


def render_outcome_report(
    joined: pd.DataFrame, run: dict[str, Any], title: str, official: bool, other_runs: int
) -> str:
    """Report for the outcomes of one forecast run.

    ``joined`` holds the forecast rows of that run with their outcomes, as read
    back from the ledger.
    """
    first = joined.iloc[0]
    level = float(first["interval_level"])
    overall = outcome_summary(joined).iloc[0]
    by_exchange = outcome_summary(joined, "exchange")
    outside = joined.loc[joined["inside_interval"] == 0, "ticker"].tolist()
    changed = joined[joined["start_price_changed"] == 1]
    better = overall["rmse_forecast"] < overall["rmse_zero"]

    parts = [
        f"# {title}",
        "",
        (
            "- Official record: outcomes of the frozen forecast in the append-only ledger."
            if official
            else "- **REHEARSAL ONLY.** Produced by `record_outcomes.py --dry-run` on a rehearsal"
            " forecast to test the pipeline. Not a result of the project."
        ),
        f"- Forecast run `{first['run_id']}` (target type `{first['target_type']}`, model"
        f" `{first['model_name']}`, created {first['created_at_utc'][:19]} UTC).",
        f"- Outcomes recorded {run['created_at_utc'][:19]} UTC in run `{run['run_id']}`,"
        f" commit `{run['git_commit'][:7]}`.",
        "- Data through: " + ", ".join(f"{m} {d}" for m, d in run["data_through"].items()),
        "- Source: Yahoo Finance through yfinance. **Unofficial data, prototyping only.**",
        "- Realised return = close on the last session of the quarter / close on the origin"
        " session - 1, split-adjusted, not dividend-adjusted, local currency.",
        f"- Other forecast runs of this type in the ledger: {other_runs}. This report covers"
        " the first one, which is the frozen forecast.",
        "",
        "## Per stock",
        "",
        table(_per_stock(joined)),
        f"## Interval coverage and error ({level:.0%} prediction interval)",
        "",
        table(
            _summary_table(
                pd.concat(
                    [outcome_summary(joined), by_exchange.rename(columns={"exchange": "group"})],
                    ignore_index=True,
                )
            )
        ),
        "`mae` and `rmse` are in return points. `zero` is a forecast of 0% for every stock."
        " `r2_vs_zero` = 1 - SSE of the forecast / SSE of the zero forecast. `same_sign` counts"
        " stocks whose forecast and realised return have the same sign.",
        "",
        "## Post-mortem",
        "",
        f"- {int(overall['inside_interval'])} of {int(overall['n'])} realised returns fell inside"
        f" the {level:.0%} prediction interval ({overall['coverage']:.0%}; nominal {level:.0%}).",
        "- Outside the interval: " + (", ".join(outside) if outside else "none") + ".",
        f"- Against a zero-return forecast the stored forecast had a"
        f" {'lower' if better else 'higher'} RMSE ({overall['rmse_forecast']:.1%} against"
        f" {overall['rmse_zero']:.1%}).",
        "- Start price changed since the forecast was stored: "
        + (
            ", ".join(
                f"{t} ({a:,.2f} stored, {b:,.2f} now)"
                for t, a, b in zip(
                    changed["ticker"],
                    changed["start_price_stored"],
                    changed["start_price_now"],
                    strict=True,
                )
            )
            + ". Check for a split or another corporate action; the realised return uses"
            " today's prices on both dates."
            if len(changed)
            else "none."
        ),
        "",
        "## How to read this",
        "",
        "- This is one quarter and the stocks move together, so these rows are far from"
        " independent observations. A coverage figure from one quarter says little about"
        " whether the interval is well calibrated; the walk-forward coverage in"
        " `reports/evaluation/summary.md` rests on many more quarters.",
        "- One quarter cannot show that a model has or lacks skill.",
        "- The names were chosen with hindsight; nothing here generalises to stocks in general.",
        "- A rights issue or other corporate action during the quarter can distort the"
        " provider's prices without a record (`docs/DECISIONS.md` 6.3). Check the quarter for"
        " such events before relying on a single stock's row.",
        "",
    ]
    return "\n".join(parts)
