#!/usr/bin/env python3
"""Shared, task-specific fold/model/scoring machinery for SCI-MD-010."""
from __future__ import annotations
import csv,hashlib,json,math,os,random,subprocess
from pathlib import Path

REVIEW_DISPOSITION="SCI_MD_010_PRE_SCORE_FREEZE_SINGLE_INDEPENDENT_REVIEW_PASS_READY_FOR_EXECUTION"
CLAIM_CEILING="RETROSPECTIVE_SOURCE_CONDITIONED_CONDITIONAL_HYDRAULIC_COMPONENT_UTILITY_ONLY"

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

R3_SEED=20260902
def brewer_drop(q,cal): return cal['a']*q*q+cal['b']*q+cal['c']
def solve_machine_darcy(line_pressure,conductance,cal,lower=0.0,upper=20.0,tol=1e-10,max_iter=200):
 """Solve q=C max(p_line-dp_machine(q),0), using predicted q only."""
 if conductance<0: raise ValueError('NEGATIVE_CONDUCTANCE')
 def f(q): return q-conductance*max(line_pressure-brewer_drop(q,cal),0.0)
 lo,hi=lower,upper;flo,fhi=f(lo),f(hi)
 if flo>0 or fhi<0: raise ValueError('NO_PHYSICAL_ROOT')
 for _ in range(max_iter):
  mid=(lo+hi)/2;fm=f(mid)
  if abs(fm)<=tol:return mid
  if fm>0:hi=mid
  else:lo=mid
 raise ValueError('ROOT_NOT_CONVERGED')
def condition_balanced_rows(rows):
 by={}
 for r in rows:by.setdefault(r['condition_id'],[]).append(r)
 return [(r,1.0/len(by)/len(v)) for v in by.values() for r in v]
def _solve_linear(a,b):
 n=len(b);m=[list(map(float,a[i]))+[float(b[i])] for i in range(n)]
 for i in range(n):
  k=max(range(i,n),key=lambda j:abs(m[j][i]))
  if abs(m[k][i])<1e-14:raise ValueError('SINGULAR_FIT')
  m[i],m[k]=m[k],m[i];z=m[i][i];m[i]=[x/z for x in m[i]]
  for j in range(n):
   if j!=i:
    z=m[j][i];m[j]=[x-z*y for x,y in zip(m[j],m[i])]
 return [m[i][-1] for i in range(n)]
def fit_condition_balanced_mean(rows):return {'mean':sum(w*float(r['flow_g_s']) for r,w in condition_balanced_rows(rows))}
def fit_condition_balanced_quadratic(rows):
 wr=condition_balanced_rows(rows);s=[[0.0]*3 for _ in range(3)];t=[0.0]*3
 for r,w in wr:
  x=float(r['line_pressure_bar']);y=float(r['flow_g_s']);v=[1,x,x*x]
  for i in range(3):
   t[i]+=w*v[i]*y
   for j in range(3):s[i][j]+=w*v[i]*v[j]
 a,b,c=_solve_linear(s,t);return {'intercept':a,'linear':b,'quadratic':c}
def predict_quadratic(model,rows):return [max(0.0,model['intercept']+model['linear']*float(r['line_pressure_bar'])+model['quadratic']*float(r['line_pressure_bar'])**2) for r in rows]
def fit_machine_darcy(rows,cal,bound=(0.0,10.0)):
 wr=condition_balanced_rows(rows)
 def loss(c):
  try:return sum(w*(solve_machine_darcy(float(r['line_pressure_bar']),c,cal)-float(r['flow_g_s']))**2 for r,w in wr)
  except ValueError:return math.inf
 lo,hi=bound;gr=(math.sqrt(5)-1)/2;x1=hi-gr*(hi-lo);x2=lo+gr*(hi-lo);f1,f2=loss(x1),loss(x2)
 for _ in range(120):
  if f1<=f2:hi,x2,f2=x2,x1,f1;x1=hi-gr*(hi-lo);f1=loss(x1)
  else:lo,x1,f1=x1,x2,f2;x2=lo+gr*(hi-lo);f2=loss(x2)
 c=max(0.0,(lo+hi)/2);return {'conductance_g_s_bar':c,'bound_status':'LOWER_BOUND' if c<=1e-9 else 'INTERIOR'}
def predict_machine_darcy(model,rows,cal):return [solve_machine_darcy(float(r['line_pressure_bar']),model['conductance_g_s_bar'],cal) for r in rows]
MODEL_CALLABLES.update({'fit_condition_balanced_mean':fit_condition_balanced_mean,'fit_condition_balanced_quadratic':fit_condition_balanced_quadratic,'predict_quadratic':predict_quadratic,'fit_machine_darcy':fit_machine_darcy,'predict_machine_darcy':predict_machine_darcy,'solve_machine_darcy':solve_machine_darcy})

def percentile_sorted(values,p):
 """Nearest-rank percentile with zero-based ceil(p*n)-1 indexing."""
 if not values:raise ValueError('EMPTY_PERCENTILE')
 return sorted(values)[max(0,min(len(values)-1,math.ceil(p*len(values))-1))]
