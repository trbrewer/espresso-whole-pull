"""Terminal XSV-FRAC-001 discrete-observer qualification runner."""
from __future__ import annotations
import argparse, copy, hashlib, json, math, subprocess
from pathlib import Path
from .fraction_collector import FractionCollector, Species
from .observer import compare, rows
from .build_receipt import sha, validate_receipt

ROOT=Path(__file__).resolve().parents[2]
BEHAVIORS=("PURE_EXACT_BOUNDARY","PURE_MULTI_BOUNDARY_SINGLE_STEP","PURE_ZERO_MASS_STEP","PURE_TERMINAL_PARTIAL_ENABLED","PURE_TERMINAL_PARTIAL_DISABLED","PURE_IRREGULAR_BOUNDARIES","PROD_LEGACY_EFFECTIVE_SOLUTE","PROD_ONE_INDEXED_LEGACY_EQUIVALENCE","PROD_IDENTICAL_SPECIES_SPLIT","PROD_DISTINCT_TWO_SPECIES","PROD_THREE_SPECIES_STRUCTURAL_BALANCE","PROD_ZERO_EXTRACTION_RATE","PROD_ZERO_DIFFUSIVITY","PROD_POSITIVE_DIFFUSIVITY","PROD_TIMESTEP_REFINEMENT","PROD_AXIAL_MESH_REFINEMENT","PROD_DETERMINISTIC_REPLAY","PROD_SERIAL_TWO_RANK_EQUIVALENCE","PROD_WETTING_REFERENCE_SMOKE","PROD_INCOMPLETE_FINAL_BOUNDARY")

def canonical(value): return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)
def record(behavior,cases,status,metric,evidence): return {"behavior_id":behavior,"case_ids":cases,"status":status,"principal_metric":metric,"evidence":evidence}
def git_identity():
    return {
      "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
      "tree":subprocess.check_output(["git","rev-parse","HEAD^{tree}"],cwd=ROOT,text=True).strip(),
    }

def pure_matrix():
    specs=[Species("water_soluble","explicitInventory",2),Species("slow_soluble","structuralBalance",2)]
    definitions={
      "PURE_EXACT_BOUNDARY":([1],[(0,1,.6,[.3,.1])],False,[{"status":"complete","water":.6,"species": [.3,.1],"end":1.0}]),
      "PURE_MULTI_BOUNDARY_SINGLE_STEP":([.25,.75],[(0,2,.6,[.3,.1])],True,[{"status":"complete","water":.15,"species":[.075,.025],"end":.5},{"status":"complete","water":.3,"species":[.15,.05],"end":1.5}]),
      "PURE_ZERO_MASS_STEP":([1],[(0,1,0,[0,0]),(1,1,.6,[.3,.1])],False,[{"status":"complete","water":.6,"species":[.3,.1],"end":2.0}]),
      "PURE_TERMINAL_PARTIAL_ENABLED":([2],[(0,1,.6,[.3,.1])],True,[{"status":"partial","water":.6,"species":[.3,.1],"end":1.0}]),
      "PURE_TERMINAL_PARTIAL_DISABLED":([2],[(0,1,.6,[.3,.1])],False,[]),
      "PURE_IRREGULAR_BOUNDARIES":([.17,.431,.9],[(0,1,.6,[.3,.1])],True,None),
    }
    output=[]
    for behavior,(bounds,steps,terminal,wants) in definitions.items():
        collector=FractionCollector(bounds,specs,terminal)
        for step in steps: collector.add_step(*step)
        got=collector.finish(); ok=True; maximum=0.0
        if wants is not None:
            ok=len(got)==len(wants)
            for row,want in zip(got,wants):
                ok &= row["status"]==want["status"]
                values=[(row["water_mass_kg"],want["water"]),(row["end_time_s"],want["end"])]
                values += list(zip(row["species_masses_kg"],want["species"]))
                maximum=max(maximum,*(abs(a-b) for a,b in values)); ok &= all(abs(a-b)<=1e-12 for a,b in values)
        else:
            ok=len(got)==3 and [r["status"] for r in got]==["complete","complete","complete"] and collector.uncompleted_boundaries==[]
        output.append(record(behavior,[behavior.lower()],"PASS" if ok else "FAIL",{"maximum_hand_error":maximum,"row_count":len(got)},["independent_hand_calculation"]))
    return output

