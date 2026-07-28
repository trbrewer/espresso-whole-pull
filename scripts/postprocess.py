#!/usr/bin/env python3
"""Post-process and numerically accept the v0.1.4 reference whole-pull run."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from espresso_reference_math import analytical_preview, b0_reduced_simulation  # noqa: E402

PACKAGE_VERSION = "0.1.4"
CASE_DEFAULT = Path("cases/reference_R0_20g_58mm_9bar")
CONFIG_DEFAULT = Path("config/reference_R0.json")
STEM = "ESPRESSO_WHOLE_PULL_REFERENCE"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def gate(status: bool, metric: object, limit: str, details: str = "") -> Dict[str, object]:
    return {
        "status": "PASS" if status else "FAIL",
        "metric": metric,
        "limit": limit,
        "details": details,
    }


def resolve(root: Path, value: Optional[Path], default: Path) -> Path:
    chosen = value if value is not None else default
    return chosen.resolve() if chosen.is_absolute() else (root / chosen).resolve()


def relative_error(actual: float, expected: float) -> float:
    scale = max(abs(expected), 1.0e-30)
    return abs(actual - expected) / scale


def monotonic_metric(
    rows: List[Dict[str, float]], key: str, tolerance: float
) -> Dict[str, object]:
    increments = [rows[index][key] - rows[index - 1][key] for index in range(1, len(rows))]
    violations = [
        {
            "row_index": index,
            "time_s": rows[index]["time_s"],
            "previous": rows[index - 1][key],
            "current": rows[index][key],
            "increment": increments[index - 1],
        }
        for index in range(1, len(rows))
        if increments[index - 1] < -tolerance
    ]
    return {
        "status": "PASS" if not violations else "FAIL",
        "minimum_increment": min(increments) if increments else 0.0,
        "tolerance": tolerance,
        "violation_count": len(violations),
        "first_violations": violations[:10],
    }


def read_rows(path: Path) -> List[Dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows: List[Dict[str, float]] = []
        for row in reader:
            converted: Dict[str, float] = {}
            for key, value in row.items():
                if key is None or value is None:
                    continue
                converted[key] = float(value)
            rows.append(converted)
    if not rows:
        raise SystemExit(f"Trace contains no data rows: {path}")
    return rows


def numeric_time_directories(case: Path) -> List[Tuple[float, Path]]:
    result: List[Tuple[float, Path]] = []
    for directory in case.iterdir():
        if not directory.is_dir():
            continue
        try:
            result.append((float(directory.name), directory))
        except ValueError:
            continue
    return sorted(result, key=lambda item: item[0])


def locate_field(directory: Optional[Path], field_name: str) -> Optional[Path]:
    if directory is None:
        return None
    for candidate in (directory / field_name, directory / (field_name + ".gz")):
        if candidate.is_file():
            return candidate
    return None


def comparison_gate(
    actual: float,
    expected: float,
    tolerance: float,
    tolerance_kind: str,
    details: str = "",
) -> Dict[str, object]:
    if tolerance_kind == "absolute":
        metric = abs(actual - expected)
        limit = f"absolute error <= {tolerance}"
    elif tolerance_kind == "relative":
        metric = relative_error(actual, expected)
        limit = f"relative error <= {tolerance}"
    else:
        raise ValueError(tolerance_kind)
    return gate(
        metric <= tolerance,
        {"actual": actual, "expected": expected, "error": metric},
        limit,
        details,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--case-dir", type=Path)
    parser.add_argument("--require-fields", choices=("yes", "no"), default="yes")
    args = parser.parse_args()

    root = args.root.resolve()
    case = resolve(root, args.case_dir, CASE_DEFAULT)
    config_path = resolve(root, args.config, CONFIG_DEFAULT)
    scenario = json.loads(config_path.read_text(encoding="utf-8"))
    source_trace = case / "postProcessing/wholePull/0/traces.csv"
    if not source_trace.is_file():
        raise SystemExit(f"Missing solver trace: {source_trace}")

    output_trace = case / f"{STEM}_TRACES_V0_1_4.csv"
    shutil.copyfile(source_trace, output_trace)
    rows = read_rows(source_trace)
    final = rows[-1]
    end_s = float(scenario["time"]["end_s"])
    dt = float(scenario["time"]["delta_t_s"])
    verification = scenario.get("verification", {})

    expected_final_fields = [
        "p",
        "U",
        "saturation",
        "wetMask",
        "porosity",
        "permeability",
        "hydraulicMobility",
        "dissolvedConcentration",
        "remainingExtractable",
        "localExtractionRate",
        "darcyFlux",
    ]
    time_dirs = numeric_time_directories(case)
    final_time_dir: Optional[Path] = None
    if time_dirs:
        candidate_time, candidate_dir = min(time_dirs, key=lambda item: abs(item[0] - end_s))
        if abs(candidate_time - end_s) <= 1.01 * dt:
            final_time_dir = candidate_dir

    final_field_paths = {
        name: locate_field(final_time_dir, name) for name in expected_final_fields
    }
    missing_final_fields = [
        name for name, path in final_field_paths.items() if path is None
    ]
    indexed_fields: List[Dict[str, object]] = []
    for time_value, directory in time_dirs:
        for name in expected_final_fields:
            path = locate_field(directory, name)
            if path is not None:
                indexed_fields.append(
                    {
                        "time_s": time_value,
                        "field": name,
                        "path": str(path.relative_to(case)),
                        "bytes": path.stat().st_size,
                        "sha256": sha256(path),
                    }
                )

    field_index_path = case / f"{STEM}_FIELD_INDEX_V0_1_4.json"
    field_index = {
        "schema_version": "espresso.whole_pull.field_index.v0.1.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_final_fields": expected_final_fields,
        "final_time_directory": final_time_dir.name if final_time_dir else None,
        "missing_final_fields": missing_final_fields,
        "indexed_file_count": len(indexed_fields),
        "files": indexed_fields,
    }
    field_index_path.write_text(json.dumps(field_index, indent=2) + "\n", encoding="utf-8")

    finite = all(math.isfinite(value) for row in rows for value in row.values())
    min_saturation = min(row["min_saturation"] for row in rows)
    max_saturation = max(row["max_saturation"] for row in rows)
    min_concentration = min(row["min_concentration_kg_m3"] for row in rows)
    max_concentration = max(row["max_concentration_kg_m3"] for row in rows)
    min_remaining_extractable = min(row["remaining_extractable_mass_kg"] for row in rows)
    max_remaining_extractable = max(row["remaining_extractable_mass_kg"] for row in rows)
    min_retained_water = min(row["stored_water_mass_kg"] for row in rows)
    max_retained_water = max(row["stored_water_mass_kg"] for row in rows)
    max_liquid_residual = max(abs(row["liquid_balance_residual_kg"]) for row in rows)
    max_solute_residual = max(abs(row["solute_balance_residual_kg"]) for row in rows)
    initial_extractable = (
        float(scenario["coffee_bed"]["dry_dose_kg"])
        * float(scenario["coffee_bed"]["initial_extractable_fraction_dry_basis"])
    )
    cumulative_inlet = max(final["cumulative_inlet_water_mass_kg"], 1.0e-30)
    saturated_rows = [
        row
        for row in rows
        if row["first_drip_s"] >= 0.0
        and row["time_s"] > row["first_drip_s"] + 0.5 * dt
    ]
    if not saturated_rows:
        saturated_rows = [final]

    max_pressure_final_residual = max(
        abs(row["pressure_final_residual"]) for row in saturated_rows
    )
    max_concentration_final_residual = max(
        abs(row["concentration_final_residual"]) for row in saturated_rows
    )
    max_pressure_iterations = max(row["pressure_iterations"] for row in saturated_rows)
    max_concentration_iterations = max(
        row["concentration_iterations"] for row in saturated_rows
    )
    axial_dx = (
        float(scenario["coffee_bed"]["bed_depth_m"])
        / int(scenario["geometry"]["axial_cells"])
    )
    porosity = float(scenario["coffee_bed"]["initial_porosity"])
    max_pore_courant = max(
        row["max_velocity_m_s"] * dt / (porosity * axial_dx)
        for row in saturated_rows
    )

    analytical = analytical_preview(scenario)
    b0_path = case / "preflight/B0_REDUCED_TWIN_V0_1_4.json"
    b0 = None
    if b0_path.is_file():
        candidate = json.loads(b0_path.read_text(encoding="utf-8"))
        if (
            candidate.get("scenario_id") == scenario.get("scenario_id")
            and int(candidate.get("axial_cells", -1))
            == int(scenario["geometry"]["axial_cells"])
            and abs(float(candidate.get("delta_t_s", -1.0)) - dt) <= 1.0e-15
        ):
            b0 = candidate
    if b0 is None:
        b0 = b0_reduced_simulation(scenario)
    b0_outputs = b0["primary_outputs"]
    first_drip_tolerance = float(
        verification.get("analytical_first_drip_absolute_tolerance_s", 1.0e-8)
    )
    flow_tolerance = float(
        verification.get("analytical_flow_relative_tolerance", 1.0e-8)
    )
    wedge_tolerance = float(
        verification.get("wedge_volume_relative_tolerance", 1.0e-8)
    )
    retained_tolerance = float(
        verification.get("retained_water_relative_tolerance", 1.0e-8)
    )
    bounded_cfg = verification.get("bounded_state", {})
    concentration_cap = float(scenario["extraction"]["saturation_concentration_kg_m3"])
    concentration_cap_tolerance = float(
        bounded_cfg.get("concentration_cap_absolute_tolerance_kg_m3", 1.0e-8)
    )
    inventory_tolerance = float(
        bounded_cfg.get("inventory_absolute_tolerance_kg", 1.0e-12)
    )
    retained_water_absolute_tolerance = float(
        bounded_cfg.get("retained_water_absolute_tolerance_kg", 1.0e-12)
    )
    monotonic_tolerance = float(
        bounded_cfg.get("monotonic_mass_absolute_tolerance_kg", 1.0e-12)
    )
    saturated_pore_water = float(analytical["saturated_pore_water_mass_kg"])
    monotonic_inlet = monotonic_metric(rows, "cumulative_inlet_water_mass_kg", monotonic_tolerance)
    monotonic_cup_water = monotonic_metric(rows, "cup_water_mass_kg", monotonic_tolerance)
    monotonic_cup_solute = monotonic_metric(rows, "cup_solute_mass_kg", monotonic_tolerance)

    numerical_gates: Dict[str, Dict[str, object]] = {
        "simulation_reached_end_time": gate(
            abs(final["time_s"] - end_s) <= 1.01 * dt,
            final["time_s"],
            f"|time - {end_s}| <= {1.01 * dt}",
        ),
        "final_paraview_field_set_present": gate(
            args.require_fields == "no" or not missing_final_fields,
            {
                "required": args.require_fields == "yes",
                "final_time_directory": final_time_dir.name if final_time_dir else None,
                "missing_fields": missing_final_fields,
            },
            "all required fields present at reconstructed final time",
        ),
        "all_trace_values_finite": gate(finite, finite, "true"),
        "saturation_bounded": gate(
            min_saturation >= -1.0e-10 and max_saturation <= 1.0 + 1.0e-10,
            {"min": min_saturation, "max": max_saturation},
            "0 <= saturation <= 1 (1e-10 tolerance)",
        ),
        "concentration_nonnegative": gate(
            min_concentration >= -1.0e-10,
            min_concentration,
            ">= -1e-10 kg/m3",
        ),
        "concentration_below_declared_capacity": gate(
            max_concentration <= concentration_cap + concentration_cap_tolerance,
            {
                "maximum_kg_m3": max_concentration,
                "declared_capacity_kg_m3": concentration_cap,
                "absolute_tolerance_kg_m3": concentration_cap_tolerance,
            },
            "maximum concentration <= declared saturation concentration + tolerance",
        ),
        "remaining_extractable_inventory_bounded": gate(
            min_remaining_extractable >= -inventory_tolerance
            and max_remaining_extractable <= initial_extractable + inventory_tolerance,
            {
                "minimum_kg": min_remaining_extractable,
                "maximum_kg": max_remaining_extractable,
                "initial_inventory_kg": initial_extractable,
                "absolute_tolerance_kg": inventory_tolerance,
            },
            "0 <= remaining extractable <= initial extractable inventory (+/- tolerance)",
        ),
        "retained_water_bounded_by_pore_capacity": gate(
            min_retained_water >= -retained_water_absolute_tolerance
            and max_retained_water <= saturated_pore_water + retained_water_absolute_tolerance,
            {
                "minimum_kg": min_retained_water,
                "maximum_kg": max_retained_water,
                "saturated_pore_capacity_kg": saturated_pore_water,
                "absolute_tolerance_kg": retained_water_absolute_tolerance,
            },
            "0 <= retained water <= saturated pore-water capacity (+/- tolerance)",
        ),
        "cumulative_inlet_water_monotonic": gate(
            monotonic_inlet["status"] == "PASS",
            monotonic_inlet,
            "nondecreasing within configured absolute tolerance",
        ),
        "cumulative_cup_water_monotonic": gate(
            monotonic_cup_water["status"] == "PASS",
            monotonic_cup_water,
            "nondecreasing within configured absolute tolerance",
        ),
        "cumulative_cup_solute_monotonic": gate(
            monotonic_cup_solute["status"] == "PASS",
            monotonic_cup_solute,
            "nondecreasing within configured absolute tolerance",
        ),
        "liquid_conservation": gate(
            max_liquid_residual <= max(1.0e-9, 1.0e-8 * cumulative_inlet),
            max_liquid_residual,
            "max absolute residual <= max(1e-9 kg, 1e-8 cumulative inlet water)",
        ),
        "solute_inventory_conservation": gate(
            max_solute_residual <= max(1.0e-10, 1.0e-8 * max(initial_extractable, 1.0e-30)),
            max_solute_residual,
            "max absolute residual <= max(1e-10 kg, 1e-8 initial extractable mass)",
        ),
        "pressure_linear_solver_residual": gate(
            max_pressure_final_residual <= 1.0e-8,
            max_pressure_final_residual,
            "maximum saturated-stage final residual <= 1e-8",
        ),
        "concentration_linear_solver_residual": gate(
            max_concentration_final_residual <= 1.0e-7,
            max_concentration_final_residual,
            "maximum saturated-stage final residual <= 1e-7",
        ),
        "pressure_iteration_limit": gate(
            max_pressure_iterations < 1000,
            max_pressure_iterations,
            "< configured maxIter 1000",
        ),
        "concentration_iteration_limit": gate(
            max_concentration_iterations < 2000,
            max_concentration_iterations,
            "< configured maxIter 2000",
        ),
        "estimated_saturated_pore_courant": gate(
            max_pore_courant <= 1.2,
            max_pore_courant,
            "<= 1.2 using maximum superficial velocity, porosity, and axial spacing",
            "Implicit upwind transport remains stable above this; this is a resolution gate.",
        ),
        "straight_sided_wedge_volume_equivalence": gate(
            abs(final["mesh_volume_relative_error"]) <= wedge_tolerance,
            {
                "relative_error": final["mesh_volume_relative_error"],
                "scale": final["straight_sided_wedge_scale"],
                "raw_wedge_volume_m3": final["raw_wedge_mesh_volume_m3"],
                "scaled_volume_m3": final["scaled_mesh_volume_m3"],
                "nominal_cylinder_volume_m3": final["nominal_cylinder_volume_m3"],
            },
            f"relative volume error <= {wedge_tolerance}",
        ),
        "exact_sharp_front_first_drip": comparison_gate(
            final["first_drip_s"],
            float(analytical["first_drip_s"]),
            first_drip_tolerance,
            "absolute",
            "The pressure ramp is integrated exactly within every time step.",
        ),
        "analytical_uniform_darcy_flow": comparison_gate(
            final["outlet_flow_m3_s"],
            float(analytical["steady_outlet_volume_flow_m3_s"]),
            flow_tolerance,
            "relative",
            "Uniform permeability, cylindrical area, and declared pressure nodes.",
        ),
        "retained_water_cylindrical_volume": comparison_gate(
            final["stored_water_mass_kg"],
            float(analytical["saturated_pore_water_mass_kg"]),
            retained_tolerance,
            "relative",
        ),
    }

    b0_cfg = verification.get("b0_parity", {})
    b0_event_tol = float(b0_cfg.get("event_absolute_tolerance_s", 1.0e-8))
    b0_hydraulic_tol = float(b0_cfg.get("hydraulic_relative_tolerance", 1.0e-8))
    b0_inventory_tol = float(b0_cfg.get("inventory_relative_tolerance", 0.005))
    b0_gates: Dict[str, Dict[str, object]] = {
        "first_drip": comparison_gate(
            final["first_drip_s"],
            float(b0_outputs["first_drip_s"]),
            b0_event_tol,
            "absolute",
        ),
        "final_outlet_flow": comparison_gate(
            final["outlet_flow_m3_s"],
            float(b0_outputs["outlet_flow_final_m3_s"]),
            b0_hydraulic_tol,
            "relative",
        ),
    }
    b0_pairs = {
        "cup_water_mass": ("cup_water_mass_kg", "cup_water_mass_at_end_kg"),
        "cup_solute_mass": ("cup_solute_mass_kg", "cup_solute_mass_at_end_kg"),
        "cup_beverage_mass": ("cup_beverage_mass_kg", "cup_beverage_mass_at_end_kg"),
        "cumulative_tds": ("cumulative_tds_mass_fraction", "cumulative_tds_mass_fraction"),
        "extraction_yield": ("extraction_yield_mass_fraction", "extraction_yield_mass_fraction"),
        "retained_dissolved_solute": ("dissolved_in_puck_mass_kg", "retained_dissolved_solute_mass_kg"),
        "remaining_extractable": ("remaining_extractable_mass_kg", "remaining_extractable_mass_kg"),
    }
    for name, (trace_key, b0_key) in b0_pairs.items():
        b0_gates[name] = comparison_gate(
            final[trace_key],
            float(b0_outputs[b0_key]),
            b0_inventory_tol,
            "relative",
        )
    if b0_outputs.get("time_to_target_mass_s") is not None:
        b0_gates["time_to_target_mass"] = comparison_gate(
            final["time_to_40g_s"],
            float(b0_outputs["time_to_target_mass_s"]),
            max(b0_inventory_tol, 1.0e-4),
            "relative",
        )

    physical_observations = {
        "first_drip_detected": gate(
            0.0 < final["first_drip_s"] < end_s,
            final["first_drip_s"],
            f"0 < first drip < {end_s} s",
        ),
        "cup_mass_broad_plausibility": gate(
            0.015 <= final["cup_beverage_mass_kg"] <= 0.080,
            final["cup_beverage_mass_kg"],
            "15 to 80 g; plausibility only",
        ),
        "tds_broad_plausibility": gate(
            0.0 <= final["cumulative_tds_mass_fraction"] <= 0.20,
            final["cumulative_tds_mass_fraction"],
            "0 to 20% mass fraction; plausibility only",
        ),
        "extraction_yield_broad_plausibility": gate(
            0.0 <= final["extraction_yield_mass_fraction"] <= 0.35,
            final["extraction_yield_mass_fraction"],
            "0 to 35% dry-dose mass fraction; plausibility only",
        ),
    }

    all_numerical = all(item["status"] == "PASS" for item in numerical_gates.values())
    all_b0 = all(item["status"] == "PASS" for item in b0_gates.values())
    bounded_gate_names = (
        "concentration_below_declared_capacity",
        "remaining_extractable_inventory_bounded",
        "retained_water_bounded_by_pore_capacity",
    )
    monotonicity_gate_names = (
        "cumulative_inlet_water_monotonic",
        "cumulative_cup_water_monotonic",
        "cumulative_cup_solute_monotonic",
    )
    all_bounded = all(
        numerical_gates[name]["status"] == "PASS" for name in bounded_gate_names
    )
    all_monotonic = all(
        numerical_gates[name]["status"] == "PASS" for name in monotonicity_gate_names
    )

    primary_outputs = {
        "first_drip_s": final["first_drip_s"],
        "outlet_flow_final_m3_s": final["outlet_flow_m3_s"],
        "cup_water_mass_at_end_kg": final["cup_water_mass_kg"],
        "cup_solute_mass_at_end_kg": final["cup_solute_mass_kg"],
        "cup_beverage_mass_at_end_kg": final["cup_beverage_mass_kg"],
        "time_to_40g_s": final["time_to_40g_s"],
        "cumulative_tds_mass_fraction": final["cumulative_tds_mass_fraction"],
        "extraction_yield_mass_fraction": final["extraction_yield_mass_fraction"],
        "retained_water_mass_kg": final["stored_water_mass_kg"],
        "retained_dissolved_solute_mass_kg": final["dissolved_in_puck_mass_kg"],
        "remaining_extractable_mass_kg": final["remaining_extractable_mass_kg"],
        "max_liquid_balance_residual_kg": max_liquid_residual,
        "max_solute_balance_residual_kg": max_solute_residual,
        "max_pressure_final_residual": max_pressure_final_residual,
        "max_concentration_final_residual": max_concentration_final_residual,
        "max_pressure_iterations": max_pressure_iterations,
        "max_concentration_iterations": max_concentration_iterations,
        "max_estimated_saturated_pore_courant": max_pore_courant,
        "maximum_concentration_kg_m3": max_concentration,
        "minimum_remaining_extractable_mass_kg": min_remaining_extractable,
        "maximum_remaining_extractable_mass_kg": max_remaining_extractable,
        "minimum_retained_water_mass_kg": min_retained_water,
        "maximum_retained_water_mass_kg": max_retained_water,
        "straight_sided_wedge_scale": final["straight_sided_wedge_scale"],
        "scaled_mesh_volume_m3": final["scaled_mesh_volume_m3"],
        "mesh_volume_relative_error": final["mesh_volume_relative_error"],
    }

    acceptance_path = case / f"{STEM}_ACCEPTANCE_V0_1_4.json"
    outputs_finalized_at = datetime.now(timezone.utc).isoformat()
    report = {
        "schema_version": "espresso.whole_pull.reference_acceptance.v0.1.4",
        "generated_at_utc": outputs_finalized_at,
        "outputs_finalized_at_utc": outputs_finalized_at,
        "qualification_finalized_at_utc": None,
        "package_version": PACKAGE_VERSION,
        "scenario_id": scenario["scenario_id"],
        "status": "PASS" if all_numerical and all_b0 else "FAIL",
        "execution_status": "COMPLETED",
        "all_required_numerical_gates_pass": all_numerical,
        "all_required_b0_parity_gates_pass": all_b0,
        "all_required_bounded_state_gates_pass": all_bounded,
        "all_required_monotonicity_gates_pass": all_monotonic,
        "all_required_reference_gates_pass": (
            all_numerical and all_b0 and all_bounded and all_monotonic
        ),
        "reference_qualification_status": "PENDING_STANDARD_ALLVERIFY",
        "release_provenance_status": "PENDING_TERMINAL_FREEZE_MANIFEST",
        "reference_freeze_status": "NOT_FROZEN",
        "numerical_acceptance_gates": numerical_gates,
        "openfoam_b0_parity_gates": b0_gates,
        "physical_plausibility_observations": physical_observations,
        "primary_outputs": primary_outputs,
        "analytical_reference": analytical,
        "b0_reduced_twin": b0,
        "calibration_and_validation": {
            "mode": scenario["mode"],
            "calibration": scenario.get("calibration"),
            "physical_validation_status": "NOT_ESTABLISHED",
            "claim_ceiling": scenario["claim_ceiling"],
        },
        "qualification_report": None,
        "freeze_finalization_prerequisites": None,
        "artifacts": {},
    }
    acceptance_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    foam_path = case / "reference_R0.foam"
    foam_path.touch()
    manifest_path = case / f"{STEM}_CASE_MANIFEST_V0_1_4.json"
    if not manifest_path.is_file():
        raise SystemExit(f"Scientific-input case manifest missing: {manifest_path}")

    immutable_artifacts = [output_trace, field_index_path, foam_path, manifest_path]
    report["artifacts"] = {
        str(path.relative_to(case)): {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "role": (
                "scientific_input_manifest"
                if path == manifest_path
                else "reference_output"
            ),
        }
        for path in immutable_artifacts
    }
    acceptance_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": report["status"],
                "first_drip_s": primary_outputs["first_drip_s"],
                "cup_mass_g": 1000.0 * primary_outputs["cup_beverage_mass_at_end_kg"],
                "time_to_40g_s": primary_outputs["time_to_40g_s"],
                "TDS_percent": 100.0 * primary_outputs["cumulative_tds_mass_fraction"],
                "EY_percent": 100.0 * primary_outputs["extraction_yield_mass_fraction"],
                "reference_qualification_status": report["reference_qualification_status"],
                "reference_freeze_status": report["reference_freeze_status"],
                "acceptance_report": str(acceptance_path),
            },
            indent=2,
        )
    )
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
