# Data-quality report

- Run: `20261112T152754Z` (retrieved 2026-11-12T15:27:54.962863+00:00)
- Source: yfinance 1.8.0. **Unofficial data, prototyping only.**
- Git commit: `515580f9b3174098d583301f5d34c12fbfae758b`
- Config digest: `47128b14d444b416`
- Price semantics: close = split-adjusted, not dividend-adjusted (auto_adjust=False)
- Data through: FX 2026-11-11, ID 2026-11-12, US 2026-11-11
- Checks flag problems. Nothing is repaired, filled or interpolated.
- Rows dropped in cleaning (counted below): `dropped_incomplete` = session still open
  at retrieval; `dropped_empty` = no prices; `dropped_excluded` = listed under
  `exclusions` in the config; `dropped_closed_day` = zero-volume provider placeholder
  on a date the calendar marks closed; `dropped_stale` = zero-volume bar of a target
  equity on a real session, treated as a missing session.

## Coverage

| symbol | market | role | rows | first_date | last_date | data_through | dropped_incomplete | dropped_empty | dropped_excluded | dropped_closed_day | dropped_stale | splits | dividends | errors | warnings |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NVDA | US | target | 4241 | 2010-01-04 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 0 | 0 | 2 | 56 | 0 | 1 |
| AAPL | US | target | 4241 | 2010-01-04 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 0 | 0 | 2 | 57 | 0 | 0 |
| MSFT | US | target | 4241 | 2010-01-04 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 0 | 0 | 0 | 67 | 0 | 0 |
| GOOGL | US | target | 4241 | 2010-01-04 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 0 | 0 | 2 | 10 | 0 | 0 |
| AMZN | US | target | 4241 | 2010-01-04 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| META | US | target | 3642 | 2012-05-18 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 2 |
| BBCA.JK | ID | target | 4067 | 2010-01-04 | 2026-11-12 | 2026-11-12 | 0 | 0 | 0 | 53 | 24 | 1 | 34 | 0 | 24 |
| BBRI.JK | ID | target | 4069 | 2010-01-04 | 2026-11-12 | 2026-11-12 | 0 | 0 | 0 | 53 | 22 | 2 | 22 | 0 | 23 |
| BMRI.JK | ID | target | 4068 | 2010-01-04 | 2026-11-12 | 2026-11-12 | 0 | 0 | 0 | 53 | 23 | 2 | 20 | 0 | 25 |
| BBNI.JK | ID | target | 4068 | 2010-01-04 | 2026-11-12 | 2026-11-12 | 0 | 0 | 0 | 53 | 23 | 1 | 17 | 0 | 23 |
| BBTN.JK | ID | target | 4068 | 2010-01-04 | 2026-11-12 | 2026-11-12 | 0 | 0 | 0 | 53 | 23 | 0 | 15 | 0 | 23 |
| ^GSPC | US | context | 4241 | 2010-01-04 | 2026-11-11 | 2026-11-11 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ^JKSE | ID | context | 4091 | 2010-01-04 | 2026-11-12 | 2026-11-12 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| IDR=X | FX | context | 4386 | 2010-01-01 | 2026-11-11 | 2026-11-11 | 1 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 530 |

## Issue counts by check

| symbol | jump | missing_session | ohlc_inconsistent |
|---|---|---|---|
| BBCA.JK | 0 | 24 | 0 |
| BBNI.JK | 0 | 23 | 0 |
| BBRI.JK | 0 | 22 | 1 |
| BBTN.JK | 0 | 23 | 0 |
| BMRI.JK | 0 | 23 | 2 |
| IDR=X | 0 | 13 | 517 |
| META | 2 | 0 | 0 |
| NVDA | 1 | 0 | 0 |

## Errors (all)

_None._

## Large moves without a recorded split (all)

| symbol | date | detail |
|---|---|---|
| NVDA | 2016-11-11 | close-to-close return +29.8%, no split recorded |
| META | 2013-07-25 | close-to-close return +29.6%, no split recorded |
| META | 2022-02-03 | close-to-close return -26.4%, no split recorded |

## Calendar cross-check

### XIDX

- Sessions with no bar for **any** symbol (calendar suspect): 0
- Symbol-specific missing sessions: 115

| symbol | missing sessions |
|---|---|
| BBCA.JK | 24 |
| BBNI.JK | 23 |
| BBRI.JK | 22 |
| BBTN.JK | 23 |
| BMRI.JK | 23 |

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
- Yahoo records no corporate action for rights issues, so `close` is not adjusted
  for them (see DECISIONS.md).
