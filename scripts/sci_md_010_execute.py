#!/usr/bin/env python3
"""Contract-driven SCI-MD-010 executor; Phase A uses preflight/synthetic only."""
import argparse,random,sys
from pathlib import Path
from sci_md_010_core import *
ROOT=Path(__file__).resolve().parents[1]
def rel(contract,key):return ROOT/contract[key]
def verify_manifest():
 p=ROOT/'docs/analysis/sci_md_010/FREEZE_ARTIFACT_MANIFEST.json';m=load_json(p)
 for a in m['artifacts']:
  if sha256(ROOT/a['path'])!=a['sha256']:raise ValueError('FREEZE_ARTIFACT_CHANGED:'+a['path'])
 return sha256(p)
def preflight(contract,freeze,receipt,out,test=False):
 mh=verify_manifest();pw=resolve_puckworks();validate_artifacts(ROOT,load_json(rel(contract,'input_register')),pw)
 specs=load_json(rel(contract,'models'))['models'];frozen={m['model_id'] for m in specs}
 if set(contract['model_ids'])!=frozen:raise ValueError('CONTRACT_MODEL_REGISTRY_MISMATCH')
 for m in specs:
  if sha256(ROOT/m['implementation_file'])!=m['implementation_sha256']:raise ValueError('MODEL_IMPLEMENTATION_CHANGED')
  for name in m['callable'].split(','):
   if name not in MODEL_CALLABLES:raise ValueError('CALLABLE_NOT_FROZEN:'+name)
 verify_receipt(receipt,freeze,mh,ROOT,test)
 if out.exists() and any(out.iterdir()):raise ValueError('OUTPUT_IDENTITY_ALREADY_USED')
 out.mkdir(parents=True,exist_ok=True);write_json(out/'PREFLIGHT_RECEIPT.json',{'contract_sha256':sha256(CONTRACT_PATH),'model_ids':sorted(frozen),'outer_scores_created':False})
 return specs,mh,pw
def load_real(contract,pw):
 reg=load_json(rel(contract,'input_register'));a=next(x for x in reg['artifacts'] if x['artifact_id']=='WASZ_OBSERVATIONS');raw=load_csv(pw/a['path']);allowed={r['shot_or_brew_id'] for r in load_csv(rel(contract,'row_index'))}
 return [{**r,'group_id':'WASZ-COND-'+r['reference_pressure_round__bar']} for r in raw if r['shot_id'] in allowed and 150<=int(r['time_index'])<=949]
def run_contract(contract,rows):
 specs=load_json(rel(contract,'models'))['models'];mids=[m['model_id'] for m in specs];folds=load_csv(rel(contract,'folds'));all_groups=sorted({r['group_id'] for r in rows});out=[]
 for f in folds:
  train=[g for g in all_groups if g!=f['group_id']]
  for result in execute_fold_models(rows,train,f['group_id'],mids):out.append(result)
 return out
