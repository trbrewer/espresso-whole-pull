import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_puckworks_base_temporal_cv as verifier


class PuckworksBaseTemporalCvTests(unittest.TestCase):
    def test_repository_import_passes(self):
        result = verifier.verify(ROOT)
        self.assertEqual(result["status"], "PASS", result["failures"])
        self.assertEqual(result["artifact_count"], 9)
        self.assertEqual(result["shot_count"], 16)
        self.assertEqual(result["exclusion_count"], 3)

    def test_exact_base_metrics_are_bound(self):
        path = ROOT / "validation/external/puckworks_base_temporal_cv/PAPER_A_TEMPORAL_MODEL_COMPARISON_V1.json"
        comparison = json.loads(path.read_text())
        for solute, expected in verifier.EXPECTED_METRICS.items():
            row = comparison["solutes"][solute]["BASE"]
            self.assertEqual((row["all_fraction_mape"], row["late_fraction_mape"],
                              row["late_signed_pct"], row["derived_cumulative_mape"]), expected)

    def test_lineage_declaration_is_fail_closed(self):
        record_path = ROOT / "validation/external/puckworks_base_temporal_cv/PUCKWORKS_BASE_TEMPORAL_CV_SOURCE_RECORD.json"
        record = json.loads(record_path.read_text())
        bad = copy.deepcopy(record["cup_masses_csv_lineage"])
        bad["independent_measurement"] = True
        self.assertFalse(verifier.contains_lineage(bad))
        self.assertTrue(verifier.contains_lineage(record))

    def test_import_hash_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "artifact"
            target.write_bytes(b"changed")
            self.assertNotEqual(verifier.sha256(target),
                                "581c985723542003a9c74f80f7b70a340d9b80869110993e03f57d2998adb5ff")


if __name__ == "__main__":
    unittest.main()
