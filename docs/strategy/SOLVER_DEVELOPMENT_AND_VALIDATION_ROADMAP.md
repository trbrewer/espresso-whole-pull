# Solver Development and Validation Roadmap

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

CURRENT_SCIENTIFIC_GATE:
  ADDITIONAL_INDEPENDENT_DATA_REQUIRED

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

No validation case, data-planning task, solver task, or mechanism-selection
task is active. Additional fitting or reuse of the same post-fit-derived
cup-mass evidence is not a route to independent physical validation.

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

## Current next scientific action

`SCI-LC-001A — Reduced lateral equalization and channeling phase diagram` is
the current next action. It begins with reduced multi-sector models and does
not inherit authority to resume `RP-D-LC-001b` or execute P3/P4. A possible
lower-conductance bridge investigation remains a distinct future tranche that
would require a newly frozen, better-resolved design; it is not a rescue of
the closed experiment.

## Next human-owner decision

The human owner may separately choose one of two evidence routes:

1. locate and qualify an admissible independent dataset; or
2. authorize and commission the synchronized measurement package already
   defined by VAL-DATA-001.

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
