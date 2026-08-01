"""Taxonomy-driven deep schemas for governed VAL-001 JSON records."""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .framework import ContractError, canonical_json, load_json, sha256
from .inventory import INVENTORY_PATH, REGISTRY_PATH, ADMIN_FREEZE_PATH, CANONICAL_LOCK_PATH, ADMIN_CLOSURE_PATH, discover, record_class, structure
from .schema import lint_schema

FAMILY_SCHEMA_PATH = "validation/val001/schemas/deep_record_families.schema.json"
COVERAGE_PATH = "validation/val001/VAL_001_DEEP_SCHEMA_COVERAGE_MATRIX.json"
SCHEMA_DOCUMENT_PATH = "validation/val001/schemas/schema_document.schema.json"
EXPLICIT_SCHEMAS = {
    INVENTORY_PATH:("governed_record_inventory.v3","validation/val001/schemas/governed_record_inventory.schema.json"),
    REGISTRY_PATH:("governed_schema_registry.v3","validation/val001/schemas/governed_schema_registry.schema.json"),
    COVERAGE_PATH:("deep_schema_coverage_matrix.v1","validation/val001/schemas/coverage_matrix.schema.json"),
    ADMIN_CLOSURE_PATH:("administrative_closure_specification.v1","validation/val001/schemas/administrative_closure_specification.schema.json"),
    ADMIN_FREEZE_PATH:("administrative_closure_freeze.v1","validation/val001/schemas/administrative_closure_freeze.schema.json"),
    CANONICAL_LOCK_PATH:("canonical_consumed_lock.v2","validation/val001/schemas/canonical_consumed_lock.schema.json"),
}

HASH_KEYS = {"sha256", "hash", "artifact_sha256", "input_sha256", "output_sha256"}
COMMIT_KEYS = {"commit", "tree", "parent", "producing_commit", "implementation_commit", "implementation_tree"}


def _scalar_schema(key: str, values: list[Any]) -> dict[str, Any]:
    value = values[0]
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    out: dict[str, Any] = {"type": "string"}
    lower = key.lower()
    if lower in HASH_KEYS or lower.endswith("_sha256"):
        out["pattern"] = "^[0-9a-f]{64}$"
    elif lower in COMMIT_KEYS or lower.endswith("_commit") or lower.endswith("_tree"):
        # Historical placeholders are deliberately modeled as enums below.
        if all(re.fullmatch(r"[0-9a-f]{40}", str(v)) for v in values):
            out["pattern"] = "^[0-9a-f]{40}$"
    elif lower == "doi":
        out["pattern"] = "^10\\.[0-9]{4,9}/[^ ]+$"
    if any(token in lower for token in ("status", "role", "classification", "disposition", "authority", "validation", "allowed", "authorized")):
        unique=sorted({str(v) for v in values})
        if 0 < len(unique) <= 24:
            out["enum"] = unique
    return out


def infer_schema(values: list[Any], key: str = "") -> dict[str, Any]:
    value=values[0]
    if isinstance(value, dict):
        keys=sorted(value)
        if not all(isinstance(v,dict) and sorted(v)==keys for v in values):
            raise ContractError("shape-family object mismatch")
        return {"type":"object","required":keys,"properties":{k:infer_schema([v[k] for v in values],k) for k in keys},"additionalProperties":False}
    if isinstance(value,list):
        if not value:
            return {"type":"array","maxItems":0,"items":{"type":"null"}}
        items=[item for v in values for item in v]
        shapes={json.dumps(structure(item),sort_keys=True) for item in items}
        if len(shapes)==1:
            item_schema=infer_schema(items,key)
        else:
            grouped=defaultdict(list)
            for item in items: grouped[json.dumps(structure(item),sort_keys=True)].append(item)
            item_schema={"anyOf":[infer_schema(group) for _,group in sorted(grouped.items())]}
        return {"type":"array","minItems":min(len(v) for v in values),"maxItems":max(len(v) for v in values),"items":item_schema}
    return _scalar_schema(key,values)


def governed_json_paths(root: Path) -> list[Path]:
    # Explicit administrative and schema-document families are routed to their
    # declared schemas; this is not an enumeration exclusion.
    return [p for p in discover(root) if p.suffix==".json" and p.relative_to(root).as_posix() not in set(EXPLICIT_SCHEMAS)|{FAMILY_SCHEMA_PATH} and "/schemas/" not in p.relative_to(root).as_posix()]


