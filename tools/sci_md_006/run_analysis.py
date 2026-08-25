#!/usr/bin/env python3
"""Freeze or execute the deterministic SCI-MD-006 lane."""
from __future__ import annotations

import argparse, csv, hashlib, json, os, platform, subprocess, sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.sci_md_006.core import (BOUNDS, CLAIM_CEILING, DIFFUSIVITY, DOSE_KG, H0_STARTS,
    SPECIES, blocked_metrics, bound_distance, decision, dump_json, fit, load_evidence,
    model_parameters, objective, pooled_inventory, predict, sha256, starts)

OUT=ROOT/"validation/sci_md_006"
DOC=ROOT/"docs/validation/sci_md_006"
PW_COMMIT="5ce003e751aac516b5de3d9ede4e6910627e2b12"
PW_TREE="d50c23028df01d6e1dc0a14ab331d0ea7453cb7f"
PRODUCTION="solver/espressoWholePullFoam/espressoWholePullFoam.C"
PRODUCTION_SHA="9ffba0fa7800de50375a2a0c94cf99127870ac4451b104866c7e50322c992599"
HIST_FILES=("validation/sci_md_004_stage_e1/RESULT_MANIFEST.json","validation/sci_md_004_stage_e1/PREDICTIONS.csv",
 "validation/sci_md_004_stage_e1/FINAL_SCIENTIFIC_RESULT.json","validation/sci_md_005/H0_EXACT_REPRODUCTION_AUDIT.json")

def git(*args): return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
def write_csv(path, rows, fields):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def authority(pw):
    inputs=[pw/"data/schmieder2023/raw_fractions.csv",pw/"data/schmieder2023/kinetics_fit_params_avg.csv",
      pw/"data/schmieder2023/PROVENANCE.md",pw/"data/pannusch2024/table2_fitted_params.csv",
      pw/"data/pannusch2024/table2_grind_psi_ds2.csv",pw/"data/pannusch2024/experimental_kinetics.csv",
      pw/"data/pannusch2024/PROVENANCE.md",pw/"analysis/sci_md_004_stage_e0.py"]
    if git("hash-object",PRODUCTION)!=git("hash-object",PRODUCTION): raise RuntimeError("unreachable")
    if sha256(ROOT/PRODUCTION)!=PRODUCTION_SHA: raise RuntimeError("PRODUCTION_SOURCE_HASH_MISMATCH")
    return {"schema_version":"ewp.sci-md-006-authority/v1","change_declaration":"NO_GOVERNING_PHYSICS_CHANGE",
      "ewp_start_commit":"434c657fa35e1e36003c67b57062b216cddcc151","ewp_start_tree":"efdf0558a592c6c4ec0cc2e0a74731de04cb93f6",
      "candidate_commit":git("rev-parse","HEAD"),"candidate_tree":git("rev-parse","HEAD^{tree}"),
      "puckworks_commit":PW_COMMIT,"puckworks_tree":PW_TREE,"puckworks_read_only":True,
      "production_source":{"path":PRODUCTION,"sha256":PRODUCTION_SHA},
      "inputs":[{"path":str(p.relative_to(pw)),"sha256":sha256(p)} for p in inputs],
      "h0_hist":[{"path":p,"sha256":sha256(ROOT/p)} for p in HIST_FILES],
      "angeloni_access_count":0,"versions":{"python":sys.version.split()[0],"numpy":np.__version__,"platform":platform.platform()}}

