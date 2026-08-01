from __future__ import annotations
import copy,unittest
from pathlib import Path
from tools.validation.val001.deep_schema import semantic_validate
from tools.validation.val001.framework import ContractError,load_json
from tools.validation.val001.schema import SchemaError,lint_schema

ROOT=Path(__file__).resolve().parents[1]

class SchemaDocumentAstTests(unittest.TestCase):
 def reject(self,mutation):
  schema={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"espresso.val001.synthetic","type":"object","properties":{"x":{"type":"object","properties":{},"additionalProperties":False}},"additionalProperties":False}
  mutation(schema)
  with self.assertRaises(SchemaError):lint_schema(schema)
 def test_schema_keyword_value_matrix(self):
  cases=[
   lambda s:s["properties"]["x"].update(required="not-an-array"),
   lambda s:s["properties"]["x"].update(required=[1]),
   lambda s:s["properties"]["x"].update(required=["a","a"]),
   lambda s:s.update(properties=[]),lambda s:s.update(items="bad"),
   lambda s:s.update(enum=[]),lambda s:s.update(enum=[1,1]),
   lambda s:s.update(pattern="["),lambda s:s.update(additionalProperties="false"),
   lambda s:s.update(minItems="1"),lambda s:s.update(minItems=-1),
   lambda s:s.update(minItems=2,maxItems=1),lambda s:s.update(typoKeyword=True),
   lambda s:s.update(type="bogus"),lambda s:s.update(anyOf=[]),
  ]
  for i,case in enumerate(cases):
   with self.subTest(i=i):self.reject(case)
 def test_three_level_nested_required_string_rejected(self):
  def mutate(s):s["properties"]["x"]={"type":"object","properties":{"y":{"type":"object","required":"bad","properties":{},"additionalProperties":False}},"additionalProperties":False}
  self.reject(mutate)

class ExplicitSemanticEscalationTests(unittest.TestCase):
 def assert_semantic_rejects(self,rel,mutate,reason):
  value=load_json(ROOT/rel);mutate(value)
  with self.assertRaisesRegex(ContractError,reason):semantic_validate(rel,value)
 def test_campaign_commissioning_execution_and_completion(self):
  rel="validation/val001/VAL_001_CAMPAIGN_PROVENANCE.json"
  self.assert_semantic_rejects(rel,lambda d:d["campaigns"][0].update(commissioning_authorized=True),"execution or commissioning|campaign authority")
  self.assert_semantic_rejects(rel,lambda d:d["campaigns"][0].update(execution_authorized=True),"execution or commissioning|campaign authority")
  self.assert_semantic_rejects(rel,lambda d:d["campaigns"][0].update(proposed_status="COMPLETED"),"campaign authority")
  self.assert_semantic_rejects(rel,lambda d:d["locked_dependency"].update(commit="0"*40),"dependency lock")
 def test_structural_identifiability(self):
  rel="validation/val001/contracts/VAL_001_SENSITIVITY_AND_IDENTIFIABILITY_METHODS.json"
  self.assert_semantic_rejects(rel,lambda d:d.update(structural_identifiability="ESTABLISHED"),"structural identifiability")
 def test_evidence_gap_execution(self):
  rel="validation/val001/adapters/GAGNE_DE1_EVIDENCE_GAP_ADAPTER.json"
  self.assert_semantic_rejects(rel,lambda d:d["execution"].update(executable=True),"evidence-gap")
 def test_fitting_configuration_solver_and_physics(self):
  rel="validation/val001/adapters/GAGNE_DE1_EVIDENCE_GAP_ADAPTER.json"
  for key,value in (("fitting_or_retuning_allowed",True),("fit_or_retune_count",1),("configuration_change",True),("solver_source_change",True)):
   with self.subTest(key=key):self.assert_semantic_rejects(rel,lambda d,k=key,v=value:d["solver_mapping"].update({k:v}),"method authority|fit or retune")
 def test_consumed_authority_matrix(self):
  rel="validation/val001/contracts/VAL_001_POSTRESULT_EXECUTION_LOCK.json"
  for key,value in (("authority_status","AVAILABLE"),("remaining_real_data_comparison_invocations",1),("remaining_governed_result_producing_invocations",1),("further_retry_authorized",True),("alternate_ledger_allowed",True)):
   with self.subTest(key=key):self.assert_semantic_rejects(rel,lambda d,k=key,v=value:d.update({k:v}),"consumed authority|alternate execution")
 def test_physical_and_new_physics_claims(self):
  rel="validation/val001/VAL_001_CAMPAIGN_PROVENANCE.json"
  for key,value in (("physical_validation","ESTABLISHED"),("general_physical_validation","ESTABLISHED"),("general_whole_solver_physical_validation","ESTABLISHED"),("new_governing_physics","AUTHORIZED")):
   with self.subTest(key=key):self.assert_semantic_rejects(rel,lambda d,k=key,v=value:d.setdefault("claim_boundaries",{}).update({k:v}),"physical validation|new physics")
