#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable

MANIFEST_NAME = "SOURCE_PACKAGE_MANIFEST.json"
STRATEGY_RELATIVE = "docs/source_strategy/espresso_puck_modeling_and_simulation_strategy_v1_2.md"
PUBLIC_METADATA_TOP_LEVEL = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "AUTHORS.md",
    "CITATION.cff",
    "CLAUDE.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "FINAL_PUBLICATION_REVIEW_SUMMARY.json",
    "FINAL_PUBLICATION_REVIEW_SUMMARY.md",
    "NOTICE.md",
    "PUBLICATION_AUDIT.json",
    "PUBLICATION_AUDIT.md",
    "SECURITY.md",
    "THIRD_PARTY_NOTICES.md",
}
PUBLIC_METADATA_DIRECTORIES = {
    ".github",
    "dependencies",
    "provenance",
    "tools",
    "validation",
}
PUBLIC_DOCUMENTATION_PATHS = {
    "docs/ARCHITECTURE.md",
    "docs/CLAIM_CEILING.md",
    "docs/DEVELOPMENT_HISTORY.md",
    "docs/LICENSING.md",
    "docs/ONBOARDING.md",
    "docs/PROJECT_STATE.md",
    "docs/PUCKWORKS_INTEGRATION.md",
    "docs/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.md",
    "docs/integration/PUCKWORKS_UPDATE_IMPACT.md",
    "docs/r1/WP01R_004_PUCKWORKS_BRIDGE_AND_CASE.md",
    "docs/validation/R1_CALIBRATION_AND_COMPARISON_CONTRACT.md",
    "docs/decisions/ADR-0001-PUBLIC_REPOSITORY_TRANSITION.md",
    "docs/strategy/WHOLE_PULL_MODELING_AND_SIMULATION_STRATEGY.md",
    "docs/strategy/history/espresso_puck_modeling_and_simulation_strategy_v1_3.md",
}


def content_bytes(path: Path) -> bytes:
    if path.is_symlink():
        return os.readlink(path).encode("utf-8")
    return path.read_bytes()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(content_bytes(path))
    return digest.hexdigest()


def git_mode(path: Path) -> str:
    if path.is_symlink():
        return "120000"
    return "100755" if path.stat().st_mode & 0o111 else "100644"


def source_metadata(path: Path) -> Dict[str, object]:
    data = content_bytes(path)
    metadata: Dict[str, object] = {
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "git_mode": git_mode(path),
    }
    if path.is_symlink():
        metadata["symlink_target"] = os.readlink(path)
    return metadata


def excluded(relative: Path) -> bool:
    text = relative.as_posix()
    parts = relative.parts
    name = relative.name
    if text == MANIFEST_NAME:
        return True
    if ".git" in parts:
        return True
    # Public repository governance, CI, provenance and compact evidence
    # summaries are tracked beside the fixed 106-file solver-package scope.
    # Keep this allowlist explicit so new solver/scenario files cannot bypass
    # source-integrity review merely by being added to the public repository.
    if text in PUBLIC_METADATA_TOP_LEVEL or text in PUBLIC_DOCUMENTATION_PATHS:
        return True
    if parts and parts[0] in PUBLIC_METADATA_DIRECTORIES:
        return True
    if "__pycache__" in parts or name.endswith(".pyc"):
        return True
    if "qualification_runs" in parts:
        return True
    # qualification/ contains runtime-only reports, logs, build records, and
    # freeze-finalization products.  Exclude the directory wholesale so a
    # completed smoke or standard campaign never appears as an unmanifested
    # source change on a later replay.
    if parts and parts[0] == "qualification":
        return True
    if any(part.startswith("processor") for part in parts):
        return True
    if "postProcessing" in parts or "polyMesh" in parts or "preflight" in parts:
        return True
    if name.startswith("log.") or name.endswith(".foam"):
        return True
    if name.startswith("ESPRESSO_") and "baseline_evidence" not in parts:
        return True
    if name.startswith("RUN_ENVIRONMENT") or name.startswith("CASE_SCENARIO"):
        return True
    if name.startswith("stage_timings"):
        return True
    if "Make" in parts and any(part.startswith("linux") for part in parts):
        return True
    if name.endswith(".bak") or name.endswith("~"):
        return True
    # Generated dictionaries are recreated deterministically by prepare_case.py.
    if len(parts) >= 3 and parts[0] == "cases" and name in {
        "blockMeshDict",
        "controlDict",
        "decomposeParDict",
        "espressoModelProperties",
    }:
        return True
    # Generated initial fields use directory 0; 0.orig is the source template.
    if len(parts) >= 3 and parts[0] == "cases" and "0" in parts and "0.orig" not in parts:
        return True
    for part in parts:
        if part != "0" and part.replace(".", "", 1).isdigit():
            return True
    return False


def source_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if (path.is_file() or path.is_symlink()) and not excluded(path.relative_to(root)):
            yield path


def aggregate(entries: Dict[str, Dict[str, object]]) -> str:
    digest = hashlib.sha256()
    for relative, metadata in sorted(entries.items()):
        digest.update(
            (
                f"{relative}\0{metadata['sha256']}\0{metadata['bytes']}\0"
                f"{metadata['git_mode']}\n"
            ).encode("utf-8")
        )
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()

    files: Dict[str, Dict[str, object]] = {}
    total = 0
    for path in source_files(root):
        relative = path.relative_to(root).as_posix()
        files[relative] = source_metadata(path)
        total += int(files[relative]["bytes"])

    strategy = root / STRATEGY_RELATIVE
    if not strategy.is_file():
        raise SystemExit(f"Controlling strategy copy missing: {strategy}")
    aggregate_hash = aggregate(files)
    report = {
        "schema_version": "espresso.whole_pull.source_package_manifest.v0.1.4-public.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "package": root.name,
        "package_version": (root / "VERSION").read_text(encoding="utf-8").strip(),
        "target": "OpenFOAM Foundation 12",
        "derivation_role": "sanitized public derivative",
        "archival_aggregate_source_sha256": "182f14a036e1fc92db8f40f6025bda164ced32f108368e7aa674abd6b032508e",
        "byte_identical_to_archival_source": False,
        "governing_physics_change": False,
        "scientific_configuration_change": True,
        "scientific_configuration_change_scope": "NEW_R1_SCENARIO_ONLY",
        "qualified_R0_scientific_configuration_change": False,
        "new_R1_scientific_configuration_added": True,
        "source_manifest_self_excluded": True,
        "mode_contract": "canonical Git object modes: 100644, 100755, or 120000",
        "excluded_runtime_patterns": [
            "__pycache__/ and *.pyc",
            "qualification/ and qualification_runs/ runtime products",
            "processor*/ and postProcessing/",
            "constant/polyMesh/ and generated numeric time directories",
            "case preflight/, logs, reports, traces, status files, and *.foam",
            "Make/linux*/ build products",
            "deterministically generated case dictionaries and case/0 fields",
        ],
        "file_count": len(files),
        "total_uncompressed_bytes_excluding_manifest": total,
        "aggregate_source_sha256": aggregate_hash,
        "aggregate_sha256": aggregate_hash,
        "strategy_source_path": STRATEGY_RELATIVE,
        "strategy_source_sha256": sha256(strategy),
        "files": files,
    }
    output = root / MANIFEST_NAME
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "manifest": str(output),
                "file_count": len(files),
                "aggregate_source_sha256": aggregate_hash,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
