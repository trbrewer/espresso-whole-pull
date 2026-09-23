"""Read-only accepted evidence verification; no export, rebuild or old orchestration."""
import argparse
import platform
import re
import shutil
import subprocess
from .common import *
from tools.sci_md_rheology_002.export import HEADER


def accepted_records(accepted):
    receipt=json.loads((OLD/'ARTIFACT_RECEIPT.json').read_text())
    import hashlib
    if hashlib.sha256(str(accepted.resolve()).encode()).hexdigest()!=receipt['artifact_root_sha256']:
        raise ValueError('accepted root receipt')
    ledger=accepted/'full/INVOCATIONS.jsonl'
    if sha(ledger)!=receipt['ledgers']['full']:
        raise ValueError('accepted ledger receipt')
    events=[json.loads(x) for x in ledger.read_text().splitlines()]
    result={}
    for k in references():
        found=[e for e in events if e['slot']==k and e['status']=='COMPLETE']
        if len(found)!=1:raise ValueError('missing accepted reference '+k)
        e=found[0];verify_files(accepted/'full'/e['id'],e['files'])
        if e['files']['case/'+str(TRACE)]!=receipt['primary_trace_sha256'][k]:
            raise ValueError('reference trace receipt')
        result[k]=e
    return result


def bind(art, frozen=False):
    patterns=['tools/sci_md_rheology_0[01][0-9]/*.py','scripts/*.py',
              'tools/sci_md_004_stage_c/compare.py',
              'cases/reference_R0_20g_58mm_9bar/0.orig/*',
              'cases/reference_R0_20g_58mm_9bar/system/fvSchemes',
              'cases/reference_R0_20g_58mm_9bar/system/fvSolution',
              'solver/espressoWholePullFoam/*.C','solver/espressoWholePullFoam/*.H',
              'solver/espressoWholePullFoam/Make/*','dependencies/puckworks.lock.json',
              'tests/test_sci_md_rheology_010.py']
    files={p for pattern in patterns for p in ROOT.glob(pattern) if p.is_file()}
    files.update(DOC/n for n in ('PROTOCOL.md','CONTRACT.json','SOURCE_USE.md','REUSE.json'))
    files.update(OLD/n for n in ('CONTRACT.json','BUILD.json','REUSE.json','ARTIFACT_RECEIPT.json','FREEZE.json'))
    if frozen:files.add(DOC/'SHORT_CHECKS.json')
    names=['SCENARIOS.json','SHORT_SCENARIOS.json','LOCATIONS.json','RUNTIME.json','REFERENCES.json']
    external=[art/n for n in names]+list((art/'tables').glob('*'))
    locations=json.loads((art/'LOCATIONS.json').read_text())
    f=dict(files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)},
           external={str(p.relative_to(art)):sha(p) for p in sorted(external)},
           executable_sha256=sha(Path(locations['executable'])),matrix=matrix(),
           governance='G1',change_declaration='SOURCE_SCENARIO_CHANGE_ONLY',
           planned_native_integrations=42,max_native_attempts=44)
    write(DOC/'FREEZE.json' if frozen else art/'PREPARATION.json',f)


def prepare(art,accepted,pw):
    if (art/'PREPARATION.json').exists():raise ValueError('preparation exists')
    reuse=json.loads((OLD/'REUSE.json').read_text());build=json.loads((OLD/'BUILD.json').read_text())
    for obj,key in [('HEAD','source_commit'),('HEAD^{tree}','source_tree')]:
        if subprocess.check_output(['git','rev-parse',obj],cwd=pw,text=True).strip()!=reuse[key]:
            raise ValueError('scientific source identity')
    verify_files(pw,reuse['source_hashes']);verify_files(ROOT,build['source'])
    if sha(ROOT/'dependencies/puckworks.lock.json')!=reuse['production_lock_sha256']:
        raise ValueError('production lock changed')
    for name,h in json.loads((OLD/'FREEZE.json').read_text())['external'].items():
        if name in ('SCENARIOS.json','SHORT_SCENARIOS.json','RUNTIME.json','build.log') or name.startswith('tables/'):
            if sha(accepted/name)!=h:raise ValueError('accepted preparation identity '+name)
    exe=accepted/'bin/espressoWholePullFoam'
    if sha(exe)!=build['executable_sha256']:raise ValueError('executable identity')
    runtime=json.loads((accepted/'RUNTIME.json').read_text())
    verify_files(Path('/'),{**runtime['libraries'],**runtime['execution_tools']})
    if platform.python_version()!=runtime['python'] or np.__version__!=runtime['numpy']:
        raise ValueError('accepted Python/NumPy runtime unavailable')
    verify_loaded(exe,runtime)
    records=accepted_records(accepted)
    (art/'tables').mkdir(exist_ok=True)
    for name,h in reuse['tables'].items():
        if sha(accepted/'tables'/name)!=h:raise ValueError('property table')
        shutil.copy2(accepted/'tables'/name,art/'tables'/name)
    oldspec=json.loads((accepted/'SCENARIOS.json').read_text());science={}
    for k,v in matrix().items():
        s=reverse(oldspec[k]);s['aggregate_viscosity']['table']=str((art/'tables'/table_name(v['law'],v['resolution'])).resolve());science[k]=s
    oldshort=json.loads((accepted/'SHORT_SCENARIOS.json').read_text());short={}
    for model in ('C','E2'):
        for variant in ('up','down','dynamic','repeat','mpi'):
            k=model+'_'+variant;s=reverse(oldshort[k]);name=Path(s['aggregate_viscosity']['table']).name
            s['aggregate_viscosity']['table']=str((art/'tables'/name).resolve());short[k]=s
    # Exact constant fixture bytes from 009 (not a scientific law).
    shutil.copy2(accepted/'tables/constant.table',art/'tables/constant.table')
    write(art/'SCENARIOS.json',science);write(art/'SHORT_SCENARIOS.json',short)
    write(art/'REFERENCES.json',records)
    shutil.copy2(accepted/'RUNTIME.json',art/'RUNTIME.json')
    write(art/'LOCATIONS.json',dict(accepted=str(accepted.resolve()),executable=str(exe.resolve()),puckworks=str(pw.resolve())))
    write(DOC/'REUSE.json',dict(source_commit=reuse['source_commit'],source_tree=reuse['source_tree'],
        source_hashes=reuse['source_hashes'],tables=reuse['tables'],production_lock_sha256=reuse['production_lock_sha256'],
        accepted_head='ef2be8a3293bdcdf7771037edb0502ae4ca76c31',accepted_squash='dd05d3dd8dd8f690941f22e1583acf2026a23955',
        executable_sha256=sha(exe),runtime_sha256=sha(art/'RUNTIME.json'),build_log_sha256=sha(accepted/'build.log'),
        source_build=build['source'],new_build=False,reference_count=len(records),
        reference_manifest_sha256=sha(art/'REFERENCES.json'),
        reference_trace_hashes={k:e['files']['case/'+str(TRACE)] for k,e in records.items()}))
    bind(art)


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True)
    p.add_argument('--accepted',type=Path);p.add_argument('--puckworks',type=Path);p.add_argument('--freeze',action='store_true');a=p.parse_args()
    if a.freeze:
        verify(a.artifacts)
        if (DOC/'FREEZE.json').exists():raise ValueError('single freeze already exists')
        q=json.loads((DOC/'SHORT_CHECKS.json').read_text())
        if q['status']!='PASS' or q['completed']!=10:raise ValueError('short qualification')
        bind(a.artifacts,True)
    else:prepare(a.artifacts,a.accepted,a.puckworks)
if __name__=='__main__':main()
