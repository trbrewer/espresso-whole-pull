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
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import sci_lc_001a_protocol as protocol  # noqa: E402

ROOT = SCRIPT_DIR.parent
MATRIX_PATH = ROOT / "validation/cases/sci_lc_001a/SCI_LC_001A_PARAMETER_MATRIX.json"
PROTOCOL_PATH = ROOT / "validation/cases/sci_lc_001a/SCI_LC_001A_PROTOCOL.json"
AUTHORITY_SCHEMA = "ewp.sci_lc_001a.execution_authority.v1"
PILOT_AUTHORITY_SCHEMA = "ewp.sci_lc_001a.pilot_authority.v1"
PILOT_ALLOWLIST_SCHEMA = "ewp.sci_lc_001a.pilot_allowlist.v1"
RUN_SCHEMA = "ewp.sci_lc_001a.run_manifest.v1"
CASE_SCHEMA = "ewp.sci_lc_001a.case_profile_result.v1"
PLAN_SCHEMA = "ewp.sci_lc_001a.execution_plan.v1"
RESULT_STATUSES = ("NOT_STARTED", "RUNNING", "COMPLETE", "STOPPED", "CAPPED",
                   "NUMERICALLY_UNRESOLVED", "AUTHORITY_INVALID", "FAILED", "INTERRUPTED")
REAL_BACKEND = "REAL_STAGE_A"
SYNTHETIC_BACKEND = "SYNTHETIC_TEST_ONLY"
PILOT_EVIDENCE = "DIAGNOSTIC_TIMING_ONLY"
PUBLIC_API = ("CanonicalStore", "ResultStore", "build_plan", "validate_execution_authority",
              "execute_authorized_graph", "pilot_plan", "execute_authorized_pilot",
              "evaluate_gain_evidence", "evaluate_uncertainty_evidence",
              "classify_stage_a_evidence", "main")
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
                "execution_mode", "backend", "evidence_kind", "output_root")
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
                    "task_count": task_count, "run_id": context.run_id}
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

    def finish_run(self, manifest: dict, summary: dict) -> None:
        final = {**manifest, "ended_at_utc": utc_now(), "status_counts": summary["statuses"],
                 "status": "COMPLETE" if summary["records"] == manifest["task_count"] else "INTERRUPTED"}
        atomic_write_json(self.manifest_path, final)

    def write_record(self, manifest: dict, record: dict) -> None:
        if manifest.get("run_manifest_identity_sha256") != self.manifest_identity(manifest):
            raise ValueError("RUN_MANIFEST_IDENTITY_MISMATCH")
        if record.get("status") not in RESULT_STATUSES:
            raise ValueError("INVALID_RESULT_STATUS")
        row = self.canonical.row(record["case_id"])
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
                 *, synthetic: bool, started: str, nfev: int = 0,
                 stop: str | None = None, linear_status: str = "NOT_APPLICABLE") -> dict:
    return {"schema": CASE_SCHEMA, "case_id": row["case_id"], "profile": profile,
            "row_hash": row["row_sha256"], "role": row["case_role"],
            "boundary_mode": row["pressure_mode"], "authorization_id": context.authorization_id,
            "authorized_head": context.authorized_head, "authorized_tree": context.authorized_tree,
            "status": status, "started_at_utc": started, "ended_at_utc": utc_now(),
            "solver_settings": profile, "rhs_evaluations": nfev, "stop_disposition": stop,
            "linear_solve_status": linear_status, "residual_status": "PASS" if status == "COMPLETE" else status,
            "metric_primitives": metrics, "evidence_kind": context.evidence_kind}


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


