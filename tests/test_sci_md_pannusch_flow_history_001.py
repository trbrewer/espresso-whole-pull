import json,pathlib,unittest
from analysis.sci_md_pannusch_flow_history_001.core import *

class FlowHistoryTests(unittest.TestCase):
 def test_cohorts_and_fraction_mapping(self):
  self.assertEqual(PRIMARY,("PRED-C01","PRED-C02","PRED-C05","PRED-C06"));self.assertEqual(RAMP,("PRED-C07","PRED-C08"));self.assertEqual(EXCLUDED,("PRED-C03","PRED-C04"));self.assertEqual(tuple(x-1 for x in ASSAY_IDS),(0,1,2,4,6,9))
 def test_registry_target_independent_and_ordered(self):
  variants=[None,[[0]*6],[[9,1]],[[.123]*6]];self.assertEqual(len({canonical(candidate_registry(v)) for v in variants}),1)
  self.assertEqual([x["candidate_id"] for x in candidate_registry()],["Q0_LEGACY_CONSTANT_START","QP_SOURCE_PROGRAMMED_SCHEDULE","QP_VOLUME_EQUIVALENT_CONSTANT","QM_MASSDATA_FLOW_SCALAR","QD_MASS_DERIVATIVE_OUTFLOW"])
  self.assertFalse(any(any(k in x["formula"].lower() for k in ("lag","smooth","multiplier","filter")) for x in candidate_registry()))
 def test_semantics_fail_closed(self):
  status,reasons=qualify_candidate(units=None,physical_side="UNKNOWN",clock_zero=None,support=None);self.assertEqual(status,"INELIGIBLE");self.assertTrue({"MISSING_UNITS","AMBIGUOUS_OR_INADMISSIBLE_PHYSICAL_SIDE","MISSING_CLOCK_ZERO","MISSING_SUPPORT"}<=set(reasons))
  _,reasons=qualify_candidate(units="g/s",physical_side="BEVERAGE_OUTFLOW",clock_zero=0,support=(0,30));self.assertIn("MISSING_MASS_TO_VOLUME_CONVERSION",reasons);self.assertIn("NO_PUBLISHED_PANNUSCH_Q_MAPPING",reasons)
 def test_prohibited_adjustments(self):
  _,r=qualify_candidate(units="mL/s",physical_side="MODEL_Q_EXPLICIT",clock_zero=0,support=(0,30),published_q_role=True,fitted_adjustment=True,extrapolation=True);self.assertIn("FITTED_LAG_OFFSET_OR_MULTIPLIER_PROHIBITED",r);self.assertIn("UNSUPPORTED_EXTRAPOLATION_PROHIBITED",r)
 def test_q_safety(self):
  self.assertEqual(validate_q(lambda t:2,[0,1,10]),[2,2,2])
  for bad in (0,-1,float("nan"),float("inf")):
   with self.assertRaises(ValueError):validate_q(lambda t,bad=bad:bad,[0,1])
 def test_identity_and_disposition(self):
  reg=candidate_registry();self.assertIn("IDENTICAL_TO_Q0_ON_PRIMARY",reg[1]["eligibility"]);self.assertEqual(classify_overall(reg),"SCI_MD_PANNUSCH_FLOW_HISTORY_001_FLOW_AUTHORITY_INELIGIBLE")
 def test_no_variable_flow_interval_helper(self):
  text=(pathlib.Path(__file__).parents[1]/"analysis/sci_md_pannusch_flow_history_001/run.py").read_text();self.assertNotIn("_interval_conc(",text);self.assertNotIn("duration-weight",text)
 def test_committed_artifacts(self):
  d=pathlib.Path(__file__).parents[1]/"docs/analysis/sci_md_pannusch_flow_history_001";f=json.loads((d/"QUALIFICATION_FREEZE.json").read_text());self.assertFalse(f["chemistry_targets_accessed"]);self.assertTrue(f["phase_b"].startswith("PROHIBITED"));self.assertTrue(f["predecessor_boundary_reference"]["all_ten_boundaries_for_24_shots"])

if __name__=="__main__":unittest.main()
