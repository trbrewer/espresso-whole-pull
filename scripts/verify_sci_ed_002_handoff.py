#!/usr/bin/env python3
"""Authoritative SCI-ED-002 vendored and exact-producer decision path."""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.git_object_authority import AuthorityError, GitAuthority, object_bytes, require_repository, verify_authority

EXACT_STATUS="SCI_ED_002_HANDOFF_EXACT_PRODUCER_VERIFIED"
VENDORED_STATUS="SCI_ED_002_LOCAL_VENDORED_CONTRACT_VERIFIED_PRODUCER_OBJECT_NOT_CHECKED"
RETIRED_AGGREGATE="RETIRED_NO_AUTHORITATIVE_AGGREGATION_ALGORITHM"
REL=Path("docs/validation/sci_ed_002")
DISPOSITION="SCI_ED_002_PROTOCOL_INCOMPLETE_COMMISSIONING_BLOCKED_REFERENCE_EXTRACTABILITY_STOPPING_RULE_NOT_DEFENSIBLY_FROZEN"
SCHEMAS={"analytical_batches":"a6b084871533ed739317006f7d1b07c509a9a599d6082b94d6e890a3e30949b2","base_coffee_materials":"f43bc4681638b76cc33603f9b666e1340d26520c72be956828c1a090e52ebcad","bridge_assignments":"fd05af5c9c7f6b36204fb7d98a30f1ed8f80b32d45d9d66a0561dc20989e02cb","chain_of_custody":"88e74cfb37a719e102f7252b9d164c66bc77e09e0672a50f1b8408af53bd516b","chemistry_measurements":"2f6759365c522f53b52d6be910ec8af1e970e8d736f9cac590cdbb8e094ce435","exclusions_and_reruns":"bb87e706f099047f70f1ca223c19037ca9f45ca67305f6a59980fc9c39b505d4","file_manifest":"96f238850b243c21ecddf35d82dc1afe04f150b8448277532bda838f4a1bec7d","holdout_registry":"20118c596afc3ae8123c543feb76e34a0f80901044630cfe761e3fccc5253f6b","laboratories":"3383bf8e8670863256ce7247fbdc1e6e1ca787e1205be5271f8c52d47711d7a2","material_roast_units":"8cddec5854fb0763a737e4d76452f05ef9e050514fd6527cd904dfe984455c49","moisture_measurements":"05422fee99a129e8871e79e8ccc976477be3efc7eedc72b91c0d5c19c390b1da","quality_control_measurements":"65ff7d242319bdb9f94af82d6cdc1702cac1c8b5cb61eab8c9a8c5d2404d74a1","reference_extraction_runs":"1da6bbed29e440d3c3590fc0d12ff3430a2a2bee933a409564b69128d6d6d5e3","reference_extraction_steps":"bc1dda55933eda8b9702cb22bc7710757f9e334caff4a9d178d8fcaefc60fb52","roast_measurements":"3f33d253381378112ad3ee9fddc2a79bdf6531d7add1a34feb7a051e6bb92eb8","sample_aliquots":"5a4d4c6bc1b615bfea832ef96a5bc2672b83b147e049e249c52cca0123f60eb3","study_source_groups":"a8de4c32bb467c288ef4c52deedc760b5773d699fffa0d7e219f376c9baf0269","total_content_measurements":"050e3896eabdf0d3cdc572ed6e60e5a08e80f2222082335828c7fff293d2c628","uncertainty_components":"93ce3447a5ceea46ea30e4f4b522b1bca64e9a218d0f5fbb847a42a32e3675b4","validation_groups":"5ed2f252060927c9e358becde19ab1f5da5d1485bd0bd694881c979d829d843c"}
_PRODUCTION_POLICY={"repository":"https://github.com/trbrewer/puckworks.git","commit":"e22a422d7c9cac5cd6d0779d5f5455bf492a018e","tree":"33c9d603760163842caa86aa932053ca44b120f8","export_path":"docs/analysis/sci_ed_002/SCI_ED_002_EXPORT.json","export_sha256":"18716c638a1837a8719a55b579e45514b217b686e9a6960ef8cc8379e7bc0d34","manifests":{"scientific_package":{"path":"docs/analysis/sci_ed_002/SOURCE_MANIFEST.json","sha256":"bfcc32b28b7a5662778b1bdb25d03b735f637961e92654658e1de4de8699f146","member_commit":"2b8c3937bf05c4c0cc00b1bbe532845532a48e1e","member_tree":"b9c84f73bbc1057d63edccb0018a6a7b04d7d4ea"},"r1_evidence":{"path":"docs/analysis/sci_ed_002/r1/SOURCE_MANIFEST.json","sha256":"f7dd8f312079a7579a5698b788a7dab52ac359979ebd2281747e7c5fa51169b8","member_commit":"e22a422d7c9cac5cd6d0779d5f5455bf492a018e","member_tree":"33c9d603760163842caa86aa932053ca44b120f8"}},"schemas":SCHEMAS,"schema_aggregate_policy":RETIRED_AGGREGATE,"disposition":DISPOSITION,"claims":{"no_commissioning":True,"predictor_eligible":False,"c_s0_mapping_status":"NOT_ESTABLISHED","holdout_status":"SEALED_NOT_ACCESSED","governing_physics_change":False}}
CORE={"ANALYTICAL_SOP.md","ESTIMAND_CONTRACT.json","INDEPENDENCE_AND_HOLDOUT_PLAN.json","LABORATORY_BRIDGE_PLAN.json","PROSPECTIVE_ACCEPTANCE_GATES.json","SAMPLING_MATRIX.csv","UNCERTAINTY_MODEL.json"}

