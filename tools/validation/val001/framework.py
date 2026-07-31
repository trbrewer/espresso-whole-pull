from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

UNAVAILABLE = "UNAVAILABLE"
UNCERTAINTY_NOT_REPORTED = "SOURCE_UNCERTAINTY_NOT_REPORTED"
ROLES = {
    "prescribed",
    "calibrated",
    "predicted_and_compared",
    "predicted_unscored",
    "contextual",
    "excluded",
    "unavailable",
}


class ContractError(ValueError):
    """Raised when an adapter or comparison contract is semantically unsafe."""


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_adapter(adapter: dict[str, Any]) -> None:
    required = {
        "schema_version", "adapter_id", "source", "evidence", "rights",
        "quantities", "solver_mapping", "claim_ceiling",
    }
    missing = sorted(required - adapter.keys())
    if missing:
        raise ContractError(f"adapter missing fields: {missing}")
    source = adapter["source"]
    for key in ("citation", "artifact_paths", "dependency_commit", "dependency_tree"):
        if key not in source:
            raise ContractError(f"source missing {key}")
    rights = adapter["rights"]
    if rights.get("access_status") != "PUBLIC" or rights.get("comparison_allowed") is not True:
        raise ContractError("comparison source must be public and comparison_allowed")
    quantities = adapter["quantities"]
    if not quantities:
        raise ContractError("adapter must declare quantities")
    names: set[str] = set()
    for quantity in quantities:
        name = quantity.get("name")
        role = quantity.get("role")
        if not name or name in names:
            raise ContractError("quantity names must be nonempty and unique")
        names.add(name)
        if role not in ROLES:
            raise ContractError(f"invalid evidence role for {name}: {role}")
        if not quantity.get("unit") or not quantity.get("definition"):
            raise ContractError(f"unit and definition required for {name}")
        if quantity.get("pressure_quantity") and not quantity.get("pressure_node"):
            raise ContractError(f"pressure node required for {name}")
        uncertainty = quantity.get("uncertainty")
        if uncertainty is None:
            raise ContractError(f"uncertainty status required for {name}")
    calibrated = {q["name"] for q in quantities if q["role"] == "calibrated"}
    compared = {q["name"] for q in quantities if q["role"] == "predicted_and_compared"}
    overlap = calibrated & compared
    if overlap:
        raise ContractError(f"calibration/comparison overlap: {sorted(overlap)}")


def validate_run_spec(spec: dict[str, Any], adapter: dict[str, Any]) -> None:
    validate_adapter(adapter)
    if spec.get("change_declaration") != "NO_GOVERNING_PHYSICS_CHANGE":
        raise ContractError("VAL-001 requires NO_GOVERNING_PHYSICS_CHANGE")
    if spec.get("protected_access_count") != 0 or spec.get("holdout_score_count") != 0:
        raise ContractError("protected and holdout access must remain zero")
    comparisons = spec.get("comparisons", [])
    if not comparisons:
        raise ContractError("at least one comparison must be frozen")
    ids = [item.get("comparison_id") for item in comparisons]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise ContractError("comparison IDs must be unique and nonempty")
    expected = spec.get("maximum_completed_score_bearing_invocations")
    if expected != 1:
        raise ContractError("this contract freezes exactly one analyzer invocation")
    for item in comparisons:
        if item.get("observation_column") == item.get("prediction_column"):
            raise ContractError("observation and prediction columns must differ")
        if item.get("threshold") is not None:
            raise ContractError("first comparisons are descriptive; thresholds are not authorized")


def _metrics(observed: list[float], predicted: list[float]) -> dict[str, Any]:
    if len(observed) != len(predicted) or not observed:
        raise ContractError("observed and predicted vectors must have equal nonzero length")
    residuals = [p - o for o, p in zip(observed, predicted)]
    rmse = math.sqrt(sum(value * value for value in residuals) / len(residuals))
    mae = sum(abs(value) for value in residuals) / len(residuals)
    mean_obs = sum(observed) / len(observed)
    denom = sum((value - mean_obs) ** 2 for value in observed)
    r2 = None if denom == 0 else 1.0 - sum(value * value for value in residuals) / denom
    return {
        "n": len(observed),
        "rmse_g_per_s": rmse,
        "mae_g_per_s": mae,
        "mean_bias_g_per_s": sum(residuals) / len(residuals),
        "maximum_absolute_error_g_per_s": max(abs(value) for value in residuals),
        "r_squared_descriptive": r2,
        "observed_range_g_per_s": [min(observed), max(observed)],
        "residuals_g_per_s": residuals,
        "uncertainty_normalized_metrics": UNAVAILABLE,
        "uncertainty_status": UNCERTAINTY_NOT_REPORTED,
    }


def run(root: Path, spec_path: Path, adapter_path: Path) -> dict[str, Any]:
    spec = load_json(spec_path)
    adapter = load_json(adapter_path)
    validate_run_spec(spec, adapter)
    input_path = root / spec["input"]["path"]
    if sha256(input_path) != spec["input"]["sha256"]:
        raise ContractError("comparison input SHA-256 does not match frozen contract")
    with input_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    results = []
    for comparison in spec["comparisons"]:
        selected = [row for row in rows if row["domain_status"] == comparison["row_filter"]["domain_status"]]
        observed = [float(row[comparison["observation_column"]]) for row in selected]
        predicted = [float(row[comparison["prediction_column"]]) for row in selected]
        results.append({
            "comparison_id": comparison["comparison_id"],
            "evidence_role": comparison["evidence_role"],
            "holdout_status": "NOT_HOLDOUT",
            "calibration_status": comparison["calibration_status"],
            "threshold": None,
            "metrics": _metrics(observed, predicted),
        })
    return {
        "schema_version": "espresso.val001.comparison_result.v1",
        "task": "VAL-001",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "adapter_id": adapter["adapter_id"],
        "contract_id": spec["contract_id"],
        "input": {"path": spec["input"]["path"], "sha256": sha256(input_path)},
        "execution_counts": {
            "completed_score_bearing_invocations": 1,
            "openfoam": 0,
            "protected_access": 0,
            "holdout_scores": 0,
            "fits_or_retunes": 0,
        },
        "comparisons": results,
        "decision": "ADDITIONAL_DATA_REQUIRED_BEFORE_NEW_PHYSICS",
        "claim_boundary": {
            "physical_validation": "NOT_ESTABLISHED",
            "whole_solver_validation": "NOT_ESTABLISHED",
            "result_class": "SOURCE_LINKED_POST_FIT_COMPONENT_COMPARISON",
        },
    }

