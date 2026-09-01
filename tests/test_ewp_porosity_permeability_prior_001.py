import csv,hashlib,json,math,os,shutil,subprocess,tempfile,unittest
from unittest import mock
from pathlib import Path
from analysis.ewp_porosity_permeability_prior_001.authority import verify,STOP_AUTHORITY
from analysis.ewp_porosity_permeability_prior_001.decision import decide
from analysis.ewp_porosity_permeability_prior_001.mappings import build,validate
from analysis.ewp_porosity_permeability_prior_001.source_adapters import wadsworth,vaca
from analysis.ewp_porosity_permeability_prior_001.scenarios import scenario
from analysis.ewp_porosity_permeability_prior_001.sensitivity import metrics
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/"docs/analysis/ewp_porosity_permeability_prior_001";ENV="EWP_POROSITY_PERMEABILITY_PRIOR_PUCKWORKS_ROOT";BASE=json.loads((ROOT/"config/reference_R0.json").read_text())
def producer_root():
 raw=os.environ.get(ENV)
 if not raw:raise RuntimeError(f"{STOP_AUTHORITY}: {ENV} is required; no fallback path")
 return Path(raw)
class Prior001(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.pw=producer_root();verify(cls.pw);cls.w=wadsworth(cls.pw);cls.fig,cls.fm,cls.v=vaca(cls.pw,BASE["liquid"]["dynamic_viscosity_Pa_s"]);cls.maps=build()
 def test_exact_external_authority(self):self.assertEqual(verify(self.pw)["tree"],"6175b4ad39f45ebcdec32a176e5611bf3b03655b")
 def test_missing_environment_has_stable_stop_and_no_fallback(self):
  old=os.environ.pop(ENV,None)
  try:
   with self.assertRaisesRegex(RuntimeError,STOP_AUTHORITY):producer_root()
  finally:
   if old is not None:os.environ[ENV]=old
 def test_missing_checkout_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(RuntimeError,STOP_AUTHORITY):verify(Path(d))
 def test_wrong_commit_and_tree_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   subprocess.run(["git","clone","-q",str(self.pw),d],check=True);p=Path(d)/"extra";p.write_text("x\n");subprocess.run(["git","-C",d,"add","extra"],check=True);subprocess.run(["git","-C",d,"-c","user.name=test","-c","user.email=test@example.invalid","commit","-qm","wrong"],check=True)
   with self.assertRaisesRegex(RuntimeError,STOP_AUTHORITY):verify(Path(d))
 def test_wrong_tree_alone_fails_closed(self):
  real=subprocess.check_output
  def answer(cmd,**kw):
   if cmd[-1]=="HEAD":return "a3428a4d4ad571ef3168a70e8a04620fca5d3520\n"
   if cmd[-1]=="HEAD^{tree}":return "0"*40+"\n"
   return real(cmd,**kw)
  with mock.patch("analysis.ewp_porosity_permeability_prior_001.authority.subprocess.check_output",side_effect=answer):
   with self.assertRaisesRegex(RuntimeError,STOP_AUTHORITY):verify(self.pw)
 def test_changed_source_file_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   subprocess.run(["git","clone","-q",str(self.pw),d],check=True);p=Path(d)/"puckworks/data/wadsworth2026/wadsworth2026_table1_full.csv";p.write_text(p.read_text()+"\n")
   with self.assertRaisesRegex(RuntimeError,STOP_AUTHORITY):verify(Path(d))
 def test_no_committed_home_paths(self):
  forbidden="/"+"home/tim/";r=subprocess.run(["git","grep","-n",forbidden],cwd=ROOT,text=True,capture_output=True);self.assertEqual(r.returncode,1,r.stdout)
 def test_wadsworth_and_vaca_counts(self):
  self.assertEqual((len(self.w),sum(r["k_m2"] is not None for r in self.w),len(self.fig),len(self.v)),(22,21,50,9));self.assertEqual(len(set(r["coffee"] for r in self.w)),2);self.assertEqual((min(r["k_m2"] for r in self.w if r["k_m2"]),max(r["k_m2"] for r in self.w if r["k_m2"])),(1.58e-11,1.91e-10))
 def test_mapping_units_files_and_semantics(self):
  by={r["source_variable"]:r for r in self.maps}
  for v in ["phi_T_total","phi_p_connected","measured_dry_bed_porosity","calculated_dry_bed_porosity","epsilon_0"]:self.assertEqual(by[v]["source_unit"],"1")
  self.assertEqual(by["phi_T_total"]["total_or_connected_basis"],"TOTAL");self.assertEqual(by["phi_p_connected"]["total_or_connected_basis"],"CONNECTED");self.assertNotEqual(by["k_published_mu_m2"]["viscosity_treatment"],by["k_ewp_reference_mu_m2"]["viscosity_treatment"]);self.assertEqual(by["Eq11_postfit_K"]["measurement_or_derivation_method"],"POST_FIT_RECONSTRUCTION");self.assertTrue(all(r["source_file"].startswith("puckworks/data/") for r in self.maps))
 def test_operator_consistency(self):
  bad=[dict(r) for r in self.maps];x=next(r for r in bad if r["source_variable"]=="calculated_dry_bed_porosity");x["observation_operator_closure_status"]="UNRESOLVED"
  with self.assertRaisesRegex(ValueError,"UNCLOSED_OPERATOR"):validate(bad)
  self.assertFalse(any(r["primary_sensitivity_eligible"]=="true" for r in self.maps if r["source_disposition"]=="SOURCE_NATIVE_STRESS_SUPPORT_ONLY"))
 def test_primary_k_keeps_wetting_k(self):
  _,c,_=scenario(BASE,"K",k=1e-12);self.assertEqual(c["hydraulics"]["wetting_permeability_m2"],BASE["hydraulics"]["wetting_permeability_m2"])
 def test_geometry_and_stable_invalid_input(self):
  _,c,g=scenario(BASE,"P",phi=.55,closure="FIXED_DOSE_MASS_CONSERVING_PRIMARY");self.assertAlmostEqual(g["implied_dry_mass_kg"],.02,14);self.assertTrue(all(0<p["position_m"]<c["coffee_bed"]["bed_depth_m"] for p in c["verification"]["pressure_probes"]))
  with self.assertRaisesRegex(ValueError,"INVALID_POROSITY"):scenario(BASE,"bad",phi=1,closure="FIXED_DOSE_MASS_CONSERVING_PRIMARY")
 def test_case_design_and_nonfusion(self):
  rows=list(csv.DictReader((DOC/"SENSITIVITY_CASE_REGISTER.csv").open()));self.assertEqual(sum(r["case_kind"]=="OBSERVED_WITHIN_SOURCE_PAIR" and r["source"]=="WADSWORTH" for r in rows),21);self.assertEqual(sum(r["case_kind"]=="OBSERVED_WITHIN_SOURCE_PAIR" and r["source"]=="VACA_C1" for r in rows),18);self.assertEqual(sum(r["case_kind"]=="SYNTHETIC_WITHIN_SOURCE_SENSITIVITY" for r in rows),27);self.assertFalse(any("WADSWORTH" in r["source"] and "VACA" in r["source"] for r in rows));self.assertTrue(all(r["wetting_k_m2"]==str(BASE["hydraulics"]["wetting_permeability_m2"]) for r in rows))
 def test_pressure_convergence_and_extreme_labels(self):
  pr=list(csv.DictReader((DOC/"PRESSURE_FLOW_RESPONSE.csv").open()));self.assertEqual(len(pr),15);self.assertEqual({float(r["pressure_pa"]) for r in pr},{3e5,9e5,12e5});cv=list(csv.DictReader((DOC/"REDUCED_TWIN_CONVERGENCE.csv").open()));self.assertEqual(len(cv),12);self.assertTrue(all(math.isfinite(float(r["final_water_mass_kg"])) for r in cv));self.assertTrue(any(r["transfer_status"]=="OUTSIDE_DEFENSIBLE_TRANSFER_INTERPRETATION" for r in cv))
 def test_waszkiewicz_is_actual_or_explicitly_not_comparable(self):
  rows=list(csv.DictReader((DOC/"WASZKIEWICZ_CONTEXT_COMPARISON.csv").open()));self.assertTrue(rows);self.assertTrue(all(float(r["waszkiewicz_central"])>0 for r in rows));self.assertTrue(all(r["comparison_status"]=="NOT_COMPARABLE_EXACT_RANGE_UNAVAILABLE" for r in rows));self.assertFalse(any("CONTEXT_ONLY_STATIC_RANGE_COMPARISON" in r.values() for r in rows))
 def test_decision_all_branches_and_not_constant(self):
  b={"source_authority_ok":True,"eligible_porosity_supports":0,"eligible_permeability_supports":0,"stress_supports":1,"unresolved_count":0,"numerical_execution_ok":True,"pressure_response_ok":True,"convergence_ok":True,"waszkiewicz_status":"NOT_COMPARABLE_EXACT_RANGE_UNAVAILABLE","production_invariants_ok":True,"materially_structures_sensitivity":True}
  expected={(1,0):"POSITIVE_POROSITY_ONLY",(0,1):"POSITIVE_PERMEABILITY_ONLY",(1,1):"POSITIVE_POROSITY_AND_PERMEABILITY",(0,0):"NEGATIVE"}
  for (p,k),suffix in expected.items():g=dict(b,eligible_porosity_supports=p,eligible_permeability_supports=k);self.assertTrue(decide(g)["code"].endswith(suffix))
  self.assertTrue(decide(dict(b,eligible_porosity_supports=1,materially_structures_sensitivity=False))["code"].endswith("NULL"));self.assertTrue(decide(dict(b,source_authority_ok=False))["code"].endswith("BLOCKED"))
 def test_claims_and_invariants(self):
  s=json.loads((DOC/"summary.json").read_text());self.assertTrue(s["decision"]["code"].endswith("POSITIVE_POROSITY_ONLY"));text=(DOC/"RESULT.md").read_text().lower();self.assertIn("physical validation is not established",text);self.assertNotIn("universal distribution established",text);self.assertEqual(s["production_invariants"]["config/reference_R0.json"],"67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286")
 def test_deterministic_generation(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/"a";b=Path(d)/"b";cmd=["python3",str(ROOT/"scripts/run_ewp_porosity_permeability_prior_001.py"),"--root",str(ROOT),"--puckworks-root",str(self.pw)]
   subprocess.run(cmd+["--output",str(a)],check=True,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"});subprocess.run(cmd+["--output",str(b)],check=True,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"});self.assertEqual({p.relative_to(a):hashlib.sha256(p.read_bytes()).hexdigest() for p in a.iterdir()},{p.relative_to(b):hashlib.sha256(p.read_bytes()).hexdigest() for p in b.iterdir()})
if __name__=="__main__":unittest.main()
