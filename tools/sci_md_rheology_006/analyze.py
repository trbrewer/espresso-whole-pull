"""Base-centered scores with every predeclared empirical allowance component."""
import argparse,json
from pathlib import Path
import numpy as np
from .common import DOC,TRACE,LAWS,matrix,sha,write
from .observer import read,validate,scores,decision

def case_decision(metrics):
    if not all(v['numerically_qualified'] for v in metrics.values()):return 'UNRESOLVED'
    outcomes=[v['outcome'] for v in metrics.values()]
    if 'MATERIAL' in outcomes:return 'MATERIAL'
    if all(v=='BELOW_BUDGET' for v in outcomes):return 'BELOW_BUDGET'
    return 'UNRESOLVED'

def analyze(art):
    f=json.loads((DOC/'FREEZE.json').read_text())
    events=[json.loads(l) for l in (art/'science/INVOCATIONS.jsonl').read_text().splitlines()]
    starts=[v for v in events if v['status']=='STARTED'];ends={v['slot']:v for v in events if v['status']=='COMPLETE'}
    if set(ends)!=set(matrix()):raise ValueError('missing/extra completed slots')
    if len(starts)>26:raise ValueError('attempt ceiling')
    metrics={};runs={};valid={}
    for ident,(law,res,pressure) in matrix().items():
        if res=='control':continue
        case=art/'science'/ends[ident]['id']/'case';d=read(case)
        if sha(case/TRACE)!=ends[ident]['intervals_sha256']:raise ValueError('trace changed')
        try:validate(d);valid[ident]=True
        except ValueError as e:valid[ident]=str(e)
        runs[ident]=dict(score=scores(d),high_precision=scores(d,np.longdouble),validity=valid[ident],trace_sha256=sha(case/TRACE))
    for law in LAWS:
        for pressure in (3,9):
            prefix=f'{law}_{pressure}bar_';base=runs[prefix+'base'];sets=('base','temporal','axial','radial')+(('property',) if law==LAWS[1] else ())
            qualified=all(valid[prefix+r] is True for r in sets);result={}
            for metric,budget in f['budgets_pp'].items():
                value=base['score'][metric]
                components={r:abs(runs[prefix+r]['score'][metric]-value) for r in ('temporal','axial','radial')}
                components['property']=abs(runs[prefix+'property']['score'][metric]-value) if law==LAWS[1] else 0.
                components['roundoff_reduction']=max(abs(runs[prefix+r]['score'][metric]-runs[prefix+r]['high_precision'][metric]) for r in sets)
                components['scalar_invariance_fixture']=f['scalar_fixture_allowance_pp']
                u=sum(components.values())
                result[metric]=dict(value_pp=value,allowance_pp=u,components_pp=components,budget_pp=budget,numerically_qualified=qualified and u<=.2*budget,outcome=decision(value,u,budget,qualified))
            outcome=case_decision(result)
            d=read(art/'science'/ends[prefix+'base']['id']/'case')
            context={k:float(d[k][-1]) for k in ('water_kg','solute_kg','remaining_kg','stored_solute_kg','inner_remaining_kg','outer_remaining_kg','cumulative_tds_fraction')}
            context.update(beverage_kg=context['water_kg']+context['solute_kg'],dilute_pore_occupancy_min=float(min(d['dilute_pore_volume_fraction'])),dilute_pore_occupancy_max=float(max(d['dilute_pore_volume_fraction'])),max_pore_courant=float(max(d['pore_courant_outgoing_max'])))
            metrics[prefix[:-1]]=dict(metrics=result,case_outcome=outcome,signed_shift_pp=base['score']['signed_shift_pp'],context=context)
    return dict(task='SCI-MD-RHEOLOGY-006',analysis_source_sha256=sha(Path(__file__)),freeze_sha256=sha(DOC/'FREEZE.json'),cases=metrics,runs=runs,counts=dict(planned=22,started=len(starts),completed=len(ends),failed=sum(v['status']=='FAILED' for v in events),recoveries=sum('__recovery' in v['id'] for v in starts)),physical_validation='NOT_ESTABLISHED')

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);write(a.output/'METRICS.json',analyze(a.artifacts))
if __name__=='__main__':main()
