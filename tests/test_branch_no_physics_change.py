import json, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from tools.verify_branch_no_physics_change import verify

class BranchNoPhysics(unittest.TestCase):
 def repo(self):
  t=Path(tempfile.mkdtemp()); subprocess.run(["git","init","-q",t],check=True); subprocess.run(["git","-C",t,"config","user.email","t@example.invalid"],check=True); subprocess.run(["git","-C",t,"config","user.name","test"],check=True)
  for p,v in {"solver/a.C":"x","cases/c/d":"x","config/a":"x","scripts/espresso_reference_math.py":"x","Allrun":"x","docs/validation/sci_ed_002/a":"x"}.items(): (t/p).parent.mkdir(parents=True,exist_ok=True); (t/p).write_text(v)
  subprocess.run(["git","-C",t,"add","."],check=True); subprocess.run(["git","-C",t,"commit","-qm","base"],check=True); b=subprocess.check_output(["git","-C",t,"rev-parse","HEAD"],text=True).strip()
  rules={"schema_version":"1.0.0","protected_roots":["solver","cases","config","dependencies","validation","verification","provenance","scripts/lib"],"protected_files":["Allrun","Allverify","Allclean","Allwmake","scripts/espresso_reference_math.py"],"allowed_changed_paths":["docs/validation/sci_ed_002/a","rules.json"]}
  rp=t/"rules.json"; rp.write_text(json.dumps(rules)); return t,b,rp
 def commit(self,t,p,content=None,mode=None):
  q=t/p
  if content is None: q.unlink()
  else: q.parent.mkdir(parents=True,exist_ok=True); q.write_text(content)
  if mode: q.chmod(mode)
  subprocess.run(["git","-C",t,"add","-A"],check=True); subprocess.run(["git","-C",t,"commit","-qm","change"],check=True); return subprocess.check_output(["git","-C",t,"rev-parse","HEAD"],text=True).strip()
 def test_allowed(self):
  t,b,r=self.repo(); h=self.commit(t,"docs/validation/sci_ed_002/a","y"); self.assertEqual(verify(t,b,h,r)["status"],"PASS_NO_BRANCH_PHYSICS_CHANGE")
 def test_mutations(self):
  cases=[("solver/a.C","y",None,"CONTENT_CHANGED"),("solver/a.C","x",0o755,"MODE_CHANGED"),("solver/a.C",None,None,"DELETED"),("solver/new.C","x",None,"ADDED"),("cases/c/d","y",None,"CONTENT_CHANGED"),("config/a","y",None,"CONTENT_CHANGED"),("scripts/espresso_reference_math.py","y",None,"CONTENT_CHANGED"),("Allrun","y",None,"CONTENT_CHANGED"),("README.md","x",None,"ADDED")]
  for p,c,m,reason in cases:
   with self.subTest(path=p,reason=reason):
    t,b,r=self.repo(); h=self.commit(t,p,c,m); out=verify(t,b,h,r); items=out["protected_changes"]+out["unexpected_changes"]; self.assertTrue(any(reason in x["reasons"] for x in items),reason)
 def test_nonancestor(self):
  t,b,r=self.repo(); subprocess.run(["git","-C",t,"checkout","-q","--orphan","other"],check=True); subprocess.run(["git","-C",t,"rm","-qrf","."],check=True); (t/"x").write_text("x"); subprocess.run(["git","-C",t,"add","."],check=True); subprocess.run(["git","-C",t,"commit","-qm","other"],check=True); h=subprocess.check_output(["git","-C",t,"rev-parse","HEAD"],text=True).strip()
  with self.assertRaisesRegex(ValueError,"BASE_NOT_ANCESTOR"): verify(t,b,h,r)
