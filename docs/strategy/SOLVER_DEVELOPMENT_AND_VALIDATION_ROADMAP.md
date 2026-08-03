# Solver Development and Validation Roadmap

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
```

## Current active phase

```text
POST-WP03-001 VALIDATION AND MECHANISM DISCRIMINATION
```

The first hydraulic/wetting corpus tranche, VAL-CORPUS-001, is complete,
approved, and merged. It satisfied the wetting, saturated-hydraulic, and
limited coupled pressure/flow exits, exposed reversed Waszkiewicz
cross-pressure ordering, and retained three finite-porosity numerical
failures. WP03-002 reproduced and corrected the numerical convergence-gate
defect; all three unchanged cases completed, but cross-pressure ordering
remained reversed. The aggregate extraction exit remains for VAL-CORPUS-002
after exact-head review closes WP03-002.

VAL-CORPUS-002 Stage A and Stage B0 are exact-head approved. Stage B1 is
complete as an exact frozen Experiment-7/H1 calibration candidate pending
final pre-B2 review. Its local reconstruction P2 rate is
`0.3439597024835067 s^-1`. OpenFOAM was executed for B1 calibration only.
Stage B2 retains 27 passing and 18 immutable typed-failed production
identities. The corrected Waszkiewicz P2 case passed, predecessor parity
remains 1,500/1,500, and all nine sensitivity identities passed. Frozen
governed reductions are complete pending exact-head review. This result is not
physical validation; protected scoring was not performed and new governing
physics remains unauthorized.

### Workstream 1 — Validation-case framework

Develop a common source-adapter schema, preserve source definitions, classify
rights and evidence, separate calibration from comparison, represent
uncertainty, calculate common metrics, and retain machine-readable bundles and
standard reports.

### Workstream 2 — Component comparisons

Compare wetting and first drip, steady pressure–flow behavior, permeability,
machine pressure nodes and delivery, quasi-static compaction, aggregate
extraction and cup chemistry, and spatial maldistribution where evidence
permits.

### Workstream 3 — Limited coupled comparisons

Compare multiple synchronized observables from the same apparatus or study.
Report the result as apparatus- and source-specific, not universal validation.

### Workstream 4 — Sensitivity and identifiability

Assess parameter influence and correlation, equifinality, uncertainty
propagation, observable information value, and transfer across pressure,
recipe and apparatus conditions.

### Workstream 5 — Mechanism discrimination

Compare compatible existing branches on common cases: constant permeability,
dissolution-indexed permeability, machine compliance, Darcy–Forchheimer
resistance, static radial heterogeneity and quasi-static compaction.

### Workstream 6 — Experimental design

Use unresolved sensitivities and residuals to rank future measurements. This
roadmap does not authorize commissioning or acquisition.

## Exit criteria

The tranche should produce at least:

1. one real-data wetting or first-drip comparison;
2. one real-data saturated hydraulic comparison;
3. one limited coupled pressure/flow comparison;
4. one aggregate extraction comparison;
5. explicit calibration-versus-comparison separation;
6. uncertainty bounds;
7. an identifiability assessment;
8. a mechanism-discrimination report;
9. a ranked next-physics recommendation; and
10. an updated experimental-data request.

Universal whole-solver validation is not an exit criterion.

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

This table guides investigation; it does not authorize a mechanism.

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
