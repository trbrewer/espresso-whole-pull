import copy, hashlib, importlib.util, json, math, pathlib, sys, tempfile, unittest
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[1];SPEC=importlib.util.spec_from_file_location("md2b",ROOT/"scripts/sci_md_002b.py");md=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=md;SPEC.loader.exec_module(md)

class CorrectedPackage(unittest.TestCase):
 def test_histories_full_and_terminal(self):
  h=md.load_histories();self.assertEqual({p:len(h[p]) for p in md.PRESSURES},{5:999,9:999,11:999})
  for p in md.PRESSURES:
   self.assertAlmostEqual(h[p][-1]["observed_pressure_pa"],md.TERMINAL_PRESSURES[p],7);self.assertAlmostEqual(h[p][-1]["reference_model_pressure_pa"],md.TERMINAL_REFERENCE_PRESSURES[p],7);self.assertAlmostEqual(h[p][-1]["observed_flow_kg_s"],md.TERMINAL_OBSERVED_FLOWS[p],12);self.assertEqual(h[p][-1]["source_time_s"],99.8999)
  self.assertFalse(any("nominal" in k or k.startswith("model_") or k.startswith("source_") and k!="source_time_s" for k in h[9][-1]))
 def test_observed_p9_flow_is_hydraulic_anchor(self):
  r=md.load_histories()[9][-1];expected=(r["observed_flow_kg_s"]/md.RHO)*md.MU*md.H0/(md.AREA*r["observed_pressure_pa"]);self.assertEqual(md.hydraulic_anchor(),expected);self.assertNotEqual(r["observed_flow_kg_s"],r["reference_model_flow_kg_s"])
 def test_constant_pressure_closed_form(self):
  rows=md.nominal_rows(9,10);I=md.cumulative_integral(rows)[-1];k=2e-15
  self.assertAlmostEqual(md.front_from_integral(I,k),math.sqrt(2*k*(9e5+md.PCAP)*10/(md.MU*md.PHI_WET)),14)
 def test_numerical_history_integral_and_inverse(self):
  rows=[{"source_time_s":0.,"observed_pressure_pa":1.},{"source_time_s":2.,"observed_pressure_pa":3.}]
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
 def test_full_temporal_signature_gate(self):
  row=next(x for x in md.matrix_rows() if x["case_id"]==md.PILOT_IDS[5]);result=md.simulate(row);self.assertEqual(md.temporal_signature(result,row),(True,"PASS"))
  bad=copy.deepcopy(result);bad["temporal"][10]["pressure_pa"]+=1;self.assertEqual(md.temporal_signature(bad,row)[1],"SOURCE_HISTORY_MISMATCH")
 def test_no_inactive_axes(self):
  rows=md.matrix_rows();a=next(x for x in rows if x["case_id"]==md.PILOT_IDS[3]);b=next(x for x in rows if x["case_id"]==md.PILOT_IDS[4]);ra=md.simulate(a);rb=md.simulate(b);self.assertNotEqual(ra["terminal_resistance_ratio"],rb["terminal_resistance_ratio"]);self.assertNotIn("dt_s",a)
 def test_synthetic_accommodation_controls_have_explicit_pressure_fixture(self):
  row=next(x for x in md.matrix_rows() if x["case_id"]=="A0-ACCOM-FIXED-E");result=md.simulate(row)
  self.assertEqual(result["terminal_pressure_pa"],9e5);self.assertEqual(result["status"],"COMPLETE")
 def test_pilot_ledger_records_matching_start_and_completion(self):
  with tempfile.TemporaryDirectory(prefix="SCI_MD_002B_attempt_fixture_") as d:
   b=pathlib.Path(d)/"attempt_fixture";md.pilot_run(b);entries=[json.loads(x) for x in (b/"process_ledger.jsonl").read_text().splitlines()]
   self.assertEqual([x["status"] for x in entries],["RUNNING","COMPLETE"]);self.assertTrue(all(x["pilot_identity"]=="attempt_fixture" for x in entries))
 def test_matrix_exact_refinement_coverage(self):
  rows=md.matrix_rows();ids={x["case_id"] for x in rows};self.assertEqual(len(rows),456);self.assertLessEqual(len(rows),2500)
  for x in rows:
   if x["arm"]=="S1":self.assertIn(x["numerical_companion_id"],ids);self.assertIn(x["control_id"],ids);self.assertEqual(len(x["cross_pressure_peer_ids"]),2);self.assertTrue(x["assumption_peer_ids"])
  self.assertEqual(len(md.adjudicative_row_ids()),435);self.assertEqual(sum(x.startswith("S1-") for x in md.adjudicative_row_ids()),432);self.assertEqual(sum(x.startswith("C0-") for x in md.adjudicative_row_ids()),3)
 def test_margin_classes(self):
  self.assertEqual(md.margin_class(2,1,.1,.1),"PASS");self.assertEqual(md.margin_class(-1,1,.1,.1),"REJECTED");self.assertEqual(md.margin_class(.05,1,.1,.1),"NUMERICALLY_UNRESOLVED")
 def test_resistance_temporal_assumption_gate_order(self):
  g=md.protocol()["gates"];self.assertLess(g.index("RESISTANCE_DIRECTION"),g.index("PRESSURE_ORDERING"));self.assertLess(g.index("TEMPORAL_SIGNATURE"),g.index("ASSUMPTION_DEPENDENCE"));self.assertEqual(g[-1],"AGGREGATE_COMPARISON")
 def test_s2_block(self):
  x=next(x for x in md.matrix_rows() if x["arm"]=="S2");self.assertEqual(md.simulate(x)["stop_reason"],"SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED")
 def authority(self,path,ids=None,**changes):
  a=md.expected_authority_bindings(path);a.update(authorization_token=md.TOKEN,owner_role="HUMAN_REPOSITORY_OWNER",authorization_date="2099-01-01T00:00:00Z")
  if ids is not None:a["authorized_row_ids"]=ids
  a.update(changes);p=path/"authority.json";p.write_text(md.canonical(a));return p
 def test_exact_cohort_authority_and_partial_rejection(self):
  with tempfile.TemporaryDirectory(prefix="SCI_MD_002B_") as d:
   b=pathlib.Path(d);ids=md.adjudicative_row_ids();p=self.authority(b);self.assertEqual(md.validate_authority(p,b)[0]["authorized_row_ids"],ids)
   rows=md.matrix_rows();first=next(x for x in rows if x["arm"]=="S1");stem=(first["powder"],first["D_multiplier"],first["cmax"],first["accommodation"]);one_candidate=sorted([x["case_id"] for x in rows if x["arm"]=="C0" or x["arm"]=="S1" and (x["powder"],x["D_multiplier"],x["cmax"],x["accommodation"])==stem])
   for bad in ([ids[3]],one_candidate,ids[:-1],ids+[md.PILOT_IDS[0]],list(reversed(ids))):
    q=self.authority(b,bad);self.assertRaises(PermissionError,md.validate_authority,q,b)
   q=self.authority(b,source_head="0"*40);self.assertRaises(PermissionError,md.validate_authority,q,b)
 def test_production_bindings_cannot_mint_owner_authority(self):
  a=md.expected_authority_bindings(pathlib.Path("/tmp/SCI_MD_002B_fixture"));self.assertFalse({"authorization_token","owner_role","authorization_date"}&set(a))
 def test_no_authority_refused(self):
  with self.assertRaises(PermissionError):md.execute_adjudicative("/tmp/SCI_MD_002B_none",None)
 def test_immutable_and_exact_resume(self):
  with tempfile.TemporaryDirectory(prefix="SCI_MD_002B_") as d:
   b=pathlib.Path(d);rec={"case_id":"X","authority_sha256":"A"};md.atomic_record(b,"X",rec)
   with self.assertRaises(FileExistsError):md.atomic_record(b,"X",rec)
   self.assertEqual(md.atomic_record(b,"X",rec,True)[1],"EXACT_RESUME_VERIFIED")
   bad={"case_id":"X","authority_sha256":"B"};self.assertRaises(FileExistsError,md.atomic_record,b,"X",bad,True)
 def synthetic_bundle(self,survivor_count=1,temporal_fail_first=False,physical_first=False,single_accommodation=True):
  td=tempfile.TemporaryDirectory(prefix="SCI_MD_002B_");b=pathlib.Path(td.name);rows={x["case_id"]:x for x in md.matrix_rows()};ids=md.adjudicative_row_ids();ap=self.authority(b);ah=md.sha(ap);stems=[]
  for x in rows.values():
   if x["arm"]=="S1" and x["resolution"]=="BASE" and x["pressure_condition"]=="SOURCE_P5":stems.append((x["powder"],x["D_multiplier"],x["cmax"],x["accommodation"]))
  chosen=[]
  for stem in stems:
   if len(chosen)<survivor_count and (not single_accommodation or stem[3]==0):chosen.append(stem)
  for cid in ids:
   x=rows[cid];control=x["arm"]=="C0";p=int(x["pressure_condition"].split("P")[1]);stem=(x["powder"],x["D_multiplier"],x["cmax"],x["accommodation"]);survive=stem in chosen
   q={5:.003,9:.002,11:.001}[p] if survive else {5:.001,9:.002,11:.003}[p];resistance=1. if control else (2. if survive else .5)
   result={"status":"COMPLETE","terminal_outlet_flow_kg_s":q,"terminal_resistance_ratio":resistance,"terminal_swelling_storage_m3":0. if control else 1e-9,"resistance_growth_onset_s":None if control else 1.,"liquid_feedback_status":"ONE_WAY_LIQUID_FEEDBACK_NOT_CLOSED_BY_DESIGN"}
   status="PHYSICAL_INVALID" if physical_first and not control and stem==stems[0] else "COMPLETE";rec={"schema_version":md.RECORD_SCHEMA,"task_id":md.TASK,"lane_id":md.LANE_ID,"case_id":cid,"source_head":md.git("rev-parse","HEAD"),"source_tree":md.git("rev-parse","HEAD^{tree}"),"authority_sha256":ah,"execution_status":status,"result":result};md.atomic_record(b/"case_records",cid,rec)
  md.manifest(b,ah,ids);return td,b,ap,chosen
 def test_missing_record_and_zero_candidates_fail_package_validity(self):
  td,b,a,_=self.synthetic_bundle()
  try:
   (b/"case_records"/f"{md.adjudicative_row_ids()[-1]}.json").unlink()
   with self.assertRaises(ValueError):md.reduce_bundle(b,a)
  finally:td.cleanup()
 def test_candidate_gate_failures_do_not_globally_veto_survivor(self):
  td,b,a,chosen=self.synthetic_bundle(2)
  calls={}
  def temporal(result,row,histories=None,tol=1e-10):
   stem=(row["powder"],row["D_multiplier"],row["cmax"],row["accommodation"]);calls[stem]=calls.get(stem,0)+1;return (stem!=chosen[0],"SYNTHETIC_TEMPORAL_FAIL" if stem==chosen[0] else "PASS")
  try:
   with mock.patch.object(md,"temporal_signature",side_effect=temporal):result=md.reduce_bundle(b,a)
   self.assertEqual(result["candidate_count"],72);self.assertTrue(any(x["aggregate_comparison_eligible"] for x in result["candidates"]));self.assertTrue(any(x["first_failed_gate"]=="TEMPORAL_SIGNATURE" for x in result["candidates"]));self.assertNotEqual(result["disposition"],"SCI_MD_002B_REJECTED_WRONG_RESISTANCE_DIRECTION")
  finally:td.cleanup()
 def test_physical_candidate_invalidity_distinct_and_observed_aggregate(self):
  td,b,a,_=self.synthetic_bundle(2,physical_first=True)
  try:
   with mock.patch.object(md,"temporal_signature",return_value=(True,"PASS")):result=md.reduce_bundle(b,a)
   survivor=next(x for x in result["candidates"] if x["aggregate_comparison_eligible"]);expected=math.sqrt(sum((q-md.TERMINAL_OBSERVED_FLOWS[p])**2 for p,q in {5:.003,9:.002,11:.001}.items())/3)
   self.assertAlmostEqual(survivor["terminal_flow_rmse_kg_s"],expected);self.assertEqual(result["candidate_count"],72);self.assertIn("observed_flow_kg_s",result["aggregate_target"]);self.assertIn("reference_model_flow_kg_s prohibited",result["aggregate_target"]);self.assertTrue(any(x["first_failed_gate"]=="NUMERICAL_OR_PHYSICAL_VALIDITY" for x in result["candidates"]));self.assertTrue(any(x["aggregate_comparison_eligible"] for x in result["candidates"]))
  finally:td.cleanup()
 def test_single_accommodation_is_not_promoted(self):
  td,b,a,_=self.synthetic_bundle(2,single_accommodation=True)
  try:
   with mock.patch.object(md,"temporal_signature",return_value=(True,"PASS")):result=md.reduce_bundle(b,a)
   self.assertNotEqual(result["disposition"],"SCI_MD_002B_WETTING_AGE_SWELLING_CAPABILITY_SURVIVES_BOUNDED_SCREEN");self.assertEqual(result["assumption_dependence"]["passing_accommodation_values"],[0.])
  finally:td.cleanup()
 def test_lane_and_dependency_boundaries(self):
  src=pathlib.Path(md.__file__).read_text().lower();self.assertNotIn("import sci_lc",src);d=json.loads(md.LANE.read_text());self.assertFalse(any("sci_lc" in x for x in d["owned_paths"]));self.assertNotIn("solver/**",d["owned_paths"])
 def test_no_absolute_paths(self):
  for p in (md.LANE,md.OUT/"SCI_MD_002B_PROTOCOL.json",md.OUT/"SCI_MD_002B_CASE_MATRIX.json"):self.assertNotIn("/home/",p.read_text())

if __name__=="__main__":unittest.main()
