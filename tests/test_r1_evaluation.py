from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "validation/r1/WP01R_005_EXECUTION_RESULT.json"


class R1EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = json.loads(RESULT.read_text(encoding="utf-8"))

    def test_frozen_execution_and_no_retuning(self) -> None:
        result = self.result
        self.assertEqual(
            result["source_dependency"]["commit"],
            "fc61c4670ec7bf801e40bb391aab16048b8da26b",
        )
        self.assertEqual(result["execution"]["parameter_fitting_count"], 0)
        self.assertEqual(result["execution"]["optimizer_iteration_count"], 0)
        self.assertEqual(result["execution"]["post_run_adjustment_count"], 0)
        self.assertEqual(
            result["execution"]["solver_executable_sha256"],
            "ada45a5440d08ae8da1a57d65cdf511748a340cd09a045121c59ea83a3d8d6d7",
        )

    def test_numerical_calibration_and_r0_regression_pass(self) -> None:
        self.assertTrue(
            self.result["numerical_and_conservation"]["all_numerical_gates_pass"]
        )
        self.assertTrue(
            self.result["numerical_and_conservation"]["all_reduced_twin_gates_pass"]
        )
        self.assertEqual(self.result["calibration_reproduction"]["status"], "PASS")
        self.assertEqual(self.result["r0_regression"]["status"], "PASS")

    def test_protected_failure_is_reported_not_hidden(self) -> None:
        protected = self.result["protected_comparison"]
        self.assertEqual(protected["status"], "FAIL")
        self.assertEqual(len(protected["shots"]), 5)
        self.assertEqual(protected["shots_at_or_below_rmse_0_20"], 0)
        self.assertEqual(protected["shots_at_or_above_pearson_0_90"], 0)
        self.assertIsNone(protected["median_pearson_r"])
        for shot in protected["shots"]:
            self.assertEqual(shot["pearson_gate_status"], "FAIL")
            self.assertEqual(shot["predicted_normalized_population_std"], 0.0)
        self.assertEqual(
            self.result["overall_r1_physical_comparison"],
            "SOURCE_LINKED_RECONSTRUCTION_FAIL",
        )
        self.assertEqual(
            self.result["residual_classification"]["primary"],
            "STRUCTURAL_MODEL_INADEQUACY",
        )
        self.assertFalse(
            self.result["residual_classification"]["software_execution_failure"]
        )

    def test_claim_ceiling_remains_bounded(self) -> None:
        self.assertEqual(self.result["physical_validation"], "NOT_ESTABLISHED")
        self.assertFalse(self.result["governing_physics_change"])


if __name__ == "__main__":
    unittest.main()
