#!/usr/bin/env python3
"""Task-local XSV-ENS-001 ensemble runtime; heavy evidence remains external."""
from __future__ import annotations

import argparse, contextlib, csv, hashlib, importlib.util, io, json, math, os
from pathlib import Path
import platform, subprocess, sys, time
from collections import deque

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CASE = ROOT / "verification/cases/xsv_ens_001"
PROTOCOL = json.loads((CASE / "XSV_ENS_001_PROTOCOL.json").read_text())
AXES = {"X": (0,1,2), "Y": (1,0,2), "Z": (2,1,0)}
FIELDS = ["case_id","geometry_id","family","state","L","voxel_um","seed","relation","parent_id","direction","force","precision","purpose"]

def canonical(v): return (json.dumps(v, sort_keys=True, separators=(",",":")) + "\n").encode()
def sha_bytes(v): return hashlib.sha256(v).hexdigest()
def sha_file(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()
def module(path, name):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def write_json(path, value): Path(path).write_bytes(canonical(value))

def inventory(_):
    def out(cmd):
        try:return subprocess.check_output(cmd,text=True,stderr=subprocess.STDOUT).strip()
        except Exception as e:return f"UNAVAILABLE:{e}"
    import psutil
    try:
        import taichi as ti; tv=".".join(map(str,ti.__version__))
    except Exception as e: tv=f"UNAVAILABLE:{e}"
    gpu=out(["nvidia-smi","--query-gpu=name,memory.total,driver_version","--format=csv,noheader,nounits"])
    cpu=out(["lscpu","-J"])
    result={"schema_version":"espresso.whole_pull.xsv_ens_001.inventory.v1","timestamp_utc":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),"cpu_lscpu":json.loads(cpu) if cpu.startswith('{') else cpu,"physical_cores":psutil.cpu_count(logical=False),"logical_cpus":psutil.cpu_count(),"ram_bytes":psutil.virtual_memory().total,"gpu":gpu,"cuda_runtime":out(["nvidia-smi","--query-gpu=compute_cap","--format=csv,noheader"]),"taichi":tv,"python":platform.python_version(),"compiler":out(["gcc","--version"]).splitlines()[0],"os":platform.platform(),"storage":out(["df","-B1",str(ROOT)]).splitlines()[-1],"openfoam_context":out(["foamVersion"])}
    print(json.dumps(result,indent=2)); return result

def connectivity(solid):
    fluid=~solid; L=solid.shape[0]; comp=np.full(solid.shape,-1,np.int32); lift=np.zeros(solid.shape+(3,),np.int32)
    counts=[0,0,0]; winds=[False]*3; cid=0
    for raw in np.argwhere(fluid):
        s=tuple(map(int,raw))
        if comp[s]>=0: continue
        comp[s]=cid; q=deque([s]); members=[]; cw=[False]*3
        while q:
            n=q.popleft(); members.append(n); base=lift[n].copy()
            for a in range(3):
                for step in (-1,1):
                    rr=list(n); rr[a]+=step; w=tuple(x%L for x in rr)
                    if not fluid[w]: continue
                    proposed=base.copy(); proposed[a]+=step
                    if comp[w]<0: comp[w]=cid; lift[w]=proposed; q.append(w)
                    elif comp[w]==cid:
                        d=proposed-lift[w]
                        for k in range(3): cw[k] |= bool(d[k])
        for k in range(3):
            if cw[k]: counts[k]+=len(members); winds[k]=True
        cid+=1
    return {f"phi_connected_{'xyz'[k]}":counts[k]/solid.size for k in range(3)} | {f"through_{'xyz'[k]}":winds[k] for k in range(3)}

def descriptors(solid):
    from scipy.ndimage import distance_transform_edt
    from skimage.measure import euler_number
    fluid=~solid; dist=distance_transform_edt(fluid); d=dist[fluid]
    faces=sum(np.count_nonzero(solid != np.roll(solid,1,a)) for a in range(3))
    conn=connectivity(solid)
    return {"phi_gross":float(fluid.mean()),"solid_fraction":float(solid.mean()),"specific_interfacial_area_lu":faces/solid.size,"pore_distance_q10":float(np.quantile(d,.1)),"pore_distance_q50":float(np.quantile(d,.5)),"pore_distance_q90":float(np.quantile(d,.9)),"euler_characteristic":int(euler_number(fluid,connectivity=3)),"isolated_void_fraction":float(fluid.mean()-max(conn[f"phi_connected_{a}"] for a in 'xyz'))} | conn

