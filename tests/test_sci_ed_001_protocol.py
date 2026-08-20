import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sci_ed_001_protocol", ROOT / "scripts/sci_ed_001_protocol.py")
MOD = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = MOD; SPEC.loader.exec_module(MOD)


class SciEd001ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = ROOT / "validation/cases/sci_ed_001"
        cls.protocol = json.loads((cls.out / "SCI_ED_001_PROTOCOL.json").read_text())
        cls.matrix = json.loads((cls.out / "SCI_ED_001_CASE_MATRIX.json").read_text())
        cls.ledger = json.loads((cls.out / "MODEL_FAMILY_INCLUSION_LEDGER.json").read_text())

    def test_generation_is_byte_stable_and_canonical(self):
        self.assertEqual(MOD.verify()["status"], "PASS")
        for path in self.out.glob("*.json"):
            obj = json.loads(path.read_text())
            self.assertEqual(path.read_text(), MOD.canonical(obj))

    def test_family_inclusion_is_complete_not_best_fit(self):
        included = [x for x in self.ledger["rows"] if x["inclusion_status"] == "INCLUDED"]
        counts = {f: sum(x["family_id"] == f for x in included) for f in ("F_TPM", "F_SWELL", "F_FINES", "F_GENERIC")}
        self.assertEqual(counts, self.ledger["eligible_counts"])
        self.assertEqual(counts, {"F_TPM": 35, "F_SWELL": 72, "F_FINES": 4, "F_GENERIC": 35})
        self.assertFalse(any("best" in (x.get("inclusion_basis") or "").lower() for x in included))
        excluded_fines = [x for x in self.ledger["rows"] if x["family_id"] == "F_FINES" and x["inclusion_status"] != "INCLUDED"]
        self.assertEqual(len(excluded_fines), 92)
        self.assertTrue(all(x["scientific_role"] == "PROVENANCE_CONTROL" for x in excluded_fines))

    def test_programs_are_exact_and_bounded(self):
        doc = json.loads((self.out / "PRESSURE_PROGRAMS.json").read_text())
        self.assertEqual([p["program_id"] for p in doc["programs"]], [f"P{i}_" + s for i, s in enumerate(["CONST_5BAR", "CONST_9BAR", "CONST_11BAR", "UPSTEP_5_TO_11", "DOWNSTEP_11_TO_5", "PULSE_9_11_9", "UNLOAD_9_0_9", "CYCLE_5_11_5_11_5", "SLOW_RAMP_5_TO_9"])])
        for program in doc["programs"]:
            self.assertEqual(program["horizon_s"], 80.0)
            self.assertEqual(program["breakpoints"][0]["time_s"], 0.0)
            self.assertEqual(program["breakpoints"][-1]["time_s"], 80.0)
            self.assertTrue(all(0 <= x["pressure_pa_gauge"] <= 1_100_000 for x in program["breakpoints"]))

    def test_preconditioning_and_clocks_are_frozen(self):
        pre = self.protocol["preconditioning"]
        self.assertEqual(pre["pressure_pa_gauge"], 500000.0)
        self.assertAlmostEqual(pre["duration_s"], pre["full_wetting_upper_bound_s"] + pre["safety_margin_s"])
        self.assertEqual(pre["safety_margin_s"], 1.0)
        self.assertFalse(pre["state_reset_at_design_clock"])
        self.assertEqual(pre["fines_start"], "SYNTHETIC_WINDOW_START_RESET")

    def test_matrix_ids_counts_and_authority_are_stable(self):
        rows = self.matrix["rows"]
        self.assertEqual(self.matrix["row_count"], 2628)
        self.assertEqual(len(rows), len({r["row_id"] for r in rows}))
        self.assertTrue(all(r["source_model_hash"] and r["source_parameter_hash"] for r in rows))
        self.assertEqual({r["resolution_id"] for r in rows}, {"BASE", "REFINED"})
        self.assertEqual({r["program_id"] for r in rows}, {p["program_id"] for p in MOD.programs()})
        self.assertTrue(all(r["adjudicative"] for r in rows))

    def test_uncertainty_is_interval_not_gaussian(self):
        noise = json.loads((self.out / "PLANNING_NOISE_MODEL.json").read_text())
        self.assertIn("INTERVAL", noise["method"])
        self.assertNotIn("GAUSSIAN", noise["method"])
        self.assertEqual(noise["scenarios"][1]["fines"], "FINES_MEASUREMENT_TARGET_NOT_PROVIDED")
        self.assertEqual(noise["scenarios"][1]["targets_si"]["outlet_volume_flow_m3_s"], 2e-8)

    def test_no_combined_family_or_adaptive_row(self):
        families = json.loads((self.out / "MODEL_FAMILY_REGISTRY.json").read_text())["families"]
        self.assertFalse(any("COMBINED" in x["name"] for x in families))
        self.assertEqual(self.matrix["adaptive_row_insertion"], "FORBIDDEN")
        self.assertEqual(self.protocol["execution"]["adaptive_rows"], "FORBIDDEN")

    def test_source_bindings_are_exact(self):
        source = json.loads((self.out / "SOURCE_BINDING.json").read_text())
        self.assertEqual(source["starting_head"], MOD.START_HEAD)
        self.assertEqual(source["starting_tree"], MOD.START_TREE)
        for binding in source["bindings"]:
            self.assertEqual(MOD.sha(ROOT / binding["path"]), binding["sha256"])
            self.assertEqual(binding["access"], "READ_ONLY")
        self.assertEqual((source["puckworks_calls"], source["openfoam_launches"], source["rpa_executions"]), (0, 0, 0))


if __name__ == "__main__": unittest.main()
