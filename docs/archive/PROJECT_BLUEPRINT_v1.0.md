# AstraQuant

## Project Design, Technical Blueprint, Manual Preparation Checklist, and Claude Code Master Prompt

**Version:** 1.0\
**Project type:** Quantitative Machine Learning / Financial Time-Series
Forecasting\
**Language:** Python\
**Primary objective:** Forecast equity returns for Q1 2027\
**Secondary objective:** Multi-horizon return forecasting\
**Status:** Proposed design; implementation decisions should be
validated during Phase 0.

------------------------------------------------------------------------

# 1. Executive Summary

AstraQuant is a research-oriented quantitative stock forecasting and
analytics platform for selected global large-cap equities and Indonesian
banking stocks. It combines statistical time-series methods, classical
machine learning, deep learning, quantitative risk analysis,
backtesting, and an interactive dashboard.

The platform is intended for research and decision support. It is
**not** an automated trading system and must not present forecasts as
guaranteed outcomes or personalized investment advice.

## Initial universe

### Global equities

-   NVDA --- NVIDIA
-   AAPL --- Apple
-   MSFT --- Microsoft
-   GOOGL --- Alphabet
-   AMZN --- Amazon
-   META --- Meta Platforms

### Indonesian equities

-   BBCA --- Bank Central Asia
-   BBRI --- Bank Rakyat Indonesia
-   BMRI --- Bank Mandiri
-   BBNI --- Bank Negara Indonesia
-   BBTN --- Bank Tabungan Negara

The universe must be configurable through a settings file or database
table. Adding/removing a ticker must not require changes to core model
code.

# 2. Forecasting Objectives and Target Definitions

## 2.1 Primary objective: Q1 2027

The primary deliverable is a forecast for the end-of-Q1 2027
price/return, accompanied by uncertainty estimates and scenario
analysis.

A critical definition is required because the project may generate
forecasts before Q1 begins:

-   **Pre-Q1 forecast (generated before 2027-01-01):** forecast the
    closing price on the final trading day of Q1 2027 relative to the
    latest valid closing price at the forecast origin. This is a forward
    return from the forecast origin to the Q1 endpoint, not the official
    Q1 calendar-quarter return.
-   **Official Q1 calendar-quarter return:** calculate from the last
    valid close of 2026 to the last valid close of Q1 2027. This can
    only be measured once both prices are available. The model may
    forecast it before Q1, but the realized return must use this fixed
    definition.
-   **Forecasts generated during Q1:** clearly label the forecast origin
    and remaining horizon. Do not compare these directly with a
    full-quarter return without adjusting the target definition.

Store the forecast origin, target start price/date, target end date,
trading calendar, and target definition with every prediction. Never
label a rolling return as a calendar-quarter return.

## 2.2 Secondary multi-horizon objectives

Forecast forward returns for: - 1 trading day - 5 trading days - 10
trading days - 20 trading days - 60 trading days

The horizon is measured in the relevant exchange's trading sessions, not
calendar days. Use exchange calendars and handle holidays independently
for US and Indonesia.

## 2.3 Target variable

The primary target should be forward percentage return, not raw price
alone:

`forward_return_h = (adjusted_close[t+h] / adjusted_close[t]) - 1`

Use adjusted prices where appropriate for total-return-consistent
historical analysis. Document provider adjustment behavior, dividends,
splits, and corporate actions. For the official Q1 price-return target,
decide explicitly whether the objective is price return or total return;
do not mix definitions.

A model may additionally produce an implied future price:

`implied_price = reference_price * (1 + predicted_return)`

Keep price prediction as a derived display, not a substitute for
return-based evaluation.

## 2.4 Forecast output

For each ticker and horizon, store: - Point estimate of expected
return - Prediction interval (for example, 80% and/or 95%) -
Bull/base/bear scenario, if statistically calibrated - Implied price
range - Forecast origin timestamp - Data-through date - Model name,
version, and feature-set version - Training window and evaluation
metadata - Important caveats / data-quality flags

Do not call a prediction interval a confidence interval unless the
statistical interpretation is justified. Do not use a generic
"confidence score" unless it is calibrated and defined.

# 3. Technology Architecture

## 3.1 Selected direction

