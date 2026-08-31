#!/usr/bin/env python3
"""Deterministic grouped comparison for XSV-PANNUSCH-MULTIMODEL-001.

March observations are not opened until the calibration freeze is written and
hash-closed. Raw/source-derived rows stay in the external evidence directory.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, pathlib, sys
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

SEED=20260830
PRIMARY=["caffeine","trigonelline"]
FC=[f"p{i}" for i in range(1,7)]
MODELS=["BASELINE-POOL-ANALYTE","BASELINE-POOL-UNIVERSAL","BASELINE-NEAREST-CONDITION",
        "BASELINE-COMPOSITIONAL-RIDGE","MODEL-ONE-TIMESCALE","MODEL-TWO-TIMESCALE",
        "MODEL-SPECIES-PARTIAL-POOL"]

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def dump(p,x): pathlib.Path(p).parent.mkdir(parents=True,exist_ok=True); pathlib.Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
def simplex(x):
    x=np.maximum(np.asarray(x,float),0); s=x.sum(axis=-1,keepdims=True); return x/np.where(s>0,s,1)

def load_fit(src):
    f=pd.read_csv(src/"fit_fraction_replicates.csv")
    valid=f[f.validity.eq("VALID")].copy()
    valid["mass"]=valid.analyte_mass_mg
    valid["liquid"]=valid.fraction_liquid_g_or_ml
    valid["campaign"]="FIT"
    valid["shot"]=valid.shot_id
    valid["condition"]=valid.condition_id
    valid["analyte"]=valid.analyte.replace({"5CQA":"5-CQA"})
    kin=pd.read_csv(src/"experimental_kinetics.csv").groupby("exp",as_index=False).first()
    valid=valid.merge(kin[["exp","Temp_C","flow_mL_s","grind_setting"]],left_on="source_experiment_id",right_on="exp",how="left")
    valid["temperature"]=valid.Temp_C; valid["flow_start"]=valid.flow_mL_s; valid["flow_end"]=valid.flow_mL_s; valid["grind"]=valid.grind_setting
    valid["intervention"]="CONSTANT"
    return valid,f

def load_march(src):
    p=pd.read_csv(src/"prediction_fraction_replicates.csv")
    p=p[p.validity.eq("VALID")].copy(); p["mass"]=p.derived_analyte_mass_mg; p["liquid"]=p.fraction_liquid_g_or_ml
    p["campaign"]="MARCH"; p["shot"]=p.shot_id; p["condition"]=p.condition_id
    p["analyte"]=p.analyte.replace({"5CQA":"5-CQA"}); p["temperature"]=(p.temperature_start_C+p.temperature_end_C)/2
    p["flow_start"]=p.flow_start_mL_s; p["flow_end"]=p.flow_end_mL_s; p["flow_start"]=p.flow_start_mL_s
    p["grind"]=1.7; p["intervention"]=np.where(p.temperature_start_C.ne(p.temperature_end_C),"TEMPERATURE_RAMP",np.where(p.flow_start_mL_s.ne(p.flow_end_mL_s),"FLOW_RAMP","CONSTANT"))
    return p

def profiles(rows):
    keys=["campaign","condition","shot","physical_replicate_id","analyte"]
    out=[]
    for key,g in rows.groupby(keys,sort=True):
        g=g.sort_values("fraction_id")
        if len(g)!=6 or g.fraction_id.nunique()!=6 or (g.mass<0).any() or not np.isfinite(g.mass).all(): continue
        m=g.mass.to_numpy(float); liq=g.liquid.to_numpy(float); p=m/m.sum(); cum=np.cumsum(liq); mid=cum-liq/2; x=mid/cum[-1]
        r=dict(zip(keys,key)); r.update({FC[i]:p[i] for i in range(6)}); r.update({f"x{i+1}":x[i] for i in range(6)})
        r.update(temperature=float(g.temperature.iloc[0]),flow_start=float(g.flow_start.iloc[0]),flow_end=float(g.flow_end.iloc[0]),grind=float(g.grind.iloc[0]),intervention=str(g.intervention.iloc[0]),total_mass=float(m.sum()))
        out.append(r)
    return pd.DataFrame(out)

def feature_matrix(df,stats=None):
    ramp=(df.flow_end-df.flow_start).to_numpy(float); temp=df.temperature.to_numpy(float); meanf=((df.flow_start+df.flow_end)/2).to_numpy(float); grind=df.grind.to_numpy(float)
    X=np.c_[temp,meanf,df.flow_start,df.flow_end,ramp,grind,(df.intervention=="FLOW_RAMP").astype(float),(df.intervention=="TEMPERATURE_RAMP").astype(float)]
    if stats is None: stats=(X.mean(0),np.where(X.std(0)>0,X.std(0),1))
    return (X-stats[0])/stats[1],stats

def fit_ridge(X,Y,a): return np.linalg.solve(X.T@X+a*np.eye(X.shape[1]),X.T@Y)
def select_alpha(df,partial=False):
    alphas=[1e-4,1e-3,1e-2,.1,1,10]; scores=[]
    for a in alphas:
        es=[]
        for c in sorted(df.condition.unique()):
            tr=df[df.condition!=c]; te=df[df.condition==c]
            yh=predict_ridge(tr,te,a,partial); es.extend(np.sqrt(np.mean((yh-te[FC].to_numpy())**2,axis=1)))
        scores.append((np.mean(es),a))
    return min(scores)[1]

def predict_ridge(tr,te,a,partial=False):
    X,st=feature_matrix(tr); Z,_=feature_matrix(te,st)
    base=np.c_[np.ones(len(X)),X]
    test=np.c_[np.ones(len(Z)),Z]
    if partial:
        it=(tr.analyte=="trigonelline").to_numpy(float)[:,None]; ie=(te.analyte=="trigonelline").to_numpy(float)[:,None]
        base=np.c_[base,it,it*X]; test=np.c_[test,ie,ie*Z]
    else:
        # analyte-specific fits are represented by separate blocks
        out=np.zeros((len(te),6))
        for an in PRIMARY:
            q=tr.analyte.eq(an); z=te.analyte.eq(an)
            B=fit_ridge(base[q],np.sqrt(tr.loc[q,FC].to_numpy()),a); out[z]=simplex(np.maximum(test[z]@B,0)**2)
        return out
    B=fit_ridge(base,np.sqrt(tr[FC].to_numpy()),a); return simplex(np.maximum(test@B,0)**2)

def timescale(tr,te,two=False):
    out=[]
    for _,r in te.iterrows():
        g=tr[tr.analyte.eq(r.analyte)]; y=g[FC].mean().to_numpy(); xb=g[[f"x{i}" for i in range(1,7)]].mean().to_numpy(); cum=np.cumsum(y)
        if two:
            def fun(z):
                w=1/(1+np.exp(-z[0])); k1=np.exp(z[1]); k2=np.exp(z[2]); return w*(1-np.exp(-k1*xb))+(1-w)*(1-np.exp(-k2*xb))-cum
            z=least_squares(fun,[0,2,0],bounds=([-8,-14,-14],[8,5,5])).x; w=1/(1+np.exp(-z[0])); k1=max(np.exp(z[1]),np.exp(z[2])); k2=min(np.exp(z[1]),np.exp(z[2])); xx=r[[f"x{i}" for i in range(1,7)]].to_numpy(float); C=w*(1-np.exp(-k1*xx))+(1-w)*(1-np.exp(-k2*xx))
        else:
            z=least_squares(lambda q:1-np.exp(-np.exp(q[0])*xb)-cum,[1],bounds=([-14],[5])).x; xx=r[[f"x{i}" for i in range(1,7)]].to_numpy(float); C=1-np.exp(-np.exp(z[0])*xx)
        out.append(simplex(np.diff(np.r_[0,C])))
    return np.asarray(out)

def predict(model,tr,te,alpha=None):
    if model=="BASELINE-POOL-ANALYTE": return np.vstack([tr[tr.analyte.eq(a)][FC].mean().to_numpy() for a in te.analyte])
    if model=="BASELINE-POOL-UNIVERSAL": return np.tile(tr[FC].mean().to_numpy(),(len(te),1))
    if model=="BASELINE-NEAREST-CONDITION":
        X,st=feature_matrix(tr); Z,_=feature_matrix(te,st); cm=tr.assign(_i=range(len(tr))).groupby("condition").first(); cx,_=feature_matrix(cm.reset_index(),st); out=[]
        for i,r in te.reset_index(drop=True).iterrows():
            j=np.argmin(np.sum((cx-Z[i])**2,axis=1)); c=cm.index[j]; g=tr[(tr.condition==c)&(tr.analyte==r.analyte)]; out.append((g if len(g) else tr[tr.analyte==r.analyte])[FC].mean().to_numpy())
        return np.asarray(out)
    if model=="BASELINE-COMPOSITIONAL-RIDGE": return predict_ridge(tr,te,alpha or select_alpha(tr),False)
    if model=="MODEL-SPECIES-PARTIAL-POOL": return predict_ridge(tr,te,alpha or select_alpha(tr,True),True)
    if model=="MODEL-ONE-TIMESCALE": return timescale(tr,te,False)
    if model=="MODEL-TWO-TIMESCALE": return timescale(tr,te,True)
    raise KeyError(model)

def evaluate(model,tr,te,scheme,fold,alpha=None):
    yh=predict(model,tr,te,alpha); rows=[]
    for i,(_,r) in enumerate(te.reset_index(drop=True).iterrows()):
        y=r[FC].to_numpy(float); q=yh[i]; x=r[[f"x{k}" for k in range(1,7)]].to_numpy(float)
        row={"scheme":scheme,"fold":str(fold),"model_id":model,"campaign":r.campaign,"condition":r.condition,"shot":r.shot,"analyte":r.analyte,"grind":r.grind,"temperature":r.temperature,"flow_start":r.flow_start,"flow_end":r.flow_end,"intervention":r.intervention,"rmse":float(np.sqrt(np.mean((q-y)**2))),"hellinger":float(np.sqrt(np.sum((np.sqrt(q)-np.sqrt(y))**2))/math.sqrt(2)),"cumulative_rmse":float(np.sqrt(np.mean((np.cumsum(q)-np.cumsum(y))**2))),"early_residual":float(q[:2].sum()-y[:2].sum()),"tail_residual":float(q[-2:].sum()-y[-2:].sum()),"centroid_residual":float(np.dot(q-y,x))}
        for k in range(6): row.update({"fraction":k+1,"observed_share":float(y[k]),"predicted_share":float(q[k]),"residual":float(q[k]-y[k])}); rows.append(row.copy())
    return rows

def grouped(fit):
    rows=[]
    for model in MODELS:
        for scheme,key in [("LOSO","shot"),("LOCO","condition"),("LOGO","grind")]:
            for fold in sorted(fit[key].unique()):
                tr=fit[fit[key]!=fold]; te=fit[fit[key]==fold]
                if len(tr) and len(te): rows+=evaluate(model,tr,te,scheme,fold)
    return pd.DataFrame(rows)

def bootstrap(camp):
    rng=np.random.default_rng(SEED); shot=camp.groupby(["model_id","condition","shot","analyte"],as_index=False).rmse.first(); base=shot[shot.model_id.eq("BASELINE-POOL-ANALYTE")].rename(columns={"rmse":"base"})
    x=shot.merge(base[["condition","shot","analyte","base"]],on=["condition","shot","analyte"]); out=[]
    for m,g in x.groupby("model_id"):
        cond=g.groupby("condition").agg(err=("rmse","mean"),base=("base","mean")); dif=(cond.err-cond.base).to_numpy(); boots=[]
        for _ in range(2000): boots.append(float(rng.choice(dif,len(dif),replace=True).mean()))
        out.append({"model_id":m,"error":float(cond.err.mean()),"ci_low":float(np.quantile(boots,.025)+cond.base.mean()),"ci_high":float(np.quantile(boots,.975)+cond.base.mean()),"difference_vs_pool":float(dif.mean()),"difference_ci_low":float(np.quantile(boots,.025)),"difference_ci_high":float(np.quantile(boots,.975)),"relative_improvement":float(-dif.mean()/cond.base.mean()),"conditions_worse":int((dif>0).sum()),"n_conditions":len(cond)})
    return pd.DataFrame(out)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--source",type=pathlib.Path,required=True); ap.add_argument("--repo",type=pathlib.Path,required=True); ap.add_argument("--evidence",type=pathlib.Path,required=True); a=ap.parse_args()
    docs=a.repo/"docs/analysis/xsv_pannusch_multimodel_001"; ev=a.evidence
    fit_rows,all_fit=load_fit(a.source); fit_all=profiles(fit_rows); fit=fit_all[fit_all.analyte.isin(PRIMARY)].copy()
    assert all_fit.shot_id.nunique()==45 and fit.condition.nunique()==15
    spills=all_fit[all_fit.validity.ne("VALID")][["shot_id","fraction_id"]].drop_duplicates()
    assert len(spills)==3
    alphas={"ridge":select_alpha(fit),"partial":select_alpha(fit,True)}
    params={"ridge_alpha":alphas["ridge"],"partial_pool_alpha":alphas["partial"],"inventory_scales":[.01,.1,1.0],"models":MODELS}
    freeze={"schema_version":1,"task_id":"XSV-PANNUSCH-MULTIMODEL-001","methods_freeze_sha256":sha(docs/"METHODS_FREEZE.json"),"calibration_rows":len(fit),"calibration_conditions":15,"calibration_shots":45,"selected_hyperparameters":params,"model_ids":MODELS,"folds":{"LOSO":45,"LOCO":15,"LOGO":3},"march_conditions":["PRED-C01","PRED-C02","PRED-C03","PRED-C04","PRED-C05","PRED-C06","PRED-C07","PRED-C08"],"march_targets_loaded":False,"prediction_code_sha256":sha(__file__),"blocked_models":{"MODEL-EWP-FIXED":"BLOCKED_MODEL_CAPABILITY_NON_TARGET_GRIND_TO_EWP_MAPPING_ABSENT","MODEL-PANNUSCH-FIXED":"PENDING_PARITY_AND_EXECUTION"}}
    dump(docs/"CALIBRATION_FREEZE.json",freeze); (ev/"protocol").mkdir(parents=True,exist_ok=True); dump(ev/"protocol/CALIBRATION_FREEZE.json",freeze)
    grouped_df=grouped(fit); (ev/"folds").mkdir(parents=True,exist_ok=True); grouped_df.to_csv(ev/"folds/grouped_internal_full.csv",index=False)
    # The March file is opened only after both freeze copies exist and match.
    assert sha(docs/"CALIBRATION_FREEZE.json")==sha(ev/"protocol/CALIBRATION_FREEZE.json")
    march_rows=load_march(a.source); march_all=profiles(march_rows); march=march_all[march_all.analyte.isin(PRIMARY)].copy(); assert march.shot.nunique()==24 and march.condition.nunique()==8
    common=march[march.condition.isin(["PRED-C01","PRED-C02","PRED-C05","PRED-C06"])]
    extended=march[march.condition.isin(["PRED-C01","PRED-C02","PRED-C05","PRED-C06","PRED-C07","PRED-C08"])]
    camp=[]
    for model in MODELS:
        camp+=evaluate(model,fit,common,"MARCH_COMMON","frozen",alphas["partial"] if model=="MODEL-SPECIES-PARTIAL-POOL" else alphas["ridge"] if model=="BASELINE-COMPOSITIONAL-RIDGE" else None)
        camp+=evaluate(model,fit,extended,"MARCH_EXTENDED","frozen",alphas["partial"] if model=="MODEL-SPECIES-PARTIAL-POOL" else alphas["ridge"] if model=="BASELINE-COMPOSITIONAL-RIDGE" else None)
    camp=pd.DataFrame(camp); (ev/"predictions").mkdir(parents=True,exist_ok=True); camp.to_csv(ev/"predictions/campaign_predictions_full.csv",index=False)
    primary=bootstrap(camp[camp.scheme.eq("MARCH_COMMON")]); primary.to_csv(docs/"CAMPAIGN_SEPARATED_RESULTS.csv",index=False)
    gi=grouped_df.groupby(["scheme","model_id"],as_index=False).rmse.mean(); gi.to_csv(docs/"GROUPED_INTERNAL_RESULTS.csv",index=False)
    primary.to_csv(docs/"MODEL_COMPARISON_RESULTS.csv",index=False)
    # Inventory scale cancels exactly in normalized shares for implemented lanes; EWP is blocked.
    inv=pd.DataFrame([{"model_id":m,"inventory_scale":s,"primary_error":float(primary.set_index("model_id").loc[m,"error"]),"rank_invariant":True,"meaning":"multiplicative recovered-mass sensitivity; normalized shares invariant"} for m in MODELS for s in [.01,.1,1.0]])
    inv.to_csv(docs/"INVENTORY_SENSITIVITY.csv",index=False)
    species=primary[primary.model_id.isin(["BASELINE-POOL-UNIVERSAL","BASELINE-POOL-ANALYTE","MODEL-SPECIES-PARTIAL-POOL","BASELINE-COMPOSITIONAL-RIDGE"])].copy(); species["structure"]=[{"BASELINE-POOL-UNIVERSAL":"H0_UNIVERSAL","BASELINE-POOL-ANALYTE":"H2_ANALYTE_POOLED","MODEL-SPECIES-PARTIAL-POOL":"H3_PARTIAL_POOL","BASELINE-COMPOSITIONAL-RIDGE":"H4_INDEPENDENT_SPECIES"}[x] for x in species.model_id]; species.to_csv(docs/"SPECIES_MODEL_RESULTS.csv",index=False)
    reduced=camp[camp.scheme.eq("MARCH_EXTENDED")].groupby(["model_id","condition","analyte","fraction"],as_index=False).agg(residual=("residual","mean"),early_residual=("early_residual","mean"),tail_residual=("tail_residual","mean"),centroid_residual=("centroid_residual","mean")); reduced.to_csv(docs/"RESIDUAL_FINDINGS.csv",index=False); (ev/"residuals").mkdir(parents=True,exist_ok=True); camp.to_csv(ev/"residuals/residual_atlas_full.csv",index=False)
    profile={"conditions":23,"physical_shots":69,"fit_conditions":15,"fit_physical_shots":45,"march_conditions":8,"march_physical_shots":24,"fractions_per_shot":6,"valid_rows_by_variable":pd.concat([fit_rows,march_rows]).groupby("analyte").size().to_dict(),"invalid_spills_excluded":3,"primary_analytes":PRIMARY,"secondary_analytes":["5-CQA"],"aggregate_lane":["TDS"],"target_exposed":True,"independent_external_validation":False}
    dump(docs/"DATA_PROFILE.json",profile)
    result={"calibration_freeze_sha256":sha(docs/"CALIBRATION_FREEZE.json"),"methods_freeze_sha256":sha(docs/"METHODS_FREEZE.json"),"primary":primary.to_dict("records"),"grouped":gi.to_dict("records"),"data":profile,"alphas":alphas}
    dump(ev/"final/core_results.json",result); print(json.dumps(result,indent=2))
if __name__=="__main__": main()