class HandoffError(ValueError):
    def __init__(self,reason,stage,field,expected,observed,expected_source="production-policy",observed_source="package"):
        self.detail={"reason":reason,"stage":stage,"field":field,"expected":expected,"observed":observed,"expected_source":expected_source,"observed_source":observed_source}; super().__init__(json.dumps(self.detail,sort_keys=True))
def sha(data): return hashlib.sha256(data).hexdigest()
def eq(a,b,reason,stage,field,**sources):
    if a!=b: raise HandoffError(reason,stage,field,b,a,**sources)
def load_package(root):
    here=Path(root)/REL; lock=json.loads((here/"PUCKWORKS_AUTHORITY.json").read_text()); data=(here/"SCI_ED_002_EXPORT.json").read_bytes(); return lock,json.loads(data),data

def conjunction(lock,export,policy):
    eq(lock["producer_commit"],policy["commit"],"PRODUCER_COMMIT_POLICY_MISMATCH","pin-conjunction","producer_commit")
    if export.get("producer_package_commit") is not None: eq(export["producer_package_commit"],policy["commit"],"PRODUCER_COMMIT_MISMATCH_ACROSS_PINNED_AUTHORITIES","pin-conjunction","producer_package_commit")
    eq(lock["producer_tree"],policy["tree"],"PRODUCER_TREE_POLICY_MISMATCH","pin-conjunction","producer_tree")
    pairs=[("no_commissioning",not export["claim_ceiling"]["commissioning_authorized"],True),("predictor_eligible",export["claim_ceiling"]["predictor_eligible"],False),("c_s0_mapping_status",export["claim_ceiling"]["c_s0_mapping_status"],"NOT_ESTABLISHED"),("holdout_status",export["holdout_status"],"SEALED_NOT_ACCESSED"),("governing_physics_change",export["claim_ceiling"]["governing_physics_change"],False)]
    checks={}
    for field,ev,required in pairs:
        lv=lock[field]; eq(lv,ev,"CLAIM_CEILING_LOCK_EXPORT_MISMATCH","claim-conjunction",field,expected_source="authority-lock",observed_source="vendored-export"); eq(lv,required,"CLAIM_CEILING_POLICY_MISMATCH","claim-policy",field); checks[field]={"lock":lv,"export":ev,"required":required,"internal_conjunction":"PASS","policy":"PASS"}
    for field in ("disposition","claim_ceiling.disposition"):
        ev=export["disposition"] if field=="disposition" else export["claim_ceiling"]["disposition"]
        eq(lock["producer_disposition"],ev,"CLAIM_CEILING_LOCK_EXPORT_MISMATCH","claim-conjunction",field,expected_source="authority-lock",observed_source="vendored-export"); eq(ev,policy["disposition"],"CLAIM_CEILING_POLICY_MISMATCH","claim-policy",field); checks[field]={"lock":lock["producer_disposition"],"export":ev,"required":policy["disposition"],"internal_conjunction":"PASS","policy":"PASS"}
    eq(lock["producer_export_sha256"],policy["export_sha256"],"EXPORT_PIN_POLICY_MISMATCH","pin-conjunction","producer_export_sha256")
    eq(export["schema_sha256"],policy["schemas"],"SCHEMA_PIN_POLICY_MISMATCH","pin-conjunction","schema_sha256")
    roles=lock.get("producer_manifests",{})
    for role,pin in policy["manifests"].items():
        if role not in roles: raise HandoffError("PRODUCER_MANIFEST_ROLE_MISSING","manifest-conjunction",role,pin,None)
        eq(roles[role]["path"],pin["path"],"PRODUCER_MANIFEST_ROLE_PATH_MISMATCH","manifest-conjunction",role)
        eq(roles[role]["sha256"],pin["sha256"],"PRODUCER_MANIFEST_ROLE_HASH_MISMATCH","manifest-conjunction",role)
        eq(roles[role]["member_authority_commit"],pin["member_commit"],"PRODUCER_MANIFEST_MEMBER_AUTHORITY_MISMATCH","manifest-conjunction",role)
        eq(roles[role]["member_authority_tree"],pin["member_tree"],"PRODUCER_MANIFEST_MEMBER_AUTHORITY_MISMATCH","manifest-conjunction",role)
    eq(export["source_manifest_sha256"],policy["manifests"]["scientific_package"]["sha256"],"EXPORT_SCIENTIFIC_MANIFEST_PIN_MISMATCH","manifest-conjunction","source_manifest_sha256")
    eq(lock.get("schema_aggregate_policy"),RETIRED_AGGREGATE,"SCHEMA_AGGREGATE_OVERCLAIM","schema-aggregate","schema_aggregate_policy")
    return checks

