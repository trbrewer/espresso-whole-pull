# Project State

## SCI-MD-011 Phase B result (2026-09-03)

`PHASE_B_COMPLETE_PENDING_FINAL_EXACT_HEAD_REVIEW`, with exact disposition
`SCI_MD_011_POROELASTIC_CLOSURE_TEST_BLOCKED_BY_IDENTIFIABILITY_EXECUTION_DOMAIN_OR_EQUIVALENCE_GAP`
and architecture `NOT_ADJUDICATED`. Universal P1 is
`WRONG_PRESSURE_RESPONSE`; finite-Phi E2C is `BLOCKED`, so finite-versus-
universal status is `NOT_COMPUTABLE`. This existing-data-only task adjudicated
only the implemented component under the frozen SCI-MD-010 observation
adapter. Current full EWP is `NOT_VALIDATED`; independent physical validation
is `NOT_ESTABLISHED`; Stage F and Stage D are `NOT_AUTHORIZED`; M01 is
`NOT_ADJUDICATED`; laboratory execution is `NOT_AUTHORIZED`; and automatic
successor is `NONE`.

## SCI-MD-010 merged result (2026-09-03)

`MERGED_COMPLETE`. L-HYD is
`NO_STABLE_REDUCED_DARCY_ADVANTAGE_OVER_EMPIRICAL_BASELINE`; reduced E1 is
`NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE`; current full EWP E2 is
`NOT_ADJUDICATED`. SCI-ED-003 remains complete, Stage F/D remain
unauthorized, no automatic successor is selected, and physical validation
remains `NOT_ESTABLISHED`.
The separate SCI-ED-003 owner decision remains bounded and authorizes no
execution; execution requires separate owner authorization.

## SCI-ED-003 closure-contract result (2026-09-02)

`SCI_ED_003_MINIMUM_DECISION_RELEVANT_CLOSURE_CONTRACT_DEFINED_SEPARATE_EXECUTION_AUTHORIZATION_REQUIRED`.
The current status is `CLOSURE_CONTRACT_DEFINED_EXECUTION_NOT_AUTHORIZED`.
M01 paired absolute chemistry/mass closure plus only the contextual subset of
M02 synchronized shot telemetry is the Pareto-minimal future candidate. Stage F
is nonadjudicative feasibility; Stage D would be sized and frozen only after
Stage F and separate authorization. M03, M04, and M05 have explicit later
triggers. No laboratory operation, procurement, data collection, OpenFOAM/model
execution, physics/default/parameter change, inventory predictor, or `c_s0`
mapping occurred. Physical validation remains `NOT_ESTABLISHED`; the old
SCI-DATA-FUSION-001 feature branch remains untouched.

## Current owner decision (2026-09-02)

`SCI-DATA-FUSION-001` is complete as
`SCI_DATA_FUSION_001_COMPLEMENTARY_SOURCE_CONDITIONED_SUPPORTS_ONLY`: no common
constraint, compatible uncertainty support, EWP-domain narrowing, or EWP-output
narrowing was established. Its named existing-data decision is exhausted.
SCI-ED-003 is complete. The current repository item is
`OWNER_DECISION_PENDING`: authorize Stage F feasibility, decline execution, or
request specific apparatus/laboratory capability input. Stage F is designed but
not authorized and nonadjudicative. Stage D is conditional, not sized, not
frozen, not authorized, and requires Stage F plus separate owner authorization.
No execution successor is automatically selected or authorized. Home-lab
status is `DEFER_HOME_LAB_PENDING_SEPARATE_EXECUTION_AUTHORIZATION`, and another
Pannusch or data-fusion cleanup is not selected. Physical validation remains
`NOT_ESTABLISHED`.

## XSV-PANNUSCH-EWP-INPUT-MAPPING-001 result (2026-09-01)

The selection language in this dated section is historical and superseded by
the current scientific-development priority above.

`XSV_PANNUSCH_EWP_INPUT_MAPPING_001_NO_QUALIFIED_MAPPING_PRESERVE_INDEPENDENT_INPUT_TREATMENTS`
after C1 correction. Twenty-one plausible operational mappings were adjudicated
and none qualified; six genuine context/state compatibilities remain. The EWP
density consumer is now registered, while the Pannusch temperature-dependent
density closure and fixed `RHO=980` flow-conversion constant are separately
rejected. The programmed-flow table label
and Puckworks Python density conversion do not close to one authorized unit
basis, so flow fails closed; C07/C08 histories and `MassData.flow` remain
excluded. **PRESERVE_PANNUSCH_AND_EWP_INDEPENDENT_INPUT_TREATMENTS.** No
materializer, solver/default/parameter/lock change, execution, coupling, or
production adoption occurred. `SCI-DATA-FUSION-001` is selected/READY only and
requires separate authorization. SOURCE_INTERNAL; TARGET_EXPOSED; NOT INDEPENDENT,
PHYSICAL, HYDRAULIC, PUCK_FACE_FLOW, PRESSURE_FLOW, CHEMISTRY, OR PRODUCTION
VALIDATION.

## SCI-MD-PANNUSCH-FLOW-HISTORY-001 result (2026-09-01)

`SCI_MD_PANNUSCH_FLOW_HISTORY_001_FLOW_AUTHORITY_INELIGIBLE`. Programmed flow
endpoints are machine instructions, not measured inlet or puck-face flow, and
the released source does not define the ramp coordinate, programme zero,
support, duration, or holds. `MassData.flow` is the vector derivative of fitted
beverage scale mass in g/s, not a scalar or authorized volumetric Pannusch Q;
no admissible density conversion or clock mapping is supplied. Phase B was
therefore prohibited before chemistry access. The scalar-start treatment is
retained and `XSV-PANNUSCH-EWP-INPUT-MAPPING-001` is selected, not implemented.
TARGET_EXPOSED; SOURCE_INTERNAL; NOT INDEPENDENT, PHYSICAL, HYDRAULIC,
PUCK_FACE_FLOW, OR PRODUCTION VALIDATION. No production adoption occurred;
Visualizer and home-lab restrictions are unchanged.

## OBS-PANNUSCH-FRACTION-WINDOW-001 result (2026-09-01)

