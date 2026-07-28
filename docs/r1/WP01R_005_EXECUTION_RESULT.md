# WP01R-005 R1 Execution Result

## Disposition

`SOURCE_LINKED_RECONSTRUCTION_FAIL`

The governed central R1 case completed to 103 s with the unchanged OpenFOAM
Foundation 12 solver. Numerical verification, reduced-twin parity, liquid and
solute conservation, and calibration reproduction passed. The five protected
flow-shape comparisons failed. This is a physical-comparison result, not a
software-execution failure, and physical validation remains
`NOT_ESTABLISHED`.

The authoritative machine-readable result is
[WP01R_005_EXECUTION_RESULT.json](../../validation/r1/WP01R_005_EXECUTION_RESULT.json).

## Frozen execution

- Puckworks commit: `fc61c4670ec7bf801e40bb391aab16048b8da26b`
- Puckworks tree: `1d553e44ee2f7480a5df521560801b478618cc84`
- solver executable SHA-256:
  `ada45a5440d08ae8da1a57d65cdf511748a340cd09a045121c59ea83a3d8d6d7`
- central permeability: `2.8642613245723525e-15 m2`
- OpenFOAM executions: one R1 central run and one separate R0 regression run
- parameter fitting, optimizer iterations, and post-run adjustments: zero

Generated fields, processor directories, complete traces, logs, and the
source-linked comparison figure remain external run evidence and are not
stored in Git. Their controlling trace and source hashes are recorded in the
JSON result. No protected numerical series is copied into this repository.

## Numerical and calibration results

- endpoint reached: `102.999999999997 s`
- first drip: `4.42643488212695 s`
- maximum liquid residual: `3.27515792264421e-15 kg`
- maximum solute residual: `2.96758025257796e-13 kg`
- late hydraulic-equivalent predicted mass flow:
  `1.8821959328388052 g/s`
- frozen analytical target: `1.8821959328386835 g/s`
- relative calibration-reproduction error: `6.46e-14` (`PASS`, limit 2%)
- fresh R0 regression: `PASS`

Chemistry outputs were recorded as unscored plausibility outputs. They are not
protected comparisons and do not support a TDS or extraction-yield validation
claim.

## Protected result

The frozen uniform-permeability prediction is constant after wetting. Its
normalized protected-window population standard deviation is zero, so Pearson
correlation is undefined and therefore `FAIL` under the predeclared `1e-8`
degeneracy rule. No jitter or regularization was applied.

| Shot | Normalized RMSE | RMSE gate | Pearson | Pearson gate |
|---|---:|---|---:|---|
| 9-1 | 0.380987 | FAIL | undefined | FAIL |
| 9-2 | 0.393133 | FAIL | undefined | FAIL |
| 9-3 | 0.480984 | FAIL | undefined | FAIL |
| 9-4 | 0.399249 | FAIL | undefined | FAIL |
| 9-5 | 0.465988 | FAIL | undefined | FAIL |

Median normalized RMSE is `0.399249`; zero of five shots meet the `0.20`
per-shot RMSE gate, and zero meet the `0.90` Pearson gate.

## Residual classification and claim ceiling

The primary residual is `STRUCTURAL_MODEL_INADEQUACY`: constant uniform Darcy
permeability reproduces the frozen static hydraulic scale but not the observed
rising-flow shapes. The result names a need for a later evidence-governed
mechanism-selection task; it does not itself authorize poroelasticity,
compaction, evolving permeability, swelling, fines, channeling, machine
compliance, or any other governing-physics change.

WP-0.1R establishes a failed source-linked, within-campaign reconstruction
test of the existing architecture. It does not establish independent physical
validation, transfer, chemistry validation, poroelastic validation, or taste
prediction.
