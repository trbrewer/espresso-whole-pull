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
LINEAGE = {
    "evidence_class": "POST_FIT_DERIVED_FROM_FITTED_KINETICS",
    "independent_measurement": False,
    "allowed_use": "SOURCE_LINEAGE_RECONSTRUCTION_OR_DERIVED_METRIC_ONLY",
    "prohibited_use": "INDEPENDENT_VALIDATION_TARGET",
    "required_citation": ("docs/validation/"
                          "VAL_PUCKWORKS_001_BASE_TEMPORAL_CROSS_VALIDATION_AND_CUP_MASS_LINEAGE.md"),
}


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
        "source_lineage": {**LINEAGE,
                           "audit_role": "SOURCE_LINEAGE_DIAGNOSTIC_OF_POST_FIT_DERIVED_QUANTITIES",
                           "uncertainty_role": "POST_FIT_DERIVED_REPLICATE_SPREAD_NOT_INDEPENDENT_MEASUREMENT_UNCERTAINTY"},
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
    from val_corpus_002_protocol import interpolate_fixed_mass

    first = final = None
    max_liquid = max_solute = 0.0
    finite = nonnegative = tds_ok = beverage_monotone = solute_monotone = True
    prior_time = prior_beverage = prior_solute = None
    samples: list[tuple[float, float, float]] = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            vals = {}
            for key, value in row.items():
                try:
                    vals[key] = float(value)
                except (TypeError, ValueError):
                    continue
            required = {"time_s", "cup_beverage_mass_kg", "cup_solute_mass_kg",
                        "cumulative_inlet_water_mass_kg", "liquid_balance_residual_kg",
                        "solute_balance_residual_kg"}
            if not required <= vals.keys():
                raise ValueError(f"retained trace missing required columns: {path}")
            time = vals["time_s"]
            beverage_kg = vals["cup_beverage_mass_kg"]
            solute = vals["cup_solute_mass_kg"]
            if first is None: first = time
            final = time
            finite &= all(math.isfinite(value) for value in vals.values())
            nonnegative &= beverage_kg >= -1e-15 and solute >= -1e-15
            if prior_time is not None:
                if time <= prior_time:
                    raise ValueError(f"retained trace time is not strictly increasing: {path}")
                beverage_monotone &= beverage_kg + 1e-12 >= prior_beverage
                solute_monotone &= solute + 1e-12 >= prior_solute
            tds = 0.0 if beverage_kg == 0 else solute / beverage_kg
            tds_ok &= -1e-12 <= tds <= 1.0 + 1e-12
            denom = max(abs(vals["cumulative_inlet_water_mass_kg"]), 1e-30)
            max_liquid = max(max_liquid, abs(vals["liquid_balance_residual_kg"]) / denom)
            max_solute = max(max_solute, abs(vals["solute_balance_residual_kg"]) / extractable_kg)
            samples.append((time, beverage_kg, solute))
            prior_time, prior_beverage, prior_solute = time, beverage_kg, solute
    if not samples or not finite or not nonnegative or not beverage_monotone or not solute_monotone or not tds_ok:
        raise ValueError(f"retained trace fails reporting boundedness gates: {path}")
    target_times: dict[float, float | None] = {}
    target_solute: dict[float, float | None] = {}
    for target_g in TARGETS_G:
        target_kg = target_g / 1000.0
        try:
            target_solute[target_g] = interpolate_fixed_mass(samples, target_kg)
        except ValueError as exc:
            if "extrapolation" not in str(exc) and "not bracketed" not in str(exc):
                raise
            target_solute[target_g] = None
        target_times[target_g] = None
        for (t0, m0, _), (t1, m1, _) in zip(samples, samples[1:]):
            if abs(m0 - target_kg) <= 1e-12:
                target_times[target_g] = t0
                break
            if m0 < target_kg < m1 and m1 - m0 > 1e-12:
                target_times[target_g] = t0 + (target_kg - m0) * (t1 - t0) / (m1 - m0)
                break
        if target_times[target_g] is None and abs(samples[-1][1] - target_kg) <= 1e-12:
            target_times[target_g] = samples[-1][0]
    return {"first_time_s": first, "final_time_s": final,
            "maximum_liquid_balance_relative_residual": max_liquid,
            "maximum_solute_balance_relative_residual": max_solute,
            "boundedness": {"finite": finite, "nonnegative": nonnegative,
                            "tds_0_to_1": tds_ok,
                            "cumulative_beverage_mass_monotone": beverage_monotone,
                            "cumulative_solute_mass_monotone": solute_monotone},
            "target_mass_times_s": {f"{int(k)}_g": v for k, v in target_times.items()},
            "target_solute_mass_kg": {f"{int(k)}_g": v for k, v in target_solute.items()},
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
        numerical_bracketing = (semantic["target_bracket_dispositions"] if is_schm else
                                 {"interval_series": "PASS"})
        computed_trace_sha = sha256(trace)
        computed_config_sha = sha256(base / "production-configuration.json")
        normal_end = record.get("normal_end")
        fatal_event_count = 0
        if normal_end is None:
            normal_end = record.get("solver_exit_code") == 0 if provenance == "REUSED_EXACT_B1_CALIBRATION_ANCHOR" else None
        log_path = base / "log.solver"
        if log_path.is_file():
            log_text = log_path.read_text(errors="replace")
            normal_end = log_text.count("\nEnd\n") == 1
            fatal_event_count = sum(log_text.count(marker) for marker in
                                    ("FOAM FATAL", "Floating point exception"))
        expected_end = 90.0 if is_schm else 63.0
        if (abs(semantic["final_time_s"] - expected_end) > 1e-9 or not normal_end or
                fatal_event_count or record.get("solver_exit_code") not in (None, 0)):
            raise ValueError(f"immutable case does not have normal terminal completion: {run_id}")
        if semantic["maximum_liquid_balance_relative_residual"] > 1e-8 or semantic["maximum_solute_balance_relative_residual"] > 1e-8:
            raise ValueError(f"immutable case fails conservation: {run_id}")
        governed = availability.get(run_id, {"target_availability": {"interval_series": True}})["target_availability"]
        row = {"run_id": run_id, "parameterization": _parameter(run_id),
               "hydraulic_mode": run_id.rsplit("_", 1)[1] if is_schm else "WASZKIEWICZ_9_BAR",
               "status": status, "execution_or_reuse_provenance": provenance,
               "configuration_sha256": computed_config_sha,
               "trace_sha256": computed_trace_sha, "trace_bytes": trace.stat().st_size,
               "first_time_s": semantic["first_time_s"], "final_time_s": semantic["final_time_s"],
               "normal_end": normal_end, "fatal_event_count": fatal_event_count,
               "numerical_target_bracketing": numerical_bracketing,
               "target_mass_times_s": semantic["target_mass_times_s"] if is_schm else UNAVAILABLE,
               "maximum_liquid_balance_relative_residual": semantic["maximum_liquid_balance_relative_residual"],
               "maximum_solute_balance_relative_residual": semantic["maximum_solute_balance_relative_residual"],
               "boundedness": semantic["boundedness"],
               "completion": "PASS" if normal_end else "FAIL",
               "governed_case_metric_availability": governed,
               "governed_case_reason": ("COMPLETE_20_40_60_VECTOR_REQUIRED_CASE_TYPED_FAILURE"
                                          if status == "TYPED_NUMERICAL_CASE_FAILURE" else "NUMERICAL_GATES_PASS"),
               "mean_outlet_flow_over_declared_intervals": UNAVAILABLE,
               "source_conditioned_hydraulic_residual": UNAVAILABLE,
               "typed_failure_reason": record.get("failure_reason")}
        if computed_config_sha != hashes[run_id] or (record.get("trace_sha256", computed_trace_sha) != computed_trace_sha):
            raise ValueError(f"immutable case binding mismatch: {run_id}")
        if status == "TYPED_NUMERICAL_CASE_FAILURE" and record.get("failure_reason") != TARGET_FAILURE:
            raise ValueError(f"typed failure mismatch: {run_id}")
        if status == "TYPED_NUMERICAL_CASE_FAILURE":
            if any(governed.values()) or numerical_bracketing["60_g"] != "FAIL_NO_EXTRAPOLATION":
                raise ValueError(f"typed case availability is not fail closed: {run_id}")
        elif is_schm and (not all(governed.values()) or not all(v == "PASS" for v in numerical_bracketing.values())):
            raise ValueError(f"passing case lacks complete governed target vector: {run_id}")
        rows.append(row)
    if len(rows) != 45 or sum(row["status"] == "PASS" for row in rows) != 27:
        raise ValueError("exact 45-case disposition inventory required")
    return {"schema_version": "espresso.val_corpus_002.b2_per_case_numerical_summary.v1",
            "status": "PASS", "reduction_status": "PASS",
            "production_matrix_disposition": "COMPLETE_WITH_18_TYPED_NUMERICAL_CASE_FAILURES",
            "source_lineage": {**LINEAGE,
                               "comparison_role": "COMPARISON_TO_POST_FIT_DERIVED_SOURCE_QUANTITIES"},
            "cases": rows}


def _esc(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _canvas(title: str, body: list[str], caption: str) -> bytes:
    rows = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="620" viewBox="0 0 1000 620">',
            '<rect x="0" y="0" width="1000" height="620" fill="white"/>',
            f'<title>{_esc(title)}</title>', f'<desc>{_esc(caption)}</desc>',
            f'<text x="40" y="34" font-family="sans-serif" font-size="20">{_esc(title)}</text>']
    rows.extend(body)
    rows.append(f'<text x="40" y="602" font-family="sans-serif" font-size="11">{_esc(caption)}</text>')
    rows.append('</svg>')
    return ("\n".join(rows) + "\n").encode()


def _axes(xlabel: str, ylabel: str) -> list[str]:
    return ['<line x1="90" y1="540" x2="950" y2="540" stroke="black"/>',
            '<line x1="90" y1="70" x2="90" y2="540" stroke="black"/>',
            f'<text x="480" y="575" font-family="sans-serif" font-size="13">{_esc(xlabel)}</text>',
            f'<text x="18" y="300" font-family="sans-serif" font-size="13" transform="rotate(-90 18 300)">{_esc(ylabel)}</text>']


def _polyline(points: list[tuple[float, float]], color: str, width: int = 2) -> str:
    encoded = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
    return f'<polyline points="{encoded}" fill="none" stroke="{color}" stroke-width="{width}"/>'


def figures(final: dict, base: dict, output: Path, source_sha: str, script_sha: str) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    interpretations = final["interpretation"]
    caveat = ("cup_masses.csv: post-fit derived source quantities, not independent measurements; "
              "see VAL_PUCKWORKS_001 lineage authority")
    content: dict[str, bytes] = {}

    cases = final["per_case_numerical_summary"]["cases"]
    body = []
    for index, row in enumerate(cases):
        col, grid_row = index % 9, index // 9
        x, y = 115 + col * 90, 115 + grid_row * 75
        color = "#2c7fb8" if row["status"] == "PASS" else "#d95f0e"
        body.append(f'<rect x="{x}" y="{y}" width="70" height="50" fill="{color}" stroke="black"/>')
        body.append(f'<text x="{x + 35}" y="{y + 30}" text-anchor="middle" font-family="sans-serif" font-size="10" fill="white">{index + 1}</text>')
    body += ['<rect x="120" y="520" width="18" height="18" fill="#2c7fb8"/><text x="145" y="534" font-family="sans-serif" font-size="12">PASS (27)</text>',
             '<rect x="270" y="520" width="18" height="18" fill="#d95f0e"/><text x="295" y="534" font-family="sans-serif" font-size="12">typed target failure (18)</text>']
    content["production_availability_matrix.svg"] = _canvas("Production availability: 45 governed identities", body,
                                                              "27 PASS; 18 immutable typed target-coverage failures; no imputation")

    body = _axes("target beverage mass (g)", "cup solute mass (g)")
    colors = {"P0": "#1b9e77", "P1": "#7570b3", "P2": "#d95f02"}
    for key, value in sorted(base["schmieder"].items()):
        if not key.endswith("_H1"):
            continue
        parameter = _parameter(key)
        source_pts = [(90 + (m["target_mass_g"] - 20) / 40 * 860,
                       540 - m["source_cup_solute_mass_g"] / 5.2 * 450) for m in value["target_metrics"]]
        model_pts = [(90 + (m["target_mass_g"] - 20) / 40 * 860,
                      540 - m["model_cup_solute_mass_g"] / 5.2 * 450) for m in value["target_metrics"]]
        body.append(_polyline(source_pts, "#555555", 1))
        body.append(_polyline(model_pts, colors[parameter], 2))
        for x, y in model_pts:
            radius = 5 if "EXP7_P2" in key else 3
            body.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{radius}" fill="{colors[parameter]}"/>')
    body.append('<text x="710" y="88" font-family="sans-serif" font-size="12">P0 green; P1 purple; P2 orange; gray source</text>')
    body.append('<text x="710" y="106" font-family="sans-serif" font-size="12">large P2 marks: Experiment-7 calibration anchor</text>')
    content["schmieder_h1_source_model.svg"] = _canvas("Schmieder H1 source/model cup-solute mass", body, caveat)

    body = _axes("axis / brew-ratio group", "contrast (g cup solute)")
    contrast_rows = []
    for p in ("P1_H1", "P2_H1"):
        for axis, ratios in sorted(base["axis_contrasts"][p].items()):
            for ratio, row in sorted(ratios.items()):
                contrast_rows.append((p, axis, ratio, row))
    scale = max(abs(row[k]) for *_, row in contrast_rows for k in ("source", "model")) or 1.0
    for i, (p, axis, ratio, row) in enumerate(contrast_rows):
        x = 110 + i * 45
        y0 = 305
        for offset, key, color in ((-6, "source", "#333333"), (6, "model", "#e6550d" if p == "P2_H1" else "#756bb1")):
            y = y0 - row[key] / scale * 200
            body.append(f'<line x1="{x+offset}" y1="{y0}" x2="{x+offset}" y2="{y:.3f}" stroke="{color}" stroke-width="5"/>')
        body.append(f'<text x="{x}" y="560" transform="rotate(60 {x} 560)" font-family="sans-serif" font-size="8">{_esc(p[:2]+"/"+axis.split("_")[0]+"/"+ratio)}</text>')
    body.append('<line x1="90" y1="305" x2="950" y2="305" stroke="#888" stroke-dasharray="4 3"/>')
    body.append('<text x="680" y="90" font-family="sans-serif" font-size="12">source black; P1 purple; P2 orange</text>')
    content["schmieder_h1_axis_contrasts.svg"] = _canvas("H1 flow, grind, and temperature contrasts", body, caveat)

    body = _axes("5-second interval index (two fixed clock panels)", "interval TDS fraction")
    source = base["waszkiewicz"]["source_tds_fraction"]
    max_tds = max(source + [v for clocks in base["waszkiewicz"]["results"].values() for rec in clocks.values() for v in rec["model_interval_tds_fraction"]])
    clock_names = ("SOURCE_REPORTED_CLOCK", "EXISTING_ACCEPTED_FIXED_SOURCE_TO_SOLVER_OFFSET_PLUS_3_SECONDS")
    colors = {"P0": "#1b9e77", "P1": "#7570b3", "P2": "#d95f02"}
    for panel, clock in enumerate(clock_names):
        xbase = 100 + panel * 430
        source_pts = [(xbase + i * 32, 530 - value / max_tds * 400) for i, value in enumerate(source)]
        body.append(_polyline(source_pts, "#222", 2))
        for x, y in source_pts: body.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="3" fill="#222"/>')
        for parameter in PARAMETERS:
            values = base["waszkiewicz"]["results"][parameter][clock]["model_interval_tds_fraction"]
            body.append(_polyline([(xbase + i * 32, 530 - value / max_tds * 400) for i, value in enumerate(values)], colors[parameter], 2))
        body.append(f'<text x="{xbase}" y="92" font-family="sans-serif" font-size="11">{_esc(clock)}</text>')
    content["waszkiewicz_both_clocks.svg"] = _canvas("Waszkiewicz interval TDS: both frozen clocks", body,
                                                      "source points black; P0 green; P1 purple; P2 orange; no optimized shift")

    body = []
    matrix = base["sensitivity"]["matrix"]
    maximum = max(abs(v) for row in matrix for v in row)
    for r, row in enumerate(matrix):
        for c, value in enumerate(row):
            intensity = int(235 - 170 * abs(value) / maximum)
            color = f"rgb({intensity},{intensity},{255 if value >= 0 else 170})"
            x, y = 120 + c * 130, 120 + r * 110
            body.append(f'<rect x="{x}" y="{y}" width="110" height="90" fill="{color}" stroke="black"/>')
            body.append(f'<text x="{x+55}" y="{y+50}" text-anchor="middle" font-family="sans-serif" font-size="12">{value:.4f}</text>')
    singular = base["sensitivity"]["singular_values"]
    for i, value in enumerate(singular):
        h = value / max(singular) * 300
        x = 700 + i * 80
        body.append(f'<rect x="{x}" y="{500-h:.3f}" width="45" height="{h:.3f}" fill="#3182bd"/>')
        body.append(f'<text x="{x+22}" y="520" text-anchor="middle" font-family="sans-serif" font-size="11">s{i+1}</text>')
    body.append(f'<text x="650" y="100" font-family="sans-serif" font-size="13">singular values; rank {base["sensitivity"]["rank"]}</text>')
    body.append('<text x="650" y="550" font-family="sans-serif" font-size="12">equifinality warning; NOT_STRUCTURAL_IDENTIFIABILITY</text>')
    content["sensitivity_matrix_and_singular_values.svg"] = _canvas("Sensitivity elasticity matrix and singular values", body,
                                                                     "3 outputs × 4 parameters; finite-range diagnostic")
    rows = []
    for name, payload in content.items():
        path = output / name
        path.write_bytes(payload)
        rows.append({"figure_path": f"validation/cases/val_corpus_002/figures/{name}", "figure_sha256": sha256(path),
                     "figure_bytes": path.stat().st_size, "source_result_sha256": source_sha,
                     "generation_script_sha256": script_sha,
                     "source_lineage": ({**LINEAGE,
                                         "comparison_role": "COMPARISON_TO_POST_FIT_DERIVED_SOURCE_QUANTITIES"}
                                        if name.startswith("schmieder_") else None),
                     "deterministic_generation_disposition": "BYTE_IDENTICAL_REPEATED_GENERATION"})
    aggregate = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item["figure_path"]):
        aggregate.update(canonical_bytes(row))
    return {"schema_version": "espresso.val_corpus_002.b2_figure_manifest.v1",
            "figure_count": 5, "figures": rows, "aggregate_sha256": aggregate.hexdigest(),
            "scientific_disposition": interpretations["scientific_result_disposition"]}


