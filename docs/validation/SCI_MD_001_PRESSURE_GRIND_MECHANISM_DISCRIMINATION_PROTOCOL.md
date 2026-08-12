# SCI-MD-001 pressure/grind mechanism-discrimination protocol

Status: `PROSPECTIVE_PROTOCOL_BEFORE_NEW_ADJUDICATIVE_CALCULATION`  
Issue: [#62](https://github.com/trbrewer/espresso-whole-pull/issues/62)

## Boundary and precedence

This exposed-evidence study prioritizes sign and ordering, residual structure,
physical plausibility, transfer, then scale error. It is
`POST_OBSERVATION_MECHANISM_DISCRIMINATION`, not a blind holdout. Accepted
immutable primitives are reused. Comparison outputs are never silently
calibration inputs; missing or nonpositive flow is unavailable, never floored.

Production-source/reduction changes are `NO_GOVERNING_PHYSICS_CHANGE`; new
existing-physics cases are `SOURCE_SCENARIO_CHANGE_ONLY`; standalone new
hypotheses are `GOVERNING_PHYSICS_CHANGE`, scope
`REDUCED_DIAGNOSTIC_ONLY`, `production_openfoam_integration: false`, and bear:

```text
REDUCED_DIAGNOSTIC_MODEL
POST_OBSERVATION_MECHANISM_SCREEN
NOT_PRODUCTION_OPENFOAM_PHYSICS
NOT_PHYSICAL_VALIDATION
```

## Arms and questions

- **P:** infer the pressure-dependent effective resistance needed for
  `5 bar > 9 bar > 11 bar` flow and mass.
- **G:** decompose the 0/3 grind-sign result into hydraulics,
  grind-to-structure, kinetics and extractable inventory.
- **T:** compare frozen early/middle/late residuals without a new optimized
  clock shift or per-source retuning.

## Frozen primary operators

- `C_app = Q / delta_p`, `R_app = delta_p / Q`, and, only where Darcy is
  admissible, `K_app = mu L Q / (A delta_p)` in SI.
- Ordering gates use measured basket-pressure histories where retained;
  nominal pressure is sensitivity-only. Strict pairwise comparisons define
  `FLOW_ORDER_5_GT_9_GT_11` and `MASS_ORDER_5_GT_9_GT_11`.
- A lower RMSE cannot override a failed sign gate.
- Grind contrast is consistently `fine - coarse` for both source and model;
  sign match is reported separately for brew ratios 1:1, 1:2 and 1:3.
- Source clock and the previously accepted +3 s presentation clock remain
  separate. Early/middle/late windows reuse predecessor definitions.
- Plausibility is classified as directly supported, extrapolated but
  defensible, outside supported range, or unresolved.
- Capability requires a nonzero-width parameter region, not an isolated
  numerical point; breadth and compensation warnings are retained.

## Analysis modes

1. Exact retained parameters.
2. A physically bounded capability envelope using deterministic sampling.
3. One-anchor transfer (9 bar for pressure; one declared brew ratio for
   grind), transparently post-observation and without condition-specific
   retuning.

## Candidate screens

Screen individually: generic pressure-dependent permeability (P1), finite-rate
poromechanics (P2), swelling resistance (P3), mobile/deposited fines (P4),
viscosity/rheology (P5), machine/boundary dynamics (P6), lateral two-path
surrogate (P7), grind-to-structure mapping (G1), and bimodal extraction (G2).
Each must recover a simpler limit, remain bounded/conservative where relevant,
and pass an independent limiting or numerical check. Pairwise screens require
individual characterization and a declared interaction; this protocol permits
only P2+P4 and G1+G2 if neither constituent alone is capable.

## Sampling and outcome taxonomy

Use analytical bounds plus deterministic log grids and base-2 low-discrepancy
sampling with seed 20260812; refine near sign changes. No black-box fit is a
primary method. Outcomes may include all categories listed in the machine
contract, including structural incapability, capability only outside plausible
bounds, equifinality, and an evidence-selected next task.

## OpenFOAM budget rule

Freeze a confirmatory matrix after reduced screening and before launch.
OpenFOAM is used only for missing primitives or selected current-physics
survivors. Maximum new confirmatory launches: 12, normally at 32 ranks, with
at most two concurrent cases. Infrastructure retries are recorded; scientific
failures are retained. Production solver source remains unchanged.

## Claim ceiling

```text
PHYSICAL_VALIDATION: NOT_ESTABLISHED
GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION: NOT_ESTABLISHED
PROTECTED_OR_HOLDOUT_SCORING: NOT_AUTHORIZED
EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED
```

## Post-freeze review correction

The prospective protocol above remains the historical freeze. Exact-head
review found that its outcome taxonomy omitted the distinct state
`CANDIDATE_MECHANISM_CAPABILITY_PLAUSIBILITY_UNRESOLVED`. The corrected
reduction adds that state; it is a post-freeze taxonomy correction, not a
prospectively frozen category. It also corrects the primary P1/P2 screens to
use retained measured terminal basket pressures rather than nominal labels.

The frozen base-2 low-discrepancy and adaptive-refinement methods were not
executed. Instead of adding post-result model work, the correction explicitly
downgrades P3 swelling, P4 fines, G1 structure mapping and G2 bimodal
extraction to `NOT_STRUCTURALLY_EXCLUDED_NOT_EVALUATED`. Only P1's 301-state
analytical grid and P2's 5,120-state one-state relaxing-resistance grid are
executed parameter ensembles. P2 is renamed
`P2_RELAXING_RESISTANCE_SURROGATE_POROMECHANICS_MOTIVATED`; it does not solve
solid equilibrium, storage, deformation or effective stress.
