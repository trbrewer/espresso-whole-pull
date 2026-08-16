import copy, hashlib, importlib.util, json, math, pathlib, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];SPEC=importlib.util.spec_from_file_location("md2b",ROOT/"scripts/sci_md_002b.py");md=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=md;SPEC.loader.exec_module(md)

class CorrectedPackage(unittest.TestCase):
 def test_histories_full_and_terminal(self):
  h=md.load_histories();self.assertEqual({p:len(h[p]) for p in md.PRESSURES},{5:999,9:999,11:999})
  for p in md.PRESSURES:self.assertAlmostEqual(h[p][-1]["pressure_pa"],md.TERMINAL_PRESSURES[p],7);self.assertEqual(h[p][-1]["source_time_s"],99.8999)
 def test_constant_pressure_closed_form(self):
  rows=md.nominal_rows(9,10);I=md.cumulative_integral(rows)[-1];k=2e-15
  self.assertAlmostEqual(md.front_from_integral(I,k),math.sqrt(2*k*(9e5+md.PCAP)*10/(md.MU*md.PHI_WET)),14)
 def test_numerical_history_integral_and_inverse(self):
  rows=[{"source_time_s":0.,"pressure_pa":1.},{"source_time_s":2.,"pressure_pa":3.}]
  I=md.cumulative_integral(rows,pcap=0);self.assertEqual(I,[0.,4.]);self.assertAlmostEqual(md.invert_integral(rows,I,1.5,pcap=0),1.)
 def test_overlay_hash_and_mutation_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/"o.json";p.write_bytes(md.OVERLAY.read_bytes())
   with self.assertRaises(ValueError):md.load_histories(p,"0"*64)
   x=json.loads(p.read_text());x["overlays"]["R1-WASZ-5-DARCY-STATIC-MEASURED"][4][0]=999;p.write_text(json.dumps(x))
   with self.assertRaises(ValueError):md.load_histories(p,md.sha(p))
 def test_phi_wet_epsilon_separate(self):
  self.assertNotEqual(md.PHI_WET,md.EPSILON_B0);p=md.protocol()["porosities"]
  self.assertIn("NOT_EWP_SOURCE_MEASUREMENT",p["phi_wet"]["provenance"]);self.assertIn("NOT_EWP_SOURCE_MEASUREMENT",p["epsilon_b0"]["provenance"])
  rows=md.load_histories()[9];k=md.hydraulic_anchor();self.assertNotEqual(md.wetting_times(rows,k,4,.2),md.wetting_times(rows,k,4,.3))
 def test_volume_bookkeeping_independent(self):
  F,dr,ac=1.05,1.02,.5;s=md.state(F,dr,ac,.001);bulk=md.AREA*.001*(1+ac*(F-1));solid=(1-md.EPSILON_B0)*md.AREA*.001*F
  self.assertAlmostEqual(s["bulk_volume_m3"],bulk);self.assertAlmostEqual(s["swollen_solid_volume_m3"],solid);self.assertAlmostEqual(s["pore_volume_m3"],bulk-solid);self.assertAlmostEqual(s["porosity"],(bulk-solid)/bulk)
 def test_nonzero_storage_and_one_way_status(self):
  row=next(x for x in md.matrix_rows() if x["case_id"]==md.PILOT_IDS[5]);r=md.simulate(row)
  self.assertGreater(r["terminal_swelling_storage_m3"],0);self.assertEqual(r["liquid_feedback_status"],"ONE_WAY_LIQUID_FEEDBACK_NOT_CLOSED_BY_DESIGN");self.assertEqual(r["whole_liquid_conservation"],"NOT_CLAIMED_ONE_WAY_FEEDBACK_UNCLOSED")
 def test_temporal_complete_deterministic(self):
  row=next(x for x in md.matrix_rows() if x["case_id"]=="C0-SOURCE-P5-NOSWELL");a=md.simulate(row);b=md.simulate(row);self.assertEqual(md.canonical(a),md.canonical(b));self.assertEqual(len(a["temporal"]),999)
  self.assertTrue(set(md.protocol()["temporal_output"]["fields"])<=set(a["temporal"][0]))
 def test_no_inactive_axes(self):
  rows=md.matrix_rows();a=next(x for x in rows if x["case_id"]==md.PILOT_IDS[3]);b=next(x for x in rows if x["case_id"]==md.PILOT_IDS[4]);ra=md.simulate(a);rb=md.simulate(b);self.assertNotEqual(ra["terminal_resistance_ratio"],rb["terminal_resistance_ratio"]);self.assertNotIn("dt_s",a)
 def test_synthetic_accommodation_controls_have_explicit_pressure_fixture(self):
  row=next(x for x in md.matrix_rows() if x["case_id"]=="A0-ACCOM-FIXED-E");result=md.simulate(row)
  self.assertEqual(result["terminal_pressure_pa"],9e5);self.assertEqual(result["status"],"COMPLETE")
 def test_matrix_exact_refinement_coverage(self):
  rows=md.matrix_rows();ids={x["case_id"] for x in rows};self.assertEqual(len(rows),456);self.assertLessEqual(len(rows),2500)
  for x in rows:
   if x["arm"]=="S1":self.assertIn(x["numerical_companion_id"],ids);self.assertIn(x["control_id"],ids);self.assertEqual(len(x["cross_pressure_peer_ids"]),2);self.assertTrue(x["assumption_peer_ids"])
 def test_margin_classes(self):
  self.assertEqual(md.margin_class(2,1,.1,.1),"PASS");self.assertEqual(md.margin_class(-1,1,.1,.1),"REJECTED");self.assertEqual(md.margin_class(.05,1,.1,.1),"NUMERICALLY_UNRESOLVED")
 def test_resistance_temporal_assumption_gate_order(self):
  g=md.protocol()["gates"];self.assertLess(g.index("RESISTANCE_DIRECTION"),g.index("PRESSURE_ORDERING"));self.assertLess(g.index("TEMPORAL_SIGNATURE"),g.index("ASSUMPTION_DEPENDENCE"));self.assertEqual(g[-1],"AGGREGATE_COMPARISON")
 def test_s2_block(self):
  x=next(x for x in md.matrix_rows() if x["arm"]=="S2");self.assertEqual(md.simulate(x)["stop_reason"],"SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED")
 def authority(self,path,ids,**changes):
  a=md.expected_authority(ids,path);a.update(owner_role="HUMAN_REPOSITORY_OWNER",authorization_date="2099-01-01T00:00:00Z");a.update(changes);p=path/"authority.json";p.write_text(md.canonical(a));return p
 def test_valid_authority_and_stale_broadened_rejection(self):
  with tempfile.TemporaryDirectory(prefix="SCI_MD_002B_") as d:
   b=pathlib.Path(d);cid=next(x["case_id"] for x in md.matrix_rows() if x["arm"]=="S1");p=self.authority(b,[cid]);self.assertEqual(md.validate_authority(p,b)[0]["authorized_row_ids"],[cid])
   q=self.authority(b,[cid],source_head="0"*40);self.assertRaises(PermissionError,md.validate_authority,q,b)
   q=self.authority(b,[md.PILOT_IDS[0]]);self.assertRaises(PermissionError,md.validate_authority,q,b)
 def test_authorized_row_restriction_and_no_authority(self):
  with tempfile.TemporaryDirectory(prefix="SCI_MD_002B_") as d:
   b=pathlib.Path(d);cid=next(x["case_id"] for x in md.matrix_rows() if x["arm"]=="S1");p=self.authority(b,[cid]);m=md.execute_authorized(b,p);self.assertEqual(m["authorized_row_ids"],[cid])
  with self.assertRaises(PermissionError):md.execute_adjudicative("/tmp/SCI_MD_002B_none",None)
 def test_immutable_and_exact_resume(self):
  with tempfile.TemporaryDirectory(prefix="SCI_MD_002B_") as d:
   b=pathlib.Path(d);rec={"case_id":"X","authority_sha256":"A"};md.atomic_record(b,"X",rec)
   with self.assertRaises(FileExistsError):md.atomic_record(b,"X",rec)
   self.assertEqual(md.atomic_record(b,"X",rec,True)[1],"EXACT_RESUME_VERIFIED")
   bad={"case_id":"X","authority_sha256":"B"};self.assertRaises(FileExistsError,md.atomic_record,b,"X",bad,True)
 def synthetic_bundle(self,kind):
  td=tempfile.TemporaryDirectory(prefix="SCI_MD_002B_");b=pathlib.Path(td.name);rows=md.matrix_rows();selected=[x for x in rows if x["arm"]=="C0"]
  selected += [x for x in rows if x["arm"]=="S1" and x["powder"]=="E" and x["D_multiplier"]==.5 and x["cmax"]==.05 and x["accommodation"]==0]
  ids=[x["case_id"] for x in selected];ap=self.authority(b,ids);ah=md.sha(ap)
  for x in selected:
   p=int(x["pressure_condition"].split("P")[1]);control=x["arm"]=="C0";q={5:3.,9:2.,11:1.}[p] if kind in ("pass","unresolved") else {5:1.,9:2.,11:3.}[p]
   if kind=="unresolved" and x["resolution"]=="REFINED":q={5:2.,9:2.,11:1.}[p]
   result={"status":"COMPLETE","terminal_outlet_flow_kg_s":q,"terminal_resistance_ratio":1. if control else 2.,"terminal_swelling_storage_m3":0. if control else 1e-9,"resistance_growth_onset_s":None if control else 1.,"liquid_feedback_status":"ONE_WAY_LIQUID_FEEDBACK_NOT_CLOSED_BY_DESIGN"}
   status="PHYSICAL_INVALID" if kind=="early" and x["case_id"]==ids[-1] else "COMPLETE";rec={"schema_version":md.RECORD_SCHEMA,"task_id":md.TASK,"lane_id":md.LANE_ID,"case_id":x["case_id"],"source_head":md.git("rev-parse","HEAD"),"source_tree":md.git("rev-parse","HEAD^{tree}"),"authority_sha256":ah,"execution_status":status,"result":result};md.atomic_record(b/"case_records",x["case_id"],rec)
  md.manifest(b,ah,ids);return td,b,ap
 def test_synthetic_reducer_pass_wrong_unresolved_early(self):
  expected={"pass":"SCI_MD_002B_CAPABILITY_DEPENDS_ON_FIXED_HEIGHT_EXTREME","wrong":"SCI_MD_002B_REJECTED_WRONG_PRESSURE_ORDERING","unresolved":"SCI_MD_002B_PRESSURE_ORDERING_NUMERICALLY_UNRESOLVED","early":"SCI_MD_002B_NUMERICAL_EXECUTION_INVALID"}
  for kind,disp in expected.items():
   td,b,a=self.synthetic_bundle(kind)
   try:self.assertEqual(md.reduce_bundle(b,a)["disposition"],disp)
   finally:td.cleanup()
 def test_lane_and_dependency_boundaries(self):
  src=pathlib.Path(md.__file__).read_text().lower();self.assertNotIn("import sci_lc",src);d=json.loads(md.LANE.read_text());self.assertFalse(any("sci_lc" in x for x in d["owned_paths"]));self.assertNotIn("solver/**",d["owned_paths"])
 def test_no_absolute_paths(self):
  for p in (md.LANE,md.OUT/"SCI_MD_002B_PROTOCOL.json",md.OUT/"SCI_MD_002B_CASE_MATRIX.json"):self.assertNotIn("/home/",p.read_text())

if __name__=="__main__":unittest.main()
