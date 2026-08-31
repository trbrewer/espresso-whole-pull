"""Research-only grouped Waszkiewicz hydraulic comparison primitives."""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

A, B, C = 0.017184292098914252, 0.03670858658698296, 0.2831597837775055
DT = 100.0 / 999.0
ALIAS = "12-8-6_alt"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


@dataclass(frozen=True)
class PhysicalFlowResult:
    flow_value: np.ndarray
    validity: np.ndarray
    invalid_reason: np.ndarray


def physical_flow_result(line_pressure, resistance, *, a=A, b=B, c=C):
    """Typed, fail-closed physical root result; invalidity is never zero-filled."""
    p = np.asarray(line_pressure, float)
    r = np.asarray(resistance, float)
    out = np.full(np.broadcast(p, r).shape, np.nan)
    pp, rr = np.broadcast_arrays(p, r)
    linear = abs(a) < 1e-12
    reason = np.full(pp.shape, "", dtype=object)
    reason[~np.isfinite(rr)] = "NONFINITE_RESISTANCE"
    reason[np.isfinite(rr) & (rr <= 0)] = "NONPOSITIVE_RESISTANCE"
    reason[np.isfinite(rr) & (rr > 0) & ~np.isfinite(pp)] = "OUT_OF_DOMAIN"
    reason[np.isfinite(rr) & (rr > 0) & np.isfinite(pp) & (pp <= c)] = "LINE_PRESSURE_BELOW_BREWER_OFFSET"
    valid = reason == ""
    if linear:
        den = b + rr
        ok = valid & (den > 1e-12)
        out[ok] = (pp[ok] - c) / den[ok]
        reason[valid & ~ok] = "NUMERICAL_FAILURE"
        return PhysicalFlowResult(out, np.isfinite(out), reason)
    disc = (b + rr) ** 2 + 4.0 * a * (pp - c)
    reason[valid & (disc < 0)] = "NEGATIVE_DISCRIMINANT"
    ok = valid & (disc >= 0)
    out[ok] = 2.0 * (pp[ok] - c) / ((b + rr[ok]) + np.sqrt(disc[ok]))
    reason[ok & ~np.isfinite(out)] = "NONFINITE_ROOT"
    reason[ok & np.isfinite(out) & (out < 0)] = "NEGATIVE_ROOT"
    out[(out < 0) | ~np.isfinite(out)] = np.nan
    return PhysicalFlowResult(out, np.isfinite(out), reason)


def physical_flow(line_pressure, resistance, *, a=A, b=B, c=C):
    """Compatibility wrapper returning values while retaining visible NaNs."""
    return physical_flow_result(line_pressure, resistance, a=a, b=b, c=c).flow_value


def integrate_increment(flow, dt=DT):
    q = np.asarray(flow, float)
    out = np.zeros_like(q)
    if len(q) > 1:
        out[1:] = np.cumsum(0.5 * (q[1:] + q[:-1]) * dt)
    return out


def fit_linear(features, target, ridge=1e-6):
    x = np.asarray(features, float)
    y = np.asarray(target, float)
    ok = np.all(np.isfinite(x), axis=1) & np.isfinite(y)
    x, y = x[ok], y[ok]
    return np.linalg.solve(x.T @ x + ridge * np.eye(x.shape[1]), x.T @ y)


def apparent_log_r(line, flow):
    p, q = np.asarray(line, float), np.asarray(flow, float)
    bed = p - (A*q*q + B*q + C)
    out = np.full_like(q, np.nan)
    ok = (q > 0.03) & (bed > 0)
    out[ok] = np.log(bed[ok] / q[ok])
    return out


def predict(model, beta, line, time, *, delay=0.0, progress_scale=None):
    t = np.asarray(time, float)
    p = np.asarray(line, float)
    if delay:
        p = np.interp(t-delay, t, p, left=p[0], right=p[-1])
    base = beta[0] + beta[1] * np.log(np.maximum(p, 0.4))
    if model == "W-H0A" or model == "W-H5":
        logr = base
        q = physical_flow(p, np.exp(logr))
        return q, integrate_increment(q)
    if model == "W-H1":
        amp, tau = beta[2], beta[3]
        logr = base + amp*np.exp(-(t-t[0])/tau)
        q = physical_flow(p, np.exp(logr))
        return q, integrate_increment(q)
    if model == "W-H3":
        amp, tc, width = beta[2], beta[3], beta[4]
        logr = base + amp/(1.0 + np.exp(np.clip((t-tc)/width, -50, 50)))
        q = physical_flow(p, np.exp(logr))
        return q, integrate_increment(q)
    if model == "W-H2":
        amp, mc = beta[2], beta[3]
        q = np.zeros_like(t); mass = np.zeros_like(t)
        for i in range(len(t)):
            logr = base[i] + amp*math.exp(-mass[i]/mc)
            q[i] = physical_flow(np.array([p[i]]), np.array([math.exp(logr)]))[0]
            if not np.isfinite(q[i]):
                mass[i:] = np.nan
                break
            if i+1 < len(t): mass[i+1] = mass[i] + q[i]*DT
        return q, mass
    raise ValueError(model)


def condition_balanced(rows, model):
    by = {}
    for r in rows:
        if r["model_id"] == model:
            by.setdefault(r["condition_id"], []).append(float(r["nrmse"]))
    return float(np.mean([np.mean(v) for v in by.values()]))


def validate_fold(training_brew_ids, held_brew_ids, training_conditions, held_conditions):
    """Reject physical-brew or controlled-condition leakage."""
    if set(training_brew_ids) & set(held_brew_ids):
        raise ValueError("HELD_OUT_BREW_IN_TRAINING")
    if set(training_conditions) & set(held_conditions):
        raise ValueError("HELD_OUT_CONDITION_IN_TRAINING")
    return True


def validate_blocked_state(model, modeled_progress_at_split, reset_requested=False):
    """Reject state reset for evolving models at the blocked-time split."""
    if model in {"W-H1", "W-H2", "W-H3"} and (reset_requested or not np.isfinite(modeled_progress_at_split)):
        raise ValueError("DYNAMIC_STATE_RESET_AT_BLOCKED_TIME_SPLIT")
    return True
