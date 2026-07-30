# Post-WP03-001 Validation and Mechanism-Discrimination Plan

## 1. Objective and authority boundary

> Test the existing modular solver family against real espresso evidence,
> determine which components explain which observations, quantify uncertainty
> and non-identifiability, and use the residuals to select the next
> governing-physics increment.

This is an action plan, not authorization for protected-data access, holdout
opening, physical experimentation, apparatus commissioning, parameter fitting
or validation-status promotion.

WP03-001 is the appropriate starting point because machine and hydraulic
integration, static spatial heterogeneity and a first explicit mechanical
response are now implemented. Additional mechanisms increasingly compete to
explain the same pressure, flow, cup and spatial observations. Comparison now
has greater information value than another immediate mechanism.

## 2. Evidence ladder

- **Level 0 — Numerical verification.** Agreement with analytical,
  manufactured, regression, conservation and refinement references. This is
  already extensive.
- **Level 1 — Source reconstruction.** Reproduction of a source equation,
  fitted curve or case under its assumptions. This is not independent physical
  validation.
- **Level 2 — Independent component comparison.** A component prediction is
  compared with a real observation not used to determine that output, such as
  first drip, wetting-front position, steady flow, permeability, basket
  pressure or cup TDS.
- **Level 3 — Limited coupled within-apparatus comparison.** Several
  synchronized outputs from one apparatus are compared. The result remains
  apparatus- and source-specific.
- **Level 4 — Cross-condition or out-of-fit comparison.** A fixed model is
  tested against a materially different coffee, grind, basket, machine,
  pressure or recipe.
- **Level 5 — Preregistered holdout and transfer.** Future separately
  authorized work using unopened observations and predeclared gates. This plan
  does not authorize Level 5 execution.

Every result must name one evidence class:

```text
CODE_VERIFICATION
SOURCE_RECONSTRUCTION
POST_FIT_RECONSTRUCTION
WITHIN_RIG_COMPARISON
INDEPENDENT_COMPONENT_COMPARISON
CROSS_CONDITION_COMPARISON
HOLDOUT_INDEPENDENT
MECHANISM_DISCRIMINATION
TRANSFER_ASSESSMENT
```

The word “validated” is insufficient without a named level, component and
scope.

## 3. Source-specific validation adapter contract

Each adapter must provide:

```text
adapter_id
source_id
source_citation
evidence_level
rights_status
redistribution_status
apparatus_id
coffee_id
grinder_id
basket_geometry
dose
bed_depth
water_properties
temperature
pressure_node_definitions
flow_definition
mass_definition
first_drip_definition
TDS_method
EY_method
source_timebase
calibration_inputs
fitted_parameters
comparison_outputs
excluded_outputs
holdout_status
uncertainty
known_circularity
solver_configuration_mapping
output_mapping
claim_ceiling
```

Units and source definitions must be preserved exactly. R0 must not be
relabeled to imitate another apparatus, and missing values must remain
explicitly unavailable rather than invented.

Parameters must be classified as `SOURCE_MEASURED`, `SOURCE_DERIVED`,
`SOURCE_FITTED`, `CROSS_SOURCE_PRIOR`, `SYNTHETIC_FIXTURE`,
`FIXED_PREDECESSOR_VALUE`, `CALIBRATED_IN_THIS_CASE`, or `UNRESOLVED`.
Calibration parameters, comparison outputs, independent outputs and excluded
outputs must be listed separately. A comparison output cannot silently become
a calibration input.

## 4. Existing evidence inventory

The candidate inventory below is planning metadata derived from the existing
locked Puckworks integration and retained WP-0.3A review. It does not advance
the runtime dependency lock or copy restricted source series.

