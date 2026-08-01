import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest

import numpy as np


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
        minus, base, plus = np.array([1.0]), np.array([2.0]), np.array([5.0])
        self.assertAlmostEqual(MOD.finite_difference(minus, plus, 1.0, 3.0)[0], 2.0)
        self.assertAlmostEqual(MOD.finite_difference(None, plus, None, 3.0, base, 2.0)[0], 3.0)
        self.assertAlmostEqual(MOD.finite_difference(minus, None, 1.0, None, base, 2.0)[0], 1.0)

    def test_fixed_scale_normalization_handles_zero_observable(self):
        result = MOD.normalized_sensitivity(np.array([0.0, 2.0]), 3.0, np.array([1.0, 4.0]))
        np.testing.assert_allclose(result, [0.0, 1.5])
        with self.assertRaises(ValueError):
            MOD.normalized_sensitivity(np.array([1.0]), 1.0, np.array([0.0]))

    def test_jacobian_dimensions_and_finite_svd(self):
        jac = np.array([[1.0, 0.0], [0.0, 2.0], [1.0, 1.0]])
        result = MOD.svd_summary(jac)
        self.assertEqual(result["dimensions"], [3, 2])
        self.assertTrue(all(np.isfinite(result["singular_values"])))

    def test_deterministic_serialization(self):
        value = {"b": [2, 1], "a": 1}
        self.assertEqual(MOD.canonical_bytes(value), MOD.canonical_bytes(json.loads(MOD.canonical_bytes(value))))

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
