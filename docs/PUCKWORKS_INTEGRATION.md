# Puckworks Integration

Puckworks is the external public evidence/model/data dependency. This
repository uses a machine-readable full-commit lock and deterministic
checkout-and-verification script, not a Git submodule.

The reviewed `refs/heads/main` snapshot is
`fc61c4670ec7bf801e40bb391aab16048b8da26b`. The lock means
`REVIEWED_MAIN_AT_RECORDED_UTC_CUTOFF`; it does not claim permanent alignment
with a moving upstream branch. See the
[impact report](integration/PUCKWORKS_UPDATE_IMPACT.md) and its
[machine-readable companion](../validation/integration/PUCKWORKS_UPDATE_IMPACT.json).

Puckworks is neither vendored nor a submodule. No rights-restricted material is
copied, and per-artifact rights review remains required. Future adopted inputs
must record model IDs, units, pressure nodes, evidence roles, uncertainty, and
rights status.

WP01R-001 recommends `ADOPT_WITH_FOLLOWUP`; that dependency review does not
authorize calibration, protected comparisons, or R1 implementation.

The issue #4 dossier is prepared from the exact locked commit:
[Markdown](evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.md) and
[JSON](../validation/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.json). Its
disposition is `READY_FOR_WP01R_003_WITH_DECLARED_GAPS`; issue #5 must freeze
the calibration/protected-comparison contract before implementation.

The issue #5 contract is now prepared against that same exact lock:
[Markdown](validation/R1_CALIBRATION_AND_COMPARISON_CONTRACT.md) and
[JSON](../validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json).
It freezes one active calibration degree of freedom (uniform permeability)
and five protected per-shot flow shapes. Chemistry is unprotected, and no
poroelastic closure is implemented. Once approved and merged, issue #6 may
implement the deterministic bridge and R1 case generator.

WP01R-004 implements that deterministic bridge:
`python3 scripts/r1_contract_bridge.py --root . --output
config/reconstruction_R1_waszkiewicz_9bar.json --check`. The governed outputs
are the [canonical scenario](../config/reconstruction_R1_waszkiewicz_9bar.json),
[input provenance](../validation/r1/WP01R_004_INPUT_PROVENANCE.json), and
[generated-case manifest](../validation/r1/WP01R_004_GENERATED_CASE_MANIFEST.json).
No Puckworks code or protected series is copied or executed.

WP01R-005 used the same locked source for one corrective protected-processing
pass after the full R0 and numerical release gates passed. See the
[execution report](r1/WP01R_005_R1_EXECUTION_AND_RESIDUALS.md),
[run status](../validation/r1/WP01R_005_RUN_STATUS.json),
[machine-readable result](../validation/r1/WP01R_005_EXECUTION_RESULT.json),
[environment and provenance](../validation/r1/WP01R_005_ENVIRONMENT_AND_PROVENANCE.json),
and [comparison figure](../validation/r1/WP01R_005_PROTECTED_FLOW_SHAPES.svg).
The result is explicitly non-blinded because PR #16 had already accessed the
protected data. No Puckworks code was executed and no complete source series
was vendored.

WP01R-006 selects the locked Waszkiewicz saturated dissolution-indexed
effective-permeability closure as the first WP-0.2 branch. See the
[decision](decisions/WP01R_006_FIRST_WP02_PHYSICS_SELECTION.md) and its
[machine-readable record](../validation/decisions/WP01R_006_FIRST_WP02_PHYSICS_SELECTION.json).
The first branch is source-linked and softly circular, implements effective
hydraulic resistance only, and is not independent validation. WP02-001
completed the governed implementation under issue #18, and issue #18 is
closed; machine/headspace coupling remains the runner-up.

WP02-001 executed the locked branch once at 9 bar and once at the predeclared
8-bar same-campaign group. The compact
[analysis result](../validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json),
[run status](../validation/wp02/WP02_001_RUN_STATUS.json), and
[endpoint amendment](../validation/wp02/WP02_001_ANALYZER_ENDPOINT_AMENDMENT.json)
record the passing aggregate gates, one pre-score software failure, and the
representation-only endpoint reconciliation. No additional Puckworks
invocation, solver rerun, fitting, or post-result adjustment occurred.
Physical validation remains `NOT_ESTABLISHED`.

WP-0.2F packages the merged WP02-001 result without refreshing or executing
Puckworks. The reviewed dependency remains the exact recorded commit and tree;
alignment with any newer upstream state requires a separate dependency-review
task.

WP-0.3A performed that moving-upstream review without importing or executing
new Puckworks code. It resolved `main` at
`bafafef3bc3c77599af8551d4e582aedb9b23f08`, tree
`64ccf86aff4c90d1c513f1614b39e0823f64d6d7`. No model-implementation or
dataset path was added. Several model-card and audit documents were added or
revised and were separately triaged. The bound Waszkiewicz model and data
identities remain unchanged, and no qualifying independent hydraulic holdout
was found. The runtime dependency lock remains
`fc61c4670ec7bf801e40bb391aab16048b8da26b`. See the
[alignment and holdout review](evidence/WP_0_3A_ALIGNMENT_AND_HOLDOUT_REVIEW.md),
[candidate matrix](../validation/evidence/WP_0_3A_HOLDOUT_CANDIDATE_MATRIX.json),
and [frozen contract](../validation/contracts/WP_0_3A_INDEPENDENT_HOLDOUT_AND_MECHANISM_DISCRIMINATION_CONTRACT.json).

The solver-support triage then adopted selected evidence semantics and
verification targets without advancing the dependency lock. It retires the
Schmieder prose pressure triple as Darcy data, records method-qualified TDS/EY
observables, downgrades Foster's direct flow-curve result to negative
exploratory evidence, and classifies Paper B2's late-window constant as
direct-target and in-sample. Moroney and Matias are specified as future
non-protected verification targets; Vaca Guerra is specified as an inactive
offline prior. See the [impact report](integration/PUCKWORKS_WP_0_3A_SOLVER_SUPPORT_TRIAGE.md)
and [machine-readable matrix](../validation/integration/WP_0_3A_PUCKWORKS_SOLVER_SUPPORT_IMPACT_MATRIX.json).
The solver-support evidence disposition is
`ADOPT_SELECTED_EVIDENCE_WITH_FOLLOWUP`; the runtime dependency lock
disposition is `RETAIN_EXISTING_LOCK`.
