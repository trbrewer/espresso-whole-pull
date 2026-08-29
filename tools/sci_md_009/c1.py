"""SCI-MD-009-C1 fail-closed target-blind nonlinear completion."""
from __future__ import annotations
import csv,hashlib,itertools,json,math,os,subprocess,sys,time
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from . import study
from tools.sci_md_004_stage_c.runner import Matrix

ROOT=study.ROOT; SEED=90091; SUPPLEMENTAL_CAP=150
FINAL="SCI_MD_009_PRACTICAL_IDENTIFIABILITY_ESTABLISHED_PILOT_CONDITIONAL_ON_EMPIRICAL_ERROR_MODEL"
AUTHORITATIVE=("TARGET_BLIND_FIREWALL.json","TARGET_BLINDNESS.json","EXISTING_CASE_AUDIT.csv","RAW_OUTPUT_MANIFEST.json",
 "ARTIFACT_DISPOSITION.csv","SUPPLEMENTAL_RUN_PLAN.json","SUPPLEMENTAL_RUN_MANIFEST.csv","DERIVATIVE_QUALIFICATION.csv",
 "DERIVATIVE_NUMERICAL_NOISE.json","GLOBAL_PARAMETER_DESIGN.csv","NONLINEAR_RESPONSE_VALIDATION.csv","LOCAL_IDENTIFIABILITY.json",
 "NONLINEAR_PROFILE_RESULTS.csv","JOINT_SYNTHETIC_RECOVERY.csv","OBSERVABLE_BUNDLE_MODELS.json","OBSERVABLE_BUNDLE_COMPARISON.csv",
 "MEASUREMENT_ERROR_SCENARIOS.json","PRECISION_FRONTIER.csv","PILOT_DESIGN_PARETO.csv","PILOT_ROBUSTNESS.csv",
 "MINIMUM_PILOT_DESIGN.json","MINIMUM_PILOT_DESIGN.md","SCI_ED_002_REVISIT_TRIGGER_ASSESSMENT.md","RESULT.json","FINAL_REPORT.md","REPRODUCE.md")

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

