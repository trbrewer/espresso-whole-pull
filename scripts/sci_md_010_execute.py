#!/usr/bin/env python3
"""Contract-driven R3 equilibrium hydraulic executor; Phase A uses synthetic/preflight only."""
import argparse,json,math,random
from pathlib import Path
from sci_md_010_core import *
ROOT=Path(__file__).resolve().parents[1]
def cpath(c,k): return ROOT/c[k]
def verify_manifest():
 p=ROOT/'docs/analysis/sci_md_010/FREEZE_ARTIFACT_MANIFEST.json';m=load_json(p)
 for a in m['artifacts']:
  if sha256(ROOT/a['path'])!=a['sha256']:raise ValueError('FREEZE_ARTIFACT_CHANGED:'+a['path'])
 return sha256(p)
def preflight(c,f,receipt,out,test=False):
 mh=verify_manifest();pw=resolve_puckworks();reg=load_json(cpath(c,'input_register'));validate_artifacts(ROOT,reg,pw);specs=load_json(cpath(c,'models'))['models'];ids={m['model_id'] for m in specs}
 if ids!=set(c['model_ids']):raise ValueError('CONTRACT_MODEL_REGISTRY_MISMATCH')
 for m in specs:
  if sha256(ROOT/m['implementation_file'])!=m['implementation_sha256']:raise ValueError('MODEL_IMPLEMENTATION_CHANGED')
  if any(n not in MODEL_CALLABLES for n in m['callable'].split(',')):raise ValueError('CALLABLE_NOT_FROZEN')
 verify_receipt(receipt,f,mh,ROOT,test)
 if out.exists() and any(out.iterdir()):raise ValueError('OUTPUT_IDENTITY_ALREADY_USED')
 out.mkdir(parents=True,exist_ok=True);write_json(out/'PREFLIGHT_RECEIPT.json',{'contract_sha256':sha256(CONTRACT_PATH),'outer_scores_created':False,'models':sorted(ids)});return mh,pw,reg
def load_real(c,pw,reg):
 eq=next(a for a in reg['artifacts'] if a['artifact_id']=='WASZ_EQUILIBRIUM');tr=next(a for a in reg['artifacts'] if a['artifact_id']=='WASZ_LINE_PRESSURE');indexed={r['source_row_id']:r for r in load_csv(cpath(c,'row_index')) if r['included']=='true'};target={r['shot_id']:r for r in load_csv(pw/eq['path']) if r['window']=='endpoint_100s' and r['shot_id'] in indexed};line={r['shot_id']:r for r in load_csv(pw/tr['path']) if r['shot_id'] in indexed and int(r['time_index'])==999}
 if len(indexed)!=56 or set(target)!=set(indexed) or set(line)!=set(indexed):raise ValueError('EQUILIBRIUM_ROW_BINDING_MISMATCH')
 rows=[]
 for sid,idx in indexed.items():
  frozen=float(idx['condition_id'].removeprefix('WASZ-COND-'));observed=float(target[sid]['reference_pressure_round__bar'])
  if abs(frozen-observed)>c['identity_pressure_tolerance_bar']:raise ValueError('SOURCE_PRESSURE_INCOMPATIBLE_WITH_FROZEN_ID:'+sid)
  rows.append({'source_row_id':sid,'physical_unit_id':idx['physical_unit_id'],'condition_id':idx['condition_id'],'line_pressure_bar':line[sid]['pressure__bar'],'flow_g_s':target[sid]['mass_flow_rate__g_per_s']})
 if len(rows)!=56 or len({r['physical_unit_id'] for r in rows})!=56 or len({r['condition_id'] for r in rows})!=11:raise ValueError('REAL_BINDING_CARDINALITY_MISMATCH')
 return rows
def validate_all_partitions(c,rows):
 folds=load_csv(cpath(c,'folds'))
 for fold in folds:partition(c,rows,fold)
 return {'joined_rows':len(rows),'physical_brews':len({r['physical_unit_id'] for r in rows}),'conditions':len({r['condition_id'] for r in rows}),'folds_partitioned':len(folds),'fit_performed':False,'predictions_generated':False,'scores_generated':False}
