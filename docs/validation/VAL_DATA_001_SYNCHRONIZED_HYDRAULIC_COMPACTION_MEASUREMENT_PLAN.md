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

The frozen protocol classification is historical fact and is not a proposed
future evidence role. Every prospective role must be frozen before
commissioning.

| Item; definition and units | `CURRENT_VAL_CASE_001_CLASSIFICATION` | Preferred source and campaign/gap | `PROSPECTIVE_VAL_DATA_001_ROLE`; calibration/comparison restriction |
|---|---|---|---|
| `k0`, reference intrinsic permeability (m2) | `CALIBRATED_PREVIOUSLY` | independent constant-head/pressure-flow characterization bound to the compared material and shot; EXP-003 | `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING`; if recalibrated, the same pressure/flow observations cannot support an independent fitted-response comparison |
| `pc`, compaction pressure scale (Pa) | `SOURCE_DERIVED` | independent mechanical pressure/deformation characterization; EXP-004 | `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING`; a fitted deformation curve cannot independently validate `pc` |
| `phi0`, stress-free/reference porosity (1) | `FIXED_PREDECESSOR_VALUE` | independently measured geometry, dose, density, and packing bound to the shot; EXP-003 | `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING`; hydraulic inference from scored outputs destroys independence |
| `Cu`, upstream compliance (m3/Pa) | `UNCERTAIN_MODEL_INPUT` | independent volume-pressure or transient characterization; machine-mode campaign gap | `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING`; telemetry must be assigned to characterization, calibration, or untouched comparison before access |
| `Ru`, upstream resistance (Pa s/m3) | `UNCERTAIN_MODEL_INPUT` | independent line-resistance characterization; machine-mode campaign gap | `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING`; telemetry-derived `Ru` cannot validate the same pressure-drop response |
| `Qfree`, free-flow supply parameter (m3/s) | `UNCERTAIN_MODEL_INPUT` | independent no-puck free-flow characterization; machine-mode campaign gap | `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING`; coupled-shot scored flow cannot also determine `Qfree` |
| `pshut`, shutoff-pressure supply parameter (Pa gauge) | `UNCERTAIN_MODEL_INPUT` | independent safe supply-curve characterization; machine-mode campaign gap | `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING`; scored coupled pressure cannot also determine `pshut` |
| mechanics branch, universal/finite-porosity switch (categorical) | `MODEL_FORM_SWITCH` | EXP-004 deformation plus EXP-001 telemetry | `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING`; model selection and untouched model-form comparison must use route-permitted separate evidence |
| viscosity, dynamic viscosity (Pa s) | `SOURCE_MEASURED`; `NOT_VARIED` | traceable temperature-dependent fluid property; EXP-001 metadata | independently prescribed input; scored flow must not be used to back-calculate it |
| density, fluid density (kg/m3) | `SOURCE_MEASURED`; `NOT_VARIED` | traceable gravimetric/volumetric or temperature-dependent property; EXP-001 | independently prescribed conversion input; scored mass/flow must not tune it |
| wetting permeability (m2) | `CALIBRATED_PREVIOUSLY`; `NOT_VARIED` | independently characterized dry-bed/wetting input; EXP-002 and EXP-003 | `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING`; first-drip comparison observations must remain unused if the response is claimed independent |
| extraction constants (quantity-specific SI units) | `FIXED_PREDECESSOR_VALUE`; `NOT_VARIED` | independent chemistry/material sources; EXP-001 and EXP-003 | `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING`; scored chemistry/extraction cannot both fit and validate the same constants |
| additional future wetting/timing inputs (field-specific units) | not part of the frozen varied-parameter inventory; listed separately | preparation metadata and physical marker characterization; EXP-002 | `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING`; pilot evidence is non-validation by default |
| additional future chemistry/dissolution quantities (field-specific units) | not part of the frozen varied-parameter inventory; listed separately | independent chemistry, dose, and material characterization; EXP-001 and EXP-003 | `ROLE_FREEZE_REQUIRED_BEFORE_COMMISSIONING`; comparison outputs intended for scoring remain unused for fitting |

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

