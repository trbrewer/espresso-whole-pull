from __future__ import annotations
import statistics
def summary(xs):
 x=sorted(v for v in xs if v is not None);return {"n":len(x),"min":x[0],"median":statistics.median(x),"max":x[-1],"quantile_semantics":"EQUAL_ROW_DESIGN_SUMMARY_NOT_POPULATION_PROBABILITY"}
ELIGIBLE_SUPPORTS=[
 {"support_id":"WADSWORTH_TOTAL_XCT_POROSITY","source_lineage":"WADSWORTH_TABLE1_XCT_LBFLOW_UNTAMPED","quantity":"initial_porosity","eligible":True},
 {"support_id":"VACA_TABLE_C1_EPSILON_0","source_lineage":"VACA_TABLE_C1_DARCY_OPERATING_POINTS","quantity":"initial_porosity","eligible":True},
]
NONELIGIBLE_SUPPORTS=[
 {"support_id":"WADSWORTH_CONNECTED_XCT_POROSITY","reason":"CONTEXTUAL_BOUND_ONLY"},
 {"support_id":"VACA_FIG12_MEASURED_DRY_POROSITY","reason":"OPERATOR_QUALIFICATION_ONLY"},
 {"support_id":"VACA_FIG12_CALCULATED_DRY_POROSITY","reason":"OPERATOR_QUALIFICATION_ONLY"},
 {"support_id":"WADSWORTH_XCT_LBFLOW_PERMEABILITY","reason":"SOURCE_NATIVE_STRESS_SUPPORT_ONLY"},
 {"support_id":"VACA_C1_DARCY_K_PUBLISHED_VISCOSITY","reason":"SOURCE_NATIVE_STRESS_SUPPORT_ONLY"},
 {"support_id":"VACA_C1_DARCY_K_EWP_VISCOSITY_REEXPRESSION","reason":"SOURCE_NATIVE_STRESS_SUPPORT_ONLY"},
 {"support_id":"VACA_EQ11_POSTFIT_RECONSTRUCTION","reason":"CONTEXTUAL_BOUND_ONLY"},
]
def build(w,figmet,vpts):
 coffees={}
 for name in sorted(set(r["coffee"] for r in w)):
  q=[r for r in w if r["coffee"]==name];coffees[name]={"phi_total":summary([r["phi_total"] for r in q]),"phi_connected":summary([r["phi_connected"] for r in q]),"k_m2":summary([r["k_m2"] for r in q])}
 return {"nonfusion":"WADSWORTH_AND_VACA_RETAINED_SEPARATELY","eligible_porosity_supports":ELIGIBLE_SUPPORTS,"noneligible_supports":NONELIGIBLE_SUPPORTS,"wadsworth":{"support_type":"EMPIRICAL_ROW_SUPPORT","per_coffee":coffees,"union":{"phi_total":summary([r["phi_total"] for r in w]),"phi_connected":summary([r["phi_connected"] for r in w]),"k_m2":summary([r["k_m2"] for r in w])},"rows":w},"vaca_figure12":{"lineage_id":"VACA_FIG12_DRY_POROSITY_OPERATOR","source_file":"puckworks/data/vacaguerra2023a/Figure_12_Calculated_versus_experimental_dry_bed_porosity_validation_experiments.csv","support_type":"OPERATOR_QUALIFICATION_DOMAIN_SUMMARY","decision_role":"OPERATOR_QUALIFICATION_ONLY","operator_closure":"CLOSED_FOR_SOURCE_OPERATOR_QUALIFICATION","ewp_transfer_status":"NOT_A_SEPARATE_PROPAGATED_EWP_SUPPORT","propagated_through_ewp_hydraulics":False,"primary_sensitivity_eligible":False,"eligible_support_contribution":0,"claim_limit":"DRY_POROSITY_OPERATOR_QUALIFICATION_ONLY","dry_state_limitation":"DRY_BED_NOT_WET_OPERATING_PUCK","operator_formula_authority":"VACA_EQ9_EQ10_NEGATED_BETA_DRY_POROSITY","coefficient_authority":"SOURCE_REPORTED_NO_REFIT","negated_beta_convention":True,"refit_performed":False,**figmet},"vaca_table_c1":{"support_type":"EMPIRICAL_ROW_SUPPORT","epsilon_0":summary([r["epsilon_0"] for r in vpts]),"k_published_mu_m2":summary([r["k_published_mu_m2"] for r in vpts]),"k_ewp_reference_mu_m2":summary([r["k_ewp_reference_mu_m2"] for r in vpts]),"rows":vpts},"vaca_eq11":{"support_type":"CONTEXTUAL_BOUND","status":"POST_FIT_RECONSTRUCTION_NOT_INDEPENDENT_DIRECT_DARCY_EVIDENCE","refit_performed":False}}
