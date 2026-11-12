# Walk-forward evaluation

- Run 2026-11-12T16:54:04.972571+00:00 on dataset build 2026-11-12T15:37:24.341203+00:00 (feature set `v2`).
- Source: yfinance. **Unofficial data, prototyping only.**
- Git commit: `bc3fd777ac7d6e8a7af5801e5bb4dfc945e802d2`
- Config digest: `eae98d0a87583711`; seed 20261112.
- Data through: ID 2026-11-12, US 2026-11-11
- Protocol: expanding window, yearly test blocks, training labels fully realised before the test block, scaling and tuning inside the training window only (blueprint section 8; details in `docs/DECISIONS.md` section 8).

## Result on the primary target

**No model beats the baseline. Selected: `historical_mean` (the baseline).**

The rule: a model replaces the baseline only if pooled `R2_oos > 0` and it beats the baseline in more than half of the test years. It was fixed before any model was run and applied here without adjustment.

## Limitations

- The 11 names were chosen with hindsight; results carry selection bias and do not generalise to stocks in general.
- The sample is small: about four quarterly observations per stock per year, and the names are highly correlated. Yearly comparisons rest on a handful of rows.
- Prices come from Yahoo Finance through yfinance, an unofficial source. Yahoo applies unrecorded adjustments at Indonesian rights-issue dates (`docs/DECISIONS.md` 6.3).
- Six targets are evaluated. Only the quarterly target decides the published model; a good result on one secondary target may be chance.
- These are prediction intervals from past forecast errors. They assume future errors resemble past ones.

## `q_return` (primary target, decides the published model)

Test rows: 408; test years: 11; `R2_oos` is measured against `historical_mean`.

**No model beats the baseline. Selected: `historical_mean` (the baseline).**

Selection rule checks:

| model | pooled_r2_oos | r2_above_zero | years_beating_baseline | test_years | beats_in_more_than_half | qualifies |
|---|---|---|---|---|---|---|
| ridge | -0.0305 | no | 4 | 11 | no | no |
| lightgbm | -0.1017 | no | 3 | 11 | no | no |

Pooled metrics:

| model | n | r2_oos | mae | rmse | directional_accuracy | r2_vs_zero |
|---|---|---|---|---|---|---|
| zero | 408 | -0.1046 | 0.1411 | 0.1899 | n/a | 0.0000 |
| historical_mean | 408 | 0.0000 | 0.1339 | 0.1807 | 63.7% | 0.0947 |
| ridge | 408 | -0.0305 | 0.1350 | 0.1835 | 63.7% | 0.0670 |
| lightgbm | 408 | -0.1017 | 0.1402 | 0.1897 | 61.2% | 0.0026 |

By test year (sum of squared errors; `beats` = lower than the baseline):

| test_year | n | sse_historical_mean | sse_zero | beats_zero | sse_ridge | beats_ridge | sse_lightgbm | beats_lightgbm |
|---|---|---|---|---|---|---|---|---|
| 2016 | 29 | 0.9371 | 0.9998 | no | 0.8854 | yes | 0.9934 | no |
| 2017 | 30 | 0.3539 | 0.6914 | no | 0.3532 | yes | 0.4206 | no |
| 2018 | 34 | 1.3996 | 1.1297 | yes | 1.3976 | yes | 1.3716 | yes |
| 2019 | 29 | 0.4234 | 0.7369 | no | 0.4285 | no | 0.4584 | no |
| 2020 | 41 | 2.7001 | 3.0393 | no | 2.3226 | yes | 2.5372 | yes |
| 2021 | 40 | 0.7506 | 1.0111 | no | 0.9313 | no | 1.0189 | no |
| 2022 | 42 | 1.6966 | 1.0974 | yes | 1.9495 | no | 2.4638 | no |
| 2023 | 42 | 1.8054 | 2.4139 | no | 1.8740 | no | 1.8551 | no |
| 2024 | 44 | 1.3946 | 1.7256 | no | 1.5789 | no | 1.7658 | no |
| 2025 | 44 | 1.0941 | 1.1424 | no | 1.1379 | no | 1.1264 | no |
| 2026 | 33 | 0.7710 | 0.7326 | yes | 0.8745 | no | 0.6708 | yes |

By market:

| market | model | n | r2_oos | mae | rmse | directional_accuracy | r2_vs_zero |
|---|---|---|---|---|---|---|---|
| ID | zero | 150 | 0.0402 | 0.1222 | 0.1635 | n/a | 0.0000 |
| ID | historical_mean | 150 | 0.0000 | 0.1238 | 0.1669 | 55.1% | -0.0419 |
| ID | ridge | 150 | -0.0549 | 0.1281 | 0.1714 | 55.1% | -0.0992 |
| ID | lightgbm | 150 | 0.0150 | 0.1250 | 0.1656 | 51.7% | -0.0263 |
| US | zero | 258 | -0.1707 | 0.1521 | 0.2038 | n/a | 0.0000 |
| US | historical_mean | 258 | 0.0000 | 0.1399 | 0.1883 | 68.6% | 0.1458 |
| US | ridge | 258 | -0.0194 | 0.1390 | 0.1901 | 68.6% | 0.1292 |
| US | lightgbm | 258 | -0.1550 | 0.1490 | 0.2024 | 66.7% | 0.0134 |

By ticker:

