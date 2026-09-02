import csv, hashlib, importlib.util, json, pathlib, subprocess, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ExistingDataLeverageProgrammeTest(unittest.TestCase):
    def test_existing_data_leverage_programme(self):
        spec = importlib.util.spec_from_file_location("validator", ROOT / "scripts/validate_existing_data_leverage_programme.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        data = module.validate()
        self.assertEqual(data["current_priority"], "SCI-ED-003")
        self.assertEqual(data["last_completed_opportunity_review"], "SCI-ED-003")
        self.assertEqual(data["current_claim_ceiling"], "CLOSURE_CONTRACT_ONLY")
        self.assertEqual(data["home_lab_status"], "DEFER_HOME_LAB_PENDING_SEPARATE_EXECUTION_AUTHORIZATION")

    @classmethod
    def setUpClass(cls):
        cls.programme = json.loads((ROOT / "provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json").read_text())
        with (ROOT / "docs/analysis/data_leverage/DATA_LEVERAGE_LEDGER.csv").open(newline="") as handle:
            cls.ledger = list(csv.DictReader(handle))

    def test_fusion_machine_ledger_agreement(self):
        machine = [x for x in self.programme["opportunities"] if x["opportunity_id"] == "SCI-DATA-FUSION-001"]
        ledger = [x for x in self.ledger if x["opportunity_id"] == "SCI-DATA-FUSION-001"]
        self.assertEqual((len(machine), len(ledger)), (1, 1))
        machine, ledger = machine[0], ledger[0]
        self.assertEqual(machine["status"], ledger["current_status"])
        self.assertEqual(machine["status"], "COMPLETE_NEGATIVE")
        self.assertTrue(machine["exhausted_for_decision"])
        self.assertEqual(ledger["exhausted_for_named_decision"], "true")
        self.assertEqual(machine["result"], ledger["result"])
        self.assertEqual(machine["next_action"], ledger["next_action"])
        self.assertEqual(ledger["evidence_path"], "docs/analysis/sci_data_fusion_001/DECISION.json")
        self.assertNotIn("implementation not authorized", ledger["data_not_yet_used"].lower())

    def test_current_priority_coherence(self):
        successor = [x for x in self.programme["opportunities"] if x["opportunity_id"] == "SCI-ED-003"]
        ledger = [x for x in self.ledger if x["opportunity_id"] == "SCI-ED-003"]
        self.assertEqual((len(successor), len(ledger)), (1, 1))
        successor, ledger = successor[0], ledger[0]
        self.assertEqual(self.programme["current_priority"], "SCI-ED-003")
        self.assertEqual(successor["status"], ledger["current_status"])
        self.assertEqual(successor["status"], "COMPLETE_POSITIVE")
        self.assertEqual(self.programme["current_claim_ceiling"], successor["claim_ceiling"])
        self.assertIn("EXECUTION_NOT_AUTHORIZED", successor["notes"])
        self.assertIn("NOT_ESTABLISHED", successor["notes"])
        self.assertFalse(self.programme["laboratory_gate"]["operation_authorized"])
        self.assertTrue(self.programme["laboratory_gate"]["separate_owner_authorization_required"])

    def test_completed_review_and_artifact_hashes(self):
        self.assertEqual(self.programme["last_completed_opportunity_review"], "SCI-ED-003")
        fusion = next(x for x in self.programme["opportunities"] if x["opportunity_id"] == "SCI-DATA-FUSION-001")
        self.assertEqual(fusion["result"], "SCI_DATA_FUSION_001_COMPLEMENTARY_SOURCE_CONDITIONED_SUPPORTS_ONLY")
        expected = {
            "DECISION.json": "437c7b99e8b4bdc876df84574acdf3464174522fa7f4978425d3ee484b70c501",
            "RESULT_ARTIFACT_MANIFEST.json": "6d0d298941b14174199e1909439b7bab81a7cc3655db56953f8ae646f84a33f2",
            "PREEXECUTION_AUDIT.json": "623620262fc9151f9033b41251400d73c3fb92dadc443b4593baeef6239f5e69",
        }
        result = ROOT / "docs/analysis/sci_data_fusion_001"
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((result / name).read_bytes()).hexdigest(), digest)
        manifest = json.loads((result / "RESULT_ARTIFACT_MANIFEST.json").read_text())
        self.assertEqual(len(manifest["artifacts"]), 31)
        for artifact in manifest["artifacts"]:
            self.assertEqual(hashlib.sha256((result / artifact["path"]).read_bytes()).hexdigest(), artifact["sha256"])

    def test_frozen_scientific_paths_unchanged(self):
        changed = subprocess.check_output([
            "git", "diff", "--name-only", "5968917fb4da2b671e9d6132e120ea1e646ce4a0", "--",
            "analysis/sci_data_fusion_001", "docs/analysis/sci_data_fusion_001",
        ], cwd=ROOT, text=True)
        self.assertEqual(changed, "")

    def test_human_current_state_agreement(self):
        sections = {
            "AGENTS.md": (ROOT / "AGENTS.md").read_text().split("Scientific-development governance", 1)[0],
            "docs/PROJECT_STATE.md": (ROOT / "docs/PROJECT_STATE.md").read_text().split("## XSV-PANNUSCH", 1)[0],
            "docs/CLAIM_CEILING.md": (ROOT / "docs/CLAIM_CEILING.md").read_text().split("`EWP-REAL-WORLD", 1)[0],
            "docs/strategy/EXISTING_DATA_LEVERAGE_PROGRAMME.md": (ROOT / "docs/strategy/EXISTING_DATA_LEVERAGE_PROGRAMME.md").read_text().split("## Pannusch-to-EWP", 1)[0],
            "docs/strategy/AVAILABLE_DATA_FIRST_POLICY.md": (ROOT / "docs/strategy/AVAILABLE_DATA_FIRST_POLICY.md").read_text().split("Before substantive", 1)[0],
            "docs/ONBOARDING.md": (ROOT / "docs/ONBOARDING.md").read_text().split("For validation work", 1)[0],
        }
        for text in sections.values():
            lower = text.lower()
            normalized = lower.replace("_", " ")
            self.assertIn("sci-ed-003", lower)
            self.assertIn("complete", lower)
            self.assertTrue("unauthorized" in lower or "not_authorized" in lower)
            self.assertIn("owner decision", normalized)
            self.assertNotIn("sci-ed-003` is `ready", lower)
            self.assertNotIn("sci-ed-003 is ready", lower)
            self.assertNotIn("sci-ed-003 is not implemented", lower)
        self.assertNotIn("sci-md-pannusch-flow-history-001", sections["docs/ONBOARDING.md"].lower())
