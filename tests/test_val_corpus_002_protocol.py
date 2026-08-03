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
                    target = MODULE.TARGET_MASS_G[brew_ratio]
                    mass = 3.0 + index
                    rows.append({"exp": str(exp), "rep": str(rep), "doe_role": "DoE Central Point" if exp == 7 else "DoE Axis Point", "target_flow_ml_s": "2", "scale_flow_ml_s": "2.01", "grind_level": "1.7", "target_temp_C": "89", "decent_temp_C": "88.5", "pressure_max_bar": "4", "component": "TDS", "brew_ratio": brew_ratio, "mass_in_cup": str(mass), "mass_units": "g", "conc_in_cup": str(mass / target)})
        anchor1, transfer1 = MODULE.select_schmieder(rows)
        altered = copy.deepcopy(rows)
        for row in altered:
            mass = float(row["mass_in_cup"]) / 2.0
            row["mass_in_cup"] = str(mass)
            row["conc_in_cup"] = str(mass / MODULE.TARGET_MASS_G[row["brew_ratio"]])
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
        first = next(row for row in cohort["anchor_records"] if row["replicate"] == 1 and row["brew_ratio"] == "1/1")
        self.assertEqual(first["tds_mass_g"], 2.95542)
        self.assertEqual(first["tds_fraction"], 0.147771)
        self.assertEqual(first["tds_fraction"], first["tds_mass_g"] / 20.0)
        self.assertNotEqual(first["tds_fraction"], 0.000147771)

    def test_tds_units_and_mass_fraction_identity_fail_closed(self):
        base = {"exp": "7", "rep": "1", "doe_role": "DoE Central Point", "target_flow_ml_s": "2", "scale_flow_ml_s": "2", "grind_level": "1.7", "target_temp_C": "89", "decent_temp_C": "88", "pressure_max_bar": "3", "component": "TDS", "brew_ratio": "1/1", "mass_in_cup": "2.95542", "mass_units": "g", "conc_in_cup": "0.147771"}
        anchor, _ = MODULE.select_schmieder([base])
        self.assertEqual(anchor[0]["tds_fraction"], 0.147771)
        for key, value in (("mass_units", "mg"), ("conc_in_cup", "0.000147771"), ("conc_in_cup", "nan")):
            invalid = dict(base)
            invalid[key] = value
            with self.assertRaises(ValueError):
                MODULE.select_schmieder([invalid])

    def test_exact_axis_metadata_and_replicate_counts(self):
        runs = self.records["run_matrix"]["final_production_run_inventory"]
        conditions = {run["experiment"]: run["source_aggregation"] for run in runs if run["parameterization"] == "P0" and run["hydraulic_role"].startswith("H0")}
        expected = {
            1: ("LOW_FLOW_AXIS", 1.0, 1.7, 89.0, 3),
            2: ("HIGH_FLOW_AXIS", 3.0, 1.7, 89.0, 3),
            3: ("FINE_GRIND_SETTING_AXIS", 2.0, 1.4, 89.0, 3),
            4: ("COARSE_GRIND_SETTING_AXIS", 2.0, 2.0, 89.0, 3),
            5: ("LOW_TEMPERATURE_AXIS", 2.0, 1.7, 80.0, 3),
            6: ("HIGH_TEMPERATURE_AXIS", 2.0, 1.7, 98.0, 3),
        }
        for exp, values in expected.items():
            condition = conditions[exp]
            self.assertEqual((condition["axis_role"], condition["target_flow_ml_s"], condition["grinder_setting"], condition["target_temperature_C"], condition["replicate_count"]), values)

    def test_parameter_classification_and_mapping(self):
        ledger = self.records["parameters"]
        allowed = {"SOURCE_MEASURED", "SOURCE_DERIVED", "SOURCE_FITTED", "SOURCE_DERIVED_REDUCED_LAW_MAPPING", "CROSS_SOURCE_PRIOR", "SYNTHETIC_FIXTURE", "FIXED_PREDECESSOR_VALUE", "CALIBRATED_IN_THIS_CASE", "UNRESOLVED"}
        for parameterization in ledger["parameterizations"].values():
            for value in parameterization.values():
                if isinstance(value, dict) and "class" in value:
                    self.assertIn(value["class"], allowed)
        p1 = ledger["parameterizations"]["P1_SCHMIEDER_EXP7_REDUCED_EXPONENTIAL_MAPPING"]
        self.assertAlmostEqual(p1["reduced_initial_extractable_mass_g"]["value"], 4.3379248847)
        self.assertAlmostEqual(p1["extractableFraction"]["value"], 0.216896244235)
        self.assertAlmostEqual(p1["extractionRateConstant"]["value"], 0.11446486815650324)
        self.assertEqual(p1["source_c0"]["semantic_role"], "FITTED_OUTLET_TDS_CONCENTRATION_NOT_SOLVER_EXTRACTABLE_FRACTION")
        self.assertNotEqual(p1["extractableFraction"]["value"], 0.24827)
        self.assertNotAlmostEqual(p1["reduced_initial_extractable_mass_g"]["value"], 4.9654)
        self.assertTrue(ledger["p1_mapping_verified"])

    def test_sensitivity_absolute_grid_valid(self):
        sensitivity = self.records["sensitivity"]
        self.assertEqual(sensitivity["future_run_count"], 9)
        fraction_values = {run["factor"]: run["absolute_parameters"]["extractableFraction"] for run in sensitivity["future_runs"] if run["parameter"] == "extractableFraction"}
        self.assertEqual(fraction_values, {0.8: 0.173516995388, 1.2: 0.260275493082})
        self.assertEqual(sensitivity["future_runs"][0]["absolute_parameters"]["extractableFraction"], 0.216896244235)
        for run in sensitivity["future_runs"]:
            self.assertTrue(all(math.isfinite(value) and value > 0 for value in run["absolute_parameters"].values()))
        self.assertEqual(sensitivity["analysis_name"], "FINITE_RANGE_ONE_AT_A_TIME_SENSITIVITY")
        self.assertEqual(sensitivity["analysis"]["normalized_sensitivity_formula"], "[ln(y_high)-ln(y_low)]/[ln(p_high)-ln(p_low)]")
        self.assertEqual(sensitivity["analysis"]["rank_ceiling"], 3)
        self.assertAlmostEqual(MODULE.normalized_log_secant(2.0, 8.0, 1.0, 2.0), 2.0)
        with self.assertRaises(ValueError):
            MODULE.normalized_log_secant(0.0, 8.0, 1.0, 2.0)

    def test_waszkiewicz_clock_and_unsupported_pressures(self):
        wasz = self.records["waszkiewicz"]
        self.assertEqual(wasz["point_count"], 12)
        self.assertEqual(wasz["optimized_time_shift"], "PROHIBITED")
        self.assertEqual(wasz["clock_mapping"]["optimization"], "PROHIBITED")
        self.assertEqual(wasz["collection_intervals_s"], [[5.0 * i, 5.0 * (i + 1)] for i in range(12)])
        self.assertEqual(wasz["integration_rule"], "PIECEWISE_LINEAR_TRAPEZOIDAL_INTEGRATION_REQUIRING_BOTH_INTERVAL_ENDPOINTS")
        self.assertEqual(wasz["clock_mapping"]["presentations"][1]["model_intervals_s"][0], [3.0, 8.0])
        self.assertEqual(wasz["midpoint_point_sampling"], "PROHIBITED")
        self.assertEqual(wasz["role"]["circularity"], "TDS_AND_DISSOLVED_MASS_SOFT_CIRCULARITY")
        self.assertEqual(wasz["unsupported_chemistry"], {"5_bar": "UNAVAILABLE_NOT_INFERRED", "11_bar": "UNAVAILABLE_NOT_INFERRED"})

    def test_run_matrix_unique_complete_and_not_executed(self):
        matrix = self.records["run_matrix"]
        runs = matrix["final_production_run_inventory"]
        ids = [run["run_id"] for run in runs]
        self.assertEqual(len(ids), 42)
        self.assertEqual(len(set(ids)), 42)
        self.assertEqual(matrix["stage_a_execution"], "NOT_AUTHORIZED")
        required = {"source_aggregation", "base_configuration", "solver", "geometry", "boundary_conditions", "hydraulics", "chemistry", "controls", "observation_operators", "gates", "artifacts"}
        self.assertTrue(all(required <= set(run) for run in runs))
        self.assertEqual(matrix["calibration_evaluation_inventory"]["hydraulic_mode"], "H1_ONLY")
        self.assertEqual(matrix["calibration_evaluation_inventory"]["h0_calibration"], "PROHIBITED")
        self.assertEqual(matrix["calibration_evaluation_inventory"]["maximum_optimizer_evaluations"], 128)
        self.assertEqual(len(matrix["reused_exact_evaluations"]), 1)
        h1 = [run for run in runs if run["hydraulic_role"].startswith("H1")]
        self.assertTrue(all(run["hydraulics"]["physical_permeability_inference"] == "PROHIBITED" for run in h1))
        expected_coefficients = {1: 3.980657465334892e-15, 2: 5.743539807144926e-15, 3: 5.283588250627103e-15, 4: 6.432151968946008e-15, 5: 5.843343533941293e-15, 6: 6.820710710461954e-15, 7: 5.99276290640711e-15}
        for run in h1:
            self.assertTrue(math.isclose(run["hydraulics"]["uniform_saturated_coefficient_m2"], expected_coefficients[run["experiment"]], rel_tol=2e-15, abs_tol=0.0))

    def test_mandatory_metrics_and_claim_ceiling(self):
        metrics = load("VAL_CORPUS_002_METRIC_AND_INTERPRETATION_SPEC.json")
        mandatory = {"cup_solute_mass_g", "cumulative_tds_fraction", "extraction_yield_fraction", "liquid_balance_residual", "solute_balance_residual", "boundedness", "completion"}
        self.assertLessEqual(mandatory, set(metrics["mandatory_outputs"]))
        claims = load("VAL_CORPUS_002_RIGHTS_AND_CLAIM_CEILING.json")
        self.assertEqual(claims["physical_validation"], "NOT_ESTABLISHED")
        self.assertEqual(claims["new_governing_physics"], "NOT_YET_JUSTIFIED")
        self.assertEqual(MODULE.interpolate_fixed_mass([(10.0, 1.0), (30.0, 5.0)], 20.0), 3.0)
        with self.assertRaises(ValueError):
            MODULE.interpolate_fixed_mass([(10.0, 1.0), (30.0, 5.0)], 40.0)
        with self.assertRaises(ValueError):
            MODULE.interpolate_fixed_mass([(10.0, 1.0), (10.0, 2.0)], 10.0)

    def test_waszkiewicz_interval_operator_integrates_not_midpoint_samples(self):
        samples = [(0.0, 0.0, 2.0), (2.5, 1.0, 2.0), (5.0, 0.0, 2.0)]
        self.assertEqual(MODULE.interval_tds(samples, 0.0, 5.0), 0.25)
        self.assertNotEqual(MODULE.interval_tds(samples, 0.0, 5.0), 1.0 / 2.0)
        with self.assertRaises(ValueError):
            MODULE.interval_tds(samples[1:], 0.0, 5.0)

    def test_species_semantics_and_fail_closed_unresolved_mappings(self):
        ledger = load("VAL_CORPUS_002_CALIBRATION_COMPARISON_LEDGER.json")
        species = next(item for item in ledger["partitions"] if item["id"] == "SCHMIEDER_SPECIES")
        self.assertEqual(species["role"], "SOURCE_ONLY_ONE_SOLUTE_LIMITATION_AUDIT")
        hydraulic = load("VAL_CORPUS_002_HYDRAULIC_CHEMISTRY_DECOMPOSITION.json")
        self.assertEqual(hydraulic["schmieder_source_pressure_history"], "UNAVAILABLE_NOT_INFERRED")
        gate = load("VAL_CORPUS_002_STAGE_B_AUTHORIZATION_REQUIREMENTS.json")
        self.assertEqual(gate["authorization_status"], "NONE")
        self.assertEqual(gate["conditional_evidence_treatments_remaining"], 0)

    def test_candidate_treatments_are_exactly_one_and_allowed(self):
        record = load("VAL_CORPUS_002_CANDIDATE_EVIDENCE_ADJUDICATION.json")
        candidates = record["candidates"]
        self.assertEqual(len({item["candidate"] for item in candidates}), len(candidates))
        self.assertEqual(len(candidates), 11)
        self.assertTrue(all(item["treatment"] in record["allowed_treatments"] for item in candidates))
        self.assertNotIn("SECONDARY_IF_FULLY_MAPPED_BEFORE_PROTOCOL_REVIEW", {item["treatment"] for item in candidates})
        egidi = next(item for item in candidates if item["candidate"].startswith("Egidi"))
        self.assertEqual(egidi["treatment"], "EXCLUDED_FROM_STAGE_B_WITH_REASON")


if __name__ == "__main__":
    unittest.main()
