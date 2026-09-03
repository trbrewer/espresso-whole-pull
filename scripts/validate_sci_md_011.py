#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
from sci_md_011_core import *
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/analysis/sci_md_011'
def freeze():
 f=load_json(D/'PRE_SCORE_FREEZE.json');assert f['task_id']==TASK and not f['scoring_executed'] and not f['phase_b_authorized'];assert tuple(f['selected_models'])==MODELS
 m=load_json(D/'FREEZE_ARTIFACT_MANIFEST.json')
 for a in m['artifacts']:assert sha256(ROOT/a['path'])==a['sha256'],a['path']
 h=load_json(D/'SCI_MD_010_HANDOFF.json')
 for a in h['artifacts']:assert sha256(ROOT/a['path'])==a['sha256'],a['path']
 assert load_json(ROOT/'dependencies/puckworks.lock.json')['checkout_commit']=='fc61c4670ec7bf801e40bb391aab16048b8da26b'
 return len(m['artifacts'])
def result(d):
 m=load_json(d/'RESULT_ARTIFACT_MANIFEST.json')
 for a in m['artifacts']:assert sha256(d/a['path'])==a['sha256'],a['path']
 br=load_csv(d/'BREW_RESULTS.csv');fr=load_csv(d/'FOLD_RESULTS.csv')
 for r in fr:
  rows=[x for x in br if x['outer_fold']==r['outer_fold'] and x['model_id']==r['model_id']];rm=math.sqrt(sum(float(x['squared_error_g_s2']) for x in rows)/len(rows));assert abs(rm-float(r['rmse_g_s']))<1e-12
 s=load_json(d/'summary.json');assert not s['current_full_ewp_validated'] and not s['stage_f_authorized'] and not s['stage_d_authorized']
 return len(br)
def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['freeze','result'],required=True);p.add_argument('--result-dir',type=Path);a=p.parse_args();n=freeze();
 if a.phase=='result':n+=result(a.result_dir)
 print(json.dumps({'task_id':TASK,'phase':a.phase,'validated_items':n,'status':'PASS'}))
if __name__=='__main__':main()
