# Espresso Whole-Pull Program Handoff and Forward Execution Plan

> **Current-status notice (2 September 2026):** SCI-MD-010 Phase B is complete
> pending final exact-result-head review. L-HYD is
> `NO_STABLE_REDUCED_DARCY_ADVANTAGE_OVER_EMPIRICAL_BASELINE`; reduced E1 is
> `NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE`; current full EWP E2 is
> `NOT_ADJUDICATED`. SCI-ED-003 remains complete, Stage F/D remain
> unauthorized, no automatic successor is selected, and physical validation
> remains `NOT_ESTABLISHED`. Detailed historical execution blocks below
> are retained for provenance. Their current-action fields are superseded by
> the [Data-First Scientific Development Plan](strategy/DATA_FIRST_SCIENTIFIC_DEVELOPMENT_PLAN.md)
> and live [Project State](PROJECT_STATE.md).
> SCI-ED-003 is complete with status
> `CLOSURE_CONTRACT_DEFINED_EXECUTION_NOT_AUTHORIZED`; its bounded
> `OWNER_DECISION_PENDING` requires separate owner authorization.
> Stage F and Stage D are not authorized.
> no solver, surrogate, or laboratory-execution task is active.

Current addendum: `SCI-MD-001` is `CORRECTED_PENDING_EXACT_HEAD_REVIEW`. The enduring
scientific sequence and restart handoff are maintained in the
[Scientific Modeling Forward Plan](strategy/SCIENTIFIC_MODELING_FORWARD_PLAN.md).
Historical consumed execution blocks below are unchanged; the additional-
independent-data gate still limits validation claims, not authorized
post-observation discovery.

**Prepared:** 2026-08-02  
**Purpose:** conversation-independent, repository-ready record of completed work, accepted scientific findings, current limitations, administrative corrections, and the next execution sequence  
**Recommended repository path:** `docs/PROGRAM_STATE_AND_FORWARD_PLAN.md`  
**Canonical repository:** `trbrewer/espresso-whole-pull`

---

## 0. Canonical restart block

```text
REPOSITORY:
  trbrewer/espresso-whole-pull

LAST_SUBSTANTIVE_SCIENTIFIC_MERGE:
  5c77b16513f932a822782fb97e9f8b97ceda0654

LAST_SUBSTANTIVE_SCIENTIFIC_TREE:
  76741f99f58672fd6f1fd021279517a255b045b6

LIVE_HEAD:
  RESOLVE_FROM_GIT

LIVE_TREE:
  RESOLVE_FROM_GIT

WP03_002:
  COMPLETE_APPROVED_AND_MERGED

WP03_002_MERGE_COMMIT:
  0a5c146078da5d5f88b344b20e7b81042bf27ddb

WP03_002_APPROVED_HEAD:
  78dc278212976a569bf21dda139a98c35756db14

OPENFOAM_TARGET:
  Foundation OpenFOAM 12

LATEST_EXECUTED_WP03_002_CANDIDATE_EXECUTABLE_SHA256:
  e682bb63d4b54a19133a81e1dc857217132b91918ecceb33ffbc88c35b6b0fd6

RUNTIME_PUCKWORKS_LOCK:
  fc61c4670ec7bf801e40bb391aab16048b8da26b

RUNTIME_PUCKWORKS_TREE:
  1d553e44ee2f7480a5df521560801b478618cc84

LATEST_READ_ONLY_PUCKWORKS_EVIDENCE_SNAPSHOT:
  9c52c94edb27b461b6e7a4d471d29f3cef9d053e

LATEST_EVIDENCE_TREE:
  44d6539096648777f78c4db83f0985d5bd16e352

WP03_002_OUTCOME:
  NUMERICAL_DEFECT_CORRECTED_AND_ALL_THREE_CASES_COMPLETE

CROSS_PRESSURE_ORDERING:
  STILL_REVERSED

FLOW_SPEARMAN:
  -1.0

MASS_SPEARMAN:
  -1.0

VAL_001:
  COMPLETE_AND_MERGED
  POST_OBSERVATION_NONBLIND_NONINDEPENDENT_DESCRIPTIVE_REPRODUCTION

VAL_INFRA_002:
  COMPLETE_APPROVED_AND_MERGED

VAL_CASE_001:
  COMPLETE_APPROVED_AND_MERGED

VAL_DATA_001:
  COMPLETE_APPROVED_AND_MERGED

VAL_CORPUS_001:
  COMPLETE_APPROVED_AND_MERGED

VAL_CORPUS_002:
  COMPLETE_APPROVED_AND_MERGED

VAL_CORPUS_002_MERGE_COMMIT:
  5c77b16513f932a822782fb97e9f8b97ceda0654

VAL_CORPUS_002_MERGE_TREE:
  76741f99f58672fd6f1fd021279517a255b045b6

VAL_CORPUS_002_APPROVED_HEAD:
  ffe899a847a1dee4dc07303991bd7b7a5f17d64b

VAL_CORPUS_002_APPROVED_TREE:
  76741f99f58672fd6f1fd021279517a255b045b6

PR_54:
  MERGED

ISSUE_53:
  CLOSED_BY_PR_LINKAGE

ACTIVE_VALIDATION_CASE:
  NONE

ACTIVE_DATA_PLANNING_TASK:
  NONE

ACTIVE_SOLVER_TASK:
  NONE

ACTIVE_CROSS_SOLVER_VERIFICATION_TASK:
  NONE

XSV_TAICHI_001:
  EXECUTION_COMPLETE

XSV_TAICHI_002:
  NOT_STARTED_NOT_AUTHORIZED

XSV_TAICHI_001_WORK_CLASS:
  CROSS_SOLVER_VERIFICATION_AND_CLOSURE_INTERFACE_QUALIFICATION

XSV_TAICHI_001_CHANGE_DECLARATION:
  NO_GOVERNING_PHYSICS_CHANGE

XSV_TAICHI_001_EVIDENCE_CLASS:
  SIMULATED_SYNTHETIC_REFERENCE

PHYSICAL_VALIDATION:
  NOT_ESTABLISHED

GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION:
  NOT_ESTABLISHED

NEW_GOVERNING_PHYSICS:
  NOT_YET_JUSTIFIED

EXPERIMENTAL_COMMISSIONING:
  NOT_AUTHORIZED

PROTECTED_OR_HOLDOUT_SCORING:
  NOT_AUTHORIZED

VAL_CASE_002:
  NOT_STARTED

CURRENT_SCIENTIFIC_GATE:
  ADDITIONAL_INDEPENDENT_DATA_REQUIRED

HUMAN_OWNER_INDEPENDENT_DATA_ROUTE_DECISION:
  STILL_REQUIRED
```

