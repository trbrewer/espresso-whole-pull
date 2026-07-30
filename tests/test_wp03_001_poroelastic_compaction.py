"""WP03-001 constitutive, configuration, and fail-closed result tests."""

import importlib.util
import json
import math
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
import poroelastic_compaction_reference as reference

SPEC = importlib.util.spec_from_file_location(
    "wp03_analyzer", ROOT/"scripts/analyze_wp03_001_poroelastic_compaction.py")
analyzer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analyzer)


REQUIRED_GATES = (
  "r0_regression", "wp02_001_regression", "wp02_002_mc2_regression",
  "wp02_003_regression", "wp02_004_regression",
  "local_constitutive_reference",
  "exact_finite_phi_scalar_flow", "universal_limit_recovery",
  "source_model_parity", "source_domain_classification",
  "openfoam_pressure_profile_reference", "rigid_bed_limit",
  "matched_reference_identity", "machine_operating_point_reference",
  "machine_field_flux_consistency", "wetting_isolation",
  "nonlinear_convergence", "timestep_refinement", "axial_mesh_refinement",
  "bounded_state", "water_conservation", "solute_conservation",
  "fixed_transport_porosity_contract", "case_completion")


CORRUPTIONS = [
  ("local porosity", "local_constitutive_reference"),
  ("permeability ratio", "local_constitutive_reference"),
  ("exact scalar flow", "exact_finite_phi_scalar_flow"),
  ("universal-limit ordering", "universal_limit_recovery"),
  ("source constant", "source_model_parity"),
  ("pressure probe", "openfoam_pressure_profile_reference"),
  ("rigid output", "rigid_bed_limit"),
  ("matched identity", "matched_reference_identity"),
  ("machine basket pressure", "machine_operating_point_reference"),
  ("machine field flow", "machine_field_flux_consistency"),
  ("first drip", "wetting_isolation"),
  ("nonlinear convergence", "nonlinear_convergence"),
  ("critical stress", "bounded_state"),
  ("timestep result", "timestep_refinement"),
  ("axial mesh result", "axial_mesh_refinement"),
  ("water balance", "water_conservation"),
  ("solute balance", "solute_conservation"),
  ("transport porosity", "fixed_transport_porosity_contract"),
  ("final trace time", "case_completion"),
]

PREDECESSOR_GATES = {
    "r0": "r0_regression",
    "wp02_001": "wp02_001_regression",
    "wp02_002_mc2": "wp02_002_mc2_regression",
    "wp02_003": "wp02_003_regression",
    "wp02_004": "wp02_004_regression"}


