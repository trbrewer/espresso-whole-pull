"""Moroney zero-flow dimensionless reference and asymptotic transcriptions.

The ODE uses dimensionless outer time ``tau`` and dimensionless states.
The publisher-literal composite is source reproduction only.  The separately
named governing-ODE-consistent composite is a derived verification reference,
not an author correction and not runtime espresso physics.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Parameters:
    case_id: str
    epsilon: float
    b1: float
    b2: float
    gamma1: float
    surface_time_s: float
    diffusion_time_s: float
    source_card_sha256: str = (
        "d4ad68ae4fd4c0a725fa10dff49a87f81d5c471a1648221ee9a9522c4c847586"
    )

    def __post_init__(self):
        values = (self.epsilon, self.b1, self.b2, self.gamma1,
                  self.surface_time_s, self.diffusion_time_s)
        if not all(math.isfinite(x) and x > 0 for x in values):
            raise ValueError("Moroney parameters must be finite and positive")


FINE = Parameters("FINE_JK_DRIP", 0.028, 5.239, 2.897, 0.70, 1.184, 42.231)
COARSE = Parameters("COARSE_CIMBALI_20", 0.071, 1.99, 1.35, 0.50, 19.389, 270.493)


def derivative(state, p: Parameters):
    """Return d(C_h,C_v,Psi_s)/d(tau), all dimensionless."""
    ch, cv, psi = state
    if not all(math.isfinite(x) for x in state) or min(state) < -1e-12:
        raise ValueError("invalid or materially negative state")
    e, b1, b2 = p.epsilon, p.b1, p.b2
    return (
        -b2 * ch * psi + (b2 / b1) * psi / e - e * b1 * ch + cv,
        e * b1 * ch - cv,
        b1 * ch * psi - psi / e,
    )


def reduced_derivative(state, p: Parameters):
    """Independent equations 31--33 two-state derivative for (C_h,C_v)."""
    ch, cv = state
    if not all(math.isfinite(x) for x in state):
        raise ValueError("nonfinite reduced state")
    psi = 1.0 - (p.b1 / p.b2) * (ch + cv - p.gamma1)
    if min(ch, cv, psi) < -1e-12:
        raise ValueError("invalid or materially negative reduced state")
    return (
        -p.b2 * ch * psi + (p.b2 / p.b1) * psi / p.epsilon
        - p.epsilon * p.b1 * ch + cv,
        p.epsilon * p.b1 * ch - cv,
    )


def inventory(state, p: Parameters):
    """Dimensionless conserved total C_h+C_v+(b2/b1)Psi_s."""
    ch, cv, psi = state
    return ch + cv + (p.b2 / p.b1) * psi


def equilibrium(p: Parameters):
    """Published Eq. 34 equilibrium (C_h,C_v,Psi_s)."""
    ch = (p.b1 * p.gamma1 + p.b2) / (p.b1 * (p.b1 * p.epsilon + 1))
    return ch, p.epsilon * p.b1 * ch, 0.0


def _rk4_step(y, step, fun, p):
    k1 = fun(y, p)
    y2 = tuple(y[j] + step * k1[j] / 2 for j in range(len(y)))
    k2 = fun(y2, p)
    y3 = tuple(y[j] + step * k2[j] / 2 for j in range(len(y)))
    k3 = fun(y3, p)
    y4 = tuple(y[j] + step * k3[j] for j in range(len(y)))
    k4 = fun(y4, p)
    return tuple(y[j] + step * (k1[j] + 2*k2[j] + 2*k3[j] + k4[j]) / 6
                 for j in range(len(y)))


def _time_grid(end_time, step):
    if not math.isfinite(end_time) or not math.isfinite(step) or end_time <= 0 or step <= 0:
        raise ValueError("time and step must be finite and positive")
    n = int(round(end_time / step))
    if abs(n * step - end_time) > 1e-12:
        raise ValueError("end time must be an integer number of steps")
    return n


def solve(p: Parameters, end_time=8.0, step=0.0005):
    """Deterministic fixed-step classical RK4 solution."""
    n = _time_grid(end_time, step)
    y = (0.0, p.gamma1, 1.0)
    out = [(0.0, *y)]
    for i in range(n):
        y = _rk4_step(y, step, derivative, p)
        if min(y) < -1e-10 or not all(math.isfinite(x) for x in y):
            raise ArithmeticError("negative or nonfinite numerical state")
        out.append(((i + 1) * step, *y))
    return out


def solve_reduced(p: Parameters, end_time=8.0, step=0.0005):
    """Independent two-state RK4 solution with Psi_s from conservation."""
    n = _time_grid(end_time, step)
    y = (0.0, p.gamma1)
    out = [(0.0, y[0], y[1], 1.0)]
    for i in range(n):
        y = _rk4_step(y, step, reduced_derivative, p)
        psi = 1.0 - (p.b1 / p.b2) * (y[0] + y[1] - p.gamma1)
        if min(*y, psi) < -1e-10 or not all(math.isfinite(x) for x in (*y, psi)):
            raise ArithmeticError("negative or nonfinite reduced state")
        out.append(((i + 1) * step, y[0], y[1], psi))
    return out


def trajectory_refinement(traces):
    """Return aligned three-level L-infinity RK4 diagnostics."""
    if len(traces) != 3:
        raise ValueError("exactly three traces required")
    n0 = len(traces[0])
    if len(traces[1]) != 2*(n0-1)+1 or len(traces[2]) != 4*(n0-1)+1:
        raise ValueError("traces are not nested by factors of two")
    component01 = [0.0, 0.0, 0.0]
    component12 = [0.0, 0.0, 0.0]
    finest_scale = 1.0
    for i, coarse in enumerate(traces[0]):
        middle, fine = traces[1][2*i], traces[2][4*i]
        if coarse[0] != middle[0] or coarse[0] != fine[0]:
            raise ValueError("unaligned trace times")
        for j in range(3):
            component01[j] = max(component01[j], abs(coarse[j+1]-middle[j+1]))
            component12[j] = max(component12[j], abs(middle[j+1]-fine[j+1]))
            finest_scale = max(finest_scale, abs(fine[j+1]))
    d01, d12 = max(component01), max(component12)
    floor = 4096.0 * math.ulp(finest_scale)
    ratio = d12/d01
    return {
        "D_01": d01, "D_12": d12, "refinement_ratio": ratio,
        "observed_order": math.log(d01/d12, 2.0),
        "component_D_01": dict(zip(("C_h", "C_v", "Psi_s"), component01)),
        "component_D_12": dict(zip(("C_h", "C_v", "Psi_s"), component12)),
        "trajectory_scale": finest_scale, "roundoff_floor": floor,
    }


def _inner_literal(t, p):
    """Publisher equations 87--89, evaluated in overflow-avoiding form."""
    e, b1, b2, g = p.epsilon, p.b1, p.b2, p.gamma1
    q, q2, q3 = math.exp(-t), math.exp(-2*t), math.exp(-3*t)
    ch0 = 1-q
    ch1 = b1*g*t/b2 + b2*(-q*(t-1)-q2)
    first = -b1*(g*t*t*q+2*(t-1)+2*q)  # literal first denominator b2
    second = (-b1*g*t*t-b2**3*(q*(t-2)*t+q2*(4*t-2)+2*q3))/(2*b2)
    cv = g + e*(-g*t) + e*e*(b2*(t+q-1)+0.5*g*t*t)
    psi = q + e*b2*(q*(t-1)+q2) + 0.5*e*e*(
        b1*g*q*t*t+b2*b2*(q*(t-2)*t+q2*(4*t-2)+2*q3))
    return ch0+e*ch1+e*e*(first+second), cv, psi


def _inner_derived(t, p):
    """Derived governing-ODE-consistent equations 87--89."""
    ch, cv, psi = _inner_literal(t, p)
    q = math.exp(-t)
    # Replace only the literal equation-87 first term by its 2*b2 form.
    literal_first = -p.b1*(p.gamma1*t*t*q+2*(t-1)+2*q)
    derived_first = 0.5*literal_first
    return ch+p.epsilon**2*(derived_first-literal_first), cv, psi


def _outer(tau, p, include_ch2):
    b1, b2, g, e = p.b1, p.b2, p.gamma1, p.epsilon
    q = math.exp(-tau)
    ch0 = b2/b1+g-g*q
    ch1 = q*(b1*g*(tau+1)+b2)-(b1*g+b2)
    ch2 = b1*b1*g+b1*b2-q*(
        0.5*b1*b1*g*(tau*tau+2*tau+2)+b1*b2*(tau+1)-b2)
    cv0 = g*q
    # Equation 46 sign derived from equation 43: +K3 exp(-tau).
    cv1 = b1*g+b2+q*(-b1*g-b2-b1*g*tau)
    k4, k5 = -b1*g-b2, b1*b1*g+b1*b2-b2
    cv2 = b1*q*(0.5*b1*g*tau*tau+(b1*g+b2)*tau)+b1*k4+k5*q
    return ch0+e*ch1+(e*e*ch2 if include_ch2 else 0.0), cv0+e*cv1+e*e*cv2, 0.0


def published_truncated_composite(tau, p: Parameters):
    """Literal publisher equations 87--97; source reproduction only."""
    if not math.isfinite(tau) or tau < 0:
        raise ValueError("time must be finite and nonnegative")
    t, e, b1, b2, g = tau/p.epsilon, p.epsilon, p.b1, p.b2, p.gamma1
    inner = _inner_literal(t, p)
    outer = _outer(tau, p, include_ch2=False)
    common_ch = (b2+e*b1*g*t+e*e*(-b1*b2*t-0.5*b1*g*t*t))/b2
    common_cv = g-e*g*t+e*e*(b2*t-b2+0.5*g*t*t)
    scaled_ch = inner[0]+(b1/b2)*outer[0]-common_ch
    return (b2/b1)*scaled_ch, inner[1]+outer[1]-common_cv, inner[2]


def governing_ode_consistent_second_order_composite(tau, p: Parameters):
    """Derived governing-ODE-consistent second-order matched composite."""
    if not math.isfinite(tau) or tau < 0:
        raise ValueError("time must be finite and nonnegative")
    t, e, b1, b2, g = tau/p.epsilon, p.epsilon, p.b1, p.b2, p.gamma1
    inner = _inner_derived(t, p)
    outer = _outer(tau, p, include_ch2=True)
    common_ch = (b2+e*b1*g*t+e*e*(-b1*b2*t+b1*b2-0.5*b1*g*t*t))/b2
    common_cv = g-e*g*t+e*e*(b2*t-b2+0.5*g*t*t)
    out = ((b2/b1)*(inner[0]+(b1/b2)*outer[0]-common_ch),
           inner[1]+outer[1]-common_cv, inner[2])
    if not all(math.isfinite(x) for x in out):
        raise ArithmeticError("nonfinite composite")
    return out


def outer_time_to_seconds(tau, p: Parameters):
    """Physical-time adapter: seconds = tau * diffusion_time_s."""
    if not math.isfinite(tau) or tau < 0:
        raise ValueError("invalid outer time")
    return tau*p.diffusion_time_s


def inner_time(tau, p: Parameters):
    """Return dimensionless inner time t=tau/epsilon."""
    if not math.isfinite(tau) or tau < 0:
        raise ValueError("invalid outer time")
    return tau/p.epsilon


def zero_flow_reference(case_id, times, step=0.0005):
    """Return structured dimensionless states; accepts no hydraulics."""
    p = {"fine": FINE, "coarse": COARSE}[case_id]
    trace = solve(p, max(times), step)
    lookup = {round(row[0], 12): row[1:] for row in trace}
    return {"case_id": p.case_id,
            "representation": "DIMENSIONLESS_EQUIVALENT_WITH_PHYSICAL_TIME_ADAPTER",
            "states": [{"time": t, "state": lookup[round(t, 12)]} for t in times]}
