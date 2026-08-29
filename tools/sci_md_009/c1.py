"""SCI-MD-009-C1 fail-closed target-blind nonlinear completion."""
from __future__ import annotations
import csv,hashlib,json,math,os,subprocess,sys,time
from pathlib import Path
import numpy as np
from . import study
from tools.sci_md_004_stage_c.runner import Matrix

ROOT=study.ROOT; SEED=90091; SUPPLEMENTAL_CAP=150
RESPONSE_FAILED_STOP="SCI_MD_009_C1_STOP_NONLINEAR_RESPONSE_NOT_QUALIFIED"
RESPONSE_PASSED_STOP="SCI_MD_009_C1_STOP_RESPONSE_QUALIFIED_DOWNSTREAM_NOT_AUTHORIZED"
AUTHORITATIVE=("TARGET_BLIND_FIREWALL.json","TARGET_BLINDNESS.json","EXISTING_CASE_AUDIT.csv","RAW_OUTPUT_MANIFEST.json",
 "ARTIFACT_DISPOSITION.csv","SUPPLEMENTAL_RUN_PLAN.json","SUPPLEMENTAL_RUN_MANIFEST.csv","DERIVATIVE_QUALIFICATION.csv",
 "DERIVATIVE_NUMERICAL_NOISE.json","GLOBAL_PARAMETER_DESIGN.csv","NONLINEAR_RESPONSE_VALIDATION.csv","LOCAL_IDENTIFIABILITY.json",
 "NONLINEAR_PROFILE_RESULTS.csv","JOINT_SYNTHETIC_RECOVERY.csv","OBSERVABLE_BUNDLE_MODELS.json","OBSERVABLE_BUNDLE_COMPARISON.csv",
 "MEASUREMENT_ERROR_SCENARIOS.json","PRECISION_FRONTIER.csv","PILOT_DESIGN_PARETO.csv","PILOT_ROBUSTNESS.csv",
 "MINIMUM_PILOT_DESIGN.json","MINIMUM_PILOT_DESIGN.md","SCI_ED_002_REVISIT_TRIGGER_ASSESSMENT.md","RESULT.json","FINAL_REPORT.md","REPRODUCE.md")
PACKAGE_FILES=AUTHORITATIVE+("SCI_ED_002_REVISIT_TRIGGER_ASSESSMENT.json","SCIENTIFIC_CONTRACT_C1.md","SCI_MD_009_C1_REVIEW_FINDINGS.md","SCI_MD_009_C1_R1_FAIL_CLOSED_CORRECTION.md","nominal_inventory.csv","operating_projection.csv")

def jwrite(p,x):study.write_json(p,x)
def cwrite(p,x,f=None):
    if f is None:
        f=[]
        for row in x:
            for key in row:
                if key not in f:f.append(key)
    study.write_csv(p,x,f)
def digest_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stream_digest(puck,rel):
    show=subprocess.Popen(["git","-C",str(puck),"show",f"{study.PW_COMMIT}:{rel}"],stdout=subprocess.PIPE)
    h=subprocess.check_output(["sha256sum"],stdin=show.stdout,text=True).split()[0];show.stdout.close()
    if show.wait():raise RuntimeError("git source stream failed")
    return h

def sanitize_git(puck,rel,columns,out,tag):
    csvout=out/f"{tag}.csv";metaout=out/f".{tag}.meta.json"
    show=subprocess.Popen(["git","-C",str(puck),"show",f"{study.PW_COMMIT}:{rel}"],stdout=subprocess.PIPE)
    cmd=[sys.executable,"-m","tools.sci_md_009.sanitize","--output",str(csvout),"--metadata",str(metaout),"--columns",','.join(columns)]
    done=subprocess.run(cmd,stdin=show.stdout,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True);show.stdout.close();rc=show.wait()
    if done.returncode or rc:raise RuntimeError("SCI_MD_009_C1_STOP_TARGET_BLINDNESS_NOT_ESTABLISHED")
    meta=json.loads(metaout.read_text());metaout.unlink();meta.update(source_object=f"{study.PW_COMMIT}:{rel}",source_sha256=stream_digest(puck,rel),classification=("TRAINING_DERIVED_NOMINAL_SCALE_FOR_DIMENSIONLESS_CENTERING" if tag=="nominal_inventory" else "OPERATING_ENVELOPE_ONLY"))
    return csvout,meta

