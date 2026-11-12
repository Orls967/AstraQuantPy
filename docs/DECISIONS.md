# AstraQuant Decisions Log

Append new entries; do not rewrite history. Each entry has a date and a status
(`fixed`, `assumption`, `open`). Blueprint = `docs/PROJECT_BLUEPRINT.md` (v2.0-lean).

Last updated: 2026-11-12 (Milestone 0, Discovery).

## 1. Fixed decisions (from blueprint and CLAUDE.md)

| ID | Decision | Source |
|---|---|---|
| D-01 | Universe: NVDA, AAPL, MSFT, GOOGL, AMZN, META (USD) and BBCA.JK, BBRI.JK, BMRI.JK, BBNI.JK, BBTN.JK (IDR). List lives in `configs/assets.yaml`. | Blueprint 2 |
| D-02 | Primary target: official Q1 2027 calendar-quarter **price return**, `close[last session of Q1 2027] / close[last session of 2026] - 1`, local currency. | Blueprint 3.1 |
| D-03 | Prices: split-adjusted, not dividend-adjusted. yfinance `auto_adjust=False`, `Close` column. To be verified on a known split per market in Milestone 1. | Blueprint 3.1, CLAUDE.md rule 8 |
| D-04 | Secondary targets: forward price return over 5, 20, 60 sessions; forward realised volatility over 20 and 60 sessions. | Blueprint 3.2 |
| D-05 | Models, in order: zero return, historical mean, Ridge, LightGBM. Nothing else. | Blueprint 8 |
| D-06 | Walk-forward: expanding window, yearly test blocks, embargo of `h` sessions, overlapping training labels dropped, transformations fit on the training window only. | Blueprint 8 |
| D-07 | Primary metric: pooled out-of-sample R² against the historical-mean baseline on non-overlapping quarter-end origins. | Blueprint 8 |
| D-08 | Selection rule: a model replaces the baseline only if pooled `R2_oos > 0` and it beats the baseline in more than half of the test years. Otherwise the baseline is published. | Blueprint 8 |
| D-09 | 80% prediction intervals from empirical quantiles of walk-forward out-of-sample residuals. Never called "confidence". | Blueprint 8 |
| D-10 | Forecast ledger is append-only (SQLite). A forecast made after the origin is a different target type. | Blueprint 3.3 |
| D-11 | Storage: Parquet for data and features, SQLite for ledger and run log. | Blueprint 5 |
| D-12 | Out of scope: PostgreSQL, FastAPI, MLflow, Docker, deep learning, ARIMA, ensembles, backtesting, portfolio analytics, live trading, paid data. | Blueprint 10 |
| D-13 | Each exchange uses its own trading calendar; no forward-filling of prices across non-trading days. | CLAUDE.md rules 7, 9 |

## 2. Confirmed in Milestone 0

### 2.1 Target dates

| Exchange | Last session of 2026 (target start) | First session of 2027 | Last session of Q1 2027 (target end) | Sessions in Q1 2027 |
|---|---|---|---|---|
| NYSE / Nasdaq | Thu 2026-12-31 (full day) | Mon 2027-01-04 | Wed 2027-03-31 (full day) | 60 |
| IDX | Wed 2026-12-30 | Mon 2027-01-04 | Wed 2027-03-31 | 53 |

The start dates differ between the two markets (IDX closes one day earlier). The
forecast origin is therefore per exchange.

**US evidence.** NYSE "Holidays & Trading Hours" page (read 2026-11-12):
<https://www.nyse.com/markets/hours-calendars>. 2026 holidays end with Christmas
Day, Fri 25 Dec; early close Thu 24 Dec. 31 Dec 2026 is not listed as a holiday or
early close. 2027: New Year's Day Fri 1 Jan, MLK Mon 18 Jan, Washington's Birthday
Mon 15 Feb, Good Friday Fri 26 Mar. No early close in Q1 2027. Nasdaq follows the
same holiday schedule; the Nasdaq page timed out and was not read directly.

