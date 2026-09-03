#!/usr/bin/env python3
"""SCI-MD-011 R2: metadata preflight, synthetic execution, or reviewed real execution."""
import argparse, json, math, os, re
from datetime import datetime, timezone
from pathlib import Path
from sci_md_011_core import *
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'docs/analysis/sci_md_011'; S10=ROOT/'docs/analysis/sci_md_010'
PW_COMMIT='2058d0e947ee9eb92c52d64f6165b810f1fb4732'; PW_TREE='a6ffb312473b15be43c1571a893b19873ea47c5a'
PASS='SCI_MD_011_PRE_SCORE_FREEZE_SINGLE_INDEPENDENT_REVIEW_PASS_READY_FOR_EXECUTION'
REQUIRED_RESULT_PAYLOAD_FILES=('PHASE_B_REVIEW_RECEIPT.json','EXECUTION_STATE.json','RUN_RECEIPT.json','BREW_RESULTS.csv','FOLD_RESULTS.csv','CONDITION_RESULTS.csv','AGGREGATE_RESULTS.csv','PAIRWISE_COMPARISONS.json','PARAMETER_STABILITY.csv','IDENTIFIABILITY_RESULTS.json','PRESSURE_RESPONSE_DIAGNOSTICS.json','UNCERTAINTY_RESULTS.json','MODEL_UTILITY_SCORECARD.csv','ARCHITECTURE_DECISION.json','EXPERIMENT_CONSEQUENCE.json','RESULTS_SUMMARY.md','RESULT.md','summary.json')
SYNTHETIC_RESULT_ADDITIONS=('SYNTHETIC_INPUT_ROWS.csv','SYNTHETIC_SCENARIO.json')
RESULT_FILES=REQUIRED_RESULT_PAYLOAD_FILES+('RESULT_ARTIFACT_MANIFEST.json',)
REAL_RECEIPT_FIELDS=('task_id','disposition','freeze_commit','freeze_tree','freeze_manifest_sha256','reviewer_identity','review_mode','durable_review_url','reviewed_at','material_findings','phase_b_authorized')
REVIEW_MODES=('FORMAL_APPROVAL','EXACT_HEAD_COMMENT_FALLBACK_AUTHENTICATED_ACCOUNT_IS_PR_AUTHOR')
SYNTHETIC_SCENARIOS=('poro','quadratic','turnover','blocked','one-P1-fold-blocked','one-E2C-fold-blocked','both-candidates-different-folds-blocked')

def verify_manifest():
 m=load_json(D/'FREEZE_ARTIFACT_MANIFEST.json');hs=[]
 for a in m['artifacts']:
  got=sha256(ROOT/a['path'])
  if got!=a['sha256']:raise ValueError('FREEZE_ARTIFACT_CHANGED:'+a['path'])
  hs.append(got)
 if hashlib.sha256(''.join(hs).encode()).hexdigest()!=m['aggregate_content_sha256']:raise ValueError('FREEZE_AGGREGATE_HASH_MISMATCH')
 return sha256(D/'FREEZE_ARTIFACT_MANIFEST.json')
def verify_handoff():
 h=load_json(D/'SCI_MD_010_HANDOFF.json')
 for a in h['artifacts']:
  if sha256(ROOT/a['path'])!=a['sha256']:raise ValueError('SCI_MD_010_HANDOFF_CHANGED:'+a['path'])
 return h
def verify_production():
 a=load_json(D/'AUTHORITY_AND_HANDOFF.json');p=a['production_sources']
 for x in p:
  if sha256(ROOT/x['path'])!=x['sha256']:raise ValueError('PRODUCTION_SOURCE_CHANGED:'+x['path'])
 lock=load_json(ROOT/'dependencies/puckworks.lock.json')
 if lock['checkout_commit']!='fc61c4670ec7bf801e40bb391aab16048b8da26b':raise ValueError('PRODUCTION_PUCKWORKS_LOCK_CHANGED')
 eq=load_json(D/'EWP_CLOSURE_EQUIVALENCE.json')
 for s in eq['production_symbols']:
  got=hashlib.sha256(symbol_text(ROOT/s['path'],s['symbol']).encode()).hexdigest()
  if got!=s['sha256']:raise ValueError('PRODUCTION_SYMBOL_CHANGED:'+s['symbol'])
def resolve_puckworks():
 raw=os.environ.get('SCI_MD_011_PUCKWORKS_ROOT','')
 if not raw:raise ValueError('SCI_MD_011_PUCKWORKS_ROOT_REQUIRED')
 p=Path(raw).resolve();a=load_json(D/'AUTHORITY_AND_HANDOFF.json')['puckworks_analysis']
 if git(p,'rev-parse','HEAD')!=PW_COMMIT or git(p,'rev-parse','HEAD^{tree}')!=PW_TREE:raise ValueError('PUCKWORKS_COMMIT_OR_TREE_MISMATCH')
 if git(p,'status','--short'):raise ValueError('PUCKWORKS_WORKTREE_DIRTY')
 for x in a['sources']:
  if sha256(p/x['path'])!=x['sha256']:raise ValueError('PUCKWORKS_SOURCE_CHANGED:'+x['path'])
 return p
