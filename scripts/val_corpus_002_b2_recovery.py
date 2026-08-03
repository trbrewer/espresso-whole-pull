#!/usr/bin/env python3
"""Closed Stage-B2 materialization recovery, cache verification and execution."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import val_corpus_002_b0_tooling as b0
import val_corpus_002_b1_calibration as b1
import val_corpus_002_b2 as b2


RECOVERY_SOURCE_HEAD = "8979d8b4b4bea5d119695e4685556f9d2909da61"
ORIGINAL_PARTIAL_AGGREGATE = "db510fb5b0431152b39a7513d99cf2604702573948fe3f2f3d326bb4bfade999"
ORIGINAL_PRODUCTION_AGGREGATE = "21e16604072de4b4b5e86561f41b0fd5a28c1c4c486b1e4964b6ef8844279c47"
ORIGINAL_WASZ_P2_HASH = "7e7a8977cc45641c6e22b90922a5b370e9e0e81179ad0e1022c371c863c79dbc"
WASZ_P2_ID = "WASZ_9_COMPACT_P2_FIXED_AFTER_EXP7_CALIBRATION_CHEMISTRY"
TARGET_FAILURE = "REQUIRED_TARGET_BEVERAGE_MASS_NOT_REACHED_NO_EXTRAPOLATION"


def _dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def configuration_maps(repo: Path, b1_root: Path) -> tuple[dict[str, dict], dict]:
    _, materialized = b2.verify_b1(repo, b1_root)
    inventory = b0.build_configuration_inventory(repo)
    configs = {row["id"]: row["configuration"] for row in inventory["numeric_configurations"]}
    configs.update(materialized["configurations"])
    hashes = {key: b0.canonical_sha256(value) for key, value in configs.items()}
    return configs, hashes


def corrected_inventory(repo: Path, b1_root: Path, old_path: Path) -> dict:
    old = json.loads(old_path.read_text())
    configs, hashes = configuration_maps(repo, b1_root)
    old_hashes = {**old["numeric_configuration_sha256"],
                  **old["materialized_p2_configuration_sha256"]}
    changed = sorted(key for key in hashes if hashes[key] != old_hashes[key])
    if changed != [WASZ_P2_ID]:
        raise ValueError(f"correction changed members outside Waszkiewicz P2: {changed}")
    if old_hashes[WASZ_P2_ID] != ORIGINAL_WASZ_P2_HASH:
        raise ValueError("superseded Waszkiewicz P2 identity mismatch")
    digest = hashlib.sha256()
    for key in sorted(hashes):
        digest.update(f"{key}\0{hashes[key]}\n".encode())
    value = {
        "schema_version": "espresso.val_corpus_002.b2_corrected_configuration_inventory.v1",
        "authorization_id": b2.AUTHORIZATION_ID,
        "fixed_rate_s_inverse": b2.RATE, "fixed_rate_hex": b2.RATE_HEX,
        "supersedes_inventory_sha256": b0.file_sha256(old_path),
        "superseded_production_aggregate_sha256": ORIGINAL_PRODUCTION_AGGREGATE,
        "corrected_production_aggregate_sha256": digest.hexdigest(),
        "superseded_waszkiewicz_p2_sha256": ORIGINAL_WASZ_P2_HASH,
        "corrected_waszkiewicz_p2_sha256": hashes[WASZ_P2_ID],
        "unchanged_numeric_count": 30, "unchanged_schmieder_p2_count": 14,
        "changed_configuration_ids": changed,
        "numeric_configuration_sha256": {key: hashes[key] for key in old["numeric_configuration_sha256"]},
        "materialized_p2_configuration_sha256": {
            key: hashes[key] for key in old["materialized_p2_configuration_sha256"]},
        "waszkiewicz_p2_rate_is_scalar": type(configs[WASZ_P2_ID]["extraction"]["rate_constant_1_s"]) is float,
        "historical_inventory": "RETAINED_IMMUTABLE",
    }
    if configs[WASZ_P2_ID]["extraction"]["rate_constant_1_s"].hex() != b2.RATE_HEX:
        raise ValueError("corrected Waszkiewicz rate identity mismatch")
    return value


def preflight_all_p2(repo: Path, b1_root: Path, output_root: Path) -> dict:
    configs, _ = configuration_maps(repo, b1_root)
    p2_ids = sorted(key for key in configs if "_P2_FIXED_" in key)
    if len(p2_ids) != 15:
        raise ValueError("exact 15-member P2 preflight required")
    output_root.mkdir(parents=True, exist_ok=False)
    rows = []
    for run_id in p2_ids:
        config = configs[run_id]
        rate_path = (config["chemistry"]["extractionRateConstant_s_inverse"]
                     if run_id.startswith("SCHM_") else config["extraction"]["rate_constant_1_s"])
        if type(rate_path) is not float or rate_path.hex() != b2.RATE_HEX:
            raise ValueError(f"non-scalar or wrong P2 rate: {run_id}")
        scenario = b2.solver_scenario(repo, config)
        member = output_root / run_id
        scenario_path = member / "solver-scenario.json"
        b2._dump(scenario_path, scenario, canonical=True)
        case = member / "temporary-case"
        subprocess.run([sys.executable, str(repo / "scripts/prepare_case.py"), "--root", str(repo),
                        "--config", str(scenario_path), "--case-dir", str(case), "--nprocs", "16"],
                       check=True, stdout=subprocess.DEVNULL)
        properties = case / "constant/espressoModelProperties"
        line = next(line.strip() for line in properties.read_text().splitlines()
                    if line.strip().startswith("extractionRateConstant"))
        if line != "extractionRateConstant     0.3439597024835067;":
            raise ValueError(f"generated scalar extraction rate mismatch: {run_id}")
        manifest = case / "ESPRESSO_WHOLE_PULL_CASE_CASE_MANIFEST_V0_1_4.json"
        rows.append({"run_id": run_id, "configuration_sha256": b0.canonical_sha256(config),
                     "scenario_sha256": b0.file_sha256(scenario_path),
                     "prepare_case": "PASS", "extraction_rate_type": "SCALAR",
                     "extraction_rate_s_inverse": rate_path,
                     "case_manifest_sha256": b0.file_sha256(manifest)})
        shutil.rmtree(case)
    digest = hashlib.sha256()
    for row in rows:
        digest.update(b0.canonical_bytes(row))
    result = {"schema_version": "espresso.val_corpus_002.b2_p2_prepare_preflight.v1",
              "status": "PASS", "configuration_count": len(rows),
              "solver_launch_count": 0, "protected_source_access": False,
              "aggregate_sha256": digest.hexdigest(), "configurations": rows}
    _dump(output_root / "P2_PREPARE_CASE_PREFLIGHT.json", result)
    return result


def _record_location(original_root: Path, run_id: str) -> tuple[Path, Path, Path]:
    reuse = original_root / "reuses" / run_id
    if (reuse / "execution-record.json").is_file():
        return reuse, reuse / "production-configuration.json", reuse / "retained-model-output-trace.csv"
    for attempt in (2, 1):
        base = original_root / "executions" / run_id / f"attempt-{attempt}"
        if (base / "execution-record.json").is_file():
            return base, base / "production-configuration.json", base / "case/postProcessing/wholePull/0/traces.csv"
    raise ValueError(f"terminal record missing: {run_id}")


def verify_partial_cache(repo: Path, b1_root: Path, original_root: Path) -> dict:
    configs, hashes = configuration_maps(repo, b1_root)
    ids = sorted(set(configs) - {WASZ_P2_ID})
    if len(ids) != 44:
        raise ValueError("exact 44-identity recovery cache required")
    rows, typed = [], []
    for run_id in ids:
        base, config_path, trace_path = _record_location(original_root, run_id)
        record_path = base / "execution-record.json"
        record = json.loads(record_path.read_text())
        if record.get("run_id") != run_id:
            raise ValueError(f"cache run identity mismatch: {run_id}")
        if b0.file_sha256(config_path) != hashes[run_id] or not trace_path.is_file():
            raise ValueError(f"cache content missing or changed: {run_id}")
        trace_sha, trace_bytes = b0.file_sha256(trace_path), trace_path.stat().st_size
        if record["status"] == "PASS" and (record.get("configuration_sha256") != hashes[run_id]
                or record.get("trace_sha256") != trace_sha or record.get("trace_bytes") != trace_bytes
                or record.get("solver_commit") != b2.SOLVER_COMMIT
                or record.get("executable_sha256") != b2.EXECUTABLE_SHA256
                or record.get("solver_exit_code") != 0):
            raise ValueError(f"passing cache binding mismatch: {run_id}")
        trace = b1._trace_rows(trace_path)
        expected_end = 63.0 if run_id.startswith("WASZ_") else 90.0
        if abs(trace[-1]["time_s"] - expected_end) > 1e-9:
            raise ValueError(f"cache terminal time mismatch: {run_id}")
        if record["status"] == "PASS":
            if run_id.startswith("SCHM_"):
                model, gates = b1.reduce_evaluation(trace, configs[run_id])
                if model != record["model_cup_solute_masses_g"] or gates != record["numerical_gates"]:
                    raise ValueError(f"cache reduction mismatch: {run_id}")
            elif run_id == "WASZ_9_COMPACT_P0_CHEMISTRY":
                reference = Path("/home/tim/espresso-development/.wp03-002-exact-head-review") / b2.REFERENCE_TRACE
                parity = b0.compare_bound_predecessor_parity(reference, b0._read_parity_csv(trace_path))
                if parity["status"] != "PASS" or parity["compared_reference_states"] != 1500:
                    raise ValueError("cached predecessor parity mismatch")
        elif record["status"] == "TYPED_NUMERICAL_CASE_FAILURE":
            solver_log = base / "log.solver"
            log_text = solver_log.read_text(errors="replace")
            if (record.get("failure_reason") != TARGET_FAILURE or record.get("objective") is not None
                    or not run_id.startswith("SCHM_") or log_text.count("\nEnd\n") != 1
                    or "FOAM FATAL" in log_text or "Floating point exception" in log_text):
                raise ValueError(f"typed cache disposition mismatch: {run_id}")
            try:
                b1.reduce_evaluation(trace, configs[run_id])
            except ValueError as exc:
                if str(exc) != "fixed-mass extrapolation is prohibited":
                    raise
            else:
                raise ValueError(f"typed target failure no longer reconstructs: {run_id}")
            typed.append(run_id)
        else:
            raise ValueError(f"nonterminal status in recovery cache: {run_id}")
        rows.append({"run_id": run_id, "status": record["status"],
                     "record_sha256": b0.file_sha256(record_path),
                     "configuration_sha256": hashes[run_id],
                     "trace_sha256": trace_sha, "trace_bytes": trace_bytes})
    if len(typed) != 18 or sum(row["status"] == "PASS" for row in rows) != 26:
        raise ValueError("partial cache disposition counts mismatch")
    digest = hashlib.sha256()
    for row in rows:
        digest.update(b0.canonical_bytes(row))
    return {"schema_version": "espresso.val_corpus_002.b2_partial_matrix_cache.v1",
            "status": "PASS", "identity_count": 44, "passing_count": 26,
            "typed_failure_count": 18, "typed_failure_identities": typed,
            "aggregate_sha256": digest.hexdigest(), "identities": rows,
            "original_partial_aggregate_sha256": ORIGINAL_PARTIAL_AGGREGATE}


def _source_summaries(repo: Path) -> tuple[dict[int, list[dict]], dict[str, int]]:
    cohort = json.loads((repo / "validation/cases/val_corpus_002/VAL_CORPUS_002_COHORT_SELECTION.json").read_text())
    summaries: dict[int, list[dict]] = {}
    for row in cohort["summaries"]:
        summaries.setdefault(int(row["experiment"]), []).append(row)
    for rows in summaries.values():
        rows.sort(key=lambda row: row["target_beverage_mass_g"])
    roles = {}
    for row in cohort["axis_transfer_records"]:
        roles[row["axis_role"]] = int(row["experiment"])
    return summaries, roles


def _trace_for(original_root: Path, recovery_root: Path, run_id: str) -> Path:
    if run_id == WASZ_P2_ID:
        return recovery_root / "executions" / run_id / "attempt-1/case/postProcessing/wholePull/0/traces.csv"
    return _record_location(original_root, run_id)[2]


def frozen_results(repo: Path, b1_root: Path, original_root: Path,
                   recovery_root: Path, puckworks_root: Path) -> dict:
    configs, hashes = configuration_maps(repo, b1_root)
    cache = verify_partial_cache(repo, b1_root, original_root)
    summaries, axis_roles = _source_summaries(repo)
    cache_by_id = {row["run_id"]: row for row in cache["identities"]}
    availability, schmieder = [], {}
    model_by_key: dict[tuple[int, str, str], list[float]] = {}
    for run_id in sorted(name for name in configs if name.startswith("SCHM_")):
        record = json.loads((_record_location(original_root, run_id)[0] / "execution-record.json").read_text())
        exp = int(run_id.split("_")[1][3:]); parameter = run_id.split("_")[2]
        mode = run_id.rsplit("_", 1)[1]
        row = {"run_id": run_id, "status": record["status"],
               "target_availability": {"20_g": False, "40_g": False, "60_g": False}}
        if record["status"] == "PASS":
            model = record["model_cup_solute_masses_g"]
            source_rows = summaries[exp]
            source = [item["replicate_mean_tds_mass_g"] for item in source_rows]
            # Reconstruct source replicate triplets from the frozen range-bearing cohort.
            source_csv = puckworks_root / "puckworks/data/schmieder2023/cup_masses.csv"
            replicates = [[] for _ in range(3)]
            with source_csv.open(newline="") as handle:
                for item in csv.DictReader(handle):
                    if int(float(item["exp"])) == exp and item["component"] == "TDS":
                        index = {"1/1": 0, "1/2": 1, "1/3": 2}[item["brew_ratio"]]
                        replicates[index].append(float(item["mass_in_cup"]))
            reduction = b0.schmieder_three_mass_reduction(source, model, replicates)
            reduction["target_metrics"] = [{
                "target_mass_g": target,
                "source_cup_solute_mass_g": source[index],
                "model_cup_solute_mass_g": model[index],
                "model_tds_fraction": model[index] / target,
                "model_extraction_yield": model[index] / 20.0,
                "signed_residual_g": model[index] - source[index],
                "relative_residual": (model[index] - source[index]) / source[index],
                "standardized_residual": reduction["metrics"]["standardized_residual"][index],
            } for index, target in enumerate((20.0, 40.0, 60.0))]
            schmieder[run_id] = reduction
            model_by_key[(exp, parameter, mode)] = model
            row["target_availability"] = {"20_g": True, "40_g": True, "60_g": True}
        else:
            row["unavailable_disposition"] = "UNAVAILABLE_TYPED_TARGET_COVERAGE_FAILURE"
        availability.append(row)

    paired = {}
    for exp in range(1, 8):
        for parameter in ("P0", "P1", "P2"):
            left, right = model_by_key.get((exp, parameter, "H0")), model_by_key.get((exp, parameter, "H1"))
            key = f"EXP{exp}_{parameter}"
            if left is None or right is None:
                paired[key] = {"status": "UNAVAILABLE_TYPED_TARGET_COVERAGE_FAILURE"}
            else:
                source = [row["replicate_mean_tds_mass_g"] for row in summaries[exp]]
                h0 = b0.production_metrics(source, left, [None] * 3)["rmse"]
                h1 = b0.production_metrics(source, right, [None] * 3)["rmse"]
                paired[key] = b0.paired_error_ratio(h0, h1)

    role_map = {"LOW_FLOW": axis_roles["LOW_FLOW_AXIS"], "HIGH_FLOW": axis_roles["HIGH_FLOW_AXIS"],
                "FINE_GRIND": axis_roles["FINE_GRIND_SETTING_AXIS"],
                "COARSE_GRIND": axis_roles["COARSE_GRIND_SETTING_AXIS"],
                "LOW_TEMPERATURE": axis_roles["LOW_TEMPERATURE_AXIS"],
                "HIGH_TEMPERATURE": axis_roles["HIGH_TEMPERATURE_AXIS"]}
    axis = {}
    source_cases = {name: [row["replicate_mean_tds_mass_g"] for row in summaries[exp]]
                    for name, exp in role_map.items()}
    source_contrasts = b0.all_axis_contrasts(source_cases)
    for parameter in ("P0", "P1", "P2"):
        for mode in ("H0", "H1"):
            key = f"{parameter}_{mode}"
            cases = {name: model_by_key.get((exp, parameter, mode)) for name, exp in role_map.items()}
            if any(value is None for value in cases.values()):
                axis[key] = {"status": "UNAVAILABLE_TYPED_TARGET_COVERAGE_FAILURE"}
            else:
                model_contrasts = b0.all_axis_contrasts(cases)  # type: ignore[arg-type]
                axis[key] = {name: {ratio: {"source": source_contrasts[name][ratio],
                                             "model": model_contrasts[name][ratio],
                                             "magnitude_error": abs(model_contrasts[name][ratio]) - abs(source_contrasts[name][ratio]),
                                             "source_sign": math.copysign(1, source_contrasts[name][ratio]) if source_contrasts[name][ratio] else 0,
                                             "model_sign": math.copysign(1, model_contrasts[name][ratio]) if model_contrasts[name][ratio] else 0}
                                     for ratio in source_contrasts[name]}
                             for name in source_contrasts}

    wasz_source_path = puckworks_root / "puckworks/data/waszkiewicz2025/tds_fractions.csv"
    with wasz_source_path.open(newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    source_tds = [float(row["tds__percent"]) / 100.0 for row in source_rows]
    uncertainty = [None if not row["tds_std__percent"] else float(row["tds_std__percent"]) / 100.0 for row in source_rows]
    cohort = json.loads((repo / "validation/cases/val_corpus_002/VAL_CORPUS_002_WASZKIEWICZ_COHORT.json").read_text())
    windows = {"early": list(range(0, 4)), "middle": list(range(4, 8)), "late": list(range(8, 12))}
    wasz = {}
    for parameter, run_id in (("P0", "WASZ_9_COMPACT_P0_CHEMISTRY"),
                              ("P1", "WASZ_9_COMPACT_P1_CHEMISTRY"),
                              ("P2", WASZ_P2_ID)):
        trace_path = _trace_for(original_root, recovery_root, run_id)
        with trace_path.open(newline="") as handle:
            raw = [{key: float(row[key]) for key in ("time_s", "outlet_flow_m3_s", "totalSoluteFluxKgS")}
                   for row in csv.DictReader(handle)]
        density = float(configs[run_id]["liquid"]["density_kg_m3"])
        presentations = {}
        for presentation in cohort["clock_mapping"]["presentations"]:
            values = [b0.interval_chemistry_raw(raw, density, start, end,
                       initial={"simulation_start_time_s": 0.0, "initial_cup_water_kg": 0.0,
                                "initial_cup_solute_kg": 0.0, "initial_outlet_flow_m3_s": 0.0,
                                "initial_solute_flux_kg_s": 0.0})
                      for start, end in presentation["model_intervals_s"]]
            presentations[presentation["id"]] = {"model_interval_tds_fraction": values,
                "metrics": b0.waszkiewicz_series_metrics(source_tds, values, windows, uncertainty)}
        wasz[parameter] = presentations

    sensitivity_result = json.loads((recovery_root / "runtime/SENSITIVITY_RECOVERY_RESULT.json").read_text())
    sens_inventory = json.loads((repo / "validation/cases/val_corpus_002/VAL_CORPUS_002_SENSITIVITY_MATRIX.json").read_text())
    outputs = {row["run_id"]: row.get("model_cup_solute_masses_g") for row in sensitivity_result["records"]}
    outputs["SENS_BASELINE"] = model_by_key[(7, "P1", "H1")]
    parameter_cases = {}
    nonbaseline = [row for row in sens_inventory["future_runs"] if row["run_id"] != "SENS_BASELINE"]
    for parameter in sorted({row["parameter"] for row in nonbaseline}):
        pair = sorted((row for row in nonbaseline if row["parameter"] == parameter), key=lambda row: row["factor"])
        parameter_cases[parameter] = {"low_parameter": pair[0]["absolute_parameters"][parameter],
                                      "high_parameter": pair[1]["absolute_parameters"][parameter],
                                      "low_outputs": outputs[pair[0]["run_id"]],
                                      "high_outputs": outputs[pair[1]["run_id"]]}
    sensitivity = b0.sensitivity_matrix(parameter_cases, absolute_rank_tolerance=1e-12,
                                         relative_rank_tolerance=1e-8)

    species_values: dict[str, list[float]] = {}
    aggregate = []
    with (puckworks_root / "puckworks/data/schmieder2023/cup_masses.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            if not row["mass_in_cup"]:
                continue
            value = float(row["mass_in_cup"])
            if row["component"] == "TDS": aggregate.append(value)
            else: species_values.setdefault(row["component"], []).append(value)
    # The audit needs only aligned, source-only series; all component rows share the campaign grid.
    species = b0.source_species_limitation_audit(species_values, aggregate)
    return {"schema_version": "espresso.val_corpus_002.b2_frozen_results.v1", "status": "PASS",
            "production_counts": {"identities": 45, "pass": 27, "typed_numerical_failure": 18,
                                  "infrastructure_failure": 0, "fresh_executions_total": 44,
                                  "b1_anchor_reuse": 1},
            "predecessor_parity": {"status": "PASS", "states_compared": 1500},
            "availability_matrix": availability, "schmieder": schmieder,
            "h0_h1_paired_metrics": paired, "axis_contrasts": axis,
            "waszkiewicz": {"source_tds_fraction": source_tds, "results": wasz,
                             "reduced_source_clock": "DIAGNOSTIC_NOT_OPENFOAM_NOT_VALIDATION"},
            "sensitivity": sensitivity, "sensitivity_counts": {"identities": 9, "pass": 9,
                            "baseline_reuses": 1, "fresh_executions": 8,
                            "typed_numerical_failure": 0, "infrastructure_failure": 0},
            "species_limitation_audit": species,
            "scientific_result_disposition": "FIXED_PARAMETER_B2_RESULT_WITH_18_IMMUTABLE_TARGET_COVERAGE_FAILURES",
            "validation_framework_disposition": "SOURCE_SPECIFIC_AGGREGATE_CHEMISTRY_SUPPORT_WITH_LIMITATIONS",
            "claim_ceiling": {"physical_validation": "NOT_ESTABLISHED",
                              "general_whole_solver_physical_validation": "NOT_ESTABLISHED",
                              "new_governing_physics": "NOT_AUTHORIZED"},
            "configuration_hashes": hashes, "partial_cache_aggregate_sha256": cache["aggregate_sha256"]}


def external_bundle(original_root: Path, recovery_root: Path) -> dict:
    original = json.loads((original_root / "runtime/B2_PARTIAL_ARTIFACT_INVENTORY.json").read_text())
    recovery = b0.external_inventory(recovery_root, [
        path for path in recovery_root.rglob("*")
        if path.is_file() and path.name not in {"B2_RECOVERY_ARTIFACT_INVENTORY.json",
                                               "B2_COMBINED_ARTIFACT_INVENTORY.json"}
    ])
    digest = hashlib.sha256()
    combined_files = []
    for prefix, inventory in (("original", original), ("recovery", recovery)):
        for row in inventory["files"]:
            item = {"path": f"{prefix}/{row['path']}", "sha256": row["sha256"], "bytes": row["bytes"]}
            combined_files.append(item)
    combined_files.sort(key=lambda row: row["path"])
    for row in combined_files:
        digest.update(f"{row['path']}\0{row['sha256']}\0{row['bytes']}\n".encode())
    combined = {"schema_version": "espresso.val_corpus_002.b2_combined_external_inventory.v1",
                "file_count": len(combined_files),
                "total_bytes": sum(row["bytes"] for row in combined_files),
                "aggregate_sha256": digest.hexdigest(), "files": combined_files,
                "original": {key: original[key] for key in ("file_count", "total_bytes", "aggregate_sha256")},
                "recovery": {key: recovery[key] for key in ("file_count", "total_bytes", "aggregate_sha256")}}
    _dump(recovery_root / "runtime/B2_RECOVERY_ARTIFACT_INVENTORY.json", recovery)
    _dump(recovery_root / "runtime/B2_COMBINED_ARTIFACT_INVENTORY.json", combined)
    return combined


def publish_results(repo: Path, recovery_root: Path) -> dict:
    runtime = recovery_root / "runtime"
    results = json.loads((runtime / "B2_FROZEN_RESULTS.json").read_text())
    combined = json.loads((runtime / "B2_COMBINED_ARTIFACT_INVENTORY.json").read_text())
    wasz = json.loads((runtime / "WASZ_P2_RECOVERY_RESULT.json").read_text())
    sensitivity = json.loads((runtime / "SENSITIVITY_RECOVERY_RESULT.json").read_text())
    base = repo / "validation/cases/val_corpus_002"
    result_path = base / "VAL_CORPUS_002_STAGE_B2_RESULT.json"
    artifact_path = base / "VAL_CORPUS_002_STAGE_B2_EXTERNAL_ARTIFACT_SUMMARY.json"
    recovery_path = base / "VAL_CORPUS_002_STAGE_B2_RECOVERY_RESULT.json"
    _dump(result_path, results)
    artifact_summary = {"schema_version": "espresso.val_corpus_002.b2_external_summary.v1",
                        "authorization_id": b2.AUTHORIZATION_ID,
                        "original": combined["original"], "recovery": combined["recovery"],
                        "combined": {key: combined[key] for key in ("file_count", "total_bytes", "aggregate_sha256")},
                        "raw_execution_products_committed": False}
    _dump(artifact_path, artifact_summary)
    recovery_summary = {"schema_version": "espresso.val_corpus_002.b2_recovery_result.v1",
                        "status": "PASS", "authorization_id": b2.AUTHORIZATION_ID,
                        "recovery_source_head": RECOVERY_SOURCE_HEAD,
                        "corrected_waszkiewicz_p2": wasz,
                        "sensitivity": {key: sensitivity[key] for key in
                                        ("identity_count", "baseline_reuse_count", "fresh_count")},
                        "partial_cache_count": 44,
                        "partial_cache_aggregate_sha256": results["partial_cache_aggregate_sha256"],
                        "corrected_production_aggregate_sha256": "c7eb8db410fe572c6638163dae1592f332cb82f15fe85c051cd65ef51651af02",
                        "original_partial_evidence": "IMMUTABLE",
                        "original_failed_preparation_attempts": "RETAINED_UNCHANGED"}
    _dump(recovery_path, recovery_summary)
    report = f"""# VAL-CORPUS-002 Stage B2 result

