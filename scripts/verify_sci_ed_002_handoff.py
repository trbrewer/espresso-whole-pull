"""Verify the fail-closed SCI-ED-002 producer lock and consumer claim ceiling."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "docs" / "validation" / "sci_ed_002"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(producer_root: Path | None = None, mutation: str | None = None) -> dict:
    lock = json.loads((HERE / "PUCKWORKS_AUTHORITY.json").read_text())
    export = json.loads((HERE / "SCI_ED_002_EXPORT.json").read_text())
    if mutation == "commit": export["candidate_commit"] = "0" * 40
    elif mutation == "tree": export["candidate_tree"] = "0" * 40
    elif mutation == "commissioning": export["claim_ceiling"]["commissioning_authorized"] = True
    elif mutation == "c_s0": export["claim_ceiling"]["c_s0_mapping_status"] = "ESTABLISHED"
    elif mutation == "predictor": export["claim_ceiling"]["predictor_eligible"] = True
    elif mutation == "holdout": export["holdout_status"] = "OPEN"
    assert export["candidate_commit"] == lock["producer_commit"], "PRODUCER_COMMIT_MISMATCH"
    assert export["candidate_tree"] == lock["producer_tree"], "PRODUCER_TREE_MISMATCH"
    assert export["claim_ceiling"]["commissioning_authorized"] is False, "COMMISSIONING_STATUS_WEAKENED"
    assert export["claim_ceiling"]["c_s0_mapping_status"] == "NOT_ESTABLISHED", "C_S0_STATUS_WEAKENED"
    assert export["claim_ceiling"]["predictor_eligible"] is False, "PREDICTOR_ELIGIBILITY_WEAKENED"
    assert export["holdout_status"] == "SEALED_NOT_ACCESSED", "HOLDOUT_STATUS_WEAKENED"
    if producer_root:
        producer_root = producer_root.resolve()
        actual_commit = subprocess.check_output(["git", "-C", str(producer_root), "rev-parse", lock["producer_commit"]], text=True).strip()
        actual_tree = subprocess.check_output(["git", "-C", str(producer_root), "rev-parse", f"{lock['producer_commit']}^{{tree}}"], text=True).strip()
        assert actual_commit == lock["producer_commit"], "PRODUCER_COMMIT_UNAVAILABLE"
        assert actual_tree == lock["producer_tree"], "PRODUCER_TREE_MISMATCH"
        source_export = producer_root / "docs" / "analysis" / "sci_ed_002" / "SCI_ED_002_EXPORT.json"
        assert digest(source_export) == lock["producer_export_sha256"], "PRODUCER_EXPORT_HASH_MISMATCH"
        source = json.loads(source_export.read_text())
        assert source == export, "VENDORED_EXPORT_SEMANTIC_MISMATCH"
        for name, expected in export["schema_sha256"].items():
            path = producer_root / "docs" / "analysis" / "sci_ed_002" / "schemas" / "1.0.0" / f"{name}.schema.json"
            assert digest(path) == expected, f"SCHEMA_HASH_MISMATCH:{name}"
    return {"status": "SCI_ED_002_HANDOFF_VERIFIED", "no_physics_change": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--producer-root", type=Path)
    args = parser.parse_args()
    try: result = verify(args.producer_root)
    except (AssertionError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
