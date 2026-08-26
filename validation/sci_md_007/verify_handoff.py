#!/usr/bin/env python3
"""Exact-byte, fail-closed verification of the SCI-MD-007-R1 handoff."""

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


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=False
    )


def derive_result(export: dict) -> dict:
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
    if (
        export["task_id"],
        export["schema_version"],
        export["evidence_cutoff_date"],
    ) != ("SCI-MD-007", "1.1.0-R1", "2026-08-25"):
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
        "schema_version": "espresso.sci_md_007.handoff.v2",
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
        checks["lock_schema"] = (
            lock["schema_version"] == "espresso.sci_md_007.puckworks_lock.v2"
        )
        checks["repository_identity"] = (
            lock["repository"] == "https://github.com/trbrewer/puckworks.git"
        )
        export = json.loads(export_bytes)
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
            upstream_export = _git(
                repo, "show", f"{lock['commit']}:{lock['export_path']}"
            )
            upstream_manifest = _git(
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
                and upstream_export.stdout.encode() == export_bytes
            )
            checks["cross_repository_manifest"] = (
                upstream_manifest.returncode == 0
                and upstream_manifest.stdout.encode() == manifest_bytes
            )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, OSError) as exc:
        failures.append(f"exception:{type(exc).__name__}:{exc}")
    failures.extend(name for name, ok in checks.items() if not ok)
    return {
        "schema_version": "espresso.sci_md_007.verification.v2",
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
