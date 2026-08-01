import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.validation.val001.framework import ContractError, canonical_json, load_json
from tools.validation.val001.invocation import atomic_write, synthetic_transaction
from tools.validation.val001.journal import classify_reconciliation, derive_summary, derive_summary_bytes, parse_journal, validate_sequence, verify_summary

ROOT = Path(__file__).resolve().parents[1]
EVENT_SCHEMA = ROOT / "validation/val001/schemas/invocation_event.schema.json"


class Val001CompletionSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.schema = load_json(EVENT_SCHEMA)
        self.events = parse_journal(ROOT / "validation/val001/VAL_001_INVOCATION_EVENTS.jsonl", self.schema)

    def write_journal(self, root, events, terminal_newline=True):
        data = b"".join(json.dumps(e, sort_keys=True, separators=(",", ":")).encode() + b"\n" for e in events)
        if not terminal_newline: data = data.rstrip(b"\n")
        path = Path(root) / "events.jsonl"; path.write_bytes(data); return path

    def test_current_journal_summary_is_byte_exact_and_idempotent(self):
        journal = ROOT / "validation/val001/VAL_001_INVOCATION_EVENTS.jsonl"
        expected = ROOT / "validation/val001/VAL_001_INVOCATION_SUMMARY_V2.json"
        first = derive_summary_bytes(journal, self.schema); second = derive_summary_bytes(journal, self.schema)
        self.assertEqual(first, second); self.assertEqual(expected.read_bytes(), first)
        verify_summary(journal, EVENT_SCHEMA, expected)

    def test_journal_mutations_fail(self):
        mutations = []
        duplicate_id = copy.deepcopy(self.events); duplicate_id[1]["event_id"] = duplicate_id[0]["event_id"]; mutations.append(duplicate_id)
        bad_sequence = copy.deepcopy(self.events); bad_sequence[2]["sequence"] = 9; mutations.append(bad_sequence)
        duplicate_terminal = copy.deepcopy(self.events); duplicate_terminal.insert(3, copy.deepcopy(duplicate_terminal[2])); mutations.append(duplicate_terminal)
        no_output = copy.deepcopy(self.events); no_output[2]["output_sha256"] = None; mutations.append(no_output)
        failed_output = copy.deepcopy(self.events); failed_output[1]["output_sha256"] = "0" * 64; mutations.append(failed_output)
        two_consumed = copy.deepcopy(self.events); two_consumed.append({**copy.deepcopy(two_consumed[-1]), "sequence": 5, "event_id": "EVT-0005"}); mutations.append(two_consumed)
        for events in mutations:
            with self.subTest(events=events):
                with self.assertRaises(ContractError): validate_sequence(events)

    def test_truncated_malformed_blank_and_extra_journal_fail(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.write_journal(d, self.events, terminal_newline=False)
            with self.assertRaises(ContractError): parse_journal(path, self.schema)
            path.write_text("{}\nnot-json\n")
            with self.assertRaises(ContractError): parse_journal(path, self.schema)
            path.write_text("{}\n\n")
            with self.assertRaises(ContractError): parse_journal(path, self.schema)

    def test_summary_count_hash_key_order_and_unknown_field_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            journal = self.write_journal(d, self.events); summary = Path(d) / "summary.json"
            value = derive_summary(self.events)
            for mutate in (lambda x: x["counts"].__setitem__("completed_invocations", 2), lambda x: x["output_hashes"].__setitem__(0, "0" * 64), lambda x: x.__setitem__("unknown", True)):
                broken = copy.deepcopy(value); mutate(broken); summary.write_bytes(canonical_json(broken))
                with self.assertRaises(ContractError): verify_summary(journal, EVENT_SCHEMA, summary)
            summary.write_text(json.dumps(value, separators=(",", ":")) + "\n")
            with self.assertRaises(ContractError): verify_summary(journal, EVENT_SCHEMA, summary)

    def test_atomic_write_fault_matrix_is_fail_closed(self):
        stages = ["before_mkdir", "before_temp_create", "before_write", "before_flush", "before_file_fsync", "before_validation", "before_replace", "after_replace", "before_directory_fsync"]
        for stage in stages:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as d:
                target = Path(d) / "result.json"
                def fault(current):
                    if current == stage: raise OSError(stage)
                with self.assertRaises(OSError): atomic_write(target, b'{"synthetic":true}\n', lambda p: load_json(p), fault)

    def test_synthetic_transaction_result_failure_matrix_records_terminal_failure(self):
        stages = ["assembly", "completion", "before_write", "before_flush", "before_file_fsync", "before_validation", "before_replace", "after_replace", "before_directory_fsync"]
        for stage in stages:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as d:
                with self.assertRaises(Exception): synthetic_transaction(Path(d), f"AUTH-{stage}", lambda: {"synthetic": True}, self.schema, stage)
                lines = (Path(d) / "events.jsonl").read_text().splitlines()
                self.assertEqual("FAILED", json.loads(lines[-1])["status"])
                with self.assertRaises(ContractError): synthetic_transaction(Path(d), f"AUTH-{stage}", lambda: {"synthetic": True}, self.schema)

    def test_reconciliation_classifications(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); journal=self.write_journal(root,self.events); result=root/"result.json"; summary=root/"summary.json"; summary.write_bytes(derive_summary_bytes(journal,self.schema)); result.write_bytes(b"x")
            self.assertEqual("RESULT_HASH_MISMATCH_MANUAL_RECONCILIATION_REQUIRED", classify_reconciliation(journal,EVENT_SCHEMA,result,summary,"0"*64))
            result.write_bytes(b"ok"); import hashlib; expected=hashlib.sha256(b"ok").hexdigest()
            self.assertEqual("CONSISTENT_CONSUMED_STATE", classify_reconciliation(journal,EVENT_SCHEMA,result,summary,expected))
            summary.write_text("{}\n")
            self.assertEqual("JOURNAL_SUMMARY_MISMATCH_MANUAL_RECONCILIATION_REQUIRED", classify_reconciliation(journal,EVENT_SCHEMA,result,summary,expected))
            journal.write_text("truncated")
            self.assertEqual("INVALID_OR_TRUNCATED_JOURNAL_MANUAL_RECONCILIATION_REQUIRED", classify_reconciliation(journal,EVENT_SCHEMA,result,summary,expected))

    def test_started_and_completion_inconsistency_classifications(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); summary=root/"summary.json"; summary.write_text("{}\n"); result=root/"result.json"
            started = [{**copy.deepcopy(self.events[2]), "sequence":1,"event_id":"EVT-0001","event_type":"INVOCATION_STARTED","status":"STARTED","output_sha256":None,"score_exposed":False,"source_opened":False}]
            journal=self.write_journal(root,started)
            self.assertEqual("STARTED_WITHOUT_RESULT_MANUAL_RECONCILIATION_REQUIRED", classify_reconciliation(journal,EVENT_SCHEMA,result,summary,"0"*64))
            completed=[{**copy.deepcopy(self.events[2]),"sequence":1,"event_id":"EVT-0001"}]; journal=self.write_journal(root,completed)
            self.assertEqual("COMPLETION_EVENT_WITHOUT_RESULT_MANUAL_RECONCILIATION_REQUIRED", classify_reconciliation(journal,EVENT_SCHEMA,result,summary,"0"*64))


if __name__ == "__main__": unittest.main()
