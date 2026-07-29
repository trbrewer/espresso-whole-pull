#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.results.read_text(encoding="utf-8"))
    gates = data["verification"]
    required = (
        "source_formula_verification",
        "puckworks_reference_parity",
        "uniform_pressure_fixture",
        "r0_disabled_branch_regression",
        "constant_r1_disabled_branch_regression",
    )
    failures = [key for key in required if gates.get(key, {}).get("status") != "PASS"]
    fixture_gate = gates.get("uniform_pressure_fixture", {})
    fixture_path_value = fixture_gate.get("result_path")
    if not fixture_path_value:
        failures.append("uniform_pressure_fixture.result_path")
    else:
        fixture_path = Path(fixture_path_value)
        if not fixture_path.is_absolute():
            fixture_path = args.root / fixture_path
        try:
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            failures.append("uniform_pressure_fixture.result")
        else:
            if fixture.get("fixture_status") != "PASS":
                failures.append("uniform_pressure_fixture.fixture_status")
            if fixture_gate.get("result_sha256") != sha256(fixture_path):
                failures.append("uniform_pressure_fixture.result_sha256")
            expected = {
                "executable_sha256": fixture.get("execution", {}).get("executable_sha256"),
                "solver_source_sha256": fixture.get("identity", {}).get("solver_source_sha256"),
                "closure_contract_sha256": fixture.get("identity", {}).get("closure_contract_sha256"),
                "fixture_correction_commit": fixture.get("identity", {}).get("implementation_commit"),
            }
            for key, value in expected.items():
                if fixture_gate.get(key) != value:
                    failures.append(f"uniform_pressure_fixture.{key}")
    print(json.dumps({"status": "FAIL" if failures else "PASS", "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
