"""Interval metrics and separately reported empirical numerical estimates."""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.sci_md_rheology_002.run import rows, CASES, DOC
from tools.sci_md_rheology_001.analysis import write


def errors(q,r,dt):
    q,r,dt=map(np.asarray,(q,r,dt))
    if q.shape!=r.shape or q.shape!=dt.shape or np.any(r<=0) or np.any(dt<=0) or not all(np.all(np.isfinite(x)) for x in (q,r,dt)):
        raise ValueError('invalid interval comparison')
    return {'integrated':float(np.sum(abs(q-r)*dt)/np.sum(r*dt)), 'peak':float(np.max(abs(q-r)/r))}


def qualified_effect(value, uncertainty, threshold):
    if value-uncertainty>=threshold:return 'material'
    if value+uncertainty<threshold:return 'below'
    return 'unresolved'


def classify(metrics, uncertainty, numerical_ok):
    if not numerical_ok:return 'NUMERICALLY_UNRESOLVED'
    flags={}
    for comparison in ('C_W','C_N'):
        flags[comparison]=[]
        for name in CASES:
            states=[qualified_effect(metrics[name][comparison][m],uncertainty[name][comparison][m],t)
                    for m,t in [('integrated',.05),('peak',.10)]]
            flags[comparison].append('material' if 'material' in states else 'unresolved' if 'unresolved' in states else 'below')
    if 'material' in flags['C_N']:return 'COUPLED_STATE_DEPENDENCE_PERSISTS'
    if 'unresolved' in flags['C_N']+flags['C_W']:return 'NUMERICALLY_UNRESOLVED'
    if 'material' in flags['C_W']:return 'STATIC_SCALE_SUFFICIENT_FOR_HYDRAULICS'
    return 'SMALL_COUPLED_EFFECT'


