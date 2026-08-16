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

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/cases/sci_lc_001a"
NA = "NOT_APPLICABLE"
INFINITE = "INFINITE_NO_LATERAL_EQUALIZATION"
STATUS = "PROSPECTIVE_PROTOCOL_CORRECTED_PENDING_SECOND_INDEPENDENT_PRE_EXECUTION_REVIEW"
TASK_ID = "SCI-LC-001A-C2-EXECUTION-CONTRACT-CLOSURE-2026-08-16"
BASE_HEAD = "3e8993f56badd575f3482ea7bfa0f87d24412100"
BASE_TREE = "ba7256d8d5813c87c72a3f896c0ac5f51cd06ee0"
REVIEWED_HEAD = "c683f7722b170d049bcdf08c6bc65afd3cef20ba"
REVIEWED_TREE = "2a352bce78abbf8ad853cd7b0af6457bfea8f8fd"
C1_HEAD = "86b9ff27b8c10d5cff9c52d9cd411b0ac179620e"
C1_TREE = "2e35a5e245be9e266c747409f2420be9971963a6"

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
D4_STATUS = "DEFERRED_NOT_AUTHORIZED_STAGE_A"
X1_STATUS = "DEFERRED_NOT_AUTHORIZED_STAGE_A"
MAX_RHS_EVALUATIONS = 200000

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


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


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
    if any(value < 0.25 or value > 4.0 for value in multipliers):
        raise ValueError("STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUT_OF_RANGE_NO_CLIPPING")
    residual = [value * multiplier for value, multiplier in zip(base["H_i"], multipliers)]
    alpha = float(d(PLACEMENT_ALPHA[placement])); floor = base["R_floor"]
    return {"multipliers": multipliers, "H_i": residual,
            "R_u_i": [floor + alpha * value for value in residual],
            "R_d_i": [floor + (1.0 - alpha) * value for value in residual]}


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


def evolution_focusing(*, tau: float, flows: list[float], startup: list[float],
                       zero_threshold: float = Q_ZERO_THRESHOLD) -> list[float]:
    if not all(math.isfinite(value) for value in flows):
        raise ValueError("STOP_NONFINITE_SECTOR_FLOW")
    total = sum(flows)
    if total < -zero_threshold or any(value < -zero_threshold for value in flows):
        raise ValueError("STOP_UNEXPECTED_FLOW_REVERSAL")
    if abs(total) <= zero_threshold:
        if tau <= STARTUP_TAU_MAX:
            return list(startup)
        raise ValueError("STOP_ZERO_TOTAL_FLOW_OUTSIDE_STARTUP_WINDOW")
    n = len(flows)
    return [(value / total) * n for value in flows]


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


def ratio_uncertainty(numerator: float, denominator: float, *,
                      u_numerator: float, u_denominator: float,
                      denominator_floor: float = 1.0e-12) -> float:
    values = (numerator, denominator, u_numerator, u_denominator)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("UNCERTAINTY_COMPONENT_UNAVAILABLE_NONFINITE")
    if abs(denominator) <= denominator_floor:
        raise ValueError("UNCERTAINTY_COMPONENT_UNAVAILABLE_DENOMINATOR_FLOOR")
    return (abs(u_numerator) / abs(denominator)
            + abs(numerator) * abs(u_denominator) / abs(denominator) ** 2)


def combine_uncertainty(components: dict[str, float | str]) -> float:
    required = ("u_integrator", "u_sector", "u_linear", "u_sampling", "u_denominator")
    if set(components) != set(required):
        raise ValueError("UNCERTAINTY_COMPONENT_SET_INCOMPLETE")
    if any(value == "UNAVAILABLE" for value in components.values()):
        raise ValueError("UNCERTAINTY_COMPONENT_UNAVAILABLE")
    values = [float(components[name]) for name in required]
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("INVALID_UNCERTAINTY_COMPONENT")
    return sum(values)


def structural_identity(row: dict) -> str | None:
    if row.get("lateral_conductance_ratio") == "0":
        return "EXACT_LAMBDA_ZERO_IDENTITY"
    if row.get("axial_placement") == "AXIALLY_SELF_SIMILAR":
        return "EXACT_SELF_SIMILAR_EXCHANGE_NULL"
    if row.get("heterogeneity_pattern") == "UNIFORM" and row.get("resistance_contrast") == "1":
        return "EXACT_UNIFORM_SYMMETRY"
    return None


class DeferredStageError(RuntimeError):
    pass


