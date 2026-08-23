"""Validated, response-derived SCI-MD-003 C1 thin consumer."""
from __future__ import annotations
import argparse, hashlib, itertools, json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'docs/analysis/sci_md_003/c1'
EXPECTED_SCHEMA='puckworks.response-atlas-export/v5'
EXPECTED_HASH='3f55615114e5938a443506107af8f93f51156e0f3682750608dead1a4f006b1e'
EXPECTED_COMMIT='fd9b0dd5b8e7bcdc057e4bd01c69954346631f15'; EXPECTED_TREE='d0bb07722997e189c7489b4c50959a84e123be2f'
EXPECTED_MERGE_COMMIT='378e4c8c094bce3599eeadbcb237464d738596e7'
EXPECTED_PROTOCOL='8bf4b9d6c5d3fd2f2fb077f98a16e2175356ebc6a975ea640c25e810a710cb37'
EXPECTED_CASE='7537675bd469e515724d1fe61535c8047bf5d05a0f71165978b02c5481f6c519'
EXPECTED_ASSUMPTIONS='17f37c2ccbb39bca86f44d3bbc004085c40b6318ca6d101869fa6dfd3d5aac4a'
EXPECTED_SPEC='a3064d18f026bef7b54e70f825febfd7b8bb01fe5bdbaff1477435030c8b678f'
EXPECTED_REGISTRY='a8e336c00982f05e3312483d2d67f894b7485995069af936b084341b9ce8e114'
EXPECTED_DECISION_INPUT='11efe65820894e8bf3768c3c4e4a43c922f05139a06d4a26617cf621167df6b7'
EXPECTED_COMPONENTS=['foster2025.machine_mode','wadsworth2026.inertial','cameron2020.extraction_bdf']
EXPECTED_CARDS={'cameron2020.md':'3d0eb1f7e6b18a5aebf2c17eab75b990f5d167aef1a5fb6129ab402f21f3f22b','foster2025_2.md':'b907b002ddb81560dd6e3d514b8cfa31bb1b2820a397195d27aa865036976b4b','wadsworth2026.md':'606abfce68ba40105b4650ee6af2e8c716c60adb2653b87065b5fd2207c25fe8','wadsworth2026_grindmap.md':'8cffbac5fe9f42072fb880be8b9e972870c847386eacd0ed2091d6f3dd1c34d4','wadsworth2026_inertial.md':'799b7dc68df3dc5602e7831db08482405c4c40cfccf24dfb81e69676f7a4c888'}
SUPPORT={'SUPPORTED','UNSUPPORTED_RELATIONSHIP','UNSUPPORTED_FOR_CASE','OUTSIDE_VALID_RANGE','MISSING_REQUIRED_INPUT','NUMERICAL_FAILURE','NOT_EVALUATED'}

