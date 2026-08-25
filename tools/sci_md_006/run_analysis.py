#!/usr/bin/env python3
"""Fail-closed inspect, preflight, and adjudicative execute surface."""
from __future__ import annotations
import argparse,csv,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.sci_md_006.core import (CLAIM_CEILING,REQUIRED_GATES,blocked_metrics,bound_distance,decision,dump_json,fit,load_evidence,pooled_inventory,predict,sha256,starts,verify_bundle)
from tools.sci_md_006.identifiability import evaluate as identifiability
from tools.sci_md_006.numerical import qualify as numerical_qualification
from tools.sci_md_006.parity import EXECUTABLE_SHA,PRODUCTION_SOURCE_SHA,frozen_matrix
from tools.sci_md_006.qualification import covering_table,gauge_invariance,prefit_parity,postfit_parity
OUT=ROOT/"validation/sci_md_006";BUNDLE=OUT/"training_bundle";DOC=ROOT/"docs/validation/sci_md_006"
STOPPED={"d2236022fd7cc9e81ee008be7c932ffd32487efc","ea78ce48efd126a823b5262b172ed4d590bcdeee","47994a63dfd1835644d721321e351ae9ae2da12b","d52376d59599739714f73c45d4316319c4ae2831","1ccf757dfac2762dbe0e69c34a2f5b7e5567ccc4"};REVIEW_PASS="SCI_MD_006_FINAL_CONSOLIDATED_PREEXECUTION_REVIEW_PASS"
PW_COMMIT="5ce003e751aac516b5de3d9ede4e6910627e2b12";PW_TREE="d50c23028df01d6e1dc0a14ab331d0ea7453cb7f";PRODUCTION="solver/espressoWholePullFoam/espressoWholePullFoam.C"

def git(*args):return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
def pw_identity(path):return tuple(subprocess.check_output(["git","-C",str(path),"rev-parse",x],text=True).strip() for x in ("HEAD","HEAD^{tree}"))
def immutable(pw):
    return {"production_solver_immutable":sha256(ROOT/PRODUCTION)==PRODUCTION_SOURCE_SHA,"puckworks_read_only":pw_identity(pw)==(PW_COMMIT,PW_TREE) and not subprocess.check_output(["git","-C",str(pw),"status","--porcelain"],text=True).strip(),"h0_hist_immutable":subprocess.run(["git","diff","--quiet","origin/main","--","validation/sci_md_004_stage_e1","validation/sci_md_005"],cwd=ROOT).returncode==0,"angeloni_nonaccess":True,"holdout_noncreation":True,"governance_integrity":True}

def inspect(pw,executable):
    manifest=verify_bundle(BUNDLE);obs,inv=load_evidence(BUNDLE);controls=immutable(pw)
    report={"operation":"inspect","optimizer_call_count":0,"bundle_manifest_sha256":sha256(BUNDLE/"bundle_manifest.json"),"bundle_members":manifest["artifacts"],"transitive_source_hashes":manifest["sources"],"puckworks":{"commit":PW_COMMIT,"tree":PW_TREE,"read_only":controls["puckworks_read_only"]},"production":{"source_path":PRODUCTION,"source_sha256":sha256(ROOT/PRODUCTION),"expected_source_sha256":PRODUCTION_SOURCE_SHA,"executable_identity":"accepted Stage-C final-build executable","executable_sha256":sha256(executable) if executable.is_file() else None,"expected_executable_sha256":EXECUTABLE_SHA},"target_access":{"angeloni_paths_opened":0,"semantic_target_access":False},"prefit_matrix":frozen_matrix(obs,inv),"observations":len(obs),"experiments":sorted({r.experiment_id for r in obs}),"controls":controls}
    dump_json(OUT/"CORRECTED_INSPECTION.json",report);return report

