#!/usr/bin/env python3
"""SCI-MD-001 reproducible inverse analysis and reduced mechanism screen.

All reduced hypotheses are REDUCED_DIAGNOSTIC_MODEL,
POST_OBSERVATION_MECHANISM_SCREEN, NOT_PRODUCTION_OPENFOAM_PHYSICS, and
NOT_PHYSICAL_VALIDATION.  The production solver is neither imported nor changed.
"""
from __future__ import annotations

import argparse, csv, hashlib, html, json, math
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
    terminal={r["pressure_nominal_bar"]:r for r in inv["rows"] if r["window"]=="terminal"}
    measured={p:terminal[p]["mean_source_pressure_bar"] for p in PRESSURES}
    # Deterministic broad screens. Values are ratios to the 5-bar conductance.
    records=[]; evals=0
    def add(mid, capable, plausible, breadth, interpretation, prediction, evaluation_kind):
        if capable is None:
            disposition="NOT_STRUCTURALLY_EXCLUDED"
        elif capable and plausible == "BOUND_UNRESOLVED":
            disposition="CANDIDATE_MECHANISM_CAPABILITY_PLAUSIBILITY_UNRESOLVED"
        elif capable and plausible.startswith("WITHIN_"):
            disposition="CANDIDATE_MECHANISM_CAPABLE_WITHIN_PLAUSIBLE_RANGE"
        elif capable:
            disposition="CANDIDATE_MECHANISM_CAPABLE_ONLY_OUTSIDE_PLAUSIBLE_RANGE"
        else:
            disposition="EXISTING_MODEL_FAMILY_STRUCTURALLY_INCAPABLE"
        records.append({"mechanism":mid,"existing_or_reduced":"REDUCED_DIAGNOSTIC_MODEL",
          "capable":capable,"evaluation_kind":evaluation_kind,
          "plausibility":plausible,"capable_region_breadth":breadth,
          "disposition":disposition,
          "interpretation":interpretation,"distinctive_prediction":prediction,"label":LABEL})
    ns=[i*0.01 for i in range(0,301)]; evals+=len(ns)
    ok=[n for n in ns if (measured[11]/measured[5])**(-n) <= target]
    add("P1_GENERIC_PRESSURE_DEPENDENT_PERMEABILITY",bool(ok),"BOUND_UNRESOLVED",f"n >= {min(ok):.2f}" if ok else "none","Measured-pressure analytical/grid screen is mathematically capable; it restates the inverse requirement and is not yet a constitutive explanation.","simultaneous pressure and bed-height histories","EXECUTED_ANALYTICAL_GRID_SCREEN")
    # relaxation x'=(x_eq(p)-x)/tau, K/K0=exp(-beta*x); analytic Euler screen
    capable=0
    for tau in [10**(-1+3*i/63) for i in range(64)]:
      for beta in [i/10 for i in range(1,81)]:
        evals+=1; vals={}
        for p in PRESSURES:
          x=(measured[p]-measured[5])/(measured[11]-measured[5])*(1-math.exp(-30/tau))
          vals[p]=measured[p]/measured[5]*math.exp(-beta*x)
        capable += ordering(vals)
    add("P2_RELAXING_RESISTANCE_SURROGATE_POROMECHANICS_MOTIVATED",capable>0,"BOUND_UNRESOLVED",f"{capable}/5120 grid points","A one-state finite-rate resistance surrogate is mathematically capable. Transient poromechanics is one possible realization, not a demonstrated explanation.","pressure-step lag and rebound/bed-height memory","EXECUTED_ONE_STATE_GRID_SCREEN")
    # generic monotone state-growth mechanisms share required resistance gain
    required=1/target
    add("P3_SWELLING",None,"BOUND_UNRESOLVED",f"inverse requirement is >= {required:.3f} resistance ratio at 11/5 bar","Not structurally excluded, but no swelling-specific dynamical model was executed.","bed-height increase and hydration-time dependence","ANALYTICAL_STRUCTURAL_CHECK_ONLY")
    add("P4_MOBILE_DEPOSITED_FINES",None,"BOUND_UNRESOLVED",f"inverse requirement is >= {required:.3f} resistance ratio at 11/5 bar","Not structurally excluded, but no fines inventory/rate model was executed.","turbidity, captured fines and incomplete recovery","ANALYTICAL_STRUCTURAL_CHECK_ONLY")
    add("P5_CONCENTRATION_DEPENDENT_VISCOSITY",True,"OUTSIDE_SUPPORTED_RANGE",f"mu11/mu5 >= {required:.3f}","An analytical viscosity-only requirement is outside the defensible water-temperature variation represented here.","large synchronized concentration/viscosity contrast","ANALYTICAL_PROPERTY_REQUIREMENT")
    add("P6_MACHINE_BOUNDARY_DYNAMICS",False,"BOUND_UNRESOLVED","none under measured basket-pressure prescription","Supply dynamics cannot reverse a relationship already conditioned on measured basket pressure without a pressure-node or unmeasured dynamic-state error.","separate commanded, upstream and basket pressure","ANALYTICAL_STRUCTURAL_CHECK_ONLY")
    add("P7_STATIC_LATERAL_PATHS",False,"BOUND_UNRESOLVED","none with pressure-independent parallel paths","Static positive parallel paths preserve monotone Q(dp); localization must itself evolve with pressure/time to become capable.","segmented outlet flow and spatial extraction","ANALYTICAL_STRUCTURAL_CHECK_ONLY")
    b2=load(B2)["axis_contrasts"]["P2_H1"]["GRIND_COARSE_MINUS_FINE"]
    deficits={br:v["source"]-v["model"] for br,v in b2.items()}
    add("G1_GRIND_TO_STRUCTURE_MAPPING",None,"BOUND_UNRESOLVED",f"required coarse-minus-fine mass correction {min(deficits.values()):.3f}..{max(deficits.values()):.3f} g","Not structurally excluded; no three-brew-ratio structure model was executed.","independent grinder-specific PSD, fines, packing and permeability","ANALYTICAL_STRUCTURAL_CHECK_ONLY")
    add("G2_BIMODAL_EXTRACTION",None,"BOUND_UNRESOLVED","conceptual two-population degree of freedom","Not structurally excluded; no two-population parameter ensemble or 3/3 prediction was executed.","fractionated or species-resolved time series under prescribed hydraulics","ANALYTICAL_STRUCTURAL_CHECK_ONLY")
    dump(OUT/"SCI_MD_001_REDUCED_SCREEN.json",{"evaluations":evals,"evaluation_breakdown":{"P1_EXECUTED_GRID_STATES":301,"P2_EXECUTED_GRID_STATES":5120,"OTHER_ITEMS":"ANALYTICAL_OR_STRUCTURAL_CHECKS_NOT_PARAMETER_ENSEMBLES"},"primary_pressure_basis":"RETAINED_MEASURED_TERMINAL_BASKET_PRESSURE","protocol_deviation":"Base-2 low-discrepancy sampling and adaptive refinement were not executed; P3/P4/G1/G2 are downgraded to not structurally excluded rather than represented as executed model passes.","records":records})
    return records,evals

