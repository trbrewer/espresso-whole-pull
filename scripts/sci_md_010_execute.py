#!/usr/bin/env python3
"""Execute reviewed SCI-MD-010 exact-reuse plan or metadata preflight."""
from __future__ import annotations
import argparse,platform,sys
from datetime import datetime,timezone
from pathlib import Path
from sci_md_010_core import *
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/analysis/sci_md_010'
def manifest_ok():
 m=load_json(D/'FREEZE_ARTIFACT_MANIFEST.json')
 for a in m['artifacts']:
  if sha256(ROOT/a['path'])!=a['sha256']:raise ValueError('FREEZE_ARTIFACT_CHANGED:'+a['path'])
 if canonical_sha(m['artifacts'])!=m['aggregate_content_sha256']:raise ValueError('FREEZE_AGGREGATE_CHANGED')
 return sha256(D/'FREEZE_ARTIFACT_MANIFEST.json')
def preflight(freeze,receipt,out,test_mode):
 pw=resolve_puckworks();mh=manifest_ok();validate_artifacts(ROOT,load_json(D/'INPUT_ARTIFACT_REGISTER.json'),pw)
 rows=load_csv(D/'ANALYSIS_ROW_INDEX.csv');members=load_csv(D/'FOLD_MEMBERSHIP.csv');validate_no_leakage(rows,members)
 specs=load_json(D/'MODEL_SPECIFICATIONS.json')['models']
 for model in specs:
  if model['callable'] not in {'EXACT_REUSE_ONLY','UNAVAILABLE'}:
   for name in model['callable'].split(','):
    if name not in MODEL_CALLABLES:raise ValueError('MODEL_CALLABLE_MISSING:'+name)
  if sha256(ROOT/model['implementation_file'])!=model['implementation_sha256']:raise ValueError('MODEL_IMPLEMENTATION_CHANGED:'+model['model_id'])
 verify_receipt(receipt,freeze,mh,ROOT,allow_synthetic=test_mode)
 if out.exists() and any(out.iterdir()):raise ValueError('OUTPUT_IDENTITY_ALREADY_USED')
 out.mkdir(parents=True,exist_ok=True)
 write_json(out/'PREFLIGHT_RECEIPT.json',{'task_id':'SCI-MD-010','preflight_only':True,'sources_verified':True,'models_verified':len(specs),'rows_verified':len(rows),'folds_verified':len(load_csv(D/'FOLD_ASSIGNMENTS.csv')),'outer_scores_created':False})
 return mh
