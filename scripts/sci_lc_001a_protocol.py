#!/usr/bin/env python3
"""Generate and verify corrected prospective SCI-LC-001A metadata.

No function in this module integrates a trajectory, launches a solver, or
classifies the scientific matrix.  The small algebra helpers and selectors are
for protocol identities and synthetic unit-test fixtures only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/cases/sci_lc_001a"
NA = "NOT_APPLICABLE"
INFINITE = "INFINITE_NO_LATERAL_EQUALIZATION"
STATUS = "PROSPECTIVE_PROTOCOL_CORRECTED_PENDING_SECOND_INDEPENDENT_PRE_EXECUTION_REVIEW"
TASK_ID = "SCI-LC-001A-PROTOCOL-CORRECTION-C1"
BASE_HEAD = "3e8993f56badd575f3482ea7bfa0f87d24412100"
BASE_TREE = "ba7256d8d5813c87c72a3f896c0ac5f51cd06ee0"
REVIEWED_HEAD = "c683f7722b170d049bcdf08c6bc65afd3cef20ba"
REVIEWED_TREE = "2a352bce78abbf8ad853cd7b0af6457bfea8f8fd"

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

FIELDS = (
    "case_id", "arm", "model_variant", "pressure_mode", "sector_count",
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
    "numerical_resolution_role", "scientific_role", "parent_selection_rule",
    "eligibility", "static_or_dynamic_classifier", "comparator_case_id",
    "prescribed_comparator_case_id", "no_evolution_comparator_case_id",
    "model_form_requirement", "adaptive_group_id",
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
    amplitude = 0.0 if span == 0 else math.log(float(d(contrast))) / span
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
    return min(0.02, 0.02 * abs(gain))


def classify_synthetic_fixture(*, authority_valid: bool = True, numerical_valid: bool = True,
                               structural_control: bool = False, initial_dependence: bool = False,
                               model_disagreement: bool = False, metric_disagreement: bool = False,
                               threshold_straddle: bool = False, end_gain: float = 1.0,
                               integrated_gain: float = 1.0) -> str:
    """Encode precedence only; never classify a prospective matrix row."""
    if not authority_valid:
        return "AUTHORITY_OR_ARTIFACT_INVALID"
    if not numerical_valid:
        return "NUMERICALLY_UNRESOLVED"
    if structural_control:
        return "UNIFORM_OR_STRUCTURAL_CONTROL"
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


def make_row(*, arm: str, pressure: str = "PRESCRIBED_PRESSURE", n: int = 8,
             pattern: str = "FOURIER", mode: str = "1", scale: str = "MODE_1",
             contrast: str = "1.5", placement: str = "UPSTREAM_LOCALIZED",
             epsilon: str = EPSILON_FLOOR, lateral: str = "0.1", storage: str = NA,
             theta_m: str = NA, law: str = "NO_EVOLUTION", theta_r: str = NA,
             sign: str = "NONE", beta: str = "0", initial: str = "BASE_PHASE",
             resolution: str = "PRIMARY", role: str = "SCIENTIFIC",
             parent: str = "FROZEN_INITIAL_MATRIX", eligibility: str = "INITIAL_ELIGIBLE",
             classifier: str = "STATIC_CLASSIFIER_V1") -> dict:
    row = {
        "case_id": "", "arm": arm, "model_variant": "CORE_ONE_EXCHANGE_PLANE",
        "pressure_mode": pressure, "sector_count": n, "axial_layer_count": 2,
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
        "numerical_resolution_role": resolution, "scientific_role": role,
        "parent_selection_rule": parent, "eligibility": eligibility,
        "static_or_dynamic_classifier": classifier, "comparator_case_id": NA,
        "prescribed_comparator_case_id": NA, "no_evolution_comparator_case_id": NA,
        "model_form_requirement": "CORE_PROVISIONAL;SEPARATE_MODEL_FORM_REVIEW_REQUIRED_BEFORE_SCI_LC_001B_NOMINATION",
        "adaptive_group_id": "", "units_or_dimensionless_status": "DIMENSIONLESS_V1",
    }
    identity = {key: row[key] for key in IDENTITY_FIELDS if key != "case_id"}
    row["case_id"] = f"SCI-LC-001A.{token(arm)}.{digest(identity)[:24]}"
    return row


def comparison_key(row: dict, *, ignore: tuple[str, ...]) -> tuple:
    return tuple((key, row[key]) for key in IDENTITY_FIELDS
                 if key not in set(ignore) | {"case_id"})


def add_dynamic_pair(rows: list[dict], **kwargs) -> None:
    active = kwargs.pop("lateral")
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
    for pressure in ("PRESCRIBED_PRESSURE_LOW", "PRESCRIBED_PRESSURE_HIGH"):
        rows.append(make_row(arm="C0", pressure=pressure, role="CONTROL",
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
            for pressure, theta_m in (("PRESCRIBED_PRESSURE", NA),) + tuple(
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
                                          "lateral_edge_conductance_G_edge", "derived_Theta_L_m"))
        if row["lateral_conductance_ratio"] == "0":
            by_key[key] = row
    for row in rows:
        if row["scientific_role"] == "SCIENTIFIC":
            key = comparison_key(row, ignore=("lateral_conductance_ratio", "lateral_edge_coefficient",
                                              "lateral_edge_conductance_G_edge", "derived_Theta_L_m"))
            row["comparator_case_id"] = by_key[key]["case_id"]

    prescribed = {}
    for row in rows:
        if row["arm"] == "D2" and row["pressure_mode"] == "PRESCRIBED_PRESSURE":
            key = comparison_key(row, ignore=("pressure_mode", "machine_response_ratio",
                                              "machine_compliance_C_u", "machine_reference_tuple"))
            prescribed[key] = row
    for row in rows:
        if row["arm"] == "D2" and row["pressure_mode"] == "MACHINE_COUPLED":
            key = comparison_key(row, ignore=("pressure_mode", "machine_response_ratio",
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


def d4_select_synthetic(results: list[dict], cap: int = 4096) -> list[dict]:
    """Pure prospective D4 selector for synthetic-result contract tests."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for item in results:
        if float(item["Lambda"]) > 0 and item["numerically_valid"]:
            groups[item["adaptive_group_id"]].append(item)
    proposals: dict[tuple[str, str], dict] = {}
    for group, items in sorted(groups.items()):
        unique = {}
        for item in sorted(items, key=lambda x: (float(x["Lambda"]), x["case_id"])):
            unique.setdefault(item["Lambda"], item)
        ordered = list(unique.values())
        intervals = []
        for left, right in zip(ordered, ordered[1:]):
            slope = abs(right["gain"] - left["gain"]) / abs(
                math.log10(float(right["Lambda"])) - math.log10(float(left["Lambda"])))
            changed = left["classification"] != right["classification"]
            near = min(abs(left["gain"] - 0.9), abs(left["gain"] - 1.1),
                       abs(right["gain"] - 0.9), abs(right["gain"] - 1.1)) <= 0.01
            intervals.append((changed, near, slope, left, right))
        steep = {tuple(sorted((x[3]["case_id"], x[4]["case_id"])))
                 for x in sorted(intervals, key=lambda x: (-x[2], x[3]["case_id"], x[4]["case_id"]))[:2]}
        for changed, near, slope, left, right in intervals:
            pair = tuple(sorted((left["case_id"], right["case_id"])))
            if changed or near or pair in steep:
                generation = max(left.get("generation", 0), right.get("generation", 0)) + 1
                if generation > 3:
                    continue
                midpoint = format(math.sqrt(float(left["Lambda"]) * float(right["Lambda"])), ".17g")
                key = (group, midpoint)
                reasons = (["ADJACENT_CLASSIFICATION_CHANGE"] if changed else []) + (
                    ["WITHIN_0P01_GAIN_OF_BOUNDARY"] if near else []) + (
                    ["TOP_TWO_NORMALIZED_FINITE_DIFFERENCE"] if pair in steep else [])
                proposal = {"adaptive_group_id": group, "Lambda": midpoint,
                            "left_parent": left["case_id"], "right_parent": right["case_id"],
                            "generation": generation,
                            "reasons": sorted(reasons)}
                proposals.setdefault(key, proposal)
        regimes = defaultdict(list)
        for item in ordered:
            regimes[item["classification"]].append(item)
        for regime, members in regimes.items():
            member = sorted(members, key=lambda x: (abs(x["gain"] - 1.0), x["case_id"]))[-1]
            key = (group, member["Lambda"])
            proposals.setdefault(key, {"adaptive_group_id": group, "Lambda": member["Lambda"],
                "left_parent": member["case_id"], "right_parent": member["case_id"],
                "generation": member.get("generation", 0), "reasons": [f"INTERIOR_{regime}"]})
    return sorted(proposals.values(), key=lambda x: (x["generation"], x["adaptive_group_id"],
                  float(x["Lambda"]), x["left_parent"], x["right_parent"]))[:cap]


