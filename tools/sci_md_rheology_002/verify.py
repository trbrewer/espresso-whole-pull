"""Short synthetic native fixtures, baseline comparisons and parallel checks."""
import argparse
import copy
import csv
import json
from pathlib import Path
import subprocess
import numpy as np
from tools.sci_md_rheology_002.run import execute, rows, scenario, ROOT
from tools.sci_md_rheology_002.export import HEADER
from tools.sci_md_rheology_001.analysis import sha, write
from scripts.espresso_reference_math import discrete_layered_pressure_reference


def traces(case):
    with (case/'postProcessing/wholePull/0/traces.csv').open() as f:
        rr=list(csv.DictReader(f))
    return {k:np.array([float(r[k]) for r in rr]) for k in rr[0] if all(_float(r[k]) for r in rr)}


def _float(x):
    try: float(x);return True
    except ValueError:return False


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--executable',type=Path,required=True)
    p.add_argument('--baseline',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    records={};cases={}
    mu=scenario('uniform_9bar')['liquid']['dynamic_viscosity_Pa_s']
    tables={}
    for name,values in [('water',[mu]*3),('double',[2*mu]*3),('evolving',[mu,2*mu,4*mu])]:
        table=a.output/(name+'.table');table.write_text(HEADER+''.join(f'{w:.17g} {v:.17g}\n' for w,v in zip([0,.1,.24],values)))
        tables[name]=table
    def run(name,s,exe=None,nprocs=1):
        case=execute(s,a.output/name,exe or a.executable,nprocs);cases[name]=case;return case
    def fixture(name='uniform_9bar',n=32):
        s=scenario(name);s['geometry'].update(axial_cells=n,radial_cells=2)
        s['time'].update(end_s=1.,field_write_interval_s=.5);return s
    def option(s,table,mode='coupled'):
        s=copy.deepcopy(s);s['aggregate_viscosity']=dict(mode=mode,purpose='synthetic',table=str(tables[table]));return s
    for name in ('uniform_9bar','reversed_3bar'):
        s=fixture(name)
        b=traces(run(name+'_baseline',s,a.baseline))
        for variant in ('absent','disabled','water'):
            q=copy.deepcopy(s)
            if variant=='disabled':q['aggregate_viscosity']={'mode':'off','table':'deliberately_missing'}
            if variant=='water':q=option(q,'water')
            t=traces(run(name+'_'+variant,q))
            common=[k for k in b if k in t and 'wall' not in k.lower() and 'cpu' not in k.lower()]
            error=max(float(np.max(abs(t[k]-b[k]))/max(float(np.max(abs(b[k]))),1)) for k in common)
            records[name+'_'+variant+'_baseline_normalized_max']=error
            assert error<=1e-10,(name,variant,error)
        c=rows(cases[name+'_water']);ref=discrete_layered_pressure_reference(s)['outlet_flow_m3_s']
        records[name+'_analytical_relative_max']=float(max(abs(c['Q_m3_s']/ref-1)))
        assert records[name+'_analytical_relative_max']<1e-6
        doubled=rows(run(name+'_double',option(s,'double')))
        q=copy.deepcopy(s);q['liquid']['dynamic_viscosity_Pa_s']*=2
        normal=traces(run(name+'_constant_double',q))
        records[name+'_multiplier_relative_max']=float(max(abs(doubled['Q_m3_s']/(c['Q_m3_s']*.5)-1)))
        assert records[name+'_multiplier_relative_max']<1e-6
        assert np.allclose(doubled['Q_m3_s'],normal['outlet_flow_m3_s'],rtol=1e-6,atol=0)
    s=option(fixture(),'evolving');c=rows(run('evolving',s));r=rows(run('repeat',s));m=rows(run('parallel',s,nprocs=2))
    records['repeat_max_absolute']=max(float(max(abs(c[k]-r[k]))) for k in c)
    records['parallel_max_normalized']=max(float(max(abs(c[k]-m[k])))/max(float(max(abs(c[k]))),1e-8) for k in c if 'balance' not in k)
    assert records['repeat_max_absolute']<=1e-12
    assert records['parallel_max_normalized']<=1e-6
    assert c['mu_max'][-1]>c['mu_max'][0] and c['Q_m3_s'][-1]<c['Q_m3_s'][0]
    records['evolving_flow_ratio']=float(c['Q_m3_s'][-1]/c['Q_m3_s'][0])
    s['extraction']['rate_constant_1_s']=0
    z=rows(run('zero',s));records['zero_water_relative_max']=float(max(abs(z['Q_m3_s']/z['Q_m3_s'][0]-1)))
    assert records['zero_water_relative_max']<1e-6 and max(z['c_next_max'])==0
    for n in (32,64):
        s=option(fixture('reversed_3bar',n),'water');d=rows(run(f'layer_refinement_{n}',s))
        records[f'layer_continuum_{n}']=float(max(abs(d['Q_m3_s']/d['Q_cont_m3_s']-1)))
    assert records['layer_continuum_64']<records['layer_continuum_32']
    records['balance_max_kg']=0.;records['correction_max_kg']=0.
    for case in cases.values():
        if not (case/'postProcessing/wholePull/0/aggregate_intervals.csv').exists():continue
        d=rows(case)
        records['balance_max_kg']=max(records['balance_max_kg'],max(abs(d['water_balance_kg'])),max(abs(d['solute_balance_kg'])))
        records['correction_max_kg']=max(records['correction_max_kg'],sum(d['correction_kg']))
    assert records['balance_max_kg']<1e-8 and records['correction_max_kg']<1e-10
    records.update(executable_sha256=sha(a.executable),baseline_executable_sha256=sha(a.baseline),
        native_short_runs=len(cases),status='PASS',scaling='max absolute difference / max(max(abs(reference)), stated floor)')
    write(a.output/'VERIFICATION.json',records);print(json.dumps(records,indent=2))

if __name__=='__main__':main()