`OBS_PANNUSCH_FRACTION_WINDOW_001_OBSERVER_EFFECT_INDISTINGUISHABLE` with
`FULL_24_QUALIFIED` and `SAME_SOURCE_LINEAGE_IDENTITY`. Released source code
proves the condition-major/replicate-minor 24-way join and derives `run.tE`
directly from the corresponding `MassData_modelval.mat` quadratic mass fit and
all ten cumulative vial masses. O1 is therefore exactly O0: the task-specific
positions 2/5/6 RMSE is 0.0131099266054 for both and the all-six RMSE is
0.0113721555596 for both; paired deltas and intervals are exactly zero.
Retain the source observer. Selected next action:
`SCI-MD-PANNUSCH-FLOW-HISTORY-001`, not implemented. TARGET_EXPOSED;
SOURCE_INTERNAL; NOT INDEPENDENT, PHYSICAL, HYDRAULIC, OR PRODUCTION
VALIDATION. No production physics, default, Puckworks tree, or runtime lock
changed; home-lab work remains deferred.

## EWP-REAL-WORLD-BOUNDARIES-001 material stop (2026-09-01)

`EWP_REAL_WORLD_BOUNDARIES_001_BLOCKED`. The exact permissioned recent-public
Visualizer current-state corpus reconciled at 23,169 logical records, but all
records lack documented device/pressure-sensor family and resolved integration
provenance in the canonical normalized schema. Under the prospectively frozen
G1 transfer contract, zero records and zero aggregate cells can qualify as an
EWP pressure boundary. No boundary library, EWP matrix, porosity materiality,
or physical-validation claim was manufactured. The single successor is
`EWP-RWB-001-PRESSURE-SENSOR-BOUNDARY-INTERFACE-RECONCILIATION`; home-lab work
remains deferred and production physics/defaults are unchanged.

## EWP-POROSITY-PERMEABILITY-PRIOR-001 result (2026-08-31)

`EWP_POROSITY_PERMEABILITY_PRIOR_001_POSITIVE_POROSITY_ONLY` after C2.
Exactly two propagated supports—Wadsworth total XCT porosity and Vaca C.1
epsilon_0—materially structure
bounded EWP initial-porosity sensitivity. Source permeability substitutions are
source-native stress supports only because no closed transfer to calibrated EWP
effective saturated permeability is established. They are not universal
distributions, wet operating-puck measurements, or physical validation. The
Vaca Figure 12 measured/calculated dry-porosity rows qualify its source operator
only and contribute zero eligible supports. Materiality is computed by
`EWP_PP_PRIOR_001_POROSITY_MATERIALITY_RULE_V1`, not inserted as a literal.
The
calibrated EWP default remains unchanged; wetting permeability remains independent.
Next task: `EWP-REAL-WORLD-BOUNDARIES-001`. Home-lab operation remains deferred.

## XSV-WASZKIEWICZ-DYNAMIC-HYD-001 grouped result (2026-08-31)

`XSV_WASZKIEWICZ_DYNAMIC_HYD_001_NO_TESTED_EVOLVING_RESISTANCE_FORM_HAS_STABLE_GROUPED_PREDICTIVE_ADVANTAGE`.
W-H1 and W-H3 reproduce average LOCO improvement and W-H2 improves mean LOCO
by 27.0%, but each wins only 6/11 conditions, W-H2's clustered interval crosses
zero and its mean is materially influenced by 1 bar, and corrected fair
blocked-time prediction favors W-H0A. Fixed resistance is retained by
parsimony, not physically validated. `EWP-POROSITY-PERMEABILITY-PRIOR-001` is
`READY_AFTER_C1_MERGE`; Visualizer, Pannusch, rheology, and other Waszkiewicz
questions remain unexhausted. SCI-ED-003 and home-lab operation remain deferred.

## Reviewed whole-corpus authority (2026-08-31)

All 39 material families are registered. Current priority is the completed
source-conditioned EWP hydraulic support qualification. Visualizer is boundary and
descriptive-hydraulic authority, not population chemistry. Wadsworth/Vaca stay
separate. Home-lab operation is deferred; production physics is unchanged.

## XSV-PANNUSCH-MULTIMODEL-001 grouped result (2026-08-30)

`XSV_PANNUSCH_MULTIMODEL_001_MODELS_INDISTINGUISHABLE_AT_AVAILABLE_VARIABILITY`.
C1 preserves the 53.05% fixed-Pannusch advantage over an ordinal-only pooled
profile but corrects the primary fairness comparison: fixed Pannusch RMSE
0.0113722 versus calibration-only boundary-aware empirical RMSE 0.0111868,
paired interval [-0.001167, 0.001499], with condition signs split 2–2. Unique
mechanistic predictive advantage is not established. Species partial pooling
was not supported. Current successor is `OBS-PANNUSCH-FRACTION-WINDOW-001`,
limited to qualifying source-order joins and the fraction-window observer.
SCI-ED-003 remains deferred; home-lab operation remains
`DEFER_HOME_LAB_EXISTING_DATA_NOT_YET_EXHAUSTED`. No production physics or
parameters changed; physical and independent validation remain unestablished.

## Current existing-data model-advancement priority (2026-08-30)

The accepted successor disposition is
`ESPRESSO_DATA_LEVERAGE_001_EXISTING_DATA_SUPPORTS_IMMEDIATE_MODEL_ADVANCEMENT`.
PANNUSCH-PRIOR-IMPACT-001 remains historically valid, including its absolute-
closure conclusion, but its immediate selection of SCI-ED-003 is additively
superseded. Current task: `XSV-PANNUSCH-MULTIMODEL-001`. Source-internal
Pannusch evidence is not exhausted: grouped comparison, bounded latent/nuisance
inventory treatment, scale-reduced observables, component falsification and
residual diagnosis remain legitimate despite exposed targets and unknown M0.
SCI-ED-003 remains later for closure and independence. Home-lab operation is
`DEFER_HOME_LAB_EXISTING_DATA_NOT_YET_EXHAUSTED`; Visualizer bulk anonymized
export remains high value and permission required. Physical and independent
validation remain `NOT_ESTABLISHED`.

`CURRENT_EXISTING_DATA_LEVERAGE_PROGRAMME`:
`docs/strategy/EXISTING_DATA_LEVERAGE_PROGRAMME.md`

`CURRENT_DATA_LEVERAGE_AUTHORITY`:
`provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json`

`CURRENT_DATA_LEVERAGE_LEDGER`:
`docs/analysis/data_leverage/DATA_LEVERAGE_LEDGER.csv`

## Data-first scientific-development pivot

