import copy
import json
import math
import multiprocessing
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.validation.val001.framework import (
    ContractError, GovernedComparisonPermit, SyntheticComparisonPermit,
    canonical_json, interpretation_rules, load_json, metrics, validate_adapter,
    validate_record,
)
from tools.validation.val001.invocation import exclusive_authority, synthetic_transaction
from tools.validation.val001.schema import SchemaError, lint_schema
from tools.validation.val001.source_identity import selected_row_identity

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "validation/val001/results/VAL_001_CORRECTED_COMPONENT_COMPARISONS_V2.json"
RESULT_SCHEMA = ROOT / "validation/val001/schemas/comparison_result.schema.json"
LEDGER = ROOT / "validation/val001/VAL_001_INVOCATION_ACCOUNTING_CONTRACT.json"
LEDGER_SCHEMA = ROOT / "validation/val001/schemas/invocation_ledger.schema.json"
EVENT_SCHEMA = ROOT / "validation/val001/schemas/invocation_event.schema.json"
ADAPTER = ROOT / "validation/val001/adapters/WASZKIEWICZ_PRESSURE_FLOW_ADAPTER.json"


def hold_lock(path, ready, release):
    with exclusive_authority(Path(path)):
        ready.set(); release.wait(5)


class Val001SyntheticFrameworkTests(unittest.TestCase):
    def test_deep_result_mutations_fail(self):
        original, schema = load_json(V2), load_json(RESULT_SCHEMA)
        mutations = [
            lambda x: x["input"].__setitem__("authority_record_sha256", "bad"),
            lambda x: x["comparisons"][0]["metrics"].__setitem__("rmse", "bad"),
            lambda x: x["comparisons"][0]["metrics"].pop("n"),
            lambda x: x["comparisons"][0]["residual_table"][0].pop("nominal_pressure_bar"),
            lambda x: x["comparisons"][0]["residual_table"][0].__setitem__("bogus", 1),
            lambda x: x["claim_boundaries"].__setitem__("physical_validation", "ESTABLISHED"),
            lambda x: x["input"].__setitem__("unknown", True),
        ]
        validate_record(original, schema)
        for mutation in mutations:
            broken = copy.deepcopy(original); mutation(broken)
            with self.assertRaises(ContractError): validate_record(broken, schema)

    def test_deep_ledger_mutations_fail(self):
        original, schema = load_json(LEDGER), load_json(LEDGER_SCHEMA)
        validate_record(original, schema)
        mutations = [
            lambda x: x["events"].__setitem__(0, {}),
            lambda x: x["historical"].__setitem__("minimum_known_total_real_data_computations", "five"),
            lambda x: x["events"][0].__setitem__("commit", "bad"),
            lambda x: x["claim_boundaries"].__setitem__("physical_validation", "ESTABLISHED"),
        ]
        for mutation in mutations:
            broken = copy.deepcopy(original); mutation(broken)
            with self.assertRaises(ContractError): validate_record(broken, schema)

    def test_schema_linter_rejects_unsupported_keyword(self):
        with self.assertRaisesRegex(SchemaError, "unsupported"):
            lint_schema({"type": "string", "format": "uri"})

    def test_schema_types_distinguish_boolean_integer_and_finite_numbers(self):
        with self.assertRaises(ContractError): validate_record({"x": True}, {"type": "object", "required": ["x"], "properties": {"x": {"type": "integer"}}, "additionalProperties": False})
        with self.assertRaises(ContractError): validate_record({"x": 1}, {"type": "object", "required": ["x"], "properties": {"x": {"type": "boolean"}}, "additionalProperties": False})
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ContractError): validate_record({"x": value}, {"type": "object", "required": ["x"], "properties": {"x": {"type": "number"}}, "additionalProperties": False})
            with self.assertRaises(ValueError): canonical_json({"x": value})

    def test_expected_puckworks_lock_is_semantically_enforced(self):
        adapter = load_json(ADAPTER)
        validate_adapter(adapter, expected_dependency=("fc61c4670ec7bf801e40bb391aab16048b8da26b", "1d553e44ee2f7480a5df521560801b478618cc84"))
        with self.assertRaisesRegex(ContractError, "dependency"):
            validate_adapter(adapter, expected_dependency=("0" * 40, "1" * 40))

    def test_production_cli_has_no_identity_overrides_and_refuses_execution(self):
        runner = ROOT / "scripts/run_val001_corrected_comparison.py"
        for option in ("--authority", "--activation", "--ledger", "--invocation-id", "--input", "--adapter", "--output"):
            completed = subprocess.run([str(runner), "--root", str(ROOT), option, "x"], text=True, capture_output=True)
            self.assertNotEqual(0, completed.returncode)
        completed = subprocess.run([str(runner), "--root", str(ROOT)], text=True, capture_output=True)
        self.assertIn("VAL001_EXECUTION_AUTHORITY_CONSUMED", completed.stderr)

    def test_environment_variable_does_not_authorize(self):
        runner = ROOT / "scripts/run_val001_corrected_comparison.py"
        environment = dict(os.environ, VAL001_REAL_DATA_EXECUTION="AUTHORIZED_SINGLE_INVOCATION")
        completed = subprocess.run([str(runner), "--root", str(ROOT)], env=environment, text=True, capture_output=True)
        self.assertNotEqual(0, completed.returncode)

    def test_direct_governed_permit_construction_fails(self):
        with self.assertRaises(ContractError): GovernedComparisonPermit(object())

    def test_synthetic_permit_refuses_governed_source_aliases(self):
        permit = SyntheticComparisonPermit()
        with self.assertRaises(ContractError): permit.assert_source(Path("validation/wp03/WP03_001_SOURCE_PRESSURE_SWEEP.csv"))
        with tempfile.TemporaryDirectory() as directory:
            link = Path(directory) / "source.csv"; link.symlink_to(ROOT / "validation/wp03/WP03_001_SOURCE_PRESSURE_SWEEP.csv")
            with self.assertRaises(ContractError): permit.assert_source(link.resolve())

    def test_interpretation_varies_with_evidence(self):
        empty = interpretation_rules({"comparisons": []})
        current = interpretation_rules({"comparisons": [{"synthetic": True}], "post_fit": True, "source_uncertainty_available": False, "criterion": None, "mechanism_uniqueness_assessed": False})
        met = interpretation_rules({"comparisons": [{"synthetic": True}], "post_fit": False, "source_uncertainty_available": True, "criterion": {"identity": "synthetic", "provenance": "synthetic", "direction": "GREATER_OR_EQUAL", "threshold": 2.0, "value": 3.0, "predeclared": True}, "mechanism_uniqueness_assessed": True})
        not_met = interpretation_rules({"comparisons": [{"synthetic": True}], "post_fit": False, "source_uncertainty_available": True, "criterion": {"identity": "synthetic", "provenance": "synthetic", "direction": "GREATER_OR_EQUAL", "threshold": 4.0, "value": 3.0, "predeclared": True}, "mechanism_uniqueness_assessed": False})
        self.assertNotEqual(empty, current); self.assertNotEqual(current, met); self.assertNotEqual(met, not_met)
        self.assertIn("QUANTITATIVE_VARIANT_DISCRIMINATION_NOT_ASSESSED", current["scientific_evaluation"])
        self.assertIn("MECHANISM_UNIQUENESS_NOT_ASSESSED", current["scientific_evaluation"])

    def test_synthetic_metrics_remain_deterministic(self):
        self.assertEqual(metrics([1.0, 2.0], [1.25, 1.75]), metrics([1.0, 2.0], [1.25, 1.75]))

    def test_synthetic_transaction_is_single_use_and_records_failures(self):
        schema = load_json(EVENT_SCHEMA)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            synthetic_transaction(root, "AUTH-1", lambda: {"synthetic": True}, schema)
            with self.assertRaises(ContractError): synthetic_transaction(root, "AUTH-1", lambda: {"synthetic": True}, schema)
            with self.assertRaises(RuntimeError): synthetic_transaction(root, "AUTH-2", lambda: {"synthetic": True}, schema, fail_stage="assembly")
            events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
            self.assertEqual("FAILED", events[-1]["status"])
            with self.assertRaises(ContractError): synthetic_transaction(root, "AUTH-2", lambda: {"synthetic": True}, schema)

    def test_started_without_completion_requires_reconciliation(self):
        schema = load_json(EVENT_SCHEMA)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ContractError): synthetic_transaction(root, "AUTH-STARTED", lambda: {"synthetic": True}, schema, fail_stage="after_started")
            with self.assertRaises(ContractError): synthetic_transaction(root, "AUTH-STARTED", lambda: {"synthetic": True}, schema)

    def test_exclusive_lock_refuses_concurrent_process(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "lock"; ready = multiprocessing.Event(); release = multiprocessing.Event()
            process = multiprocessing.Process(target=hold_lock, args=(str(lock), ready, release)); process.start(); self.assertTrue(ready.wait(5))
            with self.assertRaises(ContractError):
                with exclusive_authority(lock): pass
            release.set(); process.join(5); self.assertEqual(0, process.exitcode)

    def test_selected_row_identity_is_reproducible_without_metrics(self):
        identity = selected_row_identity(ROOT / "validation/wp03/WP03_001_SOURCE_PRESSURE_SWEEP.csv")
        self.assertEqual("37dd7ff3c1b088c0cd8558154d2af2a2ca6b6e98a11aebda78dfdb9015877c0b", identity["selected_row_canonical_sha256_v2"])
        self.assertNotIn("rmse", json.dumps(identity).lower())

    def test_selected_row_identity_detects_mutation(self):
        source = ROOT / "validation/wp03/WP03_001_SOURCE_PRESSURE_SWEEP.csv"
        with tempfile.TemporaryDirectory() as directory:
            copy_path = Path(directory) / "source.csv"; copy_path.write_bytes(source.read_bytes().replace(b"IN_DOMAIN", b"OUT_DOMAIN", 1))
            with self.assertRaises(ContractError): selected_row_identity(copy_path)


if __name__ == "__main__": unittest.main()
