from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import val_corpus_002_b0_tooling as b0


class ConfigurationTests(unittest.TestCase):
    def test_inventory_counts_and_unique_hashes(self):
        inventory = b0.build_configuration_inventory(ROOT)
        self.assertEqual(inventory["counts"]["final_production_identities"], 45)
        self.assertEqual(len(inventory["numeric_configurations"]), 30)
        self.assertEqual(len(inventory["typed_p2_templates"]), 15)
        hashes = [row["canonical_sha256"] for row in inventory["typed_p2_templates"]]
        self.assertEqual(len(hashes), len(set(hashes)))

    def test_materialization_changes_only_placeholder(self):
        template = {"a": 1, "chemistry": {"extractionRateConstant_s_inverse": b0.TYPED_PLACEHOLDER}}
        digest = b0.canonical_sha256(template)
        result = b0.materialize_p2(template, 0.2, digest)
        self.assertEqual(result, {"a": 1, "chemistry": {"extractionRateConstant_s_inverse": 0.2}})

    def test_materialization_rejects_hash_bounds_and_placeholder_count(self):
        template = {"extractionRateConstant_s_inverse": b0.TYPED_PLACEHOLDER}
        digest = b0.canonical_sha256(template)
        for rate in (math.nan, math.inf, -1.0, 3.0):
            with self.assertRaises(ValueError): b0.materialize_p2(template, rate, digest)
        with self.assertRaises(ValueError): b0.materialize_p2(template, 0.2, "0" * 64)
        with self.assertRaises(ValueError): b0.materialize_p2({}, 0.2, b0.canonical_sha256({}))
        double = {"a": b0.TYPED_PLACEHOLDER, "b": b0.TYPED_PLACEHOLDER}
        with self.assertRaises(ValueError): b0.materialize_p2(double, 0.2, b0.canonical_sha256(double))


class ReferenceAndParityTests(unittest.TestCase):
    def test_direct_reference_binding(self):
        review_root = ROOT.parent / ".wp03-002-exact-head-review"
        trace = review_root / "corrected-runs-v2/cases/WASZ-9-COMPACT/postProcessing/wholePull/0/traces.csv"
        if not trace.is_file():
            self.skipTest("read-only retained WP03-002 artifact is not present in portable CI")
        binding = b0.bind_reference(ROOT, review_root)
        self.assertEqual(binding["sha256"], b0.REFERENCE["sha256"])
        self.assertEqual(binding["first_timestamp_s"], 0.02)
        self.assertEqual(binding["final_timestamp_s"], 29.9999999999994)
        self.assertEqual(binding["historical_manifest_status"],
                         "EXCLUDED_AS_DOWNSTREAM_ARTIFACT_BY_DESIGN")

    @staticmethod
    def row(time, scale=1.0):
        return {field: (time if field == "time_s" else scale) for field in b0.PARITY_FIELDS}

    def test_parity_exact_and_interpolated(self):
        reference = [self.row(0.02, 1.0), self.row(0.03, 2.0)]
        candidate = [self.row(0.02, 1.0), self.row(0.025, 1.5), self.row(0.03, 2.0)]
        self.assertEqual(b0.compare_parity(reference, candidate)["status"], "PASS")
        reference = [self.row(0.025, 1.5)]
        candidate = [self.row(0.02, 1.0), self.row(0.03, 2.0)]
        self.assertEqual(b0.compare_parity(reference, candidate)["status"], "PASS")

    def test_parity_prohibits_t0_and_extrapolation(self):
        with self.assertRaises(ValueError):
            b0.compare_parity([self.row(0.0)], [self.row(0.0)])
        with self.assertRaises(ValueError):
            b0.compare_parity([self.row(0.02)], [self.row(0.03)])

    def test_initial_state_is_exact(self):
        keys = {key: "x" for key in {"initial_fields_sha256", "configuration_sha256",
            "geometry_mesh_sha256", "executable_sha256", "chemistry_sha256",
            "pressure_ramp_controls_sha256", "timestep_controls_sha256",
            "numerical_controls_sha256"}}
        keys["simulation_start_time_s"] = 0.0
        b0.verify_initial_state(keys, dict(keys))
        changed = dict(keys); changed["simulation_start_time_s"] = 1.0
        with self.assertRaises(ValueError): b0.verify_initial_state(changed, keys)


