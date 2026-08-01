"""Zero-exclusion VAL-001 administrative binding closure."""
from __future__ import annotations
import json, subprocess
from pathlib import Path
from typing import Any
from .framework import ContractError, load_json, sha256, validate_record
from .inventory import (ADMIN_CLOSURE_PATH, ADMIN_FREEZE_PATH, CANONICAL_LOCK_PATH,
    INVENTORY_PATH, REGISTRY_PATH, build_inventory, discover, verify_inventory, verify_registry)
from .explicit_semantics import validate_profile_dispatch,explicit_schema_for
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

def validate_binding_graph(inventory:dict[str,Any], freeze:dict[str,Any],
                           lock:dict[str,Any], specification:dict[str,Any])->dict[str,int]:
    """Build and traverse the finite record→freeze→lock→Git-tree graph."""
    expected_edges={"ORDINARY_HASH_BOUND_RECORD->ADMINISTRATIVE_FREEZE",
        "BOUND_BY_ADMINISTRATIVE_FREEZE->ADMINISTRATIVE_FREEZE",
        "BOUND_BY_CANONICAL_LOCK->CANONICAL_LOCK",
        "BOUND_BY_FINAL_GIT_TREE->FINAL_GIT_HEAD_TREE"}
    if set(specification.get("valid_edges",[]))!=expected_edges:
        raise ContractError("administrative binding edge policy mismatch")
    freeze_path=specification.get("administrative_freeze");lock_path=specification.get("canonical_lock")
    if freeze_path!=ADMIN_FREEZE_PATH or lock_path!=CANONICAL_LOCK_PATH:
        raise ContractError("administrative binder identity mismatch")
    ordinary=set(_binding_map(freeze["ordinary_record_bindings"]));admin=set(_binding_map(freeze["administrative_bindings"]))
    graph:dict[str,str]={entry["path"]:entry.get("binder","") for entry in inventory["records"]}
    # Traverse the declared graph before enforcing class-specific binder rules,
    # so a genuine malicious cycle is detected as a cycle rather than hidden by
    # a policy precheck.
    for start in graph:
        seen=set();node=start
        while node in graph:
            if node in seen: raise ContractError(f"administrative binding cycle at {node}")
            seen.add(node);node=graph[node]
        if node!="FINAL_GIT_HEAD_TREE": raise ContractError(f"orphan binding terminus: {node}")
    for entry in inventory["records"]:
        path,kind=entry["path"],entry["binding_class"]
        if kind=="ORDINARY_HASH_BOUND_RECORD":
            if path not in ordinary: raise ContractError(f"orphan ordinary record: {path}")
            if entry.get("binder")!=freeze_path: raise ContractError(f"ordinary binder mismatch: {path}")
        elif kind=="BOUND_BY_ADMINISTRATIVE_FREEZE":
            if path not in admin: raise ContractError(f"orphan administrative record: {path}")
            if entry.get("binder")!=freeze_path: raise ContractError(f"administrative binder mismatch: {path}")
        elif kind=="BOUND_BY_CANONICAL_LOCK":
            if path!=freeze_path: raise ContractError("non-freeze canonical-lock binding")
            if entry.get("binder")!=lock_path: raise ContractError("freeze binder mismatch")
        elif kind=="BOUND_BY_FINAL_GIT_TREE":
            if path!=lock_path: raise ContractError("noncanonical terminal record")
            if entry.get("binder")!="FINAL_GIT_HEAD_TREE": raise ContractError("terminal binder mismatch")
    expected_ordinary={e["path"] for e in inventory["records"] if e["binding_class"]=="ORDINARY_HASH_BOUND_RECORD"}
    expected_admin={e["path"] for e in inventory["records"] if e["binding_class"]=="BOUND_BY_ADMINISTRATIVE_FREEZE"}
    if ordinary!=expected_ordinary or admin!=expected_admin: raise ContractError("binding set has orphan or extra record")
    roots=0
    roots=len({target for target in graph.values() if target=="FINAL_GIT_HEAD_TREE"})
    if roots!=1: raise ContractError("terminal external root count is not one")
    return {"cycles":0,"orphans":0,"terminal_external_roots":roots}

