#!/usr/bin/env python3
"""Fixed-fit Form A run staging. Native outputs stay outside Git; no optimizer."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

import e1_demonstration as D
import e1_verification as E1
import form_a_verification as V


def constant_pressures():
    return sorted(set(E1.NOMINAL) | {5+i/4 for i in range(13)} | {8.25, 8.5, 8.75})


def parameters_for(bank, forcing, pressure):
    if forcing == 'constant':
        return bank['DESCRIPTIVE_ALL']
    return bank[f'HYD-LOCO-{pressure:.1f}']


def execute(work, name, cfg, exe, pressure, forcing, brew='', ranks=32):
    work = work.resolve()
    if work == V.ROOT or V.ROOT in work.parents:
        raise ValueError('Native runs must remain outside Git')
    work.mkdir(parents=True, exist_ok=True)
    saved = work/(name+'.result.json')
    identity = dict(config_sha256=hashlib.sha256((json.dumps(cfg, indent=2)+'\n').encode()).hexdigest(),
                    executable_sha256=D.digest(exe))
    trace = work/name/'postProcessing/wholePull/0/traces.csv'
    if saved.exists():
        result = json.loads(saved.read_text())
        if any(result[k] != value for k, value in identity.items()) or result['trace_sha256'] != D.digest(trace):
            raise ValueError('Run reuse identity changed: '+name)
        return result
    rows, wall = V.run_case(work, name, cfg, exe, ranks)
    bounds = E1.balance_bounds(rows, cfg)
    if bounds['status'] != 'PASS':
        raise ValueError('Existing numerical balance/bounds checks exceeded: '+name)
    if min(float(r['form_a_min_cell_x_increment']) for r in rows) < 0:
        raise ValueError('Extracted cell fraction decreased: '+name)
    end = rows[-1]
    result = dict(run=name, arm=cfg['form_a_whole_bed_closure']['arm'], forcing=forcing,
        brew=brew, nominal_pressure_bar=pressure, pressure_basis='RAW_LINE_AS_INLET_GAUGE',
        parameters=cfg['form_a_whole_bed_closure'], delta_t_s=cfg['time']['delta_t_s'],
        endpoint_flow_g_s=float(end['outlet_flow_m3_s'])*cfg['liquid']['density_kg_m3']*1000,
        first_drip_s=float(end['first_drip_s']),
        first_drip_right_censored=float(end['first_drip_s']) < 0,
        cumulative_outlet_liquid_mass_g=float(end['cup_water_mass_kg'])*1000,
        final_bed_mean_x=float(end['form_a_bed_mean_x']),
        wall_seconds=wall, ranks=ranks, core_hours=wall*ranks/3600,
        trace_sha256=D.digest(trace), balances_and_bounds_qualified=True, **identity)
    saved.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)
    return result


def run_name(arm, forcing, pressure, dt, brew=''):
    return f'{arm}-{forcing}-{brew or format(pressure, "g")}-dt{dt:g}'


def run_constant(args, bank, pressure, dt, arm, xc=None, forcing='constant'):
    cfg = V.scenario(bank['DESCRIPTIVE_ALL'], arm, pressure, dt, xc=xc)
    name = run_name(arm, forcing, pressure, dt)
    return execute(args.work, name, cfg, args.executable, pressure, forcing, ranks=args.ranks)


def read_xc(args):
    if args.xc_record is None:
        raise ValueError('A2 requires --xc-record from A1 normalization')
    record = json.loads(args.xc_record.read_text())
    if record['puckworks_commit'] != V.RUNTIME_COMMIT or record['definition'] != 'A1_DESCRIPTIVE_ALL_Xbar_at_outlet_Mc':
        raise ValueError('Xc normalization identity mismatch')
    return record


def step_pair(args, bank):
    xc = read_xc(args)['xc_9bar'] if args.arm == 'A2' else None
    rows = {}
    def evaluate(pressure):
        if pressure in rows:
            return
        fine, coarse = [run_constant(args, bank, pressure, dt, args.arm, xc, 'step-study')
                        for dt in [.0025, .005]]
        rows[pressure] = dict(arm=args.arm, pressure_bar=pressure,
            endpoint_fine_g_s=fine['endpoint_flow_g_s'], endpoint_coarse_g_s=coarse['endpoint_flow_g_s'],
            endpoint_change_g_s=coarse['endpoint_flow_g_s']-fine['endpoint_flow_g_s'],
            first_drip_change_s=coarse['first_drip_s']-fine['first_drip_s'],
            fine_run=fine['run'], coarse_run=coarse['run'])
    for pressure in [2., 5.75, 6., 6.25, 11.]:
        evaluate(pressure)
    neighbors = {5.75, 6., 6.25}
    while True:
        peaks = {step: D.quadratic_peak(sorted(neighbors),
            [rows[p][f'endpoint_{step}_g_s'] for p in sorted(neighbors)]) for step in ['fine', 'coarse']}
        extra = set()
        for step, peak in peaks.items():
            if peak is None:
                top = max(neighbors, key=lambda p: rows[p][f'endpoint_{step}_g_s'])
                if top == min(neighbors) and top > 1: extra.add(top-.25)
                if top == max(neighbors) and top < 13: extra.add(top+.25)
        if not extra:
            break
        for pressure in sorted(extra): evaluate(pressure)
        neighbors |= extra
    result = dict(arm=args.arm, comparisons=[rows[p] for p in sorted(rows)], continuous_peak_bar=peaks,
        peak_change_bar=None if any(v is None for v in peaks.values()) else peaks['coarse']-peaks['fine'],
        xc=xc, executable_sha256=D.digest(args.executable),
        native_outputs='task external run directory', inventory_metric_used_for_choice=False)
    (args.work/f'{args.arm}-STEP_STUDY.json').write_text(json.dumps(result, indent=2)+'\n')


def normalize_xc(args, bank):
    values = []
    for pressure in [6., 9., 11.]:
        # The completed step pair already supplies identical constant 6/11-bar runs.
        # execute() verifies config, executable and trace hashes before reuse.
        previous = args.work/(run_name('A1', 'step-study', pressure, args.dt)+'.result.json')
        forcing = 'step-study' if previous.exists() else 'xc-normalization'
        result = run_constant(args, bank, pressure, args.dt, 'A1', forcing=forcing)
        rows = E1.records(args.work/result['run']/'postProcessing/wholePull/0/traces.csv')
        values.append(dict(pressure_bar=pressure, xc=V.xc_at_mass(rows, bank['DESCRIPTIVE_ALL']['mcG']),
            run=result['run'], trace_sha256=result['trace_sha256'], config_sha256=result['config_sha256']))
    record = dict(definition='A1_DESCRIPTIVE_ALL_Xbar_at_outlet_Mc',
        puckworks_commit=V.RUNTIME_COMMIT, parameters=bank['DESCRIPTIVE_ALL'],
        executable_sha256=D.digest(args.executable), delta_t_s=args.dt,
        xc_9bar=values[1]['xc'], sensitivity=values)
    (args.work/f'XC-dt{args.dt:g}.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2))


def select_step(args):
    if not args.reason:
        raise ValueError('Record the numerical reason for the common time step')
    reports = [args.work/f'{arm}-STEP_STUDY.json' for arm in ['A0', 'A1', 'A2']]
    for p in reports:
        study = json.loads(p.read_text())
        if study['executable_sha256'] != D.digest(args.executable):
            raise ValueError('Step study used another executable')
    selected = dict(delta_t_s=args.dt, reason=args.reason, executable_sha256=D.digest(args.executable),
        studies={p.name: D.digest(p) for p in reports}, inventory_metric_used_for_choice=False)
    (args.work/'STEP_SELECTION.json').write_text(json.dumps(selected, indent=2)+'\n')


def run_campaign(args, bank):
    selected = json.loads((args.work/'STEP_SELECTION.json').read_text())
    for name, digest in selected['studies'].items():
        if D.digest(args.work/name) != digest:
            raise ValueError('Step-study evidence changed since selection')
    if selected['executable_sha256'] != D.digest(args.executable):
        raise ValueError('Step selection used another executable')
    dt = selected['delta_t_s']
    xc = None
    if args.arm == 'A2':
        record = read_xc(args)
        if record['delta_t_s'] != dt or record['executable_sha256'] != D.digest(args.executable):
            raise ValueError('Recompute Xc at the selected time step and executable')
        xc = record['xc_9bar']
    if args.forcing == 'constant':
        for pressure in constant_pressures():
            run_constant(args, bank, pressure, dt, args.arm, xc)
    else:
        if args.arm == 'A0':
            raise ValueError('A0 has no measured-history campaign')
        inputs = json.loads((args.work/'source_inputs.json').read_text())
        for r in inputs:
            pressure = r['nominal_pressure_bar']
            cfg = V.scenario(parameters_for(bank, 'measured_history', pressure), args.arm,
                pressure, dt, xc=xc, history=(r['times_s'], r['pressure_bar']))
            execute(args.work, run_name(args.arm, 'history', pressure, dt, r['brew']), cfg,
                args.executable, pressure, 'measured_history', r['brew'], args.ranks)


# Retains E1's observer and mask checks; only the dependency identity is changed.
def source_inputs(puckworks, raw):
    """Fixed source observer/clock, saved B1 coefficients, pressure-only inputs."""
    V.saved_inputs(puckworks)
    sys.path.insert(0, str(puckworks))
    from puckworks.analysis import pressure_peak_stage_a as A
    from puckworks.analysis import pressure_peak_stage_b0 as B
    from puckworks.analysis import pressure_peak_scorecard as S
    brews = A.load_brews(puckworks/"puckworks/data/waszkiewicz2025", V.ROOT)
    source = S.select_stage("B0c", root=puckworks)["B1"][0]
    bank = S.fold_bank("B0c", source)
    course = B.load_course(brews, raw, step=.1)
    use = course.t <= 100.
    early_saved = S.onset_inputs(puckworks)
    onset_saved = {float(r["pressure condition bar"]):float(r["delay mean s"])
        for r in E1.records(puckworks/E1.ONSET) if r["check"] == "condition onset"
        and r["pressure view"] == "RAW PRIMARY" and float(r["threshold scale"]) == 1.}
    rows = []
    reference_trace_se = []
    for i, name in enumerate(brews.ids):
        original = raw/"measurements_time_dependent"/(name+".txt")
        t0,p0,m0,_ = B.raw_trace(original)
        t, p, observed_flow, _ = B.clean_course(t0,p0,m0)
        if t[-1] < 100.:
            raise ValueError("Insufficient observed support: "+name)
        early = float(np.median(p[t <= 2.]))
        # Reconstruct B0c's existing observation mask, never a model input.
        pre = (t0 >= -2.) & (t0 <= 0.)
        baseline = np.median(m0[pre]) if pre.any() else m0[0]
        onset = B.sustained_onset(t,np.interp(t,t0,m0)-baseline,observed_flow)
        if not np.isfinite(onset):
            raise ValueError("Saved B0c observation-mask onset not reproduced: "+name)
        score_mask = (course.t >= onset+2.) & (course.t <= course.ends[i])
        coef = bank[brews.fold[i]]["free"]
        b1 = float(A.predict("B1", coef, brews.pressure[i:i+1], brews.t)[0])
        b1_full = B.predict_course("B1",coef,course.pressure[i:i+1],course.t)[0][0]
        reference_trace_se.append(float(np.mean((b1_full[score_mask]-course.flow[i,score_mask])**2)))
        b1_trace = b1_full[use]
        rows.append(dict(brew=name, nominal_pressure_bar=float(brews.condition[i]),
            times_s=brews.t.tolist(), pressure_bar=brews.pressure[i].tolist(),
            early_pressure_bar=early, observed_endpoint_g_s=float(brews.target[i]),
            trace_times_s=course.t[use].tolist(), observed_trace_g_s=course.flow[i,use].tolist(),
            trace_mask=score_mask[use].tolist(), observed_onset_for_scoring_only_s=float(onset), b1_endpoint_g_s=b1,
            b1_trace_g_s=b1_trace.tolist(), b1_coefficients=coef, fold=brews.fold[i],
            original_sha256=D.digest(original)))
    for pressure in V.NOMINAL:
        actual = np.mean([r["early_pressure_bar"] for r in rows if r["nominal_pressure_bar"] == pressure])
        if not np.isclose(actual, early_saved[pressure], atol=1e-12, rtol=0):
            raise ValueError("Pressure-only early input differs from saved B0c: "+str(pressure))
        onset = np.mean([r["observed_onset_for_scoring_only_s"] for r in rows if r["nominal_pressure_bar"] == pressure])
        if not np.isclose(onset,onset_saved[pressure],atol=1e-12,rtol=0):
            raise ValueError("B0c observation mask differs from saved onset aggregate: "+str(pressure))
    reproduced = np.mean([np.sqrt(np.mean([(r["b1_endpoint_g_s"]-r["observed_endpoint_g_s"])**2
        for r in rows if r["nominal_pressure_bar"] == p])) for p in V.NOMINAL])
    if not np.isclose(reproduced, float(source["endpoint RMSE g/s"]), atol=1e-12, rtol=0):
        raise ValueError("Saved B0c B1 endpoint score not reproduced")
    trace_reproduced = np.mean([np.sqrt(np.mean(np.array(reference_trace_se)[g])) for g in brews.groups])
    if not np.isclose(trace_reproduced,float(source["full-trace RMSE g/s"]),atol=1e-12,rtol=0):
        raise ValueError("Saved B0c B1 trace score not reproduced")
    print("B1_REPRODUCED", reproduced, "BREWS",len(rows),flush=True)
    print("B1_TRACE_REPRODUCED",trace_reproduced,flush=True)
    if len(rows) != 56 or len({r["brew"] for r in rows}) != 56:
        raise ValueError("Expected the same 56 distinct E1 brews")
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=['inputs', 'step-pair', 'normalize-xc', 'select-step', 'run'])
    p.add_argument('--puckworks', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--executable', type=Path, required=True)
    p.add_argument('--arm', choices=['A0', 'A1', 'A2'], default='A1')
    p.add_argument('--forcing', choices=['constant', 'measured_history'], default='constant')
    p.add_argument('--dt', type=float, choices=[.0025, .005], default=.0025)
    p.add_argument('--xc-record', type=Path)
    p.add_argument('--ranks', type=int, default=32)
    p.add_argument('--reason')
    p.add_argument('--raw', type=Path)
    a = p.parse_args(); a.work = a.work.resolve()
    if a.work == V.ROOT or V.ROOT in a.work.parents:
        p.error('Use an external native-output directory')
    a.work.mkdir(parents=True, exist_ok=True)
    bank = V.saved_inputs(a.puckworks)
    if a.phase == 'inputs':
        if a.raw is None: p.error('inputs requires --raw')
        rows = source_inputs(a.puckworks, a.raw)
        (a.work/'source_inputs.json').write_text(json.dumps(rows)+'\n')
    elif a.phase == 'step-pair': step_pair(a, bank)
    elif a.phase == 'normalize-xc': normalize_xc(a, bank)
    elif a.phase == 'select-step': select_step(a)
    else: run_campaign(a, bank)


if __name__ == '__main__': main()
