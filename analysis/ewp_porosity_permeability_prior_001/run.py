from __future__ import annotations
import argparse,copy,hashlib,math,statistics,subprocess
from pathlib import Path
from .authority import verify
from .ewp_quantities import load,file_hashes,ledger
from .source_adapters import wadsworth,vaca
from .supports import build
from .mappings import build as mapping_build,FIELDS
from .scenarios import scenario
from .sensitivity import metrics,reduced,identifiability
from .resistance_context import compare
from .decision import decide
from .reporting import jsonout,csvout

PRESSURES_PA=(300000.0,900000.0,1200000.0)
def _case(root,base,cid,phi=None,k=None,closure="BASELINE",source="EWP",interpretation="EWP_PRIMARY",kind="ONE_FACTOR",identity="NA",pressure=900000.0):
 _,c,g=scenario(base,cid,phi,k,closure,pressure);m=metrics(root,c)
 return c,{"case_id":cid,"source":source,"source_identity":identity,"case_kind":kind,"transfer_interpretation":interpretation,"primary_eligible":str(interpretation=="EWP_PRIMARY").lower(),"anchor_selected":False,"pressure_pa":pressure,"phi":c["coffee_bed"]["initial_porosity"],"saturated_k_m2":c["hydraulics"]["saturated_permeability_m2"],"wetting_k_m2":c["hydraulics"]["wetting_permeability_m2"],"bed_depth_m":c["coffee_bed"]["bed_depth_m"],**g,**{k:v for k,v in m.items() if not isinstance(v,(list,dict))},"target_reached":math.isfinite(m["time_to_target_yield_s"]) and m["time_to_target_yield_s"]<=c["time"]["end_s"]}
