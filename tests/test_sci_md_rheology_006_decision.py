"""Review correction: numerical qualification precedes case OR materiality."""
import unittest
from tools.sci_md_rheology_006.analyze import case_decision

class CaseDecisionTests(unittest.TestCase):
    def test_case_precedence(self):
        for a,b,qualified,expected in [('MATERIAL','UNRESOLVED',True,'MATERIAL'),('MATERIAL','BELOW_BUDGET',False,'UNRESOLVED'),('BELOW_BUDGET','BELOW_BUDGET',True,'BELOW_BUDGET'),('BELOW_BUDGET','UNRESOLVED',True,'UNRESOLVED')]:
            self.assertEqual(case_decision({'mean':dict(outcome=a,numerically_qualified=True),'peak':dict(outcome=b,numerically_qualified=qualified)}),expected)
