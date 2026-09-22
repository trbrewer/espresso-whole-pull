"""Bounded pressure-history compatibility and transfer contract."""
import copy
import json
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path
import numpy as np
from tools.sci_md_rheology_006.common import ROOT, LAWS, TRACE, radial, table_name, execute, sha, write
from tools.sci_md_rheology_007.common import BUDGETS, digest, sets
from tools.sci_md_rheology_008.observer import native, read, metrics, qualify_metric

DOC = ROOT/'docs/analysis/sci_md_rheology_009'
BASE = '3960b4a9c4b05aa3f3cdec1dade33eb16c485d24'
HISTORIES = {'UP': [3e5,3e5,9e5,9e5], 'DOWN': [9e5,9e5,3e5,3e5]}
TIMES = [0.,14.5,15.5,30.]

def history(s, name, short=False):
    s=copy.deepcopy(s);h=s['hydraulics']
    h.pop('target_inlet_pressure_gauge_Pa',None);h.pop('pressure_ramp_time_s',None)
    h['pressure_boundary_model']='prescribedPressureHistory'
    h['prescribed_pressure_boundary']=dict(schedule_type='piecewiseLinear',times_s=[0.,.065,.135,.2] if short else TIMES,pressures_gauge_Pa=HISTORIES[name] if isinstance(name,str) else [name*1e5]*4)
    return s

def matrix():
    return {f'{model}_{law}_{h}_{r}':dict(model=model,law=law,history=h,resolution=r)
            for model in ('C','E2') for law in LAWS for h in HISTORIES
            for r in sets(law)+(('radial',) if model=='C' else ())}

def pressure_audit(raw, trace, s):
    # CSV endpoint is the exact join key; no rounding or nearest-row matching.
    ends=raw['end_s'];times=trace['time_s']
    # General trace serializes at precision(15); exact equality in that
    # existing key representation, never nearest-time/tolerance matching.
    keys=[format(float(t), '.15g') for t in ends]
    trace_keys=[format(float(t), '.15g') for t in times]
    if len(set(keys))!=len(keys) or len(set(trace_keys))!=len(trace_keys) or keys!=trace_keys:
        raise ValueError('missing/duplicate/misaligned native pressure intervals')
    if not np.array_equal(raw['state_s'],raw['start_s']):raise ValueError('wrong viscosity clock')
    h=s['hydraulics'];schedule=h.get('prescribed_pressure_boundary')
    expected=np.interp(ends,schedule['times_s'],schedule['pressures_gauge_Pa']) if schedule else np.full(len(ends),h['target_inlet_pressure_gauge_Pa'])
    if schedule and (raw['start_s'][0]<schedule['times_s'][0] or ends[-1]>schedule['times_s'][-1]+1e-9):raise ValueError('pressure support')
    error=float(max(abs(trace['inlet_pressure_Pa']-expected)))
    if error>1e-6:raise ValueError('wrong endpoint pressure')
    return dict(max_pressure_error_Pa=error,intervals=len(ends),clock='P(t_end), mu(c_start)',pressure_trace_sha256=None)

def support(terminals):
    required={k for k,v in matrix().items() if v['model']=='C'}
    if set(terminals)!=required:raise ValueError('exact 18 qualified C variants required')
    result={}
    for h in HISTORIES:
        values={k:Decimal(str(v)) for k,v in terminals.items() if matrix()[k]['history']==h}
        if len(values)!=9 or any(not v.is_finite() or v<=0 for v in values.values()):raise ValueError('invalid C terminal support')
        result[h]=str((Decimal('.95')*min(values.values())).quantize(Decimal('.000000001'),rounding=ROUND_FLOOR))
    return result

def verify(art, filename='PREPARATION.json', audit=False):
    f=json.loads((DOC/filename if filename=='FREEZE.json' else art/filename).read_text())
    for root,key in ((ROOT,'files'),(art,'external')):
        for name,h in f[key].items():
            if sha(root/name)!=h:raise ValueError('frozen identity changed: '+name)
    if audit:
        a=json.loads((DOC/'AUDIT.json').read_text())
        if a['status']!='PASS' or a['freeze_sha256']!=sha(DOC/'FREEZE.json'):raise ValueError('independent audit missing/stale')
    return f