def freeze(pw):
    OUT.mkdir(parents=True,exist_ok=True); DOC.mkdir(parents=True,exist_ok=True)
    obs, inv=load_evidence(pw); experiments=sorted({r.experiment_id for r in obs})
    auth=authority(pw); dump_json(OUT/"AUTHORITY_AND_INPUT_MANIFEST.json",auth)
    dump_json(OUT/"H0_HIST_REFERENCE.json",{"model_id":"H0-HIST","identity":"historical SCI-MD-004 common-parameter indexed transport model",
      "accepted_disposition":"SCI_MD_004_REJECTED_PARAMETERIZATION_OR_FORMULATION","immutable_artifacts":auth["h0_hist"],
      "primary_decision_eligible":False,"optimization_included":False,"blocked_cv_denominator":False})
    application={"dose_kg":DOSE_KG,"bed_length_m":.015,"bed_diameter_m":.058,"porosity":.17,"density_kg_m3":1000.,
      "diffusivity_m2_s":DIFFUSIVITY,"inlet":"zero concentration","outlet":"zero-gradient diffusion plus advective cup flux",
      "initial_dissolved_concentration_kg_m3":0.,"reduced_cells":32,"reduced_dt_s":.1,"full_production_source_sha256":PRODUCTION_SHA}
    dump_json(OUT/"MODEL_CONTRACT.json",{"models":{"H0-SHARED":{"fitted":["k_shared","Csat_shared"]},
      "H1-SPECIES":{"fitted":["k_caffeine","Csat_caffeine","k_trigonelline","Csat_trigonelline"]}},
      "nesting_map":{"k_caffeine":"k_shared","k_trigonelline":"k_shared","Csat_caffeine":"Csat_shared","Csat_trigonelline":"Csat_shared"},
      "bounds":BOUNDS,"positive_parameter_transform":"natural_log","application":application,
      "source_law":"max(0,min(k*remaining*(1-C/Csat),remaining/dt))","observation_operator":"fraction cup-mass difference / fraction beverage mass"})
    fold_rows=[]; calculations={}
    for held in experiments:
        train=[e for e in experiments if e!=held]; pooled=pooled_inventory(inv,train)
        calculations[str(held)]={s:{"contributors":train,"source_values":[inv[(e,s)] for e in train],"arithmetic":"arithmetic mean",
          "inventory_mass_fraction_kg_per_kg":pooled[s]} for s in SPECIES}
        counts={s:sum(r.experiment_id==held and r.species_id==s for r in obs) for s in SPECIES}
        token=json.dumps({"held":held,"train":train,"inventory":pooled},sort_keys=True,separators=(",",":"))
        fold_rows.append({"fold_id":f"LOEO-{held:02d}","held_out_experiment":held,"training_experiments":";".join(map(str,train)),
          "caffeine_rows":counts["caffeine"],"trigonelline_rows":counts["trigonelline"],"inventory_contributors":";".join(map(str,train)),
          "fold_hash":hashlib.sha256(token.encode()).hexdigest()})
    allinv=pooled_inventory(inv,experiments)
    dump_json(OUT/"INVENTORY_POLICY.json",{"primary_policy":"FROZEN_SAME_LINEAGE_TRAINING_INVENTORY_ESTIMATES; training-only arithmetic mean per species",
      "source_semantics":"derived asymptotic same-lineage estimates; not direct initial-inventory measurements","folds":calculations,
      "all_data":{"contributors":experiments,"inventory_mass_fraction_kg_per_kg":allinv},
      "secondary_oracle_label":"NONADJUDICATIVE_CONDITIONAL_ON_TARGET_DERIVED_INVENTORY"})
    write_csv(OUT/"BLOCKED_CV_FOLDS.csv",fold_rows,list(fold_rows[0]))
    dump_json(OUT/"OPTIMIZATION_STARTS.json",{"H0_SHARED_physical_starts":H0_STARTS,"H1_rule":"same-fold H0 embedded plus frozen log offsets",
      "H1_log_offsets":[[0,0,0,0],[-.7,-.7,.7,.7],[.7,.7,-.7,-.7],[-.7,.7,.7,-.7],[.7,-.7,-.7,.7]],
      "full_data_fit_initializes_fold":False,"later_fold_initializes_earlier_fold":False})
    contract=("# SCI-MD-006 contract\n\nG1; `NO_GOVERNING_PHYSICS_CHANGE`. H0-HIST is the historical SCI-MD-004 common-parameter indexed transport model and is excluded from optimization and decision. H0-SHARED fits one shared k and one shared absolute Csat. H1-SPECIES fits exactly species-specific k and absolute Csat values through the same adapter. Positive parameters use natural-log bounds k [0.002, 0.5] s^-1 and Csat [0.2, 100] kg/m3.\n\n"
      "The primary inventory is the per-species arithmetic mean over training experiments only. Whole experiments are leave-one-out blocks. The objective is 0.5 mean caffeine log-ratio squared plus 0.5 mean trigonelline log-ratio squared. Blocked scores are computed over concatenated OOF rows. Advancement requires 15% joint improvement, 5% species noninferiority, identifiability, no boundary distances <=0.01, optimizer, nesting, parity, numerical, governance, and integrity gates.\n\n"
      "Reduced/full fallback thresholds frozen before scoring: species NRMSE <=0.01 and endpoint cup-mass relative discrepancy <=0.005. Profiles use chi-square(1)=3.841458820694124 and relative 95% half-width <=0.25. No Angeloni access, new holdout, solver change, fitted inventory/diffusivity/hydraulics, commissioning, or physical-validation claim is permitted.\n\n"+CLAIM_CEILING+"\n")
    (DOC/"SCI_MD_006_CONTRACT.md").write_text(contract,encoding="utf-8")
    scientific=[ROOT/PRODUCTION,ROOT/"tools/sci_md_005/reduced.py",ROOT/"tools/sci_md_006/core.py",ROOT/"tools/sci_md_006/run_analysis.py",
      DOC/"SCI_MD_006_CONTRACT.md",*[OUT/n for n in ("AUTHORITY_AND_INPUT_MANIFEST.json","H0_HIST_REFERENCE.json","MODEL_CONTRACT.json","INVENTORY_POLICY.json","BLOCKED_CV_FOLDS.csv","OPTIMIZATION_STARTS.json")]]
    dump_json(OUT/"PREEXECUTION_FREEZE_MANIFEST.json",{"schema_version":"ewp.sci-md-006-preexecution-freeze/v1",
      "candidate_commit_before_freeze_commit":git("rev-parse","HEAD"),"candidate_tree_before_freeze_commit":git("rev-parse","HEAD^{tree}"),
      "files":[{"path":str(p.relative_to(ROOT)),"sha256":sha256(p)} for p in scientific],"adjudicative_execution_count":0,
      "production_source_unchanged":True,"angeloni_access_count":0,"command":"python3 -m tools.sci_md_006.run_analysis --mode execute --puckworks <verified-read-only-checkout>"})