def partition(c,rows,fold):
 mem=[r for r in load_csv(cpath(c,'membership')) if r['outer_fold']==fold['outer_fold']];by={r['physical_unit_id']:r for r in rows};train=[by[m['physical_unit_id']] for m in mem if m['role']=='TRAIN'];test=[by[m['physical_unit_id']] for m in mem if m['role']=='EVALUATION']
 if set(x['condition_id'] for x in train)!=set(fold['training_groups'].split(';')) or {x['condition_id'] for x in test}!={fold['group_id']}:raise ValueError('FROZEN_MEMBERSHIP_DISAGREES')
 if {x['physical_unit_id'] for x in train}&{x['physical_unit_id'] for x in test}:raise ValueError('PHYSICAL_GROUP_LEAKAGE')
 return train,test
def execute(c,rows,cal):
 out=[]
 for fold in load_csv(cpath(c,'folds')):
  train,test=partition(c,rows,fold);means={g:sum(float(r['flow_g_s']) for r in train if r['condition_id']==g)/sum(r['condition_id']==g for r in train) for g in {r['condition_id'] for r in train}};scale=max(means.values())-min(means.values());scale_error='' if math.isfinite(scale) and scale>0 else 'TRAINING_SCALE_INVALID'
  for mid in c['model_ids']:
   failed=scale_error;roots=0
   try:
    if failed:raise ValueError(failed)
    if mid=='HYD_B0_TRAINING_MEAN':model=fit_condition_balanced_mean(train);pred=[model['mean']]*len(test)
    elif mid=='HYD_B1_PRESSURE_QUADRATIC':model=fit_condition_balanced_quadratic(train);pred=predict_quadratic(model,test)
    elif mid=='HYD_E1_LUMPED_DARCY':model=fit_machine_darcy(train,cal,(0,10));pred=predict_machine_darcy(model,test,cal)
    else:raise ValueError('UNFROZEN_MODEL')
   except ValueError as e:model={};pred=[];failed=str(e);roots=len(test)
   obs=[float(r['flow_g_s']) for r in test];phys=rmse(obs,pred) if pred else None;norm=phys/scale if phys is not None and not scale_error else None;out.append({'outer_fold':fold['outer_fold'],'model_id':mid,'training_conditions':fold['training_groups'],'evaluation_condition':fold['group_id'],'training_physical_unit_ids':[r['physical_unit_id'] for r in train],'evaluation_physical_unit_ids':[r['physical_unit_id'] for r in test],'training_scale_g_s':scale if not scale_error else None,'fit':model,'test':test,'pred':pred,'physical_loss':phys,'normalized_loss':norm,'failed_root_count':roots,'failure_reason':failed})
 return out
def diagnostics(results):
 out={}
 for mid in sorted({r['model_id'] for r in results}):
  rr=[r for r in results if r['model_id']==mid]
  if any(r['failure_reason'] or not r['pred'] for r in rr):out[mid]={'status':'UNAVAILABLE_FAILED_FOLD'};continue
  p=[sum(float(x['line_pressure_bar']) for x in r['test'])/len(r['test']) for r in rr];o=[sum(float(x['flow_g_s']) for x in r['test'])/len(r['test']) for r in rr];y=[sum(r['pred'])/len(r['pred']) for r in rr]
  def slope(ix,z):
   x=[p[i] for i in ix];v=[z[i] for i in ix];xm=sum(x)/len(x);vm=sum(v)/len(v);return sum((a-xm)*(b-vm) for a,b in zip(x,v))/sum((a-xm)**2 for a in x)
  low=[i for i,x in enumerate(p) if x<=5.25];high=[i for i,x in enumerate(p) if x>=8.5];ol,pl,oh,ph=slope(low,o),slope(low,y),slope(high,o),slope(high,y);pairs=[(i,j) for i in range(len(o)) for j in range(i+1,len(o)) if o[i]!=o[j]];concord=sum((o[j]-o[i])*(y[j]-y[i])>0 for i,j in pairs)/len(pairs);om=max(o);ym=max(y)
  out[mid]={'status':'COMPLETE','condition_means':[{'condition_id':r['evaluation_condition'],'line_pressure_bar':pp,'observed_flow_g_s':oo,'predicted_flow_g_s':yy} for r,pp,oo,yy in zip(rr,p,o,y)],'observed_low_slope':ol,'predicted_low_slope':pl,'observed_high_slope':oh,'predicted_high_slope':ph,'expected_low_direction':'POSITIVE','expected_high_direction':'NONPOSITIVE_OR_SATURATING','low_direction_ok':pl>0,'high_direction_ok':ph<=0,'observed_peak_conditions':[rr[i]['evaluation_condition'] for i,v in enumerate(o) if v==om],'predicted_peak_conditions':[rr[i]['evaluation_condition'] for i,v in enumerate(y) if v==ym],'spearman_tie_average':spearman(o,y),'ordering_concordance':concord,'ordering_denominator':len(pairs)}
 return out
