#!/usr/bin/env python3
"""Run the repository unittest discovery scope and emit unambiguous counts."""
from __future__ import annotations

import argparse
import json
import platform
import time
import unittest
from pathlib import Path


def count_cases(suite: unittest.TestSuite) -> int:
    return suite.countTestCases()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_*.py")
    discovered = count_cases(suite)
    started = time.monotonic()
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    expected_failures = len(result.expectedFailures)
    unexpected_successes = len(result.unexpectedSuccesses)
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = result.testsRun - skipped - failures - errors - expected_failures - unexpected_successes
    report = {
        "schema_version": "espresso.whole_pull.unit_qualification.v1",
        "suite": "python3 -m unittest discover -s tests -p 'test_*.py'",
        "tests_discovered": discovered,
        "tests_run": result.testsRun,
        "passed": passed,
        "skipped": skipped,
        "failures": failures,
        "errors": errors,
        "expected_failures": expected_failures,
        "unexpected_successes": unexpected_successes,
        "overall_success": result.wasSuccessful(),
        "python_version": platform.python_version(),
        "duration_seconds": round(time.monotonic() - started, 6),
        "exact_head_binding": "EXTERNAL_CI_AND_FINAL_REVIEW_EVIDENCE",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
