#!/usr/bin/env python3
"""Read-only verification of the terminal v0.1.4 freeze manifest."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from artifact_utils import (  # noqa: E402
    aggregate_records,
    load_json_object,
    sha256_file,
    verify_artifact_records,
)
from freeze_contract import (  # noqa: E402
    required_status_failures,
    verify_acceptance_artifacts,
    verify_archived_executable,
    verify_case_manifest,
    verify_field_index,
    verify_qualification_acceptances,
    verify_qualification_executable_binding,
    verify_source_manifest,
)

CASE = Path("cases/reference_R0_20g_58mm_9bar")
DEFAULT_MANIFEST = CASE / "ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    root = args.root.resolve()
    manifest_path = args.manifest if args.manifest.is_absolute() else root / args.manifest
    if not manifest_path.is_file():
        raise SystemExit(f"Terminal freeze manifest missing: {manifest_path}")
    manifest = load_json_object(manifest_path)

    source_manifest = load_json_object(root / "SOURCE_PACKAGE_MANIFEST.json")
    case_manifest = load_json_object(
        root / CASE / "ESPRESSO_WHOLE_PULL_REFERENCE_CASE_MANIFEST_V0_1_4.json"
    )
    acceptance = load_json_object(
        root / CASE / "ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json"
    )
    run_status = load_json_object(
        root / CASE / "ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json"
    )
    qualification = load_json_object(
        root / "qualification/ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json"
    )
    finalization = load_json_object(
        root / "qualification/ESPRESSO_WHOLE_PULL_FREEZE_FINALIZATION_STATUS_V0_1_4.json"
    )
    no_physics_reference = load_json_object(
        root / CASE / "preflight/NO_PHYSICS_CHANGE_VERIFICATION_V0_1_4.json"
    )
    no_physics_qualification = load_json_object(
        root / "qualification/NO_PHYSICS_CHANGE_VERIFICATION_STANDARD_V0_1_4.json"
    )
    reference_build = load_json_object(
        root / CASE / "preflight/BUILD_PROVENANCE_V0_1_4.json"
    )
    reference_build_verification = load_json_object(
        root / CASE / "preflight/BUILD_PROVENANCE_VERIFICATION_V0_1_4.json"
    )
    field_index = load_json_object(
        root / CASE / "ESPRESSO_WHOLE_PULL_REFERENCE_FIELD_INDEX_V0_1_4.json"
    )

    failures: List[Any] = []
    if manifest.get("status") != "PASS":
        failures.append("terminal manifest status is not PASS")
    if manifest.get("reference_freeze_status") != "FROZEN / QUALIFIED":
        failures.append("terminal reference_freeze_status is not FROZEN / QUALIFIED")
    for key in (
        "implementation_status",
        "code_verification_status",
        "numerical_qualification_status",
        "release_provenance_status",
    ):
        if manifest.get(key) != "PASS":
            failures.append(f"terminal {key} is not PASS")
    if manifest.get("physical_validation_status") != "NOT_ESTABLISHED":
        failures.append("physical validation status was overstated")
    if manifest.get("next_scientific_milestone") != "WP-0.1R":
        failures.append("next scientific milestone is not WP-0.1R")
    if manifest.get("governing_physics_change_from_qualified_v0_1_3") is not False:
        failures.append("terminal manifest does not prove no governing-physics change")
    if manifest.get("wp_milestone") != "WP-0.1H_COMPLETE":
        failures.append("WP-0.1H completion identity is missing")
    if manifest.get("release_role") != "WP-0.1F_NO_PHYSICS_CHANGE_FREEZE_FINALIZATION":
        failures.append("WP-0.1F release role is incorrect")
    if manifest.get("acyclic_provenance", {}).get("status") != "PASS":
        failures.append("acyclic provenance status is not PASS")
    if not manifest.get("solver_build", {}).get(
        "exact_build_reused_for_standard_qualification"
    ):
        failures.append("terminal manifest does not bind exact-build reuse")
    if manifest.get("solver_build", {}).get(
        "qualification_executable_binding", {}
    ).get("status") != "PASS":
        failures.append("terminal manifest does not record a PASS qualification-executable binding")

    records = manifest.get("controlling_artifacts", [])
    if any(str(item.get("path")) == str(DEFAULT_MANIFEST) for item in records):
        failures.append("terminal freeze manifest incorrectly self-includes")
    ok, record_failures = verify_artifact_records(records, root)
    if not ok:
        failures.append({"controlling_artifact_failures": record_failures})
    aggregate = aggregate_records(records)
    if aggregate != manifest.get("controlling_artifact_aggregate_sha256"):
        failures.append(
            {
                "issue": "controlling_artifact_aggregate_mismatch",
                "expected": manifest.get("controlling_artifact_aggregate_sha256"),
                "observed": aggregate,
            }
        )

    status_failures = required_status_failures(
        acceptance,
        qualification,
        run_status,
        finalization,
        no_physics_reference,
        no_physics_qualification,
    )
    failures.extend(status_failures)
    checks: Dict[str, Dict[str, Any]] = {
        "source_package": verify_source_manifest(root, source_manifest),
        "scientific_inputs": verify_case_manifest(root, case_manifest),
        "reference_acceptance_artifacts": verify_acceptance_artifacts(
            root, root / CASE, acceptance
        ),
        "field_index_contents": verify_field_index(root, root / CASE, field_index),
        "qualification_acceptance_reports": verify_qualification_acceptances(
            root, qualification
        ),
        "qualification_executable_binding": verify_qualification_executable_binding(
            reference_build, qualification
        ),
        "portable_archived_reference_executable": verify_archived_executable(
            root, reference_build
        ),
    }
    for label, result in checks.items():
        if result.get("status") != "PASS":
            failures.append({label: result.get("failures", result)})
    if reference_build_verification.get("status") != "PASS":
        failures.append("exact reference build verification status is not PASS")
    if not reference_build_verification.get("build_input_hashes_match"):
        failures.append("reference build input hashes do not match")
    if not reference_build_verification.get("executable_hash_matches"):
        failures.append("reference runtime executable hash does not match")
    if not reference_build_verification.get("archived_executable_hash_matches"):
        failures.append("portable archived executable hash does not match")
    if not reference_build_verification.get("runtime_archive_identity_matches"):
        failures.append("runtime/archive executable identity was not established")

    expected_acceptance_hash = finalization.get("qualified_acceptance", {}).get("sha256")
    observed_acceptance_hash = sha256_file(
        root / CASE / "ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json"
    )
    if expected_acceptance_hash != observed_acceptance_hash:
        failures.append("finalization/acceptance cross-link hash mismatch")
    expected_run_hash = finalization.get("finalized_run_status", {}).get("sha256")
    observed_run_hash = sha256_file(
        root / CASE / "ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json"
    )
    if expected_run_hash != observed_run_hash:
        failures.append("finalization/run-status cross-link hash mismatch")
    expected_qualification_hash = finalization.get("standard_qualification", {}).get(
        "sha256"
    )
    observed_qualification_hash = sha256_file(
        root / "qualification/ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json"
    )
    if expected_qualification_hash != observed_qualification_hash:
        failures.append("finalization/qualification cross-link hash mismatch")

    report = {
        "status": "PASS" if not failures else "FAIL",
        "reference_freeze_status": manifest.get("reference_freeze_status"),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "bound_artifact_count": len(records),
        "verification_checks": checks,
        "failure_count": len(failures),
        "failures": failures,
        "read_only": True,
    }
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
