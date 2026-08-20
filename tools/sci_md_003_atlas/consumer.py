from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'docs/analysis/sci_md_003'
EXPECTED_SCHEMA='puckworks.response-atlas-export/v1'
EXPECTED_HASH='434c8bd208474bd4fe33281cc6f633ee8ac4e47ffefae9039a4014cba7ad2420'
EXPECTED_COMMIT='2cb75c1fdd8aae34abad66e8fb1d42b0630fdaad'; EXPECTED_TREE='66fa1f25a9302c8e4be7dba35e8b9d99f527bd78'

def _bytes(o): return (json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
def _write(name,o): p=OUT/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(_bytes(o))
def _sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _load(rel): return json.loads((ROOT/rel).read_text())

def load_atlas(path, expected_hash=EXPECTED_HASH):
    if _sha(path)!=expected_hash: raise ValueError('PUCKWORKS_ARTIFACT_HASH_MISMATCH')
    a=json.loads(Path(path).read_text())
    if a.get('schema_version')!=EXPECTED_SCHEMA: raise ValueError('PUCKWORKS_SCHEMA_VERSION_MISMATCH')
    m=a['manifest']
    if (m['execution_code_commit'],m['execution_code_tree'])!=(EXPECTED_COMMIT,EXPECTED_TREE): raise ValueError('PUCKWORKS_IDENTITY_MISMATCH')
    return a

def retained_export():
    wp=_load('validation/wp03/WP03_002_CORRECTED_COMPARISON.json')
    vc=_load('validation/cases/val_case_001/VAL_CASE_001_RESULTS.json')
    b2=_load('validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_RESULT.json')
    rows=[]
    for case in wp['corrected_compaction']:
      e=case['endpoint']; rows.extend([
       {'case_id':case['id'],'source_artifact':'validation/wp03/WP03_002_CORRECTED_COMPARISON.json','source_field':'corrected_compaction[].endpoint.model_pressure_bar','observable':'basket_pressure','value':e['model_pressure_bar'],'unit':'bar','node':'BASKET','reference_basis':'GAUGE','time_origin':'solver_time=source_time+3s','adapter':'NONE','uncertainty':'NOT_PROVIDED','support_status':'SUPPORTED','evidence_class':'RETAINED_POST_OBSERVATION_MODEL_OUTPUT'},
       {'case_id':case['id'],'source_artifact':'validation/wp03/WP03_002_CORRECTED_COMPARISON.json','source_field':'corrected_compaction[].endpoint.model_flow_g_s','observable':'mass_flow_rate','value':e['model_flow_g_s'],'unit':'g/s','node':'BED_OUTLET','reference_basis':'beverage mass flow','time_origin':'solver_time=source_time+3s','adapter':'NONE','uncertainty':'NOT_PROVIDED','support_status':'SUPPORTED','evidence_class':'RETAINED_POST_OBSERVATION_MODEL_OUTPUT'},
       {'case_id':case['id'],'source_artifact':'validation/wp03/WP03_002_CORRECTED_COMPARISON.json','source_field':'corrected_compaction[].endpoint.model_mass_g','observable':'cumulative_delivered_mass','value':e['model_mass_g'],'unit':'g','node':'BED_OUTLET','reference_basis':'beverage mass','time_origin':'solver_time=source_time+3s','adapter':'NONE','uncertainty':'NOT_PROVIDED','support_status':'SUPPORTED','evidence_class':'RETAINED_POST_OBSERVATION_MODEL_OUTPUT'}])
    for ch in ['upstream_pressure','bed_pressure_drop','first_drip_timing','effective_resistance','permeability','porosity','bed_height_or_deformation','cup_tds','extraction_yield','spatial_flow_variance','local_extraction']:
      rows.append({'case_id':'RETAINED_SET','source_artifact':'retained artifact audit','source_field':'NOT_RETAINED_IN_SELECTED_COMPACT_ENDPOINTS','observable':ch,'value':None,'unit':'NOT_PROVIDED','node':'NOT_PROVIDED','reference_basis':'NOT_PROVIDED','time_origin':'NOT_PROVIDED','adapter':'NONE','uncertainty':'NOT_PROVIDED','support_status':'UNSUPPORTED_RELATIONSHIP','evidence_class':'NOT_AVAILABLE'})
    return {'schema_version':'ewp.sci-md-003-observable-export/v1','excluded_families':['SCI-LC-001A'],
      'retained_sources':{'wp03_002':{'sha256':_sha(ROOT/'validation/wp03/WP03_002_CORRECTED_COMPARISON.json'),'pressure_flow_ordering':wp['ordering']},'val_case_001':{'sha256':_sha(ROOT/'validation/cases/val_case_001/VAL_CASE_001_RESULTS.json'),'case_id':vc['case_id'],'scientific_disposition':vc['scientific_result_disposition']},'val_corpus_002':{'sha256':_sha(ROOT/'validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_RESULT.json'),'status':b2['status'],'production_counts':b2['production_counts'],'scientific_disposition':b2['scientific_result_disposition']}},'observables':sorted(rows,key=lambda r:(r['case_id'],r['observable']))}

def consume(atlas_path):
    atlas=load_atlas(atlas_path); ewp=retained_export()
    cross=[{'comparison_id':'EWP_WP03_PRESSURE_ORDERING_VS_PUCKWORKS_STATIC_HYDRAULICS','puckworks_component':'wadsworth2026.inertial','ewp_source':'WP03-002 corrected compaction','observable':'flow response to pressure','comparability_level':3,'numeric_residual':None,'disagreement_category':'SEMANTIC_OR_NONCOMPARABLE','reason':'EWP retained mass flow from dynamic compacting bed versus static superficial Darcy velocity; model ordering is decreasing while Puckworks lens is increasing, but bases/interventions are not level 1/2'},
      {'comparison_id':'EWP_WP03_MACHINE_VS_FOSTER_NULL','puckworks_component':'foster2025.machine_mode','ewp_source':'WP03-002 corrected compaction','observable':'machine pressure/flow/timing','comparability_level':3,'numeric_residual':None,'disagreement_category':'UNSUPPORTED_COMPARISON','reason':'selected EWP compact endpoint lacks synchronized upstream/headspace timing and first-drip observables needed for null survival gates'},
      {'comparison_id':'EWP_EXTRACTION_VS_CAMERON','puckworks_component':'cameron2020.extraction_bdf','ewp_source':'VAL-CORPUS-002','observable':'extraction response','comparability_level':4,'numeric_residual':None,'disagreement_category':'SEMANTIC_OR_NONCOMPARABLE','reason':'selected retained aggregate source/model contrasts do not expose a matching cup-basis endpoint under the frozen Cameron cases'}]
    mv={'records':atlas['measurement_value_records']['records'],'ewp_effect':'selected retained endpoints add basket pressure, flow, and delivered mass but no declared measurement uncertainty and no level-1/2 complete pair coverage','minimum_measurement_sets':'NO_COMPLETE_MEASUREMENT_SET'}
    decision={'selected_outcome':'SCI_MD_003_RP_A_001_ADDITIONAL_DATA_REQUIRED','physical_validation':'NOT_ESTABLISHED','current_gate':'ADDITIONAL_INDEPENDENT_DATA_REQUIRED','reasons':['fixed-bed apparatus null cannot be adjudicated against selected retained EWP endpoints','cross-repository comparisons are levels 3 and 4','required synchronized upstream/basket pressure, timing, deformation, spatial, and uncertainty fields are absent','NO_COMPLETE_MEASUREMENT_SET'],'not_selected':{'APPARATUS_OBSERVATION_EXPLANATION_SURVIVES':'applicable null gates incomplete','DYNAMIC_BED_SIGNATURE_DISTINGUISHABLE':'no robust unique level-1/2 deformation route','SPATIAL_LOCALIZATION_ONLY_DISTINGUISHABLE_ROUTE':'no retained supported spatial comparator'}}
    _write('ewp_observable_export.json',ewp); _write('cross_repository_comparison.json',cross); _write('measurement_value_consumer.json',mv); _write('DECISION.json',decision)
    return decision

def main():
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['run','verify']); p.add_argument('--atlas',required=True); a=p.parse_args()
    before={n:(OUT/n).read_bytes() for n in ['ewp_observable_export.json','cross_repository_comparison.json','measurement_value_consumer.json','DECISION.json'] if (OUT/n).exists()}
    consume(a.atlas)
    if a.command=='verify' and before and any((OUT/n).read_bytes()!=b for n,b in before.items()): raise SystemExit('DETERMINISTIC_EXPORT_DRIFT')
    print('SCI_MD_003_'+a.command.upper()+'_OK')
if __name__=='__main__': main()
