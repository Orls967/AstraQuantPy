"""Forecast targets.

Every function takes a series indexed by the **full session grid** of one
exchange (one row per trading session, NaN where a bar is missing). Horizons
are therefore counted in calendar sessions, never in available rows, and a
target that touches a missing bar is NaN.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from astraquant import calendars


def forward_return(close: pd.Series, horizon: int) -> pd.Series:
    """Price return from session ``t`` to session ``t + horizon``."""
    if horizon < 1:
        raise ValueError("horizon must be at least 1 session")
    return close.shift(-horizon) / close - 1.0


def forward_realised_vol(close: pd.Series, horizon: int, annualisation: int) -> pd.Series:
    """Annualised std of daily log returns over sessions ``t+1 .. t+horizon``.

    NaN unless all ``horizon`` daily returns exist.
    """
    if horizon < 2:
        raise ValueError("horizon must be at least 2 sessions")
    log_return = np.log(close).diff()
    window = log_return.rolling(horizon, min_periods=horizon).std()
    return window.shift(-horizon) * np.sqrt(annualisation)


def target_end_date(sessions: pd.DatetimeIndex, horizon: int) -> pd.Series:
    """Session ``horizon`` sessions after each origin (NaT near the end of the grid)."""
    return pd.Series(sessions, index=sessions).shift(-horizon)


def quarter_boundaries(
    code: str,
    first: pd.Timestamp,
    last: pd.Timestamp,
    extra_holidays: Iterable = (),
) -> pd.DataFrame:
    """Start and end session of each calendar quarter overlapping ``[first, last]``.

    ``target_start_date`` is the last session of the previous quarter (the
    forecast origin); ``target_end_date`` is the last session of the quarter.
    Quarters the calendar library does not fully cover are left out.
    """
    lower, upper = calendars.calendar_bounds(code)
    holidays = tuple(extra_holidays)
    rows = []
    for period in pd.period_range(first, last, freq="Q"):
        quarter_start = period.start_time.normalize()
        quarter_end = period.end_time.normalize()
        if quarter_start - pd.Timedelta(days=31) < lower or quarter_end > upper:
            continue
        start = calendars.last_session_on_or_before(
            code, quarter_start - pd.Timedelta(days=1), holidays
        )
        end = calendars.last_session_on_or_before(code, quarter_end, holidays)
        in_quarter = calendars.sessions(code, quarter_start, quarter_end, holidays)
        rows.append(
            {
                "quarter": str(period),
                "target_start_date": start,
                "target_end_date": end,
                "n_sessions": len(in_quarter),
            }
        )
    return pd.DataFrame(
        rows, columns=["quarter", "target_start_date", "target_end_date", "n_sessions"]
    )


def quarterly_returns(close: pd.Series, boundaries: pd.DataFrame) -> pd.DataFrame:
    """Calendar-quarter price return for each row of ``boundaries``.

    ``q_return`` is NaN when either boundary session has no bar, including
    quarters that have not ended yet.
    """
    out = boundaries.copy()
    start_price = close.reindex(out["target_start_date"]).to_numpy()
    end_price = close.reindex(out["target_end_date"]).to_numpy()
    out["target_start_price"] = start_price
    out["q_return"] = end_price / start_price - 1.0
    return out
