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
whether a prospectively protected comparison dataset under the selected
evidence route can support a bounded component
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
| `val_data_001_sites.csv` | `site_id` | `site_id`, `site_privacy_status`, `rights_resource_id` |
| `val_data_001_apparatus.csv` | `apparatus_id` | `apparatus_id`, `site_id`, `machine_make_model_resource_id`, `grinder_make_model_resource_id`, `burr_geometry_resource_id`, `burr_wear_state_resource_id`, `basket_geometry_resource_id` |
| `val_data_001_apparatus_signals.csv` | (`apparatus_id`, `signal_id`) | `apparatus_id`, `signal_id`, `observable_code`, `sensor_resource_id`, `native_unit`, `native_sample_interval_s`, `calibration_applicability`, `uncertainty_resource_id`, `clock_resource_id`, `synchronization_method`, `offset_drift_resource_id`, `prescribed_or_measured` |
| `val_data_001_campaigns.csv` | `campaign_instance_id` | `campaign_instance_id`, `puckworks_campaign_id`, `campaign_mapping_status`, `site_id`, `apparatus_id`, `route_id`, `contributor_resource_id`, `external_repository_resource_id`, `timezone`, `deviations_resource_id`, `schema_version` |
| `val_data_001_evidence_partitions.csv` | `evidence_partition_id` | `evidence_partition_id`, `campaign_instance_id`, `route_id`, `analysis_role`, `evidence_class`, `sealed_status`, `partition_manifest_sha256`, `seal_timestamp_utc`, `custodian_resource_id`, `access_policy_resource_id`, `rights_resource_id` |
| `val_data_001_replicates.csv` | `replicate_id` | `replicate_id`, `campaign_instance_id`, `route_id`, `condition_id`, `block_id`, `replicate_sequence`, `randomization_sequence`, `evidence_partition_id` |
| `val_data_001_blocks.csv` | `block_id` | `block_id`, `campaign_instance_id`, `block_type`, `block_label`, `session_start_utc`, `coffee_lot_resource_id`, `grinder_state_resource_id`, `operator_role_resource_id`, `apparatus_state_resource_id`, `calibration_set_id` |
| `val_data_001_resources.csv` | `resource_id` (globally unique) | `resource_id`, `resource_type`, `payload_schema_id`, `payload_json_canonical`, `resource_provenance_mode`, `source_file_id`, `rights_resource_id` |
| `val_data_001_resource_type_schemas.csv` | `payload_schema_id` | `payload_schema_id`, `resource_type`, `schema_version`, `required_members_json_canonical`, `optional_members_json_canonical`, `member_types_json_canonical`, `additional_members_allowed`, `schema_sha256` |
| `val_data_001_conditions.csv` | `condition_id` | `condition_id`, `campaign_instance_id`, `apparatus_id`, `control_mode`, `prescribed_node`, `prescribed_pressure_pa_gauge`, `command_program_resource_id`, `initial_hydraulic_state_resource_id`, `ambient_reference_pa`, `zeroing_basis`, `ramp_definition`, `plateau_definition`, `termination_rule`, `control_tolerance_pa`, `missing_value_state` |
| `val_data_001_shots.csv` | `shot_id` | `shot_id`, `campaign_instance_id`, `route_id`, `condition_id`, `apparatus_id`, `replicate_id`, `block_id`, `evidence_partition_id`, `coffee_lot_resource_id`, `grinder_resource_id`, `basket_resource_id`, `dose_g`, `dry_bed_depth_mm`, `preparation_protocol_resource_id`, `target_beverage_g`, `brew_temperature_c`, `raw_or_processed`, `inclusion_status`, `exclusion_reason`, `t0_event_code`, `t0_uncertainty_s` |
| `val_data_001_shot_events.csv` | (`shot_id`, `event_id`) | `shot_id`, `event_id`, `event_code`, `elapsed_time_s`, `source_file_id`, `value_processing_id`, `event_status`, `uncertainty_s`, `quality_flags` |
| `val_data_001_signals.csv` | (`shot_id`, `signal_id`, `sample_index`) | `shot_id`, `apparatus_id`, `signal_id`, `sample_index`, `sensor_resource_id`, `clock_resource_id`, `calibration_id`, `source_file_id`, `value_processing_id`, `native_timestamp`, `elapsed_time_s`, `native_value`, `native_unit`, `canonical_value`, `canonical_unit`, `physical_node`, `raw_or_processed`, `quality_flags`, `missing_value_state`, `clock_offset_s`, `clock_drift_s_per_s`, `sensor_latency_s`, `resampling_interval_s` |
| `val_data_001_controls.csv` | (`shot_id`, `control_sample_index`) | `shot_id`, `control_sample_index`, `command_program_resource_id`, `clock_resource_id`, `source_file_id`, `value_processing_id`, `raw_or_processed`, `native_timestamp`, `elapsed_time_s`, `commanded_pressure_value`, `commanded_pressure_unit`, `prescribed_node`, `basket_pressure_signal_id`, `basket_pressure_sample_index`, `upstream_pressure_signal_id`, `upstream_pressure_sample_index`, `upstream_pressure_availability`, `control_deviation_pa`, `control_status`, `control_phase` |
| `val_data_001_flow_conversions.csv` | `conversion_id` | `conversion_id`, `shot_id`, `density_source_resource_id`, `calibration_id`, `calibration_applicability`, `source_file_id`, `native_mass_flow_g_s`, `native_volume_flow_ml_s`, `canonical_mass_flow_kg_s`, `canonical_volume_flow_m3_s`, `density_kg_m3`, `density_temperature_c`, `conversion_formula`, `value_processing_id` |
| `val_data_001_deformation.csv` | (`shot_id`, `location_id`, `sample_index`) | `shot_id`, `apparatus_id`, `signal_id`, `location_id`, `sample_index`, `sensor_resource_id`, `clock_resource_id`, `calibration_id`, `reference_state_resource_id`, `fixture_compliance_resource_id`, `source_file_id`, `value_processing_id`, `raw_or_processed`, `native_timestamp`, `elapsed_time_s`, `native_displacement_value`, `native_displacement_unit`, `canonical_displacement_m`, `compression_sign`, `spatial_basis`, `axial_coordinate_m`, `radial_coordinate_m`, `coffee_bed_displacement_m`, `quality_flags`, `missing_value_state` |
| `val_data_001_fractions.csv` | (`shot_id`, `fraction_id`) | `shot_id`, `fraction_id`, `evidence_partition_id`, `fraction_start_s`, `fraction_end_s`, `fraction_mass_g`, `fraction_tds_pct`, `raw_or_processed`, `source_file_id`, `value_processing_id` |
| `val_data_001_chemistry.csv` | (`shot_id`, `fraction_id`, `species`) | `shot_id`, `fraction_id`, `evidence_partition_id`, `species`, `mass_mg`, `reference_basis`, `analytical_method_resource_id`, `detection_limit_mg`, `recovery_pct`, `measurement_status`, `source_file_id`, `value_processing_id` |
| `val_data_001_calibrations.csv` | `calibration_id` | `calibration_id`, `campaign_instance_id`, `evidence_partition_id`, `calibration_set_id`, `apparatus_id`, `sensor_resource_id`, `source_file_id`, `observable_code`, `native_unit`, `canonical_unit`, `calibration_method`, `reference_resource_id`, `calibration_timestamp_utc`, `offset`, `scale`, `range_min`, `range_max`, `resolution`, `bandwidth_hz`, `latency_s`, `drift_per_s`, `uncertainty_resource_id`, `valid_from_utc`, `valid_to_utc` |
| `val_data_001_files.csv` | `source_file_id` | `source_file_id`, `relative_filename`, `file_role`, `raw_or_processed`, `sha256`, `byte_count`, `media_type`, `rights_resource_id`, `creator_software_resource_id`, `campaign_instance_id`, `evidence_partition_id` |
| `val_data_001_processing_operations.csv` | `processing_id` | `processing_id`, `operation_scope`, `software_commit`, `software_tree`, `operation_resource_id`, `parameter_record_json_canonical`, `synchronization_method`, `resampling_method`, `operator_role_resource_id`, `processing_timestamp_utc` |
| `val_data_001_processing_file_edges.csv` | (`processing_id`, `edge_role`, `source_file_id`) | `processing_id`, `edge_role`, `source_file_id`, `edge_sequence`, `channel_or_output_role` |
| `val_data_001_compatibility_packages.csv` | `compatibility_package_id` | `compatibility_package_id`, `campaign_instance_id`, `route_id`, `evidence_partition_id`, `puckworks_campaign_id`, `access_policy_resource_id`, `rights_resource_id`, `package_access_status`, `package_evidence_class`, `package_dataset_status`, `package_evidence_level_claimed`, `replicate_count`, `excluded_shot_count`, `exclusions_recorded`, `fraction_chemistry_status`, `package_content_mode`, `package_manifest_sha256`, `export_grid_id`, `export_processing_id`, `export_status` |
| `val_data_001_export_grids.csv` | `export_grid_id` | `export_grid_id`, `compatibility_package_id`, `grid_start_s`, `grid_end_s`, `resampling_interval_s`, `alignment_tolerance_s`, `basket_pressure_rule`, `delivered_mass_rule`, `flow_rule`, `temperature_rule`, `missing_value_rule`, `grid_freeze_resource_id` |
| `val_data_001_export_source_rows.csv` | (`compatibility_package_id`, `export_filename`, `export_row_key`, `export_field`) | `compatibility_package_id`, `export_filename`, `export_row_key`, `export_field`, `exported_row_state`, `provenance_class`, `time_source_mode`, `source_count`, `interpolation_formula`, `flow_conversion_id`, `unit_conversion_mode`, `unit_scale_decimal`, `unit_offset_decimal`, `literal_rule_id`, `export_processing_id`, `missing_value_state` |
| `val_data_001_export_source_records.csv` | (`compatibility_package_id`, `export_filename`, `export_row_key`, `export_field`, `source_ordinal`) | `compatibility_package_id`, `export_filename`, `export_row_key`, `export_field`, `source_ordinal`, `source_table`, `source_key_json_canonical`, `source_member`, `source_value_processing_id` |
| `val_data_001_export_source_samples.csv` | (`compatibility_package_id`, `export_filename`, `export_row_key`, `export_field`, `source_ordinal`) | `compatibility_package_id`, `export_filename`, `export_row_key`, `export_field`, `source_ordinal`, `source_table`, `source_key_json_canonical`, `source_elapsed_time_s`, `source_raw_or_processed`, `source_value_processing_id`, `interpolation_weight_decimal` |
| `val_data_001_export_literal_rules.csv` | `literal_rule_id` | `literal_rule_id`, `export_filename`, `export_field`, `canonical_value`, `scalar_encoding`, `rule_sha256` |

