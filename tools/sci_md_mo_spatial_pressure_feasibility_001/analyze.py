"""Research-only five-edge slit bridge; equations and bounded protocol in PLAN.md."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.stats import qmc

EDGES = np.array([[0, 1], [1, 3], [0, 2], [2, 3], [1, 2]])
NAMES = ("SA", "AT", "SB", "BT", "AB")
TIMES = np.linspace(0.0, 32.0, 1025)
SEED = 20261021


def hydraulics(x, pressure, independent=False):
    """Dimensionless conductances, node pressures, signed flows, K, Qin, Qout."""
    x = np.asarray(x, dtype=float)
    if x.shape != (5,) or not np.all(np.isfinite(x)) or np.any(x <= 0):
        raise ValueError("invalid aperture")
    if not np.isfinite(pressure) or pressure <= 0:
        raise ValueError("invalid pressure")
    g = x**3
    a, b, c, d, e = g
    if independent:
        # Assemble the full graph Laplacian rather than reuse the 2x2 formula.
        lap = np.zeros((4, 4))
        for (u, v), ge in zip(EDGES, g):
            lap[u, u] += ge
            lap[v, v] += ge
            lap[u, v] -= ge
            lap[v, u] -= ge
        interior = np.linalg.solve(lap[1:3, 1:3], -lap[1:3, 0] * pressure)
        p = np.array([pressure, *interior, 0.0])
    else:
        aa, bb = a + b + e, c + d + e
        # Expanded determinant avoids subtraction of two large e^2 terms.
        det = (a + b) * (c + d) + e * (a + b + c + d)
        p = pressure * np.array([1.0, (a * bb + e * c) / det,
                                 (c * aa + e * a) / det, 0.0])
    dp = p[EDGES[:, 0]] - p[EDGES[:, 1]]
    q = g * dp
    qi, qo = q[0] + q[2], q[1] + q[3]
    return {"g": g, "p": p, "dp": dp, "q": q, "K": qi / pressure,
            "Qin": qi, "Qout": qo}


def positive_linear_mean(left, right):
    """Exact integral of max(linear endpoint interpolation, 0) on [0,1]."""
    low = np.minimum(left, right).astype(float)
    high = np.maximum(left, right).astype(float)
    out = np.zeros_like(low)
    full = low >= 0
    out[full] = 0.5 * (low[full] + high[full])
    part = (low < 0) & (high > 0)
    out[part] = high[part] ** 2 / (2 * (high[part] - low[part]))
    return out


def erosion(x, pressure, gamma, beta, independent=False):
    h = hydraulics(x, pressure, independent)
    shear = x * np.abs(h["dp"])
    ends = shear[:, None] - gamma - beta * h["p"][EDGES]
    if not independent:
        return positive_linear_mean(ends[:, 0], ends[:, 1])
    # Independent root-split midpoint integration: exact for a linear integrand
    # on each active subinterval; no reuse of the triangular-area formula.
    values = []
    for left, right in ends:
        cuts = [0.0, 1.0]
        if left * right < 0:
            cuts.insert(1, float(left / (left - right)))
        value = 0.0
        for lo, hi in zip(cuts[:-1], cuts[1:]):
            mid = (lo + hi) / 2
            value += (hi - lo) * max(0.0, left + mid * (right - left))
        values.append(value)
    return np.array(values)


def aperture(z, x0):
    return np.asarray(x0) - (2 - np.asarray(x0)) * np.expm1(-np.asarray(z))


def aperture_rate(x, x0, pressure, gamma, beta):
    return (2 - x) / (2 - np.asarray(x0)) * erosion(x, pressure, gamma, beta)


def integrate(candidate, pressure, method="DOP853", rtol=1e-8, atol=1e-10,
              max_step=0.25, independent=False, times=TIMES):
    x0 = np.array(candidate["x0"])
    gamma, beta = candidate["gamma"], candidate["beta"]
    evaluations = 0

    def rhs(_, z):
        nonlocal evaluations
        evaluations += 1
        if evaluations > 100000:
            raise RuntimeError("RHS evaluation budget exhausted")
        x = aperture(z, x0)
        if np.any(x <= 0) or np.any(x > 2 + 1e-12):
            raise ValueError("RHS geometric domain failure")
        return erosion(x, pressure, gamma, beta, independent) / (2 - x0)

    sol = solve_ivp(rhs, (float(times[0]), float(times[-1])), np.zeros(5),
                    method=method, t_eval=times, rtol=rtol, atol=atol,
                    max_step=max_step)
    if not sol.success or sol.y.shape != (5, len(times)):
        raise RuntimeError(sol.message)
    x = aperture(sol.y.T, x0)
    if (not np.all(np.isfinite(x)) or np.min(sol.y) < -1e-10
            or np.min(x - x0) < -1e-10 or np.max(x) > 2
            or np.min(np.diff(x, axis=0)) < -1e-8):
        exc = ValueError("accepted state/inventory/monotonicity failure")
        exc.evaluations = evaluations
        exc.diagnostics = {"min_z": float(np.min(sol.y)),
                           "min_x_minus_x0": float(np.min(x-x0)),
                           "max_x_minus_2": float(np.max(x-2)),
                           "min_dx": float(np.min(np.diff(x, axis=0)))}
        raise exc
    hs = [hydraulics(xx, pressure, independent) for xx in x]
    flow = np.array([h["Qin"] for h in hs])
    if np.min(np.diff(flow)) < -1e-8 * max(flow.max(), 1):
        raise ValueError("individual trajectory discharge decreased")
    residuals = []
    for h in hs:
        q, p, g, dp = h["q"], h["p"], h["g"], h["dp"]
        residuals.append(max(abs(q[0] - q[1] - q[4]),
                             abs(q[2] - q[3] + q[4]),
                             abs(h["Qin"] - h["Qout"]),
                             abs(pressure * h["Qin"] - np.dot(g, dp**2))))
        if np.min(p) < -1e-12 or np.max(p) > pressure + 1e-12:
            raise ValueError("pressure maximum principle failure")
    # Algebraic solid balance in units rho_s epsilon L^3; both wall volumes.
    removed = x - x0
    remaining = (2 - x0) * np.exp(-sol.y.T)
    mass_error = np.max(np.abs(removed + remaining - (2 - x0)))
    return {"x": x, "z": sol.y.T, "Q": flow,
            "evaluations": evaluations, "hydraulic_residual": max(residuals),
            "solid_balance_error": float(mass_error),
            "upper_endpoint_roundoffs": int(np.count_nonzero(x == 2)),
            "min_dQ": float(np.min(np.diff(flow)))}


def candidates():
    for i, u in enumerate(qmc.Sobol(d=8, scramble=True, seed=SEED).random_base2(7)):
        yield {"id": i, "x0": (10 ** (-1 + u[:5])).tolist(),
               "gamma": float(0.01 * 50 ** u[5]), "beta": float(4 * u[6]),
               "pressure_low": 1.0, "pressure_high": float(1.05 + 1.95 * u[7])}


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    rows, best = [], None
    total = 0
    actual_evaluations = 0
    actual_attempts = 0
    for candidate in candidates():
        row = {"id": candidate["id"], **dict(zip(NAMES, candidate["x0"])),
               **{k: v for k, v in candidate.items() if k not in ("id", "x0")}}
        used = 0
        try:
            actual_attempts += 1
            low = integrate(candidate, 1.0)
            used += low["evaluations"]
            actual_attempts += 1
            high = integrate(candidate, candidate["pressure_high"])
            used += high["evaluations"]
            total += used
            ratio = high["Q"] / low["Q"]
            j = int(np.argmin(ratio))
            row.update(status="OK", evaluations=used, min_QH_over_QL=float(ratio[j]),
                       theta_at_min=float(TIMES[j]), QL_at_min=float(low["Q"][j]),
                       QH_at_min=float(high["Q"][j]),
                       max_KL_over_KH=float(candidate["pressure_high"] / ratio[j]),
                       hydraulic_residual=max(low["hydraulic_residual"], high["hydraulic_residual"]),
                       solid_balance_error=max(low["solid_balance_error"], high["solid_balance_error"]),
                       min_dQ=min(low["min_dQ"], high["min_dQ"]),
                       upper_endpoint_roundoffs=low["upper_endpoint_roundoffs"] + high["upper_endpoint_roundoffs"])
            if best is None or ratio[j] < best["minimum_ratio"]:
                best = {"candidate": candidate, "minimum_ratio": float(ratio[j]),
                        "theta": float(TIMES[j]), "index": j}
            active = ratio < 1 - 1e-5
            if np.any(active[:-2] & active[1:-1] & active[2:]):
                # Freeze before any verification; caller must complete witness
                # assurance and explicitly resume only if that witness is invalid.
                (output / "FROZEN_CANDIDATE.json").write_text(json.dumps(candidate, indent=2) + "\n")
                row["status"] = "PRELIMINARY_WITNESS_REQUIRES_VERIFICATION"
                actual_evaluations += used
                row["actual_rhs_evaluations_or_upper_charge"] = used
                rows.append(row)
                break
        except (ValueError, RuntimeError, FloatingPointError) as exc:
            # A failed attempt consumes its full allowed budget conservatively.
            total += 200000
            used += getattr(exc, "evaluations", 100000)
            row.update(status="FAILED", evaluations=200000, failure=str(exc))
            row.update(getattr(exc, "diagnostics", {}))
        actual_evaluations += used
        row["actual_rhs_evaluations_or_upper_charge"] = used
        rows.append(row)
        if total >= 5000000:
            break
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (output / "CANDIDATES.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary = {"seed": SEED, "candidate_count": len(rows),
               "exploratory_trajectory_attempts": actual_attempts,
               "actual_rhs_evaluations_or_upper_charge": actual_evaluations,
               "failures": sum(r["status"] == "FAILED" for r in rows),
               "rhs_evaluations_or_conservative_failure_charge": total,
               "preliminary_witnesses": sum(r["status"].startswith("PRELIMINARY") for r in rows),
               "closest": best,
               "maximum_hydraulic_residual": max(r.get("hydraulic_residual", 0) for r in rows),
               "maximum_solid_balance_error": max(r.get("solid_balance_error", 0) for r in rows),
               "minimum_individual_dQ": min(r.get("min_dQ", 0) for r in rows),
               "upper_endpoint_roundoffs": sum(r.get("upper_endpoint_roundoffs", 0) for r in rows)}
    (output / "SEARCH.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output)
