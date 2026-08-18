#!/usr/bin/env python3
"""Deterministic SCI-ED-001 model adapters, execution, and reduction."""
from __future__ import annotations

import argparse, concurrent.futures, gzip, hashlib, importlib.util, itertools, json, math, os, platform, resource, subprocess, sys, time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "validation/cases/sci_ed_001"
START_HEAD = "e8a66378d7829877fb74c87889193f32dd977772"; START_TREE = "1c51175a8c5035c0cab989fada791aebb78f6fd7"
TPRE = 4.65666677903568; RHO = 965.0; RECORD_SCHEMA = "espresso.whole_pull.sci_ed_001.case_record.v1"

def canonical(x): return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
def hash_obj(x): return hashlib.sha256(canonical(x).encode()).hexdigest()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a): return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
def module(name, path):
    s=importlib.util.spec_from_file_location(name,path)
    if s is None or s.loader is None: raise RuntimeError("MODEL_INTERFACE_NOT_AVAILABLE_FOR_VIRTUAL_PROGRAM")
    m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
_MODELS=None
def models():
    global _MODELS
    if _MODELS is None:_MODELS=(module("sci_ed_a",ROOT/"scripts/sci_md_002a.py"),module("sci_ed_b",ROOT/"scripts/sci_md_002b.py"),module("sci_ed_c",ROOT/"scripts/sci_md_002c.py"))
    return _MODELS
def load(name): return json.loads((OUT/name).read_text())

def pressure(program,t):
    points=program["breakpoints"]
    if t<=points[0]["time_s"]: return points[0]["pressure_pa_gauge"]
    if t>=points[-1]["time_s"]: return points[-1]["pressure_pa_gauge"]
    for x,y in zip(points,points[1:]):
        if x["time_s"]<=t<=y["time_s"]:
            if y["time_s"]==x["time_s"]: return y["pressure_pa_gauge"]
            f=(t-x["time_s"])/(y["time_s"]-x["time_s"])
            return x["pressure_pa_gauge"]+f*(y["pressure_pa_gauge"]-x["pressure_pa_gauge"])
    raise RuntimeError("PROGRAM_EVALUATION_FAILED")

def time_grid(program,dt):
    events={0.0,TPRE,TPRE+80.0}
    events.update(TPRE+x["time_s"] for x in program["breakpoints"])
    n=math.floor((TPRE+80.0)/dt); events.update(round(i*dt,12) for i in range(n+1))
    return sorted(x for x in events if 0<=x<=TPRE+80.0)

def series(program,dt,k0=None,bmod=None):
    rows=[]
    for t in time_grid(program,dt):
        p=500000.0 if t<=TPRE else pressure(program,t-TPRE)
        qkg=0.0 if k0 is None else k0*bmod.AREA*p/(bmod.MU*bmod.H0)*bmod.RHO
        rows.append({"source_time_s":t,"solver_time_s":t,"observed_pressure_pa":p,"reference_model_pressure_pa":p,
                     "observed_flow_kg_s":qkg,"reference_model_flow_kg_s":qkg,"observed_mass_kg":0.0,"reference_model_mass_kg":0.0})
    return rows

def ledger_lookup(): return {(x["family_id"],x["parameter_stem_id"]):x for x in load("MODEL_FAMILY_INCLUSION_LEDGER.json")["rows"] if x["inclusion_status"]=="INCLUDED"}
def program_lookup(): return {x["program_id"]:x for x in load("PRESSURE_PROGRAMS.json")["programs"]}

def run_a(family,params,program,dt,a):
    src=a.source_rows();pc=float(params["critical_pressure_pa"]);tau=float(params["theta_c"])*a.TSHOT;k0=a.anchor_k0(pc,src)
    sigma=0.;mass=0.;out=[];prev_t=0.;prev_q=0.
    for i,t in enumerate(time_grid(program,dt)):
        dti=0. if i==0 else t-prev_t;p=500000. if t<=TPRE else pressure(program,t-TPRE)
        if dti: sigma=(sigma+dti*p/tau)/(1+dti/tau)
        if sigma>=pc: raise ValueError("OUTSIDE_DECLARED_MODEL_DOMAIN")
        g=a.conductance(sigma,pc,k0)
        if family=="F_GENERIC": g=a.conductance(0,pc,k0)*math.exp(-2.5*sigma/pc)
        q=g*p
        if i: mass+=0.5*(prev_q+q)*RHO*dti
        x=sigma/pc;out.append({"time_s":t,"design_time_s":t-TPRE,"pressure_pa":p,"outlet_flow_m3_s":q,"outlet_flow_kg_s":q*RHO,"cumulative_mass_kg":mass,"apparent_resistance_pa_s_m3":p/q if q>1e-12 else None,"bed_height_m":a.H0*a.bed_ratio(x) if family=="F_TPM" else None,"deformation_m":a.H0*(1-a.bed_ratio(x)) if family=="F_TPM" else None,"state_sigma_pa":sigma})
        prev_t=t;prev_q=q
    return out

