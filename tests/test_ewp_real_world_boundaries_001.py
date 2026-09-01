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
from analysis.ewp_real_world_boundaries_001.privacy import classify_group
from analysis.ewp_real_world_boundaries_001.qualification import (
    PressureTransferAuthority, TransferState, qualify, structural_statuses,
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

    def test_unrelated_scale_flow_mismatch_does_not_invalidate_achieved_pressure(self):
        raw={"schema_version":6,"hydraulic":{"time__s":[0,1,2],"pressure__Pa":[0,1,2],"mass_flow_from_scale__kg_per_s":[0,1]},"context":{},"qc":{"time_monotonic":True}}
        flags,reasons=qualify(adapt(raw)); self.assertTrue(flags["achieved_pressure_profile_eligible"]); self.assertFalse(flags["scale_flow_profile_eligible"]); self.assertIn("ARRAY_LENGTH_MISMATCH_SCALE_FLOW",reasons)

    def test_achieved_mismatch_does_not_invalidate_command(self):
        raw={"schema_version":6,"hydraulic":{"time__s":[0,1,2],"pressure__Pa":[0,1],"pressure_goal__Pa":[0,1,2]},"context":{},"qc":{"time_monotonic":True}}
        flags,reasons=qualify(adapt(raw)); self.assertTrue(flags["commanded_pressure_profile_eligible"]); self.assertFalse(flags["achieved_pressure_profile_eligible"]); self.assertFalse(flags["pressure_tracking_eligible"]); self.assertIn("ARRAY_LENGTH_MISMATCH_ACHIEVED_PRESSURE",reasons)

    def test_water_mismatch_does_not_invalidate_scale_flow(self):
        raw={"schema_version":6,"hydraulic":{"time__s":[0,1,2],"mass_flow_from_scale__kg_per_s":[0,.1,.2],"water_dispensed__kg":[0,1]},"context":{},"qc":{"time_monotonic":True}}
        flags,reasons=qualify(adapt(raw)); self.assertTrue(flags["scale_flow_profile_eligible"]); self.assertIn("ARRAY_LENGTH_MISMATCH_WATER_DISPENSED",reasons)

    def test_non_null_strings_are_not_transfer_authority(self):
        raw={"schema_version":6,"hydraulic":{"time__s":[0,1],"pressure__Pa":[0,1]},"context":{"machine":"synthetic_machine","integration_source":"synthetic_controller","integration_source_provenance":"synthetic_doc"},"qc":{"time_monotonic":True}}
        flags,_=qualify(adapt(raw)); self.assertFalse(flags["ewp_pressure_boundary_executable"])

    def test_explicit_command_authority_is_independent_of_achieved_sensor(self):
        authority=PressureTransferAuthority(integration_controller_family_resolved=True,pressure_goal_definition_source_verified=True,command_units_resolved=True,command_time_basis_resolved=True,explicitly_commanded_setpoint=True,target_ramp_operator_compatible=True,no_achieved_pressure_claim=True)
        self.assertEqual(authority.command_state,TransferState.COMMAND_TRANSFER_RESOLVED); self.assertEqual(authority.achieved_state,TransferState.ACHIEVED_TRANSFER_UNRESOLVED)
        raw={"schema_version":6,"hydraulic":{"time__s":[0,1],"pressure_goal__Pa":[0,1]},"context":{},"qc":{"time_monotonic":True}}
        flags,_=qualify(adapt(raw),authority); self.assertTrue(flags["ewp_pressure_boundary_executable"])

    def test_semantically_unresolved_large_group_is_not_privacy_suppressed(self):
        unresolved=classify_group(20,10,False); private=classify_group(19,10,False)
        self.assertTrue(unresolved.privacy_threshold_passes); self.assertTrue(unresolved.semantic_unresolved_unpublished); self.assertFalse(unresolved.privacy_suppressed)
        self.assertTrue(private.privacy_suppressed); self.assertFalse(private.semantic_unresolved_unpublished)

    def test_all_unresolved_normalized_condition_has_zero_executable_records(self):
        records=[{"schema_version":6,"hydraulic":{"time__s":[0,1],"pressure__Pa":[0,1],"pressure_goal__Pa":[0,1]},"context":{},"qc":{"time_monotonic":True}} for _ in range(20)]
        self.assertEqual(sum(qualify(adapt(raw))[0]["ewp_pressure_boundary_executable"] for raw in records),0)


if __name__ == "__main__":
    unittest.main()
