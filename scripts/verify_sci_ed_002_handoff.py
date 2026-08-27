#!/usr/bin/env python3
"""Fail-closed SCI-ED-002 authority and exact-producer verifier."""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.git_object_authority import AuthorityError, GitAuthority, object_bytes, require_repository, verify_authority

EXACT_STATUS="SCI_ED_002_HANDOFF_EXACT_PRODUCER_VERIFIED"
VENDORED_STATUS="SCI_ED_002_LOCAL_VENDORED_CONTRACT_VERIFIED_PRODUCER_OBJECT_NOT_CHECKED"
DISPOSITION="SCI_ED_002_PROTOCOL_INCOMPLETE_COMMISSIONING_BLOCKED_REFERENCE_EXTRACTABILITY_STOPPING_RULE_NOT_DEFENSIBLY_FROZEN"
MD7_DISPOSITION="SCI_MD_007_INVENTORY_PRIOR_ONLY_ADDITIONAL_DIRECT_MEASUREMENTS_REQUIRED"
RETIRED_AGGREGATE="RETIRED_NO_AUTHORITATIVE_AGGREGATION_ALGORITHM"
REL=Path("docs/validation/sci_ed_002")
HEX40=re.compile(r"[0-9a-f]{40}\Z"); HEX64=re.compile(r"[0-9a-f]{64}\Z")
SCHEMA_HASHES={"analytical_batches":"a6b084871533ed739317006f7d1b07c509a9a599d6082b94d6e890a3e30949b2","base_coffee_materials":"f43bc4681638b76cc33603f9b666e1340d26520c72be956828c1a090e52ebcad","bridge_assignments":"fd05af5c9c7f6b36204fb7d98a30f1ed8f80b32d45d9d66a0561dc20989e02cb","chain_of_custody":"88e74cfb37a719e102f7252b9d164c66bc77e09e0672a50f1b8408af53bd516b","chemistry_measurements":"2f6759365c522f53b52d6be910ec8af1e970e8d736f9cac590cdbb8e094ce435","exclusions_and_reruns":"bb87e706f099047f70f1ca223c19037ca9f45ca67305f6a59980fc9c39b505d4","file_manifest":"96f238850b243c21ecddf35d82dc1afe04f150b8448277532bda838f4a1bec7d","holdout_registry":"20118c596afc3ae8123c543feb76e34a0f80901044630cfe761e3fccc5253f6b","laboratories":"3383bf8e8670863256ce7247fbdc1e6e1ca787e1205be5271f8c52d47711d7a2","material_roast_units":"8cddec5854fb0763a737e4d76452f05ef9e050514fd6527cd904dfe984455c49","moisture_measurements":"05422fee99a129e8871e79e8ccc976477be3efc7eedc72b91c0d5c19c390b1da","quality_control_measurements":"65ff7d242319bdb9f94af82d6cdc1702cac1c8b5cb61eab8c9a8c5d2404d74a1","reference_extraction_runs":"1da6bbed29e440d3c3590fc0d12ff3430a2a2bee933a409564b69128d6d6d5e3","reference_extraction_steps":"bc1dda55933eda8b9702cb22bc7710757f9e334caff4a9d178d8fcaefc60fb52","roast_measurements":"3f33d253381378112ad3ee9fddc2a79bdf6531d7add1a34feb7a051e6bb92eb8","sample_aliquots":"5a4d4c6bc1b615bfea832ef96a5bc2672b83b147e049e249c52cca0123f60eb3","study_source_groups":"a8de4c32bb467c288ef4c52deedc760b5773d699fffa0d7e219f376c9baf0269","total_content_measurements":"050e3896eabdf0d3cdc572ed6e60e5a08e80f2222082335828c7fff293d2c628","uncertainty_components":"93ce3447a5ceea46ea30e4f4b522b1bca64e9a218d0f5fbb847a42a32e3675b4","validation_groups":"5ed2f252060927c9e358becde19ab1f5da5d1485bd0bd694881c979d829d843c"}
SCHEMAS=SCHEMA_HASHES
CORE={"ANALYTICAL_SOP.md","ESTIMAND_CONTRACT.json","INDEPENDENCE_AND_HOLDOUT_PLAN.json","LABORATORY_BRIDGE_PLAN.json","PROSPECTIVE_ACCEPTANCE_GATES.json","SAMPLING_MATRIX.csv","UNCERTAINTY_MODEL.json"}

