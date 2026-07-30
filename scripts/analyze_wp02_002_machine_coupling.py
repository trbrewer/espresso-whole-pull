#!/usr/bin/env python3
"""Reduce and adjudicate WP02-002 executions without protected-source access."""
import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
from pathlib import Path

R0_EXPECTED = {
    "first_drip_s": 4.711696185231869,
    "final_cup_mass_kg": 0.040957867483,
    "final_tds_fraction": 0.11689306389,
    "final_extraction_yield_fraction": 0.23938453103,
}
WP02_LATE_MEAN_G_S = 1.8821949576808104


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(a, b, floor=1e-30):
    return abs(a - b) / max(abs(b), floor)


def timing(path):
    data = {}
    for line in path.read_text().splitlines():
        text = line.strip()
        if text.startswith("Elapsed (wall clock) time"):
            data["wall_clock"] = text.rsplit(": ", 1)[-1]
        elif text.startswith("Maximum resident set size"):
            data["peak_resident_kb"] = int(text.rsplit(": ", 1)[-1])
    return data


def quantile_time(rows, key, fraction, eligible=None):
    selected = [row for row in rows if eligible is None or eligible(row)]
    peak = max(float(row[key]) for row in selected)
    for row in selected:
        if float(row[key]) >= fraction * peak:
            return float(row["time_s"])
    return None


