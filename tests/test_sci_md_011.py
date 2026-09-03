import json,math,tempfile,unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import sci_md_011_core as c
import sci_md_011_execute as ex
class TestSciMd011(unittest.TestCase):
 def test_authorities_and_handoff(self):
  a=c.load_json(ROOT/'docs/analysis/sci_md_011/AUTHORITY_AND_HANDOFF.json');self.assertEqual(a['puckworks_analysis']['commit'],'2058d0e947ee9eb92c52d64f6165b810f1fb4732');self.assertEqual(a['production_puckworks_lock']['checkout_commit'],'fc61c4670ec7bf801e40bb391aab16048b8da26b')
 def test_population(self):self.assertEqual(ex.load_real_metadata()['joined_rows'],56)
 def test_phi_exact(self):self.assertEqual(c.PHI,2.257390325360356/18.5)
 def test_normalization(self):self.assertEqual(c.f0(0),0);self.assertEqual(c.f0(1),1);self.assertEqual(c.fphi(0),0);self.assertAlmostEqual(c.fphi(1),1,15)
 def test_universal_limit(self):
  for x in (0,.1,.4,.9,1):self.assertAlmostEqual(c.integral(x,1e-8)/c.integral(1,1e-8),c.f0(x),7)
 def test_shape_separation(self):self.assertAlmostEqual(max(abs(c.fphi(i/10000)-c.f0(i/10000)) for i in range(10001)),.0083056755,8)
 def test_domain(self):
  with self.assertRaises(ValueError):c.f0(1.01)
 def test_monotone_shapes(self):
  for fn in (c.f0,c.fphi):
   y=[fn(i/1000) for i in range(1001)];self.assertTrue(all(a<=b for a,b in zip(y,y[1:])))
 def test_unique_root_consistency(self):
  q,p,r=c.predict(9,2,15,c.P1);self.assertLess(r['pressure_residual_bar'],c.PRESSURE_TOL*2);self.assertAlmostEqual(p+c.brewer_drop(q),9,9)
 def test_zero_drive(self):self.assertEqual(c.predict(.1,2,15,c.P1)[0],0)
 def test_no_root_retained(self):
  with self.assertRaisesRegex(ValueError,'NO_ADMISSIBLE_ROOT'):c.predict(200,2,15,c.P1)
 def test_nonfinite(self):
  with self.assertRaises(ValueError):c.predict(float('nan'),2,15,c.P1)
 def test_predicted_flow_adapter(self):
  q,p,_=c.predict(8,2,15,c.E2C);self.assertAlmostEqual(8-p,c.brewer_drop(q),9)
 def test_balanced_weights(self):
  rows=[{'condition_id':'a'},{'condition_id':'a'},{'condition_id':'b'}];c.balanced(rows);self.assertAlmostEqual(sum(w for r,w in c.balanced(rows) if r['condition_id']=='a'),.5)
 def test_fit_deterministic(self):
  r=ex.synthetic_rows();self.assertEqual(c.fit(r,c.P1),c.fit(r,c.P1))
 def test_published_calibration_not_fit_input(self):self.assertNotIn('12.39',Path(c.__file__).read_text())
 def test_bootstrap_deterministic(self):
  rr,br=ex.run(ex.synthetic_rows());sc={r['outer_fold']:r['training_scale_g_s'] for r in rr};self.assertEqual(c.bootstrap(br,sc,c.MODELS[1],c.P1),c.bootstrap(br,sc,c.MODELS[1],c.P1))
 def test_gates_exact(self):
  contract=c.load_json(ROOT/'docs/analysis/sci_md_011/EVALUATION_CONTRACT.json');self.assertEqual(contract['gates']['high'],'predicted slope <= 0')
 def test_structural_turnover_false(self):self.assertFalse(c.load_json(ROOT/'docs/analysis/sci_md_011/EWP_CLOSURE_EQUIVALENCE.json')['turnover_capability'])
 def test_pairwise_model_ids(self):self.assertEqual((c.P1,c.E2C),c.MODELS[2:])
 def test_all_six_outcomes(self):
  d={'low_direction_ok':True,'high_direction_ok':True};self.assertEqual(c.candidate_status((.1,.2),d),'STABLE_ADVANTAGE');self.assertEqual(c.candidate_status((-.2,-.1),d),'STABLE_DISADVANTAGE');self.assertEqual(c.candidate_status((-.1,.1),d),'INDISTINGUISHABLE');self.assertEqual(c.candidate_status((0,0),d,True),'BLOCKED');self.assertEqual(c.candidate_status((0,0),d|{'high_direction_ok':False}),'WRONG_PRESSURE_RESPONSE')
  cases=[({c.P1:'BLOCKED',c.E2C:'INDISTINGUISHABLE'},'INDISTINGUISHABLE'),({c.P1:'WRONG_PRESSURE_RESPONSE',c.E2C:'WRONG_PRESSURE_RESPONSE'},'INDISTINGUISHABLE'),({c.P1:'INDISTINGUISHABLE',c.E2C:'STABLE_ADVANTAGE'},'STABLE_ADVANTAGE'),({c.P1:'STABLE_ADVANTAGE',c.E2C:'INDISTINGUISHABLE'},'INDISTINGUISHABLE'),({c.P1:'INDISTINGUISHABLE',c.E2C:'INDISTINGUISHABLE'},'INDISTINGUISHABLE'),({c.P1:'STABLE_DISADVANTAGE',c.E2C:'STABLE_DISADVANTAGE'},'STABLE_DISADVANTAGE')]
  self.assertEqual(len({c.overall(s,p)[0] for s,p in cases}),6)
 def test_no_full_ewp_promotion(self):self.assertFalse(c.load_json(ROOT/'docs/analysis/sci_md_011/PRE_SCORE_FREEZE.json')['current_full_ewp_validated'])
 def test_no_production_default(self):self.assertNotIn('write',json.dumps(c.load_json(ROOT/'docs/analysis/sci_md_011/MODEL_SPECIFICATIONS.json')).lower())
 def test_target_perturbation_no_test_effect(self):
  rows=ex.synthetic_rows();fold=c.load_csv(ROOT/'docs/analysis/sci_md_010/FOLD_ASSIGNMENTS.csv')[0];tr,te=ex.partition(rows,fold);m=c.fit(tr,c.P1);te[0]['flow_g_s']+=100;self.assertEqual(m,c.fit(tr,c.P1))
 def test_freeze_guards(self):self.assertEqual(c.load_json(ROOT/'docs/analysis/sci_md_011/PRE_SCORE_FREEZE.json')['real_candidate_scores_generated'],False)
 def test_synthetic_normal_path(self):
  rr,br=ex.run(ex.synthetic_rows());self.assertEqual(len(rr),44);self.assertEqual(len(br),224)
if __name__=='__main__':unittest.main()
