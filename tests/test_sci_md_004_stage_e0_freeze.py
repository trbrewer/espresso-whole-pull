from pathlib import Path
import unittest


class StageE0FreezeTest(unittest.TestCase):
    def test_stage_e0_generator_cannot_accept_protected_targets(self) -> None:
        source = Path("tools/sci_md_004_stage_e0_freeze.py").read_text(encoding="utf-8")
        self.assertIn("angeloni_targets_long.csv", source)
        self.assertIn("protected scorer", source)
        self.assertNotIn("parser.add_argument(\"--target", source)

    def test_frozen_manifest_declares_zero_prediction_and_score(self) -> None:
        import json

        root = Path("validation/sci_md_004_stage_e0")
        manifest = json.loads((root / "FREEZE_MANIFEST.json").read_text(encoding="utf-8"))
        cases = json.loads((root / "CONDITIONAL_CASE_FREEZE.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["semantic_protected_target_access"])
        self.assertEqual(manifest["angeloni_species_prediction_count"], 0)
        self.assertEqual(manifest["protected_scorer_invocations"], 0)
        self.assertEqual(cases["case_count"], 66)
        self.assertEqual(cases["configuration_count"], 264)
        self.assertTrue(
            all(
                config["execution_status"] == "FROZEN_NOT_EXECUTED"
                for case in cases["cases"]
                for config in case["configurations"]
            )
        )

    def test_exactly_four_fitted_parameters_and_gates_pass(self) -> None:
        import json

        root = Path("validation/sci_md_004_stage_e0")
        result = json.loads((root / "PARAMETERIZATION_AND_IDENTIFIABILITY.json").read_text(encoding="utf-8"))
        self.assertEqual(result["parameter_count_fitted"], 4)
        self.assertEqual(result["disposition"], "PASS")
        self.assertEqual(set(result["parameters"]), {"caffeine", "trigonelline"})
        for value in result["parameters"].values():
            self.assertTrue(value["predictive_content"]["pass"])
            self.assertTrue(value["identifiability"]["pass"])
            self.assertEqual(value["diffusivity_status"], "PROXY_FIXED_NOT_FITTED")

    def test_blocked_cv_is_parseable_and_complete(self) -> None:
        import csv

        path = Path("validation/sci_md_004_stage_e0/BLOCKED_WHOLE_EXPERIMENT_CV.csv")
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 180)
        for species in ("caffeine", "trigonelline"):
            selected = [row for row in rows if row["species_id"] == species]
            self.assertEqual(len(selected), 90)
            self.assertEqual(
                {int(row["held_out_experiment_id"]) for row in selected},
                set(range(1, 16)),
            )
