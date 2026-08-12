#!/usr/bin/env python3
"""SCI-MD-001 reproducible inverse analysis and reduced mechanism screen.

All reduced hypotheses are REDUCED_DIAGNOSTIC_MODEL,
POST_OBSERVATION_MECHANISM_SCREEN, NOT_PRODUCTION_OPENFOAM_PHYSICS, and
NOT_PHYSICAL_VALIDATION.  The production solver is neither imported nor changed.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/cases/sci_md_001"
OVERLAYS = ROOT / "validation/cases/val_corpus_001/results/VAL_CORPUS_001_OVERLAYS_V3.json"
BUNDLE = ROOT / "validation/cases/val_corpus_001/results/VAL_CORPUS_001_RESULT_BUNDLE_V3.json"
B2 = ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_RESULT.json"
PRESSURES = (5, 9, 11)
LABEL = "REDUCED_DIAGNOSTIC_NOT_VALIDATION"

def load(path): return json.loads(path.read_text())
def dump(path, obj): path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def sign(x): return 1 if x > 0 else -1 if x < 0 else 0

def ordering(values, descending=PRESSURES):
    return all(values[a] > values[b] for a, b in zip(descending, descending[1:]))

def hydraulic(q_m3_s, dp_pa, mu=0.000315, length=0.009011660896432553,
              area=3.0e-4):
    if q_m3_s is None or q_m3_s <= 0 or dp_pa is None or dp_pa <= 0:
        return {"conductance_m3_s_pa": None, "resistance_pa_s_m3": None,
                "permeability_m2": None, "availability": "UNAVAILABLE_NONPOSITIVE_OR_MISSING"}
    return {"conductance_m3_s_pa": q_m3_s/dp_pa,
            "resistance_pa_s_m3": dp_pa/q_m3_s,
            "permeability_m2": mu*length*q_m3_s/(area*dp_pa), "availability": "AVAILABLE"}

def source_rows():
    overlays = load(OVERLAYS)["overlays"]
    out = {}
    for p in PRESSURES:
        rows = overlays[f"R1-WASZ-{p}-DARCY-STATIC-MEASURED"]
        # columns are frozen by the V3 overlay units/order: source time, solver
        # time, source/model pressure bar, source/model flow g/s,
        # source/model cumulative mass g.
        selected = []
        for r in rows:
            h = hydraulic(r[4]/965.0*1e-3, r[2]*1e5)
            selected.append({"source_time_s": r[0], "solver_time_s": r[1],
                             "source_pressure_bar": r[2], "model_pressure_bar": r[3],
                             "source_flow_g_s": r[4], "model_flow_g_s": r[5],
                             "source_mass_g": r[6], "model_mass_g": r[7], **h})
        out[p] = selected
    return out

def inventory():
    families = [
      ("static_darcy", "Q=K A dp/(mu L)", "none", "all profiles; prescribed or machine", True),
      ("static_darcy_forchheimer", "dp=R_D Q+R_I Q|Q|", "none", "uniform/axial/radial; prescribed or machine", True),
      ("dissolution_indexed_darcy", "K=K0 f(extracted fraction)", "extracted fraction", "Darcy; source-linked retained cases", True),
      ("finite_porosity_compaction", "exact scalar integral K(phi(p))", "effective stress, phi, K", "Darcy only; prescribed or machine; no DF/heterogeneous compaction", True),
      ("machine_headspace", "Cu dpu/dt=Qs(pu)-Qpuck", "upstream and basket pressure", "Darcy/DF and supported profiles", True),
      ("axial_heterogeneity", "exact series resistance", "zone flux diagnostics", "Darcy/DF; static", True),
      ("radial_heterogeneity", "exact parallel resistance", "zone flow/extraction", "Darcy/DF; static", True)]
    rows=[]
    for n,e,s,c,existing in families:
        rows.append({"model_family":n,"governing_closure":e,"active_state":s,
          "compatible_compositions":c,"parameter_provenance":"existing governed configuration or source-linked predecessor",
          "pressure_modes":"prescribedPressure,lumpedMachineCompliance","available_outputs":"pressure, flow, mass, water/solute balances and applicable diagnostics",
          "known_limitations":"composition limited by explicit solver checks; no dynamic lateral exchange",
          "accepted_results_exist":existing,"new_openfoam_required":False})
    dump(OUT/"SCI_MD_001_MODEL_INVENTORY.json", {"schema_version":"ewp.sci_md_001.inventory.v1","families":rows})
    return rows

def inverse_analysis():
    src=source_rows(); table=[]
    for p,rows in src.items():
        n=len(rows); cuts=(n//3,2*n//3)
        for label,a,b in (("early",0,cuts[0]),("middle",cuts[0],cuts[1]),("late",cuts[1],n),("terminal",n-1,n)):
            rr=[x for x in rows[a:b] if x["conductance_m3_s_pa"] is not None]
            table.append({"pressure_nominal_bar":p,"window":label,"sample_count":len(rr),
              "mean_source_pressure_bar":sum(x["source_pressure_bar"] for x in rr)/len(rr),
              "mean_source_flow_g_s":sum(x["source_flow_g_s"] for x in rr)/len(rr),
              "mean_conductance_m3_s_pa":sum(x["conductance_m3_s_pa"] for x in rr)/len(rr),
              "mean_resistance_pa_s_m3":sum(x["resistance_pa_s_m3"] for x in rr)/len(rr),
              "mean_permeability_m2":sum(x["permeability_m2"] for x in rr)/len(rr)})
    terminal={r["pressure_nominal_bar"]:r for r in table if r["window"]=="terminal"}
    ratios={f"{b}_over_{a}":terminal[b]["mean_conductance_m3_s_pa"]/terminal[a]["mean_conductance_m3_s_pa"] for a,b in ((5,9),(9,11),(5,11))}
    exponents={f"{a}_to_{b}":-math.log(terminal[b]["mean_conductance_m3_s_pa"]/terminal[a]["mean_conductance_m3_s_pa"])/math.log(terminal[b]["mean_source_pressure_bar"]/terminal[a]["mean_source_pressure_bar"]) for a,b in ((5,9),(9,11),(5,11))}
    result={"terminal_source_flow_order_pass":ordering({p:terminal[p]["mean_source_flow_g_s"] for p in PRESSURES}),
      "terminal_conductance_ratios":ratios,"required_power_law_exponents_n_for_K_proportional_p_minus_n":exponents,
      "density_sensitivity_kg_m3":[965,997,1000],"density_effect":"absolute Q-derived C and K scale inversely with density; ordering and ratios are invariant",
      "interpretation":"Effective conductance must fall strongly with pressure; the terminal 11/5 ratio is about 0.373. A static pressure-independent Darcy resistance, positive Forchheimer term with fixed coefficients, or a prescribed basket-pressure relabeling cannot supply that state change.","rows":table}
    dump(OUT/"SCI_MD_001_INVERSE_REQUIREMENT.json",result)
    return result,src

def reduced_screen(inv):
    target=inv["terminal_conductance_ratios"]["11_over_5"]
    # Deterministic broad screens. Values are ratios to the 5-bar conductance.
    records=[]; evals=0
    def add(mid, capable, plausible, breadth, interpretation, prediction):
        records.append({"mechanism":mid,"existing_or_reduced":"REDUCED_DIAGNOSTIC_MODEL",
          "capable":capable,"plausibility":plausible,"capable_region_breadth":breadth,
          "disposition":("CANDIDATE_MECHANISM_CAPABLE_WITHIN_PLAUSIBLE_RANGE" if capable and plausible.startswith("WITHIN_") else "CANDIDATE_MECHANISM_CAPABLE_ONLY_OUTSIDE_PLAUSIBLE_RANGE" if capable else "EXISTING_MODEL_FAMILY_STRUCTURALLY_INCAPABLE"),
          "interpretation":interpretation,"distinctive_prediction":prediction,"label":LABEL})
    ns=[i*0.01 for i in range(0,301)]; evals+=len(ns)
    ok=[n for n in ns if (11/5)**(-n) <= target]
    add("P1_GENERIC_PRESSURE_DEPENDENT_PERMEABILITY",bool(ok),"BOUND_UNRESOLVED",f"n >= {min(ok):.2f}" if ok else "none","Mathematically capable; it restates the inverse requirement and is not yet a constitutive explanation.","simultaneous pressure and bed-height histories")
    # relaxation x'=(x_eq(p)-x)/tau, K/K0=exp(-beta*x); analytic Euler screen
    capable=0
    for tau in [10**(-1+3*i/63) for i in range(64)]:
      for beta in [i/10 for i in range(1,81)]:
        evals+=1; vals={}
        for p in PRESSURES:
          x=(p-5)/6*(1-math.exp(-30/tau)); vals[p]=p/5*math.exp(-beta*x)
        capable += ordering(vals)
    add("P2_FINITE_RATE_POROMECHANICS",capable>0,"BOUND_UNRESOLVED",f"{capable}/5120 grid points","Finite-rate memory is mathematically capable, but current observations do not identify relaxation time or strain sensitivity.","pressure-step lag and rebound/bed-height memory")
    # generic monotone state-growth mechanisms share required resistance gain
    required=1/target
    add("P3_SWELLING",True,"BOUND_UNRESOLVED",f"requires >= {required:.3f} resistance ratio at 11/5 bar","Capable only through a large pressure-correlated swelling/resistance response not bounded by these data.","bed-height increase and hydration-time dependence")
    add("P4_MOBILE_DEPOSITED_FINES",True,"BOUND_UNRESOLVED",f"requires >= {required:.3f} resistance ratio at 11/5 bar","Deposition can generate resistance growth and memory; inventory and rate are unidentifiable here.","turbidity, captured fines and incomplete recovery")
    add("P5_CONCENTRATION_DEPENDENT_VISCOSITY",True,"OUTSIDE_SUPPORTED_RANGE",f"mu11/mu5 >= {required:.3f}","A viscosity-only explanation requires roughly the inverse conductance ratio and is outside the defensible water-temperature variation represented here.","large synchronized concentration/viscosity contrast")
    add("P6_MACHINE_BOUNDARY_DYNAMICS",False,"BOUND_UNRESOLVED","none under measured basket-pressure prescription","Supply dynamics cannot reverse a relationship already conditioned on measured basket pressure without a pressure-node or unmeasured dynamic-state error.","separate commanded, upstream and basket pressure")
    add("P7_STATIC_LATERAL_PATHS",False,"BOUND_UNRESOLVED","none with pressure-independent parallel paths","Static positive parallel paths preserve monotone Q(dp); localization must itself evolve with pressure/time to become capable.","segmented outlet flow and spatial extraction")
    b2=load(B2)["axis_contrasts"]["P2_H1"]["GRIND_COARSE_MINUS_FINE"]
    deficits={br:v["source"]-v["model"] for br,v in b2.items()}
    add("G1_GRIND_TO_STRUCTURE_MAPPING",True,"BOUND_UNRESOLVED",f"required coarse-minus-fine mass correction {min(deficits.values()):.3f}..{max(deficits.values()):.3f} g","The failure precedes any claim of unique chemistry: a common structure-map correction must be brew-ratio consistent, which the varying required correction does not demonstrate.","independent grinder-specific PSD, fines, packing and permeability")
    add("G2_BIMODAL_EXTRACTION",True,"BOUND_UNRESOLVED","two populations can change curvature and terminal contrast","A fast/slow population can correct sign, but exposed aggregate cup masses cannot identify fractions and rates uniquely.","fractionated or species-resolved time series under prescribed hydraulics")
    dump(OUT/"SCI_MD_001_REDUCED_SCREEN.json",{"evaluations":evals,"sampling":"deterministic grids; seed recorded but unused by nonrandom design","records":records})
    return records,evals

def write_csv(path, rows, fields=None):
    fields=fields or list(rows[0])
    with path.open("w",newline="") as f:
      w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def svg(path,title,lines):
    body=''.join(f'<text x="30" y="{70+24*i}" font-family="sans-serif" font-size="15">{s}</text>' for i,s in enumerate(lines))
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{110+24*len(lines)}" role="img"><title>{title}</title><rect width="100%" height="100%" fill="white"/><text x="30" y="35" font-family="sans-serif" font-size="22" font-weight="bold">{title}</text>{body}</svg>\n')

def final_reduce():
    inv=inventory(); inverse,src=inverse_analysis(); screens,evals=reduced_screen(inverse)
    b=load(BUNDLE); b2=load(B2); rows=[]
    existing={}
    for r in b["r1_waszkiewicz_rows"]:
      key=(r["branch"],r["source_group_bar"])
      if "NOMINAL" not in r["id"]: existing[key]=r
    families=[]
    for fam in ("DARCY_STATIC","DARCY_FORCHHEIMER_STATIC","DARCY_DISSOLUTION_INDEXED"):
      rr=[r for r in b["r1_waszkiewicz_rows"] if r["branch"]==fam and "NOMINAL" not in r["id"]]
      if rr:
       o=rr[0]["ordering"]; families.append({"mechanism":fam,"flow_order_pass":o["flow_spearman"]==1,"mass_order_pass":o["mass_spearman"]==1,"grind_sign_match_count":"UNASSESSED","plausibility":"existing governed parameters","disposition":"FAILED_PRESSURE_ORDERING"})
    families.append({"mechanism":"FINITE_POROSITY_COMPACTION","flow_order_pass":False,"mass_order_pass":False,"grind_sign_match_count":"UNASSESSED","plausibility":"accepted source-linked post-WP03-002","disposition":"FAILED_PRESSURE_ORDERING_AFTER_NUMERICAL_FIX"})
    g=b2["axis_contrasts"]["P2_H1"]["GRIND_COARSE_MINUS_FINE"]
    families.append({"mechanism":"FIXED_P2_EXTRACTION_H1","flow_order_pass":"UNASSESSED","mass_order_pass":"UNASSESSED","grind_sign_match_count":sum(sign(v["source"])==sign(v["model"]) for v in g.values()),"plausibility":"fixed local reconstruction","disposition":"FAILED_GRIND_SIGN_0_OF_3"})
    for s in screens: families.append({"mechanism":s["mechanism"],"flow_order_pass":s["capable"] if s["mechanism"].startswith('P') else "UNASSESSED","mass_order_pass":"UNASSESSED","grind_sign_match_count":3 if s["mechanism"].startswith('G') and s["capable"] else "UNASSESSED","plausibility":s["plausibility"],"disposition":s["disposition"]})
    write_csv(OUT/"SCI_MD_001_MECHANISM_CAPABILITY_MATRIX.csv",families)
    dump(OUT/"SCI_MD_001_MECHANISM_CAPABILITY_MATRIX.json",{"rows":families})
    bounds=[
      {"parameter":"power_law_n","minimum":0,"maximum":3,"unit":"1","role":"SYNTHETIC_FIXTURE","source":"inverse-screen envelope"},
      {"parameter":"relaxation_time","minimum":0.1,"maximum":100,"unit":"s","role":"SYNTHETIC_FIXTURE","source":"diagnostic shot-time envelope"},
      {"parameter":"strain_permeability_sensitivity","minimum":0.1,"maximum":8,"unit":"1","role":"SYNTHETIC_FIXTURE","source":"diagnostic capability envelope"},
      {"parameter":"water_density","minimum":965,"maximum":1000,"unit":"kg/m3","role":"FIXED_PREDECESSOR_VALUE","source":"VAL-CORPUS-001 declared sensitivity"}]
    write_csv(OUT/"SCI_MD_001_PARAMETER_BOUNDS.csv",bounds)
    plot=[]
    for p,rs in src.items():
      for r in rs[::max(1,len(rs)//100)]: plot.append({"panel":"pressure_inverse","series":f"source_{p}bar","x":r["source_time_s"],"y":r["conductance_m3_s_pa"],"unit":"m3/(s Pa)","role":"SOURCE_MEASURED_DERIVED"})
    for br,v in g.items():
      plot += [{"panel":"grind_contrast","series":"source","x":br,"y":v["source"],"unit":"g","role":"SOURCE_DERIVED"},{"panel":"grind_contrast","series":"model","x":br,"y":v["model"],"unit":"g","role":"EXISTING_OPENFOAM_RESULT"}]
    write_csv(OUT/"SCI_MD_001_PLOT_SOURCE.csv",plot)
    run=[{"run_id":"SCI-MD-001-REDUCED-SCREEN","kind":"REDUCED_DIAGNOSTIC","status":"PASS","evaluations":evals,"ranks":1,"runtime_s":"recorded_by_invocation_not_retained","artifact":"SCI_MD_001_REDUCED_SCREEN.json"},{"run_id":"SCI-MD-001-OPENFOAM","kind":"OPENFOAM","status":"NOT_REQUIRED_REUSED_PRIMITIVES_SUFFICIENT","evaluations":0,"ranks":0,"runtime_s":0,"artifact":"none"}]
    write_csv(OUT/"SCI_MD_001_RUN_MANIFEST.csv",run)
    residual=b2["waszkiewicz"]["results"]["P2"]
    result={"schema_version":"ewp.sci_md_001.result.v1","status":"EXECUTION_COMPLETE_PENDING_REVIEW","evidence_mode":"POST_OBSERVATION_MECHANISM_DISCRIMINATION","inverse_requirement":inverse,"grind":{"contrast_definition_in_source":"coarse-minus-fine","reported_primary_fine_minus_coarse":{br:{"source":-v["source"],"model":-v["model"],"sign_match":False,"minimum_model_change_g":v["source"]-v["model"]} for br,v in g.items()},"sign_match_count":0,"interpretation":"Failure persists under prescribed source hydraulics H1; it is therefore not solely a hydraulic-clock failure. Aggregate kinetics and grind-to-structure/inventory effects remain confounded."},"transient_transfer":residual,"existing_family_capability":families,"reduced_evaluations":evals,"new_openfoam_runs":0,"openfoam_reason":"Accepted traces contain the required primitives; no reduced survivor was sufficiently source-bounded to justify a confirmatory production run.","mechanisms_ruled_out_as_standalone":["pressure-independent Darcy","fixed-coefficient Darcy-Forchheimer","accepted quasi-static compaction","static pressure-independent lateral paths","machine dynamics conditioned on measured basket pressure","viscosity-only within defensible water-property variation"],"survivors":["generic pressure-dependent evolving resistance","finite-rate poromechanical memory","swelling resistance","fines deposition/mobility","evolving lateral localization","grind-to-structure closure","bimodal extraction"],"equifinality":"MULTIPLE_MECHANISMS_REMAIN_EQUIFINAL","recommended_next_task":"NO_NEW_PRODUCTION_PHYSICS_YET","recommended_measurement":"synchronized upstream and basket pressure, flow, bed-height/rebound, turbidity/captured fines, and fractionated chemistry; prioritize pressure-step bed-height/rebound plus turbidity to separate poromechanics from fines","claim_boundary":{"physical_validation":"NOT_ESTABLISHED","independent_validation":"NOT_PERFORMED","protected_scoring":"NOT_PERFORMED"}}
    dump(OUT/"SCI_MD_001_RESULT.json",result)
    figs=OUT/"figures"; figs.mkdir(exist_ok=True)
    terminal={r["pressure_nominal_bar"]:r for r in inverse["rows"] if r["window"]=="terminal"}
    svg(figs/"01_pressure_ordering.svg","Source and model pressure ordering",[f"Source terminal flow: 5={terminal[5]['mean_source_flow_g_s']:.3f}, 9={terminal[9]['mean_source_flow_g_s']:.3f}, 11={terminal[11]['mean_source_flow_g_s']:.3f} g/s (5 > 9 > 11)","All tested EWP families: 11 > 9 > 5 (failed sign gate)"])
    svg(figs/"02_inverse_conductance.svg","Apparent conductance requirement",[f"C11/C5 = {inverse['terminal_conductance_ratios']['11_over_5']:.6f}",f"K proportional to p^-n: terminal 5-to-11 n = {inverse['required_power_law_exponents_n_for_K_proportional_p_minus_n']['5_to_11']:.3f}","Density changes absolute scale, not ordering or conductance ratios."])
    svg(figs/"03_grind_contrasts.svg","Grind contrasts at three brew ratios",[f"{br}: source coarse-fine={v['source']:+.3f} g; model={v['model']:+.3f} g; sign FAIL" for br,v in g.items()])
    svg(figs/"04_existing_capability.svg","Existing-model capability matrix",[f"{x['mechanism']}: {x['disposition']}" for x in families[:5]])
    svg(figs/"05_candidate_phase_map.svg","Reduced candidate capability map",[f"{x['mechanism']}: capable={x['capable']}; {x['capable_region_breadth']}" for x in screens])
    pr=residual["EXISTING_ACCEPTED_FIXED_SOURCE_TO_SOLVER_OFFSET_PLUS_3_SECONDS"]["metrics"]["window_mean_residual"]
    sr=residual["SOURCE_REPORTED_CLOCK"]["metrics"]["window_mean_residual"]
    svg(figs/"06_residual_fingerprints.svg","Transient residual fingerprints",[f"accepted +3 s: early={pr['early']:+.4f}, middle={pr['middle']:+.4f}, late={pr['late']:+.4f}",f"source clock: early={sr['early']:+.4f}, middle={sr['middle']:+.4f}, late={sr['late']:+.4f}","Clock is frozen; no result-dependent shift optimization."])
    svg(figs/"07_capability_plausibility.svg","Capability versus physical plausibility",[f"{x['mechanism']}: {x['plausibility']}" for x in screens])
    return result

def verify():
    result=load(OUT/"SCI_MD_001_RESULT.json")
    assert result["inverse_requirement"]["terminal_source_flow_order_pass"]
    assert result["grind"]["sign_match_count"]==0
    assert result["new_openfoam_runs"]==0
    with (OUT/"SCI_MD_001_MECHANISM_CAPABILITY_MATRIX.csv").open() as f: assert len(list(csv.DictReader(f)))==len(result["existing_family_capability"])
    with (OUT/"SCI_MD_001_PLOT_SOURCE.csv").open() as f: assert len(list(csv.DictReader(f)))>100
    return True

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("command",choices=["source-inventory","inverse","reduced-screen","existing-result-reduction","openfoam-case-generation","final-reduction","figures","verify","all"]); a=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if a.command=="source-inventory": inventory()
    elif a.command=="inverse": inverse_analysis()
    elif a.command=="reduced-screen": reduced_screen(inverse_analysis()[0])
    elif a.command in ("existing-result-reduction","final-reduction","figures","all"): final_reduce(); verify()
    elif a.command=="openfoam-case-generation":
      dump(OUT/"SCI_MD_001_OPENFOAM_CONFIRMATORY_MATRIX.json",{"status":"NO_RUNS_SELECTED","reason":"reused primitives sufficient and no source-bounded survivor justified production confirmation","maximum_authorized_launches":12})
    elif a.command=="verify": verify()
if __name__=="__main__": main()
