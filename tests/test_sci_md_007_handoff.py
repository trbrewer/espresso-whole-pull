import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_sci_md_007", ROOT / "validation/sci_md_007/verify_handoff.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TestSciMd007Handoff(unittest.TestCase):
    def test_handoff_verifies(self):
        self.assertEqual(MODULE.verify()["status"], "PASS")

    def test_exact_lock(self):
        lock = json.loads((ROOT / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json").read_text())
        self.assertEqual(lock["commit"], "7915bcba615f142d0a3d3968d82fb6fd73c99d85")
        self.assertEqual(lock["tree"], "92bf34173d96247f59861ae1b802056c87ba70f2")
        self.assertEqual(lock["export_sha256"], "626822addc1113bb41c0b51481a0ddbe2f21f9d52f358d1cf5e70cb342e07cd1")

    def test_fail_does_not_activate_inventory_or_physics(self):
        result = json.loads((ROOT / "docs/validation/sci_md_007/RESULT.json").read_text())
        self.assertEqual(result["inventory_predictor_activation"], "NOT_AUTHORIZED")
        self.assertEqual(result["extractable_inventory_mapping_status"], "NOT_ESTABLISHED")
        self.assertEqual(result["physical_validation"], "NOT_ESTABLISHED")
        self.assertEqual(result["change_declaration"], "NO_GOVERNING_PHYSICS_CHANGE")
        self.assertFalse(result["angeloni_reuse"])
        self.assertFalse(result["sci_md_006_reopened"])


if __name__ == "__main__":
    unittest.main()
