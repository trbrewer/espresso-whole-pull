import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/campaign/wp03c"))
import stage0  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "wp03c_verifier", ROOT / "scripts/verify_wp03c_stage0_scaffold.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class Stage0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((ROOT / "validation/contracts/WP_0_3C_STAGE0_AUTHORITY_AND_INPUT_INTAKE_CONTRACT.json").read_text())
        cls.registry = json.loads((ROOT / "validation/campaign/wp03c/WP_0_3C_INPUT_REQUIREMENTS.json").read_text())
        cls.templates = {p.name: json.loads(p.read_text()) for p in sorted(
            (ROOT / "validation/campaign/wp03c/templates").glob("*.json"))}
        cls.governing = stage0.wp03a_governing_requirements(ROOT)

    def evaluate(self, contract=None, registry=None, templates=None, paths=None,
                 frozen=None, text="", governing=None, regenerated=True):
        return verifier.evaluate(
            contract or self.contract, registry or self.registry,
            templates or self.templates,
            paths if paths is not None else frozenset(),
            frozen if frozen is not None else verifier.FROZEN, text,
            regenerated, governing or self.governing)

    def resolved_package(self):
        package = stage0.input_package()
        for record in package.values():
            record["status"] = "RESOLVED_HUMAN_INPUT"
            if record["input_classification"] in stage0.PRIVATE_CLASSIFICATIONS:
                record["resolution_binding"] = {
                    "binding_type": "PRIVATE_PACKAGE_DIGEST_AND_CUSTODY",
                    "private_package_sha256": "a" * 64,
                    "custody_record_id": "SYNTHETIC_CUSTODY",
                    "custodian_role_id": "ROLE_DATA_CUSTODIAN",
                }
            else:
                record["resolution_binding"] = {
                    "binding_type": "PUBLIC_VALUE_AND_EVIDENCE",
                    "value": "SYNTHETIC_TEST_VALUE",
                    "evidence_sha256": "b" * 64,
                    "evidence_role_id": "ROLE_PROTOCOL_OWNER",
                }
        return package

    def test_unresolved_inputs_accepted_and_block_readiness(self):
        self.assertEqual(stage0.evaluate_readiness(
            stage0.input_package(), authority_established=True),
            stage0.DISPOSITION)
        self.assertTrue(all(self.evaluate().values()))

    def test_partial_readiness(self):
        package = stage0.input_package()
        resolved = self.resolved_package()
        first_id = next(iter(package))
        package[first_id] = resolved[first_id]
        self.assertEqual(stage0.evaluate_readiness(
            package, authority_established=True), stage0.PARTIAL)

    def test_authority_absent(self):
        self.assertEqual(stage0.evaluate_readiness(
            stage0.input_package(), authority_established=False),
                         "AUTHORITY_NOT_ESTABLISHED")
        self.assertEqual(stage0.evaluate_readiness(
            stage0.input_package(), authority_established=1),
            "AUTHORITY_NOT_ESTABLISHED")

    def test_empty_mapping_and_one_verified_requirement_fail_closed(self):
        with self.assertRaises(ValueError):
            stage0.evaluate_readiness({}, authority_established=True)
        one = self.resolved_package()
        one = {next(iter(one)): next(iter(one.values()))}
        with self.assertRaises(ValueError):
            stage0.evaluate_readiness(one, authority_established=True)

    def test_unknown_status_and_incomplete_verified_subset_rejected(self):
        package = stage0.input_package()
        package[next(iter(package))]["status"] = "VERIFIED"
        with self.assertRaises(ValueError):
            stage0.evaluate_readiness(package, authority_established=True)
        records = list(self.resolved_package().values())[:-1]
        with self.assertRaises(ValueError):
            stage0.validate_input_records(records)

    def test_missing_additional_and_duplicate_requirement_rejected(self):
        records = list(stage0.input_package().values())
        with self.assertRaises(ValueError):
            stage0.validate_input_records(records[:-1])
        extra = copy.deepcopy(records[0])
        extra["requirement_id"] = "ADDITIONAL_REQUIREMENT"
        with self.assertRaises(ValueError):
            stage0.validate_input_records(records + [extra])
        with self.assertRaises(ValueError):
            stage0.validate_input_records(records + [copy.deepcopy(records[0])])

    def test_requirement_metadata_mismatch_rejected(self):
        for key in ("category", "input_classification", "responsible_role_id",
                    "deadline"):
            records = list(stage0.input_package().values())
            records[0][key] = "WRONG"
            with self.assertRaises(ValueError):
                stage0.validate_input_records(records)

    def test_status_only_resolved_unknown_keys_and_bad_bindings_rejected(self):
        records = list(stage0.input_package().values())
        records[0]["status"] = "RESOLVED_HUMAN_INPUT"
        with self.assertRaises(ValueError):
            stage0.validate_input_records(records)
        for mutation in ("unknown_key", "bad_binding"):
            records = list(self.resolved_package().values())
            if mutation == "unknown_key":
                records[0]["unexpected"] = True
            else:
                records[0]["resolution_binding"] = {"binding_type": "BAD"}
            with self.assertRaises(ValueError):
                stage0.validate_input_records(records)

    def test_complete_inputs_stop_awaiting_governed_review(self):
        self.assertEqual(stage0.evaluate_readiness(
            self.resolved_package(),
            authority_established=True), stage0.COMPLETE)
        self.assertNotEqual(stage0.COMPLETE, "READY_FOR_CALIBRATION_PLANNING")

    def test_unaccountable_unresolved_value_rejected(self):
        templates = copy.deepcopy(self.templates)
        first_template = next(iter(templates.values()))
        first = next(iter(next(iter(first_template["fields"].values())).values()))
        first.pop("responsible_role_id")
        self.assertFalse(self.evaluate(templates=templates)["unresolved_values_accountable"])

    def test_invented_human_or_observed_sensor_rejected(self):
        for template_name in (
                "WP_0_3C_ROLE_ASSIGNMENT_TEMPLATE.json",
                "WP_0_3C_SENSOR_INVENTORY_TEMPLATE.json"):
            templates = copy.deepcopy(self.templates)
            template = templates[template_name]
            value = next(iter(next(iter(template["fields"].values())).values()))
            value["status"] = "RESOLVED_HUMAN_INPUT"
            value["value"] = "invented"
            checks = self.evaluate(templates=templates)
            self.assertFalse(checks["unresolved_values_accountable"])
            self.assertFalse(checks["template_structure_exact"])

    def test_template_registry_disagreement_rejected(self):
        templates = copy.deepcopy(self.templates)
        template = templates["WP_0_3C_ROLE_ASSIGNMENT_TEMPLATE.json"]
        fields = template["fields"]["governance_and_roles"]
        fields["renamed_field"] = fields.pop(next(iter(fields)))
        self.assertFalse(self.evaluate(templates=templates)["template_structure_exact"])

    def test_wp03a_campaign_floors_blinding_and_no_fit_are_frozen(self):
        cases = [
            ("minimum_pressure_groups", 3),
            ("minimum_independent_shots_per_group", 6),
            ("preregistered_and_blinded", False),
            ("no_holdout_parameter_fitting", False),
        ]
        for key, value in cases:
            governing = copy.deepcopy(self.governing)
            governing[key] = value
            self.assertFalse(self.evaluate(
                governing=governing)["wp03a_governing_requirements_exact"])

    def test_wp03a_geometry_rules_are_frozen(self):
        for key in ("bed_area_rule", "open_area_rule"):
            governing = copy.deepcopy(self.governing)
            governing[key] = "MUTATED"
            self.assertFalse(self.evaluate(
                governing=governing)["wp03a_governing_requirements_exact"])
        entries = {item["field"]: item for item in stage0.requirement_entries()}
        self.assertEqual(
            entries["bed_area_calculation"]["governing_rule_binding"],
            "frozen_governing_requirements.bed_area_rule")
        self.assertEqual(
            entries["hole_open_area_metadata"]["governing_rule_binding"],
            "frozen_governing_requirements.open_area_rule")

    def test_contract_is_exact_not_partial(self):
        for key in ("classification", "holdout_scoring",
                    "new_governing_physics", "claim_ceiling",
                    "required_input_categories", "dependencies",
                    "public_private_information_boundary"):
            contract = copy.deepcopy(self.contract)
            contract[key] = "MUTATED"
            self.assertFalse(self.evaluate(
                contract=contract)["contract_identity_exact"])

    def test_common_mode_mutation_hits_independent_identities(self):
        registry = copy.deepcopy(self.registry)
        registry["requirements"][0]["field"] = "common_mode_mutation"
        templates = copy.deepcopy(self.templates)
        fields = templates[
            "WP_0_3C_ROLE_ASSIGNMENT_TEMPLATE.json"]["fields"][
                "governance_and_roles"]
        fields["common_mode_mutation"] = fields.pop("repository_owner")
        checks = self.evaluate(registry=registry, templates=templates)
        self.assertFalse(checks["independent_requirement_metadata_identity"])
        self.assertFalse(checks["independent_template_mapping_identity"])

    def test_extra_registry_and_template_envelope_keys_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry["extra"] = True
        self.assertFalse(self.evaluate(
            registry=registry)["registry_envelope_exact"])
        templates = copy.deepcopy(self.templates)
        next(iter(templates.values()))["extra"] = True
        self.assertFalse(self.evaluate(
            templates=templates)["template_envelopes_exact"])

    def test_readiness_and_registry_boundary_mutations_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry["readiness"]["current_state"] = "READY_FOR_CALIBRATION_PLANNING"
        self.assertFalse(self.evaluate(
            registry=registry)["registry_envelope_exact"])
        registry = copy.deepcopy(self.registry)
        registry["public_private_boundary"]["public_binding"] = "MUTATED"
        self.assertFalse(self.evaluate(
            registry=registry)["registry_envelope_exact"])

    def test_private_vocabulary_and_flags_are_independently_fixed(self):
        original = set(stage0.PRIVATE_CLASSIFICATIONS)
        try:
            stage0.PRIVATE_CLASSIFICATIONS.remove("PRIVATE_PERSONAL_INPUT")
            self.assertFalse(self.evaluate()["privacy_vocabularies_exact"])
        finally:
            stage0.PRIVATE_CLASSIFICATIONS.clear()
            stage0.PRIVATE_CLASSIFICATIONS.update(original)
        templates = copy.deepcopy(self.templates)
        private_value = templates[
            "WP_0_3C_ROLE_ASSIGNMENT_TEMPLATE.json"]["fields"][
                "governance_and_roles"]["repository_owner"]
        private_value["private_value_required"] = False
        private_value["public_repository_value_allowed"] = True
        self.assertFalse(self.evaluate(
            templates=templates)["privacy_semantics_exact"])

    def test_common_mode_template_mutation_hits_complete_identity(self):
        original = stage0.unresolved

        def mutated(*args, **kwargs):
            value = original(*args, **kwargs)
            value["common_mode_marker"] = True
            return value

        templates = copy.deepcopy(self.templates)
        for template in templates.values():
            for category in template["fields"].values():
                for value in category.values():
                    value["common_mode_marker"] = True
        stage0.unresolved = mutated
        try:
            checks = self.evaluate(templates=templates)
            self.assertTrue(checks["independent_requirement_metadata_identity"])
            self.assertTrue(checks["independent_template_mapping_identity"])
            self.assertFalse(checks["complete_templates_identity"])
        finally:
            stage0.unresolved = original

    def test_deterministic_regeneration_required(self):
        self.assertFalse(self.evaluate(
            regenerated=False)["deterministic_regeneration_byte_identical"])

    def test_final_or_experimental_authorization_rejected(self):
        for key, value in (("final_preregistration", "CREATED"),
                           ("commissioning", "AUTHORIZED"),
                           ("holdout_acquisition", "AUTHORIZED")):
            contract = copy.deepcopy(self.contract)
            contract[key] = value
            self.assertFalse(self.evaluate(contract=contract)["claims_bounded"])

    def test_execution_counts_rejected(self):
        for key in ("experimental", "openfoam", "puckworks_code",
                    "protected_access", "holdout_scoring"):
            contract = copy.deepcopy(self.contract)
            contract["execution_counts"][key] = 1
            self.assertFalse(self.evaluate(contract=contract)["execution_prohibited"])

    def test_model_or_score_content_rejected(self):
        for text in ("model_prediction", "model_residual", "shot_score"):
            self.assertFalse(self.evaluate(text=text)["no_forbidden_content"])

    def test_frozen_hash_or_runtime_lock_change_rejected(self):
        frozen = dict(verifier.FROZEN)
        frozen[next(iter(frozen))] = "0" * 64
        self.assertFalse(self.evaluate(frozen=frozen)["frozen_hashes_exact"])
        self.assertEqual(
            self.contract["dependencies"]["runtime_puckworks_commit"],
            "fc61c4670ec7bf801e40bb391aab16048b8da26b")

    def test_secret_private_path_and_overclaim_rejected(self):
        for text in ("api" + "_key=abc", "/" + "home/private/thing",
                     "physical validation is established"):
            checks = self.evaluate(text=text)
            if "physical" in text:
                contract = copy.deepcopy(self.contract)
                contract["physical_validation"] = "ESTABLISHED"
                self.assertFalse(self.evaluate(contract=contract)["claims_bounded"])
            else:
                self.assertFalse(checks["no_forbidden_content"])

    def test_contract_cannot_enlarge_boundary(self):
        contract = copy.deepcopy(self.contract)
        contract["permitted_changed_paths"].append("solver/unauthorized.C")
        self.assertFalse(self.evaluate(
            contract=contract)["original_permitted_path_contract"])


