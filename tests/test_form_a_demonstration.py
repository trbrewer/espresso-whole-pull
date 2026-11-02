import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import form_a_demonstration as D


class FormADemonstrationTests(unittest.TestCase):
    def test_parallel_partitions_cover_every_declared_case_once(self):
        inputs = [dict(brew=f'brew-{i}', nominal_pressure_bar=D.V.NOMINAL[i % 11]) for i in range(56)]
        jobs = D.campaign_matrix(inputs)
        left, right = set(jobs[::2]), set(jobs[1::2])
        self.assertEqual(len(jobs), 181)
        self.assertFalse(left & right)
        self.assertEqual(left | right, set(jobs))
        self.assertEqual(sum(arm == 'A0' for arm, *_ in jobs), 23)
        self.assertFalse(any(arm == 'A0' and forcing == 'measured_history' for arm, forcing, *_ in jobs))
        with self.assertRaises(ValueError): D.campaign_matrix(inputs[:-1])

    def test_run_matrix_and_saved_fold_routing(self):
        pressures = D.constant_pressures()
        self.assertEqual(len(pressures), 23)
        self.assertTrue({1., 2., 3.5, 8.25, 8.5, 8.75, 13.} <= set(pressures))
        bank = {'DESCRIPTIVE_ALL': {'a': 1}, 'HYD-LOCO-3.5': {'a': 2}}
        self.assertEqual(D.parameters_for(bank, 'constant', 3.5), {'a': 1})
        self.assertEqual(D.parameters_for(bank, 'measured_history', 3.5), {'a': 2})

    def test_peak_pair_extends_until_both_steps_are_bracketed(self):
        calls = []
        def fake(args, bank, pressure, dt, arm, xc, forcing):
            calls.append((pressure, dt))
            peak = 7.0 if dt == .0025 else 7.04
            return dict(endpoint_flow_g_s=2-(pressure-peak)**2,
                        first_drip_s=10+dt, run=f'{pressure}-{dt}')
        with tempfile.TemporaryDirectory() as td:
            args = SimpleNamespace(work=Path(td), arm='A1', executable=Path(td)/'solver')
            args.executable.write_bytes(b'synthetic')
            with patch.object(D, 'run_constant', side_effect=fake):
                D.step_pair(args, {})
            r = json.loads((args.work/'A1-STEP_STUDY.json').read_text())
        self.assertAlmostEqual(r['continuous_peak_bar']['fine'], 7.)
        self.assertAlmostEqual(r['peak_change_bar'], .04)
        self.assertTrue({(p, dt) for p in (2., 6., 11.) for dt in (.0025, .005)} <= set(calls))
        self.assertEqual(len(calls), len(set(calls)))
        self.assertFalse(r['inventory_metric_used_for_choice'])

    def test_campaign_cannot_silently_choose_a_different_step(self):
        with tempfile.TemporaryDirectory() as td:
            args = SimpleNamespace(work=Path(td), executable=Path(td)/'solver', arm='A1')
            args.executable.write_bytes(b'changed')
            (args.work/'STEP_SELECTION.json').write_text(json.dumps(dict(
                studies={}, executable_sha256='old', delta_t_s=.005)))
            with self.assertRaisesRegex(ValueError, 'another executable'):
                D.run_campaign(args, {})


if __name__ == '__main__': unittest.main()
