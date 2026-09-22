"""Verify accepted evidence and prepare only the owner-authorized matrix."""
import argparse
import shutil
import subprocess
from .common import *
from tools.sci_md_rheology_002.export import HEADER

def prepare(art, accepted, e_art, pw):
    if (art/'PREPARATION.json').exists():raise ValueError('preparation exists')
    f=json.loads((ROOT/'docs/analysis/sci_md_rheology_006/FREEZE.json').read_text())
    src=json.loads((ROOT/'docs/analysis/sci_md_rheology_003/EXPORT.json').read_text())
    for obj,key in [('HEAD','source_commit'),('HEAD^{tree}','source_tree')]:
        if subprocess.check_output(['git','rev-parse',obj],cwd=pw,text=True).strip()!=src[key]:raise ValueError('source identity')
    for p,h in src['source_hashes'].items():
        if sha(pw/p)!=h:raise ValueError('source changed '+p)
    for path,freeze in [(accepted,f),(e_art,json.loads((ROOT/'docs/analysis/sci_md_rheology_008/FREEZE.json').read_text()))]:
        if (__import__('hashlib').sha256(str(path.resolve()).encode()).hexdigest() if path==accepted else digest(str(path.resolve())))!=freeze['artifact_root_sha256']:raise ValueError('accepted root identity')
    (art/'tables').mkdir(exist_ok=True)
    for p,h in f['tables'].items():
        if sha(accepted/'tables'/p)!=h:raise ValueError('table changed')
        shutil.copy2(accepted/'tables'/p,art/'tables'/p)
    oldc=json.loads((accepted/'SCENARIOS.json').read_text());olde=json.loads((e_art/'SCENARIOS.json').read_text())
    controls={};references={}
    c_runs=json.loads((ROOT/'docs/analysis/sci_md_rheology_006/RUNS.json').read_text())['runs']
    e_events=[json.loads(x) for x in (e_art/'science/INVOCATIONS.jsonl').read_text().splitlines()]
    for model in ('C','E2'):
        for law in LAWS:
            for p in (3,9):
                oldid=f'{law}_{p}bar_base';oldroot=accepted
                if model=='E2':oldid='E2_'+oldid;oldroot=e_art
                trace=oldroot/'science'/oldid/'case'/TRACE
                expected=c_runs[oldid]['trace_sha256'] if model=='C' else next(e['files']['case/'+str(TRACE)] for e in e_events if e['status']=='COMPLETE' and e['slot']==oldid)
                if sha(trace)!=expected:raise ValueError('accepted native reference')
                native(read(trace))
                base=copy.deepcopy((oldc if model=='C' else olde)[oldid]);base['aggregate_viscosity']['table']=str((art/'tables'/table_name(law,'base')).resolve())
                key=f'{model}_{law}_{p}bar'
                controls[key+'_legacy']=base;controls[key+'_flat']=history(base,p)
                references[key]=dict(trace=str(trace),sha256=expected)
    science={}
    for key,v in matrix().items():
        s=radial(resolution=v['resolution']);s['geometry']['radial_cells']=2 if v['model']=='E2' else s['geometry']['radial_cells']
        s['time']['field_write_interval_s']=30.
        s['aggregate_viscosity']=dict(mode='coupled',purpose='scientific',table=str((art/'tables'/table_name(v['law'],v['resolution'])).resolve()))
        science[key]=history(s,v['history'])
    mu=radial()['liquid']['dynamic_viscosity_Pa_s']
    for name,m in [('constant',mu),('double',2*mu)]:
        (art/'tables'/f'{name}.table').write_text(HEADER+''.join(f'{w} {m:.17g}\n' for w in (0,.1,.24)))
    short={}
    for model,n in [('C',64),('E2',2)]:
        for variant,h in [('up','UP'),('down','DOWN'),('double','UP'),('uniform','UP'),('dynamic','UP'),('repeat','UP'),('mpi','UP')]:
            s=radial();s['geometry'].update(axial_cells=32,radial_cells=n);s['time'].update(end_s=.2,field_write_interval_s=.2)
            table=table_name(LAWS[1],'base') if variant in ('dynamic','repeat','mpi') else ('double.table' if variant=='double' else 'constant.table')
            s['aggregate_viscosity']=dict(mode='coupled',purpose='scientific' if variant in ('dynamic','repeat','mpi') else 'synthetic',table=str((art/'tables'/table).resolve()))
            if variant=='double':s['liquid']['dynamic_viscosity_Pa_s']*=2
            if variant=='uniform':s['hydraulics']['permeability_profile']['outer_permeability_m2']=3e-15
            short[model+'_'+variant]=history(s,h,True)
    # Affected native viscosity-off regression subset: saturated radial legacy/history
    # and default unsaturated legacy; baseline and new executable, 6 runs total.
    from tools.sci_md_rheology_002.run import scenario
    regression={}
    for name,s in [('radial_constant',radial()),('radial_history',history(radial(),'UP',True)),('default_wetting',json.loads((ROOT/'config/scenario.json').read_text()) if (ROOT/'config/scenario.json').exists() else scenario('uniform_9bar'))]:
        s=copy.deepcopy(s);s.pop('aggregate_viscosity',None);s['geometry'].update(axial_cells=32,radial_cells=2);s['time'].update(end_s=.2,field_write_interval_s=.2)
        if name=='default_wetting':s['wetting'].update(initial_wet_front_m=0.,initial_saturation=0.)
        for build in ('accepted','new'):regression[name+'_'+build]=s
    for name,values in [('SCENARIOS',science),('CONTROLS',controls),('SHORT_SCENARIOS',short),('REGRESSIONS',regression),('REFERENCES',references)]:write(art/(name+'.json'),values)
    shutil.copy2(accepted/'bin/espressoWholePullFoam',art/'bin/accepted')
    write(art/'LOCATIONS.json',dict(accepted=str(accepted),e_art=str(e_art),puckworks=str(pw)))
    write(DOC/'REUSE.json',dict(source_commit=src['source_commit'],source_tree=src['source_tree'],source_hashes=src['source_hashes'],tables=f['tables'],accepted_reference_hashes={k:v['sha256'] for k,v in references.items()},production_lock_sha256=sha(ROOT/'dependencies/puckworks.lock.json'),available_data_register_sha256=sha(pw/'puckworks/data/AVAILABLE_DATA_REGISTER.json'),source_manifest_sha256=sha(pw/'puckworks/data/MANIFEST.csv'),preflight='Accepted source-conditioned 003 source-use and export authority; 006 C and 008 E2 references present and verified. Controlled synthetic histories need no experimental acquisition. No global gap.'))
    bind(art,'PREPARATION.json')

