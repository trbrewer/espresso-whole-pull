#!/usr/bin/env python3
"""Bounded, deterministic OBS-001 multiplier evidence sidecars.

This module is deliberately one-way: callers submit copies of already-computed
values and no method returns a value that can participate in scientific logic.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

CONTRACT_ID = "espresso.whole_pull.sci_lc_001a.multiplier_diagnostics.v1"
IMPLEMENTATION_VERSION = "OBS_001_R1_V1"
STOP_SCHEMA = "espresso.whole_pull.sci_lc_001a.multiplier_stop_event.v1"
SUMMARY_SCHEMA = "espresso.whole_pull.sci_lc_001a.multiplier_margin_summary.v1"
HEALTH_SCHEMA = "espresso.whole_pull.sci_lc_001a.multiplier_diagnostic_health.v2"
MANIFEST_SCHEMA = "espresso.whole_pull.sci_lc_001a.multiplier_diagnostic_manifest.v2"
MODES = ("DISABLED", "ENABLED_OPTIONAL", "ENABLED_REQUIRED")
RECORD_TYPES = ("MULTIPLIER_STOP_EVENT", "MULTIPLIER_MARGIN_SUMMARY")
APPLICABLE = "MULTIPLIER_EVOLUTION_APPLICABLE"
NOT_APPLICABLE = "NOT_APPLICABLE_NO_RESISTANCE_EVOLUTION"
APPLICABILITY_STATES = (APPLICABLE, NOT_APPLICABLE)
TERMINAL_DISPOSITIONS = (
    "MULTIPLIER_MARGIN_SUMMARY_WRITTEN",
    "MULTIPLIER_STOP_EVENT_WRITTEN",
    NOT_APPLICABLE,
    "APPLICABLE_OTHER_TERMINAL_EVIDENCE_INCOMPLETE",
    "DIAGNOSTIC_EVIDENCE_INCOMPLETE",
)
FRESH_EXECUTION_FAILURE = "DIAGNOSTIC_ENABLED_REQUIRES_FRESH_COMPLETE_EXECUTION"
BACKENDS = ("REAL_STAGE_A", "SYNTHETIC_TEST_ONLY")
ADMIN_FAILURE = "DIAGNOSTIC_EVIDENCE_INCOMPLETE"
ADMIN_REASONS = (
    "SERIALIZATION_FAILURE", "SCHEMA_FAILURE", "WRITE_FAILURE", "ATOMIC_WRITE_FAILURE",
    "MISSING_TERMINAL_RECORD", "HEALTH_FINALIZATION_FAILURE",
    "MANIFEST_RECONCILIATION_FAILURE",
)
TIE_BREAK_ORDER = (
    "accepted_step_index", "candidate_step_index", "simulation_time",
    "profile_order", "sector_index", "event_sequence",
)


def multiplier_applicability(resistance_evolution_law: object) -> str:
    """Classify applicability from frozen key semantics, never observations."""
    if resistance_evolution_law == "NO_EVOLUTION":
        return NOT_APPLICABLE
    if resistance_evolution_law == "SIGNED_LOCAL_FLOW_TO_RESISTANCE_FEEDBACK_SURROGATE":
        return APPLICABLE
    raise ValueError("UNKNOWN_RESISTANCE_EVOLUTION_APPLICABILITY")


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def exact_float(value: float) -> dict:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("UNSUPPORTED_DIAGNOSTIC_FLOAT")
    number = float(value)
    category = ("NAN" if math.isnan(number) else "POSITIVE_INFINITY" if number == math.inf
                else "NEGATIVE_INFINITY" if number == -math.inf else "FINITE")
    return {
        "value": number if category == "FINITE" else None,
        "round_trip": repr(number),
        "ieee754_hex": struct.pack(">d", number).hex(),
        "dtype": "binary64",
        "finite_category": category,
    }


def exact_vector(values: Sequence[float], names: Sequence[str]) -> dict:
    if len(values) != len(names) or len(set(names)) != len(names):
        raise ValueError("STATE_VECTOR_COMPONENT_MAPPING_INVALID")
    return {"shape": [len(values)], "dtype": "binary64", "component_order": list(names),
            "elements": [exact_float(value) for value in values]}


@dataclass(frozen=True)
class DiagnosticConfig:
    mode: str = "DISABLED"
    sidecar_root: Path | None = None
    configuration_sha256: str = ""

    @property
    def enabled(self) -> bool:
        return self.mode != "DISABLED"

    @property
    def required(self) -> bool:
        return self.mode == "ENABLED_REQUIRED"

    @classmethod
    def from_field(cls, field: Mapping[str, object] | None) -> "DiagnosticConfig":
        if field is None:
            return cls(configuration_sha256=digest({"mode": "DISABLED"}))
        if set(field) != {"mode", "sidecar_root"} or field.get("mode") not in MODES:
            raise ValueError("INVALID_MULTIPLIER_DIAGNOSTIC_CONFIGURATION")
        mode = str(field["mode"])
        raw_root = field["sidecar_root"]
        if mode == "DISABLED":
            if raw_root is not None:
                raise ValueError("DISABLED_DIAGNOSTICS_FORBID_SIDECAR_ROOT")
            material = {"mode": mode, "sidecar_root": None}
            return cls(mode=mode, configuration_sha256=digest(material))
        if not isinstance(raw_root, str) or not Path(raw_root).is_absolute():
            raise ValueError("ENABLED_DIAGNOSTICS_REQUIRE_ABSOLUTE_SIDECAR_ROOT")
        root = Path(raw_root).resolve(strict=False)
        material = {"mode": mode, "sidecar_root": str(root)}
        return cls(mode=mode, sidecar_root=root, configuration_sha256=digest(material))


COMMON_REQUIRED = {
    "schema", "schema_version", "diagnostic_contract", "implementation_version",
    "implementation_sha256", "configuration_sha256", "repository", "candidate_head",
    "candidate_tree", "executor_sha256", "protocol_source_sha256", "protocol_json_sha256",
    "matrix_json_sha256", "matrix_csv_sha256", "plan_sha256", "backend", "run_id",
    "execution_authority", "diagnostic_authority", "key_id", "row_id", "arm", "profile",
    "model_variant", "process_id", "worker_id", "attempt_number", "record_type", "record_id",
}
COMMON_IDENTITY_REQUIRED = COMMON_REQUIRED - {
    "schema", "schema_version", "diagnostic_contract", "record_type", "record_id",
}


def record_identity(record: Mapping[str, object]) -> str:
    fields = {key: record[key] for key in (
        "schema", "diagnostic_contract", "implementation_sha256", "configuration_sha256",
        "candidate_head", "candidate_tree", "run_id", "key_id", "row_id", "profile",
        "attempt_number", "record_type",
    )}
    return digest(fields)


def _require_exact_keys(record: Mapping[str, object], required: set[str], optional: set[str]) -> None:
    if not isinstance(record, Mapping):
        raise ValueError("DIAGNOSTIC_SCHEMA_OBJECT_REQUIRED")
    missing = required - set(record)
    unknown = set(record) - required - optional
    if missing:
        raise ValueError("DIAGNOSTIC_SCHEMA_MISSING_FIELDS:" + ",".join(sorted(missing)))
    if unknown:
        raise ValueError("DIAGNOSTIC_SCHEMA_UNKNOWN_FIELDS:" + ",".join(sorted(unknown)))


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_GIT_ID = re.compile(r"[0-9a-f]{40}\Z")


def _integer(value: object, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError("DIAGNOSTIC_INTEGER_INVALID:" + name)
    return value


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError("DIAGNOSTIC_NUMBER_INVALID:" + name)
    return float(value)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("DIAGNOSTIC_IDENTIFIER_INVALID:" + name)
    return value


def _sha256(value: object, name: str, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError("DIAGNOSTIC_SHA256_INVALID:" + name)


def _enum(value: object, allowed: Sequence[str], name: str) -> None:
    if value not in allowed:
        raise ValueError("DIAGNOSTIC_ENUM_INVALID:" + name)


def validate_exact_float(value: object, name: str = "exact_float") -> float:
    if not isinstance(value, Mapping):
        raise ValueError("DIAGNOSTIC_EXACT_FLOAT_OBJECT_REQUIRED:" + name)
    _require_exact_keys(value, {"value", "round_trip", "ieee754_hex", "dtype", "finite_category"}, set())
    if value["dtype"] != "binary64":
        raise ValueError("DIAGNOSTIC_EXACT_FLOAT_DTYPE_INVALID:" + name)
    if not isinstance(value["ieee754_hex"], str) or re.fullmatch(r"[0-9a-f]{16}", value["ieee754_hex"]) is None:
        raise ValueError("DIAGNOSTIC_EXACT_FLOAT_HEX_INVALID:" + name)
    if not isinstance(value["round_trip"], str):
        raise ValueError("DIAGNOSTIC_EXACT_FLOAT_ROUND_TRIP_INVALID:" + name)
    decoded = struct.unpack(">d", bytes.fromhex(value["ieee754_hex"]))[0]
    category = value["finite_category"]
    _enum(category, ("FINITE", "NAN", "POSITIVE_INFINITY", "NEGATIVE_INFINITY"), name + ".finite_category")
    expected = ("NAN" if math.isnan(decoded) else "POSITIVE_INFINITY" if decoded == math.inf
                else "NEGATIVE_INFINITY" if decoded == -math.inf else "FINITE")
    if category != expected:
        raise ValueError("DIAGNOSTIC_EXACT_FLOAT_CATEGORY_MISMATCH:" + name)
    try:
        round_trip = float(value["round_trip"])
    except ValueError as exc:
        raise ValueError("DIAGNOSTIC_EXACT_FLOAT_ROUND_TRIP_INVALID:" + name) from exc
    if expected == "FINITE":
        numeric = _number(value["value"], name + ".value")
        if struct.pack(">d", numeric) != struct.pack(">d", decoded) or struct.pack(">d", round_trip) != struct.pack(">d", decoded):
            raise ValueError("DIAGNOSTIC_EXACT_FLOAT_VALUE_HEX_MISMATCH:" + name)
        if value["round_trip"] != repr(decoded):
            raise ValueError("DIAGNOSTIC_EXACT_FLOAT_NONCANONICAL_ROUND_TRIP:" + name)
    else:
        if value["value"] is not None:
            raise ValueError("DIAGNOSTIC_EXACT_FLOAT_NONFINITE_VALUE_INVALID:" + name)
        if expected == "NAN" and not math.isnan(round_trip):
            raise ValueError("DIAGNOSTIC_EXACT_FLOAT_VALUE_HEX_MISMATCH:" + name)
        if expected != "NAN" and round_trip != decoded:
            raise ValueError("DIAGNOSTIC_EXACT_FLOAT_VALUE_HEX_MISMATCH:" + name)
    return decoded


def validate_exact_vector(value: object, name: str = "state") -> None:
    if not isinstance(value, Mapping):
        raise ValueError("DIAGNOSTIC_STATE_VECTOR_OBJECT_REQUIRED:" + name)
    _require_exact_keys(value, {"shape", "dtype", "component_order", "elements"}, set())
    shape = value["shape"]
    names = value["component_order"]
    elements = value["elements"]
    if not isinstance(shape, list) or len(shape) != 1:
        raise ValueError("DIAGNOSTIC_STATE_VECTOR_SHAPE_INVALID:" + name)
    size = _integer(shape[0], name + ".shape")
    if value["dtype"] != "binary64" or not isinstance(names, list) or not isinstance(elements, list):
        raise ValueError("DIAGNOSTIC_STATE_VECTOR_TYPE_INVALID:" + name)
    if len(names) != size or len(elements) != size or len(set(names)) != size:
        raise ValueError("DIAGNOSTIC_STATE_VECTOR_COMPONENT_MAPPING_INVALID:" + name)
    for index, component in enumerate(names):
        _text(component, f"{name}.component_order[{index}]")
    for index, element in enumerate(elements):
        validate_exact_float(element, f"{name}.elements[{index}]")


def _validate_scientific_component_order(vector: Mapping[str, object], name: str) -> None:
    names = vector["component_order"]
    def rank(component: str) -> tuple[int, int]:
        match = re.fullmatch(r"([px])_(\d+)", component)
        if match:
            return (0 if match.group(1) == "p" else 2, int(match.group(2)))
        if component == "p_upstream":
            return (1, 0)
        raise ValueError("DIAGNOSTIC_STATE_COMPONENT_NAME_INVALID:" + name)
    if [rank(component) for component in names] != sorted(rank(component) for component in names):
        raise ValueError("DIAGNOSTIC_STATE_COMPONENT_ORDER_INVALID:" + name)
    pressure = [int(component[2:]) for component in names if re.fullmatch(r"p_\d+", component)]
    evolving = [int(component[2:]) for component in names if re.fullmatch(r"x_\d+", component)]
    if pressure != list(range(len(pressure))) or evolving != list(range(len(evolving))):
        raise ValueError("DIAGNOSTIC_STATE_COMPONENT_INDEX_MAPPING_INVALID:" + name)
    if evolving and len(evolving) != len(pressure):
        raise ValueError("DIAGNOSTIC_STATE_COMPONENT_DIMENSION_INVALID:" + name)
    if names.count("p_upstream") > 1:
        raise ValueError("DIAGNOSTIC_STATE_COMPONENT_MAPPING_INVALID:" + name)


def _validate_authority(value: object, name: str) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("DIAGNOSTIC_AUTHORITY_OBJECT_REQUIRED:" + name)
    _require_exact_keys(value, {"identity", "sha256"}, set())
    _text(value["identity"], name + ".identity")
    _sha256(value["sha256"], name + ".sha256", nullable=True)


def _validate_common(record: Mapping[str, object]) -> None:
    for name in ("implementation_sha256", "configuration_sha256", "executor_sha256",
                 "protocol_source_sha256", "protocol_json_sha256", "matrix_json_sha256",
                 "matrix_csv_sha256", "plan_sha256"):
        _sha256(record[name], name)
    for name in ("repository", "run_id", "key_id", "row_id", "arm", "profile",
                 "model_variant", "worker_id", "implementation_version"):
        _text(record[name], name)
    for name in ("candidate_head", "candidate_tree"):
        if not isinstance(record[name], str) or _GIT_ID.fullmatch(record[name]) is None:
            raise ValueError("DIAGNOSTIC_GIT_IDENTITY_INVALID:" + name)
    _enum(record["backend"], BACKENDS, "backend")
    _integer(record["process_id"], "process_id")
    _integer(record["attempt_number"], "attempt_number", minimum=1)
    _validate_authority(record["execution_authority"], "execution_authority")
    _validate_authority(record["diagnostic_authority"], "diagnostic_authority")


def _validate_summary(record: Mapping[str, object]) -> None:
    _integer(record["guard_evaluations"], "guard_evaluations", minimum=1)
    minimum = record["minimum"]
    if not isinstance(minimum, Mapping):
        raise ValueError("DIAGNOSTIC_SUMMARY_MINIMUM_OBJECT_REQUIRED")
    fields = set(TIE_BREAK_ORDER) | {"lower_distance", "upper_distance", "state", "sector",
        "beta", "x_i", "M_i", "H_i0", "H_i", "tolerances", "contact_state",
        "contact_derivative", "finite_category", "global_minimum_distance", "relevant_bound"}
    _require_exact_keys(minimum, fields, set())
    for name in ("accepted_step_index", "candidate_step_index", "profile_order", "sector_index",
                 "event_sequence", "sector"):
        _integer(minimum[name], "minimum." + name)
    validate_exact_float(minimum["simulation_time"], "minimum.simulation_time")
    lower = validate_exact_float(minimum["lower_distance"], "minimum.lower_distance")
    upper = validate_exact_float(minimum["upper_distance"], "minimum.upper_distance")
    global_minimum = validate_exact_float(minimum["global_minimum_distance"], "minimum.global_minimum_distance")
    relevant = "LOWER_BOUND" if lower <= upper else "UPPER_BOUND"
    if global_minimum != min(lower, upper) or minimum["relevant_bound"] != relevant:
        raise ValueError("DIAGNOSTIC_SUMMARY_MARGIN_BOUND_INCONSISTENT")
    validate_exact_vector(minimum["state"], "minimum.state")
    _validate_scientific_component_order(minimum["state"], "minimum.state")
    exact = {name: validate_exact_float(minimum[name], "minimum." + name)
             for name in ("beta", "x_i", "M_i", "H_i0", "H_i")}
    if (lower != exact["M_i"] - .25 or upper != 4. - exact["M_i"] or
            exact["M_i"] != math.exp(exact["beta"] * exact["x_i"]) or
            exact["H_i"] != exact["H_i0"] * exact["M_i"]):
        raise ValueError("DIAGNOSTIC_SUMMARY_SCIENTIFIC_PRIMITIVE_INCONSISTENT")
    tolerances = minimum["tolerances"]
    if not isinstance(tolerances, Mapping):
        raise ValueError("DIAGNOSTIC_TOLERANCES_OBJECT_REQUIRED")
    _require_exact_keys(tolerances, {"boundary", "derivative", "event_root"}, set())
    expected_tolerances = {"boundary": 1e-12, "derivative": 1e-14, "event_root": 1e-10}
    for name, expected in expected_tolerances.items():
        if validate_exact_float(tolerances[name], "minimum.tolerances." + name) != expected:
            raise ValueError("DIAGNOSTIC_TOLERANCE_INVALID:" + name)
    _enum(minimum["contact_state"], ("INSIDE", "EXACT_CONTACT", "ORDINARY"), "minimum.contact_state")
    if minimum["contact_derivative"] is not None:
        validate_exact_float(minimum["contact_derivative"], "minimum.contact_derivative")
    _enum(minimum["finite_category"], ("FINITE", "NAN", "POSITIVE_INFINITY", "NEGATIVE_INFINITY"), "minimum.finite_category")
    if minimum["finite_category"] != minimum["M_i"]["finite_category"]:
        raise ValueError("DIAGNOSTIC_SUMMARY_FINITE_CATEGORY_MISMATCH")


def _validate_stop(record: Mapping[str, object]) -> None:
    scientific = record["scientific"]
    _require_exact_keys(scientific, {"status", "stop_token", "finite_category", "contact_category",
                                    "exited_bound", "stop_direction"}, set())
    stop_token = scientific["stop_token"]
    if (scientific["status"] != "STOPPED" or not isinstance(stop_token, str) or not (
            stop_token == "STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUTWARD_OR_OUT_OF_RANGE_NO_CLIPPING" or
            stop_token == "STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUTWARD_CROSSING_NO_CLIPPING" or
            stop_token.startswith("STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUTWARD_CROSSING_NO_CLIPPING:"))):
        raise ValueError("DIAGNOSTIC_STOP_SCIENTIFIC_DISPOSITION_INVALID")
    _enum(scientific["finite_category"], ("FINITE", "NONFINITE"), "scientific.finite_category")
    _enum(scientific["contact_category"], ("EXACT_CONTACT", "LOCATED_EVENT", "RAW_GUARD"), "scientific.contact_category")
    _enum(scientific["exited_bound"], ("LOWER_BOUND", "UPPER_BOUND", "UNKNOWN"), "scientific.exited_bound")
    _enum(scientific["stop_direction"], ("OUTWARD",), "scientific.stop_direction")
    trigger = record["trigger"]
    _require_exact_keys(trigger, {"sector_count", "triggering_sectors", "primary_sector", "parameter_bindings"}, set())
    sector_count = _integer(trigger["sector_count"], "trigger.sector_count", minimum=1)
    triggering = trigger["triggering_sectors"]
    if not isinstance(triggering, list) or not triggering or triggering != sorted(triggering):
        raise ValueError("DIAGNOSTIC_TRIGGERING_SECTORS_INVALID")
    if any(type(x) is not int or x < 0 or x >= sector_count for x in triggering) or len(set(triggering)) != len(triggering):
        raise ValueError("DIAGNOSTIC_TRIGGERING_SECTORS_INVALID")
    if trigger["primary_sector"] not in triggering or trigger["primary_sector"] != min(triggering):
        raise ValueError("DIAGNOSTIC_PRIMARY_SECTOR_INVALID")
    if not isinstance(trigger["parameter_bindings"], Mapping):
        raise ValueError("DIAGNOSTIC_PARAMETER_BINDINGS_INVALID")
    _require_exact_keys(trigger["parameter_bindings"], set(), set())
    timeline = record["timeline"]
    _require_exact_keys(timeline, {"prior_accepted_time", "prior_accepted_step_index", "candidate_time",
        "candidate_step_index", "event_root_present", "event_root_time", "evaluation_stage"}, set())
    validate_exact_float(timeline["prior_accepted_time"], "timeline.prior_accepted_time")
    validate_exact_float(timeline["candidate_time"], "timeline.candidate_time")
    _integer(timeline["prior_accepted_step_index"], "timeline.prior_accepted_step_index")
    _integer(timeline["candidate_step_index"], "timeline.candidate_step_index")
    if type(timeline["event_root_present"]) is not bool:
        raise ValueError("DIAGNOSTIC_EVENT_ROOT_FLAG_INVALID")
    if timeline["event_root_present"]:
        validate_exact_float(timeline["event_root_time"], "timeline.event_root_time")
        if timeline["evaluation_stage"] != "LOCATED_EVENT_ROOT":
            raise ValueError("DIAGNOSTIC_EVENT_ROOT_STAGE_INVALID")
    elif timeline["event_root_time"] is not None or timeline["evaluation_stage"] != "RAW_RANGE_GUARD":
        raise ValueError("DIAGNOSTIC_EVENT_ROOT_ABSENCE_INVALID")
    states = record["states"]
    _require_exact_keys(states, {"prior_accepted", "candidate", "event_root"}, set())
    validate_exact_vector(states["prior_accepted"], "states.prior_accepted")
    validate_exact_vector(states["candidate"], "states.candidate")
    _validate_scientific_component_order(states["prior_accepted"], "states.prior_accepted")
    _validate_scientific_component_order(states["candidate"], "states.candidate")
    if states["event_root"] is not None:
        validate_exact_vector(states["event_root"], "states.event_root")
        _validate_scientific_component_order(states["event_root"], "states.event_root")
    if (states["event_root"] is not None) != timeline["event_root_present"]:
        raise ValueError("DIAGNOSTIC_EVENT_ROOT_STATE_MISMATCH")
    sectors = record["sectors"]
    if not isinstance(sectors, list) or [item.get("sector") for item in sectors] != triggering:
        raise ValueError("DIAGNOSTIC_SECTOR_PAYLOAD_BINDING_INVALID")
    sector_fields = {"sector", "beta", "x_i", "beta_x_i", "M_i", "H_i0", "H_i",
                     "preceding_valid", "candidate", "event_root", "lower_bound", "upper_bound"}
    for index, item in enumerate(sectors):
        _require_exact_keys(item, sector_fields, set())
        _integer(item["sector"], f"sectors[{index}].sector")
        values = {name: validate_exact_float(item[name], f"sectors[{index}].{name}")
                  for name in ("beta", "x_i", "beta_x_i", "M_i", "H_i0", "H_i", "lower_bound", "upper_bound")}
        if (values["beta_x_i"] != values["beta"] * values["x_i"] or
                values["M_i"] != math.exp(values["beta_x_i"]) or
                values["H_i"] != values["H_i0"] * values["M_i"]):
            raise ValueError("DIAGNOSTIC_STOP_SECTOR_PRIMITIVE_INCONSISTENT")
        if values["lower_bound"] != .25 or values["upper_bound"] != 4.:
            raise ValueError("DIAGNOSTIC_STOP_BOUND_INVALID")
        for optional_state in ("preceding_valid", "candidate", "event_root"):
            if item[optional_state] is not None and not isinstance(item[optional_state], Mapping):
                raise ValueError("DIAGNOSTIC_STOP_SECTOR_STATE_INVALID")
        if item["preceding_valid"] is not None or item["candidate"] is not None:
            raise ValueError("DIAGNOSTIC_STOP_SECTOR_UNDECLARED_STATE_PAYLOAD")
        if item["event_root"] is not None:
            _require_exact_keys(item["event_root"], {"x_i", "M_i"}, set())
            root_x = validate_exact_float(item["event_root"]["x_i"], f"sectors[{index}].event_root.x_i")
            root_m = validate_exact_float(item["event_root"]["M_i"], f"sectors[{index}].event_root.M_i")
            if root_x != values["x_i"] or root_m != values["M_i"]:
                raise ValueError("DIAGNOSTIC_STOP_SECTOR_EVENT_ROOT_INCONSISTENT")
    guard = record["guard_semantics"]
    allowed_guard = {"guard_decision", "no_clipping"}
    full_guard = allowed_guard | {"boundary_tolerance", "derivative_tolerance", "located_root_tolerance"}
    _require_exact_keys(guard, allowed_guard, full_guard - allowed_guard)
    if guard["guard_decision"] != "STOP" or guard["no_clipping"] is not True:
        raise ValueError("DIAGNOSTIC_GUARD_SEMANTICS_INVALID")
    for name, expected in (("boundary_tolerance", 1e-12), ("derivative_tolerance", 1e-14), ("located_root_tolerance", 1e-10)):
        if name in guard and validate_exact_float(guard[name], "guard_semantics." + name) != expected:
            raise ValueError("DIAGNOSTIC_GUARD_TOLERANCE_INVALID:" + name)
    margins = record["margins"]
    if not isinstance(margins, Mapping):
        raise ValueError("DIAGNOSTIC_STOP_MARGINS_OBJECT_REQUIRED")
    permitted_margin_sets = ({"lower", "upper"}, {"lower", "upper", "minimum", "absolute_exceedance",
        "relative_exceedance", "normalized_interval_exceedance"})
    if set(margins) not in permitted_margin_sets:
        raise ValueError("DIAGNOSTIC_STOP_MARGINS_FIELDS_INVALID")
    for name, value in margins.items():
        if value is not None:
            validate_exact_float(value, "margins." + name)
    if set(margins) != {"lower", "upper", "minimum", "absolute_exceedance",
                        "relative_exceedance", "normalized_interval_exceedance"}:
        raise ValueError("DIAGNOSTIC_STOP_MARGIN_CONTRACT_INCOMPLETE")
    lower_margin = validate_exact_float(margins["lower"], "margins.lower")
    upper_margin = validate_exact_float(margins["upper"], "margins.upper")
    minimum_margin = validate_exact_float(margins["minimum"], "margins.minimum")
    primary_payload = sectors[trigger["triggering_sectors"].index(trigger["primary_sector"])]
    primary_multiplier = validate_exact_float(primary_payload["M_i"], "primary.M_i")
    if (lower_margin != primary_multiplier - .25 or upper_margin != 4. - primary_multiplier or
            minimum_margin != min(lower_margin, upper_margin)):
        raise ValueError("DIAGNOSTIC_STOP_MARGIN_BOUND_INCONSISTENT")
    exited_bound = scientific["exited_bound"]
    finite = scientific["finite_category"] == "FINITE"
    if finite and exited_bound == "UNKNOWN":
        raise ValueError("DIAGNOSTIC_STOP_FINITE_BOUND_UNKNOWN")
    selected_margin = lower_margin if exited_bound == "LOWER_BOUND" else upper_margin
    if finite and selected_margin > 1e-12:
        raise ValueError("DIAGNOSTIC_STOP_EXITED_BOUND_MARGIN_INCONSISTENT")
    if scientific["contact_category"] in ("EXACT_CONTACT", "LOCATED_EVENT") and selected_margin != 0.0:
        raise ValueError("DIAGNOSTIC_STOP_CONTACT_MARGIN_INCONSISTENT")
    if finite and selected_margin == 0.0 and scientific["contact_category"] == "RAW_GUARD":
        raise ValueError("DIAGNOSTIC_STOP_CONTACT_CATEGORY_INCONSISTENT")
    exceedance_names = ("absolute_exceedance", "relative_exceedance", "normalized_interval_exceedance")
    exceedances = [margins[name] for name in exceedance_names]
    if finite and selected_margin < 0.0:
        if any(value is None for value in exceedances):
            raise ValueError("DIAGNOSTIC_STOP_EXCEEDANCE_REQUIRED")
        absolute = validate_exact_float(margins["absolute_exceedance"], "margins.absolute_exceedance")
        relative = validate_exact_float(margins["relative_exceedance"], "margins.relative_exceedance")
        normalized = validate_exact_float(margins["normalized_interval_exceedance"], "margins.normalized_interval_exceedance")
        bound = .25 if exited_bound == "LOWER_BOUND" else 4.
        if absolute != -selected_margin or relative != absolute / bound or normalized != absolute / 3.75:
            raise ValueError("DIAGNOSTIC_STOP_EXCEEDANCE_INCONSISTENT")
    elif any(value is not None for value in exceedances):
        raise ValueError("DIAGNOSTIC_STOP_EXCEEDANCE_NOT_APPLICABLE")
    correlation = record["correlation"]
    _require_exact_keys(correlation, {"guard", "contact", "event_root", "stopped_result", "final_record"}, set())
    for name in ("guard", "contact", "stopped_result", "final_record"):
        _text(correlation[name], "correlation." + name)
    if correlation["event_root"] is not None:
        _text(correlation["event_root"], "correlation.event_root")


def validate_record(record: Mapping[str, object]) -> None:
    if not isinstance(record, Mapping):
        raise ValueError("DIAGNOSTIC_RECORD_OBJECT_REQUIRED")
    schema = record.get("schema")
    if schema == STOP_SCHEMA:
        required = COMMON_REQUIRED | {"scientific", "trigger", "timeline", "states", "sectors",
                                      "guard_semantics", "margins", "correlation"}
        _require_exact_keys(record, required, {"integrity_sha256"})
        if record.get("record_type") != "MULTIPLIER_STOP_EVENT":
            raise ValueError("DIAGNOSTIC_RECORD_TYPE_INVALID")
        _validate_stop(record)
    elif schema == SUMMARY_SCHEMA:
        required = COMMON_REQUIRED | {"scientific_terminal_status", "guard_evaluations",
                                      "minimum", "tie_break_order"}
        _require_exact_keys(record, required, {"integrity_sha256"})
        if record.get("record_type") != "MULTIPLIER_MARGIN_SUMMARY" or record.get(
                "scientific_terminal_status") != "COMPLETE":
            raise ValueError("DIAGNOSTIC_SUMMARY_DISPOSITION_INVALID")
        if tuple(record.get("tie_break_order", ())) != TIE_BREAK_ORDER:
            raise ValueError("DIAGNOSTIC_TIE_BREAK_ORDER_INVALID")
        _validate_summary(record)
    else:
        raise ValueError("DIAGNOSTIC_SCHEMA_IDENTITY_INVALID")
    if record.get("schema_version") != 1 or record.get("diagnostic_contract") != CONTRACT_ID:
        raise ValueError("DIAGNOSTIC_SCHEMA_VERSION_INVALID")
    _validate_common(record)
    if record.get("record_id") != record_identity(record):
        raise ValueError("DIAGNOSTIC_RECORD_IDENTITY_INVALID")
    if record.get("integrity_sha256") is not None:
        body = dict(record); supplied = body.pop("integrity_sha256")
        if supplied != digest(body):
            raise ValueError("DIAGNOSTIC_RECORD_INTEGRITY_INVALID")


def validate_run_object(record: Mapping[str, object]) -> None:
    if not isinstance(record, Mapping):
        raise ValueError("DIAGNOSTIC_RUN_OBJECT_REQUIRED")
    schema = record.get("schema")
    if schema == HEALTH_SCHEMA:
        required = {"schema", "schema_version", "diagnostic_contract", "expected_dynamic_keys",
            "applicable_dynamic_keys", "not_applicable_dynamic_keys", "started_dynamic_keys",
            "applicable_complete_keys", "applicable_multiplier_stopped_keys",
            "other_applicable_terminal_states", "completed_summaries_expected",
            "completed_summaries_written", "stop_events_expected", "stop_events_written",
            "not_applicable_dispositions", "terminal_diagnostic_dispositions",
            "duplicate_identities", "missing_identities", "missing_applicable_records",
            "unexpected_records", "serialization_failures", "schema_failures", "write_failures",
            "atomic_rename_failures", "finalization_failures", "unexpected_exceptions",
            "diagnostic_mode", "evidence_required", "clean_finalization", "implementation_version",
            "configuration_sha256", "manifest_sha256", "administrative_failures"}
        _require_exact_keys(record, required, set())
        _enum(record["diagnostic_mode"], MODES, "health.diagnostic_mode")
        for name in required - {"schema", "diagnostic_contract", "diagnostic_mode", "implementation_version",
                                "configuration_sha256", "manifest_sha256", "missing_identities",
                                "missing_applicable_records", "administrative_failures"}:
            if name in ("evidence_required", "clean_finalization"):
                if type(record[name]) is not bool: raise ValueError("DIAGNOSTIC_HEALTH_BOOLEAN_INVALID:" + name)
            elif name != "schema_version": _integer(record[name], "health." + name)
        for name in ("missing_identities", "missing_applicable_records", "administrative_failures"):
            if not isinstance(record[name], list): raise ValueError("DIAGNOSTIC_HEALTH_LIST_INVALID:" + name)
        for name in ("missing_identities", "missing_applicable_records"):
            if len(record[name]) != len(set(record[name])):
                raise ValueError("DIAGNOSTIC_HEALTH_DUPLICATE_LIST_IDENTITY:" + name)
            for key_id in record[name]: _text(key_id, "health." + name)
        for failure in record["administrative_failures"]:
            if not isinstance(failure, Mapping): raise ValueError("DIAGNOSTIC_HEALTH_FAILURE_OBJECT_REQUIRED")
            _require_exact_keys(failure, {"namespace", "key_id", "reason", "detail"}, set())
            if failure["namespace"] != ADMIN_FAILURE: raise ValueError("DIAGNOSTIC_HEALTH_FAILURE_NAMESPACE_INVALID")
            _text(failure["key_id"], "health.failure.key_id")
            _enum(failure["reason"], ADMIN_REASONS, "health.failure.reason")
            _text(failure["detail"], "health.failure.detail")
        _sha256(record["configuration_sha256"], "health.configuration_sha256")
        _sha256(record["manifest_sha256"], "health.manifest_sha256")
        if record["expected_dynamic_keys"] != record["applicable_dynamic_keys"] + record["not_applicable_dynamic_keys"]:
            raise ValueError("DIAGNOSTIC_HEALTH_APPLICABILITY_RECONCILIATION_INVALID")
        if record["applicable_dynamic_keys"] != (record["applicable_complete_keys"] +
                record["applicable_multiplier_stopped_keys"] + record["other_applicable_terminal_states"]):
            raise ValueError("DIAGNOSTIC_HEALTH_TERMINAL_RECONCILIATION_INVALID")
        if record["completed_summaries_expected"] != record["applicable_complete_keys"] or record["stop_events_expected"] != record["applicable_multiplier_stopped_keys"]:
            raise ValueError("DIAGNOSTIC_HEALTH_EXPECTED_RECORD_COUNTS_INVALID")
        if record["terminal_diagnostic_dispositions"] != record["started_dynamic_keys"]:
            raise ValueError("DIAGNOSTIC_HEALTH_TERMINAL_DISPOSITION_COUNT_INVALID")
        errors = (record["missing_identities"] or record["missing_applicable_records"] or record["unexpected_records"] or
                  record["duplicate_identities"] or record["administrative_failures"] or
                  record["completed_summaries_expected"] != record["completed_summaries_written"] or
                  record["stop_events_expected"] != record["stop_events_written"] or
                  record["not_applicable_dynamic_keys"] != record["not_applicable_dispositions"])
        if record["clean_finalization"] == bool(errors):
            raise ValueError("DIAGNOSTIC_HEALTH_CLEAN_FINALIZATION_INVALID")
    elif schema == MANIFEST_SCHEMA:
        required = {"schema", "schema_version", "diagnostic_contract", "configuration_sha256",
                    "entries", "expected_dynamic_keys", "applicable_dynamic_keys",
                    "not_applicable_dynamic_keys", "ordinary_guard_event_stream_count"}
        _require_exact_keys(record, required, set())
        if record["ordinary_guard_event_stream_count"] != 0:
            raise ValueError("ORDINARY_GUARD_EVENT_STREAM_PROHIBITED")
        if not isinstance(record["entries"], list):
            raise ValueError("DIAGNOSTIC_MANIFEST_ENTRIES_INVALID")
        _sha256(record["configuration_sha256"], "manifest.configuration_sha256")
        for name in ("expected_dynamic_keys", "applicable_dynamic_keys", "not_applicable_dynamic_keys"):
            _integer(record[name], "manifest." + name)
        if record["expected_dynamic_keys"] != record["applicable_dynamic_keys"] + record["not_applicable_dynamic_keys"]:
            raise ValueError("DIAGNOSTIC_MANIFEST_APPLICABILITY_COUNT_INVALID")
        identities = [entry.get("key_id") if isinstance(entry, Mapping) else None for entry in record["entries"]]
        if len(identities) != len(set(identities)):
            raise ValueError("DUPLICATE_DIAGNOSTIC_MANIFEST_IDENTITY")
        if len(identities) != record["expected_dynamic_keys"]:
            raise ValueError("DIAGNOSTIC_MANIFEST_COUNT_LIST_MISMATCH")
        applicable = 0
        for index, entry in enumerate(record["entries"]):
            if not isinstance(entry, Mapping): raise ValueError("DIAGNOSTIC_MANIFEST_ENTRY_OBJECT_REQUIRED")
            common = {"key_id", "applicability", "scientific_terminal_status", "scientific_stop_token", "expected_record_type",
                      "actual_record_path", "record_sha256", "schema", "validation",
                      "diagnostic_terminal_status"}
            _require_exact_keys(entry, common, set())
            _text(entry["key_id"], f"entries[{index}].key_id")
            _enum(entry["applicability"], APPLICABILITY_STATES, f"entries[{index}].applicability")
            _enum(entry["diagnostic_terminal_status"], TERMINAL_DISPOSITIONS, f"entries[{index}].diagnostic_terminal_status")
            if entry["scientific_terminal_status"] is not None:
                _enum(entry["scientific_terminal_status"], ("COMPLETE", "STOPPED", "CAPPED",
                    "NUMERICALLY_UNRESOLVED", "FAILED", "INTERRUPTED"),
                    f"entries[{index}].scientific_terminal_status")
            if entry["scientific_stop_token"] is not None:
                _text(entry["scientific_stop_token"], f"entries[{index}].scientific_stop_token")
            if entry["applicability"] == NOT_APPLICABLE:
                if any(entry[name] is not None for name in ("expected_record_type", "actual_record_path", "record_sha256", "schema")):
                    raise ValueError("DIAGNOSTIC_NOT_APPLICABLE_PAYLOAD_INVALID")
                if entry["diagnostic_terminal_status"] not in (NOT_APPLICABLE, ADMIN_FAILURE):
                    raise ValueError("DIAGNOSTIC_NOT_APPLICABLE_DISPOSITION_INVALID")
            else:
                applicable += 1
                if entry["scientific_terminal_status"] == "COMPLETE": expected_type, expected_schema, disposition = "MULTIPLIER_MARGIN_SUMMARY", SUMMARY_SCHEMA, "MULTIPLIER_MARGIN_SUMMARY_WRITTEN"
                elif (entry["scientific_terminal_status"] == "STOPPED" and
                      isinstance(entry["scientific_stop_token"], str) and
                      (entry["scientific_stop_token"] == "STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUTWARD_OR_OUT_OF_RANGE_NO_CLIPPING" or
                       entry["scientific_stop_token"] == "STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUTWARD_CROSSING_NO_CLIPPING" or
                       entry["scientific_stop_token"].startswith("STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUTWARD_CROSSING_NO_CLIPPING:"))):
                    expected_type, expected_schema, disposition = "MULTIPLIER_STOP_EVENT", STOP_SCHEMA, "MULTIPLIER_STOP_EVENT_WRITTEN"
                else: expected_type, expected_schema, disposition = None, None, (
                    ADMIN_FAILURE if entry["scientific_terminal_status"] is None
                    else "APPLICABLE_OTHER_TERMINAL_EVIDENCE_INCOMPLETE")
                if (entry["expected_record_type"], entry["schema"], entry["diagnostic_terminal_status"]) != (expected_type, expected_schema, disposition):
                    raise ValueError("DIAGNOSTIC_MANIFEST_RECORD_COUPLING_INVALID")
                if expected_type is not None:
                    _text(entry["actual_record_path"], f"entries[{index}].actual_record_path")
                    if not Path(entry["actual_record_path"]).is_absolute():
                        raise ValueError("DIAGNOSTIC_MANIFEST_RECORD_PATH_INVALID")
                    _sha256(entry["record_sha256"], f"entries[{index}].record_sha256")
                elif any(entry[name] is not None for name in ("actual_record_path", "record_sha256", "schema")):
                    raise ValueError("DIAGNOSTIC_MANIFEST_UNEXPECTED_RECORD_PAYLOAD")
            if entry["validation"] not in ("PASS", "NOT_APPLICABLE", "FAILED"):
                raise ValueError("DIAGNOSTIC_MANIFEST_VALIDATION_INVALID")
            expected_validation = ("NOT_APPLICABLE" if entry["diagnostic_terminal_status"] == NOT_APPLICABLE
                else "PASS" if entry["expected_record_type"] is not None else "FAILED")
            if entry["validation"] != expected_validation:
                raise ValueError("DIAGNOSTIC_MANIFEST_VALIDATION_COUPLING_INVALID")
        if applicable != record["applicable_dynamic_keys"]:
            raise ValueError("DIAGNOSTIC_MANIFEST_APPLICABILITY_LIST_MISMATCH")
        if identities != sorted(identities):
            raise ValueError("DIAGNOSTIC_MANIFEST_ENTRY_ORDER_INVALID")
    else:
        raise ValueError("DIAGNOSTIC_RUN_SCHEMA_IDENTITY_INVALID")
    if record.get("schema_version") != 2 or record.get("diagnostic_contract") != CONTRACT_ID:
        raise ValueError("DIAGNOSTIC_RUN_SCHEMA_VERSION_INVALID")


def validate_run_reconciliation(health: Mapping[str, object],
                                manifest: Mapping[str, object]) -> None:
    validate_run_object(manifest); validate_run_object(health)
    if health["manifest_sha256"] != digest(manifest):
        raise ValueError("DIAGNOSTIC_HEALTH_MANIFEST_HASH_MISMATCH")
    for name in ("expected_dynamic_keys", "applicable_dynamic_keys", "not_applicable_dynamic_keys"):
        if health[name] != manifest[name]:
            raise ValueError("DIAGNOSTIC_HEALTH_MANIFEST_COUNT_MISMATCH:" + name)
    entries = manifest["entries"]
    counts = {
        "completed_summaries_written": sum(e["expected_record_type"] == "MULTIPLIER_MARGIN_SUMMARY" for e in entries),
        "stop_events_written": sum(e["expected_record_type"] == "MULTIPLIER_STOP_EVENT" for e in entries),
        "not_applicable_dispositions": sum(e["diagnostic_terminal_status"] == NOT_APPLICABLE for e in entries),
    }
    for name, count in counts.items():
        if health[name] != count:
            raise ValueError("DIAGNOSTIC_HEALTH_MANIFEST_RECORD_COUNT_MISMATCH:" + name)


def seal_record(record: Mapping[str, object]) -> dict:
    sealed = dict(record)
    sealed["record_id"] = record_identity(sealed)
    validate_record(sealed)
    sealed["integrity_sha256"] = digest(sealed)
    validate_record(sealed)
    return sealed


def atomic_write_record(path: Path, record: Mapping[str, object]) -> str:
    validate_record(record)
    if path.exists():
        raise FileExistsError("DIAGNOSTIC_COMPLETED_RECORD_OVERWRITE_PROHIBITED")
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = canonical_bytes(record)
    fd, temporary = tempfile.mkstemp(prefix=".obs-001-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
        if path.read_bytes() != encoded:
            raise OSError("DIAGNOSTIC_POST_WRITE_VALIDATION_FAILED")
        validate_record(json.loads(path.read_text(encoding="ascii")))
        return hashlib.sha256(encoded).hexdigest()
    except BaseException:
        try: os.unlink(temporary)
        except FileNotFoundError: pass
        raise


def atomic_write_run_object(path: Path, record: Mapping[str, object]) -> str:
    validate_run_object(record)
    if path.exists(): raise FileExistsError("DIAGNOSTIC_RUN_OBJECT_OVERWRITE_PROHIBITED")
    path.parent.mkdir(parents=True, exist_ok=True); encoded=canonical_bytes(record)
    fd,temporary=tempfile.mkstemp(prefix=".obs-001-",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as handle:
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary,path)
        parsed=json.loads(path.read_text(encoding="ascii")); validate_run_object(parsed)
        if path.read_bytes()!=encoded: raise OSError("DIAGNOSTIC_RUN_POST_WRITE_VALIDATION_FAILED")
        return hashlib.sha256(encoded).hexdigest()
    except BaseException:
        try: os.unlink(temporary)
        except FileNotFoundError: pass
        raise


class MarginAccumulator:
    """One bounded minimum-margin sample and a count; never an event stream."""
    def __init__(self) -> None:
        self.guard_evaluations = 0
        self._minimum: dict | None = None
        self._rank: tuple | None = None

    def observe(self, sample: Mapping[str, object]) -> None:
        self.guard_evaluations += 1
        required = set(TIE_BREAK_ORDER) | {"lower_distance", "upper_distance", "state", "sector",
                                           "beta", "x_i", "M_i", "H_i0", "H_i", "tolerances",
                                           "contact_state", "contact_derivative", "finite_category"}
        if set(sample) != required:
            raise ValueError("MARGIN_SAMPLE_SCHEMA_INVALID")
        lower = validate_exact_float(sample["lower_distance"], "sample.lower_distance")
        upper = validate_exact_float(sample["upper_distance"], "sample.upper_distance")
        distance = min(lower, upper)
        relevant = "LOWER_BOUND" if lower <= upper else "UPPER_BOUND"
        rank_values = tuple(validate_exact_float(sample[name], "sample." + name)
                            if name == "simulation_time" else sample[name]
                            for name in TIE_BREAK_ORDER)
        rank = (distance,) + rank_values
        if self._rank is None or rank < self._rank:
            self._rank = rank
            self._minimum = {**dict(sample), "global_minimum_distance": exact_float(distance),
                             "relevant_bound": relevant}

    def summary(self) -> tuple[int, dict]:
        if self._minimum is None:
            raise ValueError("MISSING_MARGIN_OBSERVATION")
        return self.guard_evaluations, dict(self._minimum)


class KeyDiagnostics:
    """Per-key bounded observer. All inputs are copied, and all callback returns are ``None``."""
    def __init__(self, common_identity: Mapping[str, object]) -> None:
        missing = COMMON_IDENTITY_REQUIRED - set(common_identity)
        if missing:
            raise ValueError("DIAGNOSTIC_COMMON_IDENTITY_MISSING:" + ",".join(sorted(missing)))
        self.common = dict(common_identity)
        self.margin = MarginAccumulator()
        self.last_accepted: dict | None = None
        self.last_candidate: dict | None = None

    def accepted(self, *, time: float, step_index: int, state: Sequence[float],
                 state_names: Sequence[str]) -> None:
        self.last_accepted = {"simulation_time": exact_float(time),
                              "accepted_step_index": step_index,
                              "state": exact_vector(tuple(state), tuple(state_names))}

    def candidate(self, *, time: float, candidate_step_index: int, state: Sequence[float],
                  state_names: Sequence[str]) -> None:
        self.last_candidate = {"simulation_time": exact_float(time),
            "candidate_step_index": candidate_step_index,
            "state": exact_vector(tuple(state), tuple(state_names))}

    def observe_margin(self, sample: Mapping[str, object]) -> None:
        self.margin.observe(dict(sample))

    def completed_record(self) -> dict:
        count, minimum = self.margin.summary()
        return seal_record({**self.common, "schema": SUMMARY_SCHEMA, "schema_version": 1,
            "diagnostic_contract": CONTRACT_ID, "record_type": "MULTIPLIER_MARGIN_SUMMARY",
            "record_id": "PENDING", "scientific_terminal_status": "COMPLETE",
            "guard_evaluations": count, "minimum": minimum,
            "tie_break_order": list(TIE_BREAK_ORDER)})

    def stopped_record(self, *, scientific: Mapping[str, object], trigger: Mapping[str, object],
                       root: Mapping[str, object] | None, sectors: Sequence[Mapping[str, object]],
                       guard_semantics: Mapping[str, object], margins: Mapping[str, object],
                       correlation: Mapping[str, object]) -> dict:
        if self.last_accepted is None or self.last_candidate is None:
            raise ValueError("DIAGNOSTIC_STOP_TIMELINE_INCOMPLETE")
        timeline = {"prior_accepted_time": self.last_accepted["simulation_time"],
            "prior_accepted_step_index": self.last_accepted["accepted_step_index"],
            "candidate_time": self.last_candidate["simulation_time"],
            "candidate_step_index": self.last_candidate["candidate_step_index"],
            "event_root_present": root is not None,
            "event_root_time": None if root is None else root["simulation_time"],
            "evaluation_stage": "LOCATED_EVENT_ROOT" if root else "RAW_RANGE_GUARD"}
        states = {"prior_accepted": self.last_accepted["state"],
                  "candidate": self.last_candidate["state"],
                  "event_root": None if root is None else root["state"]}
        return seal_record({**self.common, "schema": STOP_SCHEMA, "schema_version": 1,
            "diagnostic_contract": CONTRACT_ID, "record_type": "MULTIPLIER_STOP_EVENT",
            "record_id": "PENDING", "scientific": dict(scientific), "trigger": dict(trigger),
            "timeline": timeline, "states": states, "sectors": [dict(x) for x in sectors],
            "guard_semantics": dict(guard_semantics), "margins": dict(margins),
            "correlation": dict(correlation)})


class ExecutorKeyObserver:
    """Production callback adapter retaining only terminal state and one minimum."""
    def __init__(self, common_identity: Mapping[str, object], state_names: Sequence[str],
                 base_h: Sequence[float]) -> None:
        self.key = KeyDiagnostics(common_identity); self.state_names = tuple(state_names)
        self.base_h = tuple(base_h); self.last_candidate: dict | None = None
        self.last_guard: dict | None = None
        self.root: dict | None = None; self.trigger_events: list[dict] = []
        self.failure: tuple[str, str] | None = None

    def __call__(self, event: str, payload: Mapping[str, object]) -> None:
        try:
            if event == "CANDIDATE_STATE":
                self.last_candidate = dict(payload)
                self.key.candidate(time=float(payload["tau"]),
                    candidate_step_index=int(payload["candidate_step_index"]),
                    state=payload["state"], state_names=self.state_names)
            elif event == "RAW_MULTIPLIER_GUARD" and self.last_candidate is not None:
                self.last_guard = dict(payload)
                for sector, (x_i, multiplier, h0) in enumerate(zip(
                        payload["x"], payload["multipliers"], payload["H_i0"])):
                    self.key.observe_margin({"accepted_step_index": 0,
                        "candidate_step_index": int(self.last_candidate["candidate_step_index"]),
                        "simulation_time": exact_float(float(self.last_candidate["tau"])), "profile_order": 0,
                        "sector_index": sector, "event_sequence": self.key.margin.guard_evaluations,
                        "lower_distance": exact_float(float(multiplier)-.25),
                        "upper_distance": exact_float(4.-float(multiplier)),
                        "state": exact_vector(self.last_candidate["state"], self.state_names),
                        "sector": sector, "beta": exact_float(payload["beta"]),
                        "x_i": exact_float(x_i), "M_i": exact_float(multiplier),
                        "H_i0": exact_float(h0), "H_i": exact_float(float(h0)*float(multiplier)),
                        "tolerances": {"boundary": exact_float(1e-12),
                            "derivative": exact_float(1e-14), "event_root": exact_float(1e-10)},
                        "contact_state": "EXACT_CONTACT" if multiplier in (.25,4.) else "ORDINARY",
                        "contact_derivative": None,
                        "finite_category": exact_float(multiplier)["finite_category"]})
            elif event == "ACCEPTED_STEPS":
                self.key.accepted(time=float(payload["prior_time"]),
                    step_index=int(payload["prior_step_index"]), state=payload["prior_state"],
                    state_names=self.state_names)
            elif event == "LOCATED_EVENT_ROOT":
                self.root = {"simulation_time": exact_float(payload["tau"]),
                    "state": exact_vector(payload["state"], self.state_names)}
            elif event == "STOPPED_RESULT_CONSTRUCTION":
                self.trigger_events = [dict(x) for x in payload["all_triggering_events"]]
        except BaseException as exc:
            self.failure = ("SERIALIZATION_FAILURE", type(exc).__name__ + ":" + str(exc))

    def terminal_record(self, scientific_record: Mapping[str, object]) -> dict:
        if self.failure: raise ValueError(self.failure[1])
        if scientific_record.get("status") == "COMPLETE": return self.key.completed_record()
        if self.key.last_accepted is None and self.key.last_candidate is not None:
            self.key.accepted(time=float(self.last_candidate["tau"]), step_index=0,
                state=self.last_candidate["state"], state_names=self.state_names)
        triggers=self.trigger_events or [{"sector_index":0,"bound":"UNKNOWN","tau":0.}]
        if self.last_guard is None:
            raise ValueError("DIAGNOSTIC_STOP_GUARD_STATE_MISSING")
        sectors=[]
        for item in triggers:
            sector=int(item["sector_index"])
            beta=float(self.last_guard["beta"])
            x_value=float(self.last_guard["x"][sector])
            if self.root is not None and f"x_{sector}" in self.state_names:
                x_index=self.state_names.index(f"x_{sector}")
                x_value=struct.unpack(">d",bytes.fromhex(self.root["state"]["elements"][x_index]["ieee754_hex"]))[0]
            multiplier=math.exp(beta*x_value); h0=float(self.base_h[sector])
            sectors.append({"sector":sector,
                "beta":exact_float(beta),"x_i":exact_float(x_value),
                "beta_x_i":exact_float(beta*x_value), "M_i":exact_float(multiplier),
                "H_i0":exact_float(h0), "H_i":exact_float(h0*multiplier),
                "preceding_valid":None, "candidate":None,
                "event_root":None if self.root is None else {"x_i":exact_float(x_value),"M_i":exact_float(multiplier)},
                "lower_bound":exact_float(.25),
                "upper_bound":exact_float(4.)})
        stop=str(scientific_record.get("stop_disposition"))
        primary_multiplier=struct.unpack(">d",bytes.fromhex(sectors[0]["M_i"]["ieee754_hex"]))[0]
        lower_margin=primary_multiplier-.25
        upper_margin=4.-primary_multiplier
        selected_margin=(lower_margin if triggers[0].get("bound") == "LOWER_BOUND" else upper_margin)
        finite_exceedance=math.isfinite(selected_margin) and selected_margin < 0.0
        bound=.25 if triggers[0].get("bound") == "LOWER_BOUND" else 4.
        return self.key.stopped_record(scientific={"status":scientific_record.get("status"),
            "stop_token":stop,"finite_category":"NONFINITE" if "NONFINITE" in stop else "FINITE",
            "contact_category":"LOCATED_EVENT" if self.root else "RAW_GUARD",
            "exited_bound":triggers[0].get("bound"),"stop_direction":"OUTWARD"},
            trigger={"sector_count":len(self.base_h),"triggering_sectors":sorted({int(x["sector_index"]) for x in triggers}),
                "primary_sector":min(int(x["sector_index"]) for x in triggers),"parameter_bindings":{}},
            root=self.root,sectors=sectors,guard_semantics={"boundary_tolerance":exact_float(1e-12),
                "derivative_tolerance":exact_float(1e-14),"located_root_tolerance":exact_float(1e-10),
                "guard_decision":"STOP","no_clipping":True},
            margins={"lower":exact_float(lower_margin), "upper":exact_float(upper_margin),
                "minimum":exact_float(min(lower_margin, upper_margin)),
                "absolute_exceedance":exact_float(-selected_margin) if finite_exceedance else None,
                "relative_exceedance":exact_float(-selected_margin/bound) if finite_exceedance else None,
                "normalized_interval_exceedance":exact_float(-selected_margin/3.75) if finite_exceedance else None},
            correlation={"guard":digest({"key":self.key.common["key_id"],"kind":"guard"}),
                "contact":digest({"key":self.key.common["key_id"],"kind":"contact"}),
                "event_root":None if self.root is None else digest(self.root),
                "stopped_result":digest({"key":self.key.common["key_id"],"kind":"stopped"}),
                "final_record":digest({"key":self.key.common["key_id"],"kind":"final"})})


class DiagnosticRun:
    """Run-level cardinality, health, and manifest administration."""
    def __init__(self, config: DiagnosticConfig,
                 expected_keys: Sequence[str] | Mapping[str, str]) -> None:
        self.config = config
        if isinstance(expected_keys, Mapping):
            self.applicability = dict(expected_keys)
        else:
            self.applicability = {key: APPLICABLE for key in expected_keys}
        self.expected = tuple(self.applicability)
        if len(set(self.expected)) != len(self.expected):
            raise ValueError("DUPLICATE_EXPECTED_DIAGNOSTIC_KEY")
        for key_id, applicability in self.applicability.items():
            _text(key_id, "expected_key_id")
            _enum(applicability, APPLICABILITY_STATES, "applicability")
        self.entries: dict[str, dict] = {}
        self.failures: list[dict] = []

    def register(self, key_id: str, scientific_status: str, record: Mapping[str, object]) -> None:
        if key_id in self.entries:
            raise ValueError("DUPLICATE_DIAGNOSTIC_TERMINAL_IDENTITY")
        if self.applicability.get(key_id) != APPLICABLE:
            raise ValueError("DIAGNOSTIC_MULTIPLIER_RECORD_NOT_APPLICABLE")
        if scientific_status == "COMPLETE":
            expected_type = "MULTIPLIER_MARGIN_SUMMARY"
            terminal = "MULTIPLIER_MARGIN_SUMMARY_WRITTEN"
        elif scientific_status == "STOPPED":
            expected_type = "MULTIPLIER_STOP_EVENT"
            terminal = "MULTIPLIER_STOP_EVENT_WRITTEN"
        else:
            raise ValueError("DIAGNOSTIC_APPLICABLE_TERMINAL_STATUS_REQUIRES_DISTINCT_DISPOSITION")
        if record.get("record_type") != expected_type or record.get("key_id") != key_id:
            raise ValueError("DIAGNOSTIC_CARDINALITY_OR_BINDING_INVALID")
        if not self.config.enabled:
            raise ValueError("DISABLED_DIAGNOSTICS_CANNOT_REGISTER")
        assert self.config.sidecar_root is not None
        path = self.config.sidecar_root / "records" / f"{key_id}.{expected_type.lower()}.json"
        checksum = atomic_write_record(path, record)
        self.entries[key_id] = {"applicability": APPLICABLE,
            "scientific_terminal_status": scientific_status,
            "scientific_stop_token": (record["scientific"]["stop_token"]
                                      if scientific_status == "STOPPED" else None),
            "expected_record_type": expected_type, "actual_record_path": str(path),
            "record_sha256": checksum, "schema": record["schema"], "validation": "PASS",
            "diagnostic_terminal_status": terminal}

    def register_not_applicable(self, key_id: str, scientific_status: str,
                                scientific_stop_token: object = None) -> None:
        if key_id in self.entries:
            raise ValueError("DUPLICATE_DIAGNOSTIC_TERMINAL_IDENTITY")
        if self.applicability.get(key_id) != NOT_APPLICABLE:
            raise ValueError("DIAGNOSTIC_NOT_APPLICABLE_BINDING_INVALID")
        self.entries[key_id] = {"applicability": NOT_APPLICABLE,
            "scientific_terminal_status": scientific_status,
            "scientific_stop_token": scientific_stop_token, "expected_record_type": None,
            "actual_record_path": None, "record_sha256": None, "schema": None,
            "validation": "NOT_APPLICABLE", "diagnostic_terminal_status": NOT_APPLICABLE}

    def register_other_applicable(self, key_id: str, scientific_status: str,
                                  scientific_stop_token: object = None) -> None:
        if key_id in self.entries:
            raise ValueError("DUPLICATE_DIAGNOSTIC_TERMINAL_IDENTITY")
        if self.applicability.get(key_id) != APPLICABLE or scientific_status == "COMPLETE":
            raise ValueError("DIAGNOSTIC_OTHER_APPLICABLE_BINDING_INVALID")
        self.entries[key_id] = {"applicability": APPLICABLE,
            "scientific_terminal_status": scientific_status,
            "scientific_stop_token": scientific_stop_token, "expected_record_type": None,
            "actual_record_path": None, "record_sha256": None, "schema": None,
            "validation": "FAILED",
            "diagnostic_terminal_status": "APPLICABLE_OTHER_TERMINAL_EVIDENCE_INCOMPLETE"}
        self.fail(key_id, "MISSING_TERMINAL_RECORD", "APPLICABLE_OTHER_TERMINAL_STATE:" + scientific_status)

    def fail(self, key_id: str, reason: str, detail: str) -> None:
        if reason not in ADMIN_REASONS:
            raise ValueError("UNKNOWN_DIAGNOSTIC_ADMINISTRATIVE_REASON")
        self.failures.append({"namespace": ADMIN_FAILURE, "key_id": key_id,
                              "reason": reason, "detail": detail})
        if key_id in self.applicability and key_id not in self.entries:
            self.entries[key_id] = {"applicability": self.applicability[key_id],
                "scientific_terminal_status": None, "scientific_stop_token": None,
                "expected_record_type": None,
                "actual_record_path": None, "record_sha256": None, "schema": None,
                "validation": "FAILED", "diagnostic_terminal_status": ADMIN_FAILURE}

    def finalize_objects(self) -> tuple[dict, dict]:
        verified_record_keys: set[str] = set()
        corrupt_record_keys: set[str] = set()
        unexpected_record_count = 0
        if self.config.enabled and self.config.sidecar_root is not None:
            records_root = self.config.sidecar_root / "records"
            expected_paths = set()
            for key_id, entry in self.entries.items():
                path_text = entry.get("actual_record_path")
                if path_text is None:
                    continue
                path = Path(path_text)
                expected_paths.add(path.resolve())
                try:
                    raw = path.read_bytes()
                    retained = json.loads(raw)
                    if hashlib.sha256(raw).hexdigest() != entry.get("record_sha256"):
                        raise ValueError("HASH_MISMATCH")
                    validate_record(retained)
                    if retained.get("key_id") != key_id or retained.get("record_type") != entry.get("expected_record_type"):
                        raise ValueError("IDENTITY_MISMATCH")
                    verified_record_keys.add(key_id)
                except (OSError, ValueError, TypeError, json.JSONDecodeError):
                    corrupt_record_keys.add(key_id)
                    self.failures.append({"namespace": ADMIN_FAILURE, "key_id": key_id,
                        "reason": "HEALTH_FINALIZATION_FAILURE", "detail": "DIAGNOSTIC_RECORD_FILE_OR_HASH_MISMATCH"})
            actual_paths = ({path.resolve() for path in records_root.glob("*.json")}
                            if records_root.is_dir() else set())
            for path in sorted(actual_paths - expected_paths):
                unexpected_record_count += 1
                self.failures.append({"namespace": ADMIN_FAILURE, "key_id": path.name,
                    "reason": "MANIFEST_RECONCILIATION_FAILURE", "detail": "UNMANIFESTED_DIAGNOSTIC_RECORD"})
        missing = sorted(set(self.expected) - set(self.entries))
        applicable_keys = {key for key, value in self.applicability.items() if value == APPLICABLE}
        not_applicable_keys = set(self.expected) - applicable_keys
        manifest_entries = []
        for key in sorted(self.expected):
            entry = self.entries.get(key)
            if entry is None:
                entry = {"applicability": self.applicability[key],
                    "scientific_terminal_status": None, "scientific_stop_token": None,
                    "expected_record_type": None,
                    "actual_record_path": None, "record_sha256": None, "schema": None,
                    "validation": "FAILED", "diagnostic_terminal_status": ADMIN_FAILURE}
            manifest_entries.append(dict(key_id=key, **entry))
        clean = not missing and not self.failures and all(
            entry["diagnostic_terminal_status"] not in (ADMIN_FAILURE,
                "APPLICABLE_OTHER_TERMINAL_EVIDENCE_INCOMPLETE") for entry in self.entries.values())
        manifest = {"schema": MANIFEST_SCHEMA, "schema_version": 2,
            "diagnostic_contract": CONTRACT_ID, "configuration_sha256": self.config.configuration_sha256,
            "entries": manifest_entries, "expected_dynamic_keys": len(self.expected),
            "applicable_dynamic_keys": len(applicable_keys),
            "not_applicable_dynamic_keys": len(not_applicable_keys),
            "ordinary_guard_event_stream_count": 0}
        manifest_hash = digest(manifest)
        complete = sum(e.get("scientific_terminal_status") == "COMPLETE" and e["applicability"] == APPLICABLE for e in self.entries.values())
        stopped = sum(e.get("expected_record_type") == "MULTIPLIER_STOP_EVENT" and
                      e["applicability"] == APPLICABLE for e in self.entries.values())
        other = len(applicable_keys) - complete - stopped
        health = {"schema": HEALTH_SCHEMA, "schema_version": 2, "diagnostic_contract": CONTRACT_ID,
            "expected_dynamic_keys": len(self.expected), "applicable_dynamic_keys": len(applicable_keys),
            "not_applicable_dynamic_keys": len(not_applicable_keys), "started_dynamic_keys": len(self.entries),
            "applicable_complete_keys": complete, "applicable_multiplier_stopped_keys": stopped,
            "other_applicable_terminal_states": other,
            "completed_summaries_expected": complete,
            "completed_summaries_written": sum(k in verified_record_keys and e.get("expected_record_type") == "MULTIPLIER_MARGIN_SUMMARY" for k,e in self.entries.items()),
            "stop_events_expected": stopped,
            "stop_events_written": sum(k in verified_record_keys and e.get("expected_record_type") == "MULTIPLIER_STOP_EVENT" for k,e in self.entries.items()),
            "not_applicable_dispositions": sum(e.get("diagnostic_terminal_status") == NOT_APPLICABLE for e in self.entries.values()),
            "terminal_diagnostic_dispositions": len(self.entries),
            "duplicate_identities": 0, "missing_identities": missing,
            "missing_applicable_records": sorted((set(missing) | corrupt_record_keys) & applicable_keys),
            "unexpected_records": unexpected_record_count,
            "serialization_failures": sum(x["reason"] == "SERIALIZATION_FAILURE" for x in self.failures),
            "schema_failures": sum(x["reason"] == "SCHEMA_FAILURE" for x in self.failures),
            "write_failures": sum(x["reason"] == "WRITE_FAILURE" for x in self.failures),
            "atomic_rename_failures": sum(x["reason"] == "ATOMIC_WRITE_FAILURE" for x in self.failures),
            "finalization_failures": sum("FINALIZATION" in x["reason"] or "RECONCILIATION" in x["reason"] for x in self.failures),
            "unexpected_exceptions": 0, "diagnostic_mode": self.config.mode,
            "evidence_required": self.config.required, "clean_finalization": clean,
            "implementation_version": IMPLEMENTATION_VERSION,
            "configuration_sha256": self.config.configuration_sha256,
            "manifest_sha256": manifest_hash, "administrative_failures": list(self.failures)}
        validate_run_reconciliation(health, manifest)
        return health, manifest

    def finalize(self) -> tuple[dict, dict]:
        health,manifest=self.finalize_objects()
        if not self.config.enabled or self.config.sidecar_root is None: return health,manifest
        atomic_write_run_object(self.config.sidecar_root/"MULTIPLIER_DIAGNOSTIC_MANIFEST.json",manifest)
        atomic_write_run_object(self.config.sidecar_root/"MULTIPLIER_DIAGNOSTIC_HEALTH.json",health)
        return health,manifest
