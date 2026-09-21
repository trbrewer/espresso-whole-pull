"""Synthetic fixtures only; no redistributed measured tables."""
import unittest
from tools.sci_md_rheology_001.analysis import np
from tools.sci_md_rheology_001.analysis import (solids_fraction,viscosity,resistance,errors,compare,
    axial_reduce,REF,AGGREGATE,straight_sided_wedge_scale)

class RheologyTests(unittest.TestCase):
    def test_mass_basis(self):
        self.assertAlmostEqual(float(solids_fraction(100,900)),.1)
        self.assertNotAlmostEqual(float(solids_fraction(100,900)),100/900)
    def test_inventory(self):
        for model in ('indexed_passive_species_first_order_with_capacity_ceiling','caffeine',''):
            with self.assertRaises(ValueError): solids_fraction(1,965,model)
    def test_invalid_concentration(self):
        for c in (-1,np.nan,np.inf):
            with self.assertRaises(ValueError): solids_fraction(c,965)
    def test_water_and_units(self):
        calls=[]
        def measured(t,x):
            calls.append((t,x)); return .8e-3 # synthetic mPa.s -> Pa.s
        mu,dilute=viscosity(np.array([0,.05,.1,.24]),90,.4e-3,measured)
        np.testing.assert_allclose(mu,[.4e-3,.6e-3,.8e-3,.8e-3])
        self.assertTrue(all(t==363.15 for t,x in calls)); self.assertIn((363.15,76.),calls)
        self.assertEqual(dilute.tolist(),[True,True,False,False])
    def test_source_rejection(self):
        for w,t in ((.25,90),(.36,90),(-.01,90),(.1,100),(.1,0),(np.nan,90)):
            with self.assertRaises(ValueError): viscosity([w],t,.001,lambda t,x:.002)
    def test_stress(self):
        m,_=viscosity([0,.05,.1],90,.001,lambda t,x:.002,2)
        np.testing.assert_allclose(m,[.001,.002,.003])
    def test_uniform_darcy(self):
        self.assertAlmostEqual(resistance([2,2],[1,3],[4,4],2),1)
    def test_two_layer(self):
        self.assertAlmostEqual(resistance([2,3],[1,3],[4,6],2),1)
    def test_nonuniform_thickness(self):
        self.assertAlmostEqual(resistance([1,4],[1,3],[1,1],1),13)
    def test_constant_alpha(self):
        t=np.arange(3); p=dict(t=t,q=np.ones(3)*2,q0=np.ones(3)*4)
        alpha,m=compare({REF:p,'other':p}); self.assertEqual(alpha,.5)
        self.assertEqual(m['other']['residual']['peak'],0)
    def test_time_varying(self):
        alpha,m=compare({REF:dict(t=[0,1,2],q=[1,2,1],q0=np.ones(3)*2)})
        self.assertGreater(m[REF]['residual']['integrated'],0)
    def test_reference_only(self):
        p=dict(t=[0,1],q=[1,1],q0=np.array([2,2]))
        a,m=compare({REF:p,'other':dict(t=[0,1],q=[2,2],q0=np.array([2,2]))})
        self.assertEqual(a,.5);self.assertEqual(m['other']['residual']['integrated'],1)
    def test_correlation(self):
        self.assertGreater(resistance([4,1],[1,1],[1,4],1),resistance([1,4],[1,1],[1,4],1))
    def test_sector_nonuniform(self):
        scale=straight_sided_wedge_scale(5)
        centres=np.array([[.5,0,0],[.5,1,0],[2,0,0],[2,1,0]])
        z,dz,f=axial_reduce(centres,np.array([.5,.5,1,1])/scale,{'c':[1,1,2,2]},1,scale,3)
        np.testing.assert_allclose(dz,[1,2]);np.testing.assert_equal(f['c'],[1,2])
    def test_reject_radial(self):
        with self.assertRaises(ValueError): axial_reduce(np.array([[.5,0,0],[.5,1,0]]),np.array([.5,.5]),{'c':[1,2]},1,1,1)
    def test_deterministic(self):
        p={REF:dict(t=[0,1],q=[1,2],q0=np.array([2,2]))}
        self.assertEqual(compare(p),compare(p))
    def test_positive_window(self):
        with self.assertRaises(ValueError): errors([0,1],[1,1],[0,1])

if __name__=='__main__':unittest.main()
