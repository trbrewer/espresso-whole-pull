import unittest
from tools.reference.wp03b.observables import *
class TestObservables(unittest.TestCase):
 def tds(self,method="REFRACTOMETRIC",basis="MASS"):
  return TDSMeasurement(method,"A","B",basis,.001,"synthetic")
 def test_kernel(self):
  r=drying_kernel(RetainedLiquidDryingObservation(.018,.3,.25,.06,.016,.0002,.02,.0001))
  self.assertEqual(r["role"],"MEASUREMENT_KERNEL_NOT_EXTRACTION_PHYSICS");self.assertGreater(r["retained_liquid_mass"],0)
 def test_method_merge_rejected(self):
  with self.assertRaises(ValueError):assert_compatible(self.tds(),self.tds("GRAVIMETRIC_DRY_DOWN"))
 def test_metadata_and_density(self):
  with self.assertRaises(ValueError):self.tds("UNKNOWN")
  with self.assertRaises(ValueError):EYConvention("X","REFRACTOMETRIC","VOLUME",None,"dry",False,False,"none","rss")
 def test_negative_mass(self):
  with self.assertRaises(ValueError):RetainedLiquidDryingObservation(-1,1,1,1,1,0,0,0)
if __name__=="__main__":unittest.main()
