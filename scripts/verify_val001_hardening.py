#!/usr/bin/env python3
"""Strict, non-scoring verification of final VAL-001 hardening records."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_MODULE))

from tools.validation.val001.framework import ContractError, load_json, sha256, validate_adapter, validate_record
from tools.validation.val001.schema import lint_schema
from tools.validation.val001.source_identity import selected_row_identity
from tools.validation.val001.inventory import verify_inventory, verify_registry

EXPECTED_LOCK = ("fc61c4670ec7bf801e40bb391aab16048b8da26b", "1d553e44ee2f7480a5df521560801b478618cc84")


def verify(root: Path) -> dict[str, object]:
    registry = load_json(root / "validation/val001/VAL_001_GOVERNED_SCHEMA_REGISTRY.json")
    inventory = load_json(root / "validation/val001/VAL_001_GOVERNED_RECORD_INVENTORY.json")
    verify_inventory(root, inventory); verify_registry(inventory, registry)
    validated = []
    for entry in registry["records"]:
        record_path, schema_path = root / entry["path"], root / entry["schema_path"]
        schema = load_json(schema_path); lint_schema(schema)
        if entry["treatment"] == "CURRENT_DEEP_SCHEMA":
            validate_record(load_json(record_path), schema)
        elif sha256(record_path) != entry["sha256"]:
            raise ContractError(f"immutable historical hash mismatch: {entry['path']}")
        validated.append(entry["path"])
    adapter = load_json(root / "validation/val001/adapters/WASZKIEWICZ_PRESSURE_FLOW_ADAPTER.json")
    validate_adapter(adapter, root, expected_dependency=EXPECTED_LOCK)
    journal_schema = load_json(root / "validation/val001/schemas/invocation_event.schema.json")
    journal_path = root / "validation/val001/VAL_001_INVOCATION_EVENTS.jsonl"
    events = []
    for line_number, line in enumerate(journal_path.read_text(encoding="utf-8").splitlines(), 1):
        try: event = json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        except ValueError as exc: raise ContractError(f"journal line {line_number}: {exc}") from exc
        validate_record(event, journal_schema); events.append(event)
    if not any(event["status"] == "AUTHORITY_CONSUMED" for event in events):
        raise ContractError("journal lacks consumed-authority event")
    lock = load_json(root / "validation/val001/contracts/VAL_001_POSTRESULT_EXECUTION_LOCK.json")
    for binding in lock["bindings"]:
        if sha256(root / binding["path"]) != binding["sha256"]:
            raise ContractError(f"post-result binding mismatch: {binding['path']}")
    identity = selected_row_identity(root / "validation/wp03/WP03_001_SOURCE_PRESSURE_SWEEP.csv")
    if identity["selected_row_canonical_sha256_v2"] != "37dd7ff3c1b088c0cd8558154d2af2a2ca6b6e98a11aebda78dfdb9015877c0b":
        raise ContractError("selected-row V2 identity mismatch")
    return {"schemas_validated": len(validated), "journal_events": len(events), "source_identity_verifications": 1, "real_data_comparison_invocations": 0}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", required=True, type=Path); args = parser.parse_args()
    print(json.dumps(verify(args.root.resolve()), sort_keys=True))


if __name__ == "__main__": main()
