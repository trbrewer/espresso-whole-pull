"""Strict VAL-001 invocation-journal parsing, reconciliation, and summaries."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .framework import ContractError, canonical_json, load_json, sha256, validate_record


def parse_journal(path: Path, schema: dict[str, Any]) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    if not raw.endswith(b"\n"):
        raise ContractError("INVALID_OR_TRUNCATED_JOURNAL_MANUAL_RECONCILIATION_REQUIRED")
    lines = raw.decode("utf-8").splitlines()
    if not lines or any(not line.strip() for line in lines):
        raise ContractError("journal is empty or contains blank interior lines")
    events = []
    for number, line in enumerate(lines, 1):
        try:
            event = json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        except (json.JSONDecodeError, ValueError) as exc:
            raise ContractError(f"invalid journal line {number}: {exc}") from exc
        validate_record(event, schema); events.append(event)
    validate_sequence(events)
    return events


def validate_sequence(events: list[dict[str, Any]]) -> None:
    if [event["sequence"] for event in events] != list(range(1, len(events) + 1)):
        raise ContractError("non-monotonic event sequence")
    ids = [event["event_id"] for event in events]
    if len(ids) != len(set(ids)):
        raise ContractError("duplicate event ID")
    terminal: dict[str, str] = {}
    consumed: set[str] = set()
    for event in events:
        invocation = event["invocation_id"]
        if event["status"] == "STARTED":
            if invocation in terminal: raise ContractError("STARTED after terminal event")
        elif event["status"] in {"COMPLETED", "FAILED", "FAILED_INVALIDATED_AFTER_SCORE_EXPOSURE"}:
            if event["event_type"] == "INVOCATION_TERMINAL" and invocation not in {e["invocation_id"] for e in events[:events.index(event)] if e["status"] == "STARTED"}:
                raise ContractError("terminal event before STARTED")
            if invocation in terminal: raise ContractError("duplicate terminal invocation event")
            terminal[invocation] = event["status"]
            if event["status"] == "COMPLETED" and not event["output_sha256"]:
                raise ContractError("completion lacks output hash")
            if event["status"] != "COMPLETED" and event["output_sha256"] is not None:
                raise ContractError("failed invocation has output hash")
        elif event["status"] == "AUTHORITY_CONSUMED":
            if event["authority_id"] in consumed: raise ContractError("authority consumed twice")
            consumed.add(event["authority_id"])


def derive_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    minimum = sum(event["minimum_known_count"] or 0 for event in events if event["status"] == "MINIMUM_KNOWN_HISTORY")
    terminals = [event for event in events if event["status"] in {"COMPLETED", "FAILED", "FAILED_INVALIDATED_AFTER_SCORE_EXPOSURE"}]
    completed = [event for event in terminals if event["status"] == "COMPLETED"]
    failed = [event for event in terminals if event["status"] != "COMPLETED"]
    test_ci = [event for event in terminals if event["test_or_ci"]]
    governed = [event for event in completed if event["execution_role"] == "GOVERNED_RESULT_PRODUCING_INVOCATION"]
    consumed = sorted({event["authority_id"] for event in events if event["status"] == "AUTHORITY_CONSUMED"})
    return {
        "schema_version": "espresso.val001.invocation_summary.v2",
        "record_id": "VAL001-INVOCATION-SUMMARY-V2",
        "source_of_truth": "validation/val001/VAL_001_INVOCATION_EVENTS.jsonl",
        "counts": {"historical_minimum_known": minimum, "exact_reconstructed_invocations": len(terminals), "failed_invocations": len(failed), "completed_invocations": len(completed), "governed_results": len(governed), "test_or_ci_invocations": len(test_ci), "minimum_known_cumulative_total": minimum + len(terminals)},
        "consumed_authorities": consumed,
        "remaining_real_data_invocations": 0 if consumed else 1,
        "exact_precorrection_local_count": "NOT_RECONSTRUCTABLE_FROM_COMMITTED_EVIDENCE",
        "event_ids": [event["event_id"] for event in events],
        "output_hashes": [event["output_sha256"] for event in completed],
        "claim_boundaries": {"physical_validation": "NOT_ESTABLISHED", "new_governing_physics": "NOT_AUTHORIZED_BY_VAL001"},
    }


def derive_summary_bytes(path: Path, schema: dict[str, Any]) -> bytes:
    return canonical_json(derive_summary(parse_journal(path, schema)))


def verify_summary(journal: Path, event_schema: Path, summary: Path) -> None:
    derived = derive_summary_bytes(journal, load_json(event_schema))
    if derived != summary.read_bytes():
        raise ContractError("JOURNAL_SUMMARY_MISMATCH_MANUAL_RECONCILIATION_REQUIRED")


def classify_reconciliation(journal: Path, event_schema: Path, result: Path, summary: Path, expected_hash: str) -> str:
    try: events = parse_journal(journal, load_json(event_schema))
    except ContractError: return "INVALID_OR_TRUNCATED_JOURNAL_MANUAL_RECONCILIATION_REQUIRED"
    started = any(event["status"] == "STARTED" for event in events)
    completed = [event for event in events if event["status"] == "COMPLETED"]
    if started and not result.exists(): return "STARTED_WITHOUT_RESULT_MANUAL_RECONCILIATION_REQUIRED"
    if result.exists() and not completed: return "RESULT_PRESENT_WITHOUT_COMPLETION_EVENT_MANUAL_RECONCILIATION_REQUIRED"
    if completed and not result.exists(): return "COMPLETION_EVENT_WITHOUT_RESULT_MANUAL_RECONCILIATION_REQUIRED"
    if result.exists() and sha256(result) != expected_hash: return "RESULT_HASH_MISMATCH_MANUAL_RECONCILIATION_REQUIRED"
    try: verify_summary(journal, event_schema, summary)
    except ContractError: return "JOURNAL_SUMMARY_MISMATCH_MANUAL_RECONCILIATION_REQUIRED"
    return "CONSISTENT_CONSUMED_STATE"
