import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "validation/cases/sci_lc_001a"


class CleanPathStatusTests(unittest.TestCase):
    def setUp(self):
        self.ledger = json.loads((CASE / "EXECUTION_ATTEMPT_LEDGER.json").read_text())
        self.status = json.loads((CASE / "SCI_LC_001A_CURRENT_STATUS.json").read_text())

    def test_unique_record_ids_and_ordinals(self):
        records = self.ledger["attempts"]
        self.assertEqual(len(records), len({r["record_id"] for r in records}))
        ordinals = [r["attempt_ordinal"] for r in records if isinstance(r["attempt_ordinal"], int)]
        self.assertEqual(ordinals, [1, 2, 3])

    def test_e4_count_arithmetic_and_quarantine(self):
        for record in self.ledger["attempts"]:
            if record["record_id"].startswith("E4-ATTEMPT-"):
                self.assertEqual(record["planned_keys"], record["dispatched_keys"] + record["unattempted_keys"])
                self.assertFalse(record["canonical_eligibility"])
                self.assertFalse(record["reuse_permission"])
                self.assertFalse(record["resume_permission"])

    def test_attempt_04_reserved_not_consumed_and_no_attempt_05(self):
        reservation = self.ledger["reserved_attempts"]
        self.assertEqual(len(reservation), 1)
        self.assertEqual(reservation[0]["attempt_ordinal"], 4)
        self.assertFalse(reservation[0]["consumed"])
        self.assertEqual(reservation[0]["canonical_keys_dispatched"], 0)
        self.assertEqual(self.ledger["attempt_budget"]["attempt_05_authority"], "NONE")

    def test_status_matches_canonical_result(self):
        result = self.ledger["canonical_result"]
        self.assertEqual(self.status["canonical_execution_count"], result["execution_count"])
        self.assertEqual(self.status["canonical_classification_count"], result["classification_count"])
        self.assertFalse(self.status["launch_authorized"])
        self.assertFalse(self.status["classification_authorized"])

    def test_matrix_identity(self):
        matrix = self.ledger["canonical_matrix"]
        self.assertEqual(matrix["rows"], 1280)
        self.assertEqual(matrix["static_keys"] + matrix["dynamic_keys"], 3666)
        self.assertEqual(matrix["semantic_sha256"], "4bb979181a0e5c672b896c44e3eee9574e28f0abed1d1f5dc227a47214e21717")


if __name__ == "__main__":
    unittest.main()
