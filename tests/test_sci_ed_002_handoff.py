import copy, hashlib, json, os, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import scripts.verify_sci_ed_002_handoff as h

ROOT=Path(__file__).parents[1]
def digest(b): return hashlib.sha256(b).hexdigest()
def put(p,o): p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes((json.dumps(o,sort_keys=True,separators=(",",":"))+"\n").encode())

class Fixture:
 def __init__(self,base):
  self.base=Path(base); self.repo=self.base/"producer"; self.ewp=self.base/"ewp"; subprocess.run(["git","init","-q",str(self.repo)],check=True)
  subprocess.run(["git","-C",str(self.repo),"config","user.email","test@example.invalid"],check=True); subprocess.run(["git","-C",str(self.repo),"config","user.name","Test"],check=True)
  root=self.repo/"docs/analysis/sci_ed_002"; (root/"schemas/1.0.0").mkdir(parents=True); schemas={}
  for name in h.SCHEMAS:
   data=(json.dumps({"$id":name,"type":"object"},sort_keys=True)+"\n").encode(); (root/f"schemas/1.0.0/{name}.schema.json").write_bytes(data); schemas[name]=digest(data)
  for name in h.CORE: (root/name).parent.mkdir(parents=True,exist_ok=True); (root/name).write_text(name+"\n")
  files=[]
  for p in sorted(h.CORE|{f"schemas/1.0.0/{n}.schema.json" for n in schemas}): files.append({"path":p,"sha256":digest((root/p).read_bytes())})
  put(root/"SOURCE_MANIFEST.json",{"schema_version":"test/v1","files":files}); r1=root/"r1"; r1.mkdir(); (r1/"AUTHORIZATION.md").write_text("test\n"); put(r1/"SOURCE_MANIFEST.json",{"schema_version":"test-r1/v1","files":[{"path":"AUTHORIZATION.md","sha256":digest((r1/"AUTHORIZATION.md").read_bytes())}]})
  export={"claim_ceiling":{"commissioning_authorized":False,"predictor_eligible":False,"c_s0_mapping_status":"NOT_ESTABLISHED","governing_physics_change":False,"disposition":h.DISPOSITION},"holdout_status":"SEALED_NOT_ACCESSED","disposition":h.DISPOSITION,"schema_sha256":schemas,"source_manifest_sha256":digest((root/"SOURCE_MANIFEST.json").read_bytes())}; put(root/"SCI_ED_002_EXPORT.json",export)
  subprocess.run(["git","-C",str(self.repo),"add","."],check=True); subprocess.run(["git","-C",str(self.repo),"commit","-q","-m","tree"],check=True); self.tree=subprocess.check_output(["git","-C",str(self.repo),"rev-parse","HEAD^{tree}"],text=True).strip(); self.a=subprocess.check_output(["git","-C",str(self.repo),"commit-tree",self.tree,"-m","A"],text=True).strip(); self.b=subprocess.check_output(["git","-C",str(self.repo),"commit-tree",self.tree,"-m","B"],text=True).strip()
  manifests={"scientific_package":{"path":"docs/analysis/sci_ed_002/SOURCE_MANIFEST.json","sha256":digest((root/"SOURCE_MANIFEST.json").read_bytes()),"member_commit":self.a,"member_tree":self.tree},"r1_evidence":{"path":"docs/analysis/sci_ed_002/r1/SOURCE_MANIFEST.json","sha256":digest((r1/"SOURCE_MANIFEST.json").read_bytes()),"member_commit":self.a,"member_tree":self.tree}}
  self.policy={"repository":"synthetic","commit":self.a,"tree":self.tree,"export_path":"docs/analysis/sci_ed_002/SCI_ED_002_EXPORT.json","export_sha256":digest((root/"SCI_ED_002_EXPORT.json").read_bytes()),"manifests":manifests,"schemas":schemas,"schema_aggregate_policy":h.RETIRED_AGGREGATE,"disposition":h.DISPOSITION,"claims":{"no_commissioning":True,"predictor_eligible":False,"c_s0_mapping_status":"NOT_ESTABLISHED","holdout_status":"SEALED_NOT_ACCESSED","governing_physics_change":False}}
  target=self.ewp/h.REL; target.mkdir(parents=True); (target/"SCI_ED_002_EXPORT.json").write_bytes((root/"SCI_ED_002_EXPORT.json").read_bytes()); lock={"producer_commit":self.a,"producer_tree":self.tree,"producer_export_sha256":self.policy["export_sha256"],"producer_disposition":h.DISPOSITION,"no_commissioning":True,"predictor_eligible":False,"c_s0_mapping_status":"NOT_ESTABLISHED","holdout_status":"SEALED_NOT_ACCESSED","governing_physics_change":False,"schema_aggregate_policy":h.RETIRED_AGGREGATE,"producer_manifests":{r:{"path":p["path"],"sha256":p["sha256"],"member_authority_commit":self.a,"member_authority_tree":self.tree} for r,p in manifests.items()}}; put(target/"PUCKWORKS_AUTHORITY.json",lock)
 def mutate(self,name,path,value):
  p=self.ewp/h.REL/name; o=json.loads(p.read_text()); q=o
  for k in path[:-1]: q=q[k]
  q[path[-1]]=value; put(p,o)

