"""Verify accepted receipts and generate only the authorized constituent cases."""
import argparse,copy,json,platform,shutil,subprocess
import numpy as np
from .common import *
from .observer import read,adapt
from tools.sci_md_rheology_006.common import TRACE as RTRACE

def prepare(art,accepted,pw):
    art.mkdir(parents=True,exist_ok=True)
    f=json.loads((ROOT/'docs/analysis/sci_md_rheology_006/FREEZE.json').read_text())
    r=json.loads((ROOT/'docs/analysis/sci_md_rheology_006/RUNS.json').read_text())
    if hashlib.sha256(str(accepted.resolve()).encode()).hexdigest()!=f['artifact_root_sha256']:raise ValueError('accepted location not receipt-bound')
    for path,h in f['files'].items():
        if path.startswith(('solver/','scripts/','dependencies/')) and sha(ROOT/path)!=h:raise ValueError('material source drift '+path)
    if sha(accepted/'SCENARIOS.json')!=f['scenarios_sha256']:raise ValueError('accepted configurations changed')
    if sha(accepted/'CASE_FILE_MANIFESTS.json')!=r['external_case_manifests_sha256']:raise ValueError('case manifests changed')
    manifests=json.loads((accepted/'CASE_FILE_MANIFESTS.json').read_text())
    reused={}
    for ident,v in r['runs'].items():
        if ident.startswith('control_'):continue
        case=accepted/'science'/ident/'case'
        for path,h in manifests[ident]['files'].items():
            if sha(case/path)!=h:raise ValueError('accepted file changed '+ident+'/'+path)
        if sha(case/RTRACE)!=v['trace_sha256']:raise ValueError('trace changed')
        adapt(read(case/RTRACE),'C')
        reused[ident]={k:v[k] for k in ('trace_sha256','scenario_sha256','case_tree_sha256','executable_sha256','intervals')}
    if len(reused)!=18:raise ValueError('missing radial reference')
    source=json.loads((ROOT/'docs/analysis/sci_md_rheology_003/EXPORT.json').read_text())
    for path,h in source['source_hashes'].items():
        if sha(pw/path)!=h:raise ValueError('Puckworks source changed '+path)
    for obj,key in [('HEAD','source_commit'),('HEAD^{tree}','source_tree')]:
        if subprocess.check_output(['git','rev-parse',obj],cwd=pw,text=True).strip()!=source[key]:raise ValueError('analysis authority changed')
    exe=accepted/'bin/espressoWholePullFoam'
    if sha(exe)!=f['executable_sha256']:raise ValueError('accepted executable unavailable: freeze bridge before any run')
    for directory in ('tables','bin'): (art/directory).mkdir(exist_ok=True)
    shutil.copyfile(exe,art/'bin/espressoWholePullFoam');(art/'bin/espressoWholePullFoam').chmod(0o755)
    for name,h in f['tables'].items():
        if sha(accepted/'tables'/name)!=h:raise ValueError('table changed')
        shutil.copyfile(accepted/'tables'/name,art/'tables'/name)
    specs=json.loads((accepted/'SCENARIOS.json').read_text());new={}
    for ident,(law,p,res,z) in matrix().items():
        old=specs[f'{law}_{p}bar_{res}'];generated=radial(p,res)
        generated['aggregate_viscosity']=old['aggregate_viscosity']
        if generated!=old:raise ValueError('complete generated reference dictionary drift')
        new[ident]=constituent(old,z)
        new[ident]['aggregate_viscosity']['table']=str((art/'tables'/table_name(law,res)).resolve())
    short={}
    for z in ('inner','outer'):
        for label,area,nr in [('full',1.,2),('area',WEIGHTS[('inner','outer').index(z)],2),('radial',1.,8)]:
            s=constituent(specs['TR_LINEAR_9bar_base'],z,area,True,nr)
            s['aggregate_viscosity']['table']=str((art/'tables/TR_LINEAR.table').resolve());short[z+'_'+label]=s
    write(art/'SCENARIOS.json',new);write(art/'SHORT_SCENARIOS.json',short)
    write(DOC/'REUSE.json',dict(status='PASS',runs=reused,accepted_merge='e5b3ef819f9692973f674d5da52511d3b3dad07c',accepted_tree='c930fab51b530e20d48efdde9e2bfda4e0cba118',tables=f['tables'],source_commit=source['source_commit'],source_tree=source['source_tree'],source_hashes=source['source_hashes'],streamtube_context_sha256=sha(pw/'puckworks/models/brewer2026/streamtube.py'),runtime_lock_sha256=sha(ROOT/'dependencies/puckworks.lock.json'),accepted_root_sha256=f['artifact_root_sha256']))
    write(DOC/'COMPATIBILITY.json',dict(status='EXACT_ACCEPTED_EXECUTABLE_REUSED',bridge_runs=0,executable_sha256=sha(exe),build_log_sha256=sha(accepted/'build.log'),environment=json.loads((accepted/'ENVIRONMENT.json').read_text()),solver_source={p:h for p,h in f['files'].items() if p.startswith('solver/')},bridge_if_unavailable=dict(flow_relative=1e-8,mass_absolute_kg=1e-12,share_absolute=1e-8,allowed_runs=4)))
    write(art/'LOCATIONS.json',dict(accepted=str(accepted.resolve()),puckworks=str(pw.resolve()),openfoam_bashrc=str(Path.home()/'OpenFOAM/OpenFOAM-12/etc/bashrc')))
    print('18 accepted radial runs and all case files verified; 28 full + 6 short configurations generated')

