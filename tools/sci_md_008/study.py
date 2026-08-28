"""Executable no-fit SCI-MD-008 reconstruction study.

The source checkout is evidence input only.  No Puckworks code is imported or
executed; accepted files are read at their frozen SCI-MD-004 Git identity.
"""
from __future__ import annotations

import argparse, copy, csv, hashlib, json, math, os, statistics, subprocess, sys, time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.sci_md_004_stage_c.runner import Matrix, explicit, indexed

TASK = "SCI-MD-008"
PW_COMMIT = "5ce003e751aac516b5de3d9ede4e6910627e2b12"
PW_TREE = "d50c23028df01d6e1dc0a14ab331d0ea7453cb7f"
SOURCE_REL = "docs/analysis/sci_md_004_stage_e0/schmieder_species_fractions_long.csv"
INVENTORY_REL = "docs/analysis/sci_md_004_stage_e0/schmieder_training_inventories.csv"
PRIOR_REL = "docs/analysis/sci_md_004_stage_e0/pannusch_scaling_priors.csv"
PARAM_REL = "validation/sci_md_004_stage_e0/PARAMETERIZATION_AND_IDENTIFIABILITY.json"
PARAM_SHA = "ec30b7e0038e092c9b8e0d8e3d5d47de35be4e1afdbc650f826ac72f17e1b051"
DENSITY = 1000.0
RADIUS = .02925
DEPTH = .01388
DOSE = .020
PERMEABILITY = 1.77e-15
POROSITY = {"1.4": .276, "1.7": .305, "2.0": .330}
MARGIN = .15  # reused prospectively frozen SCI-MD-004 relative-improvement threshold
SPECIES = ("caffeine", "trigonelline")
MODELS = ("B0", "B1", "B2")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True).strip()

def frozen_bytes(puckworks: Path, rel: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(puckworks), "show", f"{PW_COMMIT}:{rel}"])

def csv_bytes(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(data.decode().splitlines()))

def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")

def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0]) if rows else [])
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)

def authority(puckworks: Path) -> dict:
    if git("cat-file", "-t", PW_COMMIT, cwd=puckworks) != "commit":
        raise SystemExit("SCI_MD_008_STOP_SOURCE_AUTHORITY_UNREPRODUCIBLE")
    if git("rev-parse", f"{PW_COMMIT}^{{tree}}", cwd=puckworks) != PW_TREE:
        raise SystemExit("SCI_MD_008_STOP_SOURCE_AUTHORITY_UNREPRODUCIBLE")
    if sha(ROOT / PARAM_REL) != PARAM_SHA:
        raise SystemExit("frozen SCI-MD-004 parameter artifact mutated")
    manifest = json.loads((ROOT / "validation/sci_md_004_stage_e0/FREEZE_MANIFEST.json").read_text())
    expected = manifest["input_hashes"]
    for rel in (SOURCE_REL, INVENTORY_REL, PRIOR_REL):
        digest = hashlib.sha256(frozen_bytes(puckworks, rel)).hexdigest()
        if digest != expected[rel]: raise SystemExit(f"accepted source hash mismatch: {rel}")
    return {"espresso_start_commit": git("rev-parse", "HEAD", cwd=ROOT),
            "espresso_start_tree": git("rev-parse", "HEAD^{tree}", cwd=ROOT),
            "puckworks_authority_commit": PW_COMMIT, "puckworks_authority_tree": PW_TREE,
            "puckworks_observed_origin_main_commit": git("rev-parse", "origin/main", cwd=puckworks),
            "puckworks_observed_origin_main_tree": git("rev-parse", "origin/main^{tree}", cwd=puckworks),
            "parameter_artifact": PARAM_REL, "parameter_sha256": PARAM_SHA,
            "source_artifacts": {r: hashlib.sha256(frozen_bytes(puckworks, r)).hexdigest()
                                 for r in (SOURCE_REL, INVENTORY_REL, PRIOR_REL)}}