def generate_pack(puck, L, voxel, phis, amp, hlen, seed):
    gen=module(Path(puck)/"puckworks/models/brewer2026/pack_generator.py",f"gen_{os.getpid()}")
    s,meta=gen.make_pack(L=L,voxel_um=voxel,gs=1.3,phis_target=phis,hetero_amp=amp,hetero_len=hlen,seed=seed,batch=64,verbose=False,r_um=None,w_floor=.25)
    return np.asarray(s,bool),meta

def restrict(solid, fraction, token):
    from scipy.ndimage import distance_transform_edt
    fluid=~solid; d=distance_transform_edt(fluid); xyz=np.argwhere(fluid)
    ranked=sorted((float(d[tuple(v)]),hashlib.sha256(f"{token}|{v[0]}|{v[1]}|{v[2]}".encode()).digest(),tuple(v)) for v in xyz)
    out=solid.copy()
    for _,_,v in ranked[:round(fraction*len(ranked))]: out[v]=True
    return out

def geometry_from_row(row,puck):
    L=int(row["L"]); seed=int(row["seed"]); state=json.loads(row["state"])
    solid,meta=generate_pack(puck,L,float(row["voxel_um"]),state.get("phis",.55),state.get("amp",0),state.get("hlen",8),seed)
    if state.get("restriction",0): solid=restrict(solid,state["restriction"],row["parent_id"] or row["geometry_id"])
    return solid,meta