def verify_contract(contract,freeze,require_puckworks=True):
 mh=verify_manifest();verify_handoff();verify_production();pw=resolve_puckworks() if require_puckworks else None
 if contract['task_id']!=TASK or freeze['task_id']!=TASK or freeze.get('revision')!=REVISION:raise ValueError('TASK_OR_REVISION_MISMATCH')
 if tuple(contract['models'])!=MODELS or tuple(freeze['selected_models'])!=MODELS:raise ValueError('MODEL_SET_CHANGED')
 if contract['metrics']['seed']!=SEED or contract['metrics']['bootstrap_count']!=BOOTSTRAPS:raise ValueError('SEED_OR_BOOTSTRAP_CHANGED')
 if contract['fit']['bounds']!=BOUNDS or contract['gates']['low']!='predicted slope > 0' or contract['gates']['high']!='predicted slope <= 0':raise ValueError('BOUND_OR_GATE_CHANGED')
 return mh,pw
def verify_receipt(path,mode,mh):
 r=load_json(path)
 if not isinstance(r,dict):raise ValueError('REVIEW_RECEIPT_OBJECT_REQUIRED')
 if mode in ('synthetic','preflight'):
  if r.get('task_id')!=TASK or r.get('synthetic') is not True or r.get('phase_b_authorized') is not False:raise ValueError('PURPOSE_LIMITED_RECEIPT_REQUIRED')
  return r
 if set(r)!=set(REAL_RECEIPT_FIELDS):raise ValueError('REVIEW_RECEIPT_SCHEMA')
 string_fields=REAL_RECEIPT_FIELDS[:9]
 if any(type(r[k]) is not str for k in string_fields):raise ValueError('REVIEW_RECEIPT_STRING_TYPES')
 if r['task_id']!=TASK or r['disposition']!=PASS or type(r['phase_b_authorized']) is not bool or r['phase_b_authorized'] is not True:raise ValueError('PHASE_B_UNAUTHORIZED')
 if type(r['material_findings']) is not list or r['material_findings']!=[]:raise ValueError('MATERIAL_FINDINGS_INVALID')
 identity=r['reviewer_identity']
 if not identity or identity!=identity.strip() or identity.lower() in {'reviewer','independent-reviewer','unknown','none','test'}:raise ValueError('REVIEWER_IDENTITY_INVALID')
 review_mode=r['review_mode']
 if review_mode not in REVIEW_MODES or review_mode!=review_mode.strip():raise ValueError('REVIEW_MODE_INVALID')
 reviewed_at=r['reviewed_at']
 if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z',reviewed_at):raise ValueError('REVIEW_TIME_INVALID')
 try: parsed=datetime.fromisoformat(reviewed_at[:-1]+'+00:00')
 except ValueError as e:raise ValueError('REVIEW_TIME_INVALID') from e
 if parsed.tzinfo!=timezone.utc:raise ValueError('REVIEW_TIME_NOT_UTC')
 if not re.fullmatch(r'[0-9a-f]{40}',r['freeze_commit']) or not re.fullmatch(r'[0-9a-f]{40}',r['freeze_tree']) or not re.fullmatch(r'[0-9a-f]{64}',r['freeze_manifest_sha256']):raise ValueError('REVIEW_IDENTIFIER_FORMAT')
 if r['freeze_commit']!=git(ROOT,'rev-parse','HEAD') or r['freeze_tree']!=git(ROOT,'rev-parse','HEAD^{tree}') or r['freeze_manifest_sha256']!=mh:raise ValueError('REVIEW_EXACT_FREEZE_MISMATCH')
 comment=re.fullmatch(r'https://github\.com/trbrewer/espresso-whole-pull/pull/142#issuecomment-([1-9]\d*)',r['durable_review_url'])
 formal=re.fullmatch(r'https://github\.com/trbrewer/espresso-whole-pull/pull/142(?:#pullrequestreview-([1-9]\d*)|/reviews/([1-9]\d*))',r['durable_review_url'])
 if (review_mode==REVIEW_MODES[1] and not comment) or (review_mode==REVIEW_MODES[0] and not formal):raise ValueError('REVIEW_MODE_URL_MISMATCH')
 return r

def input_artifacts():
 reg=load_json(S10/'INPUT_ARTIFACT_REGISTER.json')['artifacts'];return {a['artifact_id']:a for a in reg}
def load_real_rows(pw,source_reader=load_csv):
 reg=input_artifacts();eq=reg['WASZ_EQUILIBRIUM'];tr=reg['WASZ_LINE_PRESSURE'];idx={r['source_row_id']:r for r in load_csv(S10/'ANALYSIS_ROW_INDEX.csv') if r['included']=='true'}
 target={r['shot_id']:r for r in source_reader(pw/eq['path']) if r['window']=='endpoint_100s' and r['shot_id'] in idx};line={r['shot_id']:r for r in source_reader(pw/tr['path']) if r['shot_id'] in idx and int(r['time_index'])==999}
 if len(idx)!=56 or set(target)!=set(idx) or set(line)!=set(idx):raise ValueError('REAL_ROW_BINDING_MISMATCH')
 rows=[]
 for sid,i in idx.items():
  rows.append({'source_row_id':sid,'physical_unit_id':i['physical_unit_id'],'condition_id':i['condition_id'],'line_pressure_bar':float(line[sid]['pressure__bar']),'flow_g_s':float(target[sid]['mass_flow_rate__g_per_s'])})
 validate_row_identities(rows);validate_against_accepted(rows);return rows
