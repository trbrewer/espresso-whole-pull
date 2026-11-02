import copy
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from prepare_case import render_properties, render_form_a, form_a_fv_solution
from form_a_verification import scenario, xc_at_mass, capacity_peak

P = dict(aGPerSBar=.7757444238135915, pstarBar=24.396659674282887,
         n=2.4709360685491837, pdBar=3.5633704054718103, mcG=28.709461834955388)


class FormATests(unittest.TestCase):
    def test_disabled_dictionary_preserves_absent_bytes(self):
        cfg = json.loads((ROOT/'config/reference_R0.json').read_text())
        expected = render_properties(cfg)
        cfg['form_a_whole_bed_closure'] = dict(enabled=False, arm='invalid')
        self.assertEqual(render_properties(cfg), expected)
        self.assertNotIn('formAWholeBedClosure', expected)

    def test_native_extraction_is_retained_and_hydraulic_closures_exclusive(self):
        cfg = scenario(P, 'A2', xc=.5)
        rendered = render_properties(cfg)
        self.assertIn('formAWholeBedClosure', rendered)
        self.assertEqual(cfg['extraction']['rate_constant_1_s'], .15)
        self.assertEqual(cfg['coffee_bed']['initial_extractable_fraction_dry_basis'], .28)
        for key, value in [('effective_permeability_evolution', {}),
                           ('e1_whole_bed_closure', {'enabled': True}),
                           ('flowResistanceModel', 'darcyForchheimer')]:
            other = copy.deepcopy(cfg); other[key] = value
            with self.assertRaises(ValueError): render_form_a(other)
        for xc in [None, 0, -1, 1.1, math.inf, math.nan]:
            other = copy.deepcopy(cfg); other['form_a_whole_bed_closure']['xc'] = xc
            with self.assertRaises((ValueError, TypeError)): render_form_a(other)
        with self.assertRaises(ValueError): scenario(P, 'A2')

    def test_local_permeability_pressure_precision_preserves_other_solver_controls(self):
        original = (ROOT/'cases/reference_R0_20g_58mm_9bar/system/fvSolution').read_text()
        for arm in ('A0', 'A1'):
            self.assertEqual(form_a_fv_solution(scenario(P, arm), original), original)
        cfg = scenario(P, 'A2', xc=.5)
        actual = form_a_fv_solution(cfg, original)
        self.assertEqual(actual, original.replace('tolerance       1e-12;', 'tolerance       1e-14;', 1))
        self.assertEqual(form_a_fv_solution(cfg, actual), actual)
        cfg['form_a_whole_bed_closure']['enabled'] = False
        self.assertEqual(form_a_fv_solution(cfg, original), original)
        cfg['form_a_whole_bed_closure']['enabled'] = True
        cfg['form_a_pressure_solver_tolerance'] = float('nan')
        with self.assertRaises(ValueError): form_a_fv_solution(cfg, original)

    def test_raw_pressure_is_clamped_without_using_observed_onset(self):
        cfg = scenario(P, 'A1', history=([0., 50., 100.], [-.1, 6., 0.]))
        h = cfg['hydraulics']['prescribed_pressure_boundary']
        self.assertEqual(h['pressures_gauge_Pa'], [0., 600000., 0.])
        self.assertNotIn('observedOnset', json.dumps(cfg))

    def test_xc_is_inventory_interpolated_at_outlet_mass_not_flow_fitted(self):
        rows = [dict(cup_water_mass_kg=.01, form_a_bed_mean_x=.2),
                dict(cup_water_mass_kg=.03, form_a_bed_mean_x=.6)]
        self.assertAlmostEqual(xc_at_mass(rows, 20), .4)
        with self.assertRaises(ValueError): xc_at_mass(rows, 40)
        rows[1]['form_a_bed_mean_x'] = .1
        with self.assertRaises(ValueError): xc_at_mass(rows, 20)

    def test_saved_descriptive_capacity_expectation(self):
        self.assertAlmostEqual(capacity_peak(P), 5.998561185369216, places=11)

    def test_cpp_darcy_conversion_uniform_x_and_monotonic_inventory(self):
        source = '''#include "formAWholeBedClosure.H"
#include <iomanip>
#include <iostream>
int main() {
 espresso::FormAParameters f{.7757444238135915,24.396659674282887,
 2.4709360685491837,3.5633704054718103,28.709461834955388,.4}; f.validate(true);
 std::cout << std::setprecision(17);
 for(double p : {0., 1e-12, 1., 2., 3.5, 6., 9., 13.})
  for(double m : {0., 28.709461834955388, 100.})
   std::cout << "flow " << p << " " << m << " "
     << 1000*965*.0026*f.basePermeability(.000315,.009,965,.0026)
       *f.multiplier(p*1e5,m)*p*1e5/(.000315*.009) << "\\n";
 for(double x : {0., .1, .4, .7, 1.})
  std::cout << "uniform " << x << " " << f.localRecovery(x) << " "
    << f.recovery(f.mc*x/f.xc) << "\\n";
 double remaining=10, previous=0;
 for(int i=0;i<100;++i) {
  remaining-=.05*remaining;
  const double x=f.extractedFraction(remaining,10);
  if(x<previous) return 2;
  previous=x;
 }
 for(double p : {-1.,0.,1e-300})
  if(!std::isfinite(f.pressureMultiplier(p))) return 3;
 f.n=1;
 if(f.pressureMultiplier(0)!=1.) return 4;
 try { f.extractedFraction(11,10); return 5; } catch(const std::invalid_argument&) {}
}'''
        with tempfile.TemporaryDirectory() as td:
            p = Path(td); (p/'check.C').write_text(source)
            subprocess.run(['g++', '-std=c++14', '-I', str(ROOT/'solver/espressoWholePullFoam'),
                            str(p/'check.C'), '-o', str(p/'check')], check=True, capture_output=True)
            lines = subprocess.check_output([str(p/'check')], text=True).splitlines()
        for line in lines:
            kind, *numbers = line.split(); a, b, actual = map(float, numbers)
            if kind == 'uniform':
                self.assertAlmostEqual(b, actual, places=15)
            else:
                expected = P['aGPerSBar']*P['pdBar']*(-math.expm1(-(a/P['pdBar'])**P['n']))
                expected *= math.exp(-a/P['pstarBar'])*math.exp(-math.exp(-b/P['mcG']))
                self.assertTrue(math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-30), line)


if __name__ == '__main__': unittest.main()
