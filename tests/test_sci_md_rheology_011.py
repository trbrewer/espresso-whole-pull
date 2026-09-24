"""Geometry, label semantics, conservation and strict decision boundaries."""
import copy
import tempfile
import unittest
from pathlib import Path
import numpy as np
from tests.test_sci_md_rheology_008 import raw
from scripts.aggregate_viscosity import contract
from scripts.prepare_case import render_block_mesh
from tools.sci_md_rheology_002.export import HEADER
from tools.sci_md_rheology_009.common import history, radial
from tools.sci_md_rheology_011.common import relocate, interface, decision, branch, support, references
from tools.sci_md_rheology_011.observer import native, high_share, independent_paths
from tools.sci_md_rheology_008.observer import native as old_native
from tools.sci_md_rheology_004.observer import compare
from tools.sci_md_rheology_007.observer import history as mass_history

class RelocationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.table=Path(self.tmp.name)/'constant.table';self.table.write_text(HEADER+'0 .001\n.1 .001\n.24 .001\n')
    def spec(self):
        s=history(radial(),'UP');s['aggregate_viscosity']=dict(mode='coupled',table=str(self.table));return relocate(s)
    def test_distribution_and_blocks(self):
        s=self.spec();self.assertIn('coupled',contract(s))
        self.assertAlmostEqual((float(interface()['binary64_repr'])/.029)**2,.75)
        mesh=render_block_mesh(s)
        self.assertEqual(mesh.count('hex ('),2)
        self.assertIn('(512 48 1)',mesh);self.assertIn('(512 16 1)',mesh)
        self.assertNotIn('type baffle',mesh)
    def test_schema_rejections(self):
        muts=[lambda s:s['geometry']['radial_mesh'].update(extra=1),lambda s:s['geometry']['radial_mesh'].update(inner_cells=True),lambda s:s['geometry']['radial_mesh'].update(inner_cells=48.),lambda s:s['geometry']['radial_mesh'].update(outer_cells=0),lambda s:s['geometry'].update(radial_cells=63),lambda s:s['geometry'].update(radial_grading=2),lambda s:s['geometry'].update(axial_grading=2),lambda s:s['geometry'].update(basket_radius_m=float('inf')),lambda s:s['hydraulics']['permeability_profile'].update(interface_radius_m=float('nan')),lambda s:s['hydraulics']['permeability_profile'].update(interface_radius_m=.03),lambda s:s['hydraulics']['permeability_profile'].update(type='uniform'),lambda s:s['aggregate_viscosity'].update(mode='bulkCoupled'),lambda s:s['aggregate_viscosity'].update(mode='off'),lambda s:s['wetting'].update(initial_saturation=.5),lambda s:s.update(effective_permeability_evolution={})]
        for mutate in muts:
            s=self.spec();mutate(s)
            for f in (contract,render_block_mesh):
                with self.assertRaises((ValueError,SystemExit),msg=str(mutate)):f(s)
    def test_A_identical_interpretation(self):
        s=history(radial(),'UP');a=old_native(raw());b=native(raw(),s)
        for key in a:
            if isinstance(a[key],np.ndarray):np.testing.assert_array_equal(a[key],b[key])
            elif key=='dose_kg':self.assertAlmostEqual(a[key],b[key])
            else:self.assertEqual(a[key],b[key])
    def braw(self):
        d=raw()
        for zone,f in [('inner',.75),('outer',.25)]:
            d[zone+'_area_m2'][:]=np.pi*.029**2*f;d[zone+'_volume_m3']=d[zone+'_area_m2']*.009011660896432553
            d[zone+'_remaining_kg']=f*d['remaining_kg']
        return d
    def test_geometry_and_inventory_cannot_validate_themselves(self):
        s=self.spec();d=self.braw();native(d,s)
        for key,value in [('outer_remaining_kg',.002),('inner_remaining_kg',.005),('inner_area_m2',1.),('inner_volume_m3',1.)]:
            b=copy.deepcopy(d);b[key][0]=value
            with self.assertRaises(ValueError):native(b,s)
        with self.assertRaises(ValueError):native(raw(),s)
        with self.assertRaises(ValueError):old_native(d)
    def test_class_mapping_and_no_second_weights(self):
        s=self.spec();raw_b=self.braw();b=native(raw_b,s)
        np.testing.assert_array_equal(b['water_kg'],raw_b['water_kg'])
        np.testing.assert_array_equal(high_share(b,s),1-b['share'])
        s['hydraulics']['permeability_profile']['inner_permeability_m2']=3e-15
        with self.assertRaises(ValueError):high_share(b,s)
    def test_permutation_null(self):
        h=np.array([0,2,9.]);l=np.array([0,1,3.])
        np.testing.assert_array_equal(independent_paths(h,l),.75*l+.25*h)
        a=native(raw(),radial());b=copy.deepcopy(a)
        # Regional labels may swap; total conservative response is unchanged.
        b['share']=1-a['share']
        score=compare(mass_history(a),mass_history(b),'B',.001)
        self.assertEqual(score['E_path'],0);self.assertEqual(score['max_fraction_TDS_pp'],0)
    def test_fraction_conservation_and_invalid_denominators(self):
        a=native(raw(),radial());h=mass_history(a)
        m=compare(h,h,'B',.001)
        self.assertAlmostEqual(sum(np.diff(m['C']['solute_g']))/1000,m['C']['solute_g'][-1]/1000)
        for end in (0,-1,float('nan'),100):
            with self.assertRaises(ValueError):compare(h,h,'B',end)
        bad=copy.deepcopy(h);bad['S'][:]=0
        with self.assertRaises(ValueError):compare(h,bad,'B',.001)
    def test_decisions_no_radial_cancellation(self):
        def score(base,ar=.0,br=.0):
            v={r:dict(E_Spath=x) for r,x in [('base',base),('temporal',base),('axial',base),('A_radial',base+ar),('B_radial',base+br)]}
            a={r:dict(E_Spath=0.) for r in v}
            return decision(v,a,'TR_LINEAR','E_Spath',True)
        self.assertEqual(score(.01)['decision'],'UNRESOLVED')
        self.assertEqual(score(.012)['decision'],'MATERIAL')
        self.assertEqual(score(.001)['decision'],'BELOW_BUDGET')
        q=score(.011,.0015,-.0015);self.assertAlmostEqual(q['u_total'],.003);self.assertEqual(q['decision'],'UNRESOLVED')
        self.assertEqual(branch(['BELOW_BUDGET']*8),'NO_MATERIAL_ARRANGEMENT_CONTRAST_FOR_TESTED_DELIVERY')
        self.assertIn('REQUIRED',branch(['MATERIAL']+['UNRESOLVED']*7))
        self.assertEqual(branch(['UNRESOLVED']*8),'ARRANGEMENT_CONTRAST_UNRESOLVED')
    def test_support_complete(self):
        t={a+'_'+k:'0.01234567891' for a in ('old','new') for k in references()}
        self.assertEqual(support(t)['UP'],'0.011728394')
        t.pop(next(iter(t)))
        with self.assertRaises(ValueError):support(t)