The locked Puckworks bindings distinguish immutable schemas from future data.
`campaign_instance_id` is the authoritative local identifier for one
acquisition/submission instance. It is never exported as a Puckworks
`campaign_id`. `puckworks_campaign_id` is the distinct `EXP-NNN` catalog
identity and references actual values in locked
`docs/data_requests/experimental_campaigns.yml` at
`$.campaigns[*].campaign_id`. By contrast, locked
`docs/data_requests/templates/campaign_metadata.yml` and
`docs/data_requests/templates/apparatus.yml` are schemas/templates whose
repository placeholder values are not parent data. `campaigns.site_id`
references the authoritative local site row and deterministically exports to
`$.site_id` in the future submitted `campaign_metadata.yml` instance.
Apparatus references resolve to the authoritative local apparatus row and
deterministically export to `$.apparatus_id` in the future submitted
`apparatus.yml` instance. Local `shot_id` and `replicate_id` values populate
the same-named columns in a future submitted `shot_metadata.csv` instance; its
`campaign_id` receives `puckworks_campaign_id`, not
`campaign_instance_id`. These are deterministic export bindings, not
additional foreign-key parents.

`campaign_mapping_status` is frozen before commissioning. When it is
`LOCKED_PUCKWORKS_CAMPAIGN`, `puckworks_campaign_id` is `NOT NULL` and resolves
to the locked catalog. For
`PUCKWORKS_MACHINE_MODE_CAMPAIGN_GAP_LOCAL_EXTENSION` or
`FUTURE_PUCKWORKS_CAMPAIGN_PENDING`, `puckworks_campaign_id` is null. Thus the
machine-mode gap remains representable under a local
`campaign_instance_id` without inventing an EXP identifier. Such a local
extension must not claim Puckworks submission compatibility until a valid
catalog campaign is prospectively selected or created under separate
authority.

### Implementation-contract closure

The following rules are normative and replace any less-specific schema prose
in this document.

#### Signal-registry and calibration binding

Every signal and deformation row carries `apparatus_id` and resolves both
`(shot_id, apparatus_id)` to the shot candidate key and
`(apparatus_id, signal_id)` to `val_data_001_apparatus_signals.csv`. The row's
`sensor_resource_id`, observable or physical node, native unit, and clock must
equal the registry entry. Raw rows use the registered native clock and unit;
processed rows retain their raw input through the processing-edge graph and
identify the synchronized clock and value-producing operation.

Calibration nullability is controlled solely by the registry's
`calibration_applicability`, never by sample missingness. `APPLICABLE` requires
one calibration whose apparatus, sensor, observable, native unit, calibration
set, and validity interval cover the acquisition time. `NOT_APPLICABLE`
requires null. `UNKNOWN_PENDING_REVIEW` requires null and blocks commissioning
readiness. A missing or failed sample does not relax these rules. Deformation
uses the same registry and calibration rules and additionally requires its
reference-state and fixture-compliance resources.

#### Fraction parent and locked chemistry export

`val_data_001_fractions.csv` is the parent of chemistry rows. Chemistry
resolves `(shot_id, fraction_id)` to that table, and its
`evidence_partition_id` must equal the fraction and shot partition. When
fraction chemistry is acquired, `fraction_metadata.csv` is generated exactly
with columns `campaign_id,shot_id,fraction_id,fraction_start_s,
fraction_end_s,fraction_mass_g,fraction_tds_pct,raw_or_processed`;
`campaign_id` is the mapped Puckworks campaign ID and every other value comes
from the fraction parent. When absent, the package records
`NOT_APPLICABLE_NO_FRACTIONATED_CHEMISTRY`; it must not fabricate fraction or
chemistry rows.

#### Typed resources and terminal rights

`payload_json_canonical` conforms to `payload_schema_id` for the declared
`resource_type`. Canonical serialization is UTF-8 JSON with lexicographically
sorted object keys, no insignificant whitespace, JSON `null` only where the
type schema permits it, finite base-10 numbers, and no duplicate keys.
Required payload members are: `CONTRIBUTOR{contact,role}`;
`EXTERNAL_REPOSITORY{external_repository,doi}`; `RIGHTS{license,access_class,
redistribution_status}`;
`SENSOR{display_text,manufacturer,model,serial_or_asset_id}`;
`CLOCK{display_text,clock_id,clock_basis}`;
`UNCERTAINTY{display_text,status,budget_resource_ids}`;
`OFFSET_DRIFT{display_text,definition,status}`;
`GRINDER{display_text,identity,definition,grinder_setting}`; machine, grinder
model, burr, basket, and grinder-setting resources
`{display_text,identity,definition}`; command, preparation, reference, density, and
operation resources `{method,version,parameters}`;
`DEVIATION_RECORD{display_text,definition,status}`;
`OPERATOR_ROLE{display_text,definition,status}`;
`ANALYTICAL_METHOD{display_text,definition,status}`; and all remaining
enumerated types `{definition,status}`. `exclusions.csv.recorded_by` is
exactly `OPERATOR_ROLE.display_text`, and
`chemistry_measurements.csv.analytical_method` is exactly
`ANALYTICAL_METHOD.display_text`. Unresolved real-world values use the
applicable controlled unresolved disposition, not invented values.
Every used `payload_schema_id` resolves to
`val_data_001_resource_type_schemas.csv`; the schema row's `resource_type`
must match, `additional_members_allowed=false`, and its canonical required,
optional, and member-type maps make the payload contract complete rather than
prose-extensible. The schema hash is verified before package assembly.

A `RIGHTS` resource is terminal: its `rights_resource_id` and
`source_file_id` are null, and its payload carries its own provenance and
rights assertion. Every non-rights resource and file has exactly one direct
reference to a terminal `RIGHTS` resource, including public-domain material.
Self-references, rights-to-rights references, and rights-reference cycles are
invalid.

#### Partition-specific compatibility packages

Each compatibility package belongs to exactly one evidence partition. A
package cannot combine rows, files, manifests, or exports from partitions
with different access or evidence roles. For Route B, calibration and sealed
scoring evidence are always separate packages; before authorized opening, a
sealed package may expose only its seal identity, rights/access metadata, and
checksum manifest, never observations or presentation exports. Package
assembly fails if an input edge crosses the package partition. Routes A and C
use the same one-partition-per-package rule, with their route-specific access
states. This prevents compatibility presentation from becoming an access
side channel.

Every package identity and summary is derived solely from its one
`evidence_partition_id`. `package_evidence_class`, access policy, terminal
rights, sealing-derived access status, dataset status, and claimed evidence
level equal or are deterministically derived from that partition and its
route. `puckworks_campaign_id` exactly equals the parent campaign mapping.
`replicate_count` counts distinct package-partition replicates;
`excluded_shot_count` counts excluded shots in that partition; and
`exclusions_recorded` is exactly `excluded_shot_count > 0`. Exported shots,
fractions, chemistry, calibrations, files, exclusions, and all counts are
restricted to the same partition. A calibration package cannot query, count,
summarize, infer status from, or otherwise depend on a sealed-scoring
partition. Any mismatch blocks package assembly.

The exact package-state mapping is: partition `evidence_class` copies to
`package_evidence_class`; partition `access_policy_resource_id` and
`rights_resource_id` copy byte-for-byte to the package; `UNSEALED_CALIBRATION`
maps to `CALIBRATION_ACCESS`; `SEALED_UNACCESSED` maps to
`SEALED_UNACCESSED`; `AUTHORIZED_OPENED` maps to `AUTHORIZED_OPENED`;
`CLOSED_AFTER_SCORING` maps to `CLOSED_AFTER_SCORING`; and
`NOT_APPLICABLE` maps to `OPEN_AUTHORIZED` only when the partition access
policy authorizes ordinary access. `PUBLIC_METADATA_ONLY` describes only a
metadata/checksum presentation and grants no observation access.

`fraction_chemistry_status` is package-level and exactly `PRESENT` or
`NOT_APPLICABLE_NO_FRACTIONATED_CHEMISTRY`. `PRESENT` requires at least one
fraction row in the package partition and complete reconciliation of all
applicable fraction and chemistry exports. The not-applicable state requires
zero fraction and zero chemistry rows and prohibits fabricated empty rows.

`package_content_mode` controls package nullability exactly:

| Content mode | Files and observations | `export_processing_id` | `export_grid_id` |
|---|---|---|---|
| `FULL_COMPATIBILITY_EXPORT` | Complete partition-authorized compatibility files, including `shot_timeseries.csv` | required; scope exactly `COMPATIBILITY_EXPORT` | required; exactly one reciprocal grid |
| `METADATA_CHECKSUM_ONLY` | Only rights/access metadata, seal identity, and checksum manifest; no observations or time-series sources | required; scope exactly `SEALED_METADATA_ASSEMBLY` | null |
| `NOT_GENERATED` | No compatibility files | null | null |
| `NOT_APPLICABLE` | No compatibility files | null | null |

