import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prepare_case", ROOT / "scripts/prepare_case.py"
)
PREPARE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PREPARE)


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


if __name__ == "__main__":
    unittest.main()
