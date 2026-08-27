import json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

from scripts.verify_sci_ed_002_handoff import EXACT_STATUS, VENDORED_STATUS, HandoffError, verify

ROOT=Path(__file__).parents[1]

class SciEd002Handoff(unittest.TestCase):
    def test_vendored_mode_is_explicitly_limited(self):
        r=verify(mode="vendored-only")
        self.assertEqual(r["status"],VENDORED_STATUS); self.assertFalse(r["full_handoff_verified"])
        self.assertFalse(r["producer_commit_verified"]); self.assertFalse(r["producer_tree_verified"])
        self.assertEqual(r["no_physics_evaluation"],"NOT_PART_OF_HANDOFF_VERIFIER")
        self.assertNotEqual(r["status"],"SCI_ED_002_HANDOFF_VERIFIED")

    def test_exact_mode_requires_producer(self):
        with patch.dict(os.environ,{},clear=True), self.assertRaisesRegex(HandoffError,"EXACT_PRODUCER_ROOT_REQUIRED"):
            verify()

    def test_real_exact_producer_when_explicitly_supplied(self):
        value=os.environ.get("PUCKWORKS_GIT_REPOSITORY")
        if value is None: self.skipTest("EXACT_PRODUCER_OBJECT_NOT_CHECKED")
        r=verify(producer_root=Path(value))
        self.assertEqual(r["status"],EXACT_STATUS); self.assertTrue(r["full_handoff_verified"])
        self.assertEqual(r["producer_schema_count"],20)

    def test_claim_ceiling_mutations_fail_vendored_validation(self):
        cases=(("commissioning_authorized",True,"COMMISSIONING_STATUS_WEAKENED"),("predictor_eligible",True,"PREDICTOR_ELIGIBILITY_WEAKENED"),("c_s0_mapping_status","ESTABLISHED","C_S0_STATUS_WEAKENED"))
        for field,value,reason in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                root=Path(td); target=root/"docs/validation/sci_ed_002"; target.mkdir(parents=True)
                for name in ("PUCKWORKS_AUTHORITY.json","SCI_ED_002_EXPORT.json"): shutil.copy2(ROOT/"docs/validation/sci_ed_002"/name,target/name)
                export=json.loads((target/"SCI_ED_002_EXPORT.json").read_text()); export["claim_ceiling"][field]=value
                data=(json.dumps(export,separators=(",",":"),sort_keys=True)+"\n").encode(); (target/"SCI_ED_002_EXPORT.json").write_bytes(data)
                lock=json.loads((target/"PUCKWORKS_AUTHORITY.json").read_text()); lock["producer_export_sha256"]=__import__("hashlib").sha256(data).hexdigest(); (target/"PUCKWORKS_AUTHORITY.json").write_text(json.dumps(lock))
                with self.assertRaisesRegex(HandoffError,reason): verify(root,mode="vendored-only")

    def test_same_tree_different_commit_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); subprocess.run(["git","init","-q",str(repo)],check=True)
            subprocess.run(["git","-C",str(repo),"config","user.email","test@example.invalid"],check=True)
            subprocess.run(["git","-C",str(repo),"config","user.name","Test"],check=True)
            (repo/"x").write_text("same\n"); subprocess.run(["git","-C",str(repo),"add","x"],check=True)
            subprocess.run(["git","-C",str(repo),"commit","-q","-m","A"],check=True)
            a=subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()
            subprocess.run(["git","-C",str(repo),"commit","-q","--allow-empty","-m","B"],check=True)
            b=subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()
            ta=subprocess.check_output(["git","-C",str(repo),"rev-parse",a+"^{tree}"],text=True).strip()
            tb=subprocess.check_output(["git","-C",str(repo),"rev-parse",b+"^{tree}"],text=True).strip()
            self.assertNotEqual(a,b); self.assertEqual(ta,tb)
            with self.assertRaisesRegex(HandoffError,"SUPPLIED_PRODUCER_COMMIT_MISMATCH"):
                verify(producer_root=repo,producer_commit=b)

    def test_ci_requires_real_exact_producer(self):
        text=(ROOT/".github/workflows/sci-ed-002-exact-producer.yml").read_text()
        for required in ("repository: trbrewer/puckworks","steps.lock.outputs.commit","rev-parse HEAD^{tree}","--mode exact-producer","--producer-root puckworks-producer","SCI_ED_002_HANDOFF_EXACT_PRODUCER_VERIFIED"):
            self.assertIn(required,text)
        self.assertNotIn("--mode vendored-only",text)

    def test_current_result_separates_status_axes(self):
        result=json.loads((ROOT/"docs/validation/sci_ed_002/RESULT.json").read_text())
        self.assertEqual(result["scientific_protocol_disposition"],"SCI_ED_002_PROTOCOL_INCOMPLETE_COMMISSIONING_BLOCKED_REFERENCE_EXTRACTABILITY_STOPPING_RULE_NOT_DEFENSIBLY_FROZEN")
        self.assertEqual(result["review_disposition"],"PENDING_INDEPENDENT_EXACT_HEAD_REREVIEW")
        self.assertEqual(result["verification"]["historical_verifier_status"],"FAIL_REPRODUCED_PREEXISTING_NOT_BRANCH_DIFF")
        self.assertEqual(result["verification"]["producer_object_mode"],"exact-producer")
        self.assertFalse(result["claim_ceiling"]["commissioning_authorized"])
        self.assertFalse(result["claim_ceiling"]["merge_authorized"])

    def test_historical_r1_records_unchanged_from_r2a_start(self):
        paths=subprocess.check_output(["git","-C",str(ROOT),"diff","--name-only","00066712d561ee94510a98257e90e35095e55314","--","docs/validation/sci_ed_002/r1"],text=True).splitlines()
        self.assertEqual(paths,[])

if __name__=="__main__": unittest.main()
