#!/usr/bin/env python3
"""Record source, build environment, exact runtime binary, and a portable archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

PACKAGE_VERSION = "0.1.4"
DEFAULT_OUTPUT = Path(
    "cases/reference_R0_20g_58mm_9bar/preflight/BUILD_PROVENANCE_V0_1_4.json"
)
DEFAULT_ARCHIVE = Path(
    "cases/reference_R0_20g_58mm_9bar/preflight/espressoWholePullFoam_v0_1_4"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative_record(path: Path, root: Path) -> Dict[str, object]:
    resolved = path.resolve()
    try:
        recorded_path = str(resolved.relative_to(root.resolve()))
        package_relative = True
    except ValueError:
        # Supported for isolated build-script tests and custom diagnostics.  The
        # production freeze contract separately requires the canonical archived
        # executable inside the package preflight directory.
        recorded_path = str(resolved)
        package_relative = False
    return {
        "path": recorded_path,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "executable": os.access(path, os.X_OK),
        "package_relative": package_relative,
    }


def runtime_record(path: Path) -> Dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "executable": os.access(path, os.X_OK),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--archive-executable", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--purpose", default="reference_Allrun")
    args = parser.parse_args()

    root = args.root.resolve()
    executable = args.executable.resolve()
    if not executable.is_file():
        raise SystemExit(f"Built executable not found: {executable}")
    if not os.access(executable, os.X_OK):
        raise SystemExit(f"Built solver is not executable: {executable}")

    output = args.output if args.output.is_absolute() else root / args.output
    archive = (
        args.archive_executable
        if args.archive_executable.is_absolute()
        else root / args.archive_executable
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    archive.parent.mkdir(parents=True, exist_ok=True)

    inputs = [
        root / "solver/espressoWholePullFoam/espressoWholePullFoam.C",
        root / "solver/espressoWholePullFoam/Make/files",
        root / "solver/espressoWholePullFoam/Make/options",
    ]
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise SystemExit("Missing build input(s): " + ", ".join(missing))

    if archive.resolve() != executable:
        temporary_archive = archive.with_name(archive.name + ".tmp")
        shutil.copyfile(executable, temporary_archive)
        temporary_archive.chmod(0o755)
        temporary_archive.replace(archive)
    else:
        archive.chmod(0o755)

    runtime = runtime_record(executable)
    archived = relative_record(archive, root)
    if runtime["sha256"] != archived["sha256"] or runtime["bytes"] != archived["bytes"]:
        raise SystemExit("Archived solver executable does not match the runtime executable")

    environment_names = (
        "WM_PROJECT",
        "WM_PROJECT_VERSION",
        "WM_OPTIONS",
        "WM_ARCH",
        "WM_COMPILER",
        "WM_COMPILE_OPTION",
        "WM_LABEL_SIZE",
        "WM_PRECISION_OPTION",
        "WM_MPLIB",
        "WM_PROJECT_DIR",
        "FOAM_SRC",
        "FOAM_USER_APPBIN",
    )
    build_inputs = [relative_record(path, root) for path in inputs]
    report = {
        "schema_version": "espresso.whole_pull.build_provenance.v0.1.4",
        "package_version": PACKAGE_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "build_purpose": args.purpose,
        "host": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "environment": {
            name: os.environ.get(name)
            for name in environment_names
            if os.environ.get(name) not in (None, "")
        },
        "build_inputs": build_inputs,
        # `executable` is retained for backward-compatible standard-Allverify
        # verification. `archived_executable` makes the frozen record portable.
        "executable": runtime,
        "runtime_executable": runtime,
        "archived_executable": archived,
        "status": "PASS",
    }
    source_bundle = hashlib.sha256()
    for item in build_inputs:
        source_bundle.update(str(item["path"]).encode("utf-8"))
        source_bundle.update(b"\0")
        source_bundle.update(str(item["sha256"]).encode("ascii"))
        source_bundle.update(b"\n")
    report["source_bundle_sha256"] = source_bundle.hexdigest()

    combined = hashlib.sha256()
    combined.update(report["source_bundle_sha256"].encode("ascii"))
    combined.update(b"\0")
    combined.update(str(runtime["sha256"]).encode("ascii"))
    report["source_and_executable_bundle_sha256"] = combined.hexdigest()
    report["runtime_archive_identity"] = {
        "status": "PASS",
        "runtime_sha256": runtime["sha256"],
        "archived_sha256": archived["sha256"],
        "same_bytes": True,
    }

    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
