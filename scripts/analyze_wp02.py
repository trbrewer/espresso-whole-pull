#!/usr/bin/env python3
"""Frozen WP02-001 multi-pressure analyzer."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import tempfile
from pathlib import Path

SCHEMA_VERSION = "espresso.public.wp02_001_analysis.v2"
AMENDMENT_PATH = "validation/wp02/WP02_001_ANALYZER_ENDPOINT_AMENDMENT.json"
CONTRACT_PATH = "validation/wp02/WP02_001_CLOSURE_CONTRACT.json"
SOURCE_POINT_COUNT = 1000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_protected_identity(path: Path, expected_hash: str) -> None:
    if sha256(path) != expected_hash:
        raise ValueError("protected source identity mismatch")


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


def floating_endpoint_tolerance_s(
    governed_endpoint_s: float,
    observed_endpoint_s: float,
    delta_t_s: float,
) -> float:
    magnitude = max(abs(governed_endpoint_s), abs(observed_endpoint_s), 1.0)
    tolerance = max(1024.0 * math.ulp(magnitude), 1.0e-12)
    if tolerance >= delta_t_s * 1.0e-6:
        raise ValueError(
            "floating endpoint tolerance is not negligible relative to timestep"
        )
    return tolerance


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


def load_prediction(
    trace: Path,
    offset: float,
    density: float,
    governed_endpoint_s: float,
    delta_t_s: float,
) -> tuple[list[float], dict]:
    with trace.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("trace is empty")
    times = [float(row["time_s"]) for row in rows]
    values = [1000.0 * density * float(row["outlet_flow_m3_s"]) for row in rows]
    if not all(math.isfinite(value) for value in times + values):
        raise ValueError("trace contains nonfinite values")
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("trace times not strictly increasing")
    targets = [
        100.0 * index / (SOURCE_POINT_COUNT - 1) + offset
        for index in range(SOURCE_POINT_COUNT)
    ]
    if targets[-1] != governed_endpoint_s:
        raise ValueError("governed mapped endpoint mismatch")
    tolerance = floating_endpoint_tolerance_s(
        governed_endpoint_s, times[-1], delta_t_s
    )
    predicted = []
    reconciled = []
    effective_sample_times = []
    for index, target in enumerate(targets):
        if target <= times[-1]:
            predicted.append(interpolate(times, values, target))
            effective_sample_times.append(target)
            continue
        gap = target - times[-1]
        if (
            index != SOURCE_POINT_COUNT - 1
            or target != governed_endpoint_s
            or gap <= 0.0
            or gap > tolerance
            or reconciled
        ):
            raise ValueError("interpolation target outside trace")
        predicted.append(values[-1])
        effective_sample_times.append(times[-1])
        reconciled.append(index)
    if len(reconciled) > 1:
        raise ValueError("more than one endpoint reconciliation")
    applied = bool(reconciled)
    gap = governed_endpoint_s - times[-1] if applied else 0.0
    audit = {
        "status": "APPLIED" if applied else "NOT_REQUIRED",
        "kind": "FLOATING_POINT_REPRESENTATION_ONLY",
        "reconciled_point_count": len(reconciled),
        "source_index": reconciled[0] if applied else None,
        "governed_mapped_time_s": governed_endpoint_s,
        "observed_trace_endpoint_s": times[-1],
        "absolute_gap_s": gap,
        "tolerance_s": tolerance,
        "frozen_timestep_s": delta_t_s,
        "gap_as_fraction_of_timestep": gap / delta_t_s,
        "effective_solver_sample_time_s": (
            effective_sample_times[-1] if applied else governed_endpoint_s
        ),
        "interpolation_extrapolation_performed": False,
        "scientific_time_mapping_changed": False,
        "trace_modified": False,
    }
    return predicted, audit


def validate_scenario(
    root: Path,
    contract: dict,
    amendment: dict,
    name: str,
    trace: Path,
) -> tuple[dict, str]:
    scenario_path = contract[name]["scenario_path"]
    scenario_file = root / scenario_path
    scenario_hash = sha256(scenario_file)
    expected = amendment["scenario_configurations"][name]
    if scenario_hash != expected["sha256"]:
        raise ValueError(f"{name} scenario identity mismatch")
    if sha256(trace) != amendment["retained_traces"][name]["sha256"]:
        raise ValueError(f"{name} trace identity mismatch")
    scenario = json.loads(scenario_file.read_text())
    validate_time_contract(scenario, contract, name)
    return scenario, scenario_hash


def validate_time_contract(scenario: dict, contract: dict, name: str) -> None:
    time = scenario["time"]
    if time["end_s"] != 103.0 or time["delta_t_s"] != 0.02:
        raise ValueError(f"{name} frozen time contract mismatch")
    scenario_offset = scenario["effective_permeability_evolution"][
        "source_to_solver_offset_s"
    ]
    if scenario_offset != contract["time_mapping"]["source_to_solver_offset_s"]:
        raise ValueError(f"{name} scenario offset mismatch")
    if 100.0 + scenario_offset != time["end_s"]:
        raise ValueError(f"{name} final mapped endpoint mismatch")


def atomic_write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


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
    contract_path = root / CONTRACT_PATH
    amendment_path = root / AMENDMENT_PATH
    contract = json.loads(contract_path.read_text())
    amendment = json.loads(amendment_path.read_text())
    source_path, expected_hash = contract["source_dependency"]["files"]["per_brew_traces"]
    source = args.puckworks / source_path
    try:
        verify_protected_identity(source, expected_hash)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    scenario_inputs = {}
    for name, trace in (
        ("nine_bar_reconstruction", args.nine_trace),
        ("eight_bar_transfer", args.eight_trace),
    ):
        scenario_inputs[name] = validate_scenario(
            root, contract, amendment, name, trace
        )
    output = {
        "schema_version": SCHEMA_VERSION,
        "task": "WP02-001",
        "analysis_identity": {
            "analyzer_sha256": sha256(Path(__file__)),
            "amendment_record_path": AMENDMENT_PATH,
            "amendment_record_sha256": sha256(amendment_path),
            "closure_contract_sha256": sha256(contract_path),
            "protected_source_sha256": expected_hash,
            "protected_analysis_invocation_count": 1,
            "failed_pre_score_analyzer_invocations": 1,
            "completed_score_bearing_analysis_invocations": 1,
        },
        "scenarios": {},
    }
    for name, trace in (("nine_bar_reconstruction", args.nine_trace), ("eight_bar_transfer", args.eight_trace)):
        cfg = contract[name]
        scenario, scenario_hash = scenario_inputs[name]
        predicted, endpoint_audit = load_prediction(
            trace,
            contract["time_mapping"]["source_to_solver_offset_s"],
            965.0,
            scenario["time"]["end_s"],
            scenario["time"]["delta_t_s"],
        )
        observed = load_source(source, cfg["reference_pressure_bin_bar"], cfg["shot_ids"])
        shot_scores = [{"shot_id": shot, **score(predicted, observed[shot], contract)} for shot in cfg["shot_ids"]]
        output["scenarios"][name] = {
            "trace_sha256": sha256(trace),
            "scenario_configuration_sha256": scenario_hash,
            "floating_endpoint_reconciliation": endpoint_audit,
            "shot_scores": shot_scores,
            "aggregate": aggregate(shot_scores, cfg["gates"]),
        }
    atomic_write_json(args.output, output)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
