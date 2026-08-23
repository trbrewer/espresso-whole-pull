import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prepare_case", ROOT / "scripts/prepare_case.py"
)
PREPARE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PREPARE)
sys.path.insert(0, str(ROOT))
from tools.sci_md_004_stage_c.oracle import (  # noqa: E402
    concentration, discrete_integrals, discrete_mode_closed,
    discrete_mode_recurrence, discrete_mode_sum_closed, discrete_profile,
    discrete_remaining_density, integrated_solution, observed_order,
    remaining_mass, weighted_errors,
)
from tools.sci_md_004_stage_c.runner import validate_complete_result  # noqa: E402


class IndexedSpeciesConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.legacy = json.loads((ROOT / "config/reference_R0.json").read_text())

    def scenario(self):
        scenario = copy.deepcopy(self.legacy)
        scenario["extraction"] = {
            "model": PREPARE.INDEXED_SPECIES_MODEL,
            "legacy_rate_constant_1_s": 0.15,
            "legacy_saturation_concentration_kg_m3": 180.0,
            "species": [
                {
                    "id": "species_a",
                    "role": "explicit_inventory",
                    "dry_coffee_inventory_mass_fraction": 0.10,
                    "availability_fraction": 1.0,
                    "rate_constant_1_s": 0.12,
                    "saturation_concentration_kg_m3": 80.0,
                    "effective_diffusivity_m2_s": 8.0e-10,
                    "parameter_provenance": {
                        key: "FIXED_STRUCTURAL_ASSUMPTION"
                        for key in (
                            "inventory", "availability", "rate",
                            "saturation", "diffusivity",
                        )
                    },
                },
                {
                    "id": "residual_extractables",
                    "role": "structural_balance",
                    "inherit_legacy_parameters": True,
                },
            ],
        }
        return scenario

    def assert_rejected(self, mutate):
        scenario = self.scenario()
        mutate(scenario["extraction"])
        with self.assertRaises(SystemExit):
            PREPARE.indexed_species_contract(scenario)

    def test_legacy_render_is_unchanged_and_has_no_indexed_text(self):
        rendered = PREPARE.render_properties(self.legacy)
        self.assertNotIn("soluteTransportModel", rendered)
        self.assertNotIn("indexedPassiveSpeciesCoeffs", rendered)

    def test_order_residual_and_rendered_schema(self):
        contract = PREPARE.indexed_species_contract(self.scenario())
        self.assertEqual(
            [item["id"] for item in contract["species"]],
            ["species_a", "residual_extractables"],
        )
        self.assertAlmostEqual(contract["species"][1]["effective_fraction"], 0.18)
        rendered = PREPARE.render_properties(self.scenario())
        self.assertLess(rendered.index("species_a"), rendered.index("residual_extractables"))
        self.assertIn("soluteTransportModel indexedPassiveSpecies;", rendered)

    def test_explicit_one_species_reduction(self):
        scenario = self.scenario()
        species = scenario["extraction"]["species"][0]
        species["dry_coffee_inventory_mass_fraction"] = 0.28
        species["rate_constant_1_s"] = 0.15
        species["saturation_concentration_kg_m3"] = 180.0
        species["effective_diffusivity_m2_s"] = 1.0e-9
        scenario["extraction"]["species"] = [species]
        contract = PREPARE.indexed_species_contract(scenario)
        self.assertEqual(contract["species"][0]["effective_fraction"], 0.28)

    def test_rejection_matrix(self):
        mutations = [
            lambda e: e.pop("species"),
            lambda e: e.update(species=[]),
            lambda e: e["species"].append(copy.deepcopy(e["species"][0])),
            lambda e: e["species"][0].update(id="../bad"),
            lambda e: e["species"][0].update(role="unknown"),
            lambda e: e["species"][0].update(dry_coffee_inventory_mass_fraction=-1),
            lambda e: e["species"][0].update(availability_fraction=-0.1),
            lambda e: e["species"][0].update(availability_fraction=1.1),
            lambda e: e["species"][0].update(rate_constant_1_s=-1),
            lambda e: e["species"][0].update(saturation_concentration_kg_m3=0),
            lambda e: e["species"][0].update(effective_diffusivity_m2_s=-1),
            lambda e: e["species"].append(
                {"id": "balance_b", "role": "structural_balance",
                 "inherit_legacy_parameters": True}
            ),
            lambda e: e["species"][1].update(rate_constant_1_s=0.2),
            lambda e: e["species"][0].update(dry_coffee_inventory_mass_fraction=0.4),
            lambda e: e["species"][0]["parameter_provenance"].update(
                rate="HOLDOUT_ENDPOINT_DERIVED"
            ),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_rejected(mutation)

    def test_underallocation_without_structural_balance_rejected(self):
        scenario = self.scenario()
        scenario["extraction"]["species"] = scenario["extraction"]["species"][:1]
        with self.assertRaises(SystemExit):
            PREPARE.indexed_species_contract(scenario)

    def test_two_renderings_are_byte_identical(self):
        first = PREPARE.render_properties(self.scenario()).encode()
        second = PREPARE.render_properties(self.scenario()).encode()
        self.assertEqual(first, second)


class StageCScopeTests(unittest.TestCase):
    def test_holdout_is_fail_closed(self):
        stage_c_paths = [
            ROOT / "tools/sci_md_004_stage_c",
            ROOT / "scripts/prepare_case.py",
            ROOT / "solver/espressoWholePullFoam/espressoWholePullFoam.C",
        ]
        forbidden = (
            "tools.sci_md_004_contract.consumer.consume",
            "angeloni_targets_long.csv",
            "holdout scorer",
        )
        for path in stage_c_paths:
            files = [path] if path.is_file() else list(path.rglob("*.py"))
            for file_path in files:
                text = file_path.read_text(encoding="utf-8")
                for token in forbidden:
                    self.assertNotIn(token, text, str(file_path))

    def test_forbidden_repository_paths_are_unchanged(self):
        import subprocess
        changed = subprocess.run(
            ["git", "diff", "--name-only", "origin/main"], cwd=ROOT,
            check=True, text=True, capture_output=True,
        ).stdout.splitlines()
        forbidden = (
            "dependencies/puckworks.lock.json",
            ".github/workflows/",
            "boundary/",
            "cases/reference_R0_20g_58mm_9bar/",
        )
        self.assertFalse([p for p in changed if p.startswith(forbidden)])


class R1FailClosedTests(unittest.TestCase):
    @staticmethod
    def valid_v15_subgates():
        return {
            "V15A": {"status": "PASS"},
            "V15B": {"status": "PASS", "analytical": {"coarse": {}},
                "temporal": {f"dt_{value}": {} for value in range(5)},
                "metric_classification": {
                    "spatial": ["profile_l1_relative", "profile_l2_relative",
                                "profile_linf_relative"],
                    "temporal": ["remaining_mass", "profile_l1_relative",
                                 "profile_l2_relative", "profile_linf_relative"],
                    "invariant": ["remaining_mass"],
                    "diagnostic": ["error_of_error_ratio"]}},
            "V15C": {"status": "PASS"},
        }

    def test_missing_required_assertion_forces_failure(self):
        gate = {
            "status": "PASS", "scenario_hashes": ["a"], "executable_hash": "b",
            "ranks": [1], "meshes": [[1, 1]], "timesteps_s": [1.0],
            "metrics": {"assertion": "PASS"}, "tolerances": {"x": 0.0},
            "per_species": {}, "aggregate": {}, "evidence_paths": [__file__],
            "output_hashes": {}, "failure_reasons": [],
        }
        result = {"gates": {f"V{i}": copy.deepcopy(gate) for i in range(1, 19)}}
        result["gates"]["V15"]["metrics"] = {
            "subgates": self.valid_v15_subgates()}
        self.assertTrue(validate_complete_result(result, verify_hashes=False))
        del result["gates"]["V10"]
        defects = validate_complete_result(result, verify_hashes=False)
        self.assertTrue(any("V10" in defect for defect in defects))

    def test_v17_boolean_placeholder_is_rejected(self):
        result = {"gates": {}}
        for number in range(1, 19):
            result["gates"][f"V{number}"] = {
                "status": "PASS", "scenario_hashes": ["a"],
                "executable_hash": "b", "ranks": [1], "meshes": [[1, 1]],
                "timesteps_s": [1.0], "metrics": {"assertion": "PASS"},
                "tolerances": {"x": 0.0}, "per_species": {}, "aggregate": {},
                "evidence_paths": [__file__], "output_hashes": {},
                "failure_reasons": [],
            }
        result["gates"]["V15"]["metrics"] = {
            "subgates": self.valid_v15_subgates()}
        result["gates"]["V17"]["metrics"] = {
            "categories": {f"case_{i}": True for i in range(39)}}
        self.assertTrue(any("Boolean placeholder" in item for item in
                            validate_complete_result(result, verify_hashes=False)))

    def complete_result(self):
        gate = {"status":"PASS","scenario_hashes":["a"],
            "executable_hash":"b","ranks":[1],"meshes":[[1,1]],
            "timesteps_s":[1.0],"metrics":{"assertion":"PASS"},
            "tolerances":{"x":0},"per_species":{},"aggregate":{},
            "evidence_paths":[__file__],"output_hashes":{},"failure_reasons":[]}
        result={"gates":{f"V{i}":copy.deepcopy(gate) for i in range(1,19)}}
        result["gates"]["V15"]["metrics"]={"subgates":self.valid_v15_subgates()}
        result["gates"]["V17"]["metrics"]={"categories":{
            f"case_{i}":"PASS" for i in range(39)}}
        return result

    def test_remaining_mass_spatial_classification_is_rejected(self):
        result=self.complete_result()
        result["gates"]["V15"]["metrics"]["subgates"]["V15B"][
            "metric_classification"]["spatial"].append("remaining_mass")
        self.assertTrue(any("remaining mass" in item for item in
            validate_complete_result(result,verify_hashes=False)))

    def test_removed_profile_norm_is_rejected(self):
        result=self.complete_result()
        result["gates"]["V15"]["metrics"]["subgates"]["V15B"][
            "metric_classification"]["spatial"].remove("profile_linf_relative")
        self.assertTrue(any("profile norm" in item for item in
            validate_complete_result(result,verify_hashes=False)))

    def test_omitted_discrete_oracle_is_rejected(self):
        result=self.complete_result()
        result["gates"]["V15"]["metrics"]["subgates"]["V15B"]["analytical"]={}
        self.assertTrue(any("spatial oracle" in item for item in
            validate_complete_result(result,verify_hashes=False)))

    def test_incomplete_temporal_sequence_is_rejected(self):
        result=self.complete_result()
        result["gates"]["V15"]["metrics"]["subgates"]["V15B"]["temporal"].pop("dt_4")
        self.assertTrue(any("temporal sequence incomplete" in item for item in
            validate_complete_result(result,verify_hashes=False)))

    def test_missing_v15c_is_rejected(self):
        result=self.complete_result()
        del result["gates"]["V15"]["metrics"]["subgates"]["V15C"]
        self.assertTrue(any("incomplete V15A" in item for item in
            validate_complete_result(result,verify_hashes=False)))

    def test_altered_evidence_is_rejected(self):
        result=self.complete_result()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"evidence.txt"; path.write_text("altered")
            gate=result["gates"]["V1"]
            gate["evidence_paths"]=[str(path)]
            gate["output_hashes"]={str(path):"0"*64}
            self.assertTrue(any("evidence hash mismatch" in item for item in
                validate_complete_result(result,verify_hashes=True)))

    def test_executable_hash_change_is_rejected(self):
        result=self.complete_result(); result["executable_sha256"]="expected"
        self.assertTrue(any("executable hash mismatch" in item for item in
            validate_complete_result(result,verify_hashes=False)))

    def test_protected_target_path_flag_is_rejected(self):
        result=self.complete_result(); result["forbidden_target_path_present"]=True
        self.assertIn("protected target path present",
                      validate_complete_result(result,verify_hashes=False))


class R1AnalyticalOracleTests(unittest.TestCase):
    def test_inventory_decay(self):
        self.assertAlmostEqual(remaining_mass(0.14, 0.12, 2.0),
                               0.14 * __import__("math").exp(-0.24))

    def test_profile_boundary_and_remainder(self):
        value, metadata = concentration(
            x=0.0, time_s=2.0, length_m=0.009, phi=0.4,
            diffusivity=8e-7, rate=0.12, initial_inventory_density=100.0)
        self.assertEqual(value, 0.0)
        self.assertLessEqual(metadata["estimated_relative_remainder"], 1e-10)

    def test_weighted_profile_errors(self):
        result = weighted_errors([1.0, 2.0], [1.0, 2.0], [0.5, 0.5])
        self.assertEqual(result["l1_relative"], 0.0)
        self.assertEqual(result["l2_relative"], 0.0)

    def test_positive_observed_order(self):
        self.assertAlmostEqual(observed_order(0.04, 0.01), 2.0)


class R2SeparatedSpaceTimeOracleTests(unittest.TestCase):
    def parameters(self, **updates):
        values = {
            "steps": 4000, "delta_t": 5.0e-4, "length_m": 0.009,
            "phi": 0.4, "diffusivity": 2.0e-7, "rate": 0.05,
            "initial_inventory_density": 70.0,
        }
        values.update(updates)
        return values

    def test_recurrence_and_closed_form_agree(self):
        for mode in (0, 1, 7, 31):
            with self.subTest(mode=mode):
                recurrence = discrete_mode_recurrence(mode=mode, **self.parameters())
                closed = discrete_mode_closed(mode=mode, **self.parameters())
                self.assertAlmostEqual(recurrence, closed, delta=abs(closed)*2e-12)

    def test_closed_modal_sum_agrees_with_recurrence(self):
        parameters = self.parameters(steps=200)
        for mode in (0, 5, 20):
            expected = sum(discrete_mode_recurrence(
                mode=mode, **(parameters | {"steps": step}))
                for step in range(1, parameters["steps"]+1))
            actual = discrete_mode_sum_closed(mode=mode, **parameters)
            self.assertAlmostEqual(actual, expected, delta=abs(expected)*2e-11)

    def test_equal_rate_limit(self):
        parameters = self.parameters(steps=100, delta_t=1e-3)
        eigenvalue = 0.5*__import__("math").pi/parameters["length_m"]
        parameters["diffusivity"] = (parameters["rate"] /
            (1-parameters["rate"]*parameters["delta_t"]))/eigenvalue**2
        recurrence = discrete_mode_recurrence(mode=0, **parameters)
        closed = discrete_mode_closed(mode=0, **parameters)
        self.assertAlmostEqual(recurrence, closed, delta=abs(closed)*2e-12)

    def test_discrete_oracle_converges_first_order_to_continuous(self):
        math = __import__("math")
        errors = []
        for dt in (4e-3, 2e-3, 1e-3, 5e-4):
            steps = round(2.0/dt)
            discrete = discrete_remaining_density(70.0, .05, dt, steps)
            continuous = 70.0*math.exp(-.1)
            errors.append(abs(discrete-continuous)/continuous)
        orders = [observed_order(errors[i], errors[i+1]) for i in range(3)]
        self.assertTrue(all(.99 < order < 1.01 for order in orders), orders)

    def test_discrete_flux_and_closure_agree_and_tail_is_resolved(self):
        result = discrete_integrals(area_m2=0.002, terms=20000,
                                    **self.parameters())
        self.assertLessEqual(result["flux_closure_relative_initial"], 1e-10)
        self.assertLessEqual(result["estimated_relative_remainder"], 1e-10)

    def test_discrete_profile_is_deterministic(self):
        locations = [(index+.5)*.009/64 for index in range(64)]
        first = discrete_profile(locations_m=locations, terms=10000,
                                 **self.parameters())
        second = discrete_profile(locations_m=locations, terms=10000,
                                  **self.parameters())
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))
        self.assertLessEqual(first[1]["estimated_relative_remainder"], 1e-10)

    def test_oracle_has_no_production_import(self):
        source = (ROOT / "tools/sci_md_004_stage_c/oracle.py").read_text()
        for forbidden in ("espressoWholePullFoam", "prepare_case", "runner"):
            self.assertNotIn(f"import {forbidden}", source)


