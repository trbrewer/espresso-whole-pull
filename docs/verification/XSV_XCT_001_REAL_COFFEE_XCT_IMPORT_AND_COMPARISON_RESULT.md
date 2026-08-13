# XSV-XCT-001 real-coffee XCT import and comparison result

## Result

XSV-XCT-001 completed the mandatory processed-real-coffee route for Wadsworth et al. (2026). It did not obtain a rights-cleared raw grayscale reconstruction or binary flow mask. Exact-volume cross-code parity, full topology transfer, segmentation and resolution sensitivity, subvolume stability, directional localization, and paired real-mask restriction therefore remain unadjudicated.

The processed-data result is nevertheless decisive within its scope. The published percolation equation using connected porosity and connected specific surface reproduces the 21 hydraulically complete samples with RMSE 0.283 in natural-log permeability and median multiplicative error 1.24. The corresponding Kozeny–Carman calculation has RMSE 0.594 and median factor 1.64. These are reproductions against published *numerical* permeability, not laboratory permeability validation.

Both frozen strict synthetic-train/real-test arms fail as extrapolations. The two-feature arm underpredicts with RMSE 9.03 in natural-log permeability, median factor 4.74×10³, signed bias −8.43, zero empirical coverage by its synthetic 95% residual interval, and R² −186.24 against the explicitly stated baseline of the mean observed log K over all 21 real evaluation rows. The three-feature `SCALE_PROXY_MISMATCH` sensitivity has smaller but still severe error: RMSE 3.81, median factor 51.93, signed bias +3.06, coverage 1/21 (0.0476), and R² −32.31 against the same baseline. This remains `SYNTHETIC_CLOSURE_REAL_DATA_OUT_OF_DOMAIN`, not evidence that a real-refitted closure has been broadly validated.

## Admitted evidence

