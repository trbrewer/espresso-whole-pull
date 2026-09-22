"""Six metrics, independent arithmetic, fixed support and separate dispositions."""
import argparse,json
import numpy as np
from .common import *
from .observer import *
from .arithmetic import audit
from tools.sci_md_rheology_006.common import TRACE as RTRACE

def load(art,accepted):
    check(art,audit=True)
    reuse=json.loads((DOC/'REUSE.json').read_text());c={};p={};missing={};quality={}
    for ident,receipt in reuse['runs'].items():
        try:
            path=accepted/'science'/ident/'case'/RTRACE
            if sha(path)!=receipt['trace_sha256']:raise ValueError('accepted trace changed')
            raw=read(path);d=adapt(raw,'C');d['Q_inner_native']=raw['Q_inner_m3_s'];c[ident]=d
        except (OSError,ValueError,KeyError) as e:missing[ident]=type(e).__name__+': '+str(e)
    ledger=art/'science/INVOCATIONS.jsonl';events=[json.loads(l) for l in ledger.read_text().splitlines()] if ledger.exists() else []
    ends={e['slot']:e for e in events if e['status']=='COMPLETE'}
    for ident in matrix():
        try:
            e=ends[ident];directory=art/'science'/e['id']
            for path,h in e['files'].items():
                if sha(directory/path)!=h:raise ValueError('run file changed')
            p[ident]=adapt(read(directory/'case'/TRACE),'uniform');quality[ident]=dict(balance=p[ident]['balance'],fields=e['fields'])
        except (OSError,ValueError,KeyError) as e:missing[ident]=type(e).__name__
    return c,p,events,missing,quality

def support(c,composites):
    result={}
    for pressure in (3,9):
        cr={k:float(history(v)['B'][-1]) for k,v in c.items() if f'_{pressure}bar_' in k}
        pr={k:float(history(v)['B'][-1]) for k,v in composites.items() if f'_{pressure}bar_' in k}
        complete=len(cr)==9 and len(pr)==7
        ref=min(cr.values()) if cr else None
        star=min([*cr.values(),*pr.values()]) if cr and pr else None
        coverage=star/ref if star and ref else None
        result[str(pressure)]=dict(B_ref_kg=ref,B_star_kg=star,coverage=coverage,complete=complete,adequate=bool(complete and coverage>=.95),individual_C_coverage={k:star/v for k,v in cr.items()} if star else {},terminal_C_kg=cr,terminal_P_kg=pr)
    return result

def analyze(art,accepted,out):
    out.mkdir(parents=True,exist_ok=True);c,p,events,missing,quality=load(art,accepted);composites={}
    for law in LAWS:
        for pressure in (3,9):
            for res in sets(law):
                key=f'{law}_{pressure}bar_{res}'
                if all(key+'_'+z in p for z in ('inner','outer')):composites[key]=compose(p[key+'_inner'],p[key+'_outer'])
    supports=support(c,composites)
    write(out/'SUPPORT.json',dict(support=supports,missing=missing,rule='minimum all required C/P; same support per pressure; no old 004 endpoint'))
    cases={};allflags=[];groups=dict(hydraulics=[],allocation=[],aggregate_delivery=[])
    for law in LAWS:
        for pressure in (3,9):
            key=f'{law}_{pressure}bar';values={};arithmetic={};sup=supports[str(pressure)]
            for res in sets(law)+('radial',):
                ck=key+'_'+res;pk=key+'_'+('base' if res=='radial' else res)
                if ck not in c or pk not in composites or sup['B_star_kg'] is None:continue
                values[res]=metrics(composites[pk],c[ck],sup['B_star_kg'])
                high=audit(p[pk+'_inner'],p[pk+'_outer'],c[ck],sup['B_star_kg'])
                arithmetic[res]={m:abs(values[res][m]-high[m]) for m in BUDGETS}
            qualified={}
            for m,budget in BUDGETS.items():
                complete=set(values)==set(sets(law)+('radial',));v=values.get('base',{}).get(m)
                terms={r:abs(values[r][m]-v) for r in ('temporal','axial','radial','property') if r in values and v is not None}
                if law==LAWS[0]:terms['property']=0.
                terms['arithmetic']=max((a[m] for a in arithmetic.values()),default=0.)
                u=sum(terms.values()) if complete else None
                group='hydraulics' if m.startswith('E_Q') else 'allocation' if m.startswith('D_share') else 'aggregate_delivery'
                valid=complete and (group!='aggregate_delivery' or sup['adequate'])
                flag=decide(v,u,budget,valid) if complete else 'UNRESOLVED'
                qualified[m]=dict(value=v,u_total=u,budget=budget,terms=terms,valid=valid,decision=flag)
                groups[group].append(flag);allflags.append(flag)
            cases[key]=dict(metrics=qualified,sets=values,arithmetic_by_set=arithmetic,verdict=verdict([v['decision'] for v in qualified.values()]))
    report=dict(task='SCI-MD-RHEOLOGY-007',disposition='PARALLEL_PATH_REDUCTION_'+verdict(allflags,not missing),observables={k:verdict(v,not missing) for k,v in groups.items()},cases=cases,support=supports,missing=missing,qualification=quality,arithmetic='Independent Decimal 50 digits (>53 bits), native values, weighting, cumulative increments, C share and mass splitting recomputed',counts=dict(new_full_started=sum(e['status']=='STARTED' for e in events),new_full_completed=sum(e['status']=='COMPLETE' for e in events),new_full_failed=sum(e['status']=='FAILED' for e in events),reused_radial=len(c),bridge=0,short=6),freeze_sha256=sha(DOC/'FREEZE.json'),physical_validation='NOT_ESTABLISHED')
    write(out/'METRICS.json',report)
    write(out/'RUNS.json',dict(events=[{k:v for k,v in e.items() if k!='files'}|({'case_manifest_sha256':digest(e['files']),'file_count':len(e['files'])} if 'files' in e else {}) for e in events],ledger_sha256=sha(art/'science/INVOCATIONS.jsonl'),counts=report['counts']))
    return report,c,composites

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--accepted',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r,_,_=analyze(a.artifacts,a.accepted,a.output);print(r['disposition'])
if __name__=='__main__':main()
