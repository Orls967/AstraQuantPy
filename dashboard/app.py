"""AstraQuant dashboard: forecasts, evaluation results, data freshness.

Read-only. Run with:  streamlit run dashboard/app.py
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from astraquant import dashboard_data as data
from astraquant.config import load_assets, load_settings

BLUE = "#2a78d6"  # single series colour; identity is carried by axis labels
MUTED = "#8a8985"
REALISED = "#f08c00"  # realised outcome marker; readable on light and dark themes

SETTINGS = load_settings()
ASSETS = load_assets()


def limitations() -> None:
    """Repeat the limitations on every page."""
    with st.expander("Limitations (read before using any number here)", expanded=False):
        for line in data.LIMITATIONS:
            st.markdown(f"- {line}")


def interval_chart(rows: pd.DataFrame) -> alt.LayerChart:
    """One row per ticker: the prediction interval as a bar, the point estimate as a dot."""
    order = rows["ticker"].tolist()
    base = alt.Chart(rows).encode(
        y=alt.Y("ticker:N", sort=order, title=None),
        tooltip=[
            alt.Tooltip("ticker:N", title="Ticker"),
            alt.Tooltip("point_estimate:Q", title="Point estimate", format="+.1%"),
            alt.Tooltip("interval_lower:Q", title="Interval lower", format="+.1%"),
            alt.Tooltip("interval_upper:Q", title="Interval upper", format="+.1%"),
            alt.Tooltip("target_start_date:N", title="Origin"),
            alt.Tooltip("target_end_date:N", title="Target end"),
        ],
    )
    span = base.mark_bar(height=6, cornerRadius=3, color=BLUE, opacity=0.35).encode(
        x=alt.X(
            "interval_lower:Q",
            title="Price return over the quarter",
            axis=alt.Axis(format="+.0%", gridOpacity=0.4),
        ),
        x2="interval_upper:Q",
    )
    point = base.mark_circle(size=90, color=BLUE, opacity=1).encode(x="point_estimate:Q")
    zero = (
        alt.Chart(pd.DataFrame({"x": [0.0]}))
        .mark_rule(color=MUTED, strokeDash=[4, 4])
        .encode(x="x:Q")
    )
    layers = zero + span + point
    if "realised_return" in rows.columns:
        layers += (
            alt.Chart(rows)
            .mark_tick(color=REALISED, thickness=3, size=22, opacity=1)
            .encode(
                y=alt.Y("ticker:N", sort=order, title=None),
                x="realised_return:Q",
                tooltip=[
                    alt.Tooltip("ticker:N", title="Ticker"),
                    alt.Tooltip("realised_return:Q", title="Realised", format="+.1%"),
                    alt.Tooltip("error:Q", title="Realised minus forecast", format="+.1%"),
                ],
            )
        )
    return layers.properties(height=34 * len(rows) + 40)


def forecast_table(rows: pd.DataFrame) -> pd.DataFrame:
    """Forecast rows formatted for reading, with the realised outcome when recorded."""
    out = pd.DataFrame(
        {
            "Ticker": rows["ticker"],
            "Currency": rows["currency"],
            "Origin": rows["target_start_date"],
            "Target end": rows["target_end_date"],
            "Start price": rows["target_start_price"].map("{:,.2f}".format),
            "Point": rows["point_estimate"].map("{:+.1%}".format),
            "Lower": rows["interval_lower"].map("{:+.1%}".format),
            "Upper": rows["interval_upper"].map("{:+.1%}".format),
            "Model": rows["model_name"],
            "Data through": rows["data_through_date"],
        }
    )
    if "realised_return" in rows.columns:
        out.insert(8, "Realised", rows["realised_return"].map("{:+.1%}".format))
        out.insert(9, "Inside interval", rows["inside_interval"].map({1: "yes", 0: "no"}))
    return out


def show_forecast(rows: pd.DataFrame, outcomes: pd.DataFrame | None = None) -> None:
    """Chart and table for the rows of one run, with realised outcomes if recorded."""
    joined = data.join_outcomes(rows, outcomes) if outcomes is not None else pd.DataFrame()
    realised = len(joined) == len(rows) and not joined.empty
    if realised:
        rows = joined
    first = rows.iloc[0]
    level = float(first["interval_level"])
    left, middle, right = st.columns(3)
    left.metric("Model", first["model_name"])
    middle.metric("Prediction interval", f"{level:.0%}")
    right.metric("Created (UTC)", first["created_at_utc"][:16].replace("T", " "))
    st.caption(
        f"Run `{first['run_id']}` · target type `{first['target_type']}` · "
        f"commit `{first['git_commit'][:7]}` · feature set `{first['feature_set_version']}`"
    )
    st.subheader(f"Price return with {level:.0%} prediction intervals")
    st.caption(
        "Dot: point estimate. Bar: prediction interval from past forecast errors. "
        "Dashed line: zero return. Local currency; do not compare price levels across markets."
        + (" Orange tick: realised return." if realised else "")
    )
    if realised:
        summary = data.outcome_summary(rows).iloc[0]
        a, b, c = st.columns(3)
        a.metric(
            "Inside the interval",
            f"{int(summary['inside_interval'])} of {int(summary['n'])}",
            help=f"Nominal level {level:.0%}. One quarter of correlated stocks says little "
            "about calibration.",
        )
        b.metric("RMSE of the forecast", f"{summary['rmse_forecast']:.1%}")
        c.metric("RMSE of a zero-return forecast", f"{summary['rmse_zero']:.1%}")
    for exchange, part in rows.groupby("exchange", sort=False):
        st.markdown(f"**{exchange}** ({part['currency'].iloc[0]})")
        st.altair_chart(interval_chart(part), width="stretch")
    st.dataframe(forecast_table(rows), hide_index=True, width="stretch")


def page_forecasts() -> None:
    """Frozen forecasts with prediction intervals."""
    st.title("Q1 2027 forecast")
    limitations()
    cfg = SETTINGS.forecast
    stored = data.load_forecasts(SETTINGS)
    frozen = data.first_run_of_type(stored, cfg["target_type"]) if not stored.empty else stored
    if frozen.empty:
        pins = SETTINGS.targets[cfg["target_key"]]
        origins = ", ".join(f"{code} {spec['start']}" for code, spec in pins.items())
        st.info(
            "No frozen forecast yet. The official forecast is stored after the last 2026 "
            f"close ({origins}) by `python scripts/forecast.py`."
        )
    else:
        st.success("Frozen forecast from the append-only ledger. These rows cannot change.")
        show_forecast(frozen, data.load_outcomes(SETTINGS))
        with st.expander("All runs in the ledger"):
            st.dataframe(data.run_summary(stored), hide_index=True, width="stretch")

    rehearsal = data.load_forecasts(SETTINGS, rehearsal=True)
    if not rehearsal.empty and st.toggle("Show the latest rehearsal run (not a forecast)"):
        st.warning(
            "REHEARSAL ONLY. Produced by `forecast.py --dry-run` to test the pipeline. "
            "Not a forecast and not in the ledger. Do not use these numbers."
        )
        latest = rehearsal[rehearsal["run_id"] == rehearsal["run_id"].max()]
        show_forecast(latest.reset_index(drop=True), data.load_outcomes(SETTINGS, rehearsal=True))


def r2_chart(overall: pd.DataFrame, baseline: str) -> alt.LayerChart:
    """Pooled out-of-sample R2 per model against the baseline."""
    frame = overall[overall["model"] != baseline]
    low, high = float(frame["r2_oos"].min()), float(frame["r2_oos"].max())
    pad = 0.2 * max(abs(low), abs(high), 0.01)  # room on both sides so zero is always visible
    base = alt.Chart(frame).encode(
        y=alt.Y("model:N", sort=frame["model"].tolist(), title=None),
        tooltip=[
            alt.Tooltip("model:N", title="Model"),
            alt.Tooltip("r2_oos:Q", title="R2 out of sample", format="+.4f"),
            alt.Tooltip("n:Q", title="Test rows"),
        ],
    )
    bars = base.mark_bar(height=18, cornerRadius=4, color=BLUE).encode(
        x=alt.X(
            "r2_oos:Q",
            title=f"Pooled R2 out of sample against {baseline}",
            scale=alt.Scale(domain=[min(low, -pad), max(high, pad)], nice=True),
        )
    )
    labels = base.mark_text(dx=6, align="left").encode(
        x="r2_oos:Q", text=alt.Text("r2_oos:Q", format="+.3f")
    )
    zero = alt.Chart(pd.DataFrame({"x": [0.0]})).mark_rule(color=MUTED).encode(x="x:Q")
    return (bars + labels + zero).properties(height=44 * len(frame) + 40)


def page_evaluation() -> None:
    """Walk-forward results and the selection rule."""
    st.title("Walk-forward evaluation")
    limitations()
    evaluation = data.load_evaluation(SETTINGS)
    if evaluation is None:
        st.info("No evaluation yet. Run `python scripts/evaluate.py`.")
        return
    primary = evaluation["primary_target"]
    targets = list(evaluation["selection"])
    target = st.selectbox(
        "Target",
        targets,
        format_func=lambda t: f"{t} (primary, decides the published model)" if t == primary else t,
    )
    selection = evaluation["selection"][target]
    tables = data.evaluation_tables(SETTINGS, target, selection)
    baseline, chosen = selection["baseline"], selection["selected"]

    if chosen == baseline:
        st.warning(f"No model beats the baseline. Selected: `{baseline}` (the baseline).")
    else:
        st.success(f"Selected: `{chosen}`, replacing the baseline `{baseline}`.")
    if target != primary:
        st.caption("Secondary target: shown for information, never used to pick the model.")
    st.caption(
        "Rule, fixed before any model was run: a model replaces the baseline only if pooled "
        "R2 out of sample is above zero and it beats the baseline in more than half of the "
        "test years."
    )
    st.dataframe(tables["checks"], hide_index=True, width="stretch")

    st.subheader("Pooled out-of-sample R2")
    st.caption("Above zero is better than the baseline; below zero is worse.")
    st.altair_chart(r2_chart(tables["overall"], baseline), width="stretch")
    st.dataframe(tables["overall"], hide_index=True, width="stretch")

    st.subheader("By test year")
    st.caption("Sum of squared errors per year. A model beats the baseline when its sum is lower.")
    st.dataframe(tables["yearly"], hide_index=True, width="stretch")

    st.subheader("By market")
    st.dataframe(tables["by_market"], hide_index=True, width="stretch")

    level = float(evaluation["evaluation_spec"]["interval"]["level"])
    st.subheader(f"{level:.0%} prediction interval coverage, out of sample")
    st.caption(
        f"Coverage below {level:.0%} means the interval was too narrow in the past. "
        "Each year's interval was built from earlier years only."
    )
    coverage = tables["coverage"].copy()
    coverage["coverage"] = coverage["coverage"].map("{:.1%}".format)
    st.dataframe(coverage, hide_index=True, width="stretch")

    with st.expander("Folds and chosen hyperparameters"):
        st.dataframe(tables["folds"], hide_index=True, width="stretch")
    st.caption(
        f"Evaluation run {evaluation['run_at_utc'][:19]} UTC · commit "
        f"`{evaluation['git_commit'][:7]}` · config `{evaluation['config_digest']}`"
    )


def page_freshness() -> None:
    """How current the data and each pipeline stage are."""
    st.title("Data freshness")
    limitations()
    now = pd.Timestamp.now(tz="UTC")
    fresh = data.freshness(ASSETS, SETTINGS, now)
    if fresh.empty:
        st.info("No data yet. Run `python scripts/ingest.py`.")
        return
    columns = st.columns(len(fresh))
    for column, row in zip(columns, fresh.itertuples(), strict=True):
        behind = int(row.sessions_behind)
        column.metric(
            f"{row.market} data through",
            row.data_through.date().isoformat(),
            "up to date" if behind == 0 else f"{behind} sessions behind",
            delta_color="off" if behind == 0 else "inverse",
            delta_arrow="off",
        )
    st.caption(
        "Sessions behind = completed exchange sessions after the data-through date, on each "
        "exchange's own calendar. Weekends and holidays do not count."
    )
    shown = fresh.copy()
    for name in ("data_through", "last_completed_session"):
        shown[name] = shown[name].dt.date.astype(str)
    st.dataframe(shown, hide_index=True, width="stretch")

    st.subheader("Pipeline stages")
    status = data.pipeline_status(SETTINGS)
    st.dataframe(status, hide_index=True, width="stretch")
    digests = set(status.loc[status["stage"].isin(["evaluation"]), "config_digest"])
    st.caption(
        "The forecast script refuses to run unless the evaluation was made on the current "
        f"dataset build and config (evaluation config: `{', '.join(sorted(digests))}`)."
    )

    st.subheader("Data-quality issues from the last ingest")
    st.caption("Issues are flagged, never repaired. Details: `reports/data_quality.md`.")
    st.dataframe(data.quality_summary(SETTINGS), hide_index=True, width="stretch")


st.set_page_config(page_title="AstraQuant", layout="wide")
navigation = st.navigation(
    [
        st.Page(page_forecasts, title="Forecasts", url_path="forecasts", default=True),
        st.Page(page_evaluation, title="Evaluation", url_path="evaluation"),
        st.Page(page_freshness, title="Data freshness", url_path="freshness"),
    ]
)
navigation.run()
