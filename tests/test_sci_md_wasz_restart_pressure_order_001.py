"""Mathematical and observation risks for the bounded exact order certificate."""
import copy
from fractions import Fraction as Q
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('order_test', ROOT/'tools/sci_md_wasz_restart_pressure_order_001/analyze.py')
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)
BUNDLE = ROOT/'docs/analysis/sci_md_wasz_restart_pressure_order_001'


def pair(pc=(7, 7, 7), pr=(8, 8, 8), qc=3, qr=2, ct=(0, 50, 100), rt=(0, 50, 100)):
    rows = [dict(t=t, m=Q(t)*qr/1000, p2=Q(p)*100, p1=999999) for t, p in zip(rt, pr)]
    rows += [dict(t=1000+t, m=Q(20)+Q(t)*qc/1000, p2=Q(p)*100, p1=-999999) for t, p in zip(ct, pc)]
    obs = A.Observer(rows)
    r = obs.interval('R', rt[0], rt[-1], (0, len(rt)-1))
    c = obs.interval('C', 1000+ct[0], 1000+ct[-1], (len(rt), len(rows)-1))
    return obs, c, r


def comparison(**kwargs):
    o, c, r = pair(**kwargs)
    return A.compare(o, c, r, 'test')


class OrderTests(unittest.TestCase):
    def test_lower_pressure_higher_delivery(self):
        c = comparison()
        self.assertEqual(c['pressure_class'], A.LOWER)
        self.assertEqual(c['delta_q_g_s'], 1)
        self.assertEqual(c['contradiction_status'], A.EXCLUDED)
        self.assertTrue(c['strict_separation'])

    def test_higher_pressure_lower_delivery(self):
        c = comparison(pc=(9, 9, 9), qc=1)
        self.assertEqual(c['pressure_class'], A.HIGHER)
        self.assertEqual(c['contradiction_status'], A.EXCLUDED)
        self.assertEqual(c['robustness']['ordered_margin_bar'], 1)

    def test_weak_order_touching_zero(self):
        c = comparison(pc=(7, 8, 7))
        self.assertEqual(c['pressure_class'], A.LOWER)
        self.assertFalse(c['strict_separation'])
        self.assertEqual(c['contradiction_status'], A.EXCLUDED)
        self.assertEqual(c['robustness']['ordered_margin_bar'], 0)
        self.assertEqual(c['min_knot_indices'], [1])

    def test_identical_pressure_equal_and_unequal_delivery(self):
        for qc, status in [(2, A.UNEXCLUDED), (3, A.EXCLUDED), (1, A.EXCLUDED)]:
            c = comparison(pc=(8, 8, 8), qc=qc)
            self.assertEqual(c['pressure_class'], A.IDENTICAL)
            self.assertEqual(c['contradiction_status'], status)
            self.assertFalse(c['strict_separation'])
            self.assertTrue(all(s['minimum_at'] == 'WHOLE_SEGMENT' for s in c['segments']))

    def test_strict_pressure_equal_delivery_allows_flat_F(self):
        for pc in [(7, 7, 7), (9, 9, 9)]:
            c = comparison(pc=pc, qc=2)
            self.assertTrue(c['strict_separation'])
            self.assertEqual(c['contradiction_status'], A.UNEXCLUDED)

    def test_staggered_interior_crossing_is_not_missed(self):
        c = comparison(pc=(7, 9, 7), pr=(8, 8, 8), ct=(0, 40, 100), rt=(0, 70, 100))
        self.assertEqual([k['elapsed_ms'] for k in c['union_knots']], [0, 40, 70, 100])
        self.assertEqual(c['dP_min_bar'], -1)
        self.assertEqual(c['dP_max_bar'], 1)
        self.assertEqual(c['pressure_class'], A.CROSSING)
        self.assertEqual(c['contradiction_status'], A.UNEXCLUDED)
        self.assertEqual(c['union_knots'][0]['dP_bar'], 1)
        self.assertEqual(c['union_knots'][-1]['dP_bar'], 1)
        self.assertEqual(c['min_knot_indices'], [1])
        self.assertIsNone(c['robustness']['ordered_margin_bar'])

    def test_no_pressure_equivalence_tolerance_or_quantization(self):
        tiny = Q(1, 10**40)
        c = comparison(pc=(8-tiny, 8+tiny, 8-tiny))
        self.assertEqual(c['pressure_class'], A.CROSSING)
        self.assertEqual(c['dP_min_bar'], -tiny)
        self.assertEqual(c['contradiction_status'], A.UNEXCLUDED)
        c = comparison(pc=(8-tiny,)*3)
        self.assertEqual(c['pressure_class'], A.LOWER)
        self.assertEqual(c['contradiction_status'], A.EXCLUDED)

    def test_unequal_durations_unsupported_exactly(self):
        c = comparison(ct=(0, 50, 101))
        self.assertEqual(c['pressure_class'], A.UNSUPPORTED)
        self.assertEqual(c['failure_reason'], 'UNEQUAL_INTERVAL_DURATIONS')
        self.assertIsNone(c['delta_q_g_s'])

    def test_gap_boundary_discontinuity_extrapolation(self):
        o, _, _ = pair()
        for a, b, bounds in [(10, 1010, (0, 5)), (-1, 50, (0, 2)), (0, 101, (0, 5)), (10, 90, (1, 2))]:
            with self.subTest(a=a, b=b, bounds=bounds):
                v = o.interval('bad', a, b, bounds)
                self.assertFalse(v['supported'])
                self.assertIsNotNone(v['failure_reason'])
        o.blocked_edges.add(0)
        self.assertFalse(o.interval('bad', 0, 100, (0, 2))['supported'])
        data = [dict(t=t, p2=800, m=Q(t, 1000)) for t in (0, 95, 190)]
        self.assertTrue(A.Observer(data).interval('ok', 0, 190, (0, 2))['supported'])
        data[-1]['t'] = 191
        self.assertFalse(A.Observer(data).interval('bad', 0, 191, (0, 2))['supported'])

    def test_missing_nonfinite_and_nonincreasing_original_rows(self):
        o, _, _ = pair()
        for field in ('t', 'm', 'p2'):
            for invalid in (None, float('nan'), float('inf')):
                rows = copy.deepcopy(o.rows)
                rows[1][field] = invalid
                v = A.Observer(rows).interval('bad', 0, 100, (0, 2))
                self.assertFalse(v['supported'])
        for t in (0, -1):
            rows = copy.deepcopy(o.rows); rows[1]['t'] = t
            self.assertFalse(A.Observer(rows).interval('bad', 0, 100, (0, 2))['supported'])
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'raw.txt'
            p.write_text('{"t":0,"p2":800,"m":0}\ninvalid\n{"t":100,"p2":800,"m":1}\n')
            rows = A.parse(p)
            self.assertEqual(len(rows), 3)
            self.assertFalse(A.Observer(rows).interval('bad', 0, 100, (0, 2))['supported'])

    def test_units_line_pressure_original_clock_exact_decimal(self):
        o, c, r = pair()
        self.assertEqual(c['start_ms'], 1000)
        self.assertEqual(c['duration_s'], Q(1, 10))
        self.assertEqual(c['rate_g_s'], 3)
        self.assertEqual(c['pressure_endpoints'][0]['value'], 7)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'raw.txt'
            p.write_text('{"t":126,"p2":800.00000000000000000001,"m":0.1234567890123456789}\n')
            row = A.parse(p)[0]
            self.assertEqual(row['p2'], Q('800.00000000000000000001'))
            self.assertEqual(row['m'], Q('0.1234567890123456789'))
        for row in o.rows:
            row['p1'] = None
        self.assertEqual(A.compare(o, c, r, 'test')['dP_min_bar'], 1)

    def test_pressure_at_boundary_preserves_weak_order(self):
        c = comparison()
        margin = c['robustness']['ordered_margin_bar']
        ds = [v['dP_bar']-margin for v in c['union_knots']]
        self.assertGreaterEqual(min(ds), 0)
        self.assertEqual(A.pressure_class(min(ds), max(ds)), A.IDENTICAL)
        self.assertEqual(c['robustness']['equal_per_trajectory_pressure_boundary_bar'], margin/2)
        self.assertLess(c['dP_min_bar']-(margin+Q(1, 100000)), 0)

    def test_delivery_at_boundary_can_remove_contradiction(self):
        for kwargs in ({}, dict(pc=(9, 9, 9), qc=1)):
            c = comparison(**kwargs)
            limit = c['robustness']['adverse_rate_boundary_g_s']
            direction = 1 if c['delta_q_g_s'] > 0 else -1
            self.assertTrue(A.contradiction(c['pressure_class'], c['delta_q_g_s']-direction*limit/2))
            self.assertFalse(A.contradiction(c['pressure_class'], c['delta_q_g_s']-direction*limit))
            self.assertEqual(c['robustness']['mass_endpoint_eta_critical_g'], limit*c['duration_s']/4)

    def test_shared_raw_samples_cancel_and_reinforce(self):
        o, c, r = pair()
        self.assertEqual(A.mass_coefficients(c, c), {})
        # Adjacent intervals share a mass endpoint with two negative contributions.
        rows = [dict(t=t, m=Q(t*t, 1000), p2=800) for t in (0, 50, 100)]
        o = A.Observer(rows)
        r = o.interval('R', 0, 50, (0, 2))
        c = o.interval('C', 50, 100, (0, 2))
        coeff = A.mass_coefficients(c, r)
        self.assertEqual(coeff, {0: Q(20), 1: Q(-40), 2: Q(20)})
        self.assertEqual(sum(map(abs, coeff.values())), 4/c['duration_s'])
        # Four interpolated endpoints on the same original edge cancel fully.
        r = o.interval('R', 0, 20, (0, 2))
        c = o.interval('C', 10, 30, (0, 2))
        out = A.compare(o, c, r, 'overlap')
        self.assertEqual(out['robustness']['raw_sample_l1_per_s'], 0)
        self.assertEqual(out['robustness']['generic_bound'], 'CONSERVATIVE')

    def test_raw_error_box_attains_norm_without_independence(self):
        o, c, r = pair(ct=(5, 50, 95), rt=(5, 50, 95))
        coeff = A.mass_coefficients(c, r)
        eta = Q(1, 100)
        errors = {i: eta if w > 0 else -eta for i, w in coeff.items()}
        self.assertEqual(sum(coeff[i]*errors[i] for i in coeff), eta*sum(map(abs, coeff.values())))
        self.assertEqual(sum(coeff.values()), 0)  # Common additive mass offset.

    def test_reporting_duplicates_and_complete_family(self):
        family = list(A.family())
        self.assertEqual(len(family), 30)
        self.assertEqual(len({r['comparison_id'] for r in family}), 27)
        by_id = {r['reporting_id']: r for r in family}
        dup = [r for r in family if r['duplicate_of']]
        self.assertEqual(len(dup), 3)
        for row in dup:
            self.assertEqual(row['comparison_id'], by_id[row['duplicate_of']]['comparison_id'])

    def test_authentication_failure_retains_all_rows(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(A.OLD, 'authenticate', side_effect=FileNotFoundError):
            result = A.produce(Path(tmp)/'missing', Path(tmp)/'out')
            self.assertEqual(result['status'], A.UNSUPPORTED)
            self.assertEqual(result['reporting_rows'], 30)
            self.assertEqual(result['unique_comparisons'], 27)
            self.assertEqual(result['unique_contradictions'], [])
            self.assertTrue(all(c['failure_reason'] for c in result['comparisons']))

    def test_retained_artifact_witnesses_and_coefficients(self):
        result = json.loads((BUNDLE/'RESULT.json').read_text())
        witnesses = json.loads((BUNDLE/'PRESSURE_ORDER_WITNESSES.json').read_text())
        self.assertEqual(len(witnesses['intervals']), 18)
        self.assertEqual(len(result['retained_interval_reconciliation']), 18)
        self.assertLess(float(Q(result['max_abs_rate_arithmetic_discrepancy_g_s'])), 1e-12)
        samples = witnesses['samples']
        comparisons = {c['comparison_id']: c for c in result['comparisons']}
        for w in witnesses['comparisons']:
            c = comparisons[w['comparison_id']]
            knots = w['union_knots']
            ds = [Q(k['dP_bar']) for k in knots]
            self.assertEqual(min(ds), Q(c['dP_min_bar']))
            self.assertEqual(max(ds), Q(c['dP_max_bar']))
            for k in knots:
                for side in ('candidate', 'reference'):
                    p = k[side]
                    value = sum(Q(samples[str(p[s+'_index'])]['pressure_bar'])*Q(p[s+'_weight']) for s in ('left', 'right'))
                    self.assertEqual(value, Q(p['value']))
            coeff = c['robustness']['raw_sample_coefficients_per_s']
            self.assertEqual(sum(Q(v)*Q(samples[i]['mass_g']) for i, v in coeff.items()), Q(c['delta_q_g_s']))
        self.assertEqual(result['physical_puck_count'], 1)
        self.assertEqual(result['duplicate_rows'], 3)
        self.assertEqual(len(result['unique_contradictions']), 6)

    def test_manifest_bindings(self):
        manifest = json.loads((BUNDLE/'SOURCE_MANIFEST.json').read_text())
        self.assertEqual(manifest['implementation_sha256'], A.OLD.sha256(Path(A.__file__)))
        self.assertEqual(manifest['plan_sha256'], A.OLD.sha256(BUNDLE/'PLAN.md'))
        for name, digest in manifest['retained_bundle_sha256'].items():
            self.assertEqual(digest, A.OLD.sha256(A.RETAINED/name))


if __name__ == '__main__':
    unittest.main()