class PoroelasticReferenceTests(unittest.TestCase):
    def test_reference_constitutive_bounds_and_identity(self):
        pc = 1239155
        for phi in (0.1, 0.4, 0.8):
            for x in (0, 0.1, 0.5, 0.8, 0.95):
                sigma = x*pc
                e = reference.strain(sigma, phi, pc)
                mechanical = reference.mechanical_porosity(sigma, phi, pc)
                ratio = reference.permeability_ratio(sigma, phi, pc)
                self.assertTrue(0 <= e < phi)
                self.assertTrue(0 < mechanical <= phi)
                self.assertTrue(0 < ratio <= 1)

    def test_independent_integral_and_universal_limit(self):
        x = 0.8
        errors = [
            abs(float(reference.integrate_j(x, phi))*4
                - float(reference.universal_qhat(x)))
            for phi in (1e-2, 1e-4, 1e-8)
        ]
        self.assertLess(errors[2], errors[1])
        self.assertLess(errors[1], errors[0])
        self.assertLess(errors[-1], 1e-8)

    def test_matched_reference_identity(self):
        k = 1.77e-15
        pc, phi, pressure = 1239155, 0.4, 900000
        matched = reference.matched_permeability(k, pressure, pc, phi)
        area, depth, mu = math.pi*0.029**2, 0.009011660896432553, 0.000315
        nonlinear = reference.flow(pressure, area, depth, mu, phi, pc, matched)
        darcy = area*k*pressure/(mu*depth)
        self.assertLessEqual(abs(float(nonlinear)-darcy)/darcy, 1e-12)

    def test_source_conversion_is_deterministic(self):
        value = reference.source_stress_free_permeability(
            1.8969919954879988, 965, 0.000315, 0.01,
            math.pi*0.028**2, 1239155, 0.122)
        self.assertAlmostEqual(
            float(value)/7.914139692656864e-15, 1.0, places=13)

    def test_prepare_case_rejects_invalid_compaction(self):
        invalid_values = [
            {"stressFreePorosity": 0}, {"stressFreePorosity": 1},
            {"criticalCompactionPressurePa": 0},
            {"stressFreePermeabilityM2": -1},
            {"nonlinearRelativeTolerance": 0},
            {"nonlinearAbsoluteTolerance": math.inf},
            {"nonlinearMaximumIterations": 0},
            {"nonlinearUnderRelaxation": 1.1},
            {"machineFluxRelativeTolerance": 0}]
        for invalid in invalid_values:
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                tmp_path = pathlib.Path(directory)
                cfg = json.loads((ROOT/"config/reference_R0.json").read_text())
                cfg["bedMechanicsModel"] = "waszkiewiczQuasiStaticCompaction"
                cfg["poroelasticCompaction"] = {
                  "model":"waszkiewicz2025FinitePhi", "stressFreePorosity":0.4,
                  "criticalCompactionPressurePa":1239155,
                  "stressFreePermeabilityM2":4.74023506749502e-15,
                  "nonlinearRelativeTolerance":1e-10,
                  "nonlinearAbsoluteTolerance":1e-10,
                  "nonlinearMaximumIterations":100,
                  "nonlinearUnderRelaxation":0.7,
                  "machineFluxRelativeTolerance":1e-6}
                cfg["poroelasticCompaction"].update(invalid)
                path = tmp_path/"bad.json"
                path.write_text(json.dumps(cfg))
                result = subprocess.run([
                    sys.executable, str(ROOT/"scripts/prepare_case.py"),
                    "--root", str(ROOT), "--config", str(path),
                    "--case-dir", str(tmp_path/"case"), "--nprocs", "1"],
                    text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)

    def test_each_adversarial_corruption_fails_closed(self):
        for corruption, gate in CORRUPTIONS:
            with self.subTest(corruption=corruption):
                gates = {name: True for name in REQUIRED_GATES}
                gates[gate] = False
                passed, disposition = analyzer.adjudicate_gates(gates)
                self.assertFalse(passed)
                self.assertEqual(disposition, "NUMERICAL_FAILURE")

    def test_production_fixture_value_corruption_exits_nonzero(self):
        retained = json.loads(
            (ROOT/"validation/wp03/WP03_001_POROELASTIC_COMPACTION_RESULTS.json")
            .read_text())["production_fixture"]
        self.assertIn("local_constitutive_values", retained)
        with tempfile.TemporaryDirectory() as directory:
            directory = pathlib.Path(directory)
            fixture = directory/"fixture.json"
            output = directory/"result.json"
            fixture.write_text(json.dumps(retained))
            baseline = subprocess.run([
                sys.executable,
                str(ROOT/"scripts/analyze_wp03_001_poroelastic_compaction.py"),
                "--check-production-fixture", str(fixture),
                "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(baseline.returncode, 0, baseline.stderr)
            retained["local_constitutive_values"][7][
                "productionMechanicalPorosity"] *= 1.01
            fixture.write_text(json.dumps(retained))
            corrupted = subprocess.run([
                sys.executable,
                str(ROOT/"scripts/analyze_wp03_001_poroelastic_compaction.py"),
                "--check-production-fixture", str(fixture),
                "--output", str(output)], capture_output=True, text=True)
            result = json.loads(output.read_text())
            self.assertNotEqual(corrupted.returncode, 0)
            self.assertFalse(result["gates"]["local_constitutive_reference"])
            self.assertFalse(result["all_gates_pass"])
            self.assertEqual(result["disposition"], "NUMERICAL_FAILURE")

    def test_each_numerical_predecessor_corruption_fails_its_gate(self):
        retained = json.loads(
            (ROOT/"validation/wp03/WP03_001_POROELASTIC_COMPACTION_RESULTS.json")
            .read_text())["predecessor_regressions"]
        for predecessor, gate in PREDECESSOR_GATES.items():
            with self.subTest(predecessor=predecessor):
                comparisons = json.loads(json.dumps(retained))
                metric = next(iter(
                    comparisons[predecessor]["metric_errors"]))
                comparisons[predecessor]["metric_errors"][metric] = 1.0
                comparisons[predecessor]["maximum_relative_error"] = max(
                    comparisons[predecessor]["metric_errors"].values())
                gates = analyzer.predecessor_gate_results(comparisons)
                self.assertFalse(gates[gate])
                passed, disposition = analyzer.adjudicate_gates(gates)
                self.assertFalse(passed)
                self.assertEqual(disposition, "NUMERICAL_FAILURE")

    def test_empty_gate_set_fails_closed(self):
        self.assertEqual(
            analyzer.adjudicate_gates({}), (False, "NUMERICAL_FAILURE"))


if __name__ == "__main__":
    unittest.main()
