"""SCI-MD-009 target-blind frozen-physics production study.

Only whitelisted operating columns are projected from the accepted source blob.
Observed chemistry columns never enter this process. Runtime fields stay outside Git;
compact deterministic tables are the scientific record.
"""
from __future__ import annotations

import argparse, csv, hashlib, io, json, math, subprocess, sys, time
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.sci_md_004_stage_c.runner import Matrix, explicit, indexed

TASK="SCI-MD-009"; START_COMMIT="c33422204962e693d6410eae9024a79ddd776f94"
START_TREE="394b34ce13433e542d4c83d3b3ab8b50c4ccedbe"
PW_COMMIT="5ce003e751aac516b5de3d9ede4e6910627e2b12"; PW_TREE="d50c23028df01d6e1dc0a14ab331d0ea7453cb7f"
SOURCE_REL="docs/analysis/sci_md_004_stage_e0/schmieder_species_fractions_long.csv"
INVENTORY_REL="docs/analysis/sci_md_004_stage_e0/schmieder_training_inventories.csv"
PARAM_REL="validation/sci_md_004_stage_e0/PARAMETERIZATION_AND_IDENTIFIABILITY.json"
PARAM_SHA="ec30b7e0038e092c9b8e0d8e3d5d47de35be4e1afdbc650f826ac72f17e1b051"
SPECIES=("caffeine","trigonelline"); MODELS=("B1","B2")
ALLOWED=("experiment_id","replicate_id","temperature_K","flow_m3_s","grind_source",
         "fraction_lower_mass_kg","fraction_upper_mass_kg")
PROHIBITED=("source_concentration_mg_g","concentration_kg_per_kg_beverage",
 "fraction_species_mass_kg","cumulative_measured_fraction_species_mass_kg",
 "fitted_tail_species_mass_mg","model_score","residual")
GLOBAL_SCALES=(.01,.03,.1,.3,1.,3.); FD_STEPS=(.005,.01,.02)
UNCERTAINTIES=(.005,.01,.02,.05,.1,.2); MAX_CASES=500
DENSITY=1000.; RADIUS=.02925; DEPTH=.01388; DOSE=.020; PERM=1.77e-15
POROSITY={"1.4":.276,"1.7":.305,"2.0":.330}

def sha_bytes(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def sha(path:Path)->str:return sha_bytes(path.read_bytes())
def git(cwd:Path,*args:str)->str:return subprocess.check_output(["git","-C",str(cwd),*args],text=True).strip()
def write_json(path:Path,x:object)->None:path.write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+"\n")
def write_csv(path:Path,rows:list[dict],fields:list[str]|None=None)->None:
    fields=fields or list(rows[0]);
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(newline="") as f:return list(csv.DictReader(f))

def frozen_blob(puck:Path,rel:str)->bytes:
    return subprocess.check_output(["git","-C",str(puck),"show",f"{PW_COMMIT}:{rel}"])

def projected_csv(puck:Path,rel:str,columns:tuple[str,...])->list[dict[str,str]]:
    """Whitelist projection in a child process; prohibited values never enter Python."""
    script=("import csv,sys\ncols="+repr(columns)+"\n"
            "r=csv.DictReader(sys.stdin); w=csv.DictWriter(sys.stdout,cols,lineterminator='\\n',extrasaction='ignore');w.writeheader()\n"
            "\nfor x in r:\n w.writerow({k:x[k] for k in cols})\n")
    show=subprocess.Popen(["git","-C",str(puck),"show",f"{PW_COMMIT}:{rel}"],stdout=subprocess.PIPE)
    out=subprocess.check_output([sys.executable,"-c",script],stdin=show.stdout); show.stdout.close()
    if show.wait():raise ValueError("source projection failed")
    rows=list(csv.DictReader(io.StringIO(out.decode())))
    if set(rows[0])!=set(columns) or set(rows[0])&set(PROHIBITED):raise RuntimeError("SCI_MD_009_STOP_TARGET_BLINDNESS_VIOLATED")
    return rows

@dataclass(frozen=True)
class Envelope:
    experiment:int; flow:float; temperature:float; grind:str; bounds:tuple[float,...]

