#!/usr/bin/env python3
"""Run the target-independent SCI-MD-005 training analysis."""
from __future__ import annotations

import argparse, csv, hashlib, json, math, sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from inventory_scaled_composition import compose
from sci_md_005.reduced import interpolate_cup, simulate

SPECIES = {"caffeine": "c_caffeine_mg_g", "trigonelline": "c_trigonelline_mg_g"}
BOUNDS = {"k_1_s": [0.002, 0.5], "csat_kg_m3": [0.2, 100.0]}
STARTS = ((.01,.5),(.01,10),(.03,2),(.03,30),(.08,1),(.08,15),(.2,3),(.2,60))


def read(path):
    with path.open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))


def load_training(puckworks: Path):
    raw = read(puckworks/"data/schmieder2023/raw_fractions.csv")
    fits = {(int(float(r["exp"])),r["component"]):r for r in read(puckworks/"data/schmieder2023/kinetics_fit_params_avg.csv")}
    grouped=defaultdict(list)
    for r in raw:
        for species,column in SPECIES.items():
            if r[column] and r["mass_fraction_g"] and r["mass_accumulated_g"]:
                grouped[(int(float(r["exp"])),int(float(r["fraction"])),species)].append(r)
    observations=[]
    first=defaultdict(list)
    for (exp,fraction,species), rows in sorted(grouped.items()):
        mass=np.mean([float(r["mass_fraction_g"])*1e-3 for r in rows])
        mid=np.mean([float(r["mass_accumulated_g"])*1e-3 for r in rows])
        concentration=np.mean([float(r[SPECIES[species]])*1e-3 for r in rows])
        observations.append({"experiment_id":exp,"fraction_id":fraction,"species_id":species,
            "flow_m3_s":float(rows[0]["flow_set_ml_s"])*1e-6,
            "temperature_K":float(rows[0]["temp_set_C"])+273.15,
            "lower_mass_kg":mid-mass/2,"upper_mass_kg":mid+mass/2,
            "observed_kg_per_kg":concentration})
        if fraction==1: first[(exp,species)].append((mass,concentration))
    inventories={}
    for (exp,species), vals in first.items():
        fit=fits[(exp,species)]; mass=np.mean([v[0] for v in vals])*1e3
        first_mg=np.mean([v[0]*1e3*v[1]*1e3 for v in vals])
        tail=float(fit["c0"])*float(fit["lambda_g"])*math.exp(-mass/float(fit["lambda_g"]))
        inventories[(exp,species)]=(first_mg+tail)/20*1e-3
    return observations,inventories


def predict(rows, inventories, species, logp, cells=32, dt=.1):
    k,csat=np.exp(logp); byexp=defaultdict(list)
    for r in rows:
        if r["species_id"]==species: byexp[r["experiment_id"]].append(r)
    values={}
    diffusivity=1e-10 if species=="caffeine" else 9.687426142431468e-11
    for exp, obs in byexp.items():
        flow=obs[0]["flow_m3_s"]; end=max(r["upper_mass_kg"] for r in obs)/(1000*flow)
        result=simulate(flow_m3_s=flow,end_s=end,dose_kg=.02,inventory_fraction=inventories[(exp,species)],
            k_1_s=k,csat_kg_m3=csat,diffusivity_m2_s=diffusivity,cells=cells,dt_s=dt)
        for r in obs:
            lo=interpolate_cup(result["history"],r["lower_mass_kg"])
            hi=interpolate_cup(result["history"],r["upper_mass_kg"])
            values[(exp,r["fraction_id"])]=(hi-lo)/(r["upper_mass_kg"]-r["lower_mass_kg"])
    return values


def fit(rows,inventories,species,starts=STARTS):
    selected=[r for r in rows if r["species_id"]==species]
    def residual(x):
        pred=predict(selected,inventories,species,x)
        return np.asarray([math.log(max(pred[(r["experiment_id"],r["fraction_id"])],1e-12))-math.log(r["observed_kg_per_kg"]) for r in selected])
    solutions=[]
    bounds=(np.log([BOUNDS["k_1_s"][0],BOUNDS["csat_kg_m3"][0]]),np.log([BOUNDS["k_1_s"][1],BOUNDS["csat_kg_m3"][1]]))
    for start in starts:
        sol=least_squares(residual,np.log(start),bounds=bounds,method="trf",xtol=1e-9,ftol=1e-9,gtol=1e-9,max_nfev=100)
        solutions.append(sol)
    best=min(solutions,key=lambda s:2*s.cost)
    return best,solutions


