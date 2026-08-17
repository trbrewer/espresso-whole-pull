import hashlib, importlib.util, json, os, sys, tempfile, unittest, uuid
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sci_md_002c",ROOT/"scripts/sci_md_002c.py")
M=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=M;SPEC.loader.exec_module(M)

class TestLaneAndSource(unittest.TestCase):
 def test_lane_agreement_and_paths(self):
  lane=json.loads(M.LANE.read_text()); charter=(M.DOC/"DECISION_AND_PARALLEL_LANE_CHARTER.md").read_text()
  self.assertEqual(lane["lane_id"],M.LANE_ID);self.assertIn(lane["branch"],charter)
  self.assertEqual(lane["owned_paths"][:4],["docs/analysis/sci_md_002c/**","validation/cases/sci_md_002c/**","scripts/sci_md_002c.py","tests/test_sci_md_002c.py"])
  self.assertIn("solver/**",lane["forbidden_paths"]);self.assertIn("docs/analysis/sci_lc_001a/**",lane["forbidden_paths"])
 def test_no_forbidden_import_or_dependency(self):
  text=(ROOT/"scripts/sci_md_002c.py").read_text().lower()
  self.assertNotIn("import sci_lc",text);self.assertNotIn("import puckworks",text);self.assertNotIn("solver/",text);self.assertNotIn("config/",text)
 def test_overlay_semantics_and_window(self):
  h=M.load_histories();self.assertEqual(set(h),{5,9,11})
  self.assertTrue(all(len(x)==800 for x in h.values()));self.assertEqual(h[5][0]["source_time_s"],10.01001);self.assertEqual(h[11][-1]["source_time_s"],89.98999)
  self.assertAlmostEqual(h[9][0]["observed_pressure_pa"],896674.5);self.assertAlmostEqual(h[9][0]["reference_model_pressure_pa"],871691.6)
  self.assertNotEqual(h[9][-1]["observed_flow_kg_s"],h[9][-1]["reference_model_flow_kg_s"])
 def test_overlay_hash_and_window_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.json";p.write_bytes(M.OVERLAY.read_bytes()+b" ")
   with self.assertRaisesRegex(ValueError,"SOURCE_OVERLAY_HASH_MISMATCH"):M.load_histories(p)
 def test_observed_p9_anchor(self):
  expect=M.TERMINAL_PRESSURES[9]/(M.TERMINAL_FLOWS[9]/M.RHO)
  self.assertEqual(M.hydraulic_anchor(),expect)

class TestFeasibilityAndPhysics(unittest.TestCase):
 def test_required_resistance_and_inventory(self):
  f=M.feasibility_bounds();self.assertAlmostEqual(f["required_additional_resistance"]["P11_below_observed_P9_flow_pa_s_m3"],89090772146.5091)
  masses=[x["max_inventory_kg"] for x in f["regions"]];self.assertEqual(min(masses),M.DOSE*.02*.25);self.assertEqual(max(masses),M.DOSE*.1*.75)
  self.assertIn("POTENTIALLY_FEASIBLE",{x["classification"] for x in f["regions"]});self.assertIn("CLEARLY_INVENTORY_IMPOSSIBLE",{x["classification"] for x in f["regions"]})
 def test_cake_identity_and_units(self):
  m=.001;eps=.5;alpha=1e13;h=m/(M.SOLID_RHO*(1-eps)*M.AREA);k=1/(M.SOLID_RHO*(1-eps)*alpha)
  a=M.MU*alpha*m/M.AREA**2;b=M.MU*h/(M.AREA*k);self.assertLess(abs(a-b)/a,1e-14)
 def row(self,**changes):
  r=next(x.copy() for x in M.matrix_rows() if x["case_id"]=="R1-SYNTH-P7-BASE");r.update(changes);return r
 def test_zero_limits(self):
  for change in ({"fines_fraction":0},{"release_rate_s":0},{"retention_fraction":0},{"specific_cake_resistance_m_kg":0}):
   z=M.simulate(self.row(**change));self.assertEqual(z["terminal"]["compact_layer_resistance_pa_s_m3"],0)
 def test_conservation_inventory_and_deposition(self):
  z=M.simulate(self.row());t=z["temporal"]
  self.assertLessEqual(z["max_abs_mass_residual_kg"],M.MASS_ABS_TOL);self.assertTrue(all(x["bound_mass_kg"]>=0 and x["mobile_mass_kg"]>=0 for x in t))
  self.assertGreater(t[-1]["deposited_mass_kg"],0);self.assertTrue(all(b["deposited_mass_kg"]>=a["deposited_mass_kg"] for a,b in zip(t,t[1:])))
  self.assertTrue(all((x["deposited_mass_kg"]>0 or x["compact_layer_resistance_pa_s_m3"]==0) for x in t))
 def test_fixed_active_bed_and_resistance(self):
  z=M.simulate(self.row());self.assertTrue(all(abs((x["total_resistance_pa_s_m3"]-x["compact_layer_resistance_pa_s_m3"])-M.hydraulic_anchor())<1e-3 for x in z["temporal"]))
 def test_refinement_is_operational_and_deterministic(self):
  a=M.simulate(self.row());b=M.simulate(self.row());self.assertEqual(M.hash_obj(a),M.hash_obj(b))
  refined=self.row(case_id="X",axial_cells=64,temporal_substeps=2,resolution="REFINED");c=M.simulate(refined);self.assertNotEqual(a["terminal"]["deposited_mass_kg"],c["terminal"]["deposited_mass_kg"])

