#!/usr/bin/env python3
"""Independent deterministic SCI-MD-011 R2 freeze/result reproduction validator."""
import argparse, csv, hashlib, json, math, os, re, sys, tempfile
from pathlib import Path
from sci_md_011_core import *
import sci_md_011_execute as ex
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/analysis/sci_md_011'
def verify_oracle():
 rec=load_json(D/'CLOSURE_ORACLE_RECEIPT.json');rows=load_csv(D/'CLOSURE_ORACLE_RESULTS.csv')
 if len(rows)!=21 or rec['row_count']!=21 or rec['results_sha256']!=sha256(D/'CLOSURE_ORACLE_RESULTS.csv'):raise ValueError('ORACLE_RECEIPT_INVALID')
 ma=mr=0.
 for r in rows:
  phi=float(r['phi']);x=float(r['x']);py_phi=fphi(x,phi);py_f0=f0(x)
  for prod,py,ae,re in ((float(r['production_fphi']),py_phi,float(r['fphi_absolute_error']),float(r['fphi_relative_error'])),(float(r['production_f0']),py_f0,float(r['f0_absolute_error']),float(r['f0_relative_error']))):
   cae=abs(prod-py);cre=cae/max(abs(prod),abs(py),1.0)
   if abs(cae-ae)>1e-18 or abs(cre-re)>1e-18:raise ValueError('ORACLE_ROW_RECOMPUTATION_FAILED')
   ma=max(ma,cae);mr=max(mr,cre)
 if ma!=rec['maximum_absolute_error'] or mr!=rec['maximum_relative_error'] or not rec['pass'] or ma>rec['absolute_tolerance'] or mr>rec['relative_tolerance']:raise ValueError('ORACLE_SUMMARY_RECOMPUTATION_FAILED')
def freeze():
 f=load_json(D/'PRE_SCORE_FREEZE.json')
 if f['task_id']!=TASK or f['revision']!='R2' or f['supersedes_freeze_commit']!='5944c597a3208a606a93b0f51e4394adf11488ec' or f['scoring_executed'] or f['phase_b_authorized'] or not f['review_required'] or tuple(f['selected_models'])!=MODELS or f['parameter_bounds']!=BOUNDS:raise ValueError('FREEZE_FLAGS')
 ex.verify_manifest();ex.verify_handoff();ex.verify_production();verify_oracle()
 if load_json(ROOT/'dependencies/puckworks.lock.json')['checkout_commit']!='fc61c4670ec7bf801e40bb391aab16048b8da26b':raise ValueError('LOCK')
 return len(load_json(D/'FREEZE_ARTIFACT_MANIFEST.json')['artifacts'])
def compare_value(a,b,path='root'):
 if isinstance(a,float) or isinstance(b,float):
  try:
   if not math.isclose(float(a),float(b),rel_tol=1e-11,abs_tol=1e-12):raise ValueError('RESULT_RECOMPUTATION_MISMATCH:'+path)
   return
  except (TypeError,ValueError):pass
 if type(a)!=type(b):raise ValueError('RESULT_RECOMPUTATION_TYPE:'+path)
 if isinstance(a,dict):
  if set(a)!=set(b):raise ValueError('RESULT_RECOMPUTATION_KEYS:'+path)
  for k in a:compare_value(a[k],b[k],path+'.'+k)
 elif isinstance(a,list):
  if len(a)!=len(b):raise ValueError('RESULT_RECOMPUTATION_LENGTH:'+path)
  for i,(x,y) in enumerate(zip(a,b)):compare_value(x,y,f'{path}[{i}]')
 elif a!=b:raise ValueError('RESULT_RECOMPUTATION_MISMATCH:'+path)
def compare_csv(a,b):
 x=load_csv(a);y=load_csv(b)
 if x!=y:raise ValueError('RESULT_CSV_RECOMPUTATION_MISMATCH:'+a.name)
