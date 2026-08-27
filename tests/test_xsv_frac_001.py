import copy
import importlib.util
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("prepare_case_xsv", ROOT/"scripts/prepare_case.py")
prepare = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(prepare)
from tools.xsv_frac_001.fraction_collector import FractionCollector, Species
from tools.xsv_frac_001.reduced_solver import tridiagonal


class XsvFrac001Tests(unittest.TestCase):
    def scenario(self):
        return json.loads((ROOT/"config/reference_R0.json").read_text())

    def enabled(self):
        return {"enabled": True, "boundaryBasis": "cumulativeBeverageMass",
                "cumulativeBoundariesKg": [.004, .0095, .015],
                "emitTerminalPartial": False}

    def test_configuration_and_legacy_absence(self):
        scenario = self.scenario()
        before = prepare.render_properties(scenario)
        self.assertIsNone(prepare.fraction_collection_contract(scenario))
        scenario["fractionCollection"] = self.enabled()
        contract = prepare.fraction_collection_contract(scenario)
        self.assertEqual(contract["boundaries"], [.004, .0095, .015])
        self.assertIn("boundaryBasis cumulativeBeverageMass", prepare.render_properties(scenario))
        del scenario["fractionCollection"]
        self.assertEqual(before, prepare.render_properties(scenario))

    def test_disabled_is_strict_and_preserves_rendering(self):
        scenario = self.scenario(); baseline = prepare.render_properties(scenario)
        scenario["fractionCollection"] = {"enabled": False}
        self.assertEqual(baseline, prepare.render_properties(scenario))
        scenario["fractionCollection"]["emitTerminalPartial"] = False
        with self.assertRaises(SystemExit): prepare.fraction_collection_contract(scenario)

    def test_invalid_fraction_configurations(self):
        mutations = [
            lambda x: x.pop("cumulativeBoundariesKg"),
            lambda x: x.update(cumulativeBoundariesKg=[]),
            lambda x: x.update(cumulativeBoundariesKg=[0]),
            lambda x: x.update(cumulativeBoundariesKg=[-1]),
            lambda x: x.update(cumulativeBoundariesKg=[1, 1]),
            lambda x: x.update(cumulativeBoundariesKg=[2, 1]),
            lambda x: x.update(cumulativeBoundariesKg=[math.nan]),
            lambda x: x.update(cumulativeBoundariesKg=[math.inf]),
            lambda x: x.update(boundaryBasis="time"),
            lambda x: x.update(enabled=1),
            lambda x: x.update(emitTerminalPartial=0),
            lambda x: x.update(extra=True),
            lambda x: x.update(cumulativeBoundariesKg=list(range(1, 10002))),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                scenario = self.scenario(); value = self.enabled(); mutate(value)
                scenario["fractionCollection"] = value
                with self.assertRaises(SystemExit): prepare.fraction_collection_contract(scenario)

    def collector(self, boundaries=(1, 2), terminal=False):
        return FractionCollector(boundaries,
            [Species("a", "explicitInventory", 10), Species("b", "structuralBalance", 10)], terminal)

    def test_exact_and_multiple_boundaries_and_zero_step(self):
        c = self.collector((1, 2, 3))
        c.add_step(0, 1, 0, [0, 0])
        c.add_step(1, 2, 2, [.5, .5])
        rows = c.finish()
        self.assertEqual(len(rows), 3)
        self.assertEqual([r["realized_upper_cumulative_beverage_mass_kg"] for r in rows], [1,2,3])
        self.assertEqual([r["end_time_s"] for r in rows], [1+2/3, 1+4/3, 3])
        for row in rows:
            self.assertLessEqual(abs(row["water_plus_solute_closure_residual_kg"]), 1e-12)
            self.assertLessEqual(abs(row["species_sum_closure_residual_kg"]), 1e-12)

    def test_terminal_partial_enabled_and_disabled(self):
        for enabled, count in ((False, 0), (True, 1)):
            c = self.collector((2,), enabled); c.add_step(0, 1, .5, [.1, .1])
            rows = c.finish(); self.assertEqual(len(rows), count)
            if enabled: self.assertEqual(rows[0]["status"], "partial")

    def test_species_mismatch_and_negative_fail_closed(self):
        c = self.collector()
        with self.assertRaises(ValueError): c.add_step(0, 1, 1, [.1, .1], .3)
        with self.assertRaises(ValueError): c.add_step(0, 1, -1, [0, 0])

    def test_deterministic_output_and_portability(self):
        def run():
            c = self.collector((.7, 1.4), True); c.add_step(0, 1, 1, [.2, .2]); return c.finish()
        self.assertEqual(run(), run())
        for path in (ROOT/"tools/xsv_frac_001").glob("*.py"):
            text = path.read_text()
            self.assertNotIn("import numpy", text); self.assertNotIn("import scipy", text)

    def test_onboarding_routes_current_development_correctly(self):
        text = (ROOT/"docs/ONBOARDING.md").read_text()
        inexpensive = text.split("## Inexpensive checks", 1)[1]
        command_block = inexpensive.split("```bash",1)[1].split("```",1)[0]
        self.assertNotIn("verify_no_physics_change.py", command_block)
        self.assertIn("verify_v0_1_4_baseline_integrity.py", command_block)
        self.assertIn("historical", inexpensive)
        self.assertIn("not a routine", inexpensive)

    def test_cpp_source_contract(self):
        text = (ROOT/"solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text()
        for token in ("fractionCollection", "wholePullFractions", "piecewise_constant_step_flux_mass_partition", "legacy_effective_solute"):
            self.assertIn(token, text)

    def test_standard_library_tridiagonal_solver(self):
        solution = tridiagonal([-1, -1], [2, 2, 2], [-1, -1], [1, 0, 1])
        for value in solution:
            self.assertAlmostEqual(value, 1.0, places=15)


if __name__ == "__main__": unittest.main()