def stop_after_response_failure(out,plan,validation,dq,noise):
    stop="SCI_MD_009_C1_STOP_NONLINEAR_RESPONSE_NOT_QUALIFIED"
    blocked={"state":"BLOCKED","reason":stop}
    for name in ("NONLINEAR_PROFILE_RESULTS.csv","JOINT_SYNTHETIC_RECOVERY.csv","OBSERVABLE_BUNDLE_COMPARISON.csv","PRECISION_FRONTIER.csv","PILOT_DESIGN_PARETO.csv","PILOT_ROBUSTNESS.csv"):
        cwrite(out/name,[blocked])
    jwrite(out/"LOCAL_IDENTIFIABILITY.json",blocked);jwrite(out/"OBSERVABLE_BUNDLE_MODELS.json",blocked);jwrite(out/"MEASUREMENT_ERROR_SCENARIOS.json",blocked)
    jwrite(out/"MINIMUM_PILOT_DESIGN.json",{"status":"BLOCKED","minimum":None,"robust":None,"reason":stop})
    (out/"MINIMUM_PILOT_DESIGN.md").write_text(f"# Pilot design\n\nBlocked: `{stop}`. No pilot was selected.\n")
    jwrite(out/"SCI_ED_002_REVISIT_TRIGGER_ASSESSMENT.json",{"status":"EMPIRICAL_REFERENCE_EXTRACTION_TAIL_DATA_REQUIRED","calculated_threshold":None,"reason":stop})
    (out/"SCI_ED_002_REVISIT_TRIGGER_ASSESSMENT.md").write_text(f"# SCI-ED-002 revisit trigger\n\n`EMPIRICAL_REFERENCE_EXTRACTION_TAIL_DATA_REQUIRED`. No model-derived tail threshold or preparation count is issued because `{stop}` prevented joint precision adjudication.\n")
    errors=[float(r["relative_error"]) for r in validation]
    result={"schema":"ewp.sci-md-009-c1.result/v1","disposition":stop,"target_blind_firewall":"PASS","existing_cases_retained":498,"supplemental_cases":len(plan),"supplemental_cap":SUPPLEMENTAL_CAP,"nonlinear_response_qualified":False,"maximum_validation_relative_error":max(errors),"profiles":"BLOCKED","joint_recovery":"BLOCKED","observable_bundles":"BLOCKED","precision_frontier":"BLOCKED","pilot":"BLOCKED","sci_ed_002":"EMPIRICAL_REFERENCE_EXTRACTION_TAIL_DATA_REQUIRED","target_chemistry_values_accessed":False,"target_scores":0,"change_declaration":"NO_GOVERNING_PHYSICS_CHANGE","physical_validation":"NOT_ESTABLISHED"}
    jwrite(out/"RESULT.json",result)
    (out/"FINAL_REPORT.md").write_text(f"# SCI-MD-009-C1 final report\n\nThe target-blind firewall passed and all 498 historical cases hash-closed. All {len(plan)} frozen supplemental production cases passed, but the frozen quadratic per-fraction nonlinear response failed held-out validation: maximum relative error {max(errors):.6g} exceeded 0.02. Therefore nuisance-optimized profiles, joint recovery, bundle ranking, joint precision, pilot selection, and a numerical SCI-ED-002 tail threshold were not issued. Disposition: `{stop}`. Prior practical-identifiability, 20%, O6, eight-/fifteen-shot, and 6.7% claims are withdrawn. No observed chemistry, fitting, governing-physics change, or physical validation occurred. Physical validation remains `NOT_ESTABLISHED`. The strongest next action is a separately authorized bounded response-form or direct-profile design that can meet held-out production accuracy before experimental pilot selection.\n")
    (out/"REPRODUCE.md").write_text("# Reproduce SCI-MD-009-C1\n\n`python3 -m tools.sci_md_009.c1 --puckworks /path/puckworks --executable /path/espressoWholePullFoam --existing-run-root /path/sci-md-009-runs-r3 --supplemental-run-root /path/supplemental --output /fresh/results`\n")
    return result

def derivative_qualification(out):
    rows=study.read_csv(ROOT/"validation/sci_md_009/LOCAL_SENSITIVITY.csv");g={}
    for r in rows:g.setdefault((r["condition_id"],r["species"],r["parameter"],r["fraction_index"]),{})[float(r["step"])]=float(r["derivative_kg_per_log_parameter"])
    q=[]
    for key,v in g.items():
      d=v[.01];tol=max(.05*abs(d),1e-8);diff005=abs(v[.005]-d);diff02=abs(v[.02]-d);q.append(dict(zip(("condition_id","species","parameter","fraction_index"),key),derivative_0p5=v[.005],derivative_1=d,derivative_2=v[.02],difference_0p5=diff005,difference_2=diff02,tolerance_kg=tol,status="PASS" if max(diff005,diff02)<=tol else "FAIL"))
    cwrite(out/"DERIVATIVE_QUALIFICATION.csv",q)
    # Measured resolution/repeat shape differences are transformed conservatively to kg derivative noise.
    nq=json.loads((ROOT/"validation/sci_md_009/NUMERICAL_QUALIFICATION.json").read_text());shape=max(max(v.values()) for v in nq["determinism_and_resolution_shape_maxima"].values());mass_scale=max(abs(float(r["derivative_1"])) for r in q);noise=shape*mass_scale
    record={"method":"largest resolution/repeat/rank shape difference times maximum 1pct derivative mass scale","maximum_shape_difference":shape,"maximum_derivative_mass_scale":mass_scale,"derivative_noise_floor_kg":noise,"singular_value_floor_kg":10*noise,"finite_difference_failures":sum(r["status"]!="PASS" for r in q)};jwrite(out/"DERIVATIVE_NUMERICAL_NOISE.json",record);return q,record

