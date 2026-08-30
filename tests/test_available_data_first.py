import copy, hashlib, json, pathlib, sys, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts")); import data_availability_preflight as pre
class TestAvailableDataFirst(unittest.TestCase):
 def test_guidance_and_strategy(self):
  self.assertIn("AVAILABLE_DATA_FIRST_POLICY",(ROOT/"AGENTS.md").read_text())
  self.assertIn("AGENTS.md",(ROOT/"CLAUDE.md").read_text())
  state=(ROOT/"docs/PROJECT_STATE.md").read_text(); self.assertIn("AVAILABLE_DATA_AUTHORITY",state); self.assertIn("CURRENT_DATA_SUFFICIENCY",state)
 def test_authority_and_exemplar(self):
  a=json.loads((ROOT/"provenance/AVAILABLE_DATA_AUTHORITY.json").read_text()); self.assertEqual(a["puckworks_commit"],"7cf18d7bc388f636d9bca98e6e1a1def4bf08cf5"); self.assertNotIn("/home/",json.dumps(a))
  d=json.loads((ROOT/"docs/analysis/pannusch_prior_impact_001/DATA_AVAILABILITY_PREFLIGHT.json").read_text()); pre.validate(d)
  bad=copy.deepcopy(d); bad["data_sufficiency_status"]="DATA_STARVED"
  with self.assertRaises(ValueError): pre.validate(bad)
  bad=copy.deepcopy(d); bad["home_lab_recommendation"]["minimum_measurement_set"]=[]
  with self.assertRaises(ValueError): pre.validate(bad)
 def test_no_solver_or_angeloni_mutation(self):
  # Task diff is documentation, metadata, validators and tests only.
  import subprocess
  names=subprocess.check_output(["git","diff","--name-only","origin/main"],cwd=ROOT,text=True).splitlines()
  self.assertFalse(any(x.startswith("solver/") for x in names)); self.assertFalse(any("angeloni" in x.lower() for x in names))
if __name__=="__main__":unittest.main()
