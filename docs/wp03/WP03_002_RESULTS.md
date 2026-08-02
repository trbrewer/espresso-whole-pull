# WP03-002 finite-porosity nonlinear robustness results

## Disposition

```text
WP03_002_OUTCOME:
  NUMERICAL_DEFECT_CORRECTED_AND_ALL_THREE_CASES_COMPLETE

CHANGE_DECLARATION:
  NO_GOVERNING_PHYSICS_CHANGE

PHYSICAL_VALIDATION:
  NOT_ESTABLISHED
```

The exact VAL-CORPUS-001 failures were reproduced before source modification.
The implementation incorrectly used a continuous analytical-flow comparison
as a nonlinear convergence gate at the discrete iteration tolerance. The
equation-preserving correction retains that comparison as a reported
verification diagnostic while gating convergence only on discrete flow
change, pressure change, and linear pressure residual.

No constitutive equation, physical parameter, source mapping, time step,
initialization, admissibility bound, or evidence alignment changed in the
three corrected source-linked runs.

## Build and execution

- accepted predecessor executable SHA-256:
  `0b9a8dd28aae6a2853e287a590162b0088116be9268a6012c037bada9699549c`;
- corrected executable SHA-256:
  `ac55fd72bca56cd234f44ecb269c1c422336a9d433f317c7e078343a2d695b8d`;
- unchanged reproduction: 3 attempted, 3 reproduced failures;
- corrected rerun: 3 attempted, 3 completed;
- corrected 16-rank durations: 3.15–3.43 s per case.

## Source-linked comparison

Metrics use the accepted VAL-CORPUS-001 alignment
`solver_time = source_time + 3.0 s`, 965 kg/m³ conversion, linear
interpolation without extrapolation, and the valid source/model overlap of
0–27 s / 3–30 s.

| Case | Pressure RMSE (bar) | Flow RMSE (g/s) | Mass RMSE (g) |
|---|---:|---:|---:|
| 5 bar | 0.306315 | 0.471678 | 4.761347 |
| 9 bar | 0.113035 | 0.516631 | 9.964731 |
| 11 bar | 0.359142 | 0.535402 | 10.491558 |

The corrected compaction branch orders both flow and mass as
`11 bar > 9 bar > 5 bar`. The source orders both as
`5 bar > 9 bar > 11 bar`. Spearman correlation remains `-1.0` for flow and
mass. Numerical recovery therefore does not repair the robust cross-pressure
transfer failure and does not justify new governing physics by itself.

The machine-readable comparison additionally records MAE, signed bias,
endpoint error, uncertainty coverage, accepted V3 baseline branches, and
early/middle/late residuals over thirds of the valid overlap.

## Verification and resources

- maximum serial/16-rank final relative difference across selected hydraulic,
  cup, porosity, and permeability outputs: `8.36e-13`;
- largest 0.02 s versus 0.005 s final relative difference: `5.70e-4`;
- largest 0.01 s versus 0.005 s final relative difference: `1.95e-4`;
- all active compaction steps converged in the repeatability/refinement runs;
- maximum liquid balance residual: `5.89e-15 kg`;
- maximum solute balance residual: `3.99e-12 kg`;
- serial 0.02 s: 10.34 s wall time, 56,280 kB maximum RSS;
- 16-rank 0.01 s: 4.51 s wall time, 60,704 kB maximum RSS;
- 16-rank 0.005 s: 7.58 s wall time, 60,672 kB maximum RSS.

The external reproduction and corrected run roots contain 50,607 files,
347,496,537 bytes, with aggregate SHA-256
`e2670ba15e12d1ac8cfb7874ba994adce38907ac4bf8e594c7ff399eacbb2520`.
Complete cases, fields, processor directories, logs, executables, and traces
remain outside Git.

## Claim boundary

This result establishes numerical diagnosis, an equation-preserving solver
correction, and synthetic/source-linked numerical comparison. The source
comparison is not independent physical validation. Experimental commissioning,
holdout acquisition, and protected scoring were not performed.
