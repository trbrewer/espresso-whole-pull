#!/usr/bin/env python3
"""Portable entry point for the governed XSV-TAICHI-001 runtime."""

from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = (
    ROOT
    / "verification"
    / "cases"
    / "xsv_taichi_001"
    / "xsv_taichi_001_runtime.py"
)

if not RUNTIME.is_file():
    raise SystemExit(f"missing governed XSV-TAICHI-001 runtime: {RUNTIME}")

sys.dont_write_bytecode = True
runpy.run_path(str(RUNTIME), run_name="__main__")
