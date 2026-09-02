def reduce_overall(components):
    blockers=[c for c in components if c.get("decision_material") is True and c.get("blockers")];conflicts=[c for c in components if c.get("component_result")=="CONFLICT_SAME_SCOPE_SUPPORTS"];positives=[c for c in components if c.get("component_result")=="POSITIVE_COMMON_CONSTRAINT"];common_no_narrow=[c for c in components if c.get("component_result")=="COMMON_SUPPORT_IDENTIFIED_NO_AUTHORIZED_EWP_BASELINE"];narrowed=[c for c in positives if c.get("narrowing",{}).get("quantitative_narrowing_claim") is True];complementary=[c for c in components if c.get("component_result")=="COMPLEMENTARY_SOURCE_CONDITIONED_ONLY"]
    if blockers:code="SCI_DATA_FUSION_001_BLOCKED_DECISION_MATERIAL_SEMANTIC_OR_AUTHORITY"
    elif conflicts:code="SCI_DATA_FUSION_001_CONFLICTING_SAME_SCOPE_COMPONENT_EVIDENCE"
    elif narrowed:code="SCI_DATA_FUSION_001_POSITIVE_AT_LEAST_ONE_COMMON_EWP_CONSTRAINT"
    elif common_no_narrow:code="SCI_DATA_FUSION_001_COMMON_SUPPORT_IDENTIFIED_NO_QUANTITATIVE_EWP_NARROWING"
    elif complementary:code="SCI_DATA_FUSION_001_COMPLEMENTARY_SOURCE_CONDITIONED_SUPPORTS_ONLY"
    else:code="SCI_DATA_FUSION_001_NEGATIVE_NO_COMMON_CROSS_CORPUS_CONSTRAINT"
    return {"disposition":code,"component_results":components,"mixed_outcomes_preserved":True,"decision_material_blocker_count":len(blockers),"conflict_count":len(conflicts),"positive_component_count":len(positives),"quantitatively_narrowed_component_count":len(narrowed)}
