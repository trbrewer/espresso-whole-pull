import csv,hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from scripts.validate_xsv_waszkiewicz_dynamic_hyd_001 import Invalid,validate
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/analysis/xsv_waszkiewicz_dynamic_hyd_001'
FILES=['PROCESSING_ROBUSTNESS.json','PROCESSING_SENSITIVITY.csv','summary.json','C1_REVIEW_MANDATED_METHODS_ADDENDUM.json','SOURCE_MODEL_PARITY.json']
class C2R1SemanticMutations(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);d=self.root/'docs/analysis/xsv_waszkiewicz_dynamic_hyd_001';d.mkdir(parents=True)
  for f in FILES: shutil.copy2(DOC/f,d/f)
 def tearDown(self): self.t.cleanup()
 def mutate(self,file,fn,code):
  d=self.root/'docs/analysis/xsv_waszkiewicz_dynamic_hyd_001';obj=json.loads((d/file).read_text());fn(obj);(d/file).write_text(json.dumps(obj))
  with self.assertRaises(Invalid) as caught: validate(self.root)
  self.assertEqual(caught.exception.code,code)
 def test_independent_time_row_bootstrap_control(self): self.assertEqual(validate(self.root)['status'],'PASS')
 def test_independent_time_row_bootstrap_rejected(self): self.mutate('C1_REVIEW_MANDATED_METHODS_ADDENDUM.json',lambda x:x['bootstrap'].__setitem__('time_rows_resampled',True),'XSV_BOOTSTRAP_TIME_ROW_INDEPENDENCE_FORBIDDEN')
 def test_legacy_ranking_stable_false_control(self): self.assertEqual(validate(self.root)['status'],'PASS')
 def test_legacy_ranking_stable_false_rejected(self): self.mutate('PROCESSING_ROBUSTNESS.json',lambda x:x.__setitem__('ranking_stable',False),'XSV_PROCESSING_OBSOLETE_FIELD')
 def test_broad_dynamic_absence_wording_control(self): self.assertEqual(validate(self.root)['status'],'PASS')
 def test_broad_dynamic_absence_wording_rejected(self): self.mutate('summary.json',lambda x:x['scope'].__setitem__('all_time_dependence_ruled_out',True),'XSV_BROAD_DYNAMIC_ABSENCE_CLAIM_FORBIDDEN')
 def test_source_model_grouped_prediction_relabel_control(self): self.assertEqual(validate(self.root)['status'],'PASS')
 def test_source_model_grouped_prediction_relabel_rejected(self): self.mutate('SOURCE_MODEL_PARITY.json',lambda x:x.__setitem__('privilege','GROUPED_PREDICTIVE_VALIDATION'),'XSV_SOURCE_MODEL_GROUPED_PREDICTION_RELABEL_FORBIDDEN')
class C2R1Records(unittest.TestCase):
 def test_owner_adjudication(self):
  x=json.loads((DOC/'C2_R1_TEST_AUTHORITY_OWNER_ADJUDICATION.json').read_text());h=x['historical_R2_result'];self.assertFalse(h['result_rejected_as_false']);self.assertFalse(h['usable_as_current_test_authority']);self.assertEqual(x['waiver_scope']['waived'],'EXACT_RETROSPECTIVE_R2_TEST_IDENTITY_RECONSTRUCTION');self.assertEqual(x['scientific_effect'],'NONE');self.assertEqual(len(x['waiver_scope']['not_waived']),10)
 def test_supported_pre_c2_authority(self):
  x=json.loads((DOC/'C2_R1_SUPPORTED_PRE_C2_TEST_AUTHORITY.json').read_text());self.assertEqual((x['discovered_test_count'],x['tests_run'],x['passed'],x['skipped'],x['failed'],x['errors']),(1119,1119,1116,3,0,0));self.assertTrue(x['repeated_discovery_identical']);self.assertTrue(x['repeat_execution_same_totals'])
 def test_processing_schema_and_csv_contract(self):
  self.assertEqual(validate(ROOT)['status'],'PASS');p=json.loads((DOC/'PROCESSING_ROBUSTNESS.json').read_text());self.assertEqual(p['tested_processing_window_count'],5);self.assertNotIn('ranking_stable',p);self.assertNotIn('processing_robustness',p)
 def test_scientific_authority_unchanged(self):
  s=json.loads((DOC/'summary.json').read_text());self.assertEqual(s['disposition'],'XSV_WASZKIEWICZ_DYNAMIC_HYD_001_NO_TESTED_EVOLVING_RESISTANCE_FORM_HAS_STABLE_GROUPED_PREDICTIVE_ADVANTAGE');self.assertEqual(s['next_task']['task_id'],'EWP-POROSITY-PERMEABILITY-PRIOR-001');self.assertFalse(s['home_lab']['operation_authorized'])
 def test_final_test_authority_consistent(self):
  x=json.loads((DOC/'C2_R1_FINAL_TEST_AUTHORITY.json').read_text());self.assertEqual(x['tests_run'],x['passed']+x['skipped']+x['failed']+x['errors']);self.assertEqual((x['failed'],x['errors']),(0,0));self.assertTrue(x['repeated_discovery_identical']);self.assertEqual(x['semantic_mutation_tests_passed'],4)
 def test_scientific_invariance_ledger(self):
  x=json.loads((DOC/'C2_R1_SCIENTIFIC_INVARIANCE_LEDGER.json').read_text());self.assertFalse(x['numeric_drift']);self.assertFalse(x['fold_drift']);self.assertFalse(x['model_drift']);self.assertFalse(x['successor_drift']);self.assertEqual(x['unexpected_byte_changes'],0)
if __name__=='__main__': unittest.main()
