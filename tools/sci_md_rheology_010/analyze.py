"""Seal reference-only support; separate transfer and modeled contrast decisions."""
import argparse
from .common import *
from .run import complete, events, qualify
from .prepare import accepted_records
from tools.sci_md_rheology_008.arithmetic import audit


def reference_data(art,requalify=False):
    accepted=Path(json.loads((art/'LOCATIONS.json').read_text())['accepted'])
    old=accepted_records(accepted);new=complete(art,references());data={};terminals={};hashes={};quality={}
    oldspec=json.loads((accepted/'SCENARIOS.json').read_text());newspec=json.loads((art/'SCENARIOS.json').read_text())
    for label,root,records,specs in [('old',accepted/'full',old,oldspec),('new',art/'runs',new,newspec)]:
        for k,e in records.items():
            key=label+'_'+k;case=root/e['id']/'case';d=native(read(case/TRACE));data[key]=d
            terminals[key]=float(d['water_kg'][-1]+d['solute_kg'][-1]);hashes[key]=sha(case/TRACE)
            quality[key]=qualify(case,specs[k]) if requalify else e['quality']
    return data,terminals,hashes,quality


def seal(art):
    verify(art,True,True)
    if (DOC/'SUPPORT.json').exists() or (art/'SUPPORT.json').exists():raise ValueError('support already sealed')
    if any(e['stage']=='E2' and e['status']=='STARTED' for e in events(art)):raise ValueError('E2 preceded support')
    _,terminals,hashes,quality=reference_data(art,True)
    record=dict(B_star_kg=support(terminals),C_terminals_kg=terminals,C_traces=hashes,
                freeze_sha256=sha(DOC/'FREEZE.json'),attempt_ledger_at_seal_sha256=sha(art/'ATTEMPTS.jsonl'),
                rule='Decimal floor_to_1e-9kg(0.95 * min(all 18 qualified C terminals per history)); old+new, both laws, all refinements')
    write(art/'SUPPORT.json',record);write(DOC/'SUPPORT.json',record)
    write(DOC/'SUPPORT_RECEIPT.json',dict(sha256=sha(DOC/'SUPPORT.json')))
    write(DOC/'REFERENCE_QUALIFICATION.json',quality)
    from tools.sci_md_rheology_008.run import append
    append(art/'ATTEMPTS.jsonl',dict(id='support',slot='support',stage='support',status='SUPPORT_SEALED',sha256=sha(DOC/'SUPPORT.json')))


def checked_support(art):
    sealed=json.loads((DOC/'SUPPORT.json').read_text());receipt=json.loads((DOC/'SUPPORT_RECEIPT.json').read_text())
    if sha(DOC/'SUPPORT.json')!=receipt['sha256'] or sha(art/'SUPPORT.json')!=receipt['sha256']:
        raise ValueError('support hash mismatch')
    if sealed['freeze_sha256']!=sha(DOC/'FREEZE.json'):raise ValueError('support freeze mismatch')
    _,terminals,hashes,_=reference_data(art)
    if hashes!=sealed['C_traces'] or terminals!=sealed['C_terminals_kg'] or support(terminals)!=sealed['B_star_kg']:
        raise ValueError('support no longer matches complete C evidence')
    ev=events(art);indices=[i for i,e in enumerate(ev) if e['status']=='SUPPORT_SEALED' and e['sha256']==receipt['sha256']]
    if len(indices)!=1 or any(e['stage']=='E2' and e['status']=='STARTED' for e in ev[:indices[0]]):
        raise ValueError('support execution order')
    return sealed


def score_case(data,law,h,end,secondary=False):
    values={};arithmetic={}
    for r in sets(law)+('radial',):
        ka,kb=pair_keys(law,h,r,secondary)
        if ka not in data or kb not in data:continue
        a,b=data[ka],data[kb];values[r]=metrics(a,b,end);ind=audit(a,b,end)
        arithmetic[r]={k:abs(values[r][k]-ind[k]) for k in BUDGETS if values[r].get(k) is not None and k in ind}
    keys=('E_Spath','D_TDS_pp') if secondary else BUDGETS
    result=dict(variants=values,arithmetic=arithmetic,
                decisions={k:decision(values,arithmetic,law,k,secondary) for k in keys})
    if secondary:
        # E/C are inherited observer keys only: E=new annulus-fast C; C=old core-fast C.
        delivery=values.get('base',{}).get('delivery')
        result['signed_fraction_TDS_new_minus_old_pp']=([a-b for a,b in zip(delivery['E']['TDS_percent'],delivery['C']['TDS_percent'])] if delivery else None)
        result['reference']='old core-fast C';result['comparison']='new annulus-fast C'
    return result


