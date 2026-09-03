#!/usr/bin/env python3
"""Frozen SCI-MD-011 executor. Phase A permits metadata preflight and synthetic data only."""
import argparse, json, math, os
from pathlib import Path
from sci_md_011_core import *
ROOT=Path(__file__).resolve().parents[1]
def verify_freeze(contract,freeze):
 if contract['task_id']!=TASK or freeze['task_id']!=TASK or tuple(contract['models'])!=MODELS or contract['metrics']['seed']!=SEED:raise ValueError('FROZEN_CONTRACT_MISMATCH')
 man=load_json(ROOT/'docs/analysis/sci_md_011/FREEZE_ARTIFACT_MANIFEST.json')
 for a in man['artifacts']:
  if sha256(ROOT/a['path'])!=a['sha256']:raise ValueError('FREEZE_ARTIFACT_CHANGED:'+a['path'])
 return sha256(ROOT/'docs/analysis/sci_md_011/FREEZE_ARTIFACT_MANIFEST.json')
def receipt(path,synthetic):
 r=load_json(path)
 if synthetic and r.get('synthetic') is True:return r
 required='SCI_MD_011_PRE_SCORE_FREEZE_SINGLE_INDEPENDENT_REVIEW_PASS_READY_FOR_EXECUTION'
 if r.get('task_id')!=TASK or r.get('disposition')!=required or r.get('phase_b_authorized') is not True:raise ValueError('PHASE_B_UNAUTHORIZED')
 if r.get('freeze_commit')!=git(ROOT,'rev-parse','HEAD') or r.get('freeze_tree')!=git(ROOT,'rev-parse','HEAD^{tree}'):raise ValueError('REVIEW_EXACT_HEAD_MISMATCH')
 return r
def load_real_metadata():
 idx=load_csv(ROOT/'docs/analysis/sci_md_010/ANALYSIS_ROW_INDEX.csv');folds=load_csv(ROOT/'docs/analysis/sci_md_010/FOLD_ASSIGNMENTS.csv');mem=load_csv(ROOT/'docs/analysis/sci_md_010/FOLD_MEMBERSHIP.csv')
 if len(idx)!=56 or len({r['physical_unit_id'] for r in idx})!=56 or len({r['condition_id'] for r in idx})!=11 or len(folds)!=11:raise ValueError('HANDOFF_CARDINALITY')
 for f in folds:
  tr={r['physical_unit_id'] for r in mem if r['outer_fold']==f['outer_fold'] and r['role']=='TRAIN'};te={r['physical_unit_id'] for r in mem if r['outer_fold']==f['outer_fold'] and r['role']=='EVALUATION'}
  if tr&te:raise ValueError('PHYSICAL_UNIT_LEAKAGE')
 # Integrity-only recomputation of the already accepted B1 predictions.
 b1=[r for r in load_csv(ROOT/'docs/analysis/sci_md_010/BREW_RESULTS.csv') if r['model_id']==MODELS[1]]
 fp={r['outer_fold']:json.loads(r['fitted_parameters']) for r in load_csv(ROOT/'docs/analysis/sci_md_010/FOLD_RESULTS.csv') if r['model_id']==MODELS[1]}
 err=max(abs(max(0,fp[r['outer_fold']]['intercept']+fp[r['outer_fold']]['linear']*float(r['line_pressure_bar'])+fp[r['outer_fold']]['quadratic']*float(r['line_pressure_bar'])**2)-float(r['predicted_flow_g_s'])) for r in b1)
 if err>1e-12:raise ValueError('B1_INTEGRITY_RECOMPUTATION_FAILED')
 return {'joined_rows':56,'distinct_physical_brews':56,'pressure_conditions':11,'outer_folds':11,'alias_duplication':0,'candidate_real_fits':0,'candidate_real_predictions':0,'candidate_real_scores':0,'b1_integrity_max_abs_error_g_s':err,'b1_integrity_tolerance_g_s':1e-12}
def synthetic_rows(kind='poro'):
 idx=load_csv(ROOT/'docs/analysis/sci_md_010/ANALYSIS_ROW_INDEX.csv');rows=[]
 for r in idx:
  p=float(r['condition_id'].replace('WASZ-COND-',''))
  if kind=='poro':y=predict(p,2.0,15.0,P1)[0]
  elif kind=='turnover':y=max(0,1.2-(p-8.)**2/30)
  elif kind=='leverage':y=.18*p+(20 if p==13 else 0)
  else:y=.15*p+.01*p*p
  rows.append({'source_row_id':r['source_row_id'],'physical_unit_id':r['physical_unit_id'],'condition_id':r['condition_id'],'line_pressure_bar':p,'flow_g_s':y})
 return rows
def partition(rows,fold):
 evalc=fold['group_id'];return [r for r in rows if r['condition_id']!=evalc],[r for r in rows if r['condition_id']==evalc]
