import copy
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "forchheimer_reference", ROOT / "scripts/forchheimer_reference.py"
)
REF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REF)
ANALYZER_SPEC = importlib.util.spec_from_file_location(
    "analyze_wp02_003", ROOT / "scripts/analyze_wp02_003_darcy_forchheimer.py"
)
ANALYZER = importlib.util.module_from_spec(ANALYZER_SPEC)
ANALYZER_SPEC.loader.exec_module(ANALYZER)


class ForchheimerReferenceTests(unittest.TestCase):
    def test_strict_si_wadsworth_value(self):
        expected = math.exp(-1.71588 * (1.77e-15) ** -0.08093)
        self.assertEqual(REF.wadsworth2026_ceramics_fit(1.77e-15), expected)
        for value in (0.0, -1.0, math.inf, math.nan):
            with self.assertRaises(ValueError):
                REF.wadsworth2026_ceramics_fit(value)

    def test_stable_root_and_zero_gradient(self):
        k, ki, mu, rho, g = 1.77e-15, 1e-10, 3.15e-4, 965.0, 1e8
        q = REF.velocity_from_gradient(g, k, ki, mu, rho)
        self.assertAlmostEqual(mu / k * q + rho / ki * q * q, g, delta=g * 2e-15)
        self.assertEqual(REF.velocity_from_gradient(0, k, ki, mu, rho), 0.0)

    def test_uniform_layered_and_darcy_limits(self):
        area, mu, rho = math.pi * .029**2, 3.15e-4, 965.0
        rd, ri = REF.series_resistance([.009], [1.77e-15], [1e-10], area, mu, rho)
        q = REF.flow_from_resistance(9e5, rd, ri)
        self.assertAlmostEqual(rd * q + ri * q * q, 9e5, delta=2e-9)
        layered = REF.series_resistance(
            [.003, .006], [1e-15, 3e-15], [2e-10, 7e-11], area, mu, rho
        )
        self.assertGreater(layered[0], 0)
        self.assertGreater(layered[1], 0)
        darcy = REF.flow_from_resistance(9e5, rd, 0)
        self.assertEqual(darcy, 9e5 / rd)
        errors = [
            abs(REF.flow_from_resistance(9e5, rd, ri / scale) / darcy - 1)
            for scale in (1, 1e3, 1e6)
        ]
        self.assertTrue(errors[0] > errors[1] > errors[2])

    def test_machine_operating_point_and_fraction_identity(self):
        result = REF.machine_operating_point(1.1e6, 0, 2e11, 3e11, 8e16)
        q = result["flow_m3_s"]
        self.assertAlmostEqual(result["basket_pressure_pa"], 1.1e6 - 2e11 * q)
        fo = REF.forchheimer_number(1e-14, 5e-4, 2e-9, 3e-4, 960)
        direct = (960 * (5e-4) ** 2 / 2e-9) / (
            3e-4 * 5e-4 / 1e-14 + 960 * (5e-4) ** 2 / 2e-9
        )
        self.assertAlmostEqual(REF.inertial_pressure_fraction(fo), direct, places=15)

    def test_run_spec_is_predeclared_and_bounded(self):
        spec = json.loads(
            (ROOT / "validation/wp02/WP02_003_DARCY_FORCHHEIMER_RUN_SPEC.json").read_text()
        )
        self.assertEqual(set(spec["case_matrix"]), {f"DF-{i}" for i in range(7)})
        self.assertEqual(spec["case_matrix"]["DF-0"]["flowResistanceModel"], "darcy")
        self.assertEqual(
            spec["claim_boundary"]["PHYSICAL_VALIDATION"], "NOT_ESTABLISHED"
        )

    def test_dual_closure_source_reconstruction(self):
        result = REF.reconstruct_wadsworth2026_source_fo_range()
        self.assertEqual(
            result["disposition"],
            "SOURCE_INTERNAL_CLOSURE_INCONSISTENCY_IDENTIFIED",
        )
        self.assertAlmostEqual(
            result["source_constants"]["mean_radii_m"][0], 145.105e-6, places=15
        )
        self.assertAlmostEqual(
            result["source_constants"]["mean_radii_m"][1], 275.620e-6, places=15
        )
        self.assertLess(
            max(abs(a - b) for a, b in zip(
                result["zhou_fo_range"], result["published_fo_range"]
            )),
            ANALYZER.SOURCE_PUBLISHED_BAND_ABSOLUTE_TOLERANCE,
        )
        self.assertAlmostEqual(result["zhou_fo_range"][0], .01613912805898314)
        self.assertAlmostEqual(result["zhou_fo_range"][1], .06380577674069203)
        self.assertAlmostEqual(result["ceramics_fo_range"][0], .010663146973690743)
        self.assertAlmostEqual(result["ceramics_fo_range"][1], .011843663314111309)


