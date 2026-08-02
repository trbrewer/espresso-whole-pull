import hashlib
import importlib.util
import json
import math
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("val_case_001", ROOT / "scripts/val_case_001.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ValCase001Tests(unittest.TestCase):
    def test_deterministic_generation_and_parent_immutability(self):
        parents = {path: digest(ROOT / path) for path in MOD.PARENT_HASHES}
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = MOD.generate_stage_a(ROOT, pathlib.Path(first))
            b = MOD.generate_stage_a(ROOT, pathlib.Path(second))
            self.assertEqual(a, b)
            for record in a:
                name = record["case_id"] + ".json"
                self.assertEqual(digest(pathlib.Path(first) / "configs" / name),
                                 digest(pathlib.Path(second) / "configs" / name))
        self.assertEqual(parents, {path: digest(ROOT / path) for path in MOD.PARENT_HASHES})

    def test_parameter_bounds_and_direction(self):
        cfg = MOD.base_config(ROOT, "finite", "MACHINE_MID")
        baseline, plus = MOD.perturb(cfg, "phi0", 0.05)
        self.assertGreater(plus, baseline)
        self.assertLess(plus, 1.0)
        with self.assertRaises(ValueError):
            MOD.perturb(MOD.base_config(ROOT, "finite", "MACHINE_MID"), "phi0", 2.0)
        self.assertEqual(MOD.PRIMARY_FRACTIONS["pc"], 0.025)
        self.assertEqual(MOD.PRIMARY_FRACTIONS["pshut"], 0.025)
        self.assertEqual(MOD.HALF_FRACTIONS["pc"], 0.0125)
        self.assertEqual(MOD.HALF_FRACTIONS["pshut"], 0.0125)

    def test_central_and_one_sided_finite_difference(self):
        minus, base, plus = [1.0], [2.0], [5.0]
        self.assertAlmostEqual(MOD.finite_difference(minus, plus, 1.0, 3.0)[0], 2.0)
        self.assertAlmostEqual(MOD.finite_difference(None, plus, None, 3.0, base, 2.0)[0], 3.0)
        self.assertAlmostEqual(MOD.finite_difference(minus, None, 1.0, None, base, 2.0)[0], 1.0)

    def test_fixed_scale_normalization_handles_zero_observable(self):
        result = MOD.normalized_sensitivity([0.0, 2.0], 3.0, [1.0, 4.0])
        self.assertEqual(result, [0.0, 1.5])
        with self.assertRaises(ValueError):
            MOD.normalized_sensitivity([1.0], 1.0, [0.0])

    def test_nominal_endpoint_roundoff_clamps_only_within_tolerance(self):
        rows = [{"time_s": "0", "x": "1"}, {"time_s": "29.9999999999994", "x": "2"}]
        self.assertEqual(MOD.interp(rows, "x", 30.0), 2.0)
        with self.assertRaises(ValueError):
            MOD.interp(rows, "x", 30.000001)

    def test_jacobian_dimensions_and_finite_svd(self):
        jac = [[1.0, 0.0], [0.0, 2.0], [1.0, 1.0]]
        result = MOD.svd_summary(jac)
        self.assertEqual(result["dimensions"], [3, 2])
        self.assertTrue(all(math.isfinite(value) for value in result["singular_values"]))

    def test_deterministic_serialization(self):
        value = {"b": [2, 1], "a": 1}
        self.assertEqual(MOD.canonical_bytes(value), MOD.canonical_bytes(json.loads(MOD.canonical_bytes(value))))

    def test_centered_primary_and_supplemental_cosine_are_distinct(self):
        result = MOD.correlation([[100.0, 100.0], [101.0, 102.0], [102.0, 101.0]],
                                 ("left", "right"))
        pair = result["pair_diagnostics"][0]
        self.assertEqual(pair["primary_method"], "CENTERED_PEARSON")
        self.assertLess(abs(pair["centered_correlation"]), 0.95)
        self.assertGreater(pair["cosine_similarity"], 0.95)
        self.assertFalse(pair["primary_near_collinear"])
        self.assertTrue(pair["supplemental_cosine_near_collinear"])

    def test_constant_column_uses_cosine_fallback(self):
        pair = MOD.correlation([[2.0, 1.0], [2.0, 2.0], [2.0, 3.0]],
                               ("constant", "varying"))["pair_diagnostics"][0]
        self.assertIsNone(pair["centered_correlation"])
        self.assertEqual(pair["primary_method"],
                         "UNCENTERED_COSINE_FALLBACK_ZERO_CENTERED_NORM")
        self.assertIsNotNone(pair["primary_value"])

    def test_zero_column_is_explicitly_undefined(self):
        pair = MOD.correlation([[0.0, 1.0], [0.0, 2.0], [0.0, 3.0]],
                               ("zero", "varying"))["pair_diagnostics"][0]
        self.assertFalse(pair["defined"])
        self.assertIsNone(pair["primary_value"])
        self.assertIsNone(pair["cosine_similarity"])
        self.assertFalse(pair["primary_near_collinear"])
        self.assertEqual(pair["undefined_reason"],
                         "CENTERED_AND_COSINE_UNDEFINED_ZERO_NORM")

    def test_negative_and_exact_absolute_threshold(self):
        negative = MOD.correlation([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]],
                                   ("a", "b"))["pair_diagnostics"][0]
        self.assertAlmostEqual(negative["primary_value"], -1.0)
        self.assertTrue(negative["primary_near_collinear"])
        for value, expected in ((0.949999999999, False), (0.95, True),
                                (0.950000000001, True)):
            self.assertEqual(MOD.is_near_collinear(value), expected)

    def test_logarithmic_sensitivity_defined_and_undefined(self):
        records = MOD.logarithmic_sensitivity([2.0, 3.0, 4.0], 5.0,
                                              [10.0, 0.0, -1.0])
        self.assertEqual(records[0]["value"], 1.0)
        self.assertEqual(records[0]["disposition"], "DEFINED_POSITIVE_BASELINE")
        self.assertIsNone(records[1]["value"])
        self.assertIsNone(records[2]["value"])

    def test_zero_repeatability_denominator_is_explicit(self):
        self.assertEqual(MOD.exact_repeatability_relative(1.0, 0.0), {
            "value": None, "disposition": "UNDEFINED_ZERO_DENOMINATOR",
            "denominator": 0.0})

    def test_corrected_result_regressions_and_supplemental_cosines(self):
        corrected = json.loads((ROOT / "validation/cases/val_case_001/VAL_CASE_001_RESULTS.json").read_text())
        superseded = json.loads(subprocess.check_output([
            "git", "show", MOD.SUPERSEDED_COMMIT
            + ":validation/cases/val_case_001/VAL_CASE_001_RESULTS.json"],
            cwd=ROOT, text=True))
        expected = {
            "SET_A": {("Qfree", "Ru"): -0.7510065044413317,
                      ("Ru", "pshut"): -0.5214655798964295,
                      ("k0", "pc"): 0.9986439395384199,
                      ("k0", "phi0"): 0.9993432759777302,
                      ("pc", "phi0"): 0.9998744993660710},
            "SET_B": {("Qfree", "Ru"): -0.8829056531458825,
                      ("Ru", "pshut"): -0.9632316875121999},
            "SET_C": {("Qfree", "Ru"): -0.9522541036921677,
                      ("Ru", "pshut"): -0.9748127684142938},
            "SET_D": {("Qfree", "Ru"): -0.9580924168083030,
                      ("Ru", "pshut"): -0.9573958657715449},
        }
        for set_id, pairs in expected.items():
            current = corrected["observable_sets"][set_id]["correlation"]
            prior = superseded["observable_sets"][set_id]["correlation"]
            indices = {name: i for i, name in enumerate(current["parameters"])}
            for pair, value in pairs.items():
                i, j = indices[pair[0]], indices[pair[1]]
                self.assertAlmostEqual(current["centered_correlation_matrix"][i][j],
                                       value, places=12)
                self.assertEqual(current["cosine_similarity_matrix"][i][j],
                                 prior["cosine_matrix"][i][j])

    def test_corrected_result_only_declared_fields_differ(self):
        corrected = json.loads((ROOT / "validation/cases/val_case_001/VAL_CASE_001_RESULTS.json").read_text())
        superseded = json.loads(subprocess.check_output([
            "git", "show", MOD.SUPERSEDED_COMMIT
            + ":validation/cases/val_case_001/VAL_CASE_001_RESULTS.json"],
            cwd=ROOT, text=True))
        for value in (corrected, superseded):
            for key in ("schema_version", "correction_provenance", "review_status",
                        "baseline_feature_vectors", "local_logarithmic_sensitivities"):
                value.pop(key, None)
            for section in ("observable_sets", "stage_c_information"):
                for item in value[section].values():
                    item.pop("correlation", None)
            for item in value["model_form_separation"].values():
                item.pop("relative_to_maximum_exact_repeatability", None)
        self.assertEqual(corrected, superseded)

    def test_run_count_reconciliation(self):
        self.assertEqual(17 + 6 + 3 * (2 + 2 * len(MOD.STAGE_C_PARAMETERS)), 47)
        self.assertLessEqual(47, 80)

    def test_framework_pins_and_paths_immutable(self):
        manifest = json.loads((ROOT / "validation/cases/val_case_001/VAL_CASE_001_EVIDENCE_AND_INPUT_MANIFEST.json").read_text())
        self.assertEqual(manifest["framework"]["commit"], "a3e632d9deb3c4ac7c34fed079e4ed85bd370a30")
        self.assertEqual(manifest["framework"]["tree"], "3de55debf9272fb6bdac928a415996fd9e1fb8e9")
        self.assertEqual(digest(ROOT / "docs/validation/VALIDATION_OPERATING_STANDARD_V1.md"),
                         "1655e033a29570f71412ea065298f18c6227c40d7567c682ee6340ae6cf3bcc0")

    def test_claim_ceiling(self):
        protocol = (ROOT / "docs/validation/cases/VAL_CASE_001_PROTOCOL.md").read_text()
        self.assertIn("CLAIM_CEILING: VALIDATION_SUPPORT_ONLY", protocol)
        self.assertIn("PHYSICAL_VALIDATION: NOT_ESTABLISHED", protocol)
        self.assertIn("STRUCTURAL_IDENTIFIABILITY: NOT_ASSESSED", protocol)


if __name__ == "__main__":
    unittest.main()
