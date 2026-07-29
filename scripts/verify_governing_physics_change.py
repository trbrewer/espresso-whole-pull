#!/usr/bin/env python3
"""Verify the bounded WP02 governing-physics change and frozen controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

EXPECTED = {
    "r0": "67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286",
    "constant_r1": "be275c0302f30dc4dcab120469b0bc62d444e401a80e082a337d9225c659b876",
    "closure": "2c898dd91e558ce62006dc81de9cff20bb633b52a89f6fa5a44c5edcda50d57a",
    "nine": "81a9089061d762aaf785a7764cebb8e0947e4f3c14bb833d58a204d2c816407e",
    "eight": "ac87cfdff2862401b33ac01fa31d87bf966e062cecd153ce59ab4a9518feb57e",
    "result": "75a79e9972176668a8bfdb574ea16cbf39373a9ea11078009bc7b997c2f76859",
    "run_status": "fec4d8157566916898914315ac6714e45df9d19bfe0fde93057cd31db2ea3d25",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path, declaration_path: Path | None = None) -> dict:
    declaration_path = declaration_path or (
        root / "validation/wp02/WP02_001_POST_RESULT_GOVERNANCE_AMENDMENT.json"
    )
    declaration = json.loads(declaration_path.read_text())
    manifest = json.loads((root / "SOURCE_PACKAGE_MANIFEST.json").read_text())
    contract = json.loads(
        (root / "validation/wp02/WP02_001_CLOSURE_CONTRACT.json").read_text()
    )
    result = json.loads(
        (root / "validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json").read_text()
    )
    run = json.loads(
        (root / "validation/wp02/WP02_001_RUN_STATUS.json").read_text()
    )
    endpoint = json.loads(
        (root / "validation/wp02/WP02_001_ANALYZER_ENDPOINT_AMENDMENT.json").read_text()
    )
    r0 = json.loads((root / "config/reference_R0.json").read_text())
    r1 = json.loads((root / "config/reconstruction_R1_waszkiewicz_9bar.json").read_text())
    solver = (root / "solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text()

    identities = {
        "r0": digest(root / "config/reference_R0.json"),
        "constant_r1": digest(root / "config/reconstruction_R1_waszkiewicz_9bar.json"),
        "closure": digest(root / "validation/wp02/WP02_001_CLOSURE_CONTRACT.json"),
        "nine": digest(root / "config/reconstruction_WP02A_waszkiewicz_9bar.json"),
        "eight": digest(root / "config/reconstruction_WP02A_waszkiewicz_8bar.json"),
        "result": digest(root / "validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json"),
        "run_status": digest(root / "validation/wp02/WP02_001_RUN_STATUS.json"),
    }
    checks = {
        "tracked_declaration": declaration.get("change_declaration")
        == "GOVERNING_PHYSICS_CHANGE",
        "active_version": (root / "VERSION").read_text().strip()
        in ("0.2.0-dev.1", "0.2.0"),
        "not_v0_1_4_active": (root / "VERSION").read_text().strip() != "0.1.4",
        "solver_display_version": any(
            token in solver
            for token in (
                "espressoWholePullFoam v0.2.0-dev.1",
                "espressoWholePullFoam v0.2.0",
            )
        ),
        "solver_banner_only_change": hashlib.sha256(
            re.sub(
                r"v0\.(?:1\.4|2\.0(?:-dev\.1)?)",
                "v<DISPLAY_VERSION>",
                solver,
            ).encode()
        ).hexdigest()
        == declaration["frozen_identities"]["normalized_solver_source_sha256"],
        "manifest_governing_change": manifest.get("governing_physics_change") is True,
        "manifest_scope": manifest.get("scientific_configuration_change_scope")
        == "R1_SCENARIO_AND_WP02_OPTIONAL_SATURATED_EFFECTIVE_PERMEABILITY_CLOSURE",
        "frozen_identities": identities == EXPECTED,
        "r0_aggregate": declaration["frozen_identities"][
            "r0_scientific_input_aggregate_sha256"
        ]
        == "d70399a76b0023d93985d76c1c83a9a42b7148b3d71d16d1b5f88275be1ebe7a",
        "constant_r1_aggregate": declaration["frozen_identities"][
            "constant_r1_generated_input_aggregate_sha256"
        ]
        == "ddc6ac9e5cfd4746d5e7548e1b78cbb4942092d134806a6e9526ef26657aa957",
        "closure_optional": contract["implementation_boundary"]["disabled_by_default"]
        is True,
        "r0_closure_inactive": not r0.get("effective_permeability_evolution", {}).get(
            "enabled", False
        ),
        "r1_closure_inactive": not r1.get("effective_permeability_evolution", {}).get(
            "enabled", False
        ),
        "run_binds_result": run.get("analysis_result_sha256") == EXPECTED["result"],
        "trace_hashes_bound": all(
            result["scenarios"][name]["trace_sha256"]
            == endpoint["retained_traces"][name]["sha256"]
            for name in ("nine_bar_reconstruction", "eight_bar_transfer")
        ),
        "invocation_counts": result["analysis_identity"][
            "failed_pre_score_analyzer_invocations"
        ]
        == 1
        and result["analysis_identity"][
            "completed_score_bearing_analysis_invocations"
        ]
        == 1,
        "execution_counts": run["execution_counts"]["nine_bar_openfoam_executions"]
        == 1
        and run["execution_counts"]["eight_bar_openfoam_executions"] == 1
        and run["execution_counts"]["solver_reruns_for_endpoint_correction"] == 0,
        "zero_adjustments": all(value == 0 for value in run["adjustment_counts"].values()),
        "nine_bar_pass": result["scenarios"]["nine_bar_reconstruction"]["aggregate"][
            "status"
        ]
        == "PASS",
        "eight_bar_pass": result["scenarios"]["eight_bar_transfer"]["aggregate"][
            "status"
        ]
        == "PASS",
        "overall_disposition": run["overall_wp02_001_disposition"]
        == "SOURCE_LINKED_MULTIPRESSURE_RECONSTRUCTION_PASS",
        "physical_validation": run["physical_validation"] == "NOT_ESTABLISHED",
        "eight_bar_not_independent": run["claim_ceiling"][
            "eight_bar_independent_validation"
        ]
        is False,
        "claim_ceiling_present": "NOT_ESTABLISHED"
        in (root / "docs/CLAIM_CEILING.md").read_text(),
        "result_unchanged_by_amendment": declaration["scientific_result_changed"]
        is False,
        "no_protected_access_in_governance": declaration["protected_source_accessed"]
        is False,
    }
    passed = all(checks.values())
    return {
        "schema_version": "espresso.whole_pull.governing_physics_change_verification.v1",
        "status": "PASS" if passed else "FAIL",
        "change_declaration": "GOVERNING_PHYSICS_CHANGE",
        "checks": {
            key: {"status": "PASS" if value else "FAIL"} for key, value in checks.items()
        },
        "identities": identities,
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