**IDX evidence.**
- 2027: IDX announcement No. Peng-00169/BEI.POP/09-2026, dated 16 Sep 2026, based
  on SKB 3 Menteri No. 1205/3/2 Tahun 2026. Q1 holidays: Fri 1 Jan, Tue 5 Jan
  (Isra Mikraj), Fri 5 Feb (cuti bersama Imlek), Mon 8 Mar (Nyepi), Tue 9 Mar to
  Fri 12 Mar and Mon 15 Mar (Idul Fitri and cuti bersama), Thu 25 Mar (cuti
  bersama) and Fri 26 Mar (Wafat Yesus Kristus). 29, 30 and 31 March are not
  listed. Cross-check: 23 weekdays in March minus 8 holidays = 15, which matches
  the "15 hari bursa" reported for March; 261 weekdays minus 20 listed holidays =
  241, which matches the announced total.
- 2026: IDX announcement No. Peng-00171/BEI.POP/09-2025. December holidays: Thu
  24 Dec (cuti bersama Natal), Fri 25 Dec (Natal), Thu 31 Dec (Libur Bursa). 28,
  29 and 30 Dec are not listed.
- **Caveat:** idx.co.id returned HTTP 403 to automated fetches, so the two PDFs
  were not read directly. The dates above come from idxchannel.com and
  fortuneidn.com articles quoting the announcement, plus the arithmetic
  cross-check. See open question Q-03.
  - <https://www.idx.co.id/StaticData/NewsAndAnnouncement/ANNOUNCEMENTSTOCK/Exchange/Libur%20Bursa%20Peng-00169%20ID-No.%20Peng-00169BEI.POP09-2026.pdf>
  - <https://idx.co.id/StaticData/NewsAndAnnouncement/ANNOUNCEMENTSTOCK/Exchange/Peng-00171%20Libur%20Bursa%202026-No.%20Peng-00171BEI.POP09-2025.pdf>
  - <https://www.idxchannel.com/market-news/dear-investor-ini-kalender-libur-bursa-efek-indonesia-2027>
  - <https://www.fortuneidn.com/market/kalender-libur-bei-2027-d7w02-00-yyq45-qs381g>
- Both IDX announcements state the calendar can change if Bank Indonesia's
  clearing calendar or government holidays change. Re-check before the freeze.

### 2.2 Environment (2026-11-12)

| Item | Finding |
|---|---|
| OS / hardware | macOS 27.0 (build 26A428), Apple M4 (arm64), 16 GB RAM |
| Disk | **about 4 GB free** on the data volume (reported 100% used) |
| Git | 2.49.0; repo initialised, branch `master`, no commits before Milestone 0; `user.name` and `user.email` set |
| Python | 3.11.14 (Homebrew, `python3.11` on PATH); 3.12.16 (uv-managed, not on PATH); 3.14.3 is the default `python3`; system 3.9.6 |
| Tools | Homebrew, uv 0.13.7, gh, make, Xcode Command Line Tools. Not installed: ruff, pyenv, conda, libomp |
| SQLite | 3.53.x bundled with both Pythons |

### 2.3 Dependency resolution (dry run, nothing installed)

`uv pip compile` for `aarch64-apple-darwin`, binary wheels only. All blueprint
section 5 packages resolve for both 3.11 and 3.12:

| Package | Resolved | Needed from |
|---|---|---|
| pandas | 3.1.1 | M1 |
| numpy | 2.4.6 (py3.11) / 2.5.4 (py3.12) | M1 |
| pyarrow | 26.0.1 | M1 |
| yfinance | 1.8.0 | M1 |
| exchange-calendars | 4.13.2 | M1 |
| pandas-market-calendars | 5.6.0 | alternative to the above |
| pyyaml | 6.0.3 | M1 (configs) |
| pytest | 9.2.0 | M1 |
| ruff | 0.17.4 | M1 |
| scikit-learn | 1.9.1 | M3 |
| lightgbm | 4.7.0 | M3 |
| streamlit | 1.67.0 | M5 (optional) |

