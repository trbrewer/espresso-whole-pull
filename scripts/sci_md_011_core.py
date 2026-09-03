#!/usr/bin/env python3
"""Task-local numerical core for SCI-MD-011."""
from __future__ import annotations
import csv, hashlib, json, math, random, subprocess
from functools import lru_cache
from pathlib import Path

TASK="SCI-MD-011"
SEED=20260902
BOOTSTRAPS=2000
MODELS=("HYD_B0_TRAINING_MEAN","HYD_B1_PRESSURE_QUADRATIC","HYD_P1_POROELASTIC_UNIVERSAL_LIMIT","HYD_E2C_EWP_FINITE_PHI_POROELASTIC_COMPONENT")
P1,E2C=MODELS[2:]
PHI=2.257390325360356/18.5
CAL={"a":0.017184292098914252,"b":0.03670858658698296,"c":0.2831597837775055}
DOMAIN_EPS=1e-10; PRESSURE_TOL=1e-9; FLOW_TOL=2e-9; MAX_ROOT_ITER=100
BOUNDS={"Qc_g_s":[0.01,20.0],"Pc_bar":[13.00000001,100.0]}

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_json(p): return json.loads(Path(p).read_text())
def load_csv(p):
 with Path(p).open(newline='') as f:return list(csv.DictReader(f))
def write_json(p,v): Path(p).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def write_csv(p,fields,rows):
 with Path(p).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()

def integral(x,phi):
 if not(math.isfinite(x) and math.isfinite(phi) and 0<=x<=1 and 0<phi<1):raise ValueError('DOMAIN')
 total=0.;pp=1.;xp=x
 for n in range(4096):
  term=pp*(xp/(n+1)-3*xp*x/(n+2)+3*xp*x*x/(n+3)-xp*x*x*x/(n+4));total+=term
  if n>8 and abs(term)<=2e-16*max(total,1e-300):break
  pp*=phi;xp*=x
 return total
def f0(x):
 if not math.isfinite(x) or not 0<=x<=1:raise ValueError('DOMAIN')
 return x*(4-6*x+4*x*x-x*x*x)
@lru_cache(maxsize=16)
def _normalizer(phi):return integral(1.,phi)
def _integral_fast(x,p):
 return (2*p**3*x**3+3*p*p*x*x*(1-3*p)+6*p*x*(3*p*p-3*p+1)+6*(1-p)**3*math.log1p(-p*x))/(6*p**4)
def fphi(x,phi=PHI):
 if not(math.isfinite(x) and 0<=x<=1 and 0<phi<1):raise ValueError('DOMAIN')
 return _integral_fast(x,phi)/_integral_fast(1.,phi)
def brewer_drop(q,cal=CAL):return cal['a']*q*q+cal['b']*q+cal['c']

def predict(line,qc,pc,model,cal=CAL):
 if not all(map(math.isfinite,(line,qc,pc))) or qc<=0 or pc<=0:raise ValueError('NONFINITE_OR_NONPOSITIVE')
 if line<=cal['c']:return 0.,0.,{'iterations':0,'pressure_residual_bar':max(0.,cal['c']-line),'flow_consistency_g_s':0.,'status':'ZERO_DRIVING_PRESSURE'}
 shape=f0 if model==P1 else fphi
 hi=min(pc*(1-DOMAIN_EPS),max(0.,line-cal['c']));lo=0.
 def h(pb):return pb+brewer_drop(qc*shape(pb/pc),cal)-line
 flo,fhi=h(lo),h(hi)
 if not all(map(math.isfinite,(flo,fhi))):raise ValueError('NONFINITE_ROOT')
 if flo>PRESSURE_TOL or fhi<-PRESSURE_TOL:raise ValueError('NO_ADMISSIBLE_ROOT')
 for it in range(1,MAX_ROOT_ITER+1):
  mid=(lo+hi)/2;hm=h(mid)
  if abs(hm)<=PRESSURE_TOL or hi-lo<=PRESSURE_TOL:
   q=qc*shape(mid/pc);cons=abs(mid+brewer_drop(q,cal)-line)
   if cons>FLOW_TOL:raise ValueError('FLOW_CONSISTENCY')
   return q,mid,{'iterations':it,'pressure_residual_bar':abs(hm),'flow_consistency_g_s':cons,'status':'PASS'}
  if hm>0:hi=mid
  else:lo=mid
 raise ValueError('ROOT_NOT_CONVERGED')

def balanced(rows):
 by={}
 for r in rows:by.setdefault(r['condition_id'],[]).append(r)
 return [(r,1/len(by)/len(v)) for v in by.values() for r in v]
def objective(logp,rows,model):
 qc,pc=map(math.exp,logp)
 try:return sum(w*(predict(float(r['line_pressure_bar']),qc,pc,model)[0]-float(r['flow_g_s']))**2 for r,w in balanced(rows))
 except ValueError:return math.inf
