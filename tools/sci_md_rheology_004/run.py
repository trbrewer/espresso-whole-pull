"""Eight SW native constant-viscosity attempts; no full retries or new C/W."""
import argparse
from pathlib import Path
from tools.sci_md_rheology_001.analysis import ROOT,sha
from tools.sci_md_rheology_002.run import scenario,execute
from tools.sci_md_rheology_003.run import invoke
from .evidence import DOC,matrix,check,qualify_reuse
from .freeze import root_identity


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('artifacts','baseline','coupled','executable','tables','audit'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--identity',choices=matrix(),required=True)
    a=p.parse_args()
    if a.artifacts.resolve().is_relative_to(ROOT):raise ValueError('external artifacts required')
    f=check(a.executable,a.tables,a.audit);qualify_reuse(a.baseline,a.coupled)
    if root_identity(a.artifacts)!=f['artifact_root_sha256']:raise ValueError('wrong task execution root')
    r,c=a.identity.split('_',1);c=c[:-2]
    alpha=f['alpha']['SW_WATER_ANCHORED_90C'][r]
    s=scenario(c,'base' if r=='property' else r)
    table=a.tables/('SW_WATER_ANCHORED_90C_'+('refined' if r=='property' else 'base')+'.table')
    s['aggregate_viscosity']=dict(mode='observe',purpose='scientific',table=str(table.resolve()))
    s['liquid']['dynamic_viscosity_Pa_s']/=alpha
    invoke(a.artifacts,a.identity,8,set(matrix()),dict(executable_sha256=sha(a.executable),
        table_sha256=sha(table),freeze_sha256=sha(DOC/'FREEZE.json'),alpha=alpha,transport='INDEPENDENT_NATIVE'),
        lambda d:execute(s,d,a.executable))
    print(a.identity+' COMPLETE')

if __name__=='__main__':main()
