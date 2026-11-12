# AstraQuant Lean Blueprint

**Version:** 2.0-lean (2026-11-12), replaces the v1.0 "full platform" blueprint
**Type:** Local, single-user quantitative research project
**Language:** Python

## 1. What this project is

AstraQuant answers one question honestly:

> Can any simple model forecast the Q1 2027 return of 11 selected stocks better than a naive baseline, and how wide is the uncertainty?

The deliverable is a **frozen, timestamped Q1 2027 forecast with prediction intervals**, backed by a walk-forward evaluation on past quarters. A dashboard is optional and comes last.

It is research and decision support only. No live trading, no investment advice, no guaranteed outcomes.

**"No model beats the baseline" is an acceptable and likely result.** In that case the published forecast is the baseline with empirical intervals, and the report says so.

## 2. Universe

| Market | Tickers (yfinance symbol) | Currency | Calendar |
|---|---|---|---|
| US | NVDA, AAPL, MSFT, GOOGL, AMZN, META | USD | NYSE/Nasdaq |
| Indonesia | BBCA.JK, BBRI.JK, BMRI.JK, BBNI.JK, BBTN.JK | IDR | IDX |

The list lives in `configs/assets.yaml`. Adding a ticker must not require code changes.

**Known limitation (must appear in every report):** these 11 names were chosen with hindsight because they are today's winners. Results carry selection bias and do not generalise to "stocks" in general. An optional wider *training* universe (for example S&P 100 and LQ45 members) may be added through config later; forecasts are still published only for the 11 names.

## 3. Targets

All returns are in local currency. No cross-currency comparison of price levels.

### 3.1 Primary: official Q1 2027 calendar-quarter price return

`q1_return = close[last trading day of Q1 2027] / close[last trading day of 2026] - 1`

- Uses **split-adjusted, not dividend-adjusted** close (price return). With yfinance this means `auto_adjust=False` and the `Close` column, not `Adj Close`. Phase 1 must verify this against known corporate actions.
- The start and end dates come from each exchange's real trading calendar. They may differ between the US and Indonesia. **Phase 0 must confirm both dates from official exchange calendars**; do not assume 31 December and 31 March.
- Historical analogue for evaluation: for every past quarter, origin = last close of the previous quarter, target = that quarter's price return.

### 3.2 Secondary

- Forward price return over 5, 20 and 60 trading sessions. (The 1- and 10-day horizons from v1.0 are dropped to limit multiple testing; they can be re-enabled in config.)
- **Forward realised volatility** over 20 and 60 sessions (standard deviation of daily log returns, annualised). Volatility is far more forecastable than return, so this is where a model is most likely to add real value.

### 3.3 Forecast record

Every stored forecast carries: ticker, exchange, currency, target type, forecast origin date, data-through date, target start date and price, target end date, point estimate, 80% prediction interval, model name and version, feature-set version, git commit, creation timestamp.

Forecasts are **append-only**. A new forecast never overwrites an old one. A forecast made after the origin (during Q1) is stored as a different target type with its remaining horizon.

## 4. Why the scope is small

- A quarterly horizon gives about 4 independent observations per stock per year. Fifteen years is about 60 points per stock, and the 11 stocks are highly correlated.
- Daily OHLCV for 11 stocks over 15 years is about 40,000 rows. This does not need a database server.
- Consequence: no deep learning, no PostgreSQL, no API layer, no experiment-tracking server in this version. See section 10.

## 5. Stack

| Need | Tool |
|---|---|
| Data handling | pandas, numpy, pyarrow |
| Price data (prototype) | yfinance |
| Trading calendars | exchange_calendars or pandas_market_calendars, verified against official calendars |
| Models | scikit-learn (Ridge), LightGBM |
| Storage | Parquet for data and features; SQLite for the forecast ledger and run log |
| Quality | pytest, ruff |
| Dashboard (later) | Streamlit, importing the package directly |

Pin versions in `pyproject.toml`. Add a dependency only when a milestone needs it.

## 6. Data rules

- yfinance is an unofficial source, suitable for prototyping only. State this in reports.
- Raw downloads are immutable, stored with retrieval timestamp and source. Cleaned data is a derived artifact.
- Never forward-fill prices across non-trading days. Missing sessions are flagged, not invented.
- Validate: duplicates, gaps against the trading calendar, zero or negative prices, zero-volume days, jumps above a threshold that do not match a known split.
- Manually spot-check Indonesian corporate actions (stock splits and rights issues) because free data is least reliable there.
- IDX holidays, including *cuti bersama*, are set by government decree and are often wrong in calendar libraries. Check against the official IDX calendar.

## 7. Features

All features use only information available at or before the forecast origin close.

