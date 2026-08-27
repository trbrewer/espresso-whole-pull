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
TIME_TOLERANCE=1e-12
RATIO_TOLERANCE=1e-12
NUMERIC_COLUMNS=("time_s","target_outlet_flow_m3_s",
 "achieved_signed_outlet_flow_m3_s","achieved_positive_outlet_flow_m3_s",
 "achieved_signed_inlet_flow_m3_s","required_inlet_pressure_Pa",
 "outlet_pressure_Pa","discrete_conductance_m3_s_Pa",
 "absolute_flow_error_m3_s","flow_error_limit_m3_s","flow_error_ratio",
 "inlet_outlet_closure_error_m3_s","closure_error_limit_m3_s",
 "outlet_reverse_flow_m3_s","inlet_reverse_flow_m3_s")

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

def parsed_rows(data):
    parsed=[]
    for index,row in enumerate(data):
        item={}
        for column in NUMERIC_COLUMNS:
            try: value=float(row[column])
            except (KeyError,TypeError,ValueError) as error:
                raise ValueError(f"row {index}: invalid {column}") from error
            if not math.isfinite(value): raise ValueError(f"row {index}: nonfinite {column}")
            item[column]=value
        for column in ("flow_gate_pass","closure_gate_pass","direction_gate_pass"):
            try: item[column]=row[column].strip().lower() in ("1","true","pass")
            except (KeyError,AttributeError) as error:
                raise ValueError(f"row {index}: invalid {column}") from error
        parsed.append(item)
    sequence=[row["time_s"] for row in parsed]
    if any(b <= a for a,b in zip(sequence,sequence[1:])):
        raise ValueError("time_s must be strictly increasing and nonduplicated")
    return parsed

def schedule_oracle(boundary):
    if boundary["scheduleType"]=="constant":
        return lambda _time:float(boundary["volumetricFlowRateM3PerS"])
    times=boundary["timesS"]; flows=boundary["volumetricFlowRatesM3PerS"]
    return lambda time:schedule_value(times,flows,time)

def maximum_at(values):
    value,time=max(values,key=lambda item:item[0])
    return value,time

def align_rows(coarse, fine, tolerance=TIME_TOLERANCE):
    matches=[]; problems=0; used=set()
    for left in coarse:
        found=[(index,right) for index,right in enumerate(fine) if abs(left["time_s"]-right["time_s"])<=tolerance]
        if len(found)!=1: problems += 1
        elif found[0][0] in used: problems += 1
        else: used.add(found[0][0]); matches.append((left,found[0][1]))
    return matches,problems