def validate_row_identities(rows):
 idx=load_csv(S10/'ANALYSIS_ROW_INDEX.csv');expected={(r['source_row_id'],r['physical_unit_id'],r['condition_id']) for r in idx if r['included']=='true'};got={(r['source_row_id'],r['physical_unit_id'],r['condition_id']) for r in rows}
 if len(rows)!=56 or len({r['physical_unit_id'] for r in rows})!=56 or len({r['condition_id'] for r in rows})!=11 or got!=expected:raise ValueError('REAL_BINDING_IDENTITY_MISMATCH')
def validate_against_accepted(rows,tol=1e-12):
 by={r['physical_unit_id']:r for r in rows};accepted=load_csv(S10/'BREW_RESULTS.csv')
 for model in (B0,B1):
  rr=[r for r in accepted if r['model_id']==model]
  if len(rr)!=56:raise ValueError('BASELINE_ROW_COUNT')
  for r in rr:
   x=by[r['physical_unit_id']]
   if r['condition_id']!=x['condition_id'] or abs(float(r['line_pressure_bar'])-x['line_pressure_bar'])>tol or abs(float(r['observed_flow_g_s'])-x['flow_g_s'])>tol:raise ValueError('ACCEPTED_BASELINE_OBSERVATION_MISMATCH')
def partitions(rows,membership_rows=None,fold_rows=None):
 mem=membership_rows or load_csv(S10/'FOLD_MEMBERSHIP.csv');folds=fold_rows or load_csv(S10/'FOLD_ASSIGNMENTS.csv');by={r['physical_unit_id']:r for r in rows};out=[]
 if len(mem)!=56*11:raise ValueError('MEMBERSHIP_ROW_COUNT')
 for fold in folds:
  mm=[m for m in mem if m['outer_fold']==fold['outer_fold']];train=[by[m['physical_unit_id']] for m in mm if m['role']=='TRAIN'];test=[by[m['physical_unit_id']] for m in mm if m['role']=='EVALUATION']
  if len(mm)!=56 or len(train)+len(test)!=56 or {x['physical_unit_id'] for x in train}&{x['physical_unit_id'] for x in test}:raise ValueError('FROZEN_MEMBERSHIP_INVALID')
  if {x['condition_id'] for x in test}!={fold['group_id']} or set(x['condition_id'] for x in train)!=set(fold['training_groups'].split(';')):raise ValueError('FROZEN_MEMBERSHIP_DISAGREES')
  out.append((fold,train,test))
 return out
def fit_quad(rows):
 wr=balanced(rows);A=[[0.]*3 for _ in range(3)];b=[0.]*3
 for r,w in wr:
  x=float(r['line_pressure_bar']);v=[1,x,x*x];y=float(r['flow_g_s'])
  for i in range(3):
   b[i]+=w*v[i]*y
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
 return {'intercept':b[0],'linear':b[1],'quadratic':b[2]}
def training_scale(train):
 means=[]
 for c in sorted({r['condition_id'] for r in train}):
  z=[float(r['flow_g_s']) for r in train if r['condition_id']==c];means.append(sum(z)/len(z))
 s=max(means)-min(means)
 if not math.isfinite(s) or s<=0:raise ValueError('INVALID_TRAINING_SCALE')
 return s
def accepted_baselines(parts,tol=1e-12):
 brew=load_csv(S10/'BREW_RESULTS.csv');folds=load_csv(S10/'FOLD_RESULTS.csv');out=[]
 for fold,train,test in parts:
  scale=training_scale(train)
  for model in (B0,B1):
   fr=next(r for r in folds if r['outer_fold']==fold['outer_fold'] and r['model_id']==model);rows=[r for r in brew if r['outer_fold']==fold['outer_fold'] and r['model_id']==model]
   if abs(scale-float(fr['training_scale_g_s']))>tol:raise ValueError('ACCEPTED_TRAINING_SCALE_MISMATCH')
   if model==B1:
    p=json.loads(fr['fitted_parameters'])
    for r in rows:
     q=max(0.,p['intercept']+p['linear']*float(r['line_pressure_bar'])+p['quadratic']*float(r['line_pressure_bar'])**2)
     if abs(q-float(r['predicted_flow_g_s']))>tol:raise ValueError('B1_INTEGRITY_RECOMPUTATION_FAILED')
   out.append(fold_record(fold,train,test,model,fr['fitted_parameters'],scale,rows=rows,accepted=True))
 return out
