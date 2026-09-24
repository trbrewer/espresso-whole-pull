"""Fourteen analytical and serial/repeat/radial-MPI qualification runs."""
import argparse
from .common import *
from .run import run, complete, qualify
from tools.sci_md_rheology_007.short import relative, final_directory
from tools.sci_md_004_stage_c.compare import scalar_internal_values

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args();art=a.artifacts
    specs=json.loads((art/'SHORT_SCENARIOS.json').read_text());data={};checks={}
    for slot,s in specs.items():
        run(art,'short',slot);d=read(art/'runs'/slot/'case'/TRACE);data[slot]=d
        if slot.endswith(('_up','_down','_double','_uniform')):
            h=s['hydraulics'];k=h['permeability_profile'];schedule=h['prescribed_pressure_boundary']
            pressure=np.interp(d['end_s'],schedule['times_s'],schedule['pressures_gauge_Pa'])
            factor=np.pi*.029**2*(.75*k['inner_permeability_m2']+.25*k['outer_permeability_m2'])/(s['liquid']['dynamic_viscosity_Pa_s']*.009011660896432553)
            q=factor*pressure;share=.75*k['inner_permeability_m2']/(.75*k['inner_permeability_m2']+.25*k['outer_permeability_m2'])
            err=float(max(abs(d['Q_total_m3_s']/q-1)));se=float(max(abs(d['Q_inner_m3_s']/d['Q_total_m3_s']/share-1)))
            discrete=float(sum(pressure*d['dt_s']));continuous=sum((b-a)*(x+y)/2 for a,b,x,y in zip(schedule['times_s'],schedule['times_s'][1:],schedule['pressures_gauge_Pa'],schedule['pressures_gauge_Pa'][1:]))
            we=abs(d['water_kg'][-1]/(965*factor*discrete)-1)
            if max(err,se,we)>1e-6:raise ValueError('analytical endpoint flow/water/share')
            if abs(d['water_kg'][-1]-965*factor*continuous)<=abs(965*factor*(discrete-continuous))*.99:raise ValueError('hidden quadrature discrepancy')
            checks[slot]=dict(flow_relative=err,share_relative=se,water_relative=we,continuous_Pa_s=continuous,endpoint_Pa_s=discrete,quadrature_discrepancy_Pa_s=discrete-continuous)
    for model,n in [('C',64),('E2',2)]:
        double=float(max(abs(data[model+'_double']['Q_total_m3_s']*2/data[model+'_up']['Q_total_m3_s']-1)))
        if double>1e-6:raise ValueError('inverse viscosity')
        checks[model+'_double']['inverse_mu_relative']=double
        base=data[model+'_dynamic']
        for variant in ('repeat','mpi'):
            d=data[model+'_'+variant];errors={}
            for key in base:
                if key in ('transverse_abs_internal_flux_m3_s','water_balance_kg','solute_balance_kg'):continue
                floor=1e-14 if 'm3_s' in key else 1e-16 if key.endswith('_m3') else 1e-12 if key.endswith('_kg') or 'Pa_s' in key else 1e-8
                errors[key]=relative(d[key],base[key],floor)
            if max(errors.values())>1e-6:raise ValueError('MPI/repeat disagreement')
            if variant=='repeat' and any(max(abs(d[k]-base[k]))>1e-12 for k in errors):raise ValueError('repeat absolute')
            checks[model+'_'+variant]=errors
        zones=[]
        for rank in (0,1):
            final=final_directory(art/'runs'/(model+'_mpi')/'case'/f'processor{rank}',.2)
            zones.append(sorted(set(scalar_internal_values(final/'permeabilityZoneId',cell_count=32*(1 if n==2 else (3*n//4 if rank==0 else n//4))))))
        if sorted(zones)!=[[0.],[1.]]:raise ValueError('MPI interface not decomposed')
        checks[model+'_mpi_zones']=zones
    records=complete(art,specs)
    write(DOC/'SHORT_QUALIFICATION.json',{k:qualify(art/'runs'/e['id']/'case',specs[k],k.endswith('_mpi')) for k,e in records.items()})
    write(DOC/'SHORT_CHECKS.json',dict(status='PASS',checks=checks,ledger_sha256=sha(art/'ATTEMPTS.jsonl'),started=14,completed=14))
if __name__=='__main__':main()
