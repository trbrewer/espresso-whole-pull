import csv,hashlib,json,unittest
from pathlib import Path
from analysis.xsv_pannusch_ewp_input_mapping_001.artifacts import generate,reduce_disposition
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"docs/analysis/xsv_pannusch_ewp_input_mapping_001"
def load(n):return json.loads((OUT/n).read_text())
def rows(n):
 with (OUT/n).open() as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def syn(role="OPERATIONAL_PROPERTY_INPUT",qualified="false",context="false",source="PASS",physical="PASS"):
 return {"mapping_role":role,"operationally_qualified":qualified,"context_compatible":context,"source_authority_gate":source,"physical_quantity_gate":physical}
class MappingC1(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.r=rows("INPUT_REGISTRY.csv");c.m=rows("MAPPING_MATRIX.csv");c.ids={x["input_id"] for x in c.r};c.mm={x["mapping_id"]:x for x in c.m}
 def test_reducer(self):
  self.assertEqual(reduce_disposition([syn(qualified="true")])[1],"A");self.assertEqual(reduce_disposition([syn("DOCUMENTATION_ONLY_COMPATIBILITY",context="true")])[1],"B")
  self.assertEqual(reduce_disposition([syn(),syn("DOCUMENTATION_ONLY_COMPATIBILITY",context="true")])[1],"C");self.assertEqual(reduce_disposition([syn()])[1],"C")
  self.assertEqual(reduce_disposition([syn(source="FAIL",physical="UNRESOLVED")])[1],"D");self.assertEqual(reduce_disposition([],False)[1],"E")
 def test_current_reducer(self):
  d=load("MAPPING_DECISION.json");self.assertEqual(reduce_disposition(self.m),(d["scientific_disposition"],"C"));self.assertEqual((d["operational_candidate_count"],d["rejected_operational_count"]),(21,21));self.assertFalse(d["operationally_qualified_mapping_ids"])
 def test_unique_and_consumers(self):
  self.assertEqual(len(self.r),len(self.ids));required={"E-FLOW-MODE","E-FLOW-TYPE","E-FLOW-CONST","E-FLOW-TIMES","E-FLOW-VALUES","E-FLOW-TOL","E-RADIUS","E-DOSE","E-DENSITY","E-POROSITY","E-SATURATION","E-INLET-ZERO","E-INITIAL-CONC","E-TEMP","E-MU","E-DEFF","E-PERMEABILITY","E-PARTICLE","E-SPECIES-ID","E-INVENTORY","E-CAPACITY","E-KEXT","E-END","E-FRACTIONS"};self.assertTrue(required<=self.ids)
  self.assertNotIn("P-RHO",self.ids);self.assertNotIn("P-D32",self.ids);self.assertTrue({"P-RHO-CLOSURE","P-RHO-FLOW-CONVERSION","P-D32-CLOSURE","P-D32-RECOMPUTED"}<=self.ids)
 def test_density_temperature_consumers(self):
  d=next(x for x in self.r if x["input_id"]=="E-DENSITY");t=next(x for x in self.r if x["input_id"]=="E-TEMP");self.assertIn("liquid.density_kg_m3",d["symbol_or_key"]);self.assertIn("liquidDensity",d["symbol_or_key"]);self.assertEqual(d["runtime_consumer_status"],"CONSUMED");self.assertEqual(t["runtime_consumer_status"],"VALIDATED_NOT_RENDERED_TO_SOLVER")
 def test_complete_coverage(self):
  covered={x["pannusch_input_id"] for x in self.m};pids={x["input_id"] for x in self.r if x["system"]=="PANNUSCH"};self.assertEqual(pids-covered,set());self.assertTrue(all(x["pannusch_input_id"] in self.ids for x in self.m));self.assertTrue(all(x["ewp_input_id"] in self.ids or x["ewp_input_id"]=="NO_EWP_RUNTIME_CONSUMER" for x in self.m))
 def test_context_is_genuine(self):
  ctx=[x for x in self.m if x["context_compatible"]=="true"];self.assertEqual([x["mapping_id"] for x in ctx],["M-DBED","M-ACS","M-DOSE","M-SATURATED","M-CLEAN","M-DS1"])
  self.assertTrue(all(x["physical_quantity_gate"]==x["unit_basis_gate"]=="PASS" and x["operationally_qualified"]=="false" for x in ctx));self.assertEqual(self.mm["M-TBOUNDS"]["context_compatible"],"false");self.assertEqual(load("summary.json")["context_compatibility_count"],6)
 def test_density_decisions_do_not_resolve_flow(self):
  a=self.mm["M-DENSITY-CLOSURE"];b=self.mm["M-DENSITY-FIXED"];self.assertEqual(a["mapping_classification"],"REQUIRES_CONSTITUTIVE_INFERENCE");self.assertEqual(a["no_constitutive_inference_gate"],"FAIL");self.assertEqual(b["mapping_classification"],"SOURCE_AUTHORITY_INELIGIBLE");self.assertEqual(b["source_authority_gate"],"FAIL");self.assertEqual(load("UNIT_BASIS_AUDIT.json")["authoritative_adjudication"],"H_UNRESOLVED")
 def test_original_protections(self):
  exp={"M-FLOW-CONST":"UNIT_OR_BASIS_UNRESOLVED","M-FLOW-ENDPOINTS":"REQUIRES_SPATIAL_OR_TEMPORAL_RECONSTRUCTION","M-MASSDATA":"OUTLET_FLOW_NOT_INLET_FLOW","M-DIV098":"SOURCE_AUTHORITY_INELIGIBLE","M-PHIV2":"SEMANTIC_QUANTITY_MISMATCH","M-GRIND":"REQUIRES_CONSTITUTIVE_INFERENCE","M-DI":"SEMANTIC_QUANTITY_MISMATCH","M-CS0":"REQUIRES_CALIBRATION_OR_REFIT","M-KREF":"SEMANTIC_QUANTITY_MISMATCH","M-AB-KEXT":"REQUIRES_CONSTITUTIVE_INFERENCE","M-TOLERANCE":"REQUIRES_NUMERICAL_METHOD_CHANGE"}
  for k,v in exp.items():self.assertEqual(self.mm[k]["mapping_classification"],v)
 def test_terminal_gates_no_materializer(self):
  gates=[k for k in self.m[0] if k.endswith("_gate")];self.assertTrue(all(x[g] in {"PASS","FAIL","NOT_APPLICABLE","UNRESOLVED"} for x in self.m for g in gates));self.assertFalse(load("MAPPING_DECISION.json")["materializer_implemented"])
 def test_deterministic_regeneration(self):
  before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir()};generate();after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir()};self.assertEqual(before,after)
 def test_programme(self):
  p=json.loads((ROOT/"provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json").read_text());o={x["opportunity_id"]:x for x in p["opportunities"]};self.assertEqual(p["current_priority"],"SCI-MD-011");self.assertEqual(p["last_completed_opportunity_review"],"SCI-ED-003");self.assertEqual(o["XSV-PANNUSCH-EWP-INPUT-MAPPING-001"]["status"],"COMPLETE_NEGATIVE");self.assertEqual(o["SCI-DATA-FUSION-001"]["status"],"COMPLETE_NEGATIVE");self.assertTrue(o["SCI-DATA-FUSION-001"]["exhausted_for_decision"])
  text="\n".join((ROOT/x).read_text() for x in ["docs/PROJECT_STATE.md","docs/strategy/EXISTING_DATA_LEVERAGE_PROGRAMME.md","docs/analysis/data_leverage/DATA_LEVERAGE_LEDGER.csv"]);self.assertIn(load("summary.json")["disposition"],text);self.assertIn("separate authorization",text.lower())
 def test_authority_paths(self):
  a=load("REPOSITORY_AUTHORITY.json");self.assertEqual(a["correction_starting_commit"],"3e988084455b6dde85321b9447730a3747352ef0");self.assertEqual(a["puckworks_authority_commit"],"2058d0e947ee9eb92c52d64f6165b810f1fb4732");self.assertNotIn("/home/","\n".join(p.read_text(errors="ignore") for p in OUT.iterdir()))
 def test_invariance(self):
  e={"solver/espressoWholePullFoam/espressoWholePullFoam.C":"99c8fe756a57410eff65e302784247346d2d2b0d61d6f9db401033b73996b6e6","solver/espressoWholePullFoam/prescribedFlowBoundaryModel.H":"a593bbb86e06af081b9a6d277c8f99030f4ae25f86c86949645d56fd6e2e8082","config/reference_R0.json":"67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286","dependencies/puckworks.lock.json":"52b15ceef87d503a3e77c6e3c1cbed785185d2dde0b79647e5fbe309395d2f10","scripts/prepare_case.py":"e99443c47594321ccb48b73a20af474c4f453238ffca2096e1971e3cd73390d6"}
  for p,h in e.items():self.assertEqual(sha(p),h)
if __name__=="__main__":unittest.main()