Resolution proves wheels exist and metadata is compatible. It does not prove
runtime behaviour; that is tested when each package is first used.

## 3. Assumptions (hold unless the user says otherwise)

| ID | Assumption |
|---|---|
| A-01 | `docs/PROJECT_BLUEPRINT.md` is the v2.0-lean file found in `~/Downloads`. It was copied in unchanged because the repo only held the superseded v1.0 document. See Q-01. |
| A-02 | Python 3.12 in a project-local `.venv` created with uv. See Q-02. |
| A-03 | yfinance is used for personal prototyping only; every report says the data is unofficial. |
| A-04 | Both target endpoints are full sessions, so the regular closing price is used. No half-day handling is needed for the Q1 2027 target. |
| A-05 | Dependencies are added per milestone. Milestone 1 installs only pandas, numpy, pyarrow, yfinance, pyyaml, one calendar library, pytest and ruff. |
| A-06 | pandas 3.x is a recent major version. If yfinance or the calendar library misbehaves on it, pin pandas to the 2.x line and record it here. |

## 4. Open questions (need a user decision)

| ID | Question | Recommendation |
|---|---|---|
| Q-01 | The repo had only the v1.0 blueprint (`docs/AstraQuant_Project_Blueprint_and_Claude_Code_Prompt.md`), which contradicts CLAUDE.md. v2.0-lean was copied from `~/Downloads`. Is that the right file, and what happens to v1.0? | Confirm v2.0-lean. Keep v1.0 out of Git (it is left untracked) or delete it. |
| Q-02 | Python 3.12 (uv) or 3.11 (Homebrew)? | 3.12: longer support, everything resolves. |
| Q-03 | Please open the two IDX PDFs (2.1) and confirm 30 Dec 2026 and 31 Mar 2027 are trading days. | Needed before the dates are treated as official. |
| Q-04 | Confirm blueprint section 3: price return, and quarter boundaries as in 2.1 (IDX starts from 30 Dec, US from 31 Dec). | Confirm as written. |
| Q-05 | Calendar library: `exchange_calendars` (XNYS, XIDX) or `pandas_market_calendars`? | `exchange_calendars`, plus an official IDX holiday list for 2026 and 2027 held in `configs/` and a test that pins the four dates in 2.1. Library IDX holidays are not trusted without that check. |
| Q-06 | History start date for ingestion? META listed in May 2012. | 2010-01-01, set in `configs/settings.yaml`; shorter histories are flagged, not padded. |
| Q-07 | Ingest context series (S&P 500 `^GSPC`, IHSG `^JKSE`, USD/IDR `IDR=X`) in Milestone 1 or wait for Milestone 2? | Milestone 1, so data quality is checked once for everything. |
| Q-08 | Disk has about 4 GB free. The virtualenv plus caches need roughly 1 GB. | Free some space before Milestone 1. |
| Q-09 | Branch is `master`; no remote. Rename to `main`? Add a remote? | Rename to `main`; remote is optional. |
| Q-10 | Have you reviewed the yfinance / Yahoo terms for personal prototyping use (blueprint 12)? | User action. |
| Q-11 | Where does the SQLite ledger live? `data/` is gitignored, but the ledger is the frozen deliverable. | Decide in Milestone 4; proposal is `data/ledger/` plus a CSV export of frozen forecasts committed under `reports/`. |
| Q-12 | LightGBM on macOS may need `brew install libomp` (not installed). | Check at Milestone 3; no action now. |

## 5. Milestone 1 (Data), 2026-11-12

### 5.1 Answers to Milestone 0 questions

The user approved the Milestone 1 plan "with the recommendations in DECISIONS.md".

