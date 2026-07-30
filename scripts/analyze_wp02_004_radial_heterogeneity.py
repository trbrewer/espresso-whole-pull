#!/usr/bin/env python3
"""Fail-closed WP02-004 result adjudication."""

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

import radial_heterogeneity_reference as ref

REQUIRED_GATES = (
    "case_completion", "predecessor_regressions", "equal_zone_identity",
    "darcy_parallel_reference", "forchheimer_parallel_reference",
    "machine_operating_point_reference", "matched_conductance_identity",
    "machine_matched_conductance_identity", "zone_conservation",
    "wetting_isolation", "radial_velocity_bound",
    "machine_field_total_flux_consistency",
    "machine_field_zone_flux_consistency", "timestep_refinement",
    "radial_mesh_refinement", "nonlinear_convergence",
    "finite_bounded_state", "water_conservation", "solute_conservation",
)


def relative(a, b, floor=1e-30):
    return abs(a-b)/max(abs(b), floor)


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def f(row, key):
    return float(row[key])


def timing(path):
    result = {"wall_clock": "", "peak_rss_kb": 0}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("Elapsed (wall clock) time"):
            result["wall_clock"] = line.rsplit(": ", 1)[-1]
        elif line.startswith("Maximum resident set size"):
            result["peak_rss_kb"] = int(line.rsplit(": ", 1)[-1])
    return result


def mean_after(trace, key):
    transition = next((f(r, "time_s") for r in trace
                       if int(r["saturationTransitionStep"])), -1.0)
    values = [f(r, key) for r in trace if f(r, "time_s") > transition]
    return statistics.mean(values)


def summary(root, cid):
    trace = rows(root/"cases"/cid/"postProcessing/wholePull/0/traces.csv")
    last = trace[-1]
    config = json.loads((root/"configs"/f"{cid}.json").read_text())
    depth = float(config["coffee_bed"]["bed_depth_m"])
    saturated = [r for r in trace
                 if f(r, "wet_front_m") >= depth-1e-14
                 and not int(r["saturationTransitionStep"])]
    return {
        "trace": trace, "last": last, "completed": bool(trace),
        "runtime": timing(root/"timing"/f"{cid}.time"),
        "cells": int(config["geometry"]["axial_cells"])*int(config["geometry"]["radial_cells"])*2,
        "dt_s": float(config["time"]["delta_t_s"]),
        "mpi_ranks": 32 if int(config["geometry"]["radial_cells"]) >= 256 else 1,
        "pressure_model": config.get("pressureBoundaryModel","prescribedPressure"),
        "flow_model": config.get("flowResistanceModel","darcy"),
        "permeability_profile": config["hydraulics"].get(
            "permeability_profile",{"type":"uniform"})["type"],
        "first_drip_s": f(last, "first_drip_s"),
        "peak_upstream_pressure_pa": max(f(r,"upstreamPressurePa") for r in trace),
        "peak_basket_pressure_pa": max(f(r,"basketPressurePa") for r in trace
                                       if not int(r["saturationTransitionStep"])),
        "basket_pressure_at_first_drip_pa": next(
            (f(r,"basketPressurePa") for r in trace
             if int(r["saturationTransitionStep"])), 0.0),
        "mean_total_flow_m3_s": mean_after(trace, "outlet_flow_m3_s"),
        "mean_inner_flow_m3_s": mean_after(trace, "innerOutletFlowM3s"),
        "mean_outer_flow_m3_s": mean_after(trace, "outerOutletFlowM3s"),
        "inner_flow_fraction": mean_after(trace, "innerFlowFraction"),
        "outer_flow_fraction": mean_after(trace, "outerFlowFraction"),
        "hydraulic_maldistribution": mean_after(trace, "hydraulicMaldistributionIndex"),
        "effective_hydraulic_area": mean_after(trace, "effectiveHydraulicAreaFraction"),
        "cup_mass_kg": f(last, "cup_beverage_mass_kg"),
        "tds": f(last, "cumulative_tds_mass_fraction"),
        "ey": f(last, "extraction_yield_mass_fraction"),
        "inner_extraction_fraction": f(last, "innerExtractionFraction"),
        "outer_extraction_fraction": f(last, "outerExtractionFraction"),
        "extraction_maldistribution": f(last, "extractionMaldistributionIndex"),
        "inner_focusing_factor": mean_after(trace,"innerFocusingFactor"),
        "outer_focusing_factor": mean_after(trace,"outerFocusingFactor"),
        "inner_cumulative_liquid_m3": f(last,"innerCumulativeLiquidM3"),
        "outer_cumulative_liquid_m3": f(last,"outerCumulativeLiquidM3"),
        "inner_cumulative_solute_kg": f(last,"innerCumulativeSoluteKg"),
        "outer_cumulative_solute_kg": f(last,"outerCumulativeSoluteKg"),
        "inner_initial_extractable_kg": f(last,"innerInitialExtractableKg"),
        "outer_initial_extractable_kg": f(last,"outerInitialExtractableKg"),
        "inner_remaining_extractable_kg": f(last,"innerRemainingExtractableKg"),
        "outer_remaining_extractable_kg": f(last,"outerRemainingExtractableKg"),
        "inner_extracted_solids_kg": f(last,"innerExtractedSolidsKg"),
        "outer_extracted_solids_kg": f(last,"outerExtractedSolidsKg"),
        "inner_retained_liquid_kg": f(last,"innerRetainedLiquidKg"),
        "outer_retained_liquid_kg": f(last,"outerRetainedLiquidKg"),
        "cup_water_mass_kg": f(last,"cup_water_mass_kg"),
        "cup_solute_mass_kg": f(last,"cup_solute_mass_kg"),
        "cumulative_outlet_liquid_m3": f(last,"cumulativePuckOutletM3"),
        "compliance_storage_m3": f(last,"compliantStorageM3"),
        "maximum_pressure_iterations": max(int(r["pressure_iterations"]) for r in trace),
        "maximum_machine_iterations": max(int(r["couplingIterations"]) for r in trace),
        "maximum_forchheimer_iterations": max(int(r["nonlinearIterations"]) for r in trace),
        "water_residual_kg": max(abs(f(r, "liquid_balance_residual_kg")) for r in trace),
        "solute_residual_kg": max(abs(f(r, "solute_balance_residual_kg")) for r in trace),
        "maximum_radial_ratio": max(f(r, "radialToAxialVelocityRatio") for r in trace
                                    if f(r, "outlet_flow_m3_s") > 0),
        "maximum_total_flux_mismatch": max(
            (f(r, "totalFluxRelativeDifference") for r in saturated), default=0.0),
        "maximum_inner_flux_mismatch": max(
            (f(r, "innerFluxRelativeDifference") for r in saturated), default=0.0),
        "maximum_outer_flux_mismatch": max(
            (f(r, "outerFluxRelativeDifference") for r in saturated), default=0.0),
    }