def fraction_config(boundaries=(.0003,.0007,.0011),partial=True): return {"enabled":True,"boundaryBasis":"cumulativeBeverageMass","cumulativeBoundariesKg":list(boundaries),"emitTerminalPartial":partial}

def run_matrix(work,solver,ranks,production_source_sha256):
    from tools.sci_md_004_stage_c.runner import Matrix,indexed,explicit,residual
    work.mkdir(parents=True,exist_ok=False); m=Matrix(solver,work); cases={}; scenarios={}; metrics={}
    def base(end=5,dt=.01,axial=64,wet=False,bounds=(.0003,.0007,.0011),partial=True):
        s=m.compact(end=end,dt=dt,axial=axial,radial=1)
        if not wet: s["wetting"]["initial_wet_front_m"]=s["coffee_bed"]["bed_depth_m"]
        s["fractionCollection"]=fraction_config(bounds,partial); return s
    definitions=[]
    definitions.append(("legacy",base(),1))
    definitions.append(("legacy_intra_step",base(end=1,bounds=(.00001,.0000101,.1),partial=True),1))
    definitions.append(("indexed_one",indexed(base(),[explicit("legacy_equivalent",.28,.15,180,1e-9)]),1))
    definitions.append(("identical_split",indexed(base(),[explicit("species_a",.14,.15,180,1e-9),explicit("species_b",.14,.15,180,1e-9)]),1))
    definitions.append(("distinct_two",indexed(base(),[explicit("fast",.10,.20,120,0),explicit("slow",.18,.08,240,2e-9)]),1))
    definitions.append(("three_structural",indexed(base(),[explicit("a",.08,.1,100,0),explicit("b",.10,.2,220,1e-9),residual()]),1))
    definitions.append(("zero_rate",indexed(base(),[explicit("zero",.10,0,180,0),residual()]),1))
    definitions.append(("zero_diff",indexed(base(),[explicit("zero_diff",.28,.15,180,0)]),1))
    definitions.append(("positive_diff",indexed(base(),[explicit("positive_diff",.28,.15,180,2e-9)]),1))
    for dt in (.02,.01,.005): definitions.append((f"time_{dt:g}",indexed(base(dt=dt),[explicit("refine",.28,.15,180,1e-9)]),1))
    for axial in (32,64,128): definitions.append((f"mesh_{axial}",indexed(base(axial=axial),[explicit("refine",.28,.15,180,1e-9)]),1))
    replay=indexed(base(),[explicit("replay",.28,.15,180,1e-9)])
    definitions += [("replay_a",replay,1),("replay_b",copy.deepcopy(replay),1)]
    mpi=indexed(base(),[explicit("mpi_species",.28,.15,180,1e-9)])
    definitions += [("mpi_serial",mpi,1)]
    if 2 in ranks: definitions += [("mpi_two",copy.deepcopy(mpi),2)]
    definitions += [("wetting_smoke",base(end=6,wet=True,bounds=(.0001,.0002),partial=True),1),
                    ("incomplete",indexed(base(end=1,bounds=(.1,),partial=False),[explicit("incomplete_species",.28,.15,180,1e-9)]),1)]
    for name,scenario,rank in definitions:
        case=m.run(name,scenario,rank); cases[name]=case; scenarios[name]=scenario
        metrics[name]=compare(case,scenario,production_source_sha256)
    exe=sha(solver); result=[]
    mapping={"PROD_LEGACY_EFFECTIVE_SOLUTE":["legacy","legacy_intra_step"],"PROD_ONE_INDEXED_LEGACY_EQUIVALENCE":["legacy","indexed_one"],"PROD_IDENTICAL_SPECIES_SPLIT":["identical_split"],"PROD_DISTINCT_TWO_SPECIES":["distinct_two"],"PROD_THREE_SPECIES_STRUCTURAL_BALANCE":["three_structural"],"PROD_ZERO_EXTRACTION_RATE":["zero_rate"],"PROD_ZERO_DIFFUSIVITY":["zero_diff"],"PROD_POSITIVE_DIFFUSIVITY":["positive_diff"],"PROD_TIMESTEP_REFINEMENT":["time_0.02","time_0.01","time_0.005"],"PROD_AXIAL_MESH_REFINEMENT":["mesh_32","mesh_64","mesh_128"],"PROD_DETERMINISTIC_REPLAY":["replay_a","replay_b"],"PROD_SERIAL_TWO_RANK_EQUIVALENCE":["mpi_serial","mpi_two"],"PROD_WETTING_REFERENCE_SMOKE":["wetting_smoke"],"PROD_INCOMPLETE_FINAL_BOUNDARY":["incomplete"]}
    def output_hashes(name):
        rel=("postProcessing/wholePullFractions/0/fractions.csv","postProcessing/wholePullFractions/0/fraction_species.csv")
        manifest=json.loads((Path(cases[name])/"postProcessing/wholePullFractions/0/manifest.json").read_text())
        semantic={key:manifest[key] for key in ("boundary_basis","requested_boundaries_kg","emit_terminal_partial","completed_fraction_count","uncompleted_requested_boundaries_kg","mass_partition_convention","time_location_convention","final_emitted_cumulative_component_totals")}
        return {"fractions_csv":sha(Path(cases[name])/rel[0]),"fraction_species_csv":sha(Path(cases[name])/rel[1]),"semantic_manifest":hashlib.sha256(canonical(semantic).encode()).hexdigest(),"oracle":hashlib.sha256(canonical(metrics[name]).encode()).hexdigest()}
    replay_hashes={name:output_hashes(name) for name in ("replay_a","replay_b")}
    mpi_comparison=equivalent_cases(cases["mpi_serial"],cases["mpi_two"],True) if "mpi_two" in cases else {"status":"FAIL","reason":"two-rank case unavailable"}
    resolution={"PROD_TIMESTEP_REFINEMENT":resolution_diagnostic(cases,["time_0.02","time_0.01","time_0.005"]),"PROD_AXIAL_MESH_REFINEMENT":resolution_diagnostic(cases,["mesh_32","mesh_64","mesh_128"])}
    extra={"PROD_ONE_INDEXED_LEGACY_EQUIVALENCE":same_numeric(rows(cases["legacy"]/"postProcessing/wholePullFractions/0/fractions.csv"),rows(cases["indexed_one"]/"postProcessing/wholePullFractions/0/fractions.csv")),
      "PROD_IDENTICAL_SPECIES_SPLIT":identical_species(cases["identical_split"]),
      "PROD_ZERO_EXTRACTION_RATE":zero_species(cases["zero_rate"],"zero"),
      "PROD_DETERMINISTIC_REPLAY":replay_hashes["replay_a"]==replay_hashes["replay_b"],
      "PROD_SERIAL_TWO_RANK_EQUIVALENCE":mpi_comparison["status"]=="PASS"}
    for behavior,names in mapping.items():
        ok=all(metrics[n]["status"]=="PASS" for n in names if n in metrics) and len(names)==sum(n in metrics for n in names) and extra.get(behavior,True)
        metric={"maximum_oracle_mass_error_kg":max((metrics[n]["maximum_mass_error_kg"] for n in names if n in metrics),default=0),"maximum_oracle_time_error_s":max((metrics[n]["maximum_time_error_s"] for n in names if n in metrics),default=0),"scenario_sha256":[sha(work/f"{n}.json") for n in names if n in cases],"executable_sha256":exe}
        if behavior in resolution:
            metric["resolution_coverage_semantics"]="RESOLUTION_COVERAGE_OBSERVER_ORACLE_PASS_AT_EVERY_LEVEL"
            metric["cross_level_diagnostic"]=resolution[behavior]
            ok &= resolution[behavior]["status"]=="PASS"
        if behavior=="PROD_DETERMINISTIC_REPLAY": metric["canonical_output_sha256"]=replay_hashes
        if behavior=="PROD_SERIAL_TWO_RANK_EQUIVALENCE": metric["serial_two_rank_comparison"]=mpi_comparison
        result.append(record(behavior,names,"PASS" if ok else "FAIL",metric,[str(cases[n].relative_to(work)) for n in names if n in cases]))
    metadata={n:{"scenario_sha256":sha(work/f"{n}.json"),"executable_sha256":exe,"oracle":metrics[n],"underlying_fraction_masses_kg":[float(r["beverage_mass_kg"]) for r in rows(cases[n]/"postProcessing/wholePullFractions/0/fractions.csv")]} for n in cases}
    return result,cases,scenarios,metadata

