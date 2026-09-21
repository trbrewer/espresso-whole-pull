#!/usr/bin/env python3
"""Portable launcher for the bounded SCI-MD-RHEOLOGY-001 runner."""
from pathlib import Path
import runpy
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'tools/sci_md_rheology_001'))
sys.dont_write_bytecode = True
if __name__ == '__main__':
    runpy.run_path(str(root / 'tools/sci_md_rheology_001/runner.py'), run_name='__main__')
