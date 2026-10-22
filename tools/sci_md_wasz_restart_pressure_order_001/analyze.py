#!/usr/bin/env python3
"""Exact recorded-interpolant order test; offline, one exposed physical puck.

Fractions are authoritative. No upstream processing code or fitted F is used.
The retained observer is reused for source authentication/constants only; this
small exact observer implements the same support contract, reconciled below.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import csv
from fractions import Fraction as Q
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OLD_PATH = ROOT / 'tools/sci_md_wasz_restart_response_001/analyze.py'
SPEC = importlib.util.spec_from_file_location('retained_restart', OLD_PATH)
OLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OLD)
RETAINED = ROOT / 'docs/analysis/sci_md_wasz_restart_response_001'
BUNDLE = ROOT / 'docs/analysis/sci_md_wasz_restart_pressure_order_001'
TASK = 'SCI-MD-WASZ-RESTART-PRESSURE-ORDER-001'
BASE = 'aace2cc6b6c2a393d2dbfb0274104192ca6c7203'
BASE_TREE = 'cb713f8229075fe4f3f1e05d1eca77868e5692ae'
PW = 'd4eb54ce4bd0eb21a0968d3c37f43ad4ef8ccd16'
LOWER, HIGHER = 'CANDIDATE_WEAKLY_LOWER', 'CANDIDATE_WEAKLY_HIGHER'
IDENTICAL, CROSSING = 'IDENTICAL_PRESSURE', 'CROSSING'
UNSUPPORTED = 'UNSUPPORTED'
EXCLUDED = 'CONTRADICTS_COMMON_NONDECREASING_RESPONSE'
UNEXCLUDED = 'NOT_EXCLUDED_BY_PAIRWISE_ORDER_TEST'
Unsupported = OLD.Unsupported
CLASSES = (LOWER, HIGHER, IDENTICAL, CROSSING, UNSUPPORTED, 'NUMERICALLY_UNRESOLVED')


def exact(x):
    return isinstance(x, (int, Q)) and not isinstance(x, bool)


def encode(x):
    if isinstance(x, Q):
        return str(x)
    if isinstance(x, dict):
        return {str(k): encode(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [encode(v) for v in x]
    return x


def dump(path, obj):
    OLD.dump(path, encode(obj))


def parse(path):
    rows = []
    for line in path.read_text().splitlines():
        try:
            r = json.loads(line, parse_float=Q, parse_constant=lambda _: None)
            rows.append(r if isinstance(r, dict) else {})
        except ValueError:
            rows.append({})  # Keep the invalid acquisition's original index.
    return rows


class Observer:
    def __init__(self, rows, blocked_edges=(), max_gap_ms=95):
        self.rows = rows
        self.times = [r.get('t') for r in rows]
        self.ordered = (bool(rows) and all(exact(t) for t in self.times)
                        and all(a < b for a, b in zip(self.times, self.times[1:])))
        self.blocked_edges = set(blocked_edges)
        self.max_gap_ms = max_gap_ms

    def edge(self, i, field):
        a, b = self.rows[i:i+2]
        if i in self.blocked_edges:
            raise Unsupported(f'DOCUMENTED_DISCONTINUITY_EDGE_{i}')
        if any(not exact(r.get(f)) for r in (a, b) for f in ('t', field)):
            raise Unsupported(f'MISSING_OR_NONFINITE_SUPPORT_EDGE_{i}')
        if b['t'] <= a['t']:
            raise Unsupported(f'NONINCREASING_CLOCK_EDGE_{i}')
        if b['t'] - a['t'] > self.max_gap_ms:
            raise Unsupported(f'UNSUPPORTED_ACQUISITION_GAP_EDGE_{i}')

    def endpoint(self, time_ms, field):
        if not self.ordered:
            raise Unsupported('MISSING_OR_NONINCREASING_ORIGINAL_CLOCK')
        k = bisect.bisect_left(self.times, time_ms)
        if k < len(self.times) and self.times[k] == time_ms:
            left = right = k
        else:
            left, right = k-1, k
            if left < 0 or right >= len(self.times):
                raise Unsupported('ENDPOINT_OUTSIDE_ORIGINAL_SUPPORT')
            self.edge(left, field)
        if not exact(self.rows[left].get(field)):
            raise Unsupported(f'MISSING_OR_NONFINITE_{field}_AT_{left}')
        weight = Q(0) if left == right else Q(time_ms-self.times[left], self.times[right]-self.times[left])
        factor = Q(1, 100) if field == 'p2' else Q(1)
        v0, v1 = self.rows[left][field], self.rows[right][field]
        return dict(time_ms=time_ms, left_index=left, right_index=right,
                    left_weight=1-weight, right_weight=weight, exact_sample=left == right,
                    value=(v0*(1-weight)+v1*weight)*factor)

    def support(self, a, b, field, bounds):
        if b <= a:
            raise Unsupported('NONPOSITIVE_INTERVAL')
        ea, eb = self.endpoint(a, field), self.endpoint(b, field)
        if ea['left_index'] < bounds[0] or eb['right_index'] > bounds[1]:
            raise Unsupported('ENDPOINT_BRACKET_CROSSES_EPISODE_BOUNDARY')
        for i in range(ea['left_index'], eb['right_index']):
            self.edge(i, field)
        return ea, eb

    def interval(self, identity, a, b, bounds, eligible=True, reason=None):
        out = dict(interval_id=identity, physical_puck_id=OLD.PUCK,
                   start_ms=a, end_ms=b, duration_s=Q(b-a, 1000), supported=False,
                   failure_reason=None, rate_g_s=None, mass_endpoints=None,
                   pressure_endpoints=None, pressure_knots_ms=None)
        try:
            if not eligible:
                raise Unsupported(reason or 'RETAINED_INELIGIBLE')
            ma, mb = self.support(a, b, 'm', bounds)
            pa, pb = self.support(a, b, 'p2', bounds)
            out.update(supported=True, rate_g_s=(mb['value']-ma['value'])/out['duration_s'],
                       mass_endpoints=[ma, mb], pressure_endpoints=[pa, pb],
                       pressure_knots_ms=[0] + [t-a for t in self.times if a < t < b] + [b-a])
        except Unsupported as error:
            out['failure_reason'] = str(error)
        return out


def pressure_class(lo, hi):
    if lo == hi == 0:
        return IDENTICAL
    if lo >= 0 and hi > 0:
        return LOWER
    if hi <= 0 and lo < 0:
        return HIGHER
    if lo < 0 < hi:
        return CROSSING
    raise ValueError('Invalid extrema')


def contradiction(cls, dq):
    return ((cls == LOWER and dq > 0) or (cls == HIGHER and dq < 0)
            or (cls == IDENTICAL and dq != 0))


def mass_coefficients(candidate, reference):
    """Aggregate before taking absolute values, even for shared endpoints."""
    d = candidate['duration_s']
    coeff = collections.defaultdict(Q)
    for interval, sign in ((candidate, 1), (reference, -1)):
        for endpoint, direction in zip(interval['mass_endpoints'], (-1, 1)):
            for side in ('left', 'right'):
                coeff[endpoint[side+'_index']] += sign*direction*endpoint[side+'_weight']/d
    return {i: c for i, c in sorted(coeff.items()) if c}


def robustness(cls, lo, hi, dq, duration, coeff):
    contrary = contradiction(cls, dq)
    margin = lo if cls == LOWER else -hi if cls == HIGHER else Q(0) if cls == IDENTICAL else None
    norm = sum(map(abs, coeff.values()), Q(0))
    magnitude = abs(dq) if contrary else None
    return dict(ordered_margin_bar=margin,
                equal_per_trajectory_pressure_boundary_bar=margin/2 if margin is not None else None,
                pressure_boundary_reason=None if margin is not None else 'CROSSING_NO_ORDER_RESERVE',
                pressure_rule='E_P<mP: strict; E_P=mP: weak; E_P>mP: certificate can fail; not an F existence test',
                adverse_rate_boundary_g_s=magnitude,
                mass_endpoint_eta_critical_g=duration*magnitude/4 if contrary else None,
                raw_sample_coefficients_per_s=coeff, raw_sample_l1_per_s=norm,
                generic_endpoint_l1_per_s=4/duration,
                generic_bound='ATTAINED' if norm == 4/duration else 'CONSERVATIVE',
                raw_sample_eta_critical_g=magnitude/norm if contrary and norm else None,
                delivery_boundary_reason=None if contrary else 'NO_CONTRARY_DELIVERY_SIGN',
                assumptions='fixed timing/interpolation; separately bounded errors; no independence required')


def compare(observer, candidate, reference, identity):
    out = dict(comparison_id=identity, candidate_interval_id=candidate['interval_id'],
               reference_interval_id=reference['interval_id'], physical_puck_id=OLD.PUCK,
               candidate_start_ms=candidate['start_ms'], candidate_end_ms=candidate['end_ms'],
               reference_start_ms=reference['start_ms'], reference_end_ms=reference['end_ms'],
               duration_s=candidate['duration_s'], candidate_rate_g_s=candidate['rate_g_s'],
               reference_rate_g_s=reference['rate_g_s'], delta_q_g_s=None,
               pressure_class=UNSUPPORTED, contradiction_status=UNSUPPORTED,
               strict_separation=None, failure_reason=None, dP_min_bar=None, dP_max_bar=None,
               union_knots=None, segments=None, min_knot_indices=None, max_knot_indices=None,
               robustness=None)
    try:
        if not candidate['supported'] or not reference['supported']:
            raise Unsupported(candidate['failure_reason'] or reference['failure_reason'])
        if candidate['duration_s'] != reference['duration_s']:
            raise Unsupported('UNEQUAL_INTERVAL_DURATIONS')
        grid = sorted(set(candidate['pressure_knots_ms']) | set(reference['pressure_knots_ms']))
        knots = []
        for s in grid:
            pc = observer.endpoint(candidate['start_ms']+s, 'p2')
            pr = observer.endpoint(reference['start_ms']+s, 'p2')
            knots.append(dict(elapsed_ms=s, candidate=pc, reference=pr, dP_bar=pr['value']-pc['value']))
        values = [k['dP_bar'] for k in knots]
        lo, hi = min(values), max(values)
        cls = pressure_class(lo, hi)
        dq = candidate['rate_g_s']-reference['rate_g_s']
        segments = []
        for i, (u, v) in enumerate(zip(values, values[1:])):
            segments.append(dict(start_knot=i, end_knot=i+1, min_bar=min(u, v), max_bar=max(u, v),
                                 minimum_at='WHOLE_SEGMENT' if u == v else i if u < v else i+1,
                                 maximum_at='WHOLE_SEGMENT' if u == v else i if u > v else i+1))
        coeff = mass_coefficients(candidate, reference)
        # A separate identity check protects endpoint sign/coefficient mistakes.
        if sum((c*observer.rows[i]['m'] for i, c in coeff.items()), Q(0)) != dq:
            raise ValueError('RAW_SAMPLE_COEFFICIENT_IDENTITY_FAILURE')
        out.update(delta_q_g_s=dq, pressure_class=cls, strict_separation=lo > 0 or hi < 0,
                   contradiction_status=EXCLUDED if contradiction(cls, dq) else UNEXCLUDED,
                   dP_min_bar=lo, dP_max_bar=hi, union_knots=knots, segments=segments,
                   min_knot_indices=[i for i, v in enumerate(values) if v == lo],
                   max_knot_indices=[i for i, v in enumerate(values) if v == hi],
                   robustness=robustness(cls, lo, hi, dq, candidate['duration_s'], coeff))
    except Unsupported as error:
        out['failure_reason'] = str(error)
    return out


def family():
    for design, _, _ in OLD.DESIGNS:
        for fam in ('A', 'B'):
            for ep in range(1, 6):
                ref = 0 if fam == 'A' else ep-1
                yield dict(reporting_id=f'{design}_{fam}_E{ep}_E{ref}', design=design, family=fam,
                           candidate_episode=f'E{ep}', reference_episode=f'E{ref}',
                           comparison_id=f'{design}_E{ep}_E{ref}',
                           duplicate_of=f'{design}_A_E1_E0' if fam == 'B' and ep == 1 else None)


def reconcile(rows, retained):
    """Reuse retained eligibility; independently verify episodes and all 18 windows."""
    if not Observer(rows).ordered:
        raise Unsupported('MISSING_OR_NONINCREASING_ORIGINAL_CLOCK')
    if any(not exact(r.get('p2')) for r in rows):
        raise Unsupported('MISSING_OR_NONFINITE_EPISODE_PRESSURE')
    states = [r['p2'] > 550 for r in rows]
    groups = []
    for i, active in enumerate(states):
        if active and (i == 0 or not states[i-1]):
            groups.append([i, i])
        elif active:
            groups[-1][1] = i
    eps = [e for e in retained['episodes'] if e['state'] == 'ACTIVE']
    expected = [(Q(str(a))*1000, Q(str(b))*1000) for a, b in OLD.EXPECTED_SPANS]
    if len(groups) != 6 or [(rows[a]['t'], rows[b]['t']) for a, b in groups] != expected:
        raise Unsupported('RETAINED_EPISODE_BOUNDARY_MISMATCH')
    for (a, b), e in zip(groups, eps):
        if (a, b) != (e['first_index'], e['last_index']):
            raise Unsupported('RETAINED_EPISODE_INDEX_MISMATCH')
    with (RETAINED/'EPISODES.csv').open() as f:
        csv_eps = [r for r in csv.DictReader(f) if r['state'] == 'ACTIVE']
    if [(int(e['first_index']), int(e['last_index'])) for e in csv_eps] != [tuple(g) for g in groups]:
        raise Unsupported('RETAINED_EPISODE_CSV_MISMATCH')
    blocked = retained['acquisition_audit']['documented_discontinuity_edges']
    observer = Observer(rows, blocked_edges=blocked)
    old_intervals = {r['interval_id']: r for r in retained['intervals'] if r['kind'] == 'later'}
    with (RETAINED/'INTERVALS.csv').open() as f:
        csv_intervals = {r['interval_id']: r for r in csv.DictReader(f) if r['kind'] == 'later'}
    if len(old_intervals) != 18 or set(csv_intervals) != set(old_intervals):
        raise Unsupported('RETAINED_INTERVAL_FAMILY_MISMATCH')
    elig = {(e['design'], e['episode_id']): e for e in retained['eligibility']}
    intervals, reconciliation = {}, []
    for design, d, g in OLD.DESIGNS:
        for n, (first, last) in enumerate(groups):
            eid = f'E{n}'
            identity = f'{design}_{eid}_later'
            old = old_intervals[identity]
            tab = csv_intervals[identity]
            end = rows[last]['t']-g*1000
            start = end-d*1000
            e = elig.get((design, eid), {'eligible': True, 'unavailable_reason': None})
            v = observer.interval(identity, start, end, (first, last), e['eligible'], e['unavailable_reason'])
            v.update(design=design, episode_id=eid, episode_bounds_indices=[first, last])
            if (Q(str(old['start_s']))*1000 != start or Q(str(old['end_s']))*1000 != end
                    or Q(tab['start_s'])*1000 != start or Q(tab['end_s'])*1000 != end
                    or old['supported'] != v['supported'] or (tab['supported'] == 'True') != v['supported']):
                raise Unsupported(f'RETAINED_INTERVAL_SUPPORT_MISMATCH:{identity}')
            diffs = []
            if v['supported'] and Q(tab['rate_g_s']) != Q(str(old['rate_g_s'])):
                raise Unsupported(f'RETAINED_CSV_RATE_MISMATCH:{identity}')
            if v['supported']:
                for field, endpoints in [('m', v['mass_endpoints']), ('p2', v['pressure_endpoints'])]:
                    for k, endpoint in enumerate(endpoints):
                        old_ep = old['mass_start' if k == 0 else 'mass_end'] if field == 'm' else old['pressure']['start' if k == 0 else 'end']
                        csv_ep = json.loads(tab['mass_start' if k == 0 else 'mass_end']) if field == 'm' else json.loads(tab['pressure'])['start' if k == 0 else 'end']
                        for saved in (old_ep, csv_ep):
                            if any(endpoint[x] != saved[x] for x in ['left_index', 'right_index', 'exact_sample']):
                                raise Unsupported(f'RETAINED_ENDPOINT_BRACKET_MISMATCH:{identity}')
                        diffs.append(dict(field=field, endpoint=k,
                            value_exact_minus_old_serialized=endpoint['value']-Q(str(old_ep['value'])),
                            weight_exact_minus_old_serialized=endpoint['right_weight']-Q(str(old_ep['interpolation_fraction']))))
            reconciliation.append(dict(interval_id=identity, supported=v['supported'],
                exact_rate_g_s=v['rate_g_s'], retained_rate_g_s=old['rate_g_s'],
                exact_minus_old_serialized_g_s=v['rate_g_s']-Q(str(old['rate_g_s'])) if v['supported'] else None,
                endpoint_arithmetic_differences=diffs, support_and_bracket_identity='MATCH'))
            intervals[identity] = v
    return observer, intervals, reconciliation, groups


def produce(source_root, output):
    output.mkdir(parents=True, exist_ok=True)
    retained_manifest = json.loads((RETAINED/'SOURCE_MANIFEST.json').read_text())
    manifest = dict(task_id=TASK, base_commit=BASE, base_tree=BASE_TREE,
                    puckworks_read_only_research_commit=PW, production_puckworks_lock=OLD.PRODUCTION,
                    physical_puck_id=OLD.PUCK, original_source=None,
                    attribution=retained_manifest['attribution'], rights=retained_manifest['rights'],
                    deposit=retained_manifest['deposit'], fields=retained_manifest['fields'],
                    acquisition='reused external Git cache; no network in producer',
                    raw_payloads='external; locators relative to --source-root',
                    full_logs='external task evidence root; relative locators/hashes in REVIEW.md',
                    inspected='restart acquisition and plotting script (lineage only); retained bundle; PLAN preflight',
                    implementation_sha256=OLD.sha256(Path(__file__)),
                    retained_helper_sha256=OLD.sha256(OLD_PATH), plan_sha256=OLD.sha256(BUNDLE/'PLAN.md'),
                    retained_bundle_sha256={p.name: OLD.sha256(p) for p in sorted(RETAINED.iterdir()) if p.is_file()})
    failure = None
    try:
        auth = OLD.authenticate(source_root)
        manifest['original_source'] = auth
        for name in (OLD.RAW, OLD.SCRIPT):
            if any(auth['files'][name][key] != retained_manifest['original_source']['files'][name][key]
                   for key in ('bytes', 'git_blob_id', 'sha256', 'pinned_tree_blob_id')):
                auth['authenticated'] = False
        if not auth['authenticated']:
            raise Unsupported('SOURCE_AUTHENTICATION_MISMATCH')
    except (OSError, subprocess.CalledProcessError, Unsupported) as error:
        failure = 'SOURCE_AUTHENTICATION_UNSUPPORTED:' + type(error).__name__
        if isinstance(error, Unsupported):
            failure += ':' + str(error)
    dump(output/'SOURCE_MANIFEST.json', manifest)
    retained = json.loads((RETAINED/'RESULT.json').read_text())
    rows, intervals, reconciliation, groups = [], {}, [], []
    if not failure:
        rows = parse(source_root/OLD.RAW)
        try:
            observer, intervals, reconciliation, groups = reconcile(rows, retained)
        except Unsupported as error:
            failure = str(error)
    unique, reporting = {}, []
    for f in family():
        identity = f['comparison_id']
        if identity not in unique:
            c_id, r_id = (f"{f['design']}_{f[x]}_later" for x in ('candidate_episode', 'reference_episode'))
            if failure:
                c = dict(comparison_id=identity, candidate_interval_id=c_id, reference_interval_id=r_id,
                         physical_puck_id=OLD.PUCK, pressure_class=UNSUPPORTED,
                         contradiction_status=UNSUPPORTED, failure_reason=failure)
            else:
                c = compare(observer, intervals[c_id], intervals[r_id], identity)
            c.update(design=f['design'], family_membership=[])
            unique[identity] = c
        unique[identity]['family_membership'].append(f['family'])
        c = unique[identity]
        reporting.append(dict(f, physical_puck_id=OLD.PUCK,
                              **{k: v for k, v in c.items() if k not in ('comparison_id', 'design', 'physical_puck_id', 'family_membership', 'union_knots', 'segments', 'min_knot_indices', 'max_knot_indices', 'robustness')},
                              **{k: c.get('robustness', {}).get(k) if c.get('robustness') else None for k in (
                                  'ordered_margin_bar', 'equal_per_trajectory_pressure_boundary_bar',
                                  'adverse_rate_boundary_g_s', 'mass_endpoint_eta_critical_g',
                                  'raw_sample_l1_per_s', 'raw_sample_eta_critical_g', 'generic_bound')}))
    counts = {fam: {cls: sum(r['family'] == fam and r['pressure_class'] == cls for r in reporting)
                    for cls in CLASSES} for fam in ('A', 'B')}
    excluded = [c['comparison_id'] for c in unique.values() if c['contradiction_status'] == EXCLUDED]
    result = dict(task_id=TASK, declaration='NO_GOVERNING_PHYSICS_CHANGE', governance_class='G1',
                  evidence_class=['RESEARCH_ONLY', 'RETROSPECTIVE', 'SOURCE_INTERNAL', 'TARGET_EXPOSED', 'NONSCORING'],
                  physical_validation='NOT_ESTABLISHED', physical_puck_count=1,
                  status=EXCLUDED if excluded else UNSUPPORTED if failure else UNEXCLUDED,
                  failure_reason=failure, reporting_rows=len(reporting), unique_comparisons=len(unique),
                  duplicate_rows=sum(r['duplicate_of'] is not None for r in reporting),
                  family_pressure_counts=counts, unique_contradictions=excluded,
                  reporting_contradictions=sum(r['contradiction_status'] == EXCLUDED for r in reporting),
                  arithmetic='exact source-decimal Fraction; rational strings; no tolerance for signs',
                  units=dict(time_ms='ms original clock', duration_s='s', pressure='bar line p2/100', mass='g', rate='g/s'),
                  physical_applicability='joint response/interpolant/observation assumptions; measurement uncertainty unestablished',
                  retained_interval_reconciliation=reconciliation,
                  max_abs_rate_arithmetic_discrepancy_g_s=max((abs(r['exact_minus_old_serialized_g_s']) for r in reconciliation if r['supported']), default=None),
                  comparisons=[{k: v for k, v in c.items() if k not in ('union_knots', 'segments', 'min_knot_indices', 'max_knot_indices')} for c in unique.values()])
    # Retain only original support samples used by the required intervals, not the raw payload.
    used = set()
    for v in intervals.values():
        if v['supported']:
            used.update(range(v['mass_endpoints'][0]['left_index'], v['mass_endpoints'][1]['right_index']+1))
    samples = {i: dict(time_ms=rows[i]['t'], p2_original=rows[i]['p2'], pressure_bar=Q(rows[i]['p2'])/100, mass_g=rows[i]['m']) for i in sorted(used)}
    witnesses = dict(task_id=TASK,
                    encoding='all rational strings exact; indices zero-based original acquisition; sample table supplies bracket times/values; weights explicit',
                    units=dict(elapsed_ms='ms', pressure_values='bar', mass_values='g', coefficients='1/s'),
                    samples=samples, intervals=list(intervals.values()),
                    active_episodes=[dict(episode_id=f'E{i}', first_index=a, last_index=b, start_ms=rows[a]['t'], end_ms=rows[b]['t']) for i, (a, b) in enumerate(groups)],
                    comparisons=[{k: v for k, v in c.items() if k in ('comparison_id', 'union_knots', 'segments', 'min_knot_indices', 'max_knot_indices', 'dP_min_bar', 'dP_max_bar', 'failure_reason')} for c in unique.values()])
    dump(output/'RESULT.json', result)
    dump(output/'PRESSURE_ORDER_WITNESSES.json', witnesses)
    OLD.csv_write(output/'COMPARISONS.csv', [encode(r) for r in reporting])
    figure(output/'PRESSURE_ORDER.svg', list(unique.values()))
    return result


def figure(path, comparisons):
    """Deterministic SVG; exact values are in tables, floats only set pixels."""
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1140" height="740" viewBox="0 0 1140 740">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="sans-serif" fill="#182b3a" font-size="13">',
             '<text x="35" y="30" font-size="20">Recorded/interpolant pressure order and delivery · one physical puck</text>',
             '<text x="35" y="53">All 27 unique comparisons; A/B E1/E0 duplicates counted once. No physical error bars inferred.</text>']
    def text(x, y, s, size=13):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}">{s}</text>')
    def line(x1, y1, x2, y2, color='#ccd4da', width=1):
        parts.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-width="{width}"/>')
    def dot(x, y, color):
        parts.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="3" fill="{color}"/>')
    def xp(p): return 180+(float(p)+.2)/.4*350
    def xq(q): return 620+float(q)/3*205
    text(180, 82, 'dP range [min,max], bar (R−C)')
    text(620, 82, 'delta q, g/s (C−R)')
    for v in (-.2, -.1, 0, .1, .2):
        line(xp(v), 94, xp(v), 625); text(xp(v)-12, 649, f'{v:g}')
    for v in (0, 1, 2, 3):
        line(xq(v), 94, xq(v), 625); text(xq(v)-4, 649, str(v))
    for i, c in enumerate(comparisons):
        y = 104+i*19
        label = c['comparison_id'].replace('SENSITIVITY_', 'S').replace('PRIMARY', 'P')
        text(20, y+4, label, 12)
        if c['pressure_class'] == UNSUPPORTED:
            text(185, y+4, 'UNSUPPORTED'); continue
        color = '#bd3e25' if c['contradiction_status'] == EXCLUDED else '#2b607d' if c['pressure_class'] != CROSSING else '#8b949b'
        line(xp(c['dP_min_bar']), y, xp(c['dP_max_bar']), y, color, 3)
        dot(xq(c['delta_q_g_s']), y, color)
    text(855, 100, 'E5/E4 detail', 17)
    text(855, 123, 'mP (bar) / delta q (g/s)', 12)
    for j, c in enumerate(c for c in comparisons if c['comparison_id'].endswith('_E5_E4') and c.get('robustness')):
        y = 155+j*105
        r = c['robustness']
        text(855, y, c['design'], 12)
        text(855, y+20, f"{float(r['ordered_margin_bar']):.9f} / +{float(c['delta_q_g_s']):.9f}", 12)
        text(855, y+40, f"epsilon P boundary: {float(r['equal_per_trajectory_pressure_boundary_bar']):.9f} bar", 11)
        text(855, y+58, f"eta boundary: {float(r['mass_endpoint_eta_critical_g']):.9f} g", 11)
    text(855, 495, 'Red: nominal contradiction', 12)
    text(855, 515, 'Blue: ordered, unexcluded', 12)
    text(855, 535, 'Gray: crossing, unexcluded', 12)
    text(35, 687, 'Pressure error at mP retains weak order; adverse delivery correction at |delta q| can remove the contrary sign.')
    text(35, 710, 'Boundary values assume fixed timing/interpolation and separate worst-case error bounds; they are not known sensor accuracies.')
    parts.append('</g></svg>')
    path.write_text('\n'.join(parts)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    r = produce(args.source_root, args.output)
    print(json.dumps({k: r[k] for k in ('status', 'reporting_rows', 'unique_comparisons', 'unique_contradictions', 'family_pressure_counts')}))
    return 2 if r['status'] == UNSUPPORTED else 0


if __name__ == '__main__':
    raise SystemExit(main())