def verify_manifest(repo,authority,role,pin,base):
    data=object_bytes(repo,authority,pin["path"]); eq(sha(data),pin["sha256"],"PRODUCER_MANIFEST_HASH_MISMATCH","producer-manifest",role)
    member_authority=GitAuthority(pin["member_commit"],pin["member_tree"])
    try: verify_authority(repo,member_authority)
    except AuthorityError as exc: raise HandoffError(str(exc),"producer-manifest-member-authority",role,{"commit":pin["member_commit"],"tree":pin["member_tree"]},None)
    doc=json.loads(data); files=doc.get("files");
    if not isinstance(files,list) or not files: raise HandoffError("PRODUCER_MANIFEST_STRUCTURE_INVALID","producer-manifest",role,"nonempty files",files)
    seen=set()
    for item in files:
        path=item.get("path","")
        if not path or path.startswith("/") or ".." in Path(path).parts or path in seen: raise HandoffError("PRODUCER_MANIFEST_MEMBER_PATH_INVALID","producer-manifest",path,"unique relative path",path)
        seen.add(path); full=f"{base}/{path}"; member=object_bytes(repo,member_authority,full); eq(sha(member),item["sha256"],"PRODUCER_MANIFEST_MEMBER_HASH_MISMATCH","producer-manifest-member",full)
    if role=="scientific_package":
        missing=CORE-seen
        if missing: raise HandoffError("SCIENTIFIC_PACKAGE_CORE_MEMBER_MISSING","producer-manifest","core_members",sorted(CORE),sorted(missing))
        expected_schemas={f"schemas/1.0.0/{name}.schema.json" for name in SCHEMAS}
        if not expected_schemas.issubset(seen): raise HandoffError("SCIENTIFIC_PACKAGE_SCHEMA_MEMBER_MISSING","producer-manifest","schemas",sorted(expected_schemas),sorted(expected_schemas-seen))
    return {"role":role,"path":pin["path"],"expected_sha256":pin["sha256"],"observed_sha256":sha(data),"member_authority_commit":pin["member_commit"],"member_authority_tree":pin["member_tree"],"member_count":len(files),"members_verified":True,"status":"PASS"}