WP03-002 and VAL-CORPUS-002 are complete, approved, and merged.
VAL-CORPUS-002 retains 27 passing and 18 immutable typed-failed production
identities, 1,500/1,500 predecessor-parity states, and 9/9 passing sensitivity
identities. Its local Experiment-7/H1 reconstruction rate remains
`0.3439597024835067 s^-1`; calibration is closed with no refit. Final reporting
classifies the result as local reconstruction only, partial directional axis
transfer with grind-sign reversal, hydraulic target-coverage mismatch, and
cross-source time-shape failure. The fail-closed comparison framework is
operational. No validation case, data-planning task, or solver task is active.
Protected scoring remains prohibited.

---

# 1. Executive summary

The program has moved through three important stages:

1. **A numerically verified, modular whole-pull OpenFOAM solver was built.**
2. **Sensitivity, practical identifiability, and measurement information value were quantified.**
3. **The solver was confronted with existing experimental, numerical, digitized, DE1, and Puckworks evidence.**

The decisive result is that the Puckworks corpus is demonstrably useful. It exposed both local successes and material transfer failures:

- selected branches reproduce some local pressure, flow, mass, permeability, or late wetting behavior;
- the solver does **not** reproduce the observed Waszkiewicz cross-pressure ordering;
- the generic machine fixture does **not** reproduce the selected DE1 shot;
- the current wetting model is only partly successful;
- the finite-porosity compaction branch originally failed numerically in all
  three source-linked pressure cases; WP03-002 corrected that numerical defect
  without changing physics, and the completed cases still reverse the source
  cross-pressure ordering.

This is not a failed validation program. It is the desired transition from internal verification to externally anchored diagnosis.

## SCI-MD-003 / RP-A-001 closed consumer record

The independently accepted Puckworks v5 response atlas is consumed through a
thin, read-only EWP adapter. The adapter independently derives zero eligible
pairwise discrimination problems, `NO_COMPLETE_MEASUREMENT_SET`, and
`SCI_MD_003_RP_A_001_ADDITIONAL_DATA_REQUIRED`. The reconciliation changes no
solver, application, case, governing physics, model parameter, or runtime
hydraulic behavior; it leaves the production dependency lock and the active
model-development programme unchanged. Physical validation remains
`NOT_ESTABLISHED`.

VAL-CORPUS-002 is complete, approved, and merged. The next scientific gate is
additional independent data, not further fitting or reuse of the same
dependent cup-mass evidence. A future human-owner decision must choose between
qualifying an admissible independent dataset or authorizing and commissioning
the synchronized measurement package defined by VAL-DATA-001.

---

# 2. Canonical merged state and completed VAL-CORPUS-002 package

| Item | Canonical state |
|---|---|
| Last substantive scientific merge | `5c77b16513f932a822782fb97e9f8b97ceda0654` |
| Last substantive scientific tree | `76741f99f58672fd6f1fd021279517a255b045b6` |
| Live head and tree | Resolve with `git rev-parse HEAD` and `git rev-parse HEAD^{tree}` |
| OpenFOAM | Foundation 12 |
| Latest executed WP03-002 candidate executable | `e682bb63d4b54a19133a81e1dc857217132b91918ecceb33ffbc88c35b6b0fd6` |
| Runtime Puckworks lock | `fc61c4670ec7bf801e40bb391aab16048b8da26b` |
| Read-only evidence snapshot used by VAL-CORPUS-001 | `9c52c94edb27b461b6e7a4d471d29f3cef9d053e` |
| Current qualification suite | `PACKAGE_QA_STATUS.json` is the machine-readable exact-head authority for current Python-test and focused current-authority-consistency counts; this handoff deliberately does not duplicate mutable totals. Confirm live pass/fail status from exact-head CI; counts elsewhere in explicitly bounded history remain historical. |
| Current static gates | `38/38 PASS` |
| Current source manifest | current exact count and aggregate are recorded in `SOURCE_PACKAGE_MANIFEST.json` and the excluded metadata record `PACKAGE_QA_STATUS.json` to avoid self-reference |
| Physical validation | `NOT_ESTABLISHED` |
| Experimental commissioning | `NOT_AUTHORIZED` |
| Governing-physics selection | `NOT_YET_JUSTIFIED` |

The current merged solver includes:

- sharp-front dry-puck wetting and first drip;
- prescribed-pressure and lumped machine/headspace boundaries;
- upstream resistance and compliance;
- Darcy and Darcy–Forchheimer saturated flow;
- uniform, axial two-layer, and radial two-zone permeability;
- optional dissolution-indexed effective permeability;
- quasi-static pressure-dependent compaction;
- one-solute transport and extraction;
- cup mass, TDS, extraction yield, water and solute balance;
- serial/MPI execution and extensive analytical, regression, conservation, timestep, and mesh verification.

---

# 3. Completed program sequence

## 3.1 Solver-development foundation

### WP01 / WP01R

Established and reconstructed the whole-pull reference implementation, source links, public boundaries, and provenance.

### WP02-001 — dissolution-indexed effective permeability

Added the optional saturated dissolution-indexed permeability closure while preserving the constant-permeability predecessor.

### WP02-002 — machine/headspace coupling

Added lumped upstream resistance and compliance, free-flow and shutoff behavior, and emergent basket pressure.

### WP02-003 — Darcy–Forchheimer

Added saturated nonlinear inertial resistance and regime diagnostics.

### WP02-004 — static radial heterogeneity

Added core/annulus permeability zones with zone-resolved flow and extraction diagnostics.

### WP03-001 — finite-porosity quasi-static compaction

Added pressure-dependent mechanical porosity and permeability under effective stress. This branch is numerically verified for its original synthetic/predecessor cases but later failed in three source-linked VAL-CORPUS-001 cases.

No current branch includes full solid displacement, Biot storage, plasticity, hysteresis, swelling, fines migration, dynamic damage, or non-axisymmetric channeling.

---

## 3.2 Validation governance and infrastructure

