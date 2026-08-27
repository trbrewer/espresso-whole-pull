"""Public synthetic XSV-FRAC-001 qualification runner."""
from __future__ import annotations
import argparse, csv, json, math, os
from pathlib import Path
from .fraction_collector import FractionCollector, Species
from .reduced_solver import ReducedSpecies, simulate

ROOT = Path(__file__).resolve().parents[2]

def canonical(value): return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
def nrmse(actual, expected):
    scale=max(max(expected)-min(expected), max(map(abs,expected)), 1e-30)
    return math.sqrt(sum((a-e)**2 for a,e in zip(actual,expected))/len(actual))/scale
def read_rows(path):
    with path.open(newline="") as stream: return list(csv.DictReader(stream))

def pure_cases():
    specs=[Species("a","explicitInventory",1),Species("b","structuralBalance",1)]
    definitions=[
      ("pure_exact_boundaries",[1,2],[(0,1,.8,[.1,.1]),(1,1,.8,[.1,.1])],False),
      ("pure_multiple_boundaries",[.2,.4,.6],[(0,1,.3,[.2,.2])],False),
      ("pure_zero_mass_step",[1],[(0,1,0,[0,0]),(1,1,.8,[.1,.1])],False),
      ("terminal_partial_enabled",[2],[(0,1,.8,[.1,.1])],True),
      ("terminal_partial_disabled",[2],[(0,1,.8,[.1,.1])],False),
      ("irregular_boundaries",[.17,.431,.9],[(0,1,.8,[.1,.1])],True),
    ]
    results=[]
    for name,bounds,steps,terminal in definitions:
        c=FractionCollector(bounds,specs,terminal)
        for step in steps: c.add_step(*step)
        rows=c.finish()
        residual=max([abs(r["water_plus_solute_closure_residual_kg"]) for r in rows] or [0])
        species=max([abs(r["species_sum_closure_residual_kg"]) for r in rows] or [0])
        results.append({"case":name,"status":"PASS" if max(residual,species)<=1e-12 else "FAIL",
                        "rows":len(rows),"maximum_component_residual_kg":residual,
                        "maximum_species_residual_kg":species})
    return results

def production_matrix(work, solver, ranks):
    from tools.sci_md_004_stage_c.runner import Matrix, indexed, explicit, residual
    work.mkdir(parents=True, exist_ok=False)
    matrix=Matrix(solver,work); definitions=[]
    for axial in (32,64,128): definitions.append((f"mesh_{axial}",axial,.01,1))
    for dt in (.02,.01,.005): definitions.append((f"time_{dt:g}",64,dt,1))
    definitions.extend([("deterministic_a",64,.01,1),("deterministic_b",64,.01,1)])
    if 2 in ranks: definitions.append(("parallel_2",64,.01,2))
    cases=[]
    for name,axial,dt,rank in definitions:
        scenario=matrix.compact(end=5.0,dt=dt,axial=axial,radial=1)
        scenario["wetting"]["initial_wet_front_m"]=scenario["coffee_bed"]["bed_depth_m"]
        scenario["fractionCollection"]={"enabled":True,"boundaryBasis":"cumulativeBeverageMass",
            "cumulativeBoundariesKg":[.0003,.0007,.0011],"emitTerminalPartial":True}
        scenario=indexed(scenario,[explicit("species_a",.10),residual()])
        case=matrix.run(name,scenario,rank)
        cases.append({"name":name,"axial_cells":axial,"delta_t_s":dt,"ranks":rank,
            "fractions":read_rows(case/"postProcessing/wholePullFractions/0/fractions.csv"),
            "species":read_rows(case/"postProcessing/wholePullFractions/0/fraction_species.csv")})
    return cases

