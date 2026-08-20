"""Focused bounded noncanonical qualification for OBS-001."""
from __future__ import annotations

import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sci_lc_001a_obs_001_diagnostics as obs
import sci_lc_001a_executor as executor
import sci_lc_001a_protocol as protocol


def identity() -> dict:
    return {
        "implementation_version": obs.IMPLEMENTATION_VERSION,
        "implementation_sha256": "1" * 64, "configuration_sha256": "2" * 64,
        "repository": "https://github.com/trbrewer/espresso-whole-pull.git",
        "candidate_head": "3" * 40, "candidate_tree": "4" * 40,
        "executor_sha256": "5" * 64, "protocol_source_sha256": "6" * 64,
        "protocol_json_sha256": "7" * 64, "matrix_json_sha256": "8" * 64,
        "matrix_csv_sha256": "9" * 64, "plan_sha256": "a" * 64,
        "backend": "SYNTHETIC_TEST_ONLY", "run_id": "OBS_FIXTURE_RUN",
        "execution_authority": {"identity": "FIXTURE", "sha256": "b" * 64},
        "diagnostic_authority": {"identity": "FIXTURE", "sha256": "c" * 64},
        "key_id": "OBS_FIXTURE_KEY_001", "row_id": "OBS_FIXTURE_ROW_001",
        "arm": "D3-LOC-FIXTURE", "profile": "BASE", "model_variant": "FIXTURE",
        "process_id": 1, "worker_id": "fixture-worker", "attempt_number": 1,
    }


def sample(**changes) -> dict:
    multiplier = math.exp(.4)
    value = {"accepted_step_index": 2, "candidate_step_index": 3,
        "simulation_time": obs.exact_float(.5),
        "profile_order": 0, "sector_index": 1, "event_sequence": 4,
        "lower_distance": obs.exact_float(multiplier - .25),
        "upper_distance": obs.exact_float(4. - multiplier),
        "state": obs.exact_vector([.1, .2], ["p_0", "x_0"]), "sector": 1,
        "beta": obs.exact_float(2.), "x_i": obs.exact_float(.2),
        "M_i": obs.exact_float(multiplier), "H_i0": obs.exact_float(1.),
        "H_i": obs.exact_float(multiplier),
        "tolerances": {"boundary": obs.exact_float(1e-12),
                       "derivative": obs.exact_float(1e-14),
                       "event_root": obs.exact_float(1e-10)},
        "contact_state": "INSIDE", "contact_derivative": None,
        "finite_category": "FINITE"}
    for name in ("simulation_time", "lower_distance", "upper_distance"):
        if name in changes and not isinstance(changes[name], dict):
            changes[name] = obs.exact_float(changes[name])
    value.update(changes); return value


def key_observer() -> obs.KeyDiagnostics:
    observer = obs.KeyDiagnostics(identity())
    observer.accepted(time=.4, step_index=2, state=[.1, .2], state_names=["p_0", "x_0"])
    observer.candidate(time=.5, candidate_step_index=3, state=[.2, .3],
                       state_names=["p_0", "x_0"])
    observer.observe_margin(sample())
    return observer


def stop_record() -> dict:
    return key_observer().stopped_record(
        scientific={"status": "STOPPED", "stop_token": protocol.MULTIPLIER_STOP,
            "finite_category": "FINITE", "contact_category": "EXACT_CONTACT",
            "exited_bound": "UPPER_BOUND", "stop_direction": "OUTWARD"},
        trigger={"sector_count": 2, "triggering_sectors": [0], "primary_sector": 0,
                 "parameter_bindings": {}}, root=None,
        sectors=[{"sector": 0, "beta": obs.exact_float(1.), "x_i": obs.exact_float(math.log(4.)),
            "beta_x_i": obs.exact_float(math.log(4.)), "M_i": obs.exact_float(4.),
            "H_i0": obs.exact_float(1.), "H_i": obs.exact_float(4.),
            "preceding_valid": None, "candidate": None, "event_root": None,
            "lower_bound": obs.exact_float(.25), "upper_bound": obs.exact_float(4.)}],
        guard_semantics={"boundary_tolerance": obs.exact_float(1e-12),
            "derivative_tolerance": obs.exact_float(1e-14),
            "located_root_tolerance": obs.exact_float(1e-10),
            "guard_decision": "STOP", "no_clipping": True},
        margins={"lower": obs.exact_float(3.75), "upper": obs.exact_float(0.),
            "minimum": obs.exact_float(0.),
            "absolute_exceedance": None, "relative_exceedance": None,
            "normalized_interval_exceedance": None},
        correlation={"guard": "g", "contact": "c", "event_root": None,
                     "stopped_result": "s", "final_record": "f"})