def x1_select_synthetic(results: list[dict], cap: int = 1000) -> list[dict]:
    """Pure prospective X1 selector for synthetic-result contract tests."""
    eligible = [x for x in results if x["numerically_valid"] and x["classification"] in {
        "LATERAL_EQUALIZATION", "HETEROGENEITY_PERSISTS", "HETEROGENEITY_AMPLIFIES"}]
    chosen: dict[str, dict] = {}
    for regime in sorted({x["classification"] for x in eligible}):
        members = [x for x in eligible if x["classification"] == regime]
        best = sorted(members, key=lambda x: (-min(abs(x["gain"] - 0.9), abs(x["gain"] - 1.1)),
                                              x["uncertainty"], x["case_id"]))[0]
        chosen[best["case_id"]] = {"case_id": best["case_id"], "reason": f"ROBUST_INTERIOR_{regime}"}
    for item in sorted(eligible, key=lambda x: (min(abs(x["gain"] - 0.9), abs(x["gain"] - 1.1)),
                                                x["uncertainty"], x["case_id"]))[:4]:
        chosen.setdefault(item["case_id"], {"case_id": item["case_id"], "reason": "BOUNDARY_SCORE"})
    # When a selected result declares a material machine effect, include its
    # exact prescribed/machine partner identified by pair_key.
    pair_keys = {x.get("pair_key") for x in eligible if x["case_id"] in chosen and
                 x.get("machine_material", False) and x.get("pair_key")}
    for item in eligible:
        if item.get("pair_key") in pair_keys:
            chosen.setdefault(item["case_id"], {"case_id": item["case_id"],
                                                "reason": "MATERIAL_MACHINE_PAIR"})
    return sorted(chosen.values(), key=lambda x: (x["reason"], x["case_id"]))[:cap]


