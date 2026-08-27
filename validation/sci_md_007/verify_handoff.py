#!/usr/bin/env python3
"""Exact-byte, fail-closed verification of the SCI-MD-007-R2 handoff.

EWP verifies the exact Puckworks producer authority and source-package bytes
and independently reduces the exported Boolean feasibility decision. Puckworks
remains the authority that derives gate primitives from evidence registers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "docs/validation/sci_md_007"
UPSTREAM = HERE / "upstream"
PASS = "SCI_MD_007_INVENTORY_PREDICTION_FEASIBLE_WITH_EXISTING_EVIDENCE"
FAIL = "SCI_MD_007_INVENTORY_PRIOR_ONLY_ADDITIONAL_DIRECT_MEASUREMENTS_REQUIRED"
GATES = ("F0", "F1", "F2", "F3", "F4", "F6", "F7")
RESULT_SCHEMA = "1.2.0-R2"
LOCK_SCHEMA = "espresso.sci_md_007.puckworks_lock.v4"
EXPECTED_R2_CONTRACT_SHA256 = "4893158c36c6902c73a7839b9b7ad65df07a74951240dc3910599b50bdaecd1d"
STARTING_COMMIT = "434c657fa35e1e36003c67b57062b216cddcc151"
STARTING_TREE = "efdf0558a592c6c4ec0cc2e0a74731de04cb93f6"
ALLOWED_R2_PATHS = {
    "PACKAGE_QA_STATUS.json",
    "SOURCE_PACKAGE_MANIFEST.json",
    "docs/PROJECT_STATE.md",
    "docs/strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md",
    "docs/validation/sci_md_007/PUCKWORKS_LOCK.json",
    "docs/validation/sci_md_007/R2_QUALIFICATION.md",
    "docs/validation/sci_md_007/RESULT.json",
    "docs/validation/sci_md_007/RESULT.md",
    "docs/validation/sci_md_007/upstream/SCI_MD_007_EXPORT.json",
    "docs/validation/sci_md_007/upstream/source_package_manifest.json",
    "docs/validation/sci_md_007/upstream/R2_EVIDENCE_PACKAGE_CORRECTION_CONTRACT.json",
    "docs/validation/sci_md_007/upstream/R2_PACKAGE_AUTHORITY_CLOSURE.json",
    "docs/validation/sci_md_007/BOUNDARY_EVIDENCE.json",
    "docs/validation/sci_md_007/EWP_CANDIDATE_BINDING.json",
    "scripts/generate_source_manifest.py",
    "tests/test_sci_md_007_handoff.py",
    "tests/test_sci_md_004_stage_a.py",
    "validation/sci_md_007/verify_handoff.py",
}
REQUIRED_INPUTS = {
    "docs/analysis/sci_md_007/feasibility_contract.json",
    "docs/analysis/sci_md_007/r1/R1_CORRECTIVE_SEARCH_CONTRACT.json",
    "docs/analysis/sci_md_007/r1/R1_CORRECTIVE_SEARCH_PROTOCOL.md",
    "docs/analysis/sci_md_007/r2/R2_EVIDENCE_PACKAGE_CORRECTION_CONTRACT.json",
    "puckworks/analysis/sci_md_007_r2.py",
    "puckworks/data/sci_md_007/sources.csv",
    "puckworks/data/sci_md_007/materials.csv",
    "puckworks/data/sci_md_007/observations.csv",
    "puckworks/data/sci_md_007/search_log.csv",
    "puckworks/data/sci_md_007/search_results.csv",
    "puckworks/data/sci_md_007/citation_passes.csv",
    "puckworks/data/sci_md_007/lineage_links.csv",
}
REQUIRED_OUTPUTS = {
    "docs/analysis/sci_md_007/SCI_MD_007_EXPORT.json",
    "docs/analysis/sci_md_007/result.json",
    "docs/analysis/sci_md_007/feasibility_gates.json",
    "docs/analysis/sci_md_007/r2/R2_CROSS_ARTIFACT_AUDIT.json",
    "docs/analysis/sci_md_007/r2/search_closure_audit.json",
    "docs/analysis/sci_md_007/r2/fold_transportability_audit.csv",
}
ACCEPTED_CONSUMER_EVIDENCE = {
    "docs/validation/sci_md_007/BOUNDARY_EVIDENCE.json",
    "docs/validation/sci_md_007/PUCKWORKS_LOCK.json",
    "docs/validation/sci_md_007/R2_QUALIFICATION.md",
    "docs/validation/sci_md_007/RESULT.json",
    "docs/validation/sci_md_007/RESULT.md",
    "docs/validation/sci_md_007/upstream/R2_EVIDENCE_PACKAGE_CORRECTION_CONTRACT.json",
    "docs/validation/sci_md_007/upstream/R2_PACKAGE_AUTHORITY_CLOSURE.json",
    "docs/validation/sci_md_007/upstream/SCI_MD_007_EXPORT.json",
    "docs/validation/sci_md_007/upstream/source_package_manifest.json",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=False
    )


def _git_bytes(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=False
    )


def derive_boundary_evidence(root: Path = ROOT) -> dict:
    changed = _git(root, "diff", "--name-only", STARTING_COMMIT)
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    paths = (
        sorted(set(changed.stdout.splitlines()) | set(untracked.stdout.splitlines()))
        if changed.returncode == 0 and untracked.returncode == 0
        else []
    )
    paths = [
        path
        for path in paths
        if path != "docs/validation/sci_md_007/EWP_CANDIDATE_BINDING.json"
    ]
    physics = [p for p in paths if p.startswith(("solver/", "src/solver/", "physics/"))]
    openfoam = [p for p in paths if p.startswith(("applications/", "cases/")) or "openfoam" in p.lower()]
    runtime = [p for p in paths if "inventory" in p.lower() and not p.startswith(("docs/", "tests/", "validation/"))]
    sci006 = [p for p in paths if "sci_md_006" in p.lower()]
    g0 = [p for p in paths if "/g0" in p.lower() or p.lower().startswith("g0")]
    protected = [p for p in paths if "angeloni" in p.lower() or "protected" in p.lower()]
    content_hits = []
    for path in paths:
        candidate = root / path
        if candidate.is_file() and path.startswith("docs/") and re.search(
            r'(?i)(source_lineage|protected_source)\s*["=: ]+angeloni',
            candidate.read_text(errors="ignore"),
        ):
            content_hits.append(path)
    commands = {
        "changed_paths": {
            "argv": ["git", "diff", "--name-only", STARTING_COMMIT],
            "exit_status": changed.returncode,
            "stdout_sha256": _sha(changed.stdout.encode()),
            "stderr_sha256": _sha(changed.stderr.encode()),
        },
        "untracked_paths": {
            "argv": ["git", "ls-files", "--others", "--exclude-standard"],
            "exit_status": untracked.returncode,
            "stdout_sha256": _sha(untracked.stdout.encode()),
            "stderr_sha256": _sha(untracked.stderr.encode()),
        },
    }
    status = changed.returncode == 0 and not any(
        (physics, openfoam, runtime, sci006, g0, protected, content_hits)
    )
    return {
        "schema_version": "espresso.sci_md_007.boundary_evidence.v1",
        "starting_commit": STARTING_COMMIT,
        "starting_tree": STARTING_TREE,
        "changed_paths": paths,
        "changed_file_sha256": {
            p: _sha((root / p).read_bytes())
            for p in paths
            if (root / p).is_file()
            and p
            not in {
                "SOURCE_PACKAGE_MANIFEST.json",
                "PACKAGE_QA_STATUS.json",
                "docs/validation/sci_md_007/BOUNDARY_EVIDENCE.json",
                "docs/validation/sci_md_007/EWP_CANDIDATE_BINDING.json",
            }
        },
        "allowed_path_check": set(paths) <= ALLOWED_R2_PATHS,
        "governing_physics_intersection": physics,
        "openfoam_intersection": openfoam,
        "runtime_inventory_provider_intersection": runtime,
        "sci_md_006_intersection": sci006,
        "g0_intersection": g0,
        "protected_data_path_intersection": protected,
        "protected_data_content_intersection": content_hits,
        "commands": commands,
        "no_network_no_new_evidence": True,
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE" if status else None,
        "inventory_predictor_activation": "NOT_AUTHORIZED" if status else None,
        "openfoam_execution": "NOT_RUN" if status else None,
        "angeloni_reuse": False if status else None,
        "sci_md_006_reopened": False if status else None,
        "g0_fraction_boundary_parity": "NOT_RUN_SEPARATE_DEFERRED" if status else None,
        "status": "PASS" if status and set(paths) <= ALLOWED_R2_PATHS else "FAIL",
    }


def create_candidate_binding(e3: str, root: Path = ROOT) -> dict:
    tree = _git(root, "rev-parse", f"{e3}^{{tree}}")
    changed = _git(root, "diff", "--name-only", STARTING_COMMIT, e3)
    if tree.returncode or changed.returncode:
        raise ValueError("cannot resolve E3 candidate")
    paths = sorted(changed.stdout.splitlines())
    scientific = [
        path
        for path in paths
        if path != "docs/validation/sci_md_007/EWP_CANDIDATE_BINDING.json"
    ]
    hashes = {}
    for path in scientific:
        value = _git_bytes(root, "show", f"{e3}:{path}")
        if value.returncode:
            raise ValueError(f"missing E3 scientific path: {path}")
        hashes[path] = _sha(value.stdout)
    lock = json.loads((root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json").read_text())
    boundary = (root / "docs/validation/sci_md_007/BOUNDARY_EVIDENCE.json").read_bytes()
    return {
        "schema_version": "espresso.sci_md_007.ewp_candidate_binding.v1",
        "starting_commit": STARTING_COMMIT,
        "starting_tree": STARTING_TREE,
        "e3_commit": e3,
        "e3_tree": tree.stdout.strip(),
        "base_to_e3_changed_paths": paths,
        "e3_scientific_file_sha256": hashes,
        "p3_commit": lock["commit"],
        "p3_tree": lock["tree"],
        "boundary_evidence_sha256": _sha(boundary),
        "allowed_e3b_paths": ["docs/validation/sci_md_007/EWP_CANDIDATE_BINDING.json"],
    }


def verify_candidate_binding(binding: dict, root: Path = ROOT) -> bool:
    required = {
        "starting_commit", "starting_tree", "e3_commit", "e3_tree",
        "base_to_e3_changed_paths", "e3_scientific_file_sha256", "p3_commit", "p3_tree",
        "boundary_evidence_sha256", "allowed_e3b_paths",
    }
    if not required <= set(binding):
        return False
    if (binding["starting_commit"], binding["starting_tree"]) != (STARTING_COMMIT, STARTING_TREE):
        return False
    tree = _git(root, "rev-parse", f"{binding['e3_commit']}^{{tree}}")
    changed = _git(root, "diff", "--name-only", STARTING_COMMIT, binding["e3_commit"])
    if tree.returncode or changed.returncode:
        return False
    if tree.stdout.strip() != binding["e3_tree"] or sorted(changed.stdout.splitlines()) != binding["base_to_e3_changed_paths"]:
        return False
    # The binding freezes E3/E3b. Unrelated later programmes are outside this
    # historical candidate range and have their own branch-scope controls.
    for path, expected in binding["e3_scientific_file_sha256"].items():
        value = _git_bytes(root, "show", f"{binding['e3_commit']}:{path}")
        if value.returncode or _sha(value.stdout) != expected:
            return False
    boundary = root / "docs/validation/sci_md_007/BOUNDARY_EVIDENCE.json"
    return boundary.is_file() and _sha(boundary.read_bytes()) == binding["boundary_evidence_sha256"]


def _manifest_members(manifest: dict) -> dict[str, str]:
    if manifest.get("schema_version") != "1.3.0-R2-C1":
        raise ValueError("manifest schema mismatch")
    inputs = manifest.get("inputs")
    outputs = manifest.get("outputs")
    if not isinstance(inputs, dict) or not inputs or not isinstance(outputs, dict) or not outputs:
        raise ValueError("manifest inputs/outputs missing")
    if not REQUIRED_INPUTS <= set(inputs):
        raise ValueError(f"required manifest inputs missing: {sorted(REQUIRED_INPUTS - set(inputs))}")
    if not REQUIRED_OUTPUTS <= set(outputs):
        raise ValueError(f"required manifest outputs missing: {sorted(REQUIRED_OUTPUTS - set(outputs))}")
    overlap = set(inputs) & set(outputs)
    if overlap:
        raise ValueError(f"manifest input/output overlap: {sorted(overlap)}")
    members = {**inputs, **outputs}
    for path, digest in members.items():
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in Path(path).parts:
            raise ValueError("invalid manifest member path")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("invalid manifest member hash")
    if manifest.get("expected_input_members") != sorted(inputs):
        raise ValueError("manifest expected/input member-set mismatch")
    if manifest.get("expected_output_members") != sorted(outputs):
        raise ValueError("manifest expected/output member-set mismatch")
    return members


def _require_fields(node: dict, fields: set[str], context: str) -> None:
    missing = fields - set(node)
    if missing:
        raise ValueError(f"missing {context} fields: {sorted(missing)}")


def _validate_gate_surface(export: dict) -> None:
    required = {
        "F0": {"applicability", "eligible_rows", "pass"},
        "F1": {"eligible_dry_basis_rows", "unsupported_conversions", "pass"},
        "F2": {"material_roast_units", "base_materials", "publications", "identified_laboratories", "validation_groups", "largest_group_share", "thresholds", "pass"},
        "F3": {"species", "thresholds", "pass"},
        "F4": {"categorical_route", "quantitative_route", "thresholds", "pass"},
        "F6": {"eligible_units", "uncertainty_bearing_units", "uncertainty_bearing_fraction", "source_laboratory_groups", "thresholds", "pass"},
        "F7": {"outer_validation_groups", "publication_leakage", "data_lineage_leakage", "base_material_leakage", "proposed_folds", "species_support_all_folds", "harmonized_roast_category_support_all_folds", "quantitative_metric_type_support_all_folds", "thresholds", "pass"},
    }
    for analyte in ("caffeine", "trigonelline"):
        gates = export["compound_gates"][analyte]
        for gate, fields in required.items():
            _require_fields(gates[gate], fields, f"{analyte}.{gate}")
        quantitative = gates["F4"]["quantitative_route"]
        _require_fields(
            quantitative,
            {"material_roast_units", "validation_groups", "units_per_species", "within_species_varying_groups", "minimum_within_species_varying_groups", "primitive_pass", "pass"},
            f"{analyte}.F4.quantitative_route",
        )
        for species in ("Arabica", "Robusta"):
            variation = quantitative["within_species_varying_groups"][species]
            _require_fields(
                variation,
                {"count", "threshold", "pass", "qualifying_groups"},
                f"{analyte}.F4.quantitative_route.{species}",
            )
        for fold in gates["F7"]["proposed_folds"]:
            _require_fields(
                fold,
                {"test_group", "training_groups", "publication_intersection_ids", "data_lineage_intersection_ids", "base_material_intersection_ids", "test_species", "training_species", "unsupported_test_species"},
                f"{analyte}.F7.fold",
            )
    _require_fields(
        export["paired_coverage"]["F5"],
        {"paired_material_roast_units", "validation_groups", "thresholds", "pass"},
        "F5",
    )


def _canonical_json_sha256(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return _sha(encoded.encode())


def derive_result(export: dict, contract: dict, boundary: dict | None = None) -> dict:
    _validate_gate_surface(export)
    compounds = {}
    gate_results = {}
    for analyte in ("caffeine", "trigonelline"):
        nested = export["compound_gates"][analyte]
        if set(nested) != set(GATES) or any(
            type(nested[g].get("pass")) is not bool for g in GATES
        ):
            raise ValueError(f"invalid nested gates for {analyte}")
        gate_results[analyte] = {g: nested[g]["pass"] for g in GATES}
        compounds[analyte] = all(gate_results[analyte].values())
    f5 = export["paired_coverage"]["F5"]["pass"]
    if type(f5) is not bool:
        raise ValueError("F5 pass is not a Boolean")
    overall = compounds["caffeine"] and compounds["trigonelline"] and f5
    disposition = PASS if overall else FAIL
    if (
        export["compound_feasible"] != compounds
        or export["overall_gate_result"] is not overall
    ):
        raise ValueError("upstream top-level Boolean disagrees with nested gates")
    if export["scientific_disposition"] != disposition:
        raise ValueError("upstream disposition disagrees with mechanical reduction")
    if export["operational_status"] != "COMPLETE":
        raise ValueError("upstream operation is not complete")
    lineage_payload = {
        key: value for key, value in export.items() if key != "claim_ceiling"
    }
    if "angeloni" in json.dumps(lineage_payload, sort_keys=True).lower():
        raise ValueError("prohibited lineage identifier in export")
    if export.get("sci_md_006_reopened") not in (None, False):
        raise ValueError("SCI-MD-006 reopening asserted")
    if export.get("openfoam_execution") not in (None, "NOT_RUN"):
        raise ValueError("OpenFOAM execution asserted")
    if export.get("inventory_predictor_activation") not in (None, "NOT_AUTHORIZED"):
        raise ValueError("runtime predictor activation asserted")
    if (
        export["task_id"],
        export["schema_version"],
        export["evidence_cutoff_date"],
    ) != ("SCI-MD-007", RESULT_SCHEMA, "2026-08-25"):
        raise ValueError("upstream task/schema/cutoff mismatch")
    claim_ceiling = contract.get("claim_ceiling")
    claim_hash = _canonical_json_sha256(claim_ceiling)
    if export.get("claim_ceiling") != claim_ceiling:
        raise ValueError("claim ceiling mismatch")
    if export.get("claim_ceiling_sha256") != claim_hash:
        raise ValueError("claim ceiling hash mismatch")
    if disposition == FAIL and export["model_stage"] != "NOT_RUN_FEASIBILITY_FAILED":
        raise ValueError("FAIL did not prevent model execution")
    if export["extractable_inventory_mapping_status"] == "DIRECTLY_SUPPORTED":
        raise ValueError(
            "total-content result improperly establishes extractable inventory"
        )
    if boundary is None:
        boundary = {
            "status": "PASS",
            "change_declaration": contract["change_declaration"],
            "inventory_predictor_activation": "NOT_AUTHORIZED",
            "openfoam_execution": "NOT_RUN",
            "angeloni_reuse": False,
            "sci_md_006_reopened": False,
            "g0_fraction_boundary_parity": "NOT_RUN_SEPARATE_DEFERRED",
        }
    if boundary.get("status") != "PASS":
        raise ValueError("boundary evidence failed")
    return {
        "schema_version": "espresso.sci_md_007.handoff.v4",
        "task_id": "SCI-MD-007",
        "change_declaration": boundary["change_declaration"],
        "operational_status": "COMPLETE",
        "scientific_disposition": disposition,
        "caffeine_feasible": compounds["caffeine"],
        "trigonelline_feasible": compounds["trigonelline"],
        "paired_gate_F5": f5,
        "overall_feasible": overall,
        "compound_gate_results": gate_results,
        "extractable_inventory_mapping_status": export[
            "extractable_inventory_mapping_status"
        ],
        "model_stage": export["model_stage"],
        "inventory_predictor_activation": boundary["inventory_predictor_activation"],
        "model_adoption_status": export["model_adoption_status"],
        "physical_validation": (
            "NOT_ESTABLISHED"
            if claim_ceiling[0] == "Physical validation remains NOT_ESTABLISHED."
            else None
        ),
        "openfoam_execution": boundary["openfoam_execution"],
        "angeloni_reuse": boundary["angeloni_reuse"],
        "sci_md_006_reopened": boundary["sci_md_006_reopened"],
        "g0_fraction_boundary_parity": boundary["g0_fraction_boundary_parity"],
        "claim_ceiling": claim_ceiling,
        "claim_ceiling_source": export["claim_ceiling_source"],
        "claim_ceiling_sha256": claim_hash,
    }


def verify(puckworks_repo: str | Path | None = None, root: Path = ROOT) -> dict:
    here = root / "docs/validation/sci_md_007"
    upstream = here / "upstream"
    failures = []
    checks = {}
    try:
        lock = json.loads((here / "PUCKWORKS_LOCK.json").read_text(encoding="utf-8"))
        export_bytes = (upstream / "SCI_MD_007_EXPORT.json").read_bytes()
        manifest_bytes = (upstream / "source_package_manifest.json").read_bytes()
        contract_bytes = (upstream / "R2_EVIDENCE_PACKAGE_CORRECTION_CONTRACT.json").read_bytes()
        closure_bytes = (upstream / "R2_PACKAGE_AUTHORITY_CLOSURE.json").read_bytes()
        checks["export_exact_hash"] = _sha(export_bytes) == lock["export_sha256"]
        checks["manifest_exact_hash"] = (
            _sha(manifest_bytes) == lock["source_package_manifest_sha256"]
        )
        checks["contract_exact_hash"] = _sha(contract_bytes) == lock["r2_contract_sha256"]
        checks["contract_immutable_authority"] = (
            _sha(contract_bytes) == EXPECTED_R2_CONTRACT_SHA256
            and lock["expected_r2_contract_sha256"] == EXPECTED_R2_CONTRACT_SHA256
        )
        checks["package_closure_exact_hash"] = (
            _sha(closure_bytes) == lock["package_authority_closure_sha256"]
        )
        checks["lock_schema"] = lock["schema_version"] == LOCK_SCHEMA
        checks["repository_identity"] = (
            lock["repository"] == "https://github.com/trbrewer/puckworks.git"
        )
        export = json.loads(export_bytes)
        manifest = json.loads(manifest_bytes)
        contract = json.loads(contract_bytes)
        closure = json.loads(closure_bytes)
        members = _manifest_members(manifest)
        checks["manifest_export_member"] = (
            manifest["outputs"].get(lock["export_path"]) == lock["export_sha256"]
            and _sha(export_bytes) == manifest["outputs"].get(lock["export_path"])
        )
        checks["manifest_contract"] = (
            manifest.get("r2_contract_sha256") == lock["r2_contract_sha256"]
        )
        checks["manifest_claim_ceiling"] = (
            manifest["claim_ceiling_sha256"] == _canonical_json_sha256(contract["claim_ceiling"])
            == lock["claim_ceiling_sha256"]
        )
        checks["package_closure_manifest"] = (
            closure["manifest_sha256"] == _sha(manifest_bytes)
            and closure["manifest_path"] == lock["manifest_path"]
        )
        checks["package_closure_status"] = (
            closure["final_package_status"] == "PASS"
            and not closure["missing_members"]
            and not closure["unexpected_members"]
            and not closure["wrong_hash_members"]
            and all(closure["checks"].values())
            and all(x["pass"] for x in closure["input_member_checks"].values())
            and all(x["pass"] for x in closure["output_member_checks"].values())
        )
        checks["lock_result_authority"] = (
            lock["result_schema_version"] == RESULT_SCHEMA
            and lock["evidence_cutoff_date"] == "2026-08-25"
        )
        boundary_path = here / "BOUNDARY_EVIDENCE.json"
        boundary = json.loads(boundary_path.read_text())
        binding_path = here / "EWP_CANDIDATE_BINDING.json"
        if binding_path.is_file() and _git(root, "rev-parse", "--git-dir").returncode == 0:
            binding = json.loads(binding_path.read_text())
            frozen_boundary = _git_bytes(
                root,
                "show",
                f"{binding['e3_commit']}:docs/validation/sci_md_007/BOUNDARY_EVIDENCE.json",
            )
            checks["boundary_evidence_rederived"] = (
                frozen_boundary.returncode == 0
                and frozen_boundary.stdout == boundary_path.read_bytes()
            )
        elif _git(root, "rev-parse", "--git-dir").returncode == 0:
            checks["boundary_evidence_rederived"] = boundary == derive_boundary_evidence(root)
        else:
            checks["boundary_evidence_hermetic"] = (
                boundary.get("status") == "PASS"
                and not boundary.get("governing_physics_intersection")
                and not boundary.get("openfoam_intersection")
                and not boundary.get("runtime_inventory_provider_intersection")
                and not boundary.get("protected_data_path_intersection")
                and not boundary.get("protected_data_content_intersection")
            )
        if binding_path.is_file() and _git(root, "rev-parse", "--git-dir").returncode == 0:
            checks["e3_e3b_candidate_binding"] = verify_candidate_binding(binding, root)
            checks["binding_p3_authority"] = (
                binding.get("p3_commit") == lock["commit"]
                and binding.get("p3_tree") == lock["tree"]
            )
            preserved = []
            for path in sorted(ACCEPTED_CONSUMER_EVIDENCE):
                frozen = _git_bytes(root, "show", f"{binding['e3_commit']}:{path}")
                current = root / path
                if frozen.returncode or not current.is_file() or frozen.stdout != current.read_bytes():
                    preserved.append(path)
            checks["accepted_consumer_evidence_preserved"] = not preserved
            failures.extend(f"accepted_consumer_evidence_changed:{path}" for path in preserved)
        expected = derive_result(export, contract, boundary)
        committed = json.loads((here / "RESULT.json").read_text(encoding="utf-8"))
        checks["generated_result"] = committed == expected
        checks["no_absolute_paths"] = "/home/" not in json.dumps(
            {"lock": lock, "result": committed}
        )
        checks["no_predictor_or_physics"] = (
            committed["inventory_predictor_activation"] == "NOT_AUTHORIZED"
            and committed["physical_validation"] == "NOT_ESTABLISHED"
            and committed["change_declaration"] == "NO_GOVERNING_PHYSICS_CHANGE"
            and committed["openfoam_execution"] == "NOT_RUN"
            and committed["g0_fraction_boundary_parity"]
            == "NOT_RUN_SEPARATE_DEFERRED"
        )
        checks["exclusions"] = (
            committed["angeloni_reuse"] is False
            and committed["sci_md_006_reopened"] is False
        )
        # Historical SCI-MD-007 applicability is bound above to its E3 consumer
        # and P3 producer objects. Later branch paths are governed separately by
        # the current task's no-physics verifier, never by this historical list.
        if puckworks_repo is not None:
            repo = Path(puckworks_repo).resolve()
            remote = _git(repo, "remote", "get-url", "origin")
            commit = _git(repo, "cat-file", "-e", lock["commit"] + "^{commit}")
            tree = _git(repo, "rev-parse", lock["commit"] + "^{tree}")
            upstream_export = _git_bytes(
                repo, "show", f"{lock['commit']}:{lock['export_path']}"
            )
            upstream_manifest = _git_bytes(
                repo, "show", f"{lock['commit']}:{lock['manifest_path']}"
            )
            upstream_contract = _git_bytes(repo, "show", f"{lock['commit']}:{lock['r2_contract_path']}")
            upstream_closure = _git_bytes(repo, "show", f"{lock['commit']}:{lock['package_authority_closure_path']}")
            checks["cross_repository_remote"] = (
                remote.returncode == 0
                and remote.stdout.strip().removesuffix(".git")
                == lock["repository"].removesuffix(".git")
            )
            checks["cross_repository_commit"] = commit.returncode == 0
            checks["cross_repository_tree"] = (
                tree.returncode == 0 and tree.stdout.strip() == lock["tree"]
            )
            checks["cross_repository_export"] = (
                upstream_export.returncode == 0
                and upstream_export.stdout == export_bytes
            )
            checks["cross_repository_manifest"] = (
                upstream_manifest.returncode == 0
                and upstream_manifest.stdout == manifest_bytes
            )
            checks["cross_repository_contract"] = upstream_contract.returncode == 0 and upstream_contract.stdout == contract_bytes
            checks["cross_repository_package_closure"] = upstream_closure.returncode == 0 and upstream_closure.stdout == closure_bytes
            member_failures = []
            for path, expected_hash in sorted(members.items()):
                object_data = _git_bytes(repo, "show", f"{lock['commit']}:{path}")
                if object_data.returncode != 0 or _sha(object_data.stdout) != expected_hash:
                    member_failures.append(path)
            checks["cross_repository_manifest_member_closure"] = not member_failures
            if member_failures:
                failures.extend(f"manifest_member:{path}" for path in member_failures)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, OSError) as exc:
        failures.append(f"exception:{type(exc).__name__}:{exc}")
    failures.extend(name for name, ok in checks.items() if not ok)
    return {
        "schema_version": "espresso.sci_md_007.verification.v3",
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--puckworks-repo", default=os.environ.get("PUCKWORKS_GIT_REPOSITORY"))
    parser.add_argument("--write-result", action="store_true")
    parser.add_argument("--write-boundary", action="store_true")
    parser.add_argument("--write-binding")
    args = parser.parse_args()
    if args.write_boundary:
        (HERE / "BOUNDARY_EVIDENCE.json").write_text(
            json.dumps(derive_boundary_evidence(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.write_binding:
        (HERE / "EWP_CANDIDATE_BINDING.json").write_text(
            json.dumps(create_candidate_binding(args.write_binding), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
    if args.write_result:
        export = json.loads(
            (UPSTREAM / "SCI_MD_007_EXPORT.json").read_text(encoding="utf-8")
        )
        contract = json.loads(
            (UPSTREAM / "R2_EVIDENCE_PACKAGE_CORRECTION_CONTRACT.json").read_text(
                encoding="utf-8"
            )
        )
        boundary = json.loads((HERE / "BOUNDARY_EVIDENCE.json").read_text())
        (HERE / "RESULT.json").write_text(
            json.dumps(derive_result(export, contract, boundary), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
    report = verify(args.puckworks_repo)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