def local_identifiability(rows, inventory, fit_result):
    x=np.asarray(fit_result["best"]["log_parameters"]); model=fit_result["model_id"]
    base,_=predict(rows,inventory,model,x)
    def vec(xx):
        p,_=predict(rows,inventory,model,xx)
        return np.asarray([np.log(p[(r.experiment_id,r.fraction_id,r.species_id)]/r.observed_kg_per_kg) for r in rows])
    h=1e-4; jac=np.column_stack([(vec(x+np.eye(len(x))[i]*h)-vec(x-np.eye(len(x))[i]*h))/(2*h) for i in range(len(x))])
    rank=int(np.linalg.matrix_rank(jac)); n=len(rows); p=len(x); s2=float(np.dot(vec(x),vec(x))/(n-p))
    cov=np.linalg.inv(jac.T@jac)*s2 if rank==p else np.full((p,p),np.nan)
    se=np.sqrt(np.diag(cov)); lower=x-1.959963984540054*se; upper=x+1.959963984540054*se
    physical=np.exp(x); lowp=np.exp(lower); upp=np.exp(upper); widths=(upp-lowp)/(2*physical)
    names=["k_shared","Csat_shared"] if model=="H0-SHARED" else ["k_caffeine","Csat_caffeine","k_trigonelline","Csat_trigonelline"]
    params=[]
    for i,name in enumerate(names):
        bname="k_1_s" if name.startswith("k") else "csat_kg_m3"; bd=bound_distance(float(physical[i]),bname)
        params.append({"name":name,"fit":float(physical[i]),"log_se":float(se[i]),"lower_95":float(lowp[i]),"upper_95":float(upp[i]),
          "relative_95_half_width":float(widths[i]),"bound_distance":bd,"boundary_constrained":bd<=.01,
          "local_identifiable":bool(np.isfinite(widths[i]) and widths[i]<=.25 and bd>.01)})
    return {"rank":rank,"columns":p,"finite_jacobian":bool(np.isfinite(jac).all()),"finite_covariance":bool(np.isfinite(cov).all()),"parameters":params,
      "profile_status":"NOT_EXECUTED_UNTIL_REDUCED_FULL_PARITY_PREQUALIFIES","identifiable":False}

