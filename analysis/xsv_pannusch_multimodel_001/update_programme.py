#!/usr/bin/env python3
"""Deterministically apply the completed XSV result to the existing programme."""
import csv, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
P=ROOT/'provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json'; L=ROOT/'docs/analysis/data_leverage/DATA_LEVERAGE_LEDGER.csv'
d=json.loads(P.read_text()); d['current_priority']='OBS-PANNUSCH-TELEMETRY-001'
for x in d['opportunities']:
 if x['opportunity_id']=='XSV-PANNUSCH-MULTIMODEL-001':
  x.update(status='COMPLETE_POSITIVE',current_evidence='XSV_PANNUSCH_MULTIMODEL_001_MECHANISTIC_STRUCTURE_HAS_GROUPED_PREDICTIVE_ADVANTAGE',completion_evidence=['docs/analysis/xsv_pannusch_multimodel_001/RESULT.md','docs/analysis/xsv_pannusch_multimodel_001/summary.json','docs/analysis/xsv_pannusch_multimodel_001/MODEL_COMPARISON_RESULTS.csv'],exhausted_for_decision=True,exhaustion_decision='WHICH_CURRENTLY_TESTED_MODEL_STRUCTURE_BEST_PREDICTS_PANNUSCH_FRACTION_SHARE_OBSERVABLES_UNDER_DECLARED_PRIVILEGES',notes='Fixed published Pannusch won the frozen grouped comparison; corpus remains open for residual-selected observer work.')
 if x['opportunity_id']=='OBS-PANNUSCH-TELEMETRY-001': x.update(status='ACTIVE',priority=1,current_evidence='systematic fraction-2 overprediction and tail underprediction with 24 beverage-mass joins',notes='Immediate residual-selected successor; observation operator only, not hydraulic validation.')
d['last_completed_opportunity_review']='XSV-PANNUSCH-MULTIMODEL-001'; d['current_claim_ceiling']='SOURCE_INTERNAL_TARGET_EXPOSED_OBSERVATION_OPERATOR_COMPONENT_EVIDENCE'
P.write_text(json.dumps(d,indent=2)+'\n')
with L.open(newline='') as f: rows=list(csv.DictReader(f)); fields=rows[0].keys()
for r in rows:
 if r['opportunity_id']=='XSV-PANNUSCH-MULTIMODEL-001':
  r.update(current_status='COMPLETE_POSITIVE',analysis_completed='frozen grouped multimodel comparison',result='MODEL-PANNUSCH-FIXED 53.05% lower March RMSE than pooled baseline',next_action='OBS-PANNUSCH-TELEMETRY-001',home_lab_consequence='DEFER',exhausted_for_named_decision='true',exhaustion_decision='WHICH_CURRENTLY_TESTED_MODEL_STRUCTURE_BEST_PREDICTS_PANNUSCH_FRACTION_SHARE_OBSERVABLES_UNDER_DECLARED_PRIVILEGES',evidence_path='docs/analysis/xsv_pannusch_multimodel_001/RESULT.md')
 if r['opportunity_id']=='OBS-PANNUSCH-TELEMETRY-001': r.update(current_status='ACTIVE',next_action='test beverage-mass/fraction-boundary observer against early-tail residual',active_or_completed_task='OBS-PANNUSCH-TELEMETRY-001')
with L.open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
