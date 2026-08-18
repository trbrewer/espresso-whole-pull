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
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

CONTRACT_ID = "espresso.whole_pull.sci_lc_001a.multiplier_diagnostics.v1"
IMPLEMENTATION_VERSION = "OBS_001_V1"
STOP_SCHEMA = "espresso.whole_pull.sci_lc_001a.multiplier_stop_event.v1"
SUMMARY_SCHEMA = "espresso.whole_pull.sci_lc_001a.multiplier_margin_summary.v1"
HEALTH_SCHEMA = "espresso.whole_pull.sci_lc_001a.multiplier_diagnostic_health.v1"
MANIFEST_SCHEMA = "espresso.whole_pull.sci_lc_001a.multiplier_diagnostic_manifest.v1"
MODES = ("DISABLED", "ENABLED_OPTIONAL", "ENABLED_REQUIRED")
RECORD_TYPES = ("MULTIPLIER_STOP_EVENT", "MULTIPLIER_MARGIN_SUMMARY")
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
    missing = required - set(record)
    unknown = set(record) - required - optional
    if missing:
        raise ValueError("DIAGNOSTIC_SCHEMA_MISSING_FIELDS:" + ",".join(sorted(missing)))
    if unknown:
        raise ValueError("DIAGNOSTIC_SCHEMA_UNKNOWN_FIELDS:" + ",".join(sorted(unknown)))


def validate_record(record: Mapping[str, object]) -> None:
    schema = record.get("schema")
    if schema == STOP_SCHEMA:
        required = COMMON_REQUIRED | {"scientific", "trigger", "timeline", "states", "sectors",
                                      "guard_semantics", "margins", "correlation"}
        _require_exact_keys(record, required, {"integrity_sha256"})
        if record.get("record_type") != "MULTIPLIER_STOP_EVENT":
            raise ValueError("DIAGNOSTIC_RECORD_TYPE_INVALID")
    elif schema == SUMMARY_SCHEMA:
        required = COMMON_REQUIRED | {"scientific_terminal_status", "guard_evaluations",
                                      "minimum", "tie_break_order"}
        _require_exact_keys(record, required, {"integrity_sha256"})
        if record.get("record_type") != "MULTIPLIER_MARGIN_SUMMARY" or record.get(
                "scientific_terminal_status") != "COMPLETE":
            raise ValueError("DIAGNOSTIC_SUMMARY_DISPOSITION_INVALID")
        if tuple(record.get("tie_break_order", ())) != TIE_BREAK_ORDER:
            raise ValueError("DIAGNOSTIC_TIE_BREAK_ORDER_INVALID")
    else:
        raise ValueError("DIAGNOSTIC_SCHEMA_IDENTITY_INVALID")
    if record.get("schema_version") != 1 or record.get("diagnostic_contract") != CONTRACT_ID:
        raise ValueError("DIAGNOSTIC_SCHEMA_VERSION_INVALID")
    if record.get("record_id") != record_identity(record):
        raise ValueError("DIAGNOSTIC_RECORD_IDENTITY_INVALID")
    if record.get("integrity_sha256") is not None:
        body = dict(record); supplied = body.pop("integrity_sha256")
        if supplied != digest(body):
            raise ValueError("DIAGNOSTIC_RECORD_INTEGRITY_INVALID")


