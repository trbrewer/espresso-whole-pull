import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from tools.sci_md_003_atlas.consumer import EXPECTED_COMMIT,EXPECTED_HASH,EXPECTED_SCHEMA,EXPECTED_TREE,load_atlas,retained_export

ROOT=Path(__file__).resolve().parents[1]
def atlas_fixture(schema=EXPECTED_SCHEMA):
 return {'schema_version':schema,'manifest':{'execution_code_commit':EXPECTED_COMMIT,'execution_code_tree':EXPECTED_TREE}}

class AtlasConsumerTests(unittest.TestCase):
 def test_exact_pin(self):
  pin=json.loads((ROOT/'docs/analysis/sci_md_003/PUCKWORKS_ANALYSIS_PIN.json').read_text())
  self.assertEqual((pin['puckworks_commit'],pin['puckworks_tree']),(EXPECTED_COMMIT,EXPECTED_TREE))
  self.assertEqual(pin['export_artifact_sha256'],EXPECTED_HASH)
 def test_load_and_reject_wrong_hash(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.json'; p.write_text(json.dumps(atlas_fixture())); h=hashlib.sha256(p.read_bytes()).hexdigest()
   self.assertEqual(load_atlas(p,h)['schema_version'],EXPECTED_SCHEMA)
   with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'): load_atlas(p,'0'*64)
 def test_wrong_schema_rejected_after_hash_binding(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.json'; p.write_text(json.dumps(atlas_fixture('wrong'))); h=hashlib.sha256(p.read_bytes()).hexdigest()
   with self.assertRaisesRegex(ValueError,'SCHEMA_VERSION'): load_atlas(p,h)
 def test_pressure_nodes_provenance_and_unsupported(self):
  e=retained_export(); supported=[r for r in e['observables'] if r['support_status']=='SUPPORTED']
  self.assertTrue(all(r['source_artifact'] and r['source_field'] for r in supported))
  self.assertTrue(any(r['node']=='BASKET' and r['reference_basis']=='GAUGE' for r in supported))
  self.assertTrue(all(r['value'] is None for r in e['observables'] if r['support_status']!='SUPPORTED'))
 def test_sci_lc_excluded(self): self.assertEqual(retained_export()['excluded_families'],['SCI-LC-001A'])
 def test_runtime_lock_unchanged_and_no_solver_source(self):
  lock=json.loads((ROOT/'dependencies/puckworks.lock.json').read_text())
  self.assertEqual(lock['checkout_commit'],'fc61c4670ec7bf801e40bb391aab16048b8da26b')
  changed=set(__import__('subprocess').check_output(['git','diff','--name-only','origin/main...HEAD'],cwd=ROOT,text=True).split())
  self.assertFalse(any(x.startswith(('src/','applications/','cases/')) for x in changed))
 def test_validation_ceiling(self):
  self.assertIn('Physical validation is `NOT_ESTABLISHED`',(ROOT/'CLAUDE.md').read_text())

if __name__=='__main__': unittest.main()
