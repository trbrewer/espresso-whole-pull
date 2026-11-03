#!/usr/bin/env python3
"""Fixed-prediction Form A grading using E1's observer, masks and resamples."""
import argparse
import csv
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

import e1_demonstration as D
import e1_verification as E1
import form_a_demonstration as F
import form_a_verification as V
from prepare_case import form_a_fv_solution

ROOT = V.ROOT
NOMINAL = np.asarray(V.NOMINAL)
SEED, RESAMPLES = 20261103, 1000


def condition_draws(values, conditions):
    """Same within-condition whole-brew draws as E1 response_draws."""
    values, conditions = np.asarray(values), np.asarray(conditions)
    rng = np.random.default_rng(SEED)
    means, draws = [], []
    for pressure in NOMINAL:
        group = np.flatnonzero(conditions == pressure)
        if not len(group):
            raise ValueError('Missing nominal condition')
        picks = rng.choice(group, (RESAMPLES, len(group)), replace=True)
        means.append(values[group].mean())
        draws.append(values[picks].mean(axis=1))
    return np.asarray(means), np.asarray(draws).T


def continuous_response(values, conditions):
    """E1's bracketed three-point interpolation, with fixed-prediction intervals."""
    means, draws = condition_draws(values, conditions)
    peak = D.quadratic_peak(NOMINAL, means)
    peaks = [D.quadratic_peak(NOMINAL, q) for q in draws]
    unresolved = sum(p is None for p in peaks)
    return dict(continuous_peak_bar=peak,
        continuous_peak_interval_bar=None if unresolved else np.quantile(peaks, [.025, .975]).tolist(),
        continuous_peak_unresolved_draws=unresolved,
        continuous_peak_uncertainty='1000 within-condition whole-brew resamples; conditional on transferred fits; nominal-pressure response')


def detector_onset(trace, density, mass_basis='beverage'):
    """Retained native-sample sensitivity; final scoring uses detector_observation."""
    from puckworks.analysis.pressure_peak_stage_b0 import sustained_onset
    with trace.open() as stream:
        header = next(csv.reader(stream))
    if mass_basis not in ('beverage','liquid'):
        raise ValueError('Unknown detector mass basis')
    keys = ['time_s','cup_beverage_mass_kg' if mass_basis=='beverage' else 'cup_water_mass_kg',
            'outlet_flow_m3_s','instantaneous_tds_mass_fraction']
    values = np.loadtxt(trace,delimiter=',',skiprows=1,usecols=[header.index(k) for k in keys]).T
    time,mass,flow,tds = values
    mass_flow = flow*density*1000.
    if mass_basis=='beverage':
        mass_flow = mass_flow/(1.-tds)
    value = sustained_onset(time,mass*1000.,mass_flow)
    return -1. if not np.isfinite(value) else float(value)


def observation_context(source, raw):
    """Authenticate the original clock and reproduce B0c's observed operator."""
    from puckworks.analysis import pressure_peak_stage_b0 as B
    path = raw/'measurements_time_dependent'/(source['brew']+'.txt')
    if D.digest(path) != source['original_sha256']:
        raise ValueError('Original observation trace changed')
    time, pressure, mass, _ = B.raw_trace(path)
    clean_time, _, flow, _ = B.clean_course(time,pressure,mass)
    pre = (time>=-2)&(time<=0)
    baseline = float(np.median(mass[pre]) if pre.any() else mass[0])
    observed = B.sustained_onset(clean_time,np.interp(clean_time,time,mass)-baseline,flow)
    return dict(time=time,pressure=pressure,observed_onset_s=float(observed),
        saved_observed_onset_s=source['observed_onset_for_scoring_only_s'],
        observed_operator_difference_s=float(observed-source['observed_onset_for_scoring_only_s']),
        original_sha256=source['original_sha256'],observed_baseline_g=baseline)


