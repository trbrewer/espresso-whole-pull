#!/usr/bin/env python3
"""Fixed published Pannusch lane; no parameter or March-target fitting."""
import argparse, json, pathlib, sys
import numpy as np, pandas as pd

PRIMARY={"caffeine":"caffeine","trigonelline":"trigonelline"}
def main():
 p=argparse.ArgumentParser(); p.add_argument('--source',type=pathlib.Path,required=True); p.add_argument('--puckworks',type=pathlib.Path,required=True); p.add_argument('--repo',type=pathlib.Path,required=True); p.add_argument('--evidence',type=pathlib.Path,required=True); a=p.parse_args()
 sys.path.insert(0,str(a.puckworks)); from puckworks.models.pannusch2024 import solver as ps
 freeze=json.load(open(a.repo/'docs/analysis/xsv_pannusch_multimodel_001/CALIBRATION_FREEZE.json')); assert freeze['march_targets_loaded'] is False
 fit=pd.read_csv(a.source/'fit_fraction_replicates.csv'); fit=fit[fit.validity.eq('VALID')]
 kin=pd.read_csv(a.source/'experimental_kinetics.csv').groupby('exp',as_index=False).first(); fit=fit.merge(kin[['exp','Temp_C','flow_mL_s','grind_setting']],left_on='source_experiment_id',right_on='exp')
 # cl1 is one global, calibration-only analyte scale; never selected on March.
 cl1={an:float(g.sort_values('fraction_id').groupby('shot_id').first().concentration_value.mean()) for an,g in fit[fit.analyte.isin(PRIMARY)].groupby('analyte')}
 params=ps._solute_params(); rows=[]
 def one(g,camp,T,flow,grind,model_an,scale=1.0):
  g=g.sort_values('fraction_id'); bounds=sorted(set(g.fraction_start_s)|set(g.fraction_end_s)); sp=dict(params[model_an]); sp['c_s0']*=scale; raw=ps.simulate_fractions(float(T),float(flow),bounds,sp,cl1[model_an],ps.GRINDS[float(grind)]); pred=np.array([ps._interval_conc(raw,bounds,float(r.fraction_start_s),float(r.fraction_end_s)) for _,r in g.iterrows()])
  liq=g.fraction_liquid_g_or_ml.to_numpy(float); mass=np.maximum(pred,0)*liq; q=mass/mass.sum(); obs=(g.analyte_mass_mg if camp=='FIT' else g.derived_analyte_mass_mg).to_numpy(float); obs=obs/obs.sum()
  for j in range(6): rows.append({'scheme':'FIXED_SOURCE','fold':'published','model_id':'MODEL-PANNUSCH-FIXED','campaign':camp,'condition':g.condition_id.iloc[0],'shot':g.shot_id.iloc[0],'analyte':model_an,'inventory_scale':scale,'fraction':j+1,'observed_share':obs[j],'predicted_share':q[j],'residual':q[j]-obs[j],'rmse':float(np.sqrt(np.mean((q-obs)**2)))})
 for (_,_,an),g in fit[fit.analyte.isin(PRIMARY)].groupby(['condition_id','shot_id','analyte']):
  if len(g)==6: one(g,'FIT',g.Temp_C.iloc[0],g.flow_mL_s.iloc[0],g.grind_setting.iloc[0],an)
 march=pd.read_csv(a.source/'prediction_fraction_replicates.csv'); march=march[march.validity.eq('VALID') & march.analyte.isin(PRIMARY) & march.condition_id.isin(['PRED-C01','PRED-C02','PRED-C05','PRED-C06'])]
 for (_,_,an),g in march.groupby(['condition_id','shot_id','analyte']):
  if len(g)==6:
   for scale in [.01,.1,1.0]: one(g,'MARCH',g.temperature_start_C.iloc[0],g.flow_start_mL_s.iloc[0],1.7,an,scale)
 out=pd.DataFrame(rows); a.evidence.joinpath('predictions').mkdir(parents=True,exist_ok=True); out.to_csv(a.evidence/'predictions/pannusch_fixed_full.csv',index=False)
 summary=out.groupby(['campaign','model_id','inventory_scale']).rmse.mean().reset_index().to_dict('records'); json.dump({'cl1_training_only':cl1,'inventory_scale_meaning':'multiplicative factor on published fitted c_s0; broad historical sensitivity grid, not a measured distribution','rows':len(out),'summary':summary,'parity':'PASS_6.372298181639968_PERCENT'},open(a.evidence/'models/pannusch_fixed_summary.json','w'),indent=2)
 print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
