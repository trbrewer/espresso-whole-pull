#!/usr/bin/env python3
"""The single governed corrected VAL-001 real-data comparison invocation."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validation.val001.framework import (
    ContractError, assert_invocation_available, assert_real_execution_context, canonical_json,
    interpretation_rules, load_json, metrics, read_selected_rows, sha256,
    validate_adapter, validate_run_spec,
)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--authority", required=True, type=Path)
    parser.add_argument("--activation", required=True, type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--invocation-id", default="VAL001-CORRECTED-REAL-001")
    args = parser.parse_args()
    root = args.root.resolve()
    assert_real_execution_context()
    authority, activation = load_json(args.authority), load_json(args.activation)
    if authority["status"] not in {"AUTHORIZED_FOR_SINGLE_CORRECTED_INVOCATION", "AUTHORIZED_FOR_ONE_SECOND_CORRECTION_REPLACEMENT_INVOCATION"} or activation["status"] not in {"ACTIVE_FOR_BOUNDED_EXECUTION", "ACTIVE_FOR_HASH_VERIFIED_ARTIFACT_REUSE"}:
        raise SystemExit("corrected authority and activation records are required")
    spec_path = root / "validation/val001/contracts/VAL_001_CORRECTED_RUN_SPEC.json"
    adapter_path = root / "validation/val001/adapters/WASZKIEWICZ_PRESSURE_FLOW_ADAPTER.json"
    ledger_path = args.ledger or root / "validation/val001/VAL_001_INVOCATION_ACCOUNTING_CONTRACT.json"
    spec, adapter, ledger = load_json(spec_path), load_json(adapter_path), load_json(ledger_path)
    validate_run_spec(spec, adapter, root)
    invocation_id = args.invocation_id
    replacement = authority["status"] == "AUTHORIZED_FOR_ONE_SECOND_CORRECTION_REPLACEMENT_INVOCATION"
    if replacement:
        if any(item.get("invocation_id") == invocation_id for item in ledger["events"]):
            raise ContractError("a second replacement real-data invocation is refused")
    else:
        assert_invocation_available(ledger)
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    event = {"invocation_id": invocation_id, "execution_role": "GOVERNED_RESULT_PRODUCING_INVOCATION", "status": "STARTED", "command": "scripts/run_val001_corrected_comparison.py", "start_timestamp": started, "completion_timestamp": None, "commit": git(root, "rev-parse", "HEAD"), "tree": git(root, "rev-parse", "HEAD^{tree}"), "analyzer_sha256": sha256(Path(__file__)), "authority_record_sha256": sha256(args.authority), "adapter_sha256": sha256(adapter_path), "input_sha256": spec["input"]["sha256"], "output_sha256": None, "exception_status": "NONE", "invalidation_status": "VALID"}
    ledger["events"].append(event)
    ledger["status"] = "CORRECTED_INVOCATION_STARTED"
    ledger_path.write_bytes(canonical_json(ledger))
    rows = read_selected_rows(root, spec)
    comparisons = []
    for item in spec["comparisons"]:
        observed = [float(row[item["observation_column"]]) for row in rows]
        predicted = [float(row[item["prediction_column"]]) for row in rows]
        calculated = metrics(observed, predicted)
        residual_table = [{"nominal_pressure_bar": float(row["nominal_pressure_bar"]), "observation_g_s": observed[i], "prediction_g_s": predicted[i], "residual_g_s": calculated["residuals"][i]} for i, row in enumerate(rows)]
        calculated.pop("residuals")
        comparisons.append({"comparison_id": item["comparison_id"], "classification": item["classification"], "metrics": {**calculated, "units": "g/s except dimensionless r_squared_descriptive", "sample_count": 10, "pressure_conditions_bar": [float(row["nominal_pressure_bar"]) for row in rows], "support_bar": [1.0, 11.0], "weighting": "EQUAL_SELECTED_CONDITION", "uncertainty_status": "SOURCE_UNCERTAINTY_NOT_REPORTED", "gate_bearing": False}, "residual_table": residual_table, "uncertainty_disposition": "DESCRIPTIVE_COMPARISON_NO_UNCERTAINTY_GATE"})
    fired, decision = interpretation_rules(comparisons)
    result = {"schema_version": "espresso.val001.comparison_result.v2", "task": "VAL-001", "classification": "POST_OBSERVATION_REPRODUCTION", "input": {"path": spec["input"]["path"], "sha256": spec["input"]["sha256"], "selected_row_canonical_sha256": spec["input"]["selected_row_canonical_sha256"], "invocation_id": invocation_id, "authority_record_sha256": sha256(args.authority), "adapter_sha256": sha256(adapter_path), "runner_sha256": sha256(Path(__file__))}, "execution_counts": {"corrected_real_data_comparison_invocations": 1, "corrected_governed_result_producing_invocations": 1, "corrected_test_or_ci_real_data_invocations": 0, "openfoam_case_executions": activation.get("actual_openfoam_case_executions", 0), "fit_or_retune_count": 0, "protected_access_count": 0, "holdout_score_count": 0}, "comparisons": comparisons, "interpretation": {"rules_fired": fired, "decision": decision, "variant_discrimination": "NOT_ESTABLISHED", "physical_equivalence": "NOT_ESTABLISHED", "model_correctness": "NOT_ESTABLISHED", "mechanism_identification": "NOT_ESTABLISHED", "blind_status": "NOT_BLIND", "independence_status": "NOT_INDEPENDENT"}, "claim_boundaries": spec["claim_boundaries"]}
    output_path = root / spec["output"]
    output_path.write_bytes(canonical_json(result))
    event["status"] = "COMPLETED"; event["completion_timestamp"] = dt.datetime.now(dt.timezone.utc).isoformat(); event["output_sha256"] = sha256(output_path)
    if replacement:
        ledger["status"] = "SECOND_CORRECTION_REPLACEMENT_INVOCATION_COMPLETED"
        ledger["historical"].update({"second_correction_real_data_comparison_invocations": 1, "second_correction_governed_result_producing_invocations": 1, "second_correction_test_or_ci_real_data_invocations": 0, "minimum_known_total_real_data_computations": 5})
    else:
        ledger["status"] = "CORRECTED_SINGLE_INVOCATION_COMPLETED"
        ledger["actual_corrected"] = {"real_data_comparison_invocations": 1, "governed_result_producing_invocations": 1, "test_or_ci_real_data_invocations": 0}
    ledger_path.write_bytes(canonical_json(ledger))


if __name__ == "__main__":
    main()