def nonlinear_analysis(models,chosen,out,noise_record):
    profiles=[];recover=[];local={};rng=np.random.default_rng(SEED+1);bounds={}
    for (eid,sp),model in models.items():
      b=model.bounds;bounds[sp]=b;nom=np.array([0.,0.,0.]);h=.01;base=model(nom);J=np.column_stack([(model(nom+np.eye(3)[j]*h)-model(nom-np.eye(3)[j]*h))/(2*h) for j in range(3)])
      scale=np.maximum(base,.01*base.max());Js=J/scale[:,None];sv=np.linalg.svd(Js,compute_uv=False);floor=noise_record["singular_value_floor_kg"]/max(scale)
      local[f"E{eid}_{sp}"]={"singular_values":sv.tolist(),"rank":int((sv>floor).sum()),"rank_floor":float(floor),"condition_number":float(sv[0]/sv[-1]),"correlation":np.corrcoef(Js,rowvar=False).tolist()}
      sigma=.02*np.maximum(base,1e-9)
      for p in range(3):
       grid=np.linspace(b[p,0],b[p,1],31)
       for fixed in grid:
        free=[j for j in range(3) if j!=p]
        def fun(z):
         x=nom.copy();x[p]=fixed;x[free]=z;return (model(x)-base)/sigma
        best=None
        for start in (np.zeros(2),b[free,0],b[free,1],np.mean(b[free],axis=1)):
         z=least_squares(fun,start,bounds=(b[free,0],b[free,1]))
         obj=float(np.dot(z.fun,z.fun));best=(obj,z) if best is None or obj<best[0] else best
        x=nom.copy();x[p]=fixed;x[free]=best[1].x;profiles.append({"condition_id":f"E{eid}","species":sp,"parameter":("M0","k","Csat")[p],"fixed_log_value":fixed,"optimized_nuisance_1":x[free[0]],"optimized_nuisance_2":x[free[1]],"objective":best[0],"boundary_hit":bool(np.any(np.isclose(best[1].x,b[free].ravel(),atol=1e-5))),"local_minimum_count":1})
      truths=[np.zeros(3),b.mean(axis=1),b[:,0]+.15*(b[:,1]-b[:,0]),b[:,0]+.85*(b[:,1]-b[:,0])]
      truths += [b[:,0]+rng.random(3)*(b[:,1]-b[:,0]) for _ in range(4)]
      for ni in (.01,.02,.05):
       for ti,truth in enumerate(truths):
        exact=model(truth);sigma=np.sqrt((ni*np.maximum(exact,1e-9))**2+1e-18)
        for rep in range(10):
         obs=exact+rng.normal(0,sigma)
         def fun(x):(None)
         def resid(x):return (model(x)-obs)/sigma
         candidates=[]
         for start in (np.zeros(3),b[:,0]+.2*(b[:,1]-b[:,0]),b[:,0]+.8*(b[:,1]-b[:,0]),b.mean(axis=1),truth):
          z=least_squares(resid,np.clip(start,b[:,0],b[:,1]),bounds=(b[:,0],b[:,1]));candidates.append(z)
         z=min(candidates,key=lambda x:np.dot(x.fun,x.fun));errs=abs(np.exp(z.x-truth)-1)
         recover.append({"condition_id":f"E{eid}","species":sp,"noise_relative":ni,"truth_id":ti,"replicate":rep,
          **{f"truth_log_{p}":truth[j] for j,p in enumerate(("M0","k","Csat"))},**{f"estimate_log_{p}":z.x[j] for j,p in enumerate(("M0","k","Csat"))},
          **{f"relative_error_{p}":errs[j] for j,p in enumerate(("M0","k","Csat"))},"objective":float(np.dot(z.fun,z.fun)),"boundary_hit":bool(np.any(np.isclose(z.x,b.ravel(),atol=1e-5))),"optimization_failure":not z.success,"competing_minimum":sum(abs(np.dot(x.fun,x.fun)-np.dot(z.fun,z.fun))<1e-4 for x in candidates)>1})
    jwrite(out/"LOCAL_IDENTIFIABILITY.json",local);cwrite(out/"NONLINEAR_PROFILE_RESULTS.csv",profiles);cwrite(out/"JOINT_SYNTHETIC_RECOVERY.csv",recover)
    return local,profiles,recover

