"""Compare the IDX trading calendar with the bars Yahoo actually has.

Report only: this script never changes the calendar. It reads the most recent
raw download (untouched provider data) and writes
``reports/idx_calendar_reconciliation.md``.

Usage: python scripts/reconcile_idx_calendar.py [first_year] [last_year]
"""

from __future__ import annotations

import sys

import pandas as pd

from astraquant import calendars
from astraquant.config import REPO_ROOT, load_assets, load_settings

CALENDAR = "XIDX"


def _raw_dates(run_dir, asset, traded_only: bool) -> pd.DatetimeIndex:
    frame = pd.read_parquet(run_dir / f"{asset.file_stem}.parquet")
    if traded_only:
        frame = frame[frame["Volume"] > 0]
    stamps = pd.DatetimeIndex(frame["Date"])
    if stamps.tz is not None:
        stamps = stamps.tz_localize(None)
    return pd.DatetimeIndex(stamps.normalize().unique())


def main() -> int:
    """Write the reconciliation report and print the per-year table."""
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 2010
    last = int(sys.argv[2]) if len(sys.argv) > 2 else 2025
    settings = load_settings()
    assets = load_assets()
    index_symbol = settings.context["ID"]["index"]
    index_asset = next(a for a in assets if a.symbol == index_symbol)
    banks = [a for a in assets if a.calendar == CALENDAR and a.role == "target"]
    run_dir = sorted((settings.raw_dir / settings.provider).iterdir())[-1]

    start, end = f"{first}-01-01", f"{last}-12-31"
    holidays = settings.holidays_for(CALENDAR)
    configured = calendars.sessions(CALENDAR, start, end, holidays)
    library = calendars.sessions(CALENDAR, start, end)
    index_days = _raw_dates(run_dir, index_asset, traded_only=False)
    index_days = index_days[(index_days >= start) & (index_days <= end)]
    traded = {b.symbol: _raw_dates(run_dir, b, traded_only=True) for b in banks}

    def banks_traded(day: pd.Timestamp) -> int:
        return sum(day in days for days in traded.values())

    rows = []
    for year in range(first, last + 1):
        cal = configured[configured.year == year]
        idx = index_days[index_days.year == year]
        rows.append(
            {
                "year": year,
                "library sessions": int((library.year == year).sum()),
                "calendar sessions": len(cal),
                f"days with {index_symbol} bar": len(idx),
                "calendar, no index bar": len(cal.difference(idx)),
                "index bar, calendar closed": len(idx.difference(cal)),
            }
        )
    table = pd.DataFrame(rows)
    totals = table.drop(columns="year").sum().to_dict() | {"year": "total"}
    table = pd.concat([table, pd.DataFrame([totals])], ignore_index=True)

    def listing(days: pd.DatetimeIndex) -> list[str]:
        if days.empty:
            return ["_None._", ""]
        out = ["| date | weekday | banks with a traded bar (volume > 0) |", "|---|---|---|"]
        out += [
            f"| {d.date()} | {d.day_name()} | {banks_traded(d)} of {len(banks)} |" for d in days
        ]
        return [*out, ""]

    overrides = [d for d in pd.to_datetime(list(holidays)) if first <= d.year <= last]
    header = "| " + " | ".join(table.columns) + " |"
    rule = "|" + "|".join("---" for _ in table.columns) + "|"
    body = ["| " + " | ".join(str(v) for v in r) + " |" for r in table.itertuples(index=False)]
    lines = [
        f"# IDX calendar reconciliation, {first} to {last}",
        "",
        f"- Raw run: `{run_dir.name}` (Yahoo Finance via yfinance, unofficial).",
        f"- **Library sessions**: `exchange_calendars` {CALENDAR} with no overrides.",
        "- **Calendar sessions**: the library minus the holidays in `configs/settings.yaml`.",
        f"  Overrides inside this range: {', '.join(str(d.date()) for d in overrides) or 'none'}.",
        f"- **Days with {index_symbol} bar**: dates in the raw download, before any cleaning.",
        "- This is a report. The calendar was not changed because of it.",
        f"- Caveat: {index_symbol} from Yahoo is not an official record of trading days. A",
        "  difference means the two sources disagree, not that either is proven wrong.",
        "",
        "## Per year",
        "",
        header,
        rule,
        *body,
        "",
        f"## Calendar session without a {index_symbol} bar",
        "",
        *listing(configured.difference(index_days)),
        f"## {index_symbol} bar on a date the calendar marks closed",
        "",
        *listing(index_days.difference(configured)),
    ]
    path = REPO_ROOT / "reports" / "idx_calendar_reconciliation.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(table.to_string(index=False))
    print(f"\nreport: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