| Candidate | Target | Available / missing evidence | Class, rights and circularity | Suitability and action |
|---|---|---|---|---|
| Foster CT infiltration material | Wetting and first drip | Digitized/fitted timing context; source-definition and uncertainty limits remain | Source reconstruction; rights remain artifact-specific; fit circularity | Use only with explicit timing reconciliation and uncertainty; not a hydraulic holdout |
| Waszkiewicz pressure/flow and compaction material | Hydraulics and quasi-static compaction | Geometry, fitted curve and public pressure points; independent deformation/transfer data remain incomplete | Post-fit or within-rig comparison; CC-BY source material; soft circularity | Reconstruct pinned definitions, then reserve any admissible out-of-fit condition |
| Gagne DE1 material | Machine and whole-shot hydraulics | Telemetry context; geometry, uncertainty, definitions and redistribution gaps remain | Exploratory within-rig candidate; rights incomplete | Do not qualify until apparatus, node, uncertainty and rights gaps close |
| Schmieder, Angeloni and Perticarini extraction evidence | Aggregate chemistry | TDS/EY or endpoint context; hydraulic histories and method compatibility vary | Source-specific chemistry evidence; not hydraulic validation | Select only after method and hydraulic-history reconciliation |
| Moroney, Matias and Liang references | Extraction mathematics and observables | Non-protected mathematical or method-explicit references | Code verification / source reconstruction | Retain as verification support, not physical validation |
| Vaca Guerra material | Prior information | Inactive offline prior only | Rights/evidence constrained | Do not activate without separate review |
| Spatial evidence candidates | Radial flow and extraction | Currently incomplete spatial flow, depletion and uncertainty | Exploratory; potentially restricted | Request segmented flow, local chemistry, imaging and post-shot depletion |

The exact Puckworks experimental campaigns retained for planning are:

| ID | Exact campaign name | Validation relevance |
|---|---|---|
| EXP-001 | Synchronized whole-shot telemetry and cup chemistry | Coupled hydraulics and chemistry |
| EXP-002 | Initially dry puck infiltration and physical first drip | Wetting and first drip |
| EXP-003 | Grinder-specific particle-size, packing, and permeability map | Hydraulic inputs and transfer |
| EXP-004 | Poroelastic deformation, pressure, and flow | Compaction discrimination |
| EXP-005 | Time-dependent bed-mechanism discrimination (kappa(t)) | Evolving-mechanism discrimination |
| EXP-006 | Species-resolved fractional extraction | One-solute limitation and chemistry |
| EXP-007 | Spatial flow/channeling and local extraction | Spatial maldistribution |
| EXP-008 | Cross-machine, cross-grinder, cross-coffee replication | Transfer |
| EXP-009 | Bottom filter-paper mechanism study | Boundary/mechanism isolation |

Campaign preparation is permitted only as planning. Commissioning and
acquisition require separate authority.

## 5. First validation tranche

### Workstream A — Validation framework

Deliver a source-adapter schema and validator, common comparison-run
specification, calibration/comparison ledger, uncertainty-aware metric
library, machine-readable result bundle, standard report template and explicit
evidence-level output.

The recommended first implementation package is:

```text
VAL-001 — Source-specific validation adapter framework
and first component comparisons
```

Repository naming conventions may refine the identifier.

### Workstream B — Wetting and hydraulics

Deliver one first-drip comparison, one wetting-front or saturation-progression
comparison where suitable, one steady pressure–flow comparison, one
permeability comparison, and one machine pressure-node comparison where source
definitions permit.

### Workstream C — Extraction

Deliver one selected source reconstruction, one out-of-fit aggregate TDS or
extraction-yield comparison, and sensitivity to extractable fraction,
mass-transfer rate, dispersion and concentration ceiling. State the current
one-solute limitation explicitly.

### Workstream D — Mechanism discrimination

Run compatible constant-permeability, dissolution-indexed permeability,
machine-compliance, Darcy–Forchheimer, static-radial and quasi-static-
compaction branches on common source-specific cases. Compare first drip,
upstream and basket pressure, instantaneous and cumulative flow, cup mass,
TDS, extraction yield, predicted deformation and spatial extraction where
available.

Do not select the lowest fitted error after unrestricted retuning. Assess
residual shape, pressure/time/spatial dependence, parameter correlation,
identifiability, equifinality and transfer.

### Workstream E — Experimental design

