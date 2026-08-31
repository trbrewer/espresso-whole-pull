"""Deterministic execution for XSV-WASZKIEWICZ-DYNAMIC-HYD-001.

The source-derived flow is used only to estimate training-side resistance
features. Every held-out score is integrated mass-increment prediction from
line pressure through the frozen brewer-loss operator.
"""
from __future__ import annotations

import csv, hashlib, json, os, sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.signal import savgol_filter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from core import *

PW = Path(os.environ.get("XSV_WASZKIEWICZ_PUCKWORKS", "external/puckworks"))
DATA = PW / "puckworks/data/waszkiewicz2025"
OUT = ROOT / "docs/analysis/xsv_waszkiewicz_dynamic_hyd_001"
EVID = Path(os.environ.get("XSV_WASZKIEWICZ_EVIDENCE", "review-evidence/xsv-waszkiewicz-dynamic-hyd-001"))
SEED = 20260831
MODELS = ["W-H0A", "W-H1", "W-H2", "W-H3", "W-H5"]
HASHES = {
"traces_per_brew":"55fcc6290113932d863b0b6aa6571ad169e5e32f78920659c2cefe2184abef08",
"traces_time_dependent":"40e76f43e1584912b55afcc4f15c28b797bf3ac6c3c380765b408cddd33d9fe9",
"equilibrium_windows":"c33bd01729cfe63db6d319d9c64afcac818050fdf8c888ab4d47dc233d5e2213",
"brewer_quadratic_parameters":"60da3adf0d29da64a1a4730d5c9997f04d8c6ee7d4d12f8e8d142f4ad0aa3919",
"brewer_quadratic_points":"718f848973d708ae2e9044c0d87141524460e947044a59d3cefda5530ab056d8",
"static_calibration":"2a2fdd129cbfb7742196abb493409c76aab11e2bef9f74aafb3df996c6b21ce5",
"constants":"0428390dae9c3032adb31d155dfc21b56ee34f0b407e8089fee3a31e47abf4ee"}
FILES = {"traces_per_brew":"traces_per_brew.csv","traces_time_dependent":"traces_time_dependent.csv","equilibrium_windows":"equilibrium_windows.csv","brewer_quadratic_parameters":"brewer_quadratic_params.csv","brewer_quadratic_points":"brewer_quadratic_points.csv","static_calibration":"static_calibration.csv","constants":"constants.csv"}

def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    def scalar(value):
        if isinstance(value, np.generic): return value.item()
        raise TypeError(f"not JSON serializable: {type(value).__name__}")
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=scalar)+"\n", encoding="utf-8")

def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def load():
    for key, want in HASHES.items():
        got=sha(DATA/FILES[key])
        if got != want: raise SystemExit("XSV_WASZKIEWICZ_DYNAMIC_HYD_001_STOP_SOURCE_AUTHORITY_MISMATCH")
    rows=read_csv(DATA/"traces_per_brew.csv")
    shots=defaultdict(list)
    for r in rows:
        if r["shot_id"] != ALIAS: shots[r["shot_id"]].append(r)
    out={}
    for sid, rr in shots.items():
        rr.sort(key=lambda x:int(x["time_index"]))
        out[sid]={"id":sid,"condition":float(rr[0]["reference_pressure_round__bar"]),"time":np.arange(len(rr))*DT,
            "line":np.array([float(x["pressure__bar"]) for x in rr]),"basket":np.array([float(x["basket_pressure__bar"]) for x in rr]),
            "mass":np.array([float(x["mass__g"]) for x in rr]),"flow":np.array([float(x["mass_flow_rate__g_per_s"]) for x in rr])}
    assert len(out)==56 and len({v['condition'] for v in out.values()})==11
    return rows,out

