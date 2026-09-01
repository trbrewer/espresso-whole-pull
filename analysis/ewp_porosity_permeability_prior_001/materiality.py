from __future__ import annotations
import math

RULE_ID="EWP_PP_PRIOR_001_POROSITY_MATERIALITY_RULE_V1"
CORE={
 "first_drip_time_s":"first_drip_s",
 "steady_outlet_flow_m3_s":"steady_outlet_volume_flow_m3_s",
 "effective_hydraulic_resistance":"R_Q_pa_s_m3",
 "final_water_mass_kg":"mass_at_final_time_kg",
 "time_to_target_yield_s":"time_to_target_yield_s",
}
SUBSTANTIVE=set(CORE)-{"first_drip_time_s"}

def evaluate_support(support_id,case,baseline,uncertainty,threshold):
 out={"support_id":support_id,"selected_case_id":case["case_id"],"baseline_case_id":baseline["case_id"],"pressure_pa":case["pressure_pa"],"pressure_bar":case["pressure_pa"]/1e5,"geometry_closure":case["closure"],"convergence_uncertainty":uncertainty,"threshold":threshold,"observables":{},"failure_reason":None}
 if case["pressure_pa"]!=900000 or case["closure"]!="FIXED_DOSE_MASS_CONSERVING_PRIMARY":out.update(qualifying_observable_count=0,support_material=False,failure_reason="INELIGIBLE_CASE_DESIGN");return out
 qualifying=[]
 for public,field in CORE.items():
  a,b=case.get(field),baseline.get(field);entry={"source_value":a,"baseline_value":b}
  if public=="time_to_target_yield_s" and case["target_reached"]!=baseline["target_reached"]:entry.update(status="TARGET_REACHABILITY_CHANGED",qualifies=True);qualifying.append(public)
  elif public=="time_to_target_yield_s" and not case["target_reached"] and not baseline["target_reached"]:entry.update(status="NOT_COMPARABLE_TARGET_NOT_REACHED",qualifies=False)
  elif not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (a,b)):out["observables"][public]=dict(entry,status="NONFINITE",qualifies=False);out.update(qualifying_observable_count=0,support_material=False,failure_reason="NONFINITE_RESULT");return out
  elif b==0:entry.update(status="NOT_COMPARABLE_ZERO_BASELINE",qualifies=False)
  else:
   effect=abs(a-b)/abs(b);q=effect>=threshold;entry.update(status="COMPARABLE",relative_effect=effect,qualifies=q)
   if q:qualifying.append(public)
  out["observables"][public]=entry
 material=len(qualifying)>=2 and bool(set(qualifying)&SUBSTANTIVE)
 out.update(qualifying_observable_count=len(qualifying),qualifying_observables=qualifying,support_material=material,failure_reason=None if material else "MATERIALITY_CRITERIA_NOT_MET")
 return out

def compute(cases,convergence,eligible_supports):
 uncertainty=max(float(r[k]) for r in convergence for k in ("first_drip_rel_to_finest","final_water_rel_to_finest","steady_flow_rel_to_finest","target_time_rel_to_finest"))
 floor=.05;multiplier=10.0;threshold=max(floor,multiplier*uncertainty);by={r["case_id"]:r for r in cases};selected={"WADSWORTH_TOTAL_XCT_POROSITY":"WADS_TOTAL_PHI_DOSE_MEDIAN","VACA_TABLE_C1_EPSILON_0":"VACA_PHI_DOSE_MEDIAN"}
 decisions=[evaluate_support(s["support_id"],by[selected[s["support_id"]]],by["EWP_BASELINE"],uncertainty,threshold) for s in eligible_supports]
 count=sum(x["support_material"] for x in decisions)
 return {"rule_id":RULE_ID,"rule_version":1,"rule_authority":"OWNER_FROZEN_TASK_CRITERION_NOT_PUBLICATION_DERIVED","absolute_engineering_floor":floor,"numerical_separation_multiplier":multiplier,"maximum_relative_convergence_uncertainty":uncertainty,"numerical_floor":multiplier*uncertainty,"materiality_threshold":threshold,"reference_pressure_pa":900000,"reference_pressure_bar":9,"geometry_closure":"FIXED_DOSE_MASS_CONSERVING_PRIMARY","baseline_case_id":"EWP_BASELINE","support_decisions":decisions,"eligible_support_count":len(eligible_supports),"material_support_count":count,"materially_structures_sensitivity":count>=1,"all_eligible_supports_material":count==len(eligible_supports),"exclusions":{"permeability_stress_cases":"SOURCE_NATIVE_STRESS_SUPPORT_ONLY","figure_12":"OPERATOR_QUALIFICATION_ONLY_NOT_PROPAGATED","fixed_geometry_cases":"MASS_INCONSISTENT_DIAGNOSTIC","pressure_3_bar_and_12_bar":"CONTEXT_ONLY","min_max_cases":"CONTEXT_ONLY","wadsworth_connected_porosity":"CONTEXTUAL_BOUND_ONLY","waszkiewicz":"CONTEXT_ONLY"},"final_gate_value":count>=1}
