import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import val_corpus_002_b0_tooling as b0
import val_corpus_002_b2 as b2


class StageB2ProspectiveTests(unittest.TestCase):
    def test_exact_fixed_rate(self):
        self.assertEqual(b2.RATE, 0.3439597024835067)
        self.assertEqual(b2.RATE.hex(), b2.RATE_HEX)

    def test_closed_inventory(self):
        inventory = b0.build_configuration_inventory(ROOT)
        self.assertEqual(inventory["counts"]["final_production_identities"], 45)
        self.assertEqual(inventory["counts"]["sensitivity_identities"], 9)

    def test_sensitivity_is_fixed_p1_h1_only(self):
        inventory = b0.build_configuration_inventory(ROOT)
        baseline = next(row["configuration"] for row in inventory["numeric_configurations"]
                        if row["id"] == "SCHM_EXP7_P1_H1")
        rows = json.loads((ROOT / b0.SENSITIVITY_MATRIX).read_text())["future_runs"]
        for row in rows:
            scenario = b2.sensitivity_scenario(ROOT, baseline, row)
            self.assertEqual(scenario["calibration"]["status"], "CLOSED_NO_REFIT")
            self.assertEqual(scenario["scenario_id"], row["run_id"])

    def test_raw_rate_has_no_entry_point(self):
        self.assertFalse(hasattr(b2, "calibrate"))
        self.assertFalse(hasattr(b2, "optimize"))

    def test_protected_or_refit_actions_absent(self):
        text = (ROOT / "scripts/val_corpus_002_b2.py").read_text()
        self.assertNotIn("historical_shape_scorer(", text)
        self.assertNotIn("golden_section_log_k(", text)

    def test_closed_matrix_driver_and_one_retry(self):
        text = (ROOT / "scripts/val_corpus_002_b2.py").read_text()
        self.assertIn("for attempt in (1, 2):", text)
        self.assertIn("production_planned\": 45", text)
        self.assertIn("sensitivity_planned\": 9", text)

    def test_b1_anchor_hash_is_immutable(self):
        self.assertEqual(b2.B1_MANIFEST_SHA256,
                         "554ce1c35979fa8961973b8cdd663a7a0ba817f6369667ea10808a06f644cbbc")

    def test_missing_target_is_typed_not_infrastructure(self):
        text = (ROOT / "scripts/val_corpus_002_b2.py").read_text()
        self.assertIn("REQUIRED_TARGET_BEVERAGE_MASS_NOT_REACHED_NO_EXTRAPOLATION", text)
        self.assertIn("raise b0.TypedNumericalEvaluationFailure", text)

    def test_refuses_reused_runtime_root(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(b2.InfrastructureFailure):
                b2.initialize(ROOT, Path(temp), Path(temp) / "missing", Path(temp))


if __name__ == "__main__":
    unittest.main()