def resolution_diagnostic(cases,names):
    aggregate={name:rows(Path(cases[name])/"postProcessing/wholePullFractions/0/fractions.csv") for name in names}
    species={name:rows(Path(cases[name])/"postProcessing/wholePullFractions/0/fraction_species.csv") for name in names}
    structure=True
    for left,right in zip(names,names[1:]):
        a,b=aggregate[left],aggregate[right]; sa,sb=species[left],species[right]
        structure &= len(a)==len(b) and len(sa)==len(sb)
        structure &= [(r["fraction_index"],r["status"],r["requested_lower_cumulative_beverage_mass_kg"],r["requested_upper_cumulative_beverage_mass_kg"]) for r in a]==[(r["fraction_index"],r["status"],r["requested_lower_cumulative_beverage_mass_kg"],r["requested_upper_cumulative_beverage_mass_kg"]) for r in b]
        structure &= [(r["fraction_index"],r["species_index"],r["species_id"],r["species_role"]) for r in sa]==[(r["fraction_index"],r["species_index"],r["species_id"],r["species_role"]) for r in sb]
    if not structure: return {"status":"FAIL","reason":"cross-level structure mismatch"}
    def rel(delta,a,b): return delta/max(abs(a),abs(b),1e-12)
    comparisons=[]; sensitive=False
    for left,right in ((names[0],names[1]),(names[1],names[2]),(names[0],names[2])):
        a,b=aggregate[left],aggregate[right]; sa,sb=species[left],species[right]
        water=max(abs(float(x["water_mass_kg"])-float(y["water_mass_kg"])) for x,y in zip(a,b))
        solute=[(abs(float(x["total_solute_mass_kg"])-float(y["total_solute_mass_kg"])),float(x["total_solute_mass_kg"]),float(y["total_solute_mass_kg"])) for x,y in zip(a,b)]
        species_mass={}; cumulative={}
        for x,y in zip(sa,sb):
            sid=x["species_id"]; d=abs(float(x["species_mass_kg"])-float(y["species_mass_kg"])); c=abs(float(x["cumulative_species_mass_kg"])-float(y["cumulative_species_mass_kg"])); species_mass[sid]=max(species_mass.get(sid,(0,0)),(d,rel(d,float(x["species_mass_kg"]),float(y["species_mass_kg"])))); cumulative[sid]=max(cumulative.get(sid,(0,0)),(c,rel(c,float(x["cumulative_species_mass_kg"]),float(y["cumulative_species_mass_kg"]))))
        time=max(abs(float(x["end_time_s"])-float(y["end_time_s"])) for x,y in zip(a,b))
        fw=abs(sum(float(x["water_mass_kg"]) for x in a)-sum(float(x["water_mass_kg"]) for x in b)); fs=abs(sum(float(x["total_solute_mass_kg"]) for x in a)-sum(float(x["total_solute_mass_kg"]) for x in b))
        entry={"levels":[left,right],"maximum_water_mass_difference_kg":water,"maximum_total_solute_mass_difference_kg":max(x[0] for x in solute),"maximum_total_solute_relative_difference":max(rel(*x) for x in solute),"species_fraction_mass_difference":{k:{"absolute_kg":v[0],"relative":v[1]} for k,v in species_mass.items()},"cumulative_species_mass_difference":{k:{"absolute_kg":v[0],"relative":v[1]} for k,v in cumulative.items()},"maximum_boundary_time_difference_s":time,"final_cumulative_water_difference_kg":fw,"final_cumulative_solute_difference_kg":fs}
        sensitive |= max(water,max(x[0] for x in solute),fw,fs)>1e-12 or time>1e-12
        comparisons.append(entry)
    actual={name:{"aggregate":[{k:r[k] for k in ("fraction_index","status","water_mass_kg","total_solute_mass_kg","beverage_mass_kg","end_time_s")} for r in aggregate[name]],"species":[{k:r[k] for k in ("fraction_index","species_index","species_id","species_role","species_mass_kg","cumulative_species_mass_kg")} for r in species[name]]} for name in names}
    return {"status":"PASS","structure_compatible":True,"classification":"UNDERLYING_PDE_RESOLUTION_DIAGNOSTIC_SENSITIVE" if sensitive else "UNDERLYING_PDE_RESOLUTION_DIAGNOSTIC_STABLE","acceptance_semantics":"observer/oracle PASS at every level; magnitudes are diagnostic only","levels":actual,"comparisons":comparisons,"physical_convergence_claim":False}

