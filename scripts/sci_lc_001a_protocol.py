#!/usr/bin/env python3
"""Generate and verify the prospective SCI-LC-001A protocol matrix.

This module constructs metadata only.  It contains no trajectory integrator,
production-solver import, case launcher, or scientific classifier.
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
STATUS = "PROSPECTIVE_PROTOCOL_PENDING_INDEPENDENT_PRE_EXECUTION_REVIEW"
TASK_ID = "SCI-LC-001A-PROTOCOL-AND-MATRIX-FREEZE"
BASE_HEAD = "3e8993f56badd575f3482ea7bfa0f87d24412100"
BASE_TREE = "ba7256d8d5813c87c72a3f896c0ac5f51cd06ee0"
FIELDS = (
    "case_id", "arm", "model_variant", "pressure_mode", "sector_count",
    "axial_layer_count", "heterogeneity_pattern", "heterogeneity_mode",
    "heterogeneity_scale", "resistance_contrast", "axial_placement",
    "lateral_conductance_ratio", "hydraulic_storage_ratio",
    "machine_response_ratio", "resistance_evolution_law",
    "resistance_evolution_timescale_ratio", "feedback_sign", "feedback_gain",
    "shot_duration", "initial_condition_variant", "numerical_resolution_role",
    "scientific_role", "parent_selection_rule", "eligibility",
    "units_or_dimensionless_status", "row_sha256",
)

LAMBDAS = ("0", "0.0001", "0.0003", "0.001", "0.003", "0.01", "0.03",
           "0.1", "0.3", "1", "3", "10", "30", "100")
CONTRASTS = ("1", "1.25", "1.5", "2", "4", "8", "16")
THETA_L = ("0.01", "0.03", "0.1", "0.3", "1", "3", "10", "30")
THETA_M = ("0.03", "0.1", "0.3", "1", "3", "10")
THETA_R = ("0.03", "0.1", "0.3", "1", "3", "10")
BETAS = ("0.25", "0.5", "1", "2")
PLACEMENTS = ("UPSTREAM", "DISTRIBUTED", "DOWNSTREAM")


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def token(value: str) -> str:
    return value.lower().replace(".", "p").replace("-", "m").replace("_", "-")


def make_row(*, arm: str, variant: str = "CORE_ONE_EXCHANGE_PLANE",
             pressure: str = "PRESCRIBED_PRESSURE", n: int = 8, layers: int = 2,
             pattern: str = "FOURIER", mode: str = "1", scale: str = "MODE_1",
             contrast: str = "1.5", placement: str = "DISTRIBUTED",
             lateral: str = "0.1", storage: str = NA, machine: str = NA,
             law: str = "NO_EVOLUTION", theta_r: str = NA, sign: str = "NONE",
             beta: str = "0", initial: str = "BASE_PHASE",
             resolution: str = "PRIMARY", role: str = "SCIENTIFIC",
             parent: str = "FROZEN_INITIAL_MATRIX", eligibility: str = "INITIAL_ELIGIBLE") -> dict:
    parts = (arm, variant, pressure, f"n{n}", f"l{layers}", pattern, f"m{mode}",
             f"x{contrast}", placement, f"lam{lateral}", f"tl{storage}",
             f"tm{machine}", sign, f"b{beta}", f"tr{theta_r}", initial)
    row = {
        "case_id": "SCI-LC-001A." + ".".join(token(str(x)) for x in parts),
        "arm": arm, "model_variant": variant, "pressure_mode": pressure,
        "sector_count": n, "axial_layer_count": layers,
        "heterogeneity_pattern": pattern, "heterogeneity_mode": mode,
        "heterogeneity_scale": scale, "resistance_contrast": contrast,
        "axial_placement": placement, "lateral_conductance_ratio": lateral,
        "hydraulic_storage_ratio": storage, "machine_response_ratio": machine,
        "resistance_evolution_law": law,
        "resistance_evolution_timescale_ratio": theta_r,
        "feedback_sign": sign, "feedback_gain": beta, "shot_duration": "1",
        "initial_condition_variant": initial,
        "numerical_resolution_role": resolution, "scientific_role": role,
        "parent_selection_rule": parent, "eligibility": eligibility,
        "units_or_dimensionless_status": "ALL_MATRIX_AXES_DIMENSIONLESS_OR_CATEGORICAL",
    }
    row["row_sha256"] = digest(row)
    return row


def build_rows() -> list[dict]:
    rows: list[dict] = []
    # C0: exact symmetry, zero-coupling, pressure-scaling, ring-invariance,
    # machine-reference, and no-evolution controls.  These are not regimes.
    for n in (4, 8, 16):
        rows.append(make_row(arm="C0", n=n, pattern="UNIFORM", mode="0", scale="UNIFORM",
                             contrast="1", lateral="0.1", role="CONTROL",
                             resolution="CONTROL", initial="UNIFORM_SYMMETRY"))
    for mode in ("1", "2", "4"):
        if int(mode) <= 8 // 2:
            for initial in ("BASE_PHASE", "ROTATED_ONE_SECTOR", "REFLECTED"):
                rows.append(make_row(arm="C0", mode=mode, scale=f"MODE_{mode}", lateral="0",
                                     role="CONTROL", resolution="CONTROL", initial=initial))
    for pressure in ("PRESCRIBED_PRESSURE_LOW", "PRESCRIBED_PRESSURE_HIGH"):
        rows.append(make_row(arm="C0", pressure=pressure, role="CONTROL",
                             resolution="CONTROL", initial="LINEAR_PRESSURE_SCALING"))
    rows.append(make_row(arm="C0", pressure="MACHINE_COUPLED", pattern="UNIFORM", mode="0",
                         scale="UNIFORM", contrast="1", storage="0.1", machine="1",
                         role="CONTROL", resolution="CONTROL", initial="MACHINE_REFERENCE"))
    rows.append(make_row(arm="C0", law="NO_EVOLUTION", theta_r="INFINITE_NO_EVOLUTION",
                         role="CONTROL", resolution="CONTROL", initial="NO_EVOLUTION_LIMIT"))

    # S1: complete primary passive atlas.
    for contrast in CONTRASTS[1:]:
        for lateral in LAMBDAS:
            for mode in ("1", "2", "4"):
                for placement in PLACEMENTS:
                    rows.append(make_row(arm="S1", contrast=contrast, lateral=lateral,
                                         mode=mode, scale=f"MODE_{mode}", placement=placement))

    # S2: bounded pattern robustness, not a second broad factorial.
    patterns = (("CONTIGUOUS_BLOCK", "BLOCK_HALF", "BLOCK_HALF"),
                ("CONTIGUOUS_BLOCK_ROTATED", "BLOCK_HALF", "BLOCK_HALF"),
                ("BROADBAND_SEED_20260816", "BROADBAND", "CORRELATION_2_SECTORS"))
    for pattern, mode, scale in patterns:
        for contrast in ("1.5", "4", "16"):
            for lateral in ("0", "0.01", "0.1", "1", "10"):
                for placement in PLACEMENTS:
                    rows.append(make_row(arm="S2", pattern=pattern, mode=mode, scale=scale,
                                         contrast=contrast, lateral=lateral, placement=placement,
                                         parent="FROZEN_PATTERN_ROBUSTNESS_SUBSET"))

    # S3: prospectively selected resolution/formulation checks.
    archetypes = (("1.5", "0.01", "1", "UPSTREAM"), ("4", "0.1", "1", "DISTRIBUTED"),
                  ("16", "10", "1", "DOWNSTREAM"), ("1.5", "1", "2", "DOWNSTREAM"),
                  ("4", "0.03", "2", "UPSTREAM"), ("16", "0.3", "2", "DISTRIBUTED"))
    for contrast, lateral, mode, placement in archetypes:
        for n in (4, 8, 16):
            for variant, layers in (("CORE_ONE_EXCHANGE_PLANE", 2),
                                    ("MULTILAYER_SELECTED_CHECK", 4)):
                rows.append(make_row(arm="S3", variant=variant, layers=layers, n=n,
                                     contrast=contrast, lateral=lateral, mode=mode,
                                     scale=f"MODE_{mode}", placement=placement,
                                     resolution="SECTOR_AND_AXIAL_FORM_CHECK",
                                     parent="FROZEN_CONVERGENCE_ARCHETYPE"))
    for n in (8, 16):
        for variant, layers in (("CORE_ONE_EXCHANGE_PLANE", 2),
                                ("MULTILAYER_SELECTED_CHECK", 4)):
            rows.append(make_row(arm="S3", variant=variant, layers=layers, n=n,
                                 contrast="4", lateral="0.1", mode="4", scale="MODE_4",
                                 resolution="SECTOR_AND_AXIAL_FORM_CHECK",
                                 parent="FROZEN_CONVERGENCE_ARCHETYPE"))

    dynamic_parents = (("1.5", "0.01", "1", "UPSTREAM"),
                       ("4", "0.1", "2", "DISTRIBUTED"),
                       ("16", "10", "4", "DOWNSTREAM"),
                       ("4", "1", "1", "DOWNSTREAM"),
                       ("16", "0.03", "2", "UPSTREAM"),
                       ("1.5", "0.3", "4", "DISTRIBUTED"))
    for contrast, lateral, mode, placement in dynamic_parents:
        for theta_l in THETA_L:
            rows.append(make_row(arm="D1", contrast=contrast, lateral=lateral, mode=mode,
                                 scale=f"MODE_{mode}", placement=placement, storage=theta_l,
                                 parent="FROZEN_STATIC_REPRESENTATIVE"))

    # D2 machine cases require storage; matched prescribed controls are explicit.
    for contrast, lateral, mode, placement in dynamic_parents[:4]:
        for theta_l in ("0.1", "1", "10"):
            rows.append(make_row(arm="D2", contrast=contrast, lateral=lateral, mode=mode,
                                 scale=f"MODE_{mode}", placement=placement, storage=theta_l,
                                 pressure="PRESCRIBED_PRESSURE", initial="MATCHED_MACHINE_CONTROL",
                                 parent="FROZEN_MACHINE_INTERACTION_SUBSET"))
            for theta_m in THETA_M:
                rows.append(make_row(arm="D2", contrast=contrast, lateral=lateral, mode=mode,
                                     scale=f"MODE_{mode}", placement=placement, storage=theta_l,
                                     pressure="MACHINE_COUPLED", machine=theta_m,
                                     parent="FROZEN_MACHINE_INTERACTION_SUBSET"))

    for arm, sign in (("D3-EQ", "EQUALIZING"), ("D3-LOC", "LOCALIZING")):
        for contrast, lateral, mode, placement in dynamic_parents[:4]:
            for beta in BETAS:
                for theta_r in THETA_R:
                    rows.append(make_row(arm=arm, contrast=contrast, lateral=lateral, mode=mode,
                                         scale=f"MODE_{mode}", placement=placement, storage="1",
                                         law="SIGNED_LOCAL_FLOW_TO_RESISTANCE_FEEDBACK_SURROGATE",
                                         theta_r=theta_r, sign=sign, beta=beta,
                                         parent="FROZEN_FEEDBACK_SUBSET"))
    return rows


def ring_eigenvalue(n: int, mode: int) -> float:
    return 4.0 * (n / (2.0 * math.pi)) ** 2 * math.sin(math.pi * mode / n) ** 2


def conductance_matched_resistances(pattern: list[float], contrast: str) -> list[float]:
    span = max(pattern) - min(pattern)
    if span == 0:
        return [1.0] * len(pattern)
    amplitude = math.log(float(Decimal(contrast))) / span
    raw = [math.exp(-amplitude * h) for h in pattern]
    mean = sum(raw) / len(raw)
    return [mean / g for g in raw]


def protocol(rows: list[dict]) -> dict:
    counts = Counter(row["arm"] for row in rows)
    initial_dynamic = sum(counts[a] for a in ("D1", "D2", "D3-EQ", "D3-LOC"))
    initial_static = len(rows) - initial_dynamic
    adaptive_max = 4096
    extraction_max = 1000
    matrix_hash = digest([{k: r[k] for k in FIELDS} for r in rows])
    return {
        "schema_version": "ewp.sci_lc_001a.protocol.v1",
        "task_id": TASK_ID,
        "status": STATUS,
        "base_head": BASE_HEAD,
        "base_tree": BASE_TREE,
        "change_declaration": "NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE",
        "repository_change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "evidence_mode": "PROSPECTIVE_REDUCED_MODEL_PROTOCOL",
        "scientific_question": ("Under what combinations of lateral conductance, axial resistance "
                                "contrast, heterogeneity scale, machine response, and resistance-"
                                "evolution timescale does puck nonuniformity decay, persist, or amplify?"),
        "hypotheses": {
            "H0": "zero-coupling fixed-resistance normalized inequality persists",
            "H1": "passive lateral exchange can equalize",
            "H2": "passive lateral exchange can focus flow downstream",
            "H3": "response depends on heterogeneity scale",
            "H4": "machine response is spatially inactive in the linear quasi-steady fixed-resistance limit",
            "H5": "signed resistance feedback distinguishes equalizing and localizing response",
            "H6": "reduced-formulation disagreement identifies higher-value future 3-D cases",
        },
        "claim_boundary": {
            "PHYSICAL_VALIDATION": "NOT_ESTABLISHED",
            "GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION": "NOT_ESTABLISHED",
            "EXPERIMENTAL_COMMISSIONING": "NOT_AUTHORIZED",
            "PROTECTED_OR_HOLDOUT_SCORING": "NOT_AUTHORIZED",
            "PRODUCTION_OPENFOAM_PHYSICS_CHANGE": "NONE",
            "OPENFOAM_EXECUTION_IN_THIS_TASK": "NONE",
            "REAL_PUCK_LATERAL_CONDUCTANCE": "NOT_MEASURED",
            "UNIVERSAL_LATERAL_COUPLING_PARAMETER": "NOT_ESTABLISHED",
            "RP_D_LC_001B_XI_ROLE": "SYNTHETIC_NUMERICAL_CONTEXT_ONLY",
            "SCI_LC_001A_ROLE": "REDUCED_DIAGNOSTIC_PHASE_DIAGRAM",
        },
        "model_variants": ["CORE_ONE_EXCHANGE_PLANE", "MULTILAYER_SELECTED_CHECK"],
        "equations": {
            "core": ["q_u_i=(p_b-p_i)/R_u_i", "q_d_i=(p_i-p_o)/R_d_i",
                     "j_i_plus_half=G_L_i_plus_half*(p_i-p_i_plus_1)",
                     "C_h_i*dp_i/dt=q_u_i-q_d_i-j_i_plus_half+j_i_minus_half"],
            "scaled_ring_laplacian": "L_N p_i=(N/(2*pi))^2*(2*p_i-p_i_minus_1-p_i_plus_1)",
            "ring_eigenvalue": "lambda_N(m)=4*(N/(2*pi))^2*sin(pi*m/N)^2 -> m^2",
            "machine": ["C_u*dp_u/dt=Q_supply(p_u,t)-Q_puck", "p_b=p_u-R_u*Q_puck"],
            "feedback": ["Theta_R*dx_i/dt=s*(F_i-1)-x_i", "R_i=R_i0*exp(beta*x_i)"],
        },
        "state_variables": ["p_b", "p_u", "p_i", "q_u_i", "q_d_i", "j_edge",
                            "R_u_i", "R_d_i", "x_i", "Q_total", "Q_supply"],
        "units": {"pressure": "Pa", "flow": "m^3/s", "resistance": "Pa s/m^3",
                  "conductance": "m^3/(s Pa)", "storage": "m^3/Pa", "time": "s"},
        "topology_and_boundary_conditions": {
            "topology": "periodic equal-area circumferential ring",
            "core_nodes_per_sector": 1,
            "axial_resistance_split": {"UPSTREAM": "0.95/0.05", "DISTRIBUTED": "0.5/0.5",
                                       "DOWNSTREAM": "0.05/0.95"},
            "boundaries": ["PRESCRIBED_PRESSURE", "MACHINE_COUPLED_WP02_002"],
        },
        "parameters": {
            "sector_count": [4, 8, 16], "resistance_contrast": list(CONTRASTS),
            "lateral_conductance_ratio": list(LAMBDAS), "fourier_modes_at_N8": [1, 2, 4],
            "axial_placement": list(PLACEMENTS), "placement_upstream_fraction": {
                "UPSTREAM": "0.95", "DISTRIBUTED": "0.5", "DOWNSTREAM": "0.05"},
            "Theta_L": list(THETA_L), "Theta_M": list(THETA_M),
            "Theta_R": list(THETA_R) + ["INFINITE_NO_EVOLUTION"],
            "beta": ["0"] + list(BETAS), "feedback_sign": ["EQUALIZING", "NONE", "LOCALIZING"],
        },
        "dimensionless_groups": {
            "Lambda": "scaled lateral conductance / characteristic axial conductance",
            "chi_R": "R_max/R_min=exp(a*(h_max-h_min))",
            "kappa_h": "Fourier mode m or inverse normalized wavelength",
            "Theta_L": "tau_lateral/T_shot", "Theta_M": "tau_machine/T_shot",
            "Theta_R": "tau_resistance/T_shot", "beta": "log-resistance feedback magnitude",
        },
        "matrix_arms": {
            "C0": "analytical and invariant controls", "S1": "primary static atlas",
            "S2": "pattern robustness", "S3": "sector and axial-form convergence",
            "D1": "transient lateral equalization", "D2": "machine coupling",
            "D3-EQ": "equalizing resistance feedback", "D3-LOC": "localizing resistance feedback",
            "D4": "adaptive transition and bistability refinement; generated only from reviewed results",
            "X1": "selected extraction diagnostics; generated only from reviewed hydraulic results",
        },
        "observables": ["H_q", "CV_q", "A_eff", "seeded_mode_amplitude", "J_L_abs",
                        "J_L_net", "pressure_CV", "G_time_end", "G_time_int",
                        "G_coupling_end", "G_coupling_int", "sigma_m",
                        "dominant_region_persistence", "conservation_residuals",
                        "extraction_diagnostics_selected_only"],
        "validity_gates": {
            "numerical_gain_uncertainty": "max(0.02 absolute, 2 percent relative as applicable)",
            "required": ["finite", "positive resistance and conductance", "local conservation",
                         "global conservation", "lateral cancellation", "passive dissipation",
                         "timestep refinement", "sector refinement", "model-form agreement"],
        },
        "classification_rules": {
            "LATERAL_EQUALIZATION": "G_coupling_end<=0.90 and G_coupling_int<=0.90 with corroboration",
            "HETEROGENEITY_PERSISTS": "both gains in [0.90,1.10] with corroboration",
            "HETEROGENEITY_AMPLIFIES": "G_coupling_end>=1.10 and G_coupling_int>=1.10 with corroboration",
            "TRANSITION_OR_BISTABLE_REGION": ["NEAR_MATERIALITY_BOUNDARY", "METRIC_DISAGREEMENT",
                "MODEL_FORM_DISAGREEMENT", "SECTOR_RESOLUTION_DISAGREEMENT",
                "INITIAL_CONDITION_DEPENDENCE", "BISTABILITY_EVIDENCE",
                "MIXED_COUPLING_AND_EVOLUTION_EFFECT"],
            "NUMERICALLY_UNRESOLVED": "validity uncertainty or refinement failure; never a transition label",
        },
        "adaptive_rules": {
            "D4_LOG_MIDPOINT_V1": {
                "selection": ["adjacent classifications differ", "gain within 10 percent of boundary",
                              "two largest finite differences", "one interior representative per regime"],
                "maximum_refinement_generations": 3,
                "maximum_new_rows_per_parent_interval": 2,
                "maximum_total_rows": adaptive_max,
            },
            "X1_SELECTED_HYDRAULIC_DIAGNOSTICS_V1": {
                "selection": "one robust interior per observed regime plus selected boundaries",
                "maximum_total_rows": extraction_max,
            },
        },
        "compute_budget": {
            "maximum_static_control_cases": 5000, "maximum_dynamic_trajectories": 15000,
            "maximum_extraction_trajectories": 1000, "maximum_total_adjudicative_cases": 20000,
            "absolute_protocol_ceiling": 25000, "timing_pilot_maximum": 64,
            "worker_process_cap": 32, "nested_library_threads": 1,
            "target_wall_hours": 4, "review_wall_hours": 8, "memory_gib": 16,
            "initial_static_control_rows": initial_static,
            "initial_dynamic_rows": initial_dynamic,
            "initial_rows": len(rows), "maximum_adaptive_rows": adaptive_max,
            "maximum_extraction_rows": extraction_max,
            "maximum_total_rows": len(rows) + adaptive_max + extraction_max,
        },
        "stop_rules": {
            "AUTHORITY_STOP": ["authority/hash mismatch", "independent review incomplete", "dirty execution checkout"],
            "NUMERICAL_STOP": ["nonfinite/nonpositive state", "conservation/dissipation failure",
                               "invariance/refinement failure", "clipping dependence"],
            "DESIGN_STOP": ["analytical redundancy", "nonconvergent ring scaling",
                            "aggregate conductance not preserved", "compute ceiling exceeded"],
            "SCIENTIFIC_BOUNDED_STOP": ["NO_AMPLIFICATION_REGION_WITHIN_FROZEN_RANGE",
                "NO_EQUALIZATION_REGION_WITHIN_FROZEN_RANGE", "ONLY_PERSISTENCE_WITHIN_FROZEN_RANGE",
                "NO_BISTABILITY_WITHIN_FROZEN_RANGE", "MACHINE_RESPONSE_STRUCTURALLY_INACTIVE_IN_TESTED_LINEAR_MODEL"],
            "COMPUTE_STOP": ["wall time", "disk or memory", "recurrent worker failures", "budget mismatch"],
        },
        "future_3d_nomination_rules": {
            "status": "PROPOSED_SCI_LC_001B_CASES_PENDING_SEPARATE_REVIEW",
            "maximum_distinct_hydraulic_base_cases": 8, "maximum_total_prescribed_machine_variants": 12,
            "priorities": ["one robust interior per observed regime", "up to two cases per important boundary",
                           "reduced-formulation disagreement", "machine variants only when materially different"],
        },
        "artifact_and_result_schemas": {
            "authority": "future immutable protocol/matrix/source/environment binding",
            "case_record": "future canonical row, numerical validity, observables, and provenance",
            "manifest": "future full expected-row partition and terminal disposition",
            "result": "future reduced findings separated from 3-D, experimental, and unidentified claims",
            "instances_created_by_this_task": "NONE",
        },
        "restart_block": {
            "permitted_only_for": "future exact-authority immutable case records",
            "refuse_on": ["authority mismatch", "matrix or row hash mismatch", "dependency mismatch",
                          "malformed or temporary artifact", "validity stop", "existing terminal manifest"],
            "execution_authorized_by_this_protocol": False,
        },
        "random_or_low_discrepancy_seeds": {"broadband_pattern": 20260816, "stochastic_execution": "NONE"},
        "canonical_ordering": "arm order C0,S1,S2,S3,D1,D2,D3-EQ,D3-LOC then nested declared loop order",
        "hashing_rules": {"canonical_json": "UTF-8 JSON, sorted keys, compact separators, ASCII escapes",
                          "row_sha256": "SHA-256 of row excluding row_sha256",
                          "matrix_sha256": "SHA-256 of ordered complete rows including row_sha256"},
        "outcomes": ["SCI_LC_001A_PHASE_DIAGRAM_COMPLETE",
            "SCI_LC_001A_EQUALIZATION_AND_PERSISTENCE_REGIONS_IDENTIFIED",
            "SCI_LC_001A_AMPLIFICATION_REGION_IDENTIFIED", "SCI_LC_001A_TRANSITION_OR_BISTABILITY_IDENTIFIED",
            "SCI_LC_001A_NO_AMPLIFICATION_WITHIN_FROZEN_RANGE", "SCI_LC_001A_REDUCED_FORMULATIONS_DISAGREE",
            "SCI_LC_001A_PARAMETER_RANGE_TRUNCATED", "SCI_LC_001A_NUMERICALLY_UNRESOLVED",
            "SCI_LC_001A_PROTOCOL_OR_AUTHORITY_FAILURE"],
        "matrix_summary": {"rows_by_arm": dict(counts), "initial_row_count": len(rows),
                           "adaptive_placeholder_rows": 0, "matrix_sha256": matrix_hash},
    }


def validate(rows: list[dict], spec: dict) -> None:
    if len({r["case_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate case ID")
    for row in rows:
        if set(row) != set(FIELDS):
            raise ValueError(f"field mismatch: {row['case_id']}")
        expected = digest({k: row[k] for k in FIELDS if k != "row_sha256"})
        if row["row_sha256"] != expected:
            raise ValueError(f"row hash mismatch: {row['case_id']}")
        mode = row["heterogeneity_mode"]
        if mode.isdigit() and int(mode) > row["sector_count"] // 2:
            raise ValueError(f"invalid Fourier mode: {row['case_id']}")
        if row["feedback_gain"] == "0" and row["feedback_sign"] != "NONE":
            raise ValueError("nonzero feedback sign with zero gain")
        if row["pressure_mode"].startswith("PRESCRIBED") and row["machine_response_ratio"] != NA:
            raise ValueError("machine timescale on prescribed row")
        if row["resistance_evolution_law"] == "NO_EVOLUTION" and row["resistance_evolution_timescale_ratio"] not in (NA, "INFINITE_NO_EVOLUTION"):
            raise ValueError("evolution timescale on no-evolution row")
    budget = spec["compute_budget"]
    if budget["maximum_total_rows"] > budget["absolute_protocol_ceiling"]:
        raise ValueError("protocol ceiling exceeded")
    if any(r["arm"] in ("D4", "X1") for r in rows):
        raise ValueError("adaptive/result-selected rows must not be materialized before execution review")


def write(rows: list[dict], spec: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SCI_LC_001A_PROTOCOL.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
    payload = {"schema_version": "ewp.sci_lc_001a.matrix.v1",
               "status": STATUS, "matrix_sha256": spec["matrix_summary"]["matrix_sha256"],
               "row_count": len(rows), "rows": rows}
    (OUT / "SCI_LC_001A_PARAMETER_MATRIX.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with (OUT / "SCI_LC_001A_PARAMETER_MATRIX.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("plan", "generate-and-verify"), default="plan")
    args = parser.parse_args()
    rows = build_rows()
    spec = protocol(rows)
    validate(rows, spec)
    if args.mode == "generate-and-verify":
        write(rows, spec)
    print(json.dumps({"task_id": TASK_ID, "status": STATUS,
                      "mode": args.mode, **spec["matrix_summary"],
                      "maximum_total_rows": spec["compute_budget"]["maximum_total_rows"],
                      "openfoam_launches": 0, "puckworks_calls": 0,
                      "adjudicative_trajectories": 0, "scientific_classifications_generated": 0},
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
