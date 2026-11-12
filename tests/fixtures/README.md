# Test fixtures

Small excerpts of real processed bars, so tests run in a fresh clone without `data/`.

| File | Window | Why |
|---|---|---|
| `prices/NVDA.csv` | 2024-03-01 to 2024-07-31 | 10:1 split on 2024-06-10, dividend before it |
| `prices/BBCA.JK.csv` | 2021-03-01 to 2021-11-30 | 5:1 split on 2021-10-13, dividend before it |

Source: Yahoo Finance through yfinance 1.8.0, ingest run `20261112T152107Z`, processed
schema (`close` split-adjusted, not dividend-adjusted). Unofficial data, kept only to
test code. Do not use these files for analysis.
