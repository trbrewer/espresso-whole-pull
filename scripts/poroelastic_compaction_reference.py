#!/usr/bin/env python3
"""Independent high-precision WP03-001 poroelastic reference."""

from decimal import Decimal, getcontext
import math

getcontext().prec = 60


def _d(value):
    return value if isinstance(value, Decimal) else Decimal(str(value))


def integrate_j(x, phi):
    """High-precision composite Simpson quadrature, independent of C++ algebra."""
    x, phi = _d(x), _d(phi)
    if not Decimal(0) <= x <= Decimal(1) or not Decimal(0) < phi < Decimal(1):
        raise ValueError("integral domain requires 0 <= X <= 1 and 0 < Phi < 1")
    if not x:
        return Decimal(0)

    def fn(s):
        return (Decimal(1)-s)**3/(Decimal(1)-phi*s)

    def composite(n):
        h = x/n
        total = fn(Decimal(0))+fn(x)
        total += sum(
            (Decimal(4) if i % 2 else Decimal(2))*fn(h*i)
            for i in range(1, n)
        )
        return h*total/3

    coarse, fine = composite(256), composite(512)
    return fine+(fine-coarse)/15


def universal_qhat(x):
    x = _d(x)
    return x*(4-6*x+4*x*x-x*x*x)


def strain(sigma_pa, phi, critical_pressure_pa):
    return _d(phi)*_d(sigma_pa)/_d(critical_pressure_pa)


def mechanical_porosity(sigma_pa, phi, critical_pressure_pa):
    e = strain(sigma_pa, phi, critical_pressure_pa)
    return (_d(phi)-e)/(1-e)


def permeability_ratio(sigma_pa, phi, critical_pressure_pa):
    x = _d(sigma_pa)/_d(critical_pressure_pa)
    return (1-x)**3/(1-_d(phi)*x)


def flow(delta_p_pa, area_m2, depth_m, viscosity_pa_s, phi,
         critical_pressure_pa, stress_free_permeability_m2):
    x = _d(delta_p_pa)/_d(critical_pressure_pa)
    return (_d(area_m2)*_d(stress_free_permeability_m2)
            *_d(critical_pressure_pa)*integrate_j(x, phi)
            /(_d(viscosity_pa_s)*_d(depth_m)))


def source_stress_free_permeability(qc_g_s, density_kg_m3, viscosity_pa_s,
                                    depth_m, area_m2, pc_pa, phi):
    qc_m3_s = _d(qc_g_s)*Decimal("1e-3")/_d(density_kg_m3)
    return qc_m3_s*_d(viscosity_pa_s)*_d(depth_m)/(
        _d(area_m2)*_d(pc_pa)*integrate_j(Decimal(1), phi)
    )


def matched_permeability(k_effective, reference_pressure_pa, pc_pa, phi):
    x = _d(reference_pressure_pa)/_d(pc_pa)
    return (_d(k_effective)*_d(reference_pressure_pa)
            /(_d(pc_pa)*integrate_j(x, phi)))


def pressure_at_position(z_over_h, delta_p_pa, phi, pc_pa):
    """Pore pressure above outlet at axial coordinate z/h (inlet=0, outlet=1)."""
    target = integrate_j(_d(delta_p_pa)/_d(pc_pa), phi)*_d(z_over_h)
    lo, hi = Decimal(0), _d(delta_p_pa)/_d(pc_pa)
    for _ in range(100):
        mid = (lo+hi)/2
        if integrate_j(mid, phi) < target:
            lo = mid
        else:
            hi = mid
    sigma = (lo+hi)*_d(pc_pa)/2
    return _d(delta_p_pa)-sigma


def profile(z_over_h, delta_p_pa, phi, pc_pa, k0):
    pressure = pressure_at_position(z_over_h, delta_p_pa, phi, pc_pa)
    sigma = _d(delta_p_pa)-pressure
    return {
        "pressure_pa": pressure, "stress_pa": sigma,
        "strain": strain(sigma, phi, pc_pa),
        "mechanical_porosity": mechanical_porosity(sigma, phi, pc_pa),
        "permeability_m2": _d(k0)*permeability_ratio(sigma, phi, pc_pa),
    }


def bed_height_ratio(delta_p_pa, phi, pc_pa):
    # Change integration variable from fixed axial coordinate to stress.  The
    # Jacobian is proportional to k(sigma), evaluated here by quadrature rather
    # than by the production closed form.
    x, phi = _d(delta_p_pa)/_d(pc_pa), _d(phi)
    n, h = 4096, x/4096
    def weighted(s):
        permeability = (Decimal(1)-s)**3/(Decimal(1)-phi*s)
        return (Decimal(1)-phi*s)*permeability
    numerator = h/3*sum(
        (Decimal(1) if i in (0,n) else Decimal(4) if i%2 else Decimal(2))
        *weighted(h*i) for i in range(n+1))
    return numerator/integrate_j(x, phi)


def basket_root(upstream_pa, outlet_pa, upstream_resistance, puck_flow):
    lo, hi = _d(outlet_pa), _d(upstream_pa)
    for _ in range(120):
        mid = (lo+hi)/2
        residual = mid-(_d(upstream_pa)-_d(upstream_resistance)*puck_flow(mid-_d(outlet_pa)))
        if residual > 0:
            hi = mid
        else:
            lo = mid
    basket = (lo+hi)/2
    return basket, puck_flow(basket-_d(outlet_pa))


def machine_step(time_s, dt_s, previous_upstream_pa, outlet_pa, compliance,
                 upstream_resistance, free_flow_m3_s, shutoff_pa, ramp_s,
                 puck_flow):
    def supply(p):
        ramp = Decimal(1) if not ramp_s else min(Decimal(1), _d(time_s)/_d(ramp_s))
        return _d(free_flow_m3_s)*ramp*max(
            Decimal(0), 1-(p-_d(outlet_pa))/(_d(shutoff_pa)-_d(outlet_pa))
        )
    lo, hi = _d(outlet_pa), _d(shutoff_pa)
    for _ in range(120):
        pu = (lo+hi)/2
        pb, qp = basket_root(pu, outlet_pa, upstream_resistance, puck_flow)
        residual = _d(compliance)*(pu-_d(previous_upstream_pa))/_d(dt_s)-(supply(pu)-qp)
        if residual > 0:
            hi = pu
        else:
            lo = pu
    pu = (lo+hi)/2
    pb, qp = basket_root(pu, outlet_pa, upstream_resistance, puck_flow)
    return {"upstream_pressure_pa": pu, "basket_pressure_pa": pb,
            "supply_flow_m3_s": supply(pu), "puck_flow_m3_s": qp,
            "storage_m3": _d(compliance)*(pu-_d(previous_upstream_pa))}


def finite(values):
    return all(math.isfinite(float(value)) for value in values)
