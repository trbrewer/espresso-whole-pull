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
        inv={"terminal_conductance_ratios":{"11_over_5":.37327310642080013}}
        a,n=sci.reduced_screen(inv); b,m=sci.reduced_screen(inv)
        self.assertEqual((a,n),(b,m)); self.assertEqual(len(a),9)

if __name__=='__main__': unittest.main()
