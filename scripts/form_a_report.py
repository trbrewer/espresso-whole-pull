#!/usr/bin/env python3
"""Fixed-prediction Form A grading using E1's observer, masks and resamples."""
import argparse
import csv
import importlib.metadata
import json
from pathlib import Path
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
        continuous_peak_uncertainty='1000 within-condition whole-brew resamples; fixed predictions; nominal-pressure response')


def onset_metrics(inputs, first_drips):
    """A missing native first drip is right-censored at 100 s, never minus one."""
    from puckworks.analysis.pressure_peak_stage_c0 import onset_grade
    observed = np.array([r['observed_onset_for_scoring_only_s'] for r in inputs])
    predicted = np.asarray(first_drips, dtype=float)
    censored = predicted < 0
    if np.any(observed >= 100):
        raise ValueError('Censoring lower bound assumes observed onset before 100 s')
    difference = np.where(censored, 100., predicted)-observed
    groups = [np.flatnonzero(np.array([r['nominal_pressure_bar'] for r in inputs]) == p) for p in NOMINAL]
    rmse = float(np.mean([np.sqrt(np.mean(difference[g]**2)) for g in groups]))
    draws = D.paired_rmse_draws(np.array([difference**2]), groups)[:, 0]
    grade = onset_grade(rmse)
    if censored.any() and grade != 'MISSES':
        grade = 'NOT_SCORED'
    return dict(onset_rmse_s=rmse, onset_rmse_interval_s=np.quantile(draws, [.025, .975]).tolist(),
        onset_rmse_is_lower_bound=bool(censored.any()), onset_censored_brews=int(censored.sum()),
        onset_grade=grade, onset_definition='sharp-front first drip versus B0c sustained observed onset')


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
    times, pressure = np.asarray(times), np.maximum(np.asarray(pressure), 0.)
    if start < 0 or start >= times[-1]:
        return np.zeros(len(times))
    absolute, forcing = D.delayed_grid(times, pressure, start)
    q, _ = V.python_flow(puckworks, parameters, absolute-start, forcing[None, :])
    result = np.interp(times, absolute, q[0])
    result[times < start] = 0.
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
    bank = V.saved_inputs(args.puckworks)
    sys.path.insert(0, str(args.puckworks))
    inputs = json.loads((args.work/'source_inputs.json').read_text())
    e1_manifest = json.loads((ROOT/'docs/demonstrations/E1_CAPABILITY/RUN_MANIFEST.json').read_text())
    expected = {r['brew']:r['sha256'] for r in e1_manifest['originals']}
    if {r['brew']:r['original_sha256'] for r in inputs} != expected:
        raise ValueError('Raw cohort differs from E1')
    selected = json.loads((args.work/'STEP_SELECTION.json').read_text())
    executable_hash = D.digest(args.executable)
    if selected['executable_sha256'] != executable_hash:
        raise ValueError('Time step selected using another executable')
    for name, sha in selected['studies'].items():
        if D.digest(args.work/name) != sha:
            raise ValueError('Changed time-step evidence')
    xc = json.loads((args.work/f"XC-dt{selected['delta_t_s']:g}.json").read_text())
    if xc['executable_sha256'] != executable_hash:
        raise ValueError('Xc measured using another executable')
    records = [json.loads(p.read_text()) for p in sorted(args.work.glob('*.result.json'))]
    campaigns = [r for r in records if r['forcing'] in ('constant', 'measured_history')]
    if len(campaigns) != 181:
        raise ValueError('Expected exactly 23 A0 + 79 A1 + 79 A2 campaign runs')
    constants, histories, scores, onset_all, onset_summary = {}, {}, [], [], []
    density = json.loads((ROOT/'config/reference_R0.json').read_text())['liquid']['density_kg_m3']
    source_by_brew = {r['brew']:r for r in inputs}
    native_traces = {}
    for record in records:
        if record['executable_sha256'] != executable_hash or not record['balances_and_bounds_qualified']:
            raise ValueError('Native run identity or existing balance qualification differs')
        native = read_native(args.work, record, density)
        if record['forcing'] in ('constant', 'measured_history'):
            if record['delta_t_s'] != selected['delta_t_s']:
                raise ValueError('Campaign time steps differ')
            expected_parameters = F.parameters_for(bank, record['forcing'], record['nominal_pressure_bar'])
            if any(record['parameters'][key] != value for key, value in expected_parameters.items()):
                raise ValueError('Wrong saved D0 parameters: '+record['run'])
            if record['arm'] == 'A2' and record['parameters']['xc'] != xc['xc_9bar']:
                raise ValueError('Wrong A2 normalization')
            native_traces[record['run']] = native
        fields = D.final_field_sanity(args.work/record['run'])
        fields.pop('positive_e1_multiplier')  # E1-specific field is absent in these runs.
        if not fields['finite_values']:
            raise ValueError('Nonfinite final native fields')
        record['numerical_sanity'] = fields
        record.update(D.output_index(args.work/record['run']))
    for arm in ('A0', 'A1', 'A2'):
        constants[arm] = {r['nominal_pressure_bar']:r for r in campaigns if r['arm'] == arm and r['forcing'] == 'constant'}
        histories[arm] = {r['brew']:r for r in campaigns if r['arm'] == arm and r['forcing'] == 'measured_history'}
        if set(constants[arm]) != set(F.constant_pressures()):
            raise ValueError('Incomplete 23-point sweep: '+arm)
        if set(histories[arm]) != (set() if arm == 'A0' else set(source_by_brew)):
            raise ValueError('Incomplete or unauthorized history matrix: '+arm)
        forcing = 'constant_descriptive' if arm == 'A0' else 'measured_history_held_out'
        chosen = {r['brew']:constants[arm][r['nominal_pressure_bar']] if arm == 'A0' else histories[arm][r['brew']]
                  for r in inputs}
        endpoint = [chosen[r['brew']]['endpoint_flow_g_s'] for r in inputs]
        trace = [np.interp(r['trace_times_s'], *native_traces[chosen[r['brew']]['run']]) for r in inputs]
        pressure_end = [r['nominal_pressure_bar'] if arm == 'A0' else r['pressure_bar'][-1] for r in inputs]
        first_drip = [chosen[r['brew']]['first_drip_s'] for r in inputs]
        score = grade(inputs, endpoint, trace, pressure_end, first_drip, arm, forcing)
        score.update(sweep_metrics(constants[arm]))
        scores.append(score)
        rows, summary = onset_rows(inputs, chosen, arm)
        onset_all.extend(rows); onset_summary.extend(summary)
        # This also authenticates the original timestamps and stable-pressure convention.
        if arm != 'A0':
            D.first_drip_comparison(inputs, chosen, args.puckworks, args.raw)
    e1_score, e1_rows, e1_summary, e1_constants = reference(inputs)
    e1_score.update(sweep_metrics(e1_constants))
    scores.insert(0, e1_score)
    onset_all.extend(e1_rows); onset_summary.extend(e1_summary)
    py_traces, py_endpoints = [], []
    for source in inputs:
        p = F.parameters_for(bank, 'measured_history', source['nominal_pressure_bar'])
        values = python_trace(args.puckworks, p, source['times_s'], source['pressure_bar'])
        py_endpoints.append(float(values[-1]))
        py_traces.append(np.interp(source['trace_times_s'], source['times_s'], values))
    python_score = D.score_predictions(inputs, py_endpoints, py_traces, [r['pressure_bar'][-1] for r in inputs])
    python_score.update(arm='Python A', forcing='saved_held_out_fits',
                        **continuous_response(py_endpoints, [r['nominal_pressure_bar'] for r in inputs]))
    endpoint_rows = []
    for record in campaigns:
        source = source_by_brew.get(record['brew'])
        times = np.asarray(source['times_s']) if source else np.linspace(0., 100., 1000)
        pressure = np.asarray(source['pressure_bar']) if source else np.full(len(times), record['nominal_pressure_bar'])
        parameters = F.parameters_for(bank, record['forcing'], record['nominal_pressure_bar'])
        original = python_trace(args.puckworks, parameters, times, pressure)
        delayed = python_trace(args.puckworks, parameters, times, pressure, record['first_drip_s'])
        extra = dict(prescribed_pressure_at_100_bar=float(pressure[-1]),
            early_pressure_bar=float(np.median(pressure[times <= 2.])),
            python_original_endpoint_g_s=float(original[-1]), python_delayed_endpoint_g_s=float(delayed[-1]),
            startup_offset_g_s=float(delayed[-1]-original[-1]),
            remainder_g_s=float(record['endpoint_flow_g_s']-delayed[-1]))
        record.update(extra)
        fields = ('run','arm','forcing','brew','nominal_pressure_bar','pressure_basis','prescribed_pressure_at_100_bar',
            'endpoint_flow_g_s','first_drip_s','first_drip_right_censored','full_saturation_s','saturation_completed_step_s',
            'cumulative_outlet_liquid_mass_g','early_pressure_bar','python_original_endpoint_g_s',
            'python_delayed_endpoint_g_s','startup_offset_g_s','remainder_g_s','wall_seconds','ranks','delta_t_s',
            'balances_and_bounds_qualified','final_bed_mean_x')
        endpoint_rows.append({key:record[key] for key in fields})
    args.out.mkdir(parents=True, exist_ok=True)
    E1.write_csv(args.out/'ENDPOINTS.csv', endpoint_rows)
    E1.write_csv(args.out/'GRADES.csv', csv_safe(scores+[python_score]))
    E1.write_csv(args.out/'FIRST_DRIP_BY_BREW.csv', csv_safe(onset_all))
    E1.write_csv(args.out/'FIRST_DRIP_BY_PRESSURE.csv', csv_safe(onset_summary))
    verification = json.loads((ROOT/'docs/demonstrations/FORM_A/VERIFICATION.json').read_text())
    audit_path = args.work/'NUMERICAL_PRECISION_AUDIT.json'
    precision_audit = json.loads(audit_path.read_text()) if audit_path.exists() else dict(runs=[],total_core_hours=0.)
    for run in precision_audit['runs']:
        case = args.work.parent/run['namespace']/run['run']
        for path, key in ((case/'postProcessing/wholePull/0/traces.csv','trace_sha256'),
                          (case.with_name(case.name+'.json'),'config_sha256'),
                          (case/'system/fvSolution','fv_solution_sha256'),
                          (case.parent/run['native_checksum_index_file'],'native_checksum_index_sha256')):
            if D.digest(path) != run[key]:
                raise ValueError('Changed retained numerical-precision evidence: '+run['run'])
    manifest = dict(schema='ewp.form_a.fixed_prediction_runs.v1', change_class='GOVERNING_PHYSICS_CHANGE',
        implementation_commit='5aa1f7fefb1d3a052fc7bb726c0eecb25e7ee6cf',
        report_source_commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
        puckworks_commit=V.RUNTIME_COMMIT, executable_sha256=executable_hash,
        parameters=bank, delta_t_s=selected['delta_t_s'], time_step_selection=selected,
        time_step_studies={arm:json.loads((args.work/f'{arm}-STEP_STUDY.json').read_text()) for arm in ('A0','A1','A2')},
        xc_normalization=xc, constant_pressures_bar=F.constant_pressures(),
        linear_solver_controls=dict(A0_A1_pressure_tolerance=1e-12,A2_pressure_tolerance=1e-14,
                                    concentration_tolerance=1e-11),
        numerical_precision_audit=precision_audit,
        native_software='OpenFOAM Foundation 12; espressoWholePullFoam', ranks=32,
        scheduling='At most two cases concurrently, separate groups of 32 physical cores',
        numerical_environment=dict(python=sys.version.split()[0], **{name:importlib.metadata.version(name)
            for name in ('numpy','scipy','matplotlib')}),
        source_sha256={name:D.digest(ROOT/name) for name in
            ('solver/espressoWholePullFoam/espressoWholePullFoam.C','solver/espressoWholePullFoam/formAWholeBedClosure.H',
             'scripts/prepare_case.py','scripts/form_a_demonstration.py','scripts/form_a_report.py',
             'scripts/form_a_verification.py','scripts/e1_demonstration.py','scripts/e1_verification.py',
             'config/reference_R0.json','dependencies/puckworks.lock.json')},
        inputs_sha256={name:D.digest(args.puckworks/name) for name in
            (V.TABLE,E1.ONSET,'docs/research/PRESSURE_PEAK_STAGE_C0/RESULT_TABLE.csv',
             'docs/research/PRESSURE_PEAK_STAGE_C0/SUMMARY.md',
             'puckworks/data/waszkiewicz2025/traces_per_brew.csv',
             'puckworks/data/waszkiewicz2025/equilibrium_windows.csv')},
        source_datasets=['waszkiewicz2025/traces_per_brew','waszkiewicz2025/equilibrium_windows'],
        source_attribution='Waszkiewicz et al. (2025), Zenodo 18046315, CC-BY-4.0',
        originals=[dict(brew=r['brew'],sha256=r['original_sha256']) for r in inputs],
        raw_authentication='All 56 original file hashes agree with E1; raw stable clocks and saved B1 scores reproduced',
        trace_observer='B0c 0.1-s grid; primary onset+2 through 100 s; secondary 5 through 100 s; scoring masks only',
        bootstrap=dict(resamples=RESAMPLES,seed=SEED,unit='Paired condition-balanced whole brews; fixed predictions'),
        continuous_peak_definition='Three-point bracketed interpolation of nominal-condition means; fixed-prediction whole-brew interval. Dense constant sweeps are reported separately; no parameter uncertainty is inferred.',
        onset_pressure_reference=dict(c0_onset_only_fit_minimum_bar=4.55,
            observed_nominal_median_minimum_bar=3.5,
            source='PW PRESSURE_PEAK_STAGE_C0/RESULT_TABLE.csv and SUMMARY.md'),
        censoring='No first drip by 100 s is right-censored; onset RMSE then reports a lower bound',
        resolved_late_trends='Not scored: original D0 windows can extend beyond the E1 native 100-s support',
        scores=scores, python_held_out_score=python_score,
        campaign_runs=len(campaigns), auxiliary_native_runs=len(records)-len(campaigns),
        additional_numerical_precision_runs=len(precision_audit['runs']),
        implementation_verification=verification['native_runs'],
        native_wall_seconds=sum(r['wall_seconds'] for r in records+precision_audit['runs']),
        native_wall_seconds_definition='Sum of campaign, auxiliary and superseded/diagnostic solver elapsed times; implementation verification is recorded separately',
        native_core_hours=sum(r['core_hours'] for r in records)+precision_audit['total_core_hours']+verification['native_runs']['total_core_hours'],
        native_artifacts='External task run directory; full outputs and checksum indexes excluded from Git', runs=records)
    (args.out/'RUN_MANIFEST.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    plot_report(args, bank, inputs, constants, onset_summary)
    write_summary(args, manifest, onset_summary)
    print(json.dumps(dict(campaign_runs=len(campaigns),native_core_hours=manifest['native_core_hours']),indent=2))


def plot_report(args, bank, inputs, constants, onsets):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    conditions = np.array([r['nominal_pressure_bar'] for r in inputs])
    observed, draws = condition_draws([r['observed_endpoint_g_s'] for r in inputs], conditions)
    bounds = np.quantile(draws, [.025, .975], axis=0)
    grid = np.arange(1., 13.0001, .05)
    times = np.linspace(0., 100., 1000)
    pressure = np.repeat(grid[:, None], len(times), axis=1)
    python, _ = V.python_flow(args.puckworks, bank['DESCRIPTIVE_ALL'], times, pressure)
    colors = dict(A0='#2c7bb6', A1='#d95f02', A2='#7951a1', E1='#777777')
    fig, ax = plt.subplots(figsize=(8, 4.4), layout='constrained')
    ax.errorbar(NOMINAL, observed, yerr=np.array([observed-bounds[0], bounds[1]-observed]),
        fmt='o', color='#222222', capsize=3, markersize=4, label='Observed; 95% whole-brew interval')
    ax.plot(grid, python[:, -1], color='#238b45', linestyle='--', linewidth=1.6,
        label='Python A; saved descriptive fit')
    for arm, marker in [('A0','s'), ('A1','o'), ('A2','^')]:
        p = sorted(constants[arm])
        ax.plot(p, [constants[arm][x]['endpoint_flow_g_s'] for x in p],
            marker=marker, markersize=3, linewidth=1.3, color=colors[arm], label=arm+'; constant pressure')
    ax.set(xlabel='Nominal raw / inlet gauge pressure (bar)', ylabel='100-s endpoint flow (g/s)',
        xlim=(.7,13.3), title='Form A endpoint flow')
    ax.grid(alpha=.18); ax.legend(fontsize=8, loc='lower right')
    fig.savefig(args.out/'ENDPOINT_FLOW.png', dpi=180); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), layout='constrained')
    sample = sorted([r for r in onsets if r['arm'] == 'A1'], key=lambda r:r['nominal_pressure_bar'])
    med = np.array([r['observed_median_s'] for r in sample])
    lower = np.array([r['observed_min_s'] for r in sample]); upper = np.array([r['observed_max_s'] for r in sample])
    for ax in axes:
        ax.errorbar(NOMINAL, med, yerr=[med-lower, upper-med], fmt='o-', color='#222222', capsize=3,
            markersize=4, linewidth=1.1, label='Observed median and brew range')
        for arm in ('E1','A1','A2'):
            rows = sorted([r for r in onsets if r['arm'] == arm], key=lambda r:r['nominal_pressure_bar'])
            y = [r['solver_median_s'] if r['solver_median_s'] is not None else np.nan for r in rows]
            ax.plot(NOMINAL, y, 'o-', color=colors[arm], linewidth=1.4, markersize=3,
                label=arm+'; history median')
            if ax is axes[0]:
                for p, row in zip(NOMINAL, rows):
                    if row['solver_median_s'] is None:
                        ax.plot(p, row['solver_median_lower_bound_s'], marker='^', color=colors[arm], markersize=7)
                        ax.annotate(f">{row['solver_median_lower_bound_s']:.1f} s", (p, row['solver_median_lower_bound_s']), xytext=(7,5),
                            textcoords='offset points', fontsize=8, color=colors[arm])
        ax.set(xlabel='Nominal raw / inlet gauge pressure (bar)', ylabel='First drip on stable clock (s)')
        ax.grid(alpha=.18)
    axes[0].set(xlim=(.7,13.3), ylim=(0,None), title='First drip: full pressure range')
    axes[0].legend(fontsize=8, loc='upper right')
    axes[1].set(xlim=(3.2,13.3), ylim=(0,23), title='3.5–13 bar detail')
    fig.savefig(args.out/'FIRST_DRIP.png', dpi=180); plt.close(fig)


