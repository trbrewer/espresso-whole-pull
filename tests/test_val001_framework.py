import copy
import ast
import csv
import hashlib
import importlib.util
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

    def _run_synthetic_top_level(self, directory):
        root = Path(directory)
        source = root / "synthetic.csv"
        pressures = ["1.0", "2.0", "3.5", "4.0", "5.0", "6.0", "7.0", "8.0", "9.0", "11.0"]
        with source.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["nominal_pressure_bar", "domain_status", "measured_mass_flow_g_s", "universal_curve_flow_g_s", "finite_phi_flow_g_s"])
            for index, pressure in enumerate(pressures, 1):
                writer.writerow([pressure, "IN_DOMAIN", index, index + 0.25, index - 0.5])
            writer.writerow(["13.0", "OUTSIDE_LOCAL_CONSTITUTIVE_DOMAIN", 11, 11.25, 10.5])
        adapter = copy.deepcopy(self.adapter)
        adapter["source"]["local_reduced_input"] = "synthetic.csv"
        adapter["source"]["local_reduced_input_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        spec = copy.deepcopy(self.spec)
        spec["adapter"] = "validation/val001/adapters/WASZKIEWICZ_PRESSURE_FLOW_ADAPTER.json"
        spec["input"]["path"] = "synthetic.csv"
        spec["input"]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        spec["input"]["selected_row_ids"] = pressures
        spec["output"] = "validation/val001/results/VAL_001_CORRECTED_COMPONENT_COMPARISONS_V2.json"
        (root / "validation/val001/results").mkdir(parents=True, exist_ok=True)
        paths = {
            "adapter": root / spec["adapter"],
            "spec": root / "validation/val001/contracts/VAL_001_CORRECTED_RUN_SPEC.json",
            "ledger": root / "validation/val001/VAL_001_INVOCATION_ACCOUNTING_CONTRACT.json",
            "authority": root / "authority.json",
            "activation": root / "activation.json",
        }
        for key in ("adapter", "spec", "ledger"):
            paths[key].parent.mkdir(parents=True, exist_ok=True)
        paths["adapter"].write_bytes(canonical_json(adapter))
        paths["spec"].write_bytes(canonical_json(spec))
        ledger = {"actual_corrected": {"real_data_comparison_invocations": 1, "governed_result_producing_invocations": 0, "test_or_ci_real_data_invocations": 0}, "events": [{"invocation_id": "VAL001-CORRECTED-REAL-001", "status": "FAILED"}], "historical": {"minimum_known_precorrection_real_data_computations": 3}}
        paths["ledger"].write_bytes(canonical_json(ledger))
        paths["authority"].write_bytes(canonical_json({"status": "AUTHORIZED_FOR_ONE_SECOND_CORRECTION_REPLACEMENT_INVOCATION"}))
        paths["activation"].write_bytes(canonical_json({"status": "ACTIVE_FOR_HASH_VERIFIED_ARTIFACT_REUSE", "actual_openfoam_case_executions": 0}))
        runner_path = ROOT / "scripts/run_val001_corrected_comparison.py"
        module_spec = importlib.util.spec_from_file_location("val001_synthetic_runner", runner_path)
        runner = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(runner)
        argv = [str(runner_path), "--root", str(root), "--authority", str(paths["authority"]), "--activation", str(paths["activation"]), "--ledger", str(paths["ledger"]), "--invocation-id", "VAL001-SECOND-CORRECTION-REPLACEMENT-001"]
        opened = []
        original_open = Path.open
        def guarded(path, *args, **kwargs):
            opened.append(str(path))
            if str(path).endswith(GOVERNED_REAL_SOURCE):
                raise AssertionError("synthetic runner opened governed real source")
            return original_open(path, *args, **kwargs)
        with mock.patch.object(runner, "git", side_effect=["f" * 40, "e" * 40]), mock.patch.object(Path, "open", guarded), mock.patch.object(__import__("sys"), "argv", argv), mock.patch.dict(__import__("os").environ, {"VAL001_REAL_DATA_EXECUTION": "AUTHORIZED_SINGLE_INVOCATION"}):
            runner.main()
        result_path = root / spec["output"]
        result = load_json(result_path)
        validate_record(result, load_json(ROOT / "validation/val001/schemas/comparison_result.schema.json"))
        self.assertIs(result["comparisons"][0]["metrics"]["gate_bearing"], False)
        self.assertEqual(2, len(result["comparisons"]))
        self.assertFalse(any(path.endswith(GOVERNED_REAL_SOURCE) for path in opened))
        return result_path.read_bytes()

    def test_exact_top_level_result_assembly_is_synthetic_and_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            self.assertEqual(self._run_synthetic_top_level(first), self._run_synthetic_top_level(second))

    def test_python_ast_rejects_bare_json_value_identifiers(self):
        forbidden = []
        for path in sorted((ROOT / "scripts").glob("*.py")) + sorted((ROOT / "tools/validation/val001").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in {"true", "false", "null"}:
                    forbidden.append((str(path.relative_to(ROOT)), node.lineno, node.id))
        self.assertEqual([], forbidden)


if __name__ == "__main__":
    unittest.main()
