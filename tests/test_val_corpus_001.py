import json
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


if __name__ == "__main__":
    unittest.main()
