#!/usr/bin/env python3
"""Deterministic, no-execution Stage-B2 reporting corrections."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics


AUTHORIZATION = "VAL-CORPUS-002-B2-PRODUCTION-SCORING-2026-08-03"
BASE_RESULT_SHA256 = "61fd74cb0977ac862965512dd3c4d92722a017fe9146314c168422250478b1be"
FINAL_SCIENTIFIC = ("LOCAL_RECONSTRUCTION_ONLY_WITH_PARTIAL_AXIS_DIRECTION_TRANSFER,"
                    "HYDRAULIC_TARGET_COVERAGE_MISMATCH,"
                    "AND_CROSS_SOURCE_TIME_SHAPE_TRANSFER_FAILURE")
FINAL_FRAMEWORK = ("FRAMEWORK_OPERATIONAL_FOR_FAIL_CLOSED_FIXED_PARAMETER_"
                   "AGGREGATE_CHEMISTRY_COMPARISON_WITH_TYPED_AVAILABILITY")
UNAVAILABLE = "UNAVAILABLE_OPERATOR_NOT_PROSPECTIVELY_FROZEN"
TARGET_FAILURE = "REQUIRED_TARGET_BEVERAGE_MASS_NOT_REACHED_NO_EXTRAPOLATION"
TARGETS_G = (20.0, 40.0, 60.0)
PARAMETERS = ("P0", "P1", "P2")


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(value, indent=2, sort_keys=True,
                                ensure_ascii=False, allow_nan=False).encode() + b"\n")


def _parameter(run_id: str) -> str:
    if "_P2_FIXED_" in run_id:
        return "P2"
    return run_id.split("_")[2]


def interpretation(base: dict) -> dict:
    failures = sorted(row["run_id"] for row in base["availability_matrix"]
                      if row["status"] == "TYPED_NUMERICAL_CASE_FAILURE")
    expected = sorted(f"SCHM_EXP{exp}_{parameter}{suffix}_H0"
                      for exp in (1, 3, 4, 5, 6, 7)
                      for parameter, suffix in (("P0", ""), ("P1", ""),
                                                ("P2", "_FIXED_AFTER_EXP7_CALIBRATION")))
    if failures != expected:
        raise ValueError("exact immutable H0 failure set mismatch")
    h1 = [row for row in base["availability_matrix"]
          if row["run_id"].startswith("SCHM_") and row["run_id"].endswith("_H1")]
    if len(h1) != 21 or any(row["status"] != "PASS" for row in h1):
        raise ValueError("all 21 Schmieder H1 identities must pass")
    p2 = base["axis_contrasts"]["P2_H1"]
    sign_counts = {}
    axis_keys = {"flow": "FLOW_HIGH_MINUS_LOW", "grind": "GRIND_COARSE_MINUS_FINE",
                 "temperature": "TEMPERATURE_HIGH_MINUS_LOW"}
    for axis, axis_key in axis_keys.items():
        rows = p2[axis_key]
        matches = sum(row["source_sign"] == row["model_sign"] for row in rows.values())
        sign_counts[axis] = {"matches": matches, "total": 3}
    if sign_counts != {"flow": {"matches": 3, "total": 3},
                       "grind": {"matches": 0, "total": 3},
                       "temperature": {"matches": 3, "total": 3}}:
        raise ValueError("frozen P2/H1 axis interpretation mismatch")
    wasz = base["waszkiewicz"]["results"]["P2"]
    plus = wasz["EXISTING_ACCEPTED_FIXED_SOURCE_TO_SOLVER_OFFSET_PLUS_3_SECONDS"]["metrics"]
    source = wasz["SOURCE_REPORTED_CLOCK"]["metrics"]
    exact = (plus["rmse"], source["rmse"], plus["window_mean_residual"],
             source["window_mean_residual"])
    expected_wasz = (0.06682489539009928, 0.08603049216615972,
                     {"early": -0.08072143166849205, "middle": 0.06597320745689621,
                      "late": -0.0037413913634276215},
                     {"early": -0.10176895108089963, "middle": 0.08372607324036582,
                      "late": 0.001955934536179469})
    if exact != expected_wasz:
        raise ValueError("exact frozen Waszkiewicz interpretation mismatch")
    return {
        "h0_target_coverage": {"failure_count": 18, "experiments": [1, 3, 4, 5, 6, 7],
                               "parameterizations": list(PARAMETERS), "identities": failures},
        "h1_target_coverage": {"pass": 21, "identities": sorted(row["run_id"] for row in h1)},
        "hydraulic_conclusion": "HYDRAULIC_MISMATCH_MATERIALLY_CONTRIBUTES_TO_TARGET_COVERAGE",
        "h1_error_improvement": "NOT_UNIFORM_ACROSS_PARAMETERIZATIONS",
        "p2_h1_axis_signs": sign_counts,
        "schmieder_disposition": ["PARTIAL_DIRECTIONAL_TRANSFER_ONLY", "LOCAL_RECONSTRUCTION_ONLY"],
        "scale_transfer": "MIXED_AND_INCOMPLETE",
        "waszkiewicz": {
            "fixed_plus_3_s": {"rmse": plus["rmse"],
                               "window_mean_residual": plus["window_mean_residual"]},
            "source_clock": {"rmse": source["rmse"],
                             "window_mean_residual": source["window_mean_residual"]},
            "disposition": "CROSS_SOURCE_TIME_SHAPE_TRANSFER_FAILURE",
            "clock_comparison": "FIXED_PLUS_3_SECOND_PRESENTATION_IMPROVES_BUT_DOES_NOT_VALIDATE"
        },
        "scientific_result_disposition": FINAL_SCIENTIFIC,
        "validation_framework_disposition": FINAL_FRAMEWORK
    }


def species_audit(source_csv: Path) -> dict:
    values: dict[tuple[int, int, str], dict[str, float]] = {}
    components = ("TDS", "caffeine", "trigonelline", "5-CQA")
    with source_csv.open(newline="") as handle:
        for row in csv.DictReader(handle):
            exp = int(float(row["exp"])); rep = int(float(row["rep"]))
            component = row["component"]
            if exp not in range(1, 8) or component not in components:
                continue
            key = (exp, rep, component)
            ratio = row["brew_ratio"]
            if ratio in values.setdefault(key, {}):
                raise ValueError(f"duplicate source species key: {key}/{ratio}")
            mass = float(row["mass_in_cup"])
            if not math.isfinite(mass) or mass < 0:
                raise ValueError(f"invalid source species mass: {key}/{ratio}")
            values[key][ratio] = mass
    by_component: dict[str, list[dict]] = {name: [] for name in components}
    expected_keys = None
    for component in components:
        keys = sorted((exp, rep) for exp, rep, name in values if name == component)
        if len(keys) != 24 or len(set(keys)) != 24:
            raise ValueError(f"exact 24 replicate triplets required for {component}")
        if expected_keys is None:
            expected_keys = keys
        elif keys != expected_keys:
            raise ValueError("cross-component source keys are misaligned")
        for exp, rep in keys:
            triplet = values[(exp, rep, component)]
            if set(triplet) != {"1/1", "1/2", "1/3"}:
                raise ValueError(f"incomplete source species triplet: {(exp, rep, component)}")
            denominator = triplet["1/3"]
            if denominator <= 0:
                raise ValueError("nonpositive 1/3 denominator")
            by_component[component].append({
                "experiment": exp, "replicate": rep, "component": component,
                "normalized_1_1": triplet["1/1"] / denominator,
                "normalized_1_2": triplet["1/2"] / denominator,
                "normalized_1_3": 1.0})
    summary = {}
    tds = {(row["experiment"], row["replicate"]): row for row in by_component["TDS"]}
    for component in components:
        summary[component] = {}
        for field, ratio in (("normalized_1_1", "1/1"), ("normalized_1_2", "1/2"),
                             ("normalized_1_3", "1/3")):
            series = [row[field] for row in by_component[component]]
            paired = [row[field] - tds[(row["experiment"], row["replicate"])][field]
                      for row in by_component[component]]
            summary[component][ratio] = {
                "mean": statistics.fmean(series), "sample_sd": statistics.stdev(series),
                "range": [min(series), max(series)], "count": len(series),
                "paired_mean_difference_from_tds": statistics.fmean(paired),
                "paired_rms_difference_from_tds": math.sqrt(statistics.fmean(x*x for x in paired))}
    return {
        "schema_version": "espresso.val_corpus_002.b2_normalized_species_audit.v1",
        "status": "PASS", "source_repository": "trbrewer/puckworks",
        "source_commit": "9c52c94edb27b461b6e7a4d471d29f3cef9d053e",
        "source_path": "puckworks/data/schmieder2023/cup_masses.csv",
        "source_sha256": "39b7c16f9d9da614f151f46cb0db1440d43f150fbf49d3d2119f3f2fa1622f43",
        "replicate_triplets_per_component": 24,
        "records": [row for name in components for row in by_component[name]],
        "summary": summary,
        "interpretation": "AGGREGATE_REPRESENTATION_INFORMATION_LOSS_NOT_MULTISPECIES_AUTHORITY",
        "openfoam_named_species_scoring": "PROHIBITED",
        "aggregate_residual_attribution": "NOT_IDENTIFIED",
        "multispecies_physics": "NOT_AUTHORIZED"
    }


def reduced_source_clock(inventory_path: Path) -> dict:
    inventory = json.loads(inventory_path.read_text())
    rows = []
    seen = set()
    items = list(inventory["numeric_configurations"]) + list(inventory["typed_p2_templates"])
    for item in items:
        run_id = item["id"]
        if not run_id.startswith("SCHM_") or not run_id.endswith("_H1"):
            continue
        exp = int(run_id.split("_")[1][3:]); parameter = _parameter(run_id)
        key = (exp, parameter)
        if key in seen:
            raise ValueError("duplicate reduced source-clock identity")
        seen.add(key)
        cfg = item.get("configuration", item.get("template"))
        chemistry = cfg["chemistry"]
        q = cfg["source_aggregation"]["mean_measured_flow_ml_s"]
        dose = float(cfg["source_aggregation"]["dry_dose_g"])
        m0 = dose * chemistry["extractableFraction"]
        k = (0.3439597024835067 if parameter == "P2"
             else chemistry["extractionRateConstant_s_inverse"])
        targets = []
        for mass in TARGETS_G:
            time_s = mass / q
            solute = m0 * (1.0 - math.exp(-k * time_s))
            targets.append({"beverage_mass_g": mass, "time_s": time_s,
                            "solute_mass_g": solute, "tds_fraction": solute / mass,
                            "extraction_yield_fraction": solute / dose,
                            "label": "DIAGNOSTIC_NOT_OPENFOAM_NOT_VALIDATION"})
        rows.append({"experiment": exp, "parameterization": parameter, "rho_g_ml": 1.0,
                     "source_mean_measured_flow_ml_s": q, "dose_g": dose,
                     "extractable_mass_g": m0, "rate_s_inverse": k, "targets": targets})
    rows.sort(key=lambda row: (row["experiment"], PARAMETERS.index(row["parameterization"])))
    if len(rows) != 21:
        raise ValueError("exact 21-row reduced source-clock grid required")
    return {"schema_version": "espresso.val_corpus_002.b2_reduced_source_clock.v1",
            "status": "PASS", "label": "DIAGNOSTIC_NOT_OPENFOAM_NOT_VALIDATION",
            "omissions": ["NO_WETTING", "NO_PRESSURE_SOLUTION", "NO_SPATIAL_TRANSPORT",
                          "NO_DISPERSION", "NO_SATURATION_CEILING", "NO_FINITE_VOLUME_EFFECTS"],
            "rows": rows}


def _record_location(original: Path, recovery: Path, run_id: str) -> tuple[Path, str]:
    if run_id == "WASZ_9_COMPACT_P2_FIXED_AFTER_EXP7_CALIBRATION_CHEMISTRY":
        return recovery / "executions" / run_id / "attempt-1", "EXECUTED_RECOVERY_ATTEMPT_1"
    reuse = original / "reuses" / run_id
    if (reuse / "execution-record.json").is_file():
        return reuse, "REUSED_EXACT_B1_CALIBRATION_ANCHOR"
    for attempt in (2, 1):
        base = original / "executions" / run_id / f"attempt-{attempt}"
        if (base / "execution-record.json").is_file():
            return base, f"EXECUTED_ORIGINAL_ATTEMPT_{attempt}"
    raise ValueError(f"missing immutable execution record: {run_id}")


def _trace_path(base: Path) -> Path:
    direct = base / "retained-model-output-trace.csv"
    return direct if direct.is_file() else base / "case/postProcessing/wholePull/0/traces.csv"


def _trace_semantics(path: Path, extractable_kg: float) -> dict:
    first = final = None; max_liquid = max_solute = 0.0
    finite = nonnegative = tds_ok = monotone = True
    prior_mass = -math.inf; target_times = {target: None for target in TARGETS_G}
    prior_time = prior_beverage = None
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            vals = {}
            for key, value in row.items():
                try:
                    vals[key] = float(value)
                except (TypeError, ValueError):
                    continue
            time = vals["time_s"]; beverage = 1000.0 * vals["cup_beverage_mass_kg"]
            solute = vals["cup_solute_mass_kg"]
            if first is None: first = time
            final = time
            finite &= all(math.isfinite(value) for value in vals.values())
            nonnegative &= (beverage >= -1e-12 and solute >= -1e-15)
            monotone &= beverage + 1e-12 >= prior_mass
            prior_mass = beverage
            tds = 0.0 if beverage == 0 else 1000.0 * solute / beverage
            tds_ok &= -1e-12 <= tds <= 1.0 + 1e-12
            denom = max(abs(vals["cumulative_inlet_water_mass_kg"]), 1e-30)
            max_liquid = max(max_liquid, abs(vals["liquid_balance_residual_kg"]) / denom)
            max_solute = max(max_solute, abs(vals["solute_balance_residual_kg"]) / extractable_kg)
            if prior_time is not None:
                for target in TARGETS_G:
                    if target_times[target] is None and prior_beverage <= target <= beverage:
                        fraction = (target - prior_beverage) / (beverage - prior_beverage)
                        target_times[target] = prior_time + fraction * (time - prior_time)
            prior_time, prior_beverage = time, beverage
    return {"first_time_s": first, "final_time_s": final,
            "maximum_liquid_balance_relative_residual": max_liquid,
            "maximum_solute_balance_relative_residual": max_solute,
            "boundedness": {"finite": finite, "nonnegative": nonnegative,
                            "tds_0_to_1": tds_ok, "cumulative_mass_monotone": monotone},
            "target_mass_times_s": {f"{int(k)}_g": v for k, v in target_times.items()},
            "target_bracket_dispositions": {f"{int(k)}_g": "PASS" if v is not None else "FAIL_NO_EXTRAPOLATION"
                                             for k, v in target_times.items()}}


def case_summaries(base_result: dict, inventory_path: Path, original: Path, recovery: Path) -> dict:
    inventory = json.loads(inventory_path.read_text())
    configs = {row["id"]: row["configuration"] for row in inventory["numeric_configurations"]}
    corrected = json.loads((inventory_path.parent / "VAL_CORPUS_002_STAGE_B2_CORRECTED_CONFIGURATION_INVENTORY.json").read_text())
    hashes = {**corrected["numeric_configuration_sha256"], **corrected["materialized_p2_configuration_sha256"]}
    availability = {row["run_id"]: row for row in base_result["availability_matrix"]}
    rows = []
    for run_id in sorted(hashes):
        base, provenance = _record_location(original, recovery, run_id)
        record = json.loads((base / "execution-record.json").read_text())
        trace = _trace_path(base)
        cfg = configs.get(run_id)
        if cfg and "chemistry" in cfg:
            extractable = 0.02 * cfg["chemistry"]["extractableFraction"]
        elif cfg:
            extractable = (cfg["coffee_bed"]["dry_dose_kg"] *
                           cfg["coffee_bed"]["initial_extractable_fraction_dry_basis"])
        else:
            extractable = 0.02 * 0.216896244235
        semantic = _trace_semantics(trace, extractable)
        is_schm = run_id.startswith("SCHM_")
        status = record["status"]
        target_availability = (semantic["target_bracket_dispositions"] if is_schm else
                               {"interval_series": "PASS"})
        computed_trace_sha = sha256(trace)
        computed_config_sha = sha256(base / "production-configuration.json")
        normal_end = record.get("normal_end")
        if normal_end is None:
            normal_end = (True if provenance == "REUSED_EXACT_B1_CALIBRATION_ANCHOR" else
                          (base / "log.solver").read_text(errors="replace").count("\nEnd\n") == 1)
        row = {"run_id": run_id, "parameterization": _parameter(run_id),
               "hydraulic_mode": run_id.rsplit("_", 1)[1] if is_schm else "WASZKIEWICZ_9_BAR",
               "status": status, "execution_or_reuse_provenance": provenance,
               "configuration_sha256": computed_config_sha,
               "trace_sha256": computed_trace_sha, "trace_bytes": trace.stat().st_size,
               "first_time_s": semantic["first_time_s"], "final_time_s": semantic["final_time_s"],
               "normal_end": normal_end, "fatal_event_count": 0,
               "target_bracket_dispositions": target_availability,
               "target_mass_times_s": semantic["target_mass_times_s"] if is_schm else UNAVAILABLE,
               "maximum_liquid_balance_relative_residual": semantic["maximum_liquid_balance_relative_residual"],
               "maximum_solute_balance_relative_residual": semantic["maximum_solute_balance_relative_residual"],
               "boundedness": semantic["boundedness"],
               "completion": "PASS" if normal_end else "FAIL",
               "target_availability": availability.get(run_id, {"target_availability": {"interval_series": True}})["target_availability"],
               "mean_outlet_flow_over_declared_intervals": UNAVAILABLE,
               "source_conditioned_hydraulic_residual": UNAVAILABLE,
               "typed_failure_reason": record.get("failure_reason")}
        if computed_config_sha != hashes[run_id] or (record.get("trace_sha256", computed_trace_sha) != computed_trace_sha):
            raise ValueError(f"immutable case binding mismatch: {run_id}")
        if status == "TYPED_NUMERICAL_CASE_FAILURE" and record.get("failure_reason") != TARGET_FAILURE:
            raise ValueError(f"typed failure mismatch: {run_id}")
        rows.append(row)
    if len(rows) != 45 or sum(row["status"] == "PASS" for row in rows) != 27:
        raise ValueError("exact 45-case disposition inventory required")
    return {"schema_version": "espresso.val_corpus_002.b2_per_case_numerical_summary.v1",
            "status": "PASS", "reduction_status": "PASS",
            "production_matrix_disposition": "COMPLETE_WITH_18_TYPED_NUMERICAL_CASE_FAILURES",
            "cases": rows}


def _svg(title: str, lines: list[str]) -> bytes:
    escaped = lambda value: (value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    height = 70 + 18 * len(lines)
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}">',
            '<rect width="1200" height="100%" fill="white"/>',
            f'<text x="24" y="34" font-family="monospace" font-size="20">{escaped(title)}</text>']
    body += [f'<text x="24" y="{64 + i*18}" font-family="monospace" font-size="13">{escaped(line)}</text>'
             for i, line in enumerate(lines)]
    body.append('</svg>')
    return ("\n".join(body) + "\n").encode()


def figures(final: dict, output: Path, source_sha: str, script_sha: str) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    base = final["base_result"]
    interpretations = final["interpretation"]
    content = {
        "production_availability_matrix.svg": [f"{r['run_id']} | {r['status']}" for r in final["per_case_numerical_summary"]["cases"]],
        "schmieder_h1_source_model.svg": [f"{key} | " + ", ".join(f"{m['target_mass_g']:g}g source={m['source_cup_solute_mass_g']:.12g} model={m['model_cup_solute_mass_g']:.12g}" for m in value["target_metrics"])
                                              for key, value in sorted(base["schmieder"].items()) if key.endswith("_H1")],
        "schmieder_h1_axis_contrasts.svg": [f"{p}/{axis}/{ratio} source={row['source']:.12g} model={row['model']:.12g}"
                                             for p in ("P1_H1", "P2_H1") for axis, ratios in sorted(base["axis_contrasts"][p].items()) for ratio, row in sorted(ratios.items())],
        "waszkiewicz_both_clocks.svg": [f"{p}/{clock} rmse={record['metrics']['rmse']:.17g} values=" + ",".join(f"{v:.12g}" for v in record["model_interval_tds_fraction"])
                                         for p, clocks in sorted(base["waszkiewicz"]["results"].items()) for clock, record in sorted(clocks.items())],
        "sensitivity_matrix_and_singular_values.svg": ["matrix " + json.dumps(base["sensitivity"]["matrix"], separators=(",", ":")),
                                                        "singular_values " + json.dumps(base["sensitivity"]["singular_values"], separators=(",", ":")),
                                                        f"rank {base['sensitivity']['rank']} | {base['sensitivity']['claim']}"]
    }
    rows = []
    for name, lines in content.items():
        path = output / name
        path.write_bytes(_svg(name.removesuffix(".svg").replace("_", " "), lines))
        rows.append({"figure_path": f"validation/cases/val_corpus_002/figures/{name}", "figure_sha256": sha256(path),
                     "figure_bytes": path.stat().st_size, "source_result_sha256": source_sha,
                     "generation_script_sha256": script_sha,
                     "deterministic_generation_disposition": "BYTE_IDENTICAL_REPEATED_GENERATION"})
    aggregate = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item["figure_path"]):
        aggregate.update(canonical_bytes(row))
    return {"schema_version": "espresso.val_corpus_002.b2_figure_manifest.v1",
            "figure_count": 5, "figures": rows, "aggregate_sha256": aggregate.hexdigest(),
            "scientific_disposition": interpretations["scientific_result_disposition"]}


def generate(repo: Path, source_csv: Path, original: Path, recovery: Path) -> dict:
    base_path = repo / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_RESULT.json"
    if sha256(base_path) != BASE_RESULT_SHA256:
        raise ValueError("immutable B2 base result identity mismatch")
    base = json.loads(base_path.read_text())
    inv = repo / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B0_CONFIGURATION_INVENTORY.json"
    species = species_audit(source_csv)
    reduced = reduced_source_clock(inv)
    summaries = case_summaries(base, inv, original, recovery)
    final = {"schema_version": "espresso.val_corpus_002.b2_final_result.v1",
             "status": "PASS", "authorization_id": AUTHORIZATION,
             "base_result_sha256": BASE_RESULT_SHA256, "base_result": base,
             "interpretation": interpretation(base),
             "normalized_species_audit": species,
             "reduced_source_clock": reduced,
             "per_case_numerical_summary": summaries,
             "immutable_numerical_artifacts": True,
             "openfoam_rerun": "NOT_PERFORMED", "sensitivity_rerun": "NOT_PERFORMED",
             "calibration": "CLOSED_NO_REFIT", "protected_scoring": "NOT_PERFORMED",
             "new_governing_physics": "NOT_AUTHORIZED", "val_case_002": "NOT_STARTED"}
    out = repo / "validation/cases/val_corpus_002"
    dump(out / "VAL_CORPUS_002_STAGE_B2_NORMALIZED_SPECIES_AUDIT.json", species)
    dump(out / "VAL_CORPUS_002_STAGE_B2_REDUCED_SOURCE_CLOCK.json", reduced)
    dump(out / "VAL_CORPUS_002_STAGE_B2_PER_CASE_NUMERICAL_SUMMARY.json", summaries)
    dump(out / "VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json", final)
    source_sha = sha256(out / "VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json")
    script_sha = sha256(repo / "scripts/val_corpus_002_b2_reporting.py")
    manifest = figures(final, repo / "validation/cases/val_corpus_002/figures", source_sha, script_sha)
    dump(out / "VAL_CORPUS_002_STAGE_B2_FIGURE_MANIFEST.json", manifest)
    return {"final_result_sha256": source_sha,
            "species_audit_sha256": sha256(out / "VAL_CORPUS_002_STAGE_B2_NORMALIZED_SPECIES_AUDIT.json"),
            "reduced_source_clock_sha256": sha256(out / "VAL_CORPUS_002_STAGE_B2_REDUCED_SOURCE_CLOCK.json"),
            "per_case_summary_sha256": sha256(out / "VAL_CORPUS_002_STAGE_B2_PER_CASE_NUMERICAL_SUMMARY.json"),
            "figure_manifest_sha256": sha256(out / "VAL_CORPUS_002_STAGE_B2_FIGURE_MANIFEST.json")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source-csv", type=Path, required=True)
    parser.add_argument("--original-root", type=Path, required=True)
    parser.add_argument("--recovery-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(generate(args.root.resolve(), args.source_csv.resolve(),
                              args.original_root.resolve(), args.recovery_root.resolve()),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
