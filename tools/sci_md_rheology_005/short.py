"""Predeclared 23 short runs (0.2 s, 32x2; one 64x2) and startup rejections."""
import argparse, copy, csv, json, re, shutil, subprocess
from pathlib import Path
import numpy as np
from tools.sci_md_rheology_001.analysis import sha, write
from tools.sci_md_rheology_002.run import scenario, execute, rows, CASES
from tools.sci_md_rheology_002.verify import traces
from tools.sci_md_rheology_002.export import HEADER
from scripts.espresso_reference_math import discrete_layered_pressure_reference

def read_bulk(case):
    a=np.genfromtxt(case/'postProcessing/wholePull/0/aggregate_bulk_intervals.csv',delimiter=',',names=True)
    return {k:np.atleast_1d(a[k]) for k in a.dtype.names}

def main():
    p=argparse.ArgumentParser()
    for k in ('output','executable','baseline'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    mu=scenario(CASES[0])['liquid']['dynamic_viscosity_Pa_s']
    table=a.output/'evolving.table';table.write_text(HEADER+f'0 {mu:.17g}\n.1 {2*mu:.17g}\n.24 {4*mu:.17g}\n')
    const=a.output/'constant.table';const.write_text(HEADER+''.join(f'{w} {2*mu:.17g}\n' for w in (0,.1,.24)))
    records={};cases={};ledger=[]
    def run(name,s,old=False,mpi=1):
        ledger.append(dict(id=name,status='STARTED'));write(a.output/'ATTEMPTS.json',ledger)
        try:case=execute(s,a.output/name,a.baseline if old else a.executable,mpi)
        except BaseException:ledger[-1]['status']='FAILED';write(a.output/'ATTEMPTS.json',ledger);raise
        ledger[-1]['status']='COMPLETE';write(a.output/'ATTEMPTS.json',ledger);cases[name]=case;return case
    def spec(c,mode=None,t=table,n=32):
        s=scenario(c);s['geometry'].update(axial_cells=n,radial_cells=2)
        s['time'].update(end_s=.2,field_write_interval_s=.2)
        if mode:s['aggregate_viscosity']=dict(mode=mode,purpose='synthetic',table=str(t.resolve()))
        return s
    def discrepancy(x,y,floor=1):
        return max(float(max(abs(x[k]-y[k])))/max(float(max(abs(y[k]))),floor)
            for k in x if k in y and 'wall' not in k.lower() and 'cpu' not in k.lower() and 'balance' not in k)
    for c in CASES:
        base=traces(run(c+'_old_absent',spec(c),True))
        for mode in (None,'off'):
            d=traces(run(c+'_'+str(mode),spec(c,mode)));err=discrepancy(d,base)
            records[c+'_'+str(mode)]=err;assert err<=1e-10
        for mode in ('observe','coupled'):
            old=rows(run(c+'_old_'+mode,spec(c,mode),True));new=rows(run(c+'_'+mode,spec(c,mode)))
            err=discrepancy(new,old);records[c+'_'+mode]=err;assert err<=1e-10
        cg=rows(run(c+'_constant_G',spec(c,'bulkCoupled',const)))
        cc=rows(run(c+'_constant_C',spec(c,'coupled',const)))
        err=discrepancy(cg,cc);records[c+'_constant_C_G']=err;assert err<=1e-10
        ref=discrete_layered_pressure_reference(spec(c))['outlet_flow_m3_s']/2
        records[c+'_analytical_relative']=float(max(abs(cg['Q_m3_s']/ref-1)))
        assert records[c+'_analytical_relative']<=1e-6
    s=spec(CASES[1],'bulkCoupled');g=rows(run('bulk_evolving',s));repeat=rows(run('bulk_repeat',s));mpi=rows(run('bulk_mpi',s,mpi=2))
    records['determinism_absolute']=max(float(max(abs(g[k]-repeat[k]))) for k in g)
    records['MPI_normalized']=discrepancy(mpi,g,1e-8)
    assert records['determinism_absolute']<=1e-12 and records['MPI_normalized']<=1e-6
    b=read_bulk(cases['bulk_evolving']);bm=read_bulk(cases['bulk_mpi'])
    records['bulk_MPI_normalized']=discrepancy(bm,b,1e-8);assert records['bulk_MPI_normalized']<=1e-6
    assert np.allclose(b['stored_dissolved_mass_kg'],np.r_[0.,g['stored_solute_kg'][:-1]],atol=1e-14,rtol=1e-12)
    assert b['applied_mu_Pa_s'][-1]>b['applied_mu_Pa_s'][0]
    expected_volume=np.pi*s['geometry']['basket_radius_m']**2*s['coffee_bed']['bed_depth_m']*s['coffee_bed']['initial_porosity']
    assert np.allclose(b['pore_water_volume_m3'],expected_volume,rtol=1e-12,atol=0)
    z=spec(CASES[0],'bulkCoupled');z['extraction']['rate_constant_1_s']=0
    zero=rows(run('zero',z));assert max(zero['c_next_max'])==0
    refined=rows(run('layer64',spec(CASES[1],'bulkCoupled',const,64)))
    coarse=rows(cases[CASES[1]+'_constant_G'])
    records['operator_layer32']=float(max(abs(coarse['Q_m3_s']/coarse['Q_cont_m3_s']-1)))
    records['operator_layer64']=float(max(abs(refined['Q_m3_s']/refined['Q_cont_m3_s']-1)))
    assert records['operator_layer64']<records['operator_layer32']
    assert len(cases)==23
    records['balance_max_kg']=0.;records['correction_kg']=0.
    for case in cases.values():
        if not (case/'postProcessing/wholePull/0/aggregate_intervals.csv').exists():continue
        d=rows(case);records['balance_max_kg']=max(records['balance_max_kg'],float(max(abs(d['water_balance_kg']))),float(max(abs(d['solute_balance_kg']))))
        records['correction_kg']=max(records['correction_kg'],float(sum(abs(d['correction_kg']))))
    assert records['balance_max_kg']<=1e-8 and records['correction_kg']<=1e-10
    # Independent native parser/startup checks bypass Python generation.
    mutations={'temperature':('liquidTemperature','360'),'density':('liquidDensity','1000'),
      'ramp':('pressureRampTime','1'),'wetting':('initialWetFront','0'),
      'mode':('aggregateViscosityMode','unknown'),'purpose':('aggregateViscosityPurpose','unknown'),
      'flow':('pressureBoundaryModel','prescribedFlow'),'mechanics':('bedMechanicsModel','unknown'),
      'resistance':('flowResistanceModel','unknown'),'profile':('permeabilityProfile','unknown'),
      'restart':('startFrom','latestTime')}
    rejected={}
    for name,(key,value) in mutations.items():
        case=a.output/('reject_'+name)
        for folder in ('0','constant','system'):shutil.copytree(cases['bulk_evolving']/folder,case/folder)
        path=case/('system/controlDict' if name=='restart' else 'constant/espressoModelProperties')
        content,n=re.subn(r'(?m)^'+key+r'\s+[^;]+;',key+' '+value+';',path.read_text())
        if n!=1:raise ValueError('mutation not applied '+name)
        path.write_text(content)
        proc=subprocess.run([str(a.executable),'-case',str(case)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (case/'startup.log').write_text(proc.stdout)
        assert proc.returncode!=0 and 'FOAM FATAL' in proc.stdout,(name,proc.stdout[-1000:])
        rejected[name]=proc.returncode
    records.update(status='PASS',native_short_runs=len(cases),startup_rejections=rejected,
        executable_sha256=sha(a.executable),baseline_executable_sha256=sha(a.baseline))
    write(a.output/'SHORT_CHECKS.json',records);print(json.dumps(records,indent=2))
if __name__=='__main__':main()
