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
 eq=next(a for a in reg['artifacts'] if a['artifact_id']=='WASZ_EQUILIBRIUM');tr=next(a for a in reg['artifacts'] if a['artifact_id']=='WASZ_LINE_PRESSURE');wanted={r['source_row_id'] for r in load_csv(cpath(c,'row_index')) if r['included']=='true'};target={r['shot_id']:r for r in load_csv(pw/eq['path']) if r['window']=='endpoint_100s' and r['shot_id'] in wanted};line={r['shot_id']:r for r in load_csv(pw/tr['path']) if r['shot_id'] in wanted and int(r['time_index'])==999}
 if set(target)!=wanted or set(line)!=wanted:raise ValueError('EQUILIBRIUM_ROW_BINDING_MISMATCH')
 return [{'source_row_id':s,'physical_unit_id':'WASZ-BREW-'+s,'condition_id':'WASZ-COND-'+target[s]['reference_pressure_round__bar'].rstrip('0').rstrip('.'),'line_pressure_bar':line[s]['pressure__bar'],'flow_g_s':target[s]['mass_flow_rate__g_per_s']} for s in sorted(wanted)]
def partition(c,rows,fold):
 mem=[r for r in load_csv(cpath(c,'membership')) if r['outer_fold']==fold['outer_fold']];by={r['physical_unit_id']:r for r in rows};train=[by[m['physical_unit_id']] for m in mem if m['role']=='TRAIN'];test=[by[m['physical_unit_id']] for m in mem if m['role']=='EVALUATION']
 if set(x['condition_id'] for x in train)!=set(fold['training_groups'].split(';')) or {x['condition_id'] for x in test}!={fold['group_id']}:raise ValueError('FROZEN_MEMBERSHIP_DISAGREES')
 if {x['physical_unit_id'] for x in train}&{x['physical_unit_id'] for x in test}:raise ValueError('PHYSICAL_GROUP_LEAKAGE')
 return train,test
def execute(c,rows,cal):
 out=[]
 for fold in load_csv(cpath(c,'folds')):
  train,test=partition(c,rows,fold);means={g:sum(float(r['flow_g_s']) for r in train if r['condition_id']==g)/sum(r['condition_id']==g for r in train) for g in {r['condition_id'] for r in train}};scale=max(means.values())-min(means.values())
  if not math.isfinite(scale) or scale<=0:raise ValueError('TRAINING_SCALE_INVALID')
  for mid in c['model_ids']:
   failed='';roots=0
   try:
    if mid=='HYD_B0_TRAINING_MEAN':model=fit_condition_balanced_mean(train);pred=[model['mean']]*len(test)
    elif mid=='HYD_B1_PRESSURE_QUADRATIC':model=fit_condition_balanced_quadratic(train);pred=predict_quadratic(model,test)
    elif mid=='HYD_E1_LUMPED_DARCY':model=fit_machine_darcy(train,cal,(0,10));pred=predict_machine_darcy(model,test,cal)
    else:raise ValueError('UNFROZEN_MODEL')
   except ValueError as e:model={};pred=[];failed=str(e);roots=len(test)
   obs=[float(r['flow_g_s']) for r in test];phys=rmse(obs,pred) if pred else math.inf;out.append({'outer_fold':fold['outer_fold'],'model_id':mid,'training_conditions':fold['training_groups'],'evaluation_condition':fold['group_id'],'fit':model,'test':test,'pred':pred,'physical_loss':phys,'normalized_loss':phys/scale,'failed_root_count':roots,'failure_reason':failed})
 return out
def diagnostics(results):
 out={}
 for mid in sorted({r['model_id'] for r in results}):
  rr=[r for r in results if r['model_id']==mid];p=[sum(float(x['line_pressure_bar']) for x in r['test'])/len(r['test']) for r in rr];o=[sum(float(x['flow_g_s']) for x in r['test'])/len(r['test']) for r in rr];y=[sum(r['pred'])/len(r['pred']) for r in rr]
  def slope(ix,z):
   x=[p[i] for i in ix];v=[z[i] for i in ix];xm=sum(x)/len(x);vm=sum(v)/len(v);return sum((a-xm)*(b-vm) for a,b in zip(x,v))/sum((a-xm)**2 for a in x)
  low=[i for i,x in enumerate(p) if x<=5.25];high=[i for i,x in enumerate(p) if x>=8.5];out[mid]={'observed_low_slope':slope(low,o),'predicted_low_slope':slope(low,y),'observed_high_slope':slope(high,o),'predicted_high_slope':slope(high,y),'low_direction_ok':slope(low,o)*slope(low,y)>=0,'high_direction_ok':slope(high,o)*slope(high,y)>=0,'observed_peak_condition':rr[max(range(len(o)),key=o.__getitem__)]['evaluation_condition'],'predicted_peak_condition':rr[max(range(len(y)),key=y.__getitem__)]['evaluation_condition']}
 return out