| ID | Outcome |
|---|---|
| Q-01 | v2.0-lean is the blueprint. The v1.0 file stays in `docs/`, untracked; it was not deleted. |
| Q-02 | Python 3.12 via uv. `pyproject.toml` requires `>=3.12,<3.13` with exact pins. |
| Q-03 | **Still open.** The user has not confirmed the two IDX PDFs. Supporting evidence from data: for 1 Jan to 12 Nov 2026 the configured official holiday list matches Yahoo bars exactly (no missing and no unexpected sessions). |
| Q-04 | Accepted as written (price return; IDX from 30 Dec, US from 31 Dec). |
| Q-05 | `exchange_calendars` plus official XIDX holidays for 2026 and 2027 in `configs/settings.yaml`. Tests pin the four target dates and the 60 / 53 session counts. |
| Q-06 | Start date 2010-01-01. META starts 2012-05-18 (its listing); nothing is padded. |
| Q-07 | `^GSPC`, `^JKSE` and `IDR=X` are ingested in Milestone 1. |
| Q-08 | Disk was still about 4 GB free. `.venv` is 267 MB, `data/` about 7 MB. |
| Q-09 | Branch renamed to `main`. No remote. |
| Q-10 | Still a user action (Yahoo terms). |
| Q-11, Q-12 | Unchanged; due at Milestones 4 and 3. |

### 5.2 Decisions made during Milestone 1

| ID | Decision | Reason |
|---|---|---|
| D-14 | The calendar library alone is not used for XIDX. Without overrides it gives 62 sessions in Q1 2027 (official: 53) and 252 in 2026 (official: 239). | Measured; guarded by a test. |
| D-15 | Raw downloads go to `data/raw/yfinance/<UTC run id>/` with a manifest and are never rewritten. Processed Parquet under `data/processed/` is a derived artifact and is replaced on each run. | Blueprint 6. |
| D-16 | Bars for a session that had not closed at retrieval time are dropped (`dropped_incomplete`). The cutoff is the last session whose official close is before the retrieval timestamp; for FX, the last weekday before the UTC date. | A partial bar is not a closing price. |
| D-17 | Zero-volume bars on dates the exchange calendar marks closed are dropped (`dropped_closed_day`). | Yahoo inserts holiday placeholders that repeat the previous close: 53 per IDX bank, all with zero volume and an unchanged close, 2014 to 2019. Keeping them would be a forward-fill across non-trading days (CLAUDE.md rule 7). A bar with volume on a closed day is kept and flagged instead. |
| D-18 | Validation never repairs. Issues are written to `data/processed/quality_issues.parquet` and summarised in `reports/data_quality.md`. `scripts/ingest.py` exits non-zero on any error-level issue or failed split check. | Blueprint 6. |
| D-19 | Price-return semantics verified on NVDA 10:1 (2024-06-10) and BBCA.JK 5:1 (2021-10-13): the split is recorded with the right ratio, `Close` is continuous across it, and `Close` differs from `Adj Close` before it. Implied unadjusted prior closes are 1,208.88 USD and 36,600 IDR. | Blueprint 3.1; milestone exit criterion. |
| D-20 | Jump threshold is 25% close-to-close (`validation.max_abs_daily_return`). | IDX auto-rejection limits reach 25 to 35%; lower values would flag ordinary limit moves. |

### 5.3 New open questions

| ID | Question | Recommendation |
|---|---|---|
| Q-13 | Each IDX bank has 22 to 24 zero-volume bars on real sessions. On 21 of those dates all five banks have zero volume and an unchanged close while IHSG moved, so they look like stale provider rows, not true closes (2011 to 2018; a few single-name cases up to 2020). They are currently kept and flagged. | Treat zero-volume bars of target equities as missing (drop in cleaning) before Milestone 2, so no feature or label uses a stale close. |
| Q-14 | Five XIDX sessions the library marks open have no bar for any Indonesian series: 2022-04-29, 2022-05-04, 2022-05-05, 2022-05-06, 2025-08-18. They look like cuti bersama holidays the library does not know. | Add them to `extra_holidays` once you confirm they were exchange holidays. |
| Q-15 | `IDR=X` has two decimal-shift bad ticks (close on 2010-11-01 and 2012-02-07 is one tenth of its neighbours), 518 bars where high/low do not bound open/close, and 11 missing weekdays. | Milestone 2 uses only `close` from this series and excludes the two bad ticks through an explicit, documented exclusion list in config. No silent repair. |
| Q-16 | `exchange_calendars` 4.13.2 triggers a pandas 3.1 deprecation warning (`Series.values` on tz-aware data). Harmless today. | No action; revisit if pandas 4 is ever adopted. |