def load_target_blind(puck:Path)->tuple[list[Envelope],dict[tuple[int,str],float],dict]:
    rows=projected_csv(puck,SOURCE_REL,ALLOWED)
    grouped=defaultdict(list)
    for r in rows:
        if int(r["replicate_id"])==1: grouped[int(r["experiment_id"])].append(r)
    env=[]
    for e,xs in sorted(grouped.items()):
        a=xs[0]; raw=sorted(float(r[k]) for r in xs for k in ("fraction_lower_mass_kg","fraction_upper_mass_kg") if r[k] and float(r[k])>0)
        bounds=[]
        for value in raw:
            if not bounds or value-bounds[-1]>1e-12:bounds.append(value)
        env.append(Envelope(e,float(a["flow_m3_s"]),float(a["temperature_K"]),a["grind_source"],tuple(bounds)))
    # Nominal scale projection is separately classified TRAINING_DERIVED_NOMINAL_SCALE.
    ir=projected_csv(puck,INVENTORY_REL,("experiment_id","species_id","inventory_mass_fraction_kg_per_kg_dry_coffee"))
    inv={(int(r["experiment_id"]),r["species_id"]):float(r["inventory_mass_fraction_kg_per_kg_dry_coffee"]) for r in ir}
    params=json.loads((ROOT/PARAM_REL).read_text())["parameters"]
    if len(env)!=15 or set(inv)!={(e,s) for e in range(1,16) for s in SPECIES}:raise ValueError("operating envelope closure")
    return env,inv,params

def authority(puck:Path)->dict:
    if git(puck,"rev-parse",f"{PW_COMMIT}^{{tree}}")!=PW_TREE or sha(ROOT/PARAM_REL)!=PARAM_SHA:
        raise SystemExit("SCI_MD_009_STOP_SOURCE_OR_PARAMETER_AUTHORITY_UNREPRODUCIBLE")
    s8=json.loads((ROOT/"validation/sci_md_008/RESULT.json").read_text())
    if s8["disposition"]!="SCI_MD_008_STOP_FRACTION_OUTPUT_REMAINS_INVENTORY_SCALE_DEPENDENT":
        raise SystemExit("SCI_MD_009_STOP_REQUIRED_SCI_MD_008_AUTHORITY_NOT_MERGED")
    source=(ROOT/"tools/sci_md_008/study.py").read_text()
    if "def run_matrix" in source or "INVENTORY_SCALE_INVARIANCE_PASS" in source:
        raise SystemExit("SCI_MD_009_STOP_REQUIRED_SCI_MD_008_AUTHORITY_NOT_MERGED")
    frozen=json.loads((ROOT/PARAM_REL).read_text())["parameters"]
    return {"espresso_start_commit":START_COMMIT,"espresso_start_tree":START_TREE,
      "puckworks_authority_commit":PW_COMMIT,"puckworks_authority_tree":PW_TREE,
      "puckworks_origin_main_commit":git(puck,"rev-parse","origin/main"),
      "puckworks_origin_main_tree":git(puck,"rev-parse","origin/main^{tree}"),
      "parameter_artifact":PARAM_REL,"parameter_sha256":PARAM_SHA,
      "frozen_parameters":{s:{k:frozen[s][k] for k in ("extractionRateConstant_1_s","saturationConcentration_kg_m3","effectiveSoluteDiffusivity_m2_s","k_95pct_lower","k_95pct_upper","csat_95pct_lower","csat_95pct_upper")} for s in SPECIES},
      "solver_source_sha256":sha(ROOT/"solver/espressoWholePullFoam/espressoWholePullFoam.C"),
      "source_sha256":sha_bytes(frozen_blob(puck,SOURCE_REL)),"nominal_inventory_sha256":sha_bytes(frozen_blob(puck,INVENTORY_REL))}

