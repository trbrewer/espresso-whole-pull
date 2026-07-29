#!/usr/bin/env python3
"""Independent fixed-boundary verifier for WP-0.3C Stage 0."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable

BASELINE = "258b4b6526acea98346031ae5cc9c9e7b3ee64a9"
EXPECTED_PATHS = frozenset({
    ".github/workflows/static-validation.yml",
    "PACKAGE_QA_STATUS.json", "SOURCE_PACKAGE_MANIFEST.json",
    "docs/DEVELOPMENT_HISTORY.md", "docs/PROJECT_STATE.md", "docs/QA_STATUS.md",
    "docs/reports/WP_0_3C_HUMAN_AND_APPARATUS_INPUT_GUIDE.md",
    "scripts/generate_source_manifest.py",
    "scripts/verify_wp03b_nonprotected_verification.py",
    "scripts/verify_wp03c_stage0_scaffold.py",
    "tests/test_wp03b_boundary.py",
    "tests/test_wp03c_stage0.py",
    "tools/campaign/wp03c/__init__.py", "tools/campaign/wp03c/stage0.py",
    "validation/contracts/WP_0_3C_STAGE0_AUTHORITY_AND_INPUT_INTAKE_CONTRACT.json",
    "validation/campaign/wp03c/WP_0_3C_INPUT_REQUIREMENTS.json",
    "validation/campaign/wp03c/templates/WP_0_3C_ROLE_ASSIGNMENT_TEMPLATE.json",
    "validation/campaign/wp03c/templates/WP_0_3C_CAMPAIGN_SCOPE_TEMPLATE.json",
    "validation/campaign/wp03c/templates/WP_0_3C_APPARATUS_INVENTORY_TEMPLATE.json",
    "validation/campaign/wp03c/templates/WP_0_3C_SENSOR_INVENTORY_TEMPLATE.json",
    "validation/campaign/wp03c/templates/WP_0_3C_MATERIAL_AND_COFFEE_TEMPLATE.json",
    "validation/campaign/wp03c/templates/WP_0_3C_PREPARATION_PROTOCOL_TEMPLATE.json",
    "validation/campaign/wp03c/templates/WP_0_3C_CALIBRATION_PLAN_TEMPLATE.json",
    "validation/campaign/wp03c/templates/WP_0_3C_COMMISSIONING_PLAN_TEMPLATE.json",
    "validation/campaign/wp03c/templates/WP_0_3C_DATA_CUSTODY_TEMPLATE.json",
    "validation/campaign/wp03c/templates/WP_0_3C_PRIVACY_AND_PUBLICATION_TEMPLATE.json",
    "validation/campaign/wp03c/templates/WP_0_3C_ACQUISITION_READINESS_TEMPLATE.json",
})
FROZEN = {
    "validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json":
        "75a79e9972176668a8bfdb574ea16cbf39373a9ea11078009bc7b997c2f76859",
    "validation/wp02/WP02_001_CLOSURE_CONTRACT.json":
        "2c898dd91e558ce62006dc81de9cff20bb633b52a89f6fa5a44c5edcda50d57a",
    "validation/contracts/WP_0_3B_A1_P1_PREEXECUTION_CORRECTION_CONTRACT.json":
        "d61d33527d6de64201018033da86e78810a3d57a477c17c46639fc90d2b92feb",
    "validation/results/WP_0_3B_A1_NONPROTECTED_EXTRACTION_VERIFICATION_RESULT.json":
        "8af2ec832b191f96994f762eca85eacdc9bfa68ef316321b6b56894d649b6349",
}
FORBIDDEN_PATTERNS = (
    r"-----BEGIN .*PRIVATE KEY-----", r"\b(password|api[_-]?key|secret)\s*[:=]\s*\S+",
    r"/home/[A-Za-z0-9_.-]+/", r"\b(model_prediction|model_residual|shot_score)\b",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changed_paths(root: Path) -> frozenset:
    output = subprocess.run(
        ["git", "diff", "--name-only", BASELINE + "...HEAD"],
        cwd=root, check=True, text=True, capture_output=True).stdout
    paths = set(output.splitlines())
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "-uall"],
        cwd=root, check=True, text=True, capture_output=True).stdout
    for line in status.splitlines():
        if len(line) <= 3:
            continue
        path = line[3:]
        if (line.startswith("?? ") and path ==
                "cases/reference_R0_20g_58mm_9bar/preflight/"
                "STATIC_VALIDATION_REPORT_V0_2_0.json"):
            continue
        paths.add(path)
    return frozenset(paths)


def evaluate(contract: Dict[str, object], registry: Dict[str, object],
             templates: Iterable[Dict[str, object]], paths: frozenset,
             frozen: Dict[str, str], text: str) -> Dict[str, bool]:
    requirements = registry.get("requirements", [])
    templates = list(templates)
    all_fields = [value for template in templates
                  for category in template.get("fields", {}).values()
                  for value in category.values()]
    return {
        "fixed_path_boundary":
            paths == EXPECTED_PATHS and
            set(contract.get("permitted_changed_paths", [])) == EXPECTED_PATHS,
        "baseline_exact":
            contract.get("baseline") == {"commit": BASELINE,
                                         "tree": "2fd9ae4a2e0040602daa29a4b5b4a7bc0ff899b9"},
        "frozen_hashes_exact": frozen == FROZEN,
        "retained_trace_identities":
            contract.get("immutable_scientific_identities", {}).get(
                "retained_9bar_trace_sha256") ==
            "10f69738a35451e4eef132edf29be80a57c667b2cb91cb64914f083302e6b1d0"
            and contract.get("immutable_scientific_identities", {}).get(
                "retained_8bar_trace_sha256") ==
            "eca75e708d4a12c3fe309ee2e1e6adb463dc974629d85eb1ab9866257ba0c7d0",
        "classifications_complete":
            all(r.get("input_classification") in registry["input_classification_vocabulary"]
                and r.get("deadline") in registry["deadline_vocabulary"]
                for r in requirements),
        "required_categories_complete":
            {r.get("category") for r in requirements} == {
                "governance_and_roles", "campaign_scope",
                "machine_and_hydraulic_apparatus", "basket_and_bed_geometry",
                "pressure_instrumentation", "mass_and_flow_instrumentation",
                "temperature_instrumentation", "time_synchronization_and_logging",
                "coffee_and_materials", "preparation_controls",
                "calibration_resources", "commissioning_resources",
                "data_custody_and_blinding"},
        "templates_nonfinal":
            len(templates) == 11 and all(
                t.get("template_status") == "NONFINAL_INPUT_TEMPLATE"
                and t.get("final_preregistration") is False
                and t.get("experimental_execution_authorized") is False
                and t.get("unresolved_value_policy") == "UNRESOLVED_HUMAN_INPUT_ONLY"
                for t in templates),
        "unresolved_values_accountable":
            bool(all_fields) and all(
                v.get("status") == "UNRESOLVED_HUMAN_INPUT"
                and v.get("responsible_role_id", "").startswith("ROLE_")
                and v.get("required_before") in registry["deadline_vocabulary"]
                for v in all_fields),
        "readiness_blocked":
            registry["readiness"]["current_state"] ==
            "STAGE0_SCAFFOLD_COMPLETE_AWAITING_HUMAN_INPUTS",
        "execution_prohibited":
            contract.get("execution_counts") == {
                "experimental": 0, "holdout_scoring": 0, "openfoam": 0,
                "protected_access": 0, "puckworks_code": 0},
        "claims_bounded":
            contract.get("physical_validation") == "NOT_ESTABLISHED"
            and contract.get("final_preregistration") == "NOT_CREATED"
            and contract.get("commissioning") == "NOT_AUTHORIZED"
            and contract.get("holdout_acquisition") == "NOT_AUTHORIZED",
        "no_forbidden_content":
            not any(re.search(pattern, text, re.IGNORECASE)
                    for pattern in FORBIDDEN_PATTERNS),
    }


def verify(root: Path) -> Dict[str, object]:
    contract = json.loads((root / "validation/contracts/WP_0_3C_STAGE0_AUTHORITY_AND_INPUT_INTAKE_CONTRACT.json").read_text())
    registry = json.loads((root / "validation/campaign/wp03c/WP_0_3C_INPUT_REQUIREMENTS.json").read_text())
    templates = [json.loads(path.read_text()) for path in sorted(
        (root / "validation/campaign/wp03c/templates").glob("*.json"))]
    paths = changed_paths(root)
    frozen = {path: sha(root / path) for path in FROZEN}
    text = "\n".join(
        (root / path).read_text(errors="replace")
        for path in paths
        if (root / path).is_file() and Path(path).suffix in {".json", ".md"}
    )
    checks = evaluate(contract, registry, templates, paths, frozen, text)
    return {
        "schema_version": "espresso.public.wp_0_3c_stage0_boundary.v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "readiness": registry["readiness"]["current_state"],
        "checks": checks,
        "changed_paths": sorted(paths),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.root.resolve())
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