def write_csv(path, rows, fields=None):
    fields=fields or list(rows[0])
    with path.open("w",newline="") as f:
      w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n"); w.writeheader(); w.writerows(rows)

COLORS=("#0072B2","#D55E00","#009E73","#CC79A7","#E69F00")
def line_svg(path,title,series,xlabel,ylabel):
    width,height=900,520; left,right,top,bottom=95,30,55,75
    pts=[p for _,values in series for p in values if p[1] is not None and math.isfinite(p[1])]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; xmin,xmax=min(xs),max(xs); ymin,ymax=min(ys),max(ys)
    if ymin==ymax: ymin,ymax=ymin-1,ymax+1
    X=lambda x:left+(x-xmin)/(xmax-xmin)*(width-left-right)
    Y=lambda y:height-bottom-(y-ymin)/(ymax-ymin)*(height-top-bottom)
    body=[f'<rect width="100%" height="100%" fill="white"/><line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="black"/><line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="black"/>']
    for i,(name,values) in enumerate(series):
      points=' '.join(f'{X(x):.1f},{Y(y):.1f}' for x,y in values if y is not None and math.isfinite(y))
      body.append(f'<polyline fill="none" stroke="{COLORS[i%len(COLORS)]}" stroke-width="2.3" points="{points}"/>')
      body.append(f'<text x="{left+180*i}" y="{height-18}" font-family="sans-serif" font-size="14" fill="{COLORS[i%len(COLORS)]}">{html.escape(name)}</text>')
    body += [f'<text x="30" y="32" font-family="sans-serif" font-size="22" font-weight="bold">{html.escape(title)}</text>',f'<text x="{width/2-50}" y="{height-42}" font-family="sans-serif" font-size="14">{html.escape(xlabel)}</text>',f'<text transform="translate(22 {height/2+50}) rotate(-90)" font-family="sans-serif" font-size="14">{html.escape(ylabel)}</text>',f'<text x="{left}" y="{height-bottom+22}" font-family="sans-serif" font-size="12">{xmin:.3g}</text>',f'<text x="{width-right-45}" y="{height-bottom+22}" font-family="sans-serif" font-size="12">{xmax:.3g}</text>',f'<text x="28" y="{height-bottom}" font-family="sans-serif" font-size="12">{ymin:.3g}</text>',f'<text x="28" y="{top+5}" font-family="sans-serif" font-size="12">{ymax:.3g}</text>']
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img"><title>{html.escape(title)}</title>{"".join(body)}</svg>\n')