**Framework:** Hybrid Quant + Deep Learning\
**Scope:** Full Quantitative Platform\
**Language:** Python\
**Dashboard:** Streamlit\
**API:** FastAPI\
**Database:** PostgreSQL\
**Analytical storage:** Parquet files\
**Initial data approach:** Free data for prototyping, with a provider
adapter design that can later support licensed sources.

## 3.2 Proposed technology stack

  ------------------------------------------------------------------------
  Layer                   Suggested tools          Purpose
  ----------------------- ------------------------ -----------------------
  Core language           Python                   Application and
                                                   research code

  Data processing         Pandas, NumPy            Tabular and numerical
                                                   processing

  Optional                Polars                   Larger data
  high-performance                                 transformations, only
  processing                                       if needed

  Market data prototype   yfinance or another      Historical price data;
                          approved provider        validate terms and
                                                   reliability

  Indonesia data          Licensed/official        IDX market data and
                          provider where possible  corporate actions

  Macro data              FRED API                 Selected US
                                                   macroeconomic series

  Technical indicators    pandas-ta or TA-Lib      Indicator calculations;
                                                   verify package
                                                   availability and
                                                   definitions

  Statistical models      statsmodels              ARIMA and statistical
                                                   baselines

  Classical ML            scikit-learn             Pipelines,
                                                   preprocessing,
                                                   baselines, metrics

  Gradient boosting       XGBoost, LightGBM        Tabular financial
                                                   features

  Deep learning           PyTorch                  LSTM/GRU and selected
                                                   neural models

  Time-series models      NeuralForecast,          Advanced forecasting
                          optionally               experiments

  Backtesting             VectorBT or a            Strategy simulation
                          transparent custom       
                          event-driven             
                          implementation           

  Risk analytics          QuantStats plus          Performance reporting
                          independently checked    
                          calculations             

  API                     FastAPI, Pydantic        Prediction and data
                                                   endpoints

  UI                      Streamlit, Plotly        Research dashboard

  Database                PostgreSQL, SQLAlchemy,  Metadata, forecasts,
                          Alembic                  runs, configurations

  Experiment tracking     MLflow (recommended)     Model runs, metrics,
                                                   artifacts, versions

  Testing                 pytest                   Unit and integration
                                                   tests

  Code quality            Ruff, mypy (selectively) Linting and type checks

  Reproducibility         requirements/pyproject   Repeatable runs
                          lock, seeds, config      
                          files                    

  Deployment              Docker Compose (optional Consistent local
                          for local services)      environment
  ------------------------------------------------------------------------

Do not install every package at the beginning. Confirm compatibility and
choose a minimal set for each milestone. Avoid duplicate libraries that
solve the same problem without a measured need.

## 3.3 High-level architecture

``` text
Market Data Providers
        |
        v
Data Ingestion Adapters
        |
        v
Validation, Cleaning, Corporate Actions, Calendars
        |
        v
PostgreSQL Metadata + Parquet Historical Data
        |
        v
Feature Engineering (point-in-time safe)
        |
        v
Research Dataset / Time-Series Splits
        |
        +--> Statistical Baselines
        +--> Classical ML (RF, XGBoost, LightGBM)
        +--> Deep Learning (LSTM/GRU; Transformer/TFT only if justified)
        |
        v
Ensemble / Model Selection (only from validation evidence)
        |
        +--> Forecast Service (FastAPI)
        +--> Walk-forward Evaluation
        +--> Backtesting and Risk Analysis
        |
        v
Streamlit Dashboard
        |
        v
Monitoring: Data Freshness, Model Drift, Forecast vs Actual
```

# 4. Functional Modules

## 4.1 Market Overview

-   Global and Indonesian watchlists
-   Latest available prices and daily returns
-   Index context (for example, S&P 500, Nasdaq, IHSG) where data is
    available
-   Data freshness indicators
-   Clear market timezone and currency labels

## 4.2 Stock Analysis

-   OHLCV history
-   Adjusted close / corporate action handling
-   Candlestick and volume charts
-   Technical indicators: SMA, EMA, RSI, MACD, ATR, Bollinger Bands
-   Volatility and drawdown history
-   Fundamentals only when reliable point-in-time data is available

## 4.3 Prediction Center

-   Q1 2027 forecast as primary view
-   1/5/10/20/60-trading-day forecasts
-   Expected return and implied price
-   Calibrated prediction intervals
-   Bull/base/bear scenarios derived from model distributions or
    documented assumptions
