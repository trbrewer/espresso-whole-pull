# Scientific Modeling Forward Plan

- **Status date:** 14 August 2026
- **Status:** Enduring scientific handoff; `RP-D-LC-001b P1b` complete with seven admitted candidates at the exact P0/P1a source authority; the dependency remains open and no later phase is authorized here
- **Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`
- **Standing disposition:** `NO_NEW_PRODUCTION_PHYSICS_YET`

**Current next action:** P2a requires separate exact-head review and authorization; do not execute it under this task.

## 1. Executive diagnosis

Espresso Whole-Pull (EWP) is already a broad numerical modeling platform. Its principal bottleneck is mechanism discrimination, not the ability to add more equations. Substantial numerical verification and useful local reconstructions exist, but physical validation remains `NOT_ESTABLISHED`.

Every tested production family reverses the observed Waszkiewicz pressure ordering: the source gives `5 bar > 9 bar > 11 bar`, while the tested models give `11 bar > 9 bar > 5 bar`. The tested grind comparison also fails in direction of response. Locally successful reconstructions do not transfer reliably across pressures, grinds, or sources. Further unrestricted fitting of the existing evidence is therefore not the answer. The useful question is which missing physical mechanism creates the required resistance evolution and spatial behavior.

Under the documented fixed-geometry and fixed-viscosity interpretation, the source requires an 11-bar/5-bar apparent-conductance ratio of approximately `0.37–0.40`, equivalent to an approximately `2.5–2.7`-fold resistance increase. This is an apparent-conductance requirement under that convention, not a measured universal material law; geometry, viscosity, pressure-node, source-processing, and evidence-role qualifications remain controlling.

## 2. Current capabilities and evidence ceiling

The merged Foundation OpenFOAM 12 platform implements initially dry sharp-front wetting; prescribed and machine-coupled pressure; Darcy and Darcy–Forchheimer saturated flow; uniform, axial, and radial heterogeneity; evolving effective permeability; saturated quasi-static compaction; conservative one-solute transport and extraction; cup accumulation; and spatial and conservation diagnostics. The wider program also contains sensitivity and identifiability tools, Taichi/LBM and pore-scale closure investigations, source adapters, and governed comparison machinery.

These are implemented, numerically verified, or diagnostic capabilities as documented by their individual packages. They are not physical validation, and additional model complexity does not by itself improve predictive accuracy.

Completed discrimination work does not support fixed Darcy resistance, fixed Darcy–Forchheimer resistance, accepted quasi-static compaction, static lateral paths, measured-basket-conditioned machine dynamics, or plausible viscosity-only change as standalone explanations of the cross-pressure ordering. Static lateral paths failed as a standalone pressure-ordering explanation, but dynamically evolving lateral equalization, persistence, or localization remains scientifically open. Generic pressure-dependent resistance and the relaxing-resistance surrogate are mathematical capability survivors, not identified physical mechanisms.

The synthetic ensemble and processed real-coffee XCT programs found substantial realization variability, no resolved synthetic representative volume in the completed study, severe synthetic-to-real feature-domain separation, and no demonstrated external transfer from the synthetic closure to real coffee. No rights-cleared exact real flow masks were available for same-mask parity. Segmentation, resolution, subvolume, anisotropy, localization, and real-mask transformation remain incompletely adjudicated. The appropriate parallel evidence route is exact real-geometry access or acquisition, not another nominal single-realization synthetic run.

## 3. Program dependencies and gates

```text
RP-D-LC-001b P1b
  -> P2a candidate quantification
  -> P2b arithmetic selection and proposed freeze
  -> STOP for second exact-head review
  -> P3/P4 if separately authorized, or bounded stop
  -> SCI-LC-001A reduced lateral phase diagram
       -> selected regime boundaries only -> SCI-LC-001B 3-D confirmations

SCI-MD-002 common mechanism-signature ladder
  -> one evidence-selected mechanism, or additional measurement design
  -> WP04-TPM-001 only if transient poromechanics is distinguishably required

