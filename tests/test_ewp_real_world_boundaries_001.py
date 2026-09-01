import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from analysis.ewp_real_world_boundaries_001.authority import (
    STOP_AUTHORITY, STOP_PROTOCOL, verify_protocol, verify_puckworks,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/analysis/ewp_real_world_boundaries_001/PROTOCOL_FREEZE.json"


class ProtocolAuthorityTests(unittest.TestCase):
    def test_protocol_hash_is_required_and_modification_fails(self):
        digest = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
        self.assertEqual(verify_protocol(PROTOCOL, digest)["protocol_id"], "EWP_RWB_001_PROTOCOL_V1")
        with self.assertRaisesRegex(RuntimeError, STOP_PROTOCOL):
            verify_protocol(PROTOCOL, "")
        with tempfile.TemporaryDirectory() as td:
            changed = Path(td) / "protocol.json"
            changed.write_text(PROTOCOL.read_text() + " ")
            with self.assertRaisesRegex(RuntimeError, STOP_PROTOCOL):
                verify_protocol(changed, digest)

    def test_frozen_rules_and_claim_boundaries(self):
        p = json.loads(PROTOCOL.read_text())
        self.assertEqual(p["corpus_contract"]["classification"], "current-state")
        self.assertEqual(p["privacy"]["minimum_shots_per_published_cell"], 20)
        self.assertEqual(p["privacy"]["minimum_distinct_users_per_published_cell"], 10)
        self.assertEqual(p["library_rule"]["maximum_cases"], 12)
        self.assertEqual(len(p["porosity_states"]), 3)
        self.assertFalse(p["rights"]["live_api"])
        self.assertFalse(p["rights"]["raw_redistribution"])

    def test_wrong_puckworks_head_fails_closed(self):
        with mock.patch("subprocess.check_output", side_effect=["wrong\n", "wrong-tree\n"]):
            with self.assertRaisesRegex(RuntimeError, STOP_AUTHORITY):
                verify_puckworks(ROOT)


if __name__ == "__main__":
    unittest.main()
