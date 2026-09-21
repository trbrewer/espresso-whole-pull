"""Fixed 24-run campaign and four separately budgeted short invariant checks."""
import argparse
import fcntl
import json
import os
from pathlib import Path
from tools.sci_md_rheology_001.analysis import ROOT,sha,write
from tools.sci_md_rheology_002.run import scenario, execute, rows, CASES
from .laws import NEW
from .evidence import DOC, INTERVAL, reuse, check_freeze

SETS=('base','temporal','spatial','property')


def matrix(short=False):
    if short:return [(r,c,'constant_2water') for r in ('base','spatial') for c in CASES]
    return [(r,c,l) for l in NEW for r in SETS for c in CASES]


def invoke(root, ident, budget, allowed, record, callback):
    """Append and fsync STARTED before invocation; never erase or retry attempts."""
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    ledger=root/'INVOCATIONS.jsonl'
    with ledger.open('a+') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        f.seek(0);events=[json.loads(s) for s in f if s.strip()]
        started=[e for e in events if e['status']=='STARTED']
        if ident not in allowed or len(started)>=budget or any(e['id']==ident for e in started):
            raise ValueError('run budget/duplicate/identity violation')
        directory=root/ident
        if directory.exists():raise ValueError('refusing existing output directory')
        def append(obj):
            f.write(json.dumps(obj,sort_keys=True,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
        append(dict(record,id=ident,status='STARTED'))
        try:
            case=callback(directory)
            end=dict(id=ident,status='COMPLETE',intervals_sha256=sha(case/INTERVAL),
                     configuration_sha256=sha(directory/'scenario.json'),
                     logs_sha256={p.name:sha(p) for p in sorted(directory.glob('command-*.log'))})
            append(end)
        except BaseException:
            append(dict(id=ident,status='FAILED'));raise
        return case


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('artifacts','baseline','executable','tables','audit'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--short',action='store_true')
    a=p.parse_args()
    if a.artifacts.resolve().is_relative_to(ROOT):raise ValueError('artifacts must be external')
    check_freeze(a.executable,a.tables,a.audit);reuse(a.baseline)
    if not a.short:
        short=json.loads((DOC/'SHORT_CHECKS.json').read_text())
        if short['status']!='PASS' or short['freeze_sha256']!=sha(DOC/'FREEZE.json'):
            raise ValueError('short invariant qualification required')
    specs=matrix(a.short);allowed={'_'.join(x) for x in specs};checks={}
    for r,c,law in specs:
        s=scenario(c,'base' if r=='property' else r)
        table=a.tables/((NEW[0] if a.short else law)+('_refined' if r=='property' else '_base')+'.table')
        s['aggregate_viscosity']=dict(mode='observe' if a.short else 'coupled',purpose='scientific',table=str(table.resolve()))
        if a.short:
            s['time']['end_s']=.2;s['time']['delta_t_s']=.02
            s['liquid']['dynamic_viscosity_Pa_s']*=2
        ident='_'.join((r,c,law))
        case=invoke(a.artifacts,ident,4 if a.short else 24,allowed,
            dict(executable_sha256=sha(a.executable),table_sha256=sha(table),freeze_sha256=sha(DOC/'FREEZE.json')),
            lambda d:execute(s,d,a.executable))
        if a.short:
            import numpy as np
            d=rows(case);w=rows(a.baseline/f'{r}_{c}_W/case')
            if len(d['Q_m3_s'])!=10 or not np.allclose(d['end_s'],w['end_s'][:10],rtol=0,atol=1e-10):
                raise ValueError('short interval mismatch')
            discrepancy=float(max(abs(d['Q_m3_s']/(.5*w['Q_m3_s'][:10])-1)))
            checks[ident]=dict(max_relative_discrepancy=discrepancy,intervals_sha256=sha(case/INTERVAL))
            if discrepancy>1e-6:raise ValueError('constant mobility invariant failed')
        print(ident+' COMPLETE',flush=True)
    if a.short:write(DOC/'SHORT_CHECKS.json',dict(status='PASS',checks=checks,freeze_sha256=sha(DOC/'FREEZE.json')))

if __name__=='__main__':main()
