#!/usr/bin/env python3
"""Run only the frozen six cases and at most six declared refinements."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.sci_md_rheology_001.analysis import ROOT,DOC,check_freeze,sha,write


def budget_available(inv, kind):
    return sum(x['kind']=='primary' if kind=='primary' else x['kind']!='primary' for x in inv)<6

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',required=True,type=Path); p.add_argument('--audit',required=True,type=Path)
    p.add_argument('--executable',required=True,type=Path)
    p.add_argument('--refine',choices=['temporal','spatial'])
    p.add_argument('--case',choices=['uniform_3bar','uniform_9bar','layered_3bar','layered_9bar','reversed_3bar','reversed_9bar'])
    a=p.parse_args(); check_freeze(a.audit)
    authority=json.loads((DOC/'AUTHORITY.json').read_text())
    if sha(a.executable)!=authority['executable_sha256']: raise SystemExit('executable identity mismatch')
    if os.environ.get('WM_PROJECT_VERSION')!='12': raise SystemExit('Foundation OpenFOAM 12 required')
    if a.runs.resolve().is_relative_to(ROOT): raise SystemExit('raw artifacts must remain outside Git')
    if bool(a.case)!=bool(a.refine): p.error('--case and --refine must be paired')
    a.runs.mkdir(parents=True,exist_ok=True)
    ledger=a.runs/'INVOCATIONS.json'; inv=json.loads(ledger.read_text()) if ledger.exists() else []
    scenarios=json.loads((DOC/'SCENARIOS.json').read_text())
    for name,s in scenarios.items():
        if a.case and name!=a.case: continue
        kind=a.refine or 'primary'; runname=name if not a.refine else name+'_'+a.refine
        if any(x['run']==runname for x in inv):
            if a.refine: raise SystemExit('refinement already attempted')
            continue
        if not budget_available(inv,kind):
            raise SystemExit('solver invocation budget exhausted')
        case=a.runs/runname
        if case.exists(): raise SystemExit('refusing to overwrite run directory')
        if a.refine=='temporal': s['time'].update(delta_t_s=.01,field_write_interval_s=.05)
        if a.refine=='spatial': s['geometry'].update(axial_cells=1024)
        config=a.runs/(runname+'.json'); write(config,s)
        def command(cmd,log):
            with (a.runs/(runname+'-'+log+'.log')).open('w') as f:
                subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,check=True,cwd=ROOT)
        command([sys.executable,ROOT/'scripts/prepare_case.py','--root',ROOT,'--config',config,'--case-dir',case,'--nprocs','1'],'prepare')
        command(['blockMesh','-case',case],'mesh')
        for func in ('writeCellCentres','writeCellVolumes'):
            command(['postProcess','-case',case,'-func',func,'-time','0'],func)
        receipt=dict(run=runname,kind=kind,config_sha256=sha(config),executable_sha256=sha(a.executable),
                     freeze_sha256=sha(DOC/'FREEZE.json'),status='STARTED')
        inv.append(receipt); write(ledger,inv) # count failures as invocations
        try: command([a.executable.resolve(),'-case',case],'solver')
        except subprocess.CalledProcessError:
            receipt['status']='FAILED'; write(ledger,inv); raise
        receipt['status']='COMPLETE';write(ledger,inv)
        print(runname+' COMPLETE',flush=True)

if __name__=='__main__': main()
