from itertools import combinations
LOAD_BEARING_GATES=("physical_quantity","reference_state","unit_basis","spatial_support","temporal_support","observation_operator","population_regime","lineage","correlation_group","independence_target_exposure","source_internal_role","provenance_rights","ewp_consumer","no_new_inference")
def independently_eligible(item):
    return bool(item.get("frozen_role")=="COMMON_CONSTRAINT_CANDIDATE" and item.get("qualified_support") and not item.get("target_exposed") and not item.get("source_internal_validation") and not item.get("consumed_comparison_conflict") and item.get("provenance_complete") and item.get("rights_permit_analysis") and item.get("lineage_id") and item.get("correlation_group_id"))
def expected_pairs(items):return list(combinations(sorted(item["support_id"] for item in items),2))
def build_pairwise(items,contracts):
    rows=[]
    for left,right in expected_pairs(items):
        key,reverse=f"{left}|{right}",f"{right}|{left}"
        if key in contracts and reverse in contracts and contracts[key]!=contracts[reverse]:raise ValueError(f"asymmetric compatibility contract: {key}")
        gates=contracts.get(key,contracts.get(reverse))
        if gates is None:raise ValueError(f"omitted compatibility pair: {key}")
        if set(gates)!=set(LOAD_BEARING_GATES):raise ValueError(f"incomplete compatibility gates: {key}")
        failed=[name for name,value in gates.items() if value is False];unknown=[name for name,value in gates.items() if value is not True and value is not False]
        rows.append({"left_support_id":left,"right_support_id":right,"gates":gates,"failed_gates":failed,"unknown_gates":unknown,"terminal_compatibility":"COMPATIBLE" if not failed and not unknown else ("INCOMPATIBLE" if failed else "BLOCKED_SEMANTIC")})
    if len(rows)!=len(items)*(len(items)-1)//2:raise ValueError("pairwise comparison count mismatch")
    return rows
def interval_metrics(left,right):
    if len(left)!=2 or len(right)!=2 or left[0]>left[1] or right[0]>right[1]:raise ValueError("invalid closed interval")
    lo,hi=max(left[0],right[0]),min(left[1],right[1]);overlap=max(0.0,hi-lo);union=max(left[1],right[1])-min(left[0],right[0])
    return {"intersection":None if lo>hi else [lo,hi],"overlap_width":overlap,"union_width":union,"overlap_fraction":overlap/union if union else 1.0,"separation_gap":max(0.0,lo-hi)}
def reduce_component(quantity_id,all_items,contracts,baseline):
    candidates=[item for item in all_items if item.get("canonical_quantity_id")==quantity_id];eligible=[item for item in candidates if independently_eligible(item)];lineages={item["lineage_id"] for item in eligible};groups={item["correlation_group_id"] for item in eligible}
    record={"quantity_id":quantity_id,"candidate_count":len(candidates),"eligible_support_count":len(eligible),"eligible_lineage_count":len(lineages),"eligible_correlation_group_count":len(groups),"decision_material":False,"conflicts":[],"blockers":[],"baseline_status":baseline["status"],"narrowing_status":"NOT_EVALUATED"}
    if len(eligible)<2 or len(lineages)<2 or len(groups)<2:record.update(component_result="NEGATIVE_NO_COMMON_SUPPORT",compatibility_findings=[]);return record
    pairs=build_pairwise(eligible,contracts);record["compatibility_findings"]=pairs
    if any(row["terminal_compatibility"]!="COMPATIBLE" for row in pairs):record.update(component_result="COMPLEMENTARY_SOURCE_CONDITIONED_ONLY",common_support=None);return record
    if any(item.get("interval") is None for item in eligible):raise ValueError("eligible common support lacks interval")
    lo=max(item["interval"][0] for item in eligible);hi=min(item["interval"][1] for item in eligible)
    if lo>hi:record.update(component_result="CONFLICT_SAME_SCOPE_SUPPORTS",common_support=None,conflicts=[{"support_ids":[item["support_id"] for item in eligible]}]);return record
    record.update(component_result="POSITIVE_COMMON_CONSTRAINT",common_support=[lo,hi],contributing_supports=[{"support_id":item["support_id"],"interval":item["interval"]} for item in eligible]);return record