def find_b_row(params,resolution,b):
    for row in b.matrix_rows():
        if row["arm"]=="S1" and row["resolution"]==resolution and all(row[k]==params[k] for k in ("powder","D_multiplier","cmax","accommodation")):
            x=dict(row);x["pressure_condition"]="SOURCE_P5";return x
    raise RuntimeError("SWELLING_STEM_INTERFACE_NOT_RESOLVED")

def run_b(params,program,dt,resolution,b):
    k0=b.hydraulic_anchor();s=series(program,dt,k0,b);hist={5:s,9:s,11:s};result=b.simulate(find_b_row(params,resolution,b),hist)
    out=[];mass=0.;prev=None
    for x in result["temporal"]:
        q=x["outlet_flow_m3_s"]
        if prev is not None: mass+=.5*(prev[1]+q)*RHO*(x["time_s"]-prev[0])
        h=b.H0+params["accommodation"]*x["swelling_storage_volume_m3"]/b.AREA
        out.append({"time_s":x["time_s"],"design_time_s":x["time_s"]-TPRE,"pressure_pa":x["pressure_pa"],"outlet_flow_m3_s":q,"outlet_flow_kg_s":q*RHO,"cumulative_mass_kg":mass,"apparent_resistance_pa_s_m3":x["pressure_pa"]/q if q>1e-12 else None,"bed_height_m":h,"deformation_m":b.H0-h,"wet_fraction":x["wet_fraction"],"swelling_storage_volume_m3":x["swelling_storage_volume_m3"]})
        prev=(x["time_s"],q)
    return out

def find_c_row(params,resolution,c):
    for row in c.matrix_rows():
        if row["arm"]=="S1" and row["resolution"]==resolution and all(row[k]==params[k] for k in ("fines_fraction","mobilizable_fraction","release_rate_s","release_exponent","retention_fraction","layer_porosity","specific_cake_resistance_m_kg","particle_velocity_ratio")):
            x=dict(row);x["pressure_identity"]="SOURCE_P5";return x
    raise RuntimeError("FINES_STEM_INTERFACE_NOT_RESOLVED")

def run_c(params,program,dt,resolution,c):
    s=series(program,dt);result=c.simulate(find_c_row(params,resolution,c),{5:s,9:s,11:s});out=[];mass=0.;prev=None
    for x in result["temporal"]:
        q=x["predicted_flow_kg_s"]/RHO
        if prev is not None: mass+=.5*(prev[1]+q)*RHO*(x["source_time_s"]-prev[0])
        out.append({"time_s":x["source_time_s"],"design_time_s":x["source_time_s"]-TPRE,"pressure_pa":x["observed_pressure_pa"],"outlet_flow_m3_s":q,"outlet_flow_kg_s":x["predicted_flow_kg_s"],"cumulative_mass_kg":mass,"apparent_resistance_pa_s_m3":x["total_resistance_pa_s_m3"] if q>1e-12 else None,"released_mass_rate_kg_s":x["released_mass_rate_kg_s"],"outlet_fines_flux_kg_s":x["outlet_fines_flux_kg_s"],"cumulative_released_mass_kg":x["cumulative_released_mass_kg"],"escaped_mass_kg":x["escaped_mass_kg"],"deposited_mass_kg":x["deposited_mass_kg"],"cake_resistance_pa_s_m3":x["compact_layer_resistance_pa_s_m3"],"fines_mass_residual_kg":x["mass_residual_kg"]})
        prev=(x["source_time_s"],q)
    return out

def event_value(rows,t,key,side="nearest"):
    valid=[x for x in rows if x.get(key) is not None]
    if not valid:return None
    return min(valid,key=lambda x:abs(x["design_time_s"]-t))[key]
