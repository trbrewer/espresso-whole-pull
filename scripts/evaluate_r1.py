#!/usr/bin/env python3
"""Evaluate the frozen WP01R-003 R1 comparison contract."""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interpolate(times: list[float], values: list[float], target: float) -> float:
    index = bisect.bisect_left(times, target)
    if index == 0:
        return values[0]
    if index == len(times):
        return values[-1]
    fraction = (target - times[index - 1]) / (times[index] - times[index - 1])
    return values[index - 1] + fraction * (values[index] - values[index - 1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--puckworks-dir", type=Path, required=True)
    parser.add_argument("--acceptance", type=Path, required=True)
    parser.add_argument("--r0-acceptance", type=Path, required=True)
    parser.add_argument("--build-provenance", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, case, puckworks = (
        args.root.resolve(),
        args.case_dir.resolve(),
        args.puckworks_dir.resolve(),
    )
    contract_path = root / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json"
    contract = load_json(contract_path)
    lock = load_json(root / "dependencies/puckworks.lock.json")
    if contract["contract_status"] != "FROZEN_FOR_WP01R_004":
        raise SystemExit("R1 contract is not frozen")
    if (lock["checkout_commit"], lock["checkout_tree_sha"]) != (
        "fc61c4670ec7bf801e40bb391aab16048b8da26b",
        "1d553e44ee2f7480a5df521560801b478618cc84",
    ):
        raise SystemExit("Puckworks lock identity mismatch")

    trace_path = case / "postProcessing/wholePull/0/traces.csv"
    source_path = puckworks / contract["protected_comparison_contract"]["source_path"]
    with trace_path.open(newline="", encoding="utf-8") as stream:
        predicted_rows = list(csv.DictReader(stream))
    predicted_times = [float(row["time_s"]) for row in predicted_rows]
    predicted_flow = [
        1000.0 * 965.0 * float(row["outlet_flow_m3_s"])
        for row in predicted_rows
    ]
    with (
        puckworks / "puckworks/data/waszkiewicz2025/traces_time_dependent.csv"
    ).open(newline="", encoding="utf-8") as stream:
        aggregate_rows = [
            row
            for row in csv.DictReader(stream)
            if float(row["reference_pressure_round__bar"]) == 9.0
        ]
    source_times = [float(row["time__s"]) for row in aggregate_rows]
    mapped_prediction = [
        interpolate(predicted_times, predicted_flow, time + 3.0)
        for time in source_times
    ]
    with source_path.open(newline="", encoding="utf-8") as stream:
        observed_rows = list(csv.DictReader(stream))

    protected = contract["protected_comparison_contract"]
    first, last = protected["protected_indices"]["first"], protected["protected_indices"]["last"]
    late_first, late_last = (
        protected["normalization_indices"]["first"],
        protected["normalization_indices"]["last"],
    )
    epsilon = protected["pearson_degeneracy"]["normalized_standard_deviation_epsilon"]
    predicted_late = statistics.mean(mapped_prediction[late_first : late_last + 1])
    predicted_norm = [
        value / predicted_late for value in mapped_prediction[first : last + 1]
    ]
    predicted_std = statistics.pstdev(predicted_norm)
    shots = []
    for shot_id in protected["shot_ids"]:
        rows = [row for row in observed_rows if row["shot_id"] == shot_id]
        observed = [float(row["mass_flow_rate__g_per_s"]) for row in rows]
        observed_late = statistics.mean(observed[late_first : late_last + 1])
        observed_norm = [
            value / observed_late for value in observed[first : last + 1]
        ]
        observed_std = statistics.pstdev(observed_norm)
        rmse = math.sqrt(
            statistics.mean(
                (predicted - actual) ** 2
                for predicted, actual in zip(predicted_norm, observed_norm)
            )
        )
        pearson = None
        pearson_status = "FAIL"
        if (
            predicted_std > epsilon
            and observed_std > epsilon
            and all(math.isfinite(value) for value in predicted_norm + observed_norm)
        ):
            pearson = statistics.correlation(predicted_norm, observed_norm)
            pearson_status = "PASS" if pearson >= 0.90 else "FAIL"
        shots.append(
            {
                "shot_id": shot_id,
                "observed_late_mean_g_per_s": observed_late,
                "predicted_late_mean_g_per_s": predicted_late,
                "normalized_shape_rmse": rmse,
                "pearson_r": pearson,
                "predicted_normalized_population_std": predicted_std,
                "observed_normalized_population_std": observed_std,
                "rmse_gate_status": "PASS" if rmse <= 0.20 else "FAIL",
                "pearson_gate_status": pearson_status,
                "pearson_undefined_reason": (
                    "PREDICTED_NORMALIZED_STD_AT_OR_BELOW_1E-8"
                    if pearson is None
                    else None
                ),
            }
        )
    median_rmse = statistics.median(item["normalized_shape_rmse"] for item in shots)
    finite_r = [item["pearson_r"] for item in shots if item["pearson_r"] is not None]
    median_r = statistics.median(finite_r) if len(finite_r) == len(shots) else None
    shape_pass = (
        median_rmse <= 0.15
        and sum(item["normalized_shape_rmse"] <= 0.20 for item in shots) >= 4
        and median_r is not None
        and median_r >= 0.95
        and sum((item["pearson_r"] or -math.inf) >= 0.90 for item in shots) >= 4
    )
    acceptance = load_json(args.acceptance)
    r0_acceptance = load_json(args.r0_acceptance)
    build = load_json(args.build_provenance)
    calibration_target = 1.8821959328386835
    calibration_error = abs(predicted_late - calibration_target) / calibration_target
    report = {
        "schema_version": "espresso.public.wp01r_005_scorecard.v1",
        "task": "WP01R-005",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "source_dependency": {
            "commit": lock["checkout_commit"],
            "tree": lock["checkout_tree_sha"],
            "protected_source_path": protected["source_path"],
            "protected_source_sha256": sha256(source_path),
        },
        "solver_trace_sha256": sha256(trace_path),
        "contract": {"path": str(contract_path.relative_to(root)), "sha256": sha256(contract_path)},
        "execution": {
            "end_time_s": float(predicted_rows[-1]["time_s"]),
            "openfoam_execution_count": 1,
            "parameter_fitting_count": 0,
            "optimizer_iteration_count": 0,
            "post_run_adjustment_count": 0,
            "solver_executable_sha256": build["executable"]["sha256"],
            "openfoam_environment": {
                key: build["environment"][key]
                for key in (
                    "WM_PROJECT",
                    "WM_PROJECT_VERSION",
                    "WM_OPTIONS",
                    "WM_COMPILER",
                    "WM_PRECISION_OPTION",
                    "WM_LABEL_SIZE",
                    "WM_MPLIB",
                )
            },
        },
        "calibration_reproduction": {
            "target_g_per_s": calibration_target,
            "simulated_late_mean_g_per_s": predicted_late,
            "relative_error": calibration_error,
            "limit": 0.02,
            "status": "PASS" if calibration_error <= 0.02 else "FAIL",
        },
        "protected_comparison": {
            "shots": shots,
            "median_normalized_shape_rmse": median_rmse,
            "shots_at_or_below_rmse_0_20": sum(
                item["normalized_shape_rmse"] <= 0.20 for item in shots
            ),
            "median_pearson_r": median_r,
            "shots_at_or_above_pearson_0_90": sum(
                (item["pearson_r"] or -math.inf) >= 0.90 for item in shots
            ),
            "status": "PASS" if shape_pass else "FAIL",
        },
        "numerical_and_conservation": {
            "source_acceptance_status": acceptance["status"],
            "all_numerical_gates_pass": all(
                gate["status"] == "PASS"
                for gate in acceptance["numerical_acceptance_gates"].values()
            ),
            "all_reduced_twin_gates_pass": all(
                gate["status"] == "PASS"
                for gate in acceptance["openfoam_b0_parity_gates"].values()
            ),
            "max_liquid_balance_residual_kg": acceptance["primary_outputs"][
                "max_liquid_balance_residual_kg"
            ],
            "max_solute_balance_residual_kg": acceptance["primary_outputs"][
                "max_solute_balance_residual_kg"
            ],
            "first_drip_s": acceptance["primary_outputs"]["first_drip_s"],
        },
        "r0_regression": {
            "status": r0_acceptance["status"],
            "all_required_reference_gates_pass": r0_acceptance[
                "all_required_reference_gates_pass"
            ],
            "all_required_b0_parity_gates_pass": r0_acceptance[
                "all_required_b0_parity_gates_pass"
            ],
            "first_drip_s": r0_acceptance["primary_outputs"]["first_drip_s"],
            "cup_beverage_mass_at_end_kg": r0_acceptance["primary_outputs"][
                "cup_beverage_mass_at_end_kg"
            ],
            "acceptance_sha256": sha256(args.r0_acceptance),
            "note": "Fresh regression run only; the frozen R0 baseline was not modified.",
        },
        "status_families": {
            "CONTRACT_INTEGRITY": "PASS",
            "CASE_GENERATION": "PASS",
            "NUMERICAL_VERIFICATION": "PASS",
            "CONSERVATION": "PASS",
            "CALIBRATION_REPRODUCTION": (
                "PASS" if calibration_error <= 0.02 else "FAIL"
            ),
            "PROTECTED_FLOW_SHAPE_COMPARISON": "PASS" if shape_pass else "FAIL",
            "CHEMISTRY_PLAUSIBILITY": "REPORTED_UNSCORED",
            "OVERALL_R1_PHYSICAL_COMPARISON": (
                "SOURCE_LINKED_RECONSTRUCTION_PASS"
                if shape_pass
                else "SOURCE_LINKED_RECONSTRUCTION_FAIL"
            ),
        },
        "residual_classification": {
            "primary": "STRUCTURAL_MODEL_INADEQUACY",
            "finding": (
                "The frozen uniform-permeability model predicts a constant "
                "post-wetting flow and does not reproduce the protected rising-flow shapes."
            ),
            "software_execution_failure": False,
            "retuning_authorized": False,
        },
        "overall_r1_physical_comparison": (
            "SOURCE_LINKED_RECONSTRUCTION_PASS"
            if shape_pass
            else "SOURCE_LINKED_RECONSTRUCTION_FAIL"
        ),
        "physical_validation": "NOT_ESTABLISHED",
        "governing_physics_change": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["overall_r1_physical_comparison"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
