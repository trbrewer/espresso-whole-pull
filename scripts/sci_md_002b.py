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
POWDERS={"E":(.292,.708,27.48e-6/2,321.7e-6/2),"H":(.275,.725,28.20e-6/2,347.5e-6/2),"M":(.203,.797,30.23e-6/2,358.47e-6/2),"F":(.097,.903,31.59e-6/2,524e-6/2)}
TERMINAL_PRESSURES={5:450096.2,9:873024.9,11:1041717.4}
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
            t,solver_t,pressure_bar,nominal_bar,model_flow,source_flow,model_mass,source_mass=map(float,r)
            if t<=last or abs(solver_t-(t+3))>1e-9 or pressure_bar<0: raise ValueError(f"SOURCE_TIME_OR_PRESSURE_INVALID_{p}_{i}")
            rows.append({"source_time_s":t,"solver_time_s":solver_t,"pressure_pa":pressure_bar*1e5,"nominal_pressure_pa":nominal_bar*1e5,"model_flow_kg_s":model_flow*1e-3,"source_flow_kg_s":source_flow*1e-3,"model_mass_kg":model_mass*1e-3,"source_mass_kg":source_mass*1e-3})
            last=t
        if abs(rows[-1]["source_time_s"]-99.8999)>1e-12 or abs(rows[-1]["pressure_pa"]-TERMINAL_PRESSURES[p])>1e-7: raise ValueError(f"SOURCE_TERMINAL_IDENTITY_INVALID_{p}")
        result[p]=rows
    return result

def cumulative_integral(rows,pcap=PCAP):
    out=[0.0]
    for a,b in zip(rows,rows[1:]): out.append(out[-1]+.5*((a["pressure_pa"]+pcap)+(b["pressure_pa"]+pcap))*(b["source_time_s"]-a["source_time_s"]))
    return out
def invert_integral(rows,cumulative,target,pcap=PCAP):
    if target<=0:return rows[0]["source_time_s"]
    if target>cumulative[-1]:return None
    lo,hi=0,len(cumulative)-1
    while hi-lo>1:
        m=(lo+hi)//2
        if cumulative[m]<target:lo=m
        else:hi=m
    a,b=rows[lo],rows[hi]; dt=b["source_time_s"]-a["source_time_s"]; p0=a["pressure_pa"]+pcap; slope=(b["pressure_pa"]-a["pressure_pa"])/dt; need=target-cumulative[lo]
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
    hist=hist or load_histories(); r=hist[9][-1]; return (r["model_flow_kg_s"]/RHO)*MU*H0/(AREA*r["pressure_pa"])
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

