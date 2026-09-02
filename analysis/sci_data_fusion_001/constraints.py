import math
BASELINE_STATUSES={"AUTHORIZED_BASELINE_AVAILABLE","NO_AUTHORIZED_NUMERIC_BASELINE","BASELINE_SEMANTICALLY_INCOMPATIBLE","BASELINE_AUTHORITY_BLOCKED"}
def narrowing(common,baseline_record):
    status=baseline_record["status"]
    if status not in BASELINE_STATUSES:raise ValueError("invalid baseline status")
    if status!="AUTHORIZED_BASELINE_AVAILABLE":return {"baseline_status":status,"quantitative_narrowing_claim":False,"narrowing_status":"UNAVAILABLE"}
    baseline=baseline_record.get("interval")
    if not baseline or common is None:return {"baseline_status":status,"quantitative_narrowing_claim":False,"narrowing_status":"EMPTY_OR_MISSING_COMMON_SUPPORT","empty_common_support":common is None}
    if baseline[0]>baseline[1] or common[0]>common[1]:raise ValueError("invalid interval")
    subset=baseline[0]<=common[0] and common[1]<=baseline[1];strict=subset and common!=baseline;bw=baseline[1]-baseline[0];cw=common[1]-common[0]
    if not subset or cw>bw:return {"baseline_status":status,"baseline_interval":baseline,"common_support_interval":common,"subset":False,"strict_subset":False,"quantitative_narrowing_claim":False,"narrowing_status":"COMMON_SUPPORT_OUTSIDE_OR_WIDER_THAN_BASELINE"}
    log_reduction=math.log10(baseline[1]/baseline[0])-math.log10(common[1]/common[0]) if baseline[0]>0 and common[0]>0 else None
    return {"baseline_status":status,"baseline_interval":baseline,"common_support_interval":common,"subset":subset,"strict_subset":strict,"absolute_width_reduction":bw-cw,"relative_width_reduction":(bw-cw)/bw if bw else None,"log10_width_reduction":log_reduction,"empty_common_support":False,"quantitative_narrowing_claim":strict and cw<bw,"narrowing_status":"STRICT_NARROWING" if strict and cw<bw else "NO_STRICT_NARROWING"}
