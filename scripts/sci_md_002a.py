#!/usr/bin/env python3
"""SCI-MD-002A deterministic reduced transient-consolidation screen.

Standalone diagnostic only: no production solver or Puckworks import/execution.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, platform, resource, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"validation/cases/sci_md_002a"
OVERLAYS=ROOT/"validation/cases/val_corpus_001/results/VAL_CORPUS_001_OVERLAYS_V3.json"
PRESSURES=(5,9,11); PCS=(1100000,1239155,1500000,2000000,3000000); THETAS=(.01,.03,.1,.3,1.,3.,10.)
PHI=.4; MU=.000315; H0=.01; AREA=.002463008640414398; RHO=965.; TSHOT=100.; DT=.05
MACHINE={"compliance_m3_pa":2e-11,"line_resistance_pa_s_m3":2e11,"free_flow_m3_s":6e-6,"shutoff_pa":1.2e6}

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
def j_integral(x,phi=PHI):
    if not 0<=x<1 or not 0<phi<1: raise ValueError("finite-porosity integral outside 0<=x<1")
    if x<1e-3:
        if x==0: return 0.
        n=8; h=x/n
        def f(s): return (1-s)**3/(1-phi*s)
        return h/3*(f(0)+f(x)+sum((4 if i%2 else 2)*f(i*h) for i in range(1,n)))
    p=phi
    return x*x*(-3/(2*p)+1/(2*p*p))+x*(3/p-3/(p*p)+1/(p**3))+x**3/(3*p)-(p-1)**3*math.log1p(-p*x)/(p**4)
def permeability_ratio(x,phi=PHI): return (1-x)**3/(1-phi*x)
def porosity(x,phi=PHI):
    eps=phi*x
    return (phi-eps)/(1-eps)
def bed_ratio(x,phi=PHI):
    if not x: return 1.
    numerator=x-1.5*x*x+x**3-.25*x**4
    return numerator/j_integral(x,phi)
def conductance(sigma,pc,k0):
    if sigma<=0: return AREA*k0/(MU*H0)
    x=sigma/pc
    return AREA*k0*pc*j_integral(x)/(MU*H0*sigma)
def equilibrium_flow(dp,pc,k0): return conductance(dp,pc,k0)*dp
def source_rows():
    d=json.loads(OVERLAYS.read_text())["overlays"]; out={}
    for p in PRESSURES:
        rr=d[f"R1-WASZ-{p}-DARCY-STATIC-MEASURED"]
        out[p]=[{"t":float(r[0]),"pressure_pa":max(0.,float(r[2])*1e5),"flow_kg_s":float(r[4])*1e-3,"mass_kg":float(r[6])*1e-3} for r in rr]
    return out
def interp(rows,t,key):
    if t<=rows[0]["t"]: return rows[0][key]
    if t>=rows[-1]["t"]: return rows[-1][key]
    u=t/(rows[-1]["t"])*(len(rows)-1); i=min(int(u),len(rows)-2); a=rows[i]; b=rows[i+1]
    f=(t-a["t"])/(b["t"]-a["t"]); return a[key]+f*(b[key]-a[key])
def anchor_k0(pc,src):
    r=src[9][-1]; q=max(r["flow_kg_s"],0)/RHO
    return q*MU*H0/(AREA*pc*j_integral(r["pressure_pa"]/pc))

def matrix_rows():
    result=[]
    def add(arm,model,pressure="NA",pc="NA",theta="NA",waveform="SOURCE",boundary="PRESCRIBED_BASKET_PRESSURE"):
        cid=f"{arm}-{model}-P{pressure}-PC{pc}-TH{theta}-{waveform}-{boundary}"
        result.append({"case_id":cid,"arm":arm,"model":model,"pressure_group_bar":pressure,"critical_pressure_pa":pc,"theta_c":theta,"waveform":waveform,"boundary_mode":boundary})
    for model,wave in (("TPM_DISABLED_FIXED_HYDRAULICS","STEP"),("TPM_QUASI_STATIC_EQUILIBRIUM","STEP"),("TPM_SINGLE_MODE_TRANSIENT","STEP"),("TPM_SINGLE_MODE_TRANSIENT","UNLOAD"),("MACHINE_ONLY","STEP")): add("C0_ANALYTICAL_CONTROLS",model,9,1239155,.1,wave)
    for pc in PCS:
        for p in PRESSURES: add("E1_EQUILIBRIUM_PRESSURE_SCREEN","TPM_QUASI_STATIC_EQUILIBRIUM",p,pc,"QUASI_STATIC_LIMIT")
    for pc in PCS:
      for th in THETAS:
        for wave in ("STEP","RAMP","HOLD","UNLOAD","PULSE"): add("T1_SYNTHETIC_TRANSIENT_SIGNATURES","TPM_SINGLE_MODE_TRANSIENT",9,pc,th,wave)
        for p in PRESSURES: add("S1_SOURCE_PRESSURE_SCREEN","TPM_SINGLE_MODE_TRANSIENT",p,pc,th)
        for p in PRESSURES: add("S2_MACHINE_TRANSFER","TPM_SINGLE_MODE_TRANSIENT",p,pc,th,"SOURCE","LUMPED_MACHINE_COMPLIANCE")
        for p in PRESSURES: add("R1_GENERIC_RELAXING_RESISTANCE_CONTROL","GENERIC_RELAXING_RESISTANCE",p,pc,th)
        for wave in ("UNLOAD","PULSE"): add("U1_UNLOADING_MEASUREMENT_DESIGN","TPM_SINGLE_MODE_TRANSIENT",9,pc,th,wave)
    return result
def protocol(matrix_hash=None):
    return {"schema_version":"ewp.sci_md_002a.protocol.v1","status":"PROSPECTIVE_FROZEN_BEFORE_ADJUDICATIVE_EXECUTION","task_id":"SCI-MD-002A","issue":72,"change_declaration":"NO_GOVERNING_PHYSICS_CHANGE","evidence_class":"POST_OBSERVATION_MECHANISM_DISCRIMINATION","models":["TPM_DISABLED_FIXED_HYDRAULICS","TPM_QUASI_STATIC_EQUILIBRIUM","TPM_SINGLE_MODE_TRANSIENT"],"state_equation":"tau_c*d(sigma_c)/dt=delta_p_basket_to_outlet-sigma_c","equilibrium_mapping":"accepted WP03 finite-porosity depth-resolved scalar integral evaluated at sigma_c; epsilon_bulk=1-bed_height_ratio(sigma_c)","pressure_nodes":{"drive":"BASKET_OR_PUCK_INLET_GAUGE minus BASKET_BOTTOM_AMBIENT_GAUGE","sign":"positive compression"},"fixed_primitives":{"phi0":PHI,"k0_m2":"9_bar_scale_only_anchor","mu_pa_s":MU,"bed_depth_m":H0,"basket_area_m2":AREA,"density_kg_m3":RHO},"parameter_bounds":{"critical_pressure_pa":list(PCS),"theta_c":list(THETAS),"shot_scale_s":TSHOT,"provenance":{"1239155":"SOURCE_DERIVED_EXISTING_CLOSURE","other_pc_levels":"SYNTHETIC_SCREEN_BOUND","theta_levels":"SYNTHETIC_SCREEN_BOUND"}},"source":{"overlays":str(OVERLAYS.relative_to(ROOT)),"groups":list(PRESSURES),"alignment":"unchanged source clock; accepted presentation clock +3 s only where predecessor already uses it","calibration":"one 9-bar multiplicative hydraulic scale; 5/11 bar transfer","grind_arm":"GRIND_TRANSFER_NOT_IDENTIFIABLE_FROM_AVAILABLE_STRUCTURE_DATA"},"numerics":{"integrator":"backward_euler_for_state_and_machine","base_dt_s":DT,"refined_dt_s":DT/2,"relative_tolerance":1e-9,"output_dt_s":.1},"validity":{"pc_strictly_greater_than_effective_state":True,"bed_height_positive":True,"porosity_interval":"0<phi<=phi0","permeability_positive":True,"no_clipping":True},"gate_order":["ARTIFACT_AND_NUMERICAL_VALIDITY","RESISTANCE_SIGN","PRESSURE_ORDERING","PHYSICAL_BOUNDS","GRIND_DIRECTION_OR_NOT_IDENTIFIABLE","TEMPORAL_SHAPE","TRANSFER","DISTINCTIVENESS","AGGREGATE_ERROR"],"budgets":{"pilot_max":64,"initial_parameter_sets":35,"refined_parameter_sets_max":0,"source_trajectories":210,"total_trajectories":580,"workers":"min(16,floor(0.25*logical_cpu_count))","memory_gib":16,"gpu":0,"target_hours":4,"review_hours":8},"stop_rules":["SOURCE_MATRIX_UNRESOLVED","RIGHTS_UNCLEAR","EFFECTIVE_STRESS_MAPPING_UNRESOLVED","HASH_MISMATCH","NONFINITE_OR_INVALID_STATE","CONSERVATION_FAILURE","REFINEMENT_CHANGES_GATE","EXECUTED_SOURCE_MISMATCH"],"matrix_sha256":matrix_hash,"claim_boundary":{"model_class":"REDUCED_DIAGNOSTIC_TRANSIENT_CONSOLIDATION_MODEL","production_openfoam_physics":"UNCHANGED","physical_validation":"NOT_ESTABLISHED","general_whole_solver_physical_validation":"NOT_ESTABLISHED","wetted_puck_modulus":"NOT_MEASURED_BY_THIS_TASK","real_puck_parameters":"NOT_IDENTIFIED","experimental_commissioning":"NOT_AUTHORIZED","wp04_tpm_001":"NOT_AUTHORIZED_BY_THIS_TASK_ALONE","combined_mechanism_model":"NOT_AUTHORIZED"}}
def freeze():
    OUT.mkdir(parents=True,exist_ok=True); rr=matrix_rows(); fields=list(rr[0]); cp=OUT/"SCI_MD_002A_CASE_MATRIX.csv"
    with cp.open("w",newline="") as f: w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rr)
    jp=OUT/"SCI_MD_002A_CASE_MATRIX.json"; jp.write_text(canonical({"schema_version":"ewp.sci_md_002a.matrix.v1","row_count":len(rr),"rows":rr}))
    (OUT/"SCI_MD_002A_PROTOCOL.json").write_text(json.dumps(protocol(sha(jp)),indent=2,sort_keys=True)+"\n")
    print(canonical({"rows":len(rr),"matrix_sha256":sha(jp)}),end="")

def waveform(name,t,nominal):
    if name=="STEP" or name=="HOLD": return nominal
    if name=="RAMP": return nominal*min(t/10,1)
    if name=="UNLOAD": return nominal if t<50 else 0
    if name=="PULSE": return nominal if 20<=t<60 else 0
    return nominal
def simulate(row,src,dt=DT):
    pc=float(row["critical_pressure_pa"] if row["critical_pressure_pa"]!="NA" else 1239155); th=float(row["theta_c"] if row["theta_c"] not in ("NA","QUASI_STATIC_LIMIT") else .1); tau=th*TSHOT
    pgroup=int(row["pressure_group_bar"] if row["pressure_group_bar"]!="NA" else 9); k0=anchor_k0(pc,src); model=row["model"]; sigma=0.; pu=0.; mass=0.; maxeps=0.; minphi=PHI; maxres=0.; samples=[]
    duration=src[pgroup][-1]["t"] if row["waveform"]=="SOURCE" else TSHOT; n=round(duration/dt)
    for i in range(n+1):
        t=i*dt
        target=interp(src[pgroup],t,"pressure_pa") if row["waveform"]=="SOURCE" else waveform(row["waveform"],t,pgroup*1e5)
        old=sigma
        if row["boundary_mode"]=="LUMPED_MACHINE_COMPLIANCE" or model=="MACHINE_ONLY":
            pu_old=pu
            def coupled(candidate):
                local_dp=max(0.,candidate)
                local_sigma=old
                for _ in range(8):
                    if model in ("TPM_DISABLED_FIXED_HYDRAULICS","MACHINE_ONLY"): local_sigma=0.
                    elif model=="TPM_QUASI_STATIC_EQUILIBRIUM": local_sigma=local_dp
                    else: local_sigma=(old+dt*local_dp/tau)/(1+dt/tau)
                    local_g=conductance(local_sigma,pc,k0)
                    if model=="GENERIC_RELAXING_RESISTANCE": local_g=conductance(0,pc,k0)*math.exp(-2.5*local_sigma/pc)
                    local_dp=candidate/(1+MACHINE["line_resistance_pa_s_m3"]*local_g)
                local_q=local_g*local_dp
                local_supply=MACHINE["free_flow_m3_s"]*max(0.,1-candidate/MACHINE["shutoff_pa"])
                residual=MACHINE["compliance_m3_pa"]*(candidate-pu_old)/dt-(local_supply-local_q)
                return residual,local_dp,local_sigma,local_supply
            lo,hi=0.,MACHINE["shutoff_pa"]
            for _ in range(50):
                mid=(lo+hi)/2
                if coupled(mid)[0]>0: hi=mid
                else: lo=mid
            pu=(lo+hi)/2; _,dp,sigma,supply=coupled(pu)
        else: dp=target; supply=None
        if supply is None:
            if model=="TPM_QUASI_STATIC_EQUILIBRIUM": sigma=dp
            elif model in ("TPM_DISABLED_FIXED_HYDRAULICS","MACHINE_ONLY"): sigma=0
            else: sigma=(old+dt*dp/tau)/(1+dt/tau)
        if sigma>=pc: return {"status":"INVALID_BOUND","case_id":row["case_id"],"reason":"sigma_c>=pc"}
        x=sigma/pc; phi=porosity(x); br=bed_ratio(x); g=conductance(sigma,pc,k0)
        if model=="GENERIC_RELAXING_RESISTANCE": g=conductance(0,pc,k0)*math.exp(-2.5*x)
        q=g*dp; mass+=q*RHO*dt
        if supply is not None: maxres=max(maxres,abs(MACHINE["compliance_m3_pa"]*(pu-pu_old)/dt-(supply-q)))
        eps=1-br; maxeps=max(maxeps,eps); minphi=min(minphi,phi)
        if i%max(1,round(.1/dt))==0: samples.append({"t":t,"dp":dp,"pu":pu,"sigma":sigma,"q":q,"mass":mass,"eps":eps,"phi":phi,"k_ratio":permeability_ratio(x),"g":g})
    s50=next((s["t"] for s in samples if s["sigma"]>=.5*max(z["sigma"] for z in samples)),None); s90=next((s["t"] for s in samples if s["sigma"]>=.9*max(z["sigma"] for z in samples)),None)
    obs=src[pgroup][-1]; return {"status":"PASS","case_id":row["case_id"],"arm":row["arm"],"model":model,"p":pgroup,"pc":pc,"theta":th,"boundary":row["boundary_mode"],"waveform":row["waveform"],"k0":k0,"final_q_kg_s":samples[-1]["q"]*RHO,"source_final_q_kg_s":obs["flow_kg_s"],"final_mass_kg":mass,"source_final_mass_kg":obs["mass_kg"],"final_conductance":samples[-1]["g"],"max_strain":maxeps,"min_porosity":minphi,"min_bed_ratio":1-maxeps,"t50_s":s50,"t90_s":s90,"unload_recovery_fraction":((maxeps-samples[-1]["eps"])/maxeps if maxeps else 0),"machine_balance_max_m3_s":maxres,"steps":n+1,"telemetry":{"peak_rss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}}

def authority(bundle,workers):
    matrix=OUT/"SCI_MD_002A_CASE_MATRIX.json"; proto=OUT/"SCI_MD_002A_PROTOCOL.json"
    return {"schema_version":"ewp.sci_md_002a.execution_authority.v1","task_id":"SCI-MD-002A","lane_id":"EWP-PAR-SCI-MD-002A","branch":git("branch","--show-current"),"source_head":git("rev-parse","HEAD"),"source_tree":git("rev-parse","HEAD^{tree}"),"protocol_sha256":sha(proto),"matrix_sha256":sha(matrix),"implementation_sha256":sha(__file__),"source_data_sha256":sha(OVERLAYS),"worker_count":workers,"thread_limits":{"OMP_NUM_THREADS":1,"OPENBLAS_NUM_THREADS":1,"MKL_NUM_THREADS":1},"output_path_policy":"EXTERNAL_UNTRACKED_TASK_NAMESPACE","execution_owner":"SECONDARY_SCI_MD_002A_AGENT","parent_pid":os.getpid(),"command":" ".join(sys.argv),"started_utc":now()}
def execute(bundle,pilot=False):
    bundle=Path(bundle); (bundle/"case_records").mkdir(parents=True,exist_ok=True); src=source_rows(); rr=matrix_rows()
    if pilot: rr=[rr[i] for i in sorted(set([0,1,2,3,4,20,190,365,500]))][:64]
    workers=max(1,min(16,(os.cpu_count() or 1)//4)); a=authority(bundle,workers); (bundle/"execution_authority.json").write_text(canonical(a)); (bundle/"protocol_snapshot.json").write_bytes((OUT/"SCI_MD_002A_PROTOCOL.json").read_bytes()); (bundle/"case_matrix_snapshot.json").write_bytes((OUT/"SCI_MD_002A_CASE_MATRIX.json").read_bytes())
    (bundle/"environment.json").write_text(canonical({"python":platform.python_version(),"platform":platform.platform(),"logical_cpus":os.cpu_count(),"nested_threads":1,"gpu":0}))
    start=time.perf_counter(); records=[]
    for row in rr:
        rec=simulate(row,src); rec["authority_sha256"]=sha(bundle/"execution_authority.json"); tmp=bundle/"case_records"/(row["case_id"]+".tmp"); final=tmp.with_suffix(".json"); tmp.write_text(canonical(rec)); tmp.replace(final); records.append(rec)
    elapsed=time.perf_counter()-start; files=sorted((bundle/"case_records").glob("*.json")); manifest={"record_count":len(files),"records":[{"name":p.name,"sha256":sha(p),"bytes":p.stat().st_size} for p in files],"aggregate_sha256":hashlib.sha256("".join(sha(p) for p in files).encode()).hexdigest()}
    (bundle/"manifest.json").write_text(canonical(manifest)); (bundle/"timing.json").write_text(canonical({"pilot":pilot,"trajectories":len(rr),"elapsed_s":elapsed,"seconds_per_case":elapsed/len(rr),"projected_580_s":elapsed/len(rr)*580,"peak_rss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,"failure_count":sum(r["status"]!="PASS" for r in records)})); (bundle/"stdout.log").write_text("SCI-MD-002A completed\n"); (bundle/"stderr.log").write_text("")
    print(canonical(json.loads((bundle/"timing.json").read_text())),end="")

def reduce_bundle(bundle):
    bundle=Path(bundle); rec=[json.loads(p.read_text()) for p in sorted((bundle/"case_records").glob("*.json"))]; valid=[r for r in rec if r["status"]=="PASS"]
    source=[r for r in valid if r["arm"]=="S1_SOURCE_PRESSURE_SCREEN"]; candidates={}
    for r in source: candidates.setdefault((r["pc"],r["theta"]),{})[r["p"]]=r
    assessed=[]
    for key,v in candidates.items():
        if set(v)!=set(PRESSURES): continue
        q={p:v[p]["final_q_kg_s"] for p in PRESSURES}; observed={p:v[p]["source_final_q_kg_s"] for p in PRESSURES}
        conductance={p:v[p]["final_conductance"] for p in PRESSURES}
        sign=conductance[11]<conductance[9]<conductance[5]
        ordering=q[5]>q[9]>q[11]; bounds=all(v[p]["min_porosity"]>0 and v[p]["min_bed_ratio"]>0 for p in PRESSURES)
        err=math.sqrt(sum((q[p]-observed[p])**2 for p in PRESSURES)/3)
        assessed.append({"pc":key[0],"theta":key[1],"resistance_direction_pass":sign,"pressure_ordering_pass":ordering,"sign_pass":sign,"ordering_pass":ordering,"bounds_pass":bounds,"rmse_kg_s":err,"max_strain":max(v[p]["max_strain"] for p in PRESSURES)})
    survivors=[x for x in assessed if x["resistance_direction_pass"] and x["pressure_ordering_pass"] and x["bounds_pass"]]
    if survivors: disposition="SCI_MD_002A_TRANSIENT_POROMECHANICS_SURVIVES_NOT_IDENTIFIED"
    elif any(x["resistance_direction_pass"] for x in assessed): disposition="SCI_MD_002A_REJECTED_WRONG_PRESSURE_ORDERING"
    else: disposition="SCI_MD_002A_REJECTED_WRONG_SIGN"
    result={"schema_version":"ewp.sci_md_002a.result.v1","authority_sha256":sha(bundle/"execution_authority.json"),"manifest_sha256":sha(bundle/"manifest.json"),"trajectory_count":len(rec),"valid_count":len(valid),"invalid_count":len(rec)-len(valid),"source_conditioned_count":len([r for r in valid if r.get("arm") in ("S1_SOURCE_PRESSURE_SCREEN","S2_MACHINE_TRANSFER")]),"synthetic_signature_count":len([r for r in valid if r.get("arm") in ("T1_SYNTHETIC_TRANSIENT_SIGNATURES","U1_UNLOADING_MEASUREMENT_DESIGN")]),"control_count":len([r for r in valid if r.get("arm") in ("C0_ANALYTICAL_CONTROLS","E1_EQUILIBRIUM_PRESSURE_SCREEN","R1_GENERIC_RELAXING_RESISTANCE_CONTROL")]),"pressure_candidates":assessed,"survivor_count":len(survivors),"best_survivor":min(survivors,key=lambda x:x["rmse_kg_s"]) if survivors else None,"gates":{"artifact_and_numerical_validity":len(valid)==len(rec),"resistance_sign":any(x["sign_pass"] for x in assessed),"pressure_ordering":bool(survivors),"physical_bounds":all(x["bounds_pass"] for x in assessed),"grind_direction":"GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED","temporal_shape":"DESCRIPTIVE_POST_OBSERVATION","transfer":bool(survivors),"distinctiveness":"DEFORMATION_MEASUREMENT_REQUIRED"},"disposition":disposition,"claim_boundary":protocol()["claim_boundary"]}
    (OUT/"SCI_MD_002A_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    with (OUT/"SCI_MD_002A_SUMMARY.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(assessed[0]),lineterminator="\n"); w.writeheader(); w.writerows(assessed)
    (OUT/"SCI_MD_002A_DISPOSITION.json").write_text(canonical({"task_id":"SCI-MD-002A","disposition":disposition,"deformation_measurement":"REQUIRED_FOR_DISCRIMINATION","production_implementation":"NOT_AUTHORIZED","physical_validation":"NOT_ESTABLISHED"}))
    print(canonical({"disposition":disposition,"survivors":len(survivors)}),end="")

if __name__=="__main__":
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True); sp.add_parser("freeze");
    for name in ("pilot","run","reduce"): q=sp.add_parser(name); q.add_argument("--bundle",required=True)
    a=ap.parse_args(); freeze() if a.cmd=="freeze" else execute(a.bundle,a.cmd=="pilot") if a.cmd in ("pilot","run") else reduce_bundle(a.bundle)
