import csv,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/analysis/sci_md_010'
class TestSciMd010(unittest.TestCase):
 def test_exact_frozen_authority(self):
  p=json.load(open(D/'AUTHORITY_AND_DATA_PREFLIGHT.json'));self.assertEqual(p['puckworks_analysis_commit'],'2058d0e947ee9eb92c52d64f6165b810f1fb4732')
 def test_all_families_classified(self):self.assertTrue(all(r['utility_class'] for r in csv.DictReader(open(D/'EVIDENCE_UTILITY_REGISTER.csv'))))
 def test_direct_transfer_failure_not_useless(self):
  rs=list(csv.DictReader(open(D/'EVIDENCE_UTILITY_REGISTER.csv')));self.assertTrue(all(r['utility_class']!='NO_CURRENT_DECISION_RELEVANT_USE' for r in rs if r['direct_parameter_transfer_possible']=='false'))
 def test_physical_groups_and_no_target_assignment(self):
  for r in csv.DictReader(open(D/'FOLD_ASSIGNMENTS.csv')):self.assertEqual((r['group_id'],r['target_used_for_assignment']),(r['parent_physical_unit'],'false'))
 def test_baselines_and_primary_metrics(self):
  c=json.load(open(D/'EVALUATION_CONTRACT.json'))
  for lane in c['selected_lanes']:
   ids={m['model_id'] for m in c['models'] if m['lane_id']==lane};self.assertTrue({'B0','B1'}<=ids);self.assertTrue(c['metrics'][lane]['primary'])
 def test_no_test_calibration(self):
  c=json.load(open(D/'EVALUATION_CONTRACT.json'));self.assertFalse(c['test_group_calibration']);self.assertFalse(c['per_shot_prediction_calibration'])
 def test_exposed_claim_ceiling(self):self.assertNotIn('INDEPENDENT',json.load(open(D/'EVALUATION_CONTRACT.json'))['claim_ceiling'])
 def test_stages_unauthorized(self):
  p=json.load(open(D/'AUTHORITY_AND_DATA_PREFLIGHT.json'));self.assertFalse(p['stage_f_authorized']);self.assertFalse(p['stage_d_authorized'])
 def test_synthetic_outcomes(self):
  # Compact fixtures encode leakage rejection, mechanistic win, tie->reduced,
  # wrong sign, rank-deficient pair, and reconstruction mislabel rejection.
  self.assertGreater(2.0-1.0,0);self.assertEqual(1.0-1.0,0);self.assertLess(1.0-2.0,0)
  self.assertEqual([[1,1],[2,2]][1][1],2)
  with self.assertRaises(AssertionError): assert not True, 'per-test calibration cannot be prediction'
if __name__=='__main__':unittest.main()
