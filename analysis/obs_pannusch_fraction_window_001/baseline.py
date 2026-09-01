"""Dependency-light exact translation of the frozen predecessor row calculation."""
import csv
import numpy as np

def reproduce(source, solver):
    def read(name):
        with (source/name).open(newline="",encoding="utf-8") as stream: return list(csv.DictReader(stream))
    fit=[r for r in read("fit_fraction_replicates.csv") if r["validity"]=="VALID" and r["analyte"] in ("caffeine","trigonelline")]
    first={}
    for r in fit:
        if int(r["fraction_id"])==1: first[(r["shot_id"],r["analyte"])]=float(r["concentration_value"])
    cl1={an:float(np.mean([v for (shot,a),v in first.items() if a==an])) for an in ("caffeine","trigonelline")}
    march=[r for r in read("prediction_fraction_replicates.csv") if r["validity"]=="VALID" and r["analyte"] in cl1 and r["condition_id"] in ("PRED-C01","PRED-C02","PRED-C05","PRED-C06")]
    groups={}
    for r in march: groups.setdefault((r["condition_id"],r["shot_id"],r["analyte"]),[]).append(r)
    params=solver._solute_params(); rows=[]
    for key,g in sorted(groups.items()):
        g.sort(key=lambda r:int(r["fraction_id"])); starts=np.array([float(r["fraction_start_s"]) for r in g]); ends=np.array([float(r["fraction_end_s"]) for r in g]); bounds=sorted(set(starts)|set(ends))
        raw=solver.simulate_fractions(float(g[0]["temperature_start_C"]),float(g[0]["flow_start_mL_s"]),bounds,dict(params[key[2]]),cl1[key[2]],solver.GRINDS[1.7])
        concentration=np.array([solver._interval_conc(raw,bounds,lo,hi) for lo,hi in zip(starts,ends)]); liquid=np.array([float(r["fraction_liquid_g_or_ml"]) for r in g]); predicted=np.maximum(concentration,0)*liquid; predicted/=predicted.sum()
        observed=np.array([float(r["derived_analyte_mass_mg"]) for r in g]); observed/=observed.sum(); residual=predicted-observed
        for i in range(6): rows.append({"condition":key[0],"shot":key[1],"analyte":key[2],"fraction":i+1,"observed_share":observed[i],"predicted_share":predicted[i],"residual":residual[i]})
    return rows
