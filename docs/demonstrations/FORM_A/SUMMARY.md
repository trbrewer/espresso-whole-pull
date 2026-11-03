# Form A whole-bed closure

**capability demonstration, not validation. PHYSICAL_VALIDATION=NOT_ESTABLISHED; TARGET_EXPOSED.**

**Held-out A1 endpoint/primary-trace RMSE: 0.156/0.283 g/s; B1: 0.286/0.456.** This transfers form A, the selected four-parameter primary candidate (accuracy vs B1: NEAR / UNRESOLVED).

| Prediction | Endpoint/primary/companion RMSE, g/s | ≥9-bar slope, g/s/bar | Residuals 1/2/3.5 bar, g/s |
|---|---|---|---|
| B1 held-out | 0.286/0.456/0.621 | -0.3405 | +0.118/+0.230/+0.100 |
| E1 retained | 0.201/0.321/0.369 | -0.0748 | +0.235/+0.371/+0.381 |
| A0 in-sample | 0.131/0.262/0.322 | -0.0753 | -0.065/-0.027/+0.375 |
| A1 held-out | 0.156/0.283/0.326 | -0.0777 | -0.091/-0.219/+0.408 |
| Python A original held-out | 0.153/0.268/0.345 | -0.0763 | -0.057/-0.193/+0.428 |
| Python A A0-delay¹ | 0.152/0.275/0.333 | -0.0764 | -0.059/-0.204/+0.408 |
| Python A A1-delay¹ | 0.156/0.283/0.326 | -0.0777 | -0.091/-0.219/+0.408 |

A0 is DESCRIPTIVE_ALL in-sample; its score is not a like-for-like gain over B1. ¹Delayed held-out curves explain wetting offsets; the A0-delay curve is the reduced A0 comparator, qualified by A0 parity, with hydraulic quantities only. Scored flow is liquid ρQ; observed flow is scale-derived beverage flow. The largest A1 endpoint beverage-minus-ρQ difference is 0.061 g/s (ungraded).

**Paired A1−A0 endpoint RMSE:** native descriptive 0.131→0.136, Δ +0.0050 [-0.0005, +0.0139]; reduced held-out 0.152→0.156, Δ +0.0042 [-0.0003, +0.0112] g/s. Intervals are conditional on transferred fits; [all three paired scores](PAIRED_COMPARISONS.csv) use identical condition/brew draws.

**Peaks:** D0 capacity **6.00 [5.77, 6.27] bar** (parameter-refit interval); observed **6.1 [5.9, 6.3] bar**. Native front/100-s flow optima: A0 **13*/6.013**, A1 **6.009/6.009**, E1 **13*/7.714 bar** (*fastest tested boundary; 0.25-bar peak interpolation, no statistical solver interval). Nominal peak grades A0/A1/E1: MEETS/MEETS/NEAR. A1 ties the two optima; observed fastest onset at nominal 3.5 bar; C0's 4.55 bar is a fitted-curve median.

**Detector onset:** A0: ≥14.41 s (51/56 detected; MISSES); A1: ≥16.29 s (52/56 detected; MISSES); E1: 8.57 s (56/56 detected; MISSES). Observed 6→13-bar onset increases **41.6%**; A1 measured-history detector medians are **6.73→8.59 s (27.7%)**. Censor bounds use actual last confirmable timestamps, not 100 s. Old A0 front RMSE 8.63 s is superseded and ungraded; [all eleven medians](FIRST_DRIP_BY_PRESSURE.csv).

A1's onset RMSE bound is dominated by 1–2 bar, where the flow-fitted opening term slows wetting (2-bar held-out detector median 52.5 s vs observed 13.9 s); at 3.5–13 bar A1's signed errors are smaller than E1's at every pressure above 5 bar. [Signed detector errors and detection counts](DETECTOR_SIGNED_ERRORS.csv).

**Native descriptive onset:** RMSE bounds A0/A1 **14.415/13.435 s**; paired bound difference **−0.980 [−2.634, +1.279] s**, conditional on transferred fits. Detector grid minima: **13/6 bar** ([table](DESCRIPTIVE_ONSET.md)); no grading change.

The uniform saturated solver reproduced the imposed lumped law. A0 retains pressure-accelerated R0 wetting; A1 leaves recovery at exp(−1) until outflow. The 6.57e−14 s analytic/native first-drip match verifies the implemented relation, not agreement with measured onset.

A2 was retired after partial execution. Its increasing recovery factor cannot delay physical front arrival relative to A1 under the same prescribed pressure history. The selected extraction normalization also limits recovery to approximately 0.737, bounding the descriptive constant-pressure liquid-flow maximum at approximately 1.551 g/s. These properties make this particular arm a poor route to repairing the identified wetting and flow-scale mismatch. Its full capability campaign was not completed.

All **102 primary cases** completed; 3 A1 concentration-bound qualification failures are retained without excluding hydraulic brews. The common 0.005-s step follows the 0.0025/0.005-s study; no inventory gate. 177 retained native executions, 673.11 core-hours including geometry postprocessing; native outputs remain outside Git. [Methods, qualifications and captions](METHODS.md) · [grades](GRADES.csv) · [manifest](RUN_MANIFEST.json).

**Next-step question (outside this PR):** What is the smallest independently motivated change that reduces signed detector-onset errors by pressure condition, adds delay where predictions are early, and preserves the useful held-out flow performance?
