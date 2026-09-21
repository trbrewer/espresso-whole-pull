#!/usr/bin/env python3
"""SCI-MD-RHEOLOGY-001: bounded frozen-field analysis, never a coupled solver."""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.sci_md_004_stage_c.compare import scalar_internal_values, internal_numeric_values
from scripts.espresso_reference_math import straight_sided_wedge_scale, discrete_layered_pressure_reference

PIN = '2058d0e947ee9eb92c52d64f6165b810f1fb4732'
AGGREGATE = 'single_effective_solute_first_order_with_capacity_ceiling'
DOC = ROOT / 'docs/analysis/sci_md_rheology_001'
REF = 'uniform_9bar'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)+'\n')


def source(puckworks):
    p = Path(puckworks).resolve()
    if subprocess.check_output(['git', '-C', str(p), 'rev-parse', 'HEAD'], text=True).strip() != PIN:
        raise ValueError('analysis source pin mismatch')
    if subprocess.check_output(['git', '-C', str(p), 'status', '--porcelain'], text=True).strip():
        raise ValueError('analysis source must be clean')
    authority_path=DOC/'AUTHORITY.json'
    if authority_path.exists():
        authority=json.loads(authority_path.read_text())
        if any(sha(p/f)!=h for f,h in authority['puckworks_source_hashes'].items()):
            raise ValueError('source artifact identity mismatch')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(p))
    data = importlib.import_module('puckworks.data')
    water = importlib.import_module('puckworks.models.pannusch2024.closures')
    if not Path(data.__file__).resolve().is_relative_to(p):
        raise ValueError('wrong imported Puckworks')
    return data, water


def solids_fraction(c, rho, model=AGGREGATE):
    c = np.asarray(c, float)
    if model != AGGREGATE:
        raise ValueError('incomplete or unqualified species inventory is not aggregate solids')
    if not np.isfinite(rho) or rho <= 0 or not np.all(np.isfinite(c)) or np.any(c < 0):
        raise ValueError('invalid concentration or water density')
    return c / (rho + c)


def viscosity(w, temperature_c, mu_water, measured, excess=1):
    """Input w is wet-basis solids fraction; authoritative loader returns Pa.s."""
    w = np.asarray(w, float)
    tk = temperature_c + 273.15
    if not 295 <= tk <= 365 or not np.all(np.isfinite(w)) or np.any((w < 0) | (w > .24)):
        raise ValueError('unsupported source domain: no clamping or gap bridging')
    if excess not in (1, 2) or not np.isfinite(mu_water) or mu_water <= 0:
        raise ValueError('invalid viscosity treatment')
    xw = 100 * (1-w)
    eta90 = measured(tk, 90.)
    mu = np.array([mu_water + v/.1*(eta90-mu_water) if v < .1
                   else measured(tk, float(x)) for v, x in zip(w.flat, xw.flat)]).reshape(w.shape)
    return mu_water + excess*(mu-mu_water), w < .1


def resistance(mu, dz, k, area):
    mu, dz, k = np.asarray(mu), np.asarray(dz), np.asarray(k)
    if dz.ndim != 1 or k.shape != dz.shape or mu.shape[-1:] != dz.shape:
        raise ValueError('axial shape mismatch')
    if area <= 0 or not all(np.all(np.isfinite(x)) and np.all(x > 0) for x in (mu, dz, k)):
        raise ValueError('nonpositive/nonfinite hydraulic input')
    return np.sum(mu * dz/k, axis=-1)/area


def errors(t, q, reference):
    t, q, reference = map(lambda x: np.asarray(x, float), (t, q, reference))
    if t.ndim != 1 or len(t) < 2 or q.shape != t.shape or reference.shape != t.shape:
        raise ValueError('time/flow shape mismatch')
    if not all(np.all(np.isfinite(x)) for x in (t,q,reference)) or np.any(np.diff(t)<=0) or np.any(reference<=0) or np.any(q<=0):
        raise ValueError('positive-flow window required')
    return dict(integrated=float(np.trapz(abs(q-reference), t)/np.trapz(reference,t)),
                peak=float(np.max(abs(q-reference)/reference)))


def compare(profiles):
    """Estimate alpha from REF once; never refit on pressure or layer conditions."""
    r = profiles[REF]
    alpha = float(np.trapz(r['q'], r['t'])/np.trapz(r['q0'], r['t']))
    return alpha, {name: dict(absolute=errors(p['t'],p['q'],p['q0']),
                             residual=errors(p['t'],p['q'],alpha*p['q0']))
                   for name,p in profiles.items()}


