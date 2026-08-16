#!/usr/bin/env python3
"""Prospective matrix generator for SCI-MD-002A (no trajectories in freeze mode)."""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/cases/sci_md_002a"
PRESSURES = (5, 9, 11)
PCS = (1100000, 1239155, 1500000, 2000000, 3000000)
THETAS = (0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0)

def canonical_json(obj): return json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rows():
    result=[]
    def add(arm, model, pressure="NA", pc="NA", theta="NA", waveform="SOURCE", boundary="PRESCRIBED_BASKET_PRESSURE"):
        cid=f"{arm}-{model}-P{pressure}-PC{pc}-TH{theta}-{waveform}-{boundary}"
        result.append({"case_id":cid,"arm":arm,"model":model,"pressure_group_bar":pressure,"critical_pressure_pa":pc,"theta_c":theta,"waveform":waveform,"boundary_mode":boundary})
    for model,wave in (("TPM_DISABLED_FIXED_HYDRAULICS","STEP"),("TPM_QUASI_STATIC_EQUILIBRIUM","STEP"),("TPM_SINGLE_MODE_TRANSIENT","STEP"),("TPM_SINGLE_MODE_TRANSIENT","UNLOAD"),("MACHINE_ONLY","STEP")):
        add("C0_ANALYTICAL_CONTROLS",model,9,1239155,0.1,wave)
    for pc in PCS:
        for p in PRESSURES: add("E1_EQUILIBRIUM_PRESSURE_SCREEN","TPM_QUASI_STATIC_EQUILIBRIUM",p,pc,"QUASI_STATIC_LIMIT")
    for pc in PCS:
        for th in THETAS:
            for wave in ("STEP","RAMP","HOLD","UNLOAD","PULSE"): add("T1_SYNTHETIC_TRANSIENT_SIGNATURES","TPM_SINGLE_MODE_TRANSIENT",9,pc,th,wave)
            for p in PRESSURES: add("S1_SOURCE_PRESSURE_SCREEN","TPM_SINGLE_MODE_TRANSIENT",p,pc,th)
            for p in PRESSURES: add("S2_MACHINE_TRANSFER","TPM_SINGLE_MODE_TRANSIENT",p,pc,th,"SOURCE","LUMPED_MACHINE_COMPLIANCE")
            for p in PRESSURES: add("R1_GENERIC_RELAXING_RESISTANCE_CONTROL","GENERIC_RELAXING_RESISTANCE",p,pc,th)
            for wave in ("UNLOAD","PULSE"): add("U1_UNLOADING_MEASUREMENT_DESIGN","TPM_SINGLE_MODE_TRANSIENT",9,pc,th,wave)
    return result

