import csv
import copy
import hashlib
import importlib.util
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
        runtime_text = runtime_path.read_text(encoding="utf-8")
        self.assertNotIn('gates = {name: "PASS"', runtime_text)
        self.assertNotIn('"overall_disposition": "XSV_TAICHI_001_CLOSURE_PARITY_ESTABLISHED"', runtime_text)
        self.assertNotIn('"disposition": "PASS", "primary_value"', runtime_text)
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
            "088ae61a044737d1ed126590f0e27a7e7c008089a2f39cfa523108f7e9962fe0",
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
        self.assertEqual({key: result["gates"][key] for key in ("G0", "G1", "G2", "G3", "G4", "G5")}, {key: "PASS" for key in ("G0", "G1", "G2", "G3", "G4", "G5")})
        self.assertEqual(result["gates"]["G6_LOCAL_PACKAGE"], "LEGACY_DERIVED_FIELD_PROVENANCE_INCOMPLETE")
        self.assertEqual(result["gates"]["FINAL_EXACT_HEAD_CI"], "RESOLVE_FROM_GITHUB_AT_REVIEW")
        self.assertEqual(result["gates"]["FINAL_EXACT_HEAD_REVIEW"], "PENDING")
        self.assertEqual(
            result["overall_disposition"],
            "XSV_TAICHI_001_COMPLETE_WITH_TYPED_FAILURES",
        )
        self.assertEqual(result["scientific_disposition"], "XSV_TAICHI_001_CLOSURE_PARITY_ESTABLISHED")
        self.assertEqual(result["package_disposition"], "XSV_TAICHI_001_COMPLETE_WITH_TYPED_PROVENANCE_LIMITATION")
        self.assertEqual(result["trace_derived_field_integrity"], "LEGACY_DERIVED_FIELD_PROVENANCE_INCOMPLETE")
        composition_fluxes = [
            result["series"]["serial"]["boundary_flux_imbalance_relative"],
            result["series"]["mpi"]["boundary_flux_imbalance_relative"],
            result["parallel"]["serial"]["boundary_flux_imbalance_relative"],
            result["parallel"]["mpi"]["boundary_flux_imbalance_relative"],
        ]
        maximum_composition_flux = max(composition_fluxes)
        self.assertTrue(math.isclose(maximum_composition_flux,
                                     2.1659767311672455e-12,
                                     rel_tol=1e-12, abs_tol=1e-12))
        authority_text = (ROOT / "docs/verification/XSV_TAICHI_001_SATURATED_HYDRAULIC_CLOSURE_PARITY.md").read_text(encoding="utf-8")
        def current_summary_is_valid(text: str) -> bool:
            return (
                "2.1659767311672455e-12" in text
                and "unchanged `1e-6` scientific gate" in text
                and "Flux imbalance is below `1e-12` for the composition fixtures" not in text
            )

        self.assertTrue(current_summary_is_valid(authority_text))
        self.assertFalse(current_summary_is_valid(
            authority_text.replace("2.1659767311672455e-12", "1.0e-12")
        ))
        self.assertFalse(current_summary_is_valid(
            authority_text + "\nFlux imbalance is below `1e-12` for the composition fixtures.\n"
        ))
        qa = json.loads((ROOT / "PACKAGE_QA_STATUS.json").read_text(encoding="utf-8"))["xsv_taichi_001"]
        self.assertNotIn("overall_scientific_disposition", qa)
        self.assertEqual(qa["scientific_disposition"], result["scientific_disposition"])
        self.assertEqual(qa["package_disposition"], result["package_disposition"])
        self.assertEqual(qa["overall_compatibility_disposition"], result["overall_disposition"])
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
        self.assertTrue(all(row["disposition"] == "PASS" for row in rows if row["row_class"] == "GOVERNED_RUN"))

        expected_lbm = {row["run_id"] for row in self.matrix if row["family"] == "LBM"}
        expected_openfoam = {row["run_id"] for row in self.matrix if row["family"] == "OPENFOAM"}
        self.assertEqual({row["run_id"] for row in result["lbm_runs"]}, expected_lbm)
        self.assertEqual({row["run_id"] for row in result["openfoam_runs"]}, expected_openfoam)
        self.assertEqual(len({row["run_id"] for row in result["lbm_runs"]}), 19)
        self.assertEqual(len({row["run_id"] for row in result["openfoam_runs"]}), 8)
        failed = [check for check in result["gate_evaluation"]["checks"] if not check["pass"]]
        self.assertTrue(failed)
        self.assertEqual({check["gate"] for check in failed}, {"G6_LOCAL_PACKAGE"})
        self.assertEqual({check["typed_failure"] for check in failed}, {"LEGACY_DERIVED_FIELD_PROVENANCE_INCOMPLETE"})
        self.assertEqual(result["external_evidence"]["manifest_member_count"], 1545)
        self.assertEqual(result["external_evidence"]["manifest_source_bytes"], 134226177)
        self.assertTrue(result["external_evidence"]["all_manifest_members_verified"])
        self.assertTrue(result["external_evidence"]["archive_inventory_verified"])

        runtime_path = CASE_ROOT / "xsv_taichi_001_runtime.py"
        spec = importlib.util.spec_from_file_location("xsv_gate_evaluator", runtime_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        baseline = runtime.evaluate_gate_contract(copy.deepcopy(result["evaluation_inputs"]))
        self.assertEqual(baseline["overall_disposition"], "XSV_TAICHI_001_COMPLETE_WITH_TYPED_FAILURES")
        self.assertEqual(baseline["scientific_disposition"], "XSV_TAICHI_001_CLOSURE_PARITY_ESTABLISHED")
        self.assertEqual(baseline["package_disposition"], "XSV_TAICHI_001_COMPLETE_WITH_TYPED_PROVENANCE_LIMITATION")

        composition = [result["series"]["serial"], result["series"]["mpi"],
                       result["parallel"]["serial"], result["parallel"]["mpi"]]
        all_openfoam = result["openfoam_runs"]
        self.assertEqual(len(all_openfoam), 8)
        for row in all_openfoam:
            self.assertTrue(math.isclose(
                row["boundary_flux_imbalance_relative"],
                runtime.relative_difference(row["inlet_flow_m3_s"], row["outlet_flow_m3_s"]),
                rel_tol=1e-12, abs_tol=1e-12,
            ))
            self.assertLessEqual(row["boundary_flux_imbalance_relative"],
                                 thresholds["flux_imbalance_relative_max"])
        for row in composition:
            csv_source = next(source for source in row["primitive_trace_sources"]
                              if source["member_identity"] == "FINAL_ROW")
            self.assertEqual(csv_source["fields"], ["inlet_flow_m3_s", "outlet_flow_m3_s"])
            self.assertEqual(csv_source["final_row_index"], 0)
            self.assertEqual(csv_source["final_row_time_s"], "0.02")
            self.assertTrue(math.isclose(
                row["flux_imbalance_relative"],
                runtime.relative_difference(row["inlet_flow_m3_s"], row["outlet_flow_m3_s"]),
                rel_tol=1e-12, abs_tol=1e-12,
            ))
            self.assertLessEqual(row["flux_imbalance_relative"], thresholds["flux_imbalance_relative_max"])
            self.assertTrue(math.isclose(
                row["previous_hybrid_inlet_aggregate_relative_difference"],
                runtime.relative_difference(row["inlet_flow_m3_s"], row["total_flow_m3_s"]),
                rel_tol=1e-12, abs_tol=1e-12,
            ))
            self.assertTrue(math.isclose(
                row["aggregate_total_vs_boundary_outlet_relative_difference"],
                runtime.relative_difference(row["total_flow_m3_s"], row["outlet_flow_m3_s"]),
                rel_tol=1e-12, abs_tol=1e-12,
            ))
            self.assertEqual(row["legacy_flux_imbalance_provenance"]["disposition"],
                             "LEGACY_DERIVED_FIELD_PROVENANCE_INCOMPLETE")
            self.assertEqual(row["legacy_flux_imbalance_provenance"]["generating_formula"],
                             "NOT_ESTABLISHED_FROM_RETAINED_EVIDENCE")

        tolerance = self.protocol["thresholds"]["returned_identity_relative_tolerance"]
        for row in result["lbm_runs"]:
            lineage = row["formula_lineage"]
            nu = (row["tau_plus"] - 0.5) / 3.0
            u_void = row["q_box_lu"] / row["phi_gross"]
            recomputed = {"nu_lu": nu, "u_void_lu": u_void,
                          "K_gross_lu": nu * row["q_box_lu"] / row["g_lu"],
                          "K_void_lu": nu * u_void / row["g_lu"],
                          "Mach": math.sqrt(3.0) * row["u_max_lu"],
                          "Re_L": u_void * {"CH33": 33, "SP32": 32, "M0A": 40}[row["case_id"]] / nu}
            for field, value in recomputed.items():
                self.assertTrue(math.isclose(lineage[field], value, rel_tol=tolerance, abs_tol=tolerance))
                self.assertTrue(math.isclose(row[field], value, rel_tol=tolerance, abs_tol=tolerance))
        handoff = result["closure_handoff_lineage"]
        self.assertEqual(handoff["source_run_ids"], ["M0A-TG-LOW", "M0A-TG-MID", "M0A-TG-HIGH"])
        self.assertEqual(handoff["origin_fit"]["recomputed"], 7.679991073929766)
        self.assertEqual(handoff["K_A_lu"]["recomputed"], 1.7919979172502785)
        self.assertEqual(handoff["K_A_m2"]["recomputed"], 1.6127981255252507e-09)
        self.assertEqual(handoff["K_B_m2"]["recomputed"], 6.451192502101003e-10)
        self.assertEqual(handoff["porosity"]["geometry"], handoff["porosity"]["fixture"])
        self.assertEqual(handoff["disposition"], "PASS")
        self.assertEqual(artifact["external_manifest_member_count"], 1545)
        self.assertEqual(artifact["external_archive_regular_file_count"], 1546)
        self.assertEqual(artifact["external_archive_file_count"], 1546)

        def mutate_check(fragment: str, value) -> dict:
            mutated = copy.deepcopy(result["evaluation_inputs"])
            candidates = [row for row in mutated["checks"] if fragment in row["check_id"]]
            self.assertTrue(candidates, fragment)
            candidates[0]["observed"] = value
            return mutated

        mutations = {
            "nonfinite_lbm": mutate_check("q_box_lu_finite", False),
            "unconverged_lbm": mutate_check("_converged", False),
            "completed_at_max": mutate_check("_completed_steps", 50000),
            "mach": mutate_check("_mach", 1.0),
            "reynolds": mutate_check("_reynolds", 1.0),
            "q_parity": mutate_check("numpy_taichi_q_box_lu_parity", 1.0),
            "K_parity": mutate_check("numpy_taichi_K_gross_lu_parity", 1.0),
            "velocity_l2": mutate_check("velocity_L2", 1.0),
            "force_linearity": mutate_check("_R2", 0.0),
            "channel_error": mutate_check("channel_gross_error", 1.0),
            "returned_k": mutate_check("returned_k_identity", 1.0),
            "adapter_advantage": mutate_check("primary_adapter_advantage", 0.0),
            "uniform_flow": mutate_check("OF-U-LOW_total_flow", 1.0),
            "uniform_q_dp": mutate_check("uniform_Q_over_delta_p", 1.0),
            "uniform_flux": mutate_check("OF-U-LOW_flux_imbalance", 1.0),
            "porosity_invariance": mutate_check("porosity_invariance", 1.0),
            "series_flow": mutate_check("OF-SERIES-1_total_flow", 1.0),
            "series_share": mutate_check("series_serial_layer_A", 1.0),
            "series_mpi_share": mutate_check("serial_mpi_series_A", 1.0),
            "radial_flow": mutate_check("OF-PARALLEL-1_total_flow", 1.0),
            "radial_share": mutate_check("radial_serial_inner", 1.0),
            "radial_mpi_share": mutate_check("serial_mpi_radial_inner", 1.0),
            "composition_flux": mutate_check("OF-SERIES-1_flux_imbalance", 1.0),
            "composition_boundary_outlet": mutate_check("OF-PARALLEL-1_flux_imbalance", 1.0),
            "aggregate_boundary_consistency": mutate_check("aggregate_total_boundary_outlet_consistency", 1.0),
            "unsupported_reproduced_claim": mutate_check("legacy_flux_provenance", "STORED_DERIVED_FIELD_REPRODUCED"),
            "missing_invalid_attempt": mutate_check("protocol_invalid_attempt", "MISSING"),
            "manifest_hash": mutate_check("external_manifest_sha256", "mismatch"),
            "archive_hash": mutate_check("external_archive_sha256", "mismatch"),
            "unverified_external": mutate_check("external_all_manifest_members_verified", False),
            "physical_validation": mutate_check("physical_validation_ceiling", True),
            "xsv_002": mutate_check("xsv_taichi_002_inactive", True),
            "lbm_K_lineage": mutate_check("K_gross_lu_formula_lineage", -1.0),
            "lbm_u_void_lineage": mutate_check("u_void_lu_formula_lineage", -1.0),
            "closure_source_runs": mutate_check("M0A_source_run_identity", ["M0A-TG-LOW"]),
            "closure_origin_fit": mutate_check("M0A_origin_fit_identity", -1.0),
            "closure_K_A_lu": mutate_check("M0A_K_A_lu_identity", -1.0),
            "closure_K_A_m2": mutate_check("M0A_K_A_m2_identity", -1.0),
            "closure_delta_x": mutate_check("M0A_delta_x_identity", -1.0),
            "closure_K_B": mutate_check("M0A_K_B_m2_identity", -1.0),
            "fixture_porosity": mutate_check("M0A_porosity_handoff", -1.0),
            "domain_bed_depth": mutate_check("domain_bed_depth_identity", -1.0),
            "domain_area": mutate_check("domain_gross_area_identity", -1.0),
            "domain_radius": mutate_check("domain_basket_radius_identity", -1.0),
        }
        omitted = copy.deepcopy(result["evaluation_inputs"]); omitted["observed_lbm_ids"].pop(); mutations["omitted_run"] = omitted
        duplicate = copy.deepcopy(result["evaluation_inputs"]); duplicate["observed_lbm_ids"].append(duplicate["observed_lbm_ids"][0]); mutations["duplicate_run"] = duplicate
        for name, mutated in mutations.items():
            with self.subTest(mutation=name):
                evaluated = runtime.evaluate_gate_contract(mutated)
                self.assertEqual(evaluated["overall_disposition"], "XSV_TAICHI_001_COMPLETE_WITH_TYPED_FAILURES")
                self.assertTrue(any(not check["pass"] for check in evaluated["checks"]))
                if name in {"composition_flux", "composition_boundary_outlet"}:
                    self.assertEqual(evaluated["gates"]["G5"], "COMPOSITION_FLUX_BALANCE_FAILED")
                    self.assertEqual(evaluated["scientific_disposition"], "XSV_TAICHI_001_COMPLETE_WITH_TYPED_FAILURES")
                if name == "unsupported_reproduced_claim":
                    self.assertEqual(evaluated["gates"]["G5"], "PASS")
                    self.assertEqual(evaluated["package_disposition"],
                                     "XSV_TAICHI_001_COMPLETE_WITH_TYPED_PROVENANCE_LIMITATION")


if __name__ == "__main__":
    unittest.main()
