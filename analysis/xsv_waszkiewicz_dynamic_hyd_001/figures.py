"""Generate compact, claim-scoped figures from frozen task products."""
import csv, json, os
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/analysis/xsv_waszkiewicz_dynamic_hyd_001'
EVID=Path(os.environ.get('XSV_WASZKIEWICZ_EVIDENCE','review-evidence/xsv-waszkiewicz-dynamic-hyd-001'))
OUT=EVID/'figures'; OUT.mkdir(parents=True,exist_ok=True)
STAMP='SOURCE_INTERNAL · CONTROLLED COMPONENT COMPARISON · NOT INDEPENDENT WHOLE-MODEL VALIDATION'

def rows(name):
    with (DOC/name).open(newline='') as f:return list(csv.DictReader(f))
def finish(name,title):
    plt.title(title); plt.figtext(.5,.01,STAMP,ha='center',fontsize=6); plt.tight_layout(rect=(0,.035,1,1)); plt.savefig(OUT/name,dpi=160); plt.close()

reg=rows('BREW_CONDITION_REGISTER.csv'); by=defaultdict(int)
for r in reg:
    if r['independent_physical_brew']=='true':by[float(r['condition_id'])]+=1
plt.bar([str(x) for x in sorted(by)],[by[x] for x in sorted(by)]); plt.xlabel('controlled condition (bar)'); plt.ylabel('physical brews'); finish('01_inventory.png','Brew and condition inventory')

for fn,num,title in [('LEAVE_ONE_BREW_OUT_RESULTS.csv','02_lobo.png','LOBO normalized mass error'),('LEAVE_ONE_CONDITION_OUT_RESULTS.csv','03_loco.png','LOCO normalized mass error'),('BLOCKED_TIME_RESULTS.csv','04_blocked_time.png','Blocked-time normalized mass error')]:
    rr=rows(fn); models=sorted(set(r['model_id'] for r in rr)); vals=[[float(r['nrmse']) for r in rr if r['model_id']==m] for m in models]; plt.boxplot(vals,labels=models,showfliers=False); plt.ylabel('normalized RMSE'); finish(num,title)

rr=rows('LEAVE_ONE_CONDITION_OUT_RESULTS.csv'); conds=sorted(set(r['condition_id'] for r in rr),key=float)
for m in ['W-H1','W-H2','W-H3','W-H5']:
    d=[]
    for c in conds:
        a=np.mean([float(r['nrmse']) for r in rr if r['condition_id']==c and r['model_id']==m]); b=np.mean([float(r['nrmse']) for r in rr if r['condition_id']==c and r['model_id']=='W-H0A']); d.append(a-b)
    plt.plot(conds,d,'o-',label=m)
plt.axhline(0,color='k',lw=.7); plt.xticks(rotation=45); plt.ylabel('evolving/control minus fixed NRMSE'); plt.legend(); finish('05_paired_condition_differences.png','Paired condition differences')

sens=rows('PROCESSING_SENSITIVITY.csv'); models=sorted(set(r['model'] for r in sens)); cfg=sorted(set(r['configuration_id'] for r in sens)); z=np.array([[float(next(r for r in sens if r['model']==m and r['configuration_id']==c)['primary_error']) for c in cfg] for m in models]); plt.imshow(z,aspect='auto'); plt.yticks(range(len(models)),models); plt.xticks(range(len(cfg)),cfg,rotation=35,ha='right'); plt.colorbar(label='LOCO NRMSE'); finish('06_processing_sensitivity.png','Processing-window sensitivity')

par=rows('PARAMETER_STABILITY.csv');
for m in sorted(set(r['model_id'] for r in par)):
    x=[float(r['value']) for r in par if r['model_id']==m and r['parameter_index']=='0']; plt.plot(x,'o',ms=3,label=m)
plt.xlabel('LOCO condition fold'); plt.ylabel('log-resistance intercept'); plt.legend(); finish('07_parameter_stability.png','Foldwise parameter stability')

res=rows('RESIDUAL_FINDINGS.csv'); plt.bar([r['model_id'] for r in res],[float(r['mean_residual_g']) for r in res]); plt.ylabel('mean mass residual (g)'); finish('08_residual_summary.png','Held-out residual summary')

cmp=rows('MODEL_COMPARISON_RESULTS.csv'); x=np.arange(len(cmp)); w=.25
for j,key in enumerate(['lobo_condition_balanced_nrmse','loco_condition_balanced_nrmse','blocked_time_condition_balanced_nrmse']): plt.bar(x+(j-1)*w,[float(r[key]) for r in cmp],w,label=key.split('_')[0])
plt.xticks(x,[r['model_id'] for r in cmp]); plt.ylabel('condition-balanced NRMSE'); plt.legend(); finish('09_grouped_overview.png','Grouped predictive comparison')

summary=json.load((DOC/'summary.json').open());
plt.axis('off'); plt.text(.02,.85,'Published Waszkiewicz lane',fontsize=15); plt.text(.02,.65,'Static parity: PASS\nDynamic 9-bar parity: PASS\nPrivilege: SOURCE_POST_FIT_RECONSTRUCTION\nSoft circularity: same-rig dissolved-mass trajectory',fontsize=11); finish('10_source_model_lane.png','Source model parity and privilege')

# Remaining required views are explicit derived summaries, not invented raw channels.
for name,title,text in [('11_signal_contract.png','Signal and observation contract','Line pressure: measured/source processed\nBasket pressure: derived\nMass: scale measured, aligned/interpolated\nFlow: SG-derived diagnostic'),('12_delay_control.png','Observation-delay control','Frozen +1 s delay did not improve grouped LOCO prediction'),('13_model_form_conclusion.png','Model-form conclusion','No evolving form passed all strong gates\nFixed resistance retained at available variability')]:
    plt.axis('off'); plt.text(.05,.65,text,fontsize=13); finish(name,title)
