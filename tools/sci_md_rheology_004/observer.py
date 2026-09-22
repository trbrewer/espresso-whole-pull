"""Conservative observer of native discrete outlet accounting (kg, seconds)."""
import numpy as np
from tools.sci_md_rheology_003.analyze import validate

# Absolute arithmetic tolerances: mass 1e-14 kg, time inherited 1e-10 s.
# Negative increments are rejected, never clipped. Float audit uses long double.
MASS_ATOL = 1e-14


def history(d):
    validate(d)
    if any(k not in d for k in ('water_kg', 'solute_kg')):
        raise ValueError('missing cumulative masses')
    w = np.r_[0., d['water_kg']]
    s = np.r_[0., d['solute_kg']]
    if np.any(np.diff(w) <= 0) or np.any(np.diff(s) < 0):
        raise ValueError('invalid cumulative masses')
    error = float(max(abs(np.diff(w) - 965*d['Q_m3_s']*d['dt_s'])))
    if error > MASS_ATOL:
        raise ValueError('water increment differs from rho Q dt')
    return dict(W=w, S=s, B=w+s, t=np.r_[0., d['end_s']], water_increment_error_kg=error)


def at(h, coordinate, points, dtype=np.float64):
    if coordinate not in ('B', 'W'):
        raise ValueError('invalid coordinate')
    x=np.asarray(h[coordinate], dtype=dtype); p=np.atleast_1d(np.asarray(points,dtype=dtype))
    if not np.all(np.isfinite(p)) or np.any(p<0) or np.any(p>x[-1]):
        raise ValueError('unsupported endpoint')
    i=np.searchsorted(x,p,side='right')-1
    i=np.minimum(i,len(x)-2)  # Last endpoint belongs to last physical interval.
    f=(p-x[i])/(x[i+1]-x[i])
    return {k:np.asarray(h[k],dtype=dtype)[i]+f*np.diff(np.asarray(h[k],dtype=dtype))[i]
            for k in ('W','S','B','t')}


def common_support(histories):
    if not histories:raise ValueError('missing required support')
    return {k:float(min(h[k][-1] for h in histories)) for k in ('B','W')}


def compare(c,n,coordinate,endpoint,dtype=np.float64):
    if not np.isfinite(endpoint) or endpoint<=0:raise ValueError('zero/invalid support')
    points=np.unique(np.r_[0., c[coordinate][c[coordinate]<endpoint],
                          n[coordinate][n[coordinate]<endpoint], endpoint])
    a,b=at(c,coordinate,points,dtype),at(n,coordinate,points,dtype)
    denominator=b['S'][-1]
    if denominator<=0:raise ValueError('zero solute denominator')
    signed=a['S']-b['S']
    boundaries=np.linspace(0,endpoint,6)
    fa,fb=at(c,coordinate,boundaries,dtype),at(n,coordinate,boundaries,dtype)
    def fractions(v):
        return dict(TDS_percent=[float(x) for x in 100*np.diff(v['S'])/np.diff(v['B'])],
                    cumulative_TDS_percent=[None]+[float(x) for x in 100*v['S'][1:]/v['B'][1:]],
                    time_s=[float(x) for x in v['t']],
                    solute_g=[float(x) for x in 1000*v['S']],
                    water_g=[float(x) for x in 1000*v['W']],
                    beverage_g=[float(x) for x in 1000*v['B']])
    fca,fnb=fractions(fa),fractions(fb)
    return dict(E_end=float(abs(signed[-1])/denominator),E_path=float(max(abs(signed))/denominator),
                signed_endpoint_solute_g=float(1000*signed[-1]),
                max_fraction_TDS_pp=float(max(abs(np.asarray(fca['TDS_percent'])-fnb['TDS_percent']))),
                t_C_s=float(a['t'][-1]),t_R_s=float(b['t'][-1]),
                time_difference_s=float(a['t'][-1]-b['t'][-1]),time_ratio=float(a['t'][-1]/b['t'][-1]),
                C=fca,R=fnb,breakpoint_count=len(points),support_kg=float(endpoint))


THRESHOLDS={'E_path':.05,'max_fraction_TDS_pp':.5}
TARGETS={'E_path':.005,'max_fraction_TDS_pp':.05}


def decide(value,u,metric):
    if not np.isfinite(value+u) or value<0 or u<0 or u>TARGETS[metric]:return 'UNRESOLVED'
    if value-u>=THRESHOLDS[metric]:return 'MATERIAL'
    if value+u<THRESHOLDS[metric]:return 'BELOW THRESHOLDS'
    return 'UNRESOLVED'


def classification(flags):
    return 'MATERIAL' if 'MATERIAL' in flags else 'BELOW THRESHOLDS' if all(x=='BELOW THRESHOLDS' for x in flags) else 'UNRESOLVED'


def disposition(decisions,complete=True):
    if not complete or 'UNRESOLVED' in decisions:return 'PARTIALLY_QUALIFIED_OR_UNRESOLVED'
    if all(x=='BELOW THRESHOLDS' for x in decisions):return 'MASS_MATCHED_AGGREGATE_DELIVERY_BELOW_THRESHOLDS'
    if all(x=='MATERIAL' for x in decisions):return 'MASS_MATCHED_AGGREGATE_DELIVERY_MATERIAL'
    return 'LAW_OR_SCENARIO_DEPENDENT'