class SciEd002Handoff(unittest.TestCase):
 def test_vendored_limited_and_missing_exact(self):
  r=h.verify(mode="vendored-only"); self.assertEqual(r["status"],h.VENDORED_STATUS); self.assertFalse(r["full_handoff_verified"]); self.assertEqual(r["no_physics_evaluation"],"NOT_PART_OF_HANDOFF_VERIFIER")
  with patch.dict(os.environ,{},clear=True),self.assertRaisesRegex(h.HandoffError,"EXACT_PRODUCER_ROOT_REQUIRED"): h.verify()
 def test_complete_cli_same_tree_and_atomicity(self):
  with tempfile.TemporaryDirectory() as td:
   f=Fixture(td); self.assertNotEqual(f.a,f.b); self.assertEqual(f.tree,subprocess.check_output(["git","-C",str(f.repo),"rev-parse",f.b+"^{tree}"],text=True).strip()); out=Path(td)/"ok.json"
   with patch.object(h,"_PRODUCTION_POLICY",f.policy): self.assertEqual(h.main(["--root",str(f.ewp),"--mode","exact-producer","--producer-root",str(f.repo),"--output",str(out)]),0)
   self.assertEqual(json.loads(out.read_text())["status"],h.EXACT_STATUS)
   for name,kind,reason in (("lock","lock","PRODUCER_COMMIT_POLICY_MISMATCH"),("export","export","PRODUCER_COMMIT_MISMATCH_ACROSS_PINNED_AUTHORITIES")):
    g=Fixture(Path(td)/name); target=Path(td)/(name+".json"); target.write_text(json.dumps({"status":h.EXACT_STATUS,"full_handoff_verified":True})); g.mutate("PUCKWORKS_AUTHORITY.json" if kind=="lock" else "SCI_ED_002_EXPORT.json",["producer_commit"] if kind=="lock" else ["producer_package_commit"],g.b)
    with patch.object(h,"_PRODUCTION_POLICY",g.policy): self.assertNotEqual(h.main(["--root",str(g.ewp),"--mode","exact-producer","--producer-root",str(g.repo),"--output",str(target)]),0)
    result=json.loads(target.read_text()); self.assertFalse(result["full_handoff_verified"]); self.assertEqual(result["failure"]["reason"],reason)
 def test_policy_same_tree_substitution_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   f=Fixture(td); p=copy.deepcopy(f.policy); p["commit"]=f.b
   with self.assertRaisesRegex(h.HandoffError,"PRODUCER_COMMIT_POLICY_MISMATCH"): h.decide(f.ewp,"exact-producer",f.repo,p)
 def test_claim_conjunction_and_joint_policy(self):
  fields=[("no_commissioning",["claim_ceiling","commissioning_authorized"],False,True),("predictor_eligible",["claim_ceiling","predictor_eligible"],True,True),("c_s0_mapping_status",["claim_ceiling","c_s0_mapping_status"],"ESTABLISHED","ESTABLISHED"),("holdout_status",["holdout_status"],"UNSEALED","UNSEALED"),("governing_physics_change",["claim_ceiling","governing_physics_change"],True,True),("producer_disposition",["disposition"],"AUTHORIZED","AUTHORIZED")]
  for lf,ep,lv,ev in fields:
   with self.subTest(field=lf),tempfile.TemporaryDirectory() as td:
    f=Fixture(td); f.mutate("PUCKWORKS_AUTHORITY.json",[lf],lv)
    with self.assertRaisesRegex(h.HandoffError,"CLAIM_CEILING_LOCK_EXPORT_MISMATCH"): h.decide(f.ewp,"vendored-only",policy=f.policy)
   with self.subTest(field=lf+"-joint"),tempfile.TemporaryDirectory() as td:
    f=Fixture(td); f.mutate("PUCKWORKS_AUTHORITY.json",[lf],lv); f.mutate("SCI_ED_002_EXPORT.json",ep,ev)
    if lf=="producer_disposition": f.mutate("SCI_ED_002_EXPORT.json",["claim_ceiling","disposition"],ev)
    with self.assertRaisesRegex(h.HandoffError,"CLAIM_CEILING_POLICY_MISMATCH"): h.decide(f.ewp,"vendored-only",policy=f.policy)
 def test_no_cli_policy_override_and_history(self):
  options={o for a in h.parser()._actions for o in a.option_strings}; self.assertFalse(options&{"--expected-commit","--expected-tree","--expected-export-hash","--expected-manifest-hash"})
  changed=subprocess.check_output(["git","-C",str(ROOT),"diff","--name-only","98e3a2c3d41290edd1cf18fe38e3f9fc988a0850","--","docs/validation/sci_ed_002/r2b"],text=True).splitlines(); self.assertEqual(changed,[])

if __name__=="__main__": unittest.main()
