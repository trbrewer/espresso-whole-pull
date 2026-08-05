# XSV-TAICHI-002 corrected review summary

Scientific reduction uses `XSV_TAICHI_002_REVIEW_REDUCER_V2`; current fail-closed evidence binding uses `XSV_TAICHI_002_REVIEW_REDUCER_V4` and the unchanged historical execution runtime `3bbf089ab5855bdbaeabb9a569ec9176974e8c25499a0c43c0d011be69d74a75`. No numerical run or raw evidence changed.

The primary `APPARENT_HYDRAULIC_CONDUCTANCE_RATIO_TARGET` is exactly `0.37327310642080013`; the separate nominal-pressure screen is `0.4545454545454545`. C05, C15, and C30 X-direction K/K0 are `0.7786665071`, `0.6134242896`, and `0.4240823969`. C30 crosses only the nominal screen.

- Constriction: `REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_CONSTRICTION_ENVELOPE`.
- Heterogeneity: `REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_HETEROGENEITY_ENVELOPE`; robustness is evaluated separately at amplitudes 1 and 2, never by pooling.
- Localization: `FLOW_LOCALIZATION_RESPONSE_REPORTED_DESCRIPTIVELY_NO_PROSPECTIVE_CHANGE_THRESHOLD`.
- Anisotropy: `DIRECTIONAL_PERMEABILITY_RESPONSE_REPORTED_DESCRIPTIVELY`.
- Overall X-direction synthesis: `REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_X_DIRECTION_ENVELOPE`.

C30 direction-normalized K ratios are X `0.42408239686225502`, Y `0.17610126503036505`, and Z `0.19374685744086939`. Y and Z are below the primary numerical target relative to their corresponding baselines. These are descriptive anisotropy-anchor observations, do not change the primary X conclusion, do not establish real-coffee anisotropy, and strengthen only the conditional case for directional permeability or fabric measurement.

All 22 frozen identities were executed and the final package order matches the case matrix. Chronological execution order is not independently reconstructable from a separate immutable ledger. The evidence is an exact static synthetic screen; physical validation is not established and additional independent data remain required.
