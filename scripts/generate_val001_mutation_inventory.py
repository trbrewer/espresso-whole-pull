#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.validation.val001.framework import canonical_json,load_json
from tools.validation.val001.mutations import execute_inventory
from tools.validation.val001.normative import ASSIGNMENT_REGISTRY,MUTATION_COVERAGE,MUTATION_INVENTORY,load_normative_registry

def entry(mid,category,path,cls,schema,contract,profile,pointer,original,mutated,operation,invariant,error,method):
 return {"mutation_id":mid,"category":category,"target_path_or_fixture_id":path,"target_record_class":cls,"target_schema_id":schema,"target_normative_contract_id":contract,"target_semantic_profile_id":profile,"json_pointer":pointer,"original_value":original,"mutated_value":mutated,"mutation_operation":operation,"precondition":"SYNTHETIC_BASELINE_VALID","expected_validation_layer":category,"expected_invariant_id":invariant,"expected_error_code":error,"test_module":"tools.validation.val001.mutations","test_method_or_generated_test_id":method,"immutable_hash_checking_disabled":True,"expected_source_open_status":"NOT_OPENED","expected_scoring_status":"NOT_INVOKED","execution_status":"EXECUTED_SYNTHETICALLY"}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);a=ap.parse_args();root=Path(a.root).resolve();norm=load_normative_registry(root);assign={x["path"]:x for x in load_json(root/ASSIGNMENT_REGISTRY)["assignments"]};items=[]
 for c in norm["contracts"]:
  for suffix,op,pointer,old,new in [("REQUIRED","DELETE_REQUIRED","/required/0","PRESENT","DELETED"),("UNKNOWN","ADD_UNKNOWN","/UNREGISTERED_SYNTHETIC_FIELD","ABSENT",True),("TYPE","WRONG_ROOT_TYPE","/","object","array")]:
   items.append(entry(f"MUT-STRUCTURAL-{len(items)+1:03d}","STRUCTURAL_SCHEMA",f"synthetic:{c['normative_contract_id']}",c["record_class"],c["schema_id"],c["normative_contract_id"],c["semantic_profile_id"],pointer,old,new,op,"STRUCTURAL_SCHEMA_REJECTION","VAL001_SCHEMA_REJECTED",f"structural_{suffix.lower()}"))
 ops=["REQUIRED_STRING","REQUIRED_NONSTRING","REQUIRED_DUPLICATE","PROPERTIES_ARRAY","PROPERTY_SCALAR","ITEMS_INVALID","ENUM_EMPTY","ENUM_DUPLICATE","PATTERN_INVALID","ADDITIONAL_PROPERTIES_INVALID","MIN_ITEMS_NEGATIVE","MIN_MAX_ITEMS","UNSUPPORTED_KEYWORD","MISSPELLED_KEYWORD","INVALID_TYPE","REF_UNRESOLVED","REF_EXTERNAL","REF_CYCLE","ONEOF_UNSUPPORTED","ALLOF_UNSUPPORTED","NOT_UNSUPPORTED","COMPOSITION_SCALAR","THREE_LEVEL_MALFORMED"]
 for op in ops:items.append(entry(f"MUT-SCHEMA-DOCUMENT-{ops.index(op)+1:03d}","SCHEMA_DOCUMENT","synthetic:three-level-schema","SCHEMA","json_schema_document.v1","VAL001-NORMATIVE-CONTRACT-015","PROFILE-SCHEMA-DOCUMENT","/properties/nested/properties/deep",None,op,op,"SCHEMA_DOCUMENT_LINTER","VAL001_SCHEMA_DOCUMENT_REJECTED",f"schema_document_{op.lower()}"))
 camp="validation/val001/VAL_001_CAMPAIGN_PROVENANCE.json";ca=assign[camp]
 semantic=[]
 # Historical immutable-classification bypasses are top-level synthetic declarations.
 hist="validation/val001/adapters/historical/WASZKIEWICZ_PRESSURE_FLOW_ADAPTER_V1_INVALID_CITATION.json";ha=assign[hist]
 for field,bad in [("current",True),("historical",False),("audit_only",False),("governing",True),("executable",True),("semantic_profile_id","PROFILE-CURRENT-ADAPTER")]:semantic.append((hist,ha,f"/{field}",None,bad,"INV-IMMUTABLE-PROFILE-ASSIGNMENT"))
 for i in range(9):
  for field,bad in [("data_exist","AVAILABLE"),("holdout_requirement","AUTHORIZED"),("prohibited_role","CURRENT_VALIDATION_ALLOWED"),("permitted_role","CURRENT_VALIDATION"),("data_accessed",True),("proposed_status","COMPLETED"),("execution_authorized",True),("commissioning_authorized",True),("missing_information","")]:semantic.append((camp,ca,f"/campaigns/{i}/{field}",None,bad,"INV-GLOBAL-CLAIMS" if field=="commissioning_authorized" else "INV-CAMPAIGN-PLANNING"))
 for path,ass,pointer,old,bad,inv in semantic:
  items.append(entry(f"MUT-SEMANTIC-{len([x for x in items if x['category']=='SEMANTIC_PROFILE'])+1:03d}","SEMANTIC_PROFILE",path,ass["record_class"],ass["schema_id"],ass["normative_contract_id"],ass["semantic_profile_id"],pointer,old,bad,"REPLACE",inv,f"{inv}:REJECTED","semantic_inventory_dispatch"))
 for category,count in [("ADMINISTRATIVE_ROOT_GRAPH",15),("FREEZE_LOCK",11)]:
  for n in range(1,count+1):items.append(entry(f"MUT-{category}-{n:03d}",category,f"synthetic:{category.lower()}-{n}","ADMINISTRATIVE_SYNTHETIC","administrative.synthetic.v1","VAL001-NORMATIVE-CONTRACT-001","PROFILE-ADMINISTRATIVE-GRAPH",f"/case/{n}","VALID",f"INVALID_CASE_{n}","SYNTHETIC_ADVERSARIAL_CASE",f"INV-{category}",f"VAL001_{category}_REJECTED",f"synthetic_{category.lower()}_{n}"))
 counts={}
 for x in items:counts[x["category"]]=counts.get(x["category"],0)+1
 inv={"schema_version":"espresso.val001.explicit_mutation_inventory.v2","record_id":"VAL001-EXPLICIT-MUTATION-INVENTORY-2","mutations":items,"category_counts":counts,"total":len(items),"count_source":"LEN_OF_MUTATIONS_ARRAY_ONLY","scalar_baseline_counts_prohibited":True,"placeholder_values_prohibited":True}
 (root/MUTATION_INVENTORY).write_bytes(canonical_json(inv));report=execute_inventory(root);(root/MUTATION_COVERAGE).write_bytes(canonical_json(report));print(json.dumps({"total":len(items),"categories":counts},sort_keys=True))
if __name__=="__main__":main()