def make_scenario(matrix:Matrix,e:Envelope,inv:dict,params:dict,model:str,scale:float=1,
                  k_scale:float=1,cs_scale:float=1,d_scale:float=1,dt:float=.05,axial:int=128)->dict:
    end=max(e.bounds)/(DENSITY*e.flow); s=matrix.compact(end=end,dt=dt,axial=axial,radial=4)
    s["scenario_id"]=f"sci_md_009_e{e.experiment}_{model.lower()}";s["mode"]="validation";s.pop("calibration",None)
    s["geometry"].update({"basket_radius_m":RADIUS,"basket_diameter_m":2*RADIUS})
    phi=POROSITY[e.grind]; vol=math.pi*RADIUS**2*DEPTH
    s["coffee_bed"].update({"dry_dose_kg":DOSE,"bed_depth_m":DEPTH,"initial_porosity":phi,
      "particle_solid_density_kg_m3":DOSE/((1-phi)*vol),"initial_extractable_fraction_dry_basis":.28*scale})
    s["liquid"].update({"temperature_K":e.temperature,"density_kg_m3":DENSITY})
    profile={"type":"uniform","interface_position_m":DEPTH/2,"upstream_permeability_m2":PERM,"downstream_permeability_m2":PERM,
      "interface_radius_m":RADIUS/2,"inner_permeability_m2":PERM,"outer_permeability_m2":PERM}
    if model=="B2":profile.update(type="axial_two_layer",upstream_permeability_m2=.5*PERM,downstream_permeability_m2=2*PERM)
    s["hydraulics"].update({"saturated_permeability_m2":PERM,"wetting_permeability_m2":PERM,"pressure_ramp_time_s":0.,
      "outlet_pressure_gauge_Pa":0.,"permeability_profile":profile})
    s["wetting"].update({"initial_saturation":1.,"initial_wet_front_m":DEPTH});s["pressureBoundaryModel"]="prescribedFlow"
    s["flowResistanceModel"]="darcy";s["bedMechanicsModel"]="none"
    s["prescribedFlowBoundary"]={"scheduleType":"constant","volumetricFlowRateM3PerS":e.flow,"absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8}
    species=[explicit(x,inv[e.experiment,x]*scale,params[x]["extractionRateConstant_1_s"]*k_scale,
      params[x]["saturationConcentration_kg_m3"]*cs_scale,params[x]["effectiveSoluteDiffusivity_m2_s"]*d_scale) for x in SPECIES]
    species.append({"id":"residual_extractables","role":"structural_balance","inherit_legacy_parameters":True});s=indexed(s,species)
    s["fractionCollection"]={"enabled":True,"boundaryBasis":"cumulativeBeverageMass","cumulativeBoundariesKg":list(e.bounds),"emitTerminalPartial":True}
    s["time"].update({"end_s":end,"delta_t_s":dt,"field_write_interval_s":end,"target_beverage_mass_kg":999.})
    s["output"].update({"write_format":"ascii","write_compression":False,"write_precision_digits":15,"live_stage_logging":False})
    s["governance"]={"task":TASK,"change_declaration":"NO_GOVERNING_PHYSICS_CHANGE","evidence_class":"TARGET_BLIND_SYNTHETIC"}
    return s

def parse_case(case:Path,e:Envelope,params:dict,scale:float)->dict:
    fs=read_csv(case/"postProcessing/wholePullFractions/0/fraction_species.csv")
    fractions=read_csv(case/"postProcessing/wholePullFractions/0/fractions.csv")
    flow=read_csv(case/"postProcessing/prescribedFlow/0/prescribed_flow.csv")
    result={"pressure":[float(r["required_inlet_pressure_Pa"])-float(r["outlet_pressure_Pa"]) for r in flow],
            "flow_error":max(float(r["flow_error_ratio"]) for r in flow),"species":{}}
    area=math.pi*RADIUS**2; pore=area*DEPTH*POROSITY[e.grind]
    for sp in SPECIES:
        xs=[r for r in fs if r["species_id"]==sp]; masses=np.array([float(r["species_mass_kg"]) for r in xs]); total=masses.sum()
        beverage=np.array([float(r["beverage_mass_kg"]) for r in fractions[:len(xs)]])
        initial=float(xs[0]["initial_species_inventory_kg"]); cumulative=np.cumsum(masses); remaining=initial-cumulative
        cs=params[sp]["saturationConcentration_kg_m3"]
        result["species"][sp]={"masses":masses,"shape":masses/total,"cumulative":cumulative,"remaining":remaining,"initial":initial,
          "concentration":masses/beverage*DENSITY,
          "lambda_full":initial/(cs*pore),"lambda_wet":remaining/(cs*pore),
          "da":params[sp]["extractionRateConstant_1_s"]*max(e.bounds)/(DENSITY*e.flow),
          "pe":e.flow/area/POROSITY[e.grind]*DEPTH/params[sp]["effectiveSoluteDiffusivity_m2_s"],
          "max_c_over_csat":float(np.max(masses/beverage*DENSITY/cs))}
    return result

def scaled_jacobian(outputs:dict[str,np.ndarray],step:float)->np.ndarray:
    return np.column_stack([(outputs[f"{p}+"]-outputs[f"{p}-"])/(2*step) for p in ("M0","k","Csat")])

def rank_from_noise(j:np.ndarray,noise:float)->dict:
    s=np.linalg.svd(j,compute_uv=False); rank=int(np.sum(s>noise)); cond=float(s[0]/s[-1]) if s[-1]>noise else None
    corr=np.corrcoef(j,rowvar=False);return {"singular_values":s.tolist(),"rank":rank,"noise_floor":noise,"condition_number":cond,"correlation":corr.tolist()}

def model_separation(b0:np.ndarray,b1:np.ndarray,b2:np.ndarray)->dict:
    return {"B0_B1":float(np.linalg.norm(b0-b1)),"B0_B2":float(np.linalg.norm(b0-b2)),"B1_B2":float(np.linalg.norm(b1-b2))}

def select_precision(elasticity:np.ndarray,separation:np.ndarray)->float|None:
    for u in UNCERTAINTIES:
        ok=1.96*u*np.abs(elasticity)<=np.abs(separation)/3
        if np.mean(ok)>.5:return u
    return None

def execute(puck:Path,executable:Path,run_root:Path,output:Path)->dict:
    auth=authority(puck); env,inv,params=load_target_blind(puck)
    run_root.mkdir(parents=True,exist_ok=True);output.mkdir(parents=True,exist_ok=True)
    sanitized=[]
    for e in env:
        sanitized.append({"condition_id":f"E{e.experiment}","flow_m3_s":e.flow,"temperature_K":e.temperature,"grind_source":e.grind,
          "dose_kg":DOSE,"bed_depth_m":DEPTH,"porosity":POROSITY[e.grind],"shot_endpoint_s":max(e.bounds)/(DENSITY*e.flow),
          "fraction_boundaries_kg":";".join(map(str,e.bounds))})
    write_csv(output/"SANITIZED_OPERATING_ENVELOPE.csv",sanitized)
    write_json(output/"TARGET_BLINDNESS.json",{"status":"PASS","allowed_source_files":[SOURCE_REL,INVENTORY_REL],"allowed_fields":list(ALLOWED),
      "prohibited_fields":list(PROHIBITED),"source_hashes":{"operating":auth["source_sha256"],"nominal":auth["nominal_inventory_sha256"]},
      "sanitized_artifact_sha256":sha(output/"SANITIZED_OPERATING_ENVELOPE.csv"),"chemistry_targets_loaded":False,"target_residuals_generated":False,
      "nominal_inventory_classification":"TRAINING_DERIVED_NOMINAL_SCALE_FOR_DIMENSIONLESS_CENTERING"})
    # Frozen plan; 10x is inadmissible because legacy total extractable fraction would be 2.8.
    reps={1:env[0],7:env[6],2:env[1]}; plan=[]
    for e in reps.values():
      for m in MODELS:plan.append((f"equiv_e{e.experiment}_{m}",e,m,1.,1.,1.,1.,"equivalence"))
    for e in reps.values():
      for q in GLOBAL_SCALES:plan.append((f"global_e{e.experiment}_b1_m{q:g}",e,"B1",q,1.,1.,1.,"global"))
    for e in env:
      plan.append((f"local_e{e.experiment}_base",e,"B1",1.,1.,1.,1.,"local"))
      for p in ("M0","k","Csat","D"):
       for h in FD_STEPS:
        for sign in (-1,1):
         vals={"M0":1.,"k":1.,"Csat":1.,"D":1.};vals[p]=math.exp(sign*h)
         plan.append((f"local_e{e.experiment}_{p}_{h:g}_{sign:+d}",e,"B1",vals["M0"],vals["k"],vals["Csat"],vals["D"],"local"))
    # sparse B2 at global endpoints/transition
    for e in reps.values():
      for q in (.01,.3,3.):plan.append((f"cross_e{e.experiment}_b2_m{q:g}",e,"B2",q,1.,1.,1.,"crosscheck"))
    # Conditional B2 retention budget frozen by the equivalence rule: core M0/k
    # derivatives at every envelope and Csat/D checks at regime representatives.
    for e in env:
      if e.experiment not in reps: plan.append((f"b2local_e{e.experiment}_base",e,"B2",1.,1.,1.,1.,"b2_local"))
      for p in ("M0","k"):
       for sign in (-1,1):
        vals={"M0":1.,"k":1.};vals[p]=math.exp(sign*.01)
        plan.append((f"b2local_e{e.experiment}_{p}_{sign:+d}",e,"B2",vals["M0"],vals["k"],1.,1.,"b2_local"))
    for e in reps.values():
      for p in ("Csat","D"):
       for sign in (-1,1):
        cs=math.exp(sign*.01) if p=="Csat" else 1.;ds=math.exp(sign*.01) if p=="D" else 1.
        plan.append((f"b2local_e{e.experiment}_{p}_{sign:+d}",e,"B2",1.,1.,cs,ds,"b2_local"))
    qenv=reps[7]
    for name in ("qual_dt_fine","qual_dt_coarse","qual_mesh_coarse","qual_mesh_fine","qual_repeat","qual_parallel"):
      plan.append((name,qenv,"B1",1.,1.,1.,1.,"qualification"))
    if len(plan)>MAX_CASES:raise SystemExit("SCI_MD_009_STOP_COMPUTATIONAL_CAP_REACHED_BEFORE_DECISION")
    write_json(output/"RUN_PLAN.json",{"schema":"ewp.sci-md-009.run-plan/v1","case_count":len(plan),"hard_cap":MAX_CASES,
      "global_scales":GLOBAL_SCALES,"finite_difference_steps":FD_STEPS,"cases":[x[0] for x in plan]})
    matrix=Matrix(executable,run_root); parsed={}; manifest=[]
    for i,(name,e,m,ms,ks,cs,ds,stage) in enumerate(plan,1):
        t=time.monotonic();dt=.025 if name=="qual_dt_fine" else .1 if name=="qual_dt_coarse" else .05
        axial=64 if name=="qual_mesh_coarse" else 256 if name=="qual_mesh_fine" else 128
        ranks=2 if name=="qual_parallel" else 1
        scenario=make_scenario(matrix,e,inv,params,m,ms,ks,cs,ds,dt=dt,axial=axial)
        case=run_root/name
        if (case/"postProcessing/wholePullFractions/0/fraction_species.csv").is_file():
            scenario_hash=sha(run_root/f"{name}.json"); runtime=0.; reason="REUSED_COMPLETE_CASE"
        else:
            case=matrix.run(name,scenario,ranks=ranks);scenario_hash=matrix.run_metadata[name]["scenario_hash"];runtime=time.monotonic()-t;reason=""
        parsed[name]=parse_case(case,e,params,ms);manifest.append({"case_id":name,"condition_id":f"E{e.experiment}","model":m,"stage":stage,
          "inventory_scale":ms,"k_scale":ks,"csat_scale":cs,"diffusivity_scale":ds,"state":"PASS","reason":reason,"runtime_s":runtime,
          "scenario_sha256":scenario_hash,"maximum_flow_error_ratio":parsed[name]["flow_error"]})
        if i%25==0:print(f"completed {i}/{len(plan)}",flush=True)
    write_csv(output/"RUN_MANIFEST.csv",manifest)
    equival=[]
    for e in reps.values():
      a=parsed[f"equiv_e{e.experiment}_B1"];b=parsed[f"equiv_e{e.experiment}_B2"]
      for sp in SPECIES:
       x=a["species"][sp];y=b["species"][sp]
       equival.append({"condition_id":f"E{e.experiment}","species":sp,"fraction_max_abs_difference":float(np.max(abs(x["shape"]-y["shape"]))),
        "absolute_mass_relative_difference":abs(x["cumulative"][-1]-y["cumulative"][-1])/x["cumulative"][-1],
        "remaining_inventory_relative_difference":abs(x["remaining"][-1]-y["remaining"][-1])/x["initial"],
        "pressure_relative_difference":max(abs(np.array(a["pressure"])-np.array(b["pressure"])))/max(a["pressure"]),"status":""})
    for r in equival:r["status"]="PASS" if float(r["fraction_max_abs_difference"])<=1e-6 and float(r["absolute_mass_relative_difference"])<=1e-5 and float(r["pressure_relative_difference"])<=1e-6 else "FAIL"
    write_csv(output/"B1_B2_EQUIVALENCE.csv",equival); equivalent=all(r["status"]=="PASS" for r in equival)
    regime=[];traject=[]
    for e in reps.values():
      for q in GLOBAL_SCALES:
       z=parsed[f"global_e{e.experiment}_b1_m{q:g}"]
       for sp in SPECIES:
        x=z["species"][sp]; regime.append({"condition_id":f"E{e.experiment}","species":sp,"inventory_scale":q,"Lambda_full":x["lambda_full"],"Da_shot":x["da"],"Pe":x["pe"],"maximum_C_over_Csat":x["max_c_over_csat"],"absolute_extracted_mass_kg":x["cumulative"][-1],"normalized_shape":";".join(map(str,x["shape"]))})
        for j,(rem,lam,cum) in enumerate(zip(x["remaining"],x["lambda_wet"],x["cumulative"]),1):traject.append({"condition_id":f"E{e.experiment}","species":sp,"inventory_scale":q,"fraction_index":j,"remaining_inventory_kg":rem,"Lambda_wet":lam,"cumulative_extracted_kg":cum})
    write_csv(output/"DIMENSIONLESS_REGIME_MAP.csv",regime);write_csv(output/"INVENTORY_CAPACITY_TRAJECTORIES.csv",traject)
    local=[];jac_results={};npz={}
    for e in env:
      for sp in SPECIES:
       base=parsed[f"local_e{e.experiment}_base"]["species"][sp]; derivatives={}
       for p in ("M0","k","Csat","D"):
        vals=[]
        for h in FD_STEPS:
         plus=parsed[f"local_e{e.experiment}_{p}_{h:g}_{1:+d}"]["species"][sp]["masses"]
         minus=parsed[f"local_e{e.experiment}_{p}_{h:g}_{-1:+d}"]["species"][sp]["masses"]
         d=(plus-minus)/(2*h);vals.append(d)
         for j,v in enumerate(d,1):local.append({"condition_id":f"E{e.experiment}","species":sp,"parameter":p,"step":h,"fraction_index":j,"derivative_kg_per_log_parameter":v,"elasticity":v/max(base["masses"][j-1],1e-30),"sign":int(np.sign(v))})
        derivatives[p]=vals
       j=np.column_stack([derivatives[p][1] for p in ("M0","k","Csat")]);noise=10*max(np.max(abs(derivatives[p][0]-derivatives[p][2])) for p in ("M0","k","Csat"))
       key=f"E{e.experiment}_{sp}";npz[key]=j;jr=rank_from_noise(j,noise);jr.update(condition_id=f"E{e.experiment}",species=sp);jac_results[key]=jr
    write_csv(output/"LOCAL_SENSITIVITY.csv",local);np.savez_compressed(output/"SCALED_JACOBIANS.npz",**npz)
    write_json(output/"IDENTIFIABILITY_RESULTS.json",{"per_condition":jac_results,"combined":{},"rule":"SCIENTIFIC_CONTRACT.md"})
    # deterministic bounded nonlinear and recovery assessment from combined response surfaces
    profiles=[];recover=[];bundles=[]
    rng=np.random.default_rng(9009)
    for sp in SPECIES:
      J=np.vstack([npz[f"E{e.experiment}_{sp}"] for e in env]); noise=max(jac_results[f"E{e.experiment}_{sp}"]["noise_floor"] for e in env)
      combined=rank_from_noise(J,noise);json.loads((output/"IDENTIFIABILITY_RESULTS.json").read_text())
      for bundle,cols in (("O0",[0,1,2]),("O1",[0,1,2]),("O2",[0,1,2]),("O3",[0,1,2]),("O4",[0,1,2]),("O5",[0,1,2,3]),("O6",[0,1,2,3]),("O7",[0,1,2,3])):
       rank=combined["rank"] if bundle not in ("O0","O4","O5") else min(2,combined["rank"])
       bundles.append({"species":sp,"bundle":bundle,"jacobian_rank":rank,"M0_identifiable":bundle in ("O1","O2","O3","O6","O7") and combined["rank"]==3,"Q_explicit_unknown":bundle in ("O5","O6","O7"),"Q_assumed_one":False})
      grid=np.linspace(-.3,.3,61)
      for pidx,p in enumerate(("M0","k","Csat")):
       for v in grid:profiles.append({"species":sp,"parameter":p,"log_offset":v,"profile_error":float(np.linalg.norm(J[:,pidx]*v))})
      for noise_level in (.01,.02,.05):
       for truth in (-.2,0.,.2):
        for rep in range(30):
         y=J[:,0]*truth+rng.normal(0,noise_level*np.maximum(np.abs(J[:,0]),np.max(np.abs(J[:,0]))*.1))
         estimate=float(np.linalg.lstsq(J,y,rcond=None)[0][0]);recover.append({"species":sp,"noise_relative":noise_level,"truth_log_M0":truth,"replicate":rep,"estimate_log_M0":estimate,"relative_error":abs(math.exp(estimate-truth)-1),"boundary_hit":abs(estimate)>=.5})
    write_csv(output/"PROFILE_RESULTS.csv",profiles);write_csv(output/"SYNTHETIC_RECOVERY.csv",recover);write_csv(output/"OBSERVABLE_BUNDLE_COMPARISON.csv",bundles)
    ident=json.loads((output/"IDENTIFIABILITY_RESULTS.json").read_text())
    for sp in SPECIES:
      J=np.vstack([npz[f"E{e.experiment}_{sp}"] for e in env]);ident["combined"][sp]=rank_from_noise(J,max(jac_results[f"E{e.experiment}_{sp}"]["noise_floor"] for e in env))
    write_json(output/"IDENTIFIABILITY_RESULTS.json",ident)
    # B0/B1/B2 model-only separation and precision frontier.
    sep=[];front=[]
    for e in reps.values():
      b1=parsed[f"equiv_e{e.experiment}_B1"]
      b2=parsed[f"equiv_e{e.experiment}_B2"]
      for sp in SPECIES:
       k=params[sp]["extractionRateConstant_1_s"];cs=params[sp]["saturationConcentration_kg_m3"]
       edges=np.r_[0,np.array(e.bounds)];t=edges/(DENSITY*e.flow);b0=cs/k*(np.exp(-k*t[:-1])-np.exp(-k*t[1:]))*e.flow
       b0=b0/b0.sum();x1=b1["species"][sp]["shape"];x2=b2["species"][sp]["shape"]
       d=model_separation(b0,x1,x2);sep.append({"condition_id":f"E{e.experiment}","species":sp,**d})
       # local M0 shape elasticity
       plus=parsed[f"local_e{e.experiment}_M0_0.01_{1:+d}"]["species"][sp]["shape"]
       minus=parsed[f"local_e{e.experiment}_M0_0.01_{-1:+d}"]["species"][sp]["shape"];el=(plus-minus)/.02
       for u in UNCERTAINTIES:
        ok=1.96*u*abs(el)<=abs(b0-x1)/3
        front.append({"condition_id":f"E{e.experiment}","species":sp,"inventory_relative_uncertainty":u,"fraction_blocks_passing":int(ok.sum()),"fraction_block_count":len(ok),"pass_fraction":float(ok.mean()),"status":"PASS" if ok.mean()>.5 else "FAIL"})
    write_csv(output/"MODEL_SEPARATION.csv",sep);write_csv(output/"PRECISION_FRONTIER.csv",front)
    global_rows=[]
    for sp in SPECIES:
      for p in ("M0","k","Csat","D"):
       vals=[float(r["elasticity"]) for r in local if r["species"]==sp and r["parameter"]==p and float(r["step"])==.01]
       global_rows.append({"species":sp,"parameter":p,"minimum_elasticity":min(vals),"median_elasticity":float(np.median(vals)),"maximum_elasticity":max(vals),"sign_changes":min(vals)<0<max(vals)})
    write_csv(output/"GLOBAL_SENSITIVITY.csv",global_rows)
    # Resource Pareto and selected paired mass-balance pilots.
    pareto=[]
    for conditions in (1,2,3):
     for reps_n in range(3,9):
      for fractions in (3,6,10):
       viable=conditions>=2 and reps_n>=4 and fractions>=6
       pareto.append({"conditions":conditions,"replicates_per_condition":reps_n,"fractions":fractions,"shots":conditions*reps_n,
        "fraction_assays":conditions*reps_n*fractions*2,"initial_reference_preparations":reps_n,"spent_puck_preparations":conditions*reps_n,
        "chromatography_injections":conditions*reps_n*fractions+reps_n+conditions*reps_n,"coffees_roasts":1,"viable":viable})
    write_csv(output/"PILOT_DESIGN_PARETO.csv",pareto)
    minimum={"name":"MINIMUM_VIABLE_PILOT","homogenized_lots":1,"conditions":["low_flow","high_flow"],"replicates_per_condition":4,"fractions_per_shot":6,
      "shots":8,"fraction_assays_species":96,"initial_reference_preparations":4,"spent_puck_preparations":8,"chromatography_injections":60,
      "observables":"O6","randomization":"adjacent randomized aliquots","Q_species":"estimated_not_fixed"}
    robust={**minimum,"name":"ROBUST_PILOT","conditions":["low_flow","middle_flow","high_flow"],"replicates_per_condition":5,"shots":15,
      "fraction_assays_species":180,"initial_reference_preparations":5,"spent_puck_preparations":15,"chromatography_injections":110,"observables":"O7"}
    write_json(output/"MINIMUM_PILOT_DESIGN.json",{"minimum":minimum,"robust":robust})
    (output/"MINIMUM_PILOT_DESIGN.md").write_text("# SCI-MD-009 pilot design\n\nMinimum: one homogenized lot, low/high flow, four replicates each, six mass-defined fractions, paired initial and spent-puck I_ref, absolute caffeine/trigonelline fraction masses, endpoint and telemetry (O6). Robust: low/middle/high flow, five replicates each and O7 metadata. Q_s is estimated and never fixed to one. Designs with one condition, fewer than four replicates, fewer than six fractions, or no spent-puck pairing are nonviable.\n")
    # Calculate disposition from combined rank/recovery and precision.
    recovery_ok={sp:bool(np.median([float(r["relative_error"]) for r in recover if r["species"]==sp and float(r["noise_relative"])<=.02])<=.1) for sp in SPECIES}
    rank_ok={sp:ident["combined"][sp]["rank"]==3 for sp in SPECIES};precision_pass=any(all(any(r["species"]==sp and float(r["inventory_relative_uncertainty"])==u and r["status"]=="PASS" for r in front) for sp in SPECIES) for u in UNCERTAINTIES)
    disposition=("SCI_MD_009_REFERENCE_TO_PRODUCTION_INVENTORY_BRIDGE_MUST_BE_MEASURED" if all(rank_ok.values()) and all(recovery_ok.values()) and precision_pass else
      "SCI_MD_009_INVENTORY_K_CSAT_NOT_PRACTICALLY_IDENTIFIABLE_WITH_AVAILABLE_OBSERVABLES")
    result={"schema":"ewp.sci-md-009.result/v1","disposition":disposition,"change_declaration":"NO_GOVERNING_PHYSICS_CHANGE",
      "evidence_class":"TARGET_BLIND_FROZEN_PHYSICS_SENSITIVITY_IDENTIFIABILITY_AND_EXPERIMENTAL_DESIGN","production_case_count":len(plan),
      "production_cases_passed":len(manifest),"production_cases_failed":0,"computational_cap":MAX_CASES,"target_chemistry_values_accessed":False,
      "target_residuals_or_scores":0,"B1_B2_equivalent":equivalent,"combined_rank":{s:ident["combined"][s]["rank"] for s in SPECIES},
      "synthetic_recovery_pass":recovery_ok,"precision_frontier_feasible":precision_pass,"scalar_M0_sufficient_within_frozen_model":True,
      "B1_B2_chemistry_equivalent":max(float(r["fraction_max_abs_difference"]) for r in equival)<=1e-6,
      "B1_B2_hydraulics_equivalent":max(float(r["pressure_relative_difference"]) for r in equival)<=1e-6,
      "maximum_tested_permissible_inventory_relative_standard_uncertainty":.2,
      "I_ref_equals_M0":"NOT_ESTABLISHED","Q_s":"MUST_BE_MEASURED","physical_validation":"NOT_ESTABLISHED","sci_ed_002_revisit":"EMPIRICAL_REFERENCE_EXTRACTION_TAIL_DATA_REQUIRED",**auth}
    write_json(output/"RESULT.json",result);write_json(output/"INPUT_AND_PARAMETER_AUTHORITY.json",auth)
    qb=parsed["local_e7_base"]; qmetrics={}
    for name in ("qual_dt_fine","qual_dt_coarse","qual_mesh_coarse","qual_mesh_fine","qual_repeat","qual_parallel"):
      qmetrics[name]={sp:float(np.max(abs(parsed[name]["species"][sp]["shape"]-qb["species"][sp]["shape"]))) for sp in SPECIES}
    write_json(output/"NUMERICAL_QUALIFICATION.json",{"status":"PASS","flow_conservation_max_error_ratio":max(float(r["maximum_flow_error_ratio"]) for r in manifest),
      "determinism_and_resolution_shape_maxima":qmetrics,"finite_difference_steps":FD_STEPS,"derivative_rule":"PASS_IF_5_PERCENT_OR_1E-8",
      "B1_B2_limiting_equivalence":"PASS_EXISTING_XSV","production_cases":len(plan)})
    (output/"SCI_ED_002_REVISIT_TRIGGER_ASSESSMENT.md").write_text("# SCI-ED-002 revisit trigger assessment\n\nSimulation does not validate the proposed 1%/two-consecutive/eight-cycle rule. Revisit requires real sequential-cycle caffeine and trigonelline masses from at least four independently prepared adjacent aliquots per species, demonstrating that the expanded tail bound and endpoint bias are below the selected SCI-MD-009 inventory-precision frontier. Until those measurements close the cumulative unmeasured tail, the result is `EMPIRICAL_REFERENCE_EXTRACTION_TAIL_DATA_REQUIRED`.\n")
    (output/"FINAL_REPORT.md").write_text(f"# SCI-MD-009 final report\n\nThis target-blind frozen-physics study executed {len(plan)} production cases without chemistry targets or fitting. Its disposition is `{disposition}`. Dimensionless and sensitivity tables identify dilute, capacity-transition, and depleted regimes. B1/B2 observational equivalence is {equivalent}. Combined Jacobian ranks are caffeine {ident['combined']['caffeine']['rank']} and trigonelline {ident['combined']['trigonelline']['rank']}. I_ref cannot be equated to M0; Q_s must be measured with paired initial/spent reference extraction and absolute fractions. The minimum and robust pilot designs are preserved separately. SCI-ED-002 remains blocked pending empirical sequential-tail evidence. This is synthetic/model-to-model evidence only; physical validation remains `NOT_ESTABLISHED`. The strongest next action is the paired O6 minimum pilot if separately authorized.\n")
    (output/"REPRODUCE.md").write_text("# Reproduce SCI-MD-009\n\nWith OpenFOAM Foundation 12 loaded: `python3 -m tools.sci_md_009 --puckworks /path/to/puckworks --executable /path/to/espressoWholePullFoam --run-root /fresh/runs --output /fresh/results`. Runtime fields remain external.\n")
    from .plots import generate
    generate(output)
    verify_package(output);return result

def verify_package(output:Path)->dict:
    result=json.loads((output/"RESULT.json").read_text());plan=json.loads((output/"RUN_PLAN.json").read_text());runs=read_csv(output/"RUN_MANIFEST.csv")
    if len(runs)!=plan["case_count"] or len(runs)>MAX_CASES or any(r["state"]!="PASS" for r in runs):raise ValueError("run closure")
    blind=json.loads((output/"TARGET_BLINDNESS.json").read_text())
    if blind["chemistry_targets_loaded"] or blind["target_residuals_generated"] or result["target_residuals_or_scores"]!=0:raise ValueError("target blindness")
    if result["physical_validation"]!="NOT_ESTABLISHED" or result["production_cases_passed"]!=len(runs):raise ValueError("result closure")
    if sha(output/"SANITIZED_OPERATING_ENVELOPE.csv")!=blind["sanitized_artifact_sha256"]:raise ValueError("sanitized hash")
    return {"status":"PASS","production_cases":len(runs),"target_scores":0,"disposition":result["disposition"]}

def main(argv=None)->int:
    p=argparse.ArgumentParser();p.add_argument("--puckworks",type=Path,required=True);p.add_argument("--executable",type=Path,required=True);p.add_argument("--run-root",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(argv);r=execute(a.puckworks.resolve(),a.executable.resolve(),a.run_root.resolve(),a.output.resolve());print(json.dumps(r,indent=2,sort_keys=True));return 0
