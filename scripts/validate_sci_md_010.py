#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from sci_md_010_core import *
R=Path(__file__).resolve().parents[1];D=R/'docs/analysis/sci_md_010';PLACE=re.compile(r'^(brew|condition)_\d+$')
def freeze_validate():
 pw=resolve_puckworks();pre=load_json(D/'PRE_SCORE_FREEZE.json');assert not pre['scoring_executed'] and not pre['review_receipt_embedded'] and pre['review_required'];assert not pre['stage_f_authorized'] and not pre['stage_d_authorized']
 assert (git(pw,'rev-parse','HEAD'),git(pw,'rev-parse','HEAD^{tree}'))==(pre['puckworks_analysis']['commit'],pre['puckworks_analysis']['tree']);assert load_json(R/'dependencies/puckworks.lock.json')==pre['production_puckworks_lock']
 validate_artifacts(R,load_json(D/'INPUT_ARTIFACT_REGISTER.json'),pw);rows=load_csv(D/'ANALYSIS_ROW_INDEX.csv');folds=load_csv(D/'FOLD_ASSIGNMENTS.csv');mem=load_csv(D/'FOLD_MEMBERSHIP.csv');validate_no_leakage(rows,mem);units={x['physical_unit_id'] for x in rows};seen={}
 for f in folds:
  assert not PLACE.match(f['group_id']) and int(f['source_row_count'])>0
  for u in f['evaluation_physical_units'].split(';'):assert u in units;seen[(f['lane_id'],u)]=seen.get((f['lane_id'],u),0)+1
 assert all(v==1 for v in seen.values())
 specs=load_json(D/'MODEL_SPECIFICATIONS.json')['models'];assert len(specs)==9
 for m in specs:
  assert sha256(R/m['implementation_file'])==m['implementation_sha256']
  if m['callable'] not in {'EXACT_REUSE_ONLY','UNAVAILABLE'}:assert all(n in MODEL_CALLABLES for n in m['callable'].split(','))
  for p in m['fitted_parameters']:assert {'name','unit','transform','lower','upper','bound_provenance'}<=set(p)
 assert all(not(m['class']=='E2' and 'PANNUSCH_FIXED' in m['model_id']) for m in specs)
 lanes=load_json(D/'BENCHMARK_LANE_SELECTION.json');assert len(lanes['aggregate_candidate_audit'])>=8 and len(lanes['nonpredictive_sublanes'])==3
 ev=load_csv(D/'EVIDENCE_UTILITY_REGISTER.csv');assert len(ev)==47 and all(x['utility_rationale'] and x['exact_dataset_ids'] for x in ev);assert any(x['direct_parameter_transfer_possible']=='false' and x['utility_class']=='NO_CURRENT_DECISION_RELEVANT_USE' for x in ev);assert len({x['utility_class'] for x in ev})>2
 for x in load_csv(D/'PRIVILEGE_LEDGER.csv'):enforce_privilege(x)
 metrics=load_json(D/'METRIC_CONTRACT.json');assert all('formula' in metrics[x] and 'normalization' in metrics[x] for x in ['L-HYD','L-FRAC'])
 assert not any(x['structural_identifiability_status']=='STRUCTURALLY_NONIDENTIFIABLE' for x in load_csv(D/'EWP_INPUT_OBSERVABILITY_REGISTER.csv'))
 manifest=load_json(D/'FREEZE_ARTIFACT_MANIFEST.json');assert not manifest['scoring_executed'] and canonical_sha(manifest['artifacts'])==manifest['aggregate_content_sha256']
 for x in manifest['artifacts']:assert sha256(R/x['path'])==x['sha256'],x['path']
 code='\n'.join((R/x).read_text(errors='ignore') for x in ['scripts/sci_md_010_core.py','scripts/sci_md_010_prepare.py','scripts/sci_md_010_execute.py','scripts/validate_sci_md_010.py','tests/test_sci_md_010.py']);assert ('/'+'home'+'/') not in code;assert 'real_execute' in (R/'scripts/sci_md_010_execute.py').read_text()
 print(f'SCI_MD_010_R1_FREEZE_VALID families={len(ev)} rows={len(rows)} folds={len(folds)} models={len(specs)}')
def result_validate(path):
 p=Path(path)
 if not p.exists():print('SCI_MD_010_RESULT_NOT_EXECUTED');return
 req=['EXECUTION_STATE.json','RUN_RECEIPT.json','FOLD_RESULTS.csv','AGGREGATE_RESULTS.csv','MODEL_UTILITY_SCORECARD.csv','ARCHITECTURE_DECISIONS.json','EXPERIMENT_NECESSITY_DECISION.json','summary.json','RESULT_ARTIFACT_MANIFEST.json'];assert all((p/x).is_file() for x in req);assert load_json(p/'EXECUTION_STATE.json')['scoring_executed'];exp=load_json(p/'EXPERIMENT_NECESSITY_DECISION.json');assert not exp['stage_f_authorized'] and not exp['stage_d_authorized']
 for x in load_json(p/'RESULT_ARTIFACT_MANIFEST.json')['artifacts']:assert sha256(p/x['path'])==x['sha256']
 print('SCI_MD_010_RESULT_VALID')
def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['freeze','result'],required=True);p.add_argument('--result-dir');a=p.parse_args();freeze_validate() if a.phase=='freeze' else result_validate(a.result_dir or D/'result_not_executed')
if __name__=='__main__':main()
