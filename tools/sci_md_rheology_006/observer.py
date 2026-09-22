"""Strict complete-interval radial observer, SI units and flow-share pp."""
import csv
import numpy as np
from .common import TRACE

S0=4/7

def read(case):
    with (case/TRACE).open() as f:
        r=csv.DictReader(f); rows=list(r)
        if not rows or len(r.fieldnames)!=len(set(r.fieldnames)):raise ValueError('empty/duplicate columns')
        return {k:np.array([float(row[k]) for row in rows]) for k in r.fieldnames}

def validate(d,end=30.):
    required=('schema_version start_s end_s dt_s state_s Q_inner_m3_s Q_outer_m3_s Q_total_m3_s reverse_inner_m3_s reverse_outer_m3_s reverse_total_m3_s volume_m3 cup_Q_m3_s c_n_min_kg_m3 c_n_max_kg_m3 mu_n_min_Pa_s mu_n_max_Pa_s c_next_min_kg_m3 c_next_max_kg_m3 mu_next_min_Pa_s mu_next_max_Pa_s correction_kg water_kg solute_kg stored_solute_kg remaining_kg inlet_loss_kg water_balance_kg solute_balance_kg dilute_pore_volume_fraction pore_courant_outgoing_max inner_area_m2 outer_area_m2 inner_volume_m3 outer_volume_m3 inner_remaining_kg outer_remaining_kg').split()
    if any(k not in d for k in required):raise ValueError('missing columns')
    n=len(d['dt_s'])
    if not n or any(len(v)!=n or not np.isfinite(v).all() for v in d.values()):raise ValueError('invalid/missing interval values')
    def gate(ok,name):
        if not np.all(ok):raise ValueError(name)
    gate(d['schema_version']==1,'schema version')
    gate((abs(d['start_s'][0])<=1e-9)&(abs(d['end_s'][-1]-end)<=1e-9),'complete support')
    gate(abs(d['start_s'][1:]-d['end_s'][:-1])<=1e-9,'interval gap/overlap')
    gate(abs(d['state_s']-d['start_s'])<=1e-9,'lagged state')
    dt=d['dt_s'];q=d['Q_total_m3_s'];qi=d['Q_inner_m3_s'];qo=d['Q_outer_m3_s']
    gate((dt>0)&(q>0),'nonpositive flow/duration')
    gate(abs(d['end_s']-d['start_s']-dt)<=1e-12,'interval duration')
    gate(abs(qi+qo-q)/q<=1e-10,'zone flow sum')
    rev=d['reverse_total_m3_s']
    gate((rev>=0)&(d['reverse_inner_m3_s']>=0)&(d['reverse_outer_m3_s']>=0),'negative reverse magnitude')
    gate(abs(rev-d['reverse_inner_m3_s']-d['reverse_outer_m3_s'])/q<=1e-10,'reverse zone sum')
    gate(rev/q<=1e-10,'outlet reverse flow')
    gate(abs(d['cup_Q_m3_s']-q)/q<=1e-10,'cup flux correspondence')
    gate(abs(d['volume_m3']-q*dt)<=1e-15,'native volume increment')
    gate(abs(np.diff(np.r_[0.,d['water_kg']])-965*q*dt)<=1e-14,'water increment')
    for k in ('water_balance_kg','solute_balance_kg'):gate(abs(d[k])<=1e-8,k)
    gate(sum(abs(d['correction_kg']))<=1e-10,'correction mass')
    for k in ('c_n_min_kg_m3','c_n_max_kg_m3','c_next_min_kg_m3','c_next_max_kg_m3'):
        gate((d[k]>=-1e-10)&(d[k]<=180+1e-8),k)
    for k in ('mu_n_min_Pa_s','mu_n_max_Pa_s','mu_next_min_Pa_s','mu_next_max_Pa_s'):gate(d[k]>0,k)
    gate((d['remaining_kg']>=-1e-12)&(d['remaining_kg']<=.0056+1e-10),'inventory')
    gate(d['stored_solute_kg']>=-1e-12,'storage')
    gate((d['dilute_pore_volume_fraction']>=0)&(d['dilute_pore_volume_fraction']<=1+1e-12),'dilute occupancy')
    gate(d['pore_courant_outgoing_max']>=0,'Courant')
    for zone,fraction in (('inner',.25),('outer',.75)):
        area=np.pi*.029**2*fraction
        gate(abs(d[zone+'_area_m2']/area-1)<=1e-8,'zone area')
        gate(abs(d[zone+'_volume_m3']/(area*.009011660896432553)-1)<=1e-8,'zone volume')
        gate(d[zone+'_remaining_kg']>=-1e-12,'zone inventory')
    gate(abs(d['inner_remaining_kg']+d['outer_remaining_kg']-d['remaining_kg'])<=1e-12,'zone inventory sum')
    return True

def scores(d,dtype=np.float64):
    q=np.array(d['Q_total_m3_s'],dtype=dtype);qi=np.array(d['Q_inner_m3_s'],dtype=dtype);dt=np.array(d['dt_s'],dtype=dtype)
    s0=dtype(4)/dtype(7)
    return dict(D_mean_pp=float(100*np.sum(abs(qi-s0*q)*dt,dtype=dtype)/np.sum(q*dt,dtype=dtype)),D_peak_pp=float(100*np.max(abs(qi/q-s0))),signed_shift_pp=float(100*(np.sum(qi*dt,dtype=dtype)/np.sum(q*dt,dtype=dtype)-s0)))

def decision(value,u,budget,valid=True):
    if not valid or u>.2*budget:return 'UNRESOLVED'
    if value-u>budget:return 'MATERIAL'
    if value+u<budget:return 'BELOW_BUDGET'
    return 'UNRESOLVED'
