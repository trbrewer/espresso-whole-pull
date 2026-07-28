#!/usr/bin/env python3
"""Generate and self-verify the terminal v0.1.4 immutable freeze manifest.

All mutable controlling records are finalized before this script runs.  This
manifest is deliberately written last and is never referenced by an artifact it
hashes, keeping the provenance graph acyclic.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from artifact_utils import (  # noqa: E402
    aggregate_records,
    artifact_record,
    atomic_write_json,
    load_json_object,
    sha256_file,
    verify_artifact_records,
)
from freeze_contract import (  # noqa: E402
    required_status_failures,
    verify_acceptance_artifacts,
    verify_archived_executable,
    verify_case_manifest,
    verify_current_qualification_executable,
    verify_field_index,
    verify_qualification_acceptances,
    verify_qualification_executable_binding,
    verify_source_manifest,
)

PACKAGE_VERSION = "0.1.4"
CASE = Path("cases/reference_R0_20g_58mm_9bar")
FIXTURE = Path("cases/fixture_layered_pressure_v0_1_4")
QUALIFICATION = Path("qualification")
OUTPUT = CASE / "ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json"

PATHS = {
    "source_manifest": Path("SOURCE_PACKAGE_MANIFEST.json"),
    "build_provenance": CASE / "preflight/BUILD_PROVENANCE_V0_1_4.json",
    "build_verification": CASE / "preflight/BUILD_PROVENANCE_VERIFICATION_V0_1_4.json",
    "archived_executable": CASE / "preflight/espressoWholePullFoam_v0_1_4",
    "timestamp_normalization": CASE / "preflight/TIMESTAMP_NORMALIZATION_V0_1_4.json",
    "no_physics_reference": CASE / "preflight/NO_PHYSICS_CHANGE_VERIFICATION_V0_1_4.json",
    "no_physics_qualification": QUALIFICATION / "NO_PHYSICS_CHANGE_VERIFICATION_STANDARD_V0_1_4.json",
    "executed_scenario": CASE / "CASE_SCENARIO_V0_1_4.json",
    "run_environment": CASE / "RUN_ENVIRONMENT_V0_1_4.json",
    "case_manifest": CASE / "ESPRESSO_WHOLE_PULL_REFERENCE_CASE_MANIFEST_V0_1_4.json",
    "stage_timings": CASE / "ESPRESSO_WHOLE_PULL_STAGE_TIMINGS_V0_1_4.json",
    "run_status": CASE / "ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json",
    "acceptance": CASE / "ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json",
    "trace": CASE / "ESPRESSO_WHOLE_PULL_REFERENCE_TRACES_V0_1_4.csv",
    "field_index": CASE / "ESPRESSO_WHOLE_PULL_REFERENCE_FIELD_INDEX_V0_1_4.json",
    "paraview": CASE / "reference_R0.foam",
    "fixture_acceptance": FIXTURE / "ESPRESSO_LAYERED_PRESSURE_FIXTURE_ACCEPTANCE_V0_1_4.json",
    "qualification_report": QUALIFICATION / "ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json",
    "qualification_csv": QUALIFICATION / "ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_RUNS_V0_1_4.csv",
    "finalization_status": QUALIFICATION / "ESPRESSO_WHOLE_PULL_FREEZE_FINALIZATION_STATUS_V0_1_4.json",
}

ROLES = {
    "source_manifest": "source_package_manifest",
    "build_provenance": "reference_solver_build_provenance",
    "build_verification": "exact_reference_build_reuse_verification",
    "archived_executable": "portable_archived_reference_executable",
    "timestamp_normalization": "archive_timestamp_normalization",
    "no_physics_reference": "reference_no_physics_change_verification",
    "no_physics_qualification": "post_qualification_no_physics_change_verification",
    "executed_scenario": "executed_reference_scenario",
    "run_environment": "reference_run_environment",
    "case_manifest": "immutable_scientific_input_manifest",
    "stage_timings": "reference_stage_timings",
    "run_status": "finalized_reference_run_status",
    "acceptance": "qualified_reference_acceptance",
    "trace": "reference_reduced_trace",
    "field_index": "reference_field_index",
    "paraview": "paraview_entry_point",
    "fixture_acceptance": "layered_pressure_fixture_acceptance",
    "qualification_report": "standard_numerical_qualification",
    "qualification_csv": "qualification_reduced_matrix",
    "finalization_status": "freeze_finalization_status",
}


def require_paths(root: Path) -> Dict[str, Path]:
    resolved = {name: root / relative for name, relative in PATHS.items()}
    missing = [str(path) for path in resolved.values() if not path.is_file()]
    if missing:
        raise SystemExit("Terminal freeze manifest missing required artifacts:\n- " + "\n- ".join(missing))
    return resolved


def check_finalization_bindings(
    finalization: Dict[str, Any], paths: Dict[str, Path], root: Path
) -> Tuple[bool, List[Dict[str, Any]]]:
    failures: List[Dict[str, Any]] = []
    expected = {
        "qualified_acceptance": paths["acceptance"],
        "finalized_run_status": paths["run_status"],
        "standard_qualification": paths["qualification_report"],
    }
    for key, path in expected.items():
        recorded = finalization.get(key, {})
        observed = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        if recorded.get("bytes") != observed["bytes"] or recorded.get("sha256") != observed["sha256"]:
            failures.append(
                {
                    "binding": key,
                    "issue": "finalization_record_mismatch",
                    "recorded": {
                        "bytes": recorded.get("bytes"),
                        "sha256": recorded.get("sha256"),
                    },
                    "observed": observed,
                }
            )
    return not failures, failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    paths = require_paths(root)

    source_manifest = load_json_object(paths["source_manifest"])
    build = load_json_object(paths["build_provenance"])
    build_verification = load_json_object(paths["build_verification"])
    no_physics_reference = load_json_object(paths["no_physics_reference"])
    no_physics_qualification = load_json_object(paths["no_physics_qualification"])
    case_manifest = load_json_object(paths["case_manifest"])
    acceptance = load_json_object(paths["acceptance"])
    qualification = load_json_object(paths["qualification_report"])
    run_status = load_json_object(paths["run_status"])
    field_index = load_json_object(paths["field_index"])
    finalization = load_json_object(paths["finalization_status"])

    status_failures = required_status_failures(
        acceptance,
        qualification,
        run_status,
        finalization,
        no_physics_reference,
        no_physics_qualification,
    )
    if build_verification.get("status") != "PASS":
        status_failures.append("exact reference build verification is not PASS")
    if not build_verification.get("executable_hash_matches"):
        status_failures.append("reference runtime executable hash does not match build provenance")
    if not build_verification.get("archived_executable_hash_matches"):
        status_failures.append("portable archived executable hash does not match build provenance")
    if not build_verification.get("runtime_archive_identity_matches"):
        status_failures.append("runtime and archived executable bytes are not identical")
    if not build_verification.get("build_input_hashes_match"):
        status_failures.append("reference build inputs do not match build provenance")
    if status_failures:
        raise SystemExit("Terminal freeze status prerequisites failed:\n- " + "\n- ".join(status_failures))

    verification = {
        "source_package": verify_source_manifest(root, source_manifest),
        "scientific_inputs": verify_case_manifest(root, case_manifest),
        "reference_acceptance_artifacts": verify_acceptance_artifacts(root, root / CASE, acceptance),
        "reconstructed_field_contents": verify_field_index(root, root / CASE, field_index),
        "qualification_acceptances": verify_qualification_acceptances(root, qualification),
        "qualification_executable_binding": verify_qualification_executable_binding(
            build, qualification
        ),
        "current_reference_executable": verify_current_qualification_executable(build),
        "portable_archived_executable": verify_archived_executable(root, build),
    }
    binding_ok, binding_failures = check_finalization_bindings(finalization, paths, root)
    verification["finalization_bindings"] = {
        "status": "PASS" if binding_ok else "FAIL",
        "checked_binding_count": 3,
        "failures": binding_failures,
    }
    failed_verifications = [
        name for name, report in verification.items() if report.get("status") != "PASS"
    ]
    if failed_verifications:
        details = {
            name: verification[name] for name in failed_verifications
        }
        raise SystemExit(
            "Terminal freeze content verification failed: "
            + json.dumps(details, sort_keys=True)
        )

    artifacts = [
        artifact_record(paths[name], root, ROLES[name]) for name in PATHS
    ]
    artifact_aggregate = aggregate_records(artifacts)
    finalized_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "schema_version": "espresso.whole_pull.reference_freeze_manifest.v0.1.4",
        "package_version": PACKAGE_VERSION,
        "freeze_finalized_at_utc": finalized_at,
        "status": "PASS",
        "implementation_status": "PASS",
        "code_verification_status": "PASS",
        "numerical_qualification_status": "PASS",
        "release_provenance_status": "PASS",
        "reference_qualification_status": "PASS",
        "reference_freeze_status": "FROZEN / QUALIFIED",
        "wp_milestone": "WP-0.1H_COMPLETE",
        "release_role": "WP-0.1F_NO_PHYSICS_CHANGE_FREEZE_FINALIZATION",
        "physical_validation_status": "NOT_ESTABLISHED",
        "next_scientific_milestone": "WP-0.1R",
        "governing_physics_change_from_qualified_v0_1_3": False,
        "source_package": {
            "manifest_path": str(PATHS["source_manifest"]),
            "manifest_sha256": sha256_file(paths["source_manifest"]),
            "aggregate_source_sha256": source_manifest.get("aggregate_source_sha256"),
            "file_count": source_manifest.get("file_count"),
        },
        "solver_build": {
            "provenance_path": str(PATHS["build_provenance"]),
            "verification_path": str(PATHS["build_verification"]),
            "source_and_executable_bundle_sha256": build.get(
                "source_and_executable_bundle_sha256"
            ),
            "runtime_executable": build.get("runtime_executable", build.get("executable")),
            "archived_executable": build.get("archived_executable"),
            "runtime_archive_identity": build.get("runtime_archive_identity"),
            "exact_build_reused_for_standard_qualification": True,
            "qualification_executable_binding": verification.get(
                "qualification_executable_binding"
            ),
            "portable_executable_bound_by_terminal_manifest": True,
        },
        "scientific_input_bundle": {
            "manifest_path": str(PATHS["case_manifest"]),
            "scientific_bundle_sha256": case_manifest.get("scientific_bundle_sha256"),
            "prepared_at_utc": case_manifest.get("prepared_at_utc"),
            "manifest_role": case_manifest.get("manifest_role"),
        },
        "reference_result": {
            "acceptance_status": acceptance.get("status"),
            "reference_qualification_status": acceptance.get(
                "reference_qualification_status"
            ),
            "reference_freeze_status_before_terminal_manifest": acceptance.get(
                "reference_freeze_status"
            ),
            "outputs_finalized_at_utc": acceptance.get("outputs_finalized_at_utc"),
            "qualification_finalized_at_utc": acceptance.get(
                "qualification_finalized_at_utc"
            ),
            "primary_outputs": acceptance.get("primary_outputs"),
        },
        "qualification": {
            "status": qualification.get("status"),
            "profile": qualification.get("profile"),
            "gate_summary": qualification.get("gate_summary"),
            "matrix_run_count": len(qualification.get("runs", {})),
            "qualification_completed_at_utc": qualification.get(
                "qualification_completed_at_utc",
                qualification.get("generated_at_utc"),
            ),
            "performance_observations": qualification.get(
                "performance_observations"
            ),
        },
        "field_archive_identity": {
            "field_index_path": str(PATHS["field_index"]),
            "indexed_file_count": field_index.get("indexed_file_count"),
            "final_time_directory": field_index.get("final_time_directory"),
            "missing_final_fields": field_index.get("missing_final_fields"),
            "field_content_aggregate_sha256": verification[
                "reconstructed_field_contents"
            ].get("field_content_aggregate_sha256"),
        },
        "verification": verification,
        "controlling_artifacts": artifacts,
        "controlling_artifact_aggregate_sha256": artifact_aggregate,
        "artifacts": artifacts,
        "artifact_set_aggregate_sha256": artifact_aggregate,
        "artifact_verification": {
            "status": "PASS",
            "checked_top_level_artifact_count": len(artifacts),
            "checked_field_file_count": verification[
                "reconstructed_field_contents"
            ].get("checked_field_file_count"),
            "checked_qualification_acceptance_count": verification[
                "qualification_acceptances"
            ].get("checked_acceptance_count"),
            "failures": [],
        },
        "acyclic_provenance": {
            "status": "PASS",
            "order": [
                "source package and scientific inputs",
                "exact solver build",
                "reference/fixture outputs and reconstructed fields",
                "standard qualification matrix",
                "qualified acceptance and finalized run status",
                "terminal freeze manifest (this file)",
            ],
            "terminal_manifest_self_hash_embedded": False,
            "note": (
                "No artifact hashed by this manifest records or depends on this "
                "manifest hash. This file is the terminal controlling record."
            ),
        },
        "calibration_and_claim_ceiling": acceptance.get(
            "calibration_and_validation"
        ),
        "claim": (
            "This is an immutably bound, numerically qualified WP-0.1 R0 "
            "calibration baseline. It is not independent physical validation of "
            "a real coffee, grinder, puck, or machine."
        ),
    }
    atomic_write_json(output, manifest)

    # Re-open the manifest and verify all top-level bound artifacts after the
    # terminal file exists. No other file is written after this check.
    frozen = load_json_object(output)
    ok, failures = verify_artifact_records(frozen["artifacts"], root)
    if not ok:
        output.unlink(missing_ok=True)
        raise SystemExit(
            "Post-write terminal freeze verification failed: "
            + json.dumps(failures, sort_keys=True)
        )

    print(
        json.dumps(
            {
                "status": "PASS",
                "reference_freeze_status": "FROZEN / QUALIFIED",
                "freeze_manifest": str(output),
                "freeze_manifest_sha256": sha256_file(output),
                "bound_top_level_artifact_count": len(artifacts),
                "verified_field_file_count": verification[
                    "reconstructed_field_contents"
                ].get("checked_field_file_count"),
                "verified_qualification_acceptance_count": verification[
                    "qualification_acceptances"
                ].get("checked_acceptance_count"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