def timestep_comparison(case_rows, scenarios):
    ids=("FLOW_UPL_DT040","FLOW_UPL_DT020","FLOW_UPL_DT010")
    try: parsed={case_id:parsed_rows(case_rows[case_id]) for case_id in ids}
    except (KeyError,ValueError) as error:
        return {"status":"FAIL","time_alignment_tolerance_s":TIME_TOLERANCE,"pairs":[],"reduction_error":str(error)}
    knot_status={case_id:all(sum(abs(row["time_s"]-knot)<=TIME_TOLERANCE for row in parsed[case_id])==1
        for knot in (1.0,3.0,5.0,6.0)) for case_id in ids}
    pairs=[]
    for coarse_id,fine_id in ((ids[0],ids[1]),(ids[0],ids[2]),(ids[1],ids[2])):
        coarse=parsed[coarse_id]; fine=parsed[fine_id]
        matched,missing=align_rows(coarse,fine)
        oracle_a=schedule_oracle(scenarios[coarse_id]["prescribedFlowBoundary"])
        oracle_b=schedule_oracle(scenarios[fine_id]["prescribedFlowBoundary"])
        pressure_values=[]; target_values=[]; conductance_values=[]; outlet_values=[]; failures=missing
        for left,right in matched:
            time=left["time_s"]
            target_diff=abs(left["target_outlet_flow_m3_s"]-right["target_outlet_flow_m3_s"])
            target_values.append((target_diff,time))
            failures += abs(left["target_outlet_flow_m3_s"]-oracle_a(time))>1e-18
            failures += abs(right["target_outlet_flow_m3_s"]-oracle_b(time))>1e-18
            failures += target_diff>1e-18
            pressure_diff=abs(left["required_inlet_pressure_Pa"]-right["required_inlet_pressure_Pa"])
            pressure_limit=1e-6+1e-9*max(abs(left["required_inlet_pressure_Pa"]),abs(right["required_inlet_pressure_Pa"]))
            pressure_values.append((pressure_diff,time,pressure_limit))
            failures += pressure_diff>pressure_limit
            conductance_values.append((abs(left["discrete_conductance_m3_s_Pa"]-right["discrete_conductance_m3_s_Pa"]),time))
            outlet_values.append((abs(left["outlet_pressure_Pa"]-right["outlet_pressure_Pa"]),time))
        final_ok=bool(coarse and fine and abs(coarse[-1]["time_s"]-6.0)<=TIME_TOLERANCE and abs(fine[-1]["time_s"]-6.0)<=TIME_TOLERANCE)
        failures += not final_ok
        failures += not knot_status[coarse_id] or not knot_status[fine_id]
        worst_pressure=max(pressure_values,default=(math.inf,None,0.0),key=lambda item:item[0])
        worst_target=max(target_values,default=(math.inf,None),key=lambda item:item[0])
        worst_conductance=max(conductance_values,default=(math.inf,None),key=lambda item:item[0])
        worst_outlet=max(outlet_values,default=(math.inf,None),key=lambda item:item[0])
        pairs.append({"pair":f"{coarse_id}_vs_{fine_id}","coarse_row_count":len(coarse),
          "matched_common_time_count":len(matched),"required_knot_presence_status":"PASS" if knot_status[coarse_id] and knot_status[fine_id] else "FAIL",
          "maximum_absolute_pressure_difference_Pa":worst_pressure[0],"maximum_pressure_difference_time_s":worst_pressure[1],
          "pressure_limit_at_worst_time_Pa":worst_pressure[2],"maximum_target_difference_m3_s":worst_target[0],
          "maximum_conductance_difference_m3_s_Pa":worst_conductance[0],"maximum_outlet_pressure_difference_Pa":worst_outlet[0],
          "missing_or_duplicate_time_count":missing,"status":"PASS" if failures==0 else "FAIL"})
    return {"status":"PASS" if all(pair["status"]=="PASS" for pair in pairs) else "FAIL",
      "time_alignment_tolerance_s":TIME_TOLERANCE,"required_knots_s":[1.0,3.0,5.0,6.0],"pairs":pairs}

def integrated_volume(data, column):
    previous=0.0; total=0.0
    for row in data:
        total += row[column]*(row["time_s"]-previous); previous=row["time_s"]
    return total