-   Forecast origin and data-through date
-   Historical forecast-versus-actual tracking
-   Prominent disclaimer and uncertainty display

## 4.4 Model Laboratory

-   Baseline models: zero-return, historical mean, simple linear model
-   Statistical baseline: ARIMA where appropriate
-   Classical ML: Random Forest, XGBoost, LightGBM
-   Deep learning: LSTM/GRU
-   Transformer/TFT only after data volume, compute, and validation
    justify them
-   Ensemble only if it improves robust out-of-sample performance
-   Model registry and experiment tracking

## 4.5 Backtesting and Risk

-   Walk-forward or rolling-origin evaluation
-   No random shuffling of time-series observations
-   Transaction costs, spread, slippage, and realistic execution timing
-   Sharpe and Sortino ratios, maximum drawdown, volatility, turnover,
    hit rate
-   Benchmark against buy-and-hold and simple baselines
-   Avoid look-ahead bias, survivorship bias, and overlapping-label
    leakage
-   Clearly distinguish forecast evaluation from strategy backtesting

## 4.6 Portfolio Analytics

-   User-defined paper portfolio
-   Position weights and exposure
-   Correlation matrix
-   Portfolio volatility and drawdown
-   Scenario analysis
-   No live order placement in the initial scope

## 4.7 System Monitoring

-   Provider/API status and data freshness
-   Missing data and anomaly flags
-   Model training runs and model versions
-   Prediction history
-   Forecast-versus-actual results
-   Error logs and reproducible run metadata

# 5. Data Design and Data Governance

## 5.1 Data categories

1.  **Market data:** OHLCV, adjusted prices, volume, splits, dividends.
2.  **Market context:** relevant indices, sector proxies, FX rates.
3.  **Macro data:** rates, inflation, and other selected series where
    timing and release dates are known.
4.  **Fundamentals:** valuation, earnings, revenue, and balance-sheet
    variables where point-in-time history is available.
5.  **News/sentiment:** optional future extension; requires a reliable
    provider, timestamping, source tracking, and licensing review.

## 5.2 Data source principles

-   Free sources are suitable for prototyping, not automatically for
    production or investment-grade decisions.
-   Verify provider terms, rate limits, historical coverage, ticker
    mappings, adjustments, and commercial-use restrictions.
-   Do not scrape or redistribute data in violation of provider terms.
-   Use official or licensed Indonesian market data for serious
    validation.
-   Store source, retrieval time, market timestamp, currency, timezone,
    and adjustment status.
-   Keep raw data immutable where possible; create cleaned/adjusted
    datasets as versioned derived artifacts.
-   Treat missing data explicitly. Never silently forward-fill prices
    across non-trading days.
-   Use point-in-time fundamentals and macro release dates to prevent
    future information leaking into historical features.

## 5.3 Currency and exchange handling

-   US equities are normally quoted in USD; Indonesian equities in IDR.
-   Do not compare nominal prices across currencies.
-   Model local-currency returns for each equity first.
-   If providing a cross-market portfolio view, calculate FX-adjusted
    returns separately and document the FX convention.
-   Respect different trading calendars, holidays, sessions, and
    timezones.

# 6. Quantitative Research Methodology

## 6.1 Feature engineering

Candidate features: - Lagged returns over multiple windows - Rolling
volatility - SMA/EMA distances - RSI, MACD, ATR, Bollinger position -
Volume change and relative volume - Market/index returns and
volatility - FX and macro variables where point-in-time safe -
Fundamental variables only when historical publication timestamps are
available

Features must be computed using information available at or before the
forecast origin. Any scaler, imputer, selector, or transformation must
be fit on training data only.

## 6.2 Model development order

1.  Naive/zero-return and historical-mean baselines
2.  Linear or regularized regression
3.  Random Forest
4.  XGBoost and LightGBM
5.  ARIMA or other statistical baselines where appropriate
6.  LSTM/GRU
7.  Transformer/TFT only if justified
8.  Ensemble only after honest out-of-sample comparison

Do not assume deep learning is superior. Financial returns are noisy;
simpler models may generalize better.

## 6.3 Validation

-   Use chronological train/validation/test splits.
-   Use expanding-window or rolling-window walk-forward validation.
-   Keep a final untouched holdout period where possible.
-   For overlapping forward-return labels, use appropriate
    purging/embargo or non-overlapping evaluation design.