| symbol | model | n | r2_oos | mae | rmse | directional_accuracy | r2_vs_zero |
|---|---|---|---|---|---|---|---|
| AAPL | zero | 43 | -0.2046 | 0.1381 | 0.1678 | n/a | 0.0000 |
| AAPL | historical_mean | 43 | 0.0000 | 0.1248 | 0.1529 | 69.8% | 0.1698 |
| AAPL | ridge | 43 | 0.0507 | 0.1234 | 0.1490 | 69.8% | 0.2120 |
| AAPL | lightgbm | 43 | -0.1042 | 0.1329 | 0.1607 | 67.4% | 0.0833 |
| AMZN | zero | 43 | -0.1119 | 0.1327 | 0.1622 | n/a | 0.0000 |
| AMZN | historical_mean | 43 | 0.0000 | 0.1217 | 0.1538 | 67.4% | 0.1007 |
| AMZN | ridge | 43 | 0.0001 | 0.1213 | 0.1538 | 67.4% | 0.1008 |
| AMZN | lightgbm | 43 | -0.1981 | 0.1266 | 0.1683 | 69.8% | -0.0775 |
| BBCA.JK | zero | 30 | 0.0932 | 0.0853 | 0.1043 | n/a | 0.0000 |
| BBCA.JK | historical_mean | 30 | 0.0000 | 0.0854 | 0.1095 | 57.1% | -0.1027 |
| BBCA.JK | ridge | 30 | -0.0251 | 0.0843 | 0.1109 | 57.1% | -0.1304 |
| BBCA.JK | lightgbm | 30 | 0.0750 | 0.0876 | 0.1053 | 57.1% | -0.0200 |
| BBNI.JK | zero | 32 | 0.0330 | 0.1338 | 0.1763 | n/a | 0.0000 |
| BBNI.JK | historical_mean | 32 | 0.0000 | 0.1346 | 0.1793 | 53.1% | -0.0341 |
| BBNI.JK | ridge | 32 | -0.0583 | 0.1378 | 0.1844 | 53.1% | -0.0944 |
| BBNI.JK | lightgbm | 32 | -0.0881 | 0.1420 | 0.1870 | 50.0% | -0.1252 |
| BBRI.JK | zero | 29 | 0.1234 | 0.1070 | 0.1403 | n/a | 0.0000 |
| BBRI.JK | historical_mean | 29 | 0.0000 | 0.1147 | 0.1499 | 50.0% | -0.1408 |
| BBRI.JK | ridge | 29 | -0.1027 | 0.1213 | 0.1574 | 50.0% | -0.2579 |
| BBRI.JK | lightgbm | 29 | -0.0281 | 0.1207 | 0.1520 | 50.0% | -0.1728 |
| BBTN.JK | zero | 29 | 0.0136 | 0.1729 | 0.2286 | n/a | 0.0000 |
| BBTN.JK | historical_mean | 29 | 0.0000 | 0.1728 | 0.2302 | 51.7% | -0.0138 |
| BBTN.JK | ridge | 29 | -0.0382 | 0.1817 | 0.2345 | 51.7% | -0.0525 |
| BBTN.JK | lightgbm | 29 | 0.0556 | 0.1676 | 0.2237 | 48.3% | 0.0425 |
| BMRI.JK | zero | 30 | -0.0013 | 0.1124 | 0.1416 | n/a | 0.0000 |
| BMRI.JK | historical_mean | 30 | 0.0000 | 0.1121 | 0.1415 | 63.3% | 0.0013 |
| BMRI.JK | ridge | 30 | -0.0581 | 0.1161 | 0.1455 | 63.3% | -0.0568 |
| BMRI.JK | lightgbm | 30 | 0.0984 | 0.1073 | 0.1343 | 53.3% | 0.0995 |
| GOOGL | zero | 43 | -0.1822 | 0.1215 | 0.1428 | n/a | 0.0000 |
| GOOGL | historical_mean | 43 | 0.0000 | 0.1089 | 0.1313 | 65.1% | 0.1541 |
| GOOGL | ridge | 43 | -0.0153 | 0.1049 | 0.1323 | 65.1% | 0.1412 |
| GOOGL | lightgbm | 43 | -0.3605 | 0.1262 | 0.1532 | 65.1% | -0.1508 |
| META | zero | 43 | -0.0299 | 0.1576 | 0.2105 | n/a | 0.0000 |
| META | historical_mean | 43 | 0.0000 | 0.1593 | 0.2074 | 60.5% | 0.0291 |
| META | ridge | 43 | 0.0017 | 0.1594 | 0.2073 | 60.5% | 0.0307 |
| META | lightgbm | 43 | -0.1358 | 0.1694 | 0.2211 | 53.5% | -0.1027 |
| MSFT | zero | 43 | -0.2012 | 0.1104 | 0.1387 | n/a | 0.0000 |
| MSFT | historical_mean | 43 | 0.0000 | 0.0985 | 0.1265 | 72.1% | 0.1675 |
| MSFT | ridge | 43 | 0.0522 | 0.0960 | 0.1232 | 72.1% | 0.2109 |
| MSFT | lightgbm | 43 | -0.2112 | 0.1109 | 0.1393 | 69.8% | -0.0083 |
| NVDA | zero | 43 | -0.2374 | 0.2526 | 0.3327 | n/a | 0.0000 |
| NVDA | historical_mean | 43 | 0.0000 | 0.2258 | 0.2991 | 76.7% | 0.1918 |
| NVDA | ridge | 43 | -0.0666 | 0.2290 | 0.3089 | 76.7% | 0.1380 |
| NVDA | lightgbm | 43 | -0.1165 | 0.2281 | 0.3160 | 74.4% | 0.0977 |

