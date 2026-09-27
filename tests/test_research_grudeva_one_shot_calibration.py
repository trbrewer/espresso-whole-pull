"""Thin-consumer identity tests plus explicitly enabled synthetic producer parity."""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('one_shot_consumer', ROOT/'scripts/research_grudeva_one_shot_calibration.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)


class Identity(unittest.TestCase):
    def test_wrong_producer_identity_before_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'pin.json'; path.write_text('{"producer_commit":"a","producer_tree":"b"}')
            with patch.object(c.parent, 'git', return_value='wrong'), self.assertRaisesRegex(ValueError, 'EXACT_EVALUATED_008'):
                c.load_producer(tmp, path)


@unittest.skipUnless(os.environ.get('SCI_MD_MASS_DELIVERY_008_PRODUCER'), 'explicit exact producer unavailable')
class Synthetic(unittest.TestCase):
    def setUp(self):
        self.producer = Path(os.environ['SCI_MD_MASS_DELIVERY_008_PRODUCER'])
        self.task, self.pin = c.load_producer(self.producer)

    def test_wrong_runtime_parent_and_source_rejected(self):
        changes = [({'producer_tree': '0'*40}, 'EXACT_EVALUATED'),
                   ({'parent_producer_commit': '0'*40}, 'ACCEPTED_PARENT'),
                   ({'source_sha256': '0'*64}, 'ACCEPTED_PARENT'),
                   ({'wrapper_schema': 'wrong'}, 'WRAPPER_SCHEMA')]
        wrong = dict(self.pin['producer_files']); wrong[c.PREFIX+'source_calibrated_tail_delivery.py'] = '0'*64
        changes.append(({'producer_files': wrong}, 'ACTUAL_SOURCE'))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'pin.json'
            for change, error in changes:
                path.write_text(json.dumps(self.pin | change))
                with self.assertRaisesRegex(ValueError, error):
                    c.load_producer(self.producer, path)

    def test_offset_and_mass_serialization_wrong_parent_calibrator_units(self):
        t = self.task; md, api = t.md, t.api
        model = md.synthetic_model(); early = md.EarlyInput('C2', model.means, 'SYNTHETIC')
        record = api.CalibrationRecord('a'*64, 1, early, (api.Observation(1, 1, .01, .01, .02, .08),))
        cal = api.calibrate_source(model, record); self.assertEqual(cal.status, 'QUALIFIED')
        state = cal.condition(early)
        self.assertEqual(api.OffsetState.from_dict(state.to_dict()), state)
        for expected in ({'parent_sha256': 'b'*64}, {'calibrator': 2}):
            with self.assertRaises(ValueError):
                api.OffsetCalibration.from_dict(cal.to_dict(), **expected)
        wrong = cal.to_dict(); wrong['units']['beverage'] = 'g'
        with self.assertRaises(ValueError):
            api.OffsetCalibration.from_dict(wrong)
        queries = [{'shot': 2, 'vial': 15, 'mass_kg': .01, 'start_kg': .01, 'end_kg': .02}]
        result = t.predict_pair(cal, 2, early, queries)
        self.assertEqual(result[0]['prediction'], asdict(state.predict_intervals([.01], [.02])[0]))
        wrong_q = deepcopy(queries); wrong_q[0]['suffix_q'] = .2
        with self.assertRaises(ValueError):
            t.predict_pair(cal, 2, early, wrong_q)
        mass = api.MassCalibration('a'*64, 1, 'b'*64, (.1, 0., .02, 1.), .08, (.01, .02), 'QUALIFIED')
        self.assertEqual(api.MassCalibration.from_dict(mass.to_dict()), mass)
        with self.assertRaises(ValueError):
            mass.condition(early)


if __name__ == '__main__':
    unittest.main()
