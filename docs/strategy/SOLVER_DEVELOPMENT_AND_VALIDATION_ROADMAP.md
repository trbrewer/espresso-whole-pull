# Solver Development and Validation Roadmap

## Current roadmap authority (2026-09-03)

SCI-MD-010 is `MERGED_COMPLETE`. L-HYD is
`NO_STABLE_REDUCED_DARCY_ADVANTAGE_OVER_EMPIRICAL_BASELINE`; reduced E1 is
`NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE`; current full EWP E2 is
`NOT_ADJUDICATED`. SCI-MD-011 is
`ACTIVE_OWNER_AUTHORIZED_G1_EXISTING_DATA_TASK`. SCI-ED-003 remains complete,
Stage F/D remain unauthorized, and physical validation
remains `NOT_ESTABLISHED`.
No automatic successor is selected.
SCI-ED-003 is complete with status
`CLOSURE_CONTRACT_DEFINED_EXECUTION_NOT_AUTHORIZED`; its owner decision is
bounded and execution requires separate owner authorization. Stage F and Stage
D are not authorized.

SCI-ED-003 is complete with status
`CLOSURE_CONTRACT_DEFINED_EXECUTION_NOT_AUTHORIZED`. M01 paired absolute
chemistry/mass closure plus contextual M02 synchronized shot telemetry is the
selected future candidate. The current repository item is
`OWNER_DECISION_PENDING`; Stage F and Stage D are not authorized, separate
owner authorization is required for execution, and no automatic successor
exists. No solver, surrogate, experimental-commissioning, Pannusch-cleanup, or
data-fusion-cleanup task is active. Physical validation remains
`NOT_ESTABLISHED`.

## Historical Waszkiewicz model-form decision, superseded by later work (2026-08-31)

C1 replaces the overly broad indistinguishability headline: some tested forms
reduce average LOCO error, but no tested bounded form has stable grouped,
cross-condition, corrected blocked-time, and processing-qualified advantage.
The fixed representation is retained by parsimony, not physically validated.
`EWP-POROSITY-PERMEABILITY-PRIOR-001` is `READY_AFTER_C1_MERGE`; Visualizer,
Pannusch, rheology, and laboratory questions remain open or deferred.

The source-internal grouped comparison was null: no tested bounded evolving
resistance passed the strong predictive-advantage gate. Default fixed
resistance is retained. `EWP-POROSITY-PERMEABILITY-PRIOR-001` is the selected
research successor; this result adds no solver equation, production default,
or physical-validation claim.

Conditional order: Waszkiewicz hydraulics; separate Wadsworth/Vaca priors;
Visualizer boundaries; Pannusch fraction windows; rheology sensitivity. Results
select successors; no production adoption or home-lab work is authorized.

## Historical XSV-PANNUSCH-MULTIMODEL-001 consequence, superseded by later work (2026-08-30)

The unchanged published Pannusch structure has source-internal grouped
predictive content beyond simple baselines for fraction shares. The immediate
successor is the research-only `OBS-PANNUSCH-FRACTION-WINDOW-001` observation-operator qualification,
not production parameter adoption or new governing physics. SCI-ED-003 and
laboratory operation remain deferred.

## Historical programme priority, superseded by later work (2026-08-30)

`XSV-PANNUSCH-MULTIMODEL-001` is the immediate scientific task. It permits
research-only adapters and grouped comparison but no production governing-
physics, solver-equation, or parameter adoption. Unknown inventory is handled
by scale-reduced observables, training-only profiling, or sensitivity bounds.
SCI-ED-003 remains later for absolute closure/independence and home-lab
operation remains deferred.

> **Current execution authority (29 August 2026):** The
> [Data-First Scientific Development Plan](DATA_FIRST_SCIENTIFIC_DEVELOPMENT_PLAN.md)
> controls current task selection. SCI-LC-001A is historical/closed and is not
> an active successor. SCI-MD-009-C2 is paused.

> **SCI-MD-007 (2026-08-25):** completed as a no-physics evidence-feasibility screen.
> Disposition: `SCI_MD_007_INVENTORY_PRIOR_ONLY_ADDITIONAL_DIRECT_MEASUREMENTS_REQUIRED`.
> The next inventory-specific action is additional paired direct dry-basis caffeine and
> trigonelline measurement evidence; no predictor activation or experimental commissioning is
> authorized. XSV-FRAC-001 has completed the separate exact discrete
> fraction-observer qualification; it does not establish reduced-PDE parity or
> authorize inventory prediction.

The enduring forward scientific sequence and merged SCI-MD-001 result are in
the [Scientific Modeling Forward Plan](SCIENTIFIC_MODELING_FORWARD_PLAN.md).
The independent-data validation gate is unchanged. `RP-D-LC-001b` is closed
at the valid pre-primary-experiment design block
`NO_UNAMBIGUOUS_BELOW_CANDIDATE`; no freeze was created and P3/P4 remain
unreachable.

## Purpose

This is the concise current / next / later roadmap. The long-form controlling
rationale is the [Whole-Pull Modeling and Simulation Strategy](WHOLE_PULL_MODELING_AND_SIMULATION_STRATEGY.md).

## Current merged platform

The merged Foundation OpenFOAM 12 solver provides:

- dry-puck sharp-front wetting and physical first-drip prediction within the
  current model;
- prescribed-pressure and lumped machine/headspace boundaries, upstream
  resistance and compliance, and emergent basket pressure;
- saturated Darcy and Darcy–Forchheimer flow;
- uniform, axial two-layer and radial two-zone permeability;
- optional dissolution-indexed effective permeability;
- quasi-static pressure-dependent compaction;
- conservative one-solute transport with extractable and retained inventories;
- spatial flow and extraction diagnostics;
- cup mass, TDS, extraction yield, water balance and solute balance; and
- serial/MPI execution with analytical, regression, conservation, timestep
  and mesh verification.

