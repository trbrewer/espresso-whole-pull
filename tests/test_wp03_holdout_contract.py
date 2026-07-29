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


if __name__ == "__main__":
    unittest.main()
