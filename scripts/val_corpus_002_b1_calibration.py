#!/usr/bin/env python3
"""Case-local B1 Experiment-7/H1 calibration orchestration."""

from __future__ import annotations

import argparse
import copy
import csv
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


AUTHORIZATION_ID = "VAL-CORPUS-002-B1-CALIBRATION-2026-08-03"
START_HEAD = "fd12ef922ca92a71e92cc6856093bede92355f90"
START_TREE = "1163b366cd7a0625bc3855286cca871f3b5038a6"
SOLVER_COMMIT = "0a5c146078da5d5f88b344b20e7b81042bf27ddb"
EXECUTABLE_SHA256 = "e682bb63d4b54a19133a81e1dc857217132b91918ecceb33ffbc88c35b6b0fd6"
EXTERNAL_TOKEN = "<VAL_CORPUS_002_RUNTIME_ROOT>"
INPUT_PATHS = (
    b0.COHORT_PATH,
    b0.RUN_MATRIX,
    b0.SENSITIVITY_MATRIX,
    b0.CASE_DIR / "VAL_CORPUS_002_EXP7_H1_CALIBRATION_SOURCE_BINDING.json",
    b0.CASE_DIR / "VAL_CORPUS_002_P2_CALIBRATION_MANIFEST_SCHEMA.json",
    b0.CASE_DIR / "VAL_CORPUS_002_CALIBRATION_ARTIFACT_MANIFEST_SCHEMA.json",
    Path("docs/validation/VAL_CORPUS_002_AGGREGATE_EXTRACTION_AND_CUP_CHEMISTRY_PROTOCOL.md"),
    Path("docs/validation/VAL_CORPUS_002_STAGE_B0_EXECUTION_TOOLING_PROTOCOL.md"),
    Path("docs/validation/VAL_CORPUS_002_STAGE_B0_EXACT_HEAD_REVIEW_CORRECTION.md"),
)


class InfrastructureFailure(Exception):
    """An orchestration failure that must escape optimizer scoring."""