Common identifiers are non-empty strings. Primary keys are unique. Each
foreign key resolves through the matrix below; there are no implied parents.
Numeric zero is never a missing-value code.

### Exact normalized tables

| File/table | Primary key | Exact required fields |
|---|---|---|
| `val_data_001_evidence_routes.csv` | `route_id` | `route_id`, `selected_route`, `calibration_evidence_class`, `scoring_evidence_class`, `prospective_freeze_resource_id`, `human_owner_disposition_resource_id`, `rights_policy_resource_id`, `access_policy_resource_id` |
| `val_data_001_campaigns.csv` | `campaign_id` | `campaign_id`, `puckworks_campaign_id`, `site_id`, `apparatus_id`, `route_id`, `schema_version` |
| `val_data_001_evidence_partitions.csv` | `evidence_partition_id` | `evidence_partition_id`, `campaign_id`, `route_id`, `analysis_role`, `evidence_class`, `sealed_status`, `partition_manifest_sha256`, `seal_timestamp_utc`, `custodian_resource_id`, `access_policy_resource_id`, `rights_resource_id` |
| `val_data_001_replicates.csv` | `replicate_id` | `replicate_id`, `campaign_id`, `condition_id`, `block_id`, `replicate_sequence`, `randomization_sequence`, `evidence_partition_id` |
| `val_data_001_blocks.csv` | `block_id` | `block_id`, `campaign_id`, `block_type`, `block_label`, `session_start_utc`, `coffee_lot_resource_id`, `grinder_state_resource_id`, `operator_role_resource_id`, `apparatus_state_resource_id`, `calibration_set_id` |
| `val_data_001_resources.csv` | (`resource_type`, `resource_id`) | `resource_type`, `resource_id`, `definition`, `source_file_id`, `rights_resource_id` |
| `val_data_001_conditions.csv` | `condition_id` | `condition_id`, `campaign_id`, `apparatus_id`, `control_mode`, `prescribed_node`, `prescribed_pressure_pa_gauge`, `command_program_resource_id`, `initial_hydraulic_state_resource_id`, `ambient_reference_pa`, `zeroing_basis`, `ramp_definition`, `plateau_definition`, `termination_rule`, `control_tolerance_pa`, `missing_value_state` |
| `val_data_001_shots.csv` | `shot_id` | `shot_id`, `campaign_id`, `condition_id`, `apparatus_id`, `replicate_id`, `block_id`, `evidence_partition_id`, `coffee_lot_resource_id`, `grinder_resource_id`, `basket_resource_id`, `dose_g`, `dry_bed_depth_mm`, `preparation_protocol_resource_id`, `brew_temperature_c`, `raw_or_processed`, `inclusion_status`, `exclusion_reason`, `t0_event_code`, `t0_uncertainty_s` |
| `val_data_001_signals.csv` | (`shot_id`, `signal_id`, `sample_index`) | `shot_id`, `signal_id`, `sample_index`, `sensor_resource_id`, `clock_resource_id`, `calibration_id`, `source_file_id`, `processing_id`, `native_timestamp`, `elapsed_time_s`, `native_value`, `native_unit`, `canonical_value`, `canonical_unit`, `physical_node`, `raw_or_processed`, `quality_flags`, `missing_value_state`, `clock_offset_s`, `clock_drift_s_per_s`, `sensor_latency_s`, `resampling_interval_s` |
| `val_data_001_controls.csv` | (`shot_id`, `control_sample_index`) | `shot_id`, `control_sample_index`, `command_program_resource_id`, `clock_resource_id`, `source_file_id`, `processing_id`, `native_timestamp`, `elapsed_time_s`, `commanded_pressure_value`, `commanded_pressure_unit`, `prescribed_node`, `basket_pressure_signal_id`, `upstream_pressure_signal_id`, `control_deviation_pa`, `control_status`, `control_phase` |
| `val_data_001_flow_conversions.csv` | `conversion_id` | `conversion_id`, `shot_id`, `density_source_resource_id`, `calibration_id`, `source_file_id`, `native_mass_flow_g_s`, `native_volume_flow_ml_s`, `canonical_mass_flow_kg_s`, `canonical_volume_flow_m3_s`, `density_kg_m3`, `density_temperature_c`, `conversion_formula`, `processing_id` |
| `val_data_001_deformation.csv` | (`shot_id`, `location_id`, `sample_index`) | `shot_id`, `location_id`, `sample_index`, `sensor_resource_id`, `calibration_id`, `reference_state_resource_id`, `fixture_compliance_resource_id`, `source_file_id`, `processing_id`, `native_timestamp`, `elapsed_time_s`, `native_displacement_value`, `native_displacement_unit`, `canonical_displacement_m`, `compression_sign`, `spatial_basis`, `axial_coordinate_m`, `radial_coordinate_m`, `coffee_bed_displacement_m`, `quality_flags`, `missing_value_state` |
| `val_data_001_calibrations.csv` | `calibration_id` | `calibration_id`, `calibration_set_id`, `apparatus_id`, `sensor_resource_id`, `source_file_id`, `observable_code`, `native_unit`, `canonical_unit`, `calibration_method`, `reference_resource_id`, `calibration_timestamp_utc`, `offset`, `scale`, `range_min`, `range_max`, `resolution`, `bandwidth_hz`, `latency_s`, `drift_per_s`, `uncertainty_resource_id`, `valid_from_utc`, `valid_to_utc` |
| `val_data_001_files.csv` | `source_file_id` | `source_file_id`, `parent_source_file_id`, `processing_id`, `relative_filename`, `file_role`, `raw_or_processed`, `sha256`, `byte_count`, `media_type`, `rights_resource_id`, `creator_software_resource_id` |
| `val_data_001_processing_lineage.csv` | `processing_id` | `processing_id`, `input_source_file_id`, `output_source_file_id`, `software_commit`, `software_tree`, `operation_resource_id`, `parameter_record`, `synchronization_method`, `resampling_method`, `operator_role_resource_id`, `processing_timestamp_utc` |

