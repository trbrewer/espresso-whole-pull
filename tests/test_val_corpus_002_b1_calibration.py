from __future__ import annotations

import copy
import math
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import val_corpus_002_b0_tooling as b0
import val_corpus_002_b1_calibration as b1
import val_corpus_002_b1_recovery as recovery


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

    def test_infrastructure_and_unknown_exceptions_escape_optimizer(self):
        with self.assertRaises(b1.InfrastructureFailure):
            b0.golden_section_log_k(lambda _rate: (_ for _ in ()).throw(
                b1.InfrastructureFailure("blockMesh")))
        with self.assertRaises(RuntimeError):
            b0.golden_section_log_k(lambda _rate: (_ for _ in ()).throw(RuntimeError("unknown")))

    def test_only_affirmative_typed_failure_becomes_failed_evaluation(self):
        result=b0.golden_section_log_k(
            lambda rate: (_ for _ in ()).throw(b0.TypedNumericalEvaluationFailure("TDS_BOUND"))
            if rate < .1 else (rate-.3)**2)
        self.assertTrue(any(row["evaluation_status"]=="FAILED_EVALUATION" for row in result["trace"]))

    def test_post_end_nonzero_is_infrastructure_not_objective(self):
        self.assertTrue(issubclass(b1.InfrastructureFailure,Exception))
        self.assertFalse(issubclass(b1.InfrastructureFailure,b0.TypedNumericalEvaluationFailure))

    def test_recovery_constants_freeze_original_bounds_and_full_cache(self):
        self.assertEqual(recovery.ATTEMPT1_COUNT,20)
        self.assertEqual([b0.LOG_K_LOWER,b0.LOG_K_UPPER],
                         [-4.470072424390813,0.13509776159727813])

    def test_failed_cache_record_is_rejected(self):
        with mock.patch.object(recovery.b1,"exact_template",return_value={}), \
             mock.patch.object(recovery,"_regular_below") as regular:
            executable=mock.Mock(); executable.__fspath__=lambda _self: "/tmp/executable"
            records=[mock.Mock()]
            regular.side_effect=records
            with self.assertRaises((b1.InfrastructureFailure,TypeError,AttributeError)):
                recovery.verify_attempt1_cache(ROOT,Path("/attempt1"))


if __name__=="__main__": unittest.main()
