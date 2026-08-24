"""Independent continuous and exact-discrete R2 V15B diffusion oracles."""
from __future__ import annotations

import math
from dataclasses import dataclass


def mode_coefficient(*, n: int, x: float, time_s: float, length_m: float,
                     phi: float, diffusivity: float, rate: float,
                     initial_inventory_density: float) -> float:
    half = n + 0.5
    eigenvalue = half * math.pi / length_m
    spatial = math.sin(eigenvalue * x)
    b_n = 2.0 / (half * math.pi)
    diffusion_rate = diffusivity * eigenvalue * eigenvalue
    if math.isclose(diffusion_rate, rate, rel_tol=0.0, abs_tol=1.0e-14):
        temporal = time_s * math.exp(-rate * time_s)
    else:
        temporal = ((math.exp(-rate * time_s) -
                     math.exp(-diffusion_rate * time_s)) /
                    (diffusion_rate - rate))
    return rate * initial_inventory_density / phi * b_n * temporal * spatial


def concentration(*, x: float, time_s: float, length_m: float, phi: float,
                  diffusivity: float, rate: float,
                  initial_inventory_density: float,
                  relative_remainder: float = 1.0e-10,
                  maximum_terms: int = 200000) -> tuple[float, dict]:
    """Evaluate the eigenfunction series with a conservative tail estimate."""
    total = 0.0
    last = math.inf
    small_count = 0
    for n in range(maximum_terms):
        term = mode_coefficient(
            n=n, x=x, time_s=time_s, length_m=length_m, phi=phi,
            diffusivity=diffusivity, rate=rate,
            initial_inventory_density=initial_inventory_density,
        )
        total += term
        last = abs(term)
        scale = max(abs(total), 1.0e-300)
        if last <= relative_remainder * scale * 0.1:
            small_count += 1
            if small_count >= 32:
                return total, {
                    "terms": n + 1,
                    "estimated_relative_remainder": last / scale,
                    "required_relative_remainder": relative_remainder,
                }
        else:
            small_count = 0
    raise RuntimeError(
        f"analytical series did not meet remainder target; last={last} total={total}"
    )


def remaining_mass(initial_mass_kg: float, rate: float, time_s: float) -> float:
    return initial_mass_kg * math.exp(-rate * time_s)


def integrated_solution(*, time_s: float, length_m: float, area_m2: float,
                        phi: float, diffusivity: float, rate: float,
                        initial_inventory_density: float,
                        terms: int = 2000) -> dict:
    """Analytical dissolved mass and inlet loss from profile and boundary flux."""
    concentration_integral = 0.0
    flux_time_integral = 0.0
    for n in range(terms):
        half = n + 0.5
        eigenvalue = half*math.pi/length_m
        b_n = 2.0/(half*math.pi)
        diffusion_rate = diffusivity*eigenvalue*eigenvalue
        if math.isclose(diffusion_rate, rate, rel_tol=0.0, abs_tol=1e-14):
            temporal = time_s*math.exp(-rate*time_s)
            temporal_integral = ((1.0-math.exp(-rate*time_s))/rate -
                                 time_s*math.exp(-rate*time_s))/rate
        else:
            temporal=(math.exp(-rate*time_s)-math.exp(-diffusion_rate*time_s))/(diffusion_rate-rate)
            temporal_integral=((1.0-math.exp(-rate*time_s))/rate-
                               (1.0-math.exp(-diffusion_rate*time_s))/diffusion_rate)/(diffusion_rate-rate)
        prefactor=rate*initial_inventory_density/phi*b_n
        concentration_integral += prefactor*temporal/eigenvalue
        flux_time_integral += prefactor*temporal_integral*eigenvalue
    # Analytic asymptotic tails make the boundary-flux evaluation independent
    # and accurate without summing the slowly convergent 1/(n+1/2)^2 tail.
    totals={2:math.pi**2/2,4:math.pi**4/6,6:math.pi**6/15,
            8:17*math.pi**8/630}
    tails={power:totals[power]-sum(1/(n+.5)**power for n in range(terms))
           for power in totals}
    exponential=math.exp(-rate*time_s)
    source_integral=(1-exponential)/rate
    common=rate*initial_inventory_density/phi
    concentration_integral += common*exponential*2*length_m**3/(diffusivity*math.pi**4)*(
        tails[4]+rate*length_m**2/(diffusivity*math.pi**2)*tails[6]+
        rate**2*length_m**4/(diffusivity**2*math.pi**4)*tails[8])
    flux_time_integral += common*2*length_m/(diffusivity*math.pi**2)*(
        source_integral*tails[2]+(source_integral*rate-1)*length_m**2/
        (diffusivity*math.pi**2)*tails[4]+rate*(source_integral*rate-1)*
        length_m**4/(diffusivity**2*math.pi**4)*tails[6])
    dissolved_mass=phi*area_m2*concentration_integral
    boundary_flux_mass=phi*diffusivity*area_m2*flux_time_integral
    initial_mass=initial_inventory_density*area_m2*length_m
    closure_mass=initial_mass-remaining_mass(initial_mass,rate,time_s)-dissolved_mass
    return {
        "dissolved_mass_kg":dissolved_mass,
        "back_diffusion_closure_kg":closure_mass,
        "back_diffusion_flux_kg":boundary_flux_mass,
        "internal_closure_relative":abs(closure_mass-boundary_flux_mass)/max(initial_mass,1e-300),
        "terms":terms,
    }


