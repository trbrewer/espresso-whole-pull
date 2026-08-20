import copy
import json
import unittest
from pathlib import Path

from scripts.validate_sci_lc_001a_ledger import validate_ledger

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "validation/cases/sci_lc_001a"


class SciLcLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads((CASE / "EXECUTION_ATTEMPT_LEDGER.json").read_text())
        cls.binding = json.loads((CASE / "RCA_002_EVIDENCE_BINDING.json").read_text())

    def record(self, ledger, record_id):
        return next(record for record in ledger["records"] if record["record_id"] == record_id)

    def assert_invalid(self, mutate, code):
        ledger, binding = copy.deepcopy(self.ledger), copy.deepcopy(self.binding)
        mutate(ledger, binding)
        with self.assertRaisesRegex(ValueError, code):
            validate_ledger(ledger, binding)

    def test_rca_002_ledger_matches_retained_immutable_evidence(self):
        validate_ledger(self.ledger, self.binding)
        rca = self.record(self.ledger, "RCA-002")
        self.assertEqual((rca["planned_keys"], rca["attempted_keys"],
                          rca["completed_keys"], rca["unattempted_keys"]),
                         (3666, 2555, 2555, 1111))
        self.assertEqual(rca["terminal_disposition"], "STOP_EVENT_STATE_CAPTURE_INCOMPLETE")
        self.assertNotEqual(rca["terminal_state"], "COMPLETE")
        self.assertFalse(rca["event_state_capture_complete"])
        self.assertFalse(rca["canonical_eligibility"])
        self.assertFalse(rca["classification_eligibility"])
        self.assertEqual(rca["classification_count"], 0)
        self.assertEqual(rca["dispatched_keys"]["status"],
                         "UNRESOLVED_FROM_RETAINED_EVIDENCE")

    def test_generic_ledger_invariants(self):
        validate_ledger(self.ledger, self.binding)
        self.assertEqual(len(self.ledger["records"]),
                         len({record["record_id"] for record in self.ledger["records"]}))
        self.assertEqual(self.ledger["attempt_05_authority"], "NONE")

    def test_attempt_04_dispatch_precision_matches_surviving_durable_evidence(self):
        attempt = self.record(self.ledger, "E4-ATTEMPT-04")
        self.assertEqual(attempt["controller_reported_dispatch_scalar"], 3666)
        self.assertEqual(attempt["dispatched_keys"]["status"],
                         "UNRESOLVED_FROM_RETAINED_EVIDENCE")
        self.assertIn("no durable per-key pre-launch dispatch records survive",
                      attempt["dispatched_keys"]["reason"])
        self.assertEqual(attempt["durable_per_key_prelaunch_dispatch_records"], 0)
        self.assertEqual((attempt["planned_keys"], attempt["attempted_keys"],
                          attempt["completed_keys"], attempt["stopped_keys"],
                          attempt["failed_keys"], attempt["unattempted_keys"]),
                         (3666, 3666, 3558, 108, 0, 0))
        self.assertFalse(attempt["diagnostic_health_complete"])
        self.assertFalse(attempt["classification_eligibility"])
        self.assertEqual(attempt["classification_count"], 0)
        self.assertTrue(attempt["quarantined"])
        self.assertEqual(self.ledger["attempt_05_authority"], "NONE")

    def test_attempt_04_dispatch_surfaces_are_consistent(self):
        result = (ROOT / "docs/analysis/sci_lc_001a/RESULT.md").read_text()
        audit = (ROOT / "docs/analysis/sci_lc_001a/AUDIT_AND_CURRENT_STATE.md").read_text()
        readme = (ROOT / "docs/analysis/sci_lc_001a/README.md").read_text()
        project = (ROOT / "docs/PROJECT_STATE.md").read_text()
        archive = json.loads((CASE / "EVIDENCE_ARCHIVE_MANIFEST.json").read_text())
        package = next(item for item in archive["packages"]
                       if item["logical_evidence_id"] == "E4-ATTEMPT-04")
        qa = json.loads((ROOT / "PACKAGE_QA_STATUS.json").read_text())["sci_lc_001a"]
        for surface in (result, audit, readme, project):
            self.assertIn("exact per-key dispatched inventory is unresolved",
                          " ".join(surface.split()))
        self.assertEqual(package["dispatched_keys"]["status"],
                         "UNRESOLVED_FROM_RETAINED_EVIDENCE")
        self.assertEqual(package["controller_reported_dispatch_scalar"], 3666)
        self.assertEqual(package["durable_per_key_prelaunch_dispatch_records"], 0)
        self.assertEqual(qa["attempt_04_exact_dispatched_inventory"],
                         "UNRESOLVED_FROM_RETAINED_EVIDENCE")

    def test_negative_attempt_04_false_complete_diagnostics(self):
        self.assert_invalid(lambda l, b: self.record(l, "E4-ATTEMPT-04").update(
            diagnostic_health_complete=True),
            "ATTEMPT_04_FINAL_EVIDENCE_MISMATCH:diagnostic_health_complete")

    def test_negative_attempt_04_exact_dispatch_integer(self):
        self.assert_invalid(lambda l, b: self.record(l, "E4-ATTEMPT-04").update(
            dispatched_keys=3666), "ATTEMPT_04_EXACT_DISPATCH_MUST_BE_TYPED_UNRESOLVED")

    def test_negative_attempt_04_unresolved_status_removed(self):
        self.assert_invalid(lambda l, b: self.record(l, "E4-ATTEMPT-04")[
            "dispatched_keys"].update(status="UNKNOWN"),
            "ATTEMPT_04_DISPATCH_UNRESOLVED_STATUS_REQUIRED")

    def test_negative_attempt_04_controller_scalar_removed(self):
        self.assert_invalid(lambda l, b: self.record(l, "E4-ATTEMPT-04").pop(
            "controller_reported_dispatch_scalar"),
            "ATTEMPT_04_FINAL_EVIDENCE_MISMATCH:controller_reported_dispatch_scalar")

    def test_negative_attempt_04_controller_scalar_changed(self):
        self.assert_invalid(lambda l, b: self.record(l, "E4-ATTEMPT-04").update(
            controller_reported_dispatch_scalar=3665),
            "ATTEMPT_04_FINAL_EVIDENCE_MISMATCH:controller_reported_dispatch_scalar")

    def test_negative_attempt_04_durable_dispatch_records_nonzero(self):
        self.assert_invalid(lambda l, b: self.record(l, "E4-ATTEMPT-04").update(
            durable_per_key_prelaunch_dispatch_records=1),
            "ATTEMPT_04_FINAL_EVIDENCE_MISMATCH:durable_per_key_prelaunch_dispatch_records")

    def test_negative_attempt_04_attempted_changed(self):
        self.assert_invalid(lambda l, b: self.record(l, "E4-ATTEMPT-04").update(
            attempted_keys=3665), "ATTEMPT_04_FINAL_EVIDENCE_MISMATCH:attempted_keys")

    def test_negative_attempt_04_outcome_arithmetic(self):
        self.assert_invalid(lambda l, b: self.record(l, "E4-ATTEMPT-04").update(
            stopped_keys=107), "PLANNED_COUNT_ARITHMETIC_INVALID:E4-ATTEMPT-04")

    def test_negative_attempt_04_eligibility_true(self):
        self.assert_invalid(lambda l, b: self.record(l, "E4-ATTEMPT-04").update(
            classification_eligibility=True),
            "INCOMPLETE_CLASSIFICATION_ELIGIBILITY:E4-ATTEMPT-04")

    def test_negative_attempt_04_classification_nonzero(self):
        self.assert_invalid(lambda l, b: self.record(l, "E4-ATTEMPT-04").update(
            classification_count=1), "INELIGIBLE_CLASSIFICATION_NONZERO:E4-ATTEMPT-04")

    def test_current_status_matches_ledger(self):
        status = json.loads((CASE / "SCI_LC_001A_CURRENT_STATUS.json").read_text())
        result = self.ledger["canonical_result"]
        self.assertEqual(status["canonical_execution_count"], result["execution_count"])
        self.assertEqual(status["canonical_classification_count"], result["classification_count"])
        self.assertEqual(status["attempt_05_authority"], self.ledger["attempt_05_authority"])
        self.assertFalse(status["launch_authorized"])
        self.assertFalse(status["classification_authorized"])

    def test_audit_summary_binds_rca_002(self):
        audit = (ROOT / "docs/analysis/sci_lc_001a/AUDIT_AND_CURRENT_STATE.md").read_text()
        for text in ("2,555 attempted and complete", "1,111 unattempted",
                     "STOP_EVENT_STATE_CAPTURE_INCOMPLETE",
                     "exact dispatched count is unresolved",
                     "Attempt 05 authority is `NONE`"):
            self.assertIn(text, audit)

    def test_negative_completed_3666(self):
        self.assert_invalid(lambda l, b: self.record(l, "RCA-002").update(completed_keys=3666),
                            "PLANNED_COUNT_ARITHMETIC_INVALID:RCA-002")

    def test_negative_unattempted_zero(self):
        self.assert_invalid(lambda l, b: self.record(l, "RCA-002").update(unattempted_keys=0),
                            "PLANNED_COUNT_ARITHMETIC_INVALID:RCA-002")

    def test_negative_terminal_complete(self):
        self.assert_invalid(lambda l, b: self.record(l, "RCA-002").update(terminal_state="COMPLETE"),
                            "COMPLETE_WITH_UNATTEMPTED:RCA-002")

    def test_negative_complete_cause(self):
        self.assert_invalid(lambda l, b: self.record(l, "RCA-002").update(
            terminal_disposition="OBSERVABILITY_DIAGNOSTIC_COMPLETE"),
            "RCA002_EVIDENCE_BINDING_MISMATCH:terminal_disposition")

    def test_negative_canonical_eligible(self):
        self.assert_invalid(lambda l, b: self.record(l, "RCA-002").update(canonical_eligibility=True),
                            "INCOMPLETE_CANONICAL_ELIGIBILITY:RCA-002")

    def test_negative_classification_eligible(self):
        self.assert_invalid(lambda l, b: self.record(l, "RCA-002").update(classification_eligibility=True),
                            "INCOMPLETE_CLASSIFICATION_ELIGIBILITY:RCA-002")

    def test_negative_classification_nonzero(self):
        self.assert_invalid(lambda l, b: self.record(l, "RCA-002").update(classification_count=1),
                            "INELIGIBLE_CLASSIFICATION_NONZERO:RCA-002")

    def test_negative_binding_source_hash(self):
        self.assert_invalid(lambda l, b: b["sources"].update({"reports/COUNTERS.json": "0" * 64}),
                            "RCA002_SOURCE_HASH_MISMATCH:reports/COUNTERS.json")

    def test_negative_attempt_05(self):
        self.assert_invalid(lambda l, b: l.update(attempt_05_authority="AUTHORIZED"),
                            "ATTEMPT_05_FORBIDDEN")

    def test_negative_planned_arithmetic(self):
        self.assert_invalid(lambda l, b: self.record(l, "E4-ATTEMPT-01").update(unattempted_keys=899),
                            "PLANNED_COUNT_ARITHMETIC_INVALID:E4-ATTEMPT-01")

    def test_negative_unresolved_missing_reason(self):
        self.assert_invalid(lambda l, b: self.record(l, "RCA-002")["dispatched_keys"].update(reason=""),
                            "TYPED_UNRESOLVED_REASON_REQUIRED")


if __name__ == "__main__":
    unittest.main()
