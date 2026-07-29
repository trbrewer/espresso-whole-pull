#!/usr/bin/env python3
"""Generate and evaluate the WP-0.3C Stage-0 input scaffold."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping

BASELINE_COMMIT = "258b4b6526acea98346031ae5cc9c9e7b3ee64a9"
BASELINE_TREE = "2fd9ae4a2e0040602daa29a4b5b4a7bc0ff899b9"
DISPOSITION = "STAGE0_SCAFFOLD_COMPLETE_AWAITING_HUMAN_INPUTS"
CLASSIFICATIONS = {
    "PUBLIC_PROTOCOL_INPUT", "PUBLIC_EQUIPMENT_METADATA",
    "PRIVATE_PERSONAL_INPUT", "PRIVATE_OPERATIONAL_INPUT",
    "SEALED_ACQUISITION_INPUT", "MEASURED_COMMISSIONING_INPUT",
    "MEASURED_HOLDOUT_INPUT", "DERIVED_NON_SCORE_BEARING_INPUT",
    "PROHIBITED_DURING_WP_0_3C",
}
DEADLINES = {
    "REQUIRED_BEFORE_PROTOCOL_DESIGN", "REQUIRED_BEFORE_COMMISSIONING",
    "REQUIRED_BEFORE_FINAL_PREREGISTRATION",
    "REQUIRED_BEFORE_HOLDOUT_ACQUISITION", "GENERATED_DURING_ACQUISITION",
    "REQUIRED_ONLY_FOR_FUTURE_WP_0_3D",
}

CATEGORIES = {
    "governance_and_roles": (
        "ROLE_PROTOCOL_OWNER", "PRIVATE_PERSONAL_INPUT",
        "REQUIRED_BEFORE_PROTOCOL_DESIGN",
        ["repository_owner", "protocol_owner", "acquisition_operator",
         "calibration_reviewer", "data_custodian", "future_analysis_operator",
         "scientific_reviewer", "safety_authority", "permitted_role_overlaps",
         "conflict_of_interest_and_independence_declaration"]),
    "campaign_scope": (
        "ROLE_PROTOCOL_OWNER", "PUBLIC_PROTOCOL_INPUT",
        "REQUIRED_BEFORE_PROTOCOL_DESIGN",
        ["campaign_location_class", "intended_independence_dimensions",
         "coffee_material_scope", "machine_scope", "basket_scope",
         "target_scientific_question", "machine_headspace_discrimination_intended",
         "bed_only_pressure_drop_measurable", "public_data_release_level",
         "budget_procurement_constraints", "scheduling_constraints"]),
    "machine_and_hydraulic_apparatus": (
        "ROLE_ACQUISITION_OPERATOR", "PUBLIC_EQUIPMENT_METADATA",
        "REQUIRED_BEFORE_COMMISSIONING",
        ["machine_manufacturer", "machine_model", "pressure_control_capability",
         "accessible_pressure_ports", "pump_type", "valve_configuration",
         "preinfusion_capability", "pressure_program_capability",
         "temperature_control_capability", "data_interface",
         "safe_operating_limits", "basket_portafilter_compatibility",
         "outlet_configuration"]),
    "basket_and_bed_geometry": (
        "ROLE_PROTOCOL_OWNER", "PUBLIC_EQUIPMENT_METADATA",
        "REQUIRED_BEFORE_COMMISSIONING",
        ["basket_manufacturer", "basket_model", "nominal_diameter",
         "measured_inside_diameter_procedure", "bed_area_calculation",
         "basket_depth", "hole_open_area_metadata", "puck_screen_paper_filter_plan",
         "initial_bed_depth_measurement", "post_shot_bed_depth_measurement"]),
    "pressure_instrumentation": (
        "ROLE_CALIBRATION_REVIEWER", "PUBLIC_EQUIPMENT_METADATA",
        "REQUIRED_BEFORE_COMMISSIONING",
        ["equipment_id", "manufacturer", "model", "sensing_type", "range",
         "resolution", "stated_accuracy", "pressure_basis", "sample_rate",
         "timestamp_capability", "expected_sensor_location",
         "tubing_impulse_line_details", "calibration_method",
         "calibration_reference_availability", "procurement_status"]),
    "mass_and_flow_instrumentation": (
        "ROLE_CALIBRATION_REVIEWER", "PUBLIC_EQUIPMENT_METADATA",
        "REQUIRED_BEFORE_COMMISSIONING",
        ["scale_manufacturer_model", "range", "resolution", "dynamic_sample_rate",
         "data_export_capability", "dynamic_response_characterization_capability",
         "direct_flow_meter", "calibration_masses", "traceability_status",
         "outlet_vessel_arrangement"]),
    "temperature_instrumentation": (
        "ROLE_CALIBRATION_REVIEWER", "PUBLIC_EQUIPMENT_METADATA",
        "REQUIRED_BEFORE_COMMISSIONING",
        ["sensor_type", "manufacturer_model", "range", "resolution",
         "sample_rate", "location", "calibration_reference", "expected_lag",
         "basket_inlet_temperature_directly_measurable"]),
    "time_synchronization_and_logging": (
        "ROLE_ACQUISITION_OPERATOR", "PRIVATE_OPERATIONAL_INPUT",
        "REQUIRED_BEFORE_COMMISSIONING",
        ["acquisition_computer_logger_class", "supported_channels", "clock_source",
         "synchronization_mechanism", "timestamp_resolution", "file_format",
         "data_loss_handling", "software_firmware_versions",
         "credentials_hostnames_excluded_from_git"]),
    "coffee_and_materials": (
        "ROLE_PROTOCOL_OWNER", "PUBLIC_PROTOCOL_INPUT",
        "REQUIRED_BEFORE_FINAL_PREREGISTRATION",
        ["coffee_availability", "roaster", "coffee_identity", "roast_date_lot",
         "intended_quantity", "storage_plan", "roast_age_window",
         "moisture_measurement_capability", "water_recipe",
         "water_chemistry_measurement", "grinder_manufacturer_model", "burr_type",
         "grinder_condition", "psd_measurement_capability"]),
    "preparation_controls": (
        "ROLE_PROTOCOL_OWNER", "PUBLIC_PROTOCOL_INPUT",
        "REQUIRED_BEFORE_FINAL_PREREGISTRATION",
        ["target_dose", "weighing_capability", "distribution_method",
         "tamp_device", "tamp_force_stress_measurement", "bed_depth_measurement",
         "grinding_to_brewing_timing", "cleaning_procedure",
         "grinder_purge_procedure", "operator_training_plan"]),
    "calibration_resources": (
        "ROLE_CALIBRATION_REVIEWER", "PUBLIC_PROTOCOL_INPUT",
        "REQUIRED_BEFORE_COMMISSIONING",
        ["pressure_reference", "traceable_masses", "temperature_reference",
         "ascending_descending_pressure_calibration_capability",
         "scale_dynamic_response_test_capability", "clock_offset_drift_capability",
         "post_campaign_verification_capability"]),
    "commissioning_resources": (
        "ROLE_PROTOCOL_OWNER", "PUBLIC_PROTOCOL_INPUT",
        "REQUIRED_BEFORE_COMMISSIONING",
        ["non_holdout_shots_available", "coffee_reserved_for_commissioning",
         "safe_pressure_conditions", "personnel_availability",
         "equipment_change_criteria_before_preregistration",
         "expected_repeatability_information"]),
    "data_custody_and_blinding": (
        "ROLE_DATA_CUSTODIAN", "PRIVATE_OPERATIONAL_INPUT",
        "REQUIRED_BEFORE_HOLDOUT_ACQUISITION",
        ["raw_data_storage_location_class", "backup_location_class",
         "data_custodian", "access_control_method", "encryption_method",
         "key_custodian", "condition_map_custodian", "private_public_split",
         "data_release_policy", "retention_period"]),
}

TEMPLATES = {
    "WP_0_3C_ROLE_ASSIGNMENT_TEMPLATE.json": ["governance_and_roles"],
    "WP_0_3C_CAMPAIGN_SCOPE_TEMPLATE.json": ["campaign_scope"],
    "WP_0_3C_APPARATUS_INVENTORY_TEMPLATE.json":
        ["machine_and_hydraulic_apparatus", "basket_and_bed_geometry"],
    "WP_0_3C_SENSOR_INVENTORY_TEMPLATE.json":
        ["pressure_instrumentation", "mass_and_flow_instrumentation",
         "temperature_instrumentation", "time_synchronization_and_logging"],
    "WP_0_3C_MATERIAL_AND_COFFEE_TEMPLATE.json": ["coffee_and_materials"],
    "WP_0_3C_PREPARATION_PROTOCOL_TEMPLATE.json": ["preparation_controls"],
    "WP_0_3C_CALIBRATION_PLAN_TEMPLATE.json": ["calibration_resources"],
    "WP_0_3C_COMMISSIONING_PLAN_TEMPLATE.json": ["commissioning_resources"],
    "WP_0_3C_DATA_CUSTODY_TEMPLATE.json": ["data_custody_and_blinding"],
    "WP_0_3C_PRIVACY_AND_PUBLICATION_TEMPLATE.json":
        ["governance_and_roles", "data_custody_and_blinding"],
    "WP_0_3C_ACQUISITION_READINESS_TEMPLATE.json": list(CATEGORIES),
}


def unresolved(role: str, deadline: str, classification: str) -> Dict[str, object]:
    return {
        "status": "UNRESOLVED_HUMAN_INPUT",
        "required_before": deadline,
        "responsible_role_id": role,
        "input_classification": classification,
        "public_repository_value_allowed":
            classification not in {"PRIVATE_PERSONAL_INPUT", "PRIVATE_OPERATIONAL_INPUT",
                                   "SEALED_ACQUISITION_INPUT", "MEASURED_HOLDOUT_INPUT"},
        "private_value_required":
            classification in {"PRIVATE_PERSONAL_INPUT", "PRIVATE_OPERATIONAL_INPUT"},
    }


def requirement_entries() -> List[Dict[str, object]]:
    entries = []
    for category, (role, classification, deadline, fields) in CATEGORIES.items():
        for field in fields:
            entries.append({
                "requirement_id": f"{category.upper()}__{field.upper()}",
                "category": category,
                "field": field,
                "input_classification": classification,
                "deadline": deadline,
                "responsible_role_id": role,
            })
    return entries


def evaluate_readiness(values: Iterable[Mapping[str, object]],
                       authority: bool = True) -> str:
    if not authority:
        return "AUTHORITY_NOT_ESTABLISHED"
    values = list(values)
    if not values or all(v.get("status") == "UNRESOLVED_HUMAN_INPUT" for v in values):
        return DISPOSITION
    if any(v.get("status") == "UNRESOLVED_HUMAN_INPUT" for v in values):
        return "HUMAN_INPUTS_PARTIALLY_COMPLETE"
    return "READY_FOR_CALIBRATION_PLANNING"


def _template(categories: Iterable[str]) -> Dict[str, object]:
    fields: Dict[str, object] = {}
    for category in categories:
        role, classification, deadline, names = CATEGORIES[category]
        fields[category] = {
            name: unresolved(role, deadline, classification) for name in names
        }
    return {
        "schema_version": "espresso.public.wp_0_3c_stage0_input_template.v1",
        "task": "WP-0.3C-0",
        "template_status": "NONFINAL_INPUT_TEMPLATE",
        "final_preregistration": False,
        "experimental_execution_authorized": False,
        "unresolved_value_policy": "UNRESOLVED_HUMAN_INPUT_ONLY",
        "fields": fields,
    }


def write_scaffold(root: Path) -> None:
    campaign = root / "validation/campaign/wp03c"
    templates = campaign / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    registry = {
        "schema_version": "espresso.public.wp_0_3c_stage0_requirements.v1",
        "task": "WP-0.3C-0",
        "input_classification_vocabulary": sorted(CLASSIFICATIONS),
        "deadline_vocabulary": sorted(DEADLINES),
        "requirements": requirement_entries(),
        "public_private_boundary": {
            "public_repository_package": [
                "role IDs", "campaign design", "equipment make/model",
                "opaque equipment IDs", "sensor specifications",
                "calibration methods", "protocol", "uncertainty requirements",
                "hashes", "public-safe location classes", "acquisition status",
                "non-sensitive provenance"],
            "private_campaign_custody_package": [
                "names and contact details", "private laboratory address",
                "sensitive serial numbers", "credentials", "private storage paths",
                "encryption keys", "condition-code map",
                "private raw data before authorized release"],
            "public_binding": "HASH_PRIVATE_PACKAGE_WITHOUT_DISCLOSURE_WHERE_APPROPRIATE",
        },
        "readiness": {
            "allowed_states": [
                "AUTHORITY_NOT_ESTABLISHED", DISPOSITION,
                "HUMAN_INPUTS_PARTIALLY_COMPLETE", "APPARATUS_NOT_AVAILABLE",
                "APPARATUS_PROCUREMENT_REQUIRED", "READY_FOR_CALIBRATION_PLANNING",
                "READY_FOR_NONHOLDOUT_COMMISSIONING",
                "READY_TO_FREEZE_FINAL_PREREGISTRATION",
                "FINAL_PREREGISTRATION_FROZEN"],
            "current_state": DISPOSITION,
        },
    }
    (campaign / "WP_0_3C_INPUT_REQUIREMENTS.json").write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name, categories in TEMPLATES.items():
        (templates / name).write_text(
            json.dumps(_template(categories), indent=2, sort_keys=True) + "\n",
            encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        write_scaffold(args.root.resolve())
    print(json.dumps({"status": "PASS", "readiness": DISPOSITION}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