def fold_record(fold,train,test,model,pars,scale,rows=None,accepted=False,fitrec=None):
 if rows is None:
  rows=[]
  for x in test:
   if model==B0:q=float(pars['mean']);pb='';rec={}
   elif model==B1:q=max(0.,pars['intercept']+pars['linear']*x['line_pressure_bar']+pars['quadratic']*x['line_pressure_bar']**2);pb='';rec={}
   else:q,pb,rec=predict(x['line_pressure_bar'],pars['Qc_g_s'],pars['Pc_bar'],model)
   e=q-x['flow_g_s'];rows.append({'outer_fold':fold['outer_fold'],'model_id':model,'source_row_id':x['source_row_id'],'physical_unit_id':x['physical_unit_id'],'condition_id':x['condition_id'],'line_pressure_bar':x['line_pressure_bar'],'observed_flow_g_s':x['flow_g_s'],'predicted_flow_g_s':q,'predicted_basket_pressure_bar':pb,'coupled_equation_residual_bar':rec.get('coupled_equation_residual_bar',''),'error_g_s':e,'squared_error_g_s2':e*e,'training_scale_g_s':scale})
 else:
  rows=[dict(r,source_row_id=next(x['source_row_id'] for x in test if x['physical_unit_id']==r['physical_unit_id']),predicted_basket_pressure_bar='',coupled_equation_residual_bar='') for r in rows]
 rmse=math.sqrt(sum(float(r['squared_error_g_s2']) for r in rows)/len(rows))
 base={'outer_fold':fold['outer_fold'],'evaluation_condition_id':fold['group_id'],'model_id':model,'training_condition_ids':fold['training_groups'],'training_physical_unit_ids':';'.join(x['physical_unit_id'] for x in train),'evaluation_physical_unit_ids':';'.join(x['physical_unit_id'] for x in test),'training_scale_g_s':scale,'execution_status':'PASS','failure_class':'','failure_reason':'','optimizer_status':'ACCEPTED_REUSE' if accepted else ('CLOSED_FORM' if model in (B0,B1) else fitrec['optimizer_status']),'prediction_status':'PASS','root_failure_count':0,'domain_failure_count':0,'nonfinite_count':0,'fitted_parameters':pars,'rmse_g_s':rmse,'normalized_loss':rmse/scale,'identifiability':'NOT_APPLICABLE' if model in (B0,B1) else fitrec['identifiability'],'fit_receipt':fitrec or {},'brew_rows':rows}
 return base
def blocked_fold(fold,train,test,model,scale,fitrec,reason=None,failure_class=None):
 return {'outer_fold':fold['outer_fold'],'evaluation_condition_id':fold['group_id'],'model_id':model,'training_condition_ids':fold['training_groups'],'training_physical_unit_ids':';'.join(x['physical_unit_id'] for x in train),'evaluation_physical_unit_ids':';'.join(x['physical_unit_id'] for x in test),'training_scale_g_s':scale,'execution_status':'BLOCKED','failure_class':failure_class or fitrec.get('failure_class','EXECUTION_FAILURE'),'failure_reason':reason or fitrec.get('failure_reason','UNKNOWN'),'optimizer_status':fitrec.get('optimizer_status','FAIL'),'prediction_status':'FAIL','root_failure_count':fitrec.get('root_failure_count',0),'domain_failure_count':fitrec.get('domain_failure_count',0),'nonfinite_count':fitrec.get('nonfinite_count',0),'fitted_parameters':fitrec.get('fitted_parameters'),'rmse_g_s':None,'normalized_loss':None,'identifiability':'EXECUTION_BLOCKED','fit_receipt':fitrec,'brew_rows':[]}
def forced_block_receipt(reason='SYNTHETIC_FORCED_BLOCK'):
 return {'execution_status':'BLOCKED','failure_class':'FIT_FAILURE','failure_reason':reason,'optimizer_status':'FAIL','prediction_status':'NOT_ATTEMPTED','fitted_parameters':None,'objective':None,'root_failure_count':0,'domain_failure_count':0,'nonfinite_count':25,'identifiability':'EXECUTION_BLOCKED','start_receipts':[],'optimizer_objective_evaluations':0,'identifiability_objective_evaluations':0,'total_objective_evaluations':0}
def synthetic_failure_plan(scenario,parts):
 if scenario not in SYNTHETIC_SCENARIOS:raise ValueError('UNKNOWN_SYNTHETIC_SCENARIO')
 folds=[x[0]['outer_fold'] for x in parts]
 if scenario=='blocked':return {(f,m):'SYNTHETIC_ALL_CANDIDATE_FOLDS_BLOCKED' for f in folds for m in CANDIDATES}
 if scenario=='one-P1-fold-blocked':return {(folds[0],P1):'SYNTHETIC_ONE_P1_FOLD_BLOCKED'}
 if scenario=='one-E2C-fold-blocked':return {(folds[0],E2C):'SYNTHETIC_ONE_E2C_FOLD_BLOCKED'}
 if scenario=='both-candidates-different-folds-blocked':return {(folds[0],P1):'SYNTHETIC_P1_FOLD_BLOCKED',(folds[1],E2C):'SYNTHETIC_E2C_DIFFERENT_FOLD_BLOCKED'}
 return {}