Status: `VAL_CORPUS_002_STAGE_B2_RESULT_COMPLETE_PENDING_REVIEW`.

The structured Waszkiewicz P2 placeholder defect was corrected prospectively.
The original partial execution and both failed preparation attempts remain
immutable. The corrected Waszkiewicz P2 execution passed on corrected attempt
1. The other 44 production dispositions were content-verified and not rerun.

Production closes at 45 identities: 27 PASS and 18 immutable
`REQUIRED_TARGET_BEVERAGE_MASS_NOT_REACHED_NO_EXTRAPOLATION` typed failures.
No missing 60 g value is extrapolated or imputed. Predecessor parity remains
1500/1500 PASS. Sensitivity closes at 9/9 PASS with one exact baseline reuse
and eight fresh executions; its 3-by-4 matrix has numerical rank
{results['sensitivity']['rank']} and remains `NOT_STRUCTURAL_IDENTIFIABILITY`.

Both fixed Waszkiewicz clock presentations are reported in the machine-readable
result. The source-reported and fixed +3 s mappings are not optimized. The
species audit is source-only; caffeine, trigonelline, and 5-CQA are not claimed
as separately predicted solver species.

Scientific disposition:
`{results['scientific_result_disposition']}`.

Validation-framework disposition:
`{results['validation_framework_disposition']}`.

