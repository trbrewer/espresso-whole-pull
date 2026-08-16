import ast
import copy
import csv
import importlib.util
import json
import math
import re
import statistics
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/sci_lc_001a_protocol.py"
OUT = ROOT / "validation/cases/sci_lc_001a"
spec = importlib.util.spec_from_file_location("sci_lc_001a_protocol", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def solve_linear(matrix, rhs):
    a = [list(row) + [value] for row, value in zip(matrix, rhs)]
    n = len(a)
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        if abs(scale) < 1e-30:
            raise ValueError("singular fixture")
        a[col] = [value / scale for value in a[col]]
        for row in range(n):
            if row != col:
                factor = a[row][col]
                a[row] = [x - factor * y for x, y in zip(a[row], a[col])]
    return [row[-1] for row in a]


def close_sequence(left, right, tol=2e-13):
    if isinstance(right, (int, float)):
        right = [right] * len(left)
    return all(abs(a - b) <= tol for a, b in zip(left, right))


def cholesky_positive_definite(matrix):
    n = len(matrix)
    lower = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            value = matrix[i][j] - sum(lower[i][k] * lower[j][k] for k in range(j))
            if i == j:
                if value <= 0:
                    return False
                lower[i][j] = math.sqrt(value)
            else:
                lower[i][j] = value / lower[j][j]
    return True


def static_fixture(placement, lateral, *, n=8, mode="1", contrast="4",
                   pattern="FOURIER", initial="BASE_PHASE", epsilon="0.05"):
    primitive = mod.resistance_primitives(n, pattern, mode, contrast, placement, epsilon, initial)
    gu = [1.0 / value for value in primitive["R_u_i"]]
    gd = [1.0 / value for value in primitive["R_d_i"]]
    ge = float(lateral) * (1.0 / n) * (n / (2.0 * math.pi)) ** 2
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        matrix[i][i] = gu[i] + gd[i] + 2.0 * ge
        matrix[i][(i - 1) % n] -= ge
        matrix[i][(i + 1) % n] -= ge
    pressure = solve_linear(matrix, gu)
    outlet = [g * p for g, p in zip(gd, pressure)]
    lateral_flux = [ge * (pressure[i] - pressure[(i + 1) % n]) for i in range(n)]
    fractions = [value / sum(outlet) for value in outlet]
    h_q = 0.5 * sum(abs(value - 1.0 / n) for value in fractions)
    return {"primitive": primitive, "matrix": matrix, "pressure": pressure,
            "outlet": outlet, "fractions": fractions, "lateral_flux": lateral_flux, "H_q": h_q}


class SciLc001aProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = mod.build_rows()
        cls.protocol = mod.protocol(cls.rows)
        mod.validate(cls.rows, cls.protocol)

    def test_reviewed_proportional_split_is_historical_null(self):
        totals = (2.0, 5.0, 11.0)
        for alpha in (0.05, 0.5, 0.95):
            pressures = []
            for total in totals:
                ru, rd = alpha * total, (1.0 - alpha) * total
                pressures.append(rd / (ru + rd))
            self.assertTrue(close_sequence(pressures, 1.0 - alpha, tol=0))

    def test_active_upstream_topology_has_lateral_driver(self):
        uncoupled = static_fixture("UPSTREAM_LOCALIZED", 0)
        coupled = static_fixture("UPSTREAM_LOCALIZED", 1)
        self.assertGreater(max(uncoupled["pressure"]) - min(uncoupled["pressure"]), 0)
        self.assertGreater(max(abs(x) for x in coupled["lateral_flux"]), 0)
        self.assertFalse(close_sequence(uncoupled["fractions"], coupled["fractions"], tol=1e-13))

    def test_active_downstream_topology_has_lateral_driver(self):
        uncoupled = static_fixture("DOWNSTREAM_LOCALIZED", 0)
        coupled = static_fixture("DOWNSTREAM_LOCALIZED", 1)
        self.assertGreater(max(uncoupled["pressure"]) - min(uncoupled["pressure"]), 0)
        self.assertGreater(max(abs(x) for x in coupled["lateral_flux"]), 0)
        self.assertFalse(close_sequence(uncoupled["fractions"], coupled["fractions"], tol=1e-13))

    def test_self_similar_is_exact_structural_null(self):
        for lateral in (0, 0.1, 100):
            result = static_fixture("AXIALLY_SELF_SIMILAR", lateral)
            self.assertTrue(close_sequence(result["pressure"], 0.5, tol=2e-14))
            self.assertTrue(close_sequence(result["lateral_flux"], 0, tol=2e-14))

    def test_total_path_and_conductance_are_exactly_preserved(self):
        for placement in mod.PLACEMENT_ALPHA:
            p = mod.resistance_primitives(8, "FOURIER", "2", "16", placement)
            self.assertTrue(close_sequence([a + b for a, b in zip(p["R_u_i"], p["R_d_i"])],
                                           p["T_i"], tol=2e-14))
            self.assertAlmostEqual(sum(p["G_i"]), 1.0, places=14)
            self.assertAlmostEqual(max(p["T_i"]) / min(p["T_i"]), 16.0, places=13)

    def test_all_frozen_rows_have_positive_primitives(self):
        for row in self.rows:
            p = mod.resistance_primitives(row["sector_count"], row["heterogeneity_pattern"],
                row["heterogeneity_mode"], row["resistance_contrast"], row["axial_placement"],
                row["epsilon_floor"], row["initial_condition_variant"])
            self.assertGreater(min(p["H_i"]), 0)
            self.assertGreater(min(p["R_u_i"] + p["R_d_i"]), 0)

    def test_lambda_zero_recovery_and_lateral_sign(self):
        zero = static_fixture("UPSTREAM_LOCALIZED", 0)
        expected = [1 / value for value in zero["primitive"]["T_i"]]
        self.assertTrue(close_sequence(zero["outlet"], expected, tol=2e-14))
        result = static_fixture("UPSTREAM_LOCALIZED", 1)
        for i, flux in enumerate(result["lateral_flux"]):
            delta = result["pressure"][i] - result["pressure"][(i + 1) % 8]
            self.assertEqual((flux > 0) - (flux < 0), (delta > 0) - (delta < 0))

    def test_global_lateral_cancellation(self):
        result = static_fixture("DOWNSTREAM_LOCALIZED", 3)
        node_lateral = [result["lateral_flux"][i]
            - result["lateral_flux"][(i - 1) % 8] for i in range(8)]
        self.assertAlmostEqual(sum(node_lateral), 0.0, places=15)

    def test_rotation_and_reflection_invariance_at_positive_lambda(self):
        base = static_fixture("UPSTREAM_LOCALIZED", 1)
        rotated = static_fixture("UPSTREAM_LOCALIZED", 1, initial="ROTATED_ONE_SECTOR")
        reflected = static_fixture("UPSTREAM_LOCALIZED", 1, initial="REFLECTED")
        self.assertAlmostEqual(base["H_q"], rotated["H_q"], places=14)
        self.assertAlmostEqual(base["H_q"], reflected["H_q"], places=14)
        self.assertTrue(close_sequence(sorted(base["pressure"]), sorted(rotated["pressure"]), tol=2e-14))

    def test_static_operator_positive_definite(self):
        for placement in mod.PLACEMENT_ALPHA:
            result = static_fixture(placement, 100)
            self.assertTrue(cholesky_positive_definite(result["matrix"]))

    def test_strong_coupling_approaches_common_pressure(self):
        weak = static_fixture("UPSTREAM_LOCALIZED", 0.001)
        strong = static_fixture("UPSTREAM_LOCALIZED", 100)
        self.assertLess(statistics.pvariance(strong["pressure"]), statistics.pvariance(weak["pressure"]))

    def test_scaled_ring_eigenvalue_converges(self):
        errors = [abs(mod.ring_eigenvalue(n, 1) - 1.0) for n in (8, 16, 32)]
        self.assertGreater(errors[0], errors[1]); self.assertGreater(errors[1], errors[2])

    def test_row_to_primitive_round_trips(self):
        dynamic = next(r for r in self.rows if r["arm"] == "D2" and
                       r["pressure_mode"] == "MACHINE_COUPLED" and
                       r["lateral_conductance_ratio"] != "0")
        n = dynamic["sector_count"]; lam = float(dynamic["lateral_conductance_ratio"])
        self.assertAlmostEqual(float(dynamic["lateral_edge_coefficient"]),
            lam * (n / (2 * math.pi)) ** 2)
        self.assertAlmostEqual(float(dynamic["lateral_edge_conductance_G_edge"]),
            lam * (1 / n) * (n / (2 * math.pi)) ** 2)
        self.assertAlmostEqual(float(dynamic["hydraulic_storage_C_h"]),
            float(dynamic["storage_ratio_S_h"]) / n)
        expected_theta = float(dynamic["storage_ratio_S_h"]) / (
            lam * mod.ring_eigenvalue(n, int(dynamic["heterogeneity_mode"])))
        self.assertAlmostEqual(float(dynamic["derived_Theta_L_m"]), expected_theta)
        self.assertAlmostEqual(float(dynamic["machine_compliance_C_u"]),
            float(dynamic["machine_response_ratio"]) * 21 / 11)
        feedback = next(r for r in self.rows if r["arm"] == "D3-EQ")
        self.assertIn(feedback["resistance_evolution_timescale_ratio"], mod.THETA_R)
        self.assertEqual(feedback["resistance_relaxation_tau_R"],
                         feedback["resistance_evolution_timescale_ratio"])
        zero = next(r for r in self.rows if r["arm"] == "D1" and r["lateral_conductance_ratio"] == "0")
        self.assertEqual(zero["derived_Theta_L_m"], mod.INFINITE)

    def test_machine_reference_parity(self):
        ref_spec = importlib.util.spec_from_file_location("machine", ROOT / "scripts/machine_coupling_reference.py")
        ref = importlib.util.module_from_spec(ref_spec); ref_spec.loader.exec_module(ref)
        theta = 0.3; compliance = theta * 21 / 11; load = 10 / 11
        actual = ref.continuous(0.4, 0, 0, compliance, 1, 1, load)
        a = 1 + load; expected = (1 / a) * (1 - math.exp(-0.4 * a / compliance))
        self.assertAlmostEqual(actual["pressure_Pa"], expected, places=14)

    def test_evolution_limits_and_bound_stop(self):
        base = mod.resistance_primitives(8, "FOURIER", "1", "4", "UPSTREAM_LOCALIZED")
        fixed = mod.evolved_resistance_primitives(base, [3] * 8, 0, "UPSTREAM_LOCALIZED")
        self.assertEqual(fixed["H_i"], base["H_i"])
        self.assertEqual(self.protocol["resistance_evolution"]["fast_control"], "Theta_R=0.03")
        with self.assertRaisesRegex(ValueError, "STOP_RESISTANCE_EVOLUTION"):
            mod.evolved_resistance_primitives(base, [10] * 8, 1, "UPSTREAM_LOCALIZED")
        for value in (0.25, 4.0):
            state = mod.evolved_resistance_primitives(base, [math.log(value)] * 8, 1,
                                                       "UPSTREAM_LOCALIZED")
            self.assertEqual(state["multipliers"][0], value)
            self.assertEqual(mod.multiplier_admissibility(state["multipliers"]), mod.MULTIPLIER_STOP)
        self.assertEqual(mod.multiplier_admissibility([.2500001, 3.999999]),
                         "SCIENTIFICALLY_ADMISSIBLE")
        self.assertEqual(mod.multiplier_admissibility([float("nan")]),
                         "STOP_NONFINITE_RESISTANCE_EVOLUTION_MULTIPLIER")

    def test_feedback_label_mapping_and_semantics(self):
        self.assertEqual(mod.feedback_sign_scalar("EQUALIZING"), 1.0)
        self.assertEqual(mod.feedback_sign_scalar("LOCALIZING"), -1.0)
        self.assertEqual(mod.feedback_sign_scalar("NONE"), 0.0)
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED"):
            mod.feedback_sign_scalar("AMPLIFY")
        active = copy.deepcopy(next(r for r in self.rows if r["arm"] == "D3-EQ"))
        mod.validate_feedback_contract(active)
        for label in ("NONE", "AMPLIFY"):
            broken = dict(active, feedback_sign=label)
            with self.assertRaises(ValueError):
                mod.validate_feedback_contract(broken)
        fixed = copy.deepcopy(next(r for r in self.rows if r["resistance_evolution_law"] == "NO_EVOLUTION"))
        mod.validate_feedback_contract(fixed)
        with self.assertRaises(ValueError):
            mod.validate_feedback_contract(dict(fixed, feedback_sign="EQUALIZING"))

    def test_boundary_initial_and_integration_are_exactly_serialized(self):
        b = self.protocol["boundary_initial_integration"]
        self.assertEqual((b["p_o_hat"], b["static_p_b_hat"], b["dynamic_p_b_hat"]),
                         ("0", "1", "min(tau/0.05,1)"))
        self.assertEqual(b["output_grid"], "tau_k=k/1000,k=0..1000")
        self.assertEqual((b["base_method"], b["refined_method"]), ("DOP853", "DOP853"))
        self.assertEqual(b["maximum_rhs_evaluations"], 200000)
        self.assertNotIn("maximum_internal_steps", b)

    def test_multilayer_placeholder_is_removed(self):
        self.assertEqual(self.protocol["model_form"]["multilayer_rows"], 0)
        self.assertFalse(any(r["model_variant"] != "CORE_ONE_EXCHANGE_PLANE" for r in self.rows))
        self.assertFalse(self.protocol["future_3d_nomination_rules"]["stage_a_authorized"])

    def test_uncertainty_ceiling_examples_and_human_agreement(self):
        self.assertEqual([mod.uncertainty_limit(x) for x in (0.5, 1.0, 2.0)], [0.01, 0.02, 0.02])
        text = (ROOT / "docs/analysis/sci_lc_001a/PROTOCOL.md").read_text()
        match = re.search(r"```protocol-summary-json\n(.*?)\n```", text, re.S)
        self.assertIsNotNone(match)
        summary = json.loads(match.group(1))
        self.assertEqual(summary["status"], self.protocol["status"])
        self.assertEqual(summary["epsilon_floor"], self.protocol["resistance_construction"]["epsilon_floor"])
        self.assertEqual(summary["uncertainty"], self.protocol["uncertainty"]["allowed_ceiling"])
        self.assertEqual(summary["classifier_precedence"], self.protocol["classification"]["precedence"])
        self.assertEqual(summary["matrix_summary"], self.protocol["matrix_summary"])

    def test_static_dynamic_classifier_routing_and_comparators(self):
        self.assertTrue(all(r["static_or_dynamic_classifier"] == "STATIC_CLASSIFIER_V1"
                            for r in self.rows if r["arm"] in ("S1", "S2", "S3")))
        ids = {r["case_id"]: r for r in self.rows}
        for row in self.rows:
            if row["static_or_dynamic_classifier"] == "DYNAMIC_CLASSIFIER_V1" and row["case_role"] == "ACTIVE_SCIENTIFIC_CASE":
                comparator = ids[row["comparator_case_id"]]
                self.assertEqual(comparator["lateral_conductance_ratio"], "0")
                for field in ("storage_ratio_S_h", "resistance_evolution_law", "pressure_mode",
                              "machine_response_ratio", "initial_condition_variant", "integration_profile"):
                    self.assertEqual(row[field], comparator[field])
        for row in self.rows:
            if row["arm"] in ("S1", "S2", "S3") and row["case_role"] == "ACTIVE_SCIENTIFIC_CASE":
                comparator = ids[row["comparator_case_id"]]
                self.assertEqual(comparator["lateral_conductance_ratio"], "0")

    def test_classification_precedence(self):
        self.assertEqual(mod.classify_synthetic_fixture(authority_valid=False, numerical_valid=False),
                         "AUTHORITY_OR_ARTIFACT_INVALID")
        self.assertEqual(mod.classify_synthetic_fixture(numerical_valid=False, structural_control=True),
                         "UNIFORM_OR_STRUCTURAL_CONTROL")
        self.assertEqual(mod.classify_synthetic_fixture(initial_dependence=True, model_disagreement=True),
                         "INITIAL_CONDITION_DEPENDENT_OR_BISTABLE")
        self.assertEqual(mod.classify_synthetic_fixture(metric_disagreement=True, threshold_straddle=True),
                         "METRIC_DISAGREEMENT")
        self.assertEqual(mod.classify_synthetic_fixture(end_gain=.8, integrated_gain=.8), "LATERAL_EQUALIZATION")

    def test_d4_is_fail_closed_for_stage_a(self):
        with self.assertRaisesRegex(mod.DeferredStageError, mod.D4_STATUS):
            mod.d4_select_synthetic([])
        self.assertEqual(self.protocol["staged_deferral"]["D4"]["status"], mod.D4_STATUS)

    def test_x1_is_fail_closed_for_stage_a(self):
        with self.assertRaisesRegex(mod.DeferredStageError, mod.X1_STATUS):
            mod.x1_select_synthetic([])
        self.assertEqual(self.protocol["staged_deferral"]["X1"]["status"], mod.X1_STATUS)

    def test_generation_ids_hashes_csv_json_and_caps(self):
        again = mod.build_rows(); self.assertEqual(self.rows, again)
        self.assertEqual(len(self.rows), len({r["case_id"] for r in self.rows}))
        for row in self.rows:
            self.assertEqual(row["row_sha256"], mod.digest({k: row[k] for k in mod.FIELDS if k != "row_sha256"}))
        payload = json.loads((OUT / "SCI_LC_001A_PARAMETER_MATRIX.json").read_text())
        with (OUT / "SCI_LC_001A_PARAMETER_MATRIX.csv").open(newline="") as handle:
            csv_rows = list(csv.DictReader(handle))
        self.assertEqual(csv_rows, [{k: str(v) for k, v in row.items()} for row in payload["rows"]])
        self.assertEqual(payload["matrix_sha256"], self.protocol["matrix_summary"]["matrix_sha256"])
        self.assertLess(self.protocol["compute_budget"]["prospective_maximum"], 20000)
        self.assertEqual(self.protocol["compute_budget"]["prospective_maximum"], len(self.rows))

    def test_zero_flow_startup_limit_and_rhs_are_finite(self):
        for placement in mod.ACTIVE_PLACEMENTS + ("AXIALLY_SELF_SIMILAR",):
            base = mod.resistance_primitives(8, "FOURIER", "1", "4", placement)
            startup = mod.startup_focusing(base, [0.125] * 8, "PRESCRIBED_DYNAMIC_RAMP")
            machine = mod.startup_focusing(base, [0.125] * 8, "MACHINE_COUPLED")
            self.assertTrue(all(math.isfinite(value) for value in startup))
            self.assertTrue(close_sequence(startup, machine, tol=0))
            self.assertAlmostEqual(sum(startup), 8.0)
            self.assertEqual(mod.evolution_focusing(tau=0, flows=[0.0] * 8, startup=startup), startup)
            for threshold in (1e-10, 1e-12, 1e-14):
                self.assertEqual(mod.evolution_focusing(tau=0, flows=[threshold / 100] * 8,
                    startup=startup, zero_threshold=threshold), startup)
            gu = [1 / value for value in base["R_u_i"]]
            gd = [1 / value for value in base["R_d_i"]]
            numerical = [a * b / .125 * 1e-8 for a, b in zip(gu, gd)]
            self.assertTrue(close_sequence(
                mod.evolution_focusing(tau=1e-5, flows=numerical, startup=startup, zero_threshold=1e-20),
                startup, tol=2e-14))
        with self.assertRaisesRegex(ValueError, "FLOW_REVERSAL"):
            mod.evolution_focusing(tau=.1, flows=[-1.0] + [0.0] * 7, startup=[1.0] * 8)
        values = mod.evolution_focusing(tau=.1, flows=[0.0] + [1.0] * 7, startup=[1.0] * 8)
        self.assertEqual(values[0], 0.0)

    def test_boundary_modes_are_closed_and_mutually_exclusive(self):
        self.assertEqual(tuple(self.protocol["boundary_modes"]["closed_enumeration"]), mod.BOUNDARY_MODES)
        for row in self.rows:
            self.assertIn(row["pressure_mode"], mod.BOUNDARY_MODES)
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_BOUNDARY_MODE"):
            mod.make_row(arm="BAD", pressure="AMBIGUOUS")
        with self.assertRaisesRegex(ValueError, "STATIC_CLASSIFIER"):
            mod.make_row(arm="BAD", pressure="MACHINE_COUPLED", theta_m="1")
        tables = self.protocol["boundary_modes"]["field_dispositions"]
        for mode in mod.BOUNDARY_MODES:
            self.assertEqual(set(tables[mode]), set(mod.FIELDS))
            self.assertFalse(set(tables[mode].values()) - set(mod.FIELD_DISPOSITIONS))

        static = next(r for r in self.rows if r["pressure_mode"] == "PRESCRIBED_STATIC")
        dynamic = next(r for r in self.rows if r["pressure_mode"] == "PRESCRIBED_DYNAMIC_RAMP")
        machine = next(r for r in self.rows if r["pressure_mode"] == "MACHINE_COUPLED")
        mutations = [
            (static, "storage_ratio_S_h", "1"), (static, "hydraulic_storage_C_h", ".125"),
            (static, "integration_profile", mod.INTEGRATION_PROFILE),
            (static, "machine_response_ratio", "1"),
            (dynamic, "machine_response_ratio", "1"),
            (dynamic, "integration_profile", "STATIC_LINEAR_SOLVE_V1"),
            (dynamic, "hydraulic_storage_C_h", mod.NA),
            (machine, "machine_response_ratio", mod.NA),
            (machine, "machine_reference_tuple", "UNSUPPORTED"),
            (machine, "storage_ratio_S_h", mod.NA),
            (machine, "hydraulic_storage_C_h", mod.NA),
        ]
        for original, field, value in mutations:
            with self.subTest(mode=original["pressure_mode"], field=field):
                with self.assertRaises(ValueError):
                    mod.validate_boundary_row(dict(original, **{field: value}))

    def test_enforceable_rhs_cap_and_event_tie_breaking(self):
        self.assertEqual(mod.enforce_rhs_cap(199999), 200000)
        with self.assertRaisesRegex(ValueError, "MAX_RHS"):
            mod.enforce_rhs_cap(200000)
        event = mod.select_multiplier_event([
            {"tau": .5, "bound": "UPPER_BOUND", "sector_index": 0},
            {"tau": .5 + 5e-11, "bound": "LOWER_BOUND", "sector_index": 2},
            {"tau": .5, "bound": "LOWER_BOUND", "sector_index": 1},
        ])
        self.assertEqual((event["bound"], event["sector_index"]), ("LOWER_BOUND", 1))
        # Dense-output event evidence is independent of the 1,001 reporting samples.
        between_samples = {"tau": .5005, "bound": "UPPER_BOUND", "sector_index": 3}
        self.assertEqual(mod.select_multiplier_event([between_samples]), between_samples)
        self.assertAlmostEqual(mod.locate_linear_event(.5, 3.9, .501, 4.1, 4.0), .5005)
        self.assertEqual(mod.locate_linear_event(.5, .25, .501, .2, .25), .5)

    def test_residual_and_uncertainty_contracts(self):
        self.assertEqual(mod.scaled_residual_norm([1e-12], [1.0]), 1e-12)
        self.assertAlmostEqual(mod.residual_corrected_gain_uncertainty(
            2, 4, corrected_numerator=2.1, corrected_denominator=4.2), 0)
        components = {name: .001 for name in mod.UNCERTAINTY_COMPONENTS}
        applicable = {name: True for name in mod.UNCERTAINTY_COMPONENTS}
        self.assertAlmostEqual(mod.combine_uncertainty(components, applicable=applicable), .005)
        allowed_na = dict(components, u_sector=mod.NA)
        self.assertAlmostEqual(mod.combine_uncertainty(allowed_na,
            applicable=dict(applicable, u_sector=False)), .004)
        with self.assertRaisesRegex(ValueError, "NOT_APPLICABLE_REQUIRED"):
            mod.combine_uncertainty(allowed_na, applicable=applicable)
        with self.assertRaisesRegex(ValueError, "NUMERICALLY_UNRESOLVED"):
            mod.combine_uncertainty(dict(components, u_sector="UNAVAILABLE"), applicable=applicable)
        for bad in (-1, float("nan"), "BAD"):
            with self.assertRaisesRegex(ValueError, "INVALID_UNCERTAINTY"):
                mod.combine_uncertainty(dict(components, u_linear=bad), applicable=applicable)
        self.assertEqual(mod.uncertainty_limit(0), 0)
        self.assertEqual(mod.uncertainty_limit(1e-12), 2e-14)
        with self.assertRaisesRegex(ValueError, "DENOMINATOR_FLOOR"):
            mod.residual_corrected_gain_uncertainty(1, 1e-13,
                corrected_numerator=1, corrected_denominator=1e-13)
        self.assertNotIn("u_denominator", self.protocol["uncertainty"]["components"])

    def test_startup_refinement_boundaries_and_routing(self):
        startup = [1.0] * 8
        q = mod.Q_ZERO_THRESHOLD
        self.assertEqual(mod.evolution_focusing(tau=0, flows=[0.0] * 8, startup=startup), startup)
        self.assertEqual(mod.evolution_focusing(tau=mod.STARTUP_TAU_MAX,
            flows=[q / 8] * 8, startup=startup), startup)
        above = mod.evolution_focusing(tau=mod.STARTUP_TAU_MAX + 1e-12,
            flows=[2 * q / 8] * 8, startup=startup)
        self.assertEqual(above, startup)
        with self.assertRaisesRegex(ValueError, "OUTSIDE_STARTUP"):
            mod.evolution_focusing(tau=mod.STARTUP_TAU_MAX + 1e-12,
                flows=[q / 8] * 8, startup=startup)
        self.assertAlmostEqual(mod.startup_uncertainty(1, .99), .01)
        for status in ("UNAVAILABLE", "STOPPED", "CAPPED"):
            with self.assertRaisesRegex(ValueError, "NUMERICALLY_UNRESOLVED"):
                mod.startup_uncertainty(1, 1, refined_status=status)
        with self.assertRaisesRegex(ValueError, "NUMERICALLY_UNRESOLVED"):
            mod.startup_uncertainty(1, float("nan"))

    def test_sector_refinement_contract_and_nonlinear_removal(self):
        row = next(r for r in self.rows if r["numerical_resolution_role"] == "SECTOR_REFINEMENT"
                   and r["sector_count"] == 4)
        self.assertEqual(mod.sector_refinement_nref(row), 8)
        self.assertIn(mod.sector_companion_case_id(row, self.rows), {r["case_id"] for r in self.rows})
        ordinary = next(r for r in self.rows if r["numerical_resolution_role"] == "PRIMARY")
        self.assertEqual(mod.sector_refinement_nref(ordinary), mod.NA)
        residual = self.protocol["residual_contract"]
        self.assertEqual(residual["stage_a_nonlinear_fixed_point_solve"], "NOT_USED")
        self.assertNotIn("nonlinear", residual)

    def test_structural_roles_and_comparator_reconciliation(self):
        ids = {row["case_id"]: row for row in self.rows}
        self.assertEqual(sum(row["case_role"] == "STRUCTURAL_COMPARATOR" for row in self.rows), 362)
        self.assertEqual(sum(row["case_role"] == "ACTIVE_SCIENTIFIC_CASE" for row in self.rows), 848)
        for row in self.rows:
            identity = mod.structural_identity(row)
            if row["case_role"] == "ACTIVE_SCIENTIFIC_CASE":
                comparator = ids[row["comparator_case_id"]]
                self.assertEqual(comparator["case_role"], "STRUCTURAL_COMPARATOR")
                self.assertIsNone(identity)
            elif row["case_role"] == "STRUCTURAL_COMPARATOR":
                self.assertEqual(row["comparator_case_id"], mod.NA)
                self.assertEqual(identity, "EXACT_LAMBDA_ZERO_IDENTITY")

    def test_zero_span_requires_unit_contrast(self):
        unit = mod.resistance_primitives(8, "UNIFORM", "0", "1", "AXIALLY_SELF_SIMILAR")
        self.assertTrue(close_sequence(unit["g_tilde"], 1.0, tol=0))
        with self.assertRaisesRegex(ValueError, "ZERO_SPAN"):
            mod.resistance_primitives(8, "UNIFORM", "0", "1.0001", "AXIALLY_SELF_SIMILAR")

    def test_matrix_removes_redundant_self_similar_factorial(self):
        self_similar = [r for r in self.rows if r["axial_placement"] == "AXIALLY_SELF_SIMILAR"]
        self.assertEqual(len(self_similar), 58)  # 54 bounded heterogeneous + 4 other controls
        self.assertFalse(any(r["arm"] == "S1" and r["axial_placement"] == "AXIALLY_SELF_SIMILAR" for r in self.rows))

    def test_protocol_has_no_execution_import_or_classifier_output(self):
        tree = ast.parse(SCRIPT.read_text())
        imports = {node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)}
        imports |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        self.assertFalse(any(name in imports for name in ("subprocess", "puckworks", "Foam")))
        self.assertFalse(self.protocol["execution_authorized"])
        self.assertEqual(set(self.protocol["zero_execution"].values()), {0})


if __name__ == "__main__":
    unittest.main()