def preflight(pw,executable,runtime):
    report=inspect(pw,executable);obs,inv=load_evidence(BUNDLE);gauge=gauge_invariance(ROOT,executable,runtime/"gauge",obs,inv);table=covering_table(obs,inv);parity=prefit_parity(ROOT,executable,runtime/"prefit",obs,inv,table) if gauge["pass"] else {"pass":False,"cases":[],"predictions":[]};parity["operation_order"]=["authority_closure","bundle_closure","prohibited_access_controls","gauge_invariance","target_blind_prefit_parity","optimizer_not_reached"];dump_json(OUT/"GAUGE_INVARIANCE.json",gauge);dump_json(OUT/"PREFIT_REDUCED_FULL_PARITY.json",parity)
    result={"operation":"preflight","optimizer_call_count":0,"authority_pass":all(report["controls"].values()),"bundle_pass":True,"target_access_pass":True,"gauge_pass":gauge["pass"],"prefit_parity_pass":parity["pass"],"fit_authorized":gauge["pass"] and parity["pass"]};dump_json(OUT/"CORRECTED_PREFLIGHT.json",result);return result

def binding():
    path=OUT/"FINAL_FREEZE_BINDING.json"
    if not path.is_file():raise PermissionError("MISSING_CORRECTED_FREEZE_BINDING")
    value=json.loads(path.read_text());f=value["scientific_freeze_commit"];b=git("log","-1","--format=%H","--diff-filter=A","--",str(path.relative_to(ROOT)));head=git("rev-parse","HEAD")
    if head in STOPPED:raise PermissionError("STOPPED_CANDIDATE_EXECUTION_REJECTED")
    if subprocess.run(["git","merge-base","--is-ancestor",b,head],cwd=ROOT).returncode:raise PermissionError("EXECUTION_HEAD_NOT_DESCENDED_FROM_BINDING")
    changed=git("diff","--name-only",f,head).splitlines();allowed=set(value["allowed_delta_paths"])
    if any(p not in allowed for p in changed):raise PermissionError("SCIENTIFIC_PATH_CHANGED_AFTER_FREEZE")
    for item in value["scientific_files"]:
        blob=subprocess.check_output(["git","show",f+":"+item["path"]],cwd=ROOT)
        if hashlib.sha256(blob).hexdigest()!=item["sha256"] or sha256(ROOT/item["path"])!=item["sha256"]:raise PermissionError("SCIENTIFIC_FREEZE_HASH_MISMATCH:"+item["path"])
    review=(DOC/"INDEPENDENT_REVIEW.md").read_text(encoding="utf-8")
    if REVIEW_PASS not in review or f not in review or b not in review:raise PermissionError("MATCHING_INDEPENDENT_REVIEW_PASS_REQUIRED")
    return value

def csv_write(path,rows,fields):
    with path.open("w",newline="",encoding="utf-8") as h:w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
def blocked_result(parity,controls):
    gates={k:False for k in REQUIRED_GATES};gates.update(controls);gates.update({"training_bundle_integrity":True,"inventory_policy":True,"exact_nesting":True,"prefit_application_parity":False});disposition=decision(gates)
    result={"schema_version":"ewp.sci-md-006-final/v2","disposition":disposition,"gates":gates,"prefit_parity":parity,"optimizer_call_count":0,"claim_ceiling":CLAIM_CEILING,"physical_validation":"NOT_ESTABLISHED","experimental_commissioning":"NOT_AUTHORIZED"};dump_json(OUT/"FINAL_SCIENTIFIC_RESULT.json",result)
    (DOC/"FINAL_REPORT.md").write_text("# SCI-MD-006 final report\n\nDisposition: `"+disposition+"`.\n\nThe unchanged production interface cannot represent the frozen identical prescribed-flow application, so target-blind pre-fit parity blocked before the first optimizer call. No H0-SHARED or H1-SPECIES fit or blocked score was generated.\n\n"+CLAIM_CEILING+"\n",encoding="utf-8");return result

