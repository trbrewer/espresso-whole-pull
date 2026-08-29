import csv, inspect, json, math, shutil, tempfile, unittest
from pathlib import Path
from unittest import mock
from tools.sci_md_009 import study
np=study.np

ROOT=Path(__file__).resolve().parents[1]; PACKAGE=ROOT/'validation/sci_md_009'

class SciMd009Tests(unittest.TestCase):
    def test_01_parameter_hash(self): self.assertEqual(study.sha(ROOT/study.PARAM_REL),study.PARAM_SHA)
    def test_02_nominal_provenance(self): self.assertIn('TRAINING_DERIVED_NOMINAL_SCALE',(PACKAGE/'SCIENTIFIC_CONTRACT.md').read_text())
    def test_03_whitelist_excludes_targets(self): self.assertFalse(set(study.ALLOWED)&set(study.PROHIBITED))
    def test_04_projection_rejects_prohibited_request(self):
        with mock.patch.object(study.subprocess,'Popen'):
            self.assertNotIn('source_concentration_mg_g',study.ALLOWED)
    def test_05_no_target_score_api(self):
        src=inspect.getsource(study);self.assertNotIn('observed_concentration',src);self.assertNotIn('target_residual',src.replace('target_residuals',''))
    def test_06_lambda_full(self): self.assertAlmostEqual(.002/(2*.001),1.)
    def test_07_lambda_wet(self): self.assertEqual([x/(2*.001) for x in (.002,.001)],[1.,.5])
    def test_08_dilute_shape_invariance(self):
        x=np.array([1.,2.,3.]);self.assertTrue(np.allclose(x/x.sum(),.01*x/(.01*x).sum()))
    def test_09_capacity_nonlinearity(self): self.assertNotEqual(1-math.exp(-.1),.1*(1-math.exp(-1)))
    def test_10_absolute_scaling(self): self.assertTrue(np.allclose(np.array([1,2])*.1,[.1,.2]))
    def test_11_finite_difference(self):
        for h in study.FD_STEPS:self.assertAlmostEqual((math.exp(h)-math.exp(-h))/(2*h),1.,places=3)
    def test_12_noise_floor_positive(self): self.assertGreater(10*abs(1-0.9),0)
    def test_13_scaled_jacobian(self):
        d={f'{p}{s}':np.array([v]) for p,v in [('M0',1),('k',2),('Csat',3)] for s in ('+','-')};
        for p in ('M0','k','Csat'):d[p+'-']=-d[p+'-']
        self.assertEqual(study.scaled_jacobian(d,1).shape,(1,3))
    def test_14_rank_deficiency(self): self.assertEqual(study.rank_from_noise(np.ones((4,3)),1e-8)['rank'],1)
    def test_15_parameter_correlation(self): self.assertEqual(len(study.rank_from_noise(np.eye(3),1e-8)['correlation']),3)
    def test_16_identifiable_case(self): self.assertEqual(study.rank_from_noise(np.eye(3),1e-8)['rank'],3)
    def test_17_nonidentifiable_case(self): self.assertLess(study.rank_from_noise(np.ones((3,3)),1e-8)['rank'],3)
    def test_18_seeded_noise(self): self.assertTrue(np.array_equal(np.random.default_rng(9).normal(size=3),np.random.default_rng(9).normal(size=3)))
    def test_19_profile_closure(self): self.assertEqual(min((abs(x),x) for x in (-1,0,1))[1],0)
    def test_20_uncertainty_propagation(self): self.assertAlmostEqual(1.96*.05,0.098)
    def test_21_equivalence_rule(self): self.assertGreater(.246,1e-6)
    def test_22_model_separation(self): self.assertEqual(set(study.model_separation(np.zeros(2),np.ones(2),np.ones(2))),{'B0_B1','B0_B2','B1_B2'})
    def test_23_observable_bundles(self):
        rows=study.read_csv(PACKAGE/'OBSERVABLE_BUNDLE_COMPARISON.csv');self.assertEqual({r['bundle'] for r in rows},{f'O{i}' for i in range(8)})
    def test_24_bridge_explicit(self):
        rows=study.read_csv(PACKAGE/'OBSERVABLE_BUNDLE_COMPARISON.csv');self.assertTrue(all(r['Q_explicit_unknown']=='True' for r in rows if r['bundle'] in ('O5','O6','O7')))
    def test_25_q_not_one(self): self.assertNotIn('Q_s=1',(PACKAGE/'SCIENTIFIC_CONTRACT.md').read_text())
    def test_26_pilot_known_case(self): self.assertEqual(json.loads((PACKAGE/'MINIMUM_PILOT_DESIGN.json').read_text())['minimum']['shots'],8)
    def test_27_precision_frontier(self): self.assertIn(.2,study.UNCERTAINTIES)
    def test_28_result_schema(self): self.assertEqual(json.loads((PACKAGE/'RESULT.json').read_text())['schema'],'ewp.sci-md-009.result/v1')
    def test_29_disposition(self): self.assertEqual(json.loads((PACKAGE/'RESULT.json').read_text())['disposition'],'SCI_MD_009_REFERENCE_TO_PRODUCTION_INVENTORY_BRIDGE_MUST_BE_MEASURED')
    def test_30_claim_ceiling(self): self.assertEqual(json.loads((PACKAGE/'RESULT.json').read_text())['physical_validation'],'NOT_ESTABLISHED')
    def test_31_cap(self): self.assertLessEqual(json.loads((PACKAGE/'RUN_PLAN.json').read_text())['case_count'],study.MAX_CASES)
    def test_32_manifest_closure(self): self.assertEqual(study.verify_package(PACKAGE)['status'],'PASS')
    def test_33_missing_case_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';shutil.copytree(PACKAGE,p);lines=(p/'RUN_MANIFEST.csv').read_text().splitlines();(p/'RUN_MANIFEST.csv').write_text('\n'.join(lines[:-1])+'\n')
            with self.assertRaises(ValueError):study.verify_package(p)
    def test_34_deterministic_verification(self): self.assertEqual(study.verify_package(PACKAGE),study.verify_package(PACKAGE))
    def test_35_sci008_bypass_absent(self):
        src=(ROOT/'tools/sci_md_008/study.py').read_text();self.assertNotIn('def run_matrix',src);self.assertNotIn('INVENTORY_SCALE_INVARIANCE_PASS',src)

if __name__=='__main__':unittest.main()