def accounting(art):
    ev=events(art);starts=[e for e in ev if e['status']=='STARTED'];done=[e for e in ev if e['status']=='COMPLETE']
    if len(starts)>44 or sum(bool(e.get('recovery')) for e in starts)>2:raise ValueError('attempt ceiling')
    return dict(planned_short=10,planned_full=32,actual_native_launches=len(starts),
        short_launches=sum(e['stage']=='short' for e in starts),C_launches=sum(e['stage']=='C' for e in starts),
        E2_launches=sum(e['stage']=='E2' for e in starts),qualified_completions=len(done),
        failed=sum(e['status']=='FAILED' for e in ev),startup_failures=sum(e['status']=='FAILED' and not e.get('integrating') for e in ev),
        infrastructure_retries=sum(bool(e.get('recovery')) for e in starts),
        native_completed=sum(e['status']=='NATIVE_COMPLETED' for e in ev),
        pending_attempts=[e['id'] for e in starts if not any(x['id']==e['id'] and x['status'] in ('COMPLETE','FAILED') for x in ev)],
        events=[{k:v for k,v in e.items() if k!='files'} for e in ev],ledger_sha256=sha(art/'ATTEMPTS.jsonl'))


def analyze(art):
    verify(art,True,True);sealed=checked_support(art)
    data,_,_,_=reference_data(art);quality={};missing={}
    for k,v in matrix().items():
        if v['model']!='E2':continue
        try:
            e=complete(art,[k])[k];case=art/'runs'/e['id']/'case'
            data['new_'+k]=native(read(case/TRACE));quality[k]=e['quality']
        except (ValueError,OSError) as error:missing[k]=str(error)
    coverage={}
    for k,d in data.items():
        h='UP' if '_UP_' in k else 'DOWN';end=float(sealed['B_star_kg'][h]);terminal=float(d['water_kg'][-1]+d['solute_kg'][-1])
        coverage[k]=dict(terminal_beverage_kg=terminal,B_star_kg=end,reaches_support=terminal>=end,scored_fraction_of_terminal=end/terminal)
    primary={};secondary={}
    for law in LAWS:
        for h in ('UP','DOWN'):
            key=law+'_'+h;end=float(sealed['B_star_kg'][h])
            primary[key]=score_case(data,law,h,end);secondary[key]=score_case(data,law,h,end,True)
    flags=[d['decision'] for c in primary.values() for d in c['decisions'].values()]
    write(DOC/'METRICS.json',dict(disposition=overall(flags),primary=primary,secondary=secondary,missing_or_invalid_candidates=missing,physical_validation='NOT_ESTABLISHED'))
    write(DOC/'COVERAGE.json',coverage);write(DOC/'QUALIFICATION.json',quality);write(DOC/'RUNS.json',accounting(art))
    write(DOC/'ARTIFACT_RECEIPT.json',dict(artifact_root_sha256=__import__('hashlib').sha256(str(art.resolve()).encode()).hexdigest(),
        ledger_sha256=sha(art/'ATTEMPTS.jsonl'),freeze_sha256=sha(DOC/'FREEZE.json'),support_sha256=sha(DOC/'SUPPORT.json'),
        runtime_sha256=sha(art/'RUNTIME.json'),executable_sha256=json.loads((DOC/'REUSE.json').read_text())['executable_sha256'],
        new_trace_hashes={e['slot']:e['files']['case/'+str(TRACE)] for e in events(art) if e['status']=='COMPLETE'},
        raw_fields_traces_tables_executable_committed=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--stage',choices=('support','analyze'),required=True);a=p.parse_args()
    (seal if a.stage=='support' else analyze)(a.artifacts)
