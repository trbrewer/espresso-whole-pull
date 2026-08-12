#!/usr/bin/env python3
"""Deterministic compact reduction and figures for XSV-ENS-001."""
from pathlib import Path
import argparse, csv, glob, hashlib, json, math
import numpy as np
import pandas as pd

CASE=Path(__file__).resolve().parent
TARGETS=(0.373506,0.389226,0.395294)
BOOT_SEED=20260812

def dump(p,v): Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+"\n")
def ci(values,stat=lambda x:np.mean(x),n=10000,seed=BOOT_SEED):
    x=np.asarray(values,float); rng=np.random.default_rng(seed); z=np.array([stat(x[rng.integers(0,len(x),len(x))]) for _ in range(n)])
    return [float(np.quantile(z,.025)),float(np.quantile(z,.975))]
def flatten(r):
    state=json.loads(r["state"]); keys=["case_id","geometry_id","family","L","voxel_um","seed","relation","parent_id","direction","force","precision","purpose","status","geometry_sha256","K_gross_lu2","K_void_lu2","q_box_lu","phi_gross","phi_connected_x","phi_connected_y","phi_connected_z","solid_fraction","specific_interfacial_area_lu","pore_distance_q10","pore_distance_q50","pore_distance_q90","euler_characteristic","velocity_cv","flux_gini","top_10_flow_share","top_25_flow_share","normalized_flow_entropy","Mach","steps","wall_seconds"]
    d={k:r.get(k) for k in keys}; d.update({"state_phis":state.get("phis"),"state_amp":state.get("amp",0),"state_hlen":state.get("hlen",8),"restriction_fraction":state.get("restriction",0)})
    return d
