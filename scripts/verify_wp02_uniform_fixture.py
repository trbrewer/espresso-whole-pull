#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

from waszkiewicz_effective_permeability import closure_state


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_error(observed: float, expected: float) -> float:
    return abs(observed - expected) / max(abs(expected), 1e-300)


def field_values(text: str) -> list[float]:
    match = re.search(r"internalField\s+uniform\s+([^;]+);", text)
    if match:
        return [float(match.group(1))]
    match = re.search(
        r"internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\((.*?)\)\s*;",
        text,
        re.S,
    )
    if not match:
        raise ValueError("unsupported internalField representation")
    values = [float(item) for item in match.group(2).split()]
    if len(values) != int(match.group(1)):
        raise ValueError("internalField count mismatch")
    return values


def control_output_settings(text: str) -> tuple[str, int, str]:
    def value(name: str) -> str:
        match = re.search(rf"^\s*{name}\s+([^;]+);", text, re.M)
        if not match:
            raise ValueError(f"missing {name}")
        return match.group(1).strip()

    return value("writeFormat"), int(value("writePrecision")), value(
        "writeCompression"
    )


def error_record(
    solver_time_s: float,
    source_time_s: float,
    source_state_time_s: float,
    expected: float,
    observed: float,
) -> dict:
    return {
        "solver_time_s": solver_time_s,
        "source_time_s": source_time_s,
        "source_state_time_s": source_state_time_s,
        "expected": expected,
        "observed": observed,
        "absolute_error": abs(observed - expected),
        "relative_error": relative_error(observed, expected),
    }


