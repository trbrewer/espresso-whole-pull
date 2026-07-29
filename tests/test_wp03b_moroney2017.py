import math, unittest
from tools.reference.wp03b import moroney2017 as m
class TestMoroney(unittest.TestCase):
 def test_cases_conserve_and_refine(self):
  for p in (m.FINE,m.COARSE):
   a=m.solve(p,2,.002);b=m.solve(p,2,.001)
   self.assertLess(max(abs(m.inventory(x[1:],p)-m.inventory(a[0][1:],p)) for x in a),2e-11)
   self.assertLess(abs(a[-1][1]-b[-1][1]),1e-5)
 def test_bad_inputs_and_no_clipping(self):
  with self.assertRaises(ValueError):m.derivative((-1,0,1),m.FINE)
  with self.assertRaises(ValueError):m.solve(m.FINE,-1,.1)
 def test_equilibrium_inventory(self):
  for p in (m.FINE,m.COARSE):self.assertAlmostEqual(m.inventory(m.equilibrium(p),p),m.inventory((0,p.gamma1,1),p))
if __name__=="__main__":unittest.main()
