import copy,hashlib,json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import scripts.verify_sci_ed_002_handoff as h
ROOT=Path(__file__).parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(o,sort_keys=True,separators=(",",":"))+"\n").encode())
def mutate(root,file,path,value):
 p=Path(root)/h.REL/file;o=json.loads(p.read_text());q=o
 for k in path[:-1]:q=q[k]
 q[path[-1]]=value;put(p,o)
def delete(root,file,path):
 p=Path(root)/h.REL/file;o=json.loads(p.read_text());q=o
 for k in path[:-1]:q=q[k]
 del q[path[-1]];put(p,o)
class Fixture:
 def __init__(self,base):
  self.base=Path(base);self.repo=self.base/"producer";self.ewp=self.base/"ewp";subprocess.run(["git","init","-q",str(self.repo)],check=True)
  subprocess.run(["git","-C",str(self.repo),"config","user.email","test@example.invalid"],check=True);subprocess.run(["git","-C",str(self.repo),"config","user.name","Test"],check=True)
  root=self.repo/"docs/analysis/sci_ed_002";(root/"schemas/1.0.0").mkdir(parents=True);schemas={}
  for name in h.SCHEMA_HASHES:
   b=(json.dumps({"$id":name,"type":"object"},sort_keys=True)+"\n").encode();p=root/f"schemas/1.0.0/{name}.schema.json";p.write_bytes(b);schemas[name]={"path":p.relative_to(self.repo).as_posix(),"sha256":sha(b)}
  for name in h.CORE:(root/name).parent.mkdir(parents=True,exist_ok=True);(root/name).write_text(name+"\n")
  members=[]
  for p in sorted(h.CORE|{f"schemas/1.0.0/{n}.schema.json" for n in schemas}):members.append({"path":p,"sha256":sha((root/p).read_bytes())})
  put(root/"SOURCE_MANIFEST.json",{"schema_version":"test/v1","files":members});r1=root/"r1";r1.mkdir();(r1/"AUTHORIZATION.md").write_text("test\n");put(r1/"SOURCE_MANIFEST.json",{"schema_version":"test/v1","files":[{"path":"AUTHORIZATION.md","sha256":sha((r1/"AUTHORIZATION.md").read_bytes())}]})
  md=root.parent/"sci_md_007";md.mkdir();put(md/"SCI_MD_007_EXPORT.json",{"scientific_disposition":h.MD7_DISPOSITION})
  subprocess.run(["git","-C",str(self.repo),"add",md.relative_to(self.repo).as_posix()],check=True);mdtree=subprocess.check_output(["git","-C",str(self.repo),"write-tree"],text=True).strip();mdcommit=subprocess.check_output(["git","-C",str(self.repo),"commit-tree",mdtree,"-m","MD7"],text=True).strip()
  export={"claim_ceiling":{"commissioning_authorized":False,"predictor_eligible":False,"c_s0_mapping_status":"NOT_ESTABLISHED","governing_physics_change":False,"disposition":h.DISPOSITION},"holdout_status":"SEALED_NOT_ACCESSED","disposition":h.DISPOSITION,"schema_sha256":{n:v["sha256"] for n,v in schemas.items()},"source_manifest_sha256":sha((root/"SOURCE_MANIFEST.json").read_bytes()),"sci_md_007_authority":{"commit":mdcommit,"tree":mdtree}};put(root/"SCI_ED_002_EXPORT.json",export)
  subprocess.run(["git","-C",str(self.repo),"add","."],check=True);subprocess.run(["git","-C",str(self.repo),"commit","-q","-m","tree"],check=True);self.tree=subprocess.check_output(["git","-C",str(self.repo),"rev-parse","HEAD^{tree}"],text=True).strip();self.a=subprocess.check_output(["git","-C",str(self.repo),"commit-tree",self.tree,"-m","A"],text=True).strip();self.b=subprocess.check_output(["git","-C",str(self.repo),"commit-tree",self.tree,"-m","B"],text=True).strip()
  mans={"scientific_package":{"role":"SCIENTIFIC_PACKAGE_SOURCE_MANIFEST","path":"docs/analysis/sci_ed_002/SOURCE_MANIFEST.json","sha256":sha((root/"SOURCE_MANIFEST.json").read_bytes()),"member_commit":self.a,"member_tree":self.tree,"count":len(members)},"r1_evidence":{"role":"R1_EVIDENCE_MANIFEST","path":"docs/analysis/sci_ed_002/r1/SOURCE_MANIFEST.json","sha256":sha((r1/"SOURCE_MANIFEST.json").read_bytes()),"member_commit":self.a,"member_tree":self.tree,"count":1}}
  md7={"commit":mdcommit,"tree":mdtree,"export_path":"docs/analysis/sci_md_007/SCI_MD_007_EXPORT.json","disposition":h.MD7_DISPOSITION};history={x:{"commit":self.a,"tree":self.tree} for x in ("r0_design_candidate","r0_export_publication","r1_scientific_content")}
  self.policy={"authority_model":"SCI_ED_002_COMPLETE_AUTHORITY_V3","authority_contract_version":"3.0.0","producer_repository":"https://github.com/trbrewer/puckworks.git","commit":self.a,"tree":self.tree,"export":{"path":"docs/analysis/sci_ed_002/SCI_ED_002_EXPORT.json","sha256":sha((root/"SCI_ED_002_EXPORT.json").read_bytes())},"manifests":mans,"schemas":schemas,"schema_version":"1.0.0","sci_md_007":md7,"claims":{"commissioning_authorized":False,"predictor_eligible":False,"c_s0_mapping_status":"NOT_ESTABLISHED","holdout_status":"SEALED_NOT_ACCESSED","governing_physics_change":False},"disposition":h.DISPOSITION,"history":history}
  target=self.ewp/h.REL;target.mkdir(parents=True);(target/"SCI_ED_002_EXPORT.json").write_bytes((root/"SCI_ED_002_EXPORT.json").read_bytes())
  lock={"authority_model":self.policy["authority_model"],"authority_contract_version":"3.0.0","producer_repository":self.policy["producer_repository"],"current_authority":{"producer_commit":self.a,"producer_tree":self.tree,"export":self.policy["export"],"producer_manifests":{r:{"role":m["role"],"path":m["path"],"sha256":m["sha256"],"member_authority_commit":self.a,"member_authority_tree":self.tree,"expected_member_count":m["count"]} for r,m in mans.items()},"schemas":schemas,"producer_schema_package_version":"1.0.0","scientific_protocol_disposition":h.DISPOSITION,"sci_md_007_authority":md7,"claim_ceiling":self.policy["claims"]},"historical_provenance":history,"retired_authorities":{"schema_aggregate":{"status":h.RETIRED_AGGREGATE,"historical_sha256":"0"*64,"part_of_current_pass":False}},"contract_metadata":{"closed_fields":True,"deprecated_manifest_aliases_absent":True,"exact_head_binding":"EXTERNAL_CI_AND_FINAL_REVIEW_EVIDENCE"}};put(target/"PUCKWORKS_AUTHORITY.json",lock)