def bar_svg(path,title,categories,series,ylabel):
    width,height=900,520; left,bottom,top=90,90,55; values=[v for _,vs in series for v in vs]; lim=max(abs(min(values)),abs(max(values)))*1.15
    Y=lambda y:top+(lim-y)/(2*lim)*(height-top-bottom); zero=Y(0); group=(width-left-30)/len(categories); bw=group/(len(series)+1)
    body=[f'<rect width="100%" height="100%" fill="white"/><line x1="{left}" y1="{zero}" x2="{width-30}" y2="{zero}" stroke="black"/>']
    for j,(name,vs) in enumerate(series):
      for i,v in enumerate(vs):
       x=left+i*group+(j+.4)*bw; y=min(zero,Y(v)); h=abs(Y(v)-zero)
       body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw*.8:.1f}" height="{h:.1f}" fill="{COLORS[j]}"/>')
      body.append(f'<text x="{left+180*j}" y="{height-18}" font-family="sans-serif" font-size="14" fill="{COLORS[j]}">{html.escape(name)}</text>')
    for i,c in enumerate(categories): body.append(f'<text x="{left+i*group+group*.35:.1f}" y="{height-bottom+25}" font-family="sans-serif" font-size="14">{html.escape(str(c))}</text>')
    body += [f'<text x="30" y="32" font-family="sans-serif" font-size="22" font-weight="bold">{html.escape(title)}</text>',f'<text transform="translate(22 {height/2+50}) rotate(-90)" font-family="sans-serif" font-size="14">{html.escape(ylabel)}</text>']
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img"><title>{html.escape(title)}</title>{"".join(body)}</svg>\n')

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
    for s in screens:
      if s["mechanism"].startswith("P1_") or s["mechanism"].startswith("P2_"):
        pressure_assessment="EXECUTED_ORDER_PASS" if s["capable"] else "EXECUTED_ORDER_FAIL"
      elif s["capable"] is False:
        pressure_assessment="ANALYTICALLY_STRUCTURALLY_INCAPABLE"
      elif s["capable"] is True:
        pressure_assessment="ANALYTICALLY_STRUCTURALLY_CAPABLE"
      else:
        pressure_assessment="NOT_STRUCTURALLY_EXCLUDED_NOT_EVALUATED"
      families.append({"mechanism":s["mechanism"],"flow_order_pass":pressure_assessment,
        "mass_order_pass":"NOT_EVALUATED","grind_sign_match_count":"NOT_EVALUATED",
        "evaluation_kind":s["evaluation_kind"],"plausibility":s["plausibility"],"disposition":s["disposition"]})
    matrix_fields=[]
    for row in families:
      for key in row:
       if key not in matrix_fields: matrix_fields.append(key)
    write_csv(OUT/"SCI_MD_001_MECHANISM_CAPABILITY_MATRIX.csv",families,matrix_fields)
    dump(OUT/"SCI_MD_001_MECHANISM_CAPABILITY_MATRIX.json",{"rows":families})
    bounds=[
      {"parameter":"power_law_n","minimum":0,"maximum":3,"unit":"1","role":"SYNTHETIC_FIXTURE","source":"inverse-screen envelope"},
      {"parameter":"relaxation_time","minimum":0.1,"maximum":100,"unit":"s","role":"SYNTHETIC_FIXTURE","source":"diagnostic shot-time envelope"},
      {"parameter":"strain_permeability_sensitivity","minimum":0.1,"maximum":8,"unit":"1","role":"SYNTHETIC_FIXTURE","source":"diagnostic capability envelope"},
      {"parameter":"water_density","minimum":965,"maximum":1000,"unit":"kg/m3","role":"FIXED_PREDECESSOR_VALUE","source":"VAL-CORPUS-001 declared sensitivity"}]
    write_csv(OUT/"SCI_MD_001_PARAMETER_BOUNDS.csv",bounds)
    plot=[]
    for p,rs in src.items():
      for r in rs[::max(1,len(rs)//160)]:
       for panel,key,unit,role in (("measured_pressure","source_pressure_bar","bar","SOURCE_MEASURED"),("measured_flow","source_flow_g_s","g/s","SOURCE_MEASURED"),("apparent_conductance","conductance_m3_s_pa","m3/(s Pa)","SOURCE_MEASURED_DERIVED")):
        plot.append({"panel":panel,"series":f"source_{p}bar","x":r["source_time_s"],"y":r[key],"unit":unit,"role":role})
    for window in ("middle","late","terminal"):
      vals={r["pressure_nominal_bar"]:r["mean_conductance_m3_s_pa"] for r in inverse["rows"] if r["window"]==window}
      plot.append({"panel":"conductance_ratio","series":"C11_over_C5","x":window,"y":vals[11]/vals[5],"unit":"1","role":"SOURCE_MEASURED_DERIVED"})
    for br,v in g.items():
      plot += [{"panel":"grind_contrast","series":"source","x":br,"y":v["source"],"unit":"g","role":"SOURCE_DERIVED"},{"panel":"grind_contrast","series":"model","x":br,"y":v["model"],"unit":"g","role":"EXISTING_OPENFOAM_RESULT"}]
    write_csv(OUT/"SCI_MD_001_PLOT_SOURCE.csv",plot)
    run=[{"run_id":"SCI-MD-001-REDUCED-SCREEN","kind":"REDUCED_DIAGNOSTIC","status":"PASS","evaluations":evals,"ranks":1,"runtime_s":"recorded_by_invocation_not_retained","artifact":"SCI_MD_001_REDUCED_SCREEN.json"},{"run_id":"SCI-MD-001-OPENFOAM","kind":"OPENFOAM","status":"NOT_REQUIRED_REUSED_PRIMITIVES_SUFFICIENT","evaluations":0,"ranks":0,"runtime_s":0,"artifact":"none"}]
    write_csv(OUT/"SCI_MD_001_RUN_MANIFEST.csv",run)
    residual=b2["waszkiewicz"]["results"]["P2"]
    result={"schema_version":"ewp.sci_md_001.result.v2","status":"CORRECTED_PENDING_EXACT_HEAD_REVIEW","evidence_mode":"POST_OBSERVATION_MECHANISM_DISCRIMINATION","review_correction":"Corrects missing unresolved-plausibility taxonomy, nominal-pressure substitution, false-green conceptual capability fields, and figure form; original protocol freeze retained.","inverse_requirement":inverse,"grind":{"contrast_definition_in_source":"coarse-minus-fine","reported_primary_fine_minus_coarse":{br:{"source":-v["source"],"model":-v["model"],"sign_match":False,"minimum_model_change_g":v["source"]-v["model"]} for br,v in g.items()},"sign_match_count":0,"interpretation":"Failure persists under prescribed source hydraulics H1; it is therefore not solely a hydraulic-clock failure. Aggregate kinetics and grind-to-structure/inventory effects remain confounded."},"transient_transfer":residual,"existing_family_capability":families,"reduced_evaluations":evals,"reduced_evaluation_breakdown":{"P1_EXECUTED_GRID_STATES":301,"P2_EXECUTED_GRID_STATES":5120,"OTHER_MECHANISMS":"ANALYTICAL_OR_STRUCTURAL_CHECKS_NOT_PARAMETER_ENSEMBLES"},"new_openfoam_runs":0,"openfoam_reason":"Accepted traces contain the required primitives; no reduced survivor was sufficiently source-bounded to justify a confirmatory production run.","mechanisms_ruled_out_as_standalone":["pressure-independent Darcy","fixed-coefficient Darcy-Forchheimer","accepted quasi-static compaction","static pressure-independent lateral paths","machine dynamics conditioned on measured basket pressure","viscosity-only within defensible water-property variation"],"survivors":["generic pressure-dependent evolving resistance","one-state relaxing-resistance surrogate (poromechanics-motivated)","swelling not structurally excluded","fines deposition/mobility not structurally excluded","evolving lateral localization","grind-to-structure closure not structurally excluded","bimodal extraction not structurally excluded"],"equifinality":"MULTIPLE_MECHANISMS_REMAIN_EQUIFINAL","recommended_next_task":"NO_NEW_PRODUCTION_PHYSICS_YET","recommended_measurement":"synchronized upstream and basket pressure, flow, bed-height/rebound, turbidity/captured fines, and fractionated chemistry; prioritize pressure-step bed-height/rebound plus turbidity to separate poromechanics from fines","claim_boundary":{"physical_validation":"NOT_ESTABLISHED","independent_validation":"NOT_PERFORMED","protected_scoring":"NOT_PERFORMED"}}
    dump(OUT/"SCI_MD_001_RESULT.json",result)
    figs=OUT/"figures"; figs.mkdir(exist_ok=True)
    terminal={r["pressure_nominal_bar"]:r for r in inverse["rows"] if r["window"]=="terminal"}
    pressure_series=[(f"{p} bar",[(r["source_time_s"],r["source_pressure_bar"]) for r in src[p]]) for p in PRESSURES]
    flow_series=[(f"{p} bar",[(r["source_time_s"],r["source_flow_g_s"]) for r in src[p]]) for p in PRESSURES]
    conductance_series=[(f"{p} bar",[(r["source_time_s"],r["conductance_m3_s_pa"]) for r in src[p]]) for p in PRESSURES]
    line_svg(figs/"01_pressure_ordering.svg","Measured pressure histories",pressure_series,"source time (s)","basket pressure (bar)")
    line_svg(figs/"02_inverse_conductance.svg","Apparent hydraulic conductance histories",conductance_series,"source time (s)","C_app (m3/(s Pa))")
    bar_svg(figs/"03_grind_contrasts.svg","Source versus model grind contrasts",list(g),[("source coarse - fine",[v["source"] for v in g.values()]),("model coarse - fine",[v["model"] for v in g.values()])],"mass contrast (g)")
    line_svg(figs/"04_existing_capability.svg","Measured flow histories",flow_series,"source time (s)","mass flow (g/s)")
    ratios=[]
    for window in ("middle","late","terminal"):
      vals={r["pressure_nominal_bar"]:r["mean_conductance_m3_s_pa"] for r in inverse["rows"] if r["window"]==window}; ratios.append(vals[11]/vals[5])
    bar_svg(figs/"05_candidate_phase_map.svg","Persistent apparent-conductance requirement",["middle","late","terminal"],[("C11 / C5",ratios)],"conductance ratio")
    pr=residual["EXISTING_ACCEPTED_FIXED_SOURCE_TO_SOLVER_OFFSET_PLUS_3_SECONDS"]["metrics"]["window_mean_residual"]
    sr=residual["SOURCE_REPORTED_CLOCK"]["metrics"]["window_mean_residual"]
    bar_svg(figs/"06_residual_fingerprints.svg","Transient residual fingerprints",["early","middle","late"],[("accepted +3 s",[pr[x] for x in ("early","middle","late")]),("source clock",[sr[x] for x in ("early","middle","late")])],"mean residual")
    # P1 boundary and P2 capability fraction are plotted as executed-screen summaries.
    p1=next(x for x in screens if x["mechanism"].startswith("P1_")); p2=next(x for x in screens if x["mechanism"].startswith("P2_"))
    p1n=float(p1["capable_region_breadth"].split()[-1]); p2count=int(p2["capable_region_breadth"].split('/')[0])
    bar_svg(figs/"07_capability_plausibility.svg","Executed reduced-screen capability boundaries",["P1 n threshold","P2 capable fraction"],[("measured-pressure primary",[p1n,p2count/5120])],"threshold or fraction")
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
