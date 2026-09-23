"""One matched-conductance reversal; inherited native observers and limits."""
import copy
import json
import os
import re
import subprocess
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path
import numpy as np
from tools.sci_md_rheology_006.common import ROOT, LAWS, TRACE, table_name, sha, write
from tools.sci_md_rheology_007.common import digest, sets
from tools.sci_md_rheology_008.observer import native, read, metrics, qualify_metric
from tools.sci_md_rheology_009.common import matrix, pressure_audit

DOC = ROOT/'docs/analysis/sci_md_rheology_010'
OLD = ROOT/'docs/analysis/sci_md_rheology_009'
INHERITED = json.loads((OLD/'CONTRACT.json').read_text())
LIMITS = INHERITED['limits']
BUDGETS = INHERITED['budgets']
BASE = 'cba79537e177938b2607c2979344b13acb56a9f2'

def permeability():
    f, ratio = Decimal(1)/4, Decimal(1)/4
    mean = f*Decimal('3e-15')+(1-f)*Decimal('7.5e-16')
    outer = mean/(f*ratio+1-f)
    return dict(inner_permeability_m2=float(ratio*outer), outer_permeability_m2=float(outer))

def reverse(s):
    result = copy.deepcopy(s)
    result['hydraulics']['permeability_profile'].update(permeability())
    return result

def references():
    return {k:v for k,v in matrix().items() if v['model']=='C'}

def support(terminals):
    required = {config+'_'+k for config in ('old','new') for k in references()}
    if set(terminals)!=required:
        raise ValueError('all 36 C variants required (18 per history)')
    result={}
    for h in ('UP','DOWN'):
        values=[Decimal(str(terminals[config+'_'+k])) for config in ('old','new')
                for k,v in references().items() if v['history']==h]
        if len(values)!=18 or any(not x.is_finite() or x<=0 for x in values):
            raise ValueError('invalid reference terminal')
        result[h]=str((Decimal('.95')*min(values)).quantize(Decimal('1e-9'),rounding=ROUND_FLOOR))
    return result

def pair_keys(law,h,resolution,secondary=False):
    if secondary:
        return 'new_C_'+law+'_'+h+'_'+resolution, 'old_C_'+law+'_'+h+'_'+resolution
    return ('new_E2_'+law+'_'+h+'_'+('base' if resolution=='radial' else resolution),
            'new_C_'+law+'_'+h+'_'+resolution)

def decision(values, arithmetic, law, metric, secondary=False):
    result=qualify_metric(values, arithmetic, law, metric)
    if secondary:
        if 'Cradial' in result['terms']:
            result['terms']['both_C_radial']=result['terms'].pop('Cradial')
        result['decision']={'PASS':'BELOW_DECLARED_MATERIALITY_BUDGET',
                            'FAIL':'MATERIAL_MODELED_DELIVERY_CONTRAST',
                            'UNRESOLVED':'UNRESOLVED'}[result['decision']]
    return result

def overall(flags):
    suffix=('INSUFFICIENT' if 'FAIL' in flags else
            'SUFFICIENT_FOR_TESTED_OUTPUTS' if len(flags)==24 and all(x=='PASS' for x in flags)
            else 'UNRESOLVED')
    return 'E2_CONDUCTANCE_MATCHED_REVERSAL_'+suffix

def verify_files(root, files):
    for name,h in files.items():
        if sha(root/name)!=h:
            raise ValueError('identity changed: '+name)

def verify(art, frozen=False, audited=False):
    f=json.loads(((DOC/'FREEZE.json') if frozen else art/'PREPARATION.json').read_text())
    verify_files(ROOT,f['files']);verify_files(art,f['external'])
    runtime=json.loads((art/'RUNTIME.json').read_text())
    verify_files(Path('/'),{**runtime['libraries'],**runtime['execution_tools']})
    locations=json.loads((art/'LOCATIONS.json').read_text())
    if sha(Path(locations['executable']))!=f['executable_sha256']:
        raise ValueError('accepted executable changed')
    verify_loaded(Path(locations['executable']),runtime)
    if audited:
        a=json.loads((DOC/'AUDIT.json').read_text())
        if a['status']!='PASS' or a['freeze_sha256']!=sha(DOC/'FREEZE.json') or not a.get('independent_reviewer'):
            raise ValueError('missing independent audit')
    return f


def runtime_environment(runtime):
    # Resolve the retained runtime, including its local zlib, without rebuilding.
    directories=list(dict.fromkeys(str(Path(p).parent) for p in runtime['libraries']))
    directories.sort(key=lambda p: p!='/usr/local/lib')
    directories.extend(p for p in os.environ.get('LD_LIBRARY_PATH','').split(':') if p and p not in directories)
    bins=list(dict.fromkeys(str(Path(p).parent) for p in runtime['execution_tools']))
    return dict(os.environ, LD_LIBRARY_PATH=':'.join(directories),
                PATH=':'.join(bins+[os.environ['PATH']]))


def verify_loaded(exe,runtime):
    ldd=subprocess.check_output(['ldd',str(exe)],text=True,env=runtime_environment(runtime))
    actual={str(Path(p).resolve()):sha(Path(p)) for p in re.findall(r'(?:=>\s+)?(/\S+)\s+\(',ldd)}
    expected={str(Path(p).resolve()):h for p,h in runtime['libraries'].items()}
    if actual!=expected:raise ValueError('accepted loaded library identities unavailable')
    return ldd
