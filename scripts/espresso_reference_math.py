#!/usr/bin/env python3
"""Independent reduced mathematics for the WP-0.1 reference and fixtures.

This module is Python-standard-library only.  It provides closed-form hydraulic
checks and a one-dimensional finite-volume verification twin for the bounded
OpenFOAM model.  It is intentionally independent of OpenFOAM field parsing.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


TINY = 1.0e-30


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def pressure_at_time(
    time_s: float,
    target_pressure_pa: float,
    ramp_time_s: float,
) -> float:
    if ramp_time_s <= 0.0:
        return target_pressure_pa
    return target_pressure_pa * clamp(time_s / ramp_time_s, 0.0, 1.0)


def positive_driving_pressure_integral(
    start_s: float,
    end_s: float,
    target_pressure_pa: float,
    ramp_time_s: float,
    front_pressure_pa: float,
) -> float:
    """Integrate max(P_in(t)-P_front, 0) exactly over [start_s, end_s]."""
    if end_s <= start_s:
        return 0.0
    start_s = max(start_s, 0.0)
    end_s = max(end_s, start_s)

    if ramp_time_s <= 0.0:
        return max(target_pressure_pa - front_pressure_pa, 0.0) * (end_s - start_s)
    if target_pressure_pa <= 0.0:
        return max(-front_pressure_pa, 0.0) * (end_s - start_s)

    result = 0.0
    slope = target_pressure_pa / ramp_time_s
    threshold_s = ramp_time_s * front_pressure_pa / target_pressure_pa

    ramp_start = max(start_s, 0.0, threshold_s)
    ramp_end = min(end_s, ramp_time_s)
    if ramp_end > ramp_start:
        result += (
            0.5 * slope * (ramp_end * ramp_end - ramp_start * ramp_start)
            - front_pressure_pa * (ramp_end - ramp_start)
        )

    plateau_start = max(start_s, ramp_time_s)
    if end_s > plateau_start:
        result += max(target_pressure_pa - front_pressure_pa, 0.0) * (
            end_s - plateau_start
        )

    return max(result, 0.0)


def first_drip_time_s(scenario: Dict) -> float:
    bed = scenario["coffee_bed"]
    hydraulic = scenario["hydraulics"]
    liquid = scenario["liquid"]
    wetting = scenario["wetting"]

    depth = float(bed["bed_depth_m"])
    initial_front = float(wetting.get("initial_wet_front_m", 0.0))
    if initial_front >= depth:
        return 0.0

    required_integral = (
        (depth * depth - initial_front * initial_front)
        * float(bed["initial_porosity"])
        * float(liquid["dynamic_viscosity_Pa_s"])
        / (2.0 * float(hydraulic["wetting_permeability_m2"]))
    )

    target = float(hydraulic["target_inlet_pressure_gauge_Pa"])
    ramp = float(hydraulic["pressure_ramp_time_s"])
    front_pressure = float(hydraulic["front_pressure_gauge_Pa"])
    plateau_drive = max(target - front_pressure, 0.0)
    if plateau_drive <= 0.0:
        return math.inf

    high = max(ramp, 1.0)
    while (
        positive_driving_pressure_integral(0.0, high, target, ramp, front_pressure)
        < required_integral
    ):
        high *= 2.0
        if high > 1.0e9:
            return math.inf

    low = 0.0
    for _ in range(100):
        mid = 0.5 * (low + high)
        integral = positive_driving_pressure_integral(
            0.0, mid, target, ramp, front_pressure
        )
        if integral >= required_integral:
            high = mid
        else:
            low = mid
    return 0.5 * (low + high)


def straight_sided_wedge_scale(wedge_angle_deg: float) -> float:
    theta = math.radians(float(wedge_angle_deg))
    if not (0.0 < theta < math.pi):
        raise ValueError("wedge angle must lie between 0 and 180 degrees")
    return 2.0 * math.pi / math.sin(theta)


def nominal_cylinder_volume_m3(scenario: Dict) -> float:
    radius = float(scenario["geometry"]["basket_radius_m"])
    depth = float(scenario["coffee_bed"]["bed_depth_m"])
    return math.pi * radius * radius * depth


def full_cross_section_area_m2(scenario: Dict) -> float:
    radius = float(scenario["geometry"]["basket_radius_m"])
    return math.pi * radius * radius


def axial_permeability_profile(scenario: Dict) -> Tuple[List[float], float]:
    geometry = scenario["geometry"]
    bed = scenario["coffee_bed"]
    hydraulic = scenario["hydraulics"]
    cells = int(geometry["axial_cells"])
    depth = float(bed["bed_depth_m"])
    dx = depth / cells
    profile = hydraulic.get("permeability_profile", {"type": "uniform"})
    profile_type = str(profile.get("type", "uniform"))

    if profile_type == "uniform":
        value = float(hydraulic["saturated_permeability_m2"])
        return [value] * cells, dx
    if profile_type == "axial_two_layer":
        interface = float(profile["interface_position_m"])
        upstream = float(profile["upstream_permeability_m2"])
        downstream = float(profile["downstream_permeability_m2"])
        values = [
            upstream if (i + 0.5) * dx < interface else downstream
            for i in range(cells)
        ]
        return values, dx
    raise ValueError(f"unsupported permeability profile: {profile_type}")


def continuum_hydraulic_resistance_m_inv(scenario: Dict) -> float:
    bed = scenario["coffee_bed"]
    hydraulic = scenario["hydraulics"]
    depth = float(bed["bed_depth_m"])
    profile = hydraulic.get("permeability_profile", {"type": "uniform"})
    profile_type = str(profile.get("type", "uniform"))
    if profile_type == "uniform":
        return depth / float(hydraulic["saturated_permeability_m2"])
    if profile_type == "axial_two_layer":
        interface = float(profile["interface_position_m"])
        return (
            interface / float(profile["upstream_permeability_m2"])
            + (depth - interface) / float(profile["downstream_permeability_m2"])
        )
    raise ValueError(f"unsupported permeability profile: {profile_type}")


def steady_outlet_flow_m3_s(scenario: Dict, inlet_pressure_pa: Optional[float] = None) -> float:
    hydraulic = scenario["hydraulics"]
    liquid = scenario["liquid"]
    if inlet_pressure_pa is None:
        inlet_pressure_pa = float(hydraulic["target_inlet_pressure_gauge_Pa"])
    pressure_drop = inlet_pressure_pa - float(hydraulic["outlet_pressure_gauge_Pa"])
    if pressure_drop <= 0.0:
        return 0.0
    resistance = continuum_hydraulic_resistance_m_inv(scenario)
    return (
        full_cross_section_area_m2(scenario)
        * pressure_drop
        / (float(liquid["dynamic_viscosity_Pa_s"]) * resistance)
    )


def analytical_preview(scenario: Dict) -> Dict:
    bed = scenario["coffee_bed"]
    liquid = scenario["liquid"]
    time_cfg = scenario["time"]
    first_drip = first_drip_time_s(scenario)
    q = steady_outlet_flow_m3_s(scenario)
    rho = float(liquid["density_kg_m3"])
    end_s = float(time_cfg["end_s"])
    initial_front = float(scenario["wetting"].get("initial_wet_front_m", 0.0))
    initial_storage = (
        rho
        * float(bed["initial_porosity"])
        * full_cross_section_area_m2(scenario)
        * initial_front
    )
    pore_water = (
        rho
        * float(bed["initial_porosity"])
        * nominal_cylinder_volume_m3(scenario)
    )
    return {
        "model": "closed_form_and_reduced_preflight_not_an_openfoam_result",
        "pressure_integration_method": "exact_piecewise_linear_positive_driving_pressure_integral",
        "first_drip_s": first_drip,
        "steady_outlet_volume_flow_m3_s": q,
        "steady_outlet_water_mass_flow_kg_s": rho * q,
        "water_mass_at_end_kg_excluding_solute": max(end_s - first_drip, 0.0) * rho * q,
        "initial_stored_water_mass_kg": initial_storage,
        "saturated_pore_water_mass_kg": pore_water,
        "straight_sided_wedge_scale": straight_sided_wedge_scale(
            scenario["geometry"]["wedge_angle_deg"]
        ),
        "nominal_cylinder_volume_m3": nominal_cylinder_volume_m3(scenario),
        "notes": [
            "The permeability is the declared R0 hydraulic calibration parameter.",
            "The preview does not establish physical validation.",
        ],
    }


def solve_tridiagonal(
    lower: Sequence[float],
    diagonal: Sequence[float],
    upper: Sequence[float],
    rhs: Sequence[float],
) -> List[float]:
    n = len(diagonal)
    if not (len(lower) == len(upper) == len(rhs) == n):
        raise ValueError("tridiagonal arrays must have the same length")
    c = list(upper)
    d = list(rhs)
    b = list(diagonal)
    a = list(lower)
    for i in range(1, n):
        if abs(b[i - 1]) <= TINY:
            raise ZeroDivisionError("singular tridiagonal system")
        factor = a[i] / b[i - 1]
        b[i] -= factor * c[i - 1]
        d[i] -= factor * d[i - 1]
    result = [0.0] * n
    if abs(b[-1]) <= TINY:
        raise ZeroDivisionError("singular tridiagonal system")
    result[-1] = d[-1] / b[-1]
    for i in range(n - 2, -1, -1):
        if abs(b[i]) <= TINY:
            raise ZeroDivisionError("singular tridiagonal system")
        result[i] = (d[i] - c[i] * result[i + 1]) / b[i]
    return result


def saturation_profile(
    cell_centres_m: Sequence[float],
    wet_front_m: float,
    bed_depth_m: float,
    smoothing_length_m: float,
) -> List[float]:
    if wet_front_m >= bed_depth_m - 1.0e-14:
        return [1.0] * len(cell_centres_m)
    if wet_front_m <= 0.0:
        return [0.0] * len(cell_centres_m)
    smoothing = max(smoothing_length_m, 1.0e-30)
    return [
        clamp(0.5 * (1.0 + math.tanh((wet_front_m - x) / smoothing)), 0.0, 1.0)
        for x in cell_centres_m
    ]


def b0_reduced_simulation(scenario: Dict) -> Dict:
    """Run a 1-D finite-volume verification twin of the bounded reference model."""
    geometry = scenario["geometry"]
    bed = scenario["coffee_bed"]
    liquid = scenario["liquid"]
    hydraulic = scenario["hydraulics"]
    wetting = scenario["wetting"]
    extraction = scenario["extraction"]
    time_cfg = scenario["time"]

    n = int(geometry["axial_cells"])
    depth = float(bed["bed_depth_m"])
    dx = depth / n
    centres = [(i + 0.5) * dx for i in range(n)]
    area = full_cross_section_area_m2(scenario)
    volume_cell = area * dx
    phi = float(bed["initial_porosity"])
    rho = float(liquid["density_kg_m3"])
    diffusivity = float(liquid["effective_solute_diffusivity_m2_s"])
    dt = float(time_cfg["delta_t_s"])
    end_s = float(time_cfg["end_s"])
    steps_float = end_s / dt
    steps = int(round(steps_float))
    if abs(steps * dt - end_s) > 1.0e-10 * max(1.0, end_s):
        raise ValueError("end time must be an integer multiple of delta_t for B0 parity")

    initial_extractable = (
        float(bed["dry_dose_kg"])
        * float(bed["initial_extractable_fraction_dry_basis"])
    )
    remaining = [initial_extractable / (area * depth)] * n
    concentration = [0.0] * n
    wet_front = float(wetting.get("initial_wet_front_m", 0.0))
    smoothing = float(wetting["front_smoothing_cells"]) * dx
    saturation = saturation_profile(centres, wet_front, depth, smoothing)
    stored_water = rho * phi * sum(saturation) * volume_cell
    initial_stored_water = stored_water
    previous_stored_water = stored_water

    first_drip = 0.0 if wet_front >= depth else -1.0
    time_to_target = -1.0
    cumulative_inlet_water = 0.0
    cup_water = 0.0
    cup_solute = 0.0
    backdiffused_solute = 0.0
    previous_cup_beverage = 0.0
    max_liquid_residual = 0.0
    max_solute_residual = 0.0
    max_concentration = 0.0
    target_mass = float(time_cfg["target_beverage_mass_kg"])
    rate_constant = float(extraction["rate_constant_1_s"])
    saturation_concentration = float(extraction["saturation_concentration_kg_m3"])

    final_q = 0.0
    for step in range(1, steps + 1):
        time_s = step * dt
        start_s = time_s - dt
        inlet_pressure = pressure_at_time(
            time_s,
            float(hydraulic["target_inlet_pressure_gauge_Pa"]),
            float(hydraulic["pressure_ramp_time_s"]),
        )
        previous_saturation = list(saturation)
        previous_front = wet_front
        saturated_at_start = previous_front >= depth - 1.0e-14

        if not saturated_at_start:
            integral = positive_driving_pressure_integral(
                start_s,
                time_s,
                float(hydraulic["target_inlet_pressure_gauge_Pa"]),
                float(hydraulic["pressure_ramp_time_s"]),
                float(hydraulic["front_pressure_gauge_Pa"]),
            )
            front_squared = (
                previous_front * previous_front
                + 2.0
                * float(hydraulic["wetting_permeability_m2"])
                * integral
                / (phi * float(liquid["dynamic_viscosity_Pa_s"]))
            )
            wet_front = min(depth, math.sqrt(max(front_squared, 0.0)))
            if wet_front >= depth - 1.0e-14 and first_drip < 0.0:
                required = (
                    (depth * depth - previous_front * previous_front)
                    * phi
                    * float(liquid["dynamic_viscosity_Pa_s"])
                    / (2.0 * float(hydraulic["wetting_permeability_m2"]))
                )
                low, high = start_s, time_s
                for _ in range(100):
                    mid = 0.5 * (low + high)
                    current = positive_driving_pressure_integral(
                        start_s,
                        mid,
                        float(hydraulic["target_inlet_pressure_gauge_Pa"]),
                        float(hydraulic["pressure_ramp_time_s"]),
                        float(hydraulic["front_pressure_gauge_Pa"]),
                    )
                    if current >= required:
                        high = mid
                    else:
                        low = mid
                first_drip = 0.5 * (low + high)
                wet_front = depth

        saturation = saturation_profile(centres, wet_front, depth, smoothing)
        stored_water = rho * phi * sum(saturation) * volume_cell
        if not saturated_at_start:
            cumulative_inlet_water += max(stored_water - previous_stored_water, 0.0)
        previous_stored_water = stored_water

        source = []
        for rem, conc, wet in zip(remaining, concentration, saturation):
            capacity = max(1.0 - conc / saturation_concentration, 0.0)
            rate = rate_constant * rem * wet * capacity
            rate = min(max(rate, 0.0), rem / dt)
            source.append(rate)

        q = 0.0
        outlet_solute_rate = 0.0
        inlet_backdiffusion_rate = 0.0
        if saturated_at_start:
            q = steady_outlet_flow_m3_s(scenario, inlet_pressure)
            q_area = q / area
            transient = phi * dx / dt
            conductance = phi * diffusivity / dx
            lower = [0.0] * n
            diagonal = [0.0] * n
            upper = [0.0] * n
            rhs = [0.0] * n
            old_concentration = list(concentration)
            for i in range(n):
                diagonal[i] = transient + q_area
                rhs[i] = transient * old_concentration[i] + source[i] * dx
                if i > 0:
                    lower[i] -= q_area

                if i == 0:
                    diagonal[i] += 2.0 * conductance
                else:
                    diagonal[i] += conductance
                    lower[i] -= conductance
                if i < n - 1:
                    diagonal[i] += conductance
                    upper[i] -= conductance

            concentration = [max(value, 0.0) for value in solve_tridiagonal(
                lower, diagonal, upper, rhs
            )]
            remaining = [max(rem - dt * rate, 0.0) for rem, rate in zip(remaining, source)]
            outlet_solute_rate = q * concentration[-1]
            inlet_backdiffusion_rate = 2.0 * phi * diffusivity * area * concentration[0] / dx
            cumulative_inlet_water += rho * q * dt
            cup_water += rho * q * dt
            cup_solute += max(outlet_solute_rate, 0.0) * dt
            backdiffused_solute += max(inlet_backdiffusion_rate, 0.0) * dt
        else:
            new_concentration: List[float] = []
            new_remaining: List[float] = []
            for old_sat, new_sat, conc, rem, rate in zip(
                previous_saturation, saturation, concentration, remaining, source
            ):
                old_bulk = phi * old_sat * conc
                new_bulk = old_bulk + dt * rate
                new_liquid_fraction = phi * new_sat
                new_concentration.append(
                    max(new_bulk / new_liquid_fraction, 0.0)
                    if new_liquid_fraction > TINY
                    else 0.0
                )
                new_remaining.append(max(rem - dt * rate, 0.0))
            concentration = new_concentration
            remaining = new_remaining

        remaining_mass = sum(remaining) * volume_cell
        dissolved_mass = sum(
            phi * sat * conc for sat, conc in zip(saturation, concentration)
        ) * volume_cell
        cup_beverage = cup_water + cup_solute
        liquid_residual = (
            initial_stored_water + cumulative_inlet_water - stored_water - cup_water
        )
        solute_residual = (
            initial_extractable
            - remaining_mass
            - dissolved_mass
            - cup_solute
            - backdiffused_solute
        )
        max_liquid_residual = max(max_liquid_residual, abs(liquid_residual))
        max_solute_residual = max(max_solute_residual, abs(solute_residual))
        max_concentration = max(max_concentration, max(concentration))

        if (
            time_to_target < 0.0
            and cup_beverage >= target_mass
            and cup_beverage > previous_cup_beverage
        ):
            fraction = clamp(
                (target_mass - previous_cup_beverage)
                / (cup_beverage - previous_cup_beverage),
                0.0,
                1.0,
            )
            time_to_target = start_s + fraction * dt
        previous_cup_beverage = cup_beverage
        final_q = q

    final_beverage = cup_water + cup_solute
    return {
        "schema_version": "espresso.whole_pull.b0_reduced_twin.v0.1.4",
        "model": "independent_1d_finite_volume_reduced_verification_twin",
        "pressure_integration_method": "exact_piecewise_linear_positive_driving_pressure_integral",
        "scenario_id": scenario["scenario_id"],
        "axial_cells": n,
        "delta_t_s": dt,
        "primary_outputs": {
            "first_drip_s": first_drip,
            "outlet_flow_final_m3_s": final_q,
            "cup_water_mass_at_end_kg": cup_water,
            "cup_solute_mass_at_end_kg": cup_solute,
            "cup_beverage_mass_at_end_kg": final_beverage,
            "time_to_target_mass_s": None if time_to_target < 0.0 else time_to_target,
            "cumulative_tds_mass_fraction": cup_solute / final_beverage if final_beverage > 0.0 else 0.0,
            "extraction_yield_mass_fraction": cup_solute / float(bed["dry_dose_kg"]),
            "retained_water_mass_kg": stored_water,
            "retained_dissolved_solute_mass_kg": dissolved_mass,
            "remaining_extractable_mass_kg": remaining_mass,
            "solute_backdiffusion_mass_kg": backdiffused_solute,
            "max_liquid_balance_residual_kg": max_liquid_residual,
            "max_solute_balance_residual_kg": max_solute_residual,
            "max_concentration_kg_m3": max_concentration,
        },
        "claim_ceiling": "Code/numerical verification twin only; not physical validation.",
    }


def discrete_layered_pressure_reference(scenario: Dict) -> Dict:
    """Exact 1-D finite-volume pressure reference for linear face interpolation."""
    permeability, dx = axial_permeability_profile(scenario)
    liquid = scenario["liquid"]
    hydraulic = scenario["hydraulics"]
    geometry = scenario["geometry"]
    mu = float(liquid["dynamic_viscosity_Pa_s"])
    mobility = [value / mu for value in permeability]
    n = len(mobility)

    resistances: List[float] = [0.5 * dx / mobility[0]]
    for i in range(n - 1):
        face_mobility = 0.5 * (mobility[i] + mobility[i + 1])
        resistances.append(dx / face_mobility)
    resistances.append(0.5 * dx / mobility[-1])

    delta_p = (
        float(hydraulic["target_inlet_pressure_gauge_Pa"])
        - float(hydraulic["outlet_pressure_gauge_Pa"])
    )
    q_area = delta_p / sum(resistances)
    area = full_cross_section_area_m2(scenario)
    q = q_area * area

    cell_pressures: List[float] = []
    outlet = float(hydraulic["outlet_pressure_gauge_Pa"])
    for i in range(n):
        downstream_resistance = resistances[-1]
        for face_index in range(i + 1, n):
            downstream_resistance += resistances[face_index]
        cell_pressures.append(outlet + q_area * downstream_resistance)

    centres = [(i + 0.5) * dx for i in range(n)]
    probes = scenario.get("verification", {}).get("pressure_probes", [])
    probe_values = []
    for probe in probes:
        position = float(probe["position_m"])
        half_width = float(probe["half_width_m"])
        selected = [
            pressure
            for centre, pressure in zip(centres, cell_pressures)
            if abs(centre - position) <= half_width + 1.0e-15
        ]
        probe_values.append(sum(selected) / len(selected) if selected else None)

    return {
        "schema_version": "espresso.whole_pull.layered_pressure_reference.v0.1.4",
        "reference": "exact_1d_finite_volume_with_linear_face_mobility_interpolation",
        "outlet_flow_m3_s": q,
        "pressure_probe_values_pa": probe_values,
        "cell_pressure_min_pa": min(cell_pressures),
        "cell_pressure_max_pa": max(cell_pressures),
        "axial_cells": n,
        "delta_x_m": dx,
    }