def paired_bootstrap(brew_rows,fold_scales,subset=None,count=2000,seed=R3_SEED):
 """Paired condition-then-brew bootstrap in normalized fold-loss space."""
 by={}
 for r in brew_rows:
  if r['model_id'] in {'HYD_B1_PRESSURE_QUADRATIC','HYD_E1_LUMPED_DARCY'}:by.setdefault((r['outer_fold'],r['model_id']),{})[r['physical_unit_id']]=float(r['squared_error_g_s2'])
 folds=sorted(subset or {k[0] for k in by});rng=random.Random(seed);draws=[]
 for _ in range(count):
  sampled=[rng.choice(folds) for _ in folds];loss={'HYD_B1_PRESSURE_QUADRATIC':0.0,'HYD_E1_LUMPED_DARCY':0.0}
  for f in sampled:
   shared=sorted(set(by[(f,'HYD_B1_PRESSURE_QUADRATIC')])&set(by[(f,'HYD_E1_LUMPED_DARCY')]))
   picked=[rng.choice(shared) for _ in shared]
   for m in loss:loss[m]+=math.sqrt(sum(by[(f,m)][u] for u in picked)/len(picked))/fold_scales[f]
  draws.append((loss['HYD_B1_PRESSURE_QUADRATIC']-loss['HYD_E1_LUMPED_DARCY'])/len(folds))
 return {'draws':draws,'low':percentile_sorted(draws,.025),'high':percentile_sorted(draws,.975),'quantile_convention':'nearest-rank ceil(p*n)-1'}
def average_ranks(values):
 order=sorted(range(len(values)),key=lambda i:values[i]);r=[0.0]*len(values);i=0
 while i<len(order):
  j=i
  while j+1<len(order) and values[order[j+1]]==values[order[i]]:j+=1
  rank=(i+j+2)/2
  for k in range(i,j+1):r[order[k]]=rank
  i=j+1
 return r
def spearman(values_a,values_b):
 a=average_ranks(values_a);b=average_ranks(values_b);am=sum(a)/len(a);bm=sum(b)/len(b);den=math.sqrt(sum((x-am)**2 for x in a)*sum((y-bm)**2 for y in b))
 return 0.0 if den==0 else sum((x-am)*(y-bm) for x,y in zip(a,b))/den
def map_r4_result(required_failed,low_ok,high_ok,full_ci,low_ci):
 if required_failed or full_ci is None or low_ci is None:return 'HYDRAULIC_UTILITY_TEST_BLOCKED'
 if not low_ok:return 'REDUCED_DARCY_SYSTEMATICALLY_WRONG_ON_PRESSURE_RESPONSE'
 if low_ci[0]>0 and (not high_ok or full_ci[0]<=0):return 'REDUCED_DARCY_LOW_PRESSURE_LIMIT_SUPPORTED_FULL_PRESSURE_DOMAIN_INSUFFICIENT'
 if high_ok and full_ci[0]>0:return 'REDUCED_DARCY_CONDITIONAL_UTILITY_ESTABLISHED_FULL_DOMAIN'
 if high_ok and full_ci[0]<=0<=full_ci[1]:return 'REDUCED_DARCY_INDISTINGUISHABLE_FROM_EMPIRICAL_BASELINE_PREFER_SIMPLER_CONDITIONAL_FORM'
 return 'NO_STABLE_REDUCED_DARCY_ADVANTAGE_OVER_EMPIRICAL_BASELINE'
ARCHITECTURE_MAP={'HYDRAULIC_UTILITY_TEST_BLOCKED':'NOT_ADJUDICATED','REDUCED_DARCY_SYSTEMATICALLY_WRONG_ON_PRESSURE_RESPONSE':'REJECT_REDUCED_FORM_FOR_FULL_PRESSURE_RESPONSE','REDUCED_DARCY_LOW_PRESSURE_LIMIT_SUPPORTED_FULL_PRESSURE_DOMAIN_INSUFFICIENT':'RETAIN_LOW_PRESSURE_DARCY_LIMIT_SIMPLIFY_OR_REPARAMETERIZE_FULL_HYDRAULICS','REDUCED_DARCY_CONDITIONAL_UTILITY_ESTABLISHED_FULL_DOMAIN':'RETAIN_AS_CONDITIONAL_COMPONENT','REDUCED_DARCY_INDISTINGUISHABLE_FROM_EMPIRICAL_BASELINE_PREFER_SIMPLER_CONDITIONAL_FORM':'PREFER_REDUCED_CONDITIONAL_FORM_BY_PARSIMONY_FULL_EWP_NOT_ADJUDICATED','NO_STABLE_REDUCED_DARCY_ADVANTAGE_OVER_EMPIRICAL_BASELINE':'NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE'}
def experiment_from_architecture(arch):
 if arch=='NOT_ADJUDICATED':return 'HYDRAULIC_EXECUTION_BLOCKER_MUST_BE_RESOLVED_M01_NOT_ADJUDICATED'
 if arch in {'NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE','PREFER_REDUCED_CONDITIONAL_FORM_BY_PARSIMONY_FULL_EWP_NOT_ADJUDICATED'}:return 'SIMPLIFY_BEFORE_HYDRAULIC_SPECIFIC_EXPERIMENT_M01_NOT_ADJUDICATED'
 return 'CONDITIONAL_HYDRAULIC_RELATION_RETAINED_M01_NOT_ADJUDICATED'

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
