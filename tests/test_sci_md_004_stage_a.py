import hashlib, json, subprocess, unittest
from pathlib import Path
from tools.sci_md_004_contract.consumer import load_contract
from tools.git_object_authority import GitAuthority, changed_paths, object_bytes, object_identity
ROOT=Path(__file__).resolve().parents[1]
STAGE_A_BASE=GitAuthority('0d2fa7595c44f1f190e61af11db9d510a940f9e6','a4eb209b5a0c50e48c9daa5688c660e62127deea')
STAGE_A_CANDIDATE=GitAuthority('9f5f66bb911adfde535b10b9a787e3357673d976','6f344dd1dad6b54876f20d80d6e58ec4ce4af9ac')
STAGE_A_ALLOWED={
 'PACKAGE_QA_STATUS.json','SOURCE_PACKAGE_MANIFEST.json','docs/PROJECT_STATE.md',
 'docs/validation/sci_md_004/STAGE_A_CONTRACT.md','docs/validation/sci_md_004/STAGE_A_DECISION.json',
 'tests/test_sci_md_004_stage_a.py','tools/sci_md_004_contract/__init__.py',
 'tools/sci_md_004_contract/__main__.py','tools/sci_md_004_contract/consumer.py',
 'validation/contracts/SCI_MD_004_STAGE_A_MULTISPECIES.json'}
ACCEPTED_EVIDENCE=(
 'docs/validation/sci_md_004/STAGE_A_CONTRACT.md',
 'docs/validation/sci_md_004/STAGE_A_DECISION.json',
 'validation/contracts/SCI_MD_004_STAGE_A_MULTISPECIES.json')
RUNTIME_LOCK='dependencies/puckworks.lock.json'
class StageA(unittest.TestCase):
 def setUp(self): self.c=load_contract()
 def test_schema_roles_and_holdout(self):
  self.assertEqual(self.c['schema_version'],'ewp.sci-md-004-stage-a/v1'); self.assertTrue(self.c['holdout']['preexisting_exposure'])
  roles={x['id']:x['role'] for x in self.c['species']}; self.assertEqual(roles['residual_extractables'],'STRUCTURAL_BALANCE_SPECIES'); self.assertEqual(roles['total_chlorogenic_acids'],'SECONDARY_ADAPTER_READY_NONADJUDICATIVE'); self.assertEqual(roles['total_lipids'],'DEFERRED_MULTIPHASE_CHANNEL')
 def test_inventory_closure(self):
  x=self.c['inventory_closure']; self.assertGreaterEqual(x['legacy_extractable_fraction']-x['arabica_named_fraction'],0); self.assertGreaterEqual(x['legacy_extractable_fraction']-x['robusta_named_fraction'],0); self.assertIn('SAME_TOTAL_IN_H0_AND_H1',x['gates'])
 def test_reduction_and_mapping_complete(self):
  self.assertEqual(len(self.c['one_species_reduction']['scalar_keys']),4); self.assertEqual(len(self.c['one_species_reduction']['legacy_fields']),3)
  required={'source','source_units_basis','target','mapping','geometry_reference_volume','provenance','validity','status'}
  self.assertTrue(all(required <= set(x) for x in self.c['parameter_mapping']))
 def test_metrics_disposition_and_claim(self):
  self.assertEqual(self.c['metrics']['material_relative_improvement'],0.15); self.assertEqual(self.c['data_sufficiency']['disposition'],'GO_STAGE_C_CONDITIONAL_HYDRAULIC_INPUT'); self.assertIn('NOT_ESTABLISHED',self.c['claim_ceiling'])
 def test_no_prohibited_provenance_or_execution(self):
  self.assertEqual(self.c['parameter_provenance']['prohibited'],['HOLDOUT_ENDPOINT_DERIVED','ANGELONI_RESPONSE_SURFACE_FIT','POST_HOLDOUT_RETUNED'])
  d=json.loads((ROOT/'docs/validation/sci_md_004/STAGE_A_DECISION.json').read_text()); self.assertEqual(d['holdout_predictions_generated'],0); self.assertEqual(d['holdout_scores_generated'],0)
 def test_allowed_paths_and_immutable_runtime_lock(self):
  historical=set(changed_paths(ROOT,STAGE_A_BASE,STAGE_A_CANDIDATE))
  self.assertEqual(historical,STAGE_A_ALLOWED)
  frozen_lock=object_bytes(ROOT,STAGE_A_CANDIDATE,RUNTIME_LOCK)
  self.assertEqual(hashlib.sha256(frozen_lock).hexdigest(),'52b15ceef87d503a3e77c6e3c1cbed785185d2dde0b79647e5fbe309395d2f10')
  self.assertEqual((ROOT/RUNTIME_LOCK).read_bytes(),frozen_lock)
  for path in ACCEPTED_EVIDENCE:
   with self.subTest(path=path):
    self.assertEqual((ROOT/path).read_bytes(),object_bytes(ROOT,STAGE_A_CANDIDATE,path))
    self.assertEqual(object_identity(ROOT,STAGE_A_CANDIDATE,path)['object_type'],'blob')
if __name__=='__main__': unittest.main()
