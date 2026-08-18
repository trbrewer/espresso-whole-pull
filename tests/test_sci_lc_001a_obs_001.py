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
    value = {"accepted_step_index": 2, "candidate_step_index": 3, "simulation_time": .5,
        "profile_order": 0, "sector_index": 1, "event_sequence": 4,
        "lower_distance": .3, "upper_distance": 3.45,
        "state": obs.exact_vector([.1, .2], ["p_0", "x_0"]), "sector": 1,
        "beta": obs.exact_float(2.), "x_i": obs.exact_float(.2),
        "M_i": obs.exact_float(math.exp(.4)), "H_i0": obs.exact_float(1.),
        "H_i": obs.exact_float(math.exp(.4)),
        "tolerances": {"boundary": obs.exact_float(1e-12),
                       "derivative": obs.exact_float(1e-14),
                       "event_root": obs.exact_float(1e-10)},
        "contact_state": "INSIDE", "contact_derivative": None,
        "finite_category": "FINITE"}
    value.update(changes); return value


def key_observer() -> obs.KeyDiagnostics:
    observer = obs.KeyDiagnostics(identity())
    observer.accepted(time=.4, step_index=2, state=[.1, .2], state_names=["p_0", "x_0"])
    observer.candidate(time=.5, candidate_step_index=3, state=[.2, .3],
                       state_names=["p_0", "x_0"])
    observer.observe_margin(sample())
    return observer


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
            trigger={"sector_count": 2, "triggering_sectors": [0, 1], "primary_sector": 0,
                     "parameter_bindings": {}}, root=None,
            sectors=[{"sector": 0, "beta": obs.exact_float(1.), "x_i": obs.exact_float(0.),
                      "beta_x_i": obs.exact_float(0.), "M_i": obs.exact_float(1.),
                      "H_i0": obs.exact_float(1.), "H_i": obs.exact_float(1.)}],
            guard_semantics={"guard_decision": "STOP", "no_clipping": True},
            margins={"lower": obs.exact_float(.75), "upper": obs.exact_float(3.)},
            correlation={"guard": "g", "contact": "c", "event_root": None,
                         "stopped_result": "s", "final_record": "f"})
        obs.validate_record(record); self.assertFalse(record["timeline"]["event_root_present"])

    def test_missing_enum_and_duplicate_rejections(self):
        record = key_observer().completed_record(); del record["minimum"]
        with self.assertRaisesRegex(ValueError, "MISSING_FIELDS"): obs.validate_record(record)
        record = key_observer().completed_record(); record["record_type"] = "BAD"
        with self.assertRaises(ValueError): obs.validate_record(record)
        config = obs.DiagnosticConfig.from_field({"mode": "ENABLED_OPTIONAL", "sidecar_root": "/tmp/obs"})
        run = obs.DiagnosticRun(config, ["a", "b"]); run.entries["a"] = {}; run.entries["b"] = {"scientific_terminal_status":"COMPLETE","expected_record_type":"MULTIPLIER_MARGIN_SUMMARY"}
        health, manifest = run.finalize_objects(); obs.validate_run_object(health); obs.validate_run_object(manifest)


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