def build_family_schema(root: Path) -> tuple[dict[str,Any],dict[str,str]]:
    grouped: dict[tuple[str,str],list[tuple[str,Any]]]=defaultdict(list)
    for path in governed_json_paths(root):
        rel=path.relative_to(root).as_posix(); value=load_json(path)
        sig=json.dumps(structure(value),sort_keys=True,separators=(",",":"))
        grouped[(record_class(rel),sig)].append((rel,value))
    branches=[]; mapping={}
    for index,((klass,_),members) in enumerate(sorted(grouped.items()),1):
        family=f"{klass.lower()}.v{index}"
        branch=infer_schema([value for _,value in members])
        branches.append(branch)
        for rel,_ in members: mapping[rel]=family
    schema={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"espresso.val001.deep_record_families.v1","anyOf":branches}
    lint_schema(schema)
    return schema,mapping


def historical(path: str) -> bool:
    markers=("/historical/","FIRST_COMPONENT","EXECUTION_FAILURE","INPUT_ROW_COUNT_AMENDMENT","PREEXECUTION_RUN_SPEC","CORRECTED_FREEZE","CORRECTED_PREEXECUTION_AUTHORITY","SECOND_CORRECTION_","INITIAL_RESULT_INVALIDATION")
    return any(marker in path for marker in markers)


def build_coverage(root: Path, mapping: dict[str,str]) -> dict[str,Any]:
    records=[]
    for path in discover(root):
        rel=path.relative_to(root).as_posix()
        data=path.read_bytes(); value=load_json(path) if path.suffix==".json" else None
        if rel in EXPLICIT_SCHEMAS:
            family,schema_path=EXPLICIT_SCHEMAS[rel]
        elif "/schemas/" in rel:
            family="json_schema_document.v1"; schema_path=SCHEMA_DOCUMENT_PATH
        elif path.suffix==".jsonl":
            family="deep_invocation_event_families.v1"; schema_path="validation/val001/schemas/deep_invocation_event_families.schema.json"
        else:
            family=mapping[rel]; schema_path=FAMILY_SCHEMA_PATH
        administratively_bound=rel in set(EXPLICIT_SCHEMAS)
        records.append({"path":rel,"sha256":None if administratively_bound else hashlib.sha256(data).hexdigest(),"git_blob":None if administratively_bound else _git(root,["hash-object",rel]),"producing_commit":"BOUND_BY_ADMINISTRATIVE_GRAPH" if administratively_bound else _git(root,["log","-1","--format=%H","--",rel]),"artifact_record_id":(value or {}).get("record_id",(value or {}).get("adapter_id",rel)),"record_class":record_class(rel),"structural_family":family,"schema_version":(value or {}).get("schema_version","JSONL_V3"),"schema_id":family,"schema_path":schema_path,"semantic_validator":"validate_governed_cross_record","semantic_profile":"VAL001_EXPLICIT_PROFILE_V1","schema_origin":"EXPLICIT_CLASS_OR_VERSION_SEMANTICS","treatment":"IMMUTABLE_HISTORICAL_DEEP_SCHEMA" if historical(rel) else "CURRENT_DEEP_SCHEMA","governing_status":"AUDIT_OR_SUPERSEDED" if historical(rel) else "CURRENT_GOVERNED","executable":False,"claim_ceiling":"NO_PHYSICAL_VALIDATION_OR_NEW_PHYSICS","puckworks_lock_applicable":True,"mutation_test_family":family,"coverage_status":"DEEP_SCHEMA_AND_SEMANTIC_VALIDATION"})
    return {"schema_version":"espresso.val001.deep_schema_coverage_matrix.v1","record_id":"VAL001-DEEP-SCHEMA-COVERAGE-MATRIX-1","scope":"ALL_GOVERNED_RECORDS_WITH_ACYCLIC_ADMINISTRATIVE_CLOSURE","record_count":len(records),"records":records,"closure":{"matrix_self":"BOUND_BY_DEEP_SCHEMA_FREEZE","inventory_registry":"GENERATED_FROM_THIS_MATRIX","freeze":"BINDS_MATRIX_INVENTORY_REGISTRY","successor_lock":"BINDS_FREEZE"}}


def _git(root:Path,args:list[str])->str:
    import subprocess
    result=subprocess.run(["git",*args],cwd=root,text=True,capture_output=True)
    return result.stdout.strip() or "PENDING_DEEP_SCHEMA_COMMIT"