def bind(art,name):
    patterns=['tools/sci_md_rheology_00[1-9]/*.py','scripts/*.py','solver/espressoWholePullFoam/*.C','solver/espressoWholePullFoam/*.H','solver/espressoWholePullFoam/Make/*','tests/test_sci_md_rheology_009.py','dependencies/puckworks.lock.json','docs/analysis/sci_md_rheology_009/PROTOCOL.md','docs/analysis/sci_md_rheology_009/CONTRACT.json']
    files={p for pat in patterns for p in ROOT.glob(pat) if p.is_file()}
    external=[p for p in art.glob('*.json') if p.name not in ('PREPARATION.json',)]+list((art/'tables').glob('*'))+list((art/'bin').glob('*'))+[art/'build.log']
    record=dict(files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)},external={str(p.relative_to(art)):sha(p) for p in sorted(external)},matrix=matrix(),executable_sha256=sha(art/'bin/espressoWholePullFoam'),build_log_sha256=sha(art/'build.log'),governance='G2',change_declaration='NO_GOVERNING_PHYSICS_CHANGE',max_full_attempts=52)
    write(DOC/name if name=='FREEZE.json' else art/name,record)

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--accepted',type=Path);p.add_argument('--accepted-e',type=Path);p.add_argument('--puckworks',type=Path);p.add_argument('--freeze',action='store_true');a=p.parse_args()
    if a.freeze:
        verify(a.artifacts)
        if json.loads((DOC/'SHORT_CHECKS.json').read_text())['status']!='PASS':raise ValueError('short qualification missing')
        if (DOC/'FREEZE.json').exists():raise ValueError('freeze exists')
        bind(a.artifacts,'FREEZE.json')
    else:prepare(a.artifacts,a.accepted,a.accepted_e,a.puckworks)
if __name__=='__main__':main()
