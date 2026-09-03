#!/usr/bin/env python3
import argparse
from pathlib import Path
from sci_md_010_core import *
R=Path(__file__).resolve().parents[1];D=R/'docs/analysis/sci_md_010'
def freeze_validate():
 pw=resolve_puckworks();pre=load_json(D/'PRE_SCORE_FREEZE.json');assert pre['revision']=='R3' and pre['random_seeds']==[20260902] and not pre['scoring_executed'] and not pre['real_target_scores_generated'] and not pre['phase_b_authorized'] and not pre['stage_f_authorized'] and not pre['stage_d_authorized']
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
 metric=load_json(R/c['metrics'])['L-HYD'];assert metric['seed']==c['seed']==20260902 and metric['target'].startswith('endpoint_100s') and 'conditions then brews' in metric['uncertainty']
 assert 'HYD_B1_PRESSURE_QUADRATIC' in ids and 'HYD_B1_PRESSURE_LINEAR' not in ids;e=next(m for m in specs if m['class']=='E1');assert e['fitted_parameters'][0]['lower']==0 and 'predicted q' in e['ewp_derivation']
 graph=load_json(D/'END_TO_END_OBSERVABILITY_GRAPH.json');edgeids={e['id'] for e in graph['edges']};assert all(x in edgeids for cut in graph['minimal_cut_sets'] for x in cut)
 report=(D/'FREEZE_REPORT.md').read_text();assert 'R3' in report and 'R1 executable' not in report and 'flow-derived' in report
 manifest=load_json(D/'FREEZE_ARTIFACT_MANIFEST.json');assert manifest['revision']=='R3' and not manifest['scoring_executed']
 for x in manifest['artifacts']:assert sha256(R/x['path'])==x['sha256']
 exe=(R/'scripts/sci_md_010_execute.py').read_text();assert "cpath(c,'membership')" in exe and 'basket_pressure__bar' not in exe and '150<=' not in exe and 'RETAIN_AS_MECHANISTIC_CORE' not in exe
 print(f'SCI_MD_010_R3_FREEZE_VALID observations={len(rows)} folds={len(folds)} models={len(specs)}')
def result_validate(path):
 p=Path(path);req=['EXECUTION_STATE.json','RUN_RECEIPT.json','FOLD_RESULTS.csv','BREW_RESULTS.csv','CONDITION_RESULTS.csv','AGGREGATE_RESULTS.csv','PARAMETER_STABILITY.csv','IDENTIFIABILITY_RESULTS.json','PRESSURE_RESPONSE_DIAGNOSTICS.json','MODEL_UTILITY_SCORECARD.csv','LIMITATION_ATTRIBUTION.csv','ARCHITECTURE_DECISIONS.json','EXPERIMENT_NECESSITY_DECISION.json','RESULTS_SUMMARY.md','RESULT.md','summary.json','RESULT_ARTIFACT_MANIFEST.json'];assert all((p/x).is_file() for x in req);c=load_json(D/'EVALUATION_CONTRACT.json');ids=set(c['model_ids']);folds={x['outer_fold'] for x in load_csv(D/'FOLD_ASSIGNMENTS.csv')};fr=load_csv(p/'FOLD_RESULTS.csv');assert {x['model_id'] for x in fr}<=ids and {x['outer_fold'] for x in fr}<=folds;state=load_json(p/'EXECUTION_STATE.json');assert state['ewp_or_reduced_ewp_scored'] or state['synthetic'];exp=load_json(p/'EXPERIMENT_NECESSITY_DECISION.json');arch=load_json(p/'ARCHITECTURE_DECISIONS.json');assert exp['derived_from_architecture']==arch['reduced_E1'] and not exp['stage_f_authorized'] and not exp['stage_d_authorized'] and arch['current_full_E2']=='NOT_ADJUDICATED'
 for x in load_json(p/'RESULT_ARTIFACT_MANIFEST.json')['artifacts']:assert sha256(p/x['path'])==x['sha256']
 print('SCI_MD_010_R3_RESULT_VALID')
def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['freeze','result'],required=True);p.add_argument('--result-dir');a=p.parse_args();freeze_validate() if a.phase=='freeze' else result_validate(a.result_dir)
if __name__=='__main__':main()
