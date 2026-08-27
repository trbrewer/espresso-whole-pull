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
from tools.xsv_frac_001.observer import configured_species, trace_steps
from tools.xsv_frac_001.runner import BEHAVIORS, pure_matrix, same_numeric


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

    def test_r2_pure_hand_calculations_and_behavior_completeness(self):
        results = pure_matrix()
        self.assertEqual(len(results), 6)
        self.assertTrue(all(row["status"] == "PASS" for row in results))
        self.assertEqual(len(BEHAVIORS), 20)
        self.assertEqual(len(set(BEHAVIORS)), 20)

    def test_comparator_rejects_unequal_rows_without_prefix_truncation(self):
        self.assertFalse(same_numeric([{"x": "1"}], [{"x": "1"}, {"x": "2"}]))
        self.assertFalse(same_numeric([{"x": "1", "id": "a"}], [{"x": "1", "id": "b"}]))
        runner = (ROOT/"tools/xsv_frac_001/runner.py").read_text()
        self.assertNotIn("min(len(actual)", runner)

    def test_legacy_species_contract_comes_from_scenario(self):
        species = configured_species(self.scenario())
        self.assertEqual(species[0].species_id, "legacy_effective_solute")
        self.assertEqual(species[0].role, "legacyEffectiveSolute")
        self.assertAlmostEqual(species[0].initial_inventory_kg, .0056)

    def test_reduced_pde_route_removed_from_acceptance(self):
        self.assertFalse((ROOT/"tools/xsv_frac_001/reduced_solver.py").exists())
        runner = (ROOT/"tools/xsv_frac_001/runner.py").read_text()
        self.assertNotIn("reduced_parity", runner)

    def _trace_fixture(self, root, aggregate, species=None):
        aggregate_path = root/"postProcessing/wholePull/0"; aggregate_path.mkdir(parents=True)
        (aggregate_path/"traces.csv").write_text("time_s,cup_water_mass_kg,cup_solute_mass_kg\n"+"\n".join(aggregate)+"\n")
        if species is not None:
            species_path=root/"postProcessing/wholePullSpecies/0"; species_path.mkdir(parents=True)
            (species_path/"species_traces.csv").write_text("time_s,species_id,cup_solute_mass_kg\n"+"\n".join(species)+"\n")

    def test_trace_rejects_descending_time_and_decreasing_mass(self):
        scenario=self.scenario(); scenario["time"]["end_s"]=.2; scenario["time"]["delta_t_s"]=.1
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self._trace_fixture(root,["0.2,1,0.1","0.1,2,0.2"])
            with self.assertRaisesRegex(ValueError,"strictly increasing"): trace_steps(root,scenario)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self._trace_fixture(root,["0.1,1,0.1","0.2,0.5,0.2"])
            with self.assertRaisesRegex(ValueError,"decreasing"): trace_steps(root,scenario)

    def test_trace_rejects_missing_duplicate_and_misaligned_species(self):
        scenario=self.scenario(); scenario["time"]["end_s"]=.2; scenario["time"]["delta_t_s"]=.1
        scenario["extraction"]={"model":prepare.INDEXED_SPECIES_MODEL,"legacy_rate_constant_1_s":.15,"legacy_saturation_concentration_kg_m3":180,
          "species":[{"id":"a","role":"explicit_inventory","dry_coffee_inventory_mass_fraction":.28,"availability_fraction":1,"rate_constant_1_s":.15,"saturation_concentration_kg_m3":180,"effective_diffusivity_m2_s":0,"parameter_provenance":{k:"FIXED_STRUCTURAL_ASSUMPTION" for k in ("inventory","availability","rate","saturation","diffusivity")}}]}
        aggregate=["0.1,1,0.1","0.2,2,0.2"]
        for rows_value in (["0.1,a,0.1"],["0.1,a,0.1","0.1,a,0.1","0.2,a,0.2"],["0.1,a,0.1","0.3,a,0.2"]):
            with tempfile.TemporaryDirectory() as td:
                root=Path(td); self._trace_fixture(root,aggregate,rows_value)
                with self.assertRaises(ValueError): trace_steps(root,scenario)

    def test_trace_rejects_aggregate_species_increment_mismatch(self):
        scenario=self.scenario(); scenario["time"]["end_s"]=.1; scenario["time"]["delta_t_s"]=.1
        scenario["extraction"]={"model":prepare.INDEXED_SPECIES_MODEL,"species":[{"id":"a","role":"explicit_inventory","dry_coffee_inventory_mass_fraction":.28,"availability_fraction":1}]}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self._trace_fixture(root,["0.1,1,0.2"],["0.1,a,0.1"])
            with self.assertRaisesRegex(ValueError,"mismatch"): trace_steps(root,scenario)


if __name__ == "__main__": unittest.main()
