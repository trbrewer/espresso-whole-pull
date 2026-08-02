import json
import math
import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import val_corpus_001 as campaign


class ValCorpus001Test(unittest.TestCase):
    def test_protocol_is_prospective_and_bounded(self):
        p = json.loads((ROOT / "validation/cases/val_corpus_001/VAL_CORPUS_001_PROTOCOL.json").read_text())
        self.assertEqual(p["change_declaration"], "NO_GOVERNING_PHYSICS_CHANGE")
        self.assertEqual(p["planned_openfoam_run_count"], len(p["run_matrix"]))
        self.assertEqual(p["planned_score_bearing_invocation_count"], 1)
        self.assertEqual([x["pressure_bar"] for x in p["run_matrix"] if x["id"].endswith("-DARCY")], [5, 9, 11])
        self.assertEqual(p["claim_ceiling"]["PHYSICAL_VALIDATION"], "NOT_ESTABLISHED")

    def test_snapshot_and_visualizer_boundary(self):
        e = json.loads((ROOT / "validation/cases/val_corpus_001/VAL_CORPUS_001_EVIDENCE_SNAPSHOT.json").read_text())
        self.assertFalse(e["runtime_lock_advanced"])
        self.assertFalse(e["visualizer_harvest"]["performed"])
        self.assertEqual(e["visualizer_harvest"]["cohort"], ["de1_fixtureA"])
        self.assertEqual(len({x["sha256"] for x in e["files"]}), len(e["files"]))

    def test_review_correction_matrix_and_mapping(self):
        p = json.loads((ROOT / "validation/cases/val_corpus_001/VAL_CORPUS_001_REVIEW_CORRECTION_PROTOCOL.json").read_text())
        self.assertEqual(len(p["correction_matrix"]), 13)
        self.assertEqual(p["planned_new_openfoam_launches"], 13)
        self.assertEqual(p["mapping"]["source_density_kg_m3"], 965.0)
        self.assertEqual(p["mapping"]["solver_time_equals_source_time_plus_s"], 3.0)
        self.assertEqual(p["mapping"]["extrapolation"], "PROHIBITED")
        self.assertEqual(p["superseded"]["protocol_sha256"], "69c227c31300835b28f700386c86209e1b2a8c785ca9318d209d00b8324c6484")

    def test_linear_interpolation_fails_outside_domain(self):
        rows = [{"t":"0","v":"1"},{"t":"2","v":"5"}]
        self.assertEqual(campaign.linear_value(rows,"t","v",1.0),3.0)
        self.assertIsNone(campaign.linear_value(rows,"t","v",-0.1))
        self.assertIsNone(campaign.linear_value(rows,"t","v",2.1))

    def test_label_rules_are_not_code_only(self):
        p = json.loads((ROOT / "validation/cases/val_corpus_001/VAL_CORPUS_001_REVIEW_CORRECTION_PROTOCOL.json").read_text())
        self.assertEqual(set(p["label_rules"]), {"WORKING","PARTIAL","FAILING","DESCRIPTIVE_ONLY","INVALIDATED_EXECUTION"})

    def test_wrong_order_is_failing_rule(self):
        text = (ROOT / "scripts/val_corpus_001.py").read_text()
        self.assertIn('if wrong_order:', text)
        self.assertIn('label = "FAILING"', text)

    def test_metric_uses_exact_odd_and_even_medians(self):
        odd = campaign.metric([1.0, 1.0, 1.0], [1.0, math.e, math.exp(3.0)])
        even = campaign.metric([1.0, 1.0, 1.0, 1.0], [1.0, math.e, math.exp(3.0), math.exp(7.0)])
        self.assertAlmostEqual(odd["median_absolute_log_ratio"]["value"], 1.0)
        self.assertAlmostEqual(even["median_absolute_log_ratio"]["value"], 2.0)

    def test_metric_excludes_nonpositive_and_nonfinite_log_pairs(self):
        result = campaign.metric([1.0, 0.0, -1.0, math.inf], [math.e, 2.0, 3.0, 4.0])
        log = result["median_absolute_log_ratio"]
        self.assertEqual(log["eligible_sample_count"], 1)
        self.assertEqual(log["excluded_nonpositive_count"], 2)
        self.assertEqual(log["excluded_nonfinite_count"], 1)
        self.assertAlmostEqual(log["value"], 1.0)
        undefined = campaign.metric([0.0, math.nan], [1.0, 2.0])["median_absolute_log_ratio"]
        self.assertIsNone(undefined["value"])
        self.assertEqual(undefined["undefined_reason"], "NO_FINITE_STRICTLY_POSITIVE_PAIRS")

    def test_final_ordering_families_are_scenario_separated(self):
        result = json.loads((ROOT / "validation/cases/val_corpus_001/results/VAL_CORPUS_001_RESULT_BUNDLE_V3.json").read_text())
        measured = result["ordering_families"]["DARCY_STATIC|MEASURED_TERMINAL_BASKET_PRESSURE"]
        nominal = result["ordering_families"]["DARCY_STATIC|NOMINAL_PRESSURE"]
        self.assertTrue(all("MEASURED" in item and "NOMINAL" not in item for item in measured["ids"]))
        self.assertTrue(all("NOMINAL" in item and "MEASURED" not in item for item in nominal["ids"]))
        self.assertTrue(set(measured["ids"]).isdisjoint(nominal["ids"]))

    def test_each_final_row_ordering_matches_its_scenario(self):
        result = json.loads((ROOT / "validation/cases/val_corpus_001/results/VAL_CORPUS_001_RESULT_BUNDLE_V3.json").read_text())
        for row in result["r1_waszkiewicz_rows"]:
            family = result["ordering_families"][row["ordering_key"]]
            self.assertIn(row["id"], family["ids"])
            self.assertEqual(row["roles"]["pressure_node_scenario"], family["pressure_node_scenario"])

    def test_anchor_and_transfer_roles_are_precise(self):
        matrix = json.loads((ROOT / "validation/cases/val_corpus_001/VAL_CORPUS_001_REVIEW_CORRECTION_PROTOCOL.json").read_text())["correction_matrix"]
        roles = {item["id"]: campaign.precise_role(item) for item in matrix if item["id"].startswith("R1-WASZ")}
        self.assertEqual(roles["R1-WASZ-9-DARCY-STATIC-MEASURED"]["anchor_role"], "ANCHOR_CONDITION_RECONSTRUCTION")
        self.assertEqual(roles["R1-WASZ-9-DF-STATIC-MEASURED"]["anchor_role"], "ANCHOR_CONDITION_RECONSTRUCTION")
        self.assertEqual(roles["R1-WASZ-5-DARCY-STATIC-MEASURED"]["anchor_role"], "ONE_ANCHOR_TRANSFER")
        self.assertEqual(roles["R1-WASZ-11-DF-STATIC-MEASURED"]["anchor_role"], "ONE_ANCHOR_TRANSFER")

    def test_post_fit_dissolution_roles_are_precise(self):
        matrix = json.loads((ROOT / "validation/cases/val_corpus_001/VAL_CORPUS_001_REVIEW_CORRECTION_PROTOCOL.json").read_text())["correction_matrix"]
        roles = {item["id"]: campaign.precise_role(item) for item in matrix if "DISSOLUTION" in item["id"]}
        self.assertEqual(roles["R1-WASZ-9-DARCY-DISSOLUTION-MEASURED"]["anchor_role"], "POST_FIT_SOURCE_RECONSTRUCTION")
        self.assertEqual(roles["R1-WASZ-5-DARCY-DISSOLUTION-MEASURED"]["anchor_role"], "POST_FIT_CROSS_CONDITION_TRANSFER")
        self.assertEqual(roles["R1-WASZ-11-DARCY-DISSOLUTION-MEASURED"]["anchor_role"], "POST_FIT_CROSS_CONDITION_TRANSFER")

    def test_density_sensitivities_are_populated(self):
        result = json.loads((ROOT / "validation/cases/val_corpus_001/results/VAL_CORPUS_001_RESULT_BUNDLE_V3.json").read_text())
        densities = {row["density_kg_m3"] for row in result["density_flow_conversion_sensitivity"]}
        self.assertEqual(densities, {965.0, 997.0, 1000.0})
        for record in result["density_flow_conversion_sensitivity"]:
            self.assertEqual(len(record["conditions"]), 3)
            for condition in record["conditions"]:
                self.assertIsNotNone(condition["flow_rmse_g_s"])
                self.assertIn("value", condition["flow_median_absolute_log_ratio"])

    def test_final_double_reduction_is_byte_identical(self):
        record = json.loads((ROOT / "validation/cases/val_corpus_001/results/VAL_CORPUS_001_FINAL_REPRODUCIBILITY_RECORD.json").read_text())
        self.assertEqual(record["status"], "PASS_BYTE_IDENTICAL")
        for artifact in record["artifacts"].values():
            self.assertEqual(artifact["invocation_a_sha256"], artifact["invocation_b_sha256"])
            self.assertEqual(artifact["invocation_a_bytes"], artifact["invocation_b_bytes"])

    def test_fatal_traces_are_not_completed(self):
        ledger = json.loads((ROOT / "validation/cases/val_corpus_001/results/VAL_CORPUS_001_COMPLETE_EXECUTION_LEDGER.json").read_text())
        complete = {x["id"] for x in ledger["historical_completed_trace_identities"]}
        fatal = {x["id"] for x in ledger["historical_fatal_trace_identities"]}
        self.assertEqual(fatal, {"WASZ-5-COMPACT", "WASZ-9-COMPACT", "WASZ-11-COMPACT"})
        self.assertTrue(complete.isdisjoint(fatal))
        self.assertEqual(len(complete), 13)

    def test_v3_is_self_contained(self):
        result = json.loads((ROOT / "validation/cases/val_corpus_001/results/VAL_CORPUS_001_RESULT_BUNDLE_V3.json").read_text())
        self.assertEqual(result["composition"], "SELF_CONTAINED")
        self.assertEqual(len(result["original_results"]), 16)
        self.assertEqual(len(result["original_fatal_compaction"]), 3)
        self.assertEqual(len(result["historical_overlap_only"]), 6)
        self.assertEqual(len(result["r1_waszkiewicz_rows"]), 12)
        self.assertEqual(len(result["foster_shift_sensitivity"]), 3)
        self.assertEqual(len(result["de1_assumption_sensitivity"]), 3)
        self.assertEqual(len(result["wadsworth_roman_component_results"]), 2)
        self.assertEqual(len(result["mo_descriptive_results"]), 2)

    def test_package_qa_matches_source_manifest(self):
        qa = json.loads((ROOT / "PACKAGE_QA_STATUS.json").read_text())
        manifest = json.loads((ROOT / "SOURCE_PACKAGE_MANIFEST.json").read_text())
        checks = qa["current_repository_checks"]
        self.assertEqual(checks["source_manifest_file_count"], manifest["file_count"])
        self.assertEqual(checks["source_manifest_aggregate_sha256"], manifest["aggregate_source_sha256"])


if __name__ == "__main__":
    unittest.main()
