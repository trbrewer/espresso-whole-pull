import copy,hashlib,json,math,tempfile,unittest
from pathlib import Path
from analysis.ewp_porosity_permeability_prior_001.authority import verify,STOP_AUTHORITY
from analysis.ewp_porosity_permeability_prior_001.source_adapters import wadsworth,vaca
from analysis.ewp_porosity_permeability_prior_001.scenarios import scenario
from analysis.ewp_porosity_permeability_prior_001.sensitivity import metrics

ROOT=Path(__file__).resolve().parents[1]
PW=Path("/home/tim/espresso-development/puckworks-ewp-porosity-permeability-authority")
BASE=json.loads((ROOT/"config/reference_R0.json").read_text())
class Prior001(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.w=wadsworth(PW);cls.fig,cls.fm,cls.v=vaca(PW,BASE["liquid"]["dynamic_viscosity_Pa_s"])
 def test_authority_exact(self):self.assertEqual(verify(PW)["tree"],"6175b4ad39f45ebcdec32a176e5611bf3b03655b")
 def test_authority_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(RuntimeError,STOP_AUTHORITY):verify(Path(d))
 def test_wadsworth_counts_and_structure(self):
  self.assertEqual(len(self.w),22);self.assertEqual(sum(r["k_m2"] is not None for r in self.w),21);self.assertEqual(sum(r["k_m2"] is None for r in self.w),1);self.assertEqual(len(set(r["coffee"] for r in self.w)),2);self.assertTrue(all(sum(r["coffee"]==c for r in self.w)==11 for c in set(r["coffee"] for r in self.w)))
 def test_wadsworth_k_extrema(self):
  k=[r["k_m2"] for r in self.w if r["k_m2"] is not None];self.assertEqual(min(k),1.58e-11);self.assertEqual(max(k),1.91e-10)
 def test_wadsworth_definitions_separate(self):self.assertTrue(any(r["phi_total"]!=r["phi_connected"] for r in self.w if r["phi_total"] is not None));self.assertTrue(all(r["uncertainty_semantics"]=="REPORTED_MAGNITUDE_CONFIDENCE_LEVEL_NOT_STATED" for r in self.w))
 def test_vaca_lineages(self):self.assertEqual(len(self.fig),50);self.assertFalse(self.fm["contains_direct_permeability"]);self.assertEqual(len(self.fm["devices"]),2);self.assertEqual(len(self.v),9)
 def test_vaca_viscosity_reexpression(self):
  for r in self.v:self.assertAlmostEqual(r["k_ewp_reference_mu_m2"]/r["k_published_mu_m2"],0.000315/0.0035,14)
 def test_primary_k_separation(self):
  _,c,_=scenario(BASE,"K",k=1e-12);self.assertEqual(c["hydraulics"]["wetting_permeability_m2"],BASE["hydraulics"]["wetting_permeability_m2"]);self.assertEqual(c["hydraulics"]["saturated_permeability_m2"],1e-12)
 def test_fixed_dose_conserves_mass_and_locations(self):
  _,c,g=scenario(BASE,"P",phi=.55,closure="FIXED_DOSE_MASS_CONSERVING_PRIMARY");self.assertAlmostEqual(g["implied_dry_mass_kg"],.02,14);L=c["coffee_bed"]["bed_depth_m"];self.assertTrue(0<c["hydraulics"]["permeability_profile"]["interface_position_m"]<L);self.assertTrue(all(0<p["position_m"]<L for p in c["verification"]["pressure_probes"]))
 def test_fixed_geometry_reports_mass_inconsistency(self):self.assertNotEqual(scenario(BASE,"P",phi=.55,closure="FIXED_GEOMETRY_TRANSPORT_DIAGNOSTIC")[2]["mass_inconsistency_kg"],0)
 def test_invalid_phi_not_clipped(self):
  with self.assertRaises(ZeroDivisionError):scenario(BASE,"P",phi=1,closure="FIXED_DOSE_MASS_CONSERVING_PRIMARY")
 def test_resistance_units_and_monotone_pressure(self):
  m=metrics(ROOT,BASE);L=BASE["coffee_bed"]["bed_depth_m"];K=BASE["hydraulics"]["saturated_permeability_m2"];A=math.pi*BASE["geometry"]["basket_radius_m"]**2;mu=BASE["liquid"]["dynamic_viscosity_Pa_s"];rho=BASE["liquid"]["density_kg_m3"];self.assertAlmostEqual(m["L_over_K_m_inv"],L/K);self.assertAlmostEqual(m["R_Q_pa_s_m3"],mu*L/(A*K));self.assertAlmostEqual(m["R_m_pa_s_kg"],mu*L/(rho*A*K));self.assertGreater(metrics(ROOT,scenario(BASE,"x",pressure=9e5)[1])["steady_outlet_volume_flow_m3_s"],metrics(ROOT,scenario(BASE,"x",pressure=6e5)[1])["steady_outlet_volume_flow_m3_s"])
 def test_saturated_k_does_not_change_first_drip(self):self.assertEqual(metrics(ROOT,BASE)["first_drip_s"],metrics(ROOT,scenario(BASE,"K",k=1e-12)[1])["first_drip_s"])
 def test_load_bearing_hashes(self):
  expected={"config/reference_R0.json":"67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286","solver/espressoWholePullFoam/espressoWholePullFoam.C":"99c8fe756a57410eff65e302784247346d2d2b0d61d6f9db401033b73996b6e6","scripts/prepare_case.py":"e99443c47594321ccb48b73a20af474c4f453238ffca2096e1971e3cd73390d6"};self.assertEqual({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in expected},expected)
 def test_claim_and_nonfusion(self):
  s=json.loads((ROOT/"docs/analysis/ewp_porosity_permeability_prior_001/summary.json").read_text());self.assertEqual(s["decision"]["claim_ceiling"],"SOURCE_CONDITIONED_STATIC_POROSITY_AND_PERMEABILITY_PRIOR_QUALIFICATION_FOR_EWP_HYDRAULIC_SENSITIVITY");self.assertEqual(s["counts"]["wadsworth_rows"],22);self.assertEqual(s["counts"]["vaca_c1"],9)
if __name__=="__main__":unittest.main()
