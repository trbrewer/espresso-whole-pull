"""Bounded native execution; all raw artifacts remain outside the repository."""
import argparse
import copy
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
from tools.sci_md_rheology_001.analysis import ROOT, sha, write

DOC=ROOT/'docs/analysis/sci_md_rheology_002'
CASES=('uniform_9bar','reversed_3bar')


def scenario(name, resolution='base'):
    s=copy.deepcopy(json.loads((ROOT/'docs/analysis/sci_md_rheology_001/SCENARIOS.json').read_text())[name])
    if resolution=='temporal': s['time']['delta_t_s']=.01
    if resolution=='spatial': s['geometry']['axial_cells']=1024
    return s


def rows(case):
    with (Path(case)/'postProcessing/wholePull/0/aggregate_intervals.csv').open() as f:
        return {k:np.array(v,float) for k,v in _columns(csv.DictReader(f)).items()}


def _columns(reader):
    out={k:[] for k in reader.fieldnames}
    for r in reader:
        for k in out: out[k].append(r[k])
    return out


def execute(s, directory, executable, nprocs=1):
    directory=Path(directory)
    if directory.exists(): raise ValueError('refusing existing run')
    directory.mkdir(parents=True)
    write(directory/'scenario.json',s)
    case=directory/'case'
    commands=[[sys.executable,str(ROOT/'scripts/prepare_case.py'),'--root',str(ROOT),'--config',str(directory/'scenario.json'),
               '--case-dir',str(case),'--nprocs',str(nprocs)],['blockMesh','-case',str(case)]]
    if nprocs>1: commands.append(['decomposePar','-case',str(case)])
    commands.append(([str(executable),'-case',str(case)] if nprocs==1 else
        ['mpirun','-np',str(nprocs),str(executable),'-case',str(case),'-parallel']))
    env=dict(os.environ,ESPRESSO_CASE_ROOT=str(case))
    for i,cmd in enumerate(commands):
        with (directory/f'command-{i}.log').open('w') as f:
            subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    return case


def check_freeze(executable,table):
    from tools.sci_md_rheology_002.authority import expected
    f,files,executable_hash=expected(DOC)
    for path,digest in files.items():
        if sha(ROOT/path)!=digest: raise ValueError('frozen implementation changed: '+path)
    if sha(executable)!=executable_hash or sha(table)!=f['runtime_table_sha256']:
        raise ValueError('runtime identity differs from freeze')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifacts',type=Path,required=True)
    p.add_argument('--executable',type=Path,required=True)
    p.add_argument('--table',type=Path,required=True)
    a=p.parse_args()
    if a.artifacts.resolve().is_relative_to(ROOT): raise ValueError('raw output must be external')
    check_freeze(a.executable,a.table)
    a.artifacts.mkdir(parents=True,exist_ok=True)
    ledger=a.artifacts/'INVOCATIONS.json'
    inv=json.loads(ledger.read_text()) if ledger.exists() else []
    for resolution in ('base','temporal','spatial'):
        alpha=None
        # Reference W/C precede N; transfer cannot inform calibration.
        for name in CASES:
            for treatment in ('W','C','N'):
                ident=f'{resolution}_{name}_{treatment}'
                directory=a.artifacts/ident
                existing=next((r for r in inv if r['id']==ident),None)
                if existing:
                    if existing['status']!='COMPLETE': raise ValueError('prior failed invocation requires explicit amendment')
                else:
                    if len(inv)>=18: raise ValueError('18 invocation budget exhausted')
                    s=scenario(name,resolution)
                    s['aggregate_viscosity']=dict(mode='coupled' if treatment=='C' else 'observe',purpose='scientific',table=str(a.table.resolve()))
                    if treatment=='N':
                        if alpha is None: raise ValueError('reference calibration unavailable')
                        s['liquid']['dynamic_viscosity_Pa_s']/=alpha
                    record=dict(id=ident,status='STARTED',executable_sha256=sha(a.executable),
                        freeze_sha256=sha(DOC/'FREEZE.json'),alpha=alpha if treatment=='N' else None)
                    inv.append(record);write(ledger,inv)
                    try: case=execute(s,directory,a.executable)
                    except Exception:
                        record['status']='FAILED';write(ledger,inv);raise
                    record.update(status='COMPLETE',configuration_sha256=sha(directory/'scenario.json'),
                        intervals_sha256=sha(case/'postProcessing/wholePull/0/aggregate_intervals.csv'))
                    write(ledger,inv)
                if name==CASES[0] and treatment=='C':
                    w=rows(a.artifacts/f'{resolution}_{name}_W/case');c=rows(directory/'case')
                    if abs(c['end_s'][-1]-30)>1e-9 or abs(w['end_s'][-1]-30)>1e-9: raise ValueError('incomplete calibration')
                    alpha=float(c['volume_m3'].sum()/w['volume_m3'].sum())
                print(ident+' COMPLETE',flush=True)

if __name__=='__main__': main()
