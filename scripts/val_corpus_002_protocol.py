#!/usr/bin/env python3
"""Generate and verify prospective VAL-CORPUS-002 Stage-A records.

This utility reads only the pinned public Puckworks evidence snapshot.  It does
not run the solver, fit a parameter, or evaluate model-versus-source metrics.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
from pathlib import Path


SNAPSHOT_COMMIT = "9c52c94edb27b461b6e7a4d471d29f3cef9d053e"
SNAPSHOT_TREE = "44d6539096648777f78c4db83f0985d5bd16e352"
DEFAULT_SNAPSHOT = Path(os.environ.get("VAL_CORPUS_002_EVIDENCE_SNAPSHOT", "../.wp03-002-exact-head-review/evidence-snapshot-puckworks"))
CASE_DIR = Path("validation/cases/val_corpus_002")
BR_ORDER = ("1/1", "1/2", "1/3")
TARGET_MASS_G = {"1/1": 20.0, "1/2": 40.0, "1/3": 60.0}
AXES = {
    1: "LOW_FLOW_AXIS",
    2: "HIGH_FLOW_AXIS",
    3: "FINE_GRIND_SETTING_AXIS",
    4: "COARSE_GRIND_SETTING_AXIS",
    5: "LOW_TEMPERATURE_AXIS",
    6: "HIGH_TEMPERATURE_AXIS",
}
TDS_IDENTITY_ABSOLUTE_TOLERANCE = 1e-12
BASE_CONFIG = "config/reference_R0.json"
BASE_CONFIG_SHA256 = "67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286"
SOLVER_COMMIT = "0a5c146078da5d5f88b344b20e7b81042bf27ddb"
SOLVER_EXECUTABLE_SHA256 = "e682bb63d4b54a19133a81e1dc857217132b91918ecceb33ffbc88c35b6b0fd6"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def evidence_entry(snapshot: Path, rel: str, *, rights: str, definition: str,
                   units: str, admissibility: str, circularity: str,
                   role: str) -> dict[str, object]:
    path = snapshot / rel
    if not path.is_file():
        raise ValueError(f"missing pinned evidence: {rel}")
    return {
        "repository": "trbrewer/puckworks",
        "commit": SNAPSHOT_COMMIT,
        "tree": SNAPSHOT_TREE,
        "path": rel,
        "sha256": sha256(path),
        "rights": rights,
        "source_definition": definition,
        "units": units,
        "admissibility": admissibility,
        "circularity": circularity,
        "intended_role": role,
    }


def select_schmieder(rows: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    """Select solely from experiment metadata; never inspect outcome columns."""
    metadata_columns = {
        "exp", "rep", "doe_role", "target_flow_ml_s", "scale_flow_ml_s",
        "grind_level", "target_temp_C", "decent_temp_C", "pressure_max_bar",
        "component", "brew_ratio",
    }
    selected: list[dict] = []
    for row in rows:
        view = {key: row[key] for key in metadata_columns}
        exp = int(float(view["exp"]))
        if exp not in range(1, 8) or view["component"] != "TDS":
            continue
        target_mass = TARGET_MASS_G.get(view["brew_ratio"])
        tds_mass = float(row["mass_in_cup"])
        tds_fraction = float(row["conc_in_cup"])
        if row["mass_units"] != "g" or target_mass not in (20.0, 40.0, 60.0):
            raise ValueError("selected TDS row has invalid mass unit or target mass")
        if not all(math.isfinite(value) for value in (tds_mass, tds_fraction)):
            raise ValueError("selected TDS row contains a nonfinite value")
        if not 0.0 <= tds_fraction <= 1.0:
            raise ValueError("selected TDS fraction is outside [0, 1]")
        if not math.isclose(tds_fraction, tds_mass / target_mass, rel_tol=0.0,
                            abs_tol=TDS_IDENTITY_ABSOLUTE_TOLERANCE):
            raise ValueError("selected TDS mass/fraction identity fails")
        selected.append({
            "experiment": exp,
            "replicate": int(float(view["rep"])),
            "doe_role": view["doe_role"],
            "axis_role": "LOCAL_RECONSTRUCTION_ANCHOR" if exp == 7 else AXES[exp],
            "target_flow_ml_s": float(view["target_flow_ml_s"]),
            "measured_flow_ml_s": float(view["scale_flow_ml_s"]),
            "grinder_setting": float(view["grind_level"]),
            "target_temperature_C": float(view["target_temp_C"]),
            "measured_temperature_C": float(view["decent_temp_C"]),
            "maximum_pressure_bar": float(view["pressure_max_bar"]),
            "brew_ratio": view["brew_ratio"],
            "target_beverage_mass_g": target_mass,
            "tds_mass_g": tds_mass,
            "tds_mass_units": row["mass_units"],
            "tds_fraction": tds_fraction,
            "source_uncertainty": "REPLICATE_DISTRIBUTION_ONLY_NO_FABRICATED_FLOOR",
            "caveat": "maximum pressure is per-shot metadata, not a time-resolved basket pressure history",
        })
    anchor = [record for record in selected if record["experiment"] == 7]
    transfer = [record for record in selected if record["experiment"] != 7]
    return anchor, transfer


def interpolate_fixed_mass(points: list[tuple[float, float]], target_mass: float) -> float:
    """Linearly interpolate cumulative solute mass; fail closed on ambiguity."""
    if not points or not math.isfinite(target_mass):
        raise ValueError("missing or invalid fixed-mass observation")
    ordered = sorted(points)
    masses = [point[0] for point in ordered]
    if len(set(masses)) != len(masses):
        raise ValueError("duplicate cumulative beverage mass is ambiguous")
    if target_mass < masses[0] or target_mass > masses[-1]:
        raise ValueError("fixed-mass extrapolation is prohibited")
    for mass, solute in ordered:
        if mass == target_mass:
            return solute
    for (m0, s0), (m1, s1) in zip(ordered, ordered[1:]):
        if m0 < target_mass < m1:
            return s0 + (s1 - s0) * (target_mass - m0) / (m1 - m0)
    raise ValueError("target mass not bracketed")


def interval_tds(samples: list[tuple[float, float, float]], start: float,
                 end: float) -> float:
    """Integrate piecewise-linear mass rates over a closed 5-second interval."""
    if end - start != 5.0:
        raise ValueError("Waszkiewicz intervals must be exactly five seconds")
    by_time = {time: (solute_rate, beverage_rate) for time, solute_rate, beverage_rate in samples}
    if len(by_time) != len(samples):
        raise ValueError("duplicate interval time is ambiguous")
    if start not in by_time or end not in by_time:
        raise ValueError("interval endpoints missing; extrapolation prohibited")
    interval = sorted((time, *rates) for time, rates in by_time.items() if start <= time <= end)
    solute_mass = 0.0
    beverage_mass = 0.0
    for (t0, s0, b0), (t1, s1, b1) in zip(interval, interval[1:]):
        solute_mass += 0.5 * (s0 + s1) * (t1 - t0)
        beverage_mass += 0.5 * (b0 + b1) * (t1 - t0)
    if not math.isfinite(solute_mass) or not math.isfinite(beverage_mass) or beverage_mass <= 0:
        raise ValueError("invalid integrated interval mass")
    return solute_mass / beverage_mass


def normalized_log_secant(y_low: float, y_high: float, p_low: float,
                          p_high: float) -> float:
    if any(not math.isfinite(value) or value <= 0 for value in (y_low, y_high, p_low, p_high)):
        raise ValueError("log-secant inputs must be finite and positive")
    denominator = math.log(p_high) - math.log(p_low)
    if denominator == 0:
        raise ValueError("log-secant parameter range is zero")
    return (math.log(y_high) - math.log(y_low)) / denominator


def summarize(records: list[dict]) -> list[dict]:
    summaries = []
    for exp in sorted({record["experiment"] for record in records}):
        for br in BR_ORDER:
            subset = [r for r in records if r["experiment"] == exp and r["brew_ratio"] == br]
            values = [r["tds_mass_g"] for r in subset]
            summaries.append({
                "experiment": exp,
                "brew_ratio": br,
                "target_beverage_mass_g": TARGET_MASS_G[br],
                "replicate_count": len(values),
                "replicate_mean_tds_mass_g": statistics.fmean(values),
                "replicate_sample_sd_tds_mass_g": statistics.stdev(values),
                "replicate_range_tds_mass_g": [min(values), max(values)],
            })
    return summaries


def build(snapshot: Path) -> dict[str, object]:
    data_root = snapshot / "puckworks/data"
    cup_path = data_root / "schmieder2023/cup_masses.csv"
    fit_path = data_root / "schmieder2023/kinetics_fit_params_avg.csv"
    with cup_path.open(newline="") as stream:
        cup_rows = list(csv.DictReader(stream))
    with fit_path.open(newline="") as stream:
        fit_rows = list(csv.DictReader(stream))
    anchor, transfer = select_schmieder(cup_rows)
    fit = next(row for row in fit_rows if row["exp"] == "7" and row["component"] == "TDS")

    expected_anchor = {
        "doe_role": "DoE Central Point", "target_flow_ml_s": 2.0,
        "grinder_setting": 1.7, "target_temperature_C": 89.0,
    }
    for key, expected in expected_anchor.items():
        if {row[key] for row in anchor} != {expected}:
            raise ValueError(f"Exp-7 metadata mismatch for {key}")
    if len({row["replicate"] for row in anchor}) != 6 or len(anchor) != 18:
        raise ValueError("Exp-7 must contain six replicates at three brew ratios")
    if {r["experiment"] for r in anchor} & {r["experiment"] for r in transfer}:
        raise ValueError("calibration/comparison overlap")

    wasz_path = data_root / "waszkiewicz2025/tds_fractions.csv"
    with wasz_path.open(newline="") as stream:
        wasz = list(csv.DictReader(stream))
    times = [float(row[next(k for k in row if k.startswith("time"))]) for row in wasz]
    if len(wasz) != 12 or times != [2.5 + 5.0 * i for i in range(12)]:
        raise ValueError("unexpected Waszkiewicz TDS time series")

    evidence_specs = [
        ("puckworks/data/schmieder2023/PROVENANCE.md", "CC-BY-4.0", "Schmieder curated-data provenance and source equations", "mixed/declared in source", "ADMISSIBLE_PUBLIC", "OBSERVABLE_NONHOLDOUT", "PROVENANCE"),
        ("puckworks/data/schmieder2023/cup_masses.csv", "CC-BY-4.0", "replicate-level component cup masses and condition metadata", "g or mg; mL/s; degC; bar", "ADMISSIBLE_PUBLIC", "EXP7_CALIBRATION_EXCLUDED_FROM_TRANSFER", "MANDATORY_PRIMARY"),
        ("puckworks/data/schmieder2023/kinetics_fit_params_avg.csv", "CC-BY-4.0", "experiment-average exponential source-fit parameters", "g/g or mg/g; g beverage", "ADMISSIBLE_PUBLIC", "SOURCE_FITTED_NOT_INDEPENDENT", "MANDATORY_PRIMARY"),
        ("docs/cards/schmieder2023.md", "CC-BY-4.0", "model card and exact source equation transcription", "mixed", "ADMISSIBLE_PUBLIC", "DESCRIPTIVE_SOURCE_SUMMARY", "EQUATION_AND_LIMITATION_REFERENCE"),
        ("puckworks/data/waszkiewicz2025/PROVENANCE.md", "CC-BY-4.0", "Waszkiewicz source provenance and clock definitions", "mixed/declared in source", "ADMISSIBLE_PUBLIC", "OBSERVABLE_NONHOLDOUT", "PROVENANCE"),
        ("puckworks/data/waszkiewicz2025/tds_fractions.csv", "CC-BY-4.0", "9-bar mean TDS fraction for twelve five-second collected fractions", "s; dimensionless fraction", "ADMISSIBLE_PUBLIC_NONHOLDOUT", "CROSS_SOURCE_CHEMISTRY_WITH_SAME_SOURCE_HYDRAULIC_CONDITIONING_AND_TDS_DISSOLVED_MASS_SOFT_CIRCULARITY", "MANDATORY_PRIMARY_NO_INDEPENDENT_WHOLE_SOLVER_CHEMISTRY_VALIDATION"),
        ("docs/cards/waszkiewicz2025.md", "CC-BY-4.0", "Waszkiewicz model/evidence card", "mixed", "ADMISSIBLE_PUBLIC", "DESCRIPTIVE_SOURCE_SUMMARY", "CLOCK_AND_LIMITATION_REFERENCE"),
    ]
    evidence = [evidence_entry(snapshot, *spec[:1], rights=spec[1], definition=spec[2], units=spec[3], admissibility=spec[4], circularity=spec[5], role=spec[6]) for spec in evidence_specs]

    c0 = 0.24827
    decay_mass_g = 17.47261
    p1_inventory_g = c0 * decay_mass_g
    p1_fraction = 0.216896244235
    if not math.isclose(p1_fraction, p1_inventory_g / 20.0, rel_tol=0.0, abs_tol=1e-15):
        raise ValueError("P1 reduced inventory fraction arithmetic mismatch")
    p1_k = 1.0 * 2.0 / decay_mass_g
    derived_class = "SOURCE_DERIVED_REDUCED_LAW_MAPPING"
    parameters = {
        "P0_MERGED_PREDECESSOR_ZERO_RETUNING": {
            "extractableFraction": {"value": 0.28, "unit": "g/g dry dose", "class": "FIXED_PREDECESSOR_VALUE"},
            "extractionRateConstant": {"value": 0.15, "unit": "s^-1", "class": "FIXED_PREDECESSOR_VALUE"},
            "saturationConcentration": {"value": 180.0, "unit": "kg/m^3", "class": "FIXED_PREDECESSOR_VALUE"},
            "effectiveSoluteDiffusivity": {"value": 1e-9, "unit": "m^2/s", "class": "FIXED_PREDECESSOR_VALUE"},
            "fitting": "NONE",
        },
        "P1_SCHMIEDER_EXP7_REDUCED_EXPONENTIAL_MAPPING": {
            "source_c0": {"value": c0, "unit": "g TDS/g beverage", "class": "SOURCE_FITTED", "semantic_role": "FITTED_OUTLET_TDS_CONCENTRATION_NOT_SOLVER_EXTRACTABLE_FRACTION"},
            "source_lambda": {"value": decay_mass_g, "unit": "g beverage", "class": "SOURCE_FITTED", "semantic_role": "FITTED_BEVERAGE_MASS_DECAY_SCALE"},
            "extractableFraction": {"value": p1_fraction, "unit": "g/g dry dose", "class": derived_class, "formula": "c0 * lambda / dry_dose"},
            "reduced_initial_extractable_mass_g": {"value": p1_inventory_g, "unit": "g", "class": derived_class, "formula": "c0 * lambda"},
            "extractionRateConstant": {"value": p1_k, "unit": "s^-1", "class": derived_class, "formula": "rho_g_per_ml * Q_target_ml_per_s / lambda_g", "inputs": {"rho_g_per_ml": 1.0, "Q_target_ml_per_s": 2.0, "lambda_g": decay_mass_g}},
            "saturationConcentration": {"value": 180.0, "unit": "kg/m^3", "class": "FIXED_PREDECESSOR_VALUE"},
            "effectiveSoluteDiffusivity": {"value": 1e-9, "unit": "m^2/s", "class": "FIXED_PREDECESSOR_VALUE"},
            "fitting": "NONE",
            "semantics": ["INTERNALLY_CONSISTENT_ZERO_DIMENSIONAL_EXPONENTIAL_MAPPING", "NOT_A_DIRECTLY_FITTED_SOLVER_PARAMETER", "NOT_EXACT_SOURCE_EQ3_DISCRETE_FIRST_FRACTION_REPRESENTATION", "NOT_EVIDENCE_PDE_LOCAL_RATE_IS_PHYSICALLY_IDENTIFIED"],
        },
        "P2_SCHMIEDER_EXP7_ONE_SCALAR_RECONSTRUCTION": {
            "extractableFraction": {"value": p1_fraction, "unit": "g/g dry dose", "class": derived_class},
            "extractionRateConstant": {"value": "UNRESOLVED_UNTIL_STAGE_B", "unit": "s^-1", "class": "CALIBRATED_IN_THIS_CASE", "linear_bounds_s_inverse": [p1_k / 10.0, p1_k * 10.0], "log_bounds": [math.log(p1_k / 10.0), math.log(p1_k * 10.0)]},
            "saturationConcentration": {"value": 180.0, "unit": "kg/m^3", "class": "FIXED_PREDECESSOR_VALUE"},
            "effectiveSoluteDiffusivity": {"value": 1e-9, "unit": "m^2/s", "class": "FIXED_PREDECESSOR_VALUE"},
            "objective": "equal-weight mean squared relative error at 20, 40, 60 g",
            "calibration_context": {"anchor": "SCHMIEDER_EXP7", "hydraulic_mode": "H1_FLOW_CONDITIONED_EFFECTIVE_DARCY_CLOCK_ONLY", "observations": "replicate-mean cup TDS mass at 20, 40, 60 g", "fitted_parameter": "ONE_GLOBAL_EXTRACTION_RATE_CONSTANT", "h0_calibration": "PROHIBITED", "separate_mode_specific_k": "PROHIBITED", "transfer_refit": "PROHIBITED", "production_application": "SAME_FITTED_K_UNCHANGED_FOR_ALL_H0_AND_H1_COMPARISONS"},
            "optimizer": {"algorithm": "bounded golden-section search in log(k)", "stopping_tolerance_log_k": 1e-8, "maximum_evaluations": 128, "tie_break": "lower k", "failure": "FAIL_CLOSED_NO_PARAMETER"},
            "stage_a_execution": "PROHIBITED_NOT_INVOKED",
        },
    }

    sensitivity = []
    base = {"extractableFraction": p1_fraction, "extractionRateConstant": p1_k, "effectiveSoluteDiffusivity": 1e-9, "saturationConcentration": 180.0}
    factors = {"extractableFraction": [0.8, 1.0, 1.2], "extractionRateConstant": [0.5, 1.0, 2.0], "effectiveSoluteDiffusivity": [0.1, 1.0, 10.0], "saturationConcentration": [0.5, 1.0, 2.0]}
    sensitivity.append({"run_id": "SENS_BASELINE", "parameter": "ALL", "factor": 1.0, "absolute_parameters": base})
    for parameter, grid in factors.items():
        for factor in grid:
            if factor == 1.0:
                continue
            values = dict(base)
            values[parameter] *= factor
            if parameter == "extractableFraction":
                values[parameter] = {0.8: 0.173516995388, 1.2: 0.260275493082}[factor]
            sensitivity.append({"run_id": f"SENS_{parameter}_{factor:g}X", "parameter": parameter, "factor": factor, "absolute_parameters": values})

    all_selected = anchor + transfer
    conditions = {}
    for exp in range(1, 8):
        exp_records = [record for record in all_selected if record["experiment"] == exp]
        unique_replicates = {}
        for record in exp_records:
            metadata = {
                "replicate": record["replicate"],
                "measured_flow_ml_s": record["measured_flow_ml_s"],
                "measured_temperature_C": record["measured_temperature_C"],
                "maximum_pressure_bar": record["maximum_pressure_bar"],
            }
            if record["replicate"] in unique_replicates and unique_replicates[record["replicate"]] != metadata:
                raise ValueError("replicate metadata differs across brew-ratio rows")
            unique_replicates[record["replicate"]] = metadata
        replicate_values = [unique_replicates[key] for key in sorted(unique_replicates)]
        mean_flow = statistics.fmean(item["measured_flow_ml_s"] for item in replicate_values)
        mean_pressure = statistics.fmean(item["maximum_pressure_bar"] for item in replicate_values)
        darcy_k = (0.000315 * 0.009011660896432553 * mean_flow * 1e-6
                   / (math.pi * 0.029**2 * mean_pressure * 1e5))
        first = exp_records[0]
        conditions[exp] = {
            "experiment": exp, "axis_role": first["axis_role"],
            "doe_role": first["doe_role"], "dry_dose_g": 20.0,
            "target_flow_ml_s": first["target_flow_ml_s"],
            "grinder_setting": first["grinder_setting"],
            "target_temperature_C": first["target_temperature_C"],
            "replicate_count": len(replicate_values), "unique_replicates": replicate_values,
            "aggregation": "ARITHMETIC_MEAN_OF_UNIQUE_REPLICATE_METADATA",
            "mean_measured_flow_ml_s": mean_flow,
            "mean_measured_temperature_C": statistics.fmean(item["measured_temperature_C"] for item in replicate_values),
            "mean_unique_replicate_maximum_pressure_bar": mean_pressure,
            "h1_effective_darcy_coefficient_m2": darcy_k,
        }

    parameter_values = {
        "P0": {"extractableFraction": 0.28, "extractionRateConstant_s_inverse": 0.15, "saturationConcentration_kg_m3": 180.0, "effectiveSoluteDiffusivity_m2_s": 1e-9},
        "P1": {"extractableFraction": p1_fraction, "extractionRateConstant_s_inverse": p1_k, "saturationConcentration_kg_m3": 180.0, "effectiveSoluteDiffusivity_m2_s": 1e-9},
        "P2_FIXED_AFTER_EXP7_CALIBRATION": {"extractableFraction": p1_fraction, "extractionRateConstant_s_inverse": "EXACT_GLOBAL_P2_K_FROM_AUTHORIZED_CALIBRATION", "saturationConcentration_kg_m3": 180.0, "effectiveSoluteDiffusivity_m2_s": 1e-9},
    }
    run_matrix = []
    for exp in range(1, 8):
        for parameterization in ("P0", "P1", "P2_FIXED_AFTER_EXP7_CALIBRATION"):
            for hydraulic in ("H0_NATIVE_COUPLED_MODE", "H1_SOURCE_CONDITIONED_DARCY_MODE"):
                condition = conditions[exp]
                coefficient = 1.77e-15 if hydraulic.startswith("H0") else condition["h1_effective_darcy_coefficient_m2"]
                run_matrix.append({
                    "run_id": f"SCHM_EXP{exp}_{parameterization}_{hydraulic.split('_')[0]}",
                    "experiment": exp, "parameterization": parameterization,
                    "hydraulic_role": hydraulic, "future_openfoam": True,
                    "source_aggregation": condition,
                    "base_configuration": {"path": BASE_CONFIG, "sha256": BASE_CONFIG_SHA256},
                    "solver": {"commit": SOLVER_COMMIT, "executable_sha256_required": SOLVER_EXECUTABLE_SHA256},
                    "geometry": {"bed_depth_m": 0.009011660896432553, "basket_radius_m": 0.029, "basket_diameter_m": 0.058, "dry_dose_kg": 0.02},
                    "boundary_conditions": {"inlet_pressure_gauge_Pa": condition["mean_unique_replicate_maximum_pressure_bar"] * 1e5, "outlet_pressure_gauge_Pa": 0.0, "pressure_ramp_time_s": 3.0},
                    "hydraulics": {"mode": "LIMITED_NATIVE_COUPLED_DIAGNOSTIC" if hydraulic.startswith("H0") else "FLOW_CONDITIONED_EFFECTIVE_DARCY_CLOCK", "uniform_saturated_coefficient_m2": coefficient, "dynamic_viscosity_Pa_s": 0.000315, "compaction": "DISABLED", "darcy_forchheimer": "DISABLED", "physical_permeability_inference": "PROHIBITED" if hydraulic.startswith("H1") else "NOT_APPLICABLE", "permeability_validation": "PROHIBITED" if hydraulic.startswith("H1") else "NOT_CLAIMED", "claim": "LIMITED_NATIVE_COUPLED_DIAGNOSTIC" if hydraulic.startswith("H0") else "CHEMISTRY_COMPONENT_DIAGNOSTIC_ONLY"},
                    "chemistry": parameter_values[parameterization],
                    "controls": {"delta_t_s": 0.02, "end_time_s": 90.0, "mpi_ranks": 16, "field_write_interval_s": 1.0, "reduced_trace_maximum_interval_s": 0.1},
                    "observation_operators": {"targets_g": [20.0, 40.0, 60.0], "cup_solute_mass": "LINEAR_INTERPOLATION_AGAINST_CUMULATIVE_BEVERAGE_MASS", "cumulative_tds": "INTERPOLATED_CUP_SOLUTE_MASS_DIVIDED_BY_TARGET_MASS", "extraction_yield": "INTERPOLATED_CUP_SOLUTE_MASS_DIVIDED_BY_20_G_DRY_DOSE", "duplicate_mass": "FAIL_CLOSED", "extrapolation": "PROHIBITED", "missing_target": "INCOMPLETE_FAIL_CLOSED"},
                    "gates": {"completion": "ALL_TARGETS_BRACKETED_AND_FINAL_TIME_REACHED_WITHOUT_FATAL", "liquid_balance_relative_absolute_max": 1e-8, "solute_balance_relative_absolute_max": 1e-8, "boundedness": "FINITE_NONNEGATIVE_MASSES_AND_0_LE_TDS_LE_1"},
                    "artifacts": {"retain": ["exact input manifest", "executable hash", "complete solver log", "reduced trace", "case/result manifest"], "identity": "SHA256_EACH_FILE_PLUS_SORTED_PATH_SIZE_SHA256_AGGREGATE", "location": "AUTHORIZED_EXTERNAL_RUNTIME_PATH_NOT_GIT"},
                })

    return {
        "evidence": {"schema_version": 1, "snapshot": {"repository": "trbrewer/puckworks", "commit": SNAPSHOT_COMMIT, "tree": SNAPSHOT_TREE}, "files": evidence},
        "cohort": {"schema_version": 1, "selection_basis": "METADATA_ONLY_NO_TDS_MASS_OR_CONCENTRATION", "anchor_records": anchor, "axis_transfer_records": transfer, "summaries": summarize(anchor + transfer), "exp7_source_fit": {"c0_g_per_g": float(fit["c0"]), "c0_se_g_per_g": float(fit["c0_se"]), "lambda_g_beverage": float(fit["lambda_g"]), "lambda_se_g_beverage": float(fit["lambda_se"])}, "partition_disjoint": True},
        "parameters": {"schema_version": 2, "source_semantics": {"c0": "FITTED_OUTLET_TDS_CONCENTRATION_G_PER_G_BEVERAGE", "lambda": "FITTED_BEVERAGE_MASS_DECAY_SCALE_G"}, "parameterizations": parameters, "density_convention": "rho=1.0 g/mL is the reduced source-mapping convention; it is not a new solver property", "mapping_dimension_check": "(g/mL)*(mL/s)/g = 1/s", "p1_mapping_verified": all((math.isclose(p1_inventory_g, 4.3379248847, rel_tol=0, abs_tol=1e-12), math.isclose(p1_fraction, 0.216896244235, rel_tol=0, abs_tol=1e-12), math.isclose(p1_k, 0.11446486815650324, rel_tol=0, abs_tol=5e-16)))},
        "run_matrix": {"schema_version": 2, "calibration_evaluation_inventory": {"anchor": "SCHMIEDER_EXP7", "hydraulic_mode": "H1_ONLY", "maximum_optimizer_evaluations": 128, "evaluation_identity": "solver_commit+executable+case_inputs+log_k", "h0_calibration": "PROHIBITED", "separate_mode_specific_k": "PROHIBITED"}, "final_production_run_inventory": run_matrix, "future_openfoam_run_count": len(run_matrix), "reused_exact_evaluations": [{"source": "FINAL_SUCCESSFUL_P2_OPTIMIZER_EVALUATION", "target": "SCHM_EXP7_P2_FIXED_AFTER_EXP7_CALIBRATION_H1", "reuse_count": 1, "condition": "REUSE_ONLY_IF_CASE_AND_EXECUTABLE_IDENTITIES_MATCH_EXACTLY"}], "stage_a_execution": "NOT_AUTHORIZED"},
        "sensitivity": {"schema_version": 2, "analysis_name": "FINITE_RANGE_ONE_AT_A_TIME_SENSITIVITY", "claim": "NOT_STRUCTURAL_IDENTIFIABILITY", "baseline": "exact reuse of production SCHM_EXP7_P1_H1 only when all identities match", "baseline_reuse_count": 1, "future_runs": sensitivity, "future_run_count": len(sensitivity), "new_future_execution_count_if_reuse_valid": len(sensitivity) - 1, "outputs": ["cup_solute_mass_g_at_20g", "cup_solute_mass_g_at_40g", "cup_solute_mass_g_at_60g"], "analysis": {"normalized_sensitivity_formula": "[ln(y_high)-ln(y_low)]/[ln(p_high)-ln(p_low)]", "nonpositive_or_missing_output": "FAIL_CLOSED", "matrix_shape": [3, 4], "rank_ceiling": 3, "jacobian": "FINITE_RANGE_LOG_SECANTS", "singular_values": True, "numerical_rank_tolerance": {"relative_to_largest_singular_value": 1e-8, "absolute": 1e-12}, "parameter_output_correlation": True, "equifinality_warning": True}},
        "waszkiewicz": {"schema_version": 2, "point_count": len(wasz), "times_s": times, "collection_intervals_s": [[5.0 * i, 5.0 * (i + 1)] for i in range(12)], "observation_operator": "INTEGRATED_OUTLET_SOLUTE_MASS_OVER_INTERVAL_DIVIDED_BY_INTEGRATED_BEVERAGE_MASS_OVER_INTERVAL", "integration_rule": "PIECEWISE_LINEAR_TRAPEZOIDAL_INTEGRATION_REQUIRING_BOTH_INTERVAL_ENDPOINTS", "midpoint_point_sampling": "PROHIBITED", "extrapolation": "PROHIBITED", "role": {"comparison": "CROSS_SOURCE_CHEMISTRY_PARAMETERIZATION_NONHOLDOUT", "hydraulics": "SAME_SOURCE_WASZKIEWICZ_HYDRAULIC_CONDITIONING", "circularity": "TDS_AND_DISSOLVED_MASS_SOFT_CIRCULARITY", "claim": "NO_INDEPENDENT_WHOLE_SOLVER_CHEMISTRY_VALIDATION"}, "chemistry_calibration": "NONE", "optimized_time_shift": "PROHIBITED", "clock_mapping": {"status": "AMBIGUOUS", "presentations": [{"id": "SOURCE_REPORTED_CLOCK", "model_intervals_s": [[5.0 * i, 5.0 * (i + 1)] for i in range(12)]}, {"id": "EXISTING_ACCEPTED_FIXED_SOURCE_TO_SOLVER_OFFSET_PLUS_3_SECONDS", "model_intervals_s": [[3.0 + 5.0 * i, 8.0 + 5.0 * i] for i in range(12)]}], "operator_identical_for_both_presentations": True, "optimization": "PROHIBITED"}, "unsupported_chemistry": {"5_bar": "UNAVAILABLE_NOT_INFERRED", "11_bar": "UNAVAILABLE_NOT_INFERRED"}},
    }


def write_records(records: dict[str, object]) -> None:
    mapping = {
        "evidence": "VAL_CORPUS_002_EVIDENCE_MANIFEST.json",
        "cohort": "VAL_CORPUS_002_COHORT_SELECTION.json",
        "parameters": "VAL_CORPUS_002_PARAMETER_SOURCE_LEDGER.json",
        "run_matrix": "VAL_CORPUS_002_FUTURE_RUN_MATRIX.json",
        "sensitivity": "VAL_CORPUS_002_SENSITIVITY_MATRIX.json",
        "waszkiewicz": "VAL_CORPUS_002_WASZKIEWICZ_COHORT.json",
    }
    for key, filename in mapping.items():
        dump(CASE_DIR / filename, records[key])


def verify(records: dict[str, object]) -> None:
    expected = {
        "evidence": "VAL_CORPUS_002_EVIDENCE_MANIFEST.json",
        "cohort": "VAL_CORPUS_002_COHORT_SELECTION.json",
        "parameters": "VAL_CORPUS_002_PARAMETER_SOURCE_LEDGER.json",
        "run_matrix": "VAL_CORPUS_002_FUTURE_RUN_MATRIX.json",
        "sensitivity": "VAL_CORPUS_002_SENSITIVITY_MATRIX.json",
        "waszkiewicz": "VAL_CORPUS_002_WASZKIEWICZ_COHORT.json",
    }
    for key, filename in expected.items():
        actual = json.loads((CASE_DIR / filename).read_text())
        if actual != records[key]:
            raise ValueError(f"stale generated record: {filename}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    records = build(args.snapshot.resolve())
    if args.write:
        write_records(records)
    else:
        verify(records)
    print("VAL_CORPUS_002_PROTOCOL_RECORDS_PASS")


if __name__ == "__main__":
    main()
