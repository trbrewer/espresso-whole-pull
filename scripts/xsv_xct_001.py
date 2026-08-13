#!/usr/bin/env python3
"""Standard-library entry point for XSV-XCT-001 scientific tooling."""
from pathlib import Path
import runpy

runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "verification/tools/xsv_xct_001.py"),
    run_name="__main__",
)
