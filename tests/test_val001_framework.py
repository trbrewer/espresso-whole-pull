import copy
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.validation.val001.framework import (
    ContractError, GOVERNED_REAL_SOURCE, assert_invocation_available, canonical_json, load_json, metrics,
    read_selected_rows, validate_adapter, validate_record, validate_run_spec,
)


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "validation/val001/adapters/WASZKIEWICZ_PRESSURE_FLOW_ADAPTER.json"
SPEC = ROOT / "validation/val001/contracts/VAL_001_CORRECTED_RUN_SPEC.json"
ADAPTER_SCHEMA = ROOT / "validation/val001/schemas/source_adapter.schema.json"
RUN_SCHEMA = ROOT / "validation/val001/schemas/comparison_run.schema.json"


class Val001SyntheticFrameworkTests(unittest.TestCase):
    def setUp(self):
        self.adapter = load_json(ADAPTER)
        self.spec = load_json(SPEC)
        self.adapter_schema = load_json(ADAPTER_SCHEMA)
        self.run_schema = load_json(RUN_SCHEMA)

    def test_complete_governed_contracts_validate_without_scoring(self):
        validate_record(self.adapter, self.adapter_schema)
        validate_record(self.spec, self.run_schema)
        validate_run_spec(self.spec, self.adapter)

    def test_deep_schema_rejects_unknown_and_wrong_nested_values(self):
        for mutate in (
            lambda x: x["rights"].__setitem__("unknown", True),
            lambda x: x["rights"].__setitem__("comparison_allowed", "yes"),
            lambda x: x["source"].__setitem__("dependency_commit", "short"),
        ):
            broken = copy.deepcopy(self.adapter); mutate(broken)
            with self.assertRaises(ContractError): validate_record(broken, self.adapter_schema)

    def test_evidence_rights_holdout_and_claims_fail_closed(self):
        cases = [
            (lambda x: x["evidence"].pop("level"), "evidence"),
            (lambda x: x["evidence"].__setitem__("level", "INVENTED"), "evidence"),
            (lambda x: x["evidence"].__setitem__("protected", True), "protected"),
            (lambda x: x["evidence"].__setitem__("holdout_status", "INDEPENDENT_HOLDOUT"), "holdout"),
            (lambda x: x["rights"].pop("analysis_permission"), "rights"),
            (lambda x: x["rights"].__setitem__("comparison_allowed", False), "permission"),
            (lambda x: x.__setitem__("claim_ceiling", "PHYSICAL_VALIDATION"), "claim"),
        ]
        for mutate, message in cases:
            with self.subTest(message=message):
                broken = copy.deepcopy(self.adapter); mutate(broken)
                with self.assertRaisesRegex(ContractError, message): validate_adapter(broken)

    def test_dependency_artifact_and_mapping_guards(self):
        with self.assertRaisesRegex(ContractError, "dependency"):
            validate_adapter(self.adapter, expected_dependency=("0" * 40, "1" * 40))
        cases = [
            lambda x: x["source"].__setitem__("artifact_paths", []),
            lambda x: x["source"]["artifact_sha256"].pop(next(iter(x["source"]["artifact_sha256"]))),
            lambda x: x["mappings"]["pressure_node"].__setitem__("value", None),
            lambda x: x["mappings"]["hydraulic_area"].__setitem__("value", None),
        ]
        for mutate in cases:
            broken = copy.deepcopy(self.adapter); mutate(broken)
            with self.assertRaises(ContractError): validate_adapter(broken)

    def test_solver_quantity_and_ledger_guards(self):
        cases = [
            lambda x: x["solver_mapping"].__setitem__("fitting_or_retuning_allowed", True),
            lambda x: x["solver_mapping"].__setitem__("fit_or_retune_count", 1),
            lambda x: x["solver_mapping"].__setitem__("configuration_change", True),
            lambda x: x["quantities"].append(copy.deepcopy(x["quantities"][0])),
            lambda x: x["quantities"][0].__setitem__("unit", ""),
            lambda x: x["quantities"][0].update({"availability": "UNAVAILABLE", "value": 3}),
            lambda x: x["quantities"][1].update({"source_role": "UNRESTRICTED_CALIBRATION", "comparison_role": "INDEPENDENT_COMPARISON"}),
        ]
        for mutate in cases:
            broken = copy.deepcopy(self.adapter); mutate(broken)
            with self.assertRaises(ContractError): validate_adapter(broken)

    def test_comparison_mapping_method_and_count_guards(self):
        cases = [
            lambda x: x["comparisons"][0].__setitem__("observation_column", "absent"),
            lambda x: x["comparisons"][0].__setitem__("prediction_column", "absent"),
            lambda x: x["comparisons"][0].__setitem__("weighting", "RESULT_SELECTED"),
            lambda x: x["comparisons"][0].__setitem__("interpolation", "LINEAR"),
            lambda x: x["comparisons"][0].__setitem__("time_shift", "OPTIMIZED"),
            lambda x: x["comparisons"][0].__setitem__("threshold", 0.3),
            lambda x: x["comparisons"][0]["metrics"].append("CORRELATION"),
            lambda x: x["planned_counts"].__setitem__("openfoam_case_executions", 2),
            lambda x: x["planned_counts"].__setitem__("real_data_comparison_invocations", 2),
            lambda x: x["input"].__setitem__("selected_data_rows", 9),
            lambda x: x["input"].__setitem__("total_data_rows", 10),
        ]
        for mutate in cases:
            broken = copy.deepcopy(self.spec); mutate(broken)
            with self.assertRaises(ContractError): validate_run_spec(broken, self.adapter)

    def test_metrics_are_synthetic_finite_deterministic_and_r2_is_not_correlation(self):
        result = metrics([1.0, 2.0, 4.0], [1.5, 1.0, 4.5])
        self.assertEqual([0.5, -1.0, 0.5], result["residuals"])
        self.assertEqual(result, metrics([1.0, 2.0, 4.0], [1.5, 1.0, 4.5]))
        self.assertIsNone(metrics([2.0, 2.0], [2.0, 3.0])["r_squared_descriptive"])
        for bad in (float("nan"), float("inf"), -float("inf")):
            with self.assertRaisesRegex(ContractError, "nonfinite"): metrics([1.0], [bad])
            with self.assertRaises(ValueError): canonical_json({"value": bad})

    def test_synthetic_csv_row_guards(self):
        spec = copy.deepcopy(self.spec)
        spec["input"].update({"path": "synthetic.csv", "total_data_rows": 2, "selected_data_rows": 2,
                              "selected_row_ids": ["1", "2"]})
        data = ("nominal_pressure_bar,domain_status,measured_mass_flow_g_s,universal_curve_flow_g_s\n"
                "1,IN_DOMAIN,1.0,1.1\n2,IN_DOMAIN,2.0,2.1\n")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = root / "synthetic.csv"; path.write_text(data)
            import hashlib
            spec["input"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(2, len(read_selected_rows(root, spec)))
            for mutate in (lambda s: s["input"]["filter"].__setitem__("field", "bad"),
                           lambda s: s["input"].__setitem__("selected_row_ids", ["1", "1"]),
                           lambda s: s["input"].__setitem__("selected_data_rows", 3)):
                broken = copy.deepcopy(spec); mutate(broken)
                with self.assertRaises(ContractError): read_selected_rows(root, broken)

    def test_ordinary_tests_never_open_governed_real_source_for_metrics(self):
        opened = []
        original = Path.open
        def guarded(path, *args, **kwargs):
            opened.append(str(path))
            if str(path).endswith(GOVERNED_REAL_SOURCE):
                raise AssertionError("ordinary test attempted governed real-data computation")
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "open", guarded):
            metrics([1.0, 2.0], [1.1, 1.9])
        self.assertFalse(any(p.endswith(GOVERNED_REAL_SOURCE) for p in opened))

    def test_invocation_ledger_refuses_second_real_data_invocation(self):
        ledger = {"actual_corrected": {"real_data_comparison_invocations": 0}, "events": []}
        assert_invocation_available(ledger)
        ledger["events"].append({"status": "COMPLETED"})
        with self.assertRaisesRegex(ContractError, "second"):
            assert_invocation_available(ledger)


if __name__ == "__main__":
    unittest.main()
