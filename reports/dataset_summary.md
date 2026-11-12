# Dataset coverage report

- Built 2026-11-12T15:28:59.286806+00:00 from ingest run `20261112T152754Z`.
- Source: yfinance. **Unofficial data, prototyping only.**
- Git commit: `e2fe7bb074fa21a586ced3e0d9120d7c7466a14f`
- Config digest: `47128b14d444b416`; feature set `v1`.
- Data through: ID 2026-11-12, US 2026-11-11
- Rows: daily 45,302; quarterly 728.
- This report shows availability only. No target statistics are shown.
- Rule: windows and horizons are counted in exchange sessions. A feature or target
  that touches a missing bar is NaN. Nothing is filled or shifted.

## Session grid per symbol

| symbol | market | sessions | first | last | missing_bars |
|---|---|---|---|---|---|
| NVDA | US | 4241 | 2010-01-04 | 2026-11-11 | 0 |
| AAPL | US | 4241 | 2010-01-04 | 2026-11-11 | 0 |
| MSFT | US | 4241 | 2010-01-04 | 2026-11-11 | 0 |
| GOOGL | US | 4241 | 2010-01-04 | 2026-11-11 | 0 |
| AMZN | US | 4241 | 2010-01-04 | 2026-11-11 | 0 |
| META | US | 3642 | 2012-05-18 | 2026-11-11 | 0 |
| BBCA.JK | ID | 4091 | 2010-01-04 | 2026-11-12 | 24 |
| BBRI.JK | ID | 4091 | 2010-01-04 | 2026-11-12 | 22 |
| BMRI.JK | ID | 4091 | 2010-01-04 | 2026-11-12 | 23 |
| BBNI.JK | ID | 4091 | 2010-01-04 | 2026-11-12 | 23 |
| BBTN.JK | ID | 4091 | 2010-01-04 | 2026-11-12 | 23 |

## Share of daily rows that are NaN, by market

Features (FX features are NaN by design for US names):

| column | ID | US |
|---|---|---|
| ret_5 | 1.2% | 0.1% |
| ret_20 | 1.6% | 0.5% |
| ret_60 | 2.6% | 1.4% |
| ret_120 | 4.1% | 2.9% |
| ret_250 | 7.2% | 6.0% |
| rvol_20 | 6.1% | 0.5% |
| rvol_60 | 14.8% | 1.4% |
| rvol_120 | 25.5% | 2.9% |
| ma_dist_50 | 12.6% | 1.2% |
| ma_dist_200 | 37.9% | 4.8% |
| rsi_14 | 4.6% | 0.3% |
| drawdown_250 | 44.7% | 6.0% |
| rel_volume_20_120 | 25.3% | 2.9% |
| mkt_ret_20 | 0.5% | 0.5% |
| mkt_ret_60 | 1.5% | 1.4% |
| mkt_rvol_20 | 0.5% | 0.5% |
| mkt_rvol_60 | 1.5% | 1.4% |
| fx_ret_20 | 1.1% | 100.0% |
| fx_ret_60 | 2.1% | 100.0% |

Targets (the last `h` sessions of each series are NaN because the future is unknown):

| column | ID | US |
|---|---|---|
| fwd_ret_5 | 1.2% | 0.1% |
| fwd_ret_20 | 1.6% | 0.5% |
| fwd_ret_60 | 2.6% | 1.4% |
| fwd_vol_20 | 6.1% | 0.5% |
| fwd_vol_60 | 14.8% | 1.4% |

## Quarterly dataset per symbol

`realised` = quarter return available; `features_complete` = every feature at the
origin is available; `usable` = both.

| symbol | market | quarters | first | last | realised | features_complete | usable |
|---|---|---|---|---|---|---|---|
| NVDA | US | 67 | 2010Q2 | 2026Q4 | 66 | 64 | 63 |
| AAPL | US | 67 | 2010Q2 | 2026Q4 | 66 | 64 | 63 |
| MSFT | US | 67 | 2010Q2 | 2026Q4 | 66 | 64 | 63 |
| GOOGL | US | 67 | 2010Q2 | 2026Q4 | 66 | 64 | 63 |
| AMZN | US | 67 | 2010Q2 | 2026Q4 | 66 | 64 | 63 |
| META | US | 58 | 2012Q3 | 2026Q4 | 57 | 54 | 53 |
| BBCA.JK | ID | 67 | 2010Q2 | 2026Q4 | 66 | 33 | 32 |
| BBRI.JK | ID | 67 | 2010Q2 | 2026Q4 | 66 | 38 | 37 |
| BMRI.JK | ID | 67 | 2010Q2 | 2026Q4 | 66 | 33 | 32 |
| BBNI.JK | ID | 67 | 2010Q2 | 2026Q4 | 66 | 36 | 35 |
| BBTN.JK | ID | 67 | 2010Q2 | 2026Q4 | 66 | 38 | 37 |

## Usable quarterly rows per year

| year | ID | US |
|---|---|---|
| 2010 | 0 | 0 |
| 2011 | 8 | 20 |
| 2012 | 0 | 20 |
| 2013 | 0 | 22 |
| 2014 | 10 | 24 |
| 2015 | 20 | 24 |
| 2016 | 5 | 24 |
| 2017 | 2 | 24 |
| 2018 | 2 | 24 |
| 2019 | 5 | 24 |
| 2020 | 11 | 24 |
| 2021 | 15 | 24 |
| 2022 | 20 | 24 |
| 2023 | 20 | 24 |
| 2024 | 20 | 24 |
| 2025 | 20 | 24 |
| 2026 | 15 | 18 |

## Ended quarters with no label (a boundary session has no bar)

_None._

## Realised quarterly rows missing each feature at the origin

Realised rows per market: ID 330, US 387. Row-level detail is in `quarterly.parquet`.

| feature | ID | US |
|---|---|---|
| ret_5 | 0 | 0 |
| ret_20 | 5 | 0 |
| ret_60 | 5 | 1 |
| ret_120 | 5 | 7 |
| ret_250 | 22 | 19 |
| rvol_20 | 19 | 0 |
| rvol_60 | 49 | 1 |
| rvol_120 | 81 | 7 |
| ma_dist_50 | 33 | 1 |
| ma_dist_200 | 126 | 18 |
| rsi_14 | 14 | 0 |
| drawdown_250 | 150 | 19 |
| rel_volume_20_120 | 81 | 7 |
| mkt_ret_20 | 0 | 0 |
| mkt_ret_60 | 0 | 1 |
| mkt_rvol_20 | 0 | 0 |
| mkt_rvol_60 | 0 | 1 |
| fx_ret_20 | 5 | 387 |
| fx_ret_60 | 0 | 387 |

## Limitations

- The 11 names were chosen with hindsight; results carry selection bias.
- Quarterly rows are few and the names are highly correlated.
- Yahoo applies an unrecorded adjustment at rights-issue ex-dates of four Indonesian
  banks (DECISIONS.md 6.3, Q-17). The affected labels and features are still in this
  dataset, unchanged.
- Features for the first 250 sessions of each series are NaN by construction.
