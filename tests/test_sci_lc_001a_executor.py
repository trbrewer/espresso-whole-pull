"""Synthetic-only tests for the prospective SCI-LC-001A Stage-A executor."""
from __future__ import annotations

import inspect
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sci_lc_001a_executor as executor  # noqa: E402
import sci_lc_001a_protocol as protocol  # noqa: E402


class SciLc001aExecutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = executor.CanonicalStore.load()
        cls.plan = executor.build_plan(cls.canonical)
        cls.authority = {
            "schema": executor.AUTHORITY_SCHEMA, "authorization_id": "SYNTHETIC_FIXTURE_ONLY",
            "authorized_head": "SYNTHETIC", "authorized_tree": "SYNTHETIC",
            "matrix_semantic_sha256": cls.canonical.matrix_hash,
            "protocol_artifact_sha256": cls.canonical.protocol_hash,
            "allowed_execution_mode": "execute", "allowed_output_root": "SYNTHETIC",
            "backend": executor.SYNTHETIC_BACKEND,
        }

    def test_denominator_floor_is_fixed_and_not_overridable(self):
        active = next(row for row in self.canonical.rows if row["case_role"] == "ACTIVE_SCIENTIFIC_CASE"
                      and row["pressure_mode"] == "PRESCRIBED_STATIC")
        signature = inspect.signature(protocol.build_gain_record)
        self.assertNotIn("denominator_floor", signature.parameters)
        self.assertEqual(protocol.GAIN_DENOMINATOR_FLOOR, 1e-12)
        for denominator in (1e-13, 1e-12, -1e-12):
            with self.assertRaisesRegex(ValueError, "DENOMINATOR_FLOOR"):
                protocol.build_gain_record(list(self.canonical.rows), active["case_id"],
                    "STATIC_GAIN", "BASE", 1., denominator)
        admitted = protocol.build_gain_record(list(self.canonical.rows), active["case_id"],
            "STATIC_GAIN", "BASE", 1., math.nextafter(1e-12, math.inf))
        self.assertGreater(abs(admitted.denominator), protocol.GAIN_DENOMINATOR_FLOOR)
        for value in (True, float("nan"), float("inf"), -float("inf")):
            with self.assertRaises(ValueError):
                protocol.build_gain_record(list(self.canonical.rows), active["case_id"],
                    "STATIC_GAIN", "BASE", 1., value)
        for override in (0, 1e-20, -1, float("nan"), float("inf")):
            with self.assertRaises(TypeError):
                protocol.build_gain_record(list(self.canonical.rows), active["case_id"],
                    "STATIC_GAIN", "BASE", 1., 1., denominator_floor=override)

    def test_dimensional_and_sector_scaled_flows_are_equivalent(self):
        n, g_ref, dp = 8, 1e-8, 1e-8
        states = ([1.] * n, [0.] + [1.] * 7, [-5e-15] + [1.] * 7,
                  [-5e-13] + [1.] * 7, [-1.] * n)
        for normalized in states:
            dimensional = [value * (g_ref / n) * dp for value in normalized]
            a = protocol.SectorFlowVector(tuple(normalized), n, "SECTOR_SCALED_DIMENSIONLESS")
            b = protocol.SectorFlowVector(tuple(dimensional), n, "DIMENSIONAL_SECTOR_FLOW", g_ref, dp)
            self.assertTrue(all(math.isclose(x, y, rel_tol=1e-15, abs_tol=0.) for x, y in
                                zip(protocol.canonical_sector_q_hat(a), protocol.canonical_sector_q_hat(b))))
            self.assertAlmostEqual(protocol.q_hat_total_from_flow(a), protocol.q_hat_total_from_flow(b))
            for tau in (0., .1):
                def disposition(flow):
                    try:
                        return protocol.evolution_focusing(tau=tau, flow=flow, startup=[1.] * n)
                    except ValueError as exc:
                        return str(exc)
                self.assertEqual(disposition(a), disposition(b))

    def test_flow_threshold_boundaries_and_unsupported_inputs(self):
        for threshold in (protocol.Q_ZERO_THRESHOLD, protocol.REFINED_Q_ZERO_THRESHOLD):
            for factor in (.5, 1., 2.):
                flow = protocol.SectorFlowVector((threshold * factor,) * 8, 8,
                                                  "SECTOR_SCALED_DIMENSIONLESS")
                self.assertTrue(math.isfinite(protocol.q_hat_total_from_flow(flow)))
        with self.assertRaisesRegex(ValueError, "UNTAGGED"):
            protocol.canonical_sector_q_hat([1.] * 8)
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_WHOLE"):
            protocol.canonical_sector_q_hat(protocol.SectorFlowVector((1.,) * 8, 8,
                "WHOLE_NETWORK_SCALED_PER_SECTOR"))
        large = protocol.SectorFlowVector((1e200,) * 8, 8, "SECTOR_SCALED_DIMENSIONLESS")
        self.assertEqual(protocol.canonical_sector_q_hat(large)[0], 1e200)

    def test_public_api_excludes_internal_transport_records(self):
        self.assertNotIn("GainRecord", executor.__all__)
        self.assertNotIn("UncertaintyContract", executor.__all__)
        self.assertNotIn("gain_record", inspect.signature(executor.evaluate_gain_evidence).parameters)
        self.assertNotIn("contract", inspect.signature(executor.evaluate_uncertainty_evidence).parameters)
        self.assertNotIn("structural_control", inspect.signature(executor.classify_stage_a_evidence).parameters)

    def test_graph_is_exact_and_deterministic(self):
        again = executor.build_plan(self.canonical)
        self.assertEqual(self.plan, again)
        self.assertEqual((self.plan["matrix_rows"], self.plan["dynamic_rows"], self.plan["static_rows"]),
                         (1280, 553, 727))
        self.assertEqual((self.plan["dynamic_profile_keys"], self.plan["static_profile_keys"],
                          self.plan["total_keys"]), (2212, 1454, 3666))
        keys = [tuple(key) for key in self.plan["keys"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertFalse(any("AND" in profile for _, profile in keys))
        self.assertFalse(any(case_id.startswith(("D4", "X1")) for case_id, _ in keys))

    def test_output_root_rejects_relative_repository_and_symlink(self):
        with self.assertRaises(ValueError):
            executor.validate_external_output_root(Path("relative"))
        with self.assertRaises(ValueError):
            executor.validate_external_output_root(ROOT / "output")
        with tempfile.TemporaryDirectory() as name:
            base = Path(name); real = base / "real"; real.mkdir(); link = base / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "SYMLINK"):
                executor.validate_external_output_root(link / "results")

    def test_authority_gate_rejects_every_mismatch(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "results"; root.mkdir()
            expected = {**self.authority, "authorized_head": "H", "authorized_tree": "T",
                        "allowed_output_root": str(root)}
            path = Path(name) / "authority.json"; path.write_text(json.dumps(expected))
            values = {("rev-parse", "HEAD"): "H", ("rev-parse", "HEAD^{tree}"): "T",
                      ("status", "--porcelain=v1", "--untracked-files=all"): ""}
            with mock.patch.object(executor, "git_value", side_effect=lambda *x: values[x]):
                accepted = executor.validate_execution_authority(path, root, self.canonical,
                    backend=executor.SYNTHETIC_BACKEND, allow_synthetic_fixture=True)
                self.assertEqual(accepted["authorization_id"], "SYNTHETIC_FIXTURE_ONLY")
                with self.assertRaisesRegex(ValueError, "BACKEND_NOT_AUTHORIZED"):
                    executor.validate_execution_authority(path, root, self.canonical,
                        backend=executor.REAL_BACKEND)
                for key in ("authorized_head", "authorized_tree", "matrix_semantic_sha256",
                            "protocol_artifact_sha256", "allowed_output_root"):
                    broken = dict(expected); broken[key] = "WRONG"; path.write_text(json.dumps(broken))
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        executor.validate_execution_authority(path, root, self.canonical,
                            backend=executor.SYNTHETIC_BACKEND, allow_synthetic_fixture=True)

    def test_execute_requires_authority_before_launcher(self):
        sentinel = mock.Mock(side_effect=AssertionError("canonical launcher reached"))
        with tempfile.TemporaryDirectory() as name, mock.patch.object(executor, "execute_graph", sentinel):
            with self.assertRaises(SystemExit):
                executor.main(["--mode", "execute", "--output-root", name])
        sentinel.assert_not_called()

    def test_synthetic_full_graph_atomic_store_and_resume(self):
        with tempfile.TemporaryDirectory() as name:
            store = executor.ResultStore(Path(name), self.canonical)
            first = executor.execute_graph(self.canonical, store, self.authority,
                executor.SYNTHETIC_BACKEND, interrupt_after=37)
            self.assertEqual((first["completed_now"], first["remaining"]), (37, 3629))
            resumed = executor.execute_graph(self.canonical, store, self.authority,
                                              executor.SYNTHETIC_BACKEND)
            self.assertEqual((resumed["completed_now"], resumed["reused"], resumed["remaining"]),
                             (3629, 37, 0))
            summary = executor.summarize(store)
            self.assertEqual(summary["records"], 3666)
            self.assertEqual(summary["statuses"]["COMPLETE"], 3666)
            self.assertEqual(summary["evidence_kinds"], [executor.SYNTHETIC_BACKEND])
            self.assertFalse(list(Path(name).rglob(".tmp-*.json")))

    def test_authoritative_gain_uncertainty_and_synthetic_classification_block(self):
        with tempfile.TemporaryDirectory() as name:
            results = executor.ResultStore(Path(name), self.canonical)
            executor.execute_graph(self.canonical, results, self.authority, executor.SYNTHETIC_BACKEND)
            active = next(row for row in self.canonical.rows if row["case_role"] == "ACTIVE_SCIENTIFIC_CASE"
                          and row["pressure_mode"] == "PRESCRIBED_STATIC" and
                          row["numerical_resolution_role"] == "PRIMARY")
            gain = executor.evaluate_gain_evidence(self.canonical, results, active["case_id"],
                                                    "STATIC_GAIN", "BASE")
            self.assertEqual(gain["comparator_case_id"], active["comparator_case_id"])
            uncertainty = executor.evaluate_uncertainty_evidence(
                self.canonical, results, active["case_id"], "STATIC_GAIN")
            self.assertEqual(uncertainty["status"], "COMPLETE")
            with self.assertRaisesRegex(ValueError, "SYNTHETIC_EVIDENCE"):
                executor.classify_stage_a_evidence(self.canonical, results, active["case_id"], "STATIC_GAIN")

    def test_static_dispatch_uses_authoritative_profiles_on_synthetic_system(self):
        row = dict(next(row for row in self.canonical.rows if row["pressure_mode"] == "PRESCRIBED_STATIC"))
        row["case_id"] = "SYNTHETIC_TEST_ONLY.static"
        row["row_sha256"] = "SYNTHETIC_TEST_ONLY"
        fake = mock.Mock(); fake.row.return_value = row
        for profile in protocol.STATIC_NUMERICAL_PROFILES:
            record = executor.execute_static_case(fake, row["case_id"], profile,
                                                   self.authority, synthetic=True)
            self.assertEqual(record["status"], "COMPLETE")
            self.assertEqual(record["profile"], profile)
            self.assertEqual(record["linear_solve_status"], "PASS")

    def test_dynamic_orchestration_uses_injected_trivial_ode_only(self):
        row = dict(next(row for row in self.canonical.rows if row["pressure_mode"] == "PRESCRIBED_DYNAMIC_RAMP"
                   and row["resistance_evolution_law"] == "NO_EVOLUTION"))
        row["case_id"] = "SYNTHETIC_TEST_ONLY.dynamic"
        row["row_sha256"] = "SYNTHETIC_TEST_ONLY"
        fake = mock.Mock(); fake.row.return_value = row

        class Solution:
            success = True; message = "synthetic"
            def sol(self, times):
                return [[min(float(t) / .05, 1.) * .5 for t in times]
                        for _ in range(row["sector_count"])]

        calls = []
        def trivial(rhs, interval, y0, **settings):
            calls.append(settings); rhs(0., y0); return Solution()
        for profile in protocol.DYNAMIC_NUMERICAL_PROFILES:
            record = executor.execute_dynamic_case(fake, row["case_id"], profile,
                self.authority, synthetic=True, solve_ivp_impl=trivial)
            self.assertEqual(record["status"], "COMPLETE")
        self.assertEqual(len(calls), 4)
        self.assertFalse(any("AND" in row["profile"] for row in []))

    def test_plan_validate_and_summarize_have_zero_solver_calls(self):
        self.assertEqual(self.plan["solver_calls"], 0)
        with tempfile.TemporaryDirectory() as name:
            with mock.patch.object(executor, "execute_static_case", side_effect=AssertionError), \
                    mock.patch.object(executor, "execute_dynamic_case", side_effect=AssertionError):
                self.assertEqual(executor.main(["--mode", "plan"]), 0)
                self.assertEqual(executor.main(["--mode", "validate", "--output-root", name]), 0)
                self.assertEqual(executor.main(["--mode", "summarize", "--output-root", name]), 0)

    def test_matrix_and_deferral_invariants(self):
        self.assertEqual(self.canonical.matrix_hash,
            "4bb979181a0e5c672b896c44e3eee9574e28f0abed1d1f5dc227a47214e21717")
        self.assertEqual((protocol.D4_STATUS, protocol.X1_STATUS),
            ("DEFERRED_NOT_AUTHORIZED_STAGE_A", "DEFERRED_NOT_AUTHORIZED_STAGE_A"))
        with self.assertRaises(protocol.DeferredStageError): protocol.d4_select_synthetic()
        with self.assertRaises(protocol.DeferredStageError): protocol.x1_select_synthetic()


if __name__ == "__main__":
    unittest.main()
