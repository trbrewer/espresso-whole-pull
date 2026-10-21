#!/usr/bin/env python3
"""Independent, retrospective Waszkiewicz terminal-mass observer audit.

Data: Waszkiewicz et al. (2025), Zenodo 18046315, CC-BY-4.0.
Upstream GPLv3 software was inspected for behavior, not copied or imported.
This module neither fits a scientific model nor changes production behavior.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
from pathlib import Path

import numpy as np
from scipy.signal import savgol_filter

TASK = 'SCI-MD-WASZ-TERMINAL-MASS-ROBUSTNESS-001'
UPSTREAM = 'fbc33d3380a9c8cff2467bae70fec7137a6ed46f'
PW = '58075bbbce548e63d94106c96b918c1464221514'
BASE = 'f93095abd58b31476ec331f3aa8d68feb98df9b0'
BUNDLE = Path('docs/analysis/sci_md_wasz_terminal_mass_robustness_001')
WINDOWS = {'q10': 10, 'q5': 5, 'q20': 20}
OBSERVERS = ['historical_endpoint', *WINDOWS]
FIELDS = ['pressure__bar', 'mass__g', 'mass_flow_rate__g_per_s', 'basket_pressure__bar']
ALIAS = {'12-8-6_alt': '12-8-6'}
GRID = np.linspace(0.0, 100.0, 1000)
# Half a serialization unit plus floating arithmetic slack, NOT measurement error.
BREW_TOL = 0.5e-5 + 1e-10
PUBLISHED_TOL = 0.5e-6 + 1e-10


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path):
    with Path(path).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')


def write_csv(path, rows):
    with Path(path).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, separators=(',', ':'), allow_nan=False)
                             if isinstance(v, (list, dict)) else v for k, v in row.items()})


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args]).decode().strip()


def identities(root, revision, paths):
    """Authenticate actual bytes against pinned Git objects, including missing files."""
    result = {}
    for rel in sorted(paths):
        expected = subprocess.check_output(['git', '-C', str(root), 'show', f'{revision}:{rel}'])
        path = root / rel
        actual = sha(path) if path.is_file() else None
        digest = hashlib.sha256(expected).hexdigest()
        result[rel] = dict(sha256=actual, git_object_sha256=digest,
                           bytes=path.stat().st_size if path.is_file() else None,
                           authenticated=actual == digest)
    return result


def acquisition(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    a = np.asarray([[r.get('t', np.nan), r.get('p2', np.nan), r.get('m', np.nan)] for r in rows], dtype=float)
    if len(a) < 32:
        raise ValueError('TOO_FEW_ACQUISITIONS')
    complete = a
    if (not np.isfinite(a[-1, 0]) and not np.isfinite(a[-1, 2])
            and np.isfinite(a[-1, 1]) and 't' not in rows[-1] and 'm' not in rows[-1]):
        complete = a[:-1]  # incomplete final JSON record; preserve p2 in source median
    if not np.isfinite(complete).all() or not np.isfinite(a[:, 1]).all():
        raise ValueError('NONFINITE_ACQUISITION')
    if np.any(np.diff(complete[:, 0]) == 0):
        raise ValueError('DUPLICATE_TIMESTAMP')
    if np.any(np.diff(complete[:, 0]) < 0):
        raise ValueError('NONMONOTONIC_TIMESTAMP')
    return a


def alignment(a, filename):
    ref = float(np.median(a[:, 1]))
    rounded = float(np.round(ref / 100 / 0.5) * 0.5)
    before = rounded
    correction = 'NONE'
    if filename == '1-2.txt':
        rounded, correction = 1.0, '1-2.txt -> 1.0'
    if rounded == 1.5:
        rounded, correction = 2.0, 'rounded 1.5 -> 2.0'
    lower, upper = max(ref * .9, ref - 50), min(ref * 1.1, ref + 50)
    violation = (a[:, 1] < lower) | (a[:, 1] > upper)
    if not violation.any():
        raise ValueError('SOURCE_ALIGNMENT_GLOBAL_GUARD_FAILED')
    # pd.Series mask[500::-1].idxmax(): includes position 500. If every
    # searched entry is False, idxmax returns the FIRST REVERSED label.
    last_search = min(500, len(a) - 1)
    candidates = np.flatnonzero(violation[:last_search + 1])
    last = int(candidates[-1]) if len(candidates) else last_search
    start = last + 1
    if start >= len(a):
        raise ValueError('ALIGNMENT_START_OUTSIDE_RECORD')
    return dict(reference_median_p2_kpa=ref, rounded_before_correction_bar=before,
                reference_condition_bar=rounded, manual_correction=correction,
                tolerance_lower_kpa=lower, tolerance_upper_kpa=upper,
                reversed_search_first_label=last_search,
                searched_prefix_has_violation=bool(len(candidates)),
                alignment_violation_index=last, start_idx=start,
                time_origin_raw_ms=float(a[start, 0]))


def aligned(a, start):
    # Match source multiplication order (0.001 * integer-ms difference).
    complete = a[start:][np.isfinite(a[start:]).all(axis=1)]
    return 0.001 * (complete[:, 0] - a[start, 0]), complete[:, 1] / 100, complete[:, 2]


def endpoint_operator(t, mass):
    if len(t) < 31:
        raise ValueError('INSUFFICIENT_FILTER_SUPPORT')
    return savgol_filter(np.gradient(mass, t, edge_order=1), 31, 1, mode='interp')


def terminal_interval_kernel(t):
    # Only the last 32 mass samples can affect the truncated SG endpoint.
    support = t[-32:]
    dt = np.diff(support)
    basis = np.vstack([np.zeros(len(dt)), np.tril(np.ones((len(dt), len(dt))))])*np.r_[dt][None, :]
    weights = [float(endpoint_operator(support, basis[:, j])[-1]) for j in range(len(dt))]
    return dict(interval_left_times_s=support[:-1].tolist(), interval_right_times_s=support[1:].tolist(),
                interval_rate_weights=weights, minimum_weight=min(weights), maximum_weight=max(weights),
                negative_weight_count=sum(w < -1e-14 for w in weights), weight_sum=sum(weights))


def reconstruct(a, meta, calibration):
    t, p, m = aligned(a, meta['start_idx'])
    keep = t <= 100.0
    tt, pp, mm = t[keep], p[keep], m[keep]
    q = endpoint_operator(tt, mm)
    ca, cb, cc = calibration
    arrays = dict(zip(FIELDS, [pp, mm, q, pp - (ca*q*q + cb*q + cc)]))
    series = {k: np.interp(GRID, tt, v) for k, v in arrays.items()}
    n = len(tt)
    # Last SG output uses 31 derivative samples; first such derivative also
    # depends on the preceding mass sample. Record the actual support times.
    full_q = endpoint_operator(t, m)
    kernel = terminal_interval_kernel(tt)
    support = dict(retained_sample_count=n, last_retained_time_s=float(tt[-1]),
                   first_subsequent_time_s=float(t[n]) if n < len(t) else None,
                   endpoint_behavior='HOLD_LAST_RETAINED' if tt[-1] < 100 else 'EXACT_SAMPLE',
                   endpoint_left_time_s=float(tt[-1]), endpoint_right_time_s=None,
                   endpoint_hold_duration_s=float(100 - tt[-1]),
                   filter_mode='interp', gradient_edge_order=1,
                   interval_kernel_minimum_weight=kernel['minimum_weight'],
                   interval_kernel_maximum_weight=kernel['maximum_weight'],
                   interval_kernel_negative_count=kernel['negative_weight_count'],
                   interval_kernel_sum=kernel['weight_sum'],
                   filter_gradient_sample_count=31,
                   filter_gradient_first_time_s=float(tt[-31]),
                   filter_gradient_last_time_s=float(tt[-1]),
                   gradient_mass_support_first_time_s=float(tt[max(0, n-32)]),
                   gradient_mass_support_last_time_s=float(tt[-1]),
                   final_gradient_g_s=float(np.gradient(mm, tt)[-1]),
                   reconstructed_pressure_bar=float(series['pressure__bar'][-1]),
                   reconstructed_endpoint_g_s=float(series['mass_flow_rate__g_per_s'][-1]),
                   untruncated_filtered_at_100_g_s=float(np.interp(100, t, full_q)),
                   untruncated_minus_truncated_endpoint_g_s=float(np.interp(100, t, full_q)-q[-1]))
    return series, support


def bracket(t, m, when):
    """No holding or extrapolation; retain both actual observations."""
    if not np.isfinite(t).all() or not np.isfinite(m).all() or np.any(np.diff(t) <= 0):
        raise ValueError('INVALID_INTERPOLATION_ACQUISITION')
    pos = int(np.searchsorted(t, when))
    blank = dict(target_s=float(when), supported=False, reason='OUTSIDE_MEASURED_SUPPORT',
                 left_time_s=None, right_time_s=None, left_mass_g=None, right_mass_g=None,
                 width_s=None, fraction=None, exact=False, interpolated_mass_g=None)
    if pos < len(t) and t[pos] == when:
        left = right = pos
    elif pos == 0 or pos == len(t):
        return blank
    else:
        left, right = pos-1, pos
    width = float(t[right]-t[left])
    fraction = float((when-t[left])/width) if width else 0.0
    return dict(target_s=float(when), supported=True, reason='',
                left_time_s=float(t[left]), right_time_s=float(t[right]),
                left_mass_g=float(m[left]), right_mass_g=float(m[right]), width_s=width,
                fraction=fraction, exact=left == right,
                interpolated_mass_g=float(m[left]+fraction*(m[right]-m[left])))


def mass_windows(t, m):
    ends = {str(s): bracket(t, m, s) for s in (80, 90, 95, 100)}
    values, reasons = {}, {}
    for name, w in WINDOWS.items():
        start, end = ends[str(100-w)], ends['100']
        values[name] = ((end['interpolated_mass_g']-start['interpolated_mass_g'])/w
                        if start['supported'] and end['supported'] else None)
        reasons[name] = ';'.join(f'{x["target_s"]}:{x["reason"]}' for x in [start, end] if not x['supported'])
    return values, reasons, ends


def slope(x, y):
    if len(x) < 2 or any(v is None for v in y):
        return None
    xm, ym = sum(x)/len(x), sum(y)/len(y)
    return sum((a-xm)*(b-ym) for a, b in zip(x, y))/sum((a-xm)**2 for a in x)


def sign(v):
    return 'UNAVAILABLE' if v is None else 'POSITIVE' if v > 0 else 'NEGATIVE' if v < 0 else 'ZERO'


def numerical_zero(x, y):
    if any(v is None for v in y) or len(x) < 2:
        return None
    xm = sum(x)/len(x)
    return 64*np.finfo(float).eps*sum(abs((p-xm)*v) for p, v in zip(x, y))/sum((p-xm)**2 for p in x)


def summarize(brews, coordinates, observer, eligible=None, deleted=None):
    rows = []
    for condition, pressure in coordinates.items():
        group = [b for b in brews if b['condition_id'] == condition
                 and b['physical_unit_id'] != deleted
                 and (eligible is None or b['physical_unit_id'] in eligible)]
        available = [b for b in group if b[observer] is not None]
        v = [b[observer] for b in available]
        mean = sum(v)/len(v) if v else None
        sd = math.sqrt(sum((x-mean)**2 for x in v)/(len(v)-1)) if len(v) > 1 else None
        rows.append(dict(observer=observer, condition_id=condition, line_pressure_bar=pressure,
                         cohort_count=len(group), available_count=len(v), mean_g_s=mean, sd_g_s=sd,
                         eligible_ids=[b['physical_unit_id'] for b in available],
                         missing_ids=[b['physical_unit_id'] for b in group if b[observer] is None]))
    result = {}
    for region in ['low', 'high']:
        subset = [r for r in rows if (r['line_pressure_bar'] <= 5.25 if region == 'low'
                                      else r['line_pressure_bar'] >= 8.5)]
        p, y = [r['line_pressure_bar'] for r in subset], [r['mean_g_s'] for r in subset]
        s, eps = slope(p, y), numerical_zero(p, y)
        result[region] = dict(slope_g_s_bar=s, sign=sign(s), arithmetic_zero_bound=eps,
                              numerically_near_zero=bool(abs(s) <= eps) if s is not None else None,
                              physical_near_zero_status='NOT_CALIBRATED',
                              conditions=[r['condition_id'] for r in subset])
    present = [r['mean_g_s'] for r in rows if r['mean_g_s'] is not None]
    peak = max(present) if present else None
    result['peak_conditions'] = [r['condition_id'] for r in rows if r['mean_g_s'] == peak] if present else []
    result['eligible_ids'] = [b['physical_unit_id'] for b in brews if b[observer] is not None
                              and b['physical_unit_id'] != deleted
                              and (eligible is None or b['physical_unit_id'] in eligible)]
    result['coverage'] = len(result['eligible_ids'])
    result['complete_canonical_support'] = len(result['eligible_ids']) == 56
    return rows, result


def influence(brews, coordinates, baselines):
    rows = []
    for deleted in brews:
        for observer in OBSERVERS:
            _, changed = summarize(brews, coordinates, observer, deleted=deleted['physical_unit_id'])
            for region in ['low', 'high']:
                base, new = baselines[observer][region]['slope_g_s_bar'], changed[region]['slope_g_s_bar']
                available = deleted[observer] is not None and new is not None and base is not None
                relevant = deleted['condition_id'] in baselines[observer][region]['conditions']
                rows.append(dict(deleted_physical_unit_id=deleted['physical_unit_id'],
                                 condition_id=deleted['condition_id'], observer=observer, region=region,
                                 relevant_to_subset=relevant, paired_deletion_available=available,
                                 unavailable_reason='' if available else 'DELETED_BREW_OR_SLOPE_UNAVAILABLE',
                                 baseline_slope_g_s_bar=base, deletion_slope_g_s_bar=new if available else None,
                                 delta_g_s_bar=new-base if available else None,
                                 baseline_sign=sign(base), deletion_sign=sign(new) if available else 'UNAVAILABLE',
                                 sign_change=sign(new) != sign(base) if available else None,
                                 fixed_pressure_coordinates=True))
    summary = {}
    for observer in OBSERVERS:
        summary[observer] = {}
        for region in ['low', 'high']:
            r = [v for v in rows if v['observer'] == observer and v['region'] == region
                 and v['relevant_to_subset'] and v['paired_deletion_available']]
            summary[observer][region] = dict(
                relevant_deletion_count=len(r),
                minimum_slope_g_s_bar=min(v['deletion_slope_g_s_bar'] for v in r) if r else None,
                maximum_slope_g_s_bar=max(v['deletion_slope_g_s_bar'] for v in r) if r else None,
                sign_changes=[v['deleted_physical_unit_id'] for v in r if v['sign_change']],
                sign_persists=all(not v['sign_change'] for v in r) if r else None,
                most_influential=sorted(r, key=lambda v: (-abs(v['delta_g_s_bar']), v['deleted_physical_unit_id']))[:3])
    return rows, summary


def synthetic():
    t = np.arange(101, dtype=float)
    # A matrix of cumulative masses induced by unit interval discharge rates.
    basis = np.vstack([np.zeros(100), np.tril(np.ones((100, 100)))])
    weights = np.asarray([endpoint_operator(t, basis[:, j])[-1] for j in range(100)])
    j = int(np.argmin(weights))
    ma, mb = t.copy(), t+basis[:, j]
    va, _, _ = mass_windows(t, ma)
    vb, _, _ = mass_windows(t, mb)
    return dict(label='SYNTHETIC_ILLUSTRATION_NOT_EMPIRICAL_ARTIFACT',
                interval_rate_kernel=weights.tolist(), sum_interval_weights=float(weights.sum()),
                negative_interval_count=int((weights < -1e-14).sum()),
                added_nonnegative_discharge_interval_s=[j, j+1],
                minimum_interval_weight=float(weights[j]),
                ordered_discharge_and_mass=True,
                endpoint_A=float(endpoint_operator(t, ma)[-1]),
                endpoint_B=float(endpoint_operator(t, mb)[-1]),
                terminal_mass_A=va, terminal_mass_B=vb,
                cumulative_order_alone_counterexample=dict(
                    definition='M_A=t; M_B=min(2*t,100), 0<=t<=100; M_B>=M_A',
                    terminal_q10_A=1.0, terminal_q10_B=0.0),
                constant_mass_max_abs=float(np.max(np.abs(endpoint_operator(t, np.ones(101))))),
                linear_mass_endpoint=float(endpoint_operator(t, 2*t+3)[-1]))


def inspect_steps(t, m):
    dt, dm = np.diff(t), np.diff(m)
    idx = int(np.argmin(dm))
    gaps = sorted(range(len(dt)), key=lambda j: (-dt[j], j))[:5]
    terminal = np.flatnonzero((t[:-1] < 100) & (t[1:] > 80))
    return dict(timestamp_strictly_increasing=True, duplicate_timestamps=0, finite_measurements=True,
                units=dict(raw_time='ms', aligned_time='s', raw_p2='kPa', scale_mass='g'),
                aligned_final_time_s=float(t[-1]), median_interval_s=float(np.median(dt)),
                maximum_interval_s=float(dt.max()), negative_mass_steps=int((dm < 0).sum()),
                largest_mass_drop=dict(left_time_s=float(t[idx]), right_time_s=float(t[idx+1]),
                                       left_mass_g=float(m[idx]), right_mass_g=float(m[idx+1]),
                                       increment_g=float(dm[idx])),
                terminal_80_100_negative_steps=int((dm[terminal] < 0).sum()),
                terminal_80_100_minimum_step_g=float(dm[terminal].min()) if len(terminal) else None,
                largest_gaps=[dict(left_time_s=float(t[j]), right_time_s=float(t[j+1]),
                                   width_s=float(dt[j]), left_mass_g=float(m[j]),
                                   right_mass_g=float(m[j+1])) for j in gaps])


def region_decision(baseline, influence_summary, region):
    return {name: dict(sign=baseline[name][region]['sign'], coverage=baseline[name]['coverage'],
                      relevant_deletion_count=influence_summary[name][region]['relevant_deletion_count'],
                      deletion_sign_changes=influence_summary[name][region]['sign_changes'],
                      sign_persists=influence_summary[name][region]['sign_persists']) for name in WINDOWS}


def run(root, pw, source, output):
    output.mkdir(parents=True, exist_ok=True)
    membership = {}
    for row in read_csv(root/'docs/analysis/sci_md_010/FOLD_MEMBERSHIP.csv'):
        if row['lane_id'] == 'L-HYD':
            record = (row['physical_unit_id'], row['group_id'])
            old = membership.setdefault(row['source_row_id'], record)
            if old != record:
                raise ValueError('INCONSISTENT_ACCEPTED_MEMBERSHIP')
    if len(membership) != 56 or len(set(c for _, c in membership.values())) != 11:
        raise ValueError('CANONICAL_MEMBERSHIP_NOT_56_11')
    if set(membership) & set(ALIAS):
        raise ValueError('ALIAS_COUNTED_AS_PHYSICAL_BREW')
    retained = {}
    pwdata = pw/'puckworks/data/waszkiewicz2025'
    equilibrium = {r['shot_id']: r for r in read_csv(pwdata/'equilibrium_windows.csv') if r['window'] == 'endpoint_100s'}
    for row in read_csv(pwdata/'traces_per_brew.csv'):
        retained.setdefault(row['shot_id'], []).append(row)
    if set(retained) != set(membership) | set(ALIAS):
        raise ValueError('RETAINED_SOURCE_MAPPING_MISMATCH')
    diagnostics = json.loads((root/'docs/analysis/sci_md_010/PRESSURE_RESPONSE_DIAGNOSTICS.json').read_text())['HYD_B0_TRAINING_MEAN']
    coordinates = {r['condition_id']: r['line_pressure_bar'] for r in diagnostics['condition_means']}
    calibration = [float(r['value']) for r in read_csv(source/'fit_parameters/brewer_calibration.csv')]
    raw_paths = [f'measurements_time_dependent/{sid}.txt' for sid in retained]
    source_paths = raw_paths + ['format_measurements_time_dependent.py', 'fit_parameters/brewer_calibration.csv',
                              'formatted_measurements/time_dependent.csv', 'README.md']
    source_id = identities(source, UPSTREAM, source_paths)
    pwpaths = ['puckworks/data/waszkiewicz2025/'+p for p in ['PROVENANCE.md', 'traces_per_brew.csv',
               'traces_time_dependent.csv', 'equilibrium_windows.csv', 'brewer_quadratic_params.csv']]
    pwpaths += ['puckworks/data/__init__.py', 'puckworks/analysis/waszkiewicz_shot_level.py',
                'tests/test_waszkiewicz_per_brew.py', 'docs/data/ESPRESSO_DATA_GUIDE.md']
    pw_id = identities(pw, PW, pwpaths)
    if not all(x['authenticated'] for x in pw_id.values()):
        raise ValueError('PUCKWORKS_AUTHORITY_BYTES_MISMATCH')
    ewp_paths = ['docs/analysis/sci_md_010/'+p for p in ['FOLD_MEMBERSHIP.csv', 'METRIC_CONTRACT.json',
                                                     'PRESSURE_RESPONSE_DIAGNOSTICS.json']]
    ewp_paths += ['docs/analysis/sci_md_011/OBSERVATION_INTERFACE.json', 'dependencies/puckworks.lock.json']
    ewp_id = identities(root, BASE, ewp_paths)
    if not all(x['authenticated'] for x in ewp_id.values()):
        raise ValueError('EWP_ACCEPTED_AUTHORITY_BYTES_MISMATCH')
    canonical_path, alias_path = [source/f'measurements_time_dependent/{sid}.txt'
                                   for sid in ['12-8-6', '12-8-6_alt']]
    prefix, extended = canonical_path.read_bytes().splitlines(), alias_path.read_bytes().splitlines()
    alias_verified = extended[:len(prefix)] == prefix
    if not alias_verified:
        raise ValueError('RAW_ALIAS_PREFIX_MISMATCH')
    brews, support_rows, reconstructions, grids, errors = [], [], [], {}, []
    for sid in sorted(retained):
        rr = sorted(retained[sid], key=lambda r: int(r['time_index']))
        if len(rr) != 1000 or [int(r['time_index']) for r in rr] != list(range(1000)):
            raise ValueError('RETAINED_GRID_INCOMPLETE')
        canonical = sid not in ALIAS
        physical, condition = membership[ALIAS.get(sid, sid)]
        endpoint = rr[-1]
        brew = dict(physical_unit_id=physical, source_file=f'measurements_time_dependent/{sid}.txt',
                    condition_id=condition, source_sha256=source_id[f'measurements_time_dependent/{sid}.txt']['sha256'],
                    accepted_endpoint_line_pressure_bar=float(endpoint['pressure__bar']),
                    frozen_condition_line_pressure_bar=coordinates[condition],
                    historical_endpoint=float(equilibrium[sid]['mass_flow_rate__g_per_s']),
                    q10=None, q5=None, q20=None, q10_reason='', q5_reason='', q20_reason='')
        try:
            if not source_id[brew['source_file']]['authenticated']:
                raise ValueError('MISSING_OR_UNAUTHENTICATED_SOURCE_FILE')
            a = acquisition(source/brew['source_file'])
            meta = alignment(a, sid+'.txt')
            accepted_ref = float(rr[0]['reference_pressure_round__bar'])
            if meta['reference_condition_bar'] != accepted_ref or condition != 'WASZ-COND-'+str(accepted_ref):
                raise ValueError('SOURCE_CONDITION_MAPPING_MISMATCH')
            t, p, m = aligned(a, meta['start_idx'])
            series, reconstruction = reconstruct(a, meta, calibration)
            grids[sid] = (accepted_ref, series)
            values, reasons, brackets = mass_windows(t, m)
            brew.update(values)
            brew.update({k+'_reason': v for k, v in reasons.items()})
            diffs = {f: float(np.max(np.abs(series[f]-np.array([float(r[f]) for r in rr])))) for f in FIELDS}
            reconstruction.update(dict(source_id=sid, physical_unit_id=physical, canonical=canonical,
                                       condition_id=condition, raw_sample_count=len(a), **meta,
                                       source_sha256=brew['source_sha256'], max_grid_abs_difference=diffs,
                                       pressure_endpoint_difference_bar=reconstruction['reconstructed_pressure_bar']-brew['accepted_endpoint_line_pressure_bar'],
                                       flow_endpoint_difference_g_s=reconstruction['reconstructed_endpoint_g_s']-brew['historical_endpoint'],
                                       all_fields_within_serialization_tolerance=all(v <= BREW_TOL for v in diffs.values())))
            full_q = endpoint_operator(t, m)
            near = (t >= 99.9) & (t <= 100.1)
            pb = p-(calibration[0]*full_q**2+calibration[1]*full_q+calibration[2])
            near_q, near_pb = float(full_q[near].mean()), float(pb[near].mean())
            reconstruction.update(dict(
                trace_endpoint_difference_g_s=reconstruction['reconstructed_endpoint_g_s']-float(endpoint['mass_flow_rate__g_per_s']),
                accepted_equilibrium_endpoint_g_s=brew['historical_endpoint'],
                accepted_equilibrium_n_samples=int(equilibrium[sid]['n_samples']),
                reconstructed_untruncated_near100_mean_g_s=near_q,
                near100_gradient_sample_times_s=t[near].tolist(),
                near100_filter_support_first_time_s=float(t[np.flatnonzero(near)[0]-15]),
                near100_filter_support_last_time_s=float(t[np.flatnonzero(near)[-1]+15]),
                near100_mass_support_first_time_s=float(t[np.flatnonzero(near)[0]-16]),
                near100_mass_support_last_time_s=float(t[np.flatnonzero(near)[-1]+16]),
                near100_all_filter_positions_interior=bool(np.flatnonzero(near)[0] >= 15 and np.flatnonzero(near)[-1] < len(t)-15),
                near100_mean_difference_g_s=near_q-brew['historical_endpoint'],
                near100_basket_difference_bar=near_pb-float(equilibrium[sid]['basket_pressure__bar']),
                near100_count_matches=int(near.sum()) == int(equilibrium[sid]['n_samples']),
                near100_matches_serialized=(abs(near_q-brew['historical_endpoint']) <= BREW_TOL and
                    abs(near_pb-float(equilibrium[sid]['basket_pressure__bar'])) <= BREW_TOL and
                    int(near.sum()) == int(equilibrium[sid]['n_samples'])),
                missing_terminal_record_count=int((~np.isfinite(a).all(axis=1)).sum())))
            reconstructions.append(reconstruction)
            if canonical:
                qa = inspect_steps(t, m)
                # Raw record QA includes pre-alignment data as well.
                qa['complete_raw_timestamps_strictly_increasing'] = bool(np.all(np.diff(a[np.isfinite(a).all(axis=1), 0]) > 0))
                qa['raw_complete_maximum_interval_s'] = float(np.diff(a[np.isfinite(a).all(axis=1), 0]).max()/1000)
                qa['raw_finite_measurements_complete_records_only'] = True
                qa['incomplete_terminal_records'] = [dict(zero_based_row=i, missing_fields=['t', 'm'], retained_p2_kpa=float(a[i, 1])) for i in range(len(a)) if not np.isfinite(a[i]).all()]
                support_rows.append(dict(physical_unit_id=physical, source_id=sid, condition_id=condition,
                                         raw_sample_count=len(a), alignment=meta, endpoints=brackets, acquisition_qa=qa,
                                         physical_support='CONTINUOUS_RECORDED_BRACKETS_NO_TERMINAL_RESET_IDENTIFIED; instrument/interpolation error uncalibrated'))
        except (ValueError, KeyError, OSError) as exc:
            errors.append(dict(source_id=sid, reason=str(exc)))
            for name in WINDOWS:
                brew[name+'_reason'] = str(exc)
        if canonical:
            brews.append(brew)
    # Accepted equal-brew pressure/flow means must reproduce the historical contract.
    for r in diagnostics['condition_means']:
        group = [b for b in brews if b['condition_id'] == r['condition_id']]
        for field, accepted in [('accepted_endpoint_line_pressure_bar', r['line_pressure_bar']),
                                ('historical_endpoint', r['observed_flow_g_s'])]:
            if abs(sum(b[field] for b in group)/len(group)-accepted) > 1e-14:
                raise ValueError('ACCEPTED_CANONICAL_MEAN_MISMATCH')
    condition_rows, baseline = [], {}
    for observer in OBSERVERS:
        rows, summary = summarize(brews, coordinates, observer)
        condition_rows.extend(rows)
        baseline[observer] = summary
    for observer in OBSERVERS:
        for region in ['low', 'high']:
            s = baseline[observer][region]['slope_g_s_bar']
            baseline[observer][region]['difference_from_historical_g_s_bar'] = s-baseline['historical_endpoint'][region]['slope_g_s_bar'] if s is not None else None
    common_ids = [b['physical_unit_id'] for b in brews if all(b[o] is not None for o in OBSERVERS)]
    common = {o: dict(zip(['conditions', 'summary'], summarize(brews, coordinates, o, eligible=set(common_ids)))) for o in OBSERVERS}
    deletions, influence_summary = influence(brews, coordinates, baseline)
    published = read_csv(source/'formatted_measurements/time_dependent.csv')
    by_condition = {}
    for r in published:
        by_condition.setdefault(float(r['reference_pressure_round__bar']), []).append(r)
    published_checks = []
    for pressure, rows in sorted(by_condition.items()):
        ids = sorted(sid for sid, (ref, _) in grids.items() if ref == pressure)
        if not ids:
            continue
        diffs = {}
        for field in FIELDS:
            arrays = np.vstack([grids[sid][1][field] for sid in ids])
            diffs[field] = float(np.max(np.abs(arrays.mean(axis=0)-np.array([float(r[field]) for r in rows]))))
            sem_field = field.replace('__', '_std__')
            diffs[sem_field] = float(np.max(np.abs(arrays.std(axis=0, ddof=1)/math.sqrt(len(ids))-
                                                   np.array([float(r[sem_field]) for r in rows]))))
        published_checks.append(dict(reference_condition_bar=pressure, record_count=len(ids), source_ids=ids,
                                     max_abs_difference=diffs, pass_serialization=all(v <= PUBLISHED_TOL for v in diffs.values()),
                                     published_endpoint_g_s=float(rows[-1]['mass_flow_rate__g_per_s']),
                                     reconstructed_57_endpoint_g_s=float(np.mean([grids[sid][1]['mass_flow_rate__g_per_s'][-1] for sid in ids])),
                                     reconstructed_56_endpoint_g_s=float(np.mean([grids[sid][1]['mass_flow_rate__g_per_s'][-1] for sid in ids if sid not in ALIAS]))))
    reconstructed_brews = [dict(b, source_truncated_endpoint=next((x['reconstructed_endpoint_g_s'] for x in reconstructions if x['physical_unit_id']==b['physical_unit_id'] and x['canonical']), None)) for b in brews]
    reconstructed_conditions, reconstructed_slopes = summarize(reconstructed_brews, coordinates, 'source_truncated_endpoint')
    reconstruction_pass = (len(reconstructions) == 57 and all(r['all_fields_within_serialization_tolerance'] for r in reconstructions)
                           and all(r['pass_serialization'] for r in published_checks))
    manifest = dict(task_id=TASK, ewp_base=BASE, puckworks_revision=PW, upstream_revision=UPSTREAM,
                    upstream_tag='v1.0.1', zenodo_record='18046315',
                    zenodo_api='https://zenodo.org/api/records/18046315',
                    zenodo_metadata_rights='cc-by-4.0',
                    zenodo_archive_md5='ee7ea52d03ea3838b0815ccf0364177f',
                    zenodo_archive_retrieved=False, original_source_retrieval_failures=[],
                    upstream_tree=git(source, 'rev-parse', UPSTREAM+'^{tree}'),
                    puckworks_tree=git(pw, 'rev-parse', PW+'^{tree}'),
                    retrieval_method='git clone --depth 1 --branch v1.0.1 https://github.com/RadostW/espresso.git upstream',
                    evidence_paths_relative_to='upstream checkout for original files; read-only Puckworks checkout for authority files',
                    source_files=source_id, puckworks_files=pw_id, ewp_files=ewp_id,
                    original_acquisition_failures=errors,
                    intake_failure='Initial local Puckworks clone lacked current main object; explicit fetch of pinned revision succeeded.',
                    alias=dict(mapping=ALIAS, exact_line_prefix=alias_verified, canonical_lines=len(prefix),
                               alias_lines=len(extended), extra_lines=len(extended)-len(prefix), counted_once=True),
                    units=dict(t='milliseconds', p2='kPa', m='grams'),
                    licenses=dict(data='CC-BY-4.0; Waszkiewicz et al. 2025; Zenodo 18046315',
                                  upstream_code='GPLv3; inspected only, not copied or executed'),
                    versions={p: importlib.metadata.version(p) for p in ['numpy', 'scipy', 'pandas']},
                    python=platform.python_version(),
                    implementation_sha256=sha(Path(__file__)), protocol_sha256=sha(root/BUNDLE/'PLAN.md'))
    result = dict(task_id=TASK, classification='G1 / NO_GOVERNING_PHYSICS_CHANGE',
                  evidence_role='RESEARCH_ONLY / RETROSPECTIVE / SOURCE_INTERNAL / TARGET_EXPOSED',
                  physical_validation='NOT_ESTABLISHED', canonical_physical_brews=56, conditions=11,
                  fixed_pressure_coordinates=coordinates, observers=baseline,
                  missing_or_invalid_acquisitions=errors, common_support_ids=common_ids,
                  common_support=common, influence=influence_summary,
                  historical_reconstruction=dict(status='SOURCE_TRACE_RECONSTRUCTED_ACCEPTED_ENDPOINT_LINEAGE_DIFFERENT' if reconstruction_pass else 'UNRESOLVED',
                      original_truncated_trace_reconstruction_pass=reconstruction_pass,
                      accepted_near100_numerical_reconstruction_pass=(len(reconstructions)==57 and all(r['near100_matches_serialized'] for r in reconstructions)),
                      accepted_operator_provenance='INFERRED_BY_NUMERICAL_REPRODUCTION; original equilibrium-table producer not retained in inspected authority',
                      paired_contrast_qualification='DESCRIPTIVE_PAIRED_CONTRAST_WITH_RETAINED_ACCEPTED_VALUES; NOT_A_QUALIFIED_CONTRAST_WITH_SOURCE_TRUNCATED_ENDPOINT',
                      per_brew_tolerance=BREW_TOL, published_tolerance=PUBLISHED_TOL,
                      tolerance_basis='half last serialized decimal (5 per-brew; 6 published) plus 1e-10 floating arithmetic slack; debug 4-decimal export not reloaded',
                      canonical_observed_low_slope=baseline['historical_endpoint']['low']['slope_g_s_bar'],
                      canonical_observed_high_slope=baseline['historical_endpoint']['high']['slope_g_s_bar'],
                      published_57_lineage=published_checks,
                      source_truncated_canonical_conditions=reconstructed_conditions,
                      source_truncated_canonical_slopes=reconstructed_slopes),
                  synthetic=synthetic(),
                  physical_support_status=('56_OF_56_CONTINUOUS_RECORDED_BRACKETS_NO_TERMINAL_RESET_IDENTIFIED; PHYSICAL_ERROR_UNCALIBRATED' if len(common_ids)==56 and not errors else 'PARTIAL_SUPPORT_UNRESOLVED'),
                  decisions=dict(
                    A_HISTORICAL_ENDPOINT_RECONSTRUCTION=('Original truncated source trace PASS;' if reconstruction_pass else 'Original truncated source trace UNRESOLVED;') + ' accepted slopes reproduced from equilibrium table. Accepted operator differs: see per-brew near100 numerical checks; original producer provenance UNRESOLVED. No qualified paired claim with the source truncated endpoint.',
                    B_ENDPOINT_OPERATOR_ORDER_PROPERTIES='Truncated composite has negative interval-rate weights and fails general discharge order preservation. Inferred accepted near100 operator is interior SG(31,1) averaging positive irregular-grid derivative weights; sampled supports differ across brews. Common physical-kernel applicability remains conditional.',
                    C_HIGH_PRESSURE_TERMINAL_MASS_SIGN_STABILITY=region_decision(baseline, influence_summary, 'high'),
                    D_LOW_PRESSURE_TERMINAL_MASS_SIGN_STABILITY=region_decision(baseline, influence_summary, 'low'),
                    E_PAIRED_BREW_INFLUENCE=dict(physical_deletions=56, sign_change_count=sum(r['sign_change'] is True for r in deletions), unavailable_count=sum(not r['paired_deletion_available'] for r in deletions), limitation='Outside-subset deletions are not independent robustness evidence'),
                    F_PHYSICAL_APPLICABILITY='Source-internal recorded terminal beverage-mass feature only. Instantaneous discharge, puck flux, common physical origin, matched material/initial states and instrument response are not established. PR207 theorem unchanged; full Mo2021 behavior not inferred.'),
                  interpretation_limits=['No physical measurement uncertainty calibration', 'Deletion ranges are not confidence intervals',
                      'No independent validation or mechanism identification', 'No new window, fit, simulator or successor'])
    write_csv(output/'BREW_RESULTS.csv', brews)
    write_csv(output/'CONDITION_RESULTS.csv', condition_rows)
    write_csv(output/'INFLUENCE.csv', deletions)
    write_csv(output/'RECONSTRUCTION.csv', reconstructions)
    write_json(output/'ACQUISITION_SUPPORT.json', support_rows)
    write_json(output/'SOURCE_MANIFEST.json', manifest)
    write_json(output/'RESULT.json', result)
    print(json.dumps(dict(reconstruction=result['historical_reconstruction']['status'],
                          slopes={k: {r: v[r]['slope_g_s_bar'] for r in ['low','high']} for k,v in baseline.items()},
                          coverage={k: v['coverage'] for k,v in baseline.items()},
                          sign_changes={k: {r: v[r]['sign_changes'] for r in ['low','high']} for k,v in influence_summary.items()}), indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--puckworks-root', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    run(args.root, args.puckworks_root, args.source_root, args.output or args.root/BUNDLE)


if __name__ == '__main__':
    main()
