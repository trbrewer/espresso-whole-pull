from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
TASK_ID = "SCI-DATA-FUSION-001"
SUPERSEDED_FREEZES = {"54b2164eaf81907a8573d54e89fd8eecbf99293e","1f9b8758c2b2b756eeb29daab28b4dce0cf3525b"}
SUPERSEDED_FREEZE = min(SUPERSEDED_FREEZES)
AUTHORITY_FILES = {"manifest_sha256":"puckworks/data/MANIFEST.csv","available_data_register_sha256":"puckworks/data/AVAILABLE_DATA_REGISTER.json","local_corpus_family_index_sha256":"puckworks/data/LOCAL_CORPUS_FAMILY_INDEX.json"}
class AuthorityError(RuntimeError): pass
def sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""): digest.update(block)
    return digest.hexdigest()
def git(root: Path,*args:str)->str:
    try: return subprocess.check_output(["git","-C",str(root),*args],text=True).strip()
    except subprocess.CalledProcessError as exc: raise AuthorityError(f"git {' '.join(args)} failed at {root}") from exc
def ancestor(root:Path,older:str,newer:str)->bool:
    return subprocess.run(["git","-C",str(root),"merge-base","--is-ancestor",older,newer]).returncode==0
def load_json(path:Path)->dict:
    try: value=json.loads(path.read_text())
    except (OSError,json.JSONDecodeError) as exc: raise AuthorityError(f"invalid JSON authority: {path}") from exc
    if not isinstance(value,dict): raise AuthorityError(f"JSON authority must be an object: {path}")
    return value
def verify_frozen_ewp(root:Path,authority:dict,include_runtime:bool=True)->dict:
    base,predecessor=authority["frozen_ewp_base"],authority["accepted_predecessor"]
    for object_id in (base["commit"],predecessor["commit"]): git(root,"cat-file","-e",f"{object_id}^{{commit}}")
    if git(root,"rev-parse",f'{base["commit"]}^{{tree}}')!=base["tree"]: raise AuthorityError("frozen EWP base tree mismatch")
    if git(root,"rev-parse",f'{predecessor["commit"]}^{{tree}}')!=predecessor["tree"]: raise AuthorityError("accepted predecessor tree mismatch")
    if not ancestor(root,predecessor["commit"],base["commit"]): raise AuthorityError("accepted predecessor is not reachable from frozen EWP base")
    if not ancestor(root,base["commit"],"HEAD"): raise AuthorityError("current execution head does not descend from frozen EWP base")
    result={"frozen_ewp_base":base,"accepted_predecessor":predecessor}
    if include_runtime:result.update(current_execution_head=git(root,"rev-parse","HEAD"),current_execution_tree=git(root,"rev-parse","HEAD^{tree}"),working_tree_clean=not bool(git(root,"status","--porcelain")))
    return result
def verify_consumed(root:Path,ledger:dict,expected_paths:set[str]|None=None)->list[dict]:
    rows=ledger.get("artifacts")
    if not isinstance(rows,list) or not rows: raise AuthorityError("consumed-artifact ledger is empty or invalid")
    paths=[row.get("path") for row in rows]
    if any(not isinstance(path,str) for path in paths) or len(paths)!=len(set(paths)): raise AuthorityError("consumed-artifact ledger has missing or duplicate paths")
    if expected_paths is not None and set(paths)!=expected_paths: raise AuthorityError("consumed-artifact ledger additions or omissions")
    for row in rows:
        scope=row.get("scope","repository")
        if scope not in {"repository","package"}:raise AuthorityError(f"invalid freeze-content scope: {scope}")
        path=(root/row["path"]) if scope=="repository" else (manifest_path.parent/row["path"])
        if not path.is_file() or sha256(path)!=row.get("sha256"): raise AuthorityError(f"consumed artifact mismatch: {row['path']}")
    return rows
def verify_puckworks(root:Path,expected:dict)->dict:
    head,tree=git(root,"rev-parse","HEAD"),git(root,"rev-parse","HEAD^{tree}")
    if (head,tree)!=(expected["commit"],expected["tree"]): raise AuthorityError(f"Puckworks identity mismatch: {head}/{tree}")
    hashes={}
    for key,relative in AUTHORITY_FILES.items():
        path=root/relative
        if not path.is_file(): raise AuthorityError(f"missing Puckworks authority file: {relative}")
        hashes[key]=sha256(path)
        if hashes[key]!=expected[key]: raise AuthorityError(f"Puckworks authority hash mismatch: {relative}")
    return {"commit":head,"tree":tree,**hashes}
def verify_freeze_manifest(root:Path,manifest_path:Path)->dict:
    manifest=load_json(manifest_path); rows=manifest.get("files")
    if not isinstance(rows,list) or not rows: raise AuthorityError("empty freeze-content manifest")
    paths=[row.get("path") for row in rows]
    if len(paths)!=len(set(paths)) or any(not isinstance(path,str) for path in paths): raise AuthorityError("invalid freeze-content manifest paths")
    for row in rows:
        scope=row.get("scope","repository")
        if scope not in {"repository","package"}:raise AuthorityError(f"invalid freeze-content scope: {scope}")
        path=root/row["path"] if scope=="repository" else manifest_path.parent/row["path"]
        if not path.is_file() or sha256(path)!=row.get("sha256"): raise AuthorityError(f"frozen decision path mismatch: {row['path']}")
    return manifest
