#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


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
    print(json.dumps({"status": "FAIL" if failures else "PASS", "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
