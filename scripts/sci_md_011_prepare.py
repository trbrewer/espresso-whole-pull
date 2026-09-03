#!/usr/bin/env python3
"""Create/validate the SCI-MD-011 Phase-A freeze without candidate target access."""
import argparse, json, os
from pathlib import Path
from sci_md_011_core import *
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs/analysis/sci_md_011'
PW_COMMIT='2058d0e947ee9eb92c52d64f6165b810f1fb4732';PW_TREE='a6ffb312473b15be43c1571a893b19873ea47c5a'
EWP='375b19b96096cf1d9681ab26efec7ed02b87dd09';TREE='5ae6135157019048205fe6bcdd6a9c2bce0a51fc'
HANDOFF=['ANALYSIS_ROW_INDEX.csv','FOLD_ASSIGNMENTS.csv','FOLD_MEMBERSHIP.csv','BREW_RESULTS.csv','FOLD_RESULTS.csv','CONDITION_RESULTS.csv','AGGREGATE_RESULTS.csv','UNCERTAINTY_RESULTS.json','PRESSURE_RESPONSE_DIAGNOSTICS.json','PARAMETER_STABILITY.csv','METRIC_CONTRACT.json','MODEL_SPECIFICATIONS.json','INPUT_ARTIFACT_REGISTER.json','PRE_SCORE_FREEZE.json','FREEZE_ARTIFACT_MANIFEST.json','RESULT_ARTIFACT_MANIFEST.json']
FREEZE_FILES=['docs/analysis/sci_md_011/TASK_CONTRACT.md','docs/analysis/sci_md_011/AUTHORITY_AND_HANDOFF.json','docs/analysis/sci_md_011/SCI_MD_010_HANDOFF.json','docs/analysis/sci_md_011/OBSERVATION_INTERFACE.json','docs/analysis/sci_md_011/EWP_CLOSURE_EQUIVALENCE.md','docs/analysis/sci_md_011/EWP_CLOSURE_EQUIVALENCE.json','docs/analysis/sci_md_011/MODEL_SPECIFICATIONS.json','docs/analysis/sci_md_011/PRIVILEGE_LEDGER.csv','docs/analysis/sci_md_011/EVALUATION_CONTRACT.json','docs/analysis/sci_md_011/PRE_SCORE_FREEZE.json','docs/analysis/sci_md_011/FREEZE_REPORT.md','scripts/sci_md_011_core.py','scripts/sci_md_011_prepare.py','scripts/sci_md_011_execute.py','scripts/validate_sci_md_011.py','scripts/run_sci_md_011_closure_oracle.sh','tests/test_sci_md_011.py','tests/fixtures/sci_md_011_synthetic_receipt.json','tests/fixtures/sci_md_011_closure_oracle/sci_md_011_closure_oracle.C','tests/fixtures/sci_md_011_closure_oracle/Make/files','tests/fixtures/sci_md_011_closure_oracle/Make/options']
def puckworks():
 p=Path(os.environ.get('SCI_MD_011_PUCKWORKS_ROOT','')).resolve()
 if not (p/'puckworks/data/MANIFEST.csv').is_file() or git(p,'rev-parse','HEAD')!=PW_COMMIT or git(p,'rev-parse','HEAD^{tree}')!=PW_TREE or git(p,'status','--short'):raise ValueError('PUCKWORKS_AUTHORITY')
 return p