def same_numeric(a,b,tol=1e-10,ignore=()):
    if len(a)!=len(b) or (a and a[0].keys()!=b[0].keys()): return False
    for x,y in zip(a,b):
        for key in x:
            if key in ignore: continue
            try:
                av=float(x[key]); bv=float(y[key])
                if abs(av-bv)>max(1e-12,tol*max(abs(av),abs(bv))): return False
            except ValueError:
                if x[key]!=y[key]: return False
    return True
def identical_species(case):
    data=rows(Path(case)/"postProcessing/wholePullFractions/0/fraction_species.csv"); a=[float(r["cumulative_extracted_fraction_of_initial_inventory"]) for r in data if r["species_id"]=="species_a"]; b=[float(r["cumulative_extracted_fraction_of_initial_inventory"]) for r in data if r["species_id"]=="species_b"]
    return len(a)==len(b) and all(abs(x-y)<=1e-10 for x,y in zip(a,b))
def zero_species(case,sid): return all(abs(float(r["species_mass_kg"]))<=1e-12 for r in rows(Path(case)/"postProcessing/wholePullFractions/0/fraction_species.csv") if r["species_id"]==sid)

def equivalent_cases(a,b,indexed):
    from tools.sci_md_004_stage_c.compare import scalar_internal_values
    paths=["postProcessing/wholePull/0/traces.csv","postProcessing/wholePullFractions/0/fractions.csv","postProcessing/wholePullFractions/0/fraction_species.csv"]
    if indexed: paths.append("postProcessing/wholePullSpecies/0/species_traces.csv")
    iteration_diagnostics={"pressure_iterations","concentration_iterations","couplingIterations","nonlinearIterations","basketOperatingPointIterations","poroelasticNonlinearIterations","pressure_initial_residual","pressure_final_residual","concentration_initial_residual","concentration_final_residual"}
    compared={p:same_numeric(rows(Path(a)/p),rows(Path(b)/p),1e-6,iteration_diagnostics) for p in paths}
    latest=lambda case:max((p for p in Path(case).iterdir() if p.is_dir() and p.name.replace('.','',1).isdigit()),key=lambda p:float(p.name))
    fields=["p","dissolvedConcentration","remainingExtractable"]
    if indexed: fields += ["dissolvedConcentration_mpi_species","remainingExtractable_mpi_species"]
    field_differences={}
    for field in fields:
        av=scalar_internal_values(latest(a)/field); bv=scalar_internal_values(latest(b)/field)
        field_differences[field]=math.inf if len(av)!=len(bv) else max((abs(x-y) for x,y in zip(av,bv)),default=0.0)
    field_equal={field:value<=1e-6 for field,value in field_differences.items()}
    if not all(compared.values()) or not all(field_equal.values()): return {"status":"FAIL","tables":compared,"final_fields":field_equal}
    ma=json.loads((Path(a)/"postProcessing/wholePullFractions/0/manifest.json").read_text()); mb=json.loads((Path(b)/"postProcessing/wholePullFractions/0/manifest.json").read_text())
    semantic=("boundary_basis","requested_boundaries_kg","emit_terminal_partial","completed_fraction_count","uncompleted_requested_boundaries_kg","mass_partition_convention","time_location_convention")
    if not all(ma[key]==mb[key] for key in semantic): return {"status":"FAIL","reason":"manifest semantic mismatch","tables":compared,"final_fields":field_equal}
    totals={key:abs(float(ma["final_emitted_cumulative_component_totals"][key])-float(mb["final_emitted_cumulative_component_totals"][key])) for key in ("water_mass_kg","solute_mass_kg","beverage_mass_kg")}
    return {"status":"PASS" if max(totals.values())<=1e-12 else "FAIL","tables":compared,"final_fields":field_equal,"maximum_final_field_absolute_difference":max(field_differences.values()),"maximum_manifest_total_difference":max(totals.values())}

