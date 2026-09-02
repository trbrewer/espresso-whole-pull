import csv,json
from collections import Counter
from pathlib import Path
from .authority import AuthorityError,sha256,verify_consumed,verify_frozen_ewp,verify_puckworks
from .compatibility import expected_pairs,independently_eligible
from .inventory import scan_registered_families,validate_support_inventory
from .vocabulary import UNCERTAINTY_ELIGIBLE_ROLES,UNCERTAINTY_STATISTICS

BOOL_FIELDS=("qualified_for_task_role","rights_permit_analysis","provenance_complete","target_exposed","source_internal_validation","consumed_comparison_conflict","ewp_calibration_independent","uncertainty_present","decision_material")
OPTIONAL_FIELDS=("source_publication_identity","source_artifact_path","source_artifact_sha256","laboratory_identity","apparatus_identity","coffee_lot_roast","grinder_preparation_compaction","geometry","independence_relative_to_candidates","rights_status","native_quantity","source_field_or_extraction_path","native_units","canonical_units","conversion_chain","basis","reference_state","physical_state","spatial_support","temporal_support","population_regime","observation_operator","replicate_unit","uncertainty_statistic","uncertainty_estimand","uncertainty_scale","uncertainty_meaning","interval_extraction_rule","ewp_consumer")
FIELDS=("support_id","originating_task_id","family_id","dataset_ids","source_register_identity","rights_basis","source_role","raw_source_bytes_status","lineage_id","correlation_group_id","experiment_id","canonical_quantity_id","value_representation","frozen_role","terminal_reason",*BOOL_FIELDS,*OPTIONAL_FIELDS)
SEED_FILES=("AUTHORITY.json","CONSUMED_RESULT_ARTIFACTS.json","DATA_AVAILABILITY_PREFLIGHT.json","ISSUE_CONTRACT.md")

