#!/usr/bin/env python3
"""E1 implementation gates only. No fitting or demonstration dispatch exists here.

Saved parameter and early-pressure aggregates: Waszkiewicz et al. (2025),
Zenodo 18046315, CC-BY-4.0, via the pinned Puckworks B0c artifacts.
Native cases, full logs and hardware identities must stay outside Git.
"""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PIN = "ba35a3bf1f832cd651fe98eebd59860849c0e850"
NOMINAL = (1., 2., 3.5, 4., 5., 6., 7., 8., 9., 11., 13.)
CSV = "docs/research/PRESSURE_PEAK_STAGE_B0C/RESULT_TABLE.csv"
ONSET = "docs/research/PRESSURE_PEAK_STAGE_B0C/ONSET.csv"


def records(path):
    with Path(path).open() as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    with Path(path).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def saved_inputs(puckworks):
    head = subprocess.check_output(["git", "-C", str(puckworks), "rev-parse", "HEAD"], text=True).strip()
    if head != PIN:
        raise ValueError("E1 requires the exact approved Puckworks runtime pin")
    row = next(r for r in records(puckworks/CSV) if
               (r["candidate"], r["scenario"], r["stage"]) == ("E1", "RAW PRIMARY", "T4 REFIT"))
    bank = json.loads(row["parameters"])["by_fold"]
    bank = {k:v for k,v in bank.items() if k.startswith("HYD-LOCO-")}
    if len(bank) != 11:
        raise ValueError("eleven saved folds required")
    med = {k: statistics.median(v["free"][i] for v in bank.values())
           for i,k in enumerate(("aGPerSBar", "pstarBar", "tauS"))}
    for key, source in (("mcG", "Mc_fixed_g"), ("onsetCS", "onset_c_fixed_s"), ("onsetN", "onset_n_fixed")):
        med[key] = statistics.median(v[source] for v in bank.values())
    early = {float(r["pressure condition bar"]):float(r["early pressure mean bar"])
             for r in records(puckworks/ONSET) if r["check"] == "condition onset"
             and r["pressure view"] == "RAW PRIMARY" and float(r["threshold scale"]) == 1}
    return med, early


def early_input(pressure, saved):
    """Median of eleven training-only pressure interpolants; never onset data."""
    values = []
    for held_out in NOMINAL:
        p = sorted(x for x in saved if x != held_out)
        if pressure <= p[0]: value = saved[p[0]]
        elif pressure >= p[-1]: value = saved[p[-1]]
        else:
            hi = next(x for x in p if x >= pressure); lo = p[p.index(hi)-1]
            value = saved[lo]+(saved[hi]-saved[lo])*(pressure-lo)/(hi-lo)
        values.append(value)
    return statistics.median(values)


def scenario(parameters, early, pressure=9., dt=.02, g1=False, enabled=True):
    cfg = json.loads((ROOT/"config/reference_R0.json").read_text())
    cfg["scenario_id"] = "E1_G1" if g1 else "E1_G2"
    cfg["mode"] = "verification_fixture"
    cfg["time"].update(end_s=100., delta_t_s=dt, field_write_interval_s=100.)
    cfg["hydraulics"]["target_inlet_pressure_gauge_Pa"] = pressure*1e5
    if enabled:
        cfg["e1_whole_bed_closure"] = dict(parameters, enabled=True,
            earlyPressureBar=early_input(pressure, early))
    if g1:
        cfg["geometry"].update(axial_cells=64, radial_cells=1)
        cfg["hydraulics"]["pressure_ramp_time_s"] = 0.
        cfg["wetting"].update(initial_saturation=1., initial_wet_front_m=cfg["coffee_bed"]["bed_depth_m"])
        cfg["coffee_bed"]["initial_extractable_fraction_dry_basis"] = 0.
        cfg["extraction"]["rate_constant_1_s"] = 0.
        cfg["liquid"]["effective_solute_diffusivity_m2_s"] = 0.
    return cfg


def python_flows(puckworks, parameters, early):
    # Use the actual pinned definition, not a second implementation or fitter.
    sys.path.insert(0, str(puckworks))
    import numpy as np
    from puckworks.analysis.pressure_peak_stage_b0 import predict_swelling
    t = np.linspace(0., 100., 1000)
    pressure = np.repeat(np.asarray(NOMINAL)[:,None], len(t), axis=1)
    delay = parameters["onsetCS"]*np.array([early_input(p,early) for p in NOMINAL])**(-parameters["onsetN"])
    return predict_swelling("E1", [parameters[k] for k in ("aGPerSBar","pstarBar","tauS")],
                            pressure,t,delay,parameters["mcG"])[0][:,-1]


