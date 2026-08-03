#!/usr/bin/env python3
"""Closed Stage-B1 attempt-1 verification and deterministic recovery replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

import val_corpus_002_b0_tooling as b0
import val_corpus_002_b1_calibration as b1


ATTEMPT1_COUNT = 20
RECOVERY_SCHEMA = "espresso.val_corpus_002.b1_attempt1_cache.v1"
APPROVED_RECOVERY_HEAD = "0acfeb1f98d775abe18504d17f2d48fc1935c1e0"
REPLAY_RESULT_SHA256 = "666f4033298ecbbe7de42d4915512a934eafbdf89f64c272fb6b7b25b9a64158"
SELECTED_EVALUATION_SHA256 = "2c99be6239eebc6816ffa4fdd726f44933ad34aa35e119ab02b519b50375d607"


def _regular_below(path: Path, root: Path) -> Path:
    if path.is_symlink() or not path.is_file():
        raise b1.InfrastructureFailure(f"required nonsymlink file absent: {path}")
    resolved, boundary = path.resolve(), root.resolve()
    if resolved != boundary and boundary not in resolved.parents:
        raise b1.InfrastructureFailure(f"artifact escapes authorized root: {path}")
    return resolved


def _aggregate(rows: list[dict]) -> str:
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item["sequence"]):
        digest.update(b0.canonical_bytes(row))
    return digest.hexdigest()


def verify_attempt1_cache(repo: Path, attempt1: Path) -> dict:
    """Fail closed unless all and only the 20 reported PASS records verify."""
    template = b1.exact_template(repo)
    executable = _regular_below(attempt1 / "runtime/executable/espressoWholePullFoam", attempt1)
    if b1.sha256(executable) != b1.EXECUTABLE_SHA256:
        raise b1.InfrastructureFailure("attempt-1 executable mismatch")
    rows: list[dict] = []
    seen: dict[str, str] = {}
    for sequence in range(ATTEMPT1_COUNT):
        directory = attempt1 / "evaluations" / f"eval-{sequence:03d}"
        record_path = _regular_below(directory / "evaluation.json", attempt1)
        record = json.loads(record_path.read_text())
        if record.get("sequence") != sequence or record.get("status") != "PASS":
            raise b1.InfrastructureFailure(f"attempt-1 PASS record mismatch: {sequence}")
        rate = record.get("rate_s_inverse")
        if (not isinstance(rate, float) or not math.isfinite(rate) or
                rate.hex() != record.get("rate_hex") or not b0.K_LOWER <= rate <= b0.K_UPPER):
            raise b1.InfrastructureFailure(f"attempt-1 rate identity mismatch: {sequence}")
        config = _regular_below(attempt1 / record["configuration_path"], attempt1)
        trace = _regular_below(attempt1 / record["trace_path"], attempt1)
        solver_log = _regular_below(directory / "log.solver", attempt1)
        if b1.sha256(config) != record.get("configuration_sha256"):
            raise b1.InfrastructureFailure(f"attempt-1 configuration hash mismatch: {sequence}")
        expected = b0._materialize_p2_rate(template, rate, b0.EXP7_H1_TEMPLATE_SHA256)
        if config.read_bytes() != b0.canonical_bytes(expected):
            raise b1.InfrastructureFailure(f"attempt-1 configuration reconstruction mismatch: {sequence}")
        if (b1.sha256(trace) != record.get("trace_sha256") or
                trace.stat().st_size != record.get("trace_bytes")):
            raise b1.InfrastructureFailure(f"attempt-1 trace identity mismatch: {sequence}")
        log_text = solver_log.read_text(encoding="utf-8", errors="replace")
        if record.get("solver_exit_code") != 0 or log_text.count("\nEnd\n") != 1:
            raise b1.InfrastructureFailure(f"attempt-1 completion mismatch: {sequence}")
        parsed = b1._trace_rows(trace)
        model, verification = b1.reduce_evaluation(parsed, expected)
        objective = b0.calibration_objective(b0.SOURCE_SOLUTE_MASSES_G, model)
        if model != record.get("model_cup_solute_masses_g") or objective != record.get("objective"):
            raise b1.InfrastructureFailure(f"attempt-1 objective reconstruction mismatch: {sequence}")
        if verification != record.get("verification"):
            raise b1.InfrastructureFailure(f"attempt-1 numerical gate mismatch: {sequence}")
        if record["rate_hex"] in seen and seen[record["rate_hex"]] != record["configuration_sha256"]:
            raise b1.InfrastructureFailure("inconsistent duplicate attempt-1 rate")
        seen[record["rate_hex"]] = record["configuration_sha256"]
        rows.append({
            "sequence": sequence, "rate_s_inverse": rate, "rate_hex": rate.hex(),
            "objective": objective, "configuration_path": record["configuration_path"],
            "configuration_sha256": record["configuration_sha256"],
            "evaluation_record_sha256": b1.sha256(record_path),
            "solver_log_path": solver_log.relative_to(attempt1).as_posix(),
            "solver_log_sha256": b1.sha256(solver_log),
            "trace_path": record["trace_path"], "trace_sha256": record["trace_sha256"],
            "trace_bytes": record["trace_bytes"], "model_cup_solute_masses_g": model,
            "first_timestamp_s": record["first_timestamp_s"],
            "final_timestamp_s": record["final_timestamp_s"], "verification": verification,
            "solver_commit": b1.SOLVER_COMMIT, "executable_sha256": b1.EXECUTABLE_SHA256,
            "calibration_template_sha256": b0.EXP7_H1_TEMPLATE_SHA256,
            "cache_status": "REUSED_CONTENT_VERIFIED_ATTEMPT_1"})
    extras = sorted((attempt1 / "evaluations").glob("eval-*/evaluation.json"))
    if len(extras) != 21:
        raise b1.InfrastructureFailure("attempt-1 evaluation-record inventory changed")
    failed = json.loads(_regular_below(attempt1 / "evaluations/eval-020/evaluation.json", attempt1).read_text())
    if failed.get("sequence") != 20 or failed.get("status") == "PASS":
        raise b1.InfrastructureFailure("attempt-1 evaluation 20 disposition changed")
    return {"schema_version": RECOVERY_SCHEMA, "authorization_id": b1.AUTHORIZATION_ID,
            "attempt": 1, "required_count": ATTEMPT1_COUNT, "verified_count": len(rows),
            "aggregate_sha256": _aggregate(rows), "evaluations": rows,
            "excluded_sequences": [20, 21]}


def adjudicate_evaluation20(attempt1: Path) -> dict:
    directory = attempt1 / "evaluations/eval-020"
    log = _regular_below(directory / "log.solver", attempt1)
    trace = _regular_below(directory / "case/postProcessing/wholePull/0/traces.csv", attempt1)
    text = log.read_text(encoding="utf-8", errors="replace")
    end_at = text.find("\nEnd\n")
    before = text[:end_at] if end_at >= 0 else text
    fatal_markers = [marker for marker in ("FOAM FATAL", "Signal: Floating point exception",
                                           "Floating point exception (core dumped)") if marker in before]
    parsed = b1._trace_rows(trace)
    if text.count("\nEnd\n") != 1 or fatal_markers or parsed[-1]["time_s"] < 90 - 1e-12:
        raise b1.InfrastructureFailure("evaluation-20 supplied post-End report not confirmed")
    if "Finalising parallel run" not in text[end_at:] or "Segmentation fault" not in text[end_at:]:
        raise b1.InfrastructureFailure("evaluation-20 MPI-finalization evidence absent")
    return {"sequence": 20, "prior_classification": "VALID_EXECUTION_WITH_TYPED_NUMERICAL_FAILURE",
            "corrected_classification": "POST_END_MPI_FINALIZATION_INFRASTRUCTURE_FAILURE",
            "normal_end_marker_count": 1, "fatal_or_numerical_abort_before_end": fatal_markers,
            "all_expected_solver_timesteps_completed": True, "trace_terminal_time_s": parsed[-1]["time_s"],
            "process_failure_phase": "MPI_FINALIZATION_AFTER_NORMAL_END", "return_code": 139,
            "solver_log_sha256": b1.sha256(log), "solver_log_bytes": log.stat().st_size,
            "objective": None, "cache_eligible": False, "optimizer_interval_effect": "MUST_NOT_BE_RETAINED"}


def infrastructure_snapshot(run_root: Path, executable: Path) -> dict:
    def output(command: list[str]) -> str:
        return subprocess.run(command, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, check=False).stdout.strip()
    stale = output(["ps", "-eo", "comm=,args="])
    relevant = [line.strip() for line in stale.splitlines()
                if line.strip().split(maxsplit=1)[0] in {"mpirun", "espressoWholePullFoam"}]
    if relevant:
        raise b1.InfrastructureFailure("stale or active calibration process detected: " + " | ".join(relevant))
    stat = os.statvfs(run_root.parent)
    shm = os.statvfs("/dev/shm") if Path("/dev/shm").is_dir() else None
    memory = Path("/proc/meminfo").read_text().splitlines()[:5]
    return {"openfoam_distribution": os.environ.get("WM_PROJECT"),
            "openfoam_version": os.environ.get("WM_PROJECT_VERSION"),
            "executable_sha256": b1.sha256(executable), "available_memory_snapshot": memory,
            "filesystem_available_bytes": stat.f_bavail * stat.f_frsize,
            "filesystem_available_inodes": stat.f_favail,
            "dev_shm_available_bytes": None if shm is None else shm.f_bavail * shm.f_frsize,
            "process_limits": {"nofile": resource.getrlimit(resource.RLIMIT_NOFILE),
                               "nproc": resource.getrlimit(resource.RLIMIT_NPROC)},
            "mpi_version": output(["mpirun", "--version"]), "relevant_processes": [],
            "command_environment": {key: os.environ.get(key) for key in
                                    ("WM_PROJECT", "WM_PROJECT_VERSION", "FOAM_APPBIN", "PATH")}}


def initialize(repo: Path, attempt1: Path, attempt2: Path, executable: Path) -> dict:
    if attempt2.exists():
        raise b1.InfrastructureFailure(f"refusing to reuse attempt-2 root: {attempt2}")
    cache = verify_attempt1_cache(repo, attempt1)
    adjudication = adjudicate_evaluation20(attempt1)
    b1.initialize(repo, attempt2, executable)
    snapshot = infrastructure_snapshot(attempt2, attempt2 / "runtime/executable/espressoWholePullFoam")
    smoke_log = attempt2 / "runtime/log.mpi-smoke"
    with smoke_log.open("wb") as stream:
        smoke = subprocess.run(["mpirun", "-np", "16", "bash", "-c", "exit 0"],
                               stdout=stream, stderr=subprocess.STDOUT, check=False)
    if smoke.returncode:
        raise b1.InfrastructureFailure(f"16-rank MPI smoke failed: {smoke.returncode}")
    b1.dump(attempt2 / "runtime/attempt-1-cache-manifest.json", cache)
    b1.dump(attempt2 / "runtime/evaluation-20-adjudication.json", adjudication)
    b1.dump(attempt2 / "runtime/infrastructure-snapshot.json", snapshot)
    record = {"status": "READY_FOR_CONTROLLED_DETERMINISTIC_REPLAY", "cache_count": 20,
              "cache_aggregate_sha256": cache["aggregate_sha256"],
              "evaluation_20": adjudication["corrected_classification"],
              "mpi_smoke": "PASS", "mpi_smoke_log_sha256": b1.sha256(smoke_log)}
    b1.dump(attempt2 / "runtime/B1_RECOVERY_ACTIVATION.json", record)
    return record


def _execute_new(repo: Path, run_root: Path, rate: float, sequence: int) -> dict:
    directory = run_root / "evaluations" / f"attempt2-eval-{sequence:03d}"
    case = directory / "case"
    directory.mkdir(parents=True)
    template = b1.exact_template(repo)
    materialized = b0._materialize_p2_rate(template, rate, b0.EXP7_H1_TEMPLATE_SHA256)
    config = directory / "calibration-configuration.json"; b1.dump(config, materialized, canonical=True)
    scenario = directory / "solver-scenario.json"; b1.dump(scenario, b1.solver_scenario(repo, materialized), canonical=True)
    try:
        subprocess.run([sys.executable, str(repo / "scripts/prepare_case.py"), "--root", str(repo),
                        "--config", str(scenario), "--case-dir", str(case), "--nprocs", "16"], check=True)
        b1._run(["blockMesh"], case, directory / "log.blockMesh")
        b1._run(["checkMesh"], case, directory / "log.checkMesh")
        b1._run(["decomposePar", "-force"], case, directory / "log.decomposePar")
        code = b1._run(["mpirun", "-np", "16", str(run_root / "runtime/executable/espressoWholePullFoam"),
                        "-parallel"], case, directory / "log.solver", solver=True)
        log_text = (directory / "log.solver").read_text(encoding="utf-8", errors="replace")
        end_at = log_text.find("\nEnd\n")
        if code:
            if end_at >= 0:
                raise b1.InfrastructureFailure(f"POST_END_MPI_FINALIZATION_OR_PROCESS_FAILURE_EXIT_{code}")
            if any(marker in log_text for marker in ("FOAM FATAL", "Signal: Floating point exception",
                                                      "Floating point exception (core dumped)")):
                raise b0.TypedNumericalEvaluationFailure("OPENFOAM_FATAL_NUMERICAL_EVENT_BEFORE_END")
            raise b1.InfrastructureFailure(f"MPI_OR_SOLVER_LAUNCH_FAILURE_EXIT_{code}")
        if log_text.count("\nEnd\n") != 1:
            raise b1.InfrastructureFailure("normal solver End marker absent or ambiguous")
        trace = case / "postProcessing/wholePull/0/traces.csv"
        parsed = b1._trace_rows(trace)
        model, verification = b1.reduce_evaluation(parsed, materialized)
        objective = b0.calibration_objective(b0.SOURCE_SOLUTE_MASSES_G, model)
        record = {"sequence": sequence, "rate_s_inverse": rate, "rate_hex": rate.hex(), "status": "PASS",
                  "objective": objective, "model_cup_solute_masses_g": model, "verification": verification,
                  "configuration_path": config.relative_to(run_root).as_posix(),
                  "configuration_sha256": b1.sha256(config), "solver_exit_code": 0,
                  "trace_path": trace.relative_to(run_root).as_posix(), "trace_sha256": b1.sha256(trace),
                  "trace_bytes": trace.stat().st_size, "first_timestamp_s": parsed[0]["time_s"],
                  "final_timestamp_s": parsed[-1]["time_s"], "cache_status": "EXECUTED_ATTEMPT_2"}
        b1.dump(directory / "evaluation.json", record)
        return record
    except (b0.TypedNumericalEvaluationFailure, b1.InfrastructureFailure):
        raise
    except Exception as exc:
        raise b1.InfrastructureFailure(f"unclassified orchestration failure: {type(exc).__name__}: {exc}") from exc


def replay(repo: Path, attempt1: Path, attempt2: Path) -> dict:
    ready = attempt2 / "runtime/B1_RECOVERY_ACTIVATION.json"
    if not ready.is_file():
        raise b1.InfrastructureFailure("recovery activation absent")
    cache = verify_attempt1_cache(repo, attempt1)
    stored = json.loads((attempt2 / "runtime/attempt-1-cache-manifest.json").read_text())
    if cache != stored:
        raise b1.InfrastructureFailure("attempt-1 cache content changed after activation")
    cached = {row["rate_hex"]: row for row in cache["evaluations"]}
    expected = [row["rate_hex"] for row in cache["evaluations"]]
    provenance: dict[str, dict] = {}
    new_records: dict[str, dict] = {}
    requested: list[str] = []
    infrastructure_attempts = 0

    def objective(rate: float) -> float:
        nonlocal infrastructure_attempts
        key = rate.hex(); requested.append(key)
        if len(requested) <= ATTEMPT1_COUNT and key != expected[len(requested)-1]:
            raise b1.InfrastructureFailure("deterministic replay diverged before failed point")
        if key in cached:
            provenance[key] = cached[key]
            return cached[key]["objective"]
        try:
            row = _execute_new(repo, attempt2, rate, len(new_records))
        except b1.InfrastructureFailure:
            infrastructure_attempts += 1
            raise
        new_records[key] = row; provenance[key] = row
        return row["objective"]

    try:
        optimizer = b0.golden_section_log_k(objective)
    except b1.InfrastructureFailure as exc:
        failure = {"status": "ATTEMPT_2_INFRASTRUCTURE_FAILURE", "reason": str(exc),
                   "cache_reuse_count": sum(key in cached for key in requested),
                   "new_execution_count": len(new_records), "infrastructure_attempt_count": infrastructure_attempts,
                   "requested_rate_hex": requested, "original_bounds": [b0.LOG_K_LOWER, b0.LOG_K_UPPER]}
        b1.dump(attempt2 / "runtime/ATTEMPT_2_FAILURE.json", failure)
        raise
    for row in optimizer["trace"]:
        source = provenance.get(row["rate_hex"])
        row["recovery_evaluation_class"] = None if source is None else source["cache_status"]
    result = {"status": optimizer["status"], "optimizer": optimizer,
              "cache_reuse_count": len({key for key in requested if key in cached}),
              "attempt2_new_execution_count": len(new_records),
              "total_objective_bearing_evaluations": optimizer["evaluations"],
              "infrastructure_attempt_count": infrastructure_attempts,
              "typed_numerical_failure_count": sum(row["evaluation_status"] == "FAILED_EVALUATION"
                                                    for row in optimizer["trace"]),
              "attempt1_cache_aggregate_sha256": cache["aggregate_sha256"],
              "original_bounds": [b0.LOG_K_LOWER, b0.LOG_K_UPPER],
              "interrupted_interval_used": False, "new_evaluations": list(new_records.values())}
    b1.dump(attempt2 / "runtime/optimizer-replay-result.json", result)
    return result


def finalize_only(repo: Path, attempt1: Path, attempt2: Path, replay_path: Path,
                  selected_evaluation_path: Path, approved_head: str,
                  verification_root: Path) -> dict:
    """Reconstruct a governed bundle using immutable artifacts only."""
    if approved_head != APPROVED_RECOVERY_HEAD:
        raise b1.InfrastructureFailure("approved recovery head mismatch")
    if verification_root.exists():
        raise b1.InfrastructureFailure("finalize-only verification root must be new and clean")
    _regular_below(replay_path, attempt2); _regular_below(selected_evaluation_path, attempt2)
    if b1.sha256(replay_path) != REPLAY_RESULT_SHA256:
        raise b1.InfrastructureFailure("optimizer replay result identity mismatch")
    if b1.sha256(selected_evaluation_path) != SELECTED_EVALUATION_SHA256:
        raise b1.InfrastructureFailure("selected evaluation record identity mismatch")
    verify_attempt1_cache(repo, attempt1)
    replay_record = json.loads(replay_path.read_text()); selected = json.loads(selected_evaluation_path.read_text())
    optimizer = replay_record.get("optimizer")
    if (replay_record.get("status") != "PASS" or not isinstance(optimizer, dict)
            or optimizer.get("selected_rate_s_inverse") != 0.3439597024835067
            or optimizer.get("selected_rate_hex") != "0x1.6036f8e53bf4ep-2"
            or optimizer.get("selected_log_k") != -1.0672307724139207
            or optimizer.get("selected_log_k_hex") != "-0x1.11360930cd77cp+0"
            or optimizer.get("selected_objective") != 0.003931989579189616):
        raise b1.InfrastructureFailure("immutable optimizer selection mismatch")
    selected_rows = [row for row in optimizer["trace"]
                     if row.get("final_selection_status") == "SELECTED_FINAL"]
    if len(selected_rows) != 1: raise b1.InfrastructureFailure("unique optimizer selection absent")
    selected_row = selected_rows[0]
    if (selected.get("status") != "PASS" or selected.get("solver_exit_code") != 0
            or selected.get("cache_status") != "EXECUTED_ATTEMPT_2"
            or selected.get("rate_s_inverse") != optimizer["selected_rate_s_inverse"]
            or selected.get("rate_hex") != optimizer["selected_rate_hex"]
            or selected.get("objective") != optimizer["selected_objective"]):
        raise b1.InfrastructureFailure("selected attempt-2 evaluation mismatch")
    configuration_source = _regular_below(attempt2 / selected["configuration_path"], attempt2)
    trace_source = _regular_below(attempt2 / selected["trace_path"], attempt2)
    if (b1.sha256(configuration_source) != selected["configuration_sha256"]
            or b1.sha256(trace_source) != selected["trace_sha256"]
            or trace_source.stat().st_size != selected["trace_bytes"]):
        raise b1.InfrastructureFailure("selected configuration or trace identity mismatch")
    template = b1.exact_template(repo)
    materialized = b0._materialize_p2_rate(template, optimizer["selected_rate_s_inverse"],
                                            b0.EXP7_H1_TEMPLATE_SHA256)
    if configuration_source.read_bytes() != b0.canonical_bytes(materialized):
        raise b1.InfrastructureFailure("selected configuration cannot be reconstructed")
    parsed = b1._trace_rows(trace_source)
    model, verification = b1.reduce_evaluation(parsed, materialized)
    objective = b0.calibration_objective(b0.SOURCE_SOLUTE_MASSES_G, model)
    if model != selected["model_cup_solute_masses_g"] or objective != optimizer["selected_objective"]:
        raise b1.InfrastructureFailure("selected trace objective cannot be reconstructed")

    verification_root.mkdir(parents=True)
    for relative in b1.INPUT_PATHS:
        source = _regular_below(attempt2 / relative, attempt2)
        target = verification_root / relative; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if b1.sha256(target) != b1.sha256(source): raise b1.InfrastructureFailure("frozen input copy mismatch")
    governed = verification_root / "governed"; governed.mkdir()
    configuration_path = governed / "calibration-configuration.json"; shutil.copy2(configuration_source, configuration_path)
    trace_path = governed / "retained-model-output-trace.csv"; shutil.copy2(trace_source, trace_path)
    optimizer_path = governed / "optimizer-trace.json"
    b1.dump(optimizer_path, {"status": "PASS", "evaluations": optimizer["evaluations"],
        "final_log_interval_width": optimizer["final_log_interval_width"], "trace": optimizer["trace"]})
    residuals = [value-source for source, value in zip(b0.SOURCE_SOLUTE_MASSES_G, model)]
    reduction = {"target_masses_g": b0.TARGET_MASSES_G,
        "source_cup_solute_masses_g": b0.SOURCE_SOLUTE_MASSES_G,
        "model_cup_solute_masses_g": model, "signed_residuals_g": residuals,
        "relative_residuals": [value/source for value, source in zip(residuals,b0.SOURCE_SOLUTE_MASSES_G)],
        "objective_identity": b0.OBJECTIVE_ID, "reconstructed_objective": objective}
    reduction_path = governed / "calibration-reduction.json"; b1.dump(reduction_path, reduction)
    with trace_path.open("rb") as trace_stream:
        trace_header_sha256 = hashlib.sha256(trace_stream.readline()).hexdigest()
    numerical = {"schema_version": "espresso.val_corpus_002.b1_numerical_verification.v1",
        "task": "VAL-CORPUS-002", "authorization_id": b1.AUTHORIZATION_ID,
        "calibration_case_id": b0.CALIBRATION_CASE_ID, "solver_commit": b1.SOLVER_COMMIT,
        "executable_sha256": b1.EXECUTABLE_SHA256,
        "calibration_configuration_sha256": b1.sha256(configuration_path),
        "openfoam_distribution": "OpenFOAM Foundation", "openfoam_version": "12",
        "mpi_ranks": 16, "delta_t_s": .02, "end_time_s": 90.0,
        "first_solver_timestamp_s": selected["first_timestamp_s"],
        "final_solver_timestamp_s": selected["final_timestamp_s"],
        "completion_disposition": "PASS", "fatal_event_count": 0,
        "target_mass_brackets": verification["target_mass_brackets"],
        "boundedness": {key: verification[key] for key in ("finite","nonnegative","tds_0_to_1")},
        "maximum_liquid_balance_relative_residual": verification["maximum_liquid_balance_relative_residual"],
        "maximum_solute_balance_relative_residual": verification["maximum_solute_balance_relative_residual"],
        "liquid_balance_gate": verification["liquid_gate"], "solute_balance_gate": verification["solute_gate"],
        "trace_path": trace_path.relative_to(verification_root).as_posix(),
        "trace_sha256": b1.sha256(trace_path), "trace_bytes": trace_path.stat().st_size,
        "trace_header_sha256": trace_header_sha256,
        "selected_evaluation_sequence": selected_row["sequence"], "overall_status": "PASS"}
    numerical_path = governed / "numerical-verification.json"; b1.dump(numerical_path, numerical)
    provenance = {"schema_version": "espresso.val_corpus_002.b1_selected_recovery_provenance.v1",
        "optimizer_sequence": selected_row["sequence"], "attempt_evaluation_sequence": selected["sequence"],
        "recovery_evaluation_class": selected["cache_status"], "rate_s_inverse": selected["rate_s_inverse"],
        "rate_hex": selected["rate_hex"], "log_k": selected_row["log_k"],
        "log_k_hex": selected_row["log_k_hex"], "objective": selected["objective"],
        "configuration_sha256": selected["configuration_sha256"], "trace_sha256": selected["trace_sha256"],
        "solver_exit_code": selected["solver_exit_code"], "evaluation_status": selected["status"],
        "evaluation_record_sha256": b1.sha256(selected_evaluation_path)}
    b1.dump(governed / "recovery-provenance.json", provenance)
    shutil.copy2(selected_evaluation_path, governed / "selected-evaluation.json")
    roles = {"OPTIMIZER_TRACE": optimizer_path, "CALIBRATION_CONFIGURATION": configuration_path,
             "CALIBRATION_REDUCTION": reduction_path, "RETAINED_MODEL_OUTPUT_TRACE": trace_path,
             "NUMERICAL_VERIFICATION": numerical_path}
    rows = [{"role": role, "path": path.relative_to(verification_root).as_posix(),
             "bytes": path.stat().st_size, "sha256": b1.sha256(path)} for role,path in roles.items()]
    digest=hashlib.sha256()
    for row in sorted(rows,key=lambda item:item["path"]):
        digest.update(f"{row['path']}\0{row['sha256']}\0{row['bytes']}\n".encode())
    artifact={"schema_version":"espresso.val_corpus_002.calibration_artifacts.v1",
              "aggregate_sha256":digest.hexdigest(),"files":rows}
    artifact_path=governed/"calibration-artifact-manifest.json"; b1.dump(artifact_path,artifact)
    manifest={"schema_version":"espresso.val_corpus_002.p2_calibration_manifest.v1",
        "status":b0.CALIBRATION_APPROVED_STATUS,"record_class":b0.GOVERNED_RECORD_CLASS,
        "task":"VAL-CORPUS-002","stage":"B1_CALIBRATION","authorization_id":b1.AUTHORIZATION_ID,
        "calibration_case_id":b0.CALIBRATION_CASE_ID,"template_sha256":b0.EXP7_H1_TEMPLATE_SHA256,
        "source_cohort_path":b0.COHORT_PATH.as_posix(),"source_cohort_sha256":b0.COHORT_SHA256,
        "target_masses_g":b0.TARGET_MASSES_G,"source_observations_g":b0.SOURCE_SOLUTE_MASSES_G,
        "objective_identity":b0.OBJECTIVE_ID,"optimizer_algorithm":"GOLDEN_SECTION_LOG_K_V1",
        "log_k_bounds":[b0.LOG_K_LOWER,b0.LOG_K_UPPER],"log_k_interval_tolerance":b0.LOG_K_TOLERANCE,
        "maximum_evaluations":b0.MAX_EVALUATIONS,"optimizer_status":"PASS",
        "optimizer_trace_sha256":b1.sha256(optimizer_path),"selected_log_k":optimizer["selected_log_k"],
        "selected_log_k_hex":optimizer["selected_log_k_hex"],
        "selected_rate_s_inverse":optimizer["selected_rate_s_inverse"],
        "selected_rate_hex":optimizer["selected_rate_hex"],"selected_objective":optimizer["selected_objective"],
        "solver_commit":b1.SOLVER_COMMIT,"executable_sha256":b1.EXECUTABLE_SHA256,
        "calibration_configuration_sha256":b1.sha256(configuration_path),
        "calibration_artifact_manifest_path":artifact_path.relative_to(verification_root).as_posix(),
        "calibration_artifact_manifest_sha256":b1.sha256(artifact_path),
        "calibration_artifact_aggregate_sha256":artifact["aggregate_sha256"],
        "numerical_completion":"PASS","conservation_disposition":"PASS"}
    manifest_path=governed/"calibration-manifest.json"; b1.dump(manifest_path,manifest)
    b0.validate_governed_calibration_manifest(manifest,expected_template_sha256=b0.EXP7_H1_TEMPLATE_SHA256,
        root=verification_root,expected_b1_authorization_id=b1.AUTHORIZATION_ID)
    barrier=b0.AccessBarrier(); barrier.authorize_b1("SEPARATE_HUMAN_OWNER_B1_AUTHORITY")
    barrier.freeze_p2(manifest,root=verification_root,expected_b1_authorization_id=b1.AUTHORIZATION_ID)
    return {"status":"PASS","selected_rate_s_inverse":manifest["selected_rate_s_inverse"],
            "selected_objective":manifest["selected_objective"],
            "calibration_manifest_sha256":b1.sha256(manifest_path),
            "artifact_manifest_sha256":b1.sha256(artifact_path),
            "artifact_aggregate_sha256":artifact["aggregate_sha256"],
            "governed_validator":"PASS","p2_freeze_barrier":"PASS"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(".")); parser.add_argument("--attempt1-root", type=Path, required=True)
    parser.add_argument("--attempt2-root", type=Path, required=True); parser.add_argument("--executable", type=Path)
    parser.add_argument("--optimizer-replay-result", type=Path)
    parser.add_argument("--selected-evaluation", type=Path); parser.add_argument("--approved-head")
    parser.add_argument("--verification-root", type=Path)
    modes = parser.add_mutually_exclusive_group(required=True); modes.add_argument("--initialize", action="store_true"); modes.add_argument("--replay", action="store_true"); modes.add_argument("--finalize-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.initialize:
            if args.executable is None: raise b1.InfrastructureFailure("--executable required")
            result = initialize(args.root.resolve(), args.attempt1_root.resolve(), args.attempt2_root.resolve(), args.executable.resolve())
        elif args.replay:
            result = replay(args.root.resolve(), args.attempt1_root.resolve(), args.attempt2_root.resolve())
        else:
            if not all((args.optimizer_replay_result, args.selected_evaluation,
                        args.approved_head, args.verification_root)):
                raise b1.InfrastructureFailure("finalize-only inputs are mandatory")
            result = finalize_only(args.root.resolve(), args.attempt1_root.resolve(),
                args.attempt2_root.resolve(), args.optimizer_replay_result.resolve(),
                args.selected_evaluation.resolve(), args.approved_head,
                args.verification_root.resolve())
    except b1.InfrastructureFailure as exc:
        print(json.dumps({"status": "INFRASTRUCTURE_OR_ORCHESTRATION_FAILURE", "reason": str(exc)}, indent=2))
        raise SystemExit(2)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
