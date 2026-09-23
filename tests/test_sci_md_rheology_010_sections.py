"""Non-scoring virtual-section observer: conservation without assay rescaling."""
import math
import unittest
from tools.sci_md_rheology_010.sections import section_weights, inventories, NAMES

class VirtualSectionTests(unittest.TestCase):
    def test_native_dimensionless_and_mass_density_notation(self):
        from tools.sci_md_rheology_010.sections import field_dimensions
        self.assertEqual(field_dimensions('dimensions [];'),[0]*7)
        self.assertEqual(field_dimensions('dimensions [0 0 0 0 0 0 0];'),[0]*7)
        self.assertEqual(field_dimensions('dimensions [1 -3 0 0 0 0 0];'),[1,-3,0,0,0,0,0])
        with self.assertRaises(ValueError):field_dimensions('no dimension record')
        with self.assertRaises(ValueError):field_dimensions('dimensions [1 2];')
    def test_partition_and_uniform_field_invariance(self):
        lo=[0,.0145];hi=[.0145,.029];v=[math.pi*(b*b-a*a)*.009 for a,b in zip(lo,hi)]
        w=section_weights(lo,hi);r=inventories(v,w,[100,100],[20,20],[.4,.4],[1,1])
        for k,residual in r['closure_residuals_kg'].items():self.assertLess(abs(residual),1e-15,k)
        rates=[x['solid_depletion_percent_initial_dry'] for x in r['sections'].values()]
        self.assertAlmostEqual(min(rates),max(rates),places=12)
        for row,a,b in zip(r['sections'].values(),[0,.018,.025],[.018,.025,.029]):
            self.assertAlmostEqual(row['remaining_solid_solubles_kg'],100*math.pi*(b*b-a*a)*.009,places=15)
            self.assertAlmostEqual(row['retained_dissolved_solute_kg'],8*math.pi*(b*b-a*a)*.009,places=15)
    def test_known_aligned_regional_inventories(self):
        lo=[0,.018,.025];hi=[.018,.025,.029];v=[math.pi*(b*b-a*a)*.009 for a,b in zip(lo,hi)]
        solid=[.0004,.0003,.0002];liquid=[.00001,.00002,.00003]
        r=inventories(v,section_weights(lo,hi),[x/y for x,y in zip(solid,v)],[x/(.4*y) for x,y in zip(liquid,v)],[.4]*3,[1]*3)
        for name,x,y in zip(NAMES,solid,liquid):
            self.assertAlmostEqual(r['sections'][name]['remaining_solid_solubles_kg'],x,places=15)
            self.assertAlmostEqual(r['sections'][name]['retained_dissolved_solute_kg'],y,places=15)
        self.assertAlmostEqual(r['whole_domain']['solid_depletion_kg'],.0056-sum(solid),places=15)
    def test_partial_cells_conserve_and_do_not_invent_e2_structure(self):
        v=[1.,3.];r=inventories(v,section_weights([0,.0145],[.0145,.029]),[.0001,.0002],[.0003,.0004],[.4,.4],[1,1])
        middle=r['sections'][NAMES[1]];outer=r['sections'][NAMES[2]]
        self.assertAlmostEqual(middle['solid_depletion_percent_initial_dry'],outer['solid_depletion_percent_initial_dry'],places=12)
        self.assertAlmostEqual(middle['retained_dissolved_percent_initial_dry'],outer['retained_dissolved_percent_initial_dry'],places=12)
    def test_actual_mesh_volumes_if_retained(self):
        import os
        from pathlib import Path
        from tools.sci_md_rheology_010.sections import geometry
        from tools.sci_md_rheology_008.geometry import mesh
        if not os.environ.get('RHEOLOGY010_ARTIFACTS'):self.skipTest('external native artifacts not configured')
        case=Path(os.environ['RHEOLOGY010_ARTIFACTS'])/'runs/C_up/case'
        volume,lo,hi=geometry(case);_,reference,*_=mesh(case,32,64)
        self.assertLess(max(abs(volume/reference-1)),1e-12)
        self.assertAlmostEqual(sum(volume),math.pi*.029**2*.009011660896432553,places=15)
        self.assertLess(max(abs(section_weights(lo,hi).sum(axis=0)-1)),1e-12)
    def test_bad_geometry_and_units_independent_field_bounds(self):
        with self.assertRaises(ValueError):section_weights([0],[.03])
        with self.assertRaises(ValueError):section_weights([.01],[.01])
        with self.assertRaises(ValueError):inventories([1],[[1],[0],[0]],[-1],[0],[.4],[1])

if __name__=='__main__':unittest.main()