- Lagged returns: 5, 20, 60, 120, 250 sessions
- Realised volatility: 20, 60, 120 sessions
- Distance from 50- and 200-session moving averages
- RSI(14), drawdown from 250-session high
- Relative volume (20 vs 120 sessions)
- Market context: index return and volatility (S&P 500 for US, IHSG for Indonesia), USD/IDR change for Indonesian names

No fundamentals, macro or news in this version: point-in-time history is not available for free.

Models are trained **pooled across tickers** on scale-free features, with a market indicator, to use the small sample as well as possible.

## 8. Evaluation protocol (fixed before any results are seen)

**Models, in order:** zero return; historical mean; Ridge regression; LightGBM. Nothing else in this version.

**Walk-forward:** expanding training window, yearly test blocks, no shuffling. An embargo of `h` sessions separates training from test, and any training label whose window overlaps the test block is removed. Scalers and any other fitted transformation are fit on the training window only. Hyperparameters are tuned only inside the training window.

**Primary metric:** out-of-sample R² against the historical-mean baseline, pooled across tickers, on the quarterly target evaluated at non-overlapping quarter-end origins:

`R2_oos = 1 - SSE_model / SSE_baseline`

**Selection rule:** a model replaces the baseline for the published forecast only if pooled `R2_oos > 0` **and** it beats the baseline in more than half of the test years. Otherwise the baseline is published.

**Reported but not used for selection:** MAE, RMSE, directional accuracy, per-ticker and per-market breakdowns, results for secondary horizons, interval coverage and width.

**Prediction intervals:** empirical quantiles of walk-forward out-of-sample residuals (80%). Coverage is checked on held-out years. Call them prediction intervals, never "confidence".

**Same protocol for volatility targets**, with trailing realised volatility as the baseline.

## 9. Milestones

Stop for review after each one. Target: forecast frozen right after the last 2026 close.

| # | Milestone | Exit criteria |
|---|---|---|
| 0 | Discovery | Environment checked; Q1 start and end dates confirmed for both exchanges; open questions listed in `docs/DECISIONS.md`. No implementation. |
| 1 | Data | One command re-ingests all tickers to Parquet; data-quality report produced; price-return semantics verified on at least one known split per market; tests pass. |
| 2 | Targets and features | Target and feature builders with unit tests; leakage tests pass (features unchanged when future rows are altered; target dates match the calendar). |
| 3 | Models and walk-forward | All four models run through the identical protocol; results table saved; selection rule applied mechanically. |
| 4 | Report and frozen forecast | `reports/q1_2027.md` with method, results, limitations; Q1 2027 forecasts written to the ledger with full metadata. |
| 5 | Dashboard (optional) | Streamlit pages: forecasts with intervals, evaluation results, data freshness. |
| 6 | Outcome tracking (April 2027) | Realised Q1 returns recorded next to the frozen forecasts; short post-mortem. |

## 10. Parked until results justify them

PostgreSQL and Alembic, FastAPI, MLflow, Docker, LSTM/GRU/Transformer/TFT, ARIMA, ensembles, strategy backtesting with costs, portfolio analytics, fundamentals, macro and news data, licensed IDX data.

Revisit only after Milestone 4, and only for a stated reason (for example: "LightGBM beat the baseline on volatility, so a backtest of a volatility-targeting rule is worth building").

## 11. Repository structure

```text
astraquant/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── .gitignore
├── configs/
│   ├── assets.yaml
│   └── settings.yaml
├── data/                  # gitignored
│   ├── raw/
│   └── processed/
├── src/astraquant/
│   ├── config.py
│   ├── calendars.py
│   ├── data/              # providers, ingestion, validation
│   ├── targets.py
│   ├── features.py
│   ├── models/            # baselines, ridge, lightgbm
│   ├── evaluation/        # walk-forward, metrics, intervals
│   └── ledger.py          # SQLite forecast ledger
├── scripts/
│   ├── ingest.py
│   ├── build_dataset.py
│   ├── evaluate.py
│   └── forecast.py
├── tests/
│   ├── unit/
│   └── leakage/
├── reports/
└── docs/
    ├── PROJECT_BLUEPRINT.md
    └── DECISIONS.md
```

## 12. What the user does manually

- Install Python, Git and Claude Code; create the folder; `git init` and make a first commit.
- Accept that yfinance data is for personal prototyping, and review its terms.
- Confirm the decisions in section 3 (price return; quarter boundaries) at the end of Milestone 0.
- Review each milestone report before approving the next.

No API keys or paid services are needed for this version.

## 13. Definition of done

1. All 11 tickers ingest reproducibly with a data-quality report.
2. Leakage tests pass.
3. Four models are compared under one fixed walk-forward protocol.
4. The selection rule was applied as written, not adjusted after seeing results.
5. Q1 2027 forecasts with 80% intervals are frozen in the ledger before Q1 begins.
6. The report states the limitations: selection bias, small sample, unofficial data.
