#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,math,re,subprocess
from pathlib import Path
from waszkiewicz_effective_permeability import closure_state

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(a,b): return abs(a-b)/max(abs(b),1e-300)
def field_values(text):
 match=re.search(r"internalField\s+uniform\s+([^;]+);",text)
 if match: return [float(match.group(1))]
 match=re.search(r"internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\((.*?)\)\s*;",text,re.S)
 if not match: raise ValueError("unsupported internalField representation")
 values=[float(item) for item in match.group(2).split()]
 if len(values)!=int(match.group(1)): raise ValueError("internalField count mismatch")
 return values
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,required=True); ap.add_argument("--case",type=Path,required=True); ap.add_argument("--executable",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
 root=a.root.resolve(); case=a.case.resolve()
 contract=json.load(open(root/"validation/wp02/WP02_001_CLOSURE_CONTRACT.json")); cfg=json.load(open(root/"config/fixture_WP02_001_uniform_pressure.json")); acc=contract["uniform_pressure_fixture"]["acceptance"]; c=cfg["effective_permeability_evolution"]; s=c["source_parameters"]; h=cfg["hydraulics"]
 trace=case/"postProcessing/wholePull/0/traces.csv"; rows=list(csv.DictReader(open(trace)))
 expected=round((cfg["time"]["end_s"]-cfg["time"]["start_s"])/cfg["time"]["delta_t_s"])
 failures=[]; maxima={"darcy_flow_relative":0.,"effective_permeability_relative":0.,"multiplier_relative":0.,"source_state_time_absolute_s":0.,"pressure_probe_absolute_Pa":0.,"multiplier_field_spatial_cv":0.,"analytical_flow_relative":0.}
 hold=supported=0; prev=-1.; observed=[]
 for row in rows:
  t=float(row["time_s"]); state=closure_state(t,True,c["source_reference_pressure_bar"],c["source_to_solver_offset_s"],c["source_validity_start_s"],c["minimum_effective_multiplier"],h["saturated_permeability_m2"],pc_bar=s["pc_bar"],qc_g_s=s["qc_g_per_s"],k_g=s["k_solids_g"],l_s=s["l_solids_s"],m_s=s["m_solids_s"],dose_g=s["dose_g"])
  maxima["source_state_time_absolute_s"]=max(maxima["source_state_time_absolute_s"],abs(float(row["source_state_time_s"])-state["source_state_time_s"]))
  maxima["multiplier_relative"]=max(maxima["multiplier_relative"],rel(float(row["effective_permeability_multiplier"]),state["multiplier"]))
  maxima["effective_permeability_relative"]=max(maxima["effective_permeability_relative"],rel(float(row["effective_permeability_m2"]),state["effective_permeability_m2"]))
  q=state["effective_permeability_m2"]*cfg["geometry"]["hydraulic_bed_area_m2"]*h["target_inlet_pressure_gauge_Pa"]/(cfg["liquid"]["dynamic_viscosity_Pa_s"]*cfg["coffee_bed"]["bed_depth_m"])
  maxima["darcy_flow_relative"]=max(maxima["darcy_flow_relative"],rel(float(row["outlet_flow_m3_s"]),q))
  maxima["analytical_flow_relative"]=max(maxima["analytical_flow_relative"],rel(float(row["continuum_analytical_outlet_flow_m3_s"]),q))
  for key,x in (("pressure_probe_1_Pa",.0025),("pressure_probe_2_Pa",.0075)):
   expected_p=h["target_inlet_pressure_gauge_Pa"]*(1-x/cfg["coffee_bed"]["bed_depth_m"])
   maxima["pressure_probe_absolute_Pa"]=max(maxima["pressure_probe_absolute_Pa"],abs(float(row[key])-expected_p))
  if row["source_support_status"]!=state["source_support_status"]: failures.append("source_support_status")
  hold += state["source_support_status"]=="PRE_SOURCE_SUPPORT_SATURATED_HOLD"; supported += state["source_support_status"]=="SOURCE_SUPPORTED_SATURATED_STAGE"
  if supported and state["multiplier"]+1e-14<prev: failures.append("multiplier_monotonic")
  prev=state["multiplier"]; observed.append(state["multiplier"])
  for key in ("liquid_balance_residual_kg","solute_balance_residual_kg"):
   if abs(float(row[key]))>1e-10: failures.append(key)
  if float(row["min_saturation"])<1-1e-12 or float(row["max_concentration_kg_m3"])>1e-12: failures.append("bounded_state")
 for row in rows:
  td=case/row["time_s"]; field=td/"effectivePermeabilityMultiplier"
  if not field.exists(): failures.append("missing_multiplier_field"); continue
  try: values=field_values(field.read_text(errors="ignore"))
  except (ValueError,OverflowError): failures.append("invalid_multiplier_field"); continue
  if not values or not all(math.isfinite(value) for value in values): failures.append("invalid_multiplier_field"); continue
  mean=sum(values)/len(values); cv=0. if mean==0 and all(value==0 for value in values) else math.sqrt(sum((value-mean)**2 for value in values)/len(values))/abs(mean)
  expected_value=float(row["effective_permeability_multiplier"])
  maxima["multiplier_field_spatial_cv"]=max(maxima["multiplier_field_spatial_cv"],cv)
  maxima["multiplier_relative"]=max(maxima["multiplier_relative"],rel(mean,expected_value))
 if len(rows)!=expected: failures.append("trace_row_count")
 if not rows or abs(float(rows[-1]["time_s"])-cfg["time"]["end_s"])>1e-10: failures.append("endpoint")
 limits={"darcy_flow_relative":"maximum_relative_darcy_flow_error","effective_permeability_relative":"maximum_effective_permeability_relative_error","multiplier_relative":"maximum_multiplier_relative_error","source_state_time_absolute_s":"maximum_source_state_time_absolute_error_s","pressure_probe_absolute_Pa":"maximum_pressure_probe_absolute_error_Pa","multiplier_field_spatial_cv":"maximum_multiplier_field_spatial_cv"}
 for key,limit in limits.items():
  if maxima[key]>acc[limit]: failures.append(key)
 if abs(observed[-1]-1)>acc["maximum_final_multiplier_distance_from_one"]: failures.append("final_multiplier")
 manifest=case/"WP02_001_GENERATED_CASE_MANIFEST.json"
 implementation_commit=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
 out={"schema_version":"espresso.public.wp02_001_uniform_pressure_fixture.v1","task":"WP02-001","fixture_status":"FAIL" if failures else "PASS","fixture_role":"DETERMINISTIC_CODE_VERIFICATION_NOT_PHYSICAL_VALIDATION","execution":{"case_execution_count":1,"mpi_ranks":1,"executable_sha256":sha(a.executable),"trace_sha256":sha(trace),"trace_rows":len(rows),"endpoint_s":float(rows[-1]["time_s"])},"identity":{"implementation_commit":implementation_commit,"solver_source_sha256":sha(root/"solver/espressoWholePullFoam/espressoWholePullFoam.C"),"closure_contract_sha256":sha(root/"validation/wp02/WP02_001_CLOSURE_CONTRACT.json"),"fixture_config_sha256":sha(root/"config/fixture_WP02_001_uniform_pressure.json"),"generated_case_manifest_sha256":sha(manifest)},"maximum_errors":maxima,"temporal_behavior":{"hold_rows":hold,"supported_rows":supported,"supported_multiplier_monotonic":"multiplier_monotonic" not in failures,"minimum_multiplier":min(observed),"maximum_multiplier":max(observed),"final_multiplier":observed[-1]},"conservation":{"liquid":"PASS" if "liquid_balance_residual_kg" not in failures else "FAIL","solute":"PASS" if "solute_balance_residual_kg" not in failures else "FAIL"},"failures":sorted(set(failures)),"physical_validation":"NOT_APPLICABLE"}
 tmp=a.output.with_suffix(a.output.suffix+".tmp"); tmp.write_text(json.dumps(out,indent=2,sort_keys=True)+"\\n"); tmp.replace(a.output); print(json.dumps(out,indent=2,sort_keys=True)); return 0 if not failures else 1
if __name__=="__main__": raise SystemExit(main())