SCI-MD-009-C1-R1 merged through PR #115 at merge commit
`834820049a98e5084495bda94fc8f3c8234b062d`, preserving the terminal
`SCI_MD_009_C1_STOP_NONLINEAR_RESPONSE_NOT_QUALIFIED`. The current surrogate
and inventory-identifiability lane is closed as a programme priority;
SCI-MD-009-C2 is `PAUSED_NOT_CURRENT_PRIORITY`. The owner has adopted the
[Data-First Scientific Development Plan](strategy/DATA_FIRST_SCIENTIFIC_DEVELOPMENT_PLAN.md).
The current next action is paired inventory/species-fraction feasibility
preparation followed by separately authorized human laboratory execution via
the EXP-006 / EXP-010 measurement route. Current solver task: `NONE`. Current
surrogate task: `NONE`. This G0 alignment changes no production physics,
scientific parameter, accepted evidence, or validation claim. Physical
validation remains `NOT_ESTABLISHED`.

## SCI-MD-009 inventory–capacity identifiability

SCI-MD-009-C1 proved the one-way target-blind firewall, hash-closed all 498
historical cases, and completed 96 frozen supplemental production cases. The
prospectively frozen quadratic nonlinear response failed held-out validation
(maximum relative fraction-mass error 0.08255 versus 0.02), so nonlinear
profiles, joint recovery, O0--O7 ranking, precision, pilot selection, and a
numerical SCI-ED-002 tail requirement were not adjudicated. Disposition:
`SCI_MD_009_C1_STOP_NONLINEAR_RESPONSE_NOT_QUALIFIED`. Prior practical-
identifiability, 20%, O6, eight-/fifteen-shot, and 6.7% statements are
withdrawn. SCI-MD-008 and SCI-ED-002 remain unchanged; physical validation
remains `NOT_ESTABLISHED`.

## SCI-MD-008 prescribed-flow exact-fraction reconstruction

SCI-MD-008 stopped prospectively at
`SCI_MD_008_STOP_FRACTION_OUTPUT_REMAINS_INVENTORY_SCALE_DEPENDENT`. Eighteen
production runs spanning low/middle/high flow, uniform/axial-two-layer geometry,
both species, and 0.01x/0.1x/1x inventory showed normalized fraction-shape
changes up to 0.0801141 versus the frozen 1e-6 tolerance. The canonical target
matrix was therefore not scored, no parameters were fitted, and no prior
disposition changed. Physical validation remains `NOT_ESTABLISHED`.

## XSV-FLOW-001 prescribed-flow numerical interface

The active G2 solver lane adds default-disabled prescribed full-basket
volumetric flow for initially saturated, static Darcy `uniform` and
`axial_two_layer` cases. Existing prescribed-pressure and lumped-machine modes
remain available and unchanged when the new mode is not selected. The new
interface is a numerical-method and boundary change only; it adds no governing
physics and physical validation remains `NOT_ESTABLISHED`.

## XSV-FRAC-001 exact discrete cup-fraction interface

XSV-FRAC-001 is complete, independently reviewed, and merged through PR #110
at merge commit `5b87d787aaf51fdd353c16ee9e08b6f6c6e83347`; issue #109 is closed. The
optional exact-discrete mass-defined multispecies fraction observer
conservatively partitions the production solver's existing per-step cup-mass
increments without adding governing physics or prescribed-flow behavior. R2A
bound fresh baseline and candidate executables to exact clean source
authorities and passed all 20 declared observer/oracle behaviors,
deterministic replay, serial/two-rank equivalence, and all four
default-disabled regressions. Timestep results were diagnostically sensitive
and axial-mesh results stable; these are application-style diagnostics only
and establish no new PDE-convergence claim. The final disposition is
`XSV_FRAC_001_R2A_PASS_MERGED_AND_CLOSED_RETURN_TO_MODEL_DEVELOPMENT`.
Physical validation remains `NOT_ESTABLISHED`. “Exact” applies only to the
production solver's existing discrete per-step cup-mass quadrature.

## SCI-ED-002 owner-accepted blocked-result closeout

SCI-ED-002 is complete as an owner-accepted, merge-authorized valid blocked design package. Its scientific blocker remains the unresolved operational reference-extractability endpoint rule. Exact producer, source, unit, hosted-CI, and branch no-physics evidence are accepted. Exhaustive public CLI mutation coverage remains incomplete and is accepted as nonblocking technical debt; the historical R2D failure is not rewritten. No further SCI-ED-002 governance work is planned absent an owner-defined revisit trigger. Commissioning, SCI-MD-007 replay, predictor development, and `c_s0` mapping remain unauthorized. The programme returns to productive model and simulation development outside the unresolved inventory-to-`c_s0` dependency.

SCI-MD-007-R2-C1 preserves the stopped R2 producer/consumer candidates and additively
supersedes their package authority with the qualified P3 handoff. The scientific reduction remains
`SCI_MD_007_INVENTORY_PRIOR_ONLY_ADDITIONAL_DIRECT_MEASUREMENTS_REQUIRED`,
locked to Puckworks commit `31741303fb604ed3e6586a555ea6ef6989c24a62` and tree
`a918072d28f555bf98638fa97da1adb568bf09b8`. Exact vendored export, manifest,
R2 correction contract, and package-authority closure
bytes are hash-verified, every manifest member closes against producer Git objects when available,
and the exported Boolean decision is independently reduced. Puckworks remains authoritative for
deriving gate primitives from evidence registers. No descriptor-conditioned
initial-inventory predictor or runtime adoption is authorized. Total roasted content remains
distinct from extractable inventory and c_s0; physical validation remains `NOT_ESTABLISHED`.
No OpenFOAM execution or governing-physics change occurred. Angeloni was not reused and
SCI-MD-006 remains its preserved pre-execution STOP. XSV-FRAC-001 has now
completed numerical qualification of the exact discrete fraction-observer
interface. It does not establish production/reduced-PDE parity, repair
SCI-MD-006, authorize an inventory predictor, or change the physical-validation
ceiling.
Public source verification: 529/529 PASS.

SCI-MD-005 is `SCI_MD_005_TRAINING_DATA_CONTRACT_BLOCKED`. Its required
inventory-scaled common-extraction H0 cannot exactly reproduce the frozen
SCI-MD-004 H0 species and total-solids artifacts because the historical cases
used one absolute saturation concentration, producing unequal species and
aggregate extracted fractions. No production physics, solver source,
Puckworks evidence, or Angeloni prediction was changed; Angeloni remains
`CONSUMED_POST_HOLDOUT_COMPARISON_DATA`. Experimental commissioning and a new
holdout execution remain unauthorized.

