"""Dashboard data access is read-only and the app renders without errors."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from astraquant import dashboard_data as data
from astraquant import ledger
from astraquant.config import REPO_ROOT, load_assets
from tests.unit.test_ledger import _forecast, _run


def test_read_ledger_is_read_only_and_tolerates_a_missing_file(tmp_path):
    assert data.read_ledger(tmp_path / "absent.sqlite").empty
    assert not (tmp_path / "absent.sqlite").exists()  # reading never creates a ledger
    path = tmp_path / "ledger.sqlite"
    conn = ledger.connect(path)
    ledger.append_run(conn, _run(), [_forecast(), _forecast(ticker="BBB")])
    conn.close()
    assert data.read_ledger(path)["ticker"].tolist() == ["AAA", "BBB"]
    readonly = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    with pytest.raises(sqlite3.OperationalError):
        readonly.execute("INSERT INTO runs SELECT * FROM runs")
    readonly.close()


def test_the_frozen_forecast_is_the_first_run_of_its_type(tmp_path):
    conn = ledger.connect(tmp_path / "ledger.sqlite")
    ledger.append_run(conn, _run("r1"), [_forecast("r1", target_type="dry")])
    ledger.append_run(conn, _run("r2"), [_forecast("r2", point_estimate=0.03)])
    ledger.append_run(conn, _run("r3"), [_forecast("r3", point_estimate=0.07)])
    stored = ledger.read_forecasts(conn)
    conn.close()
    frozen = data.first_run_of_type(stored, "q1_2027_price_return")
    assert frozen["run_id"].tolist() == ["r2"]  # the later run r3 does not replace it
    assert frozen["point_estimate"].tolist() == [0.03]
    assert data.first_run_of_type(stored, "unknown").empty
    assert data.run_summary(stored)["run_id"].tolist() == ["r1", "r2", "r3"]
    assert data.run_summary(pd.DataFrame()).empty


def test_freshness_counts_completed_sessions_only(settings):
    settings.processed_dir.mkdir(parents=True)
    manifest = {"data_through": {"US": "2026-11-11", "ID": "2026-11-12", "FX": "2026-11-11"}}
    (settings.processed_dir / "manifest.json").write_text(json.dumps(manifest))
    # Saturday 14 Nov 2026: Thursday and Friday sessions are complete on both exchanges.
    weekend = data.freshness(load_assets(), settings, pd.Timestamp("2026-11-14 12:00", tz="UTC"))
    behind = weekend.set_index("market")["sessions_behind"].to_dict()
    assert behind == {"US": 2, "ID": 1}
    # Sunday changes nothing: no session closed in between.
    sunday = data.freshness(load_assets(), settings, pd.Timestamp("2026-11-15 12:00", tz="UTC"))
    assert sunday["sessions_behind"].tolist() == weekend["sessions_behind"].tolist()
    # Right after the data-through close nothing is behind.
    same_day = data.freshness(load_assets(), settings, pd.Timestamp("2026-11-12 10:00", tz="UTC"))
    assert same_day.set_index("market")["sessions_behind"].to_dict() == {"US": 0, "ID": 0}


def test_status_tables_handle_a_project_with_no_outputs(settings, tmp_path):
    empty = replace(
        settings,
        dataset_dir=tmp_path / "dataset",
        evaluation={**settings.evaluation, "output_dir": str(tmp_path / "evaluation")},
    )
    assert data.freshness(load_assets(), empty, pd.Timestamp.now(tz="UTC")).empty
    assert data.pipeline_status(empty)["last_run_utc"].tolist() == ["never"] * 3
    assert data.quality_summary(empty).empty
    assert data.load_evaluation(empty) is None


def test_the_data_module_never_writes():
    source = (REPO_ROOT / "src/astraquant/dashboard_data.py").read_text(encoding="utf-8")
    for forbidden in ("write_text", "to_parquet", "to_csv", "INSERT", "ledger.connect", ".fit("):
        assert forbidden not in source


def test_the_app_renders_its_default_page_without_an_exception():
    app = AppTest.from_file(str(Path(REPO_ROOT) / "dashboard" / "app.py"), default_timeout=30)
    app.run()
    assert not app.exception
    assert app.title[0].value == "Q1 2027 forecast"


def test_volatility_tables_omit_directional_accuracy(tmp_path, settings):
    from dataclasses import replace

    base = tmp_path / "evaluation"
    for target in ("fwd_vol_20", "fwd_ret_20"):
        folder = base / target
        folder.mkdir(parents=True)
        predictions = pd.DataFrame(
            {
                "symbol": ["A", "B"],
                "market": ["US", "ID"],
                "test_year": [2020, 2020],
                "y": [0.2, 0.3],
                "pred_base": [0.25, 0.25],
                "pred_m": [0.2, 0.31],
            }
        )
        predictions.to_parquet(folder / "predictions.parquet")
        intervals = predictions[["market", "y"]].assign(model="m", lower=0.0, upper=1.0)
        intervals.to_parquet(folder / "intervals.parquet")
        pd.DataFrame({"test_year": [2020]}).to_parquet(folder / "folds.parquet")
    local = replace(settings, evaluation={**settings.evaluation, "output_dir": str(base)})
    selection = {"baseline": "base", "checks": []}
    vol = data.evaluation_tables(local, "fwd_vol_20", selection)
    ret = data.evaluation_tables(local, "fwd_ret_20", selection)
    assert "directional_accuracy" not in vol["overall"].columns
    assert "directional_accuracy" not in vol["by_market"].columns
    assert "directional_accuracy" in ret["overall"].columns
