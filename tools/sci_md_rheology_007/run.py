"""Audit-gated bounded native execution with durable attempts and hash-valid resume."""
import argparse,fcntl,json,os,time
from .common import *
from .observer import read,adapt
from .short import fields

def run(art,slot,reason=None):
    f=check(art,audit=True)
    if slot not in f['matrix']:raise ValueError('undeclared slot')
    science=art/'science';science.mkdir(exist_ok=True);ledger=science/'INVOCATIONS.jsonl'
    def append(e):
        with ledger.open('a') as out:out.write(json.dumps(e,sort_keys=True)+'\n');out.flush();os.fsync(out.fileno())
    with (science/'ledger.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        events=[json.loads(l) for l in ledger.read_text().splitlines()] if ledger.exists() else []
        ends=[e for e in events if e['slot']==slot and e['status']=='COMPLETE']
        if ends:
            e=ends[-1]
            for p,h in e['files'].items():
                if sha(science/e['id']/p)!=h:raise ValueError('completed evidence changed '+slot)
            print(slot+' REUSED_COMPLETE',flush=True);return
        starts=[e for e in events if e['status']=='STARTED'];prior=[e for e in starts if e['slot']==slot]
        if len(starts)>=f['max_full_attempts']:raise ValueError('absolute attempt ceiling')
        if sum(e['recovery_reason'] is not None for e in starts)>=4 and prior:raise ValueError('recovery ceiling')
        if prior and (not reason or any(not any(e['id']==s['id'] and e['status']=='FAILED' for e in events) for s in prior)):raise ValueError('terminal failure and nonsemantic reason required')
        if reason and not prior:raise ValueError('no failed slot')
        ident=slot+('__recovery'+str(len(prior)) if prior else '')
        if (science/ident).exists():raise ValueError('refuse existing directory')
        append(dict(id=ident,slot=slot,status='STARTED',recovery_reason=reason,freeze_sha256=sha(DOC/'FREEZE.json'),executable_sha256=sha(art/'bin/espressoWholePullFoam'),utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()))
    t=time.monotonic()
    try:
        spec=json.loads((art/'SCENARIOS.json').read_text())[slot]
        case=execute(spec,science/ident,art/'bin/espressoWholePullFoam')
        d=adapt(read(case/TRACE),'uniform')
        ff=fields(case,spec['geometry']['axial_cells'],2,30)
        event=dict(id=ident,slot=slot,status='COMPLETE',elapsed_s=time.monotonic()-t,cells=2*spec['geometry']['axial_cells'],balance=d['balance'],fields=ff,files={str(p.relative_to(science/ident)):sha(p) for p in sorted((science/ident).rglob('*')) if p.is_file()})
    except BaseException as e:append(dict(id=ident,slot=slot,status='FAILED',elapsed_s=time.monotonic()-t,reason=str(e)));raise
    append(event);print(slot+' COMPLETE',flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--slot');p.add_argument('--recovery-reason');a=p.parse_args()
    if a.slot:run(a.artifacts,a.slot,a.recovery_reason)
    else:
        for slot in matrix():run(a.artifacts,slot)
if __name__=='__main__':main()
