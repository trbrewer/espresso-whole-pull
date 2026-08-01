#!/usr/bin/env python3
"""Static, non-score-bearing VAL-001 correction verification."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT_IMPORT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_IMPORT))
from tools.validation.val001.framework import (  # noqa: E402
    ContractError, load_json, validate_adapter, validate_record, validate_run_spec,
)

LOCK = ("fc61c4670ec7bf801e40bb391aab16048b8da26b", "1d553e44ee2f7480a5df521560801b478618cc84")
ORIGINAL_RESULT_SHA = "07086313d022555032bbb9ecc18d2564bb197d0381bd8d08e263cd95d02bd029"
SECOND_RESULT_SHA = "7968e3b99045da9500442932c536bf920d559ebe660d2bad01f954f36b3f75b5"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path) -> dict[str, object]:
    checks: dict[str, object] = {}
    adapter_schema = load_json(root / "validation/val001/schemas/source_adapter.schema.json")
    run_schema = load_json(root / "validation/val001/schemas/comparison_run.schema.json")
    adapters = []
    for path in sorted((root / "validation/val001/adapters").glob("*.json")):
        record = load_json(path)
        if record.get("schema_version") == "espresso.val001.source_adapter.v3":
            validate_record(record, adapter_schema)
        validate_adapter(record, root, LOCK)
        adapters.append(str(path.relative_to(root)))
    spec = load_json(root / "validation/val001/contracts/VAL_001_CORRECTED_RUN_SPEC.json")
    validate_record(spec, run_schema)
    selected = load_json(root / spec["adapter"])
    validate_run_spec(spec, selected)
    governed = [
        ("validation/val001/VAL_001_INVOCATION_ACCOUNTING_CONTRACT.json", "invocation_ledger.schema.json"),
        ("validation/val001/VAL_001_EVIDENCE_AND_RIGHTS_INVENTORY.json", "evidence_rights_inventory.schema.json"),
        ("validation/val001/VAL_001_CALIBRATION_COMPARISON_LEDGER.json", "calibration_comparison_ledger.schema.json"),
        ("validation/val001/VAL_001_CAMPAIGN_PROVENANCE.json", "campaign_provenance.schema.json"),
        ("validation/val001/amendments/VAL_001_CORRECTED_ROW_COUNT_INVALIDATION.json", "amendment_invalidation.schema.json"),
    ]
    for record_path, schema_name in governed:
        validate_record(load_json(root / record_path), load_json(root / "validation/val001/schemas" / schema_name))
    for path in sorted((root / "validation/val001").rglob("*.json")):
        load_json(path)
    runner_text = (root / "scripts/run_val001_corrected_comparison.py").read_text(encoding="utf-8")
    if "WP03_001_SOURCE_PRESSURE_SWEEP.csv" in runner_text:
        raise ContractError("consumed production runner names governed comparison input")
    old = root / "validation/val001/results/VAL_001_FIRST_COMPONENT_COMPARISONS.json"
    if digest(old) != ORIGINAL_RESULT_SHA:
        raise ContractError("original result bytes changed")
    ledger = load_json(root / "validation/val001/VAL_001_INVOCATION_ACCOUNTING_CONTRACT.json")
    if ledger["actual_corrected"]["test_or_ci_real_data_invocations"] != 0:
        raise ContractError("CI/test real-data invocation count nonzero")
    replacement = root / "validation/val001/results/VAL_001_CORRECTED_COMPONENT_COMPARISONS_V2.json"
    if digest(replacement) != SECOND_RESULT_SHA:
        raise ContractError("second-correction result bytes changed")
    validate_record(
        load_json(replacement),
        load_json(root / "validation/val001/schemas/comparison_result.schema.json"),
    )
    replacement_events = [
        event for event in ledger["events"]
        if event["invocation_id"] == "VAL001-SECOND-CORRECTION-REPLACEMENT-001"
    ]
    if len(replacement_events) != 1 or replacement_events[0]["status"] != "COMPLETED":
        raise ContractError("replacement invocation ledger event is not singular and complete")
    if replacement_events[0]["output_sha256"] != SECOND_RESULT_SHA:
        raise ContractError("replacement invocation output hash mismatch")
    if ledger["historical"]["minimum_known_total_real_data_computations"] != 5:
        raise ContractError("cumulative real-data accounting mismatch")
    gap = load_json(root / "validation/val001/adapters/GAGNE_DE1_EVIDENCE_GAP_ADAPTER.json")
    if gap["execution"] != {"executable": False, "disposition": "NOT_EXECUTABLE_IN_VAL001", "reason_codes": gap["execution"]["reason_codes"]}:
        raise ContractError("evidence-gap adapter is not fail-closed")
    checks.update({"status": "PASS", "validated_adapters": adapters, "all_val001_json_standard_and_finite": True,
                   "original_result_sha256": ORIGINAL_RESULT_SHA,
                   "second_correction_result_sha256": SECOND_RESULT_SHA,
                   "test_or_ci_real_data_invocations": 0,
                   "first_corrected_real_data_invocations": ledger["actual_corrected"]["real_data_comparison_invocations"],
                   "second_correction_real_data_invocations": ledger["historical"]["second_correction_real_data_comparison_invocations"],
                   "minimum_known_total_real_data_computations": 5})
    return checks


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, required=True); args = parser.parse_args()
    print(json.dumps(verify(args.root.resolve()), indent=2, sort_keys=True))


if __name__ == "__main__": main()
