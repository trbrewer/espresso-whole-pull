#!/usr/bin/env python3
"""Prospective, case-local VAL-CORPUS-002 Stage-B0 tooling.

This module operates only on metadata, retained predecessor evidence, and
synthetic values.  It contains no OpenFOAM launcher and no source scorer.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


CASE_DIR = Path("validation/cases/val_corpus_002")
RUN_MATRIX = CASE_DIR / "VAL_CORPUS_002_FUTURE_RUN_MATRIX.json"
SENSITIVITY_MATRIX = CASE_DIR / "VAL_CORPUS_002_SENSITIVITY_MATRIX.json"
PLACEHOLDER_TOKEN = "EXACT_GLOBAL_P2_K_FROM_AUTHORIZED_CALIBRATION"
TYPED_PLACEHOLDER = {"type": "P2_EXTRACTION_RATE_S_INVERSE", "value": "UNMATERIALIZED"}
P2_BOUNDS = (1.0e-4, 2.0)
REFERENCE = {
    "binding_class": "DIRECT_CONTENT_ADDRESS",
    "normalized_path": "<WP03_002_REVIEW_ROOT>/corrected-runs-v2/cases/WASZ-9-COMPACT/postProcessing/wholePull/0/traces.csv",
    "runtime_root": "<WP03_002_REVIEW_ROOT>",
    "sha256": "bb3a5d2214b3eaf0cec2d76be0c90f56b2454cfa1982b2770841b499ed1db30a",
    "bytes": 2796444,
    "header_sha256": "27eb008688cb84f98f5b7f877aa73d745f4b3e28ce5c99f95673ed222c854831",
    "first_timestamp_s": 0.02,
    "final_timestamp_s": 29.9999999999994,
    "configuration_sha256": "09abbfdc0115a59b9452048f1ac2dcdbaf7707c91c31b166c998eab78ecf28b5",
    "executable_sha256": "e682bb63d4b54a19133a81e1dc857217132b91918ecceb33ffbc88c35b6b0fd6",
    "case_manifest_sha256": "2687a4f7b0693bf41173eecc6332e95be9e5f8cc62f7bd4957323556d45ea778",
    "scientific_input_bundle_sha256": "b4930f327466f201ddaab002373ec16e51075ea90e8621963afc056180bef770",
    "execution_record_sha256": "5a08518c0cbe6935f17b4826c473c7b494e1c4650c9efda733af903199422875",
    "build_provenance_sha256": "5a27f0b6e2e2599e1a7174f314b4f702c571b97ead262580a7a4769a52b9fcd4",
    "historical_manifest_status": "EXCLUDED_AS_DOWNSTREAM_ARTIFACT_BY_DESIGN",
}
PARITY_FIELDS = {
    "time_s": 1e-12, "inlet_pressure_Pa": 1e-6, "outlet_flow_m3_s": 1e-16,
    "cup_water_mass_kg": 1e-12, "cup_solute_mass_kg": 1e-12,
    "cup_beverage_mass_kg": 1e-12, "remaining_extractable_mass_kg": 1e-12,
    "dissolved_in_puck_mass_kg": 1e-12,
    "volumeWeightedMechanicalPorosity": 1e-12,
    "volumeWeightedPermeabilityM2": 1e-25,
}


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _replace_token(value: object) -> tuple[object, int]:
    count = 0
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            replaced, found = _replace_token(item)
            result[key] = replaced
            count += found
        return result, count
    if isinstance(value, list):
        result = []
        for item in value:
            replaced, found = _replace_token(item)
            result.append(replaced)
            count += found
        return result, count
    if value == PLACEHOLDER_TOKEN:
        return copy.deepcopy(TYPED_PLACEHOLDER), 1
    return value, 0


def typed_template(configuration: dict) -> dict:
    value, count = _replace_token(configuration)
    if count != 1:
        raise ValueError(f"P2 template requires exactly one placeholder, found {count}")
    return value


def _materialize(value: object, rate: float) -> tuple[object, int]:
    count = 0
    if isinstance(value, dict):
        if value == TYPED_PLACEHOLDER:
            return rate, 1
        result = {}
        for key, item in value.items():
            replaced, found = _materialize(item, rate)
            result[key] = replaced
            count += found
        return result, count
    if isinstance(value, list):
        result = []
        for item in value:
            replaced, found = _materialize(item, rate)
            result.append(replaced)
            count += found
        return result, count
    return value, 0


def materialize_p2(template: dict, rate: float, approved_hash: str,
                   *, bounds: tuple[float, float] = P2_BOUNDS) -> dict:
    if canonical_sha256(template) != approved_hash:
        raise ValueError("unapproved P2 template hash")
    if not math.isfinite(rate) or not bounds[0] <= rate <= bounds[1]:
        raise ValueError("P2 rate outside frozen finite bounds")
    materialized, count = _materialize(template, rate)
    if count != 1:
        raise ValueError(f"P2 template requires exactly one typed placeholder, found {count}")
    check, reverse_count = _replace_numeric_rate(materialized, rate)
    if reverse_count != 1 or check != template:
        raise ValueError("materialization changed a non-rate field")
    return materialized


def _replace_numeric_rate(value: object, rate: float) -> tuple[object, int]:
    if isinstance(value, dict):
        result, count = {}, 0
        for key, item in value.items():
            if key in {"extractionRateConstant_s_inverse", "rate_constant_1_s"} and item == rate:
                result[key], found = copy.deepcopy(TYPED_PLACEHOLDER), 1
            else:
                result[key], found = _replace_numeric_rate(item, rate)
            count += found
        return result, count
    if isinstance(value, list):
        result, count = [], 0
        for item in value:
            replaced, found = _replace_numeric_rate(item, rate)
            result.append(replaced); count += found
        return result, count
    return value, 0


def build_configuration_inventory(root: Path) -> dict:
    matrix = json.loads((root / RUN_MATRIX).read_text())
    sensitivity = json.loads((root / SENSITIVITY_MATRIX).read_text())
    production = matrix["final_production_run_inventory"]
    numeric, templates = [], []
    for record in production:
        config = copy.deepcopy(record.get("configuration", record))
        identity = record.get("id", record.get("run_id"))
        if record["parameterization"].startswith("P2"):
            config = typed_template(config)
            templates.append({"id": identity, "canonical_sha256": canonical_sha256(config),
                              "template": config})
        else:
            numeric.append({"id": identity, "parameterization": record["parameterization"],
                            "canonical_sha256": canonical_sha256(config), "configuration": config})
    sens = [{"id": row["run_id"], "reuse": row["run_id"] == "SENS_BASELINE",
             "canonical_sha256": canonical_sha256(row), "configuration": row}
            for row in sensitivity["future_runs"]]
    calibration = next(row for row in templates if row["id"] == "SCHM_EXP7_P2_FIXED_AFTER_EXP7_CALIBRATION_H1")
    if (len(production), len(numeric), len(templates), len(sens)) != (45, 30, 15, 9):
        raise ValueError("frozen configuration inventory count mismatch")
    if sum(item["id"].startswith("SCHM_") for item in templates) != 14:
        raise ValueError("Schmieder P2 template count mismatch")
    return {
        "schema_version": 1,
        "canonicalization": "UTF8_SORTED_KEYS_COMPACT_SEPARATORS_NO_NONFINITE_TERMINAL_NEWLINE",
        "counts": {"final_production_identities": 45, "numeric_p0_p1": 30,
                   "typed_p2_templates": 15, "schmieder_p2_templates": 14,
                   "waszkiewicz_p2_templates": 1, "sensitivity_identities": 9,
                   "sensitivity_new_executions_if_reuse_valid": 8,
                   "optimizer_maximum_evaluations": 128},
        "numeric_configurations": numeric, "typed_p2_templates": templates,
        "sensitivity_configurations": sens,
        "experiment_7_h1_calibration_template": {
            "id": calibration["id"], "canonical_sha256": calibration["canonical_sha256"]},
    }


def bind_reference(root: Path, review_root: Path) -> dict:
    rel = Path("corrected-runs-v2/cases/WASZ-9-COMPACT/postProcessing/wholePull/0/traces.csv")
    path = review_root / rel
    if not path.is_file() or path.is_symlink():
        raise ValueError("reference trace must be a regular retained file")
    with path.open("rb") as raw:
        header = raw.readline()
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        missing = set(PARITY_FIELDS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing parity fields: {sorted(missing)}")
        first = next(reader); final = first
        rows = 1
        for final in reader: rows += 1
    observed = {"sha256": file_sha256(path), "bytes": path.stat().st_size,
                "header_sha256": hashlib.sha256(header).hexdigest(),
                "first_timestamp_s": float(first["time_s"]),
                "final_timestamp_s": float(final["time_s"])}
    for key, expected in ((key, REFERENCE[key]) for key in observed):
        if observed[key] != expected:
            raise ValueError(f"reference {key} mismatch: {observed[key]} != {expected}")
    return {**REFERENCE, "trace_rows": rows, "required_fields": list(PARITY_FIELDS),
            "field_absolute_tolerances": PARITY_FIELDS,
            "common_domain_s": [0.02, 29.9999999999994],
            "final_timestamp_accepted_as_30s_tolerance_s": 1e-12,
            "parity_t0_insertion": "PROHIBITED",
            "initial_state_check": "EXACT_IDENTITIES_SEPARATE_FROM_TRACE"}


def verify_initial_state(actual: dict, expected: dict) -> None:
    required = {"simulation_start_time_s", "initial_fields_sha256", "configuration_sha256",
                "geometry_mesh_sha256", "executable_sha256", "chemistry_sha256",
                "pressure_ramp_controls_sha256", "timestep_controls_sha256",
                "numerical_controls_sha256"}
    if set(actual) != required or set(expected) != required or actual != expected:
        raise ValueError("initial-state exact identity check failed")


def _interpolated(row0: dict[str, float], row1: dict[str, float], time_s: float,
                  field: str) -> float:
    fraction = (time_s - row0["time_s"]) / (row1["time_s"] - row0["time_s"])
    return row0[field] + fraction * (row1[field] - row0[field])


def compare_parity(reference: list[dict[str, float]], candidate: list[dict[str, float]]) -> dict:
    if not reference or not candidate or any(row["time_s"] == 0 for row in reference):
        raise ValueError("parity requires retained nonzero reference rows")
    for rows in (reference, candidate):
        if any(b["time_s"] <= a["time_s"] for a, b in zip(rows, rows[1:])):
            raise ValueError("parity timestamps must be strictly increasing")
    failures, compared = [], 0
    index = 0
    for ref in reference:
        time_s = ref["time_s"]
        if time_s < 0.02 or time_s > 29.9999999999994:
            continue
        while index + 1 < len(candidate) and candidate[index + 1]["time_s"] <= time_s:
            index += 1
        if candidate[index]["time_s"] == time_s:
            values = candidate[index]
        elif index + 1 < len(candidate) and candidate[index]["time_s"] < time_s < candidate[index + 1]["time_s"]:
            values = {field: _interpolated(candidate[index], candidate[index + 1], time_s, field)
                      for field in PARITY_FIELDS if field != "time_s"}
            values["time_s"] = time_s
        else:
            raise ValueError("candidate does not bracket reference; extrapolation prohibited")
        for field, absolute in PARITY_FIELDS.items():
            observed, expected = values[field], ref[field]
            if not math.isfinite(observed) or not math.isfinite(expected):
                raise ValueError("nonfinite parity value")
            error = abs(observed - expected)
            if error > absolute + 1e-10 * abs(expected):
                failures.append({"time_s": time_s, "field": field, "absolute_error": error})
        compared += 1
    return {"status": "PASS" if not failures else "FAIL", "compared_reference_states": compared,
            "failures": failures, "domain_s": [0.02, 29.9999999999994]}


def external_inventory(root: Path, files: Iterable[Path]) -> dict:
    records = []
    root = root.resolve()
    for path in sorted({path.resolve() for path in files}):
        if path.is_symlink() or not path.is_file() or root not in path.parents:
            raise ValueError("artifact must be a regular file below the declared root")
        records.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
                        "sha256": file_sha256(path)})
    digest = hashlib.sha256()
    for row in records:
        digest.update(f"{row['path']}\0{row['sha256']}\0{row['bytes']}\n".encode())
    return {"file_count": len(records), "total_bytes": sum(r["bytes"] for r in records),
            "aggregate_sha256": digest.hexdigest(), "files": records}


def fixed_mass(samples: list[tuple[float, float, float]], target: float) -> dict:
    from val_corpus_002_protocol import interpolate_fixed_mass
    solute = interpolate_fixed_mass(samples, target)
    return {"target_beverage_mass_kg": target, "cup_solute_mass_kg": solute,
            "tds_fraction": solute / target}


def interval_chemistry(samples: list[dict[str, float]], start: float, end: float,
                       initial: dict[str, float] | None = None) -> float:
    from val_corpus_002_protocol import ensure_initial_boundary_sample, interval_tds
    work = samples
    if start == 0 and (not work or work[0]["time_s"] > 0):
        if initial is None:
            raise ValueError("exact initial state required for zero boundary")
        work = ensure_initial_boundary_sample(work, **initial)
    triples = [(row["time_s"], row["solute_mass_rate_kg_s"],
                row["water_mass_rate_kg_s"] + row["solute_mass_rate_kg_s"]) for row in work]
    return interval_tds(triples, start, end)


@dataclass
class Evaluation:
    sequence: int
    rate: float
    objective: float | None
    status: str
    reason: str | None
    cache_hit: bool


def golden_section(objective: Callable[[float], float], lower: float, upper: float,
                   *, max_evaluations: int = 128, absolute_tolerance: float = 1e-10,
                   relative_tolerance: float = 1e-8) -> dict:
    if not (math.isfinite(lower) and math.isfinite(upper) and lower < upper):
        raise ValueError("invalid optimizer bounds")
    cache: dict[str, Evaluation] = {}; trace: list[dict] = []; evaluations = 0
    context = {"lower": lower, "upper": upper, "interior_low": None,
               "interior_high": None, "decision": "INITIALIZE"}
    def evaluate(rate: float) -> Evaluation:
        nonlocal evaluations
        key = rate.hex()
        if key in cache:
            prior = cache[key]
            trace.append({**prior.__dict__, "sequence": len(trace), "cache_hit": True,
                          "rate_hex": key, **context})
            return prior
        if evaluations >= max_evaluations:
            raise RuntimeError("evaluation limit exhausted")
        try:
            value = float(objective(rate))
            if not math.isfinite(value): raise ValueError("NONFINITE_OBJECTIVE")
            status, reason = "PASS", None
        except Exception as exc:  # typed failed synthetic/model evaluation
            value, status, reason = None, "FAILED_EVALUATION", str(exc)
        item = Evaluation(len(trace), rate, value, status, reason, False)
        cache[key] = item; evaluations += 1
        trace.append({**item.__dict__, "rate_hex": key, **context})
        return item
    phi = (1 + math.sqrt(5.0)) / 2.0
    a, b = lower, upper
    c, d = b - (b-a)/phi, a + (b-a)/phi
    context.update(interior_low=min(c, d), interior_high=max(c, d))
    exhausted = False
    try:
        ec, ed = evaluate(min(c, d)), evaluate(max(c, d))
        while b-a > absolute_tolerance + relative_tolerance * max(abs(a), abs(b)):
            vc = math.inf if ec.objective is None else ec.objective
            vd = math.inf if ed.objective is None else ed.objective
            if vc <= vd:  # equality retains lower interval and implements lower-k tie break
                b, d, ed = d, c, ec; c = b - (b-a)/phi
                context.update(lower=a, upper=b, interior_low=min(c, d),
                               interior_high=max(c, d), decision="RETAIN_LOWER_INTERVAL")
                ec = evaluate(c)
            else:
                a, c, ec = c, d, ed; d = a + (b-a)/phi
                context.update(lower=a, upper=b, interior_low=min(c, d),
                               interior_high=max(c, d), decision="RETAIN_UPPER_INTERVAL")
                ed = evaluate(d)
        context.update(lower=a, upper=b, decision="EVALUATE_BOUNDARIES_FOR_FINAL_SELECTION")
        evaluate(lower); evaluate(upper)
    except RuntimeError:
        exhausted = True
    valid = [item for item in cache.values() if item.objective is not None]
    if not valid:
        return {"status": "FAIL_NO_VALID_EVALUATION", "evaluations": evaluations, "trace": trace}
    best = min(valid, key=lambda item: (item.objective, item.rate))
    return {"status": "NONCONVERGED_EVALUATION_LIMIT" if exhausted else "PASS",
            "evaluations": evaluations, "selected_rate": best.rate,
            "selected_objective": best.objective, "lower_rate_tie_break": True,
            "trace": trace}


def production_metrics(source: list[float], model: list[float], sd: list[float | None]) -> dict:
    if not (len(source) == len(model) == len(sd)) or not source:
        raise ValueError("metric vectors must have equal nonzero length")
    residuals = [m-s for s, m in zip(source, model)]
    return {"absolute_error": [abs(x) for x in residuals],
            "relative_error": [None if s == 0 else (m-s)/s for s, m in zip(source, model)],
            "rmse": math.sqrt(sum(x*x for x in residuals)/len(residuals)),
            "mae": sum(abs(x) for x in residuals)/len(residuals),
            "bias": sum(residuals)/len(residuals),
            "standardized_residual": [None if v is None or v <= 0 else r/v for r, v in zip(residuals, sd)]}


def axis_contrast(high: list[float], low: list[float]) -> list[float]:
    if len(high) != len(low): raise ValueError("axis vectors differ")
    return [a-b for a, b in zip(high, low)]


def finite_range_sensitivity(low_p: float, high_p: float,
                             low_y: list[float], high_y: list[float]) -> list[float]:
    values = [low_p, high_p, *low_y, *high_y]
    if any(not math.isfinite(v) or v <= 0 for v in values) or len(low_y) != len(high_y):
        raise ValueError("finite-range sensitivity requires positive finite paired values")
    denominator = math.log(high_p)-math.log(low_p)
    return [(math.log(hi)-math.log(lo))/denominator for lo, hi in zip(low_y, high_y)]


def calibration_objective(source: list[float], model: list[float]) -> float:
    """Frozen Experiment-7/H1 three-mass unweighted RMSE objective."""
    if len(source) != 3 or len(model) != 3:
        raise ValueError("calibration objective requires exactly three masses")
    return production_metrics(source, model, [None, None, None])["rmse"]


def source_species_limitation_audit(named_species: dict[str, list[float]],
                                    aggregate_tds: list[float]) -> dict:
    if not aggregate_tds or any(not math.isfinite(x) or x < 0 for x in aggregate_tds):
        raise ValueError("invalid aggregate source series")
    for name, values in named_species.items():
        if not name or len(values) != len(aggregate_tds) or any(not math.isfinite(x) or x < 0 for x in values):
            raise ValueError("invalid named-species source series")
    return {"status": "SOURCE_ONLY_SPECIES_LIMITATION_AUDIT",
            "named_species": sorted(named_species),
            "solver_predicted_named_species": False,
            "aggregate_residual_attribution": "NOT_IDENTIFIED",
            "multispecies_physics_authorized": False}


class AccessBarrier:
    def __init__(self) -> None:
        self.state = "B0_SYNTHETIC_ONLY"; self.p2_rate = None
    def authorize_b1(self, authority: str) -> None:
        if authority != "SEPARATE_HUMAN_OWNER_B1_AUTHORITY": raise PermissionError("B1 authority absent")
        self.state = "B1_EXP7_H1_ONLY"
    def require_result_access(self, case: str, *, protected: bool = False) -> None:
        if protected: raise PermissionError("protected scoring is prohibited")
        if self.state == "B0_SYNTHETIC_ONLY": raise PermissionError("model-result access prohibited in B0")
        if case != "SCHM_EXP7_P2_FIXED_AFTER_EXP7_CALIBRATION_H1":
            raise PermissionError("transfer result inaccessible before exact P2 freeze")
    def freeze_p2(self, manifest: dict) -> None:
        if self.state != "B1_EXP7_H1_ONLY" or set(manifest) != {"rate_s_inverse", "optimizer_trace_sha256", "calibration_case"}:
            raise PermissionError("exact B1 P2 manifest required")
        rate = manifest["rate_s_inverse"]
        if manifest["calibration_case"] != "SCHM_EXP7_P2_FIXED_AFTER_EXP7_CALIBRATION_H1" or not isinstance(rate, (int, float)) or not math.isfinite(rate):
            raise PermissionError("invalid exact P2 freeze")
        if not isinstance(manifest["optimizer_trace_sha256"], str) or len(manifest["optimizer_trace_sha256"]) != 64:
            raise PermissionError("optimizer trace identity absent")
        self.p2_rate = float(rate); self.state = "P2_FROZEN_TRANSFER_MAY_FOLLOW_SEPARATE_B2_AUTHORITY"
    @staticmethod
    def validate_command(arguments: list[str]) -> None:
        blocked = ("protected", "shape-scorer", "traces_per_brew", "shot_id")
        if any(token in " ".join(arguments).lower() for token in blocked):
            raise PermissionError("protected hydraulic comparison request refused")


def generate(root: Path, review_root: Path) -> None:
    inventory = build_configuration_inventory(root)
    binding = bind_reference(root, review_root)
    dump(root / CASE_DIR / "VAL_CORPUS_002_STAGE_B0_CONFIGURATION_INVENTORY.json", inventory)
    dump(root / CASE_DIR / "VAL_CORPUS_002_PREDECESSOR_PARITY_REFERENCE_BINDING.json", binding)
    dump(root / CASE_DIR / "VAL_CORPUS_002_STAGE_B0_ACCESS_AND_CLAIM_BARRIERS.json", {
        "schema_version": 1, "initial_state": "B0_SYNTHETIC_ONLY",
        "model_result_access": "PROHIBITED", "transfer_result_access": "PROHIBITED",
        "protected_scoring": "PROHIBITED", "post_transfer_refit_path": "ABSENT",
        "p2_mode_specific_rates": "PROHIBITED",
        "claim_ceiling": "PHYSICAL_VALIDATION_NOT_ESTABLISHED",
        "normal_end_state": "VAL_CORPUS_002_STAGE_B0_TOOLING_COMPLETE_PENDING_REVIEW"})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--review-root", type=Path,
                        default=Path("../.wp03-002-exact-head-review"))
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args(); root = args.root.resolve()
    if args.generate: generate(root, args.review_root.resolve())
    else:
        build_configuration_inventory(root); bind_reference(root, args.review_root.resolve())
    print(json.dumps({"status": "PASS", "openfoam": "NOT_RUN",
                      "governed_scoring": "NOT_PERFORMED"}, indent=2))


if __name__ == "__main__":
    main()