def axial_reduce(centres, volumes, fields, area, scale, length):
    """Group actual cell x centres; dz derives from actual sector volumes."""
    x = np.asarray(centres)[:,0]
    volumes = np.asarray(volumes)
    if np.any(volumes <= 0) or not np.all(np.isfinite(volumes)):
        raise ValueError('invalid volumes')
    keys = np.round(x,12)
    zs = np.unique(keys)
    dz = np.array([volumes[keys==z].sum()*scale/area for z in zs])
    if not np.isclose(dz.sum(),length,rtol=1e-8,atol=0):
        raise ValueError('full-area/sector volume mismatch')
    # Cell centres must coincide with the cumulative-thickness centres (nonuniform supported).
    if not np.allclose(zs,np.cumsum(dz)-dz/2,rtol=1e-7,atol=2e-12):
        raise ValueError('not a contiguous one-dimensional column')
    reduced = {}
    for name, values in fields.items():
        values = np.asarray(values)
        if values.shape != x.shape or not np.all(np.isfinite(values)):
            raise ValueError('invalid cell field')
        means = []
        for z in zs:
            v = values[keys==z]
            if np.ptp(v)>1e-7*max(abs(v).max(),1e-12):
                raise ValueError('radial variation invalidates series reduction: '+name)
            means.append(np.average(v,weights=volumes[keys==z]))
        reduced[name]=np.array(means)
    return zs,dz,reduced


def scenarios(water):
    base = json.loads((ROOT/'config/reference_R0.json').read_text())
    fixture = json.loads((ROOT/'config/fixture_layered_pressure.json').read_text())
    base['mode']='research_scenario'
    base['calibration']={'parameter':None,'note':'Synthetic frozen-field component screen; no experimental fit.'}
    base['claim_ceiling']='FROZEN_FIELD_HYDRAULIC_SENSITIVITY_NOT_PHYSICAL_VALIDATION'
    base['geometry'].update(axial_cells=512, radial_cells=4)
    base['liquid'].update(temperature_K=363.15,dynamic_viscosity_Pa_s=float(water.water_viscosity(363.15)))
    # Preserve the EWP water accounting convention and reference input density.
    base['wetting'].update(initial_saturation=1., initial_wet_front_m=base['coffee_bed']['bed_depth_m'])
    base['time'].update(end_s=30.,delta_t_s=.02,field_write_interval_s=.1,target_beverage_mass_kg=100.)
    base['output'].update(write_format='ascii',write_precision_digits=16)
    base['parallel']['default_subdomains']=1
    base['hydraulics']['pressure_ramp_time_s']=0.
    base['flowResistanceModel']='darcy'
    base['bedMechanicsModel']='none'
    layers=fixture['hydraulics']['permeability_profile']
    length=base['coffee_bed']['bed_depth_m']
    l1=layers['interface_position_m']; k1=layers['upstream_permeability_m2']; k2=layers['downstream_permeability_m2']
    ku=length/(l1/k1+(length-l1)/k2)
    result={}
    for geometry in ('uniform','layered','reversed'):
        for bar in (3,9):
            s=json.loads(json.dumps(base)); name=f'{geometry}_{bar}bar'; s['scenario_id']=name
            h=s['hydraulics']; h.update(target_inlet_pressure_gauge_Pa=bar*1e5,saturated_permeability_m2=ku,wetting_permeability_m2=ku)
            h['permeability_profile']=dict(type='uniform' if geometry=='uniform' else 'axial_two_layer',
                interface_position_m=l1 if geometry!='reversed' else length-l1,
                upstream_permeability_m2=ku if geometry=='uniform' else k1 if geometry=='layered' else k2,
                downstream_permeability_m2=ku if geometry=='uniform' else k2 if geometry=='layered' else k1)
            result[name]=s
    return result


