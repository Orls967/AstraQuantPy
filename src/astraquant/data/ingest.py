"""Ingestion: download, store raw immutably, clean, validate, write Parquet."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from astraquant import calendars
from astraquant.config import Asset, Settings
from astraquant.data.provider import PriceProvider
from astraquant.data.validation import ISSUE_COLUMNS, check_split, validate_prices

COLUMN_MAP = {
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",  # split-adjusted, not dividend-adjusted: the price-return series
    "Adj Close": "adj_close",  # dividend-adjusted; kept for reference only
    "Volume": "volume",
    "Dividends": "dividends",
    "Stock Splits": "stock_splits",
}
PROCESSED_COLUMNS = ["date", "symbol", "market", "currency", *COLUMN_MAP.values()]


@dataclass
class IngestResult:
    """Everything one ingest run produced."""

    run_id: str
    raw_dir: Path
    summary: pd.DataFrame
    issues: pd.DataFrame
    split_checks: list[dict[str, Any]]
    manifest: dict[str, Any]


def completed_cutoff(asset: Asset, now: pd.Timestamp, settings: Settings) -> pd.Timestamp:
    """Last date whose bar is final at ``now`` for this asset."""
    if asset.calendar is not None:
        return calendars.last_completed_session(
            asset.calendar, now, settings.holidays_for(asset.calendar)
        )
    # No exchange calendar (FX): the last weekday strictly before today's UTC date.
    today = now.tz_convert("UTC").tz_localize(None).normalize()
    return pd.bdate_range(end=today - pd.Timedelta(days=1), periods=1)[0]


def expected_sessions(asset: Asset, start, end, settings: Settings) -> pd.DatetimeIndex:
    """Sessions on which a bar is expected for this asset."""
    if asset.calendar is None:
        return pd.bdate_range(start, end, name="date")
    return calendars.sessions(asset.calendar, start, end, settings.holidays_for(asset.calendar))


def clean_bars(
    raw: pd.DataFrame,
    asset: Asset,
    cutoff: pd.Timestamp,
    sessions: pd.DatetimeIndex | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Turn a provider frame into the processed schema.

    Drops three kinds of rows, and counts each: bars after ``cutoff`` (session
    still open at retrieval), rows with no prices at all, and zero-volume bars
    on dates the exchange calendar marks closed. The last kind is a provider
    placeholder that repeats the previous close on a holiday, which would be a
    forward-fill across a non-trading day. Nothing is filled or interpolated.
    """
    frame = raw.rename(columns=COLUMN_MAP).copy()
    index = pd.DatetimeIndex(frame.index)
    if index.tz is not None:
        index = index.tz_localize(None)  # keep the exchange-local wall date
    frame.insert(0, "date", index.normalize().astype("datetime64[ns]"))
    frame = frame.reset_index(drop=True)

    after_cutoff = frame["date"] > cutoff
    empty = frame[["open", "high", "low", "close"]].isna().all(axis=1) & ~after_cutoff
    closed_day = pd.Series(False, index=frame.index)
    if sessions is not None:
        closed_day = ~frame["date"].isin(sessions) & (frame["volume"] == 0) & ~after_cutoff & ~empty
    frame = frame[~after_cutoff & ~empty & ~closed_day].sort_values("date", kind="stable")
    frame["symbol"] = asset.symbol
    frame["market"] = asset.market
    frame["currency"] = asset.currency
    counts = {
        "dropped_incomplete": int(after_cutoff.sum()),
        "dropped_empty": int(empty.sum()),
        "dropped_closed_day": int(closed_day.sum()),
    }
    return frame[PROCESSED_COLUMNS].reset_index(drop=True), counts


def _write_raw(raw: pd.DataFrame, path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"raw file already exists and is immutable: {path}")
    raw.reset_index().to_parquet(path, index=False)


def run_ingest(
    assets: list[Asset],
    settings: Settings,
    provider: PriceProvider,
    now: pd.Timestamp,
    run_meta: dict[str, Any] | None = None,
) -> IngestResult:
    """Download every asset, store raw and processed data, and validate.

    Raw files go to a new ``raw_dir/<provider>/<run_id>/`` directory that is
    never rewritten. Processed files are derived artifacts and are replaced.
    """
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    run_id = now.tz_convert("UTC").strftime("%Y%m%dT%H%M%SZ")
    raw_dir = settings.raw_dir / provider.name / run_id
    raw_dir.mkdir(parents=True, exist_ok=False)
    prices_dir = settings.processed_dir / "prices"
    prices_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    issues: list[pd.DataFrame] = []
    cleaned: dict[str, pd.DataFrame] = {}
    for asset in assets:
        raw = provider.fetch(asset.symbol, settings.start_date)
        _write_raw(raw, raw_dir / f"{asset.file_stem}.parquet")
        cutoff = completed_cutoff(asset, now, settings)
        sessions = expected_sessions(asset, settings.start_date, cutoff, settings)
        bars, counts = clean_bars(
            raw, asset, cutoff, sessions if asset.calendar is not None else None
        )
        bars.to_parquet(prices_dir / f"{asset.file_stem}.parquet", index=False)
        cleaned[asset.symbol] = bars
        found = validate_prices(
            bars,
            asset.symbol,
            sessions,
            max_abs_daily_return=settings.max_abs_daily_return,
            check_volume=asset.role == "target",
        )
        issues.append(found)
        rows.append(
            {
                "symbol": asset.symbol,
                "market": asset.market,
                "role": asset.role,
                "currency": asset.currency,
                "rows": len(bars),
                "first_date": bars["date"].min(),
                "last_date": bars["date"].max(),
                "data_through": cutoff,
                **counts,
                "splits": int((bars["stock_splits"] != 0).sum()),
                "dividends": int((bars["dividends"] > 0).sum()),
                "errors": int((found["severity"] == "error").sum()),
                "warnings": int((found["severity"] == "warning").sum()),
            }
        )

    summary = pd.DataFrame(rows)
    non_empty = [f for f in issues if not f.empty]
    all_issues = (
        pd.concat(non_empty, ignore_index=True)
        if non_empty
        else pd.DataFrame(columns=ISSUE_COLUMNS)
    )
    all_issues.to_parquet(settings.processed_dir / "quality_issues.parquet", index=False)

    split_results: list[dict[str, Any]] = []
    for check in settings.split_checks:
        result: dict[str, Any] = {"symbol": check.symbol, "date": check.date, "ratio": check.ratio}
        if check.symbol in cleaned:
            result |= check_split(
                cleaned[check.symbol],
                pd.Timestamp(check.date),
                check.ratio,
                settings.max_abs_daily_return,
            )
        else:
            result |= {"passed": False, "reason": "symbol not ingested"}
        split_results.append(result)

    manifest = {
        "run_id": run_id,
        "retrieved_at_utc": now.tz_convert("UTC").isoformat(),
        "source": provider.name,
        "source_version": provider.version(),
        "source_note": "unofficial data source; prototyping only",
        "start_date": settings.start_date.isoformat(),
        "price_semantics": "close = split-adjusted, not dividend-adjusted (auto_adjust=False)",
        "symbols": [a.symbol for a in assets],
        "data_through": {
            market: group["data_through"].min().date().isoformat()
            for market, group in summary.groupby("market")
        },
        **(run_meta or {}),
    }
    text = json.dumps(manifest, indent=2, default=str)
    (raw_dir / "manifest.json").write_text(text, encoding="utf-8")
    (settings.processed_dir / "manifest.json").write_text(text, encoding="utf-8")
    return IngestResult(run_id, raw_dir, summary, all_issues, split_results, manifest)
