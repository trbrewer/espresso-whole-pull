import gzip, importlib.util, json, math, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sci_ed_001_runner",ROOT/"scripts/sci_ed_001.py")
MOD=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=MOD;SPEC.loader.exec_module(MOD)

class SciEd001RunnerTests(unittest.TestCase):
    def test_pressure_program_exact_breakpoints_and_linear_ramps(self):
        progs=MOD.program_lookup()
        self.assertEqual(MOD.pressure(progs["P3_UPSTEP_5_TO_11"],20.5),800000.)
        self.assertEqual(MOD.pressure(progs["P6_UNLOAD_9_0_9"],25),0.)
        self.assertEqual(MOD.pressure(progs["P8_SLOW_RAMP_5_TO_9"],5),700000.)
        grid=MOD.time_grid(progs["P7_CYCLE_5_11_5_11_5"],.02)
        for t in (MOD.TPRE,MOD.TPRE+15,MOD.TPRE+16,MOD.TPRE+30,MOD.TPRE+31,MOD.TPRE+45,MOD.TPRE+46,MOD.TPRE+80):self.assertIn(t,grid)

    def test_units_nodes_and_signs_from_one_row_per_family(self):
        matrix=MOD.load("SCI_ED_001_CASE_MATRIX.json")["rows"]
        for family in ("F_TPM","F_SWELL","F_FINES","F_GENERIC"):
            row=next(x for x in matrix if x["family_id"]==family and x["program_id"]=="P6_UNLOAD_9_0_9" and x["resolution_id"]=="BASE")
            record=MOD.run_row(row);traj=record["trajectory"]
            self.assertTrue(all(x["pressure_pa"]>=0 and x["outlet_flow_m3_s"]>=0 and x["outlet_flow_kg_s"]>=0 for x in traj))
            self.assertTrue(all(b["cumulative_mass_kg"]>=a["cumulative_mass_kg"] for a,b in zip(traj,traj[1:])))

    def test_denominator_floor_and_missing_outputs(self):
        row={"design_time_s":0.,"outlet_flow_m3_s":0.,"apparent_resistance_pa_s_m3":None}
        self.assertIsNone(row["apparent_resistance_pa_s_m3"])
        matrix=MOD.load("OBSERVABLE_COMPATIBILITY_MATRIX.json")["rows"]
        saturated=[x for x in matrix if x["family_id"]=="F_TPM" and x["observable_id"]=="first_drip"]
        self.assertEqual(saturated[0]["status"],"NOT_PREDICTED_BY_FAMILY")

    def test_interval_classification(self):
        self.assertEqual(MOD.classify((0,1),(2,3)),("ROBUSTLY_SEPARATED",1))
        status,margin=MOD.classify((0,2),(1,3));self.assertEqual(status,"OVERLAPPING");self.assertLessEqual(margin,0)

    def test_cross_family_hydraulics_exclude_incomparable_absolute_anchors(self):
        for feature in ("pre_event_flow_m3_s","pre_event_resistance_pa_s_m3","terminal_mass_kg","flow_at_20s_m3_s","resistance_at_20s_pa_s_m3"):
            self.assertFalse(MOD.cross_family_comparable(feature))
        for feature in ("terminal_normalized_flow","terminal_normalized_resistance","normalized_flow_at_20s","normalized_resistance_at_20s","post_unload_residual_resistance"):
            self.assertTrue(MOD.cross_family_comparable(feature))

    def test_deterministic_three_program_capped_set_cover(self):
        rows=[]
        for i,pair in enumerate(MOD.PRIMARY_PAIRS):
            rows.append({"measurement_package_id":"M6","noise_scenario_id":"N1","classification":"ROBUSTLY_SEPARATED","program_id":f"P{i%3}","family_a":pair[0],"family_b":pair[1],"separation_margin":i+1.})
        result=MOD.select_set_cover(rows)
        self.assertTrue(result["complete_pair_coverage"]);self.assertLessEqual(result["program_count"],3)
        self.assertEqual(result,MOD.select_set_cover(rows))

    def test_atomic_gzip_record_readback_and_immutability_guard(self):
        with tempfile.TemporaryDirectory(prefix="SCI_ED_001_EXTERNAL_BUNDLE_test_") as td:
            path=Path(td)/"attempt_001"/"record.json.gz";meta=MOD.atomic_gzip(path,{"a":1})
            self.assertEqual(json.loads(gzip.decompress(path.read_bytes())),{"a":1});self.assertEqual(meta["file_sha256"],MOD.sha(path))
            path.write_bytes(path.read_bytes()[:-1]+b"x")
            with self.assertRaises(Exception):MOD.read_record(path)

    def test_bundle_must_be_external_and_symbolic(self):
        with self.assertRaises(ValueError):MOD.safe_bundle(ROOT/"SCI_ED_001_EXTERNAL_BUNDLE")
        self.assertIn("SCI_ED_001_EXTERNAL_BUNDLE",MOD.safe_bundle("/tmp/SCI_ED_001_EXTERNAL_BUNDLE/attempt_001").parts)

    def test_authority_comparison_is_canonical_object_not_presentation_bytes(self):
        a={"x":1,"y":[2,3]}
        self.assertEqual(json.loads(json.dumps(a,indent=2)),json.loads(MOD.canonical(a)))
        self.assertNotEqual(json.dumps(a,indent=2).encode(),MOD.canonical(a).encode())

    def test_replay_parity_gate(self):
        result=MOD.replay();self.assertEqual(result["status"],"PASS")
        self.assertEqual({x["family"] for x in result["checks"]},{"SCI-MD-002A","SCI-MD-002B","SCI-MD-002C"})
        self.assertTrue(all(x["status"]=="PASS" for x in result["checks"]))

if __name__=="__main__":unittest.main()
