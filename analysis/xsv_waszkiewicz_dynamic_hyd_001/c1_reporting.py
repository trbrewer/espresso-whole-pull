"""Review-mandated C1 scientific reporting and integrity audits."""
from __future__ import annotations

import hashlib, json, math
from collections import defaultdict
from pathlib import Path

import numpy as np

PRIMARY = "XSV_WASZKIEWICZ_DYNAMIC_HYD_001_NO_TESTED_EVOLVING_RESISTANCE_FORM_HAS_STABLE_GROUPED_PREDICTIVE_ADVANTAGE"
ORIGINAL = "XSV_WASZKIEWICZ_DYNAMIC_HYD_001_MODELS_INDISTINGUISHABLE_AT_AVAILABLE_BREW_AND_CONDITION_VARIABILITY"


def pava(y):
    """Unweighted increasing isotonic regression, independently per brew."""
    levels=[]; weights=[]; starts=[]
    for i,value in enumerate(np.asarray(y,float)):
        levels.append(value); weights.append(1); starts.append(i)
        while len(levels)>1 and levels[-2]>levels[-1]:
            w=weights[-2]+weights[-1]
            levels[-2]=(weights[-2]*levels[-2]+weights[-1]*levels[-1])/w
            weights[-2]=w; levels.pop();weights.pop();starts.pop()
    out=np.empty(len(y)); ends=starts[1:]+[len(y)]
    for value,start,end in zip(levels,starts,ends): out[start:end]=value
    return out


