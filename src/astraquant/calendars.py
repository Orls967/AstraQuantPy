"""Exchange trading calendars.

Sessions come from ``exchange_calendars`` with official holidays from
``configs/settings.yaml`` removed on top. The library is known to miss IDX
holidays (cuti bersama, lunar holidays), so it is never trusted alone for XIDX.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from functools import lru_cache

import exchange_calendars as xcals
import pandas as pd

DateLike = date | str | pd.Timestamp


@lru_cache(maxsize=8)
def _calendar(code: str) -> xcals.ExchangeCalendar:
    return xcals.get_calendar(code)


def _day(value: DateLike) -> pd.Timestamp:
    return pd.Timestamp(value).tz_localize(None).normalize()


def sessions(
    code: str, start: DateLike, end: DateLike, extra_holidays: Iterable[DateLike] = ()
) -> pd.DatetimeIndex:
    """Trading sessions (tz-naive dates) in ``[start, end]`` for a calendar code.

    The range is clamped to what the library covers; ``calendar_bounds`` exposes
    that coverage so callers can detect a request beyond it.
    """
    cal = _calendar(code)
    lo = max(_day(start), cal.first_session)
    hi = min(_day(end), cal.last_session)
    if lo > hi:
        return pd.DatetimeIndex([], name="date")
    out = cal.sessions_in_range(lo, hi)
    holidays = pd.DatetimeIndex([_day(d) for d in extra_holidays])
    return pd.DatetimeIndex(out.difference(holidays), name="date")


def calendar_bounds(code: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """First and last session the library knows for a calendar code."""
    cal = _calendar(code)
    return cal.first_session, cal.last_session


def last_session_on_or_before(
    code: str, day: DateLike, extra_holidays: Iterable[DateLike] = ()
) -> pd.Timestamp:
    """Latest session on or before ``day``."""
    end = _day(day)
    found = sessions(code, end - pd.Timedelta(days=31), end, extra_holidays)
    if found.empty:
        raise ValueError(f"{code}: no session within 31 days before {end.date()}")
    return found[-1]


def last_session_of_year(
    code: str, year: int, extra_holidays: Iterable[DateLike] = ()
) -> pd.Timestamp:
    """Last trading session of a calendar year."""
    return last_session_on_or_before(code, date(year, 12, 31), extra_holidays)


def last_session_of_quarter(
    code: str, year: int, quarter: int, extra_holidays: Iterable[DateLike] = ()
) -> pd.Timestamp:
    """Last trading session of a calendar quarter (1 to 4)."""
    if quarter not in (1, 2, 3, 4):
        raise ValueError("quarter must be 1, 2, 3 or 4")
    end = pd.Period(year=year, quarter=quarter, freq="Q").end_time.normalize()
    return last_session_on_or_before(code, end, extra_holidays)


def last_completed_session(
    code: str, now: pd.Timestamp, extra_holidays: Iterable[DateLike] = ()
) -> pd.Timestamp:
    """Latest session whose official close is at or before ``now`` (tz-aware).

    Used to drop the still-open session from a download, so a partial bar is
    never stored as if it were a closing price.
    """
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    cal = _calendar(code)
    now_utc = now.tz_convert("UTC")
    today = now_utc.tz_localize(None).normalize() + pd.Timedelta(days=1)
    recent = sessions(code, today - pd.Timedelta(days=31), today, extra_holidays)
    done = [s for s in recent if cal.session_close(s) <= now_utc]
    if not done:
        raise ValueError(f"{code}: no completed session in the 31 days before {now}")
    return done[-1]
