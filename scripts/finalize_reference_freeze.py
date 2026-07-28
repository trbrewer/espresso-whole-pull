#!/usr/bin/env python3
"""Finalize v0.1.4 acceptance and run status after standard Allverify passes.

This script deliberately does not generate the terminal freeze manifest.  It
updates all mutable controlling records first; generate_freeze_manifest.py then
hashes those final records as the last artifact in the provenance chain.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from artifact_utils import (  # noqa: E402
    artifact_record,
    atomic_write_json,
    load_json_object,
    sha256_file,
    verify_artifact_record,
)
from freeze_contract import verify_qualification_executable_binding  # noqa: E402

PACKAGE_VERSION = "0.1.4"
CASE = Path("cases/reference_R0_20g_58mm_9bar")
ACCEPTANCE = CASE / "ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json"
RUN_STATUS = CASE / "ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json"
CASE_MANIFEST = CASE / "ESPRESSO_WHOLE_PULL_REFERENCE_CASE_MANIFEST_V0_1_4.json"
QUALIFICATION = Path(
    "qualification/ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json"
)
NO_PHYSICS_REFERENCE = (
    CASE / "preflight/NO_PHYSICS_CHANGE_VERIFICATION_V0_1_4.json"
)
NO_PHYSICS_QUALIFICATION = Path(
    "qualification/NO_PHYSICS_CHANGE_VERIFICATION_STANDARD_V0_1_4.json"
)
FINALIZATION_STATUS = Path(
    "qualification/ESPRESSO_WHOLE_PULL_FREEZE_FINALIZATION_STATUS_V0_1_4.json"
)
BUILD_PROVENANCE = CASE / "preflight/BUILD_PROVENANCE_V0_1_4.json"
BUILD_VERIFICATION = CASE / "preflight/BUILD_PROVENANCE_VERIFICATION_V0_1_4.json"

REQUIRED_BOUNDED_GATES = (
    "concentration_below_declared_capacity",
    "remaining_extractable_inventory_bounded",
    "retained_water_bounded_by_pore_capacity",
)
REQUIRED_MONOTONICITY_GATES = (
    "cumulative_inlet_water_monotonic",
    "cumulative_cup_water_monotonic",
    "cumulative_cup_solute_monotonic",
)


def resolve(root: Path, value: Path) -> Path:
    return value if value.is_absolute() else root / value


def verify_acceptance_artifacts(
    root: Path, case: Path, acceptance: Mapping[str, Any]
) -> Tuple[bool, List[Dict[str, Any]]]:
    failures: List[Dict[str, Any]] = []
    for relative, expected in acceptance.get("artifacts", {}).items():
        record = {
            "path": str((case / relative).relative_to(root)),
            "bytes": expected.get("bytes"),
            "sha256": expected.get("sha256"),
        }
        ok, detail = verify_artifact_record(record, root)
        if not ok:
            failures.append(detail)
    return not failures, failures


def verify_case_manifest_inputs(
    root: Path, manifest: Mapping[str, Any]
) -> Tuple[bool, List[Dict[str, Any]]]:
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
                    "issue": "hash_mismatch",
                    "expected_sha256": expected_hash,
                    "observed_sha256": observed,
                }
            )
    return not failures, failures


def verify_qualification_acceptances(
    root: Path, qualification: Mapping[str, Any]
) -> Tuple[bool, List[Dict[str, Any]]]:
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
        observed = sha256_file(path)
        if observed != expected_hash:
            failures.append(
                {
                    "run_id": run_id,
                    "path": relative,
                    "issue": "hash_mismatch",
                    "expected_sha256": expected_hash,
                    "observed_sha256": observed,
                }
            )
    return not failures, failures


def gate_failures(acceptance: Mapping[str, Any]) -> List[str]:
    failures: List[str] = []
    if acceptance.get("status") != "PASS":
        failures.append("reference acceptance status is not PASS")
    if not acceptance.get("all_required_reference_gates_pass"):
        failures.append("reference numerical/B0/bounded/monotonic gates are not all PASS")
    if not acceptance.get("all_required_bounded_state_gates_pass"):
        failures.append("bounded-state gate family is not PASS")
    if not acceptance.get("all_required_monotonicity_gates_pass"):
        failures.append("monotonicity gate family is not PASS")
    gates = acceptance.get("numerical_acceptance_gates", {})
    for name in (*REQUIRED_BOUNDED_GATES, *REQUIRED_MONOTONICITY_GATES):
        if gates.get(name, {}).get("status") != "PASS":
            failures.append(f"required explicit gate not PASS: {name}")
    return failures


def write_failure_status(
    path: Path, stage: str, failures: Iterable[Any], qualification_path: Path
) -> None:
    report = {
        "schema_version": "espresso.whole_pull.freeze_finalization_status.v0.1.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "package_version": PACKAGE_VERSION,
        "status": "FAIL",
        "stage": stage,
        "reference_freeze_status": "NOT_FROZEN",
        "failures": list(failures),
        "qualification_report": str(qualification_path),
    }
    atomic_write_json(path, report)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--acceptance", type=Path, default=ACCEPTANCE)
    parser.add_argument("--run-status", type=Path, default=RUN_STATUS)
    parser.add_argument("--qualification", type=Path, default=QUALIFICATION)
    parser.add_argument("--status-output", type=Path, default=FINALIZATION_STATUS)
    args = parser.parse_args()

    root = args.root.resolve()
    case = root / CASE
    acceptance_path = resolve(root, args.acceptance)
    run_status_path = resolve(root, args.run_status)
    qualification_path = resolve(root, args.qualification)
    status_path = resolve(root, args.status_output)

    required = [
        acceptance_path,
        run_status_path,
        qualification_path,
        root / CASE_MANIFEST,
        root / NO_PHYSICS_REFERENCE,
        root / NO_PHYSICS_QUALIFICATION,
        root / BUILD_PROVENANCE,
        root / BUILD_VERIFICATION,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        write_failure_status(status_path, "required_artifacts", missing, qualification_path)
        raise SystemExit("Freeze finalization missing required artifacts:\n- " + "\n- ".join(missing))

    acceptance = load_json_object(acceptance_path)
    run_status = load_json_object(run_status_path)
    qualification = load_json_object(qualification_path)
    case_manifest = load_json_object(root / CASE_MANIFEST)
    reference_no_physics = load_json_object(root / NO_PHYSICS_REFERENCE)
    qualification_no_physics = load_json_object(root / NO_PHYSICS_QUALIFICATION)
    build_provenance = load_json_object(root / BUILD_PROVENANCE)
    build_verification = load_json_object(root / BUILD_VERIFICATION)

    failures: List[Any] = gate_failures(acceptance)
    if qualification.get("profile") != "standard":
        failures.append("qualification profile is not standard")
    if qualification.get("status") != "PASS":
        failures.append("qualification status is not PASS")
    if not qualification.get("all_required_gates_pass"):
        failures.append("qualification all_required_gates_pass is not true")
    if qualification.get("gate_summary", {}).get("pass") != 9:
        failures.append("standard qualification does not record all nine PASS gates")
    if len(qualification.get("runs", {})) != 10:
        failures.append("standard qualification does not record all ten matrix runs")
    if build_verification.get("status") != "PASS":
        failures.append("exact reference build verification is not PASS")
    for key in (
        "build_input_hashes_match",
        "executable_hash_matches",
        "archived_executable_hash_matches",
        "runtime_archive_identity_matches",
        "openfoam_build_environment_matches",
    ):
        if not build_verification.get(key):
            failures.append(f"build verification flag is not true: {key}")
    qualification_executable_binding = verify_qualification_executable_binding(
        build_provenance, qualification
    )
    if qualification_executable_binding.get("status") != "PASS":
        failures.append({"qualification_executable_binding": qualification_executable_binding})
    if run_status.get("status") != "PASS" or run_status.get("execution_status") != "COMPLETED":
        failures.append("reference run status is not a completed PASS")
    if case_manifest.get("manifest_role") != "immutable_scientific_inputs_only":
        failures.append("case manifest is not immutable scientific inputs only")
    if "outputs" in case_manifest:
        failures.append("case manifest contains mutable downstream outputs")
    for label, report in (
        ("reference", reference_no_physics),
        ("qualification", qualification_no_physics),
    ):
        if report.get("status") != "PASS" or report.get("governing_physics_change") is not False:
            failures.append(f"{label} no-physics-change verification is not PASS")

    artifacts_ok, artifact_failures = verify_acceptance_artifacts(root, case, acceptance)
    if not artifacts_ok:
        failures.append({"acceptance_artifact_failures": artifact_failures})
    inputs_ok, input_failures = verify_case_manifest_inputs(root, case_manifest)
    if not inputs_ok:
        failures.append({"scientific_input_failures": input_failures})
    matrix_ok, matrix_failures = verify_qualification_acceptances(root, qualification)
    if not matrix_ok:
        failures.append({"qualification_acceptance_failures": matrix_failures})

    if failures:
        write_failure_status(status_path, "prerequisite_verification", failures, qualification_path)
        raise SystemExit(
            "Freeze finalization prerequisites failed:\n- "
            + "\n- ".join(json.dumps(item, sort_keys=True) if not isinstance(item, str) else item for item in failures)
        )

    finalized_at = datetime.now(timezone.utc).isoformat()
    qualification_record = artifact_record(
        qualification_path, root, "standard_numerical_qualification"
    )
    reference_no_physics_record = artifact_record(
        root / NO_PHYSICS_REFERENCE, root, "reference_no_physics_change_verification"
    )
    qualification_no_physics_record = artifact_record(
        root / NO_PHYSICS_QUALIFICATION,
        root,
        "qualification_no_physics_change_verification",
    )

    acceptance["qualification_finalized_at_utc"] = finalized_at
    acceptance["qualified_after_standard_Allverify"] = True
    acceptance["reference_qualification_status"] = "PASS"
    acceptance["release_provenance_status"] = "READY_FOR_TERMINAL_FREEZE_MANIFEST"
    acceptance["reference_freeze_status"] = "QUALIFIED"
    acceptance["all_required_freeze_prerequisites_pass"] = True
    acceptance["qualification_report"] = {
        **qualification_record,
        "profile": qualification.get("profile"),
        "status": qualification.get("status"),
        "all_required_gates_pass": qualification.get("all_required_gates_pass"),
        "gate_summary": qualification.get("gate_summary"),
        "qualification_completed_at_utc": qualification.get(
            "qualification_completed_at_utc", qualification.get("generated_at_utc")
        ),
    }
    acceptance["freeze_finalization_prerequisites"] = {
        "status": "PASS",
        "finalized_at_utc": finalized_at,
        "bounded_gate_names": list(REQUIRED_BOUNDED_GATES),
        "monotonicity_gate_names": list(REQUIRED_MONOTONICITY_GATES),
        "scientific_input_manifest_verification": {
            "status": "PASS",
            "checked_file_count": len(case_manifest.get("scientific_input_sha256", {})),
        },
        "reference_artifact_verification": {
            "status": "PASS",
            "checked_artifact_count": len(acceptance.get("artifacts", {})),
        },
        "qualification_acceptance_verification": {
            "status": "PASS",
            "checked_acceptance_count": len(qualification.get("runs", {})),
        },
        "qualification_executable_binding": qualification_executable_binding,
        "exact_reference_build_verification": {
            "status": "PASS",
            "path": str(BUILD_VERIFICATION),
            "sha256": sha256_file(root / BUILD_VERIFICATION),
        },
        "no_physics_change_verification": {
            "reference": reference_no_physics_record,
            "qualification": qualification_no_physics_record,
        },
        "terminal_freeze_manifest": "PENDING_GENERATION_AS_FINAL_CONTROLLING_ARTIFACT",
    }
    atomic_write_json(acceptance_path, acceptance)
    final_acceptance_record = artifact_record(
        acceptance_path, root, "qualified_reference_acceptance"
    )

    # Finalize the operational record before the terminal manifest is generated.
    run_status["qualification_finalized_at_utc"] = finalized_at
    run_status["qualified_after_standard_Allverify"] = True
    run_status["reference_qualification_status"] = "PASS"
    run_status["release_provenance_status"] = "READY_FOR_TERMINAL_FREEZE_MANIFEST"
    run_status["reference_freeze_status"] = "QUALIFIED_PENDING_TERMINAL_MANIFEST"
    run_status.setdefault("artifacts", {})["reference_acceptance"] = {
        **final_acceptance_record,
        "status": acceptance.get("status"),
        "reference_qualification_status": acceptance.get(
            "reference_qualification_status"
        ),
        "reference_freeze_status": acceptance.get("reference_freeze_status"),
    }
    run_status["artifacts"]["full_numerical_qualification"] = {
        **qualification_record,
        "status": qualification.get("status"),
        "profile": qualification.get("profile"),
        "gate_summary": qualification.get("gate_summary"),
    }
    run_status["freeze_finalization"] = {
        "status": "PASS",
        "finalized_at_utc": finalized_at,
        "acceptance_sha256": final_acceptance_record["sha256"],
        "qualification_sha256": qualification_record["sha256"],
        "terminal_manifest": "PENDING",
    }
    atomic_write_json(run_status_path, run_status)
    final_run_status_record = artifact_record(
        run_status_path, root, "finalized_reference_run_status"
    )

    finalization_status = {
        "schema_version": "espresso.whole_pull.freeze_finalization_status.v0.1.4",
        "generated_at_utc": finalized_at,
        "package_version": PACKAGE_VERSION,
        "status": "PASS",
        "stage": "acceptance_and_run_status_finalized",
        "qualified_after_standard_Allverify": True,
        "reference_qualification_status": "PASS",
        "release_provenance_status": "READY_FOR_TERMINAL_FREEZE_MANIFEST",
        "reference_freeze_status": "QUALIFIED_PENDING_TERMINAL_MANIFEST",
        "qualified_acceptance": final_acceptance_record,
        "finalized_run_status": final_run_status_record,
        "standard_qualification": qualification_record,
        "terminal_freeze_manifest": "PENDING_GENERATION_AS_FINAL_CONTROLLING_ARTIFACT",
    }
    atomic_write_json(status_path, finalization_status)

    print(
        json.dumps(
            {
                "status": "PASS",
                "reference_qualification_status": "PASS",
                "reference_freeze_status": "QUALIFIED_PENDING_TERMINAL_MANIFEST",
                "acceptance": str(acceptance_path),
                "run_status": str(run_status_path),
                "finalization_status": str(status_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