def load_profile(case, s, measured, excess):
    if json.loads((case/'CASE_SCENARIO_V0_1_4.json').read_text()) != s:
        raise ValueError('run scenario differs from declared inputs')
    n=s['geometry']['axial_cells']*s['geometry']['radial_cells']
    area=math.pi*s['geometry']['basket_radius_m']**2
    scale=straight_sided_wedge_scale(s['geometry']['wedge_angle_deg'])
    length=s['coffee_bed']['bed_depth_m']; muw=s['liquid']['dynamic_viscosity_Pa_s']
    centres=np.array(internal_numeric_values(case/'0/C',cell_count=n)).reshape(n,3)
    volumes=np.array(scalar_internal_values(case/'0/Vc',cell_count=n))
    with (case/'postProcessing/wholePull/0/traces.csv').open() as f:
        trace=[{k:float(row[k]) for k in ('time_s','outlet_flow_m3_s','radialToAxialVelocityRatio')}
               for row in csv.DictReader(f)]
    if abs(trace[-1]['time_s']-30)>1e-8:
        raise ValueError('incomplete extraction window')
    if max(abs(row['radialToAxialVelocityRatio']) for row in trace)>1e-7:
        raise ValueError('nonaxial velocity')
    times=sorted((float(p.name),p) for p in case.iterdir() if p.is_dir() and p.name.replace('.','',1).isdigit() and float(p.name)>0)
    expected=np.arange(1,round(30/s['time']['field_write_interval_s'])+1)*s['time']['field_write_interval_s']
    if len(times)!=len(expected) or not np.allclose([t for t,p in times],expected,atol=1e-9,rtol=0):
        raise ValueError('sampling grid incomplete')
    result={'t':[0.], 'r':[], 'q':[], 'q0':[], 'histories':[]}
    lastk=None
    for t,path in times:
        fields={name:np.array(scalar_internal_values(path/name,cell_count=n)) for name in ('dissolvedConcentration','permeability','porosity','saturation')}
        z,dz,f=axial_reduce(centres,volumes,fields,area,scale,length)
        if not np.allclose(f['saturation'],1,atol=1e-12) or not np.allclose(f['porosity'],s['coffee_bed']['initial_porosity'],atol=1e-12):
            raise ValueError('state outside static saturated contract')
        k=f['permeability']
        if lastk is not None and not np.array_equal(k,lastk): raise ValueError('evolving permeability')
        lastk=k
        w=solids_fraction(f['dissolvedConcentration'],s['liquid']['density_kg_m3'],s['extraction']['model'])
        mu,dilute=viscosity(w,90,muw,measured,excess)
        r=float(resistance(mu,dz,k,area)); r0=float(resistance(np.full(len(k),muw),dz,k,area))
        dp=s['hydraulics']['target_inlet_pressure_gauge_Pa']; q0=dp/r0
        if not result['r']:
            result['r'].append(r0); result['q'].append(q0); result['q0'].append(q0)
        result['t'].append(t); result['r'].append(r); result['q'].append(dp/r); result['q0'].append(q0)
        contrib=mu*dz/k
        result['histories'].append(dict(time_s=t,R_Pa_s_m3=r,Q_m3_s=dp/r,Q0_m3_s=q0,
            c_min_kg_m3=float(f['dissolvedConcentration'].min()),c_max_kg_m3=float(f['dissolvedConcentration'].max()),
            solids_min=float(w.min()),solids_max=float(w.max()),weighted_mu_Pa_s=float(np.sum(contrib)/np.sum(dz/k)),
            dilute_cell_fraction=float(np.mean(dilute)),dilute_resistance_fraction=float(np.sum(contrib[dilute])/np.sum(contrib)),
            upstream_resistance_fraction=float(np.sum(contrib[z<length/2])/np.sum(contrib))))
    discrete_q=discrete_layered_pressure_reference(s)['outlet_flow_m3_s']
    hydraulic_error=max(abs(row['outlet_flow_m3_s']/discrete_q-1) for row in trace)
    continuum_error=max(abs(row['outlet_flow_m3_s']/result['q0'][0]-1) for row in trace)
    if hydraulic_error>1e-6: raise ValueError('unchanged EWP fails exact discrete water-flow check')
    if continuum_error>.001: raise ValueError('continuum Q0 discrepancy exceeds 0.1 percent')
    result['hydraulic_relative_error']=hydraulic_error
    result['continuum_hydraulic_relative_error']=continuum_error
    for key in ('t','r','q','q0'): result[key]=np.array(result[key])
    return result


