"""Moroney 2017 dimensionless zero-flow three-state reference.

Time is dimensionless outer time; concentrations and inventory are
dimensionless. This is code verification, not espresso extraction physics.
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
    """Return d(C_h,C_v,Psi_s)/d(t/t_d), all dimensionless."""
    ch, cv, psi = state
    if not all(math.isfinite(x) for x in state) or min(state) < -1e-12:
        raise ValueError("invalid or materially negative state")
    e, b1, b2 = p.epsilon, p.b1, p.b2
    return (
        -b2 * ch * psi + (b2 / b1) * psi / e - e * b1 * ch + cv,
        e * b1 * ch - cv,
        b1 * ch * psi - psi / e,
    )


def inventory(state, p: Parameters):
    """Dimensionless conserved total C_h+C_v+(b2/b1)Psi_s."""
    ch, cv, psi = state
    return ch + cv + (p.b2 / p.b1) * psi


def equilibrium(p: Parameters):
    """Published Eq. 34 equilibrium (C_h,C_v,Psi_s)."""
    ch = (p.b1 * p.gamma1 + p.b2) / (p.b1 * (p.b1 * p.epsilon + 1))
    return ch, p.epsilon * p.b1 * ch, 0.0


def solve(p: Parameters, end_time=8.0, step=0.0005):
    """Deterministic fixed-step RK4 solution on dimensionless outer time."""
    if not math.isfinite(end_time) or not math.isfinite(step) or end_time <= 0 or step <= 0:
        raise ValueError("time and step must be finite and positive")
    n = int(round(end_time / step))
    if abs(n * step - end_time) > 1e-12:
        raise ValueError("end time must be an integer number of steps")
    y = (0.0, p.gamma1, 1.0)
    out = [(0.0, *y)]
    for i in range(n):
        k1 = derivative(y, p)
        y2 = tuple(y[j] + step * k1[j] / 2 for j in range(3))
        k2 = derivative(y2, p)
        y3 = tuple(y[j] + step * k2[j] / 2 for j in range(3))
        k3 = derivative(y3, p)
        y4 = tuple(y[j] + step * k3[j] for j in range(3))
        k4 = derivative(y4, p)
        y = tuple(y[j] + step * (k1[j] + 2*k2[j] + 2*k3[j] + k4[j]) / 6
                  for j in range(3))
        if min(y) < -1e-10 or not all(math.isfinite(x) for x in y):
            raise ArithmeticError("negative or nonfinite numerical state")
        out.append(((i + 1) * step, *y))
    return out


def composite_surrogate(time, p: Parameters):
    """Separate two-timescale matched-composite surrogate.

    It uses the source fast and slow scales and exact equilibrium/inventory,
    independently of the RK4 state update.
    """
    if not math.isfinite(time) or time < 0:
        raise ValueError("time must be finite and nonnegative")
    eq = equilibrium(p)
    fast = math.exp(-time / p.epsilon)
    slow = math.exp(-time)
    psi = fast
    cv = eq[1] + (p.gamma1 - eq[1]) * slow
    ch = inventory((0.0, p.gamma1, 1.0), p) - cv - (p.b2/p.b1)*psi
    return ch, cv, psi


def zero_flow_reference(case_id, times, step=0.0005):
    """Return structured zero-flow states; accepts no hydraulic parameters."""
    p = {"fine": FINE, "coarse": COARSE}[case_id]
    end = max(times)
    trace = solve(p, end, step)
    lookup = {round(row[0], 12): row[1:] for row in trace}
    return {"case_id": p.case_id, "units": "dimensionless", "states":
            [{"time": t, "state": lookup[round(t, 12)]} for t in times]}