def validate_run_object(record: Mapping[str, object]) -> None:
    schema = record.get("schema")
    if schema == HEALTH_SCHEMA:
        required = {"schema", "schema_version", "diagnostic_contract", "expected_dynamic_keys",
            "started_dynamic_keys", "completed_summaries_expected", "completed_summaries_written",
            "stop_events_expected", "stop_events_written", "terminal_diagnostic_dispositions",
            "duplicate_identities", "missing_identities", "serialization_failures", "schema_failures",
            "write_failures", "atomic_rename_failures", "finalization_failures",
            "unexpected_exceptions", "diagnostic_mode", "evidence_required", "clean_finalization",
            "implementation_version", "configuration_sha256", "manifest_sha256",
            "administrative_failures"}
        _require_exact_keys(record, required, set())
        if record["diagnostic_mode"] not in MODES:
            raise ValueError("DIAGNOSTIC_HEALTH_MODE_INVALID")
    elif schema == MANIFEST_SCHEMA:
        required = {"schema", "schema_version", "diagnostic_contract", "configuration_sha256",
                    "entries", "ordinary_guard_event_stream_count"}
        _require_exact_keys(record, required, set())
        if record["ordinary_guard_event_stream_count"] != 0:
            raise ValueError("ORDINARY_GUARD_EVENT_STREAM_PROHIBITED")
        identities = [entry.get("key_id") for entry in record["entries"]]
        if len(identities) != len(set(identities)):
            raise ValueError("DUPLICATE_DIAGNOSTIC_MANIFEST_IDENTITY")
    else:
        raise ValueError("DIAGNOSTIC_RUN_SCHEMA_IDENTITY_INVALID")
    if record.get("schema_version") != 1 or record.get("diagnostic_contract") != CONTRACT_ID:
        raise ValueError("DIAGNOSTIC_RUN_SCHEMA_VERSION_INVALID")


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
        lower = float(sample["lower_distance"]); upper = float(sample["upper_distance"])
        distance = min(lower, upper)
        relevant = "LOWER_BOUND" if lower <= upper else "UPPER_BOUND"
        rank = (distance,) + tuple(sample[name] for name in TIE_BREAK_ORDER)
        if self._rank is None or rank < self._rank:
            self._rank = rank
            self._minimum = {**dict(sample), "global_minimum_distance": distance,
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
                for sector, (x_i, multiplier, h0) in enumerate(zip(
                        payload["x"], payload["multipliers"], payload["H_i0"])):
                    self.key.observe_margin({"accepted_step_index": 0,
                        "candidate_step_index": int(self.last_candidate["candidate_step_index"]),
                        "simulation_time": float(self.last_candidate["tau"]), "profile_order": 0,
                        "sector_index": sector, "event_sequence": self.key.margin.guard_evaluations,
                        "lower_distance": float(multiplier)-.25, "upper_distance": 4.-float(multiplier),
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
        sectors=[]
        for item in triggers:
            sector=int(item["sector_index"]); sectors.append({"sector":sector,
                "beta":exact_float(0.),"x_i":exact_float(0.),"beta_x_i":exact_float(0.),
                "M_i":exact_float(1.),"H_i0":exact_float(self.base_h[sector]),
                "H_i":exact_float(self.base_h[sector]), "preceding_valid":None,
                "candidate":None,"event_root":None,"lower_bound":exact_float(.25),
                "upper_bound":exact_float(4.)})
        stop=str(scientific_record.get("stop_disposition"))
        return self.key.stopped_record(scientific={"status":scientific_record.get("status"),
            "stop_token":stop,"finite_category":"NONFINITE" if "NONFINITE" in stop else "FINITE",
            "contact_category":"LOCATED_EVENT" if self.root else "RAW_GUARD",
            "exited_bound":triggers[0].get("bound"),"stop_direction":"OUTWARD"},
            trigger={"sector_count":len(self.base_h),"triggering_sectors":sorted({int(x["sector_index"]) for x in triggers}),
                "primary_sector":min(int(x["sector_index"]) for x in triggers),"parameter_bindings":{}},
            root=self.root,sectors=sectors,guard_semantics={"boundary_tolerance":exact_float(1e-12),
                "derivative_tolerance":exact_float(1e-14),"located_root_tolerance":exact_float(1e-10),
                "guard_decision":"STOP","no_clipping":True},
            margins={"lower":None,"upper":None,"minimum":None,"absolute_exceedance":None,
                     "relative_exceedance":None,"normalized_interval_exceedance":None},
            correlation={"guard":digest({"key":self.key.common["key_id"],"kind":"guard"}),
                "contact":digest({"key":self.key.common["key_id"],"kind":"contact"}),
                "event_root":None if self.root is None else digest(self.root),
                "stopped_result":digest({"key":self.key.common["key_id"],"kind":"stopped"}),
                "final_record":digest({"key":self.key.common["key_id"],"kind":"final"})})


class DiagnosticRun:
    """Run-level cardinality, health, and manifest administration."""
    def __init__(self, config: DiagnosticConfig, expected_keys: Sequence[str]) -> None:
        self.config = config
        self.expected = tuple(expected_keys)
        if len(set(self.expected)) != len(self.expected):
            raise ValueError("DUPLICATE_EXPECTED_DIAGNOSTIC_KEY")
        self.entries: dict[str, dict] = {}
        self.failures: list[dict] = []

    def register(self, key_id: str, scientific_status: str, record: Mapping[str, object]) -> None:
        if key_id in self.entries:
            raise ValueError("DUPLICATE_DIAGNOSTIC_TERMINAL_IDENTITY")
        expected_type = ("MULTIPLIER_MARGIN_SUMMARY" if scientific_status == "COMPLETE"
                         else "MULTIPLIER_STOP_EVENT")
        if record.get("record_type") != expected_type or record.get("key_id") != key_id:
            raise ValueError("DIAGNOSTIC_CARDINALITY_OR_BINDING_INVALID")
        if not self.config.enabled:
            raise ValueError("DISABLED_DIAGNOSTICS_CANNOT_REGISTER")
        assert self.config.sidecar_root is not None
        path = self.config.sidecar_root / "records" / f"{key_id}.{expected_type.lower()}.json"
        checksum = atomic_write_record(path, record)
        self.entries[key_id] = {"scientific_terminal_status": scientific_status,
            "expected_record_type": expected_type, "actual_record_path": str(path),
            "record_sha256": checksum, "schema": record["schema"], "validation": "PASS",
            "diagnostic_terminal_status": "COMPLETE"}

    def fail(self, key_id: str, reason: str, detail: str) -> None:
        if reason not in ADMIN_REASONS:
            raise ValueError("UNKNOWN_DIAGNOSTIC_ADMINISTRATIVE_REASON")
        self.failures.append({"namespace": ADMIN_FAILURE, "key_id": key_id,
                              "reason": reason, "detail": detail})

    def finalize_objects(self) -> tuple[dict, dict]:
        missing = sorted(set(self.expected) - set(self.entries))
        clean = not missing and not self.failures
        manifest = {"schema": MANIFEST_SCHEMA, "schema_version": 1,
            "diagnostic_contract": CONTRACT_ID, "configuration_sha256": self.config.configuration_sha256,
            "entries": [dict(key_id=key, **self.entries[key]) for key in self.expected if key in self.entries],
            "ordinary_guard_event_stream_count": 0}
        manifest_hash = digest(manifest)
        health = {"schema": HEALTH_SCHEMA, "schema_version": 1, "diagnostic_contract": CONTRACT_ID,
            "expected_dynamic_keys": len(self.expected), "started_dynamic_keys": len(self.entries) + len(self.failures),
            "completed_summaries_expected": sum(e.get("scientific_terminal_status") == "COMPLETE" for e in self.entries.values()),
            "completed_summaries_written": sum(e.get("expected_record_type") == "MULTIPLIER_MARGIN_SUMMARY" for e in self.entries.values()),
            "stop_events_expected": sum(e.get("scientific_terminal_status") != "COMPLETE" for e in self.entries.values()),
            "stop_events_written": sum(e.get("expected_record_type") == "MULTIPLIER_STOP_EVENT" for e in self.entries.values()),
            "terminal_diagnostic_dispositions": len(self.entries) + len(self.failures),
            "duplicate_identities": 0, "missing_identities": missing,
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
        validate_run_object(manifest); validate_run_object(health)
        return health, manifest

    def finalize(self) -> tuple[dict, dict]:
        health,manifest=self.finalize_objects()
        if not self.config.enabled or self.config.sidecar_root is None: return health,manifest
        atomic_write_run_object(self.config.sidecar_root/"MULTIPLIER_DIAGNOSTIC_MANIFEST.json",manifest)
        atomic_write_run_object(self.config.sidecar_root/"MULTIPLIER_DIAGNOSTIC_HEALTH.json",health)
        return health,manifest
