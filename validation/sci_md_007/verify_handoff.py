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
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "docs/validation/sci_md_007"
UPSTREAM = HERE / "upstream"
PASS = "SCI_MD_007_INVENTORY_PREDICTION_FEASIBLE_WITH_EXISTING_EVIDENCE"
FAIL = "SCI_MD_007_INVENTORY_PRIOR_ONLY_ADDITIONAL_DIRECT_MEASUREMENTS_REQUIRED"
GATES = ("F0", "F1", "F2", "F3", "F4", "F6", "F7")
RESULT_SCHEMA = "1.2.0-R2"
LOCK_SCHEMA = "espresso.sci_md_007.puckworks_lock.v3"
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


def _manifest_members(manifest: dict) -> dict[str, str]:
    if manifest.get("schema_version") != RESULT_SCHEMA:
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


def derive_result(export: dict) -> dict:
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
    if not isinstance(export.get("claim_ceiling"), list) or not any(
        "NOT_ESTABLISHED" in x for x in export["claim_ceiling"]
    ):
        raise ValueError("claim ceiling mismatch")
    if disposition == FAIL and export["model_stage"] != "NOT_RUN_FEASIBILITY_FAILED":
        raise ValueError("FAIL did not prevent model execution")
    if export["extractable_inventory_mapping_status"] == "DIRECTLY_SUPPORTED":
        raise ValueError(
            "total-content result improperly establishes extractable inventory"
        )
    return {
        "schema_version": "espresso.sci_md_007.handoff.v3",
        "task_id": "SCI-MD-007",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
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
        "inventory_predictor_activation": "NOT_AUTHORIZED",
        "model_adoption_status": export["model_adoption_status"],
        "physical_validation": "NOT_ESTABLISHED",
        "openfoam_execution": "NOT_RUN",
        "angeloni_reuse": False,
        "sci_md_006_reopened": False,
        "g0_fraction_boundary_parity": "NOT_RUN_SEPARATE_DEFERRED",
        "claim_ceiling": export["claim_ceiling"],
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
        checks["export_exact_hash"] = _sha(export_bytes) == lock["export_sha256"]
        checks["manifest_exact_hash"] = (
            _sha(manifest_bytes) == lock["source_package_manifest_sha256"]
        )
        checks["lock_schema"] = lock["schema_version"] == LOCK_SCHEMA
        checks["repository_identity"] = (
            lock["repository"] == "https://github.com/trbrewer/puckworks.git"
        )
        export = json.loads(export_bytes)
        manifest = json.loads(manifest_bytes)
        members = _manifest_members(manifest)
        checks["manifest_export_member"] = (
            manifest["outputs"].get(lock["export_path"]) == lock["export_sha256"]
            and _sha(export_bytes) == manifest["outputs"].get(lock["export_path"])
        )
        checks["manifest_contract"] = (
            manifest.get("r2_contract_sha256")
            == lock["correction_contract_sha256"]
        )
        checks["lock_result_authority"] = (
            lock["result_schema_version"] == RESULT_SCHEMA
            and lock["evidence_cutoff_date"] == "2026-08-25"
        )
        expected = derive_result(export)
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
    parser.add_argument("--puckworks-repo")
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args()
    if args.write_result:
        export = json.loads(
            (UPSTREAM / "SCI_MD_007_EXPORT.json").read_text(encoding="utf-8")
        )
        (HERE / "RESULT.json").write_text(
            json.dumps(derive_result(export), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    report = verify(args.puckworks_repo)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