def _dynamic_rhs_core(row: dict, profile: str, tau: float, state: list[float], base: dict,
                      storage: list[float], startup: list[float]) -> tuple[list[float], dict]:
    """Pure frozen RHS and diagnostic primitives; does not increment solver counters."""
    n = row["sector_count"]; machine = row["pressure_mode"] == "MACHINE_COUPLED"
    evolving = row["resistance_evolution_law"] != "NO_EVOLUTION"
    pressures = state[:n]; upstream = state[n] if machine else None
    x = state[n + (1 if machine else 0):]
    evolved = _evolved_primitives(row, base, x)
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
                          solve_ivp_impl: Callable | None = None) -> dict:
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
        return _dynamic_rhs_core(row, profile, tau, state, base, storage, startup)[0]

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
                                events=events or None, **settings)
    except ValueError as exc:
        status = "CAPPED" if "MAX_RHS" in str(exc) else "STOPPED"
        return _case_record(row, profile, context, status, {}, synthetic=synthetic,
                            started=started, nfev=nfev, stop=str(exc))
    if not solved.success or solved.sol is None:
        return _case_record(row, profile, context, "FAILED", {}, synthetic=synthetic,
                            started=started, nfev=nfev, stop=str(solved.message))
    if hasattr(solved, "nfev") and solved.nfev != nfev:
        return _case_record(row, profile, context, "FAILED", {}, synthetic=synthetic,
                            started=started, nfev=nfev, stop="RHS_COUNTER_NFEV_MISMATCH")
    located = []
    for index, times in enumerate(getattr(solved, "t_events", ())):
        for event_index, tau_event in enumerate(times):
            states = getattr(solved, "y_events", ())[index]
            event_state = states[event_index]
            sector = index // 2; bound = "LOWER_BOUND" if index % 2 == 0 else "UPPER_BOUND"
            x_value = event_state[n + (1 if machine else 0) + sector]
            target = .25 if bound == "LOWER_BOUND" else 4.
            if abs(math.exp(beta * x_value) - target) > protocol.EVENT_ROOT_VALUE_ATOL:
                return _case_record(row, profile, context, "FAILED", {}, synthetic=synthetic,
                    started=started, nfev=nfev, stop="EVENT_ROOT_STATE_INCONSISTENT_WITH_BOUNDARY")
            located.append({"tau": float(tau_event), "bound": bound, "sector_index": sector})
    if located:
        selected = protocol.select_multiplier_event(located)
        return _case_record(row, profile, context, "STOPPED", {"terminal_tau": selected["tau"]}, synthetic=synthetic,
                            started=started, nfev=nfev, stop=protocol.MULTIPLIER_STOP + ":" +
                            canonical_json(selected))
    sample1001 = solved.sol([i / 1000 for i in range(1001)])
    final_p = tuple(float(sample1001[i][-1]) for i in range(n))
    final_state = [float(sample1001[i][-1]) for i in range(len(sample1001))]
    final_x = final_state[n + (1 if machine else 0):]
    final_evolved = _evolved_primitives(row, base, final_x)
    aux = {"gd": [1 / x for x in final_evolved["R_d_i"]], "ge": float(row["lateral_edge_conductance_G_edge"])}
    metrics = _flow_metrics(final_p, aux, row)
    h1001, integral1001 = _dynamic_hq_grid(row, base, storage, startup, solved.sol, 1001)
    h2001, integral2001 = _dynamic_hq_grid(row, base, storage, startup, solved.sol, 2001)
    metrics.update({"H_q_endpoint": metrics["H_q"], "H_q_integral_1001": integral1001,
        "H_q_integral_2001": integral2001, "H_q_grid_1001_count": len(h1001),
        "H_q_grid_2001_count": len(h2001), "final_multipliers": final_evolved["multipliers"],
        "final_R_u_i": final_evolved["R_u_i"], "final_R_d_i": final_evolved["R_d_i"],
        "final_G_d_i": aux["gd"]})
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
        initial_condition_disagreement: bool = False, sector_disagreement: bool = False,
        model_form_disagreement: bool = False, metrics: tuple[tuple[float, float], tuple[float, float]] | None = None) -> str:
    """Pure precedence engine. Tests use it only with synthetic scalar fixtures."""
    if authority_invalid: return "AUTHORITY_OR_ARTIFACT_INVALID"
    if structural_identity: return "ANALYTICAL_STRUCTURAL_IDENTITY"
    if numerical_unresolved or metrics is None: return "NUMERICALLY_UNRESOLVED"
    if initial_condition_disagreement: return "INITIAL_CONDITION_DEPENDENT_OR_BISTABLE"
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
        return {"classification": "ANALYTICAL_STRUCTURAL_IDENTITY",
                "numerical_control_status": "SEPARATELY_RECORDED"}
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
    return {"classification": classification, "metrics": dict(zip(metric_names, evidence)),
            "precedence": list(protocol_spec_precedence())}


def protocol_spec_precedence() -> tuple[str, ...]:
    return ("AUTHORITY_OR_ARTIFACT_INVALID", "ANALYTICAL_STRUCTURAL_IDENTITY", "NUMERICALLY_UNRESOLVED",
        "INITIAL_CONDITION_DEPENDENT_OR_BISTABLE", "MODEL_FORM_OR_SECTOR_RESOLUTION_DISAGREEMENT",
        "METRIC_DISAGREEMENT", "NEAR_THRESHOLD_TRANSITION", "LATERAL_EQUALIZATION",
        "HETEROGENEITY_AMPLIFIES", "HETEROGENEITY_PERSISTS")


def synthetic_backend_record(row: dict, profile: str, context: _ValidatedExecutionContext) -> dict:
    """Deterministic orchestration fixture; it does not solve a matrix row."""
    value = 1.0 + (int(hashlib.sha256(f"{row['case_id']}:{profile}".encode()).hexdigest()[:6], 16) % 1000) / 1e6
    metrics = {"H_q": value, "H_q_static": value, "A_seeded": value + .01,
               "H_q_endpoint": value + .02, "H_q_integral_1001": value + .03,
               "H_q_integral_2001": value + .030001, "Q_total": 1.,
               "sector_outlet_flow": [], "sector_flow_fraction": []}
    return _case_record(row, profile, context, "COMPLETE", metrics, synthetic=True,
                        started="SYNTHETIC_DETERMINISTIC", nfev=0)


