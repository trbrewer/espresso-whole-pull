import sys
from pathlib import Path
from types import ModuleType
import unittest
import tempfile
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import form_a_report as R


class FormAReportTests(unittest.TestCase):
    def test_probe_reader_uses_internal_cells_and_checks_binary_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'X'
            path.write_bytes(b'format binary; arch "LSB;label=32;scalar=64";\n'
                b'internalField nonuniform List<scalar> 3\n('
                +np.array([.2,.5,.9],dtype='<f8').tobytes()+b');\nboundaryField { value uniform 99; }')
            np.testing.assert_array_equal(R.internal_scalars(path),[.2,.5,.9])
            with self.assertRaises(ValueError):R.internal_scalars(path,4)
            path.write_bytes(path.read_bytes().replace(b' arch "LSB;label=32;scalar=64";',b''))
            np.testing.assert_array_equal(R.internal_scalars(path),[.2,.5,.9])
            path.write_text('format ascii; internalField uniform 0.4; boundaryField { value uniform 99; }')
            np.testing.assert_array_equal(R.internal_scalars(path,3),[.4,.4,.4])
            path.write_text('format ascii; internalField nonuniform List<scalar> 3 (0.2 0.5 0.9);')
            np.testing.assert_array_equal(R.internal_scalars(path,3),[.2,.5,.9])

    def test_response_draws_are_paired_and_uniform_curves_have_no_sampling_spread(self):
        conditions = np.repeat(R.NOMINAL, 3)
        values = 3-(conditions-6.3)**2
        mean, draws = R.condition_draws(values, conditions)
        other, other_draws = R.condition_draws(values+2., conditions)
        np.testing.assert_allclose(other-mean, 2.)
        np.testing.assert_allclose(other_draws-draws, 2.)
        result = R.continuous_response(values, conditions)
        self.assertAlmostEqual(result['continuous_peak_bar'], 6.3)
        np.testing.assert_allclose(result['continuous_peak_interval_bar'], [6.3,6.3])
        self.assertEqual(result['continuous_peak_unresolved_draws'], 0)
        with self.assertRaises(ValueError):
            R.condition_draws(values[3:], conditions[3:])

    def test_censored_median_is_known_only_when_both_middle_values_are_observed(self):
        inputs, records = [], {}
        for pressure in R.NOMINAL:
            times = [10.,20.,-1.,-1.] if pressure == 1. else [10.,20.,30.,-1.]
            for i, time in enumerate(times):
                name = f'{pressure}-{i}'
                inputs.append(dict(brew=name, nominal_pressure_bar=pressure,
                    observed_onset_for_scoring_only_s=15.))
                records[name] = dict(first_drip_s=time)
        rows, summary = R.onset_rows(inputs, records, 'A1')
        self.assertIsNone(summary[0]['solver_median_s'])
        self.assertEqual(summary[0]['solver_median_lower_bound_s'], 60.)
        self.assertEqual(summary[1]['solver_median_s'], 25.)
        self.assertIsNone(summary[1]['solver_max_s'])
        self.assertTrue(all(r['solver_first_drip_stable_s'] is None for r in rows if r['right_censored']))

    def test_front_diagnostic_is_ungraded_and_retains_100_s_censoring(self):
        inputs = [dict(nominal_pressure_bar=float(p), observed_onset_for_scoring_only_s=10.) for p in R.NOMINAL]
        module = ModuleType('puckworks.analysis.pressure_peak_stage_c0')
        module.onset_grade = lambda value:'MISSES'
        with patch.dict(sys.modules, {'puckworks.analysis.pressure_peak_stage_c0':module}):
            result = R.onset_metrics(inputs, [-1.]*len(inputs))
        self.assertEqual(result['onset_rmse_s'], 90.)
        self.assertEqual(result['onset_censored_brews'], 11)
        self.assertTrue(result['onset_rmse_is_lower_bound'])
        self.assertNotIn('onset_grade',result)

    def test_detector_nan_uses_actual_confirmable_bound_and_never_grades_a_small_bound(self):
        inputs = [dict(nominal_pressure_bar=float(p), observed_onset_for_scoring_only_s=99.) for p in R.NOMINAL]
        module = ModuleType('puckworks.analysis.pressure_peak_stage_c0')
        module.onset_grade = lambda value:'MISSES' if value>4.53 else 'MEETS'
        with patch.dict(sys.modules, {'puckworks.analysis.pressure_peak_stage_c0':module}):
            result = R.onset_metrics(inputs,[float('nan')]*11,censor_bounds=[97.93]*11,observer='detector')
            self.assertEqual(result['onset_rmse_s'],0.)
            self.assertEqual(result['onset_grade'],'NOT_SCORED')
            self.assertEqual(result['onset_censored_brews'],11)
            for row in inputs:row['observed_onset_for_scoring_only_s']=10.
            result = R.onset_metrics(inputs,[None]*11,censor_bounds=[97.93]*11,observer='detector')
            self.assertAlmostEqual(result['onset_rmse_s'],87.93)
            self.assertEqual(result['onset_grade'],'MISSES')
            self.assertIn('Interval for the RMSE lower bound',result['onset_interval_definition'])
            with self.assertRaises(ValueError):R.onset_metrics(inputs,[None]*11,observer='detector')

    def test_detector_resamples_mass_before_the_reference_observer(self):
        module = ModuleType('puckworks.analysis.pressure_peak_stage_b0')
        observed_times=np.r_[[-1.,0.],np.linspace(.1,95.,300),[97.9,97.93,98.04,99.97,100.08]]
        captured={}
        def clean(time,pressure,mass):
            captured.update(time=time.copy(),mass=mass.copy())
            use=time>=0
            return time[use],pressure[use],np.full(use.sum(),.02),0.
        module.clean_course=clean
        module.sustained_onset=lambda *args:float('nan')
        parent=ModuleType('puckworks.analysis');parent.pressure_peak_stage_b0=module
        with patch.dict(sys.modules,{'puckworks.analysis':parent,'puckworks.analysis.pressure_peak_stage_b0':module}):
            result=R.detector_observation(np.linspace(.005,100.,20000),
                .02*np.linspace(.005,100.,20000),dict(time=observed_times,pressure=np.ones(len(observed_times))))
        np.testing.assert_array_equal(captured['time'],observed_times[1:-1])
        np.testing.assert_allclose(captured['mass'],.02*observed_times[1:-1])
        self.assertEqual(result['censor_bound_s'],97.93)
        self.assertEqual(result['last_retained_timestamp_s'],99.97)
        self.assertIsNone(result['onset_s'])


if __name__ == '__main__':
    unittest.main()
