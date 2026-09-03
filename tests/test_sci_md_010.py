import copy,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from sci_md_010_core import *
D=ROOT/'docs/analysis/sci_md_010'
class TestSciMd010(unittest.TestCase):
 def test_01_leakage(self):
  with self.assertRaises(ValueError):validate_no_leakage([{'nested_unit_id':'f','physical_unit_id':'s1'},{'nested_unit_id':'f','physical_unit_id':'s2'}],[])
 def test_02_target_independent_folds(self):
  a=[{'g':'b','y':1},{'g':'a','y':9}];b=copy.deepcopy(a);b[0]['y']=-9;self.assertEqual(stable_folds(a,'g'),stable_folds(b,'g'))
 def test_03_training_only_fit(self):
  m=fit_linear([1,2],[2,4]);self.assertEqual(m,fit_linear([1,2],[2,4]));self.assertEqual(predict_linear(m,[3]),[6])
 def test_04_mechanistic_win(self):self.assertIn('ADVANTAGE',lane_decision(.1,1))
 def test_05_tie_reduced(self):self.assertIn('PREFER_REDUCED',lane_decision(.2,.3,full=.2))
 def test_06_wrong_order(self):self.assertIn('WRONG',lane_decision(.1,.2,False))
 def test_07_practical_not_structural(self):self.assertIn('PRACTICALLY',classify_identifiability([[1,1],[2,2]]))
 def test_08_reconstruction(self):
  with self.assertRaises(ValueError):enforce_privilege({'derived_from_target':'true','claim_class':'RETROSPECTIVE_GROUPED_PREDICTION','supplied_to_ewp':'true','supplied_to_b1':'true'})
 def test_09_privilege(self):
  with self.assertRaises(ValueError):enforce_privilege({'derived_from_target':'false','claim_class':'RETROSPECTIVE_GROUPED_PREDICTION','supplied_to_ewp':'true','supplied_to_b1':'false'})
 def test_10_real_joins(self):
  u={r['physical_unit_id'] for r in load_csv(D/'ANALYSIS_ROW_INDEX.csv')};self.assertTrue(all(x in u for f in load_csv(D/'FOLD_ASSIGNMENTS.csv') for x in f['evaluation_physical_units'].split(';')))
 def test_11_callables(self):
  for m in load_json(D/'MODEL_SPECIFICATIONS.json')['models']:
   if m['callable'] not in {'EXACT_REUSE_ONLY','UNAVAILABLE'}:self.assertTrue(all(x in MODEL_CALLABLES for x in m['callable'].split(',')))
 def test_12_hash_change(self):
  with tempfile.TemporaryDirectory() as t:p=Path(t)/'x';p.write_text('a');h=sha256(p);p.write_text('b');self.assertNotEqual(h,sha256(p))
 def receipt(self,**kw):
  r={'task_id':'SCI-MD-010','review_disposition':REVIEW_DISPOSITION,'reviewed_freeze_commit':'SYNTHETIC_HEAD','reviewed_freeze_tree':'SYNTHETIC_TREE','freeze_manifest_sha256':'h','reviewer_identity':'independent','review_record':'synthetic','reviewed_at_utc':'2026-09-02T00:00:00Z','material_findings':[],'phase_b_authorized':True};r.update(kw);return r
 def test_13_receipt_guards(self):
  for k,v in [('review_disposition','bad'),('reviewer_identity',''),('material_findings',['x']),('phase_b_authorized',False),('freeze_manifest_sha256','bad')]:
   with self.assertRaises(ValueError):verify_receipt(self.receipt(**{k:v}),{},'h',ROOT,True)
 def test_14_no_circular_mutation(self):p=D/'PRE_SCORE_FREEZE.json';h=sha256(p);verify_receipt(self.receipt(),{},'h',ROOT,True);self.assertEqual(h,sha256(p))
 def test_15_single_run(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'x').write_text('x')
   with self.assertRaises(ValueError):synthetic_run(p)
 def test_16_synthetic_pipeline(self):
  with tempfile.TemporaryDirectory() as t:r=synthetic_run(Path(t)/'o');self.assertEqual(r['primary_loss'],0);self.assertTrue((Path(t)/'o/RUN_RECEIPT.json').is_file())
 def test_17_utility(self):u={x['utility_class'] for x in load_csv(D/'EVIDENCE_UTILITY_REGISTER.csv')};self.assertIn('NO_CURRENT_DECISION_RELEVANT_USE',u);self.assertIn('DIRECT_RETROSPECTIVE_PREDICTIVE_EVALUATION',u)
 def test_18_claim(self):self.assertNotIn('INDEPENDENT_VALIDATION',load_json(D/'PRE_SCORE_FREEZE.json')['claim_ceiling'])
 def test_19_stages(self):p=load_json(D/'PRE_SCORE_FREEZE.json');self.assertFalse(p['stage_f_authorized'] or p['stage_d_authorized'])
 def test_20_no_private_path(self):
  for p in ['sci_md_010_core.py','sci_md_010_prepare.py','sci_md_010_execute.py','validate_sci_md_010.py']:self.assertNotIn('/'+'home'+'/',(ROOT/'scripts'/p).read_text())
 def fixture_rows(self):
  return [{'group_id':g,'shot_id':g+'-s','basket_pressure__bar':str(p),'mass_flow_rate__g_per_s':str(2*p)} for g,p in [('g1',1.),('g2',2.),('g3',3.)] for _ in range(3)]
 def test_21_registry_controls_execution(self):
  r=self.fixture_rows();self.assertEqual({x['model_id'] for x in execute_fold_models(r,['g1','g2'],'g3',['HYD_B0_TRAINING_MEAN'])},{'HYD_B0_TRAINING_MEAN'});self.assertEqual(len(execute_fold_models(r,['g1','g2'],'g3',['HYD_B0_TRAINING_MEAN','HYD_E1_LUMPED_DARCY'])),2)
 def test_22_unfrozen_model_rejected(self):
  with self.assertRaises(ValueError):execute_fold_models(self.fixture_rows(),['g1','g2'],'g3',['UNFROZEN'])
 def test_23_evaluation_target_does_not_change_prediction(self):
  a=self.fixture_rows();x=execute_fold_models(a,['g1','g2'],'g3',['HYD_E1_LUMPED_DARCY'])[0];b=copy.deepcopy(a)
  for r in b:
   if r['group_id']=='g3':r['mass_flow_rate__g_per_s']='999'
  y=execute_fold_models(b,['g1','g2'],'g3',['HYD_E1_LUMPED_DARCY'])[0];self.assertEqual(x['fit'],y['fit']);self.assertEqual(x['predictions'],y['predictions'])
 def test_24_metric_recomputation(self):
  x=execute_fold_models(self.fixture_rows(),['g1','g2'],'g3',['HYD_E1_LUMPED_DARCY'])[0];self.assertAlmostEqual(x['primary_loss'],0.0)
 def test_25_opposite_results_not_hardcoded(self):self.assertNotEqual(lane_decision(.1,.2),lane_decision(.3,.2))
 def test_26_real_e1_derivation(self):
  e=next(x for x in load_json(D/'MODEL_SPECIFICATIONS.json')['models'] if x['class']=='E1');self.assertIn('steady_outlet_flow_m3_s',e['ewp_derivation']);self.assertEqual(e['actual_execution_mode'],'FIT_AND_PREDICT')
 def test_27_actual_observation_binding(self):self.assertFalse(any(x['target_field'].endswith('PRIOR_SCORE_ONLY') for x in load_csv(D/'ANALYSIS_ROW_INDEX.csv')))
 def test_28_explicit_graph_topology(self):self.assertEqual(len(load_json(D/'END_TO_END_OBSERVABILITY_GRAPH.json')['edges']),5)
 def test_29_flow_derived_basket_pressure_prohibited(self):
  p=load_csv(D/'PRIVILEGE_LEDGER.csv');self.assertTrue(all(x['allowed']=='false' and x['target_derived']=='true' for x in p if x['variable']=='basket_pressure__bar'))
 def test_30_machine_coupling_uses_predicted_flow(self):
  cal={'a':.017184292098914252,'b':.03670858658698296,'c':.2831597837775055};q=solve_machine_darcy(8,.2,cal);self.assertAlmostEqual(q,.2*max(8-brewer_drop(q,cal),0),9)
 def test_31_target_perturbation_does_not_change_input_or_prediction(self):
  cal={'a':.017,'b':.037,'c':.283};train=[{'condition_id':'a','line_pressure_bar':'2','flow_g_s':'.3'},{'condition_id':'b','line_pressure_bar':'4','flow_g_s':'.6'}];m=fit_machine_darcy(train,cal);x=[{'line_pressure_bar':'6','flow_g_s':'1'}];y=[{'line_pressure_bar':'6','flow_g_s':'999'}];self.assertEqual(predict_machine_darcy(m,x,cal),predict_machine_darcy(m,y,cal))
 def test_32_equilibrium_primary(self):
  m=load_json(D/'METRIC_CONTRACT.json')['L-HYD'];self.assertTrue(m['target'].startswith('endpoint_100s'));self.assertNotIn('15-95',json.dumps(m))
 def test_33_exact_56_brews(self):self.assertEqual(len({x['physical_unit_id'] for x in load_csv(D/'ANALYSIS_ROW_INDEX.csv')}),56)
 def test_34_membership_controls_partitions(self):
  f=load_csv(D/'FOLD_ASSIGNMENTS.csv')[0];m=[x for x in load_csv(D/'FOLD_MEMBERSHIP.csv') if x['outer_fold']==f['outer_fold'] and x['role']=='EVALUATION'];self.assertEqual({x['physical_unit_id'] for x in m},set(f['evaluation_physical_units'].split(';')))
 def test_35_condition_balanced_duplicate_invariance(self):
  a=[{'condition_id':'a','flow_g_s':'1'},{'condition_id':'b','flow_g_s':'3'}];b=a+[dict(a[0]) for _ in range(9)];self.assertEqual(fit_condition_balanced_mean(a),fit_condition_balanced_mean(b))
 def test_36_conductance_nonnegative(self):
  cal={'a':0.,'b':0.,'c':0.};r=[{'condition_id':'a','line_pressure_bar':'1','flow_g_s':'-1'},{'condition_id':'b','line_pressure_bar':'2','flow_g_s':'-2'}];self.assertGreaterEqual(fit_machine_darcy(r,cal)['conductance_g_s_bar'],0)
 def test_37_quadratic_turnover(self):
  r=[{'condition_id':str(x),'line_pressure_bar':str(x),'flow_g_s':str(4*x-x*x)} for x in [1,2,3]];m=fit_condition_balanced_quadratic(r);self.assertLess(m['quadratic'],0);self.assertGreater(predict_quadratic(m,[{'line_pressure_bar':'2'}])[0],predict_quadratic(m,[{'line_pressure_bar':'3'}])[0])
 def test_38_seed_consistency(self):
  self.assertEqual(load_json(D/'PRE_SCORE_FREEZE.json')['random_seeds'],[R3_SEED]);self.assertEqual(load_json(D/'EVALUATION_CONTRACT.json')['seed'],R3_SEED);self.assertEqual(load_json(D/'METRIC_CONTRACT.json')['L-HYD']['seed'],R3_SEED)
 def test_39_no_e1_to_e2_promotion(self):self.assertEqual(load_json(D/'MODEL_SPECIFICATIONS.json')['E2']['decision'],'NOT_ADJUDICATED')
 def test_40_graph_integrity(self):
  g=load_json(D/'END_TO_END_OBSERVABILITY_GRAPH.json');ids={e['id'] for e in g['edges']};self.assertTrue(all(x in ids for c in g['minimal_cut_sets'] for x in c))
if __name__=='__main__':unittest.main()
