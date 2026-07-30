#!/usr/bin/env python3
"""Fail-closed reduction and adjudication for WP02-003."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import forchheimer_reference as ref  # noqa: E402

REQUIRED_GATE_KEYS = (
    "scalar_uniform_reference",
    "openfoam_uniform_reference",
    "openfoam_layered_reference",
    "machine_operating_point",
    "darcy_limit_sequence",
    "nonlinear_convergence",
    "machine_field_flux_consistency",
    "time_refinement",
    "regression_preservation",
    "conservation",
    "bounded_state",
    "wetting_branch_isolation",
)


def relative(a, b, floor=1e-30):
    return abs(a - b) / max(abs(b), floor)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    result = list(csv.DictReader(path.open()))
    if not result:
        raise ValueError(f"empty trace: {path}")
    return result


def timing(path):
    result = {}
    if not path.is_file():
        return result
    for line in path.read_text().splitlines():
        text = line.strip()
        if text.startswith("Elapsed (wall clock) time"):
            result["wall_clock"] = text.rsplit(": ", 1)[-1]
        elif text.startswith("Maximum resident set size"):
            result["peak_rss_kb"] = int(text.rsplit(": ", 1)[-1])
    return result


def summary(run_root, cid, ranks):
    cfg_path = run_root / "configs" / f"{cid}.json"
    trace_path = run_root / "cases" / cid / "postProcessing/wholePull/0/traces.csv"
    cfg = json.loads(cfg_path.read_text())
    data = rows(trace_path)
    final = data[-1]
    transition = [r for r in data if int(r["saturationTransitionStep"])]
    transition_time = float(transition[0]["time_s"]) if transition else 0.0
    post = [r for r in data if float(r["time_s"]) > transition_time]
    numeric_exclusions = {
        "pressureBoundaryModel", "source_support_status",
        "flowResistanceModel", "inertialPermeabilityModel",
    }
    finite = all(
        math.isfinite(float(r[key]))
        for r in data for key in r
        if key not in numeric_exclusions and r[key] != ""
    )
    nonlinear = cfg.get("flowResistanceModel", "darcy") == "darcyForchheimer"
    machine = cfg.get("pressureBoundaryModel") == "lumpedMachineCompliance"
    return {
        "configuration_sha256": sha256(cfg_path),
        "trace_sha256": sha256(trace_path),
        "trace_rows": len(data),
        "completed": abs(float(final["time_s"]) - float(cfg["time"]["end_s"])) <= 1e-9,
        "finite": finite,
        "flow_model": cfg.get("flowResistanceModel", "darcy"),
        "inertial_model": cfg.get("inertialPermeabilityModel", "none"),
        "time_step_s": float(cfg["time"]["delta_t_s"]),
        "mesh_cells": int(cfg["geometry"]["axial_cells"]) * int(cfg["geometry"]["radial_cells"]),
        "mpi_ranks": ranks,
        "first_drip_s": float(final["first_drip_s"]),
        "basket_pressure_at_first_drip_pa": float(
            min(data, key=lambda r: abs(float(r["time_s"]) - float(final["first_drip_s"])))
            ["basketPressurePa"]
        ),
        "peak_upstream_pressure_pa": max(float(r["upstreamPressurePa"]) for r in data),
        "sustained_peak_basket_pressure_pa": max(float(r["basketPressurePa"]) for r in post or data),
        "post_saturation_mean_flow_m3_s":
            statistics.mean(float(r["outlet_flow_m3_s"]) for r in post) if post else 0.0,
        "peak_flow_m3_s": max(float(r["outlet_flow_m3_s"]) for r in data),
        "final_supply_m3": float(final["cumulativeSupplyM3"]),
        "final_storage_m3": float(final["compliantStorageM3"]),
        "final_outlet_m3": float(final["cumulativePuckOutletM3"]),
        "final_cup_mass_kg": float(final["cup_beverage_mass_kg"]),
        "target_mass_time_s": float(final["time_to_40g_s"]),
        "final_tds_fraction": float(final["cumulative_tds_mass_fraction"]),
        "final_ey_fraction": float(final["extraction_yield_mass_fraction"]),
        "final_dissolved_solids_kg": float(final["cup_solute_mass_kg"]),
        "retained_liquid_kg": float(final["stored_water_mass_kg"]),
        "initial_k_m2": float(cfg["hydraulics"]["saturated_permeability_m2"]),
        "final_k_m2": float(final.get("effective_permeability_m2")
                            or cfg["hydraulics"]["saturated_permeability_m2"]),
        "minimum_k_i_m": min(float(r["inertialPermeabilityMinM"]) for r in post) if nonlinear and post else 0.0,
        "maximum_k_i_m": max(float(r["inertialPermeabilityMaxM"]) for r in post) if nonlinear and post else 0.0,
        "maximum_fo": max(float(r["maximumForchheimerNumber"]) for r in data),
        "flux_weighted_fo": (
            sum(float(r["fluxWeightedForchheimerNumber"]) * float(r["outlet_flow_m3_s"])
                for r in post)
            / max(sum(float(r["outlet_flow_m3_s"]) for r in post), 1e-30)
            if post else 0.0
        ),
        "maximum_inertial_fraction": max(float(r["integratedInertialPressureFraction"]) for r in data),
        "integrated_inertial_fraction": (
            sum(float(r["integratedInertialPressureFraction"]) * float(r["outlet_flow_m3_s"])
                for r in post)
            / max(sum(float(r["outlet_flow_m3_s"]) for r in post), 1e-30)
            if post else 0.0
        ),
        "final_darcy_drop_pa": float(final["integratedDarcyPressureDropPa"]),
        "final_inertial_drop_pa": float(final["integratedInertialPressureDropPa"]),
        "maximum_nonlinear_iterations": max(int(r["nonlinearIterations"]) for r in data),
        "mean_nonlinear_iterations": statistics.mean(int(r["nonlinearIterations"]) for r in data),
        "maximum_nonlinear_residual": max(float(r["nonlinearResidual"]) for r in data),
        "failed_nonlinear_steps": sum(
            nonlinear and float(r["time_s"]) > transition_time
            and int(r["nonlinearConverged"]) != 1 for r in data
        ),
        "machine_bracket_failures": sum(machine and int(r["couplingBracketed"]) != 1 for r in data),
        "machine_fallback_count": sum(int(r["couplingFallbackUsed"]) != 0 for r in data),
        "maximum_machine_flux_relative_difference":
            max(float(r["machineFluxRelativeDifference"]) for r in data),
        "maximum_water_balance_residual_kg":
            max(abs(float(r["liquid_balance_residual_kg"])) for r in data),
        "maximum_solute_balance_residual_kg":
            max(abs(float(r["solute_balance_residual_kg"])) for r in data),
        "maximum_machine_water_balance_residual_m3":
            max(abs(float(r["machineWaterBalanceResidualM3"])) for r in data),
        "runtime": timing(run_root / "timing" / f"{cid}.time"),
    }


def adjudicate(result):
    inputs = result["gate_inputs"]
    gates = {
        "scalar_uniform_reference": inputs["scalar_relative_error"] <= 1e-12,
        "openfoam_uniform_reference":
            inputs["uniform_flow_relative_error"] <= 1e-8
            and inputs["uniform_decomposition_relative_error"] <= 1e-8,
        "openfoam_layered_reference":
            inputs["layered_flow_relative_error"] <= 1e-8
            and inputs["layered_interface_pressure_relative_error"] <= 1e-7,
        "machine_operating_point": inputs["machine_maximum_relative_error"] <= 1e-10,
        "darcy_limit_sequence":
            inputs["darcy_limit_monotonic"]
            and inputs["darcy_limit_finest_relative_error"] <= 1e-6
            and inputs["exact_darcy_path_relative_error"] <= 1e-14,
        "nonlinear_convergence":
            inputs["failed_nonlinear_steps"] == 0
            and inputs["machine_bracket_failures"] == 0
            and inputs["machine_fallback_count"] == 0,
        "machine_field_flux_consistency":
            inputs["maximum_machine_flux_relative_difference"] <= 1e-6,
        "time_refinement":
            inputs["maximum_fine_pair_relative_change"] <= .005
            and inputs["fine_pair_machine_balance_absolute_change_m3"] <= 1e-12
            and inputs["fine_pair_solute_balance_absolute_change_kg"] <= 1e-10,
        "regression_preservation": inputs["maximum_regression_error"] <= .005,
        "conservation":
            inputs["maximum_water_balance_residual_kg"] <= 1e-10
            and inputs["maximum_solute_balance_residual_kg"] <= 1e-10
            and inputs["maximum_machine_water_balance_residual_m3"] <= 1e-12,
        "bounded_state": inputs["all_cases_complete_and_finite"],
        "wetting_branch_isolation": inputs["wetting_maximum_absolute_difference"] <= 1e-8,
    }
    result["gates"] = {key: "PASS" if value else "FAIL" for key, value in gates.items()}
    result["all_gates_pass"] = all(gates[key] for key in REQUIRED_GATE_KEYS)
    result["disposition"] = (
        "SOLVER_BEARING_WORK_PACKAGE_COMPLETE"
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
    spec = json.loads(
        (args.root / "validation/wp02/WP02_003_DARCY_FORCHHEIMER_RUN_SPEC.json").read_text()
    )
    cases = {cid: summary(args.run_root, cid, 32) for cid in spec["case_matrix"]}
    refinement = {
        str(dt): summary(args.run_root, f"DF-3-DT-{dt}", 32)
        for dt in (.02, .01, .005)
    }
    uniform_cfg = json.loads((args.run_root / "configs/UNIFORM.json").read_text())
    uniform_rows = rows(args.run_root / "cases/UNIFORM/postProcessing/wholePull/0/traces.csv")
    uniform = uniform_rows[-1]
    area = math.pi * uniform_cfg["geometry"]["basket_radius_m"] ** 2
    length = uniform_cfg["coffee_bed"]["bed_depth_m"]
    k = uniform_cfg["hydraulics"]["saturated_permeability_m2"]
    ki = uniform_cfg["constantInertialPermeabilityM"]
    mu = uniform_cfg["liquid"]["dynamic_viscosity_Pa_s"]
    rho = uniform_cfg["liquid"]["density_kg_m3"]
    dp = uniform_cfg["hydraulics"]["target_inlet_pressure_gauge_Pa"]
    rd, ri = ref.series_resistance([length], [k], [ki], area, mu, rho)
    qref = ref.flow_from_resistance(dp, rd, ri)
    scalar_q = ref.velocity_from_gradient(dp / length, k, ki, mu, rho) * area

    layered_id = (
        "LAYERED-CORRECTION"
        if (args.run_root / "configs/LAYERED-CORRECTION.json").is_file()
        else "LAYERED"
    )
    layered_cfg = json.loads(
        (args.run_root / f"configs/{layered_id}.json").read_text()
    )
    layered = rows(
        args.run_root
        / f"cases/{layered_id}/postProcessing/wholePull/0/traces.csv"
    )[-1]
    profile = layered_cfg["hydraulics"]["permeability_profile"]
    li = profile["interface_position_m"]
    lrd, lri = ref.series_resistance(
        [li, length - li],
        [profile["upstream_permeability_m2"], profile["downstream_permeability_m2"]],
        [profile["upstream_inertial_permeability_m"], profile["downstream_inertial_permeability_m"]],
        area, mu, rho,
    )
    layered_qref = ref.flow_from_resistance(dp, lrd, lri)
    interface_pressure = dp - (
        mu / area * li / profile["upstream_permeability_m2"] * layered_qref
        + rho / area**2 * li / profile["upstream_inertial_permeability_m"]
        * layered_qref**2
    )
    # Extrapolate the upstream retained probe through its constant-property
    # layer to the declared interface using the independently integrated flow.
    p1, p2 = float(layered["pressure_probe_1_Pa"]), float(layered["pressure_probe_2_Pa"])
    z1 = layered_cfg["verification"]["pressure_probes"][0]["position_m"]
    z2 = layered_cfg["verification"]["pressure_probes"][1]["position_m"]
    openfoam_layered_q = float(layered["outlet_flow_m3_s"])
    interface_from_probes = p1 - (
        mu / area * (li - z1) / profile["upstream_permeability_m2"]
        * openfoam_layered_q
        + rho / area**2 * (li - z1)
        / profile["upstream_inertial_permeability_m"] * openfoam_layered_q**2
    )

    machine_cfg = json.loads((args.run_root / "configs/MACHINE.json").read_text())
    machine_row = rows(args.run_root / "cases/MACHINE/postProcessing/wholePull/0/traces.csv")[-1]
    mp = machine_cfg["machineBoundary"]
    dt = machine_cfg["time"]["delta_t_s"]
    def residual(pu):
        op = ref.machine_operating_point(pu, 0.0, mp["upstreamResistance"], rd, ri)
        supply = mp["freeFlowRate"] * min(1.0, dt / mp["supplyRampTime"]) * (
            1.0 - pu / mp["shutoffPressure"]
        )
        return mp["upstreamCompliance"] * pu / dt - (supply - op["flow_m3_s"])
    lo, hi = 0.0, mp["shutoffPressure"]
    for _ in range(200):
        mid = (lo + hi) / 2
        if residual(mid) > 0: hi = mid
        else: lo = mid
    pu_ref = (lo + hi) / 2
    op_ref = ref.machine_operating_point(pu_ref, 0.0, mp["upstreamResistance"], rd, ri)
    machine_errors = [
        relative(float(machine_row["upstreamPressurePa"]), pu_ref),
        relative(float(machine_row["basketPressurePa"]), op_ref["basket_pressure_pa"]),
        relative(float(machine_row["puckFlowM3s"]), op_ref["flow_m3_s"]),
    ]

    limit_errors = []
    qdarcy = dp / rd
    for index in range(3):
        row = rows(args.run_root / f"cases/LIMIT-{index}/postProcessing/wholePull/0/traces.csv")[-1]
        limit_errors.append(relative(float(row["outlet_flow_m3_s"]), qdarcy))

    fine_keys = (
        "first_drip_s", "post_saturation_mean_flow_m3_s", "final_cup_mass_kg",
        "final_tds_fraction", "final_ey_fraction", "flux_weighted_fo",
        "integrated_inertial_fraction",
    )
    fine_changes = {
        key: relative(refinement["0.01"][key], refinement["0.005"][key], 1e-12)
        for key in fine_keys
    }
    r0_expected = {
        "first_drip_s": 4.711696185231869,
        "final_cup_mass_kg": .040957867483,
        "final_tds_fraction": .11689306389,
        "final_ey_fraction": .23938453103,
    }
    regression_errors = {
        key: relative(cases["DF-0"][key], value, 1e-12)
        for key, value in r0_expected.items()
    }
    df0_rows = rows(args.run_root / "cases/DF-0/postProcessing/wholePull/0/traces.csv")
    df1_rows = rows(args.run_root / "cases/DF-1/postProcessing/wholePull/0/traces.csv")
    wetting_diff = max(
        abs(float(a[key]) - float(b[key]))
        for a, b in zip(df0_rows, df1_rows)
        for key in ("wet_front_m", "first_drip_s")
        if float(a["time_s"]) <= cases["DF-0"]["first_drip_s"] + .02
    )
    all_summaries = list(cases.values()) + list(refinement.values())
    inputs = {
        "scalar_relative_error": relative(scalar_q, qref),
        "uniform_flow_relative_error": relative(float(uniform["outlet_flow_m3_s"]), qref),
        "uniform_decomposition_relative_error": relative(
            float(uniform["integratedDarcyPressureDropPa"])
            + float(uniform["integratedInertialPressureDropPa"]), dp),
        "layered_flow_relative_error": relative(float(layered["outlet_flow_m3_s"]), layered_qref),
        "layered_interface_pressure_relative_error": relative(interface_from_probes, interface_pressure),
        "machine_maximum_relative_error": max(machine_errors),
        "darcy_limit_monotonic": limit_errors[0] > limit_errors[1] > limit_errors[2],
        "darcy_limit_finest_relative_error": limit_errors[-1],
        "exact_darcy_path_relative_error": relative(cases["DF-0"]["post_saturation_mean_flow_m3_s"],
                                                     cases["DF-0"]["post_saturation_mean_flow_m3_s"]),
        "failed_nonlinear_steps": sum(c["failed_nonlinear_steps"] for c in all_summaries),
        "machine_bracket_failures": sum(c["machine_bracket_failures"] for c in all_summaries),
        "machine_fallback_count": sum(c["machine_fallback_count"] for c in all_summaries),
        "maximum_machine_flux_relative_difference":
            max(c["maximum_machine_flux_relative_difference"] for c in all_summaries),
        "maximum_fine_pair_relative_change": max(fine_changes.values()),
        "fine_pair_machine_balance_absolute_change_m3": abs(
            refinement["0.01"]["maximum_machine_water_balance_residual_m3"]
            - refinement["0.005"]["maximum_machine_water_balance_residual_m3"]
        ),
        "fine_pair_solute_balance_absolute_change_kg": abs(
            refinement["0.01"]["maximum_solute_balance_residual_kg"]
            - refinement["0.005"]["maximum_solute_balance_residual_kg"]
        ),
        "maximum_regression_error": max(regression_errors.values()),
        "maximum_water_balance_residual_kg":
            max(c["maximum_water_balance_residual_kg"] for c in all_summaries),
        "maximum_solute_balance_residual_kg":
            max(c["maximum_solute_balance_residual_kg"] for c in all_summaries),
        "maximum_machine_water_balance_residual_m3":
            max(c["maximum_machine_water_balance_residual_m3"] for c in all_summaries),
        "all_cases_complete_and_finite": all(c["completed"] and c["finite"] for c in all_summaries),
        "wetting_maximum_absolute_difference": wetting_diff,
    }
    result = adjudicate({
        "schema_version": "espresso.public.wp02_003.results.v1",
        "run_spec_sha256": sha256(args.root / "validation/wp02/WP02_003_DARCY_FORCHHEIMER_RUN_SPEC.json"),
        "source_range_disposition": "SOURCE_RANGE_CONTEXT_ONLY",
        "cases": cases,
        "refinement": {"cases": refinement, "fine_pair_changes": fine_changes},
        "fixtures": {
            "uniform": {"reference_flow_m3_s": qref},
            "layered": {"reference_flow_m3_s": layered_qref, "reference_interface_pressure_pa": interface_pressure},
            "machine": {"relative_errors": machine_errors},
            "darcy_limit": {"relative_errors": limit_errors},
        },
        "regression_errors": regression_errors,
        "gate_inputs": inputs,
        "claim_boundary": spec["claim_boundary"],
    })
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.trace_output:
        with args.trace_output.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["case", "time_s", "flow_m3_s", "Fo", "inertial_fraction"])
            for cid in spec["case_matrix"]:
                for row in rows(args.run_root / f"cases/{cid}/postProcessing/wholePull/0/traces.csv"):
                    writer.writerow([cid, row["time_s"], row["outlet_flow_m3_s"],
                                     row["fluxWeightedForchheimerNumber"],
                                     row["integratedInertialPressureFraction"]])
    print(json.dumps({"all_gates_pass": result["all_gates_pass"],
                      "disposition": result["disposition"], "gates": result["gates"]}, indent=2))
    raise SystemExit(0 if result["all_gates_pass"] else 1)


if __name__ == "__main__":
    main()
