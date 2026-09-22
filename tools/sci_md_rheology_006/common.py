"""Bounded radial experiment definitions and native execution."""
import json, os, subprocess, sys
from pathlib import Path
from tools.sci_md_rheology_001.analysis import ROOT, sha, write
from tools.sci_md_rheology_002.run import scenario

DOC=ROOT/'docs/analysis/sci_md_rheology_006'
TRACE=Path('postProcessing/wholePull/0/aggregate_radial_intervals_v1.csv')
LAWS=('TR_LINEAR','SW_WATER_ANCHORED_90C')

def radial(pressure=9, resolution='base'):
    s=scenario('uniform_9bar')
    s['scenario_id']=f'synthetic_radial_{pressure}bar'
    s['claim_ceiling']='SOURCE_CONDITIONED_SYNTHETIC_MODEL_DEVELOPMENT'
    s['geometry'].update(axial_cells=1024 if resolution=='axial' else 512,radial_cells=128 if resolution=='radial' else 64)
    s['hydraulics']['target_inlet_pressure_gauge_Pa']=pressure*1e5
    s['hydraulics']['permeability_profile']=dict(type='radial_two_zone',interface_radius_m=.0145,inner_permeability_m2=3e-15,outer_permeability_m2=7.5e-16)
    s['time'].update(delta_t_s=.01 if resolution=='temporal' else .02,field_write_interval_s=5 if resolution=='base' else 30,target_beverage_mass_kg=100.)
    return s

def matrix():
    result={}
    for law in LAWS:
        for case in ('uniform_9bar','reversed_3bar'):
            result[f'control_{law}_{case}']=(law,'control',case)
    for law in LAWS:
        for pressure in (3,9):
            for res in ('base','temporal','axial','radial')+(('property',) if law==LAWS[1] else ()):
                result[f'{law}_{pressure}bar_{res}']=(law,res,pressure)
    return result

def table_name(law,res):
    return law+('.table' if law=='TR_LINEAR' else ('_refined.table' if res=='property' else '_base.table'))

def execute(s,directory,executable,mpi=False):
    """Reuse preparation; explicit radial two-way decomposition for short fixture."""
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    write(directory/'scenario.json',s);case=directory/'case'
    commands=[[sys.executable,str(ROOT/'scripts/prepare_case.py'),'--root',str(ROOT),'--config',str(directory/'scenario.json'),'--case-dir',str(case),'--nprocs','2' if mpi else '1'],['blockMesh','-case',str(case)]]
    if mpi:commands.append(['decomposePar','-case',str(case)])
    commands.append((['mpirun','-np','2',str(executable),'-case',str(case),'-parallel'] if mpi else [str(executable),'-case',str(case)]))
    for i,cmd in enumerate(commands):
        if mpi and i==2:
            (case/'system/decomposeParDict').write_text('FoamFile { version 2.0; format ascii; class dictionary; object decomposeParDict; }\nnumberOfSubdomains 2; method simple; simpleCoeffs { n (1 2 1); delta 0.001; }\n')
        with (directory/f'command-{i}.log').open('w') as f:
            subprocess.run(cmd,cwd=ROOT,env=dict(os.environ,ESPRESSO_CASE_ROOT=str(case)),stdout=f,stderr=subprocess.STDOUT,check=True)
    return case