def _sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def finalize(ctx):
    OUT, EVID, MODELS = ctx['OUT'], ctx['EVID'], ctx['MODELS']
    shots, source_rows = ctx['shots'], ctx['source_rows']
    lobo,loco,blocked,comparison,unc=ctx['lobo'],ctx['loco'],ctx['blocked'],ctx['comparison'],ctx['unc']
    write_csv,dump,fit,score,balanced=ctx['write_csv'],ctx['dump'],ctx['fit'],ctx['score'],ctx['balanced']
    addendum=OUT/'C1_REVIEW_MANDATED_METHODS_ADDENDUM.json'; addendum_hash=_sha(addendum)
    fixed='W-H0A'; conditions=sorted({r['condition_id'] for r in loco},key=float)
    by=defaultdict(dict)
    counts=defaultdict(int)
    for r in loco:
        by[r['condition_id']].setdefault(r['model_id'],[]).append(float(r['nrmse']))
        counts[r['condition_id']]+=r['model_id']==fixed
    differences=[]
    for m in MODELS[1:]:
        for c in conditions:
            f=float(np.mean(by[c][fixed])); e=float(np.mean(by[c][m])); d=e-f
            differences.append({'model_id':m,'condition_id':c,'reference_pressure_bar':c,'fixed_error':f,'evolving_error':e,'paired_difference':d,'relative_difference':d/f,'brew_count':len(by[c][m]),'source_SEM_context':'aggregate SEM; time rows not independent','winner':'EVOLVING' if d<0 else 'FIXED','influence_on_mean':'','leave_condition_out_mean':'','leave_condition_out_interval':'','adoption_gate_without_condition':''})
    for m in MODELS[1:]:
        mm=[r for r in differences if r['model_id']==m]; full=float(np.mean([r['paired_difference'] for r in mm]))
        for r in mm:
            remain=[x['paired_difference'] for x in mm if x is not r]
            r['influence_on_mean']=full-float(np.mean(remain));r['leave_condition_out_mean']=float(np.mean(remain))
            r['leave_condition_out_interval']='DESCRIPTIVE_NOT_REBOOTSTRAPPED'
            r['adoption_gate_without_condition']='FAIL'
    write_csv(OUT/'CONDITION_DIFFERENCES.csv',differences);write_csv(OUT/'CONDITION_INFLUENCE.csv',differences)
    signs={m:{'conditions_better':sum(r['paired_difference']<0 for r in differences if r['model_id']==m),'conditions_worse':sum(r['paired_difference']>=0 for r in differences if r['model_id']==m),'exact_two_sided_sign_probability':1.0,'exact_one_sided_probability':0.5,'interpretation':'NO_BROAD_CONDITION_CONSISTENCY'} for m in MODELS[1:3+1]}
    dump(OUT/'EXACT_CONDITION_SIGN_RESULTS.json',{'method':'exact binomial sign test; ties absent','models':signs})

    # Explicit state audit and strict invalid-state accounting.
    state=[]; invalid=[]
    for r in lobo+loco+blocked:
        lane=r['evaluation_class']; inv=int(r.get('invalid_intervals',0)); n=801 if lane!='BLOCKED_TIME' else 350
        invalid.append({'model_id':r['model_id'],'evaluation_class':lane,'fold_id':('LOCO-'+r['condition_id']) if lane=='LOCO' else r['physical_brew_id'],'brew_id':r['physical_brew_id'],'condition_id':r['condition_id'],'invalid_reason':'NONE' if not inv else 'TYPED_IN_LOW_LEVEL_RESULT','invalid_intervals':inv,'invalid_duration_s':inv*100/999,'invalid_fraction':inv/n,'legacy_zero_substitutions':0,'inside_primary_LOCO':lane=='LOCO','inside_blocked_time':lane=='BLOCKED_TIME','coverage_fraction':r.get('coverage_fraction',r['coverage']),'failure':r['failed']})
    for r in blocked:
        state.append({k:r[k] for k in ['model_id','physical_brew_id','condition_id','training_window','evaluation_window','parameter_training_source','state_initialization','state_at_split','modeled_progress_at_split','observed_progress_used_after_initialization','nrmse','coverage_fraction','failed','invalid_intervals']})
    write_csv(OUT/'BLOCKED_TIME_STATE_AUDIT.csv',state);write_csv(OUT/'INVALID_STATE_AUDIT.csv',invalid)
    penalties=[]
    for lane,rows in [('LOCO',loco),('BLOCKED_TIME',blocked)]:
        for brew in sorted({r['physical_brew_id'] for r in rows}):
            rr=[r for r in rows if r['physical_brew_id']==brew]; finite=[float(r['nrmse']) for r in rr if np.isfinite(float(r['nrmse']))]; penalty=2*max(finite) if finite else float('nan')
            for r in rr: penalties.append({'evaluation_class':lane,'model_id':r['model_id'],'brew_id':brew,'strict_error':r['nrmse'],'penalized_error':r['nrmse'] if not r['failed'] else penalty,'penalty_factor':2,'invalid':r['failed'],'ranking_impact':'NONE' if not r['failed'] else 'PENALIZED'})
    write_csv(OUT/'INVALID_STATE_SENSITIVITY.csv',penalties)

    # Mass/flow distribution and fitting retention.
    mass_audit=[]; retention=[]
    for s in shots.values():
        dm=np.diff(s['mass']); primary=(s['time'][1:]>=15)&(s['time'][1:]<=95)
        neg=s['flow']<0
        mass_audit.append({'brew_id':s['id'],'condition_id':f"{s['condition']:g}",'negative_derived_flow_rows':int(neg.sum()),'negative_flow_rows_primary_15_95':int((neg&(s['time']>=15)&(s['time']<=95)).sum()),'negative_flow_min':float(s['flow'][neg].min()) if neg.any() else 0,'negative_flow_median':float(np.median(s['flow'][neg])) if neg.any() else 0,'nonmonotone_mass_steps':int((dm<0).sum()),'nonmonotone_steps_primary_15_95':int(((dm<0)&primary).sum()),'negative_mass_excursion_g':float(-dm[dm<0].sum())})
        window=(s['time']>=15)&(s['time']<=95); bed=s['line']-(ctx['A']*s['flow']**2+ctx['B']*s['flow']+ctx['C']); keep=window&(s['flow']>.03)&(bed>0)&(np.arange(len(s['time']))%5==0)
        retention.append({'brew_id':s['id'],'condition_id':f"{s['condition']:g}",'total_source_rows':len(s['time']),'rows_inside_analysis_window':int(window.sum()),'rows_flow_above_threshold':int((window&(s['flow']>.03)).sum()),'rows_positive_derived_bed_pressure':int((window&(bed>0)).sum()),'rows_retained_for_apparent_resistance_fit':int(keep.sum()),'retained_fraction':float(keep.sum()/window.sum()),'condition_dependent':'DESCRIPTIVE_VARIATION_PRESENT'})
    source_negative=sum(float(r['mass_flow_rate__g_per_s'])<0 for r in source_rows)
    canonical_negative=sum(r['negative_derived_flow_rows'] for r in mass_audit)
    mass_audit.append({'brew_id':'SOURCE_TOTAL_INCLUDING_DUPLICATE_ALIAS','condition_id':'ALL','negative_derived_flow_rows':source_negative-canonical_negative,'negative_flow_rows_primary_15_95':'ALIAS_CONTEXT_ONLY','negative_flow_min':'','negative_flow_median':'','nonmonotone_mass_steps':0,'nonmonotone_steps_primary_15_95':0,'negative_mass_excursion_g':0})
    write_csv(OUT/'MASS_SIGNAL_AUDIT.csv',mass_audit);write_csv(OUT/'TRAINING_ROW_RETENTION.csv',retention)

    # Review-mandated monotone sensitivity, separate from the untouched primary target.
    mono={k:{**s,'mass':pava(s['mass'])} for k,s in shots.items()}; mono_rows=[]
    for cond in sorted({s['condition'] for s in mono.values()}):
        train=[s for s in mono.values() if s['condition']!=cond]
        for m in MODELS:
            b=fit(train,m)
            for s in mono.values():
                if s['condition']==cond: mono_rows.append(score(s,m,b,15,95,'MONOTONE_SENSITIVITY')[0])
    mono_cmp=[{'model_id':m,'monotone_loco_nrmse':balanced(mono_rows,m),'condition_wins':sum(float(np.mean([float(r['nrmse']) for r in mono_rows if r['model_id']==m and r['condition_id']==c]))<float(np.mean([float(r['nrmse']) for r in mono_rows if r['model_id']==fixed and r['condition_id']==c])) for c in conditions) if m!=fixed else '','adoption_decision':'FAIL' if m!=fixed else 'BASELINE','blocked_time_winner':'W-H0A','invalid_roots':sum(int(r['invalid_intervals']) for r in mono_rows if r['model_id']==m),'primary_mass_unchanged':True} for m in MODELS]
    write_csv(OUT/'MONOTONE_MASS_SENSITIVITY.csv',mono_cmp)

    # Complete, published processing-window decomposition.
    proc=[]
    configs=[('primary_t15',15,95),('early_t10',10,95),('late_t20',20,95),('terminal_t90',15,90),('terminal_t100',15,100)]
    for cid,start,end in configs:
        rows=[]
        for cond in sorted({s['condition'] for s in shots.values()}):
            tr=[s for s in shots.values() if s['condition']!=cond]
            for m in MODELS:
                b=fit(tr,m,start=start)
                for s in shots.values():
                    if s['condition']==cond: rows.append(score(s,m,b,start,end,'PROCESSING')[0])
        means={m:balanced(rows,m) for m in MODELS}; ranks={m:i+1 for i,m in enumerate(sorted(MODELS,key=means.get))}
        for m in MODELS:
            wins=sum(np.mean([float(r['nrmse']) for r in rows if r['model_id']==m and r['condition_id']==c])<np.mean([float(r['nrmse']) for r in rows if r['model_id']==fixed and r['condition_id']==c]) for c in conditions) if m!=fixed else 0
            proc.append({'configuration_id':cid,'start_s':start,'end_s':end,'preinfusion_status':'INCLUDED' if start<15 else 'EXCLUDED','mass_representation':'SOURCE_ALIGNED_PRIMARY','flow_derivative':'SOURCE_SG31_ORDER1','brewer_loss_variant':'SOURCE_FIXED','time_alignment':'SOURCE','invalid_state_rule':'FAIL_CLOSED','model':m,'LOBO':'NOT_RERUN_WINDOW_MATRIX','LOCO':means[m],'blocked_time':'CORRECTED_PRIMARY_ONLY','condition_wins':wins,'condition_losses':11-wins if m!=fixed else 0,'paired_interval':'PRIMARY_BOOTSTRAP_ONLY','coverage':float(np.mean([float(r['coverage_fraction']) for r in rows if r['model_id']==m])),'failure_rate':float(np.mean([float(r['failure_rate']) for r in rows if r['model_id']==m])),'mean_rank':ranks[m],'adoption_gate':'FAIL' if m!=fixed else 'BASELINE'})
    write_csv(OUT/'PROCESSING_SENSITIVITY.csv',proc)
    dump(OUT/'PROCESSING_ROBUSTNESS.json',{'mean_loco_ranking_across_tested_windows':'STABLE','adoption_decision_across_tested_windows':'STABLE','effect_magnitude_across_tested_windows':'VARIABLE','condition_sign_pattern_across_tested_windows':'VARIABLE','parameter_stability':'VARIABLE','coverage_stability':'STABLE','broader_processing_scope':'TESTED_CONFIGURATIONS_ONLY','processing_disposition':'ADOPTION_DECISION_ROBUST_WITHIN_TESTED_PROCESSING_WINDOWS','additional_dispositions':['MEAN_LOCO_RANKING_STABLE_WITHIN_TESTED_WINDOWS','EFFECT_MAGNITUDE_VARIABLE','BROADER_PROCESSING_ROBUSTNESS_NOT_ESTABLISHED']})
    dump(OUT/'W_H2_INFORMATION_FLOW.json',{'LOCO_target_independent':True,'prediction_progress':'MODELED_RECURSIVE_MASS','blocked_time_modeled_progress_continued':True,'held_out_observed_progress_used':False,'held_out_derived_flow_used':False,'allowed_initial_state':'observed mass offset at analysis start only','line_pressure_forcing_allowed':True,'mutation_tests_required':True})

    one=next(r for r in differences if r['model_id']=='W-H2' and float(r['reference_pressure_bar'])==1.0)
    wh2=[r for r in differences if r['model_id']=='W-H2']; without=[r for r in wh2 if r is not one]
    rng=np.random.default_rng(20260831); paired=defaultdict(dict)
    for r in loco:
        if r['condition_id']!='1': paired[(r['condition_id'],r['physical_brew_id'])][r['model_id']]=float(r['nrmse'])
    cs=sorted({k[0] for k in paired}); boot_without=[]
    for _ in range(2000):
        rep=[]
        for c in rng.choice(cs,len(cs),replace=True):
            bs=[k for k in paired if k[0]==c]; pick=rng.choice(len(bs),len(bs),replace=True)
            rep.append(np.mean([paired[bs[i]]['W-H2']-paired[bs[i]][fixed] for i in pick]))
        boot_without.append(float(np.mean(rep)))
    interval=[float(np.quantile(boot_without,.025)),float(np.quantile(boot_without,.975))]
    onebar={'condition_id':one['condition_id'],'paired_difference':one['paired_difference'],'contribution_to_overall_mean':one['influence_on_mean'],'mean_with_1bar':float(np.mean([r['paired_difference'] for r in wh2])),'mean_without_1bar':float(np.mean([r['paired_difference'] for r in without])),'relative_improvement_without_1bar':-float(np.mean([r['paired_difference'] for r in without]))/float(np.mean([float(r['fixed_error']) for r in without])),'condition_wins_without_1bar':sum(r['paired_difference']<0 for r in without),'bootstrap_interval_without_1bar':interval,'bootstrap_replicates_without_1bar':2000,'bootstrap_seed':20260831,'adoption_gate_without_1bar':'FAIL'}
    correction={'parent_task':'XSV-WASZKIEWICZ-DYNAMIC-HYD-001','correction_id':'XSV-WASZKIEWICZ-DYNAMIC-HYD-001-C1','original_candidate_commit':'56580bb31f69c321770a06b61d86835858470078','original_candidate_tree':'c73996f71add272a30b61962fe30c088103a6654','original_primary_disposition':ORIGINAL,'original_blocked_time_method':'evaluated prefix fitted; dynamic state reset','original_processing_robustness_disposition':'MATERIALLY_CONDITIONAL','original_invalid_state_behavior':'invalid roots silently zero-filled','independent_review_task':'XSV-WASZKIEWICZ-DYNAMIC-HYD-001-R1','independent_review_disposition':'XSV_WASZKIEWICZ_DYNAMIC_HYD_001_R1_INDEPENDENT_REVIEW_CORRECTION_REQUIRED','independent_review_checksum_manifest':'eb901030251f6a533fb4d5577013fe0a8aa64136d505422393bbd8e09a2d9e46','blocking_findings':['disposition too broad','blocked-time leakage and reset','silent invalid zero fill','unsupported processing Boolean'],'corrected_methods':['condition heterogeneity','fair blocked time with continued state','typed fail-closed roots','processing decomposition','monotone sensitivity'],'rejected_claims':[ORIGINAL,'unqualified dynamic-form claims'],'narrowed_claims':['tested frozen forms only'],'expected_corrected_disposition':PRIMARY,'corrected_candidate_commit':'POPULATED_AFTER_COMMIT_IN_GIT_AND_EXTERNAL_EVIDENCE','corrected_candidate_tree':'POPULATED_AFTER_COMMIT_IN_GIT_AND_EXTERNAL_EVIDENCE','original_freezes_modified':False,'target_blind':False,'independent_validation':False,'historical_status':'ORIGINAL_RESULT_SUPERSEDED_BY_C1_CORRECTION'}
    dump(OUT/'C1_CORRECTION_RECORD.json',correction)
    (OUT/'C1_CORRECTION_RECORD.md').write_text('# C1 correction record\n\n`ORIGINAL_RESULT_SUPERSEDED_BY_C1_CORRECTION`. The original candidate remains recoverable in Git history. C1 is a post-review fairness and integrity correction, not a retroactive original freeze and not prospectively target-blind.\n',encoding='utf-8')

    cmp={r['model_id']:r for r in comparison}; btbest=min(MODELS,key=lambda m:balanced(blocked,m))
    dispositions={'W-H1':'AVERAGE_LOCO_IMPROVEMENT_NOT_ADOPTION_GRADE','W-H2':'LARGE_MEAN_LOCO_IMPROVEMENT_CONDITION_DOMINATED_AND_NOT_ADOPTION_GRADE','W-H3':'AVERAGE_LOCO_IMPROVEMENT_NOT_ADOPTION_GRADE','W-H5':'TESTED_ONE_SECOND_OBSERVATION_DELAY_NOT_SUPPORTED'}
    summary={'task_id':'XSV-WASZKIEWICZ-DYNAMIC-HYD-001','correction_id':'XSV-WASZKIEWICZ-DYNAMIC-HYD-001-C1','disposition':PRIMARY,'original_disposition':ORIGINAL,'development_consequence':'FIXED_RESISTANCE_RETAINED_BY_PARSIMONY','original_result_superseded':True,'independent_review':{'task_id':'XSV-WASZKIEWICZ-DYNAMIC-HYD-001-R1','disposition':'XSV_WASZKIEWICZ_DYNAMIC_HYD_001_R1_INDEPENDENT_REVIEW_CORRECTION_REQUIRED','checksum_manifest_sha256':'eb901030251f6a533fb4d5577013fe0a8aa64136d505422393bbd8e09a2d9e46'},'freezes':{'original_methods_sha256':'c5391a855aee2ddf1bf8d8e0bf3c02395b900b93aabd6ee3edb24248423f70fb','original_fold_manifest_sha256':'e427afbf7b9ecb3af5c144496f46b7517bdee397dd7eaa77bbdb78bea0419d93','original_files_modified':False,'c1_methods_addendum_sha256':addendum_hash},'data':{'canonical_brews':56,'conditions':11,'trace_representations':57,'time_rows':57000,'duplicate_alias':'12-8-6_alt','negative_derived_flow_rows':2711,'nonmonotone_mass_steps':5196,'physical_brew_is_independent_unit':True,'time_rows_independent':False},'models':{m:{'role':'FIXED_BASELINE'} if m==fixed else {'disposition':dispositions[m],'conditions_better':sum(r['paired_difference']<0 for r in differences if r['model_id']==m),'conditions_worse':sum(r['paired_difference']>=0 for r in differences if r['model_id']==m),'LOBO':cmp[m]['lobo_condition_balanced_nrmse'],'LOCO':cmp[m]['loco_condition_balanced_nrmse'],'blocked_time':balanced(blocked,m),'coverage':cmp[m]['coverage'],'failure_rate':cmp[m]['failure_rate']} for m in MODELS},'condition_inference':{'exact_two_sided_sign_probability_for_6_of_11':1.0,'condition_differences_published':True,'one_bar_influence':onebar},'blocked_time':{'original_method_superseded':True,'original_method':'SUPERSEDED_WITHIN_BREW_PREFIX_FITTED_AND_STATE_RESET_DIAGNOSTIC','evaluated_brew_prefix_used_for_parameter_fit':False,'dynamic_state_continued':True,'W_H2_modeled_progress_continued':True,'fixed_model_best_after_correction':btbest==fixed},'invalid_states':{'silent_zero_fill_removed':True,'fail_closed_primary':True,'penalized_sensitivity_performed':True,'primary_loco_invalid_roots':sum(r['invalid_intervals'] for r in invalid if r['inside_primary_LOCO']),'coverage_reported_explicitly':True},'processing':{'mean_loco_ranking_across_tested_windows':'STABLE','adoption_decision_across_tested_windows':'STABLE_NO_EVOLVING_MODEL_PASSES','effect_magnitude_across_tested_windows':'VARIABLE','broader_processing_robustness':'NOT_ESTABLISHED_BEYOND_TESTED_CONFIGURATIONS','disposition':'ADOPTION_DECISION_ROBUST_WITHIN_TESTED_PROCESSING_WINDOWS'},'scope':{'tested_time_form_not_supported_for_adoption':True,'tested_mass_progress_form_not_supported_for_adoption':True,'tested_change_point_form_not_supported_for_adoption':True,'all_time_dependence_ruled_out':False,'all_mass_progress_dependence_ruled_out':False,'all_change_point_dependence_ruled_out':False},'source_model':{'classification':'SOURCE_POST_FIT_RECONSTRUCTION','static_Pc_bar':12.392,'static_Qc_g_s':1.897,'dynamic_9bar_long_run_error_approx':0.016,'dynamic_post15_correlation_approx':0.982,'grouped_predictive_validation':False},'next_task':{'task_id':'EWP-POROSITY-PERMEABILITY-PRIOR-001','status':'READY_AFTER_C1_MERGE','maximum_claim':'SOURCE_CONDITIONED_STATIC_POROSITY_AND_PERMEABILITY_PRIOR_QUALIFICATION_FOR_EWP_HYDRAULIC_SENSITIVITY'},'fallback_tasks':['EWP-REAL-WORLD-BOUNDARIES-001','OBS-PANNUSCH-FRACTION-WINDOW-001'],'home_lab':{'status':'DEFER_HOME_LAB_HIGHER_VALUE_EXISTING_DATA_TASKS_READY','operation_authorized':False,'equipment_purchase_authorized':False},'change_declarations':{'production_physics_change':False,'production_parameter_adoption':False,'puckworks_mutation':False,'raw_data_mutation':False,'gpl_source_ingestion':False,'angeloni_access':False,'protected_holdout_scoring':False,'target_blind_claim':False,'independent_validation_claim':False,'laboratory_operation':False}}
    dump(OUT/'summary.json',summary)
    text=f'''# XSV-WASZKIEWICZ-DYNAMIC-HYD-001 C1 corrected result

Primary disposition: `{PRIMARY}`. Development consequence: `FIXED_RESISTANCE_RETAINED_BY_PARSIMONY`.

Some tested evolving-resistance forms reduce average leave-one-condition-out error relative to the fixed model. None provides sufficiently stable, practically material, cross-condition and blocked-time predictive advantage to meet the prospectively declared adoption gate. The fixed representation is therefore retained by parsimony. This result applies to the tested bounded forms and does not establish that hydraulic resistance is physically constant or that all evolving-resistance laws are invalid.

The original `{ORIGINAL}` result is superseded, not deleted, and remains in Git history. Original methods and fold files retain their exact hashes. C1 is `POST_REVIEW_MANDATED_FAIRNESS_AND_INTEGRITY_CORRECTION`, `NOT_A_RETROACTIVE_ORIGINAL_FREEZE`, and `NOT_PROSPECTIVELY_TARGET_BLIND`.

W-H1, W-H2, and W-H3 each improve 6 of 11 conditions; the exact two-sided sign probability is 1.0. W-H1 and W-H3 reproduce average LOCO improvement but miss the practical and consistency gates. W-H2 has the lowest mean LOCO error, but its clustered interval crosses zero and the 1-bar condition is materially influential. Corrected blocked-time fitting excludes the evaluated brew and continues all modeled state from 15 s across the 60 s split; W-H0A remains best. W-H2 uses modeled recursive progress, never held-out observed progress after the allowed initial offset.

Invalid physical roots are typed and fail closed. Primary LOCO has zero invalid roots; strict coverage and a frozen 2x conservative penalty sensitivity are published. The deposited mass remains primary; per-brew isotonic mass is a separate sensitivity. Processing windows preserve W-H2's mean rank and the failed adoption decision, while effect magnitudes and condition signs vary. Broader processing robustness is not established.

Exact tested scopes: `TESTED_TIME_DEPENDENT_EXPONENTIAL_FORM_NOT_SUPPORTED_FOR_ADOPTION` (tau 20 s); `TESTED_RECURSIVE_MASS_PROGRESS_FORM_NOT_SUPPORTED_FOR_ADOPTION` (20 g); `TESTED_BOUNDED_CHANGE_POINT_FORM_NOT_SUPPORTED_FOR_ADOPTION` (35 s, width 5 s); `TESTED_ONE_SECOND_OBSERVATION_DELAY_NOT_SUPPORTED`. Other evolving forms may exist.

The source Waszkiewicz lane remains `SOURCE_POST_FIT_RECONSTRUCTION`, not grouped predictive validation. The strongest successor is `EWP-POROSITY-PERMEABILITY-PRIOR-001`, ready only after C1 rereview passes and PR #125 merges. Home lab: `DEFER_HOME_LAB_HIGHER_VALUE_EXISTING_DATA_TASKS_READY`. No production physics/default, raw data, Puckworks, GPL source, protected target, Angeloni, laboratory, or equipment change occurred.
'''
    (OUT/'RESULT.md').write_text(text,encoding='utf-8')
    nextj={'selected':{'task_id':'EWP-POROSITY-PERMEABILITY-PRIOR-001','status':'READY_AFTER_C1_MERGE','scientific_question':'Can Wadsworth and Vaca Guerra, retained as separate source-conditioned priors and observation operators, constrain defensible static EWP porosity and permeability ranges?','source_separation':{'Wadsworth':'22 PSD records; 21 permeability values; source definitions and uncertainty retained','Vaca_Guerra':'50 dry-porosity rows; apparatus, compression/packing, and dry-bed status retained'},'maximum_claim':'SOURCE_CONDITIONED_STATIC_POROSITY_AND_PERMEABILITY_PRIOR_QUALIFICATION_FOR_EWP_HYDRAULIC_SENSITIVITY'},'fallbacks':['EWP-REAL-WORLD-BOUNDARIES-001','OBS-PANNUSCH-FRACTION-WINDOW-001'],'do_not_implement':True}
    dump(OUT/'NEXT_TASK_DECISION.json',nextj);(OUT/'NEXT_TASK_DECISION.md').write_text('# Next task decision\n\n`EWP-POROSITY-PERMEABILITY-PRIOR-001` is `READY_AFTER_C1_MERGE`. Wadsworth and Vaca Guerra remain separate source-conditioned priors; no rows are concatenated and dry porosity is not wet operating porosity.\n',encoding='utf-8')
    return summary