| Work item | PR | Merge commit | Final role |
|---|---:|---|---|
| VAL-001 source-adapter framework | #38 | `a3e632d9deb3c4ac7c34fed079e4ed85bd370a30` | Merged framework plus post-observation, non-blind, non-independent descriptive V2 result |
| VAL-OPS-001 operating standard | #40 | `39c7bf0658c344728258ba1b4f8b935a4e889d7d` | Merged Validation Operating Standard v1 |
| VAL-INFRA-002 Stage-0 verifier repair | #44 | `0962c031a6bdaef539f68f3320020d6ccb09c174` | Merged reusable fail-closed protected-scope verifier |
| VAL-CASE-001 identifiability case | #42 | `c2c3136e5aae74306f37f8389f945139a9d9009f` | Merged sensitivity and practical-identifiability screening |
| VAL-CASE-001 administrative closure | #46 | `afc6245e1591154112e15c873e9f17dbeb4efa05` | Merged final review/owner/claim status |
| VAL-DATA-001 measurement contract | #48 | `f9bd8d5413b93d3a9986559920335d4140527f5e` | Merged prospective non-commissioning measurement/data contract |
| VAL-CORPUS-001 evidence atlas | #50 | `bafcb2bc6fb2d1fbc0680d8835efcc2133e714d1` | Merged existing-evidence comparison campaign |

---

# 4. VAL-CASE-001 — what sensitivity and identifiability screening established

## 4.1 Scope

VAL-CASE-001 executed 47 valid OpenFOAM cases with no fitting, no independent-data scoring, no protected/holdout access, and no governing-physics change.

Accepted corrected result SHA-256:

```text
bb7bba7481a56ac8729758a6d5cd36e7d046b889256a7c1d1c8ed7cff998375a
```

## 4.2 Main findings

- Flow alone is practically insufficient to identify the hydraulic and compaction parameter set.
- Basket pressure materially improves conditioning.
- Independent deformation or bed-height measurement is the key discriminator among `k0`, `pc`, and `phi0`.
- Separate upstream machine pressure adds information for `Cu`, `Ru`, `Qfree`, and `pshut`.
- First-drip timing adds machine/wetting information but relatively little saturated-compaction discrimination.
- The most informative initial conditions are prescribed 5 bar, prescribed 9 bar, and one machine-coupled condition.
- High pressure alone does not distinguish `k0` and `pc` effectively.
- Structural identifiability was not assessed.
- Physical validation was not established.

Sensitivity ranking:

```text
phi0 > pshut > k0 > pc > Qfree > Ru > Cu
```

Minimum model-informed future measurement targets were defined, but explicitly not as validated thresholds:

- basket pressure: approximately `<= 8 kPa`;
- upstream machine pressure: approximately `<= 8 kPa`;
- flow: approximately `<= 0.02 mL/s`;
- delivered mass: approximately `<= 0.5 g`;
- deformation: approximately `<= 0.05 mm`;
- synchronization: approximately `<= 20 ms`;
- optional first drip: approximately `<= 0.02 s`.

---

# 5. VAL-DATA-001 — what the measurement/data contract established

VAL-DATA-001 converted the identifiability result into a prospective, implementation-ready, non-commissioning contract.

Approved plan SHA-256:

```text
978d0711787a6604f088720327d4689102729646d4df57f96a6e121e119c5fc5
```

It defines:

- required 5-bar and 9-bar basket-top prescribed-pressure conditions;
- one machine-coupled condition;
- optional 11-bar model-form stress condition;
- separate upstream and basket-top pressure nodes;
- flow, mass, deformation, timing, preparation, calibration, uncertainty, rights, and custody requirements;
- independent, calibration-plus-holdout, and separate-characterization evidence routes;
- a parameter/evidence-role ledger;
- a normalized relational schema;
- deterministic Puckworks compatibility exports;
- sealed-partition handling;
- processing lineage;
- exact source-row provenance;
- nonrecursive manifests;
- commissioning-readiness gates.

It did **not**:

- select a final evidence route;
- prove apparatus feasibility;
- select sensors;
- determine replication;
- commission an experiment;
- collect data;
- establish physical validation.

---

# 6. VAL-CORPUS-001 — what external comparison established

## 6.1 Execution

The campaign used the unchanged Foundation OpenFOAM 12 solver.

Original campaign:

```text
16 declared
13 completed
3 fatal finite-porosity compaction launches
```

Correction campaign:

```text
13 declared
13 completed
0 failed
```

Final V3 result SHA-256:

```text
a8a8a4beda9c329021e28c12afaaa46cb230518eb72326fa7bfb09bbd45e8f7e
```

R1 external-artifact aggregate:

```text
c939258b5bddcfd1a052dae37bdb6822ea9667834af233800f2529fd7c52c854
```

## 6.2 Waszkiewicz pressure ladder

The source terminal ordering is:

```text
5 bar > 9 bar > 11 bar
```

Every tested model family instead gives:

```text
11 bar > 9 bar > 5 bar
```

Flow and accumulated-mass Spearman correlation are:

```text
-1.0
```

for:

- static Darcy;
- static Darcy–Forchheimer;
- dissolution-indexed Darcy;
- measured-terminal basket-pressure treatment;
- nominal pressure treatment;
- 965, 997, and 1000 kg/m³ flow-conversion assumptions.

Selected local agreement exists. For example, dissolution-indexed Darcy at 9 bar achieved approximately:

```text
flow RMSE: 0.120 g/s
accumulated-mass RMSE: 1.557 g
```

However, that local reconstruction does not transfer across pressure conditions.

### Full-window flow/mass RMSE summary

| Condition | Darcy static | Darcy–Forchheimer static | Dissolution-indexed Darcy |
|---|---:|---:|---:|
| 5 bar | `0.909 g/s / 26.392 g` | `1.118 g/s / 39.915 g` | `0.949 g/s / 42.879 g` |
| 9 bar | `0.863 g/s / 45.751 g` | `0.798 g/s / 17.215 g` | `0.120 g/s / 1.557 g` |
| 11 bar | `1.136 g/s / 70.311 g` | `0.721 g/s / 22.535 g` | `0.348 g/s / 17.554 g` |

Measured pressure traces improved the pressure residual but did not repair the flow/mass ordering.

## 6.3 Foster wetting-front evidence

Best declared shift:

```text
0.0 s
```

with approximately:

```text
front RMSE: 2.820 mm
```

The endpoint/late-front position is closer than the early and middle trajectory. The current wetting representation is therefore partial, not validated.

No admissible observed physical first-drip event was scored.

## 6.4 DE1 machine comparison

The current result is a generic machine-fixture overlay, not a source-informed DE1 machine reconstruction.