80% prediction intervals (quantiles of earlier test years' residuals, per market; coverage is out of sample):

| model | market | n | coverage | mean_width |
|---|---|---|---|---|
| zero | US | 210 | 73.3% | 0.3749 |
| zero | ID | 139 | 78.4% | 0.4286 |
| historical_mean | US | 210 | 72.9% | 0.3784 |
| historical_mean | ID | 139 | 78.4% | 0.4384 |
| ridge | US | 210 | 71.0% | 0.3687 |
| ridge | ID | 139 | 77.0% | 0.4427 |
| lightgbm | US | 210 | 74.3% | 0.4226 |
| lightgbm | ID | 139 | 78.4% | 0.4130 |

Folds:

| test_year | train_rows | history_rows | test_rows | train_last_label_end | test_first_origin |
|---|---|---|---|---|---|
| 2016 | 168 | 235 | 29 | 2015-12-30 | 2015-12-30 |
| 2017 | 203 | 285 | 30 | 2016-12-30 | 2016-12-30 |
| 2018 | 233 | 329 | 34 | 2017-12-29 | 2017-12-29 |
| 2019 | 261 | 367 | 29 | 2018-09-28 | 2018-12-31 |
| 2020 | 290 | 411 | 41 | 2019-12-30 | 2019-12-30 |
| 2021 | 331 | 455 | 40 | 2020-12-30 | 2020-12-30 |
| 2022 | 371 | 498 | 42 | 2021-12-30 | 2021-12-30 |
| 2023 | 419 | 547 | 42 | 2022-12-30 | 2022-12-30 |
| 2024 | 461 | 591 | 44 | 2023-12-29 | 2023-12-29 |
| 2025 | 499 | 629 | 44 | 2024-12-30 | 2024-12-30 |
| 2026 | 543 | 673 | 33 | 2025-12-30 | 2025-12-30 |

Hyperparameters chosen inside each training window:

| test_year | params_ridge | params_lightgbm |
|---|---|---|
| 2016 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2017 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2018 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 50} |
| 2019 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 50} |
| 2020 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 150} |
| 2021 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2022 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2023 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2024 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2025 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2026 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 50} |

## `fwd_ret_5` (secondary, information)

Test rows: 5199; test years: 11; `R2_oos` is measured against `historical_mean`.

**No model beats the baseline. Selected: `historical_mean` (the baseline).**

Selection rule checks:

| model | pooled_r2_oos | r2_above_zero | years_beating_baseline | test_years | beats_in_more_than_half | qualifies |
|---|---|---|---|---|---|---|
| ridge | -0.0047 | no | 5 | 11 | no | no |
| lightgbm | -0.0337 | no | 6 | 11 | yes | no |

Pooled metrics:

| model | n | r2_oos | mae | rmse | directional_accuracy | r2_vs_zero |
|---|---|---|---|---|---|---|
| zero | 5199 | -0.0086 | 0.0336 | 0.0472 | n/a | 0.0000 |
| historical_mean | 5199 | 0.0000 | 0.0334 | 0.0470 | 55.2% | 0.0085 |
| ridge | 5199 | -0.0047 | 0.0335 | 0.0471 | 55.0% | 0.0039 |
| lightgbm | 5199 | -0.0337 | 0.0335 | 0.0477 | 56.0% | -0.0249 |

By test year (sum of squared errors; `beats` = lower than the baseline):

| test_year | n | sse_historical_mean | sse_zero | beats_zero | sse_ridge | beats_ridge | sse_lightgbm | beats_lightgbm |
|---|---|---|---|---|---|---|---|---|
| 2016 | 346 | 0.6386 | 0.6505 | no | 0.6362 | yes | 0.6305 | yes |
| 2017 | 413 | 0.4247 | 0.4528 | no | 0.4298 | no | 0.4265 | no |
| 2018 | 365 | 0.6704 | 0.6519 | yes | 0.6882 | no | 0.7471 | no |
| 2019 | 461 | 0.5611 | 0.5830 | no | 0.5494 | yes | 0.5188 | yes |
| 2020 | 504 | 2.0247 | 2.0487 | no | 2.0587 | no | 2.4617 | no |
| 2021 | 538 | 0.8529 | 0.8672 | no | 0.8578 | no | 0.8478 | yes |
| 2022 | 536 | 1.9046 | 1.8652 | yes | 1.9244 | no | 1.8768 | yes |
| 2023 | 518 | 0.8200 | 0.8602 | no | 0.8115 | yes | 0.8211 | no |
| 2024 | 535 | 0.9612 | 0.9845 | no | 0.9694 | no | 0.9728 | no |
| 2025 | 520 | 1.1433 | 1.1457 | no | 1.1366 | yes | 1.1414 | yes |
| 2026 | 463 | 1.4594 | 1.4496 | yes | 1.4527 | yes | 1.4023 | yes |

By market:

| market | model | n | r2_oos | mae | rmse | directional_accuracy | r2_vs_zero |
|---|---|---|---|---|---|---|---|
| ID | zero | 1923 | 0.0018 | 0.0321 | 0.0465 | n/a | 0.0000 |
| ID | historical_mean | 1923 | 0.0000 | 0.0322 | 0.0465 | 50.6% | -0.0018 |
| ID | ridge | 1923 | -0.0120 | 0.0325 | 0.0468 | 50.7% | -0.0138 |
| ID | lightgbm | 1923 | -0.0633 | 0.0325 | 0.0480 | 52.5% | -0.0651 |
| US | zero | 3276 | -0.0145 | 0.0345 | 0.0475 | n/a | 0.0000 |
| US | historical_mean | 3276 | 0.0000 | 0.0341 | 0.0472 | 57.8% | 0.0143 |
| US | ridge | 3276 | -0.0005 | 0.0341 | 0.0472 | 57.4% | 0.0138 |
| US | lightgbm | 3276 | -0.0168 | 0.0341 | 0.0476 | 57.9% | -0.0023 |

80% prediction intervals (quantiles of earlier test years' residuals, per market; coverage is out of sample):

| model | market | n | coverage | mean_width |
|---|---|---|---|---|
| zero | US | 2670 | 73.3% | 0.0941 |
| zero | ID | 1770 | 75.5% | 0.0918 |
| historical_mean | US | 2670 | 72.9% | 0.0940 |
| historical_mean | ID | 1770 | 75.6% | 0.0919 |
| ridge | US | 2670 | 73.1% | 0.0939 |
| ridge | ID | 1770 | 75.6% | 0.0930 |
| lightgbm | US | 2670 | 72.8% | 0.0945 |
| lightgbm | ID | 1770 | 75.4% | 0.0918 |

Folds:

| test_year | train_rows | history_rows | test_rows | train_last_label_end | test_first_origin |
|---|---|---|---|---|---|
| 2016 | 2216 | 3136 | 346 | 2015-12-28 | 2016-01-04 |
| 2017 | 2567 | 3662 | 413 | 2016-12-29 | 2017-01-06 |
| 2018 | 2975 | 4202 | 365 | 2017-12-28 | 2018-01-04 |
| 2019 | 3345 | 4732 | 461 | 2018-12-26 | 2019-01-03 |
| 2020 | 3795 | 5277 | 504 | 2019-12-27 | 2020-01-07 |
| 2021 | 4305 | 5823 | 538 | 2020-12-28 | 2021-01-05 |
| 2022 | 4838 | 6372 | 536 | 2021-12-30 | 2022-01-07 |
| 2023 | 5380 | 6922 | 518 | 2022-12-29 | 2023-01-05 |
| 2024 | 5897 | 7462 | 535 | 2023-12-29 | 2024-01-05 |
| 2025 | 6432 | 7997 | 520 | 2024-12-26 | 2025-01-03 |
| 2026 | 6952 | 8532 | 463 | 2025-12-26 | 2026-01-05 |

Hyperparameters chosen inside each training window:

| test_year | params_ridge | params_lightgbm |
|---|---|---|
| 2016 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2017 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2018 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2019 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2020 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2021 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2022 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2023 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2024 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2025 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2026 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |

## `fwd_ret_20` (secondary, information)

Test rows: 1300; test years: 11; `R2_oos` is measured against `historical_mean`.

**No model beats the baseline. Selected: `historical_mean` (the baseline).**

Selection rule checks:

| model | pooled_r2_oos | r2_above_zero | years_beating_baseline | test_years | beats_in_more_than_half | qualifies |
|---|---|---|---|---|---|---|
| ridge | -0.0222 | no | 3 | 11 | no | no |
| lightgbm | 0.0127 | yes | 5 | 11 | no | no |

Pooled metrics:

| model | n | r2_oos | mae | rmse | directional_accuracy | r2_vs_zero |
|---|---|---|---|---|---|---|
| zero | 1300 | -0.0334 | 0.0706 | 0.0947 | n/a | 0.0000 |
| historical_mean | 1300 | 0.0000 | 0.0688 | 0.0931 | 59.4% | 0.0323 |
| ridge | 1300 | -0.0222 | 0.0692 | 0.0942 | 59.7% | 0.0109 |
| lightgbm | 1300 | 0.0127 | 0.0686 | 0.0925 | 59.4% | 0.0446 |

By test year (sum of squared errors; `beats` = lower than the baseline):

| test_year | n | sse_historical_mean | sse_zero | beats_zero | sse_ridge | beats_ridge | sse_lightgbm | beats_lightgbm |
|---|---|---|---|---|---|---|---|---|
| 2016 | 88 | 0.5696 | 0.6508 | no | 0.5609 | yes | 0.5667 | yes |
| 2017 | 104 | 0.4254 | 0.5419 | no | 0.4276 | no | 0.4169 | yes |
| 2018 | 98 | 0.8355 | 0.7653 | yes | 0.8264 | yes | 0.8607 | no |
| 2019 | 107 | 0.5346 | 0.5794 | no | 0.5333 | yes | 0.5404 | no |
| 2020 | 129 | 2.4760 | 2.5733 | no | 2.5789 | no | 2.2659 | yes |
| 2021 | 138 | 1.1555 | 1.2035 | no | 1.1561 | no | 1.1137 | yes |
| 2022 | 129 | 1.3829 | 1.2451 | yes | 1.4958 | no | 1.4370 | no |
| 2023 | 132 | 0.8165 | 1.0017 | no | 0.8332 | no | 0.8550 | no |
| 2024 | 132 | 0.8560 | 0.9057 | no | 0.8825 | no | 0.7881 | yes |
| 2025 | 138 | 0.8998 | 0.9109 | no | 0.9008 | no | 0.9430 | no |
| 2026 | 105 | 1.3236 | 1.2740 | yes | 1.3299 | no | 1.3450 | no |

By market:

| market | model | n | r2_oos | mae | rmse | directional_accuracy | r2_vs_zero |
|---|---|---|---|---|---|---|---|
| ID | zero | 484 | 0.0164 | 0.0675 | 0.0936 | n/a | 0.0000 |
| ID | historical_mean | 484 | 0.0000 | 0.0679 | 0.0944 | 52.7% | -0.0167 |
| ID | ridge | 484 | -0.0365 | 0.0684 | 0.0961 | 53.6% | -0.0538 |
| ID | lightgbm | 484 | 0.0101 | 0.0682 | 0.0939 | 52.1% | -0.0064 |
| US | zero | 816 | -0.0642 | 0.0725 | 0.0953 | n/a | 0.0000 |
| US | historical_mean | 816 | 0.0000 | 0.0692 | 0.0924 | 63.2% | 0.0603 |
| US | ridge | 816 | -0.0133 | 0.0697 | 0.0930 | 63.2% | 0.0478 |
| US | lightgbm | 816 | 0.0143 | 0.0689 | 0.0917 | 63.7% | 0.0737 |

80% prediction intervals (quantiles of earlier test years' residuals, per market; coverage is out of sample):

| model | market | n | coverage | mean_width |
|---|---|---|---|---|
| zero | US | 666 | 72.5% | 0.1903 |
| zero | ID | 442 | 76.0% | 0.1962 |
| historical_mean | US | 666 | 73.3% | 0.1935 |
| historical_mean | ID | 442 | 76.2% | 0.1971 |
| ridge | US | 666 | 73.1% | 0.1932 |
| ridge | ID | 442 | 76.0% | 0.1987 |
| lightgbm | US | 666 | 73.0% | 0.1932 |
| lightgbm | ID | 442 | 75.1% | 0.1967 |

Folds:

| test_year | train_rows | history_rows | test_rows | train_last_label_end | test_first_origin |
|---|---|---|---|---|---|
| 2016 | 537 | 770 | 88 | 2015-12-17 | 2016-01-19 |
| 2017 | 630 | 898 | 104 | 2016-12-29 | 2017-01-30 |
| 2018 | 729 | 1030 | 98 | 2017-12-12 | 2018-01-11 |
| 2019 | 832 | 1168 | 107 | 2018-12-26 | 2019-01-25 |
| 2020 | 934 | 1300 | 129 | 2019-12-09 | 2020-01-07 |
| 2021 | 1063 | 1438 | 138 | 2020-12-18 | 2021-01-05 |
| 2022 | 1196 | 1574 | 129 | 2021-12-23 | 2022-01-21 |
| 2023 | 1331 | 1712 | 132 | 2022-12-15 | 2023-01-12 |
| 2024 | 1462 | 1849 | 132 | 2023-12-28 | 2024-01-15 |
| 2025 | 1594 | 1981 | 138 | 2024-12-17 | 2025-01-13 |
| 2026 | 1732 | 2119 | 105 | 2025-12-26 | 2026-01-27 |

Hyperparameters chosen inside each training window:

| test_year | params_ridge | params_lightgbm |
|---|---|---|
| 2016 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2017 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2018 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2019 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2020 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2021 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 50} |
| 2022 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2023 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2024 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2025 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2026 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |

## `fwd_ret_60` (secondary, information)

Test rows: 421; test years: 11; `R2_oos` is measured against `historical_mean`.

**No model beats the baseline. Selected: `historical_mean` (the baseline).**

Selection rule checks:

| model | pooled_r2_oos | r2_above_zero | years_beating_baseline | test_years | beats_in_more_than_half | qualifies |
|---|---|---|---|---|---|---|
| ridge | -0.0311 | no | 6 | 11 | yes | no |
| lightgbm | -0.1492 | no | 3 | 11 | no | no |

Pooled metrics:

| model | n | r2_oos | mae | rmse | directional_accuracy | r2_vs_zero |
|---|---|---|---|---|---|---|
| zero | 421 | -0.0997 | 0.1308 | 0.1722 | n/a | 0.0000 |
| historical_mean | 421 | 0.0000 | 0.1262 | 0.1642 | 61.0% | 0.0907 |
| ridge | 421 | -0.0311 | 0.1282 | 0.1667 | 61.3% | 0.0624 |
| lightgbm | 421 | -0.1492 | 0.1357 | 0.1760 | 57.0% | -0.0450 |

By test year (sum of squared errors; `beats` = lower than the baseline):

| test_year | n | sse_historical_mean | sse_zero | beats_zero | sse_ridge | beats_ridge | sse_lightgbm | beats_lightgbm |
|---|---|---|---|---|---|---|---|---|
| 2016 | 29 | 0.7425 | 0.8627 | no | 0.7188 | yes | 0.6991 | yes |
| 2017 | 35 | 0.3948 | 0.7110 | no | 0.4363 | no | 0.4427 | no |
| 2018 | 29 | 0.6937 | 0.4805 | yes | 0.6916 | yes | 0.6389 | yes |
| 2019 | 34 | 0.5054 | 0.6771 | no | 0.4158 | yes | 0.4842 | yes |
| 2020 | 47 | 2.6693 | 2.9337 | no | 2.4790 | yes | 2.7261 | no |
| 2021 | 42 | 1.3607 | 1.4813 | no | 1.4300 | no | 1.5845 | no |
| 2022 | 42 | 1.4644 | 1.2588 | yes | 1.5970 | no | 1.7772 | no |
| 2023 | 42 | 1.1121 | 1.5901 | no | 1.0515 | yes | 1.2580 | no |
| 2024 | 44 | 0.8023 | 0.9548 | no | 0.8989 | no | 0.8039 | no |
| 2025 | 50 | 1.0192 | 0.9429 | yes | 1.0034 | yes | 1.7246 | no |
| 2026 | 27 | 0.5848 | 0.5879 | no | 0.9795 | no | 0.9034 | no |

By market:

| market | model | n | r2_oos | mae | rmse | directional_accuracy | r2_vs_zero |
|---|---|---|---|---|---|---|---|
| ID | zero | 157 | 0.0735 | 0.1139 | 0.1481 | n/a | 0.0000 |
| ID | historical_mean | 157 | 0.0000 | 0.1173 | 0.1539 | 48.4% | -0.0793 |
| ID | ridge | 157 | -0.1209 | 0.1269 | 0.1629 | 49.7% | -0.2098 |
| ID | lightgbm | 157 | -0.2017 | 0.1325 | 0.1687 | 45.2% | -0.2970 |
| US | zero | 264 | -0.1841 | 0.1409 | 0.1850 | n/a | 0.0000 |
| US | historical_mean | 264 | 0.0000 | 0.1315 | 0.1700 | 68.6% | 0.1555 |
| US | ridge | 264 | 0.0127 | 0.1290 | 0.1689 | 68.2% | 0.1662 |
| US | lightgbm | 264 | -0.1237 | 0.1377 | 0.1802 | 64.0% | 0.0510 |

80% prediction intervals (quantiles of earlier test years' residuals, per market; coverage is out of sample):

| model | market | n | coverage | mean_width |
|---|---|---|---|---|
| zero | US | 216 | 71.8% | 0.3730 |
| zero | ID | 141 | 82.3% | 0.3801 |
| historical_mean | US | 216 | 71.8% | 0.3681 |
| historical_mean | ID | 141 | 83.0% | 0.3838 |
| ridge | US | 216 | 70.8% | 0.3671 |
| ridge | ID | 141 | 81.6% | 0.3936 |
| lightgbm | US | 216 | 68.1% | 0.3773 |
| lightgbm | ID | 141 | 82.3% | 0.3907 |

Folds:

| test_year | train_rows | history_rows | test_rows | train_last_label_end | test_first_origin |
|---|---|---|---|---|---|
| 2016 | 160 | 245 | 29 | 2015-12-17 | 2016-02-18 |
| 2017 | 194 | 289 | 35 | 2016-11-30 | 2017-02-28 |
| 2018 | 224 | 333 | 29 | 2017-11-13 | 2018-02-09 |
| 2019 | 258 | 377 | 34 | 2018-10-26 | 2019-01-25 |
| 2020 | 287 | 421 | 47 | 2019-11-06 | 2020-01-08 |
| 2021 | 334 | 471 | 42 | 2020-12-18 | 2021-02-02 |
| 2022 | 377 | 514 | 42 | 2021-12-02 | 2022-01-21 |
| 2023 | 419 | 558 | 42 | 2022-11-15 | 2023-01-12 |
| 2024 | 460 | 601 | 44 | 2023-10-31 | 2024-01-15 |
| 2025 | 504 | 645 | 50 | 2024-10-21 | 2025-01-13 |
| 2026 | 554 | 695 | 27 | 2025-12-26 | 2026-01-27 |

Hyperparameters chosen inside each training window:

| test_year | params_ridge | params_lightgbm |
|---|---|---|
| 2016 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2017 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2018 | {'alpha': 10.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2019 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 150} |
| 2020 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2021 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2022 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2023 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2024 | {'alpha': 10000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2025 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 50} |
| 2026 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |

## `fwd_vol_20` (secondary, information)

Test rows: 1287; test years: 11; `R2_oos` is measured against `trailing_vol`.

**Selected: `ridge`, replacing the baseline `trailing_vol`.**

Selection rule checks:

| model | pooled_r2_oos | r2_above_zero | years_beating_baseline | test_years | beats_in_more_than_half | qualifies |
|---|---|---|---|---|---|---|
| ridge | 0.3521 | yes | 11 | 11 | yes | yes |
| lightgbm | 0.3260 | yes | 11 | 11 | yes | yes |

Pooled metrics:

| model | n | r2_oos | mae | rmse | directional_accuracy |
|---|---|---|---|---|---|
| trailing_vol | 1287 | 0.0000 | 0.1091 | 0.1563 | 100.0% |
| historical_mean | 1287 | 0.1121 | 0.1034 | 0.1473 | 100.0% |
| ridge | 1287 | 0.3521 | 0.0852 | 0.1258 | 100.0% |
| lightgbm | 1287 | 0.3260 | 0.0863 | 0.1283 | 100.0% |

By test year (sum of squared errors; `beats` = lower than the baseline):

| test_year | n | sse_trailing_vol | sse_historical_mean | beats_historical_mean | sse_ridge | beats_ridge | sse_lightgbm | beats_lightgbm |
|---|---|---|---|---|---|---|---|---|
| 2016 | 83 | 2.1146 | 1.7209 | yes | 1.1942 | yes | 1.4232 | yes |
| 2017 | 104 | 0.9068 | 1.6575 | no | 0.6491 | yes | 0.8030 | yes |
| 2018 | 93 | 2.8798 | 2.1562 | yes | 2.1421 | yes | 2.1650 | yes |
| 2019 | 107 | 1.2341 | 1.0394 | yes | 0.6635 | yes | 0.7397 | yes |
| 2020 | 126 | 7.6864 | 7.1121 | yes | 5.6194 | yes | 5.6519 | yes |
| 2021 | 138 | 1.2817 | 0.9257 | yes | 1.1024 | yes | 0.8702 | yes |
| 2022 | 129 | 4.3209 | 4.8578 | no | 2.5048 | yes | 2.7000 | yes |
| 2023 | 132 | 2.3065 | 2.0056 | yes | 1.2407 | yes | 1.2333 | yes |
| 2024 | 132 | 1.7901 | 1.1609 | yes | 1.2319 | yes | 1.2709 | yes |
| 2025 | 138 | 3.3199 | 2.8061 | yes | 2.1484 | yes | 1.9815 | yes |
| 2026 | 105 | 3.5990 | 2.4722 | yes | 1.8738 | yes | 2.3521 | yes |

By market:

| market | model | n | r2_oos | mae | rmse | directional_accuracy |
|---|---|---|---|---|---|---|
| ID | trailing_vol | 471 | 0.0000 | 0.0917 | 0.1309 | 100.0% |
| ID | historical_mean | 471 | -0.0149 | 0.0965 | 0.1319 | 100.0% |
| ID | ridge | 471 | 0.3379 | 0.0750 | 0.1065 | 100.0% |
| ID | lightgbm | 471 | 0.3244 | 0.0745 | 0.1076 | 100.0% |
| US | trailing_vol | 816 | 0.0000 | 0.1191 | 0.1692 | 100.0% |
| US | historical_mean | 816 | 0.1560 | 0.1074 | 0.1555 | 100.0% |
| US | ridge | 816 | 0.3570 | 0.0910 | 0.1357 | 100.0% |
| US | lightgbm | 816 | 0.3265 | 0.0932 | 0.1389 | 100.0% |

80% prediction intervals (quantiles of earlier test years' residuals, per market; coverage is out of sample):

| model | market | n | coverage | mean_width |
|---|---|---|---|---|
| trailing_vol | US | 666 | 74.8% | 0.3415 |
| trailing_vol | ID | 434 | 74.9% | 0.2638 |
| historical_mean | US | 666 | 80.5% | 0.3214 |
| historical_mean | ID | 434 | 76.5% | 0.2473 |
| ridge | US | 666 | 76.1% | 0.2559 |
| ridge | ID | 434 | 77.6% | 0.2156 |
| lightgbm | US | 666 | 79.1% | 0.2725 |
| lightgbm | ID | 434 | 74.9% | 0.2179 |

Folds:

| test_year | train_rows | history_rows | test_rows | train_last_label_end | test_first_origin |
|---|---|---|---|---|---|
| 2016 | 529 | 744 | 83 | 2015-12-17 | 2016-01-19 |
| 2017 | 617 | 867 | 104 | 2016-12-29 | 2017-01-30 |
| 2018 | 716 | 995 | 93 | 2017-12-12 | 2018-01-11 |
| 2019 | 814 | 1128 | 107 | 2018-12-26 | 2019-01-25 |
| 2020 | 916 | 1260 | 126 | 2019-12-09 | 2020-01-07 |
| 2021 | 1042 | 1395 | 138 | 2020-12-18 | 2021-01-05 |
| 2022 | 1175 | 1531 | 129 | 2021-12-23 | 2022-01-21 |
| 2023 | 1310 | 1669 | 132 | 2022-12-15 | 2023-01-12 |
| 2024 | 1441 | 1806 | 132 | 2023-12-28 | 2024-01-15 |
| 2025 | 1573 | 1938 | 138 | 2024-12-17 | 2025-01-13 |
| 2026 | 1711 | 2076 | 105 | 2025-12-26 | 2026-01-27 |

Hyperparameters chosen inside each training window:

| test_year | params_ridge | params_lightgbm |
|---|---|---|
| 2016 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 50} |
| 2017 | {'alpha': 10.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 50} |
| 2018 | {'alpha': 10.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2019 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2020 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 150} |
| 2021 | {'alpha': 0.1} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2022 | {'alpha': 0.1} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2023 | {'alpha': 0.1} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2024 | {'alpha': 10.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 150} |
| 2025 | {'alpha': 10.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 150} |
| 2026 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 150} |

## `fwd_vol_60` (secondary, information)

Test rows: 408; test years: 11; `R2_oos` is measured against `trailing_vol`.

**Selected: `lightgbm`, replacing the baseline `trailing_vol`.**

Selection rule checks:

| model | pooled_r2_oos | r2_above_zero | years_beating_baseline | test_years | beats_in_more_than_half | qualifies |
|---|---|---|---|---|---|---|
| ridge | 0.1609 | yes | 8 | 11 | yes | yes |
| lightgbm | 0.2196 | yes | 6 | 11 | yes | yes |

Pooled metrics:

| model | n | r2_oos | mae | rmse | directional_accuracy |
|---|---|---|---|---|---|
| trailing_vol | 408 | 0.0000 | 0.0932 | 0.1312 | 100.0% |
| historical_mean | 408 | 0.1362 | 0.0907 | 0.1219 | 100.0% |
| ridge | 408 | 0.1609 | 0.0829 | 0.1202 | 100.0% |
| lightgbm | 408 | 0.2196 | 0.0832 | 0.1159 | 100.0% |

By test year (sum of squared errors; `beats` = lower than the baseline):

| test_year | n | sse_trailing_vol | sse_historical_mean | beats_historical_mean | sse_ridge | beats_ridge | sse_lightgbm | beats_lightgbm |
|---|---|---|---|---|---|---|---|---|
| 2016 | 24 | 0.3054 | 0.3631 | no | 0.2190 | yes | 0.2618 | yes |
| 2017 | 35 | 0.1440 | 0.4109 | no | 0.1400 | yes | 0.1966 | no |
| 2018 | 24 | 0.4255 | 0.3715 | yes | 0.3172 | yes | 0.3028 | yes |
| 2019 | 34 | 0.3982 | 0.1826 | yes | 0.0837 | yes | 0.1271 | yes |
| 2020 | 44 | 2.7270 | 1.7272 | yes | 2.2764 | yes | 1.8022 | yes |
| 2021 | 42 | 0.4411 | 0.3651 | yes | 0.4446 | no | 0.4751 | no |
| 2022 | 42 | 0.3796 | 1.0923 | no | 0.7752 | no | 0.5640 | no |
| 2023 | 42 | 0.2816 | 0.4017 | no | 0.2784 | yes | 0.3020 | no |
| 2024 | 44 | 0.4390 | 0.1909 | yes | 0.2678 | yes | 0.2325 | yes |
| 2025 | 50 | 1.2331 | 0.5997 | yes | 0.7059 | yes | 0.9092 | yes |
| 2026 | 27 | 0.2484 | 0.3615 | no | 0.3850 | no | 0.3072 | no |

By market:

| market | model | n | r2_oos | mae | rmse | directional_accuracy |
|---|---|---|---|---|---|---|
| ID | trailing_vol | 144 | 0.0000 | 0.0867 | 0.1176 | 100.0% |
| ID | historical_mean | 144 | 0.0488 | 0.0880 | 0.1147 | 100.0% |
| ID | ridge | 144 | 0.1710 | 0.0772 | 0.1071 | 100.0% |
| ID | lightgbm | 144 | 0.2537 | 0.0742 | 0.1016 | 100.0% |
| US | trailing_vol | 264 | 0.0000 | 0.0967 | 0.1380 | 100.0% |
| US | historical_mean | 264 | 0.1708 | 0.0921 | 0.1257 | 100.0% |
| US | ridge | 264 | 0.1569 | 0.0860 | 0.1268 | 100.0% |
| US | lightgbm | 264 | 0.2061 | 0.0881 | 0.1230 | 100.0% |

80% prediction intervals (quantiles of earlier test years' residuals, per market; coverage is out of sample):

| model | market | n | coverage | mean_width |
|---|---|---|---|---|
| trailing_vol | US | 216 | 76.4% | 0.2595 |
| trailing_vol | ID | 133 | 65.4% | 0.1991 |
| historical_mean | US | 216 | 73.6% | 0.2688 |
| historical_mean | ID | 133 | 69.2% | 0.2178 |
| ridge | US | 216 | 73.1% | 0.2296 |
| ridge | ID | 133 | 63.2% | 0.1644 |
| lightgbm | US | 216 | 73.6% | 0.2320 |
| lightgbm | ID | 133 | 63.2% | 0.1632 |

Folds:

| test_year | train_rows | history_rows | test_rows | train_last_label_end | test_first_origin |
|---|---|---|---|---|---|
| 2016 | 157 | 225 | 24 | 2015-12-17 | 2016-03-16 |
| 2017 | 186 | 264 | 35 | 2016-11-30 | 2017-02-28 |
| 2018 | 216 | 304 | 24 | 2017-11-13 | 2018-02-09 |
| 2019 | 245 | 343 | 34 | 2018-10-26 | 2019-01-25 |
| 2020 | 274 | 387 | 44 | 2019-11-06 | 2020-01-08 |
| 2021 | 318 | 434 | 42 | 2020-12-18 | 2021-02-02 |
| 2022 | 361 | 477 | 42 | 2021-12-02 | 2022-01-21 |
| 2023 | 403 | 521 | 42 | 2022-11-15 | 2023-01-12 |
| 2024 | 444 | 564 | 44 | 2023-10-31 | 2024-01-15 |
| 2025 | 488 | 608 | 50 | 2024-10-21 | 2025-01-13 |
| 2026 | 538 | 658 | 27 | 2025-12-26 | 2026-01-27 |

Hyperparameters chosen inside each training window:

| test_year | params_ridge | params_lightgbm |
|---|---|---|
| 2016 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 150} |
| 2017 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2018 | {'alpha': 10.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2019 | {'alpha': 10.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2020 | {'alpha': 10.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 150} |
| 2021 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2022 | {'alpha': 1000.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2023 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2024 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 3, 'n_estimators': 150} |
| 2025 | {'alpha': 100.0} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 150} |
| 2026 | {'alpha': 0.1} | {'learning_rate': 0.05, 'min_child_samples': 20, 'colsample_bytree': 0.8, 'reg_lambda': 1.0, 'num_leaves': 7, 'n_estimators': 50} |