def fit(rows,model):
 lo=[math.log(BOUNDS['Qc_g_s'][0]),math.log(BOUNDS['Pc_bar'][0])];hi=[math.log(BOUNDS['Qc_g_s'][1]),math.log(BOUNDS['Pc_bar'][1])]
 starts=[(lo[0]+i*(hi[0]-lo[0]),lo[1]+j*(hi[1]-lo[1])) for i in range(2) for j in range(2)]
 best=None;evals=0
 for start in starts:
  x=list(start);step=[(hi[k]-lo[k])/4 for k in range(2)];v=objective(x,rows,model);evals+=1
  for _ in range(24):
   improved=False
   for k in range(2):
    for s in (-1,1):
     z=x.copy();z[k]=min(hi[k],max(lo[k],z[k]+s*step[k]));vz=objective(z,rows,model);evals+=1
     if (vz,z)<(v,x):x,v,improved=z,vz,True
   if not improved:step=[q/2 for q in step]
   if max(step)<1e-5:break
  candidate=(v,x)
  if best is None or candidate<best:best=candidate
 v,x=best;qc,pc=map(math.exp,x);near=qc/BOUNDS['Qc_g_s'][0]<1.00001 or BOUNDS['Qc_g_s'][1]/qc<1.00001 or pc/BOUNDS['Pc_bar'][0]<1.00001 or BOUNDS['Pc_bar'][1]/pc<1.00001
 return {'Qc_g_s':qc,'Pc_bar':pc,'log_Qc':x[0],'log_Pc':x[1],'objective':v,'evaluations':evals,'optimizer_status':'PASS','bound_proximity':near,'identifiability':'BOUND_CONTROLLED' if near else 'ADEQUATELY_IDENTIFIED_FOR_PREDICTION'}

def percentile(v,p):return sorted(v)[max(0,min(len(v)-1,math.ceil(p*len(v))-1))]
def bootstrap(br,scales,a,b,subset=None):
 by={}
 for r in br:
  if r['model_id'] in (a,b):by.setdefault((r['outer_fold'],r['model_id']),{})[r['physical_unit_id']]=float(r['squared_error_g_s2'])
 folds=sorted(subset or {k[0] for k in by});rng=random.Random(SEED);draws=[]
 for _ in range(BOOTSTRAPS):
  loss={a:0.,b:0.}
  for f in [rng.choice(folds) for _ in folds]:
   ids=sorted(set(by[f,a])&set(by[f,b]));picked=[rng.choice(ids) for _ in ids]
   for m in (a,b):loss[m]+=math.sqrt(sum(by[f,m][u] for u in picked)/len(picked))/scales[f]
  draws.append((loss[a]-loss[b])/len(folds))
 return {'point':None,'ci_low':percentile(draws,.025),'ci_high':percentile(draws,.975),'draws':draws,'quantile_convention':'nearest-rank ceil(p*n)-1'}

def candidate_status(ci,diag,blocked=False):
 if blocked:return 'BLOCKED'
 if not(diag['low_direction_ok'] and diag['high_direction_ok']):return 'WRONG_PRESSURE_RESPONSE'
 if ci[0]>0:return 'STABLE_ADVANTAGE'
 if ci[1]<0:return 'STABLE_DISADVANTAGE'
 return 'INDISTINGUISHABLE'
def overall(status,pair):
 if 'BLOCKED' in status.values():return ('SCI_MD_011_POROELASTIC_CLOSURE_TEST_BLOCKED_BY_IDENTIFIABILITY_EXECUTION_DOMAIN_OR_EQUIVALENCE_GAP','NOT_ADJUDICATED')
 if all(status[x]=='WRONG_PRESSURE_RESPONSE' for x in (P1,E2C)):return ('SCI_MD_011_TESTED_POROELASTIC_CLOSURES_FAIL_QUALIFIED_HIGH_PRESSURE_RESPONSE','REJECT_TESTED_QUASISTATIC_POROELASTIC_FORMS_FOR_FULL_PRESSURE_RESPONSE')
 if status[E2C]=='STABLE_ADVANTAGE' and pair=='STABLE_ADVANTAGE':return ('SCI_MD_011_CURRENT_EWP_FINITE_PHI_POROELASTIC_CLOSURE_STABLE_CONDITIONAL_UTILITY_ESTABLISHED','RETAIN_IMPLEMENTED_FINITE_PHI_PUCK_CLOSURE_AS_CONDITIONAL_COMPONENT_PENDING_SEPARATE_PRODUCTION_DECISION')
 if status[P1]=='STABLE_ADVANTAGE' and pair!='STABLE_ADVANTAGE':return ('SCI_MD_011_UNIVERSAL_POROELASTIC_LIMIT_HAS_STABLE_CONDITIONAL_UTILITY_FINITE_PHI_DEPENDENCY_NOT_SUPPORTED','SIMPLIFY_TO_UNIVERSAL_POROELASTIC_LIMIT_PRODUCTION_CHANGE_NOT_AUTHORIZED')
 passing=[status[x] for x in (P1,E2C) if status[x]!='WRONG_PRESSURE_RESPONSE']
 if passing and all(x=='STABLE_DISADVANTAGE' for x in passing):return ('SCI_MD_011_NO_TESTED_POROELASTIC_CLOSURE_ADVANTAGE_OVER_QUADRATIC_BASELINE','RETIRE_TESTED_QUASISTATIC_POROELASTIC_CLOSURES_FROM_CURRENT_MODEL_DEVELOPMENT_PRIORITY')
 return ('SCI_MD_011_POROELASTIC_CLOSURES_INDISTINGUISHABLE_FROM_QUADRATIC_BASELINE_NO_STABLE_ADVANTAGE_ESTABLISHED','RETAIN_AT_MOST_AS_CONDITIONAL_PARSIMONIOUS_REPRESENTATION_CURRENT_FULL_EWP_NOT_VALIDATED')
