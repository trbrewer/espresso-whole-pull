import inspect,io,json,shutil,tempfile,unittest
from pathlib import Path
from tools.sci_md_009 import c1,study
np=study.np
from tools.sci_md_009.sanitize import sanitize
ROOT=Path(__file__).resolve().parents[1];PKG=ROOT/'validation/sci_md_009'
class C1Tests(unittest.TestCase):
 def fx(self,text,cols):
  t=tempfile.TemporaryDirectory();p=Path(t.name)/'x';sanitize(io.StringIO(text),p,cols);return t,p
 def test_01_no_blob(self):self.assertNotIn('def frozen_blob',inspect.getsource(c1));self.assertNotIn('frozen_blob(',inspect.getsource(c1))
 def test_02_prohibited_invariant(self):
  a,p=self.fx('id,flow,target\n1,2,a\n',('id','flow'));b,q=self.fx('id,flow,target\n1,2,b\n',('id','flow'))
  try:self.assertEqual(p.read_bytes(),q.read_bytes())
  finally:a.cleanup();b.cleanup()
 def test_03_allowed_changes(self):
  a,p=self.fx('id,flow,target\n1,2,a\n',('id','flow'));b,q=self.fx('id,flow,target\n1,3,a\n',('id','flow'))
  try:self.assertNotEqual(p.read_bytes(),q.read_bytes())
  finally:a.cleanup();b.cleanup()
 def test_04_prohibited_request(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):sanitize(io.StringIO('id,x\n1,z\n'),Path(d)/'x',('secret',))
 def test_05_no_logging(self):self.assertNotIn('print(',inspect.getsource(sanitize))
 def test_06_scenarios(self):self.assertTrue(all(r['classification']=='RETAINED_VALID' for r in study.read_csv(PKG/'EXISTING_CASE_AUDIT.csv')))
 def test_07_raw(self):self.assertEqual(json.loads((PKG/'RAW_OUTPUT_MANIFEST.json').read_text())['case_count'],498)
 def test_08_derivatives(self):self.assertTrue(all(r['status']=='PASS' for r in study.read_csv(PKG/'DERIVATIVE_QUALIFICATION.csv')))
 def test_09_noise(self):self.assertGreater(json.loads((PKG/'DERIVATIVE_NUMERICAL_NOISE.json').read_text())['derivative_noise_floor_kg'],0)
 def test_10_rank_floor(self):self.assertEqual((study.rank_from_noise(np.diag([3.,2.,1.]),.5)['rank'],study.rank_from_noise(np.diag([3.,2.,1.]),1.5)['rank']),(3,2))
 def test_11_profiles_blocked(self):self.assertEqual(study.read_csv(PKG/'NONLINEAR_PROFILE_RESULTS.csv')[0]['state'],'BLOCKED')
 def test_12_multimodal_not_claimed(self):self.assertEqual(json.loads((PKG/'RESULT.json').read_text())['profiles'],'BLOCKED')
 def test_13_recovery_blocked(self):self.assertEqual(study.read_csv(PKG/'JOINT_SYNTHETIC_RECOVERY.csv')[0]['state'],'BLOCKED')
 def test_14_old_recovery_withdrawn(self):self.assertEqual(next(r for r in study.read_csv(PKG/'ARTIFACT_DISPOSITION.csv') if r['artifact']=='SYNTHETIC_RECOVERY.csv')['classification'],'SUPERSEDED_BY_C1')
 def test_15_all_params_not_faked(self):self.assertEqual(json.loads((PKG/'RESULT.json').read_text())['joint_recovery'],'BLOCKED')
 def test_16_o0_blocked(self):self.assertEqual(study.read_csv(PKG/'OBSERVABLE_BUNDLE_COMPARISON.csv')[0]['state'],'BLOCKED')
 def test_17_o4_not_assumed(self):self.assertNotIn('A_s=1',(PKG/'FINAL_REPORT.md').read_text())
 def test_18_o5_not_adjudicated(self):self.assertEqual(json.loads((PKG/'RESULT.json').read_text())['observable_bundles'],'BLOCKED')
 def test_19_o6_blocked(self):self.assertEqual(json.loads((PKG/'OBSERVABLE_BUNDLE_MODELS.json').read_text())['state'],'BLOCKED')
 def test_20_q_not_one(self):self.assertNotIn('Q=1',inspect.getsource(c1))
 def test_21_covariance_blocked(self):self.assertEqual(json.loads((PKG/'MEASUREMENT_ERROR_SCENARIOS.json').read_text())['state'],'BLOCKED')
 def test_22_endpoint_not_credited(self):self.assertNotIn('O2',json.loads((PKG/'RESULT.json').read_text()))
 def test_23_no_minimum(self):self.assertIsNone(json.loads((PKG/'MINIMUM_PILOT_DESIGN.json').read_text())['minimum'])
 def test_24_no_robust(self):self.assertIsNone(json.loads((PKG/'MINIMUM_PILOT_DESIGN.json').read_text())['robust'])
 def test_25_precision_blocked(self):self.assertEqual(study.read_csv(PKG/'PRECISION_FRONTIER.csv')[0]['state'],'BLOCKED')
 def test_26_no_ident_claim(self):self.assertNotIn('practical_identifiability',json.loads((PKG/'RESULT.json').read_text()))
 def test_27_numerical_preserved(self):self.assertEqual(json.loads((PKG/'NUMERICAL_QUALIFICATION.json').read_text())['status'],'PASS')
 def test_28_no_point_two(self):self.assertNotIn('maximum_joint_uncertainty',json.loads((PKG/'RESULT.json').read_text()))
 def test_29_no_tail(self):self.assertIsNone(json.loads((PKG/'SCI_ED_002_REVISIT_TRIGGER_ASSESSMENT.json').read_text())['calculated_threshold'])
 def test_30_report_closes(self):self.assertIn(json.loads((PKG/'RESULT.json').read_text())['disposition'],(PKG/'FINAL_REPORT.md').read_text())
 def test_31_mutations(self):
  names=('EXISTING_CASE_AUDIT.csv','SUPPLEMENTAL_RUN_MANIFEST.csv','DERIVATIVE_QUALIFICATION.csv','NONLINEAR_RESPONSE_VALIDATION.csv','NONLINEAR_PROFILE_RESULTS.csv','JOINT_SYNTHETIC_RECOVERY.csv','OBSERVABLE_BUNDLE_COMPARISON.csv','PRECISION_FRONTIER.csv','PILOT_DESIGN_PARETO.csv','MINIMUM_PILOT_DESIGN.json','SCI_ED_002_REVISIT_TRIGGER_ASSESSMENT.json','RESULT.json','TARGET_BLINDNESS.json')
  for name in names:
   with self.subTest(name=name),tempfile.TemporaryDirectory() as d:
    p=Path(d)/'p';shutil.copytree(PKG,p);q=p/name;q.write_bytes(q.read_bytes()+b' ')
    with self.assertRaises(ValueError):c1.verify(p)
 def test_32_stop(self):self.assertEqual(json.loads((PKG/'RESULT.json').read_text())['disposition'],'SCI_MD_009_C1_STOP_NONLINEAR_RESPONSE_NOT_QUALIFIED')
 def test_33_cap(self):
  x=json.loads((PKG/'SUPPLEMENTAL_RUN_PLAN.json').read_text());self.assertEqual((x['case_count'],x['cap']),(96,150))
 def test_34_no_targets(self):self.assertFalse(json.loads((PKG/'RESULT.json').read_text())['target_chemistry_values_accessed'])
 def test_35_claim(self):self.assertEqual(json.loads((PKG/'RESULT.json').read_text())['physical_validation'],'NOT_ESTABLISHED')
 def test_36_package(self):self.assertEqual(c1.verify(PKG)['status'],'PASS')
 def test_37_sci008(self):self.assertNotIn('def run_matrix',(ROOT/'tools/sci_md_008/study.py').read_text())
if __name__=='__main__':unittest.main()
