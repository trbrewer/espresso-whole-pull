"""Independent 1-D saturated prescribed-pressure reduced transport route."""
from __future__ import annotations
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ReducedSpecies:
    species_id: str
    initial_mass_kg: float
    rate_1_s: float
    capacity_kg_m3: float
    diffusivity_m2_s: float


def tridiagonal(lower, diagonal, upper, rhs):
    """Solve a tridiagonal system without third-party dependencies."""
    n = len(diagonal)
    if not n or len(rhs) != n or len(lower) != n-1 or len(upper) != n-1:
        raise ValueError("invalid tridiagonal dimensions")
    c = list(upper); d = list(rhs); b = list(diagonal)
    for i in range(1, n):
        if b[i-1] == 0: raise ArithmeticError("singular tridiagonal system")
        factor = lower[i-1]/b[i-1]
        b[i] -= factor*c[i-1]; d[i] -= factor*d[i-1]
    result = [0.0]*n; result[-1] = d[-1]/b[-1]
    for i in range(n-2, -1, -1): result[i] = (d[i]-c[i]*result[i+1])/b[i]
    return result


def simulate(*, length_m, area_m2, porosity, permeability_m2, viscosity_pa_s,
             density_kg_m3, pressure_drop_pa, cells, delta_t_s, end_s, species):
    """Return rectangular-quadrature water/species outlet increments per step."""
    values = (length_m, area_m2, porosity, permeability_m2, viscosity_pa_s,
              density_kg_m3, pressure_drop_pa, delta_t_s, end_s)
    if any(not math.isfinite(x) for x in values) or min(values[:6]) <= 0 or pressure_drop_pa < 0:
        raise ValueError("invalid reduced saturated-Darcy inputs")
    if isinstance(cells, bool) or cells < 2: raise ValueError("cells must be at least two")
    dx = length_m/cells
    flow = permeability_m2*area_m2*pressure_drop_pa/(viscosity_pa_s*length_m)
    velocity = flow/area_m2
    concentrations = [[0.0]*cells for _ in species]
    remaining = [s.initial_mass_kg for s in species]
    steps = []
    count = int(round(end_s/delta_t_s))
    if abs(count*delta_t_s-end_s) > 1e-12: raise ValueError("end_s must be an integer timestep multiple")
    for step in range(count):
        increments = []
        for si, spec in enumerate(species):
            if any(not math.isfinite(x) for x in (spec.initial_mass_kg, spec.rate_1_s,
                                                   spec.capacity_kg_m3, spec.diffusivity_m2_s)):
                raise ValueError("nonfinite species input")
            source_mass = min(remaining[si], spec.rate_1_s*remaining[si]*delta_t_s)
            remaining[si] -= source_mass
            source = source_mass/(area_m2*length_m*delta_t_s)
            adv = velocity/dx; diff = spec.diffusivity_m2_s/dx**2
            lower = [-(adv+diff)]*(cells-1); upper = [-diff]*(cells-1)
            diagonal = [porosity/delta_t_s+adv+2*diff]*cells
            rhs = [porosity*c/delta_t_s+source for c in concentrations[si]]
            # Inlet Dirichlet zero enters only through a zero RHS term; outlet zero gradient.
            diagonal[-1] -= diff
            solved = tridiagonal(lower, diagonal, upper, rhs)
            solved = [min(max(c, 0.0), spec.capacity_kg_m3) for c in solved]
            concentrations[si] = solved
            increments.append(flow*solved[-1]*delta_t_s)
        steps.append({"start_time_s":step*delta_t_s, "delta_t_s":delta_t_s,
                      "water_mass_kg":density_kg_m3*flow*delta_t_s,
                      "species_mass_kg":increments})
    return {"flow_m3_s":flow, "steps":steps, "remaining_species_mass_kg":remaining}
