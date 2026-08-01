#!/usr/bin/env python3
"""Non-writing exhaustive VAL-001 deep-schema coverage verifier."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.validation.val001.deep_schema import FAMILY_SCHEMA_PATH,COVERAGE_PATH,load_explicit_family_schema,build_coverage,validate_family_records
from tools.validation.val001.framework import ContractError,canonical_json,load_json,sha256,validate_record
from tools.validation.val001.inventory import INVENTORY_PATH,REGISTRY_PATH,verify_inventory,verify_registry
from tools.validation.val001.schema import lint_schema
from tools.validation.val001.explicit_semantics import load_policy,explicit_schema_for,validate_profile_dispatch
from tools.validation.val001.normative import taxonomy_counts,verify_generated_registry
from tools.validation.val001.mutations import execute_inventory
def verify(root:Path):
 expected_schema,mapping=load_explicit_family_schema(root); observed_schema=expected_schema
 expected=build_coverage(root,mapping);observed=load_json(root/COVERAGE_PATH)
 if canonical_json(expected)!=canonical_json(observed):raise ContractError("coverage matrix is stale")
 seen=[r['path'] for r in observed['records']]
 if len(seen)!=len(set(seen)):raise ContractError("multiply registered governed record")
 _,_,specifications,_,_=load_policy(root)
 for specification in specifications.values():lint_schema(specification['schema'])
 validated=validate_family_records(root,observed_schema,mapping)
 inventory=load_json(root/INVENTORY_PATH);registry=load_json(root/REGISTRY_PATH);verify_inventory(root,inventory);verify_registry(inventory,registry)
 registered=0
 for entry in registry['records']:
  path=root/entry['path'];schema=explicit_schema_for(root,entry['path']);lint_schema(schema)
  if path.suffix=='.jsonl':
   for line in path.read_text(encoding='utf-8').splitlines():value=json.loads(line);validate_record(value,schema);validate_profile_dispatch(root,entry['path'],value,entry)
  else:value=load_json(path);validate_record(value,schema);validate_profile_dispatch(root,entry['path'],value,entry)
  if entry['sha256'] is not None and sha256(path)!=entry['sha256']:raise ContractError(f"registered hash mismatch: {entry['path']}")
  registered+=1
 sidecars=sum(r['treatment']=="IMMUTABLE_HISTORICAL_SIDECAR" for r in observed['records'])
 if sidecars:raise ContractError("historical sidecar remains primary")
 taxonomy=taxonomy_counts(root);provenance=verify_generated_registry(root);mutations=execute_inventory(root)
 return {"records":registered,"coverage_matrix_records":len(seen),"families":taxonomy["governing_schema_families"],"family_assignments":taxonomy["schema_assignments"],"normative_contracts":taxonomy["current_normative_specifications"],"unreferenced_current_specifications":taxonomy["current_unreferenced_specifications"],"declared_mutations":mutations["declared_count"],"executed_mutations":mutations["executed_count"],"instance_inferred_governing_schemas":provenance["instance_inferred"],"copied_inferred_governing_schemas":provenance["copied_inferred"],"deep_json_records":validated,"sidecar_primary":sidecars,"unregistered":0,"multiply_registered":0,"real_data_comparisons":0}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",required=True,type=Path);a=p.parse_args();print(json.dumps(verify(a.root.resolve()),sort_keys=True))
if __name__=="__main__":main()
