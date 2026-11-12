# Dataset coverage report

- Built 2026-11-12T15:37:24.341203+00:00 from ingest run `20261112T152754Z`.
- Source: yfinance. **Unofficial data, prototyping only.**
- Git commit: `a42ed7ec75850c466c8fd4c7ced14ad9d80b7d51` (tracked files had uncommitted changes)
- Config digest: `43a40a5a34dc2654`; feature set `v2`.
- Data through: ID 2026-11-12, US 2026-11-11
- Rows: daily 45,302; quarterly 728.
- This report shows availability only. No target statistics are shown.
- Rule: windows and horizons are counted in exchange sessions. Labels and windows
  shorter than 120 sessions are strict: touching a missing bar gives NaN. Windows of
  120 sessions or more tolerate 2% missing bars in the middle (both ends must exist)
  and are computed on the bars that exist. Nothing is filled or shifted.
- Labels whose window crosses a configured price break are NaN.

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
| ret_5 | 1.3% | 0.1% |
| ret_20 | 2.1% | 0.5% |
| ret_60 | 4.1% | 1.4% |
| ret_120 | 4.1% | 2.9% |
| ret_250 | 7.2% | 6.0% |
| rvol_20 | 6.6% | 0.5% |
| rvol_60 | 16.3% | 1.4% |
| rvol_120 | 11.0% | 2.9% |
| ma_dist_50 | 13.8% | 1.2% |
| ma_dist_200 | 15.4% | 4.8% |
| rsi_14 | 5.0% | 0.3% |
| drawdown_250 | 18.9% | 6.0% |
| rel_volume_20_120 | 16.5% | 2.9% |
| mkt_ret_20 | 0.5% | 0.5% |
| mkt_ret_60 | 1.5% | 1.4% |
| mkt_rvol_20 | 0.5% | 0.5% |
| mkt_rvol_60 | 1.5% | 1.4% |
| fx_ret_20 | 1.1% | 100.0% |
| fx_ret_60 | 2.1% | 100.0% |

Targets (the last `h` sessions of each series are NaN because the future is unknown):

| column | ID | US |
|---|---|---|
| fwd_ret_5 | 1.3% | 0.1% |
| fwd_ret_20 | 2.1% | 0.5% |
| fwd_ret_60 | 4.1% | 1.4% |
| fwd_vol_20 | 6.6% | 0.5% |
| fwd_vol_60 | 16.3% | 1.4% |

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
| BBCA.JK | ID | 67 | 2010Q2 | 2026Q4 | 66 | 45 | 44 |
| BBRI.JK | ID | 67 | 2010Q2 | 2026Q4 | 65 | 45 | 43 |
| BMRI.JK | ID | 67 | 2010Q2 | 2026Q4 | 65 | 43 | 42 |
| BBNI.JK | ID | 67 | 2010Q2 | 2026Q4 | 65 | 46 | 45 |
| BBTN.JK | ID | 67 | 2010Q2 | 2026Q4 | 64 | 43 | 40 |

## Quarterly rows per year: labelled, and labelled with complete features

| year | ID labelled | ID labelled and complete | US labelled | US labelled and complete |
|---|---|---|---|---|
| 2010 | 14 | 0 | 15 | 0 |
| 2011 | 19 | 7 | 20 | 20 |
| 2012 | 19 | 8 | 22 | 20 |
| 2013 | 20 | 9 | 24 | 22 |
| 2014 | 20 | 20 | 24 | 24 |
| 2015 | 20 | 20 | 24 | 24 |
| 2016 | 20 | 5 | 24 | 24 |
| 2017 | 20 | 6 | 24 | 24 |
| 2018 | 20 | 10 | 24 | 24 |
| 2019 | 20 | 5 | 24 | 24 |
| 2020 | 20 | 17 | 24 | 24 |
| 2021 | 19 | 16 | 24 | 24 |
| 2022 | 19 | 18 | 24 | 24 |
| 2023 | 20 | 18 | 24 | 24 |
| 2024 | 20 | 20 | 24 | 24 |
| 2025 | 20 | 20 | 24 | 24 |
| 2026 | 15 | 15 | 18 | 18 |
| total | 325 | 214 | 387 | 368 |

## Ended quarters with no label (missing boundary bar or price break in the window)

| symbol | quarter | target_start_date | target_end_date |
|---|---|---|---|
| BBRI.JK | 2021Q3 | 2021-06-30 | 2021-09-30 |
| BMRI.JK | 2011Q1 | 2010-12-30 | 2011-03-31 |
| BBNI.JK | 2010Q4 | 2010-09-30 | 2010-12-30 |
| BBTN.JK | 2012Q4 | 2012-09-28 | 2012-12-28 |
| BBTN.JK | 2022Q4 | 2022-09-30 | 2022-12-30 |

## Realised quarterly rows missing each feature at the origin

Realised rows per market: ID 325, US 387. Row-level detail is in `quarterly.parquet`.

| feature | ID | US |
|---|---|---|
| ret_5 | 0 | 0 |
| ret_20 | 8 | 0 |
| ret_60 | 10 | 1 |
| ret_120 | 5 | 7 |
| ret_250 | 20 | 19 |
| rvol_20 | 22 | 0 |
| rvol_60 | 54 | 1 |
| rvol_120 | 26 | 7 |
| ma_dist_50 | 38 | 1 |
| ma_dist_200 | 44 | 18 |
| rsi_14 | 15 | 0 |
| drawdown_250 | 58 | 19 |
| rel_volume_20_120 | 53 | 7 |
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
  banks (DECISIONS.md 6.3). Labels crossing the five configured dates are NaN; in
  features the ex-date return is treated as one missing bar.
- Long-window features are NaN for the first 250 sessions of each series.