An unopened sealed partition permits only `METADATA_CHECKSUM_ONLY` or
`NOT_GENERATED`. `export_status`, manifest identity, file set, operation,
grid, source rows, and access state must agree with the content mode. The four
modes have mutually exclusive file sets. Both generated modes require
`export_status=GENERATED_VERIFIED` and a non-null manifest hash;
`NOT_GENERATED` requires the same-named status and a null manifest hash;
`NOT_APPLICABLE` requires the same-named status and a null manifest hash.
The full-mode file set is exactly `campaign_metadata.yml`, `apparatus.yml`,
`shot_metadata.csv`, `shot_timeseries.csv`, `calibration.csv`,
`exclusions.csv`, and `file_manifest.csv`, plus `fraction_metadata.csv` and
`chemistry_measurements.csv` only when `fraction_chemistry_status=PRESENT`.
The metadata-only file set is exactly `package_manifest.json`,
`rights_access.json`, and `seal_identity.json`; these contain no observation,
count, exclusion, or derived scientific value. The other two modes have an
empty file set.

#### Row-value and file-assembly lineage

`operation_scope` is exactly one of `ROW_VALUE`,
`NORMALIZED_FILE_ASSEMBLY`, `COMPATIBILITY_EXPORT`, or
`SEALED_METADATA_ASSEMBLY`. A row's `value_processing_id` references only a
`ROW_VALUE` operation and is null only for a directly reported raw native
value. File assembly and compatibility export operations never masquerade as
row-value transformations. `parent_source_file_id` is not part of the files
schema and is not authoritative. All actual dependencies use
`processing_file_edges`; every processed or derived file has exactly one
output producer, every producer has at least one input and one output, native
files have no output producer, and the bipartite file-operation graph is
acyclic. A generated compatibility package references exactly one
`export_processing_id`: full mode requires `COMPATIBILITY_EXPORT`, while
metadata-only mode requires `SEALED_METADATA_ASSEMBLY`;
non-generated and not-applicable modes reference none.
`NORMALIZED_FILE_ASSEMBLY` is never accepted for package export. Full-export
source rows reference the package's same `COMPATIBILITY_EXPORT` operation;
sealed-envelope files reference only its `SEALED_METADATA_ASSEMBLY` operation.

#### Exact synchronized-time-series and terminal-mass export

Every package that produces `shot_timeseries.csv` has one required
`export_grid_id`, and `export_grids.compatibility_package_id` is unique. Thus
the package and grid reference each other one-to-one; zero or multiple active
grids fail export readiness. Its grid
start, end, interval, alignment tolerance, per-observable selection or
interpolation rule, and missing-value behavior are explicit. Export rows are
ordered by `(shot_id, elapsed_s)`; each field records a complete canonical
source set through `val_data_001_export_source_rows.csv` and its child
`val_data_001_export_source_samples.csv`.
`provenance_class=TIME_INDEXED_SAMPLES` with
`time_source_mode=EXACT_SAMPLE` requires
`source_count=1`, ordinal 1, weight exactly 1, and the complete source primary
key. `time_source_mode=LINEAR_INTERPOLATION` requires exactly two samples ordered
by time and then source key, ordinals 1 and 2, both complete primary keys, the
frozen formula, and explicit finite weights summing exactly to 1. Otherwise
interpolation is allowed only by the frozen rule, within tolerance, between
two quality-eligible samples; extrapolation is prohibited. Missing values use
`time_source_mode=MISSING`, `source_count=0`, no child rows, an empty exported value,
and an explicit missing state.

`exported_row_state` is frozen for the complete output row. Its total mapping
is `RAW_NATIVE -> raw`, `PROCESSED_SYNCHRONIZED -> processed`, and
`DERIVED_WITH_SYNCHRONIZED_SOURCES -> processed`. `RAW_NATIVE` is permitted
only where the specific locked-template contract prospectively allows a
raw-native compatibility row. An output row may use exact and interpolated
values only from compatible states declared by the export contract;
raw-native and synchronized values are never silently combined. Every child
retains its source `raw_or_processed` state and value-processing identity.
`MISSING_DECLARED` is not a row provenance state: missingness remains solely
in `missing_value_state`, while the complete row retains its actual raw,
processed, or derived provenance. Every field sharing one
`shot_timeseries.csv` row key has that same state and therefore the same one
Puckworks `raw` or `processed` scalar.
`flow_conversion_id` is non-null only when flow/density or mass-flow/
volume-flow conversion participates. Fixed scale/offset conversions use no
flow row. `unit_conversion_mode` is `NONE`, `FIXED_SCALE_OFFSET`, or
`FLOW_DENSITY_CONVERSION`; exact decimal scale and offset are always retained.
Pressure conversion can never reference a flow conversion.
Pressure is the basket-top Pa-gauge value divided by exactly 100000; upstream
pressure is not substituted. Conversions and processing identities are
retained.

Temperature is represented as a registered signal with observable/node code
`T_MACHINE_UPSTREAM_RU_C` or `T_BASKET_BED_TOP_C`, canonical unit `degC`, and
the same apparatus, sensor, clock, calibration, quality, and source rules as
other signals. `shot_timeseries.csv.temperature_c` uses only
`T_BASKET_BED_TOP_C`; the upstream temperature is retained separately and is
not substituted. An absent basket-top temperature exports an empty value with
the frozen missing state.

Each shot has exactly one realized termination row in
`val_data_001_shot_events.csv` whose `event_code` equals the prospectively
selected condition termination event. The row retains realized elapsed time,
source file, derivation operation when derived, status, uncertainty, and
quality flags. `achieved_beverage_g` uses the last quality-eligible
`DELIVERED_MASS_G` sample at or before that exact realized event time. Ties
resolve by the largest `sample_index`. The event primary key, exact signal
primary key, and conversion provenance are retained. A condition-level rule
alone is insufficient. If the realized event or eligible mass sample is
absent, the value is empty and the shot receives a deterministic exclusion or
QC status; target mass or a later sample is never substituted.

#### Non-time-indexed export provenance

Every emitted compatibility field has exactly one `provenance_class`:
`NORMALIZED_RECORD`, `TIME_INDEXED_SAMPLES`, or `FROZEN_LITERAL`.
`NORMALIZED_RECORD` requires one or more ordered
`val_data_001_export_source_records.csv` children with complete authoritative
row keys and exact source members; time, weight, and sample-state fields are
not present and must not be invented. `TIME_INDEXED_SAMPLES` uses only the
sample-child table and the exact/interpolated/missing cardinalities above.
`FROZEN_LITERAL` has no record or sample children and requires one registered
`literal_rule_id`. Mixed provenance classes for one output field are invalid.

| Compatibility file | Authoritative table | Exact source key |
|---|---|---|
| `campaign_metadata.yml` | `val_data_001_campaigns.csv`; package summaries | `campaign_instance_id`; `compatibility_package_id` |
| `apparatus.yml` | `val_data_001_apparatus.csv`; `val_data_001_apparatus_signals.csv` | `apparatus_id`; (`apparatus_id`, `signal_id`) |
| `shot_metadata.csv` | `val_data_001_shots.csv`; terminal signal/event sources where applicable | `shot_id`; exact signal/event keys |
| `calibration.csv` | `val_data_001_calibrations.csv` | `calibration_id` |
| `exclusions.csv` | `val_data_001_shots.csv` | `shot_id` |
| `file_manifest.csv` | `val_data_001_files.csv` | `source_file_id` |
| `fraction_metadata.csv` | `val_data_001_fractions.csv` | (`shot_id`, `fraction_id`) |
| `chemistry_measurements.csv` | `val_data_001_chemistry.csv` | (`shot_id`, `fraction_id`, `species`) |

For record children, the remaining allowed authoritative table/key pairs are
`val_data_001_compatibility_packages.csv(compatibility_package_id)`,
`val_data_001_resources.csv(resource_id)`,
`val_data_001_shot_events.csv(shot_id,event_id)`,
`val_data_001_flow_conversions.csv(conversion_id)`, and
`val_data_001_processing_operations.csv(processing_id)`. No other
`source_table` value is permitted without prospective contract amendment.

`shot_timeseries.csv` uses time-indexed sources except literal or exact
record-derived presentation fields. A record child may carry
`source_value_processing_id` only for a derived normalized scalar; it never
carries elapsed time, interpolation weight, or source-sample state.
`exported_row_state` is required for every `shot_timeseries.csv` field and is
null for every non-time compatibility filename.

Every `export_row_key` is compact canonical JSON with exactly these members:

| Compatibility filename | Exact row-key members |
|---|---|
| `campaign_metadata.yml` | `campaign_instance_id` |
| `apparatus.yml` | `apparatus_id` |
| `shot_metadata.csv` | `shot_id` |
| `shot_timeseries.csv` | `shot_id`, `elapsed_s_decimal` |
| `calibration.csv` | `calibration_id` |
| `exclusions.csv` | `shot_id` |
| `file_manifest.csv` | `source_file_id` |
| `fraction_metadata.csv` | `shot_id`, `fraction_id` |
| `chemistry_measurements.csv` | `shot_id`, `fraction_id`, `species` |

`elapsed_s_decimal` uses the frozen shortest round-tripping decimal encoding.
Within a package, every compatibility filename is unique. Within a partition,
every normalized `relative_filename` is unique. All fields sharing one
time-series `export_row_key` have exactly the same `exported_row_state`; a
state mismatch rejects the entire row.

#### Exact scalar compatibility encoding

Simple text YAML scalars are UTF-8 double-quoted YAML 1.2 strings using JSON
string escaping. CSV follows RFC 4180 with UTF-8, LF records, the literal
locked header, decimal point `.`, no thousands separators, and empty unquoted
fields only for declared missing values. Booleans are lowercase `true` or
`false`; integer counts are unsigned base-10 without leading zeros; finite
decimal quantities use the shortest round-tripping base-10 form. Compound
scalars are compact canonical JSON with lexicographically sorted keys, no
insignificant whitespace or duplicate keys, and the exact resource
`payload_schema_id`; the JSON string is then CSV-escaped under RFC 4180.

