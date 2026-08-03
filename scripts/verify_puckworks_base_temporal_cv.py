#!/usr/bin/env python3
"""Verify the bounded Puckworks BASE temporal-CV evidence import."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


UPSTREAM_COMMIT = "21869fe19feec2dce6af8f4a41f63299473e31c2"
REQUIRED_LINEAGE = {
    "evidence_class": "POST_FIT_DERIVED_FROM_FITTED_KINETICS",
    "independent_measurement": False,
    "allowed_use": "SOURCE_LINEAGE_RECONSTRUCTION_OR_DERIVED_METRIC_ONLY",
    "prohibited_use": "INDEPENDENT_VALIDATION_TARGET",
    "required_citation": "docs/validation/VAL_PUCKWORKS_001_BASE_TEMPORAL_CROSS_VALIDATION_AND_CUP_MASS_LINEAGE.md",
}
EXPECTED_METRICS = {
    "caffeine": (6.773723008023561, 9.956192697201004, 1.5553653242809058, 2.2230231547476897),
    "trigonelline": (10.298791345087212, 15.158854455498721, -3.4686832418065188, 3.1662156395611976),
    "5CQA": (7.196408617674486, 10.016456716398794, 1.3445947506081093, 2.8110375983062417),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def contains_lineage(value: object) -> bool:
    if isinstance(value, dict):
        if all(value.get(key) == expected for key, expected in REQUIRED_LINEAGE.items()):
            return True
        return any(contains_lineage(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_lineage(item) for item in value)
    return False


def verify(root: Path) -> dict:
    root = root.resolve()
    local = root / "validation/external/puckworks_base_temporal_cv"
    document_path = root / "docs/validation/VAL_PUCKWORKS_001_BASE_TEMPORAL_CROSS_VALIDATION_AND_CUP_MASS_LINEAGE.md"
    record = json.loads((local / "PUCKWORKS_BASE_TEMPORAL_CV_SOURCE_RECORD.json").read_text())
    failures: list[str] = []
    if record.get("upstream_commit") != UPSTREAM_COMMIT:
        failures.append("upstream commit mismatch")
    for artifact in record.get("artifacts", []):
        path = root / artifact["local_path"]
        observed = sha256(path) if path.is_file() else None
        if (observed != artifact["upstream_sha256"] or observed != artifact["local_sha256"]
                or artifact.get("byte_identity") is not True):
            failures.append(f"artifact identity mismatch: {artifact['local_path']}")

    comparison = json.loads((local / "PAPER_A_TEMPORAL_MODEL_COMPARISON_V1.json").read_text())
    for solute, expected in EXPECTED_METRICS.items():
        base = comparison["solutes"][solute]["BASE"]
        observed = (base["all_fraction_mape"], base["late_fraction_mape"],
                    base["late_signed_pct"], base["derived_cumulative_mape"])
        if observed != expected or base["n_folds"] != 5 or base["failed_fits"] != 0:
            failures.append(f"BASE aggregate mismatch: {solute}")
        kappas = base["parameter_stability"]["kappa"]
        if kappas != [1.053357520264539] * 5:
            failures.append(f"BASE kappa mismatch: {solute}")

    manifest = json.loads((local / "PAPER_A_TEMPORAL_MATCHED_DATA_MANIFEST_V1.json").read_text())
    if (manifest["experiments"] != [1.0, 2.0, 5.0, 6.0, 7.0]
            or len(manifest["shots"]) != 16 or manifest["n_shots"] != 16
            or manifest["measured_fractions"] != [1, 2, 3, 5, 7, 10]
            or manifest["late_fractions"] != [7, 10]
            or manifest["n_excluded_overall"] != 3 or len(manifest["exclusions"]) != 3):
        failures.append("matched-data count or exclusion mismatch")

    lineage = json.loads((local / "PAPER_A_CUP_TARGET_LINEAGE_AUDIT_V1.json").read_text())
    if (lineage["rows_reproduced"] != 432 or lineage["rows_within_0p01pct"] != 427
            or lineage["median_rel_error_pct"] != 3.2238843694444866e-05
            or lineage["conc_in_cup_equals_mass_over_M_mismatches"] != 0
            or lineage["deviation_cause"]["deviating_rows_total"] != 5):
        failures.append("cup-mass lineage audit mismatch")
    if record.get("cup_masses_csv_lineage") != REQUIRED_LINEAGE:
        failures.append("structured cup-mass lineage declaration mismatch")

    document = document_path.read_text()
    required_document_text = [
        "CROSS_REPOSITORY_SUPPORTING_EXTRACTION_EVIDENCE",
        "LEAVE_ONE_EXPERIMENT_OUT_WITHIN_ONE_SOURCE_CAMPAIGN",
        "GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION: NOT_ESTABLISHED",
        "cup_masses.csv` contains quantities derived from each replicate's fitted",
        "mass_in_cup(M) = c0 * lambda * (1 - exp(-M/lambda))",
        "concentration_in_cup(M) = mass_in_cup(M) / M",
        "## Standing instruction for future validation work",
    ]
    for expected in required_document_text:
        if expected not in document:
            failures.append(f"persistent document omission: {expected}")
    for values in EXPECTED_METRICS.values():
        for value in values:
            if repr(value) not in document:
                failures.append(f"persistent document metric mismatch: {value!r}")

    exempt = {artifact["local_path"] for artifact in record["artifacts"]}
    for path in root.rglob("*.json"):
        relative = path.relative_to(root).as_posix()
        if relative in exempt or relative == "SOURCE_PACKAGE_MANIFEST.json":
            continue
        text = path.read_text(errors="replace")
        if "cup_masses.csv" not in text:
            continue
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            failures.append(f"unparseable governed cup-mass reference: {relative}")
            continue
        if not contains_lineage(value):
            failures.append(f"cup-mass reference lacks mandatory lineage declaration: {relative}")

    return {
        "schema_version": "espresso.verify.puckworks_base_temporal_cv.v1",
        "status": "PASS" if not failures else "FAIL",
        "upstream_commit": UPSTREAM_COMMIT,
        "artifact_count": len(record["artifacts"]),
        "base_solute_count": len(EXPECTED_METRICS),
        "fold_count": 5,
        "experiment_count": len(manifest["experiments"]),
        "shot_count": len(manifest["shots"]),
        "exclusion_count": len(manifest["exclusions"]),
        "lineage_rows_checked": lineage["rows_reproduced"],
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.root)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
