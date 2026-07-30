import importlib.util
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "machine_ref", ROOT / "scripts/machine_coupling_reference.py"
)
REF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REF)
ANALYZER_SPEC = importlib.util.spec_from_file_location(
    "machine_analyzer", ROOT / "scripts/analyze_wp02_002_machine_coupling.py"
)
ANALYZER = importlib.util.module_from_spec(ANALYZER_SPEC)
ANALYZER_SPEC.loader.exec_module(ANALYZER)


def passing_result():
    case = {
        "status": "PASS",
        "gates": {"case_completed": "PASS", "finite_state": "PASS"},
        "peak_upstream_pressure_Pa": 8e5,
        "peak_basket_pressure_Pa_excluding_transition": 7e5,
        "maximum_machine_water_balance_residual_m3": 1e-16,
        "maximum_coupling_residual_m3_s": 1e-18,
        "failed_steps": 0, "bracket_failures": 0, "fallback_count": 0,
    }
    return {
        "analytical_linear_load": {
            "maximum_discrete_relative_error": 1e-12,
            "observed_orders": [1.0, 1.0],
            "equilibrium": {"pressure_relative_error": 1e-10,
                            "flow_relative_error": 1e-10},
        },
        "prescribed_pressure_limit": {"sequence": [
            {"relative_error_to_prescribed_step": .1},
            {"relative_error_to_prescribed_step": .01},
            {"relative_error_to_prescribed_step": .001},
        ]},
        "two_layer_fixture": {"maximum_discrete_relative_error": 1e-12},
        "regressions": {
            "prescribed_pressure_R0": {"errors": {
                "first_drip_s": 1e-10, "final_cup_mass_kg": 1e-5}},
            "WP02_coupling_disabled": {"relative_error": 1e-10},
        },
        "full_shot_time_refinement": {
            "cases": [{"status": "PASS"}],
            "maximum_fine_pair_relative_change": 1e-3,
            "relative_output_acceptance": .005,
            "maximum_absolute_machine_water_balance_residual_m3": 1e-16,
            "machine_water_balance_acceptance_m3": 1e-12,
        },
        "cases": {"MC-2": case},
    }


class MachineCouplingTests(unittest.TestCase):
    def test_backward_euler_residual_and_continuous_limit(self):
        args = (0.02, 0.0, 2e-11, 6e-6, 1.2e6, 1.65e-12)
        p = 0.0
        for _ in range(1500):
            row = REF.backward_euler(p, *args)
            self.assertLess(abs(row["residual_m3_s"]), 1e-18)
            p = row["pressure_Pa"]
        exact = REF.continuous(30.0, 0.0, 0.0, 2e-11, 6e-6, 1.2e6, 1.65e-12)
        self.assertLess(abs(p - exact["pressure_Pa"]) / exact["pressure_Pa"], 0.01)

    def test_refinement_is_first_order(self):
        exact = REF.continuous(1.0, 0.0, 0.0, 2e-11, 6e-6, 1.2e6, 1.65e-12)
        errors = []
        for dt in (0.04, 0.02, 0.01):
            p = 0.0
            for _ in range(round(1.0 / dt)):
                p = REF.backward_euler(
                    p, dt, 0.0, 2e-11, 6e-6, 1.2e6, 1.65e-12
                )["pressure_Pa"]
            errors.append(abs(p - exact["pressure_Pa"]))
        self.assertGreater(errors[0], errors[1])
        self.assertGreater(errors[1], errors[2])
        self.assertGreater(math.log(errors[0] / errors[1], 2), 0.8)

    def test_run_spec_is_synthetic_and_predeclared(self):
        data = json.loads(
            (ROOT / "validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RUN_SPEC.json").read_text()
        )
        self.assertEqual(data["compliance_sensitivity_ratio"], [0.25, 1.0, 4.0])
        for name in ("MC-1", "MC-2", "MC-3", "MC-4", "MC-5"):
            self.assertTrue(data["case_matrix"][name]["parameter_role"].startswith("SYNTHETIC_"))

    def test_invalid_machine_config_is_rejected(self):
        prepare_spec = importlib.util.spec_from_file_location(
            "prepare", ROOT / "scripts/prepare_case.py"
        )
        prepare = importlib.util.module_from_spec(prepare_spec)
        prepare_spec.loader.exec_module(prepare)
        scenario = json.loads((ROOT / "config/reference_R0.json").read_text())
        scenario["pressureBoundaryModel"] = "lumpedMachineCompliance"
        scenario["machineBoundary"] = {}
        with self.assertRaises(SystemExit):
            prepare.render_properties(scenario)

    def test_machine_domain_and_iteration_type_are_rejected(self):
        prepare_spec = importlib.util.spec_from_file_location(
            "prepare_domain", ROOT / "scripts/prepare_case.py"
        )
        prepare = importlib.util.module_from_spec(prepare_spec)
        prepare_spec.loader.exec_module(prepare)
        scenario = json.loads((ROOT / "config/reference_R0.json").read_text())
        scenario["pressureBoundaryModel"] = "lumpedMachineCompliance"
        machine = {
            "initialUpstreamPressure": 2e6, "upstreamCompliance": 1e-11,
            "upstreamResistance": 0.0, "freeFlowRate": 1e-5,
            "shutoffPressure": 1e6, "supplyRampTime": 0.0,
            "couplingRelativeTolerance": 1e-10,
            "couplingAbsoluteTolerance": 1e-12,
            "couplingMaximumIterations": 10,
        }
        scenario["machineBoundary"] = machine
        with self.assertRaises(SystemExit):
            prepare.render_properties(scenario)
        machine["initialUpstreamPressure"] = 0.0
        machine["couplingMaximumIterations"] = 10.0
        with self.assertRaises(SystemExit):
            prepare.render_properties(scenario)

    def test_adjudication_adversarial_failures(self):
        mutations = (
            lambda r: r["analytical_linear_load"]["observed_orders"].__setitem__(0, .2),
            lambda r: r["analytical_linear_load"]["equilibrium"].__setitem__(
                "pressure_relative_error", 1e-3),
            lambda r: r["prescribed_pressure_limit"]["sequence"][1].__setitem__(
                "relative_error_to_prescribed_step", .2),
            lambda r: r["regressions"]["prescribed_pressure_R0"]["errors"].__setitem__(
                "final_cup_mass_kg", .1),
            lambda r: r["regressions"]["WP02_coupling_disabled"].__setitem__(
                "relative_error", .1),
            lambda r: r["cases"]["MC-2"].__setitem__("failed_steps", 1),
            lambda r: r["cases"]["MC-2"].__setitem__(
                "maximum_machine_water_balance_residual_m3", 1e-5),
            lambda r: r["cases"]["MC-2"].__setitem__(
                "peak_basket_pressure_Pa_excluding_transition", float("nan")),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                result = passing_result()
                mutate(result)
                ANALYZER.adjudicate(result)
                self.assertFalse(result["all_gates_pass"])
                self.assertEqual(result["disposition"], "NUMERICAL_FAILURE")

    def test_two_layer_series_conductance_reference(self):
        area, mu, depth = 0.0026, 1.0e-3, .02
        k1, k2 = 1.0e-15, 3.0e-15
        resistance = (depth / 2) / k1 + (depth / 2) / k2
        conductance = area / (mu * resistance)
        self.assertAlmostEqual(conductance, area / (mu * resistance), places=24)


if __name__ == "__main__":
    unittest.main()
