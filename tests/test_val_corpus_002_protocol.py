import copy
import csv
import importlib.util
import json
import math
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/val_corpus_002_protocol.py"
SPEC = importlib.util.spec_from_file_location("val_corpus_002_protocol", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)
CASE = ROOT / "validation/cases/val_corpus_002"


def load(name):
    return json.loads((CASE / name).read_text())


class ValCorpus002ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = {
            "evidence": load("VAL_CORPUS_002_EVIDENCE_MANIFEST.json"),
            "cohort": load("VAL_CORPUS_002_COHORT_SELECTION.json"),
            "parameters": load("VAL_CORPUS_002_PARAMETER_SOURCE_LEDGER.json"),
            "run_matrix": load("VAL_CORPUS_002_FUTURE_RUN_MATRIX.json"),
            "sensitivity": load("VAL_CORPUS_002_SENSITIVITY_MATRIX.json"),
            "waszkiewicz": load("VAL_CORPUS_002_WASZKIEWICZ_COHORT.json"),
        }

    def test_exact_source_hashes_and_generated_records(self):
        expected = {
            "puckworks/data/schmieder2023/cup_masses.csv": "39b7c16f9d9da614f151f46cb0db1440d43f150fbf49d3d2119f3f2fa1622f43",
            "puckworks/data/schmieder2023/kinetics_fit_params_avg.csv": "00ff8c8344e9690274d2a6e7ec3f3d63b092d8b233d5f5f381301af09816b1d6",
            "puckworks/data/waszkiewicz2025/tds_fractions.csv": "f22ee533f4c3e4c4c2587192a9aefa9af43bf8d47dd4456a611bfd92fb673847",
        }
        for item in self.records["evidence"]["files"]:
            if item["path"] in expected:
                self.assertEqual(item["sha256"], expected[item["path"]])
        self.assertEqual(set(expected), {item["path"] for item in self.records["evidence"]["files"] if item["path"] in expected})

    def test_deterministic_metadata_only_selector(self):
        rows = []
        for exp in range(1, 8):
            for rep in range(1, 7 if exp == 7 else 4):
                for index, brew_ratio in enumerate(MODULE.BR_ORDER):
                    rows.append({"exp": str(exp), "rep": str(rep), "doe_role": "DoE Central Point" if exp == 7 else "DoE Axis Point", "target_flow_ml_s": "2", "scale_flow_ml_s": "2.01", "grind_level": "1.7", "target_temp_C": "89", "decent_temp_C": "88.5", "pressure_max_bar": "4", "component": "TDS", "brew_ratio": brew_ratio, "mass_in_cup": str(3 + index), "mass_units": "g", "conc_in_cup": str(150 - index)})
        anchor1, transfer1 = MODULE.select_schmieder(rows)
        altered = copy.deepcopy(rows)
        for row in altered:
            row["mass_in_cup"] = "999999"
            row["conc_in_cup"] = "999999"
        anchor2, transfer2 = MODULE.select_schmieder(altered)
        strip = lambda rs: [{k: v for k, v in r.items() if not k.startswith("tds_")} for r in rs]
        self.assertEqual(strip(anchor1), strip(anchor2))
        self.assertEqual(strip(transfer1), strip(transfer2))
        self.assertEqual({r["experiment"] for r in anchor1}, {7})
        self.assertEqual({r["experiment"] for r in transfer1}, set(range(1, 7)))

    def test_partition_disjointness(self):
        cohort = self.records["cohort"]
        anchor = {(r["experiment"], r["replicate"], r["brew_ratio"]) for r in cohort["anchor_records"]}
        transfer = {(r["experiment"], r["replicate"], r["brew_ratio"]) for r in cohort["axis_transfer_records"]}
        self.assertTrue(anchor.isdisjoint(transfer))
        ledger = load("VAL_CORPUS_002_CALIBRATION_COMPARISON_LEDGER.json")
        self.assertEqual(ledger["rules"]["calibration_comparison_overlap"], "PROHIBITED_FAIL_CLOSED")

    def test_exp7_metadata_replicates_and_source_fit(self):
        cohort = self.records["cohort"]
        self.assertEqual(len(cohort["anchor_records"]), 18)
        self.assertEqual(len({r["replicate"] for r in cohort["anchor_records"]}), 6)
        self.assertEqual(cohort["exp7_source_fit"], {"c0_g_per_g": 0.24827, "c0_se_g_per_g": 0.00419, "lambda_g_beverage": 17.47261, "lambda_se_g_beverage": 0.48029})

    def test_parameter_classification_and_mapping(self):
        ledger = self.records["parameters"]
        allowed = {"SOURCE_MEASURED", "SOURCE_DERIVED", "SOURCE_FITTED", "CROSS_SOURCE_PRIOR", "SYNTHETIC_FIXTURE", "FIXED_PREDECESSOR_VALUE", "CALIBRATED_IN_THIS_CASE", "UNRESOLVED"}
        for parameterization in ledger["parameterizations"].values():
            for value in parameterization.values():
                if isinstance(value, dict) and "class" in value:
                    self.assertIn(value["class"], allowed)
        p1 = ledger["parameterizations"]["P1_SCHMIEDER_EXP7_DIRECT_SOURCE_MAPPING"]
        self.assertAlmostEqual(p1["initial_extractable_mass_for_20g_dose_g"]["value"], 4.9654)
        self.assertAlmostEqual(p1["extractionRateConstant"]["value"], 0.11446486815650324)
        self.assertTrue(ledger["p1_mapping_verified"])

    def test_sensitivity_absolute_grid_valid(self):
        sensitivity = self.records["sensitivity"]
        self.assertEqual(sensitivity["future_run_count"], 9)
        for run in sensitivity["future_runs"]:
            self.assertTrue(all(math.isfinite(value) and value > 0 for value in run["absolute_parameters"].values()))

    def test_waszkiewicz_clock_and_unsupported_pressures(self):
        wasz = self.records["waszkiewicz"]
        self.assertEqual(wasz["point_count"], 12)
        self.assertEqual(wasz["optimized_time_shift"], "PROHIBITED")
        self.assertEqual(wasz["clock_mapping"]["optimization"], "PROHIBITED")
        self.assertEqual(wasz["unsupported_chemistry"], {"5_bar": "UNAVAILABLE_NOT_INFERRED", "11_bar": "UNAVAILABLE_NOT_INFERRED"})

    def test_run_matrix_unique_complete_and_not_executed(self):
        matrix = self.records["run_matrix"]
        ids = [run["run_id"] for run in matrix["future_openfoam_runs"]]
        self.assertEqual(len(ids), 42)
        self.assertEqual(len(set(ids)), 42)
        self.assertEqual(matrix["stage_a_execution"], "NOT_AUTHORIZED")

    def test_mandatory_metrics_and_claim_ceiling(self):
        metrics = load("VAL_CORPUS_002_METRIC_AND_INTERPRETATION_SPEC.json")
        mandatory = {"cup_solute_mass_g", "cumulative_tds_fraction", "extraction_yield_fraction", "liquid_balance_residual", "solute_balance_residual", "boundedness", "completion"}
        self.assertLessEqual(mandatory, set(metrics["mandatory_outputs"]))
        claims = load("VAL_CORPUS_002_RIGHTS_AND_CLAIM_CEILING.json")
        self.assertEqual(claims["physical_validation"], "NOT_ESTABLISHED")
        self.assertEqual(claims["new_governing_physics"], "NOT_YET_JUSTIFIED")

    def test_species_semantics_and_fail_closed_unresolved_mappings(self):
        ledger = load("VAL_CORPUS_002_CALIBRATION_COMPARISON_LEDGER.json")
        species = next(item for item in ledger["partitions"] if item["id"] == "SCHMIEDER_SPECIES")
        self.assertEqual(species["role"], "SOURCE_ONLY_ONE_SOLUTE_LIMITATION_AUDIT")
        hydraulic = load("VAL_CORPUS_002_HYDRAULIC_CHEMISTRY_DECOMPOSITION.json")
        self.assertEqual(hydraulic["schmieder_source_pressure_history"], "UNAVAILABLE_NOT_INFERRED")
        gate = load("VAL_CORPUS_002_STAGE_B_AUTHORIZATION_REQUIREMENTS.json")
        self.assertEqual(gate["authorization_status"], "NONE")

    def test_candidate_treatments_are_exactly_one_and_allowed(self):
        record = load("VAL_CORPUS_002_CANDIDATE_EVIDENCE_ADJUDICATION.json")
        candidates = record["candidates"]
        self.assertEqual(len({item["candidate"] for item in candidates}), len(candidates))
        self.assertEqual(len(candidates), 11)
        self.assertTrue(all(item["treatment"] in record["allowed_treatments"] for item in candidates))


if __name__ == "__main__":
    unittest.main()
