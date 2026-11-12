"""Data-quality checks on cleaned daily bars. Checks flag; they never repair."""

from __future__ import annotations

import pandas as pd

ISSUE_COLUMNS = ["symbol", "check", "severity", "date", "detail"]
PRICE_COLUMNS = ["open", "high", "low", "close"]


def _issues(symbol: str, check: str, severity: str, dates, details) -> pd.DataFrame:
    dates = list(dates)
    if isinstance(details, str):
        details = [details] * len(dates)
    return pd.DataFrame(
        {
            "symbol": symbol,
            "check": check,
            "severity": severity,
            "date": pd.to_datetime(dates),
            "detail": list(details),
        },
        columns=ISSUE_COLUMNS,
    )


def validate_prices(
    bars: pd.DataFrame,
    symbol: str,
    expected_sessions: pd.DatetimeIndex | None,
    *,
    max_abs_daily_return: float,
    check_volume: bool,
) -> pd.DataFrame:
    """Run all checks on one symbol's bars and return one row per issue.

    ``bars`` has a ``date`` column plus open, high, low, close, volume and
    stock_splits. ``expected_sessions`` is the trading calendar over the span
    of the data, or ``None`` when no exchange calendar applies.
    """
    found: list[pd.DataFrame] = []
    dates = bars["date"]

    dup = bars[dates.duplicated(keep=False)]
    found.append(_issues(symbol, "duplicate_date", "error", dup["date"], "date appears twice"))

    for column in PRICE_COLUMNS:
        bad = bars[bars[column].isna()]
        found.append(_issues(symbol, "missing_price", "error", bad["date"], f"{column} is NaN"))
        bad = bars[bars[column] <= 0]
        found.append(
            _issues(symbol, "non_positive_price", "error", bad["date"], f"{column} <= 0")
        )

    body_high = bars[["open", "close", "low"]].max(axis=1)
    body_low = bars[["open", "close", "high"]].min(axis=1)
    bad = bars[(bars["high"] < body_high) | (bars["low"] > body_low)]
    found.append(
        _issues(symbol, "ohlc_inconsistent", "warning", bad["date"], "high/low do not bound bar")
    )

    if expected_sessions is not None and not bars.empty:
        span = expected_sessions[
            (expected_sessions >= dates.min()) & (expected_sessions <= dates.max())
        ]
        have = pd.DatetimeIndex(dates.unique())
        found.append(
            _issues(
                symbol,
                "missing_session",
                "warning",
                span.difference(have),
                "calendar session without a bar",
            )
        )
        found.append(
            _issues(
                symbol,
                "unexpected_bar",
                "warning",
                have.difference(expected_sessions),
                "bar on a date the calendar marks closed",
            )
        )

    if check_volume:
        bad = bars[bars["volume"] <= 0]
        found.append(_issues(symbol, "zero_volume", "warning", bad["date"], "volume is zero"))

    ordered = bars.drop_duplicates("date").sort_values("date")
    ret = ordered["close"].pct_change(fill_method=None)
    is_split = ordered["stock_splits"].fillna(0) != 0
    big = ret.abs() > max_abs_daily_return
    jump = ordered[big & ~is_split]
    found.append(
        _issues(
            symbol,
            "jump",
            "warning",
            jump["date"],
            [f"close-to-close return {r:+.1%}, no split recorded" for r in ret[big & ~is_split]],
        )
    )
    broken = ordered[big & is_split]
    found.append(
        _issues(
            symbol,
            "split_discontinuity",
            "error",
            broken["date"],
            [
                f"return {r:+.1%} on split day: close is not split-adjusted"
                for r in ret[big & is_split]
            ],
        )
    )

    found = [f for f in found if not f.empty]
    if not found:
        return pd.DataFrame(columns=ISSUE_COLUMNS)
    return pd.concat(found, ignore_index=True).sort_values(["date", "check"], ignore_index=True)


def check_split(
    bars: pd.DataFrame, split_date: pd.Timestamp, ratio: float, max_abs_daily_return: float
) -> dict[str, object]:
    """Verify price-return semantics around one known split.

    Passes when the provider records the split on that date, ``close`` is
    continuous across it (split-adjusted), and ``close`` differs from
    ``adj_close`` before it (not dividend-adjusted, where dividends exist).
    """
    ordered = bars.sort_values("date").reset_index(drop=True)
    row = ordered.index[ordered["date"] == split_date]
    if len(row) == 0 or row[0] == 0:
        return {"passed": False, "reason": "no bar on split date or no prior bar"}
    i = int(row[0])
    prev_close = float(ordered.loc[i - 1, "close"])
    close = float(ordered.loc[i, "close"])
    day_return = close / prev_close - 1
    recorded = float(ordered.loc[i, "stock_splits"])
    prior = ordered.iloc[:i]
    dividends_before = bool((prior["dividends"] > 0).any())
    differs = bool(((prior["close"] - prior["adj_close"]).abs() > 1e-9 * prior["close"]).any())
    passed = (
        abs(recorded - ratio) < 1e-9
        and abs(day_return) <= max_abs_daily_return
        and (differs or not dividends_before)
    )
    return {
        "passed": passed,
        "recorded_ratio": recorded,
        "prev_date": ordered.loc[i - 1, "date"],
        "prev_close": prev_close,
        "close": close,
        "day_return": day_return,
        "implied_unadjusted_prev_close": prev_close * ratio,
        "close_differs_from_adj_close": differs,
        "dividends_before_split": dividends_before,
    }
