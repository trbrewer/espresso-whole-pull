import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from analysis.ewp_real_world_boundaries_001.authority import (
    STOP_AUTHORITY, STOP_PROTOCOL, verify_protocol, verify_puckworks,
)
from analysis.ewp_real_world_boundaries_001.corpus_adapter import adapt, public_safe
from analysis.ewp_real_world_boundaries_001.qualification import qualify

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

    def test_adapter_discards_identity_outcomes_and_unknown_fields_from_public_view(self):
        raw={"id":"synthetic_A","hashed_user":"cluster_A","schema_version":6,"outcomes":{"tds__fraction":.1},"notes":"secret","unknown":{"x":1},
             "hydraulic":{"time__s":[0,1],"pressure__Pa":[0,100000],"flow_reported__native":[1,2]},"context":{"dose__kg":.02},"qc":{"time_monotonic":True}}
        adapted=adapt(raw); public=public_safe(adapted)
        self.assertNotIn("outcomes", public); self.assertNotIn("notes", public); self.assertNotIn("audit_id", public); self.assertNotIn("local_linkage", public)
        self.assertTrue(adapted.ambiguous_native_flow_present); self.assertFalse(public.get("has_scale_flow"))

    def test_achieved_commanded_and_outlet_flow_are_separate(self):
        raw={"schema_version":6,"hydraulic":{"time__s":[0,1],"pressure__Pa":[1,2],"pressure_goal__Pa":[3,4],"mass_flow_from_scale__kg_per_s":[0,.001]},"context":{},"qc":{"time_monotonic":True}}
        r=adapt(raw); self.assertNotEqual(r.achieved_pressure_pa,r.commanded_pressure_pa); self.assertEqual(r.scale_flow_kg_s[-1],.001)
        flags,reasons=qualify(r); self.assertFalse(flags["ewp_pressure_boundary_executable"]); self.assertIn("UNKNOWN_PRESSURE_SENSOR_DEVICE_FAMILY",reasons)

    def test_nonmonotone_and_length_mismatch_fail_without_repair(self):
        raw={"schema_version":6,"hydraulic":{"time__s":[0,2,1],"pressure__Pa":[1,2]},"context":{},"qc":{"time_monotonic":False}}
        flags,reasons=qualify(adapt(raw)); self.assertIn("NONMONOTONE_TIME",reasons); self.assertIn("ARRAY_LENGTH_MISMATCH",reasons); self.assertFalse(flags["boundary_summary_eligible"])


if __name__ == "__main__":
    unittest.main()
