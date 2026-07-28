#!/usr/bin/env python3
"""Read-only verification functions for the v0.1.4 freeze contract."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from artifact_utils import (
    aggregate_records,
    load_json_object,
    sha256_file,
    verify_artifact_records,
)
from generate_source_manifest import excluded


def verify_source_manifest(root: Path, manifest: Mapping[str, Any]) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = []
    expected_files = manifest.get("files", {})
    expected_paths = set(expected_files)
    actual_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not excluded(path.relative_to(root))
    }
    for relative in sorted(actual_paths - expected_paths):
        failures.append({"path": relative, "issue": "unmanifested_source_file"})
    for relative in sorted(expected_paths - actual_paths):
        failures.append({"path": relative, "issue": "manifested_source_file_missing"})

    observed_entries: Dict[str, Dict[str, Any]] = {}
    for relative, metadata in expected_files.items():
        path = root / relative
        if not path.is_file():
            continue
        observed = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "mode": format(path.stat().st_mode & 0o777, "04o"),
        }
        observed_entries[relative] = observed
        expected = {
            "bytes": metadata.get("bytes"),
            "sha256": metadata.get("sha256"),
            "mode": metadata.get("mode"),
        }
        if observed != expected:
            failures.append(
                {
                    "path": relative,
                    "issue": "source_manifest_mismatch",
                    "expected": expected,
                    "observed": observed,
                }
            )

    digest = hashlib.sha256()
    for relative, metadata in sorted(observed_entries.items()):
        digest.update(
            (
                f"{relative}\0{metadata['sha256']}\0{metadata['bytes']}\0"
                f"{metadata['mode']}\n"
            ).encode("utf-8")
        )
    observed_aggregate = (
        digest.hexdigest() if len(observed_entries) == len(expected_files) else None
    )
    recorded_aggregate = manifest.get("aggregate_source_sha256")
    if observed_aggregate != recorded_aggregate:
        failures.append(
            {
                "path": "aggregate_source_sha256",
                "issue": "aggregate_mismatch",
                "expected": recorded_aggregate,
                "observed": observed_aggregate,
            }
        )

    strategy_path = manifest.get("strategy_source_path")
    strategy_hash = manifest.get("strategy_source_sha256")
    if strategy_path:
        path = root / str(strategy_path)
        if not path.is_file() or sha256_file(path) != strategy_hash:
            failures.append(
                {
                    "path": strategy_path,
                    "issue": "controlling_strategy_hash_mismatch_or_missing",
                    "expected_sha256": strategy_hash,
                    "observed_sha256": sha256_file(path) if path.is_file() else None,
                }
            )

    return {
        "status": "PASS" if not failures else "FAIL",
        "checked_file_count": len(expected_files),
        "observed_source_file_count": len(actual_paths),
        "recorded_aggregate_source_sha256": recorded_aggregate,
        "observed_aggregate_source_sha256": observed_aggregate,
        "failures": failures,
    }


def verify_case_manifest(root: Path, manifest: Mapping[str, Any]) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = []
    for relative, expected_hash in manifest.get("scientific_input_sha256", {}).items():
        path = Path(relative)
        path = path if path.is_absolute() else root / path
        if not path.is_file():
            failures.append({"path": relative, "issue": "missing"})
            continue
        observed = sha256_file(path)
        if observed != expected_hash:
            failures.append(
                {
                    "path": relative,
                    "issue": "scientific_input_hash_mismatch",
                    "expected_sha256": expected_hash,
                    "observed_sha256": observed,
                }
            )
    aggregate = hashlib.sha256()
    for relative, expected_hash in sorted(
        manifest.get("scientific_input_sha256", {}).items()
    ):
        aggregate.update(str(relative).encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(str(expected_hash).encode("ascii"))
        aggregate.update(b"\n")
    observed_bundle = aggregate.hexdigest()
    recorded_bundle = manifest.get("scientific_bundle_sha256")
    if observed_bundle != recorded_bundle:
        failures.append(
            {
                "path": "scientific_bundle_sha256",
                "issue": "aggregate_mismatch",
                "expected": recorded_bundle,
                "observed": observed_bundle,
            }
        )
    if manifest.get("manifest_role") != "immutable_scientific_inputs_only":
        failures.append({"issue": "incorrect_manifest_role"})
    if "outputs" in manifest:
        failures.append({"issue": "acyclic_contract_broken_by_outputs_key"})
    return {
        "status": "PASS" if not failures else "FAIL",
        "checked_file_count": len(manifest.get("scientific_input_sha256", {})),
        "scientific_bundle_sha256": recorded_bundle,
        "observed_scientific_bundle_sha256": observed_bundle,
        "failures": failures,
    }


def verify_acceptance_artifacts(
    root: Path, case: Path, acceptance: Mapping[str, Any]
) -> Dict[str, Any]:
    records = []
    for relative, metadata in acceptance.get("artifacts", {}).items():
        records.append(
            {
                "path": str((case / relative).relative_to(root)),
                "role": metadata.get("role", "reference_acceptance_artifact"),
                "bytes": metadata.get("bytes"),
                "sha256": metadata.get("sha256"),
            }
        )
    ok, failures = verify_artifact_records(records, root)
    return {
        "status": "PASS" if ok else "FAIL",
        "checked_artifact_count": len(records),
        "artifact_aggregate_sha256": aggregate_records(records),
        "failures": failures,
    }


def verify_field_index(
    root: Path, case: Path, field_index: Mapping[str, Any]
) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    for item in field_index.get("files", []):
        records.append(
            {
                "path": str((case / str(item.get("path", ""))).relative_to(root)),
                "role": f"openfoam_field:{item.get('field')}@{item.get('time_s')}",
                "bytes": item.get("bytes"),
                "sha256": item.get("sha256"),
            }
        )
    ok, failures = verify_artifact_records(records, root)
    if field_index.get("missing_final_fields"):
        failures.append(
            {
                "issue": "missing_final_fields",
                "fields": field_index.get("missing_final_fields"),
            }
        )
        ok = False
    return {
        "status": "PASS" if ok else "FAIL",
        "checked_field_file_count": len(records),
        "recorded_indexed_file_count": field_index.get("indexed_file_count"),
        "field_content_aggregate_sha256": aggregate_records(records),
        "final_time_directory": field_index.get("final_time_directory"),
        "missing_final_fields": field_index.get("missing_final_fields"),
        "failures": failures,
    }


def verify_qualification_acceptances(
    root: Path, qualification: Mapping[str, Any]
) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    for run_id, run in qualification.get("runs", {}).items():
        relative = run.get("acceptance")
        expected_hash = run.get("acceptance_sha256")
        if not relative or not expected_hash:
            failures.append(
                {"run_id": run_id, "issue": "missing_acceptance_path_or_hash"}
            )
            continue
        path = root / str(relative)
        if not path.is_file():
            failures.append({"run_id": run_id, "path": relative, "issue": "missing"})
            continue
        records.append(
            {
                "path": str(relative),
                "role": f"qualification_acceptance:{run_id}",
                "bytes": path.stat().st_size,
                "sha256": str(expected_hash),
            }
        )
    ok, record_failures = verify_artifact_records(records, root)
    failures.extend(record_failures)
    return {
        "status": "PASS" if ok and not failures else "FAIL",
        "checked_acceptance_count": len(records),
        "acceptance_aggregate_sha256": aggregate_records(records),
        "failures": failures,
    }


def verify_current_qualification_executable(build: Mapping[str, Any]) -> Dict[str, Any]:
    executable = build.get("runtime_executable") or build.get("executable", {})
    path = Path(str(executable.get("path", "")))
    if not path.is_file():
        return {
            "status": "FAIL",
            "path": str(path),
            "issue": "qualification runtime executable missing",
            "recorded": executable,
        }
    observed = {
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "executable": path.stat().st_mode & 0o111 != 0,
    }
    expected = {
        "bytes": executable.get("bytes"),
        "sha256": executable.get("sha256"),
        "executable": True,
    }
    return {
        "status": "PASS" if observed == expected else "FAIL",
        "path": str(path),
        "recorded": expected,
        "observed": observed,
    }


def verify_qualification_executable_binding(
    build: Mapping[str, Any], qualification: Mapping[str, Any]
) -> Dict[str, Any]:
    runtime = build.get("runtime_executable") or build.get("executable", {})
    environment = qualification.get("environment", {})
    recorded_path = str(runtime.get("path", ""))
    qualification_path = str(environment.get("solver_executable", ""))
    expected = {
        "path": str(Path(recorded_path).resolve()) if recorded_path else "",
        "bytes": runtime.get("bytes"),
        "sha256": runtime.get("sha256"),
    }
    observed = {
        "path": str(Path(qualification_path).resolve()) if qualification_path else "",
        "bytes": environment.get("solver_executable_bytes"),
        "sha256": environment.get("solver_executable_sha256"),
    }
    return {
        "status": "PASS" if expected == observed else "FAIL",
        "expected_from_reference_build": expected,
        "observed_in_standard_qualification": observed,
    }


def verify_archived_executable(root: Path, build: Mapping[str, Any]) -> Dict[str, Any]:
    executable = build.get("archived_executable", {})
    raw_path = Path(str(executable.get("path", "")))
    if raw_path.is_absolute():
        return {
            "status": "FAIL",
            "path": str(raw_path),
            "issue": "portable archived executable path is not package-relative",
            "recorded": executable,
        }
    path = root / raw_path
    if not path.is_file():
        return {
            "status": "FAIL",
            "path": str(path),
            "issue": "portable archived executable missing",
            "recorded": executable,
        }
    observed = {
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "executable": path.stat().st_mode & 0o111 != 0,
    }
    expected = {
        "bytes": executable.get("bytes"),
        "sha256": executable.get("sha256"),
        "executable": True,
    }
    return {
        "status": "PASS" if observed == expected else "FAIL",
        "path": str(path),
        "recorded": expected,
        "observed": observed,
    }


def required_status_failures(
    acceptance: Mapping[str, Any],
    qualification: Mapping[str, Any],
    run_status: Mapping[str, Any],
    finalization: Mapping[str, Any],
    no_physics_reference: Mapping[str, Any],
    no_physics_qualification: Mapping[str, Any],
) -> List[str]:
    failures: List[str] = []
    if acceptance.get("status") != "PASS":
        failures.append("reference acceptance is not PASS")
    if acceptance.get("reference_qualification_status") != "PASS":
        failures.append("reference qualification status is not PASS")
    if acceptance.get("reference_freeze_status") != "QUALIFIED":
        failures.append("reference acceptance is not QUALIFIED")
    if not acceptance.get("all_required_freeze_prerequisites_pass"):
        failures.append("acceptance freeze prerequisites are not PASS")
    if qualification.get("status") != "PASS" or qualification.get("profile") != "standard":
        failures.append("standard qualification is not PASS")
    if not qualification.get("all_required_gates_pass"):
        failures.append("standard qualification aggregate gate flag is false")
    if run_status.get("status") != "PASS":
        failures.append("reference run status is not PASS")
    if run_status.get("reference_qualification_status") != "PASS":
        failures.append("run status was not finalized with qualification PASS")
    if finalization.get("status") != "PASS":
        failures.append("freeze finalization status is not PASS")
    for label, report in (
        ("reference", no_physics_reference),
        ("qualification", no_physics_qualification),
    ):
        if report.get("status") != "PASS" or report.get("governing_physics_change") is not False:
            failures.append(f"{label} no-physics-change verification is not PASS")
    return failures