def regressions(work,baseline,candidate):
    from tools.sci_md_004_stage_c.runner import Matrix,indexed,explicit
    outcomes={}
    for route in ("legacy","indexed"):
      for mode in ("absent","disabled"):
        scenario=Matrix(candidate,work/"seed").compact(end=1,dt=.02,axial=32,radial=1)
        if route=="indexed": scenario=indexed(scenario,[explicit("regression_species",.28,.15,180,1e-9)])
        if mode=="disabled": scenario["fractionCollection"]={"enabled":False}
        pair=[]
        for label,exe in (("baseline",baseline),("candidate",candidate)):
            root=work/f"{route}_{mode}_{label}"; matrix=Matrix(exe,root); root.mkdir(parents=True,exist_ok=False); pair.append(matrix.run("case",scenario,1))
        rel=["postProcessing/wholePull/0/traces.csv"]+(["postProcessing/wholePullSpecies/0/species_traces.csv"] if route=="indexed" else [])
        latest=lambda case:max((p for p in case.iterdir() if p.is_dir() and p.name.replace('.','',1).isdigit()),key=lambda p:float(p.name))
        fields=["p","U","dissolvedConcentration","remainingExtractable"]
        if route=="indexed": fields += ["dissolvedConcentration_regression_species","remainingExtractable_regression_species"]
        ok=all(Path(pair[0],p).read_bytes()==Path(pair[1],p).read_bytes() for p in rel) and all((latest(pair[0])/f).read_bytes()==(latest(pair[1])/f).read_bytes() for f in fields) and all(not (p/"postProcessing/wholePullFractions").exists() for p in pair)
        outcomes[f"{route}_{mode}"]={"status":"PASS" if ok else "FAIL","comparison":"byte-identical CSV/final fields and fraction-directory absence"}
    return outcomes

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--work-root",required=True,type=Path); p.add_argument("--openfoam-ranks",nargs="+",type=int,default=[1,2]); p.add_argument("--candidate-build-receipt",required=True,type=Path); p.add_argument("--baseline-build-receipt",required=True,type=Path); args=p.parse_args(argv)
    if args.work_root.exists() and any(args.work_root.iterdir()): raise SystemExit("work root must be absent or empty")
    identity=git_identity(); candidate_receipt,candidate_public=validate_receipt(args.candidate_build_receipt,"candidate",identity["commit"],identity["tree"]); baseline_receipt,baseline_public=validate_receipt(args.baseline_build_receipt,"baseline","fc668afbeb7782d3d342b8ba403fb6c1dee396d4","d04f7c7c61eeae057ae55dde878ec4d7cb936815")
    candidate=Path(candidate_receipt["executable_path"]); baseline=Path(baseline_receipt["executable_path"])
    if candidate.resolve()==baseline.resolve(): raise SystemExit("candidate and baseline executable evidence paths must differ")
    before={"candidate":sha(candidate),"baseline":sha(baseline)}
    args.work_root.mkdir(parents=True,exist_ok=True)
    pure=pure_matrix(); production,cases,scenarios,metadata=run_matrix(args.work_root/"production",candidate,args.openfoam_ranks,candidate_receipt["production_solver_source_sha256"])
    behaviors=pure+production; ids=[r["behavior_id"] for r in behaviors]
    complete=(len(ids)==20 and set(ids)==set(BEHAVIORS) and all(r["status"] in {"PASS","FAIL"} and r["evidence"] for r in behaviors))
    after_matrix={"candidate":sha(candidate),"baseline":sha(baseline)}
    regression=regressions(args.work_root/"regression",baseline,candidate)
    after_regression={"candidate":sha(candidate),"baseline":sha(baseline)}
    hashes_stable=before==after_matrix==after_regression=={"candidate":candidate_receipt["executable_sha256"],"baseline":baseline_receipt["executable_sha256"]}
    passed=complete and hashes_stable and all(r["status"]=="PASS" for r in behaviors) and all(x.get("status")=="PASS" for x in regression.values())
    result={"schema":"espresso.xsv_frac_001.r2a.result.v1","status":"PASS" if passed else "OBSERVER_QUALIFICATION_FAIL","behavior_count":len(behaviors),"behavior_ids_complete":complete,"behaviors":behaviors,"case_metadata":metadata,"default_regression":regression,"build_receipts":{"candidate":candidate_public,"baseline":baseline_public,"hashes_before":before,"hashes_after_matrix":after_matrix,"hashes_after_regression":after_regression,"hashes_stable":hashes_stable},"execution_source_identity":identity,"claim_ceiling":"Discrete fraction-observer qualification only; no physical convergence claim; physical validation NOT_ESTABLISHED."}
    (args.work_root/"R2A_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps({k:v for k,v in result.items() if k not in {"behaviors","case_metadata"}},indent=2,sort_keys=True)); return 0 if passed else 2
if __name__=="__main__": raise SystemExit(main())
