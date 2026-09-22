"""Sixteen predeclared short native runs; no scientific outcome selection."""
import argparse,copy,json
from pathlib import Path
import numpy as np
from .common import radial,execute,DOC,TRACE,sha,write
from .observer import read,validate
from tools.sci_md_rheology_002.run import scenario,rows
from tools.sci_md_rheology_002.verify import traces
from tools.sci_md_rheology_002.export import HEADER

def discrepancy(a,b,floor=1):
    errors=[]
    for k in b:
        if k not in a or 'wall' in k.lower() or 'cpu' in k.lower():continue
        if not np.isfinite(b[k]).all() or not np.isfinite(a[k]).all():continue
        errors.append(float(max(abs(a[k]-b[k])))/max(floor,float(max(abs(b[k])))))
    return max(errors)

def main():
    p=argparse.ArgumentParser()
    for k in ('output','executable','baseline'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    mu=radial()['liquid']['dynamic_viscosity_Pa_s'];records={};cases={}
    for name,values in [('constant',[mu]*3),('evolving',[mu,2*mu,4*mu])]:
        (a.output/(name+'.table')).write_text(HEADER+''.join(f'{w} {m:.17g}\n' for w,m in zip((0,.1,.24),values)))
    ledger_path=a.output/'ATTEMPTS.json';ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else []
    def run(name,s,old=False,mpi=False):
        prior=next((v for v in ledger if v['id']==name),None)
        if prior:
            if prior['status']!='COMPLETE':raise ValueError('failed short slot requires documented recovery')
            case=a.output/name/'case'
        else:
            if len(ledger)>=20:raise ValueError('short ceiling')
            r=dict(id=name,status='STARTED',executable_sha256=sha(a.baseline if old else a.executable));ledger.append(r);write(ledger_path,ledger)
            try:case=execute(s,a.output/name,a.baseline if old else a.executable,mpi)
            except BaseException:r['status']='FAILED';write(ledger_path,ledger);raise
            r.update(status='COMPLETE',scenario_sha256=sha(a.output/name/'scenario.json'));write(ledger_path,ledger)
        cases[name]=case
        if (case/TRACE).exists():validate(read(case),.2)
        print(name+' COMPLETE',flush=True);return case
    def spec(res='base',mode='observe'):
        s=radial(resolution=res);s['time'].update(end_s=.2,field_write_interval_s=.2)
        s['aggregate_viscosity']=dict(mode=mode,purpose='synthetic',table=str((a.output/'constant.table').resolve()))
        return s
    worst=0
    for res in ('base','axial','radial'):
        for variant in ('water','double','uniform_k'):
            s=spec(res)
            if variant=='double':s['liquid']['dynamic_viscosity_Pa_s']*=2
            if variant=='uniform_k':s['hydraulics']['permeability_profile']['outer_permeability_m2']=3e-15
            d=read(run(res+'_'+variant,s))
            ki=s['hydraulics']['permeability_profile']['inner_permeability_m2'];ko=s['hydraulics']['permeability_profile']['outer_permeability_m2']
            expected_q=np.pi*.029**2*(.25*ki+.75*ko)*9e5/(s['liquid']['dynamic_viscosity_Pa_s']*.009011660896432553)
            share=.25*ki/(.25*ki+.75*ko)
            qe=float(max(abs(d['Q_total_m3_s']/expected_q-1)));se=float(max(abs(d['Q_inner_m3_s']/d['Q_total_m3_s']-share)))
            records[res+'_'+variant]=dict(Q_relative=qe,share_absolute=se)
            assert qe<=1e-6 and se/share<=1e-6,(res,variant,qe,se)
            worst=max(worst,se)
    s=spec();s.pop('aggregate_viscosity');absent=traces(run('base_absent',s))
    observe=traces(cases['base_water']);coupled=traces(run('base_constant_coupled',spec(mode='coupled')))
    for name,x in [('observe',observe),('constant_coupled',coupled)]:
        records[name+'_baseline']=discrepancy(x,absent);assert records[name+'_baseline']<=1e-10
    s=scenario('reversed_3bar');s['geometry'].update(axial_cells=32,radial_cells=2);s['time'].update(end_s=.2,field_write_interval_s=.2)
    s['aggregate_viscosity']=dict(mode='bulkCoupled',purpose='synthetic',table=str((a.output/'evolving.table').resolve()))
    old=rows(run('bulk_old',s,True));new=rows(run('bulk_candidate',s));records['bulk_regression']=discrepancy(new,old);assert records['bulk_regression']<=1e-10
    s=spec(mode='coupled');s['geometry'].update(axial_cells=32,radial_cells=8);s['aggregate_viscosity']['table']=str((a.output/'evolving.table').resolve())
    d=read(run('transverse',s));r=read(run('transverse_repeat',s));m=read(run('transverse_mpi',s,mpi=True))
    records['repeat_absolute']=discrepancy(r,d,1);records['mpi_normalized']=discrepancy(m,d,1e-8)
    records['transverse_abs_flux_max']=float(max(d['transverse_abs_internal_flux_m3_s']))
    records['concentration_range_final']=float(d['c_next_max_kg_m3'][-1]-d['c_next_min_kg_m3'][-1])
    assert records['repeat_absolute']<=1e-12 and records['mpi_normalized']<=1e-6
    assert records['transverse_abs_flux_max']>1e-18 and records['concentration_range_final']>1e-6
    records.update(status='PASS',short_runs=len(cases),scalar_fixture_allowance_pp=100*worst,executable_sha256=sha(a.executable),baseline_executable_sha256=sha(a.baseline),traces={k:sha(v/TRACE) for k,v in cases.items() if (v/TRACE).exists()})
    write(a.output/'SHORT_CHECKS.json',records);print(json.dumps(records,indent=2))
if __name__=='__main__':main()
