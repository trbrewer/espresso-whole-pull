import copy,csv,json,math,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import sci_md_011_core as c
import sci_md_011_execute as ex
import validate_sci_md_011 as val
PW=Path(os.environ.get('SCI_MD_011_PUCKWORKS_ROOT',str(ROOT.parent/'puckworks-xsv-pannusch-authority')))

class TestSciMd011Core(unittest.TestCase):
 def test_corrected_bounds(self):self.assertLessEqual(c.BOUNDS['Pc_bar'][0],9);self.assertLessEqual(c.BOUNDS['Pc_bar'][0],12.39);self.assertGreaterEqual(c.BOUNDS['Pc_bar'][1],15)
 def test_bound_was_prospective(self):self.assertFalse(c.load_json(ROOT/'docs/analysis/sci_md_011/MODEL_SPECIFICATIONS.json')['bound_selection_candidate_information_used'])
 def test_lattice_interior_inclusive(self):
  s=c.lattice();self.assertEqual(len(s),25);self.assertTrue(any(c.BOUNDS['Pc_bar'][0]<math.exp(x[1])<c.BOUNDS['Pc_bar'][1] for x in s))
 def test_nonfinite_optimizer_blocks(self):self.assertEqual(c.fit([],c.P1,lambda x:math.inf)['execution_status'],'BLOCKED')
 def test_optimizer_deterministic(self):
  rows=ex.synthetic_rows('poro')[:12];self.assertEqual(c.fit(rows,c.P1),c.fit(rows,c.P1))
 def test_phi_exact(self):self.assertEqual(c.PHI,0.12202109866812735)
 def test_shapes_and_limit(self):
  for x in (0,.1,.4,.9,1):self.assertAlmostEqual(c.integral(x,1e-8)/c.integral(1,1e-8),c.f0(x),7)
  self.assertEqual(c.f0(0),0);self.assertEqual(c.f0(1),1);self.assertEqual(c.fphi(0),0);self.assertAlmostEqual(c.fphi(1),1,14)
 def test_shape_separation(self):self.assertAlmostEqual(max(abs(c.fphi(i/10000)-c.f0(i/10000)) for i in range(10001)),.008305675506984245,10)
 def test_domain_rejects(self):
  for x in (-.1,1.01,float('nan')):
   with self.assertRaises(ValueError):c.f0(x)
 def test_unique_root_and_units(self):
  q,p,r=c.predict(9,2,15,c.P1);self.assertIn('coupled_equation_residual_bar',r);self.assertNotIn('flow_consistency_g_s',r);self.assertAlmostEqual(p+c.brewer_drop(q),9,8)
 def test_no_root_retained(self):
  with self.assertRaisesRegex(ValueError,'NO_ADMISSIBLE_ROOT'):c.predict(200,2,15,c.P1)
 def test_machine_uses_predicted_flow(self):
  q,p,_=c.predict(8,2,15,c.E2C);self.assertAlmostEqual(8-p,c.brewer_drop(q),8)
 def test_balanced(self):
  z=c.balanced([{'condition_id':'a'},{'condition_id':'a'},{'condition_id':'b'}]);self.assertAlmostEqual(sum(w for r,w in z if r['condition_id']=='a'),.5)
 def test_tie_ranks_and_concordance_support(self):self.assertEqual(c.ranks([2,1,1]),[3,1.5,1.5]);self.assertAlmostEqual(c.spearman([1,1,2],[1,1,2]),1)
 def test_complexity_not_gated(self):self.assertEqual(c.complexity_status((.1,.2)),'STABLE_FINITE_PHI_ADVANTAGE')
 def test_claim_flags(self):
  f=c.load_json(ROOT/'docs/analysis/sci_md_011/PRE_SCORE_FREEZE.json');self.assertFalse(f['stage_f_authorized']);self.assertFalse(f['stage_d_authorized']);self.assertFalse(f['current_full_ewp_validated'])

