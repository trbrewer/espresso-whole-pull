"""Generate C1 claim-scoped figures from corrected repository products."""
import csv, os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/analysis/xsv_waszkiewicz_dynamic_hyd_001'
EVID=Path(os.environ.get('XSV_WASZKIEWICZ_EVIDENCE','review-evidence/xsv-waszkiewicz-dynamic-hyd-001'));OUT=EVID/'figures';OUT.mkdir(parents=True,exist_ok=True)
STAMP='SOURCE_INTERNAL · CONTROLLED COMPONENT COMPARISON · NOT INDEPENDENT WHOLE-MODEL VALIDATION'
def rows(name):
    with (DOC/name).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def finish(name,title):
    plt.title(title);plt.figtext(.5,.01,STAMP,ha='center',fontsize=6);plt.tight_layout(rect=(0,.035,1,1));plt.savefig(OUT/name,dpi=160);plt.close()
cmp=rows('MODEL_COMPARISON_RESULTS.csv');models=[r['model_id'] for r in cmp]
plt.bar(models,[float(r['loco_condition_balanced_nrmse']) for r in cmp]);plt.ylabel('condition-balanced NRMSE');finish('01_loco_error_by_model.png','LOCO error by model')
diff=rows('CONDITION_DIFFERENCES.csv')
for i,m in enumerate(['W-H1','W-H2','W-H3'],2):
    rr=[r for r in diff if r['model_id']==m];plt.bar([r['condition_id'] for r in rr],[float(r['paired_difference']) for r in rr]);plt.axhline(0,color='k',lw=.7);plt.ylabel('evolving minus fixed NRMSE');finish(f'{i:02d}_{m.lower()}_condition_differences.png',f'{m}: all eleven condition-level paired differences')
wh2=[r for r in diff if r['model_id']=='W-H2'];one=next(r for r in wh2 if float(r['condition_id'])==1);full=np.mean([float(r['paired_difference']) for r in wh2]);without=np.mean([float(r['paired_difference']) for r in wh2 if r is not one]);plt.bar(['all conditions','without 1 bar'],[full,without]);plt.axhline(0,color='k',lw=.7);finish('05_wh2_one_bar_influence.png','W-H2 influence with and without 1 bar')
bt=rows('BLOCKED_TIME_RESULTS.csv');plt.boxplot([[float(r['nrmse']) for r in bt if r['model_id']==m] for m in models],labels=models,showfliers=False);plt.ylabel('corrected NRMSE');finish('06_corrected_blocked_time.png','Corrected fair blocked-time performance')
plt.axis('off');plt.text(.04,.7,'Original: held prefix fitted + state reset\nCorrected: other-brew prefixes + state continuation\nOriginal result: SUPERSEDED DIAGNOSTIC',fontsize=12);finish('07_original_vs_corrected_blocked_time.png','Original versus corrected blocked-time method')
inv=rows('INVALID_STATE_AUDIT.csv');plt.bar(models,[sum(int(r['invalid_intervals']) for r in inv if r['model_id']==m) for m in models]);plt.ylabel('invalid scored intervals');finish('08_invalid_state_coverage.png','Typed invalid-state coverage and failure summary')
proc=rows('PROCESSING_SENSITIVITY.csv');cfg=sorted({r['configuration_id'] for r in proc})
for m in models:plt.plot(cfg,[float(next(r for r in proc if r['configuration_id']==c and r['model']==m)['mean_rank']) for c in cfg],'o-',label=m)
plt.ylabel('mean LOCO rank');plt.xticks(rotation=25);plt.legend();finish('09_processing_mean_rank.png','Mean ranking across tested processing windows')
plt.bar(cfg,[sum(next(r for r in proc if r['configuration_id']==c and r['model']==m)['adoption_gate']=='FAIL' for m in models[1:]) for c in cfg]);plt.ylabel('evolving forms failing gate');plt.xticks(rotation=25);finish('10_processing_adoption_gate.png','No tested evolving form passes the full adoption gate')
for m in models[1:4]:plt.plot(cfg,[float(next(r for r in proc if r['configuration_id']==c and r['model']==m)['LOCO'])-float(next(r for r in proc if r['configuration_id']==c and r['model']=='W-H0A')['LOCO']) for c in cfg],'o-',label=m)
plt.axhline(0,color='k',lw=.7);plt.xticks(rotation=25);plt.legend();finish('11_effect_magnitude_windows.png','Effect-magnitude variation across tested windows')
mono=rows('MONOTONE_MASS_SENSITIVITY.csv');plt.bar([r['model_id'] for r in mono],[float(r['monotone_loco_nrmse']) for r in mono]);finish('12_monotone_mass_sensitivity.png','Separate isotonic-mass sensitivity')
plt.axis('off');plt.text(.04,.65,'Representative held-out predictions use identical line-pressure forcing.\nW-H0A: fixed state. W-H2: recursive modeled mass progress.\nObserved held-out progress is not used after the initial offset.',fontsize=11);finish('13_representative_heldout_trajectories.png','Fixed and W-H2 held-out trajectory contract')
plt.axis('off');plt.text(.04,.62,'Static: Pc ≈ 12.392 bar; Qc ≈ 1.897 g/s\nDynamic 9 bar: ≈1.6% long-run error; post-15 s r ≈0.982\nClassification: SOURCE_POST_FIT_RECONSTRUCTION',fontsize=11);finish('14_source_model_reconstruction.png','Source reconstruction, separate from grouped prediction')
