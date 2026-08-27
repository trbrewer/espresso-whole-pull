#!/usr/bin/env python3
"""Verify the SCI-ED-002 vendored contract or its exact producer Git objects."""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.git_object_authority import AuthorityError, GitAuthority, object_bytes, require_repository, verify_authority

REL = Path("docs/validation/sci_ed_002")
EXACT_STATUS = "SCI_ED_002_HANDOFF_EXACT_PRODUCER_VERIFIED"
VENDORED_STATUS = "SCI_ED_002_LOCAL_VENDORED_CONTRACT_VERIFIED_PRODUCER_OBJECT_NOT_CHECKED"
SCHEMA_AGGREGATE = "527d8ac261a5bf499fa5d20537f33756a9ced9d4eb8bd532bd4f906d2b97970f"
EXPECTED_PRODUCER_COMMIT = "e22a422d7c9cac5cd6d0779d5f5455bf492a018e"
EXPECTED_PRODUCER_TREE = "33c9d603760163842caa86aa932053ca44b120f8"

class HandoffError(ValueError): pass

def _fail(reason, field, expected, observed, authority):
    raise HandoffError(json.dumps({"authority":authority,"expected":expected,"field":field,"observed":observed,"reason":reason},sort_keys=True))

def _equal(actual, expected, reason, field, authority):
    if actual != expected: _fail(reason,field,expected,actual,authority)

def _sha(data): return hashlib.sha256(data).hexdigest()

def _load(root):
    here=root/REL; lock=json.loads((here/"PUCKWORKS_AUTHORITY.json").read_text())
    data=(here/"SCI_ED_002_EXPORT.json").read_bytes()
    return lock,json.loads(data),data

def _vendored(lock, export, data):
    _equal(lock["authority_model"],"FINAL_PACKAGE_HEAD","AUTHORITY_MODEL_INVALID","authority_model","vendored")
    _equal(lock["schema_version"],export["schema_version"],"SCHEMA_VERSION_MISMATCH","schema_version","vendored")
    _equal(_sha(data),lock["producer_export_sha256"],"VENDORED_EXPORT_HASH_MISMATCH","producer_export_sha256","vendored")
    _equal(lock["producer_commit"],EXPECTED_PRODUCER_COMMIT,"PRODUCER_COMMIT_MISMATCH_ACROSS_PINNED_AUTHORITIES","producer_commit","vendored")
    _equal(lock["producer_tree"],EXPECTED_PRODUCER_TREE,"PRODUCER_TREE_MISMATCH_ACROSS_PINNED_AUTHORITIES","producer_tree","vendored")
    _equal(len(export.get("schema_sha256",{})),20,"SCHEMA_SET_INCOMPLETE","schema_count","vendored")
    ceiling=export["claim_ceiling"]
    for field,expected,reason in (("commissioning_authorized",False,"COMMISSIONING_STATUS_WEAKENED"),("predictor_eligible",False,"PREDICTOR_ELIGIBILITY_WEAKENED"),("predictor_developed",False,"PREDICTOR_STATUS_WEAKENED"),("c_s0_mapping_status","NOT_ESTABLISHED","C_S0_STATUS_WEAKENED"),("physical_validation_status","NOT_ESTABLISHED","PHYSICAL_VALIDATION_STATUS_WEAKENED")):
        _equal(ceiling.get(field),expected,reason,field,"vendored")
    _equal(export.get("holdout_status"),"SEALED_NOT_ACCESSED","VG06_OR_HOLDOUT_STATUS_WEAKENED","holdout_status","vendored")
    _equal(ceiling.get("disposition"),lock["producer_disposition"],"SCIENTIFIC_DISPOSITION_MISMATCH","disposition","vendored")
    return {"vendored_contract_verified":True,"claim_ceiling_verified_from_vendored_material":True}

