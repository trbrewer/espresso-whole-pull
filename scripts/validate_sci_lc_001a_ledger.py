#!/usr/bin/env python3
"""Fail-closed semantic validation for the SCI-LC-001A execution ledger."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "validation/cases/sci_lc_001a"
UNRESOLVED = "UNRESOLVED_FROM_RETAINED_EVIDENCE"


def _fail(code: str) -> None:
    raise ValueError(code)


def _integer(value: Any) -> bool:
    return type(value) is int


def validate_typed_values(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        if value.get("status") == UNRESOLVED:
            if not isinstance(value.get("reason"), str) or not value["reason"].strip():
                _fail(f"TYPED_UNRESOLVED_REASON_REQUIRED:{path}")
            sources = value.get("sources")
            if not isinstance(sources, list) or not sources or not all(
                    isinstance(item, str) and item.strip() for item in sources):
                _fail(f"TYPED_UNRESOLVED_SOURCE_REQUIRED:{path}")
        for key, item in value.items():
            validate_typed_values(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            validate_typed_values(item, f"{path}[{index}]")


def validate_ledger(ledger: dict, binding: dict) -> None:
    if ledger.get("schema_version") != "2.0.0":
        _fail("LEDGER_SCHEMA_VERSION_INVALID")
    records = ledger.get("records")
    if not isinstance(records, list) or not records:
        _fail("LEDGER_RECORDS_REQUIRED")
    ids = [record.get("record_id") for record in records]
    if len(ids) != len(set(ids)):
        _fail("RECORD_ID_DUPLICATE")
    ordinals = [record["attempt_ordinal"] for record in records
                if type(record.get("attempt_ordinal")) is int]
    if len(ordinals) != len(set(ordinals)):
        _fail("ATTEMPT_ORDINAL_DUPLICATE")
    if (any(record_id == "E4-ATTEMPT-05" for record_id in ids) or
            ledger.get("attempt_05_authority") != "NONE"):
        _fail("ATTEMPT_05_FORBIDDEN")

    for record in records:
        rid = record["record_id"]
        for field in ("planned_keys", "dispatched_keys", "attempted_keys", "completed_keys",
                      "stopped_keys", "failed_keys", "unattempted_keys", "classification_count"):
            value = record.get(field)
            if _integer(value) and value < 0:
                _fail(f"NEGATIVE_COUNT:{rid}:{field}")
        planned = record.get("planned_keys")
        completed = record.get("completed_keys")
        stopped = record.get("stopped_keys", 0)
        failed = record.get("failed_keys", 0)
        unattempted = record.get("unattempted_keys")
        dispatched = record.get("dispatched_keys")
        attempted = record.get("attempted_keys")
        count_model = record.get("count_model")
        if count_model == "OUTCOMES_PLUS_UNATTEMPTED" and all(
                _integer(value) for value in (planned, completed, stopped, failed, unattempted)):
            if completed + stopped + failed + unattempted != planned:
                _fail(f"PLANNED_COUNT_ARITHMETIC_INVALID:{rid}")
        elif count_model == "DISPATCHED_PLUS_UNATTEMPTED" and all(
                _integer(value) for value in (planned, dispatched, unattempted)):
            if dispatched + unattempted != planned:
                _fail(f"PLANNED_COUNT_ARITHMETIC_INVALID:{rid}")
        elif count_model not in {"OUTCOMES_PLUS_UNATTEMPTED",
                                 "DISPATCHED_PLUS_UNATTEMPTED",
                                 "UNRESOLVED_HISTORICAL_COUNTS"}:
            _fail(f"COUNT_MODEL_INVALID:{rid}")
        if _integer(dispatched) and _integer(completed) and completed > dispatched:
            _fail(f"COMPLETED_EXCEEDS_DISPATCHED:{rid}")
        if _integer(attempted) and _integer(completed) and completed > attempted:
            _fail(f"COMPLETED_EXCEEDS_ATTEMPTED:{rid}")
        if record.get("terminal_state") == "COMPLETE":
            if _integer(unattempted) and unattempted != 0:
                _fail(f"COMPLETE_WITH_UNATTEMPTED:{rid}")
            if "STOP" in str(record.get("terminal_disposition", "")):
                _fail(f"COMPLETE_WITH_STOP_DISPOSITION:{rid}")
        incomplete = (record.get("event_state_capture_complete") is False or
                      "INCOMPLETE" in str(record.get("terminal_disposition", "")) or
                      record.get("terminal_state") in {"STOPPED", "STOPPED_UNFINALIZED",
                                                       "FAILED_CONTAINED", "ARCHIVED"})
        if incomplete and record.get("terminal_state") == "COMPLETE":
            _fail(f"INCOMPLETE_TERMINAL_COMPLETE:{rid}")
        if incomplete and record.get("canonical_eligibility") is not False:
            _fail(f"INCOMPLETE_CANONICAL_ELIGIBILITY:{rid}")
        if incomplete and record.get("classification_eligibility") is not False:
            _fail(f"INCOMPLETE_CLASSIFICATION_ELIGIBILITY:{rid}")
        if (record.get("classification_eligibility") is False and
                record.get("classification_count") != 0):
            _fail(f"INELIGIBLE_CLASSIFICATION_NONZERO:{rid}")
        if (record.get("scientific_eligibility") is False and
                record.get("classification_count") != 0):
            _fail(f"SCIENTIFICALLY_INELIGIBLE_CLASSIFICATION_NONZERO:{rid}")
        if record.get("quarantined") and (
                record.get("reuse_permission") is not False or
                record.get("combination_permission") is not False):
            _fail(f"QUARANTINED_REUSE_OR_COMBINATION:{rid}")
        validate_typed_values(record, f"$.records[{rid}]")

    by_id = {record["record_id"]: record for record in records}
    rca = by_id.get("RCA-002")
    if rca is None:
        _fail("RCA002_RECORD_MISSING")
    exact = {
        "planned_keys": 3666,
        "attempted_keys": 2555,
        "completed_keys": 2555,
        "unattempted_keys": 1111,
        "terminal_disposition": "STOP_EVENT_STATE_CAPTURE_INCOMPLETE",
        "event_state_capture_complete": False,
        "canonical_eligibility": False,
        "classification_eligibility": False,
        "classification_count": 0,
    }
    for field, expected in exact.items():
        if rca.get(field) != expected or binding.get(field) != expected:
            _fail(f"RCA002_EVIDENCE_BINDING_MISMATCH:{field}")
    if rca.get("terminal_state") == "COMPLETE":
        _fail("RCA002_TERMINAL_STATE_COMPLETE")
    if (not isinstance(rca.get("dispatched_keys"), dict) or
            rca["dispatched_keys"].get("status") !=
            binding.get("dispatched_keys", {}).get("status")):
        _fail("RCA002_DISPATCH_BINDING_MISMATCH")
    expected_sources = {
        "reports/COUNTERS.json": "8bb363e28119dfd57d45e006d708bb6c6ec7d54db4f4212942d5763e1876e8bb",
        "reports/EVENT_STATE_SUFFICIENCY.json": "0392e9763c2d01cb1c6d1267b2b049892b203f89382136f3968bf9ea04d301a4",
        "reports/FINAL_DECISION.json": "183e245b1daa0614bfd34543a7c57fbec5870e58532220e346d5da62a014f29a",
        "verification/INDEPENDENT_CHECKER.json": "bddcf267609dbd1150e153b93f18269294d4d5ebbb202c916210b953688babe3",
    }
    for source, digest in expected_sources.items():
        if binding.get("sources", {}).get(source) != digest:
            _fail(f"RCA002_SOURCE_HASH_MISMATCH:{source}")
    attempt4 = by_id.get("E4-ATTEMPT-04")
    attempt4_exact = {"planned_keys": 3666, "dispatched_keys": 3666,
        "attempted_keys": 3666, "completed_keys": 3558, "stopped_keys": 108,
        "failed_keys": 0, "unattempted_keys": 0, "consumed": True,
        "terminal_state": "QUARANTINED",
        "terminal_disposition": "FINAL_ATTEMPT_04_DIAGNOSTIC_EVIDENCE_INCOMPLETE",
        "diagnostic_health_complete": False, "scientific_eligibility": False,
        "canonical_eligibility": False, "classification_eligibility": False,
        "classification_count": 0, "quarantined": True}
    if attempt4 is None:
        _fail("ATTEMPT_04_RECORD_MISSING")
    for field, expected in attempt4_exact.items():
        if attempt4.get(field) != expected:
            _fail(f"ATTEMPT_04_FINAL_EVIDENCE_MISMATCH:{field}")


def load_and_validate(case: Path = CASE) -> None:
    ledger = json.loads((case / "EXECUTION_ATTEMPT_LEDGER.json").read_text(encoding="utf-8"))
    binding = json.loads((case / "RCA_002_EVIDENCE_BINDING.json").read_text(encoding="utf-8"))
    validate_ledger(ledger, binding)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, default=CASE)
    args = parser.parse_args()
    load_and_validate(args.case_root)
    print(json.dumps({"status": "PASS", "case_root": str(args.case_root)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
