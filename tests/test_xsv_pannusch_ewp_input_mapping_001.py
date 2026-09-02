import csv, hashlib, json, re, unittest
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs/analysis/xsv_pannusch_ewp_input_mapping_001"
def load(name): return json.loads((OUT/name).read_text())
def rows(name):
 with (OUT/name).open() as stream: return list(csv.DictReader(stream))
def sha(path): return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

class TestInputMapping001(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.reg=rows("INPUT_REGISTRY.csv");cls.maps=rows("MAPPING_MATRIX.csv");cls.byid={x["mapping_id"]:x for x in cls.maps}
 def test_authority_and_predecessor(self):
  a=load("REPOSITORY_AUTHORITY.json")
  self.assertEqual(a["puckworks_authority_commit"],"2058d0e947ee9eb92c52d64f6165b810f1fb4732")
  self.assertTrue(a["no_local_path_assertion"] and a["no_puckworks_mutation_assertion"])
  self.assertIn("SCI_MD_PANNUSCH_FLOW_HISTORY_001_FLOW_AUTHORITY_INELIGIBLE",(ROOT/"docs/analysis/sci_md_pannusch_flow_history_001/DECISION.json").read_text())
 def test_no_machine_identifiers_or_paths(self):
  text="\n".join(p.read_text(errors="ignore") for p in OUT.iterdir())
  self.assertNotRegex(text,r"/home/|/Users/|[A-Za-z]:\\|espresso-development")
 def test_registry_complete_and_unique(self):
  ids=[x["input_id"] for x in self.reg];self.assertEqual(len(ids),len(set(ids)))
  required={"P-Q-CONST","P-Q0","P-QT","P-Q-GRAD-END","P-MASSDATA-FLOW","P-Q-DIV098","P-BEV-DM-DT","P-DURATION","P-TBOUNDS","P-CLOCKS","P-T-CONST","P-T-END","P-TT","P-TREF","P-RHO","P-ETA","P-DI","P-MOLPROP","P-DBED","P-ACS","P-L","P-DOSE","P-ALPHA-L","P-PHI-V2","P-SATURATED","P-CLEAN-INLET","P-1D","P-DS1","P-DS2","P-D32","P-PSI","P-GRIND","P-SOLUTE","P-AB","P-KREF","P-GAMMA","P-CS0","P-CL1","P-EQ-IC","P-TDS-PSEUDO","E-FLOW-MODE","E-FLOW-TYPE","E-FLOW-CONST","E-FLOW-TIMES","E-FLOW-VALUES","E-FLOW-TOL","E-RADIUS","E-DOSE","E-POROSITY","E-SATURATION","E-INLET-ZERO","E-MU","E-DEFF","E-PERMEABILITY","E-INVENTORY","E-CAPACITY","E-KEXT","E-END","E-FRACTIONS","E-TEMP","E-PARTICLE"}
  self.assertEqual(set(ids),required)
 def test_mapping_gates_complete_and_final(self):
  gates=[x for x in self.maps[0] if x.endswith("_gate")]
  for m in self.maps:
   self.assertIn(m["mapping_classification"],load("TASK_CONTRACT.json")["rejection_classes"])
   self.assertTrue(all(m[g] in {"PASS","FAIL","NOT_APPLICABLE","UNRESOLVED"} for g in gates))
 def test_no_operational_mapping_accepted(self):
  self.assertFalse(any(x["operationally_qualified"]=="true" for x in self.maps))
  self.assertTrue(any(x["context_compatible"]=="true" for x in self.maps))
  for x in self.maps:
   if x["context_compatible"]=="true": self.assertEqual(x["operationally_qualified"],"false")
 def test_fail_closed_semantics(self):
  expected={"M-FLOW-CONST":"UNIT_OR_BASIS_UNRESOLVED","M-FLOW-ENDPOINTS":"REQUIRES_SPATIAL_OR_TEMPORAL_RECONSTRUCTION","M-MASSDATA":"OUTLET_FLOW_NOT_INLET_FLOW","M-DIV098":"SOURCE_AUTHORITY_INELIGIBLE","M-PHIV2":"SEMANTIC_QUANTITY_MISMATCH","M-CS0":"REQUIRES_CALIBRATION_OR_REFIT","M-KREF":"SEMANTIC_QUANTITY_MISMATCH","M-AB-KEXT":"REQUIRES_CONSTITUTIVE_INFERENCE","M-DI":"SEMANTIC_QUANTITY_MISMATCH","M-TOLERANCE":"REQUIRES_NUMERICAL_METHOD_CHANGE"}
  for k,v in expected.items(): self.assertEqual(self.byid[k]["mapping_classification"],v)
 def test_flow_audit_hypotheses_and_round_trip(self):
  a=load("UNIT_BASIS_AUDIT.json");self.assertEqual(a["authoritative_adjudication"],"H_UNRESOLVED")
  self.assertTrue(a["source_condition_restrictions"]["C07_C08_histories_excluded"] and a["source_condition_restrictions"]["MassData_flow_excluded"])
  for x in a["numeric_checks"]:
   q=Decimal(x["source_numeric_value"]);v=Decimal(x["converted_ewp_m3_s"])
   self.assertEqual(v,q*Decimal("1e-6"));self.assertEqual(Decimal(x["inverse_converted_value"]),q)
   self.assertFalse(x["density_enters"] or x["area_enters"] or x["porosity_enters"] or x["mapping_use_authorized"])
  self.assertFalse(a["mass_hypothesis_density"]["mapping_use_authorized"])
 def test_context_states_and_run_control(self):
  for mid in ("M-SATURATED","M-CLEAN","M-DURATION","M-TBOUNDS"):
   self.assertEqual(self.byid[mid]["context_compatible"],"true");self.assertEqual(self.byid[mid]["operationally_qualified"],"false")
 def test_decision_summary_result_consistency(self):
  d=load("MAPPING_DECISION.json");s=load("summary.json");text=(OUT/"RESULT.md").read_text()
  self.assertEqual(d["scientific_disposition"],s["disposition"]);self.assertIn(s["disposition"],text)
  self.assertEqual(s["mapping_count"],len(self.maps));self.assertEqual(s["registry_count"],len(self.reg))
  self.assertEqual(s["context_compatibility_count"],sum(x["context_compatible"]=="true" for x in self.maps))
  self.assertEqual(d["operationally_qualified_mapping_ids"],[]);self.assertFalse(d["materializer_implemented"])
 def test_repository_invariance(self):
  expected={"solver/espressoWholePullFoam/espressoWholePullFoam.C":"99c8fe756a57410eff65e302784247346d2d2b0d61d6f9db401033b73996b6e6","solver/espressoWholePullFoam/prescribedFlowBoundaryModel.H":"a593bbb86e06af081b9a6d277c8f99030f4ae25f86c86949645d56fd6e2e8082","config/reference_R0.json":"67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286","dependencies/puckworks.lock.json":"52b15ceef87d503a3e77c6e3c1cbed785185d2dde0b79647e5fbe309395d2f10","scripts/prepare_case.py":"e99443c47594321ccb48b73a20af474c4f453238ffca2096e1971e3cd73390d6"}
  for p,h in expected.items(): self.assertEqual(sha(p),h)
 def test_claim_boundary_complete(self):
  claims=set(load("MAPPING_DECISION.json")["claims"])
  self.assertEqual(claims,{"SOURCE_INTERNAL","TARGET_EXPOSED","NOT INDEPENDENT VALIDATION","NOT PHYSICAL VALIDATION","NOT HYDRAULIC VALIDATION","NOT PUCK_FACE_FLOW VALIDATION","NOT PRESSURE_FLOW_VALIDATION","NOT CHEMISTRY VALIDATION","NOT MODEL COUPLING","NOT PRODUCTION QUALIFICATION","NO PRODUCTION ADOPTION"})

if __name__=="__main__": unittest.main()