def schema_policy(): return {n:{"path":f"docs/analysis/sci_ed_002/schemas/1.0.0/{n}.schema.json","sha256":v} for n,v in SCHEMA_HASHES.items()}
_PRODUCTION_POLICY={"authority_model":"SCI_ED_002_COMPLETE_AUTHORITY_V3","authority_contract_version":"3.0.0","producer_repository":"https://github.com/trbrewer/puckworks.git","commit":"e22a422d7c9cac5cd6d0779d5f5455bf492a018e","tree":"33c9d603760163842caa86aa932053ca44b120f8","export":{"path":"docs/analysis/sci_ed_002/SCI_ED_002_EXPORT.json","sha256":"18716c638a1837a8719a55b579e45514b217b686e9a6960ef8cc8379e7bc0d34"},"manifests":{"scientific_package":{"role":"SCIENTIFIC_PACKAGE_SOURCE_MANIFEST","path":"docs/analysis/sci_ed_002/SOURCE_MANIFEST.json","sha256":"bfcc32b28b7a5662778b1bdb25d03b735f637961e92654658e1de4de8699f146","member_commit":"2b8c3937bf05c4c0cc00b1bbe532845532a48e1e","member_tree":"b9c84f73bbc1057d63edccb0018a6a7b04d7d4ea","count":77},"r1_evidence":{"role":"R1_EVIDENCE_MANIFEST","path":"docs/analysis/sci_ed_002/r1/SOURCE_MANIFEST.json","sha256":"f7dd8f312079a7579a5698b788a7dab52ac359979ebd2281747e7c5fa51169b8","member_commit":"e22a422d7c9cac5cd6d0779d5f5455bf492a018e","member_tree":"33c9d603760163842caa86aa932053ca44b120f8","count":17}},"schemas":schema_policy(),"schema_version":"1.0.0","sci_md_007":{"commit":"31741303fb604ed3e6586a555ea6ef6989c24a62","tree":"a918072d28f555bf98638fa97da1adb568bf09b8","export_path":"docs/analysis/sci_md_007/SCI_MD_007_EXPORT.json","disposition":MD7_DISPOSITION},"claims":{"commissioning_authorized":False,"predictor_eligible":False,"c_s0_mapping_status":"NOT_ESTABLISHED","holdout_status":"SEALED_NOT_ACCESSED","governing_physics_change":False},"disposition":DISPOSITION,"history":{"r0_design_candidate":{"commit":"2b8c3937bf05c4c0cc00b1bbe532845532a48e1e","tree":"b9c84f73bbc1057d63edccb0018a6a7b04d7d4ea"},"r0_export_publication":{"commit":"cc096ac8a520a3d68f86fdd27f7dc9fb79307e6b","tree":"e7f684ded6c415ec4935563a33fbd2346ca891fe"},"r1_scientific_content":{"commit":"4b0cc9a8110560dc7e771f538ab5dbcdfa868117","tree":"048975883ebf14a3fae6d71aac80fa1508c2809e"}}}

class HandoffError(ValueError):
 def __init__(self,reason,stage,field,expected=None,observed=None,expected_source="immutable-policy",observed_source="authority-lock",detail=None):
  self.detail={"reason":reason,"reason_code":reason,"stage":stage,"field":field,"expected":expected,"observed":observed,"expected_source":expected_source,"observed_source":observed_source}
  if detail is not None:self.detail["detail"]=detail
  super().__init__(json.dumps(self.detail,sort_keys=True))
def fail(reason,stage,field,expected=None,observed=None,**kw): raise HandoffError(reason,stage,field,expected,observed,**kw)
def equal(observed,expected,reason,stage,field,expected_source="immutable-policy",observed_source="authority-lock"):
 if observed!=expected: fail(reason,stage,field,expected,observed,expected_source=expected_source,observed_source=observed_source)
