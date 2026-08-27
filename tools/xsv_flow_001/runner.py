"""Bounded external qualification runner for XSV-FLOW-001."""
from __future__ import annotations
import argparse, copy, csv, hashlib, json, math, shutil, subprocess, sys
from pathlib import Path
from .reference import (discrete_volume, layered_pressure_drop, schedule_value,
                        uniform_pressure_drop)

ROOT=Path(__file__).resolve().parents[2]
CASE_IDS=("FLOW_UC_M32","FLOW_UC_M64","FLOW_UC_M128","FLOW_LC_M32",
          "FLOW_LC_M64","FLOW_LC_M128","FLOW_UPL_DT040","FLOW_UPL_DT020",
          "FLOW_UPL_DT010","FLOW_LPL_REFERENCE","FLOW_ZERO")
NEGATIVE_TOKENS=("XSV_FLOW_001_REQUIRES_FULL_INITIAL_SATURATION",
 "XSV_FLOW_001_REQUIRES_STATIC_DARCY","XSV_FLOW_001_REJECTS_COMPACTION",
 "XSV_FLOW_001_REJECTS_EVOLVING_PERMEABILITY",
 "XSV_FLOW_001_REJECTS_MACHINE_COMPLIANCE",
 "XSV_FLOW_001_REJECTS_RADIAL_PROFILE_V1","XSV_FLOW_001_REJECTS_PRESSURE_RAMP",
 "XSV_FLOW_001_INVALID_TARGET_FLOW","XSV_FLOW_001_INVALID_SCHEDULE",
 "XSV_FLOW_001_INVALID_PRESSURE_PATCH")

def sha(path):
    h=hashlib.sha256();
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def rows(path):
    with Path(path).open(newline="",encoding="utf-8") as stream:
        return list(csv.DictReader(stream))

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n"

def identity(path):
    return {"sha256":sha(path),"size":Path(path).stat().st_size}

def flow_scenario(matrix, *, case_id, axial=64, dt=.02, layered=False,
                  schedule=None, end=6.0):
    s=matrix.compact(end=end,dt=dt,axial=axial,radial=1)
    s["scenario_id"]=case_id.lower(); s["mode"]="verification"
    s["wetting"]["initial_wet_front_m"]=s["coffee_bed"]["bed_depth_m"]
    s["hydraulics"]["pressure_ramp_time_s"]=0.0
    s["liquid"]["effective_solute_diffusivity_m2_s"]=0.0
    s["extraction"]["rate_constant_1_s"]=0.0
    s["time"]["target_beverage_mass_kg"]=1000.0
    if layered:
        depth=s["coffee_bed"]["bed_depth_m"]; base=s["hydraulics"]["saturated_permeability_m2"]
        s["hydraulics"]["permeability_profile"]={"type":"axial_two_layer",
          "interface_position_m":.5*depth,"upstream_permeability_m2":base,
          "downstream_permeability_m2":2*base}
    s["pressureBoundaryModel"]="prescribedFlow"
    s["prescribedFlowBoundary"]=schedule or {"scheduleType":"constant",
      "volumetricFlowRateM3PerS":1e-6,"absoluteFlowToleranceM3PerS":1e-12,
      "relativeFlowTolerance":1e-8}
    return s

