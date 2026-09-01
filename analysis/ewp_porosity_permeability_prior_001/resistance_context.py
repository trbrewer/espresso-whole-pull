import json
def frozen_context(root):
 p=root/"docs/analysis/xsv_waszkiewicz_dynamic_hyd_001/summary.json";s=json.loads(p.read_text())["source_model"]
 return {"artifact":str(p.relative_to(root)),"quantity_definition":"source post-fit static characteristic pressure divided by characteristic mass flow","unit":"bar/(g/s)","minimum":None,"central":s["static_Pc_bar"]/s["static_Qc_g_s"],"maximum":None,"pressure_scope":"Pc=12.392 bar","grouping_scope":"source post-fit reconstruction","processing_authority":"merged XSV-WASZKIEWICZ-DYNAMIC-HYD-001 summary","limitations":"central value only; exact empirical min/max unavailable; definition differs from EWP Darcy resistance"}
def compare(root,rows):
 c=frozen_context(root);out=[]
 for r in rows:
  if r["case_id"]=="EWP_BASELINE" or r.get("anchor_selected"):
   out.append({"comparison_authority":"MERGED_XSV_WASZKIEWICZ_DYNAMIC_HYD_001","source_case_id":r["case_id"],"ewp_resistance_bar_per_g_per_s":r["R_bar_per_g_per_s"],"waszkiewicz_min":c["minimum"],"waszkiewicz_central":c["central"],"waszkiewicz_max":c["maximum"],"waszkiewicz_unit":c["unit"],"comparison_status":"NOT_COMPARABLE_EXACT_RANGE_UNAVAILABLE","quantity_definition":c["quantity_definition"],"artifact":c["artifact"],"limitations":c["limitations"],"retained_conclusion":"FIXED_RESISTANCE_RETAINED_BY_PARSIMONY"})
 return out,c
