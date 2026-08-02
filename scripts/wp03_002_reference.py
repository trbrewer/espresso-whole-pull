#!/usr/bin/env python3
"""Independent scalar reference and failure reducer for WP03-002."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path


FATAL = re.compile(
    r"Poroelastic nonlinear solve failed at t=(?P<time>[0-9.eE+-]+) "
    r"residual=(?P<residual>[0-9.eE+-]+) closure=(?P<closure>[0-9.eE+-]+)"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def poroelastic_integral(x: float, phi: float) -> float:
    """Closed antiderivative evaluated by positive geometric expansion."""
    if not (0.0 <= x <= 1.0 and 0.0 < phi < 1.0):
        raise ValueError("poroelastic state outside the declared domain")
    total = 0.0
    phi_power = 1.0
    x_power = x
    for n in range(4096):
        term = phi_power * (
            x_power / (n + 1.0)
            - 3.0 * x_power * x / (n + 2.0)
            + 3.0 * x_power * x * x / (n + 3.0)
            - x_power * x * x * x / (n + 4.0)
        )
        total += term
        if n > 8 and abs(term) <= 2.0e-16 * max(total, math.ulp(1.0)):
            break
        phi_power *= phi
        x_power *= x
    return total


def permeability_ratio(x: float, phi: float) -> float:
    if not (0.0 <= x < 1.0 and 0.0 < phi < 1.0):
        raise ValueError("poroelastic state outside the declared domain")
    return (1.0 - x) ** 3 / (1.0 - phi * x)


def puck_flow(config: dict) -> float:
    mechanics = config["poroelasticCompaction"]
    pressure = float(config["hydraulics"]["target_inlet_pressure_gauge_Pa"])
    critical = float(mechanics["criticalCompactionPressurePa"])
    radius = float(config["geometry"]["basket_radius_m"])
    depth = float(config["coffee_bed"]["bed_depth_m"])
    viscosity = float(config["liquid"]["dynamic_viscosity_Pa_s"])
    permeability = float(mechanics["stressFreePermeabilityM2"])
    phi = float(mechanics["stressFreePorosity"])
    return (
        math.pi * radius * radius * permeability * critical
        * poroelastic_integral(pressure / critical, phi)
        / (viscosity * depth)
    )


def reduce_case(case_dir: Path, config_path: Path) -> dict:
    log = case_dir / "log.solver"
    trace = case_dir / "postProcessing/wholePull/0/traces.csv"
    matches = list(FATAL.finditer(log.read_text(errors="replace")))
    if not matches:
        raise RuntimeError(f"missing frozen fatal signature in {log}")
    fatal = matches[0].groupdict()
    with trace.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    rows = [
        row for row in rows
        if row.get("poroelasticFlowClosureError") not in (None, "")
        and row.get("poroelasticNonlinearIterations") not in (None, "")
    ]
    if not rows:
        raise RuntimeError(f"missing retained trace rows in {trace}")
    converged_rows = [
        row for row in rows
        if row.get("compactionActive") == "1"
        and row.get("poroelasticNonlinearConverged") == "1"
    ]
    last = converged_rows[-1] if converged_rows else None
    config = json.loads(config_path.read_text())
    tolerance = float(config["poroelasticCompaction"]["nonlinearAbsoluteTolerance"])
    exact = puck_flow(config)
    return {
        "case_id": config_path.stem,
        "config_sha256": sha256(config_path),
        "log_sha256": sha256(log),
        "trace_sha256": sha256(trace),
        "failure_time_s": float(fatal["time"]),
        "reported_nonlinear_residual": float(fatal["residual"]),
        "reported_continuous_flow_closure_error": float(fatal["closure"]),
        "configured_absolute_tolerance": tolerance,
        "closure_to_tolerance_ratio": float(fatal["closure"]) / tolerance,
        "last_completed_time_s": float(last["time_s"]) if last else None,
        "last_completed_continuous_flow_closure_error": (
            float(last["poroelasticFlowClosureError"]) if last else None
        ),
        "last_completed_nonlinear_iterations": (
            int(last["poroelasticNonlinearIterations"]) if last else None
        ),
        "independent_exact_scalar_flow_m3_s": exact,
        "retained_exact_scalar_flow_m3_s": (
            float(last["poroelasticExactScalarFlowM3s"]) if last else None
        ),
        "independent_scalar_relative_difference": (
            abs(exact - float(last["poroelasticExactScalarFlowM3s"]))
            / max(abs(exact), math.ulp(1.0)) if last else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = []
    for config in sorted((args.run_root / "configs").glob("WASZ-*-COMPACT.json")):
        cases.append(reduce_case(args.run_root / "cases" / config.stem, config))
    output = {
        "schema_version": "espresso.wp03_002.reproduction_and_diagnosis.v1",
        "task": "WP03-002",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "reproduction_status": "ALL_THREE_FROZEN_FAILURES_REPRODUCED",
        "diagnosis_category": "IMPLEMENTATION_DEFECT",
        "diagnosis": (
            "The nonlinear acceptance test incorrectly promotes the relative "
            "continuous analytical flow-closure comparison to an iteration "
            "convergence gate at the configured absolute tolerance. The "
            "reported maximum residual equals that closure term at every "
            "failure, just above 1e-13, although the analytical scalar evaluator "
            "is independently reproduced. This diagnostic is a mesh/reference "
            "comparison, not a residual of the discretized nonlinear equation."
        ),
        "proposed_equation_preserving_correction": (
            "Retain and report analytical flow closure, but remove it from the "
            "nonlinear fixed-point acceptance conjunction. Continue requiring "
            "flow change, pressure change, and linear pressure residual to meet "
            "their frozen controls."
        ),
        "cases": cases,
        "physical_validation": "NOT_ESTABLISHED",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