## 6. Between Milestones 1 and 2, 2026-11-12

### 6.1 User decisions on the Milestone 1 questions

| ID | Decision | Implemented as |
|---|---|---|
| Q-13 | Zero-volume bars of target equities on real sessions are missing data. Horizons are counted in calendar sessions, not rows. A label or feature that touches a missing bar is NaN; nothing is shifted. | `dropped_stale` in cleaning (22 to 24 bars per IDX bank). Targets and features are computed on the full session grid with strict NaN propagation. |
| Q-14 | Add 2022-04-29, 2022-05-04, 2022-05-05, 2022-05-06 and 2025-08-18 to the XIDX holiday list. | `calendars.extra_holidays` in `configs/settings.yaml`. |
| Q-15 | Use only `close` from `IDR=X`; exclude the two bad ticks through an explicit list. | `exclusions` in `configs/settings.yaml` (`dropped_excluded` = 2). Features read only `close` from context series. |
| Q-03 | Still open: the user is checking the two IDX PDFs. | No change. |

### 6.2 IDX calendar reconciliation, 2010 to 2025

Full table: `reports/idx_calendar_reconciliation.md` (script
`scripts/reconcile_idx_calendar.py`, report only, calendar not changed by it).

- After the five Q-14 dates, the configured calendar has 3,884 sessions in 2010 to
  2025 and raw `^JKSE` has 3,885 bars. Every calendar session has a `^JKSE` bar.
- One difference: `^JKSE` has a bar on Fri 2017-12-01, which the calendar marks
  closed. None of the five banks has a traded bar that day, so it looks like a
  provider artifact. It is dropped in cleaning (`dropped_closed_day`).
- Caveat: `^JKSE` from Yahoo is not an official record of trading days. Agreement
  between the library and Yahoo is not proof that both are right.

### 6.3 Rights issues: Yahoo does adjust for them, without recording an event

The instruction was to record that Yahoo does not adjust for rights issues. The
data shows the opposite, so this entry records what was found.

Evidence. IDX prices are whole rupiah, and split-adjusted prices of these banks
are multiples of 0.25. In the Yahoo `Close` series every bar before a certain
date is a non-tick decimal (for example BBRI 3,554.4841 on 2021-09-07), and
volume before that date is not a round number either. From that date on, all
closes are whole numbers. The switch dates are:

| Bank | First unadjusted bar | Share of history that is fractional | Yahoo close-to-close return on that day | Known rights issue |
|---|---|---|---|---|
| BBNI.JK | 2010-12-03 | 5.6% | +14.0% | December 2010, exercise price Rp3,100 (press; exact ex-date not found) |
| BMRI.JK | 2011-02-08 | 6.6% | +0.9% | February 2011 (press; price and exact ex-date not found) |
| BBRI.JK | 2021-09-08 | 69.4% | +4.9% | Ex-date 2021-09-08 regular market, Rp3,400, about 23 new per 100 old (KSEI) |
| BBTN.JK | 2022-12-23 | 77.3% | +7.8% | Ex-date 2022-12-23 regular market, Rp1,200, 32,525,443 new per 100,000,000 old (press) |
| BBCA.JK | none | 0.0% | n/a | none since 2010 |

A BBTN rights issue in late 2012 is also believed to exist (from memory, not
found in the search); it cannot be seen separately because all BBTN bars before
2022-12-23 are already fractional.

Conclusions that the data supports:

1. Yahoo back-adjusts `Close` (and volume) before each rights ex-date by an
   undocumented factor. The `Stock Splits` column records nothing on those dates.