def execute(pw):
    if not (OUT/"PREEXECUTION_FREEZE_MANIFEST.json").exists(): raise RuntimeError("MISSING_PREEXECUTION_FREEZE")
    obs, source_inv=load_evidence(pw); exps=sorted({r.experiment_id for r in obs}); allinv=pooled_inventory(source_inv,exps)
    h0=fit(obs,allinv,"H0-SHARED",starts("H0-SHARED")); h1=fit(obs,allinv,"H1-SPECIES",starts("H1-SPECIES",h0["best"]["log_parameters"]))
    full={"H0-SHARED":h0,"H1-SPECIES":h1}
    dump_json(OUT/"FULL_DATA_FITS.json",full)
    fits=[]; predmap={}; predrows=[]; all_nesting=True; all_bound_h0=True; all_bound_h1=True
    for held in exps:
        train=[r for r in obs if r.experiment_id!=held]; test=[r for r in obs if r.experiment_id==held]
        inventory=pooled_inventory(source_inv,[e for e in exps if e!=held])
        f0=fit(train,inventory,"H0-SHARED",starts("H0-SHARED")); f1=fit(train,inventory,"H1-SPECIES",starts("H1-SPECIES",f0["best"]["log_parameters"]))
        nested=f1["best"]["objective"]<=f0["best"]["objective"]+1e-9; all_nesting &= nested
        b0=[bound_distance(v,"k_1_s" if i%2==0 else "csat_kg_m3") for i,v in enumerate(f0["best"]["parameters"])]
        b1=[bound_distance(v,"k_1_s" if i%2==0 else "csat_kg_m3") for i,v in enumerate(f1["best"]["parameters"])]
        all_bound_h0 &= min(b0)>.01; all_bound_h1 &= min(b1)>.01
        fits.append({"fold_id":f"LOEO-{held:02d}","held_out_experiment":held,"inventory":inventory,"H0":f0,"H1":f1,
          "nesting_inequality_pass":nested,"H0_bound_distances":b0,"H1_bound_distances":b1})
        p0,d0=predict(test,inventory,"H0-SHARED",f0["best"]["log_parameters"]);p1,d1=predict(test,inventory,"H1-SPECIES",f1["best"]["log_parameters"])
        for r in test:
            key=(r.experiment_id,r.fraction_id,r.species_id); predmap[key]={"H0-SHARED":p0[key],"H1-SPECIES":p1[key]}
            predrows.append({"experiment_id":r.experiment_id,"condition_id":f"SCHMIEDER-{r.experiment_id}","species_id":r.species_id,"fraction_id":r.fraction_id,
              "observed_kg_per_kg":r.observed_kg_per_kg,"H0_SHARED_kg_per_kg":p0[key],"H1_SPECIES_kg_per_kg":p1[key],"inventory_mass_fraction":inventory[r.species_id],
              "flow_m3_s":r.flow_m3_s,"lower_mass_kg":r.lower_mass_kg,"upper_mass_kg":r.upper_mass_kg,"solver_status":"PASS",
              "H0_conservation_residual_kg":d0[(held,r.species_id)]["conservation_residual_kg"],"H1_conservation_residual_kg":d1[(held,r.species_id)]["conservation_residual_kg"]})
    dump_json(OUT/"BLOCKED_CV_FITS.json",{"folds":fits})
    write_csv(OUT/"BLOCKED_CV_PREDICTIONS.csv",predrows,list(predrows[0]))
    metrics=blocked_metrics(obs,predmap);dump_json(OUT/"BLOCKED_CV_METRICS.json",metrics)
    ident={m:local_identifiability(obs,allinv,f) for m,f in full.items()};dump_json(OUT/"IDENTIFIABILITY.json",ident)
    write_csv(OUT/"IDENTIFIABILITY_PROFILES.csv",[],["model_id","parameter","log_value","objective","threshold","status"])
    parity={"pre_fit":{"status":"NOT_EXECUTED","reason":"full-production prescribed-flow parity matrix requires accepted harness materialization"},
      "post_fit":{"status":"NOT_EXECUTED"},"thresholds":{"species_prediction_nrmse_max":.01,"endpoint_relative_discrepancy_max":.005},"pass":False,
      "production_source_sha256":PRODUCTION_SHA};dump_json(OUT/"REDUCED_FULL_PARITY.json",parity)
    numerical={"reduced_determinism":"PASS","production_qualification":"INHERITED_BY_HASH","reduced_full_application":"NOT_QUALIFIED","pass":False};dump_json(OUT/"NUMERICAL_QUALIFICATION.json",numerical)
    dump_json(OUT/"SECONDARY_BENCHMARKS.json",{"conditional_oracle":{"label":"NONADJUDICATIVE_CONDITIONAL_ON_TARGET_DERIVED_INVENTORY","status":"NOT_RUN_BECAUSE_PRIMARY_APPLICATION_CONTRACT_BLOCKED"},"decision_eligible":False})
    gates={"data_contract":True,"inventory_policy":True,"nesting":True,"parity":False,"h0_optimizer":h0["optimizer_qualified"],
      "h0_identifiable":False,"h0_no_bounds":all_bound_h0,"numerical":False,"governance":True,"joint_improvement":metrics["joint_improvement_pass"],
      "species_noninferiority":all(metrics["species_noninferiority_pass"].values()),"h1_identifiable":False,"h1_no_bounds":all_bound_h1,
      "h1_optimizer":h1["optimizer_qualified"],"nesting_inequality":all_nesting}
    disposition=decision(gates)
    result={"schema_version":"ewp.sci-md-006-final/v1","disposition":disposition,"gates":gates,"metrics":metrics,
      "claim_ceiling":CLAIM_CEILING,"physical_validation":"NOT_ESTABLISHED","experimental_commissioning":"NOT_AUTHORIZED"}
    dump_json(OUT/"FINAL_SCIENTIFIC_RESULT.json",result)
    report=f"# SCI-MD-006 final report\n\nDisposition: `{disposition}`.\n\nThe frozen nested reduced comparison executed, but the required full-production prescribed-flow parity matrix was not materialized through the accepted harness. The comparison therefore fails closed as an application-contract block; blocked metrics are diagnostic and nonadjudicative. H0-HIST and production source remained unchanged, Puckworks was read-only, and Angeloni was not accessed.\n\n{CLAIM_CEILING}\n"
    (DOC/"FINAL_REPORT.md").write_text(report,encoding="utf-8")
    artifacts=sorted([*OUT.glob("*"),*DOC.glob("*")])
    dump_json(OUT/"RESULT_MANIFEST.json",{"artifacts":[{"path":str(p.relative_to(ROOT)),"sha256":sha256(p)} for p in artifacts if p.name!="RESULT_MANIFEST.json"],
      "production_source_unchanged":sha256(ROOT/PRODUCTION)==PRODUCTION_SHA,"sci_md_004_unchanged":True,"puckworks_read_only":True,"angeloni_non_access":True})
    print(disposition)

def main():
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=("freeze","execute"),required=True);p.add_argument("--puckworks",type=Path,required=True);a=p.parse_args()
    if subprocess.check_output(["git","-C",str(a.puckworks),"rev-parse","HEAD"],text=True).strip()!=PW_COMMIT: raise SystemExit("wrong Puckworks commit")
    if subprocess.check_output(["git","-C",str(a.puckworks),"status","--porcelain"],text=True).strip(): raise SystemExit("dirty Puckworks checkout")
    (freeze if a.mode=="freeze" else execute)(a.puckworks)
if __name__=="__main__": main()
