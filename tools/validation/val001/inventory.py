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
ADMIN_FREEZE_PATH = "validation/val001/contracts/VAL_001_ADMINISTRATIVE_CLOSURE_FREEZE.json"
CANONICAL_LOCK_PATH = "validation/val001/contracts/VAL_001_POSTRESULT_EXECUTION_LOCK.json"
ADMIN_CLOSURE_PATH = "validation/val001/VAL_001_ADMINISTRATIVE_CLOSURE_SPECIFICATION.json"
SPEC_REGISTRY = "validation/val001/VAL_001_EXPLICIT_SCHEMA_SPECIFICATION_REGISTRY.json"
ADMIN_BOUND = {INVENTORY_PATH, REGISTRY_PATH, COVERAGE_PATH, ADMIN_CLOSURE_PATH}

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
    # Enumeration is deliberately unconditional: administrative closure is a
    # binding relationship, never a reason to omit a governed record.
    return sorted(path for path in base.rglob("*") if path.is_file() and path.suffix in {".json",".jsonl"})

def build_inventory(root: Path) -> dict[str,Any]:
    from .explicit_semantics import load_policy
    _,_,specs,bindings,_=load_policy(root)
    records=[]
    for path in discover(root):
        rel=path.relative_to(root).as_posix(); data=path.read_bytes()
        if path.suffix==".json": value=load_json(path); artifact_record_id=value.get("record_id",value.get("adapter_id",value.get("task",rel)))
        else: value=[json.loads(line) for line in path.read_text().splitlines()]; artifact_record_id="VAL001-INVOCATION-JOURNAL"
        # The inventory identity is path-derived and therefore unique even when
        # immutable historical generations legitimately retain one artifact ID.
        record_id="INV-"+hashlib.sha256(rel.encode("utf-8")).hexdigest()[:20].upper()
        binding=bindings.get(rel)
        if binding is None: raise ContractError(f"explicit schema registry omits {rel}")
        specification=specs[binding["specification_id"]]
        schema_id=specification["schema_id"];schema_path=SPEC_REGISTRY
        treatment=binding["treatment"]
        tracked=git_value(root,["ls-files","--error-unmatch",rel],"")
        blob=git_value(root,["hash-object",rel],hashlib.sha1(data).hexdigest())
        producing=git_value(root,["log","-1","--format=%H","--",rel],"PENDING_COMPLETION_COMMIT") if tracked else "PENDING_COMPLETION_COMMIT"
        if rel in ADMIN_BOUND:
            binding_class="BOUND_BY_ADMINISTRATIVE_FREEZE"; bound_sha=None; bound_blob=None; binder=ADMIN_FREEZE_PATH; producing="BOUND_BY_BINDER"
        elif rel==ADMIN_FREEZE_PATH:
            binding_class="BOUND_BY_CANONICAL_LOCK"; bound_sha=None; bound_blob=None; binder=CANONICAL_LOCK_PATH; producing="BOUND_BY_BINDER"
        elif rel==CANONICAL_LOCK_PATH:
            binding_class="BOUND_BY_FINAL_GIT_TREE"; bound_sha=None; bound_blob=None; binder="FINAL_GIT_HEAD_TREE"; producing="BOUND_BY_FINAL_GIT_TREE"
        else:
            binding_class="ORDINARY_HASH_BOUND_RECORD"; bound_sha=hashlib.sha256(data).hexdigest(); bound_blob=blob; binder=ADMIN_FREEZE_PATH
        signature=hashlib.sha256(canonical_json({"binding_class":binding_class,"schema_id":schema_id})).hexdigest() if binding_class!="ORDINARY_HASH_BOUND_RECORD" else hashlib.sha256(canonical_json(structure(value))).hexdigest()
        records.append({"path":rel,"sha256":bound_sha,"git_blob":bound_blob,"producing_commit":producing,"record_id":record_id,"artifact_record_id":artifact_record_id,"record_class":binding["record_class"],"schema_id":schema_id,"schema_version":value.get("schema_version","JSONL_V3") if isinstance(value,dict) else "JSONL_V3","schema_path":schema_path,"semantic_validator":"validate_profile_dispatch","semantic_profile":binding["semantic_profile_id"],"schema_origin":specification["origin"],"binding_class":binding_class,"binder":binder,"treatment":treatment,"current":binding["current"],"executable":False,"audit_only":binding["audit_only"],"mutability":"IMMUTABLE_AFTER_ADMINISTRATIVE_FREEZE","governing":rel.endswith("INVOCATION_SUMMARY_V2.json"),"superseded":("historical/" in rel or "FIRST_COMPONENT" in rel or "EXECUTION_FAILURE" in rel),"claim_ceiling":"NO_PHYSICAL_VALIDATION_OR_NEW_PHYSICS","puckworks_lock_applicable":rel.startswith("validation/val001/"),"source_access_role":"NO_SOURCE_ACCESS" if "ACCESS_LOG" not in rel else "SOURCE_ACCESS_AUDIT","static_validation":"REQUIRED","structure_signature_sha256":signature})
    paths=[r["path"] for r in records]; ids=[str(r["record_id"]) for r in records]
    if len(paths)!=len(set(paths)): raise ContractError("duplicate inventory path")
    duplicates={item for item in ids if ids.count(item)>1 and item not in {"VAL-001"}}
    if duplicates: raise ContractError(f"duplicate record IDs: {sorted(duplicates)}")
    return {"schema_version":"espresso.val001.governed_record_inventory.v3","record_id":"VAL001-GOVERNED-RECORD-INVENTORY-3","scope":"EVERY_JSON_AND_JSONL_UNDER_VALIDATION_VAL001_ZERO_EXCLUSIONS","record_count":len(records),"records":records,"closure":{"enumeration_exclusions":0,"administrative_freeze":ADMIN_FREEZE_PATH,"canonical_lock":CANONICAL_LOCK_PATH,"terminal_external_root":"FINAL_GIT_HEAD_TREE","sidecar_primary_validation_count":0}}