def protocol(matrix_hash=None):
    return {"schema_version":"ewp.sci_md_002a.protocol.v1","status":"PROSPECTIVE_FROZEN_BEFORE_ADJUDICATIVE_EXECUTION","task_id":"SCI-MD-002A","issue":72,"change_declaration":"NO_GOVERNING_PHYSICS_CHANGE","evidence_class":"POST_OBSERVATION_MECHANISM_DISCRIMINATION","models":["TPM_DISABLED_FIXED_HYDRAULICS","TPM_QUASI_STATIC_EQUILIBRIUM","TPM_SINGLE_MODE_TRANSIENT"],"state_equation":"tau_c*d(sigma_c)/dt=delta_p_basket_to_outlet-sigma_c","equilibrium_mapping":"accepted WP03 finite-porosity depth-resolved scalar integral evaluated at sigma_c; epsilon_bulk=1-bed_height_ratio(sigma_c)","pressure_nodes":{"drive":"BASKET_OR_PUCK_INLET_GAUGE minus BASKET_BOTTOM_AMBIENT_GAUGE","sign":"positive compression"},"fixed_primitives":{"phi0":0.4,"k0_m2":"9_bar_scale_only_anchor","mu_pa_s":0.000315,"bed_depth_m":0.01,"basket_area_m2":0.002463008640414398,"density_kg_m3":965},"parameter_bounds":{"critical_pressure_pa":list(PCS),"theta_c":list(THETAS),"shot_scale_s":100.0,"provenance":{"1239155":"SOURCE_DERIVED_EXISTING_CLOSURE","other_pc_levels":"SYNTHETIC_SCREEN_BOUND","theta_levels":"SYNTHETIC_SCREEN_BOUND"}},"source":{"overlays":"validation/cases/val_corpus_001/results/VAL_CORPUS_001_OVERLAYS_V3.json","groups":[5,9,11],"alignment":"unchanged source clock; accepted presentation clock +3 s only where predecessor already uses it","calibration":"one 9-bar multiplicative hydraulic scale; 5/11 bar transfer","grind_arm":"NOT_EXECUTED_UNLESS_GOVERNED_INITIAL_STRUCTURE_MAPPING_EXISTS"},"numerics":{"integrator":"backward_euler_for_state_and_machine","base_dt_s":0.05,"refined_dt_s":0.025,"relative_tolerance":1e-9,"output_dt_s":0.1},"validity":{"pc_strictly_greater_than_effective_state":True,"bed_height_positive":True,"porosity_interval":"0<phi<=phi0","permeability_positive":True,"no_clipping":True},"gate_order":["ARTIFACT_AND_NUMERICAL_VALIDITY","RESISTANCE_SIGN","PRESSURE_ORDERING","PHYSICAL_BOUNDS","GRIND_DIRECTION_OR_NOT_IDENTIFIABLE","TEMPORAL_SHAPE","TRANSFER","DISTINCTIVENESS","AGGREGATE_ERROR"],"budgets":{"pilot_max":64,"initial_parameter_sets":35,"refined_parameter_sets_max":0,"source_trajectories":210,"total_trajectories":400,"workers":"min(16,floor(0.25*logical_cpu_count))","memory_gib":16,"gpu":0,"target_hours":4,"review_hours":8},"stop_rules":["SOURCE_MATRIX_UNRESOLVED","RIGHTS_UNCLEAR","EFFECTIVE_STRESS_MAPPING_UNRESOLVED","HASH_MISMATCH","NONFINITE_OR_INVALID_STATE","CONSERVATION_FAILURE","REFINEMENT_CHANGES_GATE","EXECUTED_SOURCE_MISMATCH"],"matrix_sha256":matrix_hash,"claim_boundary":{"model_class":"REDUCED_DIAGNOSTIC_TRANSIENT_CONSOLIDATION_MODEL","production_openfoam_physics":"UNCHANGED","physical_validation":"NOT_ESTABLISHED","general_whole_solver_physical_validation":"NOT_ESTABLISHED","wetted_puck_modulus":"NOT_MEASURED_BY_THIS_TASK","real_puck_parameters":"NOT_IDENTIFIED","experimental_commissioning":"NOT_AUTHORIZED","wp04_tpm_001":"NOT_AUTHORIZED_BY_THIS_TASK_ALONE","combined_mechanism_model":"NOT_AUTHORIZED"}}

def generate():
    OUT.mkdir(parents=True,exist_ok=True); rr=rows()
    fields=list(rr[0]); csv_path=OUT/"SCI_MD_002A_CASE_MATRIX.csv"
    with csv_path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rr)
    matrix={"schema_version":"ewp.sci_md_002a.matrix.v1","row_count":len(rr),"rows":rr}
    (OUT/"SCI_MD_002A_CASE_MATRIX.json").write_text(canonical_json(matrix))
    p=protocol(sha(OUT/"SCI_MD_002A_CASE_MATRIX.json"))
    p["budgets"]["total_trajectories"]=len(rr)
    (OUT/"SCI_MD_002A_PROTOCOL.json").write_text(json.dumps(p,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"rows":len(rr),"matrix_sha256":p["matrix_sha256"]},sort_keys=True))

if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("command",choices=["freeze"]); args=ap.parse_args(); generate()
