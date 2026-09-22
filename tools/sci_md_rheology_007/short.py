"""Six bounded native area/dimensional-reduction fixtures; no science scores."""
import argparse,json,os,subprocess,time
import numpy as np
from .common import *
from .observer import read,adapt,clocks,EXT,CUM
from tools.sci_md_004_stage_c.compare import scalar_internal_values,internal_numeric_values
# Absolute floors are dimensional denominator floors, fixed before execution.
FLOORS=dict(flow_m3_s=1e-14,volume_m3=1e-16,mass_kg=1e-12,concentration_kg_m3=1e-8,pressure_Pa=1e-3,viscosity_Pa_s=1e-12)

def relative(a,b,floor):return float(np.max(abs(np.asarray(a)-b)/np.maximum(abs(np.asarray(b)),floor)))
def fields(case,nz,nr,end):
    n=nz*nr
    # Native structured block ordering is x-fastest; verify using generated centres.
    with (case.parent/'centres.log').open('w') as f:subprocess.run(['postProcess','-case',str(case),'-func','writeCellCentres','-time','0'],stdout=f,stderr=subprocess.STDOUT,check=True)
    xyz=np.array(internal_numeric_values(case/'0/C',cell_count=n)).reshape(n,3)
    x=np.round(xyz[:,0],13);unique=np.unique(x)
    if len(unique)!=nz or any(sum(x==v)!=nr for v in unique):raise ValueError('axial coordinate grouping')
    result={}
    for name,floor in [('dissolvedConcentration',FLOORS['concentration_kg_m3']),('p',FLOORS['pressure_Pa']),('remainingExtractable',FLOORS['concentration_kg_m3'])]:
        values=np.array(scalar_internal_values(case/str(end)/name,cell_count=n))
        groups=np.array([values[x==v] for v in unique]);err=relative(groups,groups[:,0,None],floor)
        if err>1e-6:raise ValueError('radial nonuniformity '+name+' '+str(err))
        result[name]=dict(radial_relative=err,min=float(min(values)),max=float(max(values)))
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args();art=a.artifacts
    specs=json.loads((art/'SHORT_SCENARIOS.json').read_text());exe=art/'bin/espressoWholePullFoam';out=art/'short';out.mkdir(exist_ok=True)
    ledger=out/'INVOCATIONS.jsonl'
    def append(e):
        with ledger.open('a') as f:f.write(json.dumps(e)+'\n');f.flush();os.fsync(f.fileno())
    data={};records={}
    for ident,s in specs.items():
        directory=out/ident
        if directory.exists():raise ValueError('existing short slot; explicit bounded correction required')
        append(dict(id=ident,status='STARTED',executable_sha256=sha(exe),scenario_sha256=digest(s)));t=time.monotonic()
        try:
            case=execute(s,directory,exe);area=(s['geometry']['basket_radius_m']/.029)**2
            d=read(case/TRACE);adapt(d,'uniform',.2,.0056*area)
            # Prepared case retains a complete dictionary, and native inventory checks actual volume.
            generated=json.loads((case/'CASE_SCENARIO_V0_1_4.json').read_text())
            if generated['coffee_bed']['bed_depth_m']!=s['coffee_bed']['bed_depth_m']:raise ValueError('generated depth changed')
            inventory=d['remaining_kg'][0]+d['stored_solute_kg'][0]+d['solute_kg'][0]+d['inlet_loss_kg'][0]
            if abs(inventory-.0056*area)>1e-12:raise ValueError('initial native inventory mapping')
            ff=fields(case,32,s['geometry']['radial_cells'],.2)
            data[ident]=d;records[ident]=dict(area_fraction=area,area_m2=np.pi*s['geometry']['basket_radius_m']**2,volume_m3=np.pi*s['geometry']['basket_radius_m']**2*s['coffee_bed']['bed_depth_m'],bed_depth_m=s['coffee_bed']['bed_depth_m'],dose_kg=s['coffee_bed']['dry_dose_kg'],initial_inventory_kg=float(inventory),fields=ff,elapsed_s=time.monotonic()-t)
            append(dict(id=ident,status='COMPLETE',files={str(p.relative_to(directory)):sha(p) for p in sorted(directory.rglob('*')) if p.is_file()}))
        except BaseException as e:append(dict(id=ident,status='FAILED',reason=str(e)));raise
    comparisons={}
    for zone in ('inner','outer'):
        full=data[zone+'_full']
        for label in ('area','radial'):
            ident=zone+'_'+label;d=data[ident];clocks(full,d);area=records[ident]['area_fraction'];errors={}
            for k in EXT+('Q_m3_s',):
                floor=FLOORS['flow_m3_s'] if k=='Q_m3_s' else FLOORS['volume_m3'] if k=='volume_m3' else FLOORS['mass_kg']
                errors[k]=relative(d[k]/area,full[k],floor)
            for k in ('c_n_min','c_n_max','c_next_min','c_next_max','mu_min','mu_max','mu_next_min','mu_next_max'):
                errors[k]=relative(d[k],full[k],FLOORS['viscosity_Pa_s'] if k.startswith('mu') else FLOORS['concentration_kg_m3'])
            # Pressure fields at equal axial cell indices are also area independent.
            n=32*specs[ident]['geometry']['radial_cells']
            ref=np.array(scalar_internal_values(out/(zone+'_full')/'case/0.2/p',cell_count=64)).reshape(2,32)[0]
            cand=np.array(scalar_internal_values(out/ident/'case/0.2/p',cell_count=n)).reshape(-1,32)[0]
            errors['pressure_Pa']=relative(cand,ref,FLOORS['pressure_Pa'])
            comparisons[ident]=errors
    status='PASS' if all(v<=1e-6 for e in comparisons.values() for v in e.values()) else 'BLOCKED_AREA_OR_DIMENSIONAL_MAPPING'
    write(DOC/'SHORT_CHECKS.json',dict(status=status,relative_tolerance=1e-6,denominator_floors=FLOORS,slots=records,comparisons=comparisons,ledger_sha256=sha(ledger),executable_sha256=sha(exe),started=6,completed=6,failed=0))
    print(status)
if __name__=='__main__':main()
