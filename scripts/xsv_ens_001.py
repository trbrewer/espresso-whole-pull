#!/usr/bin/env python3
"""XSV-ENS-001 reproducible pilot, matrix, execution, and reduction entry point."""
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "verification/cases/xsv_ens_001/xsv_ens_001_runtime.py"
sys.dont_write_bytecode = True
runpy.run_path(str(RUNTIME), run_name="__main__")