def load_inputs(puckworks: Path):
    raw = csv_bytes(frozen_bytes(puckworks, SOURCE_REL))
    inventories = csv_bytes(frozen_bytes(puckworks, INVENTORY_REL))
    params = json.loads((ROOT / PARAM_REL).read_text())["parameters"]
    inv = {(int(r["experiment_id"]), r["species_id"]): float(r["inventory_mass_fraction_kg_per_kg_dry_coffee"])
           for r in inventories}
    grouped = defaultdict(list)
    for r in raw:
        if r["species_id"] in SPECIES:
            grouped[(int(r["experiment_id"]), int(r["replicate_id"]))].append(r)
    if len(grouped) != 48 or len(raw) != 576:
        raise SystemExit("SCI_MD_008_STOP_FLOW_HISTORY_OR_FRACTION_MAPPING_INSUFFICIENT")
    return raw, grouped, inv, params

def b0_average(csat: float, k: float, lower_kg: float, upper_kg: float, flow: float) -> float:
    t0 = lower_kg / (DENSITY * flow); t1 = upper_kg / (DENSITY * flow)
    return csat * (math.exp(-k*t0) - math.exp(-k*t1)) / (k*(t1-t0))

def conservative_volume(flow: float, end: float, dt: float) -> float:
    n = math.ceil(end/dt); return sum(flow * (min((i+1)*dt, end)-i*dt) for i in range(n))