-   Tune hyperparameters only within training/validation windows.
-   Record the exact data cutoff for every run.
-   Compare against naive baselines.

## 6.4 Metrics

Forecast metrics: - MAE - RMSE - Directional accuracy - Sign accuracy by
horizon - Rank correlation, if cross-sectional ranking is a project
objective - Prediction interval coverage and width - Calibration
diagnostics

Strategy metrics: - Cumulative return - Annualized volatility - Sharpe
ratio - Sortino ratio - Maximum drawdown - Turnover - Transaction
costs - Benchmark-relative performance

No single metric should determine model selection. Report uncertainty
and stability across time periods and tickers.

# 7. Q1 2027 Evaluation Protocol

The Q1 forecast is the primary research target, but there is only one
realized Q1 2027 outcome. A single quarter is not enough to establish
model reliability.

Therefore: - Train and validate on many historical rolling windows with
comparable horizons (approximately one quarter of trading sessions). -
Backtest the same forecast procedure on prior quarters. - Freeze the
forecast origin and target definition for each historical simulation. -
Use only information available at each simulated origin. - Generate the
live Q1 2027 forecast with the latest eligible data. - Re-run/update
forecasts only under a documented schedule or explicit user action. -
Preserve every forecast version so later revisions do not overwrite
history.

If the forecast is generated before January 2027, display both: 1.
forecast from current origin to the final Q1 trading session; and 2.
estimated official Q1 calendar return from the last 2026 close to the
final Q1 close.

Explain that the second is a forecast of a fixed calendar-quarter
target, not an observed result.

# 8. Database and Storage Sketch

Suggested entities/tables: - `assets`: ticker, exchange, currency, asset
name, active dates - `data_sources`: provider, source configuration,
terms metadata - `market_bars`: asset, timestamp, OHLCV, adjusted
fields, source - `corporate_actions`: splits, dividends, effective
dates - `macro_observations`: series, observation date, release date,
value, source - `feature_sets`: feature definition and version -
`model_runs`: model, parameters, data cutoff, training window, code
version - `model_metrics`: run, ticker, horizon, split, metric, value -
`forecasts`: asset, origin, horizon, target definition, estimate,
interval, model version - `forecast_outcomes`: forecast ID, realized
target, evaluation timestamp - `backtest_runs`: strategy, period,
assumptions, benchmark, results - `portfolio_snapshots`: holdings,
weights, timestamp - `system_events`: ingestion and model pipeline logs

Use PostgreSQL for metadata and queryable records. Use Parquet for
larger historical feature and experiment datasets. Avoid storing large
model artifacts directly in relational tables.

# 9. API and Dashboard Sketch

## FastAPI endpoints (proposed)

-   `GET /health`
-   `GET /assets`
-   `GET /market-data/{ticker}`
-   `GET /forecasts/{ticker}`
-   `GET /forecasts/{ticker}/history`
-   `GET /models`
-   `GET /model-runs`
-   `GET /backtests/{run_id}`
-   `GET /portfolio/analytics`

Training and ingestion endpoints should be protected or restricted to
local/admin use. Do not expose arbitrary model-training execution
publicly.

## Streamlit pages

1.  Overview
2.  Market Explorer
3.  Stock Detail
4.  Q1 2027 Forecast
5.  Multi-Horizon Forecast
6.  Model Laboratory
7.  Backtesting & Risk
8.  Portfolio Analytics
9.  Data & Model Monitoring
10. Settings / About

Use a clean, professional financial analytics UI. Display source,
timestamp, currency, horizon, and uncertainty wherever relevant.

# 10. Proposed Repository Structure

