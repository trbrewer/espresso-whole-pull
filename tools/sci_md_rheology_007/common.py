"""Frozen analysis-side composition; no native equations or runtime changes."""
import copy, hashlib, json
from pathlib import Path
from tools.sci_md_rheology_001.analysis import ROOT, sha, write
from tools.sci_md_rheology_006.common import LAWS, radial, table_name, execute
DOC=ROOT/'docs/analysis/sci_md_rheology_007'
TRACE=Path('postProcessing/wholePull/0/aggregate_intervals.csv')
BUDGETS=dict(E_Qint=.01,E_Qpeak=.02,D_share_mean_pp=1.,D_share_peak_pp=2.,E_Spath=.01,D_TDS_pp=.10)
WEIGHTS=(.25,.75)
K=(3e-15,7.5e-16)

def sets(law):return ('base','temporal','axial')+(('property',) if law==LAWS[1] else ())
def matrix():return {f'{l}_{p}bar_{r}_{z}':(l,p,r,z) for l in LAWS for p in (3,9) for r in sets(l) for z in ('inner','outer')}
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
def constituent(reference,zone,area=1.,short=False,nr=2):
    s=copy.deepcopy(reference)
    s['scenario_id']='autonomous_'+zone
    s['geometry']['radial_cells']=nr
    s['hydraulics']['permeability_profile']={'type':'uniform'}
    s['hydraulics']['saturated_permeability_m2']=K[('inner','outer').index(zone)]
    s['time']['field_write_interval_s']=.2 if short else 30.
    if short:
        s['geometry']['axial_cells']=32
        s['time'].update(end_s=.2,delta_t_s=.02)
    if area!=1.:
        for k in ('basket_radius_m','basket_diameter_m'):s['geometry'][k]*=area**.5
        s['coffee_bed']['dry_dose_kg']*=area
    return s

def check(art,audit=False):
    f=json.loads((DOC/'FREEZE.json').read_text())
    if digest(str(art.resolve()))!=f['artifact_root_sha256']:raise ValueError('wrong execution root')
    for p,h in f['files'].items():
        if sha(ROOT/p)!=h:raise ValueError('frozen source changed: '+p)
    for p,h in f['external'].items():
        if sha(art/p)!=h:raise ValueError('frozen external input changed: '+p)
    if audit:
        a=json.loads((DOC/'AUDIT.json').read_text())
        if a['status']!='PASS' or a['freeze_sha256']!=sha(DOC/'FREEZE.json'):raise ValueError('independent audit missing/stale')
    return f
