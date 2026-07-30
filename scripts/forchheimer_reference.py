#!/usr/bin/env python3
"""Independent WP02-003 Darcy--Forchheimer analytical reference.

This module deliberately does not import or call the production C++ solver.
All permeability inputs use strict SI: k [m2], k_I [m].
"""
from __future__ import annotations

import math

GAMMA2 = -1.71588
TAU = -0.08093


def _positive_finite(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be positive and finite")
    return value


def wadsworth2026_ceramics_fit(k_m2: float) -> float:
    """Return k_I [m] from the numerical value of k expressed in m2."""
    k = _positive_finite("k_m2", k_m2)
    value = math.exp(GAMMA2 * k**TAU)
    return _positive_finite("k_I_m", value)


def velocity_from_gradient(
    gradient_pa_m: float, k_m2: float, k_i_m: float | None,
    mu_pa_s: float, rho_kg_m3: float,
) -> float:
    g = abs(float(gradient_pa_m))
    k = _positive_finite("k_m2", k_m2)
    mu = _positive_finite("mu_pa_s", mu_pa_s)
    if g == 0.0:
        return 0.0
    if k_i_m is None or math.isinf(k_i_m):
        return g * k / mu
    ki = _positive_finite("k_i_m", k_i_m)
    rho = _positive_finite("rho_kg_m3", rho_kg_m3)
    a = mu / k
    b = rho / ki
    return 2.0 * g / (a + math.sqrt(a * a + 4.0 * b * g))


def series_resistance(
    lengths_m: list[float], permeabilities_m2: list[float],
    inertial_permeabilities_m: list[float] | None,
    area_m2: float, mu_pa_s: float, rho_kg_m3: float,
) -> tuple[float, float]:
    if len(lengths_m) != len(permeabilities_m2) or not lengths_m:
        raise ValueError("layer vectors must have equal nonzero length")
    area = _positive_finite("area_m2", area_m2)
    mu = _positive_finite("mu_pa_s", mu_pa_s)
    rho = _positive_finite("rho_kg_m3", rho_kg_m3)
    rd = mu / area * sum(
        _positive_finite("length_m", length) /
        _positive_finite("k_m2", permeability)
        for length, permeability in zip(lengths_m, permeabilities_m2)
    )
    if inertial_permeabilities_m is None:
        return rd, 0.0
    if len(lengths_m) != len(inertial_permeabilities_m):
        raise ValueError("inertial layer vector length mismatch")
    ri = rho / area**2 * sum(
        _positive_finite("length_m", length) /
        _positive_finite("k_i_m", permeability)
        for length, permeability in zip(lengths_m, inertial_permeabilities_m)
    )
    return rd, ri


def flow_from_resistance(delta_p_pa: float, r_d: float, r_i: float) -> float:
    dp = max(float(delta_p_pa), 0.0)
    rd = _positive_finite("r_d", r_d)
    ri = float(r_i)
    if not math.isfinite(ri) or ri < 0.0:
        raise ValueError("r_i must be nonnegative and finite")
    if dp == 0.0:
        return 0.0
    if ri == 0.0:
        return dp / rd
    return 2.0 * dp / (rd + math.sqrt(rd * rd + 4.0 * ri * dp))


def machine_operating_point(
    upstream_pressure_pa: float, outlet_pressure_pa: float,
    upstream_resistance_pa_s_m3: float, r_d: float, r_i: float,
) -> dict[str, float]:
    ru = float(upstream_resistance_pa_s_m3)
    if not math.isfinite(ru) or ru < 0.0:
        raise ValueError("upstream resistance must be nonnegative and finite")
    q = flow_from_resistance(
        max(upstream_pressure_pa - outlet_pressure_pa, 0.0), r_d + ru, r_i
    )
    basket = upstream_pressure_pa - ru * q
    return {"flow_m3_s": q, "basket_pressure_pa": basket}


def forchheimer_number(
    k_m2: float, velocity_m_s: float, k_i_m: float,
    mu_pa_s: float, rho_kg_m3: float,
) -> float:
    return (
        _positive_finite("rho_kg_m3", rho_kg_m3)
        * _positive_finite("k_m2", k_m2)
        * abs(float(velocity_m_s))
        / (_positive_finite("mu_pa_s", mu_pa_s)
           * _positive_finite("k_i_m", k_i_m))
    )


def inertial_pressure_fraction(fo: float) -> float:
    value = float(fo)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("Fo must be nonnegative and finite")
    return value / (1.0 + value)