class TestMatrixAndAuthority(unittest.TestCase):
 def test_matrix_counts_and_comparators(self):
  rows=M.matrix_rows();self.assertEqual(len(rows),585);self.assertEqual(len(M.adjudicative_ids()),579);self.assertEqual(sum(x["arm"]=="S1" for x in rows),576)
  self.assertEqual(len({x["case_id"] for x in rows}),len(rows));self.assertLess(len(rows),M.HARD_CAP)
  lookup={x["case_id"] for x in rows}
  for r in rows:
   if r["arm"]=="S1":self.assertIn(r["control_id"],lookup);self.assertIn(r["refinement_id"],lookup);self.assertEqual(len(r["cross_pressure_peer_ids"]),2)
 def test_generation_and_csv_agree(self):
  before={p:M.sha(p) for p in (M.OUT/"SCI_MD_002C_CASE_MATRIX.json",M.OUT/"SCI_MD_002C_CASE_MATRIX.csv")};M.verify_generated();self.assertEqual(before,{p:M.sha(p) for p in before})
  j=json.loads((M.OUT/"SCI_MD_002C_CASE_MATRIX.json").read_text())
  with (M.OUT/"SCI_MD_002C_CASE_MATRIX.csv").open() as f:self.assertEqual(len(list(__import__('csv').DictReader(f))),j["row_count"])
 def auth(self,b):
  a=M.expected_authority_bindings(b);a["bundle_uuid"]=str(uuid.uuid4());a.update(authorization_token=M.TOKEN,owner_role=M.OWNER_ROLE,authorization_date="2026-08-16T12:00:00Z");return a
 def test_production_cannot_mint_owner_authority(self):
  with tempfile.TemporaryDirectory(prefix="sci_md_002c_") as d:
   a=M.expected_authority_bindings(d);self.assertNotIn("authorization_token",a);self.assertNotIn("owner_role",a);self.assertNotIn("authorization_date",a);self.assertEqual(a["bundle_uuid"],"INDEPENDENT_OWNER_VALUE_REQUIRED")
 def test_exact_authority_and_rejections(self):
  with tempfile.TemporaryDirectory(prefix="sci_md_002c_") as d:
   p=Path(d)/"a.json";a=self.auth(d);p.write_text(M.canonical(a));self.assertEqual(M.validate_authority(p,d)["authorized_row_ids"],M.adjudicative_ids())
   for ids in ([],a["authorized_row_ids"][:1],a["authorized_row_ids"][:-1],a["authorized_row_ids"]+["EXTRA"],list(reversed(a["authorized_row_ids"]))):
    bad=dict(a);bad["authorized_row_ids"]=ids;p.write_text(M.canonical(bad))
    with self.assertRaises(ValueError):M.validate_authority(p,d)
   bad=dict(a);bad["source_tree"]="0"*40;p.write_text(M.canonical(bad))
   with self.assertRaises(ValueError):M.validate_authority(p,d)
 def test_uuid_mismatch(self):
  with tempfile.TemporaryDirectory(prefix="sci_md_002c_") as d:
   p=Path(d)/"a.json";a=self.auth(d);a["bundle_uuid"]="bad";p.write_text(M.canonical(a))
   with self.assertRaises(ValueError):M.validate_authority(p,d)