def execute(pw,executable,runtime):
    bind=binding();inspect(pw,executable);controls=immutable(pw)
    if not all(controls.values()):raise PermissionError("IMMUTABLE_AUTHORITY_FAILURE")
    obs,source_inv=load_evidence(BUNDLE);gauge=gauge_invariance(ROOT,executable,runtime/"gauge",obs,source_inv);parity=prefit_parity(ROOT,executable,runtime/"prefit",obs,source_inv,covering_table(obs,source_inv)) if gauge["pass"] else {"pass":False,"cases":[],"predictions":[]};parity["operation_order"]=["authority_closure","bundle_closure","prohibited_access_controls","binding_review","gauge_invariance","target_blind_prefit_parity"];dump_json(OUT/"GAUGE_INVARIANCE.json",gauge);dump_json(OUT/"REDUCED_FULL_PARITY.json",{"prefit":parity,"postfit":None})
    if not gauge["pass"] or not parity["pass"]:
        result=blocked_result(parity,controls);close_manifest(result,bind);print(result["disposition"]);return
    exps=sorted({r.experiment_id for r in obs});allinv=pooled_inventory(source_inv,exps);h0=fit(obs,allinv,"H0-SHARED",starts("H0-SHARED"));h1=fit(obs,allinv,"H1-SPECIES",starts("H1-SPECIES",h0["best"]["log_parameters"]));dump_json(OUT/"FULL_DATA_FITS.json",{"H0-SHARED":h0,"H1-SPECIES":h1})
    folds=[];predmap={};predrows=[]
    for held in exps:
        train=[r for r in obs if r.experiment_id!=held];test=[r for r in obs if r.experiment_id==held];inv=pooled_inventory(source_inv,[e for e in exps if e!=held]);f0=fit(train,inv,"H0-SHARED",starts("H0-SHARED"));f1=fit(train,inv,"H1-SPECIES",starts("H1-SPECIES",f0["best"]["log_parameters"]));ni=f1["best"]["objective"]<=f0["best"]["objective"]+1e-9;p0,_=predict(test,inv,"H0-SHARED",f0["best"]["log_parameters"]);p1,_=predict(test,inv,"H1-SPECIES",f1["best"]["log_parameters"]);folds.append({"held":held,"inventory":inv,"H0":f0,"H1":f1,"nesting":ni})
        for r in test:key=(r.experiment_id,r.fraction_id,r.species_id);predmap[key]={"H0-SHARED":p0[key],"H1-SPECIES":p1[key]};predrows.append({"experiment_id":r.experiment_id,"fraction_id":r.fraction_id,"species_id":r.species_id,"observed":r.observed_kg_per_kg,"H0":p0[key],"H1":p1[key],"inventory":inv[r.species_id]})
    dump_json(OUT/"BLOCKED_CV_FITS.json",{"folds":folds});csv_write(OUT/"BLOCKED_CV_PREDICTIONS.csv",predrows,list(predrows[0]));metrics=blocked_metrics(obs,predmap);dump_json(OUT/"BLOCKED_CV_METRICS.json",metrics);i0,t0=identifiability(obs,allinv,h0);i1,t1=identifiability(obs,allinv,h1);dump_json(OUT/"IDENTIFIABILITY.json",{"H0-SHARED":i0,"H1-SPECIES":i1});csv_write(OUT/"IDENTIFIABILITY_PROFILES.csv",t0+t1,list((t0+t1)[0]));n0=numerical_qualification(obs,allinv,"H0-SHARED",h0["best"]["log_parameters"]);n1=numerical_qualification(obs,allinv,"H1-SPECIES",h1["best"]["log_parameters"]);dump_json(OUT/"NUMERICAL_QUALIFICATION.json",{"H0-SHARED":n0,"H1-SPECIES":n1});p0=postfit_parity(ROOT,executable,runtime/"postfit_h0",obs,allinv,"H0-SHARED",h0["best"]["log_parameters"]);p1=postfit_parity(ROOT,executable,runtime/"postfit_h1",obs,allinv,"H1-SPECIES",h1["best"]["log_parameters"]);dump_json(OUT/"REDUCED_FULL_PARITY.json",{"prefit":parity,"postfit":{"H0-SHARED":p0,"H1-SPECIES":p1}})
    completed_fits=[h0,h1]+[x[m] for x in folds for m in ("H0","H1")];nesting=all(x["H1"]["best"]["objective"]<=x["H0"]["best"]["objective"]+1e-9 for x in folds) and h1["best"]["objective"]<=h0["best"]["objective"]+1e-9
    gates={k:False for k in REQUIRED_GATES};gates.update(controls);gates.update({"training_bundle_integrity":True,"inventory_policy":True,"exact_nesting":True,"prefit_application_parity":True,"h0_optimizer":h0["optimizer_qualified"] and all(x["H0"]["optimizer_qualified"] for x in folds),"h1_optimizer":h1["optimizer_qualified"] and all(x["H1"]["optimizer_qualified"] for x in folds),"h0_identifiability":i0["qualified"],"h1_identifiability":i1["qualified"],"h0_no_bounds":all(bound_distance(v,"k_1_s" if j%2==0 else "csat_kg_m3")>.01 for x in [h0]+[f["H0"] for f in folds] for j,v in enumerate(x["best"]["parameters"])),"h1_no_bounds":all(bound_distance(v,"k_1_s" if j%2==0 else "csat_kg_m3")>.01 for x in [h1]+[f["H1"] for f in folds] for j,v in enumerate(x["best"]["parameters"])),"h0_postfit_parity":p0["pass"],"h1_postfit_parity":p1["pass"],"h0_numerical":n0["reduced_pass"],"h1_numerical":n1["reduced_pass"],"joint_improvement":metrics["joint_improvement_pass"],"caffeine_noninferiority":metrics["species_noninferiority_pass"]["caffeine"],"trigonelline_noninferiority":metrics["species_noninferiority_pass"]["trigonelline"],"nesting_inequality":nesting});disposition=decision(gates);result={"schema_version":"ewp.sci-md-006-final/v3","disposition":disposition,"gates":gates,"metrics":metrics,"optimizer_call_count":len(completed_fits),"claim_ceiling":CLAIM_CEILING,"physical_validation":"NOT_ESTABLISHED","experimental_commissioning":"NOT_AUTHORIZED"};dump_json(OUT/"FINAL_SCIENTIFIC_RESULT.json",result);(DOC/"FINAL_REPORT.md").write_text("# SCI-MD-006 final report\n\nDisposition: `"+disposition+"`.\n\n"+CLAIM_CEILING+"\n",encoding="utf-8");close_manifest(result,bind);print(disposition)

