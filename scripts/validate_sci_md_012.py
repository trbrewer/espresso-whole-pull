#!/usr/bin/env python3
"""Focused fail-closed validator for SCI-MD-012 artifacts."""
from __future__ import annotations
import argparse, csv, hashlib, importlib.util, json, math
from pathlib import Path

FORBIDDEN_KEYS = {"score", "rmse", "loss_ranking", "model_win", "bootstrap", "confidence_interval"}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def fail(ok, message):
    if not ok: raise ValueError(message)

def core(root):
    p=root/"scripts/sci_md_011_core.py"; spec=importlib.util.spec_from_file_location("sci_md_011_core_validation",p)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def walk_keys(value):
    if isinstance(value, dict):
        for k,v in value.items(): yield k; yield from walk_keys(v)
    elif isinstance(value, list):
        for v in value: yield from walk_keys(v)

def validate(root: Path) -> None:
    root=root.resolve(); d=root/"docs/analysis/sci_md_012"
    required={"AUTHORITY_AND_SCOPE.json","ROOT_FEASIBILITY.csv","PARAMETER_FEASIBILITY.json","SOURCE_PARAMETERIZATION_COMPARISON.json","DIAGNOSIS.json","RESULT.md","ARTIFACT_MANIFEST.json"}
    fail(required <= {p.name for p in d.iterdir()}, "MISSING_REQUIRED_ARTIFACT")
    manifest=load(d/"ARTIFACT_MANIFEST.json"); entries={x["path"]:x["sha256"] for x in manifest["artifacts"]}
    fail(set(entries)==required-{"ARTIFACT_MANIFEST.json"}, "MANIFEST_MEMBERSHIP_MISMATCH")
    for name,digest in entries.items(): fail(sha(d/name)==digest, "MANIFEST_HASH_MISMATCH:"+name)
    authority=load(d/"AUTHORITY_AND_SCOPE.json")
    for name,digest in authority["immutable_input_sha256"].items(): fail(sha(root/name)==digest, "IMMUTABLE_INPUT_HASH_MISMATCH:"+name)
    c=core(root); rows=list(csv.DictReader((d/"ROOT_FEASIBILITY.csv").open()))
    fail(len(rows)==6 and len({r["brew_id"] for r in rows})==6, "EXPECTED_SIX_UNIQUE_BREWS")
    for r in rows:
        nums={k:float(v) for k,v in r.items() if k in {"measured_line_pressure_bar","frozen_Qc_g_s","frozen_Pc_bar","hi_basket_pressure_bar","x_hi","q_hi_g_s","h_lo_bar","h_hi_bar","closure_only_endpoint_bar","machine_adapter_contribution_bar","coupled_line_pressure_ceiling_bar","representability_margin_bar","Pc_required_bar","Qc_required_g_s_at_frozen_Pc"}}
        line,qc,pc=nums["measured_line_pressure_bar"],nums["frozen_Qc_g_s"],nums["frozen_Pc_bar"]
        hi=min(pc*(1-c.DOMAIN_EPS),max(0,line-c.CAL["c"])); qhi=qc*c.fphi(hi/pc)
        fail(math.isclose(nums["hi_basket_pressure_bar"],hi,rel_tol=0,abs_tol=1e-14),"CHANGED_ENDPOINT")
        fail(math.isclose(nums["q_hi_g_s"],qhi,rel_tol=0,abs_tol=1e-14),"CHANGED_QHI")
        ceiling=hi+c.brewer_drop(qhi)
        fail(math.isclose(nums["h_lo_bar"],c.brewer_drop(qc*c.fphi(0))-line,rel_tol=0,abs_tol=1e-14),"CHANGED_HLO")
        fail(math.isclose(nums["h_hi_bar"],ceiling-line,rel_tol=0,abs_tol=1e-14),"CHANGED_HHI")
        fail(math.isclose(nums["closure_only_endpoint_bar"]+nums["machine_adapter_contribution_bar"],nums["coupled_line_pressure_ceiling_bar"],rel_tol=0,abs_tol=1e-14),"ADAPTER_DECOMPOSITION_MISMATCH")
        fail(math.isclose(nums["representability_margin_bar"],ceiling-line,rel_tol=0,abs_tol=1e-14),"CHANGED_MARGIN")
        pc_req=(line-c.brewer_drop(qc*c.fphi(1-c.DOMAIN_EPS)))/(1-c.DOMAIN_EPS)
        fail(math.isclose(nums["Pc_required_bar"],pc_req,rel_tol=0,abs_tol=1e-14),"CHANGED_PC_THRESHOLD")
        q=nums["Qc_required_g_s_at_frozen_Pc"]*c.fphi(1-c.DOMAIN_EPS)
        fail(math.isclose(c.brewer_drop(q),line-pc*(1-c.DOMAIN_EPS),rel_tol=0,abs_tol=1e-13),"CHANGED_QC_THRESHOLD")
        fail(r["target_exposed"]=="True" and r["prediction"]=="False" and r["scoring_use_prohibited"]=="True" and r["fitting_use_prohibited"]=="True","TARGET_EXPOSED_FLAGS_MISSING")
    p=load(d/"PARAMETER_FEASIBILITY.json"); diagnosis=load(d/"DIAGNOSIS.json")
    fail(p["witness"]["inside_existing_bounds"],"WITNESS_OUTSIDE_BOUNDS")
    fail(not p["witness"]["witness_is_prediction"] and not p["witness"]["witness_is_candidate_fit"] and not p["witness"]["witness_is_scored"],"WITNESS_MISREPRESENTED")
    fail(diagnosis["architecture"]=="NOT_ADJUDICATED" and diagnosis["m01"]=="NOT_ADJUDICATED","UNAUTHORIZED_ARCHITECTURE_DECISION")
    if diagnosis["targeted_measurement_authorized"]:
        fail(diagnosis.get("measurement_irreducible") and diagnosis.get("measurement_decision_material"),"UNSUPPORTED_MEASUREMENT_AUTHORIZATION")
    if diagnosis["next_action"]=="DEFINE_SEPARATELY_FROZEN_REPARAMETERIZATION_TEST":
        fail(diagnosis["decision_materiality"]=="ROOT_REPAIR_COULD_CHANGE_ADOPTION_DECISION","ROOT_WITNESS_ALONE_SELECTED_REPARAMETERIZATION")
    for path in d.iterdir():
        if path.suffix==".json": fail(not (set(walk_keys(load(path))) & FORBIDDEN_KEYS),"FABRICATED_SCORING_FIELD")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); a=ap.parse_args()
    validate(a.root); print("SCI_MD_012_VALIDATION_PASS"); return 0
if __name__=="__main__": raise SystemExit(main())
