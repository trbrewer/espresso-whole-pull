#!/usr/bin/env python3
"""Non-writing exhaustive VAL-001 deep-schema coverage verifier."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.validation.val001.deep_schema import FAMILY_SCHEMA_PATH,COVERAGE_PATH,build_family_schema,build_coverage,validate_family_records
from tools.validation.val001.framework import ContractError,canonical_json,load_json,sha256,validate_record
from tools.validation.val001.inventory import INVENTORY_PATH,REGISTRY_PATH,verify_inventory,verify_registry
from tools.validation.val001.schema import lint_schema
def verify(root:Path):
 expected_schema,mapping=build_family_schema(root); observed_schema=load_json(root/FAMILY_SCHEMA_PATH)
 if canonical_json(expected_schema)!=canonical_json(observed_schema):raise ContractError("deep family schema is stale")
 expected=build_coverage(root,mapping);observed=load_json(root/COVERAGE_PATH)
 if canonical_json(expected)!=canonical_json(observed):raise ContractError("coverage matrix is stale")
 seen=[r['path'] for r in observed['records']]
 if len(seen)!=len(set(seen)):raise ContractError("multiply registered governed record")
 for schema_path in sorted({r['schema_path'] for r in observed['records']}):lint_schema(load_json(root/schema_path))
 validated=validate_family_records(root,observed_schema,mapping)
 inventory=load_json(root/INVENTORY_PATH);registry=load_json(root/REGISTRY_PATH);verify_inventory(root,inventory);verify_registry(inventory,registry)
 registered=0
 for entry in registry['records']:
  path=root/entry['path'];schema=load_json(root/entry['schema_path']);lint_schema(schema)
  if path.suffix=='.jsonl':
   for line in path.read_text(encoding='utf-8').splitlines():validate_record(json.loads(line),schema)
  else:validate_record(load_json(path),schema)
  if sha256(path)!=entry['sha256']:raise ContractError(f"registered hash mismatch: {entry['path']}")
  registered+=1
 sidecars=sum(r['treatment']=="IMMUTABLE_HISTORICAL_SIDECAR" for r in observed['records'])
 if sidecars:raise ContractError("historical sidecar remains primary")
 return {"records":registered,"coverage_matrix_records":len(seen),"families":len(observed_schema['anyOf'])+2,"deep_json_records":validated,"sidecar_primary":sidecars,"unregistered":0,"multiply_registered":0,"real_data_comparisons":0}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",required=True,type=Path);a=p.parse_args();print(json.dumps(verify(a.root.resolve()),sort_keys=True))
if __name__=="__main__":main()
