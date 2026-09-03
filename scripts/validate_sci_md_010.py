#!/usr/bin/env python3
import argparse
from pathlib import Path
from sci_md_010_core import *
R=Path(__file__).resolve().parents[1];D=R/'docs/analysis/sci_md_010'
def freeze_validate():
 pw=resolve_puckworks();pre=load_json(D/'PRE_SCORE_FREEZE.json');assert pre['revision']=='R4' and pre['seed']==20260902 and pre['random_seeds']==[20260902] and not pre['scoring_executed'] and not pre['real_target_scores_generated'] and not pre['phase_b_authorized'] and not pre['stage_f_authorized'] and not pre['stage_d_authorized']
 gate=load_json(D/'EWP_EXECUTABILITY_GATE.json');assert gate['lanes'][0]['executable'] and gate['lanes'][0]['e1_executable']
 reg=load_json(D/'INPUT_ARTIFACT_REGISTER.json');validate_artifacts(R,reg,pw);assert {'WASZ_EQUILIBRIUM','WASZ_LINE_PRESSURE','WASZ_MACHINE_PARAMS'}<={x['artifact_id'] for x in reg['artifacts']}
 c=load_json(D/'EVALUATION_CONTRACT.json');specs=load_json(R/c['models'])['models'];ids={m['model_id'] for m in specs};assert set(c['model_ids'])==ids
 for m in specs:
  assert sha256(R/m['implementation_file'])==m['implementation_sha256']
  assert all(n in MODEL_CALLABLES for n in m['callable'].split(','))
 rows=load_csv(R/c['row_index']);assert len(rows)==len({r['physical_unit_id'] for r in rows})==56 and all(r['exogenous_fields'].startswith('pressure__bar') and 'basket_pressure' not in r['exogenous_fields'] for r in rows)
 folds=load_csv(R/c['folds']);mem=load_csv(R/c['membership']);assert len(folds)==11 and all(f['execution_mode']=='FIT_AND_PREDICT' and 'CONDITIONAL_ON_MEASURED' in f['claim_level'] for f in folds);validate_no_leakage([{'nested_unit_id':r['physical_unit_id'],'physical_unit_id':r['physical_unit_id']} for r in rows],mem)
 assert all({m['physical_unit_id'] for m in mem if m['outer_fold']==f['outer_fold'] and m['role']=='EVALUATION'}==set(f['evaluation_physical_units'].split(';')) for f in folds)
 priv=load_csv(D/'PRIVILEGE_LEDGER.csv');assert {x['model_id'] for x in priv}==ids and all(x['allowed']=='false' for x in priv if x['variable']=='basket_pressure__bar')
 metric=load_json(R/c['metrics'])['L-HYD'];assert metric['seed']==c['seed']==20260902 and metric['target'].startswith('endpoint_100s') and metric['bootstrap_unit']=='condition_then_paired_brew'
 assert 'HYD_B1_PRESSURE_QUADRATIC' in ids and 'HYD_B1_PRESSURE_LINEAR' not in ids;e=next(m for m in specs if m['class']=='E1');assert e['fitted_parameters'][0]['lower']==0 and 'predicted q' in e['ewp_derivation']
 graph=load_json(D/'END_TO_END_OBSERVABILITY_GRAPH.json');edgeids={e['id'] for e in graph['edges']};assert all(x in edgeids for cut in graph['minimal_cut_sets'] for x in cut)
 report=(D/'FREEZE_REPORT.md').read_text();assert 'R3 scientific design is accepted' in report and 'R4' in report
 manifest=load_json(D/'FREEZE_ARTIFACT_MANIFEST.json');assert manifest['revision']=='R4' and not manifest['scoring_executed']
 for x in manifest['artifacts']:assert sha256(R/x['path'])==x['sha256']
 exe=(R/'scripts/sci_md_010_execute.py').read_text();assert "cpath(c,'membership')" in exe and 'basket_pressure__bar' not in exe and '150<=' not in exe and 'RETAIN_AS_MECHANISTIC_CORE' not in exe
 print(f'SCI_MD_010_R4_FREEZE_VALID observations={len(rows)} folds={len(folds)} models={len(specs)}')