```text
PHYSICAL_VALIDATION:
  NOT_ESTABLISHED

GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION:
  NOT_ESTABLISHED
```

## Completed validation program through VAL-CORPUS-002

VAL-CORPUS-001, WP03-002, and VAL-CORPUS-002 are complete, approved, and
merged. VAL-CORPUS-001 exposed reversed Waszkiewicz cross-pressure ordering.
WP03-002 corrected an equation-extrinsic convergence-gate defect without
retuning; the unchanged source-linked cases then completed while retaining the
adverse cross-pressure ordering.

VAL-CORPUS-002 completed the fixed-parameter aggregate-extraction and cup-
chemistry comparison with:

- 27 production PASS dispositions;
- 18 immutable typed target-coverage failures;
- 9/9 sensitivity identities PASS;
- 1,500/1,500 predecessor-parity states PASS;
- fixed P2 `0.3439597024835067 s^-1`, restricted to a local
  Experiment-7/H1 reconstruction;
- `cup_masses.csv` classified as post-fit-derived quantities, not independent
  measurements;
- partial directional transfer with grind-sign reversal;
- hydraulic target-coverage mismatch; and
- cross-source time-shape failure.

These results support an operational fail-closed comparison framework. They do
not establish physical validation or authorize another mechanism.

## Current gate

```text
ACTIVE_VALIDATION_CASE:
  NONE

ACTIVE_DATA_PLANNING_TASK:
  NONE

ACTIVE_SOLVER_TASK:
  NONE

ACTIVE_SURROGATE_TASK:
  NONE

CURRENT_REPOSITORY_ITEM:
  OWNER_DECISION_PENDING

SCI_ED_003:
  COMPLETE

STAGE_F:
  NOT_AUTHORIZED

STAGE_D:
  NOT_AUTHORIZED

VAL_CASE_002:
  NOT_STARTED

EXPERIMENTAL_COMMISSIONING:
  NOT_AUTHORIZED

PROTECTED_OR_HOLDOUT_SCORING:
  NOT_AUTHORIZED

NEW_GOVERNING_PHYSICS:
  NOT_YET_JUSTIFIED

PHYSICAL_VALIDATION:
  NOT_ESTABLISHED
```

Before the mechanism-selection ladder, check and qualify available data using
`provenance/AVAILABLE_DATA_AUTHORITY.json` and a validated task preflight. The
cadence is: available-data qualification → strongest eligible real-data comparison
→ residual/identifiability assessment → at most one model increment → new data only
for the named unresolved decision.

No solver, surrogate, validation-scoring, or mechanism-selection task is
active. Additional fitting or reuse of the same post-fit-derived cup-mass
evidence is not a route to independent physical validation.

## Parallel cross-solver closure-verification ladder

- `XSV-TAICHI-001`: saturated hydraulic closure parity; authorized as a
  temporary no-physics synthetic verification task.
- `XSV-TAICHI-002`: synthetic morphology and required-permeability-collapse
  screen; candidate only, not authorized.
- `XSV-TAICHI-003`: optional same-geometry pore-scale OpenFOAM/Taichi
  comparison; future possibility, not authorized.

This ladder distinguishes backend parity, analytical verification and closure
interface qualification from physical validation. It requires explicit unit,
reference-volume and provenance contracts. No stage substitutes for
independent physical data or changes the current scientific gate.

## Current bounded owner decision

The owner may choose `AUTHORIZE_STAGE_F_FEASIBILITY`, `DECLINE_EXECUTION`, or
`REQUEST_SPECIFIC_APPARATUS_OR_LABORATORY_CAPABILITY_INPUT`. None has been
exercised. The EXP-006/EXP-010 route is historical context, not an active,
commissioned, or authorized pilot.

## Next human-owner decision

The human owner may act only on the bounded SCI-ED-003 options above. Stage F
would require separate authorization; Stage D remains conditional, not sized,
not frozen, and not authorized.

Neither route is authorized by this roadmap. Experimental commissioning,
protected or holdout scoring, VAL-CASE-002, and new governing physics remain
unauthorized.

## Later, selected by evidence

| Observed residual or discriminating evidence | Candidate next increment |
|---|---|
| Pressure/flow residual correlated with measured bed compression | Fuller poroelastic deformation or storage |
| Flow decay correlated with measured particle or bed expansion | Swelling |
| Flow changes correlated with concentration or viscosity | Concentration-dependent viscosity |
| Turbidity, captured fines or deposition | Fines transport |
| Repeatable localized outlet-flow or extraction defects | Non-axisymmetric channeling or damage |
| Temperature-correlated hydraulic or extraction residual | Energy equation |
| Species-specific extraction disagreement | Multispecies chemistry |
| No discriminating evidence | Retain the simpler model and request better data |

These are evidence-dependent possibilities only. No mechanism is selected or
authorized.

## Cadence rule

```text
complete a verified mechanism
-> perform relevant real-data comparison
-> assess sensitivity and identifiability
-> select one next mechanism from residual evidence
```

> No two new evolving-puck governing mechanisms consecutively after WP03-001
> without an intervening relevant real-data comparison.

This is human-readable program guidance, not a CI or static-validation gate.
# SCI-ED-002 measurement dependency

The prospective Puckworks contract defines a future direct-measurement path; it does not change the solver roadmap or authorize commissioning. Predictor or mapping development cannot start from synthetic capacity. A later owner decision may commission all or part of the frozen design after review and merge.
