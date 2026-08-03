#!/usr/bin/env python3
"""Closed Stage-B2 fixed-parameter production and sensitivity orchestration."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import val_corpus_002_b0_tooling as b0
import val_corpus_002_b1_calibration as b1


AUTHORIZATION_ID = "VAL-CORPUS-002-B2-PRODUCTION-SCORING-2026-08-03"
B1_AUTHORIZATION_ID = "VAL-CORPUS-002-B1-CALIBRATION-2026-08-03"
START_HEAD = "9f860d446fae3ea905ad5fd374e1ffc6abe275e5"
START_TREE = "e0f4fa4009b6fa4591d03b833258f7ba5c9d44f7"
RATE = 0.3439597024835067
RATE_HEX = "0x1.6036f8e53bf4ep-2"
EXECUTABLE_SHA256 = b1.EXECUTABLE_SHA256
SOLVER_COMMIT = b1.SOLVER_COMMIT
B1_MANIFEST_SHA256 = "554ce1c35979fa8961973b8cdd663a7a0ba817f6369667ea10808a06f644cbbc"
REFERENCE_TRACE = Path("corrected-runs-v2/cases/WASZ-9-COMPACT/postProcessing/wholePull/0/traces.csv")


class InfrastructureFailure(Exception):
    """A non-scientific failure that cannot receive a score."""


def _dump(path: Path, value: object, *, canonical: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = b0.canonical_bytes(value) if canonical else (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(payload)


def _sha(path: Path) -> str:
    return b0.file_sha256(path)


def verify_b1(root: Path, b1_root: Path) -> tuple[dict, dict]:
    manifest_path = b1_root / "governed/calibration-manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file() or _sha(manifest_path) != B1_MANIFEST_SHA256:
        raise InfrastructureFailure("exact strengthened B1 manifest unavailable")
    manifest = json.loads(manifest_path.read_text())
    rate = b0.validate_governed_calibration_manifest(
        manifest, expected_template_sha256=b0.EXP7_H1_TEMPLATE_SHA256,
        root=b1_root, expected_b1_authorization_id=B1_AUTHORIZATION_ID)
    if rate != RATE or rate.hex() != RATE_HEX:
        raise InfrastructureFailure("frozen B1 rate mismatch")
    barrier = b0.AccessBarrier()
    barrier.authorize_b1("SEPARATE_HUMAN_OWNER_B1_AUTHORITY")
    barrier.freeze_p2(manifest, root=b1_root,
                      expected_b1_authorization_id=B1_AUTHORIZATION_ID)
    inventory = b0.build_configuration_inventory(root)
    materialized = b0.materialize_all_p2(
        inventory, manifest, root=b1_root,
        expected_b1_authorization_id=B1_AUTHORIZATION_ID)
    return manifest, materialized


def prospective_inventory(root: Path, b1_root: Path) -> dict:
    _, p2 = verify_b1(root, b1_root)
    inventory = b0.build_configuration_inventory(root)
    numeric = {r["id"]: r["canonical_sha256"] for r in inventory["numeric_configurations"]}
    p2_rows = {key: b0.canonical_sha256(value) for key, value in p2["configurations"].items()}
    sensitivity = {r["id"]: r["canonical_sha256"] for r in inventory["sensitivity_configurations"]}
    all_production = {**numeric, **p2_rows}
    digest = hashlib.sha256()
    for key in sorted(all_production):
        digest.update(f"{key}\0{all_production[key]}\n".encode())
    return {
        "schema_version": "espresso.val_corpus_002.b2_configuration_inventory.v1",
        "authorization_id": AUTHORIZATION_ID,
        "governing_physics_change": "NO_GOVERNING_PHYSICS_CHANGE",
        "b1_manifest_sha256": B1_MANIFEST_SHA256,
        "governed_b1_validator": "PASS", "p2_freeze_barrier": "PASS",
        "selected_rate_s_inverse": RATE, "selected_rate_hex": RATE_HEX,
        "counts": {"production": 45, "numeric_p0_p1": 30, "materialized_p2": 15,
                   "sensitivity": 9, "fresh_production_if_reuse": 44,
                   "fresh_sensitivity_if_reuse": 8, "fresh_openfoam_if_reuse": 52},
        "numeric_configuration_sha256": numeric,
        "materialized_p2_configuration_sha256": p2_rows,
        "production_configuration_aggregate_sha256": digest.hexdigest(),
        "sensitivity_configuration_sha256": sensitivity,
        "reuse_adjudications": {
            "SCHM_EXP7_P2_FIXED_AFTER_EXP7_CALIBRATION_H1": "EXACT_IDENTITY_VERIFICATION_REQUIRED",
            "SENS_BASELINE_FROM_SCHM_EXP7_P1_H1": "EXACT_IDENTITY_VERIFICATION_REQUIRED"},
        "raw_rate_materialization": "PROHIBITED",
        "calibration_or_optimizer_entry_point": "ABSENT",
        "protected_hydraulic_scoring": "PROHIBITED",
        "post_transfer_refitting": "PROHIBITED"}


def _schmieder_scenario(root: Path, configuration: dict) -> dict:
    scenario = b1.solver_scenario(root, configuration)
    scenario["scenario_id"] = configuration["run_id"]
    scenario["calibration"] = {"status": "CLOSED_NO_REFIT", "fixed_rate_source": B1_MANIFEST_SHA256}
    scenario["extraction"]["rate_parameter_status"] = "B2_FIXED_PARAMETER_PRODUCTION"
    scenario["claim_ceiling"] = "Stage B2 fixed-parameter comparison; physical validation not established."
    return scenario


def solver_scenario(root: Path, configuration: dict) -> dict:
    if "run_id" in configuration:
        return _schmieder_scenario(root, configuration)
    scenario = copy.deepcopy(configuration)
    scenario["governance"]["authorization_id"] = AUTHORIZATION_ID
    scenario["governance"]["stage"] = "B2_FIXED_PARAMETER_PRODUCTION"
    return scenario


def sensitivity_scenario(root: Path, baseline: dict, row: dict) -> dict:
    value = copy.deepcopy(baseline)
    value["run_id"] = row["run_id"]
    value["parameterization"] = "P1_FIXED_SENSITIVITY"
    params = row["absolute_parameters"]
    value["chemistry"] = {
        "extractableFraction": params["extractableFraction"],
        "extractionRateConstant_s_inverse": params["extractionRateConstant"],
        "effectiveSoluteDiffusivity_m2_s": params["effectiveSoluteDiffusivity"],
        "saturationConcentration_kg_m3": params["saturationConcentration"]}
    return _schmieder_scenario(root, value)


def _run(command: list[str], cwd: Path, log: Path, *, solver: bool = False) -> int:
    with log.open("wb") as stream:
        result = subprocess.run(command, cwd=cwd,
                                env={**os.environ, "ESPRESSO_CASE_ROOT": str(cwd)},
                                stdout=stream, stderr=subprocess.STDOUT, check=False)
    if result.returncode and not solver:
        raise InfrastructureFailure(f"{command[0]} failed before solver completion")
    return result.returncode


def _cleanup_processors(case: Path) -> None:
    for path in case.glob("processor[0-9]*"):
        if path.is_dir() and not path.is_symlink() and path.parent == case:
            shutil.rmtree(path)


def execute_case(root: Path, run_root: Path, executable: Path, run_id: str,
                 configuration: dict, scenario: dict, attempt: int = 1) -> dict:
    target = run_root / "executions" / run_id / f"attempt-{attempt}"
    if target.exists():
        raise InfrastructureFailure(f"refusing reused case attempt: {run_id}")
    target.mkdir(parents=True)
    config_path = target / "production-configuration.json"
    scenario_path = target / "solver-scenario.json"
    _dump(config_path, configuration, canonical=True)
    _dump(scenario_path, scenario, canonical=True)
    case = target / "case"
    try:
        subprocess.run([sys.executable, str(root / "scripts/prepare_case.py"), "--root", str(root),
                        "--config", str(scenario_path), "--case-dir", str(case), "--nprocs", "16"],
                       check=True)
        _run(["blockMesh"], case, target / "log.blockMesh")
        _run(["checkMesh"], case, target / "log.checkMesh")
        _run(["decomposePar", "-force"], case, target / "log.decomposePar")
        started = time.time()
        code = _run(["mpirun", "-np", "16", str(executable), "-parallel"], case,
                    target / "log.solver", solver=True)
        trace = case / "postProcessing/wholePull/0/traces.csv"
        log_text = (target / "log.solver").read_text(errors="replace")
        normal_end = log_text.count("\nEnd\n") == 1 or log_text.rstrip().endswith("End")
        if code != 0:
            raise InfrastructureFailure("nonzero solver/MPI exit; no objective assigned")
        if not normal_end or not trace.is_file():
            raise InfrastructureFailure("normal solver completion or trace missing")
        rows = b1._trace_rows(trace)
        record = {"run_id": run_id, "attempt": attempt, "status": "PASS",
                  "execution_class": "FRESH_B2", "solver_exit_code": code,
                  "normal_end": normal_end, "configuration_sha256": _sha(config_path),
                  "scenario_sha256": _sha(scenario_path), "trace_sha256": _sha(trace),
                  "trace_bytes": trace.stat().st_size, "first_time_s": rows[0]["time_s"],
                  "final_time_s": rows[-1]["time_s"], "wall_seconds": time.time() - started,
                  "executable_sha256": _sha(executable), "solver_commit": SOLVER_COMMIT}
        if run_id.startswith("SCHM_") or run_id.startswith("SENS_"):
            model, gates = b1.reduce_evaluation(rows, configuration)
            record.update(model_cup_solute_masses_g=model, numerical_gates=gates)
        _dump(target / "execution-record.json", record)
        _cleanup_processors(case)
        return record
    except InfrastructureFailure:
        _cleanup_processors(case)
        raise
    except b0.TypedNumericalEvaluationFailure as exc:
        record = {"run_id": run_id, "attempt": attempt, "status": "TYPED_NUMERICAL_CASE_FAILURE",
                  "failure_reason": str(exc), "objective": None}
        _dump(target / "execution-record.json", record)
        _cleanup_processors(case)
        return record
    except Exception as exc:
        _cleanup_processors(case)
        raise InfrastructureFailure(f"unclassified orchestration failure: {type(exc).__name__}: {exc}") from exc


def initialize(root: Path, run_root: Path, executable: Path, b1_root: Path) -> dict:
    if run_root.exists():
        raise InfrastructureFailure("refusing to reuse B2 execution root")
    if executable.is_symlink() or not executable.is_file() or _sha(executable) != EXECUTABLE_SHA256:
        raise InfrastructureFailure("executable identity mismatch")
    if os.environ.get("WM_PROJECT") != "OpenFOAM" or os.environ.get("WM_PROJECT_VERSION") != "12":
        raise InfrastructureFailure("OpenFOAM Foundation 12 required")
    if subprocess.check_output(["git", "-C", str(root), "diff", "--name-only", SOLVER_COMMIT,
                                "--", "solver/espressoWholePullFoam"], text=True).strip():
        raise InfrastructureFailure("solver source differs from exact accepted commit")
    inventory = prospective_inventory(root, b1_root)
    run_root.mkdir(parents=True)
    binary = run_root / "runtime/executable/espressoWholePullFoam"
    binary.parent.mkdir(parents=True)
    shutil.copy2(executable, binary)
    preflight = {"authorization_id": AUTHORIZATION_ID, "approved_starting_head": START_HEAD,
                 "approved_starting_tree": START_TREE, "openfoam_distribution": "Foundation",
                 "openfoam_version": "12", "mpi_ranks": 16,
                 "executable_sha256": _sha(binary), "inventory": inventory,
                 "stale_process_check": "REQUIRED_BEFORE_EXECUTION",
                 "mpi_smoke_check": "REQUIRED_BEFORE_EXECUTION"}
    _dump(run_root / "runtime/B2_PREFLIGHT.json", preflight)
    return preflight


def _configuration_maps(root: Path, b1_root: Path) -> tuple[dict[str, dict], list[str], list[dict]]:
    _, materialized = verify_b1(root, b1_root)
    inventory = b0.build_configuration_inventory(root)
    configs = {row["id"]: row["configuration"] for row in inventory["numeric_configurations"]}
    configs.update(materialized["configurations"])
    matrix = json.loads((root / b0.RUN_MATRIX).read_text())
    order = [row.get("id", row.get("run_id")) for row in matrix["final_production_run_inventory"]]
    sensitivity = json.loads((root / b0.SENSITIVITY_MATRIX).read_text())["future_runs"]
    if len(configs) != 45 or len(order) != 45 or len(set(order)) != 45 or len(sensitivity) != 9:
        raise InfrastructureFailure("closed B2 matrix identity mismatch")
    return configs, order, sensitivity


def _load_record(run_root: Path, run_id: str) -> dict | None:
    for attempt in (2, 1):
        path = run_root / "executions" / run_id / f"attempt-{attempt}/execution-record.json"
        if path.is_file():
            return json.loads(path.read_text())
    path = run_root / "reuses" / run_id / "execution-record.json"
    return json.loads(path.read_text()) if path.is_file() else None


def _run_with_one_infrastructure_retry(root: Path, run_root: Path, executable: Path,
                                       run_id: str, config: dict, scenario: dict) -> dict:
    for attempt in (1, 2):
        try:
            return execute_case(root, run_root, executable, run_id, config, scenario, attempt)
        except InfrastructureFailure as exc:
            failed = run_root / "executions" / run_id / f"attempt-{attempt}"
            _dump(failed / "infrastructure-failure.json", {
                "run_id": run_id, "attempt": attempt,
                "status": "INFRASTRUCTURE_OR_ORCHESTRATION_FAILURE",
                "failure_reason": str(exc), "objective": None})
            if attempt == 2:
                raise
    raise AssertionError("unreachable")


def _reuse_b1_anchor(run_root: Path, b1_root: Path, configuration: dict) -> dict:
    source_config = b1_root / "governed/calibration-configuration.json"
    source_trace = b1_root / "governed/retained-model-output-trace.csv"
    expected = b0.canonical_sha256(configuration)
    if (_sha(source_config) != expected or expected !=
            "d3234d976c554ad87704d9c6c00032a08b99d52c6fc61c32846e2470dff99573"):
        raise InfrastructureFailure("B1 anchor configuration is not exact production identity")
    target = run_root / "reuses" / b0.CALIBRATION_CASE_ID
    target.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source_config, target / "production-configuration.json")
    shutil.copy2(source_trace, target / "retained-model-output-trace.csv")
    rows = b1._trace_rows(target / "retained-model-output-trace.csv")
    model, gates = b1.reduce_evaluation(rows, configuration)
    record = {"run_id": b0.CALIBRATION_CASE_ID, "status": "PASS",
              "execution_class": "REUSED_EXACT_B1_CALIBRATION_ANCHOR",
              "configuration_sha256": _sha(target / "production-configuration.json"),
              "trace_sha256": _sha(target / "retained-model-output-trace.csv"),
              "trace_bytes": (target / "retained-model-output-trace.csv").stat().st_size,
              "model_cup_solute_masses_g": model, "numerical_gates": gates,
              "solver_exit_code": 0, "executable_sha256": EXECUTABLE_SHA256,
              "solver_commit": SOLVER_COMMIT}
    _dump(target / "execution-record.json", record)
    return record


def execute_matrix(root: Path, run_root: Path, b1_root: Path) -> dict:
    executable = run_root / "runtime/executable/espressoWholePullFoam"
    if _sha(executable) != EXECUTABLE_SHA256:
        raise InfrastructureFailure("runtime executable identity mismatch")
    configs, order, sensitivity = _configuration_maps(root, b1_root)
    records: list[dict] = []
    for run_id in order:
        record = _load_record(run_root, run_id)
        if record is None:
            if run_id == b0.CALIBRATION_CASE_ID:
                record = _reuse_b1_anchor(run_root, b1_root, configs[run_id])
            else:
                record = _run_with_one_infrastructure_retry(
                    root, run_root, executable, run_id, configs[run_id],
                    solver_scenario(root, configs[run_id]))
        records.append(record)
        _dump(run_root / "runtime/B2_EXECUTION_PROGRESS.json", {
            "production_completed": len(records), "production_planned": 45,
            "last_run_id": run_id, "records": records})
    baseline = configs["SCHM_EXP7_P1_H1"]
    sensitivity_records = []
    baseline_record = next(row for row in records if row["run_id"] == "SCHM_EXP7_P1_H1")
    sensitivity_records.append({**baseline_record, "run_id": "SENS_BASELINE",
                                "execution_class": "REUSED_EXACT_B2_PRODUCTION_BASELINE"})
    for row in sensitivity[1:]:
        run_id = row["run_id"]
        record = _load_record(run_root, run_id)
        if record is None:
            config = sensitivity_scenario(root, baseline, row)
            record = _run_with_one_infrastructure_retry(root, run_root, executable,
                                                        run_id, config, config)
        sensitivity_records.append(record)
        _dump(run_root / "runtime/B2_EXECUTION_PROGRESS.json", {
            "production_completed": 45, "production_planned": 45,
            "sensitivity_completed": len(sensitivity_records), "sensitivity_planned": 9,
            "last_run_id": run_id, "records": records,
            "sensitivity_records": sensitivity_records})
    summary = {"status": "EXECUTION_COMPLETE_PENDING_REDUCTION",
               "production": records, "sensitivity": sensitivity_records,
               "counts": {"production_planned": 45, "production_pass": sum(r["status"] == "PASS" for r in records),
                          "production_fresh": sum(r.get("execution_class") == "FRESH_B2" for r in records),
                          "production_reused": sum(r.get("execution_class", "").startswith("REUSED") for r in records),
                          "sensitivity_planned": 9,
                          "sensitivity_pass": sum(r["status"] == "PASS" for r in sensitivity_records),
                          "sensitivity_fresh": sum(r.get("execution_class") == "FRESH_B2" for r in sensitivity_records),
                          "sensitivity_reused": sum(r.get("execution_class", "").startswith("REUSED") for r in sensitivity_records)}}
    _dump(run_root / "runtime/B2_EXECUTION_SUMMARY.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--b1-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--executable", type=Path)
    parser.add_argument("command", choices=("prospective-inventory", "initialize", "execute"))
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "prospective-inventory":
        value = prospective_inventory(root, args.b1_root.resolve())
        if not args.output:
            raise SystemExit("--output required")
        _dump(args.output, value)
    elif args.command == "initialize":
        if not args.run_root or not args.executable:
            raise SystemExit("--run-root and --executable required")
        initialize(root, args.run_root.resolve(), args.executable.resolve(), args.b1_root.resolve())
    else:
        if not args.run_root:
            raise SystemExit("--run-root required")
        execute_matrix(root, args.run_root.resolve(), args.b1_root.resolve())


if __name__ == "__main__":
    main()
