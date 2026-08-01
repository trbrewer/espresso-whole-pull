"""Zero-exclusion VAL-001 administrative binding closure."""
from __future__ import annotations
import json, subprocess
from pathlib import Path
from typing import Any
from .framework import ContractError, load_json, sha256, validate_record
from .inventory import (ADMIN_CLOSURE_PATH, ADMIN_FREEZE_PATH, CANONICAL_LOCK_PATH,
    INVENTORY_PATH, REGISTRY_PATH, build_inventory, discover, verify_inventory, verify_registry)
from .deep_schema import semantic_validate
from .schema import lint_schema

def _git(root:Path,*args:str)->str:
    p=subprocess.run(["git",*args],cwd=root,text=True,capture_output=True)
    if p.returncode: raise ContractError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout.strip()

def enumerate_governed(root:Path)->list[str]:
    return [p.relative_to(root).as_posix() for p in discover(root)]

def _binding_map(items:list[dict[str,Any]])->dict[str,str]:
    out={}
    for item in items:
        if item["path"] in out: raise ContractError(f"duplicate binding path: {item['path']}")
        out[item["path"]]=item["sha256"]
    return out

def validate_all_records(root:Path, inventory:dict[str,Any])->int:
    count=0
    for entry in inventory["records"]:
        path=root/entry["path"]
        if not path.exists(): raise ContractError(f"registered record missing: {entry['path']}")
        schema=load_json(root/entry["schema_path"]);lint_schema(schema)
        if path.suffix==".jsonl":
            lines=path.read_text(encoding="utf-8").splitlines()
            if not lines: raise ContractError("empty governed JSONL")
            for line in lines: validate_record(json.loads(line),schema)
        else:
            value=load_json(path);validate_record(value,schema);semantic_validate(entry["path"],value)
        count+=1
    return count

def verify_closure(root:Path, *, require_clean:bool=True)->dict[str,Any]:
    enumerated=enumerate_governed(root)
    inventory=load_json(root/INVENTORY_PATH);registry=load_json(root/REGISTRY_PATH)
    registered=[r["path"] for r in inventory["records"]]
    if len(registered)!=len(set(registered)): raise ContractError("duplicate inventory path")
    artifact_ids=[str(r["artifact_record_id"]) for r in inventory["records"]]
    duplicate_ids={x for x in artifact_ids if artifact_ids.count(x)>1}
    # Historical generations may intentionally retain an artifact ID only when
    # their paths are explicitly historical.
    for duplicate in duplicate_ids:
        paths=[r["path"] for r in inventory["records"] if str(r["artifact_record_id"])==duplicate]
        if not all("/historical/" in p for p in paths[1:]): raise ContractError(f"duplicate artifact record ID: {duplicate}")
    if enumerated!=sorted(registered):
        raise ContractError(f"zero-exclusion enumeration mismatch missing={sorted(set(enumerated)-set(registered))} extra={sorted(set(registered)-set(enumerated))}")
    verify_inventory(root,inventory);verify_registry(inventory,registry)
    validated=validate_all_records(root,inventory)
    freeze=load_json(root/ADMIN_FREEZE_PATH);lock=load_json(root/CANONICAL_LOCK_PATH)
    admin=_binding_map(freeze["administrative_bindings"]);ordinary=_binding_map(freeze["ordinary_record_bindings"])
    classes={}
    for entry in inventory["records"]:
        rel=entry["path"];kind=entry["binding_class"];classes[kind]=classes.get(kind,0)+1
        if kind=="ORDINARY_HASH_BOUND_RECORD":
            if entry["sha256"]!=sha256(root/rel) or ordinary.get(rel)!=entry["sha256"]: raise ContractError(f"ordinary binding mismatch: {rel}")
        elif kind=="BOUND_BY_ADMINISTRATIVE_FREEZE":
            if admin.get(rel)!=sha256(root/rel): raise ContractError(f"administrative freeze binding mismatch: {rel}")
        elif kind=="BOUND_BY_CANONICAL_LOCK":
            fb=lock.get("freeze_binding",{})
            if rel!=fb.get("path") or sha256(root/rel)!=fb.get("sha256"): raise ContractError("canonical lock freeze binding mismatch")
            commit=fb.get("commit","");tree=fb.get("tree","")
            if _git(root,"rev-parse",f"{commit}^{{tree}}")!=tree: raise ContractError("freeze commit/tree mismatch")
            blob=_git(root,"show",f"{commit}:{rel}").encode()
            import hashlib
            if hashlib.sha256(blob).hexdigest()!=fb.get("sha256"): raise ContractError("freeze bytes at commit mismatch")
        elif kind=="BOUND_BY_FINAL_GIT_TREE":
            if rel!=CANONICAL_LOCK_PATH: raise ContractError("noncanonical final Git-tree terminal")
            tracked_blob=_git(root,"rev-parse",f"HEAD:{rel}")
            working_blob=_git(root,"hash-object",rel)
            if tracked_blob!=working_blob: raise ContractError("canonical lock working bytes differ from HEAD")
        else: raise ContractError(f"unknown binding class: {kind}")
    if classes.get("BOUND_BY_FINAL_GIT_TREE")!=1: raise ContractError("terminal external root count is not one")
    if require_clean and _git(root,"status","--porcelain"): raise ContractError("administrative closure requires clean working tree")
    return {"enumerated":len(enumerated),"registered":len(registered),"validated":validated,"binding_classes":classes,"cycles":0,"orphans":0,"terminal_external_roots":1,"head":_git(root,"rev-parse","HEAD"),"tree":_git(root,"rev-parse","HEAD^{tree}")}