2. The factor looks wrong for at least BBTN 2022. Press reports put the cum-date
   price (2022-12-22) at about Rp1,400; Yahoo shows 1,248.21, a factor of about
   0.89. The theoretical ex-rights factor from the published terms is about 0.965.
   Yahoo therefore shows +7.8% on the ex-date where the unadjusted move was about
   -3.9% and a correctly adjusted move would be near -0.4%. The Rp1,400 figure is
   from one press report and was not verified against official data.
3. The +14.0% on BBNI 2010-12-03 and +4.9% on BBRI 2021-09-08 fall on the same
   kind of date and are suspect for the same reason, but there is no official
   price here to prove it.

What is not known: the true closes on those dates, the factor Yahoo used, and
whether earlier history contains further hidden adjustments.

Sources: <https://www.ksei.co.id/Announcement/Files/BBRI_RIGHT_20210909_ID.pdf>,
<https://finansial.bisnis.com/read/20210831/90/1435986/harga-pelaksanaan-ditetapkan-rp3400-ini-jadwal-lengkap-rights-issue-bbri>,
<https://finansial.bisnis.com/read/20221215/90/1609081/harga-rights-issue-btn-bbtn-rp1200-target-dana-rp413-triliun>,
<https://market.bisnis.com/read/20221222/7/1611159/hari-ini-cum-date-rights-issue-saham-bbtn-masih-terdiskon>,
<https://keuangan.kontan.co.id/news/investor-kakap-lokal-minati-rights-issue-bbni-1>,
<https://market.bisnis.com/read/20110121/190/17732/ihsg-turun-tajam-rights-issue-bank-mandiri-tetap-jalan-terus>.

### 6.4 Open question from 6.3

| ID | Question | Recommendation |
|---|---|---|
| Q-17 | Four ex-date returns in the Indonesian data are distorted by Yahoo's hidden rights adjustment. They enter the quarterly labels for BBNI Q4 2010, BMRI Q1 2011, BBRI Q3 2021 and BBTN Q4 2022, any 5/20/60-session label spanning those dates, and trailing features for up to 250 sessions after. Nothing has been changed in the data. | Decide before Milestone 3. Options: (a) keep as is and state the limitation; (b) set labels and features that span the four dates to NaN through a config list, consistent with the Q-13 rule; (c) rebuild the true series from official cum-date closes, which needs IDX data this project does not have. Recommendation: (b). |

## 7. Milestone 2 (Targets and features), 2026-11-12

### 7.1 Decisions

All of these were fixed before any model was run. The dataset report shows
availability only, no target statistics.

| ID | Decision | Reason |
|---|---|---|
| D-21 | Targets and features are computed on the full session grid of each exchange (one row per session, NaN where there is no bar). Windows and horizons are positions on that grid. A value that touches a missing bar is NaN. | User decision Q-13. |
| D-22 | Daily forward targets: price return over 5, 20, 60 sessions; realised volatility over 20 and 60 sessions = sample std of daily log returns over sessions `t+1..t+h`, times sqrt(252). 252 is used for both markets. | Blueprint 3.2. One annualisation constant keeps the two markets comparable; IDX has about 240 sessions a year, so IDX volatility is overstated by about 2% relative to a 240 convention. |
| D-23 | Quarterly table: one row per asset per calendar quarter. Origin = `target_start_date` = last session of the previous quarter; `target_end_date` = last session of the quarter; both from the exchange calendar. `q_return` is NaN until the end session has a bar. Features are those of the origin session. | Blueprint 3.1 and 8. |
| D-24 | Feature set `v1` (19 columns plus `is_id`): `ret_{5,20,60,120,250}`, `rvol_{20,60,120}`, `ma_dist_{50,200}`, `rsi_14`, `drawdown_250`, `rel_volume_20_120`, `mkt_ret_{20,60}`, `mkt_rvol_{20,60}`, `fx_ret_{20,60}`. | Blueprint 7. The blueprint gives no windows for index and FX features; 20 and 60 sessions were chosen to match the secondary horizons. |
| D-25 | RSI uses simple averages (Cutler), not Wilder's smoothing. | Wilder's form has infinite memory, so one missing bar would affect every later value and D-21 could not be applied. |
| D-26 | USD/IDR is lagged one business day: an IDX origin on day D reads the `IDR=X` bar dated D-1. Lookup is by exact date; a missing FX bar gives NaN, not an older value. | A Yahoo FX bar dated D closes at the end of the UTC day, after the IDX close on D. Using it would be look-ahead. |
| D-27 | Index features use the index bar of the same session (`^GSPC` for US, `^JKSE` for Indonesia). FX features are NaN for US names. | Same exchange, same close. |
| D-28 | No scaler, imputer or other fitted transformation is applied when building the dataset. | CLAUDE.md rule 3; fitting belongs inside the walk-forward training window. |
| D-29 | Tests use a synthetic panel on the real calendars plus two real excerpts in `tests/fixtures/` (NVDA and BBCA.JK around their splits). No test is skipped in a clean clone. | User request. |

