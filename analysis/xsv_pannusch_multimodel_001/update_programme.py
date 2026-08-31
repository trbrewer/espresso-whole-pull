#!/usr/bin/env python3
"""Apply the C1 null result and bounded successor to programme state."""
import csv, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
P=ROOT/'provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json'; L=ROOT/'docs/analysis/data_leverage/DATA_LEVERAGE_LEDGER.csv'
d=json.loads(P.read_text()); d['current_priority']='OBS-PANNUSCH-FRACTION-WINDOW-001'
for x in d['opportunities']:
 if x['opportunity_id']=='XSV-PANNUSCH-MULTIMODEL-001':
  x.update(status='COMPLETE_NULL',current_evidence='XSV_PANNUSCH_MULTIMODEL_001_MODELS_INDISTINGUISHABLE_AT_AVAILABLE_VARIABILITY',completion_evidence=['docs/analysis/xsv_pannusch_multimodel_001/RESULT.md','docs/analysis/xsv_pannusch_multimodel_001/summary.json','docs/analysis/xsv_pannusch_multimodel_001/C1_CORRECTION_RECORD.json','docs/analysis/xsv_pannusch_multimodel_001/BOUNDARY_PRIVILEGE_RESULTS.csv','docs/analysis/xsv_pannusch_multimodel_001/HIERARCHICAL_UNCERTAINTY_RESULTS.csv'],exhausted_for_decision=True,exhaustion_decision='WHETHER_THE_FIXED_PANNUSCH_STRUCTURE_UNIQUELY_OUTPERFORMS_FAIR_PRIVILEGE_MATCHED_EMPIRICAL_MODELS_ON_THE_DECLARED_MARCH_FRACTION_SHARE_COMPARISON',notes='No unique advantage established at available variability; corpus and observer/flow/mapping questions remain unexhausted.')
 if x['opportunity_id']=='SCI-MD-PANNUSCH-SPECIES-001': x.update(status='DEFERRED_BY_HIGHER_PRIORITY',current_evidence='SPECIES_SIGNAL_NOT_SUPPORTED_FOR_ADDED_CONDITION_DEPENDENT_COMPLEXITY',notes='DEFERRED_NO_GROUPED_ADVANTAGE')
 if x['opportunity_id']=='OBS-PANNUSCH-TELEMETRY-001':
  x.update(opportunity_id='OBS-PANNUSCH-FRACTION-WINDOW-001',task_id='OBS-PANNUSCH-FRACTION-WINDOW-001',title='Source-order join qualification and fraction-window observation-operator reconstruction',scientific_question='Can target-independent shot/window/clock/vial reconstruction explain the fraction-2/tail residual?',status='READY',priority=1,prerequisites=['PR #121 C1 corrected result merged after independent exact-head rereview'],current_evidence='24 SOURCE_ORDER_ONLY joins; observation schedule materially changes error',claim_ceiling='SOURCE_INTERNAL_FRACTION_WINDOW_AND_OBSERVATION_OPERATOR_QUALIFICATION',notes='Narrow observer qualification only; no broad telemetry or hydraulic interpretation.')
d['last_completed_opportunity_review']='XSV-PANNUSCH-MULTIMODEL-001-C1'; d['current_claim_ceiling']='SOURCE_INTERNAL_TARGET_EXPOSED_PRIVILEGE_MATCHED_FRACTION_SHARE_COMPARISON'
P.write_text(json.dumps(d,indent=2)+'\n')
with L.open(newline='') as f: rows=list(csv.DictReader(f)); fields=list(rows[0])
for r in rows:
 if r['opportunity_id']=='XSV-PANNUSCH-MULTIMODEL-001': r.update(current_status='COMPLETE_NULL',analysis_completed='C1 privilege-matched grouped comparison',result='No unique Pannusch advantage versus boundary-aware empirical profile',next_action='OBS-PANNUSCH-FRACTION-WINDOW-001',home_lab_consequence='DEFER',exhausted_for_named_decision='true',exhaustion_decision='WHETHER_FIXED_PANNUSCH_UNIQUELY_OUTPERFORMS_FAIR_PRIVILEGE_MATCHED_EMPIRICAL_MODELS',evidence_path='docs/analysis/xsv_pannusch_multimodel_001/RESULT.md')
 if r['opportunity_id']=='OBS-PANNUSCH-TELEMETRY-001': r.update(opportunity_id='OBS-PANNUSCH-FRACTION-WINDOW-001',current_status='READY',active_or_completed_task='OBS-PANNUSCH-FRACTION-WINDOW-001',result='24 SOURCE_ORDER_ONLY joins; no deterministic join',next_action='qualify shot identity, clock, vial transitions, and fraction windows',claim_ceiling='SOURCE_INTERNAL_FRACTION_WINDOW_AND_OBSERVATION_OPERATOR_QUALIFICATION')
with L.open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