class R1GeneratedCollisionRejectionTests(unittest.TestCase):
    def test_generated_field_name_collision(self):
        with self.assertRaises(SystemExit):
            PREPARE.validate_indexed_generated_names(
                ["species_a"], existing_fields={"dissolvedConcentration_species_a"})

    def test_generated_trace_name_collision(self):
        with self.assertRaises(SystemExit):
            PREPARE.validate_indexed_generated_names(
                ["species_a"], existing_traces={"species_trace_species_a"})

    def test_aggregate_field_collision(self):
        with self.assertRaises(SystemExit):
            PREPARE.validate_indexed_generated_names(
                ["species_a"],
                aggregate_fields={"dissolvedConcentration_species_a"})

    def test_duplicate_rendered_dictionary_key(self):
        with self.assertRaises(SystemExit):
            PREPARE.validate_indexed_generated_names(["species_a", "species_a"])


class R1IndividualParserRejectionTests(IndexedSpeciesConfigurationTests):
    """Each generated method has one stable category name in unittest output."""


def _remove_species(extraction):
    extraction.pop("species")


def _species_entry(extraction):
    return extraction["species"][0]


REJECTION_MUTATIONS = {
    "missing_species_list": _remove_species,
    "empty_species_list": lambda e: e.update(species=[]),
    "duplicate_species_id": lambda e: e["species"].append(copy.deepcopy(e["species"][0])),
    "invalid_openfoam_word": lambda e: _species_entry(e).update(id="bad-name"),
    "path_traversal_syntax": lambda e: _species_entry(e).update(id="../bad"),
    "whitespace_containing_id": lambda e: _species_entry(e).update(id="bad id"),
    "unstable_id": lambda e: _species_entry(e).update(id="café"),
    "unknown_role": lambda e: _species_entry(e).update(role="unknown"),
    "missing_species_dictionary": lambda e: e["species"].__setitem__(0, None),
    "missing_inventory": lambda e: _species_entry(e).pop("dry_coffee_inventory_mass_fraction"),
    "negative_inventory": lambda e: _species_entry(e).update(dry_coffee_inventory_mass_fraction=-1),
    "nan_inventory": lambda e: _species_entry(e).update(dry_coffee_inventory_mass_fraction=float("nan")),
    "infinite_inventory": lambda e: _species_entry(e).update(dry_coffee_inventory_mass_fraction=float("inf")),
    "availability_below_zero": lambda e: _species_entry(e).update(availability_fraction=-0.1),
    "availability_above_one": lambda e: _species_entry(e).update(availability_fraction=1.1),
    "nan_availability": lambda e: _species_entry(e).update(availability_fraction=float("nan")),
    "negative_transfer_constant": lambda e: _species_entry(e).update(rate_constant_1_s=-1),
    "nan_transfer_constant": lambda e: _species_entry(e).update(rate_constant_1_s=float("nan")),
    "zero_saturation_concentration": lambda e: _species_entry(e).update(saturation_concentration_kg_m3=0),
    "negative_saturation_concentration": lambda e: _species_entry(e).update(saturation_concentration_kg_m3=-1),
    "nan_saturation_concentration": lambda e: _species_entry(e).update(saturation_concentration_kg_m3=float("nan")),
    "negative_diffusivity": lambda e: _species_entry(e).update(effective_diffusivity_m2_s=-1),
    "nan_diffusivity": lambda e: _species_entry(e).update(effective_diffusivity_m2_s=float("nan")),
    "multiple_structural_balance_species": lambda e: e["species"].append({"id":"balance_b","role":"structural_balance","inherit_legacy_parameters":True}),
    "structural_balance_without_inheritance": lambda e: e["species"][1].update(inherit_legacy_parameters=False),
    "structural_balance_with_independent_inventory": lambda e: e["species"][1].update(dry_coffee_inventory_mass_fraction=0.18),
    "structural_balance_with_conflicting_rate": lambda e: e["species"][1].update(rate_constant_1_s=0.2),
    "structural_balance_with_conflicting_saturation": lambda e: e["species"][1].update(saturation_concentration_kg_m3=1.0),
    "structural_balance_with_conflicting_diffusivity": lambda e: e["species"][1].update(effective_diffusivity_m2_s=1e-8),
    "explicit_over_allocation": lambda e: _species_entry(e).update(dry_coffee_inventory_mass_fraction=0.4),
    "explicit_under_allocation_without_residual": lambda e: e.update(species=e["species"][:1]),
    "closure_outside_frozen_tolerance": lambda e: (e.update(species=e["species"][:1]), _species_entry(e).update(dry_coffee_inventory_mass_fraction=0.280000000000002)),
    "forbidden_provenance_class": lambda e: _species_entry(e)["parameter_provenance"].update(rate="HOLDOUT_ENDPOINT_DERIVED"),
    "missing_provenance_key": lambda e: _species_entry(e)["parameter_provenance"].pop("rate"),
    "unknown_provenance_class": lambda e: _species_entry(e)["parameter_provenance"].update(rate="UNKNOWN"),
}


def _make_rejection_test(mutation):
    def test(self):
        self.assert_rejected(mutation)
    return test


for _category, _mutation in REJECTION_MUTATIONS.items():
    setattr(R1IndividualParserRejectionTests, f"test_reject_{_category}",
            _make_rejection_test(_mutation))


if __name__ == "__main__":
    unittest.main()
