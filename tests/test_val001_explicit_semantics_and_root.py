from __future__ import annotations
import copy, json, subprocess, tempfile, unittest
from pathlib import Path

from tools.validation.val001.administrative import validate_binding_graph, verify_closure
from tools.validation.val001.explicit_semantics import execute_profile_invariants, load_policy
from tools.validation.val001.framework import ContractError, load_json
from tools.validation.val001.schema import lint_schema

ROOT=Path(__file__).resolve().parents[1]

class ExplicitSemanticPolicyTests(unittest.TestCase):
 def reject(self,path,mutator,code):
  value=copy.deepcopy(load_json(ROOT/path));mutator(value)
  with self.assertRaisesRegex(ContractError,code):execute_profile_invariants(ROOT,path,value)

 def test_policy_is_explicit_and_fully_dispatched(self):
  specs,profiles,_,bindings,_=load_policy(ROOT)
  self.assertTrue({s['origin'] for s in specs['specifications']} <= set(specs['allowed_origins']))
  self.assertEqual(0,specs['counts']['instance_derived_governing_schemas'])
  self.assertEqual(len(bindings),len(specs['record_bindings']))
  self.assertTrue(all(p['invariant_ids'] and p['validator_function_ids'] for p in profiles['profiles']))

 def test_campaign_escalations(self):
  p='validation/val001/VAL_001_CAMPAIGN_PROVENANCE.json'
  self.reject(p,lambda v:v['campaigns'][0].__setitem__('commissioning_authorized',True),'INV-(CAMPAIGN|GLOBAL)')
  self.reject(p,lambda v:v['campaigns'][0].__setitem__('execution_authorized',True),'INV-CAMPAIGN')
  self.reject(p,lambda v:v['campaigns'][0].__setitem__('proposed_status','COMPLETED'),'INV-CAMPAIGN')

 def test_consumed_authority_escalations(self):
  p='validation/val001/contracts/VAL_001_POSTRESULT_EXECUTION_LOCK.json'
  for key,bad in [('authority_status','AVAILABLE'),('remaining_real_data_comparison_invocations',1),('remaining_governed_result_producing_invocations',1),('alternate_invocation_id_allowed',True),('alternate_authority_allowed',True),('alternate_activation_allowed',True),('further_retry_authorized',True)]:
   with self.subTest(key=key):self.reject(p,lambda v,k=key,b=bad:v.__setitem__(k,b),'INV-CONSUMED-LOCK')

 def test_claim_method_and_protected_escalations(self):
  p='validation/val001/contracts/VAL_001_POSTRESULT_EXECUTION_LOCK.json'
  cases=[('physical_validation','ESTABLISHED','PHYSICAL_VALIDATION'),('general_physical_validation','ESTABLISHED','PHYSICAL_VALIDATION'),('general_whole_solver_physical_validation','ESTABLISHED','PHYSICAL_VALIDATION'),('new_governing_physics','AUTHORIZED','NEW_PHYSICS'),('fitting_allowed',True,'METHOD_CHANGE'),('fit_count',1,'FIT_RETUNE'),('retuning_allowed',True,'METHOD_CHANGE'),('retune_count',1,'FIT_RETUNE'),('solver_source_change',True,'METHOD_CHANGE'),('scientific_configuration_change',True,'METHOD_CHANGE'),('holdout_execution_authorized',True,'PROTECTED_EXPERIMENT'),('protected_scoring_authorized',True,'PROTECTED_EXPERIMENT'),('independent_validation','ESTABLISHED','CLAIM_CEILING'),('transfer_validation','ESTABLISHED','CLAIM_CEILING'),('mechanism_identity','ESTABLISHED','CLAIM_CEILING'),('physical_equivalence','ESTABLISHED','CLAIM_CEILING')]
  for key,bad,code in cases:
   with self.subTest(key=key):self.reject(p,lambda v,k=key,b=bad:v.__setitem__(k,b),code)

 def test_identifiability_and_historical_reexpression(self):
  self.reject('validation/val001/contracts/VAL_001_SENSITIVITY_AND_IDENTIFIABILITY_METHODS.json',lambda v:v.__setitem__('structural_identifiability','ESTABLISHED'),'STRUCTURAL_IDENTIFIABILITY')
  self.reject('validation/val001/results/historical/WP01R_R1_WASZKIEWICZ_9BAR.json',lambda v:v.__setitem__('new_score_bearing_comparison',True),'SCORE_BEARING')

 def test_failed_invocation_and_qualification(self):
  self.reject('validation/val001/results/VAL_001_CORRECTED_EXECUTION_FAILURE.json',lambda v:v.__setitem__('status','COMPLETED'),'INV-FAILED')
  self.reject('validation/val001/results/VAL_001_V2_FRAMEWORK_QUALIFICATION_PROVENANCE.json',lambda v:v.__setitem__('metric_input_artifacts',[{'unbound':True}]),'METRIC_INPUT_PROMOTION')

class RootArgumentTests(unittest.TestCase):
 def test_expected_root_arguments_are_mandatory(self):
  with self.assertRaisesRegex(ContractError,'VAL001_EXPECTED_ROOT_ARGUMENT_REQUIRED'):verify_closure(ROOT)
 def test_wrong_expected_head_and_tree_fail_before_closure(self):
  head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,text=True).strip()
  with self.assertRaisesRegex(ContractError,'VAL001_EXPECTED_HEAD_MISMATCH'):verify_closure(ROOT,expected_head='0'*40,expected_tree=tree)
  with self.assertRaisesRegex(ContractError,'VAL001_EXPECTED_TREE_MISMATCH'):verify_closure(ROOT,expected_head=head,expected_tree='0'*40)

class SchemaDocumentAdditionalTests(unittest.TestCase):
 def test_composition_and_reference_keywords_are_explicitly_rejected(self):
  for key,value in [('$ref','#/missing'),('oneOf',[]),('allOf',[]),('not',{})]:
   with self.subTest(key=key),self.assertRaises(Exception):lint_schema({'type':'object',key:value})
 def test_deep_scalar_property_schema_rejected(self):
  with self.assertRaises(Exception):lint_schema({'type':'object','properties':{'a':{'type':'object','properties':{'b':{'type':'object','properties':{'c':7}}},'additionalProperties':False}},'additionalProperties':False})
