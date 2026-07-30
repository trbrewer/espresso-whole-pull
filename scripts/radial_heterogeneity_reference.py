#!/usr/bin/env python3
"""Independent WP02-004 radial parallel-path reference (strict SI)."""

import math


def zone_areas(radius, interface_radius):
    if not (math.isfinite(radius) and math.isfinite(interface_radius)
            and 0.0 < interface_radius < radius):
        raise ValueError("require 0 < interface radius < basket radius")
    inner = math.pi * interface_radius ** 2
    outer = math.pi * (radius ** 2 - interface_radius ** 2)
    return inner, outer


def matched_permeabilities(k0, inner_fraction, contrast, high_zone):
    if not (k0 > 0.0 and 0.0 < inner_fraction < 1.0 and contrast >= 1.0):
        raise ValueError("invalid matched-conductance input")
    outer_fraction = 1.0 - inner_fraction
    high_fraction = inner_fraction if high_zone == "inner" else outer_fraction
    if high_zone not in ("inner", "outer"):
        raise ValueError("high_zone must be inner or outer")
    low = k0 / (high_fraction * contrast + 1.0 - high_fraction)
    high = contrast * low
    return (high, low) if high_zone == "inner" else (low, high)


def stable_path_flow(dp, rd, ri=0.0):
    if not all(math.isfinite(x) for x in (dp, rd, ri)) or rd <= 0.0 or ri < 0.0:
        raise ValueError("invalid path resistance")
    dp = max(dp, 0.0)
    if ri == 0.0:
        return dp / rd
    return 2.0 * dp / (rd + math.sqrt(rd * rd + 4.0 * ri * dp))


def radial_flow(dp, length, mu, rho, areas, permeabilities,
                inertial_permeabilities=None):
    flows = []
    drops = []
    for j, (area, permeability) in enumerate(zip(areas, permeabilities)):
        rd = mu * length / (area * permeability)
        ri = 0.0
        if inertial_permeabilities is not None:
            ki = inertial_permeabilities[j]
            ri = rho * length / (area * area * ki)
        q = stable_path_flow(dp, rd, ri)
        flows.append(q)
        drops.append({"darcy_pa": rd*q, "inertial_pa": ri*q*q})
    return {"zone_flows_m3_s": flows, "total_flow_m3_s": sum(flows),
            "pressure_drops": drops}


def metrics(areas, flows):
    total_area, total_flow = sum(areas), sum(flows)
    area_fractions = [a / total_area for a in areas]
    flow_fractions = ([q / total_flow for q in flows]
                      if total_flow > 0.0 else area_fractions[:])
    focusing = [s / a for s, a in zip(flow_fractions, area_fractions)]
    maldistribution = 0.5 * sum(abs(s-a) for s, a in
                                zip(flow_fractions, area_fractions))
    effective_area = 1.0 / sum(s*s/a for s, a in
                               zip(flow_fractions, area_fractions))
    return {"area_fractions": area_fractions, "flow_fractions": flow_fractions,
            "focusing_factors": focusing,
            "hydraulic_maldistribution_index": maldistribution,
            "effective_hydraulic_area_fraction": effective_area}


def basket_operating_point(pu, po, ru, path):
    lo, hi = po, pu
    for _ in range(200):
        pb = 0.5 * (lo + hi)
        q = path(pb - po)["total_flow_m3_s"]
        residual = pb - (pu - ru*q)
        if residual > 0.0:
            hi = pb
        else:
            lo = pb
    pb = 0.5 * (lo + hi)
    result = path(pb - po)
    result.update({"basket_pressure_pa": pb,
                   "basket_residual_pa": pb-(pu-ru*result["total_flow_m3_s"])})
    return result


def machine_step(time, dt, previous_pu, po, compliance, ru, free_flow,
                 shutoff, ramp_time, path):
    ramp = 1.0 if ramp_time <= 0.0 else min(1.0, max(0.0, time/ramp_time))
    def supply(pu):
        return free_flow*ramp*max(0.0, 1.0-(pu-po)/(shutoff-po))
    def state(pu):
        basket = basket_operating_point(pu, po, ru, path)
        residual = compliance*(pu-previous_pu)/dt - (
            supply(pu)-basket["total_flow_m3_s"])
        return residual, basket
    lo, hi = po, shutoff
    rlo, _ = state(lo)
    rhi, _ = state(hi)
    if not (rlo <= 0.0 <= rhi):
        raise RuntimeError("machine root not bracketed")
    for _ in range(240):
        pu = 0.5*(lo+hi)
        residual, basket = state(pu)
        if residual > 0.0:
            hi = pu
        else:
            lo = pu
    pu = 0.5*(lo+hi)
    residual, basket = state(pu)
    basket.update({"upstream_pressure_pa": pu, "supply_flow_m3_s": supply(pu),
                   "upstream_residual_m3_s": residual,
                   "compliance_storage_m3": compliance*(pu-previous_pu)})
    return basket


def extraction_metrics(initial, remaining):
    extracted = [max(i-r, 0.0) for i, r in zip(initial, remaining)]
    fractions = [e/i if i > 0.0 else 0.0 for e, i in zip(extracted, initial)]
    total_initial, total_extracted = sum(initial), sum(extracted)
    mean = sum(i*f for i, f in zip(initial, fractions))/total_initial
    variance = sum(i*(f-mean)**2 for i, f in zip(initial, fractions))/total_initial
    cv = math.sqrt(variance)/mean if mean > 0.0 else 0.0
    shares = ([e/total_extracted for e in extracted]
              if total_extracted > 0.0 else [i/total_initial for i in initial])
    initial_shares = [i/total_initial for i in initial]
    maldistribution = (0.5*sum(abs(a-b) for a, b in zip(shares, initial_shares))
                       if total_extracted > 0.0 else 0.0)
    return {"extracted_mass": extracted, "extraction_fractions": fractions,
            "mass_weighted_mean_extraction_fraction": mean,
            "extraction_fraction_cv": cv, "extracted_shares": shares,
            "extraction_maldistribution_index": maldistribution}