def validate_all_records(root:Path, inventory:dict[str,Any])->int:
    count=0
    for entry in inventory["records"]:
        path=root/entry["path"]
        if not path.exists(): raise ContractError(f"registered record missing: {entry['path']}")
        schema=explicit_schema_for(root,entry["path"]);lint_schema(schema)
        if path.suffix==".jsonl":
            lines=path.read_text(encoding="utf-8").splitlines()
            if not lines: raise ContractError("empty governed JSONL")
            for line in lines:
                event=json.loads(line);validate_record(event,schema)
                validate_profile_dispatch(root,entry["path"],event,entry)
        else:
            value=load_json(path);validate_record(value,schema);validate_profile_dispatch(root,entry["path"],value,entry)
        count+=1
    return count

def verify_closure(root:Path, *, require_clean:bool=True,
                   expected_head:str|None=None, expected_tree:str|None=None,
                   require_external_root:bool=True)->dict[str,Any]:
    if require_external_root and (not expected_head or not expected_tree):
        raise ContractError("VAL001_EXPECTED_ROOT_ARGUMENT_REQUIRED")
    for label,value in (("head",expected_head),("tree",expected_tree)):
        if value is not None and __import__("re").fullmatch(r"[0-9a-f]{40}",value) is None:
            raise ContractError(f"VAL001_EXPECTED_{label.upper()}_MALFORMED")
    observed_head=_git(root,"rev-parse","HEAD")
    observed_tree=_git(root,"rev-parse","HEAD^{tree}")
    if expected_head is not None and observed_head!=expected_head:
        raise ContractError("VAL001_EXPECTED_HEAD_MISMATCH")
    if expected_tree is not None and observed_tree!=expected_tree:
        raise ContractError("VAL001_EXPECTED_TREE_MISMATCH")
    enumerated=enumerate_governed(root)
    inventory=load_json(root/INVENTORY_PATH);registry=load_json(root/REGISTRY_PATH)
    registered=[r["path"] for r in inventory["records"]]
    if len(registered)!=len(set(registered)): raise ContractError("duplicate inventory path")
    artifact_ids=[str(r["artifact_record_id"]) for r in inventory["records"]]
    duplicate_ids={x for x in artifact_ids if artifact_ids.count(x)>1}
    # Historical generations may intentionally retain an artifact ID only when
    # their paths are explicitly historical.
    for duplicate in duplicate_ids - {"VAL-001"}:
        paths=[r["path"] for r in inventory["records"] if str(r["artifact_record_id"])==duplicate]
        if not all("/historical/" in p for p in paths[1:]): raise ContractError(f"duplicate artifact record ID: {duplicate}")
    if enumerated!=sorted(registered):
        raise ContractError(f"zero-exclusion enumeration mismatch missing={sorted(set(enumerated)-set(registered))} extra={sorted(set(registered)-set(enumerated))}")
    verify_inventory(root,inventory);verify_registry(inventory,registry)
    validated=validate_all_records(root,inventory)
    freeze=load_json(root/ADMIN_FREEZE_PATH);lock=load_json(root/CANONICAL_LOCK_PATH)
    specification=load_json(root/ADMIN_CLOSURE_PATH)
    graph_result=validate_binding_graph(inventory,freeze,lock,specification)
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
            blob=subprocess.check_output(["git","show",f"{commit}:{rel}"],cwd=root)
            import hashlib
            if hashlib.sha256(blob).hexdigest()!=fb.get("sha256"): raise ContractError("freeze bytes at commit mismatch")
        elif kind=="BOUND_BY_FINAL_GIT_TREE":
            if rel!=CANONICAL_LOCK_PATH: raise ContractError("noncanonical final Git-tree terminal")
            tracked_blob=_git(root,"rev-parse",f"HEAD:{rel}")
            working_blob=_git(root,"hash-object",rel)
            if tracked_blob!=working_blob: raise ContractError("VAL001_CANONICAL_LOCK_BLOB_MISMATCH")
        else: raise ContractError(f"unknown binding class: {kind}")
    if classes.get("BOUND_BY_FINAL_GIT_TREE")!=1: raise ContractError("terminal external root count is not one")
    if require_clean and _git(root,"status","--porcelain"): raise ContractError("VAL001_WORKING_TREE_NOT_CLEAN")
    return {"enumerated":len(enumerated),"registered":len(registered),"validated":validated,"binding_classes":classes,**graph_result,
        "expected_head":expected_head,"observed_head":observed_head,
        "expected_tree":expected_tree,"observed_tree":observed_tree,
        "lock_blob":_git(root,"rev-parse",f"HEAD:{CANONICAL_LOCK_PATH}"),
        "external_root_verified":require_external_root}
