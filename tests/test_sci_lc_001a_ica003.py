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

    def test_f01_closed_label_delimiter_and_collision_barriers(self):
        dynamic = next(row for row in self.canonical.rows if row["pressure_mode"] != "PRESCRIBED_STATIC")
        for label in protocol.STAGE_A_ORDINARY_CLASSIFICATIONS:
            expected = label + ";BASELINE_ZERO_STATE_ONLY"
            self.assertEqual(protocol.qualify_stage_a_classification(dynamic, label), expected)
            self.assertEqual(protocol.qualify_stage_a_classification(dynamic, label), expected)
        for invalid in ("", "UNKNOWN_LABEL", "LATERAL_EQUALIZATION;INJECTED"):
            with self.assertRaisesRegex(ValueError, "INVALID_STAGE_A_REGIME_LABEL"):
                protocol.qualify_stage_a_classification(dynamic, invalid)
        details = {"qualified_classification": "CALLER_SUPPLIED", "marker": "unchanged"}
        before = dict(details)
        with self.assertRaisesRegex(ValueError, "CLASSIFICATION_DERIVED_FIELD_COLLISION"):
            executor._qualified_classification_record(dynamic, "LATERAL_EQUALIZATION", **details)
        self.assertEqual(details, before)
        with mock.patch.object(protocol, "stage_a_initial_condition_scope",
                return_value={"initial_condition_scope": "BAD;SCOPE"}):
            with self.assertRaisesRegex(ValueError, "QUALIFICATION_DELIMITER"):
                protocol.qualify_stage_a_classification(dynamic, "LATERAL_EQUALIZATION")

    def test_f02_all_present_authority_conflicts_reject_before_record_write(self):
        row = next(row for row in self.canonical.rows if row["pressure_mode"] != "PRESCRIBED_STATIC")
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "results"; context = executor._synthetic_context(self.canonical, root)
            store = executor.ResultStore(root, self.canonical); manifest = store.begin_run(context, 1)
            bindings = executor._classification_manifest_bindings(manifest)
            matching = executor.synthetic_backend_record(row, "BASE", context); matching.update(bindings)
            store.write_record(manifest, matching)
            self.assertTrue(store.record_path(row["case_id"], "BASE").is_file())
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "results"; context = executor._synthetic_context(self.canonical, root)
            store = executor.ResultStore(root, self.canonical); manifest = store.begin_run(context, 1)
            absent = executor.synthetic_backend_record(row, "BASE", context)
            absent.pop("authorized_head", None)
            store.write_record(manifest, absent)
            self.assertEqual(json.loads(store.record_path(row["case_id"], "BASE").read_text())[
                "authorized_head"], manifest["git_head"])
        for field in executor.CLASSIFICATION_AUTHORITY_FIELDS:
            with tempfile.TemporaryDirectory() as name:
                root = Path(name) / "results"; context = executor._synthetic_context(self.canonical, root)
                store = executor.ResultStore(root, self.canonical); manifest = store.begin_run(context, 1)
                record = executor.synthetic_backend_record(row, "BASE", context)
                record[field] = "CONFLICT"
                with self.assertRaisesRegex(ValueError, "RESULT_RECORD_AUTHORITY_CONFLICT"):
                    store.write_record(manifest, record)
                self.assertFalse(store.record_path(row["case_id"], "BASE").exists())
            with tempfile.TemporaryDirectory() as name:
                root = Path(name) / "results"; context = executor._synthetic_context(self.canonical, root)
                store = executor.ResultStore(root, self.canonical); manifest = store.begin_run(context, 1)
                record = executor.synthetic_backend_record(row, "BASE", context)
                record[field] = executor._classification_manifest_bindings(manifest)[field]
                store.write_record(manifest, record)
                self.assertTrue(store.record_path(row["case_id"], "BASE").exists())

    def _classification_fixture(self, row, manifest):
        classified = executor._qualified_classification_record(row, "ANALYTICAL_STRUCTURAL_IDENTITY")
        return executor.build_classification_record(self.canonical, manifest, row["case_id"], "BASE",
            classified, allow_synthetic_fixture=True)

    def test_f03_deterministic_store_reload_summary_and_owner_report(self):
        rows = [next(row for row in self.canonical.rows if row["pressure_mode"] != "PRESCRIBED_STATIC"),
                next(row for row in self.canonical.rows if row["pressure_mode"] == "PRESCRIBED_STATIC")]
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "results"; context = executor._synthetic_context(self.canonical, root)
            store = executor.ResultStore(root, self.canonical); manifest = store.begin_run(context, 2)
            records = [self._classification_fixture(row, manifest) for row in rows]
            summary = executor.write_classification_artifacts(self.canonical, store, manifest,
                list(reversed(records)), allow_synthetic_fixture=True)
            paths = executor._classification_artifact_paths(store)
            first = tuple(path.read_bytes() for path in paths)
            executor.write_classification_artifacts(self.canonical, store, manifest, records,
                allow_synthetic_fixture=True)
            self.assertEqual(first, tuple(path.read_bytes() for path in paths))
            loaded = executor.load_classification_records(self.canonical, store, manifest,
                allow_synthetic_fixture=True)
            self.assertEqual(len(loaded), 2)
            self.assertEqual({r["qualified_classification"] for r in loaded}, {
                "ANALYTICAL_STRUCTURAL_IDENTITY;BASELINE_ZERO_STATE_ONLY",
                "ANALYTICAL_STRUCTURAL_IDENTITY;DYNAMIC_INITIAL_CONDITION_NOT_APPLICABLE"})
            self.assertEqual(executor.load_classification_summary(store, loaded), summary)
            report = paths[2].read_text()
            self.assertIn("ANALYTICAL_STRUCTURAL_IDENTITY;BASELINE_ZERO_STATE_ONLY", report)
            self.assertIn("Initial-condition robustness is not adjudicated", report)
            self.assertIn("## Qualified classification counts", report)
            self.assertEqual(summary["total_records"], 2)
            self.assertEqual(sum(summary["ordinary_classification_counts"].values()), 2)
            self.assertEqual(sum(summary["qualified_classification_counts"].values()), 2)
            self.assertEqual(sum(summary["initial_condition_scope_counts"].values()), 2)

    def test_f03_record_and_summary_corruptions_fail_closed(self):
        row = next(row for row in self.canonical.rows if row["pressure_mode"] != "PRESCRIBED_STATIC")
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "results"; context = executor._synthetic_context(self.canonical, root)
            store = executor.ResultStore(root, self.canonical); manifest = store.begin_run(context, 1)
            record = self._classification_fixture(row, manifest)
            corruptions = (
                lambda r: r.pop("initial_condition_scope"),
                lambda r: r.__setitem__("qualified_classification", "MALFORMED"),
                lambda r: r.__setitem__("ordinary_regime_label", "UNKNOWN_LABEL"),
                lambda r: r.__setitem__("authorized_head", "STALE"),
                lambda r: r.__setitem__("stage_a_architecture_id", "ARCHITECTURE_A"),
                lambda r: r.__setitem__("stage", "D4"),
                lambda r: r.__setitem__("case_id", "X1-UNKNOWN"),
            )
            for corrupt in corruptions:
                changed = dict(record); corrupt(changed)
                with self.assertRaises((ValueError, KeyError)):
                    executor.validate_classification_record(self.canonical, manifest, changed,
                        allow_synthetic_fixture=True)
            with self.assertRaisesRegex(ValueError, "DUPLICATE_CLASSIFICATION_KEY"):
                executor.write_classification_artifacts(self.canonical, store, manifest,
                    [record, dict(record)], allow_synthetic_fixture=True)
            with self.assertRaisesRegex(ValueError, "SYNTHETIC_CLASSIFICATION_RECORD"):
                executor.validate_classification_record(self.canonical, manifest, record)
            executor.write_classification_artifacts(self.canonical, store, manifest, [record],
                allow_synthetic_fixture=True)
            records = executor.load_classification_records(self.canonical, store, manifest,
                allow_synthetic_fixture=True)
            summary_path = executor._classification_artifact_paths(store)[1]
            summary = json.loads(summary_path.read_text()); summary["total_records"] = 2
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(ValueError, "COUNT_RECONCILIATION"):
                executor.load_classification_summary(store, records)
            summary["total_records"] = 1; summary["stage_a_architecture_id"] = "ARCHITECTURE_A"
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(ValueError, "SUMMARY_AUTHORITY_INVALID"):
                executor.load_classification_summary(store, records)
            record_path = executor._classification_artifact_paths(store)[0]
            malformed = dict(record); malformed["qualified_classification"] = "CALLER_SUPPLIED"
            record_path.write_text(json.dumps(malformed) + "\n")
            with self.assertRaisesRegex(ValueError, "QUALIFIED_VALUE_MISMATCH"):
                executor.load_classification_records(self.canonical, store, manifest,
                    allow_synthetic_fixture=True)

    def test_f03_diagnostic_and_synthetic_cannot_enter_canonical_export(self):
        row = next(row for row in self.canonical.rows if row["pressure_mode"] != "PRESCRIBED_STATIC")
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "results"; context = executor._synthetic_context(self.canonical, root)
            store = executor.ResultStore(root, self.canonical); manifest = store.begin_run(context, 1)
            classified = executor._qualified_classification_record(row, "ANALYTICAL_STRUCTURAL_IDENTITY")
            with self.assertRaisesRegex(ValueError, "DIRECT_CANONICAL_CLASSIFICATION_BUILDER_MISUSE"):
                executor.build_classification_record(self.canonical, manifest, row["case_id"], "BASE", classified)
            with self.assertRaisesRegex(ValueError, "RUN_CONTEXT_INVALID"):
                executor.export_stage_a_classifications(self.canonical, store)

    def _write_review_only_complete_manifest(self, store):
        plan = executor.build_plan(self.canonical)
        manifest = {"schema": executor.RUN_SCHEMA, "run_id": "REVIEW_ONLY",
            "authorization_id": "REVIEW_ONLY_NONCANONICAL", "git_head": executor.git_value("rev-parse", "HEAD"),
            "git_tree": executor.git_value("rev-parse", "HEAD^{tree}"),
            "matrix_semantic_sha256": self.canonical.matrix_hash,
            "protocol_sha256": self.canonical.protocol_hash,
            "executor_source_sha256": executor.sha256_file(Path(executor.__file__)),
            "execution_mode": "execute", "backend": executor.REAL_BACKEND,
            "evidence_kind": executor.REAL_BACKEND, "output_root": str(store.root),
            "stage_a_architecture_id": protocol.ARCHITECTURE_ID,
            "dynamic_initial_state_variant": protocol.DYNAMIC_INITIAL_STATE_VARIANT,
            "initial_condition_scope": protocol.DYNAMIC_INITIAL_CONDITION_SCOPE,
            "initial_condition_robustness": protocol.NOT_ADJUDICATED_STAGE_A,
            "bistability_status": protocol.NOT_ADJUDICATED_STAGE_A,
            "initial_condition_dependence_branch": protocol.INITIAL_CONDITION_BRANCH_STATUS,
            "task_count": plan["total_keys"], "branch": "REVIEW_ONLY", "started_at_utc": "REVIEW_ONLY",
            "ended_at_utc": "REVIEW_ONLY", "status_counts": {}, "status": "COMPLETE",
            "synthetic_evidence": False}
        manifest["run_manifest_identity_sha256"] = store.manifest_identity(manifest)
        executor.atomic_write_json(store.manifest_path, manifest)
        return manifest

    def test_canonical_publication_requires_validated_run_context(self):
        with tempfile.TemporaryDirectory() as name:
            store = executor.ResultStore(Path(name) / "review-only", self.canonical)
            with self.assertRaisesRegex(ValueError, "RUN_CONTEXT_MISSING"):
                executor.export_stage_a_classifications(self.canonical, store)
            self.assertFalse((store.root / "classifications").exists())

    def test_canonical_publication_requires_eligible_executed_result(self):
        with tempfile.TemporaryDirectory() as name:
            store = executor.ResultStore(Path(name) / "review-only", self.canonical)
            self._write_review_only_complete_manifest(store)
            with self.assertRaisesRegex(ValueError, "RESULT_RECORD_MISSING"):
                executor.export_stage_a_classifications(self.canonical, store)
            self.assertFalse((store.root / "classifications").exists())

    def test_canonical_publication_rejects_missing_result_record(self):
        self.test_canonical_publication_requires_eligible_executed_result()

    def test_canonical_publication_rejects_unexecuted_key(self):
        self.test_canonical_publication_requires_eligible_executed_result()

    def test_canonical_publication_rejects_result_not_in_ledger(self):
        row = next(row for row in self.canonical.rows if row["case_role"] == "ACTIVE_SCIENTIFIC_CASE")
        with tempfile.TemporaryDirectory() as name:
            store = executor.ResultStore(Path(name) / "review-only", self.canonical)
            manifest = self._write_review_only_complete_manifest(store)
            context = executor._synthetic_context(self.canonical, store.root)
            record = executor.synthetic_backend_record(row, "BASE", context)
            record.update({"evidence_kind": executor.REAL_BACKEND, "backend": executor.REAL_BACKEND})
            executor.atomic_write_json(store.record_path(row["case_id"], "BASE"), record)
            with self.assertRaises((FileNotFoundError, ValueError)):
                executor.export_stage_a_classifications(self.canonical, store)
            self.assertEqual(manifest["status"], "COMPLETE")
            self.assertFalse((store.root / "classifications").exists())

    def test_canonical_publication_rejects_result_authority_mismatch(self):
        self.test_canonical_publication_rejects_result_not_in_ledger()

    def test_canonical_publication_rejects_plan_identity_mismatch(self):
        with tempfile.TemporaryDirectory() as name:
            store = executor.ResultStore(Path(name) / "review-only", self.canonical)
            manifest = self._write_review_only_complete_manifest(store)
            manifest["task_count"] -= 1
            manifest["run_manifest_identity_sha256"] = store.manifest_identity(manifest)
            executor.atomic_write_json(store.manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "RUN_CONTEXT_INVALID"):
                executor.export_stage_a_classifications(self.canonical, store)

    def test_canonical_publication_rejects_caller_derived_fields(self):
        row = next(row for row in self.canonical.rows if row["case_role"] == "ACTIVE_SCIENTIFIC_CASE")
        classification = executor._qualified_classification_record(row, "LATERAL_EQUALIZATION")
        invalid_context = {"evidence_kind": executor.REAL_BACKEND}
        before = dict(invalid_context)
        with self.assertRaisesRegex(ValueError, "DIRECT_CANONICAL_CLASSIFICATION_BUILDER_MISUSE"):
            executor.build_classification_record(self.canonical, invalid_context,
                row["case_id"], "BASE", classification)
        self.assertEqual(invalid_context, before)

    def test_canonical_publication_rejects_diagnostic_evidence(self):
        self.test_f03_diagnostic_and_synthetic_cannot_enter_canonical_export()

    def test_canonical_publication_rejects_synthetic_evidence(self):
        self.test_f03_diagnostic_and_synthetic_cannot_enter_canonical_export()

    def test_canonical_publication_rejects_d4_evidence(self):
        with self.assertRaisesRegex(protocol.DeferredStageError, protocol.D4_AUTHORITY_STOP):
            protocol.d4_select_synthetic([])

    def test_canonical_publication_rejects_x1_evidence(self):
        with self.assertRaisesRegex(protocol.DeferredStageError, "DEFERRED_NOT_AUTHORIZED"):
            protocol.x1_select_synthetic([])

    def test_canonical_publication_failure_leaves_no_partial_artifacts(self):
        row = next(row for row in self.canonical.rows if row["case_role"] == "ACTIVE_SCIENTIFIC_CASE")
        classification = executor._qualified_classification_record(row, "LATERAL_EQUALIZATION")
        with tempfile.TemporaryDirectory() as name:
            store = executor.ResultStore(Path(name) / "review-only", self.canonical)
            invalid_context = {"evidence_kind": executor.REAL_BACKEND}
            with self.assertRaisesRegex(ValueError, "DIRECT_CANONICAL_CLASSIFICATION_WRITER_MISUSE"):
                executor.write_classification_artifacts(self.canonical, store, invalid_context, [classification])
            paths = executor._classification_artifact_paths(store)
            self.assertTrue(all(not path.exists() for path in paths))
            self.assertFalse((store.root / "classifications").exists())

    def test_noncanonical_fixture_cannot_claim_canonical_status(self):
        row = next(row for row in self.canonical.rows if row["case_role"] == "ACTIVE_SCIENTIFIC_CASE")
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "fixture"; context = executor._synthetic_context(self.canonical, root)
            store = executor.ResultStore(root, self.canonical); manifest = store.begin_run(context, 1)
            record = self._classification_fixture(row, manifest)
            self.assertEqual(record["scientific_admissibility"], "SYNTHETIC_TEST_ONLY_INADMISSIBLE")
            with self.assertRaisesRegex(ValueError, "DIRECT_CANONICAL_CLASSIFICATION_WRITER_MISUSE"):
                executor.write_classification_artifacts(self.canonical, store, manifest, [record])

    def test_report_uses_validated_classifications_without_reclassification(self):
        with mock.patch.object(executor, "classify_stage_a_evidence", side_effect=AssertionError):
            self.test_f03_deterministic_store_reload_summary_and_owner_report()

    def test_qualified_classification_survives_owner_report(self):
        self.test_f03_deterministic_store_reload_summary_and_owner_report()


if __name__ == "__main__":
    unittest.main()
