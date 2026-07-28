#!/usr/bin/env python3
"""Normalize future-dated build inputs before invoking OpenFOAM wmake.

ZIP extraction can restore local wall-clock timestamps that are ahead of the
host clock. GNU make/wmkdep then sees a prerequisite that can never become
older than its dependency target and may regenerate dependencies indefinitely.
This utility repairs only package build inputs and records every change.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

PACKAGE_VERSION = "0.1.4"


def utc_iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--future-tolerance-s", type=float, default=5.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    solver = root / "solver/espressoWholePullFoam"
    output = args.output or (
        root
        / "cases/reference_R0_20g_58mm_9bar/preflight/"
        "TIMESTAMP_NORMALIZATION_V0_1_4.json"
    )
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)

    now = time.time()
    tolerance = max(float(args.future_tolerance_s), 0.0)
    candidates: List[Path] = []
    for path in sorted(solver.rglob("*")):
        if not path.is_file():
            continue
        # Generated wmake object/dependency trees are removed separately.
        if any(part.startswith("linux") for part in path.parts if part != path.name):
            continue
        candidates.append(path)

    normalized: List[Dict[str, object]] = []
    maximum_future_offset = 0.0
    for path in candidates:
        stat = path.stat()
        future_offset = stat.st_mtime - now
        maximum_future_offset = max(maximum_future_offset, future_offset)
        if future_offset > tolerance:
            os.utime(path, (now, now))
            normalized.append(
                {
                    "path": str(path.relative_to(root)),
                    "previous_mtime_utc": utc_iso(stat.st_mtime),
                    "previous_future_offset_s": future_offset,
                    "normalized_mtime_utc": utc_iso(now),
                }
            )

    removed_build_directories: List[str] = []
    make_dir = solver / "Make"
    if normalized and make_dir.is_dir():
        for path in sorted(make_dir.glob("linux*")):
            if path.is_dir():
                shutil.rmtree(path)
                removed_build_directories.append(str(path.relative_to(root)))
            elif path.exists():
                path.unlink()
                removed_build_directories.append(str(path.relative_to(root)))

    report = {
        "schema_version": "espresso.whole_pull.timestamp_normalization.v0.1.4",
        "package_version": PACKAGE_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "host_epoch_s": now,
        "future_tolerance_s": tolerance,
        "scanned_file_count": len(candidates),
        "normalized_file_count": len(normalized),
        "maximum_observed_future_offset_s": maximum_future_offset,
        "normalized_files": normalized,
        "removed_stale_build_directories": removed_build_directories,
        "status": "PASS",
        "note": (
            "Content bytes are unchanged. Only filesystem modification times "
            "of future-dated solver build inputs are normalized."
        ),
    }
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