| Bed-depth assumption | Pressure RMSE | Mass RMSE |
|---|---:|---:|
| 7.5 mm | `2.121 bar` | `3.726 g` |
| 9.0 mm | `2.442 bar` | `4.501 g` |
| 10.5 mm | `2.693 bar` | `6.006 g` |

The mismatch worsens with assumed bed depth and remains apparatus/assumption dominated.

## 6.5 Component and numerical comparisons

- Wadsworth and Roman-Corrochano cases reproduce supplied permeability through the existing component equations. These are component reconstructions, not whole-solver validation.
- Mo preserves the expected inertial-loss direction, but unresolved coefficient dimensions prevent strong quantitative conclusions.
- The finite-porosity branch failed at all three source-linked pressure conditions:

```text
WASZ-5-COMPACT
WASZ-9-COMPACT
WASZ-11-COMPACT
```

These failures are evidence of a numerical-robustness problem. They are not evidence that the physical formulation is false.

**Later closure:** WP03-002 subsequently corrected the equation-extrinsic
convergence defect and recovered all three cases without physical or numerical
retuning. The corrected model still orders flow and mass as
`11 bar > 9 bar > 5 bar`, opposite the source ordering.

---

# 7. Current working / partial / failing / unassessed map

| Area | Current status | Meaning |
|---|---|---|
| Analytical, regression, conservation, timestep, mesh verification | Working | Extensive numerical verification exists |
| Source adapters and evidence governance | Working | Merged and reusable |
| Sensitivity and practical-identifiability screening | Working | Measurement information value is quantified |
| Local 9-bar dissolution-indexed reconstruction | Working locally | Useful source reconstruction; not transferable validation |
| Pressure-node reconstruction | Working locally | Measured pressure can be reproduced more closely |
| Wadsworth/Roman permeability equations | Working as component reconstruction | Does not establish whole-solver accuracy |
| Foster late wetting front | Partial | Early/middle shape remains wrong |
| Waszkiewicz local scales | Partial | Different branches work at different pressures |
| Waszkiewicz cross-pressure transfer | Failing | Source ordering is reversed by every tested family |
| Generic DE1 machine fixture | Failing/descriptive | Not a source-informed DE1 reconstruction |
| Finite-porosity source-linked execution | `NUMERICALLY_RECOVERED_SCIENTIFIC_TRANSFER_FAILURE_REMAINS` | 3/3 corrected cases complete; model ordering remains opposite source |
| Aggregate extraction and cup-chemistry transfer | Partial / source-specific only | VAL-CORPUS-002 completed the governed assessment: local reconstruction and partial directional transfer were observed, but grind-sign reversal, hydraulic target-coverage mismatch, and cross-source time-shape failure remain; general transfer and physical validation are not established |
| Species-resolved chemistry | Not represented | Current solver is one-solute |
| Population Visualizer transfer | Not yet executed as a frozen cohort | Available future comparison |
| Independent physical validation | Not established | No qualifying final evidence route has been executed |
| New governing physics | Not justified yet | Residuals remain confounded |

---

# 8. Scientific interpretation

## 8.1 The solver is not simply “working” or “not working”

The correct interpretation is:

- it has strong internal numerical verification;
- it can reproduce selected local source behavior;
- it does not transfer correctly across the tested pressure conditions;
- some current mechanisms improve selected conditions but are not generally predictive;
- the source-linked finite-porosity convergence defect is corrected, while
  cross-pressure scientific transfer remains unsuccessful.

## 8.2 The cross-pressure reversal is the most important external result

The failure survives:

- static versus dissolution-indexed permeability;
- Darcy versus Darcy–Forchheimer;
- measured-terminal versus nominal pressure;
- three mass-flow density conversions.

This makes it a robust observed failure of the tested model families under the current source mappings.

It does not yet identify one unique missing mechanism. Potential explanations remain confounded by:

- source-group comparability;
- bed compaction and mechanical state;
- evolving permeability;
- storage/compliance;
- source geometry;
- pressure-node interpretation;
- machine-control representation;
- timing and apparatus metadata.

## 8.3 The next physics decision must wait

A new mechanism should be selected only after:

Completed prerequisites:

- the finite-porosity implementation completes the source-linked cases;
- the corrected compaction branch is compared through the accepted atlas
  metrics; and
- VAL-CORPUS-002 is complete, approved, and merged.

Remaining scientific gate:

- additional independent data are required to separate repeated residual
  signatures from source, mapping, metadata, numerical, and identifiability
  limitations.

The completed corpus work does not imply that every source-comparability
uncertainty has been resolved. Additional fitting or reuse of the same
post-fit-derived cup-mass evidence is not a route to independent physical
validation.

---

# 9. Current administrative status

WP03-002 and VAL-CORPUS-002 are complete, approved, and merged. Earlier dated
candidate and execution records remain historical authorities for the state at
which they were issued; they are not current-status authorities.

## 9.1 Current canonical status

```text
VAL_001:
  COMPLETE_AND_MERGED

VAL_INFRA_002:
  COMPLETE_APPROVED_AND_MERGED

VAL_CASE_001:
  COMPLETE_APPROVED_AND_MERGED

VAL_DATA_001:
  COMPLETE_APPROVED_AND_MERGED

VAL_CORPUS_001:
  COMPLETE_APPROVED_AND_MERGED

VAL_CORPUS_002:
  COMPLETE_APPROVED_AND_MERGED

ACTIVE_VALIDATION_CASE:
  NONE

ACTIVE_DATA_PLANNING_TASK:
  NONE

ACTIVE_SOLVER_TASK:
  NONE

CURRENT_SCIENTIFIC_GATE:
  ADDITIONAL_INDEPENDENT_DATA_REQUIRED

PHYSICAL_VALIDATION:
  NOT_ESTABLISHED

EXPERIMENTAL_COMMISSIONING:
  NOT_AUTHORIZED

PROTECTED_OR_HOLDOUT_SCORING:
  NOT_AUTHORIZED

NEW_GOVERNING_PHYSICS:
  NOT_YET_JUSTIFIED

VAL_CASE_002:
  NOT_STARTED
```

## 9.2 Identity and reconciliation boundary

The last substantive scientific merge baseline is VAL-CORPUS-002 merge commit
`5c77b16513f932a822782fb97e9f8b97ceda0654`, tree
`76741f99f58672fd6f1fd021279517a255b045b6`. Live repository identity must be
resolved with `git rev-parse HEAD` and `git rev-parse HEAD^{tree}` rather than
stored self-referentially in this file. Administrative alignment changes no
historical scientific result or immutable campaign execution count.