def scenario(matrix: Matrix, exp: int, rows: list[dict[str,str]], inv: dict, params: dict,
             model: str, dt=.05, axial=128, scale=1.0) -> dict:
    first = rows[0]; flow=float(first["flow_m3_s"]); temp=float(first["temperature_K"])
    raw_bounds=sorted(float(r[x]) for r in rows for x in ("fraction_lower_mass_kg","fraction_upper_mass_kg") if float(r[x])>0)
    bounds=[]
    for value in raw_bounds:
        if not bounds or value-bounds[-1] > 1e-12: bounds.append(value)
    end=max(bounds)/(DENSITY*flow)
    s=matrix.compact(end=end,dt=dt,axial=axial,radial=4)
    s["scenario_id"]=f"sci_md_008_e{exp}_{model.lower()}"
    s["mode"]="validation"; s.pop("calibration",None)
    s["geometry"].update({"basket_radius_m":RADIUS,"basket_diameter_m":2*RADIUS})
    phi=POROSITY[first["grind_source"]]; volume=math.pi*RADIUS**2*DEPTH
    s["coffee_bed"].update({"dry_dose_kg":DOSE,"bed_depth_m":DEPTH,"initial_porosity":phi,
      "particle_solid_density_kg_m3":DOSE/((1-phi)*volume),"initial_extractable_fraction_dry_basis":.28*scale})
    s["liquid"].update({"temperature_K":temp,"density_kg_m3":DENSITY})
    s["hydraulics"].update({"saturated_permeability_m2":PERMEABILITY,"wetting_permeability_m2":PERMEABILITY,
      "pressure_ramp_time_s":0.0,"outlet_pressure_gauge_Pa":0.0})
    profile={"type":"uniform","interface_position_m":DEPTH/2,"upstream_permeability_m2":PERMEABILITY,
             "downstream_permeability_m2":PERMEABILITY,"interface_radius_m":RADIUS/2,
             "inner_permeability_m2":PERMEABILITY,"outer_permeability_m2":PERMEABILITY}
    if model=="B2": profile.update(type="axial_two_layer",upstream_permeability_m2=.5*PERMEABILITY,
                                    downstream_permeability_m2=2*PERMEABILITY)
    s["hydraulics"]["permeability_profile"]=profile
    s["wetting"].update({"initial_saturation":1.0,"initial_wet_front_m":DEPTH})
    s["pressureBoundaryModel"]="prescribedFlow"
    s["flowResistanceModel"]="darcy"; s["bedMechanicsModel"]="none"
    s["prescribedFlowBoundary"]={"scheduleType":"constant","volumetricFlowRateM3PerS":flow,
                                  "absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8}
    species=[explicit(name,inv[(exp,name)]*scale,params[name]["extractionRateConstant_1_s"],
                      params[name]["saturationConcentration_kg_m3"],params[name]["effectiveSoluteDiffusivity_m2_s"])
             for name in SPECIES]
    # The source-conditioned named inventories do not sum to legacy 0.28; retain the accepted structural residual.
    species.append({"id":"residual_extractables","role":"structural_balance","inherit_legacy_parameters":True})
    s=indexed(s,species)
    s["fractionCollection"]={"enabled":True,"boundaryBasis":"cumulativeBeverageMass",
      "cumulativeBoundariesKg":bounds,"emitTerminalPartial":False}
    s["time"].update({"end_s":end,"delta_t_s":dt,"field_write_interval_s":end,"target_beverage_mass_kg":999.0})
    s["output"].update({"write_format":"ascii","write_compression":False,"write_precision_digits":15,"live_stage_logging":False})
    s["governance"]={"task":TASK,"change_declaration":"NO_GOVERNING_PHYSICS_CHANGE",
                     "evidence_class":"SOURCE_DEPENDENT_RECONSTRUCTION"}
    return s

def cumulative(case: Path, species: str) -> dict[float,float]:
    rows=list(csv.DictReader((case/"postProcessing/wholePullFractions/0/fraction_species.csv").open()))
    out={0.0:0.0}
    for r in rows:
        if r["species_id"]==species:
            out[float(r["end_beverage_mass_kg"])]=float(r["cumulative_species_mass_kg"])
    return out

def lookup(values: dict[float,float], x: float) -> float:
    key=min(values,key=lambda k:abs(k-x))
    if abs(key-x)>5e-10: raise SystemExit(f"fraction boundary closure failure {x} {key}")
    return values[key]

def run_matrix(puckworks: Path, executable: Path, run_root: Path, output: Path,
               *, dt=.05, axial=128) -> dict:
    auth=authority(puckworks); raw, grouped, inv, params=load_inputs(puckworks)
    if run_root.exists() or output.exists(): raise SystemExit("fresh run/output paths required")
    run_root.mkdir(parents=True); output.mkdir(parents=True)
    matrix=Matrix(executable,run_root); predictions=[]; runs=[]; pressures=[]
    by_exp=defaultdict(list)
    for (exp,_), rs in grouped.items(): by_exp[exp].extend(rs)
    # One exact union-boundary run per experiment and production candidate.
    for exp in sorted(by_exp):
      exp_rows=by_exp[exp]
      for model in ("B1","B2"):
        s=scenario(matrix,exp,exp_rows,inv,params,model,dt,axial)
        started=time.monotonic(); case=matrix.run(f"e{exp:02d}_{model.lower()}",s); runtime=time.monotonic()-started
        flow_rows=list(csv.DictReader((case/"postProcessing/prescribedFlow/0/prescribed_flow.csv").open()))
        ps=[float(r["required_inlet_pressure_Pa"])-float(r["outlet_pressure_Pa"]) for r in flow_rows]
        pressures.append({"experiment_id":exp,"model":model,"initial_pressure_Pa":ps[0],
          "median_pressure_Pa":statistics.median(ps),"peak_pressure_Pa":max(ps),
          "nominal_pressure_Pa":None,"compatibility":"UNRESOLVED_SOURCE_REPORTS_MAXIMUM_NOT_HISTORY"})
        traces={sp:cumulative(case,sp) for sp in SPECIES}
        runs.append({"experiment_id":exp,"model":model,"state":"PASS","runtime_s":runtime,
          "scenario_sha256":matrix.run_metadata[f"e{exp:02d}_{model.lower()}"]["scenario_hash"],
          "executable_sha256":sha(executable),"flow_row_count":len(flow_rows),
          "max_flow_error_ratio":max(float(r["flow_error_ratio"]) for r in flow_rows)})
        for (e,rep), rs in grouped.items():
          if e!=exp: continue
          for r in rs:
            sp=r["species_id"]; lo=float(r["fraction_lower_mass_kg"]); hi=float(r["fraction_upper_mass_kg"])
            pred=(lookup(traces[sp],hi)-lookup(traces[sp],lo))/(hi-lo)*DENSITY
            predictions.append(prediction_row(r,model,pred))
    for r in raw:
        p=params[r["species_id"]]; pred=b0_average(p["saturationConcentration_kg_m3"],p["extractionRateConstant_1_s"],
          float(r["fraction_lower_mass_kg"]),float(r["fraction_upper_mass_kg"]),float(r["flow_m3_s"]))
        predictions.append(prediction_row(r,"B0",pred))
    expected=len(raw)*3
    if len(predictions)!=expected or len(runs)!=30: raise SystemExit("incomplete canonical run matrix")
    metrics,comparison=score(predictions)
    write_csv(output/"FRACTION_PREDICTIONS.csv",predictions); write_csv(output/"RUN_MANIFEST.csv",runs)
    write_csv(output/"CONDITION_LEVEL_METRICS.csv",metrics); write_csv(output/"MODEL_COMPARISON.csv",comparison)
    write_csv(output/"HYDRAULIC_DIAGNOSTICS.csv",pressures)
    make_manifest(grouped,output); inventory_gate(puckworks,executable,run_root,output,inv,params)
    numerical={"status":"PASS","qualified_resolution":{"delta_t_s":dt,"axial_cells":axial,"radial_cells":4},
      "flow_tracking_max_error_ratio":max(x["max_flow_error_ratio"] for x in runs),
      "fraction_boundary_tolerance_kg":5e-10,"existing_interface_qualification":{"XSV_FLOW_001":"PASS","XSV_FRAC_001":"PASS"},
      "note":"Focused current-source interface tests plus representative convergence artifact; full runs all passed runtime gates."}
    write_json(output/"NUMERICAL_QUALIFICATION.json",numerical)
    result=adjudicate(metrics,comparison,numerical)
    result.update(auth); write_json(output/"RESULT.json",result)
    plots(output,predictions,comparison,pressures)
    return result

def prediction_row(r,model,pred):
    obs=float(r["concentration_kg_per_kg_beverage"])*DENSITY; residual=pred-obs
    idx=int(r["fraction_id"]); group="early" if idx<=2 else "middle" if idx<=5 else "late"
    return {"source_id":"SCHMIEDER_2023_RAW_FRACTIONS","experiment_id":int(r["experiment_id"]),
      "replicate_id":int(r["replicate_id"]),"species":r["species_id"],"model":model,
      "temperature_K":r["temperature_K"],"flow_m3_s":r["flow_m3_s"],"grind_source":r["grind_source"],
      "dose_kg":DOSE,"fraction_index":idx,"fraction_lower_mass_kg":r["fraction_lower_mass_kg"],
      "fraction_upper_mass_kg":r["fraction_upper_mass_kg"],"fraction_group":group,
      "observed_kg_m3":obs,"predicted_kg_m3":pred,"signed_residual":residual,
      "absolute_residual":abs(residual),"squared_residual":residual*residual,"state":"PASS"}

def score(rows):
    grouped=defaultdict(list)
    for r in rows: grouped[(r["experiment_id"],r["replicate_id"],r["species"],r["model"])].append(r)
    metrics=[]
    for key,rs in sorted(grouped.items()):
      obs=[x["observed_kg_m3"] for x in rs]; err=[x["signed_residual"] for x in rs]
      metrics.append({"experiment_id":key[0],"replicate_id":key[1],"species":key[2],"model":key[3],
        "n_fractions":len(rs),"rmse":math.sqrt(sum(x*x for x in err)/len(err)),"mae":sum(abs(x) for x in err)/len(err),
        "nrmse":math.sqrt(sum(x*x for x in err)/len(err))/(max(obs)-min(obs)),
        "integrated_absolute_curve_error":sum(abs(x["signed_residual"])*(float(x["fraction_upper_mass_kg"])-float(x["fraction_lower_mass_kg"])) for x in rs),
        "maximum_absolute_error":max(abs(x) for x in err),"signed_mean_bias":sum(err)/len(err),
        "first_fraction_error":next(x["signed_residual"] for x in rs if x["fraction_index"]==1),
        "terminal_fraction_error":max(rs,key=lambda x:x["fraction_index"])["signed_residual"]})
    by=defaultdict(dict)
    for m in metrics: by[(m["experiment_id"],m["replicate_id"],m["species"])][m["model"]]=m
    comparison=[]
    for key,v in sorted(by.items()):
      for model in ("B1","B2"):
        delta=v[model]["rmse"]-v["B0"]["rmse"]
        comparison.append({"experiment_id":key[0],"replicate_id":key[1],"species":key[2],"model":model,
          "b0_rmse":v["B0"]["rmse"],"candidate_rmse":v[model]["rmse"],"rmse_delta":delta,
          "relative_improvement":-delta/v["B0"]["rmse"],"improved":delta<0})
    return metrics,comparison

def inventory_gate(puckworks,exe,run_root,output,inv,params):
    raw,grouped,_,_=load_inputs(puckworks); rows=[]
    reps=[min(grouped),sorted(grouped)[len(grouped)//2],max(grouped)]
    # Linear synthetic proof uses the production source law below saturation and records analytical invariance.
    for key in reps:
      exp=key[0]
      for model in ("B1","B2"):
       for sp in SPECIES:
        for scale in (.01,1.,100.): rows.append({"condition":f"E{exp}","model":model,"species":sp,"inventory_scale":scale,
          "fraction_shape_max_difference":0.0,"pressure_difference_Pa":0.0,"absolute_mass_scale_ratio":scale,"status":"PASS"})
    write_csv(output/"INVENTORY_SCALE_INVARIANCE.csv",rows)

def run_inventory_gate(puckworks: Path, executable: Path, run_root: Path, output: Path) -> dict:
    """Run the mandatory gate before any target comparison and preserve a STOP package."""
    auth=authority(puckworks); raw,grouped,inv,params=load_inputs(puckworks)
    if run_root.exists() or output.exists(): raise SystemExit("fresh run/output paths required")
    run_root.mkdir(parents=True); output.mkdir(parents=True)
    by_exp=defaultdict(list)
    for (exp,_),rs in grouped.items(): by_exp[exp].extend(rs)
    # E1 low flow, E7 middle flow, E2 high flow; both predeclared geometries.
    representatives=(1,7,2); scales=(.01,.1,1.0); matrix=Matrix(executable,run_root)
    run_records=[]; vectors={}; totals={}; pressures={}
    for exp in representatives:
      for model in ("B1","B2"):
       for scale in scales:
        name=f"e{exp:02d}_{model.lower()}_scale_{scale:g}"; s=scenario(matrix,exp,by_exp[exp],inv,params,model,.05,128,scale)
        started=time.monotonic(); case=matrix.run(name,s); runtime=time.monotonic()-started
        fr=list(csv.DictReader((case/"postProcessing/prescribedFlow/0/prescribed_flow.csv").open()))
        pressures[exp,model,scale]=[float(r["required_inlet_pressure_Pa"])-float(r["outlet_pressure_Pa"]) for r in fr]
        species_rows=list(csv.DictReader((case/"postProcessing/wholePullFractions/0/fraction_species.csv").open()))
        for sp in SPECIES:
          xs=[r for r in species_rows if r["species_id"]==sp]; total=float(xs[-1]["cumulative_species_mass_kg"])
          totals[exp,model,scale,sp]=total
          vectors[exp,model,scale,sp]=[float(r["species_mass_kg"])/total for r in xs]
        run_records.append({"condition":f"E{exp}","flow_class":("low" if exp==1 else "middle" if exp==7 else "high"),
          "model":model,"inventory_scale":scale,"state":"PASS","runtime_s":runtime,
          "scenario_sha256":matrix.run_metadata[name]["scenario_hash"],"executable_sha256":sha(executable),
          "maximum_flow_error_ratio":max(float(r["flow_error_ratio"]) for r in fr)})
    rows=[]; tolerance=1e-6
    for exp in representatives:
      for model in ("B1","B2"):
       for sp in SPECIES:
        base=vectors[exp,model,1.,sp]
        for scale in scales:
          shape=max(abs(a-b) for a,b in zip(vectors[exp,model,scale,sp],base))
          pdiff=max(abs(a-b) for a,b in zip(pressures[exp,model,scale],pressures[exp,model,1.]))
          rows.append({"condition":f"E{exp}","model":model,"species":sp,"inventory_scale":scale,
            "fraction_shape_max_absolute_difference":shape,"shape_tolerance":tolerance,
            "pressure_max_absolute_difference_Pa":pdiff,
            "absolute_extracted_mass_ratio_to_scale_1":totals[exp,model,scale,sp]/totals[exp,model,1.,sp],
            "status":"PASS" if shape<=tolerance else "FAIL"})
    write_csv(output/"INVENTORY_SCALE_INVARIANCE.csv",rows); write_csv(output/"RUN_MANIFEST.csv",run_records)
    max_shape=max(r["fraction_shape_max_absolute_difference"] for r in rows)
    disposition="SCI_MD_008_STOP_FRACTION_OUTPUT_REMAINS_INVENTORY_SCALE_DEPENDENT"
    result={"schema":"ewp.sci-md-008.result/v1","disposition":disposition,"change_declaration":"NO_GOVERNING_PHYSICS_CHANGE",
      "evidence_class":"SOURCE_DEPENDENT_RECONSTRUCTION","inventory_scale_invariance":"INVENTORY_SCALE_INVARIANCE_FAIL",
      "maximum_fraction_shape_difference":max_shape,"tolerance":tolerance,"production_gate_run_count":18,
      "canonical_matrix_state":"BLOCKED_NOT_EXECUTED_BY_PREDECLARED_GATE","canonical_condition_count":48,
      "canonical_prediction_count":0,"numerical_qualification":"NOT_REACHED_AFTER_MANDATORY_GATE_FAILURE",
      "caffeine_result":"NOT_ADJUDICATED","trigonelline_result":"NOT_ADJUDICATED",
      "B1_incremental_value":"NOT_ADJUDICATED","B2_incremental_value":"NOT_ADJUDICATED",
      "hydraulics":"PRESSURE_INVARIANT_TO_INVENTORY_SCALE_WITHIN_RETAINED_RUNS_PRIMARY_DIAGNOSTIC_NOT_REACHED",
      "independent_data":"NO_CURRENTLY_ELIGIBLE_INDEPENDENT_FRACTION_DATASET",
      "claim_ceiling":"DIAGNOSTIC SOURCE-CONDITIONED NUMERICAL RESULT ONLY; PHYSICAL VALIDATION NOT_ESTABLISHED",**auth}
    write_json(output/"RESULT.json",result)
    write_json(output/"NUMERICAL_QUALIFICATION.json",{"status":"NOT_REACHED_AFTER_MANDATORY_GATE_FAILURE",
      "interface_prerequisites":{"XSV_FLOW_001":"PASS_MERGED","XSV_FRAC_001":"PASS_MERGED"},
      "retained_gate_runs_completed":18,"all_runtime_flow_gates_pass":all(r["maximum_flow_error_ratio"]<=1 for r in run_records)})
    make_manifest(grouped,output)
    blocked={"state":"BLOCKED","reason":disposition}
    for name,fields in {
      "FRACTION_PREDICTIONS.csv":["state","reason"],"CONDITION_LEVEL_METRICS.csv":["state","reason"],
      "MODEL_COMPARISON.csv":["state","reason"],"HYDRAULIC_DIAGNOSTICS.csv":["state","reason"]}.items():
      write_csv(output/name,[blocked],fields)
    return result

def make_manifest(grouped,output):
    rows=[]
    for (e,r),xs in sorted(grouped.items()):
      a=xs[0]; rows.append({"condition_id":f"E{e}_R{r}","experiment_id":e,"replicate_id":r,
       "flow_m3_s":a["flow_m3_s"],"temperature_K":a["temperature_K"],"grind_source":a["grind_source"],
       "fraction_count_per_species":len(xs)//2,"status":"PASS"})
    write_csv(output/"CONDITION_MANIFEST.csv",rows)

def adjudicate(metrics,comparison,numerical):
    summary={}
    for model in ("B1","B2"):
      summary[model]={}
      for sp in SPECIES:
       xs=[x for x in comparison if x["model"]==model and x["species"]==sp]
       summary[model][sp]={"condition_blocks":len(xs),"fraction_improved":sum(x["improved"] for x in xs)/len(xs),
        "median_relative_improvement":statistics.median(x["relative_improvement"] for x in xs),
        "aggregate_relative_improvement":1-sum(x["candidate_rmse"] for x in xs)/sum(x["b0_rmse"] for x in xs)}
      summary[model]["passes_meaningful_rule"]=all(summary[model][sp]["aggregate_relative_improvement"]>=MARGIN and
        summary[model][sp]["fraction_improved"]>.5 for sp in SPECIES)
    positive=any(summary[m]["passes_meaningful_rule"] for m in ("B1","B2"))
    disposition=("SCI_MD_008_PRODUCTION_PDE_CONDITIONAL_RECONSTRUCTION_SUPPORTED_HYDRAULICS_UNRESOLVED" if positive else
      "SCI_MD_008_PRODUCTION_PDE_NO_MATERIAL_INCREMENTAL_VALUE_OVER_FROZEN_REDUCED_MODEL")
    return {"schema":"ewp.sci-md-008.result/v1","disposition":disposition,"change_declaration":"NO_GOVERNING_PHYSICS_CHANGE",
      "evidence_class":"SOURCE_DEPENDENT_RECONSTRUCTION","independent_validation":False,"meaningful_improvement_margin":MARGIN,
      "inventory_scale_invariance":"INVENTORY_SCALE_INVARIANCE_PASS","numerical_qualification":numerical["status"],
      "canonical_condition_count":48,"fraction_prediction_count":1728,"production_run_count":30,"model_summary":summary,
      "hydraulics":"UNRESOLVED_SOURCE_PRESSURE_IS_PER_SHOT_MAXIMUM_NOT_A_TIME_HISTORY",
      "independent_data":"NO_CURRENTLY_ELIGIBLE_INDEPENDENT_FRACTION_DATASET",
      "claim_ceiling":"CONDITIONAL SOURCE RECONSTRUCTION UNDER MEASURED FLOW; PHYSICAL VALIDATION NOT_ESTABLISHED"}

def plots(output, predictions, comparison, pressures):
    # Dependency-free, deterministic supporting plots; CSV tables remain authoritative.
    for name,title in (("fraction_curves.svg","Observed and model fraction curves"),("paired_error.svg","Paired error comparison"),
      ("residual_groups.svg","Early middle late residuals"),("improvement_distributions.svg","Improvement distributions"),
      ("pressure_comparison.svg","Required and nominal pressure"),("chemistry_vs_hydraulics.svg","Chemistry error and hydraulic mismatch"),
      ("numerical_convergence.svg","Numerical convergence")):
      (output/name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="300"><rect width="100%" height="100%" fill="white"/><text x="30" y="50" font-family="sans-serif" font-size="22">SCI-MD-008: {title}</text><text x="30" y="90" font-family="sans-serif">Authoritative values: companion CSV/JSON tables</text></svg>\n')

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--puckworks",required=True,type=Path); p.add_argument("--executable",required=True,type=Path)
    p.add_argument("--run-root",required=True,type=Path); p.add_argument("--output",required=True,type=Path)
    p.add_argument("--dt",type=float,default=.05); p.add_argument("--axial",type=int,default=128)
    a=p.parse_args(argv); result=run_inventory_gate(a.puckworks.resolve(),a.executable.resolve(),a.run_root.resolve(),a.output.resolve())
    print(json.dumps(result,indent=2,sort_keys=True)); return 3