def sha(b): return hashlib.sha256(b).hexdigest()
def valid_path(v,field):
 if not isinstance(v,str) or not v or v.startswith("/") or ".." in Path(v).parts or "\\" in v: fail("AUTHORITY_PATH_INVALID","structure",field,"relative Git path",v)
 return v
def require_obj(v,field):
 if not isinstance(v,dict): fail("AUTHORITY_FIELD_TYPE_INVALID","structure",field,"object",type(v).__name__)
 return v
def keys(obj,expected,field):
 actual=set(obj); expected=set(expected)
 if actual-expected: fail("AUTHORITY_UNKNOWN_FIELD","structure",field,sorted(expected),sorted(actual-expected))
 if expected-actual: fail("AUTHORITY_REQUIRED_FIELD_MISSING","structure",field,sorted(expected),sorted(expected-actual))
def string(v,field):
 if not isinstance(v,str): fail("AUTHORITY_FIELD_TYPE_INVALID","structure",field,"string",type(v).__name__)
 return v
def boolean(v,field):
 if type(v) is not bool: fail("AUTHORITY_FIELD_TYPE_INVALID","structure",field,"boolean",type(v).__name__)
 return v
def gitid(v,field):
 string(v,field)
 if not HEX40.fullmatch(v): fail("AUTHORITY_GIT_ID_FORMAT_INVALID","structure",field,"40 lowercase hex",v)
 return v
def hashid(v,field):
 string(v,field)
 if not HEX64.fullmatch(v): fail("AUTHORITY_HASH_FORMAT_INVALID","structure",field,"64 lowercase hex",v)
 return v

def authority_leaf_inventory(lock):
 out=[]
 def walk(value,pointer):
  if isinstance(value,dict):
   for key in sorted(value): walk(value[key],pointer+"/"+key.replace("~","~0").replace("/","~1"))
  else:
   if pointer.startswith("/historical_provenance/") or pointer=="/retired_authorities/schema_aggregate/historical_sha256": classification="HISTORICAL_PROVENANCE"
   elif pointer.startswith("/retired_authorities/") or pointer.startswith("/contract_metadata/"): classification="DERIVED_INFORMATIONAL"
   else: classification="ADJUDICATIVE_CURRENT_AUTHORITY"
   out.append({"json_pointer":pointer,"classification":classification,"value_type":type(value).__name__})
 walk(lock,"")
 if not out: fail("AUTHORITY_FIELD_CLASSIFICATION_INCOMPLETE","classification","/","classified leaves",0)
 return out

