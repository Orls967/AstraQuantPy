"""Coverage report for the research datasets.

Reports availability only. It shows no target statistics, so nothing here can
steer modelling choices before the evaluation protocol runs.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from astraquant.config import Settings
from astraquant.features import feature_columns


def _table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_None._\n"
    header = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    rows = frame.itertuples(index=False)
    body = ["| " + " | ".join(_cell(v) for v in row) + " |" for row in rows]
    return "\n".join([header, rule, *body]) + "\n"


def _cell(value: object) -> str:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, float):
        return f"{value:.1%}"
    return str(value)


def _missing_share(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    share = frame.groupby("market")[columns].agg(lambda s: s.isna().mean()).T
    return share.reset_index().rename(columns={"index": "column"})


def render_dataset_report(
    daily: pd.DataFrame, quarterly: pd.DataFrame, manifest: dict[str, Any], settings: Settings
) -> str:
    """Markdown coverage report for one dataset build."""
    names = feature_columns(settings.features)
    spec = settings.dataset
    daily_targets = [f"fwd_ret_{h}" for h in spec["return_horizons"]] + [
        f"fwd_vol_{h}" for h in spec["volatility_horizons"]
    ]
    # Features that exist for every market; FX features are NaN by design for US names.
    common = [c for c in names if not c.startswith("fx_")]

    sessions = (
        daily.groupby(["symbol", "market"], sort=False)
        .agg(
            sessions=("date", "size"),
            first=("date", "min"),
            last=("date", "max"),
            missing_bars=("has_bar", lambda s: int((~s).sum())),
        )
        .reset_index()
    )

    q = quarterly.copy()
    q["realised"] = q["q_return"].notna()
    q["features_complete"] = q[common].notna().all(axis=1) & (
        (q["market"] != "ID") | q[[c for c in names if c.startswith("fx_")]].notna().all(axis=1)
    )
    q["usable"] = q["realised"] & q["features_complete"]
    q["ended"] = (
        q["target_end_date"]
        <= daily.groupby("symbol")["date"].max().reindex(q["symbol"]).to_numpy()
    )
    per_symbol = (
        q.groupby(["symbol", "market"], sort=False)
        .agg(
            quarters=("quarter", "size"),
            first=("quarter", "min"),
            last=("quarter", "max"),
            realised=("realised", "sum"),
            features_complete=("features_complete", "sum"),
            usable=("usable", "sum"),
        )
        .reset_index()
    )
    lost = q[q["ended"] & ~q["realised"]][
        ["symbol", "quarter", "target_start_date", "target_end_date"]
    ]
    realised = q[q["realised"]]
    feature_gaps = (
        realised.groupby("market")[names]
        .agg(lambda col: int(col.isna().sum()))
        .T.reset_index()
        .rename(columns={"index": "feature"})
    )
    realised_rows = realised.groupby("market").size().to_dict()
    by_year = (
        q.assign(year=q["quarter"].str[:4])
        .groupby(["year", "market"])["usable"]
        .sum()
        .unstack("market")
        .fillna(0)
        .astype(int)
        .reset_index()
    )

    parts = [
        "# Dataset coverage report",
        "",
        f"- Built {manifest['built_at_utc']} from ingest run `{manifest['ingest_run_id']}`.",
        f"- Source: {manifest['source']}. **Unofficial data, prototyping only.**",
        f"- Git commit: `{manifest['git_commit']}`"
        + (" (tracked files had uncommitted changes)" if manifest["git_dirty"] else ""),
        f"- Config digest: `{manifest['config_digest']}`; feature set"
        f" `{manifest['feature_set_version']}`.",
        "- Data through: " + ", ".join(f"{k} {v}" for k, v in manifest["data_through"].items()),
        f"- Rows: daily {len(daily):,}; quarterly {len(quarterly):,}.",
        "- This report shows availability only. No target statistics are shown.",
        "- Rule: windows and horizons are counted in exchange sessions. A feature or target",
        "  that touches a missing bar is NaN. Nothing is filled or shifted.",
        "",
        "## Session grid per symbol",
        "",
        _table(sessions),
        "## Share of daily rows that are NaN, by market",
        "",
        "Features (FX features are NaN by design for US names):",
        "",
        _table(_missing_share(daily, names)),
        "Targets (the last `h` sessions of each series are NaN because the future is unknown):",
        "",
        _table(_missing_share(daily, daily_targets)),
        "## Quarterly dataset per symbol",
        "",
        "`realised` = quarter return available; `features_complete` = every feature at the",
        "origin is available; `usable` = both.",
        "",
        _table(per_symbol),
        "## Usable quarterly rows per year",
        "",
        _table(by_year),
        "## Ended quarters with no label (a boundary session has no bar)",
        "",
        _table(lost),
        "## Realised quarterly rows missing each feature at the origin",
        "",
        "Realised rows per market: "
        + ", ".join(f"{k} {v}" for k, v in realised_rows.items())
        + ". Row-level detail is in `quarterly.parquet`.",
        "",
        _table(feature_gaps),
        "## Limitations",
        "",
        "- The 11 names were chosen with hindsight; results carry selection bias.",
        "- Quarterly rows are few and the names are highly correlated.",
        "- Yahoo applies an unrecorded adjustment at rights-issue ex-dates of four Indonesian",
        "  banks (DECISIONS.md 6.3, Q-17). The affected labels and features are still in this",
        "  dataset, unchanged.",
        "- Features for the first 250 sessions of each series are NaN by construction.",
        "",
    ]
    return "\n".join(parts)
