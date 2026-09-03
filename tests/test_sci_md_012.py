import ast, csv, hashlib, importlib.util, json, shutil, subprocess, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
V=module(ROOT/"scripts/validate_sci_md_012.py","validate012")
C=module(ROOT/"scripts/sci_md_011_core.py","core012test")
D=ROOT/"docs/analysis/sci_md_012"

class TestSciMd012(unittest.TestCase):
 def rows(self): return list(csv.DictReader((D/"ROOT_FEASIBILITY.csv").open()))
 def test_authority_hashes_and_six_unique_duplicate_equality(self):
  V.validate(ROOT); rows=self.rows(); self.assertEqual(6,len(rows)); self.assertEqual(6,len({r['brew_id'] for r in rows}))
  source=list(csv.DictReader((ROOT/"docs/analysis/sci_md_011/BREW_RESULTS.csv").open())); seen={}
  for r in source:
   if r['outer_fold']=='HYD-LOCO-13.0':
    obs=(float(r['line_pressure_bar']),float(r['observed_flow_g_s']))
    self.assertEqual(seen.setdefault(r['physical_unit_id'],obs),obs)
 def test_frozen_parameters_failure_all_rows_domain_adapter_and_algebra(self):
  rows=self.rows(); p=json.load((D/"PARAMETER_FEASIBILITY.json").open()); frozen=p['frozen_parameters']
  self.assertAlmostEqual(12.300611999011151,frozen['Pc_bar']); self.assertAlmostEqual(1.9573833549313604,frozen['Qc_g_s'])
  with self.assertRaisesRegex(ValueError,'NO_ADMISSIBLE_ROOT'): C.predict(float(rows[0]['measured_line_pressure_bar']),frozen['Qc_g_s'],frozen['Pc_bar'],C.E2C)
  self.assertEqual(6,len(rows)); self.assertTrue(all(r['closure_domain_valid']=='True' and r['fphi_finite']=='True' for r in rows))
  self.assertTrue(all(abs(float(r['closure_only_endpoint_bar'])+float(r['machine_adapter_contribution_bar'])-float(r['coupled_line_pressure_ceiling_bar']))<1e-14 for r in rows))
  self.assertTrue(all(r['exact_predict_status'] in ('PASS','NO_ADMISSIBLE_ROOT') for r in rows))
  self.assertTrue(p['witness']['inside_existing_bounds']); self.assertFalse(p['witness']['witness_is_prediction']); self.assertFalse(p['witness']['witness_is_candidate_fit']); self.assertFalse(p['witness']['witness_is_scored'])
  self.assertEqual('FROZEN_READ_ONLY_NO_NEW_OBJECTIVE_EVALUATION',p['profile_information_source'])
 def test_p1_parameters_and_root_feasible(self):
  folds=list(csv.DictReader((ROOT/'docs/analysis/sci_md_011/FOLD_RESULTS.csv').open())); r=next(x for x in folds if x['outer_fold']=='HYD-LOCO-13.0' and x['model_id']==C.P1); p=json.loads(r['fitted_parameters'])
  self.assertAlmostEqual(12.578391577958245,p['Pc_bar']); self.assertEqual('PASS',r['prediction_status'])
 def test_no_optimizer_or_scoring_constructs(self):
  text=(ROOT/'scripts/diagnose_sci_md_012.py').read_text(); tree=ast.parse(text)
  imports={n.names[0].name for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom)) and n.names}
  self.assertNotIn('scipy.optimize',imports); self.assertNotIn('scipy',imports)
  lowered=text.lower(); self.assertNotIn('grid_search',lowered); self.assertNotIn('coordinate_search',lowered)
  for path in D.iterdir():
   if path.suffix=='.json': self.assertFalse(set(V.walk_keys(json.load(path.open()))) & V.FORBIDDEN_KEYS)
 def test_deterministic_rerun(self):
  before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.iterdir()}
  puckworks=ROOT.parents[1]/'puckworks-upstream'
  subprocess.run(['python3','scripts/diagnose_sci_md_012.py','--root','.','--puckworks-repo',str(puckworks)],cwd=ROOT,check=True,env={'PYTHONDONTWRITEBYTECODE':'1'})
  after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.iterdir()}; self.assertEqual(before,after)
 def mutate(self,name,change,error):
  with tempfile.TemporaryDirectory() as td:
   copy=Path(td)/'repo'; shutil.copytree(ROOT,copy,ignore=shutil.ignore_patterns('.git','__pycache__'))
   change(copy/'docs/analysis/sci_md_012'/name)
   # Refresh only the outer artifact hash so semantic validation is exercised.
   manifest=json.load((copy/'docs/analysis/sci_md_012/ARTIFACT_MANIFEST.json').open())
   for x in manifest['artifacts']:
    if x['path']==name: x['sha256']=hashlib.sha256((copy/'docs/analysis/sci_md_012'/name).read_bytes()).hexdigest()
   (copy/'docs/analysis/sci_md_012/ARTIFACT_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
   with self.assertRaisesRegex(ValueError,error): V.validate(copy)
 def test_reject_missing_brew_changed_margin_frozen_parameter_score_architecture(self):
  def csvchange(fn):
   def inner(p):
    rows=list(csv.DictReader(p.open())); fn(rows); f=p.open('w',newline=''); w=csv.DictWriter(f,rows[0].keys(),lineterminator='\n'); w.writeheader(); w.writerows(rows); f.close()
   return inner
  self.mutate('ROOT_FEASIBILITY.csv',csvchange(lambda r:r.pop()),'EXPECTED_SIX')
  self.mutate('ROOT_FEASIBILITY.csv',csvchange(lambda r:r[0].__setitem__('representability_margin_bar','0')),'CHANGED_MARGIN')
  self.mutate('ROOT_FEASIBILITY.csv',csvchange(lambda r:r[0].__setitem__('frozen_Pc_bar','12')),'CHANGED_ENDPOINT')
  def score(p): d=json.load(p.open()); d['score']=1; p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
  self.mutate('DIAGNOSIS.json',score,'FABRICATED_SCORING')
  def arch(p): d=json.load(p.open()); d['architecture']='SELECTED'; p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
  self.mutate('DIAGNOSIS.json',arch,'UNAUTHORIZED_ARCHITECTURE')
 def test_reject_measurement_and_root_only_reparameterization(self):
  def measurement(p): d=json.load(p.open()); d['targeted_measurement_authorized']=True; p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
  self.mutate('DIAGNOSIS.json',measurement,'UNSUPPORTED_MEASUREMENT')
  def reparam(p): d=json.load(p.open()); d['next_action']='DEFINE_SEPARATELY_FROZEN_REPARAMETERIZATION_TEST'; p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
  self.mutate('DIAGNOSIS.json',reparam,'ROOT_WITNESS_ALONE')

if __name__=='__main__': unittest.main()
