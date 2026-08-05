from __future__ import annotations

import csv
import hashlib
import importlib.util
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
        cls.geometry = json.loads(
            (CASE_ROOT / "XSV_TAICHI_002_GEOMETRY_MANIFEST.json").read_text(encoding="utf-8")
        )
        with (CASE_ROOT / "XSV_TAICHI_002_TARGET_INPUTS.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            cls.target_rows = list(csv.DictReader(handle))
        cls.result = json.loads(
            (CASE_ROOT / "XSV_TAICHI_002_RESULT.json").read_text(encoding="utf-8")
        )
        cls.artifacts = json.loads(
            (CASE_ROOT / "XSV_TAICHI_002_ARTIFACT_MANIFEST.json").read_text(encoding="utf-8")
        )
        reducer_path = CASE_ROOT / "xsv_taichi_002_review_reducer_v2.py"
        spec = importlib.util.spec_from_file_location("xsv002_review_reducer", reducer_path)
        assert spec is not None and spec.loader is not None
        cls.reducer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.reducer)

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
        manifest = self.geometry
        self.assertEqual(manifest["status"], "FROZEN_BEFORE_RETAINED_LBM_EXECUTION")
        self.assertEqual(manifest["repeat_identity"], "PASS")
        self.assertEqual(manifest["unique_mask_count"], 12)
        self.assertEqual(manifest["retained_lbm_runs_before_freeze"], 0)
        records = {item["mask_id"]: item for item in manifest["geometries"]}
        self.assertEqual(len(records), 12)
        self.assertEqual(records["H-A0-S42"]["payload_sha256"],
                         "10d9a010cbac4b8579154456c4271ecd2808af5116beab15a2ffd4e2c99cd039")
        self.assertEqual(records["H-A0-S42"]["phi_gross"], 0.412359375)
        self.assertEqual(records["H-A0-S42"]["phi_connected_x"], 0.41234375)
        self.assertEqual([records[key]["removed_voxel_count"] for key in ("C05", "C15", "C30")],
                         [1320, 3959, 7917])
        self.assertTrue(all(item["through_x"] and item["through_y"] and item["through_z"]
                            for item in records.values()))

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
        launcher = (ROOT / "scripts/xsv_taichi_002.py").read_text(encoding="utf-8")
        runtime = (CASE_ROOT / "xsv_taichi_002_runtime.py").read_text(encoding="utf-8")
        self.assertEqual(launcher.splitlines()[0], "#!/usr/bin/env python3")
        self.assertTrue((ROOT / "scripts/xsv_taichi_002.py").stat().st_mode & 0o111)
        for forbidden in ("import numpy", "import pandas", "import scipy", "import taichi"):
            self.assertNotIn(forbidden, launcher)
        for entrypoint in ("periodic_surface_ranking", "connectivity",
                           "generate_geometries", "run_cuda", "main"):
            self.assertIn(f"def {entrypoint}(", runtime)
        self.assertIn("arch=\"gpu\", dtype=\"f64\"", runtime)
        self.assertIn("refusing to overwrite", runtime)
        for matrix_field in ("geometry_id", "axis_permutation", "force_lu"):
            self.assertIn(f'row["{matrix_field}"]', runtime)
        for stale_field in ('row["mask_id"]', 'row["permutation"]', 'row["g_lu"]'):
            self.assertNotIn(stale_field, runtime)

    def test_final_package_is_primitive_derived_and_fail_closed(self) -> None:
        result = self.result
        runs = result["runs"]
        expected = [row["run_id"] for row in self.rows]
        observed = [row["run_id"] for row in runs]
        self.assertEqual(observed, expected)
        self.assertEqual(len(observed), len(set(observed)))
        for row in runs:
            self.assertTrue(row["converged"])
            self.assertLess(row["completed_steps"], row["maximum_steps"])
            self.assertGreater(row["q_box_lu"], 0.0)
            self.assertLessEqual(row["Mach"], 0.05)
            self.assertLessEqual(row["Re_L"], 0.10)
            self.assertLessEqual(row["gross_area_identity_residual"], 1e-12)
            self.assertTrue(math.isclose(
                row["K_gross_lu"], row["nu_lu"] * row["q_box_lu"] / row["g_lu"],
                rel_tol=1e-15, abs_tol=0.0,
            ))
            self.assertEqual(row["binding_status"], "PASS")
        for fit in result["linearity"].values():
            self.assertGreaterEqual(fit["R2"], 0.9999)
            self.assertLessEqual(fit["maximum_q_over_g_relative_deviation"], 0.01)
            self.assertLessEqual(fit["normalized_intercept"], 0.005)
            self.assertTrue(fit["pass"])
        self.assertEqual(result["family_dispositions"]["constriction"],
                         "REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_CONSTRICTION_ENVELOPE")
        self.assertEqual(result["family_dispositions"]["heterogeneity"],
                         "REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_HETEROGENEITY_ENVELOPE")
        self.assertEqual(result["family_dispositions"]["localization"],
                         "FLOW_LOCALIZATION_RESPONSE_REPORTED_DESCRIPTIVELY_NO_PROSPECTIVE_CHANGE_THRESHOLD")
        self.assertEqual(result["claim_ceiling"]["physical_validation"], "NOT_ESTABLISHED")
        self.assertEqual(result["claim_ceiling"]["next_stage"], "NOT_AUTHORIZED")
        self.assertEqual(self.artifacts["external_manifest"]["member_count"], 92)
        self.assertEqual(self.artifacts["external_archive"]["regular_file_count"], 93)
        for relative, digest in self.artifacts["committed_members"].items():
            self.assertEqual(hashlib.sha256((CASE_ROOT / relative).read_bytes()).hexdigest(), digest)
        self.assertEqual(sum(name.endswith(".svg") for name in self.artifacts["committed_members"]), 10)

        reducer_text = (CASE_ROOT / "xsv_taichi_002_review_reducer_v2.py").read_text()
        self.assertNotIn('gates = {"G0_', reducer_text)
        self.assertNotIn('FLOW_LOCALIZATION_CHANGED_WITHOUT_REQUIRED_BULK_PERMEABILITY_COLLAPSE',
                         reducer_text)
        self.assertEqual(hashlib.sha256((CASE_ROOT / "xsv_taichi_002_runtime.py").read_bytes()).hexdigest(),
                         "3bbf089ab5855bdbaeabb9a569ec9176974e8c25499a0c43c0d011be69d74a75")
        self.assertEqual(result["reduction"]["pre_review_result_sha256"],
                         "f4d2cd03bb794ac89e2aba0ddbb133e8ed531d14dc5fb41d7e4a009197259236")
        self.assertEqual(result["chronology"]["chronological_execution_order"],
                         "CHRONOLOGICAL_EXECUTION_ORDER_NOT_INDEPENDENTLY_RECONSTRUCTED")
        self.assertTrue(all(item["status"] == "PASS" for item in result["gates"].values()))
        for item in result["gates"].values():
            self.assertTrue(item["checks"])
            self.assertTrue(item["validation_rule"])
            self.assertIsNone(item["failure_reason"])

        binding_names = {item["check"] for item in result["run_binding_checks"]}
        required_bindings = {
            "run_id", "run_order", "geometry_id", "geometry_payload", "direction",
            "axis_permutation", "force_level", "force", "tau_plus", "precision",
            "cuda_backend", "convergence_tolerance", "check_interval", "minimum_steps",
            "maximum_steps", "puckworks_commit", "puckworks_tree",
            "puckworks_source_hashes", "mask_shape", "mask_dtype",
            "velocity_identity", "log_identity",
        }
        self.assertTrue(required_bindings <= binding_names)
        for name in required_bindings:
            mutation = self.reducer.check(name, "MUTATED", "FROZEN", "synthetic mutation")
            self.assertFalse(mutation["pass"], name)

        # Counterfactual family branches are derived, including no pooled robustness.
        synthetic_geometry = {
            "H-A0-S42": {"phi_connected_x": 0.4},
            "C30": {"phi_connected_x": 0.2, "through_x": True},
        }
        synthetic_rows = {
            "C05-X-MID": {"K_over_directional_baseline": 0.2},
            "C15-X-MID": {"K_over_directional_baseline": 0.8},
            "C30-X-MID": {"K_over_directional_baseline": 0.8},
        }
        self.assertEqual(self.reducer.classify_constriction(
            synthetic_rows, 0.373, synthetic_geometry),
            "REQUIRED_COLLAPSE_ATTAINED_BY_MODERATE_SYNTHETIC_CONSTRICTION")
        synthetic_rows["C05-X-MID"]["K_over_directional_baseline"] = 0.8
        synthetic_rows["C30-X-MID"]["K_over_directional_baseline"] = 0.2
        self.assertEqual(self.reducer.classify_constriction(
            synthetic_rows, 0.373, synthetic_geometry),
            "REQUIRED_COLLAPSE_ATTAINED_ONLY_BY_SEVERE_SYNTHETIC_CONSTRICTION")
        synthetic_geometry["C30"]["phi_connected_x"] = 0.05
        self.assertEqual(self.reducer.classify_constriction(
            synthetic_rows, 0.373, synthetic_geometry),
            "REQUIRED_COLLAPSE_ATTAINED_ONLY_NEAR_DIRECTIONAL_CONNECTIVITY_LOSS")
        synthetic_geometry["C30"]["through_x"] = False
        self.assertEqual(self.reducer.classify_constriction(
            synthetic_rows, 0.373, synthetic_geometry),
            "REQUIRED_COLLAPSE_CROSSED_ONLY_AFTER_DIRECTIONAL_CONNECTIVITY_LOSS")
        self.assertEqual(self.reducer.classify_overall(
            "REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_CONSTRICTION_ENVELOPE",
            "REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_HETEROGENEITY_ENVELOPE"),
            "REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_X_DIRECTION_ENVELOPE")

        hetero = result["heterogeneity"]
        self.assertEqual(set(hetero["by_amplitude"]), {"1", "2"})
        self.assertFalse(hetero["pooled_count_used_for_robustness"])
        for amplitude in hetero["by_amplitude"].values():
            self.assertEqual(len({row["seed"] for row in amplitude["paired_seed_results"]}), 3)
            self.assertEqual(amplitude["attainment_count"],
                             sum(row["target_attained"] for row in amplitude["paired_seed_results"]))

        ratios = result["anisotropy"]["C30_direction_normalized_K_ratios"]
        self.assertTrue(math.isclose(ratios["Y"], 0.17610126503036505, rel_tol=1e-15))
        self.assertTrue(math.isclose(ratios["Z"], 0.1937468574408694, rel_tol=1e-15))
        source = (CASE_ROOT / "plots/XSV_TAICHI_002_PLOT_SOURCE.csv").read_text()
        self.assertIn("0.37327310642080013", source)
        self.assertIn("0.4545454545454545", source)
        for name in ("k_ratio_vs_gross_porosity.svg", "k_ratio_vs_connected_porosity.svg",
                     "coating_response.svg", "heterogeneity_response.svg",
                     "k_ratio_vs_localization.svg", "directional_permeability.svg"):
            text = (CASE_ROOT / "plots" / name).read_text()
            self.assertIn("PRIMARY APPARENT-CONDUCTANCE TARGET 0.37327310642080013", text)
            self.assertIn("NOMINAL-PRESSURE ORDERING SCREEN 0.4545454545454545", text)


if __name__ == "__main__":
    unittest.main()