``` text
astraquant/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── docker-compose.yml
├── configs/
│   ├── assets.yaml
│   ├── data_sources.yaml
│   ├── features.yaml
│   ├── models.yaml
│   └── settings.yaml
├── data/
│   ├── raw/                 # gitignored
│   ├── processed/           # gitignored
│   └── external/            # gitignored
├── artifacts/               # gitignored; model artifacts
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_research.ipynb
│   └── 03_model_experiments.ipynb
├── src/
│   └── astraquant/
│       ├── config/
│       ├── data/
│       │   ├── providers/
│       │   ├── ingestion/
│       │   └── validation/
│       ├── features/
│       ├── targets/
│       ├── research/
│       ├── models/
│       │   ├── baselines/
│       │   ├── statistical/
│       │   ├── classical_ml/
│       │   ├── deep_learning/
│       │   └── ensemble/
│       ├── evaluation/
│       ├── backtesting/
│       ├── risk/
│       ├── portfolio/
│       ├── services/
│       ├── database/
│       └── utils/
├── api/
│   └── main.py
├── dashboard/
│   └── app.py
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── leakage/
├── scripts/
│   ├── ingest_data.py
│   ├── build_features.py
│   ├── train_models.py
│   └── run_backtest.py
└── docs/
    ├── PROJECT_BLUEPRINT.md
    ├── DATA_DICTIONARY.md
    ├── MODEL_CARD_TEMPLATE.md
    ├── VALIDATION_PROTOCOL.md
    └── DECISIONS.md
```

The exact structure can be adjusted after inspecting the existing
repository. Do not overwrite an existing project blindly.

# 11. Implementation Milestones

## Phase 0 --- Discovery and technical design

-   Inspect repository and local environment.
-   Confirm Python version and dependency strategy.
-   Finalize target definitions and forecast origin rules.
-   Verify data providers and terms.
-   Produce architecture, data dictionary, risk register, and
    implementation plan.
-   No broad implementation before the plan is reviewed.

**Exit criteria:** design decisions documented; unresolved assumptions
listed.

## Phase 1 --- Data foundation

-   Build provider adapters.
-   Ingest the initial ticker universe.
-   Normalize symbols, timestamps, currencies, and exchange calendars.
-   Validate OHLCV, duplicates, gaps, and corporate actions.
-   Persist raw and processed data.

**Exit criteria:** repeatable ingestion; data-quality report; tests for
provider and schema behavior.

## Phase 2 --- Targets and feature engineering

-   Implement forward-return targets.
-   Implement Q1 target definitions.
-   Build technical and market-context features.
-   Add point-in-time safeguards.
-   Create feature versioning and dataset generation.

**Exit criteria:** leakage tests pass; features are reproducible.

## Phase 3 --- Baseline and classical ML

-   Build naive and statistical baselines.
-   Train linear, Random Forest, XGBoost, and LightGBM models.
-   Implement walk-forward evaluation.
-   Save metrics and artifacts.

**Exit criteria:** baseline comparison report for every ticker/horizon.

## Phase 4 --- Deep learning and ensemble research

-   Implement LSTM/GRU experiments.
-   Consider Transformer/TFT only if justified by data and compute.
-   Compare models using identical splits and targets.
-   Test ensemble methods only when they improve robust validation
    results.

**Exit criteria:** reproducible experiment report; no model promoted
solely on training performance.

## Phase 5 --- Backtesting and risk

-   Convert forecasts into explicitly defined hypothetical strategies.
-   Include realistic execution timing, fees, spread, and slippage.
-   Compare against benchmarks.
-   Report risk and sensitivity analysis.

**Exit criteria:** reproducible backtests with documented assumptions.

## Phase 6 --- API, database, and dashboard

-   Implement FastAPI services.
-   Implement PostgreSQL persistence and migrations.
-   Build Streamlit pages.
-   Connect UI to service layer.
-   Add clear loading, empty, and error states.

**Exit criteria:** end-to-end local workflow works with stored
forecasts.

## Phase 7 --- Monitoring and hardening

-   Add data freshness checks.
-   Track forecast outcomes and model performance.
-   Add logs, tests, dependency pinning, and setup documentation.
-   Add Docker Compose if useful.
-   Review secrets, access controls, and provider terms.

**Exit criteria:** documented repeatable setup and operational checks.

# 12. What the User Must Prepare Manually

Claude Code can write code, create tests, configure local services, and
help debug. It cannot independently provide every external permission,
account, paid data entitlement, or local decision.

## Required before meaningful implementation

1.  **Computer and development environment**
    -   A laptop/desktop with Python support.
    -   VS Code or another editor.
    -   Git installed.
    -   Claude Code installed and authenticated.
    -   Terminal access to the project folder.
2.  **Project location**
    -   Create or select a dedicated project folder.
    -   Decide whether the repository is new or existing.
    -   Create a Git repository and make an initial commit before major
        changes.