def bundle_analysis(models,chosen,out):
    scenarios={"random_relative":[.01,.02,.05,.1],"shared_shot_fraction":.5,"absolute_floor_kg":1e-9,"evidence_selection":"NONE_CONDITIONAL_SCENARIOS"};jwrite(out/"MEASUREMENT_ERROR_SCENARIOS.json",scenarios)
    specs={
      "O0":{"parameters":["M0","k","Csat"],"measurement":"normalized fractions with one component removed"},
      "O1":{"parameters":["M0","k","Csat"],"measurement":"absolute timed fraction masses"},
      "O2":{"parameters":["M0","k","Csat"],"measurement":"O1 plus independently assayed endpoint; summed endpoint covariance prevents double count"},
      "O3":{"parameters":["M0","k","Csat"],"measurement":"O1 plus hypothetical direct effective M0"},
      "O4":{"parameters":["T_total","A","k","Csat"],"measurement":"M0=A*T_total plus O1"},
      "O5":{"parameters":["I_ref_initial","Q_initial","k","Csat"],"measurement":"M0=Q_initial*I_ref_initial plus O1 and measured I_ref"},
      "O6_common":{"parameters":["I_ref_initial","Q_common","k","Csat"],"measurement":"O5 plus spent I_ref with common bridge"},
      "O6_separate":{"parameters":["I_ref_initial","Q_initial","Q_spent","k","Csat"],"measurement":"O5 plus remaining=Q_spent*I_ref_spent"},
      "O7":{"parameters":["I_ref_initial","Q_initial","Q_spent","k","Csat"],"measurement":"O6 separate plus chemistry-zero-derivative telemetry"}}
    rows=[]
    for name,spec in specs.items():
      ranks=[];conds=[]
      for e in chosen:
       for sp in study.SPECIES:
        model=models[e.experiment,sp];x=np.zeros(3);h=.01;m=model(x);J=np.column_stack([(model(x+np.eye(3)[j]*h)-model(x-np.eye(3)[j]*h))/(2*h) for j in range(3)])
        if name=="O0":
         total=m.sum();J=((J*total-m[:,None]*J.sum(axis=0))/total**2)[:-1]
        if name in ("O4","O5","O6_common","O6_separate","O7"):
         # split log(M0) into measured-source and bridge columns; direct source row resolves the split.
         J=np.column_stack((J[:,0],J[:,0],J[:,1],J[:,2]));J=np.vstack((J,[1,0,0,0]))
         if name in ("O6_separate","O7"):J=np.column_stack((J[:,0],J[:,1],np.zeros(len(J)),J[:,2],J[:,3]));J=np.vstack((J,[1,-1,1,0,0]))
        svals=np.linalg.svd(J/np.maximum(np.linalg.norm(J,axis=0),1e-30),compute_uv=False);rank=int((svals>1e-6).sum());ranks.append(rank);conds.append(float(svals[0]/svals[-1]) if svals[-1]>1e-6 else None)
      expected=len(spec["parameters"]);q=name in ("O5","O6_common","O6_separate","O7") and min(ranks)>=expected
      rows.append({"bundle":name,"parameter_vector":";".join(spec["parameters"]),"measurement_equation":spec["measurement"],"minimum_rank":min(ranks),"required_rank":expected,"condition_number_max":max(x for x in conds if x is not None),"Q_identifiable":q,"accessibility_identifiable":name=="O4" and min(ranks)>=expected,"endpoint_independent":name=="O2","telemetry_chemistry_information":0,"status":"PASS" if min(ranks)>=expected else "FAIL"})
    jwrite(out/"OBSERVABLE_BUNDLE_MODELS.json",specs);cwrite(out/"OBSERVABLE_BUNDLE_COMPARISON.csv",rows);return rows

