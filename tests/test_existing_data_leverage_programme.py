import importlib.util, pathlib, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ExistingDataLeverageProgrammeTest(unittest.TestCase):
    def test_existing_data_leverage_programme(self):
        spec = importlib.util.spec_from_file_location("validator", ROOT / "scripts/validate_existing_data_leverage_programme.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        data = module.validate()
        self.assertEqual(data["current_priority"], "XSV-PANNUSCH-EWP-INPUT-MAPPING-001")
        self.assertEqual(data["last_completed_opportunity_review"], "SCI-MD-PANNUSCH-FLOW-HISTORY-001")
        self.assertEqual(data["current_claim_ceiling"], "SOURCE_INTERNAL_FLOW_HISTORY_QUALIFICATION_ONLY")
        self.assertEqual(data["home_lab_status"], "DEFER_HOME_LAB_HIGHER_VALUE_EXISTING_DATA_TASKS_READY")