---

# 10. Current forward gate

WP03-002 and VAL-CORPUS-002 are complete, approved, and merged. No current
instruction authorizes further VAL-CORPUS-002 execution, fitting, or scoring.

```text
CURRENT_SCIENTIFIC_GATE:
  ADDITIONAL_INDEPENDENT_DATA_REQUIRED

ACTIVE_VALIDATION_CASE:
  NONE

ACTIVE_DATA_PLANNING_TASK:
  NONE

ACTIVE_SOLVER_TASK:
  NONE
```

The next action is a human-owner evidence-route decision between:

1. locating and qualifying an admissible independent dataset; or
2. separately authorizing and commissioning the synchronized measurement
   package defined by VAL-DATA-001.

Neither route is authorized here. Candidate mechanisms remain evidence-
dependent possibilities only; no mechanism is selected or authorized.

---

# 11. WP03-002 detailed execution plan — `HISTORICAL_EXECUTED_AND_CONSUMED`

`NOT_CURRENT_AUTHORITY`. This section preserves the executed plan for
provenance. It does not authorize current or future work.

## 11.1 Proposed identifier

```text
WP03-002:
  FINITE_POROSITY_NONLINEAR_ROBUSTNESS_AND_SOURCE_LINKED_RECOMPARISON
```

Proposed issue title:

```text
WP03-002: diagnose and harden finite-porosity nonlinear compaction
```

Proposed branch:

```text
solver/wp03-002-finite-porosity-nonlinear-robustness
```

## 11.2 Phase A — persistent state and prospective freeze

Before new OpenFOAM execution:

1. verify exact `main`;
2. add `docs/PROGRAM_STATE_AND_FORWARD_PLAN.md`;
3. align current-state administrative records;
4. create a prospective numerical-diagnosis protocol;
5. freeze:
   - exact failed case identities and configurations;
   - executable/source identities;
   - failure signatures;
   - diagnostic outputs;
   - permitted numerical changes;
   - prohibited physical changes;
   - rerun matrix;
   - comparison metrics;
   - acceptance criteria.

## 11.3 Phase B — reproduce the failures unchanged

Rebuild the exact current solver and reproduce:

```text
WASZ-5-COMPACT
WASZ-9-COMPACT
WASZ-11-COMPACT
```

No parameter, timestep, tolerance, initialization, or control change is allowed for this reproduction.

Retain:

- complete logs;
- failing time and coupling iteration;
- pressure, porosity, permeability, effective stress, bracket and residual state;
- nonlinear iteration history;
- rank-local fatal context;
- configuration and executable hashes.

A failure that cannot be reproduced is a provenance problem and must be resolved before code modification.

## 11.4 Phase C — isolate the mathematical and numerical cause

Construct independent reference checks for:

- finite-porosity constitutive mapping;
- admissible porosity and permeability domain;
- residual continuity and monotonicity;
- endpoint signs and bracket validity;
- analytic or finite-difference derivative;
- variable scaling;
- pressure/effective-stress transformation;
- source and machine operating-point coupling;
- timestep continuation.

Map the residual over the admissible interval at the exact failing states.

Classify the cause as one of:

```text
IMPLEMENTATION_DEFECT
DERIVATIVE_OR_JACOBIAN_DEFECT
INVALID_BRACKET_OR_DOMAIN
SCALING_OR_CONDITIONING_DEFECT
INITIALIZATION_OR_CONTINUATION_DEFECT
COUPLING_STIFFNESS
SOURCE_CONFIGURATION_OUTSIDE_DECLARED_MODEL_DOMAIN
NO_ADMISSIBLE_SOLUTION_UNDER_CURRENT_MODEL
UNRESOLVED
```

## 11.5 Phase D — bounded correction

A code correction is permitted only after the diagnosis is demonstrated.

Permitted numerical approaches include:

- corrected residual/derivative implementation;
- exact admissible bounds;
- nondimensional residual scaling;
- bracketed or safeguarded hybrid root solve;
- line search or trust-region safeguard;
- continuation from the previous converged state;
- bounded substepping;
- deterministic fallback that solves the same equations;
- improved diagnostics and fail-closed status.

Not permitted:

- changing compaction equations;
- changing source physical parameters to obtain convergence;
- relaxing physical bounds;
- silently accepting a nonconverged state;
- changing tolerances after seeing source-comparison scores;
- clipping porosity/permeability without an equation-consistent derivation;
- adding swelling, plasticity, storage, damage, or another mechanism.

## 11.6 Phase E — verification

Required tests:

- scalar residual/reference agreement;
- derivative checks;
- bracket and endpoint tests;
- near-limit porosity cases;
- zero and high effective-stress cases;
- infeasible/no-root cases;
- deterministic failure classification;
- timestep refinement;
- serial/MPI repeatability;
- predecessor WP03-001 regression;
- WP02 machine-coupling regression;
- conservation and existing static gates.

The correction must not change predecessor results outside declared numerical tolerances.

## 11.7 Phase F — source-linked rerun

Rerun the exact three source-linked compaction cases with:

- unchanged physical inputs;
- unchanged evidence mapping;
- unchanged comparison windows;
- corrected numerical solver;
- retained failure/recovery provenance.

Then calculate:

- pressure RMSE;
- flow RMSE/MAE/bias;
- mass RMSE/MAE/bias;
- endpoint errors;
- early/middle/late residuals;
- source/model ordering;
- Spearman ordering;
- comparison with static Darcy, Darcy–Forchheimer, and dissolution-indexed branches.

## 11.8 Decision outcomes

```text
A:
  NUMERICAL_DEFECT_CORRECTED_AND_ALL_THREE_CASES_COMPLETE

B:
  NUMERICAL_ROBUSTNESS_IMPROVED_BUT_ONE_OR_MORE_CASES_REMAIN_INFEASIBLE

C:
  CURRENT_FINITE_POROSITY_MODEL_HAS_NO_ADMISSIBLE_SOLUTION_FOR_DECLARED_CASES

D:
  SOURCE_MAPPING_OUTSIDE_DECLARED_MODEL_DOMAIN

E:
  MATERIAL_SOLVER_DEFECT_REQUIRES_SEPARATE_GOVERNING_OR_ARCHITECTURAL_CHANGE
```

No outcome should be forced into `A`.

## 11.9 Acceptance criteria

WP03-002 is complete when:

- the original failures are reproduced or a provenance discrepancy is resolved;
- the mathematical cause is independently demonstrated;
- any code correction is minimal and equation-preserving;
- all original tests and new adversarial tests pass;
- exact source-linked reruns are complete or transparently fail with a justified classification;
- corpus metrics are updated;
- the cross-pressure ordering effect is reported;
- administrative state is current;
- the PR remains open for exact-head review.

---

# 12. Risks and controls — `HISTORICAL_EXECUTED_AND_CONSUMED`

`NOT_CURRENT_AUTHORITY`. This table records controls used by the completed
WP03-002 execution plan. It grants no present or future authority.

| Risk | Required control |
|---|---|
| Numerical stabilization changes the physical solution | Compare residual/root identity before and after; preserve equations |
| Tolerance relaxation hides nonconvergence | Freeze tolerances prospectively; report residuals |
| Source parameters are retuned | Prohibit physical-input changes |
| No-root state is mistaken for solver bug | Independent residual-domain map |
| Code bug is mistaken for missing physics | Reference implementation and derivative tests |
| One recovered condition is overinterpreted | Require all 5/9/11 cases and ordering analysis |
| Administrative work consumes the cycle | Limit it to the first freeze and final reconciliation commits |
| New physics is selected prematurely | Retain `NOT_YET_JUSTIFIED` unless separate evidence gate is met |

---

# 13. Human-owner authority template for WP03-002 — `HISTORICAL_EXECUTED_AND_CONSUMED`

`NOT_CURRENT_AUTHORITY`. The embedded template below records the authority
used for the completed work; it is expired and grants no present write or
execution authority.

Append manually to:

```text
<WORKSPACE_ROOT>/AGENTS.md
```

```markdown
## Task-specific exception — WP03-002 finite-porosity nonlinear robustness

### Human-owner authorization

Issued by: Tim Brewer
Issued: 2026-08-02
Status at issuance: ACTIVE
Current status: HISTORICAL_EXECUTED_AND_CONSUMED_NOT_CURRENT_AUTHORITY
Task identifier: WP03-002
Task title: Finite-porosity nonlinear robustness and source-linked re-comparison
Task class: NUMERICAL_SOLVER_DIAGNOSIS_CORRECTION_AND_EXECUTION
Change declaration: NO_GOVERNING_PHYSICS_CHANGE

This is a fresh, explicit, task-specific exception to the parent-workspace
rule that ordinarily restricts writes to `solver-private/`.

For WP03-002 only, automated repository work is authorized in:

`<WORKSPACE_ROOT>/espresso-whole-pull`

OpenFOAM build and execution artifacts are authorized under:

`<WORKSPACE_ROOT>/runtime-artifacts/WP03-002-*`

Temporary diagnostic outputs are authorized under:

`/tmp/wp03-002-*`

The purpose is to reproduce, diagnose, and where justified correct the
finite-porosity nonlinear failures observed in VAL-CORPUS-001, then rerun the
same source-linked cases and update their comparisons.

This authority permits numerical solver-source changes that preserve the
existing governing equations and physical parameters. It does not authorize
new governing physics.

### Authorized starting identity

Repository:
`<WORKSPACE_ROOT>/espresso-whole-pull`

Remote:
`trbrewer/espresso-whole-pull`

Required local main:
`bafcb2bc6fb2d1fbc0680d8835efcc2133e714d1`

Required origin/main:
`bafcb2bc6fb2d1fbc0680d8835efcc2133e714d1`

Required main tree:
`c1d3fdc88dabaea410c4b6236e31ce1376e5eaea`

Required working tree:
clean

Runtime Puckworks lock:
`fc61c4670ec7bf801e40bb391aab16048b8da26b`

Runtime Puckworks tree:
`1d553e44ee2f7480a5df521560801b478618cc84`

VAL-CORPUS-001 evidence snapshot:
`9c52c94edb27b461b6e7a4d471d29f3cef9d053e`

Evidence tree:
`44d6539096648777f78c4db83f0985d5bd16e352`

Accepted VAL-CORPUS-001 V3 result:
`a8a8a4beda9c329021e28c12afaaa46cb230518eb72326fa7bfb09bbd45e8f7e`

Accepted executable identity:
`0b9a8dd28aae6a2853e287a590162b0088116be9268a6012c037bada9699549c`

Stop without modification if any required identity, dependency, result,
repository, remote, or working-tree condition differs.

### Authorized issue, branch, and pull request

Create one issue titled substantially:

`WP03-002: diagnose and harden finite-porosity nonlinear compaction`

Create one branch directly from exact main:

`solver/wp03-002-finite-porosity-nonlinear-robustness`

Open one public, unmerged pull request linked to the issue.

Merge is not authorized.

### Persistent state and administrative alignment

The first prospective diagnostic-freeze commit must:

1. add:
   `docs/PROGRAM_STATE_AND_FORWARD_PLAN.md`;

2. update current-state records so they no longer describe merged PRs #38,
   #48, or #50 as open/pending;

3. record:
   - VAL-001 complete and merged;
   - VAL-DATA-001 complete, approved, and merged;
   - VAL-CORPUS-001 complete, approved, and merged;
   - no active validation case;
   - no active data-planning task;
   - WP03-002 as the active numerical task;
   - physical validation not established;
   - experimental commissioning not authorized;
   - new governing physics not yet justified;
   - VAL-CASE-002 not started;

4. create and freeze a WP03-002 diagnostic protocol before new execution.

Administrative alignment is subordinate to the numerical task and must not
become a separate governance-hardening cycle.

### Required failure reproduction

Before modifying solver source, reproduce unchanged:

- `WASZ-5-COMPACT`;
- `WASZ-9-COMPACT`;
- `WASZ-11-COMPACT`.

Use the exact merged configurations and physical inputs retained by
VAL-CORPUS-001.

Do not change:

- timestep;
- nonlinear tolerances;
- initialization;
- source pressure;
- permeability;
- porosity;
- compaction constants;
- machine parameters;
- evidence alignment.

Retain complete failure diagnostics and hashes.

### Authorized diagnosis

The task may:

- instrument the finite-porosity residual and nonlinear solve;
- retain per-iteration residuals, derivatives, brackets, state bounds, and
  coupling variables;
- construct an independent scalar/reference evaluator;
- map residuals across the admissible domain;
- test analytic and finite-difference derivatives;
- test variable scaling and conditioning;
- test previous-state continuation and deterministic substepping;
- distinguish no-root, invalid-domain, implementation, derivative, scaling,
  initialization, and coupling failures.

Instrumentation must not alter the physical equations.

### Authorized numerical correction

After a demonstrated diagnosis, the task may modify solver source solely to
correct or harden the numerical solution of the existing finite-porosity
equations.

Permitted examples:

- residual or derivative correction;
- exact admissible bounds;
- nondimensional scaling;
- safeguarded bracketed/hybrid root solve;
- line search or trust-region safeguard;
- previous-state continuation;
- deterministic bounded substepping;
- fail-closed diagnostics.

Any fallback must solve the same governing equations.

### Prohibited changes

Do not:

1. add or change governing physics;
2. change finite-porosity constitutive equations;
3. change source-linked physical parameters to obtain convergence;
4. relax physical admissibility bounds;
5. accept a nonconverged state;
6. clip porosity or permeability without an equation-consistent derivation;
7. add swelling, Biot storage, plasticity, hysteresis, fines, damage,
   channeling, thermal coupling, or another mechanism;
8. retune parameters against comparison results;
9. modify Puckworks or advance its lock;
10. access protected or sealed holdout evidence;
11. commission or conduct experiments;
12. begin VAL-CORPUS-002 or VAL-CASE-002;
13. create a release or tag;
14. merge the pull request;
15. edit this authority exception.

If the existing equations have no admissible solution, report that result
rather than forcing convergence.

### Required reruns

After any accepted numerical correction, rerun exactly:

- `WASZ-5-COMPACT`;
- `WASZ-9-COMPACT`;
- `WASZ-11-COMPACT`.

Additional synthetic/adversarial runs are permitted for verification.

No additional source-family fitting or parameter sweep is authorized.

### Required comparison

Use the accepted VAL-CORPUS-001 definitions and metrics to compare corrected
compaction results with:

- static Darcy;
- static Darcy–Forchheimer;
- dissolution-indexed Darcy.

Report:

- pressure, flow, and mass metrics;
- early/middle/late residuals;
- source/model ordering;
- Spearman ordering;
- numerical status;
- effect on the mechanism-gap ledger.

### Required checks

Run all applicable:

- focused finite-porosity unit/reference tests;
- derivative checks;
- adversarial bound/no-root tests;
- WP03-001 predecessor regressions;
- WP02 machine-coupling regressions;
- serial/MPI repeatability;
- timestep refinement;
- conservation checks;
- full Python suite;
- static gates;
- source-and-boundary verification;
- source-manifest verification;
- Stage-0 verifier;
- JSON, Markdown, shell, whitespace, secret/local-path checks;
- historical, release, dependency and governing-change boundaries;
- solver/configuration/framework/standard/Puckworks immutability checks
  outside the declared numerical source change;
- claim-boundary checks.

### Required outputs

Retain:

- prospective diagnostic protocol;
- exact reproduction record;
- independent residual/reference artifact;
- diagnosis report;
- source patch and rationale;
- focused tests;
- build identity;
- execution ledger;
- external artifact manifest and aggregate;
- corrected source-linked result bundle;
- comparison figures and tables;
- updated mechanism-gap ledger;
- updated program-state and QA records.

### Stop conditions

Stop and report if:

- the starting identity differs;
- the original failures cannot be reproduced and provenance cannot be
  reconciled;
- a governing-physics change appears necessary;
- physical parameters would need retuning;
- protected/holdout evidence is required;
- a new experiment is proposed;
- the task expands beyond finite-porosity numerical robustness and the exact
  three source-linked reruns.

### Completion and expiration

Stop after:

1. the issue, branch, and unmerged PR exist;
2. the persistent handoff and diagnostic protocol are committed;
3. exact failure reproduction is complete;
4. the diagnosis is demonstrated;
5. any bounded correction and tests are complete;
6. the exact three source-linked reruns are complete or transparently
   classified as infeasible;
7. the comparison and administrative records are current;
8. exact-head CI has reported;
9. final identities, results, failures, and claim ceilings are reported.

This authority expires upon delivery of the open PR and exact-head CI, merge
or closure of the PR, need for new governing physics, scope expansion, or
commencement of another task.

This authority does not authorize merge, VAL-CORPUS-002, VAL-CASE-002, or
experimental commissioning.
```

