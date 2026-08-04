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


CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 820
BANDS = {
    "title": (30, 18, 1140, 42),
    "legend": (30, 66, 1140, 48),
    "plot": (70, 122, 1080, 540),
    "lower-label": (70, 666, 1080, 34),
    "axis-title": (30, 704, 1140, 28),
    "annotation": (30, 736, 1140, 30),
    "caption": (30, 770, 1140, 42),
}
LINEAGE_CAPTION = ("cup_masses.csv contains post-fit derived source quantities, not independent "
                   "measurements; comparison role: reconstruction or derived metric only.")
SENSITIVITY_OUTPUT_LABELS = (
    "cup solute mass at 20 g",
    "cup solute mass at 40 g",
    "cup solute mass at 60 g",
)


def _text(x: float, y: float, value: object, size: int = 12, **attrs: object) -> str:
    extra = " ".join(f'{key.replace("_", "-")}="{_esc(item)}"' for key, item in attrs.items())
    return (f'<text x="{x:.3f}" y="{y:.3f}" font-family="sans-serif" font-size="{size}"'
            f'{(" " + extra) if extra else ""}>{_esc(value)}</text>')


def _band(name: str, body: list[str]) -> str:
    x, y, width, height = BANDS[name]
    return (f'<g id="{name}-band" data-band="{name}" data-x="{x}" data-y="{y}" '
            f'data-width="{width}" data-height="{height}">\n' + "\n".join(body) + "\n</g>")


def _wrapped(value: str, x: float, y: float, width: int = 150, size: int = 11) -> list[str]:
    words, lines, current = value.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return [_text(x, y + index * (size + 3), line, size) for index, line in enumerate(lines)]


def _canvas(title: str, bands: dict[str, list[str]], caption: str) -> bytes:
    rows = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" '
            f'viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}">',
            f'<rect x="0" y="0" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="white"/>',
            f'<title>{_esc(title)}</title>', f'<desc>{_esc(caption)}</desc>']
    for name in BANDS:
        body = bands.get(name, [])
        if name == "title":
            body = [_text(40, 47, title, 20)] + body
        if name == "caption":
            body = body + _wrapped(caption, 40, 786)
        rows.append(_band(name, body))
    rows.append('</svg>')
    return ("\n".join(rows) + "\n").encode()


def _panel(panel_id: str, rect: tuple[float, float, float, float], body: list[str]) -> str:
    x, y, width, height = rect
    return (f'<g id="{panel_id}" data-panel="{panel_id}" data-plot-x="{x:.3f}" '
            f'data-plot-y="{y:.3f}" data-plot-width="{width:.3f}" data-plot-height="{height:.3f}">\n'
            + "\n".join(body) + "\n</g>")


def _polyline(points: list[tuple[float, float]], color: str, width: int = 2,
              panel: str = "", dash: str | None = None) -> str:
    encoded = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
    dashed = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polyline points="{encoded}" fill="none" stroke="{color}" stroke-width="{width}"'
            f'{dashed} data-role="data" data-panel-ref="{panel}"/>')


def _marker(x: float, y: float, style: str, color: str, panel: str, anchor: bool = False) -> str:
    common = f'fill="{color}" stroke="#111" data-role="data" data-panel-ref="{panel}"'
    if style == "square":
        mark = f'<rect x="{x-3:.3f}" y="{y-3:.3f}" width="6" height="6" {common}/>'
    elif style == "triangle":
        mark = f'<polygon points="{x:.3f},{y-4:.3f} {x-4:.3f},{y+3:.3f} {x+4:.3f},{y+3:.3f}" {common}/>'
    elif style == "diamond":
        mark = f'<polygon points="{x:.3f},{y-4:.3f} {x-4:.3f},{y:.3f} {x:.3f},{y+4:.3f} {x+4:.3f},{y:.3f}" {common}/>'
    else:
        mark = f'<circle cx="{x:.3f}" cy="{y:.3f}" r="3" {common}/>'
    if anchor:
        mark += f'<circle cx="{x:.3f}" cy="{y:.3f}" r="7" fill="none" stroke="#b2182b" stroke-width="2" data-role="data" data-panel-ref="{panel}"/>'
    return mark


