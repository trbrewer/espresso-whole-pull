import copy,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestBoundary(unittest.TestCase):
 def test_contract_and_adversarial_paths(self):
  import sys;sys.path.insert(0,str(ROOT/"scripts"));import verify_wp03b_nonprotected_verification as v
  c=json.loads((ROOT/"validation/contracts/WP_0_3B_NONPROTECTED_EXTRACTION_VERIFICATION_CONTRACT.json").read_text())
  h={p:v.sha(ROOT/p) for p in v.FROZEN}
  self.assertTrue(all(v.evaluate(c,set(v.PRE),h,set(),None).values()))
  for extra in ("solver/espressoWholePullFoam/espressoWholePullFoam.C","scripts/analyze_wp02.py"):
   x=copy.deepcopy(c);x["permitted_changed_paths"].append(extra)
   self.assertFalse(v.evaluate(x,set(v.PRE),h,set(),None)["contract_path_set_exact"])
  self.assertFalse(v.evaluate(c,set(v.PRE)|{"config/reference_R0.json"},h,set(),None)["repository_path_set_exact"])
  bad=dict(h);bad[next(iter(bad))]="0"*64
  self.assertFalse(v.evaluate(c,set(v.PRE),bad,set(),None)["frozen_hashes"])
  self.assertFalse(v.evaluate(c,set(v.PRE),h,{"puckworks"},None)["no_forbidden_imports"])
 def test_source_identity(self):
  from tools.reference.wp03b.provenance import SOURCES
  self.assertEqual(SOURCES["moroney2017"]["card_sha256"],"d4ad68ae4fd4c0a725fa10dff49a87f81d5c471a1648221ee9a9522c4c847586")
if __name__=="__main__":unittest.main()