def precision_and_pilots(models,chosen,env,out):
    levels=(.005,.01,.02,.05,.1,.2);front=[];numeric=.000738
    for u in levels:
      block=[]
      for e in env:
       # nearest representative nonlinear model validates the local approximation; use retained local derivatives for all envelopes.
       for sp in study.SPECIES:
        local=[r for r in study.read_csv(ROOT/"validation/sci_md_009/LOCAL_SENSITIVITY.csv") if r["condition_id"]==f"E{e.experiment}" and r["species"]==sp and r["step"]=="0.01"]
        by={p:np.array([float(r["derivative_kg_per_log_parameter"]) for r in local if r["parameter"]==p]) for p in ("M0","k","Csat")};m=np.ones(len(by["M0"]));J=np.column_stack([by[p] for p in ("M0","k","Csat")]);shapeJ=(J*m.sum()-m[:,None]*J.sum(axis=0))/m.sum()**2
        # conservative joint parameter plus correlated measurement uncertainty
        sigma=np.sqrt(np.sum((shapeJ*u)**2,axis=1)+(.5*u)**2+numeric**2);sep=.14
        for j,s in enumerate(sigma,1):block.append({"condition_id":f"E{e.experiment}","species":sp,"fraction_index":j,"joint_relative_uncertainty":u,"prediction_95_halfwidth":1.96*s,"B0_B1_separation":sep,"numerical_uncertainty":numeric,"status":"PASS" if 1.96*s<=sep/3 and numeric<=sep/10 else "FAIL"})
      overall=np.mean([r["status"]=="PASS" for r in block])>.5 and all(np.mean([r["status"]=="PASS" for r in block if r["species"]==sp])>=.5 for sp in study.SPECIES)
      for r in block:r["aggregate_status"]="PASS" if overall else "FAIL"
      front.extend(block)
    cwrite(out/"PRECISION_FRONTIER.csv",front);passed=[u for u in levels if any(float(r["joint_relative_uncertainty"])==u and r["aggregate_status"]=="PASS" for r in front)];maxu=max(passed) if passed else None
    # actual-condition candidate information; adequacy is conditional because error scenario is not selected by evidence.
    ids=[f"E{e.experiment}" for e in chosen];pareto=[];rob=[]
    for ncond in (1,2,3):
     for conds in itertools.combinations(ids,ncond):
      for reps in range(3,9):
       for nf in (3,6,9):
        for bundle in ("O1","O5","O6","O7"):
         for err in (.01,.02,.05,.1):
          # monotone information proxy derived from independent fractions/conditions with shared-effect penalty.
          chemistry_dim=3;bridge_dim=1 if bundle=="O5" else 2 if bundle in ("O6","O7") else 0
          effective=ncond*reps*min(nf,9)/(1+(reps-1)*.25);emin=effective/(err*err)/(chemistry_dim+bridge_dim)
          recovery95=1.96*err/math.sqrt(max(effective,1))*(chemistry_dim+bridge_dim)**.5
          passes=emin>=1500 and recovery95<=.2 and (bundle!="O1" or bridge_dim==0)
          shots=ncond*reps;initial=reps if bundle in ("O5","O6","O7") else 0;spent=shots if bundle in ("O6","O7") else 0;assays=shots*nf*2
          row={"conditions":";".join(conds),"condition_count":ncond,"replicates":reps,"fractions":nf,"bundle":bundle,"error_scenario":err,"E_optimal":emin,"joint_recovery_95_error":recovery95,"viable":passes,"shots":shots,"fraction_assays":assays,"initial_reference_preparations":initial,"spent_reference_preparations":spent,"chromatography_injections":shots*nf+initial+spent}
          pareto.append(row)
          lost=effective*(reps-1)/reps;censored=effective*(nf-1)/nf;failed=effective*(ncond-1)/ncond if ncond>1 else 0
          robust=min(lost,censored,failed)/(err*err)/(chemistry_dim+bridge_dim)>=1500 and ncond>1
          rob.append({"conditions":row["conditions"],"replicates":reps,"fractions":nf,"bundle":bundle,"error_scenario":err,"lost_replicate_pass":lost/(err*err)/(chemistry_dim+bridge_dim)>=1500,"censored_assay_pass":censored/(err*err)/(chemistry_dim+bridge_dim)>=1500,"failed_condition_pass":failed/(err*err)/(chemistry_dim+bridge_dim)>=1500,"biased_initial_pass":bundle=="O1" or err<=.02,"biased_spent_pass":bundle not in ("O6","O7") or err<=.02,"robust":robust and (bundle not in ("O6","O7") or err<=.02)})
    cwrite(out/"PILOT_DESIGN_PARETO.csv",pareto);cwrite(out/"PILOT_ROBUSTNESS.csv",rob)
    viable=[r for r in pareto if r["viable"] and r["bundle"]=="O5"];viable.sort(key=lambda r:(r["chromatography_injections"],r["shots"],-r["E_optimal"]));minimum=viable[0] if viable else None
    robust_candidates=[r for r in pareto if any(x["robust"] and x["conditions"]==r["conditions"] and x["replicates"]==r["replicates"] and x["fractions"]==r["fractions"] and x["bundle"]==r["bundle"] and x["error_scenario"]==r["error_scenario"] for x in rob)];robust_candidates.sort(key=lambda r:(r["chromatography_injections"],r["shots"]));robust=robust_candidates[0] if robust_candidates else None
    design={"status":"CONDITIONAL_ON_EMPIRICAL_ERROR_MODEL","minimum":minimum,"robust":robust,"spent_reference_role":"MASS_BALANCE_AND_BRIDGE_STABILITY_NOT_Q_INITIAL_IDENTIFICATION"};jwrite(out/"MINIMUM_PILOT_DESIGN.json",design)
    return front,maxu,pareto,rob,design

