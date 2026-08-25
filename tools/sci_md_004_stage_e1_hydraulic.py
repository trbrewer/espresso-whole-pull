#!/usr/bin/env python3
"""Target-blind SCI-MD-004 Stage E1 conditional-Darcy G1 freeze.

This module accepts only the merged Stage E0 freeze and the Pannusch water
closure source.  It has no protected-target argument, loader, or scorer.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = (
    "SCI-MD-004-STAGE-E1-HYDRAULIC-RECONCILIATION-OWNER-AUTHORIZATION-"
    "CONDITIONAL-EFFECTIVE-DARCY-PERMEABILITY-FREEZE-AND-RESUMED-SINGLE-"
    "PROTECTED-HOLDOUT-EXECUTION-2026-08-25"
)
PROFILE = "EWP_SCI_MD_004_STAGE_E1_G1_HYDRAULIC_ADAPTER_TO_G3_HOLDOUT_V1"
PUCKWORKS_COMMIT = "5ce003e751aac516b5de3d9ede4e6910627e2b12"
PUCKWORKS_TREE = "d50c23028df01d6e1dc0a14ab331d0ea7453cb7f"
SOLVER_SOURCE_SHA = "9ffba0fa7800de50375a2a0c94cf99127870ac4451b104866c7e50322c992599"
EXECUTABLE_SHA = "d793a731fd2f4f82e623350c61835d0e955d886849f5e363a5abd8dd0fae4c93"
POROSITY = {"O": 0.305, "C": 0.330, "F": 0.276}
RESOLUTIONS = {
    "reference": {"axial_cells": 128, "radial_cells": 4, "delta_t_s": 0.05},
    "fine": {"axial_cells": 256, "radial_cells": 4, "delta_t_s": 0.025},
}
CLAIM_CEILING = [
    "THE GENERIC INDEXED SPECIES SOLVER IS SOFTWARE AND NUMERICALLY VERIFIED.",
    "THE CAFFEINE AND TRIGONELLINE PARAMETERS ARE TRAINING-DATA ESTIMATES, NOT UNIVERSAL PHYSICAL CONSTANTS.",
    "THE HYDRAULIC ADAPTER USES CONDITION-SPECIFIC EFFECTIVE PERMEABILITY DERIVED FROM REPORTED PRESSURE, NOMINAL YIELD, DURATION, GEOMETRY, AND WATER PROPERTIES.",
    "THE INFERRED PERMEABILITIES ARE NONPORTABLE NUISANCE INPUTS AND ARE NOT A VALIDATED GRINDER-TO-PERMEABILITY MODEL.",
    "THE ANGELONI COMPARISON IS CONDITIONAL ON MEASURED INITIAL INVENTORIES AND NONCHEMICAL APPARATUS INPUTS.",
    "THE RESULT DOES NOT VALIDATE MACHINE HYDRAULICS, PERMEABILITY, INTERNAL TRANSIENT FIELDS, THERMAL CHEMISTRY, LIPID TRANSPORT, TASTE, OR UNRESTRICTED TRANSFER.",
    "GENERAL PHYSICAL VALIDATION REMAINS NOT_ESTABLISHED.",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def load(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SystemExit(f"expected object: {path}")
    return value


def water_properties_source(puckworks: Path):
    source = puckworks / "models/pannusch2024/closures.py"
    namespace: dict[str, object] = {}
    exec(compile(source.read_bytes(), str(source), "exec"), namespace)
    return namespace["water_viscosity"], namespace["water_density"], sha(source)


def apparatus_key(h: dict) -> tuple:
    return (
        float(h["temperature_K"]), float(h["pressure_Pa"]), h["grind_code"],
        float(h["shot_duration_s"]), float(h["basket_radius_m"]),
        float(h["bed_height_m"]), float(h["beverage_mass_kg"]), float(h["dose_kg"]),
    )


def base_scenario() -> dict:
    return load(ROOT / "config/reference_R0.json")


def scenario(case: dict, condition: dict, hypothesis: str, resolution: str,
             *, zero_inventory: bool = False) -> dict:
    s = copy.deepcopy(base_scenario())
    h = case["hydraulics"]
    k = condition["effective_permeability_m2"]
    phi = condition["porosity"]
    depth = float(h["bed_height_m"])
    radius = float(h["basket_radius_m"])
    mesh = RESOLUTIONS[resolution]
    inventories = case["inventories_kg_per_kg_dry"]
    params = load(ROOT / "validation/sci_md_004_stage_e0/PARAMETERIZATION_AND_IDENTIFIABILITY.json")
    legacy_rate = float(base_scenario()["extraction"]["rate_constant_1_s"])
    legacy_sat = float(base_scenario()["extraction"]["saturation_concentration_kg_m3"])
    legacy_diff = float(base_scenario()["liquid"]["effective_solute_diffusivity_m2_s"])
    species = []
    for name in ("caffeine", "trigonelline"):
        p = params["parameters"][name]
        species.append({
            "id": name, "role": "explicit_inventory",
            "dry_coffee_inventory_mass_fraction": 0.0 if zero_inventory else float(inventories[name]),
            "availability_fraction": 1.0,
            "rate_constant_1_s": legacy_rate if hypothesis == "H0" else float(p["extractionRateConstant_1_s"]),
            "saturation_concentration_kg_m3": legacy_sat if hypothesis == "H0" else float(p["saturationConcentration_kg_m3"]),
            "effective_diffusivity_m2_s": legacy_diff if hypothesis == "H0" else float(p["effectiveSoluteDiffusivity_m2_s"]),
            "parameter_provenance": {
                "inventory": "DIRECT_MEASURED_INPUT", "availability": "FIXED_STRUCTURAL_ASSUMPTION",
                "rate": "FIXED_STRUCTURAL_ASSUMPTION" if hypothesis == "H0" else "TRAINING_DATA_ESTIMATE",
                "saturation": "FIXED_STRUCTURAL_ASSUMPTION" if hypothesis == "H0" else "TRAINING_DATA_ESTIMATE",
                "diffusivity": "FIXED_STRUCTURAL_ASSUMPTION" if hypothesis == "H0" else "PROXY",
            },
        })
    if not zero_inventory:
        species.append({"id": "residual_extractables", "role": "structural_balance", "inherit_legacy_parameters": True})
    else:
        # A zero total extractable fraction makes the two explicit zero inventories close exactly.
        s["coffee_bed"]["initial_extractable_fraction_dry_basis"] = 0.0
    s.update({
        "scenario_id": (f"sci_md_004_e1_hydraulic_{condition['condition_id']}_{resolution}"
                        if zero_inventory else f"sci_md_004_e1_{case['sample_id']}_{hypothesis}_{resolution}"),
        "mode": "validation",
        "pressureBoundaryModel": "prescribedPressure",
        "flowResistanceModel": "darcy",
        "bedMechanicsModel": "none",
        "governance": {"task": "SCI-MD-004-E1-HYDRAULIC", "authorization": AUTHORIZATION,
                       "profile": PROFILE, "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE"},
    })
    s.pop("calibration", None)
    s.pop("effective_permeability_evolution", None)
    s["geometry"].update({"basket_diameter_m": 2 * radius, "basket_radius_m": radius,
                          "axial_cells": mesh["axial_cells"], "radial_cells": mesh["radial_cells"]})
    volume = math.pi * radius * radius * depth
    s["coffee_bed"].update({
        "dry_dose_kg": float(h["dose_kg"]), "initial_porosity": phi, "bed_depth_m": depth,
        "particle_solid_density_kg_m3": float(h["dose_kg"]) / ((1 - phi) * volume),
    })
    s["liquid"].update({"temperature_K": float(h["temperature_K"]),
                        "density_kg_m3": condition["liquid_density_kg_m3"],
                        "dynamic_viscosity_Pa_s": condition["dynamic_viscosity_Pa_s"]})
    s["hydraulics"].update({
        "target_inlet_pressure_gauge_Pa": float(h["pressure_Pa"]),
        "outlet_pressure_gauge_Pa": 0.0, "pressure_ramp_time_s": 0.0,
        "front_pressure_gauge_Pa": 0.0, "saturated_permeability_m2": k,
        "wetting_permeability_m2": k,
        "permeability_profile": {"type": "uniform", "interface_position_m": depth / 2,
                                 "upstream_permeability_m2": k, "downstream_permeability_m2": k,
                                 "interface_radius_m": radius / 2,
                                 "inner_permeability_m2": k, "outer_permeability_m2": k},
    })
    s["wetting"].update({"initial_saturation": 1.0, "initial_wet_front_m": depth})
    s["extraction"] = {
        "model": "indexed_passive_species_first_order_with_capacity_ceiling",
        "legacy_rate_constant_1_s": legacy_rate,
        "legacy_saturation_concentration_kg_m3": legacy_sat,
        "species": species,
    }
    s["time"].update({"start_s": 0.0, "end_s": float(h["shot_duration_s"]),
                      "delta_t_s": mesh["delta_t_s"],
                      "field_write_interval_s": float(h["shot_duration_s"]),
                      "target_beverage_mass_kg": 0.040})
    s["parallel"].update({"default_subdomains": 1, "decomposition_method": "scotch"})
    s["output"].update({"write_format": "ascii", "write_compression": False,
                        "write_precision_digits": 15, "live_stage_logging": False})
    s["claim_ceiling"] = " ".join(CLAIM_CEILING)
    return s


def generated_case_hash(case_dir: Path) -> str:
    # Hash deterministic executable inputs only; environment/timestamp manifests are excluded.
    names = ["CASE_SCENARIO_V0_1_4.json", "system/blockMeshDict", "system/controlDict",
             "system/fvSchemes", "system/fvSolution", "system/decomposeParDict",
             "constant/espressoModelProperties"]
    names += [str(path.relative_to(case_dir)) for path in sorted((case_dir / "0.orig").iterdir())]
    digest = hashlib.sha256()
    for name in sorted(names):
        digest.update(name.encode() + b"\0" + (case_dir / name).read_bytes() + b"\n")
    return digest.hexdigest()


def materialize(s: dict, destination: Path, ranks: int = 1) -> str:
    config = destination.with_suffix(".json")
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_bytes(canonical_bytes(s))
    subprocess.run([sys.executable, str(ROOT / "scripts/prepare_case.py"), "--root", str(ROOT),
                    "--config", str(config), "--nprocs", str(ranks), "--case-dir", str(destination)],
                   check=True, stdout=subprocess.DEVNULL)
    return generated_case_hash(destination)


def freeze(puckworks: Path, output: Path, materialization_root: Path) -> None:
    if subprocess.check_output(["git", "-C", str(puckworks), "rev-parse", "HEAD"], text=True).strip() != PUCKWORKS_COMMIT:
        raise SystemExit("Puckworks commit mismatch")
    if sha(ROOT / "solver/espressoWholePullFoam/espressoWholePullFoam.C") != SOLVER_SOURCE_SHA:
        raise SystemExit("production solver source mismatch")
    viscosity, density, closure_sha = water_properties_source(puckworks)
    frozen = load(ROOT / "validation/sci_md_004_stage_e0/CONDITIONAL_CASE_FREEZE.json")
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for case in frozen["cases"]:
        groups[apparatus_key(case["hydraulics"])].append(case)
    if len(groups) != 33 or any(sorted(x["variety"] for x in pair) != ["Arabica", "Robusta"] for pair in groups.values()):
        raise SystemExit("SCI_MD_004_STAGE_E1_HYDRAULIC_INPUT_PAIRING_BLOCKED")
    conditions, by_key = [], {}
    for index, (key, pair) in enumerate(sorted(groups.items()), 1):
        h = pair[0]["hydraulics"]
        T, pressure, grind, duration, radius, depth, beverage, dose = key
        if not 353.15 <= T <= 371.15:
            raise SystemExit("temperature outside Pannusch 80-98 C closure range")
        mu, rho = float(viscosity(T)), float(density(T))
        k = mu * depth * beverage / (rho * math.pi * radius**2 * pressure * duration)
        if not math.isfinite(k) or k <= 0:
            raise SystemExit("invalid conditional permeability")
        item = {
            "condition_id": f"C{index:02d}", "apparatus_key": list(key),
            "sample_ids": sorted(x["sample_id"] for x in pair), "varieties": ["Arabica", "Robusta"],
            "dynamic_viscosity_Pa_s": mu, "liquid_density_kg_m3": rho,
            "porosity": POROSITY[grind], "effective_permeability_m2": k,
            "permeability_provenance": "NONPORTABLE_CONDITIONAL_EFFECTIVE_PERMEABILITY",
            "porosity_provenance": "LITERATURE_CONSTRAINED_NOMINAL_SOURCE_POROSITY",
            "water_property_provenance": "LITERATURE_CONSTRAINED_CONSTITUTIVE_CLOSURE",
        }
        conditions.append(item); by_key[key] = item
    adapter = {
        "schema_version": "ewp.sci-md-004-stage-e1-conditional-darcy-adapter/v1",
        "authorization": AUTHORIZATION, "profile": PROFILE,
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "protocol": "POST_WETTING_SATURATED_CONDITIONAL_EXTRACTION",
        "target_beverage_mass_role": "DIAGNOSTIC_ONLY_NOT_BOUNDARY_CONDITION",
        "beverage_observation_density_kg_m3": 1000.0,
        "pannusch_water_closure_sha256": closure_sha,
        "porosity_by_grind": POROSITY, "conditions": conditions,
        "claim_ceiling": CLAIM_CEILING,
    }
    write_json(output / "CONDITIONAL_DARCY_ADAPTER.json", adapter)
    scenarios, first_hashes = [], []
    for case in frozen["cases"]:
        c = by_key[apparatus_key(case["hydraulics"])]
        for config in case["configurations"]:
            s = scenario(case, c, config["hypothesis"], config["resolution"])
            scenario_path = output / "scenarios" / f"{config['configuration_id']}.json"
            write_json(scenario_path, s)
            dest = materialization_root / "first" / config["configuration_id"]
            generated = materialize(s, dest)
            record = {"configuration_id": config["configuration_id"], "sample_id": case["sample_id"],
                      "hypothesis": config["hypothesis"], "resolution": config["resolution"],
                      "condition_id": c["condition_id"], "scenario_path": str(scenario_path.relative_to(ROOT)),
                      "scenario_sha256": sha(scenario_path), "generated_case_sha256": generated}
            scenarios.append(record); first_hashes.append(generated)
    # Fresh second generation proves deterministic executable inputs.
    second_hashes = []
    for record in scenarios:
        s = load(ROOT / record["scenario_path"])
        second_hashes.append(materialize(s, materialization_root / "second" / record["configuration_id"]))
    if first_hashes != second_hashes or len(scenarios) != 264:
        raise SystemExit("SCI_MD_004_STAGE_E1_EXECUTABLE_CASE_FREEZE_BLOCKED")
    write_json(output / "EXECUTABLE_CASE_FREEZE.json", {"schema_version": "ewp.sci-md-004-stage-e1-executable-freeze/v1",
               "scenario_count": 264, "target_open_count": 0, "species_prediction_count": 0,
               "scenarios": scenarios})
    write_json(output / "EXECUTABLE_CASE_MANIFEST.json", {"scenario_count": 264,
               "scenario_hashes": {x["configuration_id"]: x["scenario_sha256"] for x in scenarios},
               "generated_case_hashes": {x["configuration_id"]: x["generated_case_sha256"] for x in scenarios},
               "byte_identical_regeneration": True})
    manifest = {"schema_version": "ewp.sci-md-004-stage-e1-g1-freeze/v1",
                "authorization": AUTHORIZATION, "profile": PROFILE, "target_open_count": 0,
                "production_solver_sha256": SOLVER_SOURCE_SHA, "accepted_executable_sha256": EXECUTABLE_SHA,
                "puckworks_commit": PUCKWORKS_COMMIT, "puckworks_tree": PUCKWORKS_TREE,
                "condition_count": 33, "hydraulic_qualification_run_count": 0,
                "executable_scenario_count": 264,
                "artifact_hashes": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}}
    write_json(output / "G1_FREEZE_MANIFEST.json", manifest)


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def execute_case(s: dict, run_dir: Path, executable: Path) -> tuple[dict, str]:
    materialize(s, run_dir)
    subprocess.run(["blockMesh", "-case", str(run_dir)], check=True,
                   stdout=(run_dir / "blockMesh.log").open("w"), stderr=subprocess.STDOUT)
    for function_name in ("writeCellCentres", "writeCellVolumes"):
        subprocess.run(["postProcess", "-case", str(run_dir), "-func", function_name, "-time", "0"],
                       check=True, stdout=(run_dir / f"{function_name}.log").open("w"),
                       stderr=subprocess.STDOUT)
    environment = dict(__import__("os").environ, ESPRESSO_CASE_ROOT=str(run_dir))
    with (run_dir / "solver.log").open("w") as log:
        subprocess.run([str(executable), "-case", str(run_dir)], check=True,
                       env=environment, stdout=log, stderr=subprocess.STDOUT)
    trace = run_dir / "postProcessing/wholePull/0/traces.csv"
    rows = csv_rows(trace)
    if not rows:
        raise SystemExit("empty hydraulic trace")
    return rows[-1], sha(trace)


def qualify(output: Path, run_root: Path, executable: Path) -> None:
    if sha(executable) != EXECUTABLE_SHA:
        raise SystemExit("accepted executable mismatch")
    adapter = load(output / "CONDITIONAL_DARCY_ADAPTER.json")
    frozen = load(ROOT / "validation/sci_md_004_stage_e0/CONDITIONAL_CASE_FREEZE.json")
    cases = {case["sample_id"]: case for case in frozen["cases"]}
    results = []
    for condition in adapter["conditions"]:
        representative = cases[condition["sample_ids"][0]]
        for resolution in RESOLUTIONS:
            name = f"{condition['condition_id']}-{resolution}"
            s = scenario(representative, condition, "H0", resolution, zero_inventory=True)
            final, trace_hash = execute_case(s, run_root / name, executable)
            expected_q = (condition["effective_permeability_m2"] * math.pi
                          * representative["hydraulics"]["basket_radius_m"]**2
                          * representative["hydraulics"]["pressure_Pa"]
                          / (condition["dynamic_viscosity_Pa_s"]
                             * representative["hydraulics"]["bed_height_m"]))
            q = float(final["outlet_flow_m3_s"])
            mass = float(final["cup_water_mass_kg"])
            rel = abs(q - expected_q) / expected_q
            results.append({
                "condition_id": condition["condition_id"], "resolution": resolution,
                "sample_ids": ";".join(condition["sample_ids"]),
                "effective_permeability_m2": condition["effective_permeability_m2"],
                "analytical_flow_m3_s": expected_q, "production_flow_m3_s": q,
                "flow_relative_error": rel, "beverage_mass_kg": mass,
                "beverage_mass_absolute_error_kg": abs(mass - 0.04),
                "minimum_saturation": float(final["min_saturation"]),
                "maximum_saturation": float(final["max_saturation"]),
                "liquid_mass_balance_residual_kg": float(final["liquid_balance_residual_kg"]),
                "trace_sha256": trace_hash,
                "status": "PASS" if (rel <= 1e-8 and abs(mass - 0.04) <= 1e-4
                                        and float(final["min_saturation"]) >= 1.0 - 1e-12
                                        and q >= 0 and all(math.isfinite(v) for v in
                                            (q, mass, float(final["min_saturation"]),
                                             float(final["max_saturation"]),
                                             float(final["liquid_balance_residual_kg"])))) else "FAIL",
            })
    by_condition: dict[str, list[dict]] = defaultdict(list)
    for row in results:
        by_condition[row["condition_id"]].append(row)
    for pair in by_condition.values():
        ref, fine = sorted(pair, key=lambda x: x["resolution"], reverse=True)
        difference = abs(ref["beverage_mass_kg"] - fine["beverage_mass_kg"]) / fine["beverage_mass_kg"]
        for row in pair:
            row["reference_fine_beverage_mass_relative"] = difference
            if difference > 0.0025:
                row["status"] = "FAIL"
    fields = list(results[0])
    with (output / "HYDRAULIC_QUALIFICATION.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(results)
    if len(results) != 66 or any(row["status"] != "PASS" for row in results):
        raise SystemExit("SCI_MD_004_STAGE_E1_CONDITIONAL_DARCY_ADAPTER_BLOCKED")
    manifest_path = output / "G1_FREEZE_MANIFEST.json"
    manifest = load(manifest_path)
    manifest["hydraulic_qualification_run_count"] = 66
    manifest["hydraulic_qualification_sha256"] = sha(output / "HYDRAULIC_QUALIFICATION.csv")
    manifest["all_hydraulic_qualification_runs_pass"] = True
    manifest["artifact_hashes"] = {p.name: sha(p) for p in sorted(output.iterdir())
                                   if p.is_file() and p != manifest_path}
    write_json(manifest_path, manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("freeze", "qualify"))
    parser.add_argument("--puckworks", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--materialization-root", required=True, type=Path)
    parser.add_argument("--executable", type=Path)
    args = parser.parse_args()
    if args.output.resolve() != (ROOT / "validation/sci_md_004_stage_e1_hydraulic_reconciliation").resolve():
        raise SystemExit("output must be the additive governed directory")
    if args.action == "freeze":
        if args.output.exists() or args.materialization_root.exists():
            raise SystemExit("refusing existing output")
        freeze(args.puckworks.resolve(), args.output.resolve(), args.materialization_root.resolve())
    else:
        if not args.output.exists() or args.materialization_root.exists() or args.executable is None:
            raise SystemExit("qualification requires existing freeze, fresh run root, and executable")
        qualify(args.output.resolve(), args.materialization_root.resolve(), args.executable.resolve())


if __name__ == "__main__":
    main()
