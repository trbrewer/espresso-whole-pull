"""Twelve prespecified short slots, analytical and dynamic communication gates."""
import argparse
import json
import numpy as np
from .common import *
from .run import run
from .observer import read, native, clocks
from tools.sci_md_rheology_007.short import relative, final_directory
from tools.sci_md_004_stage_c.compare import scalar_internal_values

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args();art=a.artifacts
    specs=json.loads((art/'SHORT_SCENARIOS.json').read_text());events={};data={};checks={}
    for slot,s in specs.items():
        events[slot]=run(art,slot,short=True)
        data[slot]=read(art/'short'/events[slot]['id']/'case'/TRACE)
        if slot.endswith(('water','double','uniform')):
            k=s['hydraulics']['permeability_profile'];ki,ko=k['inner_permeability_m2'],k['outer_permeability_m2']
            q=np.pi*.029**2*(.25*ki+.75*ko)*9e5/(s['liquid']['dynamic_viscosity_Pa_s']*.009011660896432553)
            share=.25*ki/(.25*ki+.75*ko);d=data[slot]
            qe=float(max(abs(d['Q_total_m3_s']/q-1)));se=float(max(abs((d['Q_inner_m3_s']/d['Q_total_m3_s'])/share-1)))
            if qe>1e-6 or se>1e-6:raise ValueError('analytical Darcy check')
            checks[slot]=dict(Q_relative=qe,share_relative=se,expected_core_share=share)
    for n in (2,4,8):
        error=float(max(abs(data[f'E{n}_double']['Q_total_m3_s']*2/data[f'E{n}_water']['Q_total_m3_s']-1)))
        if error>1e-6:raise ValueError('doubling viscosity')
        checks[f'E{n}_double']['inverse_viscosity_relative']=error
    base=data['E2_dynamic'];comparisons={}
    for name in ('E2_repeat','E2_mpi'):
        d=data[name];clocks(d,base);errors={}
        for key in base:
            # Restricted diagnostic is explicitly excluded: it is not a complete exchange measure.
            if key in ('transverse_abs_internal_flux_m3_s', 'water_balance_kg', 'solute_balance_kg'):continue
            # Balance residuals are cancellation quantities; native() already applies
            # the inherited absolute 1e-8 kg bound independently to each run.
            floor=1e-14 if 'm3_s' in key else 1e-16 if key.endswith('_m3') else 1e-12 if key.endswith('_kg') else 1e-12 if 'Pa_s' in key else 1e-8
            errors[key]=relative(d[key],base[key],floor)
        if max(errors.values())>1e-6:raise ValueError('serial/repeat/MPI mismatch '+name)
        if name=='E2_repeat' and any(max(abs(d[k]-base[k]))>1e-12 for k in errors):raise ValueError('repeat absolute mismatch')
        comparisons[name]=errors
    zone_sets=[]
    for rank in (0,1):
        case=art/'short/E2_mpi/case'/f'processor{rank}'
        values=scalar_internal_values(final_directory(case,.2)/'permeabilityZoneId',cell_count=32)
        zone_sets.append(sorted(set(values)))
    if sorted(zone_sets)!=[[0.],[1.]]:raise ValueError('MPI radial material interface')
    ledger=art/'short/INVOCATIONS.jsonl';all_events=[json.loads(s) for s in ledger.read_text().splitlines()]
    write(DOC/'SHORT_CHECKS.json',dict(status='PASS',analytical=checks,consistency=comparisons,MPI_zone_sets=zone_sets,slots={k:{p:v for p,v in e.items() if p!='files'} for k,e in events.items()},ledger_sha256=sha(ledger),started=sum(e['status']=='STARTED' for e in all_events),completed=sum(e['status']=='COMPLETE' for e in all_events),failed=sum(e['status']=='FAILED' for e in all_events),meaning='Mesh geometry, annular volumes, native signed interface advective exchange; no total diffusion attribution'))
    print('12 short slots PASS')
if __name__=='__main__':main()
