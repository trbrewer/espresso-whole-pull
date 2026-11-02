#!/usr/bin/env python3
"""Form A transfer and native 1D verification; no fitting or campaign dispatch."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np

import e1_verification as E1
from puckworks_historical_lock import RUNTIME_COMMIT, RUNTIME_TREE

ROOT = Path(__file__).resolve().parents[1]
TABLE = 'docs/research/PRESSURE_PEAK_STAGE_D0/RESULT_TABLE.csv'
NOMINAL = E1.NOMINAL


def saved_inputs(puckworks):
    """Ordinary point fits only, never a median or a bootstrap refit."""
    identity = subprocess.check_output(
        ['git', '-C', str(puckworks), 'rev-parse', 'HEAD', 'HEAD^{tree}'], text=True).split()
    if identity != [RUNTIME_COMMIT, RUNTIME_TREE]:
        raise ValueError('Form A requires the exact locked PW commit and tree')
    csv.field_size_limit(100_000_000)
    wanted = {'DESCRIPTIVE_ALL', *(f'HYD-LOCO-{p:.1f}' for p in NOMINAL)}
    bank = {}
    with (puckworks/TABLE).open() as stream:
        for row in csv.DictReader(stream):
            if (row['record_type'] != 'point_replay' or row['candidate'] != 'A'
                    or row['fold'] not in wanted):
                continue
            fold = row['fold']
            if fold in bank:
                raise ValueError('Duplicate saved point fold: '+fold)
            p = json.loads(row['parameters'])
            if p['P0_bar'] != 0 or p['Mc_fixed_g'] != float(row['Mc_fixed_g']):
                raise ValueError('D0 fixed-bank identity mismatch')
            bank[fold] = dict(aGPerSBar=p['a_g_s_bar'], pstarBar=p['Pstar_bar'],
                             n=p['n'], pdBar=p['Pd_bar'], mcG=p['Mc_fixed_g'])
    if set(bank) != wanted:
        raise ValueError('Missing ordinary or descriptive D0 point fit')
    return bank


def scenario(parameters, arm='A0', pressure=9., dt=.005, *, g1=False, xc=None,
             history=None, axial_cells=None, radial_cells=None):
    cfg = json.loads((ROOT/'config/reference_R0.json').read_text())
    cfg['scenario_id'] = 'FORM_A_'+arm
    cfg['mode'] = 'verification_fixture' if g1 else 'capability_demonstration'
    cfg['time'].update(end_s=100., delta_t_s=dt, field_write_interval_s=100.)
    cfg['hydraulics'].update(target_inlet_pressure_gauge_Pa=max(pressure, 0.)*1e5,
                             pressure_ramp_time_s=0.)
    cfg['form_a_whole_bed_closure'] = dict(parameters, enabled=True, arm=arm)
    if arm == 'A2':
        if xc is None:
            raise ValueError('A2 needs the measured A1 Xc; no default is permitted')
        cfg['form_a_whole_bed_closure']['xc'] = xc
        cfg['form_a_pressure_solver_tolerance'] = 1e-14
    if g1:
        cfg['geometry'].update(axial_cells=64, radial_cells=1)
        cfg['wetting'].update(initial_saturation=1., initial_wet_front_m=cfg['coffee_bed']['bed_depth_m'])
        cfg['coffee_bed']['initial_extractable_fraction_dry_basis'] = 0.
        cfg['extraction']['rate_constant_1_s'] = 0.
        cfg['liquid']['effective_solute_diffusivity_m2_s'] = 0.
    if axial_cells is not None:
        cfg['geometry']['axial_cells'] = axial_cells
    if radial_cells is not None:
        cfg['geometry']['radial_cells'] = radial_cells
    if history is not None:
        h = cfg['hydraulics']
        del h['target_inlet_pressure_gauge_Pa'], h['pressure_ramp_time_s']
        h['pressure_boundary_model'] = 'prescribedPressureHistory'
        h['prescribed_pressure_boundary'] = dict(schedule_type='piecewiseLinear',
            times_s=list(history[0]), pressures_gauge_Pa=(np.maximum(np.asarray(history[1]), 0.)*1e5).tolist())
    return cfg


def python_flow(puckworks, parameters, times, pressure):
    """Evaluate the actual saved PW form; importing never invokes its fitter."""
    sys.path.insert(0, str(puckworks))
    from puckworks.analysis.pressure_peak_stage_c3e import flow
    p = [parameters[k] for k in ('aGPerSBar', 'pstarBar', 'n', 'pdBar')]
    q, mass, _ = flow(p, np.asarray(pressure), np.asarray(times), parameters['mcG'], 'A', False)
    return q, mass


def capacity_peak(parameters):
    """Unique positive maximum for the saved n>=1 form, no fit."""
    p = parameters
    def derivative(pressure):
        z = (pressure/p['pdBar'])**p['n']
        return (p['n']*z/(pressure*math.expm1(z)) if z < 700 else 0.)-1/p['pstarBar']
    lo, hi = 1e-9, max(p['pdBar'], p['pstarBar'])
    while derivative(hi) > 0:
        hi *= 2
    for _ in range(80):
        mid = (lo+hi)/2
        if derivative(mid) > 0: lo = mid
        else: hi = mid
    return (lo+hi)/2


def xc_at_mass(rows, mc):
    """Initial-inventory-weighted X, interpolated at the first M=Mc crossing."""
    mass = np.array([0., *(float(r['cup_water_mass_kg'])*1000 for r in rows)])
    x = np.array([0., *(float(r['form_a_bed_mean_x']) for r in rows)])
    if np.any(np.diff(mass) < 0) or np.any(np.diff(x) < -1e-14):
        raise ValueError('Non-monotonic mass or extracted fraction')
    if mc <= 0 or mass[-1] < mc:
        raise ValueError('Outlet mass did not reach Mc; no extrapolated Xc')
    i = int(np.searchsorted(mass, mc, side='left'))
    result = float(x[i-1]+(x[i]-x[i-1])*(mc-mass[i-1])/(mass[i]-mass[i-1]))
    if not 0 < result <= 1:
        raise ValueError('Invalid measured Xc')
    return result


def run_case(work, name, cfg, exe, ranks=1):
    work = Path(work).resolve()
    if work == ROOT or ROOT in work.parents:
        raise ValueError('Native outputs must remain outside Git')
    work.mkdir(parents=True, exist_ok=True)
    return E1.run_case(work, name, cfg, exe, ranks)


def g1(args):
    p = saved_inputs(args.puckworks)['DESCRIPTIVE_ALL']
    times = np.linspace(0, 100, 10001)
    references, _ = python_flow(args.puckworks, p, times,
                                np.repeat(np.asarray(NOMINAL)[:, None], len(times), axis=1))
    results = []
    for pressure, reference in zip(NOMINAL, references[:, -1]):
        cfg = scenario(p, 'A0', pressure, .005, g1=True)
        rows, wall = run_case(args.work, f'g1-{pressure:g}', cfg, args.executable)
        actual = float(rows[-1]['outlet_flow_m3_s'])*965000
        tolerance = max(.02, .05*abs(float(reference)))  # Existing E1 G1 band, unchanged.
        results.append(dict(pressure_bar=pressure, python_g_s=float(reference), solver_g_s=actual,
            deviation_g_s=abs(actual-reference), tolerance_g_s=tolerance,
            within_existing_band=bool(abs(actual-reference) <= tolerance), wall_seconds=wall,
            core_hours=wall/3600))
        E1.write_csv(args.work/'G1.csv', results)
        print(results[-1], flush=True)
        if abs(actual-reference) > tolerance:
            raise ValueError('A0 uniform parity exceeds existing E1 G1 band')



def extraction_check(args):
    p = saved_inputs(args.puckworks)['DESCRIPTIVE_ALL']
    # Synthetic Xc tests the extraction/transport coupling, not the scientific normalization.
    cfg = scenario(p, 'A2', 6., .005, xc=.4, axial_cells=64, radial_cells=1)
    cfg['mode'] = 'verification_fixture'
    rows, wall = run_case(args.work, 'extraction-a2', cfg, args.executable)
    increments = [float(r['form_a_min_cell_x_increment']) for r in rows]
    if min(increments) < 0 or float(rows[-1]['form_a_bed_mean_x']) <= 0:
        raise ValueError('Extracted cell fractions are not monotonic and active')
    if float(rows[-1]['cup_solute_mass_kg']) <= 0:
        raise ValueError('Solute transport is inactive')
    report = dict(synthetic_xc=.4, min_cell_x_increment=min(increments),
        final_bed_mean_x=float(rows[-1]['form_a_bed_mean_x']),
        final_cup_solute_mass_kg=float(rows[-1]['cup_solute_mass_kg']),
        wall_seconds=wall, core_hours=wall/3600,
        balance_checks=E1.balance_bounds(rows, cfg))
    (args.work/'extraction_check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))




def wetting_check(args):
    p = saved_inputs(args.puckworks)['DESCRIPTIVE_ALL']
    cfg = scenario(p, 'A1', 6., .005, axial_cells=64, radial_cells=1)
    cfg['mode'] = 'verification_fixture'
    rows, wall = run_case(args.work, 'wetting-a1', cfg, args.executable)
    bed, fluid, geometry = cfg['coffee_bed'], cfg['liquid'], cfg['geometry']
    capacity = p['aGPerSBar']*p['pdBar']*(-math.expm1(-(6/p['pdBar'])**p['n']))*math.exp(-6/p['pstarBar'])
    pore_water_g = 1000*fluid['density_kg_m3']*math.pi*geometry['basket_radius_m']**2*bed['bed_depth_m']*bed['initial_porosity']
    expected = pore_water_g/(2*capacity*math.exp(-1))
    actual = float(rows[-1]['first_drip_s'])
    report = dict(expected_first_drip_s=expected, native_first_drip_s=actual,
        absolute_difference_s=abs(actual-expected), wall_seconds=wall, core_hours=wall/3600,
        mass_before_outflow_g=max(float(r['form_a_mass_g']) for r in rows if float(r['time_s'])<=actual))
    (args.work/'wetting_check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


def off_check(args):
    if args.baseline_executable is None:
        raise ValueError('off verification requires a separately built main executable')
    cfg = scenario(saved_inputs(args.puckworks)['DESCRIPTIVE_ALL'], 'A0', 9., .005,
                   axial_cells=64, radial_cells=1)
    del cfg['form_a_whole_bed_closure']
    cfg['mode'] = 'verification_fixture'
    _, baseline_wall = run_case(args.work, 'off-main', cfg, args.baseline_executable)
    cfg['form_a_whole_bed_closure'] = dict(enabled=False)
    _, candidate_wall = run_case(args.work, 'off-candidate', cfg, args.executable)
    files = ['postProcessing/wholePull/0/traces.csv',
             'constant/espressoModelProperties']
    # Compare every native final field, not logs containing wall times and paths.
    final = next(p for p in (args.work/'off-main').iterdir()
                 if p.is_dir() and p.name.replace('.', '', 1).isdigit()
                 and math.isclose(float(p.name), 100., abs_tol=1e-8))
    files += [final.name+'/'+p.name for p in sorted(final.iterdir()) if p.is_file()]
    hashes = {}
    for name in files:
        old = (args.work/'off-main'/name).read_bytes()
        new = (args.work/'off-candidate'/name).read_bytes()
        if old != new:
            raise ValueError('Disabled path differs from main: '+name)
        hashes[name] = hashlib.sha256(new).hexdigest()
    report = dict(compared_main_commit='569f3579ffa5ad607e05ec11b405a4771cd3f130',
        byte_identical=hashes, wall_seconds=baseline_wall+candidate_wall,
        core_hours=(baseline_wall+candidate_wall)/3600)
    (args.work/'off_check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=['g1', 'extraction', 'wetting', 'off', 'expectation'])
    p.add_argument('--puckworks', type=Path, required=True)
    p.add_argument('--work', type=Path)
    p.add_argument('--executable', type=Path)
    p.add_argument('--baseline-executable', type=Path)
    args = p.parse_args()
    if args.phase in {'g1', 'extraction', 'wetting', 'off'}:
        if args.work is None or args.executable is None:
            p.error('native verification requires --work and --executable')
        args.work.mkdir(parents=True, exist_ok=True)
        {'g1': g1, 'extraction': extraction_check, 'wetting': wetting_check, 'off': off_check}[args.phase](args)
    else:
        parameters = saved_inputs(args.puckworks)['DESCRIPTIVE_ALL']
        print(json.dumps(dict(parameters=parameters, capacity_peak_bar=capacity_peak(parameters)), indent=2))


if __name__ == '__main__':
    main()