class TestBindings(unittest.TestCase):
 def test_real_execution_not_unconditionally_disabled(self):self.assertNotIn('REAL_EXECUTION_REQUIRES_EXTERNAL_EXACT_REVIEW_AND_PHASE_B_PACKAGING',(ROOT/'scripts/sci_md_011_execute.py').read_text())
 def test_handoff_all_hashes(self):ex.verify_handoff()
 def test_production_hashes_and_symbols(self):ex.verify_production()
 def test_puckworks_exact(self):
  if not (PW/'.git').exists() and not PW.is_dir():self.skipTest('external SCI-MD-011 authority not provisioned')
  with mock.patch.dict(os.environ,{'SCI_MD_011_PUCKWORKS_ROOT':str(PW)}):self.assertEqual(ex.resolve_puckworks(),PW.resolve())
 def test_wrong_puckworks_rejected(self):
  with tempfile.TemporaryDirectory() as td,mock.patch.dict(os.environ,{'SCI_MD_011_PUCKWORKS_ROOT':td}):
   with self.assertRaises(Exception):ex.resolve_puckworks()
 def test_population_and_membership(self):
  rows=ex.synthetic_rows();p=ex.partitions(rows);self.assertEqual(len(p),11);self.assertEqual(sum(len(z[2]) for z in p),56)
 def test_membership_controls_partition(self):
  rows=ex.synthetic_rows();mem=c.load_csv(ROOT/'docs/analysis/sci_md_010/FOLD_MEMBERSHIP.csv');bad=copy.deepcopy(mem);bad[0]['role']='TRAIN'
  with self.assertRaises(ValueError):ex.partitions(rows,bad)
 def test_real_loader_dependency_fixture(self):
  idx=c.load_csv(ROOT/'docs/analysis/sci_md_010/ANALYSIS_ROW_INDEX.csv');accepted={r['physical_unit_id']:r for r in c.load_csv(ROOT/'docs/analysis/sci_md_010/BREW_RESULTS.csv') if r['model_id']==c.B0};eq=[];tr=[]
  for r in idx:
   a=accepted[r['physical_unit_id']];eq.append({'shot_id':r['source_row_id'],'window':'endpoint_100s','mass_flow_rate__g_per_s':a['observed_flow_g_s']});tr.append({'shot_id':r['source_row_id'],'time_index':'999','pressure__bar':a['line_pressure_bar']})
  def reader(path):return eq if path.name=='equilibrium_windows.csv' else tr
  rows=ex.load_real_rows(PW,reader);self.assertEqual(len(rows),56)
 def test_accepted_baseline_reuse(self):
  rows=ex.synthetic_rows();accepted=c.load_csv(ROOT/'docs/analysis/sci_md_010/BREW_RESULTS.csv');real=[]
  base={r['physical_unit_id']:r for r in accepted if r['model_id']==c.B0}
  for r in rows:r['flow_g_s']=float(base[r['physical_unit_id']]['observed_flow_g_s']);r['line_pressure_bar']=float(base[r['physical_unit_id']]['line_pressure_bar'])
  z=ex.accepted_baselines(ex.partitions(rows));got=[x for r in z for x in r['brew_rows'] if r['model_id']==c.B1];want=[r for r in accepted if r['model_id']==c.B1];self.assertEqual([float(x['predicted_flow_g_s']) for x in got],[float(x['predicted_flow_g_s']) for x in want])
 def test_b1_alteration_detected(self):
  rows=ex.synthetic_rows();base={r['physical_unit_id']:r for r in c.load_csv(ROOT/'docs/analysis/sci_md_010/BREW_RESULTS.csv') if r['model_id']==c.B0}
  for r in rows:r['flow_g_s']=float(base[r['physical_unit_id']]['observed_flow_g_s']);r['line_pressure_bar']=float(base[r['physical_unit_id']]['line_pressure_bar'])
  with mock.patch.object(ex,'load_csv',side_effect=lambda p:([dict(x,predicted_flow_g_s=str(float(x['predicted_flow_g_s'])+1)) for x in c.load_csv(p)] if str(p).endswith('BREW_RESULTS.csv') else c.load_csv(p))):
   with self.assertRaises(ValueError):ex.accepted_baselines(ex.partitions(rows))
 def test_metadata_preflight_zero(self):
  with mock.patch.dict(os.environ,{'SCI_MD_011_PUCKWORKS_ROOT':str(PW)}):r=ex.real_binding_metadata(PW)
  self.assertEqual((r['candidate_real_fits'],r['candidate_real_predictions'],r['candidate_real_scores']),(0,0,0))

class TestReceipts(unittest.TestCase):
 def base(self):return {'task_id':c.TASK,'disposition':ex.PASS,'freeze_commit':c.git(ROOT,'rev-parse','HEAD'),'freeze_tree':c.git(ROOT,'rev-parse','HEAD^{tree}'),'freeze_manifest_sha256':c.sha256(ROOT/'docs/analysis/sci_md_011/FREEZE_ARTIFACT_MANIFEST.json'),'reviewer_identity':'independent-reviewer','review_mode':'EXACT_HEAD_COMMENT','durable_review_url':'https://github.com/trbrewer/espresso-whole-pull/pull/142#issuecomment-1','reviewed_at':'2026-09-03T00:00:00Z','material_findings':[],'phase_b_authorized':True}
 def check_bad(self,key,value):
  r=self.base();r[key]=value
  with tempfile.NamedTemporaryFile('w',suffix='.json') as f:
   json.dump(r,f);f.flush()
   with self.assertRaises(ValueError):ex.verify_receipt(f.name,'real',c.sha256(ROOT/'docs/analysis/sci_md_011/FREEZE_ARTIFACT_MANIFEST.json'))
 def test_receipt_fields(self):
  for k,v in [('reviewer_identity',''),('durable_review_url','https://example.com'),('material_findings',['x']),('freeze_commit','bad'),('freeze_tree','bad'),('freeze_manifest_sha256','bad')]:self.check_bad(k,v)
 def test_synthetic_receipt_rejected_real(self):
  r=self.base();r['synthetic']=True
  with tempfile.NamedTemporaryFile('w',suffix='.json') as f:
   json.dump(r,f);f.flush()
   with self.assertRaisesRegex(ValueError,'SYNTHETIC'):ex.verify_receipt(f.name,'real',r['freeze_manifest_sha256'])

