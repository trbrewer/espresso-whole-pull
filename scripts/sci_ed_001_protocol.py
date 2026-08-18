#!/usr/bin/env python3
"""Generate and verify the prospective SCI-ED-001 design package."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/cases/sci_ed_001"
DOC = ROOT / "docs/analysis/sci_ed_001"
START_HEAD = "e8a66378d7829877fb74c87889193f32dd977772"
START_TREE = "1c51175a8c5035c0cab989fada791aebb78f6fd7"
TASK = "SCI-ED-001"


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"


def hash_obj(obj: Any) -> str:
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"MODEL_IMPORT_UNAVAILABLE:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def aggregate(paths: list[Path]) -> str:
    records = []
    for base in paths:
        if base.is_file():
            files = [base]
        elif base.exists():
            files = sorted(p for p in base.rglob("*") if p.is_file())
        else:
            files = []
        for path in files:
            records.append([path.relative_to(ROOT).as_posix(), sha(path)])
    return hash_obj(sorted(records))


def programs() -> list[dict[str, Any]]:
    raw = [
        ("P0_CONST_5BAR", [(0, 500000), (80, 500000)]),
        ("P1_CONST_9BAR", [(0, 500000), (1, 900000), (80, 900000)]),
        ("P2_CONST_11BAR", [(0, 500000), (1, 1100000), (80, 1100000)]),
        ("P3_UPSTEP_5_TO_11", [(0, 500000), (20, 500000), (21, 1100000), (80, 1100000)]),
        ("P4_DOWNSTEP_11_TO_5", [(0, 500000), (1, 1100000), (20, 1100000), (21, 500000), (80, 500000)]),
        ("P5_PULSE_9_11_9", [(0, 500000), (1, 900000), (20, 900000), (21, 1100000), (26, 1100000), (27, 900000), (80, 900000)]),
        ("P6_UNLOAD_9_0_9", [(0, 500000), (1, 900000), (20, 900000), (21, 0), (31, 0), (32, 900000), (80, 900000)]),
        ("P7_CYCLE_5_11_5_11_5", [(0, 500000), (1, 1100000), (15, 1100000), (16, 500000), (30, 500000), (31, 1100000), (45, 1100000), (46, 500000), (80, 500000)]),
        ("P8_SLOW_RAMP_5_TO_9", [(0, 500000), (10, 900000), (80, 900000)]),
    ]
    return [{"program_id": pid, "kind": "SYNTHETIC_VIRTUAL_EXPERIMENT_PROGRAM",
             "apparatus_feasibility": "NOT_ESTABLISHED", "commissioning": "NOT_AUTHORIZED",
             "interpolation": "PIECEWISE_LINEAR", "pressure_node": "P_BASKET_BED_TOP_PA_GAUGE",
             "ambient_outlet_pa_gauge": 0, "horizon_s": 80.0,
             "breakpoints": [{"time_s": float(t), "pressure_pa_gauge": float(p)} for t, p in pts]}
            for pid, pts in raw]


def measurement_packages() -> list[dict[str, Any]]:
    rows = [
        ("M0", ["basket_pressure", "outlet_flow", "cumulative_mass"], 3, 0, "CORE", 0),
        ("M1", ["basket_pressure", "outlet_flow", "cumulative_mass", "upstream_pressure"], 4, 1, "MEDIUM", 0),
        ("M2", ["basket_pressure", "outlet_flow", "cumulative_mass", "bed_deformation"], 4, 1, "MEDIUM", 1),
        ("M3", ["basket_pressure", "outlet_flow", "cumulative_mass", "effluent_fines", "retained_fines"], 5, 1, "HIGH", 2),
        ("M4", ["basket_pressure", "outlet_flow", "cumulative_mass", "first_drip", "wetting_timing"], 5, 1, "HIGH", 2),
        ("M5", ["basket_pressure", "outlet_flow", "cumulative_mass", "upstream_pressure", "bed_deformation"], 5, 2, "HIGH", 1),
        ("M6", ["basket_pressure", "upstream_pressure", "outlet_flow", "cumulative_mass", "bed_deformation", "first_drip", "wetting_timing", "effluent_fines"], 8, 4, "VERY_HIGH", 4),
    ]
    return [{"measurement_package_id": x[0], "observables": x[1], "sensor_class_count": x[2],
             "additional_sensor_class_count": x[3], "synchronization_burden_class": x[4],
             "direct_mechanism_measurement_count": x[5]} for x in rows]


def features() -> list[dict[str, Any]]:
    names = [
        "pre_event_mean", "post_event_terminal", "signed_response_amplitude", "normalized_response_amplitude",
        "t10_s", "t50_s", "t90_s", "rise_or_decay_time_s", "overshoot", "undershoot", "settling_fraction",
        "flow_recovery_fraction", "resistance_recovery_fraction", "post_unload_residual_resistance",
        "post_reload_residual_resistance", "resistance_hysteresis_area", "cycle_to_cycle_drift",
        "pulse_gain", "pulse_lag_s", "pulse_integrated_mass_change_kg", "post_pulse_residual", "recovery_time_s",
        "fast_slow_flow_path_difference", "fast_slow_resistance_path_difference", "fast_slow_mass_difference_kg",
        "maximum_compression_m", "maximum_expansion_m", "pressure_deformation_lag_s", "deformation_t50_s",
        "unload_deformation_recovery_fraction", "residual_deformation_m", "height_hysteresis_area",
        "full_wetting_time_s", "swelling_storage_uptake_m3", "bed_height_growth_m", "wetting_post_unload_persistence",
        "peak_release_rate_kg_s", "peak_outlet_fines_flux_kg_s", "time_to_outlet_fines_peak_s",
        "cumulative_released_mass_kg", "cumulative_escaped_mass_kg", "cumulative_deposited_mass_kg",
        "cake_resistance_pa_s_m3", "pause_tail_kg_s", "reload_remobilization_response", "terminal_inventory_kg",
        "fines_mass_conservation_residual_kg", "upstream_basket_pressure_difference_pa", "upstream_basket_lag_s",
    ]
    return [{"feature_id": name, "frozen_before_execution": True,
             "missing_output": "NOT_COMPARABLE", "structural_zero_requires_predecessor_contract": True}
            for name in names]


def inclusion_ledger() -> list[dict[str, Any]]:
    a = load_module("sci_md_002a_ro", ROOT / "scripts/sci_md_002a.py")
    b = load_module("sci_md_002b_ro", ROOT / "scripts/sci_md_002b.py")
    c = load_module("sci_md_002c_ro", ROOT / "scripts/sci_md_002c.py")
    result: list[dict[str, Any]] = []
    a_result = json.loads((OUT.parent / "sci_md_002a/SCI_MD_002A_RESULT.json").read_text())
    for item in a_result["pressure_candidates"]:
        stem = f"PC{item['pc']}-TH{item['theta']}"
        for family in ("F_TPM", "F_GENERIC"):
            result.append({"family_id": family, "predecessor_task": "SCI-MD-002A", "parameter_stem_id": stem,
                           "parameters": {"critical_pressure_pa": item["pc"], "theta_c": item["theta"]},
                           "inclusion_status": "INCLUDED", "inclusion_basis": "EVERY_VALID_SHARED_FINITE_RATE_CONSTITUTIVE_SET",
                           "exclusion_status": "NOT_EXCLUDED", "exclusion_basis": None,
                           "source_artifact": "validation/cases/sci_md_002a/SCI_MD_002A_RESULT.json",
                           "source_hash": sha(OUT.parent / "sci_md_002a/SCI_MD_002A_RESULT.json"),
                           "scientific_role": "PRIMARY_FAMILY"})
    b_result = json.loads((OUT.parent / "sci_md_002b/SCI_MD_002B_RESULT.json").read_text())
    for item in b_result["candidates"]:
        p = item["candidate"]
        stem = f"{p['powder']}-D{p['D_multiplier']}-CM{p['cmax']}-AC{p['accommodation']}"
        included = bool(item["physical_numerical_valid"])
        result.append({"family_id": "F_SWELL", "predecessor_task": "SCI-MD-002B", "parameter_stem_id": stem,
                       "parameters": p, "inclusion_status": "INCLUDED" if included else "EXCLUDED",
                       "inclusion_basis": "EVERY_COMPLETE_NUMERICALLY_AND_PHYSICALLY_VALID_CANDIDATE" if included else None,
                       "exclusion_status": "NOT_EXCLUDED" if included else "EXCLUDED_INVALID",
                       "exclusion_basis": None if included else "PREDECESSOR_PHYSICAL_OR_NUMERICAL_INVALIDITY",
                       "source_artifact": "validation/cases/sci_md_002b/SCI_MD_002B_RESULT.json",
                       "source_hash": sha(OUT.parent / "sci_md_002b/SCI_MD_002B_RESULT.json"), "scientific_role": "PRIMARY_FAMILY"})
    c_result = json.loads((OUT.parent / "sci_md_002c/SCI_MD_002C_RESULT.json").read_text())
    for index, item in enumerate(c_result["candidates"]):
        p = item["candidate_parameters"]
        stem = f"C{index:03d}-FF{p['fines_fraction']}-MF{p['mobilizable_fraction']}-KR{p['release_rate_s']}-N{p['release_exponent']}-RET{p['retention_fraction']}-AR{p['specific_cake_resistance_m_kg']:.0e}"
        included = bool(item["inventory_feasible"] and item["numerical_physical_valid"])
        result.append({"family_id": "F_FINES", "predecessor_task": "SCI-MD-002C", "parameter_stem_id": stem,
                       "parameters": p, "inclusion_status": "INCLUDED" if included else "CONTROL_ONLY_EXCLUDED_FROM_VIABLE_ENVELOPE",
                       "inclusion_basis": "ANALYTICALLY_INVENTORY_FEASIBLE_AND_NUMERICALLY_PHYSICALLY_VALID" if included else None,
                       "exclusion_status": "NOT_EXCLUDED" if included else "INVENTORY_IMPOSSIBLE_CONTROL",
                       "exclusion_basis": None if included else "PREDECESSOR_FINITE_INVENTORY_FEASIBILITY",
                       "source_artifact": "validation/cases/sci_md_002c/SCI_MD_002C_RESULT.json",
                       "source_hash": sha(OUT.parent / "sci_md_002c/SCI_MD_002C_RESULT.json"),
                       "scientific_role": "PRIMARY_FAMILY" if included else "PROVENANCE_CONTROL"})
    assert len([x for x in result if x["family_id"] == "F_TPM" and x["inclusion_status"] == "INCLUDED"]) == 35
    assert len([x for x in result if x["family_id"] == "F_GENERIC" and x["inclusion_status"] == "INCLUDED"]) == 35
    assert len([x for x in result if x["family_id"] == "F_SWELL" and x["inclusion_status"] == "INCLUDED"]) == 72
    assert len([x for x in result if x["family_id"] == "F_FINES" and x["inclusion_status"] == "INCLUDED"]) == 4
    # Imports are intentional read-only interface checks.
    assert all(hasattr(m, "simulate") for m in (a, b, c))
    return result


def family_registry() -> list[dict[str, Any]]:
    return [
        {"family_id": "F_TPM", "name": "TRANSIENT_POROMECHANICS_SINGLE_MODE", "role": "PRIMARY", "predecessor": "SCI-MD-002A"},
        {"family_id": "F_SWELL", "name": "WETTING_AGE_SWELLING_ONE_WAY", "role": "PRIMARY", "predecessor": "SCI-MD-002B"},
        {"family_id": "F_FINES", "name": "AXIAL_FINES_DEPOSITION_FIXED_ACTIVE_BED", "role": "PRIMARY", "predecessor": "SCI-MD-002C"},
        {"family_id": "F_GENERIC", "name": "GENERIC_RELAXING_RESISTANCE", "role": "PRIMARY", "predecessor": "SCI-MD-002A"},
        {"family_id": "C_FIXED", "name": "FIXED_HYDRAULICS", "role": "CONTROL", "predecessor": "SCI-MD-002A"},
        {"family_id": "C_QS", "name": "QUASI_STATIC_COMPACTION", "role": "CONTROL", "predecessor": "SCI-MD-002A"},
        {"family_id": "C_NO_SWELL", "name": "NO_SWELLING_CONTROL", "role": "CONTROL", "predecessor": "SCI-MD-002B"},
        {"family_id": "C_NO_FINES", "name": "NO_FINES_CONTROL", "role": "CONTROL", "predecessor": "SCI-MD-002C"},
        {"family_id": "C_MACHINE", "name": "FIXED_PUCK_MACHINE_RESPONSE", "role": "OPTIONAL_APPARATUS_CONTROL", "status": "MACHINE_LAYER_NOT_COMMON"},
    ]


def compatibility(families: list[dict[str, Any]], progs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for f in families:
        for p in progs:
            status = "DIRECTLY_EXECUTABLE" if f["family_id"] in {"F_TPM", "F_GENERIC", "C_FIXED", "C_QS"} else "EXECUTABLE_THROUGH_EXISTING_DECLARED_ADAPTER"
            if f["family_id"] == "C_MACHINE": status = "MACHINE_LAYER_NOT_COMMON"
            rows.append({"family_id": f["family_id"], "program_id": p["program_id"], "status": status})
    return rows


def case_matrix(ledger: list[dict[str, Any]], progs: list[dict[str, Any]], phash: str, fhash: str) -> list[dict[str, Any]]:
    rows = []
    for item in ledger:
        if item["inclusion_status"] != "INCLUDED":
            continue
        for program in progs:
            for resolution, dt in (("BASE", 0.02), ("REFINED", 0.01)):
                seed = [item["family_id"], item["parameter_stem_id"], program["program_id"], resolution]
                rid = "SED-" + hashlib.sha256(canonical(seed).encode()).hexdigest()[:20].upper()
                rows.append({"row_id": rid, "task_id": TASK, "family_id": item["family_id"],
                             "parameter_stem_id": item["parameter_stem_id"], "program_id": program["program_id"],
                             "preconditioning_id": "PRE_5BAR_FULL_WETTING_BOUND_PLUS_MARGIN",
                             "measurement_package_id": "ALL_FROZEN_MEASUREMENT_PACKAGES_REDUCTION_PROJECTION",
                             "noise_scenario_id": "N0_AND_N1_REDUCTION_PROJECTION", "resolution_id": resolution,
                             "internal_timestep_s": dt, "execution_role": "ADJUDICATIVE_PRIMARY_RESPONSE",
                             "source_model_hash": item["source_hash"], "source_parameter_hash": hash_obj(item["parameters"]),
                             "pressure_program_hash": phash, "feature_definition_hash": fhash,
                             "initial_state_contract": "CANONICAL_PREDECESSOR_START_EVOLVED_WITHOUT_DESIGN_CLOCK_RESET",
                             "output_grid_id": "EVENT_ALIGNED_20MS", "expected_outputs": "FAMILY_DECLARED_OUTPUTS",
                             "adjudicative": True})
    if len(rows) != 2628 or len({r["row_id"] for r in rows}) != len(rows):
        raise RuntimeError("PRIMARY_MATRIX_COUNT_OR_ID_INVALID")
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True); DOC.mkdir(parents=True, exist_ok=True)
    progs = programs(); packages = measurement_packages(); feats = features(); ledger = inclusion_ledger(); families = family_registry()
    pdoc = {"schema_version": "espresso.whole_pull.sci_ed_001.pressure_programs.v1", "programs": progs}
    fdoc = {"schema_version": "espresso.whole_pull.sci_ed_001.features.v1", "denominator_floor_m3_s": 1e-12,
            "normalizations": ["Q(t)/Q_pre_event", "R_app(t)/R_pre_event", "H(t)/H_pre_event", "program_minus_matched_constant", "post_minus_pre"],
            "event_windows": {"pre_event_s": [-2.0, 0.0], "immediate_post_event_s": [0.0, 2.0], "late_post_event_s": [10.0, 20.0]},
            "features": feats}
    (OUT / "PRESSURE_PROGRAMS.json").write_text(canonical(pdoc)); write_csv(OUT / "PRESSURE_PROGRAMS.csv", [dict(program_id=p["program_id"], horizon_s=p["horizon_s"], breakpoints=canonical(p["breakpoints"]).strip()) for p in progs])
    (OUT / "MEASUREMENT_PACKAGES.json").write_text(canonical({"schema_version": "espresso.whole_pull.sci_ed_001.measurements.v1", "packages": packages}))
    (OUT / "FEATURE_DEFINITIONS.json").write_text(canonical(fdoc))
    (OUT / "MODEL_FAMILY_REGISTRY.json").write_text(canonical({"schema_version": "espresso.whole_pull.sci_ed_001.families.v1", "families": families}))
    (OUT / "MODEL_FAMILY_INCLUSION_LEDGER.json").write_text(canonical({"schema_version": "espresso.whole_pull.sci_ed_001.inclusion.v1", "eligible_counts": {"F_TPM": 35, "F_SWELL": 72, "F_FINES": 4, "F_GENERIC": 35}, "rows": ledger}))
    comp = compatibility(families, progs)
    (OUT / "MODEL_PROGRAM_COMPATIBILITY_MATRIX.json").write_text(canonical({"schema_version": "espresso.whole_pull.sci_ed_001.compatibility.v1", "rows": comp}))
    observable_rows = []
    for f in families:
        for observable in ["basket_pressure", "outlet_flow", "cumulative_mass", "apparent_resistance", "bed_deformation", "first_drip", "wetting_timing", "effluent_fines", "upstream_pressure"]:
            status = "DIRECTLY_EXECUTABLE"
            if observable == "bed_deformation" and f["family_id"] not in {"F_TPM", "F_SWELL", "C_QS"}: status = "MODEL_FAMILY_STRUCTURAL_ZERO" if f["family_id"] in {"C_FIXED", "C_NO_SWELL", "C_NO_FINES"} else "NOT_PREDICTED_BY_FAMILY"
            if observable in {"first_drip", "wetting_timing"} and f["family_id"] != "F_SWELL": status = "NOT_PREDICTED_BY_FAMILY"
            if observable == "effluent_fines" and f["family_id"] != "F_FINES": status = "MODEL_FAMILY_STRUCTURAL_ZERO" if f["family_id"] in {"C_NO_FINES"} else "NOT_PREDICTED_BY_FAMILY"
            if observable == "upstream_pressure": status = "MACHINE_LAYER_NOT_COMMON"
            observable_rows.append({"family_id": f["family_id"], "observable_id": observable, "status": status})
    (OUT / "OBSERVABLE_COMPATIBILITY_MATRIX.json").write_text(canonical({"schema_version": "espresso.whole_pull.sci_ed_001.observable_compatibility.v1", "rows": observable_rows}))
    noise = {"schema_version": "espresso.whole_pull.sci_ed_001.noise.v1", "method": "CONSERVATIVE_INTERVAL_EXPANSION_NO_PROBABILITY_DISTRIBUTION",
             "scenarios": [{"noise_scenario_id": "N0", "name": "NUMERICAL_ONLY"}, {"noise_scenario_id": "N1", "name": "VAL_DATA_001_MODEL_INFORMED_PLANNING_TARGETS", "targets_si": {"basket_pressure_pa": 8000.0, "upstream_pressure_pa": 8000.0, "outlet_volume_flow_m3_s": 2e-8, "cumulative_mass_kg": 5e-4, "bed_deformation_m": 5e-5, "native_sample_interval_s": 0.02, "inter_channel_synchronization_s": 0.02, "physical_first_drip_s": 0.02}, "status": ["MODEL_INFORMED_FUTURE_DESIGN_TARGET", "NOT_VALIDATION_THRESHOLD", "NOT_DEMONSTRATED_SENSOR_UNCERTAINTY", "NOT_PROCUREMENT_SPECIFICATION"], "fines": "FINES_MEASUREMENT_TARGET_NOT_PROVIDED"}]}
    (OUT / "PLANNING_NOISE_MODEL.json").write_text(canonical(noise))
    matrix = case_matrix(ledger, progs, sha(OUT / "PRESSURE_PROGRAMS.json"), sha(OUT / "FEATURE_DEFINITIONS.json"))
    (OUT / "SCI_ED_001_CASE_MATRIX.json").write_text(canonical({"schema_version": "espresso.whole_pull.sci_ed_001.matrix.v1", "row_count": len(matrix), "unique_response_count": len(matrix), "adaptive_row_insertion": "FORBIDDEN", "rows": matrix}))
    write_csv(OUT / "SCI_ED_001_CASE_MATRIX.csv", matrix)
    source_paths = [f"scripts/sci_md_002{x}.py" for x in "abc"] + [f"validation/cases/sci_md_002{x}/SCI_MD_002{x.upper()}_RESULT.json" for x in "abc"]
    source = {"schema_version": "espresso.whole_pull.sci_ed_001.source_binding.v1", "starting_head": START_HEAD, "starting_tree": START_TREE,
              "bindings": [{"path": p, "sha256": sha(ROOT / p), "access": "READ_ONLY"} for p in source_paths],
              "puckworks_calls": 0, "openfoam_launches": 0, "rpa_executions": 0}
    (OUT / "SOURCE_BINDING.json").write_text(canonical(source))
    protocol = {"schema_version": "espresso.whole_pull.sci_ed_001.protocol.v1", "task_id": TASK, "issue": 79,
                "status": "PROSPECTIVE_FROZEN_BEFORE_NEW_VIRTUAL_RESPONSE", "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
                "task_class": "VIRTUAL_EXPERIMENT_DESIGN_AND_MECHANISM_DISCRIMINATION", "evidence_class": "POST_OBSERVATION_MODEL_INFORMED_MEASUREMENT_DESIGN",
                "hypotheses": [f"H{i}" for i in range(9)], "preconditioning": {"pressure_node": "P_BASKET_BED_TOP_PA_GAUGE", "pressure_pa_gauge": 500000.0, "hydraulic_anchor_m2": 2.7738376540492074e-15, "full_wetting_upper_bound_s": 3.6566667790356795, "safety_margin_s": 1.0, "duration_s": 4.65666677903568, "duration_rule": "maximum analytically bounded full-wetting time at 5 bar over complete retained swelling family plus max(1.0 s, 10% safety margin)", "family_state_evolution": {"F_TPM": "CONSOLIDATION_STATE_EVOLVES", "F_SWELL": "WETTING_AND_SWELLING_STATES_EVOLVE", "F_FINES": "RELEASE_TRANSPORT_DEPOSITION_EVOLVE_FROM_CANONICAL_SYNTHETIC_RESET", "F_GENERIC": "RELAXATION_STATE_EVOLVES", "controls": "FIXED_CONTROLS_REMAIN_FIXED"}, "state_reset_at_design_clock": False, "fines_start": "SYNTHETIC_WINDOW_START_RESET", "fines_limitation": "PRE_WINDOW_FINES_STATE_NOT_ADJUDICATED"},
                "output_grid": {"id": "EVENT_ALIGNED_20MS", "base_internal_timestep_s": 0.02, "refined_internal_timestep_s": 0.01, "output_interval_s": 0.02, "interpolation": "PIECEWISE_LINEAR", "integration": "TRAPEZOIDAL", "exact_breakpoints": True},
                "uncertainty": {"numeric": "ABSOLUTE_BASE_REFINED_FEATURE_DIFFERENCE", "parameter": "COMPLETE_DISCRETE_FAMILY_ENVELOPE", "measurement": "INTERVAL_EXPANSION", "gaussian_noise": False},
                "separation": {"statuses": ["ROBUSTLY_SEPARATED", "OVERLAPPING", "NUMERICALLY_UNRESOLVED", "NOT_COMPARABLE", "DIRECT_MEASUREMENT_TARGET_NOT_QUANTIFIED"], "margin": "max(lower_B-upper_A,lower_A-upper_B)", "primary_pairs": 6},
                "ranking": ["N1_robust_pair_count_desc", "minimum_positive_margin_desc", "unresolved_pair_count_asc", "additional_sensor_classes_asc", "pressure_transitions_asc", "peak_pressure_asc", "duration_asc", "program_id_asc"],
                "set_cover": {"maximum_programs": 3, "deterministic": True, "complete_library_only": True},
                "matched_companions": {"P3_UPSTEP_5_TO_11": "P2_CONST_11BAR", "P4_DOWNSTEP_11_TO_5": "P0_CONST_5BAR", "P5_PULSE_9_11_9": "P1_CONST_9BAR", "P6_UNLOAD_9_0_9": "P1_CONST_9BAR", "P8_SLOW_RAMP_5_TO_9": "P1_CONST_9BAR"},
                "resource_limits": {"workers": "max(1,min(8,floor(0.125*logical_cpu_count)))", "nested_threads": 1, "memory_gib": 16, "gpu": 0, "openfoam": 0, "puckworks": 0, "target_hours": 4, "hard_review_hours": 8},
                "execution": {"external_namespace": "SCI_ED_001_EXTERNAL_BUNDLE", "immutable_attempts": True, "atomic_records": True, "adjudicative_row_count": len(matrix), "adaptive_rows": "FORBIDDEN"},
                "claim_boundary": ["MODEL_INFORMED_FUTURE_DESIGN_ONLY", "PHYSICAL_VALIDATION_NOT_ESTABLISHED", "EXPERIMENTAL_COMMISSIONING_NOT_AUTHORIZED", "NO_COMBINED_MECHANISM_AUTHORIZATION", "NO_DYNAMIC_LOCALIZATION_RESULT", "NO_SCI_LC_001B_AUTHORIZATION"]}
    (OUT / "SCI_ED_001_PROTOCOL.json").write_text(canonical(protocol))
    prospective = [p for p in sorted(OUT.iterdir()) if p.name not in {"SCI_ED_001_PROTOCOL.json"}]
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in prospective}
    protocol["prospective_artifact_sha256"] = hashes
    (OUT / "SCI_ED_001_PROTOCOL.json").write_text(canonical(protocol))
    return {"row_count": len(matrix), "eligible_counts": {"F_TPM": 35, "F_SWELL": 72, "F_FINES": 4, "F_GENERIC": 35}, "protocol_sha256": sha(OUT / "SCI_ED_001_PROTOCOL.json")}


def verify() -> dict[str, Any]:
    before = {p: p.read_bytes() for p in OUT.glob("*") if p.is_file()}
    result = generate()
    after = {p: p.read_bytes() for p in OUT.glob("*") if p.is_file()}
    if before and before != after:
        raise RuntimeError("PROSPECTIVE_GENERATION_NOT_BYTE_STABLE")
    matrix = json.loads((OUT / "SCI_ED_001_CASE_MATRIX.json").read_text())
    if matrix["row_count"] != 2628 or len({r["row_id"] for r in matrix["rows"]}) != 2628:
        raise RuntimeError("MATRIX_INVALID")
    return {"status": "PASS", **result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=["generate", "verify"])
    args = parser.parse_args(); print(canonical(generate() if args.command == "generate" else verify()), end="")
