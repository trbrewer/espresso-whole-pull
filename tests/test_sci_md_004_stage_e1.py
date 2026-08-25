from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation/sci_md_004_stage_e1"


class StageE1BlockedContractTest(unittest.TestCase):
    def test_prediction_tool_has_no_target_or_scorer_interface(self) -> None:
        source = (ROOT / "tools/sci_md_004_stage_e1/materialize.py").read_text()
        self.assertNotIn('add_argument("--target', source)
        self.assertNotIn("import score", source)
        self.assertNotIn("subprocess.run", source)

    def test_exact_blocked_disposition_and_zero_execution(self) -> None:
        result = json.loads((OUTPUT / "FINAL_SCIENTIFIC_RESULT.json").read_text())
        self.assertEqual(
            result["primary_scientific_result"],
            "SCI_MD_004_STAGE_E1_EXECUTION_CONTRACT_BLOCKED_BEFORE_TARGET_ACCESS",
        )
        self.assertEqual(result["prediction_execution_count"], 0)
        self.assertEqual(result["protected_scorer_process_count"], 0)
        self.assertEqual(result["semantic_protected_target_access_count"], 0)

    def test_all_264_intents_fail_for_same_structural_reason(self) -> None:
        manifest = json.loads((OUTPUT / "MATERIALIZED_CASE_MANIFEST.json").read_text())
        intents = manifest["configuration_intents"]
        self.assertEqual(len(intents), 264)
        self.assertEqual(len({item["configuration_id"] for item in intents}), 264)
        self.assertEqual(
            {item["materialization_status"] for item in intents},
            {"BLOCKED_UNREPRESENTABLE_HYDRAULIC_CONTROL"},
        )
        self.assertEqual(manifest["complete_executable_scenario_count"], 0)
        self.assertFalse(manifest["capabilities"]["prescribed_outlet_flow_control"])

    def test_no_predictions_or_results_were_serialized(self) -> None:
        for name in ("PREDICTIONS.csv", "NUMERICAL_STABILITY.csv", "CONDITION_LEVEL_RESULTS.csv"):
            with (OUTPUT / name).open(newline="", encoding="utf-8") as stream:
                self.assertEqual(list(csv.DictReader(stream)), [])
        receipt = json.loads((OUTPUT / "SCORER_INVOCATION_RECEIPT.json").read_text())
        self.assertEqual(receipt["scorer_process_count"], 0)
        self.assertEqual(receipt["protected_target_scorer_open_count"], 0)
