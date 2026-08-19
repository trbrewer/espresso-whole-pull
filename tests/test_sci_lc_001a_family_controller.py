import json
import multiprocessing
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import sci_lc_001a_family_controller as fc


def _reserve_worker(root, authority, queue):
    try: queue.put(("ok", fc.reserve(Path(root), Path(authority))["attempt_ordinal"]))
    except Exception as exc: queue.put(("error", str(exc)))


class FamilyControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "control"
        self.run = Path(self.temp.name) / "run"
        self.root.mkdir()
        fc.atomic_write(self.root / "family_hold.json", {"schema": fc.SCHEMA,
            "state": "RELEASED_FOR_EXACT_AUTHORITY", "authority_sha256": "a" * 64,
            "updated_at_utc": fc.utc_now()})
        self.authority = Path(self.temp.name) / "authority.json"
        self.write_authority()

    def tearDown(self): self.temp.cleanup()

    def write_authority(self, ordinal=4, maximum=4):
        fc.atomic_write(self.authority, {"schema": fc.AUTHORITY_SCHEMA,
            "authorization_id": "TEST", "attempt_ordinal": ordinal,
            "maximum_attempt_ordinal": maximum, "authorized_head": "h" * 40,
            "authorized_tree": "t" * 40, "allowed_root": str(self.run), "profile": "TEST"})

    def reserve(self): return fc.reserve(self.root, self.authority)

    def test_state_domain(self): self.assertEqual(len(fc.STATES), 12)
    def test_hold_gates_closed(self): self.assertEqual(len(fc.HOLD_GATES), 14)
    def test_reserve(self): self.assertEqual(self.reserve()["state"], "RESERVED")
    def test_same_reservation_idempotent(self): self.assertEqual(self.reserve(), self.reserve())
    def test_attempt_five_rejected(self):
        self.write_authority(5, 5)
        with self.assertRaisesRegex(ValueError, "ORDINAL"): self.reserve()
    def test_over_maximum_rejected(self):
        self.write_authority(4, 3)
        with self.assertRaisesRegex(ValueError, "ORDINAL"): self.reserve()
    def test_existing_root_rejected(self):
        self.run.mkdir()
        with self.assertRaisesRegex(ValueError, "ROOT_EXISTS"): self.reserve()
    def test_hold_before_allocation(self):
        fc.atomic_write(self.root / "family_hold.json", {"schema":fc.SCHEMA,"state":"HELD","authority_sha256":"a"*64,"updated_at_utc":fc.utc_now()})
        with self.assertRaises(PermissionError): self.reserve()
    def test_missing_hold_fails(self):
        (self.root / "family_hold.json").unlink()
        with self.assertRaisesRegex(ValueError, "MISSING"): self.reserve()
    def test_interrupted_state_write_rejected(self):
        (self.root / "family_hold.json").write_text("{")
        with self.assertRaisesRegex(ValueError, "AMBIGUOUS"): self.reserve()
    def test_two_simultaneous_requests_single_slot(self):
        queue = multiprocessing.Queue()
        workers = [multiprocessing.Process(target=_reserve_worker, args=(self.root,self.authority,queue)) for _ in range(2)]
        for worker in workers: worker.start()
        for worker in workers: worker.join()
        self.assertEqual([queue.get()[0] for _ in workers].count("ok"), 2)  # same authority is idempotent
        self.assertEqual(json.loads((self.root/"reservation.json").read_text())["attempt_ordinal"], 4)
    def test_different_second_reservation_rejected(self):
        self.reserve(); value=json.loads(self.authority.read_text()); value["authorization_id"]="OTHER"; fc.atomic_write(self.authority,value)
        with self.assertRaisesRegex(ValueError, "ALREADY_RESERVED"): self.reserve()
    def test_legal_transitions(self):
        self.reserve(); self.assertEqual(fc.transition(self.root,"STARTING",cause="test")["state"],"STARTING")
    def test_illegal_transition(self):
        self.reserve()
        with self.assertRaisesRegex(ValueError, "ILLEGAL"): fc.transition(self.root,"COMPLETE",cause="test")
    def test_repeated_terminalization_idempotent(self):
        self.reserve(); fc.transition(self.root,"ABORTED_BEFORE_DISPATCH",cause="test")
        self.assertEqual(fc.transition(self.root,"ABORTED_BEFORE_DISPATCH",cause="again")["state"],"ABORTED_BEFORE_DISPATCH")
    def test_dispatch_requires_running(self):
        self.reserve()
        with self.assertRaisesRegex(ValueError,"RUNNING"): fc.check_dispatch(self.root)
    def test_hold_immediately_before_dispatch(self):
        self.reserve(); fc.transition(self.root,"STARTING",cause="test"); fc.transition(self.root,"RUNNING",cause="test")
        value=json.loads((self.root/"family_hold.json").read_text()); value["state"]="HELD"; fc.atomic_write(self.root/"family_hold.json",value)
        with self.assertRaises(PermissionError): fc.check_dispatch(self.root)
    def test_dispatch_marks_consumed(self):
        self.reserve(); fc.transition(self.root,"STARTING",cause="test"); fc.transition(self.root,"RUNNING",cause="test")
        result=fc.transition(self.root,"STOP_REQUESTED",cause="test",dispatched=1); self.assertTrue(result["consumed"])
    def test_dispatch_regression_rejected(self):
        self.reserve(); fc.transition(self.root,"STARTING",cause="test"); fc.transition(self.root,"RUNNING",cause="test"); fc.transition(self.root,"STOP_REQUESTED",cause="test",dispatched=2)
        with self.assertRaisesRegex(ValueError,"REGRESSION"): fc.transition(self.root,"FINALIZING",cause="test",dispatched=1)
    def test_sigint_terminal_path(self): self._signal_path("SIGINT")
    def test_sigterm_terminal_path(self): self._signal_path("SIGTERM")
    def test_external_systemd_stop_path(self): self._signal_path("SYSTEMD_STOP")
    def test_supervisor_loss_path(self): self._signal_path("SUPERVISOR_LOSS")
    def _signal_path(self,cause):
        self.reserve(); fc.transition(self.root,"STARTING",cause="test"); fc.transition(self.root,"RUNNING",cause="test"); fc.transition(self.root,"STOP_REQUESTED",cause=cause); fc.transition(self.root,"FINALIZING",cause=cause); result=fc.transition(self.root,"STOPPED",cause=cause); self.assertEqual(result["lease_state"],"CLOSED")
    def test_stale_active_lease_dead_process(self): self.assertEqual(self.recover(False,False,"COMPLETE","ACTIVE",True),"STALE_LEASE_CLOSE_REQUIRED_NO_DISPATCH")
    def test_process_alive_missing_manifest(self): self.assertEqual(self.recover(True,True,None,"ACTIVE",True),"LIVE_PROCESS_MISSING_MANIFEST_HOLD_NO_DISPATCH")
    def test_manifest_running_no_process(self): self.assertEqual(self.recover(False,False,"RUNNING","CLOSED",True),"ORPHANED_MANIFEST_FINALIZATION_REQUIRED_NO_DISPATCH")
    def test_service_process_mismatch(self): self.assertEqual(self.recover(True,False,"RUNNING","ACTIVE",True),"PROCESS_SERVICE_LEASE_MISMATCH_HOLD_NO_DISPATCH")
    def test_root_reservation_mismatch(self): self.assertEqual(self.recover(False,False,None,None,False),"ROOT_RESERVATION_MISMATCH_HOLD_NO_DISPATCH")
    def recover(self,*args): self.reserve(); return fc.recover(self.root,process_alive=args[0],service_active=args[1],manifest_state=args[2],lease_state=args[3],root_exists=args[4])
    def test_readiness_zero_dispatch(self):
        result=fc.readiness(self.root); self.assertEqual(result["canonical_keys_dispatched"],0); self.assertFalse(result["canonical_dispatcher_reachable"])
    def test_no_classification_after_incomplete(self):
        self.assertIn("classification",fc.HOLD_GATES); self.assertNotIn("classify",fc.TRANSITIONS)
    def test_no_quarantine_reuse_transition(self): self.assertEqual(fc.TRANSITIONS["QUARANTINED"],set())
    def test_no_import_api(self): self.assertFalse(hasattr(fc,"import_results"))
    def test_process_identity_has_anti_pid_reuse_fields(self):
        value=fc.process_identity("test",self.run,"a"*64); self.assertIn("os_start_ticks",value); self.assertIn("command_sha256",value)


if __name__ == "__main__": unittest.main()
