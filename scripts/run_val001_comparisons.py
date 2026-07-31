#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validation.val001.framework import run  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--spec", type=Path, default=Path("validation/val001/contracts/VAL_001_PREEXECUTION_RUN_SPEC.json"))
    parser.add_argument("--adapter", type=Path, default=Path("validation/val001/adapters/WASZKIEWICZ_PRESSURE_FLOW_ADAPTER.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    result = run(root, root / args.spec, root / args.adapter)
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