def update_maximum(maxima: dict, key: str, record: dict) -> None:
    if record["relative_error"] > maxima[key]["relative_error"]:
        maxima[key] = record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    case = args.case.resolve()
    contract = json.loads(
        (root / "validation/wp02/WP02_001_CLOSURE_CONTRACT.json").read_text()
    )
    config = json.loads(
        (root / "config/fixture_WP02_001_uniform_pressure.json").read_text()
    )
    acceptance = contract["uniform_pressure_fixture"]["acceptance"]
    closure = config["effective_permeability_evolution"]
    source = closure["source_parameters"]
    hydraulics = config["hydraulics"]
    trace = case / "postProcessing/wholePull/0/traces.csv"
    rows = list(csv.DictReader(trace.open()))
    expected_rows = round(
        (config["time"]["end_s"] - config["time"]["start_s"])
        / config["time"]["delta_t_s"]
    )
    failures: list[str] = []
    scalar_maxima = {
        "darcy_flow_relative": 0.0,
        "effective_permeability_relative": 0.0,
        "source_state_time_absolute_s": 0.0,
        "pressure_probe_absolute_Pa": 0.0,
        "multiplier_field_spatial_cv": 0.0,
        "analytical_flow_relative": 0.0,
    }
    empty = {
        "solver_time_s": None,
        "source_time_s": None,
        "source_state_time_s": None,
        "expected": None,
        "observed": None,
        "absolute_error": 0.0,
        "relative_error": 0.0,
    }
    multiplier_maxima = {
        "trace_multiplier_relative": dict(empty),
        "field_multiplier_relative": dict(empty),
        "field_to_trace_multiplier_relative": dict(empty),
    }
    states: dict[str, dict] = {}
    hold_rows = 0
    supported_rows = 0
    previous_multiplier = -1.0
    observed_multipliers: list[float] = []

    for row in rows:
        solver_time = float(row["time_s"])
        state = closure_state(
            solver_time,
            True,
            closure["source_reference_pressure_bar"],
            closure["source_to_solver_offset_s"],
            closure["source_validity_start_s"],
            closure["minimum_effective_multiplier"],
            hydraulics["saturated_permeability_m2"],
            pc_bar=source["pc_bar"],
            qc_g_s=source["qc_g_per_s"],
            k_g=source["k_solids_g"],
            l_s=source["l_solids_s"],
            m_s=source["m_solids_s"],
            dose_g=source["dose_g"],
        )
        states[row["time_s"]] = state
        trace_multiplier = float(row["effective_permeability_multiplier"])
        update_maximum(
            multiplier_maxima,
            "trace_multiplier_relative",
            error_record(
                solver_time,
                state["source_time_s"],
                state["source_state_time_s"],
                state["multiplier"],
                trace_multiplier,
            ),
        )
        scalar_maxima["source_state_time_absolute_s"] = max(
            scalar_maxima["source_state_time_absolute_s"],
            abs(float(row["source_state_time_s"]) - state["source_state_time_s"]),
        )
        scalar_maxima["effective_permeability_relative"] = max(
            scalar_maxima["effective_permeability_relative"],
            relative_error(
                float(row["effective_permeability_m2"]),
                state["effective_permeability_m2"],
            ),
        )
        expected_flow = (
            state["effective_permeability_m2"]
            * config["geometry"]["hydraulic_bed_area_m2"]
            * hydraulics["target_inlet_pressure_gauge_Pa"]
            / (
                config["liquid"]["dynamic_viscosity_Pa_s"]
                * config["coffee_bed"]["bed_depth_m"]
            )
        )
        scalar_maxima["darcy_flow_relative"] = max(
            scalar_maxima["darcy_flow_relative"],
            relative_error(float(row["outlet_flow_m3_s"]), expected_flow),
        )
        scalar_maxima["analytical_flow_relative"] = max(
            scalar_maxima["analytical_flow_relative"],
            relative_error(
                float(row["continuum_analytical_outlet_flow_m3_s"]),
                expected_flow,
            ),
        )
        for key, position in (
            ("pressure_probe_1_Pa", 0.0025),
            ("pressure_probe_2_Pa", 0.0075),
        ):
            expected_pressure = hydraulics["target_inlet_pressure_gauge_Pa"] * (
                1 - position / config["coffee_bed"]["bed_depth_m"]
            )
            scalar_maxima["pressure_probe_absolute_Pa"] = max(
                scalar_maxima["pressure_probe_absolute_Pa"],
                abs(float(row[key]) - expected_pressure),
            )
        if row["source_support_status"] != state["source_support_status"]:
            failures.append("source_support_status")
        hold_rows += (
            state["source_support_status"] == "PRE_SOURCE_SUPPORT_SATURATED_HOLD"
        )
        supported_rows += (
            state["source_support_status"] == "SOURCE_SUPPORTED_SATURATED_STAGE"
        )
        if supported_rows and state["multiplier"] + 1e-14 < previous_multiplier:
            failures.append("multiplier_monotonic")
        previous_multiplier = state["multiplier"]
        observed_multipliers.append(state["multiplier"])
        for key in ("liquid_balance_residual_kg", "solute_balance_residual_kg"):
            if abs(float(row[key])) > 1e-10:
                failures.append(key)
        if (
            float(row["min_saturation"]) < 1 - 1e-12
            or float(row["max_concentration_kg_m3"]) > 1e-12
        ):
            failures.append("bounded_state")

    for row in rows:
        field = case / row["time_s"] / "effectivePermeabilityMultiplier"
        if not field.exists():
            failures.append("missing_multiplier_field")
            continue
        try:
            values = field_values(field.read_text(errors="ignore"))
        except (ValueError, OverflowError):
            failures.append("invalid_multiplier_field")
            continue
        if not values or not all(math.isfinite(value) for value in values):
            failures.append("invalid_multiplier_field")
            continue
        mean = sum(values) / len(values)
        cv = (
            0.0
            if mean == 0 and all(value == 0 for value in values)
            else math.sqrt(
                sum((value - mean) ** 2 for value in values) / len(values)
            )
            / abs(mean)
        )
        scalar_maxima["multiplier_field_spatial_cv"] = max(
            scalar_maxima["multiplier_field_spatial_cv"], cv
        )
        state = states[row["time_s"]]
        solver_time = float(row["time_s"])
        trace_multiplier = float(row["effective_permeability_multiplier"])
        update_maximum(
            multiplier_maxima,
            "field_multiplier_relative",
            error_record(
                solver_time,
                state["source_time_s"],
                state["source_state_time_s"],
                state["multiplier"],
                mean,
            ),
        )
        update_maximum(
            multiplier_maxima,
            "field_to_trace_multiplier_relative",
            error_record(
                solver_time,
                state["source_time_s"],
                state["source_state_time_s"],
                trace_multiplier,
                mean,
            ),
        )

    try:
        write_format, write_precision, write_compression = control_output_settings(
            (case / "system/controlDict").read_text()
        )
    except (OSError, ValueError):
        write_format, write_precision, write_compression = "INVALID", -1, "INVALID"
        failures.append("control_dict_output_serialization")
    if (write_format, write_precision, write_compression) != ("ascii", 17, "off"):
        failures.append("control_dict_output_serialization")
    if len(rows) != expected_rows:
        failures.append("trace_row_count")
    if not rows or abs(float(rows[-1]["time_s"]) - config["time"]["end_s"]) > 1e-10:
        failures.append("endpoint")

    scalar_limits = {
        "darcy_flow_relative": "maximum_relative_darcy_flow_error",
        "effective_permeability_relative": "maximum_effective_permeability_relative_error",
        "source_state_time_absolute_s": "maximum_source_state_time_absolute_error_s",
        "pressure_probe_absolute_Pa": "maximum_pressure_probe_absolute_error_Pa",
        "multiplier_field_spatial_cv": "maximum_multiplier_field_spatial_cv",
    }
    for key, limit in scalar_limits.items():
        if scalar_maxima[key] > acceptance[limit]:
            failures.append(key)
    multiplier_limit = acceptance["maximum_multiplier_relative_error"]
    if (
        multiplier_maxima["trace_multiplier_relative"]["relative_error"]
        > multiplier_limit
    ):
        failures.append("trace_multiplier_relative")
    if (
        multiplier_maxima["field_multiplier_relative"]["relative_error"]
        > multiplier_limit
    ):
        failures.append("field_multiplier_relative")
    if (
        abs(observed_multipliers[-1] - 1)
        > acceptance["maximum_final_multiplier_distance_from_one"]
    ):
        failures.append("final_multiplier")

    combined = max(
        multiplier_maxima["trace_multiplier_relative"]["relative_error"],
        multiplier_maxima["field_multiplier_relative"]["relative_error"],
    )
    maximum_errors = {
        **scalar_maxima,
        **multiplier_maxima,
        "combined_multiplier_relative": combined,
        "multiplier_relative": combined,
    }
    manifest = case / "WP02_001_GENERATED_CASE_MANIFEST.json"
    implementation_commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    result = {
        "schema_version": "espresso.public.wp02_001_uniform_pressure_fixture.v1",
        "task": "WP02-001",
        "fixture_status": "FAIL" if failures else "PASS",
        "fixture_role": "DETERMINISTIC_CODE_VERIFICATION_NOT_PHYSICAL_VALIDATION",
        "execution": {
            "case_execution_count": 1,
            "mpi_ranks": 1,
            "executable_sha256": sha256(args.executable),
            "trace_sha256": sha256(trace),
            "trace_rows": len(rows),
            "endpoint_s": float(rows[-1]["time_s"]),
        },
        "identity": {
            "implementation_commit": implementation_commit,
            "solver_source_sha256": sha256(
                root / "solver/espressoWholePullFoam/espressoWholePullFoam.C"
            ),
            "closure_contract_sha256": sha256(
                root / "validation/wp02/WP02_001_CLOSURE_CONTRACT.json"
            ),
            "fixture_config_sha256": sha256(
                root / "config/fixture_WP02_001_uniform_pressure.json"
            ),
            "generated_case_manifest_sha256": sha256(manifest),
        },
        "output_serialization": {
            "write_format": write_format,
            "write_precision_digits": write_precision,
            "write_compression": write_compression,
        },
        "maximum_errors": maximum_errors,
        "temporal_behavior": {
            "hold_rows": hold_rows,
            "supported_rows": supported_rows,
            "supported_multiplier_monotonic": "multiplier_monotonic"
            not in failures,
            "minimum_multiplier": min(observed_multipliers),
            "maximum_multiplier": max(observed_multipliers),
            "final_multiplier": observed_multipliers[-1],
        },
        "conservation": {
            "liquid": "PASS"
            if "liquid_balance_residual_kg" not in failures
            else "FAIL",
            "solute": "PASS"
            if "solute_balance_residual_kg" not in failures
            else "FAIL",
        },
        "failures": sorted(set(failures)),
        "physical_validation": "NOT_APPLICABLE",
    }
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