def fit_quad(rows):
 wr=balanced(rows);A=[[0.]*3 for _ in range(3)];b=[0.]*3
 for r,w in wr:
  x=float(r['line_pressure_bar']);v=[1,x,x*x];y=float(r['flow_g_s'])
  for i in range(3):b[i]+=w*v[i]*y
  for i in range(3):
   for j in range(3):A[i][j]+=w*v[i]*v[j]
 for i in range(3):
  k=max(range(i,3),key=lambda z:abs(A[z][i]));A[i],A[k]=A[k],A[i];b[i],b[k]=b[k],b[i];q=A[i][i]
  for j in range(i,3):A[i][j]/=q
  b[i]/=q
  for k in range(3):
   if k!=i:
    q=A[k][i]
    for j in range(i,3):A[k][j]-=q*A[i][j]
    b[k]-=q*b[i]
 return {'a0':b[0],'a1':b[1],'a2':b[2]}
def run(rows):
 folds=load_csv(ROOT/'docs/analysis/sci_md_010/FOLD_ASSIGNMENTS.csv');results=[];brews=[]
 accepted=load_csv(ROOT/'docs/analysis/sci_md_010/BREW_RESULTS.csv')
 for fold in folds:
  train,test=partition(rows,fold);means=[]
  for c in sorted({r['condition_id'] for r in train}):means.append(sum(float(r['flow_g_s']) for r in train if r['condition_id']==c)/sum(r['condition_id']==c for r in train))
  scale=max(means)-min(means)
  for mid in MODELS:
   fail='';rootfails=0
   try:
    if mid==MODELS[0]:pars={'mean':sum(w*float(r['flow_g_s']) for r,w in balanced(train))};preds=[pars['mean']]*len(test)
    elif mid==MODELS[1]:pars=fit_quad(train);preds=[max(0,pars['a0']+pars['a1']*float(r['line_pressure_bar'])+pars['a2']*float(r['line_pressure_bar'])**2) for r in test]
    else:
     pars=fit(train,mid);preds=[]
     for r in test:
      try:preds.append(predict(float(r['line_pressure_bar']),pars['Qc_g_s'],pars['Pc_bar'],mid)[0])
      except ValueError:rootfails+=1;raise
   except ValueError as e:pars={};preds=[];fail=str(e)
   loss=math.sqrt(sum((float(r['flow_g_s'])-p)**2 for r,p in zip(test,preds))/len(test)) if preds else None
   results.append({'outer_fold':fold['outer_fold'],'evaluation_condition_id':fold['group_id'],'model_id':mid,'parameters':pars,'training_scale_g_s':scale,'rmse_g_s':loss,'normalized_loss':None if loss is None else loss/scale,'failure_reason':fail,'root_failures':rootfails,'test':test,'preds':preds})
   for r,p in zip(test,preds):
    e=p-float(r['flow_g_s']);brews.append({'outer_fold':fold['outer_fold'],'model_id':mid,'physical_unit_id':r['physical_unit_id'],'condition_id':r['condition_id'],'line_pressure_bar':r['line_pressure_bar'],'observed_flow_g_s':r['flow_g_s'],'predicted_flow_g_s':p,'error_g_s':e,'squared_error_g_s2':e*e,'training_scale_g_s':scale})
 return results,brews
def diagnostics(results):
 out={}
 for mid in MODELS:
  rr=[r for r in results if r['model_id']==mid];p=[sum(float(x['line_pressure_bar']) for x in r['test'])/len(r['test']) for r in rr];o=[sum(float(x['flow_g_s']) for x in r['test'])/len(r['test']) for r in rr];y=[sum(r['preds'])/len(r['preds']) for r in rr]
  def slope(ids,z):
   xx=[p[i] for i in ids];yy=[z[i] for i in ids];xm=sum(xx)/len(xx);ym=sum(yy)/len(yy);return sum((a-xm)*(b-ym) for a,b in zip(xx,yy))/sum((a-xm)**2 for a in xx)
  low=[i for i,x in enumerate(p) if x<=5.25];high=[i for i,x in enumerate(p) if x>=8.5];ls=slope(low,y);hs=slope(high,y)
  out[mid]={'predicted_low_slope':ls,'predicted_high_slope':hs,'low_direction_ok':ls>0,'high_direction_ok':hs<=0,'slope_attenuation':ls-hs,'distance_high_slope_from_zero':abs(hs),'structural_saturation_capability':mid in (P1,E2C),'structural_turnover_capability':False if mid in (P1,E2C) else None,'condition_means':[{'condition_id':r['evaluation_condition_id'],'line_pressure_bar':x,'observed':a,'predicted':b} for r,x,a,b in zip(rr,p,o,y)]}
 return out
