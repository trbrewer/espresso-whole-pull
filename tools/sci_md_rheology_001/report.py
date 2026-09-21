#!/usr/bin/env python3
"""Apply the frozen refinement/decision rules and draw compact derived figures."""
import argparse
import csv
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.sci_md_rheology_001.analysis import (DOC,ROOT,REF,source,load_profile,compare,errors,write,sha,check_freeze,check_output)


def metrics_difference(a,b):
    return np.array([max(abs(a[n][kind][m]-b[n][kind][m]) for n in a for kind in ('absolute','residual'))
                     for m in ('integrated','peak')])


def classify(metrics, uncertainty):
    thresholds=np.array([.05,.10]); uncertainty=np.asarray(uncertainty)
    absolute=np.array([max(v['absolute'][k] for v in metrics.values()) for k in ('integrated','peak')])
    residual=np.array([max(v['residual'][k] for v in metrics.values()) for k in ('integrated','peak')])
    near=any(np.any(np.abs(values-thresholds)<=uncertainty) for values in (absolute,residual))
    if np.any(uncertainty>=.005) or near: return None,'NUMERICAL_CLASSIFICATION_UNRESOLVED'
    if np.any(residual>=thresholds): category='STATE_DEPENDENT_EFFECT'
    elif np.any(absolute>=thresholds): category='STATIC_SCALE_SUFFICIENT'
    else: category='SMALL_WITHIN_TESTED_ENVELOPE'
    return category,'FROZEN_FIELD_SOURCE_CONDITIONED_ONLY'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('puckworks','runs','output','audit'): p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args(); check_output(a.output); check_freeze(a.audit); data,_=source(a.puckworks)
    ss=json.loads((DOC/'SCENARIOS.json').read_text()); summary={}; changes={}; histories={}
    for variant,excess in [('primary',1),('stress',2)]:
        profiles={n:load_profile(a.runs/n,s,data.telisromero_eta_measured,excess) for n,s in ss.items()}
        alpha,m=compare(profiles); summary[variant]=dict(alpha=alpha,metrics=m)
        histories[variant]=profiles
        coarse={n:{k:v[::2] if k in ('t','q','q0') else v for k,v in prof.items()} for n,prof in profiles.items()}
        _,cm=compare(coarse); decimation=metrics_difference(m,cm)
        diffs={}; temporal_sampling={}
        for kind in ('temporal','spatial'):
            diffs[kind]=[]
            for config in sorted(a.runs.glob('*_'+kind+'.json')):
                name=config.stem.removesuffix('_'+kind)
                if name not in ss: continue
                s=json.loads(config.read_text()); refined=load_profile(a.runs/config.stem,s,data.telisromero_eta_measured,excess)
                updated=dict(profiles); updated[name]=refined
                _,rm=compare(updated)
                diffs[kind].append((name,metrics_difference(m,rm)))
                if kind=='temporal':
                    down={k:v[::2] if k in ('t','q','q0') else v for k,v in refined.items()}
                    sampled=dict(profiles);sampled[name]=down
                    _,sm=compare(sampled)
                    temporal_sampling[name]=metrics_difference(rm,sm)
                    decimation=np.maximum(decimation,temporal_sampling[name])
            if not {'uniform_9bar','layered_3bar'}.issubset({n for n,d in diffs[kind]}):
                raise ValueError('required representative refinement missing')
        # Include measured continuum/discrete water-flow discrepancy in BOTH metrics.
        hydraulic=max(prof['continuum_hydraulic_relative_error'] for prof in profiles.values())
        uncertainty=hydraulic+decimation+np.max([d for n,d in diffs['temporal']],axis=0)+np.max([d for n,d in diffs['spatial']],axis=0)
        changes[variant]=dict(decimation=decimation.tolist(),continuum_hydraulic_allowance_pp=100*hydraulic,
            temporal_sampling_changes_pp={n:(100*v).tolist() for n,v in temporal_sampling.items()},
            temporal={n:d.tolist() for n,d in diffs['temporal']},spatial={n:d.tolist() for n,d in diffs['spatial']},
            uncertainty_pp=(100*uncertainty).tolist())
        category,reason=classify(m,uncertainty)
        summary[variant].update(category=category,qualification=reason,uncertainty_pp=(100*uncertainty).tolist())
        for name,prof in profiles.items():
            h=prof['histories']
            m[name].update(concentration_range_kg_m3=[0,max(v['c_max_kg_m3'] for v in h)],
                solids_range=[0,max(v['solids_max'] for v in h)],
                hydraulic_relative_error=prof['hydraulic_relative_error'],
                continuum_hydraulic_relative_error=prof['continuum_hydraulic_relative_error'],
                dilute_cell_fraction_range=[min(v['dilute_cell_fraction'] for v in h),max(v['dilute_cell_fraction'] for v in h)],
                dilute_resistance_fraction_range=[min(v['dilute_resistance_fraction'] for v in h),max(v['dilute_resistance_fraction'] for v in h)],
                weighted_mu_range_Pa_s=[ss[name]['liquid']['dynamic_viscosity_Pa_s'],max(v['weighted_mu_Pa_s'] for v in h)])
        summary[variant]['reversal']={str(bar):{kind:{key:m[f'reversed_{bar}bar'][kind][key]-m[f'layered_{bar}bar'][kind][key] for key in ('integrated','peak')} for kind in ('absolute','residual')} for bar in (3,9)}
    # Largest contrast is selected across BOTH variants, per frozen rule.
    scores={n:max(summary[v]['metrics'][n]['residual'][k]/th for v in summary for k,th in [('integrated',.05),('peak',.1)]) for n in ss}
    largest=sorted(scores,key=lambda n:(-scores[n],n))[0]
    for v in changes:
        for kind in ('temporal','spatial'):
            if largest not in changes[v][kind]: raise ValueError('largest contrast needs refinement: '+largest)
    a.output.mkdir(exist_ok=True,parents=True)
    write(a.output/'METRICS.json',summary);write(a.output/'NUMERICAL.json',dict(largest_contrast_case=largest,variants=changes))
    with (a.output/'METRICS.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['variant','scenario','alpha','absolute_integrated_pct','absolute_peak_pct','residual_integrated_pct','residual_peak_pct','integrated_uncertainty_pp','peak_uncertainty_pp'])
        for v,s in summary.items():
            for n,m in s['metrics'].items():
                w.writerow([v,n,s['alpha']]+[100*m[k][q] for k in ('absolute','residual') for q in ('integrated','peak')]+s['uncertainty_pp'])
    with (a.output/'HISTORIES.csv').open('w') as f:
        fields=list(next(iter(histories['primary'].values()))['histories'][0])
        w=csv.DictWriter(f,fieldnames=['variant','scenario']+fields);w.writeheader()
        for v,ps in histories.items():
            for n,pf in ps.items():
                for h in pf['histories']:w.writerow(dict(variant=v,scenario=n,**h))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':9,'svg.hashsalt':'SCI-MD-RHEOLOGY-001'})
    fig,ax=plt.subplots(1,2,figsize=(10,3.5))
    for j,v in enumerate(summary):
        for n,pf in histories[v].items():ax[j].plot(pf['t'],pf['r']/pf['r'][0],label=n)
        ax[j].set(xlabel='Time (s)',ylabel='R / water resistance',title=v+' (frozen fields)');ax[j].legend(fontsize=7)
    fig.tight_layout();fig.savefig(a.output/'resistance.svg',metadata={'Date':None});plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10,3.5))
    for ax,v in zip(axs,summary):
        names=list(ss);x=np.arange(len(names))
        for off,kind in [(-.18,'absolute'),(.18,'residual')]:
            ax.bar(x+off,[100*summary[v]['metrics'][n][kind]['integrated'] for n in names],.36,label=kind)
        ax.axhline(5,color='black',linestyle='--',linewidth=.7);ax.set_xticks(x,names,rotation=40,ha='right')
        ax.set(ylabel='Integrated absolute error (%)',title=v);ax.legend()
    fig.tight_layout();fig.savefig(a.output/'effects.svg',metadata={'Date':None});plt.close(fig)
    print(json.dumps({v:{k:s[k] for k in ('alpha','category','uncertainty_pp')} for v,s in summary.items()},indent=2))

if __name__=='__main__':main()