def observed_order(coarse_error: float, reference_error: float,
                   refinement_ratio: float = 2.0) -> float:
    if coarse_error <= 0.0 or reference_error <= 0.0:
        raise ValueError("observed order requires positive errors")
    return math.log(coarse_error / reference_error) / math.log(refinement_ratio)


def weighted_errors(actual: list[float], expected: list[float],
                    volumes: list[float]) -> dict:
    if not actual or len(actual) != len(expected) or len(actual) != len(volumes):
        raise ValueError("profile and volume vectors must be nonempty and aligned")
    if any((not math.isfinite(v) or v <= 0.0) for v in volumes):
        raise ValueError("cell volumes must be finite and positive")
    total_volume = sum(volumes)
    absolute = [abs(a-e) for a, e in zip(actual, expected)]
    l1 = sum(v*e for v, e in zip(volumes, absolute)) / total_volume
    l2 = math.sqrt(sum(v*e*e for v, e in zip(volumes, absolute))/total_volume)
    reference_l1 = sum(v*abs(e) for v, e in zip(volumes, expected))/total_volume
    reference_l2 = math.sqrt(sum(v*e*e for v, e in zip(volumes, expected))/total_volume)
    return {
        "l1_absolute": l1,
        "l1_relative": l1/max(reference_l1, 1.0e-300),
        "l2_absolute": l2,
        "l2_relative": l2/max(reference_l2, 1.0e-300),
        "maximum_absolute": max(absolute),
        "maximum_relative": max(absolute)/max(max(abs(v) for v in expected), 1.0e-300),
    }


@dataclass(frozen=True)
class ManufacturedSpecies:
    species_id: str
    initial_inventory_density: float
    rate: float
    diffusivity: float


def discrete_inventory_factor(rate: float, delta_t: float) -> float:
    factor = 1.0-rate*delta_t
    if not 0.0 < factor <= 1.0:
        raise ValueError("explicit inventory factor must be in (0, 1]")
    return factor


def discrete_remaining_density(initial_density: float, rate: float,
                               delta_t: float, steps: int) -> float:
    if steps < 0:
        raise ValueError("steps must be nonnegative")
    return initial_density*discrete_inventory_factor(rate,delta_t)**steps


def discrete_mode_recurrence(*, mode: int, steps: int, delta_t: float,
                             length_m: float, phi: float, diffusivity: float,
                             rate: float, initial_inventory_density: float) -> float:
    half=mode+.5; eigenvalue=half*math.pi/length_m
    b_n=2.0/(half*math.pi)
    r_d=1.0/(1.0+diffusivity*eigenvalue*eigenvalue*delta_t)
    r_k=discrete_inventory_factor(rate,delta_t)
    amplitude=0.0
    inventory_factor=1.0
    source=rate*initial_inventory_density/phi*b_n
    for _ in range(steps):
        amplitude=r_d*(amplitude+delta_t*source*inventory_factor)
        inventory_factor*=r_k
    return amplitude


def discrete_mode_closed(*, mode: int, steps: int, delta_t: float,
                         length_m: float, phi: float, diffusivity: float,
                         rate: float, initial_inventory_density: float) -> float:
    half=mode+.5; eigenvalue=half*math.pi/length_m
    b_n=2.0/(half*math.pi)
    r_d=1.0/(1.0+diffusivity*eigenvalue*eigenvalue*delta_t)
    r_k=discrete_inventory_factor(rate,delta_t)
    prefactor=delta_t*rate*initial_inventory_density/phi*b_n
    if math.isclose(r_d,r_k,rel_tol=0.0,abs_tol=8*math.ulp(max(r_d,r_k))):
        return prefactor*steps*r_d**steps
    return prefactor*r_d*(r_d**steps-r_k**steps)/(r_d-r_k)