def result_validate(path):
 p=Path(path);req=['EXECUTION_STATE.json','RUN_RECEIPT.json','FOLD_RESULTS.csv','BREW_RESULTS.csv','CONDITION_RESULTS.csv','AGGREGATE_RESULTS.csv','PARAMETER_STABILITY.csv','IDENTIFIABILITY_RESULTS.json','PRESSURE_RESPONSE_DIAGNOSTICS.json','UNCERTAINTY_RESULTS.json','MODEL_UTILITY_SCORECARD.csv','LIMITATION_ATTRIBUTION.csv','ARCHITECTURE_DECISIONS.json','EXPERIMENT_NECESSITY_DECISION.json','RESULTS_SUMMARY.md','RESULT.md','summary.json','RESULT_ARTIFACT_MANIFEST.json'];assert all((p/x).is_file() for x in req);c=load_json(D/'EVALUATION_CONTRACT.json');ids=set(c['model_ids']);frozen=load_csv(D/'FOLD_ASSIGNMENTS.csv');folds={x['outer_fold'] for x in frozen};fr=load_csv(p/'FOLD_RESULTS.csv');assert {(x['outer_fold'],x['model_id']) for x in fr}=={(f,m) for f in folds for m in ids}
 br=load_csv(p/'BREW_RESULTS.csv');index={r['physical_unit_id']:r for r in load_csv(D/'ANALYSIS_ROW_INDEX.csv')};membership=load_csv(D/'FOLD_MEMBERSHIP.csv')
 for r in br:
  assert r['model_id'] in ids and r['outer_fold'] in folds and r['physical_unit_id'] in index and r['condition_id']==index[r['physical_unit_id']]['condition_id'];assert any(m['outer_fold']==r['outer_fold'] and m['physical_unit_id']==r['physical_unit_id'] and m['role']=='EVALUATION' for m in membership);err=float(r['predicted_flow_g_s'])-float(r['observed_flow_g_s']);assert abs(err-float(r['error_g_s']))<1e-12 and abs(err*err-float(r['squared_error_g_s2']))<1e-12
 obs_by_unit={}
 for x in br:
  v=float(x['observed_flow_g_s'])
  if x['physical_unit_id'] in obs_by_unit:assert abs(obs_by_unit[x['physical_unit_id']]-v)<1e-12
  obs_by_unit[x['physical_unit_id']]=v
 scales={}
 for r in fr:
  mem=[m for m in membership if m['outer_fold']==r['outer_fold']];train={m['physical_unit_id'] for m in mem if m['role']=='TRAIN'};ev={m['physical_unit_id'] for m in mem if m['role']=='EVALUATION'};assert set(r['training_physical_unit_ids'].split(';'))==train and set(r['evaluation_physical_unit_ids'].split(';'))==ev and int(r['training_brew_count'])==len(train) and int(r['evaluation_brew_count'])==len(ev)
  if r['fit_status']=='PASS':
   cond={}
   for m in mem:
    if m['role']=='TRAIN':cond.setdefault(m['group_id'],[]).append(obs_by_unit[m['physical_unit_id']])
   cm=[sum(v)/len(v) for v in cond.values()];scale=max(cm)-min(cm);assert abs(scale-float(r['training_scale_g_s']))<1e-12
   rr=[x for x in br if x['outer_fold']==r['outer_fold'] and x['model_id']==r['model_id']];physical=math.sqrt(sum(float(x['squared_error_g_s2']) for x in rr)/len(rr));assert abs(physical-float(r['physical_loss_g_s']))<1e-12;assert abs(physical/scale-float(r['normalized_loss']))<1e-12;scales[r['outer_fold']]=scale
 failed=any(r['model_id'] in {'HYD_B1_PRESSURE_QUADRATIC','HYD_E1_LUMPED_DARCY'} and r['fit_status']!='PASS' for r in fr);unc=load_json(p/'UNCERTAINTY_RESULTS.json')
 if not failed:
  recomputed=paired_bootstrap(br,scales);means={f:sum(float(x['line_pressure_bar']) for x in br if x['outer_fold']==f and x['model_id']=='HYD_E1_LUMPED_DARCY')/sum(x['outer_fold']==f and x['model_id']=='HYD_E1_LUMPED_DARCY' for x in br) for f in folds};low=[f for f,v in means.items() if v<=5.25];re_low=paired_bootstrap(br,scales,low);assert abs(recomputed['low']-unc['normalized_delta_ci_low'])<1e-12 and abs(recomputed['high']-unc['normalized_delta_ci_high'])<1e-12 and abs(re_low['low']-unc['low_pressure_normalized_delta_ci_low'])<1e-12 and abs(re_low['high']-unc['low_pressure_normalized_delta_ci_high'])<1e-12
 diag=load_json(p/'PRESSURE_RESPONSE_DIAGNOSTICS.json');d=diag['HYD_E1_LUMPED_DARCY']
 if not failed:
  eb=[x for x in br if x['model_id']=='HYD_E1_LUMPED_DARCY'];groups={}
  for x in eb:groups.setdefault(x['condition_id'],[]).append(x)
  vals=[]
  for g,v in groups.items():vals.append((g,sum(float(x['line_pressure_bar']) for x in v)/len(v),sum(float(x['observed_flow_g_s']) for x in v)/len(v),sum(float(x['predicted_flow_g_s']) for x in v)/len(v)))
  vals.sort(key=lambda x:x[1]);pp=[x[1] for x in vals];oo=[x[2] for x in vals];yy=[x[3] for x in vals]
  def slope(ix,z):
   x=[pp[i] for i in ix];v=[z[i] for i in ix];xm=sum(x)/len(x);vm=sum(v)/len(v);return sum((a-xm)*(b-vm) for a,b in zip(x,v))/sum((a-xm)**2 for a in x)
  lowix=[i for i,x in enumerate(pp) if x<=5.25];hiix=[i for i,x in enumerate(pp) if x>=8.5];pl=slope(lowix,yy);ph=slope(hiix,yy);assert abs(pl-d['predicted_low_slope'])<1e-12 and abs(ph-d['predicted_high_slope'])<1e-12 and d['low_direction_ok']==(pl>0) and d['high_direction_ok']==(ph<=0) and abs(spearman(oo,yy)-d['spearman_tie_average'])<1e-12
 full=None if failed else (unc['normalized_delta_ci_low'],unc['normalized_delta_ci_high']);lowci=None if failed else (unc['low_pressure_normalized_delta_ci_low'],unc['low_pressure_normalized_delta_ci_high']);lane=map_r4_result(failed,d.get('low_direction_ok',False),d.get('high_direction_ok',False),full,lowci);arch=load_json(p/'ARCHITECTURE_DECISIONS.json');assert arch['lane_result']==lane and arch['reduced_E1']==ARCHITECTURE_MAP[lane] and arch['current_full_E2']=='NOT_ADJUDICATED';exp=load_json(p/'EXPERIMENT_NECESSITY_DECISION.json');assert exp['derived_from_architecture']==arch['reduced_E1'] and exp['recommendation']==experiment_from_architecture(arch['reduced_E1']) and not exp['stage_f_authorized'] and not exp['stage_d_authorized']
 state=load_json(p/'EXECUTION_STATE.json');complete=not failed and not state['synthetic'];assert state['scoring_completed']==complete and state['ewp_or_reduced_ewp_scored']==complete
 for x in load_json(p/'RESULT_ARTIFACT_MANIFEST.json')['artifacts']:assert sha256(p/x['path'])==x['sha256']
 print('SCI_MD_010_R4_RESULT_VALID')
def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['freeze','result'],required=True);p.add_argument('--result-dir');a=p.parse_args();freeze_validate() if a.phase=='freeze' else result_validate(a.result_dir)
if __name__=='__main__':main()