The locked Puckworks bindings are exact: `campaigns.puckworks_campaign_id`
references `docs/data_requests/experimental_campaigns.yml` campaign key
`$.campaigns[*].campaign_id`; `campaigns.site_id` references
`docs/data_requests/templates/campaign_metadata.yml` key `$.site_id`; and
`campaigns.apparatus_id`, `conditions.apparatus_id`, and
`calibrations.apparatus_id` reference
`docs/data_requests/templates/apparatus.yml` key `$.apparatus_id`, all at the
locked commit and tree above. The local `campaign_id`, `shot_id`, and
`replicate_id` values also populate the same-named columns in locked
`shot_metadata.csv`; this is an equality/export binding, not an additional
foreign-key parent.

### Foreign-key resolution matrix

Cardinality is child-to-parent. `NOT NULL` means every child row requires
exactly one parent; `NULLABLE` states the sole permitted null condition.

| Child field | Exact parent | Cardinality/null rule |
|---|---|---|
| `campaigns.puckworks_campaign_id` | locked `experimental_campaigns.yml` `$.campaigns[*].id` | many-to-one, `NOT NULL` |
| `campaigns.site_id` | locked `campaign_metadata.yml` `$.site_id` | many-to-one, `NOT NULL` |
| `campaigns.apparatus_id`, `conditions.apparatus_id`, `calibrations.apparatus_id` | locked `apparatus.yml` `$.apparatus_id` | many-to-one, `NOT NULL` |
| `campaigns.route_id`, `evidence_partitions.route_id` | `val_data_001_evidence_routes.csv.route_id` | many-to-one, `NOT NULL` |
| `evidence_partitions.campaign_id`, `replicates.campaign_id`, `blocks.campaign_id`, `conditions.campaign_id`, `shots.campaign_id` | `val_data_001_campaigns.csv.campaign_id` | many-to-one, `NOT NULL` |
| `replicates.condition_id` | `val_data_001_conditions.csv.condition_id` | many-to-one, `NOT NULL` |
| `replicates.block_id`, `shots.block_id` | `val_data_001_blocks.csv.block_id` | many-to-one, `NOT NULL` |
| `replicates.evidence_partition_id`, `shots.evidence_partition_id` | `val_data_001_evidence_partitions.csv.evidence_partition_id` | many-to-one, `NOT NULL` |
| `shots.condition_id` | `val_data_001_conditions.csv.condition_id` | many-to-one, `NOT NULL` |
| `shots.replicate_id` | `val_data_001_replicates.csv.replicate_id` | one-to-one within a condition, `NOT NULL` |
| `shots.apparatus_id` | locked `apparatus.yml` `$.apparatus_id` | many-to-one, `NOT NULL` |
| `signals.shot_id`, `controls.shot_id`, `flow_conversions.shot_id`, `deformation.shot_id` | `val_data_001_shots.csv.shot_id` | many-to-one, `NOT NULL` |
| every field ending `_resource_id` | `val_data_001_resources.csv.resource_id`, paired with the field-implied `resource_type` | many-to-one; `NOT NULL` except `resources.rights_resource_id`, which may be null only for a public-domain resource documented as `PUBLIC_DOMAIN` |
| `signals.calibration_id`, `flow_conversions.calibration_id`, `deformation.calibration_id` | `val_data_001_calibrations.csv.calibration_id` | many-to-one; null only when `missing_value_state=NOT_APPLICABLE` and the signal definition proves no calibration applies |
| `calibrations.calibration_set_id`, `blocks.calibration_set_id` | `val_data_001_resources.csv.resource_id` with `resource_type=CALIBRATION_SET` | many-to-one, `NOT NULL` |
| every `source_file_id`, `input_source_file_id`, `output_source_file_id` | `val_data_001_files.csv.source_file_id` | many-to-one, `NOT NULL` |
| `files.parent_source_file_id` | `val_data_001_files.csv.source_file_id` | many-to-one; null only for an instrument-native root file |
| every `processing_id` | `val_data_001_processing_lineage.csv.processing_id` | many-to-one; null only when `raw_or_processed=RAW_NATIVE` |
| `controls.basket_pressure_signal_id`, `controls.upstream_pressure_signal_id` | `val_data_001_signals.csv.signal_id` within the same `shot_id` | many-to-one; basket reference `NOT NULL`; upstream reference null only for prescribed mode when upstream pressure is `NOT_MEASURED` |