---

# 14. Resume block for WP03-002 — `HISTORICAL_EXECUTED_AND_CONSUMED`

`NOT_CURRENT_AUTHORITY`. This consumed resume block is retained only as
execution provenance and must not be used to resume work.

```text
WP03_002_FINITE_POROSITY_ROBUSTNESS_AUTHORITY_INSTALLED_RESUME

I have manually installed the fresh WP03-002 finite-porosity nonlinear
robustness exception in:

  <WORKSPACE_ROOT>/AGENTS.md

This task authorizes code, OpenFOAM execution, and results for numerical
diagnosis and correction of the existing finite-porosity equations.

It does not authorize new governing physics, source-parameter retuning,
Puckworks modification, protected/holdout access, experiments,
VAL-CORPUS-002, VAL-CASE-002, or merge.

## A. Verify exact state

1. Re-read all applicable AGENTS.md files and controlling repository
   documentation.

2. Verify:

   Repository:
     <WORKSPACE_ROOT>/espresso-whole-pull

   Remote:
     trbrewer/espresso-whole-pull

   local main == origin/main:
     bafcb2bc6fb2d1fbc0680d8835efcc2133e714d1

   main tree:
     c1d3fdc88dabaea410c4b6236e31ce1376e5eaea

   working tree:
     clean

   runtime Puckworks:
     fc61c4670ec7bf801e40bb391aab16048b8da26b
     tree 1d553e44ee2f7480a5df521560801b478618cc84

   VAL-CORPUS-001 V3:
     a8a8a4beda9c329021e28c12afaaa46cb230518eb72326fa7bfb09bbd45e8f7e

3. Stop without modification if any identity differs.

## B. Create persistent state and task

4. Create issue:

   WP03-002: diagnose and harden finite-porosity nonlinear compaction

5. Create branch:

   solver/wp03-002-finite-porosity-nonlinear-robustness

6. Add the supplied handoff as:

   docs/PROGRAM_STATE_AND_FORWARD_PLAN.md

7. Update current-state records to mark VAL-001, VAL-DATA-001, and
   VAL-CORPUS-001 merged; set active validation/data-planning tasks to none;
   set WP03-002 as the active numerical task.

8. Create and push a prospective WP03-002 diagnostic protocol before any new
   OpenFOAM execution.

## C. Reproduce before modifying

9. Build the exact current solver and record build/executable identity.

10. Reproduce unchanged:

    WASZ-5-COMPACT
    WASZ-9-COMPACT
    WASZ-11-COMPACT

11. Retain exact logs, iteration history, failure state, configurations,
    traces, hashes, and resource usage.

12. Do not change numerical or physical inputs during reproduction.

## D. Diagnose

13. Identify the exact failing timestep, coupling iteration, residual,
    derivative, bracket, porosity, permeability, pressure, and effective
    stress.

14. Build an independent scalar/reference evaluator.

15. Map the residual over the admissible domain at each failing state.

16. Verify derivatives independently.

17. Classify the cause using the frozen diagnosis categories.

18. Do not modify source until the diagnosis is evidenced and committed.

## E. Correct only if justified

19. Apply the smallest numerical correction that preserves the governing
    equations.

20. Add focused and adversarial tests.

21. Prove predecessor compatibility and conservation.

22. Do not tune physical inputs against source results.

## F. Rerun and compare

23. Rerun exactly the three source-linked compaction cases.

24. Feed completed traces through the accepted VAL-CORPUS-001 metrics.

25. Compare with static Darcy, Darcy–Forchheimer, and dissolution-indexed
    Darcy.

26. Report whether finite-porosity compaction:

    - completes numerically;
    - improves or worsens local scale;
    - changes cross-pressure ordering;
    - creates a new robust residual signature.

## G. Deliver

27. Commit:

    - persistent program handoff;
    - aligned administrative state;
    - diagnostic protocol;
    - reproduction record;
    - diagnosis;
    - source correction, if justified;
    - tests;
    - build/execution records;
    - corrected comparison;
    - mechanism-gap update;
    - QA and source manifests.

28. Open one unmerged PR linked to the issue.

29. Run all authorized checks and exact-head CI.

30. Report:

    - authority SHA-256;
    - issue/branch/PR;
    - base/head commits and trees;
    - exact reproduced failure signatures;
    - diagnosis category and evidence;
    - changed source paths;
    - numerical method before/after;
    - build and executable identities;
    - complete run counts;
    - 5/9/11-bar results;
    - ordering result;
    - predecessor/regression/refinement results;
    - test/static/source counts;
    - source aggregate;
    - exact-head CI;
    - working-tree state.

31. STOP with the PR open and unmerged.

Do not merge.
Do not begin VAL-CORPUS-002.
Do not add governing physics.
Do not commission an experiment.
```

