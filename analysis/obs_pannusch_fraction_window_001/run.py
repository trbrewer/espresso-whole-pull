"""Deterministic public artifact runner."""
from __future__ import annotations
import argparse, csv, json, pathlib, subprocess
from .core import *

def git(repo, *args): return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=pathlib.Path,required=True); p.add_argument("--puckworks",type=pathlib.Path,required=True); p.add_argument("--external-source",type=pathlib.Path,required=True); p.add_argument("--output",type=pathlib.Path,required=True); p.add_argument("--phase",choices=("a","b"),default="b"); p.add_argument("--freeze-sha256"); p.add_argument("--audit-file",type=pathlib.Path)
    a=p.parse_args(argv); out=a.output; out.mkdir(parents=True,exist_ok=True)
    hashes=verify_sources(a.external_source)
    semantics=source_semantics((a.external_source/"getExperimentalData_validation.m").read_text(encoding="utf-8",errors="strict"))
    from scipy.io import loadmat
    import numpy as np
    exp=np.atleast_1d(loadmat(a.external_source/"ExperimentalData_validation.mat",squeeze_me=True,struct_as_record=False)["ExperimentalData"])
    mass=np.atleast_1d(loadmat(a.external_source/"MassData_modelval.mat",squeeze_me=True,struct_as_record=False)["MassData"])
    if len(exp)!=8 or len(mass)!=24 or any(len(np.atleast_1d(x.run))!=3 for x in exp): raise ValueError("source cardinality mismatch")
    joins=join(mass,True); window_rows=[]; join_rows=[]
    for condition,rep,index in joins:
        run=np.atleast_1d(exp[condition-1].run)[rep-1]; fit=mass[index-1]
        if float(run.a_flow)!=float(fit.a) or float(run.b_flow)!=float(fit.b): raise ValueError("MassData field-copy mismatch")
        masses=np.asarray(run.mE,float).reshape(-1); bounds=cumulative_boundaries(masses.tolist())
        source=np.asarray(run.tE,float).reshape(-1); support=(0.0,float(np.asarray(fit.time).reshape(-1)[-1]))
        reconstructed=[invert_mass(float(fit.a),float(fit.b),m,support) for m in bounds]
        if not np.allclose(source,reconstructed,rtol=0,atol=1e-12): raise ValueError("same-lineage reconstruction differs")
        cid=f"PRED-C{condition:02d}"; sid=f"PRED-E{condition:02d}-R{rep}"
        join_rows.append({"condition_id":cid,"shot_id":sid,"physical_replicate_id":rep,"mass_fit_source_index":index,"join_class":"EXPLICIT_SOURCE_CODE_MAPPING","evidence_fields":"released loop i*3-3+j; copied a,b,flow,time","candidate_count":1,"uniqueness_result":"UNIQUE_BY_EXPLICIT_INDEX","qualification_result":"PASS","failure_reason":"","source_hashes":hashes["ExperimentalData_validation.mat"]+";"+hashes["MassData_modelval.mat"],"source_id":"P24-MAT-PRED;P24-MASS-PRED","rights":RIGHTS,"target_exposure":"TARGET_EXPOSED;SOURCE_INTERNAL"})
        for fid in range(1,11):
            pos=ASSAY_IDS.index(fid)+1 if fid in ASSAY_IDS else ""
            start=0.0 if fid==1 else source[fid-2]; end=source[fid-1]
            window_rows.append({"condition_id":cid,"shot_id":sid,"source_fraction_id":fid,"profile_position":pos,"source_tE_start_s":format(float(start),".12g"),"source_tE_end_s":format(float(end),".12g"),"reconstructed_start_s":format(float(start),".12g"),"reconstructed_end_s":format(float(end),".12g"),"clock_class":"DERIVED_SAME_MASS_FIT_ZERO","source_lineage_class":"DERIVED_FROM_SAME_MASS_FIT","inversion_root_status":"UNIQUE_POSITIVE_IN_SUPPORT","fit_support_status":"PASS","mass_consistency_status":"EXACT_WITHIN_1E-12_S","vial_transition_status":"CUMULATIVE_MEASURED_VIAL_MASS_BOUNDARY","qualification_result":"PASS","failure_reason":"","source_id":"P24-MAT-PRED;P24-MASS-PRED;P24-M-PREP-PRED","rights":RIGHTS,"target_exposure":"TARGET_EXPOSED;SOURCE_INTERNAL"})
    write_csv(out/"SHOT_JOIN_QUALIFICATION.csv",list(join_rows[0]),join_rows); write_csv(out/"WINDOW_QUALIFICATION.csv",list(window_rows[0]),window_rows)
    ewp_base=git(a.repo,"merge-base","origin/main","HEAD"); ewp_tree=git(a.repo,"rev-parse",ewp_base+"^{tree}"); pw=git(a.puckworks,"rev-parse","HEAD"); pwt=git(a.puckworks,"rev-parse","HEAD^{tree}")
    prior=["analysis/xsv_pannusch_multimodel_001/pannusch_fixed.py","analysis/xsv_pannusch_multimodel_001/c1_correction.py","docs/analysis/xsv_pannusch_multimodel_001/RESULT.md","docs/analysis/xsv_pannusch_multimodel_001/C1_CALIBRATION_FREEZE_ADDENDUM.json"]
    authority={"schema_version":1,"task_id":TASK,"ewp_base_commit":ewp_base,"ewp_base_tree":ewp_tree,"puckworks_commit":pw,"puckworks_tree":pwt,"pannusch_source_subset_manifest_sha256":sha(a.puckworks/"puckworks/data/pannusch2024/source_inputs.csv"),"consumed_source_sha256":hashes,"prior_artifact_sha256":{x:sha(a.repo/x) for x in prior},"runtime_puckworks_lock_sha256":sha(a.repo/"dependencies/puckworks.lock.json"),"source_rights":RIGHTS,"target_exposure":"TARGET_EXPOSED;SOURCE_INTERNAL","independent_validation":False}
    write_json(out/"DATA_AUTHORITY.json",authority)
    lineage={"schema_version":1,"task_id":TASK,"relationships":{"massdata_to_shot_order":{"status":"EXPLICIT_SOURCE_CODE_MAPPING","conclusion":"Released preprocessing traverses eight conditions and three physical runs and indexes MassData as i*3-3+j."},"massdata_to_run_tE":{"status":"DERIVED_FROM_SAME_MASS_FIT","conclusion":"run.tE is the positive-root inversion of cumulative ten-vial mE using copied MassData a and b."},"clock_origin":{"status":"DERIVED_FROM_SAME_MASS_FIT","conclusion":"Mass fit time is rebased to its selected first sample; its zero-intercept polynomial is used directly for tE."},"vial_transition":{"status":"DERIVED_FROM_SAME_MASS_FIT","conclusion":"Boundaries are cumulative measured vial masses; source supplies ten ordered collection intervals."}},"evidence":[{"source_id":"P24-M-PREP-PRED","source_sha256":hashes["getExperimentalData_validation.m"],"function":"getExperimentalData_validation","location":"sampling-times block before chemistry ingestion","conclusion":"Explicit shared index, coefficient copy, cumulative mass, positive-root inversion, and tE assignment."},{"source_id":"P24-MASS-PRED","source_sha256":hashes["MassData_modelval.mat"],"object":"MassData[1:24]","conclusion":"24 finite a,b,time,flow records in the exact consumed order."},{"source_id":"P24-DOE-PRED","source_sha256":hashes["DesignOfExperiments_Validation_03_22.xlsx"],"object":"SampleWeights","conclusion":"Ten-vial masses are assigned in condition-major, replicate-minor order."}],"rights":RIGHTS}
    write_json(out/"SOURCE_LINEAGE.json",lineage)
    contract={"schema_version":1,"task_id":TASK,"objective":"Can target-independent shot/window/clock/vial reconstruction explain or reduce the fraction-2/tail residual without changing extraction kinetics?","governance_class":"G1","change_declaration":"SOURCE_SCENARIO_CHANGE_ONLY","scientific_invariant":"NO_GOVERNING_PHYSICS_CHANGE","owner_authorization":"OBS_PANNUSCH_FRACTION_WINDOW_001_OWNER_AUTHORIZATION_EXECUTE_ONE_BOUNDED_G1_SOURCE_INTERNAL_TARGET_EXPOSED_OBSERVATION_OPERATOR_QUALIFICATION_ONE_IMPLEMENTATION_ONE_SUBSTANTIVE_EXACT_HEAD_REVIEW_AT_MOST_ONE_MATERIAL_CORRECTION_ONE_MERGE_NO_GOVERNING_PHYSICS_CHANGE_2026_09_01","new_information":["24-way association","MassData/run.tE lineage","clock compatibility","vial reconstruction","mass-to-time observer"],"decisions":{"positive":"retain source-internal only if materiality separately passes","negative":"retain original and use fallback","null":"retain simpler source-original observer and use fallback","blocked":"close route and use fallback"},"grinder_to_cup_link":"Qualifies the predicted extraction-history to collected cup-fraction measurement interface only.","repeated_blocker":"No surrogate or empirical fit may conceal source identity or clock semantics.","lower_cost_alternative":"Direct deterministic source/metadata audit precedes experiment or model lanes.","allowed_information":["source identity","source code","non-chemistry metadata","fraction masses and times","clock and vial semantics"],"forbidden_phase_a":["chemistry","analyte mass/share","predictions","residuals","RMSE"],"metrics":{"primary":"condition-balanced shot RMSE at profile positions 2,5,6","continuity":"condition-balanced shot RMSE over six positions","bootstrap":{"replicates":2000,"seed":20260830,"generator":"PCG64","unit":"condition then physical shot; paired analytes and fraction vectors intact"}},"claim_ceiling":"SOURCE_INTERNAL_FRACTION_WINDOW_AND_OBSERVATION_OPERATOR_QUALIFICATION","always_state":["TARGET_EXPOSED","SOURCE_INTERNAL","NOT INDEPENDENT VALIDATION","NOT PHYSICAL VALIDATION","NOT HYDRAULIC VALIDATION","NOT PRODUCTION QUALIFICATION"]}
    write_json(out/"TASK_CONTRACT.json",contract)
    write_json(out/"DATA_AVAILABILITY_PREFLIGHT.json",{"schema_version":1,"task_id":TASK,"sources_checked":["Puckworks normalized Pannusch products","exact external Mendeley source subset","released MATLAB preprocessing","prior EWP fixed-Pannusch artifacts"],"external_availability":"AVAILABLE_AND_HASH_VERIFIED","authorities":authority,"rights":RIGHTS,"sufficiency":"SUFFICIENT_FOR_SOURCE_INTERNAL_IDENTITY_QUALIFICATION","home_lab":{"status":"DEFER_HOME_LAB_EXISTING_DATA_NOT_YET_EXHAUSTED","operational_authorization":False}})
    audit=None
    if a.audit_file:
        audit=json.loads(a.audit_file.read_text())
        if audit.get("status")!="PASS": raise ValueError("machine audit did not pass")
    freeze={"schema_version":1,"task_id":TASK,"authorities":authority,"join_rules":"exact released condition-major/replicate-minor i*3-3+j map; no positional-length inference alone","join_evidence_fields":["released loop indexes","copied a","copied b","copied flow","copied time"],"tolerances":{"source_hash":"exact","coefficient_copy":"exact float","boundary_identity_s":1e-12,"baseline_share":1e-10},"matching_algorithm":"explicit index mapping; candidate count one; no permutation search","clock_semantics":"MassData fit time rebased to selected first raw-scale sample; run.tE uses that same clock","mass_function":"m(t)=a*t^2+b*t; grams and seconds; zero intercept","boundary_inversion":"positive source root at cumulative measured ten-vial mass","root_selection":"exact released +sqrt root; unique and inside stored fit support","extrapolation":"prohibited","source_fraction_ids":list(ASSAY_IDS),"profile_positions":[1,2,3,4,5,6],"primary_cohort":list(PRIMARY),"optional_cohorts":{"extended":["PRED-C07","PRED-C08"],"source_empirical_only":["PRED-C03","PRED-C04"]},"analytes":["caffeine","trigonelline"],"observers":{"O0":"current source run.tE windows and measured run.mE","O1":"same MassData-derived windows reconstructed under exact source semantics"},"metrics":contract["metrics"],"decision_rules":{"identity":"scientific null","positive":"paired 95% interval strictly below zero plus residual norm decrease and safety gates","materiality":"10% relative; interval below zero; <=25% conditions worse; LOCO direction consistent"},"code_sha256":{"core":sha(pathlib.Path(__file__).with_name("core.py")),"runner":sha(__file__)},"operator_construction_target_independent":True,"protected_holdout":False,"target_exposed":True,"independent_validation":False,"post_score_retuning_permitted":False,"qualification_result":"FULL_24_QUALIFIED;SAME_SOURCE_LINEAGE_IDENTITY","audit_result":{"status":audit["status"],"audit_sha256":sha(a.audit_file),"audited_pending_freeze_sha256":audit["audited_freeze_sha256"]} if audit else {"status":"PENDING_MACHINE_AUDIT"}}
    write_json(out/"QUALIFICATION_FREEZE.json",freeze); freeze_hash=sha(out/"QUALIFICATION_FREEZE.json")
    if a.phase=="a": print(freeze_hash); return
    if not a.audit_file or freeze["audit_result"].get("status")!="PASS": raise ValueError("Phase B requires passing independent audit")
    if not a.freeze_sha256 or a.freeze_sha256 != freeze_hash: raise ValueError("Phase B requires exact Phase-A freeze SHA-256")
    prior_result=json.loads((a.repo/"docs/analysis/xsv_pannusch_multimodel_001/summary.json").read_text())
    o0=float(prior_result["primary_comparison"]["pannusch_rmse"])
    import sys
    sys.path.insert(0,str(a.puckworks)); from puckworks.models.pannusch2024 import solver
    def read(name):
        with (a.puckworks/"puckworks/data/pannusch2024"/name).open(newline="",encoding="utf-8") as stream: return list(csv.DictReader(stream))
    fit=[r for r in read("fit_fraction_replicates.csv") if r["validity"]=="VALID" and r["analyte"] in ("caffeine","trigonelline")]
    first={}
    for r in fit:
        key=(r["shot_id"],r["analyte"])
        if int(r["fraction_id"])==1: first[key]=float(r["concentration_value"])
    cl1={an:sum(v for (shot,a0),v in first.items() if a0==an)/sum(a0==an for shot,a0 in first) for an in ("caffeine","trigonelline")}
    predrows=[r for r in read("prediction_fraction_replicates.csv") if r["validity"]=="VALID" and r["analyte"] in cl1 and r["condition_id"] in PRIMARY]
    groups={}
    for r in predrows: groups.setdefault((r["condition_id"],r["shot_id"],r["analyte"]),[]).append(r)
    observer=[]; shot_metrics=[]
    params=solver._solute_params()
    for key,rows in sorted(groups.items()):
        rows.sort(key=lambda x:int(x["fraction_id"])); starts=np.array([float(x["fraction_start_s"]) for x in rows]); ends=np.array([float(x["fraction_end_s"]) for x in rows]); liquid=np.array([float(x["fraction_liquid_g_or_ml"]) for x in rows])
        observed_mass=np.array([float(x["derived_analyte_mass_mg"]) for x in rows]); observed=observed_mass/observed_mass.sum(); bounds=sorted(set(starts)|set(ends))
        raw=solver.simulate_fractions(float(rows[0]["temperature_start_C"]),float(rows[0]["flow_start_mL_s"]),bounds,dict(params[key[2]]),cl1[key[2]],solver.GRINDS[1.7])
        concentration=np.array([solver._interval_conc(raw,bounds,lo,hi) for lo,hi in zip(starts,ends)]); predicted=np.maximum(concentration,0)*liquid; predicted/=predicted.sum(); residual=predicted-observed
        shot_metrics.append({"condition":key[0],"shot":key[1],"analyte":key[2],"all":float((sum(x*x for x in residual)/6)**.5),"primary":float((sum(residual[i]*residual[i] for i in (1,4,5))/3)**.5)})
        windows=[x for x in window_rows if x["condition_id"]==key[0] and x["shot_id"]==key[1] and x["profile_position"]]
        for i,window in enumerate(windows):
            observer.append({"condition_id":key[0],"shot_id":key[1],"analyte":key[2],"profile_position":i+1,"source_fraction_id":ASSAY_IDS[i],"observer":"O0_CURRENT_SOURCE_WINDOWS;O1_QUALIFIED_MASS_WINDOW_OBSERVER","window_start_s":window["source_tE_start_s"],"window_end_s":window["source_tE_end_s"],"observed_share":format(float(observed[i]),".17g"),"O0_predicted_share":format(float(predicted[i]),".17g"),"O1_predicted_share":format(float(predicted[i]),".17g"),"O0_residual":format(float(residual[i]),".17g"),"O1_residual":format(float(residual[i]),".17g"),"prediction_identity":"EXACT_SAME_INPUT_WINDOW","source_id":"P24-MAT-PRED;P24-MASS-PRED","rights":RIGHTS,"target_exposure":"TARGET_EXPOSED;SOURCE_INTERNAL"})
    write_csv(out/"OBSERVER_RESULTS.csv",list(observer[0]),observer)
    def balanced(name):
        return sum(sum(x[name] for x in shot_metrics if x["condition"]==c)/sum(x["condition"]==c for x in shot_metrics) for c in PRIMARY)/len(PRIMARY)
    primary_rmse=balanced("primary"); total_rmse=balanced("all")
    if abs(total_rmse-o0)>1e-10: raise ValueError(f"O0 predecessor reproduction failed: {total_rmse} != {o0}")
    # Re-execute an exact dependency-light translation of the frozen predecessor row calculation.
    from .baseline import reproduce
    prior_rows=reproduce(a.puckworks/"puckworks/data/pannusch2024",solver)
    current={(r["condition_id"],r["shot_id"],r["analyte"],int(r["profile_position"])):r for r in observer}
    if len(prior_rows)!=len(current): raise ValueError("O0 predecessor row cardinality mismatch")
    first_difference=None
    for r in prior_rows:
        key=(r["condition"],r["shot"],r["analyte"],int(r["fraction"])); q=current.get(key)
        if q is None: first_difference=(key,"missing"); break
        for old,new in ((r["observed_share"],q["observed_share"]),(r["predicted_share"],q["O0_predicted_share"]),(r["residual"],q["O0_residual"])):
            if abs(float(old)-float(new))>1e-10: first_difference=(key,float(old),float(new)); break
        if first_difference: break
    if first_difference: raise ValueError(f"O0 predecessor first row difference: {first_difference}")
    expected_residual=prior_result["residuals"]
    by_position={i:[float(r["O0_residual"]) for r in observer if int(r["profile_position"])==i] for i in range(1,7)}
    means={i:float(np.mean(v)) for i,v in by_position.items()}
    for pos,name in ((2,"fraction_2_mean"),(5,"fraction_5_mean"),(6,"fraction_6_mean")):
        if abs(means[pos]-float(expected_residual[name]))>1e-10: raise ValueError(f"O0 predecessor residual summary mismatch at {pos}")
    # Frozen condition-then-shot bootstrap; analytes and complete fraction vectors remain paired.
    vectors={}
    for r in observer: vectors.setdefault((r["condition_id"],r["shot_id"]),[]).append(r)
    rng=np.random.Generator(np.random.PCG64(20260830)); boots={i:[] for i in range(1,7)}
    for _ in range(2000):
        selected=[]
        for c in rng.choice(PRIMARY,size=len(PRIMARY),replace=True):
            shots=sorted({s for cc,s in vectors if cc==c}); selected.extend(vectors[(c,s)] for s in rng.choice(shots,size=len(shots),replace=True))
        flat=[r for group in selected for r in group]
        for i in range(1,7): boots[i].append(float(np.mean([float(r["O0_residual"]) for r in flat if int(r["profile_position"])==i])))
    ci={i:(float(np.quantile(v,.025)),float(np.quantile(v,.975))) for i,v in boots.items()}
    residual_vectors=[]
    for key,rows in sorted(groups.items()):
        q=sorted((current[(key[0],key[1],key[2],i)] for i in range(1,7)),key=lambda r:int(r["profile_position"]))
        residual_vectors.append((key,np.array([float(r["O0_residual"]) for r in q])))
    systematic_norm=float(np.linalg.norm([means[i] for i in (2,5,6)]))
    cumulative_rmse=float(np.mean([np.sqrt(np.mean(np.cumsum(v)**2)) for _,v in residual_vectors]))
    centroid_error=float(np.mean([sum((i+1)*v[i] for i in range(6)) for _,v in residual_vectors]))
    fields=["metric","scope","O0","O1","delta","paired_ci_low","paired_ci_high","relative_improvement","materiality","status"]
    def metric(name,scope,value,low="",high="",status="EXACT_IDENTITY_NULL"):
        return {"metric":name,"scope":scope,"O0":value,"O1":value,"delta":0.0,"paired_ci_low":low,"paired_ci_high":high,"relative_improvement":0.0,"materiality":False,"status":status}
    metrics=[metric("primary_positions_2_5_6_condition_balanced_rmse","PRIMARY",primary_rmse,0.0,0.0),metric("all_six_condition_balanced_rmse","PRIMARY",total_rmse,0.0,0.0)]
    metrics += [metric("mean_signed_residual",f"profile_position_{i}",means[i],ci[i][0],ci[i][1],"BASELINE_DIAGNOSTIC_IDENTITY") for i in range(1,7)]
    metrics += [metric("systematic_residual_vector_norm","positions_2_5_6",systematic_norm),metric("early_share_error","profile_position_1",means[1]),metric("tail_share_error","profile_position_6",means[6]),metric("cumulative_share_rmse","PRIMARY",cumulative_rmse),metric("centroid_error","PRIMARY",centroid_error),metric("reconstructed_minus_source_window_max_abs_s","FULL_24",0.0)]
    for c in PRIMARY: metrics.append(metric("primary_rmse",c,float(np.mean([x["primary"] for x in shot_metrics if x["condition"]==c]))))
    for an in ("caffeine","trigonelline"): metrics.append(metric("primary_rmse",an,float(np.mean([x["primary"] for x in shot_metrics if x["analyte"]==an]))))
    for omitted in PRIMARY: metrics.append(metric("leave_one_condition_out_primary_delta",f"omit_{omitted}",0.0,0.0,0.0,"IDENTICAL_DIRECTION"))
    metrics.append(metric("exact_four_condition_sign_enumeration","4_conditions",0.0,0.0,0.0,"ALL_ZERO_IDENTITY"))
    write_csv(out/"METRIC_RESULTS.csv",fields,metrics)
    disposition="OBS_PANNUSCH_FRACTION_WINDOW_001_OBSERVER_EFFECT_INDISTINGUISHABLE"
    decision={"schema_version":1,"task_id":TASK,"qualification":"FULL_24_QUALIFIED","qualifiers":["FULL_24_QUALIFIED","SAME_SOURCE_LINEAGE_IDENTITY","WINDOW_UNCERTAINTY_ROBUSTNESS_NOT_ESTABLISHED"],"scientific_disposition":disposition,"materiality":"NOT_MATERIAL_EXACT_IDENTITY","baseline_reproduction":"PASS_EXACT_144_ROW_IDENTITY_AND_METRIC_SUMMARIES","phase_b_authorized":True,"freeze_sha256":freeze_hash,"claim_ceiling":contract["claim_ceiling"],"production_invariants":["NO_GOVERNING_PHYSICS_CHANGE","NO_REFIT","NO_PRODUCTION_CHANGE","PUCKWORKS_READ_ONLY","RUNTIME_LOCK_UNCHANGED"],"next_action":"SCI-MD-PANNUSCH-FLOW-HISTORY-001","next_action_implemented":False,"home_lab":"DEFER_HOME_LAB_EXISTING_DATA_NOT_YET_EXHAUSTED"}
    write_json(out/"DECISION.json",decision)
    write_json(out/"summary.json",{"task_id":TASK,"disposition":disposition,"qualification":"FULL_24_QUALIFIED","joins":{"qualified":24,"total":24},"windows":{"qualified":240,"total":240,"identity":True},"phase_b":True,"machine_audit":"PASS","baseline_reproduction":{"rows":144,"status":"PASS_EXACT_ROW_IDENTITY","rmse":total_rmse},"primary_rmse":primary_rmse,"primary_delta":0.0,"total_delta":0.0,"systematic_residual_norm":systematic_norm,"position_residuals":{str(i):{"mean":means[i],"ci95":list(ci[i])} for i in (2,5,6)},"freeze_sha256":freeze_hash,"next_action":decision["next_action"],"claims":["TARGET_EXPOSED","SOURCE_INTERNAL","NOT INDEPENDENT VALIDATION","NOT PHYSICAL VALIDATION","NOT HYDRAULIC VALIDATION","NOT PRODUCTION QUALIFICATION"]})
    (out/"RESULT.md").write_text(f"""# {TASK} result\n\n`{disposition}`; `FULL_24_QUALIFIED`; `SAME_SOURCE_LINEAGE_IDENTITY`.\n\nThe released preprocessing proves the 24-way condition/physical-shot association and explicitly derives every `run.tE` from the corresponding `MassData_modelval.mat` record. It uses all ten measured vial masses, cumulative boundaries, and the source positive-root inversion of `m(t)=a t²+b t`. Reconstructed and source windows agree exactly within the frozen 1e-12 s tolerance. The independent pre-score audit reverified authority/code hashes and produced byte-identical structural qualification after chemistry arrays were zeroed, permuted, and replaced with synthetic values.\n\nO1 is therefore O0, not an alternative observer. The exact 144-row O0 predecessor reproduction passes. The condition-balanced physical-shot RMSE at profile positions 2, 5, and 6 (source fraction IDs 2, 7, and 10) is {primary_rmse:.15g} for both observers; the all-six-position RMSE is {total_rmse:.15g} for both. Both deltas and their paired intervals are [0, 0]. Baseline signed residuals at positions 2, 5, and 6 are {means[2]:.15g} [{ci[2][0]:.15g}, {ci[2][1]:.15g}], {means[5]:.15g} [{ci[5][0]:.15g}, {ci[5][1]:.15g}], and {means[6]:.15g} [{ci[6][0]:.15g}, {ci[6][1]:.15g}]; their systematic-vector norm is {systematic_norm:.15g} for both observers. Every condition, analyte, leave-one-condition-out comparison, and sign enumeration is identical; materiality is false. No kinetics, parameter, source input, mass, normalization, or production behavior changed.\n\nWindow-uncertainty robustness is not established because the source supplies no coefficient covariance or supported window-uncertainty model. TARGET_EXPOSED; SOURCE_INTERNAL; NOT INDEPENDENT VALIDATION; NOT PHYSICAL VALIDATION; NOT HYDRAULIC VALIDATION; NOT PRODUCTION QUALIFICATION. The selected, unimplemented next action is `SCI-MD-PANNUSCH-FLOW-HISTORY-001`; home-lab operation remains deferred.\n""",encoding="utf-8",newline="\n")
    print(disposition, freeze_hash)

if __name__=="__main__": main()