The exact scalar sources are:

- `campaign_metadata.contributor` = `CONTRIBUTOR.contact`;
- apparatus make/model, burr, wear, and basket fields = `display_text` from
  their correspondingly typed payloads;
- signal instrument = `SENSOR.display_text`; uncertainty =
  `UNCERTAINTY.display_text`; clock = `CLOCK.display_text`; drift =
  `OFFSET_DRIFT.display_text`;
- `shot_metadata.grinder_setting` = `GRINDER.grinder_setting`;
- `calibration.instrument` = `SENSOR.display_text`;
- `pressure_source` = canonical JSON with exactly `calibration_id`,
  `signal_id`, `source_file_id`, and `value_processing_id`;
- `flow_source` = canonical JSON with exactly `flow_conversion_id`,
  `signal_id`, `source_file_id`, and `value_processing_id`, with JSON null only
  where the declared conversion domain permits it;
- calibration notes = canonical JSON with exactly `bandwidth_hz`,
  `calibration_id`, `drift_per_s`, `latency_s`, `range_max`, `range_min`,
  `resolution`, `uncertainty_resource_id`, `valid_from_utc`, and
  `valid_to_utc`;
- file-manifest notes = canonical JSON with exactly `campaign_instance_id`,
  `evidence_partition_id`, `producing_processing_id`, and `source_file_id`.

The corresponding schemas require `CONTRIBUTOR.contact`,
`SENSOR.display_text`, `UNCERTAINTY.display_text`, `CLOCK.display_text`,
`OFFSET_DRIFT.display_text`, `GRINDER.grinder_setting`, and `display_text` for
exported apparatus identity/geometry types. An export must not refer to an
undeclared generic `definition` member.

Fixed compatibility conversions are exact decimals: `Pa gauge -> bar` uses
scale `0.00001`, offset `0`; `kg -> g` and `kg/s -> g/s` use scale `1000`,
offset `0`; `m3/s -> mL/s` uses scale `1000000`, offset `0`; `K -> degC` uses
scale `1`, offset `-273.15`; and a value already in its target unit uses mode
`NONE`, scale `1`, offset `0`. Flow-density conversion uses mode
`FLOW_DENSITY_CONVERSION`, an exact `flow_conversion_id`, and the formula
frozen in that row, with presentation scale `1` and offset `0`. No other conversion is admissible without a prospectively
amended contract.

#### Compatibility serialization closure

This subsection is normative and supersedes less-specific serialization and
manifest prose. Every resource export expression is checked against the
closed member maps in `val_data_001_resource_type_schemas.csv`. In particular,
`EXTERNAL_REPOSITORY.external_repository`, `DEVIATION_RECORD.display_text`,
`OPERATOR_ROLE.display_text`, and `ANALYTICAL_METHOD.display_text` are required
UTF-8 strings. No alias or undeclared generic member is accepted.

The metadata-only files form a prospectively defined
`SEALED_METADATA_ENVELOPE`, not a filled Puckworks submission. One
`SEALED_METADATA_ASSEMBLY` operation (a fourth operation scope) emits them and
may consume only the named package, partition, terminal-rights, access-policy,
and seal records.

| File / object key | Required members in canonical order | Optional | Source |
|---|---|---|---|
| `package_manifest.json` / `compatibility_package_id` | `schema_version`, `envelope_type`, `compatibility_package_id`, `campaign_instance_id`, `evidence_partition_id`, `package_content_mode`, `files` | none | package row; frozen `SEALED_METADATA_ENVELOPE`; sorted file descriptors |
| `rights_access.json` / `compatibility_package_id` | `schema_version`, `compatibility_package_id`, `evidence_partition_id`, `access_policy_resource_id`, `rights_resource_id`, `package_access_status` | none | exact package and partition |
| `seal_identity.json` / `evidence_partition_id` | `schema_version`, `compatibility_package_id`, `evidence_partition_id`, `sealed_status`, `partition_manifest_sha256`, `seal_timestamp_utc`, `custodian_resource_id` | none | exact package and partition |

These are closed (`additionalProperties=false`) UTF-8 JSON schemas with LF
termination, no BOM or insignificant whitespace, and members in displayed
order. `files` has exactly two objects ordered by `filename`, for
`rights_access.json` and `seal_identity.json`; each has members in order
`filename`, `sha256`, `bytes`. Hashes are lowercase 64-hex and byte counts are
unsigned decimals. Filenames are package-relative basenames; absolute, `.` or
`..` paths, duplicates, and normalization collisions fail. Field provenance
is the source above; file provenance is the unique assembly output edge.

`package_manifest.json` never lists or hashes itself. Its externally computed
hash is stored only in `compatibility_packages.package_manifest_sha256` and
the normalized file registry. The other envelope files contain no self-hash.
The envelope contains no observations, counts, exclusions, time grids, or
presentation exports. The locked Puckworks `validate-submission` command
applies only to `FULL_COMPATIBILITY_EXPORT`; an envelope is
`SEALED_METADATA_ENVELOPE_SCHEMA_VALID_ONLY`, never a successful Puckworks
submission. Observation access and later full export require separate
authority.

For a full export, `file_manifest.csv` lists every other emitted compatibility
file exactly once and never itself. Its checksum remains in the normalized
file registry and enclosing canonical package-manifest calculation. That
calculation hashes an ordered descriptor containing `file_manifest.csv` and
all files it lists, but never its own resulting hash. Duplicate filenames or
conflicting file rows invalidate assembly.

Serialization ordering is exact:

| File | Order |
|---|---|
| `campaign_metadata.yml` | locked keys: `campaign_id`, `site_id`, `contributor`, `dataset_status`, `evidence_level_claimed`, `external_repository`, `doi`, `data_license`, `timezone`, `replicate_count`, `exclusions_recorded`, `deviations_from_protocol`, `declaration`; declaration keys: `no_private_or_unlicensed_third_party_data`, `submission_does_not_authorize_a_model_or_evidence_upgrade` |
| `apparatus.yml` | locked keys: `apparatus_id`, `machine_make_model`, `grinder_make_model`, `burr_geometry`, `burr_wear_state`, `basket_geometry`, `signals`; signals ascending `signal_id`; signal keys: `observable`, `instrument`, `native_unit`, `native_sampling_rate`, `calibration`, `uncertainty`, `clock_source`, `synchronization_method`, `offset_drift_estimate`, `prescribed_or_measured` |
| `shot_metadata.csv` | ascending `shot_id` |
| `shot_timeseries.csv` | ascending `shot_id`, then numeric `elapsed_s` |
| `calibration.csv` | ascending source `calibration_id` |
| `exclusions.csv` | ascending `shot_id` |
| `file_manifest.csv` | ascending `filename` |
| `fraction_metadata.csv` | ascending `shot_id`, then `fraction_id` |
| `chemistry_measurements.csv` | ascending `shot_id`, then `fraction_id`, then `species` |

CSV headers remain the exact locked headers. Identifier sorts compare NFC
strings by Unicode code point; elapsed time compares its finite decimal value.
Duplicate keys, normalized collisions, numeric-time ties within a shot, and
filename collisions fail export. Canonical YAML paths are dot-separated with
no leading dot. The sole sequence form is
`signals[signal_id=<canonical-id>].<member>`; indices and wildcards are
prohibited, so every nested value has one stable path.

Both YAML files use one byte-deterministic emitter profile: UTF-8 without BOM;
LF line endings with exactly one final LF; no document marker, anchors,
aliases, tags, comments, trailing whitespace, or trailing blank lines;
two-space indentation; block-style `signals`; one space after every mapping
colon; the frozen key and sequence order above; and double-quoted YAML 1.2
strings with JSON escaping. For `apparatus.yml`, applicability `APPLICABLE`
emits the exact bytes `calibration: "see calibration.csv"`,
`NOT_APPLICABLE` emits `calibration: "NOT_APPLICABLE"`, and
`UNKNOWN_PENDING_REVIEW` prohibits export. Calibration identifiers and
validity intervals remain solely in the normalized calibration table and
`calibration.csv`.

The normalized compatibility mapping is frozen: `RAW_NATIVE -> raw`,
`PROCESSED_SYNCHRONIZED -> processed`, and `DERIVED -> processed`. The
time-series exported-row mapping is `RAW_NATIVE -> raw`,
`PROCESSED_SYNCHRONIZED -> processed`, and
`DERIVED_WITH_SYNCHRONIZED_SOURCES -> processed`. These mappings are total for
every Puckworks `raw_or_processed` field. Missingness never changes row
provenance, and `MISSING_DECLARED` is neither a valid `exported_row_state` nor
emitted into `raw_or_processed`.

The deterministic audit fails unless every resource member exists with its
declared type, every file has the closed schema and source contract, all YAML
paths/sequences and CSV rows are uniquely ordered, every compatibility state
is `raw` or `processed`, both manifests are nonrecursive, the envelope cannot
be mistaken for a submission, and each full package is structurally eligible
for the locked validator. It neither validates evidence nor authorizes access
or commissioning.

### Deterministic Puckworks compatibility exports

The normalized VAL-DATA-001 tables are authoritative. Locked Puckworks
templates define compatibility presentations only. Each exported file is an
`OUTPUT` edge of a processing operation whose input edges identify every
normalized source file. A duplicated value must equal its declared source and
unit conversion exactly; disagreement invalidates the export and blocks
commissioning readiness. Export is prohibited unless
`campaign_mapping_status=LOCKED_PUCKWORKS_CAMPAIGN`.