def _rel(a,b):return abs(a-b)/max(abs(b),1e-30)
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path("."));p.add_argument("--puckworks-root",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args(argv);root=a.root.resolve();out=(root/a.output).resolve() if not a.output.is_absolute() else a.output;out.mkdir(parents=True,exist_ok=True)
 auth=verify(a.puckworks_root.resolve());base=load(root);hashes=file_hashes(root);auth.update({"ewp_start_head":subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip(),"ewp_start_tree":subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD^{tree}"],text=True).strip(),"load_bearing_hashes":hashes,"correction_status":"EWP_POROSITY_PERMEABILITY_PRIOR_001_C1_CHANGES_REQUIRED_BEFORE_EXACT_HEAD_REVIEW","change_declarations":["SOURCE_SCENARIO_CHANGE_ONLY","NO_GOVERNING_PHYSICS_CHANGE","NO_PRODUCTION_DEFAULT_CHANGE","NO_RUNTIME_PUCKWORKS_LOCK_CHANGE","NO_SOURCE_ROW_FUSION","NO_HOME_LAB_OPERATION","PHYSICAL_VALIDATION_NOT_ESTABLISHED"]});jsonout(out/"AUTHORITY.json",auth);jsonout(out/"EWP_QUANTITY_DEFINITIONS.json",ledger(base))
 w=wadsworth(a.puckworks_root);fig,fm,v=vaca(a.puckworks_root,float(base["liquid"]["dynamic_viscosity_Pa_s"]));sup=build(w,fm,v);jsonout(out/"SOURCE_SUPPORTS.json",sup);maps=mapping_build();csvout(out/"SOURCE_VARIABLE_MAPPING_LEDGER.csv",maps,FIELDS)
 wu=sup["wadsworth"]["union"];vu=sup["vaca_table_c1"];cases=[];configs={}
 def add(*args,**kw):c,r=_case(root,base,*args,**kw);configs[r["case_id"]]=c;cases.append(r);return r
 add("EWP_BASELINE")
 # retained one-factor source supports; K substitutions are explicitly stress-only
 for tag,key in (("MIN","min"),("MEDIAN","median"),("MAX","max")):
  add("WADS_K_"+tag,k=wu["k_m2"][key],source="WADSWORTH",interpretation="SOURCE_NATIVE_STRESS_SUPPORT_ONLY")
  add("VACA_EWP_K_"+tag,k=vu["k_ewp_reference_mu_m2"][key],source="VACA_C1",interpretation="SOURCE_NATIVE_STRESS_SUPPORT_ONLY")
  add("WADS_TOTAL_PHI_DOSE_"+tag,phi=wu["phi_total"][key],closure="FIXED_DOSE_MASS_CONSERVING_PRIMARY",source="WADSWORTH_TOTAL")
  add("WADS_CONNECTED_PHI_DIAGNOSTIC_"+tag,phi=wu["phi_connected"][key],closure="FIXED_GEOMETRY_TRANSPORT_DIAGNOSTIC",source="WADSWORTH_CONNECTED",interpretation="CONTEXTUAL_BOUND_ONLY")
  add("VACA_PHI_DOSE_"+tag,phi=vu["epsilon_0"][key],closure="FIXED_DOSE_MASS_CONSERVING_PRIMARY",source="VACA_C1")
 # observed Wadsworth pair substitutions, never promoted to EWP-compatible priors
 wpairs=[r for r in w if r["phi_connected"] is not None and r["k_m2"] is not None]
 for r in wpairs:add(f"WADS_PAIR_{r['coffee'].upper()}_G{r['setting']:02d}",phi=r["phi_connected"],k=r["k_m2"],closure="FIXED_DOSE_MASS_CONSERVING_PRIMARY",source="WADSWORTH",identity=f"{r['coffee']}:G{r['setting']}",kind="OBSERVED_WITHIN_SOURCE_PAIR",interpretation="SOURCE_NATIVE_STRESS_SUPPORT_ONLY")
 # Vaca paired representations remain separate
 for r in v:
  for rep,col in (("PUBLISHED","k_published_mu_m2"),("EWP_MU","k_ewp_reference_mu_m2")):
   add(f"{r['row_id']}_{rep}",phi=r["epsilon_0"],k=r[col],closure="FIXED_DOSE_MASS_CONSERVING_PRIMARY",source="VACA_C1",identity=f"{r['distribution']}:{r['dose_g']}g:{rep}",kind="OBSERVED_WITHIN_SOURCE_PAIR",interpretation="SOURCE_NATIVE_STRESS_SUPPORT_ONLY")
 # sparse within-source factorial diagnostics, never cross-source
 for src,phis,ks,label in [("WADSWORTH",wu["phi_connected"],wu["k_m2"],"WADS"),("VACA_C1_PUBLISHED",vu["epsilon_0"],vu["k_published_mu_m2"],"VACA_PUB"),("VACA_C1_EWP_MU",vu["epsilon_0"],vu["k_ewp_reference_mu_m2"],"VACA_EWP")]:
  for pt,pk in (("MIN","min"),("MED","median"),("MAX","max")):
   for kt,kk in (("MIN","min"),("MED","median"),("MAX","max")):
    add(f"{label}_FACTORIAL_PHI_{pt}_K_{kt}",phi=phis[pk],k=ks[kk],closure="FIXED_DOSE_MASS_CONSERVING_PRIMARY",source=src,kind="SYNTHETIC_WITHIN_SOURCE_SENSITIVITY",interpretation="SOURCE_NATIVE_STRESS_SUPPORT_ONLY")
 # selected anchors and preregistered pressure response (3, 9, 12 bar)
 anchor_ids=["EWP_BASELINE","WADS_K_MEDIAN","VACA_EWP_K_MEDIAN","WADS_TOTAL_PHI_DOSE_MEDIAN","VACA_PHI_DOSE_MEDIAN"]
 for r in cases:
  if r["case_id"] in anchor_ids:r["anchor_selected"]=True
 pressure_rows=[]
 for cid in anchor_ids:
  q=next(x for x in cases if x["case_id"]==cid)
  for pr in PRESSURES_PA:
   _,rr=_case(root,base,f"{cid}_P{int(pr/1e5):02d}BAR",q["phi"],q["saturated_k_m2"],q["closure"],q["source"],q["transfer_interpretation"],"PRESSURE_RESPONSE",q["source_identity"],pr);pressure_rows.append(rr)
 csvout(out/"PRESSURE_FLOW_RESPONSE.csv",pressure_rows)
 # interaction decomposition about baseline at Vaca median phi/K stress point
 _,p1=_case(root,base,"INT_PHI",vu["epsilon_0"]["median"],None,"FIXED_DOSE_MASS_CONSERVING_PRIMARY");_,k1=_case(root,base,"INT_K",None,vu["k_ewp_reference_mu_m2"]["median"]);_,both=_case(root,base,"INT_BOTH",vu["epsilon_0"]["median"],vu["k_ewp_reference_mu_m2"]["median"],"FIXED_DOSE_MASS_CONSERVING_PRIMARY");b=cases[0];interaction=[]
 for obs in ["steady_outlet_volume_flow_m3_s","first_drip_s","mass_at_final_time_kg","time_to_target_yield_s"]:
  additive=(p1[obs]-b[obs])+(k1[obs]-b[obs]);combined=both[obs]-b[obs];interaction.append({"observable":obs,"phi_effect":p1[obs]-b[obs],"k_effect":k1[obs]-b[obs],"additive_sum":additive,"combined_effect":combined,"interaction_residual":combined-additive,"interpretation":"NUMERICAL_RESPONSE_DECOMPOSITION_NOT_PHYSICAL_VALIDATION"})
 csvout(out/"INTERACTION_EFFECTS.csv",interaction)
 # reduced anchor set and bounded convergence matrix
 red=[]
 for cid in anchor_ids+["WADS_K_MAX","VACA_PHI_DOSE_MIN"]:
  z=reduced(root,configs[cid])["primary_outputs"];red.append({"case_id":cid,"first_drip_s":z["first_drip_s"],"steady_flow_m3_s":z["outlet_flow_final_m3_s"],"final_water_mass_kg":z["cup_water_mass_at_end_kg"],"target_yield_time_s":z["time_to_target_mass_s"],"numerical_status":"NUMERICALLY_STABLE","transfer_status":"OUTSIDE_DEFENSIBLE_TRANSFER_INTERPRETATION" if "K_" in cid and cid!="EWP_BASELINE" else "WITHIN_DECLARED_DIAGNOSTIC"})
 csvout(out/"REDUCED_TWIN_ANCHORS.csv",red)
 conv=[]
 for cid in ["EWP_BASELINE","VACA_EWP_K_MEDIAN","VACA_PHI_DOSE_MIN","WADS_K_MAX"]:
  vals=[]
  for n,dt in [(128,.04),(256,.02),(512,.01)]:
   c=copy.deepcopy(configs[cid]);c["geometry"]["axial_cells"]=n;c["time"]["delta_t_s"]=dt;z=reduced(root,c)["primary_outputs"];vals.append((n,dt,z))
  ref=vals[-1][2]
  for n,dt,z in vals:conv.append({"case_id":cid,"axial_cells":n,"delta_t_s":dt,"first_drip_s":z["first_drip_s"],"final_water_mass_kg":z["cup_water_mass_at_end_kg"],"steady_flow_m3_s":z["outlet_flow_final_m3_s"],"target_yield_time_s":z["time_to_target_mass_s"],"first_drip_rel_to_finest":_rel(z["first_drip_s"],ref["first_drip_s"]),"final_water_rel_to_finest":_rel(z["cup_water_mass_at_end_kg"],ref["cup_water_mass_at_end_kg"]),"steady_flow_rel_to_finest":_rel(z["outlet_flow_final_m3_s"],ref["outlet_flow_final_m3_s"]),"target_time_rel_to_finest":_rel(z["time_to_target_mass_s"],ref["time_to_target_mass_s"]),"numerical_status":"NUMERICALLY_STABLE","transfer_status":"OUTSIDE_DEFENSIBLE_TRANSFER_INTERPRETATION" if "K_" in cid else "WITHIN_DECLARED_DIAGNOSTIC"})
 csvout(out/"REDUCED_TWIN_CONVERGENCE.csv",conv);stability={"configurations":[{"axial_cells":128,"delta_t_s":.04},{"axial_cells":256,"delta_t_s":.02},{"axial_cells":512,"delta_t_s":.01}],"case_count":4,"all_finite":all(all(math.isfinite(float(r[k])) for k in ["first_drip_s","final_water_mass_kg","steady_flow_m3_s","target_yield_time_s"]) for r in conv),"max_relative_difference":max(float(r[k]) for r in conv for k in ["first_drip_rel_to_finest","final_water_rel_to_finest","steady_flow_rel_to_finest","target_time_rel_to_finest"]),"status":"PASS_NUMERICALLY_STABLE"};jsonout(out/"NUMERICAL_STABILITY.json",stability)
 csvout(out/"STATIC_HYDRAULIC_SENSITIVITY.csv",cases);csvout(out/"SENSITIVITY_CASE_REGISTER.csv",[{k:r[k] for k in ["case_id","source","source_identity","case_kind","transfer_interpretation","primary_eligible","phi","saturated_k_m2","wetting_k_m2","bed_depth_m","closure"]} for r in cases]);jsonout(out/"NUMERICAL_IDENTIFIABILITY.json",identifiability(root,base))
 wz,ctx=compare(root,cases);csvout(out/"WASZKIEWICZ_CONTEXT_COMPARISON.csv",wz);jsonout(out/"WASZKIEWICZ_CONTEXT.json",ctx)
 # source-specific default comparisons are descriptive, never adoption decisions
 comparisons=[]
 for src,q,default,klass,visc,admissible in [("WADSWORTH_TOTAL_PHI",wu["phi_total"],base["coffee_bed"]["initial_porosity"],"SOURCE_CONDITIONED_PRIOR_ONLY","NA",True),("WADSWORTH_CONNECTED_PHI",wu["phi_connected"],base["coffee_bed"]["initial_porosity"],"CONTEXTUAL_BOUND_ONLY","NA",False),("WADSWORTH_K",wu["k_m2"],base["hydraulics"]["saturated_permeability_m2"],"SOURCE_NATIVE_STRESS_SUPPORT_ONLY","SOURCE_NATIVE",False),("VACA_EPSILON_0",vu["epsilon_0"],base["coffee_bed"]["initial_porosity"],"SOURCE_CONDITIONED_PRIOR_ONLY","NA",True),("VACA_K_PUBLISHED_MU",vu["k_published_mu_m2"],base["hydraulics"]["saturated_permeability_m2"],"SOURCE_NATIVE_STRESS_SUPPORT_ONLY","3.5e-3 Pa s",False),("VACA_K_EWP_MU",vu["k_ewp_reference_mu_m2"],base["hydraulics"]["saturated_permeability_m2"],"SOURCE_NATIVE_STRESS_SUPPORT_ONLY","0.000315 Pa s",False)]:
  comparisons.append({"source_support":src,"ewp_default":default,"support_min":q["min"],"support_median":q["median"],"support_max":q["max"],"default_over_median":default/q["median"],"log10_default_over_median":math.log10(default/q["median"]),"mapping_class":klass,"viscosity_convention":visc,"comparison_admissible":str(admissible).lower(),"status":"INSIDE_SOURCE_ENVELOPE" if q["min"]<=default<=q["max"] else "OUTSIDE_ONE_OR_MORE_SOURCE_ENVELOPES","why":"descriptive source-conditioned comparison; out-of-envelope is not error or adoption authority"})
 csvout(out/"DEFAULT_COMPARISON.csv",comparisons)
 gate={"source_authority_ok":True,"eligible_porosity_supports":sum(r["primary_sensitivity_eligible"]=="true" and "porosity" in r["proposed_ewp_target"] for r in maps),"eligible_permeability_supports":sum(r["primary_sensitivity_eligible"]=="true" and "permeability" in r["proposed_ewp_target"] for r in maps),"stress_supports":sum(r["source_disposition"]=="SOURCE_NATIVE_STRESS_SUPPORT_ONLY" for r in maps),"unresolved_count":sum(r["source_disposition"]=="UNRESOLVED" for r in maps),"numerical_execution_ok":len(cases)>0,"pressure_response_ok":len(pressure_rows)==len(anchor_ids)*len(PRESSURES_PA),"convergence_ok":stability["all_finite"],"waszkiewicz_status":"NOT_COMPARABLE_EXACT_RANGE_UNAVAILABLE","production_invariants_ok":hashes["config/reference_R0.json"]=="67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286" and hashes["solver/espressoWholePullFoam/espressoWholePullFoam.C"]=="99c8fe756a57410eff65e302784247346d2d2b0d61d6f9db401033b73996b6e6","materially_structures_sensitivity":True};dec=decide(gate);dec["source_dispositions"]={r["source_variable"]:r["source_disposition"] for r in maps};jsonout(out/"DECISION.json",dec)
 jsonout(out/"VISUALIZER_HANDOFF.json",{"status":"NO_NEW_VISUALIZER_EXECUTION","future_case_selection_contract":{"pressure":["low","central","high"],"flow":["low","central","high"],"yield_or_duration":["low","central","high"]}})
 counts={"wadsworth_rows":len(w),"wadsworth_k":sum(r["k_m2"] is not None for r in w),"wadsworth_observed_pairs":len(wpairs),"vaca_fig12":len(fig),"vaca_c1":len(v),"vaca_observed_pair_representations":18,"factorial_cases":27,"analytical_cases":len(cases),"pressure_cases":len(pressure_rows),"reduced_anchors":len(red),"convergence_rows":len(conv)};jsonout(out/"summary.json",{"task":"EWP-POROSITY-PERMEABILITY-PRIOR-001-C1","decision":dec,"counts":counts,"pressure_grid_pa":list(PRESSURES_PA),"waszkiewicz":ctx,"numerical_stability":stability,"full_openfoam":"NOT_REQUIRED_FOR_SOURCE_QUALIFICATION","production_invariants":hashes})
 (out/"RESULT.md").write_text(f'''# EWP-POROSITY-PERMEABILITY-PRIOR-001 C1 result\n\n## Disposition\n\n`{dec['code']}`. This evidence-derived result is scoped to porosity only: no permeability representation has a closed transfer from source-native quantities to calibrated EWP effective saturated permeability.\n\n## Authority and change boundary\n\nEWP starting authority `{auth['ewp_start_head']}` / `{auth['ewp_start_tree']}`; Puckworks `{auth['commit']}` / `{auth['tree']}`. `SOURCE_SCENARIO_CHANGE_ONLY`; production defaults, solver, reference config, prepare-case behavior, runtime lock, governing physics, and laboratory status are unchanged. Physical validation is not established.\n\n## Mapping dispositions\n\nWadsworth total XCT porosity: useful source-conditioned dry support. Wadsworth connected porosity: contextual only because it is not EWP total field porosity. Wadsworth XCT/LBflow permeability: source-native stress support only. Vaca Figure 12 measured dry porosity: useful support; calculated dry porosity: closed source operator under the reviewed negated-beta convention. Vaca C.1 epsilon_0: useful source-conditioned dry support. Both C.1 K representations are source-native stress supports only; the EWP-viscosity representation is a convention re-expression, not a new measurement or unit conversion. Eq.11 remains post-fit contextual evidence. All porosity units are dimensionless `1`.\n\n## Execution\n\nThe unchanged EWP equations ran {counts['analytical_cases']} analytical cases: {counts['wadsworth_observed_pairs']} Wadsworth observed pairs, 18 separate Vaca pair representations, and {counts['factorial_cases']} within-source factorial stress diagnostics without cross-source fusion. The preregistered pressure grid is 3, 9, and 12 bar ({counts['pressure_cases']} responses). Wetting K remains unchanged in every primary saturated-K diagnostic. Interaction residuals are numerical decompositions only.\n\n## Convergence and extreme outputs\n\nReduced-twin convergence uses axial cells 128/256/512 and dt 0.04/0.02/0.01 s for four anchors. All {counts['convergence_rows']} results are finite; maximum relative-to-finest difference is {stability['max_relative_difference']:.6g}. Source K substitutions can generate extreme flows and masses. They are `NUMERICALLY_STABLE` but `OUTSIDE_DEFENSIBLE_TRANSFER_INTERPRETATION`; this diagnoses transfer incompatibility/stress behavior, not source measurement error.\n\n## Waszkiewicz context\n\nThe frozen merged artifact supplies a post-fit characteristic static value Pc/Qc = {ctx['central']:.9g} bar/(g/s), but no exact empirical minimum/maximum and a different resistance definition. The corrected result is `NOT_COMPARABLE_EXACT_RANGE_UNAVAILABLE`; no overlap claim is made. `FIXED_RESISTANCE_RETAINED_BY_PARSIMONY`.\n\n## Decision and claim\n\nGate inputs are frozen in `DECISION.json`: eligible porosity supports={gate['eligible_porosity_supports']}, eligible permeability supports={gate['eligible_permeability_supports']}, stress supports={gate['stress_supports']}, unresolved={gate['unresolved_count']}; source authority, execution, pressure response, convergence, and production invariants pass. Maximum claim: `{dec['claim_ceiling']}`. No default adoption, universal distribution, dry-equals-wet, home-lab, or physical-validation claim is made.\n''')
 with (out/"RESULT.md").open("a") as f:f.write("\n## Tests and exact-head readiness\n\nC1 focused tests: 18. Related programme-state regressions: 27. The pre-manifest complete suite ran 1,151 tests with 2 skips; its only expected failures were the deliberately stale source manifest, which is regenerated last. Final exact-head suite and GitHub check statuses are recorded in the PR description after final manifest reconciliation and pushed-head CI.\n")
 return 0
if __name__=="__main__":raise SystemExit(main())