### Controlled enumerations

| Field | Permitted values |
|---|---|
| `selected_route` | `INDEPENDENT_COMPONENT_VALIDATION`; `CALIBRATION_THEN_HOLDOUT_OR_TRANSFER`; `SEPARATE_CHARACTERIZATION_THEN_INDEPENDENT_VALIDATION` |
| `evidence_class` | `NOT_APPLICABLE`; `PILOT_NON_VALIDATION`; `CHARACTERIZATION`; `RECONSTRUCTION_OR_CALIBRATION`; `INDEPENDENT_COMPONENT_VALIDATION`; `HOLDOUT_OR_TRANSFER` |
| `analysis_role` | `PILOT_NON_VALIDATION`; `CHARACTERIZATION`; `CALIBRATION`; `COMPARISON`; `SEALED_SCORING`; `TRANSFER` |
| `control_mode` | `PRESCRIBED_BASKET_PRESSURE`; `MACHINE_COUPLED` |
| `prescribed_node` | `P_BASKET_BED_TOP_PA_GAUGE`; `NOT_APPLICABLE_MACHINE_COUPLED` |
| `raw_or_processed` | `RAW_NATIVE`; `PROCESSED_SYNCHRONIZED`; `DERIVED` |
| `inclusion_status` | `INCLUDED`; `EXCLUDED_PREDECLARED_RULE`; `FAILED_RETAINED`; `PENDING_QC` |
| `missing_value_state` | `PRESENT`; `NOT_MEASURED`; `NOT_APPLICABLE`; `BELOW_DETECTION`; `SENSOR_FAILURE`; `MISSING_UNKNOWN` |
| `sealed_status` | `NOT_APPLICABLE`; `UNSEALED_CALIBRATION`; `SEALED_UNACCESSED`; `AUTHORIZED_OPENED`; `CLOSED_AFTER_SCORING` |
| `physical_node`/signal code | `P_MACHINE_UPSTREAM_RU_PA_GAUGE`; `P_BASKET_BED_TOP_PA_GAUGE`; `OUTLET_MASS_FLOW_G_S`; `OUTLET_VOLUME_FLOW_ML_S`; `DELIVERED_MASS_G`; `DEFORMATION_UPPER_M`; `DEFORMATION_MID_M`; `DEFORMATION_LOWER_M`; `BED_HEIGHT_BULK_M`; `FIRST_DRIP_EVENT_S` |
| `control_status` | `PENDING_FEASIBILITY`; `WITHIN_FROZEN_TOLERANCE`; `OUTSIDE_FROZEN_TOLERANCE`; `CONTROL_FAILURE` |
| `control_phase` | `PRE_SHOT`; `RAMP`; `PLATEAU`; `TERMINATION`; `POST_SHOT` |
| `block_type` | `SESSION`; `COFFEE_LOT`; `GRINDER_STATE`; `OPERATOR_STATE`; `APPARATUS_CALIBRATION_STATE` |
| `location_id` | `UPPER_BED`; `MID_BED`; `LOWER_BED`; `BULK_EQUIVALENT` |
| `resource_type` | `ACCESS_POLICY`; `APPARATUS_STATE`; `CALIBRATION_SET`; `COMMAND_PROGRAM`; `CUSTODIAN`; `DENSITY_SOURCE`; `FIXTURE_COMPLIANCE`; `FREEZE_IDENTITY`; `GRINDER`; `GRINDER_STATE`; `HUMAN_DISPOSITION`; `HYDRAULIC_INITIAL_STATE`; `OPERATION`; `OPERATOR_ROLE`; `PREPARATION_PROTOCOL`; `REFERENCE_STATE`; `REFERENCE_STANDARD`; `RIGHTS`; `SENSOR`; `SOFTWARE`; `UNCERTAINTY`; `COFFEE_LOT`; `BASKET`; `CLOCK` |