## SCI-MD-004 Stage E1 — conditional hydraulic reconciliation result (2026-08-25)

The owner-authorized G1 condition-specific Darcy adapter and G3 protected
execution are complete on the governed result branch. The prior merged result
`SCI_MD_004_STAGE_E1_EXECUTION_CONTRACT_BLOCKED_BEFORE_TARGET_ACCESS` remains
preserved exactly. The additive G1 freeze established 33 paired apparatus
conditions, 66/66 passing zero-inventory hydraulic qualifications, and 264/264
deterministically materialized scenarios without changing the production
solver or governing physics. Independent pre-scoring audit passed at commit
`51bb5c83010957a760c1cdfc851d3a4def9a16d8`.

All 264 target-blind prediction executions and all 792 numerical gates passed.
The immutable prediction freeze is commit
`8c46ca93e23ac8eb1c521509566f6d3e96cbc381`, tree
`9d9960945774e84b696d7dd5d17b62c474d4bdd4`. One scorer process then opened
the protected target once and atomically committed the result. H1 materially
worsened the caffeine and trigonelline joint result, so the exact disposition
is `SCI_MD_004_REJECTED_PARAMETERIZATION_OR_FORMULATION`. No retuning or second
scorer invocation is permitted. Angeloni may not again be called a no-retuning
holdout for a model revised in response to these results. General physical
validation remains `NOT_ESTABLISHED`.

## SCI-MD-004 Stage E1 — execution contract blocked before target access (2026-08-24)

At that historical stage, the human owner selected SCI-MD-004 as the active
development priority, superseding the then-current SCI-LC-001A next action
without reversing its historical scientific result. Stage A is merged and complete with disposition
`GO_STAGE_C_CONDITIONAL_HYDRAULIC_INPUT`. Stage C is a
`GOVERNING_PHYSICS_CHANGE` that adds strictly passive indexed solute states;
hydraulics are required to remain unchanged. A Stage C implementation
candidate reached independent exact-head review and was rejected because
mandatory positive-diffusivity mesh convergence and several complete
verification assertions were not established. It must not be merged. Active
owner-authorized R1 preserved that failed R0 history and established exact
base-legacy/candidate-legacy/indexed-one route equivalence across the positive-
diffusivity mesh hierarchy. The original sensitivity is inherited inlet
back-diffusion sensitivity, not a new indexed defect. The independent V15B
manufactured positive-diffusion series nevertheless failed its frozen positive
spatial-order and timestep-contamination rules. R1 is therefore
`SCI_MD_004_STAGE_C_R1_MATERIAL_POSITIVE_DIFFUSION_MESH_DEPENDENCE`, remains
failed and preserved, and received no independent review. The owner further
adjudicated that R1 did not establish a new indexed solver defect: its v2
method conflated temporal and spatial discretization error. R2 is the
separately authorized v3 verification-method correction. It compares finite-
timestep production output with an exact discrete-time oracle for spatial
verification, then compares that oracle with the continuous equations for
temporal verification. Production solver source remains byte-identical to R1.
The first frozen R2 matrix and interleaved performance protocol nominally
passed, but independent exact-head review failed four mandatory completeness
checks in V11, V12, V15A, and V16. That candidate remains unmerged and the
failed review is preserved. The bounded verification-only correction changes
no production solver source or tolerance. Its fresh adjudicative-002 V1–V18
matrix and interleaved performance protocol pass, and the exact corrected
candidate awaits one independent exact-head review. Stage A remains merged and unchanged; R0 PR #91 remains
closed without merge and R0 remains failed. R1 PR #93 and issue #92 are closed
without merge with the R1 failure preserved. The owner has now authorized
target-blind Stage E0 parameterization and conditional case freeze under
SCI-GOV-001 class G1. Exactly four caffeine/trigonelline parameters, blocked
whole-experiment cross-validation, identifiability, numerical application
qualification, the common H0/H1 observation operator, and all 66 H0/H1
reference/fine case configurations are frozen for independent pre-scoring
audit. Stage E1 then stopped at the target-blind executable-materialization
gate with
`SCI_MD_004_STAGE_E1_EXECUTION_CONTRACT_BLOCKED_BEFORE_TARGET_ACCESS`.
The frozen conditional outlet mass flow has no accepted representation in the
unchanged production interface without fitting permeability, adding a flow
boundary, or introducing a machine model. All are unauthorized. Active
protected comparison remains `NONE`: no Angeloni holdout prediction or score
has been generated.
SCI-MD-003 remains
closed and unchanged. Physical validation remains `NOT_ESTABLISHED`.

## Current SCI-ED / SCI-LC serialization authority

SCI-ED-001 C1 merged through PR #80 at merge commit
`9ac7bf88340b5c12a0003729ac4e998b7bf67626`. Its first parent is
`e8a66378d7829877fb74c87889193f32dd977772`, its second parent is the
independently reviewed head `481e9bebe1d01de32b6db5412248c37153e926ed`,
and its tree is the approved tree
`7dd5085ac2d2f756c687598c591c2a3e9eb39a20`. The merge used the pre-existing
uniquely scoped pull-request-only administrator bypass. Ruleset mutations were
zero and the pre/post canonical policy SHA-256 remained
`e901438be3464105ebfaff28983d15a00ad154508d665c106e33df44d9c83af2`.
Issue #79 is closed. The corrected result remains
`SCI_ED_001_FROZEN_FAMILIES_REMAIN_OBSERVATIONALLY_EQUIVALENT`; physical
validation is `NOT_ESTABLISHED` and no governing physics changed.

SCI-LC-001A rebuilt its reconciliation and execution-control layer on the
single accelerated replacement branch
`recovery/sci-lc-001a-accelerated-completion-v2`; PR #85 was merged normally
into the protocol branch. PR #71 remains draft. PR #82 and stacked PR #84 preserve their exact history and were
closed without merge as superseded after replacement PR #85 was established.
Their scientific protocol was not rejected; the reset corrects RCA-002 audit
state and simplifies integration. Historical noncanonical attempts occurred.
Final Attempt 04 executed once from the exact qualified head. Attempt/result
evidence covers all 3,666 keys; the controller reports a dispatch scalar of
3,666, while the exact per-key dispatched inventory is unresolved because no
durable pre-launch dispatch records survive. Required diagnostics were
incomplete; canonical scientific execution count is one and
canonical classification count is zero.
E3 and E4 Attempts 01--03 are scientifically ineligible and cannot be reused
or combined. Attempt 04 is terminal, quarantined, and ineligible.
Attempt 05 authority is `NONE`, and the family hold remains active.

