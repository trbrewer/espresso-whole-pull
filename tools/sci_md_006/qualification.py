"""Real conditional-Darcy gauge and reduced/full parity execution."""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import numpy as np
from tools.sci_md_004_stage_e1_hydraulic import generated_case_hash,materialize
from .core import DIFFUSIVITY,predict
from .production_adapter import (ALTERNATE_PRESSURE_PA,DENSITY_KG_M3,PRESSURE_PA,boundary_time,execute,permeability,predictions,scenario,traces)

def rel(a,b):return abs(a-b)/max(abs(b),1e-30)
def covering_table(observations,inventories):
    flows=sorted({r.flow_m3_s for r in observations});ends=sorted({r.upper_mass_kg for r in observations});inv=sorted(inventories.values())
    q=(flows[0],flows[len(flows)//2],flows[-1]);m=(ends[0],ends[len(ends)//2],ends[-1]);ks=(.002,math.sqrt(.002*.5),.5);cs=(.2,math.sqrt(.2*100),100.);ivs=(inv[0],inv[-1])
    design=((0,0,0,0,0),(1,1,1,1,1),(2,2,2,2,0),(0,2,1,2,1),(2,0,1,0,0),(0,1,2,1,1),(2,1,0,1,0),(1,0,2,2,1),(1,2,0,0,0))
    return [{"case_id":f"P{i+1:02d}","flow_m3_s":q[a],"end_mass_kg":m[b],"k_1_s":ks[c],"csat_kg_m3":cs[d],"inventory_mass_fraction":ivs[e]} for i,(a,b,c,d,e) in enumerate(design)]

def fraction_boundaries(rows,end_mass):
    found=sorted({(r.fraction_id,r.lower_mass_kg,min(r.upper_mass_kg,end_mass)) for r in rows if r.lower_mass_kg<end_mass})
    return [x for x in found if x[2]>x[1]]

def gauge_invariance(root,executable,output,observations,inventories):
    output.mkdir(parents=True,exist_ok=False)
    flows=sorted({r.flow_m3_s for r in observations});selected=(flows[0],flows[len(flows)//2],flows[-1]);params={s:(.03162277660168379,4.47213595499958) for s in DIFFUSIVITY};records=[];passed=True
    end_mass=min(.010,max(r.upper_mass_kg for r in observations))
    for index,q in enumerate(selected):
        pair=[]
        for label,pressure in (("canonical",PRESSURE_PA),("alternate",ALTERNATE_PRESSURE_PA)):
            s=scenario(root,q,end_mass,{x:0 for x in DIFFUSIVITY},params,pressure,cells=32,dt_s=.05,zero_inventory=True);case,metrics,meta=execute(root,executable,output,f"gauge_zero_{index}_{label}",s);water,_=traces(case);last=water[-1]
            duplicate=output/f"gauge_zero_{index}_{label}_duplicate";materialize(s,duplicate,1)
            item={"flow":q,"gauge":label,"pressure_pa":pressure,"permeability_m2":permeability(q,pressure),"outlet_flow_m3_s":float(last["outlet_flow_m3_s"]),"cup_water_mass_kg":float(last["cup_water_mass_kg"]),"flow_relative_error":rel(float(last["outlet_flow_m3_s"]),q),"liquid_balance_residual_kg":float(last["liquid_balance_residual_kg"]),"min_saturation":float(last["min_saturation"]),"max_saturation":float(last["max_saturation"]),"executable_sha256":meta["executable_hash"],"deterministic_input_hash_match":generated_case_hash(case)==generated_case_hash(duplicate)};pair.append(item)
        pair_record={"flow_m3_s":q,"cases":pair,"flow_gauge_relative_difference":rel(pair[0]["outlet_flow_m3_s"],pair[1]["outlet_flow_m3_s"]),"cup_water_gauge_relative_difference":rel(pair[0]["cup_water_mass_kg"],pair[1]["cup_water_mass_kg"])};pair_record["pass"]=all(x["flow_relative_error"]<=1e-8 and abs(x["liquid_balance_residual_kg"])<=1e-12 and x["min_saturation"]>=-1e-14 and x["max_saturation"]<=1+1e-14 and x["deterministic_input_hash_match"] for x in pair) and pair_record["flow_gauge_relative_difference"]<=1e-8 and pair_record["cup_water_gauge_relative_difference"]<=1e-8;passed &= pair_record["pass"];records.append(pair_record)
    q=selected[1];rows=[r for r in observations if r.flow_m3_s==q];bounds=fraction_boundaries(rows,end_mass);inv={s:sum(v for (e,x),v in inventories.items() if x==s)/len({e for e,x in inventories if x==s}) for s in DIFFUSIVITY};species=[]
    for label,pressure in (("canonical",PRESSURE_PA),("alternate",ALTERNATE_PRESSURE_PA)):
        s=scenario(root,q,end_mass,inv,params,pressure,cells=32,dt_s=.05);case,metrics,meta=execute(root,executable,output,f"gauge_species_{label}",s);species.append({"label":label,"prediction":predictions(case,bounds,q),"metrics":metrics})
    by={};endpoint=[]
    for name in DIFFUSIVITY:
        keys=[k for k in species[0]["prediction"] if k[1]==name];a=np.array([species[0]["prediction"][k] for k in keys]);b=np.array([species[1]["prediction"][k] for k in keys]);by[name]=float(np.sqrt(np.mean((a-b)**2))/max(np.mean(a),1e-30));endpoint.append(rel(species[0]["metrics"]["species"][name]["cup_mass_kg"],species[1]["metrics"]["species"][name]["cup_mass_kg"]))
    species_pass=all(x<=1e-8 for x in by.values()) and all(x<=1e-8 for x in endpoint);passed &= species_pass
    return {"zero_inventory_pairs":records,"nonzero_species_nrmse":by,"nonzero_endpoint_relative_discrepancy":dict(zip(DIFFUSIVITY,endpoint)),"pass":bool(passed)}

def prefit_parity(root,executable,output,observations,inventories,table):
    output.mkdir(parents=True,exist_ok=False)
    rows_out=[];cases=[];all_pass=True
    for item in table:
        q=item["flow_m3_s"];end=item["end_mass_kg"];selected=[r for r in observations if r.flow_m3_s==q];bounds=fraction_boundaries(selected,end);inv={s:item["inventory_mass_fraction"] for s in DIFFUSIVITY};params={s:(item["k_1_s"],item["csat_kg_m3"]) for s in DIFFUSIVITY}
        s=scenario(root,q,end,inv,params,cells=32,dt_s=.05);case,metrics,meta=execute(root,executable,output,item["case_id"],s);full=predictions(case,bounds,q)
        synthetic=[]
        for fraction,lo,hi in bounds:
            for name in DIFFUSIVITY:synthetic.append(type(observations[0])(0,fraction,name,q,lo,hi,1.0))
        reduced,diag=predict(synthetic,inv,"H1-SPECIES",[math.log(item["k_1_s"]),math.log(item["csat_kg_m3"])]*2,cells=32,dt_s=.05)
        metrics_case={}
        for name in DIFFUSIVITY:
            keys=[(f,name) for f,lo,hi in bounds];a=np.array([reduced[(0,f,name)] for f,_ in keys]);b=np.array([full[(f,name)] for f,_ in keys]);n=float(np.sqrt(np.mean((a-b)**2))/max(np.mean(b),1e-30));reduced_cup=sum(reduced[(0,f,name)]*(hi-lo) for f,lo,hi in bounds);full_cup=sum(full[(f,name)]*(hi-lo) for f,lo,hi in bounds);endpoint=rel(full_cup,reduced_cup);metrics_case[name]={"prediction_nrmse":n,"endpoint_relative_discrepancy":endpoint};all_pass &= n<=.01 and endpoint<=.005
            for fraction,lo,hi in bounds:rows_out.append({"case_id":item["case_id"],"fraction_id":fraction,"species_id":name,"lower_mass_kg":lo,"upper_mass_kg":hi,"reduced":reduced[(0,fraction,name)],"production":full[(fraction,name)]})
        water,_=traces(case);flow_error=rel(float(water[-1]["outlet_flow_m3_s"]),q);all_pass &= flow_error<=1e-8
        cases.append({**item,"metrics":metrics_case,"outlet_flow_relative_error":flow_error,"production":metrics,"executable":meta})
    return {"cases":cases,"predictions":rows_out,"thresholds":{"nrmse":.01,"endpoint":.005,"flow":1e-8},"pass":bool(all_pass)}

def postfit_parity(root,executable,output,observations,inventory,model,log_parameters):
    output.mkdir(parents=True,exist_ok=False)
    from .core import model_parameters
    params=model_parameters(model,log_parameters);rows_out=[];cases=[];passed=True
    for exp in sorted({r.experiment_id for r in observations}):
        rows=[r for r in observations if r.experiment_id==exp];q=rows[0].flow_m3_s;bounds=sorted({(r.fraction_id,r.lower_mass_kg,r.upper_mass_kg) for r in rows});end=max(x[2] for x in bounds)
        s=scenario(root,q,end,inventory,params,cells=32,dt_s=.05);case,metrics,meta=execute(root,executable,output,f"{model}_{exp:02d}",s);full=predictions(case,bounds,q);reduced,diag=predict(rows,inventory,model,log_parameters,cells=32,dt_s=.05)
        item={"experiment":exp,"species":{}}
        for name in DIFFUSIVITY:
            rr=np.array([reduced[(exp,f,name)] for f,lo,hi in bounds]);ff=np.array([full[(f,name)] for f,lo,hi in bounds]);n=float(np.sqrt(np.mean((rr-ff)**2))/max(np.mean(ff),1e-30));rc=sum(reduced[(exp,f,name)]*(hi-lo) for f,lo,hi in bounds);fc=sum(full[(f,name)]*(hi-lo) for f,lo,hi in bounds);e=rel(fc,rc);item["species"][name]={"nrmse":n,"endpoint":e};passed &= n<=.01 and e<=.005
            for f,lo,hi in bounds:rows_out.append({"model":model,"experiment":exp,"fraction":f,"species":name,"reduced":reduced[(exp,f,name)],"production":full[(f,name)]})
        cases.append(item)
    return {"model":model,"cases":cases,"predictions":rows_out,"pass":bool(passed)}
