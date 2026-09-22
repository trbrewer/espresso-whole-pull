"""72 primary decisions using fixed support and candidate-specific allowances."""
import argparse
import json
from .common import *
from .observer import native, read, metrics, qualify_metric, verdict, history
from .arithmetic import audit

def load(art):
    check(art,audit=True)
    locations=json.loads((art/'LOCATIONS.json').read_text());accepted=Path(locations['accepted'])
    reuse=json.loads((DOC/'REUSE.json').read_text());c={};e={};missing={}
    for slot,v in reuse['C'].items():
        try:
            path=accepted/'science'/slot/'case'/TRACE
            if sha(path)!=v['trace_sha256']:raise ValueError('C trace changed')
            c[slot]=native(read(path))
        except (OSError,ValueError,KeyError) as error:missing['C_'+slot]=type(error).__name__
    ledger=art/'science/INVOCATIONS.jsonl'
    events=[json.loads(s) for s in ledger.read_text().splitlines()] if ledger.exists() else []
    complete={x['slot']:x for x in events if x['status']=='COMPLETE'}
    for slot in matrix():
        try:
            event=complete[slot];directory=art/'science'/event['id']
            for p,h in event['files'].items():
                if sha(directory/p)!=h:raise ValueError('E evidence changed')
            e[slot]=native(read(directory/'case'/TRACE))
        except (OSError,ValueError,KeyError) as error:missing[slot]=type(error).__name__
    return c,e,events,missing

def selection(candidates):
    passing=[n for n in (2,4,8) if candidates[f'E{n}']['disposition']=='SUFFICIENT_FOR_TESTED_OUTPUTS']
    if passing:
        n=min(passing)
        return dict(status='COARSEST_QUALIFIED_PASSING_CANDIDATE_AMONG_2_4_8',N=n,lower_unresolved=[k for k in (2,4,8) if k<n and candidates[f'E{k}']['disposition']=='UNRESOLVED'])
    return dict(status='EVERY_CANDIDATE_HAS_QUALIFIED_FAILURE' if all(c['disposition']=='INSUFFICIENT' for c in candidates.values()) else 'ONE_OR_MORE_CANDIDATES_UNRESOLVED',N=None)

def analyze(art,out):
    c,e,events,missing=load(art);out.mkdir(parents=True,exist_ok=True)
    support=json.loads((DOC/'SUPPORT.json').read_text())['inherited']['support']
    coverage={str(p):dict(inherited=support[str(p)],candidate_terminal_kg={k:float(history(v)['B'][-1]) for k,v in e.items() if f'_{p}bar_' in k}) for p in (3,9)}
    write(out/'COVERAGE.json',coverage)
    cases={};candidates={}
    for n in (2,4,8):
        flags=[];groups=dict(hydraulics=[],allocation=[],delivery=[])
        for law in LAWS:
            for pressure in (3,9):
                key=f'{law}_{pressure}bar';values={};arithmetic={};errors={}
                for res in sets(law)+('radial',):
                    ek=f'E{n}_{key}_'+('base' if res=='radial' else res);ck=key+'_'+res
                    if ek not in e or ck not in c:continue
                    try:
                        endpoint=support[str(pressure)]['B_star_kg']
                        values[res]=metrics(e[ek],c[ck],endpoint)
                        high=audit(e[ek],c[ck],endpoint)
                        arithmetic[res]={m:abs(values[res][m]-v) for m,v in high.items() if values[res][m] is not None}
                    except (ValueError,KeyError,ArithmeticError) as error:
                        errors[res]=type(error).__name__+': '+str(error)
                scores={m:qualify_metric(values,arithmetic,law,m) for m in BUDGETS}
                for m,s in scores.items():
                    flags.append(s['decision']);group='hydraulics' if m.startswith('E_Q') else 'allocation' if m.startswith('D_share') else 'delivery'
                    groups[group].append(s['decision'])
                cases[f'E{n}_{key}']=dict(metrics=scores,variants=values,arithmetic_by_variant=arithmetic,errors=errors)
        candidates[f'E{n}']=dict(disposition=verdict(flags,len(flags)==24),observables={k:verdict(v) for k,v in groups.items()},decision_counts={k:flags.count(k) for k in ('PASS','FAIL','UNRESOLVED')},base_cells=512*n,axial_cells=1024*n)
    chosen=selection(candidates)
    if missing and all(v['decision_counts']['UNRESOLVED']==24 for v in candidates.values()):chosen['status']='EXECUTION_OR_EVIDENCE_PREVENTED_ADJUDICATION'
    counts=dict(full_starts=sum(x['status']=='STARTED' for x in events),full_completions=sum(x['status']=='COMPLETE' for x in events),failure_events=sum(x['status']=='FAILED' for x in events),recoveries=sum(x['status']=='STARTED' and x.get('recovery_reason') is not None for x in events),reused_C=len(c),reused_P_native_traces=28,new_C=0,new_P=0,bridge=0)
    report=dict(task='SCI-MD-RHEOLOGY-008',selection=chosen,candidates=candidates,cases=cases,missing=missing,counts=counts,arithmetic='Independent 50-digit Decimal on two native radial histories; recomputes shares, increments, breakpoints and splits',allowances='Empirical sensitivity sums, not confidence intervals or rigorous continuum error bounds. No inter-candidate radial differences included.',physical_validation='NOT_ESTABLISHED')
    write(out/'METRICS.json',report)
    sanitized=[]
    for event in events:
        v={k:value for k,value in event.items() if k!='files'}
        if 'reason' in v:v['reason']=v['reason'].replace(str(art),'[ART]')
        if 'files' in event:v.update(case_manifest_sha256=digest(event['files']),file_count=len(event['files']))
        sanitized.append(v)
    write(out/'RUNS.json',dict(counts=counts,events=sanitized,ledger_sha256=sha(art/'science/INVOCATIONS.jsonl') if events else None))
    write(out/'QUALIFICATION.json',dict(validated_C=len(c),validated_E=len(e),missing=missing,short_sha256=sha(DOC/'SHORT_CHECKS.json'),balances={k:v['balance'] for k,v in e.items()}))
    return report,c,e

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r,_,_=analyze(a.artifacts,a.output);print(r['selection'])
if __name__=='__main__':main()