Claim ceiling remains `PHYSICAL_VALIDATION: NOT_ESTABLISHED` and
`NEW_GOVERNING_PHYSICS: NOT_AUTHORIZED`. Calibration is closed with no refit;
protected scoring was not performed.
"""
    (repo / "docs/validation/VAL_CORPUS_002_STAGE_B2_RESULT.md").write_text(report)
    return {"result_sha256": b0.file_sha256(result_path),
            "artifact_summary_sha256": b0.file_sha256(artifact_path),
            "recovery_result_sha256": b0.file_sha256(recovery_path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("inventory", "preflight", "cache", "analyze", "bundle", "publish"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--b1-root", type=Path, required=True)
    parser.add_argument("--original-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--recovery-root", type=Path)
    parser.add_argument("--puckworks-root", type=Path)
    args = parser.parse_args()
    root, b1_root = args.root.resolve(), args.b1_root.resolve()
    if args.command == "inventory":
        value = corrected_inventory(root, b1_root, root / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_CONFIGURATION_INVENTORY.json")
        _dump(args.output, value)
    elif args.command == "preflight":
        preflight_all_p2(root, b1_root, args.output.resolve())
    elif args.command == "cache":
        if not args.original_root:
            raise SystemExit("--original-root required")
        _dump(args.output, verify_partial_cache(root, b1_root, args.original_root.resolve()))
    elif args.command == "analyze":
        if not args.original_root or not args.recovery_root or not args.puckworks_root:
            raise SystemExit("analyze requires --original-root, --recovery-root and --puckworks-root")
        _dump(args.output, frozen_results(root, b1_root, args.original_root.resolve(),
                                         args.recovery_root.resolve(), args.puckworks_root.resolve()))
    elif args.command == "bundle":
        if not args.original_root or not args.recovery_root:
            raise SystemExit("bundle requires --original-root and --recovery-root")
        _dump(args.output, external_bundle(args.original_root.resolve(), args.recovery_root.resolve()))
    else:
        if not args.recovery_root:
            raise SystemExit("publish requires --recovery-root")
        _dump(args.output, publish_results(root, args.recovery_root.resolve()))


if __name__ == "__main__":
    main()
