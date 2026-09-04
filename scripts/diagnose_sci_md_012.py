#!/usr/bin/env python3
"""SCI-MD-012: bounded, non-scoring diagnosis of the E2C 13-bar root blocker."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import subprocess
from pathlib import Path

TASK = "SCI-MD-012"
FOLD = "HYD-LOCO-13.0"
E2C = "HYD_E2C_EWP_FINITE_PHI_POROELASTIC_COMPONENT"
P1 = "HYD_P1_POROELASTIC_UNIVERSAL_LIMIT"
CLAIM = "RETROSPECTIVE_TARGET_EXPOSED_NONSCORING_EXISTING_DATA_ROOT_BLOCKER_DIAGNOSIS_ONLY"
OWNER = "SCI-MD-012-OWNER-AUTHORIZE-BOUNDED-NONSCORING-EXISTING-DATA-E2C-13BAR-COUPLED-ROOT-DIAGNOSIS-NO-REFIT-NO-NEW-SCORE-NO-PHYSICS-CHANGE-NO-MEASUREMENT-2026-09-03"
BASE_COMMIT = "6451cfe04ff10bd9c4ec706ccafc895619cf9851"
BASE_TREE = "b23347e33c67576b786922762eae168bf06b28fa"
RESULT_HEAD = "78cbd59c751393cddfe539e4c69e43a224329bca"
PUCK_COMMIT = "2058d0e947ee9eb92c52d64f6165b810f1fb4732"
PUCK_TREE = "a6ffb312473b15be43c1571a893b19873ea47c5a"
PUCK_PATH = "puckworks/models/waszkiewicz2025/poroelastic.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def load_core(root: Path, expected: str):
    path = root / "scripts/sci_md_011_core.py"
    if sha(path) != expected:
        raise RuntimeError("SCI_MD_011_CORE_HASH_MISMATCH")
    spec = importlib.util.spec_from_file_location("sci_md_011_core_frozen", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def manifest_hashes(root: Path) -> dict[str, str]:
    d = root / "docs/analysis/sci_md_011"
    result = read_json(d / "RESULT_ARTIFACT_MANIFEST.json")
    freeze = read_json(d / "FREEZE_ARTIFACT_MANIFEST.json")
    expected = {x["path"]: x["sha256"] for x in freeze["artifacts"]}
    expected.update({"docs/analysis/sci_md_011/" + x["path"]: x["sha256"] for x in result["artifacts"]})
    required = [
        "RESULT.md", "BREW_RESULTS.csv", "FOLD_RESULTS.csv", "PARAMETER_STABILITY.csv",
        "IDENTIFIABILITY_RESULTS.json", "MODEL_SPECIFICATIONS.json", "OBSERVATION_INTERFACE.json",
        "EWP_CLOSURE_EQUIVALENCE.json", "PRESSURE_RESPONSE_DIAGNOSTICS.json",
        "EXPERIMENT_CONSEQUENCE.json", "EXECUTION_STATE.json", "RESULT_ARTIFACT_MANIFEST.json",
        "FREEZE_ARTIFACT_MANIFEST.json",
    ]
    actual = {}
    for name in required:
        path = d / name
        key = "docs/analysis/sci_md_011/" + name
        digest = sha(path)
        if name not in ("RESULT_ARTIFACT_MANIFEST.json", "FREEZE_ARTIFACT_MANIFEST.json") and expected.get(key) != digest:
            raise RuntimeError("SCI_MD_011_ARTIFACT_HASH_MISMATCH:" + name)
        actual[key] = digest
    core_key = "scripts/sci_md_011_core.py"
    if sha(root / core_key) != expected[core_key]:
        raise RuntimeError("SCI_MD_011_CORE_HASH_MISMATCH")
    actual[core_key] = expected[core_key]
    return actual


def parse_parameters(raw: str) -> dict:
    value = json.loads(raw)
    if isinstance(value, str):
        value = json.loads(value)
    return value


def recover(root: Path):
    d = root / "docs/analysis/sci_md_011"
    with (d / "FOLD_RESULTS.csv").open(newline="") as f:
        folds = list(csv.DictReader(f))
    chosen = {(r["outer_fold"], r["model_id"]): r for r in folds}
    e2c_row, p1_row = chosen[(FOLD, E2C)], chosen[(FOLD, P1)]
    e2c, p1 = parse_parameters(e2c_row["fitted_parameters"]), parse_parameters(p1_row["fitted_parameters"])
    if e2c_row["failure_reason"] != "NO_ADMISSIBLE_ROOT" or e2c_row["domain_failure_count"] != "0":
        raise RuntimeError("SCI_MD_011_RECORDED_FAILURE_MISMATCH")
    with (d / "BREW_RESULTS.csv").open(newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["outer_fold"] == FOLD]
    by_id = {}
    for row in rows:
        key = row["physical_unit_id"]
        obs = (row["source_row_id"], row["condition_id"], float(row["line_pressure_bar"]), float(row["observed_flow_g_s"]))
        if key in by_id and by_id[key][0] != obs:
            raise RuntimeError("DUPLICATED_OBSERVATION_MISMATCH:" + key)
        by_id[key] = (obs, row)
    if len(by_id) != 6:
        raise RuntimeError("EXPECTED_SIX_UNIQUE_BREWS")
    brews = [pair[1] for pair in sorted(by_id.values(), key=lambda x: x[0][0])]
    return folds, brews, e2c_row, p1_row, e2c, p1


def quadratic_q(core, target_drop: float) -> float | None:
    a, b, c = core.CAL["a"], core.CAL["b"], core.CAL["c"]
    disc = b*b - 4*a*(c-target_drop)
    if disc < 0:
        return None
    roots = [(-b-math.sqrt(disc))/(2*a), (-b+math.sqrt(disc))/(2*a)]
    valid = [q for q in roots if q >= 0]
    return min(valid) if valid else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--puckworks-repo", type=Path, required=True)
    args = ap.parse_args(); root = args.root.resolve(); out = root / "docs/analysis/sci_md_012"
    hashes = manifest_hashes(root)
    core = load_core(root, hashes["scripts/sci_md_011_core.py"])
    if git(root, "rev-parse", BASE_COMMIT + "^{tree}") != BASE_TREE:
        raise RuntimeError("EWP_BASE_TREE_MISMATCH")
    if git(args.puckworks_repo, "rev-parse", PUCK_COMMIT + "^{tree}") != PUCK_TREE:
        raise RuntimeError("PUCKWORKS_TREE_MISMATCH")
    source = subprocess.check_output(["git", "-C", str(args.puckworks_repo), "show", f"{PUCK_COMMIT}:{PUCK_PATH}"])
    source_hash = hashlib.sha256(source).hexdigest()
    source_text = source.decode()
    for token in ("Valid for P <= P_c", "caller\n    decides clamping above P_c", "monotone and =1", "cannot produce the slight high-pressure flow", "popt, pcov = curve_fit", "bounds=((P.max(), 0.01)", "NOT transferable"):
        if token not in source_text:
            raise RuntimeError("PUCKWORKS_SEMANTIC_TOKEN_MISSING:" + token)

    folds, brews, e2c_row, p1_row, e2c, p1 = recover(root)
    qc, pc = e2c["Qc_g_s"], e2c["Pc_bar"]
    first_failure = None
    for row in brews:
        try: core.predict(float(row["line_pressure_bar"]), qc, pc, core.E2C)
        except ValueError as exc:
            first_failure = (row["physical_unit_id"], str(exc)); break
    if first_failure != (brews[0]["physical_unit_id"], "NO_ADMISSIBLE_ROOT"):
        raise RuntimeError("ORIGINAL_FAILURE_NOT_REPRODUCED")

    endpoint_shape = core.fphi(1-core.DOMAIN_EPS)
    diagnostic_rows = []
    pc_thresholds = []; qc_thresholds = []
    domain_failures = 0
    for row in brews:
        line, observed = float(row["line_pressure_bar"]), float(row["observed_flow_g_s"])
        hi = min(pc*(1-core.DOMAIN_EPS), max(0.0, line-core.CAL["c"]))
        xhi = hi/pc
        exception = ""
        try: shape = core.fphi(xhi); finite = math.isfinite(shape)
        except Exception as exc:  # exact diagnostic capture
            shape = math.nan; finite = False; exception = type(exc).__name__; domain_failures += 1
        qhi = qc*shape
        hlo = core.brewer_drop(qc*core.fphi(0))-line
        hhi = hi+core.brewer_drop(qhi)-line
        ceiling = hi+core.brewer_drop(qhi)
        try: core.predict(line, qc, pc, core.E2C); status = "PASS"
        except ValueError as exc: status = str(exc)
        adapter = core.brewer_drop(qhi)
        role = "MITIGATING" if adapter > core.PRESSURE_TOL else "ADVERSE" if adapter < -core.PRESSURE_TOL else "NEUTRAL_WITHIN_TOLERANCE"
        pc_req = (line-core.brewer_drop(qc*endpoint_shape))/(1-core.DOMAIN_EPS)
        target_drop = line-pc*(1-core.DOMAIN_EPS)
        endpoint_q = quadratic_q(core, target_drop)
        qc_req = None if endpoint_q is None else endpoint_q/endpoint_shape
        implied_pb = line-core.brewer_drop(observed)
        pc_thresholds.append(pc_req); qc_thresholds.append(qc_req)
        diagnostic_rows.append({
            "fold_id": FOLD, "condition_id": row["condition_id"], "brew_id": row["physical_unit_id"],
            "measured_line_pressure_bar": line, "observed_flow_g_s": observed,
            "frozen_Qc_g_s": qc, "frozen_Pc_bar": pc, "hi_basket_pressure_bar": hi, "x_hi": xhi,
            "q_hi_g_s": qhi, "h_lo_bar": hlo, "h_hi_bar": hhi,
            "closure_only_endpoint_bar": hi, "machine_adapter_contribution_bar": adapter,
            "coupled_line_pressure_ceiling_bar": ceiling, "representability_margin_bar": ceiling-line,
            "exact_predict_status": status, "root_admissible": hlo <= core.PRESSURE_TOL and hhi >= -core.PRESSURE_TOL,
            "closure_domain_valid": 0 <= xhi <= 1 and finite, "normalized_input_inside_0_1": 0 <= xhi <= 1,
            "fphi_finite": finite, "fphi_exception_class": exception, "machine_adapter_role": role,
            "counterfactual_line_as_basket_failure": "LARGER" if adapter > core.PRESSURE_TOL else "SMALLER" if adapter < -core.PRESSURE_TOL else "UNCHANGED",
            "counterfactual_is_authorized_observation_operator": False, "Pc_required_bar": pc_req,
            "Qc_required_g_s_at_frozen_Pc": qc_req,
            "observed_flow_implied_basket_pressure_bar": implied_pb,
            "observed_pair_x_at_frozen_Pc": implied_pb/pc,
            "observed_pair_requires_x_gt_1": implied_pb/pc > 1,
            "target_exposed": True, "prediction": False, "scoring_use_prohibited": True, "fitting_use_prohibited": True,
        })

    max_pc = max(pc_thresholds); max_qc = max(q for q in qc_thresholds if q is not None)
    fold_pcs = [float(r["Pc_bar"]) for r in csv.DictReader((root/"docs/analysis/sci_md_011/PARAMETER_STABILITY.csv").open()) if r["model_id"] == E2C and r["Pc_bar"] and r["outer_fold"] != FOLD]
    ident = read_json(root/"docs/analysis/sci_md_011/IDENTIFIABILITY_RESULTS.json")["folds"][FOLD+"|"+E2C]
    profiles = []
    for parameter, points in ident["diagnostics"]["profile_scans"].items():
        base = pc if parameter == "log_Pc" else qc
        threshold = max_pc if parameter == "log_Pc" else max_qc
        for point in points:
            profiles.append({"parameter": parameter, "offset": point["offset"], "implied_value": base*math.exp(point["offset"]), "frozen_profile_objective": point["objective"], "finite": point["objective"] is not None, "crosses_root_feasibility_threshold": point["objective"] is not None and base*math.exp(point["offset"]) >= threshold})
    witness_pc = max_pc + core.PRESSURE_TOL/(1-core.DOMAIN_EPS)
    witness_qc = qc
    witness = []
    for row in diagnostic_rows:
        ceiling = witness_pc*(1-core.DOMAIN_EPS)+core.brewer_drop(witness_qc*endpoint_shape)
        witness.append({"brew_id": row["brew_id"], "line_pressure_bar": row["measured_line_pressure_bar"], "coupled_endpoint_ceiling_bar": ceiling, "margin_bar": ceiling-row["measured_line_pressure_bar"], "root_admissible": ceiling-row["measured_line_pressure_bar"] >= -core.PRESSURE_TOL})
    family_ok = core.BOUNDS["Pc_bar"][0] <= witness_pc <= core.BOUNDS["Pc_bar"][1] and core.BOUNDS["Qc_g_s"][0] <= witness_qc <= core.BOUNDS["Qc_g_s"][1] and all(x["root_admissible"] for x in witness)
    pressure = read_json(root/"docs/analysis/sci_md_011/PRESSURE_RESPONSE_DIAGNOSTICS.json")
    p1pressure, e2cpressure = pressure[P1], pressure[E2C]
    all_finite = domain_failures == 0 and all(r["closure_domain_valid"] for r in diagnostic_rows)
    adapter_role = "MITIGATING" if all(r["machine_adapter_role"] == "MITIGATING" for r in diagnostic_rows) else "INDETERMINATE"
    diagnosis = {
        "task_id": TASK, "claim_ceiling": CLAIM, "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "closure_function_domain_role": "NOT_CAUSAL" if all_finite else "DEFECT_REPRODUCED",
        "frozen_root_failure_mechanism": "COUPLED_ENDPOINT_ENVELOPE_EXCEEDED" if all_finite else "FUNCTION_DOMAIN_FAILURE",
        "machine_adapter_role": adapter_role,
        "frozen_parameter_scale_role": "FEASIBILITY_ARTIFACT_SUPPORTED" if max_pc > pc and family_ok else "FEASIBILITY_ARTIFACT_NOT_SUPPORTED",
        "formal_identifiability_status": "SCI_MD_011_EXECUTION_BLOCKED_IDENTIFIABILITY_NOT_ADJUDICATED",
        "declared_family_root_representability": "REPRESENTABLE_WITHIN_EXISTING_BOUNDS" if family_ok else "NOT_REPRESENTABLE_WITHIN_EXISTING_BOUNDS",
        "source_parameterization_relation": "SOURCE_FIT_PARAMETERIZATION_DIFFERENCE_PRESENT",
        "broader_high_pressure_behavior": "STRUCTURALLY_CANNOT_PRODUCE_REQUIRED_TURNOVER",
        "decision_materiality": "ROOT_REPAIR_CANNOT_CHANGE_ADOPTION_DECISION",
        "next_action": "RETIRE_E2C_FROM_CURRENT_DEVELOPMENT_PRIORITY_NO_REPARAMETERIZATION_TEST",
        "targeted_measurement_authorized": False, "architecture": "NOT_ADJUDICATED", "m01": "NOT_ADJUDICATED",
        "stage_f_authorized": False, "stage_d_authorized": False, "physical_validation": "NOT_ESTABLISHED",
        "supporting_facts": {"held_out_rows": 6, "feasible_at_frozen_pair": sum(r["root_admissible"] for r in diagnostic_rows), "infeasible_at_frozen_pair": sum(not r["root_admissible"] for r in diagnostic_rows), "sci_md_011_domain_failure_count": int(e2c_row["domain_failure_count"]), "sci_md_012_domain_failure_count": domain_failures, "restoring_a_root_restores_required_high_pressure_behavior": False},
    }
    parameter = {
        "task_id": TASK, "frozen_parameters": {"Qc_g_s": qc, "Pc_bar": pc}, "bounds": core.BOUNDS,
        "endpoint_shape_fphi": endpoint_shape,
        "per_brew_thresholds": [{"brew_id": r["brew_id"], "Pc_required_bar": r["Pc_required_bar"], "Qc_required_g_s_at_frozen_Pc": r["Qc_required_g_s_at_frozen_Pc"]} for r in diagnostic_rows],
        "maximum_Pc_required_bar": max_pc, "Pc_delta_from_frozen_bar": max_pc-pc, "Pc_relative_delta_from_frozen": max_pc/pc-1,
        "maximum_Qc_required_g_s_at_frozen_Pc": max_qc, "Qc_delta_from_frozen_g_s": max_qc-qc, "Qc_relative_delta_from_frozen": max_qc/qc-1,
        "required_Pc_within_frozen_bounds": core.BOUNDS["Pc_bar"][0] <= max_pc <= core.BOUNDS["Pc_bar"][1],
        "completed_e2c_fold_Pc_range_bar": {"minimum": min(fold_pcs), "maximum": max(fold_pcs), "required_relation": "WITHIN" if min(fold_pcs) <= max_pc <= max(fold_pcs) else "OUTSIDE"},
        "existing_profile_points": profiles, "profile_information_source": "FROZEN_READ_ONLY_NO_NEW_OBJECTIVE_EVALUATION",
        "formal_identifiability_status": diagnosis["formal_identifiability_status"],
        "witness": {"Pc_bar": witness_pc, "Qc_g_s": witness_qc, "inside_existing_bounds": family_ok, "rows": witness, "witness_is_prediction": False, "witness_is_candidate_fit": False, "witness_is_scored": False},
        "thresholds_are_sensitivity_degeneracy_diagnostics_not_fits": True,
    }
    source_comparison = {
        "puckworks_authority": {"commit": PUCK_COMMIT, "tree": PUCK_TREE, "path": PUCK_PATH, "sha256": source_hash},
        "source_semantics": {"static_domain": "P <= Pc", "above_Pc_behavior": "CALLER_RESPONSIBILITY", "universal_curve_monotone_on_declared_domain": True, "can_produce_hinted_high_pressure_decrease": False, "fit_static_parameter_order": ["Pc", "Qc"], "fit_static_lower_bounds": ["maximum_fitted_basket_pressure", 0.01], "constants_transferable": False},
        "frozen_ewp_semantics": {"measured_line_pressure_coupled_through_machine_adapter": True, "effective_fitted_parameters": ["Qc", "Pc"], "Pc_bounds": core.BOUNDS["Pc_bar"], "condition_13_bar_excluded_from_loco_fit": True, "clamping_or_continuation_above_Pc_permitted": False},
        "classification": diagnosis["source_parameterization_relation"], "diagnostic_only_neither_implementation_declared_incorrect": True,
    }
    authority = {"task_id": TASK, "owner_authorization": OWNER, "governance_class": "G0", "claim_ceiling": CLAIM, "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE", "ewp_base": {"commit": BASE_COMMIT, "tree": BASE_TREE}, "sci_md_011": {"merge_commit": BASE_COMMIT, "reviewed_result_head": RESULT_HEAD}, "puckworks": {"commit": PUCK_COMMIT, "tree": PUCK_TREE}, "immutable_input_sha256": dict(sorted(hashes.items())), "data_availability_preflight": {"decision": "E2C_13_BAR_ROOT_BLOCKER_DIAGNOSIS", "existing_evidence_checked": ["SCI-MD-011 frozen results and profiles", "exact Puckworks source authority", "six exposed held-out observations"], "unavailable_observable": None, "external_corpus_needed": False, "measurement_needed": False, "status": "PASS_EXISTING_EVIDENCE_SUFFICIENT"}, "allowed_operations": ["bounded deterministic diagnosis", "documentation", "tests", "current-state normalization"], "prohibited_operations": ["refit", "altered bounds", "changed equation or closure", "clamping or extrapolation", "replacement prediction", "scoring or ranking", "bootstrap or confidence intervals", "protected-data rerun", "production solver change", "OpenFOAM", "laboratory work", "Puckworks mutation", "architecture adjudication", "automatic reparameterization authorization"]}
    structural = {"universal_curve_monotone_declared_domain": True, "finite_phi_curve_monotone_declared_domain": True, "Qc_Pc_only_family_negative_slope_or_turnover_capability": False, "frozen_observed_high_pressure_slope": p1pressure["observed_high_slope"], "frozen_P1_predicted_high_pressure_slope": p1pressure["predicted_high_slope"], "frozen_P1_high_pressure_gate": {"high_direction_ok": p1pressure["high_direction_ok"], "candidate_status": "WRONG_PRESSURE_RESPONSE"}, "frozen_E2C_structural_saturation_capability": e2cpressure["structural_saturation_capability"], "frozen_E2C_structural_turnover_capability": e2cpressure["structural_turnover_capability"], "restoring_a_root_is_not_restoring_required_high_pressure_behavior": True}

    out.mkdir(parents=True, exist_ok=True)
    write_json(out/"AUTHORITY_AND_SCOPE.json", authority); write_json(out/"PARAMETER_FEASIBILITY.json", parameter)
    write_json(out/"SOURCE_PARAMETERIZATION_COMPARISON.json", source_comparison); write_json(out/"DIAGNOSIS.json", {**diagnosis, "structural_high_pressure": structural})
    fields = list(diagnostic_rows[0])
    with (out/"ROOT_FEASIBILITY.csv").open("w", newline="") as f:
        w=csv.DictWriter(f, fields, lineterminator="\n"); w.writeheader(); w.writerows(diagnostic_rows)
    margins = ", ".join(f"{r['brew_id']}: {r['representability_margin_bar']:.15g}" for r in diagnostic_rows)
    result = f"""# SCI-MD-012 result\n\n## Question and authority\n\nThis G0, `NO_GOVERNING_PHYSICS_CHANGE` task answers only the authorized, retrospective target-exposed, non-scoring E2C 13-bar coupled-root questions under `{CLAIM}`. The exact SCI-MD-011 merge/result and Puckworks authorities are recorded in `AUTHORITY_AND_SCOPE.json`.\n\n## Exact diagnosis\n\nThe exact SCI-MD-011 fail-fast prediction reproduced `NO_ADMISSIBLE_ROOT` first at `{first_failure[0]}`. Independent evaluation retained all six brews: {sum(r['root_admissible'] for r in diagnostic_rows)} feasible and {sum(not r['root_admissible'] for r in diagnostic_rows)} infeasible at the frozen E2C pair. Their common coupled endpoint ceiling is approximately {diagnostic_rows[0]['coupled_line_pressure_ceiling_bar']:.12g} bar; margins (bar) are {margins}.\n\nEvery endpoint input was inside [0,1] and every finite-Phi evaluation was finite. Thus the closure-domain role is `{diagnosis['closure_function_domain_role']}` and the failure mechanism is `{diagnosis['frozen_root_failure_mechanism']}`, not a function-domain defect. The positive machine-drop contribution expands the line-pressure envelope, so its role is `{adapter_role}`; incorrectly treating line pressure as basket pressure would make the failure larger.\n\nAt frozen Qc, the maximum algebraic Pc threshold is {max_pc:.15g} bar, {max_pc-pc:.15g} bar ({(max_pc/pc-1)*100:.12g}%) above frozen Pc. At frozen Pc, the maximum algebraic endpoint Qc threshold is {max_qc:.15g} g/s. These are sensitivity/degeneracy diagnostics, not fits. Existing frozen profile points and threshold crossings are recorded without any new objective evaluation. Formal identifiability remains `{diagnosis['formal_identifiability_status']}`.\n\nThe algebraic witness Pc={witness_pc:.15g} bar, Qc={witness_qc:.15g} g/s lies inside the existing bounds and supplies an admissible endpoint margin for every row. Therefore whole-family root representability is `{diagnosis['declared_family_root_representability']}`. This witness is neither a prediction, candidate fit, nor score and does not establish predictive adequacy.\n\n## Structural consequence\n\nThe source universal curve and frozen finite-Phi curve are monotone on their declared domains. Qc/Pc scaling cannot introduce negative high-pressure slope or turnover. The frozen observed high-pressure slope is {p1pressure['observed_high_slope']:.15g}; P1 predicts {p1pressure['predicted_high_slope']:.15g} and remains `WRONG_PRESSURE_RESPONSE`; E2C has frozen saturation capability `{str(e2cpressure['structural_saturation_capability']).lower()}` and turnover capability `{str(e2cpressure['structural_turnover_capability']).lower()}`. Restoring a root is not restoring the required high-pressure behavior.\n\nDecision materiality is `{diagnosis['decision_materiality']}`. The next action is `{diagnosis['next_action']}`. No reparameterization test or measurement is authorized. Architecture and M01 remain `NOT_ADJUDICATED`; Stage F/D remain unauthorized; physical validation remains `NOT_ESTABLISHED`.\n"""
    (out/"RESULT.md").write_text(result)
    artifacts=[]
    for path in sorted(out.iterdir()):
        if path.name != "ARTIFACT_MANIFEST.json": artifacts.append({"path": path.name, "sha256": sha(path)})
    write_json(out/"ARTIFACT_MANIFEST.json", {"task_id": TASK, "artifacts": artifacts})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
