#!/usr/bin/env python3
"""Compare the protected production surface and exact branch scope using Git objects."""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path

def git(root, *args, check=True):
    p=subprocess.run(["git","-C",str(root),*args],text=True,capture_output=True)
    if check and p.returncode: raise ValueError(p.stderr.strip())
    return p

def tree(root, rev):
    out={}
    for rec in git(root,"ls-tree","-rz",rev).stdout.split("\0"):
        if not rec: continue
        meta,path=rec.split("\t",1); mode,kind,oid=meta.split()
        data=subprocess.check_output(["git","-C",str(root),"cat-file","-p",oid]) if kind=="blob" else b""
        out[path]={"mode":mode,"object_type":kind,"oid":oid,"sha256":hashlib.sha256(data).hexdigest() if kind=="blob" else None}
    return out

def protected(path,rules):
    return path in rules["protected_files"] or any(path==p or path.startswith(p+"/") for p in rules["protected_roots"])

def verify(root,base,head,rules_path,output=None):
    root=Path(root).resolve(); rules_path=Path(rules_path).resolve()
    rules=json.loads(rules_path.read_text())
    if rules.get("schema_version")!="1.0.0": raise ValueError("RULES_SCHEMA_INVALID")
    for rev,label in ((base,"BASE_COMMIT_MISSING"),(head,"HEAD_COMMIT_MISSING")):
        if git(root,"cat-file","-e",f"{rev}^{{commit}}",check=False).returncode: raise ValueError(label)
    if git(root,"merge-base","--is-ancestor",base,head,check=False).returncode: raise ValueError("BASE_NOT_ANCESTOR")
    bt,ht=tree(root,base),tree(root,head); paths=sorted(set(bt)|set(ht))
    changed=[]; protected_changes=[]; unexpected=[]
    allowed=set(rules["allowed_changed_paths"])
    for path in paths:
        old,new=bt.get(path),ht.get(path)
        if old==new: continue
        reason=[]
        if old is None: reason.append("ADDED")
        elif new is None: reason.append("DELETED")
        else:
            if old["mode"]!=new["mode"]: reason.append("MODE_CHANGED")
            if old["object_type"]!=new["object_type"]: reason.append("OBJECT_TYPE_CHANGED")
            if old["oid"]!=new["oid"]: reason.append("CONTENT_CHANGED")
        item={"path":path,"reasons":reason,"old":old,"new":new,"protected":protected(path,rules),"allowed":path in allowed}
        changed.append(item)
        if item["protected"]: protected_changes.append(item)
        elif not item["allowed"]: unexpected.append(item)
    status="PASS_NO_BRANCH_PHYSICS_CHANGE" if not protected_changes and not unexpected else "FAIL_BRANCH_SCOPE_OR_PHYSICS_CHANGE"
    report={"schema_version":"1.0.0","base_commit":base,"base_tree":git(root,"rev-parse",f"{base}^{{tree}}").stdout.strip(),"head_commit":head,"head_tree":git(root,"rev-parse",f"{head}^{{tree}}").stdout.strip(),"base_is_ancestor":True,"rules_sha256":hashlib.sha256(rules_path.read_bytes()).hexdigest(),"changed_paths":changed,"protected_path_comparison_count":sum(protected(p,rules) for p in paths),"protected_changes":protected_changes,"allowed_changes":[x for x in changed if x["allowed"] and not x["protected"]],"unexpected_changes":unexpected,"status":status,"governing_physics_change":bool(protected_changes)}
    if output: Path(output).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report

def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",required=True); p.add_argument("--base",required=True); p.add_argument("--head",required=True); p.add_argument("--rules",required=True); p.add_argument("--output",required=True)
    a=p.parse_args()
    try: r=verify(a.root,a.base,a.head,a.rules,a.output)
    except ValueError as e: print(json.dumps({"status":"FAIL","reason":str(e)})); return 1
    print(json.dumps({"status":r["status"],"protected_changes":len(r["protected_changes"]),"unexpected_changes":len(r["unexpected_changes"])}))
    return 0 if r["status"]=="PASS_NO_BRANCH_PHYSICS_CHANGE" else 1
if __name__=="__main__": raise SystemExit(main())
