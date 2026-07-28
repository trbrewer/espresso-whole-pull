#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict

from generate_source_manifest import excluded


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate(entries: Dict[str, Dict[str, object]]) -> str:
    digest = hashlib.sha256()
    for relative, metadata in sorted(entries.items()):
        digest.update(
            (
                f"{relative}\0{metadata['sha256']}\0{metadata['bytes']}\0"
                f"{metadata['mode']}\n"
            ).encode("utf-8")
        )
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = root / "SOURCE_PACKAGE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    failures = []
    expected_paths = set(manifest["files"])
    actual_source_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not excluded(path.relative_to(root))
    }
    for relative in sorted(actual_source_paths - expected_paths):
        failures.append({"path": relative, "issue": "unmanifested_source_file"})
    for relative in sorted(expected_paths - actual_source_paths):
        failures.append({"path": relative, "issue": "manifested_source_file_missing"})

    observed: Dict[str, Dict[str, object]] = {}
    for relative, expected in manifest["files"].items():
        path = root / relative
        if not path.is_file():
            failures.append({"path": relative, "issue": "missing"})
            continue
        actual = {
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "mode": format(path.stat().st_mode & 0o777, "04o"),
        }
        observed[relative] = actual
        if actual != expected:
            failures.append(
                {
                    "path": relative,
                    "issue": "metadata_mismatch",
                    "expected": expected,
                    "actual": actual,
                }
            )

    observed_aggregate = aggregate(observed) if len(observed) == len(manifest["files"]) else None
    expected_aggregate = manifest["aggregate_source_sha256"]
    if observed_aggregate != expected_aggregate:
        failures.append(
            {
                "path": "aggregate_source_sha256",
                "issue": "mismatch",
                "expected": expected_aggregate,
                "actual": observed_aggregate,
            }
        )

    report = {
        "schema_version": "espresso.whole_pull.source_manifest_verification.v0.1.4",
        "status": "PASS" if not failures else "FAIL",
        "checked_files": len(manifest["files"]),
        "observed_source_file_count": len(actual_source_paths),
        "aggregate_source_sha256": expected_aggregate,
        "failures": failures,
    }
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
