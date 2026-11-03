# Native descriptive A0–A1 onset comparison

DESCRIPTIVE_ALL constant-pressure runs; descriptive, with no grading changes. The full B0c beverage-mass operator uses each original observation timestamp series on common support. Errors are simulated detector median minus observed median; times are seconds.

| Nominal bar | Observed median | A0 detector error | A1 detector error | A0 sharp front | A1 sharp front |
|---|---|---|---|---|---|
| 1 | 25.058 | ≥+72.820 | ≥+72.820 | 28.905 | ≥100.000 |
| 2 | 13.918 | +2.806 | +11.401 | 14.453 | 22.987 |
| 3.5 | 11.115 | -1.962 | -1.775 | 8.259 | 8.470 |
| 4 | 12.479 | -4.444 | -4.444 | 7.226 | 7.237 |
| 5 | 12.985 | -6.538 | -6.164 | 5.781 | 6.158 |
| 6 | 12.610 | -7.099 | -5.978 | 4.818 | 5.937 |
| 7 | 14.943 | -10.180 | -8.218 | 4.129 | 6.051 |
| 8 | 14.057 | -9.759 | -7.052 | 3.613 | 6.276 |
| 9 | 15.306 | -11.387 | -8.026 | 3.212 | 6.535 |
| 11 | 15.863 | -12.411 | -8.027 | 2.628 | 7.093 |
| 13 | 17.858 | -14.778 | -9.355 | 2.223 | 7.699 |

Onset RMSE lower bounds: **A0 14.414895 s; A1 13.435103 s**. Paired A1−A0 difference: **-0.979793 s [-2.634435, +1.279420]**, conditional on transferred fits. This is a paired difference of computed lower bounds, not a bound or interval on the unknown uncensored RMSE difference. It uses 1,000 identical condition/brew draws, seed 20261103, rather than differences of marginal intervals.

A0: 56/56 available, 51 detected and 5 censored. Censor bounds are 97.866–97.908 s; the median censor bound is 97.878 s. Fastest detector onset on the eleven-point nominal grid: **13 bar**.
A1: 56/56 available, 51 detected and 5 censored. Censor bounds are 97.866–97.908 s; the median censor bound is 97.878 s. Fastest detector onset on the eleven-point nominal grid: **6 bar**.

The observed minimum is nominal 3.5 bar. A1 adds delay at high pressure, but still predicts onset early there; at 2 bar it increases the positive onset error. This descriptive comparison does not replace the A1 held-out history assessment. The reduced held-out A0 comparator remains hydraulic only and has no beverage detector.

[Per-pressure values](DESCRIPTIVE_ONSET.csv) · [Per-brew operator evidence and paired results](DESCRIPTIVE_ONSET.json).
