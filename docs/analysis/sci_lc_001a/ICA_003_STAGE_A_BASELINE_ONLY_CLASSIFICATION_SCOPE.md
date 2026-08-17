# ICA-003 Stage-A baseline-zero-state classification scope

Authorization: `SCI-LC-001A-ICA-003-STAGE-A-BASELINE-ONLY-CLASSIFICATION-SCOPE-RECONCILIATION-2026-08-17`.

Status: `FROZEN_PENDING_INDEPENDENT_REVIEW`. This task executed no scientific
case and establishes no physical validation.

## Controlling adjudications

ICA-001 proved that every one of the 2,212 dynamic keys has a deterministic,
finite, fully initialized executable state and that all numerical profiles use
the same scientific start. It also found that the then-current classifier
reserved an initial-condition-dependence branch without partner evidence.

ICA-002 correctly stopped because neither an alternate dynamic state nor its
mapping from the historical 0.5/1.5 placeholders was scientifically defined.
It did not invent `x_i=ln(a)/beta`, a pressure perturbation, or a resistance
transformation. The owner subsequently selected Architecture B and withdrew
the requirement that Stage A freeze D4's future alternate state.

## Selected architecture and question

`ARCHITECTURE_B_BASELINE_ZERO_STATE_STAGE_A_WITH_D4_ROBUSTNESS_DEFERRED`
asks only: what does the frozen reduced model predict from its frozen zero-state
initialization? It does not ask whether that prediction is independent of
initial condition, whether the attractor is unique, or whether bistability is
absent.

For every dynamic row, sector pressure is zero initially; machine pressure is
zero when present; feedback state `x_i` is zero when present. State ordering,
scaling, startup behavior, events, solver inputs, and the numerical first step
`1e-7` are unchanged. The scientific dynamic-state identity is
`ZERO_STATE_BASELINE`. Static algebraic rows use
`NOT_APPLICABLE_STATIC_ALGEBRAIC`.

## Structural realization is not dynamic state

The unchanged matrix field `initial_condition_variant` is retained for row-hash
compatibility. Its normative meaning is
`LEGACY_STRUCTURAL_OR_HETEROGENEITY_REALIZATION_IDENTIFIER_NOT_DYNAMIC_STATE`.
Base phase, rotation, reflection, symmetry, and machine-reference identifiers
select already frozen structural constructions; none changes the zero dynamic
state. No field, case ID, row hash, comparator, cache axis, or graph key changed.

## Mandatory classification scope

Dynamic classification records carry:

```text
dynamic_initial_state_variant = ZERO_STATE_BASELINE
initial_condition_scope = BASELINE_ZERO_STATE_ONLY
initial_condition_robustness = NOT_ADJUDICATED_STAGE_A
bistability_status = NOT_ADJUDICATED_STAGE_A
initial_condition_dependence_branch = NOT_EVALUATED_NOT_FALSE
```

Static records carry the corresponding
`DYNAMIC_INITIAL_CONDITION_NOT_APPLICABLE` and
`NOT_APPLICABLE_STATIC_ALGEBRAIC` values. A qualified classification is the
ordinary label joined to the scope with `;`. Missing, unknown, robust, or
negative-bistability scope values are authority-invalid. Old unqualified
records are not silently upgraded. Manifests, records, summaries, and
owner-facing aggregates retain scope.

The active Stage-A precedence is:

1. `AUTHORITY_OR_ARTIFACT_INVALID`
2. `ANALYTICAL_STRUCTURAL_IDENTITY`
3. `NUMERICALLY_UNRESOLVED`
4. `MODEL_FORM_OR_SECTOR_RESOLUTION_DISAGREEMENT`
5. `METRIC_DISAGREEMENT`
6. `NEAR_THRESHOLD_TRANSITION`
7. `LATERAL_EQUALIZATION`
8. `HETEROGENEITY_AMPLIFIES`
9. `HETEROGENEITY_PERSISTS`

`INITIAL_CONDITION_DEPENDENT_OR_BISTABLE` remains future D4 vocabulary but is
not evaluated and is not represented as false in Stage A. Canonical APIs accept
no caller assertion for agreement, robustness, or bistability.

## D4, historical placeholders, and X1

D4 and X1 remain `DEFERRED_NOT_AUTHORIZED`, with zero keys. The historical 0.5
and 1.5 values are
`NON_EXECUTABLE_HISTORICAL_PLACEHOLDERS_WITH_UNRESOLVED_SCIENTIFIC_MEANING`.
They do not map to pressure, `x_i`, total or residual resistance, conductance,
rows, keys, or classification.

A separate owner scientific-design task must decide: which memory state varies;
the dimensionless formula and values; normalization or invariant; any role for
phase reversal; required and exempt row classes; treatment of `beta=0` and
no-evolution rows; any eventual meaning of 0.5/1.5; finite-horizon sensitivity
versus stable-bistability evidence; partner schema and predicate; and how D4 may
uphold, qualify, or overturn a baseline label. ICA-003 answers none of these.
Baseline-only Stage A does not establish X1 eligibility.

## Invariants, tests, and claim ceiling

The matrix remains 1,280 rows, including 848 active cases, 362 structural
comparators, and 70 bounded controls. The graph remains 2,212 dynamic plus
1,454 static keys, totaling 3,666, cached by `(case_id,numerical_profile)`.
Tests cover exact scope enums, unchanged zero-state construction, qualifier
serialization, stale-record rejection, inactive D4 precedence, placeholder
non-executability, graph identity, and fail-closed D4/X1 boundaries.

An eventual result may say: “Within the exact frozen SCI-LC-001A reduced model
and from the frozen zero-state initialization, this case is classified as …”.
It may not claim initial-condition robustness, puck-history robustness,
attractor uniqueness, absence of bistability, experimental validation, or
necessary behavior of a real espresso puck.

ICA-003 authorizes no Stage-A, D4, X1, OpenFOAM, Puckworks, pilot, or physical
execution. The resulting exact head requires separate independent read-only
review before any later owner adjudication.
