"""Compatibility gates, sealed reference support, and 24 separate decisions."""
import argparse
from .common import *
from tools.sci_md_rheology_002.verify import traces
from tools.sci_md_rheology_008.arithmetic import audit

def payload(a,b):
    if set(a)!=set(b):raise ValueError('numerical column mismatch')
    errors={}
    for k in a:
        if a[k].shape!=b[k].shape:raise ValueError('numerical row mismatch')
        if not np.array_equal(np.isfinite(a[k]),np.isfinite(b[k])):raise ValueError('finiteness drift')
        if not np.isfinite(a[k]).all():continue
        errors[k]=float(max(abs(a[k]-b[k])))/max(1.,float(max(abs(b[k]))))
    if max(errors.values())>1e-10:raise ValueError('accepted numerical regression drift')
    return errors

def complete(art,group,required):
    ledger=art/group/'INVOCATIONS.jsonl';events=[json.loads(x) for x in ledger.read_text().splitlines()]
    result={}
    for slot in required:
        candidates=[e for e in events if e['slot']==slot and e['status']=='COMPLETE']
        if len(candidates)!=1:raise ValueError('missing/duplicate completed evidence '+slot)
        e=candidates[0]
        for p,h in e['files'].items():
            if sha(art/group/slot/p)!=h:raise ValueError('evidence changed '+slot)
        result[slot]=e
    return result

def compatibility(art):
    verify(art,'FREEZE.json',True)
    specs=json.loads((art/'CONTROLS.json').read_text());refs=json.loads((art/'REFERENCES.json').read_text())
    complete(art,'full',specs);reg=json.loads((art/'REGRESSIONS.json').read_text());complete(art,'regression',reg)
    checks={}
    for key,r in refs.items():
        if sha(Path(r['trace']))!=r['sha256']:raise ValueError('historical reference changed')
        legacy=read(art/'full'/(key+'_legacy')/'case'/TRACE);flat=read(art/'full'/(key+'_flat')/'case'/TRACE)
        checks[key]=dict(legacy_vs_accepted=payload(legacy,read(Path(r['trace']))),flat_vs_new_legacy=payload(flat,legacy))
    regressions={}
    for key in reg:
        if key.endswith('_new'):
            old=key[:-4]+'_accepted'
            regressions[key]=payload(traces(art/'regression'/key/'case'),traces(art/'regression'/old/'case'))
    write(DOC/'COMPATIBILITY.json',dict(status='PASS',verdict='PRESSURE_HISTORY_LOCAL_VISCOSITY_COMPATIBILITY_QUALIFIED',controls=checks,regressions=regressions,full_controls=16,regression_runs=6))

def seal(art):
    verify(art,'FREEZE.json',True)
    if (DOC/'SUPPORT.json').exists() or (art/'SUPPORT.json').exists():raise ValueError('support already sealed')
    if json.loads((DOC/'COMPATIBILITY.json').read_text())['status']!='PASS':raise ValueError('compatibility')
    required={k for k,v in matrix().items() if v['model']=='C'};complete(art,'full',required)
    terminals={};hashes={}
    for k in sorted(required):
        p=art/'full'/k/'case'/TRACE;d=native(read(p));terminals[k]=float(d['water_kg'][-1]+d['solute_kg'][-1]);hashes[k]=sha(p)
    record=dict(B_star_kg=support(terminals),C_terminals_kg=terminals,C_traces=hashes,freeze_sha256=sha(DOC/'FREEZE.json'),rule='Decimal floor(0.95*minimum of nine qualified C terminal B, 1e-9 kg), separately per history')
    write(art/'SUPPORT.json',record);write(DOC/'SUPPORT.json',record)
    write(DOC/'SUPPORT_RECEIPT.json',dict(sha256=sha(DOC/'SUPPORT.json')))

def checked_support(art):
    sealed=json.loads((DOC/'SUPPORT.json').read_text())
    receipt=json.loads((DOC/'SUPPORT_RECEIPT.json').read_text())
    if sha(DOC/'SUPPORT.json')!=receipt['sha256'] or sha(art/'SUPPORT.json')!=receipt['sha256']:
        raise ValueError('support receipt mismatch')
    if sealed['freeze_sha256']!=sha(DOC/'FREEZE.json'):raise ValueError('support freeze mismatch')
    required={k for k,v in matrix().items() if v['model']=='C'}
    complete(art,'full',required)
    terminals={};hashes={}
    for k in sorted(required):
        path=art/'full'/k/'case'/TRACE;d=native(read(path))
        terminals[k]=float(d['water_kg'][-1]+d['solute_kg'][-1]);hashes[k]=sha(path)
    if hashes!=sealed['C_traces'] or terminals!=sealed['C_terminals_kg'] or support(terminals)!=sealed['B_star_kg']:
        raise ValueError('support changed from complete qualified reference rule')
    return sealed

def analyze(art):
    verify(art,'FREEZE.json',True);complete(art,'full',matrix())
    sealed=checked_support(art);data={k:native(read(art/'full'/k/'case'/TRACE)) for k in matrix()};cases={};coverage={}
    for k,d in data.items():
        end=float(sealed['B_star_kg'][matrix()[k]['history']]);terminal=float(d['water_kg'][-1]+d['solute_kg'][-1]);coverage[k]=dict(terminal_beverage_kg=terminal,B_star_kg=end,reaches_support=terminal>=end,scored_fraction_of_terminal=end/terminal)
    for law in LAWS:
        for h in HISTORIES:
            end=float(sealed['B_star_kg'][h]);values={};arithmetic={}
            for r in sets(law)+('radial',):
                e=data[f'E2_{law}_{h}_'+('base' if r=='radial' else r)];c=data[f'C_{law}_{h}_{r}'];values[r]=metrics(e,c,end);ind=audit(e,c,end)
                arithmetic[r]={k:abs(values[r][k]-ind[k]) for k in BUDGETS if values[r].get(k) is not None and k in ind}
            cases[law+'_'+h]=dict(variants=values,arithmetic=arithmetic,decisions={k:qualify_metric(values,arithmetic,law,k) for k in BUDGETS})
    decisions=[d['decision'] for c in cases.values() for d in c['decisions'].values()]
    result='E2_PRESSURE_HISTORY_TRANSFER_INSUFFICIENT' if 'FAIL' in decisions else 'E2_PRESSURE_HISTORY_TRANSFER_SUFFICIENT_FOR_TESTED_OUTPUTS' if decisions==['PASS']*24 else 'E2_PRESSURE_HISTORY_TRANSFER_UNRESOLVED'
    write(DOC/'METRICS.json',dict(disposition=result,cases=cases,physical_validation='NOT_ESTABLISHED'));write(DOC/'COVERAGE.json',coverage)
    accounting={}
    for group in ('short','regression','full'):
        events=[json.loads(x) for x in (art/group/'INVOCATIONS.jsonl').read_text().splitlines()]
        accounting[group]=dict(started=sum(e['status']=='STARTED' for e in events),completed=sum(e['status']=='COMPLETE' for e in events),failed=sum(e['status']=='FAILED' for e in events),attempts=[{k:v for k,v in e.items() if k!='files'} for e in events],ledger_sha256=sha(art/group/'INVOCATIONS.jsonl'))
    write(DOC/'RUNS.json',accounting)

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--stage',choices=('compatibility','support','analyze'),required=True);a=p.parse_args()
    {'compatibility':compatibility,'support':seal,'analyze':analyze}[a.stage](a.artifacts)
if __name__=='__main__':main()
