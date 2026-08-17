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
            "backend": executor.SYNTHETIC_BACKEND, "executor_source_sha256": executor.sha256_file(Path(executor.__file__)),
            "evidence_kind": executor.SYNTHETIC_BACKEND,
        }

    def synthetic_context(self, root):
        return executor._synthetic_context(self.canonical, Path(root))

    def real_context(self, root, evidence=executor.REAL_BACKEND,
                     mode="execute"):
        material = {"authorization_id": "SENTINEL_AUTHORITY_ONLY", "authorized_head": "H",
            "authorized_tree": "T", "matrix_hash": self.canonical.matrix_hash,
            "protocol_hash": self.canonical.protocol_hash,
            "executor_identity": executor.sha256_file(Path(executor.__file__)),
            "execution_mode": mode, "backend": executor.REAL_BACKEND,
            "evidence_kind": evidence, "output_root": str(root)}
        return executor._ValidatedExecutionContext(**material,
            run_id=executor.sha256_bytes(executor.canonical_json(material).encode())[:24])

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
        self.assertNotIn("execute_static_case", executor.__all__)
        self.assertNotIn("execute_dynamic_case", executor.__all__)
        self.assertIn("execute_authorized_graph", executor.__all__)

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
                self.assertEqual(accepted.authorization_id, "SYNTHETIC_FIXTURE_ONLY")
                with self.assertRaisesRegex(ValueError, "BACKEND_NOT_AUTHORIZED"):
                    executor.validate_execution_authority(path, root, self.canonical,
                        backend=executor.REAL_BACKEND)
                for key in ("authorized_head", "authorized_tree", "matrix_semantic_sha256",
                            "protocol_artifact_sha256", "allowed_output_root", "executor_source_sha256",
                            "evidence_kind"):
                    broken = dict(expected); broken[key] = "WRONG"; path.write_text(json.dumps(broken))
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        executor.validate_execution_authority(path, root, self.canonical,
                            backend=executor.SYNTHETIC_BACKEND, allow_synthetic_fixture=True)

    def test_execute_requires_authority_before_launcher(self):
        sentinel = mock.Mock(side_effect=AssertionError("canonical launcher reached"))
        with tempfile.TemporaryDirectory() as name, mock.patch.object(executor, "execute_authorized_graph", sentinel):
            with self.assertRaises(SystemExit):
                executor.main(["--mode", "execute", "--output-root", name])
        sentinel.assert_not_called()
        static=next(r for r in self.canonical.rows if r["pressure_mode"]=="PRESCRIBED_STATIC")
        dynamic=next(r for r in self.canonical.rows if r["pressure_mode"]!="PRESCRIBED_STATIC")
        with self.assertRaisesRegex(ValueError,"VALIDATED_EXECUTION_CONTEXT"):
            executor._execute_static_case(self.canonical,static["case_id"],"BASE",{})
        with self.assertRaisesRegex(ValueError,"VALIDATED_EXECUTION_CONTEXT"):
            executor._execute_dynamic_case(self.canonical,dynamic["case_id"],"BASE",{})

    def test_public_real_execution_has_no_launcher_injection(self):
        signature = inspect.signature(executor.execute_authorized_graph)
        for name in ("real_launcher", "launcher", "case_runner", "callback", "executor_callback"):
            self.assertNotIn(name, signature.parameters)
            with self.assertRaises(TypeError):
                executor.execute_authorized_graph(execution_authority_path=Path("/missing"),
                    output_root=Path("/tmp/missing"), **{name: mock.Mock()})
        self.assertNotIn("_execute_canonical_case", executor.__all__)

    def test_canonical_dispatch_is_fixed_by_row_mode(self):
        static = next(row for row in self.canonical.rows if row["pressure_mode"] == "PRESCRIBED_STATIC")
        dynamic = next(row for row in self.canonical.rows if row["pressure_mode"] != "PRESCRIBED_STATIC")
        context = self.real_context("/tmp")
        static_result = {"status": "COMPLETE", "evidence_kind": executor.REAL_BACKEND}
        dynamic_result = {"status": "COMPLETE", "evidence_kind": executor.REAL_BACKEND}
        with mock.patch.object(executor, "_execute_static_case", return_value=static_result) as static_call, \
             mock.patch.object(executor, "_execute_dynamic_case", return_value=dynamic_result) as dynamic_call:
            self.assertIs(executor._execute_canonical_case(self.canonical, static, "BASE", context), static_result)
            static_call.assert_called_once(); dynamic_call.assert_not_called()
            static_call.reset_mock()
            self.assertIs(executor._execute_canonical_case(self.canonical, dynamic, "BASE", context), dynamic_result)
            dynamic_call.assert_called_once(); static_call.assert_not_called()
            with self.assertRaisesRegex(ValueError, "PROFILE_NOT_AUTHORIZED"):
                executor._execute_canonical_case(self.canonical, static, "INTEGRATOR_REFINED", context)

    def test_synthetic_injection_cannot_write_real_evidence(self):
        with tempfile.TemporaryDirectory() as name:
            context = self.synthetic_context(name)
            store = executor.ResultStore(Path(name), self.canonical)
            def forged(row, profile, _context):
                return {**executor.synthetic_backend_record(row, profile, context),
                        "evidence_kind": executor.REAL_BACKEND}
            with self.assertRaisesRegex(ValueError, "SYNTHETIC_RUNNER_EVIDENCE"):
                executor._execute_graph_synthetic_test_only(
                    self.canonical, store, context, interrupt_after=1, test_runner=forged)

    def test_synthetic_full_graph_atomic_store_and_resume(self):
        with tempfile.TemporaryDirectory() as name:
            store = executor.ResultStore(Path(name), self.canonical)
            context = self.synthetic_context(name)
            first = executor._execute_graph_synthetic_test_only(
                self.canonical, store, context, interrupt_after=37)
            self.assertEqual((first["completed_now"], first["remaining"]), (37, 3629))
            resumed = executor._execute_graph_synthetic_test_only(self.canonical, store, context)
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
            executor._execute_graph_synthetic_test_only(
                self.canonical, results, self.synthetic_context(name))
            active = next(row for row in self.canonical.rows if row["case_role"] == "ACTIVE_SCIENTIFIC_CASE"
                          and row["pressure_mode"] == "PRESCRIBED_STATIC" and
                          row["numerical_resolution_role"] == "PRIMARY")
            gain = executor.evaluate_gain_evidence(self.canonical, results, active["case_id"],
                                                    "G_static_H", "BASE")
            self.assertEqual(gain["comparator_case_id"], active["comparator_case_id"])
            uncertainty = executor.evaluate_uncertainty_evidence(
                self.canonical, results, active["case_id"], "G_static_H")
            self.assertEqual(uncertainty["status"], "COMPLETE")
            with self.assertRaisesRegex(ValueError, "SYNTHETIC_EVIDENCE"):
                executor.classify_stage_a_evidence(self.canonical, results, active["case_id"])
            path=results.record_path(active["case_id"],"BASE"); original=json.loads(path.read_text())
            tampered=dict(original); tampered["metric_primitives"]={**tampered["metric_primitives"],"H_q_static":9.}
            body=dict(tampered); body.pop("output_checksum")
            tampered["output_checksum"]=executor.sha256_bytes(executor.canonical_json(body).encode())
            path.write_text(json.dumps(tampered))
            with self.assertRaisesRegex(ValueError,"MANIFEST_CHECKSUM"):
                executor.summarize(results)
            with self.assertRaisesRegex(ValueError,"MANIFEST_CHECKSUM"):
                executor.evaluate_gain_evidence(self.canonical,results,active["case_id"],"G_static_H","BASE")

    def test_static_dispatch_uses_authoritative_profiles_on_synthetic_system(self):
        row = dict(next(row for row in self.canonical.rows if row["pressure_mode"] == "PRESCRIBED_STATIC"))
        row["case_id"] = "SYNTHETIC_TEST_ONLY.static"
        row["row_sha256"] = "SYNTHETIC_TEST_ONLY"
        fake = mock.Mock(); fake.row.return_value = row
        for profile in protocol.STATIC_NUMERICAL_PROFILES:
            record = executor._execute_static_case(fake, row["case_id"], profile,
                                                   self.synthetic_context("/tmp"), synthetic=True)
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
            record = executor._execute_dynamic_case(fake, row["case_id"], profile,
                self.synthetic_context("/tmp"), synthetic=True, solve_ivp_impl=trivial)
            self.assertEqual(record["status"], "COMPLETE")
        self.assertEqual(len(calls), 4)
        self.assertFalse(any("AND" in row["profile"] for row in []))

    def test_plan_validate_and_summarize_have_zero_solver_calls(self):
        self.assertEqual(self.plan["solver_calls"], 0)
        with tempfile.TemporaryDirectory() as name:
            with mock.patch.object(executor, "_execute_static_case", side_effect=AssertionError), \
                    mock.patch.object(executor, "_execute_dynamic_case", side_effect=AssertionError):
                self.assertEqual(executor.main(["--mode", "plan"]), 0)
                self.assertEqual(executor.main(["--mode", "validate", "--output-root", name]), 0)
                self.assertEqual(executor.main(["--mode", "summarize", "--output-root", name]), 0)

    def test_matrix_and_deferral_invariants(self):
        self.assertEqual(self.canonical.matrix_hash,
            "4bb979181a0e5c672b896c44e3eee9574e28f0abed1d1f5dc227a47214e21717")
        self.assertEqual((protocol.D4_STATUS, protocol.X1_STATUS),
                         ("DEFERRED_NOT_AUTHORIZED", "DEFERRED_NOT_AUTHORIZED"))
        with self.assertRaises(protocol.DeferredStageError): protocol.d4_select_synthetic()
        with self.assertRaises(protocol.DeferredStageError): protocol.x1_select_synthetic()

    def test_owner_hq_and_seeded_amplitudes(self):
        self.assertEqual(protocol.outlet_heterogeneity_from_fractions([.25] * 4), 0.)
        self.assertEqual(protocol.outlet_heterogeneity_from_fractions([1., 0., 0., 0.]), .75)
        base = [.45, .30, .15, .10]
        self.assertEqual(protocol.outlet_heterogeneity_from_fractions(base),
                         protocol.outlet_heterogeneity_from_fractions(base[1:] + base[:1]))
        self.assertEqual(protocol.outlet_heterogeneity_from_fractions(base),
                         protocol.outlet_heterogeneity_from_fractions(list(reversed(base))))
        n, m = 8, 1
        cosine = [math.cos(2 * math.pi * m * i / n) for i in range(n)]
        sine = [math.sin(2 * math.pi * m * i / n) for i in range(n)]
        self.assertAlmostEqual(protocol.seeded_pattern_amplitude(cosine, pattern="FOURIER", mode="1"), 1.)
        self.assertAlmostEqual(protocol.seeded_pattern_amplitude(sine, pattern="FOURIER", mode="1"), 1.)
        nyquist = [(-1.) ** i for i in range(n)]
        self.assertAlmostEqual(protocol.seeded_pattern_amplitude(nyquist, pattern="FOURIER", mode="4"), 1.)
        for mode in ("0", "5", "bad"):
            with self.assertRaises(ValueError):
                protocol.seeded_pattern_amplitude(cosine, pattern="FOURIER", mode=mode)
        self.assertEqual(protocol.seeded_pattern_amplitude([0.] * 8, pattern="UNIFORM", mode="0"), protocol.NA)

    def test_owner_nonfourier_seed_and_trapezoid(self):
        seed = protocol.pattern_values(8, "CONTIGUOUS_BLOCK", "BLOCK_HALF")
        mean = sum(seed) / 8; centered = [x - mean for x in seed]
        departures = [.3 * x for x in centered]
        self.assertAlmostEqual(protocol.seeded_pattern_amplitude(departures,
            pattern="CONTIGUOUS_BLOCK", mode="BLOCK_HALF"), .3)
        values = [(i / 1000) ** 2 for i in range(1001)]
        expected = (1 / 1000) * (.5 * values[0] + sum(values[1:-1]) + .5 * values[-1])
        self.assertEqual(protocol.composite_trapezoid(values), expected)
        self.assertNotEqual(protocol.composite_trapezoid(values), sum(values))

    def test_metric_dispatch_and_sampling_reconstruction_are_distinct(self):
        record={"status":"COMPLETE","evidence_kind":executor.SYNTHETIC_BACKEND,
                "metric_primitives":{"H_q_static":.2,"A_seeded":.3,
                    "H_q_endpoint":.4,"H_q_integral_1001":.5}}
        expected={"G_static_H":.2,"G_static_mode":.3,"G_coupling_end":.4,"G_coupling_int":.5}
        for name,value in expected.items(): self.assertEqual(executor._metric_value(record,name),value)
        with self.assertRaisesRegex(ValueError,"UNKNOWN_SCIENTIFIC_METRIC"):
            executor._metric_value(record,"UNKNOWN")
        row=dict(next(r for r in self.canonical.rows if r["pressure_mode"]=="PRESCRIBED_DYNAMIC_RAMP"
                      and r["resistance_evolution_law"]=="NO_EVOLUTION"))
        n=row["sector_count"]
        base=protocol.resistance_primitives(n,row["heterogeneity_pattern"],row["heterogeneity_mode"],
            row["resistance_contrast"],row["axial_placement"],row["epsilon_floor"],row["initial_condition_variant"])
        storage=[float(row["hydraulic_storage_C_h"])]*n
        startup=protocol.startup_focusing(base,storage,row["pressure_mode"])
        def dense(times):
            return [[(1+i*.08)*t + (n-i)*.03*t*t for t in times] for i in range(n)]
        values1001,i1001=executor._dynamic_hq_grid(row,base,storage,startup,dense,1001)
        values2001,i2001=executor._dynamic_hq_grid(row,base,storage,startup,dense,2001)
        self.assertEqual((len(values1001),len(values2001)),(1001,2001))
        self.assertNotEqual(i1001,i2001)
        self.assertEqual(i1001,protocol.composite_trapezoid(values1001))
        evolving=dict(next(r for r in self.canonical.rows if r["pressure_mode"]=="PRESCRIBED_DYNAMIC_RAMP"
                           and r["resistance_evolution_law"]!="NO_EVOLUTION"
                           and r["axial_placement"]=="DOWNSTREAM_LOCALIZED"))
        en=evolving["sector_count"]
        ebase=protocol.resistance_primitives(en,evolving["heterogeneity_pattern"],evolving["heterogeneity_mode"],
            evolving["resistance_contrast"],evolving["axial_placement"],evolving["epsilon_floor"],evolving["initial_condition_variant"])
        estorage=[float(evolving["hydraulic_storage_C_h"])]*en
        estartup=protocol.startup_focusing(ebase,estorage,evolving["pressure_mode"])
        def evolving_dense(times):
            pressures=[[(1+i*.1)*t for t in times] for i in range(en)]
            feedback=[[(i-en/2)*.02*t for t in times] for i in range(en)]
            return pressures+feedback
        _, evolved_integral=executor._dynamic_hq_grid(evolving,ebase,estorage,estartup,evolving_dense,1001)
        frozen=dict(evolving); frozen["resistance_evolution_law"]="NO_EVOLUTION"
        _, frozen_integral=executor._dynamic_hq_grid(frozen,ebase,estorage,estartup,evolving_dense,1001)
        self.assertNotEqual(evolved_integral,frozen_integral)

    def test_dynamic_rhs_core_parity_profiles_and_modes(self):
        for mode in ("PRESCRIBED_DYNAMIC_RAMP","MACHINE_COUPLED"):
            row=dict(next(r for r in self.canonical.rows if r["pressure_mode"]==mode
                          and r["resistance_evolution_law"]=="NO_EVOLUTION"))
            n=row["sector_count"]
            base=protocol.resistance_primitives(n,row["heterogeneity_pattern"],row["heterogeneity_mode"],
                row["resistance_contrast"],row["axial_placement"],row["epsilon_floor"],row["initial_condition_variant"])
            storage=[float(row["hydraulic_storage_C_h"])]*n
            startup=protocol.startup_focusing(base,storage,mode)
            state=[.2+.01*i for i in range(n)]+([.6] if mode=="MACHINE_COUPLED" else [])
            base_rhs,diag=executor._dynamic_rhs_core(row,"BASE",.2,state,base,storage,startup)
            startup_rhs,_=executor._dynamic_rhs_core(row,"STARTUP_REFINED",.2,state,base,storage,startup)
            integrator_rhs,_=executor._dynamic_rhs_core(row,"INTEGRATOR_REFINED",.2,state,base,storage,startup)
            self.assertEqual(base_rhs,startup_rhs); self.assertEqual(base_rhs,integrator_rhs)
            self.assertEqual(len(diag["outlet_flow"]),n)
            self.assertIsNotNone(diag["basket_pressure"])
        signed={}
        for label in ("EQUALIZING","LOCALIZING"):
            row=dict(next(r for r in self.canonical.rows if r["pressure_mode"]=="PRESCRIBED_DYNAMIC_RAMP"
                          and r["feedback_sign"]==label))
            n=row["sector_count"]
            base=protocol.resistance_primitives(n,row["heterogeneity_pattern"],row["heterogeneity_mode"],
                row["resistance_contrast"],row["axial_placement"],row["epsilon_floor"],row["initial_condition_variant"])
            storage=[float(row["hydraulic_storage_C_h"])]*n
            startup=protocol.startup_focusing(base,storage,row["pressure_mode"])
            state=[.2+.02*i for i in range(n)]+[0.]*n
            rhs,diag=executor._dynamic_rhs_core(row,"BASE",.2,state,base,storage,startup)
            self.assertTrue(all(math.isfinite(x) for x in rhs)); self.assertIsNotNone(diag["focusing"])
            signed[label]=rhs[-n:]
        self.assertTrue(any(a*b<0 for a,b in zip(signed["EQUALIZING"],signed["LOCALIZING"])))

    def test_static_assembly_parity(self):
        row = dict(next(r for r in self.canonical.rows if r["pressure_mode"] == "PRESCRIBED_STATIC"))
        matrix, rhs, aux = executor.assemble_static_system(row)
        n = row["sector_count"]
        self.assertEqual(len(matrix), n); self.assertEqual(len(rhs), n)
        for i in range(n):
            self.assertAlmostEqual(matrix[i][i], 1 / aux["primitives"]["R_u_i"][i] + aux["gd"][i] + 2 * aux["ge"])
            self.assertAlmostEqual(matrix[i][(i - 1) % n], -aux["ge"])
            self.assertAlmostEqual(matrix[i][(i + 1) % n], -aux["ge"])

    def test_evolved_final_primitives_use_current_x(self):
        row = dict(next(r for r in self.canonical.rows if r["resistance_evolution_law"] != "NO_EVOLUTION"
                        and r["axial_placement"] == "DOWNSTREAM_LOCALIZED"))
        base = protocol.resistance_primitives(row["sector_count"], row["heterogeneity_pattern"],
            row["heterogeneity_mode"], row["resistance_contrast"], row["axial_placement"],
            row["epsilon_floor"], row["initial_condition_variant"])
        evolved = executor._evolved_primitives(row, base, [.2] * row["sector_count"])
        self.assertNotEqual(evolved["R_d_i"], base["R_d_i"])
        control = dict(row); control["resistance_evolution_law"] = "NO_EVOLUTION"
        self.assertEqual(executor._evolved_primitives(control, base, [])["R_d_i"], base["R_d_i"])

    def test_manifest_binding_rejects_recomputed_tamper(self):
        with tempfile.TemporaryDirectory() as name:
            store = executor.ResultStore(Path(name), self.canonical); context = self.synthetic_context(name)
            executor._execute_graph_synthetic_test_only(
                self.canonical, store, context, interrupt_after=1)
            manifest = store.load_manifest(); case_id, profile = map(str, self.plan["keys"][0])
            path = store.record_path(case_id, profile); record = json.loads(path.read_text())
            self.assertTrue(store.reusable(manifest, case_id, profile))
            for field in ("authorization_id", "authorized_head", "authorized_tree",
                          "matrix_semantic_sha256", "protocol_sha256", "executor_source_sha256",
                          "backend", "evidence_kind", "run_id", "metric_primitives"):
                broken = dict(record); broken[field] = "STALE"
                body = dict(broken); body.pop("output_checksum")
                broken["output_checksum"] = executor.sha256_bytes(executor.canonical_json(body).encode())
                path.write_text(json.dumps(broken))
                with self.subTest(field=field), self.assertRaises(ValueError):
                    store.read_bound_record(manifest, case_id, profile)
                path.write_text(json.dumps(record))

    def test_terminal_event_never_continues_or_counts_diagnostic_rhs(self):
        row = dict(next(r for r in self.canonical.rows if r["pressure_mode"] == "PRESCRIBED_DYNAMIC_RAMP"
                        and r["resistance_evolution_law"] != "NO_EVOLUTION"))
        row.update(case_id="SYNTHETIC_TEST_ONLY.event", row_sha256="SYNTHETIC_TEST_ONLY")
        fake = mock.Mock(); fake.row.return_value = row
        n = row["sector_count"]; state_len = 2 * n
        class Solution:
            success=True; message="event"; nfev=1
            t_events=([.2],) + tuple([] for _ in range(2*n-1))
            event_state=[0.] * state_len
            event_state[n]=math.log(.25)/float(row["feedback_gain"])
            y_events=([event_state],) + tuple([] for _ in range(2*n-1))
            def sol(self, times):
                if max(times) > .2: raise AssertionError("dense output beyond terminal")
                return [[0. for _ in times] for _ in range(state_len)]
        def solver(rhs, interval, y0, **kwargs): rhs(0., y0); return Solution()
        record = executor._execute_dynamic_case(fake, row["case_id"], "BASE", self.synthetic_context("/tmp"),
                                                 synthetic=True, solve_ivp_impl=solver)
        self.assertEqual(record["status"], "STOPPED"); self.assertEqual(record["rhs_evaluations"], 1)

    def test_no_event_none_and_absent_results_process_with_actual_nfev(self):
        row = dict(next(r for r in self.canonical.rows if r["pressure_mode"] == "PRESCRIBED_DYNAMIC_RAMP"
                        and r["resistance_evolution_law"] == "NO_EVOLUTION"))
        row.update(case_id="DIAGNOSTIC_FIXTURE_ONLY.no_event", row_sha256="DIAGNOSTIC_FIXTURE_ONLY")
        fake = mock.Mock(); fake.row.return_value = row; n = row["sector_count"]
        def make_solver(with_none):
            class Solution:
                success = True; message = "complete"; nfev = 1
                if with_none:
                    t_events = None; y_events = None
                @staticmethod
                def sol(times):
                    return [[float(t) for t in times] for _ in range(n)]
            def solver(rhs, interval, y0, **kwargs):
                self.assertEqual(kwargs["first_step"], protocol.DYNAMIC_FIRST_STEP)
                rhs(0., y0); return Solution()
            return solver
        for with_none in (False, True):
            record = executor._execute_dynamic_case(fake, row["case_id"], "BASE",
                self.synthetic_context("/tmp"), synthetic=True, solve_ivp_impl=make_solver(with_none))
            self.assertEqual(record["status"], "COMPLETE")
            self.assertEqual(record["rhs_evaluations"], 1)

    def test_event_result_structure_failure_retains_actual_nfev(self):
        row = dict(next(r for r in self.canonical.rows if r["pressure_mode"] == "PRESCRIBED_DYNAMIC_RAMP"
                        and r["resistance_evolution_law"] != "NO_EVOLUTION"))
        row.update(case_id="DIAGNOSTIC_FIXTURE_ONLY.bad_events", row_sha256="DIAGNOSTIC_FIXTURE_ONLY")
        fake = mock.Mock(); fake.row.return_value = row
        class Solution:
            success=True; message="complete"; nfev=1; t_events=(); y_events=(); sol=mock.Mock()
        def solver(rhs, interval, y0, **kwargs): rhs(0., y0); return Solution()
        record = executor._execute_dynamic_case(fake, row["case_id"], "BASE",
            self.synthetic_context("/tmp"), synthetic=True, solve_ivp_impl=solver)
        self.assertEqual(record["stop_disposition"], "EVENT_RESULT_STRUCTURE_INCONSISTENT")
        self.assertEqual(record["rhs_evaluations"], 1)

    def test_real_scipy_fixture_startup_and_no_event_regressions(self):
        ids = ("SCI-LC-001A.d2.00b933e6816e891dc7e28a89",
               "SCI-LC-001A.d3meq.0061cf3ba15ffea327832067",
               "SCI-LC-001A.d3mloc.04e0df973f29194ff1b2ee60",
               "SCI-LC-001A.d3meq.505047457ab446cc447eef02")
        for case_id in ids:
            row = dict(self.canonical.row(case_id)); row.update(
                case_id="DIAGNOSTIC_FIXTURE_ONLY." + case_id, row_sha256="DIAGNOSTIC_FIXTURE_ONLY")
            fake = mock.Mock(); fake.row.return_value = row
            profiles = protocol.DYNAMIC_NUMERICAL_PROFILES if "d2." in case_id else ("BASE", "STARTUP_REFINED")
            for profile in profiles:
                record = executor._execute_dynamic_case(fake, row["case_id"], profile,
                    self.synthetic_context("/tmp"), synthetic=True)
                self.assertEqual(record["status"], "COMPLETE")
                self.assertGreater(record["rhs_evaluations"], 3)

    def test_persistent_zero_flow_still_stops_after_startup_window(self):
        row = dict(next(r for r in self.canonical.rows if r["pressure_mode"] == "PRESCRIBED_DYNAMIC_RAMP"
                        and r["resistance_evolution_law"] != "NO_EVOLUTION"))
        row.update(case_id="DIAGNOSTIC_FIXTURE_ONLY.persistent_zero", row_sha256="DIAGNOSTIC_FIXTURE_ONLY")
        fake = mock.Mock(); fake.row.return_value = row
        def solver(rhs, interval, y0, **kwargs):
            rhs(0., y0)
            rhs(2 * protocol.REFINED_STARTUP_TAU_MAX, y0)
            raise AssertionError("persistent zero did not stop")
        record = executor._execute_dynamic_case(fake, row["case_id"], "STARTUP_REFINED",
            self.synthetic_context("/tmp"), synthetic=True, solve_ivp_impl=solver)
        self.assertEqual(record["status"], "STOPPED")
        self.assertIn("ZERO_TOTAL_FLOW", record["stop_disposition"])
        self.assertEqual(record["rhs_evaluations"], 2)

    def test_pilot_adapter_unknown_exception_count_is_not_zero(self):
        row = next(item for item in self.canonical.rows if item["pressure_mode"] != "PRESCRIBED_STATIC")
        context = self.real_context("/tmp", executor.PILOT_EVIDENCE, "DIAGNOSTIC_TIMING_PILOT")
        with mock.patch.object(executor, "_execute_canonical_case", side_effect=TypeError("fixture")), \
             mock.patch.object(executor.time, "perf_counter_ns", side_effect=(1, 4)), \
             mock.patch.object(executor.time, "process_time_ns", side_effect=(2, 7)):
            diagnostic = executor._execute_canonical_pilot_case(self.canonical, row, "BASE", context)
        self.assertIsNone(diagnostic["rhs_evaluations"])
        self.assertEqual(diagnostic["rhs_evaluations_status"],
                         "NOT_AVAILABLE_DUE_TO_IMPLEMENTATION_EXCEPTION")
        self.assertEqual(diagnostic["execution_failure_class"], "IMPLEMENTATION_EXCEPTION")

    def test_pilot_implementation_exception_is_truthful_and_aborts(self):
        rows = [row for row in self.canonical.rows if row["pressure_mode"] == "PRESCRIBED_STATIC"][:3]
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / "pilot-output"
            authority = {"authorization_id":"FIXTURE", "authorized_head":"H", "authorized_tree":"T",
                "matrix_semantic_sha256":self.canonical.matrix_hash,
                "protocol_artifact_sha256":self.canonical.protocol_hash,
                "executor_source_sha256":executor.sha256_file(Path(executor.__file__)),
                "backend":executor.REAL_BACKEND,"evidence_kind":executor.PILOT_EVIDENCE}
            plan={"key_count":3,"keys":[[r["case_id"],"BASE"] for r in rows],"authority":authority}
            complete={"status":"COMPLETE","started_at_utc":"FIXTURE","case_wall_time_ns":1,
                "case_cpu_time_ns":1,"rhs_evaluations":0,"rhs_evaluations_status":"MEASURED",
                "execution_failure_class":"NUMERICAL_CASE_DISPOSITION","linear_solve_status":"PASS",
                "stop_disposition":None,"canonical_outcome_serialized_bytes":1}
            failure={"status":"FAILED","started_at_utc":"FIXTURE","case_wall_time_ns":2,
                "case_cpu_time_ns":2,"rhs_evaluations":None,
                "rhs_evaluations_status":"NOT_AVAILABLE_DUE_TO_IMPLEMENTATION_EXCEPTION",
                "execution_failure_class":"IMPLEMENTATION_EXCEPTION","linear_solve_status":"NOT_AVAILABLE",
                "stop_disposition":None,"failure_disposition":"TypeError:fixture",
                "canonical_outcome_serialized_bytes":0}
            sentinel=mock.Mock(side_effect=[complete,failure,AssertionError("third launched")])
            with mock.patch.object(executor,"pilot_plan",return_value=plan), \
                 mock.patch.object(executor.CanonicalStore,"load",return_value=self.canonical), \
                 mock.patch.object(executor,"_execute_canonical_pilot_case",side_effect=sentinel):
                result=executor.execute_authorized_pilot(pilot_authority_path=Path("/fixture"),
                    allowlist_path=Path("/fixture"),output_root=output)
            self.assertEqual(sentinel.call_count,2)
            self.assertEqual((result["completed"],result["remaining"],result["infrastructure_failures"]),(2,1,1))
            store=executor.ResultStore(output,self.canonical); manifest=store.load_manifest()
            self.assertEqual(manifest["status"],"INFRASTRUCTURE_FAILURE")
            summary=executor.summarize(store)
            self.assertEqual(summary["failure_classes"]["IMPLEMENTATION_EXCEPTION"],1)
            self.assertEqual(summary["projection_eligible_records"],1)

    def test_classifier_precedence_fixture(self):
        f = executor._classification_precedence_fixture
        self.assertEqual(f(authority_invalid=True, metrics=((.5,0),(.5,0))), "AUTHORITY_OR_ARTIFACT_INVALID")
        self.assertEqual(f(structural_identity=True), "ANALYTICAL_STRUCTURAL_IDENTITY")
        self.assertEqual(f(numerical_unresolved=True), "NUMERICALLY_UNRESOLVED")
        self.assertNotIn("initial_condition_disagreement", inspect.signature(f).parameters)
        self.assertEqual(f(sector_disagreement=True, metrics=((.5,0),(.5,0))),
                         "MODEL_FORM_OR_SECTOR_RESOLUTION_DISAGREEMENT")
        self.assertEqual(f(metrics=((.8,0),(1.,0))), "METRIC_DISAGREEMENT")
        self.assertEqual(f(metrics=((.8,0),(.8,0))), "LATERAL_EQUALIZATION")
        self.assertEqual(f(metrics=((1.2,0),(1.2,0))), "HETEROGENEITY_AMPLIFIES")
        self.assertEqual(f(metrics=((1.,0),(1.,0))), "HETEROGENEITY_PERSISTS")

    def test_baseline_initial_condition_scope_is_explicit_and_not_caller_overridable(self):
        status = self.canonical.by_id and json.loads(
            executor.PROTOCOL_PATH.read_text())["classification"]["initial_condition_reconciliation"]
        self.assertEqual(status["status"], protocol.INITIAL_CONDITION_AUTHORITY_STATUS)
        self.assertEqual(status["stage_a_dynamic_scope"], "BASELINE_ZERO_STATE_ONLY")
        self.assertEqual(status["initial_condition_dependence_branch"], "NOT_EVALUATED_NOT_FALSE")
        self.assertEqual(status["reserved_future_label_stage_a_status"], "NOT_ADJUDICATED_STAGE_A")
        self.assertFalse(status["hidden_runs_authorized"])
        signature = inspect.signature(executor.classify_stage_a_evidence)
        self.assertNotIn("initial_condition_disagreement", signature.parameters)
        self.assertNotIn("initial_condition_partner_ids", signature.parameters)

    def test_pilot_plan_is_allowlisted_diagnostic_only(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name); output=root/"output"; output.mkdir()
            keys=[{"case_id": self.plan["keys"][1][0], "numerical_profile": self.plan["keys"][1][1]},
                  {"case_id": self.plan["keys"][0][0], "numerical_profile": self.plan["keys"][0][1]}]
            allow=root/"allow.json"; allow.write_text(json.dumps({"schema":executor.PILOT_ALLOWLIST_SCHEMA,"keys":keys}))
            ordered,digest=executor._load_pilot_allowlist(allow,self.canonical)
            authority={"schema":executor.PILOT_AUTHORITY_SCHEMA,"authorization_id":"SYNTHETIC_PILOT",
                "authorized_head":"H","authorized_tree":"T","matrix_semantic_sha256":self.canonical.matrix_hash,
                "protocol_artifact_sha256":self.canonical.protocol_hash,
                "executor_source_sha256":executor.sha256_file(Path(executor.__file__)),"backend":executor.SYNTHETIC_BACKEND,
                "allowed_output_root":str(output),"allowlist_sha256":digest,"maximum_case_count":2,
                "evidence_kind":executor.PILOT_EVIDENCE,"reuse_policy":"DISABLED",
                "allowed_execution_mode":"DIAGNOSTIC_TIMING_PILOT"}
            auth=root/"pilot.json"; auth.write_text(json.dumps(authority))
            values={("rev-parse","HEAD"):"H",("rev-parse","HEAD^{tree}"):"T"}
            with mock.patch.object(executor,"git_value",side_effect=lambda *x:values[x]):
                plan=executor.pilot_plan(auth,allow,output,store=self.canonical,allow_synthetic_fixture=True)
            self.assertEqual(plan["keys"],[list(x) for x in ordered]); self.assertEqual(plan["solver_calls"],0)
            self.assertEqual(plan["evidence_kind"],executor.PILOT_EVIDENCE)
            material={"authorization_id":"PILOT","authorized_head":"H","authorized_tree":"T",
                "matrix_hash":self.canonical.matrix_hash,"protocol_hash":self.canonical.protocol_hash,
                "executor_identity":executor.sha256_file(Path(executor.__file__)),
                "execution_mode":"DIAGNOSTIC_TIMING_PILOT","backend":executor.REAL_BACKEND,
                "evidence_kind":executor.PILOT_EVIDENCE,"output_root":str(root/"pilot-store")}
            context=executor._ValidatedExecutionContext(**material,
                run_id=executor.sha256_bytes(executor.canonical_json(material).encode())[:24])
            pilot_store=executor.ResultStore(root/"pilot-store",self.canonical)
            pilot_store.begin_run(context,0)
            with self.assertRaisesRegex(ValueError,"DIAGNOSTIC_TIMING"):
                executor.classify_stage_a_evidence(self.canonical,pilot_store,self.plan["keys"][0][0])

    def test_public_pilot_has_no_callback_and_cli_binds_adapter(self):
        signature = inspect.signature(executor.execute_authorized_pilot)
        for name in ("launcher", "real_launcher", "callback", "case_runner",
                     "timing_result", "status_result"):
            self.assertNotIn(name, signature.parameters)
            with self.assertRaises(TypeError):
                executor.execute_authorized_pilot(pilot_authority_path=Path("/missing"),
                    allowlist_path=Path("/missing"), output_root=Path("/tmp/missing"),
                    **{name: object()})
        with tempfile.TemporaryDirectory() as name, \
             mock.patch.object(executor, "execute_authorized_pilot", return_value={}) as bound:
            rc = executor.main(["--mode", "pilot-execute", "--output-root", name,
                "--pilot-authority", "/fixture/authority.json",
                "--pilot-allowlist", "/fixture/allowlist.json"])
            self.assertEqual(rc, 0); bound.assert_called_once()

    def test_pilot_adapter_measures_canonical_outcome_internally(self):
        row = next(item for item in self.canonical.rows if item["pressure_mode"] != "PRESCRIBED_STATIC")
        context = self.real_context("/tmp", executor.PILOT_EVIDENCE,
                                    "DIAGNOSTIC_TIMING_PILOT")
        outcome = {"status": "STOPPED", "rhs_evaluations": 17,
            "linear_solve_status": "NOT_APPLICABLE", "residual_status": "STOPPED",
            "stop_disposition": "SYNTHETIC_SENTINEL_STOP", "metric_primitives": {"invented": 99}}
        with mock.patch.object(executor, "_execute_canonical_case", return_value=outcome) as canonical, \
             mock.patch.object(executor.time, "perf_counter_ns", side_effect=(100, 175)), \
             mock.patch.object(executor.time, "process_time_ns", side_effect=(20, 55)):
            diagnostic = executor._execute_canonical_pilot_case(self.canonical, row, "BASE", context)
        canonical.assert_called_once()
        self.assertEqual(diagnostic["case_wall_time_ns"], 75)
        self.assertEqual(diagnostic["case_cpu_time_ns"], 35)
        self.assertEqual(diagnostic["rhs_evaluations"], 17)
        self.assertEqual(diagnostic["status"], "STOPPED")
        self.assertNotIn("metric_primitives", diagnostic)

    def test_public_pilot_persists_only_internal_diagnostic_adapter_result(self):
        row = next(item for item in self.canonical.rows if item["pressure_mode"] == "PRESCRIBED_STATIC")
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / "pilot-output"
            authority = {"authorization_id": "SENTINEL_PILOT_ONLY", "authorized_head": "H",
                "authorized_tree": "T", "matrix_semantic_sha256": self.canonical.matrix_hash,
                "protocol_artifact_sha256": self.canonical.protocol_hash,
                "executor_source_sha256": executor.sha256_file(Path(executor.__file__)),
                "backend": executor.REAL_BACKEND, "evidence_kind": executor.PILOT_EVIDENCE}
            plan = {"key_count": 1, "keys": [[row["case_id"], "BASE"]], "authority": authority}
            diagnostic = {"status": "COMPLETE", "started_at_utc": "SYNTHETIC_SENTINEL",
                "case_wall_time_ns": 41,
                "case_cpu_time_ns": 19, "rhs_evaluations": 0,
                "linear_solve_status": "PASS", "residual_status": "PASS",
                "stop_disposition": None, "canonical_outcome_serialized_bytes": 123}
            with mock.patch.object(executor, "pilot_plan", return_value=plan), \
                 mock.patch.object(executor.CanonicalStore, "load", return_value=self.canonical), \
                 mock.patch.object(executor, "_execute_canonical_pilot_case",
                                   return_value=diagnostic) as adapter:
                result = executor.execute_authorized_pilot(
                    pilot_authority_path=Path("/sentinel/pilot.json"),
                    allowlist_path=Path("/sentinel/allowlist.json"), output_root=output)
            self.assertEqual(result["evidence_kind"], executor.PILOT_EVIDENCE)
            adapter.assert_called_once()
            store = executor.ResultStore(output, self.canonical); manifest = store.load_manifest()
            record = store.read_bound_record(manifest, row["case_id"], "BASE")
            self.assertEqual(record["evidence_kind"], executor.PILOT_EVIDENCE)
            self.assertEqual(record["metric_primitives"], {"diagnostic_timing_only": {
                key: value for key, value in diagnostic.items() if key != "status"}})


if __name__ == "__main__":
    unittest.main()
