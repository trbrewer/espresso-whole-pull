#!/usr/bin/env python3
"""Active radial G2 identities and unchanged accepted evidence/defaults."""
import argparse,hashlib,json,subprocess
from pathlib import Path

def inspect(root):
    errors=[];freeze=json.loads((root/'docs/analysis/sci_md_rheology_006/FREEZE.json').read_text())
    def sha(b):return hashlib.sha256(b).hexdigest()
    amendment_path=root/'docs/analysis/sci_md_rheology_006/POST_EXECUTION_CORRECTION.json'
    amendments={}
    if amendment_path.exists():
        amendment=json.loads(amendment_path.read_text())
        if (amendment['type']!='ANALYSIS_ONLY_CORRECTION'
            or amendment['original_freeze_sha256']!=sha((root/'docs/analysis/sci_md_rheology_006/FREEZE.json').read_bytes())
            or set(amendment['files'])!={'tools/sci_md_rheology_006/analyze.py'}):
            errors.append('invalid bounded analysis amendment')
        else:amendments=amendment['files']
    successor=root/'docs/analysis/sci_md_rheology_009/FREEZE.json'
    active=json.loads(successor.read_text()) if successor.exists() else None
    for path,digest in freeze['files'].items():
        if path in amendments:
            if amendments[path]['original_sha256']!=digest:errors.append('wrong amendment parent '+path)
            digest=amendments[path]['amended_sha256']
        historical = subprocess.check_output(['git','show','3960b4a9c4b05aa3f3cdec1dade33eb16c485d24:'+path],cwd=root) if active else (root/path).read_bytes()
        if sha(historical)!=digest:errors.append('accepted frozen file changed: '+path)
        if active and path in active['files']:
            expected=active['files'][path]
            geometry_freeze=root/'docs/analysis/sci_md_rheology_011/FREEZE.json'
            if geometry_freeze.exists() and path in ('scripts/prepare_case.py','scripts/aggregate_viscosity.py'):
                old009=subprocess.check_output(['git','show','dd05d3dd8dd8f690941f22e1583acf2026a23955:'+path],cwd=root)
                if sha(old009)!=expected:errors.append('historical 009 source changed: '+path)
                current=json.loads(geometry_freeze.read_text())
                if current['governance']!='G2' or current['change_declaration']!='NO_GOVERNING_PHYSICS_CHANGE':errors.append('011 geometry declaration')
                expected=current['files'][path]
                helper='scripts/radial_mesh.py'
                if sha((root/helper).read_bytes())!=current['files'][helper]:errors.append('active geometry helper changed')
            if sha((root/path).read_bytes())!=expected:errors.append('active frozen file changed: '+path)
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