3.  **Data-source decisions**
    -   Decide whether free historical data is sufficient for the
        prototype.
    -   For serious Indonesian equity validation, investigate
        official/licensed IDX data access.
    -   If using an API provider, create the account, choose a plan,
        accept terms, and obtain the API key yourself.
4.  **Forecast definition approval**
    -   Confirm price return versus total return.
    -   Confirm forecast origin and Q1 baseline.
    -   Confirm whether the app is research-only (recommended
        initially).

## Required when the relevant phase begins

5.  **API credentials**
    -   Obtain keys for chosen market-data or macro providers.
    -   Put secrets in a local `.env` file.
    -   Never paste keys into source code, prompts, Git commits, or
        public screenshots.
    -   Commit only `.env.example`, not `.env`.
6.  **Database**
    -   Install/run PostgreSQL locally or choose a hosted database.
    -   Create database and user credentials.
    -   Claude Code can write schema and migrations, but the user must
        authorize/start the service and manage credentials.
7.  **Data licensing and payment**
    -   Personally review and accept provider terms.
    -   Pay for subscriptions if needed.
    -   Confirm whether use is personal, academic, or commercial.
    -   Confirm storage and redistribution permissions.
8.  **Compute decisions**
    -   Start with CPU-friendly baselines and gradient boosting.
    -   Decide on GPU/cloud only if deep-learning experiments justify
        it.
    -   Do not buy hardware or cloud resources before benchmarking.
9.  **Product decisions**
    -   Approve ticker universe.
    -   Approve dashboard look and feel.
    -   Approve refresh frequency and forecast update policy.
    -   Decide whether to publish/deploy; deployment is not required for
        a local research project.

## What Claude Code can usually handle

-   Scaffold the repository and modules.
-   Write Python code, tests, SQL migrations, API routes, and dashboard
    pages.
-   Implement ingestion adapters after provider/API choices are known.
-   Generate documentation and configuration templates.
-   Run local commands and tests when its environment permissions allow.
-   Diagnose errors from logs and test results.
-   Implement model experiments and backtesting code.
-   Create Docker configuration and local setup scripts.

## What Claude Code cannot be assumed to handle

-   Register accounts or accept legal terms on the user's behalf.
-   Purchase data subscriptions or approve payments.
-   Magically access private market data without credentials and
    entitlements.
-   Guarantee the completeness or correctness of third-party data.
-   Guarantee forecast accuracy or profitability.
-   Decide legal permission to use or redistribute a dataset.
-   Keep a local machine or database running when the environment is
    shut down.
-   Verify live production reliability without actual deployment and
    monitoring.

# 13. Security, Reliability, and Research Guardrails

-   Never commit secrets or private credentials.
-   Do not use future data in historical features.
-   Do not randomly shuffle time-series observations for model
    validation.
-   Track corporate actions and delisted assets where possible.
-   Make provider limitations visible in the UI.
-   Keep an audit trail for forecasts and model versions.
-   Do not overwrite old forecasts when new ones are generated.
-   Do not claim a strategy is profitable based on in-sample results.
-   Include fees and slippage in strategy evaluation.
-   No live trading or broker order execution in the initial release.
-   Label all outputs as research estimates, not guarantees.

# 14. Definition of Done

The first complete release is acceptable when:

1.  The configured global and Indonesian tickers can be ingested
    reproducibly.
2.  Data quality and data freshness are visible.
3.  Targets and features have documented definitions.
4.  Baseline, classical ML, and justified deep-learning models can be
    trained.
5.  Walk-forward validation is implemented without known leakage.
6.  Q1 2027 and multi-horizon forecasts are stored with origin, model
    version, and uncertainty.
7.  Forecast performance is compared against simple baselines.
8.  Backtesting includes documented execution assumptions and costs.
9.  API and dashboard can display forecasts, metrics, and history.
10. Tests, setup instructions, limitations, and model documentation are
    provided.

A completed interface without a valid data pipeline and leakage-safe
evaluation is not considered a completed quantitative forecasting
system.

------------------------------------------------------------------------

# 15. Claude Code Master Prompt

Copy the prompt below into Claude Code after opening the project
directory. It is intentionally written to make Claude Code inspect and
plan first, rather than immediately generating a large amount of
unreviewed code.

------------------------------------------------------------------------

You are acting as a senior quantitative researcher, quantitative
developer, Python software architect, machine-learning engineer, data
engineer, and technical lead.

