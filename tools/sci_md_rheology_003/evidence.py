"""Hash-qualified predecessor reuse and prospective execution authority."""
import json
from pathlib import Path
import subprocess
from tools.sci_md_rheology_001.analysis import ROOT, sha, write
from tools.sci_md_rheology_002.authority import expected
from tools.sci_md_rheology_002.run import DOC as OLD

DOC=ROOT/'docs/analysis/sci_md_rheology_003'
INTERVAL='postProcessing/wholePull/0/aggregate_intervals.csv'


def reuse(artifacts):
    manifest=json.loads((OLD/'RUNS.json').read_text())
    freeze,files,exe=expected(OLD)
    for p,h in files.items():
        if sha(ROOT/p)!=h:raise ValueError('accepted amended source mismatch: '+p)
    records=manifest['scientific_invocations']
    if len(records)!=18:raise ValueError('incomplete predecessor')
    for r in records:
        directory=Path(artifacts)/r['id'];case=directory/'case'
        if r['status']!='COMPLETE' or r['executable_sha256']!=freeze['executable_sha256']:
            raise ValueError('historical executable identity mismatch')
        paths={directory/'scenario.json':r['configuration_sha256'],case/INTERVAL:r['intervals_sha256']}
        paths.update({case/p:h for p,h in r['input_hashes'].items()})
        paths.update({directory/p:h for p,h in r['logs_sha256'].items()})
        for p,h in paths.items():
            if sha(p)!=h:raise ValueError('historical artifact mismatch: '+r['id']+'/'+p.name)
    return dict(status='PASS',count=18,manifest_sha256=sha(OLD/'RUNS.json'),
                amendment_sha256=sha(OLD/'POST_RESULT_AMENDMENT.json'),
                historical_executable_sha256=freeze['executable_sha256'],qualified_executable_sha256=exe,
                intervals={r['id']:r['intervals_sha256'] for r in records})


def check_freeze(executable, tables, audit=None):
    freeze=json.loads((DOC/'FREEZE.json').read_text())
    for p,h in freeze['files'].items():
        if sha(ROOT/p)!=h:raise ValueError('frozen file changed: '+p)
    if sha(executable)!=freeze['executable_sha256']:raise ValueError('executable mismatch')
    for name,h in freeze['tables'].items():
        if sha(Path(tables)/(name+'.table'))!=h:raise ValueError('table mismatch')
    if audit is not None:
        a=json.loads(Path(audit).read_text())
        if a.get('status')!='PASS' or a.get('freeze_sha256')!=sha(DOC/'FREEZE.json') or not a.get('independent'):
            raise ValueError('independent pre-scoring audit absent or mismatched')
        if not a.get('reviewed_commit') or not a.get('reviewer'):
            raise ValueError('audit provenance missing')
    return freeze
