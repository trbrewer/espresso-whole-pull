from __future__ import annotations
import copy,math
def scenario(base,case_id,phi=None,k=None,closure="BASELINE",pressure=None):
 c=copy.deepcopy(base); oldL=c["coffee_bed"]["bed_depth_m"]
 if phi is not None:
  if not math.isfinite(phi) or not 0.0<phi<1.0:raise ValueError("EWP_POROSITY_PERMEABILITY_PRIOR_001_INVALID_POROSITY")
  c["coffee_bed"]["initial_porosity"]=phi
 if k is not None and (not math.isfinite(k) or k<=0):raise ValueError("EWP_POROSITY_PERMEABILITY_PRIOR_001_INVALID_PERMEABILITY")
 if k is not None:
  c["hydraulics"]["saturated_permeability_m2"]=k
  if c["hydraulics"]["permeability_profile"]["type"]=="uniform":
   c["hydraulics"]["permeability_profile"]["upstream_permeability_m2"]=k;c["hydraulics"]["permeability_profile"]["downstream_permeability_m2"]=k
 if pressure is not None:c["hydraulics"]["target_inlet_pressure_gauge_Pa"]=pressure
 if closure=="FIXED_DOSE_MASS_CONSERVING_PRIMARY":
  A=math.pi*c["geometry"]["basket_radius_m"]**2; L=c["coffee_bed"]["dry_dose_kg"]/(c["coffee_bed"]["particle_solid_density_kg_m3"]*A*(1-c["coffee_bed"]["initial_porosity"])); scale=L/oldL;c["coffee_bed"]["bed_depth_m"]=L
  c["hydraulics"]["permeability_profile"]["interface_position_m"]*=scale
  for p in c["verification"]["pressure_probes"]:p["position_m"]*=scale;p["half_width_m"]*=scale
 A=math.pi*c["geometry"]["basket_radius_m"]**2; implied=c["coffee_bed"]["particle_solid_density_kg_m3"]*A*c["coffee_bed"]["bed_depth_m"]*(1-c["coffee_bed"]["initial_porosity"])
 return case_id,c,{"closure":closure,"implied_dry_mass_kg":implied,"mass_inconsistency_kg":implied-c["coffee_bed"]["dry_dose_kg"]}