def reseal(record: dict) -> dict:
    corrupted = copy.deepcopy(record)
    corrupted.pop("integrity_sha256", None)
    corrupted["record_id"] = obs.record_identity(corrupted)
    corrupted["integrity_sha256"] = obs.digest(corrupted)
    return corrupted


class SchemaSerializationTests(unittest.TestCase):
    def test_exact_float_finite_nonfinite_and_negative_zero(self):
        for value in (0., -0., 1/3, math.inf, -math.inf, math.nan):
            encoded = obs.exact_float(value)
            self.assertEqual(len(encoded["ieee754_hex"]), 16)
            self.assertEqual(encoded["dtype"], "binary64")
        self.assertNotEqual(obs.exact_float(0.)["ieee754_hex"], obs.exact_float(-0.)["ieee754_hex"])

    def test_state_vector_order_and_shape(self):
        vector = obs.exact_vector([1., 2.], ["first", "last"])
        self.assertEqual(vector["shape"], [2]); self.assertEqual(vector["component_order"], ["first", "last"])
        with self.assertRaises(ValueError): obs.exact_vector([1.], ["x", "y"])

    def test_valid_summary_and_deterministic_serialization(self):
        record = key_observer().completed_record(); obs.validate_record(record)
        self.assertEqual(obs.canonical_bytes(record), obs.canonical_bytes(copy.deepcopy(record)))

    def test_valid_stop_event_and_root_absence(self):
        record = key_observer().stopped_record(
            scientific={"status": "STOPPED", "stop_token": protocol.MULTIPLIER_STOP,
                        "finite_category": "FINITE", "contact_category": "EXACT_CONTACT",
                        "exited_bound": "UPPER_BOUND", "stop_direction": "OUTWARD"},
            trigger={"sector_count": 2, "triggering_sectors": [0], "primary_sector": 0,
                     "parameter_bindings": {}}, root=None,
            sectors=[{"sector": 0, "beta": obs.exact_float(1.), "x_i": obs.exact_float(math.log(4.)),
                      "beta_x_i": obs.exact_float(math.log(4.)), "M_i": obs.exact_float(4.),
                      "H_i0": obs.exact_float(1.), "H_i": obs.exact_float(4.),
                      "preceding_valid": None, "candidate": None, "event_root": None,
                      "lower_bound": obs.exact_float(.25), "upper_bound": obs.exact_float(4.)}],
            guard_semantics={"guard_decision": "STOP", "no_clipping": True},
            margins={"lower": obs.exact_float(3.75), "upper": obs.exact_float(0.),
                "minimum": obs.exact_float(0.), "absolute_exceedance": None,
                "relative_exceedance": None, "normalized_interval_exceedance": None},
            correlation={"guard": "g", "contact": "c", "event_root": None,
                         "stopped_result": "s", "final_record": "f"})
        obs.validate_record(record); self.assertFalse(record["timeline"]["event_root_present"])

    def test_missing_enum_and_duplicate_rejections(self):
        record = key_observer().completed_record(); del record["minimum"]
        with self.assertRaisesRegex(ValueError, "MISSING_FIELDS"): obs.validate_record(record)
        record = key_observer().completed_record(); record["record_type"] = "BAD"
        with self.assertRaises(ValueError): obs.validate_record(record)
        config = obs.DiagnosticConfig.from_field({"mode": "ENABLED_OPTIONAL", "sidecar_root": "/tmp/obs"})
        run = obs.DiagnosticRun(config, {"a": obs.NOT_APPLICABLE, "b": obs.NOT_APPLICABLE})
        run.register_not_applicable("a", "COMPLETE"); run.register_not_applicable("b", "COMPLETE")
        health, manifest = run.finalize_objects(); obs.validate_run_object(health); obs.validate_run_object(manifest)


