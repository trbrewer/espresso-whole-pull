#!/usr/bin/env python3
"""Fail-closed WP03-001 numerical result adjudication."""

import argparse
import csv
import hashlib
import json
import math
import pathlib
import re
import sys

import poroelastic_compaction_reference as ref


FULL_CASES = [f"PE-{i}" for i in range(8)]
DT_CASES = [f"PE-7-DT-{x}" for x in (0.02, 0.01, 0.005)]
NX_CASES = [f"PE-7-NX-{x}" for x in (128, 256, 512)]
REQUIRED_CASES = FULL_CASES + DT_CASES + NX_CASES


def adjudicate_gates(gates):
    """Single fail-closed disposition path used by production and adversarial tests."""
    passed = bool(gates) and all(value is True for value in gates.values())
    return passed, (
        "SOLVER_BEARING_WORK_PACKAGE_COMPLETE_PR_OPEN"
        if passed else "NUMERICAL_FAILURE"
    )


def rel(a, b, floor=1e-30):
    return abs(a-b)/max(abs(b), floor)


def finite(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def comparison_error(observed, expected, absolute_tolerance=1e-15):
    """Relative error with a declared absolute comparison at exact zero."""
    observed, expected = float(observed), float(expected)
    if not finite(observed) or not finite(expected):
        return math.inf
    if expected == 0.0:
        return 0.0 if abs(observed) <= absolute_tolerance else math.inf
    return rel(observed, expected)


def local_constitutive_comparison(fixture, critical_pressure_pa):
    """Compare retained production C++ constitutive values with Python."""
    rows = fixture.get("local_constitutive_values")
    expected_pairs = {
        (phi, x) for phi in (0.1, 0.4, 0.8)
        for x in (0.0, 0.1, 0.5, 0.8, 0.95)}
    if not isinstance(rows, list) or len(rows) != len(expected_pairs):
        return {
            "maximumCompactionStrainReferenceError": math.inf,
            "maximumMechanicalPorosityReferenceError": math.inf,
            "maximumPermeabilityRatioReferenceError": math.inf,
            "allStateBoundsPass": False}
    observed_pairs = set()
    strain_errors, porosity_errors, permeability_errors = [], [], []
    bounds = True
    for row in rows:
        try:
            phi = float(row["stressFreePorosity"])
            x = float(row["normalizedEffectiveStress"])
            pair = (phi, x)
            observed_pairs.add(pair)
            sigma = x*critical_pressure_pa
            strain_errors.append(comparison_error(
                row["productionCompactionStrain"],
                ref.strain(sigma, phi, critical_pressure_pa)))
            porosity_errors.append(comparison_error(
                row["productionMechanicalPorosity"],
                ref.mechanical_porosity(sigma, phi, critical_pressure_pa)))
            permeability_errors.append(comparison_error(
                row["productionPermeabilityRatio"],
                ref.permeability_ratio(sigma, phi, critical_pressure_pa)))
            bounds = bounds and row.get("stateBoundsPass") is True
        except (KeyError, TypeError, ValueError):
            bounds = False
            strain_errors.append(math.inf)
            porosity_errors.append(math.inf)
            permeability_errors.append(math.inf)
    return {
        "maximumCompactionStrainReferenceError": max(strain_errors),
        "maximumMechanicalPorosityReferenceError": max(porosity_errors),
        "maximumPermeabilityRatioReferenceError": max(permeability_errors),
        "allStateBoundsPass": bounds and observed_pairs == expected_pairs}


def mapped_maximum_error(observed, expected, mapping):
    """Numerically compare declared observed/accepted predecessor quantities."""
    errors = {}
    for observed_key, expected_key in mapping:
        try:
            errors[observed_key] = comparison_error(
                observed[observed_key], expected[expected_key])
        except (KeyError, TypeError):
            errors[observed_key] = math.inf
    return max(errors.values(), default=math.inf), errors


def predecessor_gate_results(comparisons):
    """Return separate fail-closed predecessor gates from retained comparisons."""
    names = ("r0", "wp02_001", "wp02_002_mc2", "wp02_003", "wp02_004")
    return {
        name + "_regression":
            isinstance(comparisons.get(name), dict)
            and comparisons[name].get("complete") is True
            and finite(comparisons[name].get("maximum_relative_error"))
            and float(comparisons[name]["maximum_relative_error"])
                <= float(comparisons[name].get("tolerance", 1e-8))
        for name in names}


def trace(run_root, case_id):
    path = run_root/"cases"/case_id/"postProcessing/wholePull/0/traces.csv"
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def floats(row):
    result = {}
    for key, value in row.items():
        try:
            result[key] = float(value)
        except (TypeError, ValueError):
            result[key] = value
    return result


def completion(rows, configured_end, tolerance):
    times = [float(row["time_s"]) for row in rows]
    required = (
        "cup_beverage_mass_kg", "cumulative_tds_mass_fraction",
        "extraction_yield_mass_fraction", "liquid_balance_residual_kg",
        "solute_balance_residual_kg")
    ok = (
        bool(rows) and all(finite(x) for x in times)
        and all(b > a for a, b in zip(times, times[1:]))
        and times[-1] >= configured_end-tolerance
        and all(finite(rows[-1].get(key)) for key in required)
        and all(float(row.get("couplingConverged", 1)) == 1 for row in rows)
        and all(float(row.get("poroelasticNonlinearConverged", 1)) == 1
                for row in rows))
    return {"passed": ok, "final_time_s": times[-1] if times else None,
            "configured_end_time_s": configured_end}


def timing(path):
    text = path.read_text() if path.exists() else ""
    wall = re.search(r"Elapsed \(wall clock\) time.*:\s*(\S+)", text)
    rss = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", text)
    return {"wall_clock": wall.group(1) if wall else "UNAVAILABLE",
            "peak_rss_kb": int(rss.group(1)) if rss else None}


def metric_change(a, b):
    keys = (
        "first_drip_s", "upstreamPressurePa", "basketPressurePa",
        "outlet_flow_m3_s", "minimumMechanicalPorosity",
        "minimumPermeabilityRatio", "predictedBedHeightRatio",
        "cup_beverage_mass_kg", "cumulative_tds_mass_fraction",
        "extraction_yield_mass_fraction")
    relative = max(rel(float(a[k]), float(b[k]), 1e-12) for k in keys)
    balance_absolute = max(
        abs(float(a[k])-float(b[k])) for k in
        ("liquid_balance_residual_kg", "solute_balance_residual_kg"))
    return max(relative, balance_absolute/1e-9)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path)
    parser.add_argument("--run-root", type=pathlib.Path)
    parser.add_argument("--executable", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--trace-output", type=pathlib.Path)
    parser.add_argument("--source-output", type=pathlib.Path)
    parser.add_argument("--check-production-fixture", type=pathlib.Path)
    args = parser.parse_args()
    if args.check_production_fixture is not None:
        try:
            fixture = json.loads(args.check_production_fixture.read_text())
            comparison = local_constitutive_comparison(fixture, 1.239155e6)
            passed = (
                comparison["allStateBoundsPass"]
                and max(
                    comparison["maximumCompactionStrainReferenceError"],
                    comparison["maximumMechanicalPorosityReferenceError"],
                    comparison["maximumPermeabilityRatioReferenceError"])
                    <= 1e-12)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            comparison, passed = {}, False
        result = {
            "comparison": comparison,
            "gates": {"local_constitutive_reference": passed},
            "all_gates_pass": passed,
            "disposition": (
                "LOCAL_CONSTITUTIVE_FIXTURE_PASS"
                if passed else "NUMERICAL_FAILURE")}
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
        return 0 if passed else 1
    missing = [
        name for name in ("root", "run_root", "executable",
                          "trace_output", "source_output")
        if getattr(args, name) is None]
    if missing:
        parser.error("full analysis requires: " + ", ".join(missing))
    spec_path = args.root/"validation/wp03/WP03_001_POROELASTIC_COMPACTION_RUN_SPEC.json"
    spec = json.loads(spec_path.read_text())
    accept, reference = spec["acceptance"], spec["reference"]
    case_rows = {case: trace(args.run_root, case) for case in REQUIRED_CASES}
    cases = {}
    combined = []
    for case, rows in case_rows.items():
        cfg = json.loads((args.run_root/"configs"/f"{case}.json").read_text())
        final = floats(rows[-1])
        comp = completion(rows, cfg["time"]["end_s"],
                          accept["case_completion_time_tolerance_s"])
        post = [floats(row) for row in rows
                if float(row["wet_front_m"])
                >= cfg["coffee_bed"]["bed_depth_m"]-1e-12
                and int(float(row.get("saturationTransitionStep", 0))) == 0]
        mean_flow = sum(r["outlet_flow_m3_s"] for r in post)/len(post) if post else 0
        cases[case] = {
            "completed": comp["passed"], "completion": comp,
            "pressure_model": cfg.get("pressureBoundaryModel", "prescribedPressure"),
            "mechanics_model": cfg.get("bedMechanicsModel", "none"),
            "construction": spec["case_matrix"].get(case.split("-DT")[0].split("-NX")[0],
                                                     {}).get("construction"),
            "target_pressure_pa": cfg["hydraulics"]["target_inlet_pressure_gauge_Pa"],
            "stress_free_permeability_m2": final["stressFreePermeabilityM2"],
            "mean_outlet_flow_m3_s": mean_flow,
            "minimum_mechanical_porosity": final["minimumMechanicalPorosity"],
            "minimum_permeability_ratio": final["minimumPermeabilityRatio"],
            "predicted_bed_height_ratio": final["predictedBedHeightRatio"],
            "first_drip_s": final["first_drip_s"],
            "cup_mass_kg": final["cup_beverage_mass_kg"],
            "tds": final["cumulative_tds_mass_fraction"],
            "ey": final["extraction_yield_mass_fraction"],
            "water_residual_kg": final["liquid_balance_residual_kg"],
            "solute_residual_kg": final["solute_balance_residual_kg"],
            "maximum_nonlinear_iterations": max(float(r.get("poroelasticNonlinearIterations", 0)) for r in rows),
            "maximum_nonlinear_residual": max(float(r.get("poroelasticNonlinearResidual", 0)) for r in rows),
            "maximum_machine_field_mismatch": max(float(r.get("machineFieldFluxRelativeDifference", 0)) for r in rows),
            "runtime": timing(args.run_root/"timing"/f"{case}.time"),
            "axial_cells": cfg["geometry"]["axial_cells"],
            "radial_cells": cfg["geometry"]["radial_cells"],
            "mpi_ranks": 32,
            "dt_s": cfg["time"]["delta_t_s"]}
        run_class = ("FULL_SHOT" if case in FULL_CASES else
                     "TIMESTEP_REFINEMENT" if "-DT-" in case else "AXIAL_MESH_REFINEMENT")
        for row_index, row in enumerate(rows):
            time_value = float(row["time_s"])
            retain_row = (
                row_index in (0, len(rows)-1)
                or float(row.get("saturationTransitionStep", 0)) == 1
                or abs(time_value/0.1-round(time_value/0.1)) <= 1e-8
            )
            if not retain_row:
                continue
            item = dict(row)
            item.update({"caseId":case, "runClass":run_class,
                         "configuredEndTimeS":cfg["time"]["end_s"],
                         "timestepS":cfg["time"]["delta_t_s"],
                         "axialCellCount":cfg["geometry"]["axial_cells"],
                         "radialCellCount":cfg["geometry"]["radial_cells"]})
            combined.append(item)

    fixture = json.loads((args.run_root/"WP03_001_PRODUCTION_FIXTURE.json").read_text())
    phi, pc = reference["stress_free_porosity"], reference["critical_compaction_pressure_pa"]
    area = math.pi*0.029**2
    scalar_reference = float(ref.flow(500000, area,
        0.009011660896432553, 0.0003, phi, pc, 3.0e-15))
    scalar_error = rel(fixture["scalar_flow_m3_s"], scalar_reference)
    local_comparison = local_constitutive_comparison(fixture, pc)
    maximum_local_error = max(
        local_comparison["maximumCompactionStrainReferenceError"],
        local_comparison["maximumMechanicalPorosityReferenceError"],
        local_comparison["maximumPermeabilityRatioReferenceError"])
    universal = fixture["universal_errors"]

    profile_errors = {}
    max_profile_flow = max_profile_pressure = max_profile_state = max_height = 0.0
    base_cfg = json.loads((args.root/"config/reference_R0.json").read_text())
    depth = base_cfg["coffee_bed"]["bed_depth_m"]
    for bar in (5,9,11):
        row = floats(trace(args.run_root,f"PROFILE-{bar}BAR")[-1])
        dp = bar*1e5
        exact_flow = float(ref.flow(dp, area, depth, .000315, phi, pc,
                          reference["matched_stress_free_permeability_m2"]))
        flow_error = rel(row["openFoamOutletFlowM3s"], exact_flow)
        nx = 8192
        half_width_fraction = (
            base_cfg["verification"]["pressure_probes"][0]["half_width_m"]/depth
        )
        def probe_average(location):
            positions = [(i+.5)/nx for i in range(nx)
                         if abs((i+.5)/nx-location) <= half_width_fraction]
            return sum(float(ref.pressure_at_position(z,dp,phi,pc))
                       for z in positions)/len(positions)
        p1 = probe_average(.25)
        p2 = probe_average(.75)
        pressure_error = max(rel(row["pressure_probe_1_Pa"],p1),
                             rel(row["pressure_probe_2_Pa"],p2))
        state_error = rel(row["outletMechanicalPorosity"],
                          float(ref.mechanical_porosity(dp,phi,pc)))
        perm_error = rel(row["outletCompactionPermeabilityM2"],
                         reference["matched_stress_free_permeability_m2"]*
                         float(ref.permeability_ratio(dp,phi,pc)))
        height_error = rel(row["predictedBedHeightRatio"],
                           float(ref.bed_height_ratio(dp,phi,pc)))
        profile_errors[str(bar)] = {"flow":flow_error,"pressure":pressure_error,
            "porosity":state_error,"permeability":perm_error,"bed_height":height_error}
        max_profile_flow=max(max_profile_flow,flow_error)
        max_profile_pressure=max(max_profile_pressure,pressure_error)
        max_profile_state=max(max_profile_state,state_error,perm_error)
        max_height=max(max_height,height_error)

    source_points = json.loads((args.run_root/"configs/SOURCE_POINTS.json").read_text())
    source_rows = []
    source_phi = reference["source"]["stress_free_porosity"]
    source_pc = reference["source"]["critical_compaction_pressure_pa"]
    source_qc = reference["source"]["critical_mass_flow_g_s"]
    source_k = reference["source"]["stress_free_permeability_m2"]
    src_area = math.pi*reference["source"]["basket_radius_m"]**2
    source_field_errors = []
    src_index = 0
    for point in source_points:
        pbar = point["basket_pressure_bar"]
        universal_flow = source_qc*float(ref.universal_qhat(pbar/(source_pc/1e5)))
        finite_flow = float(ref.flow(pbar*1e5,src_area,
            reference["source"]["bed_depth_m"], reference["source"]["dynamic_viscosity_pa_s"],
            source_phi,source_pc,source_k))*reference["source"]["density_kg_m3"]*1000
        foam_flow = None
        if point["domain_status"] == "IN_DOMAIN":
            foam = floats(trace(args.run_root,f"SRC-{src_index:02d}")[-1])
            foam_flow=foam["openFoamOutletFlowM3s"]*reference["source"]["density_kg_m3"]*1000
            source_field_errors.append(rel(foam_flow,finite_flow))
        source_rows.append({**point,"universal_curve_flow_g_s":universal_flow,
            "finite_phi_flow_g_s":finite_flow,"openfoam_flow_g_s":foam_flow,
            "finite_phi_vs_universal_relative_difference":rel(finite_flow,universal_flow),
            "source_residual_g_s":universal_flow-point["measured_mass_flow_g_s"]})
        src_index += 1

    rigid_keys=("outlet_flow_m3_s","cup_beverage_mass_kg",
                "cumulative_tds_mass_fraction","extraction_yield_mass_fraction")
    rigid_error=max(rel(float(case_rows["PE-1"][-1][k]),float(case_rows["PE-0"][-1][k]),1e-12)
                    for k in rigid_keys)
    matched_analytical=fixture["matched_identity_relative_error"]
    matched_openfoam=rel(cases["PE-3"]["mean_outlet_flow_m3_s"],
                         cases["PE-0"]["mean_outlet_flow_m3_s"])
    machine_ref = ref.machine_step(10,.02,700000,0,2e-11,2e11,7e-6,1.2e6,3,
        lambda drop: ref.flow(drop,area,depth,.0003,phi,pc,
                             fixture["matched_permeability_m2"]))
    machine_error=max(
        rel(fixture["machine_upstream_pressure_pa"],float(machine_ref["upstream_pressure_pa"])),
        rel(fixture["machine_basket_pressure_pa"],float(machine_ref["basket_pressure_pa"])),
        rel(fixture["machine_puck_flow_m3_s"],float(machine_ref["puck_flow_m3_s"])),
        rel(fixture["machine_storage_m3"],float(machine_ref["storage_m3"])))
    dt_change=metric_change(floats(case_rows["PE-7-DT-0.005"][-1]),
                            floats(case_rows["PE-7-DT-0.01"][-1]))
    nx_change=metric_change(floats(case_rows["PE-7-NX-512"][-1]),
                            floats(case_rows["PE-7-NX-256"][-1]))
    wetting_error=max(
        abs(cases["PE-0"]["first_drip_s"]-cases["PE-2"]["first_drip_s"]),
        abs(cases["PE-6"]["first_drip_s"]-cases["PE-7"]["first_drip_s"]))
    comp_rows=[r for c in REQUIRED_CASES for r in case_rows[c]
               if r.get("bedMechanicsModel")=="waszkiewiczQuasiStaticCompaction"]
    bounded=all(
        finite(r.get(k)) for r in comp_rows for k in (
          "maximumEffectiveStressPa","maximumNormalizedEffectiveStress",
          "minimumMechanicalPorosity","minimumCompactionPermeabilityM2",
          "predictedBedHeightRatio")) and all(
        -1e-12 <= float(r["maximumNormalizedEffectiveStress"]) < 1
        and 0 < float(r["minimumMechanicalPorosity"]) <= float(r["stressFreePorosity"])
        and 0 < float(r["minimumPermeabilityRatio"]) <= 1
        and 0 < float(r["predictedBedHeightRatio"]) <= 1 for r in comp_rows)
    nonlinear=all(float(r["poroelasticNonlinearConverged"])==1 for r in comp_rows)
    machine_flux=max(float(r.get("machineFieldFluxRelativeDifference",0))
                     for r in comp_rows)
    maximum_water_residual=max(
        abs(float(r["liquid_balance_residual_kg"]))
        for c in REQUIRED_CASES for r in case_rows[c])
    maximum_solute_residual=max(
        abs(float(r["solute_balance_residual_kg"]))
        for c in REQUIRED_CASES for r in case_rows[c])
    transport_contract=all(float(r["mechanicalPorosityCoupledToStorage"])==0 for r in comp_rows)
    completed=all(cases[c]["completed"] for c in REQUIRED_CASES)

    wp02_004_accepted = json.loads(
        (args.root/"validation/wp02/WP02_004_RADIAL_HETEROGENEITY_RESULTS.json").read_text())
    wp02_003_accepted = json.loads(
        (args.root/"validation/wp02/WP02_003_DARCY_FORCHHEIMER_RESULTS.json").read_text())

    def observed_case(case_id):
        rows = case_rows[case_id]
        return {
            "first_drip_s": cases[case_id]["first_drip_s"],
            "peak_upstream_pressure_pa":
                max(float(r["upstreamPressurePa"]) for r in rows),
            "peak_basket_pressure_pa":
                max(float(r["basketPressurePa"]) for r in rows
                    if float(r.get("saturationTransitionStep", 0)) == 0),
            "mean_total_flow_m3_s": cases[case_id]["mean_outlet_flow_m3_s"],
            "cup_mass_kg": cases[case_id]["cup_mass_kg"],
            "tds": cases[case_id]["tds"],
            "ey": cases[case_id]["ey"],
            "water_residual_kg":
                max(abs(float(r["liquid_balance_residual_kg"])) for r in rows),
            "solute_residual_kg":
                max(abs(float(r["solute_balance_residual_kg"])) for r in rows)}

    control_mapping = (
        ("first_drip_s", "first_drip_s"),
        ("peak_upstream_pressure_pa", "peak_upstream_pressure_pa"),
        ("peak_basket_pressure_pa", "peak_basket_pressure_pa"),
        ("mean_total_flow_m3_s", "mean_total_flow_m3_s"),
        ("cup_mass_kg", "cup_mass_kg"), ("tds", "tds"), ("ey", "ey"),
        ("water_residual_kg", "water_residual_kg"),
        ("solute_residual_kg", "solute_residual_kg"))
    r0_error, r0_metrics = mapped_maximum_error(
        observed_case("PE-0"), wp02_004_accepted["cases"]["RH-0"],
        control_mapping)
    mc2_error, mc2_metrics = mapped_maximum_error(
        observed_case("PE-6"), wp02_004_accepted["cases"]["RH-5"],
        control_mapping)

    wp02_001_path = args.run_root/"WP02_COUPLING_DISABLED_REGRESSION.json"
    try:
        wp02_001_result = json.loads(wp02_001_path.read_text())
        wp02_001_error = float(wp02_001_result["relative_error"])
        wp02_001_complete = wp02_001_result.get("status") == "PASS"
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        wp02_001_result, wp02_001_error, wp02_001_complete = {}, math.inf, False

    try:
        uniform = floats(trace(args.run_root/"predecessor-wp02-003", "UNIFORM")[-1])
        layered = floats(trace(args.run_root/"predecessor-wp02-003", "LAYERED")[-1])
        wp02_003_metrics = {
            "uniform_flow": rel(
                uniform["openFoamOutletFlowM3s"],
                wp02_003_accepted["fixtures"]["uniform"]["reference_flow_m3_s"]),
            "uniform_pressure_decomposition": rel(
                uniform["integratedDarcyPressureDropPa"]
                  + uniform["integratedInertialPressureDropPa"],
                uniform["basketPressurePa"]),
            "layered_flow": rel(
                layered["openFoamOutletFlowM3s"],
                wp02_003_accepted["fixtures"]["layered"]["reference_flow_m3_s"]),
            "layered_pressure_decomposition": rel(
                layered["integratedDarcyPressureDropPa"]
                  + layered["integratedInertialPressureDropPa"],
                layered["basketPressurePa"])}
        wp02_003_error = max(wp02_003_metrics.values())
        wp02_003_complete = (
            uniform["maximumForchheimerNumber"] > 0
            and layered["maximumForchheimerNumber"] > 0)
    except (OSError, KeyError, TypeError, ValueError, IndexError):
        wp02_003_metrics, wp02_003_error, wp02_003_complete = {}, math.inf, False

    wp02_004_path = (
        args.run_root/"predecessor-wp02-004/WP02_004_PRODUCTION_FIXTURE.json")
    try:
        wp02_004_observed = json.loads(wp02_004_path.read_text())
        wp02_004_reference = wp02_004_accepted["production_fixture"]
        wp02_004_numeric_keys = sorted(
            key for key, value in wp02_004_reference.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool))
        wp02_004_error, wp02_004_metrics = mapped_maximum_error(
            wp02_004_observed, wp02_004_reference,
            tuple((key, key) for key in wp02_004_numeric_keys))
        wp02_004_complete = all(
            wp02_004_observed.get(key) is wp02_004_reference[key]
            for key in ("basket_bracketed", "basket_converged",
                        "machine_bracketed", "machine_converged"))
        wp02_004_complete = (
            wp02_004_complete
            and wp02_004_observed.get("fallback_count") == 0)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        wp02_004_metrics, wp02_004_error, wp02_004_complete = {}, math.inf, False

    predecessor = {
      "r0": {"maximum_relative_error": r0_error, "metric_errors": r0_metrics,
             "complete": True, "tolerance": 1e-8},
      "wp02_001": {
          "maximum_relative_error": wp02_001_error,
          "metric_errors": {"authoritative_relative_error": wp02_001_error},
          "complete": wp02_001_complete, "tolerance": 1e-8,
          "authoritative_result": wp02_001_result},
      "wp02_002_mc2": {
          "maximum_relative_error": mc2_error, "metric_errors": mc2_metrics,
          "complete": True, "tolerance": 1e-8},
      "wp02_003": {
          "maximum_relative_error": wp02_003_error,
          "metric_errors": wp02_003_metrics,
          "complete": wp02_003_complete, "tolerance": 1e-8},
      "wp02_004": {
          "maximum_relative_error": wp02_004_error,
          "metric_errors": wp02_004_metrics,
          "complete": wp02_004_complete, "tolerance": 1e-10}}
    predecessor_gates = predecessor_gate_results(predecessor)

    gates = {
      **predecessor_gates,
      "local_constitutive_reference":
          maximum_local_error <= accept["constitutive_relative_error"]
          and local_comparison["allStateBoundsPass"],
      "exact_finite_phi_scalar_flow": scalar_error <= accept["scalar_flow_relative_error"],
      "universal_limit_recovery": all(b<a for a,b in zip(universal,universal[1:])) and universal[-1] <= accept["universal_limit_absolute_error"],
      "source_model_parity": max(source_field_errors,default=0) <= accept["openfoam_flow_relative_error"],
      "source_domain_classification": all((p["basket_pressure_bar"]*1e5 < source_pc)==(p["domain_status"]=="IN_DOMAIN") for p in source_points),
      "openfoam_pressure_profile_reference": max_profile_flow <= accept["openfoam_flow_relative_error"] and max_profile_pressure <= accept["pressure_profile_relative_error"] and max_profile_state <= accept["field_state_relative_error"] and max_height <= accept["field_state_relative_error"],
      "rigid_bed_limit": rigid_error <= accept["rigid_limit_relative_error"],
      "matched_reference_identity": matched_analytical <= accept["matched_identity_relative_error"] and matched_openfoam <= accept["matched_openfoam_relative_error"],
      "machine_operating_point_reference": machine_error <= accept["machine_reference_relative_error"],
      "machine_field_flux_consistency": machine_flux <= accept["machine_field_flux_relative_error"],
      "wetting_isolation": wetting_error <= 1e-8,
      "nonlinear_convergence": nonlinear,
      "timestep_refinement": dt_change <= accept["fine_pair_relative_change"],
      "axial_mesh_refinement": nx_change <= accept["fine_pair_relative_change"],
      "bounded_state": bounded,
      "water_conservation": maximum_water_residual <= 1e-9,
      "solute_conservation": maximum_solute_residual <= 1e-9,
      "fixed_transport_porosity_contract": transport_contract,
      "case_completion": completed}
    all_pass, disposition = adjudicate_gates(gates)
    executable_hash=hashlib.sha256(args.executable.read_bytes()).hexdigest()
    result={"schema_version":"espresso.public.wp03_001.results.v1",
      "run_spec_sha256":hashlib.sha256(spec_path.read_bytes()).hexdigest(),
      "executable_sha256":executable_hash,"cases":cases,
      "production_fixture":fixture,"predecessor_regressions":predecessor,
      "verification":{"scalar_flow_relative_error":scalar_error,
        **local_comparison,
        "universal_limit_errors":universal,"profile_errors":profile_errors,
        "maximum_source_openfoam_flow_error":max(source_field_errors,default=0),
        "rigid_limit_error":rigid_error,"matched_analytical_error":matched_analytical,
        "matched_openfoam_error":matched_openfoam,"machine_reference_error":machine_error,
        "machine_field_mismatch":machine_flux,"wetting_isolation_error_s":wetting_error,
        "timestep_refinement_change":dt_change,"axial_mesh_refinement_change":nx_change,
        "maximumWaterResidual":maximum_water_residual,
        "maximumSoluteResidual":maximum_solute_residual},
      "source_pressure_sweep":source_rows,"gates":gates,
      "all_gates_pass":all_pass,
      "disposition":disposition,
      "claim_boundary":spec["claim_boundary"]}
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    fieldnames=list(combined[0])
    with args.trace_output.open("w",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=fieldnames)
        writer.writeheader(); writer.writerows(combined)
    with args.source_output.open("w",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(source_rows[0]))
        writer.writeheader(); writer.writerows(source_rows)
    print(json.dumps({"all_gates_pass":all_pass,"gates":gates},indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