def physical_vector(case):
    return [case[k] for k in (
        "first_drip_s", "mean_total_flow_m3_s", "inner_flow_fraction",
        "outer_flow_fraction", "hydraulic_maldistribution",
        "effective_hydraulic_area", "cup_mass_kg", "tds", "ey",
        "inner_extraction_fraction", "outer_extraction_fraction",
        "extraction_maldistribution")]


def max_pair_change(a, b):
    return max(relative(x, y, 1e-12) for x, y in zip(physical_vector(a),
                                                     physical_vector(b)))


def adjudicate(result):
    x = result["gate_inputs"]
    gates = {
        "case_completion": x["all_cases_complete"],
        "predecessor_regressions": x["predecessor_max_error"] <= .005,
        "equal_zone_identity": x["equal_zone_max_error"] <= 1e-10,
        "darcy_parallel_reference": x["darcy_fixture_max_error"] <= 1e-8,
        "forchheimer_parallel_reference": x["forchheimer_fixture_max_error"] <= 1e-8,
        "machine_operating_point_reference": x["machine_reference_max_error"] <= 1e-10,
        "matched_conductance_identity": x["conductance_identity_error"] <= 1e-12
            and x["matched_total_flow_error"] <= 1e-7 and x["heterogeneous_flow_share_changed"],
        "machine_matched_conductance_identity": x["machine_hydraulic_error"] <= 1e-6,
        "zone_conservation": x["zone_conservation_error"] <= 1e-10,
        "wetting_isolation": x["wetting_isolation_error"] <= 1e-8,
        "radial_velocity_bound": x["maximum_radial_velocity_ratio"] <= 1e-6,
        "machine_field_total_flux_consistency": x["maximum_total_flux_mismatch"] <= 1e-6,
        "machine_field_zone_flux_consistency": x["maximum_zone_flux_mismatch"] <= 1e-6,
        "timestep_refinement": x["timestep_refinement_change"] <= .005,
        "radial_mesh_refinement": x["radial_mesh_refinement_change"] <= .005,
        "nonlinear_convergence": x["failed_nonlinear_steps"] == 0,
        "finite_bounded_state": x["finite_bounded_state"],
        "water_conservation": x["maximum_water_residual_kg"] <= 1e-10,
        "solute_conservation": x["maximum_solute_residual_kg"] <= 1e-10,
    }
    result["gates"] = {k: "PASS" if v else "FAIL" for k, v in gates.items()}
    result["all_gates_pass"] = all(gates[k] for k in REQUIRED_GATES)
    result["disposition"] = ("SOLVER_BEARING_WORK_PACKAGE_COMPLETE_PR_OPEN"
                             if result["all_gates_pass"] else "NUMERICAL_FAILURE")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trace-output", type=Path, required=True)
    parser.add_argument("--predecessor-root", type=Path, required=True)
    parser.add_argument("--coupling-disabled-result", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    cases = {cid: summary(args.run_root, cid) for cid in
             [f"RH-{i}" for i in range(9)]}
    dt = {v: summary(args.run_root, f"RH-6-DT-{v}") for v in ("0.02","0.01","0.005")}
    nr = {v: summary(args.run_root, f"RH-6-NR-{v}") for v in ("256","512","1024")}
    fixture = {cid: summary(args.run_root, cid) for cid in
               ("RADIAL-DARCY","RADIAL-FORCH","MACHINE-RADIAL")}
    production = json.loads((args.run_root/"WP02_004_PRODUCTION_FIXTURE.json").read_text())
    spec = json.loads((args.root/"validation/wp02/WP02_004_RADIAL_HETEROGENEITY_RUN_SPEC.json").read_text())
    k0 = spec["reference"]["reference_permeability_m2"]
    conductance_errors = []
    for name, p in spec["matched_profiles"].items():
        keq = .25*p["inner_permeability_m2"]+.75*p["outer_permeability_m2"]
        conductance_errors.append(relative(keq, k0))
    fd = fixture["RADIAL-DARCY"]["last"]
    ff = fixture["RADIAL-FORCH"]["last"]
    darcy_fixture_error = max(f(fd, "relative_outlet_flow_error"),
                              relative(f(fd,"innerOutletFlowM3s"),
                                       production["darcy_inner_flow_m3_s"]),
                              relative(f(fd,"outerOutletFlowM3s"),
                                       production["darcy_outer_flow_m3_s"]))
    forch_fixture_error = max(f(ff, "relative_outlet_flow_error"),
                              relative(f(ff,"innerOutletFlowM3s"),
                                       production["forchheimer_inner_flow_m3_s"]),
                              relative(f(ff,"outerOutletFlowM3s"),
                                       production["forchheimer_outer_flow_m3_s"]))
    accepted = json.loads((args.root/"validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RESULTS.json").read_text())
    r0 = {"first_drip_s": 4.711696185231869,
          "cup_mass_kg": 0.0409578674833007,
          "tds": 0.116893063885692, "ey": 0.239384531030697}
    predecessor = [relative(cases["RH-0"][k], v, 1e-12) for k,v in r0.items()]
    mc2 = accepted["cases"]["MC-2"]
    predecessor += [relative(cases["RH-5"]["first_drip_s"], mc2["first_drip_s"]),
                    relative(cases["RH-5"]["cup_mass_kg"], mc2["final_cup_mass_kg"]),
                    relative(cases["RH-5"]["tds"], mc2["final_tds_fraction"]),
                    relative(cases["RH-5"]["ey"], mc2["final_extraction_yield_fraction"])]
    predecessor_fixtures = {
        cid: rows(args.predecessor_root/"cases"/cid
                  /"postProcessing/wholePull/0/traces.csv")[-1]
        for cid in ("UNIFORM","LAYERED","MACHINE")
    }
    predecessor += [
        f(row, "relative_outlet_flow_error")
        for row in predecessor_fixtures.values()
    ]
    predecessor += [
        json.loads(args.coupling_disabled_result.read_text())["relative_error"]
    ]
    radial_cases = [cases[f"RH-{i}"] for i in (1,2,3,4,6,7,8)] + list(dt.values()) + list(nr.values())
    zone_error = max(
        max(abs(f(r,"innerOutletFlowM3s")+f(r,"outerOutletFlowM3s")-f(r,"outlet_flow_m3_s"))
            / max(abs(f(r,"outlet_flow_m3_s")),1e-30),
            abs(f(r,"innerCumulativeSoluteKg")+f(r,"outerCumulativeSoluteKg")-f(r,"cup_solute_mass_kg"))
            / max(abs(f(r,"cup_solute_mass_kg")),1e-30))
        for c in radial_cases for r in c["trace"])
    wetting_error = max(abs(f(a,k)-f(b,k)) for cid in ("RH-1","RH-2","RH-3","RH-4")
                        for a,b in zip(cases["RH-0"]["trace"],cases[cid]["trace"])
                        for k in ("wet_front_m","first_drip_s")
                        if f(a,"time_s") <= cases["RH-0"]["first_drip_s"]+.02)
    all_cases = list(cases.values())+list(dt.values())+list(nr.values())+list(fixture.values())
    inputs = {
        "all_cases_complete": all(c["completed"] for c in all_cases),
        "predecessor_max_error": max(predecessor),
        "equal_zone_max_error": max(relative(cases["RH-1"][k],cases["RH-0"][k],1e-12)
                                    for k in ("first_drip_s","mean_total_flow_m3_s","cup_mass_kg","tds","ey")),
        "darcy_fixture_max_error": darcy_fixture_error,
        "forchheimer_fixture_max_error": forch_fixture_error,
        "machine_reference_max_error": production["maximum_identity_relative_error"],
        "conductance_identity_error": max(conductance_errors),
        "matched_total_flow_error": max(relative(cases[c]["mean_total_flow_m3_s"],
                                                 cases["RH-0"]["mean_total_flow_m3_s"])
                                        for c in ("RH-2","RH-3","RH-4")),
        "heterogeneous_flow_share_changed": all(abs(cases[c]["inner_flow_fraction"]-.25)>1e-3
                                                for c in ("RH-2","RH-3","RH-4")),
        "machine_hydraulic_error": max(relative(cases["RH-6"][k],cases["RH-5"][k],1e-12)
                                       for k in ("mean_total_flow_m3_s","first_drip_s")),
        "zone_conservation_error": zone_error,
        "wetting_isolation_error": wetting_error,
        "maximum_radial_velocity_ratio": max(c["maximum_radial_ratio"] for c in radial_cases),
        "maximum_total_flux_mismatch": max(c["maximum_total_flux_mismatch"] for c in radial_cases),
        "maximum_zone_flux_mismatch": max(max(c["maximum_inner_flux_mismatch"],
                                               c["maximum_outer_flux_mismatch"]) for c in radial_cases),
        "timestep_refinement_change": max_pair_change(dt["0.01"],dt["0.005"]),
        "radial_mesh_refinement_change": max_pair_change(nr["512"],nr["1024"]),
        "failed_nonlinear_steps": sum(sum(int(r["nonlinearConverged"])==0
                                             for r in c["trace"]
                                             if r["flowResistanceModel"]=="darcyForchheimer"
                                             and f(r,"outlet_flow_m3_s")>0) for c in all_cases),
        "finite_bounded_state": all(math.isfinite(f(r,k)) for c in all_cases for r in c["trace"]
                                    for k in ("inlet_pressure_Pa","outlet_flow_m3_s",
                                              "innerFlowFraction","outerFlowFraction",
                                              "hydraulicMaldistributionIndex",
                                              "effectiveHydraulicAreaFraction"))
            and all(0<=f(r,"innerFlowFraction")<=1 and 0<=f(r,"outerFlowFraction")<=1
                    and 0<=f(r,"hydraulicMaldistributionIndex")<=1
                    and 0<f(r,"effectiveHydraulicAreaFraction")<=1
                    for c in all_cases for r in c["trace"]),
        "maximum_water_residual_kg": max(c["water_residual_kg"] for c in all_cases),
        "maximum_solute_residual_kg": max(c["solute_residual_kg"] for c in all_cases),
    }
    clean_cases = {k:{kk:vv for kk,vv in v.items() if kk not in ("trace","last")}
                   for k,v in cases.items()}
    result = adjudicate({"schema_version":"espresso.public.wp02_004.results.v1",
        "run_spec_sha256": hashlib.sha256((args.root/"validation/wp02/WP02_004_RADIAL_HETEROGENEITY_RUN_SPEC.json").read_bytes()).hexdigest(),
        "gate_inputs":inputs, "cases":clean_cases,
        "timestep_refinement":{k:{kk:vv for kk,vv in v.items() if kk not in ("trace","last")} for k,v in dt.items()},
        "radial_mesh_refinement":{k:{kk:vv for kk,vv in v.items() if kk not in ("trace","last")} for k,v in nr.items()},
        "production_fixture":production})
    if args.executable.is_file():
        result["executable_sha256"] = hashlib.sha256(
            args.executable.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    with args.trace_output.open("w",newline="") as stream:
        writer=csv.DictWriter(
            stream, fieldnames=cases["RH-0"]["trace"][0].keys(),
            lineterminator="\n"
        )
        writer.writeheader()
        for cid,c in cases.items():
            for row in c["trace"][::5]:
                writer.writerow(row)
    print(json.dumps({"disposition":result["disposition"],"gates":result["gates"]},indent=2))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
