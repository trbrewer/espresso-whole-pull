"""Create the one compact pre-scoring freeze; never replace it."""
import argparse
import hashlib
import json
from pathlib import Path
from tools.sci_md_rheology_001.analysis import ROOT,sha,write
from tools.sci_md_rheology_002.run import rows,CASES
from tools.sci_md_rheology_003.analyze import analyze as reproduce
from .evidence import DOC,accepted,alphas,qualify_reuse,matrix


def root_identity(path):return hashlib.sha256(str(Path(path).resolve()).encode()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('baseline','coupled','executable','tables','artifacts','reproduction'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    if (DOC/'FREEZE.json').exists():raise ValueError('single freeze already exists')
    old=accepted();receipt=qualify_reuse(a.baseline,a.coupled)
    if sha(a.executable)!=old['executable_sha256']:raise ValueError('accepted corrected executable required')
    tables={k:v for k,v in old['tables'].items() if k.startswith('SW_')}
    for n,h in tables.items():
        if sha(a.tables/(n+'.table'))!=h:raise ValueError('accepted observer table mismatch')
    r=reproduce(a.coupled,a.baseline,a.reproduction)
    if r!=json.loads((ROOT/'docs/analysis/sci_md_rheology_003/METRICS.json').read_text()):raise ValueError('predecessor reproduction mismatch')
    alpha=alphas()
    for law,sets in alpha.items():
        for resolution,value in sets.items():
            wr='base' if resolution=='property' else resolution
            c=(a.baseline/f'{resolution}_{CASES[0]}_C' if law=='TR_LINEAR' else a.coupled/f'{resolution}_{CASES[0]}_{law}')
            cc=rows(c/'case');ww=rows(a.baseline/f'{wr}_{CASES[0]}_W/case')
            actual=float(sum(cc['volume_m3'])/sum(ww['volume_m3']))
            if actual!=value:raise ValueError('reference-only alpha mismatch')
    receipt['metric_reproduction_002_003']='EXACT'
    write(DOC/'REUSE.json',receipt)
    paths=set(old['files'])
    paths.update(str(p.relative_to(ROOT)) for pattern in ('tools/sci_md_rheology_004/*.py','tests/test_sci_md_rheology_004.py') for p in ROOT.glob(pattern))
    paths.update(str((DOC/n).relative_to(ROOT)) for n in ('PROTOCOL.md','REUSE.json'))
    paths.update('docs/analysis/sci_md_rheology_'+task+'/'+n for task in ('002','003') for n in ('FREEZE.json','RUNS.json','METRICS.json'))
    paths.add('docs/analysis/sci_md_rheology_002/POST_RESULT_AMENDMENT.json')
    f=dict(task='SCI-MD-RHEOLOGY-004',governance='G1',declaration='SOURCE_SCENARIO_CHANGE_ONLY',
        starting_commit='2542e2ea3925abcb64a881293b6dc8743e3be056',starting_tree='a793ce73337af557b0fef33eacf8baf3fc2a908c',
        files={s:sha(ROOT/s) for s in sorted(paths)},alpha=alpha,tables=tables,
        executable_sha256=old['executable_sha256'],executable_provenance=old['executable_provenance'],
        full_matrix=matrix(),full_attempt_ceiling=8,short_attempts_planned=0,
        artifact_root_sha256=root_identity(a.artifacts),prior_results='EXPOSED_COMPUTATIONAL_COMPARISONS_NO_G3',
        scientific_execution_status='NOT_STARTED',audit='INDEPENDENT_PASS_REQUIRED')
    write(DOC/'FREEZE.json',f)
    print(sha(DOC/'FREEZE.json'))

if __name__=='__main__':main()
