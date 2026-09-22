"""Native-schema adapters and explicit SI extensive-increment composition."""
import csv
import numpy as np
from tools.sci_md_rheology_003.analyze import validate as uniform_validate
from tools.sci_md_rheology_005.analyze import qualify
from tools.sci_md_rheology_006.observer import validate as radial_validate
from tools.sci_md_rheology_004.observer import compare
from .common import BUDGETS,WEIGHTS

EXT=('volume_m3','water_kg','solute_kg','stored_solute_kg','remaining_kg','inlet_loss_kg','correction_kg')
CUM=('water_kg','solute_kg','inlet_loss_kg')

def read(path):
    with path.open() as f:
        r=csv.DictReader(f)
        if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):raise ValueError('missing/duplicate columns')
        rows=list(r)
        if not rows:raise ValueError('empty intervals')
        return {k:np.array([float(v[k]) for v in rows]) for k in r.fieldnames}

def clocks(a,b):
    for k in ('start_s','end_s','state_s','dt_s'):
        if not np.array_equal(a[k],b[k]):raise ValueError('mismatched native clocks')

def accounting(d,initial=.0056):
    for k in ('water_kg','solute_kg'):
        if np.any(np.diff(np.r_[0.,d[k]])<0):raise ValueError('negative increments')
    if np.any(np.diff(np.r_[0.,d['water_kg']])<=0):raise ValueError('nonpositive water')
    water=np.cumsum(965*d['volume_m3'])-d['water_kg']
    solute=initial-d['remaining_kg']-d['stored_solute_kg']-d['solute_kg']-d['inlet_loss_kg']
    if max(abs(water))>1e-8 or max(abs(solute))>1e-8:raise ValueError('independent balance failure')
    if max(abs(np.diff(np.r_[0.,d['water_kg']])-965*d['Q']*d['dt_s']))>1e-14:raise ValueError('water increment')
    if sum(abs(d['correction_kg']))>1e-10:raise ValueError('correction mass')
    if np.any(d['remaining_kg'] < -1e-12) or np.any(d['remaining_kg']>initial+1e-10) or np.any(d['stored_solute_kg'] < -1e-12):raise ValueError('inventory bounds')
    return dict(water_max_kg=float(max(abs(water))),solute_max_kg=float(max(abs(solute))))

def adapt(d,kind,end=30.,initial=.0056):
    if kind=='C':radial_validate(d,end)
    elif kind=='uniform':
        uniform_validate(d,end)
        if end==30.:qualify(d)
        for k in ('c_n_min','c_n_max','c_next_min','c_next_max'):
            if np.any(d[k]<-1e-10) or np.any(d[k]>180+1e-8):raise ValueError('concentration bounds')
        for k in ('mu_min','mu_max','mu_next_min','mu_next_max'):
            if np.any(d[k]<=0):raise ValueError('nonpositive viscosity')
        for k in ('water_balance_kg','solute_balance_kg'):
            if max(abs(d[k]))>1e-8:raise ValueError('native balance')
    else:raise ValueError('unknown native schema')
    if max(abs(d['end_s']-d['start_s']-d['dt_s']))>1e-12:raise ValueError('duration mismatch')
    out={k:d[k].copy() for k in EXT+('start_s','end_s','state_s','dt_s')}
    out['Q']=d['Q_total_m3_s' if kind=='C' else 'Q_m3_s'].copy()
    out['kind']=kind;out['initial_inventory_kg']=initial;out['dose_kg']=initial/.28
    if kind=='C':out['share']=d['Q_inner_m3_s']/out['Q']
    out['balance']=accounting(out,initial)
    return out

def compose(inner,outer,weights=WEIGHTS,dtype=np.float64):
    if len(weights)!=2 or any(w<=0 for w in weights) or sum(weights)!=1:raise ValueError('invalid area weights')
    paths=(inner,outer);clocks(*paths)
    if any(d['kind']!='uniform' or abs(d['dose_kg']-.020)>1e-14 or abs(d['initial_inventory_kg']-.0056)>1e-14 for d in paths):raise ValueError('full-basket normalization/double scaling')
    out={k:np.asarray(inner[k],dtype=dtype) for k in ('start_s','end_s','dt_s','state_s')}
    for k in EXT+('Q',):
        v=[np.asarray(d[k],dtype=dtype) for d in paths]
        if k in CUM:v=[np.diff(np.r_[dtype(0),x]) for x in v]
        out[k]=sum(dtype(w)*x for w,x in zip(weights,v))
        if k in CUM:out[k]=np.cumsum(out[k],dtype=dtype)
    out['share']=dtype(weights[0])*np.asarray(inner['Q'],dtype=dtype)/out['Q']
    if np.any(out['Q']<=0) or np.any(out['share']<0) or np.any(out['share']>1):raise ValueError('invalid flow/share')
    out.update(kind='P_derived',dose_kg=.020,initial_inventory_kg=.0056)
    out['regions']=[{k:np.asarray(d[k],dtype=dtype)*dtype(w) for k in EXT+('Q',)} for d,w in zip(paths,weights)]
    out['balance']=accounting(out)
    return out

def history(d,dtype=np.float64):
    w=np.r_[dtype(0),np.cumsum(np.diff(np.r_[dtype(0),np.asarray(d['water_kg'],dtype=dtype)]),dtype=dtype)]
    s=np.r_[dtype(0),np.cumsum(np.diff(np.r_[dtype(0),np.asarray(d['solute_kg'],dtype=dtype)]),dtype=dtype)]
    if np.any(np.diff(w)<=0) or np.any(np.diff(s)<0):raise ValueError('invalid delivery')
    return dict(W=w,S=s,B=w+s,t=np.r_[dtype(0),np.asarray(d['end_s'],dtype=dtype)])

def metrics(p,c,endpoint,dtype=np.float64):
    clocks(p,c)
    qp,qc,dt,sp,sc=[np.asarray(x,dtype=dtype) for x in (p['Q'],c['Q'],c['dt_s'],p['share'],c['share'])]
    if np.any(qp<=0) or np.any(qc<=0):raise ValueError('nonpositive denominator')
    obs=compare(history(p,dtype),history(c,dtype),'B',endpoint,dtype)
    return dict(E_Qint=float(np.sum(abs(qp-qc)*dt)/np.sum(qc*dt)),E_Qpeak=float(max(abs(qp-qc)/qc)),
        D_share_mean_pp=float(100*np.sum(qc*abs(sp-sc)*dt)/np.sum(qc*dt)),D_share_peak_pp=float(100*max(abs(sp-sc))),
        E_Spath=obs['E_path'],D_TDS_pp=obs['max_fraction_TDS_pp'],delivery=dict(P=obs['C'],C=obs['R']))

def decide(v,u,b,valid=True):
    if not valid or not np.isfinite(v+u) or min(v,u)<0 or u>.2*b:return 'UNRESOLVED'
    if v+u<b:return 'PASS'
    if v-u>b:return 'FAIL'
    return 'UNRESOLVED'

def verdict(flags,complete=True):
    if 'FAIL' in flags:return 'INSUFFICIENT'
    if complete and flags and all(x=='PASS' for x in flags):return 'SUFFICIENT_FOR_TESTED_OUTPUTS'
    return 'UNRESOLVED'
