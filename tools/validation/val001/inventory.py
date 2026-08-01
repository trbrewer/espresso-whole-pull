"""Deterministic exhaustive inventory for VAL-001 machine-readable records."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
from typing import Any
from .framework import ContractError, canonical_json, load_json, sha256

INVENTORY_PATH = "validation/val001/VAL_001_GOVERNED_RECORD_INVENTORY.json"
REGISTRY_PATH = "validation/val001/VAL_001_GOVERNED_SCHEMA_REGISTRY.json"

COVERAGE_PATH = "validation/val001/VAL_001_DEEP_SCHEMA_COVERAGE_MATRIX.json"
FAMILY_SCHEMA_PATH = "validation/val001/schemas/deep_record_families.schema.json"
SCHEMA_DOCUMENT_PATH = "validation/val001/schemas/schema_document.schema.json"

def structure(value: Any) -> Any:
    if isinstance(value, dict): return {key: structure(value[key]) for key in sorted(value)}
    if isinstance(value, list): return [structure(item) for item in value]
    if value is None: return "null"
    if isinstance(value, bool): return "boolean"
    if isinstance(value, int): return "integer"
    if isinstance(value, float): return "number"
    return "string"

def record_class(path: str) -> str:
    name=Path(path).name
    if "/schemas/" in path: return "SCHEMA"
    if path.endswith(".jsonl"): return "INVOCATION_JOURNAL"
    for token,klass in [("ADAPTER","SOURCE_ADAPTER"),("RESULT","RESULT_OR_REEXPRESSION"),("FREEZE","FREEZE"),("AUTHORITY","AUTHORITY"),("ACTIVATION","ACTIVATION"),("LOCK","EXECUTION_LOCK"),("CORRECTION","CORRECTION"),("AMENDMENT","AMENDMENT_INVALIDATION"),("INVENTORY","EVIDENCE_OR_RECORD_INVENTORY"),("LEDGER","LEDGER"),("CAMPAIGN","CAMPAIGN_PROVENANCE"),("ACCESS_LOG","SOURCE_ACCESS_LOG"),("MANIFEST","EXTERNAL_ARTIFACT_MANIFEST"),("MECHANISM","MECHANISM_DISCRIMINATION"),("RANKED","RANKED_REQUESTS"),("SENSITIVITY","SENSITIVITY_IDENTIFIABILITY")]:
        if token in name: return klass
    return "GOVERNANCE_RECORD"

def git_value(root: Path, args: list[str], fallback: str) -> str:
    result=subprocess.run(["git",*args],cwd=root,text=True,capture_output=True)
    return result.stdout.strip() if result.returncode==0 and result.stdout.strip() else fallback

def discover(root: Path) -> list[Path]:
    base=root/"validation/val001"
    # These three canonical closure records form a directed binding chain:
    # inventory/registry -> completion freeze -> final consumed lock. Including
    # their own mutable successor bytes would require an impossible hash cycle.
    self_bound={INVENTORY_PATH,REGISTRY_PATH,
        "validation/val001/contracts/VAL_001_FINAL_HARDENING_COMPLETION_FREEZE.json",
        "validation/val001/contracts/VAL_001_POSTRESULT_EXECUTION_LOCK.json"}
    return sorted(path for path in base.rglob("*") if path.is_file() and path.suffix in {".json",".jsonl"} and path.relative_to(root).as_posix() not in self_bound)

def build_inventory(root: Path) -> dict[str,Any]:
    coverage_path=root/COVERAGE_PATH
    coverage_by_path={r["path"]:r for r in load_json(coverage_path)["records"]} if coverage_path.exists() else {}
    records=[]
    for path in discover(root):
        rel=path.relative_to(root).as_posix(); data=path.read_bytes()
        if path.suffix==".json": value=load_json(path); artifact_record_id=value.get("record_id",value.get("adapter_id",value.get("task",rel)))
        else: value=[json.loads(line) for line in path.read_text().splitlines()]; artifact_record_id="VAL001-INVOCATION-JOURNAL"
        # The inventory identity is path-derived and therefore unique even when
        # immutable historical generations legitimately retain one artifact ID.
        record_id="INV-"+hashlib.sha256(rel.encode("utf-8")).hexdigest()[:20].upper()
        if rel==COVERAGE_PATH:
            schema_id="espresso.val001.deep_schema_coverage_matrix.v1";schema_path="validation/val001/schemas/coverage_matrix.schema.json";treatment="CURRENT_DEEP_SCHEMA"
        elif "/schemas/" in rel:
            schema_id="espresso.val001.schema_document.v1";schema_path=SCHEMA_DOCUMENT_PATH;treatment="CURRENT_DEEP_SCHEMA"
        elif path.suffix==".jsonl":
            schema_id="espresso.val001.deep_invocation_event_families.v1";schema_path="validation/val001/schemas/deep_invocation_event_families.schema.json";treatment="IMMUTABLE_HISTORICAL_DEEP_SCHEMA"
        else:
            item=coverage_by_path.get(rel)
            if item is None: raise ContractError(f"coverage matrix omits {rel}")
            schema_id=item["schema_id"];schema_path=item["schema_path"];treatment=item["treatment"]
        tracked=git_value(root,["ls-files","--error-unmatch",rel],"")
        blob=git_value(root,["hash-object",rel],hashlib.sha1(data).hexdigest())
        producing=git_value(root,["log","-1","--format=%H","--",rel],"PENDING_COMPLETION_COMMIT") if tracked else "PENDING_COMPLETION_COMMIT"
        records.append({"path":rel,"sha256":hashlib.sha256(data).hexdigest(),"git_blob":blob,"producing_commit":producing,"record_id":record_id,"artifact_record_id":artifact_record_id,"record_class":record_class(rel),"schema_id":schema_id,"schema_version":value.get("schema_version","JSONL_V3") if isinstance(value,dict) else "JSONL_V3","schema_path":schema_path,"semantic_validator":"VALIDATE_DEEP_AND_CROSS_RECORD","treatment":treatment,"current":treatment=="CURRENT_DEEP_SCHEMA","executable":False,"audit_only":treatment!="CURRENT_DEEP_SCHEMA","mutability":"IMMUTABLE_AFTER_DEEP_SCHEMA_FREEZE","governing":rel.endswith("INVOCATION_SUMMARY_V2.json"),"superseded":("historical/" in rel or "FIRST_COMPONENT" in rel or "EXECUTION_FAILURE" in rel),"claim_ceiling":"NO_PHYSICAL_VALIDATION_OR_NEW_PHYSICS","puckworks_lock_applicable":rel.startswith("validation/val001/"),"source_access_role":"NO_SOURCE_ACCESS" if "ACCESS_LOG" not in rel else "SOURCE_ACCESS_AUDIT","static_validation":"REQUIRED","structure_signature_sha256":hashlib.sha256(canonical_json(structure(value))).hexdigest()})
    paths=[r["path"] for r in records]; ids=[str(r["record_id"]) for r in records]
    if len(paths)!=len(set(paths)): raise ContractError("duplicate inventory path")
    duplicates={item for item in ids if ids.count(item)>1 and item not in {"VAL-001"}}
    if duplicates: raise ContractError(f"duplicate record IDs: {sorted(duplicates)}")
    return {"schema_version":"espresso.val001.governed_record_inventory.v2","record_id":"VAL001-GOVERNED-RECORD-INVENTORY-2","scope":"ALL_JSON_AND_JSONL_UNDER_VALIDATION_VAL001_WITH_DIRECTED_CLOSURE","record_count":len(records),"records":records,"closure":{"inventory_self":"BOUND_BY_DEEP_SCHEMA_FREEZE_AVOID_SELF_HASH","registry_self":"BOUND_BY_DEEP_SCHEMA_FREEZE_AVOID_SELF_HASH","canonical_consumed_lock":"BINDS_DEEP_SCHEMA_FREEZE_INVENTORY_AND_REGISTRY_AS_CHAIN_TERMINUS","deep_schema_freeze":"BINDS_INVENTORY_REGISTRY_AND_COVERAGE","sidecar_primary_validation_count":0}}

def verify_inventory(root: Path, inventory: dict[str,Any]) -> None:
    expected=build_inventory(root); observed={r["path"]:r for r in inventory["records"]}; actual={r["path"]:r for r in expected["records"]}
    if set(observed)!=set(actual): raise ContractError(f"inventory coverage mismatch missing={sorted(set(actual)-set(observed))} extra={sorted(set(observed)-set(actual))}")
    for path,item in observed.items():
        for key in ("sha256","git_blob","record_class","schema_path","treatment","structure_signature_sha256"):
            if item[key]!=actual[path][key]: raise ContractError(f"inventory mismatch {path}:{key}")

def inventory_bytes(root: Path) -> bytes: return canonical_json(build_inventory(root))

def build_registry(inventory: dict[str, Any]) -> dict[str, Any]:
    """Create one explicit, non-prefix registry entry per inventoried record."""
    records=[]
    for item in inventory["records"]:
        records.append({key:item[key] for key in (
            "path","sha256","record_id","artifact_record_id","record_class",
            "schema_id","schema_version","schema_path","semantic_validator",
            "treatment","current","executable","audit_only","claim_ceiling",
            "puckworks_lock_applicable","static_validation","structure_signature_sha256"
        )})
    return {
        "schema_version":"espresso.val001.governed_schema_registry.v2",
        "record_id":"VAL001-GOVERNED-SCHEMA-REGISTRY-2",
        "coverage":"EXPLICIT_ONE_RECORD_ONE_TREATMENT_NO_PREFIX_OR_CATCH_ALL",
        "record_count":len(records),
        "records":records,
        "closure":{
            "registry_self":"BOUND_BY_COMPLETION_FREEZE_AVOID_SELF_HASH",
            "inventory":"EXHAUSTIVE_EXCEPT_INVENTORY_SELF",
            "final_lock":"BINDS_COMPLETION_FREEZE_REGISTRY_AND_INVENTORY"
        }
    }

def verify_registry(inventory: dict[str,Any], registry: dict[str,Any]) -> None:
    expected=build_registry(inventory)
    if registry != expected:
        raise ContractError("governed schema registry is not the deterministic inventory projection")