class ApplicabilityAndFreshExecutionTests(unittest.TestCase):
    def test_exact_frozen_plan_applicability_partition(self):
        store = executor.CanonicalStore.load(); plan = executor.build_plan(store)
        static, dynamic, no_evolution, applicable = set(), set(), set(), set()
        for case_id, profile in plan["keys"]:
            row = store.row(case_id); key = case_id + "__" + profile
            if row["pressure_mode"] == "PRESCRIBED_STATIC":
                static.add(key); continue
            dynamic.add(key)
            classification = obs.multiplier_applicability(row["resistance_evolution_law"])
            (no_evolution if classification == obs.NOT_APPLICABLE else applicable).add(key)
        self.assertEqual((plan["total_keys"], len(static), len(dynamic), len(no_evolution), len(applicable)),
                         (3666, 1454, 2212, 1060, 1152))
        self.assertFalse(no_evolution & applicable)
        self.assertEqual(no_evolution | applicable, dynamic)
        self.assertFalse(static & dynamic)

    def test_applicability_depends_only_on_committed_semantics(self):
        self.assertEqual(obs.multiplier_applicability("NO_EVOLUTION"), obs.NOT_APPLICABLE)
        self.assertEqual(obs.multiplier_applicability(
            "SIGNED_LOCAL_FLOW_TO_RESISTANCE_FEEDBACK_SURROGATE"), obs.APPLICABLE)
        with self.assertRaises(ValueError): obs.multiplier_applicability(None)

    def test_not_applicable_has_one_disposition_and_no_multiplier_payload(self):
        config = obs.DiagnosticConfig.from_field({"mode": "ENABLED_REQUIRED", "sidecar_root": "/tmp/obs-r1"})
        run = obs.DiagnosticRun(config, {"no-evolution": obs.NOT_APPLICABLE})
        run.register_not_applicable("no-evolution", "COMPLETE")
        health, manifest = run.finalize_objects()
        entry = manifest["entries"][0]
        self.assertEqual(entry["diagnostic_terminal_status"], obs.NOT_APPLICABLE)
        self.assertIsNone(entry["actual_record_path"]); self.assertTrue(health["clean_finalization"])
        self.assertEqual(health["not_applicable_dispositions"], 1)

    def test_applicable_complete_without_observation_fails_closed(self):
        observer = obs.KeyDiagnostics(identity())
        with self.assertRaisesRegex(ValueError, "MISSING_MARGIN_OBSERVATION"):
            observer.completed_record()

    def test_terminal_dispositions_are_exclusive(self):
        config = obs.DiagnosticConfig.from_field({"mode": "ENABLED_REQUIRED", "sidecar_root": "/tmp/obs-r1"})
        run = obs.DiagnosticRun(config, {"no-evolution": obs.NOT_APPLICABLE})
        run.register_not_applicable("no-evolution", "COMPLETE")
        with self.assertRaisesRegex(ValueError, "DUPLICATE"):
            run.register_not_applicable("no-evolution", "COMPLETE")
        with self.assertRaises(ValueError):
            run.register("no-evolution", "COMPLETE", key_observer().completed_record())

    def test_enabled_modes_reject_reuse_resume_and_stale_sidecar_before_dispatch(self):
        store = executor.CanonicalStore.load()
        for mode in ("ENABLED_OPTIONAL", "ENABLED_REQUIRED"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "results"; output.mkdir()
                (output / "RUN_MANIFEST.json").write_text("{}", encoding="utf-8")
                result_store = executor.ResultStore(output, store)
                config = obs.DiagnosticConfig.from_field({"mode": mode,
                    "sidecar_root": str(Path(directory) / "diagnostics")})
                dispatch = mock.Mock()
                with self.assertRaisesRegex(ValueError, obs.FRESH_EXECUTION_FAILURE):
                    executor._require_fresh_diagnostic_execution(result_store, config)
                dispatch.assert_not_called()
                for request in ({"resume_requested": True}, {"reuse_requested": True},
                                {"prior_manifest_requested": True}):
                    empty = Path(directory) / ("empty-" + next(iter(request)))
                    with self.assertRaisesRegex(ValueError, obs.FRESH_EXECUTION_FAILURE):
                        executor._require_fresh_diagnostic_execution(
                            executor.ResultStore(empty, store), config, **request)
            with self.subTest(mode=mode + "-stale"), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "results"
                sidecar = Path(directory) / "diagnostics"; sidecar.mkdir()
                (sidecar / "stale.json").write_text("{}", encoding="utf-8")
                config = obs.DiagnosticConfig.from_field({"mode": mode, "sidecar_root": str(sidecar)})
                with self.assertRaisesRegex(ValueError, obs.FRESH_EXECUTION_FAILURE):
                    executor._require_fresh_diagnostic_execution(executor.ResultStore(output, store), config)

    def test_disabled_mode_preserves_existing_reuse_path(self):
        store = executor.CanonicalStore.load()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory); (output / "prior").write_text("existing", encoding="utf-8")
            executor._require_fresh_diagnostic_execution(executor.ResultStore(output, store),
                obs.DiagnosticConfig.from_field(None))


