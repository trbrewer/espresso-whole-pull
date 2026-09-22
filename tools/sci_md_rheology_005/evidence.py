"""Task-local identities, bounded attempts, and read-only accepted evidence."""
import json
from pathlib import Path
from tools.sci_md_rheology_001.analysis import ROOT,sha,write
from tools.sci_md_rheology_002.run import CASES
from tools.sci_md_rheology_004.evidence import verify_accepted

DOC=ROOT/'docs/analysis/sci_md_rheology_005'
LAWS=('TR_LINEAR','SW_WATER_ANCHORED_90C')
BUDGETS={'E_Qint':.01,'E_Qpeak':.02,'E_Spath':.01,'D_TDS':.10}
INTERVAL='postProcessing/wholePull/0/aggregate_intervals.csv'
BULK='postProcessing/wholePull/0/aggregate_bulk_intervals.csv'

def sets(law):return ('base','temporal','spatial') if law=='TR_LINEAR' else ('base','temporal','spatial','property')
def matrix():
    # Controls first; no scientific G scores are calculated by the runner.
    return {f'{law}_{res}_{case}_{arm}':(law,res,case,arm)
            for arm in ('C','G') for law in LAWS for res in (('base',) if arm=='C' else sets(law)) for case in CASES}
def table_name(law,res):return 'TR_LINEAR.table' if law=='TR_LINEAR' else law+('_refined' if res=='property' else '_base')+'.table'
def accepted_path(baseline,coupled,law,res,case,arm='C'):
    if law=='TR_LINEAR' or arm=='W':return Path(baseline)/f'{"base" if res=="property" else res}_{case}_{arm}','002'
    return Path(coupled)/f'{res}_{case}_{law}','003'
def reuse(baseline,coupled,context):
    records={}
    for law in LAWS:
        for res in sets(law):
            for case in CASES:
                for arm in ('C','W','N'):
                    if arm=='N' and law!=LAWS[0]:path,task=Path(context)/f'{res}_{case}_N','004'
                    else:path,task=accepted_path(baseline,coupled,law,res,case,arm)
                    if task!='004':verify_accepted(path,task)
                    else:
                        historical=json.loads((ROOT/'docs/analysis/sci_md_rheology_004/RUNS.json').read_text())['events']
                        start=next(x for x in historical if x['id']==path.name and x['status']=='STARTED')
                        end=next(x for x in historical if x['id']==path.name and x['status']=='COMPLETE')
                        freeze=json.loads((ROOT/'docs/analysis/sci_md_rheology_004/FREEZE.json').read_text())
                        if start['executable_sha256']!=freeze['executable_sha256']:raise ValueError('004 executable mismatch')
                        files={path/'scenario.json':end['configuration_sha256'],path/'case'/INTERVAL:end['intervals_sha256']}
                        files.update({path/p:h for p,h in end['logs_sha256'].items()})
                        files.update({path/'case'/p:h for p,h in end['input_hashes'].items()})
                        if any(sha(p)!=h for p,h in files.items()):raise ValueError('004 artifact mismatch')
                    records[f'{law}/{res}/{case}/{arm}']=dict(task=task,id=path.name,intervals_sha256=sha(path/'case'/INTERVAL),configuration_sha256=sha(path/'scenario.json'))
    return dict(status='PASS',runs=records,source_audit_reused=['docs/analysis/sci_md_rheology_001/AUDIT.json','docs/analysis/sci_md_rheology_003/AUDIT.json'])
def check(executable=None,tables=None,audit=False,artifacts=None):
    f=json.loads((DOC/'FREEZE.json').read_text())
    for p,h in f['files'].items():
        if sha(ROOT/p)!=h:raise ValueError('frozen file changed: '+p)
    if executable and sha(executable)!=f['executable_sha256']:raise ValueError('executable mismatch')
    if tables:
        for p,h in f['tables'].items():
            if sha(Path(tables)/p)!=h:raise ValueError('table mismatch: '+p)
    if artifacts and sha_string(str(Path(artifacts).resolve()))!=f['artifact_root_sha256']:raise ValueError('wrong execution root')
    if audit:
        a=json.loads((DOC/'AUDIT.json').read_text())
        if (a.get('status')!='PASS' or not a.get('independent') or not a.get('reviewer') or not a.get('reviewed_commit') or a.get('freeze_sha256')!=sha(DOC/'FREEZE.json')):raise ValueError('independent audit missing/mismatched')
    return f
def sha_string(s):
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()
def completed(artifacts):
    f=check(artifacts=artifacts);root=Path(artifacts);ledger=root/'INVOCATIONS.jsonl'
    events=[json.loads(x) for x in ledger.read_text().splitlines()] if ledger.exists() else []
    starts={};ends={};terminal=set()
    for e in events:
        ident=e['id'];slot=e.get('slot',ident.split('__recovery')[0])
        if slot not in matrix():raise ValueError('unknown slot')
        if e['status']=='STARTED':
            if ident in starts or len(starts)>=22:raise ValueError('attempt count/identity violation')
            if e['freeze_sha256']!=sha(DOC/'FREEZE.json') or e['executable_sha256']!=f['executable_sha256']:raise ValueError('attempt authority mismatch')
            law,res,_,_=matrix()[slot]
            if e['table_sha256']!=f['tables'][table_name(law,res)]:raise ValueError('attempt table mismatch')
            starts[ident]=e
        else:
            if ident not in starts or ident in terminal or e['status'] not in ('COMPLETE','FAILED'):raise ValueError('invalid ledger')
            terminal.add(ident)
            if e['status']=='COMPLETE':
                directory=root/ident;case=directory/'case'
                paths={directory/'scenario.json':e['configuration_sha256'],case/INTERVAL:e['intervals_sha256']}
                paths.update({directory/p:h for p,h in e['logs_sha256'].items()});paths.update({case/p:h for p,h in e['input_hashes'].items()})
                if matrix()[slot][3]=='G':
                    paths[case/BULK]=json.loads((directory/'BULK_RECEIPT.json').read_text())['sha256']
                if any(not p.is_file() or sha(p)!=h for p,h in paths.items()):raise ValueError('run artifact mismatch: '+ident)
                if slot in ends:raise ValueError('multiple completed runs in slot')
                ends[slot]=dict(e,attempt=ident)
    return events,starts,ends
