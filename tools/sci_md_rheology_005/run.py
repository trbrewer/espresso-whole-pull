"""18 declared full native runs, with at most four nonsemantic recovery attempts."""
import argparse,json
from pathlib import Path
from tools.sci_md_rheology_001.analysis import sha
from tools.sci_md_rheology_002.run import scenario,execute
from tools.sci_md_rheology_003.run import invoke
from .evidence import DOC,ROOT,BULK,matrix,table_name,check,completed

def main():
    p=argparse.ArgumentParser()
    for k in ('artifacts','executable','tables'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--identity',choices=matrix(),required=True)
    p.add_argument('--recovery-reason')
    a=p.parse_args();check(a.executable,a.tables,True,a.artifacts)
    if a.artifacts.resolve().is_relative_to(ROOT):raise ValueError('external outputs required')
    events,starts,ends=completed(a.artifacts)
    slot=a.identity;previous=[x for x in starts if x.split('__recovery')[0]==slot]
    if slot in ends:raise ValueError('slot already complete')
    ident=slot
    if previous:
        if not a.recovery_reason:raise ValueError('document nonsemantic recovery reason')
        if any(not any(e['id']==i and e['status']=='FAILED' for e in events) for i in previous):raise ValueError('prior attempt not terminal failed')
        count=sum('__recovery' in i for i in starts)
        if count>=4:raise ValueError('recovery reserve exhausted')
        ident=slot+'__recovery'+str(len(previous))
    elif a.recovery_reason:raise ValueError('no failed attempt to recover')
    law,res,case,arm=matrix()[slot];table=a.tables/table_name(law,res)
    s=scenario(case,'base' if res=='property' else res)
    s['aggregate_viscosity']=dict(mode='coupled' if arm=='C' else 'bulkCoupled',purpose='scientific',table=str(table.resolve()))
    # Reuse the append/fsync ledger writer; include the companion in its file hash set
    # via a task-local wrapper, without changing historical runner semantics.
    def callback(directory):
        result=execute(s,directory,a.executable)
        if arm=='G' and not (result/BULK).is_file():raise ValueError('missing bulk diagnostics')
        if arm=='G':
            from tools.sci_md_rheology_001.analysis import write
            write(directory/'BULK_RECEIPT.json',dict(sha256=sha(result/BULK)))
        return result
    invoke(a.artifacts,ident,22,{ident},dict(slot=slot,executable_sha256=sha(a.executable),table_sha256=sha(table),
        freeze_sha256=sha(DOC/'FREEZE.json'),transport='INDEPENDENT_NATIVE',recovery_reason=a.recovery_reason),callback)
    print(ident+' COMPLETE',flush=True)
if __name__=='__main__':main()
