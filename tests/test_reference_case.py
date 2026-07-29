from __future__ import annotations

import csv
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from espresso_reference_math import (  # noqa: E402
    analytical_preview,
    b0_reduced_simulation,
    discrete_layered_pressure_reference,
    first_drip_time_s,
    positive_driving_pressure_integral,
    straight_sided_wedge_scale,
)
from generate_source_manifest import excluded  # noqa: E402
from freeze_contract import verify_source_manifest as verify_freeze_source_manifest  # noqa: E402
from prepare_case import render_control_dict  # noqa: E402
from verify_source_manifest import verify_manifest as verify_shared_source_manifest  # noqa: E402
from run_qualification import (  # noqa: E402
    PRIMARY_KEYS,
    aggregate_standard,
    write_runs_csv,
)

REFERENCE = json.loads((ROOT / "config/reference_R0.json").read_text(encoding="utf-8"))
LAYERED = json.loads((ROOT / "config/fixture_layered_pressure.json").read_text(encoding="utf-8"))


class ReferenceMathematicsTests(unittest.TestCase):
    def test_bed_depth_is_derived(self) -> None:
        bed = REFERENCE["coffee_bed"]
        geometry = REFERENCE["geometry"]
        expected = bed["dry_dose_kg"] / (
            bed["particle_solid_density_kg_m3"]
            * (1.0 - bed["initial_porosity"])
            * math.pi
            * geometry["basket_radius_m"] ** 2
        )
        self.assertAlmostEqual(expected, bed["bed_depth_m"], places=15)

    def test_exact_first_drip_reference_value(self) -> None:
        self.assertAlmostEqual(first_drip_time_s(REFERENCE), 4.71169618523187, places=13)

    def test_pressure_integral_matches_ramp_triangle_and_plateau(self) -> None:
        target = 900000.0
        ramp = 3.0
        self.assertAlmostEqual(
            positive_driving_pressure_integral(0.0, ramp, target, ramp, 0.0),
            0.5 * target * ramp,
            places=8,
        )
        self.assertAlmostEqual(
            positive_driving_pressure_integral(0.0, 5.0, target, ramp, 0.0),
            0.5 * target * ramp + target * 2.0,
            places=8,
        )

    def test_pressure_integral_honours_positive_front_threshold(self) -> None:
        target = 100.0
        ramp = 10.0
        front = 25.0
        # Driving pressure becomes positive at 2.5 s; 2.5..5 is a triangle
        # rising from 0 to 25 Pa.
        self.assertAlmostEqual(
            positive_driving_pressure_integral(0.0, 5.0, target, ramp, front),
            0.5 * 2.5 * 25.0,
            places=12,
        )

    def test_exact_straight_sided_wedge_scale(self) -> None:
        scale = straight_sided_wedge_scale(5.0)
        self.assertAlmostEqual(scale, 72.09146648398465, places=13)
        radius = REFERENCE["geometry"]["basket_radius_m"]
        depth = REFERENCE["coffee_bed"]["bed_depth_m"]
        wedge_volume = 0.5 * radius * radius * math.sin(math.radians(5.0)) * depth
        cylinder_volume = math.pi * radius * radius * depth
        self.assertAlmostEqual(scale * wedge_volume, cylinder_volume, places=18)

    def test_analytical_preview_uses_corrected_reference(self) -> None:
        preview = analytical_preview(REFERENCE)
        self.assertAlmostEqual(preview["first_drip_s"], 4.71169618523187, places=13)
        self.assertAlmostEqual(
            preview["steady_outlet_volume_flow_m3_s"],
            1.4826759715944223e-6,
            places=18,
        )
        self.assertAlmostEqual(
            preview["saturated_pore_water_mass_kg"],
            0.00919047619047619,
            places=16,
        )

    def test_b0_reduced_twin_conserves_and_is_bounded(self) -> None:
        result = b0_reduced_simulation(REFERENCE)
        outputs = result["primary_outputs"]
        self.assertLess(outputs["max_liquid_balance_residual_kg"], 1.0e-12)
        self.assertLess(outputs["max_solute_balance_residual_kg"], 1.0e-12)
        self.assertGreater(outputs["cup_beverage_mass_at_end_kg"], 0.035)
        self.assertLess(outputs["cup_beverage_mass_at_end_kg"], 0.050)
        self.assertAlmostEqual(outputs["first_drip_s"], first_drip_time_s(REFERENCE), places=12)

    def test_layered_discrete_reference_is_nontrivial(self) -> None:
        result = discrete_layered_pressure_reference(LAYERED)
        self.assertAlmostEqual(result["outlet_flow_m3_s"], 1.0108903065127255e-6, places=18)
        probes = result["pressure_probe_values_pa"]
        self.assertGreater(probes[0], probes[1])
        self.assertGreater(probes[0], 500000.0)
        self.assertLess(probes[1], 100000.0)


