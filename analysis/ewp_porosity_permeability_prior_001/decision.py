from . import MAX_CLAIM
def decide(g):
 required=["source_authority_ok","eligible_porosity_supports","eligible_permeability_supports","stress_supports","unresolved_count","numerical_execution_ok","pressure_response_ok","convergence_ok","waszkiewicz_status","production_invariants_ok","materially_structures_sensitivity"]
 if any(k not in g for k in required):raise ValueError("EWP_POROSITY_PERMEABILITY_PRIOR_001_DECISION_INPUT_MISSING")
 blocked=not all(g[k] for k in ["source_authority_ok","numerical_execution_ok","pressure_response_ok","convergence_ok","production_invariants_ok"]) or g["unresolved_count"]>0;p=g["eligible_porosity_supports"]>0;k=g["eligible_permeability_supports"]>0
 if blocked:code,scope="EWP_POROSITY_PERMEABILITY_PRIOR_001_BLOCKED","NONE"
 elif (p or k) and not g["materially_structures_sensitivity"]:code,scope="EWP_POROSITY_PERMEABILITY_PRIOR_001_NULL","NONE"
 elif p and k:code,scope="EWP_POROSITY_PERMEABILITY_PRIOR_001_POSITIVE_POROSITY_AND_PERMEABILITY","POROSITY_AND_PERMEABILITY"
 elif p:code,scope="EWP_POROSITY_PERMEABILITY_PRIOR_001_POSITIVE_POROSITY_ONLY","POROSITY_ONLY"
 elif k:code,scope="EWP_POROSITY_PERMEABILITY_PRIOR_001_POSITIVE_PERMEABILITY_ONLY","PERMEABILITY_ONLY"
 else:code,scope="EWP_POROSITY_PERMEABILITY_PRIOR_001_NEGATIVE","NONE"
 return {"code":code,"scope":scope,"gate_inputs":g,"reason":"Evidence-derived; source-native stress supports do not satisfy positive EWP-compatible gates.","claim_ceiling":MAX_CLAIM,"production_default_action":"RETAIN_UNCHANGED","successor":"EWP-REAL-WORLD-BOUNDARIES-001"}
