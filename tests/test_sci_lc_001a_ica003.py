"""ICA-003 baseline-zero-state classification-scope contract tests."""
from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import sci_lc_001a_executor as executor
from scripts import sci_lc_001a_protocol as protocol


class SciLc001aIca003Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = executor.CanonicalStore.load()
        cls.spec = json.loads(executor.PROTOCOL_PATH.read_text())

    def test_owner_selected_architecture_is_closed_and_pending_review(self):
        scope = self.spec["stage_a_initial_condition_scope"]
        self.assertEqual(scope["architecture_id"], protocol.ARCHITECTURE_ID)
        self.assertEqual(scope["authority_status"], "FROZEN_PENDING_INDEPENDENT_REVIEW")
        self.assertNotIn("ARCHITECTURE_A", json.dumps(scope))
        self.assertEqual(scope["physical_validation"], "NOT_ESTABLISHED")

    def test_zero_state_authority_and_numerical_first_step_are_distinct(self):
        scope = self.spec["stage_a_initial_condition_scope"]
        self.assertEqual(scope["dynamic_initial_state"], {
            "internal_sector_pressure": 0.0,
            "machine_pressure_where_applicable": 0.0,
            "resistance_feedback_state_x_i_where_applicable": 0.0})
        self.assertEqual(protocol.DYNAMIC_FIRST_STEP, 1.0e-7)
        self.assertEqual(self.spec["boundary_initial_integration"]["dynamic_first_step_scope"],
                         "all dynamic profiles and both dynamic boundary modes")

    def test_all_dynamic_state_families_and_profiles_construct_exact_zero_y0(self):
        rows = [
            next(row for row in self.canonical.rows if row["pressure_mode"] == "PRESCRIBED_DYNAMIC_RAMP"
                 and row["resistance_evolution_law"] == "NO_EVOLUTION"),
            next(row for row in self.canonical.rows if row["pressure_mode"] == "PRESCRIBED_DYNAMIC_RAMP"
                 and row["resistance_evolution_law"] != "NO_EVOLUTION"),
            next(row for row in self.canonical.rows if row["pressure_mode"] == "MACHINE_COUPLED"),
        ]
        for row in rows:
            for profile in protocol.DYNAMIC_NUMERICAL_PROFILES:
                captured = {}
                class Incomplete:
                    success = False
                    message = "SYNTHETIC_NO_INTEGRATION"
                    sol = None
                    nfev = 0
                def solver(_rhs, _interval, y0, **settings):
                    captured["y0"] = list(y0)
                    captured["first_step"] = settings["first_step"]
                    return Incomplete()
                fake = mock.Mock()
                fake.row.return_value = row
                context = executor._synthetic_context(self.canonical, Path("/tmp"))
                executor._execute_dynamic_case(fake, row["case_id"], profile, context,
                    synthetic=True, solve_ivp_impl=solver)
                expected_size = row["sector_count"]
                if row["pressure_mode"] == "MACHINE_COUPLED":
                    expected_size += 1
                if row["resistance_evolution_law"] != "NO_EVOLUTION":
                    expected_size += row["sector_count"]
                self.assertEqual(captured["y0"], [0.0] * expected_size)
                self.assertEqual(captured["first_step"], 1.0e-7)

    def test_every_plan_key_has_one_protocol_bound_scope_without_new_axis(self):
        plan = executor.build_plan(self.canonical)
        self.assertEqual((plan["dynamic_profile_keys"], plan["static_profile_keys"], plan["total_keys"]),
                         (2212, 1454, 3666))
        self.assertEqual(plan["cache_identity"], "(case_id,numerical_profile)")
        self.assertEqual(plan["dynamic_initial_state_variant"], "ZERO_STATE_BASELINE")
        self.assertEqual(plan["static_dynamic_initial_state_variant"],
                         "NOT_APPLICABLE_STATIC_ALGEBRAIC")
        self.assertTrue(all(len(key) == 2 for key in plan["keys"]))

    def test_legacy_initial_condition_variant_is_structural_not_dynamic_state(self):
        semantics = self.spec["stage_a_initial_condition_scope"][
            "legacy_initial_condition_variant_semantics"]
        self.assertEqual(semantics,
            "LEGACY_STRUCTURAL_OR_HETEROGENEITY_REALIZATION_IDENTIFIER_NOT_DYNAMIC_STATE")
        values = {row["initial_condition_variant"] for row in self.canonical.rows}
        self.assertEqual(values, {"BASE_PHASE", "ROTATED_ONE_SECTOR", "UNIFORM_SYMMETRY",
            "REFLECTED", "LINEAR_PRESSURE_SCALING", "MACHINE_REFERENCE", "NO_EVOLUTION_LIMIT"})
        for row in self.canonical.rows:
            scope = protocol.stage_a_initial_condition_scope(row)
            expected = ("NOT_APPLICABLE_STATIC_ALGEBRAIC" if
                row["pressure_mode"] == "PRESCRIBED_STATIC" else "ZERO_STATE_BASELINE")
            self.assertEqual(scope["dynamic_initial_state_variant"], expected)

    def test_dynamic_and_static_scope_fields_are_exact(self):
        dynamic = next(row for row in self.canonical.rows if row["pressure_mode"] != "PRESCRIBED_STATIC")
        static = next(row for row in self.canonical.rows if row["pressure_mode"] == "PRESCRIBED_STATIC")
        self.assertEqual(protocol.stage_a_initial_condition_scope(dynamic), {
            "dynamic_initial_state_variant": "ZERO_STATE_BASELINE",
            "initial_condition_scope": "BASELINE_ZERO_STATE_ONLY",
            "initial_condition_robustness": "NOT_ADJUDICATED_STAGE_A",
            "bistability_status": "NOT_ADJUDICATED_STAGE_A",
            "initial_condition_dependence_branch": "NOT_EVALUATED_NOT_FALSE"})
        self.assertEqual(protocol.stage_a_initial_condition_scope(static), {
            "dynamic_initial_state_variant": "NOT_APPLICABLE_STATIC_ALGEBRAIC",
            "initial_condition_scope": "DYNAMIC_INITIAL_CONDITION_NOT_APPLICABLE",
            "initial_condition_robustness": "NOT_APPLICABLE_STATIC_ALGEBRAIC",
            "bistability_status": "NOT_APPLICABLE_STATIC_ALGEBRAIC",
            "initial_condition_dependence_branch": "NOT_APPLICABLE_STATIC_ALGEBRAIC"})

    def test_qualified_classification_is_mandatory_and_deterministic(self):
        dynamic = next(row for row in self.canonical.rows if row["pressure_mode"] != "PRESCRIBED_STATIC")
        static = next(row for row in self.canonical.rows if row["pressure_mode"] == "PRESCRIBED_STATIC")
        labels = ("AUTHORITY_OR_ARTIFACT_INVALID", "ANALYTICAL_STRUCTURAL_IDENTITY",
            "NUMERICALLY_UNRESOLVED", "MODEL_FORM_OR_SECTOR_RESOLUTION_DISAGREEMENT",
            "METRIC_DISAGREEMENT", "NEAR_THRESHOLD_TRANSITION", "LATERAL_EQUALIZATION",
            "HETEROGENEITY_AMPLIFIES", "HETEROGENEITY_PERSISTS")
        for label in labels:
            d = executor._qualified_classification_record(dynamic, label)
            s = executor._qualified_classification_record(static, label)
            self.assertEqual(d["qualified_classification"], label + ";BASELINE_ZERO_STATE_ONLY")
            self.assertEqual(s["qualified_classification"],
                             label + ";DYNAMIC_INITIAL_CONDITION_NOT_APPLICABLE")
            self.assertEqual(d["ordinary_regime_label"], label)

    def test_active_stage_a_precedence_reserves_but_does_not_evaluate_d4_branch(self):
        precedence = executor.protocol_spec_precedence()
        self.assertEqual(precedence, tuple(self.spec["classification"]["precedence"]))
        self.assertNotIn("INITIAL_CONDITION_DEPENDENT_OR_BISTABLE", precedence)
        reconciliation = self.spec["classification"]["initial_condition_reconciliation"]
        self.assertEqual(reconciliation["reserved_future_label"],
                         "INITIAL_CONDITION_DEPENDENT_OR_BISTABLE")
        self.assertEqual(reconciliation["initial_condition_dependence_branch"],
                         "NOT_EVALUATED_NOT_FALSE")
        self.assertNotIn("initial_condition_disagreement",
                         inspect.signature(executor._classification_precedence_fixture).parameters)
        self.assertNotIn("initial_dependence",
                         inspect.signature(protocol.classify_synthetic_fixture).parameters)

    def test_historical_amplitudes_are_non_executable_and_d4_fails_closed(self):
        historical = self.spec["boundary_initial_integration"]["historical_alternate_amplitudes"]
        self.assertEqual(historical["values"], ["0.5", "1.5"])
        self.assertEqual(historical["status"], protocol.HISTORICAL_ALTERNATE_STATUS)
        self.assertEqual(historical["production_or_planning_use"], "PROHIBITED")
        self.assertNotIn("alternate_amplitudes", self.spec["boundary_initial_integration"])
        with self.assertRaisesRegex(protocol.DeferredStageError, protocol.D4_AUTHORITY_STOP):
            protocol.d4_select_synthetic([{"amplitude": "0.5"}])
        self.assertEqual(self.spec["staged_deferral"]["D4"]["stage_a_rows"], 0)

    def test_result_records_emit_scope_and_old_unqualified_records_fail_closed(self):
        row = next(row for row in self.canonical.rows if row["pressure_mode"] != "PRESCRIBED_STATIC")
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "results"
            context = executor._synthetic_context(self.canonical, root)
            store = executor.ResultStore(root, self.canonical)
            manifest = store.begin_run(context, 1)
            record = executor.synthetic_backend_record(row, "BASE", context)
            self.assertEqual(record["initial_condition_scope"], "BASELINE_ZERO_STATE_ONLY")
            stale = dict(record)
            stale.pop("initial_condition_scope")
            with self.assertRaisesRegex(ValueError, "INITIAL_CONDITION_SCOPE"):
                store.write_record(manifest, stale)
            record["initial_condition_robustness"] = "ROBUST"
            with self.assertRaisesRegex(ValueError, "INITIAL_CONDITION_SCOPE"):
                store.write_record(manifest, record)

    def test_scope_survives_manifest_record_and_summary_serialization(self):
        rows = [next(row for row in self.canonical.rows if row["pressure_mode"] != "PRESCRIBED_STATIC"),
                next(row for row in self.canonical.rows if row["pressure_mode"] == "PRESCRIBED_STATIC")]
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "results"
            context = executor._synthetic_context(self.canonical, root)
            store = executor.ResultStore(root, self.canonical)
            manifest = store.begin_run(context, 2)
            for row in rows:
                store.write_record(manifest, executor.synthetic_backend_record(row, "BASE", context))
            summary = executor.summarize(store)
            self.assertEqual(manifest["initial_condition_dependence_branch"], "NOT_EVALUATED_NOT_FALSE")
            self.assertEqual(summary["initial_condition_scopes"], {
                "BASELINE_ZERO_STATE_ONLY": 1,
                "DYNAMIC_INITIAL_CONDITION_NOT_APPLICABLE": 1})
            self.assertEqual(summary["dynamic_initial_state_variants"], {
                "ZERO_STATE_BASELINE": 1, "NOT_APPLICABLE_STATIC_ALGEBRAIC": 1})

    def test_matrix_and_graph_scientific_identity_are_unchanged(self):
        matrix = json.loads(executor.MATRIX_PATH.read_text())
        self.assertEqual(matrix["matrix_sha256"],
                         "4bb979181a0e5c672b896c44e3eee9574e28f0abed1d1f5dc227a47214e21717")
        self.assertEqual(len(matrix["rows"]), 1280)
        self.assertEqual(sum(row["case_role"] == "ACTIVE_SCIENTIFIC_CASE" for row in matrix["rows"]), 848)
        self.assertEqual(sum(row["case_role"] == "STRUCTURAL_COMPARATOR" for row in matrix["rows"]), 362)
        self.assertEqual(sum(row["case_role"] == "BOUNDED_STRUCTURAL_CONTROL" for row in matrix["rows"]), 70)

    def test_canonical_classifier_has_no_initial_condition_assertion_input(self):
        parameters = inspect.signature(executor.classify_stage_a_evidence).parameters
        for forbidden in ("initial_condition_disagreement", "initial_condition_robust",
                          "bistability", "initial_condition_partner_ids"):
            self.assertNotIn(forbidden, parameters)


if __name__ == "__main__":
    unittest.main()