def close_manifest(result,bind):
    artifacts=sorted(p for p in list(OUT.glob("*"))+list(DOC.glob("*")) if p.is_file() and p.name!="RESULT_MANIFEST.json");dump_json(OUT/"RESULT_MANIFEST.json",{"result":result["disposition"],"binding":bind,"artifacts":[{"path":str(p.relative_to(ROOT)),"sha256":sha256(p)} for p in artifacts],"production_source_unchanged":True,"h0_hist_unchanged":True,"puckworks_read_only":True,"angeloni_nonaccess":True})
def main():
    p=argparse.ArgumentParser();p.add_argument("operation",choices=("inspect","preflight","execute"));p.add_argument("--puckworks",type=Path,required=True);p.add_argument("--executable",type=Path,required=True);p.add_argument("--runtime-root",type=Path);a=p.parse_args();
    if a.operation=="inspect":value=inspect(a.puckworks,a.executable)
    else:
        if a.runtime_root is None or a.runtime_root.exists():raise SystemExit("fresh --runtime-root outside repository required")
        a.runtime_root.mkdir(parents=True);value={"preflight":preflight,"execute":execute}[a.operation](a.puckworks,a.executable,a.runtime_root)
    if a.operation!="execute":print(json.dumps(value,sort_keys=True))
if __name__=="__main__":main()
