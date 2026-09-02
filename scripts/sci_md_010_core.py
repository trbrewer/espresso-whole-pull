#!/usr/bin/env python3
"""Shared, task-specific fold/model/scoring machinery for SCI-MD-010."""
from __future__ import annotations
import csv,hashlib,json,math,os,subprocess
from pathlib import Path

REVIEW_DISPOSITION="SCI_MD_010_PRE_SCORE_FREEZE_SINGLE_INDEPENDENT_REVIEW_PASS_READY_FOR_EXECUTION"
CLAIM_CEILING="RETROSPECTIVE_SOURCE_CONDITIONED_COMPONENT_MODEL_UTILITY_AND_ARCHITECTURE_AUDIT_ONLY"

def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical_sha(value): return hashlib.sha256((json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
def git(root,*args): return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def load_json(path): return json.loads(Path(path).read_text())
def load_csv(path):
 with Path(path).open(newline='') as f:return list(csv.DictReader(f))
def write_json(path,value): Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def write_csv(path,fields,rows):
 with Path(path).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)

def resolve_puckworks():
 raw=os.environ.get('SCI_MD_010_PUCKWORKS_ROOT')
 if not raw: raise ValueError('SCI_MD_010_PUCKWORKS_ROOT_REQUIRED')
 root=Path(raw).resolve()
 if not (root/'.git').exists() or not (root/'puckworks/data/MANIFEST.csv').is_file(): raise ValueError('INVALID_PUCKWORKS_ROOT')
 return root

def stable_folds(rows,group_field): return sorted({r[group_field] for r in rows if r.get('included','true').lower()=='true'})
def validate_no_leakage(rows,membership):
 units={}
 for r in rows:
  units.setdefault(r['nested_unit_id'],r['physical_unit_id'])
  if units[r['nested_unit_id']]!=r['physical_unit_id']: raise ValueError('NESTED_UNIT_CROSSES_PHYSICAL_UNITS')
 for fold in {r['outer_fold'] for r in membership}:
  train={r['physical_unit_id'] for r in membership if r['outer_fold']==fold and r['role']=='TRAIN'}
  test={r['physical_unit_id'] for r in membership if r['outer_fold']==fold and r['role']=='EVALUATION'}
  if train&test: raise ValueError('PHYSICAL_GROUP_LEAKAGE')
 return True

def fit_mean(train):
 if not train: raise ValueError('EMPTY_TRAINING')
 return {'mean':sum(train)/len(train)}
def predict_mean(model,x): return [model['mean'] for _ in x]
def fit_linear(train_x,train_y):
 if len(train_x)!=len(train_y) or not train_x: raise ValueError('BAD_TRAINING')
 xm=sum(train_x)/len(train_x);ym=sum(train_y)/len(train_y);den=sum((x-xm)**2 for x in train_x)
 b=0.0 if den==0 else sum((x-xm)*(y-ym) for x,y in zip(train_x,train_y))/den
 return {'intercept':ym-b*xm,'slope':b}
def predict_linear(model,x): return [model['intercept']+model['slope']*v for v in x]
def hyd_reduced(params,pressure): return [params['conductance']*max(p-params.get('threshold',0.0),0.0) for p in pressure]
def fraction_shape(params,coordinate):
 vals=[max(math.exp(-params['rate']*x),0.0) for x in coordinate];s=sum(vals)
 return [v/s for v in vals] if s>0 else [0.0 for v in vals]
MODEL_CALLABLES={'fit_mean':fit_mean,'predict_mean':predict_mean,'fit_linear':fit_linear,'predict_linear':predict_linear,'hyd_reduced':hyd_reduced,'fraction_shape':fraction_shape}

def rmse(y,p): return math.sqrt(sum((a-b)**2 for a,b in zip(y,p))/len(y)) if y else math.inf
def total_variation(y,p):
 sy,sp=sum(y),sum(p)
 if sy<=0 or sp<=0:return math.inf
 return .5*sum(abs(a/sy-b/sp) for a,b in zip(y,p))
def ordering_ok(x,y,p):
 pairs=[(i,j) for i in range(len(x)) for j in range(i+1,len(x)) if x[i]!=x[j] and y[i]!=y[j]]
 return all((x[j]-x[i])*(y[j]-y[i])*(p[j]-p[i])>=0 for i,j in pairs)
def sensitivity_rank(jac,tol=1e-10):
 # Gram determinant is sufficient for the frozen two-parameter checks.
 if not jac:return 0
 if len(jac[0])==1:return int(any(abs(r[0])>tol for r in jac))
 a=sum(r[0]*r[0] for r in jac);b=sum(r[0]*r[1] for r in jac);c=sum(r[1]*r[1] for r in jac)
 return 2 if a*c-b*b>tol*max(1.0,a*c) else (1 if max(a,c)>tol else 0)
def classify_identifiability(jac): return 'WEAKLY_IDENTIFIED_OR_PRACTICALLY_NONIDENTIFIABLE' if sensitivity_rank(jac)<len(jac[0]) else 'LOCALLY_IDENTIFIABLE_SYNTHETIC_CHECK'
def lane_decision(candidate,baseline,trend=True,tol=1e-12,full=None):
 if not trend:return 'CURRENT_FORM_SYSTEMATICALLY_WRONG_ON_OBSERVABLE'
 if full is not None and abs(candidate-full)<=tol:return 'FULL_AND_REDUCED_MODELS_INDISTINGUISHABLE_PREFER_REDUCED'
 return 'RETROSPECTIVE_GROUPED_PREDICTIVE_ADVANTAGE_ESTABLISHED' if candidate+tol<baseline else 'NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE'
def enforce_privilege(record):
 if record.get('derived_from_target')=='true' and record.get('claim_class') not in {'POST_FIT_RECONSTRUCTION','CONDITIONAL_PREDICTION_GIVEN_MEASURED_CONTEXT'}: raise ValueError('TARGET_DERIVED_INFORMATION_PRIVILEGE')
 if record.get('supplied_to_ewp')!=record.get('supplied_to_b1') and record.get('claim_class')=='RETROSPECTIVE_GROUPED_PREDICTION': raise ValueError('UNEQUAL_INFORMATION_PRIVILEGE')

def verify_receipt(receipt,freeze,manifest_hash,repo,allow_synthetic=False):
 required={'task_id','review_disposition','reviewed_freeze_commit','reviewed_freeze_tree','freeze_manifest_sha256','reviewer_identity','review_record','reviewed_at_utc','material_findings','phase_b_authorized'}
 if set(receipt)<required: raise ValueError('REVIEW_RECEIPT_FIELDS_MISSING')
 if receipt['task_id']!='SCI-MD-010' or receipt['review_disposition']!=REVIEW_DISPOSITION: raise ValueError('REVIEW_DISPOSITION_INVALID')
 if not receipt['reviewer_identity'] or receipt['material_findings'] or receipt['phase_b_authorized'] is not True: raise ValueError('REVIEW_NOT_AUTHORIZING')
 if receipt['freeze_manifest_sha256']!=manifest_hash: raise ValueError('REVIEW_MANIFEST_MISMATCH')
 if allow_synthetic and receipt['reviewed_freeze_commit']=='SYNTHETIC_HEAD' and receipt['reviewed_freeze_tree']=='SYNTHETIC_TREE': return True
 if git(repo,'rev-parse','HEAD')!=receipt['reviewed_freeze_commit'] or git(repo,'rev-parse','HEAD^{tree}')!=receipt['reviewed_freeze_tree']: raise ValueError('REVIEW_GIT_IDENTITY_MISMATCH')
 return True

def validate_artifacts(repo,register,puckworks):
 for a in register['artifacts']:
  root=puckworks if a['repository']=='puckworks' else repo
  path=root/a['path']
  if not path.is_file() or sha256(path)!=a['sha256'] or path.stat().st_size!=a['size_bytes']: raise ValueError('INPUT_ARTIFACT_MISMATCH:'+a['artifact_id'])
  if a['format']=='csv':
   with path.open(newline='') as f: fields=(csv.DictReader(f).fieldnames or [])
   missing=set(a['fields_consumed'])-set(fields)
   if missing: raise ValueError('INPUT_FIELDS_MISSING:'+a['artifact_id'])
 return True

def synthetic_run(output):
 output=Path(output)
 if output.exists() and any(output.iterdir()): raise ValueError('OUTPUT_IDENTITY_ALREADY_USED')
 output.mkdir(parents=True,exist_ok=True)
 x=[1.,2.,3.,4.];y=[2.,4.,6.,8.]
 folds=[]
 for i in range(4):
  tx=[v for j,v in enumerate(x) if j!=i];ty=[v for j,v in enumerate(y) if j!=i]
  m=fit_linear(tx,ty); pred=predict_linear(m,[x[i]])[0]
  folds.append({'fold':i,'target':y[i],'prediction':pred,'loss':abs(pred-y[i]),'fit':m})
 write_csv(output/'FOLD_RESULTS.csv',['fold','target','prediction','loss','fit'],[{**r,'fit':json.dumps(r['fit'],sort_keys=True)} for r in folds])
 result={'synthetic':True,'primary_loss':sum(r['loss'] for r in folds)/4,'disposition':lane_decision(0.0,1.0),'scoring_executed':True}
 write_csv(output/'AGGREGATE_RESULTS.csv',['synthetic','primary_loss','disposition','scoring_executed'],[result]);write_json(output/'EXECUTION_STATE.json',{'scoring_executed':True,'synthetic':True});write_json(output/'RUN_RECEIPT.json',{'task_id':'SCI-MD-010','synthetic':True,'completion_status':'COMPLETE'})
 write_csv(output/'MODEL_UTILITY_SCORECARD.csv',['subsystem','architecture_decision'],[{'subsystem':'synthetic','architecture_decision':'RETAIN_AS_MECHANISTIC_CORE'}])
 write_json(output/'ARCHITECTURE_DECISIONS.json',{'synthetic':True,'decision':'RETAIN_AS_MECHANISTIC_CORE'})
 write_json(output/'EXPERIMENT_NECESSITY_DECISION.json',{'synthetic':True,'stage_f_authorized':False,'stage_d_authorized':False})
 write_json(output/'summary.json',{'synthetic':True,'scoring_executed':True})
 files=sorted(p for p in output.iterdir() if p.name!='RESULT_ARTIFACT_MANIFEST.json')
 write_json(output/'RESULT_ARTIFACT_MANIFEST.json',{'artifacts':[{'path':p.name,'sha256':sha256(p)} for p in files]})
 return result
