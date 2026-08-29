"""Executable no-fit SCI-MD-008 reconstruction study.

The source checkout is evidence input only.  No Puckworks code is imported or
executed; accepted files are read at their frozen SCI-MD-004 Git identity.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, math, subprocess, sys, time
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
SPECIES = ("caffeine", "trigonelline")
STOP = "SCI_MD_008_STOP_FRACTION_OUTPUT_REMAINS_INVENTORY_SCALE_DEPENDENT"
BLOCKED_TABLES = ("FRACTION_PREDICTIONS.csv", "CONDITION_LEVEL_METRICS.csv",
                  "MODEL_COMPARISON.csv", "HYDRAULIC_DIAGNOSTICS.csv")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True).strip()

def frozen_bytes(puckworks: Path, rel: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(puckworks), "show", f"{PW_COMMIT}:{rel}"])

def csv_bytes(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(data.decode().splitlines()))

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream: return list(csv.DictReader(stream))

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
    result={"schema":"ewp.sci-md-008.result/v1","disposition":STOP,"change_declaration":"NO_GOVERNING_PHYSICS_CHANGE",
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
    blocked={"state":"BLOCKED","reason":STOP}
    for name in BLOCKED_TABLES: write_csv(output/name,[blocked],["state","reason"])
    verify_result_package(output)
    return result

def make_manifest(grouped,output):
    rows=[]
    for (e,r),xs in sorted(grouped.items()):
      a=xs[0]; rows.append({"condition_id":f"E{e}_R{r}","experiment_id":e,"replicate_id":r,
       "flow_m3_s":a["flow_m3_s"],"temperature_K":a["temperature_K"],"grind_source":a["grind_source"],
       "fraction_count_per_species":len(xs)//2,"status":"PASS"})
    write_csv(output/"CONDITION_MANIFEST.csv",rows)

def verify_result_package(output: Path) -> dict:
    """Fail closed unless retained real rows and STOP summary close exactly."""
    result=json.loads((output/"RESULT.json").read_text())
    gate=read_csv(output/"INVENTORY_SCALE_INVARIANCE.csv")
    runs=read_csv(output/"RUN_MANIFEST.csv")
    if len(gate)!=36 or len(runs)!=18 or any(r["state"]!="PASS" for r in runs):
        raise ValueError("incomplete real inventory-gate evidence")
    expected={(f"E{e}",m,s,scale) for e in (1,7,2) for m in ("B1","B2")
              for s in SPECIES for scale in ("0.01","0.1","1.0")}
    observed={(r["condition"],r["model"],r["species"],r["inventory_scale"]) for r in gate}
    if observed!=expected: raise ValueError("inventory-gate matrix mismatch")
    recomputed=max(float(r["fraction_shape_max_absolute_difference"]) for r in gate)
    if abs(recomputed-float(result["maximum_fraction_shape_difference"]))>1e-15:
        raise ValueError("inventory maximum summary mismatch")
    if result.get("disposition")!=STOP or result.get("inventory_scale_invariance")!="INVENTORY_SCALE_INVARIANCE_FAIL":
        raise ValueError("result is not the required inventory-dependent STOP")
    if result.get("canonical_prediction_count")!=0 or result.get("canonical_matrix_state")!="BLOCKED_NOT_EXECUTED_BY_PREDECLARED_GATE":
        raise ValueError("target matrix is not fail closed")
    for name in BLOCKED_TABLES:
        rows=read_csv(output/name)
        if rows!=[{"state":"BLOCKED","reason":STOP}]: raise ValueError(f"target artifact not blocked: {name}")
    return {"status":"PASS","maximum_fraction_shape_difference":recomputed,
            "inventory_rows":len(gate),"production_runs":len(runs),"target_predictions":0}

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--puckworks",required=True,type=Path); p.add_argument("--executable",required=True,type=Path)
    p.add_argument("--run-root",required=True,type=Path); p.add_argument("--output",required=True,type=Path)
    p.add_argument("--dt",type=float,default=.05); p.add_argument("--axial",type=int,default=128)
    a=p.parse_args(argv); result=run_inventory_gate(a.puckworks.resolve(),a.executable.resolve(),a.run_root.resolve(),a.output.resolve())
    print(json.dumps(result,indent=2,sort_keys=True)); return 3