def geom_mean(x): return float(np.exp(np.mean(np.log(np.asarray(x,float)))))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--evidence",required=True); a=ap.parse_args(); root=Path(a.evidence)
    raw=[json.loads(Path(p).read_text()) for p in sorted(glob.glob(str(root/"runs/*/result.json")))]; rows=[flatten(r) for r in raw]; df=pd.DataFrame(rows)
    df.to_csv(CASE/"XSV_ENS_001_REALIZATION_RESULTS.csv",index=False)
    geom=df.drop_duplicates("geometry_id")[["geometry_id","family","L","voxel_um","seed","relation","parent_id","geometry_sha256","phi_gross","phi_connected_x","phi_connected_y","phi_connected_z","solid_fraction","specific_interfacial_area_lu","pore_distance_q10","pore_distance_q50","pore_distance_q90","euler_characteristic","state_phis","state_amp","state_hlen","restriction_fraction"]]
    geom.to_csv(CASE/"XSV_ENS_001_GEOMETRY_MANIFEST.csv",index=False)
    df[["case_id","geometry_id","status","direction","force","precision","steps","wall_seconds","Mach"]].to_csv(CASE/"XSV_ENS_001_RUN_MANIFEST.csv",index=False)
    passed=df[df.status=="PASS"].copy(); desc=passed[["case_id","geometry_id","family","direction","phi_gross","phi_connected_x","phi_connected_y","phi_connected_z","specific_interfacial_area_lu","pore_distance_q10","pore_distance_q50","pore_distance_q90","euler_characteristic","velocity_cv","flux_gini","top_10_flow_share","top_25_flow_share","normalized_flow_entropy"]]
    desc.to_csv(CASE/"XSV_ENS_001_DESCRIPTOR_RESULTS.csv",index=False)
    dirs=[]
    for gid,g in passed[passed.family=="DIRECTIONAL"].groupby("geometry_id"):
      z={r.direction:r for _,r in g.iterrows()}
      if set(z)==set("XYZ"):
       kp=(z['Y'].K_gross_lu2+z['Z'].K_gross_lu2)/2
       dirs.append({"geometry_id":gid,"Kx":z['X'].K_gross_lu2,"Ky":z['Y'].K_gross_lu2,"Kz":z['Z'].K_gross_lu2,"Kperp":kp,"Kperp_over_Kx":kp/z['X'].K_gross_lu2,"Ky_over_Kx":z['Y'].K_gross_lu2/z['X'].K_gross_lu2,"Kz_over_Kx":z['Z'].K_gross_lu2/z['X'].K_gross_lu2,"state":gid.split('-')[1]})
    ddf=pd.DataFrame(dirs); ddf.to_csv(CASE/"XSV_ENS_001_DIRECTIONAL_RESULTS.csv",index=False)
    base=passed[(passed.family=="BASELINE")&(passed.direction=="X")]
    size=[]
    for L,g in base.groupby("L"):
      k=g.K_gross_lu2.to_numpy(); size.append({"L":int(L),"n":len(k),"mean_K":float(k.mean()),"median_K":float(np.median(k)),"sd_K":float(k.std(ddof=1)),"cv_K":float(k.std(ddof=1)/k.mean()),"mean_K_ci_low":ci(k)[0],"mean_K_ci_high":ci(k)[1],"q10":float(np.quantile(k,.1)),"q90":float(np.quantile(k,.9))})
    largest=max(x["L"] for x in size); ref=next(x for x in size if x["L"]==largest)
    for x in size: x["mean_ratio_to_largest"]=x["mean_K"]/ref["mean_K"]
    resolution="SPATIAL_RESOLUTION_PREVENTS_REV_ADJUDICATION"
    rev={"schema_version":"espresso.whole_pull.xsv_ens_001.rev.v1","size_statistics":size,"largest_L":largest,"characteristic_diameter_voxels":20.0,"largest_L_over_d":largest/20,"spatial_discretization":resolution,"mean_disposition":"NO_SYNTHETIC_GENERATOR_REV_RESOLVED","variance_disposition":"SYNTHETIC_GENERATOR_VARIANCE_NOT_STABILIZED","compute_disposition":"GPU_DOMAIN_LIMIT_PREVENTS_REV_ADJUDICATION","real_puck":"REAL_PUCK_REV_NOT_ASSESSED"}; dump(CASE/"XSV_ENS_001_REV_ASSESSMENT.json",rev)
    pairs=[]
    restr=passed[(passed.family=="THROAT_RESTRICTION")&(passed.direction=="X")]
    for seed,g in restr.groupby("seed"):
      refg=g[g.restriction_fraction==0]
      if len(refg)!=1: continue
      for _,r in g[g.restriction_fraction>0].iterrows(): pairs.append({"seed":int(seed),"restriction_fraction":r.restriction_fraction,"ratio":r.K_gross_lu2/refg.iloc[0].K_gross_lu2,"connected_retention":r.phi_connected_x/refg.iloc[0].phi_connected_x,"through":True})
    assess=[]
    for f,g in pd.DataFrame(pairs).groupby("restriction_fraction"):
      ratios=g.ratio.to_numpy(); logci=ci(np.log(ratios)); c=[math.exp(v) for v in logci]; majority={str(t):float(np.mean(ratios<=t)) for t in TARGETS}; robust=c[1]<=TARGETS[0] and majority[str(TARGETS[0])]>=.75
      topo=float(g.connected_retention.min())<.25
      disp="ROBUST_TARGET_ATTAINMENT_WITHOUT_TOPOLOGY_LOSS" if robust and not topo else ("TARGET_ATTAINMENT_IN_SOME_REALIZATIONS_ONLY" if np.any(ratios<=TARGETS[0]) else "TARGET_ATTAINMENT_NOT_REACHED")
      assess.append({"restriction_fraction":float(f),"n_converged_pairs":len(g),"geometric_mean_ratio":geom_mean(ratios),"bootstrap_95_ci":c,"fraction_attaining":majority,"minimum_connected_porosity_retention":float(g.connected_retention.min()),"disposition":disp})
    target={"schema_version":"espresso.whole_pull.xsv_ens_001.target.v1","exact_targets":{"terminal":TARGETS[0],"middle":TARGETS[1],"late":TARGETS[2]},"paired_restriction":assess,"classification":"STATIC_STATE_CAPABLE_DYNAMIC_CAUSE_UNIDENTIFIED","nonconvergence_qualification":"TEN_FROZEN_IDENTITIES_NONCONVERGED_AND_NOT_REPLACED"}; dump(CASE/"XSV_ENS_001_TARGET_ASSESSMENT.json",target)
    # Grouped closure comparison, one X-flow row per geometry.
    from sklearn.compose import TransformedTargetRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.model_selection import GroupKFold, cross_val_predict
    from sklearn.metrics import r2_score, mean_squared_error
    x=passed[passed.direction=="X"].drop_duplicates("geometry_id").copy(); y=np.log(x.K_gross_lu2.to_numpy()); groups=x.geometry_id.to_numpy(); folds=min(5,len(x)); cv=GroupKFold(folds)
    models={"A_porosity_only":["phi_gross","state_phis"],"B_porosity_topology":["phi_gross","state_phis","phi_connected_x","specific_interfacial_area_lu","pore_distance_q10","pore_distance_q50","euler_characteristic"],"C_topology_fabric_state":["phi_gross","state_phis","phi_connected_x","specific_interfacial_area_lu","pore_distance_q10","pore_distance_q50","euler_characteristic","state_amp","state_hlen","restriction_fraction"]}
    scores=[]
    for name,features in models.items():
      pred=cross_val_predict(make_pipeline(SimpleImputer(),Ridge(alpha=1.0)),x[features],y,groups=groups,cv=cv); resid=y-pred
      scores.append({"model":name,"features":features,"grouped_cv_R2_logK":float(r2_score(y,pred)),"grouped_cv_RMSE_logK":float(mean_squared_error(y,pred)**.5),"residual_sd_logK":float(np.std(resid,ddof=1)),"nominal_95_predictive_factor":float(np.exp(1.96*np.std(resid,ddof=1)))})
    best=max(scores,key=lambda q:q["grouped_cv_R2_logK"])
    closure={"schema_version":"espresso.whole_pull.xsv_ens_001.closure.v1","models":scores,"recommended_model":best["model"],"uncertainty_treatment":"LOGNORMAL_CONDITIONAL_DISTRIBUTION_WITH_RESIDUAL_REALIZATION_VARIANCE","deterministic_single_K_defensible":False,"interpolation_domain":{"phi_gross":[float(x.phi_gross.min()),float(x.phi_gross.max())],"heterogeneity_amplitude":[0,2],"restriction_fraction":[0,.4]},"prohibited_extrapolation":["REAL_COFFEE_MICROSTRUCTURE","DYNAMIC_PRESSURE_CAUSATION","SUBVOXEL_FINES"],"continuum_integration":"NO_NEW_PRODUCTION_PHYSICS_YET"}; dump(CASE/"XSV_ENS_001_CLOSURE_RECOMMENDATION.json",closure)
    iraw=[json.loads(Path(p).read_text()) for p in sorted(glob.glob(str(root/"inertial/*/result.json")))]; ifits=[]
    for parent in sorted({r["parent_case_id"] for r in iraw}):
      z=sorted([r for r in iraw if r["parent_case_id"]==parent and r["status"]=="PASS"],key=lambda r:r["force"])
      if len(z)<4: continue
      q=np.array([r["q_box_lu"] for r in z]); gg=np.array([r["force"] for r in z]); X=np.c_[q,q*np.abs(q)]; coef=np.linalg.lstsq(X,gg,rcond=None)[0]; pred=X@coef; r2=1-float(np.sum((gg-pred)**2)/np.sum((gg-gg.mean())**2))
      deleted=[]
      for j in range(len(z)):
       c=np.linalg.lstsq(np.delete(X,j,0),np.delete(gg,j),rcond=None)[0]; deleted.append(float(c[1]))
      stable=max(deleted)-min(deleted)<=max(abs(float(coef[1]))*.25,1e-12)
      ifits.append({"parent_case_id":parent,"n_pass":len(z),"linear_a":float(coef[0]),"quadratic_b":float(coef[1]),"R2":r2,"max_Mach":max(r["Mach"] for r in z),"deletion_b_min":min(deleted),"deletion_b_max":max(deleted),"deletion_stable_25pct":stable,"disposition":"INERTIAL_CURVATURE_RESOLVED" if coef[1]>0 and stable else "INERTIAL_CURVATURE_NOT_RESOLVED_WITHIN_QUALIFIED_FORCE_RANGE"})
    pd.DataFrame(ifits).to_csv(CASE/"XSV_ENS_001_INERTIAL_RESULTS.csv",index=False)
    inertial_disposition="INERTIAL_CURVATURE_RESOLVED" if ifits and all(x["disposition"]=="INERTIAL_CURVATURE_RESOLVED" for x in ifits) else "INERTIAL_CURVATURE_NOT_RESOLVED_WITHIN_QUALIFIED_FORCE_RANGE"
    result={"schema_version":"espresso.whole_pull.xsv_ens_001.result.v1","run_counts":df.status.value_counts().to_dict(),"inertial_run_counts":pd.Series([r['status'] for r in iraw]).value_counts().to_dict(),"total_run_identities":len(df)+len(iraw),"primary_run_identities":len(df),"secondary_inertial_run_identities":len(iraw),"total_gpu_seconds":float(pd.to_numeric(df.wall_seconds,errors='coerce').sum()+sum(r.get('wall_seconds',0) for r in iraw)),"baseline_realization_cv_by_size":{str(s['L']):s['cv_K'] for s in size},"rev":rev,"target":target,"directional":{"n_complete":len(ddf),"Kperp_over_Kx_median":float(ddf.Kperp_over_Kx.median()),"Kperp_over_Kx_range":[float(ddf.Kperp_over_Kx.min()),float(ddf.Kperp_over_Kx.max())]},"inertial":inertial_disposition,"inertial_fits":ifits,"closure":closure,"bimodal":"RESOLVED_BIMODAL_ARM_NOT_EXECUTED_RESOLUTION_LIMIT","spatial_resolution":"NOT_FULLY_ADJUDICATED","next_programme":"REAL_GEOMETRY_IMPORT_AND_MICROCT_COMPARISON","claim_boundary":{"physical_validation":"NOT_ESTABLISHED","real_coffee_representative_volume":"NOT_ESTABLISHED","dynamic_pressure_mechanism":"NOT_IDENTIFIED"}}; dump(CASE/"XSV_ENS_001_RESULT.json",result)
    # Review-purpose plot-source table.
    plot=passed.copy(); plot.to_csv(CASE/"XSV_ENS_001_PLOT_SOURCE.csv",index=False)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    P=CASE/"plots"; P.mkdir(exist_ok=True)
    def save(name,xlabel,ylabel): plt.xlabel(xlabel); plt.ylabel(ylabel); plt.tight_layout(); plt.savefig(P/name); plt.close()
    for L,g in base.groupby('L'): plt.scatter([L]*len(g),g.K_gross_lu2,label=str(L),alpha=.7)
    save('01_permeability_distributions_by_size.svg','L (voxels)','Kx gross (lu²)')
    plt.errorbar([s['L'] for s in size],[s['mean_K'] for s in size],yerr=[[s['mean_K']-s['mean_K_ci_low'] for s in size],[s['mean_K_ci_high']-s['mean_K'] for s in size]],fmt='o-'); save('02_mean_ci_vs_size.svg','L (voxels)','ensemble mean Kx (lu²)')
    plt.plot([s['L'] for s in size],[s['cv_K'] for s in size],'o-'); save('03_cv_vs_size.svg','L (voxels)','coefficient of variation')
    plt.scatter(passed.solid_fraction,passed.K_gross_lu2,c=passed.restriction_fraction); plt.yscale('log'); save('04_K_vs_solid_fraction.svg','voxel solid fraction','Kx gross (lu², log scale)')
    pg=pd.DataFrame(pairs)
    for f,g in pg.groupby('restriction_fraction'): plt.scatter([f]*len(g),g.ratio)
    for t in TARGETS: plt.axhline(t,ls='--'); save('05_paired_restriction_ratios.svg','restriction fraction','paired K/K0')
    plt.scatter(passed.phi_connected_x,passed.K_gross_lu2,c=passed.state_amp); plt.yscale('log'); save('06_target_capability_map.svg','connected x porosity','Kx gross (lu², log scale)')
    if len(ddf):
      xx=np.arange(len(ddf)); plt.scatter(xx,ddf.Kx,label='Kx'); plt.scatter(xx,ddf.Ky,label='Ky'); plt.scatter(xx,ddf.Kz,label='Kz'); plt.legend()
    save('07_directional_components.svg','geometry index','diagonal K (lu²)')
    if len(ddf): plt.scatter(np.arange(len(ddf)),ddf.Kperp_over_Kx)
    save('08_transverse_axial_ratio.svg','geometry index','Kperp/Kx')
    plt.scatter(passed.pore_distance_q10,passed.K_gross_lu2,c=passed.specific_interfacial_area_lu); plt.yscale('log'); save('09_K_vs_topology.svg','pore-distance q10 (voxels)','Kx gross (lu², log scale)')
    plt.scatter(passed.K_gross_lu2,passed.flux_gini,c=passed.state_amp); plt.xscale('log'); save('10_localization_vs_K.svg','Kx gross (lu², log scale)','flux Gini')
    for parent in sorted({r['parent_case_id'] for r in iraw}):
      z=sorted([r for r in iraw if r['parent_case_id']==parent],key=lambda r:r['force']); plt.plot([r['q_box_lu'] for r in z],[r['force'] for r in z],'o-',label=parent)
    plt.legend(fontsize=5); save('11_inertial_force_flow.svg','superficial q (lu)','body force g (lu)')
    plt.bar([s['model'] for s in scores],[s['grouped_cv_RMSE_logK'] for s in scores]); plt.xticks(rotation=20,ha='right'); save('12_grouped_closure_cv.svg','grouped closure model','CV RMSE(log K)')
    print(json.dumps({"counts":result["run_counts"],"target":assess,"directional":result["directional"],"closure":scores},indent=2))
if __name__=="__main__": main()
