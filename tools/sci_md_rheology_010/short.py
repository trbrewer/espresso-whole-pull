"""Exactly ten native short integrations, using inherited limits."""
import argparse
from .common import *
from .run import run, complete
from tools.sci_md_rheology_007.short import relative


def qualify_short(art):
    specs=json.loads((art/'SHORT_SCENARIOS.json').read_text());checks={};data={}
    for slot,s in specs.items():
        e=run(art,'short',slot);d=read(art/'runs'/e['id']/'case'/TRACE);data[slot]=d
        if slot.endswith(('_up','_down')):
            k=s['hydraulics']['permeability_profile'];h=s['hydraulics']['prescribed_pressure_boundary']
            pressure=np.interp(d['end_s'],h['times_s'],h['pressures_gauge_Pa'])
            mean=.25*k['inner_permeability_m2']+.75*k['outer_permeability_m2']
            factor=np.pi*.029**2*mean/(s['liquid']['dynamic_viscosity_Pa_s']*.009011660896432553)
            q=factor*pressure;oldq=q*((.25*3e-15+.75*7.5e-16)/mean)
            errors=dict(flow_relative=float(max(abs(d['Q_total_m3_s']/q-1))),
                core_share_relative=float(max(abs(d['Q_inner_m3_s']/d['Q_total_m3_s']/(1/13)-1))),
                old_new_flow_relative=float(max(abs(d['Q_total_m3_s']/oldq-1))),
                discrete_water_relative=float(max(abs(d['water_kg']/(965*np.cumsum(q*d['dt_s']))-1))))
            if max(errors.values())>LIMITS['analytical_relative']:raise ValueError('constant-viscosity analytical qualification')
            errors.update(endpoint_pressure_integral_Pa_s=float(sum(pressure*d['dt_s'])),old_core_share=4/7,new_core_share=1/13)
            checks[slot]=errors
    for model in ('C','E2'):
        base=data[model+'_dynamic']
        for variant in ('repeat','mpi'):
            d=data[model+'_'+variant];errors={}
            for k in base:
                if k in ('transverse_abs_internal_flux_m3_s','water_balance_kg','solute_balance_kg'):continue
                f=LIMITS['mpi_floors'];floor=f['flow_m3_s'] if 'm3_s' in k else f['volume_m3'] if k.endswith('_m3') else f['mass_kg'] if k.endswith('_kg') else f['viscosity_Pa_s'] if 'Pa_s' in k else f['other']
                errors[k]=relative(d[k],base[k],floor)
            if max(errors.values())>LIMITS['mpi_relative']:raise ValueError('MPI/repeat disagreement')
            if variant=='repeat' and any(max(abs(d[k]-base[k]))>LIMITS['repeat_absolute'] for k in errors):raise ValueError('repeat absolute')
            checks[model+'_'+variant]=errors
    complete(art,specs)
    write(DOC/'SHORT_CHECKS.json',dict(status='PASS',completed=10,checks=checks,ledger_sha256=sha(art/'ATTEMPTS.jsonl')))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);qualify_short(p.parse_args().artifacts)