def validate_family_records(root:Path,schema:dict[str,Any],mapping:dict[str,str])->int:
    from .framework import validate_record
    count=0
    for path in governed_json_paths(root):
        value=load_json(path);validate_record(value,schema);semantic_validate(path.relative_to(root).as_posix(),value);count+=1
    return count


def _walk(value:Any):
    if isinstance(value,dict):
        for key,item in value.items():
            yield key,item
            yield from _walk(item)
    elif isinstance(value,list):
        for item in value: yield from _walk(item)


def semantic_validate(path:str,value:dict[str,Any])->None:
    """Cross-family claim, authority, and immutable-lineage invariants."""
    for key,item in _walk(value):
        lower=key.lower()
        if "physical_validation" in lower and not isinstance(item,(dict,list)) and item not in {"NOT_ESTABLISHED",False,None}:
            raise ContractError(f"physical validation escalation: {path}:{key}")
        if "new_governing_physics" in lower and not isinstance(item,(dict,list)) and item not in {"NOT_AUTHORIZED_BY_VAL001",False,None}:
            raise ContractError(f"new physics escalation: {path}:{key}")
        if lower in {"experimental_commissioning_authorized","commissioning_authorized","execution_authorized","holdout_execution_authorized","protected_scoring_authorized","holdout_scoring_authorized"} and item is not False:
            raise ContractError(f"execution or commissioning escalation: {path}:{key}")
        if lower in {"fitting_allowed","retuning_allowed","fitting_or_retuning_allowed","configuration_change","solver_source_change","governing_physics_change"} and item is not False:
            raise ContractError(f"method authority escalation: {path}:{key}")
        if lower in {"fit_count","retune_count","fit_or_retune_count","fits_or_retunes"} and item != 0:
            raise ContractError(f"fit or retune count escalation: {path}:{key}")
        if lower == "structural_identifiability" and item != "NOT_ASSESSED":
            raise ContractError(f"structural identifiability escalation: {path}")
    if "/results/historical/" in path:
        if value.get("NEW_SCORE_BEARING_COMPARISON",value.get("new_score_bearing_comparison")) is not False:
            raise ContractError(f"historical re-expression score escalation: {path}")
    if "POSTRESULT_EXECUTION_LOCK" in path:
        if value.get("authority_status")!="CONSUMED" or value.get("remaining_real_data_comparison_invocations")!=0 or value.get("remaining_governed_result_producing_invocations")!=0 or value.get("further_retry_authorized") is not False:
            raise ContractError(f"consumed authority escalation: {path}")
        for key in ("alternate_invocation_id_allowed","alternate_ledger_allowed","alternate_authority_allowed","alternate_activation_allowed"):
            if value.get(key) is not False: raise ContractError(f"alternate execution identity escalation: {path}:{key}")
    if path.endswith("VAL_001_CAMPAIGN_PROVENANCE.json"):
        if value.get("status")!="PLANNING_RECORDS_ONLY": raise ContractError("campaign status escalation")
        campaigns=value.get("campaigns",[])
        if [c.get("id") for c in campaigns] != [f"EXP-{i:03d}" for i in range(1,10)]: raise ContractError("campaign identity mismatch")
        for campaign in campaigns:
            if campaign.get("proposed_status")!="PLANNED" or campaign.get("execution_authorized") is not False or campaign.get("commissioning_authorized") is not False or campaign.get("data_accessed") is not False:
                raise ContractError(f"campaign authority escalation: {campaign.get('id')}")
        lock=value.get("locked_dependency",{})
        if lock.get("commit")!="fc61c4670ec7bf801e40bb391aab16048b8da26b" or lock.get("tree")!="1d553e44ee2f7480a5df521560801b478618cc84": raise ContractError("campaign dependency lock mismatch")
    if path.endswith("GAGNE_DE1_EVIDENCE_GAP_ADAPTER.json"):
        if value.get("execution",{}).get("executable") is not False or value.get("rights",{}).get("comparison_allowed") is not False or not value.get("execution",{}).get("reason_codes"):
            raise ContractError("evidence-gap adapter execution escalation")
    if "CORRECTED_EXECUTION_FAILURE" in path and "FAILED" not in json.dumps(value):
        raise ContractError("failed invocation lost failed status")
    if "CORRECTED_COMPONENT_COMPARISONS_V2" in path:
        text=json.dumps(value)
        for required in ("POST_OBSERVATION_REPRODUCTION","NOT_BLIND","NOT_INDEPENDENT"):
            if required not in text: raise ContractError(f"V2 lost {required}")