The bounded scientific dependency `RP-D-LC-001b` is closed at a valid
pre-primary-experiment design block. P2a completed and P2b independently
recomputed `NO_UNAMBIGUOUS_BELOW_CANDIDATE`: the family supplied several
in-window candidates but no whole-envelope below-window candidate. No freeze
or instantiated post-freeze matrix exists, and P3/P4 remain unreachable.
SCI-LC-001A is historical and closed, not an active successor. See the
[Data-First Scientific Development Plan](strategy/DATA_FIRST_SCIENTIFIC_DEVELOPMENT_PLAN.md)
for current priorities and task-selection gates. XSV-XCT-001 is
execution-complete, XSV-ENS-001 is `MERGED_COMPLETE`, and their pore-scale
limitations are incorporated into that plan.
The `ADDITIONAL_INDEPENDENT_DATA_REQUIRED` gate continues to limit validation
claims and does not stop authorized post-observation mechanism discrimination.

SCI-MD-003 / RP-A-001 is closed. The thin EWP consumer is reconciled to the
independently accepted Puckworks v5 exact-head export and independently derives
zero eligible pairwise discrimination problems, `NO_COMPLETE_MEASUREMENT_SET`,
and `SCI_MD_003_RP_A_001_ADDITIONAL_DATA_REQUIRED`. This no-physics closeout
does not alter the historical SCI-LC-001A record below, the runtime
Puckworks dependency lock, or the physical-validation ceiling.

- Current released version: `v0.2.0`
- Last substantive scientific merge: `5c77b16513f932a822782fb97e9f8b97ceda0654`
- Last substantive scientific tree: `76741f99f58672fd6f1fd021279517a255b045b6`
- Live repository identity: resolve with `git rev-parse HEAD` and
  `git rev-parse HEAD^{tree}`
- Public baseline: `v0.1.4-public.1`, immutable sanitized R0 derivative
- Archival baseline: WP-0.1H v0.1.4, `FROZEN / QUALIFIED`
- OpenFOAM target: Foundation 12
- Puckworks integration: locked external checkout, no submodule
- Public source verification: 513/513 PASS (derived from `SOURCE_PACKAGE_MANIFEST.json`)
- Active validation case: `NONE`
- Active data-planning task: `NONE`
- Active solver task: `NONE`
- Active cross-model dependency: `NONE` (`RP-D-LC-001b` closed/bounded by
  `NO_UNAMBIGUOUS_BELOW_CANDIDATE`)
- Current next action: `NONE; SCI-MD-004 negative result closeout and merge only`
- Cross-solver work class:
  `CROSS_SOLVER_VERIFICATION_AND_CLOSURE_INTERFACE_QUALIFICATION`
- Cross-solver change declaration: `NO_GOVERNING_PHYSICS_CHANGE`
- Cross-solver evidence class: `SIMULATED_SYNTHETIC_REFERENCE`
- Current physical-validation gate: `ADDITIONAL_INDEPENDENT_DATA_REQUIRED`
- Current discovery disposition: `NO_NEW_PRODUCTION_PHYSICS_YET`
- Human-owner independent-data route decision: `STILL_REQUIRED`
- Controlling strategy version: `1.7`
- Prior strategy snapshot:
  `docs/strategy/history/whole_pull_modeling_and_simulation_strategy_v1_6.md`
- Physical validation: `NOT_ESTABLISHED`
- Experimental commissioning: `NOT_AUTHORIZED`
- Active protected comparison: `SCI-MD-004 CONSUMED ONCE; NO RETUNING`
- Protected or holdout scoring: `COMPLETE; ONE SCORER PROCESS; ONE TARGET OPEN`

The exact source-manifest count and aggregate are generated in
[`SOURCE_PACKAGE_MANIFEST.json`](../SOURCE_PACKAGE_MANIFEST.json).

XSV-XCT-001 completed its processed-real-coffee comparison; no rights-cleared
raw or segmented volume was available, so exact-mask cross-code parity and
full topology transfer remain unadjudicated. All 21 scoreable real rows are
outside the synthetic shared-feature domain, and the strict synthetic closure
does not transfer. The next recommendation is dedicated access to exact XCT
flow domains or a rights-cleared real-XCT acquisition. Production OpenFOAM
physics and the locked Puckworks runtime remain unchanged. SCI-MD-001 is
`MERGED_COMPLETE` at merge commit
`1c83a860bcab93062351be0be87d745a9bfc477d`; its approved head
`5b254f893efbc9b26bd8e05e09939f5436770f78` is preserved in the merge
ancestry. XSV-ENS-001 is the completed stochastic synthetic pore-closure and
synthetic-generator representative-volume programme. It changed no production
OpenFOAM physics, does not assess real-coffee representative volume, and does
not identify a dynamic pressure mechanism.

XSV-TAICHI-001 is `EXECUTION_COMPLETE` as a no-physics computational-
verification task. It activates no validation, data-planning, solver-
development or mechanism-selection task and does not satisfy the additional-
independent-data gate. Its result and controlling authority are
[XSV-TAICHI-001 saturated hydraulic closure parity](verification/XSV_TAICHI_001_SATURATED_HYDRAULIC_CLOSURE_PARITY.md).

XSV-TAICHI-002 completed its bounded, no-physics synthetic
morphology-response screen. It uses the existing VAL-CORPUS-001 discrepancy as
an apparent-conductance target; the frozen primary ratio is
`T_11_5 = 0.37327310642080013`. This is a simplified plausibility-screen target,
not an independently validated material-property ratio, and cannot establish a
real mechanism, real-coffee
permeability, or physical validation. The additional-independent-data gate is
unchanged.

Exact-head review correction preserved every primitive and the historical
execution runtime while replacing asserted package gates with a versioned,
fail-closed reducer. Localization is now explicitly descriptive because no
prospective change threshold was frozen. The primary X-direction non-attainment
result is unchanged; transverse C30 reductions are retained only as descriptive
anisotropy anchors. G8 independently binds the final historical G0 Git and CI
evidence, rederives the target rows, and verifies both retained copies of all
twelve geometries. The package contains 22 successful retained CUDA records;
because no independent process-attempt ledger exists, process-attempt count,
retry-ceiling compliance, and chronology are not independently reconstructed.
G9 wraps the unchanged v2 scientific reduction with reducer v4, which binds
the frozen current bytes, exact ordered run set, occurrence-level claim
contexts, and byte-identical generated and committed deterministic inventories.
Final G10 adjudication clarifies that one generated deterministic core matched
the committed core byte for byte; the historical G9 output-A and output-B
fields do not establish two separately executed reductions. Direct binding of
all 22 retained records remains PASS, while real temporary-package mutation
coverage remains partial for individual run-binding classes. These are typed
package-provenance and QA-depth limitations and do not alter the scientific
non-attainment result.
PR #61 remains draft and unmerged.

