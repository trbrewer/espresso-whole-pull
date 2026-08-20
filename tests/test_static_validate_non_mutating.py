"""Regression coverage for the static validator's non-mutating default."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StaticValidatorNonMutatingTests(unittest.TestCase):
    def test_default_validation_preserves_exact_worktree_status(self) -> None:
        before = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        completed = subprocess.run(
            [sys.executable, "scripts/static_validate.py", "--root", "."],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        after = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(after, before)
        self.assertFalse(
            (ROOT / "cases/reference_R0_20g_58mm_9bar/preflight").exists()
        )

    def test_repository_output_is_rejected(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/static_validate.py",
                "--root",
                ".",
                "--output",
                str(ROOT / "forbidden.json"),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("outside the repository", completed.stderr)
        self.assertFalse((ROOT / "forbidden.json").exists())

    def test_external_symlink_parent_is_rejected_before_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            real_parent = base / "real_parent"
            real_parent.mkdir()
            symlink_parent = base / "symlink_parent"
            symlink_parent.symlink_to(real_parent, target_is_directory=True)
            destination = symlink_parent / "report.json"
            completed = subprocess.run(
                [sys.executable, "scripts/static_validate.py", "--root", ".",
                 "--output", str(destination)],
                cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("must not contain a symlink", completed.stderr)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
