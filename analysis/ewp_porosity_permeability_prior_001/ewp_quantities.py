from __future__ import annotations
import hashlib,json
from pathlib import Path
def load(root:Path): return json.loads((root/"config/reference_R0.json").read_text())
def file_hashes(root:Path):
 return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ["config/reference_R0.json","solver/espressoWholePullFoam/espressoWholePullFoam.C","scripts/prepare_case.py","dependencies/puckworks.lock.json"]}
def ledger(c):
 vals={"coffee_bed.initial_porosity":c["coffee_bed"]["initial_porosity"],"hydraulics.saturated_permeability_m2":c["hydraulics"]["saturated_permeability_m2"],"hydraulics.wetting_permeability_m2":c["hydraulics"]["wetting_permeability_m2"],"coffee_bed.bed_depth_m":c["coffee_bed"]["bed_depth_m"],"coffee_bed.dry_dose_kg":c["coffee_bed"]["dry_dose_kg"],"coffee_bed.particle_solid_density_kg_m3":c["coffee_bed"]["particle_solid_density_kg_m3"],"geometry.basket_radius_m":c["geometry"]["basket_radius_m"],"liquid.density_kg_m3":c["liquid"]["density_kg_m3"],"liquid.dynamic_viscosity_Pa_s":c["liquid"]["dynamic_viscosity_Pa_s"]}
 out=[]
 for k,v in vals.items(): out.append({"path":k,"symbol":{"porosity":"phi","permeability":"K","viscosity":"mu","density":"rho","depth":"L","dose":"m_dry","radius":"r"}.get(next((x for x in ["porosity","permeability","viscosity","density","depth","dose","radius"] if x in k),""),""),"unit":"1" if "porosity" in k else ("m^2" if "permeability" in k else "SI_AS_PATH"),"default_value":v,"state":"INITIAL_DRY" if "porosity" in k else "STATIC","runtime_role":"wetting" if "wetting" in k else ("saturated_flow" if "saturated" in k else "geometry_or_property"),"validation_status":"CALIBRATED_EFFECTIVE_NOT_INDEPENDENTLY_VALIDATED" if "saturated" in k else "NOT_PHYSICALLY_VALIDATED","compatibility_limit":"source-native dry/connected/intrinsic definitions require explicit operator"})
 return out
