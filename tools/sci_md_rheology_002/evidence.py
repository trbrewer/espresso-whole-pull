"""Package public-safe provenance and geometry checks from completed native runs."""
import argparse
import csv
import json
import math
from pathlib import Path
import numpy as np
from tools.sci_md_rheology_002.run import DOC, ROOT, rows
from tools.sci_md_rheology_001.analysis import sha, write, axial_reduce
from tools.sci_md_004_stage_c.compare import scalar_internal_values, internal_numeric_values
from scripts.espresso_reference_math import straight_sided_wedge_scale


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args()
    science=a.artifacts/'science';records=[];geometry={}
    for invocation in json.loads((science/'INVOCATIONS.json').read_text()):
        run=science/invocation['id'];case=run/'case';s=json.loads((run/'scenario.json').read_text());d=rows(case)
        record=dict(invocation)
        record['input_hashes']={str(f.relative_to(case)):sha(f) for sub in ('0','system','constant') for f in sorted((case/sub).glob('*')) if f.is_file() and f.name not in ('C','Cx','Cy','Cz','Vc')}
        record['logs_sha256']={f.name:sha(f) for f in sorted(run.glob('command-*.log'))}
        record['trace_sha256']=sha(case/'postProcessing/wholePull/0/traces.csv')
        record['normalized_water_balance_max']=float(max(abs(d['water_balance_kg']))/d['water_kg'][-1])
        record['normalized_solute_balance_max']=float(max(abs(d['solute_balance_kg']))/.0056)
        records.append(record)
        if not (case/'0/Vc').exists():continue
        n=s['geometry']['axial_cells']*s['geometry']['radial_cells'];area=math.pi*s['geometry']['basket_radius_m']**2
        centres=np.array(internal_numeric_values(case/'0/C',cell_count=n)).reshape(n,3)
        volumes=np.array(scalar_internal_values(case/'0/Vc',cell_count=n))
        fields={k:np.array(scalar_internal_values(case/'30'/k,cell_count=n)) for k in ('dissolvedConcentration','permeability','porosity','saturation')}
        z,dz,reduced=axial_reduce(centres,volumes,fields,area,straight_sided_wedge_scale(s['geometry']['wedge_angle_deg']),s['coffee_bed']['bed_depth_m'])
        with (case/'postProcessing/wholePull/0/traces.csv').open() as f:trace=list(csv.DictReader(f))
        radial=max(abs(float(r['radialToAxialVelocityRatio'])) for r in trace)
        if radial>1e-7:raise ValueError('transverse flow outside one-dimensional diagnostic')
        geometry[invocation['id']]=dict(full_area_m2=area,sector_scale=straight_sided_wedge_scale(s['geometry']['wedge_angle_deg']),
            summed_axial_thickness_m=float(sum(dz)),axial_groups=len(z),radial_to_axial_velocity_max=radial,
            radial_scalar_invariance='PASS (inherited axial_reduce relative 1e-7)',
            porosity_range=[float(min(reduced['porosity'])),float(max(reduced['porosity']))],
            saturation_range=[float(min(reduced['saturation'])),float(max(reduced['saturation']))])
    write(DOC/'RUNS.json',dict(scientific_invocations=records,full_run_budget=18,full_run_count=len(records),failed_full_runs=sum(r['status']!='COMPLETE' for r in records),
        geometry=geometry,source_derived_runtime_inputs_redistributed=False,
        external_artifacts='Owner-retained SCI-MD-RHEOLOGY-002 directory; provide explicit artifact root',
        reused_evidence='Accepted source audit/adapter/scenarios; accepted baseline executable used in short compatibility fixtures. No prior concentration fields reused as coupled runs.'))

if __name__=='__main__':main()