def decide(root=ROOT,mode="exact-producer",producer_root=None,policy=None):
    policy=policy or _PRODUCTION_POLICY; lock,export,vbytes=load_package(Path(root)); checks=conjunction(lock,export,policy)
    eq(sha(vbytes),policy["export_sha256"],"VENDORED_EXPORT_HASH_MISMATCH","vendored-package","export")
    common={"schema_version":"ewp.sci_ed_002.handoff_verification.v3","verification_mode":mode,"vendored_contract_verified":True,"claim_ceiling_conjunction":checks,"claim_ceiling_verified":True,"no_physics_evaluation":"NOT_PART_OF_HANDOFF_VERIFIER","schema_aggregate":{"status":RETIRED_AGGREGATE,"verified":False},"schema_individual_count":20}
    if mode=="vendored-only": return {**common,"status":VENDORED_STATUS,"full_handoff_verified":False,"producer_object_status":"NOT_CHECKED","producer_commit_verified":False,"producer_tree_verified":False,"producer_manifests":{"scientific_package":{"status":"NOT_CHECKED"},"r1_evidence":{"status":"NOT_CHECKED"}},"producer_schemas_status":"NOT_CHECKED"}
    if mode!="exact-producer": raise HandoffError("VERIFICATION_MODE_INVALID","cli","mode","exact-producer|vendored-only",mode)
    if producer_root is None:
        alias=os.environ.get("PUCKWORKS_GIT_REPOSITORY")
        if not alias: raise HandoffError("EXACT_PRODUCER_ROOT_REQUIRED","cli","producer_root","explicit Git repository",None)
        producer_root=Path(alias); mechanism="deprecated-environment-alias"
    else: mechanism="explicit-cli"
    try: repo=require_repository(Path(producer_root)); authority=GitAuthority(policy["commit"],policy["tree"]); verify_authority(repo,authority)
    except AuthorityError as exc: raise HandoffError(str(exc),"producer-object","commit_tree",{"commit":policy["commit"],"tree":policy["tree"]},None)
    pdata=object_bytes(repo,authority,policy["export_path"]); eq(sha(pdata),policy["export_sha256"],"PRODUCER_EXPORT_HASH_MISMATCH","producer-export","sha256"); eq(pdata,vbytes,"VENDORED_EXPORT_BYTE_MISMATCH","producer-export","bytes")
    manifests={"scientific_package":verify_manifest(repo,authority,"scientific_package",policy["manifests"]["scientific_package"],"docs/analysis/sci_ed_002"),"r1_evidence":verify_manifest(repo,authority,"r1_evidence",policy["manifests"]["r1_evidence"],"docs/analysis/sci_ed_002/r1")}
    for name,expected in sorted(policy["schemas"].items()):
        path=f"docs/analysis/sci_ed_002/schemas/1.0.0/{name}.schema.json"; data=object_bytes(repo,authority,path); eq(sha(data),expected,"PRODUCER_SCHEMA_HASH_MISMATCH","producer-schema",path); json.loads(data)
    return {**common,"status":EXACT_STATUS,"full_handoff_verified":True,"producer_object_status":"EXACT_OBJECT_VERIFIED","producer_root_mechanism":mechanism,"producer_commit":policy["commit"],"producer_tree":policy["tree"],"producer_commit_verified":True,"producer_tree_verified":True,"producer_export_verified":True,"producer_manifests":manifests,"producer_manifests_verified":True,"producer_schemas_status":"VERIFIED_20_OF_20","producer_schema_set_verified":True,"claim_ceiling_exact_producer_layer":"PASS"}

verify=decide

def atomic_write(path,payload):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w",dir=path.parent,prefix=path.name+".",delete=False,encoding="utf-8") as f: json.dump(payload,f,indent=2,sort_keys=True); f.write("\n"); temp=Path(f.name)
    os.replace(temp,path)
def parser():
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=ROOT); p.add_argument("--mode",choices=("exact-producer","vendored-only"),default="exact-producer"); p.add_argument("--producer-root",type=Path); p.add_argument("--output",type=Path); return p
def main(argv=None):
    a=parser().parse_args(argv)
    if a.output and a.output.exists(): a.output.unlink()
    try: result=decide(a.root,a.mode,a.producer_root); code=0
    except (HandoffError,AuthorityError,subprocess.CalledProcessError,json.JSONDecodeError,FileNotFoundError) as exc:
        detail=exc.detail if isinstance(exc,HandoffError) else {"reason":type(exc).__name__,"stage":"unhandled","observed":str(exc)}
        result={"schema_version":"ewp.sci_ed_002.handoff_verification.v3","status":"FAIL","full_handoff_verified":False,"verification_mode":a.mode,"failure":detail}; code=1
    if a.output: atomic_write(a.output,result)
    print(json.dumps(result,indent=2,sort_keys=True)); return code
if __name__=="__main__": raise SystemExit(main())