class Stage0FrozenScopeTests(unittest.TestCase):
    def git(self, root, *args, input_text=None):
        return subprocess.run(
            ["git", *args], cwd=root, check=True, text=True,
            input=input_text, stdout=subprocess.PIPE).stdout.strip()

    def clone_at_stage0(self, parent):
        candidate = parent / "candidate"
        subprocess.run(
            ["git", "clone", "-q", "--no-hardlinks", str(ROOT), str(candidate)],
            check=True)
        self.git(candidate, "config", "user.name", "VAL-INFRA synthetic")
        self.git(candidate, "config", "user.email", "val-infra@example.invalid")
        self.git(candidate, "checkout", "-q", "-b", "fixture",
                 verifier.STAGE0_FREEZE_COMMIT)
        return candidate

    def commit_all(self, root, message="synthetic mutation"):
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", message)

    def assert_scope_fails(self, candidate):
        self.assertFalse(verifier.frozen_stage0_scope_integrity(
            candidate, candidate))

    def test_authentic_frozen_stage0_snapshot_passes(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            self.assertTrue(verifier.historical_stage0_ancestor_of_head(candidate))
            self.assertTrue(verifier.frozen_stage0_scope_integrity(
                candidate, candidate))

    def test_current_main_stage0_scope_passes(self):
        self.assertTrue(verifier.historical_stage0_ancestor_of_head(ROOT))
        self.assertTrue(verifier.frozen_stage0_scope_integrity(ROOT))
        self.assertEqual(verifier.verify(ROOT)["status"], "PASS")

    def test_unrelated_future_path_does_not_require_enumeration(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            future = candidate / "future/work/package/not_enumerated.txt"
            future.parent.mkdir(parents=True)
            future.write_text("authorized unrelated future work\n")
            self.assertFalse(hasattr(verifier, "EXPECTED_PATHS"))
            self.assertTrue(verifier.frozen_stage0_scope_integrity(
                candidate, candidate))

    def test_unrelated_symlink_outside_scope_is_not_stage0_input(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            target = candidate / "future-target.txt"
            target.write_text("unrelated\n")
            (candidate / "future-link").symlink_to(target)
            self.assertTrue(verifier.frozen_stage0_scope_integrity(
                candidate, candidate))

    def test_protected_mutation_and_replacement_fail(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            scope = verifier.historical_stage0_scope(candidate)
            path = next(path for path in scope if "templates/" in path)
            (candidate / path).write_text("replacement\n")
            self.assert_scope_fails(candidate)

    def test_protected_deletion_fails(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            scope = verifier.historical_stage0_scope(candidate)
            path = next(path for path in scope if "templates/" in path)
            (candidate / path).unlink()
            self.assert_scope_fails(candidate)

    def test_protected_rename_fails(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            scope = verifier.historical_stage0_scope(candidate)
            path = next(path for path in scope if "templates/" in path)
            source = candidate / path
            source.rename(source.with_name("RENAMED_STAGE0_ARTIFACT.json"))
            self.assert_scope_fails(candidate)

    def test_protected_addition_fails(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            addition = candidate / "validation/campaign/wp03c/UNAUTHORIZED.json"
            addition.write_text("{}\n")
            self.assert_scope_fails(candidate)

    def test_permitted_path_contract_mutation_fails(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            contract_path = candidate / verifier.STAGE0_CONTRACT_PATH
            contract = json.loads(contract_path.read_text())
            contract["permitted_changed_paths"].append("future/unrelated.txt")
            contract_path.write_text(json.dumps(contract, indent=2) + "\n")
            self.assert_scope_fails(candidate)

    def test_each_top_level_regular_file_symlink_replacement_fails(self):
        protected = (
            verifier.STAGE0_CONTRACT_PATH,
            "docs/reports/WP_0_3C_HUMAN_AND_APPARATUS_INPUT_GUIDE.md",
        )
        for relative in protected:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as name:
                candidate = self.clone_at_stage0(Path(name))
                source = candidate / relative
                copy = candidate / "outside-protected-copy"
                copy.write_bytes(source.read_bytes())
                source.unlink()
                source.symlink_to(os.path.relpath(copy, source.parent))
                self.assert_scope_fails(candidate)

    def test_template_file_symlink_to_identical_copy_fails(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            relative = next(
                path for path in verifier.historical_stage0_scope(candidate)
                if "templates/" in path)
            source = candidate / relative
            copy = candidate / "identical-template-copy"
            copy.write_bytes(source.read_bytes())
            source.unlink()
            source.symlink_to(os.path.relpath(copy, source.parent))
            self.assert_scope_fails(candidate)

    def test_protected_directory_symlink_to_identical_tree_fails(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            directory = candidate / "validation/campaign/wp03c/templates"
            copy = candidate / "identical-templates-outside-scope"
            directory.rename(copy)
            directory.symlink_to(os.path.relpath(copy, directory.parent),
                                 target_is_directory=True)
            self.assert_scope_fails(candidate)

    def test_broken_and_directory_symlink_additions_fail(self):
        for target, is_directory in (("missing-target", False),
                                     ("../../../docs", True)):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as name:
                candidate = self.clone_at_stage0(Path(name))
                addition = candidate / "validation/campaign/wp03c/ADDED_LINK"
                addition.symlink_to(target, target_is_directory=is_directory)
                self.assert_scope_fails(candidate)

    def test_identical_bytes_with_executable_git_mode_fails(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            relative = "validation/campaign/wp03c/WP_0_3C_INPUT_REQUIREMENTS.json"
            (candidate / relative).chmod(0o755)
            self.commit_all(candidate, "change protected mode")
            self.assertFalse(verifier.frozen_stage0_git_tree_integrity(
                candidate, candidate))

    def test_blob_replaced_by_gitlink_fails(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            relative = "tools/campaign/wp03c/stage0.py"
            object_id = self.git(candidate, "rev-parse", "HEAD")
            self.git(candidate, "update-index", "--add", "--cacheinfo",
                     "160000," + object_id + "," + relative)
            self.git(candidate, "commit", "-q", "-m", "replace blob by gitlink")
            self.assertFalse(verifier.frozen_stage0_git_tree_integrity(
                candidate, candidate))

    def test_tracked_deletion_with_identical_untracked_replacement_fails(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            relative = "tools/campaign/wp03c/stage0.py"
            content = (candidate / relative).read_bytes()
            self.git(candidate, "rm", "--cached", relative)
            self.git(candidate, "commit", "-q", "-m", "delete tracked artifact")
            (candidate / relative).write_bytes(content)
            self.assertFalse(verifier.frozen_stage0_git_tree_integrity(
                candidate, candidate))
            self.assertFalse(verifier.frozen_stage0_worktree_integrity(
                candidate, candidate))

    def test_equal_tree_without_stage0_ancestry_fails(self):
        with tempfile.TemporaryDirectory() as name:
            candidate = self.clone_at_stage0(Path(name))
            tree = self.git(candidate, "rev-parse", "HEAD^{tree}")
            commit = self.git(candidate, "commit-tree", tree,
                              input_text="synthetic non-ancestor\n")
            self.git(candidate, "checkout", "-q", "--detach", commit)
            self.assertTrue(verifier.frozen_stage0_git_tree_integrity(
                candidate, candidate))
            self.assertFalse(verifier.historical_stage0_ancestor_of_head(candidate))

    def test_historical_tree_and_contract_identities_are_exact(self):
        scope = verifier.historical_stage0_scope(ROOT)
        paths = sorted(scope)
        aggregate = verifier.hashlib.sha256(
            ("\n".join(paths) + "\n").encode()).hexdigest()
        self.assertEqual(len(paths), verifier.STAGE0_PROTECTED_PATH_COUNT)
        self.assertEqual(aggregate, verifier.STAGE0_PROTECTED_PATH_AGGREGATE)
        self.assertIn(verifier.STAGE0_CONTRACT_PATH, scope)
        self.assertIn(
            "docs/reports/WP_0_3C_HUMAN_AND_APPARATUS_INPUT_GUIDE.md", scope)
        self.assertIn("validation/campaign/wp03c/WP_0_3C_INPUT_REQUIREMENTS.json", scope)
        self.assertIn("tools/campaign/wp03c/stage0.py", scope)
        self.assertEqual(11, sum("templates/" in path for path in scope))
        self.assertEqual(
            verifier.sha(ROOT / verifier.STAGE0_CONTRACT_PATH),
            verifier.STAGE0_CONTRACT_SHA256)


if __name__ == "__main__":
    unittest.main()
