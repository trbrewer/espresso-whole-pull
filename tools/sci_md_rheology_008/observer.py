"""Native radial data stays native: no constituent composition or area weights."""
import numpy as np
from tools.sci_md_rheology_007.observer import read, adapt, clocks, history, decide, verdict
from tools.sci_md_rheology_004.observer import compare
from .common import BUDGETS

def native(raw, end=30.):
    d = adapt(raw, 'C', end)
    d['kind'] = 'native_radial'
    d['Q_inner_native'] = raw['Q_inner_m3_s'].copy()
    if np.any(d['share'] < 0) or np.any(d['share'] > 1):
        raise ValueError('invalid native core share')
    for k in ('c_n_max_kg_m3', 'c_next_max_kg_m3'):
        if np.any(raw[k]/(965+raw[k]) > .24):
            raise ValueError('mass fraction domain')
    for zone, fraction in (('inner', .25), ('outer', .75)):
        if np.any(raw[zone+'_remaining_kg'] > .0056*fraction+1e-10):
            raise ValueError('regional inventory bounds')
    return d

def metrics(e, c, endpoint):
    clocks(e, c)
    q, r, dt, s, t = (e['Q'], c['Q'], c['dt_s'], e['share'], c['share'])
    den = np.sum(r*dt)
    result = dict(E_Qint=float(np.sum(abs(q-r)*dt)/den),
                  E_Qpeak=float(max(abs(q-r)/r)),
                  D_share_mean_pp=float(100*np.sum(r*abs(s-t)*dt)/den),
                  D_share_peak_pp=float(100*max(abs(s-t))))
    eh, ch = history(e), history(c)
    # Fixed support: failure affects only delivery, never shrinks endpoint.
    if endpoint > min(eh['B'][-1], ch['B'][-1]):
        result.update(E_Spath=None, D_TDS_pp=None, delivery_status='INSUFFICIENT_SUPPORT')
    else:
        obs = compare(eh, ch, 'B', endpoint)
        result.update(E_Spath=obs['E_path'], D_TDS_pp=obs['max_fraction_TDS_pp'],
                      delivery=dict(E=obs['C'], C=obs['R']), delivery_status='VALID')
    return result

def qualify_metric(values, arithmetic, law, metric):
    required = ('base', 'temporal', 'axial', 'radial') + (('property',) if law.startswith('SW') else ())
    complete = all(r in values and values[r].get(metric) is not None and
                   r in arithmetic and metric in arithmetic[r] for r in required)
    v = values.get('base', {}).get(metric)
    terms = {}
    if complete:
        terms = {name: abs(values[r][metric]-v) for name, r in
                 (('time','temporal'), ('axial','axial'), ('Cradial','radial'))}
        terms['property'] = abs(values['property'][metric]-v) if 'property' in required else 0.
        terms['arithmetic'] = max(arithmetic[r][metric] for r in required)
    u = sum(terms.values()) if complete else None
    budget = BUDGETS[metric]
    return dict(value=v, u_total=u, terms=terms, budget=budget,
                units='fraction' if metric.startswith('E_') else 'percentage_points',
                evidence_complete=complete,
                decision=decide(v, u, budget) if complete else 'UNRESOLVED')
