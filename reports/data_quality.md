# Data-quality report

- Run: `20261112T150714Z` (retrieved 2026-11-12T15:07:14.786541+00:00)
- Source: yfinance 1.8.0. **Unofficial data, prototyping only.**
- Git commit: `817a306de1f27ebd804408ddddd1586724b0892c`
- Config digest: `f2a689e37754f5d0`
- Price semantics: close = split-adjusted, not dividend-adjusted (auto_adjust=False)
- Data through: FX 2026-11-11, ID 2026-11-12, US 2026-11-11
- Checks flag problems. Nothing is repaired, filled or interpolated.
- Rows dropped in cleaning (counted below): `dropped_incomplete` = session still open
  at retrieval; `dropped_empty` = no prices; `dropped_closed_day` = zero-volume
  provider placeholder on a date the exchange calendar marks closed.

## Coverage

| symbol | market | role | rows | first_date | last_date | data_through | dropped_incomplete | dropped_empty | dropped_closed_day | splits | dividends | errors | warnings |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NVDA | US | target | 4241 | 2010-01-04 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 2 | 56 | 0 | 1 |
| AAPL | US | target | 4241 | 2010-01-04 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 2 | 57 | 0 | 0 |
| MSFT | US | target | 4241 | 2010-01-04 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 0 | 67 | 0 | 0 |
| GOOGL | US | target | 4241 | 2010-01-04 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 2 | 10 | 0 | 0 |
| AMZN | US | target | 4241 | 2010-01-04 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| META | US | target | 3642 | 2012-05-18 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 0 | 11 | 0 | 2 |
| BBCA.JK | ID | target | 4091 | 2010-01-04 | 2026-11-12 | 2026-11-12 | 0 | 0 | 53 | 1 | 35 | 0 | 29 |
| BBRI.JK | ID | target | 4091 | 2010-01-04 | 2026-11-12 | 2026-11-12 | 0 | 0 | 53 | 2 | 22 | 0 | 28 |
| BMRI.JK | ID | target | 4091 | 2010-01-04 | 2026-11-12 | 2026-11-12 | 0 | 0 | 53 | 2 | 20 | 0 | 30 |
| BBNI.JK | ID | target | 4091 | 2010-01-04 | 2026-11-12 | 2026-11-12 | 0 | 0 | 53 | 1 | 17 | 0 | 28 |
| BBTN.JK | ID | target | 4091 | 2010-01-04 | 2026-11-12 | 2026-11-12 | 0 | 0 | 53 | 0 | 15 | 0 | 28 |
| ^GSPC | US | context | 4241 | 2010-01-04 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| ^JKSE | ID | context | 4091 | 2010-01-04 | 2026-11-12 | 2026-11-12 | 0 | 0 | 1 | 0 | 0 | 0 | 5 |
| IDR=X | FX | context | 4388 | 2010-01-01 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 0 | 0 | 0 | 533 |

## Issue counts by check

| symbol | jump | missing_session | ohlc_inconsistent | zero_volume |
|---|---|---|---|---|
| BBCA.JK | 0 | 5 | 0 | 24 |
| BBNI.JK | 0 | 5 | 0 | 23 |
| BBRI.JK | 0 | 5 | 1 | 22 |
| BBTN.JK | 0 | 5 | 0 | 23 |
| BMRI.JK | 0 | 5 | 2 | 23 |
| IDR=X | 4 | 11 | 518 | 0 |
| META | 2 | 0 | 0 | 0 |
| NVDA | 1 | 0 | 0 | 0 |
| ^JKSE | 0 | 5 | 0 | 0 |

## Errors (all)

_None._

## Large moves without a recorded split (all)

| symbol | date | detail |
|---|---|---|
| NVDA | 2016-11-11 | close-to-close return +29.8%, no split recorded |
| META | 2013-07-25 | close-to-close return +29.6%, no split recorded |
| META | 2022-02-03 | close-to-close return -26.4%, no split recorded |
| IDR=X | 2010-11-01 | close-to-close return -90.0%, no split recorded |
| IDR=X | 2010-11-02 | close-to-close return +902.9%, no split recorded |
| IDR=X | 2012-02-07 | close-to-close return -90.0%, no split recorded |
| IDR=X | 2012-02-08 | close-to-close return +901.1%, no split recorded |

## Calendar cross-check

### XIDX

- Sessions with no bar for **any** symbol (calendar suspect): 5
- Symbol-specific missing sessions: 0

| year | market-wide missing sessions |
|---|---|
| 2022 | 4 |
| 2025 | 1 |

Bars on dates the calendar marks closed: 0.

_None._

## Price-return semantics: known splits

| symbol | date | ratio | passed | recorded_ratio | prev_date | prev_close | close | day_return | implied_unadjusted_prev_close | close_differs_from_adj_close | dividends_before_split |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NVDA | 2024-06-10 | 10 | True | 10.0000 | 2024-06-07 | 120.8880 | 121.7900 | 0.0075 | 1,208.8800 | True | True |
| BBCA.JK | 2021-10-13 | 5 | True | 5.0000 | 2021-10-12 | 7,320.0000 | 7,525.0000 | 0.0280 | 36,600.0000 | True | True |

A check passes when the provider records the split with the expected ratio, `close`
is continuous across the split date (split-adjusted), and `close` differs from
`adj_close` before it (not dividend-adjusted).

## Limitations

- Yahoo Finance data is unofficial and can be revised without notice.
- The full list of flagged rows is in `data/processed/quality_issues.parquet`.
- IDX holidays before 2026 come from the calendar library only; see the calendar
  cross-check above for sessions it appears to get wrong.
- Zero-volume bars on real sessions are kept and flagged. For liquid names they are
  probably stale provider rows, not true closes.
