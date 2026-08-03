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
import val_corpus_002_b2_recovery as recovery


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

    def test_structured_waszkiewicz_placeholder_collapses_to_scalar(self):
        inventory = b0.build_configuration_inventory(ROOT)
        row = next(row for row in inventory["typed_p2_templates"]
                   if row["id"] == recovery.WASZ_P2_ID)
        self.assertEqual(row["template"]["extraction"]["rate_constant_1_s"],
                         b0.TYPED_PLACEHOLDER)
        value = b0._materialize_p2_rate(row["template"], b2.RATE, row["canonical_sha256"])
        self.assertIs(type(value["extraction"]["rate_constant_1_s"]), float)
        self.assertEqual(value["extraction"]["rate_constant_1_s"].hex(), b2.RATE_HEX)
        self.assertNotIn(b0.PLACEHOLDER_TOKEN, json.dumps(value))
        self.assertNotIn("UNMATERIALIZED", json.dumps(value))
        self.assertNotIn("UNRESOLVED", json.dumps(value))

    def test_token_is_not_reverse_materialization_rate_key(self):
        value, count = b0._replace_numeric_rate({"token": b2.RATE}, b2.RATE)
        self.assertEqual(count, 0)
        self.assertEqual(value, {"token": b2.RATE})

    def test_nested_numeric_token_object_is_rejected(self):
        bad = {"extraction": {"rate_constant_1_s": {
            "status": "UNRESOLVED", "token": b2.RATE,
            "type": "CALIBRATED_SCALAR_S_INVERSE"}}}
        with self.assertRaises(ValueError):
            b0._materialize_p2_rate(bad, b2.RATE, b0.canonical_sha256(bad))

    def test_only_waszkiewicz_p2_hash_changes(self):
        old = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_CONFIGURATION_INVENTORY.json").read_text())
        inventory = b0.build_configuration_inventory(ROOT)
        new = {}
        for row in inventory["typed_p2_templates"]:
            value = b0._materialize_p2_rate(row["template"], b2.RATE, row["canonical_sha256"])
            new[row["id"]] = b0.canonical_sha256(value)
        changed = [key for key in new if new[key] != old["materialized_p2_configuration_sha256"][key]]
        self.assertEqual(changed, [recovery.WASZ_P2_ID])
        self.assertEqual(sum(key.startswith("SCHM_") for key in new), 14)

    def test_every_p2_template_has_one_semantic_rate_path(self):
        inventory = b0.build_configuration_inventory(ROOT)
        for row in inventory["typed_p2_templates"]:
            value = b0._materialize_p2_rate(row["template"], b2.RATE, row["canonical_sha256"])
            found = []
            for path in b0.APPROVED_RATE_PATHS:
                current = value
                for key in path:
                    if not isinstance(current, dict) or key not in current:
                        break
                    current = current[key]
                else:
                    found.append(current)
            self.assertEqual(found, [b2.RATE])

    def test_zero_or_multiple_semantic_rate_paths_fail(self):
        empty = {"chemistry": {"unrelated": b0.TYPED_PLACEHOLDER}}
        with self.assertRaises(ValueError):
            b0._materialize_p2_rate(empty, b2.RATE, b0.canonical_sha256(empty))
        duplicate = {"chemistry": {"extractionRateConstant_s_inverse": b0.TYPED_PLACEHOLDER},
                     "extraction": {"rate_constant_1_s": b0.TYPED_PLACEHOLDER}}
        with self.assertRaises(ValueError):
            b0._materialize_p2_rate(duplicate, b2.RATE, b0.canonical_sha256(duplicate))

    def test_non_scalar_and_nonfinite_rates_fail(self):
        for value in ({"value": b2.RATE}, [b2.RATE], "0.343", True, float("inf")):
            config = {"extraction": {"rate_constant_1_s": value}}
            with self.assertRaises(ValueError):
                b0._materialize_p2_rate(config, b2.RATE, b0.canonical_sha256(config))

    def test_corrected_inventory_preserves_declared_44(self):
        record = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_CORRECTED_CONFIGURATION_INVENTORY.json").read_text())
        self.assertEqual(record["unchanged_numeric_count"], 30)
        self.assertEqual(record["unchanged_schmieder_p2_count"], 14)
        self.assertEqual(record["changed_configuration_ids"], [recovery.WASZ_P2_ID])

    def test_typed_failures_remain_unavailable(self):
        result_path = ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_RESULT.json"
        if not result_path.exists():
            self.skipTest("final B2 result is generated after controlled execution")
        result = json.loads(result_path.read_text())
        failures = [row for row in result["availability_matrix"] if row["status"] == "TYPED_NUMERICAL_CASE_FAILURE"]
        self.assertEqual(len(failures), 18)
        self.assertTrue(all(row["unavailable_disposition"] ==
                            "UNAVAILABLE_TYPED_TARGET_COVERAGE_FAILURE" for row in failures))
        self.assertTrue(all(not any(row["target_availability"].values()) for row in failures))

    def test_result_keeps_protected_scoring_and_refit_outside_scope(self):
        text = (ROOT / "docs/validation/VAL_CORPUS_002_STAGE_B2_RESULT.md").read_text()
        self.assertIn("protected scoring was not performed", text)
        self.assertIn("Calibration is closed with no refit", text)


if __name__ == "__main__":
    unittest.main()