def calculate_uncertainty(results,brew_rows):
 required=[r for r in results if r['model_id'] in {'HYD_B1_PRESSURE_QUADRATIC','HYD_E1_LUMPED_DARCY'}];failed=any(r['failure_reason'] or r['normalized_loss'] is None for r in required)
 if failed:return {'status':'BLOCKED'},failed
 losses={m:sum(r['normalized_loss'] for r in results if r['model_id']==m)/11 for m in {r['model_id'] for r in results}};scales={r['outer_fold']:r['training_scale_g_s'] for r in required};means={r['outer_fold']:sum(float(x['line_pressure_bar']) for x in r['test'])/len(r['test']) for r in required if r['model_id']=='HYD_E1_LUMPED_DARCY'};low=sorted(f for f,p in means.items() if p<=5.25);full=paired_bootstrap(brew_rows,scales);lowb=paired_bootstrap(brew_rows,scales,low);condition_deltas=[]
 for f in sorted(scales):
  b=next(r['normalized_loss'] for r in required if r['outer_fold']==f and r['model_id']=='HYD_B1_PRESSURE_QUADRATIC');e=next(r['normalized_loss'] for r in required if r['outer_fold']==f and r['model_id']=='HYD_E1_LUMPED_DARCY');condition_deltas.append({'outer_fold':f,'normalized_delta_b1_minus_e1':b-e})
 low_point=sum(x['normalized_delta_b1_minus_e1'] for x in condition_deltas if x['outer_fold'] in low)/len(low)
 return {'status':'COMPLETE','model_losses':losses,'normalized_delta_b1_minus_e1':losses['HYD_B1_PRESSURE_QUADRATIC']-losses['HYD_E1_LUMPED_DARCY'],'normalized_delta_ci_low':full['low'],'normalized_delta_ci_high':full['high'],'low_pressure_normalized_delta_b1_minus_e1':low_point,'low_pressure_normalized_delta_ci_low':lowb['low'],'low_pressure_normalized_delta_ci_high':lowb['high'],'condition_level_paired_differences':condition_deltas,'bootstrap_unit':'condition_then_paired_brew','bootstrap_refit':False,'bootstrap_seed':R3_SEED,'bootstrap_replicates':2000,'quantile_convention':full['quantile_convention'],'materiality_status':'PREDICTIVE_RANKING_ONLY'},False
def decide(diag,unc,failed=False):
 d=diag.get('HYD_E1_LUMPED_DARCY',{});full=None if unc.get('status')!='COMPLETE' else (unc['normalized_delta_ci_low'],unc['normalized_delta_ci_high']);low=None if unc.get('status')!='COMPLETE' else (unc['low_pressure_normalized_delta_ci_low'],unc['low_pressure_normalized_delta_ci_high']);lane=map_r4_result(failed or d.get('status')!='COMPLETE',d.get('low_direction_ok',False),d.get('high_direction_ok',False),full,low);return lane,ARCHITECTURE_MAP[lane]
