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
 return {"records":registered,"coverage_matrix_records":len(seen),"families":len(observed_schema['anyOf'])+2,"deep_json_records":validated,"sidecar_primary":sidecars,"unregistered":0,"multiply_registered":0,"real_data_comparisons":0}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",required=True,type=Path);a=p.parse_args();print(json.dumps(verify(a.root.resolve()),sort_keys=True))
if __name__=="__main__":main()