def detector_observation(native_time, beverage_mass_g, context):
    """Resample mass before B0c cleanup, differentiation, 31-sample SG and onset."""
    from puckworks.analysis import pressure_peak_stage_b0 as B
    # Fresh-start native cases retain a zero cup at t=0 in their initial state.
    # Do not extrapolate beyond that state or the actual final trace timestamp.
    native_time = np.asarray(native_time, dtype=float)
    beverage_mass_g = np.asarray(beverage_mass_g, dtype=float)
    if (native_time.ndim != 1 or native_time.shape != beverage_mass_g.shape
            or len(native_time) < 2 or not np.isfinite(native_time).all()
            or not np.isfinite(beverage_mass_g).all() or (np.diff(native_time) <= 0).any()
            or native_time[0] < 0):
        raise ValueError('Missing or corrupt native mass evidence; onset unavailable')
    support_end = float(native_time[-1])
    keep = (context['time']>=0.)&(context['time']<=support_end)
    time = context['time'][keep]; pressure = context['pressure'][keep]
    if len(time) < 31 or not np.isfinite(pressure).all() or (np.diff(time) <= 0).any():
        raise ValueError('Insufficient or corrupt common observation support; onset unavailable')
    mass = np.interp(time,np.r_[0.,native_time],np.r_[0.,beverage_mass_g])
    clean_time,_,flow,_ = B.clean_course(time,pressure,mass)
    pre = (time>=-2)&(time<=0)
    baseline = float(np.median(mass[pre]) if pre.any() else mass[0])
    clean_mass = np.interp(clean_time,time,mass)-baseline
    value = float(B.sustained_onset(clean_time,clean_mass,flow))
    possible = np.flatnonzero(clean_time[-1]-clean_time>=2.)
    if not len(possible):
        raise ValueError('No confirmable two-second observation interval')
    bound = float(clean_time[possible[-1]])
    support = {}
    if np.isfinite(value):
        start = int(np.flatnonzero(clean_time == value)[0])
        confirm = int(np.flatnonzero(clean_time-clean_time[start] >= 2.)[0])
        # Every detected interval sample uses a centered 31-point filter;
        # np.gradient needs one more mass sample. Edge interpolation uses 31.
        first = max(0, min(start-16, len(clean_time)-32))
        last = min(len(clean_time)-1, max(confirm+16, 31))
        support = dict(confirmation_s=float(clean_time[confirm]),
            observer_mass_support_start_s=float(clean_time[first]),
            observer_mass_support_end_s=float(clean_time[last]),
            cup_beverage_mass_at_onset_g=float(clean_mass[start]))
    return dict(**support,onset_s=value if np.isfinite(value) else None,
        detected=bool(np.isfinite(value)),censor_bound_s=bound,
        last_retained_timestamp_s=float(clean_time[-1]),retained_samples=len(clean_time),
        native_initial_state_s=0.,native_initial_cup_mass_g=0.,native_trace_end_s=support_end,
        timestamps_sha256=F.hashlib.sha256(np.asarray(clean_time,dtype='<f8').tobytes()).hexdigest(),
        baseline_g=baseline,
        operator='B0c clean_course then sustained_onset; original timestamps; beverage mass; gradient then Savitzky-Golay 31 samples/order 1; strict >0.5 g and >0.1 g/s for >=2 s; interval start')


def onset_metrics(inputs, first_drips, *, censor_bounds=None, observer='front'):
    """Detector bounds use the last confirmable start; fronts retain 100-s bounds."""
    from puckworks.analysis.pressure_peak_stage_c0 import onset_grade
    observed = np.array([r['observed_onset_for_scoring_only_s'] for r in inputs])
    predicted = np.asarray([np.nan if p is None else p for p in first_drips],dtype=float)
    censored = ~np.isfinite(predicted)|(predicted<0)
    if observer=='detector' and censor_bounds is None:
        raise ValueError('Detector censor bounds must come from retained timestamps')
    bounds = np.full(len(inputs),100.) if censor_bounds is None else np.asarray(censor_bounds,dtype=float)
    difference = np.where(censored,np.maximum(0.,bounds-observed),predicted-observed)
    groups = [np.flatnonzero(np.array([r['nominal_pressure_bar'] for r in inputs]) == p) for p in NOMINAL]
    rmse = float(np.mean([np.sqrt(np.mean(difference[g]**2)) for g in groups]))
    draws = D.paired_rmse_draws(np.array([difference**2]), groups)[:, 0]
    result = dict(onset_rmse_s=rmse, onset_rmse_interval_s=np.quantile(draws, [.025, .975]).tolist(),
        onset_rmse_is_lower_bound=bool(censored.any()), onset_censored_brews=int(censored.sum()),
        onset_detected_brews=int((~censored).sum()),
        onset_interval_definition=('Interval for the RMSE lower bound' if censored.any() else 'RMSE interval')+'; conditional on transferred fits',
        onset_definition='B0c full observation operator' if observer=='detector' else 'Superseded front-versus-observed-onset diagnostic; ungraded',
        censor_bounds_s=bounds.tolist())
    if observer=='detector':
        grade = onset_grade(rmse)
        result['onset_grade'] = 'NOT_SCORED' if censored.any() and grade!='MISSES' else grade
    return result


