# VAL-DATA-001 synchronized hydraulic-compaction measurement plan

**Task class:** `EXPERIMENTAL_DESIGN_AND_DATA_REQUEST_PLANNING`  
**Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`  
**Status:** `COMMISSIONING_NOT_AUTHORIZED`  
**Future evidence route:** `HUMAN_OWNER_PROSPECTIVE_SELECTION_REQUIRED`
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

## Prospective evidence route

The human owner must select and freeze one route before commissioning. Pilot
data are non-validation evidence by default. Ordinary comparison replicates
must not be called holdout evidence, and one observation must never both fit a
parameter and support an independent comparison of that fitted response.

| Route | Access and leakage control | Rights and claim consequence |
|---|---|---|
| Independent dataset unused for fitting: `INDEPENDENT_COMPONENT_VALIDATION` | All scored observations remain inaccessible to calibration and model selection; pilot and characterization evidence are separate. Access must be logged and independence frozen prospectively. | Rights must permit the comparison and reported products. The result can support only a bounded independent component-validation claim under separate authority, never general physical validation. |
| Calibration subset plus sealed scoring subset: `RECONSTRUCTION_OR_CALIBRATION` followed by `HOLDOUT_OR_TRANSFER` | Partition identities and hashes are frozen before fitting. Calibration access and later sealed-subset access are separate activities; holdout access, leakage controls, and scoring require separate authority. | Rights must cover both uses. Calibration results are not independent validation; only the untouched partition may support a later bounded holdout/transfer disposition. |
| Separate characterization/calibration campaign followed by a separately commissioned untouched dataset | Pilot and characterization records may inform apparatus and calibration, but the later dataset is separately commissioned, access-controlled, and untouched until its prospective comparison protocol is frozen. | Rights and custody must independently cover both campaigns. Only the later untouched dataset may be considered for `INDEPENDENT_COMPONENT_VALIDATION`. |

Final route disposition: `HUMAN_OWNER_PROSPECTIVE_SELECTION_REQUIRED`.

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
| Prescribed 5 bar | Required | `P_BASKET_BED_TOP_PA_GAUGE = 500000 Pa gauge`; record commanded waveform separately from achieved basket-top pressure | preparation, common origin, calibration state, replicate/block ID, prospectively frozen analysis role |
| Prescribed 9 bar | Required | `P_BASKET_BED_TOP_PA_GAUGE = 900000 Pa gauge`; record commanded waveform separately from achieved basket-top pressure | primary mid-range discrimination condition |
| Machine-coupled shot | Required | basket-top pressure is measured, not prescribed; record separate machine-side and basket-top pressure outputs | complete machine command/control program, initial hydraulic state, and all common metadata |
| Prescribed 11 bar | Optional model-form stress condition | `P_BASKET_BED_TOP_PA_GAUGE = 1100000 Pa gauge`; record commanded waveform separately from achieved basket-top pressure | must not be treated as sufficient alone for local compaction discrimination |

Actual control accuracy and apparatus feasibility remain
`APPARATUS_FEASIBILITY_REQUIRED`. Every run must bind its condition ID,
replicate ID, randomized order, preparation block, sensor/calibration IDs, and
predeclared evidence partition and analysis role.

For every prescribed-pressure condition, retain distinct fields for the
command or setpoint waveform, prescribed physical node, achieved measured
basket-top pressure, upstream measured pressure, ambient reference and zeroing
basis, and ramp, plateau, termination, control-deviation, and control-status
histories. Pressure-control tolerance and achievable architecture remain
`APPARATUS_FEASIBILITY_REQUIRED`; ramp and plateau definitions remain
`PILOT_REQUIRED`. For the machine-coupled condition, retain the complete
machine command/control program and initial hydraulic state. Free-flow and
shutoff characterization remain subject to the prospective parameter-role and
pilot decisions.

## Parameter and evidence-role ledger

Every final role must be frozen before commissioning. `Unused outputs` below
must remain unused for fitting if they will support an independent comparison.

| Item; definition and units | Current status and preferred independent source | Campaign/gap and future role | Permitted calibration evidence; unused comparison outputs; holdout restriction | Circularity consequence and unresolved disposition |
|---|---|---|---|---|
| `k0`, reference intrinsic permeability (m2) | uncertain model input; independent constant-head/pressure-flow characterization bound to the compared coffee, grinder, packing, and shot | EXP-003; measured input, calibration quantity, or withheld comparison input | Separate characterization may calibrate it; comparison-shot flow/pressure must remain unused if independently scored; sealed records require separate access authority | Fitting from the scored pressure-flow response destroys independence for that response; `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING` |
| `pc`, compaction pressure scale (Pa) | uncertain model input; independent mechanical pressure/deformation characterization | EXP-004; calibration quantity or withheld compaction parameter | Calibration subset may fit it; withheld pressure/deformation outputs remain untouched; holdout identities sealed prospectively | Fitting and scoring the same deformation curve is circular; `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING` |
| `phi0`, stress-free/reference porosity (1) | uncertain model input; independent geometry, dose, density, and packing characterization bound to each compared shot | EXP-003; measured input or calibration quantity | Characterization may supply it; compared-shot deformation/flow outputs remain unused for fitting; sealed partitions require separate authority | Inferring it from the scored hydraulic response removes independence; `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING` |
| `Cu`, machine/upstream compliance (m3/Pa) | uncertain machine input; independent volume-pressure or transient hydraulic characterization | machine-mode campaign gap | Separate machine characterization or declared calibration subset; withheld upstream/basket transient outputs remain unused; no holdout access here | Inferring `Cu` from the same scored transient confounds machine and puck response; `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING` |
| `Ru`, upstream hydraulic resistance (Pa s/m3) | uncertain machine input; independent line-resistance characterization | machine-mode campaign gap | Separate machine characterization or calibration subset; withheld pressure-drop/flow outputs remain unused; telemetry role must be declared | Telemetry-derived `Ru` cannot independently validate that same pressure-drop response; `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING` |
| `Qfree`, free-flow supply parameter (m3/s) | uncertain machine input; independent no-puck free-flow characterization | machine-mode campaign gap | Characterization may prescribe it; scored machine/puck flow remains unused; any sealed comparison is separately controlled | Derivation from scored coupled flow creates circular machine-boundary evidence; `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING` |
| `pshut`, shutoff-pressure supply parameter (Pa gauge) | uncertain machine input; independent safe shutoff/supply-curve characterization | machine-mode campaign gap | Characterization may prescribe it; scored upstream/basket pressures remain unused; sealed access requires separate authority | Derivation from the scored coupled pressure response destroys independence; `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING` |
| universal/finite-porosity model-form switch (categorical) | existing model-form switch; no fitting source | EXP-004 plus EXP-001 telemetry; future withheld model-form comparison | Calibration/model selection must use only a declared subset; all discriminator outputs in a sealed subset remain untouched | Choosing the branch on scored outputs invalidates independent discrimination; `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING` |
| viscosity, dynamic viscosity (Pa s) | measured/source-derived input; traceable temperature-dependent fluid property | EXP-001 temperature metadata | Independently prescribed or calculated before comparison; scored flow is not a property-fitting source; sealed output access prohibited | Back-calculating viscosity from scored flow makes hydraulic comparison circular; `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING` |
| density, fluid density (kg/m3) | measured/source-derived input; traceable gravimetric/volumetric or temperature-dependent property | EXP-001 | Independently prescribed for mass/volume conversion; scored mass and flow remain unused for fitting; provenance travels with partition | Estimating density to reconcile scored mass and volume flow compromises that comparison; `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING` |
| wetting/first-drip inputs, including dry-bed and inlet/timing quantities (declared native units) | uncertain/measured inputs; independent preparation metadata and physical marker characterization | EXP-002 | Pilot/characterization may define detection and inputs; withheld first-drip timing remains unused; ordinary replicates are not holdouts | Tuning wetting inputs to scored first drip prevents an independent timing claim; `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING` |
| downstream extraction/dissolution quantities used in a comparison (quantity-specific SI units) | existing inputs/outputs; independent chemistry, dose, and material characterization | EXP-001 and EXP-003 | Only explicitly declared calibration quantities may be fitted; cup chemistry and extraction outputs intended for comparison remain unused and separately partitioned | Fitting against the same chemistry/extraction response precludes independent scoring; `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING` |

When `k0`, `phi0`, PSD, or packing are supplied through EXP-003-style
characterization, their identifiers and provenance must bind to the exact
compared shot or declared material/preparation block. When `Cu`, `Ru`,
`Qfree`, or `pshut` are inferred from telemetry, that telemetry must be labeled
as calibration, characterization, or sealed comparison evidence before
access.

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
| Native sample interval, where channel capability supports it | approximately <= 20 ms | `SENSOR_SELECTION_REQUIRED`; bandwidth is separate |
| Inter-channel synchronization error | approximately <= 20 ms | `PILOT_REQUIRED`; latency is separate |
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

## Submission data-schema contract

This plan is a read-only extension of the templates under
`docs/data_requests/templates/` at locked Puckworks commit
`fc61c4670ec7bf801e40bb391aab16048b8da26b` and tree
`1d553e44ee2f7480a5df521560801b478618cc84`. It preserves the meanings of
`campaign_metadata.yml`, `apparatus.yml`, `shot_metadata.csv`,
`shot_timeseries.csv`, `calibration.csv`, `exclusions.csv`,
`file_manifest.csv`, and `chemistry_measurements.csv`. Puckworks remains
unchanged. A future submission must supply those templates plus the following
normalized VAL-DATA-001 extension files.

Common identifiers are non-empty strings. Primary keys are unique; foreign
keys must resolve within the same checksum-bound submission. Missing values
must be empty only when `missing_value_state` is one of `NOT_MEASURED`,
`NOT_APPLICABLE`, `BELOW_DETECTION`, `SENSOR_FAILURE`, or `MISSING_UNKNOWN`;
numeric zero is never a missing-value code.

| File/table | Primary key and foreign keys | Required fields and canonical units |
|---|---|---|
| `val_data_001_campaign.csv` | PK `campaign_id`; FK `puckworks_campaign_id` to the locked campaign identity | `campaign_id`, `puckworks_campaign_id`, `site_id`, `apparatus_id`, `evidence_partition_id`, `analysis_role`, `rights_id`, `schema_version`; analysis role is one of `PILOT_NON_VALIDATION`, `CHARACTERIZATION`, `CALIBRATION`, `COMPARISON`, `SEALED_HOLDOUT`, or `TRANSFER` |
| `val_data_001_conditions.csv` | PK `condition_id`; FK `campaign_id`, `apparatus_id` | `control_mode`, `prescribed_node`, `prescribed_pressure_pa_gauge`, `command_program_id`, `initial_hydraulic_state_id`, `ambient_reference_pa`, `zeroing_basis`, `ramp_definition`, `plateau_definition`, `termination_rule`, `control_tolerance_pa`, `missing_value_state` |
| `val_data_001_shots.csv` | PK `shot_id`; FK `campaign_id`, `condition_id`, `apparatus_id`, `replicate_id`, `block_id`, `evidence_partition_id` | coffee/grinder/basket/dose/preparation/temperature identifiers, randomized order, `raw_or_processed`, `inclusion_status`, `exclusion_reason`, `t0_event_code`, `t0_uncertainty_s`; this extends locked `shot_metadata.csv` rather than changing it |
| `val_data_001_signals.csv` | composite PK (`shot_id`, `signal_id`, `sample_index`); FK `shot_id`, `sensor_id`, `clock_id`, `calibration_id`, `source_file_id`, optional `parent_processing_id` | `native_timestamp`, `elapsed_time_s`, `native_value`, `native_unit`, `canonical_value`, `canonical_unit`, `physical_node`, `raw_or_processed`, `quality_flags`, `missing_value_state`, `clock_offset_s`, `clock_drift_s_per_s`, `sensor_latency_s`, `resampling_interval_s` |
| `val_data_001_controls.csv` | composite PK (`shot_id`, `control_sample_index`); FK `shot_id`, `command_program_id`, `clock_id`, `source_file_id` | `native_timestamp`, `elapsed_time_s`, commanded/setpoint value and unit, `prescribed_node`, achieved basket-top pressure in Pa gauge, measured upstream pressure in Pa gauge, ambient reference in Pa, `control_deviation_pa`, `control_status`, ramp/plateau/termination state |
| `val_data_001_flow_conversion.csv` | PK `conversion_id`; FK `shot_id`, `density_source_id`, optional `calibration_id` | native mass flow in g/s, native volume flow in mL/s when measured, canonical mass flow in kg/s, canonical volume flow in m3/s, density in kg/m3, temperature basis, conversion formula, density provenance, uncertainty record ID |
| `val_data_001_deformation.csv` | composite PK (`shot_id`, `location_id`, `sample_index`); FK `shot_id`, `sensor_id`, `calibration_id`, `reference_state_id`, `source_file_id` | native/canonical displacement and units, compression sign, `spatial_basis`, axial/radial coordinates, reference state, fixture-compliance correction ID, coffee-bed-only value, quality/missing flags, timing fields |
| `val_data_001_calibrations.csv` | PK `calibration_id`; FK `apparatus_id`, `sensor_id`, `source_file_id` | observable, native/canonical units, method, reference identity, timestamp, offset, scale, range, resolution, bandwidth, latency, drift, uncertainty-record ID, validity interval; extends locked `calibration.csv` |
| `val_data_001_files.csv` | PK `source_file_id`; optional FK `parent_source_file_id`, `processing_id` | relative filename, role, `raw_or_processed`, SHA-256, byte count, media type, license/rights ID, creator software identity, transformation identity; extends locked `file_manifest.csv` |
| `val_data_001_processing_lineage.csv` | PK `processing_id`; FKs to input `source_file_id` values and output `source_file_id` | software commit/tree, command or deterministic operation ID, parameters, input/output hashes, synchronization method, resampling method, operator role, timestamp |

The signal registry must include `P_MACHINE_UPSTREAM_RU_PA_GAUGE`,
`P_BASKET_BED_TOP_PA_GAUGE`, commanded pressure as a separate control signal,
`OUTLET_MASS_FLOW_G_S`, `OUTLET_VOLUME_FLOW_ML_S`, `DELIVERED_MASS_G`, and
location-specific `DEFORMATION_MM` or `BED_HEIGHT_MM`. It must preserve native
bar versus canonical Pa, native g/s or mL/s versus canonical SI, and density
and conversion provenance. A processed value never replaces its raw parent.
Evidence partition, analysis role, calibration links, quality flags, inclusion
status, exclusion rationale, checksums, and processing lineage are mandatory.

## Timebase, timing, calibration, and latency

All raw channels require native timestamps and a declared monotonic canonical
elapsed-time basis. The physical `t=0` event remains
`T0_EVENT_SELECTION_PILOT_REQUIRED`; retain every plausible raw marker,
including command onset, upstream-pressure onset, basket-pressure onset,
first detected outlet liquid, collection start, and instrument triggers.

The following are separate records and must not be collapsed:

- native sample interval, with the model-informed objective `<= 20 ms` where
  the channel can support it;
- useful measurement bandwidth, `SENSOR_SELECTION_REQUIRED` and
  `PILOT_REQUIRED`;
- inter-channel synchronization error, with model-informed objective
  `<= 20 ms`;
- sensor dynamic latency, characterized separately for each channel, with
  model-informed objective `<= 20 ms` where applicable;
- physical-`t=0` uncertainty, with model-informed objective `<= 20 ms` after
  pilot selection;
- processed resampling interval, prospectively selected and never used to
  imply native bandwidth, with model-informed objective `<= 20 ms` where
  justified.

Each approximately 20 ms objective is independently labeled
`MODEL_INFORMED_FUTURE_DESIGN_TARGET_NOT_VALIDATION_THRESHOLD`. If a single
hardware clock is unavailable, retain native timestamps and characterize
offset and drift without overwriting raw data. Pre- and post-session
calibration records, traceability, range, detection limit, hysteresis, drift,
zeroing, cross-talk, dynamic response, alignment, and latency must be retained.
Final sensor models and calibration procedures remain
`SENSOR_SELECTION_REQUIRED`.

## Deformation spatial and compliance basis

Acquire deformation or bed-height observations at inlet/upper-bed,
center/mid-bed, and outlet/lower-bed locations. A bulk-equivalent measurement
may replace those locations only when its spatial weighting and equivalence
are prospectively justified before acquisition. Record reference state,
location/coordinates, compression sign, alignment, and unloaded and loaded
bases. Independently characterize basket, optical window, fixture, sensor
mount, and reference-frame compliance; apparatus displacement must not be
reported as coffee-bed deformation. Feasibility remains
`APPARATUS_FEASIBILITY_REQUIRED`.

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
- [ ] Future evidence route selected prospectively.
- [ ] Parameter/evidence-role ledger frozen.
- [ ] Prescribed-pressure node and control protocol frozen.
- [ ] Submission data schemas accepted.
- [ ] Timing definitions and physical `t=0` basis accepted.
- [ ] Deformation spatial/compliance basis accepted.
- [ ] Leakage and access controls accepted if a sealed holdout route is used.
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