class TestDurability(unittest.TestCase):
 def test_atomic_write_readback_and_temp_exclusion(self):
  with tempfile.TemporaryDirectory(prefix="sci_md_002c_") as d:
   p=Path(d)/"r.json";h,n=M.durable_write(p,{"x":1,"tuple":("a","b")});self.assertEqual(h,M.sha(p));self.assertEqual(n,p.stat().st_size);self.assertFalse(list(Path(d).glob("*.tmp.*")))
   with self.assertRaises(FileExistsError):M.durable_write(p,{"x":2})
 def test_corruption_and_malformed_detection(self):
  rec={"case_id":"X","bundle_uuid":"u","result":{"v":1}};rec["record_sha256"]=M.internal_hash(rec)
  self.assertEqual(rec["record_sha256"],M.internal_hash(rec));bad=json.loads(M.canonical(rec));bad["result"]["v"]=2;self.assertNotEqual(bad["record_sha256"],M.internal_hash(bad))
  with self.assertRaises(json.JSONDecodeError):json.loads('{"x":')
 def test_manifest_detects_same_size_corruption(self):
  with tempfile.TemporaryDirectory(prefix="sci_md_002c_") as d:
   b=Path(d);p=b/"case_records/X.json";rec={"case_id":"X","bundle_uuid":"u","result":{"v":1}};rec["record_sha256"]=M.internal_hash(rec);h,n=M.durable_write(p,rec)
   rows=[{"case_id":"X","path":"case_records/X.json","size":n,"sha256":h}];man={"record_count":1,"records":rows,"ordered_record_aggregate_sha256":M.hash_obj([{"case_id":"X","size":n,"sha256":h}])};M.durable_write(b/"manifest.json",man)
   self.assertEqual(M.verify_bundle(b,expected_ids=["X"])["record_count"],1);data=bytearray(p.read_bytes());data[data.index(b'1')]=ord('2');p.write_bytes(data)
   with self.assertRaisesRegex(ValueError,"FULL_RECORD_HASH_FAILURE"):M.verify_bundle(b,expected_ids=["X"])
 def test_safe_path_rejects_git_and_symlink(self):
  with self.assertRaises(ValueError):M.safe_bundle(ROOT/"SCI_MD_002C_EXTERNAL_BUNDLE")
  with tempfile.TemporaryDirectory(prefix="sci_md_002c_") as d:
   target=Path(d)/"target";target.mkdir();link=Path(d)/"link";link.symlink_to(target,target_is_directory=True)
   with self.assertRaises(ValueError):M.safe_bundle(link)

class TestReductionRules(unittest.TestCase):
 def test_ordering_uncertainty(self):
  self.assertEqual(M.ordering(3,2,.1,.1),"PASS");self.assertEqual(M.ordering(-1,2,.1,.1),"REJECTED");self.assertEqual(M.ordering(.05,2,.1,.1),"NUMERICALLY_UNRESOLVED")
 def test_temporal_signature_complete(self):
  row=next(x for x in M.matrix_rows() if x["case_id"]=="C0-SOURCE-P5-NOFINES");z=M.simulate(row);self.assertTrue(M.temporal_ok(z,row))
  bad=json.loads(json.dumps(z));bad["temporal"][2]["mass_residual_kg"]=1;self.assertFalse(M.temporal_ok(bad,row))
 def test_gate_precedence_and_aggregate_last_are_encoded(self):
  gates=M.protocol()["gates"];self.assertEqual(gates[-1],"AGGREGATE_COMPARISON");self.assertLess(gates.index("RESISTANCE_DIRECTION"),gates.index("PRESSURE_ORDERING"));self.assertLess(gates.index("PRESSURE_ORDERING"),gates.index("TEMPORAL_FINES_DEPOSITION_SIGNATURE"))
 def test_claim_and_dependence_taxonomy(self):
  p=M.protocol();self.assertIn("SCI_MD_002C_CAPABILITY_DEPENDS_ON_FULL_RETENTION_COMPACT_LAYER",p["dispositions"]);self.assertIn("GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED",p["claim_boundary"]);self.assertNotIn("FINES_SELECTED",json.dumps(p))

if __name__=="__main__":unittest.main()