def protocol(matrix_hash=None):
 return {"schema_version":"ewp.sci_md_002b.protocol.v2","task_id":TASK,"status":"CORRECTED_PREEXECUTION_PENDING_SECOND_REVIEW","change_declaration":"NO_GOVERNING_PHYSICS_CHANGE","source":{"overlay_path":str(OVERLAY.relative_to(ROOT)),"overlay_sha256":OVERLAY_SHA,"histories":{str(p):{"row_count":999,"terminal_time_s":99.8999,"terminal_pressure_pa":TERMINAL_PRESSURES[p]} for p in PRESSURES},"integration":"piecewise-linear pressure with exact trapezoidal cumulative integral; analytic within-segment inversion; no extrapolation","hydraulic_anchor":"one terminal P9 model-flow anchor shared unchanged"},"porosities":{"phi_wet":{"value":PHI_WET,"provenance":"PUCKWORKS_PINNED_REFERENCE_FOSTER_FITTED_NOT_EWP_SOURCE_MEASUREMENT","role":"REFERENCE_PRIMARY","sensitivity_bounds":[.173,.4]},"epsilon_b0":{"value":EPSILON_B0,"provenance":"PUCKWORKS_PINNED_REFERENCE_MO_NOMINAL_NOT_EWP_SOURCE_MEASUREMENT","role":"REFERENCE_PRIMARY","sensitivity_bounds":[.17,.4]}},"model":{"chain":"pressure history -> wetting time -> local age -> Mo swelling -> volume-consistent accommodation -> CK permeability -> serial resistance -> axial flow","one_way_balance":"front trajectory excludes swelling-storage feedback","liquid_status":"ONE_WAY_LIQUID_FEEDBACK_NOT_CLOSED_BY_DESIGN","two_way":"SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED"},"temporal_output":{"grid":"all 999 governed source timestamps for SOURCE rows; frozen 0.5 s grid plus terminal for nominal controls","fields":["time_s","pressure_pa","pressure_integral_pa_s","front_position_m","wet_fraction","cell_wetting_times_s","cell_wetting_ages_s","swelling_storage_volume_m3","swelling_storage_rate_m3_s","effective_serial_resistance_ratio","hydraulic_flow_m3_s","front_filling_flow_m3_s","outlet_flow_m3_s","liquid_feedback_status","resistance_growth_onset_s"]},"refinement":{"base":{"axial_cells":64,"radial_cells":32,"response_points":65},"refined":{"axial_cells":128,"radial_cells":48,"response_points":129},"uncertainty":"for each margin, abs(base margin-refined margin); PASS iff both base margins minus uncertainty >0; REJECTED iff either base margin plus uncertainty <=0; otherwise NUMERICALLY_UNRESOLVED"},"gates":["AUTHORITY_AND_ARTIFACT_VALIDITY","REFERENCE_AND_NUMERICAL_VALIDITY","PHYSICAL_STATE_AND_BOOKKEEPING_VALIDITY","RESISTANCE_DIRECTION","PRESSURE_ORDERING","TEMPORAL_SIGNATURE","ASSUMPTION_DEPENDENCE","PARTICLE_SIZE_AND_GRIND_IDENTIFIABILITY","AGGREGATE_COMPARISON"],"budget":{"row_count":len(matrix_rows()),"hard_max":HARD_CAP,"workers":1,"nested_threads":1,"memory_gib":16,"gpu":0},"pilot_row_ids":list(PILOT_IDS),"record_schema":RECORD_SCHEMA,"matrix_sha256":matrix_hash,"claim_boundary":["PHYSICAL_VALIDATION_NOT_ESTABLISHED","POST_OBSERVATION_MECHANISM_DISCRIMINATION","NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE","NO_COMBINED_MECHANISM_AUTHORIZATION","NO_SCI_LC_001B_AUTHORIZATION","GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED"]}

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
 return [{"source_time_s":i*.5,"solver_time_s":i*.5,"pressure_pa":pbar*1e5,"nominal_pressure_pa":pbar*1e5,"model_flow_kg_s":0.,"source_flow_kg_s":0.,"model_mass_kg":0.,"source_mass_kg":0.} for i in range(int(duration/.5)+1)]
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
  R=sum(s["resistance_ratio"] for s in states)/cells;pressure=src["pressure_pa"];q=k0*AREA*pressure/(MU*H0*R);full=front>=H0*(1-1e-12);out=q if full else 0.;fill=PHI_WET*AREA*(front-(temporal[-1]["front_position_m"] if temporal else 0))/(t-series[idx-1]["source_time_s"]) if idx else 0.
  if onset is None and R>1+1e-8:onset=t
  monotonic=True if prevR is None else R>=prevR-1e-10;prevR=R
  temporal.append({"time_s":t,"pressure_pa":pressure,"pressure_integral_pa_s":I,"front_position_m":front,"wet_fraction":front/H0,"cell_wetting_times_s":wet,"cell_wetting_ages_s":wetages,"swelling_storage_volume_m3":storage,"swelling_storage_rate_m3_s":rate,"effective_serial_resistance_ratio":R,"hydraulic_flow_m3_s":q,"front_filling_flow_m3_s":fill,"outlet_flow_m3_s":out,"liquid_feedback_status":"ONE_WAY_LIQUID_FEEDBACK_NOT_CLOSED_BY_DESIGN","resistance_monotonic":monotonic,"resistance_growth_onset_s":onset})
  for s in states:
   if s["bulk_volume_m3"]<=0 or s["pore_volume_m3"]<0 or not(0<s["porosity"]<1) or s["permeability_ratio"]<=0:raise ValueError("PHYSICAL_STATE_INVALID")
 terminal=temporal[-1];return {"status":"COMPLETE","case_id":row["case_id"],"source_overlay_sha256":OVERLAY_SHA,"pressure_condition":row["pressure_condition"],"terminal_pressure_pa":terminal["pressure_pa"],"terminal_outlet_flow_kg_s":terminal["outlet_flow_m3_s"]*RHO,"terminal_resistance_ratio":terminal["effective_serial_resistance_ratio"],"terminal_swelling_storage_m3":terminal["swelling_storage_volume_m3"],"full_wetting_time_s":next((x["time_s"] for x in temporal if x["wet_fraction"]>=1),None),"resistance_growth_onset_s":onset,"liquid_feedback_status":"ONE_WAY_LIQUID_FEEDBACK_NOT_CLOSED_BY_DESIGN","bookkeeping_status":"SOLID_PORE_BULK_VOLUME_CLOSED","whole_liquid_conservation":"NOT_CLAIMED_ONE_WAY_FEEDBACK_UNCLOSED","temporal":temporal}

