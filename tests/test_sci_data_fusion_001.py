import json
import tempfile
import unittest
from pathlib import Path

from analysis.sci_data_fusion_001.compatibility import adjudicate, common_constraint, interval_metrics
from analysis.sci_data_fusion_001.constraints import narrowing
from analysis.sci_data_fusion_001.lineage import independently_eligible
from analysis.sci_data_fusion_001.uncertainty import combine, compatible


class CompatibilityTests(unittest.TestCase):
    def support(self, name, lineage, interval=(0.2, 0.4)):
        return {"support_id": name, "lineage_id": lineage, "interval": interval, "eligible": True,
                "correlation_group_id": lineage, "target_exposed": False, "source_internal_validation": False}

    def test_unknown_required_semantics_fail_closed(self):
        a, b = self.support("a", "la"), self.support("b", "lb")
        a["pair_gates"] = {"b": {}}
        result = adjudicate(a, b)
        self.assertEqual(result["terminal_compatibility"], "BLOCKED_SEMANTIC")
        self.assertIn("physical_quantity", result["unknown_gates"])

    def test_explicit_mismatch_rejects(self):
        a, b = self.support("a", "la"), self.support("b", "lb")
        a["pair_gates"] = {"b": {name: True for name in ("physical_quantity", "reference_state", "unit_basis", "spatial_support", "temporal_support", "observation_operator", "population_regime", "lineage", "independence_target_exposure", "provenance_rights", "ewp_consumer", "no_new_inference")}}
        a["pair_gates"]["b"]["observation_operator"] = False
        self.assertEqual(adjudicate(a, b)["terminal_compatibility"], "INCOMPATIBLE")

    def test_distinct_lineages_required(self):
        a, b = self.support("a", "same"), self.support("b", "same")
        self.assertFalse(independently_eligible(a, b))
        self.assertEqual(common_constraint([a, b], [])["result"], "NEGATIVE_NO_COMMON_SUPPORT")

    def test_disjoint_compatible_is_conflict(self):
        a, b = self.support("a", "la", (0.1, 0.2)), self.support("b", "lb", (0.3, 0.4))
        result = common_constraint([a, b], [{"terminal_compatibility": "COMPATIBLE"}])
        self.assertEqual(result["result"], "CONFLICT_SAME_SCOPE_SUPPORTS")

    def test_source_ids_survive_intersection(self):
        a, b = self.support("a", "la"), self.support("b", "lb", (0.3, 0.5))
        result = common_constraint([a, b], [{"terminal_compatibility": "COMPATIBLE"}])
        self.assertEqual(result["source_ids"], ["a", "b"])
        self.assertEqual(result["common_support"], [0.3, 0.4])

    def test_no_baseline_no_narrowing(self):
        self.assertFalse(narrowing([0.3, 0.4], None)["quantitative_narrowing_claim"])

    def test_interval_metrics_do_not_make_distribution(self):
        result = interval_metrics((0.1, 0.4), (0.3, 0.5))
        self.assertNotIn("distribution", result)
        self.assertEqual(result["intersection"], [0.3, 0.4])

    def test_uncertainty_requires_exact_semantics_and_cannot_pool(self):
        left = {x: "same" for x in ("statistic", "estimand", "scale", "replicate_unit", "state", "observation_operator")}
        self.assertTrue(compatible(left, dict(left)))
        right = dict(left, statistic="SE")
        self.assertFalse(compatible(left, right))
        with self.assertRaises(RuntimeError):
            combine(left, right)


class ContractSentinelTests(unittest.TestCase):
    def test_accepted_result_sentinels_are_frozen(self):
        path = Path(__file__).parents[1] / "analysis/sci_data_fusion_001/task_contract_template.json"
        doc = json.loads(path.read_text())
        sentinels = set(doc["known_sentinels"])
        required = {"WADSWORTH_VACA_NO_ROW_FUSION", "PERMEABILITY_STRESS_ONLY", "VACA_FIG12_OPERATOR_ONLY_ZERO_PRIOR_ROWS", "VISUALIZER_ZERO_EWP_PRESSURE_BOUNDARIES", "PANNUSCH_ZERO_OPERATIONAL_EWP_MAPPINGS", "WASZKIEWICZ_FIXED_RESISTANCE_RETAINED"}
        self.assertTrue(required <= sentinels)
        self.assertEqual(doc["uncertainty_combination"]["numeric_rule"], "NONE_FROZEN")


if __name__ == "__main__":
    unittest.main()

