import csv,hashlib,json
from pathlib import Path
from .authority import AuthorityError,sha256,verify_consumed,verify_frozen_ewp,verify_puckworks
from .inventory import scan_registered_families,validate_support_inventory
FIELDS=["support_id","originating_task_id","family_id","dataset_ids","source_publication_identity","source_artifact_path","source_artifact_sha256","lineage_id","correlation_group_id","laboratory_identity","apparatus_identity","coffee_lot_roast","grinder_preparation_compaction","geometry","ewp_calibration_independence","independence_relative_to_candidates","source_internal_validation","target_exposed","consumed_comparison_conflict","rights_status","canonical_quantity_id","native_quantity","value_representation","source_field_or_extraction_path","native_units","canonical_units","conversion_chain","basis","reference_state","physical_state","spatial_support","temporal_support","population_regime","observation_operator","replicate_unit","uncertainty_statistic","uncertainty_meaning","interval_extraction_rule","ewp_consumer","frozen_role","terminal_reason"]
def dump(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")
def csv_dump(path,rows,fields):
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n");writer.writeheader()
        for row in rows:writer.writerow({key:json.dumps(row.get(key),sort_keys=True) if isinstance(row.get(key),(list,dict)) else row.get(key) for key in fields})
def enrich_supports(root,records,rules,manifest_ids):
    rule_by_id={row["support_id"]:row for row in rules};unknown="UNKNOWN_NOT_INFERRED";result=[]
    for source in records:
        row={key:source.get(key,unknown) for key in FIELDS};row.update(source)
        for dataset_id in row.get("dataset_ids",[]):
            if dataset_id not in manifest_ids:raise AuthorityError(f"support references unregistered dataset: {dataset_id}")
        path=row.get("source_artifact_path")
        if path and path!=unknown:
            row["source_artifact_sha256"]=sha256(root/path)
        rule=rule_by_id.get(row["support_id"]);row["source_field_or_extraction_path"]=rule and {"minimum_json_path":rule["minimum_json_path"],"maximum_json_path":rule["maximum_json_path"]};row["interval_extraction_rule"]=rule and rule["interval_semantics"]
        row.setdefault("interval",None);row.setdefault("provenance_complete",False);row.setdefault("rights_permit_analysis",False);row.setdefault("target_exposed",False);row.setdefault("source_internal_validation",False);row.setdefault("consumed_comparison_conflict",False);result.append(row)
    validate_support_inventory(result);return sorted(result,key=lambda item:item["support_id"])
def generate(root:Path,puckworks:Path,output:Path):
    authority=json.loads((output/"AUTHORITY.json").read_text());ewp=verify_frozen_ewp(root,authority);puck=verify_puckworks(puckworks,authority["puckworks"]);ledger=json.loads((output/"CONSUMED_RESULT_ARTIFACTS.json").read_text());verify_consumed(root,ledger)
    rules=json.loads((root/"analysis/sci_data_fusion_001/family_screen_rules.json").read_text());families,datasets=scan_registered_families(puckworks,rules);manifest_ids={row["dataset_id"] for row in datasets}
    extraction=json.loads((root/"analysis/sci_data_fusion_001/support_extraction_rules.json").read_text())["rules"]
    for rule in extraction:
        if sha256(root/rule["artifact_path"])!=rule["artifact_sha256"]:raise AuthorityError(f"extraction authority mismatch: {rule['support_id']}")
    source=json.loads((root/"analysis/sci_data_fusion_001/support_inventory.json").read_text());supports=enrich_supports(root,source["records"],extraction,manifest_ids)
    contract=json.loads((root/"analysis/sci_data_fusion_001/task_contract_template.json").read_text());freeze_inputs=json.loads((root/"analysis/sci_data_fusion_001/freeze_inputs.json").read_text());execution=json.loads((root/"analysis/sci_data_fusion_001/execution_plan.json").read_text());dump(output/"TASK_CONTRACT.json",contract);dump(output/"CANONICAL_QUANTITY_REGISTER.json",{"quantities":freeze_inputs["canonical_quantities"]});dump(output/"CANDIDATE_SUPPORT_FREEZE.json",{"support_candidates":supports,"pairwise_gate_contracts":execution["pairwise_gate_contracts"]})
    dump(output/"PUCKWORKS_FAMILY_SCREEN.json",{"declared_family_count":len(families),"screened_family_count":len(families),"families":families});csv_dump(output/"PUCKWORKS_FAMILY_SCREEN.csv",families,list(families[0]));csv_dump(output/"PUCKWORKS_DATASET_SCREEN.csv",datasets,list(datasets[0]));dump(output/"SOURCE_SUPPORT_INVENTORY.json",{"records":supports});csv_dump(output/"SOURCE_SUPPORT_INVENTORY.csv",supports,FIELDS);dump(output/"SUPPORT_EXTRACTION_RULES.json",{"rules":extraction});dump(output/"LINEAGE_CORRELATION_REGISTER.json",{"groups":[{"lineage_id":a,"correlation_group_id":b} for a,b in sorted({(row.get("lineage_id"),row.get("correlation_group_id")) for row in supports if row.get("lineage_id") not in (None,"UNKNOWN_NOT_INFERRED")},key=str)]});dump(output/"EXECUTION_PLAN.json",json.loads((root/"analysis/sci_data_fusion_001/execution_plan.json").read_text()));dump(output/"AUDIT_RECORD_SCHEMA.json",json.loads((root/"schemas/sci_data_fusion_001_audit_record.schema.json").read_text()))
    validation={"status":"PASS","real_phase_b_executed":False,"family_count":len(families),"dataset_reference_count":len(datasets),"detailed_support_count":len(supports),"authority":ewp,"puckworks":puck,"consumed_artifact_count":len(ledger["artifacts"]),"all_supports_terminal":True,"all_families_terminal":True};dump(output/"PREEXECUTION_VALIDATION.json",validation);return validation
def build_manifest(root:Path,output:Path):
    roles={"analysis/sci_data_fusion_001":"Phase B implementation and frozen configuration","schemas/sci_data_fusion_001_audit_record.schema.json":"audit gate schema","docs/analysis/sci_data_fusion_001":"committed pre-execution decision surface"};paths=[]
    for prefix,role in roles.items():
        path=root/prefix
        candidates=[path] if path.is_file() else sorted(item for item in path.iterdir() if item.is_file())
        for item in candidates:
            relative=item.relative_to(root).as_posix()
            if relative.endswith("FREEZE_CONTENT_MANIFEST.json"):continue
            paths.append({"path":relative,"sha256":sha256(item),"decision_surface_role":role})
    dump(output/"FREEZE_CONTENT_MANIFEST.json",{"task_id":"SCI-DATA-FUSION-001","manifest_scope":"all committed paths capable of changing Phase B scientific result","files":sorted(paths,key=lambda row:row["path"])})