def validate_final_package(repo: Path, value: dict | None = None) -> dict:
    """Validate the closed final record and every content-addressed nested record."""
    import jsonschema

    root = repo / "validation/cases/val_corpus_002"
    final = value or json.loads((root / "VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json").read_text())
    schema = json.loads((root / "VAL_CORPUS_002_STAGE_B2_FINAL_RESULT_SCHEMA.json").read_text())
    jsonschema.Draft202012Validator(schema).validate(final)
    loaded = {}
    for name, reference in final["records"].items():
        path = repo / reference["path"]
        if not path.is_file() or sha256(path) != reference["sha256"]:
            raise ValueError(f"final nested record hash mismatch: {name}")
        loaded[name] = json.loads(path.read_text())
    species = loaded["normalized_species_audit"]
    if species.get("replicate_triplets_per_component") != 24 or len(species.get("records", [])) != 96:
        raise ValueError("normalized species audit is incomplete")
    for component in ("TDS", "caffeine", "trigonelline", "5-CQA"):
        rows = [row for row in species["records"] if row["component"] == component]
        if len(rows) != 24:
            raise ValueError(f"normalized species component count mismatch: {component}")
    reduced = loaded["reduced_source_clock"]
    if len(reduced.get("rows", [])) != 21 or any(len(row.get("targets", [])) != 3 for row in reduced["rows"]):
        raise ValueError("reduced source-clock grid is incomplete")
    summary = loaded["per_case_numerical_summary"]
    cases = summary.get("cases", [])
    if len(cases) != 45 or len({row["run_id"] for row in cases}) != 45:
        raise ValueError("per-case numerical summary must contain 45 unique identities")
    passed = [row for row in cases if row["status"] == "PASS"]
    failed = [row for row in cases if row["status"] == "TYPED_NUMERICAL_CASE_FAILURE"]
    if len(passed) != 27 or len(failed) != 18:
        raise ValueError("per-case numerical disposition counts mismatch")
    for row in failed:
        if any(row["governed_case_metric_availability"].values()) or row["typed_failure_reason"] != TARGET_FAILURE:
            raise ValueError(f"typed case is not fail closed: {row['run_id']}")
    if sum(row["run_id"].startswith("SCHM_") and row["run_id"].endswith("_H1") and row["status"] == "PASS" for row in cases) != 21:
        raise ValueError("exact 21 H1 PASS identities required")
    if final["source_lineage"] != {**LINEAGE,
                                    "comparison_role": "COMPARISON_TO_POST_FIT_DERIVED_SOURCE_QUANTITIES",
                                    "uncertainty_role": "POST_FIT_DERIVED_REPLICATE_SPREAD_NOT_INDEPENDENT_MEASUREMENT_UNCERTAINTY"}:
        raise ValueError("final source-lineage metadata mismatch")
    return {"status": "PASS", "nested_records": 3, "production_identities": 45,
            "production_pass": 27, "typed_failures": 18, "h1_pass": 21,
            "species_triplets_per_component": 24, "reduced_source_clock_rows": 21}