### Route-conditional partition representation

- `INDEPENDENT_COMPONENT_VALIDATION`: one or more partitions may represent
  acquisition logistics, but every scored partition has
  `analysis_role=COMPARISON`,
  `evidence_class=INDEPENDENT_COMPONENT_VALIDATION`, and
  `sealed_status=NOT_APPLICABLE`. No `CALIBRATION` or `SEALED_SCORING`
  partition is required or permitted within that scored dataset.
  Its route record uses `calibration_evidence_class=NOT_APPLICABLE` and
  `scoring_evidence_class=INDEPENDENT_COMPONENT_VALIDATION`.
- `CALIBRATION_THEN_HOLDOUT_OR_TRANSFER`: at least one partition has
  `analysis_role=CALIBRATION`,
  `evidence_class=RECONSTRUCTION_OR_CALIBRATION`, and
  `sealed_status=UNSEALED_CALIBRATION`; at least one disjoint partition has
  `analysis_role=SEALED_SCORING`, `evidence_class=HOLDOUT_OR_TRANSFER`, and
  `sealed_status=SEALED_UNACCESSED` before fitting. Both partition manifests
  and their route freeze identity are fixed before calibration access.
  Its route record uses
  `calibration_evidence_class=RECONSTRUCTION_OR_CALIBRATION` and
  `scoring_evidence_class=HOLDOUT_OR_TRANSFER`.
