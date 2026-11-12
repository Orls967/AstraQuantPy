"""Render the data-quality report as Markdown."""

from __future__ import annotations

import pandas as pd

from astraquant.config import Asset
from astraquant.data.ingest import IngestResult


def _table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_None._\n"
    header = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    rows = frame.itertuples(index=False)
    body = ["| " + " | ".join(_cell(v) for v in row) + " |" for row in rows]
    return "\n".join([header, rule, *body]) + "\n"


def _cell(value: object) -> str:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, float):
        return f"{value:,.4f}"
    return str(value)


def market_wide_gaps(issues: pd.DataFrame, summary: pd.DataFrame, assets: list[Asset]) -> dict:
    """Split missing sessions into market-wide and symbol-specific, per calendar.

    A session missing for every symbol of a calendar that had started trading
    points at the calendar (an unknown holiday), not at the data.
    """
    out: dict[str, dict[str, pd.DataFrame]] = {}
    first = summary.set_index("symbol")["first_date"]
    missing = issues[issues["check"] == "missing_session"]
    for code in sorted({a.calendar for a in assets if a.calendar}):
        symbols = [a.symbol for a in assets if a.calendar == code]
        sub = missing[missing["symbol"].isin(symbols)]
        if sub.empty:
            continue
        counts = sub.groupby("date")["symbol"].nunique()
        active = pd.Series(
            [int((first[symbols] <= day).sum()) for day in counts.index], index=counts.index
        )
        wide = counts[counts == active].index
        out[code] = {
            "market_wide": pd.DataFrame({"date": wide}),
            "specific": sub[~sub["date"].isin(wide)][["symbol", "date"]],
        }
    return out


def render_report(result: IngestResult, assets: list[Asset]) -> str:
    """Build the Markdown data-quality report for one ingest run."""
    m = result.manifest
    issues, summary = result.issues, result.summary
    parts = [
        "# Data-quality report",
        "",
        f"- Run: `{result.run_id}` (retrieved {m['retrieved_at_utc']})",
        f"- Source: {m['source']} {m['source_version']}. **Unofficial data, prototyping only.**",
        f"- Git commit: `{m.get('git_commit', 'unknown')}`"
        + (" (working tree had uncommitted changes)" if m.get("git_dirty") else ""),
        f"- Config digest: `{m.get('config_digest', 'unknown')}`",
        f"- Price semantics: {m['price_semantics']}",
        "- Data through: " + ", ".join(f"{k} {v}" for k, v in m["data_through"].items()),
        "- Checks flag problems. Nothing is repaired, filled or interpolated.",
        "- Rows dropped in cleaning (counted below): `dropped_incomplete` = session still open",
        "  at retrieval; `dropped_empty` = no prices; `dropped_excluded` = listed under",
        "  `exclusions` in the config; `dropped_closed_day` = zero-volume provider placeholder",
        "  on a date the calendar marks closed; `dropped_stale` = zero-volume bar of a target",
        "  equity on a real session, treated as a missing session.",
        "",
        "## Coverage",
        "",
        _table(summary.drop(columns=["currency"])),
        "## Issue counts by check",
        "",
    ]
    if issues.empty:
        parts.append("_No issues._\n")
    else:
        pivot = issues.pivot_table(
            index="symbol", columns="check", values="date", aggfunc="count", fill_value=0
        ).reset_index()
        parts.append(_table(pivot))

    errors = issues[issues["severity"] == "error"]
    parts += ["## Errors (all)", "", _table(errors[["symbol", "check", "date", "detail"]])]
    jumps = issues[issues["check"] == "jump"]
    parts += [
        "## Large moves without a recorded split (all)",
        "",
        _table(jumps[["symbol", "date", "detail"]]),
    ]

    parts += ["## Calendar cross-check", ""]
    gaps = market_wide_gaps(issues, summary, assets)
    if not gaps:
        parts.append("_No missing sessions against any calendar._\n")
    for code, group in gaps.items():
        wide, specific = group["market_wide"], group["specific"]
        parts += [
            f"### {code}",
            "",
            f"- Sessions with no bar for **any** symbol (calendar suspect): {len(wide)}",
            f"- Symbol-specific missing sessions: {len(specific)}",
            "",
        ]
        if not wide.empty:
            by_year = wide.groupby(wide["date"].dt.year).size().rename("sessions").reset_index()
            by_year.columns = ["year", "market-wide missing sessions"]
            parts.append(_table(by_year))
        if not specific.empty:
            by_symbol = specific.groupby("symbol").size().rename("missing sessions").reset_index()
            parts.append(_table(by_symbol))
    unexpected = issues[issues["check"] == "unexpected_bar"]
    parts += [
        f"Bars on dates the calendar marks closed: {len(unexpected)}.",
        "",
        _table(
            unexpected.groupby("symbol").size().rename("unexpected bars").reset_index()
            if not unexpected.empty
            else unexpected
        ),
    ]

    parts += ["## Price-return semantics: known splits", ""]
    parts.append(_table(pd.DataFrame(result.split_checks)))
    parts += [
        "A check passes when the provider records the split with the expected ratio, `close`",
        "is continuous across the split date (split-adjusted), and `close` differs from",
        "`adj_close` before it (not dividend-adjusted).",
        "",
        "## Limitations",
        "",
        "- Yahoo Finance data is unofficial and can be revised without notice.",
        "- The full list of flagged rows is in `data/processed/quality_issues.parquet`.",
        "- IDX holidays before 2026 come from the calendar library only; see the calendar",
        "  cross-check above for sessions it appears to get wrong.",
        "- Yahoo records no corporate action for rights issues, so `close` is not adjusted",
        "  for them (see DECISIONS.md).",
        "",
    ]
    return "\n".join(parts)