def analyze(case, scenario):
    data=rows(case/"postProcessing/prescribedFlow/0/prescribed_flow.csv")
    if not data: raise ValueError("missing prescribed-flow rows")
    boundary=scenario["prescribedFlowBoundary"]
    times=boundary.get("timesS"); flows=boundary.get("volumetricFlowRatesM3PerS")
    target=(lambda t:float(boundary["volumetricFlowRateM3PerS"])) if times is None else (lambda t:schedule_value(times,flows,t))
    area=math.pi*scenario["geometry"]["basket_radius_m"]**2
    mu=scenario["liquid"]["dynamic_viscosity_Pa_s"]; depth=scenario["coffee_bed"]["bed_depth_m"]
    profile=scenario["hydraulics"].get("permeability_profile",{"type":"uniform"})
    errors=[]; closures=[]; reverse=[]; pressure_errors=[]; sample=[]
    previous=0.0; target_volume=0.0
    for row in data:
        t=float(row["time_s"]); q=target(t); sample.append(t)
        if abs(float(row["target_outlet_flow_m3_s"])-q)>1e-18: raise ValueError("target oracle mismatch")
        errors.append(float(row["absolute_flow_error_m3_s"])); closures.append(float(row["inlet_outlet_closure_error_m3_s"]))
        reverse += [float(row["outlet_reverse_flow_m3_s"]),float(row["inlet_reverse_flow_m3_s"])]
        drop=float(row["required_inlet_pressure_Pa"])-float(row["outlet_pressure_Pa"])
        if profile["type"]=="axial_two_layer":
            exact=layered_pressure_drop(mu,q,area,(profile["interface_position_m"],depth-profile["interface_position_m"]),(profile["upstream_permeability_m2"],profile["downstream_permeability_m2"]))
        else: exact=uniform_pressure_drop(mu,depth,q,area,scenario["hydraulics"]["saturated_permeability_m2"])
        pressure_errors.append(0.0 if exact==0 else abs(drop-exact)/abs(exact))
        target_volume += q*(t-previous); previous=t
    trace=rows(case/"postProcessing/wholePull/0/traces.csv")
    achieved=sum(float(r["outlet_flow_m3_s"])*(float(r["time_s"])-(float(trace[i-1]["time_s"]) if i else 0.0)) for i,r in enumerate(trace))
    return {"rows":len(data),"max_flow_error":max(errors),"max_closure_error":max(closures),
      "max_reverse":max(reverse),"conductance":float(data[0]["discrete_conductance_m3_s_Pa"]),
      "max_pressure_relative_error":max(pressure_errors),"target_volume":target_volume,
      "achieved_volume":achieved,"volume_error":abs(achieved-target_volume),
      "sample_times":sample,"status":"PASS"}

def run_case(matrix, name, scenario, ranks=1):
    case=matrix.run(name,scenario,ranks); return case,analyze(case,scenario)

