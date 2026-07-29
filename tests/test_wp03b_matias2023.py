import unittest
from tools.reference.wp03b import matias2023 as m
class TestMatias(unittest.TestCase):
 def test_limits(self):
  le=[abs(m.full_outlet(1,p,1,1)-m.low_pe(1,1,1)) for p in (.1,.03,.01,.003)]
  he=[abs(m.full_outlet(1,p,1,1)-m.high_pe(1,p,1,1))/m.high_pe(1,p,1,1) for p in (10,30,100,300)]
  self.assertTrue(all(a>b for a,b in zip(le,le[1:])))
  self.assertTrue(all(a>b for a,b in zip(he,he[1:])))
 def test_gating_and_domains(self):
  self.assertLess(m.front_gating_error(.1),m.front_gating_error(1))
  for args in ((1,-1,1,1),(1,1,-1,1)):
   with self.assertRaises(ValueError):m.full_outlet(*args)
if __name__=="__main__":unittest.main()
