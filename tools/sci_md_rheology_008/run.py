"""Durable launch accounting and immutable completed-slot reuse."""
import argparse
import fcntl
import json
import os
import time
from datetime import datetime, timezone
from .common import *
from .observer import native, read
from .geometry import fields

def append(path,event):
    with path.open('a') as f:
        f.write(json.dumps(event,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())

def next_attempt(events,slot,reason,ceiling,recoveries):
    starts=[e for e in events if e['status']=='STARTED'];prior=[e for e in starts if e['slot']==slot]
    if len(starts)>=ceiling:raise ValueError('absolute attempt ceiling')
    if prior:
        if not reason or sum(e.get('recovery_reason') is not None for e in starts)>=recoveries:
            raise ValueError('nonsemantic recovery reason/ceiling')
        if any(not any(e['id']==s['id'] and e['status']=='FAILED' for e in events) for s in prior):
            raise ValueError('unresolved start; no duplicate launch')
    elif reason:raise ValueError('no failed slot to recover')
    return slot+('__recovery'+str(len(prior)) if prior else '')

def run(art,slot,reason=None,short=False):
    if short:
        prep=json.loads((art/'PREPARATION.json').read_text())
        if sha(art/'SHORT_SCENARIOS.json')!=prep['short_sha256'] or sha(art/'bin/espressoWholePullFoam')!=EXE_SHA:
            raise ValueError('short freeze changed')
        for p,h in prep['tools'].items():
            if sha(ROOT/p)!=h:raise ValueError('short tool changed: '+p)
        for p,h in prep['tables'].items():
            if sha(art/'tables'/p)!=h:raise ValueError('short table changed')
        specs=json.loads((art/'SHORT_SCENARIOS.json').read_text());ceiling,reserve=14,2
    else:
        f=check(art,audit=True);specs=json.loads((art/'SCENARIOS.json').read_text());ceiling,reserve=f['max_full_attempts'],4
    if slot not in specs:raise ValueError('undeclared slot')
    parent=art/('short' if short else 'science');parent.mkdir(exist_ok=True);ledger=parent/'INVOCATIONS.jsonl'
    with (parent/'ledger.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        events=[json.loads(s) for s in ledger.read_text().splitlines()] if ledger.exists() else []
        complete=[e for e in events if e['slot']==slot and e['status']=='COMPLETE']
        if complete:
            e=complete[-1]
            for p,h in e['files'].items():
                if sha(parent/e['id']/p)!=h:raise ValueError('completed evidence changed')
            print(slot+' REUSED_COMPLETE',flush=True);return e
        ident=next_attempt(events,slot,reason,ceiling,reserve)
        if (parent/ident).exists():raise ValueError('refuse overwrite')
        append(ledger,dict(id=ident,slot=slot,status='STARTED',recovery_reason=reason,utc=datetime.now(timezone.utc).isoformat(),executable_sha256=EXE_SHA,scenario_sha256=digest(specs[slot])))
    start=time.monotonic();s=specs[slot];directory=parent/ident
    try:
        mpi=short and slot=='E2_mpi'
        case=execute(s,directory,art/'bin/espressoWholePullFoam',mpi)
        raw=read(case/TRACE);d=native(raw,s['time']['end_s'])
        ff={} if mpi else fields(case,s['geometry']['axial_cells'],s['geometry']['radial_cells'],s['time']['end_s'],short and slot in ('E2_dynamic','E2_repeat'))
        if ff:
            for key,native_key in [('final_remaining_kg','remaining_kg'),('final_stored_solute_kg','stored_solute_kg'),('inner_remaining_kg','inner_remaining_kg')]:
                if abs(ff[key]-raw[native_key][-1])>1e-10:raise ValueError('independent field aggregation '+key)
        generated=json.loads((case/'CASE_SCENARIO_V0_1_4.json').read_text())
        if generated['coffee_bed']['dry_dose_kg']!=.020:raise ValueError('dose mapping')
        inventory=raw['remaining_kg'][0]+raw['stored_solute_kg'][0]+raw['solute_kg'][0]+raw['inlet_loss_kg'][0]
        if abs(inventory-.0056)>1e-10:raise ValueError('initial inventory')
        e=dict(id=ident,slot=slot,status='COMPLETE',elapsed_s=time.monotonic()-start,cells=s['geometry']['axial_cells']*s['geometry']['radial_cells'],balance=d['balance'],fields=ff,initial_inventory_kg=float(inventory),files={str(p.relative_to(directory)):sha(p) for p in sorted(directory.rglob('*')) if p.is_file()})
    except BaseException as error:
        append(ledger,dict(id=ident,slot=slot,status='FAILED',elapsed_s=time.monotonic()-start,error_type=type(error).__name__,reason=str(error)));raise
    append(ledger,e);print(slot+' COMPLETE',flush=True);return e

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--slot');p.add_argument('--recovery-reason');a=p.parse_args()
    if a.slot:run(a.artifacts,a.slot,a.recovery_reason)
    else:
        for slot in matrix():run(a.artifacts,slot)
if __name__=='__main__':main()
