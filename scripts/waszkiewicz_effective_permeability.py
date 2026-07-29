#!/usr/bin/env python3
"""Independent WP02-001 closed form; standard library only."""
from __future__ import annotations

import json
import math
from typing import Iterable

SERIES_THRESHOLD = 0.125
SERIES_FIRST_ORDER = 4
SERIES_MAX_ORDER = 24
MINIMUM_MULTIPLIER = 1.0e-6
MAXIMUM_MULTIPLIER = 1.0
UPPER_ROUNDOFF_TOLERANCE = 1.0e-10


def _finite(*values: float) -> None:
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("finite inputs required")


def qhat(x: float) -> float:
    _finite(x)
    return x * (4.0 - 6.0 * x + 4.0 * x * x - x * x * x)

def _phi_factor_series(phi: float) -> float:
    accumulator = 0.0
    for n in range(SERIES_MAX_ORDER, SERIES_FIRST_ORDER - 1, -1):
        coefficient = (
            (n - 3) * (n - 2) * (2 * n + 1)
            / (6.0 * n * (n - 1))
        )
        accumulator = coefficient + phi * accumulator
    phi2 = phi * phi
    return phi2 * phi2 * accumulator


def _phi_factor_direct(phi: float) -> float:
    one_minus_phi = 1.0 - phi
    return (
        phi * (phi * (11.0 * phi - 15.0) + 6.0)
        + 6.0 * one_minus_phi**3 * math.log1p(-phi)
    ) / (6.0 * one_minus_phi**2)


def phi_factor(phi: float) -> float:
    _finite(phi)
    if phi == 0.0:
        return 0.0
    if not 0.0 < phi < 1.0:
        raise ValueError("phi must be in [0, 1)")
    if phi <= SERIES_THRESHOLD:
        result = _phi_factor_series(phi)
    else:
        result = _phi_factor_direct(phi)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError("invalid phi factor")
    return result


def solids_sigmoid(t_s: float, k_g: float, l_s: float, m_s: float) -> float:
    _finite(t_s, k_g, l_s, m_s)
    if k_g <= 0.0 or m_s <= 0.0:
        raise ValueError("positive solids parameters required")
    return 0.5 * k_g * (1.0 + math.tanh((t_s - l_s) / m_s))


def q_static(p_bar: float, pc_bar: float, qc_g_s: float) -> float:
    _finite(p_bar, pc_bar, qc_g_s)
    if p_bar <= 0.0 or pc_bar <= 0.0 or qc_g_s <= 0.0:
        raise ValueError("positive pressure and flow required")
    return qc_g_s * qhat(p_bar / pc_bar)


def dynamic_state(
    t_s: float,
    p_bar: float,
    pc_bar: float,
    qc_g_s: float,
    k_g: float,
    l_s: float,
    m_s: float,
    dose_g: float,
) -> dict:
    _finite(t_s, p_bar, pc_bar, qc_g_s, k_g, l_s, m_s, dose_g)
    if min(p_bar, pc_bar, qc_g_s, k_g, m_s, dose_g) <= 0.0:
        raise ValueError("positive source parameters required")
    phi_m = k_g / dose_g
    dissolved = solids_sigmoid(t_s, k_g, l_s, m_s)
    phi_t = dissolved / dose_g
    if not 0.0 < phi_m < 1.0 or not 0.0 < phi_t < 1.0:
        raise ValueError("source porosity factors must be in (0, 1)")
    q_master = qc_g_s / phi_factor(phi_m)
    p_master = pc_bar / phi_m
    flow = qhat(p_bar / (p_master * phi_t)) * q_master * phi_factor(phi_t)
    return {
        "dissolved_mass_g": dissolved,
        "phi_t": phi_t,
        "flow_g_per_s": max(0.0, flow),
    }


def raw_multiplier(t_s: float, p_bar: float, **source: float) -> float:
    dynamic = dynamic_state(t_s=t_s, p_bar=p_bar, **source)["flow_g_per_s"]
    static = q_static(p_bar, source["pc_bar"], source["qc_g_s"])
    value = dynamic / static
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("invalid raw multiplier")
    if value > MAXIMUM_MULTIPLIER + UPPER_ROUNDOFF_TOLERANCE:
        raise ValueError("raw multiplier exceeds source long-run bound")
    return value


def bounded_multiplier(raw: float, minimum: float = MINIMUM_MULTIPLIER) -> float:
    _finite(raw, minimum)
    if raw < 0.0 or minimum <= 0.0:
        raise ValueError("invalid multiplier")
    if raw > MAXIMUM_MULTIPLIER + UPPER_ROUNDOFF_TOLERANCE:
        raise ValueError("raw multiplier exceeds roundoff allowance")
    return min(MAXIMUM_MULTIPLIER, max(minimum, raw))


def closure_state(
    solver_time_s: float,
    saturated: bool,
    p_bar: float,
    source_to_solver_offset_s: float,
    source_validity_start_s: float,
    minimum: float,
    base_permeability_m2: float,
    **source: float,
) -> dict:
    if not saturated:
        return {
            "active": False,
            "source_time_s": solver_time_s - source_to_solver_offset_s,
            "source_state_time_s": None,
            "source_support_status": "UNSATURATED_BRANCH_INACTIVE",
            "multiplier_raw": 1.0,
            "multiplier": 1.0,
            "effective_permeability_m2": base_permeability_m2,
        }
    source_time = solver_time_s - source_to_solver_offset_s
    state_time = max(source_validity_start_s, source_time)
    state = dynamic_state(t_s=state_time, p_bar=p_bar, **source)
    raw = raw_multiplier(t_s=state_time, p_bar=p_bar, **source)
    multiplier = bounded_multiplier(raw, minimum)
    return {
        "active": True,
        "source_time_s": source_time,
        "source_state_time_s": state_time,
        "source_support_status": (
            "PRE_SOURCE_SUPPORT_SATURATED_HOLD"
            if source_time < source_validity_start_s
            else "SOURCE_SUPPORTED_SATURATED_STAGE"
        ),
        **state,
        "static_flow_g_per_s": q_static(p_bar, source["pc_bar"], source["qc_g_s"]),
        "multiplier_raw": raw,
        "multiplier": multiplier,
        "effective_permeability_m2": base_permeability_m2 * multiplier,
    }


def vector_dynamic(times: Iterable[float], p_bar: float, **source: float) -> list[float]:
    return [
        dynamic_state(t_s=float(t), p_bar=p_bar, **source)["flow_g_per_s"]
        for t in times
    ]


def canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
