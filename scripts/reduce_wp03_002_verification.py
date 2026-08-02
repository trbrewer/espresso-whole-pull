#!/usr/bin/env python3
"""Reduce WP03-002 repeatability, refinement, conservation, and resources."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


FIELDS = (
    "outlet_flow_m3_s",
    "cup_beverage_mass_kg",
    "cup_water_mass_kg",
    "cup_solute_mass_kg",
    "minimumMechanicalPorosity",
    "volumeWeightedPermeabilityM2",
)


def read_rows(path: Path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def maximum_abs(rows, field):
    return max(abs(float(row[field])) for row in rows if row.get(field) not in (None, ""))


def relative(a, b):
    return abs(a - b) / max(abs(b), 1.0e-300)


def parse_time(path: Path):
    text = path.read_text()
    elapsed = re.search(r"Elapsed \(wall clock\) time .*: ([0-9:.]+)", text).group(1)
    rss = int(re.search(r"Maximum resident set size \(kbytes\): (\d+)", text).group(1))
    return {"elapsed_wall_clock": elapsed, "maximum_resident_set_kbytes": rss}


def file_sha(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_inventory(roots):
    records = []
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                records.append(
                    {"path": str(path), "bytes": path.stat().st_size, "sha256": file_sha(path)}
                )
    aggregate = hashlib.sha256()
    for record in records:
        aggregate.update(
            f"{record['path']}\0{record['bytes']}\0{record['sha256']}\n".encode()
        )
    return {
        "file_count": len(records),
        "total_bytes": sum(record["bytes"] for record in records),
        "aggregate_sha256": aggregate.hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corrected-root", type=Path, required=True)
    parser.add_argument("--reproduction-root", type=Path, required=True)
    parser.add_argument("--review-root", type=Path)
    parser.add_argument("--gate-evidence", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.review_root:
        rerun = args.review_root / "corrected-runs-v2/cases/WASZ-9-COMPACT/postProcessing/wholePull/0/traces.csv"
        verification = args.review_root / "verification-runs"
    else:
        rerun = args.corrected_root / "rerun/cases/WASZ-9-COMPACT/postProcessing/wholePull/0/traces.csv"
        verification = args.corrected_root / "verification"
    paths = {
        "mpi_dt_002": rerun,
        "serial_dt_002": verification / "cases/SERIAL-DT-002/postProcessing/wholePull/0/traces.csv",
        "mpi_dt_001": verification / "cases/MPI-DT-001/postProcessing/wholePull/0/traces.csv",
        "mpi_dt_0005": verification / "cases/MPI-DT-0005/postProcessing/wholePull/0/traces.csv",
    }
    rows = {name: read_rows(path) for name, path in paths.items()}
    final = {name: values[-1] for name, values in rows.items()}
    repeatability = {
        field: relative(float(final["serial_dt_002"][field]), float(final["mpi_dt_002"][field]))
        for field in FIELDS
    }
    refinement = {}
    for field in FIELDS:
        fine = float(final["mpi_dt_0005"][field])
        refinement[field] = {
            "dt_0p02_vs_0p005_relative": relative(float(final["mpi_dt_002"][field]), fine),
            "dt_0p01_vs_0p005_relative": relative(float(final["mpi_dt_001"][field]), fine),
        }
    conservation = {}
    for name, values in rows.items():
        conservation[name] = {
            "maximum_liquid_balance_residual_kg": maximum_abs(values, "liquid_balance_residual_kg"),
            "maximum_solute_balance_residual_kg": maximum_abs(values, "solute_balance_residual_kg"),
            "maximum_continuous_flow_closure_error": maximum_abs(values, "poroelasticFlowClosureError"),
            "maximum_discrete_nonlinear_residual": maximum_abs(values, "poroelasticNonlinearResidual"),
            "all_active_compaction_steps_converged": all(
                row["poroelasticNonlinearConverged"] == "1"
                for row in values if row["compactionActive"] == "1"
            ),
        }
    resources = {
        name: parse_time(verification / f"{case}.time")
        for name, case in (
            ("serial_dt_002", "SERIAL-DT-002"),
            ("mpi_dt_001", "MPI-DT-001"),
            ("mpi_dt_0005", "MPI-DT-0005"),
        )
    }
    result = {
        "schema_version": "espresso.wp03_002.verification.v1",
        "task": "WP03-002",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "serial_mpi_final_relative_differences": repeatability,
        "timestep_refinement": refinement,
        "conservation_and_convergence": conservation,
        "resources": resources,
        "external_artifacts": artifact_inventory(
            [args.reproduction_root, args.corrected_root]
            + (
                [
                    args.review_root / "predecessor-build",
                    args.review_root / "corrected-build",
                    args.review_root / "predecessor-runs-v2",
                    args.review_root / "corrected-runs-v2",
                    args.review_root / "verification-runs",
                    args.review_root / "gate-histories",
                ]
                if args.review_root else []
            )
        ),
        "physical_validation": "NOT_ESTABLISHED",
    }
    if args.gate_evidence:
        gate = json.loads(args.gate_evidence.read_text())
        if gate.get("status") != "PASS":
            raise RuntimeError("WP03-002 gate evidence did not pass")
        result["component_wise_nonlinear_convergence"] = gate
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
