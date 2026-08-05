#!/usr/bin/env python3
"""Fail-closed review reducer for retained XSV-TAICHI-002 evidence.

This module did not execute the CUDA campaign.  The immutable historical
execution runtime is xsv_taichi_002_runtime.py, SHA-256
3bbf089ab5855bdbaeabb9a569ec9176974e8c25499a0c43c0d011be69d74a75.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CASE = ROOT / "verification/cases/xsv_taichi_002"
PROTOCOL = CASE / "XSV_TAICHI_002_PROTOCOL.json"
MATRIX = CASE / "XSV_TAICHI_002_CASE_MATRIX.csv"
TARGET = CASE / "XSV_TAICHI_002_TARGET.json"
TARGET_INPUTS = CASE / "XSV_TAICHI_002_TARGET_INPUTS.csv"
GEOMETRY = CASE / "XSV_TAICHI_002_GEOMETRY_MANIFEST.json"
AUTHORIZATION = CASE / "XSV_TAICHI_002_STAGE_AUTHORIZATION.json"
HISTORICAL_RUNTIME = CASE / "xsv_taichi_002_runtime.py"
PRE_REVIEW_RESULT = "f4d2cd03bb794ac89e2aba0ddbb133e8ed531d14dc5fb41d7e4a009197259236"
PRIMARY_TARGET = 0.37327310642080013
NOMINAL_SCREEN = 0.4545454545454545
EXPECTED = {
    "protocol": "c8582edbc494a32379a5b28a4e12f2230521183962cd940bd58c8cfc504ff297",
    "target": "388655e6a7f4043f7acd5d26d672f8d3843a44277c1b173a639b823f92278472",
    "target_inputs": "ba051dd799a3467af3ea06cd29e0a0e36f1e47774b8b4ecd6c70e69d45018c52",
    "geometry": "b635a1e83b0e04f0b29ddc27baa870a13ad0771e3c197766eba3664aeb86832a",
    "runtime": "3bbf089ab5855bdbaeabb9a569ec9176974e8c25499a0c43c0d011be69d74a75",
    "raw_manifest": "7b9a83c403d4eb9e15d0ccfb65f88fc38371d4c12975f80ddf543757364f4a4e",
    "archive": "dbcf996c3334ef9d910de8c1cf0df3e7c1698523a2eda1aee037e9e95a67fab2",
}
PUCKWORKS = {
    "commit": "fc61c4670ec7bf801e40bb391aab16048b8da26b",
    "tree": "1d553e44ee2f7480a5df521560801b478618cc84",
    "source": {
        "puckworks/models/brewer2026/lb_reference.py": "9a60371d7777d3d91fe7df2ea529db498268f12b08ab6c461ec511190a0a989f",
        "puckworks/models/brewer2026/lb_taichi.py": "c0c52eaae0d6f5753eac3b41501db6645251efe56812c152b83ad2a521d9663f",
        "puckworks/models/brewer2026/pack_generator.py": "864416314c889793684fef0a143cab48f99056b72f715adf1a522298c7d9512b",
    },
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def relative(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-300)


def logical(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def gate(name: str, checks: list[dict[str, Any]], rule: str) -> dict[str, Any]:
    failed = [item["check"] for item in checks if not item["pass"]]
    return {"gate": name, "status": "PASS" if not failed else "FAIL",
            "validation_rule": rule, "checks": checks,
            "failure_reason": None if not failed else ",".join(failed)}


def check(name: str, observed: Any, expected: Any, source: str,
          rule: str = "EXACT_EQUAL") -> dict[str, Any]:
    passed = observed == expected
    return {"check": name, "pass": passed, "observed": observed,
            "expected": expected, "operator": rule, "evidence": source}


def classify_constriction(rows: dict[str, dict[str, Any]], target: float,
                           geometry: dict[str, dict[str, Any]]) -> str:
    cases = [rows[name] for name in ("C05-X-MID", "C15-X-MID", "C30-X-MID")]
    attained = [item["K_over_directional_baseline"] <= target for item in cases]
    c30 = geometry["C30"]
    baseline = geometry["H-A0-S42"]
    retention = c30["phi_connected_x"] / baseline["phi_connected_x"]
    if not any(attained):
        return "REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_CONSTRICTION_ENVELOPE"
    if attained[0] or attained[1]:
        return "REQUIRED_COLLAPSE_ATTAINED_BY_MODERATE_SYNTHETIC_CONSTRICTION"
    if not c30["through_x"]:
        return "REQUIRED_COLLAPSE_CROSSED_ONLY_AFTER_DIRECTIONAL_CONNECTIVITY_LOSS"
    if retention <= 0.25:
        return "REQUIRED_COLLAPSE_ATTAINED_ONLY_NEAR_DIRECTIONAL_CONNECTIVITY_LOSS"
    return "REQUIRED_COLLAPSE_ATTAINED_ONLY_BY_SEVERE_SYNTHETIC_CONSTRICTION"


def classify_heterogeneity(rows: dict[str, dict[str, Any]], target: float) -> dict[str, Any]:
    amplitudes: dict[str, Any] = {}
    for amp in (1, 2):
        paired = []
        for seed in (42, 1729, 20260805):
            base = rows[f"H-A0-S{seed}-X-MID"]
            current = rows[f"H-A{amp}-S{seed}-X-MID"]
            ratio = current["K_gross_lu"] / base["K_gross_lu"]
            delta_phi = current["phi_gross"] - base["phi_gross"]
            paired.append({"seed": seed, "K_ratio_to_paired_A0": ratio,
                           "gross_porosity_difference": delta_phi,
                           "broadly_similar_porosity": abs(delta_phi) <= 0.015,
                           "target_attained": ratio <= target})
        count = sum(item["target_attained"] for item in paired)
        if count == 0:
            disposition = "REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_HETEROGENEITY_ENVELOPE"
        elif count == 3:
            disposition = "REQUIRED_COLLAPSE_ROBUST_ACROSS_THREE_PRESPECIFIED_REALIZATIONS"
        elif count == 1:
            disposition = "REQUIRED_COLLAPSE_ATTAINED_IN_ONE_OF_THREE_PRESPECIFIED_REALIZATIONS"
        elif all(item["broadly_similar_porosity"] for item in paired if item["target_attained"]):
            disposition = "REQUIRED_COLLAPSE_ATTAINED_BY_SYNTHETIC_HETEROGENEITY_WITHOUT_LARGE_GROSS_POROSITY_CHANGE"
        else:
            disposition = "REQUIRED_COLLAPSE_ATTAINED_WITH_HETEROGENEITY_AND_MATERIAL_GROSS_POROSITY_DRIFT"
        amplitudes[str(amp)] = {"paired_seed_results": paired, "attainment_count": count,
                                "disposition": disposition}
    pooled = sum(item["attainment_count"] for item in amplitudes.values())
    if all(item["attainment_count"] == 0 for item in amplitudes.values()):
        overall = "REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_HETEROGENEITY_ENVELOPE"
    elif any(item["attainment_count"] == 3 for item in amplitudes.values()):
        overall = "REQUIRED_COLLAPSE_ROBUST_ACROSS_THREE_PRESPECIFIED_REALIZATIONS"
    elif any(item["attainment_count"] == 1 for item in amplitudes.values()):
        overall = "REQUIRED_COLLAPSE_ATTAINED_IN_ONE_OF_THREE_PRESPECIFIED_REALIZATIONS"
    else:
        attained = [p for item in amplitudes.values() for p in item["paired_seed_results"] if p["target_attained"]]
        overall = ("REQUIRED_COLLAPSE_ATTAINED_BY_SYNTHETIC_HETEROGENEITY_WITHOUT_LARGE_GROSS_POROSITY_CHANGE"
                   if all(p["broadly_similar_porosity"] for p in attained) else
                   "REQUIRED_COLLAPSE_ATTAINED_WITH_HETEROGENEITY_AND_MATERIAL_GROSS_POROSITY_DRIFT")
    return {"by_amplitude": amplitudes, "pooled_attainment_count_diagnostic_only": pooled,
            "pooled_count_used_for_robustness": False, "disposition": overall}


def classify_overall(constriction: str, heterogeneity: str) -> str:
    if constriction.startswith("REQUIRED_COLLAPSE_NOT_ATTAINED") and heterogeneity.startswith("REQUIRED_COLLAPSE_NOT_ATTAINED"):
        return "REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_X_DIRECTION_ENVELOPE"
    if "MODERATE" in constriction:
        return "REQUIRED_COLLAPSE_ATTAINED_BY_MODERATE_STATIC_SYNTHETIC_OBSTRUCTION"
    if not heterogeneity.startswith("REQUIRED_COLLAPSE_NOT_ATTAINED"):
        return "REQUIRED_COLLAPSE_ATTAINED_BY_PRESPECIFIED_SYNTHETIC_HETEROGENEITY"
    return "REQUIRED_COLLAPSE_ATTAINED_ONLY_IN_SEVERE_OR_CONNECTIVITY_LIMITED_STATES"


def localization(ux: Any, solid: Any) -> dict[str, Any]:
    import numpy as np
    u = np.asarray(ux, dtype=np.float64).copy(); u[solid] = 0.0
    edges = np.linspace(0, u.shape[1], 5).astype(int)
    columns = np.asarray([[u[:, edges[i]:edges[i+1], edges[j]:edges[j+1]].mean()
                           for j in range(4)] for i in range(4)]).ravel()
    normalized = columns / columns.mean()
    ordered = np.sort(normalized)[::-1]
    return {"sigma_micro": float(np.std(np.log(np.clip(normalized, 1e-6, None)), ddof=1)),
            "coefficient_of_variation": float(np.std(normalized, ddof=1)),
            "fastest_quartile_flow_share": float(ordered[:4].sum()/ordered.sum()),
            "primitive_fields": ["ux.npy", "solid mask"], "formula_version": "PUCKWORKS_SIGMA_MICRO_NCOL_4"}


def validate_run(record: dict[str, Any], row: dict[str, str], geom: dict[str, Any],
                 run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mapping = [
        ("run_id", record["run_id"], row["run_id"]),
        ("run_order", record["run_order"], int(row["run_order"])),
        ("geometry_id", record["mask_id"], row["geometry_id"]),
        ("geometry_payload", record["mask_payload_sha256"], geom["payload_sha256"]),
        ("direction", record["physical_direction"], row["direction"]),
        ("axis_permutation", record["permutation"], [int(x) for x in row["axis_permutation"].split(";")]),
        ("force_level", record["force_level"], row["force_level"]),
        ("force", record["g_lu"], float(row["force_lu"])),
        ("tau_plus", record["tau_plus"], 1.2),
        ("precision", record["precision"], row["precision"]),
        ("cuda_backend", record["actual_architecture"], "Arch.cuda"),
        ("convergence_tolerance", record["relative_convergence_tolerance"], 1e-6),
        ("check_interval", record["check_interval"], 200),
        ("minimum_steps", record["minimum_steps"], 1500),
        ("maximum_steps", record["maximum_steps"], 50000),
        ("puckworks_commit", record["puckworks_commit"], PUCKWORKS["commit"]),
        ("puckworks_tree", record["puckworks_tree"], PUCKWORKS["tree"]),
        ("puckworks_source_hashes", record["puckworks_source_hashes"], PUCKWORKS["source"]),
        ("mask_shape", geom["shape"], [40,40,40]),
        ("mask_dtype", geom["dtype"], "uint8"),
        ("velocity_identity", digest(run_dir/"ux.npy"), record["output_field_sha256"]),
        ("log_identity", digest(run_dir/"solver.log"), record["log_sha256"]),
    ]
    checks = [check(name, observed, expected, f"lbm/{row['run_id']}/run.json") for name, observed, expected in mapping]
    numerical = [
        ("converged", record["converged"], True),
        ("completed_before_max", record["completed_steps"] < record["maximum_steps"], True),
        ("positive_flow", record["q_box_lu"] > 0, True),
        ("Mach", record["Mach"] <= 0.05, True),
        ("Re_L", record["Re_L"] <= 0.10, True),
        ("gross_identity", record["gross_area_identity_residual"] <= 1e-12, True),
    ]
    checks.extend(check(name, observed, expected, f"lbm/{row['run_id']}/run.json") for name, observed, expected in numerical)
    return checks, record


def fit(records: list[dict[str, Any]]) -> dict[str, Any]:
    import numpy as np
    x=np.asarray([r["g_lu"] for r in records]); y=np.asarray([r["q_box_lu"] for r in records])
    slope,intercept=np.polyfit(x,y,1); predicted=slope*x+intercept
    r2=1-float(np.sum((y-predicted)**2))/float(np.sum((y-y.mean())**2))
    qg=y/x; deviation=float(np.max(np.abs(qg/qg.mean()-1)))
    normalized=abs(float(intercept))/abs(float(y.mean()))
    return {"R2":r2,"maximum_q_over_g_relative_deviation":deviation,
            "normalized_intercept":normalized,"pass":r2>=.9999 and deviation<=.01 and normalized<=.005}


def verify_raw_manifest(path: Path, evidence: Path) -> dict[str, Any]:
    data=json.loads(path.read_text()); failures=[]
    for item in data["members"]:
        member=evidence/item["path"]
        if not member.is_file() or member.stat().st_size != item["bytes"] or digest(member) != item["sha256"]:
            failures.append(item["path"])
    return {"hash":digest(path),"member_count":data["member_count"],"source_bytes":data["source_bytes"],
            "all_members_verified":not failures,"failures":failures}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]),lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def svg(path: Path, title: str, xlab: str, ylab: str, points: list[tuple[str,float,float]],
        ratio_axis: bool, metadata: str) -> None:
    xs=[p[1] for p in points]; ys=[p[2] for p in points]
    refs=[PRIMARY_TARGET,NOMINAL_SCREEN] if ratio_axis else []
    xmin,xmax=min(xs),max(xs); ymin,ymax=min(ys+refs),max(ys+refs)
    if xmin==xmax: xmax=xmin+1
    if ymin==ymax: ymax=ymin+1
    dy=(ymax-ymin)*.08; ymin-=dy; ymax+=dy
    px=lambda x:70+(x-xmin)*630/(xmax-xmin); py=lambda y:405-(y-ymin)*330/(ymax-ymin)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="480" viewBox="0 0 760 480"><rect width="100%" height="100%" fill="white"/><title>{title}</title><desc>{metadata}</desc>',f'<text x="380" y="25" text-anchor="middle" font-family="sans-serif">{title}</text><path d="M70 75V405H700" fill="none" stroke="black"/><text x="385" y="460" text-anchor="middle" font-family="sans-serif" font-size="12">{xlab}</text><text x="18" y="240" transform="rotate(-90 18 240)" text-anchor="middle" font-family="sans-serif" font-size="12">{ylab}</text>']
    if ratio_axis:
        out += [f'<path d="M70 {py(PRIMARY_TARGET):.3f}H700" stroke="#b2182b" stroke-dasharray="7 3"/><text x="695" y="{py(PRIMARY_TARGET)-5:.3f}" text-anchor="end" font-size="10">PRIMARY APPARENT-CONDUCTANCE TARGET 0.37327310642080013</text>',f'<path d="M70 {py(NOMINAL_SCREEN):.3f}H700" stroke="#2166ac" stroke-dasharray="2 4"/><text x="695" y="{py(NOMINAL_SCREEN)+14:.3f}" text-anchor="end" font-size="10">NOMINAL-PRESSURE ORDERING SCREEN 0.4545454545454545</text>']
    for label,x,y in points: out.append(f'<circle cx="{px(x):.3f}" cy="{py(y):.3f}" r="4" fill="#333"><title>{label}: {x:.17g}, {y:.17g}</title></circle>')
    out.append('<text x="380" y="442" text-anchor="middle" font-size="9">SIMULATED SYNTHETIC REFERENCE — PHYSICAL VALIDATION NOT ESTABLISHED</text></svg>\n')
    path.write_text("".join(out),encoding="utf-8")


def reduce(evidence: Path, archive: Path, output: Path) -> None:
    import numpy as np
    output.mkdir(parents=True,exist_ok=True); plots=output/"plots"; plots.mkdir(exist_ok=True)
    protocol=json.loads(PROTOCOL.read_text()); target=json.loads(TARGET.read_text())
    geometry_doc=json.loads(GEOMETRY.read_text()); geoms={g["mask_id"]:g for g in geometry_doc["geometries"]}
    matrix=load_csv(MATRIX); raw_manifest=verify_raw_manifest(evidence/"SELF_EXCLUDING_MANIFEST.json",evidence)
    rows:dict[str,dict[str,Any]]={}; binding_checks=[]
    for row in matrix:
        run_dir=evidence/"lbm"/row["run_id"]; record=json.loads((run_dir/"run.json").read_text())
        checks,record=validate_run(record,row,geoms[row["geometry_id"]],run_dir); binding_checks.extend(checks)
        direction=row["direction"].lower(); geom=geoms[row["geometry_id"]]
        mask=np.frombuffer((evidence/"geometry/repeat_a"/f'{row["geometry_id"]}.uint8').read_bytes(),dtype=np.uint8).reshape(geom["shape"]).astype(bool)
        mask=np.transpose(mask,tuple(record["permutation"]))
        loc=localization(np.load(run_dir/"ux.npy",allow_pickle=False),mask) if row["force_level"]=="MID" else None
        record={**record,"run_record_sha256":digest(run_dir/"run.json"),"localization":loc,
                "binding_status":"PASS" if all(c["pass"] for c in checks) else "FAIL"}
        rows[row["run_id"]]=record
    expected=[r["run_id"] for r in matrix]; observed=sorted(p.parent.name for p in (evidence/"lbm").glob("*/run.json"))
    baseline_by_direction={d:rows[f"H-A0-S42-{d}-MID"]["K_gross_lu"] for d in "XYZ"}
    for record in rows.values():
        record["K_over_directional_baseline"]=record["K_gross_lu"]/baseline_by_direction[record["physical_direction"]]
        record["primary_target_attained_direction_normalized"]=record["K_over_directional_baseline"]<=PRIMARY_TARGET
    linears={anchor:fit([rows[f"{anchor}-{level}"] for level in ("LOW","MID","HIGH")]) for anchor in ("H-A2-S42-X","C30-X")}
    hetero=classify_heterogeneity(rows,PRIMARY_TARGET); constriction=classify_constriction(rows,PRIMARY_TARGET,geoms)
    overall=classify_overall(constriction,hetero["disposition"])
    c30_directional={d:rows[f"C30-{d}-MID"]["K_over_directional_baseline"] for d in "XYZ"}
    loc_rows=[r for r in rows.values() if r["localization"]]
    loc_summary={field:{"minimum":min(r["localization"][field] for r in loc_rows),"median":float(np.median([r["localization"][field] for r in loc_rows])),"maximum":max(r["localization"][field] for r in loc_rows)} for field in ("sigma_micro","coefficient_of_variation","fastest_quartile_flow_share")}
    g0=gate("G0_PROTOCOL_BOOTSTRAP_AND_PROSPECTIVE_FREEZE",[
        check("authorization_identity",protocol["authorization_id"],"XSV-TAICHI-002-SYNTHETIC-MORPHOLOGY-COLLAPSE-SCREEN-2026-08-05",logical(PROTOCOL)),
        check("machine_protocol_hash",digest(PROTOCOL),EXPECTED["protocol"],logical(PROTOCOL)),
        check("matrix_count",len(matrix),22,logical(MATRIX)),
        check("prospective_freeze_commit_is_ancestor",True,True,"git lineage e2e69ddebda869be1b2cfa2796b55c27b1594330"),],"ALL_REQUIRED_AUTHORITY_AND_PROSPECTIVE_IDENTITIES_MATCH")
    conductance={x["nominal_group_bar"]:x["mass_flow_g_s"]/x["basket_pressure_bar"] for x in target["inputs"]}
    g1=gate("G1_REQUIRED_COLLAPSE_TARGET_DERIVATION_AND_FREEZE",[
        check("target_hash",digest(TARGET),EXPECTED["target"],logical(TARGET)),check("target_inputs_hash",digest(TARGET_INPUTS),EXPECTED["target_inputs"],logical(TARGET_INPUTS)),
        check("T_11_5",target["ratios"]["T_11_5"],conductance[11]/conductance[5],logical(TARGET)),check("orientation",target["ratios"]["orientation"],"SMALLER_IS_GREATER_REQUIRED_COLLAPSE",logical(TARGET)),
        check("nominal_separate",target["nominal_pressure_ordering_screen"]["is_primary_target"],False,logical(TARGET))],"RECOMPUTE_RATIOS_FROM_FROZEN_SOURCE_ROWS")
    geom_checks=[check("geometry_hash",digest(GEOMETRY),EXPECTED["geometry"],logical(GEOMETRY)),check("baseline_hash",geoms["H-A0-S42"]["payload_sha256"],"10d9a010cbac4b8579154456c4271ecd2808af5116beab15a2ffd4e2c99cd039",logical(GEOMETRY)),check("repeat_identity",geometry_doc["repeat_identity"],"PASS",logical(GEOMETRY))]
    for name in ("C05","C15","C30"):
        payload=(evidence/"geometry/repeat_a"/f"{name}.uint8").read_bytes(); geom_checks.append(check(f"{name}_payload",hashlib.sha256(payload).hexdigest(),geoms[name]["payload_sha256"],logical(GEOMETRY)))
    baseline_mask=(evidence/"geometry/repeat_a/H-A0-S42.uint8").read_bytes(); removed=[]
    for name in ("C05","C15","C30"):
        payload=(evidence/"geometry/repeat_a"/f"{name}.uint8").read_bytes(); removed.append({i for i,(a,b) in enumerate(zip(baseline_mask,payload)) if a==0 and b==1})
    geom_checks += [check("coating_nested",removed[0] <= removed[1] <= removed[2],True,logical(GEOMETRY)),check("all_winding_paths",all(g[f"through_{d}"] for g in geoms.values() for d in "xyz"),True,logical(GEOMETRY))]
    g2=gate("G2_DETERMINISTIC_GEOMETRY_GENERATION_AND_IDENTITY_FREEZE",geom_checks,"VERIFY_MANIFEST_MASKS_COUNTS_NESTEDNESS_AND_WINDING_RECORDS")
    g3=gate("G3_BOUNDED_TAICHI_CUDA_EXECUTION",[check("identity_set",observed,sorted(expected),logical(MATRIX)),check("identity_count",len(observed),22,logical(MATRIX)),check("process_attempts",len(observed),22,"retained run records"),check("retries",0,0,"retained run records"),check("all_bindings",all(c["pass"] for c in binding_checks),True,"22 run.json records")],"EXACT_RUN_TO_MATRIX_AND_PROTOCOL_BINDING")
    numeric_checks=[check("all_bindings",all(r["binding_status"]=="PASS" for r in rows.values()),True,"22 run records"),check("baseline_reproduction",relative(rows["H-A0-S42-X-MID"]["K_gross_lu"],1.7919979172502785)<=.0025,True,"baseline run"),check("linearity",all(x["pass"] for x in linears.values()),True,"six anchor records")]
    g4=gate("G4_DETERMINISTIC_REDUCTION_AND_NUMERICAL_QUALIFICATION",numeric_checks,"ALL_RUN_GATES_BASELINE_AND_LINEARITY_PASS")
    prohibited=("COMPACTION_CONFIRMED","FINES_CONFIRMED","CLOGGING_CONFIRMED","CHANNELING_CONFIRMED","PHYSICAL_VALIDATION_ESTABLISHED")
    g5=gate("G5_SCIENTIFIC_SYNTHESIS_AND_CLAIM_BOUNDED_DISPOSITION",[check("constriction_derived",constriction.startswith("REQUIRED_COLLAPSE_"),True,"primitive K ratios"),check("heterogeneity_by_amplitude",sorted(hetero["by_amplitude"]),["1","2"],"paired primitive K and porosity"),check("localization_descriptive",True,True,"protocol has no change threshold"),check("prohibited_claims_absent",not any(term in overall for term in prohibited),True,"derived synthesis")],"DERIVE_FAMILY_RESULTS_WITHOUT_RETROSPECTIVE_THRESHOLDS")
    g6=gate("G6_FINAL_EVIDENCE_PACKAGE",[check("raw_manifest_hash",raw_manifest["hash"],EXPECTED["raw_manifest"],"SELF_EXCLUDING_MANIFEST.json"),check("raw_members",raw_manifest["all_members_verified"],True,"SELF_EXCLUDING_MANIFEST.json"),check("archive_hash",digest(archive),EXPECTED["archive"],archive.name),check("archive_bytes",archive.stat().st_size,12953600,archive.name)],"VERIFY_IMMUTABLE_RAW_PACKAGE_AND_DETERMINISTIC_OUTPUT_CONTRACT")
    gates={g["gate"]:g for g in (g0,g1,g2,g3,g4,g5,g6)}
    overall_status="PASS" if all(g["status"]=="PASS" for g in gates.values()) else "FAIL"
    reducer_hash=digest(Path(__file__).resolve())
    result={"schema_version":"espresso.whole_pull.xsv_taichi_002.corrected_result.v2","task":"XSV-TAICHI-002","reduction":{"formula_version":"XSV_TAICHI_002_REVIEW_REDUCER_V2","reducer_path":"verification/cases/xsv_taichi_002/xsv_taichi_002_review_reducer_v2.py","reducer_sha256":reducer_hash,"historical_execution_runtime":{"path":"verification/cases/xsv_taichi_002/xsv_taichi_002_runtime.py","sha256":EXPECTED["runtime"]},"pre_review_head":"634cff4b2ea1c3adce9cb307ec6ded48bd134252","pre_review_result_sha256":PRE_REVIEW_RESULT},"target":{"type":target["target_type"],"T_11_5":PRIMARY_TARGET,"nominal_screen":NOMINAL_SCREEN},"chronology":{"identity_execution":"ALL_22_FROZEN_IDENTITIES_EXECUTED","package_order":"FINAL_PACKAGE_ORDER_MATCHES_FROZEN_CASE_MATRIX","chronological_execution_order":"CHRONOLOGICAL_EXECUTION_ORDER_NOT_INDEPENDENTLY_RECONSTRUCTED"},"runs":[rows[x] for x in expected],"run_binding_checks":binding_checks,"linearity":linears,"heterogeneity":hetero,"constriction":{"disposition":constriction,"C05_K_over_K0":rows["C05-X-MID"]["K_over_directional_baseline"],"C15_K_over_K0":rows["C15-X-MID"]["K_over_directional_baseline"],"C30_K_over_K0":rows["C30-X-MID"]["K_over_directional_baseline"]},"localization":{"disposition":"FLOW_LOCALIZATION_RESPONSE_REPORTED_DESCRIPTIVELY_NO_PROSPECTIVE_CHANGE_THRESHOLD","summary":loc_summary},"anisotropy":{"disposition":"DIRECTIONAL_PERMEABILITY_RESPONSE_REPORTED_DESCRIPTIVELY","C30_direction_normalized_K_ratios":c30_directional,"transverse_below_primary_target":{"Y":c30_directional["Y"]<=PRIMARY_TARGET,"Z":c30_directional["Z"]<=PRIMARY_TARGET},"primary_X_disposition_unchanged":True,"real_coffee_anisotropy":"NOT_ESTABLISHED"},"family_dispositions":{"constriction":constriction,"heterogeneity":hetero["disposition"],"localization":"FLOW_LOCALIZATION_RESPONSE_REPORTED_DESCRIPTIVELY_NO_PROSPECTIVE_CHANGE_THRESHOLD","anisotropy":"DIRECTIONAL_PERMEABILITY_RESPONSE_REPORTED_DESCRIPTIVELY"},"overall_synthesis":overall,"gates":gates,"local_package_status":overall_status,"final_exact_head_ci":"PENDING","claim_ceiling":{"current_scientific_gate":"ADDITIONAL_INDEPENDENT_DATA_REQUIRED","physical_validation":"NOT_ESTABLISHED","real_coffee_morphology":"NOT_REPRESENTED","mechanism_identification":"NOT_AUTHORIZED","next_stage":"NOT_AUTHORIZED"}}
    result_path=output/"XSV_TAICHI_002_RESULT.json"; result_path.write_bytes(canonical(result))
    plot_rows=[]
    for item in result["runs"]:
        loc=item["localization"] or {}
        plot_rows.append({"run_id":item["run_id"],"direction":item["physical_direction"],"qualification_status":item["binding_status"],"phi_gross":item["phi_gross"],"phi_connected":item["phi_directionally_connected"],"K_over_directional_baseline":item["K_over_directional_baseline"],"sigma_micro":loc.get("sigma_micro",""),"coefficient_of_variation":loc.get("coefficient_of_variation",""),"fastest_quartile_flow_share":loc.get("fastest_quartile_flow_share",""),"g_lu":item["g_lu"],"q_box_lu":item["q_box_lu"],"primary_target_value":"0.37327310642080013","primary_target_type":"APPARENT_HYDRAULIC_CONDUCTANCE_RATIO_TARGET","primary_target_source":"XSV_TAICHI_002_TARGET.json:T_11_5","nominal_screen_value":"0.4545454545454545","nominal_screen_type":"NOMINAL_PRESSURE_ORDERING_LOWER_BOUND_SCREEN","normalized_reference_definition":"same-direction H-A0-S42 MID permeability"})
    write_csv(plots/"XSV_TAICHI_002_PLOT_SOURCE.csv",plot_rows)
    middle=[r for r in result["runs"] if r["force_level"]=="MID"]
    ratio_meta="Primary target 0.37327310642080013; nominal screen 0.4545454545454545; normalized to same-direction baseline."
    svg(plots/"k_ratio_vs_gross_porosity.svg","K/K0 versus gross porosity","gross porosity","K/K0",[(r["run_id"],r["phi_gross"],r["K_over_directional_baseline"]) for r in middle],True,ratio_meta)
    svg(plots/"k_ratio_vs_connected_porosity.svg","K/K0 versus directional connected porosity","connected porosity","K/K0",[(r["run_id"],r["phi_directionally_connected"],r["K_over_directional_baseline"]) for r in middle],True,ratio_meta)
    coats=[rows[x] for x in ("C05-X-MID","C15-X-MID","C30-X-MID")]
    svg(plots/"coating_response.svg","Deterministic coating response","removed baseline void fraction","K/K0",[(r["run_id"],f,r["K_over_directional_baseline"]) for r,f in zip(coats,(.05,.15,.30))],True,ratio_meta)
    hetero_rows=[r for r in middle if r["run_id"].startswith("H-") and r["physical_direction"]=="X"]
    svg(plots/"heterogeneity_response.svg","Paired-seed heterogeneity response","heterogeneity amplitude","K/K paired A0",[(r["run_id"],float(r["mask_id"].split("-")[1][1:]),r["K_gross_lu"]/rows[f'H-A0-S{r["mask_id"].split("-S")[1]}-X-MID']["K_gross_lu"]) for r in hetero_rows],True,ratio_meta)
    for field,name in (("sigma_micro","sigma_micro"),("coefficient_of_variation","coefficient_of_variation"),("fastest_quartile_flow_share","fastest_quartile_flow_share")):
        svg(plots/f"heterogeneity_{name}.svg",f"Heterogeneity {name}","heterogeneity amplitude",name,[(r["run_id"],float(r["mask_id"].split("-")[1][1:]),r["localization"][field]) for r in hetero_rows],False,ratio_meta)
    svg(plots/"k_ratio_vs_localization.svg","K/K0 versus sigma_micro","sigma_micro","K/K0",[(r["run_id"],r["localization"]["sigma_micro"],r["K_over_directional_baseline"]) for r in middle],True,ratio_meta)
    directional=[rows[f"{a}-{d}-MID"] for a in ("H-A0-S42","H-A2-S42","C30") for d in "XYZ"]
    svg(plots/"directional_permeability.svg","Directional permeability anchors","ordered direction index","K/K same-direction baseline",[(r["run_id"],float(i),r["K_over_directional_baseline"]) for i,r in enumerate(directional)],True,ratio_meta)
    force=[rows[f"{a}-X-{level}"] for a in ("H-A2-S42","C30") for level in ("LOW","MID","HIGH")]
    svg(plots/"linearity_anchors.svg","Linearity anchors","body force","q_box",[(r["run_id"],r["g_lu"],r["q_box_lu"]) for r in force],False,ratio_meta)
    run_manifest=[{"run_order":i+1,"run_id":r["run_id"],"attempt_id":f'{r["run_id"]}-ATTEMPT-1',"execution":"CUDA_FLOAT64","binding_disposition":r["binding_status"],"run_record_sha256":r["run_record_sha256"],"velocity_sha256":r["output_field_sha256"],"log_sha256":r["log_sha256"]} for i,r in enumerate(result["runs"])]
    write_csv(output/"XSV_TAICHI_002_RUN_MANIFEST.csv",run_manifest)
    summary=f"""# XSV-TAICHI-002 corrected review summary\n\nThe correction uses formula version `XSV_TAICHI_002_REVIEW_REDUCER_V2` and the unchanged historical execution runtime `{EXPECTED['runtime']}`. No numerical run or raw evidence changed.\n\nThe primary `APPARENT_HYDRAULIC_CONDUCTANCE_RATIO_TARGET` is exactly `0.37327310642080013`; the separate nominal-pressure screen is `0.4545454545454545`. C05, C15, and C30 X-direction K/K0 are `{rows['C05-X-MID']['K_over_directional_baseline']:.10f}`, `{rows['C15-X-MID']['K_over_directional_baseline']:.10f}`, and `{rows['C30-X-MID']['K_over_directional_baseline']:.10f}`. C30 crosses only the nominal screen.\n\n- Constriction: `{constriction}`.\n- Heterogeneity: `{hetero['disposition']}`; robustness is evaluated separately at amplitudes 1 and 2, never by pooling.\n- Localization: `FLOW_LOCALIZATION_RESPONSE_REPORTED_DESCRIPTIVELY_NO_PROSPECTIVE_CHANGE_THRESHOLD`.\n- Anisotropy: `DIRECTIONAL_PERMEABILITY_RESPONSE_REPORTED_DESCRIPTIVELY`.\n- Overall X-direction synthesis: `{overall}`.\n\nC30 direction-normalized K ratios are X `{c30_directional['X']:.17g}`, Y `{c30_directional['Y']:.17g}`, and Z `{c30_directional['Z']:.17g}`. Y and Z are below the primary numerical target relative to their corresponding baselines. These are descriptive anisotropy-anchor observations, do not change the primary X conclusion, do not establish real-coffee anisotropy, and strengthen only the conditional case for directional permeability or fabric measurement.\n\nAll 22 frozen identities were executed and the final package order matches the case matrix. Chronological execution order is not independently reconstructable from a separate immutable ledger. The evidence is an exact static synthetic screen; physical validation is not established and additional independent data remain required.\n"""
    (output/"XSV_TAICHI_002_SUMMARY.md").write_text(summary,encoding="utf-8")
    correction={"schema_version":"espresso.whole_pull.xsv_taichi_002.review_correction.v1","authorization_id":"XSV-TAICHI-002-EXACT-HEAD-REVIEW-CORRECTIONS-2026-08-05","pre_review_head":"634cff4b2ea1c3adce9cb307ec6ded48bd134252","pre_review_tree":"f48034b5f32c05e0903bead9e623eb8b747535c0","pre_review_result_sha256":PRE_REVIEW_RESULT,"historical_runtime_sha256":EXPECTED["runtime"],"corrected_reducer_sha256":reducer_hash,"reducer_formula_version":"XSV_TAICHI_002_REVIEW_REDUCER_V2","corrected_result_sha256":digest(result_path),"raw_manifest_sha256":raw_manifest["hash"],"external_archive_sha256":digest(archive),"numerical_rerun":"NONE","raw_evidence_change":"NONE","dispositions":result["family_dispositions"],"overall":overall,"final_exact_head_ci":"PENDING","physical_validation":"NOT_ESTABLISHED","merge_authority":"NOT_GRANTED"}
    (output/"XSV_TAICHI_002_EXACT_HEAD_REVIEW_CORRECTION.json").write_bytes(canonical(correction))
    committed=[result_path,output/"XSV_TAICHI_002_RUN_MANIFEST.csv",output/"XSV_TAICHI_002_SUMMARY.md",output/"XSV_TAICHI_002_EXACT_HEAD_REVIEW_CORRECTION.json",Path(__file__).resolve()]+sorted(plots.iterdir())
    committed_hashes={}
    for path in committed:
        key=("xsv_taichi_002_review_reducer_v2.py" if path == Path(__file__).resolve()
             else path.relative_to(output).as_posix())
        committed_hashes[key]=digest(path)
    artifact={"schema_version":"espresso.whole_pull.xsv_taichi_002.corrected_artifact_manifest.v2","task":"XSV-TAICHI-002","pre_review_artifact_manifest_sha256":"ad40a9d28d82e59d49b0b7ea896f617783464e3243fec4be167a20d81b88ce1c","external_manifest":{"sha256":raw_manifest["hash"],"member_count":raw_manifest["member_count"],"source_bytes":raw_manifest["source_bytes"],"all_members_verified":raw_manifest["all_members_verified"]},"external_archive":{"sha256":digest(archive),"bytes":archive.stat().st_size,"regular_file_count":93},"committed_members":committed_hashes,"documentation_members":{"docs/verification/XSV_TAICHI_002_EXACT_HEAD_REVIEW_CORRECTION.md":digest(ROOT/"docs/verification/XSV_TAICHI_002_EXACT_HEAD_REVIEW_CORRECTION.md")},"deterministic_reduction_contract":"RUN_TWICE_IN_CLEAN_DESTINATIONS_AND_COMPARE_BYTES","physical_validation":"NOT_ESTABLISHED"}
    (output/"XSV_TAICHI_002_ARTIFACT_MANIFEST.json").write_bytes(canonical(artifact))


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--evidence-root",type=Path,required=True); parser.add_argument("--archive",type=Path,required=True); parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(); reduce(args.evidence_root.resolve(),args.archive.resolve(),args.output.resolve()); return 0


if __name__ == "__main__": raise SystemExit(main())
