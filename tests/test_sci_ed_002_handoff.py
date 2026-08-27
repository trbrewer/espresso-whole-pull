import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from scripts.verify_sci_ed_002_handoff import verify


class SciEd002Handoff(unittest.TestCase):
    def test_handoff_claim_ceiling(self):
        self.assertEqual(verify()["status"], "SCI_ED_002_HANDOFF_VERIFIED")

    def test_fail_closed_mutations(self):
        cases = (("commit","INTERMEDIATE_COMMIT_SUBSTITUTED_FOR_FINAL_HEAD"),("tree","PRODUCER_TREE_MISMATCH"),("export","SCHEMA_HASH_MISMATCH"),("schema","SCHEMA_HASH_MISMATCH"),("commissioning","COMMISSIONING_STATUS_WEAKENED"),("c_s0","C_S0_STATUS_WEAKENED"),("predictor","PREDICTOR_ELIGIBILITY_WEAKENED"),("holdout","HOLDOUT_STATUS_WEAKENED"))
        for mutation, reason in cases:
            with self.subTest(mutation=mutation), self.assertRaisesRegex(AssertionError, reason):
                verify(mutation=mutation)

    def test_producer_files_verify_when_available(self):
        producer_value = os.environ.get("PUCKWORKS_GIT_REPOSITORY")
        if producer_value is None:
            self.skipTest("PUCKWORKS_GIT_REPOSITORY not supplied")
        producer = Path(producer_value)
        self.assertTrue((producer / ".git").exists() or (producer / "HEAD").exists())
        self.assertTrue(verify(producer)["no_physics_change"])


if __name__ == "__main__":
    unittest.main()