def freeze(art):
    if (DOC/'FREEZE.json').exists():raise ValueError('immutable freeze exists')
    short=json.loads((DOC/'SHORT_CHECKS.json').read_text())
    if short['status']!='PASS':raise ValueError('short qualification failed')
    patterns=('tools/sci_md_rheology_007/*.py','tests/test_sci_md_rheology_007.py','docs/analysis/sci_md_rheology_007/PROTOCOL.md','docs/analysis/sci_md_rheology_007/REUSE.json','docs/analysis/sci_md_rheology_007/COMPATIBILITY.json','docs/analysis/sci_md_rheology_007/SHORT_CHECKS.json','tools/sci_md_rheology_00[1-6]/*.py','scripts/prepare_case.py','scripts/aggregate_viscosity.py','solver/espressoWholePullFoam/*.C','solver/espressoWholePullFoam/*.H','solver/espressoWholePullFoam/Make/*','dependencies/puckworks.lock.json')
    files=sorted(set(p for pat in patterns for p in ROOT.glob(pat) if p.is_file()))
    external=['SCENARIOS.json','SHORT_SCENARIOS.json','bin/espressoWholePullFoam']+['tables/'+p.name for p in (art/'tables').iterdir()]
    write(DOC/'FREEZE.json',dict(task='SCI-MD-RHEOLOGY-007',governance='G1',change_declaration='SOURCE_SCENARIO_CHANGE_ONLY',files={str(p.relative_to(ROOT)):sha(p) for p in files},external={p:sha(art/p) for p in external},artifact_root_sha256=digest(str(art.resolve())),matrix=matrix(),planned_full=28,bridge_full=0,max_full_attempts=36,max_recoveries=4,short_slots=6,max_short_correction_repeats=2,budgets=BUDGETS,allowance_fraction=.2,scenario_identities={k:digest(v) for k,v in json.loads((art/'SCENARIOS.json').read_text()).items()},higher_precision_bits=np.finfo(np.longdouble).nmant+1))
    print('FROZEN '+sha(DOC/'FREEZE.json'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--accepted',type=Path);p.add_argument('--puckworks',type=Path);p.add_argument('--freeze',action='store_true');a=p.parse_args()
    if a.freeze:freeze(a.artifacts)
    else:prepare(a.artifacts,a.accepted,a.puckworks)
if __name__=='__main__':main()
