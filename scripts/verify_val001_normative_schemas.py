#!/usr/bin/env python3
"""Non-writing proof that governing schemas derive without record instances."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.validation.val001.normative import verify_generated_registry

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_generated_registry(args.root.resolve()), sort_keys=True))

if __name__ == "__main__":
    main()
