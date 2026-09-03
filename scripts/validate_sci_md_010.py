#!/usr/bin/env python3
import argparse
from pathlib import Path
from sci_md_010_core import *
R=Path(__file__).resolve().parents[1];D=R/'docs/analysis/sci_md_010'
def freeze_validate():
 pw=resolve_puckworks();pre=load_json(D/'PRE_SCORE_FREEZE.json');assert pre['revision']=='R2' and not pre['scoring_executed'] and not pre['real_target_scores_generated'] and pre['adjudicative_lane_count']>=1 and pre['executable_ewp_or_reduced_ewp_lane_count']>=1 and not pre['phase_b_authorized'] and not pre['stage_f_authorized'] and not pre['stage_d_authorized']
 gate=load_json(D/'EWP_EXECUTABILITY_GATE.json');assert any(x['executable'] and (x['e1_executable'] or x['e2_executable']) and x['actual_observation_artifact'] for x in gate['lanes'])
 reg=load_json(D/'INPUT_ARTIFACT_REGISTER.json');validate_artifacts(R,reg,pw);obs=next(x for x in reg['artifacts'] if x['artifact_id']=='WASZ_OBSERVATIONS');assert obs['artifact_class']=='PROCESSED_OBSERVATION'
 contract=load_json(D/'EVALUATION_CONTRACT.json');specs=load_json(R/contract['models'])['models'];ids={m['model_id'] for m in specs};assert set(contract['model_ids'])==ids and any(m['class'] in {'E1','E2'} and m['actual_execution_mode'] in {'FIT_AND_PREDICT','FIXED_PREDICT'} for m in specs)
 for m in specs:
  assert sha256(R/m['implementation_file'])==m['implementation_sha256']
  for name in m['callable'].split(','):assert name in MODEL_CALLABLES
  if m['class']=='E1':assert m['ewp_derivation'] and 'espresso_reference_math.py' in m['ewp_derivation']
 rows=load_csv(R/contract['row_index']);assert rows and all(not r['target_field'].endswith('PRIOR_SCORE_ONLY') for r in rows);folds=load_csv(R/contract['folds']);assert len(folds)==11
 units={r['physical_unit_id'] for r in rows};assert all(u in units for f in folds for u in f['evaluation_physical_units'].split(';'))
 priv=load_csv(D/'PRIVILEGE_LEDGER.csv');assert {x['model_id'] for x in priv}==ids and not any(x['derived_from_target']=='true' and x['variable']=='basket_pressure__bar' for x in priv)
 metric=load_json(R/contract['metrics'])['L-HYD'];assert metric['implementation'].endswith('rmse and contract executor aggregation') and 'training' in metric['normalization']
 graph=load_json(D/'END_TO_END_OBSERVABILITY_GRAPH.json');assert [e['id'] for e in graph['edges']]==['pressure_darcy','training_C','darcy_observer','psd_K','K_cup']
 manifest=load_json(D/'FREEZE_ARTIFACT_MANIFEST.json');assert manifest['revision']=='R2' and not manifest['scoring_executed']
 for x in manifest['artifacts']:assert sha256(R/x['path'])==x['sha256']
 assert 'real_execute' not in (R/'scripts/sci_md_010_execute.py').read_text();assert 'run_contract' in (R/'scripts/sci_md_010_execute.py').read_text()
 print(f'SCI_MD_010_R2_FREEZE_VALID observations={len(rows)} folds={len(folds)} models={len(specs)}')
def result_validate(path):
 p=Path(path);req=['EXECUTION_STATE.json','RUN_RECEIPT.json','FOLD_RESULTS.csv','AGGREGATE_RESULTS.csv','MODEL_UTILITY_SCORECARD.csv','ARCHITECTURE_DECISIONS.json','EXPERIMENT_NECESSITY_DECISION.json','summary.json','RESULT_ARTIFACT_MANIFEST.json'];assert all((p/x).is_file() for x in req);contract=load_json(D/'EVALUATION_CONTRACT.json');ids=set(contract['model_ids']);folds={x['group_id'] for x in load_csv(D/'FOLD_ASSIGNMENTS.csv')}
 fr=load_csv(p/'FOLD_RESULTS.csv');assert {x['model_id'] for x in fr}<=ids and {x['group_id'] for x in fr}<=folds;state=load_json(p/'EXECUTION_STATE.json');assert state['ewp_or_reduced_ewp_scored'] or state['synthetic'];exp=load_json(p/'EXPERIMENT_NECESSITY_DECISION.json');assert not exp['stage_f_authorized'] and not exp['stage_d_authorized']
 for x in load_json(p/'RESULT_ARTIFACT_MANIFEST.json')['artifacts']:assert sha256(p/x['path'])==x['sha256']
 print('SCI_MD_010_R2_RESULT_VALID')
def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['freeze','result'],required=True);p.add_argument('--result-dir');a=p.parse_args();freeze_validate() if a.phase=='freeze' else result_validate(a.result_dir)
if __name__=='__main__':main()
