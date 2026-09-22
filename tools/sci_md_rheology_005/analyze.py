"""C-denominated metrics on complete native intervals and conservative mass support."""
import argparse,json
from pathlib import Path
import numpy as np
from tools.sci_md_rheology_001.analysis import write,sha
from tools.sci_md_rheology_002.run import rows,CASES
from tools.sci_md_rheology_003.analyze import matched,gates,secondary
from tools.sci_md_rheology_004.observer import history,compare
from .evidence import ROOT,DOC,BUDGETS,LAWS,sets,matrix,check,completed,reuse,accepted_path,BULK
from .short import read_bulk

def hydraulic(g,c,dtype=np.float64,continuum=False):
    matched(g,c);key='Q_cont_m3_s' if continuum else 'Q_m3_s'
    qg=np.asarray(g[key],dtype=dtype);qc=np.asarray(c[key],dtype=dtype);dt=np.asarray(c['dt_s'],dtype=dtype)
    if np.any(qc<=0) or np.any(qg<=0):raise ValueError('nonpositive continuum flow')
    return dict(E_Qint=float(np.sum(abs(qg-qc)*dt)/np.sum(qc*dt)),E_Qpeak=float(max(abs(qg-qc)/qc)))

def operator(g,c):
    """Inherited conservative envelope plus explicit C denominator propagation."""
    matched(g,c);dt=c['dt_s'];qc=c['Q_m3_s'];dc=abs(qc-c['Q_cont_m3_s']);dg=abs(g['Q_m3_s']-g['Q_cont_m3_s'])
    cont=hydraulic(g,c,continuum=True);ec=abs(g['Q_cont_m3_s']-c['Q_cont_m3_s'])/c['Q_cont_m3_s']
    return {'E_Qint':dict(C=float(sum(dc*dt)/sum(qc*dt)),G=float(sum(dg*dt)/sum(qc*dt)),
                         denominator=float(cont['E_Qint']*sum(dc*dt)/sum(qc*dt))),
            'E_Qpeak':dict(C=float(max(dc/qc)),G=float(max(dg/qc)),denominator=float(max(ec*dc/qc)))}

def metric(g,c,end,dtype=np.float64):
    result=hydraulic(g,c,dtype);obs=compare(history(g),history(c),'B',end,dtype)
    result.update(E_Spath=obs['E_path'],D_TDS=obs['max_fraction_TDS_pp'])
    result['delivery']=dict(G=obs['C'],C=obs['R'],time_G_s=obs['t_C_s'],time_C_s=obs['t_R_s'],
                           signed_fraction_TDS_pp=[x-y for x,y in zip(obs['C']['TDS_percent'],obs['R']['TDS_percent'])],
                           TDS_at_zero=None,breakpoint_count=obs['breakpoint_count'])
    return result

def decide(v,u,b):
    if not np.isfinite(v+u) or v<0 or u<0 or u>.2*b:return 'UNRESOLVED'
    if v-u>=b:return 'QUALIFIED_FAILURE'
    if v+u<b:return 'QUALIFIED_PASS'
    return 'UNRESOLVED'

def disposition(flags,complete=True,coverage=True):
    if 'QUALIFIED_FAILURE' in flags:return 'BULK_STATE_CLOSURE_INSUFFICIENT'
    if complete and coverage and flags and all(x=='QUALIFIED_PASS' for x in flags):return 'BULK_STATE_CLOSURE_SUFFICIENT_IN_TESTED_REGIME'
    return 'BULK_STATE_CLOSURE_UNRESOLVED'

def qualify(d):
    q=gates(d)
    q['remaining_max_kg']=float(max(d['remaining_kg']));q['stored_min_kg']=float(min(d['stored_solute_kg']))
    q['pass']=bool(q['source_domain_pass'] and q['numerical_state_pass'] and q['remaining_max_kg']<=.0056+1e-10 and q['stored_min_kg']>=-1e-12)
    if not q['pass']:raise ValueError('engineering/admissibility failure')
    history(d)
    return q

