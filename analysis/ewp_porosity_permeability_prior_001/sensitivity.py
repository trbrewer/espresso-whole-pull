from __future__ import annotations
import math,sys
from pathlib import Path
def add_scripts(root):
 p=str(root/"scripts");
 if p not in sys.path:sys.path.insert(0,p)
def metrics(root,c):
 add_scripts(root);from espresso_reference_math import analytical_preview,continuum_hydraulic_resistance_m_inv,full_cross_section_area_m2
 a=analytical_preview(c); L=c["coffee_bed"]["bed_depth_m"];K=c["hydraulics"]["saturated_permeability_m2"];mu=c["liquid"]["dynamic_viscosity_Pa_s"];rho=c["liquid"]["density_kg_m3"];A=full_cross_section_area_m2(c);Rm=mu*L/(rho*A*K); end=c["time"]["end_s"]
 return {**a,"L_over_K_m_inv":L/K,"R_Q_pa_s_m3":mu*L/(A*K),"R_m_pa_s_kg":Rm,"R_bar_per_g_per_s":Rm/1e8,"mass_at_final_time_kg":a["water_mass_at_end_kg_excluding_solute"],"time_to_target_yield_s": (a["first_drip_s"]+c["time"]["target_beverage_mass_kg"]/(rho*a["steady_outlet_volume_flow_m3_s"])) if a["steady_outlet_volume_flow_m3_s"]>0 else None}
def reduced(root,c):
 add_scripts(root);from espresso_reference_math import b0_reduced_simulation
 return b0_reduced_simulation(c)
def identifiability(root,base):
 import copy
 x=[]
 for param,step in [("phi",.01),("log10_k",.02)]:
  lo=copy.deepcopy(base);hi=copy.deepcopy(base)
  if param=="phi":lo["coffee_bed"]["initial_porosity"]-=step;hi["coffee_bed"]["initial_porosity"]+=step;den=2*step
  else:
   for c,s in [(lo,-step),(hi,step)]:
    k=c["hydraulics"]["saturated_permeability_m2"]*10**s;c["hydraulics"]["saturated_permeability_m2"]=k;c["hydraulics"]["permeability_profile"]["upstream_permeability_m2"]=k;c["hydraulics"]["permeability_profile"]["downstream_permeability_m2"]=k
   den=2*step
  ml,mh=metrics(root,lo),metrics(root,hi);x.append([(mh[k]-ml[k])/den for k in ["first_drip_s","steady_outlet_volume_flow_m3_s","saturated_pore_water_mass_kg"]])
 # singular values of 2-column scaled Jacobian via J'J
 cols=list(zip(*x)); scales=[max(abs(v) for v in col) or 1 for col in cols]; J=[[x[j][i]/scales[i] for j in range(2)] for i in range(3)];a=sum(r[0]**2 for r in J);b=sum(r[0]*r[1] for r in J);d=sum(r[1]**2 for r in J);disc=math.sqrt((a-d)**2+4*b*b);sv=[math.sqrt(max(0,(a+d+disc)/2)),math.sqrt(max(0,(a+d-disc)/2))]
 return {"parameters":["phi","log10_saturated_k"],"steps":{"phi":.01,"log10_saturated_k":.02},"observables":["first_drip_s","steady_outlet_volume_flow_m3_s","saturated_pore_water_mass_kg"],"derivatives":{"phi":x[0],"log10_saturated_k":x[1]},"scaled_singular_values":sv,"rank":sum(v>1e-10 for v in sv),"interpretation":"DISTINGUISHABLE_LOCAL_NUMERICAL_SIGNATURES; saturated-K derivative of first drip is zero because primary lane retains wetting K"}