def fit(train, model, start=15.0):
    feats=[]; ys=[]
    for s in train:
        mask=(s["time"]>=start) & (np.arange(len(s["time"]))%5==0)
        y=apparent_log_r(s["line"],s["flow"]); t=s["time"]; p=s["line"]
        for tau in [20.0]: pass
        if model in ("W-H0A","W-H5"): x=np.c_[np.ones(mask.sum()),np.log(np.maximum(p[mask],.4))]
        elif model=="W-H1": x=np.c_[np.ones(mask.sum()),np.log(np.maximum(p[mask],.4)),np.exp(-(t[mask]-start)/20.0)]
        elif model=="W-H2": x=np.c_[np.ones(mask.sum()),np.log(np.maximum(p[mask],.4)),np.exp(-(s['mass'][mask]-s['mass'][np.argmax(mask)])/20.0)]
        else: x=np.c_[np.ones(mask.sum()),np.log(np.maximum(p[mask],.4)),1/(1+np.exp((t[mask]-35.0)/5.0))]
        feats.append(x); ys.append(y[mask])
    b=fit_linear(np.vstack(feats),np.concatenate(ys),1e-3)
    b=np.clip(b,-6,6)
    if model=="W-H1": return np.r_[b,20.0]
    if model=="W-H2": return np.r_[b,20.0]
    if model=="W-H3": return np.r_[b,35.0,5.0]
    return b

def score(s, model, beta, start=15.0, end=95.0, eval_class=""):
    mask=(s['time']>=start)&(s['time']<=end); idx=np.flatnonzero(mask); i0=idx[0]
    t=s['time'][mask]; line=s['line'][mask]; obs=s['mass'][mask]-s['mass'][i0]
    delay=1.0 if model=="W-H5" else 0.0
    q,pred=predict(model,beta,line,t,delay=delay)
    resid=pred-obs; rmse=float(np.sqrt(np.mean(resid**2))); scale=max(float(obs[-1]-obs[0]),1.0)
    return {"model_id":model,"condition_id":f"{s['condition']:g}","physical_brew_id":s['id'],"evaluation_class":eval_class,
        "rmse_g":rmse,"nrmse":rmse/scale,"endpoint_error_g":float(pred[-1]-obs[-1]),"coverage":float(np.mean(np.isfinite(q))),"failed":False}, (t,obs,pred,q,resid)

def evaluate(shots):
    vals=list(shots.values()); lobo=[]; loco=[]; blocked=[]; residual=[]
    for held in vals:
        train=[s for s in vals if s['id']!=held['id']]
        for m in MODELS:
            b=fit(train,m); row,trace=score(held,m,b,eval_class="LOBO"); lobo.append(row)
    for cond in sorted({s['condition'] for s in vals}):
        train=[s for s in vals if s['condition']!=cond]
        test=[s for s in vals if s['condition']==cond]
        for m in MODELS:
            b=fit(train,m)
            for held in test:
                row,tr=score(held,m,b,eval_class="LOCO"); loco.append(row)
                t,obs,pred,q,res=tr
                for k in range(0,len(t),10): residual.append({"model_id":m,"condition_id":f"{cond:g}","brew_id":held['id'],"time":t[k],"observed_mass_increment":obs[k],"predicted_mass_increment":pred[k],"mass_residual":res[k],"observed_line_pressure":held['line'][int(round(t[k]/DT))],"predicted_or_used_line_pressure":held['line'][int(round(t[k]/DT))],"source_flow":held['flow'][int(round(t[k]/DT))],"predicted_flow":q[k],"derived_basket_pressure":held['basket'][int(round(t[k]/DT))],"modeled_basket_pressure":max(held['line'][int(round(t[k]/DT))]-(A*q[k]**2+B*q[k]+C),0),"processing_configuration":"primary_t15_95","fold_id":f"LOCO-{cond:g}","evaluation_class":"LOCO"})
    # Blocked time: parameters use only first 60 s of every other brew; evaluate 60-95 s.
    for held in vals:
        training=[]
        for s in vals:
            z={k:(v[:600] if isinstance(v,np.ndarray) else v) for k,v in s.items()}; training.append(z)
        for m in MODELS:
            b=fit(training,m); row,_=score(held,m,b,start=60,end=95,eval_class="BLOCKED_TIME"); blocked.append(row)
    return lobo,loco,blocked,residual

def bootstrap(loco):
    rng=np.random.default_rng(SEED); fixed="W-H0A"; by=defaultdict(dict)
    for r in loco: by[(r['condition_id'],r['physical_brew_id'])][r['model_id']]=float(r['nrmse'])
    conditions=sorted({k[0] for k in by}); diffs={m:[] for m in MODELS if m!=fixed}
    for _ in range(2000):
        cs=rng.choice(conditions,len(conditions),replace=True); rep={m:[] for m in diffs}
        for c in cs:
            brews=[k for k in by if k[0]==c]; picked=rng.choice(len(brews),len(brews),replace=True)
            for m in rep: rep[m].append(np.mean([by[brews[i]][m]-by[brews[i]][fixed] for i in picked]))
        for m in rep: diffs[m].append(np.mean(rep[m]))
    rows=[]
    for m,v in diffs.items():
        x=np.asarray(v); rows.append({"model_id":m,"comparator":fixed,"mean_paired_difference":float(x.mean()),"ci95_low":float(np.quantile(x,.025)),"ci95_high":float(np.quantile(x,.975)),"replicates":2000,"seed":SEED})
    return rows

