"""Verify external evidence and the two accepted laws; freeze only after short QA."""
import argparse,json,shutil,subprocess
from pathlib import Path
import numpy as np
from tools.sci_md_rheology_001.analysis import source,sha,write
from tools.sci_md_rheology_002.export import export as export_tr
from tools.sci_md_rheology_003.export import SW_FILES
from tools.sci_md_rheology_003.laws import evaluate
from .evidence import ROOT,DOC,LAWS,BUDGETS,matrix,reuse,sha_string

def main():
    p=argparse.ArgumentParser()
    for k in ('artifacts','baseline','coupled','context','puckworks','accepted_tables'):p.add_argument('--'+k.replace('_','-'),type=Path,required=True)
    a=p.parse_args();exe=a.artifacts/'bin/espressoWholePullFoam';evaluator=a.artifacts/'bin/evaluator'
    if (DOC/'FREEZE.json').exists():raise ValueError('freeze already exists')
    short=json.loads((a.artifacts/'short/SHORT_CHECKS.json').read_text())
    if short['status']!='PASS' or short['executable_sha256']!=sha(exe):raise ValueError('short QA missing')
    write(DOC/'SHORT_CHECKS.json',short)
    reuse_record=reuse(a.baseline,a.coupled,a.context);write(DOC/'REUSE.json',reuse_record)
    subprocess.run(['c++','-std=c++11','-O2',str(ROOT/'tools/sci_md_rheology_002/evaluator.cpp'),'-o',str(evaluator)],check=True)
    tables=a.artifacts/'tables';tables.mkdir(exist_ok=False)
    tr=export_tr(a.puckworks,a.artifacts/'TR-export',evaluator)
    shutil.copyfile(a.artifacts/'TR-export/aggregate.table',tables/'TR_LINEAR.table')
    accepted_tr=json.loads((ROOT/'docs/analysis/sci_md_rheology_002/EXPORT.json').read_text())
    if sha(tables/'TR_LINEAR.table')!=accepted_tr['runtime_table_sha256']:raise ValueError('TR identity changed')
    sw=json.loads((ROOT/'docs/analysis/sci_md_rheology_003/EXPORT.json').read_text())
    for name,h in sw['source_hashes'].items():
        if sha(a.puckworks/name)!=h:raise ValueError('source identity mismatch: '+name)
    data,water=source(a.puckworks);muw=float(water.water_viscosity(363.15));property_checks={}
    for level in ('base','refined'):
        name='SW_WATER_ANCHORED_90C_'+level
        src=a.accepted_tables/(name+'.table')
        if sha(src)!=sw['tables'][name]['sha256']:raise ValueError('SW table identity changed')
        shutil.copyfile(src,tables/src.name)
        tab=np.loadtxt(src,skiprows=1);ws,mus=tab[:,0],tab[:,1]
        points=np.unique(np.r_[np.linspace(0,.24,240001),ws,[v+d for v in ws for d in (-1e-12,1e-12) if 0<=v+d<=.24]])
        cs=965*points/(1-points);native_w=cs/(965+cs)
        continuous=evaluate(LAWS[1],native_w,muw,data.telisromero_eta_measured);interpolated=np.interp(native_w,ws,mus)
        result=subprocess.run([str(evaluator),str(src)],input='\n'.join(format(c,'.17g') for c in cs),text=True,capture_output=True,check=True)
        native=np.array(list(map(float,result.stdout.split())))
        ne=float(max(abs(native/interpolated-1)));pe=float(max(abs(interpolated/continuous-1)))
        if ne>1e-12 or pe>1e-4:raise ValueError('property equivalence failure')
        property_checks[name]=dict(points=len(points),native_python_relative=ne,table_continuous_relative=pe)
    write(DOC/'PROPERTY.json',dict(status='PASS',TR=tr,SW=property_checks,accepted_export_sha256=sha(ROOT/'docs/analysis/sci_md_rheology_003/EXPORT.json')))
    # Freeze relevant implementation and all consumed compact predecessor evidence.
    paths=[]
    for pattern in ('solver/espressoWholePullFoam/*.C','solver/espressoWholePullFoam/*.H','solver/espressoWholePullFoam/Make/*',
                    'tools/sci_md_rheology_005/*','tests/test_sci_md_rheology_005.py','tools/sci_md_rheology_00[1-4]/*.py',
                    'docs/analysis/sci_md_rheology_00[1-4]/*.json'):
        paths.extend(p for p in ROOT.glob(pattern) if p.is_file())
    paths.extend(ROOT/p for p in ('scripts/aggregate_viscosity.py','scripts/prepare_case.py','dependencies/puckworks.lock.json',
                  'docs/analysis/sci_md_rheology_005/PROTOCOL.md','docs/analysis/sci_md_rheology_005/SHORT_CHECKS.json',
                  'docs/analysis/sci_md_rheology_005/REUSE.json','docs/analysis/sci_md_rheology_005/PROPERTY.json'))
    f=dict(task='SCI-MD-RHEOLOGY-005',governance='G2',change_declaration='GOVERNING_PHYSICS_CHANGE',
        starting_commit='ab29a805217010f8c441047aaa04e6b4adaca3fe',starting_tree='3437fa55ea8510cdebfd66c15ec8ac75e3e3fcb6',
        analysis_commit='2058d0e947ee9eb92c52d64f6165b810f1fb4732',analysis_tree='a6ffb312473b15be43c1571a893b19873ea47c5a',
        production_lock='fc61c4670ec7bf801e40bb391aab16048b8da26b',files={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))},
        executable_sha256=sha(exe),build_log_sha256=sha(a.artifacts/'build.log'),tables={p.name:sha(p) for p in sorted(tables.glob('*.table'))},
        artifact_root_sha256=sha_string(str((a.artifacts/'science').resolve())),full_matrix=matrix(),planned_full=18,maximum_full_attempts=22,
        retry_scope='at most four documented nonsemantic recovery attempts only',budgets=BUDGETS,allowance_fraction=.2,
        exposure='EXPOSED_SOURCE_CONDITIONED_MODEL_COMPARISON',audit='INDEPENDENT_PASS_REQUIRED',execution='NOT_STARTED')
    write(DOC/'FREEZE.json',f);print('Frozen '+sha(DOC/'FREEZE.json'))
if __name__=='__main__':main()