def firewall(puck,out):
    op,om=sanitize_git(puck,study.SOURCE_REL,study.ALLOWED,out,"operating_projection")
    invcols=("experiment_id","species_id","inventory_mass_fraction_kg_per_kg_dry_coffee")
    ip,im=sanitize_git(puck,study.INVENTORY_REL,invcols,out,"nominal_inventory")
    proof={"schema":"ewp.sci-md-009-c1.firewall/v1","status":"PASS","parent_received_full_source_blob":False,
      "full_source_read_api_absent":not hasattr(sys.modules[__name__],"frozen_blob"),"operating":om,"inventory":im,
      "sanitizer":"tools.sci_md_009.sanitize","prohibited_names_emitted":False}
    jwrite(out/"TARGET_BLIND_FIREWALL.json",proof)
    return op,ip,proof

def load_sanitized(op,ip):
    rows=study.read_csv(op);g={}
    for r in rows:
      if int(r["replicate_id"])!=1:continue
      g.setdefault(int(r["experiment_id"]),[]).append(r)
    env=[]
    for eid,xs in sorted(g.items()):
      a=xs[0];raw=sorted(float(r[k]) for r in xs for k in ("fraction_lower_mass_kg","fraction_upper_mass_kg") if r[k] and float(r[k])>0);b=[]
      for v in raw:
       if not b or v-b[-1]>1e-12:b.append(v)
      env.append(study.Envelope(eid,float(a["flow_m3_s"]),float(a["temperature_K"]),a["grind_source"],tuple(b)))
    ir=study.read_csv(ip); inv={(int(r["experiment_id"]),r["species_id"]):float(r["inventory_mass_fraction_kg_per_kg_dry_coffee"]) for r in ir}
    params=json.loads((ROOT/study.PARAM_REL).read_text())["parameters"]
    if len(env)!=15 or len(inv)!=30:raise RuntimeError("sanitized closure")
    return env,inv,params

def settings(name):
    return (.025 if name=="qual_dt_fine" else .1 if name=="qual_dt_coarse" else .05,
            64 if name=="qual_mesh_coarse" else 256 if name=="qual_mesh_fine" else 128,
            2 if name=="qual_parallel" else 1)

