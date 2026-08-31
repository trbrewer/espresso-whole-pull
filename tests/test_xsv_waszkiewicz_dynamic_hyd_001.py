import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'analysis/xsv_waszkiewicz_dynamic_hyd_001/core.py'
spec=importlib.util.spec_from_file_location('xsv_core',P); c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)

class TestWaszkiewiczDynamicHydraulics(unittest.TestCase):
    def test_frozen_coefficients(self):
        self.assertEqual(c.A,0.017184292098914252); self.assertEqual(c.B,0.03670858658698296); self.assertEqual(c.C,0.2831597837775055)
    def test_physical_root_and_invalid(self):
        q=c.physical_flow(c.np.array([9.0]),c.np.array([5.0]))[0]
        self.assertGreaterEqual(q,0); self.assertAlmostEqual(c.A*q*q+(c.B+5)*q+c.C,9,places=10)
        self.assertTrue(c.np.isnan(c.physical_flow(c.np.array([.1]),c.np.array([5.]))[0]))
    def test_near_linear_fallback(self):
        q=c.physical_flow(c.np.array([2.]),c.np.array([3.]),a=0)[0]
        self.assertAlmostEqual(q,(2-c.C)/(3+c.B))
    def test_mass_increment_has_no_offset(self):
        x=c.integrate_increment(c.np.ones(4),dt=.1); c.np.testing.assert_allclose(x,[0,.1,.2,.3])
    def test_alias_constant(self): self.assertEqual(c.ALIAS,'12-8-6_alt')
    def test_positive_resistance_models(self):
        t=c.np.arange(10)*c.DT; p=c.np.full(10,9.0)
        for m,b in [('W-H0A',[1,0]),('W-H1',[1,0,.2,20]),('W-H2',[1,0,.2,20]),('W-H3',[1,0,.2,35,5]),('W-H5',[1,0])]:
            q,mass=c.predict(m,c.np.array(b,float),p,t); self.assertTrue(c.np.all(q>=0)); self.assertTrue(c.np.all(c.np.diff(mass)>=0))

if __name__=='__main__': unittest.main()
