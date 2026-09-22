"""Hash-bind accepted sources, properties, fixtures and the prospective matrix."""
import argparse,json,shutil,subprocess
from pathlib import Path
import numpy as np
from .common import ROOT,DOC,LAWS,matrix,radial,scenario,table_name,sha,write
from tools.sci_md_rheology_001.analysis import source
from tools.sci_md_rheology_003.laws import evaluate

def main():
    p=argparse.ArgumentParser()
    for k in ('artifacts','accepted','puckworks'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    if (DOC/'FREEZE.json').exists():raise ValueError('freeze exists')
    short=json.loads((a.artifacts/'short/SHORT_CHECKS.json').read_text())
    exe=a.artifacts/'bin/espressoWholePullFoam'
    if short['status']!='PASS' or short['executable_sha256']!=sha(exe):raise ValueError('short qualification missing')
    rej=json.loads((a.artifacts/'rejections/REJECTIONS.json').read_text())
    if len(rej)!=16 or any(v['status']!='REJECTED' for v in rej.values()):raise ValueError('rejections missing')
    pw_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.puckworks,text=True).strip()
    pw_tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=a.puckworks,text=True).strip()
    source_record=json.loads((ROOT/'docs/analysis/sci_md_rheology_003/SOURCE_USE.json').read_text())
    if pw_commit!=source_record['source_commit'] or pw_tree!=source_record['source_tree']:raise ValueError('analysis authority mismatch')
    accepted=json.loads((ROOT/'docs/analysis/sci_md_rheology_005/FREEZE.json').read_text())
    export=json.loads((ROOT/'docs/analysis/sci_md_rheology_003/EXPORT.json').read_text())
    for name,h in export['source_hashes'].items():
        if sha(a.puckworks/name)!=h:raise ValueError('source mismatch '+name)
    tables=a.artifacts/'tables';tables.mkdir(exist_ok=True)
    for name,h in accepted['tables'].items():
        if sha(a.accepted/'tables'/name)!=h:raise ValueError('accepted table mismatch '+name)
        shutil.copyfile(a.accepted/'tables'/name,tables/name)
    evaluator=a.artifacts/'bin/evaluator'
    subprocess.run(['c++','-std=c++11','-O2',str(ROOT/'tools/sci_md_rheology_002/evaluator.cpp'),'-o',str(evaluator)],check=True)
    data,water=source(a.puckworks);muw=float(water.water_viscosity(363.15));checks={}
    for name in accepted['tables']:
        table=tables/name;arr=np.loadtxt(table,skiprows=1);ws,mus=arr[:,0],arr[:,1]
        points=np.unique(np.r_[np.linspace(0,.24,240001),ws,[v+d for v in ws for d in (-1e-12,1e-12) if 0<=v+d<=.24]])
        cs=965*points/(1-points);native_w=cs/(965+cs)
        law=LAWS[0] if name.startswith(LAWS[0]) else LAWS[1]
        continuous=evaluate(law,native_w,muw,data.telisromero_eta_measured);interpolated=np.interp(native_w,ws,mus)
        proc=subprocess.run([str(evaluator),str(table)],input='\n'.join(format(c,'.17g') for c in cs),capture_output=True,text=True,check=True)
        native=np.array(list(map(float,proc.stdout.split())))
        ne=float(max(abs(native/interpolated-1)));pe=float(max(abs(interpolated/continuous-1)))
        if ne>1e-12 or pe>1e-4:raise ValueError('property qualification')
        checks[name]=dict(points=len(points),native_python_relative=ne,table_law_relative=pe,sha256=sha(table))
    for c in ('-1','400','nan','inf'):
        proc=subprocess.run([str(evaluator),str(tables/'TR_LINEAR.table')],input=c,text=True,capture_output=True)
        if proc.returncode==0:raise ValueError('domain/nonfinite rejection '+c)
    controls={}
    for ident,(law,res,case) in matrix().items():
        if res!='control':continue
        oldid=f'{law}_base_{case}_C'
        # Accepted 005 identities are read from its own declared matrix.
        oldid=next(k for k,v in accepted['full_matrix'].items() if v==[law,'base',case,'C'])
        path=a.accepted/'science'/oldid/'case/postProcessing/wholePull/0/aggregate_intervals.csv'
        events=[json.loads(line) for line in (a.accepted/'science/INVOCATIONS.jsonl').read_text().splitlines()]
        event=next(v for v in events if v['id']==oldid and v['status']=='COMPLETE')
        if sha(path)!=event['intervals_sha256']:raise ValueError('accepted control hash')
        controls[ident]=dict(accepted_id=oldid,intervals_sha256=sha(path),configuration_sha256=event['configuration_sha256'])
    write(DOC/'SHORT_CHECKS.json',dict(short, native_rejections=rej))
    write(DOC/'REUSE.json',dict(status='PASS',analysis_commit=pw_commit,analysis_tree=pw_tree,source_hashes=export['source_hashes'],properties=checks,controls=controls,evaluator_sha256=sha(evaluator),domain_rejections=['negative','above_domain','nan','inf'],availability='Accepted external 005 tables, executable and four control traces present and hash verified; existing source/register authority reused. No corpus search or source acquisition.',register_sha256=sha(a.puckworks/'puckworks/data/AVAILABLE_DATA_REGISTER.json'),manifest_sha256=sha(a.puckworks/'puckworks/data/MANIFEST.csv')))
    specs={}
    for ident,(law,res,case) in matrix().items():
        s=scenario(case) if res=='control' else radial(case,res)
        s['aggregate_viscosity']=dict(mode='coupled',purpose='scientific',table=str((tables/table_name(law,res)).resolve()))
        specs[ident]=s
    write(a.artifacts/'SCENARIOS.json',specs)
    files=[]
    for pattern in ('solver/espressoWholePullFoam/*.C','solver/espressoWholePullFoam/*.H','solver/espressoWholePullFoam/Make/*','scripts/aggregate_viscosity.py','scripts/prepare_case.py','tools/sci_md_rheology_006/*.py','tests/test_sci_md_rheology_006.py','tools/sci_md_rheology_00[1-5]/*.py','docs/analysis/sci_md_rheology_00[1-5]/*.json','docs/analysis/sci_md_rheology_006/*.md','docs/analysis/sci_md_rheology_006/SHORT_CHECKS.json','docs/analysis/sci_md_rheology_006/REUSE.json','dependencies/puckworks.lock.json'):
        files.extend(p for p in ROOT.glob(pattern) if p.is_file())
    freeze=dict(task='SCI-MD-RHEOLOGY-006',governance='G2',change_declaration='GOVERNING_PHYSICS_CHANGE',starting_commit='db705b644bbc2c3f719690448657e845f2a8f65b',starting_tree=subprocess.check_output(['git','rev-parse','db705b6^{tree}'],cwd=ROOT,text=True).strip(),files={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(files))},executable_sha256=sha(exe),build_log_sha256=sha(a.artifacts/'build.log'),tables=accepted['tables'],scenarios_sha256=sha(a.artifacts/'SCENARIOS.json'),scenario_identities={k:__import__('hashlib').sha256(json.dumps(v,sort_keys=True).encode()).hexdigest() for k,v in specs.items()},full_matrix=matrix(),planned_full_runs=22,maximum_full_attempts=26,short_ceiling=20,native_rejection_ceiling=20,budgets_pp=dict(D_mean_pp=1.,D_peak_pp=2.),allowance_fraction=.2,scalar_fixture_allowance_pp=short['scalar_fixture_allowance_pp'],artifact_root_sha256=__import__('hashlib').sha256(str(a.artifacts.resolve()).encode()).hexdigest())
    write(DOC/'FREEZE.json',freeze);print('FROZEN '+sha(DOC/'FREEZE.json'))
if __name__=='__main__':main()
