"""Deterministic 1-D finite-volume adapter for the production species law."""
from __future__ import annotations

import math
import numpy as np
from scipy.linalg import solve_banded


def simulate(*, flow_m3_s: float, end_s: float, dose_kg: float, inventory_fraction: float,
             k_1_s: float, csat_kg_m3: float, diffusivity_m2_s: float,
             length_m: float = .015, diameter_m: float = .058, phi: float = .17,
             cells: int = 96, dt_s: float = .025) -> dict:
    """Solve production semantics after wetting at constant measured flow.

    Upwind outlet advection and the inlet zero-concentration diffusive convention
    are implicit; source and its exact beginning-step inventory cap are explicit.
    """
    if min(flow_m3_s, dose_kg, csat_kg_m3, length_m, diameter_m, phi, cells, dt_s) <= 0:
        raise ValueError("positive physical and numerical inputs required")
    area = math.pi*(diameter_m/2)**2
    dz = length_m/cells
    volume = area*length_m
    velocity = flow_m3_s/area
    concentration = np.zeros(cells)
    remaining = np.full(cells, dose_kg*inventory_fraction/volume)
    cup, back = 0.0, 0.0
    history = [{"time_s": 0.0, "beverage_mass_kg": 0.0, "cup_solute_mass_kg": 0.0}]
    maximum = 0.0
    steps = int(math.ceil(end_s/dt_s))
    for step in range(steps):
        dt = min(dt_s, end_s-step*dt_s)
        if dt <= 0: break
        source = k_1_s*remaining*np.maximum(1-concentration/csat_kg_m3, 0)
        source = np.minimum(source, remaining/dt)
        remaining -= dt*source
        adv = velocity*dt/(phi*dz)
        diff = diffusivity_m2_s*dt/dz**2
        # banded implicit matrix, C_inlet=0 (half-cell diffusion), outlet zero gradient
        ab = np.zeros((3, cells)); rhs = concentration + dt*source/phi
        ab[1, :] = 1 + adv + 2*diff
        ab[2, :-1] = -(adv+diff)
        ab[0, 1:] = -diff
        ab[1, 0] += diff  # inlet half-cell Dirichlet represented by two-sided distance
        ab[1, -1] -= diff # outlet zero-gradient
        concentration = solve_banded((1, 1), ab, rhs, check_finite=False)
        outlet_mass = flow_m3_s*concentration[-1]*dt
        inlet_loss = phi*diffusivity_m2_s*area*(2*concentration[0]/dz)*dt
        cup += outlet_mass; back += inlet_loss
        maximum = max(maximum, float(concentration.max()))
        history.append({"time_s": min((step+1)*dt_s, end_s),
                        "beverage_mass_kg": flow_m3_s*1000*min((step+1)*dt_s, end_s),
                        "cup_solute_mass_kg": cup})
    dissolved = float(phi*area*dz*concentration.sum())
    initial = dose_kg*inventory_fraction
    remaining_mass = float(area*dz*remaining.sum())
    retained = initial-cup-back-remaining_mass
    return {"history": history, "initial_inventory_kg": initial, "cup_mass_kg": cup,
            "dissolved_mass_kg": dissolved, "retained_mass_kg": retained,
            "back_diffused_mass_kg": back, "remaining_inventory_kg": remaining_mass,
            "maximum_concentration_kg_m3": maximum,
            "conservation_residual_kg": initial-(cup+back+remaining_mass+dissolved)}


def interpolate_cup(history: list[dict], beverage_mass_kg: float) -> float:
    masses = np.asarray([r["beverage_mass_kg"] for r in history])
    cups = np.asarray([r["cup_solute_mass_kg"] for r in history])
    return float(np.interp(beverage_mass_kg, masses, cups))
