from __future__ import annotations

import csv
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from espresso_reference_math import (  # noqa: E402
    analytical_preview,
    b0_reduced_simulation,
    discrete_layered_pressure_reference,
    first_drip_time_s,
    positive_driving_pressure_integral,
    straight_sided_wedge_scale,
)
from generate_source_manifest import excluded  # noqa: E402
from prepare_case import render_control_dict  # noqa: E402
from run_qualification import (  # noqa: E402
    PRIMARY_KEYS,
    aggregate_standard,
    write_runs_csv,
)

REFERENCE = json.loads((ROOT / "config/reference_R0.json").read_text(encoding="utf-8"))
LAYERED = json.loads((ROOT / "config/fixture_layered_pressure.json").read_text(encoding="utf-8"))


class ReferenceMathematicsTests(unittest.TestCase):
    def test_bed_depth_is_derived(self) -> None:
        bed = REFERENCE["coffee_bed"]
        geometry = REFERENCE["geometry"]
        expected = bed["dry_dose_kg"] / (
            bed["particle_solid_density_kg_m3"]
            * (1.0 - bed["initial_porosity"])
            * math.pi
            * geometry["basket_radius_m"] ** 2
        )
        self.assertAlmostEqual(expected, bed["bed_depth_m"], places=15)

    def test_exact_first_drip_reference_value(self) -> None:
        self.assertAlmostEqual(first_drip_time_s(REFERENCE), 4.71169618523187, places=13)

    def test_pressure_integral_matches_ramp_triangle_and_plateau(self) -> None:
        target = 900000.0
        ramp = 3.0
        self.assertAlmostEqual(
            positive_driving_pressure_integral(0.0, ramp, target, ramp, 0.0),
            0.5 * target * ramp,
            places=8,
        )
        self.assertAlmostEqual(
            positive_driving_pressure_integral(0.0, 5.0, target, ramp, 0.0),
            0.5 * target * ramp + target * 2.0,
            places=8,
        )

    def test_pressure_integral_honours_positive_front_threshold(self) -> None:
        target = 100.0
        ramp = 10.0
        front = 25.0
        # Driving pressure becomes positive at 2.5 s; 2.5..5 is a triangle
        # rising from 0 to 25 Pa.
        self.assertAlmostEqual(
            positive_driving_pressure_integral(0.0, 5.0, target, ramp, front),
            0.5 * 2.5 * 25.0,
            places=12,
        )

    def test_exact_straight_sided_wedge_scale(self) -> None:
        scale = straight_sided_wedge_scale(5.0)
        self.assertAlmostEqual(scale, 72.09146648398465, places=13)
        radius = REFERENCE["geometry"]["basket_radius_m"]
        depth = REFERENCE["coffee_bed"]["bed_depth_m"]
        wedge_volume = 0.5 * radius * radius * math.sin(math.radians(5.0)) * depth
        cylinder_volume = math.pi * radius * radius * depth
        self.assertAlmostEqual(scale * wedge_volume, cylinder_volume, places=18)

    def test_analytical_preview_uses_corrected_reference(self) -> None:
        preview = analytical_preview(REFERENCE)
        self.assertAlmostEqual(preview["first_drip_s"], 4.71169618523187, places=13)
        self.assertAlmostEqual(
            preview["steady_outlet_volume_flow_m3_s"],
            1.4826759715944223e-6,
            places=18,
        )
        self.assertAlmostEqual(
            preview["saturated_pore_water_mass_kg"],
            0.00919047619047619,
            places=16,
        )

    def test_b0_reduced_twin_conserves_and_is_bounded(self) -> None:
        result = b0_reduced_simulation(REFERENCE)
        outputs = result["primary_outputs"]
        self.assertLess(outputs["max_liquid_balance_residual_kg"], 1.0e-12)
        self.assertLess(outputs["max_solute_balance_residual_kg"], 1.0e-12)
        self.assertGreater(outputs["cup_beverage_mass_at_end_kg"], 0.035)
        self.assertLess(outputs["cup_beverage_mass_at_end_kg"], 0.050)
        self.assertAlmostEqual(outputs["first_drip_s"], first_drip_time_s(REFERENCE), places=12)

    def test_layered_discrete_reference_is_nontrivial(self) -> None:
        result = discrete_layered_pressure_reference(LAYERED)
        self.assertAlmostEqual(result["outlet_flow_m3_s"], 1.0108903065127255e-6, places=18)
        probes = result["pressure_probe_values_pa"]
        self.assertGreater(probes[0], probes[1])
        self.assertGreater(probes[0], 500000.0)
        self.assertLess(probes[1], 100000.0)


