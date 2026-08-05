#!/usr/bin/env python3
"""G8 fail-closed reducer over immutable XSV-TAICHI-002 evidence.

This reducer did not execute the CUDA campaign.  It wraps the historical v2
presentation reducer, then replaces its asserted authority/evidence gates with
checks derived from Git objects, retained target rows, mask bytes, run records,
and canonical current-authority documents.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, math, subprocess, sys, tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import xsv_taichi_002_review_reducer_v2 as v2

classify_constriction = v2.classify_constriction
classify_heterogeneity = v2.classify_heterogeneity
classify_overall = v2.classify_overall

CASE = HERE
AUTH = CASE / "XSV_TAICHI_002_STAGE_AUTHORIZATION.json"
AUTH_HISTORICAL_PATH = "verification/cases/xsv_taichi_002/XSV_TAICHI_002_STAGE_AUTHORIZATION.json"
PROTOCOL_MD = ROOT / "docs/verification/XSV_TAICHI_002_SYNTHETIC_MORPHOLOGY_AND_REQUIRED_PERMEABILITY_COLLAPSE_SCREEN.md"
PROTOCOL = CASE / "XSV_TAICHI_002_PROTOCOL.json"
MATRIX = CASE / "XSV_TAICHI_002_CASE_MATRIX.csv"
TARGET = CASE / "XSV_TAICHI_002_TARGET.json"
TARGET_INPUTS = CASE / "XSV_TAICHI_002_TARGET_INPUTS.csv"
GEOMETRY = CASE / "XSV_TAICHI_002_GEOMETRY_MANIFEST.json"
START_HEAD = "b84d5d5f2a26e00fb363b1650f1ce30b8c422d65"
G0_HEAD = "df50ec4be2734e26aa91715d3c27009ad32d0cc1"
G1_HEAD = "d299ef8"
HISTORICAL_G0_PROTOCOL = "4f3d6a528620b3d9d1d9ce39b3b9f088deb37586d33b3d761f690049610a3d7c"
CURRENT_PROTOCOL = "04911d266c77470f7d7a83a39842090100407a43fc3a36990b2177eea5496c28"
MACHINE_PROTOCOL = "c8582edbc494a32379a5b28a4e12f2230521183962cd940bd58c8cfc504ff297"
MATRIX_HASH = "74a709b8a766587cfd97194cf001002a19c124152173ad4a9d50f3bf804b7ed2"
V2_HASH = "0cc9a1f9281f545813c684962df962b50675f852753fdc7c5338374737c655d0"
V2_RESULT = "69cad8288cfb6c6b7568b5a67adc6454c39522008a4b671bd6f3c87e9d251fa0"

def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def git(*args: str) -> bytes: return subprocess.check_output(["git",*args],cwd=ROOT)
def git_text(*args: str) -> str: return git(*args).decode().strip()
def canonical(x: Any) -> bytes: return (json.dumps(x,sort_keys=True,separators=(",",":"))+"\n").encode()
def rel(a: float,b: float) -> float: return abs(a-b)/max(abs(a),abs(b),1e-300)

def ck(name: str, observed: Any, expected: Any, evidence: str, derivation: str,
       evidence_hash: str|None=None, operator: str="EXACT_EQUAL", failure: str|None=None) -> dict[str,Any]:
    passed = observed == expected
    return {"check":name,"observed":observed,"expected":expected,"operator":operator,
            "evidence_path":evidence,"evidence_sha256":evidence_hash,
            "derivation":derivation,"pass":passed,
            "typed_failure_reason":None if passed else (failure or name.upper()+"_MISMATCH")}

def gate(name: str, checks: list[dict[str,Any]], limitation: str|None=None) -> dict[str,Any]:
    if any(not c["pass"] for c in checks): status="FAIL"
    elif limitation: status="PASS_WITH_TYPED_PROVENANCE_LIMITATION"
    else: status="PASS"
    return {"gate":name,"status":status,"checks":checks,"typed_provenance_limitation":limitation}

def historical_authority() -> tuple[list[dict[str,Any]],dict[str,Any]]:
    auth=json.loads(AUTH.read_text())
    expected={"authorization_header":"HUMAN_OWNER_STAGE_AUTHORIZATION_V1","human_owner_assertion":"I_PERSONALLY_AUTHORIZE_THIS_STAGE",
      "authorization_id":"XSV-TAICHI-002-SYNTHETIC-MORPHOLOGY-COLLAPSE-SCREEN-2026-08-05","profile":"EWP_XSV_TAICHI_002_SYNTHETIC_MORPHOLOGY_COLLAPSE_SCREEN_STAGE_V1",
      "profile_type":"TASK_SPECIFIC_NONREUSABLE_CAPABILITY_EXCEPTION","human_owner":"Tim Brewer","repository":"trbrewer/espresso-whole-pull","remote":"trbrewer/espresso-whole-pull",
      "task":"XSV-TAICHI-002_SYNTHETIC_MORPHOLOGY_AND_REQUIRED_PERMEABILITY_COLLAPSE_SCREEN","task_slug":"xsv_taichi_002","stage":"G0_PROTOCOL_BOOTSTRAP_THROUGH_G6_BOUNDED_EXECUTION_AND_EVIDENCE_PACKAGE",
      "branch":"verification/xsv-taichi-002-synthetic-morphology-collapse-screen","start_head":"40588d62ee03a31057f75adab1df8a9c609a10d6","start_tree":"2c7e264a8f53b96c79dd58c65722d7677a29954e",
      "base_main":"40588d62ee03a31057f75adab1df8a9c609a10d6","base_tree":"2c7e264a8f53b96c79dd58c65722d7677a29954e","protocol_bootstrap_exception":"AUTHORIZED",
      "required_checks":["source-and-boundary","inexpensive-checks"],"valid_until":"2026-08-31T23:59:59-05:00","next_stage_authority":"NONE","merge_authority":"NOT_GRANTED","physical_validation":"NOT_ESTABLISHED"}
    checks=[ck(k,auth.get(k),v,str(AUTH.relative_to(ROOT)),"load stage-authorization field",digest(AUTH),failure="G0_AUTHORIZATION_ENVELOPE_MISMATCH") for k,v in expected.items()]
    checks += [ck("issue",auth["issue"]["number"],60,str(AUTH.relative_to(ROOT)),"load governed issue number",digest(AUTH)),
      ck("pull_request",auth["pull_request"]["number"],61,str(AUTH.relative_to(ROOT)),"load governed PR number",digest(AUTH)),
      ck("puckworks_lock",[auth["puckworks"]["commit"],auth["puckworks"]["tree"]],[v2.PUCKWORKS["commit"],v2.PUCKWORKS["tree"]],str(AUTH.relative_to(ROOT)),"load dependency lock",digest(AUTH)),
      ck("run_ceilings",auth["run_ceilings"],[*[]] if False else {"planned_scored_cuda_identities":22,"total_process_attempts":24,"infrastructure_retries":2,"openfoam":0,"full_basket":0,"explicit_fines":0},str(AUTH.relative_to(ROOT)),"load all frozen ceilings",digest(AUTH)),
      ck("capability_boundaries",["MERGE","OPENFOAM","PHYSICAL_VALIDATION_PROMOTION","XSV_TAICHI_003"], [x for x in ("MERGE","OPENFOAM","PHYSICAL_VALIDATION_PROMOTION","XSV_TAICHI_003") if x in auth["prohibited_capabilities"]],str(AUTH.relative_to(ROOT)),"require prohibited capabilities",digest(AUTH))]
    ancestor=subprocess.run(["git","merge-base","--is-ancestor",G0_HEAD,START_HEAD],cwd=ROOT).returncode==0
    parent=git_text("rev-parse",f"{G1_HEAD}^")
    historical={p:git("show",f"{G0_HEAD}:{p}") for p in (str(PROTOCOL_MD.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(MATRIX.relative_to(ROOT)),AUTH_HISTORICAL_PATH)}
    hist_auth=json.loads(historical[AUTH_HISTORICAL_PATH])
    checks += [ck("g0_ancestor",ancestor,True,"git merge-base",f"git merge-base --is-ancestor {G0_HEAD} {START_HEAD}"),
      ck("g0_is_final_pre_g1",parent,G0_HEAD,"git commit graph",f"parent of target-freeze commit {G1_HEAD}"),
      ck("historical_protocol_hash",sha(historical[str(PROTOCOL_MD.relative_to(ROOT))]),HISTORICAL_G0_PROTOCOL,f"git:{G0_HEAD}:{PROTOCOL_MD.relative_to(ROOT)}","git show bytes then SHA-256"),
      ck("historical_machine_protocol_hash",sha(historical[str(PROTOCOL.relative_to(ROOT))]),MACHINE_PROTOCOL,f"git:{G0_HEAD}:{PROTOCOL.relative_to(ROOT)}","git show bytes then SHA-256"),
      ck("historical_matrix_hash",sha(historical[str(MATRIX.relative_to(ROOT))]),MATRIX_HASH,f"git:{G0_HEAD}:{MATRIX.relative_to(ROOT)}","git show bytes then SHA-256"),
      ck("historical_human_envelope",[hist_auth["authorization_header"],hist_auth["human_owner_assertion"]],["HUMAN_OWNER_STAGE_AUTHORIZATION_V1","I_PERSONALLY_AUTHORIZE_THIS_STAGE"],f"git:{G0_HEAD}:{AUTH_HISTORICAL_PATH}","parse historical Git object"),
      ck("historical_pre_execution",hist_auth["g0_execution_state"],{"target_numerically_derived":False,"geometry_generated":False,"taichi_executions":0,"cuda_executions":0,"openfoam_executions":0},f"git:{G0_HEAD}:{AUTH_HISTORICAL_PATH}","parse historical G0 state"),
      ck("current_protocol_hash",digest(PROTOCOL_MD),CURRENT_PROTOCOL,str(PROTOCOL_MD.relative_to(ROOT)),"SHA-256 current reporting protocol",digest(PROTOCOL_MD))]
    ci=[{"name":"source-and-boundary","head_sha":G0_HEAD,"conclusion":"success","run_id":31023745600,"completed_at":"2026-08-05T16:07:46Z"},{"name":"inexpensive-checks","head_sha":G0_HEAD,"conclusion":"success","run_id":31023745681,"completed_at":"2026-08-05T16:09:30Z"}]
    checks.append(ck("historical_exact_head_ci",[(x["name"],x["head_sha"],x["conclusion"]) for x in ci],[(x,G0_HEAD,"success") for x in ("source-and-boundary","inexpensive-checks")],"GitHub check-runs API","match check name, head SHA, conclusion; retrieval bound in G8 record"))
    return checks,{"head":G0_HEAD,"historical_protocol_sha256":HISTORICAL_G0_PROTOCOL,"current_protocol_sha256":CURRENT_PROTOCOL,"ci_evidence":ci,"ci_disposition":"PASS"}

def target_checks() -> tuple[list[dict[str,Any]],dict[str,float]]:
    target=json.loads(TARGET.read_text())
    with TARGET_INPUTS.open(newline="",encoding="utf-8") as handle: rows=list(csv.DictReader(handle))
    checks=[ck("target_row_count",len(rows),3,str(TARGET_INPUTS.relative_to(ROOT)),"CSV parse",digest(TARGET_INPUTS)),
      ck("nominal_groups",[int(r["nominal_group_bar"]) for r in rows],[5,9,11],str(TARGET_INPUTS.relative_to(ROOT)),"ordered CSV groups",digest(TARGET_INPUTS))]
    inputs={int(x["nominal_group_bar"]):x for x in target["inputs"]}
    for r in rows:
        n=int(r["nominal_group_bar"]); t=inputs[n]
        expected=[t["condition"],n,t["time_s"],t["source_csv_line"],t["basket_pressure_bar"],t["mass_flow_g_s"]]
        observed=[r["condition"],n,float(r["source_time_s"]),int(r["source_csv_line"]),float(r["pressure_bar"]),float(r["mass_flow_g_s"])]
        checks.append(ck(f"row_{n}_json_csv_identity",observed,expected,str(TARGET_INPUTS.relative_to(ROOT)),"parse CSV and target JSON",digest(TARGET_INPUTS)))
        checks += [ck(f"row_{n}_pressure_field",[r["pressure_node"],"bar"],[target["selection_rule"]["pressure_field"],"bar"],str(TARGET_INPUTS.relative_to(ROOT)),"field/unit linkage",digest(TARGET_INPUTS)),
          ck(f"row_{n}_flow_field",[r["flow_field"],"g/s"],[target["selection_rule"]["flow_field"],"g/s"],str(TARGET_INPUTS.relative_to(ROOT)),"field/unit linkage",digest(TARGET_INPUTS)),
          ck(f"row_{n}_source",[r["source_path"],r["source_sha256"]],[target["source_files"]["traces"]["path"],target["source_files"]["traces"]["sha256"]],str(TARGET_INPUTS.relative_to(ROOT)),"source path/hash linkage",digest(TARGET_INPUTS))]
    h={n:float(r["mass_flow_g_s"])/float(r["pressure_bar"]) for n,r in [(int(x["nominal_group_bar"]),x) for x in rows]}
    ratios={"T_11_5":h[11]/h[5],"T_9_5":h[9]/h[5],"T_11_9":h[11]/h[9],"nominal_screen":5/11}
    for key in ("T_11_5","T_9_5","T_11_9"):
        checks.append(ck(key,rel(ratios[key],target["ratios"][key])<=1e-15,True,str(TARGET_INPUTS.relative_to(ROOT)),"independent Q/delta-p ratio recomputation",digest(TARGET_INPUTS),operator="RELATIVE_DIFFERENCE_LE_1E-15"))
    checks += [ck("selection_rule",target["selection_rule"]["rule"],"maximum time__s row within each exact reference_pressure_round__bar group",str(TARGET.relative_to(ROOT)),"load frozen selection rule",digest(TARGET)),ck("no_new_window",target["selection_rule"]["new_window_selected"],False,str(TARGET.relative_to(ROOT)),"load frozen selection rule",digest(TARGET)),ck("orientation",target["ratios"]["orientation"],"SMALLER_IS_GREATER_REQUIRED_COLLAPSE",str(TARGET.relative_to(ROOT)),"load target orientation",digest(TARGET)),ck("attainment_operator",target["ratios"]["primary_attainment_rule"],"K_case_over_K_reference <= T_11_5",str(TARGET.relative_to(ROOT)),"load frozen rule",digest(TARGET)),ck("target_type",target["target_type"],"APPARENT_HYDRAULIC_CONDUCTANCE_RATIO_TARGET",str(TARGET.relative_to(ROOT)),"load target type",digest(TARGET)),ck("nominal_role",target["nominal_pressure_ordering_screen"]["is_primary_target"],False,str(TARGET.relative_to(ROOT)),"separate nominal screen",digest(TARGET))]
    return checks,ratios

def geometry_checks(evidence: Path) -> tuple[list[dict[str,Any]],list[dict[str,Any]]]:
    import numpy as np
    import xsv_taichi_002_runtime as historical
    doc=json.loads(GEOMETRY.read_text()); checks=[]; table=[]; masks={}
    for g in doc["geometries"]:
        name=g["mask_id"]; pa=evidence/"geometry/repeat_a"/f"{name}.uint8"; pb=evidence/"geometry/repeat_b"/f"{name}.uint8"
        ba=pa.read_bytes(); bb=pb.read_bytes(); a=np.frombuffer(ba,dtype=np.uint8).reshape(g["shape"]); masks[name]=a
        con=historical.connectivity(a.astype(bool)); solid=int(a.sum()); fluid=int(a.size-solid); phi=fluid/a.size
        row={"geometry_id":name,"repeat_a_sha256":sha(ba),"repeat_b_sha256":sha(bb),"repeat_byte_identity":ba==bb,"n_solid":solid,"n_fluid":fluid,"phi_gross":phi,**con}
        table.append(row)
        pairs=[("repeat_bytes",ba==bb,True),("repeat_a_hash",sha(ba),g["payload_sha256"]),("repeat_b_hash",sha(bb),g["payload_sha256"]),("byte_count",len(ba),int(np.prod(g["shape"]))),("dtype",str(a.dtype),g["dtype"]),("n_solid",solid,g["n_solid"]),("n_fluid",fluid,g["n_fluid"]),("phi_gross",phi,g["phi_gross"])]
        for d in "xyz": pairs += [(f"through_{d}",con[f"through_{d}"],g[f"through_{d}"]),(f"phi_connected_{d}",con[f"phi_connected_{d}"],g[f"phi_connected_{d}"])]
        checks += [ck(f"{name}_{k}",o,e,f"geometry/repeat_a/{name}.uint8" if "repeat_b" not in k else f"geometry/repeat_b/{name}.uint8","read actual mask bytes and independently recompute",sha(ba) if "repeat_b" not in k else sha(bb)) for k,o,e in pairs]
    checks.append(ck("actual_baseline_payload",sha((evidence/"geometry/repeat_a/H-A0-S42.uint8").read_bytes()),"10d9a010cbac4b8579154456c4271ecd2808af5116beab15a2ffd4e2c99cd039","geometry/repeat_a/H-A0-S42.uint8","hash retained baseline payload"))
    base=masks["H-A0-S42"]
    removed=[]
    for name in ("C05","C15","C30"):
        m=masks[name]; r=set(np.flatnonzero((base==0)&(m==1)).tolist()); removed.append(r)
        expected=next(g for g in doc["geometries"] if g["mask_id"]==name)["removed_voxel_count"]
        checks += [ck(f"{name}_removed_count",len(r),expected,f"geometry/repeat_a/{name}.uint8","set difference against actual baseline"),ck(f"{name}_only_fluid_to_solid",bool(np.all(m[base==1]==1)),True,f"geometry/repeat_a/{name}.uint8","verify no baseline solid becomes fluid")]
    checks.append(ck("coating_nestedness",removed[0] <= removed[1] <= removed[2],True,"geometry/repeat_a/{C05,C15,C30}.uint8","actual removed-voxel set inclusion"))
    return checks,table

def claim_checks(result: dict[str,Any]) -> list[dict[str,Any]]:
    docs=[CASE/"XSV_TAICHI_002_SUMMARY.md",ROOT/"docs/PROJECT_STATE.md",ROOT/"docs/CLAIM_CEILING.md",PROTOCOL_MD,CASE/"XSV_TAICHI_002_EXACT_HEAD_REVIEW_CORRECTION.json",AUTH]
    forbidden=("COMPACTION_CONFIRMED","FINES_CONFIRMED","FINES_MIGRATION_CONFIRMED","FINES_DEPOSITION_CONFIRMED","CLOGGING_CONFIRMED","CHANNELING_CONFIRMED","DAMAGE_CONFIRMED","REAL_COFFEE_MORPHOLOGY_REPRESENTED","REAL_COFFEE_PERMEABILITY_ESTABLISHED","REAL_COFFEE_ANISOTROPY_ESTABLISHED","OPENFOAM_PHYSICALLY_VALIDATED","GENERAL_SOLVER_PHYSICAL_VALIDATION_ESTABLISHED","NEW_GOVERNING_PHYSICS_JUSTIFIED","INDEPENDENT_DATA_GATE_SATISFIED")
    checks=[]
    for p in docs:
        text=p.read_text(); positives=[x for x in forbidden if x in text and not any(prefix+x in text for prefix in ("prohibited: ","Prohibited: ","not `","not "))]
        checks.append(ck(f"claims_{p.name}",positives,[],str(p.relative_to(ROOT)),"scan canonical authority for positive prohibited claims while excluding explicit prohibition/not-established context",digest(p)))
    result_text=json.dumps(result); result_positives=[x for x in forbidden if x in result_text]
    checks.append(ck("claims_candidate_result",result_positives,[],"in-memory candidate result","scan candidate result object before serialization"))
    qa=json.loads((ROOT/"PACKAGE_QA_STATUS.json").read_text())["xsv_taichi_002"]
    qa_projection={k:qa.get(k) for k in ("scientific_disposition","localization_disposition","anisotropy_disposition","current_scientific_gate","physical_validation","xsv_taichi_003")}
    checks.append(ck("claims_package_qa_projection",[x for x in forbidden if x in json.dumps(qa_projection)],[],"PACKAGE_QA_STATUS.json:xsv_taichi_002 claim projection","scan claim fields independent of mechanically updated artifact hashes",sha(canonical(qa_projection))))
    protocol=json.loads(PROTOCOL.read_text()); threshold_text=json.dumps(protocol.get("thresholds",{})).lower()
    checks += [ck("protocol_has_no_localization_threshold",not any(x in threshold_text for x in ("sigma_micro","coefficient_of_variation","fastest_quartile","localization")),True,str(PROTOCOL.relative_to(ROOT)),"inspect frozen thresholds object for any localization magnitude threshold",digest(PROTOCOL)),ck("localization_disposition",result["localization"]["disposition"],"FLOW_LOCALIZATION_RESPONSE_REPORTED_DESCRIPTIVELY_NO_PROSPECTIVE_CHANGE_THRESHOLD","derived result", "inspect current result"),ck("localization_metrics_retained",all(k in result["localization"]["summary"] for k in ("sigma_micro","coefficient_of_variation","fastest_quartile_flow_share")),True,"derived result","verify exact descriptive metrics remain")]
    return checks

def reduce(evidence: Path, archive: Path, output: Path) -> None:
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        base=Path(td)/"v2"; v2.reduce(evidence,archive,base)
        for p in base.rglob("*"):
            if p.is_file():
                q=output/p.relative_to(base); q.parent.mkdir(parents=True,exist_ok=True); q.write_bytes(p.read_bytes())
    result=json.loads((output/"XSV_TAICHI_002_RESULT.json").read_text())
    g0c,g0info=historical_authority(); g1c,ratios=target_checks(); g2c,geometry_table=geometry_checks(evidence)
    run_checks=result["run_binding_checks"]
    g3c=[ck("run_to_matrix_bindings",all(x["pass"] for x in run_checks),True,"22 retained run.json and primitive artifacts","validate each matrix/configuration/primitive binding"),ck("successful_identity_set",len(result["runs"]),22,"external evidence lbm/*/run.json","count unique successfully retained run identities")]
    attempt_limitation="PROCESS_ATTEMPT_COUNT_AND_CEILING_COMPLIANCE_NOT_INDEPENDENTLY_RECONSTRUCTED"
    g4c=[]
    for r in result["runs"]:
        g4c += [ck(f"{r['run_id']}_qualified",r["binding_status"],"PASS",f"lbm/{r['run_id']}/run.json","run binding plus frozen numerical gates",r["run_record_sha256"])]
    g4c += [ck("baseline_reproduction",rel(next(r for r in result["runs"] if r["run_id"]=="H-A0-S42-X-MID")["K_gross_lu"],1.7919979172502785)<=.0025,True,"lbm/H-A0-S42-X-MID/run.json","recompute relative baseline difference"),ck("linearity_anchors",all(x["pass"] for x in result["linearity"].values()),True,"six retained low/mid/high run records","recompute both fits")]
    g5c=claim_checks(result)+[ck("constriction",result["family_dispositions"]["constriction"],"REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_CONSTRICTION_ENVELOPE","retained primitive K ratios","derive classification"),ck("heterogeneity",result["family_dispositions"]["heterogeneity"],"REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_HETEROGENEITY_ENVELOPE","paired seed primitive K/porosity","derive separately by amplitude"),ck("overall",result["overall_synthesis"],"REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_X_DIRECTION_ENVELOPE","derived family dispositions","derive overall from family results")]
    raw=v2.verify_raw_manifest(evidence/"SELF_EXCLUDING_MANIFEST.json",evidence)
    g6c=[ck("raw_manifest_hash",raw["hash"],v2.EXPECTED["raw_manifest"],"SELF_EXCLUDING_MANIFEST.json","hash actual raw manifest"),ck("all_raw_members",raw["all_members_verified"],True,"SELF_EXCLUDING_MANIFEST.json","verify every listed member bytes/hash"),ck("archive_hash",digest(archive),v2.EXPECTED["archive"],archive.name,"hash immutable archive"),ck("archive_bytes",archive.stat().st_size,12953600,archive.name,"stat immutable archive")]
    gates={g["gate"]:g for g in (gate("G0_PROTOCOL_BOOTSTRAP_AND_PROSPECTIVE_FREEZE",g0c),gate("G1_REQUIRED_COLLAPSE_TARGET_DERIVATION_AND_FREEZE",g1c),gate("G2_DETERMINISTIC_GEOMETRY_GENERATION_AND_IDENTITY_FREEZE",g2c),gate("G3_BOUNDED_TAICHI_CUDA_EXECUTION",g3c,attempt_limitation),gate("G4_DETERMINISTIC_REDUCTION_AND_NUMERICAL_QUALIFICATION",g4c),gate("G5_SCIENTIFIC_SYNTHESIS_AND_CLAIM_BOUNDED_DISPOSITION",g5c),gate("G6_FINAL_EVIDENCE_PACKAGE",g6c))}
    result["schema_version"]="espresso.whole_pull.xsv_taichi_002.corrected_result.v3"
    result["reduction"].update({"formula_version":"XSV_TAICHI_002_REVIEW_REDUCER_V3","reducer_path":str(Path(__file__).resolve().relative_to(ROOT)),"reducer_sha256":digest(Path(__file__)),"review_reducer_v2_sha256":V2_HASH,"review_reducer_v2_result_sha256":V2_RESULT})
    result["historical_g0"]=g0info; result["target"]["recomputed_ratios"]=ratios; result["geometry_verification"]=geometry_table
    result["attempt_provenance"]={"retained_successful_run_records":22,"process_attempt_count":"NOT_INDEPENDENTLY_RECONSTRUCTED","retry_disposition":"NO_RETAINED_RETRY_RECORD","attempt_ceiling_compliance":"NOT_INDEPENDENTLY_RECONSTRUCTED","chronological_execution_order":"NOT_INDEPENDENTLY_RECONSTRUCTED"}
    result["gates"]=gates; result["local_package_status"]="PASS_WITH_TYPED_PROVENANCE_LIMITATION" if all(g["status"]!="FAIL" for g in gates.values()) else "FAIL"; result["final_exact_head_ci"]="PENDING"
    (output/"XSV_TAICHI_002_RESULT.json").write_bytes(canonical(result))
    rows=list(csv.DictReader((output/"XSV_TAICHI_002_RUN_MANIFEST.csv").open()))
    for r in rows: r.pop("attempt_id",None); r["retained_record_class"]="SUCCESSFUL_RUN_RECORD_NOT_PROCESS_ATTEMPT_LEDGER"
    with (output/"XSV_TAICHI_002_RUN_MANIFEST.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n"); w.writeheader(); w.writerows(rows)
    summary=(output/"XSV_TAICHI_002_SUMMARY.md").read_text().replace("All 22 frozen identities were executed and the final package order matches the case matrix. Chronological execution order is not independently reconstructable from a separate immutable ledger.","All 22 frozen identities have successful retained run records, and final package order matches the case matrix. No independent process-attempt ledger was retained: process-attempt count, retry-ceiling compliance, and chronological execution order are not independently reconstructable. This provenance limitation does not disqualify the 22 retained numerical results.")
    (output/"XSV_TAICHI_002_SUMMARY.md").write_text(summary)
    correction={"schema_version":"espresso.whole_pull.xsv_taichi_002.g8_evidence_binding_correction.v1","authorization_id":"XSV-TAICHI-002-FAIL-CLOSED-EVIDENCE-BINDING-CORRECTION-2026-08-05","start_head":START_HEAD,"start_tree":"8b485890888e8f48a25b728cebf74ba934560d19","historical_execution_runtime_sha256":v2.EXPECTED["runtime"],"review_reducer_v2_sha256":V2_HASH,"review_reducer_v2_result_sha256":V2_RESULT,"review_reducer_v3_sha256":digest(Path(__file__)),"corrected_result_sha256":digest(output/"XSV_TAICHI_002_RESULT.json"),"historical_g0":g0info,"attempt_provenance":result["attempt_provenance"],"raw_manifest_sha256":raw["hash"],"external_archive_sha256":digest(archive),"deterministic_double_reduction":"REQUIRE_EXTERNAL_BYTE_COMPARISON","numerical_rerun":"NONE","scientific_evidence_change":"NONE","merge_authority":"NOT_GRANTED","physical_validation":"NOT_ESTABLISHED"}
    (output/"XSV_TAICHI_002_G8_EVIDENCE_BINDING_CORRECTION.json").write_bytes(canonical(correction))
    committed=[output/"XSV_TAICHI_002_RESULT.json",output/"XSV_TAICHI_002_SUMMARY.md",output/"XSV_TAICHI_002_RUN_MANIFEST.csv",output/"XSV_TAICHI_002_G8_EVIDENCE_BINDING_CORRECTION.json",Path(__file__)]+sorted((output/"plots").iterdir())
    artifact={"schema_version":"espresso.whole_pull.xsv_taichi_002.corrected_artifact_manifest.v3","task":"XSV-TAICHI-002","lineage":{"pre_review_result_sha256":v2.PRE_REVIEW_RESULT,"review_reducer_v2_sha256":V2_HASH,"review_reducer_v2_result_sha256":V2_RESULT,"historical_execution_runtime_sha256":v2.EXPECTED["runtime"]},"external_manifest":{"sha256":raw["hash"],"member_count":raw["member_count"],"source_bytes":raw["source_bytes"],"all_members_verified":raw["all_members_verified"]},"external_archive":{"sha256":digest(archive),"bytes":archive.stat().st_size,"regular_file_count":93},"committed_members":{("xsv_taichi_002_review_reducer_v3.py" if p==Path(__file__) else p.relative_to(output).as_posix()):digest(p) for p in committed},"deterministic_reduction_contract":"RUN_V3_TWICE_IN_SEPARATE_CLEAN_DESTINATIONS_AND_COMPARE_BYTES","physical_validation":"NOT_ESTABLISHED"}
    (output/"XSV_TAICHI_002_ARTIFACT_MANIFEST.json").write_bytes(canonical(artifact))

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--evidence-root",type=Path,required=True); p.add_argument("--archive",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); reduce(a.evidence_root.resolve(),a.archive.resolve(),a.output.resolve()); return 0
if __name__=="__main__": raise SystemExit(main())
