#!/usr/bin/env python3
"""Verify WP-0.2F changes only release engineering after merged WP02 science."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

DEFAULT_CONTRACT = Path(
    "validation/wp02/WP_0_2F_RELEASE_FINALIZATION_CONTRACT.json"
)
POST_RELEASE_RECORD = Path(
    "validation/release/WP_0_2G_POST_RELEASE_STATE_RECONCILIATION.json"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_solver_hash(path: Path) -> str:
    text = path.read_text()
    normalized = re.sub(
        r"v0\.(?:1\.4|2\.0(?:-dev\.1)?)", "v<DISPLAY_VERSION>", text
    )
    return hashlib.sha256(normalized.encode()).hexdigest()


def changed_paths(root: Path, baseline: str, endpoint: str) -> list[str] | None:
    completed = subprocess.run(
        ["git", "diff", "--name-only", f"{baseline}...{endpoint}"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return [line for line in completed.stdout.splitlines() if line]


def verify(root: Path, declaration_path: Path | None = None) -> dict:
    declaration_path = declaration_path or root / DEFAULT_CONTRACT
    contract = json.loads(declaration_path.read_text())
    immutable = contract["immutable_scientific_identities"]
    result = json.loads(
        (root / "validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json").read_text()
    )
    run = json.loads(
        (root / "validation/wp02/WP02_001_RUN_STATUS.json").read_text()
    )
    endpoint = json.loads(
        (root / "validation/wp02/WP02_001_ANALYZER_ENDPOINT_AMENDMENT.json").read_text()
    )
    manifest = json.loads((root / "SOURCE_PACKAGE_MANIFEST.json").read_text())
    observed = {
        "scientific_result_sha256": digest(
            root / "validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json"
        ),
        "closure_contract_sha256": digest(
            root / "validation/wp02/WP02_001_CLOSURE_CONTRACT.json"
        ),
        "r0_configuration_sha256": digest(root / "config/reference_R0.json"),
        "constant_r1_configuration_sha256": digest(
            root / "config/reconstruction_R1_waszkiewicz_9bar.json"
        ),
        "wp02_nine_bar_configuration_sha256": digest(
            root / "config/reconstruction_WP02A_waszkiewicz_9bar.json"
        ),
        "wp02_eight_bar_configuration_sha256": digest(
            root / "config/reconstruction_WP02A_waszkiewicz_8bar.json"
        ),
        "normalized_solver_source_sha256": normalized_solver_hash(
            root / "solver/espressoWholePullFoam/espressoWholePullFoam.C"
        ),
    }
    expected = {key: immutable[key] for key in observed}
    # This verifier preserves the completed release boundary. Later governed
    # tasks have their own independent path verifiers and cannot extend it.
    paths = changed_paths(
        root,
        contract["baseline"]["merge_commit"],
        "6e6b35b0fc6747f805223ce7975a0865835f01f0",
    )
    allowed = set(contract["allowed_changed_paths"])
    prefixes = tuple(contract["allowed_changed_path_prefixes"])
    post_release_record = None
    post_release_path = root / POST_RELEASE_RECORD
    if post_release_path.is_file():
        post_release_record = json.loads(post_release_path.read_text())
        allowed.update(post_release_record["allowed_post_release_changed_paths"])
    path_boundary = paths is None or all(
        path in allowed or path.startswith(prefixes) for path in paths
    )
    trace_binding = (
        result["scenarios"]["nine_bar_reconstruction"]["trace_sha256"]
        == immutable["nine_bar_trace_sha256"]
        == endpoint["retained_traces"]["nine_bar_reconstruction"]["sha256"]
        and result["scenarios"]["eight_bar_transfer"]["trace_sha256"]
        == immutable["eight_bar_trace_sha256"]
        == endpoint["retained_traces"]["eight_bar_transfer"]["sha256"]
    )
    checks = {
        "classification": contract["task_classification"]
        == [
            "NO_GOVERNING_PHYSICS_CHANGE",
            "RELEASE_ENGINEERING_AND_DOCUMENTATION_ONLY",
        ],
        "release_version": (root / "VERSION").read_text().strip() == "0.2.0",
        "manifest_release_version": manifest["package_version"] == "0.2.0",
        "immutable_identities": observed == expected,
        "trace_identities": trace_binding,
        "result_disposition": run["overall_wp02_001_disposition"]
        == "SOURCE_LINKED_MULTIPRESSURE_RECONSTRUCTION_PASS",
        "physical_validation": run["physical_validation"] == "NOT_ESTABLISHED",
        "eight_bar_not_independent": run["claim_ceiling"][
            "eight_bar_independent_validation"
        ]
        is False,
        "no_new_scientific_execution": run["execution_counts"][
            "solver_reruns_for_endpoint_correction"
        ]
        == 0,
        "zero_adjustments": all(value == 0 for value in run["adjustment_counts"].values()),
        "release_permissions_closed": contract["protected_source_access_allowed"]
        is False
        and contract["governed_scientific_solver_reruns_allowed"] is False
        and contract["scientific_score_recalculation_allowed"] is False
        and contract["governing_physics_change_allowed"] is False,
        "post_release_state_reconciled": post_release_record is None
        or (
            post_release_record["classification"]
            == [
                "POST_RELEASE_DOCUMENTATION_AND_PROVENANCE_ONLY",
                "NO_GOVERNING_PHYSICS_CHANGE",
                "NO_SCIENTIFIC_RESULT_CHANGE",
            ]
            and post_release_record["release"]["tag"] == "v0.2.0"
            and post_release_record["release"]["tag_target"]
            == "6e6b35b0fc6747f805223ce7975a0865835f01f0"
            and post_release_record["immutable_identities"][
                "scientific_result_sha256"
            ]
            == immutable["scientific_result_sha256"]
            and post_release_record[
                "tagged_tree_contains_prepublication_status_snapshot"
            ]
            is True
            and post_release_record[
                "final_publication_state_is_bound_by_release_asset_manifest"
            ]
            is True
            and post_release_record["tag_changed"] is False
            and post_release_record["release_assets_changed"] is False
            and post_release_record["scientific_records_changed"] is False
            and post_release_record["protected_accesses_added"] == 0
            and post_release_record["analyzer_invocations_added"] == 0
            and post_release_record["governed_solver_executions_added"] == 0
            and post_release_record["score_recalculations_added"] == 0
            and post_release_record["fitting_or_retuning"] is False
            and post_release_record["physical_validation"] == "NOT_ESTABLISHED"
        ),
        "changed_path_boundary": path_boundary,
    }
    passed = all(checks.values())
    return {
        "schema_version": "espresso.whole_pull.release_finalization_verification.v0.2.0",
        "status": "PASS" if passed else "FAIL",
        "task": "WP-0.2F",
        "checks": {
            key: {"status": "PASS" if value else "FAIL"} for key, value in checks.items()
        },
        "observed_identities": observed,
        "changed_paths": paths,
        "git_boundary_check": "PASS" if paths is not None and path_boundary else (
            "NOT_AVAILABLE_IN_ARCHIVE" if paths is None else "FAIL"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--declaration", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify(args.root.resolve(), args.declaration)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