def _execute_graph(store: CanonicalStore, result_store: ResultStore, context: _ValidatedExecutionContext,
                  *, interrupt_after: int | None = None,
                  real_launcher: Callable = None) -> dict:
    if not isinstance(context, _ValidatedExecutionContext):
        raise ValueError("VALIDATED_EXECUTION_CONTEXT_REQUIRED")
    plan = build_plan(store); completed = reused = 0
    manifest = result_store.begin_run(context, plan["total_keys"])
    if context.backend == REAL_BACKEND and real_launcher is None:
        real_launcher = lambda row, profile: (_execute_static_case(store, row["case_id"], profile, context)
            if row["pressure_mode"] == "PRESCRIBED_STATIC" else
            _execute_dynamic_case(store, row["case_id"], profile, context))
    for case_id, profile in plan["keys"]:
        if result_store.reusable(manifest, case_id, profile):
            reused += 1; continue
        if interrupt_after is not None and completed >= interrupt_after:
            break
        row = store.row(case_id)
        record = (synthetic_backend_record(row, profile, context) if context.backend == SYNTHETIC_BACKEND
                  else real_launcher(row, profile))
        result_store.write_record(manifest, record); completed += 1
    store_summary = summarize(result_store)
    result_store.finish_run(manifest, store_summary)
    return {"planned": plan["total_keys"], "completed_now": completed, "reused": reused,
            "remaining": plan["total_keys"] - completed - reused, "backend": context.backend,
            "status_counts": store_summary["statuses"]}


def execute_authorized_graph(execution_authority_path: Path, output_root: Path,
                             *, real_launcher: Callable | None = None) -> dict:
    store = CanonicalStore.load()
    context = validate_execution_authority(execution_authority_path, output_root, store)
    return _execute_graph(store, ResultStore(output_root, store), context, real_launcher=real_launcher)


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


def execute_authorized_pilot(pilot_authority_path: Path, allowlist_path: Path, output_root: Path,
                             *, real_launcher: Callable | None = None) -> dict:
    output = validate_external_output_root(output_root)
    if output.exists() and any(output.iterdir()): raise ValueError("PILOT_OUTPUT_ROOT_MUST_BE_NEW_OR_EMPTY")
    plan = pilot_plan(pilot_authority_path, allowlist_path, output)
    if real_launcher is None:
        raise ValueError("REAL_PILOT_LAUNCHER_NOT_BOUND")
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
    for case_id, profile in map(tuple, plan["keys"]):
        diagnostic = real_launcher(store.row(case_id), profile, context)
        if not isinstance(diagnostic, dict) or "status" not in diagnostic:
            raise ValueError("INVALID_PILOT_DIAGNOSTIC_RESULT")
        record = _case_record(store.row(case_id), profile, context, diagnostic["status"],
            {"diagnostic_timing_only": {key: value for key, value in diagnostic.items() if key != "status"}},
            synthetic=False, started=diagnostic.get("started_at_utc", utc_now()),
            nfev=int(diagnostic.get("rhs_evaluations", 0)), stop=diagnostic.get("stop_disposition"))
        results.write_record(manifest, record)
    summary = summarize(results); results.finish_run(manifest, summary)
    return {"planned": plan["key_count"], "completed": summary["records"],
            "evidence_kind": PILOT_EVIDENCE, "reuse": "DISABLED"}


def summarize(result_store: ResultStore) -> dict:
    manifest = result_store.load_manifest() if result_store.manifest_path.exists() else None
    counts = {status: 0 for status in RESULT_STATUSES}; evidence = set(); records = 0
    for path in sorted((result_store.root / "cases").glob("*/*.json")) if (result_store.root / "cases").exists() else []:
        if manifest is None:
            raise ValueError("SUMMARY_REQUIRES_RUN_MANIFEST")
        record = result_store.read_bound_record(manifest, path.parent.name, path.stem)
        counts[record["status"]] += 1; evidence.add(record["evidence_kind"]); records += 1
    return {"records": records, "statuses": counts, "evidence_kinds": sorted(evidence), "solver_calls": 0}


def _cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True,
                        choices=("plan", "validate", "execute", "summarize", "pilot-plan", "pilot-execute"))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--execution-authority", type=Path)
    parser.add_argument("--pilot-authority", type=Path)
    parser.add_argument("--pilot-allowlist", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _cli().parse_args(argv); store = CanonicalStore.load(); plan = build_plan(store)
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
    if args.mode in ("pilot-plan", "pilot-execute"):
        if args.pilot_authority is None or args.pilot_allowlist is None:
            raise SystemExit("--pilot-authority and --pilot-allowlist are required")
        if args.mode == "pilot-plan":
            planned = pilot_plan(args.pilot_authority, args.pilot_allowlist, output)
            print(json.dumps({key: value for key, value in planned.items() if key != "authority"}, indent=2)); return 0
        execute_authorized_pilot(args.pilot_authority, args.pilot_allowlist, output)
        return 0
    if args.execution_authority is None:
        raise SystemExit("--execution-authority is required for execute")
    summary = execute_authorized_graph(args.execution_authority, output)
    print(json.dumps(summary, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
