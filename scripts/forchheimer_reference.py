#!/usr/bin/env python3
"""Independent WP02-003 Darcy--Forchheimer analytical reference.

This module deliberately does not import or call the production C++ solver.
All permeability inputs use strict SI: k [m2], k_I [m].
"""
from __future__ import annotations

import math

GAMMA2 = -1.71588
TAU = -0.08093
ZHOU_GAMMA1 = 1.0e10
ZHOU_EXPONENT = 1.5
SOURCE_ALPHA_PER_M = 4808.0
SOURCE_PERCOLATION_EXPONENT = 4.4
SOURCE_GRIND_BETA_M_PER_SETTING = 4.3505e-5
SOURCE_GRIND_INTERCEPT_M = 1.0160e-4
SOURCE_GRINDER_SETTINGS = (1.0, 4.0)
SOURCE_CONNECTED_POROSITIES = (0.3, 0.5)
SOURCE_FLOW_RANGE_M_S = (5.36e-4, 5.74e-4)
SOURCE_DENSITY_KG_M3 = 960.0
SOURCE_VISCOSITY_PA_S = 3.0e-4
PUBLISHED_FO_RANGE = (0.0161, 0.0639)


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


def wadsworth2026_zhou_best_fit(k_m2: float) -> float:
    """Return Zhou best-fit k_I [m] with strict-SI k [m2]."""
    k = _positive_finite("k_m2", k_m2)
    return _positive_finite("k_I_m", ZHOU_GAMMA1 * k**ZHOU_EXPONENT)


def wadsworth2026_source_permeability(
    radius_m: float, connected_porosity: float
) -> float:
    radius = _positive_finite("radius_m", radius_m)
    phi = float(connected_porosity)
    if not math.isfinite(phi) or not 0.0 < phi < 1.0:
        raise ValueError("connected_porosity must be finite and in (0,1)")
    value = (
        2.0 * radius**2 * math.exp(-2.0 * SOURCE_ALPHA_PER_M * radius)
        / (9.0 * (1.0 - phi))
        * phi**SOURCE_PERCOLATION_EXPONENT
    )
    return _positive_finite("k_m2", value)


def reconstruct_wadsworth2026_source_fo_range() -> dict:
    """Reconstruct the paper's espresso Fo range under both named closures."""
    radii = [
        SOURCE_GRIND_BETA_M_PER_SETTING * setting
        + SOURCE_GRIND_INTERCEPT_M
        for setting in SOURCE_GRINDER_SETTINGS
    ]
    combinations = []
    for setting, radius in zip(SOURCE_GRINDER_SETTINGS, radii):
        for phi in SOURCE_CONNECTED_POROSITIES:
            permeability = wadsworth2026_source_permeability(radius, phi)
            zhou_ki = wadsworth2026_zhou_best_fit(permeability)
            ceramics_ki = wadsworth2026_ceramics_fit(permeability)
            for velocity in SOURCE_FLOW_RANGE_M_S:
                combinations.append({
                    "grinder_setting": setting,
                    "mean_radius_m": radius,
                    "connected_porosity": phi,
                    "permeability_m2": permeability,
                    "superficial_velocity_m_s": velocity,
                    "zhou_inertial_permeability_m": zhou_ki,
                    "ceramics_inertial_permeability_m": ceramics_ki,
                    "zhou_fo": forchheimer_number(
                        permeability, velocity, zhou_ki,
                        SOURCE_VISCOSITY_PA_S, SOURCE_DENSITY_KG_M3,
                    ),
                    "ceramics_fo": forchheimer_number(
                        permeability, velocity, ceramics_ki,
                        SOURCE_VISCOSITY_PA_S, SOURCE_DENSITY_KG_M3,
                    ),
                })
    return {
        "disposition": "SOURCE_INTERNAL_CLOSURE_INCONSISTENCY_IDENTIFIED",
        "source_constants": {
            "grind_beta_m_per_setting": SOURCE_GRIND_BETA_M_PER_SETTING,
            "grind_intercept_m": SOURCE_GRIND_INTERCEPT_M,
            "grinder_settings": list(SOURCE_GRINDER_SETTINGS),
            "mean_radii_m": radii,
            "permeability_alpha_per_m": SOURCE_ALPHA_PER_M,
            "percolation_exponent": SOURCE_PERCOLATION_EXPONENT,
            "connected_porosity_range": list(SOURCE_CONNECTED_POROSITIES),
            "superficial_velocity_range_m_s": list(SOURCE_FLOW_RANGE_M_S),
            "density_kg_m3": SOURCE_DENSITY_KG_M3,
            "viscosity_pa_s": SOURCE_VISCOSITY_PA_S,
            "zhou_gamma1": ZHOU_GAMMA1,
            "zhou_exponent": ZHOU_EXPONENT,
            "ceramics_gamma2": GAMMA2,
            "ceramics_tau": TAU,
        },
        "combinations": combinations,
        "zhou_fo_range": [
            min(item["zhou_fo"] for item in combinations),
            max(item["zhou_fo"] for item in combinations),
        ],
        "ceramics_fo_range": [
            min(item["ceramics_fo"] for item in combinations),
            max(item["ceramics_fo"] for item in combinations),
        ],
        "published_fo_range": list(PUBLISHED_FO_RANGE),
        "implemented_solver_closure": "wadsworth2026CeramicsFit",
        "source_comparison_status": "CONTEXT_ONLY_NOT_DIRECT_IMPLEMENTED_BRANCH_TARGET",
    }


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
