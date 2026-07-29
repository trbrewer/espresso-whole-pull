#!/usr/bin/env python3
"""Frozen WP02-001 multi-pressure analyzer."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interpolate(times: list[float], values: list[float], target: float) -> float:
    if target < times[0] or target > times[-1]:
        raise ValueError("interpolation target outside trace")
    lo, hi = 0, len(times) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if times[mid] <= target:
            lo = mid
        else:
            hi = mid
    if target == times[lo]:
        return values[lo]
    if target == times[hi]:
        return values[hi]
    fraction = (target - times[lo]) / (times[hi] - times[lo])
    return values[lo] + fraction * (values[hi] - values[lo])


def pearson(a: list[float], b: list[float], epsilon: float) -> tuple[bool, float | None]:
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    sa = math.sqrt(statistics.fmean((x - ma) ** 2 for x in a))
    sb = math.sqrt(statistics.fmean((x - mb) ** 2 for x in b))
    if sa <= epsilon or sb <= epsilon:
        return False, None
    covariance = statistics.fmean((x - ma) * (y - mb) for x, y in zip(a, b))
    return True, covariance / (sa * sb)


def score(predicted: list[float], observed: list[float], contract: dict) -> dict:
    common = contract["comparison_common"]
    p0, p1 = common["protected_indices"]
    n0, n1 = common["normalization_indices"]
    pred_late = statistics.fmean(predicted[n0 : n1 + 1])
    obs_late = statistics.fmean(observed[n0 : n1 + 1])
    pred = [x / pred_late for x in predicted[p0 : p1 + 1]]
    obs = [x / obs_late for x in observed[p0 : p1 + 1]]
    rmse = math.sqrt(statistics.fmean((x - y) ** 2 for x, y in zip(pred, obs)))
    defined, correlation = pearson(pred, obs, common["pearson_epsilon"])
    return {
        "observed_late_mean_g_per_s": obs_late,
        "predicted_late_mean_g_per_s": pred_late,
        "normalized_rmse": rmse,
        "pearson_defined": defined,
        "pearson_r": correlation,
    }


def load_source(path: Path, pressure: float, shots: list[str]) -> dict[str, list[float]]:
    selected = {shot: {} for shot in shots}
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required = {
            "reference_pressure_round__bar",
            "shot_id",
            "time_index",
            "mass_flow_rate__g_per_s",
        }
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("protected source fields missing")
        for row in reader:
            if float(row["reference_pressure_round__bar"]) != pressure:
                continue
            shot = row["shot_id"]
            if shot not in selected:
                raise ValueError(f"unexpected shot {shot}")
            selected[shot][int(row["time_index"])] = float(
                row["mass_flow_rate__g_per_s"]
            )
    result = {}
    for shot, rows in selected.items():
        if sorted(rows) != list(range(1000)):
            raise ValueError(f"invalid source indices for {shot}")
        result[shot] = [rows[index] for index in range(1000)]
    return result


def load_prediction(trace: Path, offset: float, density: float) -> list[float]:
    with trace.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    times = [float(row["time_s"]) for row in rows]
    values = [1000.0 * density * float(row["outlet_flow_m3_s"]) for row in rows]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("trace times not strictly increasing")
    return [
        interpolate(times, values, 100.0 * index / 999.0 + offset)
        for index in range(1000)
    ]


def aggregate(scores: list[dict], gates: dict) -> dict:
    rmses = [item["normalized_rmse"] for item in scores]
    rs = [item["pearson_r"] for item in scores if item["pearson_defined"]]
    return {
        "median_rmse": statistics.median(rmses),
        "rmse_count_pass": sum(x <= gates["shot_rmse_max"] for x in rmses),
        "median_pearson": statistics.median(rs) if len(rs) == len(scores) else None,
        "pearson_count_pass": sum(
            item["pearson_defined"] and item["pearson_r"] >= gates["shot_pearson_min"]
            for item in scores
        ),
        "status": (
            "PASS"
            if statistics.median(rmses) <= gates["median_rmse_max"]
            and sum(x <= gates["shot_rmse_max"] for x in rmses)
            >= gates["shots_required_rmse"]
            and len(rs) == len(scores)
            and statistics.median(rs) >= gates["median_pearson_min"]
            and sum(x >= gates["shot_pearson_min"] for x in rs)
            >= gates["shots_required_pearson"]
            else "FAIL"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--puckworks", type=Path, required=True)
    parser.add_argument("--nine-trace", type=Path, required=True)
    parser.add_argument("--eight-trace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    contract = json.loads(
        (root / "validation/wp02/WP02_001_CLOSURE_CONTRACT.json").read_text()
    )
    source_path, expected_hash = contract["source_dependency"]["files"]["per_brew_traces"]
    source = args.puckworks / source_path
    if sha256(source) != expected_hash:
        raise SystemExit("protected source identity mismatch")
    output = {"schema_version": "espresso.public.wp02_001_analysis.v1", "scenarios": {}}
    for name, trace in (("nine_bar_reconstruction", args.nine_trace), ("eight_bar_transfer", args.eight_trace)):
        cfg = contract[name]
        predicted = load_prediction(trace, contract["time_mapping"]["source_to_solver_offset_s"], 965.0)
        observed = load_source(source, cfg["reference_pressure_bin_bar"], cfg["shot_ids"])
        shot_scores = [{"shot_id": shot, **score(predicted, observed[shot], contract)} for shot in cfg["shot_ids"]]
        output["scenarios"][name] = {
            "trace_sha256": sha256(trace),
            "shot_scores": shot_scores,
            "aggregate": aggregate(shot_scores, cfg["gates"]),
        }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
