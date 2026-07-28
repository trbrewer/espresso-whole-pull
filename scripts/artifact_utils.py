#!/usr/bin/env python3
"""Small standard-library helpers for immutable v0.1.4 artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def sha256_canonical_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def load_json_object(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - message tested through callers
        raise ValueError(f"Unable to read JSON object {path}: {type(exc).__name__}: {exc}")
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def safe_relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except (OSError, ValueError):
        return str(path)


def artifact_record(path: Path, root: Path, role: str = "artifact") -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Required artifact missing: {path}")
    return {
        "path": safe_relative(path, root),
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def verify_artifact_record(
    record: Mapping[str, Any], root: Path
) -> Tuple[bool, Dict[str, Any]]:
    path = root / str(record.get("path", ""))
    if not path.is_file():
        return False, {"path": record.get("path"), "issue": "missing"}
    observed = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    expected = {"bytes": record.get("bytes"), "sha256": record.get("sha256")}
    if observed != expected:
        return False, {
            "path": record.get("path"),
            "issue": "hash_or_size_mismatch",
            "expected": expected,
            "observed": observed,
        }
    return True, {"path": record.get("path"), "status": "PASS"}


def verify_artifact_records(
    records: Iterable[Mapping[str, Any]], root: Path
) -> Tuple[bool, List[Dict[str, Any]]]:
    failures: List[Dict[str, Any]] = []
    for record in records:
        ok, detail = verify_artifact_record(record, root)
        if not ok:
            failures.append(detail)
    return not failures, failures


def aggregate_records(records: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    normalized = sorted(
        records,
        key=lambda item: (str(item.get("path", "")), str(item.get("role", ""))),
    )
    for item in normalized:
        digest.update(str(item.get("path", "")).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(item.get("role", "")).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(item.get("sha256", "")).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(item.get("bytes", "")).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()