def run_case(work, name, cfg, exe, ranks):
    case = work/name
    if case.exists():
        raise ValueError("Refusing to overwrite an existing verification attempt: "+str(case))
    path = work/(name+".json"); path.write_text(json.dumps(cfg,indent=2)+"\n")
    with (work/(name+".prepare.log")).open("w") as log:
        subprocess.run([sys.executable,str(ROOT/"scripts/prepare_case.py"),"--root",str(ROOT),
            "--config",str(path),"--case-dir",str(case),"--nprocs",str(ranks)],check=True,stdout=log,stderr=log)
    for command in (["blockMesh"], ["checkMesh"], *([["decomposePar","-force"]] if ranks>1 else [])):
        with (case/("log."+command[0])).open("w") as log:
            subprocess.run(command,cwd=case,check=True,stdout=log,stderr=log)
    cmd = (["mpirun","-np",str(ranks),"--bind-to","core",str(exe),"-parallel"] if ranks>1 else [str(exe)])
    started=time.monotonic()
    with (case/"log.solver").open("w") as log:
        subprocess.run(cmd,cwd=case,check=True,stdout=log,stderr=log,
                       env=os.environ|{"ESPRESSO_CASE_ROOT":str(case)})
    wall=time.monotonic()-started
    (case/"wall_seconds.txt").write_text(str(wall)+"\n")
    rows=records(case/"postProcessing/wholePull/0/traces.csv")
    if not math.isclose(float(rows[-1]["time_s"]),100.,abs_tol=1e-8):
        raise ValueError("Incomplete 100-s verification run")
    return rows,wall


def require_g1(work):
    rows=records(work/"G1.csv")
    if len(rows)!=11 or any(r["status"]!="PASS" for r in rows):
        raise ValueError("G1 must complete successfully before G2")


PRIMARY = ("outlet_flow_m3_s", "cup_water_mass_kg", "cup_solute_mass_kg",
           "cup_beverage_mass_kg", "stored_water_mass_kg", "remaining_extractable_mass_kg",
           "dissolved_in_puck_mass_kg", "solute_backdiffusion_mass_kg")


def balance_bounds(rows, cfg):
    r = [{k:float(v) for k,v in row.items() if k in set(PRIMARY)|{
        "cumulative_inlet_water_mass_kg","liquid_balance_residual_kg","solute_balance_residual_kg",
        "min_saturation","max_saturation","min_concentration_kg_m3","max_concentration_kg_m3"}}
        for row in rows]
    initial = cfg["coffee_bed"]["dry_dose_kg"]*cfg["coffee_bed"]["initial_extractable_fraction_dry_basis"]
    capacity = (math.pi*cfg["geometry"]["basket_radius_m"]**2*cfg["coffee_bed"]["bed_depth_m"]
                *cfg["coffee_bed"]["initial_porosity"]*cfg["liquid"]["density_kg_m3"])
    water = max(abs(x["liquid_balance_residual_kg"]) for x in r)
    solute = max(abs(x["solute_balance_residual_kg"]) for x in r)
    water_limit = max(1e-9,1e-8*r[-1]["cumulative_inlet_water_mass_kg"])
    solute_limit = max(1e-10,1e-8*initial)
    bounded = all(all(math.isfinite(v) for v in x.values()) and x["min_saturation"] >= -1e-10
        and x["max_saturation"] <= 1+1e-10 and x["min_concentration_kg_m3"] >= -1e-10
        and x["max_concentration_kg_m3"] <= cfg["extraction"]["saturation_concentration_kg_m3"]+1e-8
        and -1e-12 <= x["remaining_extractable_mass_kg"] <= initial+1e-12
        and -1e-12 <= x["stored_water_mass_kg"] <= capacity+1e-12 for x in r)
    monotonic = all(b[key] >= a[key]-1e-12 for a,b in zip(r,r[1:])
        for key in ("cumulative_inlet_water_mass_kg","cup_water_mass_kg","cup_solute_mass_kg"))
    return dict(max_liquid_residual_kg=water,liquid_limit_kg=water_limit,
        max_solute_residual_kg=solute,solute_limit_kg=solute_limit,bounded=bounded,monotonic=monotonic,
        status="PASS" if water<=water_limit and solute<=solute_limit and bounded and monotonic else "FAIL")


def observed_order(coarse, middle, fine):
    """Signed consecutive differences; no absolute-value rescue of oscillation."""
    denominator = middle-fine
    if denominator == 0:
        return "NOT_AVAILABLE"
    ratio = (coarse-middle)/denominator
    return math.log2(ratio) if ratio > 0 and math.isfinite(ratio) else "NOT_AVAILABLE"


def refinement_table(rows, names, graded=True, enabled=True):
    result=[]
    for name,limit in ((names[0],.005),(names[1],.0025)):
        for key in PRIMARY:
            fine=float(rows[names[2]][key]); error=abs(float(rows[name][key])-fine)
            relative=error/abs(fine) if fine else (0. if error==0 else math.inf)
            result.append(dict(case=name,metric=key,deviation=relative,tolerance=limit,
                status=("PASS" if relative<=limit else "FAIL") if graded else "DESCRIPTIVE"))
        fine=float(rows[names[2]]["first_drip_s"])
        error=abs(float(rows[name]["first_drip_s"])-fine)
        tolerance=max(.005,.001*abs(fine)) if enabled else 1e-8
        result.append(dict(case=name,metric="first_drip_s",deviation=error,tolerance=tolerance,
            status=("PASS" if error<=tolerance else "FAIL") if graded else "DESCRIPTIVE"))
    return result


