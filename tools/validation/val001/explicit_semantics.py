"""Checked-in explicit schema specifications and executable semantic profiles."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any,Callable
from .framework import ContractError,load_json,validate_record
from .schema import lint_schema
from .normative import ASSIGNMENT_REGISTRY,generated_explicit_registry,load_normative_registry

SPEC_REGISTRY="validation/val001/VAL_001_EXPLICIT_SCHEMA_SPECIFICATION_REGISTRY.json"
PROFILE_REGISTRY="validation/val001/VAL_001_SEMANTIC_PROFILE_REGISTRY.json"
PUCKWORKS=("fc61c4670ec7bf801e40bb391aab16048b8da26b","1d553e44ee2f7480a5df521560801b478618cc84")

def _walk(value:Any):
 if isinstance(value,dict):
  for key,item in value.items():yield key,item;yield from _walk(item)
 elif isinstance(value,list):
  for item in value:yield from _walk(item)

def load_policy(root:Path):
 load_normative_registry(root)
 specs=load_json(root/SPEC_REGISTRY);profiles=load_json(root/PROFILE_REGISTRY)
 if specs!=generated_explicit_registry(root):raise ContractError("VAL001_EXPLICIT_REGISTRY_NOT_NORMATIVELY_REPRODUCIBLE")
 assignments=load_json(root/ASSIGNMENT_REGISTRY)["assignments"]
 spec_by_id={s["specification_id"]:s for s in specs["specifications"]}
 bindings={b["path"]:b for b in specs["record_bindings"]}
 profile_by_id={p["profile_id"]:p for p in profiles["profiles"]}
 if len(spec_by_id)!=len(specs["specifications"]):raise ContractError("VAL001_DUPLICATE_SCHEMA_SPECIFICATION")
 if len(bindings)!=len(specs["record_bindings"]):raise ContractError("VAL001_DUPLICATE_EXPLICIT_RECORD_BINDING")
 if len(profile_by_id)!=len(profiles["profiles"]):raise ContractError("VAL001_DUPLICATE_SEMANTIC_PROFILE")
 prohibited=set(specs["prohibited_origins"])
 for spec in specs["specifications"]:
  if spec["origin"] in prohibited:raise ContractError("VAL001_INSTANCE_DERIVED_GOVERNING_SCHEMA")
  lint_schema(spec["schema"])
  if spec["semantic_profile_id"] not in profile_by_id:raise ContractError("VAL001_MISSING_SEMANTIC_PROFILE")
 for path,binding in bindings.items():
  if binding["specification_id"] not in spec_by_id:raise ContractError(f"VAL001_UNKNOWN_SCHEMA_SPECIFICATION:{path}")
  if binding["semantic_profile_id"] not in profile_by_id:raise ContractError(f"VAL001_MISSING_SEMANTIC_PROFILE:{path}")
  profile=profile_by_id[binding["semantic_profile_id"]]
  if binding["specification_id"] not in profile["applies_to_specification_ids"]:raise ContractError(f"VAL001_PROFILE_SCOPE_MISMATCH:{path}")
 assigned={a["path"]:a for a in assignments}
 if len(assigned)!=len(assignments):raise ContractError("VAL001_DUPLICATE_IMMUTABLE_PROFILE_ASSIGNMENT")
 if set(assigned)!=set(bindings):raise ContractError("VAL001_IMMUTABLE_PROFILE_ASSIGNMENT_COVERAGE_MISMATCH")
 for path,binding in bindings.items():
  assignment=assigned[path]
  for key in ("specification_id","semantic_profile_id"):
   if assignment[key]!=binding[key]:raise ContractError(f"VAL001_IMMUTABLE_PROFILE_ASSIGNMENT_MISMATCH:{path}:{key}")
  spec=spec_by_id[binding["specification_id"]]
  for key in ("schema_id","schema_version"):
   if assignment[key]!=spec[key]:raise ContractError(f"VAL001_IMMUTABLE_PROFILE_ASSIGNMENT_MISMATCH:{path}:{key}")
 return specs,profiles,spec_by_id,bindings,profile_by_id

def explicit_schema_for(root:Path,path:str):
 _,_,specs,bindings,_=load_policy(root)
 if path not in bindings:raise ContractError(f"VAL001_RECORD_WITHOUT_EXPLICIT_SCHEMA:{path}")
 return specs[bindings[path]["specification_id"]]["schema"]

def _global_claims(path,value,metadata):
 allowed_false={False,None,"NOT_AUTHORIZED","NOT_AUTHORIZED_BY_VAL001","NOT_PERFORMED","NO_GOVERNING_PHYSICS_CHANGE"}
 for key,item in _walk(value):
  k=key.lower()
  if not isinstance(item,(dict,list)):
   if k in {"physical_validation","general_physical_validation","general_whole_solver_physical_validation","whole_solver_validation"} and item not in {"NOT_ESTABLISHED",False,None}:raise ContractError("INV-GLOBAL-CLAIMS:PHYSICAL_VALIDATION_ESCALATION")
   if k in {"new_governing_physics","governing_physics_change"} and item not in allowed_false:raise ContractError("INV-GLOBAL-CLAIMS:NEW_PHYSICS_ESCALATION")
   if k in {"fitting_allowed","retuning_allowed","fitting_or_retuning_allowed","configuration_change","scientific_configuration_change","solver_source_change"} and item is not False:raise ContractError("INV-GLOBAL-CLAIMS:METHOD_CHANGE_ESCALATION")
   if k in {"fit_count","retune_count","fit_or_retune_count","fits_or_retunes"} and item!=0:raise ContractError("INV-GLOBAL-CLAIMS:FIT_RETUNE_COUNT_ESCALATION")
   if k in {"experimental_commissioning_authorized","commissioning_authorized","holdout_execution_authorized","protected_scoring_authorized","holdout_scoring_authorized"} and item is not False:raise ContractError("INV-GLOBAL-CLAIMS:PROTECTED_EXPERIMENT_ESCALATION")
   if k in {"independent_validation","transfer_validation","holdout_validation","physical_equivalence","model_correctness","mechanism_identity"} and item not in {False,None,"NOT_ESTABLISHED","NOT_ASSESSED","NOT_CLAIMED"}:raise ContractError("INV-GLOBAL-CLAIMS:CLAIM_CEILING_ESCALATION")

def _metadata(path,value,metadata):
 if not metadata:raise ContractError("INV-IMMUTABLE-PROFILE-ASSIGNMENT:MISSING")
 record_keys=("current","historical","audit_only","governing","executable","semantic_profile_id") if metadata["historical"] else ("semantic_profile_id",)
 for key in (*record_keys,"record_class","schema_id"):
  if key in value and key in metadata and isinstance(value[key],type(metadata[key])) and value[key]!=metadata[key]:raise ContractError(f"INV-IMMUTABLE-PROFILE-ASSIGNMENT:RECORD_MISMATCH:{key}")
  if key in metadata.get("record_declared",{}) and metadata["record_declared"][key]!=metadata[key]:raise ContractError(f"INV-IMMUTABLE-PROFILE-ASSIGNMENT:DECLARED_MISMATCH:{key}")
 if metadata["historical"]:
  required={"current":False,"historical":True,"audit_only":True,"governing":False,"executable":False}
  if any(metadata[k] is not v for k,v in required.items()):raise ContractError("INV-IMMUTABLE-PROFILE-ASSIGNMENT:HISTORICAL_AUTHORITY_ESCALATION")

def _puckworks(path,value,metadata):
 for key,item in _walk(value):
  if key in {"puckworks","puckworks_lock","locked_dependency"} and isinstance(item,dict) and ("commit" in item or "tree" in item):
   if (item.get("commit"),item.get("tree"))!=PUCKWORKS:raise ContractError("INV-PUCKWORKS-LOCK:DEPENDENCY_MISMATCH")

def _campaign(path,value,metadata):
 if value.get("status")!="PLANNING_RECORDS_ONLY":raise ContractError("INV-CAMPAIGN-PLANNING:STATUS")
 if [c.get("id") for c in value.get("campaigns",[])]!=[f"EXP-{i:03d}" for i in range(1,10)]:raise ContractError("INV-CAMPAIGN-PLANNING:IDENTITIES")
 for c in value["campaigns"]:
  required={"proposed_status":"PLANNED","evidence_level":"PLANNING_ONLY","rights_state":"NOT_ESTABLISHED","redistribution_state":"NOT_AUTHORIZED","holdout_requirement":"MUST_BE_DEFINED_BEFORE_EXECUTION","prohibited_role":"CURRENT_VALIDATION","data_exist":"NOT_ESTABLISHED","data_accessed":False,"execution_authorized":False,"commissioning_authorized":False}
  for key,expected in required.items():
   if c.get(key)!=expected:raise ContractError(f"INV-CAMPAIGN-PLANNING:{c.get('id')}:{key}")
  if not c.get("missing_information"):raise ContractError(f"INV-CAMPAIGN-PLANNING:{c.get('id')}:missing_information")
  permitted=str(c.get("permitted_role",""));prohibited=str(c.get("prohibited_role",""))
  if permitted==prohibited or "CURRENT_VALIDATION" in permitted:raise ContractError(f"INV-CAMPAIGN-PLANNING:{c.get('id')}:ROLE_ESCALATION")
 common=value.get("common_provenance",{})
 expected={"proposed_status":"PLANNED","current_evidence_level":"PLANNING_ONLY","rights_state":"NOT_ESTABLISHED","redistribution_state":"NOT_AUTHORIZED","holdout_requirement":"MUST_BE_DEFINED_BEFORE_ANY_FUTURE_EXECUTION","permitted_evidence_role":"FUTURE_INFORMATION_GAP_PLANNING","prohibited_evidence_role":"COMPLETED_EXPERIMENT_OR_CURRENT_VALIDATION","data_exist":"NOT_ESTABLISHED","data_accessed":False,"execution_authorized":False,"experimental_commissioning_authorized":False}
 for key,wanted in expected.items():
  if common.get(key)!=wanted:raise ContractError(f"INV-CAMPAIGN-PLANNING:COMMON:{key}")
 if not common.get("known_missing_information") or value.get("artifact_bindings")!=[]:raise ContractError("INV-CAMPAIGN-PLANNING:UNBOUND_EVIDENCE")

def _sensitivity(path,value,metadata):
 if value.get("structural_identifiability")!="NOT_ASSESSED":raise ContractError("INV-SENSITIVITY-PROSPECTIVE:STRUCTURAL_IDENTIFIABILITY")
 text=json.dumps(value)
 if 'BROAD_CAMPAIGN_COMPLETED' in text or 'STRUCTURAL_PROOF' in text:raise ContractError("INV-SENSITIVITY-PROSPECTIVE:FALSE_COMPLETION")

def _consumed(path,value,metadata):
 if value.get("authority_status")!="CONSUMED":raise ContractError("INV-CONSUMED-LOCK:AUTHORITY")
 for k in ("remaining_real_data_comparison_invocations","remaining_governed_result_producing_invocations"):
  if value.get(k)!=0:raise ContractError("INV-CONSUMED-LOCK:REMAINING_INVOCATIONS")
 for k in ("alternate_invocation_id_allowed","alternate_ledger_allowed","alternate_authority_allowed","alternate_activation_allowed","further_retry_authorized"):
  if value.get(k) is not False:raise ContractError("INV-CONSUMED-LOCK:ALTERNATE_OR_RETRY")

def _reexpression(path,value,metadata):
 if value.get("new_score_bearing_comparison",value.get("NEW_SCORE_BEARING_COMPARISON")) is not False:raise ContractError("INV-HISTORICAL-REEXPRESSION:SCORE_BEARING")
 if value.get("physical_validation",value.get("PHYSICAL_VALIDATION"))!="NOT_ESTABLISHED":raise ContractError("INV-HISTORICAL-REEXPRESSION:PHYSICAL_VALIDATION")

def _evidence_gap(path,value,metadata):
 if value.get("execution",{}).get("executable") is not False or value.get("rights",{}).get("comparison_allowed") is not False or not value.get("execution",{}).get("reason_codes"):raise ContractError("INV-EVIDENCE-GAP:EXECUTABLE")

def _v2(path,value,metadata):
 text=json.dumps(value)
 for token in ("POST_OBSERVATION_REPRODUCTION","NOT_BLIND","NOT_INDEPENDENT","DESCRIPTIVE_COMPARISON_NO_UNCERTAINTY_GATE"):
  if token not in text:raise ContractError(f"INV-V2-DESCRIPTIVE:MISSING_{token}")

def _failed(path,value,metadata):
 status=value.get("status","")
 if not status.startswith("FAILED_INVALIDATED") or status in {"COMPLETED","VALID"}:raise ContractError("INV-FAILED-INVOCATION:STATUS")
 if value.get("failure",{}).get("score_exposure") in {None,"NONE"}:raise ContractError("INV-FAILED-INVOCATION:SCORE_EXPOSURE")

def _qualification(path,value,metadata):
 if value.get("metric_input_artifacts") not in ([],None):raise ContractError("INV-OPENFOAM-QUALIFICATION:METRIC_INPUT_PROMOTION")
 if "traces_produced_v2_pressure_sweep_predictions" in value and value.get("traces_produced_v2_pressure_sweep_predictions") is not False:raise ContractError("INV-OPENFOAM-QUALIFICATION:V2_DERIVATION_CLAIM")
 for item in value.get("framework_qualification_artifacts",[]):
  if not item.get("trace_sha256") or not item.get("log_sha256"):raise ContractError("INV-OPENFOAM-QUALIFICATION:MISSING_HASH")

def _rights(path,value,metadata):
 for item in value.get("selected",[]):
  if item.get("protected") is not False or item.get("holdout") is not False or item.get("comparison_allowed") is not True:raise ContractError("INV-RIGHTS-ACCESS:INADMISSIBLE_EXECUTION")

def _adapter(path,value,metadata):
 if value.get("rights",{}).get("comparison_allowed") is not True or value.get("evidence",{}).get("protected") is not False or value.get("evidence",{}).get("holdout_status")!="NOT_HOLDOUT":raise ContractError("INV-CURRENT-ADAPTER:RIGHTS_OR_HOLDOUT")

def _authority(path,value,metadata):
 _global_claims(path,value,metadata)

def _external_root(path,value,metadata):
 if value.get("default_to_current_head") is not False or value.get("terminal_root_self_embedded") is not False or value.get("later_commit_requires_new_review_root") is not True:raise ContractError("INV-EXTERNAL-ROOT:PROTOCOL")

def _invalidated(path,value,metadata):
 if value.get("claim_boundary",{}).get("physical_validation")!="NOT_ESTABLISHED":raise ContractError("INV-INVALIDATED-RESULT:CLAIM")
 if value.get("decision")!="ADDITIONAL_DATA_REQUIRED_BEFORE_NEW_PHYSICS":raise ContractError("INV-INVALIDATED-RESULT:DECISION")

def _comparison_run(path,value,metadata):
 text=json.dumps(value)
 if "RETUN" in text and "NO_" not in text and '"fits_or_retunes": 0' not in text:raise ContractError("INV-COMPARISON-RUN:RETUNING")

INVARIANTS:dict[str,Callable]= {
 "INV-GLOBAL-CLAIMS":_global_claims,"INV-METADATA-STATE":_metadata,"INV-PUCKWORKS-LOCK":_puckworks,
 "INV-IMMUTABLE-PROFILE-ASSIGNMENT":_metadata,
 "INV-CAMPAIGN-PLANNING":_campaign,"INV-SENSITIVITY-PROSPECTIVE":_sensitivity,"INV-CONSUMED-LOCK":_consumed,
 "INV-HISTORICAL-REEXPRESSION":_reexpression,"INV-EVIDENCE-GAP":_evidence_gap,"INV-V2-DESCRIPTIVE":_v2,
 "INV-FAILED-INVOCATION":_failed,"INV-OPENFOAM-QUALIFICATION":_qualification,"INV-RIGHTS-ACCESS":_rights,
 "INV-CURRENT-ADAPTER":_adapter,"INV-AUTHORITY-FREEZE-ACTIVATION":_authority,"INV-EXTERNAL-ROOT":_external_root,
 "INV-INVALIDATED-RESULT":_invalidated,"INV-COMPARISON-RUN":_comparison_run,
}

def validate_profile_dispatch(root:Path,path:str,value:dict[str,Any],metadata:dict[str,Any]|None=None)->list[str]:
 _,profiles,specs,bindings,profile_by_id=load_policy(root)
 binding=bindings.get(path)
 if not binding:raise ContractError(f"VAL001_RECORD_WITHOUT_EXECUTABLE_SEMANTIC_PROFILE:{path}")
 spec=specs[binding["specification_id"]];validate_record(value,spec["schema"])
 return execute_profile_invariants(root,path,value,metadata)

def execute_profile_invariants(root:Path,path:str,value:dict[str,Any],metadata:dict[str,Any]|None=None)->list[str]:
 """Execute named profile invariants independently of immutable hashes/schema consts."""
 _,profiles,specs,bindings,profile_by_id=load_policy(root)
 binding=bindings.get(path)
 if not binding:raise ContractError(f"VAL001_RECORD_WITHOUT_EXECUTABLE_SEMANTIC_PROFILE:{path}")
 assignments={a["path"]:a for a in load_json(root/ASSIGNMENT_REGISTRY)["assignments"]}
 assignment=assignments.get(path)
 if not assignment:raise ContractError(f"VAL001_RECORD_WITHOUT_IMMUTABLE_PROFILE_ASSIGNMENT:{path}")
 if binding["semantic_profile_id"]!=assignment["semantic_profile_id"]:raise ContractError(f"VAL001_IMMUTABLE_PROFILE_ASSIGNMENT_MISMATCH:{path}")
 effective=dict(assignment)
 if metadata:effective["record_declared"]=metadata
 profile=profile_by_id[assignment["semantic_profile_id"]];executed=[]
 _metadata(path,value,effective);executed.append("INV-IMMUTABLE-PROFILE-ASSIGNMENT")
 for invariant_id in profile["invariant_ids"]:
  invariant=INVARIANTS.get(invariant_id)
  if invariant is None:raise ContractError(f"VAL001_UNKNOWN_INVARIANT:{invariant_id}")
  invariant(path,value,effective);executed.append(invariant_id)
 if set(profile["invariant_ids"])-set(executed):raise ContractError("VAL001_REQUIRED_INVARIANT_NOT_EXECUTED")
 return executed
