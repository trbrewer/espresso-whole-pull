import importlib.util
import math
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "wp03_002_reference", ROOT / "scripts" / "wp03_002_reference.py"
)
REF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REF)


class WP03002ReferenceTests(unittest.TestCase):
    def test_continuous_closure_is_diagnostic_not_convergence_gate(self):
        source = (ROOT / "solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text()
        match = re.search(r"if\s*\(\s*flowChange.*?\)\s*\{", source, re.DOTALL)
        self.assertIsNotNone(match)
        convergence = match.group(0)
        self.assertIn("flowChange <= poroelasticRelativeTolerance", convergence)
        self.assertIn("pressureChange <= poroelasticAbsoluteTolerance", convergence)
        self.assertIn("pressureFinalResidual <= poroelasticAbsoluteTolerance", convergence)
        self.assertNotIn("poroelasticFlowClosureError", convergence)

    def test_integral_derivative_matches_permeability_ratio(self):
        for phi in (0.2, 0.4, 0.7):
            for x in (0.01, 0.2, 0.5, 0.85):
                step = 1.0e-6
                derivative = (
                    REF.poroelastic_integral(x + step, phi)
                    - REF.poroelastic_integral(x - step, phi)
                ) / (2.0 * step)
                self.assertAlmostEqual(
                    derivative, REF.permeability_ratio(x, phi), delta=5.0e-10
                )

    def test_integral_is_monotone_and_positive(self):
        for phi in (0.1, 0.4, 0.8):
            values = [REF.poroelastic_integral(i / 20.0, phi) for i in range(20)]
            self.assertEqual(values[0], 0.0)
            self.assertTrue(all(a < b for a, b in zip(values, values[1:])))

    def test_declared_domain_fails_closed(self):
        for x, phi in ((-0.1, 0.4), (1.1, 0.4), (0.5, 0.0), (0.5, 1.0)):
            with self.assertRaises(ValueError):
                REF.poroelastic_integral(x, phi)

    def test_integral_is_finite_near_declared_limit(self):
        value = REF.poroelastic_integral(math.nextafter(1.0, 0.0), 0.4)
        self.assertTrue(math.isfinite(value))
        self.assertGreater(value, 0.0)


if __name__ == "__main__":
    unittest.main()