def validate_lock(lock):
 require_obj(lock,"/"); keys(lock,{"authority_model","authority_contract_version","producer_repository","current_authority","historical_provenance","retired_authorities","contract_metadata"},"/")
 ca=require_obj(lock["current_authority"],"/current_authority"); keys(ca,{"producer_commit","producer_tree","export","producer_manifests","schemas","producer_schema_package_version","scientific_protocol_disposition","sci_md_007_authority","claim_ceiling"},"/current_authority")
 equal(string(lock["authority_model"],"/authority_model"),_PRODUCTION_POLICY["authority_model"],"AUTHORITY_MODEL_MISMATCH","structure","/authority_model")
 equal(string(lock["authority_contract_version"],"/authority_contract_version"),_PRODUCTION_POLICY["authority_contract_version"],"AUTHORITY_CONTRACT_VERSION_UNSUPPORTED","structure","/authority_contract_version")
 equal(string(lock["producer_repository"],"/producer_repository"),_PRODUCTION_POLICY["producer_repository"],"PRODUCER_REPOSITORY_IDENTITY_MISMATCH","policy","/producer_repository")
 gitid(ca["producer_commit"],"/current_authority/producer_commit"); gitid(ca["producer_tree"],"/current_authority/producer_tree")
 ex=require_obj(ca["export"],"/current_authority/export"); keys(ex,{"path","sha256"},"/current_authority/export"); valid_path(ex["path"],"/current_authority/export/path"); hashid(ex["sha256"],"/current_authority/export/sha256")
 mans=require_obj(ca["producer_manifests"],"/current_authority/producer_manifests"); keys(mans,{"scientific_package","r1_evidence"},"/current_authority/producer_manifests")
 for role,m in mans.items():
  require_obj(m,f"/current_authority/producer_manifests/{role}"); keys(m,{"role","path","sha256","member_authority_commit","member_authority_tree","expected_member_count"},f"/current_authority/producer_manifests/{role}"); valid_path(m["path"],role+"/path"); hashid(m["sha256"],role+"/sha256"); gitid(m["member_authority_commit"],role+"/member_authority_commit"); gitid(m["member_authority_tree"],role+"/member_authority_tree")
  if type(m["expected_member_count"]) is not int: fail("AUTHORITY_FIELD_TYPE_INVALID","structure",role+"/expected_member_count","integer",type(m["expected_member_count"]).__name__)
 schemas=require_obj(ca["schemas"],"/current_authority/schemas"); equal(set(schemas),set(SCHEMA_HASHES),"SCHEMA_SET_INCOMPLETE","structure","/current_authority/schemas")
 for name,s in schemas.items(): require_obj(s,"schemas/"+name); keys(s,{"path","sha256"},"schemas/"+name); valid_path(s["path"],name+"/path"); hashid(s["sha256"],name+"/sha256")
 string(ca["producer_schema_package_version"],"/current_authority/producer_schema_package_version"); string(ca["scientific_protocol_disposition"],"/current_authority/scientific_protocol_disposition")
 md=require_obj(ca["sci_md_007_authority"],"/current_authority/sci_md_007_authority"); keys(md,{"commit","tree","export_path","disposition"},"/current_authority/sci_md_007_authority"); gitid(md["commit"],"md7/commit"); gitid(md["tree"],"md7/tree"); valid_path(md["export_path"],"md7/export_path"); string(md["disposition"],"md7/disposition")
 claims=require_obj(ca["claim_ceiling"],"/current_authority/claim_ceiling"); keys(claims,{"commissioning_authorized","predictor_eligible","c_s0_mapping_status","holdout_status","governing_physics_change"},"/current_authority/claim_ceiling"); boolean(claims["commissioning_authorized"],"commissioning_authorized"); boolean(claims["predictor_eligible"],"predictor_eligible"); string(claims["c_s0_mapping_status"],"c_s0_mapping_status"); string(claims["holdout_status"],"holdout_status"); boolean(claims["governing_physics_change"],"governing_physics_change")
 hist=require_obj(lock["historical_provenance"],"/historical_provenance"); keys(hist,set(_PRODUCTION_POLICY["history"]),"/historical_provenance")
 for role,a in hist.items(): require_obj(a,"history/"+role); keys(a,{"commit","tree"},"history/"+role); gitid(a["commit"],role+"/commit"); gitid(a["tree"],role+"/tree")
 retired=require_obj(lock["retired_authorities"],"/retired_authorities"); keys(retired,{"schema_aggregate"},"/retired_authorities"); agg=require_obj(retired["schema_aggregate"],"schema_aggregate"); keys(agg,{"status","historical_sha256","part_of_current_pass"},"schema_aggregate"); hashid(agg["historical_sha256"],"historical_sha256"); boolean(agg["part_of_current_pass"],"part_of_current_pass")
 meta=require_obj(lock["contract_metadata"],"/contract_metadata"); keys(meta,{"closed_fields","deprecated_manifest_aliases_absent","exact_head_binding"},"/contract_metadata"); boolean(meta["closed_fields"],"closed_fields"); boolean(meta["deprecated_manifest_aliases_absent"],"deprecated_manifest_aliases_absent")
 return lock

def load_package(root):
 p=Path(root)/REL/"PUCKWORKS_AUTHORITY.json"
 try: raw=p.read_bytes()
 except OSError as e: fail("AUTHORITY_STRUCTURE_INVALID","load","authority_lock","readable file",e.__class__.__name__)
 try: lock=json.loads(raw)
 except (json.JSONDecodeError,UnicodeDecodeError) as e: fail("AUTHORITY_JSON_INVALID","load","authority_lock","valid UTF-8 JSON",e.__class__.__name__)
 if not isinstance(lock,dict): fail("AUTHORITY_ROOT_TYPE_INVALID","structure","/","object",type(lock).__name__)
 validate_lock(lock)
 ep=Path(root)/REL/"SCI_ED_002_EXPORT.json"
 try: data=ep.read_bytes(); export=json.loads(data)
 except (OSError,json.JSONDecodeError,UnicodeDecodeError) as e: fail("VENDORED_EXPORT_INVALID","load","vendored_export","valid JSON",e.__class__.__name__)
 if not isinstance(export,dict): fail("VENDORED_EXPORT_INVALID","structure","vendored_export","object",type(export).__name__)
 return lock,export,data

