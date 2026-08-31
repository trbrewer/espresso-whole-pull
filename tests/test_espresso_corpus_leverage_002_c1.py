import json
import unittest
from pathlib import Path

from scripts.validate_local_data_corpus_authority import validate

ROOT = Path(__file__).resolve().parents[1]


class CorpusLeverageC1Tests(unittest.TestCase):
    def test_authority_and_coverage(self):
        self.assertEqual(validate()["unregistered_material_families"], 0)

    def test_priority_and_home_lab_gate(self):
        programme = json.loads((ROOT / "provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json").read_text())
        self.assertEqual(programme["current_priority"], "XSV-WASZKIEWICZ-DYNAMIC-HYD-001")
        self.assertEqual(programme["home_lab_status"], "DEFER_HOME_LAB_HIGHER_VALUE_EXISTING_DATA_TASKS_READY")
        self.assertFalse(programme["laboratory_gate"]["operation_authorized"])
        self.assertTrue(any(x["opportunity_id"] == "SCI-ED-003" and x["status"] == "DEFERRED_BY_HIGHER_VALUE_EXISTING_DATA_TASKS" for x in programme["opportunities"]))

    def test_no_production_source_change(self):
        changed = __import__("subprocess").check_output(["git", "diff", "--name-only", "36b68dc2670349738871ed2aad233357b1474123", "--", "src", "applications"], cwd=ROOT, text=True)
        self.assertEqual(changed, "")


if __name__ == "__main__":
    unittest.main()