The primary source is [Wadsworth et al., “A model for the permeability of coffee pucks validated using X-ray computed micro-tomography”](https://doi.org/10.1098/rsos.252031), with its CC BY 4.0 [open repository record](https://strathprints.strath.ac.uk/95930/). The hash-verified Table 1 source has 22 samples: Guayacan and Tumba, grind settings 1–11. One row, Guayacan G2, lacks the source hydraulic fields and is retained but excluded only from undefined metrics. Source voxel sizes are 2.99 µm and 2.69 µm respectively. The samples were loosely loaded into 5 mm straws without controlled tamping, so they are `REAL_PACKED_GROUND_COFFEE_XCT`, not controlled tamped espresso pucks.

[Mo et al. (2023)](https://doi.org/10.1038/s41598-023-42380-y) was admitted as secondary method context only. Its volumes were not treated as public: the source states that datasets are available from the authors on reasonable request, and no request was sent. Its porosity-conditioned segmentation remains `SOURCE_MODEL_CONDITIONED_SEGMENTATION`.

No public raw or segmented Wadsworth flow volume was established. The publisher supplement endpoint was not retrievable during the audit, although a rights-compatible, owner-supplied read-only Table 1 copy was available from the locked evidence checkout. No large external file or local path is committed. The minimum future package is specified in `docs/data/XSV_XCT_001_REAL_VOLUME_DATA_REQUEST.md`.

## Source reproduction

The exact reproduced equations were

`K_KC = phi_c^3 / (5 s_c^2)`

and

`K_perc = 2 (1 - phi_c) phi_c^4.4 / s_c^2`,

with connected porosity `phi_c` and connected specific surface `s_c` in m⁻¹. The source angular-particle surface relation was also evaluated with `alpha = 4808 m⁻¹`. Using the angular modeled surface rather than the measured connected surface gives RMSE 0.791 and median factor 1.96 on the available rows. The source directional mean and directional standard-deviation convention could be identified from the method but not independently recalculated because the admitted Table 1 contains only the supplied aggregate.

The Table 1 grain-radius values give an ordinary all-row linear fit `R = 5.805×10⁻⁵ G + 1.3797×10⁻⁴ m`; this does not reproduce the coefficients printed in the article prose. It is retained as a source-table/prose discrepancy and is not used to tune permeability.

Simple leave-one-coffee-out references are recorded separately from reproduction. They are a two-coffee stress test, not broad validation. Connected porosity alone has RMSE 0.781 in log K; adding specific surface reduces it to 0.204. Thus surface/topological information materially improves within-source prediction, while the very small number of coffee families prevents a population claim.

## Synthetic-to-real comparison

The training set contains 225 unique XSV-ENS masks in 179 physical lineages; grouped folds keep related synthetic states together. Real observations are never used for fitting or hyperparameter selection.

The frozen two-feature arm maps connected porosity and a **specific-surface proxy mapping with non-identical definitions**. The real feature is Wadsworth's connected percolating-phase surface derived using marching cubes. The synthetic feature is a total periodic voxel-face interfacial-area proxy and is not restricted to the connected pore phase. These must not be interpreted as identically defined connected-specific-surface quantities. Real connected-phase surface spans 17,105–46,688 m⁻¹ versus 3,932–7,551 m⁻¹ for the synthetic total voxel-face proxy. As a separate robustness check, imported real total surface spans 29,884–55,947 m⁻¹ and remains surface-scale separated from the synthetic proxy.

The frozen three-feature sensitivity adds `pore_distance_q50 × voxel_m` synthetically and `R_mean_m` for the real samples. It is prominently classified `SCALE_PROXY_MISMATCH`: median pore distance and mean particle radius are non-equivalent scale descriptors. The proxy changes the fitted extrapolation from large underprediction to large overprediction and reduces error magnitude, but does not rescue transfer. All 21 rows remain outside both boxes. Median standardized nearest-synthetic distance increases from 33.13 in the two-feature arm to 49.47 in the three-feature arm; interval coverage rises only from 0/21 to 1/21.

This establishes surface-scale domain separation under a non-identical proxy mapping. It does not prove that specific surface alone is causal or uniquely identify a physical morphology mechanism. The processed source does not expose the full XSV-ENS topology feature set, so direct external evaluation of frozen `B_porosity_topology` is `FULL_TRANSFER_NOT_TESTABLE_WITH_PROCESSED_DATA_ONLY`. Without masks, the work cannot determine whether overlapping spheres are too smooth, too connected, too isotropic, or deficient in a more specific topological way.

Residuals are retained row by row and stratified by coffee and integer grind rank. Ten grind ranks contain two observations and rank 2 contains one because Guayacan G2 lacks hydraulic fields. Aggregate grind-rank error statistics are therefore formally `NOT_ESTIMABLE` at the available sample count; no unstable grouped statistic is invented.

One deterministic permeability is not supported across these real processed samples: published numerical permeability spans a factor of about 12.1. Coffee, grind, porosity, preparation, and numerical-domain effects are confounded, so this range is not an estimate of uncontrolled real-puck stochastic variance.

## SCI-MD target and unavailable volume analyses

The minimum-to-maximum cross-sample conductance ratio is 0.08272, below all three exact SCI-MD targets: 0.373506, 0.389226, and 0.395294. The observed range therefore spans the required 2.5–2.7-fold resistance change only as a `STATIC_STATE_CAPABILITY_COMPARISON` and `POST_OBSERVATION_TARGET_COMPARISON`. It does not isolate grind, coffee, porosity, or preparation and does not identify a pressure, fines, swelling, compaction, or erosion mechanism.

No raw mask means there was no scientifically valid target-transform arm, GPU LBM run, segmentation variant, resolution variant, subvolume case, anisotropy recomputation, or localization comparison. Cross-code status is `CROSS_CODE_PARITY_NOT_ADJUDICATED`; real-coffee REV status is `REAL_COFFEE_REV_NOT_ADJUDICATED`. The existing diagnostic and production solvers are unchanged.

## Scientific disposition

The evidence supports dedicated access to the exact Wadsworth binary flow domains—or a rights-cleared, well-characterized real-XCT acquisition that includes tamped-puck states—as the next programme. That is required to decide whether the generator itself should be replaced or augmented and to distinguish closure-domain shift from crop, boundary, segmentation, and resolution effects. SCI-LC-001, WP04-FIN-001, and WP04-TPM-001 are not commenced or justified by processed data alone.

`NO_NEW_PRODUCTION_PHYSICS_YET`

## Claim boundary

```text
PHYSICAL_VALIDATION: NOT_ESTABLISHED
REAL_COFFEE_GEOMETRY: PROCESSED_DATA_ONLY
REAL_TAMPED_PUCK_REPRESENTATIVE_VOLUME: NOT_ESTABLISHED
DYNAMIC_PRESSURE_MECHANISM: NOT_IDENTIFIED
PRODUCTION_OPENFOAM_PHYSICS: UNCHANGED
```

Compact evidence is under `verification/cases/xsv_xct_001/`; data-driven figures are under `docs/verification/figures/xsv_xct_001/`.
