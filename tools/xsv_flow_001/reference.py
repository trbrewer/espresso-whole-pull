"""Independent standard-library oracles for XSV-FLOW-001."""
from __future__ import annotations
import math


def schedule_value(times: list[float], flows: list[float], time_s: float) -> float:
    if len(times) < 2 or len(times) != len(flows):
        raise ValueError("invalid schedule length")
    if any(not math.isfinite(x) for x in times + flows):
        raise ValueError("nonfinite schedule")
    if any(b <= a for a, b in zip(times, times[1:])) or any(x < 0 for x in flows):
        raise ValueError("invalid schedule order or flow")
    endpoint_tolerance=1e-12*max(1.0,abs(times[0]),abs(times[-1]))
    if time_s < times[0]-endpoint_tolerance or time_s > times[-1]+endpoint_tolerance:
        raise ValueError("schedule does not cover time")
    if abs(time_s-times[0]) <= endpoint_tolerance:
        return flows[0]
    if abs(time_s-times[-1]) <= endpoint_tolerance:
        return flows[-1]
    for i, knot in enumerate(times):
        if time_s == knot:
            return flows[i]
        if time_s < knot:
            f = (time_s-times[i-1])/(knot-times[i-1])
            return flows[i-1]+f*(flows[i]-flows[i-1])
    return flows[-1]


def uniform_pressure_drop(mu: float, depth: float, flow: float,
                          area: float, permeability: float) -> float:
    return mu*depth*flow/(area*permeability)


def layered_pressure_drop(mu: float, flow: float, area: float,
                          lengths: tuple[float, float],
                          permeabilities: tuple[float, float]) -> float:
    return mu*flow/area*sum(length/k for length, k in zip(lengths, permeabilities))


def discrete_volume(sample_times: list[float], widths: list[float],
                    target) -> float:
    if len(sample_times) != len(widths):
        raise ValueError("sample/width mismatch")
    return sum(target(time)*width for time, width in zip(sample_times, widths))