def execute_candidates(parts,fit_fn=fit,failure_plan=None):
 out=[]
 for fold,train,test in parts:
  try:scale=training_scale(train)
  except ValueError as e:
   for m in CANDIDATES:out.append(blocked_fold(fold,train,test,m,None,{},str(e),'TRAINING_SCALE_FAILURE'))
   continue
  for m in CANDIDATES:
   reason=(failure_plan or {}).get((fold['outer_fold'],m));rec=forced_block_receipt(reason) if reason else fit_fn(train,m)
   if rec['execution_status']!='PASS':out.append(blocked_fold(fold,train,test,m,scale,rec));continue
   try:out.append(fold_record(fold,train,test,m,rec['fitted_parameters'],scale,fitrec=rec))
   except ValueError as e:
    rec=dict(rec);rec['root_failure_count']=1;out.append(blocked_fold(fold,train,test,m,scale,rec,str(e),'ROOT_OR_DOMAIN_FAILURE'))
 return out
def synthetic_rows(kind='poro'):
 idx=load_csv(S10/'ANALYSIS_ROW_INDEX.csv');pressure={c:float(c.removeprefix('WASZ-COND-')) for c in {r['condition_id'] for r in idx}};rows=[]
 for n,r in enumerate(idx):
  p=pressure[r['condition_id']]
  if kind=='poro':y=predict(p,2.0,15.0,P1)[0]+((n%3)-1)*.002
  elif kind=='turnover':y=max(.01,1.8-.025*(p-7.)**2)+((n%3)-1)*.002
  elif kind=='quadratic':y=max(.01,-.15+.45*p-.025*p*p)+((n%3)-1)*.002
  elif kind=='blocked':y=.1*p+((n%3)-1)*.002
  else:y=.15*p+.01*p*p+((n%3)-1)*.002
  rows.append({'source_row_id':r['source_row_id'],'physical_unit_id':r['physical_unit_id'],'condition_id':r['condition_id'],'line_pressure_bar':p,'flow_g_s':y})
 return rows
def synthetic_baselines(parts):
 out=[]
 for fold,train,test in parts:
  scale=training_scale(train);mean=sum(w*r['flow_g_s'] for r,w in balanced(train));out.append(fold_record(fold,train,test,B0,{'mean':mean},scale))
  p=fit_quad(train);out.append(fold_record(fold,train,test,B1,p,scale))
 return out

def diagnostics(records):
 out={}
 for m in MODELS:
  rr=[r for r in records if r['model_id']==m]
  if len(rr)!=11 or any(r['execution_status']!='PASS' for r in rr):out[m]={'status':'NOT_COMPUTABLE','reason':'REQUIRED_FOLD_BLOCKED','structural_saturation_capability':m in CANDIDATES,'structural_turnover_capability':False if m in CANDIDATES else None};continue
  cm=[]
  for r in rr:
   z=r['brew_rows'];cm.append({'condition_id':r['evaluation_condition_id'],'line_pressure_bar':sum(float(x['line_pressure_bar']) for x in z)/len(z),'observed_flow_g_s':sum(float(x['observed_flow_g_s']) for x in z)/len(z),'predicted_flow_g_s':sum(float(x['predicted_flow_g_s']) for x in z)/len(z),'signed_bias_g_s':sum(float(x['error_g_s']) for x in z)/len(z)})
  p=[x['line_pressure_bar'] for x in cm];o=[x['observed_flow_g_s'] for x in cm];y=[x['predicted_flow_g_s'] for x in cm];lo=[i for i,x in enumerate(p) if x<=5.25];hi=[i for i,x in enumerate(p) if x>=8.5];ol=slope([p[i] for i in lo],[o[i] for i in lo]);pl=slope([p[i] for i in lo],[y[i] for i in lo]);oh=slope([p[i] for i in hi],[o[i] for i in hi]);ph=slope([p[i] for i in hi],[y[i] for i in hi]);pairs=[(i,j) for i in range(11) for j in range(i+1,11) if o[i]!=o[j]]
  out[m]={'status':'COMPLETE','condition_means':cm,'signed_bias_g_s':sum(x['signed_bias_g_s'] for x in cm)/11,'observed_low_slope':ol,'predicted_low_slope':pl,'observed_high_slope':oh,'predicted_high_slope':ph,'low_direction_ok':pl>0,'high_direction_ok':ph<=0,'slope_attenuation':pl-ph,'distance_high_slope_from_zero':abs(ph),'observed_peak_conditions':[cm[i]['condition_id'] for i,v in enumerate(o) if v==max(o)],'predicted_peak_conditions':[cm[i]['condition_id'] for i,v in enumerate(y) if v==max(y)],'spearman_average_ties':spearman(o,y),'ordering_concordance':sum((o[j]-o[i])*(y[j]-y[i])>0 for i,j in pairs)/len(pairs),'ordering_denominator':len(pairs),'structural_saturation_capability':m in CANDIDATES,'structural_turnover_capability':False if m in CANDIDATES else None}
 return out
