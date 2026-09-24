"""Distribution-preserving relocation; task-local geometry and fixed decisions."""
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
from .observer import native, read, metrics
from tools.sci_md_rheology_008.observer import qualify_metric
from tools.sci_md_rheology_009.common import matrix, pressure_audit

DOC = ROOT/'docs/analysis/sci_md_rheology_011'
OLD = ROOT/'docs/analysis/sci_md_rheology_009'
INHERITED = json.loads((OLD/'CONTRACT.json').read_text())
LIMITS = INHERITED['limits']
BUDGETS = INHERITED['budgets']
BASE = '63fd95e'

def interface():
    from decimal import localcontext
    with localcontext() as ctx:
        ctx.prec=80
        exact=Decimal('.029')*(Decimal(3)/4).sqrt()
        return dict(expression='Decimal("0.029") * (Decimal(3)/4).sqrt()',
                    precision=80, decimal=str(exact), binary64_repr=repr(float(exact)),
                    native_serialized=format(float(exact),'.16g'))

def relocate(s):
    result=copy.deepcopy(s)
    result['hydraulics']['permeability_profile'].update(
        interface_radius_m=float(interface()['binary64_repr']),
        inner_permeability_m2=7.5e-16,outer_permeability_m2=3e-15)
    n=result['geometry']['radial_cells']
    ni,no=(1,1) if n==2 else (3*n//4,n//4)
    if n not in (2,64,128):raise ValueError('undeclared radial allocation')
    result['geometry']['radial_mesh']=dict(type='interface_aligned_two_zone',inner_cells=ni,outer_cells=no)
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

def decision(values, arithmetic, law, metric, primary=False):
    if not primary:return qualify_metric(values,arithmetic,law,metric)
    required=('base','temporal','axial','A_radial','B_radial')+(('property',) if law.startswith('SW') else ())
    complete=all(r in values and values[r].get(metric) is not None and r in arithmetic and metric in arithmetic[r] for r in required)
    v=values.get('base',{}).get(metric);terms={}
    if complete:
        complete=all(np.isfinite(values[r][metric]) and np.isfinite(arithmetic[r][metric]) and arithmetic[r][metric]>=0 for r in required)
    if complete:
        terms={r:abs(values[r][metric]-v) for r in required if r!='base'}
        terms.setdefault('property',0.)
        terms['arithmetic']=max(arithmetic[r][metric] for r in required)
    u=sum(terms.values()) if complete else None;b=BUDGETS[metric]
    from tools.sci_md_rheology_007.observer import decide
    flag=decide(v,u,b) if complete else 'UNRESOLVED'
    return dict(value=v,u_total=u,terms=terms,budget=b,evidence_complete=complete,
                decision={'PASS':'BELOW_BUDGET','FAIL':'MATERIAL','UNRESOLVED':'UNRESOLVED'}[flag])

def branch(flags):
    if len(flags)!=8 or any(x not in ('MATERIAL','BELOW_BUDGET','UNRESOLVED') for x in flags):raise ValueError('eight primary decisions required')
    if 'MATERIAL' in flags:return 'MATERIAL_ARRANGEMENT_CONTRAST_CONDITIONAL_E2_REQUIRED'
    if all(x=='BELOW_BUDGET' for x in flags):return 'NO_MATERIAL_ARRANGEMENT_CONTRAST_FOR_TESTED_DELIVERY'
    return 'ARRANGEMENT_CONTRAST_UNRESOLVED'

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
