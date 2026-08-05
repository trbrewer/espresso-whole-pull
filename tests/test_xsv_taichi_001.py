import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import unittest


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "verification/cases/xsv_taichi_001"


class XSVTaichi001Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = json.loads(
            (CASE_ROOT / "XSV_TAICHI_001_PROTOCOL.json").read_text(encoding="utf-8")
        )
        with (CASE_ROOT / "XSV_TAICHI_001_CASE_MATRIX.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            cls.matrix = list(csv.DictReader(handle))

    def test_frozen_protocol_identity_and_quantity_contract(self) -> None:
        protocol = self.protocol
        self.assertEqual(protocol["task"], "XSV-TAICHI-001")
        self.assertEqual(
            protocol["sources"]["puckworks"]["commit"],
            "fc61c4670ec7bf801e40bb391aab16048b8da26b",
        )
        self.assertEqual(
            protocol["sources"]["puckworks"]["tree"],
            "1d553e44ee2f7480a5df521560801b478618cc84",
        )
        quantities = protocol["quantities"]
        self.assertEqual(quantities["phi_gross"], "N_fluid / N_total")
        self.assertEqual(
            quantities["K_gross_lu"], "nu_lu * q_box_lu / g_lu"
        )
        self.assertEqual(
            protocol["adapters"]["primary"]["K_EWP_lu"],
            "phi_gross * k_puckworks_returned",
        )
        self.assertNotEqual(
            protocol["adapters"]["primary"]["K_EWP_lu"],
            protocol["adapters"]["alternate_diagnostic"]["K_ALT_lu"],
        )
        self.assertEqual(
            protocol["claim_ceiling"]["physical_validation"], "NOT_ESTABLISHED"
        )

        launcher_path = ROOT / "scripts/xsv_taichi_001.py"
        runtime_path = CASE_ROOT / "xsv_taichi_001_runtime.py"
        self.assertTrue(launcher_path.is_file())
        self.assertTrue(runtime_path.is_file())
        self.assertTrue(os.access(launcher_path, os.X_OK))
        self.assertTrue(launcher_path.stat().st_mode & stat.S_IXUSR)
        launcher = launcher_path.read_text(encoding="utf-8")
        runtime = runtime_path.read_text(encoding="utf-8")
        self.assertEqual(launcher.splitlines()[0], "#!/usr/bin/env python3")
        self.assertIn("runpy.run_path", launcher)
        self.assertIn('"verification"', launcher)
        self.assertIn('"cases"', launcher)
        self.assertIn('"xsv_taichi_001"', launcher)
        self.assertIn('"xsv_taichi_001_runtime.py"', launcher)
        forbidden_import = re.compile(
            r"^\s*(?:from|import)\s+(?:numpy|pandas|scipy|taichi)(?:\s|\.|$)",
            re.MULTILINE,
        )
        self.assertIsNone(forbidden_import.search(launcher))
        for function_name in (
            "generate_mask",
            "connected_descriptor",
            "generate_geometry",
            "run_lbm",
            "parse_args",
            "main",
        ):
            self.assertIn(f"def {function_name}(", runtime)
        self.assertIn(
            'EXPECTED_PUCKWORKS_COMMIT = "fc61c4670ec7bf801e40bb391aab16048b8da26b"',
            runtime,
        )
        self.assertIn("Path(__file__).resolve().parents[3]", runtime)
        self.assertIn("sys.dont_write_bytecode = True", runtime)
        self.assertIn('lbm = subparsers.add_parser("run-lbm")', runtime)
        self.assertIn('k_gross = nu_lu * q_box / g_lu', runtime)
        self.assertIn('k_void = nu_lu * u_void / g_lu', runtime)
        fixture = json.loads(
            (CASE_ROOT / "openfoam/XSV_TAICHI_001_OPENFOAM_FIXTURES.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(fixture["runs"]), 8)
        self.assertEqual(fixture["closure"]["K_B_over_K_A"], 0.4)
        self.assertEqual(fixture["domain"]["radial_cells"], 512)
        self.assertEqual(fixture["retained_openfoam_runs_before_freeze"], 0)
        geometry_manifest = CASE_ROOT / "XSV_TAICHI_001_GEOMETRY_MANIFEST.json"
        self.assertEqual(
            hashlib.sha256(geometry_manifest.read_bytes()).hexdigest(),
            "5ddb9617b3543d7f48eecf5941291d265894a6cd2d5a142265a0750ab509afdd",
        )

    def test_exact_prospective_run_matrices(self) -> None:
        lbm = [row for row in self.matrix if row["family"] == "LBM"]
        openfoam = [row for row in self.matrix if row["family"] == "OPENFOAM"]
        self.assertEqual(len(lbm), 19)
        self.assertEqual(len(openfoam), 8)
        self.assertEqual(len({row["run_id"] for row in self.matrix}), 27)
        self.assertEqual({row["precision"] for row in lbm}, {"float64"})
        self.assertEqual(
            {row["geometry"] for row in lbm}, {"CH33", "SP32", "M0A"}
        )
        self.assertEqual(
            {row["fixture"] for row in openfoam},
            {"UNIFORM", "AXIAL_TWO_LAYER", "RADIAL_TWO_ZONE"},
        )
        self.assertTrue(all(row["status"] == "PROSPECTIVE" for row in self.matrix))

    def test_geometry_definitions_and_thresholds_are_exact(self) -> None:
        geometry = self.protocol["geometry_definitions"]
        self.assertEqual(geometry["CH33"]["shape"], [33, 33, 33])
        self.assertEqual(
            geometry["SP32"],
            {"function": "lb_reference.sphere_case", "L": 32, "c_nom": 0.08},
        )
        self.assertEqual(geometry["M0A"]["seed"], 42)
        self.assertEqual(geometry["M0A"]["hetero_amp"], 0.0)
        thresholds = self.protocol["thresholds"]
        self.assertEqual(thresholds["backend_relative_q_max"], 0.0025)
        self.assertEqual(thresholds["channel_relative_error_max"], 0.0075)
        self.assertEqual(thresholds["returned_identity_relative_tolerance"], 1e-12)
        self.assertEqual(thresholds["serial_mpi_relative_difference_max"], 1e-8)

    def test_authorized_radial_mesh_alignment_amendment_is_fail_closed(self) -> None:
        amendment_path = CASE_ROOT / "XSV_TAICHI_001_PROTOCOL_AMENDMENT_001.json"
        fixture_path = CASE_ROOT / "openfoam/XSV_TAICHI_001_OPENFOAM_FIXTURES.json"
        amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertEqual(
            amendment["authorization_id"],
            "XSV-TAICHI-001-G5-RADIAL-MESH-ALIGNMENT-2026-08-04",
        )
        self.assertEqual(
            amendment["original_authorities"]["machine_protocol"]["sha256"],
            "d93323c9f78bed1e23f18f70e783f3d849d93831133ddef45368fb65e62d187e",
        )
        self.assertEqual(
            amendment["original_authorities"]["openfoam_fixture"]["sha256"],
            "62f1d1963e9778c4bc41d77eaeb7b14b416a4631c6cea8b8d1d922ce05c050fa",
        )
        self.assertEqual(
            hashlib.sha256(amendment_path.read_bytes()).hexdigest(),
            self.protocol["protocol_amendment_001"]["sha256"],
        )
        domain = fixture["domain"]
        profile = fixture["profiles"]["radial_two_zone"]
        old = fixture["profiles"]["superseded_radial_fixture_revision_1"]
        self.assertEqual(domain["radial_cells"], 512)
        self.assertEqual(domain["radial_grading"], 1.0)
        ideal = domain["radial_cells"] / math.sqrt(2.0)
        self.assertAlmostEqual(ideal, 362.0386719675123)
        departures = {
            j: abs((j / domain["radial_cells"]) ** 2 - 0.5)
            for j in range(1, domain["radial_cells"])
        }
        selected = profile["interface_face_index"]
        self.assertEqual(selected, 362)
        self.assertEqual(
            [j for j, value in departures.items() if value == min(departures.values())],
            [selected],
        )
        radius = domain["basket_radius_m"] * selected / domain["radial_cells"]
        f_inner = (selected / domain["radial_cells"]) ** 2
        f_outer = 1.0 - f_inner
        self.assertEqual(radius, profile["interface_radius_m"])
        self.assertEqual(f_inner, profile["declared_inner_area_fraction"])
        self.assertEqual(f_outer, profile["declared_outer_area_fraction"])
        self.assertNotEqual(profile["interface_radius_m"], old["interface_radius_m"])
        self.assertNotEqual(profile["declared_inner_area_fraction"], 0.5)
        self.assertFalse(old["executable"])
        k_a = fixture["closure"]["K_A_m2"]
        k_b = fixture["closure"]["K_B_m2"]
        k_effective = f_inner * k_a + f_outer * k_b
        target_q = next(
            row["target_q_m_s"]
            for row in fixture["runs"]
            if row["run_id"] == "OF-PARALLEL-1"
        )
        delta_p = (
            fixture["fluid"]["dynamic_viscosity_Pa_s"]
            * domain["bed_depth_m"]
            * target_q
            / k_effective
        )
        self.assertEqual(k_effective, profile["K_parallel_effective_m2"])
        self.assertEqual(delta_p, 0.5315118640909556)
        self.assertNotEqual(delta_p, old["delta_p_Pa"])
        self.assertEqual(f_inner * k_a / k_effective, profile["expected_inner_flow_share"])
        self.assertEqual(f_outer * k_b / k_effective, profile["expected_outer_flow_share"])
        self.assertEqual(f_inner + f_outer, 1.0)
        self.assertEqual(fixture["closure"]["K_B_over_K_A"], 0.4)
        self.assertEqual(profile["solver_alignment_tolerance"], 1e-8)
        self.assertEqual(len(fixture["runs"]), 8)
        self.assertEqual(
            {row["run_id"] for row in fixture["runs"]},
            {row["run_id"] for row in self.matrix if row["family"] == "OPENFOAM"},
        )
        accounting = fixture["process_attempt_accounting"]
        self.assertEqual(accounting["ceiling"], 9)
        self.assertEqual(accounting["protocol_invalid_pre_solve_attempts"], 1)
        self.assertEqual(len(accounting["remaining_authorized_invocations"]), 3)
        self.assertEqual(
            amendment["accepted_predecessor_results"]["OF-SERIES-1"]["disposition"],
            "COMPLETE_PASS",
        )
        self.assertEqual(amendment["completed_predecessor_results_rerun"], "PROHIBITED")
        self.assertFalse(amendment["unchanged_inputs"]["thresholds_changed"])
        self.assertFalse(amendment["governing_physics_changed"])
        self.assertEqual(amendment["physical_validation"], "NOT_ESTABLISHED")
        self.assertEqual(
            hashlib.sha256(
                (ROOT / "docs/strategy/WHOLE_PULL_MODELING_AND_SIMULATION_STRATEGY.md").read_bytes()
            ).hexdigest(),
            "8f6736c89da502b4b41d115292a504b0b83e28bfb94366f4cc83848309d810ab",
        )
        roadmap = (ROOT / "docs/strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("`XSV-TAICHI-002`", roadmap)
        self.assertIn("candidate only, not authorized", roadmap)

    def test_frozen_geometry_manifest_is_complete_and_connected(self) -> None:
        manifest = json.loads(
            (CASE_ROOT / "XSV_TAICHI_001_GEOMETRY_MANIFEST.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["generation_repetitions"], 2)
        self.assertEqual(manifest["repeat_identity"], "PASS")
        self.assertFalse(
            manifest["connectivity"][
                "connected_porosity_used_to_redefine_flow_or_permeability"
            ]
        )
        geometries = {row["case_id"]: row for row in manifest["geometries"]}
        self.assertEqual(set(geometries), {"CH33", "SP32", "M0A"})
        expected_payloads = {
            "CH33": "9bf1654efe5045c59f8b0bbb0b2f537b390382522a1c34bfaaa294635240edd7",
            "SP32": "40196fd2f2b86de853f2afcfce801b6da0fca1d399e107c6ed40328776ed5a85",
            "M0A": "10d9a010cbac4b8579154456c4271ecd2808af5116beab15a2ffd4e2c99cd039",
        }
        expected_configs = {
            "CH33": "674b2f00791e0f12f9dd5cf8c26b98afd56f2ccde81980189cfddda7c5afbebb",
            "SP32": "6f086749b44555938e2b5612c2a41ebcc6536661756a541a78f5c1657d6eb9ac",
            "M0A": "4c5ded6230ec5781c810d2a8f53a92a507a3b393cc99f16d9c2a8e5fb027b4f9",
        }
        for case_id, row in geometries.items():
            self.assertEqual(row["payload_sha256"], expected_payloads[case_id])
            self.assertEqual(
                row["geometry_config_sha256"], expected_configs[case_id]
            )
            self.assertTrue(row["x_through_connected"])
            self.assertGreater(row["phi_gross"], 0.0)
            self.assertLess(row["phi_gross"], 1.0)
            self.assertLessEqual(row["phi_x_connected"], row["phi_gross"])
        self.assertEqual(manifest["retained_flow_solutions_before_freeze"], 0)

    def test_final_reduced_package_recomputes_all_gates_and_claim_boundaries(self) -> None:
        result_path = CASE_ROOT / "XSV_TAICHI_001_RESULT.json"
        summary_path = CASE_ROOT / "XSV_TAICHI_001_SUMMARY.csv"
        artifact_path = CASE_ROOT / "XSV_TAICHI_001_ARTIFACT_MANIFEST.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        self.assertEqual(result["case_matrix"], {"lbm": 19, "openfoam": 8})
        self.assertEqual(len(result["lbm_runs"]), 19)
        self.assertEqual(len(result["openfoam_runs"]), 8)
        self.assertEqual(result["process_attempts"]["openfoam"], 9)
        self.assertEqual(result["process_attempts"]["protocol_invalid_pre_solve"], 1)
        self.assertEqual(
            result["protocol_invalid_attempt"]["disposition"],
            "PROTOCOL_INVALID_PRE_SOLVE_MESH_INTERFACE_MISALIGNMENT",
        )
        self.assertEqual(set(result["gates"].values()), {"PASS"})
        self.assertEqual(
            result["overall_disposition"],
            "XSV_TAICHI_001_CLOSURE_PARITY_ESTABLISHED",
        )
        thresholds = self.protocol["thresholds"]
        parity = result["backend_parity"]
        self.assertLessEqual(
            parity["maximum_numpy_taichi_K_relative_difference"],
            thresholds["backend_relative_K_gross_max"],
        )
        self.assertLessEqual(
            parity["maximum_taichi_cpu_cuda_K_relative_difference"],
            thresholds["backend_relative_K_gross_max"],
        )
        self.assertTrue(
            all(value <= thresholds["mid_force_velocity_relative_L2_max"]
                for value in parity["mid_force_velocity_relative_L2"].values())
        )
        for metrics in result["force_linearity"].values():
            self.assertGreaterEqual(metrics["R2"], thresholds["force_linearity_R2_min"])
            self.assertLessEqual(metrics["q_over_g_max_relative_deviation"], thresholds["q_over_g_max_relative_deviation"])
            self.assertLessEqual(metrics["normalized_intercept"], thresholds["normalized_intercept_max"])
        channel = result["channel_adapter"]
        self.assertLessEqual(channel["maximum_gross_relative_error"], thresholds["channel_relative_error_max"])
        self.assertLessEqual(channel["returned_k_identity_max_relative_error"], thresholds["returned_identity_relative_tolerance"])
        self.assertGreaterEqual(channel["primary_adapter_advantage"], thresholds["primary_adapter_advantage_min"])
        self.assertLessEqual(result["openfoam_uniform"]["maximum_total_flow_relative_error"], thresholds["uniform_relative_error_max"])
        self.assertLessEqual(result["openfoam_uniform"]["porosity_invariance_relative_difference"], thresholds["porosity_invariance_relative_difference_max"])
        self.assertLessEqual(result["mesh_preflight"]["maximum_mesh_zone_area_relative_error"], 1e-8)
        for family in ("series", "parallel"):
            self.assertLessEqual(result[family]["serial"]["total_flow_relative_error"], thresholds["composition_relative_error_max"])
            self.assertLessEqual(result[family]["mpi"]["total_flow_relative_error"], thresholds["composition_relative_error_max"])
            self.assertLessEqual(result[family]["serial_mpi_total_flow_relative_difference"], thresholds["serial_mpi_relative_difference_max"])
        self.assertEqual(result["claim_ceiling"]["physical_validation"], "NOT_ESTABLISHED")
        self.assertEqual(result["claim_ceiling"]["independent_data_gate"], "UNCHANGED")
        self.assertFalse(result["prohibited_work"]["XSV_TAICHI_002_started"])
        text = result_path.read_text(encoding="utf-8") + artifact_path.read_text(encoding="utf-8")
        self.assertNotIn("/home/", text)
        self.assertNotIn("tim-MS-", text)
        self.assertEqual(
            artifact["committed_members"]["XSV_TAICHI_001_RESULT.json"],
            hashlib.sha256(result_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            artifact["committed_members"]["XSV_TAICHI_001_SUMMARY.csv"],
            hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        )
        with summary_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len([row for row in rows if row["row_class"] == "GOVERNED_RUN"]), 27)
        self.assertEqual(len([row for row in rows if row["row_class"] == "PROTOCOL_INVALID_ATTEMPT"]), 1)


if __name__ == "__main__":
    unittest.main()
