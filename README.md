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
uv pip install -e ".[dev]"
```

## Use

```bash
python scripts/ingest.py          # download, clean, validate -> data/, reports/data_quality.md
python scripts/build_dataset.py   # targets and features -> data/processed/dataset/
ruff check . && pytest            # checks
```

`data/` is not in Git. Every run records the git commit, data-through date and config digest.

## Where things are

| Path | Content |
|---|---|
| `docs/PROJECT_BLUEPRINT.md` | Specification (v2.0-lean). Read this first. |
| `docs/DECISIONS.md` | Decisions, assumptions and open questions, by milestone. |
| `docs/archive/` | Superseded v1.0 blueprint, kept for reference only. |
| `configs/` | Universe, horizons, feature windows, calendars. Nothing is hardcoded. |
| `src/astraquant/` | Package: calendars, data, targets, features, dataset. |
| `scripts/` | Pipeline entry points. |
| `reports/` | Generated reports. |
| `tests/` | Unit and leakage tests; `tests/fixtures/` holds small real-data excerpts. |

## Status

Milestones 0 to 2 (discovery, data, targets and features) are built. Models, the report
and the frozen forecast are Milestones 3 and 4. See blueprint section 9.
