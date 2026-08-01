#!/usr/bin/env python3
"""Independent fixed-boundary verifier for WP-0.3C Stage 0."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable

ROOT_MODULE = Path(__file__).resolve().parents[1] / "tools/campaign/wp03c"
sys.path.insert(0, str(ROOT_MODULE))
import stage0  # noqa: E402

BASELINE = "258b4b6526acea98346031ae5cc9c9e7b3ee64a9"
STAGE0_FREEZE_COMMIT = "f43bf2166f60f984e4ca5ca7f30c791a68c6259e"
STAGE0_FREEZE_TREE = "6b812f61bb4e0630d80dc0fb4a0922d63554a704"
STAGE0_CONTRACT_PATH = \
    "validation/contracts/WP_0_3C_STAGE0_AUTHORITY_AND_INPUT_INTAKE_CONTRACT.json"
STAGE0_CONTRACT_SHA256 = \
    "88aee87865e5ea1cd9542432bad36809773cc62c8b24a3be30e043296ef3c613"
STAGE0_PROTECTED_PATH_COUNT = 16
STAGE0_PROTECTED_PATH_AGGREGATE = \
    "8f21a12285d93cc5ee24730c892d6da6db7cdad9948b2c76dd60bc0c1e5dce7c"
# Later work-package paths are intentionally absent. The protected scope is
# derived from the pinned historical Stage-0 contract below.
FROZEN = {
    "validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json":
        "75a79e9972176668a8bfdb574ea16cbf39373a9ea11078009bc7b997c2f76859",
    "validation/wp02/WP02_001_CLOSURE_CONTRACT.json":
        "2c898dd91e558ce62006dc81de9cff20bb633b52a89f6fa5a44c5edcda50d57a",
    "validation/contracts/WP_0_3B_A1_P1_PREEXECUTION_CORRECTION_CONTRACT.json":
        "d61d33527d6de64201018033da86e78810a3d57a477c17c46639fc90d2b92feb",
    "validation/results/WP_0_3B_A1_NONPROTECTED_EXTRACTION_VERIFICATION_RESULT.json":
        "8af2ec832b191f96994f762eca85eacdc9bfa68ef316321b6b56894d649b6349",
    "validation/contracts/WP_0_3A_INDEPENDENT_HOLDOUT_AND_MECHANISM_DISCRIMINATION_CONTRACT.json":
        "50c9e3e45772b6f243dfe406a4aae3b9496cee3a1e28b41909ab39406d8e2de4",
}
EXPECTED_TEMPLATE_CATEGORIES = {
    "WP_0_3C_ROLE_ASSIGNMENT_TEMPLATE.json": ["governance_and_roles"],
    "WP_0_3C_CAMPAIGN_SCOPE_TEMPLATE.json": ["campaign_scope"],
    "WP_0_3C_APPARATUS_INVENTORY_TEMPLATE.json":
        ["machine_and_hydraulic_apparatus", "basket_and_bed_geometry"],
    "WP_0_3C_SENSOR_INVENTORY_TEMPLATE.json":
        ["pressure_instrumentation", "mass_and_flow_instrumentation",
         "temperature_instrumentation", "time_synchronization_and_logging"],
    "WP_0_3C_MATERIAL_AND_COFFEE_TEMPLATE.json": ["coffee_and_materials"],
    "WP_0_3C_PREPARATION_PROTOCOL_TEMPLATE.json": ["preparation_controls"],
    "WP_0_3C_CALIBRATION_PLAN_TEMPLATE.json": ["calibration_resources"],
    "WP_0_3C_COMMISSIONING_PLAN_TEMPLATE.json": ["commissioning_resources"],
    "WP_0_3C_DATA_CUSTODY_TEMPLATE.json": ["data_custody_and_blinding"],
    "WP_0_3C_PRIVACY_AND_PUBLICATION_TEMPLATE.json":
        ["governance_and_roles", "data_custody_and_blinding"],
    "WP_0_3C_ACQUISITION_READINESS_TEMPLATE.json": list(stage0.CATEGORIES),
}
EXPECTED_REQUIREMENT_METADATA_AGGREGATE = \
    "844532b10a101ce6e4c60baceeb0d670eeb136943183cf2b9e7444f26cab1aab"
EXPECTED_TEMPLATE_MAPPING_AGGREGATE = \
    "40942bbd9848efec54e560b834c44225b0b47c9c624c4228c922c6fd1fdb1a7a"
EXPECTED_COMPLETE_REGISTRY_AGGREGATE = \
    "1776a7b78a2d472ea1a09ecdfa529e117de59920bc35b28d701b5cedff83384c"
EXPECTED_COMPLETE_TEMPLATES_AGGREGATE = \
    "f5caa1b5baa72c5840ace39bb6714a042685ceb7b6346a0d96cfb2edb62a3171"
EXPECTED_CONTRACT_CANONICAL_SHA256 = \
    "9447b938cf91e0ae9d50af4b315b24393b5885dd333a89458d56413294a561fa"
EXPECTED_CLASSIFICATION = [
    "PROTOCOL_SCAFFOLD_AND_INPUT_INTAKE_ONLY",
    "NO_GOVERNING_PHYSICS_CHANGE", "NO_EXPERIMENTAL_EXECUTION",
    "NO_OPENFOAM_EXECUTION", "NO_PUCKWORKS_CODE_EXECUTION",
    "NO_PROTECTED_ACCESS", "NO_HOLDOUT_SCORING",
    "NO_MODEL_DATA_COMPARISON", "NO_SCIENTIFIC_RESULT_CHANGE",
]
EXPECTED_CATEGORIES = [
    "governance_and_roles", "campaign_scope",
    "machine_and_hydraulic_apparatus", "basket_and_bed_geometry",
    "pressure_instrumentation", "mass_and_flow_instrumentation",
    "temperature_instrumentation", "time_synchronization_and_logging",
    "coffee_and_materials", "preparation_controls", "calibration_resources",
    "commissioning_resources", "data_custody_and_blinding",
]
EXPECTED_IDENTITIES = {
    "wp02_result_sha256":
        "75a79e9972176668a8bfdb574ea16cbf39373a9ea11078009bc7b997c2f76859",
    "wp02_closure_contract_sha256":
        "2c898dd91e558ce62006dc81de9cff20bb633b52a89f6fa5a44c5edcda50d57a",
    "historical_scientific_executable_sha256":
        "39056c46c74c53a254e969d02f989ce720dfb567924a90c2f5f8d3b661469ba0",
    "release_executable_sha256":
        "5af892d6382cbc47fa2e6b505fccacf7390bb42bc8d7177106620a43fb26c97b",
    "normalized_solver_source_sha256":
        "97c685bf71df32156e6f697b37fe89e9933b556a02eaf3e7b3b79be0c05ee36f",
    "retained_9bar_trace_sha256":
        "10f69738a35451e4eef132edf29be80a57c667b2cb91cb64914f083302e6b1d0",
    "retained_8bar_trace_sha256":
        "eca75e708d4a12c3fe309ee2e1e6adb463dc974629d85eb1ab9866257ba0c7d0",
    "wp03b_p1_contract_sha256":
        "d61d33527d6de64201018033da86e78810a3d57a477c17c46639fc90d2b92feb",
    "wp03b_amended_result_sha256":
        "8af2ec832b191f96994f762eca85eacdc9bfa68ef316321b6b56894d649b6349",
    "wp03a_holdout_contract_sha256":
        "50c9e3e45772b6f243dfe406a4aae3b9496cee3a1e28b41909ab39406d8e2de4",
}
EXPECTED_DEPENDENCIES = {
    "runtime_puckworks_commit": "fc61c4670ec7bf801e40bb391aab16048b8da26b",
    "runtime_puckworks_tree": "1d553e44ee2f7480a5df521560801b478618cc84",
    "reviewed_puckworks_commit": "bafafef3bc3c77599af8551d4e582aedb9b23f08",
    "reviewed_puckworks_tree": "64ccf86aff4c90d1c513f1614b39e0823f64d6d7",
}
EXPECTED_INFORMATION_BOUNDARY = {
    "public": "PROTOCOL_EQUIPMENT_METADATA_ROLE_IDS_AND_NON_SENSITIVE_HASHES",
    "private": "PERSONAL_OPERATIONAL_CREDENTIAL_KEY_CONDITION_MAP_AND_CONTROLLED_DATA",
    "private_package_binding": "HASH_ONLY_WHERE_APPROPRIATE",
    "credentials_in_repository": False,
}
EXPECTED_REGISTRY_KEYS = {
    "schema_version", "task", "input_classification_vocabulary",
    "deadline_vocabulary", "requirements", "frozen_governing_requirements",
    "public_private_boundary", "readiness",
}
EXPECTED_TEMPLATE_KEYS = {
    "schema_version", "task", "template_status", "final_preregistration",
    "experimental_execution_authorized", "unresolved_value_policy", "fields",
}
EXPECTED_PRIVATE_CLASSIFICATIONS = {
    "PRIVATE_PERSONAL_INPUT", "PRIVATE_OPERATIONAL_INPUT",
    "SEALED_ACQUISITION_INPUT", "MEASURED_HOLDOUT_INPUT",
}
EXPECTED_INPUT_STATUSES = {
    "UNRESOLVED_HUMAN_INPUT", "RESOLVED_HUMAN_INPUT",
}
EXPECTED_READINESS = {
    "current_state": "STAGE0_SCAFFOLD_COMPLETE_AWAITING_HUMAN_INPUTS",
    "stage0_evaluator_states": [
        "AUTHORITY_NOT_ESTABLISHED",
        "STAGE0_SCAFFOLD_COMPLETE_AWAITING_HUMAN_INPUTS",
        "HUMAN_INPUTS_PARTIALLY_COMPLETE",
        "HUMAN_INPUTS_COMPLETE_AWAITING_GOVERNED_REVIEW",
    ],
    "future_governed_authorization_required_states": [
        "APPARATUS_NOT_AVAILABLE", "APPARATUS_PROCUREMENT_REQUIRED",
        "READY_FOR_CALIBRATION_PLANNING",
        "READY_FOR_NONHOLDOUT_COMMISSIONING",
        "READY_TO_FREEZE_FINAL_PREREGISTRATION",
        "FINAL_PREREGISTRATION_FROZEN",
    ],
}
EXPECTED_REGISTRY_INFORMATION_BOUNDARY = {
    "public_repository_package": [
        "role IDs", "campaign design", "equipment make/model",
        "opaque equipment IDs", "sensor specifications",
        "calibration methods", "protocol", "uncertainty requirements",
        "hashes", "public-safe location classes", "acquisition status",
        "non-sensitive provenance",
    ],
    "private_campaign_custody_package": [
        "names and contact details", "private laboratory address",
        "sensitive serial numbers", "credentials", "private storage paths",
        "encryption keys", "condition-code map",
        "private raw data before authorized release",
    ],
    "public_binding": "HASH_PRIVATE_PACKAGE_WITHOUT_DISCLOSURE_WHERE_APPROPRIATE",
}
FORBIDDEN_PATTERNS = (
    r"-----BEGIN .*PRIVATE KEY-----", r"\b(password|api[_-]?key|secret)\s*[:=]\s*\S+",
    r"/home/[A-Za-z0-9_.-]+/", r"\b(model_prediction|model_residual|shot_score)\b",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_aggregate(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def template_mapping(templates: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    return {
        name: {
            category: sorted(fields)
            for category, fields in template.get("fields", {}).items()
        }
        for name, template in templates.items()
    }


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


def _git(root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True,
        stdout=subprocess.PIPE).stdout


def _protected_stage0_path(path: str) -> bool:
    return (
        path == STAGE0_CONTRACT_PATH
        or path == "docs/reports/WP_0_3C_HUMAN_AND_APPARATUS_INPUT_GUIDE.md"
        or path.startswith("validation/campaign/wp03c/")
        or path.startswith("tools/campaign/wp03c/")
    )


def _tree_entries(root: Path, revision: str) -> Dict[str, Dict[str, str]]:
    """Read exact recursive Git-tree entries using an unambiguous NUL format."""
    raw = _git(root, "ls-tree", "-rz", "--full-tree", revision)
    entries = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode, object_type, object_id = metadata.decode("ascii").split(" ")
        path = encoded_path.decode("utf-8", "surrogateescape")
        entries[path] = {
            "path": path,
            "mode": mode,
            "object_type": object_type,
            "object_id": object_id,
        }
    return entries


def historical_stage0_scope(history_root: Path) -> Dict[str, Dict[str, str]]:
    """Return protected Stage-0 Git entries from the pinned public history."""
    observed_tree = _git(
        history_root, "rev-parse", STAGE0_FREEZE_COMMIT + "^{tree}"
    ).decode().strip()
    if observed_tree != STAGE0_FREEZE_TREE:
        raise ValueError("historical Stage-0 tree mismatch")
    historical_contract = _git(
        history_root, "show", STAGE0_FREEZE_COMMIT + ":" + STAGE0_CONTRACT_PATH)
    if hashlib.sha256(historical_contract).hexdigest() != STAGE0_CONTRACT_SHA256:
        raise ValueError("historical Stage-0 contract mismatch")
    contract = json.loads(historical_contract.decode())
    permitted = contract.get("permitted_changed_paths", [])
    if len(permitted) != len(set(permitted)):
        raise ValueError("historical Stage-0 permitted path contract is not unique")
    protected = sorted(path for path in permitted if _protected_stage0_path(path))
    path_aggregate = hashlib.sha256(
        ("\n".join(protected) + "\n").encode()).hexdigest()
    if (len(protected) != STAGE0_PROTECTED_PATH_COUNT
            or path_aggregate != STAGE0_PROTECTED_PATH_AGGREGATE
            or STAGE0_CONTRACT_PATH not in protected
            or "docs/reports/WP_0_3C_HUMAN_AND_APPARATUS_INPUT_GUIDE.md"
            not in protected
            or not any(path.startswith("validation/campaign/wp03c/templates/")
                       for path in protected)
            or "tools/campaign/wp03c/stage0.py" not in protected):
        raise ValueError("historical Stage-0 protected scope is empty or incomplete")
    tree = _tree_entries(history_root, STAGE0_FREEZE_COMMIT)
    scope = {path: dict(tree[path]) for path in protected}
    for path, entry in scope.items():
        if entry["object_type"] != "blob":
            raise ValueError("historical protected entry is not a blob: " + path)
        content = _git(history_root, "cat-file", "blob", entry["object_id"])
        entry["content_sha256"] = hashlib.sha256(content).hexdigest()
    return scope


def historical_stage0_ancestor_of_head(candidate_root: Path) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", STAGE0_FREEZE_COMMIT, "HEAD"],
        cwd=candidate_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0


def frozen_stage0_git_tree_integrity(candidate_root: Path,
                                     history_root: Path = None) -> bool:
    history = history_root or candidate_root
    try:
        expected = historical_stage0_scope(history)
        candidate_tree = _tree_entries(candidate_root, "HEAD")
    except (KeyError, ValueError, subprocess.CalledProcessError,
            json.JSONDecodeError):
        return False
    actual = {path: candidate_tree[path] for path in candidate_tree
              if _protected_stage0_path(path)}
    return actual == {
        path: {key: value for key, value in entry.items()
               if key != "content_sha256"}
        for path, entry in expected.items()
    }


def frozen_stage0_worktree_integrity(candidate_root: Path,
                                     history_root: Path = None) -> bool:
    history = history_root or candidate_root
    try:
        expected = historical_stage0_scope(history)
    except (KeyError, ValueError, subprocess.CalledProcessError,
            json.JSONDecodeError):
        return False
    for path, entry in expected.items():
        target = candidate_root / path
        current = candidate_root
        for component in Path(path).parts:
            current = current / component
            try:
                if stat.S_ISLNK(current.lstat().st_mode):
                    return False
            except FileNotFoundError:
                return False
        try:
            metadata = target.lstat()
        except FileNotFoundError:
            return False
        if entry["object_type"] != "blob" or not stat.S_ISREG(metadata.st_mode):
            return False
        if hashlib.sha256(target.read_bytes()).hexdigest() != entry["content_sha256"]:
            return False
    pathspecs = sorted({
        STAGE0_CONTRACT_PATH,
        "docs/reports/WP_0_3C_HUMAN_AND_APPARATUS_INPUT_GUIDE.md",
        "validation/campaign/wp03c",
        "tools/campaign/wp03c",
    })
    try:
        status = _git(
            candidate_root, "status", "--porcelain=v1", "-z",
            "--untracked-files=all", "--", *pathspecs)
    except subprocess.CalledProcessError:
        return False
    return status == b""


def frozen_stage0_scope_integrity(candidate_root: Path,
                                  history_root: Path = None) -> bool:
    """Compatibility aggregate for callers of the first corrected head."""
    return (frozen_stage0_git_tree_integrity(candidate_root, history_root)
            and frozen_stage0_worktree_integrity(candidate_root, history_root))


def evaluate(contract: Dict[str, object], registry: Dict[str, object],
             templates: Dict[str, Dict[str, object]], paths: frozenset,
             frozen: Dict[str, str], text: str,
             regenerated_identical: bool = True,
             expected_governing: Dict[str, object] = None) -> Dict[str, bool]:
    requirements = registry.get("requirements", [])
    template_values = list(templates.values())
    all_fields = [value for template in template_values
                  for category in template.get("fields", {}).values()
                  for value in category.values()]
    expected_requirements = stage0.requirement_entries()
    expected_by_id = {item["requirement_id"]: item
                      for item in expected_requirements}
    observed_ids = [item.get("requirement_id") for item in requirements]
    templates_exact = set(templates) == set(EXPECTED_TEMPLATE_CATEGORIES)
    if templates_exact:
        templates_exact = all(
            template.get("schema_version") ==
                "espresso.public.wp_0_3c_stage0_input_template.v1"
            and template.get("task") == "WP-0.3C-0"
            and set(template.get("fields", {})) ==
                set(EXPECTED_TEMPLATE_CATEGORIES[name])
            and all(
                set(template["fields"][category]) == {
                    item["field"] for item in expected_requirements
                    if item["category"] == category
                }
                and all(
                    value == stage0.unresolved(
                        stage0.CATEGORIES[category][0],
                        stage0.CATEGORIES[category][2],
                        stage0.CATEGORIES[category][1],
                        stage0.FIELD_RULE_BINDINGS.get((category, field)))
                    for field, value in template["fields"][category].items()
                )
                for category in EXPECTED_TEMPLATE_CATEGORIES[name]
            )
            for name, template in templates.items())
    governing = registry.get("frozen_governing_requirements", {})
    privacy_semantics = all(
        value.get("private_value_required") ==
            (value.get("input_classification") in EXPECTED_PRIVATE_CLASSIFICATIONS)
        and value.get("public_repository_value_allowed") ==
            (value.get("input_classification") not in EXPECTED_PRIVATE_CLASSIFICATIONS)
        for value in all_fields
    )
    return {
        "original_permitted_path_contract":
            canonical_aggregate(contract) == EXPECTED_CONTRACT_CANONICAL_SHA256,
        "baseline_exact":
            contract.get("baseline") == {"commit": BASELINE,
                                         "tree": "2fd9ae4a2e0040602daa29a4b5b4a7bc0ff899b9"},
        "frozen_hashes_exact": frozen == FROZEN,
        "contract_identity_exact":
            canonical_aggregate(contract) == EXPECTED_CONTRACT_CANONICAL_SHA256,
        "contract_semantics_exact":
            contract.get("classification") == EXPECTED_CLASSIFICATION
            and contract.get("required_input_categories") == EXPECTED_CATEGORIES
            and contract.get("allowed_unresolved_status") ==
                "UNRESOLVED_HUMAN_INPUT"
            and contract.get("independent_scaffold_identities") == {
                "canonical_requirement_metadata_aggregate_sha256":
                    EXPECTED_REQUIREMENT_METADATA_AGGREGATE,
                "template_filename_category_field_mapping_aggregate_sha256":
                    EXPECTED_TEMPLATE_MAPPING_AGGREGATE,
                "complete_registry_aggregate_sha256":
                    EXPECTED_COMPLETE_REGISTRY_AGGREGATE,
                "complete_templates_aggregate_sha256":
                    EXPECTED_COMPLETE_TEMPLATES_AGGREGATE}
            and contract.get("immutable_scientific_identities") ==
                EXPECTED_IDENTITIES
            and contract.get("dependencies") == EXPECTED_DEPENDENCIES
            and contract.get("public_private_information_boundary") ==
                EXPECTED_INFORMATION_BOUNDARY
            and contract.get("final_disposition") ==
                "STAGE0_SCAFFOLD_COMPLETE_AWAITING_HUMAN_INPUTS"
            and contract.get("holdout_scoring") == "NOT_PERFORMED"
            and contract.get("new_governing_physics") == "NOT_AUTHORIZED"
            and contract.get("claim_ceiling") ==
                "Input scaffold only; no experimental evidence, final "
                "preregistration, model execution, scoring, or physical validation.",
        "wp03a_governing_requirements_exact":
            expected_governing is not None and governing == expected_governing
            and governing.get("independent_campaign") is True
            and governing.get("preregistered_and_blinded") is True
            and governing.get("minimum_pressure_groups") == 2
            and governing.get("minimum_independent_shots_per_group") == 5
            and governing.get("wp02_parameters_fixed_before_campaign") is True
            and governing.get("no_holdout_parameter_fitting") is True
            and bool(governing.get("required_raw_channels"))
            and bool(governing.get("required_geometry"))
            and bool(governing.get("optional_geometry"))
            and governing.get("bed_area_rule") ==
                expected_governing.get("bed_area_rule")
            and governing.get("open_area_rule") ==
                expected_governing.get("open_area_rule")
            and bool(governing.get("required_timing"))
            and bool(governing.get("required_uncertainty"))
            and bool(governing.get("required_metadata"))
            and bool(governing.get("machine_headspace_discrimination"))
            and "before execution" in governing.get(
                "sample_size_adequacy_rule", ""),
        "retained_trace_identities":
            contract.get("immutable_scientific_identities", {}).get(
                "retained_9bar_trace_sha256") ==
            "10f69738a35451e4eef132edf29be80a57c667b2cb91cb64914f083302e6b1d0"
            and contract.get("immutable_scientific_identities", {}).get(
                "retained_8bar_trace_sha256") ==
            "eca75e708d4a12c3fe309ee2e1e6adb463dc974629d85eb1ab9866257ba0c7d0",
        "requirement_ids_exact_unique":
            len(observed_ids) == len(set(observed_ids)) and
            set(observed_ids) == set(expected_by_id),
        "requirement_metadata_exact":
            len(requirements) == len(expected_requirements) and
            all(item == expected_by_id.get(item.get("requirement_id"))
                for item in requirements),
        "independent_requirement_metadata_identity":
            canonical_aggregate(requirements) ==
                EXPECTED_REQUIREMENT_METADATA_AGGREGATE,
        "independent_template_mapping_identity":
            canonical_aggregate(template_mapping(templates)) ==
                EXPECTED_TEMPLATE_MAPPING_AGGREGATE,
        "complete_registry_identity":
            canonical_aggregate(registry) == EXPECTED_COMPLETE_REGISTRY_AGGREGATE,
        "complete_templates_identity":
            canonical_aggregate(templates) == EXPECTED_COMPLETE_TEMPLATES_AGGREGATE,
        "registry_envelope_exact":
            set(registry) == EXPECTED_REGISTRY_KEYS
            and registry.get("readiness") == EXPECTED_READINESS
            and registry.get("public_private_boundary") ==
                EXPECTED_REGISTRY_INFORMATION_BOUNDARY,
        "template_envelopes_exact":
            all(set(template) == EXPECTED_TEMPLATE_KEYS
                for template in template_values),
        "privacy_vocabularies_exact":
            stage0.PRIVATE_CLASSIFICATIONS == EXPECTED_PRIVATE_CLASSIFICATIONS
            and stage0.INPUT_STATUSES == EXPECTED_INPUT_STATUSES,
        "privacy_semantics_exact": privacy_semantics,
        "classifications_complete":
            set(registry.get("input_classification_vocabulary", [])) ==
                stage0.CLASSIFICATIONS
            and set(registry.get("deadline_vocabulary", [])) == stage0.DEADLINES,
        "required_categories_complete":
            {r.get("category") for r in requirements} == set(EXPECTED_CATEGORIES),
        "templates_nonfinal":
            len(template_values) == 11 and all(
                t.get("template_status") == "NONFINAL_INPUT_TEMPLATE"
                and t.get("final_preregistration") is False
                and t.get("experimental_execution_authorized") is False
                and t.get("unresolved_value_policy") == "UNRESOLVED_HUMAN_INPUT_ONLY"
                for t in template_values),
        "template_structure_exact": templates_exact,
        "deterministic_regeneration_byte_identical": regenerated_identical,
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
            and contract.get("holdout_acquisition") == "NOT_AUTHORIZED"
            and contract.get("holdout_scoring") == "NOT_PERFORMED"
            and contract.get("new_governing_physics") == "NOT_AUTHORIZED",
        "no_forbidden_content":
            not any(re.search(pattern, text, re.IGNORECASE)
                    for pattern in FORBIDDEN_PATTERNS),
    }


def verify(root: Path) -> Dict[str, object]:
    contract = json.loads((root / "validation/contracts/WP_0_3C_STAGE0_AUTHORITY_AND_INPUT_INTAKE_CONTRACT.json").read_text())
    registry = json.loads((root / "validation/campaign/wp03c/WP_0_3C_INPUT_REQUIREMENTS.json").read_text())
    template_dir = root / "validation/campaign/wp03c/templates"
    templates = {path.name: json.loads(path.read_text())
                 for path in sorted(template_dir.glob("*.json"))}
    with tempfile.TemporaryDirectory(prefix="wp03c-stage0-a-") as a_name, \
            tempfile.TemporaryDirectory(prefix="wp03c-stage0-b-") as b_name:
        a = Path(a_name)
        b = Path(b_name)
        stage0.write_scaffold(root, a)
        stage0.write_scaffold(root, b)
        generated_paths = [
            "validation/campaign/wp03c/WP_0_3C_INPUT_REQUIREMENTS.json"
        ] + [
            "validation/campaign/wp03c/templates/" + name
            for name in sorted(EXPECTED_TEMPLATE_CATEGORIES)
        ]
        regenerated_identical = all(
            (a / path).read_bytes() == (b / path).read_bytes() ==
            (root / path).read_bytes() for path in generated_paths)
    paths = changed_paths(root)
    frozen = {path: sha(root / path) for path in FROZEN}
    scope = historical_stage0_scope(root)
    text = "\n".join(
        (root / path).read_text(errors="replace")
        for path in sorted(scope)
        if (root / path).is_file() and Path(path).suffix in {".json", ".md"})
    checks = evaluate(
        contract, registry, templates, paths, frozen, text,
        regenerated_identical, stage0.wp03a_governing_requirements(root))
    checks["historical_stage0_identity"] = bool(scope)
    checks["historical_stage0_ancestor_of_head"] = \
        historical_stage0_ancestor_of_head(root)
    checks["frozen_stage0_git_tree_integrity"] = \
        frozen_stage0_git_tree_integrity(root)
    checks["frozen_stage0_worktree_integrity"] = \
        frozen_stage0_worktree_integrity(root)
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
