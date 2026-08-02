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
GATE_SPEC = importlib.util.spec_from_file_location(
    "wp03_002_gate", ROOT / "scripts" / "reduce_wp03_002_gate_evidence.py"
)
GATE = importlib.util.module_from_spec(GATE_SPEC)
GATE_SPEC.loader.exec_module(GATE)


class WP03002ReferenceTests(unittest.TestCase):
    def test_continuous_closure_is_diagnostic_not_convergence_gate(self):
        source = (ROOT / "solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text()
        match = re.search(
            r"const bool poroelasticIterationConverged\s*=.*?;", source, re.DOTALL
        )
        self.assertIsNotNone(match)
        convergence = match.group(0)
        self.assertIn("flowChange <= poroelasticRelativeTolerance", convergence)
        self.assertIn("pressureChange <= poroelasticAbsoluteTolerance", convergence)
        self.assertIn("pressureFinalResidual <= poroelasticAbsoluteTolerance", convergence)
        self.assertNotIn("poroelasticFlowClosureError", convergence)

    @staticmethod
    def gate_row(**updates):
        row = {
            "time": 1.0,
            "iteration": 2,
            "iterationFlow": 1.0e-6,
            "flowChange": 5.0e-10,
            "pressureChange": 5.0e-14,
            "pressureFinalResidual": 5.0e-14,
            "combinedResidual": 5.0e-10,
            "poroelasticFlowClosureError": 2.0e-13,
            "nonlinearRelativeTolerance": 1.0e-9,
            "nonlinearAbsoluteTolerance": 1.0e-13,
            "converged": "true",
        }
        row.update(updates)
        return row

    def test_independent_retained_gate_all_components_pass(self):
        result = GATE.evaluate_gate(self.gate_row(), "retained")
        self.assertTrue(result["independentConverged"])
        self.assertEqual(result["retained_gate_ratio"], 0.5)
        self.assertEqual(result["closure_ratio"], 2.0)

    def test_each_retained_component_fails_individually(self):
        cases = (
            {"flowChange": 2.0e-9, "combinedResidual": 2.0e-9},
            {"pressureChange": 2.0e-13, "combinedResidual": 5.0e-10},
            {"pressureFinalResidual": 2.0e-13, "combinedResidual": 5.0e-10},
        )
        for update in cases:
            with self.subTest(update=update):
                update["converged"] = "false"
                result = GATE.evaluate_gate(self.gate_row(**update), "retained")
                self.assertFalse(result["independentConverged"])

    def test_closure_veto_is_excluded_from_retained_gate(self):
        retained = GATE.evaluate_gate(self.gate_row(), "retained")
        self.assertTrue(retained["independentConverged"])
        predecessor_row = self.gate_row(
            combinedResidual=5.0e-10, converged="false"
        )
        predecessor = GATE.evaluate_gate(predecessor_row, "predecessor")
        self.assertFalse(predecessor["independentConverged"])

    def test_gate_reducer_fails_closed(self):
        invalid = (
            {"flowChange": None},
            {"pressureChange": float("nan")},
            {"converged": "false"},
            {"combinedResidual": 1.0e-20},
        )
        for update in invalid:
            with self.subTest(update=update):
                with self.assertRaises(GATE.GateEvidenceError):
                    GATE.evaluate_gate(self.gate_row(**update), "retained")

    def test_mixed_relative_and_absolute_tolerances(self):
        result = GATE.evaluate_gate(
            self.gate_row(
                flowChange=7.5e-10,
                pressureChange=2.5e-14,
                pressureFinalResidual=1.0e-14,
                combinedResidual=7.5e-10,
            ),
            "retained",
        )
        self.assertAlmostEqual(result["flow_ratio"], 0.75)
        self.assertAlmostEqual(result["pressure_ratio"], 0.25)
        self.assertAlmostEqual(result["linear_ratio"], 0.1)

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
