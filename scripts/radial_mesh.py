#!/usr/bin/env python3
"""Explicit conforming two-zone wedge mesh; legacy scenarios are untouched."""
import math


def contract(s):
    g = s.get('geometry', {})
    if not isinstance(g, dict) or 'radial_mesh' not in g:
        return None
    m = g['radial_mesh']
    if not isinstance(m, dict) or set(m) != {'type', 'inner_cells', 'outer_cells'}:
        raise ValueError('radial_mesh requires exactly type, inner_cells, outer_cells')
    if m['type'] != 'interface_aligned_two_zone':
        raise ValueError('unsupported radial_mesh type')
    for value in (m['inner_cells'], m['outer_cells'], g['radial_cells'], g['axial_cells'], g['azimuthal_cells']):
        if type(value) is not int or value <= 0:
            raise ValueError('mesh counts must be positive integers')
    if m['inner_cells'] + m['outer_cells'] != g['radial_cells'] or g['azimuthal_cells'] != 1:
        raise ValueError('inconsistent radial counts or unsupported azimuthal cells')
    h, b = s['hydraulics'], s['coffee_bed']
    p = h.get('permeability_profile', {})
    if p.get('type') != 'radial_two_zone':
        raise ValueError('two-zone mesh requires radial_two_zone hydraulics')
    r, interface, depth, angle = g['basket_radius_m'], p['interface_radius_m'], b['bed_depth_m'], g['wedge_angle_deg']
    values = (r, interface, depth, angle, g['radial_grading'], g['axial_grading'], p['inner_permeability_m2'], p['outer_permeability_m2'])
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError('invalid finite positive geometry/permeability')
    if not 0 < interface < r or not 0 < angle <= 5 or g['radial_grading'] != 1 or g['axial_grading'] != 1:
        raise ValueError('two-zone mesh requires uniform within-zone/axial grading and supported wedge')
    boundary = h.get('pressure_boundary_model', s.get('pressureBoundaryModel', 'prescribedPressure'))
    if (s.get('aggregate_viscosity', {}).get('mode') not in ('observe', 'coupled')
        or boundary not in ('prescribedPressure', 'prescribedPressureHistory')
        or s.get('flowResistanceModel', 'darcy') != 'darcy'
        or s.get('bedMechanicsModel', 'none') != 'none'
        or 'effective_permeability_evolution' in s
        or s['wetting']['initial_wet_front_m'] != depth
        or s['wetting']['initial_saturation'] != 1 or s['time'].get('start_s', 0) != 0):
        raise ValueError('two-zone mesh requires fresh saturated static local-viscosity Darcy pressure boundary')
    return dict(m, radius=r, interface=interface, depth=depth, angle=angle)


def render(s, m):
    nz = s['geometry']['axial_cells']
    a = math.radians(m['angle']/2)
    # Retain the established axial x direction and straight-sided wedge scaling.
    points = [(0,0,0),(m['depth'],0,0)]
    for r in (m['interface'], m['radius']):
        y,z = r*math.cos(a),r*math.sin(a)
        points.extend([(m['depth'],y,-z),(0,y,-z),(m['depth'],y,z),(0,y,z)])
    vertices = '\n'.join('    ('+' '.join(format(v,'.17g') for v in p)+')' for p in points)
    patches = [('inlet','patch','(0 3 5 0) (3 7 9 5)'),
               ('outlet','patch','(1 1 4 2) (2 4 8 6)'),
               ('outerWall','wall','(7 6 8 9)'),
               ('axis','empty','(0 0 1 1)'),
               ('wedgeMinus','wedge','(0 1 2 3) (3 2 6 7)'),
               ('wedgePlus','wedge','(0 5 4 1) (5 9 8 4)')]
    boundary = '\n'.join(f'    {name}\n    {{ type {kind}; faces ({faces}); }}' for name,kind,faces in patches)
    return f'''FoamFile
{{ version 2.0; format ascii; class dictionary; object blockMeshDict; }}
// Interface from hydraulics; shared internal faces, no material boundary patch.
scale 1;
vertices
(
{vertices}
);
blocks
(
    hex (0 1 2 3 0 1 4 5) ({nz} {m['inner_cells']} 1) simpleGrading (1 1 1)
    hex (3 2 6 7 5 4 8 9) ({nz} {m['outer_cells']} 1) simpleGrading (1 1 1)
);
edges ();
boundary
(
{boundary}
);
mergePatchPairs ();
'''