def freeze(puckworks):
    _,water=source(puckworks)
    write(DOC/'SCENARIOS.json',scenarios(water))
    files=['scripts/sci_md_rheology_001.py','scripts/run_sci_md_rheology_001.py','scripts/report_sci_md_rheology_001.py',
           'tools/sci_md_rheology_001/analysis.py','tools/sci_md_rheology_001/runner.py','tools/sci_md_rheology_001/report.py','tests/test_sci_md_rheology_001.py',
           'docs/analysis/sci_md_rheology_001/AUTHORITY.json','docs/analysis/sci_md_rheology_001/PROTOCOL.md','docs/analysis/sci_md_rheology_001/SCENARIOS.json']
    write(DOC/'FREEZE.json',dict(files={p:sha(ROOT/p) for p in files},puckworks_commit=PIN,
        ewp_base='ac49fe939f9e7fb38ba4eabc95d65e2fa47ee666',runtime_lock_sha256=sha(ROOT/'dependencies/puckworks.lock.json')))


def check_freeze(audit):
    f=json.loads((DOC/'FREEZE.json').read_text())
    expected = dict(f['files'])
    amendment = DOC/'POST_RESULT_AMENDMENT.json'
    if amendment.exists():
        a = json.loads(amendment.read_text())
        if a['original_freeze_sha256'] != sha(DOC/'FREEZE.json'):
            raise ValueError('post-result amendment targets another freeze')
        for path, delta in a['files'].items():
            if expected.get(path) != delta['original_sha256']:
                raise ValueError('post-result amendment original hash mismatch')
            expected[path] = delta['amended_sha256']
    if any(sha(ROOT/p)!=h for p,h in expected.items()): raise ValueError('frozen analysis changed')
    if f['puckworks_commit']!=PIN: raise ValueError('wrong analysis authority')
    subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',f['ewp_base'],'HEAD'],check=True)
    if sha(ROOT/'dependencies/puckworks.lock.json')!=f['runtime_lock_sha256']:
        raise ValueError('runtime lock changed')
    authority=json.loads((DOC/'AUTHORITY.json').read_text())
    if any(sha(ROOT/p)!=h for p,h in authority['solver_source_hashes'].items()):
        raise ValueError('solver source changed')
    a=json.loads(Path(audit).read_text())
    if a.get('disposition')!='PASS' or a.get('freeze_sha256')!=sha(DOC/'FREEZE.json') or not a.get('independent_reviewer'):
        raise ValueError('independent pre-result audit missing or not bound to freeze')


def check_output(output):
    p=Path(output).resolve()
    if p.is_relative_to(ROOT) and p!=DOC.resolve():
        raise ValueError('only task reduced summaries may be written inside repository')


def analyze(puckworks, runs, output, audit):
    check_freeze(audit)
    data,_=source(puckworks); runs=Path(runs); output=Path(output); check_output(output); output.mkdir(exist_ok=True,parents=True)
    ss=json.loads((DOC/'SCENARIOS.json').read_text()); summary={}; histories={}
    for variant,excess in [('primary',1),('stress',2)]:
        profiles={name:load_profile(runs/name,s,data.telisromero_eta_measured,excess) for name,s in ss.items()}
        alpha,metrics=compare(profiles)
        summary[variant]=dict(alpha=alpha,metrics=metrics)
        for name,p in profiles.items():
            hist=p['histories']; histories[variant+'/'+name]=hist
            metrics[name].update(hydraulic_relative_error=p['hydraulic_relative_error'],
                concentration_range_kg_m3=[0,max(h['c_max_kg_m3'] for h in hist)],
                weighted_mu_range_Pa_s=[min(p['r'])/p['r'][0]*ss[name]['liquid']['dynamic_viscosity_Pa_s'],max(h['weighted_mu_Pa_s'] for h in hist)],
                dilute_resistance_range=[min(h['dilute_resistance_fraction'] for h in hist),max(h['dilute_resistance_fraction'] for h in hist)])
    write(output/'PRIMARY_SCREEN.json',summary); write(output/'HISTORIES.json',histories)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('action',choices=['freeze','analyze'])
    p.add_argument('--puckworks',required=True,type=Path); p.add_argument('--runs',type=Path); p.add_argument('--output',type=Path); p.add_argument('--audit',type=Path)
    a=p.parse_args()
    if a.action=='freeze': freeze(a.puckworks)
    else:
        if None in (a.runs,a.output,a.audit): p.error('analyze requires --runs --output --audit')
        analyze(a.puckworks,a.runs,a.output,a.audit)

if __name__=='__main__': main()
