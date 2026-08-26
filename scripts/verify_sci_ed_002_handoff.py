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


def git_bytes(root: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{path}"])


def verify(producer_root: Path | None = None, mutation: str | None = None) -> dict:
    lock = json.loads((HERE / "PUCKWORKS_AUTHORITY.json").read_text())
    export = json.loads((HERE / "SCI_ED_002_EXPORT.json").read_text())
    if mutation == "commit":
        lock["producer_commit"] = lock["scientific_content_commit"]
        lock["authority_model"] = "INTERMEDIATE"
    elif mutation == "tree": lock["producer_tree"] = "0" * 40
    elif mutation == "export": export["schema_version"] = "MUTATED"
    elif mutation == "schema": lock["schema_version"] = "MUTATED"
    elif mutation == "commissioning": export["claim_ceiling"]["commissioning_authorized"] = True
    elif mutation == "c_s0": export["claim_ceiling"]["c_s0_mapping_status"] = "ESTABLISHED"
    elif mutation == "predictor": export["claim_ceiling"]["predictor_eligible"] = True
    elif mutation == "holdout": export["holdout_status"] = "OPEN"
    assert lock["authority_model"] == "FINAL_PACKAGE_HEAD", "INTERMEDIATE_COMMIT_SUBSTITUTED_FOR_FINAL_HEAD"
    assert lock["producer_tree"] == "33c9d603760163842caa86aa932053ca44b120f8", "PRODUCER_TREE_MISMATCH"
    assert lock["schema_version"] == export["schema_version"], "SCHEMA_HASH_MISMATCH"
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
        export_bytes = git_bytes(producer_root, lock["producer_commit"], lock["producer_export_path"])
        assert hashlib.sha256(export_bytes).hexdigest() == lock["producer_export_sha256"], "PRODUCER_EXPORT_HASH_MISMATCH"
        assert export_bytes == (HERE / "SCI_ED_002_EXPORT.json").read_bytes(), "VENDORED_EXPORT_BYTE_MISMATCH"
        source = json.loads(export_bytes)
        assert source == export, "VENDORED_EXPORT_SEMANTIC_MISMATCH"
        for name, expected in export["schema_sha256"].items():
            data = git_bytes(producer_root, lock["producer_commit"], f"docs/analysis/sci_ed_002/schemas/1.0.0/{name}.schema.json")
            assert hashlib.sha256(data).hexdigest() == expected, f"SCHEMA_HASH_MISMATCH:{name}"
        manifest = git_bytes(producer_root, lock["producer_commit"], lock["producer_source_manifest_path"])
        assert hashlib.sha256(manifest).hexdigest() == lock["producer_source_manifest_sha256"], "SOURCE_MANIFEST_MISMATCH"
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
