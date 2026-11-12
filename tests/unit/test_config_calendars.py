"""Config loading and trading-calendar behaviour."""

from __future__ import annotations

import pandas as pd
import pytest

from astraquant import calendars
from astraquant.config import load_assets, load_settings


def test_universe_matches_blueprint():
    assets = load_assets()
    targets = [a for a in assets if a.role == "target"]
    assert len(targets) == 11
    assert sum(a.market == "US" for a in targets) == 6
    assert sum(a.market == "ID" for a in targets) == 5
    assert all(a.currency == "IDR" and a.calendar == "XIDX" for a in targets if a.market == "ID")
    assert all(a.currency == "USD" and a.calendar == "XNYS" for a in targets if a.market == "US")


def test_file_stems_are_unique_and_safe():
    stems = [a.file_stem for a in load_assets()]
    assert len(stems) == len(set(stems))
    assert all(stem.replace(".", "").replace("_", "").replace("-", "").isalnum() for stem in stems)


@pytest.mark.parametrize("code", ["XNYS", "XIDX"])
def test_q1_2027_target_dates_match_confirmed_calendar(code):
    """The four dates confirmed in Milestone 0 are what the calendar module returns."""
    settings = load_settings()
    pinned = settings.targets["q1_2027"][code]
    holidays = settings.holidays_for(code)
    start = calendars.last_session_of_year(code, 2026, holidays)
    end = calendars.last_session_of_quarter(code, 2027, 1, holidays)
    assert start == pd.Timestamp(pinned["start"])
    assert end == pd.Timestamp(pinned["end"])
    in_quarter = calendars.sessions(code, "2027-01-01", "2027-03-31", holidays)
    assert len(in_quarter) == pinned["sessions"]


def test_idx_2026_has_the_officially_announced_239_sessions():
    settings = load_settings()
    found = calendars.sessions("XIDX", "2026-01-01", "2026-12-31", settings.holidays_for("XIDX"))
    assert len(found) == 239


def test_library_alone_is_wrong_for_idx_so_overrides_matter():
    """Guards against silently dropping the override list."""
    assert len(calendars.sessions("XIDX", "2027-01-01", "2027-03-31")) != 53


def test_extra_holidays_are_removed_and_weekends_never_appear():
    plain = calendars.sessions("XNYS", "2024-03-01", "2024-03-31")
    cut = calendars.sessions("XNYS", "2024-03-01", "2024-03-31", ["2024-03-05"])
    assert pd.Timestamp("2024-03-05") in plain and pd.Timestamp("2024-03-05") not in cut
    assert len(cut) == len(plain) - 1
    assert (cut.day_of_week < 5).all()


def test_last_completed_session_excludes_open_session():
    # Tue 2024-03-05, 11:00 New York: the session is still open.
    during = pd.Timestamp("2024-03-05 11:00", tz="America/New_York")
    after = pd.Timestamp("2024-03-05 16:30", tz="America/New_York")
    assert calendars.last_completed_session("XNYS", during) == pd.Timestamp("2024-03-04")
    assert calendars.last_completed_session("XNYS", after) == pd.Timestamp("2024-03-05")


def test_last_completed_session_requires_timezone():
    with pytest.raises(ValueError):
        calendars.last_completed_session("XNYS", pd.Timestamp("2024-03-05 11:00"))
