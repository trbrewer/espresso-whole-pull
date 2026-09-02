#!/usr/bin/env python3
import argparse,csv,hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'docs/analysis/sci_md_010'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['freeze','result'],required=True);a=p.parse_args()
 pre=json.load(open(D/'AUTHORITY_AND_DATA_PREFLIGHT.json'));assert pre['stage_f_authorized'] is False and pre['stage_d_authorized'] is False
 assert json.load(open(R/'dependencies/puckworks.lock.json'))==pre['production_puckworks_lock']
 rows=list(csv.DictReader(open(D/'EVIDENCE_UTILITY_REGISTER.csv')));assert rows and all(x['utility_class'] for x in rows)
 folds=list(csv.DictReader(open(D/'FOLD_ASSIGNMENTS.csv')));assert all(x['target_used_for_assignment']=='false' and x['group_id']==x['parent_physical_unit'] for x in folds)
 c=json.load(open(D/'EVALUATION_CONTRACT.json'));assert not c['test_group_calibration'] and not c['per_shot_prediction_calibration']
 for lane in c['selected_lanes']:
  ids={x['model_id'] for x in c['models'] if x['lane_id']==lane};assert {'B0','B1'}<=ids;assert lane in c['metrics'] and c['metrics'][lane]['primary']
 f=json.load(open(D/'PRE_SCORE_FREEZE.json'));assert f['scoring_executed'] is False
 m=json.load(open(D/'FREEZE_ARTIFACT_MANIFEST.json'))
 for x in m['artifacts']:
  assert sha(R/x['path'])==x['sha256'],x['path']
 assert 'fc61c4670ec7bf801e40bb391aab16048b8da26b' in (R/'dependencies/puckworks.lock.json').read_text()
 if a.phase=='result': raise SystemExit('RESULT_PHASE_NOT_AUTHORIZED_OR_EXECUTED')
 print(f'SCI_MD_010_FREEZE_VALID families={len(rows)} folds={len(folds)}')
if __name__=='__main__':main()