- `SEPARATE_CHARACTERIZATION_THEN_INDEPENDENT_VALIDATION`: two distinct
  `campaign_id` values are required. The first has a `CHARACTERIZATION`
  partition with `evidence_class=CHARACTERIZATION`; the later campaign has a
  wholly untouched `COMPARISON` partition with
  `evidence_class=INDEPENDENT_COMPONENT_VALIDATION`. The later campaign is not
  a holdout subset of the first.
  Its route record uses `calibration_evidence_class=CHARACTERIZATION` and
  `scoring_evidence_class=INDEPENDENT_COMPONENT_VALIDATION`.

Every replicate belongs to exactly one condition, block, and evidence
partition. Blocks encode acquisition structure only; neither a block nor an
ordinary replicate becomes holdout evidence unless Route B prospectively
assigns its enclosing partition to `SEALED_SCORING`.

Measured pressure samples have one source of truth:
`val_data_001_signals.csv`. `val_data_001_controls.csv` contains command and
state records plus `basket_pressure_signal_id` and
`upstream_pressure_signal_id`; it contains no independently authoritative
measured-pressure value. `control_deviation_pa` is derived from the referenced
basket signal and commanded pressure and therefore requires `processing_id`.
If duplicated presentation values are exported later, they must be byte- and
value-derived from that signal row; conflicts resolve in favor of the signal
table and invalidate the export.

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
multiple-condition structure, and anticipated exclusions. It must document
assumptions and sensitivity to them; this plan does not invent a replicate
count or power value. Partition and access rules depend on the selected route:

- `INDEPENDENT_COMPONENT_VALIDATION`: calculate replication for the complete
  independent comparison dataset. No within-dataset calibration/holdout split
  is required. Freeze evidence identity, rights, protocol, and access policy
  before outcome access; the entire scored dataset remains unused for fitting
  and model selection.
- `CALIBRATION_THEN_HOLDOUT_OR_TRANSFER`: calculate calibration and scoring
  replication separately. Freeze partition membership and manifest hashes
  before fitting; seal the scoring partition. Opening or scoring it requires
  separate authority and leakage controls.
- `SEPARATE_CHARACTERIZATION_THEN_INDEPENDENT_VALIDATION`: calculate the
  characterization campaign and later independent campaign separately.
  Characterization is non-validation evidence; the later campaign remains
  wholly untouched and is not an ordinary holdout subset of the earlier one.

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

## Route-conditional preregistration, partitioning, and access

Before access to comparison outcomes, preregister time origin, filtering and
resampling, feature definitions, uncertainty propagation, missingness,
exclusions, parameter/model-form metrics, thresholds, and interpretation.
Separate prescribed quantities, independently measured inputs, calibration
quantities, comparison outputs, contextual metadata, and excluded quantities.

For `INDEPENDENT_COMPONENT_VALIDATION`, preregister the complete comparison and
freeze the complete dataset identity before outcome access; there is no
required within-dataset holdout allocation. For
`CALIBRATION_THEN_HOLDOUT_OR_TRANSFER`, preregister calibration and scoring
roles, freeze and seal scoring units or blocks before fitting, and prohibit
calibration/model selection from using them. For
`SEPARATE_CHARACTERIZATION_THEN_INDEPENDENT_VALIDATION`, preregister the later
campaign independently and keep it wholly inaccessible during characterization
and model selection. Holdout access and scoring, when Route B is selected,
require separate authority and are not authorized here. Downstream decisions
must distinguish inadequate measurement information, parameter confounding,
model-form discrimination, and persistent structured residuals.

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
- [ ] Route-appropriate replication and partition calculation:
      `DESIGN_CALCULATION_REQUIRED`.
- [ ] Randomization, blocks, exclusions, and preregistered analysis frozen.
- [ ] Rights, privacy, custody, and deposit plan accepted.
- [ ] Safety and operational review accepted by responsible humans.
- [ ] Evidence roles and claim ceiling recorded.

Until every required item is resolved, status remains
`COMMISSIONING_NOT_AUTHORIZED`.
