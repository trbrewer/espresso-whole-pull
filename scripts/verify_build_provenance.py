#!/usr/bin/env python3
"""Verify the exact v0.1.4 runtime solver and its portable archived copy."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

PACKAGE_VERSION = "0.1.4"
DEFAULT_PROVENANCE = Path(
    "cases/reference_R0_20g_58mm_9bar/preflight/BUILD_PROVENANCE_V0_1_4.json"
)
DEFAULT_OUTPUT = Path(
    "cases/reference_R0_20g_58mm_9bar/preflight/"
    "BUILD_PROVENANCE_VERIFICATION_V0_1_4.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return value


def resolve_record_path(root: Path, record: Mapping[str, Any]) -> Path:
    raw = Path(str(record.get("path", "")))
    return raw if raw.is_absolute() else root / raw


def verify_file_record(
    root: Path, record: Mapping[str, Any], *, require_executable: bool
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    path = resolve_record_path(root, record)
    expected: Dict[str, Any] = {
        "bytes": record.get("bytes"),
        "sha256": record.get("sha256"),
    }
    if require_executable:
        expected["executable"] = True
    if path.is_file():
        observed: Optional[Dict[str, Any]] = {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        if require_executable:
            observed["executable"] = os.access(path, os.X_OK)
        status = "PASS" if observed == expected else "FAIL"
    else:
        observed = None
        status = "FAIL"
    result = {
        "path": str(path),
        "status": status,
        "expected": expected,
        "observed": observed,
    }
    failure = None if status == "PASS" else result
    return result, failure


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    provenance_path = args.provenance or DEFAULT_PROVENANCE
    provenance_path = (
        provenance_path if provenance_path.is_absolute() else root / provenance_path
    )
    output = args.output or DEFAULT_OUTPUT
    output = output if output.is_absolute() else root / output
    output.parent.mkdir(parents=True, exist_ok=True)

    failures: List[Dict[str, Any]] = []
    if not provenance_path.is_file():
        raise SystemExit(
            f"Reference build provenance missing: {provenance_path}. Run ./Allrun first."
        )
    provenance = load(provenance_path)

    input_results: List[Dict[str, Any]] = []
    for expected in provenance.get("build_inputs", []):
        path = root / str(expected.get("path", ""))
        if not path.is_file():
            result = {
                "path": str(expected.get("path")),
                "status": "FAIL",
                "issue": "missing",
            }
            failures.append(result)
            input_results.append(result)
            continue
        observed = {"bytes": path.stat().st_size, "sha256": sha256(path)}
        expected_identity = {
            "bytes": expected.get("bytes"),
            "sha256": expected.get("sha256"),
        }
        status = "PASS" if observed == expected_identity else "FAIL"
        result = {
            "path": str(expected.get("path")),
            "status": status,
            "expected": expected_identity,
            "observed": observed,
        }
        input_results.append(result)
        if status != "PASS":
            failures.append(result)

    runtime_record = provenance.get("runtime_executable") or provenance.get("executable") or {}
    runtime_result, runtime_failure = verify_file_record(
        root, runtime_record, require_executable=True
    )
    if runtime_failure is not None:
        failures.append({"artifact": "runtime_executable", **runtime_failure})

    archive_record = provenance.get("archived_executable") or {}
    archive_result, archive_failure = verify_file_record(
        root, archive_record, require_executable=True
    )
    if archive_failure is not None:
        failures.append({"artifact": "archived_executable", **archive_failure})

    runtime_observed = runtime_result.get("observed")
    archive_observed = archive_result.get("observed")
    runtime_archive_identity_matches = bool(
        runtime_result.get("status") == "PASS"
        and archive_result.get("status") == "PASS"
        and isinstance(runtime_observed, dict)
        and isinstance(archive_observed, dict)
        and runtime_observed.get("bytes") == archive_observed.get("bytes")
        and runtime_observed.get("sha256") == archive_observed.get("sha256")
    )
    if not runtime_archive_identity_matches:
        failures.append(
            {
                "artifact": "runtime_archive_identity",
                "runtime": runtime_result,
                "archive": archive_result,
            }
        )

    recorded_environment = provenance.get("environment", {})
    environment_checks: Dict[str, Dict[str, Any]] = {}
    for name in ("WM_PROJECT", "WM_PROJECT_VERSION", "WM_OPTIONS"):
        recorded = recorded_environment.get(name)
        current = os.environ.get(name)
        status = "PASS" if recorded not in (None, "") and current == recorded else "FAIL"
        environment_checks[name] = {
            "status": status,
            "recorded": recorded,
            "current": current,
        }
        if status != "PASS":
            failures.append({"environment": name, **environment_checks[name]})

    build_input_hashes_match = all(item["status"] == "PASS" for item in input_results)
    executable_hash_matches = runtime_result.get("status") == "PASS"
    archived_executable_hash_matches = archive_result.get("status") == "PASS"
    environment_matches = all(
        item["status"] == "PASS" for item in environment_checks.values()
    )
    status = (
        "PASS"
        if provenance.get("status") == "PASS"
        and build_input_hashes_match
        and executable_hash_matches
        and archived_executable_hash_matches
        and runtime_archive_identity_matches
        and environment_matches
        and not failures
        else "FAIL"
    )

    report = {
        "schema_version": "espresso.whole_pull.build_provenance_verification.v0.1.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "package_version": PACKAGE_VERSION,
        "status": status,
        "reference_build_provenance": {
            "path": str(provenance_path.relative_to(root)),
            "bytes": provenance_path.stat().st_size,
            "sha256": sha256(provenance_path),
            "generated_at_utc": provenance.get("generated_at_utc"),
            "source_and_executable_bundle_sha256": provenance.get(
                "source_and_executable_bundle_sha256"
            ),
        },
        "build_input_hashes_match": build_input_hashes_match,
        "executable_hash_matches": executable_hash_matches,
        "archived_executable_hash_matches": archived_executable_hash_matches,
        "runtime_archive_identity_matches": runtime_archive_identity_matches,
        "openfoam_build_environment_matches": environment_matches,
        "build_inputs": input_results,
        "runtime_executable": runtime_result,
        "archived_executable": archive_result,
        # Backward-compatible alias retained for existing readers.
        "executable": runtime_result,
        "environment": environment_checks,
        "failures": failures,
        "qualification_build_policy": (
            "Standard Allverify reuses the exact runtime executable that produced "
            "the reference Allrun. The same bytes are archived inside the case and "
            "bound by the terminal freeze manifest for portable later verification."
        ),
    }
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(
        json.dumps(
            {
                "status": status,
                "report": str(output),
                "runtime_executable": runtime_result.get("path"),
                "archived_executable": archive_result.get("path"),
                "executable_sha256": (
                    runtime_observed.get("sha256")
                    if isinstance(runtime_observed, dict)
                    else None
                ),
            },
            indent=2,
        )
    )
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
