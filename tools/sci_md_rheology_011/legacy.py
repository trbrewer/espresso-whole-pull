"""Byte-for-byte generated legacy physics parity at identical inputs/locators."""
import argparse
import copy
import importlib.util
import json
import subprocess
from pathlib import Path
from .common import ROOT,DOC,sha,write
from scripts import prepare_case as current
from .observer import native,read
from tools.sci_md_rheology_008.observer import native as old_native
from .prepare import accepted_records
from tools.sci_md_rheology_006.common import TRACE
import numpy as np


def verify(art,accepted):
    # Execute baseline module with its original SCRIPT_DIR semantics; no file writes.
    source=subprocess.check_output(['git','show','origin/main:scripts/prepare_case.py'],cwd=ROOT,text=True)
    namespace={'__file__':str(ROOT/'scripts/prepare_case.py'),'__name__':'baseline_prepare'}
    # Pin baseline aggregate validator as well, rather than importing the candidate.
    oldagg={ '__name__':'baseline_aggregate' }
    exec(compile(subprocess.check_output(['git','show','origin/main:scripts/aggregate_viscosity.py'],cwd=ROOT,text=True),'baseline_aggregate','exec'),oldagg)
    exec(compile(source,'baseline_prepare','exec'),namespace)
    namespace['aggregate_viscosity_contract']=oldagg['contract']
    cases=json.loads((accepted/'SCENARIOS.json').read_text());checks={}
    for name in ('config/reference_R0.json','config/fixture_radial_two_zone.json'):
        p=ROOT/name
        if p.exists():cases[name]=json.loads(p.read_text())
    # Accepted radial constant pressure and pressure history, with viscosity off too.
    seed=copy.deepcopy(next(iter(cases.values())))
    seed['hydraulics'].pop('prescribed_pressure_boundary',None)
    seed['hydraulics'].update(pressure_boundary_model='prescribedPressure',target_inlet_pressure_gauge_Pa=3e5,pressure_ramp_time_s=0)
    cases['legacy_radial_constant']=seed
    for k in list(cases):
        if k.endswith('_base') or k=='legacy_radial_constant':
            off=copy.deepcopy(cases[k]);off['aggregate_viscosity']={'mode':'off'};cases[k+'_off']=off
    for key,s in cases.items():
        hashes={}
        for name in ('render_block_mesh','render_control_dict','render_properties'):
            old=namespace[name](s);new=getattr(current,name)(s)
            if old!=new:raise ValueError('legacy physical rendering changed: '+key+'/'+name)
            hashes[name]=__import__('hashlib').sha256(new.encode()).hexdigest()
        for np_ in (1,2):
            if namespace['render_decompose'](s,np_)!=current.render_decompose(s,np_):raise ValueError('legacy decomposition changed')
        checks[key]=hashes
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only','origin/main','cases/reference_R0_20g_58mm_9bar'],cwd=ROOT,text=True).splitlines()
    templates={}
    for name in paths:
        if '/0.orig/' in name or name.endswith(('fvSchemes','fvSolution')):
            old=subprocess.check_output(['git','show','origin/main:'+name],cwd=ROOT)
            if old!=(ROOT/name).read_bytes():raise ValueError('initial fields/operators changed')
            templates[name]=sha(ROOT/name)
    scenarios=json.loads((accepted/'SCENARIOS.json').read_text());parity={}
    for k,e in accepted_records(accepted).items():
        raw=read(accepted/'full'/e['id']/'case'/TRACE);a=old_native(raw);b=native(raw,scenarios[k])
        for key,value in a.items():
            if isinstance(value,np.ndarray):
                if not np.array_equal(value,b[key]):raise ValueError('A adapter parity '+key)
            elif key=='dose_kg':
                if abs(value-b[key])>1e-15:raise ValueError('dose parity')
            elif value!=b[key]:raise ValueError('A adapter parity '+key)
        parity[k]='IDENTICAL'
    result=dict(status='PASS',legacy_generated_physics=checks,templates=templates,A_observer_parity=parity,
        provenance_metadata='No physical differences normalized. New source/config hashes will change generated provenance metadata only.',native_reruns=0)
    write(DOC/'COMPATIBILITY.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--accepted',type=Path,required=True);a=p.parse_args();verify(a.artifacts,a.accepted)