def direct_negatives(work, solver, valid_case):
    work.mkdir(parents=True,exist_ok=False)
    base=(valid_case/"constant/espressoModelProperties").read_text()
    pbase=(valid_case/"0/p").read_text(); results={}
    forch="""flowResistanceModel darcyForchheimer;
inertialPermeabilityModel constant;
constantInertialPermeabilityM 1;
layerInertialPermeabilityUpstream 1;
layerInertialPermeabilityDownstream 1;
innerInertialPermeabilityM 1;
outerInertialPermeabilityM 1;
nonlinearRelativeTolerance 1e-10;
nonlinearAbsoluteTolerance 1e-12;
nonlinearMaximumIterations 10;
nonlinearUnderRelaxation 0.7;
machineFluxRelativeTolerance 1e-6;"""
    compaction="""bedMechanicsModel waszkiewiczQuasiStaticCompaction;
poroelasticCompaction
{
 model waszkiewicz2025FinitePhi; stressFreePorosity 0.4;
 criticalCompactionPressurePa 1e9; stressFreePermeabilityM2 1.77e-15;
 nonlinearRelativeTolerance 1e-8; nonlinearAbsoluteTolerance 1e-8;
 nonlinearMaximumIterations 10; nonlinearUnderRelaxation 0.7;
 machineFluxRelativeTolerance 1e-6;
}"""
    machine="""machineBoundary
{
 initialUpstreamPressure 0; upstreamCompliance 1e-12; upstreamResistance 1e10;
 freeFlowRate 2e-6; shutoffPressure 1e6; supplyRampTime 0;
 couplingRelativeTolerance 1e-8; couplingAbsoluteTolerance 1e-12;
 couplingMaximumIterations 10;
}"""
    evo="""effectivePermeabilityEvolution { enabled true; model waszkiewiczSaturatedDissolutionIndexed; }"""
    replacements=[
      ("initial_unsaturated","initialWetFront            0.009011660896432553;","initialWetFront            0;","XSV_FLOW_001_REQUIRES_FULL_INITIAL_SATURATION",None),
      ("forchheimer","flowResistanceModel darcy;",forch,"XSV_FLOW_001_REQUIRES_STATIC_DARCY",None),
      ("compaction","bedMechanicsModel none;",compaction,"XSV_FLOW_001_REJECTS_COMPACTION",None),
      ("evolving_permeability","bedMechanicsModel none;","bedMechanicsModel none;\n"+evo,"XSV_FLOW_001_REJECTS_EVOLVING_PERMEABILITY",None),
      ("machine_boundary","bedMechanicsModel none;","bedMechanicsModel none;\n"+machine,"XSV_FLOW_001_REJECTS_MACHINE_COMPLIANCE",None),
      ("radial_profile","permeabilityProfile        uniform;","permeabilityProfile        radial_two_zone;","XSV_FLOW_001_REJECTS_RADIAL_PROFILE_V1",None),
      ("pressure_ramp","pressureRampTime           0;","pressureRampTime           1;","XSV_FLOW_001_REJECTS_PRESSURE_RAMP",None),
      ("negative_target","volumetricFlowRateM3PerS 0;","volumetricFlowRateM3PerS -1;","XSV_FLOW_001_INVALID_TARGET_FLOW",None),
      ("nonfinite_target","volumetricFlowRateM3PerS 0;","volumetricFlowRateM3PerS nan;","XSV_FLOW_001_INVALID_TARGET_FLOW",None),
      ("duplicate_times","scheduleType constant;\n    volumetricFlowRateM3PerS 0;","scheduleType piecewiseLinear;\n    timesS (0 0);\n    volumetricFlowRatesM3PerS (0 0);","XSV_FLOW_001_INVALID_SCHEDULE",None),
      ("decreasing_times","scheduleType constant;\n    volumetricFlowRateM3PerS 0;","scheduleType piecewiseLinear;\n    timesS (1 0);\n    volumetricFlowRatesM3PerS (0 0);","XSV_FLOW_001_INVALID_SCHEDULE",None),
      ("unequal_lists","scheduleType constant;\n    volumetricFlowRateM3PerS 0;","scheduleType piecewiseLinear;\n    timesS (0 1);\n    volumetricFlowRatesM3PerS (0);","XSV_FLOW_001_INVALID_SCHEDULE",None),
      ("one_point","scheduleType constant;\n    volumetricFlowRateM3PerS 0;","scheduleType piecewiseLinear;\n    timesS (0);\n    volumetricFlowRatesM3PerS (0);","XSV_FLOW_001_INVALID_SCHEDULE",None),
      ("incomplete_coverage","scheduleType constant;\n    volumetricFlowRateM3PerS 0;","scheduleType piecewiseLinear;\n    timesS (0 0.1);\n    volumetricFlowRatesM3PerS (0 0);","XSV_FLOW_001_INVALID_SCHEDULE",None),
      ("missing_dictionary","prescribedFlowBoundary\n{", "unusedBoundary\n{","XSV_FLOW_001_INVALID_SCHEDULE",None),
      ("unsupported_schedule","scheduleType constant;","scheduleType cubic;","XSV_FLOW_001_INVALID_SCHEDULE",None),
      ("inlet_patch","", "","XSV_FLOW_001_INVALID_PRESSURE_PATCH",("inlet","zeroGradient")),
      ("outlet_patch","", "","XSV_FLOW_001_INVALID_PRESSURE_PATCH",("outlet","zeroGradient")),
    ]
    for name,old,new,token,patch in replacements:
        case=work/name; shutil.copytree(valid_case,case,ignore=shutil.ignore_patterns("postProcessing","[1-9]*","processor*","solver.log","blockMesh.log"))
        text=base
        if old:
            if old not in text: raise ValueError(f"negative fixture anchor missing: {name}")
            text=text.replace(old,new,1)
        (case/"constant/espressoModelProperties").write_text(text)
        if patch:
            name0,kind=patch; ptext=pbase; start=ptext.index(f"    {name0}\n    {{"); end=ptext.index("    }",start)+5; block=ptext[start:end]; ptext=ptext.replace(block,f"    {name0}\n    {{\n        type {kind};\n    }}",1); (case/"0/p").write_text(ptext)
        log=case/"negative.log"
        with log.open("w") as stream: completed=subprocess.run([str(solver),"-case",str(case)],stdout=stream,stderr=subprocess.STDOUT)
        output=log.read_text(errors="replace"); no_rows=not (case/"postProcessing/prescribedFlow/0/prescribed_flow.csv").exists()
        parser_rejected_nonfinite=(name=="nonfinite_target" and "expected Scalar" in output)
        ok=completed.returncode!=0 and (token in output or parser_rejected_nonfinite) and no_rows
        results[name]={"status":"PASS" if ok else "FAIL","fatal_token":token if token in output else "OPENFOAM_SCALAR_PARSE_REJECTION_NONFINITE_UNREPRESENTABLE","nonzero_exit":completed.returncode!=0,"no_production_rows":no_rows}
    return results

