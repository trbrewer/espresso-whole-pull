"""Liang 2021 rate transformation and deterministic synthetic identifiability."""
import math
import random


def rates_from_K_tau(K, tau):
    """Return k_D,k_A in s^-1 from dimensionless K and tau in seconds."""
    if not math.isfinite(K) or not 0 <= K <= 1:
        raise ValueError("K must be finite in [0,1]")
    if not math.isfinite(tau) or tau <= 0:
        raise ValueError("tau must be finite and positive")
    return K / tau, (1.0 - K) / tau


def K_tau_from_rates(k_d, k_a):
    """Return dimensionless K and tau in seconds from rates in s^-1."""
    if not all(math.isfinite(x) and x >= 0 for x in (k_d, k_a)) or k_d + k_a <= 0:
        raise ValueError("rates must be finite, nonnegative, and not both zero")
    return k_d / (k_d + k_a), 1.0 / (k_d + k_a)


def transient(time_s, K, tau_s, amplitude=1.0):
    """Synthetic measured fraction, dimensionless."""
    if not math.isfinite(time_s) or time_s < 0 or not math.isfinite(amplitude) or amplitude < 0:
        raise ValueError("invalid transient input")
    rates_from_K_tau(K, tau_s)
    return amplitude * K * (-math.expm1(-time_s / tau_s))


def synthetic(K, tau_s, times_s, amplitude, noise_sigma, seed):
    """Generate deterministic synthetic observations only."""
    if noise_sigma < 0 or not math.isfinite(noise_sigma):
        raise ValueError("invalid noise")
    rng = random.Random(seed)
    return [transient(t, K, tau_s, amplitude) + rng.gauss(0, noise_sigma)
            for t in times_s]


def estimate(times_s, observations, amplitude=1.0):
    """Deterministic bounded grid estimator for synthetic tests."""
    if len(times_s) != len(observations) or len(times_s) < 3:
        raise ValueError("inadequate time support")
    if len(set(times_s)) < 3 or max(observations) - min(observations) <= 1e-15:
        raise ValueError("singular information")
    best = None
    for i in range(1, 4001):
        tau = 0.05 * (2000.0 ** (i / 4000.0))
        basis = [-math.expm1(-t / tau) for t in times_s]
        den = sum(x*x for x in basis)
        K = sum(y*x for x, y in zip(basis, observations)) / (amplitude * den)
        if not 0 <= K <= 1:
            continue
        error = sum((y - amplitude*K*x)**2 for x, y in zip(basis, observations))
        if best is None or error < best[0]:
            best = (error, K, tau)
    if best is None:
        raise ValueError("no admissible estimate")
    return {"K": best[1], "tau_s": best[2], "sse": best[0]}


FIT_STATUS = "PROHIBITED_UNTIL_GOVERNED_DIGITIZATION_EXISTS"


def endpoint_identifiability(K, tau_values, transient_times_s, amplitude=1.0):
    """Generate the endpoint/transient identifiability conclusion."""
    if len(tau_values) < 2 or len(set(tau_values)) != len(tau_values):
        raise ValueError("at least two distinct tau values required")
    for tau in tau_values:
        rates_from_K_tau(K, tau)
    endpoints = [amplitude*K for _ in tau_values]
    transient_rows = [[transient(t, K, tau, amplitude) for t in transient_times_s]
                      for tau in tau_values]
    endpoint_objective = [sum((x-endpoints[0])**2 for x in [endpoint])
                          for endpoint in endpoints]
    transient_objective = [
        sum((x-y)**2 for x, y in zip(row, transient_rows[0]))
        for row in transient_rows
    ]
    return {
        "tau_values_s": list(tau_values),
        "analytic_infinite_time_endpoints": endpoints,
        "endpoint_objective": endpoint_objective,
        "transient_objective": transient_objective,
        "endpoint_only_tau_identifiable": len(set(endpoint_objective)) > 1,
        "transient_tau_information_demonstrated": any(x > 0 for x in transient_objective[1:]),
        "fit_status": FIT_STATUS,
    }
