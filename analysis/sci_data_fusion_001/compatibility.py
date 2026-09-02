from itertools import combinations
from .vocabulary import LOAD_BEARING_GATES
def independently_eligible(item):
    return (item.get("frozen_role")=="COMMON_CONSTRAINT_CANDIDATE" and item.get("qualified_for_task_role") is True and item.get("rights_permit_analysis") is True and item.get("provenance_complete") is True and item.get("target_exposed") is False and item.get("source_internal_validation") is False and item.get("consumed_comparison_conflict") is False and item.get("ewp_calibration_independent") is True and isinstance(item.get("lineage_id"),str) and bool(item["lineage_id"]) and isinstance(item.get("correlation_group_id"),str) and bool(item["correlation_group_id"]))
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
    blockers=[{"support_id":x["support_id"],"blocker_type":x["frozen_role"],"affected_canonical_component":quantity_id,"exact_authority":x.get("source_artifact_path"),"decision_material":x.get("decision_material") is True,"controls_overall":x.get("decision_material") is True,"terminal_next_action_consequence":x.get("terminal_reason")} for x in candidates if x.get("frozen_role") in {"BLOCKED_AUTHORITY","BLOCKED_SEMANTIC","BLOCKED_RIGHTS"}]
    record["blockers"]=blockers;record["decision_material"]=any(x["decision_material"] for x in blockers)
    if len(eligible)<2 or len(lineages)<2 or len(groups)<2:
        if blockers:result={"BLOCKED_AUTHORITY":"BLOCKED_AUTHORITY","BLOCKED_RIGHTS":"BLOCKED_RIGHTS"}.get(blockers[0]["blocker_type"],"BLOCKED_SEMANTIC")
        else:result="NEGATIVE_NO_COMMON_SUPPORT"
        record.update(component_result=result,compatibility_findings=[]);return record
    pairs=build_pairwise(eligible,contracts);record["compatibility_findings"]=pairs
    if any(row["terminal_compatibility"]!="COMPATIBLE" for row in pairs):
        failed={gate for row in pairs for gate in row["failed_gates"]}
        result="COMPLEMENTARY_SOURCE_CONDITIONED_ONLY" if "population_regime" in failed else ("BLOCKED_SEMANTIC" if any(row["unknown_gates"] for row in pairs) else "NEGATIVE_NO_COMMON_SUPPORT")
        record.update(component_result=result,common_support=None);return record
    if any(item.get("interval") is None for item in eligible):raise ValueError("eligible common support lacks interval")
    lo=max(item["interval"][0] for item in eligible);hi=min(item["interval"][1] for item in eligible)
    if lo>hi:record.update(component_result="CONFLICT_SAME_SCOPE_SUPPORTS",common_support=None,conflicts=[{"support_ids":[item["support_id"] for item in eligible]}]);return record
    result="POSITIVE_COMMON_CONSTRAINT" if baseline["status"]=="AUTHORIZED_BASELINE_AVAILABLE" else "COMMON_SUPPORT_IDENTIFIED_NO_AUTHORIZED_EWP_BASELINE"
    record.update(component_result=result,common_support=[lo,hi],contributing_supports=[{"support_id":item["support_id"],"interval":item["interval"]} for item in eligible]);return record
