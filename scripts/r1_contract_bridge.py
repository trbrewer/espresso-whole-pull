#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

LOCK_PATH = Path("dependencies/puckworks.lock.json")
DOSSIER_PATH = Path("validation/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.json")
CONTRACT_PATH = Path("validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json")
R0_PATH = Path("config/reference_R0.json")
PROVENANCE_PATH = Path("validation/r1/WP01R_004_INPUT_PROVENANCE.json")
SCENARIO_PATH = Path("config/reconstruction_R1_waszkiewicz_9bar.json")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot load governed JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"governed JSON must be an object: {path}")
    return value


def pointer(document: Any, text: str) -> Any:
    value = document
    for token in text.strip("/").split("/") if text != "/" else []:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(token)]
        else:
            value = value[token]
    return value


def require_number(document: dict[str, Any], path: str) -> float:
    value = pointer(document, path)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SystemExit(f"required numeric value missing or invalid: {path}")
    return float(value)


def require_identity(lock: dict[str, Any], dossier: dict[str, Any], contract: dict[str, Any]) -> None:
    if lock.get("schema_version") != "espresso.public.puckworks_lock.v2":
        raise SystemExit("unsupported Puckworks lock schema")
    if dossier.get("schema_version") != "espresso.public.waszkiewicz_r1_source_dossier.v1":
        raise SystemExit("unsupported dossier schema")
    if contract.get("schema_version") != "espresso.public.r1_calibration_and_comparison_contract.v1":
        raise SystemExit("unsupported R1 contract schema")
    if contract.get("contract_status") != "FROZEN_FOR_WP01R_004":
        raise SystemExit("R1 contract is not frozen for WP01R-004")
    commit = lock.get("checkout_commit")
    tree = lock.get("checkout_tree_sha")
    if not isinstance(commit, str) or not HEX40.fullmatch(commit):
        raise SystemExit("invalid locked Puckworks commit")
    if not isinstance(tree, str) or not HEX40.fullmatch(tree):
        raise SystemExit("invalid locked Puckworks tree")
    source = contract.get("source_dependency", {})
    dependency = dossier.get("dependency_identity", {})
    if source.get("commit") != commit or source.get("tree") != tree:
        raise SystemExit("contract/Puckworks lock identity mismatch")
    if dependency.get("commit") != commit or dependency.get("tree") != tree:
        raise SystemExit("dossier/Puckworks lock identity mismatch")
    if contract.get("dossier_dependency", {}).get("disposition") != dossier.get(
        "dossier_disposition"
    ):
        raise SystemExit("contract/dossier disposition mismatch")
    calibration = contract.get("calibration_contract", {})
    if calibration.get("active_solver_calibration_degrees_of_freedom") != 1:
        raise SystemExit("contract must contain exactly one historical calibration degree")
    for field in (
        "runtime_adjustable_parameter_count",
        "generation_time_adjustable_parameter_count",
        "post_run_adjustable_parameter_count",
    ):
        if calibration.get(field) != 0:
            raise SystemExit(f"adjustable scientific parameters forbidden: {field}")
    protected = contract.get("protected_comparison_contract", {})
    if not isinstance(protected.get("shot_ids"), list) or not protected["shot_ids"]:
        raise SystemExit("protected shot identities absent")
    for field in ("protected_indices", "normalization_indices", "gates", "pearson_degeneracy"):
        if field not in protected:
            raise SystemExit(f"protected comparison contract incomplete: {field}")
    if "solver_to_source_flow_mapping" not in contract:
        raise SystemExit("solver/source flow mapping absent")