def referenced_hashes():return {x["path"]:x["sha256"] for x in json.loads(REFS.read_text())["puckworks"]["files"]}
def expected_authority(rows,bundle):
 ident=file_identity();return {"authorization_token":TOKEN,"task_id":TASK,"lane_id":LANE_ID,"branch":BRANCH,"source_head":ident["head"],"source_tree":ident["tree"],"protocol_hash":sha(OUT/"SCI_MD_002B_PROTOCOL.json"),"matrix_hash":sha(OUT/"SCI_MD_002B_CASE_MATRIX.json"),"implementation_hash":sha(Path(__file__)),"source_overlay_hash":sha(OVERLAY),"puckworks_commit":PUCK_COMMIT,"puckworks_referenced_file_hashes":referenced_hashes(),"authorized_row_ids":rows,"external_result_namespace":EXTERNAL_NAMESPACE,"worker_limit":1,"nested_thread_limit":1,"record_schema":RECORD_SCHEMA,"no_overwrite":True,"resume_semantics":"EXACT_RECORD_HASH_AND_AUTHORITY_ONLY"}
def validate_authority(path,bundle):
 if not path:raise PermissionError("SCI_MD_002B_ADJUDICATIVE_EXECUTION_NOT_AUTHORIZED")
 a=json.loads(Path(path).read_text()); ids=a.get("authorized_row_ids")
 if not isinstance(ids,list) or not ids or len(ids)!=len(set(ids)):raise PermissionError("AUTHORITY_ROW_SET_INVALID")
 exp=expected_authority(ids,bundle)
 for k,v in exp.items():
  if a.get(k)!=v:raise PermissionError(f"AUTHORITY_MISMATCH_{k}")
 if not isinstance(a.get("owner_role"),str) or not a["owner_role"] or not isinstance(a.get("authorization_date"),str) or not a["authorization_date"]:raise PermissionError("AUTHORITY_OWNER_OR_DATE_MISSING")
 matrix={r["case_id"]:r for r in matrix_rows()}
 if any(i not in matrix or matrix[i]["arm"] not in ("S1","C0") for i in ids):raise PermissionError("AUTHORITY_BROADENED_OR_UNKNOWN_ROW")
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
def reduce_bundle(bundle_arg,authority_arg,output=None):
 b=safe_bundle(bundle_arg);a,ah=validate_authority(authority_arg,b);m=verify_bundle(b,authority_arg);records={}
 for x in m["records"]:
  r=json.loads((b/"case_records"/x["name"]).read_text())
  if r["source_head"]!=a["source_head"] or r["authority_sha256"]!=ah:raise ValueError("MIXED_SOURCE_OR_AUTHORITY")
  records[r["case_id"]]=r
 matrix={r["case_id"]:r for r in matrix_rows()};candidates=[]
 bases=[r for r in matrix.values() if r["arm"]=="S1" and r["resolution"]=="BASE" and r["pressure_condition"]=="SOURCE_P5"]
 for first in bases:
  stem=(first["powder"],first["D_multiplier"],first["cmax"],first["accommodation"]);sets={}
  for res in ("BASE","REFINED"):
   group=[r for r in matrix.values() if r["arm"]=="S1" and r["resolution"]==res and (r["powder"],r["D_multiplier"],r["cmax"],r["accommodation"])==stem]
   if any(x["case_id"] not in records for x in group):continue
   sets[res]={int(x["pressure_condition"].split("P")[1]):records[x["case_id"]]["result"] for x in group}
  if set(sets)!={"BASE","REFINED"}:continue
  q={res:{p:sets[res][p]["terminal_outlet_flow_kg_s"] for p in PRESSURES} for res in sets};marg={res:(q[res][5]-q[res][9],q[res][9]-q[res][11]) for res in sets};u=(abs(marg["BASE"][0]-marg["REFINED"][0]),abs(marg["BASE"][1]-marg["REFINED"][1]));cls=margin_class(*marg["BASE"],*u)
  controls={p:records.get(f"C0-SOURCE-P{p}-NOSWELL") for p in PRESSURES};resdir=all(controls[p] and sets["BASE"][p]["terminal_resistance_ratio"]>controls[p]["result"]["terminal_resistance_ratio"] for p in PRESSURES)
  temporal=all(x["liquid_feedback_status"]=="ONE_WAY_LIQUID_FEEDBACK_NOT_CLOSED_BY_DESIGN" and x["terminal_swelling_storage_m3"]>0 and x["resistance_growth_onset_s"] is not None for x in sets["BASE"].values())
  candidates.append({"candidate":stem,"M59":marg["BASE"][0],"M911":marg["BASE"][1],"U59":u[0],"U911":u[1],"ordering_class":cls,"resistance_direction_pass":resdir,"temporal_signature_pass":temporal})
 # Gate precedence: package/reference/physical completeness precedes candidate science.
 early_invalid=any(r["execution_status"]!="COMPLETE" or r["result"].get("status")!="COMPLETE" for r in records.values())
 if early_invalid:disp="SCI_MD_002B_NUMERICAL_EXECUTION_INVALID"
 elif any(not x["resistance_direction_pass"] for x in candidates):disp="SCI_MD_002B_REJECTED_WRONG_RESISTANCE_DIRECTION"
 elif any(x["ordering_class"]=="PASS" and not x["temporal_signature_pass"] for x in candidates):disp="SCI_MD_002B_ADDITIONAL_SWELLING_AND_DEFORMATION_DATA_REQUIRED"
 elif any(x["ordering_class"]=="PASS" for x in candidates):
  passing=[x for x in candidates if x["ordering_class"]=="PASS"]
  fixed_only=all(x["candidate"][3]==0 for x in passing); powders={x["candidate"][0] for x in passing}
  disp="SCI_MD_002B_CAPABILITY_DEPENDS_ON_FIXED_HEIGHT_EXTREME" if fixed_only else "SCI_MD_002B_CAPABILITY_DEPENDS_ON_UNMAPPED_PARTICLE_SIZE" if len(powders)==1 else "SCI_MD_002B_WETTING_AGE_SWELLING_CAPABILITY_SURVIVES_BOUNDED_SCREEN"
 elif any(x["ordering_class"]=="NUMERICALLY_UNRESOLVED" for x in candidates):disp="SCI_MD_002B_PRESSURE_ORDERING_NUMERICALLY_UNRESOLVED"
 else:disp="SCI_MD_002B_REJECTED_WRONG_PRESSURE_ORDERING"
 result={"schema_version":"ewp.sci_md_002b.reduction.v2","authority_sha256":ah,"manifest_sha256":sha(b/"manifest.json"),"gate_precedence":protocol()["gates"],"candidate_count":len(candidates),"candidates":candidates,"assumption_dependence":"EVALUATE_ACCOMMODATION_AND_PARTICLE_PEERS_BEFORE_AGGREGATE","grind_identifiability":"GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED","aggregate_comparison":"ONLY_FOR_EARLIER_GATE_SURVIVORS","disposition":disp}
 if output:Path(output).write_text(canonical(result))
 return result

