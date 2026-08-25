#!/usr/bin/env python3
"""Independent fail-closed verification of the SCI-MD-007 thin handoff."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "docs/validation/sci_md_007"
PASS = "SCI_MD_007_INVENTORY_PREDICTION_FEASIBLE_WITH_EXISTING_EVIDENCE"
FAIL = "SCI_MD_007_INVENTORY_PRIOR_ONLY_ADDITIONAL_DIRECT_MEASUREMENTS_REQUIRED"


def verify():
    lock = json.loads((HERE / "PUCKWORKS_LOCK.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
    failures = []
    expected = result["caffeine_feasible"] and result["trigonelline_feasible"] and result["paired_gate_F5"]
    disposition = PASS if expected else FAIL
    checks = {
        "repository": lock["repository"] == "https://github.com/trbrewer/puckworks.git",
        "git_identity": len(lock["commit"]) == 40 and len(lock["tree"]) == 40,
        "hash_identity": len(lock["export_sha256"]) == 64 and len(lock["source_package_manifest_sha256"]) == 64,
        "schema": lock["result_schema_version"] == "1.0.0" and result["task_id"] == "SCI-MD-007",
        "boolean_reduction": result["overall_feasible"] is expected and result["scientific_disposition"] == disposition,
        "compound_gates_preserved": all(set(v) == {"F0", "F1", "F2", "F3", "F4", "F6", "F7"} for v in result["compound_gate_results"].values()),
        "fail_disables_predictor": disposition != FAIL or (result["inventory_predictor_activation"] == "NOT_AUTHORIZED" and result["model_stage"] == "NOT_RUN_FEASIBILITY_FAILED"),
        "total_not_extractable": result["extractable_inventory_mapping_status"] != "DIRECTLY_SUPPORTED",
        "claim_ceiling": result["physical_validation"] == "NOT_ESTABLISHED" and result["change_declaration"] == "NO_GOVERNING_PHYSICS_CHANGE",
        "exclusions": result["angeloni_reuse"] is False and result["sci_md_006_reopened"] is False,
        "no_absolute_paths": "/home/" not in json.dumps({"lock": lock, "result": result}),
    }
    failures.extend(name for name, ok in checks.items() if not ok)
    return {"schema_version": "espresso.sci_md_007.verification.v1", "status": "PASS" if not failures else "FAIL", "checks": checks, "failures": failures}


if __name__ == "__main__":
    report = verify()
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)
