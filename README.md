# AstraQuant

Local research project. One question: can a simple model forecast the Q1 2027 price
return of 11 stocks (6 US, 5 Indonesian banks) better than a naive baseline, and how wide
is the uncertainty?

The deliverable is a frozen, timestamped Q1 2027 forecast with 80% prediction intervals,
backed by a walk-forward evaluation on past quarters. "No model beats the baseline" is an
acceptable result.

Research and decision support only. Not investment advice, no trading.

## Limitations to keep in mind

- The 11 names were chosen with hindsight; results carry selection bias.
- A quarterly horizon gives about four independent observations per stock per year.
- Prices come from Yahoo Finance through yfinance: unofficial, for prototyping only.

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e ".[dev,dashboard]"
```

## Use

```bash
python scripts/ingest.py          # download, clean, validate -> data/, reports/data_quality.md
python scripts/build_dataset.py   # targets and features -> data/processed/dataset/
python scripts/evaluate.py        # walk-forward evaluation -> reports/evaluation/summary.md
python scripts/forecast.py        # frozen forecast -> ledger, reports/q1_2027.md (after the last 2026 close)
ruff check . && pytest            # checks
```

Optional read-only dashboard (forecasts with prediction intervals, evaluation results,
data freshness):

```bash
streamlit run dashboard/app.py
```

`data/` is not in Git. Every run records the git commit, data-through date and config digest.

## Where things are

| Path | Content |
|---|---|
| `docs/PROJECT_BLUEPRINT.md` | Specification (v2.0-lean). Read this first. |
| `docs/DECISIONS.md` | Decisions, assumptions and open questions, by milestone. |
| `docs/archive/` | Superseded v1.0 blueprint, kept for reference only. |
| `configs/` | Universe, horizons, feature windows, calendars. Nothing is hardcoded. |
| `src/astraquant/` | Package: calendars, data, targets, features, dataset, models, evaluation. |
| `scripts/` | Pipeline entry points. |
| `dashboard/` | Streamlit app. Reads outputs only; never writes. |
| `reports/` | Generated reports. |
| `tests/` | Unit and leakage tests; `tests/fixtures/` holds small real-data excerpts. |

## Status

Milestones 0 to 3 and the optional dashboard (5) are built, and the Milestone 4 tooling (ledger, forecast script, report)
is built and rehearsed. The official Q1 2027 forecast is frozen after the 2026-12-31 close:
run the four scripts above in order. See blueprint section 9 and `docs/DECISIONS.md` section 9.