class FailClosedAnalyzerTests(unittest.TestCase):
    def passing(self):
        return {"gate_inputs": {
            "scalar_relative_error": 0.0,
            "uniform_flow_relative_error": 0.0,
            "uniform_decomposition_relative_error": 0.0,
            "layered_flow_relative_error": 0.0,
            "layered_interface_pressure_relative_error": 0.0,
            "machine_maximum_relative_error": 0.0,
            "darcy_limit_monotonic": True,
            "darcy_limit_finest_relative_error": 0.0,
            "exact_darcy_path_relative_error": 0.0,
            "failed_nonlinear_steps": 0,
            "machine_bracket_failures": 0,
            "machine_fallback_count": 0,
            "maximum_machine_flux_relative_difference": 0.0,
            "maximum_fine_pair_relative_change": 0.0,
            "fine_pair_machine_balance_absolute_change_m3": 0.0,
            "fine_pair_solute_balance_absolute_change_kg": 0.0,
            "source_reconstruction_deterministic": True,
            "source_reconstruction_positive_finite": True,
            "source_zhou_published_band_maximum_absolute_error": 0.0,
            "source_ceramics_result_retained": True,
            "source_inconsistency_disposition_correct": True,
            "production_zero_inertia_status": "PASS",
            "production_zero_inertia_maximum_relative_error": 0.0,
            "production_zero_inertia_all_values_finite": True,
            "production_zero_inertia_all_flows_nonnegative": True,
            "production_zero_inertia_machine_bracketed": True,
            "production_zero_inertia_machine_fallback_used": False,
            "r0_maximum_regression_error": 0.0,
            "wp02_002_mc2_regression_status": "PASS",
            "wp02_002_mc5_regression_status": "PASS",
            "wp02_coupling_disabled_regression_status": "PASS",
            "maximum_water_balance_residual_kg": 0.0,
            "maximum_solute_balance_residual_kg": 0.0,
            "maximum_machine_water_balance_residual_m3": 0.0,
            "all_cases_complete_and_finite": True,
            "wetting_maximum_absolute_difference": 0.0,
        }}

    def test_adversarial_corruptions_fail(self):
        corruptions = {
            "uniform": ("uniform_flow_relative_error", 1e-3),
            "layered": ("layered_flow_relative_error", 1e-3),
            "machine": ("machine_maximum_relative_error", 1e-3),
            "darcy_order": ("darcy_limit_monotonic", False),
            "nonlinear": ("failed_nonlinear_steps", 1),
            "flux": ("maximum_machine_flux_relative_difference", 1e-3),
            "refinement": ("maximum_fine_pair_relative_change", .01),
            "water": ("maximum_water_balance_residual_kg", 1e-3),
            "finite": ("all_cases_complete_and_finite", False),
            "source": ("source_reconstruction_deterministic", False),
            "r0": ("r0_maximum_regression_error", .01),
            "mc2": ("wp02_002_mc2_regression_status", "FAIL"),
            "mc5": ("wp02_002_mc5_regression_status", "FAIL"),
            "coupling_disabled":
                ("wp02_coupling_disabled_regression_status", "FAIL"),
        }
        self.assertTrue(ANALYZER.adjudicate(self.passing())["all_gates_pass"])
        for name, (key, value) in corruptions.items():
            with self.subTest(name=name):
                candidate = self.passing()
                candidate["gate_inputs"][key] = value
                self.assertFalse(
                    ANALYZER.adjudicate(candidate)["all_gates_pass"]
                )

    def test_corrupt_production_zero_inertia_fails_closed(self):
        candidate = self.passing()
        candidate["gate_inputs"][
            "production_zero_inertia_maximum_relative_error"
        ] = 1e-3
        result = ANALYZER.adjudicate(candidate)
        self.assertEqual(result["gates"]["production_zero_inertia_path"], "FAIL")
        self.assertFalse(result["all_gates_pass"])
        self.assertEqual(result["disposition"], "NUMERICAL_FAILURE")
        self.assertNotEqual(ANALYZER.result_exit_code(result), 0)


if __name__ == "__main__":
    unittest.main()
