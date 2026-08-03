#!/usr/bin/env python3
"""Prospective, case-local VAL-CORPUS-002 Stage-B0 tooling.

This module operates only on metadata, retained predecessor evidence, and
synthetic values.  It contains no OpenFOAM launcher and no source scorer.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


CASE_DIR = Path("validation/cases/val_corpus_002")
RUN_MATRIX = CASE_DIR / "VAL_CORPUS_002_FUTURE_RUN_MATRIX.json"
SENSITIVITY_MATRIX = CASE_DIR / "VAL_CORPUS_002_SENSITIVITY_MATRIX.json"
PLACEHOLDER_TOKEN = "EXACT_GLOBAL_P2_K_FROM_AUTHORIZED_CALIBRATION"
TYPED_PLACEHOLDER = {"type": "P2_EXTRACTION_RATE_S_INVERSE", "value": "UNMATERIALIZED"}
AUTHORIZATION_ID = "VAL-CORPUS-002-B0-CORRECTION-2026-08-03"
OBJECTIVE_ID = "EXP7_H1_EQUAL_WEIGHT_MEAN_SQUARED_RELATIVE_ERROR_20_40_60_G_V1"
COHORT_PATH = CASE_DIR / "VAL_CORPUS_002_COHORT_SELECTION.json"
COHORT_SHA256 = "4fd5c0e4971b9f976c0f4da707ab5f9a43e1d5131e06e3ea4c64675bc5b0b054"
TARGET_MASSES_G = [20.0, 40.0, 60.0]
SOURCE_SOLUTE_MASSES_G = [2.9240100000000004, 3.8761999999999994, 4.187098333333333]
K_LOWER = 0.011446486815650324
K_UPPER = 1.1446486815650323
LOG_K_LOWER = -4.470072424390813
LOG_K_UPPER = 0.13509776159727813
LOG_K_TOLERANCE = 1e-8
MAX_EVALUATIONS = 128
P2_BOUNDS = (K_LOWER, K_UPPER)
CALIBRATION_CASE_ID = "SCHM_EXP7_P2_FIXED_AFTER_EXP7_CALIBRATION_H1"
EXP7_H1_TEMPLATE_SHA256 = "2e688b4f9e756aa9bc3890f4eb8a05b9191f28208c1fc4a431d9a84fa3b710b8"
CALIBRATION_APPROVED_STATUS = "P2_CALIBRATION_FROZEN_APPROVED_FOR_B2_REVIEW"
SYNTHETIC_CALIBRATION_STATUS = "SYNTHETIC_B0_TEST_ONLY"
GOVERNED_RECORD_CLASS = "GOVERNED_B1_CALIBRATION"
SYNTHETIC_RECORD_CLASS = "SYNTHETIC_B0_TEST_FIXTURE"
ARTIFACT_ROLES = {
    "OPTIMIZER_TRACE", "CALIBRATION_CONFIGURATION", "CALIBRATION_REDUCTION",
    "RETAINED_MODEL_OUTPUT_TRACE", "NUMERICAL_VERIFICATION",
}
NUMERICAL_VERIFICATION_KEYS = {
    "schema_version", "task", "authorization_id", "calibration_case_id", "solver_commit",
    "executable_sha256", "calibration_configuration_sha256", "openfoam_distribution",
    "openfoam_version", "mpi_ranks", "delta_t_s", "end_time_s", "first_solver_timestamp_s",
    "final_solver_timestamp_s", "completion_disposition", "fatal_event_count",
    "target_mass_brackets", "boundedness", "maximum_liquid_balance_relative_residual",
    "maximum_solute_balance_relative_residual", "liquid_balance_gate", "solute_balance_gate",
    "trace_path", "trace_sha256", "trace_bytes", "trace_header_sha256",
    "selected_evaluation_sequence", "overall_status",
}
TRACE_REQUIRED_FIELDS = {
    "time_s", "cup_water_mass_kg", "cup_solute_mass_kg", "cup_beverage_mass_kg",
    "cumulative_inlet_water_mass_kg", "liquid_balance_residual_kg",
    "solute_balance_residual_kg", "remaining_extractable_mass_kg",
    "dissolved_in_puck_mass_kg", "min_saturation", "max_saturation",
    "min_concentration_kg_m3", "max_concentration_kg_m3",
}
MODEL_VECTOR_ABSOLUTE_TOLERANCE_G = 1e-12
OBJECTIVE_SERIALIZATION_ABSOLUTE_TOLERANCE = 1e-15
REFERENCE = {
    "binding_class": "DIRECT_CONTENT_ADDRESS",
    "normalized_path": "<WP03_002_REVIEW_ROOT>/corrected-runs-v2/cases/WASZ-9-COMPACT/postProcessing/wholePull/0/traces.csv",
    "runtime_root": "<WP03_002_REVIEW_ROOT>",
    "sha256": "bb3a5d2214b3eaf0cec2d76be0c90f56b2454cfa1982b2770841b499ed1db30a",
    "bytes": 2796444,
    "header_sha256": "27eb008688cb84f98f5b7f877aa73d745f4b3e28ce5c99f95673ed222c854831",
    "first_timestamp_s": 0.02,
    "final_timestamp_s": 29.9999999999994,
    "configuration_sha256": "09abbfdc0115a59b9452048f1ac2dcdbaf7707c91c31b166c998eab78ecf28b5",
    "executable_sha256": "e682bb63d4b54a19133a81e1dc857217132b91918ecceb33ffbc88c35b6b0fd6",
    "case_manifest_sha256": "2687a4f7b0693bf41173eecc6332e95be9e5f8cc62f7bd4957323556d45ea778",
    "scientific_input_bundle_sha256": "b4930f327466f201ddaab002373ec16e51075ea90e8621963afc056180bef770",
    "execution_record_sha256": "5a08518c0cbe6935f17b4826c473c7b494e1c4650c9efda733af903199422875",
    "build_provenance_sha256": "5a27f0b6e2e2599e1a7174f314b4f702c571b97ead262580a7a4769a52b9fcd4",
    "historical_manifest_status": "EXCLUDED_AS_DOWNSTREAM_ARTIFACT_BY_DESIGN",
}
PARITY_FIELDS = {
    "time_s": 1e-12, "inlet_pressure_Pa": 1e-6, "outlet_flow_m3_s": 1e-16,
    "cup_water_mass_kg": 1e-12, "cup_solute_mass_kg": 1e-12,
    "cup_beverage_mass_kg": 1e-12, "remaining_extractable_mass_kg": 1e-12,
    "dissolved_in_puck_mass_kg": 1e-12,
    "volumeWeightedMechanicalPorosity": 1e-12,
    "volumeWeightedPermeabilityM2": 1e-25,
}


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _replace_token(value: object) -> tuple[object, int]:
    count = 0
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            replaced, found = _replace_token(item)
            result[key] = replaced
            count += found
        return result, count
    if isinstance(value, list):
        result = []
        for item in value:
            replaced, found = _replace_token(item)
            result.append(replaced)
            count += found
        return result, count
    if value == PLACEHOLDER_TOKEN:
        return copy.deepcopy(TYPED_PLACEHOLDER), 1
    return value, 0


def typed_template(configuration: dict) -> dict:
    value, count = _replace_token(configuration)
    if count != 1:
        raise ValueError(f"P2 template requires exactly one placeholder, found {count}")
    return value


def _materialize(value: object, rate: float) -> tuple[object, int]:
    count = 0
    if isinstance(value, dict):
        if value == TYPED_PLACEHOLDER:
            return rate, 1
        result = {}
        for key, item in value.items():
            replaced, found = _materialize(item, rate)
            result[key] = replaced
            count += found
        return result, count
    if isinstance(value, list):
        result = []
        for item in value:
            replaced, found = _materialize(item, rate)
            result.append(replaced)
            count += found
        return result, count
    return value, 0


def _materialize_p2_rate(template: dict, rate: float, approved_hash: str,
                         *, bounds: tuple[float, float] = P2_BOUNDS) -> dict:
    if canonical_sha256(template) != approved_hash:
        raise ValueError("unapproved P2 template hash")
    if not math.isfinite(rate) or not bounds[0] <= rate <= bounds[1]:
        raise ValueError("P2 rate outside frozen finite bounds")
    materialized, count = _materialize(template, rate)
    if count != 1:
        raise ValueError(f"P2 template requires exactly one typed placeholder, found {count}")
    check, reverse_count = _replace_numeric_rate(materialized, rate)
    if reverse_count != 1 or check != template:
        raise ValueError("materialization changed a non-rate field")
    return materialized


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


CALIBRATION_MANIFEST_KEYS = {
    "schema_version", "status", "record_class", "task", "stage", "authorization_id",
    "calibration_case_id", "template_sha256", "source_cohort_path", "source_cohort_sha256",
    "target_masses_g", "source_observations_g", "objective_identity", "optimizer_algorithm",
    "log_k_bounds", "log_k_interval_tolerance", "maximum_evaluations", "optimizer_status",
    "optimizer_trace_sha256", "selected_log_k", "selected_log_k_hex", "selected_rate_s_inverse",
    "selected_rate_hex", "selected_objective", "solver_commit", "executable_sha256",
    "calibration_configuration_sha256", "calibration_artifact_manifest_path",
    "calibration_artifact_manifest_sha256", "calibration_artifact_aggregate_sha256",
    "numerical_completion", "conservation_disposition",
}


def _validate_manifest_envelope(manifest: dict, *, expected_template_sha256: str,
                                allow_synthetic: bool) -> float:
    if not isinstance(manifest, dict) or set(manifest) != CALIBRATION_MANIFEST_KEYS:
        raise ValueError("complete exact calibration manifest required")
    pairing = (manifest["status"], manifest["record_class"])
    governed_pair = (CALIBRATION_APPROVED_STATUS, GOVERNED_RECORD_CLASS)
    synthetic_pair = (SYNTHETIC_CALIBRATION_STATUS, SYNTHETIC_RECORD_CLASS)
    if pairing == synthetic_pair and not allow_synthetic:
        raise ValueError("synthetic calibration manifest requires explicit synthetic path")
    if pairing not in ({governed_pair, synthetic_pair} if allow_synthetic else {governed_pair}):
        raise ValueError("invalid exact status/record-class pairing")
    expected = {
        "schema_version": "espresso.val_corpus_002.p2_calibration_manifest.v1",
        "task": "VAL-CORPUS-002", "stage": "B1_CALIBRATION",
        "calibration_case_id": CALIBRATION_CASE_ID,
        "template_sha256": expected_template_sha256,
        "source_cohort_path": COHORT_PATH.as_posix(), "source_cohort_sha256": COHORT_SHA256,
        "target_masses_g": TARGET_MASSES_G, "source_observations_g": SOURCE_SOLUTE_MASSES_G,
        "objective_identity": OBJECTIVE_ID, "optimizer_algorithm": "GOLDEN_SECTION_LOG_K_V1",
        "log_k_bounds": [LOG_K_LOWER, LOG_K_UPPER],
        "log_k_interval_tolerance": LOG_K_TOLERANCE,
        "maximum_evaluations": MAX_EVALUATIONS, "optimizer_status": "PASS",
        "numerical_completion": "PASS", "conservation_disposition": "PASS",
        "solver_commit": "0a5c146078da5d5f88b344b20e7b81042bf27ddb",
        "executable_sha256": REFERENCE["executable_sha256"],
    }
    for key, value in expected.items():
        if manifest[key] != value: raise ValueError(f"calibration manifest mismatch: {key}")
    if not isinstance(manifest["authorization_id"], str) or not manifest["authorization_id"].strip():
        raise ValueError("calibration authorization identity absent")
    hash_keys = [key for key in manifest if key.endswith("_sha256")]
    if any(not _valid_sha256(manifest[key]) for key in hash_keys):
        raise ValueError("malformed lowercase SHA-256 in calibration manifest")
    values = [manifest["selected_log_k"], manifest["selected_rate_s_inverse"], manifest["selected_objective"]]
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError("nonfinite selected calibration value")
    log_k, rate = float(values[0]), float(values[1])
    if manifest["selected_objective"] < 0:
        raise ValueError("selected objective must be nonnegative")
    if not LOG_K_LOWER <= log_k <= LOG_K_UPPER or not K_LOWER <= rate <= K_UPPER:
        raise ValueError("selected calibration rate outside frozen bounds")
    if log_k.hex() != manifest["selected_log_k_hex"] or rate.hex() != manifest["selected_rate_hex"]:
        raise ValueError("selected floating-point identity mismatch")
    if not math.isclose(math.exp(log_k), rate, rel_tol=1e-15, abs_tol=0.0):
        raise ValueError("selected log-k and rate disagree")
    return rate


def _confined_regular_file(root: Path, relative: str, label: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"invalid {label} path")
    original = root / rel
    try:
        original.lstat()
    except FileNotFoundError as exc:
        raise ValueError(f"missing {label}") from exc
    if original.is_symlink() or not original.is_file():
        raise ValueError(f"{label} must be a nonsymlink regular file")
    resolved, resolved_root = original.resolve(), root.resolve()
    if resolved_root not in resolved.parents:
        raise ValueError(f"{label} escapes authorized root")
    return resolved


def _artifact_manifest_record(value: object) -> list[dict]:
    if not isinstance(value, dict) or set(value) != {"schema_version", "aggregate_sha256", "files"}:
        raise ValueError("closed calibration artifact manifest required")
    if value["schema_version"] != "espresso.val_corpus_002.calibration_artifacts.v1":
        raise ValueError("calibration artifact manifest schema mismatch")
    if not _valid_sha256(value["aggregate_sha256"]) or not isinstance(value["files"], list):
        raise ValueError("invalid calibration artifact manifest envelope")
    files = value["files"]
    if len(files) != len(ARTIFACT_ROLES):
        raise ValueError("calibration artifact manifest member count mismatch")
    for row in files:
        if (not isinstance(row, dict) or set(row) != {"role", "path", "bytes", "sha256"}
                or row["role"] not in ARTIFACT_ROLES or not isinstance(row["path"], str)
                or not isinstance(row["bytes"], int) or row["bytes"] < 0
                or not _valid_sha256(row["sha256"])):
            raise ValueError("invalid calibration artifact member")
    if {row["role"] for row in files} != ARTIFACT_ROLES or len({row["path"] for row in files}) != len(files):
        raise ValueError("calibration artifact roles and paths must be exact and unique")
    return files


def numerical_verification_schema() -> dict:
    """Closed machine-readable contract for selected B1 numerical evidence."""
    properties = {key: {} for key in sorted(NUMERICAL_VERIFICATION_KEYS)}
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "espresso.val_corpus_002.b1_numerical_verification.v1",
            "type": "object", "additionalProperties": False,
            "required": sorted(NUMERICAL_VERIFICATION_KEYS), "properties": properties}


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"numerical verification {label} must be finite")
    return float(value)


def _validate_numerical_record(record: object, manifest: dict, trace_row: dict) -> dict:
    if not isinstance(record, dict) or set(record) != NUMERICAL_VERIFICATION_KEYS:
        raise ValueError("closed numerical-verification record required")
    exact = {
        "schema_version": "espresso.val_corpus_002.b1_numerical_verification.v1",
        "task": "VAL-CORPUS-002", "authorization_id": manifest["authorization_id"],
        "calibration_case_id": CALIBRATION_CASE_ID, "solver_commit": manifest["solver_commit"],
        "executable_sha256": manifest["executable_sha256"],
        "calibration_configuration_sha256": manifest["calibration_configuration_sha256"],
        "openfoam_distribution": "OpenFOAM Foundation", "openfoam_version": "12",
        "mpi_ranks": 16, "delta_t_s": 0.02, "end_time_s": 90.0,
        "completion_disposition": "PASS", "fatal_event_count": 0,
        "target_mass_brackets": {"20_g": "PASS", "40_g": "PASS", "60_g": "PASS"},
        "overall_status": "PASS",
    }
    for key, expected in exact.items():
        if record.get(key) != expected:
            raise ValueError(f"numerical verification identity/disposition mismatch: {key}")
    if manifest["authorization_id"] == "VAL-CORPUS-002-B1-CALIBRATION-2026-08-03":
        frozen = {"calibration_configuration_sha256":
                  "d3234d976c554ad87704d9c6c00032a08b99d52c6fc61c32846e2470dff99573"}
        if any(record[key] != value for key,value in frozen.items()):
            raise ValueError("selected B1 numerical identity differs from frozen result")
        if (manifest["selected_rate_s_inverse"] != 0.3439597024835067
                or manifest["selected_log_k"] != -1.0672307724139207
                or manifest["selected_objective"] != 0.003931989579189616):
            raise ValueError("selected B1 scientific values differ from frozen result")
    if record["selected_evaluation_sequence"] != trace_row.get("sequence"):
        raise ValueError("numerical verification selected sequence mismatch")
    if not isinstance(record["trace_path"], str) or not isinstance(record["trace_bytes"], int):
        raise ValueError("numerical verification trace identity type mismatch")
    for key in ("trace_sha256", "trace_header_sha256"):
        if not _valid_sha256(record[key]): raise ValueError(f"malformed {key}")
    if set(record["boundedness"]) != {"finite", "nonnegative", "tds_0_to_1"} or any(
            not isinstance(value, bool) for value in record["boundedness"].values()):
        raise ValueError("numerical verification boundedness contract mismatch")
    for key in ("first_solver_timestamp_s", "final_solver_timestamp_s",
                "maximum_liquid_balance_relative_residual",
                "maximum_solute_balance_relative_residual", "liquid_balance_gate", "solute_balance_gate"):
        _finite_number(record[key], key)
    if record["liquid_balance_gate"] != 1e-8 or record["solute_balance_gate"] != 1e-8:
        raise ValueError("numerical conservation gate mismatch")
    if (record["maximum_liquid_balance_relative_residual"] < 0
            or record["maximum_solute_balance_relative_residual"] < 0
            or record["maximum_liquid_balance_relative_residual"] > record["liquid_balance_gate"]
            or record["maximum_solute_balance_relative_residual"] > record["solute_balance_gate"]):
        raise ValueError("numerical conservation disposition fails")
    return record


def _parse_semantic_trace(path: Path) -> tuple[list[dict[str, float]], str]:
    try:
        with path.open("rb") as raw: header = raw.readline()
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if set(TRACE_REQUIRED_FIELDS) - set(reader.fieldnames or []):
                raise ValueError("retained trace required columns absent")
            rows = []
            for raw_row in reader:
                row = {key: float(raw_row[key]) for key in TRACE_REQUIRED_FIELDS}
                if any(not math.isfinite(value) for value in row.values()):
                    raise ValueError("retained trace contains nonfinite value")
                rows.append(row)
    except (OSError, UnicodeError, csv.Error, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("retained trace"):
            raise
        raise ValueError("retained trace is not valid closed CSV") from exc
    if not rows: raise ValueError("retained trace is empty")
    if any(b["time_s"] <= a["time_s"] for a, b in zip(rows, rows[1:])):
        raise ValueError("retained trace time is not strictly increasing")
    return rows, hashlib.sha256(header).hexdigest()


def _semantic_trace_reduction(rows: list[dict[str, float]], configuration: dict) -> dict:
    samples = [(row["time_s"], row["cup_beverage_mass_kg"], row["cup_solute_mass_kg"])
               for row in rows]
    try:
        model = [1000.0 * fixed_mass(samples, target)["cup_solute_mass_kg"]
                 for target in (0.020, 0.040, 0.060)]
    except ValueError as exc:
        raise ValueError("retained trace target requires extrapolation or invalid bracketing") from exc
    cumulative = ("cup_water_mass_kg", "cup_solute_mass_kg", "cup_beverage_mass_kg",
                  "cumulative_inlet_water_mass_kg")
    if any(b[key] < a[key] - 1e-15 for key in cumulative for a, b in zip(rows, rows[1:])):
        raise ValueError("retained trace cumulative mass decreases")
    extractable = (configuration["geometry"]["dry_dose_kg"]
                   * configuration["chemistry"]["extractableFraction"])
    liquid = max(abs(row["liquid_balance_residual_kg"])
                 / max(abs(row["cumulative_inlet_water_mass_kg"]), 1e-30) for row in rows)
    solute = max(abs(row["solute_balance_residual_kg"]) / extractable for row in rows)
    finite = all(math.isfinite(value) for row in rows for value in row.values())
    nonnegative = all(row[key] >= -1e-12 for row in rows for key in
                      ("cup_water_mass_kg", "cup_solute_mass_kg", "cup_beverage_mass_kg",
                       "remaining_extractable_mass_kg", "dissolved_in_puck_mass_kg"))
    tds_values = [row["cup_solute_mass_kg"] / row["cup_beverage_mass_kg"]
                  for row in rows if row["cup_beverage_mass_kg"] > 0]
    tds_ok = bool(tds_values) and all(0 <= value <= 1 for value in tds_values)
    minimum_saturation = min(row["min_saturation"] for row in rows)
    maximum_saturation = max(row["max_saturation"] for row in rows)
    minimum_concentration = min(row["min_concentration_kg_m3"] for row in rows)
    maximum_concentration = max(row["max_concentration_kg_m3"] for row in rows)
    if minimum_saturation < -1e-12 or maximum_saturation > 1 + 1e-12:
        raise ValueError("retained trace saturation bounds fail")
    if minimum_concentration < -1e-12:
        raise ValueError("retained trace concentration is materially negative")
    residuals = [value-source for source, value in zip(SOURCE_SOLUTE_MASSES_G, model)]
    return {"model_cup_solute_masses_g": model, "signed_residuals_g": residuals,
            "relative_residuals": [value/source for value, source in zip(residuals, SOURCE_SOLUTE_MASSES_G)],
            "objective": calibration_objective(SOURCE_SOLUTE_MASSES_G, model),
            "maximum_liquid_balance_relative_residual": liquid,
            "maximum_solute_balance_relative_residual": solute,
            "boundedness": {"finite": finite, "nonnegative": nonnegative, "tds_0_to_1": tds_ok},
            "minimum_saturation": minimum_saturation, "maximum_saturation": maximum_saturation,
            "minimum_concentration_kg_m3": minimum_concentration,
            "maximum_concentration_kg_m3": maximum_concentration,
            "configured_capacity_kg_m3": configuration["chemistry"]["saturationConcentration_kg_m3"]}


def _verify_governed_contents(manifest: dict, root: Path) -> dict:
    cohort = _confined_regular_file(root, manifest["source_cohort_path"], "source cohort")
    if file_sha256(cohort) != manifest["source_cohort_sha256"]:
        raise ValueError("source cohort content identity mismatch")
    artifact = _confined_regular_file(root, manifest["calibration_artifact_manifest_path"],
                                      "calibration artifact manifest")
    if file_sha256(artifact) != manifest["calibration_artifact_manifest_sha256"]:
        raise ValueError("calibration artifact manifest content mismatch")
    try:
        artifact_record = json.loads(artifact.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("calibration artifact manifest is not valid JSON") from exc
    files = _artifact_manifest_record(artifact_record)
    if artifact_record["aggregate_sha256"] != manifest["calibration_artifact_aggregate_sha256"]:
        raise ValueError("calibration artifact aggregate mismatch")
    digest = hashlib.sha256(); members = {}
    for row in sorted(files, key=lambda item: item["path"]):
        member = _confined_regular_file(root, row["path"], f"calibration artifact {row['role']}")
        if member.stat().st_size != row["bytes"] or file_sha256(member) != row["sha256"]:
            raise ValueError(f"calibration artifact content mismatch: {row['role']}")
        digest.update(f"{row['path']}\0{row['sha256']}\0{row['bytes']}\n".encode())
        members[row["role"]] = member
    if digest.hexdigest() != artifact_record["aggregate_sha256"]:
        raise ValueError("calibration artifact manifest aggregate does not verify")

    inventory = build_configuration_inventory(root)
    template_row = next(row for row in inventory["typed_p2_templates"]
                        if row["id"] == CALIBRATION_CASE_ID)
    configuration = _materialize_p2_rate(template_row["template"],
                                         manifest["selected_rate_s_inverse"],
                                         EXP7_H1_TEMPLATE_SHA256)
    if canonical_sha256(configuration) != manifest["calibration_configuration_sha256"]:
        raise ValueError("calibration configuration cannot be reconstructed")
    config_path = members["CALIBRATION_CONFIGURATION"]
    if file_sha256(config_path) != manifest["calibration_configuration_sha256"]:
        raise ValueError("retained calibration configuration identity mismatch")

    try:
        optimizer = json.loads(members["OPTIMIZER_TRACE"].read_text(encoding="utf-8"))
        reduction = json.loads(members["CALIBRATION_REDUCTION"].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("calibration result artifacts are not valid JSON") from exc
    if file_sha256(members["OPTIMIZER_TRACE"]) != manifest["optimizer_trace_sha256"]:
        raise ValueError("optimizer trace identity mismatch")
    if (not isinstance(optimizer, dict)
            or set(optimizer) != {"status", "evaluations", "final_log_interval_width", "trace"}
            or optimizer["status"] != "PASS"
            or not isinstance(optimizer["evaluations"], int) or not 0 < optimizer["evaluations"] <= MAX_EVALUATIONS
            or not isinstance(optimizer["final_log_interval_width"], (int, float))
            or not math.isfinite(optimizer["final_log_interval_width"])
            or optimizer["final_log_interval_width"] < 0
            or optimizer["final_log_interval_width"] > LOG_K_TOLERANCE
            or not isinstance(optimizer["trace"], list)):
        raise ValueError("optimizer trace closed contract mismatch")
    selected = [row for row in optimizer["trace"] if isinstance(row, dict)
                and row.get("final_selection_status") == "SELECTED_FINAL"]
    if len(selected) != 1:
        raise ValueError("optimizer trace requires exactly one selected final row")
    selected_row = selected[0]
    selected_fields = ("selected_log_k", "selected_log_k_hex", "selected_rate_s_inverse",
                       "selected_rate_hex", "selected_objective")
    row_fields = ("log_k", "log_k_hex", "rate_s_inverse", "rate_hex", "objective")
    if any(selected_row.get(row_key) != manifest[manifest_key]
           for manifest_key, row_key in zip(selected_fields, row_fields)):
        raise ValueError("optimizer selected row disagrees with calibration manifest")

    reduction_keys = {"target_masses_g", "source_cup_solute_masses_g",
                      "model_cup_solute_masses_g", "signed_residuals_g",
                      "relative_residuals", "objective_identity", "reconstructed_objective"}
    if (not isinstance(reduction, dict)
            or set(reduction) != reduction_keys
            or reduction["target_masses_g"] != TARGET_MASSES_G
            or reduction["source_cup_solute_masses_g"] != SOURCE_SOLUTE_MASSES_G
            or reduction["objective_identity"] != OBJECTIVE_ID
            or not isinstance(reduction["model_cup_solute_masses_g"], list)
            or len(reduction["model_cup_solute_masses_g"]) != 3):
        raise ValueError("retained calibration reduction vector mismatch")
    residuals = [model-source for source, model in zip(
        SOURCE_SOLUTE_MASSES_G, reduction["model_cup_solute_masses_g"])]
    if (reduction["signed_residuals_g"] != residuals
            or reduction["relative_residuals"] != [value/source for value, source in zip(
                residuals, SOURCE_SOLUTE_MASSES_G)]):
        raise ValueError("retained calibration residual vector mismatch")
    recomputed = calibration_objective(SOURCE_SOLUTE_MASSES_G,
                                       reduction["model_cup_solute_masses_g"])
    if (not math.isclose(recomputed, reduction["reconstructed_objective"], rel_tol=0.0,
                         abs_tol=OBJECTIVE_SERIALIZATION_ABSOLUTE_TOLERANCE)
            or not math.isclose(recomputed, manifest["selected_objective"], rel_tol=0.0,
                                abs_tol=OBJECTIVE_SERIALIZATION_ABSOLUTE_TOLERANCE)):
        raise ValueError("selected objective does not reconstruct")

    try:
        numerical = json.loads(members["NUMERICAL_VERIFICATION"].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("numerical verification is not valid JSON") from exc
    numerical = _validate_numerical_record(numerical, manifest, selected_row)
    retained_trace = members["RETAINED_MODEL_OUTPUT_TRACE"]
    trace_member = next(row for row in files if row["role"] == "RETAINED_MODEL_OUTPUT_TRACE")
    if (numerical["trace_path"] != trace_member["path"]
            or numerical["trace_sha256"] != trace_member["sha256"]
            or numerical["trace_bytes"] != trace_member["bytes"]):
        raise ValueError("numerical verification and trace artifact identity disagree")
    trace_rows, header_sha256 = _parse_semantic_trace(retained_trace)
    if header_sha256 != numerical["trace_header_sha256"]:
        raise ValueError("retained trace header identity mismatch")
    if (trace_rows[0]["time_s"] != numerical["first_solver_timestamp_s"]
            or trace_rows[-1]["time_s"] != numerical["final_solver_timestamp_s"]):
        raise ValueError("retained trace terminal timestamps mismatch")
    semantic = _semantic_trace_reduction(trace_rows, configuration)
    if any(not math.isclose(actual, expected, rel_tol=0.0,
                            abs_tol=MODEL_VECTOR_ABSOLUTE_TOLERANCE_G)
           for actual, expected in zip(semantic["model_cup_solute_masses_g"],
                                       reduction["model_cup_solute_masses_g"])):
        raise ValueError("retained trace model vector mismatch")
    if manifest["authorization_id"] == "VAL-CORPUS-002-B1-CALIBRATION-2026-08-03":
        frozen_model = [2.782144673131987, 4.227214080217558, 4.334636376028199]
        if any(not math.isclose(actual, expected, rel_tol=0.0,
                                abs_tol=MODEL_VECTOR_ABSOLUTE_TOLERANCE_G)
               for actual,expected in zip(semantic["model_cup_solute_masses_g"], frozen_model)):
            raise ValueError("retained trace differs from frozen B1 model vector")
    if (not math.isclose(semantic["objective"], manifest["selected_objective"], rel_tol=0.0,
                         abs_tol=OBJECTIVE_SERIALIZATION_ABSOLUTE_TOLERANCE)
            or semantic["boundedness"] != numerical["boundedness"]):
        raise ValueError("retained trace objective or boundedness mismatch")
    for key in ("maximum_liquid_balance_relative_residual",
                "maximum_solute_balance_relative_residual"):
        if not math.isclose(semantic[key], numerical[key], rel_tol=0.0, abs_tol=1e-15):
            raise ValueError(f"retained trace {key} mismatch")
    if (semantic["maximum_liquid_balance_relative_residual"] > numerical["liquid_balance_gate"]
            or semantic["maximum_solute_balance_relative_residual"] > numerical["solute_balance_gate"]):
        raise ValueError("retained trace conservation gate fails")
    if manifest["numerical_completion"] != numerical["completion_disposition"]:
        raise ValueError("manifest numerical completion is not derived from numerical verification")
    if manifest["conservation_disposition"] != "PASS":
        raise ValueError("manifest conservation disposition mismatch")

    provenance_path = _confined_regular_file(root, "governed/recovery-provenance.json",
                                              "selected recovery provenance")
    try:
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("selected recovery provenance is not valid JSON") from exc
    provenance_keys = {"schema_version", "optimizer_sequence", "attempt_evaluation_sequence",
                       "recovery_evaluation_class", "rate_s_inverse", "rate_hex", "log_k",
                       "log_k_hex", "objective", "configuration_sha256", "trace_sha256",
                       "solver_exit_code", "evaluation_status", "evaluation_record_sha256"}
    if not isinstance(provenance, dict) or set(provenance) != provenance_keys:
        raise ValueError("closed selected recovery provenance required")
    expected_provenance = {
        "schema_version": "espresso.val_corpus_002.b1_selected_recovery_provenance.v1",
        "optimizer_sequence": selected_row.get("sequence"),
        "recovery_evaluation_class": "EXECUTED_ATTEMPT_2",
        "rate_s_inverse": manifest["selected_rate_s_inverse"], "rate_hex": manifest["selected_rate_hex"],
        "log_k": manifest["selected_log_k"], "log_k_hex": manifest["selected_log_k_hex"],
        "objective": manifest["selected_objective"],
        "configuration_sha256": manifest["calibration_configuration_sha256"],
        "trace_sha256": numerical["trace_sha256"], "solver_exit_code": 0,
        "evaluation_status": "PASS",
    }
    for key, expected in expected_provenance.items():
        if provenance.get(key) != expected:
            raise ValueError(f"selected recovery provenance mismatch: {key}")
    if (not isinstance(provenance["attempt_evaluation_sequence"], int)
            or not _valid_sha256(provenance["evaluation_record_sha256"])):
        raise ValueError("selected recovery provenance evaluation identity invalid")
    selected_evaluation_path = _confined_regular_file(root, "governed/selected-evaluation.json",
                                                       "selected evaluation record")
    if file_sha256(selected_evaluation_path) != provenance["evaluation_record_sha256"]:
        raise ValueError("selected evaluation record content identity mismatch")
    try:
        selected_evaluation = json.loads(selected_evaluation_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("selected evaluation record is not valid JSON") from exc
    selected_expected = {"sequence": provenance["attempt_evaluation_sequence"],
        "rate_s_inverse": manifest["selected_rate_s_inverse"], "rate_hex": manifest["selected_rate_hex"],
        "objective": manifest["selected_objective"], "configuration_sha256": manifest["calibration_configuration_sha256"],
        "trace_sha256": numerical["trace_sha256"], "solver_exit_code": 0, "status": "PASS",
        "cache_status": "EXECUTED_ATTEMPT_2"}
    if not isinstance(selected_evaluation, dict) or any(
            selected_evaluation.get(key) != value for key,value in selected_expected.items()):
        raise ValueError("selected evaluation record disagrees with optimizer provenance")
    return semantic


def validate_governed_calibration_manifest(manifest: dict, *, expected_template_sha256: str,
                                            root: Path,
                                            expected_b1_authorization_id: str) -> float:
    if root is None:
        raise ValueError("governed verification root is mandatory")
    if not isinstance(expected_b1_authorization_id, str) or not expected_b1_authorization_id:
        raise ValueError("expected B1 authorization identity is mandatory")
    rate = _validate_manifest_envelope(manifest, expected_template_sha256=expected_template_sha256,
                                       allow_synthetic=False)
    if manifest["authorization_id"] != expected_b1_authorization_id:
        raise ValueError("B1 authorization identity mismatch")
    _verify_governed_contents(manifest, Path(root))
    return rate


def validate_synthetic_calibration_manifest(manifest: dict, *,
                                             expected_template_sha256: str,
                                             allow_synthetic: bool) -> float:
    if not allow_synthetic:
        raise ValueError("synthetic calibration validation requires allow_synthetic=true")
    return _validate_manifest_envelope(manifest, expected_template_sha256=expected_template_sha256,
                                       allow_synthetic=True)


def materialize_p2(template: dict, calibration_manifest: dict, approved_hash: str,
                   *, root: Path, expected_b1_authorization_id: str) -> dict:
    if isinstance(calibration_manifest, (int, float)):
        raise TypeError("raw-rate P2 materialization is prohibited")
    rate = validate_governed_calibration_manifest(
        calibration_manifest, expected_template_sha256=EXP7_H1_TEMPLATE_SHA256,
        root=root, expected_b1_authorization_id=expected_b1_authorization_id)
    return _materialize_p2_rate(template, rate, approved_hash)


def materialize_p2_synthetic(template: dict, calibration_manifest: dict, approved_hash: str,
                             *, allow_synthetic: bool) -> dict:
    rate = validate_synthetic_calibration_manifest(
        calibration_manifest, expected_template_sha256=EXP7_H1_TEMPLATE_SHA256,
        allow_synthetic=allow_synthetic)
    return _materialize_p2_rate(template, rate, approved_hash)


def _replace_numeric_rate(value: object, rate: float) -> tuple[object, int]:
    if isinstance(value, dict):
        result, count = {}, 0
        for key, item in value.items():
            if key in {"extractionRateConstant_s_inverse", "rate_constant_1_s", "token"} and item == rate:
                result[key], found = copy.deepcopy(TYPED_PLACEHOLDER), 1
            else:
                result[key], found = _replace_numeric_rate(item, rate)
            count += found
        return result, count
    if isinstance(value, list):
        result, count = [], 0
        for item in value:
            replaced, found = _replace_numeric_rate(item, rate)
            result.append(replaced); count += found
        return result, count
    return value, 0


def build_configuration_inventory(root: Path) -> dict:
    matrix = json.loads((root / RUN_MATRIX).read_text())
    sensitivity = json.loads((root / SENSITIVITY_MATRIX).read_text())
    production = matrix["final_production_run_inventory"]
    numeric, templates = [], []
    for record in production:
        config = copy.deepcopy(record.get("configuration", record))
        identity = record.get("id", record.get("run_id"))
        if record["parameterization"].startswith("P2"):
            config = typed_template(config)
            templates.append({"id": identity, "canonical_sha256": canonical_sha256(config),
                              "template": config})
        else:
            numeric.append({"id": identity, "parameterization": record["parameterization"],
                            "canonical_sha256": canonical_sha256(config), "configuration": config})
    sens = [{"id": row["run_id"], "reuse": row["run_id"] == "SENS_BASELINE",
             "canonical_sha256": canonical_sha256(row), "configuration": row}
            for row in sensitivity["future_runs"]]
    calibration = next(row for row in templates if row["id"] == "SCHM_EXP7_P2_FIXED_AFTER_EXP7_CALIBRATION_H1")
    if (len(production), len(numeric), len(templates), len(sens)) != (45, 30, 15, 9):
        raise ValueError("frozen configuration inventory count mismatch")
    if sum(item["id"].startswith("SCHM_") for item in templates) != 14:
        raise ValueError("Schmieder P2 template count mismatch")
    return {
        "schema_version": 1,
        "canonicalization": "UTF8_SORTED_KEYS_COMPACT_SEPARATORS_NO_NONFINITE_TERMINAL_NEWLINE",
        "counts": {"final_production_identities": 45, "numeric_p0_p1": 30,
                   "typed_p2_templates": 15, "schmieder_p2_templates": 14,
                   "waszkiewicz_p2_templates": 1, "sensitivity_identities": 9,
                   "sensitivity_new_executions_if_reuse_valid": 8,
                   "optimizer_maximum_evaluations": 128},
        "numeric_configurations": numeric, "typed_p2_templates": templates,
        "sensitivity_configurations": sens,
        "experiment_7_h1_calibration_template": {
            "id": calibration["id"], "canonical_sha256": calibration["canonical_sha256"]},
    }


def bind_calibration_source(root: Path) -> dict:
    path = root / COHORT_PATH
    if not path.is_file() or path.is_symlink() or file_sha256(path) != COHORT_SHA256:
        raise ValueError("Experiment-7 source cohort identity mismatch")
    record = json.loads(path.read_text())
    rows = [row for row in record.get("summaries", []) if row.get("experiment") == 7]
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("Experiment-7 source vector must contain exactly three rows")
    rows = sorted(rows, key=lambda row: row["target_beverage_mass_g"])
    targets = [row["target_beverage_mass_g"] for row in rows]
    values = [row["replicate_mean_tds_mass_g"] for row in rows]
    if targets != TARGET_MASSES_G or values != SOURCE_SOLUTE_MASSES_G:
        raise ValueError("Experiment-7 ordered calibration vector mismatch")
    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise ValueError("calibration source denominators must be finite and positive")
    return {"source_cohort_path": COHORT_PATH.as_posix(), "source_cohort_sha256": COHORT_SHA256,
            "target_masses_g": targets, "source_observations_g": values,
            "objective_identity": OBJECTIVE_ID,
            "replicate_statistics": rows}


def bind_reference(root: Path, review_root: Path) -> dict:
    rel = Path("corrected-runs-v2/cases/WASZ-9-COMPACT/postProcessing/wholePull/0/traces.csv")
    path = review_root / rel
    if not path.is_file() or path.is_symlink():
        raise ValueError("reference trace must be a regular retained file")
    with path.open("rb") as raw:
        header = raw.readline()
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        missing = set(PARITY_FIELDS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing parity fields: {sorted(missing)}")
        first = next(reader); final = first
        rows = 1
        for final in reader: rows += 1
    observed = {"sha256": file_sha256(path), "bytes": path.stat().st_size,
                "header_sha256": hashlib.sha256(header).hexdigest(),
                "first_timestamp_s": float(first["time_s"]),
                "final_timestamp_s": float(final["time_s"])}
    for key, expected in ((key, REFERENCE[key]) for key in observed):
        if observed[key] != expected:
            raise ValueError(f"reference {key} mismatch: {observed[key]} != {expected}")
    return {**REFERENCE, "trace_rows": rows, "required_fields": list(PARITY_FIELDS),
            "field_absolute_tolerances": PARITY_FIELDS,
            "common_domain_s": [0.02, 29.9999999999994],
            "final_timestamp_accepted_as_30s_tolerance_s": 1e-12,
            "parity_t0_insertion": "PROHIBITED",
            "initial_state_check": "EXACT_IDENTITIES_SEPARATE_FROM_TRACE"}


def verify_initial_state(actual: dict, expected: dict) -> None:
    required = {"simulation_start_time_s", "initial_fields_sha256", "configuration_sha256",
                "geometry_mesh_sha256", "executable_sha256", "chemistry_sha256",
                "pressure_ramp_controls_sha256", "timestep_controls_sha256",
                "numerical_controls_sha256"}
    if set(actual) != required or set(expected) != required or actual != expected:
        raise ValueError("initial-state exact identity check failed")


def _interpolated(row0: dict[str, float], row1: dict[str, float], time_s: float,
                  field: str) -> float:
    fraction = (time_s - row0["time_s"]) / (row1["time_s"] - row0["time_s"])
    return row0[field] + fraction * (row1[field] - row0[field])


def compare_parity(reference: list[dict[str, float]], candidate: list[dict[str, float]],
                   *, required_reference_count: int | None = None) -> dict:
    if not reference or not candidate or any(row["time_s"] == 0 for row in reference):
        raise ValueError("parity requires retained nonzero reference rows")
    for rows in (reference, candidate):
        if any(b["time_s"] <= a["time_s"] for a, b in zip(rows, rows[1:])):
            raise ValueError("parity timestamps must be strictly increasing")
    failures, compared = [], 0
    index = 0
    for ref in reference:
        time_s = ref["time_s"]
        if time_s < 0.02 or time_s > 29.9999999999994:
            continue
        while index + 1 < len(candidate) and candidate[index + 1]["time_s"] <= time_s:
            index += 1
        if candidate[index]["time_s"] == time_s:
            values = candidate[index]
        elif index + 1 < len(candidate) and candidate[index]["time_s"] < time_s < candidate[index + 1]["time_s"]:
            values = {field: _interpolated(candidate[index], candidate[index + 1], time_s, field)
                      for field in PARITY_FIELDS if field != "time_s"}
            values["time_s"] = time_s
        else:
            raise ValueError("candidate does not bracket reference; extrapolation prohibited")
        for field, absolute in PARITY_FIELDS.items():
            observed, expected = values[field], ref[field]
            if not math.isfinite(observed) or not math.isfinite(expected):
                raise ValueError("nonfinite parity value")
            error = abs(observed - expected)
            if error > absolute + 1e-10 * abs(expected):
                failures.append({"time_s": time_s, "field": field, "absolute_error": error})
        compared += 1
    if required_reference_count is not None and (len(reference) != required_reference_count or compared != required_reference_count):
        raise ValueError("predecessor parity requires the complete retained reference")
    return {"status": "PASS" if not failures else "FAIL", "compared_reference_states": compared,
            "failures": failures, "domain_s": [0.02, 29.9999999999994]}


def _read_parity_csv(path: Path) -> list[dict[str, float]]:
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if set(PARITY_FIELDS) - set(reader.fieldnames or []):
            raise ValueError("parity trace field mismatch")
        return [{field: float(row[field]) for field in PARITY_FIELDS} for row in reader]


def compare_bound_predecessor_parity(reference_path: Path,
                                     candidate: list[dict[str, float]]) -> dict:
    if reference_path.is_symlink() or not reference_path.is_file():
        raise ValueError("accepted predecessor trace unavailable")
    if file_sha256(reference_path) != REFERENCE["sha256"]:
        raise ValueError("accepted predecessor content identity mismatch")
    reference = _read_parity_csv(reference_path)
    if (len(reference) != 1500 or reference[0]["time_s"] != REFERENCE["first_timestamp_s"]
            or reference[-1]["time_s"] != REFERENCE["final_timestamp_s"]):
        raise ValueError("accepted predecessor coverage mismatch")
    return compare_parity(reference, candidate, required_reference_count=1500)


def external_inventory(root: Path, files: Iterable[Path]) -> dict:
    records = []
    root = root.resolve()
    seen: dict[Path, Path] = {}
    for original in sorted(list(files), key=lambda path: os.fspath(path)):
        try:
            original.lstat()
        except FileNotFoundError as exc:
            raise ValueError("artifact path is missing") from exc
        if original.is_symlink():
            raise ValueError("artifact symlink rejected before resolution")
        path = original.resolve()
        if not path.is_file() or root not in path.parents:
            raise ValueError("artifact must be a regular file below the declared root")
        if path in seen:
            raise ValueError(f"duplicate artifact alias: {original} and {seen[path]}")
        seen[path] = original
        records.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
                        "sha256": file_sha256(path)})
    digest = hashlib.sha256()
    for row in records:
        digest.update(f"{row['path']}\0{row['sha256']}\0{row['bytes']}\n".encode())
    return {"file_count": len(records), "total_bytes": sum(r["bytes"] for r in records),
            "aggregate_sha256": digest.hexdigest(), "files": records}


def fixed_mass(samples: list[tuple[float, float, float]], target: float) -> dict:
    from val_corpus_002_protocol import interpolate_fixed_mass
    solute = interpolate_fixed_mass(samples, target)
    return {"target_beverage_mass_kg": target, "cup_solute_mass_kg": solute,
            "tds_fraction": solute / target}


def interval_chemistry_raw(samples: list[dict[str, float]], liquid_density_kg_m3: float,
                           start: float, end: float,
                           initial: dict[str, float] | None = None) -> float:
    from val_corpus_002_protocol import ensure_initial_boundary_sample, interval_tds
    if not math.isfinite(liquid_density_kg_m3) or liquid_density_kg_m3 <= 0:
        raise ValueError("exact positive liquid density required")
    required = {"time_s", "outlet_flow_m3_s", "totalSoluteFluxKgS"}
    work = []
    for row in samples:
        if set(row) != required:
            raise ValueError("production interval reducer accepts raw trace fields only")
        flow, solute = row["outlet_flow_m3_s"], row["totalSoluteFluxKgS"]
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (row["time_s"], flow, solute)):
            raise ValueError("nonfinite raw interval field")
        water = liquid_density_kg_m3 * flow
        rates = [water, solute]
        for index, value in enumerate(rates):
            if value < -1e-15: raise ValueError("materially negative interval mass rate")
            if value < 0: rates[index] = 0.0
        work.append({"time_s": row["time_s"], "water_mass_rate_kg_s": rates[0],
                     "solute_mass_rate_kg_s": rates[1]})
    if start == 0 and (not work or work[0]["time_s"] > 0):
        if initial is None:
            raise ValueError("exact initial state required for zero boundary")
        work = ensure_initial_boundary_sample(work, **initial)
    triples = [(row["time_s"], row["solute_mass_rate_kg_s"],
                row["water_mass_rate_kg_s"] + row["solute_mass_rate_kg_s"]) for row in work]
    return interval_tds(triples, start, end)


def interval_chemistry(*args, **kwargs):
    raise TypeError("precomputed mass-rate interval API is non-production and prohibited")


@dataclass
class Evaluation:
    sequence: int
    log_k: float
    rate_s_inverse: float
    objective: float | None
    status: str
    reason: str | None
    cache_hit: bool


class TypedNumericalEvaluationFailure(Exception):
    """Affirmative model-output failure eligible for optimizer accounting."""


class OptimizerEvaluationLimit(Exception):
    """Internal control signal for the frozen evaluation ceiling."""


def golden_section_log_k(objective: Callable[[float], float], *,
                         max_evaluations: int = MAX_EVALUATIONS) -> dict:
    """Exact frozen golden-section mechanics in x=log(k), synthetic in B0."""
    if not 1 <= max_evaluations <= MAX_EVALUATIONS:
        raise ValueError("invalid optimizer evaluation limit")
    cache: dict[str, Evaluation] = {}; trace: list[dict] = []; evaluations = 0
    context = {"active_log_lower": LOG_K_LOWER, "active_log_upper": LOG_K_UPPER,
               "active_interior_log_low": None, "active_interior_log_high": None,
               "decision": "INITIALIZE"}
    def trace_row(item: Evaluation, cache_hit: bool) -> dict:
        return {"sequence": len(trace), "log_k": item.log_k, "log_k_hex": item.log_k.hex(),
                "rate_s_inverse": item.rate_s_inverse, "rate_hex": item.rate_s_inverse.hex(),
                "objective": item.objective, "evaluation_status": item.status,
                "failure_reason": item.reason, "cache_hit": cache_hit, **context,
                "final_selection_status": "NOT_FINAL"}
    def evaluate(log_k: float) -> Evaluation:
        nonlocal evaluations
        key = log_k.hex()
        if key in cache:
            prior = cache[key]
            trace.append(trace_row(prior, True))
            return prior
        if evaluations >= max_evaluations:
            raise OptimizerEvaluationLimit("evaluation limit exhausted")
        rate = math.exp(log_k)
        try:
            value = float(objective(rate))
            if not math.isfinite(value):
                raise TypedNumericalEvaluationFailure("NONFINITE_OBJECTIVE")
            status, reason = "PASS", None
        except TypedNumericalEvaluationFailure as exc:
            value, status, reason = None, "FAILED_EVALUATION", str(exc)
        item = Evaluation(len(trace), log_k, rate, value, status, reason, False)
        cache[key] = item; evaluations += 1
        trace.append(trace_row(item, False))
        return item
    phi = (1 + math.sqrt(5.0)) / 2.0
    a, b = LOG_K_LOWER, LOG_K_UPPER
    c, d = b - (b-a)/phi, a + (b-a)/phi
    context.update(active_interior_log_low=min(c, d), active_interior_log_high=max(c, d))
    exhausted = False
    try:
        ec, ed = evaluate(min(c, d)), evaluate(max(c, d))
        while b-a > LOG_K_TOLERANCE:
            vc = math.inf if ec.objective is None else ec.objective
            vd = math.inf if ed.objective is None else ed.objective
            if vc <= vd:  # equality retains lower interval and implements lower-k tie break
                b, d, ed = d, c, ec; c = b - (b-a)/phi
                context.update(active_log_lower=a, active_log_upper=b,
                               active_interior_log_low=min(c, d), active_interior_log_high=max(c, d),
                               decision="RETAIN_LOWER_K_INTERVAL")
                ec = evaluate(c)
            else:
                a, c, ec = c, d, ed; d = a + (b-a)/phi
                context.update(active_log_lower=a, active_log_upper=b,
                               active_interior_log_low=min(c, d), active_interior_log_high=max(c, d),
                               decision="RETAIN_UPPER_K_INTERVAL")
                ed = evaluate(d)
        context.update(active_log_lower=a, active_log_upper=b,
                       decision="EVALUATE_FROZEN_BOUNDARIES_FOR_FINAL_SELECTION")
        evaluate(LOG_K_LOWER); evaluate(LOG_K_UPPER)
    except OptimizerEvaluationLimit:
        exhausted = True
    valid = [item for item in cache.values() if item.objective is not None]
    if not valid:
        return {"status": "FAIL_NO_VALID_EVALUATION", "evaluations": evaluations, "trace": trace}
    best = min(valid, key=lambda item: (item.objective, item.rate_s_inverse))
    for row in trace:
        if row["log_k_hex"] == best.log_k.hex() and not row["cache_hit"]:
            row["final_selection_status"] = "SELECTED_FINAL"; break
    status = "NONCONVERGED_EVALUATION_LIMIT" if exhausted else "PASS"
    return {"status": status, "evaluations": evaluations,
            "selected_log_k": best.log_k, "selected_log_k_hex": best.log_k.hex(),
            "selected_rate_s_inverse": best.rate_s_inverse,
            "selected_rate_hex": best.rate_s_inverse.hex(),
            "selected_objective": best.objective, "lower_rate_tie_break": True,
            "final_log_interval_width": b-a, "trace": trace}


def production_metrics(source: list[float], model: list[float], sd: list[float | None]) -> dict:
    if not (len(source) == len(model) == len(sd)) or not source:
        raise ValueError("metric vectors must have equal nonzero length")
    values = [*source, *model, *(value for value in sd if value is not None)]
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError("metric vectors must be finite")
    if any(s <= 0 for s in source):
        raise ValueError("source denominator must be positive")
    residuals = [m-s for s, m in zip(source, model)]
    return {"absolute_error": [abs(x) for x in residuals],
            "relative_error": [None if s == 0 else (m-s)/s for s, m in zip(source, model)],
            "rmse": math.sqrt(sum(x*x for x in residuals)/len(residuals)),
            "mae": sum(abs(x) for x in residuals)/len(residuals),
            "bias": sum(residuals)/len(residuals),
            "standardized_residual": [None if v is None or v <= 0 else r/v for r, v in zip(residuals, sd)]}


def replicate_binding(values: list[float]) -> dict:
    if not values or any(not math.isfinite(v) for v in values):
        raise ValueError("finite source replicates required")
    return {"mean": statistics.mean(values), "sample_sd": statistics.stdev(values) if len(values) > 1 else None,
            "range": [min(values), max(values)], "count": len(values)}


def schmieder_three_mass_reduction(source: list[float], model: list[float],
                                   replicate_values: list[list[float]]) -> dict:
    if len(source) != 3 or len(model) != 3 or len(replicate_values) != 3:
        raise ValueError("three-mass reduction requires three targets")
    bindings = [replicate_binding(values) for values in replicate_values]
    metrics = production_metrics(source, model, [row["sample_sd"] for row in bindings])
    counts = []
    for value, binding in zip(model, bindings):
        sd = binding["sample_sd"]
        counts.append({"within_observed_range": binding["range"][0] <= value <= binding["range"][1],
                       "within_one_source_sd": None if sd is None else abs(value-binding["mean"]) <= sd,
                       "within_two_source_sd": None if sd is None else abs(value-binding["mean"]) <= 2*sd})
    return {"target_masses_g": TARGET_MASSES_G, "source_g": source, "model_g": model,
            "replicate_statistics": bindings, "metrics": metrics, "within_counts": counts,
            "count_within_observed_range": sum(row["within_observed_range"] for row in counts),
            "count_within_one_source_sd": sum(row["within_one_source_sd"] is True for row in counts),
            "count_within_two_source_sd": sum(row["within_two_source_sd"] is True for row in counts)}


def paired_error_ratio(native_error: float, conditioned_error: float) -> dict:
    if any(not math.isfinite(v) or v < 0 for v in (native_error, conditioned_error)):
        raise ValueError("paired errors must be finite and nonnegative")
    if conditioned_error == 0:
        return {"ratio": None, "disposition": "UNDEFINED_ZERO_DENOMINATOR_WITH_PAIRED_ERRORS_REPORTED",
                "native_error": native_error, "source_conditioned_error": conditioned_error}
    return {"ratio": native_error/conditioned_error, "disposition": "DEFINED",
            "native_error": native_error, "source_conditioned_error": conditioned_error}


def all_axis_contrasts(cases: dict[str, list[float]]) -> dict:
    pairs = {"FLOW_HIGH_MINUS_LOW": ("HIGH_FLOW", "LOW_FLOW"),
             "GRIND_COARSE_MINUS_FINE": ("COARSE_GRIND", "FINE_GRIND"),
             "TEMPERATURE_HIGH_MINUS_LOW": ("HIGH_TEMPERATURE", "LOW_TEMPERATURE")}
    if set(cases) != {name for pair in pairs.values() for name in pair}:
        raise ValueError("all six frozen axis endpoints required")
    if any(len(values) != 3 for values in cases.values()):
        raise ValueError("every axis endpoint requires all three brew ratios")
    return {name: dict(zip(("1/1", "1/2", "1/3"), axis_contrast(cases[hi], cases[lo])))
            for name, (hi, lo) in pairs.items()}


def waszkiewicz_series_metrics(source: list[float], model: list[float],
                               windows: dict[str, list[int]],
                               uncertainty: list[float | None] | None = None) -> dict:
    if not source or len(source) != len(model) or any(not math.isfinite(v) for v in [*source, *model]):
        raise ValueError("finite paired Waszkiewicz series required")
    residuals = [m-s for s, m in zip(source, model)]
    required_windows = {"early", "middle", "late"}
    if set(windows) != required_windows or sorted(i for values in windows.values() for i in values) != list(range(len(source))):
        raise ValueError("complete disjoint early/middle/late windows required")
    result = {"rmse": math.sqrt(sum(r*r for r in residuals)/len(residuals)),
              "mae": sum(abs(r) for r in residuals)/len(residuals),
              "bias": statistics.mean(residuals),
              "window_mean_residual": {name: statistics.mean(residuals[i] for i in indices)
                                       for name, indices in windows.items()}}
    weighted = []
    if uncertainty is not None:
        if len(uncertainty) != len(source): raise ValueError("uncertainty vector length mismatch")
        for residual, sigma in zip(residuals, uncertainty):
            if sigma is None: continue
            if not math.isfinite(sigma) or sigma <= 0: raise ValueError("supplied uncertainty must be positive")
            weighted.append((residual, sigma))
    result["uncertainty_weighted_secondary"] = (None if not weighted else {
        "weighted_mse": sum((r/s)**2 for r, s in weighted)/len(weighted), "count": len(weighted)})
    return result


def axis_contrast(high: list[float], low: list[float]) -> list[float]:
    if len(high) != len(low): raise ValueError("axis vectors differ")
    return [a-b for a, b in zip(high, low)]


def finite_range_sensitivity(low_p: float, high_p: float,
                             low_y: list[float], high_y: list[float]) -> list[float]:
    values = [low_p, high_p, *low_y, *high_y]
    if any(not math.isfinite(v) or v <= 0 for v in values) or len(low_y) != len(high_y):
        raise ValueError("finite-range sensitivity requires positive finite paired values")
    denominator = math.log(high_p)-math.log(low_p)
    return [(math.log(hi)-math.log(lo))/denominator for lo, hi in zip(low_y, high_y)]


def _symmetric_eigenvalues_3x3(matrix: list[list[float]]) -> list[float]:
    a = [row[:] for row in matrix]
    for _ in range(64):
        p, q = max(((i, j) for i in range(3) for j in range(i+1, 3)), key=lambda ij: abs(a[ij[0]][ij[1]]))
        if abs(a[p][q]) <= 1e-15: break
        angle = .5 * math.atan2(2*a[p][q], a[q][q]-a[p][p]); c, s = math.cos(angle), math.sin(angle)
        app, aqq, apq = a[p][p], a[q][q], a[p][q]
        a[p][p] = c*c*app - 2*s*c*apq + s*s*aqq
        a[q][q] = s*s*app + 2*s*c*apq + c*c*aqq; a[p][q] = a[q][p] = 0.0
        for r in range(3):
            if r in (p, q): continue
            arp, arq = a[r][p], a[r][q]
            a[r][p] = a[p][r] = c*arp - s*arq
            a[r][q] = a[q][r] = s*arp + c*arq
    return sorted((max(0.0, a[i][i]) for i in range(3)), reverse=True)


def sensitivity_matrix(parameter_cases: dict[str, dict[str, object]], *,
                       absolute_rank_tolerance: float = 1e-12,
                       relative_rank_tolerance: float = 1e-10) -> dict:
    if len(parameter_cases) != 4:
        raise ValueError("complete four-parameter sensitivity set required")
    parameters = sorted(parameter_cases)
    columns = []
    for name in parameters:
        row = parameter_cases[name]
        columns.append(finite_range_sensitivity(float(row["low_parameter"]), float(row["high_parameter"]),
                                                list(row["low_outputs"]), list(row["high_outputs"])))
    if any(len(column) != 3 for column in columns): raise ValueError("three outputs required per parameter")
    matrix = [[columns[col][row] for col in range(4)] for row in range(3)]
    gram = [[sum(matrix[i][k]*matrix[j][k] for k in range(4)) for j in range(3)] for i in range(3)]
    singular = [math.sqrt(v) for v in _symmetric_eigenvalues_3x3(gram)]
    threshold = max(absolute_rank_tolerance, relative_rank_tolerance*(singular[0] if singular else 0.0))
    rank = sum(value > threshold for value in singular)
    correlations = {}
    for i, left in enumerate(parameters):
        correlations[left] = {}
        for j, right in enumerate(parameters):
            x, y = columns[i], columns[j]; mx, my = statistics.mean(x), statistics.mean(y)
            numerator = sum((a-mx)*(b-my) for a, b in zip(x, y))
            denominator = math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
            correlations[left][right] = None if denominator == 0 else numerator/denominator
    return {"parameters": parameters, "outputs": 3, "matrix": matrix, "singular_values": singular,
            "absolute_rank_tolerance": absolute_rank_tolerance,
            "relative_rank_tolerance": relative_rank_tolerance, "rank_threshold": threshold,
            "rank": rank, "rank_ceiling": 3, "parameter_correlations": correlations,
            "equifinality_warning": rank < 4, "claim": "NOT_STRUCTURAL_IDENTIFIABILITY"}


def calibration_objective(source: list[float], model: list[float]) -> float:
    """Frozen Experiment-7/H1 equal-weight mean squared relative error."""
    if len(source) != 3 or len(model) != 3:
        raise ValueError("calibration objective requires exactly three masses")
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in source):
        raise ValueError("calibration source denominators must be finite and positive")
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in model):
        raise ValueError("calibration model values must be finite and nonnegative")
    return sum(((m-s)/s)**2 for s, m in zip(source, model)) / 3.0


def calibration_evaluation(rate: float, model: list[float], source_binding: dict) -> dict:
    if source_binding.get("objective_identity") != OBJECTIVE_ID:
        raise ValueError("calibration objective identity mismatch")
    objective = calibration_objective(source_binding["source_observations_g"], model)
    return {"rate_s_inverse": rate, "rate_hex": rate.hex(), "model_values_g": model,
            "source_values_g": source_binding["source_observations_g"],
            "objective_identity": OBJECTIVE_ID, "objective": objective}


def source_species_limitation_audit(named_species: dict[str, list[float]],
                                    aggregate_tds: list[float]) -> dict:
    if not aggregate_tds or any(not math.isfinite(x) or x < 0 for x in aggregate_tds):
        raise ValueError("invalid aggregate source series")
    for name, values in named_species.items():
        if not name or len(values) != len(aggregate_tds) or any(not math.isfinite(x) or x < 0 for x in values):
            raise ValueError("invalid named-species source series")
    return {"status": "SOURCE_ONLY_SPECIES_LIMITATION_AUDIT",
            "named_species": sorted(named_species),
            "solver_predicted_named_species": False,
            "aggregate_residual_attribution": "NOT_IDENTIFIED",
            "multispecies_physics_authorized": False}


class AccessBarrier:
    def __init__(self) -> None:
        self.state = "B0_SYNTHETIC_ONLY"; self.p2_rate = None
    def authorize_b1(self, authority: str) -> None:
        if authority != "SEPARATE_HUMAN_OWNER_B1_AUTHORITY": raise PermissionError("B1 authority absent")
        self.state = "B1_EXP7_H1_ONLY"
    def require_result_access(self, case: str, *, protected: bool = False) -> None:
        if protected: raise PermissionError("protected scoring is prohibited")
        if self.state == "B0_SYNTHETIC_ONLY": raise PermissionError("model-result access prohibited in B0")
        if case != "SCHM_EXP7_P2_FIXED_AFTER_EXP7_CALIBRATION_H1":
            raise PermissionError("transfer result inaccessible before exact P2 freeze")
    def freeze_p2(self, manifest: dict, *, root: Path,
                  expected_b1_authorization_id: str) -> None:
        if self.state != "B1_EXP7_H1_ONLY":
            raise PermissionError("exact B1 P2 manifest required")
        if manifest.get("optimizer_status") != "PASS":
            raise PermissionError("nonconverged optimizer cannot freeze P2")
        try:
            rate = validate_governed_calibration_manifest(
                manifest, expected_template_sha256=EXP7_H1_TEMPLATE_SHA256,
                root=root, expected_b1_authorization_id=expected_b1_authorization_id)
        except ValueError as exc:
            raise PermissionError("invalid exact P2 freeze") from exc
        self.p2_rate = rate; self.state = "P2_FROZEN_TRANSFER_MAY_FOLLOW_SEPARATE_B2_AUTHORITY"
    @staticmethod
    def validate_action(action: str, case_id: str) -> None:
        allowed = {("VERIFY_METADATA", CALIBRATION_CASE_ID),
                   ("LOAD_B1_CALIBRATION_RESULT", CALIBRATION_CASE_ID),
                   ("REDUCE_B1_CALIBRATION_OBJECTIVE", CALIBRATION_CASE_ID)}
        if (action, case_id) not in allowed:
            raise PermissionError("action/case pair is not on the exact B1 allowlist")


def materialize_all_p2(inventory: dict, manifest: dict, *, root: Path,
                       expected_b1_authorization_id: str) -> dict:
    templates = inventory.get("typed_p2_templates")
    if not isinstance(templates, list) or len(templates) != 15:
        raise ValueError("all 15 P2 templates required")
    rate = validate_governed_calibration_manifest(
        manifest, expected_template_sha256=EXP7_H1_TEMPLATE_SHA256, root=root,
        expected_b1_authorization_id=expected_b1_authorization_id)
    results = {}
    for row in templates:
        results[row["id"]] = materialize_p2(
            row["template"], manifest, row["canonical_sha256"], root=root,
            expected_b1_authorization_id=expected_b1_authorization_id)
    return {"manifest_bound_rate_s_inverse": rate, "materialized_count": len(results),
            "identical_rate_all_templates": True, "configurations": results}


def materialize_all_p2_synthetic(inventory: dict, manifest: dict, *,
                                 allow_synthetic: bool) -> dict:
    templates = inventory.get("typed_p2_templates")
    if not isinstance(templates, list) or len(templates) != 15:
        raise ValueError("all 15 P2 templates required")
    rate = validate_synthetic_calibration_manifest(
        manifest, expected_template_sha256=EXP7_H1_TEMPLATE_SHA256,
        allow_synthetic=allow_synthetic)
    results = {row["id"]: materialize_p2_synthetic(
        row["template"], manifest, row["canonical_sha256"], allow_synthetic=allow_synthetic)
        for row in templates}
    return {"manifest_bound_rate_s_inverse": rate, "materialized_count": len(results),
            "identical_rate_all_templates": True, "configurations": results}


def calibration_manifest_schema() -> dict:
    properties = {key: {} for key in sorted(CALIBRATION_MANIFEST_KEYS)}
    for key in ("schema_version", "status", "record_class", "task", "stage", "authorization_id",
                "calibration_case_id", "template_sha256", "source_cohort_path", "source_cohort_sha256",
                "objective_identity", "optimizer_algorithm", "optimizer_status", "optimizer_trace_sha256",
                "selected_log_k_hex", "selected_rate_hex", "solver_commit", "executable_sha256",
                "calibration_configuration_sha256", "calibration_artifact_manifest_path",
                "calibration_artifact_manifest_sha256", "calibration_artifact_aggregate_sha256",
                "numerical_completion", "conservation_disposition"):
        properties[key] = {"type": "string"}
    for key in ("selected_log_k", "selected_rate_s_inverse", "selected_objective",
                "log_k_interval_tolerance"):
        properties[key] = {"type": "number"}
    properties["maximum_evaluations"] = {"type": "integer"}
    for key in ("target_masses_g", "source_observations_g", "log_k_bounds"):
        properties[key] = {"type": "array", "items": {"type": "number"}}
    properties["status"] = {"enum": [CALIBRATION_APPROVED_STATUS, SYNTHETIC_CALIBRATION_STATUS]}
    properties["record_class"] = {"enum": [GOVERNED_RECORD_CLASS, SYNTHETIC_RECORD_CLASS]}
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "espresso.val_corpus_002.p2_calibration_manifest.v1",
            "type": "object", "additionalProperties": False,
            "required": sorted(CALIBRATION_MANIFEST_KEYS), "properties": properties,
            "oneOf": [
                {"properties": {"status": {"const": CALIBRATION_APPROVED_STATUS},
                                "record_class": {"const": GOVERNED_RECORD_CLASS}}},
                {"properties": {"status": {"const": SYNTHETIC_CALIBRATION_STATUS},
                                "record_class": {"const": SYNTHETIC_RECORD_CLASS}}},
            ]}


def calibration_artifact_manifest_schema() -> dict:
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "espresso.val_corpus_002.calibration_artifacts.v1",
            "type": "object", "additionalProperties": False,
            "required": ["schema_version", "aggregate_sha256", "files"],
            "properties": {
                "schema_version": {"const": "espresso.val_corpus_002.calibration_artifacts.v1"},
                "aggregate_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                "files": {"type": "array", "minItems": 5, "maxItems": 5,
                          "items": {"type": "object", "additionalProperties": False,
                                    "required": ["role", "path", "bytes", "sha256"],
                                    "properties": {
                                        "role": {"enum": sorted(ARTIFACT_ROLES)},
                                        "path": {"type": "string", "minLength": 1},
                                        "bytes": {"type": "integer", "minimum": 0},
                                        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}}}}}


def generate(root: Path, review_root: Path) -> None:
    inventory = build_configuration_inventory(root)
    binding = bind_reference(root, review_root)
    source_binding = bind_calibration_source(root)
    dump(root / CASE_DIR / "VAL_CORPUS_002_STAGE_B0_CONFIGURATION_INVENTORY.json", inventory)
    dump(root / CASE_DIR / "VAL_CORPUS_002_PREDECESSOR_PARITY_REFERENCE_BINDING.json", binding)
    dump(root / CASE_DIR / "VAL_CORPUS_002_EXP7_H1_CALIBRATION_SOURCE_BINDING.json", source_binding)
    dump(root / CASE_DIR / "VAL_CORPUS_002_P2_CALIBRATION_MANIFEST_SCHEMA.json",
         calibration_manifest_schema())
    dump(root / CASE_DIR / "VAL_CORPUS_002_CALIBRATION_ARTIFACT_MANIFEST_SCHEMA.json",
         calibration_artifact_manifest_schema())
    dump(root / CASE_DIR / "VAL_CORPUS_002_STAGE_B0_CORRECTED_TOOLING_QUALIFICATION.json", {
        "schema_version": 1, "authorization_id": AUTHORIZATION_ID,
        "profile": "EWP_TOOLING_STAGE_V1",
        "disposition": "VAL_CORPUS_002_STAGE_B0_FINAL_TOOLING_PENDING_REVIEW",
        "calibration_source_binding": source_binding,
        "objective": {"identity": OBJECTIVE_ID,
            "formula": "mean(((model_i-source_i)/source_i)^2)",
            "zero_source_denominator": "FAIL_CLOSED"},
        "optimizer": {"algorithm": "GOLDEN_SECTION_LOG_K_V1",
            "k_bounds_s_inverse": [K_LOWER, K_UPPER], "log_k_bounds": [LOG_K_LOWER, LOG_K_UPPER],
            "log_k_interval_tolerance": LOG_K_TOLERANCE,
            "maximum_evaluations": MAX_EVALUATIONS,
            "nonconverged_manifest": "PROHIBITED"},
        "p2_materialization": {"input": "EXACT_CALIBRATION_MANIFEST_ONLY",
            "raw_rate": "PROHIBITED", "template_count": 15,
            "identical_manifest_bound_rate": "REQUIRED",
            "governed_content_verification": "MANDATORY",
            "status_record_class_pairing": "EXACT_FAIL_CLOSED",
            "synthetic_path": "SEPARATE_NONPRODUCTION_ONLY"},
        "governed_artifact_manifest": {
            "schema_path": (CASE_DIR / "VAL_CORPUS_002_CALIBRATION_ARTIFACT_MANIFEST_SCHEMA.json").as_posix(),
            "schema_sha256": "e224be9d68f0a5f2978545f8a323acce0f1620793a1ab2416b541514b31f0436",
            "required_roles": sorted(ARTIFACT_ROLES),
            "content_verification": "ALL_MEMBERS_MANDATORY_FAIL_CLOSED"},
        "governed_reconstruction": {
            "calibration_template_sha256": EXP7_H1_TEMPLATE_SHA256,
            "configuration": "ONE_TYPED_PLACEHOLDER_RECONSTRUCTED_AND_HASH_VERIFIED",
            "optimizer_trace": "UNIQUE_SELECTED_FINAL_ROW_VERIFIED",
            "objective": "EXACT_THREE_MASS_RELATIVE_MSE_RECOMPUTED",
            "objective_serialization_absolute_tolerance": OBJECTIVE_SERIALIZATION_ABSOLUTE_TOLERANCE},
        "reducers": ["SCHMIEDER_THREE_MASS_AND_RESIDUALS", "REPLICATE_STATISTICS",
            "OBSERVED_RANGE_AND_SD_COUNTS", "PAIRED_H0_H1_ERROR_RATIO",
            "ALL_THREE_AXIS_CONTRASTS_ALL_BREW_RATIOS", "WASZKIEWICZ_FULL_SERIES_AND_WINDOWS",
            "SUPPLIED_UNCERTAINTY_SECONDARY_METRICS", "COMPLETE_3_BY_4_SENSITIVITY_SVD_RANK_CORRELATION",
            "SOURCE_ONLY_SPECIES_LIMITATION_AUDIT"],
        "interval_input": ["time_s", "outlet_flow_m3_s", "totalSoluteFluxKgS", "liquid_density_kg_m3"],
        "artifact_symlinks": "REJECTED_BEFORE_RESOLUTION",
        "parity": {"reference_sha256": REFERENCE["sha256"], "required_rows": 1500,
            "first_timestamp_s": REFERENCE["first_timestamp_s"],
            "final_timestamp_s": REFERENCE["final_timestamp_s"]},
        "protected_action_control": "EXACT_ACTION_AND_CASE_ALLOWLIST",
        "openfoam": "NOT_BUILT_NOT_RUN", "calibration": "NOT_EXECUTED",
        "model_result_access": "NOT_PERFORMED", "governed_scoring": "NOT_PERFORMED",
        "stage_b1": "NOT_STARTED"})
    dump(root / CASE_DIR / "VAL_CORPUS_002_STAGE_B0_ACCESS_AND_CLAIM_BARRIERS.json", {
        "schema_version": 1, "initial_state": "B0_SYNTHETIC_ONLY",
        "model_result_access": "PROHIBITED", "transfer_result_access": "PROHIBITED",
        "protected_scoring": "PROHIBITED", "post_transfer_refit_path": "ABSENT",
        "p2_mode_specific_rates": "PROHIBITED",
        "claim_ceiling": "PHYSICAL_VALIDATION_NOT_ESTABLISHED",
        "protected_action_policy": "EXACT_ACTION_AND_CASE_ALLOWLIST",
        "production_materialization": "EXACT_CALIBRATION_MANIFEST_ONLY_NO_RAW_RATE",
        "normal_end_state": "VAL_CORPUS_002_STAGE_B0_FINAL_TOOLING_PENDING_REVIEW"})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--review-root", type=Path,
                        default=Path("../.wp03-002-exact-head-review"))
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args(); root = args.root.resolve()
    if args.generate: generate(root, args.review_root.resolve())
    else:
        build_configuration_inventory(root); bind_reference(root, args.review_root.resolve())
    print(json.dumps({"status": "PASS", "openfoam": "NOT_RUN",
                      "governed_scoring": "NOT_PERFORMED"}, indent=2))


if __name__ == "__main__":
    main()
