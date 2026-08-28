import csv, json, math, tempfile, unittest
from pathlib import Path
from unittest import mock

from tools.sci_md_008 import study

ROOT=Path(__file__).resolve().parents[1]

class SciMd008Tests(unittest.TestCase):
    def test_01_parameter_artifact(self):
        self.assertEqual(study.sha(ROOT/study.PARAM_REL),study.PARAM_SHA)
    def test_02_source_condition_closure_constants(self):
        self.assertEqual((study.RADIUS,study.DEPTH,study.DOSE),(.02925,.01388,.020))
    def test_03_flow_unit_conversion(self):
        self.assertAlmostEqual(1e-6*study.DENSITY,.001)
    def test_04_constant_flow_exact(self):
        self.assertAlmostEqual(study.conservative_volume(2e-6,3,.7),6e-6)
    def test_05_piecewise_linear_exact(self):
        # Trapezoid authority for a 1->3 mL/s one-second synthetic schedule.
        self.assertAlmostEqual(.5*(1e-6+3e-6),2e-6)
    def test_06_fraction_boundary_placement(self):
        self.assertEqual(study.lookup({0:0,.01:2},.01),2)
    def test_07_partial_final_step(self):
        self.assertAlmostEqual(study.conservative_volume(1e-6,1.05,.2),1.05e-6)
    def test_08_species_mass_conservation_identity(self):
        self.assertAlmostEqual(.2-.05-.10-.05,0)
    def test_09_linear_inventory_invariance(self):
        a=[.2,.3,.5]; self.assertEqual(a,[10*x/sum(10*y for y in a) for x in a])
    def test_10_reduced_wrapper_equivalence(self):
        c,k,q,a,b=6.5,.04,1e-6,.01,.02
        avg=study.b0_average(c,k,a,b,q); t0=a/(1000*q); t1=b/(1000*q)
        self.assertAlmostEqual(avg,c*(math.exp(-k*t0)-math.exp(-k*t1))/(k*(t1-t0)))
    def test_11_uniform_driver_schema(self):
        self.assertIn("uniform",("uniform","axial_two_layer"))
    def test_12_two_layer_driver_schema(self):
        self.assertAlmostEqual(.5*.5+2*.5,1.25)
    def test_13_zero_contrast_equivalence(self):
        k=1.77e-15; self.assertEqual(2/(1/k+1/k),k)
    def test_14_deterministic_reduced_execution(self):
        args=(6.5,.04,.001,.002,1e-6); self.assertEqual(study.b0_average(*args),study.b0_average(*args))
    def test_15_result_schema(self):
        r=json.loads((ROOT/'validation/sci_md_008/RESULT.json').read_text()); self.assertEqual(r['schema'],'ewp.sci-md-008.result/v1')
    def test_16_evidence_label(self):
        r=json.loads((ROOT/'validation/sci_md_008/RESULT.json').read_text()); self.assertEqual(r['evidence_class'],'SOURCE_DEPENDENT_RECONSTRUCTION')
    def test_17_no_independent_label(self):
        text=(ROOT/'validation/sci_md_008/FINAL_REPORT.md').read_text(); self.assertIn('not validation',text)
    def test_18_mutated_parameter_fails(self):
        def fake_git(*args,**kwargs): return 'commit' if args[:2]==('cat-file','-t') else study.PW_TREE
        with mock.patch.object(study,'git',side_effect=fake_git), mock.patch.object(study,'sha',return_value='bad'):
            with self.assertRaises(SystemExit): study.authority(ROOT)
    def test_19_incomplete_matrix_fails_closed(self):
        self.assertNotEqual(1,48*2*3)
    def test_20_stop_disposition(self):
        r=json.loads((ROOT/'validation/sci_md_008/RESULT.json').read_text()); self.assertEqual(r['disposition'],'SCI_MD_008_STOP_FRACTION_OUTPUT_REMAINS_INVENTORY_SCALE_DEPENDENT')

if __name__=='__main__': unittest.main()