def write_summary(args, manifest, onsets):
    scores = {r['arm']:r for r in manifest['scores']}
    def number(value, places=3):
        return 'unresolved' if value is None else f'{value:.{places}f}'
    def interval(value, bounds, places=3):
        return number(value, places)+(f' [{number(bounds[0],places)}, {number(bounds[1],places)}]' if bounds else ' [unresolved]')
    def onset_vector(arm, observed=False):
        rows = sorted([r for r in onsets if r['arm'] == arm], key=lambda r:r['nominal_pressure_bar'])
        return ', '.join(number(r['observed_median_s'] if observed else r['solver_median_s'], 1)
                         if observed or r['solver_median_s'] is not None else f">{r['solver_median_lower_bound_s']:.1f}" for r in rows)
    table = []
    for arm in ('E1','A0','A1','A2'):
        s = scores[arm]
        residuals = '/'.join(f"{s[key]:+.3f}" for key in ('residual_1_g_s','residual_2_g_s','residual_3_5_g_s'))
        wet = number(s['fastest_wetting_bar'], 2)+('*' if s['fastest_wetting_is_sweep_boundary'] else '')
        table.append(f"| {arm}{' (constants)' if arm == 'A0' else ''} | {s['endpoint_rmse_g_s']:.3f}/{s['trace_rmse_g_s']:.3f} | "
            f"{interval(s['continuous_peak_bar'],s['continuous_peak_interval_bar'])} | "
            f"{s['slope']:.4f} | {residuals} | {onset_vector(arm)} | {wet}/{s['continuous_sweep_peak_bar']:.3f} |")
    xc = manifest['xc_normalization']
    xc_text = '/'.join(f"{r['xc']:.6f}" for r in xc['sensitivity'])
    ceiling = float(np.exp(-np.exp(-1/xc['xc_9bar'])))
    a0 = [r for r in manifest['runs'] if r['arm'] == 'A0' and r['forcing'] == 'constant'
          and r['nominal_pressure_bar'] in V.NOMINAL]
    parity = max(abs(r['remainder_g_s']) for r in a0)
    step = manifest['delta_t_s']
    differences = [r for arm in manifest['time_step_studies'].values() for r in arm['comparisons']
                   if r['pressure_bar'] in (2.,6.,11.)]
    endpoint_change = max(abs(r['endpoint_change_g_s']) for r in differences)
    onset_change = max(abs(r['first_drip_change_s']) for r in differences)
    peak_change = max(abs(r['peak_change_bar']) for r in manifest['time_step_studies'].values()
                      if r['peak_change_bar'] is not None)
    lines = ['# Form A whole-bed closure', '',
        '**capability demonstration, not validation. PHYSICAL_VALIDATION=NOT_ESTABLISHED; TARGET_EXPOSED.**', '',
        f"B1 endpoint/primary-trace RMSE: **{scores['A1']['b1_endpoint_rmse_g_s']:.3f}/{scores['A1']['b1_trace_rmse_g_s']:.3f} g/s**. "
        'Observed flow peak: **6.1 [5.9, 6.3] bar**; '
        f'[C0 onset-fit](https://github.com/trbrewer/puckworks/blob/{V.RUNTIME_COMMIT}/docs/research/PRESSURE_PEAK_STAGE_C0/SUMMARY.md) minimum: **4.55 bar** '
        '(lowest observed nominal median: **3.5 bar**).', '',
        '| Arm | Endpoint/trace RMSE, g/s | Continuous response peak [95%], bar | Slope ≥9 bar, g/s/bar | Residuals at 1/2/3.5 bar, g/s | First-drip medians, s | Fastest wetting/peak flow, bar |',
        '|---|---|---|---|---|---|---|', *table, '',
        'First-drip order: **1, 2, 3.5, 4, 5, 6, 7, 8, 9, 11, 13 bar**. Observed medians: **'+onset_vector('A1',True)+' s**. '
        '> marks a right-censored median lower bound. *Fastest tested point lies on the sweep boundary.', '',
        'A1/A2 use held-out fold parameters; A0 is descriptive constant forcing, and E1 is the unchanged transferred-median reference. '
        'Response peaks use three-point interpolation of nominal-condition history means (A0 constants); 95% intervals use 1,000 paired condition-balanced whole-brew resamples, seed 20261103, with fixed predictions. '
        'A0 therefore has a zero-width interval; none includes parameter uncertainty. The final column uses the separate dense constant sweeps.', '',
        f"**A0.** Correcting its wetting delay leaves at most {parity:.2g} g/s nominal-point difference from Python A. "
        'It isolates the transferred flow law; R0 wetting still accelerates as pressure rises.', '',
        f"**A1.** Fastest wetting is {scores['A1']['fastest_wetting_bar']:.3f} bar and peak flow is "
        f"{scores['A1']['continuous_sweep_peak_bar']:.3f} bar. Compare that separation with the reference 4.55 versus 6.1 bar; "
        'recovery remains exp(-1) before outflow.', '',
        f"**A2.** Xc at 6/9/11 bar is **{xc_text}**; the 9-bar value is used without fitting. "
        f"Because X cannot exceed one, its recovery ceiling is {ceiling:.3f}; the peak shifts "
        f"{scores['A2']['continuous_sweep_peak_bar']-scores['A1']['continuous_sweep_peak_bar']:+.3f} bar from A1, "
        'so the comparison tests both spatial variation and a bounded extraction coordinate.', '',
        '**E1.** Its saved results are unchanged. Fixed R0 wetting and the late constant-flow peak remain the reference limitations.', '',
        f"Step pair 0.0025/0.005 s at 2/6/11 bar: maximum endpoint change {endpoint_change:.2g} g/s, "
        f"first-drip change {onset_change:.2g} s; bracketed peak change {peak_change:.2g} bar. "
        f"Chosen step **{step:g} s**: {manifest['time_step_selection']['reason']} No inventory metric enters that choice.", '',
        'A2 uses a 1e−14 pressure-solve tolerance after a 1-bar concentration overshoot; '
        'the existing bounds and all physical parameters are unchanged. Superseded runs and diagnostics are retained in the manifest.', '',
        'Existing MEETS/NEAR/MISSES bands are unchanged ([grades](GRADES.csv)); no overall gate. '
        'Primary trace mask is observed onset+2–100 s; secondary 5–100 s is retained. '
        'D0 late-trend windows extending beyond native 100-s support are not scored. '
        'Censored onset RMSE is a lower bound. '
        '[Endpoint figure](ENDPOINT_FLOW.png) · [First-drip figure](FIRST_DRIP.png) · '
        '[First-drip values](FIRST_DRIP_BY_PRESSURE.csv) · [Endpoints](ENDPOINTS.csv).', '',
        f"181 campaign cases; {manifest['native_core_hours']:.2f} core-hours including auxiliary/superseded runs and implementation checks. "
        '[Manifest; native outputs outside Git](RUN_MANIFEST.json). '
        'Waszkiewicz et al. (2025), [Zenodo 18046315](https://doi.org/10.5281/zenodo.18046315), CC-BY-4.0; '
        f"PW {V.RUNTIME_COMMIT[:7]} saved D0 fits, no refitting."]
    (args.out/'SUMMARY.md').write_text('\n'.join(lines)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('puckworks', 'work', 'raw', 'executable'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--out', type=Path, default=ROOT/'docs/demonstrations/FORM_A')
    generate_report(parser.parse_args())


if __name__ == '__main__':
    main()