| Locked template and field | Authoritative normalized source or exact rule |
|---|---|
| `campaign_metadata.yml.campaign_id` | `campaigns.puckworks_campaign_id` |
| `.site_id` | `campaigns.site_id` |
| `.contributor` | UTF-8 YAML scalar from `CONTRIBUTOR.contact` for `campaigns.contributor_resource_id` |
| `.dataset_status` | `compatibility_packages.package_dataset_status`, derived only from the package partition: `proposal_only` before acquisition; `pilot_collected` for pilot-only partitions; `holdout_reserved` for unopened Route-B scoring partitions; `controlled_dataset` for other controlled acquired partitions |
| `.evidence_level_claimed` | `compatibility_packages.package_evidence_level_claimed`, derived only from its partition: `feasibility_pilot` for pilot evidence; `controlled_replicated` for controlled comparison/calibration; `holdout_independent` only for an authorized opened Route-B score; no upgrade is implied |
| `.external_repository`, `.doi` | exact `external_repository` and `doi` members of the `EXTERNAL_REPOSITORY` resource referenced by `campaigns.external_repository_resource_id` |
| `.data_license` | exact `license` member of the `RIGHTS` resource referenced through the selected route and partitions |
| `.timezone` | `campaigns.timezone` |
| `.replicate_count` | `compatibility_packages.replicate_count`, the count of distinct replicates represented in that package's one evidence partition |
| `.exclusions_recorded` | `compatibility_packages.exclusions_recorded`, exactly whether `excluded_shot_count > 0` within that package partition and reconciled with its exported `exclusions.csv` |
| `.deviations_from_protocol` | UTF-8 YAML scalar from `DEVIATION_RECORD.display_text` |
| `.declaration.*` | literal `true` only after the corresponding rights and no-upgrade assertions are verified; otherwise export is prohibited |

| `apparatus.yml` field | Authoritative normalized source |
|---|---|
| `apparatus_id` | `apparatus.apparatus_id` |
| `machine_make_model`, `grinder_make_model`, `burr_geometry`, `burr_wear_state`, `basket_geometry` | `display_text` from the correspondingly typed apparatus resource payload |
| `signals[].observable` | `apparatus_signals.observable_code` |
| `signals[].instrument` | `SENSOR.display_text` for `apparatus_signals.sensor_resource_id` |
| `signals[].native_unit` | `apparatus_signals.native_unit` |
| `signals[].native_sampling_rate` | reciprocal of `apparatus_signals.native_sample_interval_s`, with the operation and conversion retained |
| `signals[].calibration` | `APPLICABLE`: exact YAML string `"see calibration.csv"`; `NOT_APPLICABLE`: exact YAML string `"NOT_APPLICABLE"`; `UNKNOWN_PENDING_REVIEW`: export prohibited. Actual IDs and validity remain in normalized calibrations and `calibration.csv` and are never serialized as a variable list here |
| `signals[].uncertainty` | `UNCERTAINTY.display_text` for `apparatus_signals.uncertainty_resource_id` |
| `signals[].clock_source` | `CLOCK.display_text` for `apparatus_signals.clock_resource_id` |
| `signals[].synchronization_method` | `apparatus_signals.synchronization_method` |
| `signals[].offset_drift_estimate` | `OFFSET_DRIFT.display_text` for `apparatus_signals.offset_drift_resource_id` |
| `signals[].prescribed_or_measured` | `apparatus_signals.prescribed_or_measured` |

| `shot_metadata.csv` field | Authoritative normalized source |
|---|---|
| `campaign_id` | `campaigns.puckworks_campaign_id`, never `campaign_instance_id` |
| `site_id`, `apparatus_id` | campaign and shot local authoritative IDs |
| `coffee_lot_id`, `grinder_id`, `basket_id` | exact resource IDs from the shot |
| `shot_id`, `replicate_id`, `dose_g`, `target_beverage_g`, `brew_temperature_c`, `raw_or_processed`, `exclusion_reason` | same-named authoritative shot fields |
| `achieved_beverage_g` | authoritative final `DELIVERED_MASS_G` signal sample for the shot |
| `grinder_setting` | exact `GRINDER.grinder_setting` member for `shots.grinder_resource_id` |
| `included` | `true` only for `inclusion_status=INCLUDED`; otherwise `false` |

| `shot_timeseries.csv` field | Authoritative normalized source/conversion |
|---|---|
| `shot_id` | `signals.shot_id` |
| `elapsed_s` | selected `signals.elapsed_time_s` synchronized timebase |
| `pressure_bar` | basket-top `signals.canonical_value` in Pa gauge divided by exactly `100000` |
| `pressure_source` | basket signal ID, source-file ID, calibration ID, and processing ID serialized deterministically |
| `beverage_mass_g` | `DELIVERED_MASS_G` authoritative canonical observation converted to g if needed |
| `flow_g_s` | authoritative mass-flow signal, or authoritative volume flow converted by the referenced flow-conversion/density record |
| `flow_source` | signal/conversion/source-file/processing identifiers serialized deterministically |
| `temperature_c` | authoritative registered `T_BASKET_BED_TOP_C` signal in `degC`; machine-upstream temperature is never substituted |
| `raw_or_processed` | authoritative exported signal row state |

Separate upstream pressure remains only in the normalized extension because
the locked `shot_timeseries.csv` has no upstream-pressure column.

| Remaining locked template | Exact field-level export rule |
|---|---|
| `calibration.csv` | scalar fields come from the calibration row; `instrument=SENSOR.display_text`; `notes` uses the exact canonical-JSON member set defined above |
| `exclusions.csv` | `campaign_id=campaigns.puckworks_campaign_id`; `shot_id` and `replicate_id` from the shot; `exclusion_reason` from the shot; `recorded_by=OPERATOR_ROLE.display_text` from the applicable operator-role resource |
| `file_manifest.csv` | scalar fields come from the partition file row; `license=RIGHTS.license`; `notes` uses the exact canonical-JSON member set defined above |
| `fraction_metadata.csv` | exact locked header; campaign mapping plus authoritative fraction-parent values, or package disposition `NOT_APPLICABLE_NO_FRACTIONATED_CHEMISTRY` |
| `chemistry_measurements.csv` | when applicable, `campaign_id=campaigns.puckworks_campaign_id`; `shot_id`, `fraction_id`, `species`, `mass_mg`, `reference_basis`, `detection_limit_mg`, `recovery_pct`, and `measurement_status` from chemistry; `analytical_method=ANALYTICAL_METHOD.display_text`. When no chemistry is acquired, the file is declared `NOT_APPLICABLE` and is not fabricated |

### Primary and candidate keys

| Table | Unique key used by references |
|---|---|
| evidence routes | (`route_id`) |
| sites | (`site_id`) |
| apparatus | (`apparatus_id`); candidate (`apparatus_id`, `site_id`) |
| apparatus signals | (`apparatus_id`, `signal_id`) |
| campaigns | (`campaign_instance_id`); candidate (`campaign_instance_id`, `route_id`); candidate (`campaign_instance_id`, `apparatus_id`); candidate (`campaign_instance_id`, `site_id`, `apparatus_id`) |
| evidence partitions | (`evidence_partition_id`); candidate (`evidence_partition_id`, `campaign_instance_id`); candidate (`evidence_partition_id`, `campaign_instance_id`, `route_id`) |
| conditions | (`condition_id`); candidate (`condition_id`, `campaign_instance_id`, `apparatus_id`) |
| blocks | (`block_id`); candidate (`block_id`, `campaign_instance_id`) |
| replicates | (`replicate_id`); candidate (`replicate_id`, `campaign_instance_id`, `route_id`, `condition_id`, `block_id`, `evidence_partition_id`) |
| shots | (`shot_id`); candidate (`shot_id`, `apparatus_id`); candidate (`shot_id`, `evidence_partition_id`); candidate (`shot_id`, `campaign_instance_id`, `route_id`, `condition_id`, `apparatus_id`, `replicate_id`, `block_id`, `evidence_partition_id`) |
| shot events | (`shot_id`, `event_id`); unique candidate (`shot_id`, `event_code`) for the realized termination code |
| resources | (`resource_id`) globally unique |
| resource type schemas | (`payload_schema_id`); candidate (`payload_schema_id`, `resource_type`) |
| signals | (`shot_id`, `signal_id`, `sample_index`) |
| controls | (`shot_id`, `control_sample_index`) |
| flow conversions | (`conversion_id`) |
| deformation | (`shot_id`, `location_id`, `sample_index`) |
| fractions | (`shot_id`, `fraction_id`); candidate (`shot_id`, `fraction_id`, `evidence_partition_id`) |
| chemistry | (`shot_id`, `fraction_id`, `species`) |
| calibrations | (`calibration_id`) |
| files | (`source_file_id`); unique candidate (`evidence_partition_id`, `relative_filename`) |
| processing operations | (`processing_id`) |
| processing file edges | (`processing_id`, `edge_role`, `source_file_id`); unique candidate (`processing_id`, `edge_role`, `edge_sequence`) |
| compatibility packages | (`compatibility_package_id`); candidate (`compatibility_package_id`, `campaign_instance_id`, `route_id`, `evidence_partition_id`) |
| export grids | (`export_grid_id`); unique candidate (`compatibility_package_id`); candidate (`export_grid_id`, `compatibility_package_id`) |
| export source rows | (`compatibility_package_id`, `export_filename`, `export_row_key`, `export_field`) |
| export source records | (`compatibility_package_id`, `export_filename`, `export_row_key`, `export_field`, `source_ordinal`) |
| export source samples | (`compatibility_package_id`, `export_filename`, `export_row_key`, `export_field`, `source_ordinal`) |
| export literal rules | (`literal_rule_id`); candidate (`export_filename`, `export_field`, `literal_rule_id`) |

### Foreign-key resolution matrix

Cardinality is child-to-parent. `NOT NULL` means every child row requires
exactly one parent; `NULLABLE` states the sole permitted null condition.

