from __future__ import annotations

import csv
import hashlib
import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "verification/cases/xsv_taichi_002"


class XSVTaichi002ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = json.loads(
            (CASE_ROOT / "XSV_TAICHI_002_PROTOCOL.json").read_text(encoding="utf-8")
        )
        with (CASE_ROOT / "XSV_TAICHI_002_CASE_MATRIX.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.target = json.loads(
            (CASE_ROOT / "XSV_TAICHI_002_TARGET.json").read_text(encoding="utf-8")
        )
        with (CASE_ROOT / "XSV_TAICHI_002_TARGET_INPUTS.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            cls.target_rows = list(csv.DictReader(handle))

    def test_authority_dependency_and_claim_boundary(self) -> None:
        protocol = self.protocol
        self.assertEqual(
            protocol["authorization_id"],
            "XSV-TAICHI-002-SYNTHETIC-MORPHOLOGY-COLLAPSE-SCREEN-2026-08-05",
        )
        self.assertEqual(protocol["classification"]["change_declaration"],
                         "NO_GOVERNING_PHYSICS_CHANGE")
        self.assertEqual(protocol["puckworks"]["commit"],
                         "fc61c4670ec7bf801e40bb391aab16048b8da26b")
        self.assertEqual(protocol["puckworks"]["tree"],
                         "1d553e44ee2f7480a5df521560801b478618cc84")
        self.assertEqual(protocol["claim_ceiling"]["physical_validation"],
                         "NOT_ESTABLISHED")
        self.assertEqual(protocol["claim_ceiling"]["next_stage"], "NOT_AUTHORIZED")
        self.assertIn("OPENFOAM_EXECUTION", protocol["prohibited"])
        self.assertIn("PROTECTED_OR_HOLDOUT_SCORING", protocol["prohibited"])

    def test_target_orientation_and_nominal_screen_are_frozen(self) -> None:
        target = self.protocol["target"]
        self.assertEqual(target["status"], "G1_NOT_DERIVED")
        self.assertEqual(target["attainment_operator"], "K_case/K_reference<=T_11_5")
        self.assertEqual(target["primary_ratio"],
                         "T_11_5=(Q_11/delta_p_11)/(Q_5/delta_p_5)")
        self.assertTrue(math.isclose(target["nominal_screen"]["ratio_upper_bound"],
                                     5.0 / 11.0, rel_tol=0.0, abs_tol=1e-16))
        self.assertTrue(math.isclose(target["nominal_screen"]["collapse_lower_bound"],
                                     1.0 - 5.0 / 11.0, rel_tol=0.0, abs_tol=1e-16))
        self.assertEqual(
            target["default_type_if_equal_geometry_and_viscosity_unproved"],
            "APPARENT_HYDRAULIC_CONDUCTANCE_RATIO_TARGET",
        )
        frozen = self.target
        self.assertEqual(frozen["target_type"],
                         "APPARENT_HYDRAULIC_CONDUCTANCE_RATIO_TARGET")
        self.assertEqual([int(row["nominal_group_bar"]) for row in self.target_rows],
                         [5, 9, 11])
        self.assertEqual([int(row["source_csv_line"]) for row in self.target_rows],
                         [5001, 9001, 10001])
        conductance = {
            int(row["nominal_group_bar"]):
            float(row["mass_flow_g_s"]) / float(row["pressure_bar"])
            for row in self.target_rows
        }
        expected = {
            "T_11_5": conductance[11] / conductance[5],
            "T_9_5": conductance[9] / conductance[5],
            "T_11_9": conductance[11] / conductance[9],
        }
        for key, value in expected.items():
            self.assertTrue(math.isclose(frozen["ratios"][key], value,
                                         rel_tol=1e-15, abs_tol=0.0))
        self.assertEqual(frozen["ratios"]["primary_attainment_rule"],
                         "K_case_over_K_reference <= T_11_5")
        self.assertFalse(frozen["selection_rule"]["new_window_selected"])
        self.assertEqual(frozen["selection_rule"]["pressure_field"],
                         "basket_pressure__bar")
        self.assertFalse(frozen["morphology_generated_before_freeze"])

    def test_geometry_transform_and_axes_are_exact(self) -> None:
        geometry = self.protocol["geometry"]
        self.assertEqual(geometry["seeds"], [42, 1729, 20260805])
        self.assertEqual(geometry["hetero_amp"], [0.0, 1.0, 2.0])
        self.assertEqual(geometry["axis_permutations"],
                         {"X": [0, 1, 2], "Y": [1, 0, 2], "Z": [2, 1, 0]})
        self.assertEqual(geometry["axis_permutations"],
                         geometry["axis_inverse_permutations"])
        coating = geometry["coating"]
        self.assertEqual(coating["fractions"], [0.0, 0.05, 0.15, 0.30])
        self.assertEqual(coating["removal_count"], "floor(f*N_void_0+0.5)")
        self.assertTrue(coating["immutable_nested_ranking"])
        self.assertFalse(coating["connectivity_repair"])
        token = "XSV_TAICHI_002_COATING_V1|1|2|3".encode("ascii")
        self.assertEqual(len(hashlib.sha256(token).hexdigest()), 64)

    def test_exact_case_matrix_order_and_attempt_ceiling(self) -> None:
        expected = [
            "H-A0-S42-X-MID", "H-A0-S1729-X-MID", "H-A0-S20260805-X-MID",
            "H-A1-S42-X-MID", "H-A1-S1729-X-MID", "H-A1-S20260805-X-MID",
            "H-A2-S42-X-MID", "H-A2-S1729-X-MID", "H-A2-S20260805-X-MID",
            "C05-X-MID", "C15-X-MID", "C30-X-MID",
            "H-A0-S42-Y-MID", "H-A0-S42-Z-MID",
            "H-A2-S42-Y-MID", "H-A2-S42-Z-MID", "C30-Y-MID", "C30-Z-MID",
            "H-A2-S42-X-LOW", "H-A2-S42-X-HIGH", "C30-X-LOW", "C30-X-HIGH",
        ]
        observed = [row["run_id"] for row in self.rows]
        self.assertEqual(observed, expected)
        self.assertEqual(len(observed), len(set(observed)))
        self.assertEqual([int(row["run_order"]) for row in self.rows], list(range(1, 23)))
        self.assertEqual(self.protocol["case_matrix"]["planned_scored_cuda_identities"], 22)
        self.assertEqual(self.protocol["case_matrix"]["absolute_process_attempt_ceiling"], 24)
        self.assertEqual(self.protocol["case_matrix"]["maximum_identical_infrastructure_retries"], 2)
        self.assertNotIn("C00-X-MID", observed)

    def test_lbm_settings_thresholds_and_g0_barrier(self) -> None:
        lbm = self.protocol["lbm"]
        self.assertEqual(lbm["backend"], "taichi_cuda")
        self.assertEqual(lbm["precision"], "float64")
        self.assertEqual(lbm["tau_plus"], 1.2)
        self.assertEqual(lbm["minimum_steps"], 1500)
        self.assertEqual(lbm["maximum_steps"], 50000)
        self.assertEqual(lbm["forces"], {"LOW": 5e-7, "MID": 1e-6, "HIGH": 2e-6})
        self.assertFalse(lbm["cpu_substitution"])
        self.assertEqual(self.protocol["thresholds"], {
            "Mach_max": 0.05,
            "Re_L_max": 0.10,
            "returned_identity_relative_tolerance": 1e-12,
            "force_fit_R2_min": 0.9999,
            "q_over_g_max_relative_deviation": 0.01,
            "normalized_intercept_max": 0.005,
            "broadly_similar_porosity_absolute_delta_max": 0.015,
            "near_directional_connectivity_loss_retention_max": 0.25,
        })
        self.assertEqual(self.protocol["g0_state"], {
            "target_numerically_derived": False,
            "geometry_generated": False,
            "retained_masks": 0,
            "taichi_executions": 0,
            "cuda_executions": 0,
            "openfoam_executions": 0,
        })


if __name__ == "__main__":
    unittest.main()