Your task is to design and progressively build **AstraQuant**, a
research-grade quantitative machine-learning stock forecasting and
analytics platform.

## A. Project objective

Build a modular Python platform that forecasts forward equity returns
for:

Global: - NVDA, AAPL, MSFT, GOOGL, AMZN, META

Indonesia: - BBCA, BBRI, BMRI, BBNI, BBTN

Primary objective: - Forecast the Q1 2027 equity return / end-of-quarter
outcome. - Store forecast origin, target definition, data cutoff, model
version, point estimate, and uncertainty. - Clearly distinguish a
forecast made before Q1 from the official realized calendar-quarter
return.

Secondary objectives: - Forecast 1, 5, 10, 20, and 60 trading-day
returns.

The application is for quantitative research and decision support, not
automated trading or guaranteed investment advice.

## B. Agreed architecture

Use a Hybrid Quant + Deep Learning approach.

Preferred stack: - Python - Pandas, NumPy - scikit-learn - XGBoost and
LightGBM - statsmodels - PyTorch - NeuralForecast only if justified -
VectorBT or a carefully tested alternative for backtesting - QuantStats
for supplementary analytics - FastAPI - Streamlit - PostgreSQL -
Parquet - SQLAlchemy and Alembic - pytest - Ruff - MLflow for experiment
tracking if practical

Do not blindly install all packages. Verify compatibility, use stable
versions, pin dependencies, and justify each dependency.

## C. Non-negotiable research rules

1.  Never use random train-test splitting for time-series forecasting.
2.  Use chronological splits and walk-forward / rolling-origin
    validation.
3.  Prevent look-ahead bias, target leakage, survivorship bias, and
    preprocessing leakage.
4.  Fit scalers, imputers, selectors, and transformations only on
    training windows.
5.  Respect point-in-time availability of fundamentals and macroeconomic
    releases.
6.  Include corporate actions and clearly document adjusted-price
    semantics.
7.  Respect US and Indonesian trading calendars, timezones, and
    currencies.
8.  Evaluate all models against simple baselines.
9.  Do not assume deep learning is superior.
10. Do not promote a model because of training performance.
11. Do not fabricate missing data, provider credentials, performance
    results, or model confidence.
12. Label uncertain or unavailable information explicitly.
13. Do not implement live broker execution in the initial scope.

## D. Q1 target definition

Before implementation, document two distinct concepts:

1.  A pre-Q1 forecast from the latest available forecast-origin close to
    the final Q1 2027 trading close.
2.  The official calendar-quarter Q1 return, measured from the final
    valid 2026 close to the final valid Q1 2027 close.

These are not interchangeable.

Store the origin date, baseline date and price, endpoint, exchange
calendar, target type, and realized outcome separately. Forecasts
generated during Q1 must show their remaining horizon and must not be
misleadingly compared with a full-quarter return.

Use forward percentage return as the principal target. Make price return
versus total return an explicit documented decision.

## E. Required modules

1.  Market data ingestion and provider adapters.
2.  Data validation and corporate-action handling.
3.  Feature engineering and target generation.
4.  Statistical and classical ML models.
5.  Deep-learning models where justified.
6.  Ensemble research.
7.  Walk-forward evaluation and model comparison.
8.  Backtesting and risk analytics.
9.  PostgreSQL persistence and Parquet storage.
10. FastAPI prediction service.
11. Streamlit dashboard.
12. Forecast history and outcome tracking.
13. Data/model monitoring.
14. Tests and technical documentation.

## F. Required dashboard pages

-   Market Overview
-   Market Explorer
-   Stock Detail
-   Q1 2027 Forecast
-   Multi-Horizon Forecast
-   Model Laboratory
-   Backtesting & Risk
-   Portfolio Analytics
-   Data & Model Monitoring
-   Settings / About

Use a polished, professional financial analytics design. Every forecast
must show ticker, exchange, currency, forecast origin, data-through
date, horizon, model version, expected return, uncertainty, and relevant
caveats.

## G. Development workflow

Work in gated milestones.

### Phase 0 --- Discovery and design (FIRST TASK)

Do not immediately implement the full system.