def integrate(rows,key,start=0,end=80):
    xs=[x for x in rows if start<=x["design_time_s"]<=end and x.get(key) is not None];total=0.
    for a,b in zip(xs,xs[1:]):total+=.5*(a[key]+b[key])*(b["design_time_s"]-a["design_time_s"])
    return total if len(xs)>1 else None

def features(rows,program_id):
    design=[x for x in rows if x["design_time_s"]>=-1e-10];pre=[x for x in rows if -2<=x["design_time_s"]<=0]
    q0=sum(x["outlet_flow_m3_s"] for x in pre)/len(pre);rvals=[x["apparent_resistance_pa_s_m3"] for x in pre if x["apparent_resistance_pa_s_m3"] is not None];r0=sum(rvals)/len(rvals)
    last=design[-1];f={"pre_event_flow_m3_s":q0,"pre_event_resistance_pa_s_m3":r0,"terminal_normalized_flow":last["outlet_flow_m3_s"]/q0 if q0 else None,"terminal_normalized_resistance":last["apparent_resistance_pa_s_m3"]/r0 if last["apparent_resistance_pa_s_m3"] is not None and r0 else None,"terminal_mass_kg":last["cumulative_mass_kg"]-design[0]["cumulative_mass_kg"]}
    event_times={"P3_UPSTEP_5_TO_11":[20,21],"P4_DOWNSTEP_11_TO_5":[20,21],"P5_PULSE_9_11_9":[20,21,26,27],"P6_UNLOAD_9_0_9":[20,21,31,32],"P7_CYCLE_5_11_5_11_5":[15,16,30,31,45,46],"P8_SLOW_RAMP_5_TO_9":[0,10]}.get(program_id,[])
    for t in event_times:
        f[f"flow_at_{t:g}s_m3_s"]=event_value(design,t,"outlet_flow_m3_s");f[f"resistance_at_{t:g}s_pa_s_m3"]=event_value(design,t,"apparent_resistance_pa_s_m3")
    if program_id in {"P4_DOWNSTEP_11_TO_5","P6_UNLOAD_9_0_9","P7_CYCLE_5_11_5_11_5"}:
        before=event_value(design,20 if program_id!="P7_CYCLE_5_11_5_11_5" else 15,"apparent_resistance_pa_s_m3");late=last["apparent_resistance_pa_s_m3"]
        f["post_unload_residual_resistance"]=late/r0-1 if late is not None and r0 else None;f["resistance_recovery_fraction"]=(before-late)/(before-r0) if None not in (before,late) and abs(before-r0)>0 else None
    if program_id=="P5_PULSE_9_11_9":f["pulse_integrated_flow_m3"]=integrate(design,"outlet_flow_m3_s",20,27)
    if any(x.get("deformation_m") is not None for x in design):
        vals=[x["deformation_m"] for x in design if x.get("deformation_m") is not None];f["maximum_compression_m"]=max(vals);f["residual_deformation_m"]=vals[-1]
    if any("swelling_storage_volume_m3" in x for x in design):f["swelling_storage_uptake_m3"]=max(x.get("swelling_storage_volume_m3",0) for x in design)
    if any("outlet_fines_flux_kg_s" in x for x in design):
        f.update({"peak_outlet_fines_flux_kg_s":max(x["outlet_fines_flux_kg_s"] for x in design),"cumulative_released_mass_kg":last["cumulative_released_mass_kg"],"cumulative_escaped_mass_kg":last["escaped_mass_kg"],"cumulative_deposited_mass_kg":last["deposited_mass_kg"],"cake_resistance_pa_s_m3":last["cake_resistance_pa_s_m3"],"fines_mass_conservation_residual_kg":max(abs(x["fines_mass_residual_kg"]) for x in design)})
    return f

def run_row(row):
    a,b,c=models();item=ledger_lookup()[(row["family_id"],row["parameter_stem_id"])];program=program_lookup()[row["program_id"]];dt=float(row["internal_timestep_s"])
    if row["family_id"] in {"F_TPM","F_GENERIC"}:traj=run_a(row["family_id"],item["parameters"],program,dt,a)
    elif row["family_id"]=="F_SWELL":traj=run_b(item["parameters"],program,dt,row["resolution_id"],b)
    elif row["family_id"]=="F_FINES":traj=run_c(item["parameters"],program,dt,row["resolution_id"],c)
    else:raise RuntimeError("UNKNOWN_FAMILY")
    return {"schema_version":RECORD_SCHEMA,"row_id":row["row_id"],"family_id":row["family_id"],"parameter_stem_id":row["parameter_stem_id"],"program_id":row["program_id"],"resolution_id":row["resolution_id"],"authority":{k:row[k] for k in ("source_model_hash","source_parameter_hash","pressure_program_hash","feature_definition_hash")},"features":features(traj,row["program_id"]),"trajectory":traj}

