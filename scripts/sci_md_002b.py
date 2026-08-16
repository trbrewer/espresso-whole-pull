#!/usr/bin/env python3
"""SCI-MD-002B corrected prospective wetting-age swelling screen.

Standalone standard-library implementation. Production OpenFOAM and
Puckworks are neither imported nor executed.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, platform, resource, subprocess, sys, time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"validation/cases/sci_md_002b"
OVERLAY=ROOT/"validation/cases/val_corpus_001/results/VAL_CORPUS_001_OVERLAYS_V3.json"
REFS=OUT/"SCI_MD_002B_REFERENCE_SOURCES.json"; LANE=ROOT/"docs/analysis/sci_md_002b/PARALLEL_LANE_DECLARATION.json"
TASK="SCI-MD-002B"; LANE_ID="EWP-PAR-SCI-MD-002B"; BRANCH="research/sci-md-002b-wetting-age-swelling"
OVERLAY_SHA="e69d2b7b0f0ee6945013a0b185da21803d404270a34f1c9d26aed6ecda370c0e"
PUCK_COMMIT="fc61c4670ec7bf801e40bb391aab16048b8da26b"; PUCK_TREE="1d553e44ee2f7480a5df521560801b478618cc84"
TOKEN="SCI_MD_002B_ADJUDICATIVE_EXECUTION_AUTHORIZED"; EXTERNAL_NAMESPACE="SCI_MD_002B_EXTERNAL_BUNDLE"
PRESSURES=(5,9,11); PHI_WET=0.322; EPSILON_B0=0.17; MU=0.000315; RHO=965.; AREA=.002463008640414398; H0=.01; PCAP=1e4
D0=1.25e-10; N_TORT=.5; HARD_CAP=2500; RECORD_SCHEMA="ewp.sci_md_002b.case_record.v2"
TEMPORAL_ABS_TOL=1e-10; RESISTANCE_REL_STEP_TOL=5e-5
POWDERS={"E":(.292,.708,27.48e-6/2,321.7e-6/2),"H":(.275,.725,28.20e-6/2,347.5e-6/2),"M":(.203,.797,30.23e-6/2,358.47e-6/2),"F":(.097,.903,31.59e-6/2,524e-6/2)}
TERMINAL_PRESSURES={5:450096.2,9:873024.9,11:1041717.4}
TERMINAL_REFERENCE_PRESSURES={5:450476.8,9:871691.6,11:1041916.7}
TERMINAL_OBSERVED_FLOWS={5:.002056292,9:.001827218,11:.001777572}
PILOT_IDS=("A0-FOSTER-CONSTANT-P9","C0-SOURCE-P5-NOSWELL","C1-SOURCE-P9-E-AC0.0","R1-SYNTH-P7-E-BASE","R1-SYNTH-P7-E-REFINED","T0-SOURCE-P11-E-STORAGE","A0-ACCOM-FIXED-E","A0-ACCOM-FREE-E")

def utc(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n"
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a): return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def file_identity(): return {"head":git("rev-parse","HEAD"),"tree":git("rev-parse","HEAD^{tree}")}

def safe_bundle(path):
    p=Path(path).absolute(); resolved=p.resolve(strict=False)
    if ROOT==resolved or ROOT in resolved.parents: raise ValueError("bundle must remain outside Git")
    if "sci_md_002b" not in str(resolved).lower(): raise ValueError("bundle lacks task namespace")
    for q in [p,*p.parents]:
        if q.exists() and q.is_symlink(): raise ValueError("symlink component in bundle path")
    return resolved

def load_histories(path=OVERLAY, expected_hash=OVERLAY_SHA):
    path=Path(path)
    if sha(path)!=expected_hash: raise ValueError("SOURCE_OVERLAY_HASH_MISMATCH")
    obj=json.loads(path.read_text())
    if obj.get("units")!={"flow":"g/s","mass":"g","pressure":"bar","solver_time":"s","source_time":"s","wetting_front":"mm"}: raise ValueError("SOURCE_OVERLAY_UNITS_INVALID")
    if obj.get("alignment")!="solver_time=source_time+3.0s for Waszkiewicz; linear interpolation within domain; no extrapolation": raise ValueError("SOURCE_OVERLAY_ALIGNMENT_INVALID")
    result={}
    for p in PRESSURES:
        key=f"R1-WASZ-{p}-DARCY-STATIC-MEASURED"; raw=obj.get("overlays",{}).get(key)
        if not isinstance(raw,list) or len(raw)!=999: raise ValueError(f"SOURCE_HISTORY_MISSING_{p}")
        rows=[]; last=-math.inf
        for i,r in enumerate(raw):
            if not isinstance(r,list) or len(r)!=8 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in r): raise ValueError(f"SOURCE_ROW_INVALID_{p}_{i}")
            t,solver_t,observed_pressure_bar,reference_pressure_bar,observed_flow,reference_flow,observed_mass,reference_mass=map(float,r)
            if t<=last or abs(solver_t-(t+3))>1e-9 or observed_pressure_bar<0 or reference_pressure_bar<0: raise ValueError(f"SOURCE_TIME_OR_PRESSURE_INVALID_{p}_{i}")
            rows.append({"source_time_s":t,"solver_time_s":solver_t,"observed_pressure_pa":observed_pressure_bar*1e5,"reference_model_pressure_pa":reference_pressure_bar*1e5,"observed_flow_kg_s":observed_flow*1e-3,"reference_model_flow_kg_s":reference_flow*1e-3,"observed_mass_kg":observed_mass*1e-3,"reference_model_mass_kg":reference_mass*1e-3})
            last=t
        if abs(rows[-1]["source_time_s"]-99.8999)>1e-12 or abs(rows[-1]["observed_pressure_pa"]-TERMINAL_PRESSURES[p])>1e-7 or abs(rows[-1]["reference_model_pressure_pa"]-TERMINAL_REFERENCE_PRESSURES[p])>1e-7: raise ValueError(f"SOURCE_TERMINAL_IDENTITY_INVALID_{p}")
        result[p]=rows
    return result

def cumulative_integral(rows,pcap=PCAP):
    out=[0.0]
    for a,b in zip(rows,rows[1:]): out.append(out[-1]+.5*((a["observed_pressure_pa"]+pcap)+(b["observed_pressure_pa"]+pcap))*(b["source_time_s"]-a["source_time_s"]))
    return out
def invert_integral(rows,cumulative,target,pcap=PCAP):
    if target<=0:return rows[0]["source_time_s"]
    if target>cumulative[-1]:return None
    lo,hi=0,len(cumulative)-1
    while hi-lo>1:
        m=(lo+hi)//2
        if cumulative[m]<target:lo=m
        else:hi=m
    a,b=rows[lo],rows[hi]; dt=b["source_time_s"]-a["source_time_s"]; p0=a["observed_pressure_pa"]+pcap; slope=(b["observed_pressure_pa"]-a["observed_pressure_pa"])/dt; need=target-cumulative[lo]
    if abs(slope)<1e-20:x=need/p0
    else:x=(-p0+math.sqrt(max(0,p0*p0+2*slope*need)))/slope
    return a["source_time_s"]+x
def interp(rows,t,key):
    if t<rows[0]["source_time_s"] or t>rows[-1]["source_time_s"]: raise ValueError("SOURCE_INTERPOLATION_EXTRAPOLATION")
    lo,hi=0,len(rows)-1
    while hi-lo>1:
        m=(lo+hi)//2
        if rows[m]["source_time_s"]<=t:lo=m
        else:hi=m
    if t==rows[lo]["source_time_s"]: return rows[lo][key]
    a,b=rows[lo],rows[hi]; f=(t-a["source_time_s"])/(b["source_time_s"]-a["source_time_s"]); return a[key]+f*(b[key]-a[key])

def hydraulic_anchor(hist=None):
    hist=hist or load_histories(); r=hist[9][-1]; return (r["observed_flow_kg_s"]/RHO)*MU*H0/(AREA*r["observed_pressure_pa"])
def front_from_integral(I,k0,phi_wet=PHI_WET): return math.sqrt(max(0,2*k0*I/(MU*phi_wet)))
def wetting_times(rows,k0,cells,phi_wet=PHI_WET):
    ci=cumulative_integral(rows); return [invert_integral(rows,ci,MU*phi_wet*((i+.5)*H0/cells)**2/(2*k0)) for i in range(cells)]

def tridiagonal(lo,di,up,rhs):
    n=len(di); b=di[:]; c=up[:]; d=rhs[:]
    for i in range(1,n): f=lo[i]/b[i-1]; b[i]-=f*c[i-1]; d[i]-=f*d[i-1]
    x=[0.]*n;x[-1]=d[-1]/b[-1]
    for i in range(n-2,-1,-1):x[i]=(d[i]-c[i]*x[i+1])/b[i]
    return x
@lru_cache(maxsize=20000)
def swelling_ratio(radius,age,D,cmax,n):
    if age<=0 or D==0 or cmax==0:return 1.
    tau=D*age/radius**2; steps=max(1,min(12000,math.ceil(tau/.005)))
    if steps==12000 and tau>60:return 1/(1-cmax)
    dt=tau/steps;dx=1/n;c=[0.]*n
    for _ in range(steps):
        lo=[0.]*n;di=[0.]*n;up=[0.]*n;rhs=c[:];f=dt*(1-c[0])/dx**2;di[0]=1+6*f;up[0]=-6*f
        for i in range(1,n):
            x=i*dx;f=dt*(1-c[i]);a=1/dx**2-1/(x*dx);z=1/dx**2+1/(x*dx);lo[i]=-f*a;di[i]=1+2*f/dx**2
            if i<n-1:up[i]=-f*z
            else:rhs[i]+=f*z*cmax
        c=tridiagonal(lo,di,up,rhs)
        if any(not math.isfinite(v) or v<0 or v>=1 for v in c):raise RuntimeError("SWELLING_PDE_PHYSICAL_INVALID")
    full=c+[cmax];integ=sum(.5*dx*((i*dx)**2/(1-full[i])+((i+1)*dx)**2/(1-full[i+1])) for i in range(n));return 3*integ
def particle(powder,age,D,cmax,n):
    tf,tc,rf,rc=POWDERS[powder];vf=swelling_ratio(rf,age,D,cmax,n);vc=swelling_ratio(rc,age,D,cmax,n);F=tf*vf+tc*vc;d=2/(tc/(rc*vc**(1/3))+tf/(rf*vf**(1/3)));d0=2/(tc/rc+tf/rf);return F,d/d0
def state(F,dr,ac,h0=H0):
    hr=1+ac*(F-1); initial_bulk=AREA*h0; initial_solid=(1-EPSILON_B0)*initial_bulk; swollen=initial_solid*F; bulk=initial_bulk*hr;pore=bulk-swollen;eps=pore/bulk
    if not (bulk>0 and pore>=0 and 0<eps<1):raise ValueError("PHYSICAL_VOLUME_INVALID")
    kr=(eps/EPSILON_B0)**(3+2*N_TORT)*dr**2*((1-EPSILON_B0)/(1-eps))**2
    if kr<=0:raise ValueError("PERMEABILITY_INVALID")
    return {"initial_solid_volume_m3":initial_solid,"swollen_solid_volume_m3":swollen,"swelling_storage_volume_m3":swollen-initial_solid,"bulk_volume_m3":bulk,"pore_volume_m3":pore,"porosity":eps,"cell_height_m":h0*hr,"permeability_ratio":kr,"resistance_ratio":hr/kr}

@dataclass(frozen=True)
class Case:
    case_id:str;arm:str;evidence_role:str;pressure_condition:str;powder:str;D_multiplier:float;cmax:float;accommodation:float;coupling:str;axial_cells:int;radial_cells:int;response_points:int;resolution:str;pilot_eligible:bool;adjudicative:bool;control_id:str|None;numerical_companion_id:str|None;cross_pressure_peer_ids:tuple[str,...];assumption_peer_ids:tuple[str,...];output_schema_version:str=RECORD_SCHEMA
def matrix_rows():
    rr=[]
    def add(*a,**k):rr.append(asdict(Case(*a,**k)))
    add(PILOT_IDS[0],"A0","DERIVED_IDENTITY","NOMINAL_STEP_9","E",0,0,0,"CONSTANT_PRESSURE",64,32,65,"BASE",True,False,None,None,(),())
    add(PILOT_IDS[6],"A0","DERIVED_IDENTITY","SYNTHETIC","E",1,.1,0,"ACCOM_ENDPOINT",64,32,65,"BASE",True,False,None,None,(),())
    add(PILOT_IDS[7],"A0","DERIVED_IDENTITY","SYNTHETIC","E",1,.1,1,"ACCOM_ENDPOINT",64,32,65,"BASE",True,False,None,None,(),())
    for p in PRESSURES:
        cid=f"C0-SOURCE-P{p}-NOSWELL";add(cid,"C0","EWP_GOVERNED_SOURCE",f"SOURCE_P{p}","M",0,0,0,"ONE_WAY",64,32,65,"BASE",cid==PILOT_IDS[1],False,None,None,(),())
    for powder in POWDERS:
      for ac in (0.,.5,1.):
        cid=f"C1-SOURCE-P9-{powder}-AC{ac}";add(cid,"C1","NUMERICAL_CONTROL","SOURCE_P9",powder,1,.1,ac,"SIMULTANEOUS",64,32,65,"BASE",cid==PILOT_IDS[2],False,"C0-SOURCE-P9-NOSWELL",None,(),())
    # Every candidate/pressure has prospectively matched base and refined rows.
    for powder in POWDERS:
      for dm in (.5,1.,2.):
       for cm in (.05,.1):
        for ac in (0.,.5,1.):
         for res,n,rn,rp in (("BASE",64,32,65),("REFINED",128,48,129)):
          ids=tuple(f"S1-SOURCE-P{p}-{powder}-D{dm}-CM{cm}-AC{ac}-{res}" for p in PRESSURES)
          assumption=tuple(f"S1-SOURCE-P9-{pw}-D{dm}-CM{cm}-AC{x}-{res}" for pw in POWDERS for x in (0.,.5,1.) if not(pw==powder and x==ac))
          for p,cid in zip(PRESSURES,ids):
            companion=cid.replace(res,"REFINED" if res=="BASE" else "BASE")
            add(cid,"S1","EWP_GOVERNED_SOURCE",f"SOURCE_P{p}",powder,dm,cm,ac,"ONE_WAY",n,rn,rp,res,False,True,f"C0-SOURCE-P{p}-NOSWELL",companion,tuple(x for x in ids if x!=cid),assumption)
    for p in PRESSURES:add(f"S2-DESIGN-BLOCKED-P{p}","S2","NUMERICAL_CONTROL",f"SOURCE_P{p}","M",1,.1,.5,"TWO_WAY_DESIGN_BLOCKED",64,32,65,"BASE",False,False,None,None,(),())
    add(PILOT_IDS[3],"R1","SYNTHETIC_SCREEN_BOUND","NOMINAL_STEP_7","E",1,.1,.5,"ONE_WAY",32,24,33,"BASE",True,False,None,PILOT_IDS[4],(),())
    add(PILOT_IDS[4],"R1","SYNTHETIC_SCREEN_BOUND","NOMINAL_STEP_7","E",1,.1,.5,"ONE_WAY",64,32,65,"REFINED",True,False,None,PILOT_IDS[3],(),())
    add(PILOT_IDS[5],"T0","EWP_GOVERNED_SOURCE","SOURCE_P11","E",1,.1,.5,"ONE_WAY",32,24,33,"BASE",True,False,"C0-SOURCE-P11-NOSWELL",None,(),())
    if len(rr)>HARD_CAP or len({x["case_id"] for x in rr})!=len(rr):raise RuntimeError("MATRIX_ID_OR_CAP_INVALID")
    return rr

def adjudicative_row_ids():
    """The one canonical, indivisible scientific execution cohort."""
    ids=sorted(r["case_id"] for r in matrix_rows() if r["arm"] in ("C0","S1"))
    if len(ids)!=435 or sum(i.startswith("C0-") for i in ids)!=3 or sum(i.startswith("S1-") for i in ids)!=432:raise RuntimeError("ADJUDICATIVE_COHORT_INVALID")
    return ids

def adjudicative_row_ids_sha256():return hashlib.sha256(canonical(adjudicative_row_ids()).encode()).hexdigest()

def protocol(matrix_hash=None):
 return {"schema_version":"ewp.sci_md_002b.protocol.v3","task_id":TASK,"status":"ADJUDICATION_LAYER_CORRECTED_PENDING_FINAL_REVIEW","change_declaration":"NO_GOVERNING_PHYSICS_CHANGE","source":{"overlay_path":str(OVERLAY.relative_to(ROOT)),"overlay_sha256":OVERLAY_SHA,"column_contract":["source_time_s","solver_time_s","observed_pressure_pa","reference_model_pressure_pa","observed_flow_kg_s","reference_model_flow_kg_s","observed_mass_kg","reference_model_mass_kg"],"histories":{str(p):{"row_count":999,"terminal_time_s":99.8999,"terminal_observed_pressure_pa":TERMINAL_PRESSURES[p],"terminal_reference_model_pressure_pa":TERMINAL_REFERENCE_PRESSURES[p],"terminal_observed_flow_kg_s":TERMINAL_OBSERVED_FLOWS[p]} for p in PRESSURES},"integration":"piecewise-linear observed pressure with exact trapezoidal cumulative integral; analytic within-segment inversion; no extrapolation","hydraulic_anchor":"one observed P9 terminal-flow hydraulic scale, transferred unchanged to P5 and P11"},"porosities":{"phi_wet":{"value":PHI_WET,"provenance":"PUCKWORKS_PINNED_REFERENCE_FOSTER_FITTED_NOT_EWP_SOURCE_MEASUREMENT","role":"REFERENCE_PRIMARY","sensitivity_bounds":[.173,.4],"matrix_axis_executed":False},"epsilon_b0":{"value":EPSILON_B0,"provenance":"PUCKWORKS_PINNED_REFERENCE_MO_NOMINAL_NOT_EWP_SOURCE_MEASUREMENT","role":"REFERENCE_PRIMARY","sensitivity_bounds":[.17,.4],"matrix_axis_executed":False}},"model":{"chain":"observed pressure history -> wetting time -> local age -> Mo swelling -> volume-consistent accommodation -> CK permeability -> serial resistance -> axial flow","one_way_balance":"front trajectory excludes swelling-storage feedback","liquid_status":"ONE_WAY_LIQUID_FEEDBACK_NOT_CLOSED_BY_DESIGN","two_way":"SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED"},"temporal_output":{"grid":"exactly all 999 governed source timestamps for SOURCE rows; frozen 0.5 s grid plus terminal for nominal controls","absolute_tolerance":TEMPORAL_ABS_TOL,"resistance_relative_step_tolerance":RESISTANCE_REL_STEP_TOL,"requirements":["exact source time and observed pressure","finite complete fields","bounded monotonic front and wet fraction","exact wetting age identity","no storage or resistance growth before local wetting","positive storage after wetting for nonzero C_M","onset not earlier than first wetting","resistance nondecrease within frozen relative step tolerance","consistent full-wetting and terminal events"],"fields":["time_s","pressure_pa","pressure_integral_pa_s","front_position_m","wet_fraction","cell_wetting_times_s","cell_wetting_ages_s","cell_swelling_storage_volumes_m3","cell_resistance_ratios","swelling_storage_volume_m3","swelling_storage_rate_m3_s","effective_serial_resistance_ratio","hydraulic_flow_m3_s","front_filling_flow_m3_s","outlet_flow_m3_s","liquid_feedback_status","resistance_growth_onset_s"]},"refinement":{"base":{"axial_cells":64,"radial_cells":32,"response_points":65},"refined":{"axial_cells":128,"radial_cells":48,"response_points":129},"uncertainty":"for each margin, abs(base margin-refined margin); PASS iff both base margins minus uncertainty >0; REJECTED iff either base margin plus uncertainty <=0; otherwise NUMERICALLY_UNRESOLVED"},"adjudicative_cohort":{"row_count":435,"candidate_count":72,"c0_count":3,"row_ids_sha256":adjudicative_row_ids_sha256(),"authority_must_equal_sorted_cohort":True},"gates":["AUTHORITY_AND_ARTIFACT_VALIDITY","REFERENCE_AND_NUMERICAL_VALIDITY","PHYSICAL_STATE_AND_BOOKKEEPING_VALIDITY","RESISTANCE_DIRECTION","PRESSURE_ORDERING","TEMPORAL_SIGNATURE","ASSUMPTION_DEPENDENCE","PARTICLE_SIZE_AND_GRIND_IDENTIFIABILITY","AGGREGATE_COMPARISON"],"budget":{"row_count":len(matrix_rows()),"hard_max":HARD_CAP,"workers":1,"nested_threads":1,"memory_gib":16,"gpu":0},"pilot_row_ids":list(PILOT_IDS),"record_schema":RECORD_SCHEMA,"matrix_sha256":matrix_hash,"claim_boundary":["PHYSICAL_VALIDATION_NOT_ESTABLISHED","POST_OBSERVATION_MECHANISM_DISCRIMINATION","NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE","NO_COMBINED_MECHANISM_AUTHORIZATION","NO_SCI_LC_001B_AUTHORIZATION","GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED","PHI_WET_AND_EPSILON_B0_BOUND_ROBUSTNESS_NOT_ESTABLISHED"]}

def generate():
 OUT.mkdir(parents=True,exist_ok=True);rows=matrix_rows();jp=OUT/"SCI_MD_002B_CASE_MATRIX.json";jp.write_text(canonical({"schema_version":"ewp.sci_md_002b.matrix.v2","row_count":len(rows),"rows":rows}))
 with (OUT/"SCI_MD_002B_CASE_MATRIX.csv").open("w",newline="") as f:
  fields=list(rows[0]);w=csv.DictWriter(f,fields,lineterminator="\n");w.writeheader()
  for x in rows:
   y=x.copy()
   for k in ("cross_pressure_peer_ids","assumption_peer_ids"):y[k]="|".join(y[k])
   w.writerow(y)
 (OUT/"SCI_MD_002B_PROTOCOL.json").write_text(json.dumps(protocol(sha(jp)),indent=2,sort_keys=True)+"\n");print(canonical({"row_count":len(rows),"matrix_sha256":sha(jp)}),end="")
def verify_generated():
 disk=json.loads((OUT/"SCI_MD_002B_CASE_MATRIX.json").read_text());rows=json.loads(canonical(matrix_rows()));p=json.loads((OUT/"SCI_MD_002B_PROTOCOL.json").read_text())
 if disk["rows"]!=rows or disk["row_count"]!=len(rows) or p!=json.loads(canonical(protocol(sha(OUT/"SCI_MD_002B_CASE_MATRIX.json")))):raise RuntimeError("GENERATION_MISMATCH")
 print(canonical({"status":"PASS","row_count":len(rows)}),end="")

def response_table(row,max_age):
 points=row["response_points"]; ages=[max_age*i/(points-1) for i in range(points)];vals=[]
 for a in ages:
  F,dr=particle(row["powder"],a,D0*row["D_multiplier"],row["cmax"],row["radial_cells"]);vals.append(state(F,dr,row["accommodation"],H0/row["axial_cells"]))
 return ages,vals
def table_value(ages,vals,a):
 if a<=0:return vals[0]
 if a>=ages[-1]:return vals[-1]
 u=a/ages[-1]*(len(ages)-1);i=min(int(u),len(ages)-2);f=(a-ages[i])/(ages[i+1]-ages[i]);return {k:vals[i][k]+f*(vals[i+1][k]-vals[i][k]) for k in vals[i]}
def nominal_rows(pbar,duration=30.):
 return [{"source_time_s":i*.5,"solver_time_s":i*.5,"observed_pressure_pa":pbar*1e5,"reference_model_pressure_pa":pbar*1e5,"observed_flow_kg_s":0.,"reference_model_flow_kg_s":0.,"observed_mass_kg":0.,"reference_model_mass_kg":0.} for i in range(int(duration/.5)+1)]
def simulate(row,histories=None):
 if row["coupling"]=="TWO_WAY_DESIGN_BLOCKED":return {"status":"DESIGN_BLOCKED","stop_reason":"SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED"}
 histories=histories or load_histories(); source=row["pressure_condition"].startswith("SOURCE_P")
 if source:p=int(row["pressure_condition"].split("P")[1]);series=histories[p]
 elif row["pressure_condition"].startswith("NOMINAL_STEP_"):p=float(row["pressure_condition"].removeprefix("NOMINAL_STEP_"));series=nominal_rows(p)
 elif row["pressure_condition"]=="SYNTHETIC":p=9.;series=nominal_rows(p)
 else:raise ValueError("UNSUPPORTED_PRESSURE_CONDITION")
 k0=hydraulic_anchor(histories);ci=cumulative_integral(series);cells=row["axial_cells"]
 wet=[0.]*cells if row["coupling"] in ("SIMULTANEOUS","ACCOM_ENDPOINT") else wetting_times(series,k0,cells)
 max_age=series[-1]["source_time_s"]; ages,vals=response_table(row,max_age); temporal=[];prev_storage=0.;onset=None;prevR=None
 for idx,(src,I) in enumerate(zip(series,ci)):
  t=src["source_time_s"];front=min(H0,front_from_integral(I,k0));wetages=[max(0,t-w) if w is not None else 0. for w in wet];states=[table_value(ages,vals,a) if a>0 else state(1,1,row["accommodation"],H0/cells) for a in wetages]
  storage=sum(s["swelling_storage_volume_m3"] for s in states);rate=0. if idx==0 else (storage-prev_storage)/(t-series[idx-1]["source_time_s"]);prev_storage=storage
  R=sum(s["resistance_ratio"] for s in states)/cells;pressure=src["observed_pressure_pa"];q=k0*AREA*pressure/(MU*H0*R);full=front>=H0*(1-1e-12);out=q if full else 0.;fill=PHI_WET*AREA*(front-(temporal[-1]["front_position_m"] if temporal else 0))/(t-series[idx-1]["source_time_s"]) if idx else 0.
  if onset is None and R>1+1e-8:onset=t
  monotonic=True if prevR is None else R>=prevR-1e-10;prevR=R
  temporal.append({"time_s":t,"pressure_pa":pressure,"pressure_integral_pa_s":I,"front_position_m":front,"wet_fraction":front/H0,"cell_wetting_times_s":wet,"cell_wetting_ages_s":wetages,"cell_swelling_storage_volumes_m3":[s["swelling_storage_volume_m3"] for s in states],"cell_resistance_ratios":[s["resistance_ratio"] for s in states],"swelling_storage_volume_m3":storage,"swelling_storage_rate_m3_s":rate,"effective_serial_resistance_ratio":R,"hydraulic_flow_m3_s":q,"front_filling_flow_m3_s":fill,"outlet_flow_m3_s":out,"liquid_feedback_status":"ONE_WAY_LIQUID_FEEDBACK_NOT_CLOSED_BY_DESIGN","resistance_monotonic":monotonic,"resistance_growth_onset_s":onset})
  for s in states:
   if s["bulk_volume_m3"]<=0 or s["pore_volume_m3"]<0 or not(0<s["porosity"]<1) or s["permeability_ratio"]<=0:raise ValueError("PHYSICAL_STATE_INVALID")
 terminal=temporal[-1];return {"status":"COMPLETE","case_id":row["case_id"],"source_overlay_sha256":OVERLAY_SHA,"pressure_condition":row["pressure_condition"],"terminal_pressure_pa":terminal["pressure_pa"],"terminal_outlet_flow_kg_s":terminal["outlet_flow_m3_s"]*RHO,"terminal_resistance_ratio":terminal["effective_serial_resistance_ratio"],"terminal_swelling_storage_m3":terminal["swelling_storage_volume_m3"],"full_wetting_time_s":next((x["time_s"] for x in temporal if x["wet_fraction"]>=1),None),"resistance_growth_onset_s":onset,"liquid_feedback_status":"ONE_WAY_LIQUID_FEEDBACK_NOT_CLOSED_BY_DESIGN","bookkeeping_status":"SOLID_PORE_BULK_VOLUME_CLOSED","whole_liquid_conservation":"NOT_CLAIMED_ONE_WAY_FEEDBACK_UNCLOSED","temporal":temporal}

def referenced_hashes():return {x["path"]:x["sha256"] for x in json.loads(REFS.read_text())["puckworks"]["files"]}
def expected_authority_bindings(bundle):
 """Expected mechanical bindings only; deliberately cannot mint owner authority."""
 ident=file_identity();return {"task_id":TASK,"lane_id":LANE_ID,"branch":BRANCH,"source_head":ident["head"],"source_tree":ident["tree"],"protocol_hash":sha(OUT/"SCI_MD_002B_PROTOCOL.json"),"matrix_hash":sha(OUT/"SCI_MD_002B_CASE_MATRIX.json"),"implementation_hash":sha(Path(__file__)),"source_overlay_hash":sha(OVERLAY),"puckworks_commit":PUCK_COMMIT,"puckworks_referenced_file_hashes":referenced_hashes(),"authorized_row_ids":adjudicative_row_ids(),"authorized_row_ids_sha256":adjudicative_row_ids_sha256(),"external_result_namespace":EXTERNAL_NAMESPACE,"worker_limit":1,"nested_thread_limit":1,"record_schema":RECORD_SCHEMA,"no_overwrite":True,"resume_semantics":"EXACT_RECORD_HASH_AND_AUTHORITY_ONLY"}
def validate_authority(path,bundle):
 if not path:raise PermissionError("SCI_MD_002B_ADJUDICATIVE_EXECUTION_NOT_AUTHORIZED")
 a=json.loads(Path(path).read_text()); ids=a.get("authorized_row_ids");cohort=adjudicative_row_ids()
 if ids!=cohort:raise PermissionError("AUTHORITY_MUST_BIND_EXACT_CANONICAL_435_ROW_COHORT")
 exp=expected_authority_bindings(bundle)
 for k,v in exp.items():
  if a.get(k)!=v:raise PermissionError(f"AUTHORITY_MISMATCH_{k}")
 if a.get("authorization_token")!=TOKEN or a.get("owner_role")!="HUMAN_REPOSITORY_OWNER":raise PermissionError("INDEPENDENT_OWNER_AUTHORITY_REQUIRED")
 try:
  if not a["authorization_date"].endswith("Z") or datetime.fromisoformat(a["authorization_date"].replace("Z","+00:00")).tzinfo is None:raise ValueError
 except (KeyError,TypeError,ValueError):raise PermissionError("AUTHORIZATION_DATE_INVALID")
 return a,sha(Path(path))
def record_hash(rec):return hashlib.sha256(canonical({k:v for k,v in rec.items() if k!="record_sha256"}).encode()).hexdigest()
def atomic_record(d,cid,rec,resume=False):
 d.mkdir(parents=True,exist_ok=True);final=d/f"{cid}.json"
 if final.exists():
  old=json.loads(final.read_text())
  if resume and old.get("record_sha256")==record_hash(old) and old.get("authority_sha256")==rec.get("authority_sha256") and old.get("case_id")==cid:return final,"EXACT_RESUME_VERIFIED"
  raise FileExistsError("IMMUTABLE_RECORD_EXISTS")
 rec=dict(rec);rec["record_sha256"]=record_hash(rec);tmp=d/f".{cid}.{os.getpid()}.tmp";tmp.write_text(canonical(rec));os.replace(tmp,final);return final,"CREATED"
def manifest(bundle,authority_hash,ids):
 files=sorted((bundle/"case_records").glob("*.json"));m={"schema_version":"ewp.sci_md_002b.external_manifest.v2","authority_sha256":authority_hash,"authorized_row_ids":ids,"record_count":len(files),"records":[{"name":p.name,"bytes":p.stat().st_size,"sha256":sha(p)} for p in files]};m["ordered_record_aggregate_sha256"]=hashlib.sha256("".join(x["sha256"] for x in m["records"]).encode()).hexdigest();(bundle/"manifest.json").write_text(canonical(m));return m
def execute_authorized(bundle_arg,authority_arg,resume=False):
 bundle=safe_bundle(bundle_arg);a,ah=validate_authority(authority_arg,bundle);matrix={r["case_id"]:r for r in matrix_rows()};ledger=bundle/"process_ledger.jsonl";start=utc()
 with ledger.open("a") as f:f.write(canonical({"pid":os.getpid(),"parent_pid":os.getppid(),"task_id":TASK,"command":" ".join(sys.argv),"working_directory":str(ROOT),"start_utc":start,"status":"RUNNING"}))
 for cid in a["authorized_row_ids"]:
  row=matrix[cid];base={"schema_version":RECORD_SCHEMA,"task_id":TASK,"lane_id":LANE_ID,"case_id":cid,"source_head":a["source_head"],"source_tree":a["source_tree"],"authority_sha256":ah,"protocol_sha256":a["protocol_hash"],"matrix_sha256":a["matrix_hash"],"implementation_sha256":a["implementation_hash"],"source_overlay_sha256":a["source_overlay_hash"],"parameters":row,"start_utc":utc(),"worker_pid":os.getpid()}
  try:result=simulate(row);status="COMPLETE"
  except ValueError as e:result={"error":str(e)};status="PHYSICAL_INVALID"
  except Exception as e:result={"error_type":type(e).__name__,"error":str(e)};status="NUMERICAL_FAILURE"
  atomic_record(bundle/"case_records",cid,{**base,"completion_utc":utc(),"execution_status":status,"result":result},resume)
 m=manifest(bundle,ah,a["authorized_row_ids"])
 with ledger.open("a") as f:f.write(canonical({"pid":os.getpid(),"task_id":TASK,"completion_utc":utc(),"status":"COMPLETE","record_count":m["record_count"]}))
 return m
def execute_adjudicative(bundle,authority,resume=False):return execute_authorized(bundle,authority,resume)

def verify_bundle(bundle_arg,authority_arg=None):
 b=safe_bundle(bundle_arg);m=json.loads((b/"manifest.json").read_text());seen=set()
 for x in m["records"]:
  p=b/"case_records"/x["name"]
  if not p.exists() or p.stat().st_size!=x["bytes"] or sha(p)!=x["sha256"]:raise ValueError("RECORD_MANIFEST_MISMATCH")
  r=json.loads(p.read_text());cid=r["case_id"]
  if cid in seen or r.get("record_sha256")!=record_hash(r):raise ValueError("DUPLICATE_OR_RECORD_HASH_INVALID")
  seen.add(cid)
 if set(seen)!=set(m["authorized_row_ids"]):raise ValueError("MISSING_OR_EXTRA_RECORD")
 if authority_arg:
  _,ah=validate_authority(authority_arg,b)
  if ah!=m["authority_sha256"]:raise ValueError("MANIFEST_AUTHORITY_MISMATCH")
 return m
def margin_class(m59,m911,u59,u911):
 if m59-u59>0 and m911-u911>0:return "PASS"
 if m59+u59<=0 or m911+u911<=0:return "REJECTED"
 return "NUMERICALLY_UNRESOLVED"
def temporal_signature(result,row,histories=None,tol=TEMPORAL_ABS_TOL):
 histories=histories or load_histories();series=histories[int(row["pressure_condition"].split("P")[1])];temporal=result.get("temporal")
 if not isinstance(temporal,list) or len(temporal)!=999:return False,"TEMPORAL_ROW_COUNT"
 required=set(protocol()["temporal_output"]["fields"]);prev_front=prev_wet=prev_res=-math.inf;first_wet=None
 for i,(x,src) in enumerate(zip(temporal,series)):
  if not required<=set(x):return False,"TEMPORAL_FIELD_MISSING"
  scalars=[x[k] for k in required if k not in ("cell_wetting_times_s","cell_wetting_ages_s","cell_swelling_storage_volumes_m3","cell_resistance_ratios","liquid_feedback_status") and x[k] is not None]
  if any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in scalars):return False,"TEMPORAL_NONFINITE"
  if abs(x["time_s"]-src["source_time_s"])>tol or abs(x["pressure_pa"]-src["observed_pressure_pa"])>tol:return False,"SOURCE_HISTORY_MISMATCH"
  if not(-tol<=x["front_position_m"]<=H0+tol and -tol<=x["wet_fraction"]<=1+tol) or x["front_position_m"]+tol<prev_front or x["wet_fraction"]+tol<prev_wet:return False,"FRONT_INVALID"
  wet=x["cell_wetting_times_s"];ages=x["cell_wetting_ages_s"];cell_storage=x["cell_swelling_storage_volumes_m3"];cell_resistance=x["cell_resistance_ratios"]
  if len(wet)!=row["axial_cells"] or not(len(ages)==len(wet)==len(cell_storage)==len(cell_resistance)):return False,"CELL_TEMPORAL_SHAPE"
  for w,a,storage_j,resistance_j in zip(wet,ages,cell_storage,cell_resistance):
   expected=0. if w is None else max(0.,x["time_s"]-w)
   if abs(a-expected)>tol:return False,"WETTING_AGE_IDENTITY"
   if expected<=tol and (abs(storage_j)>tol or resistance_j>1+tol):return False,"CELL_PREWET_SWELLING"
  any_wet=any(w is not None and x["time_s"]+tol>=w for w in wet)
  if any_wet and first_wet is None:first_wet=x["time_s"]
  if not any_wet and (abs(x["swelling_storage_volume_m3"])>tol or x["effective_serial_resistance_ratio"]>1+tol):return False,"PREWET_SWELLING"
  if prev_res>0 and x["effective_serial_resistance_ratio"]<prev_res*(1-RESISTANCE_REL_STEP_TOL)-tol:return False,"RESISTANCE_DEPARTURE_EXCEEDS_TOLERANCE"
  prev_front=x["front_position_m"];prev_wet=x["wet_fraction"];prev_res=x["effective_serial_resistance_ratio"]
 if row["cmax"]>0 and result.get("terminal_swelling_storage_m3",0)<=tol:return False,"POSTWET_STORAGE_MISSING"
 onset=result.get("resistance_growth_onset_s")
 if onset is not None and first_wet is not None and onset+tol<first_wet:return False,"ONSET_BEFORE_WETTING"
 full=next((x["time_s"] for x in temporal if x["wet_fraction"]>=1-tol),None)
 if result.get("full_wetting_time_s")!=full:return False,"FULL_WETTING_IDENTITY"
 return True,"PASS"

def reduce_bundle(bundle_arg,authority_arg,output=None):
 b=safe_bundle(bundle_arg);a,ah=validate_authority(authority_arg,b);m=verify_bundle(b,authority_arg);records={}
 if m.get("record_count")!=435 or m.get("authorized_row_ids")!=adjudicative_row_ids():raise ValueError("PACKAGE_VALIDITY_EXACT_COHORT_REQUIRED")
 for x in m["records"]:
  r=json.loads((b/"case_records"/x["name"]).read_text())
  if r.get("schema_version")!=RECORD_SCHEMA or r["source_head"]!=a["source_head"] or r.get("source_tree")!=a["source_tree"] or r["authority_sha256"]!=ah:raise ValueError("MIXED_SOURCE_AUTHORITY_OR_SCHEMA")
  records[r["case_id"]]=r
 matrix={r["case_id"]:r for r in matrix_rows()};controls={p:records.get(f"C0-SOURCE-P{p}-NOSWELL") for p in PRESSURES}
 if len(records)!=435 or any(not controls[p] or controls[p].get("execution_status")!="COMPLETE" or controls[p].get("result",{}).get("status")!="COMPLETE" for p in PRESSURES):raise ValueError("PACKAGE_VALIDITY_CONTROLS_OR_RECORDS_INVALID")
 candidates=[];histories=load_histories()
 bases=[r for r in matrix.values() if r["arm"]=="S1" and r["resolution"]=="BASE" and r["pressure_condition"]=="SOURCE_P5"]
 if len(bases)!=72:raise ValueError("PACKAGE_VALIDITY_EXPECTED_72_CANDIDATES")
 for first in bases:
  stem=(first["powder"],first["D_multiplier"],first["cmax"],first["accommodation"]);sets={}
  for res in ("BASE","REFINED"):
   group=[r for r in matrix.values() if r["arm"]=="S1" and r["resolution"]==res and (r["powder"],r["D_multiplier"],r["cmax"],r["accommodation"])==stem]
   if len(group)!=3 or any(x["case_id"] not in records for x in group):raise ValueError("PACKAGE_VALIDITY_CANDIDATE_COMPARATOR_MISSING")
   sets[res]={int(x["pressure_condition"].split("P")[1]):(x,records[x["case_id"]]) for x in group}
  all_records=[rec for group in sets.values() for _,rec in group.values()];valid=all(rec.get("execution_status")=="COMPLETE" and rec.get("result",{}).get("status")=="COMPLETE" for rec in all_records)
  item={"candidate":{"powder":stem[0],"D_multiplier":stem[1],"cmax":stem[2],"accommodation":stem[3]},"physical_numerical_valid":valid,"first_failed_gate":None,"candidate_disposition":None,"aggregate_comparison_eligible":False}
  if not valid:item.update(first_failed_gate="NUMERICAL_OR_PHYSICAL_VALIDITY",candidate_disposition="SCI_MD_002B_NUMERICAL_EXECUTION_INVALID",resistance_direction_status="NOT_EVALUATED",ordering_class="NOT_EVALUATED",temporal_signature_status="NOT_EVALUATED");candidates.append(item);continue
  results={res:{p:pair[1]["result"] for p,pair in group.items()} for res,group in sets.items()}
  q={res:{p:results[res][p]["terminal_outlet_flow_kg_s"] for p in PRESSURES} for res in results};marg={res:(q[res][5]-q[res][9],q[res][9]-q[res][11]) for res in results};u=(abs(marg["BASE"][0]-marg["REFINED"][0]),abs(marg["BASE"][1]-marg["REFINED"][1]));cls=margin_class(*marg["BASE"],*u)
  resdir=all(results["BASE"][p]["terminal_resistance_ratio"]>controls[p]["result"]["terminal_resistance_ratio"] for p in PRESSURES);item.update(M59_kg_s=marg["BASE"][0],M911_kg_s=marg["BASE"][1],U59_kg_s=u[0],U911_kg_s=u[1],ordering_class=cls,resistance_direction_status="PASS" if resdir else "FAIL")
  if not resdir:item.update(first_failed_gate="RESISTANCE_DIRECTION",candidate_disposition="SCI_MD_002B_REJECTED_WRONG_RESISTANCE_DIRECTION",temporal_signature_status="NOT_EVALUATED");candidates.append(item);continue
  if cls!="PASS":item.update(first_failed_gate="PRESSURE_ORDERING",candidate_disposition="SCI_MD_002B_PRESSURE_ORDERING_NUMERICALLY_UNRESOLVED" if cls=="NUMERICALLY_UNRESOLVED" else "SCI_MD_002B_REJECTED_WRONG_PRESSURE_ORDERING",temporal_signature_status="NOT_EVALUATED");candidates.append(item);continue
  temporal_checks=[temporal_signature(rec["result"],row,histories) for group in sets.values() for row,rec in group.values()];temporal_ok=all(x[0] for x in temporal_checks);item["temporal_signature_status"]="PASS" if temporal_ok else temporal_checks[next(i for i,x in enumerate(temporal_checks) if not x[0])][1]
  if not temporal_ok:item.update(first_failed_gate="TEMPORAL_SIGNATURE",candidate_disposition="SCI_MD_002B_ADDITIONAL_SWELLING_AND_DEFORMATION_DATA_REQUIRED");candidates.append(item);continue
  target={p:histories[p][-1]["observed_flow_kg_s"] for p in PRESSURES};residual={p:q["BASE"][p]-target[p] for p in PRESSURES};ref_residual={p:q["REFINED"][p]-target[p] for p in PRESSURES};item.update(candidate_disposition="SURVIVES_EARLY_GATES_PENDING_ASSUMPTION_REDUCTION",aggregate_comparison_eligible=True,terminal_residuals_kg_s=residual,refined_terminal_residuals_kg_s=ref_residual,terminal_flow_rmse_kg_s=math.sqrt(sum(v*v for v in residual.values())/3),terminal_flow_mae_kg_s=sum(abs(v) for v in residual.values())/3);candidates.append(item)
 if len(candidates)!=72:raise ValueError("PACKAGE_VALIDITY_EXPECTED_72_CANDIDATES")
 valid=[x for x in candidates if x["physical_numerical_valid"]];direction=[x for x in valid if x["resistance_direction_status"]=="PASS"];ordered=[x for x in direction if x["ordering_class"]=="PASS"];survivors=[x for x in ordered if x["temporal_signature_status"]=="PASS"]
 dependence={"passing_accommodation_values":sorted({x["candidate"]["accommodation"] for x in survivors}),"passing_powders":sorted({x["candidate"]["powder"] for x in survivors}),"passing_D_multipliers":sorted({x["candidate"]["D_multiplier"] for x in survivors}),"passing_cmax":sorted({x["candidate"]["cmax"] for x in survivors}),"phi_wet_epsilon_b0_sensitivity_axes_executed":False,"robustness_across_porosity_bounds_established":False,"secondary_flags":[]}
 if not valid:disp="SCI_MD_002B_NUMERICAL_EXECUTION_INVALID"
 elif not direction:disp="SCI_MD_002B_REJECTED_WRONG_RESISTANCE_DIRECTION"
 elif not ordered:disp="SCI_MD_002B_PRESSURE_ORDERING_NUMERICALLY_UNRESOLVED" if any(x["ordering_class"]=="NUMERICALLY_UNRESOLVED" for x in direction) else "SCI_MD_002B_REJECTED_WRONG_PRESSURE_ORDERING"
 elif not survivors:disp="SCI_MD_002B_ADDITIONAL_SWELLING_AND_DEFORMATION_DATA_REQUIRED"
 else:
  ac=dependence["passing_accommodation_values"];pw=dependence["passing_powders"]
  if ac==[0.]:disp="SCI_MD_002B_CAPABILITY_DEPENDS_ON_FIXED_HEIGHT_EXTREME"
  elif len(ac)==1:disp="SCI_MD_002B_ADDITIONAL_SWELLING_AND_DEFORMATION_DATA_REQUIRED";dependence["secondary_flags"].append("CAPABILITY_DEPENDS_ON_SINGLE_ACCOMMODATION_STATE")
  elif len(pw)==1:disp="SCI_MD_002B_CAPABILITY_DEPENDS_ON_UNMAPPED_PARTICLE_SIZE"
  else:disp="SCI_MD_002B_WETTING_AGE_SWELLING_CAPABILITY_SURVIVES_BOUNDED_SCREEN"
  if len(pw)==1:dependence["secondary_flags"].append("CAPABILITY_DEPENDS_ON_UNMAPPED_PARTICLE_SIZE")
 for x in survivors:x["candidate_disposition"]=disp
 result={"schema_version":"ewp.sci_md_002b.reduction.v3","authority_sha256":ah,"manifest_sha256":sha(b/"manifest.json"),"gate_precedence":protocol()["gates"],"candidate_count":len(candidates),"candidates":candidates,"assumption_dependence":dependence,"grind_identifiability":"GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED","aggregate_target":"terminal observed_flow_kg_s only; reference_model_flow_kg_s prohibited","aggregate_comparison_eligible_candidate_count":len(survivors),"disposition":disp}
 if output:Path(output).write_text(canonical(result))
 return result

def pilot_run(bundle_arg):
 b=safe_bundle(bundle_arg);rows={r["case_id"]:r for r in matrix_rows()};start=time.perf_counter();records=[];ledger=b/"process_ledger.jsonl";b.mkdir(parents=True,exist_ok=True);pilot_identity=b.name
 with ledger.open("a") as f:f.write(canonical({"task_id":TASK,"pid":os.getpid(),"parent_pid":os.getppid(),"command":" ".join(sys.argv),"working_directory":str(ROOT),"pilot_identity":pilot_identity,"start_utc":utc(),"status":"RUNNING"}))
 for cid in PILOT_IDS:
  result=simulate(rows[cid]);rec={"schema_version":RECORD_SCHEMA,"task_id":TASK,"lane_id":LANE_ID,"case_id":cid,"source_head":git("rev-parse","HEAD"),"source_tree":git("rev-parse","HEAD^{tree}"),"source_overlay_sha256":sha(OVERLAY),"parameters":rows[cid],"execution_status":"COMPLETE","result":result,"pilot_only":True,"scientific_reduction_authorized":False};atomic_record(b/"case_records",cid,rec);records.append(rec)
 m=manifest(b,"PILOT_NO_ADJUDICATIVE_AUTHORITY",list(PILOT_IDS));timing={"row_count":len(records),"completion_count":len(records),"failure_count":0,"wall_s":time.perf_counter()-start,"peak_rss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,"manifest_sha256":sha(b/"manifest.json"),"scientific_reducer_ran":False,"source_ordering_calculated":False,"complete_adjudicative_triplet":False};(b/"timing.json").write_text(canonical(timing))
 with ledger.open("a") as f:f.write(canonical({"task_id":TASK,"pid":os.getpid(),"parent_pid":os.getppid(),"pilot_identity":pilot_identity,"completion_utc":utc(),"status":"COMPLETE","completion_count":len(records),"failure_count":0}))
 return timing

def references():
 h=load_histories();const=nominal_rows(9,10);ci=cumulative_integral(const);k=hydraulic_anchor(h);s=front_from_integral(ci[-1],k);closed=math.sqrt(2*k*(9e5+PCAP)*10/(MU*PHI_WET));mo=swelling_ratio(50e-6,10,D0,.1,32)
 if abs(s-closed)>1e-14 or abs(mo-1.1108624452500107)>1e-4:raise RuntimeError("REFERENCE_PARITY_FAIL")
 print(canonical({"status":"PASS","constant_pressure_front_m":s,"mo_volume_ratio":mo}),end="")
def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True)
 for n in ("generate","verify","references"):sp.add_parser(n)
 p=sp.add_parser("pilot-run");p.add_argument("--bundle",required=True)
 for n in ("execute-adjudicative","reduce","verify-bundle"):
  p=sp.add_parser(n);p.add_argument("--bundle",required=True);p.add_argument("--authority");p.add_argument("--resume",action="store_true");p.add_argument("--output")
 a=ap.parse_args()
 if a.cmd=="generate":generate()
 elif a.cmd=="verify":verify_generated()
 elif a.cmd=="references":references()
 elif a.cmd=="pilot-run":print(canonical(pilot_run(a.bundle)),end="")
 elif a.cmd=="execute-adjudicative":print(canonical(execute_adjudicative(a.bundle,a.authority,a.resume)),end="")
 elif a.cmd=="verify-bundle":print(canonical({"status":"PASS","record_count":verify_bundle(a.bundle,a.authority)["record_count"]}),end="")
 elif a.cmd=="reduce":print(canonical(reduce_bundle(a.bundle,a.authority,a.output)),end="")
if __name__=="__main__":main()
