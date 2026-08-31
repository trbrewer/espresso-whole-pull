from __future__ import annotations
import statistics
def summary(xs):
 x=sorted(v for v in xs if v is not None);return {"n":len(x),"min":x[0],"median":statistics.median(x),"max":x[-1],"quantile_semantics":"EQUAL_ROW_DESIGN_SUMMARY_NOT_POPULATION_PROBABILITY"}
def build(w,figmet,vpts):
 coffees={}
 for name in sorted(set(r["coffee"] for r in w)):
  q=[r for r in w if r["coffee"]==name];coffees[name]={"phi_total":summary([r["phi_total"] for r in q]),"phi_connected":summary([r["phi_connected"] for r in q]),"k_m2":summary([r["k_m2"] for r in q])}
 return {"nonfusion":"WADSWORTH_AND_VACA_RETAINED_SEPARATELY","wadsworth":{"support_type":"EMPIRICAL_ROW_SUPPORT","per_coffee":coffees,"union":{"phi_total":summary([r["phi_total"] for r in w]),"phi_connected":summary([r["phi_connected"] for r in w]),"k_m2":summary([r["k_m2"] for r in w])},"rows":w},"vaca_figure12":{"support_type":"SOURCE_OPERATOR_PREDICTION",**figmet},"vaca_table_c1":{"support_type":"EMPIRICAL_ROW_SUPPORT","epsilon_0":summary([r["epsilon_0"] for r in vpts]),"k_published_mu_m2":summary([r["k_published_mu_m2"] for r in vpts]),"k_ewp_reference_mu_m2":summary([r["k_ewp_reference_mu_m2"] for r in vpts]),"rows":vpts},"vaca_eq11":{"support_type":"CONTEXTUAL_BOUND","status":"POST_FIT_RECONSTRUCTION_NOT_INDEPENDENT_DIRECT_DARCY_EVIDENCE","refit_performed":False}}