def _ticks(rect: tuple[float, float, float, float], xmin: float, xmax: float,
           ymin: float, ymax: float, xticks: list[tuple[float, str]],
           yticks: list[tuple[float, str]]) -> list[str]:
    x, y, width, height = rect
    rows = [f'<rect x="{x:.3f}" y="{y:.3f}" width="{width:.3f}" height="{height:.3f}" fill="none" stroke="#333"/>']
    for value, label in xticks:
        px = x + (value - xmin) / (xmax - xmin) * width
        rows.extend([f'<line x1="{px:.3f}" y1="{y+height:.3f}" x2="{px:.3f}" y2="{y+height+4:.3f}" stroke="#333"/>',
                     _text(px, y + height + 16, label, 9, text_anchor="middle")])
    for value, label in yticks:
        py = y + height - (value - ymin) / (ymax - ymin) * height
        rows.extend([f'<line x1="{x-4:.3f}" y1="{py:.3f}" x2="{x:.3f}" y2="{py:.3f}" stroke="#333"/>',
                     _text(x - 7, py + 3, label, 9, text_anchor="end")])
    return rows


def figures(final: dict, base: dict, output: Path, source_sha: str, script_sha: str) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    interpretations = final["interpretation"]
    content: dict[str, bytes] = {}

    cases = final["per_case_numerical_summary"]["cases"]
    indexed = {row["run_id"]: row for row in cases}
    matrix_body = []
    columns = (("P0/H0", "P0", "H0"), ("P0/H1", "P0", "H1"),
               ("P1/H0", "P1", "H0"), ("P1/H1", "P1", "H1"),
               ("P2/H0", "P2", "H0"), ("P2/H1", "P2", "H1"))
    x0, y0, cell_w, cell_h = 250, 150, 132, 55
    for col, (label, _, _) in enumerate(columns):
        matrix_body.append(_text(x0 + col * cell_w + cell_w / 2, 140, label, 11, text_anchor="middle"))
    for row_index, exp in enumerate(range(1, 8)):
        matrix_body.append(_text(235, y0 + row_index * cell_h + 32, f"Schmieder Exp {exp}", 11, text_anchor="end"))
        for col, (_, parameter, mode) in enumerate(columns):
            suffix = "_FIXED_AFTER_EXP7_CALIBRATION" if parameter == "P2" else ""
            run_id = f"SCHM_EXP{exp}_{parameter}{suffix}_{mode}"
            row = indexed[run_id]
            x, y = x0 + col * cell_w, y0 + row_index * cell_h
            color = "#2c7fb8" if row["status"] == "PASS" else "#d95f0e"
            matrix_body.append(f'<g data-run-id="{run_id}"><title>{run_id}</title><rect x="{x:.3f}" y="{y:.3f}" width="{cell_w-8}" height="{cell_h-8}" fill="{color}" stroke="#222" data-role="data" data-panel-ref="availability"/>{_text(x+(cell_w-8)/2, y+28, "PASS" if row["status"] == "PASS" else "TYPED", 10, fill="white", text_anchor="middle")}</g>')
    wasz_y = y0 + 7 * cell_h + 20
    matrix_body.append(_text(235, wasz_y + 32, "Waszkiewicz 9 bar", 11, text_anchor="end"))
    for col, parameter in enumerate(PARAMETERS):
        run_id = (f"WASZ_9_COMPACT_{parameter}_CHEMISTRY" if parameter != "P2"
                  else "WASZ_9_COMPACT_P2_FIXED_AFTER_EXP7_CALIBRATION_CHEMISTRY")
        row = indexed[run_id]
        x = x0 + col * cell_w * 2
        matrix_body.append(f'<g data-run-id="{run_id}"><title>{run_id}</title><rect x="{x:.3f}" y="{wasz_y:.3f}" width="{cell_w*2-8}" height="47" fill="#2c7fb8" stroke="#222" data-role="data" data-panel-ref="availability"/>{_text(x+(cell_w*2-8)/2, wasz_y+28, parameter+" PASS", 10, fill="white", text_anchor="middle")}</g>')
    matrix_panel = _panel("availability", (250, 150, 784, 452), matrix_body)
    bands = {"legend": ['<rect x="330" y="80" width="18" height="18" fill="#2c7fb8"/>', _text(356, 94, "numerical PASS (27)", 12),
                         '<rect x="550" y="80" width="18" height="18" fill="#d95f0e"/>', _text(576, 94, "typed target unavailability (18; normal execution, not infrastructure)", 12)],
             "plot": [matrix_panel],
             "lower-label": [_text(640, 687, "Columns identify parameterization and hydraulic mode; each cell carries its governed run_id.", 11, text_anchor="middle")],
             "axis-title": [_text(640, 723, "45 governed identities: 42 Schmieder + 3 Waszkiewicz", 12, text_anchor="middle")],
             "annotation": [_text(640, 754, "No imputation or extrapolation; typed target coverage is distinct from execution failure.", 11, text_anchor="middle")]}
    content["production_availability_matrix.svg"] = _canvas("Production availability matrix", bands,
                                                              "27 PASS; 18 immutable typed target-coverage failures.")

    colors = {"P0": "#1b9e77", "P1": "#7570b3", "P2": "#d95f02"}
    styles = {"source": ("#222", "circle", None), "P0": (colors["P0"], "square", "7 4"),
              "P1": (colors["P1"], "triangle", "2 3"), "P2": (colors["P2"], "diamond", None)}
    all_values = [metric[key] for run_id, record in base["schmieder"].items() if run_id.endswith("_H1")
                  for metric in record["target_metrics"] for key in ("source_cup_solute_mass_g", "model_cup_solute_mass_g")]
    ymax = math.ceil(max(all_values) * 1.08 * 10) / 10
    panels = []
    for exp in range(1, 8):
        col, row_index = (exp - 1) % 4, (exp - 1) // 4
        rect = (92 + col * 270, 158 + row_index * 245, 220, 180)
        panel_id = f"schm-exp-{exp}"
        body = _ticks(rect, 20, 60, 0, ymax, [(20, "20"), (40, "40"), (60, "60")],
                      [(0, "0"), (ymax / 2, f"{ymax/2:.1f}"), (ymax, f"{ymax:.1f}")])
        p0_key = f"SCHM_EXP{exp}_P0_H1"
        series = {"source": [m["source_cup_solute_mass_g"] for m in base["schmieder"][p0_key]["target_metrics"]]}
        for parameter in PARAMETERS:
            suffix = "_FIXED_AFTER_EXP7_CALIBRATION" if parameter == "P2" else ""
            key = f"SCHM_EXP{exp}_{parameter}{suffix}_H1"
            series[parameter] = [m["model_cup_solute_mass_g"] for m in base["schmieder"][key]["target_metrics"]]
        for name in ("source", "P0", "P1", "P2"):
            color, marker, dash = styles[name]
            points = [(rect[0] + 8 + (mass - 20) / 40 * (rect[2] - 16),
                       rect[1] + rect[3] - value / ymax * rect[3])
                      for mass, value in zip(TARGETS_G, series[name])]
            body.append(_polyline(points, color, 2, panel_id, dash))
            body.extend(_marker(x, y, marker, color, panel_id, exp == 7 and name == "P2") for x, y in points)
        body.append(_text(rect[0] + rect[2] / 2, rect[1] - 9, f"Experiment {exp}" + (" — P2 calibration anchor" if exp == 7 else ""), 10, text_anchor="middle"))
        panels.append(_panel(panel_id, rect, body))
    legend = []
    for index, name in enumerate(("source", "P0", "P1", "P2")):
        color, marker, dash = styles[name]
        x = 300 + index * 170
        legend.extend([f'<line x1="{x}" y1="90" x2="{x+35}" y2="90" stroke="{color}" stroke-width="2"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>',
                       f'<circle cx="{x+17}" cy="90" r="3" fill="{color}" stroke="#111"/>',
                       _text(x + 43, 94, name if name == "source" else f"model {name}", 12)])
    bands = {"legend": legend, "plot": panels,
             "lower-label": [_text(640, 688, "Target beverage mass (g): 20, 40, 60 in every panel", 11, text_anchor="middle")],
             "axis-title": [_text(640, 723, f"Cup solute mass (g); shared y-domain 0 to {ymax:.1f} g", 12, text_anchor="middle")],
             "annotation": [_text(640, 754, "Red rings identify Experiment-7/P2 as the calibration reconstruction anchor.", 11, text_anchor="middle")]}
    content["schmieder_h1_source_model.svg"] = _canvas("Schmieder H1 source/model cup-solute mass", bands, LINEAGE_CAPTION)

    contrast_rows = [(p, axis, ratio, base["axis_contrasts"][p][axis][ratio])
                     for p in ("P1_H1", "P2_H1")
                     for axis in ("FLOW_HIGH_MINUS_LOW", "GRIND_COARSE_MINUS_FINE", "TEMPERATURE_HIGH_MINUS_LOW")
                     for ratio in ("1/1", "1/2", "1/3")]
    scale = math.ceil(max(abs(row[key]) for *_, row in contrast_rows for key in ("source", "model")) * 1.1 * 10) / 10
    contrast_panels = []
    axis_labels = (("FLOW_HIGH_MINUS_LOW", "Flow: high − low"), ("GRIND_COARSE_MINUS_FINE", "Grind: coarse − fine"),
                   ("TEMPERATURE_HIGH_MINUS_LOW", "Temperature: high − low"))
    for p_index, parameter in enumerate(("P1_H1", "P2_H1")):
        for axis_index, (axis, axis_label) in enumerate(axis_labels):
            rect = (105 + axis_index * 360, 165 + p_index * 250, 285, 180)
            panel_id = f"contrast-{parameter[:2].lower()}-{axis_index}"
            body = _ticks(rect, 0, 4, -scale, scale, [(1, "1:1"), (2, "1:2"), (3, "1:3")],
                          [(-scale, f"-{scale:.1f}"), (0, "0"), (scale, f"{scale:.1f}")])
            zero = rect[1] + rect[3] / 2
            body.append(f'<line x1="{rect[0]:.3f}" y1="{zero:.3f}" x2="{rect[0]+rect[2]:.3f}" y2="{zero:.3f}" stroke="#666" stroke-dasharray="4 3"/>')
            for idx, ratio in enumerate(("1/1", "1/2", "1/3"), 1):
                row = base["axis_contrasts"][parameter][axis][ratio]
                for offset, key, color, marker in ((-8, "source", "#222", "circle"), (8, "model", colors[parameter[:2]], "square")):
                    x = rect[0] + idx / 4 * rect[2] + offset
                    y = rect[1] + rect[3] - (row[key] + scale) / (2 * scale) * rect[3]
                    body.append(f'<line x1="{x:.3f}" y1="{zero:.3f}" x2="{x:.3f}" y2="{y:.3f}" stroke="{color}" stroke-width="3" data-role="data" data-panel-ref="{panel_id}"/>')
                    body.append(_marker(x, y, marker, color, panel_id))
            body.append(_text(rect[0] + rect[2] / 2, rect[1] - 10, f"{parameter[:2]} — {axis_label}", 11, text_anchor="middle"))
            contrast_panels.append(_panel(panel_id, rect, body))
    bands = {"legend": ['<circle cx="430" cy="90" r="4" fill="#222" stroke="#111"/>', _text(442, 94, "source", 12),
                         '<rect x="540" y="86" width="8" height="8" fill="#7570b3" stroke="#111"/>', _text(556, 94, "P1 model", 12),
                         '<rect x="680" y="86" width="8" height="8" fill="#d95f02" stroke="#111"/>', _text(696, 94, "fixed P2 model", 12)],
             "plot": contrast_panels,
             "lower-label": [_text(640, 688, "Brew ratio categories: 1:1, 1:2, 1:3", 11, text_anchor="middle")],
             "axis-title": [_text(640, 723, f"High-minus-low cup-solute contrast (g); shared symmetric scale ±{scale:.1f} g", 12, text_anchor="middle")],
             "annotation": [_text(640, 754, "Zero line shown; source/model and P1/P2 identities use both marker form and colour.", 11, text_anchor="middle")]}
    content["schmieder_h1_axis_contrasts.svg"] = _canvas("Schmieder H1 frozen axis contrasts", bands, LINEAGE_CAPTION)

    source = base["waszkiewicz"]["source_tds_fraction"]
    max_tds = max(source + [v for clocks in base["waszkiewicz"]["results"].values() for rec in clocks.values() for v in rec["model_interval_tds_fraction"]])
    clock_names = ("SOURCE_REPORTED_CLOCK", "EXISTING_ACCEPTED_FIXED_SOURCE_TO_SOLVER_OFFSET_PLUS_3_SECONDS")
    yscale = math.ceil(max_tds * 1.1 * 100) / 100
    wasz_panels = []
    for panel, clock in enumerate(clock_names):
        rect = (115 + panel * 550, 180, 450, 390)
        panel_id = f"wasz-clock-{panel}"
        body = _ticks(rect, 1, 12, 0, yscale, [(value, str(value)) for value in (1, 3, 5, 7, 9, 11, 12)],
                      [(0, "0.00"), (yscale / 2, f"{yscale/2:.2f}"), (yscale, f"{yscale:.2f}")])
        source_pts = [(rect[0] + 5 + i / 11 * (rect[2] - 10),
                       rect[1] + 6 + (1 - value / yscale) * (rect[3] - 12))
                      for i, value in enumerate(source)]
        body.append(_polyline(source_pts, "#222", 2, panel_id))
        body.extend(_marker(x, y, "circle", "#222", panel_id) for x, y in source_pts)
        for parameter in PARAMETERS:
            values = base["waszkiewicz"]["results"][parameter][clock]["model_interval_tds_fraction"]
            points = [(rect[0] + 5 + i / 11 * (rect[2] - 10),
                       rect[1] + 6 + (1 - value / yscale) * (rect[3] - 12))
                      for i, value in enumerate(values)]
            body.append(_polyline(points, colors[parameter], 2, panel_id, styles[parameter][2]))
            body.extend(_marker(x, y, styles[parameter][1], colors[parameter], panel_id) for x, y in points)
        heading = "Source-reported clock" if panel == 0 else "Frozen +3 s offset"
        body.append(_text(rect[0] + rect[2] / 2, rect[1] - 14, heading, 13, text_anchor="middle"))
        wasz_panels.append(_panel(panel_id, rect, body))
    legend = [_text(290, 94, "source ●", 12, fill="#222"), _text(430, 94, "P0 ■ dashed", 12, fill=colors["P0"]),
              _text(590, 94, "P1 ▲ dotted", 12, fill=colors["P1"]), _text(750, 94, "fixed P2 ◆", 12, fill=colors["P2"])]
    bands = {"legend": legend, "plot": wasz_panels,
             "lower-label": [_text(640, 688, "5-second interval index (1–12)", 11, text_anchor="middle")],
             "axis-title": [_text(640, 723, f"Interval TDS fraction; shared y-domain 0 to {yscale:.2f}", 12, text_anchor="middle")],
             "annotation": [_text(640, 754, "No optimized shift; lower +3 s RMSE is a fixed-presentation improvement, not validation.", 11, text_anchor="middle")]}
    content["waszkiewicz_both_clocks.svg"] = _canvas("Waszkiewicz interval TDS under both frozen clocks", bands,
                                                      "Same OpenFOAM results under two prospectively frozen clock presentations.")

    matrix = base["sensitivity"]["matrix"]
    maximum = max(abs(v) for row in matrix for v in row)
    matrix_body = []
    matrix_rect = (250, 190, 560, 330)
    for r, row in enumerate(matrix):
        for c, value in enumerate(row):
            intensity = int(235 - 170 * abs(value) / maximum)
            color = f"rgb({intensity},{intensity},{255 if value >= 0 else 135})"
            x, y = matrix_rect[0] + c * 140, matrix_rect[1] + r * 110
            matrix_body.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="140" height="110" fill="{color}" stroke="#222" data-role="data" data-panel-ref="sensitivity-matrix"/>')
            matrix_body.append(_text(x + 70, y + 60, repr(value), 10, text_anchor="middle"))
    for r, label in enumerate(SENSITIVITY_OUTPUT_LABELS):
        matrix_body.append(_text(238, matrix_rect[1] + r * 110 + 58, label, 10, text_anchor="end"))
    for c, label in enumerate(base["sensitivity"]["parameters"]):
        matrix_body.append(_text(matrix_rect[0] + c * 140 + 70, 175, label, 10, text_anchor="middle"))
    matrix_panel = _panel("sensitivity-matrix", matrix_rect, matrix_body)
    singular = base["sensitivity"]["singular_values"]
    singular_rect = (900, 190, 220, 330)
    singular_body = []
    for i, value in enumerate(singular):
        height = value / max(singular) * 250
        x = singular_rect[0] + 15 + i * 68
        y = singular_rect[1] + 275 - height
        singular_body.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="42" height="{height:.3f}" fill="#3182bd" stroke="#222" data-role="data" data-panel-ref="singular-values"/>')
        singular_body.extend([_text(x + 21, singular_rect[1] + 295, f"s{i+1}", 10, text_anchor="middle"),
                              _text(x + 21, y - 7, repr(value), 8, text_anchor="middle")])
    singular_body.append(_text(1010, 535, f"matrix rank = {base['sensitivity']['rank']}", 11, text_anchor="middle"))
    singular_panel = _panel("singular-values", singular_rect, singular_body)
    bands = {"legend": [_text(300, 91, "Signed elasticity key:", 12),
                         '<rect x="455" y="78" width="35" height="18" fill="rgb(65,65,255)" stroke="#222"/>', _text(498, 92, "positive / stronger", 11),
                         '<rect x="660" y="78" width="35" height="18" fill="rgb(65,65,135)" stroke="#222"/>', _text(703, 92, "negative / stronger", 11),
                         '<rect x="860" y="78" width="35" height="18" fill="rgb(235,235,255)" stroke="#222"/>', _text(903, 92, "near zero", 11)],
             "plot": [matrix_panel, singular_panel],
             "lower-label": [_text(640, 688, "Every 3 × 4 matrix cell and all three singular values are labeled numerically.", 11, text_anchor="middle")],
             "axis-title": [_text(640, 723, "Finite-range log-secant sensitivity diagnostic", 12, text_anchor="middle")],
             "annotation": [_text(640, 754, "Equifinality warning; NOT_STRUCTURAL_IDENTIFIABILITY — not structural-identifiability proof.", 11, text_anchor="middle")]}
    content["sensitivity_matrix_and_singular_values.svg"] = _canvas("Sensitivity elasticity matrix and singular values", bands,
                                                                     "Finite-range 3-output × 4-parameter diagnostic; rank ceiling three.")
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