def verify_result_manifest(result_dir,synthetic):
 if result_dir.is_symlink():raise ValueError('RESULT_DIRECTORY_SYMLINK')
 manifest=load_json(result_dir/'RESULT_ARTIFACT_MANIFEST.json')
 if not isinstance(manifest,dict) or set(manifest)!= {'task_id','artifacts'} or manifest['task_id']!=TASK or not isinstance(manifest['artifacts'],list):raise ValueError('RESULT_MANIFEST_SCHEMA')
 expected=set(ex.REQUIRED_RESULT_PAYLOAD_FILES+(ex.SYNTHETIC_RESULT_ADDITIONS if synthetic else ()))
 entries=manifest['artifacts'];paths=[]
 for a in entries:
  if not isinstance(a,dict) or set(a)!= {'path','sha256'} or type(a['path']) is not str or not re.fullmatch(r'[0-9a-f]{64}',a['sha256']):raise ValueError('RESULT_MANIFEST_ENTRY')
  p=Path(a['path'])
  if p.is_absolute() or '..' in p.parts or len(p.parts)!=1 or a['path']=='RESULT_ARTIFACT_MANIFEST.json':raise ValueError('RESULT_MANIFEST_PATH')
  q=result_dir/p
  if q.is_symlink() or not q.is_file() or q.resolve().parent!=result_dir.resolve():raise ValueError('RESULT_MANIFEST_TARGET')
  paths.append(a['path'])
 if len(paths)!=len(set(paths)) or set(paths)!=expected:raise ValueError('RESULT_MANIFEST_FILE_SET')
 actual={p.name for p in result_dir.iterdir()}
 if actual!=expected|{'RESULT_ARTIFACT_MANIFEST.json'}:raise ValueError('RESULT_DIRECTORY_FILE_SET')
 for a in entries:
  if sha256(result_dir/a['path'])!=a['sha256']:raise ValueError('RESULT_MANIFEST_HASH:'+a['path'])
 return manifest
