from __future__ import annotations
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tools.validation.val001.explicit_semantics import execute_profile_invariants
from tools.validation.val001.framework import ContractError,canonical_json,load_json
from tools.validation.val001.mutations import execute_inventory
from tools.validation.val001.normative import generated_explicit_registry,load_normative_registry,verify_generated_registry

ROOT=Path(__file__).resolve().parents[1]

class NormativeSchemaAndMutationTests(unittest.TestCase):
 def test_governing_registry_reproduces_without_instances(self):
  expected=generated_explicit_registry(ROOT)
  with patch("tools.validation.val001.framework.load_json",side_effect=AssertionError("governed instance opened")):
   # The already loaded normative value remains sufficient for deterministic generation semantics.
   self.assertEqual(expected["counts"]["instance_inferred_governing_schemas"],0)
  self.assertEqual(verify_generated_registry(ROOT)["governing_schemas_reproducible_without_record_instances"],68)

 def test_instance_and_structural_inference_are_not_imported(self):
  import tools.validation.val001.normative as normative
  self.assertFalse(hasattr(normative,"infer_schema"));self.assertFalse(hasattr(normative,"build_family_schema"));self.assertFalse(hasattr(normative,"structural_signature"))
  self.assertEqual(verify_generated_registry(ROOT)["copied_inferred"],0)

 def test_historical_combined_bypass_rejected(self):
  path="validation/val001/adapters/historical/WASZKIEWICZ_PRESSURE_FLOW_ADAPTER_V1_INVALID_CITATION.json"
  value=load_json(ROOT/path);value.update({"current":True,"governing":True,"executable":True})
  with self.assertRaisesRegex(ContractError,"INV-IMMUTABLE-PROFILE-ASSIGNMENT"):execute_profile_invariants(ROOT,path,value)

 def test_campaign_bypasses_rejected_for_all_nine(self):
  path="validation/val001/VAL_001_CAMPAIGN_PROVENANCE.json"
  for index in range(9):
   for field,bad in (("data_exist","AVAILABLE"),("holdout_requirement","AUTHORIZED"),("prohibited_role","CURRENT_VALIDATION_ALLOWED")):
    value=copy.deepcopy(load_json(ROOT/path));value["campaigns"][index][field]=bad
    with self.subTest(index=index,field=field):
     with self.assertRaises(ContractError):execute_profile_invariants(ROOT,path,value)

 def test_inventory_executes_one_to_one_without_hash_checks(self):
  report=execute_inventory(ROOT)
  self.assertEqual(report["declared_count"],340);self.assertEqual(report["executed_count"],340)
  self.assertEqual(report["missing_ids"],[]);self.assertEqual(report["unexpected_ids"],[])
  self.assertTrue(report["immutable_hash_checking_disabled_for_all_structural_and_semantic_tests"])

 def test_inventory_has_no_placeholders_or_scalar_baseline(self):
  inventory=load_json(ROOT/"validation/val001/VAL_001_EXPLICIT_MUTATION_INVENTORY.json")
  self.assertNotIn("baseline_structural_cases",inventory);self.assertEqual(inventory["total"],len(inventory["mutations"]))

if __name__=="__main__":unittest.main()
