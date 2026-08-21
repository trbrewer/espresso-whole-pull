import hashlib,json,subprocess,tempfile,unittest
from pathlib import Path
from tools.sci_md_003_atlas.consumer import *
ROOT=Path(__file__).resolve().parents[1]
def fixture():
 return {'schema_version':EXPECTED_SCHEMA,'run_manifest':{'execution_code_commit':EXPECTED_COMMIT,'execution_code_tree':EXPECTED_TREE,'protocol_sha256':EXPECTED_PROTOCOL,'case_matrix_sha256':EXPECTED_CASE,'measurement_assumption_sha256':EXPECTED_ASSUMPTIONS},'summary_counts':{'explanations':0,'pair_eligibility':0,'eligible_pairs':0,'measurement_records':0,'result_cells':0},'explanations':[],'pair_eligibility':[],'measurement_value_records':[],'result_cells':[],'measurement_assumptions':{'channels':[{'channel':'flow'}]},'decision':{'selected_outcome':'SCI_MD_003_RP_A_001_ADDITIONAL_DATA_REQUIRED','decision_reason_record_ids':[]}}
def temporary(a):
 d=tempfile.TemporaryDirectory();p=Path(d.name)/'a.json';p.write_bytes(pretty(a));return d,p,sha256(p)
class Tests(unittest.TestCase):
 def test_end_to_end(self):
  d,p,h=temporary(fixture())
  try:self.assertEqual(build(load_atlas(p,h))['decision']['decision_id'],'EWP_CROSS_REPOSITORY_PROGRAMME_DECISION')
  finally:d.cleanup()
 def test_old_schema_rejected(self):
  a=fixture();a['schema_version']='puckworks.response-atlas-export/v1';d,p,h=temporary(a)
  try:
   with self.assertRaisesRegex(ValueError,'SCHEMA_VERSION'):load_atlas(p,h)
  finally:d.cleanup()
 def test_identity_and_summary_mutations(self):
  for dotted in ['run_manifest.execution_code_commit','run_manifest.execution_code_tree','run_manifest.protocol_sha256','summary_counts.explanations']:
   a=fixture();x=a
   for k in dotted.split('.')[:-1]:x=x[k]
   x[dotted.split('.')[-1]]='bad';d,p,h=temporary(a)
   try:
    with self.assertRaises(ValueError):load_atlas(p,h)
   finally:d.cleanup()
 def test_hash_rejected(self):
  d,p,h=temporary(fixture())
  try:
   with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):load_atlas(p,'0'*64)
  finally:d.cleanup()
 def test_unsupported_numeric_rejected(self):
  a=fixture();a['result_cells']=[{'support_status':'UNSUPPORTED_FOR_CASE','value':1}];a['summary_counts']['result_cells']=1;d,p,h=temporary(a)
  try:
   with self.assertRaisesRegex(ValueError,'UNSUPPORTED_NUMERIC'):load_atlas(p,h)
  finally:d.cleanup()
 def test_pairs_recomputed(self):self.assertTrue(all(p.eligibility=='ineligible' for p in derive_pairs(fixture(),retained_export())))
 def test_measurement_coverage_recomputed(self):
  b=build(fixture());self.assertEqual(b['measurement_value'],[]);self.assertTrue(all(not x['robustly_covered_pair_ids'] for x in b['coverage_matrix']))
 def test_zero_pair_nonvacuous(self):self.assertEqual(minimum_sets([],[])['result'],'NO_COMPLETE_MEASUREMENT_SET')
 def test_all_minima(self):self.assertEqual(minimum_sets(['p'],[{'channel':'a','pair_id':'p','covers_pair_robustly':True},{'channel':'b','pair_id':'p','covers_pair_robustly':True}])['sets'],[['a'],['b']])
 def test_decision_not_copied(self):
  a=fixture();a['decision']['selected_outcome']='ALTERED';self.assertNotEqual(build(a)['decision']['selected_outcome'],'ALTERED')
 def test_sci_lc_excluded(self):self.assertEqual(retained_export()['excluded_families'],['SCI-LC-001A'])
 def test_runtime_lock_and_no_solver_diff(self):
  self.assertEqual(hashlib.sha256((ROOT/'dependencies/puckworks.lock.json').read_bytes()).hexdigest(),'52b15ceef87d503a3e77c6e3c1cbed785185d2dde0b79647e5fbe309395d2f10');changed=set(subprocess.check_output(['git','diff','--name-only','origin/main...HEAD'],cwd=ROOT,text=True).split());self.assertFalse(any(x.startswith(('src/','applications/','cases/')) for x in changed))
 def test_determinism(self):self.assertEqual(canonical(build(fixture())),canonical(build(fixture())))
if __name__=='__main__':unittest.main()