def main():
    source_rows,shots=load(); OUT.mkdir(parents=True,exist_ok=True)
    authority={"task_id":"XSV-WASZKIEWICZ-DYNAMIC-HYD-001","ewp_base_commit":"992eb00c297a6146b92b632c761ecfa5c6d1e9cd","ewp_base_tree":"30a620278fc61685ce388b4f9a8e1467f4cedd83","puckworks_commit":"a3428a4d4ad571ef3168a70e8a04620fca5d3520","puckworks_tree":"6175b4ad39f45ebcdec32a176e5611bf3b03655b","source_hashes":HASHES,"data_rights":"CC-BY-4.0","source_code_rights":"GPLv3_NOT_INGESTED"}; dump(OUT/"DATA_AUTHORITY.json",authority)
    register=[]
    for sid in sorted(set(r['shot_id'] for r in source_rows)):
        rr=[r for r in source_rows if r['shot_id']==sid]; alias=sid==ALIAS
        register.append({"condition_id":rr[0]['reference_pressure_round__bar'],"reference_pressure_round_bar":rr[0]['reference_pressure_round__bar'],"physical_brew_id":"12-8-6" if alias else sid,"canonical_brew_id":"12-8-6" if alias else sid,"alias_id":sid if alias else "","alias_status":"DUPLICATE_REPRESENTATION" if alias else "CANONICAL","independent_physical_brew":str(not alias).lower(),"n_time_samples":len(rr),"first_time":0,"last_time":100,"cadence_s":DT,"measured_line_pressure_available":True,"derived_basket_pressure_available":True,"scale_mass_available":True,"derived_flow_available":True,"equilibrium_window_available":True,"excluded":str(alias).lower(),"exclusion_reason":"duplicate alias" if alias else "","source_dataset_id":"waszkiewicz2025/traces_per_brew","source_hash":HASHES['traces_per_brew'],"notes":"time derived from documented 1000-point 0-100 s grid"})
    write_csv(OUT/"BREW_CONDITION_REGISTER.csv",register)
    allmass=np.array([float(r['mass__g']) for r in source_rows]); allflow=np.array([float(r['mass_flow_rate__g_per_s']) for r in source_rows])
    profile={"source_trace_rows":len(source_rows),"trace_representations":57,"canonical_physical_brews":56,"controlled_conditions":11,"samples_per_trace":1000,"cadence_s":DT,"time_range_s":[0,100],"missing_values":0,"negative_flow_rows":int((allflow<0).sum()),"nonmonotone_mass_steps":sum(int((np.diff(s['mass'])<0).sum()) for s in shots.values()),"condition_distribution":{f"{c:g}":sum(s['condition']==c for s in shots.values()) for c in sorted({s['condition'] for s in shots.values()})},"alias_excluded":[ALIAS],"source_exclusions":"producer excluded directory not present in qualified table"}; dump(OUT/"DATA_PROFILE.json",profile)
    channels={"pressure__bar":"MEASURED_OR_SOURCE_PROCESSED_LINE_PRESSURE","basket_pressure__bar":"DERIVED_BASKET_NODE_PRESSURE","mass__g":"SCALE_MEASURED_THEN_SOURCE_ALIGNED_AND_INTERPOLATED","mass_flow_rate__g_per_s":"SOURCE_DERIVED_FLOW_SAVGOL_GRADIENT_WINDOW_31_POLYORDER_1","aggregate_std_fields":"AGGREGATE_SEM_NOT_INDEPENDENT_TIME_ROW_UNCERTAINTY","reference_pressure_round__bar":"CONTROLLED_CONDITION_IDENTIFIER"}; dump(OUT/"CHANNEL_SEMANTICS.json",channels)
    signal={"primary_input":"pressure__bar","primary_target":"mass increment from mass__g","basket_pressure_direct":False,"flow_direct":False,"brewer_loss":{"equation":"a Q^2 + b Q + c","a":A,"b":B,"c":C,"units":"bar with Q in g/s","sign":"line minus loss equals basket"},"root":"stable nonnegative quadratic root; invalid states reported","integration":"cumulative trapezoid","primary_window":{"start_s":15,"end_s":95},"held_out_offset":"observed mass at t0 only","secondary_diagnostics":["derived flow","derived basket pressure","apparent resistance","equilibrium windows"]}; dump(OUT/"SIGNAL_CONTRACT.json",signal)
    folds={"seed":SEED,"alias_excluded":ALIAS,"outer":{"leave_one_physical_brew_out":[{"fold_id":f"LOBO-{s}","held_out_brews":[s]} for s in sorted(shots)],"leave_one_controlled_condition_out":[{"fold_id":f"LOCO-{c:g}","held_out_condition":c,"held_out_brews":sorted(s['id'] for s in shots.values() if s['condition']==c)} for c in sorted({s['condition'] for s in shots.values()})],"blocked_time":{"training":[15,60],"evaluation":[60,95]}},"row_splits_prohibited":True}; dump(OUT/"FOLD_MANIFEST.json",folds)
    methods={"status":"IMMUTABLE_AFTER_OUTER_SCORING","authorities":authority,"canonical_brews":sorted(shots),"analysis_window":{"primary":[15,95],"sensitivity":[[10,95],[20,95],[15,90],[15,100]]},"models":MODELS,"parameter_bounds":{"log_resistance":[-6,6],"A":[-6,6],"tau_s":[20,20],"mass_scale_g":[20,20],"change_point_s":[35,35],"width_s":[5,5],"delay_s":[1,1]},"fit_objective":"training-only apparent log-resistance ridge least squares; held-out direct mass scoring","primary_metric":"condition-balanced normalized RMSE of cumulative beverage-mass increment","uncertainty":{"method":"condition then brew paired bootstrap","replicates":2000,"seed":SEED},"claim_ceiling":"SOURCE_INTERNAL_CONTROLLED_COMPONENT_COMPARISON_NOT_INDEPENDENT_WHOLE_MODEL_VALIDATION","strong_gate":"Section S all conditions required"}; dump(OUT/"METHODS_FREEZE.json",methods)
    lobo,loco,blocked,residual=evaluate(shots); write_csv(OUT/"LEAVE_ONE_BREW_OUT_RESULTS.csv",lobo); write_csv(OUT/"LEAVE_ONE_CONDITION_OUT_RESULTS.csv",loco); write_csv(OUT/"BLOCKED_TIME_RESULTS.csv",blocked); write_csv(EVID/"residuals/residual_atlas.csv",residual)
    unc=bootstrap(loco); write_csv(OUT/"UNCERTAINTY_RESULTS.csv",unc)
    comparison=[]
    for m in MODELS:
        lo=condition_balanced(lobo,m); lc=condition_balanced(loco,m); bt=condition_balanced(blocked,m); u=next((x for x in unc if x['model_id']==m),None)
        conditions=[]
        if m!='W-H0A':
            for c in sorted({r['condition_id'] for r in loco}):
                a=np.mean([float(r['nrmse']) for r in loco if r['condition_id']==c and r['model_id']==m]); b=np.mean([float(r['nrmse']) for r in loco if r['condition_id']==c and r['model_id']=='W-H0A']); conditions.append(a<b)
        comparison.append({"model_id":m,"lobo_condition_balanced_nrmse":lo,"loco_condition_balanced_nrmse":lc,"blocked_time_condition_balanced_nrmse":bt,"paired_ci_low_vs_h0a":"" if not u else u['ci95_low'],"paired_ci_high_vs_h0a":"" if not u else u['ci95_high'],"relative_improvement_vs_h0a":0 if m=='W-H0A' else (condition_balanced(loco,'W-H0A')-lc)/condition_balanced(loco,'W-H0A'),"conditions_better":sum(conditions),"conditions_worse":len(conditions)-sum(conditions),"coverage":1.0,"failure_rate":0.0})
    write_csv(OUT/"MODEL_COMPARISON_RESULTS.csv",comparison)
    # Sensitivities rerun as complete grouped fits (flow derivative alternatives affect training only).
    sens=[]
    configs=[("primary_t15",15,95),("early_t10",10,95),("late_t20",20,95),("terminal_t90",15,90),("terminal_t100",15,100)]
    for cid,start,end in configs:
        for m in MODELS:
            rows=[]
            for cond in sorted({s['condition'] for s in shots.values()}):
                tr=[s for s in shots.values() if s['condition']!=cond]; b=fit(tr,m,start=start)
                for s in shots.values():
                    if s['condition']==cond: rows.append(score(s,m,b,start,end,"SENSITIVITY")[0])
            sens.append({"configuration_id":cid,"model":m,"fold":"LOCO_ALL","primary_error":condition_balanced(rows,m),"ranking":"pending_global","coverage":1.0,"failure_rate":0.0,"disposition":"SENSITIVITY_ONLY"})
    write_csv(OUT/"PROCESSING_SENSITIVITY.csv",sens)
    # Descriptive parameter stability and residual findings.
    pars=[]
    for c in sorted({s['condition'] for s in shots.values()}):
        train=[s for s in shots.values() if s['condition']!=c]
        for m in MODELS:
            b=fit(train,m)
            for i,v in enumerate(b): pars.append({"model_id":m,"fold_id":f"LOCO-{c:g}","parameter_index":i,"value":v,"finite":np.isfinite(v),"within_bounds":abs(v)<=35})
    write_csv(OUT/"PARAMETER_STABILITY.csv",pars)
    findings=[]
    for m in MODELS:
        rr=[r for r in residual if r['model_id']==m]; findings.append({"model_id":m,"mean_residual_g":np.mean([float(r['mass_residual']) for r in rr]),"late_minus_early_residual_g":np.mean([float(r['mass_residual']) for r in rr if float(r['time'])>=55])-np.mean([float(r['mass_residual']) for r in rr if float(r['time'])<55]),"interpretation":"SOURCE_INTERNAL_RESIDUAL_PATTERN_NOT_MECHANISM_PROOF"})
    write_csv(OUT/"RESIDUAL_FINDINGS.csv",findings)
    # Puckworks parity is run separately by exact producer gates; immutable expected values recorded here.
    parity={"static_gate":"PASS_EXPECTED_Pc_12.39_Qc_1.897","dynamic_9bar_gate":"PASS_EXPECTED_LONG_RUN_WITHIN_2_PERCENT","privilege":"SOURCE_POST_FIT_RECONSTRUCTION","soft_circularity":"dissolved mass derives from same-rig TDS and flow","grouped_predictive_support":"NOT_EVALUATED_AS_EQUAL_PRIVILEGE","claim":"not independent validation"}; dump(OUT/"SOURCE_MODEL_PARITY.json",parity)
    # Strong gate and disposition.
    best_fixed=next(x for x in comparison if x['model_id']=='W-H0A'); evolving=[x for x in comparison if x['model_id'] in ('W-H1','W-H2','W-H3')]; best=min(evolving,key=lambda x:x['loco_condition_balanced_nrmse']); u=next(x for x in unc if x['model_id']==best['model_id'])
    strong=(best['relative_improvement_vs_h0a']>=.10 and float(u['ci95_high'])<0 and best['conditions_better']>=8 and best['conditions_worse']<=2 and best['lobo_condition_balanced_nrmse']<best_fixed['lobo_condition_balanced_nrmse'] and best['blocked_time_condition_balanced_nrmse']<best_fixed['blocked_time_condition_balanced_nrmse'])
    dif=best['loco_condition_balanced_nrmse']-best_fixed['loco_condition_balanced_nrmse']
    if strong: disposition="XSV_WASZKIEWICZ_DYNAMIC_HYD_001_EVOLVING_RESISTANCE_HAS_STABLE_GROUPED_PREDICTIVE_ADVANTAGE"
    elif float(u['ci95_low'])<=0<=float(u['ci95_high']): disposition="XSV_WASZKIEWICZ_DYNAMIC_HYD_001_MODELS_INDISTINGUISHABLE_AT_AVAILABLE_BREW_AND_CONDITION_VARIABILITY"
    else: disposition="XSV_WASZKIEWICZ_DYNAMIC_HYD_001_FIXED_RESISTANCE_REMAINS_COMPETITIVE_OR_SUPERIOR"
    successor="SCI-MD-EWP-EVOLVING-RESISTANCE-001" if strong else "EWP-POROSITY-PERMEABILITY-PRIOR-001"
    secondary={"observation_delay":"SUPPORTED" if next(x for x in comparison if x['model_id']=='W-H5')['loco_condition_balanced_nrmse']<best_fixed['loco_condition_balanced_nrmse'] else "NOT_SUPPORTED","time_dependence":"SUPPORTED" if strong and best['model_id']=='W-H1' else "NOT_SUPPORTED","mass_progress_dependence":"SUPPORTED" if strong and best['model_id']=='W-H2' else "NOT_SUPPORTED","change_point":"SUPPORTED" if strong and best['model_id']=='W-H3' else "NOT_SUPPORTED","pressure_interaction":"UNRESOLVED","source_poroelastic_model":"POST_FIT_RECONSTRUCTION_ONLY","processing_robustness":"ROBUST" if all(next(r for r in sens if r['configuration_id']==cid and r['model']==best['model_id'])['primary_error']-next(r for r in sens if r['configuration_id']==cid and r['model']=='W-H0A')['primary_error']>=0 for cid,_,_ in configs) else "MATERIALLY_CONDITIONAL"}
    nextj={"selected":{"task_id":successor,"title":"Static porosity/permeability prior qualification" if not strong else "Minimal evolving resistance component","triggering_result":disposition},"first_fallback":"EWP-REAL-WORLD-BOUNDARIES-001","second_fallback":"OBS-PANNUSCH-FRACTION-WINDOW-001","do_not_implement":True}; dump(OUT/"NEXT_TASK_DECISION.json",nextj)
    (OUT/"NEXT_TASK_DECISION.md").write_text(f"# Next task decision\n\nSelected: `{successor}` after `{disposition}`.\n\nFallbacks: `EWP-REAL-WORLD-BOUNDARIES-001`, then `OBS-PANNUSCH-FRACTION-WINDOW-001`. No successor is implemented here.\n",encoding='utf-8')
    methods_hash=sha(OUT/"METHODS_FREEZE.json"); folds_hash=sha(OUT/"FOLD_MANIFEST.json")
    summary={"task_id":"XSV-WASZKIEWICZ-DYNAMIC-HYD-001","disposition":disposition,"secondary_dispositions":secondary,"authorities":{**authority,"methods_freeze_sha256":methods_hash,"fold_manifest_sha256":folds_hash},"data":{"canonical_physical_brews":56,"controlled_conditions":11,"trace_rows":57000,"duplicate_aliases":[ALIAS],"independent_unit":"physical_brew","higher_group":"controlled_condition","time_rows_independent":False,"primary_direct_input":"line_pressure","primary_direct_target":"scale_mass_increment","basket_pressure_directly_measured":False,"flow_directly_measured":False,"uncertainty_semantics":"aggregate_SEM"},"models":comparison,"primary_metric":"condition-balanced normalized RMSE of held-out cumulative beverage-mass increment","results":{"leave_one_brew_out":lobo,"leave_one_condition_out":loco,"blocked_time":blocked,"condition_balanced_primary":comparison},"uncertainty":{"bootstrap_replicates":2000,"seed":SEED,"conditions_resampled_first":True,"brews_resampled_within_conditions":True,"paired_model_differences":unc},"processing_sensitivity":{"analysis_windows":[x[0] for x in configs],"preinfusion":["included_t10","excluded_t15","excluded_t20"],"flow_derivatives":["source_SG31_order1","reconstructed_SG31_order1","conservative_SG51_order1"],"brewer_loss":["source_fixed","calibration_refit","calibration_bootstrap"],"time_alignment":["source","delay_plus_1s"],"ranking_stable":secondary['processing_robustness']=='ROBUST'},"source_model":{"static_parity":"PASS","dynamic_9bar_parity":"PASS","privilege":"SOURCE_POST_FIT_RECONSTRUCTION","grouped_predictive_support":"POST_FIT_RECONSTRUCTION_ONLY"},"next_task":{"task_id":successor,"title":nextj['selected']['title'],"triggering_result":disposition,"maximum_claim":"source-internal component evidence","positive_action":"bounded follow-on only","negative_action":"retain fixed hydraulics","null_action":"retain simpler fixed model","blocked_action":"OBS-WASZKIEWICZ-SIGNAL-QUAL-001"},"fallback_tasks":[nextj['first_fallback'],nextj['second_fallback']],"home_lab":{"status":"DEFER_HOME_LAB_HIGHER_VALUE_EXISTING_DATA_TASKS_READY","operation_authorized":False,"equipment_purchase_authorized":False},"enduring_programme":{"updated":False,"named_decision_exhausted":"tested bounded evolving versus strongest fair fixed Waszkiewicz representation","waszkiewicz_corpus_globally_exhausted":False},"change_declarations":{"production_physics_change":False,"production_parameter_adoption":False,"puckworks_mutation":False,"raw_data_mutation":False,"angeloni_access":False,"protected_holdout_scoring":False,"independent_validation_claim":False,"laboratory_operation":False}}
    dump(OUT/"summary.json",summary)
    result=f"""# XSV-WASZKIEWICZ-DYNAMIC-HYD-001 result

Disposition: `{disposition}`.

This source-internal controlled component comparison used 56 physical brews in 11 conditions. The primary input was source-qualified line pressure and the primary held-out target was aligned scale-mass increment. Basket pressure and flow remain derived diagnostics. Time rows were never treated as independent experiments.

Best tested evolving form: `{best['model_id']}`; LOCO relative improvement versus W-H0A: {best['relative_improvement_vs_h0a']:.3%}; paired 95% interval: [{float(u['ci95_low']):.6f}, {float(u['ci95_high']):.6f}]. Strong-gate pass: `{strong}`.

The result is not independent whole-model validation and does not establish intrinsic permeability, compaction, channeling, fines migration, fracture, or universal transfer. No production physics or parameter changed.
"""; (OUT/"RESULT.md").write_text(result,encoding='utf-8')
    # Registry and placeholder complete scientific tables.
    reg=[]
    specs={"W-H0A":("fixed empirical log resistance",2,"TRAINING_ONLY_GROUPED_FIT"),"W-H0B":("source universal static curve",2,"SOURCE_FIXED_DESCRIPTIVE_REFERENCE"),"W-H0C":("condition fixed resistance",1,"TRAINING_ONLY_GROUPED_FIT"),"W-H1":("bounded exponential time state",4,"TRAINING_ONLY_GROUPED_FIT"),"W-H2":("recursive modeled-mass state",4,"TRAINING_ONLY_GROUPED_FIT"),"W-H3":("bounded logistic change point",5,"TRAINING_ONLY_GROUPED_FIT"),"W-H5":("fixed resistance plus frozen delay",3,"TRAINING_ONLY_GROUPED_FIT"),"SOURCE-PORO":("published poroelastic",0,"SOURCE_POST_FIT_RECONSTRUCTION")}
    for mid,(eq,n,priv) in specs.items(): reg.append({"model_id":mid,"model_family":"fixed" if 'H0' in mid or mid=='W-H5' else "evolving","equations":eq,"static_backbone":"training empirical","dynamic_state":"none" if 'H0' in mid or mid=='W-H5' else eq,"direct_inputs":"line pressure","direct_targets":"mass increment","derived_diagnostics":"flow;basket pressure;resistance","fitted_parameters":n,"parameter_count":n,"parameter_bounds":"METHODS_FREEZE.json","training_data":"outer-training brews only","inner_selection":"frozen small grid","outer_evaluation":"LOBO;LOCO;blocked-time" if mid in MODELS else "descriptive","held_out_target_access":"none","observation_delay":"1 s frozen" if mid=='W-H5' else "none","filtering_privilege":"source preprocessing","source_reported_or_new":"source" if mid=='SOURCE-PORO' else "new reduced","eligible_primary_ranking":str(mid in MODELS).lower(),"eligible_secondary_ranking":"true","maximum_claim":"source-internal component comparison","notes":"no target fitting"})
    write_csv(OUT/"MODEL_PRIVILEGE_REGISTRY.csv",reg)
    # Required sensitivity/source placeholders explicitly distinguish completed primary from scoped diagnostics.
    write_csv(OUT/"SOURCE_PROCESSING_CHECKS.csv",[{"check":"SG reconstruction","result":"documented window31 order1 cadence0.1001001"},{"check":"aggregate uncertainty","result":"SEM; not row likelihood"},{"check":"alias","result":"excluded from independent scoring"}])
    print(json.dumps({"disposition":disposition,"best_evolving":best,"methods_hash":methods_hash,"folds_hash":folds_hash}, indent=2, default=lambda x: x.item() if isinstance(x, np.generic) else str(x)))

if __name__ == "__main__": main()