def discrete_mode_sum_closed(*, mode: int, steps: int, delta_t: float,
                             length_m: float, phi: float, diffusivity: float,
                             rate: float,
                             initial_inventory_density: float) -> float:
    """Return sum(a_m, m=1..steps) without iterating over timesteps."""
    half=mode+.5; eigenvalue=half*math.pi/length_m
    b_n=2.0/(half*math.pi)
    r_d=1.0/(1.0+diffusivity*eigenvalue*eigenvalue*delta_t)
    r_k=discrete_inventory_factor(rate,delta_t)
    prefactor=delta_t*rate*initial_inventory_density/phi*b_n
    if math.isclose(r_d,r_k,rel_tol=0.0,abs_tol=8*math.ulp(max(r_d,r_k))):
        if steps == 0:
            return 0.0
        numerator=r_d*(1.0-(steps+1)*r_d**steps+steps*r_d**(steps+1))
        return prefactor*numerator/(1.0-r_d)**2
    sum_rd=r_d*(1.0-r_d**steps)/(1.0-r_d)
    sum_rk=r_k*(1.0-r_k**steps)/(1.0-r_k)
    return prefactor*r_d*(sum_rd-sum_rk)/(r_d-r_k)


def discrete_profile(*, locations_m: list[float], steps: int, delta_t: float,
                     length_m: float, phi: float, diffusivity: float,
                     rate: float, initial_inventory_density: float,
                     terms: int = 20000) -> tuple[list[float], dict]:
    if not locations_m or terms < 64:
        raise ValueError("locations and at least 64 modes are required")
    values=[0.0]*len(locations_m)
    last=0.0
    for mode in range(terms):
        coefficient=discrete_mode_closed(
            mode=mode,steps=steps,delta_t=delta_t,length_m=length_m,phi=phi,
            diffusivity=diffusivity,rate=rate,
            initial_inventory_density=initial_inventory_density)
        last=abs(coefficient)
        eigenvalue=(mode+.5)*math.pi/length_m
        for index,x in enumerate(locations_m):
            values[index]+=coefficient*math.sin(eigenvalue*x)
    scale=max(max(abs(value) for value in values),1e-300)
    # Coefficients have an asymptotic n^-3 envelope; the oscillatory tail at
    # interior half-cell locations is bounded conservatively by the first
    # omitted coefficient times two.
    estimated=2*last/scale
    return values,{"terms":terms,"estimated_relative_remainder":estimated,
                   "required_relative_remainder":1e-10}


def discrete_integrals(*, steps: int, delta_t: float, length_m: float,
                       area_m2: float, phi: float, diffusivity: float,
                       rate: float, initial_inventory_density: float,
                       terms: int = 200000) -> dict:
    if terms < 256 or terms % 4:
        raise ValueError("terms must be a multiple of four and at least 256")
    dissolved_integral=0.0
    boundary_time_integral=0.0
    flux_snapshots={}
    for mode in range(terms):
        eigenvalue=(mode+.5)*math.pi/length_m
        final_amplitude=discrete_mode_closed(
            mode=mode,steps=steps,delta_t=delta_t,length_m=length_m,phi=phi,
            diffusivity=diffusivity,rate=rate,
            initial_inventory_density=initial_inventory_density)
        dissolved_integral+=final_amplitude/eigenvalue
        amplitude_sum=discrete_mode_sum_closed(
            mode=mode,steps=steps,delta_t=delta_t,length_m=length_m,phi=phi,
            diffusivity=diffusivity,rate=rate,
            initial_inventory_density=initial_inventory_density)
        boundary_time_integral+=eigenvalue*amplitude_sum
        count=mode+1
        if count in (terms//4,terms//2,terms):
            flux_snapshots[count]=boundary_time_integral
    dissolved=phi*area_m2*dissolved_integral
    flux_scale=phi*diffusivity*area_m2*delta_t
    # The modal boundary-flux sum has a leading O(1/N) tail.  Two successive
    # first-order Richardson extrapolations independently remove that tail;
    # their difference is the reported remainder estimate.
    extrap_half=2.0*flux_snapshots[terms//2]-flux_snapshots[terms//4]
    extrap_full=2.0*flux_snapshots[terms]-flux_snapshots[terms//2]
    flux=flux_scale*extrap_full
    initial=initial_inventory_density*area_m2*length_m
    remaining=discrete_remaining_density(initial_inventory_density,rate,delta_t,steps)*area_m2*length_m
    closure=initial-remaining-dissolved
    return {"initial_mass_kg":initial,"remaining_mass_kg":remaining,
            "dissolved_mass_kg":dissolved,"back_diffusion_flux_kg":flux,
            "back_diffusion_closure_kg":closure,
            "flux_closure_relative_initial":abs(flux-closure)/max(initial,1e-300),
            "terms":terms,
            "estimated_relative_remainder":abs(flux_scale*(extrap_full-extrap_half))/max(initial,1e-300)}
