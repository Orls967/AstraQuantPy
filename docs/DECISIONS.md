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
