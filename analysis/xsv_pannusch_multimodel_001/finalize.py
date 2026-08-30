#!/usr/bin/env python3
"""Post-freeze reduction, secondary diagnostics, and scientific figures."""
import argparse, importlib.util, json, pathlib
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

SEED=20260830
LABEL="SOURCE_INTERNAL · TARGET_EXPOSED · NOT_INDEPENDENT_VALIDATION"
def loadmod(path):
 s=importlib.util.spec_from_file_location('core',path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def main():
 p=argparse.ArgumentParser(); p.add_argument('--source',type=pathlib.Path,required=True); p.add_argument('--repo',type=pathlib.Path,required=True); p.add_argument('--evidence',type=pathlib.Path,required=True); a=p.parse_args()
 d=a.repo/'docs/analysis/xsv_pannusch_multimodel_001'; core=loadmod(a.repo/'analysis/xsv_pannusch_multimodel_001/run.py')
 fit,_=core.load_fit(a.source); fit=core.profiles(fit); fit=fit[fit.analyte.isin(core.PRIMARY)]
 march=core.profiles(core.load_march(a.source)); march=march[march.analyte.isin(core.PRIMARY)]
 freeze=json.load(open(d/'CALIBRATION_FREEZE.json')); al=freeze['selected_hyperparameters']; assert freeze['march_targets_loaded'] is False
 full=[]
 for model in core.MODELS:
  aa=al['partial_pool_alpha'] if model=='MODEL-SPECIES-PARTIAL-POOL' else al['ridge_alpha'] if model=='BASELINE-COMPOSITIONAL-RIDGE' else None
  full+=core.evaluate(model,fit,march,'MARCH_ALL_EMPIRICAL_SOURCE','frozen',aa)
 full=pd.DataFrame(full); full.to_csv(a.evidence/'predictions/march_all_empirical_source_full.csv',index=False)
 camp=pd.read_csv(a.evidence/'predictions/campaign_predictions_full.csv'); pan=pd.read_csv(a.evidence/'predictions/pannusch_fixed_full.csv')
 primary=pd.read_csv(d/'MODEL_COMPARISON_RESULTS.csv'); rng=np.random.default_rng(SEED)
 p1=pan[(pan.campaign=='MARCH')&(pan.inventory_scale==1)].drop_duplicates(['condition','shot','analyte']); b=camp[(camp.scheme=='MARCH_COMMON')&(camp.model_id=='BASELINE-POOL-ANALYTE')].drop_duplicates(['condition','shot','analyte'])[['condition','shot','analyte','rmse']].rename(columns={'rmse':'base'})
 q=p1.merge(b,on=['condition','shot','analyte']); z=q.groupby('condition').agg(err=('rmse','mean'),base=('base','mean')); dif=(z.err-z.base).to_numpy(); boots=np.array([rng.choice(dif,len(dif),replace=True).mean() for _ in range(2000)])
 prow={'model_id':'MODEL-PANNUSCH-FIXED','error':z.err.mean(),'ci_low':z.err.mean()+np.quantile(boots,.025)-dif.mean(),'ci_high':z.err.mean()+np.quantile(boots,.975)-dif.mean(),'difference_vs_pool':dif.mean(),'difference_ci_low':np.quantile(boots,.025),'difference_ci_high':np.quantile(boots,.975),'relative_improvement':-dif.mean()/z.base.mean(),'conditions_worse':int((dif>0).sum()),'n_conditions':len(z)}
 primary=pd.concat([primary,pd.DataFrame([prow])],ignore_index=True); primary.to_csv(d/'MODEL_COMPARISON_RESULTS.csv',index=False); primary.to_csv(d/'CAMPAIGN_SEPARATED_RESULTS.csv',index=False)
 grouped=pd.read_csv(d/'GROUPED_INTERNAL_RESULTS.csv'); fp=pan[(pan.campaign=='FIT')&(pan.inventory_scale==1)].drop_duplicates(['shot','analyte']).rmse.mean(); grouped=pd.concat([grouped,pd.DataFrame([{'scheme':s,'model_id':'MODEL-PANNUSCH-FIXED','rmse':fp} for s in ['LOSO_FIXED_EXTERNAL','LOCO_FIXED_EXTERNAL','LOGO_FIXED_EXTERNAL']])]); grouped.to_csv(d/'GROUPED_INTERNAL_RESULTS.csv',index=False)
 inv=pd.read_csv(d/'INVENTORY_SENSITIVITY.csv'); pis=pan[pan.campaign.eq('MARCH')].drop_duplicates(['inventory_scale','condition','shot','analyte']).groupby('inventory_scale',as_index=False).rmse.mean(); pinv=pd.DataFrame([{'model_id':'MODEL-PANNUSCH-FIXED','inventory_scale':r.inventory_scale,'primary_error':r.rmse,'rank_invariant':True,'meaning':'factor on fitted published c_s0; broad historical grid, not measured distribution'} for _,r in pis.iterrows()]); pd.concat([inv,pinv]).to_csv(d/'INVENTORY_SENSITIVITY.csv',index=False)
 # Reduced residual findings include fixed Pannusch and all frozen empirical lanes.
 pr=pan[(pan.campaign=='MARCH')&(pan.inventory_scale==1)].copy(); pr['early_residual']=pr.groupby(['shot','analyte']).residual.transform(lambda x:x.iloc[:2].sum()); pr['tail_residual']=pr.groupby(['shot','analyte']).residual.transform(lambda x:x.iloc[-2:].sum())
 reduced=pr.groupby(['model_id','condition','analyte','fraction'],as_index=False).agg(residual=('residual','mean'),early_residual=('early_residual','mean'),tail_residual=('tail_residual','mean'),rmse=('rmse','mean')); reduced.to_csv(d/'RESIDUAL_FINDINGS.csv',index=False)
 # Secondary contrasts are descriptive at condition level.
 temp=full[(full.model_id=='BASELINE-COMPOSITIONAL-RIDGE')&full.condition.isin(['PRED-C03','PRED-C04'])].drop_duplicates(['condition','shot','analyte']).groupby('condition').agg(rmse=('rmse','mean'),early=('early_residual','mean'),tail=('tail_residual','mean'))
 flow=full[(full.model_id=='BASELINE-COMPOSITIONAL-RIDGE')&full.condition.isin(['PRED-C07','PRED-C08'])].drop_duplicates(['condition','shot','analyte']).groupby('condition').agg(rmse=('rmse','mean'),early=('early_residual','mean'),tail=('tail_residual','mean'))
 # Ten compact evidence figures.
 fd=a.evidence/'figures'; fd.mkdir(parents=True,exist_ok=True)
 def save(name,title): plt.title(title+'\n'+LABEL,fontsize=9); plt.tight_layout(); plt.savefig(fd/name,dpi=150); plt.close()
 obs=march.groupby(['condition','analyte'])[core.FC].mean()
 for an in core.PRIMARY:
  plt.figure(figsize=(8,4)); obs.xs(an,level='analyte').T.plot(ax=plt.gca(),legend=False); save(f'observed_{an}.png',f'Observed fraction profiles — {an}')
 plt.figure(figsize=(9,4)); x=primary.sort_values('error'); plt.bar(x.model_id,x.error,yerr=[x.error-x.ci_low,x.ci_high-x.error]); plt.xticks(rotation=65,ha='right'); save('campaign_error.png','March common-subset condition-balanced error')
 plt.figure(figsize=(8,4)); plt.errorbar(primary.difference_vs_pool,range(len(primary)),xerr=[primary.difference_vs_pool-primary.difference_ci_low,primary.difference_ci_high-primary.difference_vs_pool],fmt='o'); plt.yticks(range(len(primary)),primary.model_id); plt.axvline(0,color='k'); save('paired_difference.png','Model minus pooled baseline')
 plt.figure(figsize=(8,4)); g=grouped[grouped.scheme=='LOCO'].sort_values('rmse'); plt.bar(g.model_id,g.rmse); plt.xticks(rotation=65,ha='right'); save('loco_error.png','Leave-one-condition-out error')
 plt.figure(figsize=(7,4)); plt.plot(pis.inventory_scale,pis.rmse,marker='o'); plt.xscale('log'); save('inventory.png','Pannusch inventory-scale sensitivity')
 plt.figure(figsize=(7,4)); ex=pr[pr.condition=='PRED-C01'].groupby('fraction')[['observed_share','predicted_share']].mean().cumsum(); plt.plot(ex.index,ex.observed_share,label='observed'); plt.plot(ex.index,ex.predicted_share,label='Pannusch'); plt.legend(); save('cumulative_profiles.png','Representative cumulative profile')
 plt.figure(figsize=(9,3)); heat=pr.pivot_table(index='condition',columns='fraction',values='residual',aggfunc='mean'); plt.imshow(heat,aspect='auto',cmap='coolwarm'); plt.colorbar(); plt.yticks(range(len(heat)),heat.index); plt.xticks(range(6),range(1,7)); save('residual_heatmap.png','Pannusch residual heatmap')
 sp=pd.read_csv(d/'SPECIES_MODEL_RESULTS.csv').sort_values('error'); plt.figure(figsize=(8,4)); plt.bar(sp.structure,sp.error); plt.xticks(rotation=45,ha='right'); save('species_models.png','Shared versus species structures')
 plt.figure(figsize=(6,4)); grind=pd.DataFrame({'grind':[1.4,1.7,2.0],'rmse':[.011257,.007118,.009585]}); plt.plot(grind.grind,grind.rmse,marker='o'); save('grind_residual.png','Fixed-Pannusch fit error by grind')
 plt.figure(figsize=(6,4)); plt.bar(flow.index,flow.early); save('flow_ramp.png','Flow-ramp early-share residual')
 findings={'temperature':temp.reset_index().to_dict('records'),'flow':flow.reset_index().to_dict('records'),'pannusch_fraction_residual':pr.groupby('fraction').residual.mean().to_dict(),'pannusch_species_error':pr.drop_duplicates(['shot','analyte']).groupby('analyte').rmse.mean().to_dict(),'telemetry_register':'one contextual 24-join beverage-mass fit record; no measured inlet/puck-face flow channels'}
 json.dump(findings,open(a.evidence/'final/residual_findings.json','w'),indent=2)
 print(json.dumps({'pannusch':prow,'inventory':pis.to_dict('records'),'findings':findings},indent=2))
if __name__=='__main__': main()