def case_summary(cid, trace, cfg, time_file, ranks):
    rows = list(csv.DictReader(trace.open()))
    if not rows:
        raise ValueError("empty trace " + cid)
    numeric_fields = [
        key for key in rows[0]
        if key not in {"pressureBoundaryModel", "source_support_status"}
    ]
    finite = all(
        math.isfinite(float(row[key]))
        for row in rows for key in numeric_fields if row[key] != ""
    )
    machine = cfg.get("pressureBoundaryModel") == "lumpedMachineCompliance"
    transition = [row for row in rows if int(row["saturationTransitionStep"])]
    post = []
    transition_time = float(transition[0]["time_s"]) if transition else None
    if transition_time is not None:
        post = [row for row in rows if float(row["time_s"]) > transition_time]
    physical_rows = [
        row for row in rows if not int(row["saturationTransitionStep"])
    ]
    final = rows[-1]
    first_drip = float(final["first_drip_s"])
    first = min(rows, key=lambda row: abs(float(row["time_s"]) - first_drip))
    residuals = [abs(float(row["machineWaterBalanceResidualM3"])) for row in rows]
    coupling = [abs(float(row["couplingResidualM3s"])) for row in rows]
    iterations = [int(row["couplingIterations"]) for row in rows]
    failed = sum(int(row["couplingConverged"]) != 1 for row in rows) if machine else 0
    bracket_failures = sum(int(row["couplingBracketed"]) != 1 for row in rows) if machine else 0
    fallbacks = sum(int(row["couplingFallbackUsed"]) != 0 for row in rows)
    outlet = float(cfg["hydraulics"]["outlet_pressure_gauge_Pa"])
    shutoff = float(cfg.get("machineBoundary", {}).get(
        "shutoffPressure", cfg["hydraulics"]["target_inlet_pressure_gauge_Pa"]
    ))
    bounded = all(
        outlet - 1e-8 <= float(row["basketPressurePa"])
        <= float(row["upstreamPressurePa"]) + 1e-8
        <= shutoff + 1e-6
        and float(row["supplyFlowM3s"]) >= -1e-18
        and float(row["puckFlowM3s"]) >= -1e-18
        for row in rows
    )
    gates = {
        "case_completed": abs(float(final["time_s"]) - float(cfg["time"]["end_s"])) <= 1e-9,
        "finite_state": finite,
        "bounded_state": bounded,
        "coupling_converged": failed == 0,
        "bracketed": bracket_failures == 0,
        "no_fallback": fallbacks == 0,
        "machine_water_balance": max(residuals) <= 1e-12,
        "existing_liquid_conservation":
            max(abs(float(row["liquid_balance_residual_kg"])) for row in rows) <= 1e-10,
        "existing_solute_conservation":
            max(abs(float(row["solute_balance_residual_kg"])) for row in rows) <= 1e-10,
    }
    pdrop = [
        float(row["upstreamPressurePa"]) - float(row["basketPressurePa"])
        for row in rows
    ]
    return {
        "status": "PASS" if all(gates.values()) else "FAIL",
        "gates": {key: "PASS" if value else "FAIL" for key, value in gates.items()},
        "configuration_sha256": sha(cfg["_path"]),
        "trace_sha256": sha(trace),
        "trace_rows": len(rows),
        "time_step_s": float(cfg["time"]["delta_t_s"]),
        "mesh_cells": int(cfg["geometry"]["axial_cells"]) * int(cfg["geometry"]["radial_cells"]),
        "mpi_ranks": ranks,
        "transition_step_count": len(transition),
        "transition_step_time_s": transition_time,
        "transition_treatment": "FLAGGED_EXCLUDED_FROM_PHYSICAL_PEAK_NO_INTERNAL_SPLIT",
        "peak_upstream_pressure_Pa": max(float(row["upstreamPressurePa"]) for row in rows),
        "peak_basket_pressure_Pa_excluding_transition":
            max(float(row["basketPressurePa"]) for row in physical_rows),
        "maximum_sustained_post_saturation_basket_pressure_Pa":
            max(float(row["basketPressurePa"]) for row in post) if post else None,
        "pressure_t50_s": quantile_time(physical_rows, "basketPressurePa", .5),
        "pressure_t90_s": quantile_time(physical_rows, "basketPressurePa", .9),
        "pressure_t99_s": quantile_time(physical_rows, "basketPressurePa", .99),
        "maximum_upstream_basket_drop_Pa": max(pdrop),
        "first_drip_s": first_drip,
        "pressure_at_first_drip_Pa": float(first["basketPressurePa"]),
        "supply_at_first_drip_m3": float(first["cumulativeSupplyM3"]),
        "storage_at_first_drip_m3": float(first["compliantStorageM3"]),
        "final_cup_mass_kg": float(final["cup_beverage_mass_kg"]),
        "final_tds_fraction": float(final["cumulative_tds_mass_fraction"]),
        "final_extraction_yield_fraction": float(final["extraction_yield_mass_fraction"]),
        "cumulative_supply_m3": float(final["cumulativeSupplyM3"]),
        "cumulative_puck_intake_m3": float(final["cumulativePuckIntakeM3"]),
        "cumulative_puck_outlet_m3": float(final["cumulativePuckOutletM3"]),
        "final_compliant_storage_m3": float(final["compliantStorageM3"]),
        "peak_supply_flow_m3_s": max(float(row["supplyFlowM3s"]) for row in rows),
        "mean_supply_flow_m3_s": statistics.mean(float(row["supplyFlowM3s"]) for row in rows),
        "peak_puck_flow_m3_s": max(float(row["puckFlowM3s"]) for row in rows),
        "mean_puck_flow_m3_s": statistics.mean(float(row["puckFlowM3s"]) for row in rows),
        "compliance_m3_Pa": cfg.get("machineBoundary", {}).get("upstreamCompliance", 0.0),
        "upstream_resistance_Pa_s_m3": cfg.get("machineBoundary", {}).get("upstreamResistance", 0.0),
        "maximum_machine_water_balance_residual_m3": max(residuals),
        "maximum_coupling_residual_m3_s": max(coupling),
        "maximum_coupling_iterations": max(iterations),
        "mean_coupling_iterations": statistics.mean(iterations),
        "failed_steps": failed,
        "bracket_failures": bracket_failures,
        "fallback_count": fallbacks,
        "maximum_liquid_balance_residual_kg":
            max(abs(float(row["liquid_balance_residual_kg"])) for row in rows),
        "maximum_solute_balance_residual_kg":
            max(abs(float(row["solute_balance_residual_kg"])) for row in rows),
        "runtime": timing(time_file) if time_file.is_file() else {},
    }