def pretty(x:Any)->bytes:return (json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
def canonical(x:Any)->bytes:return (json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def _load(rel:str)->Any:return json.loads((ROOT/rel).read_text())
def _write(name:str,x:Any)->None:
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(pretty(x))

def validate_atlas(a:dict[str,Any])->dict[str,Any]:
 if a.get('schema_version')!=EXPECTED_SCHEMA:raise ValueError('PUCKWORKS_SCHEMA_VERSION_MISMATCH')
 m=a.get('run_manifest',{})
 for k,v in {'execution_code_commit':EXPECTED_COMMIT,'execution_code_tree':EXPECTED_TREE,'protocol_sha256':EXPECTED_PROTOCOL,'case_matrix_sha256':EXPECTED_CASE,'measurement_assumption_sha256':EXPECTED_ASSUMPTIONS,'component_response_atlas_spec_sha256':EXPECTED_SPEC,'registry_snapshot_sha256':EXPECTED_REGISTRY,'selected_components':EXPECTED_COMPONENTS,'selected_card_sha256':EXPECTED_CARDS}.items():
  if m.get(k)!=v:raise ValueError(f'PUCKWORKS_{k.upper()}_MISMATCH')
 counts=a.get('summary_counts',{}); eligibility=a.get('channel_eligibility',[]); actual={'explanations':len(a.get('explanations',[])),'channel_eligibility':len(eligibility),'eligible_records':sum(x.get('eligibility')=='eligible' for x in eligibility),'measurement_records':len(a.get('measurement_value_records',[])),'result_cells':len(a.get('result_cells',[]))}
 if any(counts.get(k)!=v for k,v in actual.items()):raise ValueError('PUCKWORKS_SUMMARY_COUNTS_MISMATCH')
 if a.get('matched_comparisons')!=eligibility:raise ValueError('PUCKWORKS_AUTHORIZED_COMPARISON_UNIVERSE_MISMATCH')
 for c in a.get('result_cells',[]):
  if c.get('support_status') not in SUPPORT:raise ValueError('UNKNOWN_SUPPORT_STATE')
  if c['support_status']!='SUPPORTED' and c.get('value') is not None:raise ValueError('UNSUPPORTED_NUMERIC_CELL')
 decision=a.get('decision',{}); apparatus=a.get('apparatus_evaluation',{})
 if decision.get('decision_input_hash')!=EXPECTED_DECISION_INPUT or decision.get('selected_outcome')!='SCI_MD_003_RP_A_001_ADDITIONAL_DATA_REQUIRED':raise ValueError('PUCKWORKS_DECISION_AUTHORITY_MISMATCH')
 if decision.get('physical_validation')!='NOT_ESTABLISHED' or decision.get('minimum_measurement_sets')!='NO_COMPLETE_MEASUREMENT_SET' or decision.get('eligible_pair_count')!=0:raise ValueError('PUCKWORKS_DECISION_SEMANTICS_MISMATCH')
 if apparatus.get('status')!='NOT_EVALUATED' or a.get('apparatus_gate_evidence') or a.get('apparatus_gate_results'):raise ValueError('PUCKWORKS_APPARATUS_STATE_MISMATCH')
 return a

def load_atlas(path:Path,expected_hash:str=EXPECTED_HASH)->dict[str,Any]:
 if sha256(path)!=expected_hash:raise ValueError('PUCKWORKS_ARTIFACT_HASH_MISMATCH')
 return validate_atlas(json.loads(path.read_text()))

def retained_export()->dict[str,Any]:
 wp=_load('validation/wp03/WP03_002_CORRECTED_COMPARISON.json');vc=_load('validation/cases/val_case_001/VAL_CASE_001_RESULTS.json');b2=_load('validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_RESULT.json');rows=[]
 for case in wp['corrected_compaction']:
  e=case['endpoint']
  for obs,field,unit,node,basis in [('basket_pressure','model_pressure_bar','bar','BASKET','GAUGE'),('flow','model_flow_g_s','g/s','BED_OUTLET','BEVERAGE_MASS_FLOW'),('delivered_mass','model_mass_g','g','BED_OUTLET','BEVERAGE_MASS')]:
   rows.append({'case_id':case['id'],'source_artifact':'validation/wp03/WP03_002_CORRECTED_COMPARISON.json','source_field':f'corrected_compaction[].endpoint.{field}','observable':obs,'value':e[field],'unit':unit,'node':node,'reference_basis':basis,'time_basis':'solver_time=source_time+3s; endpoint','uncertainty':'NOT_PROVIDED','support_status':'SUPPORTED','evidence_class':'RETAINED_POST_OBSERVATION_MODEL_OUTPUT'})
 available={r['observable'] for r in rows}
 for ch in ['basket_pressure','separate_upstream_pressure','flow','delivered_mass','bed_height_or_deformation','first_drip_timing','temperature','turbidity_or_downstream_suspended_solids','retained_fines_mass','spatial_flow_variance','local_extraction']:
  if ch not in available:rows.append({'case_id':'RETAINED_SET','source_artifact':'retained artifact audit','source_field':'NOT_RETAINED_IN_SELECTED_COMPACT_ENDPOINTS','observable':ch,'value':None,'unit':'NOT_PROVIDED','node':'NOT_PROVIDED','reference_basis':'NOT_PROVIDED','time_basis':'NOT_PROVIDED','uncertainty':'NOT_PROVIDED','support_status':'UNSUPPORTED_RELATIONSHIP','evidence_class':'NOT_AVAILABLE'})
 return {'schema_version':'ewp.sci-md-003-observable-export/c1','excluded_families':['SCI-LC-001A'],'retained_sources':{'wp03_002':{'sha256':sha256(ROOT/'validation/wp03/WP03_002_CORRECTED_COMPARISON.json'),'pressure_flow_ordering':wp['ordering']},'val_case_001':{'sha256':sha256(ROOT/'validation/cases/val_case_001/VAL_CASE_001_RESULTS.json'),'case_id':vc['case_id'],'scientific_disposition':vc['scientific_result_disposition']},'val_corpus_002':{'sha256':sha256(ROOT/'validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_RESULT.json'),'status':b2['status'],'production_counts':b2['production_counts'],'scientific_disposition':b2['scientific_result_disposition']}},'observables':sorted(rows,key=lambda r:(r['case_id'],r['observable']))}

@dataclass(frozen=True)
class Pair:
 pair_id:str;puckworks_explanation:str;ewp_explanation:str;scenario:str;channel:str;comparability_level:int;pair_role:str;eligibility:str;reason_code:str;uncertainty_available:bool
 def __post_init__(self):
  if self.comparability_level not in range(1,6):raise ValueError('BAD_COMPARABILITY_LEVEL')
  if self.eligibility=='eligible' and (self.comparability_level>2 or self.pair_role not in {'SCIENTIFICALLY_COMPETING','NESTED_LIMIT'}):raise ValueError('INELIGIBLE_PAIR_MARKED_ELIGIBLE')

def derive_pairs(a:dict[str,Any],e:dict[str,Any])->list[Pair]:
 wads=any(c.get('component_id')=='wadsworth2026.inertial' and c.get('adjudicative') is True for c in a['result_cells'])
 pairs=[Pair('EWP_FOSTER_MACHINE','FOSTER_FIXED_BED_MACHINE_NULL','EWP_WP03_DYNAMIC_BED','MACHINE_REF','flow',3,'SCIENTIFICALLY_COMPETING','ineligible','MACHINE_PARAMETERS_AND_TIME_HISTORY_NOT_MATCHED',False),Pair('EWP_WADSWORTH_FLOW','WADSWORTH_STATIC_INERTIAL_LENS','EWP_WP03_DYNAMIC_BED','P09_REF','flow',4,'SCIENTIFICALLY_COMPETING','ineligible','BED_DROP_STATIC_VELOCITY_VS_BASKET_DYNAMIC_MASS_FLOW',False),Pair('EWP_CAMERON_EXTRACTION','CAMERON_EXTRACTION_OBSERVER','EWP_RETAINED_EXTRACTION','P09_REF','local_extraction',4,'OBSERVATION_OPERATOR_COMPARISON','ineligible','NO_MATCHED_CUP_BASIS_ENDPOINT',False)]
 if wads:pairs.append(Pair('EWP_WADSWORTH_ADJUDICATIVE','WADSWORTH_STATIC_INERTIAL_LENS','EWP_WP03_DYNAMIC_BED','P09_REF','flow',2,'SCIENTIFICALLY_COMPETING','unresolved','UNCERTAINTY_NOT_PROVIDED',False))
 return pairs

def measurement(p:Pair)->dict[str,Any]:
 if p.eligibility=='eligible' and p.uncertainty_available:raise ValueError('ELIGIBLE_INTERVALS_REQUIRED')
 classification='NOT_ADJUDICATED_MISSING_UNCERTAINTY' if p.eligibility=='eligible' else 'UNSUPPORTED'
 return {'measurement_record_id':f'MV_{p.pair_id}_{p.channel}_{p.scenario}','pair_id':p.pair_id,'scenario':p.scenario,'channel':p.channel,'comparability_level':p.comparability_level,'left_support_state':'SUPPORTED' if p.eligibility=='eligible' else 'UNSUPPORTED_FOR_CASE','right_support_state':'SUPPORTED','left_prediction_interval':None,'right_prediction_interval':None,'declared_measurement_uncertainty':'NOT_PROVIDED','measurement_uncertainty_provenance':'NOT_PROVIDED','expanded_observable_intervals':None,'interval_combination_method':'CONSERVATIVE_ADDITIVE_BOUNDED_HALF_WIDTHS_NO_DISTRIBUTION','classification':classification,'reason_code':p.reason_code,'evidence_label':'RETAINED_CROSS_REPOSITORY_ANALYSIS','covers_pair_robustly':False,'claim_ceiling':'MODEL_RESPONSE_COMPARISON_ONLY__PHYSICAL_VALIDATION_NOT_ESTABLISHED'}

def minimum_sets(ids:list[str],records:list[dict[str,Any]])->dict[str,Any]:
 if not ids:return {'eligible_pair_ids':[],'result':'NO_COMPLETE_MEASUREMENT_SET','zero_pair_status':'NO_ELIGIBLE_PAIRWISE_DISCRIMINATION_PROBLEM','sets':[]}
 channels=sorted({r['channel'] for r in records if r['covers_pair_robustly']})
 for n in range(1,len(channels)+1):
  found=[]
  for choice in itertools.combinations(channels,n):
   covered={r['pair_id'] for r in records if r['covers_pair_robustly'] and r['channel'] in choice}
   if covered>=set(ids):found.append(list(choice))
  if found:return {'eligible_pair_ids':ids,'result':'COMPLETE_MEASUREMENT_SET','zero_pair_status':'NOT_APPLICABLE','sets':found}
 return {'eligible_pair_ids':ids,'result':'NO_COMPLETE_MEASUREMENT_SET','zero_pair_status':'NOT_APPLICABLE','sets':[]}

def build(a:dict[str,Any])->dict[str,Any]:
 e=retained_export();pairs=derive_pairs(a,e);eligible=[p.pair_id for p in pairs if p.eligibility=='eligible'];records=[measurement(p) for p in pairs if p.eligibility=='eligible'];channels=[x['channel'] for x in a['measurement_assumptions']['channels']];coverage=[{'channel':c,'robustly_covered_pair_ids':sorted({r['pair_id'] for r in records if r['channel']==c and r['covers_pair_robustly']})} for c in channels];sets=minimum_sets(eligible,records)
 decision={'decision_id':'EWP_CROSS_REPOSITORY_PROGRAMME_DECISION','selected_outcome':'SCI_MD_003_RP_A_001_ADDITIONAL_DATA_REQUIRED','puckworks_component_atlas_decision':a['decision']['selected_outcome'],'decision_reason_record_ids':[p.pair_id for p in pairs],'eligible_pair_count':len(eligible),'minimum_measurement_sets':sets['result'],'zero_pair_status':sets['zero_pair_status'],'physical_validation':'NOT_ESTABLISHED','reasons':['No level-1/2 scientifically eligible cross-repository pair survives retained-case, evidence-domain, node, basis, and uncertainty checks.','The zero-pair universe is not treated as successful coverage.','A complete measurement set cannot be calculated until comparability and uncertainty are established.'],'not_selected':{'APPARATUS_OBSERVATION_EXPLANATION_SURVIVES':'Foster and retained EWP machine histories are not matched at level 1/2.','DYNAMIC_BED_SIGNATURE_DISTINGUISHABLE':'No robust unique retained deformation discriminator.','SPATIAL_LOCALIZATION_ONLY_DISTINGUISHABLE_ROUTE':'No supported retained spatial comparator.'},'claim_ceiling':'MODEL_RESPONSE_COMPARISON_ONLY__PHYSICAL_VALIDATION_NOT_ESTABLISHED'}
 return {'ewp_observable_export':e,'pair_eligibility':[asdict(p) for p in pairs],'cross_repository_comparison':[asdict(p) for p in pairs],'measurement_value':records,'coverage_matrix':coverage,'minimum_measurement_sets':sets,'decision':decision}

def consume(path:Path)->dict[str,Any]:
 b=build(load_atlas(path))
 for name,value in b.items():_write(name+'.json',value)
 return b['decision']
def verify(path:Path)->None:
 for name,value in build(load_atlas(path)).items():
  p=OUT/(name+'.json')
  if not p.exists() or p.read_bytes()!=pretty(value):raise ValueError('DETERMINISTIC_EXPORT_DRIFT:'+name)
def main()->None:
 p=argparse.ArgumentParser();p.add_argument('command',choices=['run','verify']);p.add_argument('--atlas',type=Path,required=True);a=p.parse_args();consume(a.atlas) if a.command=='run' else verify(a.atlas);print('SCI_MD_003_C1_'+a.command.upper()+'_OK')
if __name__=='__main__':main()
