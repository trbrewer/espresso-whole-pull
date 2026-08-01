from __future__ import annotations
import copy,unittest
from pathlib import Path
from tools.validation.val001.deep_schema import semantic_validate
from tools.validation.val001.framework import ContractError,load_json
from tools.validation.val001.schema import SchemaError,lint_schema
from tools.validation.val001.administrative import validate_binding_graph

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

class AdministrativeBindingMutationTests(unittest.TestCase):
 def records(self):
  return tuple(load_json(ROOT/p) for p in (
   "validation/val001/VAL_001_GOVERNED_RECORD_INVENTORY.json",
   "validation/val001/contracts/VAL_001_ADMINISTRATIVE_CLOSURE_FREEZE.json",
   "validation/val001/contracts/VAL_001_POSTRESULT_EXECUTION_LOCK.json",
   "validation/val001/VAL_001_ADMINISTRATIVE_CLOSURE_SPECIFICATION.json"))
 def reject(self,mutate,reason):
  values=[copy.deepcopy(v) for v in self.records()];mutate(*values)
  with self.assertRaisesRegex(ContractError,reason):validate_binding_graph(*values)
 def test_orphan_ordinary_record(self):
  self.reject(lambda i,f,l,s:f["ordinary_record_bindings"].pop(),"orphan|binding set")
 def test_orphan_administrative_record(self):
  self.reject(lambda i,f,l,s:f["administrative_bindings"].pop(),"orphan|binding set")
 def test_duplicate_binding_path(self):
  self.reject(lambda i,f,l,s:f["ordinary_record_bindings"].append(copy.deepcopy(f["ordinary_record_bindings"][0])),"duplicate binding")
 def test_binding_cycle_policy(self):
  self.reject(lambda i,f,l,s:s["valid_edges"].append("CANONICAL_LOCK->ADMINISTRATIVE_FREEZE"),"edge policy")
 def test_two_terminal_records(self):
  def mutate(i,f,l,s):
   candidate=next(x for x in i["records"] if x["binding_class"]=="ORDINARY_HASH_BOUND_RECORD")
   candidate["binding_class"]="BOUND_BY_FINAL_GIT_TREE"
  self.reject(mutate,"noncanonical terminal")
 def test_no_terminal_record(self):
  def mutate(i,f,l,s):
   candidate=next(x for x in i["records"] if x["binding_class"]=="BOUND_BY_FINAL_GIT_TREE")
   candidate["binding_class"]="ORDINARY_HASH_BOUND_RECORD"
  self.reject(mutate,"orphan|binding set|terminal")
