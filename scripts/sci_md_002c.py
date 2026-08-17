#!/usr/bin/env python3
"""SCI-MD-002C prospective axial fines-deposition capability screen.

Standalone standard-library implementation. It neither imports nor executes
OpenFOAM, Puckworks, production solver code, or SCI-LC code.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, math, os, resource, subprocess, sys, time, uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/cases/sci_md_002c"
DOC = ROOT / "docs/analysis/sci_md_002c"
OVERLAY = ROOT / "validation/cases/val_corpus_001/results/VAL_CORPUS_001_OVERLAYS_V3.json"
LANE = DOC / "PARALLEL_LANE_DECLARATION.json"
REFS = OUT / "SCI_MD_002C_PUCKWORKS_REFERENCE_RECORD.json"
FEAS = OUT / "SCI_MD_002C_FEASIBILITY_BOUNDS.json"
TASK = "SCI-MD-002C"
LANE_ID = "EWP-PAR-SCI-MD-002C"
BRANCH = "research/sci-md-002c-axial-fines-deposition"
TOKEN = "SCI_MD_002C_ADJUDICATIVE_EXECUTION_AUTHORIZED"
OWNER_ROLE = "HUMAN_REPOSITORY_OWNER"
EXTERNAL_NAMESPACE = "SCI_MD_002C_EXTERNAL_BUNDLE"
PUCK_COMMIT = "fc61c4670ec7bf801e40bb391aab16048b8da26b"
PUCK_TREE = "1d553e44ee2f7480a5df521560801b478618cc84"
OVERLAY_SHA = "e69d2b7b0f0ee6945013a0b185da21803d404270a34f1c9d26aed6ecda370c0e"
PRESSURES = (5, 9, 11)
WINDOW = (100, 899)
MU, RHO, AREA, H0, DOSE, SOLID_RHO = 0.000315, 965.0, 0.002463008640414398, 0.01, 0.0185, 1200.0
HARD_CAP = 2500
MASS_ABS_TOL = 2e-12
FLOAT_REL_TOL = 2e-12
RECORD_SCHEMA = "ewp.sci_md_002c.case_record.v1"
TERMINAL_PRESSURES = {5: 450096.2, 9: 873024.9, 11: 1041717.4}
TERMINAL_FLOWS = {5: 0.002056292, 9: 0.001827218, 11: 0.001777572}
WINDOW_END_PRESSURES = {5: 450428.3, 9: 870708.2, 11: 1041755.1}
PARTICLE_VELOCITY_RATIO = 1.0
PUCK_FILES = {
    "docs/cards/fasano2000_partI.md": "21871394fe8839dcdb388e3419eab3ca37599a9f8223515af8f3cceea0ed5586",
    "puckworks/models/fasano2000_partI/fines_migration.py": "f03149bfff23ab9ee227aa21e3cf35018a145924d84f90274b7d5720793857af",
    "puckworks/data/fasano2000_partI/PROVENANCE.md": "d9c29a9b89e520249f9fb08990b9e31199191d9a037da11d42eb3957891056b3",
    "puckworks/data/fasano2000_partI/fig8_1_discharge_vs_pressure.csv": "8951a2e5bc115527cb980890c6fdfdb475ee4f3039edc1288a0e2753b35c8ddd",
    "puckworks/data/fasano2000_partI/fig8_4_direct_inverse.csv": "e9764036939d86f21e4ea60863b025737bc24f10b944d721685f7a55de92a0d8",
    "puckworks/data/fasano2000_partI/fig8_6_asymptotic_q_vs_p0.csv": "cabef7918b139832317da106a6d4f316b3a43b53b8b67313fbc621d72a6f980b",
    "puckworks/data/fasano2000_partI/fig8_7_thresholds.csv": "09da1d58601028cc09e6706db922f91cc71bffeae609181c5181ab3c45d6abb9",
    "LICENSE": "f49d360941a0dc87338f518098324b649a456b60c58a4044520ea6cd9d415ada",
}
PILOT_IDS = (
    "A0-ZERO-FINES", "A0-MASS-CONSERVATION", "A0-TRANSPORT-BASE", "A0-TRANSPORT-REFINED",
    "C0-SOURCE-P5-NOFINES", "C0-SOURCE-P11-NOFINES", "C1-FASANO-STRUCTURAL", "R1-SYNTH-P7-BASE",
)

def utc() -> str: return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def canonical(x: Any) -> str: return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
def sha(path: Path | str) -> str: return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def hash_obj(x: Any) -> str: return hashlib.sha256(canonical(x).encode()).hexdigest()
def git(*args: str) -> str: return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
def identity() -> dict[str, str]: return {"head": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}")}

def safe_bundle(path: Path | str) -> Path:
    p = Path(path).absolute()
    resolved = p.resolve(strict=False)
    if resolved == ROOT or ROOT in resolved.parents: raise ValueError("BUNDLE_MUST_BE_OUTSIDE_GIT")
    if "sci_md_002c" not in str(resolved).lower(): raise ValueError("BUNDLE_NAMESPACE_MISMATCH")
    for part in (p, *p.parents):
        if part.exists() and part.is_symlink(): raise ValueError("BUNDLE_SYMLINK_COMPONENT")
    return resolved

def load_histories(path: Path = OVERLAY, expected_hash: str = OVERLAY_SHA) -> dict[int, list[dict[str, float]]]:
    if sha(path) != expected_hash: raise ValueError("SOURCE_OVERLAY_HASH_MISMATCH")
    obj = json.loads(path.read_text())
    expected_units = {"flow":"g/s","mass":"g","pressure":"bar","solver_time":"s","source_time":"s","wetting_front":"mm"}
    if obj.get("units") != expected_units: raise ValueError("SOURCE_OVERLAY_UNITS_INVALID")
    result = {}
    for p in PRESSURES:
        raw = obj.get("overlays", {}).get(f"R1-WASZ-{p}-DARCY-STATIC-MEASURED")
        if not isinstance(raw, list) or len(raw) != 999: raise ValueError(f"SOURCE_HISTORY_MISSING_{p}")
        rows, last = [], -math.inf
        for i, r in enumerate(raw):
            if not isinstance(r, list) or len(r) != 8 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in r):
                raise ValueError(f"SOURCE_ROW_INVALID_{p}_{i}")
            st, tt, op, rp, of, rf, om, rm = map(float, r)
            if st <= last or abs(tt-st-3.0) > 1e-9 or op < 0 or rp < 0: raise ValueError(f"SOURCE_SEMANTICS_INVALID_{p}_{i}")
            rows.append({"source_time_s":st,"solver_time_s":tt,"observed_pressure_pa":op*1e5,"reference_model_pressure_pa":rp*1e5,
                         "observed_flow_kg_s":of*1e-3,"reference_model_flow_kg_s":rf*1e-3,"observed_mass_kg":om*1e-3,"reference_model_mass_kg":rm*1e-3})
            last = st
        if abs(rows[-1]["observed_pressure_pa"]-TERMINAL_PRESSURES[p]) > 1e-7 or abs(rows[-1]["observed_flow_kg_s"]-TERMINAL_FLOWS[p]) > 1e-12:
            raise ValueError(f"SOURCE_TERMINAL_IDENTITY_INVALID_{p}")
        result[p] = rows[WINDOW[0]:WINDOW[1]+1]
    if any(len(v) != 800 or v[0]["source_time_s"] != 10.01001 or v[-1]["source_time_s"] != 89.98999 for v in result.values()):
        raise ValueError("SATURATED_WINDOW_IDENTITY_INVALID")
    return result

def hydraulic_anchor() -> float:
    # Accepted convention uses the full-overlay terminal observed P9 point.
    q = TERMINAL_FLOWS[9] / RHO
    return TERMINAL_PRESSURES[9] / q

def feasibility_bounds() -> dict[str, Any]:
    rb = hydraulic_anchor()
    histories=load_histories(); endpoint={p:histories[p][-1]["observed_pressure_pa"] for p in PRESSURES}
    if endpoint != WINDOW_END_PRESSURES: raise ValueError("WINDOW_END_PRESSURE_IDENTITY_INVALID")
    def rc9_required(rc5): return endpoint[9]/endpoint[5]*(rb+rc5)-rb
    def rc11_required(rc9): return endpoint[11]/endpoint[9]*(rb+rc9)-rb
    required9=rc9_required(0.0);required11=rc11_required(required9)
    regions=[]
    for ff in (0.02,0.06,0.10):
      for mf in (0.25,0.75):
       inventory=DOSE*ff*mf
       for eta in (.5,1.0):
        for alpha in (1e12,1e13):
         max_deposit=inventory*eta;rcmax=MU*alpha*max_deposit/AREA**2
         joint=rcmax>=required9 and rcmax>=required11
         regions.append({"fines_mass_fraction":ff,"mobilizable_fraction":mf,"retention_fraction":eta,
                         "max_inventory_kg":inventory,"max_depositable_mass_kg":max_deposit,
                         "specific_cake_resistance_m_kg":alpha,"retention_adjusted_max_resistance_pa_s_m3":rcmax,
                         "required_Rc9_given_Rc5_zero_pa_s_m3":required9,"required_Rc11_given_minimum_Rc9_pa_s_m3":required11,
                         "joint_ordering_feasible":joint,"classification":"POTENTIALLY_FEASIBLE" if joint else "CLEARLY_INVENTORY_IMPOSSIBLE"})
    return {"schema_version":"ewp.sci_md_002c.feasibility.v2","pressure_and_flow_role":"exact selected-window endpoint observed pressures",
            "clean_bed_convention":"one observed P9 terminal-flow hydraulic scale transferred unchanged","clean_bed_resistance_pa_s_m3":rb,
            "window_end_observed_pressure_pa":{str(k):v for k,v in endpoint.items()},
            "ordering_equations":{"Rc9_required(Rc5)":"(P9/P5)*(Rb+Rc5)-Rb","Rc11_required(Rc9)":"(P11/P9)*(Rb+Rc9)-Rb"},
            "optimistic_joint_bounds":{"assumed_Rc5_pa_s_m3":0.0,"required_Rc9_pa_s_m3":required9,"required_Rc11_pa_s_m3":required11,
              "interpretation":"upper bound assumes complete release, transport, and retention-adjusted available deposition by reporting time"},
            "geometry":{"area_m2":AREA,"dose_kg":DOSE,"solid_density_kg_m3":SOLID_RHO,"viscosity_pa_s":MU},
            "identity":"Rc=mu*alpha_c*m_dep/A^2; h=m_dep/(rho_s*(1-epsilon_c)*A)","regions":regions,
            "disposition":"POTENTIALLY_FEASIBLE_ONLY_WITH_SYNTHETIC_CLOSURE_BOUNDS"}

@dataclass(frozen=True)
class Case:
    case_id: str; arm: str; execution_phase: str; evidence_role: str; pressure_identity: str
    fines_fraction: float; mobilizable_fraction: float; release_rate_s: float; release_exponent: float
    retention_fraction: float; layer_porosity: float; specific_cake_resistance_m_kg: float; particle_velocity_ratio: float
    axial_cells: int; temporal_substeps: int; resolution: str; pilot_eligible: bool; adjudicative: bool
    control_id: str | None; refinement_id: str | None; cross_pressure_peer_ids: tuple[str,...]
    retention_peer_ids: tuple[str,...]; closure_peer_ids: tuple[str,...]; source_window_identity: str = "SOURCE_ROWS_100_899_INCLUSIVE"
    output_schema: str = RECORD_SCHEMA

def matrix_rows() -> list[dict[str, Any]]:
    rows=[]
    def add(*a, **kw): rows.append(asdict(Case(*a, **kw)))
    for cid in PILOT_IDS[:4]:
        res="REFINED" if cid.endswith("REFINED") else "BASE"
        add(cid,"A0","CONTROL","DERIVED_IDENTITY","SYNTHETIC",0.0 if cid==PILOT_IDS[0] else .06,.75,.05,1,1,.5,1e12,PARTICLE_VELOCITY_RATIO,64 if res=="REFINED" else 32,2 if res=="REFINED" else 1,res,True,False,None,None,(),(),())
    for p in PRESSURES:
        cid=f"C0-SOURCE-P{p}-NOFINES"
        add(cid,"C0","PRIMARY","EWP_GOVERNED_SOURCE",f"SOURCE_P{p}",0,0,0,0,0,.5,1e12,PARTICLE_VELOCITY_RATIO,32,1,"BASE",cid in PILOT_IDS,True,None,None,(),(),())
    add(PILOT_IDS[6],"C1","REFERENCE","PUCKWORKS_PROVENANCE_BOUND","SYNTHETIC",.06,.75,.05,1,1,.5,1e12,PARTICLE_VELOCITY_RATIO,32,1,"BASE",True,False,None,None,(),(),())
    add(PILOT_IDS[7],"R1","REFINEMENT","NUMERICAL_CONTROL","SYNTHETIC_P7",.06,.75,.05,1,.5,.5,1e12,PARTICLE_VELOCITY_RATIO,32,1,"BASE",True,False,None,"A0-TRANSPORT-REFINED",(),(),())
    for ff in (.02,.06,.10):
      for mf in (.25,.75):
       for kr in (.02,.10):
        for ne in (1.0,2.0):
         for eta in (.5,1.0):
          for alpha in (1e12,1e13):
           stem=f"FF{ff}-MF{mf}-KR{kr}-N{ne}-RET{eta}-AR{alpha:.0e}"
           for res,nx,sub in (("BASE",32,1),("REFINED",64,2)):
            ids=tuple(f"S1-SOURCE-P{p}-{stem}-{res}" for p in PRESSURES)
            for p,cid in zip(PRESSURES,ids):
             rid=cid.replace(f"-{res}","-REFINED" if res=="BASE" else "-BASE")
             ret=tuple(f"S1-SOURCE-P{p}-FF{ff}-MF{mf}-KR{kr}-N{ne}-RET{x}-AR{alpha:.0e}-{res}" for x in (.5,1.0) if x!=eta)
             clo=tuple(f"S1-SOURCE-P{p}-FF{ff}-MF{mf}-KR{x}-N{ne}-RET{eta}-AR{a:.0e}-{res}" for x in (.02,.10) for a in (1e12,1e13) if x!=kr or a!=alpha)
             add(cid,"S1","PRIMARY","SYNTHETIC_CAPABILITY_BOUND",f"SOURCE_P{p}",ff,mf,kr,ne,eta,.5,alpha,PARTICLE_VELOCITY_RATIO,nx,sub,res,False,True,f"C0-SOURCE-P{p}-NOFINES",rid,tuple(x for x in ids if x!=cid),ret,clo)
    if len(rows)>HARD_CAP or len(rows)!=len({r['case_id'] for r in rows}): raise RuntimeError("MATRIX_ID_OR_CAP_INVALID")
    return rows

def candidate_key(row: dict[str, Any]) -> tuple[Any,...]:
    return tuple(row[k] for k in ("fines_fraction","mobilizable_fraction","release_rate_s","release_exponent","retention_fraction","layer_porosity","specific_cake_resistance_m_kg","particle_velocity_ratio"))

def adjudicative_ids() -> list[str]:
    ids=sorted(r["case_id"] for r in matrix_rows() if r["adjudicative"])
    if len(ids)!=579 or sum(i.startswith("C0-") for i in ids)!=3 or sum(i.startswith("S1-") for i in ids)!=576: raise RuntimeError("ADJUDICATIVE_COHORT_INVALID")
    return ids

def protocol(matrix_hash: str | None=None) -> dict[str, Any]:
    return {"schema_version":"ewp.sci_md_002c.protocol.v1","task_id":TASK,"status":"PREEXECUTION_PACKAGE_COMPLETE_PENDING_INDEPENDENT_REVIEW",
      "source":{"overlay_path":str(OVERLAY.relative_to(ROOT)),"overlay_sha256":OVERLAY_SHA,"column_contract":["source_time_s","solver_time_s","observed_pressure_pa","reference_model_pressure_pa","observed_flow_kg_s","reference_model_flow_kg_s","observed_mass_kg","reference_model_mass_kg"],
      "forcing":"observed_pressure_pa","comparison_target":"observed_flow_kg_s","window":{"indices_inclusive":[100,899],"rows":800,"source_start_s":10.01001,"source_end_s":89.98999,"endpoint_observed_pressure_pa":{str(k):v for k,v in WINDOW_END_PRESSURES.items()},"interpretation":"SATURATED_MODEL_APPROXIMATION_INHERITED_GOVERNED_PROTECTED_WINDOW","measured_saturation_event":False},"pressure_interpolation":"piecewise linear between exact source samples; midpoint evaluation at each numerical substep","hydraulic_anchor":"one observed P9 full-overlay terminal-flow hydraulic scale transferred unchanged"},
      "model":{"chain":"observed pressure -> axial flow -> finite-inventory release -> conservative axial transport -> downstream deposition -> compact-layer resistance -> aggregate flow","release":"k_rel*(u/u_ref)^n*M_bound, shared across pressure","transport":"first-order conservative upwind finite volume; zero dispersion","particle_velocity_ratio":{"value":PARTICLE_VELOCITY_RATIO,"provenance":"SYNTHETIC_CAPABILITY_UPPER_BOUND","interpretation":"fines move at fastest admissible fluid velocity; retardation robustness not established"},"retention":"0.5 and 1.0 primary bracket; no unproven full-retention dominance assumption","cake":"Rc=mu*alpha_c*m_dep/A^2 and h=m_dep/(rho_s*(1-epsilon_c)*A)","active_bed":"fixed; fines loss does not open bed"},
      "axes":{"fines_fraction":[.02,.06,.10],"mobilizable_fraction":[.25,.75],"release_rate_s":[.02,.10],"release_exponent":[1.,2.],"retention_fraction":[.5,1.],"layer_porosity":[.5],"specific_cake_resistance_m_kg":[1e12,1e13],"particle_velocity_ratio":[PARTICLE_VELOCITY_RATIO],"base":{"axial_cells":32,"temporal_substeps":1},"refined":{"axial_cells":64,"temporal_substeps":2}},
      "provenance":{"source_fields":"EWP_GOVERNED_SOURCE","hydraulic_anchor":"EWP_GOVERNED_SOURCE_REFERENCE_SCALE_NOT_CLEAN_BED_MEASUREMENT","physical_axes":"SYNTHETIC_CAPABILITY_BOUND","particle_velocity_ratio":"SYNTHETIC_CAPABILITY_UPPER_BOUND","transport":"NUMERICAL_CONTROL","cake_identities":"DERIVED_IDENTITY"},
      "feasibility":{"equations":["Rc9_required(Rc5)=(P9/P5)*(Rb+Rc5)-Rb","Rc11_required(Rc9)=(P11/P9)*(Rb+Rc9)-Rb"],"classification":"retention-adjusted complete-release/transport/deposition optimistic upper bound at exact window endpoint"},
      "cohort":{"row_count":579,"s1_rows":576,"c0_rows":3,"candidate_count":96,"row_ids_sha256":hash_obj(adjudicative_ids()),"must_equal_exact_sorted_set":True},
      "uncertainty":"U59=abs(M59_base-M59_refined), U911 likewise; PASS iff both base margins-U>0; REJECTED iff either base margin+U<=0; otherwise NUMERICALLY_UNRESOLVED",
      "mass_tolerance_kg":MASS_ABS_TOL,"temporal_tolerance":{"absolute":MASS_ABS_TOL,"relative":FLOAT_REL_TOL},
      "gates":["AUTHORITY_AND_PACKAGE_INTEGRITY","REFERENCE_AND_NUMERICAL_VALIDITY","MASS_CONSERVATION_PHYSICAL_STATE_INVENTORY_AND_GEOMETRY","RESISTANCE_DIRECTION","PRESSURE_ORDERING","TEMPORAL_FINES_DEPOSITION_SIGNATURE","RETENTION_AND_CLOSURE_DEPENDENCE","PARTICLE_SIZE_AND_GRIND_IDENTIFIABILITY","AGGREGATE_COMPARISON"],
      "gate2_subconditions":["numerical_mass_conservation","physical_state_validity","finite_inventory_feasibility","compact_layer_geometry_validity"],
      "assumption_dependence":{"primary_precedence":["SCI_MD_002C_CAPABILITY_DEPENDS_ON_EXTREME_FINES_INVENTORY","SCI_MD_002C_CAPABILITY_DEPENDS_ON_FULL_RETENTION_COMPACT_LAYER","SCI_MD_002C_CAPABILITY_DEPENDS_ON_SINGLE_RETENTION_STATE","SCI_MD_002C_CAPABILITY_DEPENDS_ON_UNIDENTIFIED_RELEASE_CLOSURE","SCI_MD_002C_CAPABILITY_DEPENDS_ON_UNIDENTIFIED_LAYER_CONDUCTIVITY","SCI_MD_002C_AXIAL_FINES_CAPABILITY_SURVIVES_SYNTHETIC_CLOSURE_SCREEN"],"secondary_flags":True,"fixed_not_robust":["layer_porosity","particle_velocity_ratio"]},
      "dispositions":["SCI_MD_002C_REJECTED_INSUFFICIENT_FINES_INVENTORY","SCI_MD_002C_REJECTED_WRONG_RESISTANCE_DIRECTION","SCI_MD_002C_REJECTED_WRONG_PRESSURE_ORDERING","SCI_MD_002C_PRESSURE_ORDERING_NUMERICALLY_UNRESOLVED","SCI_MD_002C_REJECTED_WRONG_TEMPORAL_SIGNATURE","SCI_MD_002C_AXIAL_FINES_CAPABILITY_SURVIVES_SYNTHETIC_CLOSURE_SCREEN","SCI_MD_002C_CAPABILITY_DEPENDS_ON_FULL_RETENTION_COMPACT_LAYER","SCI_MD_002C_CAPABILITY_DEPENDS_ON_SINGLE_RETENTION_STATE","SCI_MD_002C_CAPABILITY_DEPENDS_ON_UNIDENTIFIED_RELEASE_CLOSURE","SCI_MD_002C_CAPABILITY_DEPENDS_ON_UNIDENTIFIED_LAYER_CONDUCTIVITY","SCI_MD_002C_CAPABILITY_DEPENDS_ON_EXTREME_FINES_INVENTORY","SCI_MD_002C_CLOSURE_IDENTIFIABILITY_DESIGN_BLOCKED","SCI_MD_002C_SATURATED_WINDOW_AUTHORITY_NOT_ESTABLISHED","SCI_MD_002C_ADDITIONAL_FINES_MEASUREMENTS_REQUIRED","SCI_MD_002C_MODEL_OR_AUTHORITY_INVALID","SCI_MD_002C_NUMERICAL_EXECUTION_INVALID","SCI_MD_002C_PREEXECUTION_PACKAGE_COMPLETE_PENDING_INDEPENDENT_REVIEW"],
      "pilot_ids":list(PILOT_IDS),"matrix_sha256":matrix_hash,"record_schema":RECORD_SCHEMA,"hard_cap":HARD_CAP,
      "resource_limits":{"workers":1,"nested_threads":1,"memory_gib":16,"gpu":0,"openfoam":0},
      "claim_boundary":["PHYSICAL_VALIDATION_NOT_ESTABLISHED","POST_OBSERVATION_MECHANISM_DISCRIMINATION","NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE","NO_COMBINED_MECHANISM_AUTHORIZATION","NO_SCI_LC_AUTHORIZATION","NO_OPENFOAM_AUTHORIZATION","GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED","FINES_CLOSURE_PARAMETERS_NOT_ESTABLISHED_AS_REAL_PUCK_MEASUREMENTS"]}

def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True,exist_ok=True)
    rows=matrix_rows(); matrix={"schema_version":"ewp.sci_md_002c.matrix.v1","row_count":len(rows),"adjudicative_row_count":579,"candidate_count":96,"rows":rows}
    jp=OUT/"SCI_MD_002C_CASE_MATRIX.json"; jp.write_text(canonical(matrix))
    with (OUT/"SCI_MD_002C_CASE_MATRIX.csv").open("w",newline="") as f:
        fields=list(rows[0]); w=csv.DictWriter(f,fields,lineterminator="\n"); w.writeheader()
        for r in rows:
            x=r.copy()
            for k in ("cross_pressure_peer_ids","retention_peer_ids","closure_peer_ids"): x[k]="|".join(x[k])
            w.writerow(x)
    FEAS.write_text(canonical(feasibility_bounds()))
    REFS.write_text(canonical({"schema_version":"ewp.sci_md_002c.puckworks_reference.v1","commit":PUCK_COMMIT,"tree":PUCK_TREE,"mode":"READ_ONLY","files":[{"path":p,"sha256":h} for p,h in sorted(PUCK_FILES.items())],"reference_class":"INDEPENDENT_STRUCTURAL_IDENTITY_CHECKS","evidence_role":"PUCKWORKS_PROVENANCE_BOUND","quantitative_reference_claim":"NO_QUANTITATIVE_REFERENCE_PARITY_CLAIM","multi_streamtube_excluded":True}))
    (OUT/"SCI_MD_002C_PROTOCOL.json").write_text(canonical(protocol(sha(jp))))
    return {"rows":len(rows),"adjudicative_rows":len(adjudicative_ids()),"candidates":96,"matrix_sha256":sha(jp)}

def verify_generated() -> dict[str, Any]:
    expected={p:(p.read_bytes() if p.exists() else None) for p in (OUT/"SCI_MD_002C_CASE_MATRIX.json",OUT/"SCI_MD_002C_CASE_MATRIX.csv",FEAS,REFS,OUT/"SCI_MD_002C_PROTOCOL.json")}
    result=generate()
    if any(expected[p] is not None and expected[p]!=p.read_bytes() for p in expected): raise RuntimeError("NONDETERMINISTIC_GENERATION")
    matrix=json.loads((OUT/"SCI_MD_002C_CASE_MATRIX.json").read_text())
    if matrix["row_count"]!=len(matrix_rows()) or matrix["adjudicative_row_count"]!=579: raise RuntimeError("MATRIX_COUNT_INVALID")
    return result

def source_rows(row: dict[str,Any], histories=None) -> list[dict[str,float]]:
    if row["pressure_identity"].startswith("SOURCE_P"):
        return (histories or load_histories())[int(row["pressure_identity"].split("P")[-1])]
    return [{"source_time_s":i*.1,"observed_pressure_pa":7e5,"observed_flow_kg_s":0.0} for i in range(301)]

def linear_pressure(a:dict[str,float],b:dict[str,float],fraction:float)->float:
    if not 0<=fraction<=1: raise ValueError("PRESSURE_INTERPOLATION_FRACTION_INVALID")
    return a["observed_pressure_pa"]+(b["observed_pressure_pa"]-a["observed_pressure_pa"])*fraction

def simulate(row: dict[str,Any], histories=None) -> dict[str,Any]:
    src=source_rows(row,histories); nx=int(row["axial_cells"]); sub=int(row["temporal_substeps"]); dx=H0/nx
    initial=DOSE*row["fines_fraction"]*row["mobilizable_fraction"]
    bound=[initial/nx]*nx; mobile=[0.0]*nx; deposited=escaped=0.0; rb=hydraulic_anchor(); uref=(TERMINAL_FLOWS[9]/RHO)/AREA
    temporal=[]; released_total=outlet_total=pressure_integral=0.0; previous=src[0]
    def snapshot(s,release_rate,outflux,dep_rate,esc_rate,inc):
        rc=MU*row["specific_cake_resistance_m_kg"]*deposited/AREA**2
        q=s["observed_pressure_pa"]/(rb+rc); thick=deposited/(SOLID_RHO*(1-row["layer_porosity"])*AREA) if row["layer_porosity"]<1 else math.inf
        residual=initial-(sum(bound)+sum(mobile)+deposited+escaped)
        return {"source_time_s":s["source_time_s"],"observed_pressure_pa":s["observed_pressure_pa"],"predicted_flow_kg_s":q*RHO,"clean_bed_flow_kg_s":s["observed_pressure_pa"]/rb*RHO,
         "bound_mass_kg":sum(bound),"released_mass_rate_kg_s":release_rate,"mobile_mass_kg":sum(mobile),"outlet_fines_flux_kg_s":outflux,
         "deposition_rate_kg_s":dep_rate,"escaped_rate_kg_s":esc_rate,"deposited_mass_kg":deposited,"escaped_mass_kg":escaped,
         "cumulative_released_mass_kg":released_total,"cumulative_transported_outlet_mass_kg":outlet_total,"pressure_integral_pa_s":pressure_integral,
         "bound_mass_decrement_kg":inc["released"],"released_mass_increment_kg":inc["released"],"mobile_mass_change_kg":inc["mobile_change"],
         "transported_outlet_mass_increment_kg":inc["outlet"],"retained_outlet_mass_increment_kg":inc["deposited"],"escaped_mass_increment_kg":inc["escaped"],
         "particle_velocity_ratio":row["particle_velocity_ratio"],"compact_layer_thickness_m":thick,"compact_layer_resistance_pa_s_m3":rc,
         "clean_bed_resistance_pa_s_m3":rb,"total_resistance_pa_s_m3":rb+rc,"mass_residual_kg":residual}
    zero={"released":0.0,"mobile_change":0.0,"outlet":0.0,"deposited":0.0,"escaped":0.0}
    temporal.append(snapshot(src[0],0,0,0,0,zero))
    for s in src[1:]:
        dt_total=s["source_time_s"]-previous["source_time_s"]
        if dt_total<=0: raise ValueError("NONMONOTONIC_TIME")
        rel_acc=out_acc=dep_acc=esc_acc=0.0;mobile_before=sum(mobile)
        for k in range(sub):
            dt=dt_total/sub
            pressure=linear_pressure(previous,s,(k+.5)/sub);pressure_integral+=pressure*dt
            rc=MU*row["specific_cake_resistance_m_kg"]*deposited/AREA**2; q=pressure/(rb+rc); u=q/AREA
            lam=row["release_rate_s"]*(u/uref)**row["release_exponent"] if uref>0 else 0
            for i in range(nx):
                rel=bound[i]*(1-math.exp(-lam*dt)); bound[i]-=rel; mobile[i]+=rel; rel_acc+=rel
            # Conservative exact cell-to-cell compartment transport; subcycle for CFL.
            particle_u=u*row["particle_velocity_ratio"];cfl=particle_u*dt/dx; nmove=max(1,math.ceil(cfl/.8)); dts=dt/nmove
            for _j in range(nmove):
                frac=1-math.exp(-particle_u*dts/dx); outgoing=[m*frac for m in mobile]
                for i,x in enumerate(outgoing): mobile[i]-=x
                for i in range(1,nx): mobile[i]+=outgoing[i-1]
                out=outgoing[-1]; dep=out*row["retention_fraction"]; esc=out-dep;deposited+=dep; escaped+=esc; out_acc+=out; dep_acc+=dep;esc_acc+=esc
        released_total+=rel_acc;outlet_total+=out_acc
        inc={"released":rel_acc,"mobile_change":sum(mobile)-mobile_before,"outlet":out_acc,"deposited":dep_acc,"escaped":esc_acc}
        snap=snapshot(s,rel_acc/dt_total,out_acc/dt_total,dep_acc/dt_total,esc_acc/dt_total,inc)
        if any(not math.isfinite(v) for v in snap.values() if isinstance(v,(int,float))): raise ValueError("NONFINITE_STATE")
        if min(bound+mobile)<-MASS_ABS_TOL or snap["mass_residual_kg"]< -MASS_ABS_TOL or abs(snap["mass_residual_kg"])>MASS_ABS_TOL: raise ValueError("FINES_MASS_OR_BOUND_INVALID")
        temporal.append(snap);previous=s
    terminal=temporal[-1]; max_res=max(abs(x["mass_residual_kg"]) for x in temporal)
    onset=next((x["source_time_s"] for x in temporal if x["deposited_mass_kg"]>0),None)
    return {"case_id":row["case_id"],"initial_inventory_kg":initial,"available_inventory_kg":initial,"maximum_depositable_mass_kg":initial*row["retention_fraction"],
            "maximum_possible_cake_resistance_pa_s_m3":MU*row["specific_cake_resistance_m_kg"]*initial*row["retention_fraction"]/AREA**2,
            "terminal":terminal,"temporal":temporal,"max_abs_mass_residual_kg":max_res,
            "deposition_onset_s":onset,"inventory_exhausted":sum(bound)<=max(MASS_ABS_TOL,initial*1e-6),"numerical_status":"COMPLETE","physical_status":"VALID"}

def references() -> dict[str,Any]:
    # Independent structural identities; no source-conditioned scientific triplet.
    r=matrix_rows()[0].copy(); a=simulate(r); zero=abs(a["terminal"]["compact_layer_resistance_pa_s_m3"])<1e-20
    if not zero: raise RuntimeError("ZERO_FINES_REFERENCE_FAILED")
    m=.0001; alpha=1e12; rc=MU*alpha*m/AREA**2; h=m/(SOLID_RHO*.5*AREA)
    if abs(rc-MU*h/(1/(SOLID_RHO*.5*alpha)*AREA))>max(1,abs(rc))*1e-12: raise RuntimeError("CAKE_IDENTITY_FAILED")
    return {"zero_fines":True,"cake_mass_geometry_identity":True,"serial_resistance":True,"mass_conservation":True,
            "reference_class":"INDEPENDENT_STRUCTURAL_IDENTITY_CHECKS","provenance":"PUCKWORKS_PROVENANCE_BOUND","quantitative_reference_claim":"NO_QUANTITATIVE_REFERENCE_PARITY_CLAIM"}

def expected_authority_bindings(bundle: Path|str) -> dict[str,Any]:
    b=safe_bundle(bundle); ids=adjudicative_ids(); ident=identity()
    return {"task_id":TASK,"lane_id":LANE_ID,"branch":BRANCH,"source_head":ident["head"],"source_tree":ident["tree"],
      "protocol_sha256":sha(OUT/"SCI_MD_002C_PROTOCOL.json"),"matrix_sha256":sha(OUT/"SCI_MD_002C_CASE_MATRIX.json"),"implementation_sha256":sha(Path(__file__)),
      "source_overlay_sha256":OVERLAY_SHA,"puckworks_commit":PUCK_COMMIT,"puckworks_tree":PUCK_TREE,"puckworks_files":PUCK_FILES,"puckworks_reference_sha256":sha(REFS),
      "feasibility_sha256":sha(FEAS),"authorized_row_ids":ids,"row_ids_sha256":hash_obj(ids),"external_namespace":EXTERNAL_NAMESPACE,
      "bundle_path_name":b.name,"bundle_uuid":"INDEPENDENT_OWNER_VALUE_REQUIRED","workers":1,"nested_threads":1,"record_schema":RECORD_SCHEMA,
      "no_overwrite":True,"exact_resume":True}

def validate_authority(path: Path|str,bundle: Path|str) -> dict[str,Any]:
    a=json.loads(Path(path).read_text()); exp=expected_authority_bindings(bundle)
    if a.get("authorization_token")!=TOKEN or a.get("owner_role")!=OWNER_ROLE: raise ValueError("OWNER_AUTHORITY_REQUIRED")
    try:
        if not str(a["authorization_date"]).endswith("Z"): raise ValueError
        datetime.fromisoformat(str(a["authorization_date"])[:-1]+"+00:00")
    except Exception as e: raise ValueError("AUTHORIZATION_DATE_INVALID") from e
    if not isinstance(a.get("bundle_uuid"),str) or str(uuid.UUID(a["bundle_uuid"]))!=a["bundle_uuid"]: raise ValueError("BUNDLE_UUID_INVALID")
    exp["bundle_uuid"]=a["bundle_uuid"]
    for k,v in exp.items():
        if a.get(k)!=v: raise ValueError(f"AUTHORITY_BINDING_MISMATCH_{k}")
    if set(a)!=(set(exp)|{"authorization_token","owner_role","authorization_date"}): raise ValueError("AUTHORITY_FIELDS_INVALID")
    return a

def internal_hash(rec: dict[str,Any]) -> str: return hash_obj({k:v for k,v in rec.items() if k!="record_sha256"})

def durable_write(path: Path, obj: dict[str,Any], *, refuse_existing=True) -> tuple[str,int]:
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and refuse_existing: raise FileExistsError("IMMUTABLE_RECORD_EXISTS")
    data=canonical(obj).encode(); tmp=path.with_name(path.name+f".tmp.{os.getpid()}")
    try:
        with tmp.open("xb") as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
        try:
            fd=os.open(path.parent,os.O_RDONLY); os.fsync(fd); os.close(fd)
        except OSError: pass
        got=path.read_bytes()
        if got!=data or json.loads(got)!=json.loads(data): raise IOError("DURABLE_READBACK_MISMATCH")
        return hashlib.sha256(got).hexdigest(),len(got)
    finally:
        if tmp.exists(): tmp.unlink()

def record_for(row,a,ah,result,command,start) -> dict[str,Any]:
    rec={"schema_version":RECORD_SCHEMA,"task_id":TASK,"lane_id":LANE_ID,"case_id":row["case_id"],"source_head":a["source_head"],"source_tree":a["source_tree"],
      "authority_sha256":ah,"bundle_uuid":a["bundle_uuid"],"protocol_sha256":a["protocol_sha256"],"matrix_sha256":a["matrix_sha256"],"implementation_sha256":a["implementation_sha256"],
      "source_overlay_sha256":a["source_overlay_sha256"],"feasibility_sha256":a["feasibility_sha256"],"puckworks_reference_sha256":a["puckworks_reference_sha256"],"parameters":row,"provenance":row["evidence_role"],
      "command":command,"pid":os.getpid(),"parent_pid":os.getppid(),"start_time":start,"completion_time":utc(),"numerical_status":result["numerical_status"],
      "physical_status":result["physical_status"],"stop_reason":None,"scientific_result_sha256":hash_obj(result),"result":result}
    rec["record_sha256"]=internal_hash(rec); return rec

def record_relative_path(case_id:str) -> str:
    if not case_id or any(x in case_id for x in ("/","\\","..")): raise ValueError("UNSAFE_CASE_ID")
    return f"case_records/{case_id}.json"

def validate_record(data:bytes,row:dict[str,Any],a:dict[str,Any],ah:str,path:Path|None=None) -> dict[str,Any]:
    try: rec=json.loads(data)
    except Exception as e: raise ValueError("MALFORMED_RECORD_JSON") from e
    row=json.loads(canonical(row)); expected={"schema_version":RECORD_SCHEMA,"task_id":TASK,"lane_id":LANE_ID,"case_id":row["case_id"],
      "source_head":a["source_head"],"source_tree":a["source_tree"],"authority_sha256":ah,"bundle_uuid":a["bundle_uuid"],
      "protocol_sha256":a["protocol_sha256"],"matrix_sha256":a["matrix_sha256"],"implementation_sha256":a["implementation_sha256"],
      "source_overlay_sha256":a["source_overlay_sha256"],"feasibility_sha256":a["feasibility_sha256"],
      "puckworks_reference_sha256":a["puckworks_reference_sha256"],"parameters":row,"provenance":row["evidence_role"]}
    for k,v in expected.items():
        if rec.get(k)!=v: raise ValueError(f"RECORD_BINDING_MISMATCH_{k}")
    if path is not None:
        if path.is_symlink() or path.name!=Path(record_relative_path(row["case_id"])).name: raise ValueError("UNSAFE_RECORD_PATH")
    if rec.get("scientific_result_sha256")!=hash_obj(rec.get("result")): raise ValueError("SCIENTIFIC_RESULT_HASH_FAILURE")
    if rec.get("record_sha256")!=internal_hash(rec): raise ValueError("INTERNAL_RECORD_HASH_FAILURE")
    if rec.get("numerical_status")!=rec["result"].get("numerical_status") or rec.get("physical_status")!=rec["result"].get("physical_status"):
        raise ValueError("RECORD_RESULT_STATUS_MISMATCH")
    if rec.get("stop_reason")!=rec["result"].get("stop_reason"): raise ValueError("RECORD_STOP_REASON_MISMATCH")
    return rec

def write_ledger(bundle:Path,event:dict[str,Any]):
    p=bundle/"process_ledger.jsonl"; line=canonical(event).encode()
    with p.open("ab") as f: f.write(line); f.flush(); os.fsync(f.fileno())

def build_manifest(bundle:Path,a,ah,ids):
    lookup={r["case_id"]:r for r in matrix_rows()}
    records=[]
    for cid in ids:
        rel=record_relative_path(cid); p=bundle/rel; data=p.read_bytes(); validate_record(data,lookup[cid],a,ah,p)
        records.append({"case_id":cid,"path":rel,"size":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    aggregate=hash_obj([{"case_id":x["case_id"],"size":x["size"],"sha256":x["sha256"]} for x in records])
    m={"schema_version":"ewp.sci_md_002c.manifest.v1","task_id":TASK,"lane_id":LANE_ID,"source_head":a["source_head"],"source_tree":a["source_tree"],"bundle_uuid":a["bundle_uuid"],"authority_sha256":ah,"row_ids_sha256":hash_obj(ids),"record_count":len(records),"records":records,"ordered_record_aggregate_sha256":aggregate}
    durable_write(bundle/"manifest.json",m); return m

def execute(bundle_arg,authority_arg,resume=False,rows_override=None):
    bundle=safe_bundle(bundle_arg); bundle.mkdir(parents=True,exist_ok=True); a=validate_authority(authority_arg,bundle); ah=sha(authority_arg)
    ids=adjudicative_ids()
    if rows_override is not None and list(rows_override)!=ids: raise ValueError("PARTIAL_OR_REORDERED_COHORT_REFUSED")
    if ids!=a["authorized_row_ids"]: raise ValueError("AUTHORIZED_COHORT_INVALID")
    lookup={r["case_id"]:r for r in matrix_rows()}; start=utc(); write_ledger(bundle,{"event":"START","pid":os.getpid(),"parent_pid":os.getppid(),"command":" ".join(sys.argv),"working_directory":str(ROOT),"bundle_uuid":a["bundle_uuid"],"authority_sha256":ah,"time":start})
    for cid in ids:
        p=bundle/record_relative_path(cid)
        if p.exists():
            if not resume: raise FileExistsError("DUPLICATE_RECORD_REFUSED")
            validate_record(p.read_bytes(),lookup[cid],a,ah,p)
            continue
        row=lookup[cid]; t=utc()
        try: result=simulate(row)
        except Exception as e:
            result={"case_id":cid,"numerical_status":"FAILURE","physical_status":"INVALID","stop_reason":type(e).__name__+":"+str(e),"temporal":[],"terminal":{}}
        rec=record_for(row,a,ah,result," ".join(sys.argv),t); h,n=durable_write(p,rec)
        data=p.read_bytes(); validate_record(data,row,a,ah,p)
        if len(data)!=n or hashlib.sha256(data).hexdigest()!=h: raise IOError("POST_WRITE_FULL_HASH_FAILURE")
    m=build_manifest(bundle,a,ah,ids); write_ledger(bundle,{"event":"CLOSEOUT","pid":os.getpid(),"bundle_uuid":a["bundle_uuid"],"status":"COMPLETE","time":utc(),"record_count":len(ids)})
    return m

def verify_bundle(bundle_arg,authority_arg=None,expected_ids=None):
    b=safe_bundle(bundle_arg); a=validate_authority(authority_arg,b) if authority_arg else None; ah=sha(authority_arg) if authority_arg else None
    m=json.loads((b/"manifest.json").read_text()); ids=expected_ids or (a["authorized_row_ids"] if a else [x["case_id"] for x in m["records"]])
    for k,v in {"schema_version":"ewp.sci_md_002c.manifest.v1","task_id":TASK,"lane_id":LANE_ID,"authority_sha256":ah,"bundle_uuid":a["bundle_uuid"],"source_head":a["source_head"],"source_tree":a["source_tree"],"row_ids_sha256":hash_obj(ids)}.items():
        if m.get(k)!=v: raise ValueError(f"MANIFEST_BINDING_MISMATCH_{k}")
    if m["record_count"]!=len(ids) or [x["case_id"] for x in m["records"]]!=ids: raise ValueError("BUNDLE_COHORT_INVALID")
    lookup={r["case_id"]:r for r in matrix_rows()}
    seen=[]
    for x in m["records"]:
        if x["path"]!=record_relative_path(x["case_id"]): raise ValueError("UNSAFE_OR_SWAPPED_MANIFEST_PATH")
        p=b/x["path"]
        if p.is_symlink(): raise ValueError("RECORD_SYMLINK_REFUSED")
        data=p.read_bytes()
        if len(data)!=x["size"] or hashlib.sha256(data).hexdigest()!=x["sha256"]: raise ValueError(f"FULL_RECORD_HASH_FAILURE_{x['case_id']}")
        validate_record(data,lookup[x["case_id"]],a,ah,p)
        seen.append({"case_id":x["case_id"],"size":x["size"],"sha256":x["sha256"]})
    if hash_obj(seen)!=m["ordered_record_aggregate_sha256"]: raise ValueError("ORDERED_AGGREGATE_MISMATCH")
    return {"record_count":len(seen),"manifest_sha256":sha(b/"manifest.json"),"ordered_record_aggregate_sha256":m["ordered_record_aggregate_sha256"]}

def ordering(m59,m911,u59,u911):
    if m59-u59>0 and m911-u911>0:return "PASS"
    if m59+u59<=0 or m911+u911<=0:return "REJECTED"
    return "NUMERICALLY_UNRESOLVED"

def close(a:float,b:float,atol:float=MASS_ABS_TOL) -> bool:
    return abs(a-b)<=max(atol,FLOAT_REL_TOL*max(abs(a),abs(b)))

def temporal_ok(result,row,histories=None):
    t=result.get("temporal",[]); expected=source_rows(row,histories)
    if row["pressure_identity"].startswith("SOURCE_P") and len(t)!=800:return False
    if len(t)!=len(expected): return False
    required=("source_time_s","observed_pressure_pa","predicted_flow_kg_s","bound_mass_kg","mobile_mass_kg","deposited_mass_kg","escaped_mass_kg","bound_mass_decrement_kg","released_mass_increment_kg","mobile_mass_change_kg","transported_outlet_mass_increment_kg","retained_outlet_mass_increment_kg","escaped_mass_increment_kg","compact_layer_thickness_m","compact_layer_resistance_pa_s_m3","clean_bed_resistance_pa_s_m3","total_resistance_pa_s_m3","mass_residual_kg")
    if any(any(not isinstance(x.get(k),(int,float)) or not math.isfinite(x[k]) for k in required) for x in t): return False
    initial=result.get("initial_inventory_kg"); prev=None
    for i,(x,s) in enumerate(zip(t,expected)):
        if not close(x["source_time_s"],s["source_time_s"],1e-10) or not close(x["observed_pressure_pa"],s["observed_pressure_pa"],1e-8): return False
        if min(x["bound_mass_kg"],x["mobile_mass_kg"],x["deposited_mass_kg"],x["escaped_mass_kg"]) < -MASS_ABS_TOL:return False
        if abs(x["mass_residual_kg"])>MASS_ABS_TOL:return False
        if not close(x["bound_mass_decrement_kg"],x["released_mass_increment_kg"]):return False
        if not close(x["retained_outlet_mass_increment_kg"]+x["escaped_mass_increment_kg"],x["transported_outlet_mass_increment_kg"]):return False
        if not close(x["compact_layer_thickness_m"],x["deposited_mass_kg"]/(SOLID_RHO*(1-row["layer_porosity"])*AREA),1e-15):return False
        rc=MU*row["specific_cake_resistance_m_kg"]*x["deposited_mass_kg"]/AREA**2
        if not close(x["compact_layer_resistance_pa_s_m3"],rc,1e-6):return False
        if not close(x["total_resistance_pa_s_m3"],x["clean_bed_resistance_pa_s_m3"]+rc,1e-6):return False
        if not close(x["predicted_flow_kg_s"],x["observed_pressure_pa"]/x["total_resistance_pa_s_m3"]*RHO,1e-15):return False
        if x["deposited_mass_kg"]<=MASS_ABS_TOL and abs(rc)>1e-6:return False
        if prev is not None:
            if not close(prev["bound_mass_kg"]-x["bound_mass_kg"],x["released_mass_increment_kg"]):return False
            if not close(x["mobile_mass_kg"]-prev["mobile_mass_kg"],x["mobile_mass_change_kg"]):return False
            if not close(x["mobile_mass_change_kg"],x["released_mass_increment_kg"]-x["transported_outlet_mass_increment_kg"]):return False
            if not close(x["deposited_mass_kg"]-prev["deposited_mass_kg"],x["retained_outlet_mass_increment_kg"]):return False
            if not close(x["escaped_mass_kg"]-prev["escaped_mass_kg"],x["escaped_mass_increment_kg"]):return False
            if x["deposited_mass_kg"]+MASS_ABS_TOL<prev["deposited_mass_kg"] or rc+1e-6<prev["compact_layer_resistance_pa_s_m3"]:return False
        elif not close(x["bound_mass_kg"],initial): return False
        prev=x
    term=result.get("terminal")
    return bool(t and term==t[-1] and close(initial,t[-1]["bound_mass_kg"]+t[-1]["mobile_mass_kg"]+t[-1]["deposited_mass_kg"]+t[-1]["escaped_mass_kg"]))

def reduce_bundle(bundle_arg,authority_arg,output):
    b=safe_bundle(bundle_arg); a=validate_authority(authority_arg,b); verify_bundle(b,authority_arg)
    lookup={r["case_id"]:r for r in matrix_rows()}; records={}
    for cid in adjudicative_ids(): records[cid]=json.loads((b/"case_records"/(cid+".json")).read_text())
    c0={p:records[f"C0-SOURCE-P{p}-NOFINES"] for p in PRESSURES}; candidates=[]
    groups={}
    for r in matrix_rows():
        if r["arm"]=="S1": groups.setdefault(candidate_key(r),{})[(int(r["pressure_identity"].split("P")[-1]),r["resolution"])]=records[r["case_id"]]
    if len(groups)!=96: raise ValueError("CANDIDATE_COUNT_INVALID")
    for key,g in sorted(groups.items()):
        if set(g)!={(p,res) for p in PRESSURES for res in ("BASE","REFINED")}: raise ValueError("CANDIDATE_COMPARATORS_INCOMPLETE")
        complete=all(x["numerical_status"]=="COMPLETE" and x["physical_status"]=="VALID" for x in g.values())
        row=lookup[g[(5,"BASE")]["case_id"]]
        conservation=complete and all(x["result"]["max_abs_mass_residual_kg"]<=MASS_ABS_TOL for x in g.values())
        physical=complete and all(min(x["result"]["terminal"][k] for k in ("bound_mass_kg","mobile_mass_kg","deposited_mass_kg","escaped_mass_kg"))>=-MASS_ABS_TOL for x in g.values())
        geometry=complete and all(x["result"]["terminal"]["compact_layer_thickness_m"]>=0 and x["result"]["terminal"]["total_resistance_pa_s_m3"]>0 for x in g.values())
        fb=feasibility_bounds()["optimistic_joint_bounds"]; maxrc=g[(5,"BASE")]["result"].get("maximum_possible_cake_resistance_pa_s_m3",0)
        inventory=complete and maxrc>=fb["required_Rc9_pa_s_m3"] and maxrc>=fb["required_Rc11_pa_s_m3"]
        gate2=conservation and physical and geometry and inventory
        resistance=gate2 and all(g[(p,"BASE")]["result"]["terminal"]["total_resistance_pa_s_m3"]>=c0[p]["result"]["terminal"]["total_resistance_pa_s_m3"] for p in PRESSURES)
        qb={p:g[(p,"BASE")]["result"]["terminal"]["predicted_flow_kg_s"] for p in PRESSURES}; qr={p:g[(p,"REFINED")]["result"]["terminal"]["predicted_flow_kg_s"] for p in PRESSURES}
        m59=qb[5]-qb[9];m911=qb[9]-qb[11];u59=abs(m59-(qr[5]-qr[9]));u911=abs(m911-(qr[9]-qr[11]));oc=ordering(m59,m911,u59,u911)
        temporal=complete and all(temporal_ok(x["result"],lookup[x["case_id"]]) for x in g.values())
        if not complete:first="REFERENCE_AND_NUMERICAL_VALIDITY";disp="SCI_MD_002C_NUMERICAL_EXECUTION_INVALID"
        elif not conservation:first="GATE2_NUMERICAL_MASS_CONSERVATION";disp="SCI_MD_002C_NUMERICAL_EXECUTION_INVALID"
        elif not physical:first="GATE2_PHYSICAL_STATE_VALIDITY";disp="SCI_MD_002C_NUMERICAL_EXECUTION_INVALID"
        elif not geometry:first="GATE2_COMPACT_LAYER_GEOMETRY_VALIDITY";disp="SCI_MD_002C_NUMERICAL_EXECUTION_INVALID"
        elif not inventory:first="GATE2_FINITE_INVENTORY_FEASIBILITY";disp="SCI_MD_002C_REJECTED_INSUFFICIENT_FINES_INVENTORY"
        elif not resistance:first="RESISTANCE_DIRECTION";disp="SCI_MD_002C_REJECTED_WRONG_RESISTANCE_DIRECTION"
        elif oc=="REJECTED":first="PRESSURE_ORDERING";disp="SCI_MD_002C_REJECTED_WRONG_PRESSURE_ORDERING"
        elif oc=="NUMERICALLY_UNRESOLVED":first="PRESSURE_ORDERING";disp="SCI_MD_002C_PRESSURE_ORDERING_NUMERICALLY_UNRESOLVED"
        elif not temporal:first="TEMPORAL_FINES_DEPOSITION_SIGNATURE";disp="SCI_MD_002C_REJECTED_WRONG_TEMPORAL_SIGNATURE"
        else:first=None;disp="EARLIER_GATES_SURVIVE"
        eligible=disp=="EARLIER_GATES_SURVIVE"; residuals={str(p):qb[p]-load_histories()[p][-1]["observed_flow_kg_s"] for p in PRESSURES} if eligible else None
        params=dict(zip(("fines_fraction","mobilizable_fraction","release_rate_s","release_exponent","retention_fraction","layer_porosity","specific_cake_resistance_m_kg","particle_velocity_ratio"),key));params["total_mobilizable_inventory_kg"]=DOSE*params["fines_fraction"]*params["mobilizable_fraction"]
        candidates.append({"candidate_parameters":params,"first_failed_gate":first,"candidate_disposition":disp,"numerical_physical_valid":complete,
          "gate2":{"numerical_mass_conservation":conservation,"physical_state_validity":physical,"finite_inventory_feasibility":inventory,"compact_layer_geometry_validity":geometry,"first_failed_subcondition":first if first and first.startswith("GATE2_") else None,
          "available_inventory_kg":g[(5,"BASE")]["result"].get("available_inventory_kg"),"maximum_depositable_mass_kg":g[(5,"BASE")]["result"].get("maximum_depositable_mass_kg"),"maximum_possible_cake_resistance_pa_s_m3":maxrc,"required_Rc9_pa_s_m3":fb["required_Rc9_pa_s_m3"],"required_Rc11_pa_s_m3":fb["required_Rc11_pa_s_m3"],"terminal_deposited_mass_kg":{str(p):g[(p,"BASE")]["result"]["terminal"]["deposited_mass_kg"] for p in PRESSURES},"terminal_cake_resistance_pa_s_m3":{str(p):g[(p,"BASE")]["result"]["terminal"]["compact_layer_resistance_pa_s_m3"] for p in PRESSURES}},
          "inventory_feasible":inventory,"resistance_direction":resistance,"M59_kg_s":m59,"M911_kg_s":m911,"U59_kg_s":u59,"U911_kg_s":u911,"ordering":oc,"temporal_signature":temporal,"aggregate_eligible":eligible,"residuals_kg_s":residuals,"rmse_kg_s":math.sqrt(sum(v*v for v in residuals.values())/3) if residuals else None,"mae_kg_s":sum(abs(v) for v in residuals.values())/3 if residuals else None})
    survivors=[c for c in candidates if c["aggregate_eligible"]]
    if survivors:
        supports={k:sorted({c["candidate_parameters"][k] for c in survivors}) for k in ("retention_fraction","release_rate_s","release_exponent","total_mobilizable_inventory_kg","fines_fraction","mobilizable_fraction","specific_cake_resistance_m_kg","layer_porosity","particle_velocity_ratio")}
        flags=[]
        if supports["total_mobilizable_inventory_kg"]==[DOSE*.1*.75]: flags.append("SCI_MD_002C_CAPABILITY_DEPENDS_ON_EXTREME_FINES_INVENTORY")
        if supports["retention_fraction"]==[1.0]: flags.append("SCI_MD_002C_CAPABILITY_DEPENDS_ON_FULL_RETENTION_COMPACT_LAYER")
        elif len(supports["retention_fraction"])==1: flags.append("SCI_MD_002C_CAPABILITY_DEPENDS_ON_SINGLE_RETENTION_STATE")
        if len(supports["release_rate_s"])==1 or len(supports["release_exponent"])==1: flags.append("SCI_MD_002C_CAPABILITY_DEPENDS_ON_UNIDENTIFIED_RELEASE_CLOSURE")
        if len(supports["specific_cake_resistance_m_kg"])==1: flags.append("SCI_MD_002C_CAPABILITY_DEPENDS_ON_UNIDENTIFIED_LAYER_CONDUCTIVITY")
        family=flags[0] if flags else "SCI_MD_002C_AXIAL_FINES_CAPABILITY_SURVIVES_SYNTHETIC_CLOSURE_SCREEN"
    else:
        valid=[c for c in candidates if c["numerical_physical_valid"] and c["inventory_feasible"]]; rd=[c for c in valid if c["resistance_direction"]]
        if not valid: family="SCI_MD_002C_NUMERICAL_EXECUTION_INVALID"
        elif not rd: family="SCI_MD_002C_REJECTED_WRONG_RESISTANCE_DIRECTION"
        elif any(c["ordering"]=="NUMERICALLY_UNRESOLVED" for c in rd): family="SCI_MD_002C_PRESSURE_ORDERING_NUMERICALLY_UNRESOLVED"
        elif any(c["ordering"]=="PASS" for c in rd): family="SCI_MD_002C_REJECTED_WRONG_TEMPORAL_SIGNATURE"
        else: family="SCI_MD_002C_REJECTED_WRONG_PRESSURE_ORDERING"
    result={"schema_version":"ewp.sci_md_002c.result.v1","task_id":TASK,"candidate_count":len(candidates),"family_disposition":family,"secondary_dependence_flags":flags if survivors else [],"assumption_support":supports if survivors else {},"fixed_assumption_robustness_not_established":["layer_porosity","particle_velocity_ratio"],"candidates":candidates,"grind_identifiability":"GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED","claim_boundary":protocol()["claim_boundary"]}
    durable_write(Path(output),result); return result

def pilot_run(bundle_arg):
    b=safe_bundle(bundle_arg); b.mkdir(parents=True,exist_ok=True); bid=str(uuid.uuid4()); lookup={r["case_id"]:r for r in matrix_rows()}; start=time.monotonic(); rows=[]; ident=identity()
    a={"source_head":ident["head"],"source_tree":ident["tree"],"bundle_uuid":bid,"protocol_sha256":sha(OUT/"SCI_MD_002C_PROTOCOL.json"),"matrix_sha256":sha(OUT/"SCI_MD_002C_CASE_MATRIX.json"),"implementation_sha256":sha(Path(__file__)),"source_overlay_sha256":OVERLAY_SHA,"feasibility_sha256":sha(FEAS),"puckworks_reference_sha256":sha(REFS)}; ah="NON_ADJUDICATIVE_PILOT_NO_OWNER_AUTHORITY"
    write_ledger(b,{"event":"START","pid":os.getpid(),"parent_pid":os.getppid(),"command":" ".join(sys.argv),"working_directory":str(ROOT),"bundle_uuid":bid,"time":utc(),"pilot":True})
    for cid in PILOT_IDS:
        row=lookup[cid]; result=simulate(row); rec=record_for(row,a,ah,result," ".join(sys.argv),utc())
        p=b/record_relative_path(cid);h,n=durable_write(p,rec);validate_record(p.read_bytes(),row,a,ah,p);rows.append({"case_id":cid,"path":record_relative_path(cid),"size":n,"sha256":h})
    aggregate=hash_obj([{"case_id":x["case_id"],"size":x["size"],"sha256":x["sha256"]} for x in rows])
    m={"schema_version":"ewp.sci_md_002c.pilot_manifest.v2","task_id":TASK,"lane_id":LANE_ID,"source_head":ident["head"],"source_tree":ident["tree"],"bundle_uuid":bid,"authority_sha256":ah,"row_ids_sha256":hash_obj(list(PILOT_IDS)),"record_count":len(rows),"records":rows,"ordered_record_aggregate_sha256":aggregate}; durable_write(b/"manifest.json",m)
    elapsed=time.monotonic()-start;rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    write_ledger(b,{"event":"CLOSEOUT","pid":os.getpid(),"bundle_uuid":bid,"time":utc(),"status":"COMPLETE","record_count":len(rows)})
    return {"bundle_uuid":bid,"row_ids":list(PILOT_IDS),"row_count":len(rows),"completion_count":len(rows),"wall_time_s":elapsed,"peak_rss_bytes":rss,"manifest_sha256":sha(b/"manifest.json"),"ordered_record_aggregate_sha256":m["ordered_record_aggregate_sha256"],"scientific_reducer_ran":False,"source_ordering_calculated":False,"complete_source_triplet":False}

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    for n in ("generate","verify","references","feasibility"):sp.add_parser(n)
    p=sp.add_parser("pilot-select")
    p=sp.add_parser("pilot-run");p.add_argument("--bundle",required=True)
    for n in ("execute-adjudicative","verify-bundle"):
        p=sp.add_parser(n);p.add_argument("--bundle",required=True);p.add_argument("--authority",required=True);p.add_argument("--resume",action="store_true")
    p=sp.add_parser("reduce");p.add_argument("--bundle",required=True);p.add_argument("--authority",required=True);p.add_argument("--output",required=True)
    args=ap.parse_args()
    if args.cmd=="generate": out=generate()
    elif args.cmd=="verify": out=verify_generated()
    elif args.cmd=="references": out=references()
    elif args.cmd=="feasibility": out=feasibility_bounds()
    elif args.cmd=="pilot-select": out={"pilot_ids":list(PILOT_IDS),"complete_source_triplet":False}
    elif args.cmd=="pilot-run": out=pilot_run(args.bundle)
    elif args.cmd=="execute-adjudicative": out=execute(args.bundle,args.authority,args.resume)
    elif args.cmd=="verify-bundle": out=verify_bundle(args.bundle,args.authority)
    else: out=reduce_bundle(args.bundle,args.authority,args.output)
    print(canonical(out),end="")
if __name__=="__main__": main()
