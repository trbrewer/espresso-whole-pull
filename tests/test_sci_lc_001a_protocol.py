import ast
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

    def test_boundary_initial_and_integration_are_exactly_serialized(self):
        b = self.protocol["boundary_initial_integration"]
        self.assertEqual((b["p_o_hat"], b["static_p_b_hat"], b["dynamic_p_b_hat"]),
                         ("0", "1", "min(tau/0.05,1)"))
        self.assertEqual(b["output_grid"], "tau_k=k/1000,k=0..1000")
        self.assertEqual((b["base_method"], b["refined_method"]), ("DOP853", "DOP853"))

    def test_multilayer_placeholder_is_removed(self):
        self.assertEqual(self.protocol["model_form"]["multilayer_rows"], 0)
        self.assertFalse(any(r["model_variant"] != "CORE_ONE_EXCHANGE_PLANE" for r in self.rows))
        self.assertTrue(self.protocol["future_3d_nomination_rules"]["model_form_corroboration_required"])

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
            if row["static_or_dynamic_classifier"] == "DYNAMIC_CLASSIFIER_V1" and row["scientific_role"] == "SCIENTIFIC":
                comparator = ids[row["comparator_case_id"]]
                self.assertEqual(comparator["lateral_conductance_ratio"], "0")
                for field in ("storage_ratio_S_h", "resistance_evolution_law", "pressure_mode",
                              "machine_response_ratio", "initial_condition_variant", "integration_profile"):
                    self.assertEqual(row[field], comparator[field])
        for row in self.rows:
            if row["arm"] in ("S1", "S2", "S3"):
                comparator = ids[row["comparator_case_id"]]
                self.assertEqual(comparator["lateral_conductance_ratio"], "0")

    def test_classification_precedence(self):
        self.assertEqual(mod.classify_synthetic_fixture(authority_valid=False, numerical_valid=False),
                         "AUTHORITY_OR_ARTIFACT_INVALID")
        self.assertEqual(mod.classify_synthetic_fixture(numerical_valid=False, structural_control=True),
                         "NUMERICALLY_UNRESOLVED")
        self.assertEqual(mod.classify_synthetic_fixture(initial_dependence=True, model_disagreement=True),
                         "INITIAL_CONDITION_DEPENDENT_OR_BISTABLE")
        self.assertEqual(mod.classify_synthetic_fixture(metric_disagreement=True, threshold_straddle=True),
                         "METRIC_DISAGREEMENT")
        self.assertEqual(mod.classify_synthetic_fixture(end_gain=.8, integrated_gain=.8), "LATERAL_EQUALIZATION")

    def test_d4_selector_is_deterministic_handles_zero_ties_duplicates_and_caps(self):
        fixture = [
            {"case_id": "z", "adaptive_group_id": "g", "Lambda": "0", "gain": 1.0,
             "classification": "HETEROGENEITY_PERSISTS", "numerically_valid": True},
            {"case_id": "a", "adaptive_group_id": "g", "Lambda": "0.01", "gain": .89,
             "classification": "LATERAL_EQUALIZATION", "numerically_valid": True},
            {"case_id": "b", "adaptive_group_id": "g", "Lambda": "0.1", "gain": .91,
             "classification": "HETEROGENEITY_PERSISTS", "numerically_valid": True},
            {"case_id": "b-duplicate", "adaptive_group_id": "g", "Lambda": "0.1", "gain": .91,
             "classification": "HETEROGENEITY_PERSISTS", "numerically_valid": True},
            {"case_id": "c", "adaptive_group_id": "g", "Lambda": "1", "gain": 1.11,
             "classification": "HETEROGENEITY_AMPLIFIES", "numerically_valid": True},
        ]
        first = mod.d4_select_synthetic(fixture, cap=3)
        self.assertEqual(first, mod.d4_select_synthetic(list(reversed(fixture)), cap=3))
        self.assertLessEqual(len(first), 3)
        self.assertFalse(any(item["left_parent"] == "z" for item in first))
        self.assertEqual(len({(x["adaptive_group_id"], x["Lambda"]) for x in first}), len(first))
        exhausted = [dict(x, generation=3) for x in fixture]
        self.assertFalse(any(x["generation"] > 3 for x in mod.d4_select_synthetic(exhausted)))

    def test_x1_selector_handles_absent_regimes_boundary_and_ties(self):
        fixture = [
            {"case_id": "a", "classification": "LATERAL_EQUALIZATION", "gain": .7,
             "uncertainty": .01, "numerically_valid": True},
            {"case_id": "b", "classification": "LATERAL_EQUALIZATION", "gain": .89,
             "uncertainty": .01, "numerically_valid": True},
            {"case_id": "c", "classification": "HETEROGENEITY_PERSISTS", "gain": 1.0,
             "uncertainty": .01, "numerically_valid": True},
            {"case_id": "m", "classification": "HETEROGENEITY_PERSISTS", "gain": 1.0,
             "uncertainty": .02, "numerically_valid": True, "pair_key": "p", "machine_material": True},
            {"case_id": "p", "classification": "HETEROGENEITY_PERSISTS", "gain": 1.0,
             "uncertainty": .02, "numerically_valid": True, "pair_key": "p"},
            {"case_id": "bad", "classification": "HETEROGENEITY_AMPLIFIES", "gain": 1.3,
             "uncertainty": .01, "numerically_valid": False},
        ]
        selected = mod.x1_select_synthetic(fixture, cap=10)
        self.assertEqual(selected, mod.x1_select_synthetic(list(reversed(fixture)), cap=10))
        self.assertNotIn("bad", {x["case_id"] for x in selected})
        self.assertTrue({"m", "p"} <= {x["case_id"] for x in selected})
        self.assertLessEqual(len(selected), 10)

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
