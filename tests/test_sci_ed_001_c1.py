import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sci_ed_001_c1",ROOT/"scripts/sci_ed_001.py")
MOD=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=MOD;SPEC.loader.exec_module(MOD)
VERIFY_SPEC=importlib.util.spec_from_file_location("sci_ed_001_verify",ROOT/"scripts/sci_ed_001_verify_no_governing_physics_change.py")
VERIFY=importlib.util.module_from_spec(VERIFY_SPEC);sys.modules[VERIFY_SPEC.name]=VERIFY;VERIFY_SPEC.loader.exec_module(VERIFY)
OUT=ROOT/"validation/cases/sci_ed_001"

class SciEd001C1Tests(unittest.TestCase):
    def test_phase_i_prefix_authority_is_complete(self):
        r=json.loads((OUT/"CAUSAL_ATTRIBUTION_REVIEW_C1.json").read_text())
        self.assertEqual(r["prefix_audit"]["groups_expected"],292)
        self.assertEqual(r["prefix_audit"]["groups_completed"],292)
        self.assertEqual(r["prefix_audit"]["groups_different"],0)
        self.assertEqual(r["attempt_004"]["completed_rows"],2628)
        self.assertEqual(r["attempt_004"]["base_refined_pairs"],1314)

    def test_pre_event_support_is_nonranking(self):
        x=MOD.c1_eligibility("pre_event_flow_m3_s","P0_CONST_5BAR")
        self.assertEqual((x["feature_support_start_s"],x["feature_support_end_s"]),(-2.0,0.0))
        self.assertFalse(x["uses_post_design_data"]);self.assertFalse(x["ranking_eligible"])

    def test_exact_zero_points_are_general_common_prefix_rule(self):
        for feature in ("normalized_flow_at_0s","normalized_resistance_at_0s","flow_at_0s_m3_s"):
            x=MOD.c1_eligibility(feature,"P8_SLOW_RAMP_5_TO_9")
            self.assertEqual(x["causal_role"],"COMMON_PREFIX_DIAGNOSTIC")
            self.assertEqual(x["feature_support_end_s"],0.0);self.assertFalse(x["ranking_eligible"])

    def test_positive_point_has_post_support_but_ambiguous_mapping(self):
        x=MOD.c1_eligibility("normalized_flow_at_10s","P8_SLOW_RAMP_5_TO_9")
        self.assertTrue(x["uses_post_design_data"]);self.assertEqual(x["feature_support_end_s"],10.0)
        self.assertFalse(x["ranking_eligible"]);self.assertEqual(x["ranking_exclusion_reason"],"AMBIGUOUS_PROSPECTIVE_MAPPING")

    def test_terminal_normalized_features_remain_potentially_eligible(self):
        for feature in ("terminal_normalized_flow","terminal_normalized_resistance"):
            x=MOD.c1_eligibility(feature,"P0_CONST_5BAR")
            self.assertTrue(x["uses_post_design_data"]);self.assertTrue(x["ranking_eligible"])

    def test_pulse_support_is_post_design_but_mapping_ambiguous(self):
        x=MOD.c1_eligibility("pulse_integrated_flow_m3","P5_PULSE_9_11_9")
        self.assertEqual((x["feature_support_start_s"],x["feature_support_end_s"]),(20.0,27.0))
        self.assertTrue(x["uses_post_design_data"]);self.assertFalse(x["ranking_eligible"])

    def test_no_feature_specific_zero_patch(self):
        source=(ROOT/"scripts/sci_ed_001.py").read_text()
        self.assertNotIn('if feature=="normalized_flow_at_0s"',source)
        self.assertNotIn("if feature == 'normalized_flow_at_0s'",source)

    def test_c1_authority_is_exact(self):
        self.assertEqual(MOD.C1_SOURCE_HEAD,"5217b4b8b9984e01a849b82bda6d61b60ff07a2c")
        self.assertEqual(MOD.C1_SOURCE_AGGREGATE,"9a0bcea35850d8ea94db16e0aa9a6af15fc7f2ee8b0f2bae6be6b5a4cdd5336e")

    def test_support_metadata_is_deterministic(self):
        a=MOD.c1_eligibility("terminal_normalized_flow","P1_CONST_9BAR")
        b=MOD.c1_eligibility("terminal_normalized_flow","P1_CONST_9BAR")
        self.assertEqual(MOD.canonical(a),MOD.canonical(b))

    def test_required_preconditioning_diagnostic_is_emitted(self):
        source=(ROOT/"scripts/sci_ed_001.py").read_text()
        self.assertIn('PRECONDITIONING_DIAGNOSTICS_C1.json',source)
        self.assertIn('groups_expected":292',source)

    def test_no_new_program_or_feature_contract(self):
        protocol=json.loads((OUT/"SCI_ED_001_C1_CORRECTION_PROTOCOL.json").read_text())
        self.assertIn("NEW_FEATURE",protocol["forbidden_changes"])
        self.assertIn("NEW_PROGRAM",protocol["forbidden_changes"])
        self.assertTrue(protocol["no_corrected_ranking_before_commit_e"])

    def test_verifier_strict_default_is_preserved(self):
        r=VERIFY.classify_changed_paths(sorted(VERIFY.AUTHORIZED_SHARED_METADATA),None)
        self.assertFalse(r["strict_all_changed_paths_owned"])
        self.assertFalse(r["effective_path_contract_pass"])

    def test_verifier_exact_owner_authorization_succeeds(self):
        r=VERIFY.classify_changed_paths(sorted(VERIFY.AUTHORIZED_SHARED_METADATA),VERIFY.OWNER_AUTHORIZATION)
        self.assertTrue(r["owner_authorization_exact"])
        self.assertTrue(r["authorized_shared_metadata_set_exact"])
        self.assertTrue(r["owner_authorized_shared_metadata_mode"])
        self.assertTrue(r["effective_path_contract_pass"])
        self.assertEqual(r["unauthorized_changed_paths"],[])
        self.assertEqual(r["integration_classification"],VERIFY.AUTHORIZED_CLASSIFICATION)

    def test_verifier_missing_authorization_fails(self):
        r=VERIFY.classify_changed_paths(sorted(VERIFY.AUTHORIZED_SHARED_METADATA),None)
        self.assertFalse(r["owner_authorization_supplied"]);self.assertFalse(r["effective_path_contract_pass"])

    def test_verifier_incorrect_authorizations_fail(self):
        token=VERIFY.OWNER_AUTHORIZATION
        for value in ("", "wrong", token[:-1], token+"X"):
            with self.subTest(value=value):
                r=VERIFY.classify_changed_paths(sorted(VERIFY.AUTHORIZED_SHARED_METADATA),value)
                self.assertFalse(r["owner_authorization_exact"]);self.assertFalse(r["effective_path_contract_pass"])

    def test_verifier_partial_shared_set_fails(self):
        for count in (1,2):
            r=VERIFY.classify_changed_paths(sorted(VERIFY.AUTHORIZED_SHARED_METADATA)[:count],VERIFY.OWNER_AUTHORIZATION)
            self.assertFalse(r["authorized_shared_metadata_set_exact"]);self.assertFalse(r["effective_path_contract_pass"])

    def test_verifier_fourth_path_fails(self):
        paths=sorted(VERIFY.AUTHORIZED_SHARED_METADATA)+["README.md"]
        r=VERIFY.classify_changed_paths(paths,VERIFY.OWNER_AUTHORIZATION)
        self.assertEqual(r["unauthorized_changed_paths"],["README.md"]);self.assertFalse(r["effective_path_contract_pass"])

    def test_verifier_sci_lc_task_path_fails(self):
        paths=sorted(VERIFY.AUTHORIZED_SHARED_METADATA)+["docs/analysis/sci_lc_001a/PROTOCOL.md"]
        r=VERIFY.classify_changed_paths(paths,VERIFY.OWNER_AUTHORIZATION)
        self.assertIn("docs/analysis/sci_lc_001a/PROTOCOL.md",r["unauthorized_changed_paths"])
        self.assertFalse(r["effective_path_contract_pass"])

    def test_verifier_protected_physics_path_fails(self):
        paths=sorted(VERIFY.AUTHORIZED_SHARED_METADATA)+["solver/espressoWholePullFoam/espressoWholePullFoam.C"]
        r=VERIFY.classify_changed_paths(paths,VERIFY.OWNER_AUTHORIZATION)
        self.assertIn("solver/espressoWholePullFoam/espressoWholePullFoam.C",r["unauthorized_changed_paths"])
        self.assertFalse(r["effective_path_contract_pass"])

    def test_verifier_reports_strict_and_effective_truthfully(self):
        r=VERIFY.classify_changed_paths(sorted(VERIFY.AUTHORIZED_SHARED_METADATA),VERIFY.OWNER_AUTHORIZATION)
        self.assertFalse(r["strict_all_changed_paths_owned"]);self.assertTrue(r["effective_path_contract_pass"])

    def test_verifier_path_output_is_deterministic(self):
        paths=["docs/PROJECT_STATE.md","scripts/sci_ed_001.py","SOURCE_PACKAGE_MANIFEST.json","PACKAGE_QA_STATUS.json"]
        a=VERIFY.classify_changed_paths(paths,VERIFY.OWNER_AUTHORIZATION)
        b=VERIFY.classify_changed_paths(list(reversed(paths)),VERIFY.OWNER_AUTHORIZATION)
        self.assertEqual(VERIFY.canonical(a),VERIFY.canonical(b))
        for key in ("task_owned_changed_paths","non_task_owned_changed_paths","authorized_shared_metadata_changed_paths","unauthorized_changed_paths"):
            self.assertEqual(a[key],sorted(a[key]))

if __name__=="__main__":unittest.main()
