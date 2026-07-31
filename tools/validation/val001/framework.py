"""Fail-closed VAL-001 contracts and deterministic comparison arithmetic."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any

from .schema import SchemaError, validate as validate_schema

UNAVAILABLE = "UNAVAILABLE"
UNCERTAINTY_NOT_REPORTED = "SOURCE_UNCERTAINTY_NOT_REPORTED"
HASH_RE = re.compile(r"[0-9a-f]{64}")
COMMIT_RE = re.compile(r"[0-9a-f]{40}")
ALLOWED_EVIDENCE = {
    "SOURCE_LINKED_POST_FIT_COMPONENT_COMPARISON",
    "HISTORICAL_GOVERNED_RESULT_REEXPRESSION",
    "PLANNING_EVIDENCE_GAP",
}
ALLOWED_CLAIMS = {
    "POST_OBSERVATION_REPRODUCTION",
    "POST_FIT_SOURCE_RECONSTRUCTION",
    "PREDECLARED_NO_RETUNING_SAME_CAMPAIGN_COMPARISON",
    "HISTORICAL_GOVERNED_RESULT_REEXPRESSED_NO_NEW_SCORE",
    "NOT_EXECUTABLE_IN_VAL001",
}
GOVERNED_REAL_SOURCE = "validation/wp03/WP03_001_SOURCE_PRESSURE_SWEEP.csv"


class ContractError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    def reject(value: str) -> None:
        raise ContractError(f"non-standard JSON number: {value}")
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream, parse_constant=reject)
    if not isinstance(value, dict):
        raise ContractError("governed JSON root must be an object")
    return value


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_record(record: dict[str, Any], schema: dict[str, Any]) -> None:
    try:
        validate_schema(record, schema)
    except SchemaError as exc:
        raise ContractError(str(exc)) from exc


def _required_mapping(mapping: dict[str, Any], names: tuple[str, ...], label: str) -> None:
    missing = [name for name in names if name not in mapping]
    if missing:
        raise ContractError(f"{label} incomplete: {missing}")


def validate_adapter(adapter: dict[str, Any], root: Path | None = None,
                     expected_dependency: tuple[str, str] | None = None) -> None:
    _required_mapping(adapter, ("adapter_id", "source", "evidence", "rights", "mappings",
                                  "quantities", "solver_mapping", "execution", "claim_ceiling"), "adapter")
    source, evidence, rights = adapter["source"], adapter["evidence"], adapter["rights"]
    _required_mapping(source, ("publication_citation", "dataset_identity", "artifact_paths",
                               "artifact_sha256", "dependency_repository", "dependency_commit",
                               "dependency_tree", "local_reduced_input", "local_reduced_input_sha256"), "source")
    if not source["artifact_paths"] or set(source["artifact_paths"]) != set(source["artifact_sha256"]):
        raise ContractError("source artifact paths and hashes must be nonempty and identical sets")
    if expected_dependency and (source["dependency_commit"], source["dependency_tree"]) != expected_dependency:
        raise ContractError("dependency lock commit or tree mismatch")
    if not COMMIT_RE.fullmatch(source["dependency_commit"]) or not COMMIT_RE.fullmatch(source["dependency_tree"]):
        raise ContractError("dependency identities must be full Git object IDs")
    if root is not None:
        local = root / source["local_reduced_input"]
        if not local.is_file() or not HASH_RE.fullmatch(source["local_reduced_input_sha256"]):
            raise ContractError("source artifact absent or hash missing")
        if sha256(local) != source["local_reduced_input_sha256"]:
            raise ContractError("source artifact SHA-256 mismatch")
    if evidence.get("level") not in ALLOWED_EVIDENCE:
        raise ContractError("missing or unknown evidence class")
    if evidence.get("protected") or evidence.get("holdout_status") == "INDEPENDENT_HOLDOUT":
        if adapter["execution"].get("executable"):
            raise ContractError("protected or holdout execution denied")
    _required_mapping(rights, ("access_status", "comparison_allowed", "redistribution_status",
                               "analysis_permission", "derived_publication_permission"), "rights")
    executable = adapter["execution"].get("executable")
    if executable and (rights["access_status"] != "PUBLIC" or rights["comparison_allowed"] is not True):
        raise ContractError("incomplete rights or comparison permission false")
    if executable and rights["redistribution_status"] not in {"CC_BY_4_0_REDUCED_DATA", "GOVERNED_DERIVED_RECORD"}:
        raise ContractError("redistribution status inconsistent with committed data")
    mappings = adapter["mappings"]
    _required_mapping(mappings, ("apparatus", "pressure_node", "pressure_basis", "outlet_reference",
                                 "hydraulic_area", "time_origin", "time_unit", "coordinate_origin",
                                 "positive_coordinate_direction", "sign_convention", "conversion_rules",
                                 "interpolation_rules", "missing_data_behavior", "uncertainty_status"), "scientific mappings")
    essential = ("pressure_node", "pressure_basis", "outlet_reference", "hydraulic_area")
    if executable and any(mappings[name].get("value") is None for name in essential):
        raise ContractError("essential scientific mapping unavailable")
    names: set[str] = set()
    for quantity in adapter["quantities"]:
        _required_mapping(quantity, ("id", "unit", "source_role", "model_role", "comparison_role",
                                     "calibration_influence", "score_bearing", "availability"), "quantity")
        if quantity["id"] in names:
            raise ContractError("duplicate quantity identifiers")
        names.add(quantity["id"])
        if quantity["availability"] == "UNAVAILABLE" and quantity.get("value") is not None:
            raise ContractError("unavailable quantity represented numerically")
        if not quantity["unit"]:
            raise ContractError("quantity without units")
        if quantity["source_role"] == "UNRESTRICTED_CALIBRATION" and quantity["comparison_role"] == "INDEPENDENT_COMPARISON":
            raise ContractError("calibration/comparison overlap")
    solver = adapter["solver_mapping"]
    if solver.get("fitting_or_retuning_allowed") or solver.get("fit_or_retune_count") != 0:
        raise ContractError("fitting or retuning prohibited")
    if solver.get("configuration_change") or solver.get("solver_source_change"):
        raise ContractError("undeclared configuration or solver-source change")
    if adapter["claim_ceiling"] not in ALLOWED_CLAIMS:
        raise ContractError("overbroad claim ceiling")
    if executable and adapter["execution"].get("disposition") != "EXECUTABLE":
        raise ContractError("executable adapter has inconsistent disposition")
    if not executable and not adapter["execution"].get("reason_codes"):
        raise ContractError("non-executable adapter requires reason codes")


def validate_run_spec(spec: dict[str, Any], adapter: dict[str, Any], root: Path | None = None) -> None:
    validate_adapter(adapter, root)
    if spec.get("change_declaration") != "NO_GOVERNING_PHYSICS_CHANGE":
        raise ContractError("VAL-001 requires NO_GOVERNING_PHYSICS_CHANGE")
    counts = spec["planned_counts"]
    if counts != {"openfoam_case_executions": 3, "real_data_comparison_invocations": 1,
                  "governed_result_producing_invocations": 1, "test_or_ci_real_data_invocations": 0,
                  "fit_or_retune_count": 0, "protected_access_count": 0, "holdout_score_count": 0}:
        raise ContractError("planned execution counts differ from corrected authority")
    inp = spec["input"]
    if inp["header_rows"] != 1 or inp["total_data_rows"] != 11 or inp["selected_data_rows"] != 10 or inp["excluded_data_rows"] != 1:
        raise ContractError("frozen row counts invalid")
    if len(inp["selected_row_ids"]) != 10 or len(set(inp["selected_row_ids"])) != 10:
        raise ContractError("selected-row identity invalid")
    quantities = {q["id"]: q for q in adapter["quantities"]}
    for comparison in spec["comparisons"]:
        if comparison["observation_column"] not in quantities:
            raise ContractError("observation absent from adapter")
        if comparison["prediction_column"] not in quantities:
            raise ContractError("prediction absent from adapter")
        if not quantities[comparison["observation_column"]]["score_bearing"]:
            raise ContractError("score-bearing observation omitted from ledger")
        if comparison["weighting"] != "EQUAL_SELECTED_CONDITION" or comparison["residual_sign"] != "PREDICTION_MINUS_OBSERVATION":
            raise ContractError("undeclared weighting or residual sign")
        if comparison["threshold"] is not None:
            raise ContractError("threshold lacks independent basis")
        if comparison["interpolation"] != "NONE" or comparison["time_shift"] != "NONE":
            raise ContractError("unsupported interpolation or result-selected time shift")
        allowed = {"RMSE", "MAE", "MEAN_BIAS", "MAXIMUM_ABSOLUTE_ERROR", "DESCRIPTIVE_R_SQUARED"}
        if not set(comparison["metrics"]).issubset(allowed):
            raise ContractError("unsupported metric or normalization")


def metrics(observed: list[float], predicted: list[float]) -> dict[str, Any]:
    if len(observed) != len(predicted) or not observed:
        raise ContractError("vectors must have equal nonzero length")
    if not all(math.isfinite(v) for v in observed + predicted):
        raise ContractError("nonfinite comparison value")
    residuals = [p - o for o, p in zip(observed, predicted)]
    mean_obs = sum(observed) / len(observed)
    sst = sum((v - mean_obs) ** 2 for v in observed)
    return {
        "n": len(observed),
        "rmse": math.sqrt(sum(v * v for v in residuals) / len(residuals)),
        "mae": sum(abs(v) for v in residuals) / len(residuals),
        "mean_bias": sum(residuals) / len(residuals),
        "maximum_absolute_error": max(abs(v) for v in residuals),
        "r_squared_descriptive": None if sst == 0 else 1 - sum(v * v for v in residuals) / sst,
        "residuals": residuals,
    }


def read_selected_rows(root: Path, spec: dict[str, Any]) -> list[dict[str, str]]:
    path = root / spec["input"]["path"]
    if sha256(path) != spec["input"]["sha256"]:
        raise ContractError("input hash mismatch")
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != spec["input"]["total_data_rows"]:
        raise ContractError("total-row count mismatch")
    field, value = spec["input"]["filter"]["field"], spec["input"]["filter"]["value"]
    if field != "domain_status" or value != "IN_DOMAIN":
        raise ContractError("unsupported filter")
    selected = [row for row in rows if row.get(field) == value]
    if len(selected) != spec["input"]["selected_data_rows"]:
        raise ContractError("selected-row count mismatch or silent row dropping")
    ids = [row[spec["input"]["row_id_column"]] for row in selected]
    if ids != spec["input"]["selected_row_ids"] or len(ids) != len(set(ids)):
        raise ContractError("selected support, order, or duplicate rows mismatch")
    return selected


def assert_real_execution_context() -> None:
    if os.environ.get("VAL001_REAL_DATA_EXECUTION") != "AUTHORIZED_SINGLE_INVOCATION":
        raise ContractError("governed real comparison requires explicit activation context")


def interpretation_rules(comparisons: list[dict[str, Any]]) -> tuple[list[str], str]:
    fired = ["SOURCE_UNCERTAINTY_OR_INDEPENDENT_DISCRIMINATION_CRITERION_UNAVAILABLE",
             "POST_FIT_SOURCE_RECONSTRUCTION_ONLY",
             "VARIANTS_NOT_DISCRIMINATED_AND_RESIDUAL_NOT_MECHANISM_UNIQUE"]
    if not comparisons:
        return ["EVIDENCE_NOT_EXECUTABLE"], "EVIDENCE_NOT_EXECUTABLE"
    return fired, "ADDITIONAL_DATA_REQUIRED_BEFORE_NEW_PHYSICS"


def assert_invocation_available(ledger: dict[str, Any]) -> None:
    actual = ledger["actual_corrected"]
    if actual["real_data_comparison_invocations"] != 0 or ledger["events"]:
        raise ContractError("a second corrected real-data invocation is refused")