def adjudicate(result):
    analytical = result["analytical_linear_load"]
    analytical["backward_euler_gate"] = (
        "PASS" if analytical["maximum_discrete_relative_error"] <= 1e-10 else "FAIL"
    )
    analytical["temporal_refinement_gate"] = (
        "PASS" if min(analytical["observed_orders"]) >= .8
        and max(analytical["observed_orders"]) <= 1.2 else "FAIL"
    )
    analytical["equilibrium_gate"] = (
        "PASS" if max(analytical["equilibrium"].values()) <= 1e-8 else "FAIL"
    )
    sequence = result["prescribed_pressure_limit"]["sequence"]
    result["prescribed_pressure_limit"]["systematic_approach_gate"] = (
        "PASS" if all(
            sequence[i]["relative_error_to_prescribed_step"]
            > sequence[i + 1]["relative_error_to_prescribed_step"]
            for i in range(len(sequence) - 1)
        ) else "FAIL"
    )
    result["two_layer_fixture"]["status"] = (
        "PASS" if result["two_layer_fixture"]["maximum_discrete_relative_error"]
        <= 1e-10 else "FAIL"
    )
    r0 = result["regressions"]["prescribed_pressure_R0"]
    r0["status"] = "PASS" if (
        r0["errors"]["first_drip_s"] <= 1e-8
        and max(value for key, value in r0["errors"].items()
                if key != "first_drip_s") <= .005
    ) else "FAIL"
    wp02 = result["regressions"]["WP02_coupling_disabled"]
    wp02["status"] = "PASS" if wp02["relative_error"] <= 1e-8 else "FAIL"
    full = result["full_shot_time_refinement"]
    full["status"] = "PASS" if (
        full["maximum_fine_pair_relative_change"]
        <= full["relative_output_acceptance"]
        and full["maximum_absolute_machine_water_balance_residual_m3"]
        <= full["machine_water_balance_acceptance_m3"]
        and all(case["status"] == "PASS" for case in full["cases"])
    ) else "FAIL"
    for case in result["cases"].values():
        numerical_values = (
            case["peak_upstream_pressure_Pa"],
            case["peak_basket_pressure_Pa_excluding_transition"],
            case["maximum_machine_water_balance_residual_m3"],
            case["maximum_coupling_residual_m3_s"],
        )
        case["status"] = "PASS" if (
            all(math.isfinite(value) for value in numerical_values)
            and case["failed_steps"] == 0
            and case["bracket_failures"] == 0
            and case["fallback_count"] == 0
            and case["maximum_machine_water_balance_residual_m3"] <= 1e-12
            and all(value == "PASS" for value in case["gates"].values())
        ) else "FAIL"
    required = []
    required.extend(
        result["analytical_linear_load"][key] == "PASS"
        for key in ("backward_euler_gate", "temporal_refinement_gate", "equilibrium_gate")
    )
    required.append(result["prescribed_pressure_limit"]["systematic_approach_gate"] == "PASS")
    required.append(result["two_layer_fixture"]["status"] == "PASS")
    required.extend(value["status"] == "PASS" for value in result["regressions"].values()
                    if isinstance(value, dict) and "status" in value)
    required.append(result["full_shot_time_refinement"]["status"] == "PASS")
    required.extend(case["status"] == "PASS" for case in result["cases"].values())
    result["all_gates_pass"] = all(required)
    result["disposition"] = (
        "NUMERICALLY_VERIFIED_SYNTHETIC_MACHINE_PUCK_COUPLING_DEMONSTRATION"
        if result["all_gates_pass"] else "NUMERICAL_FAILURE"
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trace-output", type=Path)
    args = parser.parse_args()
    from machine_coupling_reference import backward_euler, continuous
    from analyze_wp02 import load_prediction

    configs = {}
    cases = {}
    for cid in ("MC-0", "MC-1", "MC-2", "MC-3", "MC-4", "MC-5"):
        path = args.run_root / "configs" / (cid + ".json")
        cfg = json.loads(path.read_text()); cfg["_path"] = path
        configs[cid] = cfg
        cases[cid] = case_summary(
            cid,
            args.run_root / "cases" / cid / "postProcessing/wholePull/0/traces.csv",
            cfg, args.run_root / "timing" / (cid + ".time"), 32,
        )

    refinement = []
    for dt in (.04, .02, .01):
        trace = args.run_root / "cases" / ("LF-" + str(dt)) / "postProcessing/wholePull/0/traces.csv"
        rows = list(csv.DictReader(trace.open()))
        cfg = json.loads((args.run_root / "configs" / ("LF-" + str(dt) + ".json")).read_text())
        area = math.pi * cfg["geometry"]["basket_radius_m"] ** 2
        conductance = area * cfg["hydraulics"]["saturated_permeability_m2"] / (
            cfg["liquid"]["dynamic_viscosity_Pa_s"] * cfg["coffee_bed"]["bed_depth_m"]
        )
        pressure = 0.0
        maximum = 0.0
        for row in rows:
            reference = backward_euler(pressure, dt, 0.0, 2e-11, 6e-6, 1.2e6, conductance)
            maximum = max(maximum, relative(float(row["upstreamPressurePa"]), reference["pressure_Pa"], 1.0))
            pressure = reference["pressure_Pa"]
        exact = continuous(2.0, 0.0, 0.0, 2e-11, 6e-6, 1.2e6, conductance)
        refinement.append({
            "dt_s": dt, "maximum_discrete_relative_error": maximum,
            "continuous_endpoint_absolute_error_Pa":
                abs(float(rows[-1]["upstreamPressurePa"]) - exact["pressure_Pa"]),
            "trace_sha256": sha(trace),
        })
    orders = [
        math.log(refinement[i]["continuous_endpoint_absolute_error_Pa"] /
                 refinement[i + 1]["continuous_endpoint_absolute_error_Pa"], 2)
        for i in range(2)
    ]
    discrete = max(item["maximum_discrete_relative_error"] for item in refinement)

    eq_rows = list(csv.DictReader(open(
        args.run_root / "cases/LF-EQ/postProcessing/wholePull/0/traces.csv"
    )))
    eq_cfg = json.loads((args.run_root / "configs/LF-EQ.json").read_text())
    area = math.pi * eq_cfg["geometry"]["basket_radius_m"] ** 2
    conductance = area * eq_cfg["hydraulics"]["saturated_permeability_m2"] / (
        eq_cfg["liquid"]["dynamic_viscosity_Pa_s"] * eq_cfg["coffee_bed"]["bed_depth_m"]
    )
    eq_ref = continuous(100.0, 0.0, 0.0, 2e-11, 6e-6, 1.2e6, conductance)
    equilibrium = {
        "pressure_relative_error": relative(
            float(eq_rows[-1]["upstreamPressurePa"]), eq_ref["equilibrium_pressure_Pa"]
        ),
        "flow_relative_error": relative(
            float(eq_rows[-1]["puckFlowM3s"]),
            conductance * eq_ref["equilibrium_pressure_Pa"],
        ),
    }

    limiting = []
    for index in range(3):
        cfg = json.loads((args.run_root / "configs" / ("PL-" + str(index) + ".json")).read_text())
        rows = list(csv.DictReader(open(
            args.run_root / "cases" / ("PL-" + str(index)) / "postProcessing/wholePull/0/traces.csv"
        )))
        limiting.append({
            "case": "PL-" + str(index),
            "relative_error_to_prescribed_step":
                relative(float(rows[-1]["upstreamPressurePa"]), 900000.0),
        })

    tl_cfg = json.loads((args.run_root / "configs/TL.json").read_text())
    tl_rows = list(csv.DictReader(open(
        args.run_root / "cases/TL/postProcessing/wholePull/0/traces.csv"
    )))
    profile = tl_cfg["hydraulics"]["permeability_profile"]
    resistance = (
        profile["interface_position_m"] / profile["upstream_permeability_m2"]
        + (tl_cfg["coffee_bed"]["bed_depth_m"] - profile["interface_position_m"])
        / profile["downstream_permeability_m2"]
    )
    tl_g = math.pi * tl_cfg["geometry"]["basket_radius_m"] ** 2 / (
        tl_cfg["liquid"]["dynamic_viscosity_Pa_s"] * resistance
    )
    pressure = 0.0
    tl_error = 0.0
    for row in tl_rows:
        ref = backward_euler(pressure, .02, 0.0, 2e-11, 6e-6, 1.2e6, tl_g)
        tl_error = max(tl_error, relative(float(row["upstreamPressurePa"]), ref["pressure_Pa"], 1.0))
        pressure = ref["pressure_Pa"]

    dt_summaries = []
    for dt in (.02, .01, .005):
        cid = "MC2-DT-" + str(dt)
        path = args.run_root / "configs" / (cid + ".json")
        cfg = json.loads(path.read_text()); cfg["_path"] = path
        dt_summaries.append(case_summary(
            cid,
            args.run_root / "cases" / cid / "postProcessing/wholePull/0/traces.csv",
            cfg, args.run_root / "timing" / (cid + ".time"), 32,
        ))
    keys = (
        "first_drip_s", "maximum_sustained_post_saturation_basket_pressure_Pa",
        "final_cup_mass_kg", "final_tds_fraction",
        "final_extraction_yield_fraction",
    )
    dt_changes = {
        key: relative(dt_summaries[1][key], dt_summaries[2][key], 1e-20)
        for key in keys
    }
    dt_balance = max(
        summary["maximum_machine_water_balance_residual_m3"]
        for summary in dt_summaries
    )
    dt_gate = max(dt_changes.values()) <= .005 and dt_balance <= 1e-12 and all(
        summary["status"] == "PASS" for summary in dt_summaries
    )

    r0_errors = {
        key: (abs(cases["MC-0"][key] - expected)
              if key == "first_drip_s" else relative(cases["MC-0"][key], expected))
        for key, expected in R0_EXPECTED.items()
    }
    r0_pass = (
        r0_errors["first_drip_s"] <= 1e-8
        and max(value for key, value in r0_errors.items() if key != "first_drip_s") <= .005
    )
    wp02_trace = args.run_root / "cases/WP02-disabled/postProcessing/wholePull/0/traces.csv"
    predicted, _ = load_prediction(wp02_trace, 3.0, 965.0, 103.0, .02)
    late_mean = statistics.mean(predicted[900:1000])
    wp02_error = relative(late_mean, WP02_LATE_MEAN_G_S)

    result = {
        "schema_version": "espresso.public.wp02_002.results.v2",
        "physical_validation": "NOT_ESTABLISHED",
        "python": platform.python_version(),
        "analytical_linear_load": {
            "refinement": refinement, "observed_orders": orders,
            "equilibrium": equilibrium,
            "maximum_discrete_relative_error": discrete,
            "backward_euler_gate": "PASS" if discrete <= 1e-10 else "FAIL",
            "temporal_refinement_gate": "PASS" if min(orders) >= .8 and max(orders) <= 1.2 else "FAIL",
            "equilibrium_gate": "PASS" if max(equilibrium.values()) <= 1e-8 else "FAIL",
        },
        "prescribed_pressure_limit": {
            "sequence": limiting,
            "systematic_approach_gate": "PASS" if all(
                limiting[i]["relative_error_to_prescribed_step"]
                > limiting[i + 1]["relative_error_to_prescribed_step"]
                for i in range(2)
            ) else "FAIL",
        },
        "two_layer_fixture": {
            "maximum_discrete_relative_error": tl_error,
            "status": "PASS" if tl_error <= 1e-10 else "FAIL",
        },
        "regressions": {
            "prescribed_pressure_R0": {
                "errors": r0_errors, "status": "PASS" if r0_pass else "FAIL",
            },
            "WP02_coupling_disabled": {
                "predicted_late_mean_g_s": late_mean,
                "frozen_predicted_late_mean_g_s": WP02_LATE_MEAN_G_S,
                "relative_error": wp02_error,
                "status": "PASS" if wp02_error <= 1e-8 else "FAIL",
            },
        },
        "full_shot_time_refinement": {
            "cases": dt_summaries, "fine_pair_relative_changes": dt_changes,
            "maximum_fine_pair_relative_change": max(dt_changes.values()),
            "relative_output_acceptance": .005,
            "maximum_absolute_machine_water_balance_residual_m3": dt_balance,
            "machine_water_balance_acceptance_m3": 1e-12,
            "status": "PASS" if dt_gate else "FAIL",
        },
        "execution": {
            "openfoam_full_shot_cases": 8,
            "protected_scoring_invocations": 0,
            "openfoam_version": "Foundation 12",
        },
        "cases": cases,
    }
    adjudicate(result)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    if args.trace_output:
        fields = (
            "case", "time_s", "upstreamPressurePa", "basketPressurePa",
            "supplyFlowM3s", "puckFlowM3s", "compliantStorageM3",
            "machineWaterBalanceResidualM3", "couplingResidualM3s",
            "saturationTransitionStep", "wet_front_m", "first_drip_s",
            "cup_beverage_mass_kg", "cumulative_tds_mass_fraction",
            "extraction_yield_mass_fraction",
        )
        with args.trace_output.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for cid in cases:
                rows = list(csv.DictReader(open(
                    args.run_root / "cases" / cid / "postProcessing/wholePull/0/traces.csv"
                )))
                for index, row in enumerate(rows):
                    if index % 5 and index != len(rows) - 1:
                        continue
                    writer.writerow({"case": cid, **{key: row[key] for key in fields[1:]}})
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
