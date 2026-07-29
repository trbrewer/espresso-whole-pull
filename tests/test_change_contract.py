from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_change_contract import selected_verifier  # noqa: E402
from verify_governing_physics_change import verify as verify_governing  # noqa: E402
from verify_v0_1_4_baseline_integrity import verify as verify_baseline  # noqa: E402


class ChangeContractRoutingTests(unittest.TestCase):
    def copy_root(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temporary = tempfile.TemporaryDirectory()
        target = Path(temporary.name) / "repo"
        shutil.copytree(
            ROOT,
            target,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "preflight"),
        )
        return temporary, target

    def test_correct_wp02_metadata_selects_and_passes_governing_verifier(self) -> None:
        self.assertEqual(
            selected_verifier({"change_declaration": "GOVERNING_PHYSICS_CHANGE"}),
            "verify_governing_physics_change.py",
        )
        self.assertEqual(verify_governing(ROOT)["status"], "PASS")

    def test_governing_change_fails_with_v0_1_4_active_version(self) -> None:
        temporary, root = self.copy_root()
        try:
            (root / "VERSION").write_text("0.1.4\n")
            self.assertEqual(verify_governing(root)["status"], "FAIL")
        finally:
            temporary.cleanup()

    def test_governing_change_fails_if_r0_or_constant_r1_changes(self) -> None:
        for relative in (
            "config/reference_R0.json",
            "config/reconstruction_R1_waszkiewicz_9bar.json",
        ):
            temporary, root = self.copy_root()
            try:
                path = root / relative
                value = json.loads(path.read_text())
                value["synthetic_forbidden_change"] = True
                path.write_text(json.dumps(value))
                self.assertEqual(verify_governing(root)["status"], "FAIL")
            finally:
                temporary.cleanup()

    def test_governing_change_fails_if_closure_defaults_active(self) -> None:
        temporary, root = self.copy_root()
        try:
            path = root / "validation/wp02/WP02_001_CLOSURE_CONTRACT.json"
            value = json.loads(path.read_text())
            value["implementation_boundary"]["disabled_by_default"] = False
            path.write_text(json.dumps(value))
            self.assertEqual(verify_governing(root)["status"], "FAIL")
        finally:
            temporary.cleanup()

    def test_governing_change_fails_if_result_or_run_status_changes(self) -> None:
        for relative in (
            "validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json",
            "validation/wp02/WP02_001_RUN_STATUS.json",
        ):
            temporary, root = self.copy_root()
            try:
                path = root / relative
                value = json.loads(path.read_text())
                value["synthetic_forbidden_change"] = True
                path.write_text(json.dumps(value))
                self.assertEqual(verify_governing(root)["status"], "FAIL")
            finally:
                temporary.cleanup()

    def test_governing_change_fails_if_validation_is_overstated(self) -> None:
        temporary, root = self.copy_root()
        try:
            path = root / "validation/wp02/WP02_001_RUN_STATUS.json"
            value = json.loads(path.read_text())
            value["physical_validation"] = "ESTABLISHED"
            path.write_text(json.dumps(value))
            self.assertEqual(verify_governing(root)["status"], "FAIL")
        finally:
            temporary.cleanup()

    def test_historical_integrity_is_independently_usable(self) -> None:
        self.assertEqual(verify_baseline(ROOT)["status"], "PASS")
        self.assertTrue((ROOT / "scripts/verify_no_physics_change.py").is_file())

    def test_no_physics_declaration_routes_to_historical_contract_and_fails_current_physics(self) -> None:
        self.assertEqual(
            selected_verifier({"change_declaration": "NO_GOVERNING_PHYSICS_CHANGE"}),
            "verify_no_physics_change.py",
        )
        with tempfile.TemporaryDirectory() as td:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/verify_no_physics_change.py"),
                    "--root",
                    str(ROOT),
                    "--output",
                    str(Path(td) / "report.json"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_no_route_can_skip_both_contracts(self) -> None:
        for declaration in ({}, {"change_declaration": "SKIP"}):
            with self.assertRaises(ValueError):
                selected_verifier(declaration)


if __name__ == "__main__":
    unittest.main()