def classify_synthetic_fixture(*, authority_valid: bool = True, numerical_valid: bool = True,
                               structural_control: bool = False, initial_dependence: bool = False,
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
    if initial_dependence:
        return "INITIAL_CONDITION_DEPENDENT_OR_BISTABLE"
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
    raise DeferredStageError(D4_STATUS)


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
    return {
        "schema_version": "ewp.sci_lc_001a.protocol.v2",
        "task_id": TASK_ID, "status": STATUS, "base_head": BASE_HEAD, "base_tree": BASE_TREE,
        "reviewed_head": REVIEWED_HEAD, "reviewed_tree": REVIEWED_TREE,
        "c1_head": C1_HEAD, "c1_tree": C1_TREE,
        "change_declaration": "NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE",
        "evidence_mode": "PROSPECTIVE_REDUCED_MODEL_PROTOCOL_CORRECTION",
        "execution_authorized": False,
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
            "PRESCRIBED_STATIC": {"unknowns": ["p_i"], "prescribed": ["p_o_hat=0", "p_b_hat=amplitude"],
                "equations": "algebraic conservative node balance", "required": ["prescribed_pressure_amplitude"],
                "prohibited": ["machine_reference_tuple", "machine_compliance_C_u", "storage_ratio_S_h"]},
            "PRESCRIBED_DYNAMIC_RAMP": {"unknowns": ["p_i(tau)"],
                "prescribed": ["p_o_hat=0", "p_b_hat=min(tau/0.05,1)"],
                "equations": "C_h dp_i/dt=q_u_i-q_d_i-j_plus+j_minus",
                "initial": "p_i(0)=0", "required": ["storage_ratio_S_h"],
                "prohibited": ["machine_reference_tuple", "machine_compliance_C_u"]},
            "MACHINE_COUPLED": {"unknowns": ["p_i(tau)", "p_u(tau)", "p_b(tau)"],
                "prescribed": ["p_o_hat=0", "command=min(tau/0.05,1)"],
                "equations": ["C_h dp_i/dt=q_u_i-q_d_i-j_plus+j_minus",
                    "C_u dp_u/dt=Q_supply-Q_puck", "p_b=p_u-R_line*Q_puck"],
                "initial": "p_i(0)=p_u(0)=0", "required": ["machine_reference_tuple", "machine_compliance_C_u"],
                "prohibited": ["prescribed_pressure_amplitude"]}},
        "machine_reference": {"id": MACHINE_TUPLE_ID, "p_o": "0", "p_shut": "1", "q_free": "1",
            "R_line": "0.1", "supply_law": "q_free*ramp(tau)*max(1-(p_u-p_o)/(p_shut-p_o),0)",
            "initial_p_u": "0", "G_ref": "1", "G_load": "10/11", "a_eff": "21/11",
            "Theta_M_levels": list(THETA_M), "C_u_mapping": "C_u=Theta_M*T_shot*(21/11)",
            "basket_relation": "p_b=p_u-R_line*Q_puck"},
        "resistance_evolution": {"name": "SIGNED_LOCAL_FLOW_TO_RESISTANCE_FEEDBACK_SURROGATE",
            "equations": ["Theta_R*dx_i/dtau=s*(F_i-1)-x_i", "H_i(t)=H_i0*exp(beta*x_i)",
                "R_u_i=R_floor+alpha_place*H_i(t)", "R_d_i=R_floor+(1-alpha_place)*H_i(t)"],
            "initial_x_i": "0", "multiplier_bounds": ["0.25", "4"],
            "out_of_bounds": "STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUT_OF_RANGE_NO_CLIPPING",
            "no_evolution": ["beta=0", "Theta_R=INFINITE_NO_EVOLUTION"],
            "fast_control": "Theta_R=0.03", "aggregate_renormalization": "NONE",
            "zero_flow_startup": {"dynamic_limit": "F_i=N*(G_u_i*G_d_i/C_h_i)/sum_j(G_u_j*G_d_j/C_h_j)",
                "machine_note": "machine compliance changes only the common leading time coefficient",
                "q_hat_zero_threshold": "1e-14", "startup_tau_max": "1e-6",
                "exact_zero": "use analytical limit only within startup window",
                "below_threshold": "use same branch and require threshold-refinement uncertainty",
                "flow_reversal": "STOP_UNEXPECTED_FLOW_REVERSAL",
                "nonfinite": "STOP_NONFINITE_SECTOR_FLOW",
                "zero_sector_positive_total": "F_i=0"}},
        "boundary_initial_integration": {"p_o_hat": "0", "static_p_b_hat": "1",
            "dynamic_p_b_hat": "min(tau/0.05,1)", "tau_ramp": "0.05", "shot_horizon": ["0", "1"],
            "initial_internal_p_hat": "0", "initial_machine_p_u_hat": "0", "initial_feedback_x": "0",
            "primary_fourier_phase": "0", "rotation": "i->(i+1) mod N", "reflection": "i->(-i) mod N",
            "alternate_amplitudes": ["0.5", "1.5"], "phase_reversal": "phase->phase+pi",
            "output_grid": "tau_k=k/1000,k=0..1000", "base_method": "DOP853",
            "base_rtol": "1e-8", "base_atol": "1e-10", "base_max_step": "0.0025",
            "refined_method": "DOP853", "refined_rtol": "2.5e-9", "refined_atol": "2.5e-11",
            "refined_max_step": "0.00125", "solver_api": "scipy.integrate.solve_ivp",
            "maximum_rhs_evaluations": MAX_RHS_EVALUATIONS,
            "rhs_counter": "increments before every RHS call, including rejected trial steps",
            "cap_operator": "if nfev>=200000 before next evaluation: stop",
            "cap_disposition": "STOP_MAX_RHS_EVALUATIONS_REACHED;PARTIAL_DIAGNOSTIC_INADMISSIBLE",
            "events": {"lower": "exp(beta*x_i)-0.25", "upper": "4-exp(beta*x_i)",
                "direction": "-1", "terminal": True, "boundary_contact_stops": True,
                "root_time_tolerance": "1e-10 tau", "earliest": "minimum root time",
                "tie_break": "LOWER_BOUND before UPPER_BOUND, then ascending sector index",
                "nonfinite": "STOP_NONFINITE_EVENT_FUNCTION",
                "event_cap_order": "located event in accepted dense-output step precedes later cap; cap precedes unevaluated event"},
            "failure": "NUMERICALLY_UNRESOLVED;NO_CLASSIFICATION"},
        "residual_contract": {
            "linear": {"vector": "r=A*p-b", "scale": "s_i=max(abs(b_i),sum_j(abs(A_ij)*abs(p_j)),1e-14)",
                "norm": "max_i(abs(r_i)/s_i)", "tolerance": "1e-12", "operator": "<=", "retry": "NONE"},
            "nonlinear": {"vector": "r=y-Phi(y)", "scale": "s_i=max(abs(y_i),abs(Phi_i),1e-14)",
                "norm": "max_i(abs(r_i)/s_i)", "tolerance": "1e-10", "operator": "<=", "retry": "NONE"},
            "nonfinite": "NUMERICAL_STOP_NONFINITE_RESIDUAL", "failure_route": "BEFORE_SCIENTIFIC_CLASSIFIER"},
        "model_form": {"initial_variant": "CORE_ONE_EXCHANGE_PLANE_ONLY",
            "multilayer_rows": 0, "reason": "independent review found the prior placeholder non-executable",
            "broad_core_status": "PROVISIONAL_CORE_CLASSIFICATION",
            "nomination_gate": "SEPARATE_REVIEWED_MODEL_FORM_CHECK_REQUIRED_BEFORE_SCI_LC_001B_NOMINATION"},
        "observables": ["H_q", "CV_q", "A_eff", "seeded_mode_amplitude", "J_L_abs", "J_L_net",
            "pressure_CV", "G_static_H", "G_static_mode", "G_coupling_end", "G_coupling_int",
            "sigma_m", "conservation", "dissipation", "selected_extraction_diagnostics"],
        "denominator_floors": {"H_q": "1e-12", "seeded_mode_amplitude": "1e-12",
            "total_flow": "1e-14", "generic_ratio_denominator": "1e-12",
            "fallback": {"uniform": "STRUCTURAL_IDENTITY", "fourier": "USE_SEEDED_MODE_IF_H_Q_FLOORED",
                         "otherwise": "NUMERICALLY_UNRESOLVED"}},
        "uncertainty": {"allowed_ceiling": "u_limit(G)=min(0.02,0.02*abs(G))",
            "rationale": "2-percent relative ceiling capped at 0.02 gain units; exact structural identities use analytical preclassification",
            "components": {
                "u_integrator": "abs(G_base-G_refined) from required DOP853 companion",
                "u_sector": "abs(G_N-G_Nref) when row requires sector refinement; explicit NOT_APPLICABLE otherwise",
                "u_linear": "ratio propagation from scaled-residual-derived numerator and denominator errors",
                "u_sampling": "abs(G_1001-G_2001) reconstructed from the same accepted dense output",
                "u_denominator": "abs(A)*u_B/abs(B)^2; unavailable when abs(B)<=declared floor"},
            "combination": "u_G=u_integrator+u_sector+u_linear+u_sampling+u_denominator",
            "units": "all components are absolute gain units", "operator": "u_G<=u_limit(G)",
            "unavailable": "NUMERICALLY_UNRESOLVED", "stopped": "UNAVAILABLE;NO_CLASSIFICATION",
            "model_form": "SEPARATE_TRANSITION_REASON_NOT_SCALAR_ERROR"},
        "classification": {"static": {"metrics": ["G_static_H", "G_static_mode"],
                "comparator": "exact same-row identity with Lambda=0"},
            "dynamic": {"metrics": ["G_coupling_end", "G_coupling_int"],
                "comparator": "materialized Lambda=0 with same storage,evolution,boundary,machine,initial,numerics"},
            "thresholds": {"equalization": "0.90", "amplification": "1.10"},
            "precedence": ["AUTHORITY_OR_ARTIFACT_INVALID", "ANALYTICAL_STRUCTURAL_IDENTITY",
                "NUMERICALLY_UNRESOLVED", "INITIAL_CONDITION_DEPENDENT_OR_BISTABLE",
                "MODEL_FORM_OR_SECTOR_RESOLUTION_DISAGREEMENT", "METRIC_DISAGREEMENT",
                "NEAR_THRESHOLD_TRANSITION", "LATERAL_EQUALIZATION", "HETEROGENEITY_AMPLIFIES",
                "HETEROGENEITY_PERSISTS"]},
        "staged_deferral": {"D4": {"status": D4_STATUS, "stage_a_rows": 0,
                "future_requirements": ["canonical row materialization", "exact comparators", "alternate initial conditions",
                    "duplicate reconciliation", "atomic cap", "separate freeze/tests/review/authorization"]},
            "X1": {"status": X1_STATUS, "stage_a_nominations": 0,
                "future_requirements": ["complete eligibility", "atomic prescribed-machine pairing", "atomic cap",
                    "admissible Stage-A evidence", "separate freeze/tests/review/authorization"]}},
        "compute_budget": {"maximum_static_control_cases": 5000, "maximum_dynamic_trajectories": 15000,
            "maximum_extraction_trajectories": 1000, "maximum_total_adjudicative_cases": 20000,
            "absolute_protocol_ceiling": 25000, "timing_pilot_maximum": 64, "worker_process_cap": 32,
            "nested_library_threads": 1, "target_wall_hours": 4, "review_wall_hours": 8, "memory_gib": 16,
            "initial_rows": len(rows), "maximum_D4": 0, "maximum_X1": 0,
            "stage_a_hard_maximum": len(rows), "prospective_maximum": len(rows)},
        "stop_rules": {"AUTHORITY_STOP": ["authority/hash/review mismatch", "dirty execution checkout"],
            "NUMERICAL_STOP": ["nonfinite/nonpositive", "conservation/dissipation", "refinement", "clipping"],
            "DESIGN_STOP": ["redundancy", "inadequate topology", "budget"],
            "SCIENTIFIC_BOUNDED_STOP": ["no amplification", "no equalization", "persistence only",
                "no bistability", "machine structurally inactive"], "COMPUTE_STOP": ["time", "memory", "disk"]},
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
    if len({row["case_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate case ID")
    by_id = {row["case_id"]: row for row in rows}
    ids = set(by_id)
    for row in rows:
        if set(row) != set(FIELDS):
            raise ValueError(f"field mismatch {row['case_id']}")
        if row["row_sha256"] != digest({key: row[key] for key in FIELDS if key != "row_sha256"}):
            raise ValueError(f"row hash mismatch {row['case_id']}")
        if row["heterogeneity_mode"].isdigit() and int(row["heterogeneity_mode"]) > row["sector_count"] // 2:
            raise ValueError("invalid Fourier mode")
        if row["feedback_gain"] == "0" and row["feedback_sign"] != "NONE":
            raise ValueError("redundant feedback")
        if row["pressure_mode"] not in BOUNDARY_MODES:
            raise ValueError("unsupported boundary mode")
        if row["pressure_mode"] == "PRESCRIBED_STATIC":
            if row["boundary_profile"] != "CONSTANT_BASKET_PRESSURE" or row["prescribed_pressure_amplitude"] == NA:
                raise ValueError("invalid prescribed-static boundary")
            if row["machine_reference_tuple"] != NA or row["machine_compliance_C_u"] != NA:
                raise ValueError("machine primitive in prescribed-static row")
        elif row["pressure_mode"] == "PRESCRIBED_DYNAMIC_RAMP":
            if row["boundary_profile"] != "PIECEWISE_LINEAR_RAMP_TAU_0P05" or row["storage_ratio_S_h"] == NA:
                raise ValueError("invalid prescribed-dynamic boundary")
            if row["machine_reference_tuple"] != NA or row["machine_compliance_C_u"] != NA:
                raise ValueError("machine primitive in prescribed-dynamic row")
        else:
            if row["boundary_profile"] != "WP02_002_LINEAR_SUPPLY_RAMP_TAU_0P05":
                raise ValueError("invalid machine profile")
            if row["machine_reference_tuple"] == NA or row["machine_compliance_C_u"] == NA:
                raise ValueError("missing machine primitive")
            if row["prescribed_pressure_amplitude"] != NA:
                raise ValueError("prescribed basket pressure conflicts with machine boundary")
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