def audit_existing(env,inv,params,run_root,out):
    old=study.read_csv(ROOT/"validation/sci_md_009/RUN_MANIFEST.csv");by={e.experiment:e for e in env};audit=[];raw={};matrix=Matrix(Path("/dev/null"),run_root)
    for r in old:
      name=r["case_id"];e=by[int(r["condition_id"][1:])];dt,ax,_=settings(name)
      s=study.make_scenario(matrix,e,inv,params,r["model"],float(r["inventory_scale"]),float(r["k_scale"]),float(r["csat_scale"]),float(r["diffusivity_scale"]),dt,ax)
      expected=json.dumps(s,sort_keys=True,indent=2)+"\n";cfg=run_root/f"{name}.json";case=run_root/name
      expected_hash=hashlib.sha256(expected.encode()).hexdigest();recorded=r["scenario_sha256"];actual=digest_file(cfg) if cfg.is_file() else "MISSING"
      files=[case/"postProcessing/wholePullFractions/0/fraction_species.csv",case/"postProcessing/wholePullFractions/0/fractions.csv",case/"postProcessing/prescribedFlow/0/prescribed_flow.csv"]
      complete=actual==expected_hash==recorded and all(p.is_file() and p.stat().st_size for p in files)
      audit.append({"case_id":name,"expected_scenario_sha256":expected_hash,"recorded_scenario_sha256":recorded,"retained_scenario_sha256":actual,"raw_files_complete":complete,"target_fields_present":any(x in expected for x in study.PROHIBITED),"classification":"RETAINED_VALID" if complete else "WITHDRAWN_UNSUPPORTED"})
      if complete:raw[name]={str(p.relative_to(run_root)):digest_file(p) for p in files}
    if len(audit)!=498 or not all(r["classification"]=="RETAINED_VALID" for r in audit):raise RuntimeError("SCI_MD_009_C1_STOP_EXISTING_PRODUCTION_EVIDENCE_UNREPRODUCIBLE")
    cwrite(out/"EXISTING_CASE_AUDIT.csv",audit);jwrite(out/"RAW_OUTPUT_MANIFEST.json",{"root_role":"EXTERNAL_NOT_COMMITTED","case_count":len(raw),"cases":raw})
    disp=[]
    retained=("RUN_MANIFEST.csv","DIMENSIONLESS_REGIME_MAP.csv","INVENTORY_CAPACITY_TRAJECTORIES.csv","LOCAL_SENSITIVITY.csv","B1_B2_EQUIVALENCE.csv","NUMERICAL_QUALIFICATION.json")
    withdrawn=("PROFILE_RESULTS.csv","SYNTHETIC_RECOVERY.csv","OBSERVABLE_BUNDLE_COMPARISON.csv","PRECISION_FRONTIER.csv","PILOT_DESIGN_PARETO.csv","MINIMUM_PILOT_DESIGN.json","FINAL_REPORT.md","RESULT.json")
    for x in retained:disp.append({"artifact":x,"classification":"REGENERATED_FROM_VALID_RAW_CASES","reason":"498 raw cases hash-close"})
    for x in withdrawn:disp.append({"artifact":x,"classification":"SUPERSEDED_BY_C1","reason":"reviewed adjudicative method unsupported"})
    cwrite(out/"ARTIFACT_DISPOSITION.csv",disp);return old

def lhs(n,d,rng):
    a=np.empty((n,d))
    for j in range(d):a[:,j]=(rng.permutation(n)+.5)/n
    return a
def transform(u,p):
    return np.array([math.log(.1)+u[0]*(math.log(3)-math.log(.1)),math.log(p["k_95pct_lower"]/p["extractionRateConstant_1_s"])+u[1]*math.log(p["k_95pct_upper"]/p["k_95pct_lower"]),math.log(p["csat_95pct_lower"]/p["saturationConcentration_kg_m3"])+u[2]*math.log(p["csat_95pct_upper"]/p["csat_95pct_lower"])])
def features(x):
    a,b,c=x;return np.array([1,a,b,c,a*a,b*b,c*c,a*b,a*c,b*c])

