"""Seal reference-only support; separate transfer and modeled contrast decisions."""
import argparse
from .common import *
from .run import complete, events, qualify
from .prepare import accepted_records
from .arithmetic import audit


def reference_data(art,requalify=False):
    accepted=Path(json.loads((art/'LOCATIONS.json').read_text())['accepted'])
    old=accepted_records(accepted);new=complete(art,references());data={};terminals={};hashes={};quality={}
    oldspec=json.loads((accepted/'SCENARIOS.json').read_text());newspec=json.loads((art/'SCENARIOS.json').read_text())
    for label,root,records,specs in [('old',accepted/'full',old,oldspec),('new',art/'runs',new,newspec)]:
        for k,e in records.items():
            key=label+'_'+k;case=root/e['id']/'case';d=native(read(case/TRACE),specs[k]);data[key]=d
            
            from decimal import localcontext
            with localcontext() as ctx:
                ctx.prec=80
                terminals[key]=str(Decimal.from_float(float(d['water_kg'][-1]))+Decimal.from_float(float(d['solute_kg'][-1])));hashes[key]=sha(case/TRACE)
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


def score_case(data,law,h,end,primary=False):
    values={};arithmetic={}
    resolutions=('base','temporal','axial')+(('property',) if law.startswith('SW') else ())+(('A_radial','B_radial') if primary else ('radial',))
    for r in resolutions:
        if primary:
            ar='radial' if r=='A_radial' else 'base' if r=='B_radial' else r
            br='radial' if r=='B_radial' else 'base' if r=='A_radial' else r
            ka='new_C_'+law+'_'+h+'_'+br;kb='old_C_'+law+'_'+h+'_'+ar
        else:
            ka='new_E2_'+law+'_'+h+'_'+('base' if r=='radial' else r)
            kb='new_C_'+law+'_'+h+'_'+r
        if ka not in data or kb not in data:continue
        a,b=data[ka],data[kb];values[r]=metrics(a,b,end);ind=audit(a,b,end)
        arithmetic[r]={k:abs(values[r][k]-ind[k]) for k in BUDGETS if values[r].get(k) is not None and k in ind}
    keys=('E_Spath','D_TDS_pp') if primary else BUDGETS
    return dict(variants=values,arithmetic=arithmetic,
                reference='C_A' if primary else 'C_B',comparison='C_B' if primary else 'E2_B',
                decisions={k:decision(values,arithmetic,law,k,primary) for k in keys})


def primary(art):
    verify(art,True,True);sealed=checked_support(art)
    if (DOC/'PRIMARY.json').exists():raise ValueError('primary already sealed')
    data,_,_,_=reference_data(art);results={}
    for law in LAWS:
        for h in ('UP','DOWN'):
            results[law+'_'+h]=score_case(data,law,h,float(sealed['B_star_kg'][h]),True)
    flags=[d['decision'] for c in results.values() for d in c['decisions'].values()]
    record=dict(disposition=branch(flags),cases=results,freeze_sha256=sha(DOC/'FREEZE.json'),support_sha256=sha(DOC/'SUPPORT.json'))
    write(DOC/'PRIMARY.json',record)
    write(DOC/'PRIMARY_RECEIPT.json',dict(sha256=sha(DOC/'PRIMARY.json')))
    from tools.sci_md_rheology_008.run import append
    append(art/'ATTEMPTS.jsonl',dict(id='primary',slot='primary',stage='primary',status='PRIMARY_SCORED',sha256=sha(DOC/'PRIMARY.json')))
    return record


def checked_primary(art,require_trigger=True):
    checked_support(art)
    p=json.loads((DOC/'PRIMARY.json').read_text());receipt=json.loads((DOC/'PRIMARY_RECEIPT.json').read_text())
    if sha(DOC/'PRIMARY.json')!=receipt['sha256'] or p['support_sha256']!=sha(DOC/'SUPPORT.json') or p['freeze_sha256']!=sha(DOC/'FREEZE.json'):raise ValueError('primary receipt changed')
    flags=[d['decision'] for c in p['cases'].values() for d in c['decisions'].values()]
    if p['disposition']!=branch(flags):raise ValueError('primary branch mismatch')
    ev=events(art);idx=[i for i,e in enumerate(ev) if e['status']=='PRIMARY_SCORED' and e['sha256']==receipt['sha256']]
    if len(idx)!=1 or any(e['stage']=='E2' and e['status']=='STARTED' for e in ev[:idx[0]]):raise ValueError('primary execution order')
    if require_trigger and 'MATERIAL' not in flags:raise ValueError('conditional E2 not triggered')
    return p

