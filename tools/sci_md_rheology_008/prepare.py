"""Recover only receipt-bound evidence; freeze the complete family before scoring."""
import argparse
import copy
import hashlib
import json
import platform
import re
import shutil
import subprocess
import numpy as np
from .common import *
from .observer import read, native
from tools.sci_md_rheology_002.export import HEADER
from tools.sci_md_rheology_007.analyze import load as load_p
from tools.sci_md_rheology_007.observer import compose, metrics as p_metrics
from tools.sci_md_rheology_007.common import check as check_p

def prepare(art, p_art):
    if art.exists():
        raise ValueError('refuse to overwrite preparation')
    check_p(p_art, audit=True)
    locations = json.loads((p_art/'LOCATIONS.json').read_text())
    accepted, pw = Path(locations['accepted']), Path(locations['puckworks'])
    f = json.loads((ROOT/'docs/analysis/sci_md_rheology_006/FREEZE.json').read_text())
    runs = json.loads((ROOT/'docs/analysis/sci_md_rheology_006/RUNS.json').read_text())
    if hashlib.sha256(str(accepted.resolve()).encode()).hexdigest()!=f['artifact_root_sha256']:
        raise ValueError('C location not bound')
    if sha(accepted/'CASE_FILE_MANIFESTS.json')!=runs['external_case_manifests_sha256']:
        raise ValueError('C manifest changed')
    if sha(accepted/'SCENARIOS.json')!=f['scenarios_sha256']:
        raise ValueError('C scenarios changed')
    manifests=json.loads((accepted/'CASE_FILE_MANIFESTS.json').read_text())
    reused={}
    for ident,v in runs['runs'].items():
        if ident.startswith('control_'):continue
        case=accepted/'science'/ident/'case'
        for p,h in manifests[ident]['files'].items():
            if sha(case/p)!=h:raise ValueError('C file changed: '+ident+'/'+p)
        if sha(case/TRACE)!=v['trace_sha256']:raise ValueError('C trace changed')
        native(read(case/TRACE))
        reused[ident]=v
    if len(reused)!=18:raise ValueError('18 C science traces required')
    source=json.loads((ROOT/'docs/analysis/sci_md_rheology_003/EXPORT.json').read_text())
    for p,h in source['source_hashes'].items():
        if sha(pw/p)!=h:raise ValueError('source changed: '+p)
    for obj,key in [('HEAD','source_commit'),('HEAD^{tree}','source_tree')]:
        if subprocess.check_output(['git','rev-parse',obj],cwd=pw,text=True).strip()!=source[key]:
            raise ValueError('analysis Puckworks identity')
    for p,h in f['files'].items():
        if p.startswith(('solver/','scripts/','dependencies/')) and sha(ROOT/p)!=h:
            raise ValueError('production identity changed: '+p)
    exe=accepted/'bin/espressoWholePullFoam'
    if sha(exe)!=EXE_SHA or sha(accepted/'build.log')!=f['build_log_sha256']:
        raise ValueError('accepted executable/build unavailable; no bridge authorized')
    c,p,events,missing,quality=load_p(p_art,accepted)
    if missing or len(p)!=28:raise ValueError('P native evidence incomplete')
    accepted_scores=json.loads((ROOT/'docs/analysis/sci_md_rheology_007/METRICS.json').read_text())
    support=json.loads((ROOT/'docs/analysis/sci_md_rheology_007/SUPPORT.json').read_text())
    regression={}
    for law in LAWS:
        for pressure in (3,9):
            key=f'{law}_{pressure}bar';variants={}
            for r in sets(law)+('radial',):
                pk=key+'_'+('base' if r=='radial' else r)
                m=p_metrics(compose(p[pk+'_inner'],p[pk+'_outer']),c[key+'_'+r],support['support'][str(pressure)]['B_star_kg'])
                old=accepted_scores['cases'][key]['sets'][r]
                errors={k:abs(m[k]-old[k]) for k in BUDGETS}
                if max(errors.values())>1e-12:raise ValueError('P/C regression changed')
                variants[r]=errors
            regression[key]=variants
    art.mkdir(parents=True)
    for directory in ('bin','tables'):(art/directory).mkdir()
    shutil.copy2(exe,art/'bin/espressoWholePullFoam')
    for name,h in f['tables'].items():
        if sha(accepted/'tables'/name)!=h:raise ValueError('table identity')
        shutil.copy2(accepted/'tables'/name,art/'tables'/name)
    specs=json.loads((accepted/'SCENARIOS.json').read_text());new={}
    for ident,(n,law,pressure,res) in matrix().items():
        old=specs[f'{law}_{pressure}bar_{res}'];generated=radial(pressure,res)
        generated['aggregate_viscosity']=old['aggregate_viscosity']
        if generated!=old:raise ValueError('accepted builder dictionary drift')
        s=candidate(old,n);s['aggregate_viscosity']['table']=str((art/'tables'/table_name(law,res)).resolve())
        new[ident]=s
    mu=radial()['liquid']['dynamic_viscosity_Pa_s']
    for name,vals in [('constant',[mu]*3),('double',[2*mu]*3),('evolving',[mu,2*mu,4*mu])]:
        (art/'tables'/f'{name}.table').write_text(HEADER+''.join(f'{w} {v:.17g}\n' for w,v in zip((0,.1,.24),vals)))
    short={}
    for n in (2,4,8):
        for variant in ('water','double','uniform'):
            s=candidate(specs['TR_LINEAR_9bar_base'],n)
            s['geometry']['axial_cells']=32;s['time'].update(end_s=.2,delta_t_s=.02,field_write_interval_s=.2)
            name='double' if variant=='double' else 'constant'
            s['aggregate_viscosity']=dict(mode='coupled',purpose='synthetic',table=str((art/'tables'/f'{name}.table').resolve()))
            if variant=='double':s['liquid']['dynamic_viscosity_Pa_s']*=2
            if variant=='uniform':s['hydraulics']['permeability_profile']['outer_permeability_m2']=3e-15
            short[f'E{n}_{variant}']=s
    for variant in ('dynamic','repeat','mpi'):
        s=copy.deepcopy(short['E2_water']);s['aggregate_viscosity']['table']=str((art/'tables/evolving.table').resolve())
        short['E2_'+variant]=s
    write(art/'SCENARIOS.json',new);write(art/'SHORT_SCENARIOS.json',short)
    write(art/'LOCATIONS.json',dict(locations,accepted_p=str(p_art.resolve())))
    ldd=subprocess.check_output(['ldd',str(exe)],text=True)
    libraries={v:sha(Path(v)) for v in re.findall(r'(?:=>\s+)?(/\S+)\s+\(',ldd)}
    write(art/'RUNTIME.json',dict(ldd=ldd,libraries=libraries,python=platform.python_version(),numpy=np.__version__,environment=json.loads((accepted/'ENVIRONMENT.json').read_text())))
    write(DOC/'COMPATIBILITY.json',dict(status='EXACT_ACCEPTED_EXECUTABLE_REUSED',executable_sha256=EXE_SHA,build_log_sha256=f['build_log_sha256'],runtime_sha256=sha(art/'RUNTIME.json'),library_hashes=sorted(libraries.values()),solver_source={p:h for p,h in f['files'].items() if p.startswith('solver/')},bridge_runs=0))
    write(DOC/'REUSE.json',dict(status='PASS',C=reused,P_traces=28,P_compositions=14,P_ledger_sha256=sha(p_art/'science/INVOCATIONS.jsonl'),C_manifest_sha256=sha(accepted/'CASE_FILE_MANIFESTS.json'),C_root_sha256=f['artifact_root_sha256'],P_root_sha256=digest(str(p_art.resolve())),source_commit=source['source_commit'],source_tree=source['source_tree'],source_hashes=source['source_hashes'],tables=f['tables'],production_lock_sha256=sha(ROOT/'dependencies/puckworks.lock.json'),register_sha256=sha(pw/'puckworks/data/AVAILABLE_DATA_REGISTER.json'),manifest_sha256=sha(pw/'puckworks/data/MANIFEST.csv')))
    write(DOC/'P_REGRESSION.json',dict(status='PASS',all_variants=regression,accepted_disposition=accepted_scores['disposition'],new_P_runs=0))
    write(DOC/'SUPPORT.json',dict(inherited=support,source_sha256=sha(ROOT/'docs/analysis/sci_md_rheology_007/SUPPORT.json'),rule='Exact inherited pressure endpoints; never shrink for E'))
    # Bind the short matrix before any short launch, including execution tooling.
    write(art/'PREPARATION.json',dict(short_sha256=sha(art/'SHORT_SCENARIOS.json'),science_sha256=sha(art/'SCENARIOS.json'),tools={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'tools/sci_md_rheology_008').glob('*.py'))},executable_sha256=EXE_SHA,tables={p.name:sha(p) for p in (art/'tables').iterdir()}))
    print('18 C and 28 P traces verified; P/C regression PASS; 42 full + 12 short slots prepared')

