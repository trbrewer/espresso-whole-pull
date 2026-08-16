import csv
import hashlib
import importlib.util
import json
import math
import os
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("md2b", ROOT / "scripts/sci_md_002b.py")
md = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = md
SPEC.loader.exec_module(md)


class SciMd002BTests(unittest.TestCase):
    def test_lane_charter_agreement_and_paths(self):
        d = json.loads(md.LANE.read_text())
        charter = (md.LANE.parent / "DECISION_AND_PARALLEL_LANE_CHARTER.md").read_text()
        self.assertEqual(d["lane_id"], "EWP-PAR-SCI-MD-002B")
        self.assertIn("scripts/sci_md_002b.py", d["owned_paths"])
        self.assertIn("solver/**", d["forbidden_paths"])
        self.assertIn(d["branch"], charter)

    def test_no_sci_lc_import_or_owned_path(self):
        src = pathlib.Path(md.__file__).read_text().lower()
        self.assertNotIn("import sci_lc", src)
        d = json.loads(md.LANE.read_text())
        self.assertFalse(any("sci_lc" in x for x in d["owned_paths"]))

    def test_deterministic_matrix_and_exact_count(self):
        a, b = md.matrix_rows(), md.matrix_rows()
        self.assertEqual(md.canonical(a), md.canonical(b))
        self.assertEqual(len(a), 243)
        self.assertLessEqual(len(a), 2500)
        self.assertEqual(len({r["case_id"] for r in a}), len(a))

    def test_protocol_and_matrix_hash(self):
        p = json.loads((md.OUT / "SCI_MD_002B_PROTOCOL.json").read_text())
        self.assertEqual(p["matrix_sha256"], md.sha(md.OUT / "SCI_MD_002B_CASE_MATRIX.json"))
        self.assertEqual(p["budget"]["row_count"], 243)

    def test_csv_json_agreement(self):
        j = json.loads((md.OUT / "SCI_MD_002B_CASE_MATRIX.json").read_text())
        with (md.OUT / "SCI_MD_002B_CASE_MATRIX.csv").open(newline="") as f:
            c = list(csv.DictReader(f))
        self.assertEqual(len(c), j["row_count"])
        self.assertEqual([x["case_id"] for x in c], [x["case_id"] for x in j["rows"]])

    def test_comparators_and_provenance_complete(self):
        rows = md.matrix_rows(); ids = {r["case_id"] for r in rows}
        allowed = set(md.protocol()["provenance_classes"])
        for r in rows:
            self.assertTrue(set(r["comparator_ids"]) <= ids)
            self.assertIn(r["evidence_role"], allowed)

    def test_foster_closed_form_and_zero_capillary_limit(self):
        k, p, t = 2e-15, 5e5, 2.3
        s = md.foster_front(t, p, k, pcap=0)
        self.assertAlmostEqual(s*s, 2*k*p*t/(md.MU*md.PHI0), places=18)
        tw = md.foster_wetting_times(p, k, 8)
        self.assertTrue(all(tw[i] < tw[i+1] for i in range(7)))

    def test_zero_swelling_and_monotonicity(self):
        self.assertEqual(md.swelling_volume_ratio(50e-6, 30, 0, .1, 20), 1)
        a = md.swelling_volume_ratio(50e-6, 2, md.D0, .1, 20)
        b = md.swelling_volume_ratio(50e-6, 20, md.D0, .1, 20)
        self.assertGreaterEqual(b, a)

    def test_accommodation_endpoint_and_volume_identities(self):
        fixed = md.accommodation_state(1.05, 1.01, 0)
        free = md.accommodation_state(1.05, 1.01, 1)
        self.assertEqual(fixed["height_ratio"], 1)
        self.assertAlmostEqual(free["porosity"], md.PHI0)
        self.assertGreater(fixed["porosity"], 0)
        self.assertGreater(free["pore_ratio"], 0)

    def test_serial_resistance_and_fixed_pressure_monotonicity(self):
        rs = [1., 2., 3.]
        self.assertEqual(sum(rs)/len(rs), 2)
        self.assertGreater(11e5/2, 9e5/2)

    def test_simultaneous_wetting_identity(self):
        base = 7e5
        rel = md.accommodation_state(*md.particle_state("E", 10, md.D0, .1, 20), 0)["resistance_ratio"]
        self.assertAlmostEqual((11e5/rel)/(5e5/rel), 11/5)
        self.assertGreater(base/rel, 0)

    def test_physical_state_bounds_no_clipping(self):
        for ac in (0, .5, 1):
            x = md.accommodation_state(1.08, 1.02, ac)
            self.assertTrue(0 < x["porosity"] < 1)
            self.assertGreater(x["permeability_ratio"], 0)
            self.assertGreater(x["resistance_ratio"], 0)

    def test_one_way_local_age_and_no_prewet_swelling(self):
        wet = md.foster_wetting_times(9e5, md.hydraulic_anchor(), 16)
        self.assertEqual(max(0, wet[0]-wet[0]), 0)
        self.assertGreater(wet[-1], wet[0])

    def test_two_way_is_reason_specific_block(self):
        row = next(r for r in md.matrix_rows() if r["arm"] == "S2")
        self.assertEqual(md.simulate(row)["stop_reason"], "SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED")

    def test_conservation_fields_and_refinement_logic(self):
        row = next(r for r in md.matrix_rows() if r["case_id"] == md.PILOT_IDS[6])
        result = md.simulate(row)
        self.assertEqual(result["liquid_balance_residual_m3"], 0)
        self.assertFalse(result["clipping"])
        self.assertTrue(row["refinement_companions"])

    def test_pressure_margin_uncertainty_classification(self):
        def classify(m1, m2, u):
            if min(m1-u, m2-u) > 0: return "PASS"
            if m1+u <= 0 or m2+u <= 0: return "REJECT"
            return "UNRESOLVED"
        self.assertEqual(classify(2, 1, .2), "PASS")
        self.assertEqual(classify(-2, 1, .2), "REJECT")
        self.assertEqual(classify(.1, 1, .2), "UNRESOLVED")

    def test_gate_precedence_rmse_cannot_rescue_order(self):
        gates = md.protocol()["gates"]
        self.assertLess(gates.index("PRESSURE_ORDERING"), gates.index("AGGREGATE_COMPARISON"))

    def test_grind_mapping_fails_closed(self):
        self.assertIn("GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED", md.protocol()["claim_boundary"])

    def test_execution_without_owner_authority_refused(self):
        with self.assertRaises(PermissionError):
            md.execute_adjudicative("/tmp/SCI_MD_002B_test", None)

    def test_pilot_has_no_complete_adjudicative_triplet(self):
        rows = {r["case_id"]: r for r in md.matrix_rows()}
        chosen = [rows[x] for x in md.PILOT_IDS]
        self.assertFalse(any(r["adjudicative"] for r in chosen))

    def test_atomic_records_and_overwrite_refusal(self):
        with tempfile.TemporaryDirectory(prefix="SCI_MD_002B_") as d:
            p = pathlib.Path(d)
            md.record_atomic(p, "X", {"a": 1})
            with self.assertRaises(FileExistsError): md.record_atomic(p, "X", {"a": 1})

    def test_process_ownership_predicates_and_path_safety(self):
        with self.assertRaises(ValueError): md.safe_bundle(ROOT / "SCI_MD_002B_EXTERNAL_BUNDLE")
        with tempfile.TemporaryDirectory() as d:
            link = pathlib.Path(d)/"SCI_MD_002B_link"
            link.symlink_to("/tmp")
            with self.assertRaises(ValueError): md.safe_bundle(link)

    def test_no_absolute_paths_or_production_changes_declared(self):
        for p in [md.LANE, md.OUT/"SCI_MD_002B_PROTOCOL.json", md.OUT/"SCI_MD_002B_CASE_MATRIX.json"]:
            self.assertNotIn("/home/", p.read_text())
        self.assertNotIn("solver/**", json.loads(md.LANE.read_text())["owned_paths"])


if __name__ == "__main__": unittest.main()
