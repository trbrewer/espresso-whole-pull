# VAL-CORPUS-002 Stage B0 Execution Tooling Report

**Disposition:** `VAL_CORPUS_002_STAGE_B0_CORRECTED_TOOLING_PENDING_REVIEW`

**Change declaration:** `SOURCE_SCENARIO_CHANGE_ONLY`

**Result class:** prospective tooling qualification; no scientific result

Stage B0 implements and synthetically qualifies the case-local configuration,
template, parity, observation, optimization, metric, sensitivity, artifact,
access, protected-scoring, and claim-ceiling tools frozen in the append-only
tooling protocol. OpenFOAM was not built, prepared, decomposed, or run. The
optimizer was not invoked against the solver. P2 was not fitted or
materialized for execution. No transfer model result or protected flow series
was loaded, and no governed model-versus-source score was calculated.

The exact-head correction binds the Experiment-7/H1 objective directly to the
cohort record as equal-weight mean squared relative error, moves the frozen
golden-section search to exact log-k coordinates and bounds, requires a closed
calibration manifest before P2 materialization, completes all frozen production
reducers, accepts only raw interval trace fields, rejects artifact symlinks
before resolution, requires all 1,500 predecessor states, records the final
optimizer selection, and replaces protected-action substring filtering with an
exact action/case allowlist. The correction is governed by authorization
`VAL-CORPUS-002-B0-CORRECTION-2026-08-03` under `EWP_TOOLING_STAGE_V1`.

## Direct predecessor reference

The binding record uses `DIRECT_CONTENT_ADDRESS` for
`<WP03_002_REVIEW_ROOT>/corrected-runs-v2/cases/WASZ-9-COMPACT/postProcessing/wholePull/0/traces.csv`.
It verifies 1,500 retained states, 2,796,444 bytes, file SHA-256
`bb3a5d2214b3eaf0cec2d76be0c90f56b2454cfa1982b2770841b499ed1db30a`,
and header SHA-256
`27eb008688cb84f98f5b7f877aa73d745f4b3e28ce5c99f95673ed222c854831`.
Coverage is `[0.02, 29.9999999999994] s`, inclusive; the final timestamp is
30 seconds within `1e-12 s`. A zero-time row is prohibited in parity. The
historical manifest status is
`EXCLUDED_AS_DOWNSTREAM_ARTIFACT_BY_DESIGN`.

Reference configuration SHA-256 is
`09abbfdc0115a59b9452048f1ac2dcdbaf7707c91c31b166c998eab78ecf28b5`;
executable SHA-256 is
`e682bb63d4b54a19133a81e1dc857217132b91918ecceb33ffbc88c35b6b0fd6`;
scientific-input bundle SHA-256 is
`b4930f327466f201ddaab002373ec16e51075ea90e8621963afc056180bef770`.
Initial-state parity is a separate exact-identity gate.

The Waszkiewicz interval reducer alone may add a zero-time, zero-rate,
zero-inventory integration boundary after exact initial-state checks. It is
not an observed or retained trace row and cannot enter predecessor parity.

## Deterministic inventory and barriers

The generated inventory contains exactly 45 production identities, 30 numeric
P0/P1 configurations, 15 typed P2 templates (14 Schmieder and one
Waszkiewicz), nine sensitivity identities, eight prospective new sensitivity
executions under exact baseline reuse, and a 128-evaluation optimizer maximum.
The Experiment-7/H1 P2 template canonical SHA-256 is
`2e688b4f9e756aa9bc3890f4eb8a05b9191f28208c1fc4a431d9a84fa3b710b8`.
The Waszkiewicz P2 template canonical SHA-256 is
`daf456a15525ac97299a35bb45259731b50243697b0e3b2e6f4fba33509fd0e9`.
All remaining exact hashes are retained in the machine-readable inventory.

The B0 state refuses every model-result access. The prospective B1 transition
requires separate human-owner authority and permits only Experiment-7/H1.
Transfer access before an exact P2 freeze, protected hydraulic comparison,
mode-specific P2 values, calibration use of transfer observations, and
post-transfer refitting all fail closed.

## Qualification boundary

Synthetic tests cover exact and interpolated parity, no extrapolation, no
parity `t=0`, exact initial-state identity, plateau-safe fixed-mass reduction,
the checked interval boundary, metric and sensitivity arithmetic, canonical
inventory counts, typed-template rejection paths, deterministic artifacts,
golden-section interior/boundary/tie/cache/failure/nonfinite/exhaustion paths,
and result-access/protected-score barriers.

Final repository-wide qualification counts and exact Git/CI identities are
reported in the exact-head handoff after the final commit and push.

```text
PHYSICAL_VALIDATION: NOT_ESTABLISHED
OPENFOAM: NOT_RUN
CALIBRATION: NOT_EXECUTED
OPTIMIZER_AGAINST_SOLVER: NOT_INVOKED
GOVERNED_SCORING: NOT_PERFORMED
STAGE_B1: NOT_STARTED
PR_54: DRAFT_OPEN_UNMERGED
```
