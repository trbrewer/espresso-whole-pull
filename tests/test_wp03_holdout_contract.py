from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WP03HoldoutContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.alignment = json.loads(
            (
                ROOT
                / "validation/evidence/WP_0_3A_PUCKWORKS_ALIGNMENT_REVIEW.json"
            ).read_text()
        )
        cls.matrix = json.loads(
            (
                ROOT
                / "validation/evidence/WP_0_3A_HOLDOUT_CANDIDATE_MATRIX.json"
            ).read_text()
        )
        cls.contract = json.loads(
            (
                ROOT
                / "validation/contracts/WP_0_3A_INDEPENDENT_HOLDOUT_AND_MECHANISM_DISCRIMINATION_CONTRACT.json"
            ).read_text()
        )
        cls.impact = json.loads(
            (
                ROOT
                / "validation/integration/WP_0_3A_PUCKWORKS_SOLVER_SUPPORT_IMPACT_MATRIX.json"
            ).read_text()
        )
        cls.verification_spec = json.loads(
            (
                ROOT
                / "validation/contracts/WP_0_3A_NONPROTECTED_VERIFICATION_PACKAGE_SPEC.json"
            ).read_text()
        )
        cls.vaca_spec = json.loads(
            (
                ROOT
                / "validation/contracts/WP_0_3A_VACA_GUERRA_OFFLINE_INITIALIZER_SPEC.json"
            ).read_text()
        )

    def test_alignment_records_exact_current_and_adopted_identities(self) -> None:
        self.assertEqual(
            self.alignment["moving_upstream_snapshot"]["commit"],
            "bafafef3bc3c77599af8551d4e582aedb9b23f08",
        )
        self.assertEqual(
            self.alignment["moving_upstream_snapshot"]["tree"],
            "64ccf86aff4c90d1c513f1614b39e0823f64d6d7",
        )
        self.assertEqual(
            self.alignment["adopted_historical_baseline"]["commit"],
            "fc61c4670ec7bf801e40bb391aab16048b8da26b",
        )
        self.assertEqual(self.alignment["decision"]["disposition"], "NO_ADOPTION")
        self.assertFalse(
            self.alignment["review_method"]["new_puckworks_code_executed"]
        )

    def test_moving_upstream_added_no_model_or_dataset(self) -> None:
        delta = self.alignment["delta_inventory"]
        self.assertEqual(delta["dataset_paths"], 0)
        self.assertEqual(delta["model_implementation_paths"], 0)
        self.assertTrue(
            self.alignment["locked_waszkiewicz_identity_check"][
                "unchanged_on_moving_upstream"
            ]
        )

    def test_every_candidate_carries_required_evidence_dimensions(self) -> None:
        required = {
            "source_and_persistent_identifier",
            "rights_and_redistribution",
            "coffee",
            "grinder",
            "machine",
            "basket_geometry_and_area",
            "dose",
            "preparation",
            "pressure_control_and_history",
            "flow_or_mass_history",
            "timing_origin_and_first_drip",
            "sampling_cadence",
            "measurement_uncertainty",
            "temperature",
            "endpoint_yield",
            "tds_or_species",
            "data_status",
            "wp02_selection_or_parameter_use",
            "blinding",
            "testable_claim",
            "classifications",
            "qualification",
        }
        self.assertGreaterEqual(len(self.matrix["candidates"]), 10)
        for candidate in self.matrix["candidates"]:
            self.assertFalse(required - candidate.keys(), candidate["candidate_id"])

    def test_no_hydraulic_candidate_is_forced_to_qualify(self) -> None:
        decision = self.matrix["decision"]
        self.assertEqual(
            decision["disposition"],
            "NO_QUALIFYING_INDEPENDENT_HYDRAULIC_HOLDOUT_AVAILABLE",
        )
        self.assertEqual(
            decision["qualifying_independent_hydraulic_holdout_count"], 0
        )
        self.assertFalse(decision["execution_authorized"])
        self.assertEqual(decision["physical_validation"], "NOT_ESTABLISHED")

    def test_endpoint_and_chemistry_evidence_cannot_validate_hydraulics(self) -> None:
        requirement = self.contract["minimum_hydraulic_holdout_requirements"]
        self.assertFalse(
            requirement["endpoint_or_extraction_only_evidence_validates_wp02_hydraulics"]
        )
        self.assertFalse(requirement["unknown_essential_quantities_may_be_fitted"])

    def test_only_frozen_branches_are_in_scope(self) -> None:
        branches = self.contract["frozen_existing_branches"]
        self.assertEqual(set(branches), {"r0", "constant_r1", "wp02_v0_2_0"})
        self.assertEqual(
            branches["constant_r1"]["configuration_sha256"],
            "be275c0302f30dc4dcab120469b0bc62d444e401a80e082a337d9225c659b876",
        )
        self.assertEqual(
            branches["wp02_v0_2_0"]["closure_contract_sha256"],
            "2c898dd91e558ce62006dc81de9cff20bb633b52a89f6fa5a44c5edcda50d57a",
        )
        self.assertFalse(branches["wp02_v0_2_0"]["parameter_fitting_allowed"])

    def test_contract_freezes_access_and_invocation_limits(self) -> None:
        access = self.contract["future_blinded_access_plan"]
        self.assertEqual(access["maximum_score_bearing_analyzer_invocations"], 1)
        self.assertEqual(access["maximum_solver_invocations_per_frozen_branch"], 1)
        self.assertFalse(access["result_dependent_reruns_allowed"])
        boundary = self.contract["authorization_boundary"]
        self.assertFalse(boundary["holdout_execution_authorized"])
        self.assertFalse(boundary["new_mechanism_authorized"])
        self.assertFalse(boundary["protected_source_access_authorized"])

    def test_thresholds_require_measurement_uncertainty(self) -> None:
        evaluation = self.contract["predeclared_evaluation_template"]
        self.assertIsNone(evaluation["current_numeric_thresholds"])
        self.assertIn("measurement uncertainty", evaluation["threshold_rule"])
        self.assertIn(
            "No qualifying dataset", evaluation["numeric_thresholds_absent_reason"]
        )

    def test_mechanism_matrix_is_hypothesis_only(self) -> None:
        mechanisms = {
            item["later_hypothesis"]
            for item in self.contract["mechanism_discrimination"]
        }
        self.assertIn("machine or headspace coupling", mechanisms)
        self.assertIn("explicit compaction or swelling", mechanisms)
        self.assertIn("bounded heterogeneity", mechanisms)
        self.assertTrue(
            self.contract["authorization_boundary"][
                "future_mechanism_decision_requires_separate_task"
            ]
        )

    def test_claim_state_remains_bounded(self) -> None:
        claims = self.contract["claim_state"]
        self.assertEqual(
            claims["wp02_result"], "SOURCE_LINKED_MULTIPRESSURE_RECONSTRUCTION_PASS"
        )
        self.assertEqual(
            claims["release"],
            "SOFTWARE_AND_SOURCE_LINKED_RECONSTRUCTION_RELEASE_PASS",
        )
        self.assertEqual(claims["physical_validation"], "NOT_ESTABLISHED")

    def test_only_exact_new_document_paths_are_manifest_excluded(self) -> None:
        import sys

        sys.path.insert(0, str(ROOT / "scripts"))
        from generate_source_manifest import excluded

        self.assertTrue(
            excluded(Path("docs/evidence/WP_0_3A_ALIGNMENT_AND_HOLDOUT_REVIEW.md"))
        )
        self.assertTrue(
            excluded(
                Path("docs/validation/WP_0_3A_FUTURE_HOLDOUT_EXECUTION_BRIEF.md")
            )
        )
        self.assertFalse(excluded(Path("docs/evidence/arbitrary_future_file.md")))
        self.assertFalse(excluded(Path("docs/validation/arbitrary_future_file.md")))

    def test_frozen_scientific_hashes_remain_exact(self) -> None:
        import hashlib

        expected = {
            "validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json": "75a79e9972176668a8bfdb574ea16cbf39373a9ea11078009bc7b997c2f76859",
            "validation/wp02/WP02_001_CLOSURE_CONTRACT.json": "2c898dd91e558ce62006dc81de9cff20bb633b52a89f6fa5a44c5edcda50d57a",
            "config/reference_R0.json": "67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286",
            "config/reconstruction_R1_waszkiewicz_9bar.json": "be275c0302f30dc4dcab120469b0bc62d444e401a80e082a337d9225c659b876",
            "config/reconstruction_WP02A_waszkiewicz_9bar.json": "81a9089061d762aaf785a7764cebb8e0947e4f3c14bb833d58a204d2c816407e",
            "config/reconstruction_WP02A_waszkiewicz_8bar.json": "ac87cfdff2862401b33ac01fa31d87bf966e062cecd153ce59ab4a9518feb57e",
        }
        for relative, digest in expected.items():
            self.assertEqual(
                hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest
            )

    def test_every_solver_support_artifact_has_one_allowed_disposition(self) -> None:
        allowed = set(self.impact["allowed_dispositions"])
        required_ids = {
            "moroney2017",
            "liang2021",
            "liang2021_audit",
            "schmieder2023",
            "schmieder2023_audit",
            "vacaguerra2023a",
            "matias2023",
            "maille2024",
            "perticarini2024",
            "ellero2019_jfe",
            "kusumaatmaja2010",
            "foster_evidence_selection_correction",
            "paper_b2_late_window_access_correction",
            "tds_and_ey_normalization_hazards",
        }
        observed_ids = {item["artifact_id"] for item in self.impact["artifacts"]}
        self.assertEqual(observed_ids, required_ids)
        for artifact in self.impact["artifacts"]:
            self.assertIn(artifact["disposition"], allowed)
            self.assertIsInstance(artifact["disposition"], str)

    def test_mandatory_pressure_and_access_corrections_are_exact(self) -> None:
        corrections = self.impact["mandatory_corrections"]
        self.assertEqual(
            corrections["schmieder_retired_pressure_triple_bar"], [9.3, 7.4, 3.8]
        )
        self.assertEqual(
            corrections["schmieder_retired_role"],
            "NOT_A_DARCY_PRESSURE_FLOW_DATUM",
        )
        self.assertEqual(
            corrections["schmieder_table2_condition_mean_pressure_range_bar"],
            [2.58, 8.433333333333334],
        )
        self.assertEqual(
            corrections["paper_b2_late_window"]["access_class"],
            "DIRECT_TARGET_IN_SAMPLE_SUBSET_FIT",
        )
        self.assertEqual(
            corrections["foster_flow_curve"],
            "NEGATIVE_DIRECT_EVIDENCE_EXPLORATORY_CAPACITY_ONLY",
        )

    def test_selected_evidence_does_not_advance_lock(self) -> None:
        self.assertEqual(
            self.impact["final_disposition"],
            "ADOPT_SELECTED_EVIDENCE_WITH_FOLLOWUP",
        )
        recommendation = self.impact["lock_recommendation"]
        self.assertFalse(recommendation["advance_lock_now"])
        self.assertEqual(
            recommendation["recommendation"],
            "RETAIN_EXISTING_LOCK_PENDING_ACQUISITION",
        )
        self.assertIn(
            "scripts/verify_release_finalization.py",
            self.impact["allowed_repository_changed_paths"],
        )

    def test_nonprotected_package_is_specification_only(self) -> None:
        self.assertEqual(
            self.verification_spec["package_status"],
            "SPECIFIED_NOT_IMPLEMENTED_NOT_EXECUTED",
        )
        self.assertFalse(self.verification_spec["runtime_wp02_connection_allowed"])
        self.assertFalse(self.verification_spec["protected_data_required"])
        self.assertEqual(
            set(self.verification_spec["components"]),
            {
                "moroney2017_zero_flow",
                "matias2023_analytic_limits",
                "liang2021_planning",
                "observables",
            },
        )

    def test_observables_cannot_silently_merge_tds_or_ey_conventions(self) -> None:
        observables = self.verification_spec["components"]["observables"]
        self.assertFalse(
            observables["tds_measurement_schema"]["silent_method_conversion_allowed"]
        )
        self.assertFalse(
            observables["ey_convention"]["silent_convention_merge_allowed"]
        )
        required = observables["tds_measurement_schema"]["required_fields"]
        for field in (
            "method_id",
            "instrument_model",
            "calibrant_material",
            "sample_temperature_C",
            "measurement_uncertainty",
        ):
            self.assertIn(field, required)

    def test_vaca_prior_is_inactive_bounded_and_distinct_from_wp02(self) -> None:
        self.assertEqual(
            self.vaca_spec["status"], "SPECIFIED_INACTIVE_NOT_IMPLEMENTED"
        )
        self.assertEqual(
            self.vaca_spec["corrected_surface"]["beta_signs"]["dry_porosity_omega"],
            "NEGATIVE_X3_BETA",
        )
        self.assertTrue(
            self.vaca_spec["permeability_variants"]["viscosity_renormalized"][
                "must_not_overwrite_published_variant"
            ]
        )
        prohibitions = self.vaca_spec["prohibitions"]
        self.assertIn("do not replace or alter WP02 calibrated permeability", prohibitions)
        self.assertIn("do not treat dry porosity as wet dynamic porosity", prohibitions)
        self.assertEqual(
            self.vaca_spec["source_domain"]["extrapolation_default"], "REJECT"
        )

    def test_new_triage_document_alone_is_manifest_excluded(self) -> None:
        import sys

        sys.path.insert(0, str(ROOT / "scripts"))
        from generate_source_manifest import excluded

        self.assertTrue(
            excluded(
                Path(
                    "docs/integration/PUCKWORKS_WP_0_3A_SOLVER_SUPPORT_TRIAGE.md"
                )
            )
        )
        self.assertFalse(
            excluded(Path("docs/integration/arbitrary_solver_support_triage.md"))
        )


if __name__ == "__main__":
    unittest.main()