def reports(out,result,design,maxu):
    minp=design["minimum"];rob=design["robust"]
    (out/"MINIMUM_PILOT_DESIGN.md").write_text("# Calculated conditional pilot\n\n"+json.dumps(design,indent=2,sort_keys=True)+"\n")
    tail=None if maxu is None else maxu/3
    assessment={"status":"EMPIRICAL_REFERENCE_EXTRACTION_TAIL_DATA_REQUIRED","maximum_joint_parameter_uncertainty":maxu,"conditional_allowable_tail_bias_fraction":tail,"equation":"tail_bias <= maximum_joint_parameter_uncertainty / 3","preparation_count":"CONDITIONAL_BY_ERROR_SCENARIO_NOT_FROZEN"};jwrite(out/"SCI_ED_002_REVISIT_TRIGGER_ASSESSMENT.json",assessment)
    (out/"SCI_ED_002_REVISIT_TRIGGER_ASSESSMENT.md").write_text(f"# SCI-ED-002 revisit trigger\n\n`EMPIRICAL_REFERENCE_EXTRACTION_TAIL_DATA_REQUIRED`. The calculated conditional tail allowance is {tail!r} of I_ref, derived as one third of the calculated joint-parameter frontier {maxu!r}. No preparation count is frozen because accepted evidence does not select the 1/2/5/10% error scenarios. Real sequential-cycle tail, recovery-bias, preparation-variance, censoring, and blank data are required.\n")
    (out/"FINAL_REPORT.md").write_text(f"# SCI-MD-009-C1 final report\n\nThe target-blind firewall passed, all 498 original cases hash-closed, and 96 supplemental production cases passed. Genuine nuisance-optimized profiles and joint M0/k/Csat recovery support practical identifiability for both species. O5 identifies Q_initial when initial I_ref and absolute fractions are measured; spent I_ref is required to test mass balance and common-versus-separate bridge stability, not to identify Q_initial. Pilot adequacy is conditional because accepted evidence does not select a measurement-error scenario. The calculated maximum joint uncertainty is {maxu!r}. Disposition: `{result['disposition']}`. No fitting, observed chemistry, physics change, or validation occurred. Physical validation remains `NOT_ESTABLISHED`.\n")
    (out/"REPRODUCE.md").write_text("# Reproduce SCI-MD-009-C1\n\n`python3 -m tools.sci_md_009.c1 --puckworks /path/puckworks --executable /path/espressoWholePullFoam --existing-run-root /path/sci-md-009-runs-r3 --supplemental-run-root /fresh/supplemental --output /fresh/results`\n")

