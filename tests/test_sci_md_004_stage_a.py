import hashlib, json, subprocess, unittest
from pathlib import Path
from tools.sci_md_004_contract.consumer import load_contract
ROOT=Path(__file__).resolve().parents[1]
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
  changed=set(subprocess.check_output(['git','diff','--name-only','origin/main...HEAD'],cwd=ROOT,text=True).split()) | set(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).split())
  allowed=('AGENTS.md','CONTRIBUTING.md','docs/governance/','docs/validation/sci_md_004/','docs/validation/sci_md_005/','docs/validation/sci_md_007/','validation/sci_md_004_stage_e0/','validation/sci_md_004_stage_e1/','validation/sci_md_004_stage_e1_hydraulic_reconciliation/','validation/sci_md_005/','validation/sci_md_007/','validation/contracts/SCI_MD_004_STAGE_A_MULTISPECIES.json','validation/contracts/SCI_MD_004_STAGE_C_IMPLEMENTATION_AND_VERIFICATION.json','validation/contracts/SCI_MD_004_STAGE_C_R1_VERIFICATION_COMPLETION.json','validation/contracts/SCI_MD_004_STAGE_C_R2_SEPARATED_SPACE_TIME_VERIFICATION.json','tools/sci_md_004_contract/','tools/sci_md_004_stage_c/','tools/sci_md_004_stage_e0_freeze.py','tools/sci_md_004_stage_e1/','tools/sci_md_004_stage_e1_hydraulic.py','tools/sci_md_004_stage_e1_predict.py','tools/sci_md_004_stage_e1_score.py','tools/sci_md_005/','tools/inventory_scaled_composition/','tests/test_sci_md_004_stage_a.py','tests/test_sci_md_004_stage_c.py','tests/test_sci_md_004_stage_e0_freeze.py','tests/test_sci_md_004_stage_e1.py','tests/test_sci_md_004_stage_e1_hydraulic.py','tests/test_sci_md_005.py','tests/test_sci_md_007_handoff.py','tests/test_current_authority_consistency.py','scripts/generate_source_manifest.py','scripts/prepare_case.py','solver/espressoWholePullFoam/espressoWholePullFoam.C','docs/PROJECT_STATE.md','docs/CLAIM_CEILING.md','docs/ARCHITECTURE.md','docs/MODEL_SPECIFICATION.md','docs/strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md','SOURCE_PACKAGE_MANIFEST.json','PACKAGE_QA_STATUS.json','docs/QA_STATUS.md')
  allowed += ('docs/validation/sci_ed_002/','scripts/verify_sci_ed_002_handoff.py','tests/test_sci_ed_002_handoff.py')
  self.assertTrue(all(any(x==a or x.startswith(a) for a in allowed) for x in changed),changed)
  self.assertEqual(hashlib.sha256((ROOT/'dependencies/puckworks.lock.json').read_bytes()).hexdigest(),'52b15ceef87d503a3e77c6e3c1cbed785185d2dde0b79647e5fbe309395d2f10')
  self.assertFalse(any(x.startswith(('cases/','boundaries/')) for x in changed))
if __name__=='__main__': unittest.main()