def replay():
    a,b,c=models();checks=[];src=a.source_rows()
    arows=a.matrix_rows();selected=[]
    selectors=[
        lambda r:r["model"]=="TPM_SINGLE_MODE_TRANSIENT" and r["arm"]=="S1_SOURCE_PRESSURE_SCREEN" and r["theta_c"]==.01 and r["pressure_group_bar"]==9,
        lambda r:r["model"]=="TPM_SINGLE_MODE_TRANSIENT" and r["arm"]=="S1_SOURCE_PRESSURE_SCREEN" and r["theta_c"]==.3 and r["pressure_group_bar"]==9,
        lambda r:r["model"]=="TPM_SINGLE_MODE_TRANSIENT" and r["arm"]=="S1_SOURCE_PRESSURE_SCREEN" and r["theta_c"]==10. and r["pressure_group_bar"]==9,
        lambda r:r["model"]=="TPM_SINGLE_MODE_TRANSIENT" and r["arm"]=="S1_SOURCE_PRESSURE_SCREEN" and r["pressure_group_bar"]==11,
        lambda r:r["model"]=="TPM_SINGLE_MODE_TRANSIENT" and r["waveform"]=="UNLOAD",
        lambda r:r["model"]=="TPM_QUASI_STATIC_EQUILIBRIUM",
        lambda r:r["model"]=="TPM_DISABLED_FIXED_HYDRAULICS",
        lambda r:r["model"]=="GENERIC_RELAXING_RESISTANCE",
    ]
    for selector in selectors:selected.append(next(r for r in arows if selector(r)))
    for row in selected:
        x=a.simulate(row,src);checks.append({"family":"SCI-MD-002A","case_id":row["case_id"],"status":"PASS" if x["status"]=="PASS" else "FAIL","terminal_flow":x.get("final_q_kg_s"),"terminal_mass":x.get("final_mass_kg")})
    for row in [r for r in b.matrix_rows() if r["pilot_eligible"]]:
        x=b.simulate(row);checks.append({"family":"SCI-MD-002B","case_id":row["case_id"],"status":"PASS" if x["status"] in {"COMPLETE","DESIGN_BLOCKED"} else "FAIL","terminal_flow":x.get("terminal_outlet_flow_kg_s"),"full_wetting_time":x.get("full_wetting_time_s")})
    cresult=json.loads((ROOT/"validation/cases/sci_md_002c/SCI_MD_002C_RESULT.json").read_text());feasible=[x["candidate_parameters"] for x in cresult["candidates"] if x["inventory_feasible"] and x["numerical_physical_valid"]]
    all_c=c.matrix_rows();crows=[]
    for params in feasible:crows.append(next(r for r in all_c if r["arm"]=="S1" and r["resolution"]=="BASE" and r["pressure_identity"]=="SOURCE_P9" and all(r[k]==params[k] for k in ("fines_fraction","mobilizable_fraction","release_rate_s","release_exponent","retention_fraction","layer_porosity","specific_cake_resistance_m_kg","particle_velocity_ratio"))))
    crows.extend([next(r for r in all_c if r["arm"]=="S1" and r["resolution"]=="BASE" and r["pressure_identity"]=="SOURCE_P9" and r not in crows),next(r for r in all_c if r["arm"]=="C0" and r["pressure_identity"]=="SOURCE_P9")])
    for row in crows:
        x=c.simulate(row);terminal=x.get("terminal") or x.get("temporal",[{}])[-1];checks.append({"family":"SCI-MD-002C","case_id":row["case_id"],"status":"PASS" if x.get("temporal") and math.isfinite(terminal["predicted_flow_kg_s"]) else "FAIL","terminal_flow":terminal.get("predicted_flow_kg_s"),"mass_residual":terminal.get("mass_residual_kg")})
    result={"schema_version":"espresso.whole_pull.sci_ed_001.replay.v1","status":"PASS" if all(x["status"]=="PASS" for x in checks) else "FAIL","tolerance_policy":"EXACT_PREDECESSOR_CALLABLE_NO_TOLERANCE_WEAKENING","predecessor_implementation_sha256":{"SCI-MD-002A":sha(ROOT/"scripts/sci_md_002a.py"),"SCI-MD-002B":sha(ROOT/"scripts/sci_md_002b.py"),"SCI-MD-002C":sha(ROOT/"scripts/sci_md_002c.py")},"predecessor_dispositions":{"SCI-MD-002A":"SCI_MD_002A_REJECTED_WRONG_PRESSURE_ORDERING","SCI-MD-002B":"SCI_MD_002B_REJECTED_WRONG_PRESSURE_ORDERING","SCI-MD-002C":"SCI_MD_002C_REJECTED_WRONG_PRESSURE_ORDERING"},"checks":checks}
    return result

