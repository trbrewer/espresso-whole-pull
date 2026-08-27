import copy
import importlib.util
import json
import math
import sys
import tempfile
import unittest
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("prepare_case_xsv", ROOT/"scripts/prepare_case.py")
prepare = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(prepare)
from tools.xsv_frac_001.fraction_collector import FractionCollector, Species
from tools.xsv_frac_001.observer import configured_species, trace_steps, validate_manifest_source
from tools.xsv_frac_001.runner import BEHAVIORS, main as runner_main, pure_matrix, resolution_diagnostic, same_numeric
from tools.xsv_frac_001.build_receipt import create_receipt, validate_receipt


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

    def _receipt_fixture(self, root, role="candidate"):
        for relative in ("solver/espressoWholePullFoam/espressoWholePullFoam.C","solver/espressoWholePullFoam/Make/files","solver/espressoWholePullFoam/Make/options"):
            path=root/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(relative)
        executable=root/"evidence"/f"solver-{role}"; executable.parent.mkdir(); executable.write_bytes(b"binary-"+role.encode())
        subprocess.run(["git","init","-q"],cwd=root,check=True); subprocess.run(["git","config","user.email","test@example.invalid"],cwd=root,check=True); subprocess.run(["git","config","user.name","test"],cwd=root,check=True); subprocess.run(["git","remote","add","origin","https://example.invalid/repo.git"],cwd=root,check=True); subprocess.run(["git","add","solver"],cwd=root,check=True); subprocess.run(["git","commit","-qm","fixture"],cwd=root,check=True)
        old=(os.environ.get("WM_PROJECT"),os.environ.get("WM_PROJECT_VERSION")); os.environ["WM_PROJECT"]="OpenFOAM"; os.environ["WM_PROJECT_VERSION"]="12"
        receipt=create_receipt(root,executable,role,"./Allwmake")
        if old[0] is None: os.environ.pop("WM_PROJECT",None)
        else: os.environ["WM_PROJECT"]=old[0]
        if old[1] is None: os.environ.pop("WM_PROJECT_VERSION",None)
        else: os.environ["WM_PROJECT_VERSION"]=old[1]
        path=root/f"{role}.json"; path.write_text(json.dumps(receipt)); return path,receipt,executable

    def test_build_receipt_rejects_authority_role_fields_and_stale_binary(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); path,receipt,executable=self._receipt_fixture(root); commit=receipt["git_commit"]; tree=receipt["git_tree"]
            validate_receipt(path,"candidate",commit,tree)
            mutations=(("wrong candidate commit",lambda r:r.update(git_commit="0"*40)),("wrong candidate tree",lambda r:r.update(git_tree="0"*40)),("missing field",lambda r:r.pop("build_command")),("baseline as candidate",lambda r:r.update(role="baseline")))
            for label,mutate in mutations:
                with self.subTest(label=label):
                    bad=copy.deepcopy(receipt); mutate(bad); path.write_text(json.dumps(bad))
                    with self.assertRaises(ValueError): validate_receipt(path,"candidate",commit,tree)
            path.write_text(json.dumps(receipt)); executable.write_bytes(b"altered")
            with self.assertRaisesRegex(ValueError,"altered"): validate_receipt(path,"candidate",commit,tree)
            executable.unlink()
            with self.assertRaises(ValueError): validate_receipt(path,"candidate",commit,tree)

    def test_build_receipt_rejects_baseline_authority_dirty_and_source_change(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); path,receipt,_=self._receipt_fixture(root,"baseline"); commit=receipt["git_commit"]; tree=receipt["git_tree"]
            with self.assertRaises(ValueError): validate_receipt(path,"baseline","0"*40,tree)
            with self.assertRaises(ValueError): validate_receipt(path,"baseline",commit,"0"*40)
            source=root/"solver/espressoWholePullFoam/espressoWholePullFoam.C"; source.write_text("dirty")
            with self.assertRaisesRegex(ValueError,"clean"): validate_receipt(path,"baseline",commit,tree)
            subprocess.run(["git","checkout","--",str(source)],cwd=root,check=True)
            altered=copy.deepcopy(receipt); altered["production_solver_source_sha256"]="0"*64; path.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError,"bundle"): validate_receipt(path,"baseline",commit,tree)

    def test_runner_requires_both_receipts_and_has_no_implicit_binary_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(SystemExit): runner_main(["--work-root",td,"--candidate-build-receipt","missing"])
        text=(ROOT/"tools/xsv_frac_001/runner.py").read_text()
        self.assertNotIn("FOAM_USER_APPBIN",text); self.assertIn("required=True",text)

    def test_manifest_source_binding_rejects_mismatch(self):
        validate_manifest_source({"production_source_sha256":"a"},"a")
        with self.assertRaises(AssertionError): validate_manifest_source({"production_source_sha256":"a"},"b")

    def test_resolution_diagnostic_requires_structure_and_reports_all_pairs(self):
        header="fraction_index,status,requested_lower_cumulative_beverage_mass_kg,requested_upper_cumulative_beverage_mass_kg,water_mass_kg,total_solute_mass_kg,beverage_mass_kg,end_time_s\n"
        sheader="fraction_index,species_index,species_id,species_role,species_mass_kg,cumulative_species_mass_kg\n"
        with tempfile.TemporaryDirectory() as td:
            cases={}
            for i,name in enumerate(("coarse","middle","fine")):
                case=Path(td)/name/"postProcessing/wholePullFractions/0"; case.mkdir(parents=True); (case/"fractions.csv").write_text(header+f"1,complete,0,1,{1+i*1e-6},{.1+i*1e-7},{1.1+i*1.1e-6},{1+i*.01}\n"); (case/"fraction_species.csv").write_text(sheader+f"1,0,a,explicitInventory,{.1+i*1e-7},{.1+i*1e-7}\n"); cases[name]=case.parents[2]
            result=resolution_diagnostic(cases,["coarse","middle","fine"])
            self.assertEqual(result["status"],"PASS"); self.assertEqual(len(result["comparisons"]),3); self.assertFalse(result["physical_convergence_claim"]); self.assertEqual(result["classification"],"UNDERLYING_PDE_RESOLUTION_DIAGNOSTIC_SENSITIVE")
            (Path(cases["fine"])/"postProcessing/wholePullFractions/0/fractions.csv").write_text(header)
            self.assertEqual(resolution_diagnostic(cases,["coarse","middle","fine"])["status"],"FAIL")


if __name__ == "__main__": unittest.main()
