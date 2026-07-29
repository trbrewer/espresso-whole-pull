#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from espresso_reference_math import analytical_preview

CONTRACT = Path("validation/wp02/WP02_001_CLOSURE_CONTRACT.json")
BASE = Path("config/reconstruction_R1_waszkiewicz_9bar.json")
LOCK = Path("dependencies/puckworks.lock.json")
OUTPUTS = {
    "nine_bar_reconstruction": Path("config/reconstruction_WP02A_waszkiewicz_9bar.json"),
    "eight_bar_transfer": Path("config/reconstruction_WP02A_waszkiewicz_8bar.json"),
    "uniform_pressure_fixture": Path("config/fixture_WP02_001_uniform_pressure.json"),
}


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def scenario(root: Path, pressure: str) -> dict:
    contract = load(root / CONTRACT)
    base = load(root / BASE)
    lock = load(root / LOCK)
    if contract["contract_status"] != "FROZEN_BEFORE_SCIENTIFIC_EXECUTION":
        raise ValueError("closure contract is not frozen")
    source = contract["source_dependency"]
    if (
        lock["checkout_commit"] != source["commit"]
        or lock["checkout_tree_sha"] != source["tree"]
    ):
        raise ValueError("Puckworks identity mismatch")
    cfg = copy.deepcopy(base)
    fixture = pressure == "uniform_pressure_fixture"
    choice = contract["nine_bar_reconstruction"] if fixture else contract[pressure]
    is_eight = pressure == "eight_bar_transfer"
    cfg["schema_version"] = "espresso.whole_pull.reconstruction_scenario.wp02a.v1"
    cfg["scenario_id"] = (
        "fixture_WP02_001_uniform_pressure"
        if fixture
        else
        "reconstruction_WP02A_waszkiewicz_18p5g_56mm_7p566bar"
        if is_eight
        else "reconstruction_WP02A_waszkiewicz_18p5g_56mm_8p709bar"
    )
    if fixture:
        cfg["mode"] = "verification_fixture"
        cfg["fixture_role"] = "CLOSED_FORM_TO_OPENFOAM_EFFECTIVE_PERMEABILITY_VERIFICATION"
        cfg["physical_validation_role"] = "NOT_APPLICABLE_CODE_VERIFICATION"
        cfg["geometry"].update({"axial_cells": 64, "radial_cells": 32, "azimuthal_cells": 1, "axial_grading": 1.0, "radial_grading": 1.0})
        cfg["wetting"]["initial_saturation"] = 1.0
        cfg["wetting"]["initial_wet_front_m"] = cfg["coffee_bed"]["bed_depth_m"]
        cfg["hydraulics"]["pressure_ramp_time_s"] = 0.0
        cfg["coffee_bed"]["initial_extractable_fraction_dry_basis"] = 0.0
        cfg["extraction"]["rate_constant_1_s"] = 0.0
        cfg["liquid"]["effective_solute_diffusivity_m2_s"] = 0.0
        cfg["time"].update({"start_s": 0.0, "end_s": 103.0, "delta_t_s": 1.0, "field_write_interval_s": 1.0})
        serialization = contract["fixture_output_serialization"]
        cfg["output"].update(
            {
                "write_format": serialization["format"],
                "write_compression": False,
                "write_precision_digits": serialization[
                    "field_write_precision_digits"
                ],
            }
        )
        cfg["parallel"]["default_subdomains"] = 1
        half_width = 0.51 * cfg["coffee_bed"]["bed_depth_m"] / 64
        cfg["verification"]["pressure_probes"] = [
            {"name": "quarter_depth", "position_m": 0.0025, "half_width_m": half_width},
            {"name": "three_quarter_depth", "position_m": 0.0075, "half_width_m": half_width}
        ]
        cfg["verification"]["fixture_contract"] = contract["uniform_pressure_fixture"]
        cfg.pop("flow_comparison_contract", None)
    cfg["governance"] = {
        "task": "WP02-001",
        "issue": 18,
        "change_declaration": "GOVERNING_PHYSICS_CHANGE",
        "closure_contract_path": CONTRACT.as_posix(),
        "base_R1_path": BASE.as_posix(),
        "puckworks_lock_path": LOCK.as_posix(),
        "frozen_R0_configuration_change": False,
        "constant_R1_configuration_change": False,
    }
    if is_eight and not fixture:
        p_bar = choice["late_basket_pressure_bar"]
        permeability = choice["static_permeability_m2"]
        cfg["hydraulics"]["target_inlet_pressure_gauge_Pa"] = p_bar * 100000.0
        cfg["hydraulics"]["saturated_permeability_m2"] = permeability
        cfg["hydraulics"]["wetting_permeability_m2"] = permeability
        cfg["hydraulics"]["permeability_profile"]["upstream_permeability_m2"] = permeability
        cfg["hydraulics"]["permeability_profile"]["downstream_permeability_m2"] = permeability
        cfg["flow_comparison_contract"]["protected_shot_ids"] = choice["shot_ids"]
        cfg["flow_comparison_contract"]["source_selector"] = (
            "reference_pressure_round__bar == 8.0; shot_id in protected list; "
            "mass_flow_rate__g_per_s"
        )
        cfg["flow_comparison_contract"]["gates"] = {
            "median_normalized_shape_rmse_max": choice["gates"]["median_rmse_max"],
            "median_pearson_r_min": choice["gates"]["median_pearson_min"],
            "shot_count": 4,
            "shots_required_at_or_above_r_0_90": choice["gates"]["shots_required_pearson"],
            "shots_required_at_or_below_rmse_0_20": choice["gates"]["shots_required_rmse"],
        }
    params = contract["source_parameters"]
    regularization = contract["numerical_regularization"]
    mapping = contract["time_mapping"]
    cfg["effective_permeability_evolution"] = {
        "enabled": True,
        "model": "waszkiewiczSaturatedDissolutionIndexed",
        "source_reference_pressure_bar": choice["reference_pressure_bin_bar"],
        "source_parameters": {
            "pc_bar": params["pc_bar"],
            "qc_g_per_s": params["qc_g_per_s"],
            "k_solids_g": params["k_solids_g"],
            "l_solids_s": params["l_solids_s"],
            "m_solids_s": params["m_solids_s"],
            "dose_g": params["dose_g"],
        },
        "source_to_solver_offset_s": mapping["source_to_solver_offset_s"],
        "source_validity_start_s": mapping["source_validity_start_s"],
        "minimum_effective_multiplier": regularization["minimum_effective_multiplier"],
        "maximum_effective_multiplier": regularization["maximum_effective_multiplier"],
        "upper_roundoff_tolerance": regularization["upper_roundoff_tolerance"],
        "interface_mapping": contract["hydraulic_interface_mapping"]["id"],
        "fixed_8s_offset_used": False,
    }
    preview = analytical_preview(cfg)
    cfg["verification"]["analytical_first_drip_s"] = preview["first_drip_s"]
    cfg["execution_boundaries"] = {
        **cfg["execution_boundaries"],
        "scientific_result_status": "NOT_RUN",
        "openfoam_execution_count": 0,
        "puckworks_reference_execution_count": 0,
    }
    return cfg


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    mismatches = []
    for key, relative in OUTPUTS.items():
        expected = canonical(scenario(root, key))
        path = root / relative
        if args.check:
            if not path.is_file() or path.read_bytes() != expected:
                mismatches.append(relative.as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    report = {"status": "PASS" if not mismatches else "FAIL", "mismatches": mismatches}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
