#!/usr/bin/env python3
"""Verify immutable v0.1.4 baseline identities without classifying active physics."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED = {
    "config/reference_R0.json": "67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286",
    "config/fixture_layered_pressure.json": "7db882f59da51d5e1501b54edebef465d2644cfe1dc5368deb0a46e6a05c512b",
    "validation/baselines/v0.1.4/PUBLIC_BASELINE_SUMMARY.json": "27f256c5d726913fd69d9020d61027e276d7b4b18cf487240627a66de508fa09",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path) -> dict:
    checks = {
        path: {
            "expected_sha256": expected,
            "observed_sha256": digest(root / path) if (root / path).is_file() else None,
        }
        for path, expected in EXPECTED.items()
    }
    for item in checks.values():
        item["status"] = (
            "PASS" if item["observed_sha256"] == item["expected_sha256"] else "FAIL"
        )
    summary = json.loads(
        (root / "validation/baselines/v0.1.4/PUBLIC_BASELINE_SUMMARY.json").read_text()
    )
    semantic = {
        "reference_status": summary.get("reference_status") == "FROZEN / QUALIFIED",
        "physical_validation": summary.get("physical_validation_status")
        == "NOT_ESTABLISHED",
        "governing_physics_change": summary.get("governing_physics_change") is False,
        "scientific_input_aggregate": summary.get(
            "scientific_input_aggregate_sha256"
        )
        == "d70399a76b0023d93985d76c1c83a9a42b7148b3d71d16d1b5f88275be1ebe7a",
        "historical_no_physics_verifier_present": (
            root / "scripts/verify_no_physics_change.py"
        ).is_file(),
    }
    passed = all(x["status"] == "PASS" for x in checks.values()) and all(
        semantic.values()
    )
    return {
        "schema_version": "espresso.whole_pull.v0_1_4_baseline_integrity.v1",
        "status": "PASS" if passed else "FAIL",
        "baseline": "v0.1.4-public.1",
        "checks": checks,
        "semantic_checks": semantic,
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
