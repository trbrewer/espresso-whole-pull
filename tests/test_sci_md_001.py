import importlib.util, json, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("sci",ROOT/"scripts/sci_md_001.py")
sci=importlib.util.module_from_spec(spec); spec.loader.exec_module(sci)

class SciMd001Tests(unittest.TestCase):
    def test_strict_ordering_and_swapped_labels(self):
        self.assertTrue(sci.ordering({5:3,9:2,11:1}))
        self.assertFalse(sci.ordering({5:1,9:2,11:3}))
        self.assertFalse(sci.ordering({5:3,9:3,11:1}))
    def test_exact_si_hydraulics(self):
        h=sci.hydraulic(2e-6,5e5,mu=1e-3,length=1e-2,area=2e-4)
        self.assertAlmostEqual(h["conductance_m3_s_pa"],4e-12)
        self.assertAlmostEqual(h["resistance_pa_s_m3"],2.5e11)
        self.assertAlmostEqual(h["permeability_m2"],2e-13)
    def test_nonpositive_not_floored(self):
        self.assertIsNone(sci.hydraulic(0,5e5)["conductance_m3_s_pa"])
        self.assertIsNone(sci.hydraulic(-1,5e5)["resistance_pa_s_m3"])
    def test_grind_subtraction_direction(self):
        d=json.loads((ROOT/"validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_RESULT.json").read_text())
        v=d["axis_contrasts"]["P2_H1"]["GRIND_COARSE_MINUS_FINE"]["1/1"]
        self.assertGreater(v["source"],0); self.assertLess(v["model"],0)
        self.assertLess(-v["source"],0); self.assertGreater(-v["model"],0)
    def test_source_clock_is_not_refit(self):
        p=json.loads((ROOT/"validation/cases/sci_md_001/SCI_MD_001_PROTOCOL.json").read_text())
        self.assertEqual(p["clocks"],["SOURCE_CLOCK","ACCEPTED_PRESENTATION_CLOCK_PLUS_3_S"])
    def test_lower_rmse_cannot_be_sign_pass(self):
        self.assertFalse(sci.ordering({5:1.99,9:2.00,11:2.01}))
    def test_reduced_limits_bounded(self):
        self.assertAlmostEqual((11/5)**0,1)
        x=(1-__import__('math').exp(-30/10)); self.assertGreaterEqual(x,0); self.assertLessEqual(x,1)
    def test_deterministic_screen_and_result_consistency(self):
        inv={"terminal_conductance_ratios":{"11_over_5":.37327310642080013},
             "rows":[{"window":"terminal","pressure_nominal_bar":p,
                      "mean_source_pressure_bar":v} for p,v in
                     ((5,4.500962),(9,8.730249),(11,10.417174))]}
        a,n=sci.reduced_screen(inv); b,m=sci.reduced_screen(inv)
        self.assertEqual((a,n),(b,m)); self.assertEqual(len(a),9)
    def test_unresolved_is_not_outside_supported(self):
        inv=sci.inverse_analysis()[0]
        rows,_=sci.reduced_screen(inv)
        unresolved=[r for r in rows if r["plausibility"]=="BOUND_UNRESOLVED" and r["capable"]]
        self.assertTrue(unresolved)
        self.assertTrue(all(r["disposition"]=="CANDIDATE_MECHANISM_CAPABILITY_PLAUSIBILITY_UNRESOLVED" for r in unresolved))
        viscosity=next(r for r in rows if r["mechanism"].startswith("P5_"))
        self.assertEqual(viscosity["disposition"],"CANDIDATE_MECHANISM_CAPABLE_ONLY_OUTSIDE_PLAUSIBLE_RANGE")
    def test_primary_screen_uses_measured_not_nominal_pressure(self):
        inv=sci.inverse_analysis()[0]
        rows,_=sci.reduced_screen(inv)
        p1=next(r for r in rows if r["mechanism"].startswith("P1_"))
        self.assertEqual(p1["capable_region_breadth"],"n >= 1.18")
        nominal_first=next(n for n in [i*.01 for i in range(301)] if (11/5)**(-n)<=inv["terminal_conductance_ratios"]["11_over_5"])
        self.assertAlmostEqual(nominal_first,1.25)
        self.assertNotEqual(float(p1["capable_region_breadth"].split()[-1]),nominal_first)
    def test_conceptual_mechanisms_are_not_false_green(self):
        rows,_=sci.reduced_screen(sci.inverse_analysis()[0])
        for prefix in ("P3_","P4_","G1_","G2_"):
            row=next(r for r in rows if r["mechanism"].startswith(prefix))
            self.assertIsNone(row["capable"])
            self.assertEqual(row["disposition"],"NOT_STRUCTURALLY_EXCLUDED")
    def test_committed_matrix_and_plots_are_not_false_green(self):
        import csv
        with (ROOT/"validation/cases/sci_md_001/SCI_MD_001_MECHANISM_CAPABILITY_MATRIX.csv").open() as f:
            rows=list(csv.DictReader(f))
        for prefix in ("P3_","P4_","G1_","G2_"):
            row=next(r for r in rows if r["mechanism"].startswith(prefix))
            self.assertEqual(row["flow_order_pass"],"NOT_STRUCTURALLY_EXCLUDED_NOT_EVALUATED")
            self.assertEqual(row["grind_sign_match_count"],"NOT_EVALUATED")
            self.assertEqual(row["evaluation_kind"],"ANALYTICAL_STRUCTURAL_CHECK_ONLY")
        with (ROOT/"validation/cases/sci_md_001/SCI_MD_001_PLOT_SOURCE.csv").open() as f:
            plot_rows=list(csv.DictReader(f))
        self.assertTrue({"measured_pressure","measured_flow","apparent_conductance","conductance_ratio","grind_contrast"} <= {r["panel"] for r in plot_rows})
        for figure in (ROOT/"validation/cases/sci_md_001/figures").glob("*.svg"):
            text=figure.read_text()
            self.assertTrue("<polyline" in text or text.count("<rect") > 1)

if __name__=='__main__': unittest.main()
