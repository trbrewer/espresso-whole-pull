from __future__ import annotations

import copy
import math
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import val_corpus_002_b0_tooling as b0
import val_corpus_002_b1_calibration as b1


class StageB1DryRunTests(unittest.TestCase):
    def test_exact_template_and_scenario_mapping(self):
        template=b1.exact_template(ROOT)
        materialized=b0._materialize_p2_rate(template,.1,b0.EXP7_H1_TEMPLATE_SHA256)
        scenario=b1.solver_scenario(ROOT,materialized)
        self.assertEqual(scenario["scenario_id"],b0.CALIBRATION_CASE_ID)
        self.assertEqual(scenario["extraction"]["rate_constant_1_s"],.1)
        self.assertEqual(scenario["coffee_bed"]["initial_extractable_fraction_dry_basis"],.216896244235)
        self.assertEqual(scenario["hydraulics"]["saturated_permeability_m2"],5.99276290640711e-15)
        self.assertEqual(scenario["time"]["end_s"],90.)
        self.assertEqual(scenario["parallel"]["default_subdomains"],16)

    def test_only_typed_rate_changes(self):
        template=b1.exact_template(ROOT)
        first=b0._materialize_p2_rate(template,.1,b0.EXP7_H1_TEMPLATE_SHA256)
        second=b0._materialize_p2_rate(template,.2,b0.EXP7_H1_TEMPLATE_SHA256)
        a=copy.deepcopy(first); b=copy.deepcopy(second)
        a["chemistry"]["extractionRateConstant_s_inverse"]="RATE"
        b["chemistry"]["extractionRateConstant_s_inverse"]="RATE"
        self.assertEqual(a,b)

    def test_exact_objective_and_bounds(self):
        self.assertEqual(b0.TARGET_MASSES_G,[20.,40.,60.])
        self.assertEqual(b0.SOURCE_SOLUTE_MASSES_G,
            [2.9240100000000004,3.8761999999999994,4.187098333333333])
        self.assertEqual(math.log(b0.K_LOWER),b0.LOG_K_LOWER)
        self.assertEqual(math.log(b0.K_UPPER),b0.LOG_K_UPPER)


if __name__=="__main__": unittest.main()