if __name__=='__main__':unittest.main()

class TopologyTests(unittest.TestCase):
    setUp=RelocationTests.setUp
    spec=RelocationTests.spec
    def mesh_fixture(self):
        from scripts.radial_mesh import contract as mesh_contract,render
        import re
        s=self.spec();s['geometry'].update(radial_cells=2,axial_cells=1,radial_mesh=dict(type='interface_aligned_two_zone',inner_cells=1,outer_cells=1))
        txt=render(s,mesh_contract(s));part=txt.split('vertices\n(\n')[1].split('\n);')[0]
        pts=np.array([list(map(float,t.split())) for t in re.findall(r'\(([^()]+)\)',part)])
        faces=[[3,2,4,5],[0,3,5],[3,7,9,5],[1,4,2],[2,4,8,6],[7,6,8,9],[0,1,2,3],[3,2,6,7],[0,5,4,1],[5,9,8,4]]
        owners=[0,0,1,0,1,1,0,1,0,1]
        centers=[pts[[0,1,2,3,4,5]].mean(axis=0),pts[[2,3,4,5,6,7,8,9]].mean(axis=0)]
        for i,face in enumerate(faces):
            vs=pts[face];normal=np.cross(vs[1]-vs[0],vs[2]-vs[0])
            if np.dot(normal,vs.mean(axis=0)-centers[owners[i]])<0:faces[i]=face[::-1]
        case=Path(self.tmp.name)/'case';pm=case/'constant/polyMesh';pm.mkdir(parents=True)
        (pm/'points').write_text('\n10\n(\n'+'\n'.join('('+' '.join(map(str,p))+')' for p in pts)+'\n)\n')
        (pm/'faces').write_text('\n10\n(\n'+'\n'.join(str(len(f))+'('+' '.join(map(str,f))+')' for f in faces)+'\n)\n')
        for name,v in [('owner',owners),('neighbour',[1])]:
            (pm/name).write_text('\n'+str(len(v))+'\n(\n'+'\n'.join(map(str,v))+'\n)\n')
        boundary=[('inlet','patch',2,1),('outlet','patch',2,3),('outerWall','wall',1,5),('axis','empty',0,6),('wedgeMinus','wedge',2,6),('wedgePlus','wedge',2,8)]
        (pm/'boundary').write_text('\n'.join(f'{n} {{ type {t}; nFaces {c}; startFace {a}; }}' for n,t,c,a in boundary))
        return case,s
    def test_connected_interface_and_negative_boundaries(self):
        from tools.sci_md_rheology_011.geometry import mesh
        case,s=self.mesh_fixture();summary,*_=mesh(case,s)
        self.assertTrue(summary['connected']);self.assertEqual(summary['interface_faces'],1)
        p=case/'constant/polyMesh/boundary';old=p.read_text();p.write_text(old.replace('outerWall { type wall','outerWall { type patch'))
        with self.assertRaises(ValueError):mesh(case,s)
        p.write_text(old)
        p=case/'constant/polyMesh/neighbour';p.write_text('\n1\n(\n0\n)\n')
        with self.assertRaises(ValueError):mesh(case,s)
