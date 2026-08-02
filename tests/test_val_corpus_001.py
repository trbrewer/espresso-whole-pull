import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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


if __name__ == "__main__":
    unittest.main()