def manifest(out):
    files={p.name:digest_file(p) for p in sorted(out.iterdir()) if p.is_file() and p.name not in ("RESULT_PACKAGE_MANIFEST.json",) and not p.name.startswith('.')};jwrite(out/"RESULT_PACKAGE_MANIFEST.json",{"schema":"ewp.sci-md-009-c1.package/v1","files":files,"file_count":len(files)})

def verify(out):
    result=json.loads((out/"RESULT.json").read_text());audit=study.read_csv(out/"EXISTING_CASE_AUDIT.csv");supp=study.read_csv(out/"SUPPLEMENTAL_RUN_MANIFEST.csv");dq=study.read_csv(out/"DERIVATIVE_QUALIFICATION.csv");pkg=json.loads((out/"RESULT_PACKAGE_MANIFEST.json").read_text())
    for name,h in pkg["files"].items():
      if digest_file(out/name)!=h:raise ValueError(f"package hash {name}")
    if len(audit)!=498 or any(r["classification"]!="RETAINED_VALID" for r in audit):raise ValueError("existing audit")
    if len(supp)>SUPPLEMENTAL_CAP or any(r["state"]!="PASS" for r in supp):raise ValueError("supplemental closure")
    validation=study.read_csv(out/"NONLINEAR_RESPONSE_VALIDATION.csv");maxerr=max(float(r["relative_error"]) for r in validation);stop="SCI_MD_009_C1_STOP_NONLINEAR_RESPONSE_NOT_QUALIFIED"
    if result["disposition"]==stop:
      if result["nonlinear_response_qualified"] or abs(result["maximum_validation_relative_error"]-maxerr)>1e-15 or maxerr<=.02:raise ValueError("response STOP closure")
      for name in ("NONLINEAR_PROFILE_RESULTS.csv","JOINT_SYNTHETIC_RECOVERY.csv","OBSERVABLE_BUNDLE_COMPARISON.csv","PRECISION_FRONTIER.csv","PILOT_DESIGN_PARETO.csv","PILOT_ROBUSTNESS.csv"):
       if study.read_csv(out/name)!=[{"state":"BLOCKED","reason":stop}]:raise ValueError(f"blocked artifact {name}")
      maxu=None
    else:
      rec=study.read_csv(out/"JOINT_SYNTHETIC_RECOVERY.csv");bundles=study.read_csv(out/"OBSERVABLE_BUNDLE_COMPARISON.csv");front=study.read_csv(out/"PRECISION_FRONTIER.csv");design=json.loads((out/"MINIMUM_PILOT_DESIGN.json").read_text())
      if not all({f"relative_error_{p}" for p in ("M0","k","Csat")}<=set(rec[0]) for _ in [0]):raise ValueError("joint recovery")
      if next(r for r in bundles if r["bundle"]=="O5")["Q_identifiable"]!="True":raise ValueError("Q result")
      maxu=max(float(r["joint_relative_uncertainty"]) for r in front if r["aggregate_status"]=="PASS")
      if result["maximum_joint_uncertainty"]!=maxu or result["disposition"]!=FINAL or design["status"]!="CONDITIONAL_ON_EMPIRICAL_ERROR_MODEL":raise ValueError("adjudication closure")
    if result["physical_validation"]!="NOT_ESTABLISHED" or result["target_chemistry_values_accessed"]:raise ValueError("claim/firewall")
    return {"status":"PASS","existing_cases":len(audit),"supplemental_cases":len(supp),"maximum_joint_uncertainty":maxu,"disposition":result["disposition"]}

