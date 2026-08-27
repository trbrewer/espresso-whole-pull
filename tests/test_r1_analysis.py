from __future__ import annotations

import importlib.util
import json
import math
import csv
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from tools.sci_ed_002_record_context import RecordContextError, validate_record_context

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("r1_analysis", ROOT / "scripts/analyze_r1.py")
assert SPEC and SPEC.loader
ANALYSIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYSIS)


class R1AnalysisSyntheticTests(unittest.TestCase):
    def test_exact_governed_bindings_and_no_8s_mapping(self) -> None:
        contract, scenario, lock = ANALYSIS.authorities(ROOT)
        self.assertEqual(lock["checkout_commit"], contract["source_dependency"]["commit"])
        self.assertEqual(lock["checkout_tree_sha"], contract["source_dependency"]["tree"])
        self.assertEqual(
            scenario["source_time_mapping"]["solver_time_equals_source_time_plus_s"],
            contract["time_mapping_contract"]["source_to_solver_offset_s"],
        )
        self.assertFalse(contract["time_mapping_contract"]["source_first_drop_offset_8s_used"])

    def test_linear_interpolation_and_strict_range(self) -> None:
        self.assertEqual(ANALYSIS.interpolate([0.0, 1.0], [2.0, 4.0], 0.5), 3.0)
        with self.assertRaises(ValueError):
            ANALYSIS.interpolate([0.0, 1.0], [2.0, 4.0], -0.1)
        with self.assertRaises(ValueError):
            ANALYSIS.interpolate([0.0, 1.0], [2.0, 4.0], 1.1)

    def test_rmse_normalization_and_population_pearson(self) -> None:
        observed = [1.0, 2.0, 3.0]
        predicted = [2.0, 4.0, 6.0]
        obs_norm = [value / 3.0 for value in observed]
        pred_norm = [value / 6.0 for value in predicted]
        rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(obs_norm, pred_norm)) / 3)
        self.assertEqual(rmse, 0.0)
        value, defined = ANALYSIS.pearson(obs_norm, pred_norm, 1e-8)
        self.assertTrue(defined)
        self.assertAlmostEqual(value, 1.0)

    def test_degeneracy_is_undefined_without_jitter(self) -> None:
        value, defined = ANALYSIS.pearson([1.0] * 5, [1, 2, 3, 4, 5], 1e-8)
        self.assertIsNone(value)
        self.assertFalse(defined)

    def test_median_and_four_of_five_gates(self) -> None:
        gates = {
            "median_normalized_shape_rmse_max": 0.15,
            "shots_required_at_or_below_rmse_0_20": 4,
            "median_pearson_r_min": 0.95,
            "shots_required_at_or_above_r_0_90": 4,
        }
        shots = [
            {"normalized_shape_rmse": 0.1, "pearson_defined": True, "pearson_r": 0.96}
            for _ in range(4)
        ] + [{"normalized_shape_rmse": 0.3, "pearson_defined": True, "pearson_r": 0.8}]
        self.assertEqual(ANALYSIS.aggregate(shots, gates)["status"], "PASS")
        shots[0]["pearson_defined"] = False
        shots[0]["pearson_r"] = None
        self.assertEqual(ANALYSIS.aggregate(shots, gates)["status"], "FAIL")

    def test_thresholds_are_derived_and_ambiguous_keys_fail(self) -> None:
        contract, _, _ = ANALYSIS.authorities(ROOT)
        gates = contract["protected_comparison_contract"]["gates"]
        required, threshold, key = ANALYSIS.governed_shot_gate(
            gates, "shots_required_at_or_below_rmse_"
        )
        self.assertEqual((required, threshold, key), (4, 0.20, "shots_required_at_or_below_rmse_0_20"))
        ambiguous = dict(gates)
        ambiguous["shots_required_at_or_below_rmse_0_25"] = 4
        with self.assertRaises(ValueError):
            ANALYSIS.governed_shot_gate(
                ambiguous, "shots_required_at_or_below_rmse_"
            )

    def test_governed_source_grid_matches_frozen_windows(self) -> None:
        contract, _, _ = ANALYSIS.authorities(ROOT)
        grid = ANALYSIS.source_grid(contract)
        self.assertEqual(len(grid), 1000)
        self.assertEqual(grid[0], 0.0)
        self.assertEqual(grid[-1], 100.0)
        self.assertAlmostEqual(grid[100], 10.01001001001001)
        self.assertAlmostEqual(grid[899], 89.98998998998998)
        self.assertAlmostEqual(grid[900], 90.09009009009009)

    def test_floating_endpoint_reconciliation_is_tightly_bounded(self) -> None:
        contract, scenario, _ = ANALYSIS.authorities(ROOT)
        observed = 102.999999999997
        tolerance = ANALYSIS.floating_endpoint_tolerance_s(
            103.0, observed, scenario["time"]["delta_t_s"]
        )
        self.assertGreater(tolerance, 103.0 - observed)
        self.assertLess(tolerance, scenario["time"]["delta_t_s"] * 1e-6)
        rows = [
            {"time_s": index / 10, "outlet_flow_m3_s": 1.0}
            for index in range(1030)
        ]
        rows.append({"time_s": observed, "outlet_flow_m3_s": 2.0})
        result = ANALYSIS.predicted_trace(contract, scenario, rows)
        reconciliation = result["floating_endpoint_reconciliation"]
        self.assertEqual(reconciliation["status"], "APPLIED")
        self.assertEqual(reconciliation["source_index"], 999)
        self.assertEqual(reconciliation["reconciled_point_count"], 1)
        self.assertFalse(reconciliation["interpolation_extrapolation_performed"])
        self.assertFalse(reconciliation["scientific_time_mapping_changed"])
        self.assertEqual(result["mapped"][-1], 103.0)
        self.assertEqual(result["effective_times"][-1], observed)
        self.assertEqual(rows[-1]["time_s"], observed)

    def test_floating_endpoint_reconciliation_rejects_material_gap(self) -> None:
        contract, scenario, _ = ANALYSIS.authorities(ROOT)
        rows = [
            {"time_s": index / 10, "outlet_flow_m3_s": 1.0}
            for index in range(1030)
        ]
        rows.append({"time_s": 102.99, "outlet_flow_m3_s": 1.0})
        with self.assertRaises(ValueError):
            ANALYSIS.predicted_trace(contract, scenario, rows)

    def test_numerical_stage_freezes_calibration_without_puckworks(self) -> None:
        contract, scenario, _ = ANALYSIS.authorities(ROOT)
        target = contract["calibration_contract"]["equilibrium_mass_flow_g_per_s"]
        density = contract["solver_to_source_flow_mapping"]["primary_predicted_quantity"][
            "liquid_density_kg_m3"
        ]
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            trace = base / "trace.csv"
            with trace.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=sorted(ANALYSIS.REQUIRED_TRACE))
                writer.writeheader()
                for index in range(1031):
                    row = {field: 0.0 for field in ANALYSIS.REQUIRED_TRACE}
                    row.update(
                        time_s=index / 10,
                        outlet_flow_m3_s=target / (1000 * density),
                        max_saturation=1.0,
                    )
                    writer.writerow(row)
            acceptance = base / "acceptance.json"
            acceptance.write_text(json.dumps({
                "numerical_acceptance_gates": {"numerical": {"status": "PASS"}},
                "openfoam_b0_parity_gates": {"parity": {"status": "PASS"}},
            }), encoding="utf-8")
            manifest = base / "manifest.json"
            manifest.write_text(json.dumps({
                "r1_scientific_input_aggregate_sha256":
                    "ddc6ac9e5cfd4746d5e7548e1b78cbb4942092d134806a6e9526ef26657aa957"
            }), encoding="utf-8")
            output = base / "numerical.json"
            ANALYSIS.numerical_stage(ROOT, trace, acceptance, manifest, output)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["calibration_reproduction"]["status"], "PASS")
            self.assertTrue(result["protected_release_authorized"])
            self.assertFalse(result["protected_source_opened"])

    def test_scientific_values_are_read_not_embedded_as_results(self) -> None:
        source = (ROOT / "scripts/analyze_r1.py").read_text(encoding="utf-8")
        for forbidden in ("0.380987", "0.393133", "0.480984", "0.465988"):
            self.assertNotIn(forbidden, source)
        contract = json.loads(
            (ROOT / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json").read_text()
        )
        self.assertIn("liquid_density_kg_m3", contract["solver_to_source_flow_mapping"]["primary_predicted_quantity"])

    def test_physical_failure_remains_distinct_from_software_failure(self) -> None:
        shots = [
            {"normalized_shape_rmse": 1.0, "pearson_defined": False, "pearson_r": None}
            for _ in range(5)
        ]
        contract = json.loads(
            (ROOT / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json").read_text()
        )
        self.assertEqual(
            ANALYSIS.aggregate(shots, contract["protected_comparison_contract"]["gates"])["status"],
            "FAIL",
        )

    def test_final_environment_and_record_context(self) -> None:
        environment = json.loads(
            (ROOT / "validation/r1/WP01R_005_ENVIRONMENT_AND_PROVENANCE.json").read_text()
        )
        self.assertEqual(
            environment["record_status"],
            "COMPLETE_WITH_DECLARED_UNAVAILABLE_FIELDS",
        )
        self.assertEqual(environment["solver_build"]["openfoam_version"]["value"], "12")
        self.assertEqual(
            environment["solver_build"]["wm_options"]["value"],
            "linux64GccDPInt32Opt",
        )
        self.assertEqual(environment["execution_contract"]["mpi_ranks"]["value"], 32)
        unavailable = [
            environment["solver_build"]["compiler_version"],
            environment["solver_build"]["mpi_version"],
            environment["platform"]["operating_system_distribution_and_version"],
            environment["platform"]["cpu_model"],
            environment["platform"]["logical_processor_count"],
            environment["platform"]["physical_memory_bytes"],
        ]
        self.assertEqual(len(unavailable), 6)
        for item in unavailable:
            self.assertIsNone(item["value"])
            self.assertEqual(item["status"], "UNAVAILABLE_FROM_RETAINED_EVIDENCE")
            self.assertFalse(item["present_machine_observation_used"])
            self.assertTrue(item["reason"])
        self.assertFalse(
            environment["completeness_assessment"]["exact_machine_reconstruction_claimed"]
        )

        protocol = json.loads(
            (ROOT / "validation/r1/WP01R_005_PROTOCOL_CORRECTION.json").read_text()
        )
        summary = protocol["corrective_protocol_summary"]
        self.assertEqual(summary["historical_preliminary_pr"], 16)
        self.assertEqual(summary["corrective_attempt_2_central_r1_execution_count"], 1)
        self.assertEqual(summary["additional_r1_execution_count_after_attempt_2"], 0)
        self.assertEqual(summary["corrective_protected_processing_count"], 1)

        result = json.loads(
            (ROOT / "validation/r1/WP01R_005_EXECUTION_RESULT.json").read_text()
        )
        context = result["embedded_acceptance_context"]
        self.assertFalse(context["raw_reference_freeze_status_is_final_authority"])
        self.assertFalse(context["raw_analytical_note_is_r1_calibration_authority"])
        self.assertEqual(context["authoritative_final_r0_release_pointer"], "/r0_release_gate")

        status = json.loads(
            (ROOT / "validation/r1/WP01R_005_RUN_STATUS.json").read_text()
        )
        self.assertEqual(status["workflow_execution_status"], "PASS")
        self.assertEqual(status["protected_comparison_status"], "FAIL")

        activation = json.loads((ROOT / "docs/validation/sci_ed_002/r1/ACTIVATION.json").read_text())
        r1_result = json.loads((ROOT / "docs/validation/sci_ed_002/r1/R1_RESULT.json").read_text())
        validate_record_context(activation, r1_result)

    def test_final_record_context_rejects_nonportable_or_escalated_state(self) -> None:
        activation = json.loads((ROOT / "docs/validation/sci_ed_002/r1/ACTIVATION.json").read_text())
        result = json.loads((ROOT / "docs/validation/sci_ed_002/r1/R1_RESULT.json").read_text())
        cases = (
            ("MACHINE_LOCAL_ABSOLUTE_PATH", activation, {**activation, "path": "/tmp/worktree"}, result),
            ("WRONG_REPOSITORY_AUTHORITY", activation, {**activation, "branch": "main"}, result),
            ("SCIENTIFIC_DISPOSITION_CHANGED", result, activation, {**result, "disposition": "PASS"}),
            ("COMMISSIONING_TRUE", result, activation, {**result, "commissioning_authorized": True}),
            ("PREDICTOR_ELIGIBILITY_TRUE", result, activation, {**result, "predictor_eligible": True}),
            ("C_S0_ESTABLISHED", result, activation, {**result, "c_s0_mapping_status": "ESTABLISHED"}),
            ("INCONSISTENT_STATUS", result, activation, {**result, "consumer_status": "PASS"}),
        )
        for reason, _, candidate_activation, candidate_result in cases:
            with self.subTest(reason=reason), self.assertRaisesRegex(RecordContextError, reason):
                validate_record_context(candidate_activation, candidate_result)
        missing = deepcopy(activation); missing.pop("base")
        with self.assertRaisesRegex(RecordContextError, "MISSING_CONTEXT_FIELD"):
            validate_record_context(missing, result)


if __name__ == "__main__":
    unittest.main()