def decide(results,diag):
 losses={m:sum(r['normalized_loss'] for r in results if r['model_id']==m)/11 for m in {r['model_id'] for r in results}};e=losses['HYD_E1_LUMPED_DARCY'];b=losses['HYD_B1_PRESSURE_QUADRATIC'];d=diag['HYD_E1_LUMPED_DARCY'];low=[r for r in results if sum(float(x['line_pressure_bar']) for x in r['test'])/len(r['test'])<=5.25];el=sum(r['normalized_loss'] for r in low if r['model_id']=='HYD_E1_LUMPED_DARCY')/sum(r['model_id']=='HYD_E1_LUMPED_DARCY' for r in low);bl=sum(r['normalized_loss'] for r in low if r['model_id']=='HYD_B1_PRESSURE_QUADRATIC')/sum(r['model_id']=='HYD_B1_PRESSURE_QUADRATIC' for r in low)
 if not d['low_direction_ok']:lane='REDUCED_DARCY_SYSTEMATICALLY_WRONG_ON_PRESSURE_RESPONSE'
 elif el<=bl and (e>b or not d['high_direction_ok']):lane='REDUCED_DARCY_LOW_PRESSURE_LIMIT_SUPPORTED_FULL_PRESSURE_DOMAIN_INSUFFICIENT'
 elif e<=b and d['high_direction_ok']:lane='REDUCED_DARCY_CONDITIONAL_UTILITY_ESTABLISHED_FULL_DOMAIN'
 else:lane='NO_STABLE_REDUCED_DARCY_ADVANTAGE_OVER_EMPIRICAL_BASELINE'
 amap={'REDUCED_DARCY_CONDITIONAL_UTILITY_ESTABLISHED_FULL_DOMAIN':'RETAIN_AS_CONDITIONAL_COMPONENT','REDUCED_DARCY_LOW_PRESSURE_LIMIT_SUPPORTED_FULL_PRESSURE_DOMAIN_INSUFFICIENT':'RETAIN_LOW_PRESSURE_DARCY_LIMIT_SIMPLIFY_OR_REPARAMETERIZE_FULL_HYDRAULICS','REDUCED_DARCY_SYSTEMATICALLY_WRONG_ON_PRESSURE_RESPONSE':'REJECT_REDUCED_FORM_FOR_FULL_PRESSURE_RESPONSE','NO_STABLE_REDUCED_DARCY_ADVANTAGE_OVER_EMPIRICAL_BASELINE':'NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE'};return losses,lane,amap[lane]