def safe_bundle(path):
    p=Path(path).resolve()
    if "SCI_ED_001_EXTERNAL_BUNDLE" not in p.parts or ROOT==p or ROOT in p.parents:raise ValueError("EXTERNAL_BUNDLE_PATH_INVALID")
    return p
def atomic_gzip(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+".tmp");data=canonical(obj).encode()
    with tmp.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw,mode="wb",mtime=0) as z:z.write(data)
        raw.flush();os.fsync(raw.fileno())
    tmp.replace(path);decoded=gzip.decompress(path.read_bytes())
    if decoded!=data:raise IOError("ATOMIC_RECORD_READBACK_FAILED")
    return {"path":path.name,"bytes":path.stat().st_size,"file_sha256":sha(path),"content_sha256":hashlib.sha256(data).hexdigest()}
def execute(bundle_arg,authority_arg):
    bundle=safe_bundle(bundle_arg)
    if bundle.exists():raise FileExistsError("IMMUTABLE_ATTEMPT_ALREADY_EXISTS")
    bundle.mkdir(parents=True);authority=json.loads(Path(authority_arg).read_text());matrix=load("SCI_ED_001_CASE_MATRIX.json")
    expected={"source_head":git("rev-parse","HEAD"),"source_tree":git("rev-parse","HEAD^{tree}"),"protocol_sha256":sha(OUT/"SCI_ED_001_PROTOCOL.json"),"matrix_sha256":sha(OUT/"SCI_ED_001_CASE_MATRIX.json"),"implementation_sha256":sha(Path(__file__))}
    if any(authority.get(k)!=v for k,v in expected.items()):raise PermissionError("EXECUTION_AUTHORITY_MISMATCH")
    workers=max(1,min(8,(os.cpu_count() or 1)//8));(bundle/"authority").mkdir();(bundle/"adjudicative").mkdir();(bundle/"manifests").mkdir();(bundle/"logs").mkdir()
    (bundle/"authority/EXECUTION_AUTHORITY.json").write_text(canonical(authority));(bundle/"authority/ENVIRONMENT.json").write_text(canonical({"python":platform.python_version(),"logical_cpus":os.cpu_count(),"workers":workers,"nested_threads":1,"gpu":0,"openfoam":0,"puckworks":0}))
    (bundle/"protocol").mkdir()
    for name in ("SCI_ED_001_PROTOCOL.json","SCI_ED_001_CASE_MATRIX.json","SOURCE_BINDING.json","PRESSURE_PROGRAMS.json","FEATURE_DEFINITIONS.json"):
        (bundle/"protocol"/name).write_bytes((OUT/name).read_bytes())
    start=time.perf_counter();records=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        pending={};iterator=iter(matrix["rows"])
        for row in itertools.islice(iterator,workers*2):pending[pool.submit(run_row,row)]=row
        while pending:
            done,_=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                row=pending.pop(future);rec=future.result();rec["execution_authority_sha256"]=sha(bundle/"authority/EXECUTION_AUTHORITY.json")
                records.append(atomic_gzip(bundle/"adjudicative"/(row["row_id"]+".json.gz"),rec))
                next_row=next(iterator,None)
                if next_row is not None:pending[pool.submit(run_row,next_row)]=next_row
    records.sort(key=lambda x:x["path"]);aggregate=hashlib.sha256("".join(x["file_sha256"] for x in records).encode()).hexdigest();elapsed=time.perf_counter()-start
    manifest={"schema_version":"espresso.whole_pull.sci_ed_001.run_manifest.v1","expected_rows":matrix["row_count"],"completed_rows":len(records),"invalid_rows":0,"records":records,"ordered_record_aggregate_sha256":aggregate,"elapsed_s":elapsed,"worker_count":workers,"peak_rss_bytes_parent":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
    (bundle/"manifests/RUN_MANIFEST.json").write_text(canonical(manifest));return manifest

PRIMARY_PAIRS=(("F_TPM","F_SWELL"),("F_TPM","F_FINES"),("F_TPM","F_GENERIC"),("F_SWELL","F_FINES"),("F_SWELL","F_GENERIC"),("F_FINES","F_GENERIC"))
def record_files(bundle):return sorted((safe_bundle(bundle)/"adjudicative").glob("*.json.gz"))
def read_record(path):
    data=gzip.decompress(path.read_bytes());obj=json.loads(data)
    if canonical(obj).encode()!=data:raise ValueError("NONCANONICAL_OR_CORRUPT_CASE_RECORD")
    return obj
def verify_bundle(bundle_arg,authority_arg):
    bundle=safe_bundle(bundle_arg);manifest=json.loads((bundle/"manifests/RUN_MANIFEST.json").read_text());authority=json.loads(Path(authority_arg).read_text())
    external_authority=json.loads(Path(authority_arg).read_text());internal_authority=json.loads((bundle/"authority/EXECUTION_AUTHORITY.json").read_text())
    if external_authority!=internal_authority:raise PermissionError("BUNDLE_AUTHORITY_OBJECT_MISMATCH")
    files=record_files(bundle);records=[]
    for p in files:
        rec=read_record(p);records.append({"path":p.name,"bytes":p.stat().st_size,"file_sha256":sha(p),"content_sha256":hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest()})
    records.sort(key=lambda x:x["path"]);agg=hashlib.sha256("".join(x["file_sha256"] for x in records).encode()).hexdigest()
    ok=len(records)==manifest["expected_rows"]==manifest["completed_rows"] and agg==manifest["ordered_record_aggregate_sha256"] and authority["source_head"]==git("rev-parse","HEAD")
    return {"schema_version":"espresso.whole_pull.sci_ed_001.bundle_verification.v1","status":"PASS" if ok else "FAIL","record_count":len(records),"ordered_record_aggregate_sha256":agg}
def feature_class(feature):
    if "deformation" in feature or "compression" in feature:return "DEFORMATION"
    if "fines" in feature or "released_mass" in feature or "deposited_mass" in feature or "escaped_mass" in feature or "cake_resistance" in feature:return "FINES"
    if "wetting" in feature or "swelling" in feature:return "WETTING"
    if "upstream" in feature:return "UPSTREAM"
    return "HYDRAULIC"
def package_allows(package,feature):
    cls=feature_class(feature);allowed={"M0":{"HYDRAULIC"},"M1":{"HYDRAULIC","UPSTREAM"},"M2":{"HYDRAULIC","DEFORMATION"},"M3":{"HYDRAULIC","FINES"},"M4":{"HYDRAULIC","WETTING"},"M5":{"HYDRAULIC","UPSTREAM","DEFORMATION"},"M6":{"HYDRAULIC","UPSTREAM","DEFORMATION","FINES","WETTING"}}
    return cls in allowed[package]
def measurement_expansion(feature,values):
    if feature=="terminal_mass_kg":return 5e-4
    if feature in {"maximum_compression_m","residual_deformation_m"}:return 5e-5
    if feature=="pre_event_flow_m3_s":return 2e-8
    if feature=="terminal_normalized_flow":
        denominators=[v for v in values if isinstance(v,(int,float)) and v>0]
        return 4e-8/min(denominators) if denominators else math.inf
    if "resistance" in feature:
        denominators=[v for v in values if isinstance(v,(int,float)) and v>0]
        return 2*(8000/500000+2e-8/min(denominators)) if denominators else 0.0
    if feature_class(feature)=="FINES":return None
    return 0.0
def classify(a,b):
    margin=max(b[0]-a[1],a[0]-b[1]);return ("ROBUSTLY_SEPARATED" if margin>0 else "OVERLAPPING",margin)
def select_set_cover(separations,package="M6",scenario="N1"):
    rows=[x for x in separations if x["measurement_package_id"]==package and x["noise_scenario_id"]==scenario and x["classification"]=="ROBUSTLY_SEPARATED"]
    programs=sorted({x["program_id"] for x in rows});target={tuple(sorted(x)) for x in PRIMARY_PAIRS};candidates=[]
    for n in range(1,4):
      for combo in itertools.combinations(programs,n):
        chosen=[x for x in rows if x["program_id"] in combo];covered={tuple(sorted((x["family_a"],x["family_b"]))) for x in chosen}
        if covered==target:
            margins=[]
            for pair in target:margins.append(max(x["separation_margin"] for x in chosen if tuple(sorted((x["family_a"],x["family_b"])))==pair))
            candidates.append({"program_ids":list(combo),"program_count":n,"complete_pair_coverage":True,"worst_pair_margin":min(margins),"measurement_package_id":package})
      if candidates:break
    return sorted(candidates,key=lambda x:(-x["worst_pair_margin"],x["program_count"],x["program_ids"]))[0] if candidates else {"program_ids":[],"program_count":0,"complete_pair_coverage":False,"worst_pair_margin":None,"measurement_package_id":package}
def reduce_bundle(bundle_arg,authority_arg):
    bundle=safe_bundle(bundle_arg);verification=verify_bundle(bundle,authority_arg)
    if verification["status"]!="PASS":raise ValueError("BUNDLE_VERIFICATION_FAILED")
    grouped={}
    for p in record_files(bundle):
        r=read_record(p);grouped.setdefault((r["family_id"],r["parameter_stem_id"],r["program_id"]),{})[r["resolution_id"]]=r
    if any(set(v)!={"BASE","REFINED"} for v in grouped.values()):raise ValueError("BASE_REFINED_PAIR_INCOMPLETE")
    primitive=[]
    for (family,stem,program),pair in sorted(grouped.items()):
        common=set(pair["BASE"]["features"])&set(pair["REFINED"]["features"])
        for feature in sorted(common):
            x=pair["BASE"]["features"][feature];y=pair["REFINED"]["features"][feature]
            if isinstance(x,(int,float)) and isinstance(y,(int,float)) and math.isfinite(x) and math.isfinite(y):primitive.append({"family_id":family,"parameter_stem_id":stem,"program_id":program,"feature_id":feature,"base":x,"refined":y,"numeric_uncertainty":abs(x-y)})
    preflows={(x["family_id"],x["parameter_stem_id"],x["program_id"]):x["base"] for x in primitive if x["feature_id"]=="pre_event_flow_m3_s"}
    envelopes=[]
    for scenario in ("N0","N1"):
      for key in sorted({(x["family_id"],x["program_id"],x["feature_id"]) for x in primitive}):
        vals=[x for x in primitive if (x["family_id"],x["program_id"],x["feature_id"])==key];lo=min(x["base"]-x["numeric_uncertainty"] for x in vals);hi=max(x["base"]+x["numeric_uncertainty"] for x in vals);expand=0.0
        if scenario=="N1":
            expand=measurement_expansion(key[2],[preflows.get((x["family_id"],x["parameter_stem_id"],x["program_id"])) for x in vals])
            if expand is None:expand=0.0
        minrow=min(vals,key=lambda x:x["base"]-x["numeric_uncertainty"]);maxrow=max(vals,key=lambda x:x["base"]+x["numeric_uncertainty"])
        envelopes.append({"family_id":key[0],"program_id":key[1],"feature_id":key[2],"noise_scenario_id":scenario,"family_feature_min":lo,"family_feature_max":hi,"numerical_expansion":max(x["numeric_uncertainty"] for x in vals),"measurement_expansion":expand,"expanded_min":lo-expand,"expanded_max":hi+expand,"parameter_stem_at_min":minrow["parameter_stem_id"],"parameter_stem_at_max":maxrow["parameter_stem_id"],"feature_status":"COMPARABLE"})
    emap={(x["family_id"],x["program_id"],x["feature_id"],x["noise_scenario_id"]):x for x in envelopes};separations=[]
    for program in [x["program_id"] for x in load("PRESSURE_PROGRAMS.json")["programs"]]:
      for package in [f"M{i}" for i in range(7)]:
       for scenario in ("N0","N1"):
        for fa,fb in PRIMARY_PAIRS:
          shared=sorted({k[2] for k in emap if k[0]==fa and k[1]==program and k[3]==scenario}&{k[2] for k in emap if k[0]==fb and k[1]==program and k[3]==scenario})
          candidates=[]
          for feature in shared:
            if not package_allows(package,feature):continue
            ea=emap[(fa,program,feature,scenario)];eb=emap[(fb,program,feature,scenario)];status,margin=classify((ea["expanded_min"],ea["expanded_max"]),(eb["expanded_min"],eb["expanded_max"]));candidates.append((status,margin,feature))
          separated=[x for x in candidates if x[0]=="ROBUSTLY_SEPARATED"]
          if separated:status,margin,feature=max(separated,key=lambda x:(x[1],x[2]))
          elif candidates:status,margin,feature=max(candidates,key=lambda x:(x[1],x[2]))
          else:status,margin,feature="NOT_COMPARABLE",None,None
          separations.append({"program_id":program,"measurement_package_id":package,"noise_scenario_id":scenario,"family_a":fa,"family_b":fb,"classification":status,"separation_margin":margin,"best_feature":feature})
    rankings=[]
    for program in [x["program_id"] for x in load("PRESSURE_PROGRAMS.json")["programs"]]:
      for package in [f"M{i}" for i in range(7)]:
        rows=[x for x in separations if x["program_id"]==program and x["measurement_package_id"]==package and x["noise_scenario_id"]=="N1"]
        sep=[x for x in rows if x["classification"]=="ROBUSTLY_SEPARATED"]
        rankings.append({"program_id":program,"measurement_package_id":package,"robust_pair_count_n1":len(sep),"minimum_positive_margin":min((x["separation_margin"] for x in sep),default=None),"unresolved_primary_pairs":sum(x["classification"] in {"NUMERICALLY_UNRESOLVED","NOT_COMPARABLE"} for x in rows)})
    packages={x["measurement_package_id"]:x for x in load("MEASUREMENT_PACKAGES.json")["packages"]};progs={x["program_id"]:x for x in load("PRESSURE_PROGRAMS.json")["programs"]}
    rankings.sort(key=lambda x:(-x["robust_pair_count_n1"],-(x["minimum_positive_margin"] or -math.inf),x["unresolved_primary_pairs"],packages[x["measurement_package_id"]]["additional_sensor_class_count"],len(progs[x["program_id"]]["breakpoints"])-2,max(z["pressure_pa_gauge"] for z in progs[x["program_id"]]["breakpoints"]),x["program_id"],x["measurement_package_id"]))
    for i,x in enumerate(rankings,1):x["rank"]=i
    set_cover=select_set_cover(separations)
    reduction=bundle/"reduction";reduction.mkdir();docs={"FEATURE_SUMMARIES.json":{"schema_version":"espresso.whole_pull.sci_ed_001.feature_summaries.v1","rows":primitive},"FAMILY_ENVELOPES.json":{"schema_version":"espresso.whole_pull.sci_ed_001.family_envelopes.v1","rows":envelopes},"PAIRWISE_SEPARATION_MATRIX.json":{"schema_version":"espresso.whole_pull.sci_ed_001.pairwise.v1","rows":separations},"PROGRAM_RANKING.json":{"schema_version":"espresso.whole_pull.sci_ed_001.program_ranking.v1","rows":rankings},"SET_COVER_RESULT.json":{"schema_version":"espresso.whole_pull.sci_ed_001.set_cover.v1","result":set_cover}}
    for name,obj in docs.items():(reduction/name).write_text(canonical(obj))
    return {"status":"PASS","primitive_feature_rows":len(primitive),"family_envelopes":len(envelopes),"pairwise_rows":len(separations),"top_rank":rankings[0],"set_cover":set_cover,"files":{k:sha(reduction/k) for k in docs}}

def main():
    p=argparse.ArgumentParser();sp=p.add_subparsers(dest="cmd",required=True);q=sp.add_parser("replay");q.add_argument("--output")
    q=sp.add_parser("run-row");q.add_argument("--row-id",required=True)
    q=sp.add_parser("execute");q.add_argument("--bundle",required=True);q.add_argument("--authority",required=True)
    q=sp.add_parser("verify-bundle");q.add_argument("--bundle",required=True);q.add_argument("--authority",required=True)
    q=sp.add_parser("reduce");q.add_argument("--bundle",required=True);q.add_argument("--authority",required=True)
    a=p.parse_args()
    if a.cmd=="replay":
        result=replay()
        if a.output:Path(a.output).write_text(canonical(result))
        print(canonical(result),end="")
    elif a.cmd=="run-row":
        row=next(x for x in load("SCI_ED_001_CASE_MATRIX.json")["rows"] if x["row_id"]==a.row_id);print(canonical(run_row(row)),end="")
    elif a.cmd=="execute":print(canonical(execute(a.bundle,a.authority)),end="")
    elif a.cmd=="verify-bundle":print(canonical(verify_bundle(a.bundle,a.authority)),end="")
    else:print(canonical(reduce_bundle(a.bundle,a.authority)),end="")
if __name__=="__main__":main()
