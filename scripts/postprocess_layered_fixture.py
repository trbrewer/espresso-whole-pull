#!/usr/bin/env python3
"""Accept the nonuniform layered-permeability pressure-solver fixture."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from espresso_reference_math import discrete_layered_pressure_reference  # noqa: E402

STEM = "ESPRESSO_LAYERED_PRESSURE_FIXTURE"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def gate(status: bool, metric: object, limit: str, details: str = "") -> Dict[str, object]:
    return {
        "status": "PASS" if status else "FAIL",
        "metric": metric,
        "limit": limit,
        "details": details,
    }


def relative_error(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), 1.0e-30)


def resolve(root: Path, value: Optional[Path], default: Path) -> Path:
    selected = value if value is not None else default
    return selected.resolve() if selected.is_absolute() else (root / selected).resolve()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--case-dir", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    config_path = resolve(root, args.config, Path("config/fixture_layered_pressure.json"))
    case = resolve(root, args.case_dir, Path("cases/fixture_layered_pressure_v0_1_4"))
    scenario = json.loads(config_path.read_text(encoding="utf-8"))
    trace_path = case / "postProcessing/wholePull/0/traces.csv"
    if not trace_path.is_file():
        raise SystemExit(f"Missing fixture trace: {trace_path}")

    with trace_path.open(newline="", encoding="utf-8") as stream:
        rows: List[Dict[str, float]] = [
            {key: float(value) for key, value in row.items() if key is not None and value is not None}
            for row in csv.DictReader(stream)
        ]
    if not rows:
        raise SystemExit("Layered fixture trace is empty")
    final = rows[-1]
    exact = discrete_layered_pressure_reference(scenario)
    expected_probes = exact["pressure_probe_values_pa"]
    verification = scenario["verification"]

    flow_error = relative_error(final["outlet_flow_m3_s"], exact["outlet_flow_m3_s"])
    probe1_error = abs(final["pressure_probe_1_Pa"] - expected_probes[0])
    probe2_error = abs(final["pressure_probe_2_Pa"] - expected_probes[1])
    max_iterations = max(row["pressure_iterations"] for row in rows)
    finite = all(math.isfinite(value) for row in rows for value in row.values())
    gates = {
        "simulation_reached_end_time": gate(
            abs(final["time_s"] - float(scenario["time"]["end_s"]))
            <= 1.01 * float(scenario["time"]["delta_t_s"]),
            final["time_s"],
            f"within one time step of {scenario['time']['end_s']} s",
        ),
        "all_trace_values_finite": gate(finite, finite, "true"),
        "nonzero_pressure_iterations": gate(
            max_iterations > 0,
            max_iterations,
            "> 0 for at least one solve",
            "The fixture deliberately starts from an incompatible zero field and uses two permeability layers.",
        ),
        "exact_discrete_outlet_flow": gate(
            flow_error <= float(verification["discrete_flow_relative_tolerance"]),
            {
                "actual_m3_s": final["outlet_flow_m3_s"],
                "expected_m3_s": exact["outlet_flow_m3_s"],
                "relative_error": flow_error,
            },
            f"relative error <= {verification['discrete_flow_relative_tolerance']}",
        ),
        "quarter_depth_pressure": gate(
            probe1_error <= float(verification["pressure_probe_absolute_tolerance_Pa"]),
            {
                "actual_Pa": final["pressure_probe_1_Pa"],
                "expected_Pa": expected_probes[0],
                "absolute_error_Pa": probe1_error,
            },
            f"absolute error <= {verification['pressure_probe_absolute_tolerance_Pa']} Pa",
        ),
        "three_quarter_depth_pressure": gate(
            probe2_error <= float(verification["pressure_probe_absolute_tolerance_Pa"]),
            {
                "actual_Pa": final["pressure_probe_2_Pa"],
                "expected_Pa": expected_probes[1],
                "absolute_error_Pa": probe2_error,
            },
            f"absolute error <= {verification['pressure_probe_absolute_tolerance_Pa']} Pa",
        ),
        "straight_sided_wedge_volume_equivalence": gate(
            abs(final["mesh_volume_relative_error"])
            <= float(verification["wedge_volume_relative_tolerance"]),
            final["mesh_volume_relative_error"],
            f"relative error <= {verification['wedge_volume_relative_tolerance']}",
        ),
        "liquid_conservation": gate(
            max(abs(row["liquid_balance_residual_kg"]) for row in rows) <= 1.0e-10,
            max(abs(row["liquid_balance_residual_kg"]) for row in rows),
            "<= 1e-10 kg",
        ),
    }
    passed = all(item["status"] == "PASS" for item in gates.values())
    output = case / f"{STEM}_ACCEPTANCE_V0_1_4.json"
    report = {
        "schema_version": "espresso.whole_pull.layered_pressure_acceptance.v0.1.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenario_id": scenario["scenario_id"],
        "status": "PASS" if passed else "FAIL",
        "execution_status": "COMPLETED",
        "all_required_gates_pass": passed,
        "gates": gates,
        "exact_discrete_reference": exact,
        "primary_outputs": {
            "outlet_flow_m3_s": final["outlet_flow_m3_s"],
            "pressure_probe_1_Pa": final["pressure_probe_1_Pa"],
            "pressure_probe_2_Pa": final["pressure_probe_2_Pa"],
            "max_pressure_iterations": max_iterations,
            "max_pressure_final_residual": max(abs(row["pressure_final_residual"]) for row in rows),
        },
        "claim_ceiling": scenario["claim_ceiling"],
        "trace": {
            "path": str(trace_path.relative_to(case)),
            "bytes": trace_path.stat().st_size,
            "sha256": sha256(trace_path),
        },
    }
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    (case / "layered_pressure_fixture.foam").touch()
    print(json.dumps({"status": report["status"], "acceptance_report": str(output)}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
