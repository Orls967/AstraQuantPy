"""Synthetic walk-forward samples for evaluation tests. No real data."""

from __future__ import annotations

import numpy as np
import pandas as pd

from astraquant import calendars

SYMBOLS = {"AAA": "US", "BBB": "US", "CCC.JK": "ID", "DDD.JK": "ID"}
CODES = {"US": "XNYS", "ID": "XIDX"}


def quarterly_frame(
    features: list[str], first_year: int = 2011, last_year: int = 2020, seed: int = 7
) -> pd.DataFrame:
    """Quarterly samples on the real calendars with random features and a weak signal."""
    rng = np.random.default_rng(seed)
    rows = []
    for period in pd.period_range(f"{first_year}Q1", f"{last_year}Q4", freq="Q"):
        for symbol, market in SYMBOLS.items():
            code = CODES[market]
            origin = calendars.last_session_on_or_before(
                code, period.start_time.normalize() - pd.Timedelta(days=1)
            )
            end = calendars.last_session_on_or_before(code, period.end_time.normalize())
            values = dict(zip(features, rng.normal(size=len(features)), strict=True))
            values["is_id"] = int(market == "ID")
            if market != "ID":
                values.update({c: np.nan for c in features if c.startswith("fx_")})
            signal = 0.05 * values[features[0]]
            rows.append(
                {
                    "symbol": symbol,
                    "market": market,
                    "origin_date": origin,
                    "target_end_date": end,
                    "test_year": period.year,
                    "y": signal + rng.normal(0.02, 0.08),
                    "complete": True,
                    **values,
                }
            )
    return pd.DataFrame(rows)


def cutoffs(years: range) -> dict[int, dict[str, pd.Timestamp]]:
    """One shared cutoff per year: the earlier of the two last sessions of the year before."""
    out = {}
    for year in years:
        day = min(calendars.last_session_of_year(code, year - 1) for code in CODES.values())
        out[year] = dict.fromkeys(CODES, day)
    return out