def grade(inputs, endpoints, traces, pressure_end, first_drips, arm, forcing):
    from puckworks.analysis.pressure_peak_stage_c0 import bias_grade
    score = D.score_predictions(inputs, endpoints, traces, pressure_end)
    conditions = np.array([r['nominal_pressure_bar'] for r in inputs])
    residual = np.asarray(endpoints)-[r['observed_endpoint_g_s'] for r in inputs]
    mean, draws = condition_draws(residual, conditions)
    score.update(arm=arm, forcing=forcing, **continuous_response(endpoints, conditions),
        **onset_metrics(inputs, first_drips), condition_residuals_g_s=mean.tolist(),
        condition_residual_intervals_g_s=np.quantile(draws, [.025, .975], axis=0).T.tolist(),
        low_pressure_bias_g_s=float(mean[:3].mean()), low_pressure_bias_grade=bias_grade(mean[:3].mean()),
        low_pressure_bias_interval_g_s=np.quantile(draws[:, :3].mean(axis=1), [.025, .975]).tolist(),
        residual_1_g_s=float(mean[0]), residual_2_g_s=float(mean[1]), residual_3_5_g_s=float(mean[2]),
        trend_grade='NOT_SCORED',
        trend_note='E1 native histories stop at 100 s; D0 resolved late windows can extend beyond 100 s. No extrapolation.')
    return score


def onset_rows(inputs, records, arm):
    rows, summary = [], []
    for source in inputs:
        value = records[source['brew']]['first_drip_s']
        censored = value < 0
        observed = source['observed_onset_for_scoring_only_s']
        rows.append(dict(arm=arm, brew=source['brew'], nominal_pressure_bar=source['nominal_pressure_bar'],
            forcing='constant_descriptive' if arm == 'A0' else 'measured_history',
            clock='seconds since stable pressure', solver_first_drip_stable_s=None if censored else value,
            solver_first_drip_lower_bound_s=100. if censored else value, right_censored=censored,
            observed_onset_stable_s=observed, solver_minus_observed_s=None if censored else value-observed,
            difference_lower_bound_s=(100. if censored else value)-observed))
    for pressure in NOMINAL:
        group = [r for r in rows if r['nominal_pressure_bar'] == pressure]
        lower = np.array([r['solver_first_drip_lower_bound_s'] for r in group])
        observed = np.array([r['observed_onset_stable_s'] for r in group])
        count = sum(r['right_censored'] for r in group)
        # For even samples, both central order statistics must be observed.
        known_median = count == 0 or len(group)-count > len(group)//2
        summary.append(dict(arm=arm, nominal_pressure_bar=float(pressure), brews=len(group),
            forcing='constant_descriptive' if arm == 'A0' else 'measured_history',
            clock='seconds since stable pressure', disposition='DESCRIPTIVE',
            solver_median_s=float(np.median(lower)) if known_median else None,
            solver_min_s=float(lower.min()) if count < len(group) else None,
            solver_max_s=float(lower.max()) if count == 0 else None,
            observed_median_s=float(np.median(observed)), observed_min_s=float(observed.min()),
            observed_max_s=float(observed.max()),
            difference_median_s=float(np.median(lower-observed)) if count == 0 else None,
            difference_min_s=float(np.min(lower-observed)) if count == 0 else None,
            difference_max_s=float(np.max(lower-observed)) if count == 0 else None,
            right_censored_brews=count, solver_median_lower_bound_s=float(np.median(lower))))
    return rows, summary


def read_native(work, record, density):
    trace = work/record['run']/'postProcessing/wholePull/0/traces.csv'
    if D.digest(trace) != record['trace_sha256']:
        raise ValueError('Native trace changed: '+record['run'])
    config = work/(record['run']+'.json')
    if D.digest(config) != record['config_sha256']:
        raise ValueError('Native config changed: '+record['run'])
    solution = work/record['run']/'system/fvSolution'
    reference = ROOT/'cases/reference_R0_20g_58mm_9bar/system/fvSolution'
    if solution.read_text() != form_a_fv_solution(json.loads(config.read_text()), reference.read_text()):
        raise ValueError('Unexpected native linear-solver controls: '+record['run'])
    solution_hash = D.digest(solution)
    if record.get('fv_solution_sha256', solution_hash) != solution_hash:
        raise ValueError('Native linear-solver controls changed: '+record['run'])
    record['fv_solution_sha256'] = solution_hash
    with trace.open() as stream:
        header = next(csv.reader(stream))
    keys = ['time_s', 'outlet_flow_m3_s', 'min_saturation', 'form_a_bed_mean_x', 'form_a_min_cell_x_increment']
    values = np.loadtxt(trace, delimiter=',', skiprows=1, usecols=[header.index(k) for k in keys]).T
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite native output')
    record['minimum_cell_x_increment'] = float(values[4].min())
    if record['minimum_cell_x_increment'] < 0:
        raise ValueError('Extracted fraction decreased in a native cell')
    saturated = np.flatnonzero(values[2] >= 1.)
    record['full_saturation_s'] = record['first_drip_s']
    record['saturation_completed_step_s'] = float(values[0, saturated[0]]) if len(saturated) else None
    return values[0], values[1]*density*1000