First: 1. Inspect the current working directory and repository. 2.
Identify existing files and code that must be preserved. 3. Inspect
Python version, OS, installed tools, and environment constraints. 4.
Identify whether this is a new or existing project. 5. List missing
credentials and external dependencies without requesting or exposing
secrets. 6. Validate package availability and likely compatibility. 7.
Identify data-provider options and their limitations; do not assume an
API is free, reliable, or licensed for every use. 8. Resolve ambiguities
in Q1 target definitions. 9. Propose final architecture and repository
structure. 10. Create a phased implementation plan with dependencies and
acceptance criteria.

Create or update these documents: - `docs/PROJECT_BLUEPRINT.md` -
`docs/DATA_DICTIONARY.md` - `docs/VALIDATION_PROTOCOL.md` -
`docs/DECISIONS.md` - `docs/RISK_REGISTER.md` -
`docs/IMPLEMENTATION_PLAN.md` - `README.md`

If a document already exists, inspect and update it carefully. Do not
destroy useful content.

At the end of Phase 0, report: - Repository/environment findings -
Proposed architecture - Data-source choices and unresolved provider
decisions - Required manual user actions - Risks and assumptions -
Milestones and acceptance criteria - Exact commands needed to prepare
the environment

**STOP after Phase 0 and request review/approval before beginning broad
implementation.**

### Later phases

After approval, implement one phase at a time:

1.  Data foundation
2.  Targets and feature engineering
3.  Baselines and classical ML
4.  Deep learning and ensemble research
5.  Walk-forward validation, backtesting, and risk
6.  Database, API, and dashboard
7.  Monitoring, security, documentation, and hardening

At the end of each phase: - Run relevant tests. - Report files
created/modified. - Report commands executed. - Report test results
honestly. - List known issues and unresolved decisions. - Demonstrate
acceptance criteria. - Do not claim completion if tests were not run or
failed. - Stop for review before moving to the next major phase.

## H. Code quality expectations

-   Modular, typed, documented Python code.
-   Avoid giant monolithic files.
-   Use configuration-driven ticker lists and model settings.
-   Keep data access, research logic, API, and UI separated.
-   Use dependency injection or clear interfaces where useful.
-   Add unit, integration, and data-leakage tests.
-   Use reproducible random seeds where relevant.
-   Record code version, feature version, data cutoff, and model
    parameters.
-   Add structured logging and useful error messages.
-   Never hardcode API keys or passwords.
-   Provide `.env.example`, `.gitignore`, and setup instructions.
-   Do not place large datasets, secrets, or model binaries in Git.
-   Prefer small, reviewable changes.

## I. Model selection expectations

Begin with naive baselines and classical ML before deep learning.

Compare: - Zero-return / historical-mean baseline - Linear or
regularized regression - Random Forest - XGBoost - LightGBM - ARIMA
where appropriate - LSTM / GRU - Transformer / TFT only if justified

Use identical chronological evaluation windows when comparing models.
Report MAE, RMSE, directional accuracy, prediction interval coverage,
and relevant strategy metrics.

Use an ensemble only when out-of-sample evidence demonstrates a robust
improvement.

## J. User interaction and permissions

-   Ask before destructive operations, deleting data, overwriting
    existing project files, or running costly cloud jobs.
-   Never request that the user paste secrets into chat or source files.
-   Provide commands the user can run locally for authentication and
    credential setup.
-   Distinguish what can be automated in the local development
    environment from actions requiring account ownership, payment, legal
    acceptance, or external permissions.
-   Do not deploy publicly without explicit approval.

## K. First response required

Start by performing Phase 0 discovery only.

Do not generate the entire application in one pass.

Your first response must provide a concise but technically meaningful
discovery report, proposed architecture, unresolved decisions, manual
preparation checklist, and a proposed Phase 1 plan. Wait for approval
before broad implementation.

------------------------------------------------------------------------

# 16. Recommended first manual checklist

Before starting Claude Code, prepare:

-   [ ] Create project folder `astraquant`
-   [ ] Open it in VS Code
-   [ ] Install and authenticate Claude Code
-   [ ] Install Git
-   [ ] Confirm Python environment
-   [ ] Initialize Git and make an initial commit
-   [ ] Decide whether to begin with free historical data
-   [ ] Investigate official/licensed IDX data access for later
    validation
-   [ ] Decide price return versus total return
-   [ ] Do not put API keys in the prompt or repository

**Recommended starting point:** ask Claude Code to complete Phase 0
only. Review its design and provider assumptions before allowing
implementation.