def build(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    lock_path, dossier_path, contract_path, r0_path = (
        root / LOCK_PATH,
        root / DOSSIER_PATH,
        root / CONTRACT_PATH,
        root / R0_PATH,
    )
    lock = load_json(lock_path)
    dossier = load_json(dossier_path)
    contract = load_json(contract_path)
    r0 = load_json(r0_path)
    require_identity(lock, dossier, contract)
    dossier_dependency = contract["dossier_dependency"]
    if sha256(dossier_path) != dossier_dependency["json"]["sha256"]:
        raise SystemExit("merged dossier JSON identity differs from frozen contract")
    dossier_markdown = root / dossier_dependency["markdown"]["path"]
    if sha256(dossier_markdown) != dossier_dependency["markdown"]["sha256"]:
        raise SystemExit("merged dossier Markdown identity differs from frozen contract")

    inputs = contract["scenario_inputs"]
    calibration = contract["calibration_contract"]
    pressure = contract["pressure_node_contract"]
    inlet = next(item for item in pressure if item["node"] == "BASKET_OR_PUCK_INLET_GAUGE")
    outlet = next(item for item in pressure if item["node"] == "BASKET_BOTTOM_AMBIENT_GAUGE")
    time_map = contract["time_mapping_contract"]
    numeric = contract["numerical_configuration"]
    boundary = contract["boundary_profile"]
    flow = contract["solver_to_source_flow_mapping"]
    protected = contract["protected_comparison_contract"]
    r0_wetting = r0["wetting"]
    r0_output = r0["output"]
    r0_verification = r0["verification"]

    scenario: dict[str, Any] = {
        "schema_version": "espresso.whole_pull.reconstruction_scenario.r1.v1",
        "scenario_id": "reconstruction_R1_waszkiewicz_18p5g_56mm_8p709bar",
        "solver": r0["solver"],
        "solver_version": r0["solver_version"],
        "openfoam_distribution": r0["openfoam_distribution"],
        "openfoam_version": r0["openfoam_version"],
        "mode": "source_linked_reconstruction",
        "governance": {
            "task": "WP01R-004",
            "issue": 6,
            "change_scope": "SOURCE_SCENARIO_CHANGE_ONLY",
            "governing_physics_change": False,
            "qualified_R0_scientific_configuration_change": False,
            "new_R1_scientific_configuration_added": True,
            "package_scientific_configuration_change": True,
            "new_governing_equation_or_closure": False,
            "contract_path": CONTRACT_PATH.as_posix(),
            "dossier_path": DOSSIER_PATH.as_posix(),
            "puckworks_lock_path": LOCK_PATH.as_posix(),
        },
        "geometry": {
            "hardware_basket_diameter_m": inputs["hardware_basket_diameter_m"],
            "basket_diameter_m": inputs["hydraulic_bed_diameter_m"],
            "basket_radius_m": inputs["hydraulic_bed_radius_m"],
            "hydraulic_bed_area_m2": inputs["hydraulic_bed_area_m2"],
            "wedge_angle_deg": r0["geometry"]["wedge_angle_deg"],
            "axial_cells": numeric["mesh"]["axial_cells"],
            "radial_cells": numeric["mesh"]["radial_cells"],
            "azimuthal_cells": numeric["mesh"]["azimuthal_cells"],
            "axial_grading": r0["geometry"]["axial_grading"],
            "radial_grading": r0["geometry"]["radial_grading"],
        },
        "coffee_bed": {
            "dry_dose_kg": inputs["dry_dose_kg"],
            "particle_solid_density_kg_m3": inputs["particle_solid_density_kg_m3"],
            "initial_porosity": inputs["initial_porosity"],
            "bed_depth_m": inputs["bed_depth_m"],
            "initial_extractable_fraction_dry_basis": inputs[
                "initial_extractable_fraction_dry_basis"
            ],
            "bed_depth_status": inputs["bed_depth_status"],
        },
        "liquid": {
            "temperature_K": inputs["temperature_K"],
            "density_kg_m3": inputs["liquid_density_kg_m3"],
            "dynamic_viscosity_Pa_s": inputs["dynamic_viscosity_Pa_s"],
            "effective_solute_diffusivity_m2_s": inputs[
                "effective_solute_diffusivity_m2_s"
            ],
        },
        "hydraulics": {
            "target_inlet_pressure_gauge_Pa": inlet["value_Pa_gauge"],
            "outlet_pressure_gauge_Pa": outlet["value_Pa_gauge"],
            "pressure_ramp_time_s": boundary["ramp_end_time_s"],
            "saturated_permeability_m2": calibration["saturated_permeability_m2"],
            "wetting_permeability_m2": calibration["wetting_permeability_m2"],
            "front_pressure_gauge_Pa": r0["hydraulics"]["front_pressure_gauge_Pa"],
            "gravity_enabled": r0["hydraulics"]["gravity_enabled"],
            "pressure_integration_method": r0["hydraulics"]["pressure_integration_method"],
            "permeability_profile": {
                "type": "uniform",
                "interface_position_m": inputs["bed_depth_m"] / 2.0,
                "upstream_permeability_m2": calibration["central_uniform_permeability_m2"],
                "downstream_permeability_m2": calibration["central_uniform_permeability_m2"],
            },
            "historically_calibrated_parameter_count": calibration[
                "historically_calibrated_scenario_parameter_count"
            ],
            "runtime_adjustable_parameter_count": calibration[
                "runtime_adjustable_parameter_count"
            ],
        },
        "wetting": r0_wetting,
        "extraction": {
            "model": r0["extraction"]["model"],
            "rate_constant_1_s": inputs["first_order_extraction_rate_1_s"],
            "saturation_concentration_kg_m3": inputs["capacity_concentration_kg_m3"],
            "status": "INHERITED_R0_UNCALIBRATED_UNSCORED",
        },
        "time": {
            "start_s": 0.0,
            "end_s": time_map["solver_end_time_s"],
            "delta_t_s": numeric["delta_t_s"],
            "field_write_interval_s": numeric["field_snapshot_interval_s"],
            "reduced_trace_maximum_interval_s": numeric[
                "reduced_flow_trace_maximum_interval_s"
            ],
            "target_beverage_mass_kg": r0["time"]["target_beverage_mass_kg"],
            "target_beverage_mass_role": "UNSCORED_DIAGNOSTIC_NOT_TERMINATION",
        },
        "parallel": {
            "default_subdomains": numeric["routine_mpi_ranks"],
            "decomposition_method": numeric["decomposition"],
        },
        "pressure_nodes": {
            "inlet": "BASKET_OR_PUCK_INLET_GAUGE",
            "outlet": "BASKET_BOTTOM_AMBIENT_GAUGE",
            "reference_bin": "REFERENCE_PRESSURE_BIN_CONTEXT_ONLY",
        },
        "source_time_mapping": {
            "solver_time_equals_source_time_plus_s": time_map[
                "source_to_solver_offset_s"
            ],
            "source_fixed_8s_offset_used": time_map[
                "source_first_drop_offset_8s_used"
            ],
        },
        "flow_comparison_contract": {
            "primary_predicted_quantity": flow["primary_predicted_quantity"],
            "secondary_unscored_diagnostic": flow["secondary_unscored_diagnostic"],
            "protected_shot_ids": protected["shot_ids"],
            "source_path": protected["source_path"],
            "source_selector": protected["source_selector"],
            "protected_indices": protected["protected_indices"],
            "normalization_indices": protected["normalization_indices"],
            "gates": protected["gates"],
            "pearson_degeneracy": protected["pearson_degeneracy"],
            "protected_series_embedded": False,
        },
        "claim_ceiling": contract["claim_ceiling"]["statement"],
        "output": r0_output,
        "verification": r0_verification,
        "execution_boundaries": {
            "analytical_preflight_execution_count": 1,
            "reduced_preflight_execution_count": 1,
            "openfoam_execution_count": 0,
            "protected_comparison_execution_count": 0,
            "scientific_result_status": "NOT_RUN",
            "parameter_fitting_count": 0,
            "optimizer_iteration_count": 0,
            "puckworks_code_execution_count": 0,
        },
    }

    contract_hash = sha256(contract_path)
    dossier_hash = sha256(dossier_path)
    r0_hash = sha256(r0_path)
    records: list[dict[str, Any]] = []
    generated_entries = {
        "/geometry/basket_radius_m": [
            {"dictionary": "system/blockMeshDict", "keyword": "vertices"},
            {"dictionary": "constant/espressoModelProperties", "keyword": "basketRadius"},
        ],
        "/geometry/wedge_angle_deg": [
            {"dictionary": "system/blockMeshDict", "keyword": "vertices"},
            {"dictionary": "constant/espressoModelProperties", "keyword": "wedgeAngleDegrees"},
        ],
        "/geometry/axial_cells": [{"dictionary": "system/blockMeshDict", "keyword": "blocks"}],
        "/geometry/radial_cells": [{"dictionary": "system/blockMeshDict", "keyword": "blocks"}],
        "/geometry/azimuthal_cells": [{"dictionary": "system/blockMeshDict", "keyword": "blocks"}],
        "/geometry/axial_grading": [{"dictionary": "system/blockMeshDict", "keyword": "simpleGrading"}],
        "/geometry/radial_grading": [{"dictionary": "system/blockMeshDict", "keyword": "simpleGrading"}],
        "/coffee_bed/bed_depth_m": [
            {"dictionary": "system/blockMeshDict", "keyword": "vertices"},
            {"dictionary": "constant/espressoModelProperties", "keyword": "bedDepth"},
        ],
        "/coffee_bed/dry_dose_kg": [{"dictionary": "constant/espressoModelProperties", "keyword": "dryDose"}],
        "/coffee_bed/initial_porosity": [{"dictionary": "constant/espressoModelProperties", "keyword": "initialPorosity"}],
        "/coffee_bed/initial_extractable_fraction_dry_basis": [{"dictionary": "constant/espressoModelProperties", "keyword": "extractableFraction"}],
        "/liquid/density_kg_m3": [{"dictionary": "constant/espressoModelProperties", "keyword": "liquidDensity"}],
        "/liquid/dynamic_viscosity_Pa_s": [{"dictionary": "constant/espressoModelProperties", "keyword": "dynamicViscosity"}],
        "/liquid/effective_solute_diffusivity_m2_s": [{"dictionary": "constant/espressoModelProperties", "keyword": "effectiveSoluteDiffusivity"}],
        "/hydraulics/target_inlet_pressure_gauge_Pa": [{"dictionary": "constant/espressoModelProperties", "keyword": "targetInletPressure"}],
        "/hydraulics/outlet_pressure_gauge_Pa": [{"dictionary": "constant/espressoModelProperties", "keyword": "outletPressure"}],
        "/hydraulics/front_pressure_gauge_Pa": [{"dictionary": "constant/espressoModelProperties", "keyword": "frontPressure"}],
        "/hydraulics/pressure_ramp_time_s": [{"dictionary": "constant/espressoModelProperties", "keyword": "pressureRampTime"}],
        "/hydraulics/saturated_permeability_m2": [{"dictionary": "constant/espressoModelProperties", "keyword": "saturatedPermeability"}],
        "/hydraulics/wetting_permeability_m2": [{"dictionary": "constant/espressoModelProperties", "keyword": "wettingPermeability"}],
        "/wetting/initial_wet_front_m": [{"dictionary": "constant/espressoModelProperties", "keyword": "initialWetFront"}],
        "/extraction/rate_constant_1_s": [{"dictionary": "constant/espressoModelProperties", "keyword": "extractionRateConstant"}],
        "/extraction/saturation_concentration_kg_m3": [{"dictionary": "constant/espressoModelProperties", "keyword": "saturationConcentration"}],
        "/time/end_s": [{"dictionary": "system/controlDict", "keyword": "endTime"}],
        "/time/delta_t_s": [{"dictionary": "system/controlDict", "keyword": "deltaT"}],
        "/time/field_write_interval_s": [{"dictionary": "system/controlDict", "keyword": "writeInterval"}],
        "/time/target_beverage_mass_kg": [{"dictionary": "constant/espressoModelProperties", "keyword": "targetBeverageMass"}],
        "/parallel/default_subdomains": [{"dictionary": "system/decomposeParDict", "keyword": "numberOfSubdomains"}],
    }

    def record(
        destination: str,
        unit: str,
        origin: str,
        source_path: Path,
        source_pointer: str,
        *,
        generated_dictionary: str | None = None,
        generated_keyword: str | None = None,
        formula: str | None = None,
        pressure_node: str | None = None,
        time_origin: str | None = None,
        evidence_role: str = "PRESCRIBED_INPUT",
        limitation: str | None = None,
    ) -> None:
        records.append(
            {
                "field_id": destination.strip("/").replace("/", "."),
                "destination_scenario_json_pointer": destination,
                "generated_dictionary": generated_dictionary,
                "generated_keyword": generated_keyword,
                "generated_dictionary_entries": generated_entries.get(destination, []),
                "value": pointer(scenario, destination),
                "unit": unit,
                "basis": evidence_role,
                "origin_class": origin,
                "source_document_path": source_path.as_posix(),
                "source_json_pointer": source_pointer,
                "source_content_sha256": {
                    CONTRACT_PATH: contract_hash,
                    DOSSIER_PATH: dossier_hash,
                    R0_PATH: r0_hash,
                }[source_path],
                "formula_or_unit_conversion": formula,
                "pressure_node": pressure_node,
                "time_origin": time_origin,
                "evidence_role": evidence_role,
                "adjustable_status": "FROZEN_NOT_ADJUSTABLE",
                "unresolved_limitation": limitation,
            }
        )

    contract_fields = {
        "/geometry/hardware_basket_diameter_m": ("/scenario_inputs/hardware_basket_diameter_m", "m"),
        "/geometry/basket_diameter_m": ("/scenario_inputs/hydraulic_bed_diameter_m", "m"),
        "/geometry/basket_radius_m": ("/scenario_inputs/hydraulic_bed_radius_m", "m"),
        "/geometry/hydraulic_bed_area_m2": ("/scenario_inputs/hydraulic_bed_area_m2", "m2"),
        "/geometry/axial_cells": ("/numerical_configuration/mesh/axial_cells", "count"),
        "/geometry/radial_cells": ("/numerical_configuration/mesh/radial_cells", "count"),
        "/geometry/azimuthal_cells": ("/numerical_configuration/mesh/azimuthal_cells", "count"),
        "/coffee_bed/dry_dose_kg": ("/scenario_inputs/dry_dose_kg", "kg"),
        "/coffee_bed/particle_solid_density_kg_m3": ("/scenario_inputs/particle_solid_density_kg_m3", "kg/m3"),
        "/coffee_bed/initial_porosity": ("/scenario_inputs/initial_porosity", "1"),
        "/coffee_bed/bed_depth_m": ("/scenario_inputs/bed_depth_m", "m"),
        "/coffee_bed/initial_extractable_fraction_dry_basis": ("/scenario_inputs/initial_extractable_fraction_dry_basis", "1"),
        "/liquid/temperature_K": ("/scenario_inputs/temperature_K", "K"),
        "/liquid/density_kg_m3": ("/scenario_inputs/liquid_density_kg_m3", "kg/m3"),
        "/liquid/dynamic_viscosity_Pa_s": ("/scenario_inputs/dynamic_viscosity_Pa_s", "Pa s"),
        "/liquid/effective_solute_diffusivity_m2_s": ("/scenario_inputs/effective_solute_diffusivity_m2_s", "m2/s"),
        "/hydraulics/target_inlet_pressure_gauge_Pa": ("/pressure_node_contract/2/value_Pa_gauge", "Pa"),
        "/hydraulics/outlet_pressure_gauge_Pa": ("/pressure_node_contract/3/value_Pa_gauge", "Pa"),
        "/hydraulics/pressure_ramp_time_s": ("/boundary_profile/ramp_end_time_s", "s"),
        "/hydraulics/saturated_permeability_m2": ("/calibration_contract/saturated_permeability_m2", "m2"),
        "/hydraulics/wetting_permeability_m2": ("/calibration_contract/wetting_permeability_m2", "m2"),
        "/hydraulics/historically_calibrated_parameter_count": ("/calibration_contract/historically_calibrated_scenario_parameter_count", "count"),
        "/hydraulics/runtime_adjustable_parameter_count": ("/calibration_contract/runtime_adjustable_parameter_count", "count"),
        "/extraction/rate_constant_1_s": ("/scenario_inputs/first_order_extraction_rate_1_s", "1/s"),
        "/extraction/saturation_concentration_kg_m3": ("/scenario_inputs/capacity_concentration_kg_m3", "kg/m3"),
        "/time/end_s": ("/time_mapping_contract/solver_end_time_s", "s"),
        "/time/delta_t_s": ("/numerical_configuration/delta_t_s", "s"),
        "/time/field_write_interval_s": ("/numerical_configuration/field_snapshot_interval_s", "s"),
        "/time/reduced_trace_maximum_interval_s": ("/numerical_configuration/reduced_flow_trace_maximum_interval_s", "s"),
        "/parallel/default_subdomains": ("/numerical_configuration/routine_mpi_ranks", "count"),
        "/source_time_mapping/solver_time_equals_source_time_plus_s": ("/time_mapping_contract/source_to_solver_offset_s", "s"),
        "/source_time_mapping/source_fixed_8s_offset_used": ("/time_mapping_contract/source_first_drop_offset_8s_used", "boolean"),
        "/flow_comparison_contract/primary_predicted_quantity": ("/solver_to_source_flow_mapping/primary_predicted_quantity", "structured contract"),
        "/flow_comparison_contract/secondary_unscored_diagnostic": ("/solver_to_source_flow_mapping/secondary_unscored_diagnostic", "structured contract"),
        "/flow_comparison_contract/protected_shot_ids": ("/protected_comparison_contract/shot_ids", "identifiers"),
        "/flow_comparison_contract/source_path": ("/protected_comparison_contract/source_path", "logical path"),
        "/flow_comparison_contract/source_selector": ("/protected_comparison_contract/source_selector", "selector"),
        "/flow_comparison_contract/protected_indices": ("/protected_comparison_contract/protected_indices", "zero-based inclusive indices"),
        "/flow_comparison_contract/normalization_indices": ("/protected_comparison_contract/normalization_indices", "zero-based inclusive indices"),
        "/flow_comparison_contract/gates": ("/protected_comparison_contract/gates", "structured thresholds"),
        "/flow_comparison_contract/pearson_degeneracy": ("/protected_comparison_contract/pearson_degeneracy", "structured threshold"),
    }
    for dest, (src, unit) in contract_fields.items():
        record(dest, unit, "FROZEN_R1_CONTRACT", CONTRACT_PATH, src)

    inherited = {
        "/geometry/wedge_angle_deg": "/geometry/wedge_angle_deg",
        "/geometry/axial_grading": "/geometry/axial_grading",
        "/geometry/radial_grading": "/geometry/radial_grading",
        "/hydraulics/front_pressure_gauge_Pa": "/hydraulics/front_pressure_gauge_Pa",
        "/hydraulics/gravity_enabled": "/hydraulics/gravity_enabled",
        "/hydraulics/pressure_integration_method": "/hydraulics/pressure_integration_method",
        "/wetting/model": "/wetting/model",
        "/wetting/front_smoothing_cells": "/wetting/front_smoothing_cells",
        "/wetting/initial_saturation": "/wetting/initial_saturation",
        "/wetting/initial_wet_front_m": "/wetting/initial_wet_front_m",
        "/time/target_beverage_mass_kg": "/time/target_beverage_mass_kg",
        "/time/start_s": "/time/start_s",
        "/parallel/decomposition_method": "/parallel/decomposition_method",
        "/extraction/model": "/extraction/model",
        "/output": "/output",
        "/verification": "/verification",
    }
    for dest, src in inherited.items():
        record(dest, "see source", "INHERITED_FROZEN_R0", R0_PATH, src)

    for destination, formula in (
        ("/hydraulics/permeability_profile/type", "uniform profile frozen by R1 contract"),
        ("/hydraulics/permeability_profile/interface_position_m", "bed_depth_m / 2"),
        ("/hydraulics/permeability_profile/upstream_permeability_m2", "central uniform permeability"),
        ("/hydraulics/permeability_profile/downstream_permeability_m2", "central uniform permeability"),
    ):
        record(
            destination,
            "see destination",
            "DERIVED_FROM_FROZEN_R1_CONTRACT",
            CONTRACT_PATH,
            "/calibration_contract/central_uniform_permeability_m2",
            formula=formula,
        )

    provenance = {
        "schema_version": "espresso.public.wp01r_004_input_provenance.v1",
        "task": "WP01R-004",
        "issue": 6,
        "scenario_path": SCENARIO_PATH.as_posix(),
        "records": records,
        "scientific_fields_consumed_by_generator": len(records),
        "scientific_fields_with_provenance": len(records),
        "provenance_coverage_percent": 100.0,
        "ungoverned_scientific_defaults": 0,
        "runtime_adjustable_scientific_parameters": 0,
        "change_scope": {
            "governing_physics_change": False,
            "package_scientific_configuration_change": True,
            "scientific_configuration_change_scope": "NEW_R1_SCENARIO_ONLY",
            "qualified_R0_scientific_configuration_change": False,
            "new_R1_scientific_configuration_added": True,
        },
    }
    return scenario, provenance


def verify_checkout(path: Path, commit: str, tree: str) -> None:
    head = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    observed_tree = subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD^{tree}"], text=True
    ).strip()
    status = subprocess.check_output(
        ["git", "-C", str(path), "status", "--porcelain"], text=True
    )
    branch = subprocess.run(
        ["git", "-C", str(path), "symbolic-ref", "-q", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if head != commit or observed_tree != tree or status or branch.returncode == 0:
        raise SystemExit("Puckworks checkout is not the exact clean detached lock")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--verify-puckworks-checkout", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    scenario, provenance = build(root)
    lock = load_json(root / LOCK_PATH)
    if args.verify_puckworks_checkout:
        verify_checkout(
            args.verify_puckworks_checkout.resolve(),
            lock["checkout_commit"],
            lock["checkout_tree_sha"],
        )
    expected = canonical_bytes(scenario)
    provenance_bytes = canonical_bytes(provenance)
    provenance_path = root / PROVENANCE_PATH
    if args.check:
        if output.read_bytes() != expected:
            raise SystemExit("committed canonical R1 scenario differs from bridge output")
        if provenance_path.read_bytes() != provenance_bytes:
            raise SystemExit("committed R1 provenance differs from bridge output")
        print("R1 bridge check: PASS")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(expected)
    provenance_path.write_bytes(provenance_bytes)
    print(json.dumps({"scenario": str(output), "provenance": str(provenance_path)}, indent=2))


if __name__ == "__main__":
    main()
