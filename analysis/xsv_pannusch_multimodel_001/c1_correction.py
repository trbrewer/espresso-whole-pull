#!/usr/bin/env python3
"""Deterministic C1 privilege-matched correction.

Implements the independently frozen calibration-only PAVA boundary comparator,
condition-then-shot paired bootstrap, exact condition tests, schedule ablation,
inventory-scale check, and residual uncertainty. March chemistry is evaluation
only; target shot windows are non-chemistry observation-operator inputs.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, pathlib, sys
import numpy as np
import pandas as pd

PRIMARY = ("caffeine", "trigonelline")
CONDITIONS = ("PRED-C01", "PRED-C02", "PRED-C05", "PRED-C06")
SCALES = (0.001, 0.01, 0.1, 1.0, 10.0)
SEED = 20260830

def sha(path): return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def write_json(path, value):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

def pava(values, weights):
    vals, wts, starts = [], [], []
    for i, (value, weight) in enumerate(zip(values, weights)):
        vals.append(float(value)); wts.append(float(weight)); starts.append(i)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            weight = wts[-2] + wts[-1]
            value = (vals[-2] * wts[-2] + vals[-1] * wts[-1]) / weight
            vals[-2:] = [value]; wts[-2:] = [weight]; starts[-1:] = []
    out = np.empty(len(values)); ends = starts[1:] + [len(values)]
    for value, start, end in zip(vals, starts, ends): out[start:end] = value
    return out

def load_profiles(source):
    fit = pd.read_csv(source / "fit_fraction_replicates.csv")
    kinetics = pd.read_csv(source / "experimental_kinetics.csv").groupby("exp", as_index=False).first()
    fit = fit[fit.validity.eq("VALID") & fit.analyte.isin(PRIMARY)].merge(
        kinetics[["exp", "Temp_C", "flow_mL_s", "grind_setting"]],
        left_on="source_experiment_id", right_on="exp")
    march = pd.read_csv(source / "prediction_fraction_replicates.csv")
    march = march[march.validity.eq("VALID") & march.analyte.isin(PRIMARY)]
    rows = []
    for campaign, frame, mass_col in (("FIT", fit, "analyte_mass_mg"),
                                      ("MARCH", march, "derived_analyte_mass_mg")):
        for (condition, shot, analyte), group in frame.groupby(
                ["condition_id", "shot_id", "analyte"], sort=True):
            group = group.sort_values("fraction_id")
            if len(group) != 6 or group.fraction_id.nunique() != 6: continue
            mass = group[mass_col].to_numpy(float); liquid = group.fraction_liquid_g_or_ml.to_numpy(float)
            if not np.isfinite(mass).all() or mass.sum() <= 0: raise ValueError("invalid profile mass")
            start = group.fraction_start_s.to_numpy(float); end = group.fraction_end_s.to_numpy(float)
            rows.append({"campaign": campaign, "condition": condition, "shot": shot, "analyte": analyte,
                         "obs": mass/mass.sum(), "liquid": liquid, "start": start, "end": end,
                         "bx": np.r_[0, np.cumsum(liquid)/liquid.sum()],
                         "temperature": float(group.Temp_C.iloc[0] if campaign == "FIT" else group.temperature_start_C.iloc[0]),
                         "flow": float(group.flow_mL_s.iloc[0] if campaign == "FIT" else group.flow_start_mL_s.iloc[0]),
                         "grind": float(group.grind_setting.iloc[0] if campaign == "FIT" else 1.7),
                         "source_experiment": int(group.source_experiment_id.iloc[0]) if campaign == "FIT" else None})
    return rows, fit, march

def fit_boundary(rows):
    models = {}
    for analyte in PRIMARY:
        xx, yy, ww = [], [], []
        for row in rows:
            if row["campaign"] != "FIT" or row["analyte"] != analyte: continue
            xx.extend(row["bx"]); yy.extend(np.r_[0, np.cumsum(row["obs"])]); ww.extend([20]+[1]*5+[20])
        order = np.argsort(xx); x = np.asarray(xx)[order]; y = np.asarray(yy)[order]; w = np.asarray(ww)[order]
        monotone = pava(y, w); ux = np.unique(x)
        uy = np.array([np.average(monotone[x == value], weights=w[x == value]) for value in ux])
        uy = np.maximum.accumulate(np.clip(uy, 0, 1)); uy[0] = 0; uy[-1] = 1
        models[analyte] = (ux, uy)
    return models

def boundary_predict(models, row):
    x, y = models[row["analyte"]]
    if row["bx"].min() < x.min() or row["bx"].max() > x.max():
        raise ValueError("target fraction window outside calibration-supported domain")
    mass = np.maximum(np.diff(np.interp(row["bx"], x, y)), 0)
    return mass / mass.sum()

def fixed_predictions(rows, fit, puckworks):
    sys.path.insert(0, str(puckworks)); from puckworks.models.pannusch2024 import solver
    params = solver._solute_params()
    cl1 = {a: float(g.sort_values("fraction_id").groupby("shot_id").first().concentration_value.mean())
           for a, g in fit.groupby("analyte")}
    exact, ablated = [], []
    march = [r for r in rows if r["campaign"] == "MARCH" and r["condition"] in CONDITIONS]
    for row in march:
        bounds = sorted(set(row["start"]) | set(row["end"]))
        for scale in SCALES:
            solute = dict(params[row["analyte"]]); solute["c_s0"] *= scale
            raw = solver.simulate_fractions(row["temperature"], row["flow"], bounds, solute,
                                            cl1[row["analyte"]], solver.GRINDS[row["grind"]])
            conc = np.array([solver._interval_conc(raw, bounds, lo, hi)
                             for lo, hi in zip(row["start"], row["end"])])
            mass = np.maximum(conc, 0) * row["liquid"]; pred = mass / mass.sum()
            exact.append({"condition": row["condition"], "shot": row["shot"], "analyte": row["analyte"],
                          "scale": scale, "pred": pred, "mass": mass,
                          "rmse": float(np.sqrt(np.mean((pred-row["obs"])**2)))})
    for condition in CONDITIONS:
        group = [r for r in march if r["condition"] == condition]
        unique = {r["shot"]: r for r in group}
        starts = np.mean([r["start"] for r in unique.values()], axis=0)
        ends = np.mean([r["end"] for r in unique.values()], axis=0)
        liquids = np.mean([r["liquid"] for r in unique.values()], axis=0)
        bounds = sorted(set(starts) | set(ends))
        for row in group:
            raw = solver.simulate_fractions(row["temperature"], row["flow"], bounds,
                    dict(params[row["analyte"]]), cl1[row["analyte"]], solver.GRINDS[row["grind"]])
            conc = np.array([solver._interval_conc(raw, bounds, lo, hi) for lo, hi in zip(starts, ends)])
            pred = np.maximum(conc, 0) * liquids; pred /= pred.sum()
            ablated.append({"condition": condition, "shot": row["shot"], "analyte": row["analyte"],
                            "rmse": float(np.sqrt(np.mean((pred-row["obs"])**2)))})
    return exact, ablated, cl1

def hierarchical(frame, model, comparator, seed=SEED):
    rng = np.random.default_rng(seed); values = []
    for _ in range(2000):
        selected = rng.choice(CONDITIONS, len(CONDITIONS), replace=True); left, right = [], []
        for condition in selected:
            group = frame[frame.condition.eq(condition)]; shots = group.shot.unique()
            sampled = rng.choice(shots, len(shots), replace=True)
            intact = pd.concat([group[group.shot.eq(shot)] for shot in sampled], ignore_index=True)
            left.append(intact[model].mean()); right.append(intact[comparator].mean())
        m, b = float(np.mean(left)), float(np.mean(right)); values.append((m, b, m-b))
    values = np.asarray(values)
    return {"model_low": np.quantile(values[:,0], .025), "model_high": np.quantile(values[:,0], .975),
            "comparator_low": np.quantile(values[:,1], .025), "comparator_high": np.quantile(values[:,1], .975),
            "difference_low": np.quantile(values[:,2], .025), "difference_high": np.quantile(values[:,2], .975)}

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--source", type=pathlib.Path, required=True)
    parser.add_argument("--puckworks", type=pathlib.Path, required=True); parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--evidence", type=pathlib.Path, required=True); args = parser.parse_args()
    args.evidence.mkdir(parents=True, exist_ok=True); (args.evidence/"predictions").mkdir(exist_ok=True)
    docs = args.repo/"docs/analysis/xsv_pannusch_multimodel_001"
    rows, fit, _ = load_profiles(args.source); boundary = fit_boundary(rows)
    exact, ablated, cl1 = fixed_predictions(rows, fit, args.puckworks)
    march = {(r["condition"],r["shot"],r["analyte"]):r for r in rows if r["campaign"]=="MARCH" and r["condition"] in CONDITIONS}
    pooled = {a: np.mean([r["obs"] for r in rows if r["campaign"]=="FIT" and r["analyte"]==a],axis=0) for a in PRIMARY}
    one = {(x["condition"],x["shot"],x["analyte"]):x for x in exact if x["scale"]==1}
    records=[]; residual=[]
    for key,row in march.items():
        p=one[key]["pred"]; bp=boundary_predict(boundary,row)
        records.append({"condition":key[0],"shot":key[1],"analyte":key[2],"pannusch":one[key]["rmse"],
          "ordinal":float(np.sqrt(np.mean((pooled[key[2]]-row["obs"])**2))),
          "boundary":float(np.sqrt(np.mean((bp-row["obs"])**2)))})
        residual.append({"condition":key[0],"shot":key[1],"analyte":key[2],**{f"fraction_{i+1}":p[i]-row["obs"][i] for i in range(6)}})
    paired=pd.DataFrame(records); cond=paired.groupby("condition",as_index=False).mean(numeric_only=True)
    for col in ("ordinal","boundary"): cond[f"pannusch_minus_{col}"]=cond.pannusch-cond[col]
    bo=hierarchical(paired,"pannusch","ordinal"); bb=hierarchical(paired,"pannusch","boundary")
    paired.to_csv(args.evidence/"predictions/paired_shot_analyte_errors.csv",index=False)
    cond.to_csv(docs/"CONDITION_DIFFERENCES.csv",index=False)
    pd.DataFrame([{"comparison":"PANNUSCH_MINUS_ORDINAL",**bo},{"comparison":"PANNUSCH_MINUS_BOUNDARY",**bb}]).to_csv(docs/"HIERARCHICAL_UNCERTAINTY_RESULTS.csv",index=False)
    loo=[]
    for omitted in CONDITIONS:
        z=cond[cond.condition.ne(omitted)]; rec={"omitted_condition":omitted}
        for col in ("pannusch","ordinal","boundary"): rec[f"{col}_rmse"]=z[col].mean()
        rec.update(pannusch_minus_ordinal=rec["pannusch_rmse"]-rec["ordinal_rmse"],pannusch_minus_boundary=rec["pannusch_rmse"]-rec["boundary_rmse"],
                   boundary_winner="PANNUSCH" if rec["pannusch_rmse"]<rec["boundary_rmse"] else "BOUNDARY_AWARE")
        loo.append(rec)
    pd.DataFrame(loo).to_csv(docs/"LEAVE_ONE_MARCH_CONDITION_OUT.csv",index=False)
    differences=cond.pannusch_minus_ordinal.to_numpy(); observed=differences.mean()
    assignments=np.array([np.mean(differences*np.array(signs)) for signs in itertools.product((-1,1),repeat=4)])
    sign={"assignments_enumerated":16,"observed_mean":observed,"one_sided_p":float(np.mean(assignments<=observed)),"two_sided_p":float(np.mean(np.abs(assignments)>=abs(observed)-1e-15))}
    write_json(docs/"EXACT_SIGN_FLIP_RESULT.json",sign)
    inv=[]; base={(x["condition"],x["shot"],x["analyte"]):x for x in exact if x["scale"]==1}
    for x in exact:
        b=base[(x["condition"],x["shot"],x["analyte"])]
        inv.append({"condition":x["condition"],"shot":x["shot"],"analyte":x["analyte"],"c_s0_scale":x["scale"],"rmse":x["rmse"],
                    "unnormalized_mass_sum":x["mass"].sum(),"mass_ratio_vs_1x":x["mass"].sum()/b["mass"].sum(),"max_share_delta_vs_1x":np.max(np.abs(x["pred"]-b["pred"]))})
    pd.DataFrame(inv).to_csv(docs/"INVENTORY_SENSITIVITY.csv",index=False)
    pd.DataFrame(ablated).to_csv(docs/"BOUNDARY_PRIVILEGE_RESULTS.csv",index=False)
    res=pd.DataFrame(residual); rr=[]; rng=np.random.default_rng(SEED)
    for fraction in range(1,7):
        vals=[]
        for _ in range(2000):
            means=[]
            for c in rng.choice(CONDITIONS,len(CONDITIONS),replace=True):
                g=res[res.condition.eq(c)]; shots=rng.choice(g.shot.unique(),g.shot.nunique(),replace=True)
                means.append(pd.concat([g[g.shot.eq(s)] for s in shots])[f"fraction_{fraction}"].mean())
            vals.append(np.mean(means))
        rr.append({"fraction":fraction,"mean":res.groupby("condition")[f"fraction_{fraction}"].mean().mean(),"ci_low":np.quantile(vals,.025),"ci_high":np.quantile(vals,.975)})
    pd.DataFrame(rr).to_csv(docs/"RESIDUAL_FINDINGS.csv",index=False)
    means=cond[["pannusch","ordinal","boundary"]].mean().to_dict()
    summary={"means":means,"ordinal_bootstrap":bo,"boundary_bootstrap":bb,"condition_differences":cond.to_dict("records"),"leave_one_out":loo,"sign_flip":sign,
             "cl1":cl1,"condition_average_schedule_rmse":pd.DataFrame(ablated).groupby("condition").rmse.mean().mean(),"boundary_knots":{a:len(boundary[a][0]) for a in PRIMARY},"residuals":rr}
    write_json(args.evidence/"final/c1_computed_results.json",summary); print(json.dumps(summary,indent=2))

if __name__ == "__main__": main()