---

# 15. New-conversation bootstrap

Paste this into a new conversation together with this document:

```text
The espresso-whole-pull program is scientifically merged through
VAL-CORPUS-002 merge commit 5c77b16513f932a822782fb97e9f8b97ceda0654,
tree 76741f99f58672fd6f1fd021279517a255b045b6. Resolve the live
repository identity from Git rather than treating that scientific baseline as
the mutable live HEAD.

VAL-CORPUS-002 is complete, approved, and merged. No validation case,
data-planning task, or solver task is active. The current scientific gate is
ADDITIONAL_INDEPENDENT_DATA_REQUIRED.

The human owner must select between locating and qualifying an admissible
independent dataset and separately authorizing and commissioning the
synchronized measurement package defined by VAL-DATA-001. Neither route is
authorized by this bootstrap. Experimental commissioning is not authorized,
VAL-CASE-002 is not started, new governing physics is not yet justified, and
physical validation is not established.

Use the attached PROGRAM_STATE_AND_FORWARD_PLAN as the persistent controlling
handoff.
```

---

# 16. Repository references

- VAL-CORPUS-002 substantive merge baseline:
  `https://github.com/trbrewer/espresso-whole-pull/commit/5c77b16513f932a822782fb97e9f8b97ceda0654`
- VAL-CORPUS-002 PR #54:
  `https://github.com/trbrewer/espresso-whole-pull/pull/54`
- VAL-CORPUS-002 Issue #53:
  `https://github.com/trbrewer/espresso-whole-pull/issues/53`
- Stage B2 result report:
  `docs/validation/VAL_CORPUS_002_STAGE_B2_RESULT.md`
- BASE/cup-mass lineage authority:
  `docs/validation/VAL_PUCKWORKS_001_BASE_TEMPORAL_CROSS_VALIDATION_AND_CUP_MASS_LINEAGE.md`
- Current project state:
  `docs/PROJECT_STATE.md`
- Current concise roadmap:
  `docs/strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md`
- VAL-001 PR #38:  
  `https://github.com/trbrewer/espresso-whole-pull/pull/38`
- VAL-OPS-001 PR #40:  
  `https://github.com/trbrewer/espresso-whole-pull/pull/40`
- VAL-INFRA-002 PR #44:  
  `https://github.com/trbrewer/espresso-whole-pull/pull/44`
- VAL-CASE-001 PR #42:  
  `https://github.com/trbrewer/espresso-whole-pull/pull/42`
- VAL-CASE-001 closure PR #46:  
  `https://github.com/trbrewer/espresso-whole-pull/pull/46`
- VAL-DATA-001 PR #48:  
  `https://github.com/trbrewer/espresso-whole-pull/pull/48`
- VAL-CORPUS-001 PR #50:  
  `https://github.com/trbrewer/espresso-whole-pull/pull/50`
- VAL-CORPUS-001 atlas at current main:  
  `docs/validation/VAL_CORPUS_001_EXISTING_EVIDENCE_COMPARISON_ATLAS.md`
- VAL-DATA-001 plan at current main:  
  `docs/validation/VAL_DATA_001_SYNCHRONIZED_HYDRAULIC_COMPACTION_MEASUREMENT_PLAN.md`

---

# 17. Controlling claim boundary

```text
NUMERICAL_VERIFICATION:
  EXTENSIVE_FOR_TESTED_CASES

SOURCE_RECONSTRUCTION:
  ESTABLISHED_FOR_SELECTED_COMPONENTS_AND_CONDITIONS

CROSS_CONDITION_TRANSFER:
  FAILED_FOR_TESTED_WASZKIEWICZ_PRESSURE_ORDERING

PRACTICAL_IDENTIFIABILITY_SCREENING:
  COMPLETE_FOR_VAL_CASE_001_SCOPE

MEASUREMENT_CONTRACT:
  COMPLETE_AND_MERGED

PHYSICAL_VALIDATION:
  NOT_ESTABLISHED

GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION:
  NOT_ESTABLISHED

EXPERIMENTAL_COMMISSIONING:
  NOT_AUTHORIZED

NEW_GOVERNING_PHYSICS:
  NOT_YET_JUSTIFIED
```