| Child field | Exact parent | Cardinality/null rule |
|---|---|---|
| `campaigns.puckworks_campaign_id` | locked catalog `docs/data_requests/experimental_campaigns.yml` `$.campaigns[*].campaign_id` | many-to-one; `NOT NULL` only for `campaign_mapping_status=LOCKED_PUCKWORKS_CAMPAIGN`, otherwise null |
| `campaigns.site_id` | `val_data_001_sites.csv.site_id` | many-to-one, `NOT NULL`; exported to the future template instance |
| `campaigns.apparatus_id`, `conditions.apparatus_id`, `shots.apparatus_id`, `calibrations.apparatus_id`, `apparatus_signals.apparatus_id` | `val_data_001_apparatus.csv.apparatus_id` | many-to-one, `NOT NULL`; exported to the future template instance |
| `campaigns.(apparatus_id, site_id)` | `val_data_001_apparatus.csv.(apparatus_id, site_id)` | many-to-one, both `NOT NULL`; separate existence is insufficient |
| `apparatus.site_id` | `val_data_001_sites.csv.site_id` | many-to-one, `NOT NULL` |
| `campaigns.route_id`, `evidence_partitions.route_id` | `val_data_001_evidence_routes.csv.route_id` | many-to-one, `NOT NULL` |
| `evidence_partitions.campaign_instance_id`, `replicates.campaign_instance_id`, `blocks.campaign_instance_id`, `conditions.campaign_instance_id`, `shots.campaign_instance_id`, `files.campaign_instance_id` | `val_data_001_campaigns.csv.campaign_instance_id` | many-to-one, `NOT NULL` |
| `evidence_partitions.(campaign_instance_id, route_id)` | `val_data_001_campaigns.csv.(campaign_instance_id, route_id)` | many-to-one, both `NOT NULL` |
| `replicates.(condition_id, campaign_instance_id)` | `val_data_001_conditions.csv.(condition_id, campaign_instance_id)` | many-to-one, both `NOT NULL` |
| `replicates.(block_id, campaign_instance_id)` | `val_data_001_blocks.csv.(block_id, campaign_instance_id)` | many-to-one, both `NOT NULL` |
| `replicates.(evidence_partition_id, campaign_instance_id, route_id)` | `val_data_001_evidence_partitions.csv.(evidence_partition_id, campaign_instance_id, route_id)` | many-to-one, all `NOT NULL` |
| `shots.(replicate_id, campaign_instance_id, route_id, condition_id, block_id, evidence_partition_id)` | corresponding six fields of the replicate candidate key | many-to-one, all `NOT NULL` |
| `shots.(condition_id, campaign_instance_id, apparatus_id)` | condition candidate key | many-to-one, all `NOT NULL` |
| `shot_events.shot_id`, `signals.shot_id`, `controls.shot_id`, `flow_conversions.shot_id`, `deformation.shot_id`, `fractions.shot_id`, `chemistry.shot_id` | `val_data_001_shots.csv.shot_id` | many-to-one, `NOT NULL` |
| `signals.(shot_id, apparatus_id)`, `deformation.(shot_id, apparatus_id)` | `val_data_001_shots.csv.(shot_id, apparatus_id)` | many-to-one, both `NOT NULL` |
| `signals.(apparatus_id, signal_id)`, `deformation.(apparatus_id, signal_id)` | `val_data_001_apparatus_signals.csv.(apparatus_id, signal_id)` | many-to-one, both `NOT NULL`; registry identity fields must agree |
| `signals.source_file_id` | `val_data_001_files.csv.source_file_id` | many-to-one, `NOT NULL` |
| `shot_events.source_file_id` | `val_data_001_files.csv.source_file_id` | many-to-one, `NOT NULL` |
| `controls.source_file_id` | `val_data_001_files.csv.source_file_id` | many-to-one, `NOT NULL` |
| `flow_conversions.source_file_id` | `val_data_001_files.csv.source_file_id` | many-to-one, `NOT NULL` |
| `deformation.source_file_id` | `val_data_001_files.csv.source_file_id` | many-to-one, `NOT NULL` |
| `fractions.source_file_id` | `val_data_001_files.csv.source_file_id` | many-to-one, `NOT NULL` |
| `chemistry.source_file_id` | `val_data_001_files.csv.source_file_id` | many-to-one, `NOT NULL` |
| `calibrations.source_file_id` | `val_data_001_files.csv.source_file_id` | many-to-one, `NOT NULL` |
| `calibrations.(evidence_partition_id, campaign_instance_id)` | `val_data_001_evidence_partitions.csv.(evidence_partition_id, campaign_instance_id)` | many-to-one, both `NOT NULL`; exported only in the matching package partition |
| `signals.calibration_id`, `deformation.calibration_id` | `val_data_001_calibrations.csv.calibration_id` | governed by the referenced registry row's `calibration_applicability`; `APPLICABLE` requires a validity-covering calibration, `NOT_APPLICABLE` requires null, and `UNKNOWN_PENDING_REVIEW` requires null and blocks readiness |
| `flow_conversions.calibration_id` | `val_data_001_calibrations.csv.calibration_id` | many-to-one; `NOT NULL` when `flow_conversions.calibration_applicability=APPLICABLE`; null when it is `NOT_APPLICABLE` or `UNKNOWN_PENDING_REVIEW`, with `UNKNOWN_PENDING_REVIEW` blocking readiness |
| `shot_events.value_processing_id`, `signals.value_processing_id`, `controls.value_processing_id`, `flow_conversions.value_processing_id`, `deformation.value_processing_id`, `fractions.value_processing_id`, `chemistry.value_processing_id` | `val_data_001_processing_operations.csv.processing_id` | parent must have `operation_scope=ROW_VALUE`; null only for a directly reported raw native value or event |
| `processing_file_edges.processing_id` | `val_data_001_processing_operations.csv.processing_id` | many-to-one, `NOT NULL` |
| `processing_file_edges.source_file_id` | `val_data_001_files.csv.source_file_id` | many-to-one, `NOT NULL` |
| `controls.(shot_id, basket_pressure_signal_id, basket_pressure_sample_index)` | `val_data_001_signals.csv.(shot_id, signal_id, sample_index)` | many-to-one, complete reference `NOT NULL` |
| `controls.(shot_id, upstream_pressure_signal_id, upstream_pressure_sample_index)` | `val_data_001_signals.csv.(shot_id, signal_id, sample_index)` | many-to-one; signal ID and sample index are both present or both absent, and both may be absent only when `controls.upstream_pressure_availability=NOT_MEASURED` |
| `chemistry.(shot_id, fraction_id)` | `val_data_001_fractions.csv.(shot_id, fraction_id)` | many-to-one, both `NOT NULL`; partition must agree |
| `fractions.(shot_id, evidence_partition_id)` | `val_data_001_shots.csv.(shot_id, evidence_partition_id)` | many-to-one, both `NOT NULL` |
| `chemistry.(shot_id, fraction_id, evidence_partition_id)` | `val_data_001_fractions.csv.(shot_id, fraction_id, evidence_partition_id)` | many-to-one, all `NOT NULL`; this also binds the shot partition |
| `files.(evidence_partition_id, campaign_instance_id)` | `val_data_001_evidence_partitions.csv.(evidence_partition_id, campaign_instance_id)` | many-to-one, both `NOT NULL`; partition route must agree with campaign |
| `compatibility_packages.(evidence_partition_id, campaign_instance_id, route_id)` | `val_data_001_evidence_partitions.csv.(evidence_partition_id, campaign_instance_id, route_id)` | many-to-one, all `NOT NULL`; one partition per package |
| `compatibility_packages.puckworks_campaign_id` | `val_data_001_campaigns.csv.puckworks_campaign_id` through the package `campaign_instance_id` | exact equality; `NOT NULL` for an exportable locked mapping, otherwise package export prohibited |
| `compatibility_packages.export_processing_id` | `val_data_001_processing_operations.csv.processing_id` | `FULL_COMPATIBILITY_EXPORT`: required with parent scope exactly `COMPATIBILITY_EXPORT`; `METADATA_CHECKSUM_ONLY`: required with parent scope exactly `SEALED_METADATA_ASSEMBLY`; `NOT_GENERATED` and `NOT_APPLICABLE`: null |
| `compatibility_packages.export_grid_id`, `export_grids.(export_grid_id, compatibility_package_id)` | reciprocal package/grid keys | exactly one for `FULL_COMPATIBILITY_EXPORT`; null/no row for all other modes |
| `export_grids.compatibility_package_id`, `export_source_rows.compatibility_package_id` | `val_data_001_compatibility_packages.csv.compatibility_package_id` | many-to-one, `NOT NULL` |
| `export_source_rows.export_processing_id` | `val_data_001_processing_operations.csv.processing_id` | `NOT NULL`, equals its package export operation, scope exactly `COMPATIBILITY_EXPORT` |
| `export_source_rows.flow_conversion_id` | `val_data_001_flow_conversions.csv.conversion_id` | non-null only for `FLOW_DENSITY_CONVERSION`; null for `NONE` and `FIXED_SCALE_OFFSET`; pressure always null |
| `export_source_rows.literal_rule_id` | `val_data_001_export_literal_rules.csv.literal_rule_id` | non-null only for `FROZEN_LITERAL`; null for record and sample provenance |
| `export_source_records.(compatibility_package_id, export_filename, export_row_key, export_field)`, `export_source_samples.(compatibility_package_id, export_filename, export_row_key, export_field)` | complete `val_data_001_export_source_rows.csv` primary key | many-to-one, all `NOT NULL`; record and sample child classes are mutually exclusive |
| `export_source_records.source_value_processing_id` | `val_data_001_processing_operations.csv.processing_id` | nullable for directly reported normalized records; otherwise scope `ROW_VALUE` |
| `export_source_samples.source_value_processing_id` | `val_data_001_processing_operations.csv.processing_id` | nullable only for a directly reported raw-native source sample; otherwise parent scope `ROW_VALUE` |
| `resources.(payload_schema_id, resource_type)` | `val_data_001_resource_type_schemas.csv.(payload_schema_id, resource_type)` | many-to-one, both `NOT NULL` |

`export_source_samples.source_table` is a controlled time-indexed-table
binding, not a free-form name. Its canonical source-key object has exactly the
members below and no others:

| `source_table` | Exact `source_key_json_canonical` members |
|---|---|
| `val_data_001_signals.csv` | `shot_id`, `signal_id`, `sample_index` |
| `val_data_001_deformation.csv` | `shot_id`, `location_id`, `sample_index` |

Every key object resolves to exactly one authoritative row in the same package
partition. `EXACT_SAMPLE` permits one child with ordinal 1 and weight 1.
`LINEAR_INTERPOLATION` permits two children with ordinals 1 and 2, strictly
ordered source times bracketing the export time, and the frozen weights.
Other cardinalities, incomplete keys, duplicate keys, or cross-partition keys
are invalid.

### Complete field-coverage classification

The commissioning-readiness audit enumerates every required field in every
exact table above. Key columns are classified in the primary/candidate-key
table; relational identifiers are classified in the foreign-key matrix;
`*_resource_id` columns are classified in the resource-reference matrix;
Puckworks catalog/template fields and `source_table` keys are controlled
external bindings. The remaining fields are expressly non-relational scalar,
measurement, status, enumeration, canonical-payload, checksum, timestamp,
unit, count, formula, quality, or provenance attributes governed by their
table and controlled-enumeration rules. A field ending in `_id`, `_ids`, or
`_key` that is not found in one of those five classes is an audit failure.
The same fail-closed audit rejects a declared reference whose target table,
candidate key, resource type, cardinality, null rule, or package partition is
missing or ambiguous.

### Resource-reference matrix

`val_data_001_resources.csv.resource_id` is globally unique, so every child
reference below resolves to one complete parent key. The required parent
`resource_type` is additionally checked.

| Resource-reference field | Required `resource_type` |
|---|---|
| `evidence_routes.prospective_freeze_resource_id` | `FREEZE_IDENTITY` |
| `evidence_routes.human_owner_disposition_resource_id` | `HUMAN_DISPOSITION` |
| `evidence_routes.rights_policy_resource_id`, `evidence_partitions.rights_resource_id`, `compatibility_packages.rights_resource_id`, `resources.rights_resource_id`, `files.rights_resource_id` | `RIGHTS` |
| `evidence_routes.access_policy_resource_id`, `evidence_partitions.access_policy_resource_id`, `compatibility_packages.access_policy_resource_id` | `ACCESS_POLICY` |
| `evidence_partitions.custodian_resource_id` | `CUSTODIAN` |
| `campaigns.contributor_resource_id` | `CONTRIBUTOR` |
| `campaigns.external_repository_resource_id` | `EXTERNAL_REPOSITORY` |
| `campaigns.deviations_resource_id` | `DEVIATION_RECORD` |
| `sites.rights_resource_id` | `RIGHTS` |
| `apparatus.machine_make_model_resource_id` | `MACHINE_MODEL` |
| `apparatus.grinder_make_model_resource_id` | `GRINDER_MODEL` |
| `apparatus.burr_geometry_resource_id` | `BURR_GEOMETRY` |
| `apparatus.burr_wear_state_resource_id` | `BURR_WEAR_STATE` |
| `apparatus.basket_geometry_resource_id` | `BASKET_GEOMETRY` |
| `apparatus_signals.sensor_resource_id` | `SENSOR` |
| `apparatus_signals.uncertainty_resource_id` | `UNCERTAINTY` |
| `apparatus_signals.clock_resource_id` | `CLOCK` |
| `apparatus_signals.offset_drift_resource_id` | `OFFSET_DRIFT` |
| `blocks.coffee_lot_resource_id`, `shots.coffee_lot_resource_id` | `COFFEE_LOT` |
| `blocks.grinder_state_resource_id` | `GRINDER_STATE` |
| `blocks.operator_role_resource_id`, `processing_operations.operator_role_resource_id` | `OPERATOR_ROLE` |
| `blocks.apparatus_state_resource_id` | `APPARATUS_STATE` |
| `blocks.calibration_set_id`, `calibrations.calibration_set_id` | `CALIBRATION_SET` |
| `conditions.command_program_resource_id`, `controls.command_program_resource_id` | `COMMAND_PROGRAM` |
| `conditions.initial_hydraulic_state_resource_id` | `HYDRAULIC_INITIAL_STATE` |
| `shots.grinder_resource_id` | `GRINDER` |
| `shots.basket_resource_id` | `BASKET` |
| `shots.preparation_protocol_resource_id` | `PREPARATION_PROTOCOL` |
| `signals.sensor_resource_id`, `deformation.sensor_resource_id`, `calibrations.sensor_resource_id` | `SENSOR` |
| `signals.clock_resource_id`, `controls.clock_resource_id`, `deformation.clock_resource_id` | `CLOCK` |
| `flow_conversions.density_source_resource_id` | `DENSITY_SOURCE` |
| `deformation.reference_state_resource_id` | `REFERENCE_STATE` |
| `deformation.fixture_compliance_resource_id` | `FIXTURE_COMPLIANCE` |
| `calibrations.reference_resource_id` | `REFERENCE_STANDARD` |
| `calibrations.uncertainty_resource_id` | `UNCERTAINTY` |
| `files.creator_software_resource_id` | `SOFTWARE` |
| `processing_operations.operation_resource_id` | `OPERATION` |
| `chemistry.analytical_method_resource_id` | `ANALYTICAL_METHOD` |
| `export_grids.grid_freeze_resource_id` | `FREEZE_IDENTITY` |

`resources.source_file_id` references `files.source_file_id`; it is `NOT NULL`
when `resources.resource_provenance_mode=SOURCE_FILE_BOUND` and null only when
that field is `INLINE_DECLARATION`, except that terminal `RIGHTS` resources
always carry provenance in their canonical payload and have null
`source_file_id`. `resources.rights_resource_id` references a globally unique
terminal resource of type `RIGHTS`; only a `RIGHTS` resource itself may have a
null rights reference.

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
| `physical_node`/signal code | `P_MACHINE_UPSTREAM_RU_PA_GAUGE`; `P_BASKET_BED_TOP_PA_GAUGE`; `T_MACHINE_UPSTREAM_RU_C`; `T_BASKET_BED_TOP_C`; `OUTLET_MASS_FLOW_G_S`; `OUTLET_VOLUME_FLOW_ML_S`; `DELIVERED_MASS_G`; `DEFORMATION_UPPER_M`; `DEFORMATION_MID_M`; `DEFORMATION_LOWER_M`; `BED_HEIGHT_BULK_M`; `FIRST_DRIP_EVENT_S` |
| `control_status` | `PENDING_FEASIBILITY`; `WITHIN_FROZEN_TOLERANCE`; `OUTSIDE_FROZEN_TOLERANCE`; `CONTROL_FAILURE` |
| `control_phase` | `PRE_SHOT`; `RAMP`; `PLATEAU`; `TERMINATION`; `POST_SHOT` |
| `block_type` | `SESSION`; `COFFEE_LOT`; `GRINDER_STATE`; `OPERATOR_STATE`; `APPARATUS_CALIBRATION_STATE` |
| `location_id` | `UPPER_BED`; `MID_BED`; `LOWER_BED`; `BULK_EQUIVALENT` |
| `resource_type` | `ACCESS_POLICY`; `ANALYTICAL_METHOD`; `APPARATUS_STATE`; `BASKET`; `BASKET_GEOMETRY`; `BURR_GEOMETRY`; `BURR_WEAR_STATE`; `CALIBRATION_SET`; `CLOCK`; `COFFEE_LOT`; `COMMAND_PROGRAM`; `CONTRIBUTOR`; `CUSTODIAN`; `DENSITY_SOURCE`; `DEVIATION_RECORD`; `EXTERNAL_REPOSITORY`; `FIXTURE_COMPLIANCE`; `FREEZE_IDENTITY`; `GRINDER`; `GRINDER_MODEL`; `GRINDER_STATE`; `HUMAN_DISPOSITION`; `HYDRAULIC_INITIAL_STATE`; `MACHINE_MODEL`; `OFFSET_DRIFT`; `OPERATION`; `OPERATOR_ROLE`; `PREPARATION_PROTOCOL`; `REFERENCE_STATE`; `REFERENCE_STANDARD`; `RIGHTS`; `SENSOR`; `SOFTWARE`; `UNCERTAINTY` |
| `upstream_pressure_availability` | `MEASURED`; `NOT_MEASURED`; `SENSOR_FAILURE` |
| `calibration_applicability` | `APPLICABLE`; `NOT_APPLICABLE`; `UNKNOWN_PENDING_REVIEW` |
| `resource_provenance_mode` | `INLINE_DECLARATION`; `SOURCE_FILE_BOUND` |
| `campaign_mapping_status` | `LOCKED_PUCKWORKS_CAMPAIGN`; `PUCKWORKS_MACHINE_MODE_CAMPAIGN_GAP_LOCAL_EXTENSION`; `FUTURE_PUCKWORKS_CAMPAIGN_PENDING` |
| `edge_role` | `INPUT`; `OUTPUT` |
| `operation_scope` | `ROW_VALUE`; `NORMALIZED_FILE_ASSEMBLY`; `COMPATIBILITY_EXPORT`; `SEALED_METADATA_ASSEMBLY` |
| `package_access_status` | `OPEN_AUTHORIZED`; `CALIBRATION_ACCESS`; `SEALED_UNACCESSED`; `AUTHORIZED_OPENED`; `CLOSED_AFTER_SCORING`; `PUBLIC_METADATA_ONLY` |
| `export_status` | `NOT_GENERATED`; `GENERATED_VERIFIED`; `NOT_APPLICABLE` |
| `fraction_chemistry_status` | `PRESENT`; `NOT_APPLICABLE_NO_FRACTIONATED_CHEMISTRY` |
| `package_content_mode` | `FULL_COMPATIBILITY_EXPORT`; `METADATA_CHECKSUM_ONLY`; `NOT_GENERATED`; `NOT_APPLICABLE` |
| `provenance_class` | `NORMALIZED_RECORD`; `TIME_INDEXED_SAMPLES`; `FROZEN_LITERAL` |
| `time_source_mode` | `EXACT_SAMPLE`; `LINEAR_INTERPOLATION`; `MISSING`; null for non-time provenance |
| `unit_conversion_mode` | `NONE`; `FIXED_SCALE_OFFSET`; `FLOW_DENSITY_CONVERSION` |
| `exported_row_state` | `RAW_NATIVE` only where the template prospectively permits raw-native presentation; `PROCESSED_SYNCHRONIZED`; `DERIVED_WITH_SYNCHRONIZED_SOURCES`; null only for non-time compatibility filenames |
| `event_status` | `OBSERVED`; `DERIVED`; `MISSING`; `AMBIGUOUS_RETAINED` |

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
  `campaign_instance_id` values are required. The first has a `CHARACTERIZATION`
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
state records plus the complete basket reference
(`shot_id`, `basket_pressure_signal_id`, `basket_pressure_sample_index`) and
complete upstream reference (`shot_id`, `upstream_pressure_signal_id`,
`upstream_pressure_sample_index`); it contains no independently authoritative
measured-pressure value. The basket reference is always present and resolves
to `physical_node=P_BASKET_BED_TOP_PA_GAUGE`. Upstream ID and index are both
present or both absent; a present reference resolves to
`physical_node=P_MACHINE_UPSTREAM_RU_PA_GAUGE`, and absence is allowed only
for `upstream_pressure_availability=NOT_MEASURED`. `SENSOR_FAILURE` retains a
referenced signal sample whose `missing_value_state=SENSOR_FAILURE`.

