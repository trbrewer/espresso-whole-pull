from __future__ import annotations

import importlib.util
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("r1_analysis", ROOT / "scripts/analyze_r1.py")
assert SPEC and SPEC.loader
ANALYSIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYSIS)


class R1AnalysisSyntheticTests(unittest.TestCase):
    def test_exact_governed_bindings_and_no_8s_mapping(self) -> None:
        contract, scenario, lock = ANALYSIS.authorities(ROOT)
        self.assertEqual(lock["checkout_commit"], contract["source_dependency"]["commit"])
        self.assertEqual(lock["checkout_tree_sha"], contract["source_dependency"]["tree"])
        self.assertEqual(
            scenario["source_time_mapping"]["solver_time_equals_source_time_plus_s"],
            contract["time_mapping_contract"]["source_to_solver_offset_s"],
        )
        self.assertFalse(contract["time_mapping_contract"]["source_first_drop_offset_8s_used"])

    def test_linear_interpolation_and_strict_range(self) -> None:
        self.assertEqual(ANALYSIS.interpolate([0.0, 1.0], [2.0, 4.0], 0.5), 3.0)
        with self.assertRaises(ValueError):
            ANALYSIS.interpolate([0.0, 1.0], [2.0, 4.0], -0.1)
        with self.assertRaises(ValueError):
            ANALYSIS.interpolate([0.0, 1.0], [2.0, 4.0], 1.1)

    def test_rmse_normalization_and_population_pearson(self) -> None:
        observed = [1.0, 2.0, 3.0]
        predicted = [2.0, 4.0, 6.0]
        obs_norm = [value / 3.0 for value in observed]
        pred_norm = [value / 6.0 for value in predicted]
        rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(obs_norm, pred_norm)) / 3)
        self.assertEqual(rmse, 0.0)
        value, defined = ANALYSIS.pearson(obs_norm, pred_norm, 1e-8)
        self.assertTrue(defined)
        self.assertAlmostEqual(value, 1.0)

    def test_degeneracy_is_undefined_without_jitter(self) -> None:
        value, defined = ANALYSIS.pearson([1.0] * 5, [1, 2, 3, 4, 5], 1e-8)
        self.assertIsNone(value)
        self.assertFalse(defined)

    def test_median_and_four_of_five_gates(self) -> None:
        gates = {
            "median_normalized_shape_rmse_max": 0.15,
            "shots_required_at_or_below_rmse_0_20": 4,
            "median_pearson_r_min": 0.95,
            "shots_required_at_or_above_r_0_90": 4,
        }
        shots = [
            {"normalized_shape_rmse": 0.1, "pearson_defined": True, "pearson_r": 0.96}
            for _ in range(4)
        ] + [{"normalized_shape_rmse": 0.3, "pearson_defined": True, "pearson_r": 0.8}]
        self.assertEqual(ANALYSIS.aggregate(shots, gates)["status"], "PASS")
        shots[0]["pearson_defined"] = False
        shots[0]["pearson_r"] = None
        self.assertEqual(ANALYSIS.aggregate(shots, gates)["status"], "FAIL")

    def test_scientific_values_are_read_not_embedded_as_results(self) -> None:
        source = (ROOT / "scripts/analyze_r1.py").read_text(encoding="utf-8")
        for forbidden in ("0.380987", "0.393133", "0.480984", "0.465988"):
            self.assertNotIn(forbidden, source)
        contract = json.loads(
            (ROOT / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json").read_text()
        )
        self.assertIn("liquid_density_kg_m3", contract["solver_to_source_flow_mapping"]["primary_predicted_quantity"])

    def test_physical_failure_remains_distinct_from_software_failure(self) -> None:
        shots = [
            {"normalized_shape_rmse": 1.0, "pearson_defined": False, "pearson_r": None}
            for _ in range(5)
        ]
        contract = json.loads(
            (ROOT / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json").read_text()
        )
        self.assertEqual(
            ANALYSIS.aggregate(shots, contract["protected_comparison_contract"]["gates"])["status"],
            "FAIL",
        )


if __name__ == "__main__":
    unittest.main()