def aggregate(records,diag):
 out=[];b1={r['outer_fold']:r for r in records if r['model_id']==B1 and r['execution_status']=='PASS'}
 for m in MODELS:
  rr=[r for r in records if r['model_id']==m];valid=[r for r in rr if r['normalized_loss'] is not None]
  if len(valid)!=11:out.append({'model_id':m,'execution_status':'BLOCKED','normalized_loss':'','mean_rmse_g_s':'','fold_loss_min':'','fold_loss_max':'','signed_bias_g_s':'','low_pressure_loss':'','high_pressure_loss':'','condition_wins_vs_b1':''});continue
  lows=[r for r in valid if sum(float(x['line_pressure_bar']) for x in r['brew_rows'])/len(r['brew_rows'])<=5.25];highs=[r for r in valid if sum(float(x['line_pressure_bar']) for x in r['brew_rows'])/len(r['brew_rows'])>=8.5];loss=[r['normalized_loss'] for r in valid]
  out.append({'model_id':m,'execution_status':'PASS','normalized_loss':sum(loss)/11,'mean_rmse_g_s':sum(r['rmse_g_s'] for r in valid)/11,'fold_loss_min':min(loss),'fold_loss_max':max(loss),'signed_bias_g_s':diag[m]['signed_bias_g_s'],'low_pressure_loss':sum(r['normalized_loss'] for r in lows)/len(lows),'high_pressure_loss':sum(r['normalized_loss'] for r in highs)/len(highs),'condition_wins_vs_b1':sum(r['normalized_loss']<b1[r['outer_fold']]['normalized_loss'] for r in valid) if m!=B1 else 0})
 return out
def comparisons(records,brew,agg,diag):
 losses={r['model_id']:r['normalized_loss'] for r in agg if r['execution_status']=='PASS'};sc={r['outer_fold']:r['training_scale_g_s'] for r in records if r['model_id']==B1};means={r['outer_fold']:sum(float(x['line_pressure_bar']) for x in r['brew_rows'])/len(r['brew_rows']) for r in records if r['model_id']==B1};low=sorted(f for f,p in means.items() if p<=5.25);out={}
 for a,b,key in ((B1,P1,'B1_VS_P1'),(B1,E2C,'B1_VS_E2C'),(P1,E2C,'P1_VS_E2C')):
  blocked=a not in losses or b not in losses
  if blocked:out[key]={'models':[a,b],'sign_convention':f'LOSS_{a} - LOSS_{b}; positive favors {b}','status':'NOT_COMPUTABLE','reason':'REQUIRED_MODEL_BLOCKED','point_delta':None,'full_domain_interval':None,'low_pressure_interval':None};continue
  full=bootstrap(brew,sc,a,b);lb=bootstrap(brew,sc,a,b,low);out[key]={'models':[a,b],'sign_convention':f'LOSS_{a} - LOSS_{b}; positive favors {b}','status':'COMPLETE','point_delta':losses[a]-losses[b],'full_domain_interval':[full['ci_low'],full['ci_high']],'low_pressure_interval':[lb['ci_low'],lb['ci_high']],'quantile_convention':full['quantile_convention'],'bootstrap_count':BOOTSTRAPS,'seed':SEED}
 return out
def decisions(records,pairs,diag):
 statuses={}
 for m,key in ((P1,'B1_VS_P1'),(E2C,'B1_VS_E2C')):
  blocked=any(r['model_id']==m and r['execution_status']!='PASS' for r in records);ci=None if pairs[key]['status']!='COMPLETE' else pairs[key]['full_domain_interval'];statuses[m]=candidate_status(ci or (0,0),diag[m] if diag[m]['status']=='COMPLETE' else {'low_direction_ok':False,'high_direction_ok':False},blocked)
 ci=None if pairs['P1_VS_E2C']['status']!='COMPLETE' else pairs['P1_VS_E2C']['full_domain_interval'];complexity=complexity_status(ci);disp,arch=overall(statuses,complexity);return statuses,complexity,disp,arch
