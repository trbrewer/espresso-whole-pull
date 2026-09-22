#!/usr/bin/env python3
"""Active radial G2 identities and unchanged accepted evidence/defaults."""
import argparse,hashlib,json,subprocess
from pathlib import Path

def inspect(root):
    errors=[];freeze=json.loads((root/'docs/analysis/sci_md_rheology_006/FREEZE.json').read_text())
    def sha(b):return hashlib.sha256(b).hexdigest()
    for path,digest in freeze['files'].items():
        if sha((root/path).read_bytes())!=digest:errors.append('active frozen file changed: '+path)
    if freeze['governance']!='G2' or freeze['change_declaration']!='GOVERNING_PHYSICS_CHANGE':errors.append('declaration')
    base=freeze['starting_commit']
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',base,'docs/analysis','config','dependencies/puckworks.lock.json'],cwd=root,text=True).splitlines()
    protected=[p for p in paths if p.startswith(('config/','dependencies/')) or any('/sci_md_rheology_'+n+'/' in p for n in ('001','002','003','004','005'))]
    for path in protected:
        original=subprocess.check_output(['git','show',base+':'+path],cwd=root)
        if (root/path).read_bytes()!=original:errors.append('accepted evidence/default/lock changed: '+path)
    if subprocess.run(['git','merge-base','--is-ancestor',base,'HEAD'],cwd=root).returncode:errors.append('accepted base not ancestor')
    return dict(status='PASS' if not errors else 'FAIL',errors=errors,active_files=len(freeze['files']),historical_controls=len(protected))

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();r=inspect(a.root);print(json.dumps(r,indent=2));return r['status']!='PASS'
if __name__=='__main__':raise SystemExit(main())
