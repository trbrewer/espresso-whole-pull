#!/usr/bin/env python3
"""Fixed-boundary verifier for WP-0.3B."""
import argparse, ast, hashlib, json, subprocess
from pathlib import Path

BASELINE="7f26b643fde4c99263384c402547e9d6c606c99e"
FINAL=frozenset({
".github/workflows/static-validation.yml","PACKAGE_QA_STATUS.json","SOURCE_PACKAGE_MANIFEST.json",
"docs/DEVELOPMENT_HISTORY.md","docs/PROJECT_STATE.md","docs/PUCKWORKS_INTEGRATION.md","docs/QA_STATUS.md",
"docs/verification/WP_0_3B_NONPROTECTED_EXTRACTION_REFERENCES.md","scripts/generate_source_manifest.py",
"scripts/verify_wp03_evidence_review.py","scripts/verify_wp03b_nonprotected_verification.py","tests/test_wp03b_boundary.py",
"tests/test_wp03b_liang2021.py","tests/test_wp03b_matias2023.py","tests/test_wp03b_moroney2017.py",
"tests/test_wp03b_observables.py","tools/reference/wp03b/__init__.py","tools/reference/wp03b/canonical_run.py",
"tools/reference/wp03b/liang2021.py","tools/reference/wp03b/matias2023.py","tools/reference/wp03b/moroney2017.py",
"tools/reference/wp03b/observables.py","tools/reference/wp03b/provenance.py",
"validation/contracts/WP_0_3B_NONPROTECTED_EXTRACTION_VERIFICATION_CONTRACT.json",
"validation/results/WP_0_3B_NONPROTECTED_EXTRACTION_VERIFICATION_RESULT.json"})
PRE=FINAL-{"validation/results/WP_0_3B_NONPROTECTED_EXTRACTION_VERIFICATION_RESULT.json"}
FROZEN={
"validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json":"75a79e9972176668a8bfdb574ea16cbf39373a9ea11078009bc7b997c2f76859",
"validation/wp02/WP02_001_CLOSURE_CONTRACT.json":"2c898dd91e558ce62006dc81de9cff20bb633b52a89f6fa5a44c5edcda50d57a",
"config/reference_R0.json":"67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286",
"config/reconstruction_R1_waszkiewicz_9bar.json":"be275c0302f30dc4dcab120469b0bc62d444e401a80e082a337d9225c659b876",
"config/reconstruction_WP02A_waszkiewicz_9bar.json":"81a9089061d762aaf785a7764cebb8e0947e4f3c14bb833d58a204d2c816407e",
"config/reconstruction_WP02A_waszkiewicz_8bar.json":"ac87cfdff2862401b33ac01fa31d87bf966e062cecd153ce59ab4a9518feb57e"}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def paths(root):
 c=subprocess.run(["git","diff","--name-only",BASELINE],cwd=root,text=True,capture_output=True)
 u=subprocess.run(["git","ls-files","--others","--exclude-standard"],cwd=root,text=True,capture_output=True)
 if c.returncode or u.returncode:return None
 out=set(c.stdout.splitlines())|set(u.stdout.splitlines())
 out.discard("cases/reference_R0_20g_58mm_9bar/preflight/STATIC_VALIDATION_REPORT_V0_2_0.json")
 return out
def evaluate(contract, changed, hashes, imports, result):
 expected=FINAL if result else PRE
 return {
 "classification":contract["classification"]==["NONPROTECTED_REFERENCE_IMPLEMENTATION","EVIDENCE_AND_NUMERICAL_VERIFICATION_SUPPORT_ONLY","NO_GOVERNING_PHYSICS_CHANGE","NO_OPENFOAM_EXECUTION","NO_RUNTIME_WP02_COUPLING","NO_PUCKWORKS_CODE_EXECUTION","NO_PROTECTED_SOURCE_ACCESS","NO_PHYSICAL_VALIDATION_CLAIM"],
 "contract_path_set_exact":set(contract["permitted_changed_paths"])==FINAL,
 "repository_path_set_exact":changed==expected,"frozen_hashes":hashes==FROZEN,
 "no_forbidden_imports":not (imports&{"puckworks","solver","analyze_wp02"}),
 "runtime_lock":contract["puckworks"]["runtime_lock_commit"]=="fc61c4670ec7bf801e40bb391aab16048b8da26b",
 "bounded_claim":"No experimental extraction validation" in contract["claim_ceiling"]
 and "physical validation is established" in contract["claim_ceiling"],
 "result_binding":result is None or (result["implementation"]["commit"] not in ("",None)
 and result["execution_counts"]=={"canonical_reference":1,"puckworks_code":0,"openfoam":0,"protected_access":0,"wp02_analyzer":0,"scientific_scores":0}
 and result["runtime_wp02_coupling"] is False and result["physical_validation"]=="NOT_ESTABLISHED")}
def verify(root):
 contract=json.loads((root/"validation/contracts/WP_0_3B_NONPROTECTED_EXTRACTION_VERIFICATION_CONTRACT.json").read_text())
 result_path=root/"validation/results/WP_0_3B_NONPROTECTED_EXTRACTION_VERIFICATION_RESULT.json"
 result=json.loads(result_path.read_text()) if result_path.exists() else None
 imports=set()
 for p in (root/"tools/reference/wp03b").glob("*.py"):
  for n in ast.walk(ast.parse(p.read_text())):
   if isinstance(n,ast.Import):imports.update(a.name.split(".")[0] for a in n.names)
   elif isinstance(n,ast.ImportFrom) and n.module:imports.add(n.module.split(".")[0])
 checks=evaluate(contract,paths(root),{p:sha(root/p) for p in FROZEN},imports,result)
 return {"schema_version":"espresso.public.wp_0_3b_boundary.v1","status":"PASS" if all(checks.values()) else "FAIL","checks":checks,"changed_paths":sorted(paths(root) or [])}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--output",type=Path);a=p.parse_args()
 r=verify(a.root.resolve());s=json.dumps(r,indent=2,sort_keys=True)+"\n"
 if a.output:a.output.write_text(s)
 print(s,end="");return 0 if r["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