def write_result(out,records,mh,review,synthetic,input_rows=None,synthetic_scenario=None):
 out.mkdir(parents=True,exist_ok=True);brew=[x for r in records for x in r['brew_rows']];diag=diagnostics(records);agg=aggregate(records,diag);pairs=comparisons(records,brew,agg,diag);statuses,complexity,disp,arch=decisions(records,pairs,diag);blocked=any(x=='BLOCKED' for x in statuses.values());scientific='BLOCKED' if blocked else 'SCORED'
 ff=[]
 for r in records:
  ff.append({k:(json.dumps(json_safe(r[k]),sort_keys=True,allow_nan=False) if k in ('fitted_parameters','fit_receipt') else '' if r[k] is None else r[k]) for k in ('outer_fold','evaluation_condition_id','model_id','training_condition_ids','training_physical_unit_ids','evaluation_physical_unit_ids','training_scale_g_s','execution_status','failure_class','failure_reason','optimizer_status','prediction_status','root_failure_count','domain_failure_count','nonfinite_count','fitted_parameters','rmse_g_s','normalized_loss','identifiability','fit_receipt')})
 bf=('outer_fold','model_id','source_row_id','physical_unit_id','condition_id','line_pressure_bar','observed_flow_g_s','predicted_flow_g_s','predicted_basket_pressure_bar','coupled_equation_residual_bar','error_g_s','squared_error_g_s2','training_scale_g_s');write_csv(out/'BREW_RESULTS.csv',bf,brew);write_csv(out/'FOLD_RESULTS.csv',list(ff[0]),ff)
 cond=[{'condition_id':x['condition_id'],'model_id':m,'line_pressure_bar':x['line_pressure_bar'],'observed_flow_g_s':x['observed_flow_g_s'],'predicted_flow_g_s':x['predicted_flow_g_s'],'signed_bias_g_s':x['signed_bias_g_s']} for m,d in diag.items() if d['status']=='COMPLETE' for x in d['condition_means']];write_csv(out/'CONDITION_RESULTS.csv',['condition_id','model_id','line_pressure_bar','observed_flow_g_s','predicted_flow_g_s','signed_bias_g_s'],cond);write_csv(out/'AGGREGATE_RESULTS.csv',list(agg[0]),agg);write_json(out/'PAIRWISE_COMPARISONS.json',pairs);write_json(out/'UNCERTAINTY_RESULTS.json',{'bootstrap_count':BOOTSTRAPS,'seed':SEED,'bootstrap_refit':False,'unit':'condition_then_paired_brew','comparisons':pairs});write_json(out/'PRESSURE_RESPONSE_DIAGNOSTICS.json',diag)
 ps=[{'outer_fold':r['outer_fold'],'model_id':r['model_id'],'execution_status':r['execution_status'],'Qc_g_s':'' if not r['fitted_parameters'] else r['fitted_parameters'].get('Qc_g_s',''),'Pc_bar':'' if not r['fitted_parameters'] else r['fitted_parameters'].get('Pc_bar',''),'bound_proximity':r['fit_receipt'].get('bound_proximity',''),'identifiability':r['identifiability']} for r in records if r['model_id'] in CANDIDATES];write_csv(out/'PARAMETER_STABILITY.csv',list(ps[0]),ps);write_json(out/'IDENTIFIABILITY_RESULTS.json',{'scope':'effective predictive Qc/Pc only; no constituent physical parameters identified','folds':{r['outer_fold']+'|'+r['model_id']:{'classification':r['identifiability'],'diagnostics':r['fit_receipt'].get('identifiability_diagnostics',{}),'bound_proximity':r['fit_receipt'].get('bound_proximity')} for r in records if r['model_id'] in CANDIDATES}});write_csv(out/'MODEL_UTILITY_SCORECARD.csv',list(agg[0]),agg)
 decision={'disposition':disp,'architecture':arch,'candidate_status':statuses,'finite_vs_universal':complexity,'process_status':'COMPLETE','scientific_status':scientific,'current_full_ewp':'NOT_VALIDATED','physical_validation':'NOT_ESTABLISHED'};exp=experiment_consequence(arch);write_json(out/'ARCHITECTURE_DECISION.json',decision);write_json(out/'EXPERIMENT_CONSEQUENCE.json',exp);write_json(out/'PHASE_B_REVIEW_RECEIPT.json',review)
 candidate_records=[r for r in records if r['model_id'] in CANDIDATES];passed=[r for r in candidate_records if r['execution_status']=='PASS'];real_fit_started=not synthetic and any(r['fit_receipt'].get('optimizer_objective_evaluations',0)>0 for r in candidate_records);real_complete=not synthetic and len(passed)==len(candidate_records)
 state={'process_status':'COMPLETE','scientific_status':scientific,'synthetic':synthetic,'scoring_executed':not synthetic,'real_candidate_fits_generated':real_fit_started,'real_candidate_predictions_generated':real_complete,'real_candidate_scores_generated':real_complete,'current_full_ewp_validated':False,'physical_validation':'NOT_ESTABLISHED','stage_f_authorized':False,'stage_d_authorized':False,'m01_adjudicated':False}
 if synthetic:state['synthetic_scenario']=synthetic_scenario
 write_json(out/'EXECUTION_STATE.json',state);run={'task_id':TASK,'revision':REVISION,'execution_mode':'synthetic' if synthetic else 'real','freeze_commit':git(ROOT,'rev-parse','HEAD'),'freeze_tree':git(ROOT,'rev-parse','HEAD^{tree}'),'freeze_manifest_sha256':mh,'synthetic_scenario':synthetic_scenario if synthetic else None,'single_unchanged_scientific_configuration':True,**state};write_json(out/'RUN_RECEIPT.json',run);summary={'disposition':disp,'architecture':arch,'candidate_status':statuses,'finite_vs_universal':complexity,'current_full_ewp_validated':False,'stage_f_authorized':False,'stage_d_authorized':False,'m01_adjudicated':False,'physical_validation':'NOT_ESTABLISHED','synthetic':synthetic};write_json(out/'summary.json',summary)
 lines=['# SCI-MD-011 '+('synthetic ' if synthetic else '')+'result','',f'`{disp}`','',f'Architecture: `{arch}`. Scientific status: `{scientific}`.','', 'Authority: SCI-MD-010 frozen 56-brew, 11-condition observation interface; Puckworks analysis commit '+PW_COMMIT+'. The source 60-brew full-data calibration is context only.','', 'Models: immutable B0/B1 baselines, universal P1, and fixed-Phi E2C. Candidate fits estimate effective positive Qc/Pc only. The production-equivalent closure uses the SCI-MD-010 quadratic adapter, not the production machine boundary.','', 'Aggregate results:']+[f"- {r['model_id']}: {r['normalized_loss'] if r['normalized_loss']!='' else 'NOT_COMPUTABLE'}" for r in agg]+['','Pairwise comparisons:']+[f"- {k}: {v['status']} delta={v['point_delta']} interval={v['full_domain_interval']}" for k,v in pairs.items()]+['','Every fold, failure, diagnostic, parameter, and identifiability receipt is retained in the machine-readable package. P1/E2C are monotone saturating forms and do not contain turnover physics.','',f"Experiment consequence: `{exp['action']}`.",'','Current full EWP: NOT_VALIDATED. Physical validation: NOT_ESTABLISHED. Stage F/D: NOT_AUTHORIZED. M01: NOT_ADJUDICATED.'];text='\n'.join(lines)+'\n';(out/'RESULTS_SUMMARY.md').write_text(text);(out/'RESULT.md').write_text(text)
 if synthetic and input_rows is not None:
  write_csv(out/'SYNTHETIC_INPUT_ROWS.csv',['source_row_id','physical_unit_id','condition_id','line_pressure_bar','flow_g_s'],input_rows);write_json(out/'SYNTHETIC_SCENARIO.json',{'task_id':TASK,'revision':REVISION,'synthetic_scenario':synthetic_scenario,'test_only':True})
 files=sorted(p for p in out.iterdir() if p.name!='RESULT_ARTIFACT_MANIFEST.json');write_json(out/'RESULT_ARTIFACT_MANIFEST.json',{'task_id':TASK,'artifacts':[{'path':p.name,'sha256':sha256(p)} for p in files]})