def policy_checks(lock,export,policy):
 ca=lock["current_authority"]
 equal(ca["producer_commit"],policy["commit"],"PRODUCER_COMMIT_POLICY_MISMATCH","policy","producer_commit")
 equal(ca["producer_tree"],policy["tree"],"PRODUCER_TREE_POLICY_MISMATCH","policy","producer_tree")
 equal(ca["export"]["path"],policy["export"]["path"],"PRODUCER_EXPORT_PATH_POLICY_MISMATCH","policy","export.path")
 equal(ca["export"]["sha256"],policy["export"]["sha256"],"PRODUCER_EXPORT_HASH_MISMATCH","policy","export.sha256")
 equal(ca["producer_schema_package_version"],policy["schema_version"],"SCHEMA_VERSION_SEMANTICS_UNRESOLVED","policy","producer_schema_package_version")
 equal(ca["scientific_protocol_disposition"],policy["disposition"],"CLAIM_CEILING_POLICY_MISMATCH","policy","scientific_protocol_disposition")
 for role,p in policy["manifests"].items():
  m=ca["producer_manifests"][role]
  for lk,pk,reason in (("role","role","PRODUCER_MANIFEST_ROLE_SWAPPED"),("path","path","PRODUCER_MANIFEST_PATH_POLICY_MISMATCH"),("sha256","sha256","PRODUCER_MANIFEST_HASH_MISMATCH"),("member_authority_commit","member_commit","PRODUCER_MANIFEST_MEMBER_AUTHORITY_MISMATCH"),("member_authority_tree","member_tree","PRODUCER_MANIFEST_MEMBER_AUTHORITY_MISMATCH"),("expected_member_count","count","DERIVED_AUTHORITY_VALUE_MISMATCH")): equal(m[lk],p[pk],reason,"policy",f"manifests.{role}.{lk}")
 for name,p in policy["schemas"].items():
  equal(ca["schemas"][name]["path"],p["path"],"SCHEMA_PATH_POLICY_MISMATCH","policy",name+".path"); equal(ca["schemas"][name]["sha256"],p["sha256"],"SCHEMA_HASH_MISMATCH","policy",name+".sha256")
 equal(ca["sci_md_007_authority"],policy["sci_md_007"],"SCI_MD_007_AUTHORITY_MISMATCH","policy","sci_md_007_authority")
 equal(lock["historical_provenance"],policy["history"],"HISTORICAL_PROVENANCE_AUTHORITY_MISMATCH","historical-provenance","historical_provenance")
 equal(lock["retired_authorities"]["schema_aggregate"]["status"],RETIRED_AGGREGATE,"DERIVED_AUTHORITY_VALUE_MISMATCH","derived","schema_aggregate.status")
 equal(lock["retired_authorities"]["schema_aggregate"]["part_of_current_pass"],False,"DERIVED_AUTHORITY_VALUE_MISMATCH","derived","schema_aggregate.part_of_current_pass")
 ce=export.get("claim_ceiling");
 if not isinstance(ce,dict): fail("VENDORED_EXPORT_INVALID","claim-conjunction","claim_ceiling","object",type(ce).__name__)
 pairs={"commissioning_authorized":ce.get("commissioning_authorized"),"predictor_eligible":ce.get("predictor_eligible"),"c_s0_mapping_status":ce.get("c_s0_mapping_status"),"holdout_status":export.get("holdout_status"),"governing_physics_change":ce.get("governing_physics_change")}
 out={}
 for field,observed in pairs.items():
  expected=ca["claim_ceiling"][field]; equal(observed,expected,"CLAIM_CEILING_LOCK_EXPORT_MISMATCH","claim-conjunction",field,expected_source="authority-lock",observed_source="vendored-export"); equal(expected,policy["claims"][field],"CLAIM_CEILING_POLICY_MISMATCH","claim-policy",field); out[field]={"lock":expected,"export":observed,"policy":policy["claims"][field],"status":"PASS"}
 for field,observed in (("disposition",export.get("disposition")),("claim_ceiling.disposition",ce.get("disposition"))): equal(observed,ca["scientific_protocol_disposition"],"CLAIM_CEILING_LOCK_EXPORT_MISMATCH","claim-conjunction",field,expected_source="authority-lock",observed_source="vendored-export")
 equal(export.get("source_manifest_sha256"),ca["producer_manifests"]["scientific_package"]["sha256"],"EXPORT_SCIENTIFIC_MANIFEST_PIN_MISMATCH","manifest-conjunction","source_manifest_sha256")
 equal(
  export.get("schema_sha256"),
  {name: schema["sha256"] for name, schema in policy["schemas"].items()},
  "SCHEMA_PIN_POLICY_MISMATCH",
  "schema-conjunction",
  "schema_sha256",
 )
 equal(export.get("sci_md_007_authority"),{"commit":policy["sci_md_007"]["commit"],"tree":policy["sci_md_007"]["tree"]},"SCI_MD_007_AUTHORITY_MISMATCH","sci-md-007","export.sci_md_007_authority")
 return out

