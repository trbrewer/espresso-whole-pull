#!/usr/bin/env python3
"""Independent reduced WP02-001 flow history."""
from __future__ import annotations

from waszkiewicz_effective_permeability import closure_state


def reduced_history(scenario: dict) -> list[dict]:
    closure = scenario["effective_permeability_evolution"]
    source = closure["source_parameters"]
    hydraulic = scenario["hydraulics"]
    time = scenario["time"]
    first_drip = float(scenario["verification"]["analytical_first_drip_s"])
    saturated_time = first_drip
    rows = []
    steps = round((time["end_s"] - time["start_s"]) / time["delta_t_s"])
    area = scenario["geometry"]["hydraulic_bed_area_m2"]
    mu = scenario["liquid"]["dynamic_viscosity_Pa_s"]
    depth = scenario["coffee_bed"]["bed_depth_m"]
    pressure = hydraulic["target_inlet_pressure_gauge_Pa"]
    base = hydraulic["saturated_permeability_m2"]
    for index in range(steps + 1):
        solver_time = time["start_s"] + index * time["delta_t_s"]
        state = closure_state(
            solver_time_s=solver_time,
            saturated=solver_time >= saturated_time,
            p_bar=closure["source_reference_pressure_bar"],
            source_to_solver_offset_s=closure["source_to_solver_offset_s"],
            source_validity_start_s=closure["source_validity_start_s"],
            minimum=closure["minimum_effective_multiplier"],
            base_permeability_m2=base,
            pc_bar=source["pc_bar"],
            qc_g_s=source["qc_g_per_s"],
            k_g=source["k_solids_g"],
            l_s=source["l_solids_s"],
            m_s=source["m_solids_s"],
            dose_g=source["dose_g"],
        )
        flow_m3_s = (
            state["effective_permeability_m2"] * area * pressure / (mu * depth)
            if state["active"]
            else 0.0
        )
        rows.append({"time_s": solver_time, "outlet_flow_m3_s": flow_m3_s, **state})
    return rows