class PackageContractTests(unittest.TestCase):
    def test_versions_match_v014(self) -> None:
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "0.1.4")
        self.assertEqual(REFERENCE["solver_version"], "0.1.4")
        self.assertEqual(LAYERED["solver_version"], "0.1.4")
        cpp = (ROOT / "solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text(encoding="utf-8")
        self.assertIn("espressoWholePullFoam v0.1.4", cpp)

    def test_reference_remains_explicit_calibration(self) -> None:
        self.assertEqual(REFERENCE["mode"], "calibration")
        self.assertEqual(REFERENCE["calibration"]["parameter"], "saturated_permeability_m2")
        self.assertEqual(REFERENCE["calibration"]["independent_validation_status"], "not_validated")

    def test_qualified_routine_default_is_32_ranks(self) -> None:
        self.assertEqual(REFERENCE["parallel"]["default_subdomains"], 32)
        allrun = (ROOT / "Allrun").read_text(encoding="utf-8")
        self.assertIn("DEFAULT_NPROCS=32", allrun)

    def test_no_physics_change_source_contract_is_bundled(self) -> None:
        baseline = ROOT / "baseline_evidence/v0_1_3/source_contract"
        for name in (
            "espressoWholePullFoam.C",
            "espresso_reference_math.py",
            "reference_R0.json",
            "fixture_layered_pressure.json",
            "Make.files",
            "Make.options",
        ):
            self.assertTrue((baseline / name).is_file(), name)

    def test_explicit_bounded_state_contract_is_declared(self) -> None:
        bounded = REFERENCE["verification"]["bounded_state"]
        self.assertEqual(
            set(bounded),
            {
                "concentration_cap_absolute_tolerance_kg_m3",
                "inventory_absolute_tolerance_kg",
                "retained_water_absolute_tolerance_kg",
                "monotonic_mass_absolute_tolerance_kg",
            },
        )
        postprocess = (ROOT / "scripts/postprocess.py").read_text(encoding="utf-8")
        for name in (
            "concentration_below_declared_capacity",
            "remaining_extractable_inventory_bounded",
            "retained_water_bounded_by_pore_capacity",
            "cumulative_inlet_water_monotonic",
            "cumulative_cup_water_monotonic",
            "cumulative_cup_solute_monotonic",
        ):
            self.assertIn(name, postprocess)

    def test_required_initial_fields_exist_for_both_cases(self) -> None:
        for relative in (
            "cases/reference_R0_20g_58mm_9bar/0.orig",
            "cases/fixture_layered_pressure_v0_1_4/0.orig",
        ):
            zero = ROOT / relative
            for name in (
                "p",
                "U",
                "saturation",
                "wetMask",
                "porosity",
                "permeability",
                "dissolvedConcentration",
                "remainingExtractable",
                "localExtractionRate",
            ):
                self.assertTrue((zero / name).is_file(), f"{relative}/{name}")

    def test_solver_uses_foundation12_explicit_headers(self) -> None:
        cpp = (ROOT / "solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text(encoding="utf-8")
        self.assertNotIn('#include "fvCFD.H"', cpp)
        for header in (
            "argList.H",
            "volFields.H",
            "surfaceFields.H",
            "fvMatrices.H",
            "fvcFlux.H",
            "fvcGrad.H",
            "fvmDdt.H",
            "fvmDiv.H",
            "fvmLaplacian.H",
        ):
            self.assertIn(f'#include "{header}"', cpp)

    def test_solver_contains_hardening_corrections(self) -> None:
        cpp = (ROOT / "solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text(encoding="utf-8")
        self.assertIn("2.0*constant::mathematical::pi/std::sin(wedgeAngleRadians)", cpp)
        self.assertNotIn("360.0/wedgeAngleDegrees", cpp)
        self.assertIn("positiveDrivingPressureIntegral", cpp)
        self.assertIn("pressureIntegralCrossingTime", cpp)
        self.assertIn("axial_two_layer", cpp)
        self.assertIn("pressureProbe1", cpp)

    def test_generated_control_dict_disables_binary_compression(self) -> None:
        text = render_control_dict(REFERENCE)
        self.assertIn("writeFormat     binary;", text)
        self.assertIn("writeCompression off;", text)
        self.assertNotIn("writeCompression on;", text)

    def test_allrun_has_live_logging_fixture_and_timings(self) -> None:
        text = (ROOT / "Allrun").read_text(encoding="utf-8")
        for token in (
            "2>&1 | tee",
            "stage_timings_v0_1_4.tsv",
            "SOLVER_EXECUTABLE",
            'run_case_command "$FIXTURE_CASE" "$SOLVER_EXECUTABLE"',
            'run_case_command "$REFERENCE_CASE" "$SOLVER_EXECUTABLE"',
            "fixture_run_solver",
            "postprocess_layered_fixture.py",
            "ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json",
        ):
            self.assertIn(token, text)

    def test_allverify_declares_full_matrix(self) -> None:
        text = (ROOT / "scripts/run_qualification.py").read_text(encoding="utf-8")
        for token in (
            "--solver-executable",
            "solver_executable_bytes",
            "solver_executable_sha256",
            "dt_0p020_ref_r32",
            "dt_0p010_ref_r32",
            "dt_0p005_ref_r32",
            "mesh_128x256_dt0p010_r16",
            "mesh_512x1024_dt0p010_r64",
            "rank_1_ref_dt0p010",
            "rank_16_ref_dt0p010",
            "rank_64_ref_dt0p010",
            "layered_rank_1",
            "layered_rank_16",
        ):
            self.assertIn(token, text)

    def test_standard_allverify_reuses_build_and_finalizes_terminal_manifest(self) -> None:
        text = (ROOT / "Allverify").read_text(encoding="utf-8")
        self.assertIn("verify_reference_solver_build", text)
        self.assertIn("verify_build_provenance.py", text)
        self.assertIn("SOLVER_EXECUTABLE", text)
        self.assertIn("--solver-executable", text)
        self.assertIn("recorded solver executable path is not absolute", text)
        self.assertIn("finalize_reference_freeze.py", text)
        self.assertIn("postqualification_no_physics_change_verification", text)
        self.assertIn("generate_freeze_manifest.py", text)
        self.assertIn("verify_terminal_freeze_manifest", text)
        self.assertLess(
            text.index("finalize_reference_freeze.py"),
            text.index("generate_freeze_manifest.py"),
        )

    def test_source_manifest_excludes_all_qualification_runtime_products(self) -> None:
        for relative in (
            "qualification/ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json",
            "qualification/NO_PHYSICS_CHANGE_VERIFICATION_STANDARD_V0_1_4.json",
            "qualification/BUILD_PROVENANCE_SMOKE_V0_1_4.json",
            "qualification/log.qualification.standard",
            "qualification_runs/standard/sample/case/result.json",
        ):
            self.assertTrue(excluded(Path(relative)), relative)

    def test_source_manifest_excludes_only_the_approved_puckworks_report(self) -> None:
        self.assertTrue(excluded(Path("docs/integration/PUCKWORKS_UPDATE_IMPACT.md")))
        self.assertFalse(excluded(Path("docs/integration/arbitrary_solver_source.md")))

    def test_source_manifest_excludes_only_the_approved_waszkiewicz_dossier(self) -> None:
        self.assertTrue(excluded(Path("docs/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.md")))
        self.assertFalse(excluded(Path("docs/evidence/arbitrary_scenario_source.md")))

    def test_source_manifest_excludes_only_the_approved_r1_contract(self) -> None:
        self.assertTrue(
            excluded(Path("docs/validation/R1_CALIBRATION_AND_COMPARISON_CONTRACT.md"))
        )
        self.assertFalse(excluded(Path("docs/validation/arbitrary_contract_source.md")))

    def test_waszkiewicz_dossier_contract_is_complete_but_not_frozen(self) -> None:
        dossier = json.loads(
            (
                ROOT / "validation/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            dossier["schema_version"],
            "espresso.public.waszkiewicz_r1_source_dossier.v1",
        )
        self.assertEqual(dossier["analysis_status"], "COMPLETE")
        self.assertEqual(
            dossier["dossier_disposition"],
            "READY_FOR_WP01R_003_WITH_DECLARED_GAPS",
        )
        self.assertEqual(
            dossier["dependency_identity"]["commit"],
            "fc61c4670ec7bf801e40bb391aab16048b8da26b",
        )
        self.assertEqual(
            dossier["dependency_identity"]["tree"],
            "1d553e44ee2f7480a5df521560801b478618cc84",
        )
        allowed = {
            "DIRECT_OBSERVATION",
            "SOURCE_REPORTED_PARAMETER",
            "DIGITIZED_VALUE",
            "DERIVED_VALUE",
            "FITTED_PARAMETER",
            "ENGINEERING_ASSUMPTION",
            "UNAVAILABLE",
        }
        quantities = dossier["quantity_inventory"]
        self.assertTrue(quantities)
        self.assertTrue(all(item["classification"] in allowed for item in quantities))
        self.assertEqual(len(quantities), 42)
        counts = {
            classification: sum(
                item["classification"] == classification for item in quantities
            )
            for classification in allowed
        }
        self.assertEqual(counts["FITTED_PARAMETER"], 11)
        self.assertEqual(counts["ENGINEERING_ASSUMPTION"], 1)
        self.assertEqual(sum(counts.values()), 42)
        self.assertEqual(
            {key: value for key, value in counts.items() if value},
            dossier["quantity_classification_counts"],
        )
        self.assertTrue(
            all(item["role_status"] == "PROPOSED_NOT_FROZEN" for item in quantities)
        )
        by_id = {item["quantity_id"]: item for item in quantities}
        offset = by_id["first-drop-offset"]
        self.assertEqual(offset["classification"], "ENGINEERING_ASSUMPTION")
        self.assertEqual(offset["uncertainty"]["status"], "NOT_ESTIMATED")
        self.assertIsNone(offset["uncertainty"]["value"])
        self.assertEqual(offset["source_recorded_std_field"], 0.0)
        self.assertEqual(
            offset["proposed_r1_role"],
            "EXCLUDED_SOURCE_PROCESSING_ASSUMPTION",
        )
        fitted_ids = {
            item["quantity_id"]
            for item in quantities
            if item["classification"] == "FITTED_PARAMETER"
        }
        self.assertNotIn("first-drop-offset", fitted_ids)
        time_offset = next(
            item
            for item in dossier["time_origin_map"]
            if item["node_id"] == "SOLIDS_FIRST_DROP_OFFSET"
        )
        self.assertEqual(
            time_offset["solver_mapping_status"],
            "EXCLUDED_FROM_FUTURE_SOLVER_TIME_MAPPING",
        )
        covariance_uncertainties = [
            item["uncertainty"]
            for item in quantities
            if item["uncertainty"]["status"] == "SOURCE_FIT_COVARIANCE_STD"
        ]
        self.assertTrue(covariance_uncertainties)
        self.assertTrue(
            all(
                uncertainty["kind"]
                == "CURVE_FIT_COVARIANCE_1SIGMA_APPROXIMATION"
                and "not shot-to-shot experimental standard deviation"
                in uncertainty["note"]
                and "Off-diagonal covariance is not present" in uncertainty["note"]
                for uncertainty in covariance_uncertainties
            )
        )
        self.assertTrue(
            all(
                item["value_status"] != "RIGHTS_WITHHELD_FROM_DOSSIER"
                for item in quantities
                if item["rights_status"].startswith("CC-BY")
            )
        )
        markdown = (
            ROOT / "docs/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.md"
        ).read_text(encoding="utf-8")
        self.assertIn("fixed 8.0 s first-drop offset", markdown)
        self.assertIn("was not optimized with the sigmoid parameters", markdown)
        self.assertIn("not withheld because of a", markdown)
        self.assertNotIn("fitted 8 s first-drop offset", markdown)
        self.assertNotIn("8 s fitted offset", markdown)
        artifacts = dossier["source_artifacts"]
        self.assertTrue(artifacts)
        self.assertTrue(
            all(
                item["rights_status"]
                and item["license_or_restriction"]
                and item["redistribution_treatment"]
                for item in artifacts
            )
        )
        self.assertGreaterEqual(len(dossier["pressure_node_map"]), 3)
        self.assertGreaterEqual(len(dossier["time_origin_map"]), 5)
        gaps = {item["register_id"]: item for item in dossier["missing_data_and_ambiguities"]}
        for required in (
            "basket-versus-bed-diameter",
            "reference-versus-basket-pressure",
            "mass-to-volumetric-flow",
            "time-origin-mapping",
        ):
            self.assertIn(required, gaps)
        boundaries = dossier["authorization_boundaries"]
        self.assertFalse(boundaries["calibration_contract_frozen"])
        self.assertFalse(boundaries["protected_comparison_contract_frozen"])
        self.assertFalse(boundaries["r1_implementation_authorized"])

    def test_r1_contract_is_complete_frozen_and_not_implemented(self) -> None:
        contract_path = (
            ROOT
            / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json"
        )
        markdown_path = (
            ROOT / "docs/validation/R1_CALIBRATION_AND_COMPARISON_CONTRACT.md"
        )
        self.assertTrue(contract_path.is_file())
        self.assertTrue(markdown_path.is_file())
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        dossier = json.loads(
            (
                ROOT / "validation/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            contract["schema_version"],
            "espresso.public.r1_calibration_and_comparison_contract.v1",
        )
        self.assertEqual(contract["contract_status"], "FROZEN_FOR_WP01R_004")
        self.assertEqual(
            contract["authority_status"], "EFFECTIVE_WHEN_MERGED_TO_MAIN"
        )
        self.assertEqual(
            contract["source_dependency"]["commit"],
            "fc61c4670ec7bf801e40bb391aab16048b8da26b",
        )
        self.assertEqual(
            contract["source_dependency"]["tree"],
            "1d553e44ee2f7480a5df521560801b478618cc84",
        )
        self.assertEqual(
            contract["dossier_dependency"]["disposition"],
            "READY_FOR_WP01R_003_WITH_DECLARED_GAPS",
        )
        self.assertEqual(
            contract["dossier_dependency"]["markdown"]["git_blob"],
            "0198b490393e6c75f2b1be627ee67873da495ad7",
        )
        self.assertEqual(
            contract["dossier_dependency"]["json"]["git_blob"],
            "b224ab2a53dbee98f0e3354a3254429f1521d52d",
        )
        allowed_roles = {
            "PRESCRIBED_INPUT",
            "CALIBRATED_PARAMETER",
            "PREDICTED_OUTPUT",
            "PROTECTED_COMPARISON",
            "PLAUSIBILITY_OBSERVATION",
            "UNAVAILABLE_OR_EXCLUDED",
        }
        dossier_ids = {item["quantity_id"] for item in dossier["quantity_inventory"]}
        crosswalk = contract["source_quantity_role_crosswalk"]
        crosswalk_ids = [item["quantity_id"] for item in crosswalk]
        self.assertEqual(len(crosswalk_ids), 42)
        self.assertEqual(len(crosswalk_ids), len(set(crosswalk_ids)))
        self.assertEqual(set(crosswalk_ids), dossier_ids)
        self.assertTrue(all(item["role"] in allowed_roles for item in crosswalk))

        scenario = contract["scenario_inputs"]
        self.assertAlmostEqual(
            scenario["hydraulic_bed_area_m2"], math.pi * 0.028**2, places=18
        )
        expected_porosity = 1.0 - 0.0185 / (
            1400.0 * scenario["hydraulic_bed_area_m2"] * 0.010
        )
        self.assertAlmostEqual(
            scenario["initial_porosity"], expected_porosity, places=15
        )
        pressure = next(
            item
            for item in contract["derived_contract_quantities"]
            if item["quantity_id"] == "late-basket-pressure"
        )
        flow = next(
            item
            for item in contract["derived_contract_quantities"]
            if item["quantity_id"] == "source-static-equilibrium-flow"
        )
        permeability = next(
            item
            for item in contract["derived_contract_quantities"]
            if item["quantity_id"] == "uniform-darcy-permeability"
        )
        calibrated = [
            item
            for item in contract["derived_contract_quantities"]
            if item["role"] == "CALIBRATED_PARAMETER"
        ]
        protected_quantities = [
            item
            for item in contract["derived_contract_quantities"]
            if item["role"] == "PROTECTED_COMPARISON"
        ]
        self.assertEqual(
            [item["quantity_id"] for item in calibrated],
            ["uniform-darcy-permeability"],
        )
        self.assertEqual(
            [item["quantity_id"] for item in protected_quantities],
            [f"protected-flow-shape-9-{index}" for index in range(1, 6)],
        )
        self.assertAlmostEqual(pressure["value"], 8.70902419, places=12)
        pc = contract["calibration_contract"]["source_fit_inputs"]["P_c_bar"]
        qc = contract["calibration_contract"]["source_fit_inputs"]["Q_c_g_per_s"]
        x = pressure["value"] / pc
        expected_flow = qc * x * (4.0 - 6.0 * x + 4.0 * x**2 - x**3)
        self.assertAlmostEqual(flow["value"], expected_flow, places=14)
        expected_permeability = (
            (expected_flow / 1000.0 / scenario["liquid_density_kg_m3"])
            * scenario["dynamic_viscosity_Pa_s"]
            * scenario["bed_depth_m"]
            / (
                scenario["hydraulic_bed_area_m2"]
                * pressure["solver_value_Pa_gauge"]
            )
        )
        self.assertAlmostEqual(
            permeability["value"], expected_permeability, delta=1e-29
        )
        calibration = contract["calibration_contract"]
        self.assertEqual(calibration["active_solver_calibration_degrees_of_freedom"], 1)
        self.assertEqual(
            calibration["active_calibrated_quantity_id"],
            "uniform-darcy-permeability",
        )
        self.assertEqual(
            calibration["source_fit_inputs"]["active_solver_degrees_of_freedom"], 0
        )
        self.assertEqual(
            calibration["wetting_permeability_m2"],
            calibration["saturated_permeability_m2"],
        )
        self.assertEqual(
            calibration["wetting_equals_saturated_status"],
            "EXPLICIT_ENGINEERING_SIMPLIFICATION",
        )
        envelope = calibration["diagnostic_envelope"]
        self.assertEqual(
            envelope["kind"], "NONPROBABILISTIC_SOURCE_FIT_CORNER_ENVELOPE"
        )
        self.assertFalse(envelope["confidence_interval"])
        self.assertFalse(envelope["endpoint_can_rescue_failed_comparison"])

        protected = contract["protected_comparison_contract"]
        self.assertEqual(protected["shot_ids"], ["9-1", "9-2", "9-3", "9-4", "9-5"])
        self.assertEqual(
            protected["protected_indices"],
            {"first": 100, "last": 899, "inclusive": True},
        )
        self.assertEqual(
            protected["normalization_indices"],
            {"first": 900, "last": 999, "inclusive": True},
        )
        self.assertEqual(
            protected["metrics"]["undefined_pearson_disposition"], "FAIL"
        )
        self.assertEqual(
            contract["time_mapping_contract"]["source_to_solver_offset_s"], 3.0
        )
        self.assertFalse(
            contract["time_mapping_contract"]["source_first_drop_offset_8s_used"]
        )
        for forbidden in (
            "permeability selection",
            "time shifting",
            "pressure adjustment",
            "smoothing selection",
            "amplitude scaling",
        ):
            self.assertIn(forbidden, protected["forbidden_uses"])
        self.assertEqual(calibration["optimizer_iterations"], 0)
        self.assertEqual(calibration["post_run_calibration_iterations"], 0)
        self.assertFalse(
            any(
                token in protected["quantity"].lower()
                for token in ("tds", "extraction yield", "dissolved mass")
            )
        )
        excluded_text = " ".join(contract["unavailable_or_excluded"]).lower()
        for token in (
            "carman-kozeny",
            "brewer quadratic",
            "poroelastic",
            "structural evolution",
        ):
            self.assertIn(token, excluded_text)
        boundaries = contract["authorization_boundaries"]
        self.assertFalse(boundaries["r1_case_implemented"])
        self.assertEqual(boundaries["r1_execution_count"], 0)
        self.assertEqual(boundaries["openfoam_execution_count"], 0)
        self.assertEqual(boundaries["parameter_fitting_count"], 0)
        self.assertEqual(boundaries["optimizer_iteration_count"], 0)
        markdown = markdown_path.read_text(encoding="utf-8")
        for token in (
            "FROZEN_FOR_WP01R_004",
            "2.8642613245723525e-15",
            "9-1",
            "indices 100–899",
            "fixed source-processing first-drop offset of 8 s is excluded",
        ):
            self.assertIn(token, markdown)

    def test_puckworks_v2_lock_and_checkout_contract(self) -> None:
        lock = json.loads(
            (ROOT / "dependencies/puckworks.lock.json").read_text(encoding="utf-8")
        )
        selected = "fc61c4670ec7bf801e40bb391aab16048b8da26b"
        self.assertEqual(lock["schema_version"], "espresso.public.puckworks_lock.v2")
        self.assertEqual(lock["repository_url"], "https://github.com/trbrewer/puckworks.git")
        self.assertEqual(lock["checkout_commit"], selected)
        self.assertEqual(
            lock["checkout_tree_sha"],
            "1d553e44ee2f7480a5df521560801b478618cc84",
        )
        checkout = (ROOT / "tools/checkout_puckworks.sh").read_text(encoding="utf-8")
        self.assertIn("dependencies/puckworks.lock.json", checkout)
        self.assertNotIn(selected, checkout)
        self.assertNotIn(lock["historical_reviewed_commit"], checkout)

    def test_source_manifest_is_acyclic_by_construction(self) -> None:
        text = (ROOT / "scripts/prepare_case.py").read_text(encoding="utf-8")
        self.assertIn('"manifest_role": "immutable_scientific_inputs_only"', text)
        self.assertIn('"downstream_artifacts_intentionally_excluded"', text)
        self.assertNotIn('manifest["outputs"]', text)

    def test_allwmake_uses_foam_src_and_normalizes_timestamps(self) -> None:
        text = (ROOT / "Allwmake").read_text(encoding="utf-8")
        self.assertIn('FOAM_SOURCE_ROOT="${FOAM_SRC:-${WM_PROJECT_DIR}/src}"', text)
        self.assertIn("normalize_timestamps.py", text)
        self.assertIn("wclean", text)
        self.assertIn("write_build_provenance.py", text)
        self.assertNotIn("${LIB_SRC}", text)


class ScriptIntegrationTests(unittest.TestCase):
    def test_prepare_case_writes_hardened_properties(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "case"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/prepare_case.py"),
                    "--root",
                    str(ROOT),
                    "--nprocs",
                    "7",
                    "--config",
                    str(ROOT / "config/reference_R0.json"),
                    "--case-dir",
                    str(case),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            properties = (case / "constant/espressoModelProperties").read_text(encoding="utf-8")
            self.assertIn("pressureIntegrationMethod  exactPiecewiseLinearIntegral;", properties)
            self.assertIn("permeabilityProfile        uniform;", properties)
            self.assertIn("pressureProbe1Position", properties)
            control = (case / "system/controlDict").read_text(encoding="utf-8")
            self.assertIn("writeCompression off;", control)
            decompose = (case / "system/decomposeParDict").read_text(encoding="utf-8")
            self.assertIn("numberOfSubdomains 7;", decompose)
            self.assertTrue((case / "preflight/B0_REDUCED_TWIN_V0_1_4.json").is_file())
            manifest = json.loads(
                (case / "ESPRESSO_WHOLE_PULL_REFERENCE_CASE_MANIFEST_V0_1_4.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["manifest_role"], "immutable_scientific_inputs_only")
            self.assertNotIn("outputs", manifest)
            self.assertIn("scientific_bundle_sha256", manifest)

    def test_timestamp_normalizer_repairs_future_solver_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "solver/espressoWholePullFoam/espressoWholePullFoam.C"
            source.parent.mkdir(parents=True)
            source.write_text("int main(){}\n", encoding="utf-8")
            make_file = source.parent / "Make/files"
            make_file.parent.mkdir(parents=True)
            make_file.write_text("x\n", encoding="utf-8")
            future = time.time() + 3600.0
            os.utime(source, (future, future))
            output = root / "report.json"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize_timestamps.py"),
                    "--root",
                    str(root),
                    "--output",
                    str(output),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["normalized_file_count"], 1)
            self.assertLessEqual(source.stat().st_mtime, time.time() + 5.0)

    def test_no_physics_change_verification_passes_against_v013_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "no_physics.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/verify_no_physics_change.py"),
                    "--root",
                    str(ROOT),
                    "--output",
                    str(output),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(
                report["governing_physics_change"], "UNRESOLVED_DIFFERENCE"
            )
            self.assertEqual(
                report["comparison_summary"]["failed_comparisons"],
                ["openfoam_solver_source"],
            )
            self.assertGreaterEqual(report["comparison_summary"]["total"], 28)

    def test_allwmake_mock_environment(self) -> None:
        headers = (
            "argList.H",
            "Time.H",
            "fvMesh.H",
            "volFields.H",
            "surfaceFields.H",
            "IOdictionary.H",
            "fixedValueFvPatchFields.H",
            "zeroGradientFvPatchFields.H",
            "fvMatrices.H",
            "fvcFlux.H",
            "fvcGrad.H",
            "fvmDdt.H",
            "fvmDiv.H",
            "fvmLaplacian.H",
            "PstreamReduceOps.H",
            "mathematicalConstants.H",
            "OSspecific.H",
            "setRootCase.H",
            "createTime.H",
            "createMesh.H",
        )
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            project = temp / "OpenFOAM-12"
            include = project / "src/OpenFOAM/lnInclude"
            include.mkdir(parents=True)
            (project / "src/finiteVolume/lnInclude").mkdir(parents=True)
            (project / "src/meshTools/lnInclude").mkdir(parents=True)
            os_specific = project / "src/OSspecific/POSIX/lnInclude"
            os_specific.mkdir(parents=True)
            for header in headers:
                target = os_specific if header == "OSspecific.H" else include
                (target / header).touch()

            appbin = temp / "user-bin"
            fakebin = temp / "fake-bin"
            fakebin.mkdir()
            (fakebin / "wclean").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (fakebin / "wmake").write_text(
                "#!/usr/bin/env bash\n"
                "set -e\n"
                "mkdir -p \"$FOAM_USER_APPBIN\"\n"
                "printf '#!/usr/bin/env bash\\nexit 0\\n' > \"$FOAM_USER_APPBIN/espressoWholePullFoam\"\n"
                "chmod +x \"$FOAM_USER_APPBIN/espressoWholePullFoam\"\n",
                encoding="utf-8",
            )
            (fakebin / "wclean").chmod(0o755)
            (fakebin / "wmake").chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{fakebin}:/usr/bin:/bin",
                    "WM_PROJECT": "OpenFOAM",
                    "WM_PROJECT_VERSION": "12",
                    "WM_PROJECT_DIR": str(project),
                    "FOAM_USER_APPBIN": str(appbin),
                    "BUILD_PROVENANCE_OUTPUT": str(temp / "build-provenance.json"),
                    "ARCHIVED_EXECUTABLE_OUTPUT": str(temp / "archived-espressoWholePullFoam"),
                    "TIMESTAMP_NORMALIZATION_OUTPUT": str(temp / "timestamp-normalization.json"),
                }
            )
            for name in ("FOAM_SRC", "LIB_SRC", "OPENFOAM_BASHRC"):
                env.pop(name, None)
            result = subprocess.run(
                [str(ROOT / "Allwmake")],
                cwd=str(ROOT),
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("Foundation 12 explicit-header preflight: PASS", result.stdout)
            self.assertTrue((appbin / "espressoWholePullFoam").is_file())
            self.assertTrue((temp / "archived-espressoWholePullFoam").is_file())

    def _status_report(self, log_text: str) -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            case = root / "cases/reference_R0_20g_58mm_9bar"
            case.mkdir(parents=True)
            log = case / "log.test"
            log.write_text(log_text, encoding="utf-8")
            timings = case / "stage_timings_v0_1_4.tsv"
            timings.write_text(
                "stage\tstart_utc\tend_utc\tduration_s\tstatus\texit_code\tlog\n"
                "test\tA\tB\t1.25\tFAIL\t1\tcases/reference/log.test\n",
                encoding="utf-8",
            )
            output = case / "status.json"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/write_run_status.py"),
                    "--root",
                    str(root),
                    "--status",
                    "FAIL",
                    "--stage",
                    "test",
                    "--exit-code",
                    "1",
                    "--current-log",
                    str(log),
                    "--timings",
                    str(timings),
                    "--output",
                    str(output),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            return json.loads(output.read_text(encoding="utf-8"))

    def test_status_treats_foam_sigfpe_enablement_as_information(self) -> None:
        report = self._status_report(
            "sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).\n"
        )
        self.assertEqual(report["diagnostics"]["detected_issue_count"], 0)
        self.assertEqual(report["diagnostics"]["informational_safeguard_count"], 1)

    def test_status_treats_successful_relative_error_metric_as_information(self) -> None:
        report = self._status_report("Mesh-volume relative error: 5.692061406e-15\n")
        self.assertEqual(report["diagnostics"]["detected_issue_count"], 0)
        self.assertEqual(report["diagnostics"]["informational_metric_count"], 1)

    def test_status_still_detects_real_floating_point_exception(self) -> None:
        report = self._status_report("Floating point exception (core dumped)\n")
        self.assertEqual(report["diagnostics"]["detected_issue_count"], 1)

    def test_status_detects_compiler_and_shell_failures(self) -> None:
        report = self._status_report(
            "espressoWholePullFoam.C:15:10: fatal error: missing.H: No such file or directory\n"
            "Allwmake: line 10: LIB_SRC: unbound variable\n"
        )
        issues = report["diagnostics"]["detected_issue_lines"]
        self.assertTrue(any("fatal error" in item["line"] for item in issues))
        self.assertTrue(any("unbound variable" in item["line"] for item in issues))

    def test_status_parses_stage_timing(self) -> None:
        report = self._status_report("ERROR: synthetic\n")
        stages = report["runtime"]["stage_timings"]["stages"]
        self.assertEqual(len(stages), 1)
        self.assertAlmostEqual(stages[0]["duration_s"], 1.25)

    def test_build_provenance_verifier_accepts_exact_reference_binary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            case_preflight = root / "cases/reference_R0_20g_58mm_9bar/preflight"
            case_preflight.mkdir(parents=True)
            build_inputs = []
            for relative, content in (
                ("solver/espressoWholePullFoam/espressoWholePullFoam.C", "source\n"),
                ("solver/espressoWholePullFoam/Make/files", "files\n"),
                ("solver/espressoWholePullFoam/Make/options", "options\n"),
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                import hashlib
                build_inputs.append(
                    {
                        "path": relative,
                        "bytes": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                )
            executable = root / "bin/espressoWholePullFoam"
            executable.parent.mkdir()
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o755)
            import hashlib
            archived = case_preflight / "espressoWholePullFoam_v0_1_4"
            archived.write_bytes(executable.read_bytes())
            archived.chmod(0o755)
            runtime_record = {
                "path": str(executable),
                "bytes": executable.stat().st_size,
                "sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                "executable": True,
            }
            archived_record = {
                "path": str(archived.relative_to(root)),
                "bytes": archived.stat().st_size,
                "sha256": hashlib.sha256(archived.read_bytes()).hexdigest(),
                "executable": True,
            }
            provenance = {
                "status": "PASS",
                "generated_at_utc": "synthetic",
                "environment": {
                    "WM_PROJECT": "OpenFOAM",
                    "WM_PROJECT_VERSION": "12",
                    "WM_OPTIONS": "linux64GccDPInt32Opt",
                },
                "build_inputs": build_inputs,
                "executable": runtime_record,
                "runtime_executable": runtime_record,
                "archived_executable": archived_record,
                "runtime_archive_identity": {"status": "PASS", "same_bytes": True},
                "source_and_executable_bundle_sha256": "synthetic",
            }
            provenance_path = case_preflight / "BUILD_PROVENANCE_V0_1_4.json"
            provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
            output = case_preflight / "verification.json"
            env = os.environ.copy()
            env.update(provenance["environment"])
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/verify_build_provenance.py"),
                    "--root",
                    str(root),
                    "--output",
                    str(output),
                ],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(report["build_input_hashes_match"])
            self.assertTrue(report["executable_hash_matches"])
            self.assertTrue(report["archived_executable_hash_matches"])
            self.assertTrue(report["runtime_archive_identity_matches"])

    def test_synthetic_freeze_finalization_is_acyclic_and_self_verifying(self) -> None:
        import hashlib

        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as runtime_td:
            root = Path(td)
            case = root / "cases/reference_R0_20g_58mm_9bar"
            fixture = root / "cases/fixture_layered_pressure_v0_1_4"
            qualification = root / "qualification"
            preflight = case / "preflight"
            preflight.mkdir(parents=True)
            fixture.mkdir(parents=True)
            qualification.mkdir(parents=True)

            def write_json(path: Path, value: dict) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

            def identity(path: Path) -> dict:
                return {
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }

            empty_aggregate = hashlib.sha256(b"").hexdigest()
            write_json(root / "SOURCE_PACKAGE_MANIFEST.json", {
                "aggregate_source_sha256": empty_aggregate,
                "file_count": 0,
                "files": {},
            })
            executable = Path(runtime_td) / "espressoWholePullFoam"
            executable.parent.mkdir(parents=True, exist_ok=True)
            executable.write_text("binary", encoding="utf-8")
            executable.chmod(0o755)
            archived_executable = preflight / "espressoWholePullFoam_v0_1_4"
            archived_executable.write_bytes(executable.read_bytes())
            archived_executable.chmod(0o755)
            runtime_record = {"path": str(executable), **identity(executable), "executable": True}
            archived_record = {
                "path": str(archived_executable.relative_to(root)),
                **identity(archived_executable),
                "executable": True,
            }
            write_json(preflight / "BUILD_PROVENANCE_V0_1_4.json", {
                "status": "PASS",
                "source_and_executable_bundle_sha256": "bundle",
                "executable": runtime_record,
                "runtime_executable": runtime_record,
                "archived_executable": archived_record,
                "runtime_archive_identity": {"status": "PASS", "same_bytes": True},
            })
            write_json(preflight / "BUILD_PROVENANCE_VERIFICATION_V0_1_4.json", {
                "status": "PASS",
                "build_input_hashes_match": True,
                "executable_hash_matches": True,
                "archived_executable_hash_matches": True,
                "runtime_archive_identity_matches": True,
                "openfoam_build_environment_matches": True,
            })
            write_json(preflight / "TIMESTAMP_NORMALIZATION_V0_1_4.json", {"status": "PASS"})
            write_json(preflight / "NO_PHYSICS_CHANGE_VERIFICATION_V0_1_4.json", {
                "status": "PASS", "governing_physics_change": False
            })
            write_json(qualification / "NO_PHYSICS_CHANGE_VERIFICATION_STANDARD_V0_1_4.json", {
                "status": "PASS", "governing_physics_change": False
            })
            write_json(case / "CASE_SCENARIO_V0_1_4.json", {"scenario_id": "reference"})
            write_json(case / "RUN_ENVIRONMENT_V0_1_4.json", {"wm_project_version": "12"})
            scientific_manifest = case / "ESPRESSO_WHOLE_PULL_REFERENCE_CASE_MANIFEST_V0_1_4.json"
            write_json(scientific_manifest, {
                "manifest_role": "immutable_scientific_inputs_only",
                "scientific_input_sha256": {},
                "scientific_bundle_sha256": empty_aggregate,
                "prepared_at_utc": "prepared",
            })
            write_json(case / "ESPRESSO_WHOLE_PULL_STAGE_TIMINGS_V0_1_4.json", {"stage_count": 1})
            write_json(case / "ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json", {
                "status": "PASS",
                "execution_status": "COMPLETED",
                "artifacts": {},
            })
            trace = case / "ESPRESSO_WHOLE_PULL_REFERENCE_TRACES_V0_1_4.csv"
            trace.write_text("time_s\n0\n", encoding="utf-8")
            field_index = case / "ESPRESSO_WHOLE_PULL_REFERENCE_FIELD_INDEX_V0_1_4.json"
            write_json(field_index, {
                "indexed_file_count": 0,
                "final_time_directory": "30",
                "missing_final_fields": [],
                "files": [],
            })
            foam = case / "reference_R0.foam"
            foam.touch()
            fixture_acceptance = fixture / "ESPRESSO_LAYERED_PRESSURE_FIXTURE_ACCEPTANCE_V0_1_4.json"
            write_json(fixture_acceptance, {"status": "PASS"})
            qualification_runs = {}
            for index in range(10):
                run_id = f"synthetic_{index}"
                run_acceptance = root / f"qualification_runs/{run_id}/case/acceptance.json"
                write_json(run_acceptance, {"status": "PASS"})
                qualification_runs[run_id] = {
                    "status": "PASS",
                    "acceptance": str(run_acceptance.relative_to(root)),
                    "acceptance_sha256": identity(run_acceptance)["sha256"],
                }
            qualification_report = qualification / "ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json"
            write_json(qualification_report, {
                "status": "PASS",
                "profile": "standard",
                "all_required_gates_pass": True,
                "gate_summary": {"pass": 9, "fail": 0, "total": 9},
                "environment": {
                    "solver_executable": str(executable.resolve()),
                    "solver_executable_bytes": executable.stat().st_size,
                    "solver_executable_sha256": identity(executable)["sha256"],
                },
                "runs": qualification_runs,
            })
            runs_csv = qualification / "ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_RUNS_V0_1_4.csv"
            runs_csv.write_text("run_id,status\nsynthetic,PASS\n", encoding="utf-8")

            artifact_paths = [trace, field_index, foam, scientific_manifest]
            gates = {
                name: {"status": "PASS"}
                for name in (
                    "concentration_below_declared_capacity",
                    "remaining_extractable_inventory_bounded",
                    "retained_water_bounded_by_pore_capacity",
                    "cumulative_inlet_water_monotonic",
                    "cumulative_cup_water_monotonic",
                    "cumulative_cup_solute_monotonic",
                )
            }
            acceptance_path = case / "ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json"
            write_json(acceptance_path, {
                "status": "PASS",
                "all_required_reference_gates_pass": True,
                "all_required_bounded_state_gates_pass": True,
                "all_required_monotonicity_gates_pass": True,
                "numerical_acceptance_gates": gates,
                "reference_freeze_status": "NOT_FROZEN",
                "primary_outputs": {},
                "calibration_and_validation": {"physical_validation_status": "NOT_ESTABLISHED"},
                "artifacts": {
                    str(path.relative_to(case)): {**identity(path)} for path in artifact_paths
                },
            })

            finalize = subprocess.run(
                [sys.executable, str(ROOT / "scripts/finalize_reference_freeze.py"), "--root", str(root)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            self.assertEqual(finalize.returncode, 0, finalize.stdout)
            finalized = json.loads(acceptance_path.read_text(encoding="utf-8"))
            self.assertEqual(finalized["reference_freeze_status"], "QUALIFIED")

            freeze = subprocess.run(
                [sys.executable, str(ROOT / "scripts/generate_freeze_manifest.py"), "--root", str(root)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            self.assertEqual(freeze.returncode, 0, freeze.stdout)
            freeze_path = case / "ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json"
            frozen = json.loads(freeze_path.read_text(encoding="utf-8"))
            self.assertEqual(frozen["reference_freeze_status"], "FROZEN / QUALIFIED")
            self.assertEqual(frozen["artifact_verification"]["status"], "PASS")
            self.assertNotIn("ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json", {
                item["path"] for item in frozen["artifacts"]
            })
            before_verification = identity(freeze_path)
            verify = subprocess.run(
                [sys.executable, str(ROOT / "scripts/verify_freeze_manifest.py"), "--root", str(root)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            self.assertEqual(verify.returncode, 0, verify.stdout)
            self.assertEqual(identity(freeze_path), before_verification)

    def test_qualification_csv_ignores_non_tabular_diagnostic_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "runs.csv"
            primary = {key: 1.0 for key in PRIMARY_KEYS}
            primary["max_pressure_iterations"] = 4.0
            primary["mesh_volume_relative_error"] = 0.0
            results = {
                "sample": {
                    "run_id": "sample",
                    "kind": "reference",
                    "axial_cells": 64,
                    "radial_cells": 128,
                    "delta_t_s": 0.02,
                    "ranks": 1,
                    "status": "PASS",
                    "total_stage_duration_s": 1.0,
                    "primary_outputs": primary,
                }
            }
            write_runs_csv(output, results)
            with output.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["run_id"], "sample")
            self.assertNotIn("max_pressure_iterations", rows[0])
            self.assertNotIn("mesh_volume_relative_error", rows[0])

    def test_standard_qualification_aggregator_accepts_equivalent_matrix(self) -> None:
        reference_outputs = {key: 1.0 for key in PRIMARY_KEYS}
        reference_outputs["first_drip_s"] = 4.711696185231869
        layered_outputs = {
            "outlet_flow_m3_s": 1.0e-6,
            "pressure_probe_1_Pa": 500000.0,
            "pressure_probe_2_Pa": 100000.0,
        }
        results = {}
        for run_id in (
            "dt_0p020_ref_r32",
            "dt_0p010_ref_r32",
            "dt_0p005_ref_r32",
            "mesh_128x256_dt0p010_r16",
            "mesh_512x1024_dt0p010_r64",
            "rank_1_ref_dt0p010",
            "rank_16_ref_dt0p010",
            "rank_64_ref_dt0p010",
        ):
            results[run_id] = {"status": "PASS", "primary_outputs": dict(reference_outputs)}
        results["layered_rank_1"] = {
            "status": "PASS",
            "primary_outputs": dict(layered_outputs),
        }
        results["layered_rank_16"] = {
            "status": "PASS",
            "primary_outputs": dict(layered_outputs),
        }
        gates = aggregate_standard(results)
        self.assertTrue(gates)
        self.assertTrue(all(item["status"] == "PASS" for item in gates.values()))


class WP01R006DecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.json_path = (
            ROOT
            / "validation/decisions/WP01R_006_FIRST_WP02_PHYSICS_SELECTION.json"
        )
        self.markdown_path = (
            ROOT / "docs/decisions/WP01R_006_FIRST_WP02_PHYSICS_SELECTION.md"
        )
        self.decision = json.loads(self.json_path.read_text(encoding="utf-8"))

    def test_decision_artifacts_exist_and_agree(self) -> None:
        self.assertTrue(self.json_path.is_file())
        self.assertTrue(self.markdown_path.is_file())
        markdown = self.markdown_path.read_text(encoding="utf-8")
        mechanism = self.decision["selected_mechanism"]
        self.assertIn(mechanism["id"], markdown)
        self.assertIn(self.decision["implementation_issue"]["url"], markdown)

    def test_input_result_and_selection_are_exact(self) -> None:
        residual = self.decision["input_residual"]
        self.assertEqual(
            residual["wp01r_005_merge_commit"],
            "7f2c7a6c8881233574f28be74414f20b04bbf51a",
        )
        self.assertEqual(
            residual["execution_result_sha256"],
            "3a29c38d560c1003cb1c4730323b7241ac37a9ecb67933be9a17c6e37af07d5d",
        )
        self.assertEqual(residual["predicted_normalized_std"], 0.0)
        self.assertEqual(residual["primary_residual"], "STRUCTURAL_MODEL_INADEQUACY")
        self.assertEqual(
            self.decision["selected_mechanism"]["id"],
            "WASZKIEWICZ_SATURATED_DISSOLUTION_INDEXED_EFFECTIVE_PERMEABILITY",
        )

    def test_all_ranked_candidate_categories_are_assessed(self) -> None:
        candidates = self.decision["ranked_candidates"]
        self.assertEqual([item["rank"] for item in candidates], list(range(1, 11)))
        required = {
            "residual_addressed",
            "evidence_availability",
            "identifiability",
            "rights_data_availability",
            "numerical_conservation_risk",
            "verification_route",
            "validation_opportunity",
            "engineering_value",
            "computational_cost",
            "claim_ceiling_effect",
            "disposition",
        }
        for candidate in candidates:
            self.assertTrue(required.issubset(candidate))
        self.assertEqual(candidates[1]["disposition"], "RUNNER_UP")
        self.assertIn("Machine/headspace", candidates[1]["candidate"])

    def test_effective_permeability_scope_and_claim_ceiling(self) -> None:
        allowed = " ".join(self.decision["selected_scope"]["allowed"])
        deferred = " ".join(self.decision["deferred_scope"])
        self.assertIn("effective-permeability", allowed)
        self.assertIn("mesh motion", deferred)
        self.assertIn("pore-volume storage", deferred)
        self.assertIn("solid displacement", deferred)
        self.assertIn("softly circular", self.decision["selected_scope"]["soft_circularity"])
        self.assertFalse(
            self.decision["validation_entry_contract"]["independent_validation_claim"]
        )
        self.assertIn("generic fitted K(t)", self.decision["deferred_scope"])

    def test_future_issue_and_entry_contract_are_frozen(self) -> None:
        issue = self.decision["implementation_issue"]
        self.assertEqual(issue["number"], 18)
        self.assertEqual(
            issue["url"],
            "https://github.com/trbrewer/espresso-whole-pull/issues/18",
        )
        self.assertEqual(issue["change_declaration"], "GOVERNING_PHYSICS_CHANGE")
        required = self.decision["verification_entry_contract"]["required"]
        self.assertTrue(required)
        self.assertTrue(
            self.decision["validation_entry_contract"][
                "non_9_bar_same_campaign_comparison_frozen_before_execution"
            ]
        )

    def test_strategy_and_authorization_boundary(self) -> None:
        strategy = (
            ROOT / "docs/strategy/WHOLE_PULL_MODELING_AND_SIMULATION_STRATEGY.md"
        ).read_text(encoding="utf-8")
        self.assertIn("**Strategy version:** 1.5", strategy)
        current_header = strategy.split("---", 1)[0]
        current_sequence = strategy.split(
            "The immediate program sequence is:", 1
        )[1].split("The model program continues", 1)[0]
        self.assertIn(
            "fc61c4670ec7bf801e40bb391aab16048b8da26b",
            current_header,
        )
        self.assertIn(
            "1d553e44ee2f7480a5df521560801b478618cc84",
            current_header,
        )
        self.assertNotIn(
            "alignment must be refreshed before integration",
            current_header,
        )
        self.assertIn("issue #18", current_sequence)
        self.assertNotIn("construct a source-and-quantity dossier", current_sequence)
        self.assertNotIn("implement the Waszkiewicz-linked", current_sequence)
        self.assertIn("historical", strategy.lower())
        boundary = self.decision["authorization_boundaries"]
        self.assertFalse(boundary["governing_physics_change"])
        self.assertFalse(boundary["scientific_configuration_change"])
        self.assertTrue(boundary["future_physics_change_selected"])
        self.assertFalse(boundary["future_physics_change_implemented"])

    def test_strategy_correction_does_not_change_decision_artifacts(self) -> None:
        import hashlib

        self.assertEqual(
            hashlib.sha256(self.markdown_path.read_bytes()).hexdigest(),
            "bfe57b2475733550ac46e62eb426559732a87a2d3a9a24fd272a17cbd963ac48",
        )
        self.assertEqual(
            hashlib.sha256(self.json_path.read_bytes()).hexdigest(),
            "4a2a4931a6d5f3f0417e33b6db9554073c0dd2d849c66b1040c276c0cccae790",
        )

    def test_decision_documentation_exclusion_is_exact_path_only(self) -> None:
        self.assertTrue(
            excluded(
                Path("docs/decisions/WP01R_006_FIRST_WP02_PHYSICS_SELECTION.md")
            )
        )
        self.assertFalse(
            excluded(Path("docs/decisions/arbitrary-decision.md"))
        )


class PublicSourceManifestPortabilityTests(unittest.TestCase):
    def copy_repository(self, destination: Path) -> None:
        shutil.copytree(
            ROOT,
            destination,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "preflight"),
        )

    def verify(self, root: Path) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [
                sys.executable,
                str(root / "scripts/verify_source_manifest.py"),
                "--root",
                str(root),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=environment,
        )

    def test_regular_file_group_write_bits_do_not_change_git_mode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            self.copy_repository(root)
            readme = root / "README.md"
            readme.chmod(0o644)
            first = self.verify(root)
            self.assertEqual(first.returncode, 0, first.stdout)
            readme.chmod(0o664)
            second = self.verify(root)
            self.assertEqual(second.returncode, 0, second.stdout)

    def test_shared_and_terminal_verifiers_are_identical(self) -> None:
        manifest = json.loads(
            (ROOT / "SOURCE_PACKAGE_MANIFEST.json").read_text(encoding="utf-8")
        )
        shared = verify_shared_source_manifest(ROOT, manifest)
        terminal = verify_freeze_source_manifest(ROOT, manifest)
        for key in (
            "status",
            "checked_file_count",
            "observed_source_file_count",
            "observed_aggregate_source_sha256",
            "failures",
        ):
            self.assertEqual(shared[key], terminal[key])

    def test_executable_group_write_bits_do_not_change_git_mode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            self.copy_repository(root)
            script = root / "Allrun"
            script.chmod(0o755)
            first = self.verify(root)
            self.assertEqual(first.returncode, 0, first.stdout)
            script.chmod(0o775)
            second = self.verify(root)
            self.assertEqual(second.returncode, 0, second.stdout)

    def test_actual_executable_bit_change_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            self.copy_repository(root)
            (root / "README.md").chmod(0o755)
            result = self.verify(root)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("metadata_mismatch", result.stdout)

    def test_content_change_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            self.copy_repository(root)
            with (root / "README.md").open("a", encoding="utf-8") as stream:
                stream.write("\nchanged\n")
            result = self.verify(root)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("metadata_mismatch", result.stdout)

    def test_missing_manifest_path_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            self.copy_repository(root)
            (root / "README.md").unlink()
            result = self.verify(root)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("manifested_source_file_missing", result.stdout)

    def test_additional_source_path_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            self.copy_repository(root)
            (root / "UNEXPECTED_SOURCE_FILE.txt").write_text(
                "unexpected\n", encoding="utf-8"
            )
            result = self.verify(root)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("unmanifested_source_file", result.stdout)


if __name__ == "__main__":
    unittest.main()
