# VAL-DATA-001 synchronized hydraulic-compaction measurement plan

**Task class:** `EXPERIMENTAL_DESIGN_AND_DATA_REQUEST_PLANNING`  
**Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`  
**Status:** `COMMISSIONING_NOT_AUTHORIZED`  
**Evidence class intended for a future separately authorized case:**
`INDEPENDENT_COMPONENT_VALIDATION`  
**Claim ceiling:** `VALIDATION_SUPPORT_ONLY_PHYSICAL_VALIDATION_NOT_ESTABLISHED`

This document is an implementation-ready planning input for a later human
commissioning decision. It does not authorize procurement, apparatus work,
data collection, calibration execution, model fitting, scoring, or a
validation case.

## Scientific questions and decisions enabled

The future package should determine whether synchronized pressure, flow/mass,
and deformation distinguish hydraulic resistance from compaction response;
whether the existing universal and finite-porosity branches produce resolvable
differences; which machine-side parameters remain practically confounded; and
whether an independently held-out dataset can support a bounded component
comparison. Results may support parameter/model-form discrimination or show
that additional data are required. A governing-physics increment would be
considered only after reproducible, uncertainty-aware residual structure
remains across independent conditions and cannot be explained by preparation,
apparatus, boundary-node, calibration, or existing-model uncertainty. A fit
improvement alone would not justify new physics.

## Campaign crosswalk

| Measurement need | Puckworks campaign | Coverage |
|---|---|---|
| Basket pressure, outlet flow/mass, temperature, cup chemistry | EXP-001 — Synchronized whole-shot telemetry and cup chemistry | Partial/core whole-shot telemetry |
| Physical first drip and initially dry infiltration | EXP-002 — Initially dry puck infiltration and physical first drip | Optional high-value wetting package |
| PSD, fines fraction, packing, porosity, permeability | EXP-003 — Grinder-specific particle-size, packing, and permeability map | Required input-characterization support |
| Deformation, pressure, flow | EXP-004 — Poroelastic deformation, pressure, and flow | Principal compaction-discrimination campaign |
| Time-dependent swelling/coupled-bed discrimination | EXP-005 — Time-dependent bed-mechanism discrimination (`kappa(t)`) | Deferred; not minimum package |
| Separate upstream machine-side pressure and machine response | No complete current campaign | `PUCKWORKS_MACHINE_MODE_CAMPAIGN_GAP` |

Future human disposition may extend EXP-001, extend EXP-004, define a new
Puckworks campaign, or retain an espresso-whole-pull-specific extension. None
is selected or commissioned here. EXP-001 through EXP-004 do not collectively
establish complete upstream machine-pressure coverage.

## Apparatus and physical nodes

The apparatus record must identify machine, hydraulic circuit, basket, coffee
bed, outlet collection, deformation reference, and every sensor location.
Four nodes are distinct and must never be substituted:

1. `P_MACHINE_UPSTREAM_RU_PA_GAUGE`: machine-side gauge pressure upstream of
   the declared upstream resistance `Ru`.
2. `P_BASKET_BED_TOP_PA_GAUGE`: basket pressure at the coffee-bed top.
3. `OUTLET_FLOW_ML_S` and `DELIVERED_MASS_G`: basket-bottom outlet flow and
   cumulative collected mass.
4. `BED_HEIGHT_MM` or `DEFORMATION_MM`: displacement relative to a declared
   unloaded/reference bed-height basis and spatial location.

Pressure sign is positive above ambient gauge pressure; outlet flow and mass
are positive leaving the basket; compression/deformation sign must be declared
once and retained. Temperature uses degrees Celsius with sensor location.
Physical first drip is elapsed time from the common shot origin to independently
detected physical liquid at the defined outlet plane.

## Minimum condition matrix

| Condition | Status | Control and measured nodes | Required role fields |
|---|---|---|---|
| Prescribed 5 bar | Required | prescribed boundary target; independently measured basket-top pressure, outlet flow/mass, and deformation | preparation, common origin, calibration state, replicate/block ID, comparison/holdout role |
| Prescribed 9 bar | Required | same nodes and metadata as 5 bar | primary mid-range discrimination condition |
| Machine-coupled shot | Required | measured machine-side pressure upstream of `Ru` and separate basket-top pressure, outlet flow/mass, deformation | machine response plus all common metadata |
| Prescribed 11 bar | Optional model-form stress condition | same prescribed-condition nodes | must not be treated as sufficient alone for local compaction discrimination |

Actual control accuracy and apparatus feasibility remain
`APPARATUS_FEASIBILITY_REQUIRED`. Every run must bind its condition ID,
replicate ID, randomized order, preparation block, sensor/calibration IDs, and
predeclared comparison or holdout role.

## Model-informed signal targets

Every value below is
`MODEL_INFORMED_FUTURE_DESIGN_TARGET_NOT_VALIDATION_THRESHOLD` (also the
short-form planning class `MODEL_INFORMED_FUTURE_DESIGN_TARGET`). It is not a
validated threshold, acceptance gate, demonstrated uncertainty, feasibility
claim, or procurement specification.

| Signal | Model-informed future design target | Resolution status |
|---|---:|---|
| Basket-top pressure | approximately <= 8 kPa | `SENSOR_SELECTION_REQUIRED`; `APPARATUS_FEASIBILITY_REQUIRED` |
| Machine-side pressure upstream of `Ru` | approximately <= 8 kPa | `SENSOR_SELECTION_REQUIRED`; campaign gap |
| Basket-bottom outlet flow | approximately <= 0.02 mL/s | `SENSOR_SELECTION_REQUIRED`; `PILOT_REQUIRED` |
| Cumulative delivered mass | approximately <= 0.5 g | `SENSOR_SELECTION_REQUIRED`; `PILOT_REQUIRED` |
| Bed height/deformation | approximately <= 0.05 mm | `SENSOR_SELECTION_REQUIRED`; `APPARATUS_FEASIBILITY_REQUIRED` |
| Common synchronization/raw sampling | approximately <= 20 ms | latency study required |
| Optional physical first drip | approximately <= 0.02 s | `SENSOR_SELECTION_REQUIRED`; `PILOT_REQUIRED` |

## Metadata and preparation controls

Record apparatus identifiers and revisions; hydraulic schematic and node
coordinates; basket geometry and coffee-bed hydraulic area; dose, dry bed
depth, post-preparation bed height, headspace, water temperature, ambient
pressure, and relevant line temperature; coffee identity and rights status;
roast and age metadata; grinder identity/settings; PSD/fines characterization;
distribution, leveling, tamp protocol and force record; operator/automation
role; timing; and deviations. Real values remain unresolved until authorized
acquisition.

## Timebase, calibration, and latency

All raw channels require one monotonic elapsed-time basis with an explicit
physical `t=0` event. If a single hardware clock is unavailable, retain native
timestamps and document offset, drift, resampling, and latency characterization
without overwriting raw data. Pre- and post-session calibration records,
traceability, range, detection limit, hysteresis, drift, zeroing, cross-talk,
dynamic response, alignment, and clock latency must be retained. Final sensor
models and calibration procedures remain `SENSOR_SELECTION_REQUIRED`.

## Uncertainty-budget headings

The future uncertainty budget must separately cover calibration reference,
resolution/quantization, repeatability, drift, latency and synchronization,
dynamic response, spatial/node placement, temperature dependence, density
conversion, collection/retention/evaporation, deformation reference and
alignment, preparation variability, between-block variability, and processing
effects. Numerical values require pilot and calibration evidence and remain
`PILOT_REQUIRED`.

## Pilot and replication design

Pilot objectives are to demonstrate node accessibility, signal range,
bandwidth, clock synchronization, safe operation, preparation repeatability,
missingness/failure modes, and deformation-reference stability. They remain
`PILOT_REQUIRED` and `COMMISSIONING_NOT_AUTHORIZED`.

Final replicates are `DESIGN_CALCULATION_REQUIRED`. The later calculation must
use pilot estimates of within-condition and between-block variance, the
smallest predeclared discrimination contrast, desired interval width or power,
multiple-condition structure, anticipated exclusions, and independent holdout
allocation. It must document assumptions and sensitivity to them; this plan
does not invent a replicate count or power value.

Randomize condition order within feasible thermal/preparation blocks. Predefine
blocks for day/session, coffee batch, grinder state, operator or automation
state, and apparatus/calibration state. Record order and deviations. Never
silently replace failed or excluded runs.

## Data layout and integrity

Retain separate checksum-bound areas:

- `raw/`: immutable instrument-native files and calibration outputs;
- `processed/`: synchronized, unit-normalized, quality-flagged signals with
  transformation provenance;
- `derived/`: declared features, uncertainty propagation, comparisons, and
  figures.

Provide a data dictionary containing signal name, physical definition, units,
sign, node/spatial basis, native clock, sampling, missing-value code,
calibration ID, and processing lineage. Preserve all replicates and all failed
or excluded runs with reason codes. Never smooth, overwrite, or replace raw
files. Distinguish prescribed targets from measured quantities.

## Quality control, failures, and exclusions

Predeclare checks for clock monotonicity, dropped/duplicate samples, saturation,
range, zero/reference drift, calibration validity, sensor-node identity,
collection continuity, mass monotonicity where physically applicable,
deformation reference, metadata completeness, and protocol deviations.
Equipment failure, invalid calibration, lost synchronization, wrong condition,
or documented preparation failure may exclude a run only under a preregistered
rule. Preserve the run, raw files, flags, and rationale. Scientific disagreement
is never an exclusion reason.

## Preregistered analysis, fitting separation, and holdout

Before access to comparison outcomes, preregister time origin, filtering and
resampling, feature definitions, uncertainty propagation, missingness,
exclusions, parameter/model-form metrics, thresholds, and interpretation.
Separate prescribed quantities, independently measured inputs, calibration
quantities, comparison outputs, contextual metadata, and excluded quantities.

Allocate holdout units or blocks before fitting and seal their identities and
files. Calibration and model selection must not use holdout observations.
Holdout access and scoring require separate authority; they are not authorized
here. Downstream decisions must distinguish inadequate measurement information,
parameter confounding, model-form discrimination, and persistent structured
residuals.

## Rights, privacy, and deposit

Before commissioning, document ownership, participant/operator privacy,
apparatus confidentiality, redistribution license, source rights, consent where
applicable, embargo, public/private field partition, and repository destination.
Deposit must include checksums, immutable raw files, processed/derived lineage,
data dictionary, protocols, calibration records, exclusions, software identity,
and citation metadata. Rights must permit the intended independent comparison.

## Commissioning-readiness checklist

- [ ] Human owner issues separate commissioning authority.
- [ ] Machine-mode campaign gap receives a documented human disposition.
- [ ] Apparatus and node feasibility: `APPARATUS_FEASIBILITY_REQUIRED`.
- [ ] Sensors and calibration chain: `SENSOR_SELECTION_REQUIRED`.
- [ ] Pilot protocol and evidence: `PILOT_REQUIRED`.
- [ ] Replication and holdout calculation: `DESIGN_CALCULATION_REQUIRED`.
- [ ] Randomization, blocks, exclusions, and preregistered analysis frozen.
- [ ] Rights, privacy, custody, and deposit plan accepted.
- [ ] Safety and operational review accepted by responsible humans.
- [ ] Evidence roles and claim ceiling recorded.

Until every required item is resolved, status remains
`COMMISSIONING_NOT_AUTHORIZED`.
