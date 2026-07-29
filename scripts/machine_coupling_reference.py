#!/usr/bin/env python3
"""Independent linear-load references for WP02-002 (SI units throughout)."""
import math


def continuous(t, p0, outlet, compliance, q0, shutoff, conductance):
    a = q0 / (shutoff - outlet) + conductance
    p_inf = outlet + q0 / a
    tau = compliance / a
    p = p_inf + (p0 - p_inf) * math.exp(-t / tau)
    return {"pressure_Pa": p, "puck_flow_m3_s": conductance * (p - outlet),
            "equilibrium_pressure_Pa": p_inf, "time_constant_s": tau}


def backward_euler(pn, dt, outlet, compliance, q0, shutoff, conductance):
    a = q0 / (shutoff - outlet) + conductance
    forcing = q0 + a * outlet
    p = (compliance * pn / dt + forcing) / (compliance / dt + a)
    qs = q0 * max(0.0, 1.0 - (p - outlet) / (shutoff - outlet))
    qp = conductance * max(p - outlet, 0.0)
    return {"pressure_Pa": p, "supply_flow_m3_s": qs,
            "puck_flow_m3_s": qp,
            "residual_m3_s": compliance * (p - pn) / dt - (qs - qp)}