def ancestor(repo,a,b):
 cp=subprocess.run(["git","-C",str(repo),"merge-base","--is-ancestor",a,b],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 if cp.returncode: fail("HISTORICAL_AUTHORITY_NOT_ANCESTOR","historical-provenance",a,b,a,expected_source="final-producer",observed_source="historical-authority")
def verify_manifest(repo,final_authority,role,m):
 try:data=object_bytes(repo,final_authority,m["path"])
 except AuthorityError: fail("PRODUCER_MANIFEST_MEMBER_MISSING","producer-manifest",m["path"],"Git blob","missing",observed_source="producer-object")
 equal(sha(data),m["sha256"],"PRODUCER_MANIFEST_HASH_MISMATCH","producer-manifest",role,observed_source="producer-object")
 try:doc=json.loads(data)
 except (json.JSONDecodeError,UnicodeDecodeError): fail("PRODUCER_MANIFEST_STRUCTURE_INVALID","producer-manifest",role,"valid JSON manifest","invalid")
 files=doc.get("files");
 if not isinstance(files,list): fail("PRODUCER_MANIFEST_STRUCTURE_INVALID","producer-manifest",role,"files array",type(files).__name__)
 equal(len(files),m["expected_member_count"],"DERIVED_AUTHORITY_VALUE_MISMATCH","derived",role+".member_count")
 ma=GitAuthority(m["member_authority_commit"],m["member_authority_tree"])
 try:verify_authority(repo,ma)
 except AuthorityError as e: fail(str(e),"producer-manifest-member-authority",role,{"commit":ma.commit,"tree":ma.tree},None)
 seen=set()
 for i,item in enumerate(files):
  if not isinstance(item,dict) or set(item)!={"path","sha256"}: fail("PRODUCER_MANIFEST_STRUCTURE_INVALID","producer-manifest",f"{role}/{i}","path+sha256 object",item)
  p=valid_path(item["path"],f"{role}/{i}/path"); hashid(item["sha256"],f"{role}/{i}/sha256")
  if p in seen: fail("AUTHORITY_DUPLICATE_LOGICAL_ID","producer-manifest",p,"unique path",p)
  seen.add(p)
  try:b=object_bytes(repo,ma,str(Path(m["path"]).parent/p))
  except AuthorityError: fail("PRODUCER_MANIFEST_MEMBER_MISSING","producer-manifest-member",p,"Git blob","missing",observed_source="producer-object")
  equal(sha(b),item["sha256"],"PRODUCER_MANIFEST_MEMBER_HASH_MISMATCH","producer-manifest-member",p,observed_source="producer-object")
 if role=="scientific_package":
  missing=CORE-seen
  if missing: fail("SCIENTIFIC_PACKAGE_CORE_MEMBER_MISSING","producer-manifest",role,sorted(CORE),sorted(missing))
  sm={f"schemas/1.0.0/{n}.schema.json" for n in SCHEMA_HASHES}
  if not sm.issubset(seen): fail("SCHEMA_MANIFEST_MEMBERSHIP_MISSING","producer-manifest",role,sorted(sm),sorted(sm-seen))
 return {"status":"PASS","path":m["path"],"sha256":m["sha256"],"member_count":len(files),"member_authority":{"commit":ma.commit,"tree":ma.tree},"members_verified":True}

def exact_checks(lock,export,vbytes,repo,policy):
 ca=lock["current_authority"]; final=GitAuthority(ca["producer_commit"],ca["producer_tree"])
 try:verify_authority(repo,final)
 except AuthorityError as e: fail(str(e),"producer-object","producer_commit_tree",{"commit":final.commit,"tree":final.tree},None,observed_source="producer-object")
 try:pbytes=object_bytes(repo,final,ca["export"]["path"])
 except AuthorityError: fail("PRODUCER_EXPORT_MISSING","producer-export",ca["export"]["path"],"Git blob","missing",observed_source="producer-object")
 equal(sha(pbytes),ca["export"]["sha256"],"PRODUCER_EXPORT_HASH_MISMATCH","producer-export","export.sha256",observed_source="producer-object"); equal(pbytes,vbytes,"PRODUCER_EXPORT_BYTES_MISMATCH","producer-export","export.bytes",observed_source="producer-object")
 manifests={r:verify_manifest(repo,final,r,m) for r,m in ca["producer_manifests"].items()}
 for n,s in ca["schemas"].items():
  try:b=object_bytes(repo,final,s["path"])
  except AuthorityError: fail("SCHEMA_SET_INCOMPLETE","producer-schema",n,"Git blob","missing",observed_source="producer-object")
  equal(sha(b),s["sha256"],"SCHEMA_HASH_MISMATCH","producer-schema",n,observed_source="producer-object")
 history={}
 for role,a in lock["historical_provenance"].items():
  try:verify_authority(repo,GitAuthority(a["commit"],a["tree"]))
  except AuthorityError as e: fail(str(e),"historical-provenance",role,a,None,observed_source="producer-object")
  ancestor(repo,a["commit"],final.commit); history[role]={"status":"PASS","used_for_current_selection":False,**a}
 equal(history["r0_design_candidate"]["commit"],ca["producer_manifests"]["scientific_package"]["member_authority_commit"],"SCIENTIFIC_PACKAGE_MEMBER_AUTHORITY_MISMATCH","historical-provenance","r0_design_candidate")
 md=ca["sci_md_007_authority"]; mda=GitAuthority(md["commit"],md["tree"])
 try:verify_authority(repo,mda); mdbytes=object_bytes(repo,mda,md["export_path"]); mddoc=json.loads(mdbytes)
 except AuthorityError as e: fail(str(e),"sci-md-007","authority",md,None,observed_source="producer-object")
 equal(mddoc.get("scientific_disposition"),md["disposition"],"SCI_MD_007_DISPOSITION_MISMATCH","sci-md-007","scientific_disposition",observed_source="producer-object")
 return {"current_authority_verified":True,"historical_provenance_verified":True,"historical_provenance_used_for_current_selection":False,"producer_commit_verified":True,"producer_tree_verified":True,"producer_export_verified":True,"producer_manifests":manifests,"producer_manifests_verified":True,"producer_schema_set_verified":True,"producer_schemas_status":"VERIFIED_20_OF_20","sci_md_007_authority_verified":True,"historical_provenance":history}

def decide(root=ROOT,mode="exact-producer",producer_root=None,policy=None):
 policy=policy or _PRODUCTION_POLICY; lock,export,vbytes=load_package(root); inventory=authority_leaf_inventory(lock); claims=policy_checks(lock,export,policy)
 equal(sha(vbytes),lock["current_authority"]["export"]["sha256"],"VENDORED_EXPORT_HASH_MISMATCH","vendored-package","export.sha256",expected_source="authority-lock",observed_source="vendored-export")
 counts={name:sum(item["classification"]==name for item in inventory) for name in ("ADJUDICATIVE_CURRENT_AUTHORITY","DERIVED_INFORMATIONAL","HISTORICAL_PROVENANCE","DEPRECATED_DUPLICATE")}
 common={"schema_version":"ewp.sci_ed_002.handoff_verification.v4","verification_mode":mode,"authority_contract_valid":True,"authority_field_classification_complete":True,"authority_field_count":len(inventory),"authority_classification_counts":counts,"all_current_adjudicative_fields_verified":True,"derived_values_recomputed":True,"deprecated_duplicates_absent":True,"vendored_contract_verified":True,"claim_ceiling_conjunction":claims,"claim_ceiling_verified":True,"no_physics_evaluation":"NOT_PART_OF_HANDOFF_VERIFIER","schema_aggregate":{"status":RETIRED_AGGREGATE,"verified":False}}
 if mode=="vendored-only": return {**common,"status":VENDORED_STATUS,"full_handoff_verified":False,"producer_object_status":"NOT_CHECKED","producer_commit_verified":False,"producer_tree_verified":False,"producer_manifests":{"scientific_package":{"status":"NOT_CHECKED"},"r1_evidence":{"status":"NOT_CHECKED"}},"producer_schemas_status":"NOT_CHECKED","sci_md_007_object_status":"NOT_CHECKED","historical_provenance_object_status":"NOT_CHECKED"}
 if mode!="exact-producer": fail("VERIFICATION_MODE_INVALID","cli","mode","exact-producer|vendored-only",mode)
 if producer_root is None:
  alias=os.environ.get("PUCKWORKS_GIT_REPOSITORY")
  if not alias: fail("EXACT_PRODUCER_ROOT_REQUIRED","cli","producer_root","explicit Git repository",None)
  producer_root=Path(alias); mechanism="deprecated-environment-alias"
 else: mechanism="explicit-cli"
 try:repo=require_repository(Path(producer_root))
 except AuthorityError as e: fail(str(e),"producer-object","producer_root","Git repository",None)
 exact=exact_checks(lock,export,vbytes,repo,policy)
 return {**common,**exact,"status":EXACT_STATUS,"full_handoff_verified":True,"producer_object_status":"EXACT_OBJECT_VERIFIED","producer_root_mechanism":mechanism,"producer_commit":policy["commit"],"producer_tree":policy["tree"]}
verify=decide

def atomic_write(path,payload):
 path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile("w",dir=path.parent,prefix=path.name+".",delete=False,encoding="utf-8") as f: json.dump(payload,f,indent=2,sort_keys=True); f.write("\n"); temp=Path(f.name)
 os.replace(temp,path)
def parser():
 p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=ROOT); p.add_argument("--mode",choices=("exact-producer","vendored-only"),default="exact-producer"); p.add_argument("--producer-root",type=Path); p.add_argument("--output",type=Path); return p
