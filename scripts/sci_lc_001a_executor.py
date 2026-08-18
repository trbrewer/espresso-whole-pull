#!/usr/bin/env python3
"""Prospective SCI-LC-001A Stage-A executor.

The implementation is complete but execution remains authority-gated.  Plan,
validate, and summarize never call a solver.  Tests inject SYNTHETIC_TEST_ONLY;
synthetic records are permanently inadmissible as scientific evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import sci_lc_001a_protocol as protocol  # noqa: E402
import sci_lc_001a_obs_001_diagnostics as obs_001  # noqa: E402

ROOT = SCRIPT_DIR.parent
MATRIX_PATH = ROOT / "validation/cases/sci_lc_001a/SCI_LC_001A_PARAMETER_MATRIX.json"
PROTOCOL_PATH = ROOT / "validation/cases/sci_lc_001a/SCI_LC_001A_PROTOCOL.json"
AUTHORITY_SCHEMA = "ewp.sci_lc_001a.execution_authority.v1"
PILOT_AUTHORITY_SCHEMA = "ewp.sci_lc_001a.pilot_authority.v1"
PILOT_ALLOWLIST_SCHEMA = "ewp.sci_lc_001a.pilot_allowlist.v1"
RUN_SCHEMA = "ewp.sci_lc_001a.run_manifest.v1"
CASE_SCHEMA = "ewp.sci_lc_001a.case_profile_result.v1"
CLASSIFICATION_SCHEMA = "ewp.sci_lc_001a.classification_record.v1"
CLASSIFICATION_SUMMARY_SCHEMA = "ewp.sci_lc_001a.classification_summary.v1"
PLAN_SCHEMA = "ewp.sci_lc_001a.execution_plan.v1"
RESULT_STATUSES = ("NOT_STARTED", "RUNNING", "COMPLETE", "STOPPED", "CAPPED",
                   "NUMERICALLY_UNRESOLVED", "AUTHORITY_INVALID", "FAILED", "INTERRUPTED")
REAL_BACKEND = "REAL_STAGE_A"
SYNTHETIC_BACKEND = "SYNTHETIC_TEST_ONLY"
PILOT_EVIDENCE = "DIAGNOSTIC_TIMING_ONLY"
PUBLIC_API = ("CanonicalStore", "ResultStore", "build_plan", "validate_execution_authority",
              "execute_authorized_graph", "pilot_plan", "execute_authorized_pilot",
              "evaluate_gain_evidence", "evaluate_uncertainty_evidence",
              "classify_stage_a_evidence", "build_classification_record",
              "validate_classification_record", "write_classification_artifacts",
              "load_classification_records", "load_classification_summary",
              "export_stage_a_classifications", "main")
__all__ = PUBLIC_API


@dataclass(frozen=True)
class _ValidatedExecutionContext:
    authorization_id: str
    authorized_head: str
    authorized_tree: str
    matrix_hash: str
    protocol_hash: str
    executor_identity: str
    execution_mode: str
    backend: str
    evidence_kind: str
    output_root: str
    run_id: str


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def git_value(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True,
                          stdout=subprocess.PIPE).stdout.strip()


def path_has_symlink_parent(path: Path) -> bool:
    if not path.is_absolute():
        return True
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current = current / component
        if current.is_symlink():
            return True
    return False


def validate_external_output_root(path: Path) -> Path:
    if not path.is_absolute():
        raise ValueError("OUTPUT_ROOT_MUST_BE_ABSOLUTE")
    if path_has_symlink_parent(path):
        raise ValueError("OUTPUT_ROOT_SYMLINK_COMPONENT_REJECTED")
    resolved = path.resolve(strict=False)
    if resolved == ROOT or ROOT in resolved.parents:
        raise ValueError("OUTPUT_ROOT_INSIDE_REPOSITORY")
    cases = ROOT / "cases"
    if resolved == cases or cases in resolved.parents:
        raise ValueError("OUTPUT_ROOT_INSIDE_SCIENTIFIC_CASES")
    return resolved


@dataclass(frozen=True)
class CanonicalStore:
    rows: tuple[dict, ...]
    by_id: Mapping[str, dict]
    matrix_hash: str
    protocol_hash: str

    @classmethod
    def load(cls) -> "CanonicalStore":
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        spec = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
        rows = tuple(matrix["rows"])
        protocol.validate(list(rows), spec)
        expected = protocol.digest([{key: row[key] for key in protocol.FIELDS} for row in rows])
        if matrix["matrix_sha256"] != expected or expected != spec["matrix_summary"]["matrix_sha256"]:
            raise ValueError("MATRIX_SEMANTIC_HASH_MISMATCH")
        by_id = {row["case_id"]: row for row in rows}
        if len(by_id) != len(rows):
            raise ValueError("DUPLICATE_CANONICAL_CASE_ID")
        return cls(rows, by_id, expected, sha256_file(PROTOCOL_PATH))

    def row(self, case_id: str) -> dict:
        if case_id not in self.by_id:
            raise ValueError("UNKNOWN_CANONICAL_CASE_ID")
        row = self.by_id[case_id]
        protocol.validate_row_against_expected_fields(row, dict(self.by_id))
        return row


def build_plan(store: CanonicalStore) -> dict:
    graph = protocol.execution_graph(list(store.rows))
    keys = tuple(tuple(key) for key in graph["keys"])
    if len(keys) != 3666 or len(set(keys)) != 3666:
        raise ValueError("FROZEN_EXECUTION_GRAPH_MISMATCH")
    return {"schema": PLAN_SCHEMA, "matrix_sha256": store.matrix_hash,
            "protocol_sha256": store.protocol_hash, "matrix_rows": len(store.rows),
            "dynamic_rows": graph["dynamic_matrix_rows"], "static_rows": graph["static_matrix_rows"],
            "dynamic_profile_keys": graph["maximum_dynamic_trajectory_invocations"],
            "static_profile_keys": graph["maximum_static_solve_invocations"],
            "total_keys": len(keys), "keys": [list(key) for key in keys],
            "dynamic_initial_state_variant": protocol.DYNAMIC_INITIAL_STATE_VARIANT,
            "static_dynamic_initial_state_variant": protocol.STATIC_INITIAL_STATE_VARIANT,
            "initial_condition_scope": protocol.DYNAMIC_INITIAL_CONDITION_SCOPE,
            "cache_identity": "(case_id,numerical_profile)",
            "solver_calls": 0, "d4_keys": 0, "x1_keys": 0}


def validate_execution_authority(path: Path, output_root: Path, store: CanonicalStore,
                                 *, backend: str = REAL_BACKEND,
                                 allow_synthetic_fixture: bool = False) -> _ValidatedExecutionContext:
    output_root = validate_external_output_root(output_root)
    if not path.is_absolute() or not path.is_file():
        raise ValueError("EXECUTION_AUTHORITY_ABSOLUTE_FILE_REQUIRED")
    authority = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema", "authorization_id", "authorized_head", "authorized_tree",
                "matrix_semantic_sha256", "protocol_artifact_sha256", "allowed_execution_mode",
                "allowed_output_root", "backend", "executor_source_sha256", "evidence_kind"}
    if set(authority) != required or authority["schema"] != AUTHORITY_SCHEMA:
        raise ValueError("MALFORMED_EXECUTION_AUTHORITY")
    if backend == SYNTHETIC_BACKEND:
        if not allow_synthetic_fixture or authority["backend"] != SYNTHETIC_BACKEND:
            raise ValueError("SYNTHETIC_AUTHORITY_CANNOT_AUTHORIZE_REAL_BACKEND")
    elif authority["backend"] != REAL_BACKEND:
        raise ValueError("EXECUTION_BACKEND_NOT_AUTHORIZED")
    checks = {
        "authorized_head": git_value("rev-parse", "HEAD"),
        "authorized_tree": git_value("rev-parse", "HEAD^{tree}"),
        "matrix_semantic_sha256": store.matrix_hash,
        "protocol_artifact_sha256": store.protocol_hash,
        "allowed_execution_mode": "execute",
        "allowed_output_root": str(output_root),
        "executor_source_sha256": sha256_file(Path(__file__)),
        "evidence_kind": backend,
    }
    for key, expected in checks.items():
        if authority[key] != expected:
            raise ValueError("EXECUTION_AUTHORITY_MISMATCH:" + key)
    if git_value("status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("EXECUTION_WORKTREE_NOT_CLEAN")
    run_material = {"authorization_id": authority["authorization_id"],
                    "authorized_head": authority["authorized_head"],
                    "authorized_tree": authority["authorized_tree"],
                    "matrix_hash": store.matrix_hash, "protocol_hash": store.protocol_hash,
                    "executor_identity": authority["executor_source_sha256"],
                    "execution_mode": authority["allowed_execution_mode"], "backend": backend,
                    "evidence_kind": authority["evidence_kind"], "output_root": str(output_root)}
    return _ValidatedExecutionContext(**run_material,
        run_id=sha256_bytes(canonical_json(run_material).encode())[:24])


def _synthetic_context(store: CanonicalStore, output_root: Path,
                       authorization_id: str = "SYNTHETIC_FIXTURE_ONLY") -> _ValidatedExecutionContext:
    material = {"authorization_id": authorization_id, "authorized_head": "SYNTHETIC",
        "authorized_tree": "SYNTHETIC", "matrix_hash": store.matrix_hash,
        "protocol_hash": store.protocol_hash, "executor_identity": sha256_file(Path(__file__)),
        "execution_mode": "synthetic-test", "backend": SYNTHETIC_BACKEND,
        "evidence_kind": SYNTHETIC_BACKEND, "output_root": str(output_root)}
    return _ValidatedExecutionContext(**material,
        run_id=sha256_bytes(canonical_json(material).encode())[:24])


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    fd, temporary = tempfile.mkstemp(prefix=".tmp-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".tmp-", suffix=path.suffix, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


class ResultStore:
    def __init__(self, root: Path, canonical: CanonicalStore):
        self.root = validate_external_output_root(root)
        self.canonical = canonical

    def record_path(self, case_id: str, profile: str) -> Path:
        return self.root / "cases" / case_id / f"{profile}.json"

    def checksum_path(self, case_id: str, profile: str) -> Path:
        return self.root / "record-ledger" / case_id / f"{profile}.json"

    @property
    def manifest_path(self) -> Path:
        return self.root / "RUN_MANIFEST.json"

    @staticmethod
    def manifest_identity(manifest: dict) -> str:
        keys = ("schema", "run_id", "authorization_id", "git_head", "git_tree",
                "matrix_semantic_sha256", "protocol_sha256", "executor_source_sha256",
                "execution_mode", "backend", "evidence_kind", "output_root",
                "stage_a_architecture_id", "dynamic_initial_state_variant",
                "initial_condition_scope", "initial_condition_robustness", "bistability_status",
                "initial_condition_dependence_branch")
        if any(key not in manifest for key in keys):
            raise ValueError("RUN_MANIFEST_IDENTITY_FIELD_MISSING")
        return sha256_bytes(canonical_json({key: manifest[key] for key in keys}).encode())

    def begin_run(self, context: _ValidatedExecutionContext, task_count: int) -> dict:
        if not isinstance(context, _ValidatedExecutionContext):
            raise ValueError("VALIDATED_EXECUTION_CONTEXT_REQUIRED")
        expected = {"authorization_id": context.authorization_id,
                    "git_head": context.authorized_head, "git_tree": context.authorized_tree,
                    "matrix_semantic_sha256": context.matrix_hash,
                    "protocol_sha256": context.protocol_hash,
                    "executor_source_sha256": context.executor_identity,
                    "execution_mode": context.execution_mode, "output_root": str(self.root),
                    "backend": context.backend, "evidence_kind": context.evidence_kind,
                    "task_count": task_count, "run_id": context.run_id,
                    "stage_a_architecture_id": protocol.ARCHITECTURE_ID,
                    "dynamic_initial_state_variant": protocol.DYNAMIC_INITIAL_STATE_VARIANT,
                    "initial_condition_scope": protocol.DYNAMIC_INITIAL_CONDITION_SCOPE,
                    "initial_condition_robustness": protocol.NOT_ADJUDICATED_STAGE_A,
                    "bistability_status": protocol.NOT_ADJUDICATED_STAGE_A,
                    "initial_condition_dependence_branch": protocol.INITIAL_CONDITION_BRANCH_STATUS}
        if self.manifest_path.exists():
            manifest = self.load_manifest()
            if any(manifest.get(key) != value for key, value in expected.items()):
                raise ValueError("RESUME_MANIFEST_AUTHORITY_MISMATCH")
            return manifest
        manifest = {"schema": RUN_SCHEMA, **expected, "branch": git_value("branch", "--show-current"),
                    "started_at_utc": utc_now(), "ended_at_utc": None,
                    "status_counts": {status: 0 for status in RESULT_STATUSES},
                    "status": "RUNNING", "synthetic_evidence": context.backend == SYNTHETIC_BACKEND}
        manifest["run_manifest_identity_sha256"] = self.manifest_identity(manifest)
        atomic_write_json(self.manifest_path, manifest)
        return manifest

    def finish_run(self, manifest: dict, summary: dict, *, status: str | None = None,
                   unattempted_keys: int | None = None) -> None:
        final = {**manifest, "ended_at_utc": utc_now(), "status_counts": summary["statuses"],
                 "status": status or ("COMPLETE" if summary["records"] == manifest["task_count"] else "INTERRUPTED")}
        if unattempted_keys is not None:
            final["unattempted_key_count"] = unattempted_keys
        atomic_write_json(self.manifest_path, final)

    def write_record(self, manifest: dict, record: dict) -> None:
        if manifest.get("run_manifest_identity_sha256") != self.manifest_identity(manifest):
            raise ValueError("RUN_MANIFEST_IDENTITY_MISMATCH")
        if record.get("status") not in RESULT_STATUSES:
            raise ValueError("INVALID_RESULT_STATUS")
        row = self.canonical.row(record["case_id"])
        _validate_record_initial_condition_scope(row, record)
        if record["profile"] not in (protocol.STATIC_NUMERICAL_PROFILES if
                row["pressure_mode"] == "PRESCRIBED_STATIC" else protocol.DYNAMIC_NUMERICAL_PROFILES):
            raise ValueError("PROFILE_NOT_AUTHORIZED_FOR_ROW")
        bindings = {"run_id": manifest["run_id"], "authorization_id": manifest["authorization_id"],
            "authorized_head": manifest["git_head"], "authorized_tree": manifest["git_tree"],
            "matrix_semantic_sha256": manifest["matrix_semantic_sha256"],
            "protocol_sha256": manifest["protocol_sha256"],
            "executor_source_sha256": manifest["executor_source_sha256"],
            "execution_mode": manifest["execution_mode"], "backend": manifest["backend"],
            "evidence_kind": manifest["evidence_kind"],
            "run_manifest_identity_sha256": manifest["run_manifest_identity_sha256"]}
        conflicts = [key for key, value in bindings.items()
                     if key in record and record[key] != value]
        if conflicts:
            raise ValueError("RESULT_RECORD_AUTHORITY_CONFLICT:" + ",".join(sorted(conflicts)))
        record = {**record, **bindings}
        body = dict(record); body.pop("output_checksum", None)
        record = {**body, "output_checksum": sha256_bytes(canonical_json(body).encode())}
        atomic_write_json(self.record_path(record["case_id"], record["profile"]), record)
        atomic_write_json(self.checksum_path(record["case_id"], record["profile"]), {
            "run_manifest_identity_sha256": manifest["run_manifest_identity_sha256"],
            "case_id": record["case_id"], "profile": record["profile"], "output_checksum": record["output_checksum"]})

    def load_manifest(self) -> dict:
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema") != RUN_SCHEMA or manifest.get("run_manifest_identity_sha256") != self.manifest_identity(manifest):
            raise ValueError("RUN_MANIFEST_IDENTITY_MISMATCH")
        if (manifest["matrix_semantic_sha256"] != self.canonical.matrix_hash or
                manifest["protocol_sha256"] != self.canonical.protocol_hash or
                manifest["output_root"] != str(self.root)):
            raise ValueError("RUN_MANIFEST_AUTHORITY_MISMATCH")
        return manifest

    def read_bound_record(self, manifest: dict, case_id: str, profile: str) -> dict:
        if manifest.get("run_manifest_identity_sha256") != self.manifest_identity(manifest):
            raise ValueError("RUN_MANIFEST_IDENTITY_MISMATCH")
        record = json.loads(self.record_path(case_id, profile).read_text(encoding="utf-8"))
        body = dict(record); checksum = body.pop("output_checksum", None)
        if checksum != sha256_bytes(canonical_json(body).encode()):
            raise ValueError("RESULT_RECORD_CHECKSUM_MISMATCH")
        ledger = json.loads(self.checksum_path(case_id, profile).read_text(encoding="utf-8"))
        if ledger != {"run_manifest_identity_sha256": manifest["run_manifest_identity_sha256"],
                      "case_id": case_id, "profile": profile, "output_checksum": checksum}:
            raise ValueError("RESULT_RECORD_MANIFEST_CHECKSUM_MISMATCH")
        row = self.canonical.row(case_id)
        if (record.get("schema") != CASE_SCHEMA or record.get("case_id") != case_id or
                record.get("row_hash") != row["row_sha256"] or record.get("profile") != profile or
                record.get("status") not in RESULT_STATUSES):
            raise ValueError("RESULT_RECORD_CANONICAL_IDENTITY_MISMATCH")
        _validate_record_initial_condition_scope(row, record)
        bindings = {"run_id": "run_id", "authorization_id": "authorization_id",
            "authorized_head": "git_head", "authorized_tree": "git_tree",
            "matrix_semantic_sha256": "matrix_semantic_sha256", "protocol_sha256": "protocol_sha256",
            "executor_source_sha256": "executor_source_sha256", "execution_mode": "execution_mode",
            "backend": "backend", "evidence_kind": "evidence_kind",
            "run_manifest_identity_sha256": "run_manifest_identity_sha256"}
        for record_key, manifest_key in bindings.items():
            if record.get(record_key) != manifest.get(manifest_key):
                raise ValueError("RESULT_RECORD_MANIFEST_BINDING_MISMATCH:" + record_key)
        return record

    def reusable(self, manifest: dict, case_id: str, profile: str) -> bool:
        try:
            return self.read_bound_record(manifest, case_id, profile)["status"] in (
                "COMPLETE", "STOPPED", "CAPPED", "NUMERICALLY_UNRESOLVED")
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            return False


def _case_record(row: dict, profile: str, context: _ValidatedExecutionContext, status: str, metrics: dict,
                 *, synthetic: bool, started: str, nfev: int | None = 0,
                 stop: str | None = None, linear_status: str = "NOT_APPLICABLE",
                 execution_failure_class: str = "NUMERICAL_CASE_DISPOSITION",
                 rhs_evaluations_status: str | None = None) -> dict:
    rhs_status = rhs_evaluations_status or ("MEASURED" if nfev is not None else
        "NOT_AVAILABLE_DUE_TO_IMPLEMENTATION_EXCEPTION")
    scope = protocol.stage_a_initial_condition_scope(row)
    return {"schema": CASE_SCHEMA, "case_id": row["case_id"], "profile": profile,
            "row_hash": row["row_sha256"], "role": row["case_role"],
            "boundary_mode": row["pressure_mode"], "authorization_id": context.authorization_id,
            "authorized_head": context.authorized_head, "authorized_tree": context.authorized_tree,
            "status": status, "started_at_utc": started, "ended_at_utc": utc_now(),
            "solver_settings": profile, "rhs_evaluations": nfev,
            "rhs_evaluations_status": rhs_status,
            "execution_failure_class": execution_failure_class, "stop_disposition": stop,
            "linear_solve_status": linear_status, "residual_status": "PASS" if status == "COMPLETE" else status,
            "metric_primitives": metrics, "evidence_kind": context.evidence_kind,
            "stage_a_architecture_id": protocol.ARCHITECTURE_ID, **scope}


def _validate_record_initial_condition_scope(row: dict, record: Mapping[str, object]) -> None:
    expected = protocol.stage_a_initial_condition_scope(row)
    if record.get("stage_a_architecture_id") != protocol.ARCHITECTURE_ID:
        raise ValueError("RESULT_RECORD_STAGE_A_ARCHITECTURE_SCOPE_MISSING_OR_INVALID")
    if any(record.get(key) != value for key, value in expected.items()):
        raise ValueError("RESULT_RECORD_INITIAL_CONDITION_SCOPE_MISSING_OR_INVALID")


def assemble_static_system(row: dict) -> tuple[list[list[float]], list[float], dict]:
    p = protocol.resistance_primitives(row["sector_count"], row["heterogeneity_pattern"],
        row["heterogeneity_mode"], row["resistance_contrast"], row["axial_placement"],
        row["epsilon_floor"], row["initial_condition_variant"])
    n = row["sector_count"]; gu = [1 / x for x in p["R_u_i"]]; gd = [1 / x for x in p["R_d_i"]]
    ge = float(row["lateral_edge_conductance_G_edge"])
    a = [[0.0] * n for _ in range(n)]
    for i in range(n):
        a[i][i] = gu[i] + gd[i] + 2 * ge
        a[i][(i - 1) % n] -= ge; a[i][(i + 1) % n] -= ge
    return a, gu, {"primitives": p, "gd": gd, "ge": ge}


def _flow_metrics(pressure: tuple[float, ...] | list[float], auxiliaries: dict,
                  row: dict | None = None) -> dict:
    q = [g * p for g, p in zip(auxiliaries["gd"], pressure)]; total = sum(q); n = len(q)
    if not math.isfinite(total) or total <= 0:
        raise ValueError("NONPOSITIVE_OR_NONFINITE_TOTAL_FLOW")
    canonical_q = protocol.canonical_sector_q_hat(protocol.SectorFlowVector(
        tuple(q), n, "DIMENSIONAL_SECTOR_FLOW", 1., 1.))
    if any(value < -protocol.Q_ZERO_THRESHOLD for value in canonical_q) or sum(canonical_q) / n <= protocol.Q_ZERO_THRESHOLD:
        raise ValueError("NUMERICALLY_UNRESOLVED_OR_REVERSED_OUTLET_FLOW")
    fractions = [value / sum(canonical_q) for value in canonical_q]
    departures = [value - 1 / n for value in fractions]
    h_q = protocol.outlet_heterogeneity_from_fractions(fractions)
    seeded = (protocol.seeded_pattern_amplitude(departures, pattern=row["heterogeneity_pattern"],
              mode=row["heterogeneity_mode"], initial=row["initial_condition_variant"])
              if row is not None else protocol.NA)
    return {"H_q": h_q, "H_q_static": h_q, "A_seeded": seeded, "Q_total": total,
            "sector_outlet_flow": q, "sector_flow_fraction": fractions}


def _execute_static_case(store: CanonicalStore, case_id: str, profile: str,
                         context: _ValidatedExecutionContext, *, synthetic: bool = False) -> dict:
    if not isinstance(context, _ValidatedExecutionContext):
        raise ValueError("VALIDATED_EXECUTION_CONTEXT_REQUIRED")
    row = store.row(case_id)
    if row["pressure_mode"] != "PRESCRIBED_STATIC" or profile not in protocol.STATIC_NUMERICAL_PROFILES:
        raise ValueError("STATIC_DISPATCH_MISMATCH")
    started = utc_now(); a, b, aux = assemble_static_system(row)
    if profile == "BASE":
        solved = protocol.solve_dense_binary64(a, b)
        if solved.solver_status != "PASS":
            return _case_record(row, profile, context, "NUMERICALLY_UNRESOLVED", {},
                                synthetic=synthetic, started=started, linear_status="FAIL")
        pressure = solved.solution; residual = solved.scaled_residual
    else:
        refined = protocol.linear_refined_state(a, b)
        pressure = refined.corrected_state; residual = refined.corrected_scaled_residual
    metrics = _flow_metrics(pressure, aux, row); metrics["scaled_residual"] = residual
    return _case_record(row, profile, context, "COMPLETE", metrics, synthetic=synthetic,
                        started=started, linear_status="PASS")


def _evolved_primitives(row: dict, base: dict, x: list[float] | tuple[float, ...]) -> dict:
    if row["resistance_evolution_law"] == "NO_EVOLUTION":
        return {**base, "multipliers": [1.0] * len(base["H_i"])}
    return {**base, **protocol.evolved_resistance_primitives(
        base, list(x), float(row["feedback_gain"]), row["axial_placement"])}


def _evolved_primitives_observed(row: dict, base: dict, x: list[float] | tuple[float, ...],
                                 diagnostic_observer) -> dict:
    """Observed equivalent; callback output is intentionally ignored."""
    if diagnostic_observer is None:
        return _evolved_primitives(row, base, x)
    if row["resistance_evolution_law"] == "NO_EVOLUTION":
        return {**base, "multipliers": [1.0] * len(base["H_i"])}
    return {**base, **protocol.evolved_resistance_primitives(
        base, list(x), float(row["feedback_gain"]), row["axial_placement"],
        diagnostic_observer=diagnostic_observer)}


def _emit_diagnostic(observer, event: str, payload: dict) -> None:
    """Never permit diagnostic administration to affect a scientific result."""
    if observer is None:
        return
    try:
        observer(event, payload)
    except BaseException:
        return


def _dynamic_rhs_core(row: dict, profile: str, tau: float, state: list[float], base: dict,
                      storage: list[float], startup: list[float], *,
                      diagnostic_observer=None) -> tuple[list[float], dict]:
    """Pure frozen RHS and diagnostic primitives; does not increment solver counters."""
    n = row["sector_count"]; machine = row["pressure_mode"] == "MACHINE_COUPLED"
    evolving = row["resistance_evolution_law"] != "NO_EVOLUTION"
    pressures = state[:n]; upstream = state[n] if machine else None
    x = state[n + (1 if machine else 0):]
    evolved = _evolved_primitives_observed(row, base, x, diagnostic_observer)
    gu = [1 / value for value in evolved["R_u_i"]]; gd = [1 / value for value in evolved["R_d_i"]]
    if machine:
        sum_gu = sum(gu); right = upstream + .1 * sum(g * p for g, p in zip(gu, pressures))
        a = [[1 + .1 * sum_gu]]; b = [right]
        solve = protocol.linear_refined_state(a, b).corrected_state if profile == "LINEAR_REFINED" else \
            protocol.solve_dense_binary64(a, b).solution
        basket = solve[0]
    else:
        basket = min(tau / .05, 1.)
    qu = [g * (basket - p) for g, p in zip(gu, pressures)]
    qd = [g * p for g, p in zip(gd, pressures)]
    ge = float(row["lateral_edge_conductance_G_edge"])
    lateral = [ge * (pressures[i] - pressures[(i + 1) % n]) for i in range(n)]
    dp = [(qu[i] - qd[i] - lateral[i] + lateral[(i - 1) % n]) / storage[i] for i in range(n)]
    result = list(dp); supply = None
    if machine:
        command = min(tau / .05, 1.); supply = command * max(1 - upstream, 0)
        result.append((supply - sum(qu)) / float(row["machine_compliance_C_u"]))
    focusing = None
    if evolving:
        threshold = protocol.REFINED_Q_ZERO_THRESHOLD if profile == "STARTUP_REFINED" else protocol.Q_ZERO_THRESHOLD
        tau_max = protocol.REFINED_STARTUP_TAU_MAX if profile == "STARTUP_REFINED" else protocol.STARTUP_TAU_MAX
        focusing = protocol.evolution_focusing(tau=tau,
            flow=protocol.SectorFlowVector(tuple(qd), n, "DIMENSIONAL_SECTOR_FLOW", 1., 1.),
            startup=startup, zero_threshold=threshold, startup_tau_max=tau_max)
        sign = protocol.feedback_sign_scalar(row["feedback_sign"])
        theta = float(row["resistance_relaxation_tau_R"])
        result.extend((sign * (value - 1) - xi) / theta for value, xi in zip(focusing, x))
    return result, {"evolved": evolved, "G_u": gu, "G_d": gd, "basket_pressure": basket,
        "upstream_flow": qu, "outlet_flow": qd, "lateral_exchange": lateral,
        "supply_flow": supply, "focusing": focusing}


def _dynamic_hq_grid(row: dict, base: dict, storage: list[float], startup: list[float],
                     dense_output: Callable, points: int) -> tuple[list[float], float]:
    n = row["sector_count"]; machine = row["pressure_mode"] == "MACHINE_COUPLED"
    times = [i / (points - 1) for i in range(points)]
    states = dense_output(times); values = []
    startup_fractions = [value / n for value in startup]
    for k, tau in enumerate(times):
        if k == 0:
            values.append(protocol.outlet_heterogeneity_from_fractions(startup_fractions)); continue
        state = [float(states[i][k]) for i in range(len(states))]
        x = state[n + (1 if machine else 0):]
        evolved = _evolved_primitives(row, base, x)
        qd = [(1.0 / rd) * state[i] for i, rd in enumerate(evolved["R_d_i"])]
        canonical_q = protocol.canonical_sector_q_hat(protocol.SectorFlowVector(
            tuple(qd), n, "DIMENSIONAL_SECTOR_FLOW", 1., 1.))
        values.append(protocol.outlet_fraction_primitives(canonical_q)["H_q"])
    return values, protocol.composite_trapezoid(values)


def _execute_dynamic_case(store: CanonicalStore, case_id: str, profile: str,
                          context: _ValidatedExecutionContext, *, synthetic: bool = False,
                          solve_ivp_impl: Callable | None = None, diagnostic_observer=None) -> dict:
    """Execute the frozen dynamic network; tests provide only trivial ODE fixtures."""
    if not isinstance(context, _ValidatedExecutionContext):
        raise ValueError("VALIDATED_EXECUTION_CONTEXT_REQUIRED")
    row = store.row(case_id)
    if row["pressure_mode"] == "PRESCRIBED_STATIC" or profile not in protocol.DYNAMIC_NUMERICAL_PROFILES:
        raise ValueError("DYNAMIC_DISPATCH_MISMATCH")
    if solve_ivp_impl is None:
        solve_ivp_impl = importlib.import_module("scipy.integrate").solve_ivp
    started = utc_now(); n = row["sector_count"]
    base = protocol.resistance_primitives(n, row["heterogeneity_pattern"], row["heterogeneity_mode"],
        row["resistance_contrast"], row["axial_placement"], row["epsilon_floor"],
        row["initial_condition_variant"])
    storage = [float(row["hydraulic_storage_C_h"])] * n
    evolving = row["resistance_evolution_law"] != "NO_EVOLUTION"
    beta = float(row["feedback_gain"])
    machine = row["pressure_mode"] == "MACHINE_COUPLED"
    startup = protocol.startup_focusing(base, storage, row["pressure_mode"])
    nfev = 0

    def rhs(tau: float, state: list[float]) -> list[float]:
        nonlocal nfev
        nfev = protocol.enforce_rhs_cap(nfev)
        _emit_diagnostic(diagnostic_observer, "CANDIDATE_STATE",
            {"tau": tau, "candidate_step_index": nfev, "state": list(state)})
        return _dynamic_rhs_core(row, profile, tau, state, base, storage, startup,
                                 diagnostic_observer=diagnostic_observer)[0]

    y0 = [0.] * n + ([0.] if machine else []) + ([0.] * n if evolving else [])
    settings = ({"rtol": 2.5e-9, "atol": 2.5e-11, "max_step": .00125} if
                profile == "INTEGRATOR_REFINED" else {"rtol": 1e-8, "atol": 1e-10, "max_step": .0025})
    events = []
    if evolving:
        x_offset = n + (1 if machine else 0)
        for sector in range(n):
            def lower(_tau, state, sector=sector):
                return math.exp(beta * state[x_offset + sector]) - .25
            def upper(_tau, state, sector=sector):
                return 4. - math.exp(beta * state[x_offset + sector])
            lower.direction = -1; lower.terminal = True
            upper.direction = -1; upper.terminal = True
            events.extend((lower, upper))
    try:
        solved = solve_ivp_impl(rhs, (0., 1.), y0, method="DOP853", dense_output=True,
                                events=events or None, first_step=protocol.DYNAMIC_FIRST_STEP, **settings)
    except ValueError as exc:
        if not (str(exc).startswith("STOP_") or str(exc).startswith("LINEAR_REFINED_")):
            return _case_record(row, profile, context, "FAILED", {}, synthetic=synthetic,
                started=started, nfev=nfev, stop=type(exc).__name__ + ":" + str(exc),
                execution_failure_class="IMPLEMENTATION_EXCEPTION")
        status = "CAPPED" if "MAX_RHS" in str(exc) else "STOPPED"
        return _case_record(row, profile, context, status, {}, synthetic=synthetic,
                            started=started, nfev=nfev, stop=str(exc))
    except Exception as exc:
        return _case_record(row, profile, context, "FAILED", {}, synthetic=synthetic,
            started=started, nfev=nfev, stop=type(exc).__name__ + ":" + str(exc),
            execution_failure_class="IMPLEMENTATION_EXCEPTION")
    if not solved.success or solved.sol is None:
        return _case_record(row, profile, context, "FAILED", {}, synthetic=synthetic,
                            started=started, nfev=nfev, stop=str(solved.message))
    if hasattr(solved, "nfev") and solved.nfev != nfev:
        return _case_record(row, profile, context, "FAILED", {}, synthetic=synthetic,
                            started=started, nfev=nfev, stop="RHS_COUNTER_NFEV_MISMATCH")
    if diagnostic_observer is not None and len(solved.t):
        prior_index = max(0, len(solved.t) - 2)
        _emit_diagnostic(diagnostic_observer, "ACCEPTED_STEPS", {
            "prior_time": float(solved.t[prior_index]), "prior_step_index": prior_index,
            "prior_state": [float(solved.y[i][prior_index]) for i in range(len(solved.y))]})
    raw_t_events = getattr(solved, "t_events", None)
    raw_y_events = getattr(solved, "y_events", None)
    t_events = raw_t_events if raw_t_events is not None else ()
    y_events = raw_y_events if raw_y_events is not None else ()
    if events and (len(t_events) != len(events) or len(y_events) != len(events)):
        return _case_record(row, profile, context, "FAILED", {}, synthetic=synthetic,
            started=started, nfev=nfev, stop="EVENT_RESULT_STRUCTURE_INCONSISTENT",
            execution_failure_class="NUMERICAL_CASE_DISPOSITION")
    located = []
    for index, times in enumerate(t_events):
        if index >= len(y_events) or len(y_events[index]) != len(times):
            return _case_record(row, profile, context, "FAILED", {}, synthetic=synthetic,
                started=started, nfev=nfev, stop="EVENT_RESULT_STRUCTURE_INCONSISTENT",
                execution_failure_class="NUMERICAL_CASE_DISPOSITION")
        for event_index, tau_event in enumerate(times):
            states = y_events[index]
            event_state = states[event_index]
            sector = index // 2; bound = "LOWER_BOUND" if index % 2 == 0 else "UPPER_BOUND"
            x_value = event_state[n + (1 if machine else 0) + sector]
            target = .25 if bound == "LOWER_BOUND" else 4.
            if abs(math.exp(beta * x_value) - target) > protocol.EVENT_ROOT_VALUE_ATOL:
                return _case_record(row, profile, context, "FAILED", {}, synthetic=synthetic,
                    started=started, nfev=nfev, stop="EVENT_ROOT_STATE_INCONSISTENT_WITH_BOUNDARY")
            located.append({"tau": float(tau_event), "bound": bound, "sector_index": sector})
            _emit_diagnostic(diagnostic_observer, "LOCATED_EVENT_ROOT",
                {"tau": float(tau_event), "bound": bound, "sector_index": sector,
                 "state": [float(value) for value in event_state]})
    if located:
        selected = protocol.select_multiplier_event(located)
        _emit_diagnostic(diagnostic_observer, "STOPPED_RESULT_CONSTRUCTION",
            {"selected": dict(selected), "all_triggering_events": [dict(event) for event in located],
             "nfev": nfev})
        return _case_record(row, profile, context, "STOPPED", {"terminal_tau": selected["tau"]}, synthetic=synthetic,
                            started=started, nfev=nfev, stop=protocol.MULTIPLIER_STOP + ":" +
                            canonical_json(selected))
    try:
        sample1001 = solved.sol([i / 1000 for i in range(1001)])
        final_p = tuple(float(sample1001[i][-1]) for i in range(n))
        final_state = [float(sample1001[i][-1]) for i in range(len(sample1001))]
        final_x = final_state[n + (1 if machine else 0):]
        final_evolved = _evolved_primitives(row, base, final_x)
        aux = {"gd": [1 / x for x in final_evolved["R_d_i"]], "ge": float(row["lateral_edge_conductance_G_edge"])}
        metrics = _flow_metrics(final_p, aux, row)
        h1001, integral1001 = _dynamic_hq_grid(row, base, storage, startup, solved.sol, 1001)
        h2001, integral2001 = _dynamic_hq_grid(row, base, storage, startup, solved.sol, 2001)
    except Exception as exc:
        return _case_record(row, profile, context, "FAILED", {}, synthetic=synthetic,
            started=started, nfev=nfev, stop=type(exc).__name__ + ":" + str(exc),
            execution_failure_class="IMPLEMENTATION_EXCEPTION")
    metrics.update({"H_q_endpoint": metrics["H_q"], "H_q_integral_1001": integral1001,
        "H_q_integral_2001": integral2001, "H_q_grid_1001_count": len(h1001),
        "H_q_grid_2001_count": len(h2001), "final_multipliers": final_evolved["multipliers"],
        "final_R_u_i": final_evolved["R_u_i"], "final_R_d_i": final_evolved["R_d_i"],
        "final_G_d_i": aux["gd"]})
    _emit_diagnostic(diagnostic_observer, "NORMAL_COMPLETION",
        {"tau": 1.0, "nfev": nfev, "state": list(final_state)})
    return _case_record(row, profile, context, "COMPLETE", metrics, synthetic=synthetic,
                        started=started, nfev=nfev)


def _metric_value(record: dict, metric_kind: str) -> float:
    if record.get("status") != "COMPLETE":
        raise ValueError("NUMERICALLY_UNRESOLVED_REQUIRED_RESULT")
    if record.get("evidence_kind") == SYNTHETIC_BACKEND:
        # Synthetic values may exercise evidence arithmetic, but never scientific classification.
        pass
    keys = {"G_static_H": "H_q_static", "G_static_mode": "A_seeded",
            "G_coupling_end": "H_q_endpoint", "G_coupling_int": "H_q_integral_1001"}
    if metric_kind not in keys:
        raise ValueError("UNKNOWN_SCIENTIFIC_METRIC")
    key = keys[metric_kind]
    value = record.get("metric_primitives", {}).get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("INVALID_RESULT_METRIC")
    return float(value)


def evaluate_gain_evidence(canonical: CanonicalStore, results: ResultStore, subject_case_id: str,
                           metric_kind: str, numerical_profile: str) -> dict:
    subject = canonical.row(subject_case_id)
    if subject["case_role"] != "ACTIVE_SCIENTIFIC_CASE":
        raise ValueError("ORDINARY_GAIN_REQUIRES_ACTIVE_CASE")
    comparator_id = subject["comparator_case_id"]
    comparator = canonical.row(comparator_id)
    protocol._validate_comparator_pair(subject, comparator)
    static = subject["pressure_mode"] == "PRESCRIBED_STATIC"
    allowed = ("G_static_H", "G_static_mode") if static else ("G_coupling_end", "G_coupling_int")
    if metric_kind not in allowed:
        raise ValueError("METRIC_BOUNDARY_MODE_MISMATCH")
    manifest = results.load_manifest()
    active_record = results.read_bound_record(manifest, subject_case_id, numerical_profile)
    comparator_record = results.read_bound_record(manifest, comparator_id, numerical_profile)
    for field in ("authorization_id", "authorized_head", "authorized_tree", "evidence_kind"):
        if active_record.get(field) != comparator_record.get(field):
            raise ValueError("GAIN_RESULT_AUTHORITY_MISMATCH:" + field)
    numerator = _metric_value(active_record, metric_kind)
    denominator = _metric_value(comparator_record, metric_kind)
    generic_kind = "STATIC_GAIN" if static else ("DYNAMIC_ENDPOINT_GAIN" if metric_kind == "G_coupling_end"
                                                    else "DYNAMIC_INTEGRATED_GAIN")
    internal = protocol.build_gain_record(list(canonical.rows), subject_case_id, generic_kind,
                                          numerical_profile, numerator, denominator)
    return {"subject_case_id": internal.subject_case_id, "comparator_case_id": internal.comparator_case_id,
            "metric_kind": metric_kind, "profile": internal.numerical_profile,
            "gain": internal.gain, "denominator": internal.denominator,
            "denominator_floor": protocol.GAIN_DENOMINATOR_FLOOR, "status": "COMPLETE",
            "evidence_kind": active_record["evidence_kind"]}


def evaluate_uncertainty_evidence(canonical: CanonicalStore, results: ResultStore,
                                  subject_case_id: str, metric_kind: str) -> dict:
    subject = canonical.row(subject_case_id)
    static = subject["pressure_mode"] == "PRESCRIBED_STATIC"
    base = evaluate_gain_evidence(canonical, results, subject_case_id, metric_kind, "BASE")
    components: dict[str, float | str] = {name: protocol.NA for name in protocol.UNCERTAINTY_COMPONENTS}
    generic_kind = ("STATIC_GAIN" if static else
                    "DYNAMIC_ENDPOINT_GAIN" if metric_kind == "G_coupling_end" else "DYNAMIC_INTEGRATED_GAIN")
    contract = protocol.derive_uncertainty_contract(list(canonical.rows), subject_case_id, generic_kind,
                                                     "GAIN", "COMPLETE", "BASE")
    applicable = dict(contract.applicability)
    profiles = {"u_integrator": "INTEGRATOR_REFINED", "u_startup": "STARTUP_REFINED",
                "u_linear": "LINEAR_REFINED"}
    for name, profile in profiles.items():
        if applicable[name]:
            refined = evaluate_gain_evidence(canonical, results, subject_case_id, metric_kind, profile)
            components[name] = abs(base["gain"] - refined["gain"])
    if applicable["u_sampling"]:
        manifest = results.load_manifest()
        active = results.read_bound_record(manifest, subject_case_id, "BASE")
        comparator = results.read_bound_record(manifest, subject["comparator_case_id"], "BASE")
        d1001 = comparator["metric_primitives"]["H_q_integral_1001"]
        d2001 = comparator["metric_primitives"]["H_q_integral_2001"]
        if abs(d1001) <= protocol.GAIN_DENOMINATOR_FLOOR or abs(d2001) <= protocol.GAIN_DENOMINATOR_FLOOR:
            raise ValueError("NUMERICALLY_UNRESOLVED_DENOMINATOR_FLOOR")
        g1001 = active["metric_primitives"]["H_q_integral_1001"] / d1001
        g2001 = active["metric_primitives"]["H_q_integral_2001"] / d2001
        components["u_sampling"] = abs(g1001 - g2001)
    if applicable["u_sector"]:
        companion = protocol.sector_companion_case_id(subject, list(canonical.rows))
        components["u_sector"] = abs(base["gain"] - evaluate_gain_evidence(
            canonical, results, companion, metric_kind, "BASE")["gain"])
    total = protocol.combine_uncertainty(components, contract)
    return {"subject_case_id": subject_case_id, "metric_kind": metric_kind,
            "components": components, "total": total, "status": "COMPLETE",
            "evidence_kind": base["evidence_kind"]}


def _classification_precedence_fixture(*, authority_invalid: bool = False,
        structural_identity: bool = False, numerical_unresolved: bool = False,
        sector_disagreement: bool = False,
        model_form_disagreement: bool = False, metrics: tuple[tuple[float, float], tuple[float, float]] | None = None) -> str:
    """Pure precedence engine. Tests use it only with synthetic scalar fixtures."""
    if authority_invalid: return "AUTHORITY_OR_ARTIFACT_INVALID"
    if structural_identity: return "ANALYTICAL_STRUCTURAL_IDENTITY"
    if numerical_unresolved or metrics is None: return "NUMERICALLY_UNRESOLVED"
    if model_form_disagreement or sector_disagreement: return "MODEL_FORM_OR_SECTOR_RESOLUTION_DISAGREEMENT"
    labels = []
    for gain, uncertainty in metrics:
        if not all(math.isfinite(value) and value >= 0 for value in (gain, uncertainty)):
            return "NUMERICALLY_UNRESOLVED"
        if uncertainty > protocol.uncertainty_limit(gain): return "NUMERICALLY_UNRESOLVED"
        if gain + uncertainty <= .90: labels.append("LATERAL_EQUALIZATION")
        elif gain - uncertainty >= 1.10: labels.append("HETEROGENEITY_AMPLIFIES")
        elif gain - uncertainty >= .90 and gain + uncertainty <= 1.10: labels.append("HETEROGENEITY_PERSISTS")
        else: labels.append("NEAR_THRESHOLD_TRANSITION")
    if labels[0] != labels[1]: return "METRIC_DISAGREEMENT"
    return labels[0]


def _qualified_classification_record(row: dict, regime_label: str, **details: object) -> dict:
    reserved = {"ordinary_regime_label", "qualified_classification", "stage_a_architecture_id",
                *protocol.stage_a_initial_condition_scope(row)}
    collisions = reserved.intersection(details)
    if collisions:
        raise ValueError("CLASSIFICATION_DERIVED_FIELD_COLLISION:" + ",".join(sorted(collisions)))
    scope = protocol.stage_a_initial_condition_scope(row)
    return {"ordinary_regime_label": regime_label,
            "qualified_classification": protocol.qualify_stage_a_classification(row, regime_label),
            "stage_a_architecture_id": protocol.ARCHITECTURE_ID, **scope, **details}


def classify_stage_a_evidence(canonical: CanonicalStore, results: ResultStore,
                              subject_case_id: str) -> dict:
    manifest = results.load_manifest()
    if manifest["evidence_kind"] == SYNTHETIC_BACKEND:
        raise ValueError("SYNTHETIC_EVIDENCE_CANNOT_CLASSIFY_SCIENTIFICALLY")
    if manifest["evidence_kind"] == PILOT_EVIDENCE:
        raise ValueError("DIAGNOSTIC_TIMING_EVIDENCE_CANNOT_CLASSIFY_SCIENTIFICALLY")
    if manifest["evidence_kind"] != REAL_BACKEND:
        raise ValueError("AUTHORITY_OR_ARTIFACT_INVALID_EVIDENCE_KIND")
    subject = canonical.row(subject_case_id)
    structural = (subject["case_role"] != "ACTIVE_SCIENTIFIC_CASE" or
                  subject["lateral_conductance_ratio"] == "0" or
                  subject["axial_placement"] == "AXIALLY_SELF_SIMILAR" or
                  subject["heterogeneity_pattern"] == "UNIFORM")
    if structural:
        return _qualified_classification_record(subject, "ANALYTICAL_STRUCTURAL_IDENTITY",
            numerical_control_status="SEPARATELY_RECORDED",
            precedence=list(protocol_spec_precedence()))
    metric_names = (("G_static_H", "G_static_mode") if subject["pressure_mode"] == "PRESCRIBED_STATIC"
                    else ("G_coupling_end", "G_coupling_int"))
    evidence = []
    for name in metric_names:
        gain = evaluate_gain_evidence(canonical, results, subject_case_id, name, "BASE")
        uncertainty = evaluate_uncertainty_evidence(canonical, results, subject_case_id, name)
        evidence.append((gain["gain"], uncertainty["total"]))
    sector_disagreement = False
    if protocol.sector_refinement_nref(subject) != protocol.NA:
        companion_id = protocol.sector_companion_case_id(subject, list(canonical.rows))
        companion = canonical.row(companion_id)
        companion_metrics = (("G_static_H", "G_static_mode") if companion["pressure_mode"] == "PRESCRIBED_STATIC"
                             else ("G_coupling_end", "G_coupling_int"))
        companion_evidence = []
        for other_name in companion_metrics:
            other = evaluate_gain_evidence(canonical, results, companion_id, other_name, "BASE")["gain"]
            other_u = evaluate_uncertainty_evidence(canonical, results, companion_id, other_name)["total"]
            companion_evidence.append((other, other_u))
        sector_disagreement = (_classification_precedence_fixture(metrics=tuple(evidence)) !=
                               _classification_precedence_fixture(metrics=tuple(companion_evidence)))
    classification = _classification_precedence_fixture(metrics=tuple(evidence),
                                                          sector_disagreement=sector_disagreement)
    return _qualified_classification_record(subject, classification,
        metrics=dict(zip(metric_names, evidence)), precedence=list(protocol_spec_precedence()))


def protocol_spec_precedence() -> tuple[str, ...]:
    return protocol.STAGE_A_ORDINARY_CLASSIFICATIONS


CLASSIFICATION_SCOPE_FIELDS = ("dynamic_initial_state_variant", "initial_condition_scope",
    "initial_condition_robustness", "bistability_status", "initial_condition_dependence_branch")
CLASSIFICATION_AUTHORITY_FIELDS = ("run_id", "authorization_id", "authorized_head", "authorized_tree",
    "matrix_semantic_sha256", "protocol_sha256", "executor_source_sha256",
    "run_manifest_identity_sha256", "evidence_kind")
CLASSIFICATION_RECORD_FIELDS = frozenset(("schema", "stage", "case_id", "profile", "row_hash",
    "boundary_mode", "stage_a_architecture_id", *CLASSIFICATION_SCOPE_FIELDS,
    "ordinary_regime_label", "qualified_classification", *CLASSIFICATION_AUTHORITY_FIELDS,
    "scientific_admissibility"))


def _classification_manifest_bindings(manifest: Mapping[str, object]) -> dict[str, object]:
    return {"run_id": manifest["run_id"], "authorization_id": manifest["authorization_id"],
        "authorized_head": manifest["git_head"], "authorized_tree": manifest["git_tree"],
        "matrix_semantic_sha256": manifest["matrix_semantic_sha256"],
        "protocol_sha256": manifest["protocol_sha256"],
        "executor_source_sha256": manifest["executor_source_sha256"],
        "run_manifest_identity_sha256": manifest["run_manifest_identity_sha256"],
        "evidence_kind": manifest["evidence_kind"]}


def build_classification_record(canonical: CanonicalStore, manifest: Mapping[str, object],
        case_id: str, profile: str, classification: Mapping[str, object], *,
        allow_synthetic_fixture: bool = False) -> dict:
    """Build a permanently inadmissible test record; canonical export is result-bound."""
    if not allow_synthetic_fixture:
        raise ValueError("DIRECT_CANONICAL_CLASSIFICATION_BUILDER_MISUSE")
    row = canonical.row(case_id)
    allowed_profiles = (protocol.STATIC_NUMERICAL_PROFILES if row["pressure_mode"] == "PRESCRIBED_STATIC"
                        else protocol.DYNAMIC_NUMERICAL_PROFILES)
    if profile not in allowed_profiles:
        raise ValueError("CLASSIFICATION_PROFILE_NOT_AUTHORIZED_FOR_ROW")
    expected_scope = protocol.stage_a_initial_condition_scope(row)
    expected_keys = {"ordinary_regime_label", "qualified_classification", "stage_a_architecture_id",
                     *CLASSIFICATION_SCOPE_FIELDS}
    if not expected_keys.issubset(classification):
        raise ValueError("CLASSIFICATION_OUTPUT_REQUIRED_FIELD_MISSING")
    if classification.get("stage_a_architecture_id") != protocol.ARCHITECTURE_ID or any(
            classification.get(key) != value for key, value in expected_scope.items()):
        raise ValueError("CLASSIFICATION_OUTPUT_SCOPE_OR_ARCHITECTURE_INVALID")
    ordinary = classification.get("ordinary_regime_label")
    expected_qualified = protocol.qualify_stage_a_classification(row, ordinary)
    if classification.get("qualified_classification") != expected_qualified:
        raise ValueError("CLASSIFICATION_OUTPUT_QUALIFIED_VALUE_MISMATCH")
    evidence_kind = manifest.get("evidence_kind")
    if evidence_kind != SYNTHETIC_BACKEND:
        raise ValueError("CLASSIFICATION_RECORD_NONCANONICAL_EVIDENCE_REJECTED")
    admissibility = "SYNTHETIC_TEST_ONLY_INADMISSIBLE"
    return {"schema": CLASSIFICATION_SCHEMA, "stage": "STAGE_A", "case_id": case_id,
        "profile": profile, "row_hash": row["row_sha256"], "boundary_mode": row["pressure_mode"],
        "stage_a_architecture_id": protocol.ARCHITECTURE_ID, **expected_scope,
        "ordinary_regime_label": ordinary, "qualified_classification": expected_qualified,
        **_classification_manifest_bindings(manifest), "scientific_admissibility": admissibility}


def validate_classification_record(canonical: CanonicalStore, manifest: Mapping[str, object],
        record: Mapping[str, object], *, allow_synthetic_fixture: bool = False) -> None:
    if set(record) != CLASSIFICATION_RECORD_FIELDS:
        raise ValueError("CLASSIFICATION_RECORD_SCHEMA_FIELDS_INVALID")
    if record.get("schema") != CLASSIFICATION_SCHEMA or record.get("stage") != "STAGE_A":
        raise ValueError("CLASSIFICATION_RECORD_SCHEMA_OR_STAGE_INVALID")
    row = canonical.row(str(record["case_id"])); expected_scope = protocol.stage_a_initial_condition_scope(row)
    if (record.get("row_hash") != row["row_sha256"] or
            record.get("boundary_mode") != row["pressure_mode"] or
            record.get("stage_a_architecture_id") != protocol.ARCHITECTURE_ID):
        raise ValueError("CLASSIFICATION_RECORD_CANONICAL_IDENTITY_INVALID")
    allowed_profiles = (protocol.STATIC_NUMERICAL_PROFILES if row["pressure_mode"] == "PRESCRIBED_STATIC"
                        else protocol.DYNAMIC_NUMERICAL_PROFILES)
    if record.get("profile") not in allowed_profiles:
        raise ValueError("CLASSIFICATION_RECORD_PROFILE_INVALID")
    if any(record.get(key) != value for key, value in expected_scope.items()):
        raise ValueError("CLASSIFICATION_RECORD_SCOPE_INVALID")
    expected_qualified = protocol.qualify_stage_a_classification(
        row, str(record.get("ordinary_regime_label")))
    if record.get("qualified_classification") != expected_qualified:
        raise ValueError("CLASSIFICATION_RECORD_QUALIFIED_VALUE_MISMATCH")
    bindings = _classification_manifest_bindings(manifest)
    if any(record.get(key) != value for key, value in bindings.items()):
        raise ValueError("CLASSIFICATION_RECORD_AUTHORITY_MISMATCH")
    synthetic = record.get("evidence_kind") == SYNTHETIC_BACKEND
    expected_admissibility = ("SYNTHETIC_TEST_ONLY_INADMISSIBLE" if synthetic
                              else "CANONICAL_STAGE_A_SCIENTIFIC_EVIDENCE")
    if record.get("scientific_admissibility") != expected_admissibility:
        raise ValueError("CLASSIFICATION_RECORD_ADMISSIBILITY_INVALID")
    if synthetic and not allow_synthetic_fixture:
        raise ValueError("SYNTHETIC_CLASSIFICATION_RECORD_SCIENTIFICALLY_INADMISSIBLE")
    if not synthetic and record.get("evidence_kind") != REAL_BACKEND:
        raise ValueError("CLASSIFICATION_RECORD_NONCANONICAL_EVIDENCE_REJECTED")


def _classification_artifact_paths(result_store: ResultStore) -> tuple[Path, Path, Path]:
    root = result_store.root / "classifications"
    return (root / "CLASSIFICATION_RECORDS.jsonl", root / "CLASSIFICATION_SUMMARY.json",
            root / "CLASSIFICATION_REPORT.md")


def _write_classification_artifacts(canonical: CanonicalStore, result_store: ResultStore,
        manifest: Mapping[str, object], records: list[dict], *,
        allow_synthetic_fixture: bool, canonical_publication: bool = False) -> dict:
    plan_order = {tuple(key): index for index, key in enumerate(build_plan(canonical)["keys"])}
    seen: set[tuple[str, str]] = set(); validated: list[dict] = []
    for record in records:
        validate_classification_record(canonical, manifest, record,
            allow_synthetic_fixture=allow_synthetic_fixture)
        key = (str(record["case_id"]), str(record["profile"]))
        if key in seen:
            raise ValueError("DUPLICATE_CLASSIFICATION_KEY")
        if key not in plan_order:
            raise ValueError("CLASSIFICATION_KEY_NOT_IN_FROZEN_PLAN")
        seen.add(key); validated.append(dict(record))
    validated.sort(key=lambda record: plan_order[(record["case_id"], record["profile"])])
    ordinary: dict[str, int] = {}; qualified: dict[str, int] = {}; scopes: dict[str, int] = {}
    variants: dict[str, int] = {}
    for record in validated:
        for field, destination in (("ordinary_regime_label", ordinary),
                ("qualified_classification", qualified), ("initial_condition_scope", scopes),
                ("dynamic_initial_state_variant", variants)):
            value = str(record[field]); destination[value] = destination.get(value, 0) + 1
    total = len(validated)
    if any(sum(counts.values()) != total for counts in (ordinary, qualified, scopes, variants)):
        raise ValueError("CLASSIFICATION_SUMMARY_COUNT_RECONCILIATION_FAILED")
    summary = {"schema": CLASSIFICATION_SUMMARY_SCHEMA, "total_records": total,
        "stage_a_architecture_id": protocol.ARCHITECTURE_ID,
        "governing_run_manifest_identity_sha256": manifest["run_manifest_identity_sha256"],
        "scientific_admissibility": ("SYNTHETIC_TEST_ONLY_INADMISSIBLE" if
            manifest["evidence_kind"] == SYNTHETIC_BACKEND else "CANONICAL_STAGE_A_SCIENTIFIC_EVIDENCE"),
        "ordinary_classification_counts": dict(sorted(ordinary.items())),
        "qualified_classification_counts": dict(sorted(qualified.items())),
        "initial_condition_scope_counts": dict(sorted(scopes.items())),
        "dynamic_initial_state_variant_counts": dict(sorted(variants.items())),
        "reconciliation_status": "PASS", "rejected_record_count": 0,
        "initial_condition_robustness": protocol.NOT_ADJUDICATED_STAGE_A,
        "bistability_status": protocol.NOT_ADJUDICATED_STAGE_A,
        "d4_status": protocol.D4_STATUS, "x1_status": protocol.X1_STATUS,
        "physical_validation": "NOT_ESTABLISHED"}
    records_path, summary_path, report_path = _classification_artifact_paths(result_store)
    atomic_write_text(records_path, "".join(canonical_json(record) + "\n" for record in validated))
    atomic_write_json(summary_path, summary)
    report_lines = ["# SCI-LC-001A Stage-A classification report", "",
        f"- Governing manifest: `{manifest['run_manifest_identity_sha256']}`",
        f"- Authorized HEAD: `{manifest['git_head']}`", f"- Authorized tree: `{manifest['git_tree']}`",
        f"- Architecture: `{protocol.ARCHITECTURE_ID}`", f"- Canonical records: {total}",
        f"- Scientific admissibility: `{summary['scientific_admissibility']}`", "",
        "## Ordinary classification counts", ""]
    report_lines.extend(f"- `{label}`: {count}" for label, count in sorted(ordinary.items()))
    report_lines.extend(["", "## Qualified classification counts", ""])
    report_lines.extend(f"- `{label}`: {count}" for label, count in sorted(qualified.items()))
    report_lines.extend(["", "## Initial-condition scope counts", ""])
    report_lines.extend(f"- `{label}`: {count}" for label, count in sorted(scopes.items()))
    report_lines.extend(["", "## Explicit non-claims", "",
        "- Alternate-start agreement is not established.",
        "- Initial-condition robustness is not adjudicated.", "- Bistability is not adjudicated.",
        "- Physical validation is not established.", "- D4 is deferred and unauthorized.",
        "- X1 is deferred and unauthorized.", "",
        "Rejected invalid, stale, duplicate, diagnostic, synthetic, D4, or X1 records: 0 accepted.", ""])
    atomic_write_text(report_path, "\n".join(report_lines))
    return summary


def write_classification_artifacts(canonical: CanonicalStore, result_store: ResultStore,
        manifest: Mapping[str, object], records: list[dict], *,
        allow_synthetic_fixture: bool = False) -> dict:
    """Serialize only permanent test fixtures; canonical publication uses export."""
    if not allow_synthetic_fixture:
        raise ValueError("DIRECT_CANONICAL_CLASSIFICATION_WRITER_MISUSE")
    loaded_manifest = result_store.load_manifest()
    if manifest != loaded_manifest or manifest.get("evidence_kind") != SYNTHETIC_BACKEND:
        raise ValueError("NONCANONICAL_FIXTURE_RUN_CONTEXT_INVALID")
    return _write_classification_artifacts(canonical, result_store, manifest, records,
        allow_synthetic_fixture=True)


def load_classification_records(canonical: CanonicalStore, result_store: ResultStore,
        manifest: Mapping[str, object], *, allow_synthetic_fixture: bool = False) -> list[dict]:
    records_path, _, _ = _classification_artifact_paths(result_store)
    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines() if line]
    seen: set[tuple[str, str]] = set()
    for record in records:
        validate_classification_record(canonical, manifest, record,
            allow_synthetic_fixture=allow_synthetic_fixture)
        key = (record["case_id"], record["profile"])
        if key in seen: raise ValueError("DUPLICATE_CLASSIFICATION_KEY")
        seen.add(key)
    return records


def load_classification_summary(result_store: ResultStore, records: list[dict]) -> dict:
    _, summary_path, _ = _classification_artifact_paths(result_store)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    required = {"schema", "total_records", "stage_a_architecture_id",
        "governing_run_manifest_identity_sha256", "scientific_admissibility",
        "ordinary_classification_counts", "qualified_classification_counts",
        "initial_condition_scope_counts", "dynamic_initial_state_variant_counts",
        "reconciliation_status", "rejected_record_count", "initial_condition_robustness",
        "bistability_status", "d4_status", "x1_status", "physical_validation"}
    if set(summary) != required or summary.get("schema") != CLASSIFICATION_SUMMARY_SCHEMA:
        raise ValueError("CLASSIFICATION_SUMMARY_SCHEMA_INVALID")
    manifest = result_store.load_manifest()
    expected_admissibility = ("SYNTHETIC_TEST_ONLY_INADMISSIBLE" if
        manifest["evidence_kind"] == SYNTHETIC_BACKEND else
        "CANONICAL_STAGE_A_SCIENTIFIC_EVIDENCE")
    expected_authority = {
        "stage_a_architecture_id": protocol.ARCHITECTURE_ID,
        "governing_run_manifest_identity_sha256": manifest["run_manifest_identity_sha256"],
        "scientific_admissibility": expected_admissibility,
        "initial_condition_robustness": protocol.NOT_ADJUDICATED_STAGE_A,
        "bistability_status": protocol.NOT_ADJUDICATED_STAGE_A,
        "d4_status": protocol.D4_STATUS,
        "x1_status": protocol.X1_STATUS,
        "physical_validation": "NOT_ESTABLISHED",
        "rejected_record_count": 0,
    }
    if any(summary.get(key) != value for key, value in expected_authority.items()):
        raise ValueError("CLASSIFICATION_SUMMARY_AUTHORITY_INVALID")
    expected: dict[str, dict[str, int]] = {}
    for field, output in (("ordinary_regime_label", "ordinary_classification_counts"),
            ("qualified_classification", "qualified_classification_counts"),
            ("initial_condition_scope", "initial_condition_scope_counts"),
            ("dynamic_initial_state_variant", "dynamic_initial_state_variant_counts")):
        counts: dict[str, int] = {}
        for record in records:
            value = str(record[field]); counts[value] = counts.get(value, 0) + 1
        expected[output] = dict(sorted(counts.items()))
    if (summary.get("total_records") != len(records) or
            any(summary.get(key) != value for key, value in expected.items()) or
            summary.get("reconciliation_status") != "PASS"):
        raise ValueError("CLASSIFICATION_SUMMARY_COUNT_RECONCILIATION_FAILED")
    return summary


def _build_canonical_classification_record(canonical: CanonicalStore, manifest: Mapping[str, object],
        case_id: str, profile: str, classification: Mapping[str, object],
        executed_result: Mapping[str, object]) -> dict:
    """Derive one canonical record from an already ledger-validated executed result."""
    row = canonical.row(case_id)
    if (executed_result.get("case_id") != case_id or executed_result.get("profile") != profile or
            executed_result.get("row_hash") != row["row_sha256"] or
            executed_result.get("status") != "COMPLETE"):
        raise ValueError("CANONICAL_CLASSIFICATION_RESULT_IDENTITY_OR_ELIGIBILITY_INVALID")
    reserved = {"scientific_admissibility", *CLASSIFICATION_AUTHORITY_FIELDS,
                *CLASSIFICATION_RECORD_FIELDS}
    unexpected = reserved.intersection(set(classification) - {
        "ordinary_regime_label", "qualified_classification", "stage_a_architecture_id",
        *CLASSIFICATION_SCOPE_FIELDS})
    if unexpected:
        raise ValueError("CANONICAL_CLASSIFICATION_DERIVED_FIELD_COLLISION:" +
                         ",".join(sorted(unexpected)))
    expected_scope = protocol.stage_a_initial_condition_scope(row)
    if classification.get("stage_a_architecture_id") != protocol.ARCHITECTURE_ID or any(
            classification.get(key) != value for key, value in expected_scope.items()):
        raise ValueError("CLASSIFICATION_OUTPUT_SCOPE_OR_ARCHITECTURE_INVALID")
    ordinary = classification.get("ordinary_regime_label")
    qualified = protocol.qualify_stage_a_classification(row, ordinary)
    if classification.get("qualified_classification") != qualified:
        raise ValueError("CLASSIFICATION_OUTPUT_QUALIFIED_VALUE_MISMATCH")
    record = {"schema": CLASSIFICATION_SCHEMA, "stage": "STAGE_A", "case_id": case_id,
        "profile": profile, "row_hash": row["row_sha256"], "boundary_mode": row["pressure_mode"],
        "stage_a_architecture_id": protocol.ARCHITECTURE_ID, **expected_scope,
        "ordinary_regime_label": ordinary, "qualified_classification": qualified,
        **_classification_manifest_bindings(manifest),
        "scientific_admissibility": "CANONICAL_STAGE_A_SCIENTIFIC_EVIDENCE"}
    validate_classification_record(canonical, manifest, record)
    return record


def _publish_canonical_classification_artifacts(canonical: CanonicalStore,
        result_store: ResultStore, manifest: Mapping[str, object], records: list[dict]) -> dict:
    """Validate and atomically install the complete canonical classification set."""
    destination = result_store.root / "classifications"
    if destination.exists():
        raise ValueError("CANONICAL_CLASSIFICATION_OUTPUT_ALREADY_EXISTS")
    temporary_root = Path(tempfile.mkdtemp(prefix=".classification-publication-",
                                           dir=result_store.root))
    temporary_store = ResultStore(temporary_root, canonical)
    try:
        summary = _write_classification_artifacts(canonical, temporary_store, manifest, records,
            allow_synthetic_fixture=False, canonical_publication=True)
        staged_records = load_classification_records(canonical, temporary_store, manifest)
        load_classification_summary(temporary_store, staged_records)
        os.replace(temporary_root / "classifications", destination)
        return summary
    except BaseException:
        shutil.rmtree(temporary_root, ignore_errors=True)
        raise
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root, ignore_errors=True)


def export_stage_a_classifications(canonical: CanonicalStore, result_store: ResultStore) -> dict:
    """Canonical no-solver export derived only from a complete validated run store."""
    try:
        manifest = result_store.load_manifest()
    except FileNotFoundError as exc:
        raise ValueError("CANONICAL_CLASSIFICATION_RUN_CONTEXT_MISSING") from exc
    except (KeyError, json.JSONDecodeError) as exc:
        raise ValueError("CANONICAL_CLASSIFICATION_RUN_CONTEXT_INVALID") from exc
    plan = build_plan(canonical)
    expected_manifest = {
        "git_head": git_value("rev-parse", "HEAD"),
        "git_tree": git_value("rev-parse", "HEAD^{tree}"),
        "matrix_semantic_sha256": canonical.matrix_hash,
        "protocol_sha256": canonical.protocol_hash,
        "executor_source_sha256": sha256_file(Path(__file__)),
        "execution_mode": "execute", "backend": REAL_BACKEND,
        "evidence_kind": REAL_BACKEND, "stage_a_architecture_id": protocol.ARCHITECTURE_ID,
        "task_count": plan["total_keys"], "status": "COMPLETE",
        "dynamic_initial_state_variant": protocol.DYNAMIC_INITIAL_STATE_VARIANT,
        "initial_condition_scope": protocol.DYNAMIC_INITIAL_CONDITION_SCOPE,
        "initial_condition_robustness": protocol.NOT_ADJUDICATED_STAGE_A,
        "bistability_status": protocol.NOT_ADJUDICATED_STAGE_A,
        "initial_condition_dependence_branch": protocol.INITIAL_CONDITION_BRANCH_STATUS,
    }
    if any(manifest.get(key) != value for key, value in expected_manifest.items()):
        raise ValueError("CANONICAL_CLASSIFICATION_RUN_CONTEXT_INVALID")
    if manifest["evidence_kind"] != REAL_BACKEND:
        raise ValueError("CLASSIFICATION_EXPORT_REQUIRES_CANONICAL_STAGE_A_EVIDENCE")
    records: list[dict] = []
    for case_id, profile in plan["keys"]:
        if profile != "BASE":
            continue
        if not result_store.record_path(case_id, profile).is_file():
            raise ValueError("CANONICAL_CLASSIFICATION_RESULT_RECORD_MISSING:" + case_id)
        result = result_store.read_bound_record(manifest, case_id, profile)
        if result.get("status") != "COMPLETE":
            raise ValueError("CANONICAL_CLASSIFICATION_RESULT_NOT_ELIGIBLE:" + case_id)
        if result.get("backend") != REAL_BACKEND or result.get("evidence_kind") != REAL_BACKEND:
            raise ValueError("CANONICAL_CLASSIFICATION_RESULT_EVIDENCE_INVALID:" + case_id)
        classification = classify_stage_a_evidence(canonical, result_store, case_id)
        records.append(_build_canonical_classification_record(
            canonical, manifest, case_id, profile, classification, result))
    return _publish_canonical_classification_artifacts(canonical, result_store, manifest, records)


def synthetic_backend_record(row: dict, profile: str, context: _ValidatedExecutionContext) -> dict:
    """Deterministic orchestration fixture; it does not solve a matrix row."""
    value = 1.0 + (int(hashlib.sha256(f"{row['case_id']}:{profile}".encode()).hexdigest()[:6], 16) % 1000) / 1e6
    metrics = {"H_q": value, "H_q_static": value, "A_seeded": value + .01,
               "H_q_endpoint": value + .02, "H_q_integral_1001": value + .03,
               "H_q_integral_2001": value + .030001, "Q_total": 1.,
               "sector_outlet_flow": [], "sector_flow_fraction": []}
    return _case_record(row, profile, context, "COMPLETE", metrics, synthetic=True,
                        started="SYNTHETIC_DETERMINISTIC", nfev=0)


def _execute_canonical_case(store: CanonicalStore, row: Mapping[str, object], profile: str,
                            context: _ValidatedExecutionContext, *, diagnostic_observer=None) -> dict:
    """Dispatch one authority-bound real calculation; callers cannot replace it."""
    if not isinstance(context, _ValidatedExecutionContext):
        raise ValueError("VALIDATED_EXECUTION_CONTEXT_REQUIRED")
    if context.backend != REAL_BACKEND or context.evidence_kind not in (REAL_BACKEND, PILOT_EVIDENCE):
        raise ValueError("CANONICAL_DISPATCH_REQUIRES_REAL_VALIDATED_CONTEXT")
    canonical = store.row(str(row.get("case_id")))
    if canonical is not row and canonical != row:
        raise ValueError("CANONICAL_DISPATCH_ROW_MISMATCH")
    profiles = (protocol.STATIC_NUMERICAL_PROFILES if canonical["pressure_mode"] == "PRESCRIBED_STATIC"
                else protocol.DYNAMIC_NUMERICAL_PROFILES)
    if profile not in profiles:
        raise ValueError("PROFILE_NOT_AUTHORIZED_FOR_ROW")
    if canonical["pressure_mode"] == "PRESCRIBED_STATIC":
        return _execute_static_case(store, canonical["case_id"], profile, context)
    if canonical["pressure_mode"] in ("PRESCRIBED_DYNAMIC_RAMP", "MACHINE_COUPLED"):
        return _execute_dynamic_case(store, canonical["case_id"], profile, context,
                                     diagnostic_observer=diagnostic_observer)
    raise ValueError("UNSUPPORTED_CANONICAL_BOUNDARY_MODE")


def _execute_graph(store: CanonicalStore, result_store: ResultStore, context: _ValidatedExecutionContext,
                  *, interrupt_after: int | None = None,
                  diagnostic_config: obs_001.DiagnosticConfig | None = None) -> dict:
    if not isinstance(context, _ValidatedExecutionContext):
        raise ValueError("VALIDATED_EXECUTION_CONTEXT_REQUIRED")
    if context.backend != REAL_BACKEND or context.evidence_kind != REAL_BACKEND:
        raise ValueError("REAL_GRAPH_REQUIRES_REAL_STAGE_A_CONTEXT")
    plan = build_plan(store); completed = reused = 0
    diagnostic_config = diagnostic_config or obs_001.DiagnosticConfig.from_field(None)
    dynamic_keys = [case_id + "__" + profile for case_id, profile in plan["keys"]
                    if store.row(case_id)["pressure_mode"] != "PRESCRIBED_STATIC"]
    diagnostic_run = obs_001.DiagnosticRun(diagnostic_config, dynamic_keys) if diagnostic_config.enabled else None
    manifest = result_store.begin_run(context, plan["total_keys"])
    infrastructure_failure = False
    for case_id, profile in plan["keys"]:
        if result_store.reusable(manifest, case_id, profile):
            reused += 1; continue
        if interrupt_after is not None and completed >= interrupt_after:
            break
        row = store.row(case_id)
        key_id = case_id + "__" + profile
        key_observer = None
        if diagnostic_run is not None and row["pressure_mode"] != "PRESCRIBED_STATIC":
            n = int(row["sector_count"]); machine = row["pressure_mode"] == "MACHINE_COUPLED"
            evolving = row["resistance_evolution_law"] != "NO_EVOLUTION"
            state_names = ([f"p_{i}" for i in range(n)] + (["p_upstream"] if machine else []) +
                           ([f"x_{i}" for i in range(n)] if evolving else []))
            base_h = protocol.resistance_primitives(n, row["heterogeneity_pattern"], row["heterogeneity_mode"],
                row["resistance_contrast"], row["axial_placement"], row["epsilon_floor"],
                row["initial_condition_variant"])["H_i"]
            common = {"implementation_version": obs_001.IMPLEMENTATION_VERSION,
                "implementation_sha256": sha256_file(Path(obs_001.__file__)),
                "configuration_sha256": diagnostic_config.configuration_sha256,
                "repository": "https://github.com/trbrewer/espresso-whole-pull.git",
                "candidate_head": context.authorized_head, "candidate_tree": context.authorized_tree,
                "executor_sha256": context.executor_identity,
                "protocol_source_sha256": sha256_file(Path(protocol.__file__)),
                "protocol_json_sha256": sha256_file(PROTOCOL_PATH),
                "matrix_json_sha256": sha256_file(MATRIX_PATH),
                "matrix_csv_sha256": sha256_file(MATRIX_PATH.with_suffix(".csv")),
                "plan_sha256": "32257a94c278149fad01eb212f35592c8ff6971553ce59a9f9c85f72f39aec27",
                "backend": context.backend, "run_id": context.run_id,
                "execution_authority": {"identity": context.authorization_id, "sha256": None},
                "diagnostic_authority": {"identity": "OBS_001_CONFIGURATION", "sha256": diagnostic_config.configuration_sha256},
                "key_id": key_id, "row_id": case_id, "arm": row["arm"], "profile": profile,
                "model_variant": row["model_variant"], "process_id": os.getpid(),
                "worker_id": "EXECUTOR_MAIN", "attempt_number": 1}
            key_observer = obs_001.ExecutorKeyObserver(common, state_names, base_h)
        try:
            if key_observer is None:
                record = _execute_canonical_case(store, row, profile, context)
            else:
                record = _execute_canonical_case(store, row, profile, context,
                                                 diagnostic_observer=key_observer)
        except Exception as exc:
            record = _case_record(row, profile, context, "FAILED", {}, synthetic=False,
                started=utc_now(), nfev=None, stop=type(exc).__name__ + ":" + str(exc),
                execution_failure_class="IMPLEMENTATION_EXCEPTION",
                rhs_evaluations_status="NOT_AVAILABLE_DUE_TO_IMPLEMENTATION_EXCEPTION")
        result_store.write_record(manifest, record); completed += 1
        if diagnostic_run is not None and key_observer is not None:
            try:
                diagnostic_run.register(key_id, record["status"], key_observer.terminal_record(record))
            except BaseException as exc:
                diagnostic_run.fail(key_id, "SERIALIZATION_FAILURE", type(exc).__name__ + ":" + str(exc))
                if diagnostic_config.required:
                    infrastructure_failure = True
                    break
        if record.get("execution_failure_class") in ("IMPLEMENTATION_EXCEPTION", "SHARED_INFRASTRUCTURE_FAILURE"):
            infrastructure_failure = True
            break
    store_summary = summarize(result_store)
    remaining = plan["total_keys"] - completed - reused
    result_store.finish_run(manifest, store_summary,
        status="INFRASTRUCTURE_FAILURE" if infrastructure_failure else None,
        unattempted_keys=remaining if infrastructure_failure else None)
    result = {"planned": plan["total_keys"], "completed_now": completed, "reused": reused,
            "remaining": remaining, "backend": context.backend,
            "infrastructure_failures": 1 if infrastructure_failure else 0,
            "status_counts": store_summary["statuses"]}
    if diagnostic_run is not None:
        try:
            result["diagnostic_health"] = diagnostic_run.finalize()[0]
        except BaseException as exc:
            diagnostic_run.fail("RUN_FINALIZATION", "HEALTH_FINALIZATION_FAILURE",
                type(exc).__name__ + ":" + str(exc))
            result["diagnostic_health"] = diagnostic_run.finalize_objects()[0]
            if diagnostic_config.required:
                result["diagnostic_administrative_status"] = obs_001.ADMIN_FAILURE
    return result


def execute_authorized_graph(*, execution_authority_path: Path, output_root: Path,
                             diagnostic_config: obs_001.DiagnosticConfig | None = None) -> dict:
    store = CanonicalStore.load()
    context = validate_execution_authority(execution_authority_path, output_root, store)
    return _execute_graph(store, ResultStore(output_root, store), context,
                          diagnostic_config=diagnostic_config)


def _execute_graph_synthetic_test_only(store: CanonicalStore, result_store: ResultStore,
        context: _ValidatedExecutionContext, *, interrupt_after: int | None = None,
        test_runner: Callable[[dict, str, _ValidatedExecutionContext], dict] | None = None) -> dict:
    """Exercise orchestration only; cannot accept or emit real/diagnostic evidence."""
    if (not isinstance(context, _ValidatedExecutionContext) or context.backend != SYNTHETIC_BACKEND or
            context.evidence_kind != SYNTHETIC_BACKEND):
        raise ValueError("SYNTHETIC_TEST_ONLY_CONTEXT_REQUIRED")
    runner = test_runner or synthetic_backend_record
    plan = build_plan(store); completed = reused = 0
    manifest = result_store.begin_run(context, plan["total_keys"])
    for case_id, profile in plan["keys"]:
        if result_store.reusable(manifest, case_id, profile):
            reused += 1; continue
        if interrupt_after is not None and completed >= interrupt_after:
            break
        record = runner(store.row(case_id), profile, context)
        if record.get("evidence_kind") != SYNTHETIC_BACKEND:
            raise ValueError("SYNTHETIC_RUNNER_EVIDENCE_KIND_VIOLATION")
        result_store.write_record(manifest, record); completed += 1
    store_summary = summarize(result_store)
    result_store.finish_run(manifest, store_summary)
    return {"planned": plan["total_keys"], "completed_now": completed, "reused": reused,
            "remaining": plan["total_keys"] - completed - reused, "backend": context.backend,
            "status_counts": store_summary["statuses"]}


def _load_pilot_allowlist(path: Path, store: CanonicalStore) -> tuple[list[tuple[str, str]], str]:
    if not path.is_absolute() or not path.is_file():
        raise ValueError("PILOT_ALLOWLIST_ABSOLUTE_FILE_REQUIRED")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {"schema", "keys"} or payload["schema"] != PILOT_ALLOWLIST_SCHEMA:
        raise ValueError("MALFORMED_PILOT_ALLOWLIST")
    keys = []
    for item in payload["keys"]:
        if not isinstance(item, dict) or set(item) != {"case_id", "numerical_profile"}:
            raise ValueError("MALFORMED_PILOT_ALLOWLIST_KEY")
        row = store.row(item["case_id"]); profile = item["numerical_profile"]
        profiles = protocol.STATIC_NUMERICAL_PROFILES if row["pressure_mode"] == "PRESCRIBED_STATIC" else protocol.DYNAMIC_NUMERICAL_PROFILES
        if profile not in profiles:
            raise ValueError("PILOT_PROFILE_NOT_AUTHORIZED")
        keys.append((row["case_id"], profile))
    if len(keys) != len(set(keys)):
        raise ValueError("DUPLICATE_PILOT_KEY")
    keys = sorted(keys)
    digest = sha256_bytes(canonical_json({"schema": PILOT_ALLOWLIST_SCHEMA,
                                          "keys": [list(key) for key in keys]}).encode())
    return keys, digest


def pilot_plan(pilot_authority_path: Path, allowlist_path: Path, output_root: Path,
               *, store: CanonicalStore | None = None, allow_synthetic_fixture: bool = False) -> dict:
    store = store or CanonicalStore.load(); output = validate_external_output_root(output_root)
    keys, allowlist_hash = _load_pilot_allowlist(allowlist_path, store)
    if not pilot_authority_path.is_absolute() or not pilot_authority_path.is_file():
        raise ValueError("PILOT_AUTHORITY_ABSOLUTE_FILE_REQUIRED")
    authority = json.loads(pilot_authority_path.read_text(encoding="utf-8"))
    required = {"schema", "authorization_id", "authorized_head", "authorized_tree",
        "matrix_semantic_sha256", "protocol_artifact_sha256", "executor_source_sha256", "backend",
        "allowed_output_root", "allowlist_sha256", "maximum_case_count", "evidence_kind", "reuse_policy",
        "allowed_execution_mode"}
    if set(authority) != required or authority["schema"] != PILOT_AUTHORITY_SCHEMA:
        raise ValueError("MALFORMED_PILOT_AUTHORITY")
    if authority["allowed_execution_mode"] != "DIAGNOSTIC_TIMING_PILOT" or authority["evidence_kind"] != PILOT_EVIDENCE:
        raise ValueError("PILOT_MODE_OR_EVIDENCE_NOT_AUTHORIZED")
    if authority["reuse_policy"] != "DISABLED": raise ValueError("PILOT_REUSE_MUST_BE_DISABLED")
    if authority["backend"] != REAL_BACKEND and not (allow_synthetic_fixture and authority["backend"] == SYNTHETIC_BACKEND):
        raise ValueError("PILOT_BACKEND_NOT_AUTHORIZED")
    expected = {"authorized_head": git_value("rev-parse", "HEAD"),
        "authorized_tree": git_value("rev-parse", "HEAD^{tree}"), "matrix_semantic_sha256": store.matrix_hash,
        "protocol_artifact_sha256": store.protocol_hash, "executor_source_sha256": sha256_file(Path(__file__)),
        "allowed_output_root": str(output), "allowlist_sha256": allowlist_hash}
    for key, value in expected.items():
        if authority[key] != value: raise ValueError("PILOT_AUTHORITY_MISMATCH:" + key)
    if not allow_synthetic_fixture and git_value("status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("PILOT_WORKTREE_NOT_CLEAN")
    if (type(authority["maximum_case_count"]) is not int or authority["maximum_case_count"] < 0 or
            authority["maximum_case_count"] > 64 or len(keys) > authority["maximum_case_count"]):
        raise ValueError("PILOT_MAXIMUM_CASE_COUNT_EXCEEDED")
    return {"schema": "ewp.sci_lc_001a.pilot_plan.v1", "keys": [list(key) for key in keys],
        "key_count": len(keys), "allowlist_sha256": allowlist_hash, "backend": authority["backend"],
        "reuse": "DISABLED", "evidence_kind": PILOT_EVIDENCE, "solver_calls": 0,
        "authority": authority}


def _execute_canonical_pilot_case(store: CanonicalStore, row: Mapping[str, object], profile: str,
                                  context: _ValidatedExecutionContext) -> dict:
    """Measure one canonical calculation and retain diagnostic-only information."""
    if (not isinstance(context, _ValidatedExecutionContext) or context.backend != REAL_BACKEND or
            context.evidence_kind != PILOT_EVIDENCE or
            context.execution_mode != "DIAGNOSTIC_TIMING_PILOT"):
        raise ValueError("VALIDATED_DIAGNOSTIC_PILOT_CONTEXT_REQUIRED")
    started_at_utc = utc_now()
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    try:
        outcome = _execute_canonical_case(store, row, profile, context)
    except Exception as exc:
        wall_end = time.perf_counter_ns(); cpu_end = time.process_time_ns()
        return {"status": "FAILED", "started_at_utc": started_at_utc,
                "case_wall_time_ns": wall_end - wall_start,
                "case_cpu_time_ns": cpu_end - cpu_start, "solver_status": "EXCEPTION",
                "failure_disposition": type(exc).__name__ + ":" + str(exc),
                "rhs_evaluations": None,
                "rhs_evaluations_status": "NOT_AVAILABLE_DUE_TO_IMPLEMENTATION_EXCEPTION",
                "execution_failure_class": "IMPLEMENTATION_EXCEPTION",
                "linear_solve_status": "NOT_AVAILABLE",
                "stop_disposition": None, "canonical_outcome_serialized_bytes": 0}
    wall_end = time.perf_counter_ns(); cpu_end = time.process_time_ns()
    encoded_size = len(canonical_json(outcome).encode("utf-8"))
    return {"status": outcome["status"], "started_at_utc": started_at_utc,
            "case_wall_time_ns": wall_end - wall_start,
            "case_cpu_time_ns": cpu_end - cpu_start,
            "solver_status": outcome.get("status", "FAILED"),
            "rhs_evaluations": outcome.get("rhs_evaluations"),
            "rhs_evaluations_status": outcome.get("rhs_evaluations_status", "MEASURED"),
            "execution_failure_class": outcome.get("execution_failure_class", "NUMERICAL_CASE_DISPOSITION"),
            "linear_solve_status": outcome.get("linear_solve_status", "NOT_APPLICABLE"),
            "residual_status": outcome.get("residual_status", "NOT_AVAILABLE"),
            "stop_disposition": outcome.get("stop_disposition"),
            "canonical_outcome_serialized_bytes": encoded_size}


def execute_authorized_pilot(*, pilot_authority_path: Path, allowlist_path: Path,
                             output_root: Path) -> dict:
    output = validate_external_output_root(output_root)
    if output.exists() and any(output.iterdir()): raise ValueError("PILOT_OUTPUT_ROOT_MUST_BE_NEW_OR_EMPTY")
    plan = pilot_plan(pilot_authority_path, allowlist_path, output)
    authority = plan["authority"]
    material = {"authorization_id": authority["authorization_id"],
        "authorized_head": authority["authorized_head"], "authorized_tree": authority["authorized_tree"],
        "matrix_hash": authority["matrix_semantic_sha256"], "protocol_hash": authority["protocol_artifact_sha256"],
        "executor_identity": authority["executor_source_sha256"], "execution_mode": "DIAGNOSTIC_TIMING_PILOT",
        "backend": authority["backend"], "evidence_kind": PILOT_EVIDENCE, "output_root": str(output)}
    context = _ValidatedExecutionContext(**material,
        run_id=sha256_bytes(canonical_json(material).encode())[:24])
    store = CanonicalStore.load(); results = ResultStore(output, store)
    manifest = results.begin_run(context, plan["key_count"])
    infrastructure_failure = False
    for case_id, profile in map(tuple, plan["keys"]):
        diagnostic = _execute_canonical_pilot_case(store, store.row(case_id), profile, context)
        if not isinstance(diagnostic, dict) or "status" not in diagnostic:
            raise ValueError("INVALID_PILOT_DIAGNOSTIC_RESULT")
        record = _case_record(store.row(case_id), profile, context, diagnostic["status"],
            {"diagnostic_timing_only": {key: value for key, value in diagnostic.items() if key != "status"}},
            synthetic=False, started=diagnostic["started_at_utc"],
            nfev=diagnostic.get("rhs_evaluations"), stop=diagnostic.get("stop_disposition"),
            execution_failure_class=diagnostic.get("execution_failure_class", "NUMERICAL_CASE_DISPOSITION"),
            rhs_evaluations_status=diagnostic.get("rhs_evaluations_status"))
        results.write_record(manifest, record)
        if record["execution_failure_class"] in ("IMPLEMENTATION_EXCEPTION", "SHARED_INFRASTRUCTURE_FAILURE"):
            infrastructure_failure = True
            break
    summary = summarize(results)
    remaining = plan["key_count"] - summary["records"]
    results.finish_run(manifest, summary,
        status="INFRASTRUCTURE_FAILURE" if infrastructure_failure else None,
        unattempted_keys=remaining if infrastructure_failure else None)
    return {"planned": plan["key_count"], "completed": summary["records"],
            "remaining": remaining, "infrastructure_failures": 1 if infrastructure_failure else 0,
            "evidence_kind": PILOT_EVIDENCE, "reuse": "DISABLED"}


def summarize(result_store: ResultStore) -> dict:
    manifest = result_store.load_manifest() if result_store.manifest_path.exists() else None
    counts = {status: 0 for status in RESULT_STATUSES}; evidence = set(); records = 0
    failure_classes = {}; projection_eligible = 0; complete_horizon_samples = 0
    initial_condition_scopes: dict[str, int] = {}
    dynamic_initial_state_variants: dict[str, int] = {}
    for path in sorted((result_store.root / "cases").glob("*/*.json")) if (result_store.root / "cases").exists() else []:
        if manifest is None:
            raise ValueError("SUMMARY_REQUIRES_RUN_MANIFEST")
        record = result_store.read_bound_record(manifest, path.parent.name, path.stem)
        counts[record["status"]] += 1; evidence.add(record["evidence_kind"]); records += 1
        failure_class = record.get("execution_failure_class", "NUMERICAL_CASE_DISPOSITION")
        failure_classes[failure_class] = failure_classes.get(failure_class, 0) + 1
        for field, counts_by_value in (("initial_condition_scope", initial_condition_scopes),
                ("dynamic_initial_state_variant", dynamic_initial_state_variants)):
            value = str(record[field])
            counts_by_value[value] = counts_by_value.get(value, 0) + 1
        if failure_class not in ("IMPLEMENTATION_EXCEPTION", "SHARED_INFRASTRUCTURE_FAILURE"):
            projection_eligible += 1
            if record["status"] == "COMPLETE": complete_horizon_samples += 1
    return {"records": records, "statuses": counts, "failure_classes": failure_classes,
            "projection_eligible_records": projection_eligible,
            "complete_horizon_projection_records": complete_horizon_samples,
            "evidence_kinds": sorted(evidence),
            "stage_a_architecture_id": protocol.ARCHITECTURE_ID,
            "initial_condition_scopes": initial_condition_scopes,
            "dynamic_initial_state_variants": dynamic_initial_state_variants,
            "initial_condition_robustness": protocol.NOT_ADJUDICATED_STAGE_A,
            "bistability_status": protocol.NOT_ADJUDICATED_STAGE_A,
            "initial_condition_dependence_branch": protocol.INITIAL_CONDITION_BRANCH_STATUS,
            "solver_calls": 0}


def _cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True,
                        choices=("plan", "validate", "execute", "summarize", "classify",
                                 "pilot-plan", "pilot-execute"))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--execution-authority", type=Path)
    parser.add_argument("--pilot-authority", type=Path)
    parser.add_argument("--pilot-allowlist", type=Path)
    parser.add_argument("--multiplier-diagnostics-config", type=Path)
    return parser


def _load_multiplier_diagnostics_config(path: Path | None) -> obs_001.DiagnosticConfig:
    if path is None:
        return obs_001.DiagnosticConfig.from_field(None)
    if not path.is_absolute() or not path.is_file():
        raise ValueError("MULTIPLIER_DIAGNOSTICS_CONFIG_ABSOLUTE_FILE_REQUIRED")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {"multiplier_diagnostics"}:
        raise ValueError("MULTIPLIER_DIAGNOSTICS_SINGLE_FIELD_REQUIRED")
    return obs_001.DiagnosticConfig.from_field(payload["multiplier_diagnostics"])


def main(argv: list[str] | None = None) -> int:
    args = _cli().parse_args(argv)
    diagnostic_config = _load_multiplier_diagnostics_config(args.multiplier_diagnostics_config)
    store = CanonicalStore.load(); plan = build_plan(store)
    if args.mode == "plan":
        print(json.dumps({key: value for key, value in plan.items() if key != "keys"}, indent=2)); return 0
    if args.output_root is None:
        raise SystemExit("--output-root is required for validate/execute/summarize/pilot modes")
    output = validate_external_output_root(args.output_root)
    if args.mode == "validate":
        existing = summarize(ResultStore(output, store)) if (output / "RUN_MANIFEST.json").exists() else None
        print(json.dumps({"status": "PASS", "output_root": str(output), "solver_calls": 0,
                          "total_keys": plan["total_keys"], "existing_store": existing}, indent=2)); return 0
    result_store = ResultStore(output, store)
    if args.mode == "summarize":
        print(json.dumps(summarize(result_store), indent=2)); return 0
    if args.mode == "classify":
        print(json.dumps(export_stage_a_classifications(store, result_store), indent=2)); return 0
    if args.mode in ("pilot-plan", "pilot-execute"):
        if args.pilot_authority is None or args.pilot_allowlist is None:
            raise SystemExit("--pilot-authority and --pilot-allowlist are required")
        if args.mode == "pilot-plan":
            planned = pilot_plan(args.pilot_authority, args.pilot_allowlist, output)
            print(json.dumps({key: value for key, value in planned.items() if key != "authority"}, indent=2)); return 0
        execute_authorized_pilot(pilot_authority_path=args.pilot_authority,
                                 allowlist_path=args.pilot_allowlist, output_root=output)
        return 0
    if args.execution_authority is None:
        raise SystemExit("--execution-authority is required for execute")
    summary = execute_authorized_graph(execution_authority_path=args.execution_authority,
                                       output_root=output, diagnostic_config=diagnostic_config)
    print(json.dumps(summary, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