def independent_derived(records):
 """Recalculate metrics/diagnostics/decisions without trusting result fields."""
 brew=[x for r in records for x in r['brew_rows']];diag={};aggregates=[]
 for model in MODELS:
  rr=[r for r in records if r['model_id']==model];valid=len(rr)==11 and all(r['execution_status']=='PASS' and r['brew_rows'] for r in rr)
  if not valid:
   diag[model]={'status':'NOT_COMPUTABLE','reason':'REQUIRED_FOLD_BLOCKED','structural_saturation_capability':model in CANDIDATES,'structural_turnover_capability':False if model in CANDIDATES else None};continue
  cm=[]
  for r in rr:
   z=r['brew_rows'];p=sum(float(x['line_pressure_bar']) for x in z)/len(z);o=sum(float(x['observed_flow_g_s']) for x in z)/len(z);y=sum(float(x['predicted_flow_g_s']) for x in z)/len(z);cm.append({'condition_id':r['evaluation_condition_id'],'line_pressure_bar':p,'observed_flow_g_s':o,'predicted_flow_g_s':y,'signed_bias_g_s':y-o})
  p=[x['line_pressure_bar'] for x in cm];o=[x['observed_flow_g_s'] for x in cm];y=[x['predicted_flow_g_s'] for x in cm];lo=[i for i,x in enumerate(p) if x<=5.25];hi=[i for i,x in enumerate(p) if x>=8.5];pl=slope([p[i] for i in lo],[y[i] for i in lo]);ph=slope([p[i] for i in hi],[y[i] for i in hi]);pairs=[(i,j) for i in range(11) for j in range(i+1,11) if o[i]!=o[j]]
  diag[model]={'status':'COMPLETE','condition_means':cm,'signed_bias_g_s':sum(x['signed_bias_g_s'] for x in cm)/11,'observed_low_slope':slope([p[i] for i in lo],[o[i] for i in lo]),'predicted_low_slope':pl,'observed_high_slope':slope([p[i] for i in hi],[o[i] for i in hi]),'predicted_high_slope':ph,'low_direction_ok':pl>0,'high_direction_ok':ph<=0,'slope_attenuation':pl-ph,'distance_high_slope_from_zero':abs(ph),'observed_peak_conditions':[cm[i]['condition_id'] for i,v in enumerate(o) if v==max(o)],'predicted_peak_conditions':[cm[i]['condition_id'] for i,v in enumerate(y) if v==max(y)],'spearman_average_ties':spearman(o,y),'ordering_concordance':sum((o[j]-o[i])*(y[j]-y[i])>0 for i,j in pairs)/len(pairs),'ordering_denominator':len(pairs),'structural_saturation_capability':model in CANDIDATES,'structural_turnover_capability':False if model in CANDIDATES else None}
 b1={r['outer_fold']:r for r in records if r['model_id']==B1 and r['execution_status']=='PASS'}
 for model in MODELS:
  rr=[r for r in records if r['model_id']==model];valid=[r for r in rr if r['normalized_loss'] is not None]
  if len(valid)!=11:aggregates.append({'model_id':model,'execution_status':'BLOCKED','normalized_loss':'','mean_rmse_g_s':'','fold_loss_min':'','fold_loss_max':'','signed_bias_g_s':'','low_pressure_loss':'','high_pressure_loss':'','condition_wins_vs_b1':''});continue
  nl=[r['normalized_loss'] for r in valid];low=[r for r in valid if sum(float(x['line_pressure_bar']) for x in r['brew_rows'])/len(r['brew_rows'])<=5.25];high=[r for r in valid if sum(float(x['line_pressure_bar']) for x in r['brew_rows'])/len(r['brew_rows'])>=8.5]
  aggregates.append({'model_id':model,'execution_status':'PASS','normalized_loss':sum(nl)/11,'mean_rmse_g_s':sum(r['rmse_g_s'] for r in valid)/11,'fold_loss_min':min(nl),'fold_loss_max':max(nl),'signed_bias_g_s':diag[model]['signed_bias_g_s'],'low_pressure_loss':sum(r['normalized_loss'] for r in low)/len(low),'high_pressure_loss':sum(r['normalized_loss'] for r in high)/len(high),'condition_wins_vs_b1':sum(r['normalized_loss']<b1[r['outer_fold']]['normalized_loss'] for r in valid) if model!=B1 else 0})
 losses={r['model_id']:r['normalized_loss'] for r in aggregates if r['execution_status']=='PASS'};sc={r['outer_fold']:r['training_scale_g_s'] for r in records if r['model_id']==B1};means={r['outer_fold']:sum(float(x['line_pressure_bar']) for x in r['brew_rows'])/len(r['brew_rows']) for r in records if r['model_id']==B1};lowfolds=sorted(f for f,p in means.items() if p<=5.25);comparisons={}
 for a,b,key in ((B1,P1,'B1_VS_P1'),(B1,E2C,'B1_VS_E2C'),(P1,E2C,'P1_VS_E2C')):
  if a not in losses or b not in losses:comparisons[key]={'models':[a,b],'sign_convention':f'LOSS_{a} - LOSS_{b}; positive favors {b}','status':'NOT_COMPUTABLE','reason':'REQUIRED_MODEL_BLOCKED','point_delta':None,'full_domain_interval':None,'low_pressure_interval':None};continue
  full=bootstrap(brew,sc,a,b);low=bootstrap(brew,sc,a,b,lowfolds);comparisons[key]={'models':[a,b],'sign_convention':f'LOSS_{a} - LOSS_{b}; positive favors {b}','status':'COMPLETE','point_delta':losses[a]-losses[b],'full_domain_interval':[full['ci_low'],full['ci_high']],'low_pressure_interval':[low['ci_low'],low['ci_high']],'quantile_convention':full['quantile_convention'],'bootstrap_count':BOOTSTRAPS,'seed':SEED}
 statuses={}
 for model,key in ((P1,'B1_VS_P1'),(E2C,'B1_VS_E2C')):
  blocked=any(r['model_id']==model and r['execution_status']!='PASS' for r in records);ci=None if comparisons[key]['status']!='COMPLETE' else comparisons[key]['full_domain_interval'];statuses[model]=candidate_status(ci or (0,0),diag[model] if diag[model]['status']=='COMPLETE' else {'low_direction_ok':False,'high_direction_ok':False},blocked)
 ci=None if comparisons['P1_VS_E2C']['status']!='COMPLETE' else comparisons['P1_VS_E2C']['full_domain_interval'];complexity=complexity_status(ci);disp,arch=overall(statuses,complexity)
 return brew,diag,aggregates,comparisons,{'disposition':disp,'architecture':arch,'candidate_status':statuses,'finite_vs_universal':complexity,'process_status':'COMPLETE','scientific_status':'BLOCKED' if 'BLOCKED' in statuses.values() else 'SCORED','current_full_ewp':'NOT_VALIDATED','physical_validation':'NOT_ESTABLISHED'},experiment_consequence(arch)