def write_results(out,results,c,mh,synthetic):
 fr=[];br=[]
 for r in results:
  fr.append({'outer_fold':r['outer_fold'],'model_id':r['model_id'],'training_condition_ids':r['training_conditions'],'evaluation_condition_id':r['evaluation_condition'],'training_physical_unit_ids':';'.join(r['training_physical_unit_ids']),'evaluation_physical_unit_ids':';'.join(r['evaluation_physical_unit_ids']),'training_condition_count':len(r['training_conditions'].split(';')),'training_brew_count':len(r['training_physical_unit_ids']),'evaluation_brew_count':len(r['test']),'training_scale_g_s':'' if r['training_scale_g_s'] is None else r['training_scale_g_s'],'fitted_parameters':json.dumps(r['fit'],sort_keys=True),'parameter_bound_status':r['fit'].get('bound_status','NA'),'fit_status':'PASS' if not r['failure_reason'] else 'FAIL','prediction_status':('FAIL' if r['failure_reason'] else 'SYNTHETIC' if synthetic else 'PASS'),'physical_loss_g_s':'' if r['physical_loss'] is None else r['physical_loss'],'normalized_loss':'' if r['normalized_loss'] is None else r['normalized_loss'],'failed_root_count':r['failed_root_count'],'failure_reason':r['failure_reason']})
  for x,p in zip(r['test'],r['pred']):
   err=p-float(x['flow_g_s']);br.append({'outer_fold':r['outer_fold'],'model_id':r['model_id'],'physical_unit_id':x['physical_unit_id'],'condition_id':x['condition_id'],'line_pressure_bar':x['line_pressure_bar'],'observed_flow_g_s':x['flow_g_s'],'predicted_flow_g_s':p,'error_g_s':err,'squared_error_g_s2':err*err,'training_scale_g_s':r['training_scale_g_s']})
 diag=diagnostics(results);unc,failed=calculate_uncertainty(results,br);lane,arch=decide(diag,unc,failed);recommendation=experiment_from_architecture(arch);losses=unc.get('model_losses',{});agg=[{'model_id':m,'normalized_loss':losses.get(m,''),'normalized_delta_b1_minus_e1':unc.get('normalized_delta_b1_minus_e1','') if m=='HYD_E1_LUMPED_DARCY' else '','normalized_delta_ci_low':unc.get('normalized_delta_ci_low','') if m=='HYD_E1_LUMPED_DARCY' else '','normalized_delta_ci_high':unc.get('normalized_delta_ci_high','') if m=='HYD_E1_LUMPED_DARCY' else '','low_pressure_normalized_delta_b1_minus_e1':unc.get('low_pressure_normalized_delta_b1_minus_e1','') if m=='HYD_E1_LUMPED_DARCY' else '','low_pressure_normalized_delta_ci_low':unc.get('low_pressure_normalized_delta_ci_low','') if m=='HYD_E1_LUMPED_DARCY' else '','low_pressure_normalized_delta_ci_high':unc.get('low_pressure_normalized_delta_ci_high','') if m=='HYD_E1_LUMPED_DARCY' else '','materiality_status':'PREDICTIVE_RANKING_ONLY'} for m in c['model_ids']]
 write_csv(out/'FOLD_RESULTS.csv',list(fr[0]),fr);write_csv(out/'BREW_RESULTS.csv',list(br[0]) if br else ['outer_fold','model_id','physical_unit_id','condition_id','line_pressure_bar','observed_flow_g_s','predicted_flow_g_s','error_g_s','squared_error_g_s2','training_scale_g_s'],br);write_json(out/'PRESSURE_RESPONSE_DIAGNOSTICS.json',diag);write_json(out/'UNCERTAINTY_RESULTS.json',unc);write_csv(out/'AGGREGATE_RESULTS.csv',list(agg[0]),agg);write_csv(out/'CONDITION_RESULTS.csv',['condition_id','model_id','normalized_loss'],[{'condition_id':r['evaluation_condition'],'model_id':r['model_id'],'normalized_loss':'' if r['normalized_loss'] is None else r['normalized_loss']} for r in results]);write_csv(out/'PARAMETER_STABILITY.csv',['outer_fold','model_id','parameters'],[{'outer_fold':r['outer_fold'],'model_id':r['model_id'],'parameters':json.dumps(r['fit'],sort_keys=True)} for r in results]);write_json(out/'IDENTIFIABILITY_RESULTS.json',{'E1':'one effective conductance only; full EWP quantities not identified'});write_json(out/'ARCHITECTURE_DECISIONS.json',{'lane_result':lane,'reduced_E1':arch,'current_full_E2':'NOT_ADJUDICATED'});write_json(out/'EXPERIMENT_NECESSITY_DECISION.json',{'derived_from_architecture':arch,'recommendation':recommendation,'m01_absolute_chemistry_adjudicated':False,'stage_f_authorized':False,'stage_d_authorized':False});write_csv(out/'MODEL_UTILITY_SCORECARD.csv',list(agg[0]),agg);write_csv(out/'LIMITATION_ATTRIBUTION.csv',['item','limitation'],[{'item':'current_full_E2','limitation':'NOT_ADJUDICATED'}]);(out/'RESULTS_SUMMARY.md').write_text(('# Synthetic result\n' if synthetic else '# SCI-MD-010 result\n')+lane+'\n');(out/'RESULT.md').write_text('# Result\n\n'+lane+'\n')
 required_complete=not failed;real=not synthetic;state={'scoring_attempted':real,'scoring_completed':real and required_complete,'scoring_executed':real and required_complete,'new_real_predictions_generated':real and required_complete,'new_real_scores_generated':real and required_complete,'prior_scores_materialized':False,'ewp_or_reduced_ewp_scored':real and required_complete,'synthetic':synthetic};write_json(out/'EXECUTION_STATE.json',state);write_json(out/'RUN_RECEIPT.json',{'freeze_manifest_sha256':mh,'contract_sha256':sha256(CONTRACT_PATH),'freeze_sha256':sha256(FREEZE_PATH),'review_receipt_sha256':sha256(REVIEW_PATH),**state});write_json(out/'summary.json',{'lane_result':lane,'architecture_decision':arch,'experiment_recommendation':recommendation,**state});files=sorted(p for p in out.iterdir() if p.name!='RESULT_ARTIFACT_MANIFEST.json');write_json(out/'RESULT_ARTIFACT_MANIFEST.json',{'artifacts':[{'path':p.name,'sha256':sha256(p)} for p in files]})
