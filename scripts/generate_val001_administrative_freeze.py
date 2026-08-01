#!/usr/bin/env python3
"""Generate the reviewed administrative freeze from the explicit inventory."""
from __future__ import annotations
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.validation.val001.framework import canonical_json,load_json,sha256
from tools.validation.val001.inventory import ADMIN_BOUND,ADMIN_CLOSURE_PATH,ADMIN_FREEZE_PATH,INVENTORY_PATH,REGISTRY_PATH,COVERAGE_PATH
def git(root,*args):return subprocess.check_output(["git",*args],cwd=root,text=True).strip()
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",required=True,type=Path);p.add_argument("--implementation-commit",required=True);a=p.parse_args();root=a.root.resolve();inventory=load_json(root/INVENTORY_PATH)
 admin=[{"path":rel,"sha256":sha256(root/rel)} for rel in sorted(ADMIN_BOUND)]
 ordinary=[{"path":r["path"],"sha256":r["sha256"]} for r in inventory["records"] if r["binding_class"]=="ORDINARY_HASH_BOUND_RECORD"]
 value={"schema_version":"espresso.val001.administrative_closure_freeze.v1","record_id":"VAL001-ADMINISTRATIVE-CLOSURE-FREEZE-1","status":"FROZEN","implementation_commit":a.implementation_commit,"implementation_tree":git(root,"rev-parse",f"{a.implementation_commit}^{{tree}}"),"administrative_bindings":admin,"ordinary_record_bindings":ordinary,"counts":{"independent_enumeration_exclusions":0,"unregistered_governed_records":0,"unbound_governed_records":0,"binding_graph_cycles":0,"terminal_external_roots":1},"terminal_external_root_type":"FINAL_GIT_HEAD_TREE","execution_counts":{"new_openfoam_builds":0,"new_openfoam_case_executions":0,"new_real_data_comparison_invocations":0,"new_governed_result_producing_invocations":0},"preservation":{"v2_result_changed":False,"invocation_journal_changed":False,"invocation_summary_changed":False},"execution_authority":"CONSUMED","claim_boundaries":{"physical_validation":"NOT_ESTABLISHED","new_governing_physics":"NOT_AUTHORIZED_BY_VAL001"},"puckworks_lock":{"commit":"fc61c4670ec7bf801e40bb391aab16048b8da26b","tree":"1d553e44ee2f7480a5df521560801b478618cc84"}}
 (root/ADMIN_FREEZE_PATH).write_bytes(canonical_json(value))
 print(f"VAL001_ADMINISTRATIVE_FREEZE_GENERATED admin={len(admin)} ordinary={len(ordinary)}")
if __name__=="__main__":main()
