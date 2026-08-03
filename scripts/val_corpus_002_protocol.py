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
            "target_beverage_mass_g": TARGET_MASS_G[view["brew_ratio"]],
            "tds_mass_g": float(row["mass_in_cup"]),
            "tds_mass_units": row["mass_units"],
            "tds_fraction": float(row["conc_in_cup"]) / 1000.0,
            "source_uncertainty": "REPLICATE_DISTRIBUTION_ONLY_NO_FABRICATED_FLOOR",
            "caveat": "maximum pressure is per-shot metadata, not a time-resolved basket pressure history",
        })
    anchor = [record for record in selected if record["experiment"] == 7]
    transfer = [record for record in selected if record["experiment"] != 7]
    return anchor, transfer


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
        ("puckworks/data/waszkiewicz2025/tds_fractions.csv", "CC-BY-4.0", "9-bar mean TDS-fraction series", "s; dimensionless fraction", "ADMISSIBLE_PUBLIC", "CROSS_SOURCE_NOT_CALIBRATION", "MANDATORY_PRIMARY"),
        ("docs/cards/waszkiewicz2025.md", "CC-BY-4.0", "Waszkiewicz model/evidence card", "mixed", "ADMISSIBLE_PUBLIC", "DESCRIPTIVE_SOURCE_SUMMARY", "CLOCK_AND_LIMITATION_REFERENCE"),
    ]
    evidence = [evidence_entry(snapshot, *spec[:1], rights=spec[1], definition=spec[2], units=spec[3], admissibility=spec[4], circularity=spec[5], role=spec[6]) for spec in evidence_specs]

    p1_k = 1.0 * 2.0 / 17.47261
    parameters = {
        "P0_MERGED_PREDECESSOR_ZERO_RETUNING": {
            "extractableFraction": {"value": 0.28, "unit": "g/g dry dose", "class": "FIXED_PREDECESSOR_VALUE"},
            "extractionRateConstant": {"value": 0.15, "unit": "s^-1", "class": "FIXED_PREDECESSOR_VALUE"},
            "saturationConcentration": {"value": 180.0, "unit": "kg/m^3", "class": "FIXED_PREDECESSOR_VALUE"},
            "effectiveSoluteDiffusivity": {"value": 1e-9, "unit": "m^2/s", "class": "FIXED_PREDECESSOR_VALUE"},
            "fitting": "NONE",
        },
        "P1_SCHMIEDER_EXP7_DIRECT_SOURCE_MAPPING": {
            "extractableFraction": {"value": 0.24827, "unit": "g/g dry dose", "class": "SOURCE_FITTED"},
            "initial_extractable_mass_for_20g_dose_g": {"value": 4.9654, "class": "SOURCE_DERIVED"},
            "extractionRateConstant": {"value": p1_k, "unit": "s^-1", "class": "SOURCE_DERIVED", "formula": "rho_g_per_ml * Q_target_ml_per_s / lambda_g", "inputs": {"rho_g_per_ml": 1.0, "Q_target_ml_per_s": 2.0, "lambda_g": 17.47261}},
            "saturationConcentration": {"value": 180.0, "unit": "kg/m^3", "class": "FIXED_PREDECESSOR_VALUE"},
            "effectiveSoluteDiffusivity": {"value": 1e-9, "unit": "m^2/s", "class": "FIXED_PREDECESSOR_VALUE"},
            "fitting": "NONE",
        },
        "P2_SCHMIEDER_EXP7_ONE_SCALAR_RECONSTRUCTION": {
            "extractableFraction": {"value": 0.24827, "unit": "g/g dry dose", "class": "SOURCE_FITTED"},
            "extractionRateConstant": {"value": "UNRESOLVED_UNTIL_STAGE_B", "unit": "s^-1", "class": "CALIBRATED_IN_THIS_CASE", "linear_bounds_s_inverse": [p1_k / 10.0, p1_k * 10.0], "log_bounds": [math.log(p1_k / 10.0), math.log(p1_k * 10.0)]},
            "saturationConcentration": {"value": 180.0, "unit": "kg/m^3", "class": "FIXED_PREDECESSOR_VALUE"},
            "effectiveSoluteDiffusivity": {"value": 1e-9, "unit": "m^2/s", "class": "FIXED_PREDECESSOR_VALUE"},
            "objective": "equal-weight mean squared relative error at 20, 40, 60 g",
            "optimizer": {"algorithm": "bounded golden-section search in log(k)", "stopping_tolerance_log_k": 1e-8, "maximum_evaluations": 128, "tie_break": "lower k", "failure": "FAIL_CLOSED_NO_PARAMETER"},
            "stage_a_execution": "PROHIBITED_NOT_INVOKED",
        },
    }

    sensitivity = []
    base = {"extractableFraction": 0.24827, "extractionRateConstant": p1_k, "effectiveSoluteDiffusivity": 1e-9, "saturationConcentration": 180.0}
    factors = {"extractableFraction": [0.8, 1.0, 1.2], "extractionRateConstant": [0.5, 1.0, 2.0], "effectiveSoluteDiffusivity": [0.1, 1.0, 10.0], "saturationConcentration": [0.5, 1.0, 2.0]}
    sensitivity.append({"run_id": "SENS_BASELINE", "parameter": "ALL", "factor": 1.0, "absolute_parameters": base})
    for parameter, grid in factors.items():
        for factor in grid:
            if factor == 1.0:
                continue
            values = dict(base)
            values[parameter] *= factor
            sensitivity.append({"run_id": f"SENS_{parameter}_{factor:g}X", "parameter": parameter, "factor": factor, "absolute_parameters": values})

    run_matrix = []
    for exp in range(1, 8):
        for parameterization in ("P0", "P1", "P2_FIXED_AFTER_EXP7_CALIBRATION"):
            for hydraulic in ("H0_NATIVE_COUPLED_MODE", "H1_SOURCE_CONDITIONED_DARCY_MODE"):
                run_matrix.append({"run_id": f"SCHM_EXP{exp}_{parameterization}_{hydraulic.split('_')[0]}", "experiment": exp, "parameterization": parameterization, "hydraulic_role": hydraulic, "future_openfoam": True})

    return {
        "evidence": {"schema_version": 1, "snapshot": {"repository": "trbrewer/puckworks", "commit": SNAPSHOT_COMMIT, "tree": SNAPSHOT_TREE}, "files": evidence},
        "cohort": {"schema_version": 1, "selection_basis": "METADATA_ONLY_NO_TDS_MASS_OR_CONCENTRATION", "anchor_records": anchor, "axis_transfer_records": transfer, "summaries": summarize(anchor + transfer), "exp7_source_fit": {"c0_g_per_g": float(fit["c0"]), "c0_se_g_per_g": float(fit["c0_se"]), "lambda_g_beverage": float(fit["lambda_g"]), "lambda_se_g_beverage": float(fit["lambda_se"])}, "partition_disjoint": True},
        "parameters": {"schema_version": 1, "parameterizations": parameters, "density_convention": "rho=1.0 g/mL is the source direct-mapping convention; it is not a new solver property", "mapping_dimension_check": "(g/mL)*(mL/s)/g = 1/s", "p1_mapping_verified": math.isclose(p1_k, 0.11446486815650324, rel_tol=0, abs_tol=5e-16)},
        "run_matrix": {"schema_version": 1, "future_openfoam_runs": run_matrix, "future_openfoam_run_count": len(run_matrix), "stage_a_execution": "NOT_AUTHORIZED"},
        "sensitivity": {"schema_version": 1, "baseline": "P1 at Schmieder Exp-7 representative condition in H1", "future_runs": sensitivity, "future_run_count": len(sensitivity), "outputs": ["cup_solute_mass_g_at_20g", "cup_solute_mass_g_at_40g", "cup_solute_mass_g_at_60g"], "analysis": {"normalized_sensitivities": True, "jacobian": True, "singular_values": True, "numerical_rank_tolerance": {"relative_to_largest_singular_value": 1e-8, "absolute": 1e-12}, "parameter_output_correlation": True, "equifinality_warning": True, "claim": "PRACTICAL_LOCAL_SENSITIVITY_NOT_STRUCTURAL_IDENTIFIABILITY"}},
        "waszkiewicz": {"schema_version": 1, "point_count": len(wasz), "times_s": times, "role": "CROSS_SOURCE_NONHOLDOUT_COMPARISON", "chemistry_calibration": "NONE", "optimized_time_shift": "PROHIBITED", "clock_mapping": {"status": "AMBIGUOUS", "presentations": ["SOURCE_REPORTED_CLOCK", "EXISTING_ACCEPTED_FIXED_SOURCE_TO_SOLVER_OFFSET_PLUS_3_SECONDS"], "optimization": "PROHIBITED"}, "unsupported_chemistry": {"5_bar": "UNAVAILABLE_NOT_INFERRED", "11_bar": "UNAVAILABLE_NOT_INFERRED"}},
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
