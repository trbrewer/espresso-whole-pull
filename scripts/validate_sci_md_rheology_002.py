#!/usr/bin/env python3
"""Check the active G2 freeze while preserving immutable predecessor evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.sci_md_rheology_002.authority import expected


def inspect(root):
    doc=root/'docs/analysis/sci_md_rheology_002'
    f,files,_=expected(doc)
    errors=[]
    for path,digest in files.items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=digest:
            errors.append('frozen source changed: '+path)
    if f['governance']!='G2' or f['change_declaration']!='GOVERNING_PHYSICS_CHANGE':errors.append('wrong declaration')
    if hashlib.sha256((root/'dependencies/puckworks.lock.json').read_bytes()).hexdigest()!=f['runtime_lock_sha256']:errors.append('runtime lock changed')
    base='14fc4c8a4a94ffa54ffafd5c2c99037c1af680b9'
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',base,'docs/analysis/sci_md_rheology_001'],cwd=root,text=True).splitlines()
    for path in paths:
        if (root/path).read_bytes()!=subprocess.check_output(['git','show',base+':'+path],cwd=root):errors.append('historical evidence changed: '+path)
    if subprocess.run(['git','merge-base','--is-ancestor',base,'HEAD'],cwd=root).returncode:errors.append('predecessor absent')
    return dict(status='PASS' if not errors else 'FAIL',errors=errors,frozen_files=len(f['files']),historical_files=len(paths))


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
    report=inspect(a.root);print(json.dumps(report,indent=2));return report['status']!='PASS'

if __name__=='__main__':raise SystemExit(main())
