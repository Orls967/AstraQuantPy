# IDX calendar reconciliation, 2010 to 2025

- Raw run: `20261112T152754Z` (Yahoo Finance via yfinance, unofficial).
- **Library sessions**: `exchange_calendars` XIDX with no overrides.
- **Calendar sessions**: the library minus the holidays in `configs/settings.yaml`.
  Overrides inside this range: 2022-04-29, 2022-05-04, 2022-05-05, 2022-05-06, 2025-08-18.
- **Days with ^JKSE bar**: dates in the raw download, before any cleaning.
- This is a report. The calendar was not changed because of it.
- Caveat: ^JKSE from Yahoo is not an official record of trading days. A
  difference means the two sources disagree, not that either is proven wrong.

## Per year

| year | library sessions | calendar sessions | days with ^JKSE bar | calendar, no index bar | index bar, calendar closed |
|---|---|---|---|---|---|
| 2010 | 245 | 245 | 245 | 0 | 0 |
| 2011 | 247 | 247 | 247 | 0 | 0 |
| 2012 | 246 | 246 | 246 | 0 | 0 |
| 2013 | 244 | 244 | 244 | 0 | 0 |
| 2014 | 242 | 242 | 242 | 0 | 0 |
| 2015 | 244 | 244 | 244 | 0 | 0 |
| 2016 | 246 | 246 | 246 | 0 | 0 |
| 2017 | 238 | 238 | 239 | 0 | 1 |
| 2018 | 240 | 240 | 240 | 0 | 0 |
| 2019 | 245 | 245 | 245 | 0 | 0 |
| 2020 | 242 | 242 | 242 | 0 | 0 |
| 2021 | 247 | 247 | 247 | 0 | 0 |
| 2022 | 250 | 246 | 246 | 0 | 0 |
| 2023 | 239 | 239 | 239 | 0 | 0 |
| 2024 | 237 | 237 | 237 | 0 | 0 |
| 2025 | 237 | 236 | 236 | 0 | 0 |
| total | 3889 | 3884 | 3885 | 0 | 1 |

## Calendar session without a ^JKSE bar

_None._

## ^JKSE bar on a date the calendar marks closed

| date | weekday | banks with a traded bar (volume > 0) |
|---|---|---|
| 2017-12-01 | Friday | 0 of 5 |