def freeze(art):
    if (DOC/'FREEZE.json').exists():raise ValueError('immutable freeze exists')
    if json.loads((DOC/'SHORT_CHECKS.json').read_text())['status']!='PASS':raise ValueError('short qualification required')
    patterns=['tools/sci_md_rheology_00[1-8]/*.py','tests/test_sci_md_rheology_008.py','scripts/prepare_case.py','scripts/aggregate_viscosity.py','solver/espressoWholePullFoam/*.C','solver/espressoWholePullFoam/*.H','solver/espressoWholePullFoam/Make/*','dependencies/puckworks.lock.json']
    files=set(p for pat in patterns for p in ROOT.glob(pat) if p.is_file())
    files.update(DOC/name for name in ('PROTOCOL.md','SUPPORT.json','REUSE.json','COMPATIBILITY.json','SHORT_CHECKS.json','P_REGRESSION.json'))
    external=['SCENARIOS.json','SHORT_SCENARIOS.json','PREPARATION.json','RUNTIME.json','bin/espressoWholePullFoam']+['tables/'+p.name for p in (art/'tables').iterdir()]
    write(DOC/'FREEZE.json',dict(task='SCI-MD-RHEOLOGY-008',governance='G1',change_declaration='SOURCE_SCENARIO_CHANGE_ONLY',files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)},external={p:sha(art/p) for p in external},artifact_root_sha256=digest(str(art.resolve())),matrix=matrix(),planned_full=42,max_full_attempts=46,max_recoveries=4,short_slots=12,max_short_attempts=14,budgets=BUDGETS,allowance_fraction=.2,scenario_identities={k:digest(v) for k,v in json.loads((art/'SCENARIOS.json').read_text()).items()},short_ledger_sha256=sha(art/'short/INVOCATIONS.jsonl')))
    print('FROZEN '+sha(DOC/'FREEZE.json'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--accepted-p',type=Path);p.add_argument('--freeze',action='store_true');a=p.parse_args()
    if a.freeze:freeze(a.artifacts)
    else:prepare(a.artifacts,a.accepted_p)
if __name__=='__main__':main()