def python_trace(puckworks, parameters, times, pressure, start=0.):
    return python_prediction(puckworks,parameters,times,pressure,start)[0]


def python_prediction(puckworks, parameters, times, pressure, start=0.):
    """Liquid flow/mass only; forcing retains its original absolute timestamps."""
    times, pressure = np.asarray(times), np.maximum(np.asarray(pressure), 0.)
    if start < 0 or start >= times[-1]:
        return np.zeros(len(times)),np.zeros(len(times))
    absolute, forcing = D.delayed_grid(times, pressure, start)
    q, mass = V.python_flow(puckworks, parameters, absolute-start, forcing[None, :])
    result = np.interp(times, absolute, q[0])
    delivered = np.interp(times,absolute,mass[0])
    result[times < start] = 0.
    delivered[times < start] = 0.
    return result,delivered


def r0_front_delay(config):
    """The unchanged uniform R0 front integral, with no fitted onset input."""
    h=config['hydraulics'];w=config['wetting'];bed=config['coffee_bed']
    if w['initial_saturation']!=0. or w['initial_wet_front_m']!=0.:
        raise ValueError('Reduced comparator requires the retained R0 initial state')
    schedule=h['prescribed_pressure_boundary']
    time=np.asarray(schedule['times_s']);p=np.asarray(schedule['pressures_gauge_Pa'])-h['front_pressure_gauge_Pa']
    if (p<0).any():raise ValueError('R0 replay requires the retained nonnegative pressure histories')
    target=bed['bed_depth_m']**2*config['liquid']['dynamic_viscosity_Pa_s']*bed['initial_porosity']/(2*h['wetting_permeability_m2'])
    integral=0.
    for i,dt in enumerate(np.diff(time)):
        step=.5*(p[i]+p[i+1])*dt
        if integral+step>=target:
            lo,hi=0.,float(dt)
            slope=(p[i+1]-p[i])/dt
            for _ in range(64):
                mid=(lo+hi)/2
                if p[i]*mid+.5*slope*mid**2<target-integral:lo=mid
                else:hi=mid
            return float(time[i]+(lo+hi)/2)
        integral+=step
    return -1.


def reduced_a0_delays(args,bank,inputs,e1_records):
    """Authenticate E1's R0 history delay, with an unchanged-integral fallback."""
    result={}
    for source in inputs:
        brew=source['brew'];p=source['nominal_pressure_bar']
        expected=V.scenario(F.parameters_for(bank,'measured_history',p),'A0',p,.005,
                            history=(source['times_s'],source['pressure_bar']))
        integral=r0_front_delay(expected)
        record=e1_records.get(brew)
        path=args.e1_work/(record['run']+'.json') if record and args.e1_work else None
        verified=False;reason=None;config_hash=None
        if path and path.exists():
            config_hash=D.digest(path)
            old=json.loads(path.read_text())
            verified=config_hash==record['config_sha256'] and all(old[k]==expected[k]
                for k in ('geometry','coffee_bed','liquid','hydraulics','wetting')) and old['time']['start_s']==expected['time']['start_s']
            if not verified:reason='Retained E1 config does not authenticate every R0 input'
        else:reason='Retained E1 config unavailable; use the unchanged R0 front integral'
        delay=float(record['first_drip_s']) if verified else integral
        result[brew]=dict(delay_s=delay,method='authenticated E1 history R0 breakthrough' if verified else 'unchanged R0 front integral',
            identical_pressure_geometry_initial_state_and_clock=verified,E1_config_sha256=config_hash,
            integral_delay_s=integral,E1_minus_integral_s=delay-integral if verified else None,fallback_reason=reason,
            role='Reduced A0 comparator, qualified by A0 parity; hydraulic quantities only')
    return result


