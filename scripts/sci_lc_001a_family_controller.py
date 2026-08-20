#!/usr/bin/env python3
"""Fail-closed SCI-LC-001A execution-family lifecycle controller.

This module controls authority and process lifecycle only. It does not contain
or invoke the scientific dispatcher. Readiness plans are permanently synthetic.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import signal
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "ewp.sci_lc_001a.execution_family.v1"
AUTHORITY_SCHEMA = "ewp.sci_lc_001a.attempt_authority.v1"
STATES = ("UNALLOCATED", "RESERVED", "STARTING", "RUNNING", "STOP_REQUESTED",
          "FINALIZING", "COMPLETE", "FAILED", "STOPPED", "ABORTED_BEFORE_DISPATCH",
          "ARCHIVED", "QUARANTINED")
TERMINAL = frozenset(("COMPLETE", "FAILED", "STOPPED", "ABORTED_BEFORE_DISPATCH",
                      "ARCHIVED", "QUARANTINED"))
TRANSITIONS = {
    "UNALLOCATED": {"RESERVED"}, "RESERVED": {"STARTING", "ABORTED_BEFORE_DISPATCH"},
    "STARTING": {"RUNNING", "STOP_REQUESTED", "FAILED", "ABORTED_BEFORE_DISPATCH"},
    "RUNNING": {"STOP_REQUESTED", "FINALIZING", "FAILED"},
    "STOP_REQUESTED": {"FINALIZING", "STOPPED", "FAILED"},
    "FINALIZING": {"COMPLETE", "FAILED", "STOPPED"},
    "COMPLETE": {"ARCHIVED"}, "FAILED": {"QUARANTINED"},
    "STOPPED": {"QUARANTINED"}, "ABORTED_BEFORE_DISPATCH": {"ARCHIVED"},
    "ARCHIVED": set(), "QUARANTINED": set(),
}
HOLD_GATES = ("allocation", "reservation", "post_reservation", "root_creation",
              "unit_generation", "service_launch", "post_launch_pre_dispatch",
              "dispatch", "replacement", "retry", "resume", "recovery",
              "classification", "publication")


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical_json(value)); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        try: os.unlink(temporary)
        except FileNotFoundError: pass
        raise


@contextmanager
def family_lock(control_root: Path):
    control_root.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(control_root / "family.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN); os.close(descriptor)


def load_closed(path: Path, keys: set[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("AMBIGUOUS_OR_PARTIAL_STATE") from exc
    if set(value) != keys:
        raise ValueError("UNCLOSED_STATE_SCHEMA")
    return value


def authority(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    try: value = json.loads(raw)
    except json.JSONDecodeError as exc: raise ValueError("INVALID_AUTHORITY_JSON") from exc
    required = {"schema", "authorization_id", "attempt_ordinal", "maximum_attempt_ordinal",
                "authorized_head", "authorized_tree", "allowed_root", "profile"}
    if set(value) != required or value["schema"] != AUTHORITY_SCHEMA:
        raise ValueError("INVALID_AUTHORITY_SCHEMA")
    ordinal = value["attempt_ordinal"]
    if not isinstance(ordinal, int) or ordinal < 1 or ordinal > value["maximum_attempt_ordinal"] or ordinal > 4:
        raise ValueError("ATTEMPT_ORDINAL_NOT_AUTHORIZED")
    if not Path(value["allowed_root"]).is_absolute():
        raise ValueError("AUTHORIZED_ROOT_NOT_ABSOLUTE")
    return value, sha256_bytes(raw)


def hold_state(control_root: Path, gate: str, authority_sha256: str | None = None) -> None:
    if gate not in HOLD_GATES: raise ValueError("UNKNOWN_HOLD_GATE")
    path = control_root / "family_hold.json"
    if not path.exists(): raise ValueError("FAMILY_HOLD_RECORD_MISSING")
    value = load_closed(path, {"schema", "state", "authority_sha256", "updated_at_utc"})
    if value["schema"] != SCHEMA or value["state"] != "RELEASED_FOR_EXACT_AUTHORITY":
        raise PermissionError("FAMILY_HOLD_ACTIVE:" + gate)
    if authority_sha256 is not None and value["authority_sha256"] != authority_sha256:
        raise PermissionError("FAMILY_HOLD_AUTHORITY_MISMATCH:" + gate)


def process_identity(attempt_id: str, run_root: Path, authority_sha256: str,
                     unit: str = "NONE") -> dict:
    pid = os.getpid()
    stat = Path(f"/proc/{pid}/stat").read_text().split()
    command = Path(f"/proc/{pid}/cmdline").read_bytes()
    return {"pid": pid, "os_start_ticks": stat[21], "executable": os.readlink(f"/proc/{pid}/exe"),
            "command_sha256": sha256_bytes(command), "working_directory": os.getcwd(),
            "service_unit": unit, "attempt_id": attempt_id, "run_root": str(run_root),
            "authority_sha256": authority_sha256}


def reserve(control_root: Path, authority_path: Path) -> dict:
    auth, auth_hash = authority(authority_path)
    with family_lock(control_root):
        hold_state(control_root, "allocation", auth_hash); hold_state(control_root, "reservation", auth_hash)
        reservation_path = control_root / "reservation.json"
        if reservation_path.exists():
            existing = json.loads(reservation_path.read_text())
            if existing.get("authority_sha256") == auth_hash and existing.get("attempt_ordinal") == auth["attempt_ordinal"]:
                return existing
            raise ValueError("ATTEMPT_SLOT_ALREADY_RESERVED")
        run_root = Path(auth["allowed_root"])
        if run_root.exists(): raise ValueError("ROOT_EXISTS_BEFORE_RESERVATION")
        value = {"schema": SCHEMA, "attempt_id": f"E4-ATTEMPT-{auth['attempt_ordinal']:02d}",
                 "attempt_ordinal": auth["attempt_ordinal"], "maximum_attempt_ordinal": auth["maximum_attempt_ordinal"],
                 "authority_sha256": auth_hash, "authorized_head": auth["authorized_head"],
                 "authorized_tree": auth["authorized_tree"], "run_root": str(run_root),
                 "reserved_at_utc": utc_now(), "state": "RESERVED", "canonical_keys_dispatched": 0,
                 "consumed": False, "controller_identity": process_identity(
                    f"E4-ATTEMPT-{auth['attempt_ordinal']:02d}", run_root, auth_hash)}
        atomic_write(reservation_path, value); hold_state(control_root, "post_reservation", auth_hash)
        return value


def transition(control_root: Path, target: str, *, cause: str, dispatched: int | None = None,
               authority_path: Path | None = None) -> dict:
    if target not in STATES: raise ValueError("UNKNOWN_TARGET_STATE")
    with family_lock(control_root):
        path = control_root / "reservation.json"
        value = json.loads(path.read_text())
        if authority_path is not None:
            _, supplied_hash = authority(authority_path)
            if supplied_hash != value["authority_sha256"]:
                raise PermissionError("TRANSITION_AUTHORITY_MISMATCH")
        current = value["state"]
        if target == current and target in TERMINAL: return value
        if target not in TRANSITIONS[current]: raise ValueError(f"ILLEGAL_TRANSITION:{current}:{target}")
        if target in ("STARTING", "RUNNING"):
            hold_state(control_root, "root_creation" if target == "STARTING" else "post_launch_pre_dispatch",
                       value["authority_sha256"])
        if dispatched is not None:
            if dispatched < value["canonical_keys_dispatched"]: raise ValueError("DISPATCH_COUNT_REGRESSION")
            value["canonical_keys_dispatched"] = dispatched
            value["consumed"] = dispatched > 0
        value.update(state=target, transition_cause=cause, updated_at_utc=utc_now())
        if target in TERMINAL:
            value["terminal"] = True
            value["scientific_eligibility"] = target == "COMPLETE"
            value["lease_state"] = "CLOSED"
        atomic_write(path, value)
        return value


def check_dispatch(control_root: Path) -> None:
    value = json.loads((control_root / "reservation.json").read_text())
    hold_state(control_root, "dispatch", value["authority_sha256"])
    if value["state"] != "RUNNING": raise ValueError("DISPATCH_REQUIRES_RUNNING")


def readiness(control_root: Path) -> dict:
    """Exercise lifecycle wiring with no reference to the canonical dispatcher."""
    hold_state(control_root, "recovery")
    return {"schema": SCHEMA, "mode": "SYNTHETIC_NONCANONICAL_READINESS",
            "canonical_dispatcher_reachable": False, "canonical_keys_dispatched": 0,
            "attempt_budget_consumed": 0, "canonical_attempt_root_created": False}


def recover(control_root: Path, *, process_alive: bool, service_active: bool,
            manifest_state: str | None, lease_state: str | None, root_exists: bool) -> str:
    hold_state(control_root, "recovery")
    combinations = (process_alive, service_active, manifest_state, lease_state, root_exists)
    if manifest_state in TERMINAL and lease_state == "ACTIVE" and not process_alive:
        return "STALE_LEASE_CLOSE_REQUIRED_NO_DISPATCH"
    if process_alive and manifest_state is None:
        return "LIVE_PROCESS_MISSING_MANIFEST_HOLD_NO_DISPATCH"
    if manifest_state in ("STARTING", "RUNNING") and not process_alive:
        return "ORPHANED_MANIFEST_FINALIZATION_REQUIRED_NO_DISPATCH"
    if root_exists != (control_root / "reservation.json").exists():
        return "ROOT_RESERVATION_MISMATCH_HOLD_NO_DISPATCH"
    if service_active != process_alive or (lease_state == "ACTIVE") != process_alive:
        return "PROCESS_SERVICE_LEASE_MISMATCH_HOLD_NO_DISPATCH"
    return "UNIQUELY_RECONCILED_NO_DISPATCH" if combinations else "UNREACHABLE"


def _cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-root", type=Path, required=True)
    parser.add_argument("--mode", choices=("reserve", "transition", "readiness"), required=True)
    parser.add_argument("--authority", type=Path)
    parser.add_argument("--target", choices=STATES)
    parser.add_argument("--cause", default="CLI_REQUEST")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _cli().parse_args(argv)
    if args.mode == "reserve": result = reserve(args.control_root, args.authority)
    elif args.mode == "transition": result = transition(
        args.control_root, args.target, cause=args.cause, authority_path=args.authority)
    else: result = readiness(args.control_root)
    print(json.dumps(result, sort_keys=True, indent=2)); return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except KeyboardInterrupt: raise SystemExit(128 + signal.SIGINT)
