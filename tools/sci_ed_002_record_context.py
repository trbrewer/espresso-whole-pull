"""Validation for the portable SCI-ED-002 final record context."""

from __future__ import annotations

from pathlib import Path


class RecordContextError(ValueError):
    pass


def validate_record_context(activation: dict, result: dict) -> None:
    required = {"path", "branch", "base", "base_tree", "r0_head", "r0_tree"}
    if missing := required - set(activation):
        raise RecordContextError(f"MISSING_CONTEXT_FIELD:{sorted(missing)[0]}")
    path = activation["path"]
    if not isinstance(path, str) or path.startswith("/") or Path(path).is_absolute():
        raise RecordContextError("MACHINE_LOCAL_ABSOLUTE_PATH")
    if activation["branch"] != "research/sci-ed-002-measurement-contract-handoff":
        raise RecordContextError("WRONG_REPOSITORY_AUTHORITY")
    if result.get("disposition") != "SCI_ED_002_PROTOCOL_INCOMPLETE_COMMISSIONING_BLOCKED_REFERENCE_EXTRACTABILITY_STOPPING_RULE_NOT_DEFENSIBLY_FROZEN":
        raise RecordContextError("SCIENTIFIC_DISPOSITION_CHANGED")
    if result.get("commissioning_authorized") is not False:
        raise RecordContextError("COMMISSIONING_TRUE")
    if result.get("predictor_eligible") is not False:
        raise RecordContextError("PREDICTOR_ELIGIBILITY_TRUE")
    if result.get("c_s0_mapping_status") != "NOT_ESTABLISHED":
        raise RecordContextError("C_S0_ESTABLISHED")
    if result.get("consumer_status") != "PENDING_FINAL_HEAD_QUALIFICATION":
        raise RecordContextError("INCONSISTENT_STATUS")
