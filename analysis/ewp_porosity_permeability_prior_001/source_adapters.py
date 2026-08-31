from __future__ import annotations
import csv, math
from pathlib import Path

def rows(p):
    with Path(p).open(newline="") as f:return list(csv.DictReader(f))
def wadsworth(root:Path):
    out=[]
    for r in rows(root/"puckworks/data/wadsworth2026/wadsworth2026_table1_full.csv"):
        out.append({"lineage_id":"WADSWORTH_TABLE1_XCT_LBFLOW_UNTAMPED","coffee":r["coffee"],"setting":int(r["G"]),
          "phi_total":float(r["phi_T_total"]) if r["phi_T_total"] else None,"phi_connected":float(r["phi_p_connected"]) if r["phi_p_connected"] else None,
          "s_total_per_m":float(r["s_total_per_m"]) if r["s_total_per_m"] else None,"s_connected_per_m":float(r["s_p_connected_per_m"]) if r["s_p_connected_per_m"] else None,
          "k_m2":float(r["k_m2"]) if r["k_m2"] else None,"k_uncertainty_reported_m2":float(r["k_err_m2"]) if r["k_err_m2"] else None,
          "uncertainty_semantics":"REPORTED_MAGNITUDE_CONFIDENCE_LEVEL_NOT_STATED"})
    return out
def vaca(root:Path, ewp_mu:float):
    base=root/"puckworks/data/vacaguerra2023a"
    fig=rows(base/"Figure_12_Calculated_versus_experimental_dry_bed_porosity_validation_experiments.csv")
    y=[float(r["measured_dry_bed_porosity"]) for r in fig]; f=[float(r["calculated_dry_bed_porosity"]) for r in fig]; ym=sum(y)/len(y)
    ss=sum((a-b)**2 for a,b in zip(y,f)); metrics={"n":len(y),"r_squared":1-ss/sum((a-ym)**2 for a in y),"rmse":math.sqrt(ss/len(y)),"devices":sorted(set(r["series"] for r in fig)),"contains_direct_permeability":False}
    mu=3.5e-3; area=math.pi*(0.059/2)**2; L0=.0255; pts=[]
    for i,r in enumerate(rows(base/"Table_C1_Extraction_conditions_from_permeability_experiments.csv"),1):
        q=float(r["Q_ml_per_s"])*1e-6; dp=float(r["DeltaP_bar"])*1e5; L=L0-float(r["delta_L_mm"])*1e-3
        k=q*mu*L/(area*dp)
        pts.append({"row_id":f"VACA_C1_{i:02d}","lineage_id":"VACA_TABLE_C1_DARCY_OPERATING_POINTS","distribution":r["Distribution"],"dose_g":float(r["Dosage_g"]),"epsilon_0":float(r["epsilon_0"]),"delta_p_bar":float(r["DeltaP_bar"]),"q_ml_s":float(r["Q_ml_per_s"]),"length_m":L,"area_m2":area,"k_published_mu_m2":k,"k_ewp_reference_mu_m2":k*ewp_mu/mu,"published_mu_pa_s":mu,"ewp_mu_pa_s":ewp_mu,"limitation":"UNPUBLISHED_PUMP_CURVE"})
    return fig,metrics,pts
