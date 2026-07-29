#!/usr/bin/env python3
"""Dispatch active boundary verification from a tracked change declaration."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_DECLARATION = Path(
    "validation/wp02/WP_0_2F_RELEASE_FINALIZATION_CONTRACT.json"
)


def selected_verifier(declaration: dict) -> str:
    classifications = declaration.get("task_classification", [])
    if (
        "NO_GOVERNING_PHYSICS_CHANGE" in classifications
        and "RELEASE_ENGINEERING_AND_DOCUMENTATION_ONLY" in classifications
    ):
        return "verify_release_finalization.py"
    value = declaration.get("change_declaration")
    if value == "GOVERNING_PHYSICS_CHANGE":
        return "verify_governing_physics_change.py"
    if value in ("NO_GOVERNING_PHYSICS_CHANGE", "NO_PHYSICS_CHANGE"):
        return "verify_no_physics_change.py"
    raise ValueError("tracked change declaration is missing or unsupported")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--declaration", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    declaration_path = args.declaration or root / DEFAULT_DECLARATION
    declaration = json.loads(declaration_path.read_text())
    verifier = selected_verifier(declaration)
    command = [
        sys.executable,
        str(root / "scripts" / verifier),
        "--root",
        str(root),
        "--output",
        str(args.output),
    ]
    if verifier in (
        "verify_governing_physics_change.py",
        "verify_release_finalization.py",
    ):
        command.extend(["--declaration", str(declaration_path)])
    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
