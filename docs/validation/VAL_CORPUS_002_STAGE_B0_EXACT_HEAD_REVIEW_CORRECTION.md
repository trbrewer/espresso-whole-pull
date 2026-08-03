# VAL-CORPUS-002 Stage B0 Exact-Head Review Correction

**Status:** `FROZEN_BEFORE_CORRECTION_IMPLEMENTATION`

**Authorization:** `VAL-CORPUS-002-B0-CORRECTION-2026-08-03`

**Profile:** `EWP_TOOLING_STAGE_V1`

**Starting head:** `44c45266ee44319df939fcb397234adfdc34507e`

**Starting tree:** `4d14a506da3af9aacd81ec440c03c37a905cd1e9`

**Change declaration:** `SOURCE_SCENARIO_CHANGE_ONLY`

This append-only record freezes the exact-head review corrections before
implementation. It supplements, and does not rewrite, the Stage B0 execution
tooling protocol. It grants no Stage B1 authority and authorizes no OpenFOAM
build/run, calibration, fitting, model-result access, governed scoring,
protected access, solver/framework/dependency change, or merge.

## Frozen findings

1. `CALIBRATION_OBJECTIVE_MISMATCH`
2. `OPTIMIZER_COORDINATE_AND_BOUNDS_MISMATCH`
3. `P2_MANIFEST_GATE_INCOMPLETE`
4. `PRODUCTION_REDUCERS_INCOMPLETE`
5. `RAW_INTERVAL_FIELD_MAPPING_BYPASS`
6. `ARTIFACT_SYMLINK_CHECK_BYPASS`
7. `ZERO_SOURCE_DENOMINATOR_NOT_FAIL_CLOSED`
8. `PARITY_REFERENCE_NOT_FULLY_BOUND`
9. `OPTIMIZER_FINAL_SELECTION_MARKER_MISSING`

## Exact calibration objective correction

The source is bound to
`validation/cases/val_corpus_002/VAL_CORPUS_002_COHORT_SELECTION.json` and its
exact SHA-256. The ordered Experiment-7/H1 calibration vector is:

```text
target masses g: [20.0, 40.0, 60.0]
source cup-solute masses g:
  [2.9240100000000004, 3.8761999999999994, 4.187098333333333]
```

The objective identity is
`EXP7_H1_EQUAL_WEIGHT_MEAN_SQUARED_RELATIVE_ERROR_20_40_60_G_V1`, with

```text
J(k) = mean(((model_i(k) - source_i) / source_i)^2)
```

Exactly three finite positive source values and three finite nonnegative model
values are required. A zero or negative source denominator fails closed.

## Exact optimizer correction

Golden-section search operates only in `x = log(k)` and evaluates at
`k = exp(x)`. Frozen constants are:

```text
K_LOWER_S_INVERSE: 0.011446486815650324
K_UPPER_S_INVERSE: 1.1446486815650323
LOG_K_LOWER: -4.470072424390813
LOG_K_UPPER: 0.13509776159727813
LOG_K_INTERVAL_TOLERANCE: 1e-8
MAXIMUM_EVALUATIONS: 128
```

Stopping requires active log-interval width at most `1e-8`, except typed
evaluation-limit or fail-closed termination. Every trace row binds sequence,
log-k and floating identity, rate and floating identity, objective, evaluation
status/failure, cache state, active log bounds/interiors, decision, and final
selection status. Equal objectives select lower `k`. Nonconvergence cannot
produce an approved calibration manifest.

## Exact P2 manifest correction

Production materialization accepts only a typed, schema-validated synthetic or
future governed calibration manifest, never a free scalar. The governed status
required for future B2 review is
`P2_CALIBRATION_FROZEN_APPROVED_FOR_B2_REVIEW`. The manifest binds task/stage,
authorization, calibration case/template/source/objective/optimizer identities,
selected log-k/k and floating identities, solver/executable/configuration,
calibration artifact manifest/aggregate, and completion/conservation. Every
lowercase SHA-256 is syntax checked and content verified where available.
Materialization changes exactly one approved typed placeholder and applies one
identical manifest-bound rate to all 15 P2 templates. B0 tests use only a
clearly marked synthetic manifest and do not create a real B1 record.

## Reducer and barrier corrections

The production reducers will implement all frozen Schmieder replicate,
three-mass, residual, observed-range/SD-count, paired H0/H1 ratio, axis,
Waszkiewicz series/window/uncertainty, complete 3-by-4 sensitivity, singular
value/rank/correlation/equifinality, rank-ceiling, and source-only species
outputs. Source-denominator zero is
`UNDEFINED_ZERO_DENOMINATOR_WITH_PAIRED_ERRORS_REPORTED`, with no epsilon.

The production Waszkiewicz interval entry accepts only raw `time_s`,
`outlet_flow_m3_s`, `totalSoluteFluxKgS`, and exact case density. It internally
maps water and beverage mass rates and applies the `1e-15 kg/s` negative-rate
rule. Its exact checked interval-only `t=0` boundary and no-extrapolation rule
remain unchanged.

Artifact inventory checks the original path with `lstat`/`is_symlink` before
resolution, then confines the resolved target and rejects duplicate aliases.
Production parity binds the accepted reference content identity and requires
all 1,500 states from `0.02 s` through `29.9999999999994 s`; subsets, parity
`t=0`, and extrapolation fail. Protected-action control becomes an exact
allowlist of B1-admissible actions and case identities with no generic path to
protected flow data or the historical scorer.

## End boundary

The corrected tooling must finish at
`VAL_CORPUS_002_STAGE_B0_CORRECTED_TOOLING_PENDING_REVIEW`. Stage B1 remains
`NOT_STARTED`; next-stage authority remains `NONE`.
