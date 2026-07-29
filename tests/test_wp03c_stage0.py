import copy
import importlib.util
import json
import sys
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
        cls.templates = [json.loads(p.read_text()) for p in sorted(
            (ROOT / "validation/campaign/wp03c/templates").glob("*.json"))]

    def evaluate(self, contract=None, registry=None, templates=None, paths=None,
                 frozen=None, text=""):
        return verifier.evaluate(
            contract or self.contract, registry or self.registry,
            templates or self.templates,
            paths if paths is not None else verifier.EXPECTED_PATHS,
            frozen if frozen is not None else verifier.FROZEN, text)

    def test_unresolved_inputs_accepted_and_block_readiness(self):
        self.assertEqual(stage0.evaluate_readiness(
            [{"status": "UNRESOLVED_HUMAN_INPUT"}]),
            stage0.DISPOSITION)
        self.assertTrue(all(self.evaluate().values()))

    def test_partial_readiness(self):
        self.assertEqual(stage0.evaluate_readiness([
            {"status": "VERIFIED"}, {"status": "UNRESOLVED_HUMAN_INPUT"}]),
            "HUMAN_INPUTS_PARTIALLY_COMPLETE")

    def test_authority_absent(self):
        self.assertEqual(stage0.evaluate_readiness([], authority=False),
                         "AUTHORITY_NOT_ESTABLISHED")

    def test_invented_identity_or_sensor_observation_rejected(self):
        for field in ("verified human name", "fabricated sensor observed"):
            checks = self.evaluate(text=field + " password=secret")
            self.assertFalse(checks["no_forbidden_content"])

    def test_unaccountable_unresolved_value_rejected(self):
        templates = copy.deepcopy(self.templates)
        first = next(iter(next(iter(templates[0]["fields"].values())).values()))
        first.pop("responsible_role_id")
        self.assertFalse(self.evaluate(templates=templates)["unresolved_values_accountable"])

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
        self.assertFalse(self.evaluate(contract=contract)["fixed_path_boundary"])


if __name__ == "__main__":
    unittest.main()
