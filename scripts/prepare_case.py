#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from espresso_reference_math import (  # noqa: E402
    analytical_preview,
    b0_reduced_simulation,
    nominal_cylinder_volume_m3,
    straight_sided_wedge_scale,
)

PACKAGE_VERSION = "0.1.4"
REFERENCE_CASE_RELATIVE = Path("cases/reference_R0_20g_58mm_9bar")
REFERENCE_CONFIG_RELATIVE = Path("config/reference_R0.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_stem(scenario: dict) -> str:
    scenario_id = str(scenario["scenario_id"])
    if scenario_id.startswith("reference_R0"):
        return "ESPRESSO_WHOLE_PULL_REFERENCE"
    if scenario_id.startswith("fixture_layered_pressure"):
        return "ESPRESSO_LAYERED_PRESSURE_FIXTURE"
    return "ESPRESSO_WHOLE_PULL_CASE"


def render_block_mesh(scenario: dict) -> str:
    geometry = scenario["geometry"]
    bed = scenario["coffee_bed"]
    radius = float(geometry["basket_radius_m"])
    depth = float(bed["bed_depth_m"])
    half_angle = math.radians(float(geometry["wedge_angle_deg"]) / 2.0)
    y = radius * math.cos(half_angle)
    z = radius * math.sin(half_angle)
    axial_cells = int(geometry["axial_cells"])
    radial_cells = int(geometry["radial_cells"])
    azimuthal_cells = int(geometry["azimuthal_cells"])
    axial_grading = float(geometry["axial_grading"])
    radial_grading = float(geometry["radial_grading"])
    return f'''FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}

// x is puck depth (bed top at x=0; basket bottom at x={depth:.16g}).
// Straight-sided wedge spanning {geometry['wedge_angle_deg']} degrees.
scale 1;

vertices
(
    (0          0       0)
    ({depth:.16g} 0       0)
    ({depth:.16g} {y:.16g} {-z:.16g})
    (0          {y:.16g} {-z:.16g})
    (0          0       0)
    ({depth:.16g} 0       0)
    ({depth:.16g} {y:.16g} {z:.16g})
    (0          {y:.16g} {z:.16g})
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({axial_cells} {radial_cells} {azimuthal_cells})
        simpleGrading ({axial_grading:.16g} {radial_grading:.16g} 1)
);

edges
(
);

boundary
(
    inlet
    {{
        type patch;
        faces ((0 3 7 4));
    }}

    outlet
    {{
        type patch;
        faces ((1 5 6 2));
    }}

    outerWall
    {{
        type wall;
        faces ((3 2 6 7));
    }}

    axis
    {{
        type empty;
        faces ((0 4 5 1));
    }}

    wedgeMinus
    {{
        type wedge;
        faces ((0 1 2 3));
    }}

    wedgePlus
    {{
        type wedge;
        faces ((4 7 6 5));
    }}
);

mergePatchPairs
(
);
'''


def render_control_dict(scenario: dict) -> str:
    time_cfg = scenario["time"]
    output_cfg = scenario.get("output", {})
    compression = "on" if bool(output_cfg.get("write_compression", False)) else "off"
    write_format = str(output_cfg.get("write_format", "binary"))
    return f'''FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      controlDict;
}}

application     espressoWholePullFoam;

startFrom       startTime;
startTime       {float(time_cfg.get('start_s', 0.0)):.16g};
stopAt          endTime;
endTime         {float(time_cfg['end_s']):.16g};
deltaT          {float(time_cfg['delta_t_s']):.16g};

writeControl    runTime;
writeInterval   {float(time_cfg['field_write_interval_s']):.16g};
purgeWrite      0;
writeFormat     {write_format};
writePrecision  10;
writeCompression {compression};
timeFormat      general;
timePrecision   12;
runTimeModifiable false;

functions
{{
}}
'''


def render_properties(scenario: dict) -> str:
    geometry = scenario["geometry"]
    bed = scenario["coffee_bed"]
    liquid = scenario["liquid"]
    hydraulic = scenario["hydraulics"]
    wetting = scenario["wetting"]
    extraction = scenario["extraction"]
    time_cfg = scenario["time"]
    profile = hydraulic.get("permeability_profile", {"type": "uniform"})
    probes = scenario.get("verification", {}).get("pressure_probes", [])
    if len(probes) < 2:
        depth = float(bed["bed_depth_m"])
        dx = depth / int(geometry["axial_cells"])
        probes = [
            {"position_m": 0.25 * depth, "half_width_m": 0.51 * dx},
            {"position_m": 0.75 * depth, "half_width_m": 0.51 * dx},
        ]
    axial_dx = float(bed["bed_depth_m"]) / int(geometry["axial_cells"])
    smoothing = float(wetting["front_smoothing_cells"]) * axial_dx
    return f'''FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      espressoModelProperties;
}}

scenarioId                 {scenario['scenario_id']};
mode                       {scenario['mode']};
inletPatch                 inlet;
outletPatch                outlet;
pressureIntegrationMethod  exactPiecewiseLinearIntegral;

// Geometry [SI]
basketRadius               {float(geometry['basket_radius_m']):.16g};
bedDepth                   {float(bed['bed_depth_m']):.16g};
wedgeAngleDegrees          {float(geometry['wedge_angle_deg']):.16g};

// Coffee bed and inventory [SI]
dryDose                    {float(bed['dry_dose_kg']):.16g};
extractableFraction        {float(bed['initial_extractable_fraction_dry_basis']):.16g};
initialPorosity            {float(bed['initial_porosity']):.16g};
initialWetFront            {float(wetting.get('initial_wet_front_m', 0.0)):.16g};

// Liquid at fixed temperature [SI]
liquidDensity              {float(liquid['density_kg_m3']):.16g};
dynamicViscosity           {float(liquid['dynamic_viscosity_Pa_s']):.16g};
effectiveSoluteDiffusivity {float(liquid['effective_solute_diffusivity_m2_s']):.16g};

// Hydraulics and exact sharp-front pressure integration [SI]
saturatedPermeability      {float(hydraulic['saturated_permeability_m2']):.16g};
wettingPermeability        {float(hydraulic['wetting_permeability_m2']):.16g};
targetInletPressure        {float(hydraulic['target_inlet_pressure_gauge_Pa']):.16g};
outletPressure             {float(hydraulic['outlet_pressure_gauge_Pa']):.16g};
frontPressure              {float(hydraulic['front_pressure_gauge_Pa']):.16g};
pressureRampTime           {float(hydraulic['pressure_ramp_time_s']):.16g};
frontSmoothingLength       {smoothing:.16g};

permeabilityProfile        {profile.get('type', 'uniform')};
layerInterfacePosition     {float(profile.get('interface_position_m', 0.5*float(bed['bed_depth_m']))):.16g};
layerPermeabilityUpstream  {float(profile.get('upstream_permeability_m2', hydraulic['saturated_permeability_m2'])):.16g};
layerPermeabilityDownstream {float(profile.get('downstream_permeability_m2', hydraulic['saturated_permeability_m2'])):.16g};

pressureProbe1Position     {float(probes[0]['position_m']):.16g};
pressureProbe1HalfWidth    {float(probes[0]['half_width_m']):.16g};
pressureProbe2Position     {float(probes[1]['position_m']):.16g};
pressureProbe2HalfWidth    {float(probes[1]['half_width_m']):.16g};

// One effective soluble inventory [SI]
extractionRateConstant     {float(extraction['rate_constant_1_s']):.16g};
saturationConcentration    {float(extraction['saturation_concentration_kg_m3']):.16g};

targetBeverageMass         {float(time_cfg['target_beverage_mass_kg']):.16g};
'''


def render_decompose(scenario: dict, nprocs: int) -> str:
    method = str(scenario["parallel"]["decomposition_method"])
    return f'''FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      decomposeParDict;
}}

numberOfSubdomains {nprocs};
method              {method};

distributed         no;
roots               ();
'''


def resolve_path(root: Path, value: Path, default: Path) -> Path:
    chosen = value if value is not None else default
    return chosen.resolve() if chosen.is_absolute() else (root / chosen).resolve()


def ensure_case_template(root: Path, case: Path) -> None:
    template = root / REFERENCE_CASE_RELATIVE
    (case / "system").mkdir(parents=True, exist_ok=True)
    (case / "constant").mkdir(parents=True, exist_ok=True)
    if not (case / "0.orig").is_dir():
        shutil.copytree(template / "0.orig", case / "0.orig")
    for name in ("fvSchemes", "fvSolution"):
        target = case / "system" / name
        if not target.is_file():
            shutil.copy2(template / "system" / name, target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--nprocs", type=int, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--case-dir", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    config_path = resolve_path(root, args.config, REFERENCE_CONFIG_RELATIVE)
    case = resolve_path(root, args.case_dir, REFERENCE_CASE_RELATIVE)
    scenario = json.loads(config_path.read_text(encoding="utf-8"))
    if args.nprocs < 1:
        raise SystemExit("nprocs must be positive")

    ensure_case_template(root, case)
    zero = case / "0"
    if zero.exists():
        shutil.rmtree(zero)
    shutil.copytree(case / "0.orig", zero)

    (case / "system/blockMeshDict").write_text(
        render_block_mesh(scenario), encoding="utf-8"
    )
    (case / "system/controlDict").write_text(
        render_control_dict(scenario), encoding="utf-8"
    )
    (case / "system/decomposeParDict").write_text(
        render_decompose(scenario, args.nprocs), encoding="utf-8"
    )
    (case / "constant/espressoModelProperties").write_text(
        render_properties(scenario), encoding="utf-8"
    )
    (case / "CASE_SCENARIO_V0_1_4.json").write_text(
        json.dumps(scenario, indent=2) + "\n", encoding="utf-8"
    )

    preflight_dir = case / "preflight"
    preflight_dir.mkdir(parents=True, exist_ok=True)
    preview = analytical_preview(scenario)
    (preflight_dir / "ANALYTICAL_PREFLIGHT_V0_1_4.json").write_text(
        json.dumps(preview, indent=2) + "\n", encoding="utf-8"
    )

    b0 = None
    if str(scenario["scenario_id"]).startswith("reference_R0"):
        b0 = b0_reduced_simulation(scenario)
        (preflight_dir / "B0_REDUCED_TWIN_V0_1_4.json").write_text(
            json.dumps(b0, indent=2) + "\n", encoding="utf-8"
        )

    environment = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "requested_mpi_ranks": args.nprocs,
        "wm_project": os.environ.get("WM_PROJECT"),
        "wm_project_version": os.environ.get("WM_PROJECT_VERSION"),
        "wm_options": os.environ.get("WM_OPTIONS"),
        "foam_user_appbin": os.environ.get("FOAM_USER_APPBIN"),
    }
    (case / "RUN_ENVIRONMENT_V0_1_4.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8"
    )

    scientific_inputs = [
        config_path,
        root / "solver/espressoWholePullFoam/espressoWholePullFoam.C",
        root / "solver/espressoWholePullFoam/Make/files",
        root / "solver/espressoWholePullFoam/Make/options",
        case / "system/blockMeshDict",
        case / "system/controlDict",
        case / "system/fvSchemes",
        case / "system/fvSolution",
        case / "system/decomposeParDict",
        case / "constant/espressoModelProperties",
    ] + sorted((case / "0.orig").iterdir())
    hashes = {}
    for path in scientific_inputs:
        try:
            relative = str(path.resolve().relative_to(root))
        except ValueError:
            relative = str(path)
        hashes[relative] = sha256(path)
    aggregate = hashlib.sha256()
    for relative, digest in sorted(hashes.items()):
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(digest.encode("ascii"))
        aggregate.update(b"\n")

    stem = artifact_stem(scenario)
    manifest_name = f"{stem}_CASE_MANIFEST_V0_1_4.json"
    prepared_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "schema_version": "espresso.whole_pull.scientific_input_manifest.v0.1.4",
        "manifest_role": "immutable_scientific_inputs_only",
        "prepared_at_utc": prepared_at,
        "generated_at_utc": prepared_at,
        "scenario_id": scenario["scenario_id"],
        "solver": scenario["solver"],
        "solver_version": scenario["solver_version"],
        "openfoam_target": "OpenFOAM Foundation 12",
        "mode": scenario["mode"],
        "requested_mpi_ranks": args.nprocs,
        "mesh_identity": {
            "axial_cells": int(scenario["geometry"]["axial_cells"]),
            "radial_cells": int(scenario["geometry"]["radial_cells"]),
            "azimuthal_cells": int(scenario["geometry"]["azimuthal_cells"]),
            "total_cells_expected": (
                int(scenario["geometry"]["axial_cells"])
                * int(scenario["geometry"]["radial_cells"])
                * int(scenario["geometry"]["azimuthal_cells"])
            ),
            "delta_t_s": float(scenario["time"]["delta_t_s"]),
            "end_time_s": float(scenario["time"]["end_s"]),
            "wedge_angle_deg": float(scenario["geometry"]["wedge_angle_deg"]),
            "straight_sided_wedge_scale": straight_sided_wedge_scale(
                scenario["geometry"]["wedge_angle_deg"]
            ),
            "nominal_cylinder_volume_m3": nominal_cylinder_volume_m3(scenario),
        },
        "pressure_integration_method": scenario["hydraulics"].get(
            "pressure_integration_method"
        ),
        "scientific_input_sha256": hashes,
        "scientific_input_file_count": len(hashes),
        "scientific_bundle_sha256": aggregate.hexdigest(),
        "calibration": scenario.get("calibration"),
        "claim_ceiling": scenario["claim_ceiling"],
        "downstream_artifacts_intentionally_excluded": [
            "trace CSV",
            "field index",
            "reference acceptance",
            "qualification report",
            "run status",
            "freeze manifest",
        ],
        "acyclic_provenance_note": (
            "This manifest is immutable after case preparation and hashes only "
            "scientific source/configuration/generated case inputs."
        ),
    }
    (case / manifest_name).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "prepared_case": str(case),
                "config": str(config_path),
                "case_manifest": str(case / manifest_name),
                "preflight": preview,
                "b0_reduced_twin_generated": b0 is not None,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
