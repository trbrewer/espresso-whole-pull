"""Prescribed-flow-equivalent conditional-Darcy production adapter."""
from __future__ import annotations
import copy,csv,json,math
from pathlib import Path
from tools.sci_md_004_stage_c.runner import Matrix,explicit,indexed
from .core import DIFFUSIVITY,DOSE_KG

PRESSURE_PA=900000.0
ALTERNATE_PRESSURE_PA=450000.0
VISCOSITY_PA_S=0.000315
DENSITY_KG_M3=1000.0
LENGTH_M=.015
DIAMETER_M=.058
POROSITY=.17

def area_m2():return math.pi*(DIAMETER_M/2)**2
def permeability(flow_m3_s,pressure_pa=PRESSURE_PA):return VISCOSITY_PA_S*LENGTH_M*flow_m3_s/(area_m2()*pressure_pa)
def boundary_time(mass_kg,flow_m3_s):return mass_kg/(DENSITY_KG_M3*flow_m3_s)

def scenario(root:Path,flow_m3_s,end_mass_kg,inventories,parameters,pressure_pa=PRESSURE_PA,*,cells=32,dt_s=.05,zero_inventory=False):
    base=json.loads((root/"config/reference_R0.json").read_text());s=copy.deepcopy(base);radius=DIAMETER_M/2;volume=area_m2()*LENGTH_M
    inv={name:0.0 if zero_inventory else float(inventories[name]) for name in DIFFUSIVITY}
    species=[explicit(name,inv[name],rate=float(parameters[name][0]),saturation=float(parameters[name][1]),diffusivity=DIFFUSIVITY[name]) for name in DIFFUSIVITY]
    s=indexed(s,species);k=permeability(flow_m3_s,pressure_pa)
    s.update({"scenario_id":"sci_md_006_conditional_darcy","mode":"validation","pressureBoundaryModel":"prescribedPressure","flowResistanceModel":"darcy","bedMechanicsModel":"none"});s.pop("calibration",None);s.pop("effective_permeability_evolution",None)
    s["geometry"].update({"basket_diameter_m":DIAMETER_M,"basket_radius_m":radius,"axial_cells":cells,"radial_cells":4})
    s["coffee_bed"].update({"dry_dose_kg":DOSE_KG,"initial_porosity":POROSITY,"bed_depth_m":LENGTH_M,"particle_solid_density_kg_m3":DOSE_KG/((1-POROSITY)*volume),"initial_extractable_fraction_dry_basis":sum(inv.values())})
    s["liquid"].update({"density_kg_m3":DENSITY_KG_M3,"dynamic_viscosity_Pa_s":VISCOSITY_PA_S})
    s["hydraulics"].update({"target_inlet_pressure_gauge_Pa":pressure_pa,"outlet_pressure_gauge_Pa":0.0,"pressure_ramp_time_s":0.0,"front_pressure_gauge_Pa":0.0,"saturated_permeability_m2":k,"wetting_permeability_m2":k,"permeability_profile":{"type":"uniform","interface_position_m":LENGTH_M/2,"upstream_permeability_m2":k,"downstream_permeability_m2":k,"interface_radius_m":radius/2,"inner_permeability_m2":k,"outer_permeability_m2":k}})
    s["wetting"].update({"initial_saturation":1.0,"initial_wet_front_m":LENGTH_M})
    end=boundary_time(end_mass_kg,flow_m3_s);s["time"].update({"start_s":0.0,"end_s":end,"delta_t_s":dt_s,"field_write_interval_s":end,"target_beverage_mass_kg":end_mass_kg})
    s["parallel"].update({"default_subdomains":1});s["output"].update({"write_format":"ascii","write_compression":False,"write_precision_digits":15,"live_stage_logging":False})
    s["governance"]={"task":"SCI-MD-006","application":"NONPORTABLE_PRESCRIBED_FLOW_EQUIVALENT_DARCY_NUISANCE_INPUT"}
    return s

def read_rows(path):
    with path.open(newline="") as h:return list(csv.DictReader(h))
def interpolate(rows,time_s,column):
    if time_s<=float(rows[0]["time_s"]):return float(rows[0][column])
    for a,b in zip(rows,rows[1:]):
        ta,tb=float(a["time_s"]),float(b["time_s"])
        if ta<=time_s<=tb:
            q=(time_s-ta)/(tb-ta);return float(a[column])+q*(float(b[column])-float(a[column]))
    return float(rows[-1][column])
def traces(case):
    water=read_rows(case/"postProcessing/wholePull/0/traces.csv");species=read_rows(case/"postProcessing/wholePullSpecies/0/species_traces.csv")
    return water,species
def predictions(case,boundaries,flow_m3_s):
    _,rows=traces(case);out={}
    for name in DIFFUSIVITY:
        selected=[r for r in rows if r["species_id"]==name]
        for fraction,lo,hi in boundaries:
            a=interpolate(selected,boundary_time(lo,flow_m3_s),"cup_solute_mass_kg");b=interpolate(selected,boundary_time(hi,flow_m3_s),"cup_solute_mass_kg")
            out[(fraction,name)]=(b-a)/(hi-lo)
    return out
def execute(root,executable,output,name,scenario_value):
    matrix=Matrix(executable,output);case=matrix.run(name,scenario_value);return case,matrix.application_metrics(case),matrix.run_metadata[name]