class StrictRecursiveSemanticValidationTests(unittest.TestCase):
    def assert_resealed_rejected(self, mutate, pattern=None):
        record = key_observer().completed_record(); mutate(record)
        context = self.assertRaisesRegex(ValueError, pattern) if pattern else self.assertRaises(ValueError)
        with context: obs.validate_record(reseal(record))

    def test_exact_review_probes_reject_after_reseal(self):
        probes = (
            (lambda r: r.__setitem__("minimum", "garbage"), "MINIMUM_OBJECT"),
            (lambda r: r.__setitem__("guard_evaluations", -9), "INTEGER_INVALID"),
            (lambda r: r.__setitem__("backend", "NOT_A_BACKEND"), "ENUM_INVALID"),
        )
        for mutate, pattern in probes:
            with self.subTest(pattern=pattern): self.assert_resealed_rejected(mutate, pattern)

    def test_unknown_missing_and_wrong_nested_values_reject(self):
        probes = (
            lambda r: r["minimum"].__setitem__("unknown", 1),
            lambda r: r["minimum"]["state"].pop("shape"),
            lambda r: r["minimum"].__setitem__("sector", "one"),
            lambda r: r["minimum"].__setitem__("sector", True),
            lambda r: r["execution_authority"].__setitem__("sha256", "bad"),
            lambda r: r.__setitem__("schema", obs.STOP_SCHEMA),
            lambda r: r.__setitem__("record_type", "MULTIPLIER_STOP_EVENT"),
        )
        for index, mutate in enumerate(probes):
            with self.subTest(probe=index): self.assert_resealed_rejected(mutate)

    def test_float_and_state_corruption_reject_after_reseal(self):
        probes = (
            lambda r: r["minimum"]["M_i"].__setitem__("value", 2.),
            lambda r: r["minimum"]["M_i"].__setitem__("ieee754_hex", "garbage"),
            lambda r: r["minimum"]["state"].__setitem__("shape", [99]),
            lambda r: r["minimum"]["state"].__setitem__("component_order", ["x_0", "p_0"]),
            lambda r: r["minimum"].__setitem__("relevant_bound", "UPPER_BOUND"),
            lambda r: r.__setitem__("guard_evaluations", 0),
        )
        for index, mutate in enumerate(probes):
            with self.subTest(probe=index): self.assert_resealed_rejected(mutate)

    def test_stop_sector_and_primary_corruption_reject_after_reseal(self):
        probes = (
            lambda r: r["trigger"].__setitem__("triggering_sectors", [0, 0]),
            lambda r: r["trigger"].__setitem__("primary_sector", 1),
            lambda r: r["states"]["candidate"].__setitem__("shape", [99]),
            lambda r: r["correlation"].pop("guard"),
            lambda r: r["guard_semantics"].__setitem__("unknown", True),
            lambda r: r["trigger"]["parameter_bindings"].__setitem__("unknown", 1),
            lambda r: r["sectors"][0].__setitem__("preceding_valid", {}),
            lambda r: r["sectors"][0].__setitem__("event_root", {"x_i": obs.exact_float(0.),
                "M_i": obs.exact_float(1.)}),
            lambda r: r["margins"].__setitem__("absolute_exceedance", obs.exact_float(1.)),
        )
        for index, mutate in enumerate(probes):
            record = stop_record(); mutate(record)
            with self.subTest(probe=index), self.assertRaises(ValueError): obs.validate_record(reseal(record))

    def test_manifest_health_reconciliation_and_not_applicable_coupling(self):
        config = obs.DiagnosticConfig.from_field({"mode": "ENABLED_REQUIRED", "sidecar_root": "/tmp/obs-r1"})
        run = obs.DiagnosticRun(config, {"n": obs.NOT_APPLICABLE})
        run.register_not_applicable("n", "COMPLETE"); health, manifest = run.finalize_objects()
        mutations = (
            lambda m: m.__setitem__("expected_dynamic_keys", 2),
            lambda m: m["entries"][0].__setitem__("actual_record_path", "/fabricated"),
            lambda m: m["entries"][0].__setitem__("applicability", "INVALID"),
            lambda m: m["entries"][0].__setitem__("validation", "PASS"),
        )
        for mutate in mutations:
            candidate = copy.deepcopy(manifest); mutate(candidate)
            with self.assertRaises(ValueError): obs.validate_run_object(candidate)
        bad_health = copy.deepcopy(health); bad_health["clean_finalization"] = True
        bad_health["missing_identities"] = ["missing"]
        with self.assertRaises(ValueError): obs.validate_run_object(bad_health)
        mismatched_health = copy.deepcopy(health)
        mismatched_health["manifest_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "MANIFEST_HASH_MISMATCH"):
            obs.validate_run_reconciliation(mismatched_health, manifest)

    def test_manifest_order_and_multiplier_stop_token_coupling(self):
        config = obs.DiagnosticConfig.from_field({"mode": "ENABLED_REQUIRED", "sidecar_root": "/tmp/obs-r1"})
        run = obs.DiagnosticRun(config, {"z": obs.NOT_APPLICABLE, "a": obs.NOT_APPLICABLE})
        run.register_not_applicable("z", "COMPLETE")
        run.register_not_applicable("a", "COMPLETE")
        _, manifest = run.finalize_objects()
        self.assertEqual([entry["key_id"] for entry in manifest["entries"]], ["a", "z"])
        candidate = copy.deepcopy(manifest); candidate["entries"].reverse()
        with self.assertRaisesRegex(ValueError, "ENTRY_ORDER"):
            obs.validate_run_object(candidate)
        candidate = copy.deepcopy(manifest)
        candidate["entries"][0]["scientific_terminal_status"] = "STOPPED"
        candidate["entries"][0]["scientific_stop_token"] = protocol.MULTIPLIER_STOP
        candidate["entries"][0]["applicability"] = obs.APPLICABLE
        with self.assertRaises(ValueError):
            obs.validate_run_object(candidate)
        with tempfile.TemporaryDirectory() as directory:
            stop_config = obs.DiagnosticConfig.from_field(
                {"mode": "ENABLED_REQUIRED", "sidecar_root": directory})
            stopped = obs.DiagnosticRun(stop_config, {"OBS_FIXTURE_KEY_001": obs.APPLICABLE})
            stopped.register("OBS_FIXTURE_KEY_001", "STOPPED", stop_record())
            stop_health, stop_manifest = stopped.finalize_objects()
            obs.validate_run_reconciliation(stop_health, stop_manifest)
            missing = copy.deepcopy(stop_manifest["entries"][0])
            missing["actual_record_path"] = None
            stop_manifest["entries"][0] = missing
            with self.assertRaises(ValueError):
                obs.validate_run_object(stop_manifest)


class MarginAndGuardTests(unittest.TestCase):
    def test_minimum_first_middle_final_and_tie_break(self):
        accumulator = obs.MarginAccumulator()
        accumulator.observe(sample(lower_distance=.1, accepted_step_index=5))
        accumulator.observe(sample(lower_distance=.1, accepted_step_index=2, sector_index=2))
        accumulator.observe(sample(lower_distance=.1, accepted_step_index=2, sector_index=1))
        count, minimum = accumulator.summary()
        self.assertEqual(count, 3); self.assertEqual(minimum["sector_index"], 1)

    def test_lower_upper_nearest_exact_contact_and_nonfinite_metadata(self):
        for lower, upper, expected in ((.0, 3.75, "LOWER_BOUND"), (3.75, .0, "UPPER_BOUND")):
            accumulator = obs.MarginAccumulator(); accumulator.observe(sample(lower_distance=lower, upper_distance=upper))
            self.assertEqual(accumulator.summary()[1]["relevant_bound"], expected)
        self.assertEqual(obs.exact_float(math.inf)["finite_category"], "POSITIVE_INFINITY")

    def test_guard_strict_exits_contacts_and_derivative_boundaries(self):
        stop = protocol.MULTIPLIER_STOP
        self.assertEqual(protocol.multiplier_admissibility(.25-2e-12, 1., 0., "ACCEPTED_STEP"), protocol.MULTIPLIER_OUTSIDE_STOP)
        self.assertEqual(protocol.multiplier_admissibility(4+2e-12, 1., 0., "ACCEPTED_STEP"), protocol.MULTIPLIER_OUTSIDE_STOP)
        for multiplier, derivative, expected in ((.25, -2e-14, stop), (.25, 2e-14, "SCIENTIFICALLY_ADMISSIBLE"),
            (4., 2e-14, stop), (4., -2e-14, "SCIENTIFICALLY_ADMISSIBLE"),
            (.25, -1e-14, "SCIENTIFICALLY_ADMISSIBLE"), (4., 1e-14, "SCIENTIFICALLY_ADMISSIBLE")):
            self.assertEqual(protocol.multiplier_admissibility(multiplier, 1., derivative/multiplier, "ACCEPTED_STEP"), expected)

    def test_observer_is_one_way_for_guard_and_contact(self):
        events = []
        base = {"H_i": [1.], "R_floor": .1}
        result = protocol.evolved_resistance_primitives(base, [0.], 1., "AXIALLY_SELF_SIMILAR",
            diagnostic_observer=lambda kind, payload: events.append((kind, payload)) or "IGNORED")
        scientific = protocol.evolved_resistance_primitives(base, [0.], 1., "AXIALLY_SELF_SIMILAR")
        self.assertEqual(result, scientific); self.assertEqual(events[0][0], "RAW_MULTIPLIER_GUARD")

    def test_observer_exception_cannot_change_scientific_guard_result(self):
        base = {"H_i": [1.], "R_floor": .1}
        def broken(_kind, _payload): raise RuntimeError("DIAGNOSTIC_FIXTURE_FAILURE")
        observed = protocol.evolved_resistance_primitives(
            base, [0.], 1., "AXIALLY_SELF_SIMILAR", diagnostic_observer=broken)
        disabled = protocol.evolved_resistance_primitives(base, [0.], 1., "AXIALLY_SELF_SIMILAR")
        self.assertEqual(observed, disabled)
        self.assertEqual(protocol.multiplier_admissibility(.25, 1., 0., "ACCEPTED_STEP",
            diagnostic_observer=broken), "SCIENTIFICALLY_ADMISSIBLE")


class ConfigurationCardinalityFailureTests(unittest.TestCase):
    def test_default_disabled_and_explicit_modes(self):
        disabled = obs.DiagnosticConfig.from_field(None); self.assertFalse(disabled.enabled)
        for mode in ("ENABLED_OPTIONAL", "ENABLED_REQUIRED"):
            config = obs.DiagnosticConfig.from_field({"mode": mode, "sidecar_root": "/tmp/obs-fixture"})
            self.assertTrue(config.enabled); self.assertEqual(config.required, mode == "ENABLED_REQUIRED")
        with self.assertRaises(ValueError): obs.DiagnosticConfig.from_field({"mode": "BAD", "sidecar_root": None})

    def test_atomic_write_no_overwrite_and_manifest_cardinality(self):
        with tempfile.TemporaryDirectory() as directory:
            config = obs.DiagnosticConfig.from_field({"mode": "ENABLED_REQUIRED", "sidecar_root": directory})
            run = obs.DiagnosticRun(config, [identity()["key_id"]])
            record = key_observer().completed_record(); run.register(identity()["key_id"], "COMPLETE", record)
            with self.assertRaises(ValueError): run.register(identity()["key_id"], "COMPLETE", record)
            health, manifest = run.finalize_objects()
            self.assertTrue(health["clean_finalization"]); self.assertEqual(len(manifest["entries"]), 1)
            self.assertEqual(manifest["ordinary_guard_event_stream_count"], 0)

    def test_failure_namespace_reasons_and_incomplete_health(self):
        config = obs.DiagnosticConfig.from_field({"mode": "ENABLED_REQUIRED", "sidecar_root": "/tmp/obs-fixture"})
        for reason in obs.ADMIN_REASONS:
            run = obs.DiagnosticRun(config, ["key"]); run.fail("key", reason, "fixture")
            health, _ = run.finalize_objects(); self.assertFalse(health["clean_finalization"])
            self.assertEqual(health["administrative_failures"][0]["namespace"], obs.ADMIN_FAILURE)

    def test_atomic_rename_failure_does_not_create_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            with mock.patch.object(obs.os, "replace", side_effect=OSError("fixture")):
                with self.assertRaises(OSError): obs.atomic_write_record(path, key_observer().completed_record())
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