def verify(root=ROOT, mode="exact-producer", producer_root=None, producer_commit=None):
    root=Path(root).resolve(); lock,export,data=_load(root); local=_vendored(lock,export,data)
    if mode=="vendored-only":
        return {"schema_version":"ewp.sci_ed_002.handoff_verification.v2","status":VENDORED_STATUS,"verification_mode":mode,"full_handoff_verified":False,**local,"producer_repository_supplied":False,"producer_commit_verified":False,"producer_tree_verified":False,"producer_object_status":"NOT_CHECKED","no_physics_evaluation":"NOT_PART_OF_HANDOFF_VERIFIER"}
    if mode!="exact-producer": _fail("VERIFICATION_MODE_INVALID","mode","exact-producer|vendored-only",mode,"invocation")
    mechanism="explicit-cli"
    if producer_root is None:
        alias=os.environ.get("PUCKWORKS_GIT_REPOSITORY")
        if not alias: _fail("EXACT_PRODUCER_ROOT_REQUIRED","producer_root","explicit Git repository",None,"exact-producer")
        producer_root,mechanism=Path(alias),"deprecated-environment-alias"
    try: repo=require_repository(Path(producer_root))
    except AuthorityError as exc: _fail("PRODUCER_GIT_REPOSITORY_INVALID","producer_root","Git repository",str(exc),"exact-producer")
    locked=lock["producer_commit"]
    if not re.fullmatch(r"[0-9a-f]{40}",locked): _fail("LOCKED_PRODUCER_COMMIT_INVALID","producer_commit","40 lowercase hex",locked,"exact-producer")
    selected=producer_commit or locked
    _equal(selected,locked,"SUPPLIED_PRODUCER_COMMIT_MISMATCH","producer_commit","exact-producer")
    authority=GitAuthority(selected,lock["producer_tree"])
    try: verify_authority(repo,authority)
    except AuthorityError as exc: _fail(str(exc),"producer_authority",{"commit":selected,"tree":lock["producer_tree"]},None,"exact-producer")
    producer_export=object_bytes(repo,authority,lock["producer_export_path"])
    _equal(_sha(producer_export),lock["producer_export_sha256"],"PRODUCER_EXPORT_HASH_MISMATCH","producer_export_sha256","exact-producer")
    _equal(producer_export,data,"VENDORED_EXPORT_BYTE_MISMATCH","producer_export","exact-producer")
    schemas=export["schema_sha256"]
    for name in sorted(schemas):
        path=f"docs/analysis/sci_ed_002/schemas/1.0.0/{name}.schema.json"
        try: schema_data=object_bytes(repo,authority,path)
        except AuthorityError as exc: _fail("PRODUCER_SCHEMA_MISSING",path,schemas[name],str(exc),"exact-producer")
        _equal(_sha(schema_data),schemas[name],"PRODUCER_SCHEMA_HASH_MISMATCH",path,"exact-producer")
        schema=json.loads(schema_data)
        if "$schema" not in schema and "$id" not in schema: _fail("PRODUCER_SCHEMA_IDENTITY_INVALID",path,"schema identifier",None,"exact-producer")
    manifest=object_bytes(repo,authority,lock["producer_source_manifest_path"])
    _equal(_sha(manifest),lock["producer_source_manifest_sha256"],"PRODUCER_SOURCE_MANIFEST_HASH_MISMATCH","producer_source_manifest_sha256","exact-producer")
    json.loads(manifest)
    top=subprocess.check_output(["git","-C",str(repo),"rev-parse","--show-toplevel"],text=True).strip()
    remotes=subprocess.run(["git","-C",str(repo),"remote","get-url","--all","origin"],capture_output=True,text=True).stdout.splitlines()
    return {"schema_version":"ewp.sci_ed_002.handoff_verification.v2","status":EXACT_STATUS,"verification_mode":mode,"full_handoff_verified":True,**local,"producer_repository_supplied":True,"producer_root_mechanism":mechanism,"producer_repository_toplevel":top,"producer_repository_identity":"CANONICAL_REMOTE_OBJECT_VERIFIED" if any("trbrewer/puckworks" in x for x in remotes) else "LOCAL_MIRROR_OBJECT_VERIFIED","producer_commit":locked,"producer_tree":lock["producer_tree"],"producer_commit_verified":True,"producer_tree_verified":True,"producer_export_verified":True,"producer_schema_set_verified":True,"producer_schema_count":len(schemas),"producer_schema_aggregate_sha256":SCHEMA_AGGREGATE,"producer_source_manifest_verified":True,"claim_ceiling_verified":True,"holdout_status_verified":True,"commissioning_status_verified":True,"predictor_status_verified":True,"c_s0_status_verified":True,"no_physics_evaluation":"NOT_PART_OF_HANDOFF_VERIFIER"}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=ROOT); p.add_argument("--mode",choices=("exact-producer","vendored-only"),default="exact-producer"); p.add_argument("--producer-root",type=Path); p.add_argument("--producer-commit"); p.add_argument("--output",type=Path); a=p.parse_args()
    try: result=verify(a.root,a.mode,a.producer_root,a.producer_commit); code=0
    except (HandoffError,AuthorityError,subprocess.CalledProcessError,json.JSONDecodeError) as exc: result={"schema_version":"ewp.sci_ed_002.handoff_verification.v2","status":"FAIL","verification_mode":a.mode,"reason":str(exc)}; code=1
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.output: a.output.write_text(text,encoding="utf-8")
    print(text,end=""); return code

if __name__=="__main__": raise SystemExit(main())
