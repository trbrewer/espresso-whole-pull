#!/usr/bin/env python3
"""Deterministic numerical and decision core for SCI-MD-011 R1."""
from __future__ import annotations
import csv, hashlib, json, math, random, subprocess
from functools import lru_cache
from pathlib import Path

TASK="SCI-MD-011"; REVISION="R1"; SEED=20260902; BOOTSTRAPS=2000
MODELS=("HYD_B0_TRAINING_MEAN","HYD_B1_PRESSURE_QUADRATIC","HYD_P1_POROELASTIC_UNIVERSAL_LIMIT","HYD_E2C_EWP_FINITE_PHI_POROELASTIC_COMPONENT")
B0,B1,P1,E2C=MODELS; CANDIDATES=(P1,E2C); PHI=2.257390325360356/18.5
CAL={"a":0.017184292098914252,"b":0.03670858658698296,"c":0.2831597837775055}
DOMAIN_EPS=1e-10; PRESSURE_TOL=1e-9; COUPLED_RESIDUAL_TOL=2e-9; MAX_ROOT_ITER=100
BOUNDS={"Qc_g_s":[0.01,20.0],"Pc_bar":[1.0,100.0]}
OPT={"lattice_points_per_axis":5,"max_iterations_per_start":32,"max_evaluations":4000,"step_reduction":0.5,"stopping_log_step":1e-6,"objective_comparison_tolerance":1e-14,"tie_break":"objective tolerance then lexicographic log(Qc),log(Pc)","bound_hit_log_distance":1e-5}
IDENT={"hessian_step":1e-3,"profile_log_offsets":[0.05,0.1,0.25],"adequate_condition_max":1e5,"weak_condition_max":1e9,"minimum_relative_profile_increase":1e-5,"fold_log_cv_weak":0.5}

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical_hash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def json_safe(v):
 if isinstance(v,float) and not math.isfinite(v):return None
 if isinstance(v,dict):return {k:json_safe(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [json_safe(x) for x in v]
 return v
def load_json(p): return json.loads(Path(p).read_text())
def load_csv(p):
 with Path(p).open(newline='') as f:return list(csv.DictReader(f))
def write_json(p,v): Path(p).write_text(json.dumps(json_safe(v),indent=2,sort_keys=True,allow_nan=False)+'\n')
def write_csv(p,fields,rows):
 with Path(p).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n',extrasaction='ignore');w.writeheader();w.writerows(rows)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def symbol_text(path,symbol):
 text=Path(path).read_text();start=text.index(symbol);line=text.rfind('\n',0,start)+1;brace=text.index('{',start);depth=0
 for i in range(brace,len(text)):
  if text[i]=='{':depth+=1
  elif text[i]=='}':
   depth-=1
   if depth==0:return text[line:i+1]
 raise ValueError('SYMBOL_BLOCK_NOT_FOUND:'+symbol)

def integral(x,phi):
 if not(math.isfinite(x) and math.isfinite(phi) and 0<=x<=1 and 0<phi<1):raise ValueError('DOMAIN')
 total=0.;pp=1.;xp=x
 for n in range(4096):
  term=pp*(xp/(n+1)-3*xp*x/(n+2)+3*xp*x*x/(n+3)-xp*x*x*x/(n+4));total+=term
  if n>8 and abs(term)<=2e-16*max(abs(total),1e-300):break
  pp*=phi;xp*=x
 return total
def f0(x):
 if not math.isfinite(x) or not 0<=x<=1:raise ValueError('DOMAIN')
 return x*(4-6*x+4*x*x-x*x*x)
def _integral_fast(x,p):return (2*p**3*x**3+3*p*p*x*x*(1-3*p)+6*p*x*(3*p*p-3*p+1)+6*(1-p)**3*math.log1p(-p*x))/(6*p**4)
@lru_cache(maxsize=16)
def _norm(phi):return _integral_fast(1.,phi)
def fphi(x,phi=PHI):
 if not(math.isfinite(x) and 0<=x<=1 and 0<phi<1):raise ValueError('DOMAIN')
 return _integral_fast(x,phi)/_norm(phi)
def brewer_drop(q,cal=CAL):return cal['a']*q*q+cal['b']*q+cal['c']
def predict(line,qc,pc,model,cal=CAL):
 if model not in CANDIDATES:raise ValueError('MODEL')
 if not all(map(math.isfinite,(line,qc,pc))) or qc<=0 or pc<=0:raise ValueError('NONFINITE_OR_NONPOSITIVE')
 if line<=cal['c']:return 0.,0.,{'iterations':0,'pressure_residual_bar':max(0.,cal['c']-line),'coupled_equation_residual_bar':max(0.,cal['c']-line),'status':'ZERO_DRIVING_PRESSURE'}
 shape=f0 if model==P1 else fphi;lo=0.;hi=min(pc*(1-DOMAIN_EPS),max(0.,line-cal['c']))
 def h(pb):return pb+brewer_drop(qc*shape(pb/pc),cal)-line
 flo,fhi=h(lo),h(hi)
 if not all(map(math.isfinite,(flo,fhi))):raise ValueError('NONFINITE_ROOT')
 if flo>PRESSURE_TOL or fhi<-PRESSURE_TOL:raise ValueError('NO_ADMISSIBLE_ROOT')
 mid=lo;hm=flo
 for it in range(1,MAX_ROOT_ITER+1):
  mid=(lo+hi)/2;hm=h(mid)
  if not math.isfinite(hm):raise ValueError('NONFINITE_ROOT')
  if abs(hm)<=PRESSURE_TOL or hi-lo<=PRESSURE_TOL:break
  if hm>0:hi=mid
  else:lo=mid
 else:raise ValueError('ROOT_NOT_CONVERGED')
 q=qc*shape(mid/pc);res=abs(mid+brewer_drop(q,cal)-line)
 if res>COUPLED_RESIDUAL_TOL:raise ValueError('COUPLED_EQUATION_RESIDUAL')
 return q,mid,{'iterations':it,'pressure_residual_bar':abs(hm),'coupled_equation_residual_bar':res,'status':'PASS'}

def balanced(rows):
 by={}
 for r in rows:by.setdefault(r['condition_id'],[]).append(r)
 return [(r,1/len(by)/len(v)) for v in by.values() for r in v]
def objective(logp,rows,model):
 if len(logp)!=2 or not all(map(math.isfinite,logp)):return math.inf
 qc,pc=map(math.exp,logp)
 try:
  value=sum(w*(predict(float(r['line_pressure_bar']),qc,pc,model)[0]-float(r['flow_g_s']))**2 for r,w in balanced(rows))
  return value if math.isfinite(value) else math.inf
 except (ValueError,OverflowError):return math.inf
def lattice():
 lo=[math.log(BOUNDS['Qc_g_s'][0]),math.log(BOUNDS['Pc_bar'][0])];hi=[math.log(BOUNDS['Qc_g_s'][1]),math.log(BOUNDS['Pc_bar'][1])];n=OPT['lattice_points_per_axis']
 return [(lo[0]+i*(hi[0]-lo[0])/(n-1),lo[1]+j*(hi[1]-lo[1])/(n-1)) for i in range(n) for j in range(n)]
def _better(v,x,bv,bx):
 tol=OPT['objective_comparison_tolerance'];return v<bv-tol or (abs(v-bv)<=tol and tuple(x)<tuple(bx))
def _profile_hessian(x,v,rows,model):
 h=IDENT['hessian_step'];cache={}
 def ev(dx,dy):
  if (dx,dy) not in cache:cache[dx,dy]=objective((x[0]+dx,x[1]+dy),rows,model)
  return cache[dx,dy]
 fxx=(ev(h,0)-2*v+ev(-h,0))/h**2;fyy=(ev(0,h)-2*v+ev(0,-h))/h**2;fxy=(ev(h,h)-ev(h,-h)-ev(-h,h)+ev(-h,-h))/(4*h*h)
 tr=fxx+fyy;disc=max(0.,(fxx-fyy)**2+4*fxy*fxy);eig=[(tr-math.sqrt(disc))/2,(tr+math.sqrt(disc))/2];cond=math.inf if eig[0]<=0 or not all(map(math.isfinite,eig)) else eig[1]/eig[0]
 profiles={}
 for k,name in enumerate(('log_Qc','log_Pc')):
  profiles[name]=[]
  for off in IDENT['profile_log_offsets']:
   for sign in (-1,1):
    y=list(x);y[k]+=sign*off;profiles[name].append({'offset':sign*off,'objective':objective(y,rows,model)})
 finite=[z['objective'] for q in profiles.values() for z in q if math.isfinite(z['objective'])];inc=min(((z-v)/max(abs(v),1e-12) for z in finite),default=0.)
 return {'hessian_log_space':[[fxx,fxy],[fxy,fyy]],'hessian_eigenvalues':eig,'hessian_condition_number':None if not math.isfinite(cond) else cond,'profile_scans':profiles,'minimum_relative_profile_increase':inc}
def fit(rows,model,objective_fn=None):
 raw_obj=objective_fn or (lambda x:objective(x,rows,model));cache={}
 def obj(x):
  key=tuple(x)
  if key not in cache:cache[key]=raw_obj(x)
  return cache[key]
 lo=[math.log(BOUNDS['Qc_g_s'][0]),math.log(BOUNDS['Pc_bar'][0])];hi=[math.log(BOUNDS['Qc_g_s'][1]),math.log(BOUNDS['Pc_bar'][1])]
 starts=lattice();best=None;evals=0;finite_starts=0;total_iters=0;last_step=None
 for start in starts:
  x=list(start);v=obj(x);evals+=1
  if not math.isfinite(v):continue
  finite_starts+=1;step=[(hi[k]-lo[k])/4 for k in range(2)];reason='MAX_ITERATIONS'
  for it in range(1,OPT['max_iterations_per_start']+1):
   total_iters+=1;improved=False
   for k in range(2):
    for sign in (-1,1):
     if evals>=OPT['max_evaluations']:reason='MAX_EVALUATIONS';break
     z=x.copy();z[k]=min(hi[k],max(lo[k],z[k]+sign*step[k]));vz=obj(z);evals+=1
     if math.isfinite(vz) and _better(vz,z,v,x):x,v,improved=z,vz,True
    if evals>=OPT['max_evaluations']:break
   if not improved:step=[q*OPT['step_reduction'] for q in step]
   if max(step)<=OPT['stopping_log_step']:reason='LOG_STEP_TOLERANCE';break
   if evals>=OPT['max_evaluations']:break
  last_step=max(step);candidate=(v,x,reason)
  if best is None or _better(v,x,best[0],best[1]):best=candidate
 if best is None:
  return {'execution_status':'BLOCKED','failure_class':'FIT_FAILURE','failure_reason':'NO_FINITE_ADMISSIBLE_FIT','optimizer_status':'FAIL','prediction_status':'NOT_ATTEMPTED','fitted_parameters':None,'objective':None,'finite_start_count':0,'start_count':len(starts),'evaluations':evals,'iterations':total_iters,'final_step_size':last_step,'convergence_reason':'NO_FINITE_START','root_failure_count':0,'domain_failure_count':0,'nonfinite_count':len(starts),'identifiability':'EXECUTION_BLOCKED'}
 v,x,reason=best;qc,pc=map(math.exp,x)
 if not(math.isfinite(v) and all(map(math.isfinite,(qc,pc))) and all(lo[k]-1e-12<=x[k]<=hi[k]+1e-12 for k in range(2))):
  return {'execution_status':'BLOCKED','failure_class':'FIT_FAILURE','failure_reason':'INVALID_FINAL_FIT','optimizer_status':'FAIL','prediction_status':'NOT_ATTEMPTED','fitted_parameters':None,'objective':None,'finite_start_count':finite_starts,'start_count':len(starts),'evaluations':evals,'iterations':total_iters,'final_step_size':last_step,'convergence_reason':reason,'root_failure_count':0,'domain_failure_count':0,'nonfinite_count':len(starts)-finite_starts,'identifiability':'EXECUTION_BLOCKED'}
 near=any(min(abs(x[k]-lo[k]),abs(hi[k]-x[k]))<=OPT['bound_hit_log_distance'] for k in range(2));diag=_profile_hessian(x,v,rows,model);cond=diag['hessian_condition_number'];inc=diag['minimum_relative_profile_increase']
 ident='BOUND_CONTROLLED' if near else ('PRACTICALLY_NONIDENTIFIABLE' if cond is None or cond>IDENT['weak_condition_max'] or inc<=0 else ('WEAKLY_IDENTIFIED' if cond>IDENT['adequate_condition_max'] or inc<IDENT['minimum_relative_profile_increase'] else 'ADEQUATELY_IDENTIFIED_FOR_PREDICTION'))
 return {'execution_status':'PASS','failure_class':'','failure_reason':'','optimizer_status':'PASS','prediction_status':'PENDING','fitted_parameters':{'Qc_g_s':qc,'Pc_bar':pc,'log_Qc':x[0],'log_Pc':x[1]},'objective':v,'finite_start_count':finite_starts,'start_count':len(starts),'evaluations':evals+16,'iterations':total_iters,'final_step_size':last_step,'convergence_reason':reason,'bound_proximity':near,'root_failure_count':0,'domain_failure_count':0,'nonfinite_count':len(starts)-finite_starts,'identifiability':ident,'identifiability_diagnostics':diag}

def percentile(v,p):return sorted(v)[max(0,min(len(v)-1,math.ceil(p*len(v))-1))]
def bootstrap(br,scales,a,b,folds=None):
 by={}
 for r in br:
  if r['model_id'] in (a,b):by.setdefault((r['outer_fold'],r['model_id']),{})[r['physical_unit_id']]=float(r['squared_error_g_s2'])
 fs=sorted(folds or {k[0] for k in by});rng=random.Random(SEED);draws=[]
 for _ in range(BOOTSTRAPS):
  loss={a:0.,b:0.}
  for f in [rng.choice(fs) for _ in fs]:
   ids=sorted(set(by.get((f,a),{}))&set(by.get((f,b),{})))
   if not ids:raise ValueError('BOOTSTRAP_MISSING_PAIRED_ROWS')
   picked=[rng.choice(ids) for _ in ids]
   for m in (a,b):loss[m]+=math.sqrt(sum(by[f,m][u] for u in picked)/len(picked))/scales[f]
  draws.append((loss[a]-loss[b])/len(fs))
 return {'ci_low':percentile(draws,.025),'ci_high':percentile(draws,.975),'draws':draws,'quantile_convention':'nearest-rank ceil(p*n)-1'}
def ranks(v):
 order=sorted(range(len(v)),key=lambda i:v[i]);out=[0.]*len(v);i=0
 while i<len(order):
  j=i+1
  while j<len(order) and v[order[j]]==v[order[i]]:j+=1
  rank=(i+1+j)/2
  for k in order[i:j]:out[k]=rank
  i=j
 return out
def spearman(a,b):
 ra,rb=ranks(a),ranks(b);am=sum(ra)/len(ra);bm=sum(rb)/len(rb);num=sum((x-am)*(y-bm) for x,y in zip(ra,rb));den=math.sqrt(sum((x-am)**2 for x in ra)*sum((y-bm)**2 for y in rb));return 0. if den==0 else num/den
def slope(x,y):
 xm=sum(x)/len(x);ym=sum(y)/len(y);den=sum((z-xm)**2 for z in x);return 0. if den==0 else sum((a-xm)*(b-ym) for a,b in zip(x,y))/den
def candidate_status(ci,diag,blocked=False):
 if blocked:return 'BLOCKED'
 if not(diag['low_direction_ok'] and diag['high_direction_ok']):return 'WRONG_PRESSURE_RESPONSE'
 if ci[0]>0:return 'STABLE_ADVANTAGE'
 if ci[1]<0:return 'STABLE_DISADVANTAGE'
 return 'INDISTINGUISHABLE'
def complexity_status(ci):
 if ci is None:return 'NOT_COMPUTABLE'
 if ci[0]>0:return 'STABLE_FINITE_PHI_ADVANTAGE'
 if ci[1]<0:return 'STABLE_UNIVERSAL_ADVANTAGE'
 return 'INDISTINGUISHABLE'
def overall(status,complexity):
 if any(status[x]=='BLOCKED' for x in CANDIDATES):return ('SCI_MD_011_POROELASTIC_CLOSURE_TEST_BLOCKED_BY_IDENTIFIABILITY_EXECUTION_DOMAIN_OR_EQUIVALENCE_GAP','NOT_ADJUDICATED')
 if all(status[x]=='WRONG_PRESSURE_RESPONSE' for x in CANDIDATES):return ('SCI_MD_011_TESTED_POROELASTIC_CLOSURES_FAIL_QUALIFIED_HIGH_PRESSURE_RESPONSE','REJECT_TESTED_QUASISTATIC_POROELASTIC_FORMS_FOR_FULL_PRESSURE_RESPONSE')
 pbad=status[P1] in ('WRONG_PRESSURE_RESPONSE','STABLE_DISADVANTAGE')
 if status[E2C]=='STABLE_ADVANTAGE' and (complexity=='STABLE_FINITE_PHI_ADVANTAGE' or pbad):return ('SCI_MD_011_CURRENT_EWP_FINITE_PHI_POROELASTIC_CLOSURE_STABLE_CONDITIONAL_UTILITY_ESTABLISHED','RETAIN_IMPLEMENTED_FINITE_PHI_PUCK_CLOSURE_AS_CONDITIONAL_COMPONENT_PENDING_SEPARATE_PRODUCTION_DECISION')
 if status[P1]=='STABLE_ADVANTAGE' and complexity!='STABLE_FINITE_PHI_ADVANTAGE':return ('SCI_MD_011_UNIVERSAL_POROELASTIC_LIMIT_HAS_STABLE_CONDITIONAL_UTILITY_FINITE_PHI_DEPENDENCY_NOT_SUPPORTED','SIMPLIFY_TO_UNIVERSAL_POROELASTIC_LIMIT_PRODUCTION_CHANGE_NOT_AUTHORIZED')
 passing=[status[x] for x in CANDIDATES if status[x]!='WRONG_PRESSURE_RESPONSE']
 if passing and all(x=='STABLE_DISADVANTAGE' for x in passing):return ('SCI_MD_011_NO_TESTED_POROELASTIC_CLOSURE_ADVANTAGE_OVER_QUADRATIC_BASELINE','RETIRE_TESTED_QUASISTATIC_POROELASTIC_CLOSURES_FROM_CURRENT_MODEL_DEVELOPMENT_PRIORITY')
 return ('SCI_MD_011_POROELASTIC_CLOSURES_INDISTINGUISHABLE_FROM_QUADRATIC_BASELINE_NO_STABLE_ADVANTAGE_ESTABLISHED','RETAIN_AT_MOST_AS_CONDITIONAL_PARSIMONIOUS_REPRESENTATION_CURRENT_FULL_EWP_NOT_VALIDATED')
def experiment_consequence(architecture):
 if architecture=='NOT_ADJUDICATED':action='IDENTIFY_EXACT_BLOCKER_NO_MEASUREMENT_UNLESS_IRREDUCIBLE_DECISION_CHANGING_OBSERVABLE'
 elif architecture.startswith('RETIRE') or architecture.startswith('REJECT'):action='REFORMULATE_BEFORE_HYDRAULIC_SPECIFIC_MEASUREMENT'
 elif architecture.startswith('RETAIN_AT_MOST'):action='PREFER_SIMPLEST_ADEQUATE_CONDITIONAL_REPRESENTATION_NO_COMPLEXITY_PRESERVATION_EXPERIMENT'
 else:action='RETAIN_FOR_SEPARATELY_AUTHORIZED_DECISION_NO_AUTOMATIC_EXPERIMENT'
 return {'architecture':architecture,'action':action,'stage_f_authorized':False,'stage_d_authorized':False,'m01_adjudicated':False}