def main(argv=None):
 try:a=parser().parse_args(argv)
 except SystemExit: raise
 if a.output and a.output.exists(): a.output.unlink()
 try:result=decide(a.root,a.mode,a.producer_root); code=0
 except HandoffError as e: result={"schema_version":"ewp.sci_ed_002.handoff_verification.v4","status":"FAIL","full_handoff_verified":False,"verification_mode":a.mode,"stage":e.detail["stage"],"reason_code":e.detail["reason_code"],"failure":e.detail}; code=1
 except (AuthorityError,subprocess.SubprocessError,OSError,UnicodeError,json.JSONDecodeError,TypeError,ValueError) as e: result={"schema_version":"ewp.sci_ed_002.handoff_verification.v4","status":"FAIL","full_handoff_verified":False,"verification_mode":a.mode,"stage":"internal-error","reason_code":"UNEXPECTED_VERIFIER_INTERNAL_ERROR","failure":{"reason_code":"UNEXPECTED_VERIFIER_INTERNAL_ERROR","stage":"internal-error","field":"internal","expected":"controlled verification","observed":e.__class__.__name__,"expected_source":"verifier-contract","observed_source":"internal"}}; code=1
 if a.output: atomic_write(a.output,result)
 print(json.dumps(result,indent=2,sort_keys=True)); return code
if __name__=="__main__": raise SystemExit(main())
