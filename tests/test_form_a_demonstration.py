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
        self.assertEqual(len(jobs), 102)
        self.assertFalse(left & right)
        self.assertEqual(left | right, set(jobs))
        self.assertEqual(sum(arm == 'A0' for arm, *_ in jobs), 23)
        self.assertEqual(sum(arm == 'A1' for arm, *_ in jobs), 79)
        self.assertFalse(any(arm == 'A2' for arm, *_ in jobs))
        self.assertFalse(any(arm == 'A0' and forcing == 'measured_history' for arm, forcing, *_ in jobs))
        with self.assertRaises(ValueError): D.campaign_matrix(inputs[:-1])

    def test_run_matrix_and_saved_fold_routing(self):
        pressures = D.constant_pressures()
        self.assertEqual(len(pressures), 23)
        self.assertTrue({1., 2., 3.5, 8.25, 8.5, 8.75, 13.} <= set(pressures))
        bank = {'DESCRIPTIVE_ALL': {'a': 1}, 'HYD-LOCO-3.5': {'a': 2}}
        self.assertEqual(D.parameters_for(bank, 'constant', 3.5), {'a': 1})
        self.assertEqual(D.parameters_for(bank, 'measured_history', 3.5), {'a': 2})
        with self.assertRaisesRegex(ValueError,'retired'):
            D.run_campaign(SimpleNamespace(arm='A2'),{})

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

    def test_recovery_preserves_completed_run_and_failed_qualification_without_execution(self):
        with tempfile.TemporaryDirectory() as td:
            work=Path(td);case=work/'retained';case.mkdir();(case/'system').mkdir()
            (case/'system/fvSolution').write_text('retained controls')
            trace=case/'postProcessing/wholePull/0/traces.csv';trace.parent.mkdir(parents=True)
            trace.write_text('time_s,outlet_flow_m3_s,first_drip_s,cup_water_mass_kg,form_a_bed_mean_x,form_a_min_cell_x_increment,max_concentration_kg_m3\n'
                '100,0.0000001,54,0.004,0.4,0,180.000000020847\n')
            (case/'wall_seconds.txt').write_text('5\n');(case/'log.solver').write_text('End\n')
            exe=work/'solver';exe.write_bytes(b'unchanged executable')
            cfg=dict(form_a_whole_bed_closure=dict(arm='A1'),time=dict(delta_t_s=.005),
                     liquid=dict(density_kg_m3=965),extraction=dict(saturation_concentration_kg_m3=180.))
            (work/'retained.json').write_text(json.dumps(cfg,indent=2)+'\n')
            with patch.object(D.V,'run_case') as execute,patch.object(D.E1,'balance_bounds',return_value=dict(status='FAIL',bounded=False)):
                result=D.execute(work,'retained',cfg,exe,1.,'measured_history','1-2',32,recover_completed=True)
            execute.assert_not_called()
            self.assertTrue(result['native_completed'])
            self.assertFalse(result['balances_and_bounds_qualified'])
            self.assertEqual(result['numerical_balance_bounds']['status'],'FAIL')
            self.assertEqual(result['maximum_concentration_kg_m3'],180.000000020847)
            self.assertEqual(result['concentration_limit_kg_m3'],180.)
            self.assertEqual(result['core_hours'],5*32/3600)
            self.assertIn('log.solver',result['native_log_sha256'])
            self.assertEqual(json.loads((work/'retained.result.json').read_text()),result)


if __name__ == '__main__': unittest.main()