def accounting(art):
    ev=events(art);starts=[e for e in ev if e['status']=='STARTED'];done=[e for e in ev if e['status']=='COMPLETE']
    if len(starts)>48 or sum(bool(e.get('recovery')) for e in starts)>2:raise ValueError('attempt ceiling')
    return dict(planned_short=14,planned_full=32,actual_native_launches=len(starts),
        short_launches=sum(e['stage']=='short' for e in starts),C_launches=sum(e['stage']=='C' for e in starts),
        E2_launches=sum(e['stage']=='E2' for e in starts),qualified_completions=len(done),
        preparation_failures=sum(e['status']=='PREPARATION_FAILED' for e in ev),
        integration_starts=sum(e['status']=='INTEGRATION_STARTED' for e in ev)+sum(e['status']=='FAILED' and e.get('integrating',False) for e in ev),
        failed=sum(e['status']=='FAILED' for e in ev),startup_failures=sum(e['status']=='FAILED' and not e.get('integrating') for e in ev),
        infrastructure_retries=sum(bool(e.get('recovery')) for e in starts),
        native_completed=sum(e['status']=='NATIVE_COMPLETED' for e in ev),
        pending_attempts=[e['id'] for e in starts if not any(x['id']==e['id'] and x['status'] in ('COMPLETE','FAILED') for x in ev)],
        events=[{k:v for k,v in e.items() if k!='files'} for e in ev],ledger_sha256=sha(art/'ATTEMPTS.jsonl'))


def analyze(art):
    verify(art,True,True);sealed=checked_support(art)
    p=checked_primary(art,False);trigger='CONDITIONAL_E2_REQUIRED' in p['disposition']
    data,_,_,_=reference_data(art);quality={};missing={}
    specs=json.loads((art/'SCENARIOS.json').read_text())
    for k,v in matrix().items():
        if v['model']!='E2' or not trigger:continue
        try:
            e=complete(art,[k])[k];case=art/'runs'/e['id']/'case'
            data['new_'+k]=native(read(case/TRACE),specs[k]);quality[k]=e['quality']
        except (ValueError,OSError) as error:missing[k]=str(error)
    coverage={}
    for k,d in data.items():
        h='UP' if '_UP_' in k else 'DOWN';end=float(sealed['B_star_kg'][h]);terminal=float(d['water_kg'][-1]+d['solute_kg'][-1])
        coverage[k]=dict(terminal_beverage_kg=terminal,B_star_kg=end,reaches_support=terminal>=end,scored_fraction_of_terminal=end/terminal)
    conditional={}
    for law in LAWS:
        for h in ('UP','DOWN'):
            key=law+'_'+h;end=float(sealed['B_star_kg'][h])
            if trigger:conditional[key]=score_case(data,law,h,end)
    flags=[d['decision'] for c in conditional.values() for d in c['decisions'].values()]
    from tools.sci_md_rheology_007.observer import verdict
    write(DOC/'METRICS.json',dict(disposition=p['disposition'],primary=p['cases'],conditional=conditional,conditional_disposition=verdict(flags,not missing) if trigger else 'E2_NOT_EXECUTED_CONDITIONAL_GATE',missing_or_invalid_candidates=missing,physical_validation='NOT_ESTABLISHED'))
    write(DOC/'COVERAGE.json',coverage);write(DOC/'QUALIFICATION.json',quality);write(DOC/'RUNS.json',accounting(art))
    write(DOC/'ARTIFACT_RECEIPT.json',dict(artifact_root_sha256=__import__('hashlib').sha256(str(art.resolve()).encode()).hexdigest(),
        ledger_sha256=sha(art/'ATTEMPTS.jsonl'),freeze_sha256=sha(DOC/'FREEZE.json'),support_sha256=sha(DOC/'SUPPORT.json'),
        runtime_sha256=sha(art/'RUNTIME.json'),executable_sha256=json.loads((DOC/'REUSE.json').read_text())['executable_sha256'],
        new_trace_hashes={e['slot']:e['files']['case/'+str(TRACE)] for e in events(art) if e['status']=='COMPLETE'},
        raw_fields_traces_tables_executable_committed=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--stage',choices=('support','primary','analyze'),required=True);a=p.parse_args()
    {'support':seal,'primary':primary,'analyze':analyze}[a.stage](a.artifacts)