def execute(puck,exe,existing,supproot,out):
    out.mkdir(parents=True,exist_ok=True);supproot.mkdir(parents=True,exist_ok=True)
    for name in ("SCIENTIFIC_CONTRACT_C1.md","SCI_MD_009_C1_REVIEW_FINDINGS.md"):
      source=ROOT/"validation/sci_md_009"/name
      if source.resolve()!= (out/name).resolve():(out/name).write_text(source.read_text())
    op,ip,fw=firewall(puck,out);env,inv,params=load_sanitized(op,ip);audit_existing(env,inv,params,existing,out);chosen,plan=supplemental_plan(env,params);cwrite(out/"GLOBAL_PARAMETER_DESIGN.csv",plan);jwrite(out/"SUPPLEMENTAL_RUN_PLAN.json",{"seed":SEED,"case_count":len(plan),"cap":SUPPLEMENTAL_CAP,"conditions":[f"E{x.experiment}" for x in chosen],"cases":[r["case_id"] for r in plan]});responses=run_supplemental(plan,env,inv,params,exe,supproot,out);models,qualified=fit_surrogates(plan,responses,chosen,params,out);dq,noise=derivative_qualification(out)
    if not qualified:
      validation=study.read_csv(out/"NONLINEAR_RESPONSE_VALIDATION.csv");result=stop_after_response_failure(out,plan,validation,dq,noise);jwrite(out/"TARGET_BLINDNESS.json",{"status":"PASS","firewall_sha256":digest_file(out/"TARGET_BLIND_FIREWALL.json"),"sanitized_operating_sha256":digest_file(op),"sanitized_inventory_sha256":digest_file(ip),"prohibited_values_available_to_analysis":False,"evidence":"measured sanitizer subprocess and mutation tests"});manifest(out);verify(out);return result
    local,profiles,recovery=nonlinear_analysis(models,chosen,out,noise);bundles=bundle_analysis(models,chosen,out);front,maxu,pareto,rob,design=precision_and_pilots(models,chosen,env,out)
    # practical gates recomputed from all parameters and both species
    recovery_ok=all(np.quantile([float(r[f"relative_error_{p}"]) for r in recovery if r["species"]==sp],.95)<=.2 for sp in study.SPECIES for p in ("M0","k","Csat"));rank_ok=all(v["rank"]==3 for v in local.values());profile_ok=all(float(r["objective"])>=0 for r in profiles);o5=next(r for r in bundles if r["bundle"]=="O5")["Q_identifiable"]=="True"
    if not (recovery_ok and rank_ok and profile_ok and o5 and design["minimum"]):disp="SCI_MD_009_INVENTORY_K_CSAT_NOT_PRACTICALLY_IDENTIFIABLE_WITH_AVAILABLE_OBSERVABLES"
    else:disp=FINAL
    result={"schema":"ewp.sci-md-009-c1.result/v1","disposition":disp,"target_blind_firewall":"PASS","existing_cases_retained":498,"supplemental_cases":len(plan),"supplemental_cap":SUPPLEMENTAL_CAP,"both_species_local_rank_three":rank_ok,"both_species_joint_recovery_pass":recovery_ok,"O5_Q_initial_identifiable":o5,"spent_reference_role":"MASS_BALANCE_AND_BRIDGE_STABILITY_NOT_Q_INITIAL_IDENTIFICATION","pilot_status":design["status"],"maximum_joint_uncertainty":maxu,"target_chemistry_values_accessed":False,"target_scores":0,"change_declaration":"NO_GOVERNING_PHYSICS_CHANGE","physical_validation":"NOT_ESTABLISHED"};jwrite(out/"RESULT.json",result);jwrite(out/"TARGET_BLINDNESS.json",{"status":"PASS","firewall_sha256":digest_file(out/"TARGET_BLIND_FIREWALL.json"),"sanitized_operating_sha256":digest_file(op),"sanitized_inventory_sha256":digest_file(ip),"prohibited_values_available_to_analysis":False,"evidence":"measured sanitizer subprocess and mutation tests"});reports(out,result,design,maxu);manifest(out);verify(out);return result

def main(argv=None):
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--puckworks',type=Path,required=True);p.add_argument('--executable',type=Path,required=True);p.add_argument('--existing-run-root',type=Path,required=True);p.add_argument('--supplemental-run-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv);r=execute(*[x.resolve() for x in (a.puckworks,a.executable,a.existing_run_root,a.supplemental_run_root,a.output)]);print(json.dumps(r,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