def flow_score(inputs,endpoints,traces,pressure_end,label,scope):
    """Unchanged E1 hydraulic score and condition-wise residuals."""
    from puckworks.analysis.pressure_peak_stage_c0 import bias_grade
    score=D.score_predictions(inputs,endpoints,traces,pressure_end)
    conditions=np.array([r['nominal_pressure_bar'] for r in inputs])
    residual=np.asarray(endpoints)-[r['observed_endpoint_g_s'] for r in inputs]
    means,draws=condition_draws(residual,conditions)
    score.update(arm=label,scope=scope,available_brews=len(inputs),intended_brews=56,
        interval_scope='conditional on transferred fits',
        condition_residuals_g_s=means.tolist(),
        condition_residual_intervals_g_s=np.quantile(draws,[.025,.975],axis=0).T.tolist(),
        residual_1_g_s=float(means[0]),residual_2_g_s=float(means[1]),residual_3_5_g_s=float(means[2]),
        low_pressure_bias_g_s=float(means[:3].mean()),low_pressure_bias_grade=bias_grade(means[:3].mean()))
    return score


def paired_comparison(inputs,left,right,scope):
    """Both scores and paired A1-minus-A0 intervals from identical brew draws."""
    groups=[np.flatnonzero(np.array([r['nominal_pressure_bar'] for r in inputs])==p) for p in NOMINAL]
    result=[]
    for metric in ('endpoint','primary_trace','companion_trace'):
        squared=[]
        for prediction in (left,right):
            if metric=='endpoint':
                se=(np.asarray(prediction['endpoints'])-[r['observed_endpoint_g_s'] for r in inputs])**2
            else:
                se=[]
                for source,q in zip(inputs,prediction['traces']):
                    mask=np.array(source['trace_mask'],dtype=bool) if metric=='primary_trace' else np.asarray(source['trace_times_s'])>=5.
                    se.append(float(np.mean((np.asarray(q)[mask]-np.asarray(source['observed_trace_g_s'])[mask])**2)))
                se=np.asarray(se)
            squared.append(se)
        points=[float(np.mean([np.sqrt(se[g].mean()) for g in groups])) for se in squared]
        draws=D.paired_rmse_draws(np.asarray(squared),groups,count=RESAMPLES,seed=SEED)
        result.append(dict(comparison=scope,metric=metric,A0_rmse_g_s=points[0],A1_rmse_g_s=points[1],
            A1_minus_A0_g_s=points[1]-points[0],
            paired_interval_g_s=np.quantile(draws[:,1]-draws[:,0],[.025,.975]).tolist(),
            interval_scope='conditional on transferred fits; paired differences on identical condition/brew draws',
            brews=len(inputs),resamples=RESAMPLES,seed=SEED))
    return result


def csv_safe(rows):
    keys = list(dict.fromkeys(k for row in rows for k in row))
    return [{k:json.dumps(r.get(k)) if isinstance(r.get(k), (dict, list)) else r.get(k)
             for k in keys} for r in rows]


def parse_score(row):
    result = {}
    for key, value in row.items():
        try:
            result[key] = json.loads(value)
        except (ValueError, TypeError):
            result[key] = value
    return result


def reference(inputs):
    directory = ROOT/'docs/demonstrations/E1_CAPABILITY'
    manifest = json.loads((directory/'RUN_MANIFEST.json').read_text())
    records = {r['brew']:r for r in manifest['runs'] if r['forcing'] == 'measured_history'}
    score = parse_score(next(r for r in E1.records(directory/'GRADES.csv') if r['forcing'] == 'measured_history'))
    endpoints = [records[r['brew']]['endpoint_flow_g_s'] for r in inputs]
    conditions = [r['nominal_pressure_bar'] for r in inputs]
    residual, draws = condition_draws(np.asarray(endpoints)-[r['observed_endpoint_g_s'] for r in inputs], conditions)
    from puckworks.analysis.pressure_peak_stage_c0 import bias_grade
    score.update(arm='E1', forcing='measured_history_transferred_medians',
        **continuous_response(endpoints, conditions),
        **onset_metrics(inputs, [records[r['brew']]['first_drip_s'] for r in inputs]),
        condition_residuals_g_s=residual.tolist(),
        condition_residual_intervals_g_s=np.quantile(draws, [.025, .975], axis=0).T.tolist(),
        residual_1_g_s=float(residual[0]), residual_2_g_s=float(residual[1]), residual_3_5_g_s=float(residual[2]),
        low_pressure_bias_g_s=float(residual[:3].mean()), low_pressure_bias_grade=bias_grade(residual[:3].mean()),
        low_pressure_bias_interval_g_s=np.quantile(draws[:, :3].mean(axis=1), [.025, .975]).tolist())
    rows, summary = onset_rows(inputs, records, 'E1')
    constants = {r['nominal_pressure_bar']:r for r in manifest['runs'] if r['forcing'] == 'constant'}
    return score, rows, summary, constants


