#!/usr/bin/env python3
"""Verify the independently bounded WP-0.3A evidence-review change."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

BASELINE = "89b9ab16dc9c1871815873522733c9101b713bfc"
IMPACT_PATH = Path(
    "validation/integration/WP_0_3A_PUCKWORKS_SOLVER_SUPPORT_IMPACT_MATRIX.json"
)
ALIGNMENT_PATH = Path("validation/evidence/WP_0_3A_PUCKWORKS_ALIGNMENT_REVIEW.json")
CONTRACT_PATH = Path(
    "validation/contracts/WP_0_3A_INDEPENDENT_HOLDOUT_AND_MECHANISM_DISCRIMINATION_CONTRACT.json"
)
EXPECTED_CHANGED_PATHS = frozenset(
    {
        ".github/workflows/static-validation.yml",
        "PACKAGE_QA_STATUS.json",
        "README.md",
        "SOURCE_PACKAGE_MANIFEST.json",
        "docs/DEVELOPMENT_HISTORY.md",
        "docs/PROJECT_STATE.md",
        "docs/PUCKWORKS_INTEGRATION.md",
        "docs/evidence/WP_0_3A_ALIGNMENT_AND_HOLDOUT_REVIEW.md",
        "docs/integration/PUCKWORKS_WP_0_3A_SOLVER_SUPPORT_TRIAGE.md",
        "docs/validation/WP_0_3A_FUTURE_HOLDOUT_EXECUTION_BRIEF.md",
        "scripts/generate_source_manifest.py",
        "scripts/verify_release_finalization.py",
        "scripts/verify_wp03_evidence_review.py",
        "tests/test_wp03_holdout_contract.py",
        "validation/contracts/WP_0_3A_INDEPENDENT_HOLDOUT_AND_MECHANISM_DISCRIMINATION_CONTRACT.json",
        "validation/contracts/WP_0_3A_NONPROTECTED_VERIFICATION_PACKAGE_SPEC.json",
        "validation/contracts/WP_0_3A_VACA_GUERRA_OFFLINE_INITIALIZER_SPEC.json",
        "validation/evidence/WP_0_3A_HOLDOUT_CANDIDATE_MATRIX.json",
        "validation/evidence/WP_0_3A_MECHANISM_DISCRIMINATION_MATRIX.json",
        "validation/evidence/WP_0_3A_PUCKWORKS_ALIGNMENT_REVIEW.json",
        "validation/evidence/WP_0_3A_REVIEW_DISPOSITION.json",
        "validation/integration/WP_0_3A_PUCKWORKS_IDENTITY_AND_RIGHTS.json",
        "validation/integration/WP_0_3A_PUCKWORKS_SOLVER_SUPPORT_IMPACT_MATRIX.json",
    }
)
FROZEN_HASHES = {
    "validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json":
        "75a79e9972176668a8bfdb574ea16cbf39373a9ea11078009bc7b997c2f76859",
    "validation/wp02/WP02_001_CLOSURE_CONTRACT.json":
        "2c898dd91e558ce62006dc81de9cff20bb633b52a89f6fa5a44c5edcda50d57a",
    "config/reference_R0.json":
        "67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286",
    "config/reconstruction_R1_waszkiewicz_9bar.json":
        "be275c0302f30dc4dcab120469b0bc62d444e401a80e082a337d9225c659b876",
    "config/reconstruction_WP02A_waszkiewicz_9bar.json":
        "81a9089061d762aaf785a7764cebb8e0947e4f3c14bb833d58a204d2c816407e",
    "config/reconstruction_WP02A_waszkiewicz_8bar.json":
        "ac87cfdff2862401b33ac01fa31d87bf966e062cecd153ce59ab4a9518feb57e",
}
EXPECTED_CLASSIFICATION = [
    "EXTERNAL_DEPENDENCY_REVIEW",
    "EVIDENCE_AND_VERIFICATION_SUPPORT_ONLY",
    "NO_GOVERNING_PHYSICS_CHANGE",
    "NO_PROTECTED_ANALYSIS",
    "NO_SCIENTIFIC_RESULT_CHANGE",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_changed_paths(root: Path) -> set[str] | None:
    completed = subprocess.run(
        ["git", "diff", "--name-only", BASELINE],
        cwd=root, capture_output=True, text=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=root, capture_output=True, text=True,
    )
    if completed.returncode or untracked.returncode:
        return None
    paths = set(completed.stdout.splitlines()) | set(untracked.stdout.splitlines())
    paths.discard(
        "cases/reference_R0_20g_58mm_9bar/preflight/"
        "STATIC_VALIDATION_REPORT_V0_2_0.json"
    )
    return paths


def evaluate(
    impact: dict,
    alignment: dict,
    contract: dict,
    lock: dict,
    changed_paths: set[str] | None,
    frozen_hashes: dict[str, str],
) -> dict[str, bool]:
    changed_cards = alignment["delta_inventory"]["all_changed_model_card_paths"]
    represented = [
        item["path"] for item in impact["artifacts"]
        if item["path"] in changed_cards
    ]
    return {
        "classification": impact["classification"] == EXPECTED_CLASSIFICATION,
        "exact_upstream_identity":
            impact["upstream"]["old_commit"] == "fc61c4670ec7bf801e40bb391aab16048b8da26b"
            and impact["upstream"]["old_tree"] == "1d553e44ee2f7480a5df521560801b478618cc84"
            and impact["upstream"]["review_target_commit"] == "bafafef3bc3c77599af8551d4e582aedb9b23f08"
            and impact["upstream"]["review_target_tree"] == "64ccf86aff4c90d1c513f1614b39e0823f64d6d7",
        "runtime_lock_retained":
            lock["checkout_commit"] == "fc61c4670ec7bf801e40bb391aab16048b8da26b"
            and lock["checkout_tree_sha"] == "1d553e44ee2f7480a5df521560801b478618cc84"
            and impact["runtime_dependency_lock_disposition"] == "RETAIN_EXISTING_LOCK",
        "evidence_disposition":
            impact["solver_support_evidence_disposition"]
            == "ADOPT_SELECTED_EVIDENCE_WITH_FOLLOWUP",
        "no_execution_or_protected_access":
            impact["upstream"]["new_code_executed"] is False
            and impact["upstream"]["protected_source_accessed"] is False,
        "no_scientific_result_change":
            impact["claim_state"]["scientific_result_changed"] is False,
        "frozen_scientific_hashes": frozen_hashes == FROZEN_HASHES,
        "record_path_set_exact":
            set(impact["allowed_repository_changed_paths"]) == EXPECTED_CHANGED_PATHS,
        "repository_path_set_exact":
            changed_paths is not None and changed_paths == EXPECTED_CHANGED_PATHS,
        "changed_card_coverage_exact":
            len(represented) == len(set(represented))
            and set(represented) == set(changed_cards),
        "holdout_not_authorized":
            contract["authorization_boundary"]["holdout_execution_authorized"] is False,
        "physical_validation_not_established":
            impact["claim_state"]["physical_validation"] == "NOT_ESTABLISHED"
            and contract["claim_state"]["physical_validation"] == "NOT_ESTABLISHED",
    }


def verify(root: Path, changed_paths: set[str] | None = None) -> dict:
    impact = json.loads((root / IMPACT_PATH).read_text())
    alignment = json.loads((root / ALIGNMENT_PATH).read_text())
    contract = json.loads((root / CONTRACT_PATH).read_text())
    lock = json.loads((root / "dependencies/puckworks.lock.json").read_text())
    observed = {path: digest(root / path) for path in FROZEN_HASHES}
    paths = git_changed_paths(root) if changed_paths is None else changed_paths
    checks = evaluate(impact, alignment, contract, lock, paths, observed)
    return {
        "schema_version": "espresso.public.wp_0_3a_evidence_review_verification.v1",
        "task": "WP-0.3A",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": {key: "PASS" if value else "FAIL" for key, value in checks.items()},
        "changed_paths": sorted(paths) if paths is not None else None,
        "frozen_hashes": observed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify(args.root.resolve())
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
