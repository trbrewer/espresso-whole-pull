from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "config/reconstruction_R1_waszkiewicz_9bar.json"
PROVENANCE = ROOT / "validation/r1/WP01R_004_INPUT_PROVENANCE.json"
MANIFEST = ROOT / "validation/r1/WP01R_004_GENERATED_CASE_MANIFEST.json"

SPEC = importlib.util.spec_from_file_location(
    "prepare_case_for_r1_tests", ROOT / "scripts/prepare_case.py"
)
assert SPEC and SPEC.loader
PREPARE_CASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREPARE_CASE)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class R1BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenario = load(SCENARIO)
        cls.provenance = load(PROVENANCE)
        cls.manifest = load(MANIFEST)
        cls.temp = tempfile.TemporaryDirectory()
        cls.temp_root = Path(cls.temp.name)
        cls.case_a = cls.temp_root / "case-a"
        cls.case_b = cls.temp_root / "unrelated" / "case-b"
        for case in (cls.case_a, cls.case_b):
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/prepare_case.py"),
                    "--root",
                    str(ROOT),
                    "--config",
                    str(SCENARIO),
                    "--case-dir",
                    str(case),
                    "--nprocs",
                    "32",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={"PYTHONDONTWRITEBYTECODE": "1"},
            )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_bridge_check_and_exact_authorities(self) -> None:
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/r1_contract_bridge.py"),
                "--root",
                str(ROOT),
                "--output",
                str(SCENARIO),
                "--check",
            ],
            check=True,
            capture_output=True,
            text=True,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        )
        contract = load(
            ROOT / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json"
        )
        dossier = load(
            ROOT / "validation/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.json"
        )
        lock = load(ROOT / "dependencies/puckworks.lock.json")
        self.assertEqual(contract["contract_status"], "FROZEN_FOR_WP01R_004")
        self.assertEqual(
            lock["checkout_commit"],
            "fc61c4670ec7bf801e40bb391aab16048b8da26b",
        )
        self.assertEqual(
            lock["checkout_tree_sha"],
            "1d553e44ee2f7480a5df521560801b478618cc84",
        )
        self.assertEqual(
            dossier["dossier_disposition"],
            "READY_FOR_WP01R_003_WITH_DECLARED_GAPS",
        )

    def test_bridge_fails_closed_for_missing_and_unsupported_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/r1_contract_bridge.py"),
                    "--root",
                    temp,
                    "--output",
                    str(Path(temp) / "scenario.json"),
                ],
                capture_output=True,
                text=True,
                env={"PYTHONDONTWRITEBYTECODE": "1"},
            )
            self.assertNotEqual(result.returncode, 0)
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            for relative in (
                "dependencies/puckworks.lock.json",
                "validation/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.json",
                "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json",
                "config/reference_R0.json",
            ):
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)
            contract_path = (
                target
                / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json"
            )
            contract = load(contract_path)
            contract["schema_version"] = "unsupported"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/r1_contract_bridge.py"),
                    "--root",
                    str(target),
                    "--output",
                    str(target / "scenario.json"),
                ],
                capture_output=True,
                text=True,
                env={"PYTHONDONTWRITEBYTECODE": "1"},
            )
            self.assertNotEqual(result.returncode, 0)

    def test_canonical_scientific_values_and_truthful_scope(self) -> None:
        scenario = self.scenario
        geometry = scenario["geometry"]
        bed = scenario["coffee_bed"]
        hydraulics = scenario["hydraulics"]
        self.assertEqual(geometry["hardware_basket_diameter_m"], 0.058)
        self.assertEqual(geometry["basket_diameter_m"], 0.056)
        self.assertEqual(geometry["basket_radius_m"], 0.028)
        self.assertAlmostEqual(
            geometry["hydraulic_bed_area_m2"], 3.141592653589793 * 0.028**2
        )
        self.assertAlmostEqual(
            bed["initial_porosity"],
            1.0
            - bed["dry_dose_kg"]
            / (
                bed["particle_solid_density_kg_m3"]
                * geometry["hydraulic_bed_area_m2"]
                * bed["bed_depth_m"]
            ),
        )
        self.assertEqual(hydraulics["target_inlet_pressure_gauge_Pa"], 870902.4190000001)
        self.assertEqual(
            scenario["source_time_mapping"][
                "solver_time_equals_source_time_plus_s"
            ],
            3.0,
        )
        self.assertFalse(
            scenario["source_time_mapping"]["source_fixed_8s_offset_used"]
        )
        self.assertEqual(
            hydraulics["saturated_permeability_m2"], 2.8642613245723525e-15
        )
        self.assertEqual(
            hydraulics["wetting_permeability_m2"],
            hydraulics["saturated_permeability_m2"],
        )
        self.assertEqual(hydraulics["historically_calibrated_parameter_count"], 1)
        self.assertEqual(hydraulics["runtime_adjustable_parameter_count"], 0)
        governance = scenario["governance"]
        self.assertEqual(governance["change_scope"], "SOURCE_SCENARIO_CHANGE_ONLY")
        self.assertFalse(governance["governing_physics_change"])
        self.assertFalse(governance["qualified_R0_scientific_configuration_change"])
        self.assertTrue(governance["new_R1_scientific_configuration_added"])
        self.assertTrue(governance["package_scientific_configuration_change"])

    def test_flow_contract_is_carried_without_protected_values(self) -> None:
        flow = self.scenario["flow_comparison_contract"]
        primary = flow["primary_predicted_quantity"]
        self.assertEqual(primary["solver_native_field"], "outlet_flow_m3_s")
        self.assertEqual(primary["liquid_density_kg_m3"], 965.0)
        self.assertFalse(primary["includes_solute_mass_flux"])
        self.assertEqual(
            primary["formula"],
            "q_pred_g_per_s = 1000 * liquid_density_kg_m3 * outlet_flow_m3_s",
        )
        secondary = flow["secondary_unscored_diagnostic"]
        self.assertEqual(secondary["comparison_role"], "UNSCORED_DIAGNOSTIC")
        self.assertFalse(secondary["may_replace_primary_quantity"])
        self.assertEqual(flow["protected_shot_ids"], ["9-1", "9-2", "9-3", "9-4", "9-5"])
        self.assertEqual(flow["protected_indices"], {"first": 100, "inclusive": True, "last": 899})
        self.assertEqual(flow["normalization_indices"], {"first": 900, "inclusive": True, "last": 999})
        self.assertEqual(
            flow["pearson_degeneracy"]["normalized_standard_deviation_epsilon"],
            1e-8,
        )
        self.assertEqual(flow["pearson_degeneracy"]["undefined_disposition"], "FAIL")
        self.assertFalse(flow["protected_series_embedded"])
        text = SCENARIO.read_text(encoding="utf-8")
        self.assertNotIn("mass_flow_rate__g_per_s\": [", text)

    def test_provenance_is_complete_and_has_no_scientific_defaults(self) -> None:
        provenance = self.provenance
        self.assertEqual(
            provenance["scientific_fields_consumed_by_generator"],
            provenance["scientific_fields_with_provenance"],
        )
        self.assertEqual(
            provenance["scientific_fields_consumed_by_generator"],
            len(provenance["records"]),
        )
        self.assertEqual(provenance["provenance_coverage_percent"], 100.0)
        self.assertEqual(provenance["ungoverned_scientific_defaults"], 0)
        self.assertEqual(provenance["runtime_adjustable_scientific_parameters"], 0)
        destinations = {
            item["destination_scenario_json_pointer"]
            for item in provenance["records"]
        }
        for required in (
            "/geometry/basket_radius_m",
            "/coffee_bed/initial_porosity",
            "/hydraulics/saturated_permeability_m2",
            "/flow_comparison_contract/primary_predicted_quantity",
            "/flow_comparison_contract/pearson_degeneracy",
        ):
            self.assertIn(required, destinations)

    def test_two_generations_have_identical_governed_bytes(self) -> None:
        manifest_a = load(self.case_a / "WP01R_004_GENERATED_CASE_MANIFEST.json")
        manifest_b = load(self.case_b / "WP01R_004_GENERATED_CASE_MANIFEST.json")
        self.assertEqual(manifest_a, manifest_b)
        self.assertEqual(
            manifest_a["canonical_scenario"]["sha256"],
            self.manifest["canonical_scenario"]["sha256"],
        )
        for relative in manifest_a["governed_generated_file_sha256"]:
            self.assertEqual(
                (self.case_a / relative).read_bytes(),
                (self.case_b / relative).read_bytes(),
                relative,
            )
        text = (self.case_a / "WP01R_004_GENERATED_CASE_MANIFEST.json").read_text(
            encoding="utf-8"
        )
        self.assertNotIn(str(self.case_a), text)
        self.assertNotIn(str(self.case_b), text)
        self.assertNotIn("generated_at", text)
        self.assertNotIn("timestamp", text.lower())
        self.assertFalse((self.case_a / "RUN_ENVIRONMENT_V0_1_4.json").exists())
        generation = manifest_a["case_generation"]
        self.assertEqual(generation["generation_invocation_count"], 1)
        self.assertFalse(generation["cross_directory_comparison_performed"])
        self.assertEqual(
            generation["cross_directory_byte_identity_result"],
            "NOT_PERFORMED_IN_THIS_INVOCATION",
        )
        qualification = manifest_a["generator_determinism_qualification"]
        self.assertEqual(qualification["replay_count"], 2)
        self.assertEqual(
            qualification["cross_directory_byte_identity_result"], "PASS"
        )
        self.assertEqual(
            qualification["qualified_generator_sha256"],
            sha256(ROOT / "scripts/prepare_case.py"),
        )
        self.assertIn(
            "test_two_generations_have_identical_governed_bytes",
            qualification["qualification_test"],
        )

    def test_r1_requires_explicit_case_dir_without_touching_r0(self) -> None:
        reference = ROOT / "cases/reference_R0_20g_58mm_9bar"
        before = {
            path.relative_to(reference).as_posix(): sha256(path)
            for path in reference.rglob("*")
            if path.is_file()
        }
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/prepare_case.py"),
                "--root",
                str(ROOT),
                "--config",
                str(SCENARIO),
                "--nprocs",
                "32",
            ],
            capture_output=True,
            text=True,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires explicit --case-dir", result.stderr)
        after = {
            path.relative_to(reference).as_posix(): sha256(path)
            for path in reference.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)

    def test_r1_rejects_nonempty_stale_and_symlink_targets_before_mutation(self) -> None:
        stale_names = (
            "ordinary-file",
            "constant/polyMesh/points",
            "processor0/U",
            "postProcessing/flow/0.dat",
            "12/U",
        )
        for index, relative in enumerate(stale_names):
            target = self.temp_root / f"stale-{index}"
            stale = target / relative
            stale.parent.mkdir(parents=True)
            stale.write_text("unchanged\n", encoding="utf-8")
            before = {
                path.relative_to(target).as_posix(): path.read_bytes()
                for path in target.rglob("*")
                if path.is_file()
            }
            result = self._run_prepare(target)
            self.assertNotEqual(result.returncode, 0, relative)
            after = {
                path.relative_to(target).as_posix(): path.read_bytes()
                for path in target.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after, relative)
        empty = self.temp_root / "empty-target"
        empty.mkdir()
        self.assertEqual(self._run_prepare(empty).returncode, 0)
        link = self.temp_root / "case-link"
        link.symlink_to(self.case_a, target_is_directory=True)
        result = self._run_prepare(link)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)

    def test_only_exact_canonical_scenario_is_accepted(self) -> None:
        copied = self.temp_root / "copied-scenario.json"
        copied.write_bytes(SCENARIO.read_bytes())
        result = self._run_prepare(
            self.temp_root / "copied-case", config=copied
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact canonical config", result.stderr)
        altered = load(SCENARIO)
        altered["hydraulics"]["target_inlet_pressure_gauge_Pa"] += 1.0
        altered_path = self.temp_root / "altered-scenario.json"
        altered_path.write_text(json.dumps(altered), encoding="utf-8")
        result = self._run_prepare(
            self.temp_root / "altered-case", config=altered_path
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self._run_prepare(self.temp_root / "canonical-case").returncode, 0)

    def test_r1_missing_scientific_fields_fail_closed(self) -> None:
        removals = (
            ("hydraulics", "permeability_profile", "interface_position_m"),
            ("verification", "pressure_probes"),
            ("output", "write_format"),
            ("wetting", "initial_wet_front_m"),
        )
        for path in removals:
            scenario = json.loads(json.dumps(self.scenario))
            target = scenario
            for key in path[:-1]:
                target = target[key]
            del target[path[-1]]
            with self.assertRaises(SystemExit, msg="/".join(path)):
                PREPARE_CASE.validate_r1_scenario(scenario, 32)

    def test_r1_analytical_note_is_source_linked_not_r0_calibration(self) -> None:
        preview = load(self.case_a / "preflight/ANALYTICAL_PREFLIGHT_V0_1_4.json")
        notes = " ".join(preview["notes"])
        self.assertIn("source-linked deterministic analytical inversion", notes)
        self.assertIn("not adjustable", notes)
        self.assertNotIn("declared R0 hydraulic calibration parameter", notes)

    def _run_prepare(
        self, target: Path, *, config: Path = SCENARIO
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/prepare_case.py"),
                "--root",
                str(ROOT),
                "--config",
                str(config),
                "--case-dir",
                str(target),
                "--nprocs",
                "32",
            ],
            capture_output=True,
            text=True,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        )

    def test_qualified_templates_and_r0_sources_are_unchanged(self) -> None:
        reference = ROOT / "cases/reference_R0_20g_58mm_9bar"
        for name in ("fvSchemes", "fvSolution"):
            self.assertEqual(
                (self.case_a / "system" / name).read_bytes(),
                (reference / "system" / name).read_bytes(),
            )
        for source in sorted((reference / "0.orig").iterdir()):
            self.assertEqual(
                (self.case_a / "0.orig" / source.name).read_bytes(),
                source.read_bytes(),
            )
        self.assertNotEqual(
            sha256(ROOT / "solver/espressoWholePullFoam/espressoWholePullFoam.C"),
            "33412d78b8c0624ea6279acbb2c5d653c15a4753a38a228b58d27307110737f1",
        )
        self.assertEqual(
            sha256(ROOT / "scripts/espresso_reference_math.py"),
            "c5331b8fc11bc4f04c939206e4b1e227cf46be16264b403b845af5294164f1d0",
        )
        self.assertEqual(
            sha256(ROOT / "config/reference_R0.json"),
            "67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286",
        )
        baseline = load(ROOT / "validation/baselines/v0.1.4/PUBLIC_BASELINE_SUMMARY.json")
        self.assertEqual(
            baseline["scientific_input_aggregate_sha256"],
            "d70399a76b0023d93985d76c1c83a9a42b7148b3d71d16d1b5f88275be1ebe7a",
        )

    def test_execution_boundary_is_zero(self) -> None:
        counters = self.scenario["execution_boundaries"]
        self.assertEqual(counters["openfoam_execution_count"], 0)
        self.assertEqual(counters["protected_comparison_execution_count"], 0)
        self.assertEqual(counters["parameter_fitting_count"], 0)
        self.assertEqual(counters["optimizer_iteration_count"], 0)
        self.assertEqual(counters["puckworks_code_execution_count"], 0)
        self.assertEqual(counters["scientific_result_status"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
