"""Task-local authority; accepted histories are never synthesized or replayed."""
import json
from pathlib import Path
from tools.sci_md_rheology_001.analysis import ROOT,sha,write
from tools.sci_md_rheology_003.evidence import reuse,INTERVAL
from tools.sci_md_rheology_003.analyze import validate_campaign
from tools.sci_md_rheology_002.run import CASES

DOC=ROOT/'docs/analysis/sci_md_rheology_004'
LAWS=('TR_LINEAR','SW_WATER_ANCHORED_90C')
SETS=('base','temporal','spatial','property')


def matrix():return [f'{r}_{c}_N' for r in SETS for c in CASES]


def accepted():
    return json.loads((ROOT/'docs/analysis/sci_md_rheology_003/FREEZE.json').read_text())


def alphas():
    m=json.loads((ROOT/'docs/analysis/sci_md_rheology_003/METRICS.json').read_text())
    return {l:{r:v['alpha'] for r,v in m['laws'][l]['sets'].items()} for l in LAWS}


def qualify_reuse(baseline,coupled):
    old=reuse(baseline)
    starts,ends=validate_campaign(coupled)
    if len(starts)!=24 or len(ends)!=24:raise ValueError('incomplete accepted 003 evidence')
    return dict(predecessor_002=old,predecessor_003_runs=24,
                predecessor_003_manifest_sha256=sha(ROOT/'docs/analysis/sci_md_rheology_003/RUNS.json'))


def check(executable=None,tables=None,audit=None):
    f=json.loads((DOC/'FREEZE.json').read_text())
    for p,h in f['files'].items():
        if sha(ROOT/p)!=h:raise ValueError('frozen source/evidence mismatch: '+p)
    if executable is not None and sha(executable)!=f['executable_sha256']:raise ValueError('executable mismatch')
    if tables is not None:
        for n,h in f['tables'].items():
            if sha(Path(tables)/(n+'.table'))!=h:raise ValueError('table mismatch')
    if audit is not None:
        a=json.loads(Path(audit).read_text())
        if a.get('status')!='PASS' or not a.get('independent') or not a.get('reviewer') or not a.get('reviewed_commit') or a.get('freeze_sha256')!=sha(DOC/'FREEZE.json'):
            raise ValueError('independent pre-scoring audit missing/mismatched')
    return f


def completed(artifacts):
    f=check(); starts={};ends={};terminal=set()
    ledger=Path(artifacts)/'INVOCATIONS.jsonl'
    events=[json.loads(x) for x in ledger.read_text().splitlines()] if ledger.exists() else []
    for e in events:
        ident=e['id']
        if ident not in matrix():raise ValueError('undeclared run identity')
        if e['status']=='STARTED':
            r=ident.split('_')[0];table='SW_WATER_ANCHORED_90C_'+('refined' if r=='property' else 'base')
            if ident in starts or len(starts)>=8:raise ValueError('duplicate/budget violation')
            if (e['freeze_sha256']!=sha(DOC/'FREEZE.json') or e['executable_sha256']!=f['executable_sha256'] or
                e['table_sha256']!=f['tables'][table] or e['alpha']!=f['alpha']['SW_WATER_ANCHORED_90C'][r] or e.get('transport')!='INDEPENDENT_NATIVE'):
                raise ValueError('native execution authority mismatch; chemistry scaling forbidden')
            starts[ident]=e
        else:
            if ident not in starts or ident in terminal or e['status'] not in ('COMPLETE','FAILED'):raise ValueError('invalid ledger sequence')
            terminal.add(ident)
            if e['status']=='COMPLETE':
                directory=Path(artifacts)/ident
                paths={directory/'scenario.json':e['configuration_sha256'],directory/'case'/INTERVAL:e['intervals_sha256']}
                paths.update({directory/p:h for p,h in e['logs_sha256'].items()})
                paths.update({directory/'case'/p:h for p,h in e['input_hashes'].items()})
                if any(sha(p)!=h for p,h in paths.items()):raise ValueError('native run artifact mismatch')
                ends[ident]=e
    return starts,ends