def pilot_run(bundle_arg):
 b=safe_bundle(bundle_arg);rows={r["case_id"]:r for r in matrix_rows()};start=time.perf_counter();records=[];ledger=b/"process_ledger.jsonl";b.mkdir(parents=True,exist_ok=True)
 with ledger.open("a") as f:f.write(canonical({"task_id":TASK,"pid":os.getpid(),"parent_pid":os.getppid(),"command":" ".join(sys.argv),"working_directory":str(ROOT),"start_utc":utc(),"status":"RUNNING_PILOT_ATTEMPT3"}))
 for cid in PILOT_IDS:
  result=simulate(rows[cid]);rec={"schema_version":RECORD_SCHEMA,"task_id":TASK,"lane_id":LANE_ID,"case_id":cid,"source_head":git("rev-parse","HEAD"),"source_tree":git("rev-parse","HEAD^{tree}"),"source_overlay_sha256":sha(OVERLAY),"parameters":rows[cid],"execution_status":"COMPLETE","result":result,"pilot_only":True,"scientific_reduction_authorized":False};atomic_record(b/"case_records",cid,rec);records.append(rec)
 m=manifest(b,"PILOT_NO_ADJUDICATIVE_AUTHORITY",list(PILOT_IDS));timing={"row_count":len(records),"completion_count":len(records),"failure_count":0,"wall_s":time.perf_counter()-start,"peak_rss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,"manifest_sha256":sha(b/"manifest.json"),"scientific_reducer_ran":False,"source_ordering_calculated":False,"complete_adjudicative_triplet":False};(b/"timing.json").write_text(canonical(timing));return timing

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
