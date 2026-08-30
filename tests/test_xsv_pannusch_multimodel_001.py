import csv, hashlib, json, pathlib, subprocess, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/analysis/xsv_pannusch_multimodel_001'
BASE='1519a0294eda106ceeff9c56cd57c8027bdcd9cf'
def load(name): return json.loads((DOC/name).read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

class XsvPannuschMultimodel001(unittest.TestCase):
 def test_authority_rights_and_counts(self):
  a=load('DATA_AUTHORITY.json'); p=load('DATA_PROFILE.json')
  self.assertEqual(a['puckworks_commit'],'7cf18d7bc388f636d9bca98e6e1a1def4bf08cf5'); self.assertEqual(a['rights'],'CC-BY-NC-3.0')
  self.assertEqual(a['source_subset_manifest_sha256'],'15b9f765d49abe45d6788d7c7891b0695fca185d9c614d122e393993ec06a83c')
  self.assertEqual((p['conditions'],p['physical_shots'],p['fit_physical_shots'],p['march_physical_shots'],p['fractions_per_shot']),(23,69,45,24,6)); self.assertEqual(p['invalid_spills_excluded'],3); self.assertTrue(p['target_exposed'])
 def test_freezes_and_march_guard(self):
  m=load('METHODS_FREEZE.json'); c=load('CALIBRATION_FREEZE.json'); s=load('summary.json')
  self.assertTrue(m['campaign_separated']); self.assertFalse(m['target_blind']); self.assertFalse(c['march_targets_loaded'])
  self.assertEqual(sha(DOC/'METHODS_FREEZE.json'),s['authorities']['methods_freeze_sha256']); self.assertEqual(sha(DOC/'CALIBRATION_FREEZE.json'),s['authorities']['calibration_freeze_sha256'])
  code=(ROOT/'analysis/xsv_pannusch_multimodel_001/run.py').read_text(); self.assertLess(code.index('CALIBRATION_FREEZE.json'),code.index('load_march(a.source)'))
 def test_model_privilege_and_parameters(self):
  rows=list(csv.DictReader((DOC/'MODEL_PRIVILEGE_REGISTRY.csv').open())); ranked=[r for r in rows if r['eligible_primary_ranking']=='true']
  self.assertGreaterEqual(len(ranked),6); self.assertTrue(all(r['parameter_count']!='' for r in rows)); self.assertFalse(any(r['target_specific_fit']=='true' for r in ranked)); self.assertFalse(any(r['privilege_class']=='TARGET_FITTED_DESCRIPTIVE_REFERENCE' for r in ranked))
 def test_observable_and_inventory(self):
  o=load('OBSERVABLE_CONTRACT.json'); s=load('summary.json'); inv=list(csv.DictReader((DOC/'INVENTORY_SENSITIVITY.csv').open()))
  self.assertEqual(o['primary'],'FRACTION_MASS_SHARE_VECTOR'); self.assertIn('NOT_MOLECULAR_SPECIES',o['tds_lane']); self.assertEqual(sorted({float(r['inventory_scale']) for r in inv if r['model_id']=='MODEL-PANNUSCH-FIXED'}),[.01,.1,1.0]); self.assertEqual(s['inventory']['ranking_stability'],'INVARIANT')
 def test_grouping_and_result(self):
  g=list(csv.DictReader((DOC/'GROUPED_INTERNAL_RESULTS.csv').open())); schemes={r['scheme'] for r in g}; self.assertTrue({'LOSO','LOCO','LOGO'}<=schemes)
  s=load('summary.json'); self.assertEqual(s['primary_comparison']['winner'],'MODEL-PANNUSCH-FIXED'); self.assertGreater(s['primary_comparison']['relative_improvement'],.10); self.assertLess(s['primary_comparison']['difference_95_interval'][1],0)
 def test_programme_named_exhaustion_and_lab_gate(self):
  p=json.loads((ROOT/'provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json').read_text()); x=next(v for v in p['opportunities'] if v['opportunity_id']=='XSV-PANNUSCH-MULTIMODEL-001')
  self.assertEqual(x['status'],'COMPLETE_POSITIVE'); self.assertTrue(x['completion_evidence']); self.assertTrue(x['exhaustion_decision']); self.assertFalse(p['laboratory_gate']['operation_authorized']); self.assertNotIn('entire Pannusch corpus exhausted',x['notes'])
 def test_historical_and_production_protection(self):
  changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines(); self.assertFalse(any(x.startswith('solver/') for x in changed)); self.assertFalse(any('angeloni' in x.lower() for x in changed))
  self.assertNotIn('angeloni',(ROOT/'analysis/xsv_pannusch_multimodel_001/run.py').read_text().lower())

if __name__=='__main__': unittest.main()