class HandoffTests(unittest.TestCase):
 def cli(self,f,mode="vendored-only",out=None,repo=None,policy=None):
  out=out or f.base/"out.json";args=["--root",str(f.ewp),"--mode",mode,"--output",str(out)];
  if repo:args += ["--producer-root",str(repo)]
  with patch.object(h,"_PRODUCTION_POLICY",policy or f.policy):code=h.main(args)
  return code,json.loads(out.read_text())
 def test_valid_complete_cli_and_same_tree_controls(self):
  with tempfile.TemporaryDirectory() as td:
   f=Fixture(td);code,r=self.cli(f,"exact-producer",repo=f.repo);self.assertEqual(code,0);self.assertEqual(r["status"],h.EXACT_STATUS);self.assertNotEqual(f.a,f.b)
   for field in ("producer_commit",):
    g=Fixture(Path(td)/field);mutate(g.ewp,"PUCKWORKS_AUTHORITY.json",["current_authority",field],g.b);out=Path(td)/(field+".json");put(out,{"status":h.EXACT_STATUS,"full_handoff_verified":True});code,r=self.cli(g,"exact-producer",out,g.repo);self.assertNotEqual(code,0);self.assertFalse(r["full_handoff_verified"]);self.assertEqual(r["reason_code"],"PRODUCER_COMMIT_POLICY_MISMATCH")
   g=Fixture(Path(td)/"policy");p=copy.deepcopy(g.policy);p["commit"]=g.b;code,r=self.cli(g,"exact-producer",repo=g.repo,policy=p);self.assertNotEqual(code,0);self.assertEqual(r["reason_code"],"PRODUCER_COMMIT_POLICY_MISMATCH")
   g=Fixture(Path(td)/"missing-a");mirror=Path(td)/"mirror";subprocess.run(["git","init","-q",str(mirror)],check=True);subprocess.run(["git","-C",str(mirror),"fetch","-q",str(g.repo),g.b],check=True);code,r=self.cli(g,"exact-producer",repo=mirror);self.assertNotEqual(code,0);self.assertEqual(r["reason_code"],"LOCKED_COMMIT_OBJECT_MISSING")
 def test_all_claim_mutation_classes_cli(self):
  cases=[("commissioning_authorized",["claim_ceiling","commissioning_authorized"],True),("predictor_eligible",["claim_ceiling","predictor_eligible"],True),("c_s0_mapping_status",["claim_ceiling","c_s0_mapping_status"],"ESTABLISHED"),("holdout_status",["holdout_status"],"UNSEALED"),("governing_physics_change",["claim_ceiling","governing_physics_change"],True)]
  for field,ep,bad in cases:
   for kind in ("lock-only","export-only","inconsistent-dual","joint-wrong"):
    with self.subTest(field=field,kind=kind),tempfile.TemporaryDirectory() as td:
     f=Fixture(td)
     if kind in ("lock-only","inconsistent-dual","joint-wrong"):mutate(f.ewp,"PUCKWORKS_AUTHORITY.json",["current_authority","claim_ceiling",field],bad)
     if kind in ("export-only","joint-wrong"):mutate(f.ewp,"SCI_ED_002_EXPORT.json",ep,bad)
     if kind=="inconsistent-dual":mutate(f.ewp,"SCI_ED_002_EXPORT.json",ep,"DIFFERENT" if isinstance(bad,str) else (not bad))
     code,r=self.cli(f);self.assertNotEqual(code,0);self.assertIn(r["reason_code"],{"CLAIM_CEILING_LOCK_EXPORT_MISMATCH","CLAIM_CEILING_POLICY_MISMATCH"})
 def test_current_authority_mutations_cli(self):
  cases=[(["authority_model"],"bad","AUTHORITY_MODEL_MISMATCH"),(["authority_contract_version"],"9.0.0","AUTHORITY_CONTRACT_VERSION_UNSUPPORTED"),(["producer_repository"],"https://invalid/other.git","PRODUCER_REPOSITORY_IDENTITY_MISMATCH"),(["current_authority","producer_tree"],"1"*40,"PRODUCER_TREE_POLICY_MISMATCH"),(["current_authority","export","path"],"../x","AUTHORITY_PATH_INVALID"),(["current_authority","export","sha256"],"1"*64,"PRODUCER_EXPORT_HASH_MISMATCH"),(["current_authority","producer_manifests","scientific_package","path"],"wrong.json","PRODUCER_MANIFEST_PATH_POLICY_MISMATCH"),(["current_authority","sci_md_007_authority","commit"],"1"*40,"SCI_MD_007_AUTHORITY_MISMATCH")]
  for path,value,reason in cases:
   with self.subTest(path=path),tempfile.TemporaryDirectory() as td:
    f=Fixture(td);mutate(f.ewp,"PUCKWORKS_AUTHORITY.json",path,value);code,r=self.cli(f);self.assertNotEqual(code,0);self.assertEqual(r["reason_code"],reason)
 def test_malformed_authorities_are_structured_and_atomic(self):
  mutations=[("invalid-json",lambda f:(f.ewp/h.REL/"PUCKWORKS_AUTHORITY.json").write_text("{"),"AUTHORITY_JSON_INVALID"),("root-list",lambda f:put(f.ewp/h.REL/"PUCKWORKS_AUTHORITY.json",[]),"AUTHORITY_ROOT_TYPE_INVALID"),("missing",lambda f:delete(f.ewp,"PUCKWORKS_AUTHORITY.json",["current_authority"]),"AUTHORITY_REQUIRED_FIELD_MISSING"),("wrong-type",lambda f:mutate(f.ewp,"PUCKWORKS_AUTHORITY.json",["current_authority","claim_ceiling"],[]),"AUTHORITY_FIELD_TYPE_INVALID"),("bad-hash",lambda f:mutate(f.ewp,"PUCKWORKS_AUTHORITY.json",["current_authority","export","sha256"],"bad"),"AUTHORITY_HASH_FORMAT_INVALID"),("bad-git",lambda f:mutate(f.ewp,"PUCKWORKS_AUTHORITY.json",["current_authority","producer_commit"],"bad"),"AUTHORITY_GIT_ID_FORMAT_INVALID"),("unknown",lambda f:mutate(f.ewp,"PUCKWORKS_AUTHORITY.json",["unexpected"],True),"AUTHORITY_UNKNOWN_FIELD")]
  for name,fn,reason in mutations:
   with self.subTest(name=name),tempfile.TemporaryDirectory() as td:
    f=Fixture(td);out=Path(td)/"result.json";put(out,{"status":h.EXACT_STATUS,"full_handoff_verified":True});fn(f);code,r=self.cli(f,out=out);self.assertNotEqual(code,0);self.assertEqual(r["reason_code"],reason);self.assertFalse(r["full_handoff_verified"]);self.assertIn("expected_source",r["failure"]);self.assertIn("observed_source",r["failure"])
 def test_deprecated_alias_and_unknown_field_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   f=Fixture(td);mutate(f.ewp,"PUCKWORKS_AUTHORITY.json",["producer_source_manifest_path"],"x");code,r=self.cli(f);self.assertEqual(r["reason_code"],"AUTHORITY_UNKNOWN_FIELD")
 def test_vendored_is_limited_and_missing_producer_fails(self):
  r=h.decide(mode="vendored-only");self.assertFalse(r["full_handoff_verified"]);self.assertEqual(r["sci_md_007_object_status"],"NOT_CHECKED")
  with patch.dict(os.environ,{},clear=True),self.assertRaisesRegex(h.HandoffError,"EXACT_PRODUCER_ROOT_REQUIRED"):h.decide()
 def test_cli_has_no_policy_overrides_and_r2c_history_unchanged(self):
  options={o for a in h.parser()._actions for o in a.option_strings};self.assertFalse(options&{"--expected-commit","--expected-tree","--expected-export-hash"});changed=subprocess.check_output(["git","-C",str(ROOT),"diff","--name-only","2d9b2b537545a67accd24d33d3c975e624b0fe93","--","docs/validation/sci_ed_002/r2c"],text=True).splitlines();self.assertEqual(changed,[])
 def test_public_control_mapping_and_authority_inventory_complete(self):
  evidence=ROOT/h.REL/"r2d";lock=json.loads((ROOT/h.REL/"PUCKWORKS_AUTHORITY.json").read_text());recorded=json.loads((evidence/"AUTHORITY_FIELD_INVENTORY.json").read_text())["fields"]
  self.assertEqual(recorded,h.authority_leaf_inventory(lock))
  matrix=json.loads((evidence/"NEGATIVE_CONTROL_MATRIX.json").read_text());workflow=(ROOT/".github/workflows/sci-ed-002-exact-producer.yml").read_text()
  self.assertIn("tests.test_sci_ed_002_handoff",workflow)
  for control in matrix["controls"]:
   node=control["test_node"].split(".")[-1];self.assertTrue(hasattr(HandoffTests,node),f"NEGATIVE_CONTROL_PUBLIC_TEST_MAPPING_INCOMPLETE: {node}")
if __name__=="__main__":unittest.main()
