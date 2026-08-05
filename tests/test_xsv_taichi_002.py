from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import shutil
import tempfile
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
        reducer_path = CASE_ROOT / "xsv_taichi_002_review_reducer_v4.py"
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

        reducer_text = (CASE_ROOT / "xsv_taichi_002_review_reducer_v4.py").read_text()
        self.assertNotIn('gates = {"G0_', reducer_text)
        self.assertNotIn('FLOW_LOCALIZATION_CHANGED_WITHOUT_REQUIRED_BULK_PERMEABILITY_COLLAPSE',
                         reducer_text)
        self.assertEqual(hashlib.sha256((CASE_ROOT / "xsv_taichi_002_runtime.py").read_bytes()).hexdigest(),
                         "3bbf089ab5855bdbaeabb9a569ec9176974e8c25499a0c43c0d011be69d74a75")
        self.assertEqual(result["reduction"]["start_result_sha256"],
                         "2d2315dab8855560c8c7aaf31ec2f6908c1698e80395f435fcca42660691a708")
        self.assertEqual(result["chronology"]["chronological_execution_order"],
                         "CHRONOLOGICAL_EXECUTION_ORDER_NOT_INDEPENDENTLY_RECONSTRUCTED")
        self.assertEqual(result["local_package_status"], "PASS_WITH_TYPED_PROVENANCE_LIMITATION")
        self.assertTrue(all(item["status"] in {"PASS", "PASS_WITH_TYPED_PROVENANCE_LIMITATION"}
                            for item in result["gates"].values()))
        self.assertEqual(result["gates"]["G3_BOUNDED_TAICHI_CUDA_EXECUTION"]["status"],
                         "PASS_WITH_TYPED_PROVENANCE_LIMITATION")
        for item in result["gates"].values():
            self.assertTrue(item["checks"])
            for evidence_check in item["checks"]:
                self.assertIn("observed", evidence_check)
                self.assertIn("expected", evidence_check)
                self.assertTrue(evidence_check["evidence_path"])
                self.assertTrue(evidence_check["derivation"])
                self.assertIsNone(evidence_check["typed_failure_reason"])

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
            mutation = self.reducer.ck(name, "MUTATED", "FROZEN", "synthetic mutation",
                                       "integrated binding comparison")
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

        self.assertEqual(result["historical_g0"]["head"],
                         "df50ec4be2734e26aa91715d3c27009ad32d0cc1")
        self.assertEqual(result["historical_g0"]["historical_protocol_sha256"],
                         "4f3d6a528620b3d9d1d9ce39b3b9f088deb37586d33b3d761f690049610a3d7c")
        self.assertEqual(result["historical_g0"]["current_protocol_sha256"],
                         "04911d266c77470f7d7a83a39842090100407a43fc3a36990b2177eea5496c28")
        self.assertEqual(result["historical_g0"]["ci_disposition"], "PASS")
        self.assertEqual(len(result["geometry_verification"]), 12)
        self.assertTrue(all(row["repeat_byte_identity"] for row in result["geometry_verification"]))
        self.assertEqual(result["attempt_provenance"]["process_attempt_count"],
                         "NOT_INDEPENDENTLY_RECONSTRUCTED")
        with (CASE_ROOT / "XSV_TAICHI_002_RUN_MANIFEST.csv").open(newline="") as handle:
            self.assertNotIn("attempt_id", next(csv.DictReader(handle)))

        # Actual gate builders fail closed against isolated mutated package inputs.
        with tempfile.TemporaryDirectory(dir=CASE_ROOT) as temporary:
            temporary_path = Path(temporary)
            target = temporary_path / "target.json"
            inputs = temporary_path / "inputs.csv"
            shutil.copy2(CASE_ROOT / "XSV_TAICHI_002_TARGET.json", target)
            shutil.copy2(CASE_ROOT / "XSV_TAICHI_002_TARGET_INPUTS.csv", inputs)
            old_target, old_inputs = self.reducer.TARGET, self.reducer.TARGET_INPUTS
            try:
                self.reducer.TARGET, self.reducer.TARGET_INPUTS = target, inputs
                checks, _ = self.reducer.target_checks(target, inputs)
                self.assertTrue(all(item["pass"] for item in checks))
                text = inputs.read_text().replace("2.057772", "2.157772", 1)
                inputs.write_text(text)
                checks, _ = self.reducer.target_checks(target, inputs)
                self.assertTrue(any(not item["pass"] for item in checks))
            finally:
                self.reducer.TARGET, self.reducer.TARGET_INPUTS = old_target, old_inputs

        with tempfile.TemporaryDirectory(dir=CASE_ROOT) as temporary:
            auth_path = Path(temporary) / "authorization.json"
            auth = json.loads((CASE_ROOT / "XSV_TAICHI_002_STAGE_AUTHORIZATION.json").read_text())
            auth["merge_authority"] = "GRANTED"
            auth_path.write_text(json.dumps(auth))
            old_auth = self.reducer.v3.AUTH
            try:
                self.reducer.v3.AUTH = auth_path
                checks, _ = self.reducer.v3.historical_authority()
                self.assertTrue(any(item["check"] == "merge_authority" and not item["pass"]
                                    for item in checks))
            finally:
                self.reducer.v3.AUTH = old_auth

    def test_v4_real_package_mutations_fail_closed(self) -> None:
        reducer = self.reducer
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for _, (relative, _) in reducer.FROZEN.items():
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)
            self.assertTrue(all(item["pass"] for item in reducer.frozen_checks(root)))
            for key in ("protocol", "matrix", "target", "target_inputs", "geometry", "runtime"):
                relative = reducer.FROZEN[key][0]
                path = root / relative
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                failed = {item["check"] for item in reducer.frozen_checks(root) if not item["pass"]}
                self.assertIn(f"frozen_{key}_sha256", failed)
                path.write_bytes(original)

        with tempfile.TemporaryDirectory() as temporary:
            matrix = Path(temporary) / "matrix.csv"
            shutil.copy2(CASE_ROOT / "XSV_TAICHI_002_CASE_MATRIX.csv", matrix)
            checks, rows = reducer.matrix_checks(matrix)
            self.assertTrue(all(item["pass"] for item in checks))
            duplicate = [dict(row) for row in rows]
            duplicate[1]["run_id"] = duplicate[0]["run_id"]
            with matrix.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(duplicate[0]), lineterminator="\n")
                writer.writeheader(); writer.writerows(duplicate)
            checks, _ = reducer.matrix_checks(matrix)
            self.assertTrue(any(item["check"] == "matrix_unique_run_ids" and not item["pass"] for item in checks))
            reordered = list(reversed(rows))
            with matrix.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(reordered[0]), lineterminator="\n")
                writer.writeheader(); writer.writerows(reordered)
            checks, _ = reducer.matrix_checks(matrix)
            self.assertTrue(any(item["check"] == "matrix_ordered_run_ids" and not item["pass"] for item in checks))

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target.json"
            inputs = Path(temporary) / "inputs.csv"
            shutil.copy2(CASE_ROOT / "XSV_TAICHI_002_TARGET.json", target)
            shutil.copy2(CASE_ROOT / "XSV_TAICHI_002_TARGET_INPUTS.csv", inputs)
            target_data = json.loads(target.read_text())
            target_data["inputs"][0]["mass_flow_g_s"] *= 2
            target_data["inputs"][2]["mass_flow_g_s"] *= 2
            target.write_text(json.dumps(target_data))
            with inputs.open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            rows[0]["mass_flow_g_s"] = str(float(rows[0]["mass_flow_g_s"]) * 2)
            rows[2]["mass_flow_g_s"] = str(float(rows[2]["mass_flow_g_s"]) * 2)
            with inputs.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
                writer.writeheader(); writer.writerows(rows)
            checks, _ = reducer.target_checks(target, inputs)
            self.assertFalse(next(x for x in checks if x["check"] == "target_frozen_hash")["pass"])
            self.assertFalse(next(x for x in checks if x["check"] == "target_inputs_frozen_hash")["pass"])

        mixed = "not FINES_CONFIRMED\nThe result is FINES_CONFIRMED\n"
        findings = reducer.claim_occurrences(mixed)
        self.assertTrue(any(item["pass"] for item in findings))
        self.assertTrue(any(not item["pass"] for item in findings))
        self.assertTrue(all(item["pass"] for item in reducer.claim_occurrences(
            "FINES_CONFIRMED: NOT_ESTABLISHED\nProhibited: CLOGGING_CONFIRMED\n")))

        a = [{"path": "x", "bytes": 1, "sha256": "a"}]
        b = [{"path": "x", "bytes": 1, "sha256": "b"}]
        self.assertFalse(reducer.compare_inventories(a, b, a)[0]["pass"])
        self.assertFalse(reducer.compare_inventories(a, a, b)[1]["pass"])

        with tempfile.TemporaryDirectory(dir=CASE_ROOT) as temporary:
            artifact = Path(temporary) / "artifact.json"
            data = json.loads((CASE_ROOT / "XSV_TAICHI_002_ARTIFACT_MANIFEST.json").read_text())
            first = next(iter(data["committed_members"]))
            data["committed_members"][first] = "0" * 64
            artifact.write_text(json.dumps(data))
            checks = reducer.artifact_checks(artifact, CASE_ROOT,
                ROOT / "PACKAGE_QA_STATUS.json", CASE_ROOT / "XSV_TAICHI_002_RESULT.json")
            self.assertTrue(any(not item["pass"] for item in checks))
            data = json.loads((CASE_ROOT / "XSV_TAICHI_002_ARTIFACT_MANIFEST.json").read_text())
            data["committed_members"].pop("XSV_TAICHI_002_RESULT.json")
            artifact.write_text(json.dumps(data))
            checks = reducer.artifact_checks(artifact, CASE_ROOT,
                ROOT / "PACKAGE_QA_STATUS.json", CASE_ROOT / "XSV_TAICHI_002_RESULT.json")
            self.assertFalse(next(x for x in checks if x["check"] == "artifact_required_classes")["pass"])

        for field, value, check_name in (
            ("result_sha256", "0" * 64, "qa_result_hash"),
            ("physical_validation", "ESTABLISHED", "qa_physical_validation"),
            ("xsv_taichi_003", "AUTHORIZED", "qa_next_stage"),
        ):
            with tempfile.TemporaryDirectory() as temporary:
                qa = Path(temporary) / "qa.json"
                payload = json.loads((ROOT / "PACKAGE_QA_STATUS.json").read_text())
                payload["xsv_taichi_002"][field] = value
                qa.write_text(json.dumps(payload))
                checks = reducer.artifact_checks(
                    CASE_ROOT / "XSV_TAICHI_002_ARTIFACT_MANIFEST.json", CASE_ROOT,
                    qa, CASE_ROOT / "XSV_TAICHI_002_RESULT.json")
                self.assertFalse(next(x for x in checks if x["check"] == check_name)["pass"])

    def test_final_evidence_adjudication_is_consistent_and_bounded(self) -> None:
        adjudication_path = CASE_ROOT / "XSV_TAICHI_002_FINAL_EVIDENCE_ADJUDICATION.json"
        adjudication = json.loads(adjudication_path.read_text())
        deterministic = adjudication["deterministic_reduction_evidence"]
        binding = adjudication["run_binding_evidence"]
        self.assertEqual(
            adjudication["bound_identities"]["historical_g9_deterministic_record_sha256"],
            "88617500c4c4d6934e751d297e6f1c1efeb9d596548f82b0b1f41101894762e0",
        )
        self.assertEqual(deterministic["independent_second_reduction"], "NOT_ESTABLISHED")
        self.assertEqual(binding["real_temporary_package_mutation_coverage"], "PARTIAL")
        self.assertEqual(binding["direct_run_to_matrix_binding"], "PASS")
        self.assertEqual(binding["direct_primitive_artifact_binding"], "PASS")
        self.assertEqual(adjudication["scientific_disposition"], self.result["overall_synthesis"])

        qa = json.loads((ROOT / "PACKAGE_QA_STATUS.json").read_text())["xsv_taichi_002"]
        self.assertEqual(qa["independent_second_reduction"], "NOT_ESTABLISHED")
        self.assertEqual(qa["run_binding_real_input_mutation_coverage"], "PARTIAL")
        self.assertEqual(qa["run_binding_direct_verification"], "PASS")
        self.assertEqual(qa["package_disposition"], adjudication["package_disposition"])
        self.assertEqual(
            qa["final_evidence_adjudication_sha256"],
            hashlib.sha256(adjudication_path.read_bytes()).hexdigest(),
        )

        summary = (CASE_ROOT / "XSV_TAICHI_002_SUMMARY.md").read_text()
        project = (ROOT / "docs/PROJECT_STATE.md").read_text()
        for text in (summary, project, json.dumps(qa), json.dumps(adjudication)):
            lower = text.lower()
            self.assertNotIn("two independent reductions executed", lower)
            self.assertNotIn("complete real-input mutation coverage for every run-binding class", lower)
            self.assertNotIn("/home/", text)
        self.assertIn("does not independently establish", summary)
        self.assertIn("remains partial", project)

        frozen = {
            "xsv_taichi_002_review_reducer_v4.py": "37459e5e6f2c278f69455d073c699b06f71a413369a7f19342d7b9a9f8c61965",
            "XSV_TAICHI_002_RESULT.json": "01ee56ed97cf0779450e6d22e249cc3de1d22701f08edd88e10f0feafe7e31af",
            "XSV_TAICHI_002_PROTOCOL.json": "c8582edbc494a32379a5b28a4e12f2230521183962cd940bd58c8cfc504ff297",
            "XSV_TAICHI_002_CASE_MATRIX.csv": "74a709b8a766587cfd97194cf001002a19c124152173ad4a9d50f3bf804b7ed2",
            "XSV_TAICHI_002_TARGET.json": "388655e6a7f4043f7acd5d26d672f8d3843a44277c1b173a639b823f92278472",
            "XSV_TAICHI_002_GEOMETRY_MANIFEST.json": "b635a1e83b0e04f0b29ddc27baa870a13ad0771e3c197766eba3664aeb86832a",
        }
        for relative, expected in frozen.items():
            self.assertEqual(hashlib.sha256((CASE_ROOT / relative).read_bytes()).hexdigest(), expected)
        self.assertEqual(self.artifacts["external_manifest"]["sha256"],
                         "7b9a83c403d4eb9e15d0ccfb65f88fc38371d4c12975f80ddf543757364f4a4e")
        self.assertEqual(self.artifacts["external_archive"]["sha256"],
                         "dbcf996c3334ef9d910de8c1cf0df3e7c1698523a2eda1aee037e9e95a67fab2")


if __name__ == "__main__":
    unittest.main()
