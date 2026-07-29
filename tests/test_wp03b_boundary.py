import copy,json,tempfile,unittest
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
 def test_a1_boundary_is_independently_fixed(self):
  import sys;sys.path.insert(0,str(ROOT/"scripts"));import verify_wp03b_nonprotected_verification as v
  c=json.loads((ROOT/"validation/contracts/WP_0_3B_A1_NONPROTECTED_EXTRACTION_VERIFICATION_CONTRACT.json").read_text())
  self.assertEqual(set(c["fixed_changed_paths"]),set(v.A1))
  bad=copy.deepcopy(c);bad["fixed_changed_paths"].append("solver/espressoWholePullFoam/espressoWholePullFoam.C")
  self.assertNotEqual(set(bad["fixed_changed_paths"]),set(v.A1))
  self.assertEqual(v.sha(ROOT/"validation/contracts/WP_0_3B_NONPROTECTED_EXTRACTION_VERIFICATION_CONTRACT.json"),"4b05d9a8f7f91dc6e476c9942639524213541d3f887452d4fb369715bc9f89a6")
  self.assertEqual(v.sha(ROOT/"validation/results/WP_0_3B_NONPROTECTED_EXTRACTION_VERIFICATION_RESULT.json"),"80d0a91d6456ff1219e74f0503f3e6846c9974b3ed868cff19f6f9da943cde90")
 def test_amended_builder_in_memory_determinism_and_atomic_preflight(self):
  from tools.reference.wp03b import canonical_run as c
  a=c.build_amended_result(ROOT,"synthetic-freeze","synthetic-tree")
  b=c.build_amended_result(ROOT,"synthetic-freeze","synthetic-tree")
  self.assertEqual(json.dumps(a,sort_keys=True),json.dumps(b,sort_keys=True))
  with tempfile.TemporaryDirectory() as d:
   missing=Path(d)/"missing"/"result.json"
   with self.assertRaises(FileNotFoundError):c.atomic_write_result(missing,a)
   self.assertFalse(missing.exists())
 def test_source_identity(self):
  from tools.reference.wp03b.provenance import SOURCES
  self.assertEqual(SOURCES["moroney2017"]["card_sha256"],"d4ad68ae4fd4c0a725fa10dff49a87f81d5c471a1648221ee9a9522c4c847586")
if __name__=="__main__":unittest.main()
