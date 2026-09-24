"""Strict complete-interval radial observer, SI units and flow-share pp."""
import csv
import numpy as np
from tools.sci_md_rheology_006.common import TRACE
from tools.sci_md_rheology_007.observer import EXT, accounting, history, clocks, read
from tools.sci_md_rheology_008.observer import metrics

def dimensions(s):
    r=s["geometry"]["basket_radius_m"]
    a=s["hydraulics"]["permeability_profile"]["interface_radius_m"]
    return r, s["coffee_bed"]["bed_depth_m"], (a/r)**2


S0=4/7

def read_case(case):
    with (case/TRACE).open() as f:
        r=csv.DictReader(f); rows=list(r)
        if not rows or len(r.fieldnames)!=len(set(r.fieldnames)):raise ValueError('empty/duplicate columns')
        return {k:np.array([float(row[k]) for row in rows]) for k in r.fieldnames}

def validate(d,s,end=30.):
    radius, depth, fraction_inner = dimensions(s)
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
    for zone,fraction in (('inner',fraction_inner),('outer',1-fraction_inner)):
        area=np.pi*radius**2*fraction
        gate(abs(d[zone+'_area_m2']/area-1)<=1e-8,'zone area')
        gate(abs(d[zone+'_volume_m3']/(area*depth)-1)<=1e-8,'zone volume')
        gate((d[zone+'_remaining_kg']>=-1e-12)&(d[zone+'_remaining_kg']<=.0056*fraction+1e-10),'zone inventory')
    gate(abs(d['inner_remaining_kg']+d['outer_remaining_kg']-d['remaining_kg'])<=1e-12,'zone inventory sum')
    return True

def native(raw,s,end=30.):
    validate(raw,s,end)
    out={k:raw[k].copy() for k in EXT+('start_s','end_s','state_s','dt_s')}
    out.update(Q=raw['Q_total_m3_s'].copy(), Q_inner_native=raw['Q_inner_m3_s'].copy(),
               kind='native_radial', initial_inventory_kg=.0056, dose_kg=.020)
    out['share']=out['Q_inner_native']/out['Q']
    if np.any(out['share']<0) or np.any(out['share']>1):raise ValueError('invalid core share')
    for k in ('c_n_max_kg_m3','c_next_max_kg_m3'):
        if np.any(raw[k]/(965+raw[k])>.24):raise ValueError('mass fraction domain')
    out['balance']=accounting(out)
    return out


def high_share(d,s):
    p=s['hydraulics']['permeability_profile']
    if p['inner_permeability_m2']==p['outer_permeability_m2']:
        raise ValueError('equal permeabilities have no distinct high class')
    return d['share'] if p['inner_permeability_m2']>p['outer_permeability_m2'] else 1-d['share']


def independent_paths(high,low):
    """Permutation null for unchanged per-unit-area autonomous path responses."""
    high,low=np.asarray(high),np.asarray(low)
    if high.shape!=low.shape or not np.isfinite(high).all() or not np.isfinite(low).all():
        raise ValueError('invalid path response')
    return .25*high+.75*low