### 7.2 Leakage tests

`tests/leakage/test_no_lookahead.py`:

- Features up to a cut date are bit-for-bit identical after every value after the
  cut is replaced in every series, and identical to features built from data
  truncated at the cut.
- Quarterly features and the start price are unchanged when everything after the
  origin is replaced, while the label does change.
- The FX bar dated on the origin is not used.
- Forward targets depend only on their own window.
- Removing one bar leaves the session grid and target dates unchanged, blanks
  exactly the values whose window includes it, and leaves neighbours untouched.

Three deliberate leaks were injected to confirm the tests fail when they should:
a centred volatility window (3 tests failed), FX lag set to zero (1 failed), and
forward-filling the session grid (1 failed).

### 7.3 Coverage found (ingest run 20261112T152754Z)

| | US | Indonesia |
|---|---|---|
| Quarterly rows with a realised label | 387 | 330 |
| Of those, with every feature available at the origin | 368 | 173 |
| Of those, if only features with windows up to 60 sessions were required | 386 | 281 |

- No ended quarter lost its label: every quarter-boundary session has a bar.
- The Indonesian loss comes from D-21 combined with long windows. A single missing
  bar blanks `drawdown_250` for 250 sessions and `ma_dist_200` for 200. Indonesian
  usable rows per year: 0 in 2012 and 2013, 2 to 5 in 2016 to 2019, 20 from 2022.
- US rows are lost only in the first 250 sessions of each series.

### 7.4 Open questions

| ID | Question | Recommendation |
|---|---|---|
| Q-03 | IDX PDFs for 30 Dec 2026 and 31 Mar 2027: still with the user. | Unchanged. |
| Q-17 | Yahoo's hidden rights adjustment (section 6.3). The four affected quarterly labels are in the dataset, unchanged. | Decide before Milestone 3; recommendation (b) in 6.4. |
| Q-18 | Under the strict NaN rule only 173 of 330 Indonesian quarterly rows have a complete feature vector, and whole years are empty. Ridge cannot use rows with NaN; LightGBM can. This must be settled before any result is seen, because it changes the training sample. | Options: (a) keep strict and let each model use what it can, which gives Ridge and LightGBM different samples; (b) keep strict and require complete rows for all models, which drops about half of Indonesia; (c) allow a small tolerance for long windows, for example at most 2% missing bars inside a window of 120 sessions or more, computed on available bars; (d) drop the 200- and 250-session features. Recommendation: (c), with the tolerance fixed in config now and the strict rule kept for labels and for windows up to 60. |
| Q-19 | FX features are NaN for all US rows by design. A pooled Ridge needs a rule for them. | Decide in the Milestone 3 plan: set them to zero for US rows after scaling (the `is_id` indicator already separates the markets). No result depends on it yet. |
| Q-20 | `rvol_*` targets and features use 252 for both markets (D-22). | Keep, unless you prefer per-market constants. |