def localization(ux,solid,ncol=4):
    u=ux.copy(); u[solid]=0; L=u.shape[1]; edges=np.linspace(0,L,ncol+1,dtype=int); qs=[]
    for i in range(ncol):
      for j in range(ncol): qs.append(float(u[:,edges[i]:edges[i+1],edges[j]:edges[j+1]].mean()))
    q=np.array(qs); norm=q/q.mean(); pos=np.clip(norm,1e-12,None); order=np.sort(np.maximum(q,0))[::-1]
    shares=order/order.sum(); gini=float(np.sum(np.abs(norm[:,None]-norm[None,:]))/(2*len(norm)**2*norm.mean()))
    return {"velocity_cv":float(np.std(norm,ddof=1)),"flux_gini":gini,"top_10_flow_share":float(shares[:max(1,math.ceil(.1*len(q)))].sum()),"top_25_flow_share":float(shares[:max(1,len(q)//4)].sum()),"normalized_flow_entropy":float(-np.sum(shares*np.log(np.clip(shares,1e-15,None)))/np.log(len(shares)))}

def solve(solid,puck,precision,force,max_steps=50000):
    lb=module(Path(puck)/"puckworks/models/brewer2026/lb_taichi.py",f"lb_{os.getpid()}")
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf),contextlib.redirect_stderr(buf):
        lb.init_lb(arch="gpu",dtype=precision)
        r=lb.solve(solid,g=force,tau_plus=1.2,max_steps=max_steps,check=200,rtol=1e-6,min_steps=1500,verbose=False)
    phi=float((~solid).mean()); q=float(r["q"]); nu=float(r["nu"]); kg=nu*q/force; kv=kg/phi; umax=float(np.max(np.abs(r["ux"])))
    return {"q_box_lu":q,"phi_gross":phi,"u_void_lu":q/phi,"nu_lu":nu,"K_gross_lu2":kg,"K_void_lu2":kv,"gross_void_identity_residual":abs(kg-phi*kv),"puckworks_K_void_lu2":float(r["k"]),"steps":int(r["steps"]),"wall_seconds":float(r["seconds"]),"converged":int(r["steps"])<max_steps,"u_max_lu":umax,"Mach":umax*math.sqrt(3),"ux":r["ux"],"log":buf.getvalue()}

def pilot(args):
    root=Path(args.evidence); root.mkdir(parents=True,exist_ok=True); inv=inventory(None)
    cases=[]; solid,meta=generate_pack(args.puckworks,40,30,.55,0,8,42)
    for precision in ("f64","f32"):
      for force in ((5e-7,1e-6,2e-6) if precision=="f64" else (1e-5,)):
        s=solve(solid,args.puckworks,precision,force); ux=s.pop("ux"); log=s.pop("log")
        rec={"case_id":f"ANCHOR-{precision}-{force:.0e}","precision":precision,"force":force,**s,**localization(ux,solid),**descriptors(solid)}
        cases.append(rec); (root/f"{rec['case_id']}.log").write_text(log); np.save(root/f"{rec['case_id']}-ux.npy",ux)
    ref=next(x for x in cases if x["case_id"]=="ANCHOR-f64-1e-06"); f32=next(x for x in cases if x["precision"]=="f32")
    force64=[x for x in cases if x["precision"]=="f64"]
    qg=np.array([x["q_box_lu"]/x["force"] for x in force64]); linearity=float((qg.max()-qg.min())/qg.mean())
    qualification={"f32_K_relative_difference":abs(f32["K_gross_lu2"]/ref["K_gross_lu2"]-1),"f32_localization_cv_relative_difference":abs(f32["velocity_cv"]/ref["velocity_cv"]-1),"force_q_over_g_range_relative":linearity,"accepted_anchor_K":1.7919979172502785,"anchor_K_relative_difference":abs(ref["K_gross_lu2"]/1.7919979172502785-1)}
    qualification["f32_qualified"]=qualification["f32_K_relative_difference"]<=.01 and qualification["f32_localization_cv_relative_difference"]<=.05 and f32["Mach"]<.05
    qualification["force_qualified"]=linearity<=.01 and max(x["Mach"] for x in force64)<.05
    result={"schema_version":"espresso.whole_pull.xsv_ens_001.pilot.v1","evidence_class":"NUMERICAL_QUALIFICATION_ONLY","inventory":inv,"anchor_geometry":meta,"cases":cases,"qualification":qualification,"spatial_discretization":"PENDING_THREE_LEVEL_CONTINUOUS_GEOMETRY_STUDY"}
    write_json(root/"pilot.json",result); print(json.dumps(result,indent=2)); return result

def freeze(args):
    pilot=json.loads(Path(args.pilot).read_text()); prec="f32" if pilot["qualification"]["f32_qualified"] else "f64"; force=1e-5 if prec=="f32" else 1e-6
    sizes=[24,32,40,56,72]; seeds=PROTOCOL["ensemble"]["seeds"][:8]; rows=[]
    def add(gid,family,state,L,seed,rel="INDEPENDENT_REALIZATIONS",parent="",dirs=("X",),purpose="SCORED"):
      for d in dirs:
       rows.append({"case_id":f"{gid}-{d}","geometry_id":gid,"family":family,"state":json.dumps(state,separators=(",",":"),sort_keys=True),"L":L,"voxel_um":30,"seed":seed,"relation":rel,"parent_id":parent,"direction":d,"force":force,"precision":prec,"purpose":purpose})
    for L in sizes:
      for seed in seeds: add(f"BASE-L{L}-S{seed}","BASELINE",{"phis":.55,"amp":0,"hlen":8},L,seed)
    for phis in (.50,.55,.60,.64):
      for seed in seeds: add(f"SF{int(phis*100)}-L40-S{seed}","SOLID_FRACTION",{"phis":phis,"amp":0,"hlen":8},40,seed,"RELATED_NON_NESTED")
    for seed in seeds[:4]:
      parent=f"BASE-L40-S{seed}"
      for frac in (0,.10,.20,.30,.40): add(f"DEP{int(frac*100):02}-L40-S{seed}","THROAT_RESTRICTION",{"phis":.55,"amp":0,"hlen":8,"restriction":frac},40,seed,"PAIRED_TRANSFORMATION",parent)
    for amp in (1,2):
      for hlen in (4,8):
       for seed in seeds: add(f"H{amp}-C{hlen}-L40-S{seed}","HETEROGENEITY_FABRIC",{"phis":.55,"amp":amp,"hlen":hlen},40,seed)
    for seed in seeds[:4]:
      for state,name in [({"phis":.55,"amp":0,"hlen":8},"BASE"),({"phis":.64,"amp":0,"hlen":8},"SF64"),({"phis":.55,"amp":0,"hlen":8,"restriction":.30},"DEP30"),({"phis":.55,"amp":2,"hlen":8},"H2")]: add(f"DIR-{name}-L40-S{seed}","DIRECTIONAL",state,40,seed,"INDEPENDENT_REALIZATIONS","",("X","Y","Z"),"SCORED_DIRECTIONAL")
    csvp=CASE/"XSV_ENS_001_SCORED_MATRIX.csv"
    with csvp.open("w",newline="") as f: w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    write_json(CASE/"XSV_ENS_001_SCORED_MATRIX.json",{"schema_version":"espresso.whole_pull.xsv_ens_001.matrix.v1","frozen_from_pilot_sha256":sha_file(args.pilot),"precision":prec,"force":force,"rows":rows,"run_identity_count":len(rows),"bimodal":"NOT_EXECUTED_RESOLUTION_LIMIT_PENDING_PILOT","sequential_minimum_n":8,"sequential_batch_n":4,"sequential_maximum_n":24})
    print(json.dumps({"rows":len(rows),"precision":prec,"force":force}))

def run_case(args):
    with (CASE/"XSV_ENS_001_SCORED_MATRIX.csv").open() as f: matches=[r for r in csv.DictReader(f) if r["case_id"]==args.case_id]
    if len(matches)!=1: raise SystemExit("case identity not unique")
    row=matches[0]; out=Path(args.evidence)/"runs"/args.case_id
    if (out/"result.json").exists(): print((out/"result.json").read_text()); return
    out.mkdir(parents=True,exist_ok=True); solid,meta=geometry_from_row(row,args.puckworks); d=descriptors(solid); axis=row["direction"].lower()
    rec={"schema_version":"espresso.whole_pull.xsv_ens_001.run.v1",**row,"geometry_sha256":sha_bytes(np.ascontiguousarray(solid,np.uint8).tobytes()),"generator_metadata":meta,**d,"status":"DISCONNECTED_GEOMETRY" if not d[f"through_{axis}"] else "PENDING"}
    np.save(out/"solid.npy",solid)
    if rec["status"]=="PENDING":
      try:
       oriented=np.transpose(solid,AXES[row["direction"]]); s=solve(oriented,args.puckworks,row["precision"],float(row["force"])); ux=s.pop("ux"); log=s.pop("log"); rec.update(s); rec.update(localization(ux,oriented)); rec["status"]="PASS" if s["converged"] and s["Mach"]<.05 else ("MACH_LIMIT_FAILURE" if s["Mach"]>=.05 else "NONCONVERGED"); np.save(out/"ux.npy",ux); (out/"solver.log").write_text(log)
      except MemoryError as e: rec.update(status="GPU_ALLOCATION_FAILURE",error=str(e))
      except Exception as e: rec.update(status="NUMERICAL_INSTABILITY",error=repr(e))
    write_json(out/"result.json",rec); print(json.dumps(rec,indent=2))

def verify(_):
    p=PROTOCOL; assert p["targets"]=={"primary":0.373506,"supporting":[0.389226,0.395294],"rounded_substitution_prohibited":True}
    phi=.4; q=2e-5; nu=.2; g=1e-6; kg=nu*q/g; kv=nu*(q/phi)/g; assert math.isclose(kg,phi*kv) and not math.isclose(kg,kv)
    assert AXES["Y"]==(1,0,2) and AXES["Z"]==(2,1,0)
    print(json.dumps({"hydraulic_semantics":"PASS","exact_targets":"PASS","axis_transposition":"PASS","complete_tensor_claim":"PROHIBITED"}))

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    sp.add_parser("inventory")
    p=sp.add_parser("pilot"); p.add_argument("--puckworks",required=True); p.add_argument("--evidence",required=True)
    p=sp.add_parser("freeze-matrix"); p.add_argument("--pilot",required=True)
    p=sp.add_parser("run"); p.add_argument("--puckworks",required=True); p.add_argument("--evidence",required=True); p.add_argument("--case-id",required=True)
    sp.add_parser("verify")
    a=ap.parse_args(); {"inventory":inventory,"pilot":pilot,"freeze-matrix":freeze,"run":run_case,"verify":verify}[a.cmd](a)
if __name__=="__main__": main()