def sweep_metrics(records):
    pressures = np.array(sorted(records))
    flow = np.array([records[p]['endpoint_flow_g_s'] for p in pressures])
    drip = np.array([records[p]['first_drip_s'] for p in pressures])
    valid = drip >= 0
    point = D.quadratic_peak(pressures[valid], -drip[valid])
    return dict(continuous_sweep_peak_bar=D.quadratic_peak(pressures, flow),
        fastest_wetting_bar=float(pressures[valid][np.argmin(drip[valid])]) if point is None else point,
        fastest_wetting_is_sweep_boundary=point is None)


def generate_report(args):
    # Kept here as the public CLI; closeout contains reporting only, never CFD.
    from form_a_closeout import generate_report as closeout
    return closeout(args)


def internal_scalars(path, count=None):
    """Read Foundation 12 scalar internal fields; boundary values are excluded."""
    raw = path.read_bytes()
    match = re.search(rb'internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\(', raw)
    if match:
        size = int(match[1])
        if b'format      binary;' in raw or re.search(rb'format\s+binary;', raw):
            arch = re.search(rb'\barch\s+"([^"]+)"',raw)
            if (arch and arch[1] != b'LSB;label=32;scalar=64') or (not arch and sys.byteorder != 'little'):
                raise ValueError('Unsupported binary field architecture')
            if not re.match(rb'\s*\)',raw[match.end()+8*size:]):
                raise ValueError('Expected native 64-bit scalar field')
            values = np.frombuffer(raw, dtype='<f8', count=size, offset=match.end()).copy()
        else:
            values = np.fromstring(raw[match.end():raw.index(b')',match.end())].decode(), sep=' ')
        if len(values) != size or (count is not None and size != count):
            raise ValueError('Field size mismatch')
    else:
        match = re.search(rb'internalField\s+uniform\s+([^;]+);', raw)
        if match is None or count is None:
            raise ValueError('Missing scalar internal field or uniform field size')
        values = np.full(count, float(match[1]))
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite internal field')
    return values


def a0_owner_review(args, bank, inputs, density):
    """Historical owner review; final closeout does not use this propagated interval."""
    from scipy.optimize import brentq
    from scipy.special import expi
    records = {p:json.loads((args.work/f'A0-constant-{p:g}-dt0.005.result.json').read_text())
               for p in F.constant_pressures()}
    if any(r['executable_sha256'] != D.digest(args.executable)
           or any(r['parameters'][key] != value for key,value in bank['DESCRIPTIVE_ALL'].items())
           for r in records.values()):
        raise ValueError('A0 saved-fit or executable identity mismatch')
    native = {p:read_native(args.work,r,density) for p,r in records.items()}
    chosen = [records[r['nominal_pressure_bar']] for r in inputs]
    score = grade(inputs,[r['endpoint_flow_g_s'] for r in chosen],
        [np.interp(r['trace_times_s'],*native[r['nominal_pressure_bar']]) for r in inputs],
        [r['nominal_pressure_bar'] for r in inputs],[r['first_drip_s'] for r in chosen],
        'A0','in_sample_DESCRIPTIVE_ALL_constant')
    pressure = np.array(sorted(records))
    delay = np.array([records[p]['first_drip_s'] for p in pressure])
    table = E1.records(args.puckworks/V.TABLE)
    point = json.loads(next(r['parameters'] for r in table if r['record_type']=='point_replay'
                            and r['candidate']=='A' and r['fold']=='DESCRIPTIVE_ALL'))
    saved = [r for r in table if r['record_type']=='refit' and r['candidate']=='A' and r['fold']=='DESCRIPTIVE_ALL']
    def evaluate(parameters):
        p = parameters
        capacity = p['a_g_s_bar']*p['Pd_bar']*(-np.expm1(-(pressure/p['Pd_bar'])**p['n']))*np.exp(-pressure/p['Pstar_bar'])
        tau = capacity*(100-delay)/p['Mc_fixed_g']
        # Integral of dz/dtau=exp(-exp(-z)): Ei(1)-Ei(exp(-z))=tau.
        z = [brentq(lambda x:expi(1.)-expi(np.exp(-x))-t,t*np.exp(-1.),t,xtol=1e-13)
             if t>0 else 0. for t in tau]
        flow = capacity*np.exp(-np.exp(-np.array(z)))
        return D.quadratic_peak(pressure,flow),flow
    peaks = [dict(draw=int(r['draw']),peak_bar=evaluate(json.loads(r['parameters']))[0]) for r in saved]
    predicted_peak, predicted_flow = evaluate(point)
    saved_e1 = json.loads((ROOT/'docs/demonstrations/E1_CAPABILITY/RUN_MANIFEST.json').read_text())
    e1_constants = {r['nominal_pressure_bar']:r for r in saved_e1['runs'] if r['forcing']=='constant'}
    drip = [dict(nominal_pressure_bar=p,A0_first_drip_s=records[p]['first_drip_s'],
                 E1_first_drip_s=e1_constants[p]['first_drip_s'],
                 difference_s=records[p]['first_drip_s']-e1_constants[p]['first_drip_s']) for p in V.NOMINAL]
    actual_flow = np.array([records[p]['endpoint_flow_g_s'] for p in pressure])
    result = dict(score=score, scope='In-sample DESCRIPTIVE_ALL; not a like-for-like gain over held-out B1',
        comparable_held_out_python_A_endpoint_rmse_g_s=.1530012355513247,
        native_dense_sweep_peak_bar=D.quadratic_peak(pressure,actual_flow),
        propagated_peak_interval_bar=np.quantile([r['peak_bar'] for r in peaks],[.025,.975]).tolist(),
        delayed_python_point_peak_bar=predicted_peak,
        maximum_native_vs_analytic_endpoint_difference_g_s=float(max(abs(actual_flow-predicted_flow))),
        saved_D0_draw_count=len(peaks),saved_D0_seed=int(next(r['seed'] for r in table if r['record_type']=='pairing')),
        interval_method='Propagate saved D0 DESCRIPTIVE_ALL parameter draws through exact separable Form A with existing A0 R0 wetting delays and the same 23-point quadratic peak estimator; no new fits or native runs',
        interval_scope='Parameter propagation through the verified uniform limit; distinct from unchanged 1000-resample fixed-prediction grades',
        D0_python_peak_bar=5.9985611853692165,D0_python_peak_interval_bar=[5.769910854571623,6.272472184514531],
        source_table_sha256=D.digest(args.puckworks/V.TABLE),draws=peaks,first_drip_comparison=drip,
        maximum_first_drip_difference_s=max(abs(r['difference_s']) for r in drip),
        native_records=list(records.values()))
    return result