def protocol(rows: list[dict]) -> dict:
    counts = Counter(row["arm"] for row in rows)
    controls = sum(row["scientific_role"] == "CONTROL" for row in rows)
    dynamic = sum(row["static_or_dynamic_classifier"] == "DYNAMIC_CLASSIFIER_V1" for row in rows)
    comparators = sum(row["comparator_case_id"] != NA for row in rows)
    dynamic_bindings = sum(row["comparator_case_id"] != NA and
                           row["static_or_dynamic_classifier"] == "DYNAMIC_CLASSIFIER_V1"
                           for row in rows)
    comparator_rows = sum(row["static_or_dynamic_classifier"] == "DYNAMIC_CLASSIFIER_V1"
                          and row["scientific_role"] == "SCIENTIFIC"
                          and row["lateral_conductance_ratio"] == "0" for row in rows)
    static_comparator_rows = sum(row["static_or_dynamic_classifier"] == "STATIC_CLASSIFIER_V1"
                                 and row["scientific_role"] == "SCIENTIFIC"
                                 and row["lateral_conductance_ratio"] == "0" for row in rows)
    matrix_hash = digest([{key: row[key] for key in FIELDS} for row in rows])
    return {
        "schema_version": "ewp.sci_lc_001a.protocol.v2",
        "task_id": TASK_ID, "status": STATUS, "base_head": BASE_HEAD, "base_tree": BASE_TREE,
        "reviewed_head": REVIEWED_HEAD, "reviewed_tree": REVIEWED_TREE,
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
            "fast_control": "Theta_R=0.03", "aggregate_renormalization": "NONE"},
        "boundary_initial_integration": {"p_o_hat": "0", "static_p_b_hat": "1",
            "dynamic_p_b_hat": "min(tau/0.05,1)", "tau_ramp": "0.05", "shot_horizon": ["0", "1"],
            "initial_internal_p_hat": "0", "initial_machine_p_u_hat": "0", "initial_feedback_x": "0",
            "primary_fourier_phase": "0", "rotation": "i->(i+1) mod N", "reflection": "i->(-i) mod N",
            "alternate_amplitudes": ["0.5", "1.5"], "phase_reversal": "phase->phase+pi",
            "output_grid": "tau_k=k/1000,k=0..1000", "base_method": "DOP853",
            "base_rtol": "1e-8", "base_atol": "1e-10", "base_max_step": "0.0025",
            "refined_method": "DOP853", "refined_rtol": "2.5e-9", "refined_atol": "2.5e-11",
            "refined_max_step": "0.00125", "linear_relative_residual": "1e-12",
            "nonlinear_relative_residual": "1e-10", "maximum_internal_steps": 200000,
            "failure": "NUMERICALLY_UNRESOLVED;NO_CLASSIFICATION"},
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
            "combination": "u_G=u_integrator+u_sector+u_linear+u_sampling+u_denominator",
            "model_form": "SEPARATE_TRANSITION_REASON_NOT_SCALAR_ERROR"},
        "classification": {"static": {"metrics": ["G_static_H", "G_static_mode"],
                "comparator": "exact same-row identity with Lambda=0"},
            "dynamic": {"metrics": ["G_coupling_end", "G_coupling_int"],
                "comparator": "materialized Lambda=0 with same storage,evolution,boundary,machine,initial,numerics"},
            "thresholds": {"equalization": "0.90", "amplification": "1.10"},
            "precedence": ["AUTHORITY_OR_ARTIFACT_INVALID", "NUMERICALLY_UNRESOLVED",
                "UNIFORM_OR_STRUCTURAL_CONTROL", "INITIAL_CONDITION_DEPENDENT_OR_BISTABLE",
                "MODEL_FORM_OR_SECTOR_RESOLUTION_DISAGREEMENT", "METRIC_DISAGREEMENT",
                "NEAR_THRESHOLD_TRANSITION", "LATERAL_EQUALIZATION", "HETEROGENEITY_AMPLIFIES",
                "HETEROGENEITY_PERSISTS"]},
        "adaptive_rules": {"D4": {"grouping_fields": [key for key in IDENTITY_FIELDS if key not in {
                "case_id", "lateral_conductance_ratio", "lateral_edge_coefficient",
                "lateral_edge_conductance_G_edge", "derived_Theta_L_m"}],
                "zero_lambda": "FIXED_COMPARATOR_NOT_LOG_REFINED",
                "boundary_distance": "0.01 gain units", "midpoint": "geometric mean of positive endpoints",
                "finite_difference": "absolute gain change per log10 Lambda", "tie_break": "canonical case_id",
                "maximum_refinement_generations": 3, "maximum_new_rows_per_parent_interval": 2,
                "maximum_total_rows": 4096, "duplicate_rule": "canonical parameter identity first wins"},
            "X1": {"robust_interior_score": "distance to nearest 0.90/1.10 boundary",
                "boundary_score": "distance to nearest boundary", "eligible": "valid resolved hydraulic regimes",
                "tie_break": "uncertainty then canonical case_id", "pairing": "prescribed/machine only if informative",
                "maximum_total_rows": 1000}},
        "compute_budget": {"maximum_static_control_cases": 5000, "maximum_dynamic_trajectories": 15000,
            "maximum_extraction_trajectories": 1000, "maximum_total_adjudicative_cases": 20000,
            "absolute_protocol_ceiling": 25000, "timing_pilot_maximum": 64, "worker_process_cap": 32,
            "nested_library_threads": 1, "target_wall_hours": 4, "review_wall_hours": 8, "memory_gib": 16,
            "initial_rows": len(rows), "maximum_D4": 4096, "maximum_X1": 1000,
            "prospective_maximum": len(rows) + 5096},
        "stop_rules": {"AUTHORITY_STOP": ["authority/hash/review mismatch", "dirty execution checkout"],
            "NUMERICAL_STOP": ["nonfinite/nonpositive", "conservation/dissipation", "refinement", "clipping"],
            "DESIGN_STOP": ["redundancy", "inadequate topology", "budget"],
            "SCIENTIFIC_BOUNDED_STOP": ["no amplification", "no equalization", "persistence only",
                "no bistability", "machine structurally inactive"], "COMPUTE_STOP": ["time", "memory", "disk"]},
        "future_3d_nomination_rules": {"status": "PROPOSED_SCI_LC_001B_CASES_PENDING_SEPARATE_REVIEW",
            "maximum_distinct_hydraulic_base_cases": 8, "maximum_total_prescribed_machine_variants": 12,
            "model_form_corroboration_required": True},
        "canonical_ordering": "C0,S1,S2,S3,D1,D2,D3-EQ,D3-LOC then declared loop order",
        "hashing_rules": {"canonical_json": "UTF-8 sorted compact JSON", "row_sha256": "row excluding hash",
            "matrix_sha256": "ordered rows including row hashes"},
        "matrix_summary": {"rows_by_arm": dict(counts), "controls": controls,
            "scientific_rows": len(rows) - controls, "dynamic_rows": dynamic,
            "dynamic_comparator_rows": comparator_rows,
            "static_comparator_rows": static_comparator_rows,
            "dynamic_comparator_bindings": dynamic_bindings,
            "comparator_bindings": comparators, "model_form_rows": 0,
            "initial_row_count": len(rows), "matrix_sha256": matrix_hash},
        "zero_execution": {"openfoam_launches": 0, "puckworks_calls": 0,
            "adjudicative_reduced_trajectories": 0, "timing_pilot_cases": 0,
            "scientific_matrix_classifications": 0, "SCI_LC_001B_nominations": 0},
    }


def validate(rows: list[dict], spec: dict) -> None:
    if len({row["case_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate case ID")
    ids = {row["case_id"] for row in rows}
    for row in rows:
        if set(row) != set(FIELDS):
            raise ValueError(f"field mismatch {row['case_id']}")
        if row["row_sha256"] != digest({key: row[key] for key in FIELDS if key != "row_sha256"}):
            raise ValueError(f"row hash mismatch {row['case_id']}")
        if row["heterogeneity_mode"].isdigit() and int(row["heterogeneity_mode"]) > row["sector_count"] // 2:
            raise ValueError("invalid Fourier mode")
        if row["feedback_gain"] == "0" and row["feedback_sign"] != "NONE":
            raise ValueError("redundant feedback")
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
