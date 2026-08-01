#!/usr/bin/env python3
"""Generate the successor consumed lock from the committed correction freeze."""
from __future__ import annotations
import argparse,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.validation.val001.framework import canonical_json,sha256

LOCK="validation/val001/contracts/VAL_001_POSTRESULT_EXECUTION_LOCK.json"
FREEZE="validation/val001/contracts/VAL_001_SCHEMA_PROVENANCE_AND_SEMANTIC_COMPLETION_FREEZE.json"
PATHS=["validation/val001/VAL_001_ADMINISTRATIVE_CLOSURE_SPECIFICATION.json","validation/val001/VAL_001_EXTERNAL_CANDIDATE_ROOT_VERIFICATION_PROTOCOL.json","validation/val001/VAL_001_NORMATIVE_SCHEMA_CONTRACT_REGISTRY.json","validation/val001/VAL_001_SCHEMA_PROVENANCE_TRANSITION_MATRIX.json","validation/val001/VAL_001_SCHEMA_TAXONOMY_AND_COUNTING_SPECIFICATION.json","validation/val001/VAL_001_SEMANTIC_PROFILE_REGISTRY.json","validation/val001/VAL_001_IMMUTABLE_PROFILE_ASSIGNMENT_REGISTRY.json","validation/val001/VAL_001_EXPLICIT_MUTATION_INVENTORY.json","validation/val001/VAL_001_MUTATION_EXECUTION_COVERAGE.json","validation/val001/VAL_001_GOVERNED_RECORD_INVENTORY.json","validation/val001/VAL_001_GOVERNED_SCHEMA_REGISTRY.json","validation/val001/VAL_001_DEEP_SCHEMA_COVERAGE_MATRIX.json","validation/val001/VAL_001_INVOCATION_EVENTS.jsonl","validation/val001/VAL_001_INVOCATION_SUMMARY_V2.json","validation/val001/results/VAL_001_CORRECTED_COMPONENT_COMPARISONS_V2.json","scripts/run_val001_corrected_comparison.py"]
def git(root,*args):return subprocess.check_output(["git",*args],cwd=root,text=True).strip()
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",required=True,type=Path);p.add_argument("--freeze-commit",required=True);a=p.parse_args();root=a.root.resolve();commit=git(root,"rev-parse",a.freeze_commit)
 value={"alternate_activation_allowed":False,"alternate_authority_allowed":False,"alternate_invocation_id_allowed":False,"alternate_ledger_allowed":False,"authority_status":"CONSUMED","bindings":[{"path":path,"sha256":sha256(root/path)} for path in PATHS],"branch":"validation/val-001-source-adapters","claim_boundaries":{"experimental_commissioning":"NOT_AUTHORIZED","general_physical_validation":"NOT_ESTABLISHED","general_whole_solver_physical_validation":"NOT_ESTABLISHED","holdout_execution":"NOT_AUTHORIZED","new_governing_physics":"NOT_AUTHORIZED_BY_VAL001","physical_validation":"NOT_ESTABLISHED","protected_or_holdout_scoring":"NOT_AUTHORIZED"},"freeze_binding":{"commit":commit,"path":FREEZE,"sha256":sha256(root/FREEZE),"tree":git(root,"rev-parse",commit+"^{tree}")},"further_retry_authorized":False,"issue":37,"puckworks_lock":{"commit":"fc61c4670ec7bf801e40bb391aab16048b8da26b","tree":"1d553e44ee2f7480a5df521560801b478618cc84"},"pull_request":38,"record_id":"VAL001-POSTRESULT-EXECUTION-LOCK-9-SCHEMA-PROVENANCE","remaining_governed_result_producing_invocations":0,"remaining_real_data_comparison_invocations":0,"schema_version":"espresso.val001.postresult_execution_lock.v3","task":"VAL-001"}
 (root/LOCK).write_bytes(canonical_json(value))
if __name__=="__main__":main()
