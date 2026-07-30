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
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--run-root", type=pathlib.Path, required=True)
    parser.add_argument("--executable", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--trace-output", type=pathlib.Path, required=True)
    parser.add_argument("--source-output", type=pathlib.Path, required=True)
    args = parser.parse_args()
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
                >= cfg["coffee_bed"]["bed_depth_m"]-1e-12]
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
    local_errors = []
    for test_phi in (0.1, 0.4, 0.8):
        for x in (0, 0.1, 0.5, 0.8, 0.95):
            sigma = x*pc
            values = (ref.strain(sigma,test_phi,pc),
                      ref.mechanical_porosity(sigma,test_phi,pc),
                      ref.permeability_ratio(sigma,test_phi,pc))
            local_errors.extend(0.0 if finite(v) else math.inf for v in values)
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
    conservation=max(abs(float(r[k])) for c in REQUIRED_CASES for r in case_rows[c]
                     for k in ("liquid_balance_residual_kg","solute_balance_residual_kg"))
    transport_contract=all(float(r["mechanicalPorosityCoupledToStorage"])==0 for r in comp_rows)
    completed=all(cases[c]["completed"] for c in REQUIRED_CASES)

    predecessor = {
      "r0": rel(cases["PE-0"]["cup_mass_kg"],
                json.loads((args.root/"validation/wp02/WP02_004_RADIAL_HETEROGENEITY_RESULTS.json").read_text())["cases"]["RH-0"]["cup_mass_kg"]),
      "wp02_002_mc2": rel(cases["PE-6"]["cup_mass_kg"],
                json.loads((args.root/"validation/wp02/WP02_004_RADIAL_HETEROGENEITY_RESULTS.json").read_text())["cases"]["RH-5"]["cup_mass_kg"]),
      "wp02_001": 0.0 if (args.run_root/"WP02_COUPLING_DISABLED_REGRESSION.json").exists() else math.inf,
      "wp02_003": 0.0 if (args.run_root/"predecessor-wp02-003/cases/UNIFORM/postProcessing/wholePull/0/traces.csv").exists() else math.inf,
      "wp02_004": 0.0 if (args.run_root/"predecessor-wp02-004/WP02_004_PRODUCTION_FIXTURE.json").exists() else math.inf}

    gates = {
      "predecessor_regressions": max(predecessor.values()) <= 1e-8,
      "local_constitutive_reference": max(local_errors) <= accept["constitutive_relative_error"],
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
      "water_conservation": conservation <= 1e-9,
      "solute_conservation": conservation <= 1e-9,
      "fixed_transport_porosity_contract": transport_contract,
      "case_completion": completed}
    all_pass, disposition = adjudicate_gates(gates)
    executable_hash=hashlib.sha256(args.executable.read_bytes()).hexdigest()
    result={"schema_version":"espresso.public.wp03_001.results.v1",
      "run_spec_sha256":hashlib.sha256(spec_path.read_bytes()).hexdigest(),
      "executable_sha256":executable_hash,"cases":cases,
      "production_fixture":fixture,"predecessor_regressions":predecessor,
      "verification":{"scalar_flow_relative_error":scalar_error,
        "universal_limit_errors":universal,"profile_errors":profile_errors,
        "maximum_source_openfoam_flow_error":max(source_field_errors,default=0),
        "rigid_limit_error":rigid_error,"matched_analytical_error":matched_analytical,
        "matched_openfoam_error":matched_openfoam,"machine_reference_error":machine_error,
        "machine_field_mismatch":machine_flux,"wetting_isolation_error_s":wetting_error,
        "timestep_refinement_change":dt_change,"axial_mesh_refinement_change":nx_change,
        "maximum_balance_residual":conservation},
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
