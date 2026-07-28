#!/usr/bin/env python3
"""Prove that v0.1.4 changes release engineering, not WP-0.1 physics."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from artifact_utils import atomic_write_json, sha256_canonical_json, sha256_file  # noqa: E402

PACKAGE_VERSION = "0.1.4"
BASELINE_VERSION = "0.1.3"
DEFAULT_OUTPUT = Path(
    "cases/reference_R0_20g_58mm_9bar/preflight/"
    "NO_PHYSICS_CHANGE_VERIFICATION_V0_1_4.json"
)

VERSION_PATTERNS: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?<!\d)0\.1\.(?:3|4)(?!\d)"), "<PACKAGE_VERSION>"),
    (re.compile(r"V0_1_(?:3|4)"), "V<PACKAGE_VERSION>"),
    (re.compile(r"v0_1_(?:3|4)"), "v<PACKAGE_VERSION>"),
)

PHYSICS_KEYS = (
    "solver",
    "openfoam_distribution",
    "openfoam_version",
    "mode",
    "calibration",
    "geometry",
    "coffee_bed",
    "liquid",
    "hydraulics",
    "wetting",
    "extraction",
    "time",
    "pressure_nodes",
    "claim_ceiling",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_version_text(text: str) -> bytes:
    result = text.replace("\r\n", "\n")
    for pattern, replacement in VERSION_PATTERNS:
        result = pattern.sub(replacement, result)
    return result.encode("utf-8")


def physics_projection(document: Dict[str, Any]) -> Dict[str, Any]:
    projected = {key: document.get(key) for key in PHYSICS_KEYS}
    scenario_id = str(document.get("scenario_id", ""))
    projected["scenario_id"] = re.sub(
        r"fixture_layered_pressure_v0_1_(?:3|4)",
        "fixture_layered_pressure_v<PACKAGE_VERSION>",
        scenario_id,
    )
    return projected


def compare_normalized_text(
    root: Path, current: Path, baseline: Path, allowed: str
) -> Dict[str, Any]:
    current_normalized = normalize_version_text(current.read_text(encoding="utf-8"))
    baseline_normalized = normalize_version_text(baseline.read_text(encoding="utf-8"))
    return {
        "status": "PASS" if current_normalized == baseline_normalized else "FAIL",
        "current_path": str(current.relative_to(root)),
        "baseline_path": str(baseline.relative_to(root)),
        "current_raw_sha256": sha256_file(current),
        "baseline_raw_sha256": sha256_file(baseline),
        "current_normalized_sha256": sha256_bytes(current_normalized),
        "baseline_normalized_sha256": sha256_bytes(baseline_normalized),
        "allowed_difference": allowed,
    }


def compare_exact(root: Path, current: Path, baseline: Path) -> Dict[str, Any]:
    current_hash = sha256_file(current)
    baseline_hash = sha256_file(baseline)
    return {
        "status": "PASS" if current_hash == baseline_hash else "FAIL",
        "current_path": str(current.relative_to(root)),
        "baseline_path": str(baseline.relative_to(root)),
        "current_sha256": current_hash,
        "baseline_sha256": baseline_hash,
        "allowed_difference": "none",
    }


def compare_config(root: Path, current: Path, baseline: Path) -> Dict[str, Any]:
    current_document = json.loads(current.read_text(encoding="utf-8"))
    baseline_document = json.loads(baseline.read_text(encoding="utf-8"))
    current_projection = physics_projection(current_document)
    baseline_projection = physics_projection(baseline_document)
    current_hash = sha256_canonical_json(current_projection)
    baseline_hash = sha256_canonical_json(baseline_projection)
    return {
        "status": "PASS" if current_hash == baseline_hash else "FAIL",
        "current_path": str(current.relative_to(root)),
        "baseline_path": str(baseline.relative_to(root)),
        "current_physics_projection_sha256": current_hash,
        "baseline_physics_projection_sha256": baseline_hash,
        "physics_projection_keys": [*PHYSICS_KEYS, "scenario_id"],
        "excluded_release_only_sections": [
            "schema_version",
            "solver_version",
            "parallel.default_subdomains",
            "output.reference_artifact_version",
            "verification.bounded_state",
            "numerical_hardening",
        ],
    }


def exact_file_pairs(root: Path, baseline: Path) -> Iterable[Tuple[str, Path, Path]]:
    yield (
        "openfoam_make_files",
        root / "solver/espressoWholePullFoam/Make/files",
        baseline / "Make.files",
    )
    yield (
        "openfoam_make_options",
        root / "solver/espressoWholePullFoam/Make/options",
        baseline / "Make.options",
    )
    for label, current_base, baseline_base in (
        (
            "reference_case",
            root / "cases/reference_R0_20g_58mm_9bar",
            baseline,
        ),
        (
            "layered_fixture",
            root / "cases/fixture_layered_pressure_v0_1_4",
            baseline,
        ),
    ):
        baseline_zero = (
            baseline / "reference_case_0.orig"
            if label == "reference_case"
            else baseline / "fixture_case_0.orig"
        )
        baseline_system = (
            baseline / "reference_case_system"
            if label == "reference_case"
            else baseline / "fixture_case_system"
        )
        for path in sorted((current_base / "0.orig").iterdir()):
            if path.is_file():
                yield (
                    f"{label}_initial_field_{path.name}",
                    path,
                    baseline_zero / path.name,
                )
        for name in ("fvSchemes", "fvSolution"):
            yield (
                f"{label}_{name}",
                current_base / "system" / name,
                baseline_system / name,
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    baseline = root / "baseline_evidence/v0_1_3/source_contract"
    output = args.output or DEFAULT_OUTPUT
    output = output.resolve() if output.is_absolute() else (root / output).resolve()

    required_baseline = [
        baseline / "espressoWholePullFoam.C",
        baseline / "espresso_reference_math.py",
        baseline / "reference_R0.json",
        baseline / "fixture_layered_pressure.json",
        baseline / "Make.files",
        baseline / "Make.options",
    ]
    missing = [str(path) for path in required_baseline if not path.is_file()]
    if missing:
        raise SystemExit("Missing qualified v0.1.3 source-contract files: " + ", ".join(missing))

    comparisons: Dict[str, Dict[str, Any]] = {
        "openfoam_solver_source": compare_normalized_text(
            root,
            root / "solver/espressoWholePullFoam/espressoWholePullFoam.C",
            baseline / "espressoWholePullFoam.C",
            "displayed package version token only",
        ),
        "reduced_verification_mathematics": compare_normalized_text(
            root,
            root / "scripts/espresso_reference_math.py",
            baseline / "espresso_reference_math.py",
            "artifact/schema version tokens only",
        ),
        "reference_R0_physics_configuration": compare_config(
            root,
            root / "config/reference_R0.json",
            baseline / "reference_R0.json",
        ),
        "layered_fixture_physics_configuration": compare_config(
            root,
            root / "config/fixture_layered_pressure.json",
            baseline / "fixture_layered_pressure.json",
        ),
    }
    for name, current, predecessor in exact_file_pairs(root, baseline):
        comparisons[name] = compare_exact(root, current, predecessor)

    failed = [name for name, item in comparisons.items() if item["status"] != "PASS"]
    report = {
        "schema_version": "espresso.whole_pull.no_physics_change_verification.v0.1.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "package_version": PACKAGE_VERSION,
        "qualified_predecessor_version": BASELINE_VERSION,
        "status": "PASS" if not failed else "FAIL",
        "governing_physics_change": False if not failed else "UNRESOLVED_DIFFERENCE",
        "comparison_summary": {
            "pass": len(comparisons) - len(failed),
            "fail": len(failed),
            "total": len(comparisons),
            "failed_comparisons": failed,
        },
        "comparisons": comparisons,
        "allowed_release_changes": [
            "schema, package, scenario-fixture, and artifact version labels",
            "routine default MPI ranks from 64 to the qualified faster 32-rank setting",
            "additional acceptance/provenance/freeze-finalization gates and reports",
            "diagnostic classification, orchestration, tests, and documentation",
        ],
        "claim": (
            "PASS proves that the governing OpenFOAM source and independent reduced-twin "
            "mathematics are byte-equivalent after version-token normalization, that both "
            "scenario physics projections are identical, and that Make contracts, initial "
            "fields, and discretization dictionaries are byte-identical to qualified v0.1.3."
        ),
    }
    atomic_write_json(output, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "governing_physics_change": report["governing_physics_change"],
                "comparison_summary": report["comparison_summary"],
                "report": str(output),
            },
            indent=2,
        )
    )
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