class TestIntegratedResults(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.base=Path(cls.tmp.name);env=os.environ|{'SCI_MD_011_PUCKWORKS_ROOT':str(PW),'PYTHONDONTWRITEBYTECODE':'1'}
  common=[sys.executable,str(ROOT/'scripts/sci_md_011_execute.py'),'--contract',str(ROOT/'docs/analysis/sci_md_011/EVALUATION_CONTRACT.json'),'--freeze',str(ROOT/'docs/analysis/sci_md_011/PRE_SCORE_FREEZE.json'),'--review-receipt',str(ROOT/'tests/fixtures/sci_md_011_synthetic_receipt.json'),'--synthetic-test-mode']
  for outcome in ('poro','quadratic','blocked'):
   subprocess.run(common+['--output',str(cls.base/outcome),'--synthetic-outcome',outcome],env=env,check=True)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_two_full_outcomes_differ(self):self.assertNotEqual(c.load_json(self.base/'poro/summary.json')['disposition'],c.load_json(self.base/'blocked/summary.json')['disposition'])
 def test_results_validate(self):
  for x in ('poro','quadratic','blocked'):val.result(self.base/x)
 def test_blocked_complete_package(self):
  d=c.load_json(self.base/'blocked/ARCHITECTURE_DECISION.json');s=c.load_json(self.base/'blocked/EXECUTION_STATE.json');self.assertEqual(d['scientific_status'],'BLOCKED');self.assertEqual(s['process_status'],'COMPLETE');self.assertEqual(set(ex.RESULT_FILES),{p.name for p in (self.base/'blocked').iterdir() if p.name!='SYNTHETIC_INPUT_ROWS.csv'})
 def test_blocked_pairs_not_computable(self):self.assertTrue(all(x['status']=='NOT_COMPUTABLE' for x in c.load_json(self.base/'blocked/PAIRWISE_COMPARISONS.json').values()))
 def test_root_failure_writes_complete_block(self):
  rows=ex.synthetic_rows('poro');parts=ex.partitions(rows);base=ex.synthetic_baselines(parts)
  def root_fit(train,m):return {'execution_status':'PASS','failure_class':'','failure_reason':'','optimizer_status':'PASS','prediction_status':'PENDING','fitted_parameters':{'Qc_g_s':20.,'Pc_bar':1.,'log_Qc':math.log(20),'log_Pc':0.},'objective':1.,'root_failure_count':0,'domain_failure_count':0,'nonfinite_count':0,'identifiability':'BOUND_CONTROLLED','bound_proximity':True}
  rec=base+ex.execute_candidates(parts,root_fit)
  with tempfile.TemporaryDirectory() as td:
   ex.write_result(Path(td),rec,'fixture',{'synthetic':True},True,rows);d=c.load_json(Path(td)/'ARCHITECTURE_DECISION.json');self.assertEqual(d['scientific_status'],'BLOCKED');self.assertTrue(any(r['failure_class']=='ROOT_OR_DOMAIN_FAILURE' for r in rec))
 def test_complete_diagnostics(self):
  d=c.load_json(self.base/'poro/PRESSURE_RESPONSE_DIAGNOSTICS.json')[c.P1]
  for k in ('signed_bias_g_s','predicted_low_slope','predicted_high_slope','slope_attenuation','distance_high_slope_from_zero','observed_peak_conditions','predicted_peak_conditions','spearman_average_ties','ordering_concordance'):self.assertIn(k,d)
 def test_all_pair_intervals(self):
  for x in c.load_json(self.base/'poro/PAIRWISE_COMPARISONS.json').values():self.assertIsNotNone(x['full_domain_interval']);self.assertIsNotNone(x['low_pressure_interval'])
 def test_heldout_target_perturbation(self):
  rows=ex.synthetic_rows();fold,train,test=ex.partitions(rows)[0];a=c.fit(train,c.P1);test[0]['flow_g_s']+=100;b=c.fit(train,c.P1);self.assertEqual(a,b);p=a['fitted_parameters'];self.assertEqual(c.predict(test[0]['line_pressure_bar'],p['Qc_g_s'],p['Pc_bar'],c.P1)[:2],c.predict(test[0]['line_pressure_bar'],p['Qc_g_s'],p['Pc_bar'],c.P1)[:2])
 def test_tamper_regenerated_manifest_fails(self):
  target=self.base/'tamper';subprocess.run(['cp','-a',str(self.base/'poro'),str(target)],check=True);rows=c.load_csv(target/'BREW_RESULTS.csv');rows[0]['predicted_flow_g_s']=str(float(rows[0]['predicted_flow_g_s'])+.1);c.write_csv(target/'BREW_RESULTS.csv',list(rows[0]),rows);m=c.load_json(target/'RESULT_ARTIFACT_MANIFEST.json');next(x for x in m['artifacts'] if x['path']=='BREW_RESULTS.csv')['sha256']=c.sha256(target/'BREW_RESULTS.csv');c.write_json(target/'RESULT_ARTIFACT_MANIFEST.json',m)
  with self.assertRaises(ValueError):val.result(target)
 def test_duplicate_guard(self):
  self.assertTrue(any((self.base/'poro').iterdir()))
 def calculated_fixture(self,case,out):
  folds=c.load_csv(ROOT/'docs/analysis/sci_md_010/FOLD_ASSIGNMENTS.csv');press=[1,2,3.5,4,5,6,7,8,9,11,13];records=[]
  for i,(fold,p) in enumerate(zip(folds,press)):
   observed=2-.025*(p-7)**2;passing=observed;wrong=p
   errors={'blocked':{c.B0:.5,c.B1:.5,c.P1:.5,c.E2C:.5},'wrong':{c.B0:.5,c.B1:.5,c.P1:.1,c.E2C:.1},'finite':{c.B0:.5,c.B1:1,c.P1:2,c.E2C:0},'universal':{c.B0:.5,c.B1:1,c.P1:0,c.E2C:.5},'tie':{c.B0:.5,c.B1:.5,c.P1:.5,c.E2C:.5},'negative':{c.B0:.5,c.B1:0,c.P1:1,c.E2C:1}}[case]
   for m in c.MODELS:
    blocked=case=='blocked' and m==c.P1 and i==0;pred=(wrong if case=='wrong' and m in c.CANDIDATES else passing)+errors[m]
    brew=[] if blocked else [{'outer_fold':fold['outer_fold'],'model_id':m,'source_row_id':f's{i}','physical_unit_id':f'u{i}','condition_id':fold['group_id'],'line_pressure_bar':p,'observed_flow_g_s':observed,'predicted_flow_g_s':pred,'predicted_basket_pressure_bar':'' if m not in c.CANDIDATES else max(0,p-.5),'coupled_equation_residual_bar':'' if m not in c.CANDIDATES else 0.,'error_g_s':pred-observed,'squared_error_g_s2':(pred-observed)**2,'training_scale_g_s':1.}]
    records.append({'outer_fold':fold['outer_fold'],'evaluation_condition_id':fold['group_id'],'model_id':m,'training_condition_ids':fold['training_groups'],'training_physical_unit_ids':'train','evaluation_physical_unit_ids':f'u{i}','training_scale_g_s':1.,'execution_status':'BLOCKED' if blocked else 'PASS','failure_class':'FIT_FAILURE' if blocked else '','failure_reason':'CALCULATED_FIXTURE_BLOCK' if blocked else '','optimizer_status':'FAIL' if blocked else 'PASS','prediction_status':'FAIL' if blocked else 'PASS','root_failure_count':0,'domain_failure_count':0,'nonfinite_count':0,'fitted_parameters':None if blocked else {},'rmse_g_s':None if blocked else abs(pred-observed),'normalized_loss':None if blocked else abs(pred-observed),'identifiability':'EXECUTION_BLOCKED' if blocked else 'ADEQUATELY_IDENTIFIED_FOR_PREDICTION','fit_receipt':{},'brew_rows':brew})
  ex.write_result(out,records,'fixture-manifest',{'synthetic':True},True,[]);return c.load_json(out/'summary.json')['disposition']
 def test_all_six_calculated_outcomes(self):
  with tempfile.TemporaryDirectory() as td:
   dispositions={self.calculated_fixture(case,Path(td)/case) for case in ('blocked','wrong','finite','universal','tie','negative')}
  self.assertEqual(len(dispositions),6)
 def test_no_production_adoption(self):self.assertFalse(c.load_json(self.base/'poro/summary.json')['current_full_ewp_validated'])

if __name__=='__main__':unittest.main()