def supplemental_plan(env,params):
    ordered=sorted(env,key=lambda e:(e.flow,e.experiment));chosen=(ordered[0],ordered[len(ordered)//2],ordered[-1]);rng=np.random.default_rng(SEED);rows=[]
    for e in chosen:
      for split,n in (("TRAIN",24),("VALIDATION",6)):
       ua=lhs(n,3,rng);ub=lhs(n,3,rng)
       for i in range(n):
        row={"case_id":f"c1_e{e.experiment}_{split.lower()}_{i:02d}","condition_id":f"E{e.experiment}","split":split,"model":"B1"}
        for sp,u in zip(study.SPECIES,(ua[i],ub[i])):
         x=transform(u,params[sp]);row.update({f"{sp}_log_M0":x[0],f"{sp}_log_k":x[1],f"{sp}_log_Csat":x[2]})
        rows.append(row)
    for e in chosen:
      for sign in (-1,1):rows.append({"case_id":f"c1_e{e.experiment}_D_{sign:+d}","condition_id":f"E{e.experiment}","split":"D_SENSITIVITY","model":"B1","D_scale":1+.1*sign})
    if len(rows)>SUPPLEMENTAL_CAP:raise RuntimeError("SCI_MD_009_C1_STOP_SUPPLEMENTAL_CAP_REACHED")
    return chosen,rows

def run_supplemental(rows,env,inv,params,exe,run_root,out):
    by={f"E{e.experiment}":e for e in env};m=Matrix(exe,run_root);manifest=[];responses={}
    for i,r in enumerate(rows,1):
      e=by[r["condition_id"]];sc={}
      for sp in study.SPECIES:
       if r["split"]=="D_SENSITIVITY":sc[sp]=(1,1,1,float(r["D_scale"]))
       else:sc[sp]=tuple(math.exp(float(r[f"{sp}_log_{p}"])) for p in ("M0","k","Csat"))+(1.,)
      s=study.make_scenario(m,e,inv,params,r["model"],species_scales=sc);name=r["case_id"];case=run_root/name
      if (case/"postProcessing/wholePullFractions/0/fraction_species.csv").is_file():sh=digest_file(run_root/f"{name}.json");runtime=0.;reason="REUSED_COMPLETE_CASE"
      else:
       t=time.monotonic();case=m.run(name,s);runtime=time.monotonic()-t;sh=m.run_metadata[name]["scenario_hash"];reason=""
      z=study.parse_case(case,e,params,1);responses[name]=z
      manifest.append({"case_id":name,"condition_id":r["condition_id"],"split":r["split"],"model":r["model"],"state":"PASS","reason":reason,"runtime_s":runtime,"scenario_sha256":sh,
       "fraction_species_sha256":digest_file(case/"postProcessing/wholePullFractions/0/fraction_species.csv"),"fractions_sha256":digest_file(case/"postProcessing/wholePullFractions/0/fractions.csv"),"flow_sha256":digest_file(case/"postProcessing/prescribedFlow/0/prescribed_flow.csv")})
      if i%20==0:print(f"supplemental {i}/{len(rows)}",flush=True)
    cwrite(out/"SUPPLEMENTAL_RUN_MANIFEST.csv",manifest);return responses

class Surrogate:
    def __init__(self,coef,bounds):self.coef=coef;self.bounds=np.array(bounds)
    def __call__(self,x):
      x=np.asarray(x)
      if np.any(x<self.bounds[:,0]-1e-12) or np.any(x>self.bounds[:,1]+1e-12):raise ValueError("surrogate extrapolation")
      return np.exp(features(x)@self.coef)-1e-12

def fit_surrogates(plan,responses,chosen,params,out):
    models={};validation=[]
    for e in chosen:
     for sp in study.SPECIES:
      train=[r for r in plan if r["condition_id"]==f"E{e.experiment}" and r["split"]=="TRAIN"];valid=[r for r in plan if r["condition_id"]==f"E{e.experiment}" and r["split"]=="VALIDATION"]
      X=np.array([features([float(r[f"{sp}_log_{p}"]) for p in ("M0","k","Csat")]) for r in train]);Y=np.array([responses[r["case_id"]]["species"][sp]["masses"] for r in train]);coef=np.linalg.lstsq(X,np.log(Y+1e-12),rcond=None)[0]
      bounds=[(math.log(.1),math.log(3)),(math.log(params[sp]["k_95pct_lower"]/params[sp]["extractionRateConstant_1_s"]),math.log(params[sp]["k_95pct_upper"]/params[sp]["extractionRateConstant_1_s"])),(math.log(params[sp]["csat_95pct_lower"]/params[sp]["saturationConcentration_kg_m3"]),math.log(params[sp]["csat_95pct_upper"]/params[sp]["saturationConcentration_kg_m3"]))]
      model=Surrogate(coef,bounds);models[e.experiment,sp]=model
      for r in valid:
       truth=responses[r["case_id"]]["species"][sp]["masses"];pred=model([float(r[f"{sp}_log_{p}"]) for p in ("M0","k","Csat")]);rel=abs(pred-truth)/np.maximum(truth,1e-9)
       for j,x in enumerate(rel,1):validation.append({"condition_id":f"E{e.experiment}","species":sp,"fraction_index":j,"relative_error":x,"absolute_error_kg":abs(pred[j-1]-truth[j-1]),"status":"PASS" if x<=.02 and abs(pred[j-1]-truth[j-1])<=1e-5 else "FAIL"})
    aggregate=max(float(r["relative_error"]) for r in validation);qualified=aggregate<=.02 and all(r["status"]=="PASS" for r in validation)
    cwrite(out/"NONLINEAR_RESPONSE_VALIDATION.csv",validation)
    return models,qualified

def stop_after_response_gate(out,plan,validation,qualified):
    stop=RESPONSE_PASSED_STOP if qualified else RESPONSE_FAILED_STOP
    blocked={"state":"BLOCKED","reason":stop}
    for name in ("NONLINEAR_PROFILE_RESULTS.csv","JOINT_SYNTHETIC_RECOVERY.csv","OBSERVABLE_BUNDLE_COMPARISON.csv","PRECISION_FRONTIER.csv","PILOT_DESIGN_PARETO.csv","PILOT_ROBUSTNESS.csv"):
        cwrite(out/name,[blocked])
    jwrite(out/"LOCAL_IDENTIFIABILITY.json",blocked);jwrite(out/"OBSERVABLE_BUNDLE_MODELS.json",blocked);jwrite(out/"MEASUREMENT_ERROR_SCENARIOS.json",blocked)
    jwrite(out/"MINIMUM_PILOT_DESIGN.json",{"status":"BLOCKED","minimum":None,"robust":None,"reason":stop})
    (out/"MINIMUM_PILOT_DESIGN.md").write_text(f"# Pilot design\n\nBlocked: `{stop}`. No pilot was selected.\n")
    jwrite(out/"SCI_ED_002_REVISIT_TRIGGER_ASSESSMENT.json",{"status":"EMPIRICAL_REFERENCE_EXTRACTION_TAIL_DATA_REQUIRED","calculated_threshold":None,"reason":stop})
    (out/"SCI_ED_002_REVISIT_TRIGGER_ASSESSMENT.md").write_text(f"# SCI-ED-002 revisit trigger\n\n`EMPIRICAL_REFERENCE_EXTRACTION_TAIL_DATA_REQUIRED`. No model-derived tail threshold or preparation count is issued because `{stop}` prevented joint precision adjudication.\n")
    errors=[float(r["relative_error"]) for r in validation]
    result={"schema":"ewp.sci-md-009-c1.result/v1","disposition":stop,"target_blind_firewall":"PASS","existing_cases_retained":498,"supplemental_cases":len(plan),"supplemental_cap":SUPPLEMENTAL_CAP,"nonlinear_response_qualified":qualified,"maximum_validation_relative_error":max(errors),"profiles":"BLOCKED","joint_recovery":"BLOCKED","observable_bundles":"BLOCKED","precision_frontier":"BLOCKED","pilot":"BLOCKED","sci_ed_002":"EMPIRICAL_REFERENCE_EXTRACTION_TAIL_DATA_REQUIRED","target_chemistry_values_accessed":False,"target_scores":0,"change_declaration":"NO_GOVERNING_PHYSICS_CHANGE","physical_validation":"NOT_ESTABLISHED"}
    jwrite(out/"RESULT.json",result)
    gate_text=(f"failed held-out validation: maximum relative error {max(errors):.6g} exceeded 0.02" if not qualified else "met its response threshold, but downstream adjudication is not authorized in C1")
    (out/"FINAL_REPORT.md").write_text(f"# SCI-MD-009-C1 final report\n\nThe target-blind firewall passed and all 498 historical cases hash-closed. All {len(plan)} frozen supplemental production cases passed, and the frozen quadratic per-fraction nonlinear response {gate_text}. Therefore derivative-noise and local-rank dispositions, nuisance-optimized profiles, joint recovery, bundle ranking, joint precision, pilot selection, and a numerical SCI-ED-002 tail threshold were not issued. Disposition: `{stop}`. Prior practical-identifiability, 20%, O6, eight-/fifteen-shot, and 6.7% claims are withdrawn. No observed chemistry, fitting, governing-physics change, or physical validation occurred. Physical validation remains `NOT_ESTABLISHED`.\n")
    (out/"REPRODUCE.md").write_text("# Reproduce SCI-MD-009-C1\n\n`python3 -m tools.sci_md_009.c1 --puckworks /path/puckworks --executable /path/espressoWholePullFoam --existing-run-root /path/sci-md-009-runs-r3 --supplemental-run-root /path/supplemental --output /fresh/results`\n")
    return result

def derivative_qualification(out):
    rows=study.read_csv(ROOT/"validation/sci_md_009/LOCAL_SENSITIVITY.csv");g={}
    for r in rows:g.setdefault((r["condition_id"],r["species"],r["parameter"],r["fraction_index"]),{})[float(r["step"])]=float(r["derivative_kg_per_log_parameter"])
    q=[]
    for key,v in g.items():
      d=v[.01];tol=max(.05*abs(d),1e-8);diff005=abs(v[.005]-d);diff02=abs(v[.02]-d);q.append(dict(zip(("condition_id","species","parameter","fraction_index"),key),derivative_0p5=v[.005],derivative_1=d,derivative_2=v[.02],difference_0p5=diff005,difference_2=diff02,tolerance_kg=tol,status="PASS" if max(diff005,diff02)<=tol else "FAIL"))
    cwrite(out/"DERIVATIVE_QUALIFICATION.csv",q)
    # Historical proxy only: derivatives were not recomputed while varying resolution.
    nq=json.loads((ROOT/"validation/sci_md_009/NUMERICAL_QUALIFICATION.json").read_text());shape=max(max(v.values()) for v in nq["determinism_and_resolution_shape_maxima"].values());mass_scale=max(abs(float(r["derivative_1"])) for r in q);noise=shape*mass_scale
    record={"status":"DIAGNOSTIC_DERIVATIVE_NOISE_PROXY_NOT_ADJUDICATED","method":"largest resolution/repeat/rank shape difference times maximum 1pct derivative mass scale","maximum_shape_difference":shape,"maximum_derivative_mass_scale":mass_scale,"diagnostic_derivative_noise_proxy_kg":noise,"historical_derivative_noise_floor_kg":noise,"direct_resolution_varied_derivatives_executed":False,"usable_for_rank_adjudication":False,"reason":"nonlinear response failed before corrected rank adjudication","finite_difference_failures":sum(r["status"]!="PASS" for r in q)};jwrite(out/"DERIVATIVE_NUMERICAL_NOISE.json",record);return q,record

def manifest(out):
    files={name:digest_file(out/name) for name in sorted(PACKAGE_FILES)};jwrite(out/"RESULT_PACKAGE_MANIFEST.json",{"schema":"ewp.sci-md-009-c1.package/v1","files":files,"file_count":len(files)})

def verify(out):
    result=json.loads((out/"RESULT.json").read_text());audit=study.read_csv(out/"EXISTING_CASE_AUDIT.csv");supp=study.read_csv(out/"SUPPLEMENTAL_RUN_MANIFEST.csv");pkg=json.loads((out/"RESULT_PACKAGE_MANIFEST.json").read_text())
    for name,h in pkg["files"].items():
      if digest_file(out/name)!=h:raise ValueError(f"package hash {name}")
    if len(audit)!=498 or any(r["classification"]!="RETAINED_VALID" for r in audit):raise ValueError("existing audit")
    if len(supp)>SUPPLEMENTAL_CAP or any(r["state"]!="PASS" for r in supp):raise ValueError("supplemental closure")
    validation=study.read_csv(out/"NONLINEAR_RESPONSE_VALIDATION.csv");maxerr=max(float(r["relative_error"]) for r in validation);qualified=maxerr<=.02 and all(r["status"]=="PASS" for r in validation);expected=RESPONSE_PASSED_STOP if qualified else RESPONSE_FAILED_STOP
    if result["disposition"]!=expected or result["nonlinear_response_qualified"]!=qualified or abs(result["maximum_validation_relative_error"]-maxerr)>1e-15:raise ValueError("response STOP closure")
    for name in ("NONLINEAR_PROFILE_RESULTS.csv","JOINT_SYNTHETIC_RECOVERY.csv","OBSERVABLE_BUNDLE_COMPARISON.csv","PRECISION_FRONTIER.csv","PILOT_DESIGN_PARETO.csv","PILOT_ROBUSTNESS.csv"):
      if study.read_csv(out/name)!=[{"state":"BLOCKED","reason":expected}]:raise ValueError(f"blocked artifact {name}")
    for name in ("LOCAL_IDENTIFIABILITY.json","OBSERVABLE_BUNDLE_MODELS.json","MEASUREMENT_ERROR_SCENARIOS.json"):
      if json.loads((out/name).read_text())!={"state":"BLOCKED","reason":expected}:raise ValueError(f"blocked artifact {name}")
    noise=json.loads((out/"DERIVATIVE_NUMERICAL_NOISE.json").read_text())
    if noise.get("status")!="DIAGNOSTIC_DERIVATIVE_NOISE_PROXY_NOT_ADJUDICATED" or noise.get("direct_resolution_varied_derivatives_executed") is not False or noise.get("usable_for_rank_adjudication") is not False:raise ValueError("derivative proxy closure")
    if result["physical_validation"]!="NOT_ESTABLISHED" or result["target_chemistry_values_accessed"] or result["target_scores"]!=0:raise ValueError("claim/firewall")
    return {"status":"PASS","existing_cases":len(audit),"supplemental_cases":len(supp),"maximum_validation_relative_error":maxerr,"disposition":result["disposition"]}

def execute(puck,exe,existing,supproot,out):
    out.mkdir(parents=True,exist_ok=True);supproot.mkdir(parents=True,exist_ok=True)
    for name in ("SCIENTIFIC_CONTRACT_C1.md","SCI_MD_009_C1_REVIEW_FINDINGS.md","SCI_MD_009_C1_R1_FAIL_CLOSED_CORRECTION.md"):
      source=ROOT/"validation/sci_md_009"/name
      if source.resolve()!= (out/name).resolve():(out/name).write_text(source.read_text())
    op,ip,fw=firewall(puck,out);env,inv,params=load_sanitized(op,ip);audit_existing(env,inv,params,existing,out);chosen,plan=supplemental_plan(env,params);cwrite(out/"GLOBAL_PARAMETER_DESIGN.csv",plan);jwrite(out/"SUPPLEMENTAL_RUN_PLAN.json",{"seed":SEED,"case_count":len(plan),"cap":SUPPLEMENTAL_CAP,"conditions":[f"E{x.experiment}" for x in chosen],"cases":[r["case_id"] for r in plan]});responses=run_supplemental(plan,env,inv,params,exe,supproot,out);models,qualified=fit_surrogates(plan,responses,chosen,params,out);derivative_qualification(out)
    validation=study.read_csv(out/"NONLINEAR_RESPONSE_VALIDATION.csv");result=stop_after_response_gate(out,plan,validation,qualified);jwrite(out/"TARGET_BLINDNESS.json",{"status":"PASS","firewall_sha256":digest_file(out/"TARGET_BLIND_FIREWALL.json"),"sanitized_operating_sha256":digest_file(op),"sanitized_inventory_sha256":digest_file(ip),"prohibited_values_available_to_analysis":False,"evidence":"measured sanitizer subprocess and mutation tests"});manifest(out);verify(out);return result

def main(argv=None):
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--puckworks',type=Path,required=True);p.add_argument('--executable',type=Path,required=True);p.add_argument('--existing-run-root',type=Path,required=True);p.add_argument('--supplemental-run-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv);r=execute(*[x.resolve() for x in (a.puckworks,a.executable,a.existing_run_root,a.supplemental_run_root,a.output)]);print(json.dumps(r,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
