#!/usr/bin/env python3
"""Add explicitly declared record-level contracts for correction administration."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.validation.val001.framework import canonical_json,load_json
from tools.validation.val001.normative import ASSIGNMENT_REGISTRY,NORMATIVE_REGISTRY

DECLARATIONS=[
 (63,"validation/val001/VAL_001_NORMATIVE_SCHEMA_CONTRACT_REGISTRY.json","NORMATIVE_SCHEMA_CONTRACT_REGISTRY","espresso.val001.normative_schema_contract_registry.v1",["schema_version","record_id","allowed_origins","prohibited_origins","contracts","record_bindings","counts"]),
 (64,"validation/val001/VAL_001_IMMUTABLE_PROFILE_ASSIGNMENT_REGISTRY.json","IMMUTABLE_PROFILE_ASSIGNMENT_REGISTRY","espresso.val001.immutable_profile_assignment_registry.v1",["schema_version","record_id","assignment_key","assignments","counts"]),
 (65,"validation/val001/VAL_001_SCHEMA_PROVENANCE_TRANSITION_MATRIX.json","SCHEMA_PROVENANCE_TRANSITION_MATRIX","espresso.val001.schema_provenance_transition_matrix.v1",["schema_version","record_id","prior_inferred_family_count","transition_count","entries","final_disposition"]),
 (66,"validation/val001/VAL_001_SCHEMA_TAXONOMY_AND_COUNTING_SPECIFICATION.json","SCHEMA_TAXONOMY_COUNTING","espresso.val001.schema_taxonomy_counting.v1",["schema_version","record_id","definitions","count_formulas","val001_schema_spec_015_disposition","counts"]),
 (67,"validation/val001/VAL_001_MUTATION_EXECUTION_COVERAGE.json","MUTATION_EXECUTION_COVERAGE","espresso.val001.mutation_execution_coverage.v1",["schema_version","record_id","declared_mutation_ids","executed_mutation_ids","missing_ids","unexpected_ids","duplicate_ids","placeholder_ids","category_counts","declared_count","executed_count","immutable_hash_checking_disabled_for_all_structural_and_semantic_tests","final_status"]),
 (68,"validation/val001/corrections/VAL_001_PR38_SCHEMA_PROVENANCE_AND_SEMANTIC_ENFORCEMENT_PLAN.json","CORRECTION_PLAN","espresso.val001.schema_provenance_semantic_enforcement_plan.v1",["schema_version","record_id","task","authority","controlling_adjudication","starting_identity","blocking_findings","stale_documentation_finding","designs","prohibited_actions","intended_additive_commit_sequence","stop_conditions","change_declaration"]),
]

def primitive(key):
 if key.endswith("_count") or key.endswith("count"):return {"type":"integer","minimum":0}
 if key.startswith("is_") or key.endswith("_disabled_for_all_structural_and_semantic_tests"):return {"type":"boolean"}
 if key in {"contracts","record_bindings","assignments","entries","declared_mutation_ids","executed_mutation_ids","missing_ids","unexpected_ids","duplicate_ids","placeholder_ids","blocking_findings","prohibited_actions","intended_additive_commit_sequence","stop_conditions"}:return {"type":"array","items":{},"uniqueItems":key.endswith("_ids")}
 if key in {"counts","definitions","count_formulas","authority","starting_identity","designs"}:return {"type":"object"}
 return {"type":"string"}

def closed(keys,overrides=None):
 overrides=overrides or {};return {"type":"object","required":keys,"properties":{k:overrides.get(k,primitive(k)) for k in keys},"additionalProperties":False}

def declared_schema(cls,keys):
 if cls=="SCHEMA_PROVENANCE_TRANSITION_MATRIX":
  entry_keys=["previous_inferred_schema_id","previous_schema_sha256","new_normative_contract_id","new_contract_sha256","new_governing_schema_id","new_governing_schema_sha256","authoritative_source_references","schema_bytes_identical","independent_derivation_explanation","no_instance_generation_test_id","semantic_profile_id","reviewer_disposition"]
  item=closed(entry_keys,{"previous_schema_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"new_contract_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"new_governing_schema_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"authoritative_source_references":{"type":"array","items":{"type":"string"},"minItems":1,"uniqueItems":True},"schema_bytes_identical":{"type":"boolean"},"reviewer_disposition":{"type":"string","const":"NORMATIVE_SOURCE_REPLACED"},"semantic_profile_id":{"type":"string","pattern":"^PROFILE-.+$"}})
  return closed(keys,{"prior_inferred_family_count":{"type":"integer","const":48},"transition_count":{"type":"integer","const":48},"entries":{"type":"array","items":item,"minItems":48,"maxItems":48},"final_disposition":{"type":"string","const":"ALL_PRIOR_INFERRED_FAMILIES_HAVE_NORMATIVE_TRANSITIONS"}})
 if cls=="SCHEMA_TAXONOMY_COUNTING":
  defkeys=["normative_schema_specification","governing_schema_family","administrative_meta_schema_family","schema_document_count","normative_contract_count","semantic_profile_count"]
  formulakeys=["governing_schema_family_count","prohibited_arithmetic","all_counts"]
  countkeys=["current_normative_specifications","current_referenced_specifications","current_unreferenced_specifications","governing_schema_families","schema_documents","administrative_meta_schema_families","schema_assignments"]
  assignment=closed(["schema_id","record_count"],{"record_count":{"type":"integer","minimum":1}})
  counts=closed(countkeys,{**{k:{"type":"integer","minimum":0} for k in countkeys[:-1]},"schema_assignments":{"type":"array","items":assignment,"minItems":1}})
  return closed(keys,{"definitions":closed(defkeys),"count_formulas":closed(formulakeys),"val001_schema_spec_015_disposition":{"type":"string","enum":["OBSOLETE_REMOVED"]},"counts":counts})
 return closed(keys)

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);a=ap.parse_args();root=Path(a.root).resolve();reg=load_json(root/NORMATIVE_REGISTRY);assign=load_json(root/ASSIGNMENT_REGISTRY);profiles=load_json(root/"validation/val001/VAL_001_SEMANTIC_PROFILE_REGISTRY.json")
 reg["contracts"]=[c for c in reg["contracts"] if c["specification_id"] not in {f"VAL001-SCHEMA-SPEC-{n:03d}" for n,*_ in DECLARATIONS}]
 reg["record_bindings"]=[b for b in reg["record_bindings"] if b["path"] not in {p for _,p,*_ in DECLARATIONS}]
 assign["assignments"]=[x for x in assign["assignments"] if x["path"] not in {p for _,p,*_ in DECLARATIONS}]
 profile=next(x for x in profiles["profiles"] if x["profile_id"]=="PROFILE-CURRENT-GOVERNANCE")
 for n,path,cls,version,keys in DECLARATIONS:
  spec=f"VAL001-SCHEMA-SPEC-{n:03d}";contract=f"VAL001-NORMATIVE-CONTRACT-{n:03d}";schema_id=f"{cls.lower()}.v1"
  schema={"$schema":"https://json-schema.org/draft/2020-12/schema","title":f"Normative {cls} contract","description":"Explicit record-level administrative contract; deeper normative invariants execute in the named validators.",**declared_schema(cls,keys)}
  reg["contracts"].append({"normative_contract_id":contract,"version":"v1","specification_id":spec,"schema_id":schema_id,"schema_version":version,"record_class":cls,"record_version":version,"status":"CURRENT","scope":"EXPLICIT_RECORD_SEMANTICS","origin":"NORMATIVE_RECORD_CONTRACT","authoritative_source_references":["human-owner correction authority dated 2026-08-01","docs/validation/VAL_001_SOURCE_ADAPTERS_AND_COMPONENT_COMPARISONS.md"],"required_fields":keys,"optional_fields":[],"prohibited_fields":[],"null_and_unavailable_reason_semantics":"NULL_ONLY_WHERE_SCHEMA_PERMITS; unavailable values require explicit reason fields","allowed_enum_domain":"DECLARED_BY_NORMATIVE_CONTRACT_AND_INVARIANTS","prohibited_enum_values":["INSTANCE_INFERENCE","CURRENT_VALIDATION","PHYSICAL_VALIDATION_ESTABLISHED"],"execution_status":"NONEXECUTABLE_ADMINISTRATION","governing_audit_status":"CURRENT_GOVERNING_ADMINISTRATION","protected_holdout_status":"NO_ACCESS_OR_SCORING_AUTHORIZED","rights_requirements":"NO_RIGHTS_ESCALATION","fitting_retuning_restrictions":"PROHIBITED","solver_configuration_restrictions":"PROHIBITED","dependency_lock_requirements":"PUCKWORKS_EXACT_IF_APPLICABLE","evidence_role_restrictions":"ADMINISTRATIVE_ONLY","score_bearing_rules":"NON_SCORE_BEARING","claim_ceiling":"NO_PHYSICAL_VALIDATION_OR_NEW_PHYSICS","physical_validation_status":"NOT_ESTABLISHED","identifiability_status":"NOT_APPLICABLE","campaign_status":"NOT_APPLICABLE","semantic_profile_id":"PROFILE-CURRENT-GOVERNANCE","required_cross_record_bindings":[],"required_mutation_ids":[f"MUT-STRUCTURAL-{3*(len(reg['contracts']))+i:03d}" for i in range(1,4)],"governing_schema":schema})
  binding={"path":path,"specification_id":spec,"semantic_profile_id":"PROFILE-CURRENT-GOVERNANCE","record_class":cls,"record_version":version,"schema_id":schema_id,"schema_version":version,"current":True,"audit_only":False,"executable":False,"treatment":"CURRENT_DEEP_SCHEMA"}
  reg["record_bindings"].append(binding);assign["assignments"].append({**binding,"normative_contract_id":contract,"current":True,"historical":False,"audit_only":False,"governing":True,"executable":False,"treatment":"CURRENT_DEEP_SCHEMA"})
  if spec not in profile["applies_to_specification_ids"]:profile["applies_to_specification_ids"].append(spec)
 reg["contracts"].sort(key=lambda x:x["specification_id"]);reg["record_bindings"].sort(key=lambda x:x["path"]);assign["assignments"].sort(key=lambda x:x["path"]);profile["applies_to_specification_ids"].sort()
 reg["counts"]={"current_normative_contracts":len(reg["contracts"]),"current_referenced_contracts":len({x["specification_id"] for x in reg["record_bindings"]}),"current_unreferenced_contracts":0,"instance_inferred_governing_schemas":0,"copied_inferred_governing_schemas":0,"structural_signature_governing_schemas":0,"filename_selected_governing_schemas":0}
 assign["counts"]={"governed_records":len(assign["assignments"]),"records_without_assignment":0,"duplicate_assignments":0}
 (root/NORMATIVE_REGISTRY).write_bytes(canonical_json(reg));(root/ASSIGNMENT_REGISTRY).write_bytes(canonical_json(assign));(root/"validation/val001/VAL_001_SEMANTIC_PROFILE_REGISTRY.json").write_bytes(canonical_json(profiles))
if __name__=="__main__":main()
