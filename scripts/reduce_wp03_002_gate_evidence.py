#!/usr/bin/env python3
"""Fail-closed independent reducer for WP03-002 nonlinear gate telemetry."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path


PREFIX = "WP03_002_POROELASTIC_ITERATION"
REQUIRED = (
    "time",
    "iteration",
    "iterationFlow",
    "flowChange",
    "pressureChange",
    "pressureFinalResidual",
    "combinedResidual",
    "poroelasticFlowClosureError",
    "nonlinearRelativeTolerance",
    "nonlinearAbsoluteTolerance",
    "converged",
)


class GateEvidenceError(RuntimeError):
    """Telemetry cannot support a fail-closed gate decision."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def evaluate_gate(row: dict[str, object], gate: str) -> dict[str, object]:
    missing = [name for name in REQUIRED if name not in row or row[name] in (None, "")]
    if missing:
        raise GateEvidenceError(f"missing component(s): {', '.join(missing)}")
    try:
        values = {name: float(row[name]) for name in REQUIRED[:-1]}
    except (TypeError, ValueError) as exc:
        raise GateEvidenceError("nonnumeric component or tolerance") from exc
    if not all(math.isfinite(value) for value in values.values()):
        raise GateEvidenceError("nonfinite component or tolerance")
    relative = values["nonlinearRelativeTolerance"]
    absolute = values["nonlinearAbsoluteTolerance"]
    if relative <= 0.0 or absolute <= 0.0:
        raise GateEvidenceError("nonpositive tolerance")
    flow_ratio = values["flowChange"] / relative
    pressure_ratio = values["pressureChange"] / absolute
    linear_ratio = values["pressureFinalResidual"] / absolute
    closure_ratio = values["poroelasticFlowClosureError"] / absolute
    retained_ratio = max(flow_ratio, pressure_ratio, linear_ratio)
    predecessor_ratio = max(retained_ratio, closure_ratio)
    retained_residual = max(
        values["flowChange"],
        values["pressureChange"],
        values["pressureFinalResidual"],
    )
    predecessor_residual = max(
        retained_residual, values["poroelasticFlowClosureError"]
    )
    expected_residual = retained_residual if gate == "retained" else predecessor_residual
    combined = values["combinedResidual"]
    if not math.isclose(combined, expected_residual, rel_tol=5.0e-10, abs_tol=1.0e-300):
        raise GateEvidenceError(
            f"unreconstructable combined residual: {combined} != {expected_residual}"
        )
    independent = (retained_ratio if gate == "retained" else predecessor_ratio) <= 1.0
    reported_text = str(row["converged"]).lower()
    if reported_text not in ("true", "false", "1", "0"):
        raise GateEvidenceError("invalid solver convergence flag")
    reported = reported_text in ("true", "1")
    if reported != independent:
        raise GateEvidenceError(
            f"independent and solver gate disagreement: {independent} != {reported}"
        )
    if gate == "retained" and reported and retained_ratio > 1.0:
        raise GateEvidenceError("solver accepted retained_gate_ratio greater than one")
    return {
        **values,
        "solverConverged": reported,
        "flow_ratio": flow_ratio,
        "pressure_ratio": pressure_ratio,
        "linear_ratio": linear_ratio,
        "closure_ratio": closure_ratio,
        "retained_gate_ratio": retained_ratio,
        "predecessor_gate_ratio": predecessor_ratio,
        "independentConverged": independent,
    }


def parse_log(path: Path, gate: str) -> list[dict[str, object]]:
    records = []
    for line_number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if PREFIX not in line:
            continue
        payload = line.split(PREFIX, 1)[1]
        fields = dict(re.findall(r"([A-Za-z][A-Za-z0-9]*)=([^ ]+)", payload))
        try:
            record = evaluate_gate(fields, gate)
        except GateEvidenceError as exc:
            raise GateEvidenceError(f"{path}:{line_number}: {exc}") from exc
        record["line"] = line_number
        records.append(record)
    if not records:
        raise GateEvidenceError(f"missing iteration telemetry: {path}")
    return records


def reduce_case(path: Path, gate: str, history_path: Path) -> dict[str, object]:
    records = parse_log(path, gate)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(records[0])
    with history_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    accepted = [row for row in records if row["solverConverged"]]
    retained_pass = [row for row in records if row["retained_gate_ratio"] <= 1.0]
    maxima = {
        name: max(float(row[name]) for row in records)
        for name in (
            "flowChange",
            "pressureChange",
            "pressureFinalResidual",
            "poroelasticFlowClosureError",
            "flow_ratio",
            "pressure_ratio",
            "linear_ratio",
            "closure_ratio",
        )
    }
    return {
        "log_sha256": sha256(path),
        "iteration_count": len(records),
        "accepted_iteration_count": len(accepted),
        "component_maxima": maxima,
        "accepted_component_maxima": {
            name: max((float(row[name]) for row in accepted), default=None)
            for name in (
                "flowChange",
                "pressureChange",
                "pressureFinalResidual",
                "poroelasticFlowClosureError",
                "flow_ratio",
                "pressure_ratio",
                "linear_ratio",
                "closure_ratio",
            )
        },
        "retained_gate_passing_iteration_count": len(retained_pass),
        "minimum_closure_ratio_at_retained_gate_pass": min(
            (float(row["closure_ratio"]) for row in retained_pass), default=None
        ),
        "maximum_closure_ratio_at_retained_gate_pass": max(
            (float(row["closure_ratio"]) for row in retained_pass), default=None
        ),
        "maximum_accepted_retained_gate_ratio": max(
            (float(row["retained_gate_ratio"]) for row in accepted), default=None
        ),
        "maximum_accepted_predecessor_gate_ratio": max(
            (float(row["predecessor_gate_ratio"]) for row in accepted), default=None
        ),
        "history_sha256": sha256(history_path),
        "history_rows": len(records),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predecessor-root", type=Path, required=True)
    parser.add_argument("--corrected-root", type=Path, required=True)
    parser.add_argument("--history-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases: dict[str, object] = {}
    for case_id in ("WASZ-5-COMPACT", "WASZ-9-COMPACT", "WASZ-11-COMPACT"):
        cases[case_id] = {
            "predecessor": reduce_case(
                args.predecessor_root / "cases" / case_id / "log.solver",
                "predecessor",
                args.history_root / "predecessor" / f"{case_id}.csv",
            ),
            "corrected": reduce_case(
                args.corrected_root / "cases" / case_id / "log.solver",
                "retained",
                args.history_root / "corrected" / f"{case_id}.csv",
            ),
        }
    corrected = [entry["corrected"] for entry in cases.values()]
    result = {
        "schema_version": "espresso.wp03_002.gate_evidence.v1",
        "task": "WP03-002",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "status": "PASS",
        "independent_reduction": "PASS_FAIL_CLOSED",
        "cases": cases,
        "maximum_accepted_retained_gate_ratio": max(
            float(entry["maximum_accepted_retained_gate_ratio"])
            for entry in corrected
        ),
        "physical_validation": "NOT_ESTABLISHED",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