XSV-XCT-002 exact real-geometry access/closure proceeds in parallel
```

Entry gates are exact source identity, prospectively frozen protocol and decision rules, admissible evidence rights, and validated predecessor artifacts. Exit gates are canonical artifact validation, conservation and numerical checks appropriate to the task, explicit scientific disposition, and an unchanged claim ceiling. Stop on authority mismatch, invalid or noncanonical predecessors, exhausted survivors, absent rights, non-identifiability, or a result that requires changing frozen tolerances, geometry, forcing, candidate families, or decision rules. A null result is a valid exit and must not be rescued by retuning.

The independent-data gate limits physical-validation claims. It does not prohibit bounded, post-observation mechanism-discrimination work.

## 4. Priority 0 — close the current Puckworks dependency

### `RP-D-LC-001b`

Purpose: determine whether the WP6 lateral-coupling boundary inverse recovers an independently field-derived effective lateral-coupling number from a corrected, independently implemented, spatially resolved three-dimensional creeping-flow virtual fixture.

P1b fixed-step evidence completed on 14 August 2026 at the exact source bound by the accepted P0 and P1a authorities. Canonical validation admitted seven candidates (`w3_kz2`, `w3_kz3`, `w3_kz4`, `w5_kz2`, `w5_kz3`, `w5_kz4`, and `w7_kz2`); the other five candidates were rejected at P1a because their point estimates alone exceeded the artifact budget. The bounded disposition is:

```text
P1B_COMPLETE_ADMITTED_CANDIDATES
```

The Puckworks dependency remains open because candidate quantification has not passed P2a. This task stops after P1b. P2a, P2b, P3, P4, Stage B, and Paper 4 require separate authority. Neither an admitted candidate nor a null result establishes experimental validation, a measured real-puck `Xi`, or a universal physical `Xi`.

Claim ceiling:

```text
SYNTHETIC_DETERMINISTIC_GEOMETRY
SINGLE_PHASE_STEADY_CREEPING_FLOW
CROSS_MODEL_NUMERICAL_VERIFICATION
NO_EXPERIMENTAL_VALIDATION
NO_MEASURED_REAL_PUCK_XI
NO_UNIVERSAL_PHYSICAL_XI
NO_EVIDENCE_RUNG_PROMOTION
NO_STAGE_B_AUTHORIZATION
NO_PAPER_4_AUTHORIZATION
```

## 5. Priority 1 — first new EWP modeling program

### `SCI-LC-001A — Reduced lateral equalization and channeling phase diagram`

This is the first new EWP modeling task after the Puckworks dependency is closed or bounded. It asks: under what combinations of lateral conductance, axial resistance contrast, heterogeneity scale, machine response, and resistance-evolution timescale does puck nonuniformity decay, persist, or amplify?

Use a reduced multi-sector model before selected three-dimensional OpenFOAM work. It must include multiple lateral or circumferential sectors, an axial resistance per sector, local pressures and axial flows, neighboring-sector exchange, prescribed-pressure and machine-coupled modes, and optional resistance evolution introduced one mechanism at a time. A generic structure is `q_i = delta_p_i / R_i` and `q_i_to_j = G_L (p_i - p_j)`; use a better established repository formulation if one exists.

Sweep dimensionless lateral-to-axial conductance, initial resistance or permeability contrast, sector number and heterogeneity scale, machine compliance or response time, shot duration relative to equalization time, and selected resistance-evolution times only after the static map is understood.

Required observables are sector-flow fractions, flow inequality (coefficient of variation or equivalent), maximum/minimum flow ratio, lateral exchange flux, pressure asymmetry, perturbation decay or growth, persistence of dominant outlet regions, and local and aggregate extraction differences. Classify:

```text
LATERAL_EQUALIZATION
HETEROGENEITY_PERSISTS
HETEROGENEITY_AMPLIFIES
TRANSITION_OR_BISTABLE_REGION
```

Only transition cases, instability boundaries, and regions where reduced formulations disagree progress to three-dimensional simulation. A synthetic `RP-D-LC-001b` estimate may be a numerical anchor or consistency constraint, never a measured real-puck parameter.

## 6. Priority 1 — mechanism-specific resistance discrimination

### `SCI-MD-002 — Physical mechanism-signature ladder`

Run reduced, mechanism-specific models on one common admissible case matrix, separately comparing finite-rate poromechanics; swelling or dissolution-linked structural change; fines deposition and erosion; evolving lateral localization; machine-dynamics control; viscosity control; and the existing generic relaxing-resistance surrogate. Do not fit several new mechanisms simultaneously.

Evaluate established source-mapped pressure and grind/brew-ratio cases in this order: correct sign; pressure ordering; grind-response direction; residual shape and timing; cross-condition transfer; aggregate error. Lower RMSE cannot rescue the wrong sign or ordering.

Predeclare distinguishing evidence:

| Candidate | Distinguishing evidence |
|---|---|
| Transient poromechanics | Bed-height lag, consolidation time, pressure dependence, possible unloading response |
| Swelling/dissolution | Wetting- or extraction-linked delayed, mostly monotonic resistance growth |
| Fines | Turbidity, retained/deposited fines, grind sensitivity, erosion or recovery |
| Evolving localization | Increasing spatial flow variance and persistent high-flow paths |
| Machine dynamics | Upstream-to-basket pressure lag and apparatus-specific response |
| Viscosity | Temperature or concentration dependence without matching deformation |

Required disposition:

```text
TRANSIENT_POROMECHANICS_SELECTED
SWELLING_SELECTED
FINES_SELECTED
DYNAMIC_LOCALIZATION_SELECTED
COMBINED_MECHANISM_REQUIRED_BUT_NOT_IDENTIFIABLE
ADDITIONAL_DATA_REQUIRED
```

A combined-mechanism result authorizes measurement design, not simultaneous implementation.

## 7. Priority 1 in parallel — real-geometry closure

### `XSV-XCT-002 — Exact real-geometry closure and localization`

Pursue exact source binary flow domains, rights-cleared grayscale volumes with segmentation information, or a newly acquired well-characterized tamped-puck XCT dataset. Once an admissible mask exists, test same-mask cross-code permeability; the permeability tensor or directional response; transverse conductance; velocity localization and high-flow volume fraction; segmentation-threshold, voxel-resolution/coarsening, subvolume/crop, and boundary-condition sensitivity; multiple subvolumes or realizations; and whether a stable engineering volume exists. Do not block reduced EWP modeling while access proceeds.

## 8. Priority 2 — selected full-puck confirmation

### `SCI-LC-001B — Selected three-dimensional continuum confirmations`

Freeze a small set from `SCI-LC-001A`: one clearly equalizing case, one persistent case, one amplifying case if present, cases near important regime boundaries, and prescribed-pressure and machine-coupled versions of the most informative cases. Start with static local resistance. Add only the single evidence-selected dynamic law after reduced/full-model consistency is understood. Require conservation, representative mesh and timestep checks, rank consistency, and documented reduced/full-model comparison.

### `WP04-TPM-001 — Transient poromechanics` (conditional)

This is the strongest major production-physics candidate, but it is not automatic. Authorize it only if `SCI-MD-002` shows finite-rate deformation is materially and distinguishably required. Begin minimally with one displacement or volumetric-strain state, fluid storage or consolidation time, effective-stress-dependent porosity, permeability coupled to porosity or strain, machine coupling, and reversible or irreversible terms only where evidence requires them. Do not add fines, swelling, or damage in the same first branch.

Verification must include a one-dimensional consolidation or equivalent benchmark, an independent reduced or manufactured transient solution, recovery of the quasi-static limit, liquid-volume and storage conservation, timestep/mesh/MPI consistency, physical bounds and monotonicity, and unchanged predecessor behavior when disabled.

## 9. Priority 3 — conditional, evidence-selected work

- `WP04-FIN-001`: fines migration, requiring a distinct fines signature.
- `WP04-UW-001`: unsaturated wetting and trapped air, requiring an early-wetting residual the sharp-front limit cannot explain.
- `WP05-MSX-001`: multispecies extraction, requiring chemistry that the one-solute aggregate cannot represent.
- Thermal coupling, requiring a distinct unresolved thermal residual.

Each requires a measurement or residual that the preceding model cannot explain.

## 10. Compute strategy

Use analytical inversions and reduced models for broad screening. Reserve OpenFOAM for a small frozen set of regime boundaries and model-disagreement cases. Use controlled ensembles where realization variability matters; do not substitute one expensive nominal run for an ensemble question. Use the GPU for pore-scale ensembles and suitable reductions and CPU concurrency for independent cases, subject to live host limits and each task’s execution authority. Numerical resolution targets are design starting points, not validated universal specifications.

## 11. Experimental evidence priorities

Without changing any experimental authority, prioritize:

1. grinder-specific particle-size, packing, and permeability characterization;
2. synchronized pressure, flow, mass, and puck-deformation measurements;
3. time-dependent resistance observations separating consolidation, swelling, and fines;
4. spatial flow or local-extraction measurements;
5. synchronized whole-shot chemistry after the hydraulic mechanism is better constrained.

## 12. Explicit non-priorities

The program does not prioritize further unrestricted tuning of the locally successful 9-bar reconstruction; simultaneous addition of several mechanisms; another single-realization synthetic pore-scale study; large three-dimensional sweeps before reduced screening; thermal coupling merely because it is implementable; cup mass or extraction yield as proof of correct internal mechanisms; unrelated repository-wide refactoring; or new governance machinery without a demonstrated scientific or reader-facing need.

Administrative work remains proportional: correct material scientific errors, misleading claims, false-green checks, and genuine identity failures, without turning scientific work into a new assurance-framework project.

## 13. Claim boundaries

```text
PHYSICAL_VALIDATION: NOT_ESTABLISHED
GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION: NOT_ESTABLISHED
EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED
PROTECTED_OR_HOLDOUT_SCORING: NOT_AUTHORIZED
NO_NEW_PRODUCTION_PHYSICS_YET
```

Discovery, numerical verification, reconstruction, and physical validation remain distinct. Local reconstruction and cross-model synthetic verification do not raise the claim ceiling.

## 14. Restart block

1. Resolve mutable EWP and Puckworks identities from live Git: absolute checkout, branch, `HEAD`, `HEAD^{tree}`, `origin/main`, merge bases, relevant feature branches, PRs/issues, and worktree status. Never treat a SHA copied from this document or an older report as automatically current.
2. Read the repository instructions, current project state and claim ceiling, this plan, and the complete live protocol for the active task.
3. Keep the EWP runtime Puckworks lock unchanged unless a separate dependency-refresh task authorizes advancement.
4. For `RP-D-LC-001b`, validate the external bundle and exact P0/P1a-bound source before any phase action. Derive candidates from canonical records. Respect idempotency and stop at the authorized phase.
5. Preserve the claim ceiling: synthetic cross-model verification is not physical validation and does not measure a real-puck or universal `Xi`.
6. After the dependency is closed or bounded, the first new EWP modeling task is `SCI-LC-001A`.

Historical identities belong in the history snapshot and task evidence as labeled anchors. They are not substitutes for live identity resolution.