VAL-CASE-001 is complete, exact-head approved, and merged. Its corrected v2
result remains validation-support sensitivity and practical-identifiability
screening; it does not establish physical validation. VAL-CASE-002 is
`NOT_STARTED`.

WP03-002 is `COMPLETE_APPROVED_AND_MERGED` at merge commit
`0a5c146078da5d5f88b344b20e7b81042bf27ddb`; its approved head was
`78dc278212976a569bf21dda139a98c35756db14` and its executed solver SHA-256 was
`e682bb63d4b54a19133a81e1dc857217132b91918ecceb33ffbc88c35b6b0fd6`.
VAL-CORPUS-002 is `COMPLETE_APPROVED_AND_MERGED`. PR #54 merged the exact
approved head `ffe899a847a1dee4dc07303991bd7b7a5f17d64b` as merge commit
`5c77b16513f932a822782fb97e9f8b97ceda0654`, and Issue #53 closed through the
PR linkage. Its 45 production identities retain 27 PASS and 18 immutable typed
target-coverage failures; predecessor parity remains 1,500/1,500 PASS and the
nine-identity sensitivity inventory remains 9/9 PASS. The exact P2 rate
`0.3439597024835067 s^-1` remains a local Experiment-7/H1 reconstruction with
calibration closed and no refit. Final reporting identifies Schmieder
`cup_masses.csv` as post-fit derived evidence, not an independent measurement.
The result remains local reconstruction only with partial directional
transfer, grind-sign reversal, and cross-source time-shape failure. The
fail-closed framework is operational. No validation case, data-planning task,
solver task, or next mechanism is active. Protected scoring and VAL-CASE-002
remain unauthorized and have not started.

The next scientific gate is `ADDITIONAL_INDEPENDENT_DATA_REQUIRED`. A future
human-owner decision must choose between locating and qualifying an admissible
independent dataset or authorizing and commissioning the synchronized
measurement package defined by VAL-DATA-001. Additional fitting or reuse of
the same dependent cup-mass evidence is not a route to independent physical
validation. No acquisition, commissioning, new validation case, or governing
physics is authorized by this administrative state.

VAL-DATA-001 is a complete, approved, and merged non-commissioning plan for
the synchronized measurement package. `EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED`,
`GOVERNING_PHYSICS_CHANGE: NONE`, and VAL-CASE-002 remains `NOT_STARTED`.
Its final status is `COMPLETE_APPROVED_AND_MERGED`; the future
evidence route still requires prospective human-owner selection.
The final schema correction restores exact frozen VAL-CASE-001 parameter
classifications, makes partition rules route-conditional, closes all declared
foreign keys, and assigns measured pressure to one authoritative signal table.
The historical referential-integrity candidate correction bound complete pressure-sample keys,
global resource keys, table-specific null rules, and cross-table campaign and
route invariants; its then-current status was
`CORRECTED_PENDING_EXACT_HEAD_REVIEW`. Exact-head approval and PR #48 merge
subsequently closed that candidate state.
The template-interoperability correction separates local campaign instances
from catalog IDs, adds deterministic Puckworks exports, and represents
processing lineage as an acyclic multi-input/multi-output edge graph.
The implementation-contract closure binds samples and deformation to the
shot apparatus and signal registry, makes calibration applicability
registry-controlled, adds fraction parents and partition-isolated
compatibility packages, types resource payloads with terminal rights, and
separates row-value processing from file assembly and exact synchronized
exports. Commissioning remains unauthorized.
The final machine-contract closure completes all field/reference bindings,
makes package identities and summaries partition-specific, adds registered
basket-top temperature, records exact or two-source interpolated export
provenance, adds package-level fraction/chemistry disposition, and enforces
one export grid and one `COMPATIBILITY_EXPORT` operation per time-series
package.
The final export-contract reconciliation separates fixed unit conversion from
flow/density conversion, enforces the three-layer processing graph, separates
time-indexed samples from record/literal provenance, freezes package-mode
nullability and scalar encodings, and binds terminal mass to a realized shot
event. The task remains non-commissioning.
The historical compatibility-serialization closure reconciled typed resource members,
defines a sealed metadata envelope distinct from a Puckworks submission,
freezes row and nested-field ordering, maps local provenance to Puckworks
`raw`/`processed`, and removed recursive manifest dependencies. PR #48 was
subsequently approved and merged; commissioning remains unauthorized.
The state-and-serialization consistency correction makes package-operation
references mode-conditional, gives full and sealed exports disjoint graph
branches, removes unreachable status values, makes row provenance mapping
total, and freezes the apparatus calibration scalar and YAML emitter. Package
QA now binds the current source-manifest identity exactly.

VAL-INFRA-002 is a merged reusable-infrastructure repair that scopes the
legacy WP-0.3C Stage-0 verifier scope. It changes no scientific result,
framework pin, operating standard, solver, configuration, dependency, or claim
ceiling and performs no scientific execution. Its exact-head correction binds
protected Git modes and object types, rejects symbolic-link substitution, and
requires the pinned Stage-0 merge to be an ancestor of the candidate.

## Completed sequence

- **WP-0.1:** reference whole-pull implementation — complete.
- **WP-0.1H:** numerical hardening and frozen R0 qualification — complete,
  frozen and qualified.
- **WP01R:** source-linked reconstruction and residual assessment — complete
  with a structural residual; not independent physical validation.
- **WP02-001:** optional dissolution-indexed effective permeability — complete.
- **WP02-002:** lumped machine/headspace compliance and emergent basket
  pressure — complete.
- **WP02-003:** saturated Darcy–Forchheimer resistance and regime diagnostics
  — complete.
- **WP02-004:** static radial permeability heterogeneity with zone-resolved
  flow and extraction — complete.
- **WP03-001:** saturated finite-porosity quasi-static compaction — complete.

