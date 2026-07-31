import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.validation.val001.framework import ContractError, run, validate_adapter, validate_run_spec


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "validation/val001/adapters/WASZKIEWICZ_PRESSURE_FLOW_ADAPTER.json"
SPEC_PATH = ROOT / "validation/val001/contracts/VAL_001_PREEXECUTION_RUN_SPEC.json"


class Val001FrameworkTests(unittest.TestCase):
    def setUp(self):
        self.adapter = json.loads(ADAPTER_PATH.read_text())
        self.spec = json.loads(SPEC_PATH.read_text())

    def test_governed_records_validate(self):
        validate_adapter(self.adapter)
        validate_run_spec(self.spec, self.adapter)

    def test_pressure_node_is_required(self):
        broken = copy.deepcopy(self.adapter)
        del broken["quantities"][0]["pressure_node"]
        with self.assertRaisesRegex(ContractError, "pressure node"):
            validate_adapter(broken)

    def test_comparison_cannot_be_calibration(self):
        broken = copy.deepcopy(self.adapter)
        duplicated = copy.deepcopy(broken["quantities"][2])
        duplicated["role"] = "calibrated"
        broken["quantities"].append(duplicated)
        with self.assertRaises(ContractError):
            validate_adapter(broken)

    def test_protected_count_fails_closed(self):
        broken = copy.deepcopy(self.spec)
        broken["protected_access_count"] = 1
        with self.assertRaisesRegex(ContractError, "protected"):
            validate_run_spec(broken, self.adapter)

    def test_input_hash_is_enforced(self):
        broken = copy.deepcopy(self.spec)
        broken["input"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            spec_path = Path(directory) / "spec.json"
            spec_path.write_text(json.dumps(broken))
            with self.assertRaisesRegex(ContractError, "SHA-256"):
                run(ROOT, spec_path, ADAPTER_PATH)

    def test_metrics_are_deterministic_and_uncertainty_bounded(self):
        result = run(ROOT, SPEC_PATH, ADAPTER_PATH)
        self.assertEqual(2, len(result["comparisons"]))
        self.assertEqual("SOURCE_UNCERTAINTY_NOT_REPORTED", result["comparisons"][0]["metrics"]["uncertainty_status"])
        self.assertEqual(0, result["execution_counts"]["openfoam"])
        self.assertEqual("NOT_ESTABLISHED", result["claim_boundary"]["physical_validation"])


if __name__ == "__main__":
    unittest.main()
