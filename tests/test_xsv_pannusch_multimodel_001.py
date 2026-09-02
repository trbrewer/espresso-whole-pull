import csv, hashlib, json, pathlib, subprocess, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]; DOC=ROOT/'docs/analysis/xsv_pannusch_multimodel_001'; BASE='1519a0294eda106ceeff9c56cd57c8027bdcd9cf'
def load(n): return json.loads((DOC/n).read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
class XsvPannuschC1(unittest.TestCase):
 def test_authority_and_freeze_integrity(self):
  a=load('DATA_AUTHORITY.json'); s=load('summary.json'); ma=load('C1_REVIEW_MANDATED_METHODS_ADDENDUM.json'); ca=load('C1_CALIBRATION_FREEZE_ADDENDUM.json')
  self.assertEqual(a['puckworks_commit'],'7cf18d7bc388f636d9bca98e6e1a1def4bf08cf5'); self.assertEqual(sha(DOC/'METHODS_FREEZE.json'),'7d7492864adb7eb74c39cfc35692d3cc51fbcf49c423f2abba48c07c779c0631'); self.assertEqual(sha(DOC/'CALIBRATION_FREEZE.json'),'0b9a70bc3fd265c2df49a14c8ffd80baebbb7adc0aadc38bd3fb7e3567e40990')
  self.assertEqual(ma['original_methods_freeze_sha256'],sha(DOC/'METHODS_FREEZE.json')); self.assertEqual(ca['original_calibration_freeze_sha256'],sha(DOC/'CALIBRATION_FREEZE.json')); self.assertFalse(ca['prospective_target_blind']); self.assertFalse(s['freezes']['target_blind'])
 def test_boundary_privilege_and_result(self):
  s=load('summary.json'); rows=list(csv.DictReader((DOC/'MODEL_PRIVILEGE_REGISTRY.csv').open())); by={r['model_id']:r for r in rows}
  self.assertEqual(by['BASELINE-BOUNDARY-AWARE-POOL-ANALYTE']['privilege_class'],'CALIBRATION_ONLY_BOUNDARY_AWARE_EMPIRICAL_PROFILE'); self.assertEqual(by['MODEL-PANNUSCH-FIXED']['target_shot_windows'],'True'); self.assertEqual(by['BASELINE-BOUNDARY-AWARE-POOL-ANALYTE']['target_shot_windows'],'True'); self.assertEqual(by['BASELINE-ORDINAL-POOL-ANALYTE']['target_shot_windows'],'False')
  p=s['primary_comparison']; self.assertAlmostEqual(p['boundary_aware_rmse'],.01118680114,10); self.assertAlmostEqual(p['pannusch_rmse'],.01137215556,10); self.assertEqual(p['condition_signs'],{'pannusch_better':2,'boundary_aware_better':2}); self.assertFalse(p['unique_mechanistic_advantage_supported'])
 def test_hierarchical_exact_and_leave_one_out(self):
  s=load('summary.json'); u=s['uncertainty']; self.assertTrue(u['condition_then_shot']); self.assertEqual(u['replicates'],2000); self.assertEqual(u['seed'],20260830); self.assertLess(u['pannusch_minus_ordinal_interval'][1],0); self.assertLess(u['pannusch_minus_boundary_aware_interval'][0] if 'pannusch_minus_boundary_aware_interval' in u else s['primary_comparison']['pannusch_minus_boundary_aware_interval'][0],0)
  sign=load('EXACT_SIGN_FLIP_RESULT.json'); self.assertEqual(sign['assignments_enumerated'],16); self.assertEqual(sign['one_sided_p'],.0625); self.assertEqual(sign['two_sided_p'],.125)
  loo=list(csv.DictReader((DOC/'LEAVE_ONE_MARCH_CONDITION_OUT.csv').open())); self.assertEqual(len(loo),4); self.assertEqual(len({r['omitted_condition'] for r in loo}),4); self.assertTrue(all(float(r['pannusch_minus_ordinal'])<0 for r in loo))
 def test_fixed_roles_and_labels(self):
  roles=list(csv.DictReader((DOC/'PANNUSCH_SOURCE_ROLE_RESULTS.csv').open())); self.assertEqual(len(roles),4); self.assertIn('9;10;11;14;15',{r['conditions'] for r in roles})
  g=[r for r in csv.DictReader((DOC/'GROUPED_INTERNAL_RESULTS.csv').open()) if r['model_id']=='MODEL-PANNUSCH-FIXED']; self.assertEqual({r['scheme'] for r in g},{'LOSO','LOCO','LEAVE_GRIND_OUT'}); self.assertTrue(all('NO_FOLD_SPECIFIC_REFIT' in r['rmse'] for r in g))
 def test_inventory_species_residual_and_telemetry(self):
  s=load('summary.json'); self.assertEqual(s['inventory']['disposition'],'NORMALIZED_FIXED_PANNUSCH_CS0_SCALE_INVARIANT'); self.assertFalse(s['inventory']['cross_model_ranking_robustness_established'])
  inv=list(csv.DictReader((DOC/'INVENTORY_SENSITIVITY.csv').open())); self.assertEqual(sorted({float(r['c_s0_scale']) for r in inv}),[.001,.01,.1,1.,10.]); self.assertTrue(any(abs(float(r['mass_ratio_vs_1x'])-1)>0.5 for r in inv)); self.assertLess(max(float(r['max_share_delta_vs_1x']) for r in inv),2e-4)
  self.assertEqual(s['species']['disposition'],'SPECIES_SIGNAL_NOT_SUPPORTED_FOR_ADDED_CONDITION_DEPENDENT_COMPLEXITY'); tele=list(csv.DictReader((DOC/'TELEMETRY_JOIN_AUDIT.csv').open())); self.assertEqual(len(tele),24); self.assertEqual({r['join_class'] for r in tele},{'SOURCE_ORDER_ONLY'}); self.assertEqual(s['next_task']['task_id'],'OBS-PANNUSCH-FRACTION-WINDOW-001')
 def test_programme_and_protection(self):
  p=json.loads((ROOT/'provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json').read_text()); x=next(v for v in p['opportunities'] if v['opportunity_id']=='XSV-PANNUSCH-MULTIMODEL-001'); self.assertEqual(x['status'],'COMPLETE_NULL'); self.assertEqual(p['current_priority'],'SCI-DATA-FUSION-001'); self.assertFalse(p['laboratory_gate']['operation_authorized']); self.assertIn('corpus',x['notes'])
  changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines(); self.assertFalse(any(x.startswith('solver/') for x in changed)); self.assertFalse(any('angeloni' in x.lower() for x in changed))
if __name__=='__main__': unittest.main()