class ReducerTests(unittest.TestCase):
    def test_plateau_safe_fixed_mass(self):
        result = b0.fixed_mass([(0, 0, 0), (1, .01, .001), (2, .01, .001),
                                (3, .03, .003)], .02)
        self.assertAlmostEqual(result["cup_solute_mass_kg"], .002)
        with self.assertRaises(ValueError):
            b0.fixed_mass([(0, 0, 0), (1, .01, .001), (2, .01, .002)], .01)

    def test_interval_zero_boundary_is_permitted_only_with_exact_state(self):
        samples = [{"time_s": 5.0, "water_mass_rate_kg_s": 2.0,
                    "solute_mass_rate_kg_s": 1.0}]
        initial = {"simulation_start_time_s": 0.0, "initial_cup_water_kg": 0.0,
                   "initial_cup_solute_kg": 0.0, "initial_outlet_flow_m3_s": 0.0,
                   "initial_solute_flux_kg_s": 0.0}
        self.assertAlmostEqual(b0.interval_chemistry(samples, 0, 5, initial), 1/3)
        initial["initial_outlet_flow_m3_s"] = 1e-9
        with self.assertRaises(ValueError): b0.interval_chemistry(samples, 0, 5, initial)

    def test_metrics_axes_and_sensitivity(self):
        metrics = b0.production_metrics([1, 2, 3], [2, 2, 2], [1, None, 2])
        self.assertAlmostEqual(metrics["rmse"], math.sqrt(2/3))
        self.assertEqual(b0.axis_contrast([3, 4], [1, 1]), [2, 3])
        self.assertEqual(b0.finite_range_sensitivity(1, 2, [1, 2], [2, 4]), [1, 1])
        with self.assertRaises(ValueError): b0.finite_range_sensitivity(0, 2, [1], [2])
        self.assertEqual(b0.calibration_objective([1, 2, 3], [1, 2, 3]), 0)
        audit = b0.source_species_limitation_audit({"caffeine": [1, 2]}, [3, 4])
        self.assertFalse(audit["solver_predicted_named_species"])


class OptimizerTests(unittest.TestCase):
    def test_interior_minimum(self):
        result = b0.golden_section(lambda x: (x-.4)**2, .1, 1.0)
        self.assertEqual(result["status"], "PASS")
        self.assertAlmostEqual(result["selected_rate"], .4, places=7)

    def test_boundary_minimum(self):
        result = b0.golden_section(lambda x: x, .1, 1.0)
        self.assertEqual(result["selected_rate"], .1)

    def test_ties_choose_lower_rate(self):
        result = b0.golden_section(lambda x: 1.0, .1, 1.0)
        self.assertEqual(result["selected_rate"], .1)

    def test_failed_and_nonfinite_evaluations(self):
        def objective(x):
            if x < .3: raise ValueError("SYNTHETIC_FAILURE")
            if x > .8: return math.nan
            return (x-.5)**2
        result = b0.golden_section(objective, .1, 1.0)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(any(row["status"] == "FAILED_EVALUATION" for row in result["trace"]))

    def test_evaluation_limit_exhaustion(self):
        result = b0.golden_section(lambda x: (x-.4)**2, .1, 1.0, max_evaluations=2)
        self.assertEqual(result["status"], "NONCONVERGED_EVALUATION_LIMIT")
        self.assertEqual(result["evaluations"], 2)

    def test_cache_does_not_consume_evaluation(self):
        result = b0.golden_section(lambda x: 1.0, .1, 1.0)
        keys = [row["rate_hex"] for row in result["trace"] if not row["cache_hit"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all({"lower", "upper", "interior_low", "interior_high", "decision"} <= row.keys()
                            for row in result["trace"]))


class ArtifactAndBarrierTests(unittest.TestCase):
    def test_inventory_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "b").write_text("b"); (root / "a").write_text("a")
            first = b0.external_inventory(root, [root / "b", root / "a"])
            second = b0.external_inventory(root, [root / "a", root / "b"])
            self.assertEqual(first, second)

    def test_b0_result_access_and_protected_scoring_fail_closed(self):
        barrier = b0.AccessBarrier()
        with self.assertRaises(PermissionError): barrier.require_result_access("SCHM_EXP7_P2_FIXED_AFTER_EXP7_CALIBRATION_H1")
        with self.assertRaises(PermissionError): barrier.authorize_b1("NOT_AUTHORIZED")
        with self.assertRaises(PermissionError): barrier.validate_command(["--protected-shape-scorer"])
        barrier.authorize_b1("SEPARATE_HUMAN_OWNER_B1_AUTHORITY")
        barrier.require_result_access("SCHM_EXP7_P2_FIXED_AFTER_EXP7_CALIBRATION_H1")
        with self.assertRaises(PermissionError): barrier.require_result_access("SCHM_EXP1_P2_FIXED_AFTER_EXP7_CALIBRATION_H1")
        barrier.freeze_p2({"rate_s_inverse": .1, "optimizer_trace_sha256": "a" * 64,
                           "calibration_case": "SCHM_EXP7_P2_FIXED_AFTER_EXP7_CALIBRATION_H1"})
        self.assertEqual(barrier.p2_rate, .1)


if __name__ == "__main__":
    unittest.main()
