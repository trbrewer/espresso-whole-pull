"""Matched output native-to-native comparisons on prospectively shared support."""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.sci_md_rheology_001.analysis import write
from tools.sci_md_rheology_002.run import rows,CASES
from tools.sci_md_rheology_003.analyze import gates,secondary,matched
from .evidence import DOC,LAWS,SETS,matrix,check,qualify_reuse,completed
from .observer import history,common_support,compare,decide,classification,disposition,THRESHOLDS


def analyze(baseline,coupled,artifacts,output):
    baseline,coupled,artifacts,output=map(Path,(baseline,coupled,artifacts,output))
    output.mkdir(parents=True,exist_ok=False)
    freeze=check(audit=DOC/'AUDIT.json');receipt=qualify_reuse(baseline,coupled)
    starts,ends=completed(artifacts)
    data={};raw={};quality={};missing=[]
    # Coverage/state qualification precedes support construction and all discrepancies.
    for law in LAWS:
        for r in (SETS[:3] if law=='TR_LINEAR' else SETS):
            wr='base' if r=='property' else r
            for c in CASES:
                group={};rr={}
                for arm in ('W','C','N'):
                    path=baseline/f'{wr}_{c}_{arm}'
                    if law!='TR_LINEAR' and arm=='C':path=coupled/f'{r}_{c}_{law}'
                    if law!='TR_LINEAR' and arm=='N':
                        if f'{r}_{c}_N' not in ends:
                            missing.append(f'{law}/{r}/{c}/N');continue
                        path=artifacts/f'{r}_{c}_N'
                    d=rows(path/'case');g=gates(d)
                    if not g['source_domain_pass'] or not g['numerical_state_pass']:
                        raise ValueError('inherited state gate failed: '+str(path.name))
                    h=history(d)
                    if np.any(d['remaining_kg']> .0056+1e-10) or np.any(d['stored_solute_kg'] < -1e-12):
                        raise ValueError('inventory bound failed')
                    group[arm]=h;rr[arm]=d
                    quality[f'{law}/{r}/{c}/{arm}']=dict(g,water_increment_error_kg=h['water_increment_error_kg'])
                data[law,r,c]=group;raw[law,r,c]=rr
                if 'N' in group:
                    matched(rr['N'],rr['W'])
                    alpha=freeze['alpha'][law][r]
                    departure=float(max(abs(rr['N']['Q_m3_s']/(alpha*rr['W']['Q_m3_s'])-1)))
                    if departure>1e-6:raise ValueError('native N hydraulic invariant failed')
                    quality[f'{law}/{r}/{c}/N']['flow_relative_departure']=departure
    support={c:common_support([h for (l,r,s),arms in data.items() if s==c for arm,h in arms.items() if arm in ('C','N')]) for c in CASES}
    coverage={f'{l}/{r}/{c}/{arm}':dict(final_B_kg=float(h['B'][-1]),final_W_kg=float(h['W'][-1]),end_s=float(h['t'][-1]))
              for (l,r,c),arms in data.items() for arm,h in arms.items()}
    write(output/'SUPPORT.json',dict(support=support,coverage=coverage,provisional=bool(missing),missing=missing))
    results={};fixed={};curves={}
    for law in LAWS:
        for c in CASES:
            key=law+'/'+c;sets={};fixed[key]={}
            for r in (SETS[:3] if law=='TR_LINEAR' else SETS):
                arms=data[law,r,c];sets[r]={};fixed[key][r]={a:secondary(d) for a,d in raw[law,r,c].items()}
                for coord in ('B','W'):
                    sets[r][coord]={}
                    for arm in ('N','W'):
                        if arm not in arms:continue
                        if arms[arm][coord][-1]<support[c][coord]:raise ValueError('W/reference does not cover support')
                        value=compare(arms['C'],arms[arm],coord,support[c][coord])
                        extended=compare(arms['C'],arms[arm],coord,support[c][coord],np.longdouble)
                        value['arithmetic_error']={m:abs(value[m]-extended[m]) for m in THRESHOLDS}
                        sets[r][coord]['C_'+arm]=value
            qualifications={}
            for coord in ('B','W'):
                qualifications[coord]={}
                for comp in ('C_N','C_W'):
                    if any(comp not in sets[r][coord] for r in sets):continue
                    terms={};flags=[]
                    for m in THRESHOLDS:
                        b=sets['base'][coord][comp][m]
                        term={r:abs(sets[r][coord][comp][m]-b) for r in SETS[1:] if r in sets}
                        if law=='TR_LINEAR':term['property']=0.
                        term['observer_arithmetic']=max(sets[r][coord][comp]['arithmetic_error'][m] for r in sets)
                        term['total']=sum(term.values())
                        term['classification']=decide(b,term['total'],m)
                        terms[m]=term;flags.append(term['classification'])
                    qualifications[coord][comp]=dict(terms=terms,classification=classification(flags))
            results[key]=dict(sets=sets,qualification=qualifications,
                classification=qualifications['B'].get('C_N',{}).get('classification','UNRESOLVED'),
                support_provisional=bool(missing))
            curves[key]=data[law,'base',c]
    report=dict(classification=disposition([r['classification'] for r in results.values()],not missing),
                comparisons=results,support=support,coverage=coverage,gates=quality,fixed_time_30s=fixed,
                executions=dict(started=len(starts),completed=len(ends),failed=sum(x not in ends for x in starts),
                                missing=missing,reused_002=18,reused_SW_C=8),reuse=receipt,
                hydraulic_classification='COUPLED_STATE_DEPENDENCE_PERSISTS; unchanged accepted 003 classifications',
                arithmetic_method='float64 versus longdouble on identical union breakpoints; observed error added to u',
                TR_property='zero: accepted law is exactly piecewise linear on its accepted table knots')
    write(output/'METRICS.json',report)
    from .plot import figures
    figures(curves,report,output)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('baseline','coupled','artifacts','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    try:r=analyze(a.baseline,a.coupled,a.artifacts,a.output)
    except (ValueError,OSError,KeyError) as e:
        a.output.mkdir(parents=True,exist_ok=True)
        write(a.output/'UNRESOLVED.json',dict(classification='PARTIALLY_QUALIFIED_OR_UNRESOLVED',dependency=str(e)))
        raise
    print(r['classification'])

if __name__=='__main__':main()
