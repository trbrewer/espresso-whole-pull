"""Assemble the single prospective freeze after property and reuse qualification."""
import argparse
import json
from pathlib import Path
import subprocess
from tools.sci_md_rheology_001.analysis import ROOT,sha,write
from tools.sci_md_rheology_002.authority import expected
from tools.sci_md_rheology_002.run import DOC as OLD
from .evidence import DOC
from .analyze import check_baseline
from .run import matrix


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('executable','tables','baseline','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    if (DOC/'FREEZE.json').exists():raise ValueError('prospective freeze already exists')
    if a.output.resolve().is_relative_to(ROOT):raise ValueError('reproduction artifacts must be external')
    export=json.loads((a.tables/'EXPORT.json').read_text())
    _,_,exe=expected(OLD)
    if sha(a.executable)!=exe:raise ValueError('accepted corrected executable required')
    for name,record in export['tables'].items():
        if sha(a.tables/(name+'.table'))!=record['sha256']:raise ValueError('qualified table changed')
    _,reuse=check_baseline(a.baseline,a.output/'baseline-reproduction')
    write(DOC/'REUSE.json',reuse);write(DOC/'EXPORT.json',export)
    paths=[p for pattern in ('tools/sci_md_rheology_003/*.py','tests/test_sci_md_rheology_003.py') for p in ROOT.glob(pattern)]
    paths += [DOC/n for n in ('PROTOCOL.md','SOURCE_USE.json','EXPORT.json','REUSE.json')]
    paths += [p for p in (ROOT/'solver/espressoWholePullFoam').rglob('*') if p.is_file() and ('Make' not in p.parts or p.name in ('files','options'))]
    paths += [ROOT/p for p in ('scripts/prepare_case.py','scripts/aggregate_viscosity.py',
        'tools/sci_md_rheology_001/analysis.py','tools/sci_md_rheology_002/authority.py',
        'tools/sci_md_rheology_002/run.py','tools/sci_md_rheology_002/analyze.py',
        'tools/sci_md_rheology_002/export.py','tools/sci_md_rheology_002/evaluator.cpp',
        'docs/analysis/sci_md_rheology_001/SCENARIOS.json','dependencies/puckworks.lock.json')]
    freeze=dict(task='SCI-MD-RHEOLOGY-003',governance='G1',declaration='SOURCE_SCENARIO_CHANGE_ONLY',
        starting_commit='d40e0e64316d57dd4b685089daf07e3a13a11974',starting_tree='ebf8c0b78fda04f182ddae52968eab6002dbf768',
        files={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))},executable_sha256=exe,
        executable_provenance='accepted 002 POST_RESULT_AMENDMENT corrected build; original science executable remains distinct',
        tables={n:r['sha256'] for n,r in export['tables'].items()},full_matrix=matrix(),short_matrix=matrix(True),
        full_attempt_ceiling=24,short_attempt_ceiling=4,scientific_execution_status='NOT_STARTED',
        independent_pre_scoring_audit='REQUIRED_BEFORE_EXECUTION',prior_results='KNOWN_COMPARISON_NOT_UNSEEN_HOLDOUT')
    write(DOC/'FREEZE.json',freeze);print(sha(DOC/'FREEZE.json'))

if __name__=='__main__':main()
