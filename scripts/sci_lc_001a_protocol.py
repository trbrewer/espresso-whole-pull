#!/usr/bin/env python3
"""Generate and verify corrected prospective SCI-LC-001A metadata.

No function in this module integrates a trajectory, launches a solver, or
classifies the scientific matrix.  Small algebra helpers exist only to make the
prospective execution contract testable without executing a matrix trajectory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/cases/sci_lc_001a"
NA = "NOT_APPLICABLE"
INFINITE = "INFINITE_NO_LATERAL_EQUALIZATION"
STATUS = "STAGE_A_BASELINE_ZERO_STATE_SCOPE_FROZEN_PENDING_INDEPENDENT_REVIEW"
TASK_ID = "SCI-LC-001A-ICA-003-STAGE-A-BASELINE-ONLY-CLASSIFICATION-SCOPE-RECONCILIATION-2026-08-17"
OWNER_METRIC_AUTHORITY_ID = "SCI-LC-001A-OWNER-METRIC-AUTHORITY-2026-08-16"
BASE_HEAD = "3e8993f56badd575f3482ea7bfa0f87d24412100"
BASE_TREE = "ba7256d8d5813c87c72a3f896c0ac5f51cd06ee0"
REVIEWED_HEAD = "c683f7722b170d049bcdf08c6bc65afd3cef20ba"
REVIEWED_TREE = "2a352bce78abbf8ad853cd7b0af6457bfea8f8fd"
C1_HEAD = "86b9ff27b8c10d5cff9c52d9cd411b0ac179620e"
C1_TREE = "2e35a5e245be9e266c747409f2420be9971963a6"
C2_HEAD = "cbbec20d29dcde7e4a1aa3b1fb14b986b8820180"
C2_TREE = "3cce042f161fc7bf3cd42cc679893db7c45f9743"
C3_HEAD = "a33b85a752b3f27c675b7658aeefa18b1cbc987c"
C3_TREE = "0ae277a266b05c499e5c1c91aca5a24fa6d42f0e"
C4_HEAD = "4f06c5e179d9e6f045e1b58cef06ffa98ec0fbea"
C4_TREE = "3f35ae046647dca44353cd8015eda471c9852a37"
C5_HEAD = "9b28ee8811e09ad069f9c029bb27cd92134c28b2"
C5_TREE = "3e0c4dac7ccbc095899c376f6d6833bd3133618c"

LAMBDAS = ("0", "0.0001", "0.0003", "0.001", "0.003", "0.01", "0.03",
           "0.1", "0.3", "1", "3", "10", "30", "100")
CONTRASTS = ("1", "1.25", "1.5", "2", "4", "8", "16")
S_H_LEVELS = ("0.01", "0.03", "0.1", "0.3", "1", "3", "10", "30")
THETA_M = ("0.03", "0.1", "0.3", "1", "3", "10")
THETA_R = ("0.03", "0.1", "0.3", "1", "3", "10")
BETAS = ("0.25", "0.5", "1", "2")
ACTIVE_PLACEMENTS = ("UPSTREAM_LOCALIZED", "DOWNSTREAM_LOCALIZED")
PLACEMENT_ALPHA = {"UPSTREAM_LOCALIZED": "1", "AXIALLY_SELF_SIMILAR": "0.5",
                   "DOWNSTREAM_LOCALIZED": "0"}
EPSILON_FLOOR = "0.05"
FLOOR_LEVELS = ("0.02", "0.05", "0.10")
G_REF_ID = "DIMENSIONLESS_WHOLE_NETWORK_G_REF_1"
MACHINE_TUPLE_ID = "WP02_002_DIMENSIONLESS_LINEAR_SUPPLY_V1"
INTEGRATION_PROFILE = "SCIPY_SOLVE_IVP_DOP853_V1"
BOUNDARY_MODES = ("PRESCRIBED_STATIC", "PRESCRIBED_DYNAMIC_RAMP", "MACHINE_COUPLED")
Q_ZERO_THRESHOLD = 1.0e-14
STARTUP_TAU_MAX = 1.0e-6
PATTERN_SPAN_TOLERANCE = 1.0e-14
D4_STATUS = "DEFERRED_NOT_AUTHORIZED"
X1_STATUS = "DEFERRED_NOT_AUTHORIZED"
D4_AUTHORITY_STOP = "D4_ALTERNATE_INITIAL_STATE_AUTHORITY_UNFROZEN_NOT_AUTHORIZED"
ARCHITECTURE_ID = "ARCHITECTURE_B_BASELINE_ZERO_STATE_STAGE_A_WITH_D4_ROBUSTNESS_DEFERRED"
INITIAL_CONDITION_AUTHORITY_STATUS = (
    "STAGE_A_BASELINE_ZERO_STATE_SCOPE_FROZEN_D4_ROBUSTNESS_UNADJUDICATED_PENDING_REVIEW")
DYNAMIC_INITIAL_STATE_VARIANT = "ZERO_STATE_BASELINE"
STATIC_INITIAL_STATE_VARIANT = "NOT_APPLICABLE_STATIC_ALGEBRAIC"
DYNAMIC_INITIAL_CONDITION_SCOPE = "BASELINE_ZERO_STATE_ONLY"
STATIC_INITIAL_CONDITION_SCOPE = "DYNAMIC_INITIAL_CONDITION_NOT_APPLICABLE"
NOT_ADJUDICATED_STAGE_A = "NOT_ADJUDICATED_STAGE_A"
INITIAL_CONDITION_BRANCH_STATUS = "NOT_EVALUATED_NOT_FALSE"
LEGACY_REALIZATION_SEMANTICS = (
    "LEGACY_STRUCTURAL_OR_HETEROGENEITY_REALIZATION_IDENTIFIER_NOT_DYNAMIC_STATE")
HISTORICAL_ALTERNATE_STATUS = (
    "NON_EXECUTABLE_HISTORICAL_PLACEHOLDERS_WITH_UNRESOLVED_SCIENTIFIC_MEANING")
MAX_RHS_EVALUATIONS = 200000
STARTUP_REFINEMENT_FACTOR = 10.0
REFINED_Q_ZERO_THRESHOLD = Q_ZERO_THRESHOLD / STARTUP_REFINEMENT_FACTOR
REFINED_STARTUP_TAU_MAX = STARTUP_TAU_MAX / STARTUP_REFINEMENT_FACTOR
DYNAMIC_FIRST_STEP = 1.0e-7
FEEDBACK_SIGN_SCALARS = {"EQUALIZING": 1.0, "LOCALIZING": -1.0, "NONE": 0.0}
MULTIPLIER_STOP = "STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUTWARD_CROSSING_NO_CLIPPING"
MULTIPLIER_OUTSIDE_STOP = "STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUTWARD_OR_OUT_OF_RANGE_NO_CLIPPING"
MULTIPLIER_BOUNDARY_ATOL = 1.0e-12
MULTIPLIER_DERIVATIVE_ATOL = 1.0e-14
EVENT_ROOT_VALUE_ATOL = 1.0e-10
MULTIPLIER_CONTEXTS = ("INITIAL_STATE", "ACCEPTED_STEP", "LOCATED_EVENT_ROOT")
FLOW_SCALES = ("SECTOR_SCALED_DIMENSIONLESS", "DIMENSIONAL_SECTOR_FLOW",
               "WHOLE_NETWORK_SCALED_PER_SECTOR")
LINEAR_RESIDUAL_TOLERANCE = 1.0e-12
PIVOT_RATIO_FLOOR = 64.0 * 2.220446049250313e-16
LINEAR_REFINEMENT_MONOTONICITY_ATOL = PIVOT_RATIO_FLOOR
GAIN_DENOMINATOR_FLOOR = 1.0e-12
H_Q_DENOMINATOR_FLOOR = 1.0e-12
SEEDED_MODE_AMPLITUDE_FLOOR = 1.0e-12
SCIENTIFIC_METRICS = ("G_static_H", "G_static_mode", "G_coupling_end", "G_coupling_int")
UNCERTAINTY_COMPONENTS = ("u_integrator", "u_sector", "u_linear", "u_sampling", "u_startup")
FIELD_DISPOSITIONS = ("REQUIRED", "PROHIBITED", "DERIVED", "NOT_APPLICABLE", "PROVENANCE_ONLY")
FIELD_AUTHORITY_CLASSES = ("IDENTITY_PRIMITIVE", "SCIENTIFIC_PRIMITIVE", "DERIVED_EXECUTION_FIELD",
                           "ROLE_OR_CONTROL_FIELD", "PROVENANCE_ONLY")
ALLOWED_ACTIVE_THETA_R = frozenset(THETA_R)
DYNAMIC_NUMERICAL_PROFILES = ("BASE", "INTEGRATOR_REFINED", "STARTUP_REFINED", "LINEAR_REFINED")
STATIC_NUMERICAL_PROFILES = ("BASE", "LINEAR_REFINED")
METRIC_KINDS = ("STATIC_GAIN", "DYNAMIC_ENDPOINT_GAIN", "DYNAMIC_INTEGRATED_GAIN",
                "STATIC_STRUCTURAL_NUMERICAL_CONTROL",
                "DYNAMIC_ENDPOINT_STRUCTURAL_NUMERICAL_CONTROL",
                "DYNAMIC_INTEGRATED_STRUCTURAL_NUMERICAL_CONTROL")
QA_PROTOCOL_FOCUSED_COMMAND = "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sci_lc_001a_protocol"
QA_STATIC_REGRESSION_COMMAND = "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_static_validate_non_mutating"
QA_EXECUTOR_FOCUSED_COMMAND = "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sci_lc_001a_executor"
QA_ICA003_FOCUSED_COMMAND = "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sci_lc_001a_ica003"
QA_COMBINED_FOCUSED_COMMAND = ("PYTHONDONTWRITEBYTECODE=1 python3 -m unittest "
    "tests.test_sci_lc_001a_protocol tests.test_sci_lc_001a_executor "
    "tests.test_static_validate_non_mutating tests.test_sci_lc_001a_ica003")

FIELDS = (
    "case_id", "arm", "model_variant", "pressure_mode", "boundary_profile",
    "prescribed_pressure_amplitude", "sector_count",
    "axial_layer_count", "heterogeneity_pattern", "heterogeneity_mode",
    "heterogeneity_scale", "resistance_contrast", "axial_placement",
    "placement_alpha", "epsilon_floor", "lateral_conductance_ratio",
    "lateral_edge_coefficient", "lateral_edge_conductance_G_edge",
    "G_ref_identity", "G_A_identity", "storage_ratio_S_h",
    "hydraulic_storage_C_h", "derived_Theta_L_m", "machine_response_ratio",
    "machine_compliance_C_u", "machine_reference_tuple",
    "resistance_evolution_law", "resistance_evolution_timescale_ratio",
    "resistance_relaxation_tau_R",
    "feedback_sign", "feedback_gain", "evolution_multiplier_bounds",
    "shot_duration", "initial_condition_variant", "integration_profile",
    "numerical_resolution_role", "scientific_role", "case_role", "parent_selection_rule",
    "eligibility", "static_or_dynamic_classifier", "comparator_case_id",
    "prescribed_comparator_case_id", "no_evolution_comparator_case_id",
    "model_form_requirement", "adaptive_group_id", "uncertainty_profile",
    "units_or_dimensionless_status", "row_sha256",
)
IDENTITY_FIELDS = tuple(x for x in FIELDS if x not in {
    "row_sha256", "comparator_case_id", "prescribed_comparator_case_id",
    "no_evolution_comparator_case_id", "adaptive_group_id"})

FIELD_AUTHORITY = {
    **{key: "IDENTITY_PRIMITIVE" for key in (
        "arm", "model_variant", "pressure_mode", "sector_count", "axial_layer_count",
        "heterogeneity_pattern", "heterogeneity_mode", "heterogeneity_scale", "resistance_contrast",
        "axial_placement", "epsilon_floor", "lateral_conductance_ratio", "G_ref_identity",
        "storage_ratio_S_h", "machine_response_ratio", "resistance_evolution_law",
        "resistance_evolution_timescale_ratio", "feedback_sign", "feedback_gain", "shot_duration",
        "initial_condition_variant")},
    **{key: "SCIENTIFIC_PRIMITIVE" for key in (
        "parent_selection_rule", "eligibility", "units_or_dimensionless_status")},
    **{key: "DERIVED_EXECUTION_FIELD" for key in (
        "case_id", "boundary_profile", "prescribed_pressure_amplitude", "placement_alpha",
        "lateral_edge_coefficient", "lateral_edge_conductance_G_edge", "G_A_identity",
        "hydraulic_storage_C_h", "derived_Theta_L_m", "machine_compliance_C_u",
        "machine_reference_tuple", "resistance_relaxation_tau_R", "evolution_multiplier_bounds",
        "integration_profile", "static_or_dynamic_classifier", "row_sha256")},
    **{key: "ROLE_OR_CONTROL_FIELD" for key in (
        "numerical_resolution_role", "scientific_role", "case_role", "comparator_case_id",
        "prescribed_comparator_case_id", "no_evolution_comparator_case_id", "model_form_requirement",
        "adaptive_group_id", "uncertainty_profile")},
}
if set(FIELD_AUTHORITY) != set(FIELDS):
    raise RuntimeError("FIELD_AUTHORITY_MUST_EXHAUSTIVELY_CLASSIFY_SERIALIZED_SCHEMA")
if set(FIELD_AUTHORITY.values()) - set(FIELD_AUTHORITY_CLASSES):
    raise RuntimeError("UNSUPPORTED_FIELD_AUTHORITY_CLASS")


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def validate_qa_focused_scope(checks: dict) -> None:
    required = {
        "sci_lc_001a_protocol_focused_command": QA_PROTOCOL_FOCUSED_COMMAND,
        "sci_lc_001a_static_validator_regression_command": QA_STATIC_REGRESSION_COMMAND,
        "sci_lc_001a_executor_focused_command": QA_EXECUTOR_FOCUSED_COMMAND,
        "sci_lc_001a_ica003_focused_command": QA_ICA003_FOCUSED_COMMAND,
        "sci_lc_001a_combined_focused_command": QA_COMBINED_FOCUSED_COMMAND,
    }
    if any(checks.get(key) != value for key, value in required.items()):
        raise ValueError("PACKAGE_QA_FOCUSED_COMMAND_SCOPE_MISMATCH")
    protocol_count = checks.get("sci_lc_001a_protocol_focused_test_count")
    static_count = checks.get("sci_lc_001a_static_validator_regression_test_count")
    executor_count = checks.get("sci_lc_001a_executor_focused_test_count")
    ica003_count = checks.get("sci_lc_001a_ica003_focused_test_count")
    combined = checks.get("sci_lc_001a_combined_focused_test_count")
    if (type(protocol_count) is not int or type(static_count) is not int or
            type(executor_count) is not int or type(ica003_count) is not int or
            type(combined) is not int or
            combined != protocol_count + static_count + executor_count + ica003_count):
        raise ValueError("PACKAGE_QA_FOCUSED_COUNT_SCOPE_MISMATCH")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def d(value: str | int | float) -> Decimal:
    return Decimal(str(value))


def token(value: object) -> str:
    return str(value).lower().replace(".", "p").replace("-", "m").replace("_", "-")


def ring_eigenvalue(n: int, mode: int) -> float:
    return 4.0 * (n / (2.0 * math.pi)) ** 2 * math.sin(math.pi * mode / n) ** 2


def edge_coefficient(n: int, lateral: str) -> str:
    if lateral == NA:
        return NA
    return format(float(d(lateral)) * (n / (2.0 * math.pi)) ** 2, ".17g")


def theta_lateral(n: int, mode: str, lateral: str, storage: str) -> str:
    if storage == NA or not mode.isdigit() or int(mode) == 0:
        return NA
    if d(lateral) == 0:
        return INFINITE
    value = float(d(storage)) / (float(d(lateral)) * ring_eigenvalue(n, int(mode)))
    return format(value, ".17g")


def machine_compliance(theta_m: str) -> str:
    if theta_m == NA:
        return NA
    # p_o=0, p_shut=1, q_free=1 -> G_supply=1.  G_ref=1 and R_line=0.1
    # give G_load=1/(1+0.1)=10/11 and a_eff=1+10/11=21/11.
    return format(float(d(theta_m) * d(21) / d(11)), ".17g")


def pattern_values(n: int, pattern: str, mode: str, initial: str = "BASE_PHASE") -> list[float]:
    phase = math.pi if "PHASE_REVERSED" in initial else 0.0
    shift = 1 if "ROTATED_ONE_SECTOR" in initial else 0
    reflected = "REFLECTED" in initial
    values = []
    for i in range(n):
        j = (-i if reflected else i) + shift
        if pattern == "CONTIGUOUS_BLOCK_ROTATED":
            j += max(1, n // 4)
        if pattern == "UNIFORM":
            value = 0.0
        elif pattern.startswith("FOURIER"):
            value = math.cos(2.0 * math.pi * int(mode) * j / n + phase)
        elif pattern.startswith("CONTIGUOUS_BLOCK"):
            value = 1.0 if j % n < n // 2 else -1.0
        elif pattern == "BROADBAND_SEED_20260816":
            value = (math.cos(2 * math.pi * j / n + 0.17)
                     + 0.5 * math.cos(4 * math.pi * j / n + 0.41)
                     + 0.25 * math.cos(6 * math.pi * j / n + 0.73))
        else:
            raise ValueError(f"unknown pattern {pattern}")
        values.append(value)
    return values


def outlet_heterogeneity_from_fractions(fractions: list[float] | tuple[float, ...]) -> float:
    """Owner-authorized H_q: half the L1 distance from uniform outlet share."""
    if not fractions or any(isinstance(value, bool) or not isinstance(value, (int, float)) or
                            not math.isfinite(value) for value in fractions):
        raise ValueError("INVALID_OUTLET_FLOW_FRACTIONS")
    total = sum(fractions)
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1.0e-12):
        raise ValueError("OUTLET_FLOW_FRACTIONS_MUST_SUM_TO_ONE")
    n = len(fractions)
    return 0.5 * sum(abs(float(value) - 1.0 / n) for value in fractions)


def outlet_fraction_primitives(flows: list[float] | tuple[float, ...]) -> dict:
    if not flows or any(isinstance(value, bool) or not isinstance(value, (int, float)) or
                        not math.isfinite(value) for value in flows):
        raise ValueError("INVALID_OUTLET_SECTOR_FLOW")
    if any(value < -Q_ZERO_THRESHOLD for value in flows):
        raise ValueError("STOP_UNEXPECTED_FLOW_REVERSAL")
    total = sum(flows)
    if total <= Q_ZERO_THRESHOLD:
        raise ValueError("NUMERICALLY_UNRESOLVED_TOTAL_FLOW_FLOOR")
    fractions = tuple(float(value) / total for value in flows)
    departures = tuple(value - 1.0 / len(flows) for value in fractions)
    return {"Q_total": total, "fractions": fractions, "departures": departures,
            "H_q": outlet_heterogeneity_from_fractions(fractions)}


def seeded_pattern_amplitude(departures: list[float] | tuple[float, ...], *,
                             pattern: str, mode: str, initial: str = "BASE_PHASE") -> float | str:
    """Owner-authorized phase-invariant Fourier or centered-seed amplitude."""
    n = len(departures)
    if n == 0 or any(isinstance(value, bool) or not isinstance(value, (int, float)) or
                     not math.isfinite(value) for value in departures):
        raise ValueError("INVALID_SEEDED_AMPLITUDE_DEPARTURES")
    if pattern.startswith("FOURIER"):
        try:
            m = int(mode)
        except (TypeError, ValueError) as exc:
            raise ValueError("INVALID_FOURIER_MODE") from exc
        if str(m) != str(mode) or m <= 0 or m > n // 2:
            raise ValueError("INVALID_FOURIER_MODE")
        c_m = sum(value * math.cos(2.0 * math.pi * m * i / n)
                  for i, value in enumerate(departures))
        s_m = sum(value * math.sin(2.0 * math.pi * m * i / n)
                  for i, value in enumerate(departures))
        if n % 2 == 0 and m == n // 2:
            return abs(c_m) / n
        return 2.0 * math.hypot(c_m, s_m) / n
    seed = pattern_values(n, pattern, mode, initial)
    mean = sum(seed) / n
    centered = [value - mean for value in seed]
    norm2 = sum(value * value for value in centered)
    if norm2 <= PATTERN_SPAN_TOLERANCE:
        return NA
    return abs(sum(value * seed_value for value, seed_value in zip(departures, centered))) / norm2


def composite_trapezoid(values: list[float] | tuple[float, ...]) -> float:
    if len(values) < 2 or any(isinstance(value, bool) or not isinstance(value, (int, float)) or
                              not math.isfinite(value) for value in values):
        raise ValueError("INVALID_TRAPEZOID_VALUES")
    step = 1.0 / (len(values) - 1)
    return step * (0.5 * values[0] + sum(values[1:-1]) + 0.5 * values[-1])


def resistance_primitives(n: int, pattern: str, mode: str, contrast: str,
                          placement: str, epsilon: str = EPSILON_FLOOR,
                          initial: str = "BASE_PHASE") -> dict:
    h = pattern_values(n, pattern, mode, initial)
    span = max(h) - min(h)
    if span <= PATTERN_SPAN_TOLERANCE:
        if d(contrast) != 1:
            raise ValueError("ZERO_SPAN_PATTERN_REQUIRES_UNIT_CONTRAST")
        amplitude = 0.0
    else:
        amplitude = math.log(float(d(contrast))) / span
    raw = [math.exp(-amplitude * value) for value in h]
    mean = sum(raw) / n
    g_tilde = [value / mean for value in raw]
    # G_ref=1, a_i=1/N and G_A=1/N.
    conductances = [value / n for value in g_tilde]
    totals = [1.0 / value for value in conductances]
    floor = float(d(epsilon)) * min(totals)
    residual = [value - 2.0 * floor for value in totals]
    alpha = float(d(PLACEMENT_ALPHA[placement]))
    upstream = [floor + alpha * value for value in residual]
    downstream = [floor + (1.0 - alpha) * value for value in residual]
    return {"h": h, "g_tilde": g_tilde, "G_i": conductances, "T_i": totals,
            "R_floor": floor, "H_i": residual, "R_u_i": upstream,
            "R_d_i": downstream}


def evolved_resistance_primitives(base: dict, x: list[float], beta: float,
                                  placement: str) -> dict:
    multipliers = [math.exp(beta * value) for value in x]
    if any(not math.isfinite(value) for value in multipliers):
        raise ValueError("STOP_NONFINITE_RESISTANCE_EVOLUTION_MULTIPLIER")
    if any(value < 0.25 or value > 4.0 for value in multipliers):
        raise ValueError("STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUT_OF_RANGE_NO_CLIPPING")
    residual = [value * multiplier for value, multiplier in zip(base["H_i"], multipliers)]
    alpha = float(d(PLACEMENT_ALPHA[placement])); floor = base["R_floor"]
    return {"multipliers": multipliers, "H_i": residual,
            "R_u_i": [floor + alpha * value for value in residual],
            "R_d_i": [floor + (1.0 - alpha) * value for value in residual]}


def multiplier_admissibility(multiplier: float, beta: float, dx_dt: float, context: str,
                              located_boundary: str | None = None) -> str:
    """Apply the closed-interval, outward-crossing rule to one sector state."""
    if context not in MULTIPLIER_CONTEXTS:
        raise ValueError("INVALID_MULTIPLIER_STATE_CONTEXT")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
           for value in (multiplier, beta, dx_dt)):
        return "STOP_NONFINITE_RESISTANCE_EVOLUTION_MULTIPLIER"
    if context == "LOCATED_EVENT_ROOT":
        targets = {"LOWER_BOUND": 0.25, "UPPER_BOUND": 4.0}
        if located_boundary not in targets:
            raise ValueError("LOCATED_EVENT_ROOT_REQUIRES_BOUNDARY_IDENTITY")
        target = targets[located_boundary]
        if abs(multiplier - target) > EVENT_ROOT_VALUE_ATOL:
            raise ValueError("EVENT_ROOT_STATE_INCONSISTENT_WITH_BOUNDARY")
        multiplier = target
    elif located_boundary is not None:
        raise ValueError("BOUNDARY_IDENTITY_ONLY_VALID_FOR_LOCATED_EVENT_ROOT")
    if multiplier < 0.25 - MULTIPLIER_BOUNDARY_ATOL or multiplier > 4.0 + MULTIPLIER_BOUNDARY_ATOL:
        return MULTIPLIER_OUTSIDE_STOP
    dm_dt = beta * multiplier * dx_dt
    if not math.isfinite(dm_dt):
        return "STOP_NONFINITE_RESISTANCE_EVOLUTION_MULTIPLIER_DERIVATIVE"
    if 0.25 - MULTIPLIER_BOUNDARY_ATOL <= multiplier <= 0.25 + MULTIPLIER_BOUNDARY_ATOL:
        return MULTIPLIER_STOP if dm_dt < -MULTIPLIER_DERIVATIVE_ATOL else "SCIENTIFICALLY_ADMISSIBLE"
    if 4.0 - MULTIPLIER_BOUNDARY_ATOL <= multiplier <= 4.0 + MULTIPLIER_BOUNDARY_ATOL:
        return MULTIPLIER_STOP if dm_dt > MULTIPLIER_DERIVATIVE_ATOL else "SCIENTIFICALLY_ADMISSIBLE"
    return "SCIENTIFICALLY_ADMISSIBLE"


def feedback_sign_scalar(label: str) -> float:
    try:
        return FEEDBACK_SIGN_SCALARS[label]
    except (KeyError, TypeError) as exc:
        raise ValueError("UNSUPPORTED_FEEDBACK_SIGN_LABEL") from exc


def validate_feedback_contract(row: dict) -> None:
    label = row["feedback_sign"]
    scalar = feedback_sign_scalar(label)
    active = row["resistance_evolution_law"] == "SIGNED_LOCAL_FLOW_TO_RESISTANCE_FEEDBACK_SURROGATE"
    try:
        beta = d(row["feedback_gain"])
    except Exception as exc:
        raise ValueError("INVALID_FEEDBACK_GAIN") from exc
    if active:
        theta = row["resistance_evolution_timescale_ratio"]
        if (label not in ("EQUALIZING", "LOCALIZING") or scalar == 0 or beta <= 0 or
                not beta.is_finite() or theta not in ALLOWED_ACTIVE_THETA_R or
                row["resistance_relaxation_tau_R"] != theta or
                row["evolution_multiplier_bounds"] != "[0.25,4]"):
            raise ValueError("ACTIVE_FEEDBACK_REQUIRES_FINITE_NONZERO_SIGNED_EVOLUTION")
    elif row["resistance_evolution_law"] == "NO_EVOLUTION":
        no_evolution_tuple = (label, scalar, str(row["feedback_gain"]),
            row["resistance_evolution_timescale_ratio"], row["resistance_relaxation_tau_R"],
            row["evolution_multiplier_bounds"])
        allowed = {
            ("NONE", 0.0, "0", NA, NA, NA),
            ("NONE", 0.0, "0", "INFINITE_NO_EVOLUTION", "INFINITE_NO_EVOLUTION", NA),
        }
        if no_evolution_tuple not in allowed:
            raise ValueError("INVALID_NO_EVOLUTION_VARIANT_TUPLE")
    else:
        raise ValueError("UNSUPPORTED_RESISTANCE_EVOLUTION_LAW")


def boundary_field_dispositions(mode: str) -> dict[str, str]:
    """Return the explicit, exhaustive disposition table for one mode.

    The global authority is the only starting partition; there is deliberately
    no provenance fallback.  Mode overrides are closed literal sets and the
    final partition is asserted below.
    """
    if mode not in BOUNDARY_MODES:
        raise ValueError("UNSUPPORTED_BOUNDARY_MODE")
    result = {}
    for field, authority in FIELD_AUTHORITY.items():
        if authority in ("IDENTITY_PRIMITIVE", "SCIENTIFIC_PRIMITIVE"):
            result[field] = "REQUIRED"
        elif authority in ("DERIVED_EXECUTION_FIELD", "ROLE_OR_CONTROL_FIELD"):
            result[field] = "DERIVED"
        elif authority == "PROVENANCE_ONLY":
            result[field] = "PROVENANCE_ONLY"
        else:  # pragma: no cover - module initialization guards this
            raise RuntimeError("UNASSIGNED_BOUNDARY_FIELD")
    if mode == "PRESCRIBED_STATIC":
        result["prescribed_pressure_amplitude"] = "REQUIRED"
        for field in ("storage_ratio_S_h", "hydraulic_storage_C_h", "derived_Theta_L_m",
                      "machine_response_ratio", "machine_compliance_C_u", "machine_reference_tuple"):
            result[field] = "NOT_APPLICABLE"
    elif mode == "PRESCRIBED_DYNAMIC_RAMP":
        result.update({"prescribed_pressure_amplitude": "DERIVED", "storage_ratio_S_h": "REQUIRED",
                       "hydraulic_storage_C_h": "DERIVED", "derived_Theta_L_m": "DERIVED"})
        for field in ("machine_response_ratio", "machine_compliance_C_u", "machine_reference_tuple"):
            result[field] = "NOT_APPLICABLE"
    else:
        result["prescribed_pressure_amplitude"] = "NOT_APPLICABLE"
        result.update({"storage_ratio_S_h": "REQUIRED", "hydraulic_storage_C_h": "DERIVED",
                       "derived_Theta_L_m": "DERIVED", "machine_response_ratio": "REQUIRED",
                       "machine_compliance_C_u": "DERIVED", "machine_reference_tuple": "REQUIRED"})
    if set(result) != set(FIELDS) or set(result.values()) - set(FIELD_DISPOSITIONS):
        raise RuntimeError("INCOMPLETE_BOUNDARY_FIELD_TRUTH_TABLE")
    if any(FIELD_AUTHORITY[field] == "DERIVED_EXECUTION_FIELD" and disposition == "PROVENANCE_ONLY"
           for field, disposition in result.items()):
        raise RuntimeError("EXECUTION_FIELD_CANNOT_BE_PROVENANCE_ONLY")
    return result


def validate_boundary_row(row: dict) -> None:
    mode = row["pressure_mode"]
    dispositions = boundary_field_dispositions(mode)
    if set(dispositions) != set(FIELDS) or set(dispositions.values()) - set(FIELD_DISPOSITIONS):
        raise ValueError("INCOMPLETE_BOUNDARY_FIELD_TRUTH_TABLE")
    if mode == "PRESCRIBED_STATIC":
        if (row["boundary_profile"] != "CONSTANT_BASKET_PRESSURE" or
                row["integration_profile"] != "STATIC_LINEAR_SOLVE_V1" or
                row["prescribed_pressure_amplitude"] == NA):
            raise ValueError("INVALID_PRESCRIBED_STATIC_BOUNDARY")
        prohibited = ("storage_ratio_S_h", "hydraulic_storage_C_h", "derived_Theta_L_m",
                      "machine_response_ratio", "machine_compliance_C_u", "machine_reference_tuple")
    elif mode == "PRESCRIBED_DYNAMIC_RAMP":
        if (row["boundary_profile"] != "PIECEWISE_LINEAR_RAMP_TAU_0P05" or
                row["integration_profile"] != INTEGRATION_PROFILE or
                row["prescribed_pressure_amplitude"] != "1"):
            raise ValueError("INVALID_PRESCRIBED_DYNAMIC_BOUNDARY")
        prohibited = ("machine_response_ratio", "machine_compliance_C_u", "machine_reference_tuple")
    else:
        if (row["boundary_profile"] != "WP02_002_LINEAR_SUPPLY_RAMP_TAU_0P05" or
                row["integration_profile"] != INTEGRATION_PROFILE or
                row["prescribed_pressure_amplitude"] != NA or
                row["machine_reference_tuple"] != MACHINE_TUPLE_ID):
            raise ValueError("INVALID_MACHINE_BOUNDARY")
        prohibited = ()
    if any(row[field] != NA for field in prohibited):
        raise ValueError("PROHIBITED_BOUNDARY_FIELD_IS_ACTIVE")
    if mode != "PRESCRIBED_STATIC":
        if row["storage_ratio_S_h"] == NA or row["hydraulic_storage_C_h"] == NA:
            raise ValueError("MISSING_DYNAMIC_STORAGE_PRIMITIVE")
        expected_ch = format(float(d(row["storage_ratio_S_h"])) / int(row["sector_count"]), ".17g")
        if row["hydraulic_storage_C_h"] != expected_ch:
            raise ValueError("INCONSISTENT_DYNAMIC_STORAGE_PRIMITIVE")
    if mode == "MACHINE_COUPLED":
        if row["machine_response_ratio"] == NA or row["machine_compliance_C_u"] == NA:
            raise ValueError("MISSING_MACHINE_PRIMITIVE")
        if row["machine_compliance_C_u"] != machine_compliance(row["machine_response_ratio"]):
            raise ValueError("INCONSISTENT_MACHINE_COMPLIANCE")


def uncertainty_limit(gain: float) -> float:
    if not math.isfinite(gain):
        raise ValueError("NONFINITE_GAIN")
    return min(0.02, 0.02 * abs(gain))


def startup_focusing(base: dict, storage: list[float], boundary_mode: str) -> list[float]:
    """Exact tau->0+ outlet focusing for the frozen zero-pressure start.

    Dynamic prescribed and machine pressure are common scalar forcings.  The
    first nonzero internal-pressure coefficient is proportional to G_u/C_h;
    q_d is therefore proportional to G_u*G_d/C_h.  Machine compliance changes
    only the common time coefficient and cancels from normalized fractions.
    The prescribed-static mode instead starts at its algebraic unit-pressure
    state and has no zero-flow branch.
    """
    if boundary_mode not in BOUNDARY_MODES:
        raise ValueError("UNSUPPORTED_BOUNDARY_MODE")
    if boundary_mode == "PRESCRIBED_STATIC":
        raise ValueError("STATIC_MODE_HAS_NO_ZERO_FLOW_STARTUP_BRANCH")
    if len(storage) != len(base["R_u_i"]) or any(value <= 0 for value in storage):
        raise ValueError("INVALID_STARTUP_STORAGE")
    weights = [1.0 / (ru * rd * ch) for ru, rd, ch in
               zip(base["R_u_i"], base["R_d_i"], storage)]
    total = sum(weights)
    n = len(weights)
    return [(value / total) * n for value in weights]


class SectorFlowVector(NamedTuple):
    values: tuple[float, ...]
    N: int
    scale: str
    G_ref: float | None = None
    delta_p_ref: float | None = None


def q_hat_total_from_flow(flow: SectorFlowVector) -> float:
    return sum(canonical_sector_q_hat(flow)) / flow.N


def canonical_sector_q_hat(flow: SectorFlowVector) -> tuple[float, ...]:
    """Return the sole canonical sector-scaled dimensionless flow vector."""
    if not isinstance(flow, SectorFlowVector):
        raise ValueError("UNTAGGED_FLOW_VECTOR_NOT_AUTHORIZED")
    if type(flow.N) is not int or flow.N not in (4, 8, 16) or len(flow.values) != flow.N:
        raise ValueError("INVALID_SECTOR_COUNT_FOR_TOTAL_Q_HAT")
    if flow.scale not in FLOW_SCALES:
        raise ValueError("UNKNOWN_SECTOR_FLOW_SCALE")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
           for value in flow.values):
        raise ValueError("NONFINITE_SECTOR_FLOW")
    if flow.scale == "WHOLE_NETWORK_SCALED_PER_SECTOR":
        raise ValueError("UNSUPPORTED_WHOLE_NETWORK_SCALED_PER_SECTOR_INPUT")
    if flow.scale == "SECTOR_SCALED_DIMENSIONLESS":
        return tuple(float(value) for value in flow.values)
    if any(value is None or isinstance(value, bool) or not isinstance(value, (int, float)) or
           not math.isfinite(value) or value <= 0 for value in (flow.G_ref, flow.delta_p_ref)):
        raise ValueError("INVALID_TOTAL_Q_HAT_REFERENCE_SCALE")
    g_a = flow.G_ref / flow.N
    return tuple(float(value) / (g_a * flow.delta_p_ref) for value in flow.values)


def evolution_focusing(*, tau: float, flow: SectorFlowVector, startup: list[float],
                       zero_threshold: float = Q_ZERO_THRESHOLD,
                       startup_tau_max: float = STARTUP_TAU_MAX) -> list[float]:
    flows = canonical_sector_q_hat(flow)
    q_total = sum(flows) / flow.N
    total = sum(flows)
    if q_total < -zero_threshold or any(value < -zero_threshold for value in flows):
        raise ValueError("STOP_UNEXPECTED_FLOW_REVERSAL")
    if abs(q_total) <= zero_threshold:
        if tau <= startup_tau_max:
            return list(startup)
        raise ValueError("STOP_ZERO_TOTAL_FLOW_OUTSIDE_STARTUP_WINDOW")
    n = len(flows)
    return [(value / total) * n for value in flows]


def startup_uncertainty(base_gain: float | str, refined_gain: float | str,
                        *, refined_status: str = "COMPLETE") -> float:
    if refined_status in ("STOPPED", "CAPPED", "UNAVAILABLE"):
        raise ValueError("NUMERICALLY_UNRESOLVED_STARTUP_REFINEMENT")
    if refined_status != "COMPLETE":
        raise ValueError("AUTHORITY_OR_ARTIFACT_INVALID_STARTUP_REFINEMENT_STATUS")
    if not isinstance(base_gain, (int, float)) or not isinstance(refined_gain, (int, float)):
        raise ValueError("AUTHORITY_OR_ARTIFACT_INVALID_STARTUP_REFINEMENT_VALUE")
    if not math.isfinite(base_gain) or not math.isfinite(refined_gain):
        raise ValueError("NUMERICALLY_UNRESOLVED_STARTUP_REFINEMENT")
    return abs(base_gain - refined_gain)


def scaled_residual_norm(residual: list[float], scale: list[float],
                         absolute_floor: float = 1.0e-14) -> float:
    if len(residual) != len(scale) or not residual:
        raise ValueError("INVALID_RESIDUAL_VECTOR")
    if not all(math.isfinite(value) for value in residual + scale):
        raise ValueError("NONFINITE_RESIDUAL_OR_SCALE")
    return max(abs(value) / max(abs(unit), absolute_floor)
               for value, unit in zip(residual, scale))


def enforce_rhs_cap(nfev: int, cap: int = MAX_RHS_EVALUATIONS) -> int:
    """Return the incremented counter or fail before an over-cap RHS call."""
    if nfev >= cap:
        raise ValueError("STOP_MAX_RHS_EVALUATIONS_REACHED")
    return nfev + 1


def select_multiplier_event(events: list[dict], *, time_tolerance: float = 1.0e-10) -> dict:
    """Select the earliest dense-output-located terminal event deterministically."""
    if not events:
        raise ValueError("NO_EVENT")
    for event in events:
        if not math.isfinite(float(event["tau"])):
            raise ValueError("STOP_NONFINITE_EVENT_FUNCTION")
        if event["bound"] not in ("LOWER_BOUND", "UPPER_BOUND"):
            raise ValueError("INVALID_EVENT_BOUND")
    first = min(float(event["tau"]) for event in events)
    tied = [event for event in events if abs(float(event["tau"]) - first) <= time_tolerance]
    order = {"LOWER_BOUND": 0, "UPPER_BOUND": 1}
    return min(tied, key=lambda event: (order[event["bound"]], int(event["sector_index"])))


def locate_linear_event(t0: float, value0: float, t1: float, value1: float,
                        target: float) -> float:
    """Tiny exact fixture for a dense-output crossing, not a trajectory integrator."""
    values = (t0, value0, t1, value1, target)
    if not all(math.isfinite(value) for value in values) or t1 <= t0 or value1 == value0:
        raise ValueError("INVALID_EVENT_BRACKET")
    fraction = (target - value0) / (value1 - value0)
    if not 0 <= fraction <= 1:
        raise ValueError("EVENT_NOT_BRACKETED")
    return t0 + fraction * (t1 - t0)


class LinearSolveResult(NamedTuple):
    solution: tuple[float, ...]
    scaled_residual: float
    solver_status: str
    pivot_history: tuple[tuple[int, int, float], ...]
    row_permutation: tuple[int, ...]
    failure_reason: str | None


class LinearRefinementResult(NamedTuple):
    base: LinearSolveResult
    correction: LinearSolveResult
    corrected_state: tuple[float, ...]
    corrected_scaled_residual: float
    status: str
    failure_reason: str | None
    correction_steps: int


def _linear_failure(reason: str) -> LinearSolveResult:
    return LinearSolveResult((), math.inf, "FAIL", (), (), reason)


def solve_dense_binary64(matrix: list[list[float]], rhs: list[float]) -> LinearSolveResult:
    """Authoritative binary64 Gaussian solve with scaled partial pivoting."""
    if not isinstance(matrix, (list, tuple)) or not isinstance(rhs, (list, tuple)):
        return _linear_failure("INVALID_LINEAR_SYSTEM_CONTAINER")
    n = len(rhs)
    if n == 0 or len(matrix) != n or any(not isinstance(row, (list, tuple)) or len(row) != n
                                         for row in matrix):
        return _linear_failure("INVALID_LINEAR_SYSTEM_SHAPE")
    values = [value for row in matrix for value in row] + list(rhs)
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
               for value in values):
        return _linear_failure("NONFINITE_OR_UNSUPPORTED_LINEAR_SYSTEM")
    original_a = [[float(value) for value in row] for row in matrix]
    original_b = [float(value) for value in rhs]
    augmented = [row[:] + [original_b[i]] for i, row in enumerate(original_a)]
    row_scales = [max(abs(value) for value in row) for row in original_a]
    if any(not math.isfinite(value) or value == 0.0 for value in row_scales):
        return _linear_failure("ZERO_OR_NONFINITE_INITIAL_ROW_SCALE")
    row_ids = list(range(n)); pivots = []
    for column in range(n):
        candidates = [(abs(augmented[index][column]) / row_scales[index], -row_ids[index], index)
                      for index in range(column, n)]
        ratio, _, pivot = max(candidates)
        if not math.isfinite(ratio) or ratio <= PIVOT_RATIO_FLOOR:
            return _linear_failure("SCALED_PIVOT_RATIO_AT_OR_BELOW_FLOOR")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        row_scales[column], row_scales[pivot] = row_scales[pivot], row_scales[column]
        row_ids[column], row_ids[pivot] = row_ids[pivot], row_ids[column]
        pivots.append((column, row_ids[column], ratio))
        divisor = augmented[column][column]
        for row in range(column + 1, n):
            factor = augmented[row][column] / divisor
            for index in range(column, n + 1):
                augmented[row][index] -= factor * augmented[column][index]
    solution = [0.0] * n
    for row in range(n - 1, -1, -1):
        pivot = augmented[row][row]
        ratio = abs(pivot) / row_scales[row]
        if not math.isfinite(ratio) or ratio <= PIVOT_RATIO_FLOOR:
            return _linear_failure("SCALED_BACKSUBSTITUTION_PIVOT_AT_OR_BELOW_FLOOR")
        solution[row] = (augmented[row][n] - sum(augmented[row][j] * solution[j]
                                                 for j in range(row + 1, n))) / pivot
    if not all(math.isfinite(value) for value in solution):
        return _linear_failure("NONFINITE_LINEAR_SOLUTION")
    residual = [sum(original_a[i][j] * solution[j] for j in range(n)) - original_b[i]
                for i in range(n)]
    scale = [max(abs(original_b[i]), sum(abs(original_a[i][j]) * abs(solution[j])
                                        for j in range(n)), 1.0e-14) for i in range(n)]
    norm = scaled_residual_norm(residual, scale)
    if not math.isfinite(norm) or norm > LINEAR_RESIDUAL_TOLERANCE:
        return LinearSolveResult(tuple(solution), norm, "FAIL", tuple(pivots), tuple(row_ids),
                                 "BASE_SCALED_RESIDUAL_ABOVE_TOLERANCE")
    return LinearSolveResult(tuple(solution), norm, "PASS", tuple(pivots), tuple(row_ids), None)


def linear_refinement_residuals_admissible(base_norm: float, corrected_norm: float) -> bool:
    """Apply the frozen absolute ceiling and binary64 monotonicity allowance."""
    return (math.isfinite(base_norm) and math.isfinite(corrected_norm) and
            corrected_norm <= LINEAR_RESIDUAL_TOLERANCE and
            corrected_norm <= base_norm + LINEAR_REFINEMENT_MONOTONICITY_ATOL)


def linear_refined_state(matrix: list[list[float]], rhs: list[float]) -> LinearRefinementResult:
    """Obtain authoritative BASE and apply exactly one identical-solver correction."""
    base = solve_dense_binary64(matrix, rhs)
    if base.solver_status != "PASS":
        raise ValueError("LINEAR_REFINED_BASE_SOLVE_FAILED:" + str(base.failure_reason))
    n = len(rhs); base_state = base.solution
    residual0 = [sum(float(matrix[i][j]) * base_state[j] for j in range(n)) - float(rhs[i])
                 for i in range(n)]
    correction = solve_dense_binary64(matrix, [-value for value in residual0])
    if correction.solver_status != "PASS":
        raise ValueError("LINEAR_REFINED_CORRECTION_SOLVE_FAILED:" + str(correction.failure_reason))
    state1 = [value + delta for value, delta in zip(base_state, correction.solution)]
    residual1 = [sum(matrix[i][j] * state1[j] for j in range(n)) - rhs[i] for i in range(n)]
    scale1 = [max(abs(rhs[i]), sum(abs(matrix[i][j]) * abs(state1[j]) for j in range(n)), 1.0e-14)
              for i in range(n)]
    norm1 = scaled_residual_norm(residual1, scale1)
    if not linear_refinement_residuals_admissible(base.scaled_residual, norm1):
        raise ValueError("LINEAR_REFINED_RESIDUAL_FAILED")
    return LinearRefinementResult(base, correction, tuple(state1), norm1, "PASS", None, 1)


class GainRecord(NamedTuple):
    subject_case_id: str
    comparator_case_id: str
    metric_kind: str
    numerical_profile: str
    numerator: float
    denominator: float
    gain: float
    denominator_floor: float
    denominator_status: str
    subject_role: str
    comparator_role: str
    boundary_mode: str
    construction_status: str


class UncertaintyContract(NamedTuple):
    subject_case_id: str
    comparator_case_id: str | None
    metric_kind: str
    evaluation_kind: str
    numerical_profile: str
    applicability: tuple[tuple[str, bool], ...]


def _canonical_map(canonical_rows: list[dict]) -> dict[str, dict]:
    mapping = {row["case_id"]: row for row in canonical_rows}
    if len(mapping) != len(canonical_rows):
        raise ValueError("DUPLICATE_CANONICAL_CASE_ID")
    return mapping


def _validate_comparator_pair(subject: dict, comparator: dict) -> None:
    if subject["comparator_case_id"] != comparator["case_id"] or subject["case_id"] == comparator["case_id"]:
        raise ValueError("AUTHORITY_OR_ARTIFACT_INVALID_COMPARATOR")
    if comparator["case_role"] != "STRUCTURAL_COMPARATOR" or comparator["lateral_conductance_ratio"] != "0":
        raise ValueError("AUTHORITY_OR_ARTIFACT_INVALID_COMPARATOR_ROLE")
    ignored = ("lateral_conductance_ratio", "lateral_edge_coefficient",
               "lateral_edge_conductance_G_edge", "derived_Theta_L_m", "scientific_role", "case_role")
    if comparison_key(subject, ignore=ignored) != comparison_key(comparator, ignore=ignored):
        raise ValueError("AUTHORITY_OR_ARTIFACT_INVALID_COMPARATOR_IDENTITY")


def build_gain_record(canonical_rows: list[dict], subject_case_id: str, metric_kind: str,
                      numerical_profile: str, numerator: float, denominator: float) -> GainRecord:
    rows = _canonical_map(canonical_rows)
    if subject_case_id not in rows:
        raise ValueError("UNKNOWN_GAIN_SUBJECT")
    subject = rows[subject_case_id]
    validate_row_against_expected_fields(subject, _canonical_map(build_rows()))
    if metric_kind not in METRIC_KINDS[:3] or subject["case_role"] != "ACTIVE_SCIENTIFIC_CASE":
        raise ValueError("ORDINARY_GAIN_REQUIRES_ACTIVE_SCIENTIFIC_CASE")
    comparator_id = subject["comparator_case_id"]
    if comparator_id == NA or comparator_id not in rows:
        raise ValueError("GAIN_REQUIRES_RESOLVED_COMPARATOR")
    comparator = rows[comparator_id]
    validate_row_against_expected_fields(comparator, _canonical_map(build_rows()))
    _validate_comparator_pair(subject, comparator)
    static = subject["pressure_mode"] == "PRESCRIBED_STATIC"
    if static != (metric_kind == "STATIC_GAIN"):
        raise ValueError("GAIN_METRIC_BOUNDARY_MODE_MISMATCH")
    profiles = STATIC_NUMERICAL_PROFILES if static else DYNAMIC_NUMERICAL_PROFILES
    if numerical_profile not in profiles:
        raise ValueError("GAIN_NUMERICAL_PROFILE_NOT_AUTHORIZED")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
           for value in (numerator, denominator)):
        raise ValueError("INVALID_GAIN_NUMERIC_INPUT")
    if abs(denominator) <= GAIN_DENOMINATOR_FLOOR:
        raise ValueError("NUMERICALLY_UNRESOLVED_DENOMINATOR_FLOOR")
    return GainRecord(subject_case_id, comparator_id, metric_kind, numerical_profile,
                      float(numerator), float(denominator), float(numerator / denominator),
                      GAIN_DENOMINATOR_FLOOR, "PASS", subject["case_role"], comparator["case_role"],
                      subject["pressure_mode"], "COMPLETE")


def gain_profile_uncertainty(base_record: GainRecord, refined_record: GainRecord,
                             expected_refined_profile: str) -> float:
    if not isinstance(base_record, GainRecord) or not isinstance(refined_record, GainRecord):
        raise ValueError("GAIN_UNCERTAINTY_REQUIRES_VALIDATED_RECORDS")
    if base_record.numerical_profile != "BASE" or refined_record.numerical_profile != expected_refined_profile:
        raise ValueError("GAIN_PROFILE_MISMATCH")
    identity = ("subject_case_id", "comparator_case_id", "metric_kind", "subject_role",
                "comparator_role", "boundary_mode")
    if any(getattr(base_record, key) != getattr(refined_record, key) for key in identity):
        raise ValueError("GAIN_RECORD_IDENTITY_MISMATCH")
    if any(record.construction_status != "COMPLETE" or record.denominator_status != "PASS"
           for record in (base_record, refined_record)):
        raise ValueError("NUMERICALLY_UNRESOLVED_REQUIRED_PROFILE")
    return abs(base_record.gain - refined_record.gain)


def derive_uncertainty_contract(canonical_rows: list[dict], subject_case_id: str,
                                metric_kind: str, evaluation_kind: str,
                                execution_status: str, numerical_profile: str = "BASE") -> UncertaintyContract:
    if metric_kind not in METRIC_KINDS or evaluation_kind not in ("GAIN", "CONTROL"):
        raise ValueError("UNSUPPORTED_UNCERTAINTY_EVALUATION")
    if execution_status != "COMPLETE":
        raise ValueError("NUMERICALLY_UNRESOLVED_EXECUTION_STATUS")
    rows = _canonical_map(canonical_rows)
    if subject_case_id not in rows:
        raise ValueError("UNKNOWN_UNCERTAINTY_SUBJECT")
    subject = rows[subject_case_id]
    validate_row_against_expected_fields(subject, _canonical_map(build_rows()))
    gain_metric = metric_kind in METRIC_KINDS[:3]
    if gain_metric != (evaluation_kind == "GAIN"):
        raise ValueError("METRIC_EVALUATION_KIND_MISMATCH")
    static_metric = metric_kind in ("STATIC_GAIN", "STATIC_STRUCTURAL_NUMERICAL_CONTROL")
    static_row = subject["pressure_mode"] == "PRESCRIBED_STATIC"
    if static_metric != static_row:
        raise ValueError("METRIC_BOUNDARY_MODE_MISMATCH")
    profiles = STATIC_NUMERICAL_PROFILES if static_row else DYNAMIC_NUMERICAL_PROFILES
    if numerical_profile not in profiles:
        raise ValueError("UNAUTHORIZED_NUMERICAL_PROFILE")
    comparator_id = None
    if gain_metric:
        if subject["case_role"] != "ACTIVE_SCIENTIFIC_CASE":
            raise ValueError("GAIN_REQUIRES_ACTIVE_SCIENTIFIC_CASE")
        comparator_id = subject["comparator_case_id"]
        if comparator_id == NA or comparator_id not in rows:
            raise ValueError("GAIN_REQUIRES_RESOLVED_COMPARATOR")
        comparator = rows[comparator_id]
        validate_row_against_expected_fields(comparator, _canonical_map(build_rows()))
        _validate_comparator_pair(subject, comparator)
    elif subject["case_role"] not in ("STRUCTURAL_COMPARATOR", "BOUNDED_STRUCTURAL_CONTROL"):
        raise ValueError("CONTROL_METRIC_REQUIRES_STRUCTURAL_OR_BOUNDED_CONTROL")
    sector = sector_refinement_nref(subject) != NA
    table = {
        "STATIC_GAIN": (False, sector, True, False, False),
        "DYNAMIC_ENDPOINT_GAIN": (True, sector, True, False, True),
        "DYNAMIC_INTEGRATED_GAIN": (True, sector, True, True, True),
        "STATIC_STRUCTURAL_NUMERICAL_CONTROL": (False, sector, True, False, False),
        "DYNAMIC_ENDPOINT_STRUCTURAL_NUMERICAL_CONTROL": (True, sector, True, False, True),
        "DYNAMIC_INTEGRATED_STRUCTURAL_NUMERICAL_CONTROL": (True, sector, True, True, True),
    }
    return UncertaintyContract(subject_case_id, comparator_id, metric_kind, evaluation_kind,
                               numerical_profile, tuple(zip(UNCERTAINTY_COMPONENTS, table[metric_kind])))


def combine_uncertainty(components: dict[str, float | str], contract: UncertaintyContract) -> float:
    if not isinstance(contract, UncertaintyContract):
        raise ValueError("AUTHORITATIVE_UNCERTAINTY_CONTRACT_REQUIRED")
    applicable = dict(contract.applicability)
    if set(components) != set(UNCERTAINTY_COMPONENTS):
        raise ValueError("AUTHORITY_OR_ARTIFACT_INVALID_UNCERTAINTY_COMPONENT_SET")
    total = 0.0
    for name in UNCERTAINTY_COMPONENTS:
        value = components[name]
        if not applicable[name]:
            if value != NA:
                raise ValueError("AUTHORITY_OR_ARTIFACT_INVALID_INAPPLICABLE_COMPONENT_VALUE")
            continue
        if value == NA:
            if applicable[name]:
                raise ValueError("AUTHORITY_OR_ARTIFACT_INVALID_NOT_APPLICABLE_REQUIRED_COMPONENT")
        if value == "UNAVAILABLE":
            raise ValueError("NUMERICALLY_UNRESOLVED_UNCERTAINTY_COMPONENT")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("AUTHORITY_OR_ARTIFACT_INVALID_UNCERTAINTY_COMPONENT")
        if not math.isfinite(value) or value < 0:
            raise ValueError("AUTHORITY_OR_ARTIFACT_INVALID_UNCERTAINTY_COMPONENT")
        total += value
    return total


def sector_refinement_nref(row: dict) -> int | str:
    role = row["numerical_resolution_role"]
    n = int(row["sector_count"])
    if role == "SECTOR_REFINEMENT":
        return {4: 8, 8: 16, 16: NA}.get(n, NA)
    if role == "NYQUIST_TO_RESOLVED_DIAGNOSTIC":
        return 16 if n == 8 else NA
    return NA


def sector_companion_case_id(row: dict, rows: list[dict]) -> str:
    nref = sector_refinement_nref(row)
    if nref == NA:
        return NA
    ignored = {"case_id", "sector_count", "G_A_identity", "hydraulic_storage_C_h",
               "lateral_edge_coefficient", "lateral_edge_conductance_G_edge",
               "derived_Theta_L_m", "comparator_case_id", "row_sha256", "adaptive_group_id"}
    matches = [candidate for candidate in rows if candidate["sector_count"] == nref and
               all(candidate[key] == row[key] for key in FIELDS if key not in ignored)]
    if len(matches) != 1:
        raise ValueError("NUMERICALLY_UNRESOLVED_SECTOR_COMPANION")
    return matches[0]["case_id"]


def execution_graph(rows: list[dict]) -> dict:
    """Prospective unique case/profile keys only; performs no solve."""
    keys = []
    for row in rows:
        profiles = (STATIC_NUMERICAL_PROFILES if row["pressure_mode"] == "PRESCRIBED_STATIC"
                    else DYNAMIC_NUMERICAL_PROFILES)
        keys.extend((row["case_id"], profile) for profile in profiles)
    if len(keys) != len(set(keys)):
        raise ValueError("DUPLICATE_EXECUTION_GRAPH_KEY")
    dynamic_rows = sum(row["pressure_mode"] != "PRESCRIBED_STATIC" for row in rows)
    static_rows = len(rows) - dynamic_rows
    return {"keys": keys, "dynamic_matrix_rows": dynamic_rows, "static_matrix_rows": static_rows,
            "maximum_dynamic_trajectory_invocations": dynamic_rows * len(DYNAMIC_NUMERICAL_PROFILES),
            "maximum_static_solve_invocations": static_rows * len(STATIC_NUMERICAL_PROFILES),
            "maximum_total_solver_cases": len(keys), "sampling_additional_trajectories": 0,
            "sector_additional_out_of_matrix_cases": 0,
            "cache_key": "(case_id,numerical_profile)", "automatic_retries": 0,
            "combined_profiles_authorized": False}


def sector_bundle_audit(rows: list[dict]) -> dict:
    by_id = {row["case_id"]: row for row in rows}
    sources = [row for row in rows if row["case_role"] == "ACTIVE_SCIENTIFIC_CASE" and
               sector_refinement_nref(row) != NA]
    complete = 0
    for row in sources:
        companion = by_id.get(sector_companion_case_id(row, rows))
        comparator = by_id.get(row["comparator_case_id"])
        if companion is None or comparator is None:
            continue
        companion_comparator = by_id.get(companion["comparator_case_id"])
        if companion_comparator is not None and sector_companion_case_id(comparator, rows) == companion_comparator["case_id"]:
            complete += 1
    return {"required_bundles": len(sources), "complete_four_case_bundles": complete,
            "all_complete": complete == len(sources)}


def structural_identity(row: dict) -> str | None:
    if row.get("lateral_conductance_ratio") == "0":
        return "EXACT_LAMBDA_ZERO_IDENTITY"
    if row.get("axial_placement") == "AXIALLY_SELF_SIMILAR":
        return "EXACT_SELF_SIMILAR_EXCHANGE_NULL"
    if row.get("heterogeneity_pattern") == "UNIFORM" and row.get("resistance_contrast") == "1":
        return "EXACT_UNIFORM_SYMMETRY"
    return None


def stage_a_initial_condition_scope(row: dict) -> dict[str, str]:
    """Return the frozen Stage-A scope; no row field can select another start."""
    if row.get("pressure_mode") == "PRESCRIBED_STATIC":
        return {
            "dynamic_initial_state_variant": STATIC_INITIAL_STATE_VARIANT,
            "initial_condition_scope": STATIC_INITIAL_CONDITION_SCOPE,
            "initial_condition_robustness": STATIC_INITIAL_STATE_VARIANT,
            "bistability_status": STATIC_INITIAL_STATE_VARIANT,
            "initial_condition_dependence_branch": STATIC_INITIAL_STATE_VARIANT,
        }
    if row.get("pressure_mode") not in ("PRESCRIBED_DYNAMIC_RAMP", "MACHINE_COUPLED"):
        raise ValueError("UNKNOWN_STAGE_A_STATIC_DYNAMIC_IDENTITY")
    return {
        "dynamic_initial_state_variant": DYNAMIC_INITIAL_STATE_VARIANT,
        "initial_condition_scope": DYNAMIC_INITIAL_CONDITION_SCOPE,
        "initial_condition_robustness": NOT_ADJUDICATED_STAGE_A,
        "bistability_status": NOT_ADJUDICATED_STAGE_A,
        "initial_condition_dependence_branch": INITIAL_CONDITION_BRANCH_STATUS,
    }


def qualify_stage_a_classification(row: dict, regime_label: str) -> str:
    """Make the Stage-A scope inseparable from every serialized classification."""
    if not isinstance(regime_label, str) or not regime_label:
        raise ValueError("INVALID_STAGE_A_REGIME_LABEL")
    return regime_label + ";" + stage_a_initial_condition_scope(row)["initial_condition_scope"]


class DeferredStageError(RuntimeError):
    pass


def classify_synthetic_fixture(*, authority_valid: bool = True, numerical_valid: bool = True,
                               structural_control: bool = False,
                               model_disagreement: bool = False, metric_disagreement: bool = False,
                               threshold_straddle: bool = False, end_gain: float = 1.0,
                               integrated_gain: float = 1.0) -> str:
    """Encode precedence only; never classify a prospective matrix row."""
    if not authority_valid:
        return "AUTHORITY_OR_ARTIFACT_INVALID"
    if structural_control:
        return "UNIFORM_OR_STRUCTURAL_CONTROL"
    if not numerical_valid:
        return "NUMERICALLY_UNRESOLVED"
    if model_disagreement:
        return "MODEL_FORM_OR_SECTOR_RESOLUTION_DISAGREEMENT"
    if metric_disagreement:
        return "METRIC_DISAGREEMENT"
    if threshold_straddle:
        return "NEAR_THRESHOLD_TRANSITION"
    if end_gain <= 0.9 and integrated_gain <= 0.9:
        return "LATERAL_EQUALIZATION"
    if end_gain >= 1.1 and integrated_gain >= 1.1:
        return "HETEROGENEITY_AMPLIFIES"
    return "HETEROGENEITY_PERSISTS"


def make_row(*, arm: str, pressure: str = "PRESCRIBED_STATIC", n: int = 8,
             pattern: str = "FOURIER", mode: str = "1", scale: str = "MODE_1",
             contrast: str = "1.5", placement: str = "UPSTREAM_LOCALIZED",
             epsilon: str = EPSILON_FLOOR, lateral: str = "0.1", storage: str = NA,
             theta_m: str = NA, law: str = "NO_EVOLUTION", theta_r: str = NA,
             sign: str = "NONE", beta: str = "0", initial: str = "BASE_PHASE",
             resolution: str = "PRIMARY", role: str = "SCIENTIFIC",
             parent: str = "FROZEN_INITIAL_MATRIX", eligibility: str = "INITIAL_ELIGIBLE",
             classifier: str = "STATIC_CLASSIFIER_V1", pressure_amplitude: str = "1") -> dict:
    if pressure == "PRESCRIBED_STATIC":
        boundary_profile, amplitude = "CONSTANT_BASKET_PRESSURE", pressure_amplitude
    elif pressure == "PRESCRIBED_DYNAMIC_RAMP":
        boundary_profile, amplitude = "PIECEWISE_LINEAR_RAMP_TAU_0P05", "1"
    elif pressure == "MACHINE_COUPLED":
        boundary_profile, amplitude = "WP02_002_LINEAR_SUPPLY_RAMP_TAU_0P05", NA
    else:
        raise ValueError("UNSUPPORTED_BOUNDARY_MODE")
    if classifier == "STATIC_CLASSIFIER_V1" and pressure != "PRESCRIBED_STATIC":
        raise ValueError("STATIC_CLASSIFIER_REQUIRES_PRESCRIBED_STATIC")
    if classifier == "DYNAMIC_CLASSIFIER_V1" and pressure == "PRESCRIBED_STATIC":
        raise ValueError("DYNAMIC_CLASSIFIER_REQUIRES_DYNAMIC_BOUNDARY")
    row = {
        "case_id": "", "arm": arm, "model_variant": "CORE_ONE_EXCHANGE_PLANE",
        "pressure_mode": pressure, "boundary_profile": boundary_profile,
        "prescribed_pressure_amplitude": amplitude,
        "sector_count": n, "axial_layer_count": 2,
        "heterogeneity_pattern": pattern, "heterogeneity_mode": mode,
        "heterogeneity_scale": scale, "resistance_contrast": contrast,
        "axial_placement": placement, "placement_alpha": PLACEMENT_ALPHA[placement],
        "epsilon_floor": epsilon, "lateral_conductance_ratio": lateral,
        "lateral_edge_coefficient": edge_coefficient(n, lateral),
        "lateral_edge_conductance_G_edge": (NA if lateral == NA else
            format(float(d(lateral)) * (1.0 / n) * (n / (2.0 * math.pi)) ** 2, ".17g")),
        "G_ref_identity": G_REF_ID, "G_A_identity": f"{G_REF_ID}/N={1/n:.17g}",
        "storage_ratio_S_h": storage,
        "hydraulic_storage_C_h": NA if storage == NA else format(float(d(storage)) / n, ".17g"),
        "derived_Theta_L_m": theta_lateral(n, mode, lateral, storage),
        "machine_response_ratio": theta_m, "machine_compliance_C_u": machine_compliance(theta_m),
        "machine_reference_tuple": MACHINE_TUPLE_ID if pressure == "MACHINE_COUPLED" else NA,
        "resistance_evolution_law": law,
        "resistance_evolution_timescale_ratio": theta_r,
        "resistance_relaxation_tau_R": theta_r, "feedback_sign": sign,
        "feedback_gain": beta,
        "evolution_multiplier_bounds": "[0.25,4]" if law != "NO_EVOLUTION" else NA,
        "shot_duration": "1", "initial_condition_variant": initial,
        "integration_profile": "STATIC_LINEAR_SOLVE_V1" if classifier == "STATIC_CLASSIFIER_V1" else INTEGRATION_PROFILE,
        "numerical_resolution_role": resolution,
        "scientific_role": ("CONTROL" if role == "CONTROL" or lateral == "0" else "SCIENTIFIC"),
        "case_role": ("BOUNDED_STRUCTURAL_CONTROL" if role == "CONTROL" else
                      "STRUCTURAL_COMPARATOR" if lateral == "0" else "ACTIVE_SCIENTIFIC_CASE"),
        "parent_selection_rule": parent, "eligibility": eligibility,
        "static_or_dynamic_classifier": classifier, "comparator_case_id": NA,
        "prescribed_comparator_case_id": NA, "no_evolution_comparator_case_id": NA,
        "model_form_requirement": "CORE_PROVISIONAL;SEPARATE_MODEL_FORM_REVIEW_REQUIRED_BEFORE_SCI_LC_001B_NOMINATION",
        "adaptive_group_id": "", "uncertainty_profile": "ADDITIVE_GAIN_UNCERTAINTY_V2",
        "units_or_dimensionless_status": "DIMENSIONLESS_V1",
    }
    identity = {key: row[key] for key in IDENTITY_FIELDS if key != "case_id"}
    row["case_id"] = f"SCI-LC-001A.{token(arm)}.{digest(identity)[:24]}"
    return row


def comparison_key(row: dict, *, ignore: tuple[str, ...]) -> tuple:
    return tuple((key, row[key]) for key in IDENTITY_FIELDS
                 if key not in set(ignore) | {"case_id"})


def derive_expected_execution_fields(row: dict, canonical_row: dict | None = None) -> dict:
    n = int(row["sector_count"])
    lateral = row["lateral_conductance_ratio"]
    storage = row["storage_ratio_S_h"]
    mode = row["pressure_mode"]
    classifier = "STATIC_CLASSIFIER_V1" if mode == "PRESCRIBED_STATIC" else "DYNAMIC_CLASSIFIER_V1"
    expected = {
        "placement_alpha": PLACEMENT_ALPHA[row["axial_placement"]],
        "G_A_identity": f"{G_REF_ID}/N={1/n:.17g}",
        "lateral_edge_coefficient": edge_coefficient(n, lateral),
        "lateral_edge_conductance_G_edge": (NA if lateral == NA else
            format(float(d(lateral)) * (1.0 / n) * (n / (2.0 * math.pi)) ** 2, ".17g")),
        "hydraulic_storage_C_h": NA if storage == NA else format(float(d(storage)) / n, ".17g"),
        "derived_Theta_L_m": theta_lateral(n, row["heterogeneity_mode"], lateral, storage),
        "machine_compliance_C_u": machine_compliance(row["machine_response_ratio"]),
        "resistance_relaxation_tau_R": row["resistance_evolution_timescale_ratio"],
        "evolution_multiplier_bounds": ("[0.25,4]" if
            row["resistance_evolution_law"] == "SIGNED_LOCAL_FLOW_TO_RESISTANCE_FEEDBACK_SURROGATE" else NA),
        "static_or_dynamic_classifier": classifier,
        "integration_profile": "STATIC_LINEAR_SOLVE_V1" if mode == "PRESCRIBED_STATIC" else INTEGRATION_PROFILE,
        "boundary_profile": {"PRESCRIBED_STATIC": "CONSTANT_BASKET_PRESSURE",
            "PRESCRIBED_DYNAMIC_RAMP": "PIECEWISE_LINEAR_RAMP_TAU_0P05",
            "MACHINE_COUPLED": "WP02_002_LINEAR_SUPPLY_RAMP_TAU_0P05"}[mode],
        "prescribed_pressure_amplitude": (NA if mode == "MACHINE_COUPLED" else
            "1" if mode == "PRESCRIBED_DYNAMIC_RAMP" else
            canonical_row["prescribed_pressure_amplitude"] if canonical_row is not None else row["prescribed_pressure_amplitude"]),
        "machine_reference_tuple": MACHINE_TUPLE_ID if mode == "MACHINE_COUPLED" else NA,
        "feedback_scalar": feedback_sign_scalar(row["feedback_sign"]),
        "case_role": ("BOUNDED_STRUCTURAL_CONTROL" if row["numerical_resolution_role"] in
            ("CONTROL", "STRUCTURAL_NULL_CONTROL") else
            "STRUCTURAL_COMPARATOR" if lateral == "0" else "ACTIVE_SCIENTIFIC_CASE"),
    }
    if canonical_row is not None:
        expected["numerical_resolution_role"] = canonical_row["numerical_resolution_role"]
    return expected


def validate_row_against_expected_fields(row: dict, canonical_by_id: dict[str, dict]) -> None:
    if set(row) != set(FIELDS) or set(FIELD_AUTHORITY) != set(FIELDS):
        raise ValueError("UNKNOWN_OR_UNCLASSIFIED_SERIALIZED_FIELD")
    canonical = canonical_by_id.get(row.get("case_id"))
    if canonical is None:
        raise ValueError("ROW_NOT_IN_FROZEN_STAGE_A_UNIVERSE")
    expected = derive_expected_execution_fields(row, canonical)
    for field, value in expected.items():
        if field != "feedback_scalar" and row[field] != value:
            raise ValueError(f"DERIVED_EXECUTION_FIELD_MISMATCH:{field}")
    identity = {key: row[key] for key in IDENTITY_FIELDS if key != "case_id"}
    expected_case_id = f"SCI-LC-001A.{token(row['arm'])}.{digest(identity)[:24]}"
    if row["case_id"] != expected_case_id:
        raise ValueError("CASE_IDENTITY_MISMATCH")
    expected_hash = digest({key: row[key] for key in FIELDS if key != "row_sha256"})
    if row["row_sha256"] != expected_hash:
        raise ValueError("ROW_HASH_MISMATCH")
    if row != canonical:
        raise ValueError("ROW_DIFFERS_FROM_FROZEN_STAGE_A_CANONICAL_UNIVERSE")


def add_dynamic_pair(rows: list[dict], **kwargs) -> None:
    active = kwargs.pop("lateral")
    kwargs.setdefault("pressure", "PRESCRIBED_DYNAMIC_RAMP")
    rows.append(make_row(lateral="0", **kwargs))
    rows.append(make_row(lateral=active, **kwargs))


def add_static_pair(rows: list[dict], **kwargs) -> None:
    active = kwargs.pop("lateral")
    rows.append(make_row(lateral="0", **kwargs))
    rows.append(make_row(lateral=active, **kwargs))


def build_rows() -> list[dict]:
    rows: list[dict] = []
    # C0 exact identities plus a bounded self-similar structural family.
    for n in (4, 8, 16):
        rows.append(make_row(arm="C0", n=n, pattern="UNIFORM", mode="0", scale="UNIFORM",
                             contrast="1", placement="AXIALLY_SELF_SIMILAR", lateral="0.1",
                             role="CONTROL", resolution="CONTROL", initial="UNIFORM_SYMMETRY"))
    for mode in ("1", "2", "4"):
        for initial in ("BASE_PHASE", "ROTATED_ONE_SECTOR", "REFLECTED"):
            rows.append(make_row(arm="C0", mode=mode, scale=f"MODE_{mode}", lateral="0",
                                 role="CONTROL", resolution="CONTROL", initial=initial))
    for amplitude in ("0.5", "2"):
        rows.append(make_row(arm="C0", pressure="PRESCRIBED_STATIC",
                             pressure_amplitude=amplitude, role="CONTROL",
                             resolution="CONTROL", initial="LINEAR_PRESSURE_SCALING"))
    rows.append(make_row(arm="C0", pressure="MACHINE_COUPLED", pattern="UNIFORM", mode="0",
                         scale="UNIFORM", contrast="1", placement="AXIALLY_SELF_SIMILAR",
                         storage="0.1", theta_m="1", role="CONTROL", resolution="CONTROL",
                         classifier="DYNAMIC_CLASSIFIER_V1", initial="MACHINE_REFERENCE"))
    rows.append(make_row(arm="C0", law="NO_EVOLUTION", theta_r="INFINITE_NO_EVOLUTION",
                         role="CONTROL", resolution="CONTROL", initial="NO_EVOLUTION_LIMIT"))
    for contrast in ("1.5", "4", "16"):
        for mode in ("1", "2", "4"):
            for lateral in ("0", "0.1", "10"):
                for initial in ("BASE_PHASE", "ROTATED_ONE_SECTOR"):
                    rows.append(make_row(arm="C0", contrast=contrast, mode=mode,
                                         scale=f"MODE_{mode}", placement="AXIALLY_SELF_SIMILAR",
                                         lateral=lateral, initial=initial, role="CONTROL",
                                         resolution="STRUCTURAL_NULL_CONTROL",
                                         parent="BOUNDED_SELF_SIMILAR_NULL_FAMILY"))

    # S1: active residual-localized passive atlas only.
    for contrast in CONTRASTS[1:]:
        for lateral in LAMBDAS:
            for mode in ("1", "2", "4"):
                for placement in ACTIVE_PLACEMENTS:
                    rows.append(make_row(arm="S1", contrast=contrast, lateral=lateral,
                                         mode=mode, scale=f"MODE_{mode}", placement=placement))

    patterns = (("CONTIGUOUS_BLOCK", "BLOCK_HALF", "BLOCK_HALF"),
                ("CONTIGUOUS_BLOCK_ROTATED", "BLOCK_HALF", "BLOCK_HALF"),
                ("BROADBAND_SEED_20260816", "BROADBAND", "CORRELATION_2_SECTORS"))
    for pattern, mode, scale in patterns:
        for contrast in ("1.5", "4", "16"):
            for lateral in ("0", "0.01", "0.1", "1", "10"):
                for placement in ACTIVE_PLACEMENTS:
                    rows.append(make_row(arm="S2", pattern=pattern, mode=mode, scale=scale,
                                         contrast=contrast, lateral=lateral, placement=placement,
                                         parent="FROZEN_PATTERN_ROBUSTNESS_SUBSET"))

    # S3 is core-only: fixed-mode sector checks, explicit Nyquist label, and floor sensitivity.
    archetypes = (("1.5", "0.01", "1", "UPSTREAM_LOCALIZED"),
                  ("4", "0.1", "1", "DOWNSTREAM_LOCALIZED"),
                  ("16", "10", "1", "UPSTREAM_LOCALIZED"),
                  ("1.5", "1", "2", "DOWNSTREAM_LOCALIZED"),
                  ("4", "0.03", "2", "UPSTREAM_LOCALIZED"),
                  ("16", "0.3", "2", "DOWNSTREAM_LOCALIZED"))
    for contrast, lateral, mode, placement in archetypes:
        for n in (4, 8, 16):
            add_static_pair(rows, arm="S3", n=n, contrast=contrast, lateral=lateral,
                            mode=mode, scale=f"FIXED_PHYSICAL_MODE_{mode}", placement=placement,
                            resolution="SECTOR_REFINEMENT", parent="EXACT_S1_PARENT_OR_ANALOGUE")
    for n in (8, 16):
        add_static_pair(rows, arm="S3", n=n, contrast="4", lateral="0.1", mode="4",
                        scale="MODE_4_N8_NYQUIST_TO_N16_RESOLVED", placement="UPSTREAM_LOCALIZED",
                        resolution="NYQUIST_TO_RESOLVED_DIAGNOSTIC",
                        parent="EXPLICIT_N8_MODE4_COMPARISON")
    for contrast, lateral, mode, placement in archetypes[:4]:
        for epsilon in FLOOR_LEVELS:
            add_static_pair(rows, arm="S3", contrast=contrast, lateral=lateral, mode=mode,
                            scale=f"MODE_{mode}", placement=placement, epsilon=epsilon,
                            resolution="FLOOR_SENSITIVITY", parent="BOUNDED_FLOOR_SENSITIVITY")

    dynamic_parents = (("1.5", "0.01", "1", "UPSTREAM_LOCALIZED"),
                       ("4", "0.1", "2", "DOWNSTREAM_LOCALIZED"),
                       ("16", "10", "4", "UPSTREAM_LOCALIZED"),
                       ("4", "1", "1", "DOWNSTREAM_LOCALIZED"),
                       ("16", "0.03", "2", "UPSTREAM_LOCALIZED"),
                       ("1.5", "0.3", "4", "DOWNSTREAM_LOCALIZED"))
    for contrast, lateral, mode, placement in dynamic_parents:
        for storage in S_H_LEVELS:
            add_dynamic_pair(rows, arm="D1", contrast=contrast, lateral=lateral, mode=mode,
                             scale=f"MODE_{mode}", placement=placement, storage=storage,
                             parent="FROZEN_STATIC_REPRESENTATIVE",
                             classifier="DYNAMIC_CLASSIFIER_V1")

    for contrast, lateral, mode, placement in dynamic_parents[:4]:
        for storage in ("0.1", "1", "10"):
            for pressure, theta_m in (("PRESCRIBED_DYNAMIC_RAMP", NA),) + tuple(
                    ("MACHINE_COUPLED", value) for value in THETA_M):
                add_dynamic_pair(rows, arm="D2", contrast=contrast, lateral=lateral, mode=mode,
                                 scale=f"MODE_{mode}", placement=placement, storage=storage,
                                 pressure=pressure, theta_m=theta_m,
                                 parent="FROZEN_MACHINE_INTERACTION_SUBSET",
                                 classifier="DYNAMIC_CLASSIFIER_V1")

    for arm, sign in (("D3-EQ", "EQUALIZING"), ("D3-LOC", "LOCALIZING")):
        for contrast, lateral, mode, placement in dynamic_parents[:3]:
            for beta in BETAS:
                for theta_r in THETA_R:
                    add_dynamic_pair(rows, arm=arm, contrast=contrast, lateral=lateral, mode=mode,
                                     scale=f"MODE_{mode}", placement=placement, storage="1",
                                     law="SIGNED_LOCAL_FLOW_TO_RESISTANCE_FEEDBACK_SURROGATE",
                                     theta_r=theta_r, sign=sign, beta=beta,
                                     parent="FROZEN_FEEDBACK_SUBSET",
                                     classifier="DYNAMIC_CLASSIFIER_V1")
    bind_relationships(rows)
    return rows


def bind_relationships(rows: list[dict]) -> None:
    by_key: dict[tuple, dict] = {}
    for row in rows:
        key = comparison_key(row, ignore=("lateral_conductance_ratio", "lateral_edge_coefficient",
                                          "lateral_edge_conductance_G_edge", "derived_Theta_L_m",
                                          "scientific_role", "case_role"))
        if row["lateral_conductance_ratio"] == "0":
            by_key[key] = row
    for row in rows:
        if row["case_role"] == "ACTIVE_SCIENTIFIC_CASE":
            key = comparison_key(row, ignore=("lateral_conductance_ratio", "lateral_edge_coefficient",
                                              "lateral_edge_conductance_G_edge", "derived_Theta_L_m",
                                              "scientific_role", "case_role"))
            row["comparator_case_id"] = by_key[key]["case_id"]

    prescribed = {}
    for row in rows:
        if row["arm"] == "D2" and row["pressure_mode"] == "PRESCRIBED_DYNAMIC_RAMP":
            key = comparison_key(row, ignore=("pressure_mode", "boundary_profile",
                                              "prescribed_pressure_amplitude", "machine_response_ratio",
                                              "machine_compliance_C_u", "machine_reference_tuple"))
            prescribed[key] = row
    for row in rows:
        if row["arm"] == "D2" and row["pressure_mode"] == "MACHINE_COUPLED":
            key = comparison_key(row, ignore=("pressure_mode", "boundary_profile",
                                              "prescribed_pressure_amplitude", "machine_response_ratio",
                                              "machine_compliance_C_u", "machine_reference_tuple"))
            row["prescribed_comparator_case_id"] = prescribed[key]["case_id"]

    no_evolution = {}
    for row in rows:
        if row["arm"] == "D1" and row["storage_ratio_S_h"] == "1":
            key = comparison_key(row, ignore=("arm", "resistance_evolution_law",
                "resistance_evolution_timescale_ratio", "resistance_relaxation_tau_R",
                "feedback_sign", "feedback_gain",
                "evolution_multiplier_bounds", "parent_selection_rule"))
            no_evolution[key] = row
    for row in rows:
        if row["arm"] in ("D3-EQ", "D3-LOC"):
            key = comparison_key(row, ignore=("arm", "resistance_evolution_law",
                "resistance_evolution_timescale_ratio", "resistance_relaxation_tau_R",
                "feedback_sign", "feedback_gain",
                "evolution_multiplier_bounds", "parent_selection_rule"))
            row["no_evolution_comparator_case_id"] = no_evolution[key]["case_id"]

    group_ignore = ("case_id", "lateral_conductance_ratio", "lateral_edge_coefficient",
                    "lateral_edge_conductance_G_edge", "derived_Theta_L_m")
    for row in rows:
        row["adaptive_group_id"] = "D4G-" + digest({key: row[key] for key in IDENTITY_FIELDS
                                                     if key not in group_ignore})[:20]
        row["row_sha256"] = digest({key: row[key] for key in FIELDS if key != "row_sha256"})


def d4_select_synthetic(*_args: object, **_kwargs: object) -> list[dict]:
    """Fail closed: Stage A cannot materialize D4 rows."""
    raise DeferredStageError(D4_AUTHORITY_STOP)


def x1_select_synthetic(*_args: object, **_kwargs: object) -> list[dict]:
    """Fail closed: Stage A cannot nominate SCI-LC-001B cases."""
    raise DeferredStageError(X1_STATUS)


def protocol(rows: list[dict]) -> dict:
    counts = Counter(row["arm"] for row in rows)
    controls = sum(row["scientific_role"] == "CONTROL" for row in rows)
    dynamic = sum(row["static_or_dynamic_classifier"] == "DYNAMIC_CLASSIFIER_V1" for row in rows)
    comparators = sum(row["comparator_case_id"] != NA for row in rows)
    dynamic_bindings = sum(row["comparator_case_id"] != NA and
                           row["static_or_dynamic_classifier"] == "DYNAMIC_CLASSIFIER_V1"
                           for row in rows)
    comparator_rows = sum(row["static_or_dynamic_classifier"] == "DYNAMIC_CLASSIFIER_V1"
                          and row["case_role"] == "STRUCTURAL_COMPARATOR" for row in rows)
    static_comparator_rows = sum(row["static_or_dynamic_classifier"] == "STATIC_CLASSIFIER_V1"
                                 and row["case_role"] == "STRUCTURAL_COMPARATOR" for row in rows)
    matrix_hash = digest([{key: row[key] for key in FIELDS} for row in rows])
    graph = execution_graph(rows)
    graph_summary = {key: value for key, value in graph.items() if key != "keys"}
    sector_audit = sector_bundle_audit(rows)
    return {
        "schema_version": "ewp.sci_lc_001a.protocol.v2",
        "task_id": TASK_ID, "status": STATUS, "base_head": BASE_HEAD, "base_tree": BASE_TREE,
        "reviewed_head": REVIEWED_HEAD, "reviewed_tree": REVIEWED_TREE,
        "c1_head": C1_HEAD, "c1_tree": C1_TREE,
        "c2_reviewed_head": C2_HEAD, "c2_reviewed_tree": C2_TREE,
        "c3_reviewed_head": C3_HEAD, "c3_reviewed_tree": C3_TREE,
        "c4_reviewed_head": C4_HEAD, "c4_reviewed_tree": C4_TREE,
        "c5_reviewed_head": C5_HEAD, "c5_reviewed_tree": C5_TREE,
        "change_declaration": "NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE",
        "evidence_mode": "PROSPECTIVE_REDUCED_MODEL_PROTOCOL_CORRECTION",
        "execution_authorized": False,
        "stage_a_initial_condition_scope": {
            "architecture_id": ARCHITECTURE_ID,
            "authority_status": "FROZEN_PENDING_INDEPENDENT_REVIEW",
            "initial_condition_classification_authority_status": INITIAL_CONDITION_AUTHORITY_STATUS,
            "dynamic_initial_state_variant": DYNAMIC_INITIAL_STATE_VARIANT,
            "dynamic_initial_state": {"internal_sector_pressure": 0.0,
                "machine_pressure_where_applicable": 0.0,
                "resistance_feedback_state_x_i_where_applicable": 0.0},
            "dynamic_scope": DYNAMIC_INITIAL_CONDITION_SCOPE,
            "static_dynamic_initial_state_variant": STATIC_INITIAL_STATE_VARIANT,
            "static_scope": STATIC_INITIAL_CONDITION_SCOPE,
            "initial_condition_robustness": NOT_ADJUDICATED_STAGE_A,
            "bistability_status": NOT_ADJUDICATED_STAGE_A,
            "initial_condition_dependence_branch": INITIAL_CONDITION_BRANCH_STATUS,
            "legacy_initial_condition_variant_semantics": LEGACY_REALIZATION_SEMANTICS,
            "cache_identity": "(case_id,numerical_profile)",
            "d4_alternate_initial_state_construction":
                "UNFROZEN_PENDING_SEPARATE_OWNER_SCIENTIFIC_DESIGN",
            "d4_status": D4_STATUS, "x1_status": X1_STATUS,
            "physical_validation": "NOT_ESTABLISHED"},
        "field_authority_classes": list(FIELD_AUTHORITY_CLASSES),
        "field_authority": FIELD_AUTHORITY,
        "scientific_question": ("Under what combinations of lateral conductance, axial resistance contrast, "
            "heterogeneity scale, machine response, and resistance-evolution timescale does puck "
            "nonuniformity decay, persist, or amplify?"),
        "review_findings_corrected": ["PROPORTIONAL_SPLIT_STATIC_NULL", "EVOLUTION_PLACEMENT_UNDERSPECIFIED",
            "PRIMITIVE_MAPPING_INCOMPLETE", "BOUNDARY_INITIAL_INTEGRATION_INCOMPLETE",
            "MULTILAYER_NOT_EXECUTABLE", "ADAPTIVE_RULES_NOT_MATERIALIZABLE",
            "UNCERTAINTY_RULE_DISAGREEMENT", "CLASSIFIER_AND_COMPARATOR_INCOMPLETE"],
        "hypotheses": {"H0": "uncoupled persistence", "H1": "passive equalization",
            "H2": "passive focusing", "H3": "scale dependence",
            "H4": "machine structural invariance in fixed linear quasi-steady limit",
            "H5": "signed generic resistance feedback", "H6": "reduced disagreement prioritizes 3-D"},
        "claim_boundary": {"PHYSICAL_VALIDATION": "NOT_ESTABLISHED",
            "GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION": "NOT_ESTABLISHED",
            "OPENFOAM_EXECUTION_IN_THIS_TASK": "NONE", "PUCKWORKS_EXECUTION_IN_THIS_TASK": "NONE",
            "REAL_PUCK_LATERAL_CONDUCTANCE": "NOT_MEASURED",
            "UNIVERSAL_LATERAL_COUPLING_PARAMETER": "NOT_ESTABLISHED",
            "RP_D_LC_001B_XI_ROLE": "SYNTHETIC_NUMERICAL_CONTEXT_ONLY",
            "SCI_LC_001A_ROLE": "REDUCED_DIAGNOSTIC_PHASE_DIAGRAM"},
        "scales": {"Delta_p_ref": "1 dimensionless pressure scale", "T_shot": "1 dimensionless time scale",
            "G_ref": "1 whole-network conductance", "G_A": "G_ref/N",
            "p_hat": "(p-p_o)/Delta_p_ref", "tau": "t/T_shot",
            "q_hat": "q/(G_A*Delta_p_ref)"},
        "resistance_construction": {"epsilon_floor": EPSILON_FLOOR,
            "conductance_normalization": "g_tilde_i=exp(-a_h*h_i)/sum_j(a_j*exp(-a_h*h_j))",
            "sector_conductance": "G_i=a_i*G_ref*g_tilde_i", "total_path": "T_i=1/G_i",
            "common_floor": "R_floor=epsilon_floor*min_i(T_i)", "residual": "H_i=T_i-2*R_floor",
            "upstream": "R_u_i=R_floor+alpha_place*H_i",
            "downstream": "R_d_i=R_floor+(1-alpha_place)*H_i",
            "placement_alpha": PLACEMENT_ALPHA, "required": ["H_i>0", "sum_i G_i=G_ref",
                "R_u_i+R_d_i=T_i", "max(T_i)/min(T_i)=chi_R"]},
        "lateral_operator": {"operator": "L_N p_i=(N/(2*pi))^2*(2*p_i-p_i-1-p_i+1)",
            "eigenvalue": "4*(N/(2*pi))^2*sin(pi*m/N)^2",
            "edge_conductance": "G_edge=Lambda*G_A*(N/(2*pi))^2"},
        "storage_mapping": {"axis": "S_h=C_h/(G_A*T_shot)", "levels": list(S_H_LEVELS),
            "primitive": "C_h=S_h*G_A*T_shot", "derived": "Theta_L_m=S_h/(Lambda*lambda_N(m))",
            "zero_coupling": INFINITE},
        "boundary_modes": {
            "closed_enumeration": list(BOUNDARY_MODES),
            "field_disposition_values": list(FIELD_DISPOSITIONS),
            "field_dispositions": {mode: boundary_field_dispositions(mode) for mode in BOUNDARY_MODES},
            "unassigned_field_count": 0, "fallback_provenance_count": 0,
            "explicit_provenance_counts": {mode: sum(value == "PROVENANCE_ONLY" for value in
                boundary_field_dispositions(mode).values()) for mode in BOUNDARY_MODES},
            "PRESCRIBED_STATIC": {"unknowns": ["p_i"], "prescribed": ["p_o_hat=0", "p_b_hat=amplitude"],
                "equations": "algebraic conservative node balance", "integration_profile": "STATIC_LINEAR_SOLVE_V1",
                "required": ["prescribed_pressure_amplitude"],
                "prohibited": ["storage_ratio_S_h", "hydraulic_storage_C_h", "derived_Theta_L_m",
                    "machine_response_ratio", "machine_reference_tuple", "machine_compliance_C_u"]},
            "PRESCRIBED_DYNAMIC_RAMP": {"unknowns": ["p_i(tau)"],
                "prescribed": ["p_o_hat=0", "p_b_hat=min(tau/0.05,1)"],
                "equations": "C_h dp_i/dt=q_u_i-q_d_i-j_plus+j_minus",
                "initial": "p_i(0)=0", "integration_profile": INTEGRATION_PROFILE,
                "required": ["storage_ratio_S_h", "hydraulic_storage_C_h"],
                "prohibited": ["machine_response_ratio", "machine_reference_tuple", "machine_compliance_C_u"],
                "amplitude_field_semantics": "derived terminal ramp amplitude; not a static pressure prescription"},
            "MACHINE_COUPLED": {"unknowns": ["p_i(tau)", "p_u(tau)", "p_b(tau)"],
                "prescribed": ["p_o_hat=0", "command=min(tau/0.05,1)"],
                "equations": ["C_h dp_i/dt=q_u_i-q_d_i-j_plus+j_minus",
                    "C_u dp_u/dt=Q_supply-Q_puck", "p_b=p_u-R_line*Q_puck"],
                "initial": "p_i(0)=p_u(0)=0", "integration_profile": INTEGRATION_PROFILE,
                "required": ["storage_ratio_S_h", "hydraulic_storage_C_h", "machine_response_ratio",
                    "machine_reference_tuple", "machine_compliance_C_u"],
                "prohibited": ["prescribed_pressure_amplitude"]}},
        "machine_reference": {"id": MACHINE_TUPLE_ID, "p_o": "0", "p_shut": "1", "q_free": "1",
            "R_line": "0.1", "supply_law": "q_free*ramp(tau)*max(1-(p_u-p_o)/(p_shut-p_o),0)",
            "initial_p_u": "0", "G_ref": "1", "G_load": "10/11", "a_eff": "21/11",
            "Theta_M_levels": list(THETA_M), "C_u_mapping": "C_u=Theta_M*T_shot*(21/11)",
            "basket_relation": "p_b=p_u-R_line*Q_puck"},
        "resistance_evolution": {"name": "SIGNED_LOCAL_FLOW_TO_RESISTANCE_FEEDBACK_SURROGATE",
            "equations": ["Theta_R*dx_i/dtau=s*(F_i-1)-x_i", "H_i(t)=H_i0*exp(beta*x_i)",
                "R_u_i=R_floor+alpha_place*H_i(t)", "R_d_i=R_floor+(1-alpha_place)*H_i(t)"],
            "initial_x_i": "0", "feedback_sign_scalar": FEEDBACK_SIGN_SCALARS,
            "sign_interpretation": {"EQUALIZING": "F_i>1 increases x_i,H_i,total resistance and suppresses high flow",
                "LOCALIZING": "F_i>1 decreases x_i,H_i,total resistance and reinforces high flow",
                "placement": "changes split but not sign of total resistance response"},
            "allowed_active_Theta_R": list(THETA_R),
            "no_evolution_variants": {
                "NO_EVOLUTION_BETA_ZERO": ["NO_EVOLUTION", "NONE", "0", NA, NA, NA],
                "NO_EVOLUTION_INFINITE_RELAXATION": ["NO_EVOLUTION", "NONE", "0",
                    "INFINITE_NO_EVOLUTION", "INFINITE_NO_EVOLUTION", NA]},
            "multiplier_admissible_interval": "0.25 <= H_i/H_i0 <= 4.0",
            "stop_rule": "outward crossing only; exact inward or tangential contact is admissible",
            "boundary_atol": MULTIPLIER_BOUNDARY_ATOL,
            "derivative_atol": MULTIPLIER_DERIVATIVE_ATOL,
            "event_root_value_atol": EVENT_ROOT_VALUE_ATOL,
            "state_contexts": list(MULTIPLIER_CONTEXTS),
            "outward_crossing_disposition": MULTIPLIER_STOP,
            "diagnostic_reconstruction_at_contact": True,
            "no_evolution": ["beta=0", "Theta_R=INFINITE_NO_EVOLUTION"],
            "fast_control": "Theta_R=0.03", "aggregate_renormalization": "NONE",
            "zero_flow_startup": {"dynamic_limit": "F_i=N*(G_u_i*G_d_i/C_h_i)/sum_j(G_u_j*G_d_j/C_h_j)",
                "machine_note": "machine compliance changes only the common leading time coefficient",
                "q_hat_zero_threshold": "1e-14", "startup_tau_max": "1e-6",
                "Q_hat_total": "Q_total/(G_ref*Delta_p_ref)=(1/N)*sum_i q_hat_i",
                "flow_scale_enumeration": list(FLOW_SCALES),
                "authoritative_input": "SectorFlowVector(values,N,scale,G_ref,delta_p_ref)",
                "unsupported_scale": "WHOLE_NETWORK_SCALED_PER_SECTOR",
                "branch_operators": "abs(Q_hat_total)<=q_threshold and tau<=startup_tau_max",
                "refinement_factor": "10", "refined_q_hat_zero_threshold": "1e-15",
                "refined_startup_tau_max": "1e-7",
                "companion": "same case; only both startup thresholds divided by 10",
                "uncertainty": "u_startup(G)=abs(G_base_thresholds-G_refined_thresholds)",
                "unavailable_or_stopped": "NUMERICALLY_UNRESOLVED;NO_CLASSIFICATION",
                "exact_zero": "use analytical limit only within startup window",
                "below_threshold": "use same branch and require threshold-refinement uncertainty",
                "flow_reversal": "STOP_UNEXPECTED_FLOW_REVERSAL",
                "nonfinite": "STOP_NONFINITE_SECTOR_FLOW",
                "zero_sector_positive_total": "F_i=0"}},
        "boundary_initial_integration": {"p_o_hat": "0", "static_p_b_hat": "1",
            "dynamic_p_b_hat": "min(tau/0.05,1)", "tau_ramp": "0.05", "shot_horizon": ["0", "1"],
            "initial_internal_p_hat": "0", "initial_machine_p_u_hat": "0", "initial_feedback_x": "0",
            "primary_fourier_phase": "0", "rotation": "i->(i+1) mod N", "reflection": "i->(-i) mod N",
            "historical_alternate_amplitudes": {"values": ["0.5", "1.5"],
                "status": HISTORICAL_ALTERNATE_STATUS,
                "production_or_planning_use": "PROHIBITED"},
            "phase_reversal": "HISTORICAL_UNFROZEN_D4_CONCEPT_NOT_EXECUTABLE_STAGE_A",
            "output_grid": "tau_k=k/1000,k=0..1000", "base_method": "DOP853",
            "base_rtol": "1e-8", "base_atol": "1e-10", "base_max_step": "0.0025",
            "refined_method": "DOP853", "refined_rtol": "2.5e-9", "refined_atol": "2.5e-11",
            "refined_max_step": "0.00125", "solver_api": "scipy.integrate.solve_ivp",
            "dynamic_first_step": DYNAMIC_FIRST_STEP,
            "dynamic_first_step_scope": "all dynamic profiles and both dynamic boundary modes",
            "maximum_rhs_evaluations": MAX_RHS_EVALUATIONS,
            "rhs_counter": "increments before every RHS call, including rejected trial steps",
            "cap_operator": "if nfev>=200000 before next evaluation: stop",
            "cap_disposition": "STOP_MAX_RHS_EVALUATIONS_REACHED;PARTIAL_DIAGNOSTIC_INADMISSIBLE",
            "events": {"lower": "exp(beta*x_i)-0.25", "upper": "4-exp(beta*x_i)",
                "direction": "-1", "terminal": True, "boundary_contact_stops": False,
                "exact_boundary": "directional outward event stops; inward/tangential event does not fire",
                "tangential_or_inward_contact": "ADMISSIBLE_NO_TERMINAL_EVENT",
                "terminal_event_continue_path": "ABSENT", "post_event_dense_output": "PROHIBITED",
                "post_event_counted_rhs_call": "ABSENT", "rhs_count_requirement": "wrapper_count==solve_ivp.nfev",
                "root_time_tolerance": "1e-10 tau", "earliest": "minimum root time",
                "tie_break": "LOWER_BOUND before UPPER_BOUND, then ascending sector index",
                "nonfinite": "STOP_NONFINITE_EVENT_FUNCTION",
                "event_cap_order": "located event in accepted dense-output step precedes later cap; cap precedes unevaluated event"},
            "failure": "NUMERICALLY_UNRESOLVED;NO_CLASSIFICATION"},
        "residual_contract": {
            "linear": {"vector": "r=A*p-b", "scale": "s_i=max(abs(b_i),sum_j(abs(A_ij)*abs(p_j)),1e-14)",
                "norm": "max_i(abs(r_i)/s_i)", "tolerance": "1e-12", "operator": "<=", "retry": "NONE"},
            "BASE": {"api": "sci_lc_001a_protocol.solve_dense_binary64",
                "dtype": "IEEE-754 binary64", "layout": "canonical logical row-major",
                "algorithm": "dense Gaussian elimination with scaled partial pivoting",
                "pivot_ratio_floor": PIVOT_RATIO_FLOOR,
                "pivot_tie_break": "lowest original canonical row index", "caller_state_allowed": False},
            "LINEAR_REFINED": {"api": "sci_lc_001a_protocol.linear_refined_state",
                "algorithm": "authoritative BASE then one correction using identical binary64 scaled-pivot solver",
                "steps": ["r0=A*p0-b", "solve A*delta_p=-r0 exactly once", "p1=p0+delta_p",
                    "require residual1<=1e-12 and residual1<=residual0+monotonicity_atol"],
                "monotonicity_atol": LINEAR_REFINEMENT_MONOTONICITY_ATOL,
                "monotonicity_atol_identity": "PIVOT_RATIO_FLOOR=64*epsilon_binary64",
                "base_source": "solve_dense_binary64(A,b); external p0 prohibited",
                "dynamic_application": "separate complete trajectory; correction at every algebraic solve",
                "failure": "NUMERICALLY_UNRESOLVED;NO_RETRY_OR_SUBSTITUTION"},
            "stage_a_nonlinear_fixed_point_solve": "NOT_USED",
            "nonfinite": "NUMERICAL_STOP_NONFINITE_RESIDUAL", "failure_route": "BEFORE_SCIENTIFIC_CLASSIFIER"},
        "model_form": {"initial_variant": "CORE_ONE_EXCHANGE_PLANE_ONLY",
            "multilayer_rows": 0, "reason": "independent review found the prior placeholder non-executable",
            "broad_core_status": "PROVISIONAL_CORE_CLASSIFICATION",
            "nomination_gate": "SEPARATE_REVIEWED_MODEL_FORM_CHECK_REQUIRED_BEFORE_SCI_LC_001B_NOMINATION"},
        "observables": ["H_q", "CV_q", "A_eff", "seeded_mode_amplitude", "J_L_abs", "J_L_net",
            "pressure_CV", "G_static_H", "G_static_mode", "G_coupling_end", "G_coupling_int",
            "sigma_m", "conservation", "dissipation", "selected_extraction_diagnostics"],
        "owner_metric_authority": {
            "owner_metric_authority_id": OWNER_METRIC_AUTHORITY_ID,
            "effective_at": "E2-R1 exact commit; no prior result is reinterpreted",
            "sector_indexing": "i=0,...,N-1",
            "flow_fraction_definition": "f_i=q_i/sum_j(q_j)",
            "flow_departure_definition": "d_i=f_i-1/N",
            "H_q_definition": "H_q=(1/2)*sum_i(abs(d_i))",
            "H_q_denominator_floor": H_Q_DENOMINATOR_FLOOR,
            "zero_time_dynamic_fraction": "f_i(0)=F_i(0+)/N from analytical startup focusing",
            "current_resistance": ["M_i=exp(beta*x_i)", "H_i=H_i0*M_i",
                "R_u_i=R_floor+alpha_place*H_i", "R_d_i=R_floor+(1-alpha_place)*H_i",
                "G_d_i=1/R_d_i", "q_i=G_d_i*(p_i-p_o)"],
            "static_H": {"primitive": "H_q_static", "gain": "G_static_H=H_q_active/H_q_comparator",
                "comparator": "exact Lambda=0", "denominator_floor": H_Q_DENOMINATOR_FLOOR},
            "static_mode": {"primitive": "A_seeded", "fourier_C_m": "sum_i(d_i*cos(2*pi*m*i/N))",
                "fourier_S_m": "sum_i(d_i*sin(2*pi*m*i/N))",
                "ordinary_fourier_normalization": "A_seeded=(2/N)*sqrt(C_m^2+S_m^2)",
                "nyquist_normalization": "A_seeded=abs(C_m)/N when N even and m=N/2",
                "phase_rotation_reflection": "magnitude invariant; no phase-zero projection",
                "non_fourier_seed_source": "pattern_values(validated canonical row)",
                "centered_seed": "s_i=h_i-mean(h)",
                "least_squares_amplitude": "A_seeded=abs(sum_i(d_i*s_i))/sum_i(s_i^2)",
                "uniform_disposition": NA, "denominator_floor": SEEDED_MODE_AMPLITUDE_FLOOR,
                "gain": "G_static_mode=A_seeded_active/A_seeded_comparator"},
            "dynamic_endpoint": {"final_state_required": "complete admissible tau=1 trajectory",
                "evolved_resistance_reconstruction": True, "primitive": "H_q(1)",
                "gain": "G_coupling_end=H_q_active(1)/H_q_comparator(1)",
                "stopped_or_capped": "NUMERICALLY_UNRESOLVED"},
            "dynamic_integrated": {"interval": "[0,1]", "primary_grid_points": 1001,
                "companion_grid_points": 2001, "quadrature": "COMPOSITE_TRAPEZOIDAL",
                "weights": {"endpoint": "1/2", "interior": "1", "delta_tau": "1/(M-1)"},
                "tau_zero": "analytical startup fractions", "active_reconstruction": "separate H_q grid",
                "comparator_reconstruction": "separate H_q grid",
                "gain": "G_coupling_int_M=I_M_active/I_M_comparator",
                "primary_reported_grid": 1001, "denominator_floor": GAIN_DENOMINATOR_FLOOR},
            "sampling": {"formula": "abs(G_coupling_int_1001-G_coupling_int_2001)",
                "same_base_dense_output": True, "additional_trajectory_count": 0,
                "applicability": {"STATIC_GAIN": NA, "DYNAMIC_ENDPOINT_GAIN": NA,
                    "DYNAMIC_INTEGRATED_GAIN": "APPLICABLE"}},
            "classifier_binding": {"static": ["G_static_H", "G_static_mode"],
                "dynamic": ["G_coupling_end", "G_coupling_int"]}},
        "denominator_floors": {"H_q": "1e-12", "seeded_mode_amplitude": "1e-12",
            "total_flow": "1e-14", "generic_ratio_denominator": "1e-12",
            "fallback": {"uniform": "STRUCTURAL_IDENTITY", "fourier": "USE_SEEDED_MODE_IF_H_Q_FLOORED",
                         "otherwise": "NUMERICALLY_UNRESOLVED"}},
        "gain_authority": {"record": "GainRecord", "constructor": "build_gain_record",
            "subject": "validated canonical ACTIVE_SCIENTIFIC_CASE",
            "comparator": "resolved internally and validated as exact Lambda-zero STRUCTURAL_COMPARATOR",
            "denominator_required": True, "denominator_default": False,
            "denominator_floor_constant": "GAIN_DENOMINATOR_FLOOR=1e-12",
            "caller_floor_override": False,
            "gate": "abs(denominator)<=denominator_floor -> NUMERICALLY_UNRESOLVED",
            "structural_control_path": "distinct; ordinary gain construction prohibited"},
        "uncertainty": {"allowed_ceiling": "u_limit(G)=min(0.02,0.02*abs(G))",
            "rationale": "2-percent relative ceiling capped at 0.02 gain units; exact structural identities use analytical preclassification",
            "components": {
                "u_integrator": "abs(G_base-G_refined) from required DOP853 companion",
                "u_sector": "abs(G_N-G_Nref); applies only to SECTOR_REFINEMENT 4->8 or 8->16 and NYQUIST 8->16",
                "u_linear": "abs(G_BASE-G_LINEAR_REFINED)",
                "u_sampling": "abs(G_1001-G_2001) reconstructed from the same accepted dense output",
                "u_startup": "abs(G_base_startup_thresholds-G_refined_startup_thresholds)"},
            "combination": "u_G=u_integrator+u_sector+u_linear+u_sampling+u_startup",
            "applicability_authority": "derive_uncertainty_contract(canonical_rows,subject_case_id,metric,evaluation,status,profile)",
            "applicability_table": {
                "STATIC_GAIN": [NA, "SECTOR_PREDICATE", "APPLICABLE", NA, NA],
                "DYNAMIC_ENDPOINT_GAIN": ["APPLICABLE", "SECTOR_PREDICATE", "APPLICABLE", NA, "APPLICABLE"],
                "DYNAMIC_INTEGRATED_GAIN": ["APPLICABLE", "SECTOR_PREDICATE", "APPLICABLE", "APPLICABLE", "APPLICABLE"],
                "STATIC_STRUCTURAL_NUMERICAL_CONTROL": [NA, "SECTOR_PREDICATE", "APPLICABLE", NA, NA],
                "DYNAMIC_ENDPOINT_STRUCTURAL_NUMERICAL_CONTROL": ["APPLICABLE", "SECTOR_PREDICATE", "APPLICABLE", NA, "APPLICABLE"],
                "DYNAMIC_INTEGRATED_STRUCTURAL_NUMERICAL_CONTROL": ["APPLICABLE", "SECTOR_PREDICATE", "APPLICABLE", "APPLICABLE", "APPLICABLE"]},
            "sentinels": {"finite_nonnegative": "include once", "NOT_APPLICABLE": "zero only when predicate false",
                "NOT_APPLICABLE_REQUIRED": "AUTHORITY_OR_ARTIFACT_INVALID", "UNAVAILABLE": "NUMERICALLY_UNRESOLVED",
                "missing_negative_nonfinite_unsupported": "AUTHORITY_OR_ARTIFACT_INVALID"},
            "sector_refinement": {"SECTOR_REFINEMENT": {"4": 8, "8": 16, "16": NA},
                "NYQUIST_TO_RESOLVED_DIAGNOSTIC": {"8": 16},
                "identity": "all scientific primitives equal except N and N-derived G_A,C_h,G_edge,Theta_L and IDs"},
            "denominator_allocation": "denominator residual error occurs once in u_linear; denominator floor is validity gate, not additive uncertainty",
            "units": "all components are absolute gain units", "operator": "u_G<=u_limit(G)",
            "unavailable": "NUMERICALLY_UNRESOLVED", "stopped": "UNAVAILABLE;NO_CLASSIFICATION",
            "model_form": "SEPARATE_TRANSITION_REASON_NOT_SCALAR_ERROR"},
        "numerical_execution_graph": {**graph_summary,
            "dynamic_profiles": list(DYNAMIC_NUMERICAL_PROFILES),
            "static_profiles": list(STATIC_NUMERICAL_PROFILES),
            "gain_components": {"u_integrator": "abs(G_BASE-G_INTEGRATOR_REFINED)",
                "u_startup": "abs(G_BASE-G_STARTUP_REFINED)",
                "u_linear": "abs(G_BASE-G_LINEAR_REFINED)",
                "u_sampling": "abs(G_1001_FROM_BASE-G_2001_FROM_BASE)",
                "u_sector": "abs(G_N_BASE-G_NREF_BASE)"},
            "sector_bundle_audit": sector_audit},
        "stage_a_executor": {"module": "scripts/sci_lc_001a_executor.py",
            "status": "E2_R3_DYNAMIC_RUNTIME_CORRECTION_PENDING_REVIEW",
            "modes": ["plan", "validate", "execute", "summarize", "pilot-plan", "pilot-execute"],
            "public_real_execution_api": "execute_authorized_graph",
            "public_real_execution_launcher_parameter": False,
            "canonical_dispatcher": "_execute_canonical_case",
            "private_case_executors": ["_execute_static_case", "_execute_dynamic_case"],
            "execution_authority_required": True, "real_execution_authority_created": False,
            "output": "absolute external non-symlink result root; atomic JSON records",
            "resume": "manifest-identity and checksum-ledger bound records; no cross-run reuse or automatic retry",
            "synthetic_backend": "SYNTHETIC_TEST_ONLY; scientifically inadmissible",
            "pilot": {"status": "CANONICAL_ADAPTER_IMPLEMENTED_PENDING_E2_R3_REVIEW", "authority_created": False,
                "allowlist_required": True, "reuse": "DISABLED", "evidence_kind": "DIAGNOSTIC_TIMING_ONLY",
                "public_launcher_parameter": False, "canonical_adapter": "_execute_canonical_pilot_case",
                "wall_time_source": "time.perf_counter_ns around canonical case calculation",
                "cpu_time_source": "time.process_time_ns around canonical case calculation",
                "output_size_definition": "serialized canonical case-outcome bytes before diagnostic filtering",
                "implementation_exception": "manifest INFRASTRUCTURE_FAILURE; abort before next key; no retry",
                "unknown_rhs_count": "null;NOT_AVAILABLE_DUE_TO_IMPLEMENTATION_EXCEPTION",
                "projection_exclusion": ["IMPLEMENTATION_EXCEPTION", "SHARED_INFRASTRUCTURE_FAILURE"],
                "scientific_evidence": False},
            "timing_pilot_authorized": False, "scientific_execution_authorized": False},
        "classification": {"static": {"metrics": ["G_static_H", "G_static_mode"],
                "comparator": "exact same-row identity with Lambda=0"},
            "dynamic": {"metrics": ["G_coupling_end", "G_coupling_int"],
                "comparator": "materialized Lambda=0 with same storage,evolution,boundary,machine,initial,numerics"},
            "thresholds": {"equalization": "0.90", "amplification": "1.10"},
            "initial_condition_reconciliation": {
                "status": INITIAL_CONDITION_AUTHORITY_STATUS,
                "architecture_id": ARCHITECTURE_ID,
                "serialized_field": "initial_condition_variant",
                "serialized_field_semantics": LEGACY_REALIZATION_SEMANTICS,
                "stage_a_dynamic_scope": DYNAMIC_INITIAL_CONDITION_SCOPE,
                "stage_a_static_scope": STATIC_INITIAL_CONDITION_SCOPE,
                "initial_condition_robustness": NOT_ADJUDICATED_STAGE_A,
                "bistability_status": NOT_ADJUDICATED_STAGE_A,
                "initial_condition_dependence_branch": INITIAL_CONDITION_BRANCH_STATUS,
                "reserved_future_label": "INITIAL_CONDITION_DEPENDENT_OR_BISTABLE",
                "reserved_future_label_stage_a_status": NOT_ADJUDICATED_STAGE_A,
                "hidden_runs_authorized": False,
                "d4_alternate_initial_state_construction":
                    "UNFROZEN_PENDING_SEPARATE_OWNER_SCIENTIFIC_DESIGN"},
            "precedence": ["AUTHORITY_OR_ARTIFACT_INVALID", "ANALYTICAL_STRUCTURAL_IDENTITY",
                "NUMERICALLY_UNRESOLVED", "MODEL_FORM_OR_SECTOR_RESOLUTION_DISAGREEMENT", "METRIC_DISAGREEMENT",
                "NEAR_THRESHOLD_TRANSITION", "LATERAL_EQUALIZATION", "HETEROGENEITY_AMPLIFIES",
                "HETEROGENEITY_PERSISTS"]},
        "staged_deferral": {"D4": {"status": D4_STATUS, "stage_a_rows": 0,
                "alternate_initial_state_construction":
                    "UNFROZEN_PENDING_SEPARATE_OWNER_SCIENTIFIC_DESIGN",
                "partner_group_schema": "UNFROZEN", "disagreement_predicate": "UNFROZEN",
                "missing_partner_routing": "UNFROZEN_PENDING_GROUP_DESIGN",
                "direct_invocation_disposition": D4_AUTHORITY_STOP},
            "X1": {"status": X1_STATUS, "stage_a_nominations": 0,
                "eligibility_from_baseline_stage_a": "NOT_ADJUDICATED",
                "future_requirements": ["complete eligibility", "atomic prescribed-machine pairing", "atomic cap",
                    "admissible Stage-A evidence", "separate freeze/tests/review/authorization"]}},
        "compute_budget": {"maximum_static_control_cases": 5000, "maximum_dynamic_trajectories": 15000,
            "maximum_extraction_trajectories": 1000, "maximum_total_adjudicative_cases": 20000,
            "absolute_protocol_ceiling": 25000, "timing_pilot_maximum": 64, "worker_process_cap": 32,
            "nested_library_threads": 1, "target_wall_hours": 4, "review_wall_hours": 8, "memory_gib": 16,
            "initial_rows": len(rows), "maximum_D4": 0, "maximum_X1": 0,
            "stage_a_hard_maximum": len(rows), "prospective_maximum": len(rows),
            "maximum_dynamic_trajectory_invocations": graph["maximum_dynamic_trajectory_invocations"],
            "maximum_static_solve_invocations": graph["maximum_static_solve_invocations"],
            "maximum_total_solver_cases": graph["maximum_total_solver_cases"]},
        "stop_rules": {"AUTHORITY_STOP": ["authority/hash/review mismatch", "dirty execution checkout"],
            "NUMERICAL_STOP": ["nonfinite/nonpositive", "conservation/dissipation", "refinement", "clipping"],
            "DESIGN_STOP": ["redundancy", "inadequate topology", "budget"],
            "SCIENTIFIC_BOUNDED_STOP": ["no amplification", "no equalization", "persistence only",
                "machine structurally inactive"], "COMPUTE_STOP": ["time", "memory", "disk"]},
        "future_3d_nomination_rules": {"status": X1_STATUS, "stage_a_authorized": False,
            "separate_freeze_review_and_authorization_required": True},
        "canonical_ordering": "C0,S1,S2,S3,D1,D2,D3-EQ,D3-LOC then declared loop order",
        "hashing_rules": {"canonical_json": "UTF-8 sorted compact JSON", "row_sha256": "row excluding hash",
            "matrix_sha256": "ordered rows including row hashes"},
        "matrix_summary": {"rows_by_arm": dict(counts), "controls": controls,
            "scientific_rows": len(rows) - controls, "dynamic_rows": dynamic,
            "dynamic_comparator_rows": comparator_rows,
            "static_comparator_rows": static_comparator_rows,
            "dynamic_comparator_bindings": dynamic_bindings,
            "comparator_bindings": comparators, "active_scientific_rows": sum(
                row["case_role"] == "ACTIVE_SCIENTIFIC_CASE" for row in rows),
            "structural_comparator_rows": sum(row["case_role"] == "STRUCTURAL_COMPARATOR" for row in rows),
            "model_form_rows": 0,
            "initial_row_count": len(rows), "matrix_sha256": matrix_hash},
        "zero_execution": {"openfoam_launches": 0, "puckworks_calls": 0,
            "adjudicative_reduced_trajectories": 0, "timing_pilot_cases": 0,
            "scientific_matrix_classifications": 0, "SCI_LC_001B_nominations": 0},
    }


def validate(rows: list[dict], spec: dict) -> None:
    canonical_rows = build_rows()
    canonical_by_id = {row["case_id"]: row for row in canonical_rows}
    scope = spec.get("stage_a_initial_condition_scope", {})
    required_scope = {
        "architecture_id": ARCHITECTURE_ID,
        "authority_status": "FROZEN_PENDING_INDEPENDENT_REVIEW",
        "initial_condition_classification_authority_status": INITIAL_CONDITION_AUTHORITY_STATUS,
        "dynamic_initial_state_variant": DYNAMIC_INITIAL_STATE_VARIANT,
        "dynamic_scope": DYNAMIC_INITIAL_CONDITION_SCOPE,
        "static_dynamic_initial_state_variant": STATIC_INITIAL_STATE_VARIANT,
        "static_scope": STATIC_INITIAL_CONDITION_SCOPE,
        "initial_condition_robustness": NOT_ADJUDICATED_STAGE_A,
        "bistability_status": NOT_ADJUDICATED_STAGE_A,
        "initial_condition_dependence_branch": INITIAL_CONDITION_BRANCH_STATUS,
        "legacy_initial_condition_variant_semantics": LEGACY_REALIZATION_SEMANTICS,
        "cache_identity": "(case_id,numerical_profile)",
        "d4_alternate_initial_state_construction":
            "UNFROZEN_PENDING_SEPARATE_OWNER_SCIENTIFIC_DESIGN",
        "d4_status": D4_STATUS, "x1_status": X1_STATUS,
        "physical_validation": "NOT_ESTABLISHED",
    }
    if any(scope.get(key) != value for key, value in required_scope.items()):
        raise ValueError("STAGE_A_BASELINE_SCOPE_AUTHORITY_MISMATCH")
    if scope.get("dynamic_initial_state") != {"internal_sector_pressure": 0.0,
            "machine_pressure_where_applicable": 0.0,
            "resistance_feedback_state_x_i_where_applicable": 0.0}:
        raise ValueError("STAGE_A_ZERO_STATE_AUTHORITY_MISMATCH")
    reconciliation = spec.get("classification", {}).get("initial_condition_reconciliation", {})
    if (reconciliation.get("initial_condition_dependence_branch") != INITIAL_CONDITION_BRANCH_STATUS or
            reconciliation.get("reserved_future_label_stage_a_status") != NOT_ADJUDICATED_STAGE_A or
            "INITIAL_CONDITION_DEPENDENT_OR_BISTABLE" in spec["classification"]["precedence"]):
        raise ValueError("STAGE_A_INITIAL_CONDITION_BRANCH_MUST_REMAIN_INACTIVE")
    placeholders = spec.get("boundary_initial_integration", {}).get("historical_alternate_amplitudes", {})
    if placeholders != {"values": ["0.5", "1.5"], "status": HISTORICAL_ALTERNATE_STATUS,
                        "production_or_planning_use": "PROHIBITED"}:
        raise ValueError("HISTORICAL_ALTERNATE_PLACEHOLDER_AUTHORITY_MISMATCH")
    if len({row["case_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate case ID")
    if len(rows) != len(canonical_rows):
        raise ValueError("FROZEN_STAGE_A_ROW_COUNT_MISMATCH")
    integration = spec["boundary_initial_integration"]
    if (not math.isfinite(DYNAMIC_FIRST_STEP) or DYNAMIC_FIRST_STEP <= 0 or
            DYNAMIC_FIRST_STEP > REFINED_STARTUP_TAU_MAX or
            DYNAMIC_FIRST_STEP > min(float(integration["base_max_step"]),
                                     float(integration["refined_max_step"])) or
            integration.get("dynamic_first_step") != DYNAMIC_FIRST_STEP):
        raise ValueError("DYNAMIC_FIRST_STEP_AUTHORITY_MISMATCH")
    refined = spec["residual_contract"]["LINEAR_REFINED"]
    if (refined.get("monotonicity_atol") != LINEAR_REFINEMENT_MONOTONICITY_ATOL or
            LINEAR_REFINEMENT_MONOTONICITY_ATOL != PIVOT_RATIO_FLOOR):
        raise ValueError("LINEAR_REFINEMENT_MONOTONICITY_AUTHORITY_MISMATCH")
    by_id = {row["case_id"]: row for row in rows}
    ids = set(by_id)
    for row in rows:
        validate_row_against_expected_fields(row, canonical_by_id)
        if row["heterogeneity_mode"].isdigit() and int(row["heterogeneity_mode"]) > row["sector_count"] // 2:
            raise ValueError("invalid Fourier mode")
        validate_feedback_contract(row)
        validate_boundary_row(row)
        if row["case_role"] == "ACTIVE_SCIENTIFIC_CASE":
            if row["lateral_conductance_ratio"] == "0" or row["comparator_case_id"] == NA:
                raise ValueError("active row lacks exact Lambda-zero comparator")
            comparator = by_id[row["comparator_case_id"]]
            left = comparison_key(row, ignore=("lateral_conductance_ratio", "lateral_edge_coefficient",
                "lateral_edge_conductance_G_edge", "derived_Theta_L_m", "scientific_role", "case_role"))
            right = comparison_key(comparator, ignore=("lateral_conductance_ratio", "lateral_edge_coefficient",
                "lateral_edge_conductance_G_edge", "derived_Theta_L_m", "scientific_role", "case_role"))
            if left != right:
                raise ValueError("comparator primitive mismatch")
        elif row["case_role"] == "STRUCTURAL_COMPARATOR":
            if row["lateral_conductance_ratio"] != "0" or row["comparator_case_id"] != NA:
                raise ValueError("invalid structural comparator role")
        elif row["case_role"] != "BOUNDED_STRUCTURAL_CONTROL":
            raise ValueError("unsupported case role")
        for field in ("comparator_case_id", "prescribed_comparator_case_id", "no_evolution_comparator_case_id"):
            if row[field] != NA and row[field] not in ids:
                raise ValueError(f"unbound {field}")
        primitives = resistance_primitives(row["sector_count"], row["heterogeneity_pattern"],
            row["heterogeneity_mode"], row["resistance_contrast"], row["axial_placement"],
            row["epsilon_floor"], row["initial_condition_variant"])
        if min(primitives["H_i"]) <= 0 or min(primitives["R_u_i"] + primitives["R_d_i"]) <= 0:
            raise ValueError("nonpositive primitive")
    budget = spec["compute_budget"]
    if budget["prospective_maximum"] > min(budget["absolute_protocol_ceiling"],
                                            budget["maximum_total_adjudicative_cases"]):
        raise ValueError("budget exceeded")
    if any(row["model_variant"] != "CORE_ONE_EXCHANGE_PLANE" for row in rows):
        raise ValueError("unreviewed multilayer row")
    if spec["staged_deferral"]["D4"]["status"] != D4_STATUS or spec["staged_deferral"]["X1"]["status"] != X1_STATUS:
        raise ValueError("adaptive stage is not fail-closed")
    if budget["prospective_maximum"] != len(rows) or budget["stage_a_hard_maximum"] != len(rows):
        raise ValueError("Stage-A maximum differs from fixed matrix")
    graph = execution_graph(rows)
    if (graph["maximum_dynamic_trajectory_invocations"], graph["maximum_static_solve_invocations"],
            graph["maximum_total_solver_cases"]) != (2212, 1454, 3666):
        raise ValueError("STAGE_A_EXECUTION_GRAPH_COUNT_MISMATCH")
    if not sector_bundle_audit(rows)["all_complete"] or sector_bundle_audit(rows)["required_bundles"] != 13:
        raise ValueError("SECTOR_REFINEMENT_BUNDLE_MISMATCH")


def write(rows: list[dict], spec: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SCI_LC_001A_PROTOCOL.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
    payload = {"schema_version": "ewp.sci_lc_001a.matrix.v2", "status": STATUS,
               "matrix_sha256": spec["matrix_summary"]["matrix_sha256"],
               "row_count": len(rows), "fields": list(FIELDS), "rows": rows}
    (OUT / "SCI_LC_001A_PARAMETER_MATRIX.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with (OUT / "SCI_LC_001A_PARAMETER_MATRIX.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("plan", "generate-and-verify"), default="plan")
    args = parser.parse_args()
    rows = build_rows(); spec = protocol(rows); validate(rows, spec)
    if args.mode == "generate-and-verify":
        write(rows, spec)
    print(json.dumps({"task_id": TASK_ID, "status": STATUS, "mode": args.mode,
                      **spec["matrix_summary"],
                      "prospective_maximum": spec["compute_budget"]["prospective_maximum"],
                      **spec["zero_execution"], "analytical_fixture_checks": 0,
                      "synthetic_selector_fixtures": 0}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