def real_execute(out,receipt,mh):
 fold=[]
 for r in load_csv(ROOT/'docs/analysis/xsv_waszkiewicz_dynamic_hyd_001/LEAVE_ONE_CONDITION_OUT_RESULTS.csv'):
  if r['model_id'] in {'W-H0A','W-H1','W-H2','W-H3'}:fold.append({'lane_id':'L-HYD','source_family':'waszkiewicz2025','outer_fold':'HYD-LOCO-'+r['condition_id'],'group_id':'WASZ-COND-'+r['condition_id'],'model_id':'HYD_B1_WH0A_FIXED_LOG_R' if r['model_id']=='W-H0A' else 'PRIOR_'+r['model_id'],'claim_level':'LEVEL_1_SOURCE_POST_FIT_RECONSTRUCTION','fit_status':'PRIOR_EXPOSED','prediction_status':'EXACT_SCORE_REUSE','primary_loss':r['nrmse'],'secondary_metrics':'{}','qualitative_trend_status':'PRIOR_RESULT','free_parameter_count':'2','training_group_count':'10','target_group_calibration':'false','numerical_status':'PRIOR_ACCEPTED','failure_reason':r['failed']})
 for r in load_csv(ROOT/'docs/analysis/xsv_pannusch_multimodel_001/LEAVE_ONE_MARCH_CONDITION_OUT.csv'):
  for mid,col in [('FRAC_B0_ORDINAL','ordinal_rmse'),('FRAC_B1_BOUNDARY_AWARE','boundary_rmse'),('FRAC_B2_PANNUSCH_FIXED','pannusch_rmse')]:fold.append({'lane_id':'L-FRAC','source_family':'pannusch2024','outer_fold':'FRAC-LOCO-'+r['omitted_condition'],'group_id':r['omitted_condition'],'model_id':mid,'claim_level':'SOURCE_INTERNAL_TARGET_EXPOSED_GROUPED_COMPARISON','fit_status':'PRIOR_EXPOSED','prediction_status':'EXACT_SCORE_REUSE','primary_loss':r[col],'secondary_metrics':'{}','qualitative_trend_status':'PRIOR_RESULT','free_parameter_count':'0' if mid.endswith('FIXED') else '12','training_group_count':'3','target_group_calibration':'false','numerical_status':'PRIOR_ACCEPTED','failure_reason':''})
 fields=['lane_id','source_family','outer_fold','group_id','model_id','claim_level','fit_status','prediction_status','primary_loss','secondary_metrics','qualitative_trend_status','free_parameter_count','training_group_count','target_group_calibration','numerical_status','failure_reason'];write_csv(out/'FOLD_RESULTS.csv',fields,fold)
 hyd=load_csv(ROOT/'docs/analysis/xsv_waszkiewicz_dynamic_hyd_001/MODEL_COMPARISON_RESULTS.csv');pan=load_csv(ROOT/'docs/analysis/xsv_pannusch_multimodel_001/MODEL_COMPARISON_RESULTS.csv');pann=next(x for x in pan if x['model']=='MODEL-PANNUSCH-FIXED')
 agg=[{'lane_id':'L-HYD','model_id':'HYD_B1_WH0A_FIXED_LOG_R','aggregate_loss':next(x['loco_condition_balanced_nrmse'] for x in hyd if x['model_id']=='W-H0A'),'comparator':'predecessor evolving forms','paired_delta':'PRIOR_RESULT','interval':'PRIOR_RESULT','condition_signs':'PRIOR_RESULT','materiality':'PREDICTIVE_RANKING_ONLY','lane_disposition':'SOURCE_CONDITIONED_RECONSTRUCTION_ONLY'},{'lane_id':'L-FRAC','model_id':'FRAC_B2_PANNUSCH_FIXED','aggregate_loss':pann['march_rmse'],'comparator':'FRAC_B1_BOUNDARY_AWARE','paired_delta':pann['difference_vs_boundary'],'interval':pann['paired_ci_low']+';'+pann['paired_ci_high'],'condition_signs':pann['condition_wins'],'materiality':'PREDICTIVE_RANKING_ONLY','lane_disposition':'NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE'}];write_csv(out/'AGGREGATE_RESULTS.csv',list(agg[0]),agg)
 write_csv(out/'PARAMETER_STABILITY.csv',['lane_id','model_id','status'],[{'lane_id':'L-HYD','model_id':'HYD_B1_WH0A_FIXED_LOG_R','status':'EXACT_PREDECESSOR_REFERENCED'},{'lane_id':'L-FRAC','model_id':'FRAC_B2_PANNUSCH_FIXED','status':'PUBLICATION_FIXED'}]);write_json(out/'IDENTIFIABILITY_RESULTS.json',{'structural_nonidentifiability_claimed':False,'L-HYD':'SOURCE_RECONSTRUCTION_ONLY','L-FRAC':'CURRENT_EWP_NOT_EVALUABLE'})
 sf=['subsystem','lane_id','model_id','strongest_claim_level','naive_baseline_result','competitive_baseline_result','source_native_result','reduced_ewp_result','full_ewp_result','stable_advantage','material_advantage','trend_status','calibration_burden','identifiability','architecture_decision','evidence_limit'];score=[dict(zip(sf,['hydraulics','L-HYD','HYD_E2_CURRENT_EWP_UNAVAILABLE','LEVEL_1','NOT_NEWLY_SCORED','PRIOR_ACCEPTED','NA','NOT_NEWLY_SCORED','UNAVAILABLE','false','NOT_ESTABLISHED','PRIOR','source post-fit','NOT_ADJUDICATED','NOT_ADJUDICATED','current EWP unavailable'])),dict(zip(sf,['chemistry','L-FRAC','FRAC_E2_CURRENT_EWP_UNAVAILABLE','TARGET_EXPOSED','PANNUSCH_BEATS_ORDINAL_PRIOR','NO_PANNUSCH_ADVANTAGE_PRIOR','PRIOR_EXECUTED','NOT_NEWLY_SCORED','UNAVAILABLE','false','NOT_ESTABLISHED','PRIOR','source exposed','NOT_ADJUDICATED','NOT_ADJUDICATED','current EWP unavailable']))];write_csv(out/'MODEL_UTILITY_SCORECARD.csv',sf,score)
 lf=['item_id','item_type','primary_limitation','supporting_evidence','counterfactual_resolution','would_resolution_change_model_decision','data_problem','analysis_problem','architecture_problem','model_form_problem','exact_next_action'];write_csv(out/'LIMITATION_ATTRIBUTION.csv',lf,[dict(zip(lf,['L-HYD','lane','MODEL_INPUT_REQUIREMENT','no exact E2 artifact','qualified observer','true','false','false','true','not adjudicated','owner decision'])),dict(zip(lf,['L-FRAC','lane','OBSERVATION_OPERATOR','no EWP fraction mapping','observable adapter','true','false','true','true','not adjudicated','owner decision']))])
 write_json(out/'ARCHITECTURE_DECISIONS.json',{'decisions':[{'subsystem':'hydraulics','decision':'NOT_ADJUDICATED','reason':'current EWP unavailable'},{'subsystem':'chemistry','decision':'NOT_ADJUDICATED','reason':'source-native no B1 advantage; current EWP unavailable'}],'claim_ceiling':CLAIM_CEILING});graph=load_json(D/'END_TO_END_OBSERVABILITY_GRAPH.json');graph['result']='LEVEL_4_NOT_ESTABLISHED';write_json(out/'END_TO_END_OBSERVABILITY_GRAPH.json',graph)
 write_json(out/'EXPERIMENT_NECESSITY_DECISION.json',{'sci_ed_003_status':'COMPLETE','stage_f_authorized':False,'stage_d_authorized':False,'recommendation':'EXISTING_DATA_CANNOT_ADJUDICATE_EXPERIMENT_NECESSITY','rationale':'current EWP unavailable in selected lanes','next_owner_decision':'none automatically authorized'})
 summary={'task_id':'SCI-MD-010','disposition':'SCI_MD_010_EXISTING_DATA_INSUFFICIENT_FOR_PREDICTIVE_UTILITY_EXACT_GAPS_IDENTIFIED','scoring_executed':True,'new_target_scores':False,'prior_scores_reused':True,'physical_validation':'NOT_ESTABLISHED'};write_json(out/'summary.json',summary);(out/'RESULTS_SUMMARY.md').write_text('# SCI-MD-010 result\n\nExact prior scores reused; current EWP unavailable.\n');(out/'RESULT.md').write_text('# SCI-MD-010 result\n\nRetrospective source evidence only; current EWP utility not adjudicated.\n')
 write_json(out/'EXECUTION_STATE.json',{'task_id':'SCI-MD-010','freeze_manifest_sha256':mh,'output_identity':out.name,'scoring_executed':True});write_json(out/'RUN_RECEIPT.json',{'task_id':'SCI-MD-010','freeze_manifest_sha256':mh,'review_receipt_sha256':canonical_sha(receipt),'environment':{'python':sys.version.split()[0],'os':platform.system()},'ended_utc':datetime.now(timezone.utc).isoformat(),'folds_attempted':15,'cases_executed':0,'score_rows_reused':len(fold),'completion_status':'COMPLETE','scoring_executed':True})
 files=sorted(x for x in out.iterdir() if x.name!='RESULT_ARTIFACT_MANIFEST.json');write_json(out/'RESULT_ARTIFACT_MANIFEST.json',{'artifacts':[{'path':x.name,'sha256':sha256(x)} for x in files]})
def main():
 p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--freeze',required=True);p.add_argument('--review-receipt',required=True);p.add_argument('--output',required=True);p.add_argument('--preflight-only',action='store_true');p.add_argument('--synthetic-test-mode',action='store_true',help=argparse.SUPPRESS);a=p.parse_args();freeze=load_json(a.freeze);receipt=load_json(a.review_receipt);out=Path(a.output);mh=preflight(freeze,receipt,out,a.synthetic_test_mode)
 if a.preflight_only:return
 (out/'PREFLIGHT_RECEIPT.json').unlink()
 if a.synthetic_test_mode:synthetic_run(out)
 else:real_execute(out,receipt,mh)
if __name__=='__main__':main()
