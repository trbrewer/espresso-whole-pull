import unittest
from tools.reference.wp03b import liang2021 as l
class TestLiang(unittest.TestCase):
 def test_transform_roundtrip(self):
  for K,t in ((0,2),(.7,12),(1,3)):
   self.assertEqual(l.K_tau_from_rates(*l.rates_from_K_tau(K,t)),(K,t))
 def test_synthetic_recovery(self):
  ts=[0,.5,1,2,4,8,16,32,64]; y=l.synthetic(.7,12,ts,1,0,3);e=l.estimate(ts,y)
  self.assertLess(abs(e["K"]-.7),.003);self.assertLess(abs(e["tau_s"]/12-1),.003)
 def test_invalid_and_degenerate(self):
  for x in ((-1,1),(1.1,1),(.5,0)):
   with self.assertRaises(ValueError):l.rates_from_K_tau(*x)
  with self.assertRaises(ValueError):l.estimate([0,1,2],[1,1,1])
 def test_fit_prohibited(self):self.assertEqual(l.FIT_STATUS,"PROHIBITED_UNTIL_GOVERNED_DIGITIZATION_EXISTS")
if __name__=="__main__":unittest.main()
