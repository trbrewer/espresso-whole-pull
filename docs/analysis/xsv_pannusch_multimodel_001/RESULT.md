# XSV-PANNUSCH-MULTIMODEL-001 C1 corrected result

## Corrected disposition

`XSV_PANNUSCH_MULTIMODEL_001_MODELS_INDISTINGUISHABLE_AT_AVAILABLE_VARIABILITY`

The fixed Pannusch model predicts the March profiles well and strongly outperforms an ordinal-only pooled baseline. It does not outperform a calibration-only empirical model supplied with the same fraction-window information. The available data therefore do not establish unique mechanistic predictive advantage, but they do show that observation-window information is material and motivate a bounded fraction-window qualification task.

This source-internal, target-exposed correction supersedes—not deletes—the original result. Independent review R2 disposition was `XSV_PANNUSCH_MULTIMODEL_001_R2_INDEPENDENT_REVIEW_SCIENTIFIC_DISPOSITION_NOT_SUPPORTED`. Producer authority is Puckworks `7cf18d7bc388f636d9bca98e6e1a1def4bf08cf5` (tree `8ced3bc61283bb8aa156c80e73e92c0ed8f03215`). No Puckworks/raw/production/Angeloni/protected-target mutation occurred.

## Fair comparison and uncertainty

Boundary-aware empirical RMSE is 0.01118680114; fixed Pannusch is 0.01137215556; ordinal pooled is 0.02422119588. Pannusch changes error by -1.657% versus the fair comparator, with paired 95% interval [-0.00116699, 0.00149899] and 2–2 condition signs. It reduces error 53.0487% versus the ordinal-only baseline: `PANNUSCH_STRONGLY_OUTPERFORMS_ORDINAL_ONLY_BASELINE`, not unique mechanistic advantage.

The primary 2,000-replicate PCG64 bootstrap samples conditions then physical shots, retaining paired analytes and intact fractions. Direct absolute intervals are Pannusch [0.00956803, 0.01408466], ordinal [0.01432273, 0.03625182], and boundary-aware [0.00897302, 0.01381262]. The corrected Pannusch-minus-ordinal interval is [-0.02377193, -0.00413934]; the superseded condition-mean interval was [-0.02286529, -0.00538683]. All four leave-one-condition-out cases retain Pannusch over ordinal, but not over boundary-aware. Exact sign flip enumerates 16 assignments: one-sided p=0.0625 and two-sided p=0.125; four conditions cannot attain conventional two-sided p<0.05.

## Fixed model, inventory, species, residuals

The published-fit subset (experiments 9,10,11,14,15), ten-condition source nonfit subset, all-calibration reconstruction, and March prediction are separate evidence classes in `PANNUSCH_SOURCE_ROLE_RESULTS.csv`. Fixed Pannusch LOSO, LOCO, and leave-grind-out are `N/A — NO_FOLD_SPECIFIC_REFIT`.

Calibration-derived `c_l1` is 8.66100465 for caffeine and 5.6214203353 for trigonelline in source concentration units. It scales unnormalized magnitude and cancels analytically and numerically from normalized shares. Across 0.001x–10x, absolute masses scale while normalized shares, primary RMSE, and residual shape remain invariant: `NORMALIZED_FIXED_PANNUSCH_CS0_SCALE_INVARIANT`. Production M0, absolute closure, general inventory robustness, and cross-model ranking robustness are not established.

Universal, analyte-pooled, partial-pool, and independent/ridge RMSEs are approximately 0.02714, 0.02422, 0.02406, and 0.02406. Added condition-dependent species complexity improves only ~0.67%, intervals cross zero, and two of four conditions worsen: `SPECIES_SIGNAL_NOT_SUPPORTED_FOR_ADDED_CONDITION_DEPENDENT_COMPLEXITY`. No molecular interaction or species successor is claimed.

Fixed-Pannusch residual means/intervals are fraction 2 +0.01669281 [0.00993480, 0.02423930], fraction 5 -0.00946034 [-0.01085453, -0.00790235], and fraction 6 -0.01001482 [-0.01233840, -0.00845346]. This supports `SYSTEMATIC_FRACTION_2_AND_TAIL_TIMING_STRUCTURE`, not a hydraulic mechanism. Condition-average windows worsen Pannusch RMSE to 0.02301356: `OBSERVATION_SCHEDULE_INFORMATION_IS_MATERIAL` and `OBSERVATION_SCHEDULE_DEPENDENCE_IS_MATERIAL`. Common-window results are secondary and limited to piecewise-linear cumulative interpolation without invented within-fraction detail.

## Successor, programme, and claim ceiling

All 24 potential telemetry associations remain `SOURCE_ORDER_ONLY`, with unqualified clocks/vial transitions and no deterministic direct-ID join. Broad telemetry/hydraulic interpretation remains unresolved. The strongest successor is `OBS-PANNUSCH-FRACTION-WINDOW-001`; fallbacks are flow history then target-independent EWP input mapping. Grind remains conditional and unsupported by the current residual. Home lab remains `DEFER_HOME_LAB_EXISTING_DATA_NOT_YET_EXHAUSTED`.

Maximum claim: source-internal, target-exposed evidence shows fixed Pannusch and a calibration-only, privilege-matched boundary-aware empirical profile predict the declared March fraction-mass-share observable with indistinguishable error at available condition and shot variability. This is not target-blind or independent validation. No production governing physics, solver equation, default, or parameter adoption changed.
