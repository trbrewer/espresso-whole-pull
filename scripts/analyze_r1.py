#!/usr/bin/env python3
"""Frozen WP01R-005 numerical and protected analysis."""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
from pathlib import Path

REQUIRED_TRACE = {
    "time_s", "outlet_flow_m3_s", "cup_beverage_mass_kg", "min_saturation",
    "max_saturation", "min_concentration_kg_m3", "max_concentration_kg_m3",
    "liquid_balance_residual_kg", "solute_balance_residual_kg",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def interpolate(times: list[float], values: list[float], target: float) -> float:
    if target < times[0] or target > times[-1]:
        raise ValueError("interpolation target outside solver trace")
    index = bisect.bisect_left(times, target)
    if index < len(times) and times[index] == target:
        return values[index]
    if index == 0 or index == len(times):
        raise ValueError("interpolation would extrapolate")
    fraction = (target - times[index - 1]) / (times[index] - times[index - 1])
    return values[index - 1] + fraction * (values[index] - values[index - 1])


def pearson(a: list[float], b: list[float], epsilon: float) -> tuple[float | None, bool]:
    if not all(math.isfinite(value) for value in a + b):
        return None, False
    mean_a, mean_b = statistics.mean(a), statistics.mean(b)
    std_a, std_b = statistics.pstdev(a), statistics.pstdev(b)
    if std_a <= epsilon or std_b <= epsilon:
        return None, False
    covariance = statistics.mean((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    return covariance / (std_a * std_b), True


def governed_shot_gate(gates: dict, prefix: str) -> tuple[int, float, str]:
    matches = [key for key in gates if key.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one governed shot gate with prefix {prefix!r}")
    key = matches[0]
    suffix = key[len(prefix):]
    if not re.fullmatch(r"\d+(?:_\d+)?", suffix):
        raise ValueError(f"invalid governed threshold suffix in {key!r}")
    return int(gates[key]), float(suffix.replace("_", ".")), key


def aggregate(shots: list[dict], gates: dict) -> dict:
    rmse_required, rmse_threshold, rmse_key = governed_shot_gate(
        gates, "shots_required_at_or_below_rmse_"
    )
    r_required, r_threshold, r_key = governed_shot_gate(
        gates, "shots_required_at_or_above_r_"
    )
    median_rmse = statistics.median(item["normalized_shape_rmse"] for item in shots)
    defined = [item["pearson_r"] for item in shots if item["pearson_defined"]]
    median_r = statistics.median(defined) if len(defined) == len(shots) else None
    rmse_count = sum(item["normalized_shape_rmse"] <= rmse_threshold for item in shots)
    r_count = sum(
        item["pearson_defined"] and item["pearson_r"] >= r_threshold for item in shots
    )
    passed = (
        median_rmse <= gates["median_normalized_shape_rmse_max"]
        and rmse_count >= rmse_required
        and median_r is not None and median_r >= gates["median_pearson_r_min"]
        and r_count >= r_required
    )
    return {
        "median_normalized_shape_rmse": median_rmse,
        "median_pearson_r": median_r,
        "shots_at_or_below_rmse_0_20": rmse_count,
        "shots_at_or_above_pearson_0_90": r_count,
        "shot_thresholds": {
            "rmse": {"contract_key": rmse_key, "value": rmse_threshold, "required": rmse_required},
            "pearson": {"contract_key": r_key, "value": r_threshold, "required": r_required},
        },
        "status": "PASS" if passed else "FAIL",
    }


def authorities(root: Path) -> tuple[dict, dict, dict]:
    contract = read_json(root / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json")
    scenario = read_json(root / "config/reconstruction_R1_waszkiewicz_9bar.json")
    lock = read_json(root / "dependencies/puckworks.lock.json")
    if contract["contract_status"] != "FROZEN_FOR_WP01R_004":
        raise ValueError("contract is not frozen")
    if lock["checkout_commit"] != contract["source_dependency"]["commit"]:
        raise ValueError("locked commit differs from contract")
    if lock["checkout_tree_sha"] != contract["source_dependency"]["tree"]:
        raise ValueError("locked tree differs from contract")
    if scenario["source_time_mapping"]["source_fixed_8s_offset_used"]:
        raise ValueError("source 8 s offset entered solver mapping")
    return contract, scenario, lock


def trace_rows(path: Path, scenario: dict) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or not REQUIRED_TRACE.issubset(reader.fieldnames):
            raise ValueError("solver trace header is incomplete")
        rows = [{key: float(value) for key, value in row.items()} for row in reader]
    times = [row["time_s"] for row in rows]
    if not all(math.isfinite(value) for row in rows for value in row.values()):
        raise ValueError("solver trace contains nonfinite value")
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("solver trace times are not strictly increasing")
    cadence = max(b - a for a, b in zip(times, times[1:]))
    if cadence > scenario["time"]["reduced_trace_maximum_interval_s"] + 1e-9:
        raise ValueError("solver trace cadence exceeds governed maximum")
    if abs(times[-1] - scenario["time"]["end_s"]) > 1.01 * scenario["time"]["delta_t_s"]:
        raise ValueError("solver trace did not reach governed endpoint")
    return rows


def source_grid(contract: dict) -> list[float]:
    mapping = contract["time_mapping_contract"]
    protected = contract["protected_comparison_contract"]
    count = protected["normalization_indices"]["last"] + 1
    if count != 1000:
        raise ValueError("governed protected sample count is not 1000")
    source_end = mapping["solver_end_time_s"] - mapping["source_to_solver_offset_s"]
    if source_end != 100.0:
        raise ValueError("governed source support is not 0..100 s")
    grid = [index * source_end / (count - 1) for index in range(count)]
    for window, indices in (
        (mapping["protected_source_window"], protected["protected_indices"]),
        (mapping["late_normalization_window"], protected["normalization_indices"]),
    ):
        observed = [grid[indices["first"]], grid[indices["last"]]]
        if any(abs(a - b) > 5e-6 for a, b in zip(observed, window["source_time_s"])):
            raise ValueError("derived source grid disagrees with frozen window endpoints")
    return grid


def calibration_tolerance(contract: dict) -> float:
    gates = [
        item["gate"]
        for item in contract["acceptance_gates"]
        if item["status_family"] == "CALIBRATION_REPRODUCTION"
        and "late-window mean" in item["gate"]
    ]
    if len(gates) != 1:
        raise ValueError("expected one late-flow calibration acceptance gate")
    match = re.search(r"within\s+([0-9]+(?:\.[0-9]+)?)%\s+relative", gates[0])
    if not match:
        raise ValueError("calibration tolerance missing from governed gate")
    return float(match.group(1)) / 100.0


def predicted_trace(contract: dict, rows: list[dict[str, float]]) -> dict:
    times = [row["time_s"] for row in rows]
    density = contract["solver_to_source_flow_mapping"]["primary_predicted_quantity"][
        "liquid_density_kg_m3"
    ]
    flow = [1000.0 * density * row["outlet_flow_m3_s"] for row in rows]
    grid = source_grid(contract)
    offset = contract["time_mapping_contract"]["source_to_solver_offset_s"]
    mapped = [time + offset for time in grid]
    predicted = [interpolate(times, flow, time) for time in mapped]
    late = contract["protected_comparison_contract"]["normalization_indices"]
    late_mean = statistics.mean(predicted[late["first"]:late["last"] + 1])
    return {
        "source_grid": grid,
        "mapped": mapped,
        "predicted": predicted,
        "density": density,
        "late_mean": late_mean,
    }


def numerical_stage(root: Path, trace: Path, acceptance: Path, case_manifest: Path, output: Path) -> None:
    contract, scenario, lock = authorities(root)
    rows = trace_rows(trace, scenario)
    accepted = read_json(acceptance)
    manifest = read_json(case_manifest)
    gates = accepted["numerical_acceptance_gates"]
    parity = accepted["openfoam_b0_parity_gates"]
    numerical_pass = all(item["status"] == "PASS" for item in gates.values()) and all(
        item["status"] == "PASS" for item in parity.values()
    )
    prediction = predicted_trace(contract, rows)
    target = contract["calibration_contract"]["equilibrium_mass_flow_g_per_s"]
    tolerance = calibration_tolerance(contract)
    error = abs(prediction["late_mean"] - target) / target
    calibration_status = "PASS" if error <= tolerance else "FAIL"
    status = numerical_pass and calibration_status == "PASS"
    result = {
        "stage": "NUMERICAL",
        "status": "PASS" if status else "FAIL",
        "trace_sha256": digest(trace),
        "trace_row_count": len(rows),
        "maximum_trace_interval_s": max(
            b["time_s"] - a["time_s"] for a, b in zip(rows, rows[1:])
        ),
        "endpoint_s": rows[-1]["time_s"],
        "acceptance": accepted,
        "case_manifest_sha256": digest(case_manifest),
        "generated_r1_input_aggregate": manifest["r1_scientific_input_aggregate_sha256"],
        "contract_sha256": digest(root / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json"),
        "scenario_sha256": digest(root / "config/reconstruction_R1_waszkiewicz_9bar.json"),
        "lock": {"commit": lock["checkout_commit"], "tree": lock["checkout_tree_sha"]},
        "protected_source_opened": False,
        "calibration_reproduction": {
            "predicted_late_mean_g_per_s": prediction["late_mean"],
            "target_g_per_s": target,
            "relative_error": error,
            "maximum_relative_error": tolerance,
            "status": calibration_status,
            "protected_source_opened": False,
        },
        "protected_release_authorized": status,
    }
    canonical_write(output, result)
    if not status:
        raise SystemExit("numerical release gate failed")


def protected_stage(root: Path, trace: Path, numerical: Path, puckworks: Path, output: Path, reduced: Path) -> None:
    contract, scenario, lock = authorities(root)
    numerical_result = read_json(numerical)
    if (
        numerical_result.get("status") != "PASS"
        or numerical_result.get("calibration_reproduction", {}).get("status") != "PASS"
        or numerical_result.get("protected_release_authorized") is not True
    ):
        raise ValueError("protected analysis forbidden before numerical release")
    if digest(trace) != numerical_result["trace_sha256"]:
        raise ValueError("trace changed after numerical release")
    contract_path = root / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json"
    scenario_path = root / "config/reconstruction_R1_waszkiewicz_9bar.json"
    if digest(contract_path) != numerical_result["contract_sha256"]:
        raise ValueError("contract changed after numerical release")
    if digest(scenario_path) != numerical_result["scenario_sha256"]:
        raise ValueError("scenario changed after numerical release")
    if subprocess.check_output(["git", "-C", str(puckworks), "rev-parse", "HEAD"], text=True).strip() != lock["checkout_commit"]:
        raise ValueError("Puckworks commit mismatch")
    if subprocess.check_output(["git", "-C", str(puckworks), "rev-parse", "HEAD^{tree}"], text=True).strip() != lock["checkout_tree_sha"]:
        raise ValueError("Puckworks tree mismatch")
    protected = contract["protected_comparison_contract"]
    source_info = contract["source_dependency"]["per_brew_trace"]
    if protected["source_path"] != source_info["path"]:
        raise ValueError("protected source paths disagree")
    nodes = [
        item for item in contract["pressure_node_contract"]
        if item.get("node") == "REFERENCE_PRESSURE_BIN"
        and item.get("role") == "SOURCE_GROUPING_LABEL_ONLY"
    ]
    if len(nodes) != 1:
        raise ValueError("expected one governed reference pressure bin")
    selector_match = re.fullmatch(
        r"reference_pressure_round__bar == ([0-9]+(?:\.[0-9]+)?); "
        r"shot_id in protected list; mass_flow_rate__g_per_s",
        protected["source_selector"],
    )
    if not selector_match:
        raise ValueError("protected source selector is malformed")
    reference_pressure = float(selector_match.group(1))
    if reference_pressure != nodes[0]["value_bar"]:
        raise ValueError("protected selector and pressure node disagree")
    source = puckworks / source_info["path"]
    if digest(source) != source_info["sha256"]:
        raise ValueError("protected source hash mismatch")
    rows = trace_rows(trace, scenario)
    with source.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required = {
            "reference_pressure_round__bar", "shot_id", "time_index",
            "mass_flow_rate__g_per_s",
        }
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError("protected source fields are incomplete")
        source_rows = list(reader)
    shots = protected["shot_ids"]
    grouped = {
        shot: [
            row for row in source_rows
            if row["shot_id"] == shot
            and float(row["reference_pressure_round__bar"]) == reference_pressure
        ]
        for shot in shots
    }
    selected_shots = {
        row["shot_id"] for row in source_rows
        if float(row["reference_pressure_round__bar"]) == reference_pressure
    }
    if selected_shots != set(shots):
        raise ValueError("protected shot set mismatch")
    if any(len(values) != 1000 for values in grouped.values()):
        raise ValueError("protected shot row count mismatch")
    grids = [[int(row["time_index"]) for row in grouped[shot]] for shot in shots]
    if any(grid != list(range(1000)) for grid in grids):
        raise ValueError("protected source ordering mismatch")
    prediction = predicted_trace(contract, rows)
    source_times = prediction["source_grid"]
    mapped = prediction["mapped"]
    predicted = prediction["predicted"]
    density = prediction["density"]
    first, last = protected["protected_indices"]["first"], protected["protected_indices"]["last"]
    late_first, late_last = protected["normalization_indices"]["first"], protected["normalization_indices"]["last"]
    pred_late = prediction["late_mean"]
    pred_norm_all = [value / pred_late for value in predicted]
    pred_norm = pred_norm_all[first:last + 1]
    epsilon = protected["pearson_degeneracy"]["normalized_standard_deviation_epsilon"]
    _, rmse_threshold, _ = governed_shot_gate(
        protected["gates"], "shots_required_at_or_below_rmse_"
    )
    _, r_threshold, _ = governed_shot_gate(
        protected["gates"], "shots_required_at_or_above_r_"
    )
    metrics = []
    for shot in shots:
        observed = [float(row["mass_flow_rate__g_per_s"]) for row in grouped[shot]]
        if not all(math.isfinite(value) for value in observed):
            raise ValueError("nonfinite protected observation")
        obs_late = statistics.mean(observed[late_first:late_last + 1])
        obs_norm = [value / obs_late for value in observed[first:last + 1]]
        rmse = math.sqrt(statistics.mean((a - b) ** 2 for a, b in zip(pred_norm, obs_norm)))
        correlation, defined = pearson(pred_norm, obs_norm, epsilon)
        metrics.append({
            "shot_id": shot, "observed_late_mean_g_per_s": obs_late,
            "normalized_shape_rmse": rmse, "pearson_r": correlation,
            "pearson_defined": defined, "predicted_normalized_population_std": statistics.pstdev(pred_norm),
            "observed_normalized_population_std": statistics.pstdev(obs_norm),
            "rmse_status": "PASS" if rmse <= rmse_threshold else "FAIL",
            "pearson_status": "PASS" if defined and correlation >= r_threshold else "FAIL",
        })
    summary = aggregate(metrics, protected["gates"])
    result = {
        "stage": "PROTECTED", "status": "PASS", "shots": metrics, "aggregate": summary,
        "predicted_late_mean_g_per_s": pred_late,
        "calibration_reproduction": numerical_result["calibration_reproduction"],
        "source_time_grid": {
            "kind": "GOVERNED_RECONSTRUCTION_FROM_LOCKED_TIME_INDEX",
            "sample_count": len(source_times),
            "support_s": [source_times[0], source_times[-1]],
        },
        "source": {"path": source_info["path"], "sha256": source_info["sha256"], "commit": lock["checkout_commit"], "tree": lock["checkout_tree_sha"], "rights": "CC-BY-4.0_WITH_ATTRIBUTION"},
        "historical_protected_access_occurred": True,
        "blinding_status": "NOT_BLINDED_DUE_TO_PRIOR_PR16_ACCESS",
        "corrective_protocol_protected_processing_count": 1,
    }
    canonical_write(output, result)
    with reduced.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["source_index","source_time_s","mapped_solver_time_s","outlet_flow_m3_s","predicted_flow_g_per_s","normalized_predicted_flow","protected_window","normalization_window"])
        for index, (source_time, solver_time, value, normalized) in enumerate(zip(source_times, mapped, predicted, pred_norm_all)):
            writer.writerow([index, f"{source_time:.12g}", f"{solver_time:.12g}", f"{value/(1000*density):.16g}", f"{value:.16g}", f"{normalized:.16g}", int(first <= index <= last), int(late_first <= index <= late_last)])


def finalize_stage(numerical: Path, protected: Path, output: Path) -> None:
    num, prot = read_json(numerical), read_json(protected)
    shape_pass = prot["aggregate"]["status"] == "PASS"
    result = {
        "schema_version": "espresso.public.wp01r_005_execution_result.v1",
        "protocol": {"historical_protected_access_occurred": True, "historical_protected_result_known": True, "blinding_status": "NOT_BLINDED_DUE_TO_PRIOR_PR16_ACCESS", "corrective_result_role": "GOVERNED_NONBLINDED_REPRODUCIBILITY_CONFIRMATION"},
        "numerical": num, "protected": prot,
        "overall_r1_physical_comparison": "SOURCE_LINKED_RECONSTRUCTION_PASS" if shape_pass else "SOURCE_LINKED_RECONSTRUCTION_FAIL",
        "physical_validation": "NOT_ESTABLISHED",
        "governing_physics_change": False,
        "post_protected_retuning_occurred": False,
    }
    canonical_write(output, result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("numerical", "protected", "finalize"), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--acceptance", type=Path)
    parser.add_argument("--case-manifest", type=Path)
    parser.add_argument("--numerical", type=Path)
    parser.add_argument("--puckworks", type=Path)
    parser.add_argument("--protected", type=Path)
    parser.add_argument("--reduced", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.stage == "numerical":
        numerical_stage(root, args.trace, args.acceptance, args.case_manifest, args.output)
    elif args.stage == "protected":
        protected_stage(root, args.trace, args.numerical, args.puckworks, args.output, args.reduced)
    else:
        finalize_stage(args.numerical, args.protected, args.output)


if __name__ == "__main__":
    main()
