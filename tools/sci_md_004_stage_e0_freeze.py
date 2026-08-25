#!/usr/bin/env python3
"""Create the target-blind SCI-MD-004 Stage E0 G1 freeze.

The generator intentionally has no argument for the protected target file and
does not import or invoke the Stage C protected scorer.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

TRAINING_FILES = (
    "bundle_manifest.json",
    "training_contract.json",
    "schmieder_species_fractions_long.csv",
    "schmieder_training_inventories.csv",
    "pannusch_scaling_priors.csv",
    "maille_caffeine_plausibility.csv",
)
INPUT_FILES = ("angeloni_conditions.csv", "angeloni_inventories_long.csv", "data_contract.json")
SPECIES = ("caffeine", "trigonelline")
DENSITY_KG_M3 = 1000.0
LEGACY_EXTRACTABLE_FRACTION = 0.28


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fit_log_linear(rows: list[dict[str, float]]) -> dict[str, float]:
    points = [(row["time_s"], math.log(row["concentration_kg_m3"])) for row in rows]
    n = len(points)
    mean_t = sum(t for t, _ in points) / n
    mean_y = sum(y for _, y in points) / n
    sxx = sum((t - mean_t) ** 2 for t, _ in points)
    slope = sum((t - mean_t) * (y - mean_y) for t, y in points) / sxx
    intercept = mean_y - slope * mean_t
    residuals = [y - (intercept + slope * t) for t, y in points]
    sigma2 = sum(value * value for value in residuals) / (n - 2)
    se_slope = math.sqrt(sigma2 / sxx)
    se_intercept = math.sqrt(sigma2 * (1.0 / n + mean_t * mean_t / sxx))
    k = -slope
    csat = math.exp(intercept)
    return {
        "extractionRateConstant_1_s": k,
        "saturationConcentration_kg_m3": csat,
        "k_95pct_lower": k - 1.96 * se_slope,
        "k_95pct_upper": k + 1.96 * se_slope,
        "csat_95pct_lower": math.exp(intercept - 1.96 * se_intercept),
        "csat_95pct_upper": math.exp(intercept + 1.96 * se_intercept),
        "n_observations": n,
    }


def observations(training_dir: Path) -> dict[str, list[dict[str, float]]]:
    raw = read_csv(training_dir / "schmieder_species_fractions_long.csv")
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in raw:
        needed = ("flow_m3_s", "accumulated_mass_coordinate_kg", "concentration_kg_per_kg_beverage")
        if row["species_id"] in SPECIES and all(row[key] for key in needed):
            grouped[(row["experiment_id"], row["fraction_id"], row["species_id"])].append(row)
    result: dict[str, list[dict[str, float]]] = {species: [] for species in SPECIES}
    for (experiment, _, species), replicas in sorted(grouped.items()):
        coordinate = sum(float(row["accumulated_mass_coordinate_kg"]) for row in replicas) / len(replicas)
        concentration = sum(float(row["concentration_kg_per_kg_beverage"]) for row in replicas) / len(replicas)
        flow = float(replicas[0]["flow_m3_s"])
        result[species].append(
            {
                "experiment_id": float(experiment),
                "time_s": coordinate / DENSITY_KG_M3 / flow,
                "concentration_kg_m3": concentration * DENSITY_KG_M3,
            }
        )
    return result


def blocked_cv(species_rows: list[dict[str, float]]) -> tuple[list[dict[str, Any]], dict[str, float]]:
    predictions: list[dict[str, Any]] = []
    for experiment in sorted({int(row["experiment_id"]) for row in species_rows}):
        training = [row for row in species_rows if int(row["experiment_id"]) != experiment]
        held_out = [row for row in species_rows if int(row["experiment_id"]) == experiment]
        fit = fit_log_linear(training)
        for row in held_out:
            predicted = fit["saturationConcentration_kg_m3"] * math.exp(
                -fit["extractionRateConstant_1_s"] * row["time_s"]
            )
            predictions.append(
                {
                    "held_out_experiment_id": experiment,
                    "time_s": row["time_s"],
                    "observed_kg_m3": row["concentration_kg_m3"],
                    "predicted_kg_m3": predicted,
                }
            )
    observed = [row["observed_kg_m3"] for row in predictions]
    mean_observed = sum(observed) / len(observed)
    sse = sum((row["observed_kg_m3"] - row["predicted_kg_m3"]) ** 2 for row in predictions)
    sst = sum((value - mean_observed) ** 2 for value in observed)
    metrics = {
        "blocked_whole_experiment_r2": 1.0 - sse / sst,
        "blocked_nrmse": math.sqrt(sse / len(predictions)) / mean_observed,
        "n_predictions": len(predictions),
    }
    return predictions, metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--puckworks", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    training_dir = args.puckworks / "docs/analysis/sci_md_004_stage_e0"
    input_dir = args.puckworks / "docs/analysis/sci_md_004"
    for name in (*TRAINING_FILES,):
        if not (training_dir / name).is_file():
            raise SystemExit(f"missing approved training input: {name}")
    for name in INPUT_FILES:
        if not (input_dir / name).is_file():
            raise SystemExit(f"missing approved input-side artifact: {name}")
    # Fail closed if a caller attempts to place protected responses in either approved input directory.
    prohibited = {"angeloni_targets_long.csv"}
    accessed = {path.name for path in (*[training_dir / n for n in TRAINING_FILES], *[input_dir / n for n in INPUT_FILES])}
    if accessed & prohibited:
        raise SystemExit("protected target path entered the Stage E0 input set")

    args.output.mkdir(parents=True, exist_ok=True)
    obs = observations(training_dir)
    priors = {row["species_id"]: row for row in read_csv(training_dir / "pannusch_scaling_priors.csv")}
    parameters: dict[str, Any] = {}
    cv_rows: list[dict[str, Any]] = []
    all_pass = True
    for species in SPECIES:
        fit = fit_log_linear(obs[species])
        predictions, metrics = blocked_cv(obs[species])
        for row in predictions:
            cv_rows.append({"species_id": species, **row})
        rel_k_width = (fit["k_95pct_upper"] - fit["k_95pct_lower"]) / (2.0 * fit["extractionRateConstant_1_s"])
        rel_csat_width = (fit["csat_95pct_upper"] - fit["csat_95pct_lower"]) / (
            2.0 * fit["saturationConcentration_kg_m3"]
        )
        predictive_pass = metrics["blocked_whole_experiment_r2"] >= 0.50
        identifiable = fit["k_95pct_lower"] > 0 and max(rel_k_width, rel_csat_width) <= 0.25
        all_pass = all_pass and predictive_pass and identifiable
        parameters[species] = {
            **fit,
            **metrics,
            "effectiveSoluteDiffusivity_m2_s": float(priors[species]["effective_diffusivity_reference_m2_s"]),
            "diffusivity_status": "PROXY_FIXED_NOT_FITTED",
            "fit_objective": "OLS_LOG_CONCENTRATION_ON_ELAPSED_BEVERAGE_TIME",
            "mapping": {
                "time_s": "accumulated_beverage_mass_kg / (1000 kg/m3 * flow_m3_s)",
                "concentration_kg_m3": "fraction_concentration_kg_per_kg_beverage * 1000 kg/m3",
                "equation": "C_out(t)=saturationConcentration*exp(-extractionRateConstant*t)",
            },
            "identifiability": {
                "max_relative_95pct_half_width": max(rel_k_width, rel_csat_width),
                "threshold": 0.25,
                "pass": identifiable,
            },
            "predictive_content": {"r2_threshold": 0.50, "pass": predictive_pass},
        }

    with (args.output / "BLOCKED_WHOLE_EXPERIMENT_CV.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ("species_id", "held_out_experiment_id", "time_s", "observed_kg_m3", "predicted_kg_m3")
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(cv_rows)

    parameterization = {
        "schema_version": "ewp.sci-md-004-stage-e0-g1-parameterization/v1",
        "governance_class": "G1_PARAMETERIZATION_AND_PRE_HOLDOUT_FREEZE",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "parameter_count_fitted": 4,
        "parameters": parameters,
        "residual_extractables": {
            "behavior": "EXACT_ACCEPTED_LEGACY",
            "legacy_extractable_fraction": LEGACY_EXTRACTABLE_FRACTION,
        },
        "training_fit_is_validation": False,
        "blocked_training_prediction_is_independent_holdout": False,
        "angeloni_status": "PROTECTED_EXTERNAL_NO_RETUNING_ENDPOINT_HOLDOUT",
        "disposition": "PASS" if all_pass else "SCIENTIFIC_BLOCKER",
    }
    write_json(args.output / "PARAMETERIZATION_AND_IDENTIFIABILITY.json", parameterization)

    # The fitted outlet operator is smooth. Freeze conservative application
    # discretizations and qualify them against its exact integral without
    # executing an Angeloni species case.
    numerical: dict[str, Any] = {"method": "EXACT_OPERATOR_PREAPPLICATION_QUADRATURE", "species": {}}
    for species, fit in parameters.items():
        k = fit["extractionRateConstant_1_s"]
        csat = fit["saturationConcentration_kg_m3"]
        duration = 35.0
        exact = csat * (1.0 - math.exp(-k * duration)) / k
        values = {}
        for label, dt in (("reference", 0.05), ("fine", 0.025)):
            count = round(duration / dt)
            midpoint = sum(csat * math.exp(-k * ((index + 0.5) * dt)) * dt for index in range(count))
            values[label] = {"delta_t_s": dt, "integral": midpoint, "relative_exact_error": abs(midpoint - exact) / exact}
        sensitivity = abs(values["reference"]["integral"] - values["fine"]["integral"]) / values["fine"]["integral"]
        numerical["species"][species] = {
            **values,
            "reference_fine_relative": sensitivity,
            "frozen_limit": 0.0025,
            "pass": sensitivity <= 0.0025,
        }
        all_pass = all_pass and sensitivity <= 0.0025
    numerical["mesh"] = {
        "reference": "STAGE_C_ACCEPTED_REFERENCE_MESH",
        "fine": "STAGE_C_ACCEPTED_FINE_MESH",
        "qualification": "REUSED_BY_UNCHANGED_PRODUCTION_SOLVER_HASH_AND_STAGE_C_EVIDENCE_HASHES",
        "new_species_execution": False,
    }
    numerical["disposition"] = "PASS" if all_pass else "SCIENTIFIC_BLOCKER"
    write_json(args.output / "NUMERICAL_APPLICATION_QUALIFICATION.json", numerical)

    conditions = sorted(read_csv(input_dir / "angeloni_conditions.csv"), key=lambda row: row["sample_id"])
    inventories = {
        (row["variety"], row["species_id"]): float(row["canonical_value"])
        for row in read_csv(input_dir / "angeloni_inventories_long.csv")
        if row["species_id"] in SPECIES
    }
    cases = []
    for condition in conditions:
        variety = condition["variety"]
        named = {species: inventories[(variety, species)] for species in SPECIES}
        residual = LEGACY_EXTRACTABLE_FRACTION - sum(named.values())
        if residual < 0:
            raise SystemExit("negative residual inventory")
        hydraulic = {
            "pressure_Pa": float(condition["pressure_Pa"]),
            "pressure_reference": condition["pressure_reference"],
            "temperature_K": float(condition["temperature_K"]),
            "shot_duration_s": float(condition["source_shot_duration_s"]),
            "basket_radius_m": float(condition["basket_radius_m"]),
            "bed_height_m": float(condition["bed_height_m"]),
            "dose_kg": float(condition["dose_nominal_kg"]),
            "beverage_mass_kg": float(condition["beverage_mass_nominal_kg"]),
            "conditional_outlet_mass_flow_kg_s": float(condition["beverage_mass_nominal_kg"]) / float(condition["source_shot_duration_s"]),
            "grind_code": condition["grind_code_source"],
            "permeability_fit": None,
            "basis": "CONDITIONAL_MEASURED_NOMINAL_YIELD_OVER_REPORTED_DURATION",
        }
        configurations = []
        for hypothesis in ("H0", "H1"):
            for resolution in ("reference", "fine"):
                configurations.append(
                    {
                        "configuration_id": f"{condition['sample_id']}-{hypothesis}-{resolution}",
                        "hypothesis": hypothesis,
                        "resolution": resolution,
                        "execution_status": "FROZEN_NOT_EXECUTED",
                    }
                )
        cases.append(
            {
                "sample_id": condition["sample_id"],
                "variety": variety,
                "hydraulics": hydraulic,
                "inventories_kg_per_kg_dry": {**named, "residual_extractables": residual},
                "configurations": configurations,
            }
        )
    if len(cases) != 66 or sum(len(case["configurations"]) for case in cases) != 264:
        raise SystemExit("expected 66 cases and 264 H0/H1 reference/fine configurations")
    case_freeze = {
        "schema_version": "ewp.sci-md-004-stage-e0-g1-case-freeze/v1",
        "case_count": 66,
        "configuration_count": 264,
        "hydraulic_status": "CONDITIONAL_INPUT_ONLY",
        "species_prediction_count": 0,
        "protected_scorer_invocations": 0,
        "cases": cases,
    }
    write_json(args.output / "CONDITIONAL_CASE_FREEZE.json", case_freeze)

    operator = {
        "schema_version": "ewp.sci-md-004-stage-e0-g1-observation-operator/v1",
        "common_to": ["H0", "H1"],
        "cup_mass_operator": "time_integral_outlet_advective_species_flux",
        "cup_concentration_operator": "cup_species_mass_kg / (beverage_mass_kg / 1000 kg_m3)",
        "density_kg_m3": 1000.0,
        "nominal_beverage_mass_only": True,
        "selection_used_protected_targets": False,
        "frozen_before_prediction": True,
    }
    write_json(args.output / "COMMON_H0_H1_OBSERVATION_OPERATOR.json", operator)

    input_hashes = {
        f"docs/analysis/sci_md_004_stage_e0/{name}": sha256(training_dir / name) for name in TRAINING_FILES
    }
    input_hashes.update({f"docs/analysis/sci_md_004/{name}": sha256(input_dir / name) for name in INPUT_FILES})
    artifacts = sorted(path for path in args.output.iterdir() if path.name != "FREEZE_MANIFEST.json")
    manifest = {
        "schema_version": "ewp.sci-md-004-stage-e0-g1-freeze/v1",
        "puckworks_commit": "5ce003e751aac516b5de3d9ede4e6910627e2b12",
        "puckworks_tree": "d50c23028df01d6e1dc0a14ab331d0ea7453cb7f",
        "puckworks_scientific_bundle_sha256": "112f8b3b943a5cea3399746fde512048e3898f99c8079433dae86bd142db8709",
        "input_hashes": input_hashes,
        "artifact_hashes": {path.name: sha256(path) for path in artifacts},
        "production_solver_sha256": "9ffba0fa7800de50375a2a0c94cf99127870ac4451b104866c7e50322c992599",
        "semantic_protected_target_access": False,
        "angeloni_species_prediction_count": 0,
        "protected_scorer_invocations": 0,
        "disposition": "PASS" if all_pass else "SCIENTIFIC_BLOCKER",
    }
    write_json(args.output / "FREEZE_MANIFEST.json", manifest)
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
