"""Declared constitutive stresses; no fitted EWP parameters or source ranking."""
import numpy as np
from tools.sci_md_rheology_001.analysis import viscosity

LAWS = ('TR_LINEAR', 'TR_DELAYED', 'TR_EARLY', 'SW_WATER_ANCHORED_90C')
NEW = LAWS[1:]
RHO = 965.
TK = 363.15


def fraction(c):
    c = np.asarray(c, float)
    if np.any(~np.isfinite(c)) or np.any(c < 0):
        raise ValueError('invalid pore-water concentration')
    return c/(RHO+c)


def eq5(w, temperature_c, *, extrapolate_90=False):
    w = np.asarray(w, float)
    if np.any(~np.isfinite(w)) or np.any((w < 0) | (w > .5)):
        raise ValueError('Eq5 requires solids fraction in [0,0.5], not percent/water')
    if not (0 <= temperature_c <= 80 or (extrapolate_90 and temperature_c == 90)):
        raise ValueError('Eq5 temperature must be Celsius in recorded domain or explicit 90 C stress')
    return np.exp(-12.96-9.43*w+8.12*w*w+(1789+4382*w)/(temperature_c+273.15))


def evaluate(law, w, mu_water, measured, temperature_k=TK):
    w = np.asarray(w, float)
    if law not in LAWS or temperature_k != TK or not np.isfinite(mu_water) or mu_water <= 0:
        raise ValueError('invalid fixed law/temperature/water endpoint')
    if np.any(~np.isfinite(w)) or np.any((w < 0) | (w > .24)):
        raise ValueError('source domain [0,0.24] exceeded; no clipping')
    if law == LAWS[3]:
        return mu_water*eq5(w,90,extrapolate_90=True)/eq5(0,90,extrapolate_90=True)
    mu, _ = viscosity(w,90,mu_water,measured)
    x = w/.1
    shape = x*x if law == 'TR_DELAYED' else 2*x-x*x if law == 'TR_EARLY' else x
    return np.where(w < .1, mu_water+(measured(TK,90.)-mu_water)*shape, mu)


def knots(breakpoints, refined=False):
    count = 480 if refined else 240
    return np.array(sorted({i/(2000 if refined else 1000) for i in range(count+1)} |
                           {0.,.1,.24} | {round(float(w),14) for w in breakpoints}))
