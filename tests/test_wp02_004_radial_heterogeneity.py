import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
import radial_heterogeneity_reference as ref  # noqa: E402
import analyze_wp02_004_radial_heterogeneity as analysis  # noqa: E402


class RadialReferenceTests(unittest.TestCase):
    def test_matched_profiles(self):
        for contrast, zone in ((4, "inner"), (4, "outer"), (16, "inner")):
            ki, ko = ref.matched_permeabilities(1.77e-15, .25, contrast, zone)
            self.assertLessEqual(abs((.25*ki+.75*ko)/1.77e-15-1), 3e-16)

    def test_darcy_parallel_and_metrics(self):
        areas = ref.zone_areas(.029, .0145)
        result = ref.radial_flow(9e5, .009011660896432553, 3e-4, 960,
                                 areas, (4.045714285714286e-15,
                                         1.0114285714285715e-15))
        metric = ref.metrics(areas, result["zone_flows_m3_s"])
        self.assertAlmostEqual(result["zone_flows_m3_s"][0]
                               /result["zone_flows_m3_s"][1], 4/3, places=14)
        self.assertAlmostEqual(metric["flow_fractions"][0], 4/7, places=14)
        self.assertGreater(metric["hydraulic_maldistribution_index"], 0)
        self.assertLess(metric["effective_hydraulic_area_fraction"], 1)

    def test_forchheimer_and_machine_roots(self):
        areas = ref.zone_areas(.029, .0145)
        path = lambda dp: ref.radial_flow(
            dp, .009011660896432553, 3e-4, 960, areas,
            (4.045714285714286e-15, 1.0114285714285715e-15),
            (2e-11, 9e-11))
        basket = ref.basket_operating_point(1e6, 0, 2e11, path)
        self.assertLess(abs(basket["basket_residual_pa"]), 1e-7)
        machine = ref.machine_step(10, .02, 7e5, 0, 2e-11, 2e11,
                                   7e-6, 1.2e6, 3, path)
        self.assertLess(abs(machine["upstream_residual_m3_s"]), 1e-18)

    def test_extraction_zero_state(self):
        result = ref.extraction_metrics((1, 3), (1, 3))
        self.assertEqual(result["extraction_maldistribution_index"], 0)
        self.assertEqual(result["extraction_fraction_cv"], 0)


class FailClosedTests(unittest.TestCase):
    def passing(self):
        return {key: value for key, value in {
            "all_cases_complete": True, "predecessor_max_error": 0.0,
            "equal_zone_max_error": 0.0, "darcy_fixture_max_error": 0.0,
            "forchheimer_fixture_max_error": 0.0,
            "machine_reference_max_error": 0.0,
            "conductance_identity_error": 0.0, "matched_total_flow_error": 0.0,
            "heterogeneous_flow_share_changed": True,
            "machine_hydraulic_error": 0.0, "zone_conservation_error": 0.0,
            "wetting_isolation_error": 0.0, "maximum_radial_velocity_ratio": 0.0,
            "maximum_total_flux_mismatch": 0.0,
            "maximum_zone_flux_mismatch": 0.0,
            "timestep_refinement_change": 0.0,
            "radial_mesh_refinement_change": 0.0,
            "failed_nonlinear_steps": 0, "finite_bounded_state": True,
            "maximum_water_residual_kg": 0.0,
            "maximum_solute_residual_kg": 0.0}.items()}

    def test_every_required_gate_passes(self):
        result = analysis.adjudicate({"gate_inputs": self.passing()})
        self.assertTrue(result["all_gates_pass"])
        self.assertEqual(set(result["gates"]), set(analysis.REQUIRED_GATES))

    def test_adversarial_corruptions_fail_closed(self):
        corruptions = {
            "zone_flow": ("darcy_fixture_max_error", 1),
            "matched_conductance": ("conductance_identity_error", 1),
            "machine_basket_pressure": ("machine_reference_max_error", 1),
            "zone_liquid_sum": ("zone_conservation_error", 1),
            "zone_solute_sum": ("zone_conservation_error", 1),
            "first_drip": ("wetting_isolation_error", 1),
            "radial_velocity": ("maximum_radial_velocity_ratio", 1),
            "total_flux": ("maximum_total_flux_mismatch", 1),
            "zone_flux": ("maximum_zone_flux_mismatch", 1),
            "timestep": ("timestep_refinement_change", 1),
            "mesh": ("radial_mesh_refinement_change", 1),
            "water": ("maximum_water_residual_kg", 1),
            "solute": ("maximum_solute_residual_kg", 1),
            "finite": ("finite_bounded_state", False),
        }
        for name, (key, value) in corruptions.items():
            with self.subTest(name=name):
                inputs = self.passing()
                inputs[key] = value
                result = analysis.adjudicate({"gate_inputs": inputs})
                self.assertFalse(result["all_gates_pass"])
                self.assertEqual(result["disposition"], "NUMERICAL_FAILURE")


if __name__ == "__main__":
    unittest.main()
