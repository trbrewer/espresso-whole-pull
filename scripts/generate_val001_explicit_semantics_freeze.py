#!/usr/bin/env python3
"""Generate the explicit-semantics freeze without scientific computation."""
from __future__ import annotations
import argparse,hashlib,json,subprocess
from pathlib import Path

LINEAGE={"original_result_sha256":"07086313d022555032bbb9ecc18d2564bb197d0381bd8d08e263cd95d02bd029","failed_invocation_sha256":"529dc254d46ac65bf1c1fa1d98eb4bf799dfe5712302e729b4c72fc49b154919","v2_result_sha256":"7968e3b99045da9500442932c536bf920d559ebe660d2bad01f954f36b3f75b5","invocation_journal_sha256":"f66ee8a29bab276e650d3d5c01fab5b0b78480453da0841b096e103512591730","invocation_summary_sha256":"01855ee4769ff9b12d97b98cf80530079ff906ca76d0c5710ea2c43efd766ea8"}
PATHS=["validation/val001/VAL_001_EXPLICIT_SCHEMA_SPECIFICATION_REGISTRY.json","validation/val001/VAL_001_SEMANTIC_PROFILE_REGISTRY.json","validation/val001/VAL_001_EXPLICIT_MUTATION_INVENTORY.json","validation/val001/VAL_001_EXTERNAL_CANDIDATE_ROOT_VERIFICATION_PROTOCOL.json","validation/val001/VAL_001_GOVERNED_RECORD_INVENTORY.json","validation/val001/VAL_001_GOVERNED_SCHEMA_REGISTRY.json","validation/val001/VAL_001_DEEP_SCHEMA_COVERAGE_MATRIX.json","tools/validation/val001/schema.py","tools/validation/val001/deep_schema.py","tools/validation/val001/explicit_semantics.py","tools/validation/val001/administrative.py","scripts/verify_val001_administrative_closure.py","scripts/verify_val001_deep_schema_coverage.py","tests/test_val001_explicit_semantics_and_root.py"]
def git(root,*args):return subprocess.check_output(["git",*args],cwd=root,text=True).strip()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--implementation-commit',required=True);p.add_argument('--output',required=True,type=Path);a=p.parse_args();root=a.root.resolve()
 implementation_commit=git(root,'rev-parse',a.implementation_commit)
 value={"schema_version":"espresso.val001.explicit_semantics_completion_freeze.v1","record_id":"VAL001-EXPLICIT-SEMANTICS-COMPLETION-FREEZE-1","status":"FROZEN","implementation":{"commit":implementation_commit,"tree":git(root,'rev-parse',implementation_commit+'^{tree}')},"bindings":[{"path":x,"sha256":hashlib.sha256((root/x).read_bytes()).hexdigest()} for x in sorted(PATHS)],"counts":{"instance_derived_governing_schemas":0,"records_without_executable_semantic_profiles":0,"expected_root_must_be_externally_supplied":True,"terminal_root_self_embedded":False},"preserved_lineage":LINEAGE,"puckworks_lock":{"commit":"fc61c4670ec7bf801e40bb391aab16048b8da26b","tree":"1d553e44ee2f7480a5df521560801b478618cc84"},"execution":{"new_openfoam_builds":0,"new_openfoam_case_executions":0,"new_real_data_comparison_invocations":0,"new_governed_result_producing_invocations":0,"execution_authority":"CONSUMED"},"claim_boundaries":{"physical_validation":"NOT_ESTABLISHED","new_governing_physics":"NOT_AUTHORIZED_BY_VAL001"}}
 a.output.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