def write_results(out,results,c,mh,synthetic):
 diag=diagnostics(results);losses,lane,arch=decide(results,diag);fr=[];br=[]
 for r in results:
  fr.append({'outer_fold':r['outer_fold'],'model_id':r['model_id'],'training_conditions':r['training_conditions'],'evaluation_condition':r['evaluation_condition'],'fitted_parameters':json.dumps(r['fit'],sort_keys=True),'parameter_bound_status':r['fit'].get('bound_status','NA'),'training_condition_count':len(r['training_conditions'].split(';')),'training_brew_count':'FROZEN_MEMBERSHIP','evaluation_brew_count':len(r['test']),'fit_status':'PASS' if not r['failure_reason'] else 'FAIL','prediction_status':'SYNTHETIC' if synthetic else 'NEW_REAL_PREDICTION','physical_unit_loss_g_s':r['physical_loss'],'normalized_loss':r['normalized_loss'],'failed_root_count':r['failed_root_count'],'failure_reason':r['failure_reason']})
  for x,p in zip(r['test'],r['pred']):br.append({'outer_fold':r['outer_fold'],'model_id':r['model_id'],'physical_unit_id':x['physical_unit_id'],'condition_id':x['condition_id'],'line_pressure_bar':x['line_pressure_bar'],'observed_flow_g_s':x['flow_g_s'],'predicted_flow_g_s':p,'error_g_s':p-float(x['flow_g_s'])})
 write_csv(out/'FOLD_RESULTS.csv',list(fr[0]),fr);write_csv(out/'BREW_RESULTS.csv',list(br[0]),br);write_json(out/'PRESSURE_RESPONSE_DIAGNOSTICS.json',diag);rng=random.Random(R3_SEED);sq={}
 for x in br:sq.setdefault((x['condition_id'],x['model_id']),[]).append(float(x['error_g_s'])**2)
 conds=sorted({x[0] for x in sq});boots=[]
 for _ in range(2000):
  sample=[rng.choice(conds) for _ in conds];v={m:sum(math.sqrt(sum(rng.choice(sq[(g,m)]) for _ in sq[(g,m)])/len(sq[(g,m)])) for g in sample)/len(sample) for m in ['HYD_B1_PRESSURE_QUADRATIC','HYD_E1_LUMPED_DARCY']};boots.append(v['HYD_B1_PRESSURE_QUADRATIC']-v['HYD_E1_LUMPED_DARCY'])
 boots.sort();agg=[{'model_id':m,'normalized_loss':v,'paired_delta_b1_minus_e1':losses['HYD_B1_PRESSURE_QUADRATIC']-losses['HYD_E1_LUMPED_DARCY'] if m=='HYD_E1_LUMPED_DARCY' else '','ci_low':boots[49] if m=='HYD_E1_LUMPED_DARCY' else '','ci_high':boots[1949] if m=='HYD_E1_LUMPED_DARCY' else ''} for m,v in sorted(losses.items())];write_csv(out/'AGGREGATE_RESULTS.csv',list(agg[0]),agg);write_csv(out/'CONDITION_RESULTS.csv',['condition_id','model_id','normalized_loss'],[{'condition_id':r['evaluation_condition'],'model_id':r['model_id'],'normalized_loss':r['normalized_loss']} for r in results]);write_csv(out/'PARAMETER_STABILITY.csv',['outer_fold','model_id','parameters'],[{'outer_fold':r['outer_fold'],'model_id':r['model_id'],'parameters':json.dumps(r['fit'],sort_keys=True)} for r in results]);write_json(out/'IDENTIFIABILITY_RESULTS.json',{'E1':'one effective conductance only; full EWP quantities not identified'});write_json(out/'ARCHITECTURE_DECISIONS.json',{'lane_result':lane,'reduced_E1':arch,'current_full_E2':'NOT_ADJUDICATED'});write_json(out/'EXPERIMENT_NECESSITY_DECISION.json',{'derived_from_architecture':arch,'recommendation':'HYDRAULIC_LANE_DOES_NOT_ADJUDICATE_M01_CHEMISTRY','stage_f_authorized':False,'stage_d_authorized':False});write_csv(out/'MODEL_UTILITY_SCORECARD.csv',list(agg[0]),agg);write_csv(out/'LIMITATION_ATTRIBUTION.csv',['item','limitation'],[{'item':'current_full_E2','limitation':'NOT_ADJUDICATED'}]);(out/'RESULTS_SUMMARY.md').write_text(('# Synthetic result\n' if synthetic else '# SCI-MD-010 result\n')+lane+'\n');(out/'RESULT.md').write_text('# Result\n\n'+lane+'\n');state={'scoring_executed':not synthetic,'new_real_predictions_generated':not synthetic,'new_real_scores_generated':not synthetic,'prior_scores_materialized':False,'ewp_or_reduced_ewp_scored':not synthetic,'synthetic':synthetic};write_json(out/'EXECUTION_STATE.json',state);write_json(out/'RUN_RECEIPT.json',{'freeze_manifest_sha256':mh,**state});write_json(out/'summary.json',{'lane_result':lane,'architecture_decision':arch,**state});files=sorted(p for p in out.iterdir() if p.name!='RESULT_ARTIFACT_MANIFEST.json');write_json(out/'RESULT_ARTIFACT_MANIFEST.json',{'artifacts':[{'path':p.name,'sha256':sha256(p)} for p in files]})
def synthetic_rows():
 cal={'a':.017184292098914252,'b':.03670858658698296,'c':.2831597837775055};rows=[]
 for r in load_csv(ROOT/'docs/analysis/sci_md_010/ANALYSIS_ROW_INDEX.csv'):
  p=float(r['condition_id'].removeprefix('WASZ-COND-'));rows.append({'source_row_id':r['source_row_id'],'physical_unit_id':r['physical_unit_id'],'condition_id':r['condition_id'],'line_pressure_bar':str(p),'flow_g_s':str(solve_machine_darcy(p,.18,cal))})
 return rows
def main():
 global CONTRACT_PATH
 ap=argparse.ArgumentParser();ap.add_argument('--contract',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--review-receipt',required=True);ap.add_argument('--output',required=True);ap.add_argument('--preflight-only',action='store_true');ap.add_argument('--synthetic-test-mode',action='store_true',help=argparse.SUPPRESS);a=ap.parse_args();CONTRACT_PATH=Path(a.contract).resolve();c=load_json(CONTRACT_PATH);f=load_json(a.freeze);receipt=load_json(a.review_receipt);out=Path(a.output);mh,pw,reg=preflight(c,f,receipt,out,a.synthetic_test_mode)
 if a.preflight_only:return
 (out/'PREFLIGHT_RECEIPT.json').unlink();rows=synthetic_rows() if a.synthetic_test_mode else load_real(c,pw,reg);write_results(out,execute(c,rows,c['machine_calibration']),c,mh,a.synthetic_test_mode)
if __name__=='__main__':main()
