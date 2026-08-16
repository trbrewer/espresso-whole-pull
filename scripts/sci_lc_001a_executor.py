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
RUN_SCHEMA = "ewp.sci_lc_001a.run_manifest.v1"
CASE_SCHEMA = "ewp.sci_lc_001a.case_profile_result.v1"
PLAN_SCHEMA = "ewp.sci_lc_001a.execution_plan.v1"
RESULT_STATUSES = ("NOT_STARTED", "RUNNING", "COMPLETE", "STOPPED", "CAPPED",
                   "NUMERICALLY_UNRESOLVED", "AUTHORITY_INVALID", "FAILED", "INTERRUPTED")
REAL_BACKEND = "REAL_STAGE_A"
SYNTHETIC_BACKEND = "SYNTHETIC_TEST_ONLY"
PUBLIC_API = ("CanonicalStore", "ResultStore", "build_plan", "validate_execution_authority",
              "evaluate_gain_evidence", "evaluate_uncertainty_evidence",
              "classify_stage_a_evidence", "execute_static_case", "execute_dynamic_case", "main")
__all__ = PUBLIC_API


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
                                 allow_synthetic_fixture: bool = False) -> dict:
    output_root = validate_external_output_root(output_root)
    if not path.is_absolute() or not path.is_file():
        raise ValueError("EXECUTION_AUTHORITY_ABSOLUTE_FILE_REQUIRED")
    authority = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema", "authorization_id", "authorized_head", "authorized_tree",
                "matrix_semantic_sha256", "protocol_artifact_sha256", "allowed_execution_mode",
                "allowed_output_root", "backend"}
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
    }
    for key, expected in checks.items():
        if authority[key] != expected:
            raise ValueError("EXECUTION_AUTHORITY_MISMATCH:" + key)
    if git_value("status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("EXECUTION_WORKTREE_NOT_CLEAN")
    return authority


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

    @property
    def manifest_path(self) -> Path:
        return self.root / "RUN_MANIFEST.json"

    def begin_run(self, authority: dict, backend: str, task_count: int) -> dict:
        expected = {"authorization_id": authority["authorization_id"],
                    "git_head": authority["authorized_head"], "git_tree": authority["authorized_tree"],
                    "matrix_semantic_sha256": self.canonical.matrix_hash,
                    "protocol_sha256": self.canonical.protocol_hash,
                    "executor_source_sha256": sha256_file(Path(__file__)), "output_root": str(self.root),
                    "backend": backend, "task_count": task_count}
        if self.manifest_path.exists():
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if any(manifest.get(key) != value for key, value in expected.items()):
                raise ValueError("RESUME_MANIFEST_AUTHORITY_MISMATCH")
            return manifest
        manifest = {"schema": RUN_SCHEMA, "run_id": sha256_bytes(canonical_json(expected).encode())[:24],
                    **expected, "branch": git_value("branch", "--show-current"),
                    "started_at_utc": utc_now(), "ended_at_utc": None,
                    "status_counts": {status: 0 for status in RESULT_STATUSES},
                    "status": "RUNNING", "synthetic_evidence": backend == SYNTHETIC_BACKEND}
        atomic_write_json(self.manifest_path, manifest)
        return manifest

    def finish_run(self, manifest: dict, summary: dict) -> None:
        final = {**manifest, "ended_at_utc": utc_now(), "status_counts": summary["statuses"],
                 "status": "COMPLETE" if summary["records"] == manifest["task_count"] else "INTERRUPTED"}
        atomic_write_json(self.manifest_path, final)

    def write_record(self, record: dict) -> None:
        if record.get("status") not in RESULT_STATUSES:
            raise ValueError("INVALID_RESULT_STATUS")
        row = self.canonical.row(record["case_id"])
        if record["profile"] not in (protocol.STATIC_NUMERICAL_PROFILES if
                row["pressure_mode"] == "PRESCRIBED_STATIC" else protocol.DYNAMIC_NUMERICAL_PROFILES):
            raise ValueError("PROFILE_NOT_AUTHORIZED_FOR_ROW")
        body = dict(record); body.pop("output_checksum", None)
        record = {**body, "output_checksum": sha256_bytes(canonical_json(body).encode())}
        atomic_write_json(self.record_path(record["case_id"], record["profile"]), record)

    def read_record(self, case_id: str, profile: str) -> dict:
        record = json.loads(self.record_path(case_id, profile).read_text(encoding="utf-8"))
        body = dict(record); checksum = body.pop("output_checksum", None)
        if checksum != sha256_bytes(canonical_json(body).encode()):
            raise ValueError("RESULT_RECORD_CHECKSUM_MISMATCH")
        row = self.canonical.row(case_id)
        if record["row_hash"] != row["row_sha256"] or record["profile"] != profile:
            raise ValueError("RESULT_RECORD_CANONICAL_IDENTITY_MISMATCH")
        return record

    def reusable(self, case_id: str, profile: str) -> bool:
        try:
            return self.read_record(case_id, profile)["status"] in (
                "COMPLETE", "STOPPED", "CAPPED", "NUMERICALLY_UNRESOLVED")
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            return False


def _case_record(row: dict, profile: str, authority: dict, status: str, metrics: dict,
                 *, synthetic: bool, started: str, nfev: int = 0,
                 stop: str | None = None, linear_status: str = "NOT_APPLICABLE") -> dict:
    return {"schema": CASE_SCHEMA, "case_id": row["case_id"], "profile": profile,
            "row_hash": row["row_sha256"], "role": row["case_role"],
            "boundary_mode": row["pressure_mode"], "authorization_id": authority["authorization_id"],
            "authorized_head": authority["authorized_head"], "authorized_tree": authority["authorized_tree"],
            "status": status, "started_at_utc": started, "ended_at_utc": utc_now(),
            "solver_settings": profile, "rhs_evaluations": nfev, "stop_disposition": stop,
            "linear_solve_status": linear_status, "residual_status": "PASS" if status == "COMPLETE" else status,
            "metric_primitives": metrics, "evidence_kind": SYNTHETIC_BACKEND if synthetic else REAL_BACKEND}


def _static_system(row: dict) -> tuple[list[list[float]], list[float], dict]:
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


def _flow_metrics(pressure: tuple[float, ...] | list[float], auxiliaries: dict) -> dict:
    q = [g * p for g, p in zip(auxiliaries["gd"], pressure)]; total = sum(q); n = len(q)
    if not math.isfinite(total) or total <= 0:
        raise ValueError("NONPOSITIVE_OR_NONFINITE_TOTAL_FLOW")
    fractions = [value / total for value in q]
    h_q = .5 * sum(abs(value - 1 / n) for value in fractions)
    return {"H_q": h_q, "Q_total": total, "sector_outlet_flow": q,
            "sector_flow_fraction": fractions, "sampling_1001": h_q, "sampling_2001": h_q}


def execute_static_case(store: CanonicalStore, case_id: str, profile: str,
                        authority: dict, *, synthetic: bool = False) -> dict:
    row = store.row(case_id)
    if row["pressure_mode"] != "PRESCRIBED_STATIC" or profile not in protocol.STATIC_NUMERICAL_PROFILES:
        raise ValueError("STATIC_DISPATCH_MISMATCH")
    started = utc_now(); a, b, aux = _static_system(row)
    if profile == "BASE":
        solved = protocol.solve_dense_binary64(a, b)
        if solved.solver_status != "PASS":
            return _case_record(row, profile, authority, "NUMERICALLY_UNRESOLVED", {},
                                synthetic=synthetic, started=started, linear_status="FAIL")
        pressure = solved.solution; residual = solved.scaled_residual
    else:
        refined = protocol.linear_refined_state(a, b)
        pressure = refined.corrected_state; residual = refined.corrected_scaled_residual
    metrics = _flow_metrics(pressure, aux); metrics["scaled_residual"] = residual
    return _case_record(row, profile, authority, "COMPLETE", metrics, synthetic=synthetic,
                        started=started, linear_status="PASS")


def execute_dynamic_case(store: CanonicalStore, case_id: str, profile: str,
                         authority: dict, *, synthetic: bool = False,
                         solve_ivp_impl: Callable | None = None) -> dict:
    """Execute the frozen dynamic network; tests provide only trivial ODE fixtures."""
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
    theta_r = float(row["resistance_relaxation_tau_R"]) if evolving else math.inf
    beta = float(row["feedback_gain"]); sign = protocol.feedback_sign_scalar(row["feedback_sign"])
    machine = row["pressure_mode"] == "MACHINE_COUPLED"
    q_threshold = protocol.REFINED_Q_ZERO_THRESHOLD if profile == "STARTUP_REFINED" else protocol.Q_ZERO_THRESHOLD
    t_threshold = protocol.REFINED_STARTUP_TAU_MAX if profile == "STARTUP_REFINED" else protocol.STARTUP_TAU_MAX
    startup = protocol.startup_focusing(base, storage, row["pressure_mode"])
    nfev = 0

    def rhs(tau: float, state: list[float]) -> list[float]:
        nonlocal nfev
        nfev = protocol.enforce_rhs_cap(nfev)
        pressures = state[:n]; upstream = state[n] if machine else None
        x = state[n + (1 if machine else 0):]
        if evolving:
            multipliers = [math.exp(beta * value) for value in x]
            if any(not math.isfinite(value) for value in multipliers):
                raise ValueError("STOP_NONFINITE_RESISTANCE_EVOLUTION_MULTIPLIER")
            alpha = float(protocol.d(protocol.PLACEMENT_ALPHA[row["axial_placement"]]))
            residual = [value * multiplier for value, multiplier in zip(base["H_i"], multipliers)]
            evolved = {**base, "H_i": residual,
                "R_u_i": [base["R_floor"] + alpha * value for value in residual],
                "R_d_i": [base["R_floor"] + (1 - alpha) * value for value in residual]}
        else:
            evolved = base
        gu = [1 / value for value in evolved["R_u_i"]]; gd = [1 / value for value in evolved["R_d_i"]]
        if machine:
            sum_gu = sum(gu); right = upstream + .1 * sum(g * p for g, p in zip(gu, pressures))
            a = [[1 + .1 * sum_gu]]; b = [right]
            basket = (protocol.linear_refined_state(a, b).corrected_state[0] if profile == "LINEAR_REFINED"
                      else protocol.solve_dense_binary64(a, b).solution[0])
        else:
            basket = min(tau / .05, 1.)
        qu = [g * (basket - p) for g, p in zip(gu, pressures)]
        qd = [g * p for g, p in zip(gd, pressures)]
        ge = float(row["lateral_edge_conductance_G_edge"])
        dp = [(qu[i] - qd[i] - ge * (pressures[i] - pressures[(i + 1) % n])
               + ge * (pressures[(i - 1) % n] - pressures[i])) / storage[i] for i in range(n)]
        result = dp
        if machine:
            command = min(tau / .05, 1.); supply = command * max(1 - upstream, 0)
            result += [(supply - sum(qu)) / float(row["machine_compliance_C_u"])]
        if evolving:
            flow = protocol.SectorFlowVector(tuple(qd), n, "DIMENSIONAL_SECTOR_FLOW", 1., 1.)
            focusing = protocol.evolution_focusing(tau=tau, flow=flow, startup=startup,
                zero_threshold=q_threshold, startup_tau_max=t_threshold)
            result += [(sign * (value - 1) - xi) / theta_r for value, xi in zip(focusing, x)]
        return result

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
        return _case_record(row, profile, authority, status, {}, synthetic=synthetic,
                            started=started, nfev=nfev, stop=str(exc))
    if not solved.success or solved.sol is None:
        return _case_record(row, profile, authority, "FAILED", {}, synthetic=synthetic,
                            started=started, nfev=nfev, stop=str(solved.message))
    located = []
    for index, times in enumerate(getattr(solved, "t_events", ())):
        for event_index, tau_event in enumerate(times):
            states = getattr(solved, "y_events", ())[index]
            event_state = states[event_index]
            sector = index // 2; bound = "LOWER_BOUND" if index % 2 == 0 else "UPPER_BOUND"
            x_value = event_state[n + (1 if machine else 0) + sector]
            multiplier = math.exp(beta * x_value)
            derivative = rhs(float(tau_event), list(event_state))[n + (1 if machine else 0) + sector]
            disposition = protocol.multiplier_admissibility(multiplier, beta, derivative,
                "LOCATED_EVENT_ROOT", bound)
            if disposition == protocol.MULTIPLIER_STOP:
                located.append({"tau": float(tau_event), "bound": bound, "sector_index": sector})
    if located:
        selected = protocol.select_multiplier_event(located)
        return _case_record(row, profile, authority, "STOPPED", {}, synthetic=synthetic,
                            started=started, nfev=nfev, stop=protocol.MULTIPLIER_STOP + ":" +
                            canonical_json(selected))
    sample1001 = solved.sol([i / 1000 for i in range(1001)])
    sample2001 = solved.sol([i / 2000 for i in range(2001)])
    final_p = tuple(float(sample1001[i][-1]) for i in range(n))
    aux = {"gd": [1 / x for x in base["R_d_i"]], "ge": float(row["lateral_edge_conductance_G_edge"])}
    metrics = _flow_metrics(final_p, aux)
    metrics["sampling_1001"] = sum(float(sample1001[i][-1]) for i in range(n))
    metrics["sampling_2001"] = sum(float(sample2001[i][-1]) for i in range(n))
    return _case_record(row, profile, authority, "COMPLETE", metrics, synthetic=synthetic,
                        started=started, nfev=nfev)


def _metric_value(record: dict, metric_kind: str) -> float:
    if record.get("status") != "COMPLETE":
        raise ValueError("NUMERICALLY_UNRESOLVED_REQUIRED_RESULT")
    if record.get("evidence_kind") == SYNTHETIC_BACKEND:
        # Synthetic values may exercise evidence arithmetic, but never scientific classification.
        pass
    key = "H_q"
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
    active_record = results.read_record(subject_case_id, numerical_profile)
    comparator_record = results.read_record(comparator_id, numerical_profile)
    for field in ("authorization_id", "authorized_head", "authorized_tree", "evidence_kind"):
        if active_record.get(field) != comparator_record.get(field):
            raise ValueError("GAIN_RESULT_AUTHORITY_MISMATCH:" + field)
    numerator = _metric_value(active_record, metric_kind)
    denominator = _metric_value(comparator_record, metric_kind)
    internal = protocol.build_gain_record(list(canonical.rows), subject_case_id, metric_kind,
                                          numerical_profile, numerator, denominator)
    return {"subject_case_id": internal.subject_case_id, "comparator_case_id": internal.comparator_case_id,
            "metric_kind": internal.metric_kind, "profile": internal.numerical_profile,
            "gain": internal.gain, "denominator": internal.denominator,
            "denominator_floor": protocol.GAIN_DENOMINATOR_FLOOR, "status": "COMPLETE",
            "evidence_kind": active_record["evidence_kind"]}


def evaluate_uncertainty_evidence(canonical: CanonicalStore, results: ResultStore,
                                  subject_case_id: str, metric_kind: str) -> dict:
    subject = canonical.row(subject_case_id)
    static = subject["pressure_mode"] == "PRESCRIBED_STATIC"
    base = evaluate_gain_evidence(canonical, results, subject_case_id, metric_kind, "BASE")
    components: dict[str, float | str] = {name: protocol.NA for name in protocol.UNCERTAINTY_COMPONENTS}
    contract = protocol.derive_uncertainty_contract(list(canonical.rows), subject_case_id, metric_kind,
                                                     "GAIN", "COMPLETE", "BASE")
    applicable = dict(contract.applicability)
    profiles = {"u_integrator": "INTEGRATOR_REFINED", "u_startup": "STARTUP_REFINED",
                "u_linear": "LINEAR_REFINED"}
    for name, profile in profiles.items():
        if applicable[name]:
            refined = evaluate_gain_evidence(canonical, results, subject_case_id, metric_kind, profile)
            components[name] = abs(base["gain"] - refined["gain"])
    if applicable["u_sampling"]:
        active = results.read_record(subject_case_id, "BASE")
        comparator = results.read_record(subject["comparator_case_id"], "BASE")
        g1001 = active["metric_primitives"]["sampling_1001"] / comparator["metric_primitives"]["sampling_1001"]
        g2001 = active["metric_primitives"]["sampling_2001"] / comparator["metric_primitives"]["sampling_2001"]
        components["u_sampling"] = abs(g1001 - g2001)
    if applicable["u_sector"]:
        companion = protocol.sector_companion_case_id(subject, list(canonical.rows))
        components["u_sector"] = abs(base["gain"] - evaluate_gain_evidence(
            canonical, results, companion, metric_kind, "BASE")["gain"])
    total = protocol.combine_uncertainty(components, contract)
    return {"subject_case_id": subject_case_id, "metric_kind": metric_kind,
            "components": components, "total": total, "status": "COMPLETE",
            "evidence_kind": base["evidence_kind"]}


def classify_stage_a_evidence(canonical: CanonicalStore, results: ResultStore,
                              subject_case_id: str, metric_kind: str) -> dict:
    gain = evaluate_gain_evidence(canonical, results, subject_case_id, metric_kind, "BASE")
    uncertainty = evaluate_uncertainty_evidence(canonical, results, subject_case_id, metric_kind)
    if gain["evidence_kind"] != REAL_BACKEND or uncertainty["evidence_kind"] != REAL_BACKEND:
        raise ValueError("SYNTHETIC_EVIDENCE_CANNOT_CLASSIFY_SCIENTIFICALLY")
    g, u = gain["gain"], uncertainty["total"]
    if u > protocol.uncertainty_limit(g):
        return {"classification": "NUMERICALLY_UNRESOLVED", "gain": g, "uncertainty": u}
    if g + u <= .9:
        classification = "LATERAL_EQUALIZATION"
    elif g - u >= 1.1:
        classification = "HETEROGENEITY_AMPLIFIES"
    elif g - u >= .9 and g + u <= 1.1:
        classification = "HETEROGENEITY_PERSISTS"
    else:
        classification = "TRANSITION_OR_BISTABLE_REGION"
    return {"classification": classification, "gain": g, "uncertainty": u}


def synthetic_backend_record(row: dict, profile: str, authority: dict) -> dict:
    """Deterministic orchestration fixture; it does not solve a matrix row."""
    value = 1.0 + (int(hashlib.sha256(f"{row['case_id']}:{profile}".encode()).hexdigest()[:6], 16) % 1000) / 1e6
    metrics = {"H_q": value, "Q_total": 1., "sector_outlet_flow": [],
               "sector_flow_fraction": [], "sampling_1001": value, "sampling_2001": value}
    return _case_record(row, profile, authority, "COMPLETE", metrics, synthetic=True,
                        started="SYNTHETIC_DETERMINISTIC", nfev=0)


def execute_graph(store: CanonicalStore, result_store: ResultStore, authority: dict,
                  backend: str, *, interrupt_after: int | None = None,
                  real_launcher: Callable = None) -> dict:
    plan = build_plan(store); completed = reused = 0
    manifest = result_store.begin_run(authority, backend, plan["total_keys"])
    if backend == REAL_BACKEND and real_launcher is None:
        real_launcher = lambda row, profile: (execute_static_case(store, row["case_id"], profile, authority)
            if row["pressure_mode"] == "PRESCRIBED_STATIC" else
            execute_dynamic_case(store, row["case_id"], profile, authority))
    for case_id, profile in plan["keys"]:
        if result_store.reusable(case_id, profile):
            reused += 1; continue
        if interrupt_after is not None and completed >= interrupt_after:
            break
        row = store.row(case_id)
        record = (synthetic_backend_record(row, profile, authority) if backend == SYNTHETIC_BACKEND
                  else real_launcher(row, profile))
        result_store.write_record(record); completed += 1
    store_summary = summarize(result_store)
    result_store.finish_run(manifest, store_summary)
    return {"planned": plan["total_keys"], "completed_now": completed, "reused": reused,
            "remaining": plan["total_keys"] - completed - reused, "backend": backend,
            "status_counts": store_summary["statuses"]}


def summarize(result_store: ResultStore) -> dict:
    if result_store.manifest_path.exists():
        manifest = json.loads(result_store.manifest_path.read_text(encoding="utf-8"))
        if (manifest.get("matrix_semantic_sha256") != result_store.canonical.matrix_hash or
                manifest.get("protocol_sha256") != result_store.canonical.protocol_hash or
                manifest.get("output_root") != str(result_store.root)):
            raise ValueError("SUMMARY_MANIFEST_AUTHORITY_MISMATCH")
    counts = {status: 0 for status in RESULT_STATUSES}; evidence = set(); records = 0
    for path in sorted((result_store.root / "cases").glob("*/*.json")) if (result_store.root / "cases").exists() else []:
        record = result_store.read_record(path.parent.name, path.stem)
        counts[record["status"]] += 1; evidence.add(record["evidence_kind"]); records += 1
    return {"records": records, "statuses": counts, "evidence_kinds": sorted(evidence), "solver_calls": 0}


def _cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("plan", "validate", "execute", "summarize"))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--execution-authority", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _cli().parse_args(argv); store = CanonicalStore.load(); plan = build_plan(store)
    if args.mode == "plan":
        print(json.dumps({key: value for key, value in plan.items() if key != "keys"}, indent=2)); return 0
    if args.output_root is None:
        raise SystemExit("--output-root is required for validate/execute/summarize")
    output = validate_external_output_root(args.output_root)
    if args.mode == "validate":
        existing = summarize(ResultStore(output, store)) if (output / "RUN_MANIFEST.json").exists() else None
        print(json.dumps({"status": "PASS", "output_root": str(output), "solver_calls": 0,
                          "total_keys": plan["total_keys"], "existing_store": existing}, indent=2)); return 0
    result_store = ResultStore(output, store)
    if args.mode == "summarize":
        print(json.dumps(summarize(result_store), indent=2)); return 0
    if args.execution_authority is None:
        raise SystemExit("--execution-authority is required for execute")
    authority = validate_execution_authority(args.execution_authority, output, store)
    summary = execute_graph(store, result_store, authority, REAL_BACKEND)
    print(json.dumps(summary, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
