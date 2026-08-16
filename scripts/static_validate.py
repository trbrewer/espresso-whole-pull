#!/usr/bin/env python3
"""Static gates for the active package while preserving frozen baseline checks."""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from espresso_reference_math import (  # noqa: E402
    analytical_preview,
    first_drip_time_s,
    straight_sided_wedge_scale,
)
from prepare_case import render_control_dict  # noqa: E402
from verify_val001_correction import verify as verify_val001_correction  # noqa: E402
from verify_val001_hardening import verify as verify_val001_hardening  # noqa: E402
from verify_val001_deep_schema_coverage import verify as verify_val001_deep_schema_coverage  # noqa: E402
from tools.validation.val001.administrative import verify_closure as verify_val001_administrative_closure  # noqa: E402

PACKAGE_VERSION = "0.2.0"
FROZEN_SCENARIO_VERSION = "0.1.4"


def gate(status: bool, **details: object) -> Dict[str, object]:
    return {"status": "PASS" if status else "FAIL", **details}


def balanced_cpp(text: str) -> bool:
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack: List[str] = []
    in_string = None
    in_line_comment = False
    in_block_comment = False
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if in_line_comment:
            if char == "\n":
                in_line_comment = False
        elif in_block_comment:
            if char == "*" and nxt == "/":
                in_block_comment = False
                index += 1
        elif in_string is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = None
        else:
            if char == "/" and nxt == "/":
                in_line_comment = True
                index += 1
            elif char == "/" and nxt == "*":
                in_block_comment = True
                index += 1
            elif char in ('"', "'"):
                in_string = char
            elif char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack or pairs[stack.pop()] != char:
                    return False
        index += 1
    return not stack and in_string is None and not in_block_comment


def all_tokens(text: str, tokens: Iterable[str]) -> bool:
    return all(token in text for token in tokens)