Rank future measurements by expected information value, covering synchronized
telemetry and chemistry, wetting, PSD/packing/permeability, deformation,
time-dependent mechanisms, spatial flow/extraction, species-resolved
extraction and cross-apparatus transfer. No experiment is authorized here.

## 6. Initial comparison priorities

1. **Wetting and first drip:** reconcile definitions; report observed and
   predicted timing, front history where available, uncertainty, residual
   shape and claim ceiling.
2. **Saturated hydraulics and permeability:** report pressure, flow, geometry,
   permeability role, pressure nodes, justified Darcy/Forchheimer/compaction
   comparisons, uncertainty and residuals.
3. **Machine-coupled pressure and flow:** test emergent basket pressure,
   compliance and upstream resistance with synchronized nodes.
4. **Aggregate extraction:** follow hydraulic-history assessment and preserve
   the one-solute limitation.
5. **Spatial maldistribution:** begin with qualitative or bounded comparison
   until spatial observations and uncertainties are adequate.

## 7. Mechanism-discrimination matrix

The executable tranche must maintain a matrix whose observation rows include
first drip, wetting progression, basket/upstream pressure, pressure-flow
nonlinearity, early/late flow, flow-decay shape, cumulative water, cup mass,
TDS, extraction yield, bed-height change, spatial flow/extraction splits,
temperature dependence and turbidity/fines evidence.

Columns must include constant permeability, machine compliance,
dissolution-indexed permeability, Darcy–Forchheimer resistance, static radial
heterogeneity, quasi-static compaction, and unresolved swelling, viscosity,
fines and damage/channeling. Each entry records expected signature, current
solver capability, available evidence, discriminating strength, confounders
and missing measurements.

## 8. Uncertainty and identifiability

Assess source digitization, sensor and timing-definition uncertainty; dose and
geometry uncertainty; permeability, wetting, extraction and
machine-compliance uncertainty; parameter correlation; practical
identifiability; output sensitivity; and residual correlation. Use uncertainty
bands only when supported. Otherwise record:

```text
SOURCE_UNCERTAINTY_NOT_REPORTED
```

## 9. Residual-led next-physics decision

The tranche must end with one of:

```text
EXISTING_MODEL_FAMILY_SUFFICIENT_FOR_CURRENT_EVIDENCE
FULLER_POROELASTIC_STORAGE_JUSTIFIED
SWELLING_BRANCH_JUSTIFIED
VISCOSITY_BRANCH_JUSTIFIED
FINES_TRANSPORT_JUSTIFIED
NONAXISYMMETRIC_CHANNELING_JUSTIFIED
THERMAL_BRANCH_JUSTIFIED
MULTISPECIES_BRANCH_JUSTIFIED
ADDITIONAL_DATA_REQUIRED_BEFORE_NEW_PHYSICS
```

The rationale must use residuals, identifiability, cross-condition behavior,
uncertainty, information value and model complexity. It may not use
`NEW_PHYSICS_JUSTIFIED_BECAUSE_IMPLEMENTABLE`.

## 10. Exit criteria and retained outputs

The first tranche is complete after it produces a working adapter framework;
evidence/rights inventory; one wetting or first-drip, saturated hydraulic,
limited coupled pressure/flow and aggregate extraction comparison; explicit
calibration/comparison separation; uncertainty-aware metrics; sensitivity and
identifiability results; a mechanism matrix; ranked experimental-data request;
and a residual-led recommendation for one next physics increment.

Retain immutable input mappings, ledgers, traces, uncertainty-aware metrics,
residual plots, sensitivities, identifiability findings, mechanism matrix,
ranked data gaps and the recommendation. Universal validation and completion
of every campaign are not required.

## 11. Claim boundary

Every result must report numerical verification, source reconstruction,
component comparison, limited coupled comparison, cross-condition comparison,
holdout status and transfer status separately.

```text
GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION:
  NOT_ESTABLISHED

HOLDOUT_EXECUTION:
  NOT_AUTHORIZED_BY_THIS_PLAN

EXPERIMENTAL_COMMISSIONING:
  NOT_AUTHORIZED_BY_THIS_PLAN
```

A component may receive a bounded comparison status without promoting the
whole solver.