WP03-001 changes mechanical porosity and hydraulic permeability under
effective stress and composes with the machine operating-point calculation.
It is inactive during wetting and uses a fixed reference mesh. It does not
solve solid displacement or couple mechanical porosity to transport storage,
and it excludes transient Biot storage, plasticity, hysteresis, swelling,
fines, damage and dynamic channeling. Its tested cases are numerically
verified; physical validation is not established.

## Current merged capabilities

The solver includes dry-puck sharp-front wetting, first drip, prescribed or
lumped-machine pressure boundaries, upstream resistance and compliance,
Darcy and Darcy–Forchheimer saturated flow, uniform/axial/radial permeability
profiles, optional dissolution-indexed effective permeability, quasi-static
compaction, conservative one-solute transport, spatial extraction diagnostics,
cup accumulation, and water/solute conservation reporting.

R0 remains frozen and unchanged. Source-linked and synthetic mechanism
diagnostics are not improved predictions merely because they add complexity.

## Completed post-WP03 validation program and current gate

VAL-001 and PR #38 are complete and merged. The source-specific adapter framework was added
without changing governing physics. Its governed V2 comparison remains a
post-observation, non-blind, non-independent descriptive reconstruction; it is
not physical validation and does not authorize a next-physics increment.
VAL-OPS-001 provides a merged concise prospective operating standard for
proportionate validation cases and reusable infrastructure work.

VAL-CORPUS-001, WP03-002, and VAL-CORPUS-002 are complete, approved, and
merged. No validation case, data-planning task, solver task, or mechanism-
selection task is active. The current gate is
`ADDITIONAL_INDEPENDENT_DATA_REQUIRED`; the next evidence route requires a
separate human-owner decision and authorization.

See the concise
[solver development and validation roadmap](strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md)
and the
[post-WP03-001 validation and mechanism-discrimination plan](validation/POST_WP03_001_VALIDATION_AND_MECHANISM_DISCRIMINATION_PLAN.md).

General whole-solver physical validation remains `NOT_ESTABLISHED`.

SCI-MD-002A completed and merged its independent reduced transient-consolidation
lane at merge commit `c872f782351a22277b7d7a8430bcbf140cff130e`. Its accepted
disposition is `SCI_MD_002A_TRANSIENT_POROMECHANICS_REJECTED` for
`WRONG_PRESSURE_ORDERING`. The bounded result applies only to the frozen
single-state reversible family and does not reject all poromechanics.

SCI-MD-002B completed and merged its independent reduced one-way wetting-age
swelling lane at merge commit `db5b0a5492b36d568241f97b482fe90fac8d44da`.
Its accepted disposition is `SCI_MD_002B_REJECTED_WRONG_PRESSURE_ORDERING`,
qualified by
`PACKAGE_INTEGRITY_RECOVERED_BY_SAME_AUTHORITY_SINGLE_RECORD_EXACT_RESUME`.

SCI-MD-002C execution and reduction are complete, and owner scientific review
approved the disposition `SCI_MD_002C_REJECTED_WRONG_PRESSURE_ORDERING`. Its
frozen execution source is `cb9ebd2d4ba220d4777f033e06eddbae787b519a`;
serial integration remains pending exact-head review. This post-observation
screen establishes no physical validation and makes
`NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`. SCI-LC-001A remains the active,
independent primary lane. The standing `ADDITIONAL_INDEPENDENT_DATA_REQUIRED`,
`PHYSICAL_VALIDATION_NOT_ESTABLISHED`, and `NO_NEW_PRODUCTION_PHYSICS_YET`
boundaries remain unchanged.

SCI-ED-001 and its C1 causal-attribution correction are complete, independently
reviewed, owner-approved, and merged through PR #80. The corrected disposition is
`SCI_ED_001_FROZEN_FAMILIES_REMAIN_OBSERVATIONALLY_EQUIVALENT`. C1 established
that the historical P8 three-pair result came from asymmetric exposure of the
common end-of-preconditioning `normalized_flow_at_0s` signature. That feature
is `PRECONDITIONING_ONLY_NONRANKING`, a
`COMMON_PRECONDITIONING_STATE_SIGNATURE`, and
`NOT_A_PRESSURE_PROGRAM_DISCRIMINATOR`. Under the frozen N1 planning bounds,
zero of six primary family pairs are robustly separated, all six overlap, and
there is no best pressure program, best measurement package, complete set
cover, or recommended pressure program. The N0 deformation separation of TPM
from swelling does not survive N1. Quantitative direct-measurement value
remains unresolved because common cross-family observable interfaces and
frozen uncertainty targets are missing. This is
`MODEL_INFORMED_FUTURE_DESIGN_ONLY`; physical validation is not established,
experimental commissioning is not authorized, and no production governing
physics changed.
The task-specific physics-boundary verifier retains strict task-local ownership
by default and adds an exact-token, exact-three-path integration mode classified
as `OWNER_AUTHORIZED_SCI_ED_FIRST_SHARED_METADATA_OVERLAP`; SCI-LC-001A must
refresh from post-SCI-ED `origin/main` before its own eventual integration.
Independent exact-head review R1 stopped with
`SCI_ED_001_C1_INDEPENDENT_EXACT_HEAD_REVIEW_FAIL_VERIFIER_CONTRACT`: its ten
new verifier tests covered helper-level path classification but not durable CLI
exit, top-level result, or protected-check conjunction semantics. The scientific
correction was not reopened. Helper tests remain, while real strict/wrong/exact
CLI tests, protected-check override prevention, and fixed mandatory-conjunction
coverage are now added. R2A passed at the exact approved head. The
owner-approved two-parent merge is complete, Issue #79 is closed, and
SCI-ED-first shared-metadata serialization has transferred to SCI-LC.

## Completed VAL-CORPUS-001 comparison campaign

VAL-CORPUS-001 is complete, approved, and merged. It executed the unchanged
merged solver against a separately authorized read-only Puckworks evidence
snapshot without advancing the runtime
dependency lock. Exact-head review correction preserved the original attempt
history and added 13 prospectively frozen correction runs; all completed. The
corrected static branches exclude dissolution-indexed permeability evolution,
use 965 kg/m3 for Waszkiewicz mass, and use the frozen +3 s alignment without
extrapolation. Final analysis closure independently calculates measured and
nominal ordering, assigns precise anchor/transfer/post-fit roles, corrects
median-log arithmetic, and evaluates 965/997/1000 kg/m3 flow conversion. All
tested Waszkiewicz families reverse the source condition ordering at every
density. The original three finite-porosity compaction runs remain invalidated
as a separate numerical-robustness finding and were not rerun. The completed
campaign establishes neither independent nor general physical validation. See the
[comparison atlas](validation/VAL_CORPUS_001_EXISTING_EVIDENCE_COMPARISON_ATLAS.md).