def write_owner_review(args):
    """Owner-requested A0 review and one A2 probe; never dispatch native runs."""
    bank = V.saved_inputs(args.puckworks)
    sys.path.insert(0,str(args.puckworks))
    inputs = json.loads((args.work/'source_inputs.json').read_text())
    e1 = json.loads((ROOT/'docs/demonstrations/E1_CAPABILITY/RUN_MANIFEST.json').read_text())
    if {r['brew']:r['original_sha256'] for r in inputs} != {r['brew']:r['sha256'] for r in e1['originals']}:
        raise ValueError('Raw cohort differs from E1')
    density = json.loads((ROOT/'config/reference_R0.json').read_text())['liquid']['density_kg_m3']
    a0 = a0_owner_review(args,bank,inputs,density)
    xc = json.loads((args.work/'XC-dt0.005.json').read_text())
    case = args.owner_probe.resolve()
    record = json.loads(case.with_name(case.name+'.result.json').read_text())
    cfg = json.loads(case.with_name(case.name+'.json').read_text())
    expected = V.scenario(bank['DESCRIPTIVE_ALL'],'A2',9.,.005,xc=xc['xc_9bar'])
    expected['time']['field_write_interval_s'] = 10.
    if cfg != expected or record['executable_sha256'] != D.digest(args.executable):
        raise ValueError('Probe differs from the unchanged closure apart from field-output cadence')
    t2,q2 = read_native(case.parent,record,density)
    a1_record = json.loads((args.work/'A1-constant-9-dt0.005.result.json').read_text())
    t1,q1 = read_native(args.work,a1_record,density)
    def mass_trace(directory):
        rows = E1.records(directory/'postProcessing/wholePull/0/traces.csv')
        return tuple(np.array([float(r[key])*factor for r in rows]) for key,factor in
                     [('time_s',1),('cup_water_mass_kg',1000),('form_a_bed_mean_x',1)])
    mt1,m1,_ = mass_trace(args.work/a1_record['run']); mt2,m2,x2 = mass_trace(case)
    processors = sorted(case.glob('processor[0-9]*'),key=lambda p:int(p.name[9:]))
    if len(processors) != record['ranks']:
        raise ValueError('Incomplete probe decomposition')
    volumes = [internal_scalars(p/'10/Vc') for p in processors]
    weight = np.concatenate(volumes)
    if (weight<=0).any():raise ValueError('Nonpositive cell volume')
    field_hashes = {str(p/'10/Vc'):D.digest(p/'10/Vc') for p in processors}
    rows = []
    for time in [10.,20.,40.,60.,100.]:
        fields=[]; recoveries=[]
        for p,v in zip(processors,volumes):
            directory=min((d for d in p.iterdir() if d.is_dir() and re.fullmatch(r'[0-9.eE+-]+',d.name)),key=lambda d:abs(float(d.name)-time))
            if not np.isclose(float(directory.name),time,rtol=0,atol=1e-8):raise ValueError('Missing requested snapshot')
            for name,target in [('formAExtractedFraction',fields),('formARecovery',recoveries)]:
                path=directory/name; target.append(internal_scalars(path,len(v)))
                field_hashes[str(path)]=D.digest(path)
        x=np.concatenate(fields); used=np.concatenate(recoveries)
        recovery=np.exp(-np.exp(-x/xc['xc_9bar']))
        mass1=float(np.interp(time,mt1,m1));mass2=float(np.interp(time,mt2,m2))
        flow1=float(np.interp(time,t1,q1));flow2=float(np.interp(time,t2,q2))
        rows.append(dict(time_s=time,A2_over_A1_flow_ratio=flow2/flow1,A1_flow_g_s=flow1,A2_flow_g_s=flow2,
            mean_x=float(np.average(x,weights=weight)),min_cell_x=float(x.min()),max_cell_x=float(x.max()),
            trace_bed_mean_x=float(np.interp(time,mt2,x2)),
            mean_R_cell=float(np.average(recovery,weights=weight)),mean_R_cell_used=float(np.average(used,weights=weight)),
            global_R_at_A1_outlet_mass=float(np.exp(-np.exp(-mass1/bank['DESCRIPTIVE_ALL']['mcG']))),
            global_R_at_A2_outlet_mass=float(np.exp(-np.exp(-mass2/bank['DESCRIPTIVE_ALL']['mcG']))),
            A1_outlet_mass_g=mass1,A2_outlet_mass_g=mass2))
    hold=json.loads((args.work/'A2_OWNER_HOLD.json').read_text())
    completed=[json.loads(p.read_text()) for p in sorted(args.work.glob('A2-constant-*.result.json'))]
    probe=dict(definition='Single owner-requested A2 DESCRIPTIVE_ALL 9-bar constant probe',
        xc_normalization=xc,rows=rows,run=record,A1_reference_run=a1_record,
        recovery_ceiling=float(np.exp(-np.exp(-1/xc['xc_9bar']))),
        averaging='Cell-volume weighted; initial extractable density is uniform, so this equals initial-solid-weighted averaging',
        recovery_definition='R_cell recomputed from snapshot X; mean_R_cell_used retains the actual preceding-step recovery field. Global R uses A1 outlet mass; the A2-mass counterfactual is also recorded.',
        field_encoding='Foundation 12 DP/Int32 native little-endian scalar64; absent arch headers use the native build encoding, with payload length checked',
        snapshot_sha256={str(Path(p).relative_to(case)):v for p,v in field_hashes.items()},
        hold=hold,retained_completed_A2_campaign_runs=completed,
        source_sha256={p:D.digest(ROOT/p) for p in ['scripts/form_a_report.py','scripts/form_a_verification.py','scripts/form_a_demonstration.py','solver/espressoWholePullFoam/formAWholeBedClosure.H','solver/espressoWholePullFoam/espressoWholePullFoam.C']},
        native_outputs='External task run directory; no native files deleted',
        native_index=D.output_index(case))
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'A0_REVIEW.json').write_text(json.dumps(a0,indent=2,allow_nan=False)+'\n')
    (args.out/'A2_PROBE.json').write_text(json.dumps(probe,indent=2,allow_nan=False)+'\n')
    E1.write_csv(args.out/'A0_FIRST_DRIP_COMPARISON.csv',a0['first_drip_comparison'])
    E1.write_csv(args.out/'A2_PROBE.csv',rows)
    print(json.dumps(dict(A0_peak=a0['native_dense_sweep_peak_bar'],A0_interval=a0['propagated_peak_interval_bar'],probe=rows),indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('puckworks', 'work', 'raw', 'executable'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--e1-work', type=Path, help='Retained E1 native traces; never rerun')
    parser.add_argument('--probe-work', type=Path, help='Retained A2 probe case directory')
    parser.add_argument('--out', type=Path, default=ROOT/'docs/demonstrations/FORM_A')
    parser.add_argument('--owner-probe', type=Path,
                        help='Reproduce the historical owner probe review; use --probe-work for final closeout')
    args = parser.parse_args()
    if args.owner_probe:
        write_owner_review(args)
    else:
        generate_report(args)


if __name__ == '__main__':
    main()