def analyze(a):
    a.output.mkdir(parents=True,exist_ok=False);f=check(audit=True,artifacts=a.artifacts)
    reused=reuse(a.baseline,a.coupled,a.context)
    if reused!=json.loads((DOC/'REUSE.json').read_text()):raise ValueError('reuse differs from freeze')
    events,starts,ends=completed(a.artifacts);data={};quality={};missing={};regression={};bulk={}
    # Base C controls qualify reuse per law/scenario. Full controls retain 005 IDs.
    for law in LAWS:
        for case in CASES:
            slot=f'{law}_base_{case}_C';key=law+'/'+case
            try:
                new=rows(a.artifacts/ends[slot]['attempt']/'case');qualify(new)
                oldpath,_=accepted_path(a.baseline,a.coupled,law,'base',case);old=rows(oldpath/'case');matched(new,old)
                err=max(float(max(abs(new[k]-old[k])))/max(1.,float(max(abs(old[k])))) for k in old)
                regression[key]=dict(max_normalized_difference=err,tolerance=1e-10,pass_gate=err<=1e-10)
                if err>1e-10:raise ValueError('changed legacy coupled behavior')
            except (OSError,ValueError,KeyError) as ex:missing[key+'/C_regression']=type(ex).__name__;continue
            for res in sets(law):
                for arm in ('C','G'):
                    label=f'{law}/{res}/{case}/{arm}'
                    try:
                        if arm=='C':
                            path,_=accepted_path(a.baseline,a.coupled,law,res,case)
                            if res=='base':path=a.artifacts/ends[slot]['attempt']
                        else:path=a.artifacts/ends[f'{law}_{res}_{case}_G']['attempt']
                        d=rows(path/'case');quality[label]=qualify(d)
                        if arm=='G':
                            b=read_bulk(path/'case')
                            if any(not np.all(np.isfinite(v)) for v in b.values()):raise ValueError('nonfinite bulk diagnostic')
                            if not np.allclose(b['state_s'],d['start_s'],rtol=0,atol=1e-10):raise ValueError('bulk timing')
                            err=float(max(abs(b['stored_dissolved_mass_kg']-np.r_[0.,d['stored_solute_kg'][:-1]])))
                            if err>1e-12:raise ValueError('bulk state storage mismatch')
                            if not np.allclose(b['w_bar'],b['stored_dissolved_mass_kg']/(965*b['pore_water_volume_m3']+b['stored_dissolved_mass_kg']),rtol=1e-12,atol=1e-14):raise ValueError('bulk fraction mismatch')
                            if not np.array_equal(b['Q_applied_cont_m3_s'],d['Q_cont_m3_s']):raise ValueError('applied continuum mismatch')
                            bulk[label]=dict(storage_identity_error_kg=err,pore_volume_m3=float(b['pore_water_volume_m3'][0]),
                                applied_mu_range_Pa_s=[float(min(b['applied_mu_Pa_s'])),float(max(b['applied_mu_Pa_s']))],
                                final_applied_mu_Pa_s=float(b['applied_mu_Pa_s'][-1]),bulk_w_range=[float(min(b['w_bar'])),float(max(b['w_bar']))])
                        data[law,res,case,arm]=d
                    except (OSError,ValueError,KeyError) as ex:missing[label]=type(ex).__name__+': '+str(ex).replace(str(a.artifacts),'[external]')
    inherited=json.loads((ROOT/'docs/analysis/sci_md_rheology_004/SUPPORT.json').read_text())['support']
    support={};coverage={}
    for case in CASES:
        relevant={ '/'.join(k):float(d['water_kg'][-1]+d['solute_kg'][-1]) for k,d in data.items() if k[2]==case }
        if not relevant:continue
        b=min(inherited[case]['B'],*relevant.values())
        support[case]=dict(B_star_kg=b,inherited_004_B_kg=inherited[case]['B'],coverage_ratio=b/inherited[case]['B'],adequate=b/inherited[case]['B']>=.95)
        coverage.update(relevant)
    # Write the support artifact before calculating discrepancies, including missing arms.
    write(a.output/'SUPPORT.json',dict(support=support,terminal_B_kg=coverage,missing=missing,provisional=bool(missing)))
    result={};flags=[];fixed={}
    for law in LAWS:
        for case in CASES:
            key=law+'/'+case;values={};ops={};arith={}
            for res in sets(law):
                if any((law,res,case,arm) not in data for arm in ('G','C')):continue
                g,c=(data[law,res,case,arm] for arm in ('G','C'));end=support[case]['B_star_kg']
                values[res]=metric(g,c,end);extended=metric(g,c,end,np.longdouble)
                arith[res]={m:abs(values[res][m]-extended[m]) for m in BUDGETS};ops[res]=operator(g,c)
                fixed[key+'/'+res]={arm:secondary(d) for arm,d in [('G',g),('C',c)]}
            qualifications={}
            if set(values)==set(sets(law)):
                for m,budget in BUDGETS.items():
                    base=values['base'][m]
                    term={r:abs(values[r][m]-base) if r in values else 0. for r in ('temporal','spatial','property')}
                    term['observer_arithmetic']=max(arith[r][m] for r in values)
                    term['operator']=0.
                    operator_detail={}
                    if m in ('E_Qint','E_Qpeak'):
                        # Sum conservative component maxima; no cancellation or duplicate total.
                        operator_detail={part:max(ops[r][m][part] for r in values) for part in ('C','G','denominator')}
                        term['operator']=sum(operator_detail.values())
                    u=sum(term.values());flag=decide(base,u,budget);flags.append(flag)
                    qualifications[m]=dict(value=base,allowance=u,budget=budget,allowance_limit=.2*budget,terms=term,
                        operator_components=operator_detail,classification=flag)
            else:flags.append('UNRESOLVED')
            result[key]=dict(sets=values,qualification=qualifications,operator_by_set=ops,
                            status=disposition([q['classification'] for q in qualifications.values()],bool(qualifications)))
    report=dict(task='SCI-MD-RHEOLOGY-005',classification=disposition(flags,not missing and len(ends)==18,all(v['adequate'] for v in support.values()) and len(support)==2),
        comparisons=result,support=support,missing=missing,regression=regression,gates=quality,bulk=bulk,fixed_time_30s=fixed,
        executions=dict(planned=18,started=len(starts),completed=len(ends),failed=sum(e['status']=='FAILED' for e in events),recoveries=sum('__recovery' in x for x in starts)),
        physical_validation='NOT_ESTABLISHED',engineering='PASS' if not missing else 'INCOMPLETE_OR_FAILED',source_admissibility='SOURCE_CONDITIONED_ASSUMPTIONS_RETAINED',
        freeze_sha256=sha(DOC/'FREEZE.json'))
    write(a.output/'METRICS.json',report);write(a.output/'RUNS.json',dict(events=events,bulk_receipts={slot:json.loads((a.artifacts/e['attempt']/'BULK_RECEIPT.json').read_text()) for slot,e in ends.items() if matrix()[slot][3]=='G'}))
    return report,data

def main():
    p=argparse.ArgumentParser()
    for k in ('artifacts','baseline','coupled','context','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();report,_=analyze(a);print(report['classification'])
if __name__=='__main__':main()
