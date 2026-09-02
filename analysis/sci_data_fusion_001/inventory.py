from __future__ import annotations
import csv,json
from pathlib import Path
SCREEN_VOCABULARY={"MATCHED_DETAILED_SUPPORT_CANDIDATE","MATCHED_CONTEXT_OR_OPERATOR_ONLY","MATCHED_STRESS_OR_SHAPE_ONLY","MATCHED_BUT_UNQUALIFIED_SUCCESSOR_ONLY","MATCHED_BUT_DATA_UNAVAILABLE","MATCHED_BUT_RIGHTS_BLOCKED","EXCLUDED_NO_MATCHING_CANONICAL_QUANTITY","EXCLUDED_NO_EXISTING_EWP_CONSUMER","EXCLUDED_REQUIRES_NEW_COMPONENT_INVESTIGATION","EXCLUDED_DUPLICATE_LINEAGE","EXCLUDED_ALREADY_EXHAUSTED_FOR_NAMED_DECISION"}
def manifest_rows(path:Path)->list[dict]:
    with path.open(newline="") as stream:return list(csv.DictReader(stream))
def scan_registered_families(puckworks:Path,rules:dict)->tuple[list[dict],list[dict]]:
    index=json.loads((puckworks/"puckworks/data/LOCAL_CORPUS_FAMILY_INDEX.json").read_text()); register=json.loads((puckworks/"puckworks/data/AVAILABLE_DATA_REGISTER.json").read_text()); manifest=manifest_rows(puckworks/"puckworks/data/MANIFEST.csv")
    manifest_by_id={row["dataset_id"]:row for row in manifest}; register_by_lower={row["family_id"].lower():row for row in register["families"]}; families=index.get("families",[])
    if len(families)!=index.get("material_family_count") or len(families)!=index.get("mapped_or_registered_family_count"):raise ValueError("family-index declared counts do not reconcile")
    ids=[row["family_id"] for row in families]
    if len(ids)!=len(set(ids)):raise ValueError("duplicate family in exact family index")
    screens,datasets=[],[]
    default={"quantity_ids":[],"match_basis":"no accepted component mapping or existing EWP consumer","disposition":"EXCLUDED_NO_MATCHING_CANONICAL_QUANTITY","terminal_reason":"NO_FROZEN_MATCH"}
    for family in sorted(families,key=lambda row:row["family_id"]):
        family_id=family["family_id"]; rule=rules.get(family_id,default)
        if rule["disposition"] not in SCREEN_VOCABULARY:raise ValueError(f"unknown screening disposition for {family_id}")
        dataset_ids=family.get("manifest_dataset_ids",[]); missing=[item for item in dataset_ids if item not in manifest_by_id]
        if missing:raise ValueError(f"unregistered manifest datasets for {family_id}: {missing}")
        aliases={alias.lower() for alias in family.get("aliases",[])}; registered=register_by_lower.get(family_id.lower()) or next((row for key,row in register_by_lower.items() if key in aliases),None)
        if registered is None and "AVAILABLE_DATA_REGISTER:G10_LIQUOR_RHEOLOGY" in family.get("source_registration",""):registered=register_by_lower.get("g10_liquor_rheology")
        if registered is None:raise ValueError(f"family absent from available-data register: {family_id}")
        screens.append({"family_id":family_id,"source_registration":family.get("source_registration"),"manifest_dataset_ids":dataset_ids,"model_chain_stages":family.get("model_chain_stages",[]),"strongest_current_uses":family.get("strongest_current_uses",[]),"raw_access_status":family.get("raw_access_status","UNKNOWN"),"rights_access_summary":family.get("rights_access_status",[]),"last_qualified_task":family.get("last_qualified_task","UNKNOWN"),"potentially_matching_canonical_quantity_ids":rule["quantity_ids"],"match_basis":rule["match_basis"],"screening_disposition":rule["disposition"],"terminal_reason":rule["terminal_reason"],"detailed_support_record_count":rule.get("support_count",0)})
        for dataset_id in dataset_ids:
            item=manifest_by_id[dataset_id]; datasets.append({"family_id":family_id,"dataset_id":dataset_id,"manifest_source_card":item["source_card"],"manifest_source_artifact":item["source_artifact"],"license_access":item["license_access"],"manifest_verified":True})
    return screens,datasets
def validate_support_inventory(records:list[dict])->None:
    ids=[row.get("support_id") for row in records]
    if any(not item for item in ids) or len(ids)!=len(set(ids)):raise ValueError("support IDs must be present and unique")
    for row in records:
        if not row.get("frozen_role") or not row.get("terminal_reason"):raise ValueError(f"support lacks terminal role: {row.get('support_id')}")
        if row.get("qualified_support") and row.get("originating_task_id") is None:raise ValueError("unqualified registry entry promoted to qualified support")