def analyze(artifacts,output):
    artifacts,output=Path(artifacts),Path(output);output.mkdir(parents=True,exist_ok=True)
    data={};sets={};gates={}
    for resolution in ('base','temporal','spatial'):
        dd={name:{t:rows(artifacts/f'{resolution}_{name}_{t}/case') for t in ('W','C','N')} for name in CASES}
        data[resolution]=dd
        alpha=float(sum(dd[CASES[0]]['C']['volume_m3'])/sum(dd[CASES[0]]['W']['volume_m3']))
        result={}
        for name,tt in dd.items():
            w,c,n=[tt[t] for t in ('W','C','N')]
            for t,d in tt.items():
                if (abs(d['start_s'][0])>1e-10 or abs(d['end_s'][-1]-30)>1e-8
                    or not np.allclose(d['start_s'][1:],d['end_s'][:-1],atol=1e-10,rtol=0)
                    or not np.allclose(d['state_s'],d['start_s'],atol=1e-10,rtol=0)
                    or not np.allclose(d['dt_s'],d['end_s']-d['start_s'],atol=1e-10,rtol=0)):
                    raise ValueError('interval coverage/time-level error')
                if not np.allclose(d['end_s'],c['end_s'],atol=1e-10,rtol=0):raise ValueError('unmatched treatment grids')
                key=f'{resolution}_{name}_{t}'
                gates[key]=dict(water_balance_max_kg=float(max(abs(d['water_balance_kg']))),
                    solute_balance_max_kg=float(max(abs(d['solute_balance_kg']))),
                    correction_total_kg=float(sum(d['correction_kg'])),
                    c_min_kg_m3=float(min(min(d['c_n_min']),min(d['c_next_min']))),
                    c_max_kg_m3=float(max(max(d['c_n_max']),max(d['c_next_max']))),
                    remaining_min_kg=float(min(d['remaining_kg'])),
                    volume_identity_max_m3=float(max(abs(d['volume_m3']-d['Q_m3_s']*d['dt_s']))))
            secondary={t:{k:float(d[k][-1]) for k in ('water_kg','solute_kg','stored_solute_kg','remaining_kg','inlet_loss_kg','cumulative_tds')}
                       for t,d in tt.items()}
            for t,d in tt.items():
                secondary[t].update(beverage_kg=float(d['water_kg'][-1]+d['solute_kg'][-1]),
                    pore_courant_max=float(max(d['pore_courant_max'])),
                    dilute_volume_range=[float(min(d['dilute_volume_fraction'])),float(max(d['dilute_volume_fraction']))],
                    tds_range=[float(min(d['tds'])),float(max(d['tds']))],
                    mu_range_Pa_s=[float(min(min(d['mu_min']),min(d['mu_next_min']))),float(max(max(d['mu_max']),max(d['mu_next_max'])))],
                    dilute_resistance_range=[float(min(d['dilute_resistance_fraction'])),float(max(d['dilute_resistance_fraction']))])
            decomposition=dict(operator_max_relative_to_W=float(max(abs(c['Q_m3_s']-c['Q_cont_m3_s'])/w['Q_m3_s'])),
                feedback_signed_volume_relative_to_W=float(sum((c['Q_cont_m3_s']-w['Q_cont_m3_s'])*c['dt_s'])/sum(w['volume_m3'])),
                feedback_peak_relative_to_W=float(max(abs(c['Q_cont_m3_s']-w['Q_cont_m3_s'])/w['Q_m3_s'])),
                frozen_absolute=errors(w['Q_cont_m3_s'],w['Q_m3_s'],w['dt_s']))
            result[name]=dict(C_W=errors(c['Q_m3_s'],w['Q_m3_s'],c['dt_s']),C_N=errors(c['Q_m3_s'],n['Q_m3_s'],c['dt_s']),
                constant_multiplier_relative_max=float(max(abs(n['Q_m3_s']/(alpha*w['Q_m3_s'])-1))),
                secondary=secondary,decomposition=decomposition)
        sets[resolution]=dict(alpha=alpha,conditions=result)
    uncertainty={};terms={}
    for name in CASES:
        uncertainty[name]={};terms[name]={}
        for comp in ('C_W','C_N'):
            uncertainty[name][comp]={};terms[name][comp]={}
            for m in ('integrated','peak'):
                base=sets['base']['conditions'][name][comp][m]
                temporal=abs(sets['temporal']['conditions'][name][comp][m]-base)
                spatial=abs(sets['spatial']['conditions'][name][comp][m]-base)
                # Native piecewise-constant interval integrals are exact for the discrete trajectory.
                # Pairwise aggregation preserves maxima explicitly; no sparse-field quadrature.
                sampling=0.
                operator=max(sets[r]['conditions'][name]['decomposition']['operator_max_relative_to_W'] for r in sets)
                if comp=='C_N':operator/=min(sets[r]['alpha'] for r in sets)
                total=temporal+spatial+sampling+operator
                uncertainty[name][comp][m]=total
                terms[name][comp][m]=dict(temporal=temporal,spatial=spatial,quadrature_sampling=sampling,
                    native_continuum_allowance=operator,total=total)
    alpha_propagation={}
    for res in ('temporal','spatial'):
        alpha_propagation[res]={}
        for name in CASES:
            d=data['base'][name]; adjusted=errors(d['C']['Q_m3_s'],sets[res]['alpha']*d['W']['Q_m3_s'],d['C']['dt_s'])
            alpha_propagation[res][name]={m:adjusted[m]-sets['base']['conditions'][name]['C_N'][m] for m in adjusted}
    numeric_ok=(all(g['water_balance_max_kg']<=1e-8 and g['solute_balance_max_kg']<=1e-8
        and g['correction_total_kg']<=1e-10 and g['c_min_kg_m3']>=-1e-10 and g['c_max_kg_m3']<=180+1e-8
        and g['remaining_min_kg']>=-1e-12 and g['volume_identity_max_m3']<=1e-15 for g in gates.values())
        and all(v<=.005 for n in uncertainty.values() for c in n.values() for v in c.values())
        and all(c['constant_multiplier_relative_max']<=1e-6 for s in sets.values() for c in s['conditions'].values()))
    report=dict(classification=classify(sets['base']['conditions'],uncertainty,numeric_ok),sets=sets,
        empirical_estimates=terms,alpha_propagation_diagnostic_not_added_twice=alpha_propagation,gates=gates,numerical_gates_pass=numeric_ok)
    write(output/'METRICS.json',report)
    # Small data-driven SVG figures; all curves use the present native interval grid.
    from tools.sci_md_rheology_002.plot import figures
    figures(data['base'],output)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,default=DOC)
    a=p.parse_args();r=analyze(a.artifacts,a.output);print(r['classification'])

if __name__=='__main__':main()
