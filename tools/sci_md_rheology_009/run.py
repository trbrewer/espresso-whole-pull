"""Durable bounded execution; stages cannot cross missing qualification gates."""
import argparse
import fcntl
import os
import time
from .common import *
from tools.sci_md_rheology_008.run import append, next_attempt
from tools.sci_md_rheology_008.geometry import fields
from tools.sci_md_rheology_002.verify import traces

def run(art,stage,slot):
    short=stage=='short';reg=stage=='regression'
    verify(art,'PREPARATION.json' if short else 'FREEZE.json',audit=not short)
    files={'short':'SHORT_SCENARIOS','control':'CONTROLS','C':'SCENARIOS','E2':'SCENARIOS','regression':'REGRESSIONS'}
    specs=json.loads((art/(files[stage]+'.json')).read_text())
    if slot not in specs or (stage in ('C','E2') and matrix()[slot]['model']!=stage):raise ValueError('undeclared slot')
    if stage in ('C','E2'):
        if json.loads((DOC/'COMPATIBILITY.json').read_text())['status']!='PASS':raise ValueError('compatibility gate')
    if stage=='E2':
        sealed=json.loads((DOC/'SUPPORT.json').read_text())
        if sha(art/'SUPPORT.json')!=sha(DOC/'SUPPORT.json'):raise ValueError('support changed')
        for k,h in sealed['C_traces'].items():
            if sha(art/'full'/k/'case'/TRACE)!=h:raise ValueError('C support evidence changed')
    parent=art/('short' if short else 'regression' if reg else 'full');parent.mkdir(exist_ok=True)
    ledger=parent/'INVOCATIONS.jsonl'
    with (parent/'ledger.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        events=[json.loads(x) for x in ledger.read_text().splitlines()] if ledger.exists() else []
        complete=[e for e in events if e['slot']==slot and e['status']=='COMPLETE']
        if complete:
            e=complete[-1]
            for p,h in e['files'].items():
                if sha(parent/slot/p)!=h:raise ValueError('completed evidence changed')
            return e
        requalify=short and slot=='C_double' and any(e['slot']==slot and e['status']=='FAILED' and e.get('reason')=='missing/duplicate/misaligned native pressure intervals' for e in events)
        ident=slot if requalify else next_attempt(events,slot,None,14 if short else 6 if reg else 52,0 if short or reg else 4)
        exe=art/'bin'/('accepted' if reg and slot.endswith('_accepted') else 'espressoWholePullFoam')
        append(ledger,dict(id=ident,slot=slot,stage=stage,status='REQUALIFICATION_STARTED' if requalify else 'STARTED',scenario_sha256=digest(specs[slot]),executable_sha256=sha(exe)))
    start=time.monotonic();s=specs[slot];directory=parent/slot
    try:
        mpi=short and slot.endswith('_mpi')
        case=directory/'case' if requalify else execute(s,directory,exe,mpi)
        quality={}
        if not reg:
            raw=read(case/TRACE);d=native(raw,s['time']['end_s']);quality['balance']=d['balance']
            quality['pressure']=pressure_audit(raw,traces(case),s)
            quality['pressure']['pressure_trace_sha256']=sha(case/'postProcessing/wholePull/0/traces.csv')
            if not mpi:
                ff=fields(case,s['geometry']['axial_cells'],s['geometry']['radial_cells'],s['time']['end_s'],short and slot.endswith(('_dynamic','_repeat')))
                for k,r in [('final_remaining_kg','remaining_kg'),('final_stored_solute_kg','stored_solute_kg'),('inner_remaining_kg','inner_remaining_kg')]:
                    if abs(ff[k]-raw[r][-1])>1e-10:raise ValueError('field mass accounting '+k)
                quality['fields']=ff
        e=dict(id=ident,slot=slot,stage=stage,status='COMPLETE',elapsed_s=time.monotonic()-start,cells=s['geometry']['axial_cells']*s['geometry']['radial_cells'],quality=quality,files={str(p.relative_to(directory)):sha(p) for p in sorted(directory.rglob('*')) if p.is_file()})
    except BaseException as error:
        append(ledger,dict(id=ident,slot=slot,stage=stage,status='FAILED',elapsed_s=time.monotonic()-start,error_type=type(error).__name__,reason=str(error)));raise
    append(ledger,e);print(slot+' COMPLETE',flush=True);return e

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--stage',choices=('control','regression','C','E2'),required=True);p.add_argument('--slot');a=p.parse_args()
    names={'control':'CONTROLS','regression':'REGRESSIONS','C':'SCENARIOS','E2':'SCENARIOS'}
    slots=json.loads((a.artifacts/(names[a.stage]+'.json')).read_text())
    for slot in slots:
        if a.stage in ('C','E2') and matrix()[slot]['model']!=a.stage:continue
        if not a.slot or slot==a.slot:run(a.artifacts,a.stage,slot)
if __name__=='__main__':main()
