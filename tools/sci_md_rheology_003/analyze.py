"""Whole-interval hydraulic metrics; empirical refinement estimates, no null chemistry."""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.sci_md_rheology_001.analysis import write,sha
from tools.sci_md_rheology_002.run import rows, CASES, DOC as OLD
from tools.sci_md_rheology_002.analyze import errors,qualified_effect,analyze as baseline_analyze
from .laws import LAWS,NEW,fraction
from .run import SETS,matrix
from .evidence import DOC,INTERVAL,reuse


def validate(d, end=30):
    required=('start_s','end_s','dt_s','state_s','Q_m3_s','volume_m3')
    if any(k not in d for k in required):raise ValueError('missing interval column')
    n=len(d['start_s'])
    if not n or any(len(v)!=n or not np.all(np.isfinite(v)) for v in d.values()):
        raise ValueError('empty/nonfinite/mismatched intervals')
    if (abs(d['start_s'][0])>1e-10 or abs(d['end_s'][-1]-end)>1e-8
        or np.any(d['dt_s']<=0) or np.any(d['Q_m3_s']<=0)
        or not np.allclose(d['start_s'][1:],d['end_s'][:-1],atol=1e-10,rtol=0)
        or not np.allclose(d['state_s'],d['start_s'],atol=1e-10,rtol=0)
        or not np.allclose(d['dt_s'],d['end_s']-d['start_s'],atol=1e-10,rtol=0)
        or np.max(abs(d['volume_m3']-d['Q_m3_s']*d['dt_s']))>1e-15):
        raise ValueError('interval coverage/positive denominator/volume failure')


def matched(c,w):
    validate(c);validate(w)
    if any(c[k].shape!=w[k].shape or not np.allclose(c[k],w[k],atol=1e-10,rtol=0)
           for k in ('start_s','end_s','dt_s')):raise ValueError('mismatched physical intervals')


def calibrate(reference_c,reference_w):
    """Only uniform reference arrays enter; caller supplies no transfer records."""
    matched(reference_c,reference_w)
    return float(sum(reference_c['volume_m3'])/sum(reference_w['volume_m3']))


def gates(d):
    validate(d)
    cmin=float(min(min(d['c_n_min']),min(d['c_next_min'])))
    cmax=float(max(max(d['c_n_max']),max(d['c_next_max'])))
    result=dict(water_balance_max_kg=float(max(abs(d['water_balance_kg']))),
        solute_balance_max_kg=float(max(abs(d['solute_balance_kg']))),
        correction_total_kg=float(sum(abs(d['correction_kg']))),
        c_min_kg_m3=cmin,c_max_kg_m3=cmax,remaining_min_kg=float(min(d['remaining_kg'])),
        volume_identity_max_m3=float(max(abs(d['volume_m3']-d['Q_m3_s']*d['dt_s']))))
    result['source_domain_pass']=cmin>=-1e-10 and cmax/(965+cmax)<=.24
    result['numerical_state_pass']=(result['water_balance_max_kg']<=1e-8 and result['solute_balance_max_kg']<=1e-8
        and result['correction_total_kg']<=1e-10 and cmin>=-1e-10 and cmax<=180+1e-8
        and result['remaining_min_kg']>=-1e-12 and result['volume_identity_max_m3']<=1e-15)
    return result


def comparison_status(metrics,terms,ok=True):
    if not ok:return 'unresolved'
    flags=[qualified_effect(metrics[m],terms[m]['total'],t) for m,t in (('integrated',.05),('peak',.10))]
    return 'material' if 'material' in flags else 'below' if all(v=='below' for v in flags) else 'unresolved'


def family_status(laws):
    if set(laws)!=set(LAWS):return 'SOURCE_DOMAIN_OR_NUMERICAL_UNRESOLVED'
    decisions=[laws[l]['conditions'][c]['C_N'] for l in LAWS for c in CASES]
    if any(not laws[l]['qualified'] for l in LAWS) or 'unresolved' in decisions:
        return 'SOURCE_DOMAIN_OR_NUMERICAL_UNRESOLVED'
    if all(x=='material' for x in decisions):return 'ROBUST_ACROSS_TESTED_VISCOSITY_LAWS'
    if any(laws['TR_LINEAR']['conditions'][c]['C_N']=='material' and laws[l]['conditions'][c]['C_N']=='below'
           for l in NEW for c in CASES):return 'SOURCE_OR_CONTINUATION_SENSITIVE'
    return 'SOURCE_DOMAIN_OR_NUMERICAL_UNRESOLVED'


def secondary(d):
    result={k:float(d[k][-1]) for k in ('water_kg','solute_kg','stored_solute_kg','remaining_kg','inlet_loss_kg','cumulative_tds')}
    result.update(beverage_kg=result['water_kg']+result['solute_kg'],
        c_range_kg_m3=[float(min(min(d['c_n_min']),min(d['c_next_min']))),float(max(max(d['c_n_max']),max(d['c_next_max'])))],
        mu_range_Pa_s=[float(min(min(d['mu_min']),min(d['mu_next_min']))),float(max(max(d['mu_max']),max(d['mu_next_max'])))],
        pore_courant_max=float(max(d['pore_courant_max'])))
    result['w_range']=[float(x/(965+x)) for x in result['c_range_kg_m3']]
    for key in ('tds','dilute_volume_fraction','dilute_resistance_fraction'):
        result[key+'_range']=[float(min(d[key])),float(max(d[key]))]
    return result


def check_baseline(baseline, output):
    receipt=reuse(baseline)
    reproduced=baseline_analyze(baseline,output)
    accepted=json.loads((OLD/'METRICS.json').read_text())
    if reproduced!=accepted:raise ValueError('accepted baseline metric reproduction differs')
    receipt['metric_reproduction']='EXACT';return reproduced,receipt