def write_result(out,results,br,mh,synthetic):
 out.mkdir(parents=True);fr=[{k:r[k] for k in ('outer_fold','evaluation_condition_id','model_id','training_scale_g_s','rmse_g_s','normalized_loss','failure_reason','root_failures')}|{'fitted_parameters':json.dumps(r['parameters'],sort_keys=True)} for r in results]
 write_csv(out/'FOLD_RESULTS.csv',list(fr[0]),fr);write_csv(out/'BREW_RESULTS.csv',list(br[0]),br);loss={m:sum(r['normalized_loss'] for r in results if r['model_id']==m)/11 for m in MODELS};sc={r['outer_fold']:r['training_scale_g_s'] for r in results};pairs={};
 for a,b,key in [(MODELS[1],P1,'B1_P1'),(MODELS[1],E2C,'B1_E2C'),(P1,E2C,'P1_E2C')]:
  z=bootstrap(br,sc,a,b);z['point']=loss[a]-loss[b];pairs[key]=z
 diag=diagnostics(results);status={P1:candidate_status((pairs['B1_P1']['ci_low'],pairs['B1_P1']['ci_high']),diag[P1]),E2C:candidate_status((pairs['B1_E2C']['ci_low'],pairs['B1_E2C']['ci_high']),diag[E2C])};pair=candidate_status((pairs['P1_E2C']['ci_low'],pairs['P1_E2C']['ci_high']),diag[E2C]);disp,arch=overall(status,pair)
 write_csv(out/'AGGREGATE_RESULTS.csv',['model_id','normalized_loss','mean_rmse_g_s'],[{'model_id':m,'normalized_loss':loss[m],'mean_rmse_g_s':sum(r['rmse_g_s'] for r in results if r['model_id']==m)/11} for m in MODELS]);write_csv(out/'CONDITION_RESULTS.csv',['condition_id','model_id','normalized_loss'],[{'condition_id':r['evaluation_condition_id'],'model_id':r['model_id'],'normalized_loss':r['normalized_loss']} for r in results]);write_json(out/'PAIRWISE_COMPARISONS.json',pairs);write_json(out/'UNCERTAINTY_RESULTS.json',pairs);write_json(out/'PRESSURE_RESPONSE_DIAGNOSTICS.json',diag);write_csv(out/'PARAMETER_STABILITY.csv',['outer_fold','model_id','parameters'],[{'outer_fold':r['outer_fold'],'model_id':r['model_id'],'parameters':json.dumps(r['parameters'],sort_keys=True)} for r in results]);ident={f:{r['model_id']:r['parameters'].get('identifiability','NOT_APPLICABLE') for r in results if r['outer_fold']==f} for f in sorted({r['outer_fold'] for r in results})};write_json(out/'IDENTIFIABILITY_RESULTS.json',ident);write_json(out/'ARCHITECTURE_DECISION.json',{'disposition':disp,'architecture':arch,'candidate_status':status,'finite_vs_universal':pair,'current_full_ewp':'NOT_VALIDATED'});write_json(out/'EXPERIMENT_CONSEQUENCE.json',{'stage_f_authorized':False,'stage_d_authorized':False,'m01_adjudicated':False});write_json(out/'EXECUTION_STATE.json',{'synthetic':synthetic,'scoring_executed':not synthetic,'complete':True});write_json(out/'RUN_RECEIPT.json',{'task_id':TASK,'freeze_manifest_sha256':mh,'single_configuration':True,'synthetic':synthetic});write_json(out/'summary.json',{'disposition':disp,'architecture':arch,'synthetic':synthetic,'current_full_ewp_validated':False,'stage_f_authorized':False,'stage_d_authorized':False});(out/'RESULTS_SUMMARY.md').write_text(f'# SCI-MD-011 {"synthetic " if synthetic else ""}result\n\n`{disp}`\n');(out/'RESULT.md').write_text(f'# SCI-MD-011 result\n\n`{disp}`\n\nCurrent full EWP: NOT_VALIDATED. Physical validation: NOT_ESTABLISHED.\n');files=sorted(p for p in out.iterdir());write_json(out/'RESULT_ARTIFACT_MANIFEST.json',{'artifacts':[{'path':p.name,'sha256':sha256(p)} for p in files]})
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--contract',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--review-receipt',required=True);ap.add_argument('--output',required=True);ap.add_argument('--synthetic-test-mode',action='store_true');ap.add_argument('--real-binding-preflight-only',action='store_true');ap.add_argument('--synthetic-outcome',choices=['poro','turnover','quadratic','leverage'],default='poro');a=ap.parse_args();out=Path(a.output)
 if out.exists() and any(out.iterdir()):raise ValueError('DUPLICATE_RESULT_GUARD')
 c=load_json(a.contract);f=load_json(a.freeze);mh=verify_freeze(c,f);receipt(a.review_receipt,a.synthetic_test_mode or a.real_binding_preflight_only)
 if a.real_binding_preflight_only:out.mkdir(parents=True);write_json(out/'REAL_BINDING_PREFLIGHT.json',load_real_metadata());return
 if not a.synthetic_test_mode:raise ValueError('REAL_EXECUTION_REQUIRES_EXTERNAL_EXACT_REVIEW_AND_PHASE_B_PACKAGING')
 results,br=run(synthetic_rows(a.synthetic_outcome));write_result(out,results,br,mh,True)
if __name__=='__main__':main()
