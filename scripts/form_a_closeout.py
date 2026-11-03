#!/usr/bin/env python3
"""Reporting-only closeout of retained Form A evidence; never launches CFD."""
import csv
import json
from pathlib import Path
import sys

import numpy as np

import form_a_report as R

D, E1, F, V = R.D, R.E1, R.F, R.V
ROOT, NOMINAL = R.ROOT, R.NOMINAL
A2_DISPOSITION = ('A2 was retired after partial execution. Its increasing recovery factor cannot delay physical front arrival relative to A1 under the same prescribed pressure history. The selected extraction normalization also limits recovery to approximately 0.737, bounding the descriptive constant-pressure liquid-flow maximum at approximately 1.551 g/s. These properties make this particular arm a poor route to repairing the identified wetting and flow-scale mismatch. Its full capability campaign was not completed.')
NEXT_STEP = 'What is the smallest independently motivated change that reduces signed detector-onset errors by pressure condition, adds delay where predictions are early, and preserves the useful held-out flow performance?'


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def columns(path, names):
    with path.open() as stream:
        header = next(csv.reader(stream))
    data = np.loadtxt(path, delimiter=',', skiprows=1, usecols=[header.index(k) for k in names], ndmin=2).T
    if not np.isfinite(data).all():
        raise ValueError('Nonfinite retained trace')
    return dict(zip(names, data))


def native_observations(work, record, context):
    path = work/record['run']/'postProcessing/wholePull/0/traces.csv'
    if D.digest(path) != record['trace_sha256']:
        raise ValueError('Changed retained trace')
    if D.digest(work/(record['run']+'.json')) != record['config_sha256']:
        raise ValueError('Changed retained configuration')
    c = columns(path, ['time_s', 'cup_beverage_mass_kg'])
    return R.detector_observation(c['time_s'], c['cup_beverage_mass_kg']*1000., context)