def serial_two_rank_comparison(serial_rows, mpi_rows):
    try: serial=parsed_rows(serial_rows); mpi=parsed_rows(mpi_rows)
    except ValueError as error:
        return {"status":"FAIL","row_count_status":"FAIL","time_alignment_status":"FAIL","common_row_count":0,"reduction_error":str(error)}
    matched,alignment_problems=align_rows(serial,mpi)
    row_count_ok=len(serial)==len(mpi)
    endpoints_ok=bool(serial and mpi and abs(serial[0]["time_s"]-mpi[0]["time_s"])<=TIME_TOLERANCE and abs(serial[-1]["time_s"]-mpi[-1]["time_s"])<=TIME_TOLERANCE)
    fields=("target_outlet_flow_m3_s","achieved_signed_outlet_flow_m3_s","achieved_signed_inlet_flow_m3_s",
      "required_inlet_pressure_Pa","discrete_conductance_m3_s_Pa","flow_error_ratio","inlet_outlet_closure_error_m3_s")
    maxima={field:(-1.0,None,0.0) for field in fields}; failures=alignment_problems+(not row_count_ok)+(not endpoints_ok)
    for left,right in matched:
        time=left["time_s"]
        for field in fields:
            difference=abs(left[field]-right[field]); limit=0.0
            if field=="required_inlet_pressure_Pa": limit=1e-5+1e-8*max(abs(left[field]),abs(right[field]))
            elif field=="discrete_conductance_m3_s_Pa": limit=1e-18+1e-8*max(abs(left[field]),abs(right[field]))
            elif field in ("target_outlet_flow_m3_s","achieved_signed_outlet_flow_m3_s","achieved_signed_inlet_flow_m3_s"):
                limit=2e-12+1e-8*max(abs(left[field]),abs(right[field]))
            elif field=="inlet_outlet_closure_error_m3_s": limit=max(left["closure_error_limit_m3_s"],right["closure_error_limit_m3_s"])
            if difference>maxima[field][0]: maxima[field]=(difference,time,limit)
            if field not in ("flow_error_ratio",) and difference>limit: failures += 1
        for row in (left,right):
            failures += row["flow_error_ratio"]>1.0+RATIO_TOLERANCE
            failures += row["inlet_outlet_closure_error_m3_s"]>row["closure_error_limit_m3_s"]
    serial_target=integrated_volume(serial,"target_outlet_flow_m3_s"); mpi_target=integrated_volume(mpi,"target_outlet_flow_m3_s")
    serial_achieved=integrated_volume(serial,"achieved_signed_outlet_flow_m3_s"); mpi_achieved=integrated_volume(mpi,"achieved_signed_outlet_flow_m3_s")
    serial_error=abs(serial_achieved-serial_target); mpi_error=abs(mpi_achieved-mpi_target); volume_difference=abs(serial_achieved-mpi_achieved)
    failures += serial_error>1e-12+1e-9*abs(serial_target)
    failures += mpi_error>1e-12+1e-9*abs(mpi_target)
    failures += volume_difference>1e-12+1e-9*max(abs(serial_achieved),abs(mpi_achieved))
    result={"status":"PASS" if failures==0 else "FAIL","row_count_status":"PASS" if row_count_ok else "FAIL",
      "time_alignment_status":"PASS" if alignment_problems==0 and endpoints_ok else "FAIL","common_row_count":len(matched),
      "first_time_s":{"serial":serial[0]["time_s"] if serial else None,"mpi":mpi[0]["time_s"] if mpi else None},
      "final_time_s":{"serial":serial[-1]["time_s"] if serial else None,"mpi":mpi[-1]["time_s"] if mpi else None},
      "serial_target_volume_m3":serial_target,"mpi_target_volume_m3":mpi_target,"serial_achieved_volume_m3":serial_achieved,
      "mpi_achieved_volume_m3":mpi_achieved,"serial_target_volume_error_m3":serial_error,"mpi_target_volume_error_m3":mpi_error,
      "serial_mpi_volume_difference_m3":volume_difference,
      "maximum_flow_error_ratio":{"serial":max((r["flow_error_ratio"] for r in serial),default=0.0),"mpi":max((r["flow_error_ratio"] for r in mpi),default=0.0)},
      "maximum_closure_error_m3_s":{"serial":max((r["inlet_outlet_closure_error_m3_s"] for r in serial),default=0.0),"mpi":max((r["inlet_outlet_closure_error_m3_s"] for r in mpi),default=0.0)}}
    for field,(difference,time,limit) in maxima.items():
        result[f"maximum_{field}_difference"]={"value":max(0.0,difference),"time_s":time}
        if field in ("required_inlet_pressure_Pa","discrete_conductance_m3_s_Pa"): result[f"maximum_{field}_difference"]["limit_at_worst_time"]=limit
    return result

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
    raw=rows(case/"postProcessing/prescribedFlow/0/prescribed_flow.csv")
    if not raw: raise ValueError("missing prescribed-flow rows")
    try: data=parsed_rows(raw)
    except ValueError as error:
        return {"status":"FAIL","row_count":len(raw),"reduction_error":str(error),"gate_failure_count":1}
    boundary=scenario["prescribedFlowBoundary"]
    target=schedule_oracle(boundary)
    area=math.pi*scenario["geometry"]["basket_radius_m"]**2
    mu=scenario["liquid"]["dynamic_viscosity_Pa_s"]; depth=scenario["coffee_bed"]["bed_depth_m"]
    profile=scenario["hydraulics"].get("permeability_profile",{"type":"uniform"})
    errors=[]; closures=[]; reverse=[]; ratios=[]; pressure_errors=[]; failures=0
    for row in data:
        t=row["time_s"]; q=target(t)
        failures += abs(row["target_outlet_flow_m3_s"]-q)>1e-18
        failures += sum(not row[flag] for flag in ("flow_gate_pass","closure_gate_pass","direction_gate_pass"))
        failures += row["absolute_flow_error_m3_s"]>row["flow_error_limit_m3_s"]
        failures += row["inlet_outlet_closure_error_m3_s"]>row["closure_error_limit_m3_s"]
        failures += row["outlet_reverse_flow_m3_s"]>1e-12 or row["inlet_reverse_flow_m3_s"]>1e-12
        failures += row["flow_error_ratio"]>1.0+RATIO_TOLERANCE
        errors.append((row["absolute_flow_error_m3_s"],t)); closures.append((row["inlet_outlet_closure_error_m3_s"],t))
        reverse += [(row["outlet_reverse_flow_m3_s"],t),(row["inlet_reverse_flow_m3_s"],t)]; ratios.append((row["flow_error_ratio"],t))
        drop=row["required_inlet_pressure_Pa"]-row["outlet_pressure_Pa"]
        if profile["type"]=="axial_two_layer":
            exact=layered_pressure_drop(mu,q,area,(profile["interface_position_m"],depth-profile["interface_position_m"]),(profile["upstream_permeability_m2"],profile["downstream_permeability_m2"]))
        else: exact=uniform_pressure_drop(mu,depth,q,area,scenario["hydraulics"]["saturated_permeability_m2"])
        pressure_errors.append((0.0 if exact==0 else abs(drop-exact)/abs(exact),t))
    target_volume=integrated_volume(data,"target_outlet_flow_m3_s")
    achieved=integrated_volume(data,"achieved_signed_outlet_flow_m3_s")
    volume_error=abs(achieved-target_volume); failures += volume_error>1e-12+1e-9*abs(target_volume)
    max_error,error_time=maximum_at(errors); max_closure,closure_time=maximum_at(closures)
    max_reverse,reverse_time=maximum_at(reverse); max_ratio,ratio_time=maximum_at(ratios)
    max_pressure,pressure_time=maximum_at(pressure_errors)
    return {"row_count":len(data),"first_time_s":data[0]["time_s"],"last_time_s":data[-1]["time_s"],
      "maximum_flow_error_m3_s":max_error,"maximum_flow_error_time_s":error_time,
      "maximum_closure_error_m3_s":max_closure,"maximum_closure_error_time_s":closure_time,
      "maximum_reverse_flow_m3_s":max_reverse,"maximum_reverse_flow_time_s":reverse_time,
      "maximum_flow_error_ratio":max_ratio,"maximum_flow_error_ratio_time_s":ratio_time,
      "discrete_conductance_m3_s_Pa":data[0]["discrete_conductance_m3_s_Pa"],
      "maximum_analytical_pressure_relative_error":max_pressure,"maximum_analytical_pressure_error_time_s":pressure_time,
      "target_discrete_volume_m3":target_volume,"achieved_discrete_volume_m3":achieved,"volume_error_m3":volume_error,
      "gate_failure_count":failures,"status":"PASS" if failures==0 else "FAIL"}

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