A control reference with `raw_or_processed=PROCESSED_SYNCHRONIZED` points to a
signal row with the same state and mandatory `value_processing_id`.
`control_deviation_pa` identifies the exact basket sample above and is derived
from that sample and `commanded_pressure_value`; any populated deviation
therefore requires the control row's `value_processing_id` to identify the deriving
operation.
If duplicated presentation values are exported later, they must be byte- and
value-derived from that signal row; conflicts resolve in favor of the signal
table and invalidate the export.

### Processing operation and edge-graph invariants

1. Every `processing_operations.processing_id` has at least one `INPUT` and
   one `OUTPUT` row in `processing_file_edges`; multiple inputs and outputs are
   permitted and ordered independently by `edge_sequence` within each role.
2. Every edge resolves to one operation and one
   `files.source_file_id`. The edge primary key prevents duplicate file/role
   membership in an operation.
3. Every processed or derived signal, control value, flow conversion,
   deformation value, chemistry value, or compatibility export references its
   producing operation. The output file containing that value has exactly one
   `OUTPUT` edge for that operation.
4. Each output file has exactly one producing operation across the entire edge
   table. Native/root files have `raw_or_processed=RAW_NATIVE`, have no
   `OUTPUT` edge, and may appear only as inputs.
5. The directed graph from input files through operations to output files is
   acyclic. A deterministic topological sort over files and operations must
   include every node; a cycle or orphan processed file invalidates the
   submission.
6. Synchronization is a `ROW_VALUE` operation and may consume multiple native
   channel files, but it emits only row-value artifacts. A distinct
   `NORMALIZED_FILE_ASSEMBLY` operation consumes those artifacts and emits
   complete authoritative normalized tables. From that layer exactly one of
   two export branches is permitted per generated package:
   `NORMALIZED_FILE_ASSEMBLY -> COMPATIBILITY_EXPORT` for full Puckworks
   presentation, or
   `NORMALIZED_FILE_ASSEMBLY -> SEALED_METADATA_ASSEMBLY` for the sealed
   metadata envelope. The sealed branch consumes only package, partition,
   terminal-rights, access-policy, seal, and checksum inputs and emits only
   `package_manifest.json`, `rights_access.json`, and `seal_identity.json`.
   Edges preserve provenance; no operation or package spans or mixes branches.
7. Every compatibility export field above is recomputed from its authoritative
   normalized source during verification. Exported/local disagreement,
   missing input edges, or ambiguous producing operations invalidate the
   export.
8. `ROW_VALUE` operations produce only raw/intermediate/synchronized row-value
   artifacts, never complete normalized tables or compatibility files.
   `NORMALIZED_FILE_ASSEMBLY` consumes row-value artifacts and produces only
   complete authoritative normalized submission tables.
   `COMPATIBILITY_EXPORT` consumes verified normalized files and produces only
   the partition-specific Puckworks presentation.
   `SEALED_METADATA_ASSEMBLY` consumes only the restricted normalized metadata
   inputs above and produces only the three sealed-envelope JSON files. Scope
   or output mixing invalidates the graph.
9. No file-to-file parent column supplies provenance. Reachability, complete
   input multiplicity, the unique producer, software identity, parameters,
   and output identity are reconstructed exclusively from operation rows and
   input/output edges.
10. `(processing_id, edge_role, edge_sequence)` is unique. Within each role,
    edge sequence starts at 1 and is gap-free; ordering is by that integer,
    never filesystem enumeration. Each operation declares exactly one scope,
    and every output file role is permitted by that scope.

### Cross-table relational invariants

1. `evidence_partitions.(campaign_instance_id, route_id)` must match the campaign
   candidate key; existence of each identifier separately is insufficient.
2. A replicate's (`condition_id`, `campaign_instance_id`) and (`block_id`,
   `campaign_instance_id`) must match the corresponding condition and block candidate
   keys.
3. A replicate's (`evidence_partition_id`, `campaign_instance_id`, `route_id`) must
   match one partition candidate key, and its (`campaign_instance_id`, `route_id`) must
   match its campaign.
4. A shot's duplicated campaign, route, condition, block, and partition fields
   must exactly equal those inherited through the complete replicate candidate
   key. Its (`condition_id`, `campaign_instance_id`, `apparatus_id`) must also match the
   condition candidate key, and its apparatus must equal the campaign instance's
   apparatus. Any mismatch rejects the row.
5. Every referenced pressure sample has the same `shot_id` as the control row.
   For `control_mode=PRESCRIBED_BASKET_PRESSURE`, the condition and every
   control row use `prescribed_node=P_BASKET_BED_TOP_PA_GAUGE`, and the basket
   reference resolves to that physical node.
6. For `control_mode=MACHINE_COUPLED`, the condition and every control row use
   `prescribed_node=NOT_APPLICABLE_MACHINE_COUPLED`; basket pressure remains a
   measured signal, never a prescribed value.
7. Route-specific partition roles, evidence classes, and sealing states must
   satisfy the selected route rules below. Ordinary replicates and blocks do
   not acquire holdout status independently of their partition.
8. Every local row carries or inherits exactly one `campaign_instance_id`.
   `puckworks_campaign_id` is never used as a local relational key.
9. `campaign_mapping_status=LOCKED_PUCKWORKS_CAMPAIGN` requires a catalog-valid
   non-null `puckworks_campaign_id`. Both gap/pending statuses require it to be
   null and prohibit compatibility export. The mapping status and selected
   route are frozen before commissioning.
10. A signal or deformation row's shot apparatus, registry apparatus, sensor,
    observable or node, native unit, and clock are identical. Calibration
    applicability and acquisition-time validity are enforced from that same
    registry row.
11. Fractions and chemistry inherit the shot's campaign, route, and evidence
    partition. Chemistry cannot exist without its exact fraction parent.
12. A compatibility package, its grid, every exported source row, all input
    files, and every exported shot belong to one campaign and one evidence
    partition. Route-B calibration and sealed-scoring partitions never share
    a package or processing operation.
13. Resource payloads validate against their type-specific schema. Every
    non-rights resource and file terminates in exactly one direct `RIGHTS`
    resource, and a rights resource has no rights or source-file parent.
14. Every synchronized export row has one frozen grid position and complete
    source-key records. Every achieved-mass value has one exact terminal
    delivered-mass source key selected by the frozen termination rule.
15. Package campaign, route, partition, Puckworks campaign, evidence class,
    access policy, terminal rights, access status, dataset status, and evidence
    level reconcile to one parent partition and campaign. Package counts and
    exclusion summaries use only rows in that partition.
16. Package shots, files, calibrations, fractions, chemistry, exclusions,
    source samples, grids, and processing inputs share the package partition.
    A Route-B calibration package has no edge, key, count, status, checksum,
    or derived dependency on a sealed-scoring partition.
17. A time-series-producing package has exactly one reciprocal package/grid
    pair and exactly one export operation of scope `COMPATIBILITY_EXPORT`.
    A normalized-file assembly operation cannot satisfy that reference.
18. Temperature export resolves only to registered
    `T_BASKET_BED_TOP_C` samples. Exact exports retain one source; interpolated
    exports retain two ordered, bracketing sources and frozen weights; missing
    exports retain no source and an explicit missing state.
19. `fraction_chemistry_status=PRESENT` is equivalent to a nonempty,
    reconciled package fraction set. The not-applicable state is equivalent to
    zero fraction and chemistry rows and emits neither fraction nor chemistry
    data files.
20. Campaign `(apparatus_id, site_id)` resolves to the apparatus candidate
    key. Package-relative compatibility filenames and partition-relative
    normalized filenames are unique. Export row keys match the exact
    filename-specific schemas, and every field of one time-series row has an
    identical `exported_row_state`.
21. A source row uses exactly one provenance class. Non-time record children
    have no elapsed time, weight, or sample state; time-indexed children have
    the frozen one- or two-source cardinality; literals have no children.
22. Fixed unit conversions retain exact scale and offset with null
    `flow_conversion_id`. Flow-density conversions require that ID. Pressure
    never references a flow conversion.
23. Every full package has one grid and one compatibility-export operation;
    metadata/checksum-only packages have the export operation but no grid;
    non-generated and not-applicable packages have neither. File sets are
    mutually exclusive by mode.
24. Every achieved beverage mass resolves to one realized shot-termination
    event and one eligible delivered-mass sample selected against its elapsed
    time. Missing or ambiguous events cannot silently select a mass.

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