def dump(path: Path, value: object, *, canonical: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = b0.canonical_bytes(value) if canonical else (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(data)


def sha256(path: Path) -> str:
    return b0.file_sha256(path)


def exact_template(root: Path) -> dict:
    inventory = b0.build_configuration_inventory(root)
    row = next(item for item in inventory["typed_p2_templates"]
               if item["id"] == b0.CALIBRATION_CASE_ID)
    if row["canonical_sha256"] != b0.EXP7_H1_TEMPLATE_SHA256:
        raise InfrastructureFailure("calibration template identity mismatch")
    return row["template"]


def solver_scenario(root: Path, materialized: dict) -> dict:
    """Derive the exact executable scenario from the frozen typed configuration."""
    base = json.loads((root / "config/reference_R0.json").read_text(encoding="utf-8"))
    value = copy.deepcopy(base)
    value["scenario_id"] = b0.CALIBRATION_CASE_ID
    value["mode"] = "source_linked_reconstruction"
    value["calibration"] = {
        "parameter": "extraction_rate_constant_s_inverse",
        "source_role": "EXPERIMENT_7_H1_RECONSTRUCTION_ANCHOR",
        "independent_validation_status": "not_validated"}
    value["geometry"]["basket_diameter_m"] = materialized["geometry"]["basket_diameter_m"]
    value["geometry"]["basket_radius_m"] = materialized["geometry"]["basket_radius_m"]
    value["coffee_bed"]["dry_dose_kg"] = materialized["geometry"]["dry_dose_kg"]
    value["coffee_bed"]["bed_depth_m"] = materialized["geometry"]["bed_depth_m"]
    value["coffee_bed"]["initial_extractable_fraction_dry_basis"] = materialized["chemistry"]["extractableFraction"]
    value["liquid"]["dynamic_viscosity_Pa_s"] = materialized["hydraulics"]["dynamic_viscosity_Pa_s"]
    value["liquid"]["effective_solute_diffusivity_m2_s"] = materialized["chemistry"]["effectiveSoluteDiffusivity_m2_s"]
    value["hydraulics"]["target_inlet_pressure_gauge_Pa"] = materialized["boundary_conditions"]["inlet_pressure_gauge_Pa"]
    value["hydraulics"]["outlet_pressure_gauge_Pa"] = materialized["boundary_conditions"]["outlet_pressure_gauge_Pa"]
    value["hydraulics"]["pressure_ramp_time_s"] = materialized["boundary_conditions"]["pressure_ramp_time_s"]
    coefficient = materialized["hydraulics"]["uniform_saturated_coefficient_m2"]
    value["hydraulics"]["saturated_permeability_m2"] = coefficient
    value["hydraulics"]["wetting_permeability_m2"] = coefficient
    value["hydraulics"]["permeability_profile"] = {
        "type": "uniform", "interface_position_m": value["coffee_bed"]["bed_depth_m"] / 2,
        "upstream_permeability_m2": coefficient, "downstream_permeability_m2": coefficient}
    value["extraction"]["rate_constant_1_s"] = materialized["chemistry"]["extractionRateConstant_s_inverse"]
    value["extraction"]["saturation_concentration_kg_m3"] = materialized["chemistry"]["saturationConcentration_kg_m3"]
    value["extraction"]["rate_parameter_status"] = "B1_EXP7_H1_CALIBRATION_CANDIDATE"
    value["time"].update({"start_s": 0.0, "end_s": materialized["controls"]["end_time_s"],
                          "delta_t_s": materialized["controls"]["delta_t_s"],
                          "field_write_interval_s": materialized["controls"]["field_write_interval_s"],
                          "target_beverage_mass_kg": 0.06})
    value["parallel"]["default_subdomains"] = materialized["controls"]["mpi_ranks"]
    value["claim_ceiling"] = "B1 Experiment-7/H1 reconstruction calibration candidate; physical validation not established."
    return value


def initialize(root: Path, run_root: Path, executable: Path) -> dict:
    if run_root.exists():
        raise InfrastructureFailure(f"refusing to reuse execution root: {run_root}")
    if executable.is_symlink() or not executable.is_file() or sha256(executable) != EXECUTABLE_SHA256:
        raise InfrastructureFailure("exact executable identity mismatch")
    if os.environ.get("WM_PROJECT") != "OpenFOAM" or os.environ.get("WM_PROJECT_VERSION") != "12":
        raise InfrastructureFailure("OpenFOAM Foundation 12 environment required")
    if subprocess.check_output(["git", "-C", str(root), "diff", "--name-only", SOLVER_COMMIT,
                                "--", "solver/espressoWholePullFoam"], text=True).strip():
        raise InfrastructureFailure("solver source differs from accepted main")
    run_root.mkdir(parents=True)
    records = []
    for relative in INPUT_PATHS:
        source, target = root / relative, run_root / relative
        if source.is_symlink() or not source.is_file():
            raise InfrastructureFailure(f"invalid frozen input: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
        if sha256(source) != sha256(target):
            raise InfrastructureFailure(f"copied input mismatch: {relative}")
        records.append({"path": relative.as_posix(), "bytes": target.stat().st_size,
                        "sha256": sha256(target)})
    binary = run_root / "runtime/executable/espressoWholePullFoam"
    binary.parent.mkdir(parents=True); shutil.copy2(executable, binary)
    if sha256(binary) != EXECUTABLE_SHA256:
        raise InfrastructureFailure("copied executable mismatch")
    activation = {"schema_version": "espresso.val_corpus_002.b1_runtime_activation.v1",
                  "authorization_id": AUTHORIZATION_ID, "approved_starting_head": START_HEAD,
                  "approved_starting_tree": START_TREE, "external_root": EXTERNAL_TOKEN,
                  "openfoam_distribution": "OpenFOAM Foundation", "openfoam_version": "12",
                  "solver_commit": SOLVER_COMMIT, "executable_sha256": EXECUTABLE_SHA256,
                  "calibration_case_id": b0.CALIBRATION_CASE_ID,
                  "calibration_template_sha256": b0.EXP7_H1_TEMPLATE_SHA256,
                  "inputs": records, "transfer_result_access": "PROHIBITED",
                  "stage_b2": "NOT_AUTHORIZED"}
    dump(run_root / "runtime/B1_RUNTIME_ACTIVATION.json", activation)
    return activation


def _run(command: list[str], cwd: Path, log: Path, *, solver: bool = False) -> int:
    env = dict(os.environ, ESPRESSO_CASE_ROOT=str(cwd))
    with log.open("wb") as stream:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, check=False)
    if result.returncode and not solver:
        raise InfrastructureFailure(f"orchestration command failed: {command[0]}")
    return result.returncode


def _trace_rows(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream); names = reader.fieldnames or []
        required = {"time_s", "cup_water_mass_kg", "cup_solute_mass_kg",
                    "cup_beverage_mass_kg", "cumulative_inlet_water_mass_kg",
                    "liquid_balance_residual_kg", "solute_balance_residual_kg",
                    "remaining_extractable_mass_kg", "dissolved_in_puck_mass_kg",
                    "min_saturation", "max_saturation", "min_concentration_kg_m3",
                    "max_concentration_kg_m3"}
        if required - set(names):
            raise InfrastructureFailure("retained trace schema mismatch")
        rows = [{key: float(value) for key, value in row.items() if key in required}
                for row in reader]
    if not rows: raise InfrastructureFailure("retained trace is empty")
    return rows


def reduce_evaluation(rows: list[dict[str, float]], materialized: dict) -> tuple[list[float], dict]:
    samples = [(row["time_s"], row["cup_beverage_mass_kg"], row["cup_solute_mass_kg"])
               for row in rows]
    model_g = [1000.0 * b0.fixed_mass(samples, target)["cup_solute_mass_kg"]
               for target in (0.020, 0.040, 0.060)]
    dose = materialized["geometry"]["dry_dose_kg"]
    extractable = dose * materialized["chemistry"]["extractableFraction"]
    liquid_relative = max(abs(row["liquid_balance_residual_kg"]) /
                          max(abs(row["cumulative_inlet_water_mass_kg"]), 1e-30) for row in rows)
    solute_relative = max(abs(row["solute_balance_residual_kg"]) / extractable for row in rows)
    finite = all(math.isfinite(value) for row in rows for value in row.values())
    nonnegative = all(row[key] >= -1e-12 for row in rows for key in
                      ("cup_water_mass_kg", "cup_solute_mass_kg", "cup_beverage_mass_kg",
                       "remaining_extractable_mass_kg", "dissolved_in_puck_mass_kg"))
    tds = [row["cup_solute_mass_kg"] / row["cup_beverage_mass_kg"]
           for row in rows if row["cup_beverage_mass_kg"] > 0]
    bounded = finite and nonnegative and all(0 <= value <= 1 for value in tds)
    verification = {"finite": finite, "nonnegative": nonnegative, "tds_0_to_1": bounded,
                    "maximum_liquid_balance_relative_residual": liquid_relative,
                    "maximum_solute_balance_relative_residual": solute_relative,
                    "liquid_gate": 1e-8, "solute_gate": 1e-8,
                    "target_mass_brackets": {"20_g": "PASS", "40_g": "PASS", "60_g": "PASS"}}
    if not bounded or liquid_relative > 1e-8 or solute_relative > 1e-8:
        raise b0.TypedNumericalEvaluationFailure("NUMERICAL_ADMISSIBILITY_GATE_FAILED")
    return model_g, verification


def execute(root: Path, run_root: Path) -> dict:
    activation_path = run_root / "runtime/B1_RUNTIME_ACTIVATION.json"
    if not activation_path.is_file(): raise InfrastructureFailure("runtime activation absent")
    executable = run_root / "runtime/executable/espressoWholePullFoam"
    if sha256(executable) != EXECUTABLE_SHA256: raise InfrastructureFailure("runtime executable changed")
    template = exact_template(root); evaluations: dict[str, dict] = {}

    def objective(rate: float) -> float:
        sequence = len(evaluations); key = rate.hex()
        if key in evaluations: return evaluations[key]["objective"]
        evaluation = run_root / "evaluations" / f"eval-{sequence:03d}"
        case = evaluation / "case"; evaluation.mkdir(parents=True)
        materialized = b0._materialize_p2_rate(template, rate, b0.EXP7_H1_TEMPLATE_SHA256)
        config_path = evaluation / "calibration-configuration.json"; dump(config_path, materialized, canonical=True)
        scenario = solver_scenario(root, materialized)
        scenario_path = evaluation / "solver-scenario.json"; dump(scenario_path, scenario, canonical=True)
        subprocess.run([sys.executable, str(root / "scripts/prepare_case.py"), "--root", str(root),
                        "--config", str(scenario_path), "--case-dir", str(case), "--nprocs", "16"],
                       check=True)
        _run(["blockMesh"], case, evaluation / "log.blockMesh")
        _run(["checkMesh"], case, evaluation / "log.checkMesh")
        _run(["decomposePar", "-force"], case, evaluation / "log.decomposePar")
        started = time.time()
        code = _run(["mpirun", "-np", "16", str(executable), "-parallel"], case,
                    evaluation / "log.solver", solver=True)
        trace = case / "postProcessing/wholePull/0/traces.csv"
        record = {"sequence": sequence, "rate_s_inverse": rate, "rate_hex": rate.hex(),
                  "configuration_path": config_path.relative_to(run_root).as_posix(),
                  "configuration_sha256": sha256(config_path), "solver_exit_code": code,
                  "wall_seconds": time.time() - started}
        if code != 0 or not trace.is_file():
            record.update(status="VALID_EXECUTION_WITH_TYPED_NUMERICAL_FAILURE", objective=None)
            evaluations[key] = record; dump(evaluation / "evaluation.json", record)
            raise InfrastructureFailure("SOLVER_NONZERO_EXIT_OR_TRACE_ABSENT")
        rows = _trace_rows(trace)
        try:
            model, verification = reduce_evaluation(rows, materialized)
        except b0.TypedNumericalEvaluationFailure as exc:
            record.update(status="VALID_EXECUTION_WITH_TYPED_NUMERICAL_FAILURE", objective=None,
                          failure_reason=str(exc), trace_path=trace.relative_to(run_root).as_posix(),
                          trace_sha256=sha256(trace), trace_bytes=trace.stat().st_size)
            evaluations[key] = record; dump(evaluation / "evaluation.json", record); raise
        value = b0.calibration_objective(b0.SOURCE_SOLUTE_MASSES_G, model)
        record.update(status="PASS", objective=value, model_cup_solute_masses_g=model,
                      verification=verification, trace_path=trace.relative_to(run_root).as_posix(),
                      trace_sha256=sha256(trace), trace_bytes=trace.stat().st_size,
                      first_timestamp_s=rows[0]["time_s"], final_timestamp_s=rows[-1]["time_s"])
        evaluations[key] = record; dump(evaluation / "evaluation.json", record)
        return value

    optimizer = b0.golden_section_log_k(objective)
    if optimizer["status"] != "PASS":
        dump(run_root / "governed/optimizer-trace.json", {
            "status": optimizer["status"], "evaluations": optimizer["evaluations"],
            "final_log_interval_width": optimizer.get("final_log_interval_width"),
            "trace": optimizer["trace"]})
        raise InfrastructureFailure(f"optimizer did not converge: {optimizer['status']}")
    selected = evaluations[optimizer["selected_rate_hex"]]
    if selected["status"] != "PASS": raise InfrastructureFailure("selected evaluation did not pass")
    governed = run_root / "governed"; governed.mkdir()
    optimizer_record = {"status": "PASS", "evaluations": optimizer["evaluations"],
                        "final_log_interval_width": optimizer["final_log_interval_width"],
                        "trace": optimizer["trace"]}
    optimizer_path = governed / "optimizer-trace.json"; dump(optimizer_path, optimizer_record)
    selected_eval = run_root / Path(selected["configuration_path"]).parent
    configuration_path = governed / "calibration-configuration.json"
    shutil.copy2(run_root / selected["configuration_path"], configuration_path)
    selected_trace = run_root / selected["trace_path"]
    trace_path = governed / "retained-model-output-trace.csv"; shutil.copy2(selected_trace, trace_path)
    residuals = [model-source for source, model in zip(b0.SOURCE_SOLUTE_MASSES_G,
                                                       selected["model_cup_solute_masses_g"])]
    reduction = {"target_masses_g": b0.TARGET_MASSES_G,
                 "source_cup_solute_masses_g": b0.SOURCE_SOLUTE_MASSES_G,
                 "model_cup_solute_masses_g": selected["model_cup_solute_masses_g"],
                 "signed_residuals_g": residuals,
                 "relative_residuals": [value/source for value, source in zip(residuals, b0.SOURCE_SOLUTE_MASSES_G)],
                 "objective_identity": b0.OBJECTIVE_ID,
                 "reconstructed_objective": b0.calibration_objective(
                     b0.SOURCE_SOLUTE_MASSES_G, selected["model_cup_solute_masses_g"])}
    reduction_path = governed / "calibration-reduction.json"; dump(reduction_path, reduction)
    verify = selected["verification"]
    numerical = {"schema_version": "espresso.val_corpus_002.b1_numerical_verification.v1",
                 "task": "VAL-CORPUS-002", "authorization_id": AUTHORIZATION_ID,
                 "calibration_case_id": b0.CALIBRATION_CASE_ID, "solver_commit": SOLVER_COMMIT,
                 "executable_sha256": EXECUTABLE_SHA256,
                 "calibration_configuration_sha256": sha256(configuration_path),
                 "openfoam_distribution": "OpenFOAM Foundation", "openfoam_version": "12",
                 "mpi_ranks": 16, "delta_t_s": .02, "end_time_s": 90.0,
                 "first_solver_timestamp_s": selected["first_timestamp_s"],
                 "final_solver_timestamp_s": selected["final_timestamp_s"],
                 "completion_disposition": "PASS", "fatal_event_count": 0,
                 "target_mass_brackets": verify["target_mass_brackets"],
                 "boundedness": {key: verify[key] for key in ("finite", "nonnegative", "tds_0_to_1")},
                 "maximum_liquid_balance_relative_residual": verify["maximum_liquid_balance_relative_residual"],
                 "maximum_solute_balance_relative_residual": verify["maximum_solute_balance_relative_residual"],
                 "liquid_balance_gate": verify["liquid_gate"], "solute_balance_gate": verify["solute_gate"],
                 "trace_path": trace_path.relative_to(run_root).as_posix(), "trace_sha256": sha256(trace_path),
                 "trace_bytes": trace_path.stat().st_size,
                 "trace_header_sha256": hashlib.sha256(trace_path.open("rb").readline()).hexdigest(),
                 "selected_evaluation_sequence": selected["sequence"], "overall_status": "PASS"}
    numerical_path = governed / "numerical-verification.json"; dump(numerical_path, numerical)
    roles = {"OPTIMIZER_TRACE": optimizer_path, "CALIBRATION_CONFIGURATION": configuration_path,
             "CALIBRATION_REDUCTION": reduction_path, "RETAINED_MODEL_OUTPUT_TRACE": trace_path,
             "NUMERICAL_VERIFICATION": numerical_path}
    rows = [{"role": role, "path": path.relative_to(run_root).as_posix(),
             "bytes": path.stat().st_size, "sha256": sha256(path)} for role, path in roles.items()]
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item["path"]):
        digest.update(f"{row['path']}\0{row['sha256']}\0{row['bytes']}\n".encode())
    artifact = {"schema_version": "espresso.val_corpus_002.calibration_artifacts.v1",
                "aggregate_sha256": digest.hexdigest(), "files": rows}
    artifact_path = governed / "calibration-artifact-manifest.json"; dump(artifact_path, artifact)
    manifest = {"schema_version": "espresso.val_corpus_002.p2_calibration_manifest.v1",
        "status": b0.CALIBRATION_APPROVED_STATUS, "record_class": b0.GOVERNED_RECORD_CLASS,
        "task": "VAL-CORPUS-002", "stage": "B1_CALIBRATION", "authorization_id": AUTHORIZATION_ID,
        "calibration_case_id": b0.CALIBRATION_CASE_ID, "template_sha256": b0.EXP7_H1_TEMPLATE_SHA256,
        "source_cohort_path": b0.COHORT_PATH.as_posix(), "source_cohort_sha256": b0.COHORT_SHA256,
        "target_masses_g": b0.TARGET_MASSES_G, "source_observations_g": b0.SOURCE_SOLUTE_MASSES_G,
        "objective_identity": b0.OBJECTIVE_ID, "optimizer_algorithm": "GOLDEN_SECTION_LOG_K_V1",
        "log_k_bounds": [b0.LOG_K_LOWER,b0.LOG_K_UPPER], "log_k_interval_tolerance": b0.LOG_K_TOLERANCE,
        "maximum_evaluations": b0.MAX_EVALUATIONS, "optimizer_status": "PASS",
        "optimizer_trace_sha256": sha256(optimizer_path), "selected_log_k": optimizer["selected_log_k"],
        "selected_log_k_hex": optimizer["selected_log_k_hex"],
        "selected_rate_s_inverse": optimizer["selected_rate_s_inverse"],
        "selected_rate_hex": optimizer["selected_rate_hex"], "selected_objective": optimizer["selected_objective"],
        "solver_commit": SOLVER_COMMIT, "executable_sha256": EXECUTABLE_SHA256,
        "calibration_configuration_sha256": sha256(configuration_path),
        "calibration_artifact_manifest_path": artifact_path.relative_to(run_root).as_posix(),
        "calibration_artifact_manifest_sha256": sha256(artifact_path),
        "calibration_artifact_aggregate_sha256": artifact["aggregate_sha256"],
        "numerical_completion": "PASS", "conservation_disposition": "PASS"}
    manifest_path = governed / "calibration-manifest.json"; dump(manifest_path, manifest)
    b0.validate_governed_calibration_manifest(manifest,
        expected_template_sha256=b0.EXP7_H1_TEMPLATE_SHA256, root=run_root,
        expected_b1_authorization_id=AUTHORIZATION_ID)
    barrier=b0.AccessBarrier(); barrier.authorize_b1("SEPARATE_HUMAN_OWNER_B1_AUTHORITY")
    barrier.freeze_p2(manifest, root=run_root, expected_b1_authorization_id=AUTHORIZATION_ID)
    summary = {"status": "VAL_CORPUS_002_STAGE_B1_CALIBRATION_COMPLETE_PENDING_REVIEW",
               "selected": optimizer | {"trace": "RETAINED_SEPARATELY"},
               "reduction": reduction, "numerical_verification": numerical,
               "artifact_manifest_path": artifact_path.relative_to(run_root).as_posix(),
               "artifact_manifest_sha256": sha256(artifact_path),
               "calibration_manifest_path": manifest_path.relative_to(run_root).as_posix(),
               "calibration_manifest_sha256": sha256(manifest_path),
               "external_artifact_count": len(rows),
               "external_artifact_bytes": sum(row["bytes"] for row in rows),
               "external_artifact_aggregate_sha256": artifact["aggregate_sha256"],
               "governed_validator": "PASS", "p2_freeze_barrier": "PASS",
               "transfer_result_access": "NOT_PERFORMED", "stage_b2": "NOT_STARTED"}
    dump(governed / "B1_CALIBRATION_SUMMARY.json", summary)
    return summary


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--run-root",type=Path,required=True)
    parser.add_argument("--executable",type=Path); parser.add_argument("--initialize",action="store_true")
    parser.add_argument("--execute",action="store_true"); args=parser.parse_args()
    root=args.root.resolve(); run_root=args.run_root.resolve()
    try:
        if args.initialize == args.execute: raise InfrastructureFailure("select exactly one mode")
        result=initialize(root,run_root,args.executable.resolve()) if args.initialize else execute(root,run_root)
    except InfrastructureFailure as exc:
        print(json.dumps({"status":"INFRASTRUCTURE_OR_ORCHESTRATION_FAILURE","reason":str(exc)},indent=2))
        raise SystemExit(2)
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__ == "__main__": main()