def regular_files(root, sections=None, exclude=()):
    result={}
    roots=[root/section for section in sections] if sections else [root]
    for base in roots:
        if not base.exists(): continue
        for path in sorted(base.rglob("*")):
            if path.is_file():
                relative=path.relative_to(root)
                if not any(relative==item or item in relative.parents for item in exclude): result[relative.as_posix()]=path.read_bytes()
    return result

def compare_default_pair(baseline_case, candidate_case):
    excluded=(Path("constant/polyMesh"),)
    baseline_inputs=regular_files(baseline_case,("0","constant","system"),excluded)
    candidate_inputs=regular_files(candidate_case,("0","constant","system"),excluded)
    baseline_outputs=regular_files(baseline_case/"postProcessing")
    candidate_outputs=regular_files(candidate_case/"postProcessing")
    input_paths=sorted(set(baseline_inputs)|set(candidate_inputs)); output_paths=sorted(set(baseline_outputs)|set(candidate_outputs))
    input_path_equal=set(baseline_inputs)==set(candidate_inputs); output_path_equal=set(baseline_outputs)==set(candidate_outputs)
    input_bytes_equal=input_path_equal and all(baseline_inputs[path]==candidate_inputs[path] for path in input_paths)
    output_bytes_equal=output_path_equal and all(baseline_outputs[path]==candidate_outputs[path] for path in output_paths)
    prescribed_absent=all(not (case/"postProcessing/prescribedFlow").exists() for case in (baseline_case,candidate_case))
    species_paths=[path for path in output_paths if "species" in path.lower() or "fraction" in path.lower()]
    status=input_path_equal and input_bytes_equal and output_path_equal and output_bytes_equal and prescribed_absent
    return {"input_path_set_equality":input_path_equal,"input_byte_equality":input_bytes_equal,
      "input_file_count":len(input_paths),"postprocessing_path_set_equality":output_path_equal,
      "postprocessing_byte_equality":output_bytes_equal,"postprocessing_file_count":len(output_paths),
      "postprocessing_output_paths":output_paths,"species_fraction_output_comparison":"PASS" if species_paths else "NOT_APPLICABLE",
      "prescribed_flow_output_absence":prescribed_absent,"status":"PASS" if status else "FAIL"}

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
        result[name]=compare_default_pair(pair[0],pair[1])
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
        timestep=timestep_comparison({case_id:rows(cases[case_id]/"postProcessing/prescribedFlow/0/prescribed_flow.csv") for case_id in ("FLOW_UPL_DT040","FLOW_UPL_DT020","FLOW_UPL_DT010")},scenarios)
        mpi={"status":"BLOCKED"}
        if 2 in args.openfoam_ranks:
            mpi_case,mpi_metric=run_case(matrix,"FLOW_LPL_REFERENCE_MPI2",copy.deepcopy(scenarios["FLOW_LPL_REFERENCE"]),2)
            a=rows(cases["FLOW_LPL_REFERENCE"]/"postProcessing/prescribedFlow/0/prescribed_flow.csv"); b=rows(mpi_case/"postProcessing/prescribedFlow/0/prescribed_flow.csv")
            mpi=serial_two_rank_comparison(a,b)
        regressions=default_regressions(args.work_root/"regression",args.baseline_solver,args.candidate_solver)
        negatives=direct_negatives(args.work_root/"negative",args.candidate_solver,cases["FLOW_ZERO"])
        after={"baseline":identity(args.baseline_solver),"candidate":identity(args.candidate_solver)}
        uniform_fine=metrics["FLOW_UC_M128"]["maximum_analytical_pressure_relative_error"]; uniform_coarse=metrics["FLOW_UC_M32"]["maximum_analytical_pressure_relative_error"]
        layered_fine=metrics["FLOW_LC_M128"]["maximum_analytical_pressure_relative_error"]; layered_coarse=metrics["FLOW_LC_M32"]["maximum_analytical_pressure_relative_error"]
        pressure_ok=(uniform_fine<=5e-4 and (uniform_fine<=1e-12 or uniform_fine<=1.05*uniform_coarse) and layered_fine<=2e-3 and layered_fine<=1.05*layered_coarse)
        gate_ok=all(x["status"]=="PASS" for x in metrics.values())
        all_pass=gate_ok and pressure_ok and timestep["status"]=="PASS" and deterministic and mpi["status"]=="PASS" and all(x["status"]=="PASS" for x in regressions.values()) and all(x["status"]=="PASS" for x in negatives.values()) and before==after
        git=lambda *a:subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
        max_flow=max((v["maximum_flow_error_m3_s"],k,v["maximum_flow_error_time_s"]) for k,v in metrics.items()); max_closure=max((v["maximum_closure_error_m3_s"],k,v["maximum_closure_error_time_s"]) for k,v in metrics.items())
        result={"schema":"XSV_FLOW_001_RESULT_V1","task_id":"XSV-FLOW-001","change_declaration":"NUMERICAL_METHOD_CHANGE","scientific_classification":"NO_NEW_GOVERNING_PHYSICS","governing_physics_change":False,"evidence_class":"SIMULATED_SYNTHETIC_NUMERICAL_QUALIFICATION","physical_validation":"NOT_ESTABLISHED","base_authority":{"commit":"85190cf68cd80789d19f7836d88294c1030c6ff9","tree":"3777a6bf2da4d83c598001de2a61dfc2e54dcd76"},"candidate_authority":{"commit":git("rev-parse","HEAD"),"tree":git("rev-parse","HEAD^{tree}"),"source_sha256":sha(ROOT/"solver/espressoWholePullFoam/espressoWholePullFoam.C")},"mandatory_case_ids":list(CASE_IDS),"cases":metrics,"production_run_count":len(specs)+2,"startup_negative_run_count":len(negatives),"negative_cases":negatives,"gate_counts":{"production_pass":sum(v["status"]=="PASS" for v in metrics.values()),"startup_negative_pass":sum(v["status"]=="PASS" for v in negatives.values())},"maximum_flow_error":{"m3_s":max_flow[0],"case_id":max_flow[1],"time_s":max_flow[2]},"maximum_closure_error":{"m3_s":max_closure[0],"case_id":max_closure[1],"time_s":max_closure[2]},"maximum_reverse_flow_m3_s":max(v["maximum_reverse_flow_m3_s"] for v in metrics.values()),"discrete_conductance_range_m3_s_Pa":[min(v["discrete_conductance_m3_s_Pa"] for v in metrics.values()),max(v["discrete_conductance_m3_s_Pa"] for v in metrics.values())],"pressure_acceptance":{"status":"PASS" if pressure_ok else "FAIL"},"runtime_gates":{"status":"PASS" if gate_ok else "FAIL"},"timestep_comparison":timestep,"deterministic_replay":{"status":"PASS" if deterministic else "FAIL"},"serial_two_rank":mpi,"zero_flow":{"status":metrics["FLOW_ZERO"]["status"]},"default_disabled_regression":regressions,"executable_identity":{"before":before,"after":after},"environment":{"openfoam":"Foundation OpenFOAM 12","compiler":subprocess.check_output(["c++","--version"],text=True).splitlines()[0]},"external_evidence_identity":"XSV_FLOW_001_EXTERNAL_QUALIFICATION","final_disposition":"XSV_FLOW_001_PASS_READY_FOR_SINGLE_FOCUSED_REVIEW" if all_pass else "XSV_FLOW_001_STOP_MATERIAL_IMPLEMENTATION_OR_NUMERICAL_DEFECT","claim_ceiling":"implemented and numerically qualified; physical validation NOT_ESTABLISHED"}
        args.result_out.write_text(canonical(result),encoding="utf-8")
        raise SystemExit(0 if all_pass else 2)
    except FileNotFoundError:
        raise SystemExit(3)

if __name__=="__main__": main()