def analyze(artifacts,baseline,output):
    artifacts,baseline,output=map(Path,(artifacts,baseline,output));output.mkdir(parents=True,exist_ok=False)
    old,receipt=check_baseline(baseline,output/'baseline-reproduction')
    ledger=[json.loads(s) for s in (artifacts/'INVOCATIONS.jsonl').read_text().splitlines()]
    starts=[r for r in ledger if r['status']=='STARTED'];ends=[r for r in ledger if r['status']=='COMPLETE']
    expected={'_'.join(x) for x in matrix()}
    if len(starts)!=24 or len(ends)!=24 or {r['id'] for r in starts}!=expected or {r['id'] for r in ends}!=expected:
        raise ValueError('incomplete family/failed attempts: no scientific PASS')
    for r in ends:
        if sha(artifacts/r['id']/'case'/INTERVAL)!=r['intervals_sha256']:raise ValueError('new interval identity mismatch')
    mu_water=json.loads((DOC/'EXPORT.json').read_text())['water_viscosity_Pa_s']
    data={};laws={};run_gates={}
    for law in LAWS:
        sets={};data[law]={}
        resolutions=SETS if law in NEW else SETS[:3]
        for res in resolutions:
            wr='base' if res=='property' else res
            dd={c:dict(W=rows(baseline/f'{wr}_{c}_W/case'),
                C=rows((artifacts/f'{res}_{c}_{law}' if law in NEW else baseline/f'{res}_{c}_C')/'case'),
                TR=rows(baseline/f'{wr}_{c}_C/case')) for c in CASES}
            data[law][res]=dd
            alpha=calibrate(dd[CASES[0]]['C'],dd[CASES[0]]['W'])
            conditions={}
            for name,p in dd.items():
                c,w=p['C'],p['W'];matched(c,w);matched(c,p['TR'])
                run_gates[f'{law}_{res}_{name}']=gates(c)
                conditions[name]=dict(C_W=errors(c['Q_m3_s'],w['Q_m3_s'],c['dt_s']),
                    C_N=errors(c['Q_m3_s'],alpha*w['Q_m3_s'],c['dt_s']),
                    C_TR_LINEAR=errors(c['Q_m3_s'],p['TR']['Q_m3_s'],c['dt_s']),
                    operator_relative_to_W=float(max(abs(c['Q_m3_s']-c['Q_cont_m3_s'])/w['Q_m3_s'])),
                    coupled_secondary=secondary(c))
            sets[res]=dict(alpha=alpha,mu_N_Pa_s=mu_water/alpha,conditions=conditions)
        terms={};classification={};propagation={}
        for name in CASES:
            terms[name]={};classification[name]={}
            for comp in ('C_W','C_N'):
                terms[name][comp]={}
                for metric in ('integrated','peak'):
                    base=sets['base']['conditions'][name][comp][metric]
                    if law=='TR_LINEAR':
                        term=old['empirical_estimates'][name][comp][metric].copy()
                        term['property_table']=0.;term['property_table_note']='accepted exactly piecewise-linear primary law'
                    else:
                        term={r:abs(sets[r]['conditions'][name][comp][metric]-base) for r in SETS[1:]}
                        term['property_table']=term.pop('property')
                        operator=max(sets[r]['conditions'][name]['operator_relative_to_W'] for r in sets)
                        if comp=='C_N':operator/=min(sets[r]['alpha'] for r in sets)
                        term.update(native_continuum_allowance=operator,quadrature_sampling=0.)
                        term['total']=sum(term.values())
                    terms[name][comp][metric]=term
                ok=all(g['source_domain_pass'] and g['numerical_state_pass'] for key,g in run_gates.items() if key.startswith(law+'_'))
                ok=ok and all(t['total']<=.005 for t in terms[name][comp].values())
                classification[name][comp]=comparison_status(sets['base']['conditions'][name][comp],terms[name][comp],ok)
            classification[name]['outcome']=('COUPLED_STATE_DEPENDENCE_PERSISTS' if classification[name]['C_N']=='material' else
                'STATIC_SCALE_SUFFICIENT_FOR_HYDRAULICS' if classification[name]['C_N']=='below' and classification[name]['C_W']=='material' else
                'SMALL_COUPLED_EFFECT' if classification[name]['C_N']==classification[name]['C_W']=='below' else 'UNRESOLVED')
            propagation[name]={}
            d=data[law]['base'][name]
            for r in resolutions[1:]:
                e=errors(d['C']['Q_m3_s'],sets[r]['alpha']*d['W']['Q_m3_s'],d['C']['dt_s'])
                propagation[name][r]={m:e[m]-sets['base']['conditions'][name]['C_N'][m] for m in e}
        laws[law]=dict(sets=sets,empirical_estimates=terms,conditions=classification,
            qualified=all(v!='unresolved' for c in classification.values() for k,v in c.items() if k!='outcome'),
            alpha_propagation_diagnostic_not_added_twice=propagation)
    report=dict(classification=family_status(laws),laws=laws,gates=run_gates,baseline_reuse=receipt,
        full_run_count=len(starts),null_outputs='hydraulics only; no null transport produced',
        freeze_sha256=sha(DOC/'FREEZE.json'))
    write(output/'METRICS.json',report)
    from .plot import figures
    figures(data,output)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('artifacts','baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    try:r=analyze(a.artifacts,a.baseline,a.output)
    except (ValueError,OSError) as e:
        a.output.mkdir(parents=True,exist_ok=True)
        write(a.output/'UNRESOLVED.json',dict(classification='SOURCE_DOMAIN_OR_NUMERICAL_UNRESOLVED',cause=str(e)))
        raise
    print(r['classification'])

if __name__=='__main__':main()
