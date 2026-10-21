"""Focused arithmetic/provenance checks; no original payload needed in hosted CI."""
import csv
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('terminal_mass', ROOT/'tools/sci_md_wasz_terminal_mass_robustness_001/analyze.py')
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)
BUNDLE = ROOT/A.BUNDLE


class TerminalMassTests(unittest.TestCase):
    def raw(self, n=600):
        return A.np.column_stack([A.np.arange(n)*100, A.np.full(n, 1000), A.np.arange(n)*.1])

    def test_exact_501_search_and_start_origin(self):
        raw = self.raw()
        raw[0, 1] = 0
        raw[500, 1] = 0
        r = A.alignment(raw, 'unrelated.txt')
        self.assertEqual(r['alignment_violation_index'], 500)
        self.assertEqual(r['start_idx'], 501)
        self.assertEqual(A.aligned(raw, 501)[0][0], 0)
        self.assertAlmostEqual(A.aligned(raw, 501)[0][1], .1)

    def test_global_guard_and_all_false_reversed_prefix(self):
        raw = self.raw()
        with self.assertRaisesRegex(ValueError, 'GLOBAL_GUARD'):
            A.alignment(raw, 'x.txt')
        raw[550, 1] = 0
        r = A.alignment(raw, 'x.txt')
        self.assertEqual(r['start_idx'], 501)
        self.assertFalse(r['searched_prefix_has_violation'])

    def test_manual_pressure_corrections_and_strict_bounds(self):
        raw = self.raw()
        raw[:, 1] = 150
        raw[0, 1] = 0
        self.assertEqual(A.alignment(raw, 'x.txt')['reference_condition_bar'], 2)
        self.assertEqual(A.alignment(raw, '1-2.txt')['reference_condition_bar'], 1)
        raw[:, 1] = 1000
        raw[0, 1] = 0
        raw[400, 1] = 950  # exactly lower bound is not a violation
        self.assertEqual(A.alignment(raw, 'x.txt')['start_idx'], 1)
        raw[400, 1] = 949.999
        self.assertEqual(A.alignment(raw, 'x.txt')['start_idx'], 401)

    def test_brackets_exact_and_no_holding(self):
        t, m = A.np.array([90., 99.9, 100.1]), A.np.array([0., 9.9, 10.1])
        b = A.bracket(t, m, 100.)
        self.assertTrue(b['supported'])
        self.assertAlmostEqual(b['fraction'], .5)
        self.assertAlmostEqual(b['interpolated_mass_g'], 10.)
        self.assertTrue(A.bracket(t, m, 90.)['exact'])
        self.assertFalse(A.bracket(t, m, 101.)['supported'])
        self.assertFalse(A.bracket(t, m, 89.)['supported'])

    def test_gap_remains_calculable_and_explicit_not_automatically_rejected(self):
        b = A.bracket(A.np.array([80., 120.]), A.np.array([2., 42.]), 100)
        self.assertTrue(b['supported'])
        self.assertEqual(b['width_s'], 40)
        self.assertEqual(b['interpolated_mass_g'], 22)

    def test_constant_linear_and_negative_mass_increments(self):
        t = A.np.linspace(0, 110, 1101)
        for rate in [0., 2., -.2]:
            v, reasons, _ = A.mass_windows(t, 7+rate*t)
            for q in v.values():
                self.assertAlmostEqual(q, rate)
            self.assertFalse(any(reasons.values()))
            self.assertLess(float(A.np.max(A.np.abs(A.endpoint_operator(t, 7+rate*t)-rate))), 1e-10)

    def test_missing_endpoint_is_not_substituted(self):
        t = A.np.arange(100.)
        v, reasons, _ = A.mass_windows(t, t)
        self.assertEqual(v, dict(q10=None, q5=None, q20=None))
        self.assertTrue(all('OUTSIDE_MEASURED_SUPPORT' in s for s in reasons.values()))

    def test_invalid_raw_and_incomplete_terminal_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'raw.txt'
            def write(rows):
                p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            good = [dict(t=i*100, p2=100, m=i) for i in range(600)]
            for kind in ['duplicate', 'decreasing', 'nonfinite', 'interior_missing']:
                rows = [dict(r) for r in good]
                if kind == 'duplicate': rows[10]['t'] = rows[9]['t']
                if kind == 'decreasing': rows[10]['t'] = 0
                if kind == 'nonfinite': rows[10]['m'] = float('nan')
                if kind == 'interior_missing': del rows[10]['t']
                write(rows)
                with self.assertRaises(ValueError): A.acquisition(p)
            write(good+[dict(p2=110)])
            a = A.acquisition(p)
            self.assertEqual(len(a), 601)
            self.assertEqual(len(A.aligned(a, 1)[0]), 599)
            p.unlink()
            with self.assertRaises(FileNotFoundError): A.acquisition(p)

    def test_endpoint_sg_edge_matches_independent_linear_regression(self):
        t = A.np.arange(80.) + .01*A.np.sin(A.np.arange(80.))
        m = .2*t*t + A.np.cos(t)
        # Independently express nonuniform central gradient and terminal one-sided gradient.
        g = []
        for i in range(49, 80):
            if i == 79:
                g.append((m[i]-m[i-1])/(t[i]-t[i-1]))
            else:
                h0, h1 = t[i]-t[i-1], t[i+1]-t[i]
                g.append(h1/(h0+h1)*(m[i]-m[i-1])/h0 + h0/(h0+h1)*(m[i+1]-m[i])/h1)
        # Last SG value is fitted line at x=30 using derivative indices 0..30.
        mean = sum(g)/31
        beta = sum((i-15)*v for i,v in enumerate(g))/sum((i-15)**2 for i in range(31))
        self.assertAlmostEqual(A.endpoint_operator(t, m)[-1], mean+15*beta, places=11)

    def test_truncation_endpoint_holds_actual_last_sample(self):
        a = self.raw(1500)
        a[0, 1] = 0
        a[:, 0] = A.np.arange(1500)*93
        meta = A.alignment(a, 'x.txt')
        series, support = A.reconstruct(a, meta, [0, 0, 0])
        self.assertEqual(support['endpoint_behavior'], 'HOLD_LAST_RETAINED')
        self.assertLess(support['last_retained_time_s'], 100)
        self.assertGreater(support['first_subsequent_time_s'], 100)
        self.assertAlmostEqual(series['mass_flow_rate__g_per_s'][-1], 100/93)

    def test_composite_kernel_and_order_counterexample(self):
        s = A.synthetic()
        self.assertLess(s['endpoint_B'], s['endpoint_A'])
        self.assertGreater(s['negative_interval_count'], 0)
        self.assertAlmostEqual(s['sum_interval_weights'], 1)
        for key in A.WINDOWS:
            self.assertGreaterEqual(s['terminal_mass_B'][key], s['terminal_mass_A'][key]-1e-14)
        k = A.terminal_interval_kernel(A.np.arange(101.))
        self.assertGreater(k['negative_weight_count'], 0)
        self.assertAlmostEqual(k['weight_sum'], 1)

    def test_aggregation_sd_and_fixed_pressure_deletion(self):
        brews = [dict(physical_unit_id=str(i), condition_id=c, **{o:q for o in A.OBSERVERS})
                 for i,(c,q) in enumerate([('a',1.),('a',3.),('b',4.),('b',4.),('c',10.),('c',20.)])]
        p = {'a':1., 'b':4., 'c':10.}
        rows, s = A.summarize(brews, p, 'q10')
        self.assertEqual(rows[0]['mean_g_s'], 2)
        self.assertAlmostEqual(rows[0]['sd_g_s'], math.sqrt(2))
        self.assertAlmostEqual(s['low']['slope_g_s_bar'], 2/3)
        reduced, d = A.summarize(brews, p, 'q10', deleted='0')
        self.assertEqual([r['line_pressure_bar'] for r in reduced], list(p.values()))
        self.assertAlmostEqual(d['low']['slope_g_s_bar'], 1/3)
        self.assertIsNone(s['high']['slope_g_s_bar'])

    def test_retained_membership_and_serialization(self):
        result = json.loads((BUNDLE/'RESULT.json').read_text())
        source = json.loads((BUNDLE/'SOURCE_MANIFEST.json').read_text())
        brews = A.read_csv(BUNDLE/'BREW_RESULTS.csv')
        recon = A.read_csv(BUNDLE/'RECONSTRUCTION.csv')
        self.assertEqual(len(brews), 56)
        self.assertEqual(len({b['physical_unit_id'] for b in brews}), 56)
        self.assertEqual(len({b['condition_id'] for b in brews}), 11)
        self.assertEqual(source['alias']['extra_lines'], 42)
        self.assertTrue(source['alias']['exact_line_prefix'])
        self.assertEqual(len(source['source_files']), 61)
        self.assertTrue(all(x['authenticated'] for x in source['source_files'].values()))
        self.assertEqual(len(recon), 57)
        self.assertTrue(all(r['all_fields_within_serialization_tolerance']=='True' for r in recon))
        self.assertTrue(all(r['near100_matches_serialized']=='True' for r in recon))
        self.assertEqual(result['observers']['historical_endpoint']['low']['slope_g_s_bar'], .5042068394004887)
        self.assertEqual(result['observers']['historical_endpoint']['high']['slope_g_s_bar'], -.06550641262782862)
        self.assertEqual(len(result['common_support_ids']), 56)

    def test_retained_endpoint_support_and_raw_exceptions(self):
        support = json.loads((BUNDLE/'ACQUISITION_SUPPORT.json').read_text())
        self.assertEqual(len(support), 56)
        incomplete = [s for s in support if s['acquisition_qa']['incomplete_terminal_records']]
        self.assertEqual([s['source_id'] for s in incomplete], ['7-1'])
        for brew in support:
            for end in brew['endpoints'].values():
                self.assertTrue(end['supported'])
                self.assertLessEqual(end['left_time_s'], end['target_s'])
                self.assertGreaterEqual(end['right_time_s'], end['target_s'])
                expected = end['left_mass_g']+end['fraction']*(end['right_mass_g']-end['left_mass_g'])
                self.assertEqual(end['interpolated_mass_g'], expected)

    def test_retained_csv_json_means_slopes_and_deletions(self):
        result = json.loads((BUNDLE/'RESULT.json').read_text())
        brews = A.read_csv(BUNDLE/'BREW_RESULTS.csv')
        for b in brews:
            for o in A.OBSERVERS: b[o] = float(b[o]) if b[o] else None
        stored_conditions = A.read_csv(BUNDLE/'CONDITION_RESULTS.csv')
        for o in A.OBSERVERS:
            rows, summary = A.summarize(brews, result['fixed_pressure_coordinates'], o)
            for row in rows:
                stored = next(r for r in stored_conditions if r['observer']==o and r['condition_id']==row['condition_id'])
                self.assertEqual(float(stored['mean_g_s']), row['mean_g_s'])
                self.assertEqual(float(stored['sd_g_s']), row['sd_g_s'])
            for region in ['low','high']:
                self.assertAlmostEqual(summary[region]['slope_g_s_bar'],result['observers'][o][region]['slope_g_s_bar'],places=14)
        deleted, _ = A.influence(brews, result['fixed_pressure_coordinates'], result['observers'])
        stored = A.read_csv(BUNDLE/'INFLUENCE.csv')
        self.assertEqual(len(stored),56*4*2)
        for a,b in zip(deleted,stored):
            self.assertEqual(a['deleted_physical_unit_id'],b['deleted_physical_unit_id'])
            self.assertAlmostEqual(a['deletion_slope_g_s_bar'],float(b['deletion_slope_g_s_bar']),places=14)
            self.assertEqual(str(a['sign_change']),b['sign_change'])
            self.assertEqual(str(a['relevant_to_subset']),b['relevant_to_subset'])
            if not a['relevant_to_subset']: self.assertEqual(a['delta_g_s_bar'],0)

    def test_missing_deletion_explicit_and_sign_bookkeeping(self):
        brews = [dict(physical_unit_id=str(i), condition_id=c, **{o:q for o in A.OBSERVERS})
                 for i,(c,q) in enumerate([('a',0.),('a',10.),('b',4.),('b',4.),('h',3.),('h',5.),('j',1.),('j',2.)])]
        p = {'a':1., 'b':4., 'h':9., 'j':12.}
        baseline = {o:A.summarize(brews,p,o)[1] for o in A.OBSERVERS}
        rows, _ = A.influence(brews,p,baseline)
        self.assertTrue(any(r['sign_change'] for r in rows))
        brews[0]['q5'] = None
        rows, _ = A.influence(brews,p,baseline)
        self.assertTrue(all(not r['paired_deletion_available'] for r in rows if r['deleted_physical_unit_id']=='0' and r['observer']=='q5'))


if __name__ == '__main__':
    unittest.main()