def verify_inventory(root: Path, inventory: dict[str,Any]) -> None:
    expected=build_inventory(root); observed={r["path"]:r for r in inventory["records"]}; actual={r["path"]:r for r in expected["records"]}
    if set(observed)!=set(actual): raise ContractError(f"inventory coverage mismatch missing={sorted(set(actual)-set(observed))} extra={sorted(set(observed)-set(actual))}")
    for path,item in observed.items():
        for key in ("sha256","git_blob","record_class","schema_path","treatment","structure_signature_sha256","binding_class","binder"):
            if item[key]!=actual[path][key]: raise ContractError(f"inventory mismatch {path}:{key}")

def inventory_bytes(root: Path) -> bytes: return canonical_json(build_inventory(root))

def build_registry(inventory: dict[str, Any]) -> dict[str, Any]:
    """Create one explicit, non-prefix registry entry per inventoried record."""
    records=[]
    for item in inventory["records"]:
        records.append({key:item[key] for key in (
            "path","sha256","record_id","artifact_record_id","record_class",
            "schema_id","schema_version","schema_path","semantic_validator","semantic_profile","schema_origin","binding_class","binder",
            "treatment","current","executable","audit_only","claim_ceiling",
            "puckworks_lock_applicable","static_validation","structure_signature_sha256"
        )})
    return {
        "schema_version":"espresso.val001.governed_schema_registry.v3",
        "record_id":"VAL001-GOVERNED-SCHEMA-REGISTRY-3",
        "coverage":"EXPLICIT_ONE_RECORD_ONE_TREATMENT_NO_PREFIX_OR_CATCH_ALL",
        "record_count":len(records),
        "records":records,
        "closure":{
            "enumeration_exclusions":0,
            "administrative_records":"DIRECTLY_REGISTERED_AND_VALIDATED",
            "final_lock":"SOLE_FINAL_GIT_TREE_TERMINAL"
        }
    }

def verify_registry(inventory: dict[str,Any], registry: dict[str,Any]) -> None:
    expected=build_registry(inventory)
    if registry != expected:
        raise ContractError("governed schema registry is not the deterministic inventory projection")