def metrics(rows, predictions):
    obs=np.array([r["observed_kg_per_kg"] for r in rows]); pred=np.array([predictions[(r["experiment_id"],r["fraction_id"],r["species_id"])] for r in rows])
    err=pred-obs; rel=np.abs(err)/obs
    return {"rms_log_error":float(np.sqrt(np.mean(np.log(pred/obs)**2))),"nrmse":float(np.sqrt(np.mean(err**2))/np.mean(obs)),
        "mae":float(np.mean(np.abs(err))),"median_absolute_relative_error":float(np.median(rel)),"signed_bias":float(np.mean(err))}


def main():
    p=argparse.ArgumentParser();p.add_argument("--puckworks",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    rows,inventories=load_training(a.puckworks); a.output.mkdir(parents=True,exist_ok=True)
    fitted={}; starts_report={}
    for species in SPECIES:
        sol,solutions=fit(rows,inventories,species)
        fitted[species]={"k_1_s":float(np.exp(sol.x[0])),"csat_kg_m3":float(np.exp(sol.x[1])),"objective":float(2*sol.cost)}
        starts_report[species]=[{"start":list(s),"converged":bool(x.success),"objective":float(2*x.cost),"parameters":list(map(float,np.exp(x.x)))} for s,x in zip(STARTS,solutions)]
    cv_h1={}; cv_h0={}; experiment_effect={}
    experiments=sorted({r["experiment_id"] for r in rows})
    for held in experiments:
        train=[r for r in rows if r["experiment_id"]!=held]; test=[r for r in rows if r["experiment_id"]==held]
        for species in SPECIES:
            sol,_=fit(train,inventories,species,starts=(tuple(fitted[species].values())[:2],))
            pred=predict(test,inventories,species,sol.x)
            for r in test: cv_h1[(held,r["fraction_id"],species)]=pred[(held,r["fraction_id"])]
        # H0: unchanged legacy aggregate history followed by the generic closure.
        flow=test[0]["flow_m3_s"]; end=max(r["upper_mass_kg"] for r in test)/(1000*flow)
        agg=simulate(flow_m3_s=flow,end_s=end,dose_kg=.02,inventory_fraction=.28,k_1_s=.15,
            csat_kg_m3=180,diffusivity_m2_s=1e-9,cells=32,dt_s=.1)
        fractions=sorted({(r["fraction_id"],r["lower_mass_kg"],r["upper_mass_kg"]) for r in test})
        closure=compose(aggregate_history=agg["history"],inventories={s:inventories[(held,s)] for s in SPECIES},dry_dose_kg=.02,
            fractions=[{"fraction_id":f,"lower_beverage_mass_kg":lo,"upper_beverage_mass_kg":hi} for f,lo,hi in fractions],aggregate_inventory_fraction=.28)
        for item in closure["species"]: cv_h0[(held,item["fraction_id"],item["species_id"])]=item["species_concentration_kg_per_kg_beverage"]
    report={"schema_version":"ewp.sci-md-005-training-result/v1",
        "adjudicative_status":"NONADJUDICATIVE_UPSTREAM_H0_CONTRACT_BLOCKED",
        "warning":"These attempted reduced-model metrics cannot select a scientific result because the required H0 identity cannot exactly reproduce the frozen SCI-MD-004 H0 artifacts.",
        "bounds":BOUNDS,"fixed_starts":starts_report,"fitted_parameters":fitted,"metrics":{},"joint":{}}
    for species in SPECIES:
        sr=[r for r in rows if r["species_id"]==species]
        report["metrics"][species]={"H0":metrics(sr,cv_h0),"H1_production":metrics(sr,cv_h1)}
    j0=.5*sum(report["metrics"][s]["H0"]["nrmse"] for s in SPECIES); j1=.5*sum(report["metrics"][s]["H1_production"]["nrmse"] for s in SPECIES)
    report["joint"]={"J_H0":j0,"J_H1_production":j1,"required_maximum":.85*j0,"material_improvement_pass":j1<=.85*j0}
    report["starts_within_one_percent"]={s:max(x["objective"] for x in starts_report[s])<=1.01*min(x["objective"] for x in starts_report[s]) for s in SPECIES}
    out=a.output/"TRAINING_RESULT.json";out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    with (a.output/"BLOCKED_CV_PREDICTIONS.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["experiment_id","fraction_id","species_id","observed_kg_per_kg","H0_kg_per_kg","H1_production_kg_per_kg"],lineterminator="\n");w.writeheader()
        for r in rows:w.writerow({**{k:r[k] for k in ("experiment_id","fraction_id","species_id","observed_kg_per_kg")},"H0_kg_per_kg":cv_h0[(r["experiment_id"],r["fraction_id"],r["species_id"])],"H1_production_kg_per_kg":cv_h1[(r["experiment_id"],r["fraction_id"],r["species_id"])]})
    print(json.dumps(report["joint"],sort_keys=True))
if __name__=="__main__":main()
