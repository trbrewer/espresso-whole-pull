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

    def test_censoring_gives_an_onset_rmse_lower_bound_without_using_minus_one(self):
        inputs = [dict(nominal_pressure_bar=float(p), observed_onset_for_scoring_only_s=10.) for p in R.NOMINAL]
        module = ModuleType('puckworks.analysis.pressure_peak_stage_c0')
        module.onset_grade = lambda value:'MISSES'
        with patch.dict(sys.modules, {'puckworks.analysis.pressure_peak_stage_c0':module}):
            result = R.onset_metrics(inputs, [-1.]*len(inputs))
        self.assertEqual(result['onset_rmse_s'], 90.)
        self.assertEqual(result['onset_censored_brews'], 11)
        self.assertTrue(result['onset_rmse_is_lower_bound'])
        self.assertEqual(result['onset_grade'], 'MISSES')


if __name__ == '__main__':
    unittest.main()