def onset_assessment(inputs, chosen, work, contexts, arm, scope):
    """Missing evidence is unavailable; a valid non-detection is censored."""
    rows = []
    for source in inputs:
        brew = source['brew']; record = chosen.get(brew)
        row = dict(arm=arm, scope=scope, brew=brew, nominal_pressure_bar=source['nominal_pressure_bar'],
                   clock='seconds since stable pressure', observed_onset_s=source['observed_onset_for_scoring_only_s'],
                   front_arrival_s=None, front_censored=None, front_bound_s=None,
                   detector_available=False, detector_onset_s=None, detector_censored=None,
                   detector_censor_bound_s=None, unavailable_reason=None)
        if record:
            front = record['first_drip_s']
            row.update(front_arrival_s=front if front >= 0 else None, front_censored=front < 0,
                       front_bound_s=100. if front < 0 else front,
                       native_qualification_failed=not record['balances_and_bounds_qualified'],
                       native_run=record.get('run'),native_trace_sha256=record.get('trace_sha256'),
                       native_config_sha256=record.get('config_sha256'))
        try:
            if record is None or work is None:
                raise ValueError('Retained native evidence unavailable')
            detector = native_observations(work, record, contexts[brew])
            row.update(detector_available=True, detector_onset_s=detector['onset_s'],
                       detector_censored=not detector['detected'], detector_censor_bound_s=detector['censor_bound_s'],
                       detector_observation=detector)
            if detector['detected']:
                row['signed_detector_error_s'] = detector['onset_s']-row['observed_onset_s']
            row['detector_squared_error_or_bound_s2'] = ((detector['onset_s']-row['observed_onset_s'])**2
                if detector['detected'] else max(0.,detector['censor_bound_s']-row['observed_onset_s'])**2)
        except (OSError, ValueError, KeyError) as error:
            row['unavailable_reason'] = type(error).__name__+': retained evidence unavailable or invalid'
        rows.append(row)
    available = sum(r['detector_available'] for r in rows)
    score = dict(intended_brews=len(inputs), available_brews=available,
                 unavailable_brews=[r['brew'] for r in rows if not r['detector_available']], onset_grade='NOT_SCORED')
    if available == len(inputs):
        score.update(R.onset_metrics(inputs, [r['detector_onset_s'] for r in rows],
            censor_bounds=[r['detector_censor_bound_s'] for r in rows], observer='detector'))
    summaries = []
    for p in NOMINAL:
        group = [r for r in rows if r['nominal_pressure_bar'] == p]
        item = dict(arm=arm, scope=scope, nominal_pressure_bar=float(p), intended_brews=len(group),
                    available_detector_brews=sum(r['detector_available'] for r in group),
                    observed_median_s=float(np.median([r['observed_onset_s'] for r in group])))
        for name, known, bound, censor in (
            ('front', 'front_arrival_s', 'front_bound_s', 'front_censored'),
            ('detector', 'detector_onset_s', 'detector_censor_bound_s', 'detector_censored')):
            usable = all(r[censor] is not None for r in group)
            item[name+'_detected_brews'] = sum(r[censor] is False for r in group)
            item[name+'_censored_brews'] = sum(r[censor] is True for r in group)
            item[name+'_median_s'] = None; item[name+'_median_lower_bound_s'] = None
            item[name+'_censor_bounds_s'] = [r[bound] for r in group if r[censor] is True]
            if usable:
                # A bound is not an exact detection. A median is identified only
                # if each censored value's possible rank lies above its center.
                values = np.array([r[bound] if r[censor] else r[known] for r in group])
                median = float(np.median(values))
                item[name+'_median_lower_bound_s'] = median
                censored_bounds = [r[bound] for r in group if r[censor]]
                if not censored_bounds or min(censored_bounds) > sorted(values)[len(values)//2]:
                    item[name+'_median_s'] = median
        summaries.append(item)
    return score, rows, summaries


def descriptive_onset_comparison(inputs, assessments):
    """Native constant arms only; paired differences of censor-aware scores."""
    if any([r['brew'] for r in value['rows']] != [r['brew'] for r in inputs]
           or not all(r['detector_available'] for r in value['rows']) for value in assessments.values()):
        raise ValueError('Paired onset comparison requires the same complete available cohort in both arms')
    squared=np.asarray([[r['detector_squared_error_or_bound_s2'] for r in assessments[arm]['rows']]
                        for arm in ('A0','A1')])
    groups=[np.flatnonzero(np.array([r['nominal_pressure_bar'] for r in inputs])==p) for p in NOMINAL]
    draws=D.paired_rmse_draws(squared,groups,count=R.RESAMPLES,seed=R.SEED)
    a0=assessments['A0']['score'];a1=assessments['A1']['score']
    censored=a0['onset_rmse_is_lower_bound'] or a1['onset_rmse_is_lower_bound']
    paired=dict(A0_onset_rmse_s=a0['onset_rmse_s'],A1_onset_rmse_s=a1['onset_rmse_s'],
        A0_is_lower_bound=a0['onset_rmse_is_lower_bound'],A1_is_lower_bound=a1['onset_rmse_is_lower_bound'],
        paired_A1_minus_A0_s=a1['onset_rmse_s']-a0['onset_rmse_s'],
        paired_conditional_interval_s=np.quantile(draws[:,1]-draws[:,0],[.025,.975]).tolist(),
        definition=('Paired difference of computed RMSE lower bounds; not a bound or interval on the difference of unknown uncensored RMSEs'
                    if censored else 'Paired onset RMSE difference'),
        interval_scope='conditional on transferred fits; identical condition/brew draws',resamples=R.RESAMPLES,seed=R.SEED)
    table=[]
    for i,p in enumerate(NOMINAL):
        row=dict(nominal_pressure_bar=float(p),scope='native DESCRIPTIVE_ALL constants; descriptive',
                 observed_onset_median_s=assessments['A0']['summary'][i]['observed_median_s'])
        for arm in ('A0','A1'):
            item=assessments[arm]['summary'][i]
            median=item['detector_median_s'];bound=item['detector_median_lower_bound_s'];observed=item['observed_median_s']
            row.update({arm+'_detector_median_s':median,arm+'_detector_median_lower_bound_s':bound,
                arm+'_signed_median_error_s':None if median is None else median-observed,
                arm+'_signed_median_error_lower_bound_s':bound-observed,
                arm+'_detected_brews':item['detector_detected_brews'],arm+'_censored_brews':item['detector_censored_brews'],
                arm+'_front_breakthrough_s':item['front_median_s'],arm+'_front_lower_bound_s':item['front_median_lower_bound_s']})
        table.append(row)
    fastest={arm:float(min((r for r in assessments[arm]['summary'] if r['detector_median_s'] is not None),
                          key=lambda r:r['detector_median_s'])['nominal_pressure_bar']) for arm in ('A0','A1')}
    return dict(scope='Native DESCRIPTIVE_ALL constant-pressure onset comparison; descriptive; no grading changes',
        intended_brews=len(inputs),nominal_conditions=len(NOMINAL),table=table,paired=paired,
        fastest_detector_onset_nominal_bar=fastest,
        fastest_definition='Minimum detector-onset median among the eleven nominal observed-pressure conditions; grid resolution only',
        evidence={arm:dict(value,score={k:v for k,v in value['score'].items() if k!='onset_grade'})
                  for arm,value in assessments.items()})


def write_descriptive_onsets(out, result):
    E1.write_csv(out/'DESCRIPTIVE_ONSET.csv',R.csv_safe(result['table']))
    write_json(out/'DESCRIPTIVE_ONSET.json',result)
    paired=result['paired'];lo,hi=paired['paired_conditional_interval_s']
    lines=['# Native descriptive A0–A1 onset comparison','',
        'DESCRIPTIVE_ALL constant-pressure runs; descriptive, with no grading changes. '
        'The full B0c beverage-mass operator uses each original observation timestamp series on common support. '
        'Errors are simulated detector median minus observed median; times are seconds.','',
        '| Nominal bar | Observed median | A0 detector error | A1 detector error | A0 sharp front | A1 sharp front |',
        '|---|---|---|---|---|---|']
    for r in result['table']:
        values=[]
        for arm,key,bound in [('A0','signed_median_error_s','signed_median_error_lower_bound_s'),
                              ('A1','signed_median_error_s','signed_median_error_lower_bound_s'),
                              ('A0','front_breakthrough_s','front_lower_bound_s'),
                              ('A1','front_breakthrough_s','front_lower_bound_s')]:
            value=r[arm+'_'+key]
            actual=r[arm+'_'+bound] if value is None else value
            values.append(('≥' if value is None else '')+format(actual,'+.3f' if key.startswith('signed') else '.3f'))
        lines.append(f"| {r['nominal_pressure_bar']:g} | {r['observed_onset_median_s']:.3f} | "+' | '.join(values)+' |')
    lines += ['',f"Onset RMSE lower bounds: **A0 {paired['A0_onset_rmse_s']:.6f} s; A1 {paired['A1_onset_rmse_s']:.6f} s**. "
        f"Paired A1−A0 difference: **{paired['paired_A1_minus_A0_s']:+.6f} s [{lo:+.6f}, {hi:+.6f}]**, conditional on transferred fits. "
        'This is a paired difference of computed lower bounds, not a bound or interval on the unknown uncensored RMSE difference. '
        'It uses 1,000 identical condition/brew draws, seed 20261103, rather than differences of marginal intervals.','']
    for arm in ('A0','A1'):
        s=result['evidence'][arm]['score'];bounds=[r['detector_censor_bound_s'] for r in result['evidence'][arm]['rows'] if r['detector_censored']]
        lines.append(f"{arm}: {s['available_brews']}/{s['intended_brews']} available, {s['onset_detected_brews']} detected and {s['onset_censored_brews']} censored. "
            +(f"Censor bounds are {min(bounds):.3f}–{max(bounds):.3f} s; the median censor bound is {np.median(bounds):.3f} s. " if bounds else '')+
            f"Fastest detector onset on the eleven-point nominal grid: **{result['fastest_detector_onset_nominal_bar'][arm]:g} bar**.")
    lines += ['', 'The observed minimum is nominal 3.5 bar. A1 adds delay at high pressure, but still predicts onset early there; at 2 bar it increases the positive onset error. This descriptive comparison does not replace the A1 held-out history assessment. The reduced held-out A0 comparator remains hydraulic only and has no beverage detector.', '',
              '[Per-pressure values](DESCRIPTIVE_ONSET.csv) · [Per-brew operator evidence and paired results](DESCRIPTIVE_ONSET.json).']
    (out/'DESCRIPTIVE_ONSET.md').write_text('\n'.join(lines)+'\n')


def native_prediction(inputs, chosen, native):
    return dict(endpoints=[chosen[r['brew']]['endpoint_flow_g_s'] for r in inputs],
        traces=[np.interp(r['trace_times_s'], *native[chosen[r['brew']]['run']]) for r in inputs])


def hydraulic_predictions(args, bank, inputs, constants, histories, native, e1_records):
    endpoint_pressure = [r['pressure_bar'][-1] for r in inputs]
    nominal_pressure = [r['nominal_pressure_bar'] for r in inputs]
    chosen = {arm:{r['brew']:constants[arm][r['nominal_pressure_bar']] for r in inputs} for arm in ('A0','A1')}
    predictions = {'B1':dict(endpoints=[r['b1_endpoint_g_s'] for r in inputs], traces=[r['b1_trace_g_s'] for r in inputs]),
        'A0':native_prediction(inputs, chosen['A0'], native),
        'A1 descriptive':native_prediction(inputs, chosen['A1'], native),
        'A1':native_prediction(inputs, histories, native)}
    scopes = dict(B1='held-out B1 reference', A0='native in-sample DESCRIPTIVE_ALL constants',
                  A1='native ordinary-fold held-out histories')
    scopes['A1 descriptive'] = 'native in-sample DESCRIPTIVE_ALL constants'
    e1_unavailable = []
    e1_native = {}
    for source in inputs:
        brew = source['brew']; record = e1_records.get(brew)
        try:
            if not args.e1_work or not record:
                raise ValueError('E1 retained trace unavailable')
            path = args.e1_work/record['run']/'postProcessing/wholePull/0/traces.csv'
            if D.digest(path) != record['trace_sha256'] or D.digest(args.e1_work/(record['run']+'.json')) != record['config_sha256']:
                raise ValueError('E1 retained evidence hash mismatch')
            e1_native[record['run']] = D.trace_flow(path, 965.)
        except (OSError, ValueError) as error:
            e1_unavailable.append(dict(brew=brew, reason=type(error).__name__+': retained E1 evidence unavailable or invalid'))
    if not e1_unavailable:
        predictions['E1'] = native_prediction(inputs, e1_records, e1_native)
        scopes['E1'] = 'retained native E1 histories; transferred medians'
    delays = R.reduced_a0_delays(args, bank, inputs, e1_records)
    python_rows = []
    for label, delay_name in [('Python A original','original'),('Python A A0-delay','A0'),('Python A A1-delay','A1')]:
        endpoints, traces = [], []
        for source in inputs:
            brew=source['brew']; p=source['nominal_pressure_bar']
            delay = 0. if delay_name=='original' else delays[brew]['delay_s'] if delay_name=='A0' else histories[brew]['first_drip_s']
            q,mass = R.python_prediction(args.puckworks,F.parameters_for(bank,'measured_history',p),
                source['times_s'],source['pressure_bar'],delay)
            endpoints.append(float(q[-1])); traces.append(np.interp(source['trace_times_s'],source['times_s'],q))
            python_rows.append(dict(prediction=label,brew=brew,nominal_pressure_bar=p,delay_s=delay,
                endpoint_liquid_flow_g_s=float(q[-1]),outlet_liquid_mass_g=float(mass[-1]),
                beverage_detector_onset='unavailable: hydraulic reduced model only'))
        predictions[label] = dict(endpoints=endpoints,traces=traces)
        scopes[label] = ('original empirical held-out benchmark; mass starts at stable zero' if delay_name=='original' else
            'reduced A0 comparator, qualified by A0 parity; held-out; hydraulic only' if delay_name=='A0' else
            'held-out A1-delay implementation evidence; hydraulic only')
    scores=[]
    for label in ['B1','E1','A0','A1 descriptive','A1','Python A original','Python A A0-delay','Python A A1-delay']:
        if label not in predictions:
            scores.append(dict(arm=label,scope='retained E1 unavailable',intended_brews=56,
                               available_brews=56-len(e1_unavailable),accuracy_grade='NOT_SCORED'))
            continue
        prediction=predictions[label]
        scores.append(R.flow_score(inputs,prediction['endpoints'],prediction['traces'],
            nominal_pressure if label in ('A0','A1 descriptive') else endpoint_pressure,label,scopes[label]))
    paired = R.paired_comparison(inputs,predictions['A0'],predictions['A1 descriptive'],'native DESCRIPTIVE_ALL constants; descriptive')
    paired += R.paired_comparison(inputs,predictions['Python A A0-delay'],predictions['A1'],
                                 'reduced A0 comparator, qualified by A0 parity; ordinary-fold held-out')
    return scores,predictions,paired,delays,python_rows,e1_unavailable


def endpoint_diagnostics(work, record, density):
    path=work/record['run']/'postProcessing/wholePull/0/traces.csv'
    c=columns(path,['time_s','outlet_flow_m3_s','instantaneous_tds_mass_fraction','cup_beverage_mass_kg'])
    liquid=float(c['outlet_flow_m3_s'][-1]*density*1000.)
    beverage=liquid/(1.-float(c['instantaneous_tds_mass_fraction'][-1]))
    return dict(endpoint_liquid_flow_g_s=liquid,endpoint_beverage_flow_g_s=beverage,
        endpoint_beverage_minus_liquid_flow_g_s=beverage-liquid,
        endpoint_cup_beverage_mass_g=float(c['cup_beverage_mass_kg'][-1]*1000.),
        diagnostic_disposition='ungraded; scored flow is liquid rhoQ, observed flow is scale-derived beverage flow')


def cell_addressing(path):
    """Foundation 12 Int32 cell-to-global labels, independent of decomposition."""
    raw=path.read_bytes()
    match=R.re.search(rb'\n\s*(\d+)\s*\(',raw)
    if not match:raise ValueError('Missing cell addressing payload')
    count=int(match[1])
    if R.re.search(rb'format\s+binary;',raw):
        values=np.frombuffer(raw,dtype='<i4',count=count,offset=match.end()).copy()
        if not R.re.match(rb'\s*\)',raw[match.end()+count*4:]):
            raise ValueError('Invalid Int32 cell addressing payload')
    else:
        values=np.fromstring(raw[match.end():raw.index(b')',match.end())].decode(),sep=' ',dtype=int)
    if len(values)!=count or (values<0).any():raise ValueError('Invalid global cell labels')
    return values


def global_cell_volumes(probe, ranks):
    labels=[];volumes=[];hashes={}
    for i in range(ranks):
        address=probe/f'processor{i}/constant/polyMesh/cellProcAddressing'
        field=probe/f'processor{i}/10/Vc'
        ids=cell_addressing(address);value=R.internal_scalars(field,len(ids))
        labels.extend(ids.tolist());volumes.extend(value.tolist())
        for path in (address,field):hashes['probe/'+str(path.relative_to(probe))]=D.digest(path)
    if sorted(labels)!=list(range(len(labels))) or min(volumes)<=0:
        raise ValueError('Incomplete or duplicate global volume mapping')
    result=np.empty(len(labels));result[labels]=volumes
    return result,hashes


def qualification_diagnostic(args, record, observer, density):
    """Exact saved-time excess integral, plus explicit bounds at unsaved times."""
    case=args.work/record['run']; probe=args.probe_work
    cfg=json.loads((args.work/(record['run']+'.json')).read_text())
    limit=cfg['extraction']['saturation_concentration_kg_m3']
    c=columns(case/'postProcessing/wholePull/0/traces.csv',
        ['time_s','max_concentration_kg_m3','stored_water_mass_kg','cup_beverage_mass_kg'])
    excess=np.maximum(c['max_concentration_kg_m3']-limit,0.)
    mass_bound=excess*c['stored_water_mass_kg']/density*1000.
    worst=int(np.argmax(excess)); positive=np.flatnonzero(excess>0.)
    failed=np.flatnonzero(excess>record['original_concentration_check_roundoff_allowance_kg_m3'])
    result=dict(run=record['run'],brew=record['brew'],native_completed=True,qualification='FAIL',
        original_check=record['numerical_balance_bounds'],maximum_concentration_kg_m3=float(c['max_concentration_kg_m3'][worst]),
        concentration_limit_kg_m3=limit,maximum_time_s=float(c['time_s'][worst]),
        first_positive_excess_s=float(c['time_s'][positive[0]]),
        first_failed_original_check_s=float(c['time_s'][failed[0]]) if len(failed) else None,
        worst_time_excess_solute_mass_upper_bound_g=float(mass_bound[worst]),
        unsaved_time_integral='Unavailable: cell concentration fields were retained only at initial/final times. Bounds use (max concentration - limit)+ times retained pore liquid volume.',
        core_hours=record['core_hours'],detector_flag=True,
        hydraulic_retention='Included in all 56 hydraulic brews: constant viscosity and no concentration feedback; failed qualification disclosed')
    if observer and observer['detector_available'] and not observer['detector_censored']:
        obs=observer['detector_observation']; onset=obs['onset_s']
        use=(c['time_s']>=obs['observer_mass_support_start_s'])&(c['time_s']<=obs['observer_mass_support_end_s'])
        result.update(cup_beverage_mass_at_detector_onset_g=obs['cup_beverage_mass_at_onset_g'],
            excess_mass_upper_bound_at_onset_g=float(np.interp(onset,c['time_s'],mass_bound)),
            maximum_excess_mass_upper_bound_over_onset_support_g=float(mass_bound[use].max()),
            onset_mass_support_s=[obs['observer_mass_support_start_s'],obs['observer_mass_support_end_s']],
            maximum_violation_after_onset_support=bool(c['time_s'][worst]>obs['observer_mass_support_end_s']),
            first_violation_after_onset_support=bool(c['time_s'][positive[0]]>obs['observer_mass_support_end_s']))
    else:
        result['detector_onset_note']='No detected onset on available support; no onset beverage mass can be reported'
    # Authenticate the global mesh, then map Vc by global cell labels because
    # parallel decomposition can differ. This neither clips nor reruns CFD.
    integral=0.; hashes={}
    mesh_verified=all(D.digest(case/'constant/polyMesh'/name)==D.digest(probe/'constant/polyMesh'/name)
                      for name in ('points','faces','owner','neighbour'))
    volume_map, volume_hashes = global_cell_volumes(probe, record['ranks'])
    hashes.update(volume_hashes)
    for name in ('points','faces','owner','neighbour'):
        hashes['global_mesh/'+name]=D.digest(case/'constant/polyMesh'/name)
    case_ids=[]
    for i in range(record['ranks']):
        proc=case/f'processor{i}'
        address=proc/'constant/polyMesh/cellProcAddressing'
        ids=cell_addressing(address);case_ids.extend(ids.tolist())
        volumes=volume_map[ids]
        final=max((p for p in proc.iterdir() if p.is_dir() and R.re.fullmatch(r'[0-9.eE+-]+',p.name)),key=lambda p:float(p.name))
        values={k:R.internal_scalars(final/k,len(volumes)) for k in ('dissolvedConcentration','porosity','saturation')}
        integral+=float(np.sum(np.maximum(values['dissolvedConcentration']-limit,0.)*values['porosity']*values['saturation']*volumes))
        for path in [address]+[final/k for k in values]:
            hashes['case/'+str(path.relative_to(case))]=D.digest(path)
    mesh_verified=mesh_verified and sorted(case_ids)==list(range(len(volume_map)))
    result['global_mesh_and_cell_addressing_authenticated']=bool(mesh_verified)
    if mesh_verified:
        # The native trace is whole-bed; convert its sector field integral with
        # the exact logged scale used by the solver.
        rows=E1.records(case/'postProcessing/wholePull/0/traces.csv')
        scale=float(rows[-1]['straight_sided_wedge_scale'])
        result.update(final_saved_time_s=float(final.name),final_exact_excess_solute_mass_g=integral*scale*1000.,
                      final_cup_beverage_mass_g=float(c['cup_beverage_mass_kg'][-1]*1000.),field_sha256=hashes)
    else:
        result['final_exact_integral_unavailable']='Retained geometry/order could not be authenticated against probe Vc'
    return result


def run_accounting(args, records, xc):
    """One row per native execution; reused normalization cases have two roles."""
    ledger=[]
    for record in records:
        role=('primary A0' if record['arm']=='A0' else 'primary A1' if record['arm']=='A1' else 'retired A2 partial') if record['forcing'] in ('constant','measured_history') else record['forcing']
        roles=[role]
        if record['run'] in {r['run'] for r in xc['sensitivity']} and role!='xc-normalization':
            roles.append('xc-normalization (reused; no additional execution)')
        ledger.append(dict(record,namespace='campaign',roles=roles))
    probe=json.loads(args.probe_work.with_name(args.probe_work.name+'.result.json').read_text())
    ledger.append(dict(probe,namespace='a2-probe',roles=['retired A2 single 9-bar probe']))
    precision=json.loads((args.work/'NUMERICAL_PRECISION_AUDIT.json').read_text())
    for record in precision['runs']:
        ledger.append(dict(record,roles=[record['role']]))
    for namespace in ('verification','off-verification'):
        for case in sorted((args.work.parent/namespace).iterdir()):
            if not case.is_dir() or not (case/'postProcessing/wholePull/0/traces.csv').is_file():
                continue
            wall=float((case/'wall_seconds.txt').read_text())
            ledger.append(dict(run=case.name,namespace=namespace,
                roles=['implementation verification' if namespace=='verification' else 'superseded off-report wrapper; native completed'],
                native_completed=True,wall_seconds=wall,ranks=1,core_hours=wall/3600.,
                config_sha256=D.digest(case.with_name(case.name+'.json')),
                trace_sha256=D.digest(case/'postProcessing/wholePull/0/traces.csv')))
    keys=[(r['namespace'],r['run']) for r in ledger]
    if len(keys)!=len(set(keys)):
        raise ValueError('Native execution counted twice')
    actual={(namespace,p.name) for namespace in ('campaign','a2-probe','verification','off-verification','diagnostics','superseded-pressure-tolerance')
            for p in (args.work.parent/namespace).iterdir() if p.is_dir() and (p/'postProcessing/wholePull/0/traces.csv').is_file()}
    if actual!=set(keys):
        raise ValueError('Retained native executions do not reconcile with ledger: '+str(actual.symmetric_difference(keys)))
    for record in ledger:
        case=args.work.parent/record['namespace']/record['run']
        for path,key in [(case/'postProcessing/wholePull/0/traces.csv','trace_sha256'),
                         (case.with_name(case.name+'.json'),'config_sha256')]:
            if D.digest(path)!=record[key]:
                raise ValueError('Changed retained accounting evidence: '+record['run'])
        record.update(D.output_index(case))
        record['runtime_file_sha256']=D.digest(case/'wall_seconds.txt')
        record['native_log_sha256']={p.name:D.digest(p) for p in sorted(case.glob('log.*'))}
        record['native_completed']=True
    roles={}
    for record in ledger:
        primary=record['roles'][0]
        group=roles.setdefault(primary,dict(executions=0,core_hours=0.))
        group['executions']+=1;group['core_hours']+=record['core_hours']
    return ledger,roles


def final_normalization(args, bank, xc):
    """Authenticate numerical probe observations separately from the algebraic cap."""
    probe=json.loads((ROOT/'docs/demonstrations/FORM_A/A2_PROBE.json').read_text())
    for name,expected in probe['snapshot_sha256'].items():
        if D.digest(args.probe_work/name)!=expected:
            raise ValueError('Retained probe snapshot changed')
    for entry in xc['sensitivity']:
        record=json.loads((args.work/(entry['run']+'.result.json')).read_text())
        if any(record[k]!=entry[k] for k in ('trace_sha256','config_sha256')):
            raise ValueError('Normalization evidence changed')
    cap=float(np.exp(-np.exp(-1./xc['xc_9bar'])))
    p=bank['DESCRIPTIVE_ALL']
    def capacity(x):
        return p['aGPerSBar']*p['pdBar']*(-np.expm1(-(x/p['pdBar'])**p['n']))*np.exp(-x/p['pstarBar'])
    peak=V.capacity_peak(p)
    maximum=capacity(peak)
    result=dict(disposition=A2_DISPOSITION,xc_normalization=xc,
        numerical_probe_observations=probe['rows'],probe_run=probe['run'],
        probe_snapshot_sha256=probe['snapshot_sha256'],
        algebraic_limits=dict(recovery_cap=cap,capacity_peak_pressure_bar=float(peak),
            capacity_maximum_g_s=float(maximum),constant_liquid_flow_maximum_bound_g_s=float(maximum*cap),
            qualification='Algebraic bounds from X<=1; distinct from measured numerical probe observations'),
        verification_scope='Uniform saturated parity verifies the imposed lumped law; analytic/native first drip verifies the implemented front relation, not measured onset agreement')
    return result


def generate_report(args):
    sys.path.insert(0,str(args.puckworks))
    bank=V.saved_inputs(args.puckworks)
    inputs=json.loads((args.work/'source_inputs.json').read_text())
    e1_manifest=json.loads((ROOT/'docs/demonstrations/E1_CAPABILITY/RUN_MANIFEST.json').read_text())
    if len(inputs)!=56 or {r['brew']:r['original_sha256'] for r in inputs}!={r['brew']:r['sha256'] for r in e1_manifest['originals']}:
        raise ValueError('Intended cohort differs from E1 56-brew cohort')
    contexts={r['brew']:R.observation_context(r,args.raw) for r in inputs}
    selected=json.loads((args.work/'STEP_SELECTION.json').read_text())
    executable_hash=D.digest(args.executable)
    if selected['executable_sha256']!=executable_hash:
        raise ValueError('Step selection executable changed')
    for name,sha in selected['studies'].items():
        if D.digest(args.work/name)!=sha:raise ValueError('Step selection evidence changed')
    xc=json.loads((args.work/'XC-dt0.005.json').read_text())
    records=[json.loads(p.read_text()) for p in sorted(args.work.glob('*.result.json'))]
    primary=[r for r in records if r['arm'] in ('A0','A1') and r['forcing'] in ('constant','measured_history')]
    constants={arm:{r['nominal_pressure_bar']:r for r in primary if r['arm']==arm and r['forcing']=='constant'} for arm in ('A0','A1')}
    histories={r['brew']:r for r in primary if r['arm']=='A1' and r['forcing']=='measured_history'}
    if (len(primary)!=102 or any(set(constants[a])!=set(F.constant_pressures()) for a in constants)
            or set(histories)!={r['brew'] for r in inputs}):
        raise ValueError(f'Primary campaign incomplete: {len(primary)}/102; A1 histories {len(histories)}/56. A2 has no completeness requirement.')
    if args.probe_work is None:
        raise ValueError('Retained A2 probe required for accounting and normalization')
    native={}; density=965.
    for record in records:
        if record['executable_sha256']!=executable_hash:
            raise ValueError('Native executable identity changed')
        if not record['balances_and_bounds_qualified']:
            # Recover provenance/check details from existing output only.
            cfg=json.loads((args.work/(record['run']+'.json')).read_text())
            record.update(F.execute(args.work,record['run'],cfg,args.executable,record['nominal_pressure_bar'],
                          record['forcing'],record['brew'],record['ranks'],recover_completed=True))
        native[record['run']]=R.read_native(args.work,record,density)
        if record['forcing'] in ('constant','measured_history'):
            expected=F.parameters_for(bank,record['forcing'],record['nominal_pressure_bar'])
            if record['delta_t_s']!=selected['delta_t_s'] or any(record['parameters'][k]!=v for k,v in expected.items()):
                raise ValueError('Campaign transfer parameters or time step changed')
        record['numerical_sanity']=D.final_field_sanity(args.work/record['run'])
        record['numerical_sanity'].pop('positive_e1_multiplier')
        if not record['numerical_sanity']['finite_values']:
            raise ValueError('Nonfinite final fields')
        record.update(endpoint_diagnostics(args.work,record,density))
    e1_records={r['brew']:r for r in e1_manifest['runs'] if r['forcing']=='measured_history'}
    scores,predictions,paired,delays,python_rows,e1_unavailable=hydraulic_predictions(args,bank,inputs,constants,histories,native,e1_records)
    onsets=[]; onset_rows=[]; onset_scores={}; assessments={}
    for arm,chosen,work,scope in [
        ('A0',{r['brew']:constants['A0'][r['nominal_pressure_bar']] for r in inputs},args.work,'native DESCRIPTIVE_ALL constants; descriptive'),
        ('A1',histories,args.work,'native ordinary-fold held-out histories'),
        ('E1',e1_records,args.e1_work,'retained native E1 histories')]:
        score,rows,summary=onset_assessment(inputs,chosen,work,contexts,arm,scope)
        onset_scores[arm]=score;onset_rows.extend(rows);onsets.extend(summary)
        assessments[arm]=dict(score=score,rows=rows,summary=summary)
    constant_chosen={r['brew']:constants['A1'][r['nominal_pressure_bar']] for r in inputs}
    score,rows,summary=onset_assessment(inputs,constant_chosen,args.work,contexts,'A1','native DESCRIPTIVE_ALL constants; descriptive')
    descriptive_onset=descriptive_onset_comparison(inputs,dict(A0=assessments['A0'],A1=dict(score=score,rows=rows,summary=summary)))
    for score in scores:
        if score['arm'] in onset_scores:score.update(onset_scores[score['arm']])
    qualification=[]
    for record in records:
        if not record['balances_and_bounds_qualified']:
            observer=next((r for r in onset_rows if r['arm']==record['arm'] and r['brew']==record['brew']),None)
            qualification.append(qualification_diagnostic(args,record,observer,density))
    endpoint_rows=[]
    for record in primary:
        source=next((r for r in inputs if r['brew']==record['brew']),None)
        times=np.asarray(source['times_s']) if source else np.linspace(0.,100.,1001)
        pressure=np.asarray(source['pressure_bar']) if source else np.full(len(times),record['nominal_pressure_bar'])
        params=F.parameters_for(bank,record['forcing'],record['nominal_pressure_bar'])
        original=R.python_prediction(args.puckworks,params,times,pressure)[0]
        delayed=R.python_prediction(args.puckworks,params,times,pressure,record['first_drip_s'])[0]
        record.update(python_original_endpoint_g_s=float(original[-1]),python_delay_matched_endpoint_g_s=float(delayed[-1]),
                      native_minus_delay_matched_g_s=float(record['endpoint_flow_g_s']-delayed[-1]))
        endpoint_rows.append({k:v for k,v in record.items() if not isinstance(v,(dict,list))})
    constant_comparison=[dict(pressure_bar=p,A0_flow_g_s=constants['A0'][p]['endpoint_flow_g_s'],
        A1_flow_g_s=constants['A1'][p]['endpoint_flow_g_s'],
        A1_minus_A0_flow_g_s=constants['A1'][p]['endpoint_flow_g_s']-constants['A0'][p]['endpoint_flow_g_s'],
        A0_front_s=constants['A0'][p]['first_drip_s'],A1_front_s=constants['A1'][p]['first_drip_s'],
        scope='native DESCRIPTIVE_ALL constant; descriptive') for p in F.constant_pressures()]
    e1_constants={r['nominal_pressure_bar']:r for r in e1_manifest['runs'] if r['forcing']=='constant'}
    peaks={a:R.sweep_metrics(c) for a,c in dict(constants,E1=e1_constants).items()}
    peaks['definition']='Finite 100-s endpoint sweeps; bracketed three-point quadratic interpolation, 0.25-bar local spacing. No statistical solver peak interval. Time-step sensitivity is separate.'
    peaks['D0_capacity']=dict(pressure_bar=5.9985611853692165,parameter_refit_interval_bar=[5.769910854571623,6.272472184514531],
                              definition='Saved D0 capacity optimum and parameter-refit interval; not a solver resampling interval')
    normalization=final_normalization(args,bank,xc)
    ledger,roles=run_accounting(args,records,xc)
    postprocessing=json.loads((args.probe_work.parent/'postprocessing.json').read_text())
    studies={a:json.loads((args.work/f'{a}-STEP_STUDY.json').read_text()) for a in ('A0','A1','A2')}
    partial=[r for r in records if r['arm']=='A2' and r['forcing'] in ('constant','measured_history')]
    hold=json.loads((args.work/'A2_OWNER_HOLD.json').read_text())
    held=hold['unstarted_case_sentinels']
    if len(held)!=69 or any(not (args.work/Path(name).name).is_file() for name in held):
        raise ValueError('Retired A2 held cases do not reconcile with retained sentinels')
    manifest=dict(schema='ewp.form_a.fixed_prediction_runs.v2',change_class='GOVERNING_PHYSICS_CHANGE',
        puckworks_commit=V.RUNTIME_COMMIT,executable_sha256=executable_hash,parameters=bank,
        intended_primary_cases=102,completed_primary_cases=len(primary),intended_history_brews=56,available_history_brews=len(histories),
        primary_matrix=dict(A0_constants=23,A1_constants=23,A1_histories=56),
        A2_disposition='retired after partial execution; no capability grade',A2_completed_campaign_cases=len(partial),
        A2_unstarted_held_cases=len(held),A2_held_run_names=[Path(name).name for name in held],
        A2_hold_record_sha256=D.digest(args.work/'A2_OWNER_HOLD.json'),A2_retained_campaign_runs=[r['run'] for r in partial],
        delta_t_s=selected['delta_t_s'],time_step_selection=selected,time_step_studies=studies,
        input_sha256=dict(D0_saved_fits=D.digest(args.puckworks/V.TABLE),source_inputs=D.digest(args.work/'source_inputs.json'),
            B0_observer_source=D.digest(args.puckworks/'puckworks/analysis/pressure_peak_stage_b0.py')),
        native_software='OpenFOAM Foundation 12; unchanged candidate executable',
        implementation_commit='5aa1f7fefb1d3a052fc7bb726c0eecb25e7ee6cf',
        numerical_environment=dict(python=sys.version.split()[0],**{n:R.importlib.metadata.version(n) for n in ('numpy','scipy','matplotlib')}),
        source_attribution='Waszkiewicz et al. (2025), Zenodo 18046315, CC-BY-4.0',
        originals=[dict(brew=r['brew'],sha256=r['original_sha256']) for r in inputs],
        observed_operator_replay_max_difference_s=max(abs(c['observed_operator_difference_s']) for c in contexts.values()),
        detector='B0c full operator: common native/source support, original timestamps, beverage mass baseline, gradient, 31-sample/order-1 Savitzky-Golay, strict thresholds and sustained interval start',
        detector_censor='latest retained sampled t_j with T_last-t_j >= 2 s; non-detection is a bound, missing/corrupt evidence unavailable',
        front_censor='100 s, descriptive only; superseded A0 front-versus-onset RMSE 8.627208878837111 s has no grade',
        hydraulic_scoring='liquid rhoQ versus observed scale-derived beverage flow; original E1 primary onset+2–100 s and companion 5–100 s masks',
        endpoint_beverage_difference='ungraded diagnostic; retained separately in ENDPOINTS.csv',
        bootstrap=dict(resamples=R.RESAMPLES,seed=R.SEED,unit='paired condition-balanced whole brews',interval_scope='conditional on transferred fits'),
        slope_definition='Inherited regression of 9/11/13-bar condition mean flows on condition mean endpoint pressures; nominal pressures for constant forcing',
        peaks=peaks,scores=scores,onset_scores=onset_scores,paired_comparisons=paired,
        native_descriptive_onset_comparison=descriptive_onset['paired'],reduced_A0_delay_evidence=delays,
        E1_evidence=dict(manifest_sha256=D.digest(ROOT/'docs/demonstrations/E1_CAPABILITY/RUN_MANIFEST.json'),
                         native_trace_sha256={k:v['trace_sha256'] for k,v in e1_records.items()},unavailable=e1_unavailable,
                         rerun=False,modified=False,core_hours_excluded_from_this_task=True),
        qualification_failures=qualification,normalization_record='VERIFICATION_FINAL.json',
        follow_up_outside_this_PR='Consider a relative tolerance on the concentration-bound check; no successor implementation in this PR',
        run_roles=roles,native_execution_count=len(ledger),native_core_hours=sum(r['core_hours'] for r in ledger),
        geometry_postprocessing=postprocessing,total_core_hours=sum(r['core_hours'] for r in ledger)+postprocessing['core_hours'],
        runs=ledger,native_outputs='Retained outside Git; no native evidence deleted; no runtime caps',
        source_sha256={str(p.relative_to(ROOT)):D.digest(p) for p in [ROOT/'scripts'/n for n in
            ('form_a_closeout.py','form_a_report.py','form_a_demonstration.py','form_a_verification.py','e1_demonstration.py','e1_verification.py')]
            +[ROOT/'solver/espressoWholePullFoam/formAWholeBedClosure.H',ROOT/'solver/espressoWholePullFoam/espressoWholePullFoam.C']})
    args.out.mkdir(parents=True,exist_ok=True)
    for name,data in [('ENDPOINTS.csv',endpoint_rows),('GRADES.csv',scores),('FIRST_DRIP_BY_BREW.csv',onset_rows),
        ('FIRST_DRIP_BY_PRESSURE.csv',onsets),('PAIRED_COMPARISONS.csv',paired),('CONSTANT_COMPARISONS.csv',constant_comparison),
        ('PYTHON_PREDICTIONS.csv',python_rows)]:E1.write_csv(args.out/name,R.csv_safe(data))
    write_descriptive_onsets(args.out,descriptive_onset)
    write_json(args.out/'VERIFICATION_FINAL.json',normalization)
    write_json(args.out/'QUALIFICATION_FAILURES.json',qualification)
    write_json(args.out/'RUN_MANIFEST.json',manifest)
    plot_report(args,inputs,constants,partial,normalization,onsets,bank)
    write_summary(args,manifest,onsets)
    write_methods(args,manifest,onsets)
    print(json.dumps(dict(primary_cases=len(primary),A2_partial=len(partial),native_executions=len(ledger),
                          total_core_hours=manifest['total_core_hours'],onset_scores=onset_scores),indent=2))


def plot_report(args, inputs, constants, partial, normalization, onsets, bank):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors=dict(A0='#4477aa',A1='#228833',E1='#aa3377',A2='#cc6677')
    fig,ax=plt.subplots(figsize=(8,4.8),layout='constrained')
    groups=[[r['observed_endpoint_g_s'] for r in inputs if r['nominal_pressure_bar']==p] for p in NOMINAL]
    means=np.array([np.mean(g) for g in groups])
    ax.errorbar(NOMINAL,means,yerr=[means-[min(g) for g in groups],[max(g) for g in groups]-means],
                fmt='ko',capsize=3,markersize=4,label='Observed beverage flow: mean and brew range')
    pressure=np.linspace(1.,13.,241);times=np.linspace(0.,100.,1001)
    q=V.python_flow(args.puckworks,bank['DESCRIPTIVE_ALL'],times,np.broadcast_to(pressure[:,None],(len(pressure),len(times))))[0][:,-1]
    ax.plot(pressure,q,'--',color='#666666',label='Python A: DESCRIPTIVE_ALL, no wetting delay')
    for arm in ('A0','A1'):
        p=sorted(constants[arm]);flow=[constants[arm][x]['endpoint_flow_g_s'] for x in p]
        ax.plot(p,flow,'o-',color=colors[arm],markersize=3,label=arm+': native DESCRIPTIVE_ALL, 100 s')
    ax.scatter([r['nominal_pressure_bar'] for r in partial],[r['endpoint_flow_g_s'] for r in partial],
               marker='x',color=colors['A2'],label='A2: retained partial execution, ungraded')
    probe=normalization['numerical_probe_observations'][-1]
    ax.scatter([9.],[probe['A2_flow_g_s']],marker='s',facecolors='none',edgecolors=colors['A2'],label='A2: single 9-bar probe')
    ax.set(xlabel='Nominal inlet gauge pressure (bar)',ylabel='Endpoint flow (g/s)',title='Finite-time endpoint sweep; original observed cohort')
    ax.grid(alpha=.2);ax.legend(fontsize=8,loc='lower right')
    fig.savefig(args.out/'ENDPOINT_FLOW.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(10,7),layout='constrained')
    observed=[np.median([r['observed_onset_for_scoring_only_s'] for r in inputs if r['nominal_pressure_bar']==p]) for p in NOMINAL]
    for j,name in enumerate(('front','detector')):
        for k in range(2):
            ax=axes[j,k];ax.plot(NOMINAL,observed,'ko-',linewidth=1,markersize=3,label='Observed B0c onset median')
            for arm in ('E1','A0','A1'):
                rows=sorted([r for r in onsets if r['arm']==arm],key=lambda r:r['nominal_pressure_bar'])
                y=[r[name+'_median_s'] if r[name+'_median_s'] is not None else np.nan for r in rows]
                ax.plot(NOMINAL,y,'o-',color=colors[arm],linewidth=1.2,markersize=3,
                        label=arm+(' constants, descriptive' if arm=='A0' else ' histories'))
                for p,r in zip(NOMINAL,rows):
                    bound=r[name+'_median_lower_bound_s']
                    if r[name+'_median_s'] is None and bound is not None:
                        ax.scatter(p,bound,marker='^',color=colors[arm],s=40)
            ax.set(xlabel='Nominal pressure (bar)',ylabel='Stable-clock time (s)',
                title=('Sharp front (descriptive)' if name=='front' else 'B0c beverage-mass detector')+(' — all 11 conditions' if k==0 else ' — 3.5–13 bar detail'),
                xlim=(.7,13.3) if k==0 else (3.2,13.3),ylim=(0,105) if k==0 else (0,23))
            ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=7);axes[1,0].text(.04,.95,'▲ median lower bound; missing evidence is omitted',transform=axes[1,0].transAxes,fontsize=7,va='top')
    fig.savefig(args.out/'FIRST_DRIP.png',dpi=180);plt.close(fig)


def fmt(value, digits=3):
    return 'unavailable' if value is None else f'{value:.{digits}f}'


def write_summary(args, manifest, onsets):
    scores={s['arm']:s for s in manifest['scores']};a1=scores['A1'];peaks=manifest['peaks']
    rows=[]
    labels={'B1':'B1 held-out','E1':'E1 retained','A0':'A0 in-sample','A1':'A1 held-out',
            'Python A original':'Python A original held-out','Python A A0-delay':'Python A A0-delay¹','Python A A1-delay':'Python A A1-delay¹'}
    for label,caption in labels.items():
        s=scores[label]
        if 'endpoint_rmse_g_s' not in s:
            rows.append(f'| {caption} | unavailable | unavailable | unavailable |');continue
        residual='/'.join(f'{s[k]:+.3f}' for k in ('residual_1_g_s','residual_2_g_s','residual_3_5_g_s'))
        rows.append(f"| {caption} | {s['endpoint_rmse_g_s']:.3f}/{s['trace_rmse_g_s']:.3f}/{s['startup_inclusive_trace_rmse_g_s']:.3f} | {s['slope']:.4f} | {residual} |")
    onset=[]
    for arm in ('A0','A1','E1'):
        s=manifest['onset_scores'][arm]
        onset.append(arm+': '+('≥' if s.get('onset_rmse_is_lower_bound') else '')+fmt(s.get('onset_rmse_s'),2)+
                     f" s ({s.get('onset_detected_brews',0)}/56 detected; {s['onset_grade']})")
    paired=[r for r in manifest['paired_comparisons'] if r['metric']=='endpoint']
    differences=[]
    for row,label in zip(paired,('native descriptive','reduced held-out')):
        lo,hi=row['paired_interval_g_s']
        differences.append(f"{label} {row['A0_rmse_g_s']:.3f}→{row['A1_rmse_g_s']:.3f}, Δ {row['A1_minus_A0_g_s']:+.3f} [{lo:+.3f}, {hi:+.3f}]")
    byp={r['nominal_pressure_bar']:r for r in onsets if r['arm']=='A1'}
    onset6=byp[6.]['detector_median_s'];onset13=byp[13.]['detector_median_s']
    increase=100*(onset13/onset6-1.) if onset6 is not None and onset13 is not None else None
    diagnostic=max(r['endpoint_beverage_minus_liquid_flow_g_s'] for r in manifest['runs'] if 'primary A1' in r['roles'])
    lines=['# Form A whole-bed closure','',
        '**capability demonstration, not validation. PHYSICAL_VALIDATION=NOT_ESTABLISHED; TARGET_EXPOSED.**','',
        f"**Held-out A1 endpoint/primary-trace RMSE: {a1['endpoint_rmse_g_s']:.3f}/{a1['trace_rmse_g_s']:.3f} g/s; B1: {a1['b1_endpoint_rmse_g_s']:.3f}/{a1['b1_trace_rmse_g_s']:.3f}.** "
        'This transfers form A, the selected four-parameter primary candidate (accuracy vs B1: NEAR / UNRESOLVED).','',
        '| Prediction | Endpoint/primary/companion RMSE, g/s | ≥9-bar slope | Residuals 1/2/3.5 bar, g/s |',
        '|---|---|---|---|',*rows,'',
        'A0 is DESCRIPTIVE_ALL in-sample; its score is not a like-for-like gain over B1. ¹Delayed held-out curves explain wetting offsets; the A0-delay curve is the reduced A0 comparator, qualified by A0 parity, with hydraulic quantities only. '
        'Scored flow is liquid ρQ; observed flow is scale-derived beverage flow. '
        f'The largest A1 endpoint beverage-minus-ρQ difference is {diagnostic:.2g} g/s (ungraded).','',
        '**Paired A1−A0 endpoint RMSE:** '+'; '.join(differences)+' g/s. Intervals are conditional on transferred fits; [all three paired scores](PAIRED_COMPARISONS.csv) use identical condition/brew draws.','',
        f"**Peaks:** D0 capacity **6.00 [5.77, 6.27] bar** (parameter-refit interval); finite 100-s solver sweeps: A0 **{peaks['A0']['continuous_sweep_peak_bar']:.3f}**, A1 **{peaks['A1']['continuous_sweep_peak_bar']:.3f}**, E1 **{peaks['E1']['continuous_sweep_peak_bar']:.3f} bar** (0.25-bar interpolation, not statistical intervals). "
        f"Nominal peak grades A0/A1/E1: {scores['A0']['peak_grade']}/{a1['peak_grade']}/{scores['E1'].get('peak_grade','unavailable')}. "
        f"A1 fastest physical wetting is {peaks['A1']['fastest_wetting_bar']:.3f} bar: the same capacity fixes both optima. "
        "Observed fastest onset at nominal 3.5 bar; C0's 4.55 bar is a fitted-curve median.",'',
        '**Detector onset:** '+'; '.join(onset)+'. '
        f"Observed 6→13-bar onset increases **41.6%**; A1 measured-history detector medians are **{fmt(onset6,2)}→{fmt(onset13,2)} s ({fmt(increase,1)}%)**. "
        'Censor bounds use actual last confirmable timestamps, not 100 s. Old A0 front RMSE 8.63 s is superseded and ungraded; [all eleven medians](FIRST_DRIP_BY_PRESSURE.csv).','',
        'The uniform saturated solver reproduced the imposed lumped law. A0 retains pressure-accelerated R0 wetting; A1 leaves recovery at exp(−1) until outflow. The 6.57e−14 s analytic/native first-drip match verifies the implemented relation, not agreement with measured onset.','',
        A2_DISPOSITION,'',
        f"All **102 primary cases** completed; {len(manifest['qualification_failures'])} A1 concentration-bound qualification failures are retained without excluding hydraulic brews. "
        f"The common 0.005-s step follows the 0.0025/0.005-s study; no inventory gate. {manifest['native_execution_count']} retained native executions, {manifest['total_core_hours']:.2f} core-hours including geometry postprocessing; native outputs remain outside Git. "
        '[Methods, qualifications and captions](METHODS.md) · [grades](GRADES.csv) · [manifest](RUN_MANIFEST.json).','',
        '**Next-step question (outside this PR):** '+NEXT_STEP]
    (args.out/'SUMMARY.md').write_text('\n'.join(lines)+'\n')


def write_methods(args, manifest, onsets):
    score={s['arm']:s for s in manifest['scores']};normal=json.loads((args.out/'VERIFICATION_FINAL.json').read_text())
    lines=['# Form A reporting definitions and retained evidence','',
        'This closeout performs no refit or CFD rerun. It uses Waszkiewicz et al. (2025), '
        '[Zenodo 18046315](https://doi.org/10.5281/zenodo.18046315), CC-BY-4.0, with the same 56 source hashes and masks as E1. '
        f"Saved tuples come from [PW D0](https://github.com/trbrewer/puckworks/blob/{V.RUNTIME_COMMIT}/{V.TABLE}).",'',
        'The primary matrix is 23 A0 constants plus 23 A1 constants and 56 A1 histories. A2 has ten retained campaign constants, one probe, its step studies and superseded numerical diagnostics; 69 held cases were never started. A2 has no capability grade. Every execution is counted once in the manifest; reused Xc normalization cases carry a second role without additional core-hours. Historical E1 runs are references, excluded from new-task core-hours.','',
        '## Observation and censoring','',
        'Each raw trace is authenticated against the original E1 hash. PW raw_trace establishes the stable-pressure clock; clean_course and sustained_onset reproduce the original observed onset exactly. Simulated cup beverage mass is resampled onto the original timestamps on common native/source support before mass-to-flow differentiation and the 31-sample, order-1 Savitzky–Golay filter. Initial zero cup mass is the retained fresh-start state at time zero; terminal mass is never extended. The detector requires strict mass >0.5 g and flow >0.1 g/s continuously for at least 2 s and reports the interval start. Form A M remains outlet liquid grams.','',
        'A valid trace with no confirmed interval is censored at the latest retained sampled t_j satisfying T_last−t_j≥2 s. Its squared-error contribution is max(0,c_i−observed_i)². Missing/corrupt evidence is unavailable, never a censored brew. Coverage is explicit; an incomplete cohort receives no 56-brew score. Any censor makes the RMSE a lower bound: existing MISSES applies only when that bound exceeds 4.53 s; otherwise NOT_SCORED/unresolved. Intervals for a bound are labeled as such. Front arrival is a separate descriptive quantity, with its own 100-s censor.','',
        '| Arm | Available/intended | Detected | Censored | RMSE or lower bound, s | 95% interval | Grade |',
        '|---|---|---|---|---|---|---|']
    for arm,s in manifest['onset_scores'].items():
        bounds=s.get('onset_rmse_interval_s');ci='unavailable' if bounds is None else f'[{bounds[0]:.3f}, {bounds[1]:.3f}]'
        lines.append(f"| {arm} | {s['available_brews']}/{s['intended_brews']} | {s.get('onset_detected_brews',0)} | {s.get('onset_censored_brews',0)} | {'≥' if s.get('onset_rmse_is_lower_bound') else ''}{fmt(s.get('onset_rmse_s'))} | {ci} | {s['onset_grade']} |")
    lines += ['', 'The separate [native descriptive onset comparison](DESCRIPTIVE_ONSET.md) reports A0/A1 constants, signed condition errors, sharp fronts, grid minima and paired differences of censor-aware RMSE lower bounds. It does not change grades.', '', 'All intervals above are conditional on transferred fits; intervals in censored rows describe the RMSE lower bound. Per-brew censor bounds, observation timestamp hashes, detector support and eleven condition medians appear in the onset CSVs. The old A0 front-versus-observed-onset RMSE 8.627208878837111 s is preserved solely as a superseded diagnostic, with no grade.', '',
        '## Hydraulic comparisons and peaks','',
        'Endpoint/trace scoring remains liquid ρQ against scale-derived observed beverage flow. Native instantaneous beverage flow is ρQ/(1−instantaneous TDS); its endpoint difference from ρQ is an ungraded ENDPOINTS.csv diagnostic. Detector flow instead comes from differentiation/filtering of the resampled beverage mass.','',
        'The empirical Python A prediction starts M at stable-pressure zero. Its recomputed held-out endpoint score is '
        f"{score['Python A original']['endpoint_rmse_g_s']:.12f} g/s. The two delayed evaluators use ordinary-fold tuples and preserve the original absolute pressure times. The A0 delay is authenticated against retained E1 geometry, initial state, pressure history and clock, with the unchanged R0 front integral as fallback. A1 delay is used only for the A1-delay evaluator. The reduced A0 comparator has no beverage mass, solute history or detector onset.",'',
        'Primary trace masks are observed onset+2 through 100 s; companion masks are 5 through 100 s. B1, E1, native A0/A1 and all three Python predictions share these masks. D0 full-support trace scores are not substituted. Late-trend windows beyond native support remain unscored. The slope is the inherited regression through the 9/11/13 condition means (mean actual endpoint pressure for histories, nominal for constants). Individual residuals at 1, 2 and 3.5 bar remain visible.','',
        'PAIRED_COMPARISONS.csv reports both scores and A1−A0 for endpoint, primary trace and companion trace. Native DESCRIPTIVE_ALL constants are descriptive: the eleven nominal constants are compared with their 56 observed brews; CONSTANT_COMPARISONS.csv retains differences at all 23 native pressures. The held-out comparison uses the reduced A0 comparator, qualified by A0 parity. Each interval is computed from paired differences on the same condition and whole-brew draws: 1,000 resamples, seed 20261103, conditional on transferred fits. Differences of marginal intervals are never used.','',
        'D0 capacity peak 5.998561 [5.769911, 6.272472] bar uses saved parameter refits. Solver endpoint peaks use a finite 100-s constant sweep and bracketed three-point quadratic interpolation at 0.25-bar spacing; no statistical interval is inferred for a deterministic sweep. The nominal peak grade is separate and uses E1’s unchanged condition-resample bands. These uncertainty concepts are not interchangeable.','',
        '| Arm | Peak at dt=0.0025 / 0.005 s, bar | Maximum endpoint change at 2/6/11, g/s | Maximum front change at 2/6/11, s |',
        '|---|---|---|---|']
    for arm,s in manifest['time_step_studies'].items():
        rows=[r for r in s['comparisons'] if r['pressure_bar'] in (2.,6.,11.)]
        lines.append(f"| {arm} | {s['continuous_peak_bar']['fine']:.9f} / {s['continuous_peak_bar']['coarse']:.9f} | {max(abs(r['endpoint_change_g_s']) for r in rows):.9g} | {max(abs(r['first_drip_change_s']) for r in rows):.9g} |")
    lines += ['', 'The pre-campaign study selected 0.005 s because these reported quantities were stable under halving the step; no extractable-inventory gate was used. A0/A1 controls are unchanged. A2’s earlier pressure-tolerance diagnostics and every superseded run remain separately accounted for.', '',
        '## Retained failed qualifications','',
        'The original concentration check remains failed. Recovery reads retained config, traces, logs, runtime and hashes; it records native completion separately from numerical qualification, without rerunning, clipping or relaxing a bound. All 56 A1 histories remain in the hydraulic assessment because viscosity is constant and concentration does not feed back into A1 permeability.','',
        '| Brew | Maximum C versus 180 kg/m³ | Worst time, s | Exact final excess solute, g | Worst-time excess upper bound, g | Beverage mass at detector onset, g | Excess bound over onset support, g |',
        '|---|---|---|---|---|---|---|']
    timing_notes=[]
    for q in manifest['qualification_failures']:
        lines.append(f"| {q['brew']} | {q['maximum_concentration_kg_m3']:.12f} | {q['maximum_time_s']:.3f} | {q.get('final_exact_excess_solute_mass_g','unavailable')} | {q['worst_time_excess_solute_mass_upper_bound_g']:.6g} | {q.get('cup_beverage_mass_at_detector_onset_g','unavailable')} | {q.get('maximum_excess_mass_upper_bound_over_onset_support_g','unavailable')} |")
        if 'onset_mass_support_s' in q:
            timing_notes.append(f"Brew {q['brew']}: onset mass support {q['onset_mass_support_s'][0]:.3f}–{q['onset_mass_support_s'][1]:.3f} s; first positive excess {q['first_positive_excess_s']:.3f} s, worst excess {q['maximum_time_s']:.3f} s. First/worst violation after support: {q['first_violation_after_onset_support']}/{q['maximum_violation_after_onset_support']}.")
    lines += ['', *timing_notes, '', 'Exact final excess mass integrates max(C−180,0) over cell pore liquid volume, using retained final porosity/saturation fields, authenticated global cell addressing and the probe’s saved geometric cell volumes. Cell fields were not saved at every intermediate time: an exact integral at an unsaved worst/onset timestamp is unavailable. The reported upper bound there is max(C_max−180,0) times the retained total pore liquid volume. Zero over the observer support implies zero excess integral there. These reporting calculations neither modify concentration nor change qualification. Follow-up outside this PR: consider a relative tolerance on the concentration-bound check.', '',
        '## Probe and figure captions','',A2_DISPOSITION,'',
        f"Xc at 6/9/11 bar is 0.8294438807 / 0.8422833432 / 0.8524326302. The [final normalization record](VERIFICATION_FINAL.json) separates the algebraic recovery cap {normal['algebraic_limits']['recovery_cap']:.9f} from the probe’s numerical observations. The 9-bar A2/A1 flow ratios at 10/20/40/60/100 s are "+' / '.join(f"{r['A2_over_A1_flow_ratio']:.6f}" for r in normal['numerical_probe_observations'])+'.','',
        '**Endpoint figure:** Observed means/ranges use scale-derived beverage flow; Python A, A0 and A1 show DESCRIPTIVE_ALL liquid-flow predictions at 100 s. Python original has no wetting delay. A2 markers are retained partial constants and its single 9-bar probe, not a completed sweep or grade. Connecting lines do not supply an uncertainty interval.','',
        '**Onset figure:** All eleven nominal medians appear in full-range panels; right panels expand 3.5–13 bar. Sharp-front arrival is descriptive, plotted against observed detector onset for context. The lower panels use the full B0c beverage-mass operator. A0 constants are descriptive; E1/A1 use measured histories. Triangles indicate median lower bounds from actual censor times (front bounds remain 100 s); unavailable evidence is omitted and its coverage reported. A2 is retired and receives no completed onset curve or grade.','',
        '[Endpoint flow](ENDPOINT_FLOW.png) · [Front and detector onset](FIRST_DRIP.png) · [Probe observations](A2_PROBE.csv) · [Qualification details](QUALIFICATION_FAILURES.json).']
    (args.out/'METHODS.md').write_text('\n'.join(lines)+'\n')
