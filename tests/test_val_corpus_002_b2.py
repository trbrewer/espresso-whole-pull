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
import val_corpus_002_b2_reporting as reporting


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

    def test_final_result_exact_inventory_and_dispositions(self):
        result = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json").read_text())
        cases = result["per_case_numerical_summary"]["cases"]
        self.assertEqual(len(cases), 45)
        self.assertEqual(sum(row["status"] == "PASS" for row in cases), 27)
        failures = [row for row in cases if row["status"] == "TYPED_NUMERICAL_CASE_FAILURE"]
        self.assertEqual(len(failures), 18)
        self.assertTrue(all(row["typed_failure_reason"] == reporting.TARGET_FAILURE for row in failures))
        self.assertEqual(result["interpretation"]["scientific_result_disposition"], reporting.FINAL_SCIENTIFIC)
        self.assertEqual(result["interpretation"]["validation_framework_disposition"], reporting.FINAL_FRAMEWORK)
        self.assertNotEqual(result["interpretation"]["validation_framework_disposition"],
                            "SOURCE_SPECIFIC_AGGREGATE_CHEMISTRY_SUPPORT_WITH_LIMITATIONS")

    def test_hydraulic_coverage_and_axis_interpretation(self):
        result = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json").read_text())
        interpreted = result["interpretation"]
        self.assertEqual(interpreted["h0_target_coverage"]["failure_count"], 18)
        self.assertEqual(interpreted["h1_target_coverage"]["pass"], 21)
        self.assertEqual(interpreted["p2_h1_axis_signs"], {
            "flow": {"matches": 3, "total": 3},
            "grind": {"matches": 0, "total": 3},
            "temperature": {"matches": 3, "total": 3}})

    def test_exact_waszkiewicz_interpretation(self):
        value = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json").read_text())["interpretation"]["waszkiewicz"]
        self.assertEqual(value["fixed_plus_3_s"]["rmse"], 0.06682489539009928)
        self.assertEqual(value["source_clock"]["rmse"], 0.08603049216615972)
        self.assertEqual(value["fixed_plus_3_s"]["window_mean_residual"], {
            "early": -0.08072143166849205, "middle": 0.06597320745689621,
            "late": -0.0037413913634276215})

    def test_normalized_species_audit_is_complete(self):
        audit = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_NORMALIZED_SPECIES_AUDIT.json").read_text())
        self.assertEqual(audit["replicate_triplets_per_component"], 24)
        self.assertEqual(len(audit["records"]), 96)
        means = {name: [audit["summary"][name][ratio]["mean"] for ratio in ("1/1", "1/2", "1/3")]
                 for name in ("TDS", "trigonelline", "5-CQA", "caffeine")}
        expected = {"TDS": [0.7080462873561918, 0.9300451013015908, 1.0],
                    "trigonelline": [0.7356657104905614, 0.9419107120748139, 1.0],
                    "5-CQA": [0.6599169162836315, 0.9071458316027874, 1.0],
                    "caffeine": [0.6338657391825547, 0.8929750022861945, 1.0]}
        for name in expected:
            for actual, target in zip(means[name], expected[name]):
                self.assertAlmostEqual(actual, target, places=15)

    def test_reduced_source_clock_grid_is_closed(self):
        value = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_REDUCED_SOURCE_CLOCK.json").read_text())
        self.assertEqual(len(value["rows"]), 21)
        self.assertTrue(all(len(row["targets"]) == 3 for row in value["rows"]))
        self.assertTrue(all(target["label"] == "DIAGNOSTIC_NOT_OPENFOAM_NOT_VALIDATION"
                            for row in value["rows"] for target in row["targets"]))

    def test_mandatory_summary_and_unavailable_operator(self):
        value = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_PER_CASE_NUMERICAL_SUMMARY.json").read_text())
        self.assertEqual(value["reduction_status"], "PASS")
        self.assertEqual(value["production_matrix_disposition"],
                         "COMPLETE_WITH_18_TYPED_NUMERICAL_CASE_FAILURES")
        self.assertEqual(len(value["cases"]), 45)
        self.assertTrue(all(row["mean_outlet_flow_over_declared_intervals"] == reporting.UNAVAILABLE
                            and row["source_conditioned_hydraulic_residual"] == reporting.UNAVAILABLE
                            for row in value["cases"]))

    def test_deterministic_figure_manifest_and_repeatability(self):
        result_path = ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json"
        result = json.loads(result_path.read_text())
        script_sha = reporting.sha256(ROOT / "scripts/val_corpus_002_b2_reporting.py")
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            first = reporting.figures(result, Path(one), reporting.sha256(result_path), script_sha)
            second = reporting.figures(result, Path(two), reporting.sha256(result_path), script_sha)
            self.assertEqual([Path(one, Path(row["figure_path"]).name).read_bytes() for row in first["figures"]],
                             [Path(two, Path(row["figure_path"]).name).read_bytes() for row in second["figures"]])
            self.assertEqual(first["aggregate_sha256"], second["aggregate_sha256"])
        manifest = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FIGURE_MANIFEST.json").read_text())
        self.assertEqual(manifest["figure_count"], 5)
        for row in manifest["figures"]:
            self.assertEqual(reporting.sha256(ROOT / row["figure_path"]), row["figure_sha256"])

    def test_claim_and_execution_boundaries_unchanged(self):
        result = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json").read_text())
        self.assertEqual(result["base_result_sha256"], reporting.BASE_RESULT_SHA256)
        self.assertEqual(result["base_result"]["claim_ceiling"]["physical_validation"], "NOT_ESTABLISHED")
        self.assertEqual(result["openfoam_rerun"], "NOT_PERFORMED")
        self.assertEqual(result["sensitivity_rerun"], "NOT_PERFORMED")
        self.assertEqual(result["calibration"], "CLOSED_NO_REFIT")
        self.assertEqual(result["protected_scoring"], "NOT_PERFORMED")
        self.assertEqual(result["new_governing_physics"], "NOT_AUTHORIZED")

    def test_final_report_manifest_hash_consistency(self):
        manifest = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_REPORT_MANIFEST.json").read_text())
        for member in manifest["members"].values():
            self.assertEqual(reporting.sha256(ROOT / member["path"]), member["sha256"])
        self.assertEqual(manifest["immutable_inputs"]["base_b2_result_sha256"],
                         reporting.BASE_RESULT_SHA256)

    def test_final_result_closed_schema_top_level(self):
        schema = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT_SCHEMA.json").read_text())
        result = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json").read_text())
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(result), set(schema["required"]))
        self.assertEqual(set(schema["properties"]), set(schema["required"]))


if __name__ == "__main__":
    unittest.main()
