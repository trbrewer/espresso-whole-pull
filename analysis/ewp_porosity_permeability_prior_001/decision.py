from . import MAX_CLAIM
def decide(g):
 required=["source_authority_pass","eligible_porosity_support_ids","eligible_porosity_support_count","eligible_permeability_support_ids","eligible_permeability_support_count","permeability_stress_support_count","qualified_source_operator_count","unresolved_mapping_count","numerical_execution_pass","pressure_response_pass","convergence_pass","waszkiewicz_comparison_status","production_invariants_pass","materially_structures_sensitivity","material_support_count","materiality_rule_id"]
 if any(k not in g for k in required):raise ValueError("EWP_POROSITY_PERMEABILITY_PRIOR_001_DECISION_INPUT_MISSING")
 blocked=not all(g[k] for k in ["source_authority_pass","numerical_execution_pass","pressure_response_pass","convergence_pass","production_invariants_pass"]) or g["unresolved_mapping_count"]>0;p=g["eligible_porosity_support_count"]>0;k=g["eligible_permeability_support_count"]>0
 if blocked:code,scope="EWP_POROSITY_PERMEABILITY_PRIOR_001_BLOCKED","NONE"
 elif (p or k) and not g["materially_structures_sensitivity"]:code,scope="EWP_POROSITY_PERMEABILITY_PRIOR_001_NULL","NONE"
 elif p and k:code,scope="EWP_POROSITY_PERMEABILITY_PRIOR_001_POSITIVE_POROSITY_AND_PERMEABILITY","POROSITY_AND_PERMEABILITY"
 elif p:code,scope="EWP_POROSITY_PERMEABILITY_PRIOR_001_POSITIVE_POROSITY_ONLY","POROSITY_ONLY"
 elif k:code,scope="EWP_POROSITY_PERMEABILITY_PRIOR_001_POSITIVE_PERMEABILITY_ONLY","PERMEABILITY_ONLY"
 else:code,scope="EWP_POROSITY_PERMEABILITY_PRIOR_001_NEGATIVE","NONE"
 return {"code":code,"scope":scope,"gate_inputs":g,"reason":"Evidence-derived; source-native stress supports do not satisfy positive EWP-compatible gates.","claim_ceiling":MAX_CLAIM,"production_default_action":"RETAIN_UNCHANGED","successor":"EWP-REAL-WORLD-BOUNDARIES-001"}
