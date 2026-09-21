#!/usr/bin/env python3
"""Maintained case-generation contract for optional aggregate viscosity."""
import math
from pathlib import Path


def contract(s):
    option = s.get('aggregate_viscosity', {})
    mode = option.get('mode', 'off')
    if mode == 'off':
        return ''
    if mode not in ('observe', 'coupled'):
        raise ValueError('unsupported aggregate viscosity mode')
    h, b, l = s['hydraulics'], s['coffee_bed'], s['liquid']
    if (h.get('pressure_boundary_model', s.get('pressureBoundaryModel', 'prescribedPressure')) != 'prescribedPressure'
        or s.get('flowResistanceModel', 'darcy') != 'darcy'
        or s.get('bedMechanicsModel', 'none') != 'none'
        or 'effective_permeability_evolution' in s
        or h.get('pressure_ramp_time_s') != 0
        or not h['target_inlet_pressure_gauge_Pa'] > h['outlet_pressure_gauge_Pa']
        or h.get('permeability_profile', {}).get('type', 'uniform') not in ('uniform', 'axial_two_layer')
        or s['wetting']['initial_wet_front_m'] != b['bed_depth_m']
        or s['wetting']['initial_saturation'] != 1
        or s['extraction']['model'] != 'single_effective_solute_first_order_with_capacity_ceiling'
        or l['temperature_K'] != 363.15 or l['density_kg_m3'] != 965
        or s['time'].get('start_s', 0) != 0):
        raise ValueError('aggregate viscosity requires fresh saturated static aggregate Darcy at 363.15 K')
    table = Path(option['table']).resolve()
    # Validate metadata and entries here as well as independently in native startup.
    tokens = table.read_text().split()
    if tokens[:4] != ['EWP_AGGREGATE_V1', 'wet_mass_fraction', 'Pa.s', 'linear']:
        raise ValueError('aggregate viscosity table basis/units/interpolation')
    numbers = list(map(float, tokens[4:]))
    if numbers[:4] != [363.15, 965, .1, .24] or len(numbers[4:]) % 2:
        raise ValueError('aggregate viscosity table contract')
    rows = list(zip(numbers[4::2], numbers[5::2]))
    if (len(rows)<3 or rows[0][0]!=0 or rows[-1][0]!=.24 or .1 not in [x for x,y in rows]
        or any(not math.isfinite(x) or not math.isfinite(y) or y<=0 or x<0 or x>.24 for x,y in rows)
        or any(a[0]>=b[0] for a,b in zip(rows,rows[1:]))):
        raise ValueError('aggregate viscosity table entries/coverage')
    if '"' in str(table) or '\n' in str(table):
        raise ValueError('invalid table filename')
    purpose = option.get('purpose', 'scientific')
    if purpose not in ('scientific', 'synthetic'):
        raise ValueError('invalid viscosity purpose')
    return (f'aggregateViscosityMode {mode};\naggregateViscosityPurpose {purpose};\n'
            f'aggregateViscosityTable "{table}";\nliquidTemperature 363.15;\n')
