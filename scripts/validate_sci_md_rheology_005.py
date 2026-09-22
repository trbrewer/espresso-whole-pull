#!/usr/bin/env python3
"""Active G2 contract plus immutable 001–004 evidence and historical 002 source."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.sci_md_rheology_002.authority import expected

def inspect(root):
    base='ab29a805217010f8c441047aaa04e6b4adaca3fe';errors=[]
    def blob(p):return subprocess.check_output(['git','show',base+':'+p],cwd=root)
    def sha(b):return hashlib.sha256(b).hexdigest()
    freeze=json.loads((root/'docs/analysis/sci_md_rheology_005/FREEZE.json').read_text())
    successor = root/'docs/analysis/sci_md_rheology_006/FREEZE.json'
    accepted005 = 'db705b644bbc2c3f719690448657e845f2a8f65b'
    if successor.exists():
        from scripts.validate_sci_md_rheology_006 import inspect as radial_inspect
        errors.extend(radial_inspect(root)['errors'])
    for p,h in freeze['files'].items():
        actual = subprocess.check_output(['git','show',accepted005+':'+p],cwd=root) if successor.exists() else (root/p).read_bytes()
        if sha(actual)!=h:errors.append('005 frozen file changed: '+p)
    if freeze['governance']!='G2' or freeze['change_declaration']!='GOVERNING_PHYSICS_CHANGE':errors.append('wrong G2 declaration')
    _,old,_=expected(root/'docs/analysis/sci_md_rheology_002')
    for p,h in old.items():
        if sha(blob(p))!=h:errors.append('accepted historical 002 source mismatch: '+p)
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',base,'docs/analysis'],cwd=root,text=True).splitlines()
    historical=[p for p in paths if any('/sci_md_rheology_'+n+'/' in p for n in ('001','002','003','004'))]
    for p in historical:
        if (root/p).read_bytes()!=blob(p):errors.append('historical evidence modified: '+p)
    controls=subprocess.check_output(['git','ls-tree','-r','--name-only',base,'config','dependencies/puckworks.lock.json'],cwd=root,text=True).splitlines()
    for p in controls:
        if (root/p).read_bytes()!=blob(p):errors.append('default/lock changed: '+p)
    if subprocess.run(['git','merge-base','--is-ancestor',base,'HEAD'],cwd=root).returncode:errors.append('accepted base not ancestor')
    return dict(status='PASS' if not errors else 'FAIL',errors=errors,active_frozen_files=len(freeze['files']),historical_files=len(historical),unchanged_controls=len(controls))
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
    r=inspect(a.root);print(json.dumps(r,indent=2));return r['status']!='PASS'
if __name__=='__main__':raise SystemExit(main())
