#!/usr/bin/env python3
"""Verify VAL-001's consumed state; no real-data execution remains authorized."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validation.val001.invocation import verify_consumed_state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--verify-consumed-state", action="store_true")
    args = parser.parse_args()
    if not args.verify_consumed_state:
        raise SystemExit("VAL001_EXECUTION_AUTHORITY_CONSUMED_NO_FURTHER_INVOCATION")
    verify_consumed_state(args.root.resolve())
    print("VAL001_EXECUTION_AUTHORITY_CONSUMED_NO_FURTHER_INVOCATION")


if __name__ == "__main__":
    main()