def real_binding_metadata(pw):
 idx=load_csv(S10/'ANALYSIS_ROW_INDEX.csv');folds=load_csv(S10/'FOLD_ASSIGNMENTS.csv');mem=load_csv(S10/'FOLD_MEMBERSHIP.csv');validate_row_identities([{'source_row_id':r['source_row_id'],'physical_unit_id':r['physical_unit_id'],'condition_id':r['condition_id']} for r in idx]);partitions([{'source_row_id':r['source_row_id'],'physical_unit_id':r['physical_unit_id'],'condition_id':r['condition_id']} for r in idx],mem,folds);accepted=load_csv(S10/'BREW_RESULTS.csv');b0=len([r for r in accepted if r['model_id']==B0])==56;b1=len([r for r in accepted if r['model_id']==B1])==56;oracle=load_json(D/'CLOSURE_ORACLE_RECEIPT.json')['pass']
 return {'joined_rows':56,'distinct_physical_brews':56,'pressure_conditions':11,'outer_folds':11,'alias_duplication':0,'candidate_real_fits':0,'candidate_real_predictions':0,'candidate_real_scores':0,'b0_handoff_valid':b0,'b1_handoff_valid':b1,'production_oracle_valid':oracle,'puckworks_authority_valid':True,'phase_b_ready_after_exact_review':True}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--contract',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--review-receipt',required=True);ap.add_argument('--output',required=True);ap.add_argument('--synthetic-test-mode',action='store_true');ap.add_argument('--real-binding-preflight-only',action='store_true');ap.add_argument('--synthetic-outcome',choices=SYNTHETIC_SCENARIOS,default=None);a=ap.parse_args();out=Path(a.output)
 if a.synthetic_test_mode and a.real_binding_preflight_only:raise ValueError('MUTUALLY_EXCLUSIVE_EXECUTION_MODES')
 if a.synthetic_outcome is not None and not a.synthetic_test_mode:raise ValueError('SYNTHETIC_SCENARIO_REQUIRES_SYNTHETIC_MODE')
 if out.exists() and any(out.iterdir()):raise ValueError('DUPLICATE_RESULT_GUARD')
 c=load_json(a.contract);f=load_json(a.freeze);mode='preflight' if a.real_binding_preflight_only else 'synthetic' if a.synthetic_test_mode else 'real';mh,pw=verify_contract(c,f,mode!='synthetic');r=verify_receipt(a.review_receipt,mode,mh)
 if a.real_binding_preflight_only:out.mkdir(parents=True);write_json(out/'REAL_BINDING_PREFLIGHT.json',real_binding_metadata(pw));return
 if a.synthetic_test_mode:
  scenario=a.synthetic_outcome or 'poro';kind=scenario if scenario in ('poro','quadratic','turnover','blocked') else 'poro';rows=synthetic_rows(kind);parts=partitions(rows);base=synthetic_baselines(parts);rec=base+execute_candidates(parts,failure_plan=synthetic_failure_plan(scenario,parts));write_result(out,rec,mh,r,True,rows,scenario);return
 rows=load_real_rows(pw);parts=partitions(rows);records=accepted_baselines(parts)+execute_candidates(parts);write_result(out,records,mh,r,False)
if __name__=='__main__':main()