def reduced_parity(production):
    base=json.loads((ROOT/"config/reference_R0.json").read_text()); area=math.pi*base["geometry"]["basket_radius_m"]**2
    species=[ReducedSpecies("species_a",.002,.15,180,1e-9),
             ReducedSpecies("residual_extractables",.0036,.15,180,base["liquid"]["effective_solute_diffusivity_m2_s"])]
    reduced=simulate(length_m=base["coffee_bed"]["bed_depth_m"],area_m2=area,
      porosity=base["coffee_bed"]["initial_porosity"],permeability_m2=base["hydraulics"]["saturated_permeability_m2"],
      viscosity_pa_s=base["liquid"]["dynamic_viscosity_Pa_s"],density_kg_m3=base["liquid"]["density_kg_m3"],
      pressure_drop_pa=base["hydraulics"]["target_inlet_pressure_gauge_Pa"]-base["hydraulics"]["outlet_pressure_gauge_Pa"],
      cells=production["axial_cells"],delta_t_s=production["delta_t_s"],end_s=5.0,species=species)
    collector=FractionCollector([.0003,.0007,.0011],[Species(s.species_id,"synthetic",s.initial_mass_kg) for s in species],True)
    for step in reduced["steps"]: collector.add_step(step["start_time_s"],step["delta_t_s"],step["water_mass_kg"],step["species_mass_kg"])
    rr=collector.finish(); metrics={}
    for index,s in enumerate(species):
        actual=[float(r["species_mass_kg"]) for r in production["species"] if r["species_id"]==s.species_id]
        expected=[r["species_masses_kg"][index] for r in rr]; count=min(len(actual),len(expected)); actual=actual[:count]; expected=expected[:count]
        metrics[s.species_id]={"fraction_nrmse":nrmse(actual,expected) if count else 1e300,
          "endpoint_relative":abs(sum(actual)-sum(expected))/max(abs(sum(expected)),1e-30)}
    return metrics

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--work-root",required=True,type=Path)
    p.add_argument("--openfoam-ranks",nargs="+",type=int,default=[1,2]); args=p.parse_args(argv)
    if args.work_root.exists() and any(args.work_root.iterdir()): raise SystemExit("work root must be absent or empty")
    args.work_root.mkdir(parents=True,exist_ok=True); pure=pure_cases()
    solver=Path(os.environ.get("FOAM_USER_APPBIN",""))/"espressoWholePullFoam"
    if not solver.is_file():
        result={"schema":"espresso.xsv_frac_001.result.v1","status":"OPENFOAM_UNAVAILABLE","pure_cases":pure,
                "claim_ceiling":"NUMERICAL_QUALIFICATION_NOT_PHYSICAL_VALIDATION"}
    else:
        production=production_matrix(args.work_root/"production",solver,args.openfoam_ranks)
        parity=reduced_parity(next(c for c in production if c["name"]=="time_0.01"))
        complete=[r for c in production for r in c["fractions"] if r["status"]=="complete"]
        boundary=max(abs(float(r["realized_upper_cumulative_beverage_mass_kg"])-float(r["requested_upper_cumulative_beverage_mass_kg"])) for r in complete)
        component=max(abs(float(r["water_plus_solute_closure_residual_kg"])) for c in production for r in c["fractions"])
        species=max(abs(float(r["species_sum_closure_residual_kg"])) for c in production for r in c["fractions"])
        da=next(c for c in production if c["name"]=="deterministic_a"); db=next(c for c in production if c["name"]=="deterministic_b")
        deterministic=canonical(da["fractions"])==canonical(db["fractions"]) and canonical(da["species"])==canonical(db["species"])
        passed=all(x["status"]=="PASS" for x in pure) and boundary<=1e-12 and component<=1e-12 and species<=1e-12 and deterministic and all(v["fraction_nrmse"]<=.01 and v["endpoint_relative"]<=.005 for v in parity.values())
        result={"schema":"espresso.xsv_frac_001.result.v1","status":"PASS" if passed else "NUMERICAL_QUALIFICATION_FAIL",
          "case_count":len(pure)+len(production)+1,"pure_cases":pure,"production_case_count":len(production),
          "maximum_boundary_error_kg":boundary,"maximum_component_residual_kg":component,
          "maximum_species_residual_kg":species,"production_reduced_parity":parity,
          "deterministic_replay":deterministic,"serial_two_rank_executed":any(c["ranks"]==2 for c in production),
          "claim_ceiling":"Exact means conservative only with respect to discrete per-step cup-mass quadrature; physical validation NOT_ESTABLISHED."}
    (args.work_root/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="pure_cases"},indent=2,sort_keys=True))
    return 0 if result["status"]=="PASS" else (3 if result["status"]=="OPENFOAM_UNAVAILABLE" else 2)

if __name__=="__main__": raise SystemExit(main())