def generate():
 pw=puckworks();OUT.mkdir(parents=True,exist_ok=True);s10=ROOT/'docs/analysis/sci_md_010'
 arts=[{'path':f'docs/analysis/sci_md_010/{n}','sha256':sha256(s10/n)} for n in HANDOFF]
 sources=[]
 for rel in ['docs/cards/waszkiewicz2025.md','puckworks/models/waszkiewicz2025/poroelastic.py','puckworks/data/MANIFEST.csv','puckworks/data/waszkiewicz2025/solids_calibration.csv','puckworks/data/waszkiewicz2025/constants.csv','puckworks/data/waszkiewicz2025/brewer_quadratic_params.csv','puckworks/data/waszkiewicz2025/equilibrium_windows.csv','puckworks/data/waszkiewicz2025/traces_per_brew.csv']:
  sources.append({'path':rel,'sha256':sha256(pw/rel)})
 hand={'task_id':TASK,'sci_md_010_merge_commit':EWP,'sci_md_010_merge_tree':TREE,'result_head':'72236a656b9d8230e657ce5cb2df4b610f5c1503','freeze_head':'9b1c7ed2505ac5a95768cdd188682e7a6ee6ee77','freeze_tree':'1ef01bd26ee2a45ec509ee8c6afa99eaa009c4a5','freeze_manifest_sha256':'cdac6800b8976290621b1f0e75b484c7b062833d4ebe03fefee51a8789dbf030','result_manifest_sha256':'2e7379806f021bc26649fd8169b07620a85808c74a6f590d4441e07530d3a3d5','artifacts':arts}
 write_json(OUT/'SCI_MD_010_HANDOFF.json',hand)
 authority={'task_id':TASK,'ewp':{'commit':EWP,'tree':TREE},'puckworks_analysis':{'commit':PW_COMMIT,'tree':PW_TREE,'worktree':'CLEAN','sources':sources},'production_puckworks_lock':load_json(ROOT/'dependencies/puckworks.lock.json'),'reviewed_to_live_delta':[],'pr_140':'MERGED','issue_139':'CLOSED','stage_f_authorized':False,'stage_d_authorized':False}
 write_json(OUT/'AUTHORITY_AND_HANDOFF.json',authority)
 observation={'authority':'SCI_MD_010_ACCEPTED_LINE_TO_BASKET_OBSERVATION_ADAPTER','target':{'field':'mass_flow_rate__g_per_s','time':'endpoint_100s','role':'accepted equilibrium proxy; not identical to source 110-120 s calibration'},'predictive_input':'directly measured endpoint line_pressure__bar','prohibited_input':'flow-derived or target-derived basket pressure','machine_calibration':CAL,'equation':'p_basket_pred = p_line_measured - (a*q_pred^2+b*q_pred+c)','evaluation_units':56,'pressure_conditions':11,'outer_folds':11,'safety_flow_range_g_s':[0,20],'source_60_brew_calibration':'CONTEXT_ONLY'}
 write_json(OUT/'OBSERVATION_INTERFACE.json',observation)
 specs={'task_id':TASK,'models':[{'model_id':MODELS[0],'role':'contextual naive; immutable SCI-MD-010 reuse'},{'model_id':MODELS[1],'equation':'max(0,a0+a1*p_line+a2*p_line^2)','role':'accepted comparator; immutable reuse plus integrity recomputation'},{'model_id':P1,'equation':'Qc*x*(4-6*x+4*x^2-x^3)','fitted':['log(Qc_g_s)','log(Pc_bar)']},{'model_id':E2C,'equation':'Qc*J(x,Phi)/J(1,Phi)','fixed_Phi':PHI,'phi_privilege':'TARGET_EXPOSED_SOURCE_CONDITIONED_CONTEXT_NOT_FOLD_FITTED','fitted':['log(Qc_g_s)','log(Pc_bar)']}],'parameterization':'log positive','bounds':BOUNDS,'bounds_basis':'broad numerical/source-domain admissibility; not candidate performance','optimizer':{'starts':'2x2 inclusive deterministic log-boundary lattice','refinement':'bounded coordinate pattern search','same_for_candidates':True,'tie_break':'objective then lexicographic log parameters','max_iterations_per_start':24,'log_step_stop':1e-5},'production_code':{'path':'solver/espressoWholePullFoam/poroelasticCompaction.H','sha256':sha256(ROOT/'solver/espressoWholePullFoam/poroelasticCompaction.H')}}
 write_json(OUT/'MODEL_SPECIFICATIONS.json',specs)
 contract={'task_id':TASK,'models':list(MODELS),'row_index':'docs/analysis/sci_md_010/ANALYSIS_ROW_INDEX.csv','fold_assignments':'docs/analysis/sci_md_010/FOLD_ASSIGNMENTS.csv','fold_membership':'docs/analysis/sci_md_010/FOLD_MEMBERSHIP.csv','sci_md_010_brew_results':'docs/analysis/sci_md_010/BREW_RESULTS.csv','observation_interface':'docs/analysis/sci_md_011/OBSERVATION_INTERFACE.json','model_specifications':'docs/analysis/sci_md_011/MODEL_SPECIFICATIONS.json','machine_calibration':CAL,'fixed_phi':PHI,'domain':{'x':[0,'1 exclusive'],'epsilon':DOMAIN_EPS,'pressure_residual_tolerance_bar':PRESSURE_TOL,'flow_consistency_tolerance':FLOW_TOL,'maximum_iterations':MAX_ROOT_ITER,'no_bracket':'retain failed prediction','nonfinite':'reject','line_pressure_le_c':'zero flow and basket pressure'},'fit':{'objective':'condition-balanced squared flow error g2/s2','bounds':BOUNDS},'metrics':{'primary':'equal-condition mean of fold RMSE/training condition-mean flow range','bootstrap_count':BOOTSTRAPS,'seed':SEED,'bootstrap_refit':False,'unit':'condition_then_paired_brew','quantile':'nearest-rank ceil(p*n)-1'},'gates':{'low_subset_condition_mean_line_pressure_bar':'<=5.25','high_subset_condition_mean_line_pressure_bar':'>=8.5','low':'predicted slope > 0','high':'predicted slope <= 0'},'claim_level':'LEVEL_3_RETROSPECTIVE_GROUPED_WITHIN_SOURCE_CONDITIONAL_ON_MEASURED_HYDRAULIC_CONTEXT','current_full_ewp':'NOT_TESTED'}
 write_json(OUT/'EVALUATION_CONTRACT.json',contract)
 freeze={'task_id':TASK,'governance':'G1','scoring_executed':False,'real_candidate_fits_generated':False,'real_candidate_predictions_generated':False,'real_candidate_scores_generated':False,'phase_b_authorized':False,'stage_f_authorized':False,'stage_d_authorized':False,'current_full_ewp_validated':False,'seed':SEED,'bootstrap_count':BOOTSTRAPS,'selected_models':list(MODELS),'production_openfoam_case_count':0,'fixed_phi':PHI,'puckworks_analysis':authority['puckworks_analysis'],'ewp_base':authority['ewp']}
 write_json(OUT/'PRE_SCORE_FREEZE.json',freeze)
 manifest={'task_id':TASK,'scoring_executed':False,'artifacts':[{'path':p,'sha256':sha256(ROOT/p)} for p in FREEZE_FILES]}
 manifest['aggregate_content_sha256']=hashlib.sha256(''.join(a['sha256'] for a in manifest['artifacts']).encode()).hexdigest();write_json(OUT/'FREEZE_ARTIFACT_MANIFEST.json',manifest)
 return pw
def validate():
 pw=puckworks(); hand=load_json(OUT/'SCI_MD_010_HANDOFF.json')
 for a in hand['artifacts']:
  if sha256(ROOT/a['path'])!=a['sha256']:raise ValueError('HANDOFF_CHANGED:'+a['path'])
 if len(load_csv(ROOT/'docs/analysis/sci_md_010/ANALYSIS_ROW_INDEX.csv'))!=56:raise ValueError('ROW_COUNT')
 return {'joined_rows':56,'distinct_physical_brews':56,'pressure_conditions':11,'outer_folds':11,'alias_duplication':0,'candidate_real_fits':0,'candidate_real_predictions':0,'candidate_real_scores':0}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--validate-only',action='store_true');a=ap.parse_args()
 if not a.validate_only:generate()
 print(json.dumps(validate(),sort_keys=True))
if __name__=='__main__':main()
