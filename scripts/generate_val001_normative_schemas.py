#!/usr/bin/env python3
"""Generate governing schema compatibility records from normative contracts."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.validation.val001.framework import canonical_json
from tools.validation.val001.normative import EXPLICIT_REGISTRY, generated_explicit_registry

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    (root / EXPLICIT_REGISTRY).write_bytes(canonical_json(generated_explicit_registry(root)))

if __name__ == "__main__":
    main()