WP03-002 reproduced all three finite-porosity failures, diagnosed and corrected
an equation-extrinsic convergence-gate defect, and completed the unchanged
source-linked reruns. The recovered branch still reverses the source 5/9/11
bar flow and mass ordering with Spearman `-1.0`. New governing physics is
`NOT_YET_JUSTIFIED`; VAL-CASE-002 is `NOT_STARTED`.

## Completed VAL-CASE-001 validation-support case

VAL-CASE-001 applies the merged Validation Operating Standard v1 without
changing the solver or reusable validation framework. Its prospectively
frozen local campaign completed 47 valid Foundation OpenFOAM 12 cases, with
two completed probe endpoints transparently invalidated under one bounded
correction. The result screens hydraulic and compaction sensitivities,
practical identifiability, existing model-form separation, and future
measurement information value. It performs no fitting or external-data
scoring and establishes no physical validation. Independent exact-head review
approved the corrected result, and PR #42 merged as
`c2c3136e5aae74306f37f8389f945139a9d9009f`. See the
[case report](validation/cases/VAL_CASE_001_HYDRAULIC_COMPACTION_IDENTIFIABILITY_RESULTS.md).

## Merged VAL-001 framework

VAL-001 adds enforced source adapters, semantic validation, evidence/rights
and calibration/comparison ledgers, synthetic adversarial tests, historical
re-expression records, campaign provenance, and a fail-closed evidence-gap
adapter. The initial PR arithmetic remains verified for ten in-domain points,
but its prospective-governance status is invalidated. The corrected invocation
failed after score exposure and remains invalidated. The separately authorized
replacement is `POST_OBSERVATION_REPRODUCTION`, `NOT_BLIND`, and
`NOT_INDEPENDENT`; it produced one governed result without a new OpenFOAM run.
No protected or holdout data, retuning, physics, threshold, or scientific
configuration change occurred. See the
[VAL-001 report](validation/VAL_001_SOURCE_ADAPTERS_AND_COMPONENT_COMPARISONS.md).

Final post-result hardening consumes all remaining real-data execution
authority. The original result remains arithmetic-correct but prospectively
invalidated; the first corrected invocation remains failed after score
exposure; and V2 remains the successful post-observation, non-blind,
non-independent descriptive reproduction. V2 was not rewritten. Quantitative
discrimination and mechanism uniqueness were not assessed;
`ADDITIONAL_DATA_REQUIRED_BEFORE_NEW_PHYSICS` is a conservative evidence-policy
decision. Three earlier current-head OpenFOAM runs qualify the framework but
did not produce the V2 pressure-sweep columns.

The registry, synthetic transaction, and journal-to-summary gaps were closed by
PR #38. The summary
ledger is byte-derived from the four-event journal and the production runner
refuses the final consumed authority before source access. The former
deep-schema gap is closed through 68 registry-referenced normative schema
families and direct validation of 105 current and immutable historical records.
## VAL-001 PR #38 administrative remediation

The merged candidate directly enumerates and validates all governed JSON/JSONL
records with no exclusions, cycles, or orphans. The administrative freeze is
bound by a canonical consumed lock containing the complete freeze commit and
tree. Recursive schema-AST validation remains active. Sixty-eight normative
contracts regenerate governing schemas without governed instances, all 48
earlier inferred families have transition provenance, and immutable registry
assignments select 18 executable profiles. The 340-entry mutation inventory
executes one-to-one. Final candidate closure additionally requires externally
supplied exact head and tree identities. No comparison or OpenFOAM execution
occurred in this correction. V2 remains descriptive,
post-observation, non-blind, and non-independent. No new scoring, solver run,
fit, protected access, experiment, or physics change occurred.
# SCI-ED-002 prospective measurement contract (candidate)

The branch consumes the exact Puckworks SCI-ED-002 candidate contract. Commissioning is not authorized and additional direct measurements remain required. Do not rerun SCI-MD-007 until real open-core evidence exists. Predictor development remains ineligible and `c_s0` mapping remains `NOT_ESTABLISHED`. This is a candidate branch state, not a merged authority.

## XSV-FRAC-001 completed R2A closeout

R1 failed and remains preserved; its reduced-PDE scores are non-adjudicative
because the compared routes did not share forcing or source/capacity
semantics. R2 corrected the legacy pseudo-species output and produced 20/20
observer/oracle numerical passes, but remains a preserved terminal FAIL
because executable/source binding and cross-level adjudication were
incomplete. R2A closed those two exact gaps without changing production solver
source. Its bound rerun, hosted CI, and focused exact-head review passed. PR
#110 merged at `5b87d787aaf51fdd353c16ee9e08b6f6c6e83347`, issue #109 closed, and the
programme returned to model development. Timestep sensitivity and axial-mesh
stability remain application-style diagnostics, not a PDE-convergence claim.
This adds no governing physics and establishes no physical validation;
EXP-006 remains future experimental work and SCI-MD-006 remains unchanged.
# PANNUSCH-PRIOR-IMPACT-001 current pointers (2026-08-30)

`PANNUSCH_PRIOR_IMPACT_001_COMPLETE_NORMALIZED_TRANSFER_REMAINS_INVENTORY_BLOCKED`.
Recovered source-internal fraction chemistry narrows prior broad data-gap
wording, but production M0, closure, local method qualification, hydraulics,
structure and independent validation remain scoped gaps. Next task:
`SCI-ED-003` local caffeine/trigonelline method and closure qualification
contract; no laboratory execution is authorized.

CURRENT_AVAILABLE_DATA_AUTHORITY: `provenance/AVAILABLE_DATA_AUTHORITY.json`

CURRENT_DATA_SUFFICIENCY: `docs/analysis/pannusch_prior_impact_001/CURRENT_DATA_SUFFICIENCY.json`

CURRENT_DATA_PREFLIGHT_POLICY: `docs/strategy/AVAILABLE_DATA_FIRST_POLICY.md`

## SCI-DATA-FUSION-001 result (2026-09-02)

`SCI_DATA_FUSION_001_COMPLEMENTARY_SOURCE_CONDITIONED_SUPPORTS_ONLY`. cross-corpus route exhausted; sources remain conditioned alternatives. Selected next action: `SCI-ED-003`. No production adoption, physical validation, OpenFOAM, or laboratory operation.
