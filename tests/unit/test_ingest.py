"""Ingest orchestration with an in-memory provider (no network)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from astraquant import calendars
from astraquant.data.ingest import PROCESSED_COLUMNS, clean_bars, run_ingest
from astraquant.data.report import render_report
from tests.conftest import FakeProvider, make_raw

SESSIONS = calendars.sessions("XNYS", "2024-03-01", "2024-03-28")
# Wed 2024-03-27, 11:00 New York: that day's session is still open.
NOW = pd.Timestamp("2024-03-27 11:00", tz="America/New_York")


def test_clean_bars_schema_and_exchange_local_dates(us_asset):
    bars, counts = clean_bars(make_raw(SESSIONS), us_asset, SESSIONS[-1], SESSIONS)
    assert list(bars.columns) == PROCESSED_COLUMNS
    assert bars["date"].dt.tz is None
    assert list(bars["date"]) == list(SESSIONS)
    assert counts == {"dropped_incomplete": 0, "dropped_empty": 0, "dropped_closed_day": 0}
    # close stays the provider's Close; Adj Close is kept apart and never substituted.
    assert (bars["close"] != bars["adj_close"]).all()


def test_jakarta_timestamps_keep_their_local_date():
    asset_dates = calendars.sessions("XIDX", "2024-03-01", "2024-03-08")
    raw = make_raw(asset_dates, tz="Asia/Jakarta")
    from astraquant.config import Asset

    asset = Asset("X.JK", "X", "ID", "target", "XIDX", "IDR", "Asia/Jakarta")
    bars, _ = clean_bars(raw, asset, asset_dates[-1], asset_dates)
    assert list(bars["date"]) == list(asset_dates)


def test_run_ingest_drops_open_session_and_writes_outputs(us_asset, settings):
    provider = FakeProvider({"TEST": make_raw(SESSIONS)})
    result = run_ingest([us_asset], settings, provider, NOW, {"git_commit": "abc"})

    row = result.summary.iloc[0]
    assert row["data_through"] == pd.Timestamp("2024-03-26")
    assert row["last_date"] == pd.Timestamp("2024-03-26")
    assert row["dropped_incomplete"] == 2  # 27 March (open) and 28 March (future)
    assert row["errors"] == 0 and row["warnings"] == 0

    processed = pd.read_parquet(settings.processed_dir / "prices" / "TEST.parquet")
    assert processed["date"].max() == pd.Timestamp("2024-03-26")
    raw = pd.read_parquet(result.raw_dir / "TEST.parquet")
    assert len(raw) == len(SESSIONS)  # raw keeps everything the provider returned

    manifest = json.loads((result.raw_dir / "manifest.json").read_text())
    assert manifest["source"] == "fake" and manifest["git_commit"] == "abc"
    assert manifest["data_through"] == {"US": "2024-03-26"}
    assert "Unofficial data" in render_report(result, [us_asset])


def test_raw_runs_are_immutable(us_asset, settings):
    provider = FakeProvider({"TEST": make_raw(SESSIONS)})
    first = run_ingest([us_asset], settings, provider, NOW)
    with pytest.raises(FileExistsError):
        run_ingest([us_asset], settings, provider, NOW)
    later = run_ingest([us_asset], settings, provider, NOW + pd.Timedelta(seconds=1))
    assert later.raw_dir != first.raw_dir and first.raw_dir.exists()


def test_gap_in_provider_data_stays_a_gap(us_asset, settings):
    raw = make_raw(SESSIONS)
    raw = raw.drop(index=raw.index[4])
    result = run_ingest([us_asset], settings, FakeProvider({"TEST": raw}), NOW)
    processed = pd.read_parquet(settings.processed_dir / "prices" / "TEST.parquet")
    assert SESSIONS[4] not in set(processed["date"])
    assert list(result.issues["check"]) == ["missing_session"]
    assert "Symbol-specific missing sessions: 0" in render_report(result, [us_asset])


def test_now_must_be_timezone_aware(us_asset, settings):
    with pytest.raises(ValueError):
        run_ingest([us_asset], settings, FakeProvider({}), pd.Timestamp("2024-03-27"))
