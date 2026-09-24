#!/usr/bin/env python3
"""Maintained case-generation contract for optional aggregate viscosity."""
import math
from pathlib import Path
from scripts.radial_mesh import contract as radial_mesh_contract


def contract(s):
    mesh = radial_mesh_contract(s)
    option = s.get('aggregate_viscosity', {})
    mode = option.get('mode', 'off')
    if mode == 'off':
        return ''
    if mode not in ('observe', 'coupled', 'bulkCoupled'):
        raise ValueError('unsupported aggregate viscosity mode')
    h, b, l = s['hydraulics'], s['coffee_bed'], s['liquid']
    boundary = h.get('pressure_boundary_model', s.get('pressureBoundaryModel', 'prescribedPressure'))
    history = boundary == 'prescribedPressureHistory'
    if history:
        # Reuse the native case-parser contract; no scalar target/ramp fabrication.
        from scripts.prepare_case import pressure_history_contract
        schedule = pressure_history_contract(s)
        if (mode == 'bulkCoupled'
            or h.get('permeability_profile', {}).get('type') != 'radial_two_zone'
            or not all(p > h['outlet_pressure_gauge_Pa'] for p in schedule['pressures_gauge_Pa'])):
            raise ValueError('history viscosity requires local radial flow above outlet pressure')
    if (boundary not in ('prescribedPressure', 'prescribedPressureHistory')
        or s.get('flowResistanceModel', 'darcy') != 'darcy'
        or s.get('bedMechanicsModel', 'none') != 'none'
        or 'effective_permeability_evolution' in s
        or (not history and (h.get('pressure_ramp_time_s') != 0
            or not h['target_inlet_pressure_gauge_Pa'] > h['outlet_pressure_gauge_Pa']))
        or h.get('permeability_profile', {}).get('type', 'uniform') not in (('uniform', 'axial_two_layer') if mode == 'bulkCoupled' else ('uniform', 'axial_two_layer', 'radial_two_zone'))
        or s['wetting']['initial_wet_front_m'] != b['bed_depth_m']
        or s['wetting']['initial_saturation'] != 1
        or s['extraction']['model'] != 'single_effective_solute_first_order_with_capacity_ceiling'
        or l['temperature_K'] != 363.15 or l['density_kg_m3'] != 965
        or s['time'].get('start_s', 0) != 0):
        raise ValueError('aggregate viscosity requires fresh saturated static aggregate Darcy at 363.15 K')
    profile = h.get('permeability_profile', {})
    if profile.get('type') == 'radial_two_zone':
        radius = s['geometry']['basket_radius_m']
        interface = profile['interface_radius_m']
        n = s['geometry']['radial_cells']
        values = (radius, interface, profile['inner_permeability_m2'], profile['outer_permeability_m2'], h['outlet_pressure_gauge_Pa'])
        if not history:
            values += (h['target_inlet_pressure_gauge_Pa'],)
        if not all(math.isfinite(v) for v in values) or not 0 < interface < radius or min(values[2:4]) <= 0:
            raise ValueError('invalid radial aggregate geometry/permeability/pressure')
        if mesh is None and (s['geometry'].get('radial_grading', 1) != 1 or abs(interface/radius*n-round(interface/radius*n)) > 1e-10):
            raise ValueError('radial aggregate interface must align with mesh')
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
