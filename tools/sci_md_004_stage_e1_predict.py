#!/usr/bin/env python3
"""Execute the audited target-blind SCI-MD-004 Stage E1 prediction matrix."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from sci_md_004_stage_e1_hydraulic import EXECUTABLE_SHA, execute_case, load, sha  # noqa:E402

FREEZE_COMMIT = "51bb5c83010957a760c1cdfc851d3a4def9a16d8"
FREEZE_TREE = "0b2e1c376e64a1ba00d6f062a15fa42e207a7265"
RELATIVE_LIMIT = 0.0075
CONCENTRATION_FLOOR_KG_M3 = 1e-9
MASS_FLOOR_KG = 1e-12


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def canonical_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def aggregate_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\n")
    return digest.hexdigest()


def final_species_rows(case: Path) -> dict[str, dict[str, str]]:
    path = case / "postProcessing/wholePullSpecies/0/species_traces.csv"
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = {}
    for row in rows:
        result[row["species_id"]] = row
    return result


def run(executable: Path, run_root: Path, output: Path) -> None:
    if sha(executable) != EXECUTABLE_SHA:
        raise SystemExit("accepted executable mismatch")
    if run_root.exists() or output.exists():
        raise SystemExit("prediction paths must be fresh")
    run_root.mkdir(parents=True); output.mkdir(parents=True)
    freeze = load(ROOT / "validation/sci_md_004_stage_e1_hydraulic_reconciliation/EXECUTABLE_CASE_FREEZE.json")
    executions, predictions = [], []
    for index, record in enumerate(freeze["scenarios"], 1):
        scenario_path = ROOT / record["scenario_path"]
        if sha(scenario_path) != record["scenario_sha256"]:
            raise SystemExit("audited scenario hash mismatch")
        scenario = load(scenario_path)
        case = run_root / record["configuration_id"]
        final, trace_hash = execute_case(scenario, case, executable)
        species_path = case / "postProcessing/wholePullSpecies/0/species_traces.csv"
        species_hash = sha(species_path)
        species = final_species_rows(case)
        water = float(final["cup_water_mass_kg"])
        if not math.isfinite(water) or water <= 0:
            raise SystemExit("invalid cup water mass")
        observables = {}
        for name in ("caffeine", "trigonelline"):
            row = species[name]
            cup = float(row["cup_solute_mass_kg"])
            initial = float(row["initial_extractable_mass_kg"])
            residual = float(row["solute_balance_residual_kg"])
            observables[name] = {"cup_mass_kg": cup, "concentration_kg_m3": cup / (water / 1000.0),
                                 "initial_inventory_kg": initial,
                                 "remaining_inventory_kg": float(row["remaining_extractable_mass_kg"]),
                                 "dissolved_mass_kg": float(row["dissolved_mass_kg"]),
                                 "back_diffusion_mass_kg": float(row["back_diffusion_mass_kg"]),
                                 "conservation_residual_kg": residual,
                                 "minimum_concentration_kg_m3": float(row["min_concentration_kg_m3"])}
        total_cup = float(final["cup_solute_mass_kg"])
        observables["total_solids"] = {"cup_mass_kg": total_cup,
            "concentration_kg_m3": total_cup / (water / 1000.0),
            "conservation_residual_kg": float(final["solute_balance_residual_kg"])}
        completion = "PASS"
        numeric = [water, *(value for obs in observables.values() for value in obs.values())]
        if (not all(math.isfinite(value) for value in numeric)
                or any(obs["cup_mass_kg"] < 0 or obs["concentration_kg_m3"] < 0 for obs in observables.values())
                or any(abs(observables[name]["conservation_residual_kg"]) > 1e-12 for name in ("caffeine", "trigonelline"))
                or abs(observables["total_solids"]["conservation_residual_kg"]) > 1e-12):
            completion = "FAIL"
        executions.append({"execution_index": index, "configuration_id": record["configuration_id"],
            "scenario_sha256": record["scenario_sha256"], "generated_case_sha256": record["generated_case_sha256"],
            "executable_sha256": EXECUTABLE_SHA, "rank_count": 1, "completion_state": completion,
            "trace_sha256": trace_hash, "species_trace_sha256": species_hash,
            "final_cup_water_mass_kg": water, "observables": observables})
        for observable, values in observables.items():
            predictions.append({"sample_id": record["sample_id"], "hypothesis": record["hypothesis"],
                "resolution": record["resolution"], "observable": observable,
                "concentration_kg_m3": values["concentration_kg_m3"], "cup_mass_kg": values["cup_mass_kg"],
                "cup_water_mass_kg": water, "scenario_sha256": record["scenario_sha256"],
                "generated_case_sha256": record["generated_case_sha256"], "trace_sha256": trace_hash,
                "species_trace_sha256": species_hash})
    if len(executions) != 264 or any(x["completion_state"] != "PASS" for x in executions):
        raise SystemExit("prediction execution failure")
    execution_path = output / "EXECUTION_MANIFEST.json"
    canonical_json(execution_path, {"audited_freeze_commit": FREEZE_COMMIT, "audited_freeze_tree": FREEZE_TREE,
        "execution_count": 264, "rank_count": 1, "worker_count": 1,
        "schedule": "LEXICOGRAPHIC_CONFIGURATION_ID_SERIAL_BOUNDED_DETERMINISTIC",
        "semantic_protected_target_open_count": 0, "executions": executions})
    prediction_rows = sorted(predictions, key=lambda x:(x["sample_id"],x["hypothesis"],x["observable"],x["resolution"]))
    write_csv(output / "PREDICTIONS_ALL_RESOLUTIONS.csv", prediction_rows)
    indexed = {(x["sample_id"],x["hypothesis"],x["observable"],x["resolution"]):x for x in prediction_rows}
    stability, primary = [], []
    for sample in sorted({x["sample_id"] for x in prediction_rows}):
        for hypothesis in ("H0", "H1"):
            for observable in ("caffeine", "trigonelline", "total_solids"):
                ref=indexed[(sample,hypothesis,observable,"reference")]
                fine=indexed[(sample,hypothesis,observable,"fine")]
                for quantity, floor in (("concentration_kg_m3",CONCENTRATION_FLOOR_KG_M3),("cup_mass_kg",MASS_FLOOR_KG)):
                    absolute=abs(float(ref[quantity])-float(fine[quantity]))
                    relative=absolute/abs(float(fine[quantity])) if abs(float(fine[quantity]))>floor else None
                    passed=absolute<=floor if relative is None else relative<=RELATIVE_LIMIT
                    stability.append({"sample_id":sample,"hypothesis":hypothesis,"observable":observable,
                        "quantity":quantity,"reference":ref[quantity],"fine":fine[quantity],
                        "absolute_difference":absolute,"relative_difference":"" if relative is None else relative,
                        "absolute_floor":floor,"relative_limit":RELATIVE_LIMIT,"status":"PASS" if passed else "FAIL"})
                primary.append({"sample_id":sample,"hypothesis":hypothesis,"observable":observable,
                    "prediction_kg_m3":ref["concentration_kg_m3"],"cup_mass_kg":ref["cup_mass_kg"],
                    "cup_water_mass_kg":ref["cup_water_mass_kg"],
                    "reference_scenario_sha256":ref["scenario_sha256"],"fine_scenario_sha256":fine["scenario_sha256"],
                    "reference_trace_sha256":ref["trace_sha256"],"fine_trace_sha256":fine["trace_sha256"]})
    write_csv(output / "NUMERICAL_STABILITY.csv", stability)
    if any(x["status"] != "PASS" for x in stability):
        canonical_json(output / "NUMERICAL_FAILURE.json", {"result":"SCI_MD_004_STAGE_E1_NUMERICAL_APPLICATION_BLOCKED_BEFORE_SCORING",
                       "semantic_protected_target_open_count":0,"failed_gates":[x for x in stability if x["status"]!="PASS"]})
        raise SystemExit("SCI_MD_004_STAGE_E1_NUMERICAL_APPLICATION_BLOCKED_BEFORE_SCORING")
    write_csv(output / "PREDICTIONS.csv", primary)
    adapter=load(ROOT/"validation/sci_md_004_stage_e1_hydraulic_reconciliation/CONDITIONAL_DARCY_ADAPTER.json")
    pairs=[{"condition_id":x["condition_id"],"sample_a":x["sample_ids"][0],"sample_b":x["sample_ids"][1],
            "definition_basis":"INPUT_METADATA_ONLY_NONVARIETY_APPARATUS_KEY"} for x in adapter["conditions"]]
    canonical_json(output/"DIRECTIONAL_PAIR_MANIFEST.json",{"pair_count":33,"target_derived":False,"pairs":pairs})
    artifacts=[execution_path,output/"PREDICTIONS_ALL_RESOLUTIONS.csv",output/"NUMERICAL_STABILITY.csv",
               output/"PREDICTIONS.csv",output/"DIRECTIONAL_PAIR_MANIFEST.json"]
    canonical_json(output/"PREDICTION_MANIFEST.json",{"audited_freeze_commit":FREEZE_COMMIT,"audited_freeze_tree":FREEZE_TREE,
        "prediction_execution_count":264,"primary_prediction_count":396,"numerical_gate_count":792,
        "numerical_gate_status":"PASS","semantic_protected_target_open_count":0,
        "artifact_hashes":{p.name:sha(p) for p in artifacts},"prediction_bundle_sha256":aggregate_hash(artifacts)})


def main():
    p=argparse.ArgumentParser(); p.add_argument("--executable",required=True,type=Path)
    p.add_argument("--run-root",required=True,type=Path); p.add_argument("--output",required=True,type=Path)
    a=p.parse_args(); run(a.executable.resolve(),a.run_root.resolve(),a.output.resolve())


if __name__ == "__main__": main()
