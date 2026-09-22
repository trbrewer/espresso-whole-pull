"""Frozen 22-slot native campaign, durable attempt ledger and bounded recovery."""
import argparse,fcntl,hashlib,json,os
from pathlib import Path
from .common import ROOT,DOC,TRACE,execute,sha,write
from .observer import read,validate
from .short import discrepancy
from tools.sci_md_rheology_002.run import rows
from tools.sci_md_rheology_005.analyze import qualify

def run(art,accepted,identity,recovery_reason=None):
    freeze=json.loads((DOC/'FREEZE.json').read_text());exe=art/'bin/espressoWholePullFoam'
    if hashlib.sha256(str(art.resolve()).encode()).hexdigest()!=freeze['artifact_root_sha256']:raise ValueError('execution root changed')
    for path,h in freeze['files'].items():
        if sha(ROOT/path)!=h:raise ValueError('frozen file changed '+path)
    if sha(exe)!=freeze['executable_sha256'] or sha(art/'SCENARIOS.json')!=freeze['scenarios_sha256']:raise ValueError('executable/scenario changed')
    for name,h in freeze['tables'].items():
        if sha(art/'tables'/name)!=h:raise ValueError('table changed')
    if identity not in freeze['full_matrix']:raise ValueError('undeclared slot')
    science=art/'science';science.mkdir(exist_ok=True);ledger=science/'INVOCATIONS.jsonl'
    def append(event):
        with ledger.open('a') as f:f.write(json.dumps(event,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
    with (science/'ledger.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        events=[json.loads(l) for l in ledger.read_text().splitlines()] if ledger.exists() else []
        starts=[v for v in events if v['status']=='STARTED'];previous=[v for v in starts if v['slot']==identity]
        if len(starts)>=26:raise ValueError('full attempt ceiling')
        if any(v.get('slot')==identity and v['status']=='COMPLETE' for v in events):raise ValueError('completed slot')
        ident=identity
        if previous:
            if not recovery_reason or any(not any(e['id']==v['id'] and e['status']=='FAILED' for e in events) for v in previous):raise ValueError('documented failed recovery required')
            if sum('__recovery' in v['id'] for v in starts)>=4:raise ValueError('recovery ceiling')
            ident+='__recovery'+str(len(previous))
        elif recovery_reason:raise ValueError('no failed slot')
        append(dict(id=ident,slot=identity,status='STARTED',freeze_sha256=sha(DOC/'FREEZE.json'),executable_sha256=sha(exe),recovery_reason=recovery_reason))
    try:
        spec=json.loads((art/'SCENARIOS.json').read_text())[identity]
        case=execute(spec,science/ident,exe)
        control=freeze['full_matrix'][identity][1]=='control'
        if control:
            d=rows(case);qualify(d)
            reuse=json.loads((DOC/'REUSE.json').read_text())['controls'][identity]
            oldcase=accepted/'science'/reuse['accepted_id']/'case';old=rows(oldcase)
            if sha(oldcase/'postProcessing/wholePull/0/aggregate_intervals.csv')!=reuse['intervals_sha256']:raise ValueError('accepted evidence changed')
            err=discrepancy(d,old)
            if err>1e-10:raise ValueError('legacy compatibility '+str(err))
            trace=case/'postProcessing/wholePull/0/aggregate_intervals.csv'
        else:
            validate(read(case));err=None;trace=case/TRACE
        event=dict(id=ident,slot=identity,status='COMPLETE',intervals_sha256=sha(trace),scenario_sha256=sha(science/ident/'scenario.json'),compatibility_normalized=err,files={str(p.relative_to(science/ident)):sha(p) for p in sorted((science/ident).rglob('*')) if p.is_file() and ('postProcessing' in p.parts or p.suffix=='.log' or p.name=='scenario.json')})
    except BaseException as e:
        append(dict(id=ident,slot=identity,status='FAILED',reason=str(e)));raise
    append(event);print(identity+' COMPLETE',flush=True)

def main():
    p=argparse.ArgumentParser()
    for k in ('artifacts','accepted'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--identity',required=True);p.add_argument('--recovery-reason');a=p.parse_args()
    run(a.artifacts,a.accepted,a.identity,a.recovery_reason)
if __name__=='__main__':main()