def result(result_dir):
 state=load_json(result_dir/'EXECUTION_STATE.json');synthetic=state.get('synthetic');
 if type(synthetic) is not bool:raise ValueError('RESULT_MODE_INVALID')
 verify_result_manifest(result_dir,synthetic);mh=sha256(D/'FREEZE_ARTIFACT_MANIFEST.json');review=ex.verify_receipt(result_dir/'PHASE_B_REVIEW_RECEIPT.json','synthetic' if synthetic else 'real',mh)
 if synthetic:
  scenario_record=load_json(result_dir/'SYNTHETIC_SCENARIO.json')
  if not isinstance(scenario_record,dict) or scenario_record!={'task_id':TASK,'revision':REVISION,'synthetic_scenario':state.get('synthetic_scenario'),'test_only':True}:raise ValueError('SYNTHETIC_SCENARIO_RECORD')
  scenario=state['synthetic_scenario']
  if scenario not in ex.SYNTHETIC_SCENARIOS:raise ValueError('SYNTHETIC_SCENARIO_INVALID')
  kind=scenario if scenario in ('poro','quadratic','turnover','blocked') else 'poro';rows=ex.synthetic_rows(kind);parts=ex.partitions(rows);base=ex.synthetic_baselines(parts);records=base+ex.execute_candidates(parts,failure_plan=ex.synthetic_failure_plan(scenario,parts))
 else:
  if 'synthetic_scenario' in state:raise ValueError('REAL_RESULT_HAS_SYNTHETIC_SCENARIO')
  pw=ex.resolve_puckworks();rows=ex.load_real_rows(pw);parts=ex.partitions(rows);records=ex.accepted_baselines(parts)+ex.execute_candidates(parts)
 recomputed_brew,recomputed_diag,recomputed_agg,recomputed_pairs,recomputed_decision,recomputed_experiment=independent_derived(records)
 compare_value(load_json(result_dir/'PRESSURE_RESPONSE_DIAGNOSTICS.json'),recomputed_diag,'PRESSURE_RESPONSE_DIAGNOSTICS.json')
 compare_value(load_json(result_dir/'PAIRWISE_COMPARISONS.json'),recomputed_pairs,'PAIRWISE_COMPARISONS.json')
 compare_value(load_json(result_dir/'ARCHITECTURE_DECISION.json'),recomputed_decision,'ARCHITECTURE_DECISION.json')
 compare_value(load_json(result_dir/'EXPERIMENT_CONSEQUENCE.json'),recomputed_experiment,'EXPERIMENT_CONSEQUENCE.json')
 with tempfile.TemporaryDirectory() as td:
  expected=Path(td);ex.write_result(expected,records,mh,review,synthetic,rows if synthetic else None,state.get('synthetic_scenario'))
  for n in sorted(p.name for p in expected.iterdir()):
   if (result_dir/n).read_bytes()!=(expected/n).read_bytes():raise ValueError('RESULT_BYTE_RECOMPUTATION_MISMATCH:'+n)
 s=load_json(result_dir/'summary.json')
 if s['current_full_ewp_validated'] or s['stage_f_authorized'] or s['stage_d_authorized'] or s['physical_validation']!='NOT_ESTABLISHED':raise ValueError('CLAIM_BOUNDARY')
 return len(load_csv(result_dir/'BREW_RESULTS.csv'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['freeze','result'],required=True);p.add_argument('--result-dir',type=Path);a=p.parse_args();n=freeze()
 if a.phase=='result':
  if not a.result_dir:raise ValueError('--result-dir required')
  n+=result(a.result_dir)
 print(json.dumps({'task_id':TASK,'revision':REVISION,'phase':a.phase,'validated_items':n,'status':'PASS'}))
if __name__=='__main__':main()