def write_results(out,results,contract,mh,synthetic):
 fields=['lane_id','outer_fold','group_id','model_id','primary_loss','fit_status','prediction_status','target_group_calibration'];rows=[]
 for r in results:rows.append({'lane_id':'L-HYD','outer_fold':'LOCO-'+r['group_id'],'group_id':r['group_id'],'model_id':r['model_id'],'primary_loss':r['primary_loss'],'fit_status':'PASS','prediction_status':'NEW_REAL_PREDICTION' if not synthetic else 'SYNTHETIC','target_group_calibration':'false'})
 write_csv(out/'FOLD_RESULTS.csv',fields,rows);models=sorted({r['model_id'] for r in results});agg=[]
 for m in models:
  vals=[r['primary_loss'] for r in results if r['model_id']==m];agg.append({'model_id':m,'primary_loss':sum(vals)/len(vals)})
 by_model={a['model_id']:a['primary_loss'] for a in agg};paired=[]
 by_fold={(r['group_id'],r['model_id']):r['primary_loss'] for r in results}
 for group in sorted({r['group_id'] for r in results}):paired.append(by_fold[(group,'HYD_B1_PRESSURE_LINEAR')]-by_fold[(group,'HYD_E1_LUMPED_DARCY')])
 rng=random.Random(20260902);boots=[sum(rng.choice(paired) for _ in paired)/len(paired) for _ in range(2000)];boots.sort();delta=sum(paired)/len(paired);lo=boots[int(.025*len(boots))];hi=boots[int(.975*len(boots))-1]
 for a in agg:a.update({'paired_delta_b1_minus_e1':delta if a['model_id']=='HYD_E1_LUMPED_DARCY' else '','paired_delta_ci_low':lo if a['model_id']=='HYD_E1_LUMPED_DARCY' else '','paired_delta_ci_high':hi if a['model_id']=='HYD_E1_LUMPED_DARCY' else ''})
 write_csv(out/'AGGREGATE_RESULTS.csv',['model_id','primary_loss','paired_delta_b1_minus_e1','paired_delta_ci_low','paired_delta_ci_high'],agg);best=min(agg,key=lambda x:x['primary_loss'])['model_id']
 tol=1e-12
 if by_model['HYD_E1_LUMPED_DARCY']+tol<by_model['HYD_B1_PRESSURE_LINEAR'] and lo>0:decision='RETAIN_AS_MECHANISTIC_CORE'
 elif abs(by_model['HYD_E1_LUMPED_DARCY']-by_model['HYD_B1_PRESSURE_LINEAR'])<=tol or lo<=0<=hi:decision='SIMPLIFY_OR_REPARAMETERIZE'
 else:decision='NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE'
 write_json(out/'ARCHITECTURE_DECISIONS.json',{'calculated_best_model':best,'paired_delta_b1_minus_e1':delta,'paired_delta_95pct':[lo,hi],'decision':decision});write_json(out/'EXPERIMENT_NECESSITY_DECISION.json',{'stage_f_authorized':False,'stage_d_authorized':False,'recommendation':'DEFER_PENDING_ARCHITECTURE_RESULT'});write_csv(out/'MODEL_UTILITY_SCORECARD.csv',['model_id','primary_loss','paired_delta_b1_minus_e1','paired_delta_ci_low','paired_delta_ci_high'],agg)
 state={'scoring_executed':not synthetic,'new_real_predictions_generated':not synthetic,'new_real_scores_generated':not synthetic,'prior_scores_materialized':False,'ewp_or_reduced_ewp_scored':not synthetic,'synthetic':synthetic};write_json(out/'EXECUTION_STATE.json',state);write_json(out/'RUN_RECEIPT.json',{'freeze_manifest_sha256':mh,**state});write_json(out/'summary.json',{'best_model':best,'architecture_decision':decision,**state});files=sorted(p for p in out.iterdir() if p.name!='RESULT_ARTIFACT_MANIFEST.json');write_json(out/'RESULT_ARTIFACT_MANIFEST.json',{'artifacts':[{'path':p.name,'sha256':sha256(p)} for p in files]})
def synthetic_rows(sign=1):
 rows=[]
 for g,p in [(f'WASZ-COND-{x}',float(x)) for x in ['1.0','2.0','3.5','4.0','5.0','6.0','7.0','8.0','9.0','11.0','13.0']]:
  for i in range(4):rows.append({'group_id':g,'basket_pressure__bar':str(p),'mass_flow_rate__g_per_s':str(sign*2*p+i*0.0)})
 return rows
def main():
 global CONTRACT_PATH
 p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--freeze',required=True);p.add_argument('--review-receipt',required=True);p.add_argument('--output',required=True);p.add_argument('--preflight-only',action='store_true');p.add_argument('--synthetic-test-mode',action='store_true',help=argparse.SUPPRESS);a=p.parse_args();CONTRACT_PATH=Path(a.contract).resolve();contract=load_json(CONTRACT_PATH);freeze=load_json(a.freeze);receipt=load_json(a.review_receipt);out=Path(a.output);specs,mh,pw=preflight(contract,freeze,receipt,out,a.synthetic_test_mode)
 if a.preflight_only:return
 (out/'PREFLIGHT_RECEIPT.json').unlink();rows=synthetic_rows() if a.synthetic_test_mode else load_real(contract,pw);results=run_contract(contract,rows);write_results(out,results,contract,mh,a.synthetic_test_mode)
if __name__=='__main__':main()
