#!/usr/bin/env python3
"""Prove the SCI-ED-001 branch adds no production physics relative to its start."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

SCHEMA = "espresso.whole_pull.sci_ed_001.no_governing_physics_change.v1"
OWNED = ("docs/analysis/sci_ed_001/", "validation/cases/sci_ed_001/", "scripts/sci_ed_001", "tests/test_sci_ed_001")
FORBIDDEN_PREFIXES = ("solver/", "config/", "cases/", "dependencies/", "tools/", "docs/analysis/sci_md_002", "validation/cases/sci_md_002", "scripts/sci_md_002", "tests/test_sci_md_002", "docs/analysis/sci_lc_001a/", "validation/cases/sci_lc_001a/", "scripts/sci_lc_001a", "tests/test_sci_lc_001a")
SHARED_MACHINE = ("scripts/machine_coupling_reference.py", "scripts/analyze_wp02_002_machine_coupling.py", "solver/espressoWholePullFoam/machineBoundaryModel.H")


def canonical(obj): return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
def sha_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def git(root: Path, *args: str) -> str: return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def tree_files(root: Path, revision: str, prefix: str) -> list[str]:
    raw = git(root, "ls-tree", "-r", "--name-only", revision, "--", prefix)
    return raw.splitlines() if raw else []


def aggregate_revision(root: Path, revision: str, prefixes: tuple[str, ...]) -> str:
    records = []
    for prefix in prefixes:
        for path in tree_files(root, revision, prefix):
            records.append([path, sha_bytes(subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=root))])
    return sha_bytes(canonical(sorted(records)).encode())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True); p.add_argument("--expected-start-head", required=True); p.add_argument("--expected-start-tree", required=True)
    p.add_argument("--expected-current-head", required=True); p.add_argument("--expected-current-tree", required=True); p.add_argument("--output", required=True)
    a = p.parse_args(); root = Path(a.root).resolve()
    observed_head = git(root, "rev-parse", "HEAD"); observed_tree = git(root, "rev-parse", "HEAD^{tree}")
    start_tree = git(root, "rev-parse", f"{a.expected_start_head}^{{tree}}")
    current_tree = git(root, "rev-parse", f"{a.expected_current_head}^{{tree}}")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", a.expected_start_head, a.expected_current_head], cwd=root).returncode == 0
    changed_raw = git(root, "diff", "--name-only", f"{a.expected_start_head}..{a.expected_current_head}")
    changed = changed_raw.splitlines() if changed_raw else []
    owned = all(any(path.startswith(prefix) for prefix in OWNED) for path in changed)
    forbidden = [path for path in changed if path.startswith(FORBIDDEN_PREFIXES)]
    start_solver_sha = sha_bytes(subprocess.check_output(["git", "show", f"{a.expected_start_head}:solver/espressoWholePullFoam/espressoWholePullFoam.C"], cwd=root))
    current_solver_sha = sha_bytes(subprocess.check_output(["git", "show", f"{a.expected_current_head}:solver/espressoWholePullFoam/espressoWholePullFoam.C"], cwd=root))
    aggregates = {}
    groups = {"solver": ("solver/",), "config": ("config/",), "cases": ("cases/",), "dependencies": ("dependencies/",), "shared_machine_utilities": SHARED_MACHINE}
    for name, prefixes in groups.items():
        before = aggregate_revision(root, a.expected_start_head, prefixes); after = aggregate_revision(root, a.expected_current_head, prefixes)
        aggregates[name] = {"starting_sha256": before, "current_sha256": after, "status": "PASS" if before == after else "FAIL"}
    predecessor_imports = []
    for path in changed:
        if path.startswith("scripts/sci_ed_001") and path.endswith(".py"):
            text = subprocess.check_output(["git", "show", f"{a.expected_current_head}:{path}"], cwd=root, text=True)
            predecessor_imports.extend(x for x in ("sci_md_002a.py", "sci_md_002b.py", "sci_md_002c.py") if x in text)
    checks = {
        "starting_head_exists_and_tree_exact": start_tree == a.expected_start_tree,
        "current_head_and_tree_exact": observed_head == a.expected_current_head and observed_tree == a.expected_current_tree and current_tree == a.expected_current_tree,
        "descends_from_start": ancestor, "all_changed_paths_owned": owned, "forbidden_paths_unchanged": not forbidden,
        "production_solver_exact": start_solver_sha == current_solver_sha,
        "all_protected_aggregates_exact": all(x["status"] == "PASS" for x in aggregates.values()),
        "declaration_exact": "NO_GOVERNING_PHYSICS_CHANGE" in subprocess.check_output(["git", "show", f"{a.expected_current_head}:validation/cases/sci_ed_001/SCI_ED_001_PROTOCOL.json"], cwd=root, text=True),
        "predecessor_read_only_interface_declared": len(set(predecessor_imports)) == 3,
    }
    report = {"schema_version": SCHEMA, "status": "PASS" if all(checks.values()) else "FAIL", "starting_head": a.expected_start_head,
              "starting_tree": a.expected_start_tree, "current_head": a.expected_current_head, "current_tree": a.expected_current_tree,
              "observed_head": observed_head, "observed_tree": observed_tree, "changed_paths": changed, "forbidden_changed_paths": forbidden,
              "production_solver_path": "solver/espressoWholePullFoam/espressoWholePullFoam.C", "starting_production_solver_sha256": start_solver_sha,
              "current_production_solver_sha256": current_solver_sha, "aggregates": aggregates, "checks": checks,
              "active_solver_context": "ACTIVE_SOLVER_ALREADY_CONTAINS_ACCEPTED_GOVERNING_CHANGES",
              "task_result": "SCI_ED_001_INTRODUCED_NO_NEW_GOVERNING_CHANGE" if all(checks.values()) else "SCI_ED_001_NO_GOVERNING_PHYSICS_BOUNDARY_FAILED",
              "claim": "SCI-ED-001 added no new production governing-physics change relative to its frozen current-main starting authority."}
    Path(a.output).write_text(canonical(report)); print(canonical(report), end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())