def refinement(work, names=("g2-base","g2-mid","g2-fine"),
               output="G2_REFINEMENT.csv", graded=True, enabled=True):
    rows = {name:records(work/name/"postProcessing/wholePull/0/traces.csv")[-1] for name in names}
    result=refinement_table(rows,names,graded,enabled)
    write_csv(work/output,result)
    if graded and any(x["status"]!="PASS" for x in result):
        raise SystemExit("G2 FAILED: stop; do not tune")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase",choices=("g1","g2-base","g2-refine","off-baseline","off-candidate",
                                               "off-diagnostic","finer-on","finer-off"))
    p.add_argument("--work",type=Path,required=True);p.add_argument("--puckworks",type=Path,required=True)
    p.add_argument("--executable",type=Path,required=True);p.add_argument("--ranks",type=int,default=32)
    a=p.parse_args();a.work=a.work.resolve();a.work.mkdir(parents=True,exist_ok=True)
    if a.work==ROOT or ROOT in a.work.parents: raise ValueError("Keep native runs outside Git")
    parameters,early=saved_inputs(a.puckworks)
    if a.phase=="g1":
        reference=python_flows(a.puckworks,parameters,early);results=[]
        for pressure,expected in zip(NOMINAL,reference):
            cfg=scenario(parameters,early,pressure=pressure,g1=True)
            rows,wall=run_case(a.work,f"g1-{pressure:g}",cfg,a.executable,1)
            actual=float(rows[-1]["outlet_flow_m3_s"])*cfg["liquid"]["density_kg_m3"]*1000
            error=abs(actual-float(expected));limit=max(.02,.05*abs(float(expected)))
            results.append(dict(pressure_bar=pressure,python_g_s=float(expected),solver_g_s=actual,
                deviation_g_s=error,tolerance_g_s=limit,status="PASS" if error<=limit else "FAIL",wall_seconds=wall))
            write_csv(a.work/"G1.csv",results);print(results[-1],flush=True)
            if error>limit: raise SystemExit("G1 FAILED: stop; do not tune")
    else:
        require_g1(a.work)
        choices={"g2-base":[(.02,"g2-base",True)],"g2-refine":[(.01,"g2-mid",True),(.005,"g2-fine",True)],
                 "off-baseline":[(.02,"off-baseline",False)],"off-candidate":[(.02,"off-candidate",False)],
                 "off-diagnostic":[(.01,"off-mid",False),(.005,"off-fine",False)],
                 "finer-on":[(.0025,"on-finer-mid",True),(.00125,"on-finer-fine",True)],
                 "finer-off":[(.0025,"off-finer-mid",False),(.00125,"off-finer-fine",False)]}
        if a.phase in ("off-diagnostic","finer-on","finer-off"):
            identity=json.loads((a.work/"OFF_BYTE_IDENTITY.json").read_text())
            if identity["status"]!="PASS": raise SystemExit("STOP: off-mode byte identity required")
        for dt,name,enabled in choices[a.phase]:
            cfg=scenario(parameters,early,dt=dt,enabled=enabled)
            rows,wall=run_case(a.work,name,cfg,a.executable,a.ranks)
            audit=balance_bounds(rows,cfg)
            (a.work/(name+".checks.json")).write_text(json.dumps(audit,indent=2)+"\n")
            print(dict(case=name,wall_seconds=wall,checks=audit),flush=True)
            if audit["status"]!="PASS": raise SystemExit("G2 FAILED: stop; do not tune")
        if a.phase=="g2-refine":refinement(a.work)
        elif a.phase=="off-diagnostic":
            refinement(a.work,("off-candidate","off-mid","off-fine"),"OFF_DIAGNOSTIC_REFINEMENT.csv",False,False)
            orders=[]
            for mode,names in (("E1_ON",("g2-base","g2-mid","g2-fine")),
                               ("E1_OFF",("off-candidate","off-mid","off-fine"))):
                end=[records(a.work/name/"postProcessing/wholePull/0/traces.csv")[-1] for name in names]
                for key in ("remaining_extractable_mass_kg","dissolved_in_puck_mass_kg"):
                    values=[float(row[key]) for row in end]
                    orders.append(dict(mode=mode,metric=key,coarse=values[0],middle=values[1],fine=values[2],
                                       observed_order=observed_order(*values)))
            write_csv(a.work/"OBSERVED_ORDERS.csv",orders)
        elif a.phase=="finer-on":
            refinement(a.work,("g2-fine","on-finer-mid","on-finer-fine"),"G2_FINER_ON.csv")
        elif a.phase=="finer-off":
            refinement(a.work,("off-fine","off-finer-mid","off-finer-fine"),"G2_FINER_OFF.csv",True,False)


if __name__=="__main__":main()