def synthetic_rows():
 cal={'a':.017184292098914252,'b':.03670858658698296,'c':.2831597837775055};rows=[]
 for r in load_csv(ROOT/'docs/analysis/sci_md_010/ANALYSIS_ROW_INDEX.csv'):
  p=float(r['condition_id'].removeprefix('WASZ-COND-'));rows.append({'source_row_id':r['source_row_id'],'physical_unit_id':r['physical_unit_id'],'condition_id':r['condition_id'],'line_pressure_bar':str(p),'flow_g_s':str(solve_machine_darcy(p,.18,cal))})
 return rows
def main():
 global CONTRACT_PATH,FREEZE_PATH,REVIEW_PATH
 ap=argparse.ArgumentParser();ap.add_argument('--contract',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--review-receipt',required=True);ap.add_argument('--output',required=True);ap.add_argument('--preflight-only',action='store_true');ap.add_argument('--real-binding-preflight-only',action='store_true');ap.add_argument('--synthetic-test-mode',action='store_true',help=argparse.SUPPRESS);a=ap.parse_args();CONTRACT_PATH=Path(a.contract).resolve();FREEZE_PATH=Path(a.freeze).resolve();REVIEW_PATH=Path(a.review_receipt).resolve();c=load_json(CONTRACT_PATH);f=load_json(FREEZE_PATH);receipt=load_json(REVIEW_PATH);out=Path(a.output);mh,pw,reg=preflight(c,f,receipt,out,a.synthetic_test_mode)
 if a.real_binding_preflight_only:
  report=validate_all_partitions(c,load_real(c,pw,reg));write_json(out/'REAL_BINDING_PREFLIGHT.json',report);return
 if a.preflight_only:return
 (out/'PREFLIGHT_RECEIPT.json').unlink();rows=synthetic_rows() if a.synthetic_test_mode else load_real(c,pw,reg);write_results(out,execute(c,rows,c['machine_calibration']),c,mh,a.synthetic_test_mode)
if __name__=='__main__':main()