def dump(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")
def csv_dump(path,rows,fields):
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n");writer.writeheader()
        for row in rows:writer.writerow({key:json.dumps(row.get(key),sort_keys=True) if isinstance(row.get(key),(list,dict)) else row.get(key) for key in fields})
def uncertainty_eligible(item):
    if item.get("uncertainty_present") is not True:return False
    return bool(item["uncertainty_statistic"] in UNCERTAINTY_STATISTICS and isinstance(item["uncertainty_estimand"],str) and item["uncertainty_estimand"] and isinstance(item["replicate_unit"],str) and item["replicate_unit"] and isinstance(item["uncertainty_scale"],str) and item["uncertainty_scale"] and isinstance(item["observation_operator"],str) and item["observation_operator"] and item["frozen_role"] in UNCERTAINTY_ELIGIBLE_ROLES)
def enrich_supports(root,records,rules,manifest_ids,family_ids,ledger_by_path):
    rule_by_id={row["support_id"]:row for row in rules};result=[]
    for source in records:
        row={key:source.get(key) for key in FIELDS};row.update(source)
        for field in BOOL_FIELDS:
            if type(row.get(field)) is not bool:raise AuthorityError(f"support Boolean absent or non-Boolean: {row.get('support_id')}:{field}")
        if row["family_id"] not in family_ids:raise AuthorityError(f"support family is not registered: {row['support_id']}")
        for dataset_id in row["dataset_ids"]:
            if dataset_id not in manifest_ids:raise AuthorityError(f"support references unregistered dataset: {dataset_id}")
        path=row.get("source_artifact_path")
        if path:
            row["source_artifact_sha256"]=sha256(root/path)
            if path not in ledger_by_path or ledger_by_path[path]!=row["source_artifact_sha256"]:raise AuthorityError(f"support artifact is not bound by consumed ledger: {row['support_id']}")
        if row["provenance_complete"] is True:
            mandatory=(row.get("originating_task_id"),path,row.get("source_register_identity"),row.get("rights_basis"),row.get("source_role"),row.get("lineage_id"),row.get("correlation_group_id"))
            if any(not value for value in mandatory):raise AuthorityError(f"provenance marked complete without mandatory identity: {row['support_id']}")
        if row["rights_permit_analysis"] is True and not row.get("rights_basis"):raise AuthorityError(f"rights true without traceable basis: {row['support_id']}")
        rule=rule_by_id.get(row["support_id"]);row["source_field_or_extraction_path"]={"minimum_json_path":rule["minimum_json_path"],"maximum_json_path":rule["maximum_json_path"]} if rule else None;row["interval_extraction_rule"]=rule["interval_semantics"] if rule else None
        if row["uncertainty_present"] is False:
            for field in ("uncertainty_statistic","uncertainty_estimand","replicate_unit","uncertainty_scale","uncertainty_meaning"):row[field]=None
        elif not uncertainty_eligible(row):raise AuthorityError(f"typed uncertainty record incomplete or role-ineligible: {row['support_id']}")
        row["interval"]=None;result.append(row)
    validate_support_inventory(result);return sorted(result,key=lambda item:item["support_id"])
def real_config_preflight(supports,execution):
    by_component={}
    for item in supports:
        if item.get("canonical_quantity_id"):by_component.setdefault(item["canonical_quantity_id"],[]).append(item)
    components=[]
    for quantity,items in sorted(by_component.items()):
        common=[item for item in items if item["frozen_role"]=="COMMON_CONSTRAINT_CANDIDATE"]
        eligible=[item for item in common if independently_eligible(item)]
        required=expected_pairs(eligible);configured=[]
        for left,right in required:
            key=f"{left}|{right}";reverse=f"{right}|{left}"
            if key not in execution["pairwise_gate_contracts"] and reverse not in execution["pairwise_gate_contracts"]:raise AuthorityError(f"real config omits required pair: {key}")
            configured.append([left,right])
        components.append({"canonical_quantity_id":quantity,"common_candidate_count":len(common),"independently_eligible_count":len(eligible),"common_candidate_ids":[x["support_id"] for x in common],"required_pair_count":len(required),"generated_pair_count":len(configured),"generated_pairs":configured})
    return {"components":components,"uncertainty_record_count":sum(uncertainty_eligible(item) for item in supports),"blocker_record_count":sum(item["frozen_role"] in ("BLOCKED_AUTHORITY","BLOCKED_SEMANTIC","BLOCKED_RIGHTS") for item in supports),"decision_material_blocker_count":sum(item["decision_material"] is True and item["frozen_role"] in ("BLOCKED_AUTHORITY","BLOCKED_SEMANTIC","BLOCKED_RIGHTS") for item in supports)}
def generate(root:Path,puckworks:Path,output:Path):
    authority=json.loads((output/"AUTHORITY.json").read_text());verify_frozen_ewp(root,authority,include_runtime=False);puck=verify_puckworks(puckworks,authority["puckworks"]);ledger=json.loads((output/"CONSUMED_RESULT_ARTIFACTS.json").read_text());verify_consumed(root,ledger);ledger_by_path={row["path"]:row["sha256"] for row in ledger["artifacts"]}
    rules=json.loads((root/"analysis/sci_data_fusion_001/family_screen_rules.json").read_text());families,datasets=scan_registered_families(puckworks,rules);family_ids={row["family_id"] for row in families};manifest_ids={row["dataset_id"] for row in datasets}
    extraction=json.loads((root/"analysis/sci_data_fusion_001/support_extraction_rules.json").read_text())["rules"]
    for rule in extraction:
        if sha256(root/rule["artifact_path"])!=rule["artifact_sha256"]:raise AuthorityError(f"extraction authority mismatch: {rule['support_id']}")
    supports=enrich_supports(root,json.loads((root/"analysis/sci_data_fusion_001/support_inventory.json").read_text())["records"],extraction,manifest_ids,family_ids,ledger_by_path)
    counts=Counter(row["family_id"] for row in supports)
    for family in families:family["detailed_support_record_count"]=counts[family["family_id"]]
    if sum(row["detailed_support_record_count"] for row in families)!=len(supports):raise AuthorityError("family/support counts do not reconcile")
    contract=json.loads((root/"analysis/sci_data_fusion_001/task_contract_template.json").read_text());freeze_inputs=json.loads((root/"analysis/sci_data_fusion_001/freeze_inputs.json").read_text());execution=json.loads((root/"analysis/sci_data_fusion_001/execution_plan.json").read_text());preflight=real_config_preflight(supports,execution)
    dump(output/"TASK_CONTRACT.json",contract);dump(output/"CANONICAL_QUANTITY_REGISTER.json",{"quantities":freeze_inputs["canonical_quantities"]});dump(output/"CANDIDATE_SUPPORT_FREEZE.json",{"support_candidates":supports,"pairwise_gate_contracts":execution["pairwise_gate_contracts"]});dump(output/"PUCKWORKS_FAMILY_SCREEN.json",{"declared_family_count":len(families),"screened_family_count":len(families),"families":families});csv_dump(output/"PUCKWORKS_FAMILY_SCREEN.csv",families,list(families[0]));csv_dump(output/"PUCKWORKS_DATASET_SCREEN.csv",datasets,list(datasets[0]));dump(output/"SOURCE_SUPPORT_INVENTORY.json",{"records":supports});csv_dump(output/"SOURCE_SUPPORT_INVENTORY.csv",supports,FIELDS);dump(output/"SUPPORT_EXTRACTION_RULES.json",{"rules":extraction});dump(output/"LINEAGE_CORRELATION_REGISTER.json",{"groups":[{"lineage_id":a,"correlation_group_id":b} for a,b in sorted({(row.get("lineage_id"),row.get("correlation_group_id")) for row in supports if row.get("lineage_id")},key=str)]});dump(output/"EXECUTION_PLAN.json",execution);dump(output/"AUDIT_RECORD_SCHEMA.json",json.loads((root/"schemas/sci_data_fusion_001_audit_record.schema.json").read_text()));dump(output/"SUPPORT_RECORD_SCHEMA.json",json.loads((root/"schemas/sci_data_fusion_001_support_record.schema.json").read_text()));dump(output/"RESULT_VOCABULARY.json",json.loads((root/"analysis/sci_data_fusion_001/result_vocabulary.json").read_text()))
    validation={"status":"PASS","real_phase_b_executed":False,"family_count":len(families),"dataset_reference_count":len(datasets),"detailed_support_count":len(supports),"frozen_ewp_base":authority["frozen_ewp_base"],"accepted_predecessor":authority["accepted_predecessor"],"puckworks":puck,"consumed_artifact_count":len(ledger["artifacts"]),"all_supports_typed_and_terminal":True,"all_families_terminal_and_reconciled":True,"real_config_preflight":preflight};dump(output/"PREEXECUTION_VALIDATION.json",validation);return validation
def build_manifest(root:Path,output:Path):
    repo_paths=[]
    for directory,role in ((root/"analysis/sci_data_fusion_001","Phase B implementation and frozen configuration"),(root/"schemas","task schemas")):
        for item in sorted(directory.iterdir()):
            if item.is_file() and (directory.name=="sci_data_fusion_001" or item.name.startswith("sci_data_fusion_001_")):repo_paths.append({"scope":"repository","path":item.relative_to(root).as_posix(),"sha256":sha256(item),"decision_surface_role":role})
    package_paths=[]
    for item in sorted(output.iterdir()):
        if item.is_file() and item.name!="FREEZE_CONTENT_MANIFEST.json":package_paths.append({"scope":"package","path":item.name,"sha256":sha256(item),"decision_surface_role":"immutable pre-execution artifact"})
    dump(output/"FREEZE_CONTENT_MANIFEST.json",{"task_id":"SCI-DATA-FUSION-001","manifest_scope":"all repository and requested-output paths capable of changing Phase B result","files":repo_paths+package_paths})