def path_has_symlink_parent(path: Path) -> bool:
    """Inspect caller spelling before resolve; reject every symlink ancestor."""
    if not path.is_absolute():
        raise ValueError("path must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:-1]:
        current = current / component
        if current.is_symlink():
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        help="optional absolute report path outside the repository; default is stdout only",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    output = None
    if args.output is not None:
        if not args.output.is_absolute():
            parser.error("--output must be an absolute path")
        if path_has_symlink_parent(args.output):
            parser.error("--output parent path must not contain a symlink")
        output = args.output.resolve(strict=False)
        if output == root or root in output.parents:
            parser.error("--output must be outside the repository")
        parent = output.parent
        if not parent.is_dir() or parent.is_symlink():
            parser.error("--output parent must be an existing non-symlink directory")
    case = root / "cases/reference_R0_20g_58mm_9bar"
    fixture_case = root / "cases/fixture_layered_pressure_v0_1_4"
    scenario = json.loads((root / "config/reference_R0.json").read_text(encoding="utf-8"))
    fixture = json.loads((root / "config/fixture_layered_pressure.json").read_text(encoding="utf-8"))
    gates: Dict[str, Dict[str, object]] = {}

    fields = (
        "p",
        "U",
        "saturation",
        "wetMask",
        "porosity",
        "permeability",
        "dissolvedConcentration",
        "remainingExtractable",
        "localExtractionRate",
    )
    required = [
        "Allrun",
        "Allclean",
        "Allwmake",
        "Allverify",
        "VERSION",
        "README.md",
        "SOURCE_PACKAGE_MANIFEST.json",
        "solver/espressoWholePullFoam/espressoWholePullFoam.C",
        "solver/espressoWholePullFoam/Make/files",
        "solver/espressoWholePullFoam/Make/options",
        "config/reference_R0.json",
        "config/fixture_layered_pressure.json",
        "scripts/artifact_utils.py",
        "scripts/espresso_reference_math.py",
        "scripts/freeze_contract.py",
        "scripts/finalize_reference_freeze.py",
        "scripts/generate_freeze_manifest.py",
        "scripts/generate_source_manifest.py",
        "scripts/normalize_timestamps.py",
        "scripts/postprocess.py",
        "scripts/postprocess_layered_fixture.py",
        "scripts/prepare_case.py",
        "scripts/run_qualification.py",
        "scripts/static_validate.py",
        "scripts/verify_freeze_manifest.py",
        "scripts/verify_no_physics_change.py",
        "scripts/verify_change_contract.py",
        "scripts/verify_governing_physics_change.py",
        "scripts/verify_release_finalization.py",
        "scripts/verify_v0_1_4_baseline_integrity.py",
        "scripts/verify_source_manifest.py",
        "scripts/write_build_provenance.py",
        "scripts/write_run_status.py",
        "scripts/lib/openfoam_env.sh",
        "baseline_evidence/v0_1_3/source_contract/espressoWholePullFoam.C",
        "baseline_evidence/v0_1_3/source_contract/espresso_reference_math.py",
        "baseline_evidence/v0_1_3/source_contract/reference_R0.json",
        "baseline_evidence/v0_1_3/source_contract/fixture_layered_pressure.json",
        "baseline_evidence/v0_1_3/ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_3.json",
        "docs/source_strategy/espresso_puck_modeling_and_simulation_strategy_v1_2.md",
        "cases/reference_R0_20g_58mm_9bar/system/fvSchemes",
        "cases/reference_R0_20g_58mm_9bar/system/fvSolution",
        "cases/fixture_layered_pressure_v0_1_4/system/fvSchemes",
        "cases/fixture_layered_pressure_v0_1_4/system/fvSolution",
    ]
    required.extend(
        f"cases/reference_R0_20g_58mm_9bar/0.orig/{name}" for name in fields
    )
    required.extend(
        f"cases/fixture_layered_pressure_v0_1_4/0.orig/{name}" for name in fields
    )
    missing = [relative for relative in required if not (root / relative).is_file()]
    gates["required_files_present"] = gate(not missing, missing=missing)

    executable_files = [
        "Allrun",
        "Allclean",
        "Allwmake",
        "Allverify",
        "scripts/clean_case.sh",
        "scripts/lib/openfoam_env.sh",
        *[
            str(path.relative_to(root))
            for path in sorted((root / "scripts").glob("*.py"))
        ],
    ]
    not_executable = [
        relative for relative in executable_files if not os.access(root / relative, os.X_OK)
    ]
    gates["entry_points_executable"] = gate(
        not not_executable, not_executable=not_executable
    )

    version_file = (root / "VERSION").read_text(encoding="utf-8").strip()
    cpp = (root / "solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text(
        encoding="utf-8"
    )
    version_ok = (
        version_file == PACKAGE_VERSION
        and scenario.get("solver_version") == FROZEN_SCENARIO_VERSION
        and fixture.get("solver_version") == FROZEN_SCENARIO_VERSION
        and "espressoWholePullFoam v0.2.0" in cpp
    )
    gates["version_identity_consistent"] = gate(
        version_ok,
        version_file=version_file,
        reference_solver_version=scenario.get("solver_version"),
        fixture_solver_version=fixture.get("solver_version"),
    )

    bed = scenario["coffee_bed"]
    geometry = scenario["geometry"]
    derived_depth = float(bed["dry_dose_kg"]) / (
        float(bed["particle_solid_density_kg_m3"])
        * (1.0 - float(bed["initial_porosity"]))
        * math.pi
        * float(geometry["basket_radius_m"]) ** 2
    )
    configured_depth = float(bed["bed_depth_m"])
    depth_error = abs(derived_depth - configured_depth) / max(abs(derived_depth), 1e-30)
    gates["bed_depth_derived_from_dose_density_porosity"] = gate(
        depth_error < 1.0e-12,
        derived_m=derived_depth,
        configured_m=configured_depth,
        relative_difference=depth_error,
    )

    bounded = (
        0.0 < float(bed["initial_porosity"]) < 1.0
        and float(scenario["hydraulics"]["saturated_permeability_m2"]) > 0.0
        and float(scenario["time"]["delta_t_s"]) > 0.0
        and int(geometry["azimuthal_cells"]) == 1
        and 0.0 < float(geometry["wedge_angle_deg"]) <= 5.0
    )
    gates["bounded_reference_inputs"] = gate(bounded)

    target_ok = all(
        item.get("openfoam_distribution") == "OpenFOAM Foundation"
        and str(item.get("openfoam_version")) == "12"
        for item in (scenario, fixture)
    )
    gates["openfoam_foundation_12_target_frozen"] = gate(
        target_ok, distribution="OpenFOAM Foundation", version="12"
    )

    total_cells = (
        int(geometry["axial_cells"])
        * int(geometry["radial_cells"])
        * int(geometry["azimuthal_cells"])
    )
    default_ranks = int(scenario["parallel"]["default_subdomains"])
    cells_per_rank = total_cells / default_ranks
    gates["qualified_32_rank_routine_default"] = gate(
        default_ranks == 32 and cells_per_rank >= 1000.0,
        total_cells=total_cells,
        default_subdomains=default_ranks,
        cells_per_default_rank=cells_per_rank,
        override="NPROCS remains supported",
    )

    analytical = analytical_preview(scenario)
    first_drip = first_drip_time_s(scenario)
    scale = straight_sided_wedge_scale(geometry["wedge_angle_deg"])
    gates["analytical_reference_values_frozen"] = gate(
        abs(first_drip - 4.71169618523187) <= 1.0e-12
        and abs(scale - 72.09146648398465) <= 1.0e-12
        and analytical["steady_outlet_volume_flow_m3_s"] > 0.0,
        first_drip_s=first_drip,
        straight_sided_wedge_scale=scale,
        steady_outlet_flow_m3_s=analytical["steady_outlet_volume_flow_m3_s"],
    )

    texts = {
        "allrun": (root / "Allrun").read_text(encoding="utf-8"),
        "allclean": (root / "Allclean").read_text(encoding="utf-8"),
        "allwmake": (root / "Allwmake").read_text(encoding="utf-8"),
        "allverify": (root / "Allverify").read_text(encoding="utf-8"),
        "prepare": (root / "scripts/prepare_case.py").read_text(encoding="utf-8"),
        "postprocess": (root / "scripts/postprocess.py").read_text(encoding="utf-8"),
        "math": (root / "scripts/espresso_reference_math.py").read_text(
            encoding="utf-8"
        ),
        "status": (root / "scripts/write_run_status.py").read_text(encoding="utf-8"),
        "normalize": (root / "scripts/normalize_timestamps.py").read_text(
            encoding="utf-8"
        ),
        "qualification": (root / "scripts/run_qualification.py").read_text(
            encoding="utf-8"
        ),
        "finalizer": (root / "scripts/finalize_reference_freeze.py").read_text(
            encoding="utf-8"
        ),
        "freeze": (root / "scripts/generate_freeze_manifest.py").read_text(
            encoding="utf-8"
        ),
        "freeze_contract": (root / "scripts/freeze_contract.py").read_text(
            encoding="utf-8"
        ),
        "freeze_verify": (root / "scripts/verify_freeze_manifest.py").read_text(
            encoding="utf-8"
        ),
        "build_verify": (root / "scripts/verify_build_provenance.py").read_text(
            encoding="utf-8"
        ),
        "no_physics": (root / "scripts/verify_no_physics_change.py").read_text(
            encoding="utf-8"
        ),
        "openfoam_env": (root / "scripts/lib/openfoam_env.sh").read_text(
            encoding="utf-8"
        ),
    }

    source_root_ok = all_tokens(
        texts["allwmake"],
        (
            'FOAM_SOURCE_ROOT="${FOAM_SRC:-${WM_PROJECT_DIR}/src}"',
            'FINITE_VOLUME_INCLUDE="$FOAM_SOURCE_ROOT/finiteVolume/lnInclude"',
            'MESH_TOOLS_INCLUDE="$FOAM_SOURCE_ROOT/meshTools/lnInclude"',
            'OS_SPECIFIC_INCLUDE="$FOAM_SOURCE_ROOT/OSspecific/POSIX/lnInclude"',
        ),
    ) and "${LIB_SRC}" not in texts["allwmake"] and all_tokens(
        texts["openfoam_env"],
        ('export FOAM_SRC="${FOAM_SRC:-${WM_PROJECT_DIR}/src}"', "set +u", "set -u"),
    )
    gates["foundation12_shell_source_root_portability"] = gate(source_root_ok)

    required_headers = (
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
    missing_headers = [header for header in required_headers if f'#include "{header}"' not in cpp]
    gates["foundation12_explicit_solver_headers"] = gate(
        not missing_headers and '#include "fvCFD.H"' not in cpp,
        missing_headers=missing_headers,
        obsolete_fvCFD_header_present='#include "fvCFD.H"' in cpp,
    )

    gates["exact_straight_sided_wedge_scaling"] = gate(
        all_tokens(
            cpp,
            (
                "2.0*constant::mathematical::pi/std::sin(wedgeAngleRadians)",
                "nominalCylinderVolume",
                "meshVolumeRelativeError",
                "Straight-sided wedge volume equivalence failed",
            ),
        )
        and "360.0/wedgeAngleDegrees" not in cpp,
        expected_scale=scale,
    )
    gates["exact_pressure_ramp_integration"] = gate(
        all_tokens(
            cpp,
            (
                "positiveDrivingPressureIntegral",
                "pressureIntegralCrossingTime",
                "wettingPressureIntegral",
                "exactPiecewiseLinearIntegral",
            ),
        )
        and all_tokens(
            texts["math"],
            ("positive_driving_pressure_integral", "first_drip_time_s"),
        )
    )

    control = render_control_dict(scenario)
    gates["foundation12_binary_output_without_ineffective_compression"] = gate(
        "writeFormat     binary;" in control
        and "writeCompression off;" in control
        and scenario["output"]["write_compression"] is False
    )
    gates["automatic_future_timestamp_normalization"] = gate(
        all_tokens(texts["allwmake"], ("normalize_timestamps.py", "wclean", "wmake"))
        and all_tokens(
            texts["normalize"],
            ("future_tolerance_s", "normalized_file_count", "os.utime"),
        )
    )
    gates["live_stage_logging_and_wall_clock_timings"] = gate(
        all_tokens(
            texts["allrun"],
            (
                "2>&1 | tee",
                "stage_timings_v0_1_4.tsv",
                "record_timing",
                "ESPRESSO_WHOLE_PULL_STAGE_TIMINGS_V0_1_4.json",
            ),
        )
    )

    gates["successful_relative_error_metrics_not_issues"] = gate(
        all_tokens(
            texts["status"],
            (
                "SAFEGUARD_PATTERNS",
                "BENIGN_METRIC_PATTERNS",
                "informational_metric_count",
                "informational_metric_lines",
                "FOAM_SIGFPE",
            ),
        )
    )

    fixture_ok = (
        fixture["hydraulics"]["permeability_profile"]["type"] == "axial_two_layer"
        and fixture["wetting"]["initial_saturation"] == 1.0
        and fixture["verification"]["require_nonzero_pressure_iterations"] is True
        and all_tokens(
            texts["allrun"],
            (
                "prepare_layered_pressure_fixture",
                "fixture_run_solver",
                "postprocess_layered_fixture.py",
            ),
        )
        and "discrete_layered_pressure_reference" in texts["math"]
    )
    gates["mandatory_nonuniform_pressure_fixture"] = gate(fixture_ok)

    matrix_tokens = (
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
    )
    gates["declared_allverify_qualification_matrix"] = gate(
        all_tokens(texts["qualification"], matrix_tokens)
        and all_tokens(
            texts["allverify"],
            ("run_qualification.py", "PROFILE", "verify_build_provenance.py"),
        ),
        matrix_run_count=len(matrix_tokens),
    )
    gates["independent_b0_reduced_verification_twin"] = gate(
        all_tokens(
            texts["math"],
            (
                "b0_reduced_simulation",
                "solve_tridiagonal",
                "max_liquid_balance_residual_kg",
                "max_solute_balance_residual_kg",
            ),
        )
        and "openfoam_b0_parity_gates" in texts["postprocess"]
    )

    bounded_tokens = (
        "concentration_below_declared_capacity",
        "remaining_extractable_inventory_bounded",
        "retained_water_bounded_by_pore_capacity",
        "cumulative_inlet_water_monotonic",
        "cumulative_cup_water_monotonic",
        "cumulative_cup_solute_monotonic",
        "all_required_bounded_state_gates_pass",
        "all_required_monotonicity_gates_pass",
    )
    gates["explicit_bounded_state_and_monotonicity_contract"] = gate(
        all_tokens(texts["postprocess"], bounded_tokens),
        required_gate_names=list(bounded_tokens[:6]),
    )

    acyclic_ok = all_tokens(
        texts["prepare"],
        (
            '"manifest_role": "immutable_scientific_inputs_only"',
            '"downstream_artifacts_intentionally_excluded"',
            '"scientific_bundle_sha256"',
            "acyclic_provenance_note",
        ),
    ) and 'manifest["outputs"]' not in texts["prepare"]
    gates["acyclic_scientific_input_manifest"] = gate(acyclic_ok)

    finalization_ok = (
        all_tokens(
            texts["postprocess"],
            (
                "PENDING_STANDARD_ALLVERIFY",
                "PENDING_TERMINAL_FREEZE_MANIFEST",
                '"reference_freeze_status": "NOT_FROZEN"',
            ),
        )
        and all_tokens(
            texts["allverify"],
            (
                "finalize_reference_acceptance_and_run_status",
                "generate_terminal_freeze_manifest",
                "verify_terminal_freeze_manifest",
                'if [[ "$PROFILE" == "standard" ]]',
            ),
        )
        and all_tokens(
            texts["finalizer"],
            (
                'acceptance["reference_freeze_status"] = "QUALIFIED"',
                "all_required_freeze_prerequisites_pass",
                "qualification_report",
                "run_status",
            ),
        )
        and all_tokens(
            texts["freeze"],
            (
                '"reference_freeze_status": "FROZEN / QUALIFIED"',
                '"physical_validation_status": "NOT_ESTABLISHED"',
                '"next_scientific_milestone": "WP-0.1R"',
                "controlling_artifact_aggregate_sha256",
            ),
        )
        and "read_only" in texts["freeze_verify"]
    )
    gates["standard_allverify_terminal_freeze_finalization"] = gate(
        finalization_ok,
        final_artifact="ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json",
    )

    profile_isolation = all_tokens(
        texts["allverify"],
        (
            "ESPRESSO_WHOLE_PULL_NUMERICAL_SMOKE_V0_1_4.json",
            "qualification_runs/smoke",
            "qualification_runs/standard",
            'if [[ "$PROFILE" == "standard" ]]',
        ),
    ) and all_tokens(
        texts["qualification"],
        ("SMOKE_REPORT_NAME", "STANDARD_REPORT_NAME", "--runs-root"),
    )
    gates["smoke_profile_cannot_overwrite_standard_freeze"] = gate(profile_isolation)

    no_physics_ok = all_tokens(
        texts["no_physics"],
        (
            "source_contract",
            "openfoam_solver_source",
            "reduced_verification_mathematics",
            "reference_R0_physics_configuration",
            "layered_fixture_physics_configuration",
            "governing_physics_change",
            "Make.options",
            "fvSchemes",
            "0.orig",
        ),
    ) and all_tokens(
        texts["allrun"],
        ("no_physics_change_verification", "verify_no_physics_change.py"),
    )
    gates["historical_v0_1_4_no_physics_change_contract_present"] = gate(no_physics_ok)

    active_manifest = json.loads(
        (root / "SOURCE_PACKAGE_MANIFEST.json").read_text(encoding="utf-8")
    )
    active_run = json.loads(
        (root / "validation/wp02/WP02_001_RUN_STATUS.json").read_text(encoding="utf-8")
    )
    gates["active_wp02_governing_change_metadata"] = gate(
        active_manifest.get("governing_physics_change") is True
        and active_manifest.get("package_version") == PACKAGE_VERSION
        and active_run.get("overall_wp02_001_disposition")
        == "SOURCE_LINKED_MULTIPRESSURE_RECONSTRUCTION_PASS"
        and active_run.get("physical_validation") == "NOT_ESTABLISHED"
    )
    gates["classification_aware_validation_routing"] = gate(
        (root / "scripts/verify_change_contract.py").is_file()
        and (root / "scripts/verify_governing_physics_change.py").is_file()
        and (root / "scripts/verify_v0_1_4_baseline_integrity.py").is_file()
        and (root / "scripts/verify_release_finalization.py").is_file()
    )

    build_provenance_ok = (
        all_tokens(
            texts["allwmake"],
            (
                "BUILD_PURPOSE",
                "BUILD_PROVENANCE_OUTPUT",
                "ARCHIVED_EXECUTABLE_OUTPUT",
                "TIMESTAMP_NORMALIZATION_OUTPUT",
                "write_build_provenance.py",
            ),
        )
        and all_tokens(
            texts["allrun"],
            (
                "BUILD_PROVENANCE_V0_1_4.json",
                'BUILD_PURPOSE="reference_Allrun"',
                "SOLVER_EXECUTABLE",
                'run_case_command "$FIXTURE_CASE" "$SOLVER_EXECUTABLE"',
                'run_case_command "$REFERENCE_CASE" "$SOLVER_EXECUTABLE"',
            ),
        )
        and all_tokens(
            texts["allverify"],
            (
                "REFERENCE_BUILD",
                "SOLVER_EXECUTABLE",
                "--solver-executable",
                "verify_reference_solver_build",
                "verify_build_provenance.py",
                "BUILD_PROVENANCE_VERIFICATION_SMOKE_V0_1_4.json",
            ),
        )
        and "BUILD_PROVENANCE_STANDARD_V0_1_4.json" not in texts["allverify"]
        and all_tokens(
            texts["qualification"],
            (
                "--solver-executable",
                "solver_executable",
                "solver_executable_bytes",
                "solver_executable_sha256",
            ),
        )
        and all_tokens(
            texts["freeze_contract"],
            ("verify_qualification_executable_binding", "standard_qualification"),
        )
        and all_tokens(
            texts["build_verify"],
            (
                "build_input_hashes_match",
                "executable_hash_matches",
                "archived_executable_hash_matches",
                "runtime_archive_identity_matches",
                "openfoam_build_environment_matches",
                "Standard Allverify reuses the exact runtime executable",
            ),
        )
    )
    gates["reference_executable_reused_for_standard_qualification"] = gate(
        build_provenance_ok,
        standard_behavior="verify and reuse exact Allrun executable; do not rebuild",
        smoke_behavior="verify and reuse exact Allrun executable without rewriting frozen artifacts",
    )

    solver_symbols = (
        "fvm::laplacian(hydraulicMobility, p)",
        "fvm::ddt(porosity, dissolvedConcentration)",
        "fvm::div(darcyFlux, dissolvedConcentration)",
        "remainingExtractable",
        "soluteBalanceResidual",
        "liquidBalanceResidual",
        "ESPRESSO_CASE_ROOT",
        "pressurePerformance.finalResidual()",
        "concentrationPerformance.finalResidual()",
        "pressurePerformance.nIterations()",
        "concentrationPerformance.nIterations()",
        "permeabilityProfile",
        "pressureProbe1",
        "pressureProbe2",
    )
    missing_symbols = [symbol for symbol in solver_symbols if symbol not in cpp]
    gates["solver_contains_required_hardened_spine"] = gate(
        not missing_symbols, missing_symbols=missing_symbols
    )
    gates["solver_delimiters_balanced"] = gate(balanced_cpp(cpp))

    field_details: Dict[str, bool] = {}
    fields_ok = True
    for case_dir in (case, fixture_case):
        for field in fields:
            path = case_dir / "0.orig" / field
            text = path.read_text(encoding="utf-8")
            ok = (
                "FoamFile" in text
                and "boundaryField" in text
                and text.count("{") == text.count("}")
            )
            field_details[str(path.relative_to(root))] = ok
            fields_ok = fields_ok and ok
    gates["initial_fields_structurally_valid"] = gate(fields_ok, fields=field_details)

    continuity: Dict[str, bool] = {}
    continuity_ok = True
    for name in ("porosity", "permeability", "remainingExtractable", "localExtractionRate"):
        text = (case / "0.orig" / name).read_text(encoding="utf-8")
        match = re.search(r"inlet\s*\{(?P<body>.*?)\}", text, re.S)
        ok = bool(match and "type zeroGradient;" in match.group("body"))
        continuity[name] = ok
        continuity_ok = continuity_ok and ok
    gates["material_inventory_inlet_boundaries_continuous"] = gate(
        continuity_ok, fields=continuity
    )

    python_sources = [
        path for path in (root / "scripts").rglob("*.py") if path.is_file()
    ] + [path for path in (root / "tests").rglob("*.py") if path.is_file()]
    third_party = []
    bad_write_text = []
    third_party_re = re.compile(
        r"^\s*(?:import\s+(?:numpy|pandas|scipy)\b|from\s+(?:numpy|pandas|scipy)\b)",
        re.M,
    )
    write_text_newline_re = re.compile(r"\.write_text\s*\([^)]*\bnewline\s*=", re.S)
    for path in python_sources:
        text = path.read_text(encoding="utf-8")
        if third_party_re.search(text):
            third_party.append(str(path.relative_to(root)))
        if write_text_newline_re.search(text):
            bad_write_text.append(str(path.relative_to(root)))
    gates["python_standard_library_portability"] = gate(
        not third_party and not bad_write_text,
        forbidden_third_party_imports=third_party,
        forbidden_Path_write_text_newline_arguments=bad_write_text,
        minimum_supported_python="3.8+",
    )

    runtime_paths = [
        root / "Allrun",
        root / "Allclean",
        root / "Allwmake",
        root / "Allverify",
        *python_sources,
        root / "solver/espressoWholePullFoam/espressoWholePullFoam.C",
        root / "config/reference_R0.json",
        root / "config/fixture_layered_pressure.json",
    ]
    stale_re = re.compile(
        r"(?:PACKAGE_VERSION\s*=\s*[\"']0\.1\.(?:2|3)[\"']|"
        r"RUN_STATUS_V0_1_(?:2|3)|ACCEPTANCE_V0_1_3|TRACES_V0_1_3|"
        r"run_status\.v0\.1\.(?:2|3)|static_validation\.v0\.1\.(?:2|3))"
    )
    stale_files = []
    for path in runtime_paths:
        if path in {root / "scripts/static_validate.py", root / "scripts/verify_no_physics_change.py"}:
            continue
        if stale_re.search(path.read_text(encoding="utf-8", errors="ignore")):
            stale_files.append(str(path.relative_to(root)))
    gates["no_stale_pre_v0_1_4_runtime_contracts"] = gate(
        not stale_files, files=stale_files
    )

    strategy_path = root / "docs/source_strategy/espresso_puck_modeling_and_simulation_strategy_v1_2.md"
    strategy_text = strategy_path.read_text(encoding="utf-8")
    gates["strategy_v1_2_freeze_scope_embedded"] = gate(
        all_tokens(
            strategy_text,
            (
                "no governing-physics change",
                "terminal freeze manifest",
                "32 ranks",
                "WP-0.1R",
            ),
        )
    )

    try:
        val001_details = verify_val001_correction(root)
        val001_details = {key: value for key, value in val001_details.items() if key != "status"}
        gates["val001_corrected_contracts_fail_closed"] = gate(True, **val001_details)
    except (ValueError, OSError, KeyError) as exc:
        gates["val001_corrected_contracts_fail_closed"] = gate(False, error=str(exc))

    try:
        hardening_details = verify_val001_hardening(root)
        gates["val001_postresult_framework_hardening"] = gate(True, **hardening_details)
    except (ValueError, OSError, KeyError) as exc:
        gates["val001_postresult_framework_hardening"] = gate(False, error=str(exc))
    try:
        deep_schema_details = verify_val001_deep_schema_coverage(root)
        gates["val001_complete_deep_schema_coverage"] = gate(True, **deep_schema_details)
    except Exception as exc:
        gates["val001_complete_deep_schema_coverage"] = gate(False, error=str(exc))
    try:
        closure_details = verify_val001_administrative_closure(root, require_clean=False, require_external_root=False)
        gates["val001_zero_exclusion_administrative_closure"] = gate(True, **closure_details)
    except Exception as exc:
        gates["val001_zero_exclusion_administrative_closure"] = gate(False, error=str(exc))

    all_pass = all(item["status"] == "PASS" for item in gates.values())
    report = {
        "schema_version": "espresso.whole_pull.static_validation.v0.2.0",
        "status": "PASS" if all_pass else "FAIL",
        "gate_summary": {
            "pass": sum(item["status"] == "PASS" for item in gates.values()),
            "fail": sum(item["status"] == "FAIL" for item in gates.values()),
            "total": len(gates),
        },
        "gates": gates,
        "limitations": [
            "This is a static/package mathematics check, not a wmake compilation.",
            "Historical Allrun/Allverify gates remain scoped to the immutable v0.1.4 R0 baseline.",
            "WP02 governing-change evidence is verified by verify_change_contract.py.",
            "Physical validation is not established.",
        ],
    }
    if output is not None:
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"static-validation report written to {output}", file=sys.stderr)
    print(json.dumps(report, indent=2))
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
