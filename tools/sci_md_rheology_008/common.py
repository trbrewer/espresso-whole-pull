"""Fixed native radial family; no closure or production modifications."""
import copy
import json
from pathlib import Path
from tools.sci_md_rheology_001.analysis import ROOT, sha, write
from tools.sci_md_rheology_006.common import LAWS, TRACE, radial, table_name, execute
from tools.sci_md_rheology_007.common import BUDGETS, digest, sets
DOC = ROOT/'docs/analysis/sci_md_rheology_008'
EXE_SHA = 'bea2860f92f4934c3f191b7da8d9c425f73ac254cd42131172dad133dd77d7ad'

def matrix():
    return {f'E{n}_{law}_{p}bar_{r}': (n, law, p, r)
            for n in (2, 4, 8) for law in LAWS for p in (3, 9) for r in sets(law)}

def candidate(reference, n):
    if n not in (2, 4, 8):
        raise ValueError('undeclared radial candidate')
    s = copy.deepcopy(reference)
    s['scenario_id'] = 'sci_md_rheology_008_E'+str(n)
    s['geometry']['radial_cells'] = n
    s['time']['field_write_interval_s'] = 30.
    return s

def check(art, audit=False):
    f = json.loads((DOC/'FREEZE.json').read_text())
    if digest(str(art.resolve())) != f['artifact_root_sha256']:
        raise ValueError('wrong artifact location')
    for root, values in ((ROOT, f['files']), (art, f['external'])):
        for p, h in values.items():
            if sha(root/p) != h:
                raise ValueError('frozen identity changed: '+p)
    if audit:
        a = json.loads((DOC/'AUDIT.json').read_text())
        if a['status'] != 'PASS' or a['freeze_sha256'] != sha(DOC/'FREEZE.json'):
            raise ValueError('independent pre-scoring audit missing/stale')
    return f