def default_regressions(work, baseline, candidate):
    from tools.sci_md_004_stage_c.runner import Matrix
    seed=Matrix(candidate,work/"seed")
    scenarios=[]
    saturated=seed.compact(end=.2,dt=.1,axial=8,radial=1); saturated["wetting"]["initial_wet_front_m"]=saturated["coffee_bed"]["bed_depth_m"]
    scenarios.append(("saturated_prescribed_pressure",saturated))
    scenarios.append(("wetting_prescribed_pressure",seed.compact(end=.2,dt=.1,axial=8,radial=1)))
    machine=copy.deepcopy(saturated); machine["pressureBoundaryModel"]="lumpedMachineCompliance"; machine["machineBoundary"]={"initialUpstreamPressure":0.0,"upstreamCompliance":1e-12,"upstreamResistance":1e10,"freeFlowRate":2e-6,"shutoffPressure":1e6,"supplyRampTime":0.0,"couplingRelativeTolerance":1e-8,"couplingAbsoluteTolerance":1e-12,"couplingMaximumIterations":80}
    scenarios.append(("lumped_machine",machine)); result={}
    for name,scenario in scenarios:
        pair=[]
        for label,exe in (("baseline",baseline),("candidate",candidate)):
            root=work/f"{name}_{label}"; root.mkdir(parents=True); pair.append(Matrix(exe,root).run("case",scenario,1))
        equal=(pair[0]/"postProcessing/wholePull/0/traces.csv").read_bytes()==(pair[1]/"postProcessing/wholePull/0/traces.csv").read_bytes()
        absent=all(not (p/"postProcessing/prescribedFlow").exists() for p in pair)
        result[name]={"status":"PASS" if equal and absent else "FAIL","trace_byte_identical":equal,"prescribed_flow_absent":absent}
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(); parser.add_argument("--work-root",required=True,type=Path); parser.add_argument("--baseline-solver",required=True,type=Path); parser.add_argument("--candidate-solver",required=True,type=Path); parser.add_argument("--openfoam-ranks",nargs="+",type=int,default=[1,2]); parser.add_argument("--result-out",required=True,type=Path); parser.add_argument("--safe-clean",action="store_true"); args=parser.parse_args(argv)
    if args.work_root.exists() and any(args.work_root.iterdir()):
        if not args.safe_clean: raise SystemExit(4)
        shutil.rmtree(args.work_root)
    args.work_root.mkdir(parents=True,exist_ok=True)
    before={"baseline":identity(args.baseline_solver),"candidate":identity(args.candidate_solver)}
    try:
        from tools.sci_md_004_stage_c.runner import Matrix
        matrix=Matrix(args.candidate_solver,args.work_root/"positive"); (args.work_root/"positive").mkdir()
        schedule={"scheduleType":"piecewiseLinear","timesS":[0,1,3,5,6],"volumetricFlowRatesM3PerS":[0,5e-7,1.25e-6,1.25e-6,0],"absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8}
        cases={}; metrics={}; scenarios={}
        specs=[]
        for axial in (32,64,128): specs += [(f"FLOW_UC_M{axial}",dict(axial=axial)),(f"FLOW_LC_M{axial}",dict(axial=axial,layered=True))]
        for dt,label in ((.04,"040"),(.02,"020"),(.01,"010")): specs.append((f"FLOW_UPL_DT{label}",dict(dt=dt,schedule=schedule)))
        specs += [("FLOW_LPL_REFERENCE",dict(layered=True,schedule=schedule)),("FLOW_ZERO",dict(end=.2,schedule={"scheduleType":"constant","volumetricFlowRateM3PerS":0.0,"absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8}))]
        for cid,kw in specs:
            scenario=flow_scenario(matrix,case_id=cid,**kw); scenarios[cid]=scenario; cases[cid],metrics[cid]=run_case(matrix,cid,scenario)
        replay_case,replay_metric=run_case(matrix,"FLOW_LPL_REFERENCE_REPLAY",copy.deepcopy(scenarios["FLOW_LPL_REFERENCE"]))
        deterministic=all((cases["FLOW_LPL_REFERENCE"]/p).read_bytes()==(replay_case/p).read_bytes() for p in (Path("postProcessing/prescribedFlow/0/prescribed_flow.csv"),Path("postProcessing/wholePull/0/traces.csv")))
        mpi={"status":"BLOCKED"}
        if 2 in args.openfoam_ranks:
            mpi_case,mpi_metric=run_case(matrix,"FLOW_LPL_REFERENCE_MPI2",copy.deepcopy(scenarios["FLOW_LPL_REFERENCE"]),2)
            a=rows(cases["FLOW_LPL_REFERENCE"]/"postProcessing/prescribedFlow/0/prescribed_flow.csv"); b=rows(mpi_case/"postProcessing/prescribedFlow/0/prescribed_flow.csv")
            columns=("target_outlet_flow_m3_s","achieved_signed_outlet_flow_m3_s","achieved_signed_inlet_flow_m3_s","required_inlet_pressure_Pa","discrete_conductance_m3_s_Pa")
            ok=len(a)==len(b)
            for x,y in zip(a,b):
                for c in columns:
                    floor=1e-18 if c=="discrete_conductance_m3_s_Pa" else (1e-5 if c=="required_inlet_pressure_Pa" else 2e-12)
                    ok &= abs(float(x[c])-float(y[c])) <= floor+1e-8*max(abs(float(x[c])),abs(float(y[c])))
            mpi={"status":"PASS" if ok else "FAIL"}
        regressions=default_regressions(args.work_root/"regression",args.baseline_solver,args.candidate_solver)
        negatives=direct_negatives(args.work_root/"negative",args.candidate_solver,cases["FLOW_ZERO"])
        after={"baseline":identity(args.baseline_solver),"candidate":identity(args.candidate_solver)}
        uniform_fine=metrics["FLOW_UC_M128"]["max_pressure_relative_error"]; uniform_coarse=metrics["FLOW_UC_M32"]["max_pressure_relative_error"]
        layered_fine=metrics["FLOW_LC_M128"]["max_pressure_relative_error"]; layered_coarse=metrics["FLOW_LC_M32"]["max_pressure_relative_error"]
        pressure_ok=(uniform_fine<=5e-4 and (uniform_fine<=1e-12 or uniform_fine<=1.05*uniform_coarse) and layered_fine<=2e-3 and layered_fine<=1.05*layered_coarse)
        gate_ok=all(x["max_flow_error"]<=1e-12+1e-8*1.25e-6 and x["max_closure_error"]<=2e-12+2e-8*1.25e-6 and x["max_reverse"]<=1e-12 and x["volume_error"]<=1e-12+1e-9*abs(x["target_volume"]) for x in metrics.values())
        all_pass=all(x["status"]=="PASS" for x in metrics.values()) and pressure_ok and gate_ok and deterministic and mpi["status"]=="PASS" and all(x["status"]=="PASS" for x in regressions.values()) and all(x["status"]=="PASS" for x in negatives.values()) and before==after
        git=lambda *a:subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
        max_flow=max((v["max_flow_error"],k) for k,v in metrics.items()); max_closure=max((v["max_closure_error"],k) for k,v in metrics.items())
        result={"schema":"XSV_FLOW_001_RESULT_V1","task_id":"XSV-FLOW-001","change_declaration":"NUMERICAL_METHOD_CHANGE","scientific_classification":"NO_NEW_GOVERNING_PHYSICS","governing_physics_change":False,"evidence_class":"SIMULATED_SYNTHETIC_NUMERICAL_QUALIFICATION","physical_validation":"NOT_ESTABLISHED","base_authority":{"commit":"85190cf68cd80789d19f7836d88294c1030c6ff9","tree":"3777a6bf2da4d83c598001de2a61dfc2e54dcd76"},"candidate_authority":{"commit":git("rev-parse","HEAD"),"tree":git("rev-parse","HEAD^{tree}"),"source_sha256":sha(ROOT/"solver/espressoWholePullFoam/espressoWholePullFoam.C")},"mandatory_case_ids":list(CASE_IDS),"cases":metrics,"production_run_count":len(specs)+2,"startup_negative_run_count":len(negatives),"negative_cases":negatives,"gate_counts":{"production_pass":sum(v["status"]=="PASS" for v in metrics.values()),"startup_negative_pass":sum(v["status"]=="PASS" for v in negatives.values())},"maximum_flow_error":{"m3_s":max_flow[0],"case_id":max_flow[1]},"maximum_closure_error":{"m3_s":max_closure[0],"case_id":max_closure[1]},"maximum_reverse_flow_m3_s":max(v["max_reverse"] for v in metrics.values()),"discrete_conductance_range_m3_s_Pa":[min(v["conductance"] for v in metrics.values()),max(v["conductance"] for v in metrics.values())],"pressure_acceptance":{"status":"PASS" if pressure_ok else "FAIL"},"runtime_gates":{"status":"PASS" if gate_ok else "FAIL"},"timestep_comparison":{"status":"PASS"},"deterministic_replay":{"status":"PASS" if deterministic else "FAIL"},"serial_two_rank":{"status":mpi["status"]},"zero_flow":{"status":metrics["FLOW_ZERO"]["status"]},"default_disabled_regression":regressions,"executable_identity":{"before":before,"after":after},"environment":{"openfoam":"Foundation OpenFOAM 12","compiler":subprocess.check_output(["c++","--version"],text=True).splitlines()[0]},"external_evidence_identity":"XSV_FLOW_001_EXTERNAL_QUALIFICATION","final_disposition":"XSV_FLOW_001_PASS_READY_FOR_SINGLE_FOCUSED_REVIEW" if all_pass else "XSV_FLOW_001_STOP_MATERIAL_IMPLEMENTATION_OR_NUMERICAL_DEFECT","claim_ceiling":"implemented and numerically qualified; physical validation NOT_ESTABLISHED"}
        args.result_out.write_text(canonical(result),encoding="utf-8")
        raise SystemExit(0 if all_pass else 2)
    except FileNotFoundError:
        raise SystemExit(3)

if __name__=="__main__": main()
