#!/usr/bin/env python3
"""Production semantic validator for the current Waszkiewicz result package."""
import argparse,csv,json,sys
from pathlib import Path

class Invalid(Exception):
    def __init__(self,code,detail): self.code=code; super().__init__(detail)
def require(ok,code,detail):
    if not ok: raise Invalid(code,detail)
def validate(root: Path):
    d=root/'docs/analysis/xsv_waszkiewicz_dynamic_hyd_001'
    p=json.loads((d/'PROCESSING_ROBUSTNESS.json').read_text()); s=json.loads((d/'summary.json').read_text()); a=json.loads((d/'C1_REVIEW_MANDATED_METHODS_ADDENDUM.json').read_text()); parity=json.loads((d/'SOURCE_MODEL_PARITY.json').read_text())
    obsolete={'ranking_stable','processing_robustness','broader_processing_scope'}
    require(not obsolete.intersection(p),'XSV_PROCESSING_OBSOLETE_FIELD','obsolete current processing field')
    required={'schema_version':2,'tested_processing_window_count':5,'mean_loco_ranking_across_tested_windows':'STABLE','mean_loco_winner_across_tested_windows':'W-H2','W_H2_first_in_every_tested_window':True,'adoption_decision_across_tested_windows':'STABLE_NO_EVOLVING_MODEL_PASSES','all_tested_windows_reject_evolving_model_adoption':True,'effect_magnitude_across_tested_windows':'VARIABLE','condition_sign_pattern_across_tested_windows':'VARIABLE','parameter_stability':'VARIABLE','coverage_stability':'STABLE','broader_processing_robustness':'NOT_ESTABLISHED_BEYOND_TESTED_CONFIGURATIONS','processing_disposition':'ADOPTION_DECISION_ROBUST_WITHIN_TESTED_PROCESSING_WINDOWS'}
    require(all(p.get(k)==v for k,v in required.items()),'XSV_PROCESSING_ENUM_INCONSISTENT','processing enum/value mismatch')
    with (d/'PROCESSING_SENSITIVITY.csv').open() as stream: rows=list(csv.DictReader(stream))
    ids=sorted({r['configuration_id'] for r in rows})
    require(len(ids)==5 and sorted(p.get('tested_processing_window_ids',[]))==ids,'XSV_PROCESSING_WINDOW_SET_MISMATCH','declared and CSV window IDs differ')
    for wid in ids:
        wr=[r for r in rows if r['configuration_id']==wid]
        require(all(r['coverage']!='' and r['failure_rate']!='' for r in wr),'XSV_PROCESSING_COVERAGE_INCOMPLETE',wid)
        winner=min(wr,key=lambda r:float(r['LOCO']))['model']; require(winner=='W-H2','XSV_PROCESSING_WINNER_MISMATCH',wid)
        require(all(r['adoption_gate']=='FAIL' for r in wr if r['model']!='W-H0A'),'XSV_PROCESSING_ADOPTION_MISMATCH',wid)
    require(a.get('bootstrap',{}).get('time_rows_resampled') is False,'XSV_BOOTSTRAP_TIME_ROW_INDEPENDENCE_FORBIDDEN','time rows must not be resampled independently')
    scope=s.get('scope',{}); require(not any(scope.get(k) is True for k in ('all_time_dependence_ruled_out','all_mass_progress_dependence_ruled_out','all_change_point_dependence_ruled_out')),'XSV_BROAD_DYNAMIC_ABSENCE_CLAIM_FORBIDDEN','broad dynamic absence claim')
    require(parity.get('privilege')=='SOURCE_POST_FIT_RECONSTRUCTION' and parity.get('grouped_predictive_support')=='NOT_EVALUATED_AS_EQUAL_PRIVILEGE' and s.get('source_model',{}).get('classification')=='SOURCE_POST_FIT_RECONSTRUCTION' and s.get('source_model',{}).get('grouped_predictive_validation') is False,'XSV_SOURCE_MODEL_GROUPED_PREDICTION_RELABEL_FORBIDDEN','source model relabeled as grouped prediction')
    return {'status':'PASS','tested_processing_windows':ids}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));a=p.parse_args()
    try: print(json.dumps(validate(a.root.resolve()),indent=2))
    except Invalid as e: print(json.dumps({'status':'FAIL','error_code':e.code,'detail':str(e)},indent=2));raise SystemExit(1)
if __name__=='__main__': main()