def generate(repo: Path, source_csv: Path, original: Path, recovery: Path) -> dict:
    base_path = repo / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_RESULT.json"
    if sha256(base_path) != BASE_RESULT_SHA256:
        raise ValueError("immutable B2 base result identity mismatch")
    base = json.loads(base_path.read_text())
    inv = repo / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B0_CONFIGURATION_INVENTORY.json"
    species = species_audit(source_csv)
    reduced = reduced_source_clock(inv)
    summaries = case_summaries(base, inv, original, recovery)
    out = repo / "validation/cases/val_corpus_002"
    dump(out / "VAL_CORPUS_002_STAGE_B2_NORMALIZED_SPECIES_AUDIT.json", species)
    dump(out / "VAL_CORPUS_002_STAGE_B2_REDUCED_SOURCE_CLOCK.json", reduced)
    dump(out / "VAL_CORPUS_002_STAGE_B2_PER_CASE_NUMERICAL_SUMMARY.json", summaries)
    refs = {
        "normalized_species_audit": {"path": "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_NORMALIZED_SPECIES_AUDIT.json",
                                     "sha256": sha256(out / "VAL_CORPUS_002_STAGE_B2_NORMALIZED_SPECIES_AUDIT.json")},
        "reduced_source_clock": {"path": "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_REDUCED_SOURCE_CLOCK.json",
                                 "sha256": sha256(out / "VAL_CORPUS_002_STAGE_B2_REDUCED_SOURCE_CLOCK.json")},
        "per_case_numerical_summary": {"path": "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_PER_CASE_NUMERICAL_SUMMARY.json",
                                       "sha256": sha256(out / "VAL_CORPUS_002_STAGE_B2_PER_CASE_NUMERICAL_SUMMARY.json")},
    }
    final = {"schema_version": "espresso.val_corpus_002.b2_final_result.v1",
             "bundle_status": "RESULT_COMPLETE_WITH_TYPED_FAILURES",
             "reduction_status": "PASS",
             "production_matrix_disposition": "COMPLETE_WITH_18_TYPED_NUMERICAL_CASE_FAILURES",
             "authorization_id": AUTHORIZATION,
             "base_result_reference": {
                 "path": "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_RESULT.json",
                 "sha256": BASE_RESULT_SHA256,
                 "base_result_role": "IMMUTABLE_HISTORICAL_SUPERSEDED_FOR_INTERPRETATION"},
             "authoritative_interpretation": "FINAL_RESULT_INTERPRETATION",
             "interpretation": interpretation(base),
             "records": refs,
             "source_lineage": {**LINEAGE,
                                "comparison_role": "COMPARISON_TO_POST_FIT_DERIVED_SOURCE_QUANTITIES",
                                "uncertainty_role": "POST_FIT_DERIVED_REPLICATE_SPREAD_NOT_INDEPENDENT_MEASUREMENT_UNCERTAINTY"},
             "production_counts": {"identities": 45, "pass": 27,
                                   "typed_target_coverage_failures": 18, "h1_pass": 21},
             "immutable_numerical_artifacts": True,
             "openfoam_rerun": "NOT_PERFORMED", "sensitivity_rerun": "NOT_PERFORMED",
             "calibration": "CLOSED_NO_REFIT", "protected_scoring": "NOT_PERFORMED",
             "new_governing_physics": "NOT_AUTHORIZED", "val_case_002": "NOT_STARTED"}
    dump(out / "VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json", final)
    source_sha = sha256(out / "VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json")
    script_sha = sha256(repo / "scripts/val_corpus_002_b2_reporting.py")
    figure_input = {**final, "per_case_numerical_summary": summaries}
    manifest = figures(figure_input, base, repo / "validation/cases/val_corpus_002/figures", source_sha, script_sha)
    dump(out / "VAL_CORPUS_002_STAGE_B2_FIGURE_MANIFEST.json", manifest)
    validation = validate_final_package(repo, final)
    return {"final_result_sha256": source_sha,
            "species_audit_sha256": sha256(out / "VAL_CORPUS_002_STAGE_B2_NORMALIZED_SPECIES_AUDIT.json"),
            "reduced_source_clock_sha256": sha256(out / "VAL_CORPUS_002_STAGE_B2_REDUCED_SOURCE_CLOCK.json"),
            "per_case_summary_sha256": sha256(out / "VAL_CORPUS_002_STAGE_B2_PER_CASE_NUMERICAL_SUMMARY.json"),
            "figure_manifest_sha256": sha256(out / "VAL_CORPUS_002_STAGE_B2_FIGURE_MANIFEST.json"),
            "nested_validation": validation}


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
