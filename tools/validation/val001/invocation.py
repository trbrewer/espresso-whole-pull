"""Durable synthetic invocation state and canonical consumed-state checks."""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator

from .framework import ContractError, canonical_json, load_json, sha256, validate_record

LOCK_PATH = "validation/val001/contracts/VAL_001_POSTRESULT_EXECUTION_LOCK.json"
LEDGER_PATH = "validation/val001/VAL_001_INVOCATION_ACCOUNTING_CONTRACT.json"
JOURNAL_PATH = "validation/val001/VAL_001_INVOCATION_EVENTS.jsonl"
V2_PATH = "validation/val001/results/VAL_001_CORRECTED_COMPONENT_COMPARISONS_V2.json"
EXPECTED_V2_SHA256 = "7968e3b99045da9500442932c536bf920d559ebe660d2bad01f954f36b3f75b5"


def atomic_write(path: Path, data: bytes, validator: Callable[[Path], None] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        if validator:
            validator(temp_path)
        os.replace(temp_path, path)
        directory = os.open(path.parent, os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if temp_path.exists(): temp_path.unlink()


def append_event(path: Path, event: dict[str, Any], event_schema: dict[str, Any]) -> None:
    validate_record(event, event_schema)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as stream:
        stream.write(json.dumps(event, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n")
        stream.flush(); os.fsync(stream.fileno())


@contextmanager
def exclusive_authority(lock_file: Path) -> Iterator[None]:
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with lock_file.open("a+b") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ContractError("authority already locked by another process") from exc
        yield


def synthetic_transaction(root: Path, authority_id: str, operation: Callable[[], dict[str, Any]], event_schema: dict[str, Any], fail_stage: str | None = None) -> dict[str, Any]:
    """Exercise state mechanics with synthetic data only."""
    journal = root / "events.jsonl"; lock_file = root / "authority.lock"; result_path = root / "result.json"
    with exclusive_authority(lock_file):
        prior = journal.read_text().splitlines() if journal.exists() else []
        events = [json.loads(line) for line in prior]
        if any(event["authority_id"] == authority_id for event in events):
            raise ContractError("authority consumed or manual reconciliation required")
        started = {"event_id": f"{authority_id}-STARTED", "authority_id": authority_id, "status": "STARTED", "source_opened": false_value(), "score_exposed": false_value(), "output_sha256": None, "failure_reason": None}
        append_event(journal, started, event_schema)
        if fail_stage == "after_started":
            raise ContractError("synthetic interruption after STARTED")
        try:
            result = operation()
            if fail_stage == "assembly": raise RuntimeError("synthetic assembly failure")
            atomic_write(result_path, canonical_json(result), lambda p: load_json(p))
            if fail_stage == "completion": raise RuntimeError("synthetic completion failure")
            completed = {"event_id": f"{authority_id}-COMPLETED", "authority_id": authority_id, "status": "COMPLETED", "source_opened": true_value(), "score_exposed": true_value(), "output_sha256": sha256(result_path), "failure_reason": None}
            append_event(journal, completed, event_schema)
            return result
        except Exception as exc:
            failed = {"event_id": f"{authority_id}-FAILED", "authority_id": authority_id, "status": "FAILED", "source_opened": true_value(), "score_exposed": true_value(), "output_sha256": sha256(result_path) if result_path.exists() else None, "failure_reason": type(exc).__name__}
            append_event(journal, failed, event_schema)
            raise


def false_value() -> bool: return False
def true_value() -> bool: return True


def verify_consumed_state(root: Path) -> None:
    lock_path = root / LOCK_PATH
    if not lock_path.is_file():
        raise ContractError("canonical post-result execution lock missing")
    lock = load_json(lock_path)
    if lock.get("authority_status") != "CONSUMED" or lock.get("remaining_real_data_comparison_invocations") != 0 or lock.get("further_retry_authorized") is not False:
        raise ContractError("post-result execution authority is not consumed")
    if sha256(root / V2_PATH) != EXPECTED_V2_SHA256:
        raise ContractError("bound V2 result mismatch")
    for binding in lock["bindings"]:
        path = root / binding["path"]
        if not path.is_file() or sha256(path) != binding["sha256"]:
            raise ContractError(f"consumed-state binding mismatch: {binding['path']}")
    raise ContractError("VAL001_EXECUTION_AUTHORITY_CONSUMED_NO_FURTHER_INVOCATION")