class PackageContractTests(unittest.TestCase):
    def test_versions_match_v014(self) -> None:
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "0.1.4")
        self.assertEqual(REFERENCE["solver_version"], "0.1.4")
        self.assertEqual(LAYERED["solver_version"], "0.1.4")
        cpp = (ROOT / "solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text(encoding="utf-8")
        self.assertIn("espressoWholePullFoam v0.1.4", cpp)

    def test_reference_remains_explicit_calibration(self) -> None:
        self.assertEqual(REFERENCE["mode"], "calibration")
        self.assertEqual(REFERENCE["calibration"]["parameter"], "saturated_permeability_m2")
        self.assertEqual(REFERENCE["calibration"]["independent_validation_status"], "not_validated")

    def test_qualified_routine_default_is_32_ranks(self) -> None:
        self.assertEqual(REFERENCE["parallel"]["default_subdomains"], 32)
        allrun = (ROOT / "Allrun").read_text(encoding="utf-8")
        self.assertIn("DEFAULT_NPROCS=32", allrun)

    def test_no_physics_change_source_contract_is_bundled(self) -> None:
        baseline = ROOT / "baseline_evidence/v0_1_3/source_contract"
        for name in (
            "espressoWholePullFoam.C",
            "espresso_reference_math.py",
            "reference_R0.json",
            "fixture_layered_pressure.json",
            "Make.files",
            "Make.options",
        ):
            self.assertTrue((baseline / name).is_file(), name)

    def test_explicit_bounded_state_contract_is_declared(self) -> None:
        bounded = REFERENCE["verification"]["bounded_state"]
        self.assertEqual(
            set(bounded),
            {
                "concentration_cap_absolute_tolerance_kg_m3",
                "inventory_absolute_tolerance_kg",
                "retained_water_absolute_tolerance_kg",
                "monotonic_mass_absolute_tolerance_kg",
            },
        )
        postprocess = (ROOT / "scripts/postprocess.py").read_text(encoding="utf-8")
        for name in (
            "concentration_below_declared_capacity",
            "remaining_extractable_inventory_bounded",
            "retained_water_bounded_by_pore_capacity",
            "cumulative_inlet_water_monotonic",
            "cumulative_cup_water_monotonic",
            "cumulative_cup_solute_monotonic",
        ):
            self.assertIn(name, postprocess)

    def test_required_initial_fields_exist_for_both_cases(self) -> None:
        for relative in (
            "cases/reference_R0_20g_58mm_9bar/0.orig",
            "cases/fixture_layered_pressure_v0_1_4/0.orig",
        ):
            zero = ROOT / relative
            for name in (
                "p",
                "U",
                "saturation",
                "wetMask",
                "porosity",
                "permeability",
                "dissolvedConcentration",
                "remainingExtractable",
                "localExtractionRate",
            ):
                self.assertTrue((zero / name).is_file(), f"{relative}/{name}")

    def test_solver_uses_foundation12_explicit_headers(self) -> None:
        cpp = (ROOT / "solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text(encoding="utf-8")
        self.assertNotIn('#include "fvCFD.H"', cpp)
        for header in (
            "argList.H",
            "volFields.H",
            "surfaceFields.H",
            "fvMatrices.H",
            "fvcFlux.H",
            "fvcGrad.H",
            "fvmDdt.H",
            "fvmDiv.H",
            "fvmLaplacian.H",
        ):
            self.assertIn(f'#include "{header}"', cpp)

    def test_solver_contains_hardening_corrections(self) -> None:
        cpp = (ROOT / "solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text(encoding="utf-8")
        self.assertIn("2.0*constant::mathematical::pi/std::sin(wedgeAngleRadians)", cpp)
        self.assertNotIn("360.0/wedgeAngleDegrees", cpp)
        self.assertIn("positiveDrivingPressureIntegral", cpp)
        self.assertIn("pressureIntegralCrossingTime", cpp)
        self.assertIn("axial_two_layer", cpp)
        self.assertIn("pressureProbe1", cpp)

    def test_generated_control_dict_disables_binary_compression(self) -> None:
        text = render_control_dict(REFERENCE)
        self.assertIn("writeFormat     binary;", text)
        self.assertIn("writeCompression off;", text)
        self.assertNotIn("writeCompression on;", text)

    def test_allrun_has_live_logging_fixture_and_timings(self) -> None:
        text = (ROOT / "Allrun").read_text(encoding="utf-8")
        for token in (
            "2>&1 | tee",
            "stage_timings_v0_1_4.tsv",
            "SOLVER_EXECUTABLE",
            'run_case_command "$FIXTURE_CASE" "$SOLVER_EXECUTABLE"',
            'run_case_command "$REFERENCE_CASE" "$SOLVER_EXECUTABLE"',
            "fixture_run_solver",
            "postprocess_layered_fixture.py",
            "ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json",
        ):
            self.assertIn(token, text)

    def test_allverify_declares_full_matrix(self) -> None:
        text = (ROOT / "scripts/run_qualification.py").read_text(encoding="utf-8")
        for token in (
            "--solver-executable",
            "solver_executable_bytes",
            "solver_executable_sha256",
            "dt_0p020_ref_r32",
            "dt_0p010_ref_r32",
            "dt_0p005_ref_r32",
            "mesh_128x256_dt0p010_r16",
            "mesh_512x1024_dt0p010_r64",
            "rank_1_ref_dt0p010",
            "rank_16_ref_dt0p010",
            "rank_64_ref_dt0p010",
            "layered_rank_1",
            "layered_rank_16",
        ):
            self.assertIn(token, text)

    def test_standard_allverify_reuses_build_and_finalizes_terminal_manifest(self) -> None:
        text = (ROOT / "Allverify").read_text(encoding="utf-8")
        self.assertIn("verify_reference_solver_build", text)
        self.assertIn("verify_build_provenance.py", text)
        self.assertIn("SOLVER_EXECUTABLE", text)
        self.assertIn("--solver-executable", text)
        self.assertIn("recorded solver executable path is not absolute", text)
        self.assertIn("finalize_reference_freeze.py", text)
        self.assertIn("postqualification_no_physics_change_verification", text)
        self.assertIn("generate_freeze_manifest.py", text)
        self.assertIn("verify_terminal_freeze_manifest", text)
        self.assertLess(
            text.index("finalize_reference_freeze.py"),
            text.index("generate_freeze_manifest.py"),
        )

    def test_source_manifest_excludes_all_qualification_runtime_products(self) -> None:
        for relative in (
            "qualification/ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json",
            "qualification/NO_PHYSICS_CHANGE_VERIFICATION_STANDARD_V0_1_4.json",
            "qualification/BUILD_PROVENANCE_SMOKE_V0_1_4.json",
            "qualification/log.qualification.standard",
            "qualification_runs/standard/sample/case/result.json",
        ):
            self.assertTrue(excluded(Path(relative)), relative)

    def test_source_manifest_is_acyclic_by_construction(self) -> None:
        text = (ROOT / "scripts/prepare_case.py").read_text(encoding="utf-8")
        self.assertIn('"manifest_role": "immutable_scientific_inputs_only"', text)
        self.assertIn('"downstream_artifacts_intentionally_excluded"', text)
        self.assertNotIn('manifest["outputs"]', text)

    def test_allwmake_uses_foam_src_and_normalizes_timestamps(self) -> None:
        text = (ROOT / "Allwmake").read_text(encoding="utf-8")
        self.assertIn('FOAM_SOURCE_ROOT="${FOAM_SRC:-${WM_PROJECT_DIR}/src}"', text)
        self.assertIn("normalize_timestamps.py", text)
        self.assertIn("wclean", text)
        self.assertIn("write_build_provenance.py", text)
        self.assertNotIn("${LIB_SRC}", text)


class ScriptIntegrationTests(unittest.TestCase):
    def test_prepare_case_writes_hardened_properties(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "case"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/prepare_case.py"),
                    "--root",
                    str(ROOT),
                    "--nprocs",
                    "7",
                    "--config",
                    str(ROOT / "config/reference_R0.json"),
                    "--case-dir",
                    str(case),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            properties = (case / "constant/espressoModelProperties").read_text(encoding="utf-8")
            self.assertIn("pressureIntegrationMethod  exactPiecewiseLinearIntegral;", properties)
            self.assertIn("permeabilityProfile        uniform;", properties)
            self.assertIn("pressureProbe1Position", properties)
            control = (case / "system/controlDict").read_text(encoding="utf-8")
            self.assertIn("writeCompression off;", control)
            decompose = (case / "system/decomposeParDict").read_text(encoding="utf-8")
            self.assertIn("numberOfSubdomains 7;", decompose)
            self.assertTrue((case / "preflight/B0_REDUCED_TWIN_V0_1_4.json").is_file())
            manifest = json.loads(
                (case / "ESPRESSO_WHOLE_PULL_REFERENCE_CASE_MANIFEST_V0_1_4.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["manifest_role"], "immutable_scientific_inputs_only")
            self.assertNotIn("outputs", manifest)
            self.assertIn("scientific_bundle_sha256", manifest)

    def test_timestamp_normalizer_repairs_future_solver_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "solver/espressoWholePullFoam/espressoWholePullFoam.C"
            source.parent.mkdir(parents=True)
            source.write_text("int main(){}\n", encoding="utf-8")
            make_file = source.parent / "Make/files"
            make_file.parent.mkdir(parents=True)
            make_file.write_text("x\n", encoding="utf-8")
            future = time.time() + 3600.0
            os.utime(source, (future, future))
            output = root / "report.json"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize_timestamps.py"),
                    "--root",
                    str(root),
                    "--output",
                    str(output),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["normalized_file_count"], 1)
            self.assertLessEqual(source.stat().st_mtime, time.time() + 5.0)

    def test_no_physics_change_verification_passes_against_v013_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "no_physics.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/verify_no_physics_change.py"),
                    "--root",
                    str(ROOT),
                    "--output",
                    str(output),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertIs(report["governing_physics_change"], False)
            self.assertGreaterEqual(report["comparison_summary"]["total"], 28)

    def test_allwmake_mock_environment(self) -> None:
        headers = (
            "argList.H",
            "Time.H",
            "fvMesh.H",
            "volFields.H",
            "surfaceFields.H",
            "IOdictionary.H",
            "fixedValueFvPatchFields.H",
            "zeroGradientFvPatchFields.H",
            "fvMatrices.H",
            "fvcFlux.H",
            "fvcGrad.H",
            "fvmDdt.H",
            "fvmDiv.H",
            "fvmLaplacian.H",
            "PstreamReduceOps.H",
            "mathematicalConstants.H",
            "OSspecific.H",
            "setRootCase.H",
            "createTime.H",
            "createMesh.H",
        )
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            project = temp / "OpenFOAM-12"
            include = project / "src/OpenFOAM/lnInclude"
            include.mkdir(parents=True)
            (project / "src/finiteVolume/lnInclude").mkdir(parents=True)
            (project / "src/meshTools/lnInclude").mkdir(parents=True)
            os_specific = project / "src/OSspecific/POSIX/lnInclude"
            os_specific.mkdir(parents=True)
            for header in headers:
                target = os_specific if header == "OSspecific.H" else include
                (target / header).touch()

            appbin = temp / "user-bin"
            fakebin = temp / "fake-bin"
            fakebin.mkdir()
            (fakebin / "wclean").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (fakebin / "wmake").write_text(
                "#!/usr/bin/env bash\n"
                "set -e\n"
                "mkdir -p \"$FOAM_USER_APPBIN\"\n"
                "printf '#!/usr/bin/env bash\\nexit 0\\n' > \"$FOAM_USER_APPBIN/espressoWholePullFoam\"\n"
                "chmod +x \"$FOAM_USER_APPBIN/espressoWholePullFoam\"\n",
                encoding="utf-8",
            )
            (fakebin / "wclean").chmod(0o755)
            (fakebin / "wmake").chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{fakebin}:/usr/bin:/bin",
                    "WM_PROJECT": "OpenFOAM",
                    "WM_PROJECT_VERSION": "12",
                    "WM_PROJECT_DIR": str(project),
                    "FOAM_USER_APPBIN": str(appbin),
                    "BUILD_PROVENANCE_OUTPUT": str(temp / "build-provenance.json"),
                    "ARCHIVED_EXECUTABLE_OUTPUT": str(temp / "archived-espressoWholePullFoam"),
                    "TIMESTAMP_NORMALIZATION_OUTPUT": str(temp / "timestamp-normalization.json"),
                }
            )
            for name in ("FOAM_SRC", "LIB_SRC", "OPENFOAM_BASHRC"):
                env.pop(name, None)
            result = subprocess.run(
                [str(ROOT / "Allwmake")],
                cwd=str(ROOT),
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("Foundation 12 explicit-header preflight: PASS", result.stdout)
            self.assertTrue((appbin / "espressoWholePullFoam").is_file())
            self.assertTrue((temp / "archived-espressoWholePullFoam").is_file())

    def _status_report(self, log_text: str) -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            case = root / "cases/reference_R0_20g_58mm_9bar"
            case.mkdir(parents=True)
            log = case / "log.test"
            log.write_text(log_text, encoding="utf-8")
            timings = case / "stage_timings_v0_1_4.tsv"
            timings.write_text(
                "stage\tstart_utc\tend_utc\tduration_s\tstatus\texit_code\tlog\n"
                "test\tA\tB\t1.25\tFAIL\t1\tcases/reference/log.test\n",
                encoding="utf-8",
            )
            output = case / "status.json"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/write_run_status.py"),
                    "--root",
                    str(root),
                    "--status",
                    "FAIL",
                    "--stage",
                    "test",
                    "--exit-code",
                    "1",
                    "--current-log",
                    str(log),
                    "--timings",
                    str(timings),
                    "--output",
                    str(output),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            return json.loads(output.read_text(encoding="utf-8"))

    def test_status_treats_foam_sigfpe_enablement_as_information(self) -> None:
        report = self._status_report(
            "sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).\n"
        )
        self.assertEqual(report["diagnostics"]["detected_issue_count"], 0)
        self.assertEqual(report["diagnostics"]["informational_safeguard_count"], 1)

    def test_status_treats_successful_relative_error_metric_as_information(self) -> None:
        report = self._status_report("Mesh-volume relative error: 5.692061406e-15\n")
        self.assertEqual(report["diagnostics"]["detected_issue_count"], 0)
        self.assertEqual(report["diagnostics"]["informational_metric_count"], 1)

    def test_status_still_detects_real_floating_point_exception(self) -> None:
        report = self._status_report("Floating point exception (core dumped)\n")
        self.assertEqual(report["diagnostics"]["detected_issue_count"], 1)

    def test_status_detects_compiler_and_shell_failures(self) -> None:
        report = self._status_report(
            "espressoWholePullFoam.C:15:10: fatal error: missing.H: No such file or directory\n"
            "Allwmake: line 10: LIB_SRC: unbound variable\n"
        )
        issues = report["diagnostics"]["detected_issue_lines"]
        self.assertTrue(any("fatal error" in item["line"] for item in issues))
        self.assertTrue(any("unbound variable" in item["line"] for item in issues))

    def test_status_parses_stage_timing(self) -> None:
        report = self._status_report("ERROR: synthetic\n")
        stages = report["runtime"]["stage_timings"]["stages"]
        self.assertEqual(len(stages), 1)
        self.assertAlmostEqual(stages[0]["duration_s"], 1.25)

    def test_build_provenance_verifier_accepts_exact_reference_binary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            case_preflight = root / "cases/reference_R0_20g_58mm_9bar/preflight"
            case_preflight.mkdir(parents=True)
            build_inputs = []
            for relative, content in (
                ("solver/espressoWholePullFoam/espressoWholePullFoam.C", "source\n"),
                ("solver/espressoWholePullFoam/Make/files", "files\n"),
                ("solver/espressoWholePullFoam/Make/options", "options\n"),
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                import hashlib
                build_inputs.append(
                    {
                        "path": relative,
                        "bytes": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                )
            executable = root / "bin/espressoWholePullFoam"
            executable.parent.mkdir()
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o755)
            import hashlib
            archived = case_preflight / "espressoWholePullFoam_v0_1_4"
            archived.write_bytes(executable.read_bytes())
            archived.chmod(0o755)
            runtime_record = {
                "path": str(executable),
                "bytes": executable.stat().st_size,
                "sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                "executable": True,
            }
            archived_record = {
                "path": str(archived.relative_to(root)),
                "bytes": archived.stat().st_size,
                "sha256": hashlib.sha256(archived.read_bytes()).hexdigest(),
                "executable": True,
            }
            provenance = {
                "status": "PASS",
                "generated_at_utc": "synthetic",
                "environment": {
                    "WM_PROJECT": "OpenFOAM",
                    "WM_PROJECT_VERSION": "12",
                    "WM_OPTIONS": "linux64GccDPInt32Opt",
                },
                "build_inputs": build_inputs,
                "executable": runtime_record,
                "runtime_executable": runtime_record,
                "archived_executable": archived_record,
                "runtime_archive_identity": {"status": "PASS", "same_bytes": True},
                "source_and_executable_bundle_sha256": "synthetic",
            }
            provenance_path = case_preflight / "BUILD_PROVENANCE_V0_1_4.json"
            provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
            output = case_preflight / "verification.json"
            env = os.environ.copy()
            env.update(provenance["environment"])
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/verify_build_provenance.py"),
                    "--root",
                    str(root),
                    "--output",
                    str(output),
                ],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(report["build_input_hashes_match"])
            self.assertTrue(report["executable_hash_matches"])
            self.assertTrue(report["archived_executable_hash_matches"])
            self.assertTrue(report["runtime_archive_identity_matches"])

    def test_synthetic_freeze_finalization_is_acyclic_and_self_verifying(self) -> None:
        import hashlib

        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as runtime_td:
            root = Path(td)
            case = root / "cases/reference_R0_20g_58mm_9bar"
            fixture = root / "cases/fixture_layered_pressure_v0_1_4"
            qualification = root / "qualification"
            preflight = case / "preflight"
            preflight.mkdir(parents=True)
            fixture.mkdir(parents=True)
            qualification.mkdir(parents=True)

            def write_json(path: Path, value: dict) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

            def identity(path: Path) -> dict:
                return {
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }

            empty_aggregate = hashlib.sha256(b"").hexdigest()
            write_json(root / "SOURCE_PACKAGE_MANIFEST.json", {
                "aggregate_source_sha256": empty_aggregate,
                "file_count": 0,
                "files": {},
            })
            executable = Path(runtime_td) / "espressoWholePullFoam"
            executable.parent.mkdir(parents=True, exist_ok=True)
            executable.write_text("binary", encoding="utf-8")
            executable.chmod(0o755)
            archived_executable = preflight / "espressoWholePullFoam_v0_1_4"
            archived_executable.write_bytes(executable.read_bytes())
            archived_executable.chmod(0o755)
            runtime_record = {"path": str(executable), **identity(executable), "executable": True}
            archived_record = {
                "path": str(archived_executable.relative_to(root)),
                **identity(archived_executable),
                "executable": True,
            }
            write_json(preflight / "BUILD_PROVENANCE_V0_1_4.json", {
                "status": "PASS",
                "source_and_executable_bundle_sha256": "bundle",
                "executable": runtime_record,
                "runtime_executable": runtime_record,
                "archived_executable": archived_record,
                "runtime_archive_identity": {"status": "PASS", "same_bytes": True},
            })
            write_json(preflight / "BUILD_PROVENANCE_VERIFICATION_V0_1_4.json", {
                "status": "PASS",
                "build_input_hashes_match": True,
                "executable_hash_matches": True,
                "archived_executable_hash_matches": True,
                "runtime_archive_identity_matches": True,
                "openfoam_build_environment_matches": True,
            })
            write_json(preflight / "TIMESTAMP_NORMALIZATION_V0_1_4.json", {"status": "PASS"})
            write_json(preflight / "NO_PHYSICS_CHANGE_VERIFICATION_V0_1_4.json", {
                "status": "PASS", "governing_physics_change": False
            })
            write_json(qualification / "NO_PHYSICS_CHANGE_VERIFICATION_STANDARD_V0_1_4.json", {
                "status": "PASS", "governing_physics_change": False
            })
            write_json(case / "CASE_SCENARIO_V0_1_4.json", {"scenario_id": "reference"})
            write_json(case / "RUN_ENVIRONMENT_V0_1_4.json", {"wm_project_version": "12"})
            scientific_manifest = case / "ESPRESSO_WHOLE_PULL_REFERENCE_CASE_MANIFEST_V0_1_4.json"
            write_json(scientific_manifest, {
                "manifest_role": "immutable_scientific_inputs_only",
                "scientific_input_sha256": {},
                "scientific_bundle_sha256": empty_aggregate,
                "prepared_at_utc": "prepared",
            })
            write_json(case / "ESPRESSO_WHOLE_PULL_STAGE_TIMINGS_V0_1_4.json", {"stage_count": 1})
            write_json(case / "ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json", {
                "status": "PASS",
                "execution_status": "COMPLETED",
                "artifacts": {},
            })
            trace = case / "ESPRESSO_WHOLE_PULL_REFERENCE_TRACES_V0_1_4.csv"
            trace.write_text("time_s\n0\n", encoding="utf-8")
            field_index = case / "ESPRESSO_WHOLE_PULL_REFERENCE_FIELD_INDEX_V0_1_4.json"
            write_json(field_index, {
                "indexed_file_count": 0,
                "final_time_directory": "30",
                "missing_final_fields": [],
                "files": [],
            })
            foam = case / "reference_R0.foam"
            foam.touch()
            fixture_acceptance = fixture / "ESPRESSO_LAYERED_PRESSURE_FIXTURE_ACCEPTANCE_V0_1_4.json"
            write_json(fixture_acceptance, {"status": "PASS"})
            qualification_runs = {}
            for index in range(10):
                run_id = f"synthetic_{index}"
                run_acceptance = root / f"qualification_runs/{run_id}/case/acceptance.json"
                write_json(run_acceptance, {"status": "PASS"})
                qualification_runs[run_id] = {
                    "status": "PASS",
                    "acceptance": str(run_acceptance.relative_to(root)),
                    "acceptance_sha256": identity(run_acceptance)["sha256"],
                }
            qualification_report = qualification / "ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json"
            write_json(qualification_report, {
                "status": "PASS",
                "profile": "standard",
                "all_required_gates_pass": True,
                "gate_summary": {"pass": 9, "fail": 0, "total": 9},
                "environment": {
                    "solver_executable": str(executable.resolve()),
                    "solver_executable_bytes": executable.stat().st_size,
                    "solver_executable_sha256": identity(executable)["sha256"],
                },
                "runs": qualification_runs,
            })
            runs_csv = qualification / "ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_RUNS_V0_1_4.csv"
            runs_csv.write_text("run_id,status\nsynthetic,PASS\n", encoding="utf-8")

            artifact_paths = [trace, field_index, foam, scientific_manifest]
            gates = {
                name: {"status": "PASS"}
                for name in (
                    "concentration_below_declared_capacity",
                    "remaining_extractable_inventory_bounded",
                    "retained_water_bounded_by_pore_capacity",
                    "cumulative_inlet_water_monotonic",
                    "cumulative_cup_water_monotonic",
                    "cumulative_cup_solute_monotonic",
                )
            }
            acceptance_path = case / "ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json"
            write_json(acceptance_path, {
                "status": "PASS",
                "all_required_reference_gates_pass": True,
                "all_required_bounded_state_gates_pass": True,
                "all_required_monotonicity_gates_pass": True,
                "numerical_acceptance_gates": gates,
                "reference_freeze_status": "NOT_FROZEN",
                "primary_outputs": {},
                "calibration_and_validation": {"physical_validation_status": "NOT_ESTABLISHED"},
                "artifacts": {
                    str(path.relative_to(case)): {**identity(path)} for path in artifact_paths
                },
            })

            finalize = subprocess.run(
                [sys.executable, str(ROOT / "scripts/finalize_reference_freeze.py"), "--root", str(root)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            self.assertEqual(finalize.returncode, 0, finalize.stdout)
            finalized = json.loads(acceptance_path.read_text(encoding="utf-8"))
            self.assertEqual(finalized["reference_freeze_status"], "QUALIFIED")

            freeze = subprocess.run(
                [sys.executable, str(ROOT / "scripts/generate_freeze_manifest.py"), "--root", str(root)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            self.assertEqual(freeze.returncode, 0, freeze.stdout)
            freeze_path = case / "ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json"
            frozen = json.loads(freeze_path.read_text(encoding="utf-8"))
            self.assertEqual(frozen["reference_freeze_status"], "FROZEN / QUALIFIED")
            self.assertEqual(frozen["artifact_verification"]["status"], "PASS")
            self.assertNotIn("ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json", {
                item["path"] for item in frozen["artifacts"]
            })
            before_verification = identity(freeze_path)
            verify = subprocess.run(
                [sys.executable, str(ROOT / "scripts/verify_freeze_manifest.py"), "--root", str(root)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            self.assertEqual(verify.returncode, 0, verify.stdout)
            self.assertEqual(identity(freeze_path), before_verification)

    def test_qualification_csv_ignores_non_tabular_diagnostic_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "runs.csv"
            primary = {key: 1.0 for key in PRIMARY_KEYS}
            primary["max_pressure_iterations"] = 4.0
            primary["mesh_volume_relative_error"] = 0.0
            results = {
                "sample": {
                    "run_id": "sample",
                    "kind": "reference",
                    "axial_cells": 64,
                    "radial_cells": 128,
                    "delta_t_s": 0.02,
                    "ranks": 1,
                    "status": "PASS",
                    "total_stage_duration_s": 1.0,
                    "primary_outputs": primary,
                }
            }
            write_runs_csv(output, results)
            with output.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["run_id"], "sample")
            self.assertNotIn("max_pressure_iterations", rows[0])
            self.assertNotIn("mesh_volume_relative_error", rows[0])

    def test_standard_qualification_aggregator_accepts_equivalent_matrix(self) -> None:
        reference_outputs = {key: 1.0 for key in PRIMARY_KEYS}
        reference_outputs["first_drip_s"] = 4.711696185231869
        layered_outputs = {
            "outlet_flow_m3_s": 1.0e-6,
            "pressure_probe_1_Pa": 500000.0,
            "pressure_probe_2_Pa": 100000.0,
        }
        results = {}
        for run_id in (
            "dt_0p020_ref_r32",
            "dt_0p010_ref_r32",
            "dt_0p005_ref_r32",
            "mesh_128x256_dt0p010_r16",
            "mesh_512x1024_dt0p010_r64",
            "rank_1_ref_dt0p010",
            "rank_16_ref_dt0p010",
            "rank_64_ref_dt0p010",
        ):
            results[run_id] = {"status": "PASS", "primary_outputs": dict(reference_outputs)}
        results["layered_rank_1"] = {
            "status": "PASS",
            "primary_outputs": dict(layered_outputs),
        }
        results["layered_rank_16"] = {
            "status": "PASS",
            "primary_outputs": dict(layered_outputs),
        }
        gates = aggregate_standard(results)
        self.assertTrue(gates)
        self.assertTrue(all(item["status"] == "PASS" for item in gates.values()))


if __name__ == "__main__":
    unittest.main()
