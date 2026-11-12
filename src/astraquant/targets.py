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


def _break_ahead(index: pd.DatetimeIndex, horizon: int, breaks: Iterable) -> pd.Series:
    """True where a price break falls in sessions ``t+1 .. t+horizon``."""
    flags = pd.Series(index.isin(pd.to_datetime(list(breaks))), index=index).astype(float)
    return flags.rolling(horizon, min_periods=1).sum().shift(-horizon).fillna(0) > 0


def forward_return(close: pd.Series, horizon: int, breaks: Iterable = ()) -> pd.Series:
    """Price return from session ``t`` to session ``t + horizon``.

    NaN when either end has no bar or the window crosses a price break.
    """
    if horizon < 1:
        raise ValueError("horizon must be at least 1 session")
    out = close.shift(-horizon) / close - 1.0
    return out.mask(_break_ahead(close.index, horizon, breaks))


def forward_realised_vol(
    close: pd.Series, horizon: int, annualisation: int, breaks: Iterable = ()
) -> pd.Series:
    """Annualised std of daily log returns over sessions ``t+1 .. t+horizon``.

    NaN unless all ``horizon`` daily returns exist and none is a price break.
    """
    if horizon < 2:
        raise ValueError("horizon must be at least 2 sessions")
    log_return = np.log(close).diff()
    window = log_return.rolling(horizon, min_periods=horizon).std()
    out = window.shift(-horizon) * np.sqrt(annualisation)
    return out.mask(_break_ahead(close.index, horizon, breaks))


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


def quarterly_returns(
    close: pd.Series, boundaries: pd.DataFrame, breaks: Iterable = ()
) -> pd.DataFrame:
    """Calendar-quarter price return for each row of ``boundaries``.

    ``q_return`` is NaN when either boundary session has no bar (including
    quarters that have not ended yet) or a price break falls after the start
    session and on or before the end session.
    """
    out = boundaries.copy()
    start_price = close.reindex(out["target_start_date"]).to_numpy()
    end_price = close.reindex(out["target_end_date"]).to_numpy()
    out["target_start_price"] = start_price
    out["q_return"] = end_price / start_price - 1.0
    for day in pd.to_datetime(list(breaks)):
        crossed = (out["target_start_date"] < day) & (day <= out["target_end_date"])
        out.loc[crossed, "q_return"] = np.nan
    return out
