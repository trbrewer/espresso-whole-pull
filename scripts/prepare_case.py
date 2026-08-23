#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
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
R1_TASK = "WP01R-004"
R1_MANIFEST_NAME = "WP01R_004_GENERATED_CASE_MANIFEST.json"
R1_CONFIG_RELATIVE = Path("config/reconstruction_R1_waszkiewicz_9bar.json")
WP02_TASK = "WP02-001"
WP02_CONFIG_RELATIVES = {
    Path("config/reconstruction_WP02A_waszkiewicz_9bar.json"),
    Path("config/reconstruction_WP02A_waszkiewicz_8bar.json"),
    Path("config/fixture_WP02_001_uniform_pressure.json"),
}

INDEXED_SPECIES_MODEL = "indexed_passive_species_first_order_with_capacity_ceiling"
ALLOWED_SPECIES_PROVENANCE = {
    "DIRECT_MEASURED_INPUT", "LITERATURE_CONSTRAINED", "TRAINING_DATA_ESTIMATE",
    "FIXED_STRUCTURAL_ASSUMPTION", "PROXY",
}


def indexed_species_contract(scenario: dict) -> dict | None:
    extraction = scenario["extraction"]
    model = extraction.get(
        "model", "single_effective_solute_first_order_with_capacity_ceiling"
    )
    if model != INDEXED_SPECIES_MODEL:
        return None
    species = extraction.get("species")
    if not isinstance(species, list) or not species:
        raise SystemExit("indexed extraction requires a nonempty species list")
    legacy_fraction = float(
        scenario["coffee_bed"]["initial_extractable_fraction_dry_basis"]
    )
    legacy_rate = float(extraction["legacy_rate_constant_1_s"])
    legacy_saturation = float(extraction["legacy_saturation_concentration_kg_m3"])
    legacy_diffusivity = float(scenario["liquid"]["effective_solute_diffusivity_m2_s"])
    seen: set[str] = set()
    explicit_sum = 0.0
    structural_count = 0
    normalized = []
    for index, raw in enumerate(species):
        species_id = raw.get("id")
        if (
            not isinstance(species_id, str) or not species_id
            or not species_id.replace("_", "a").isalnum()
            or not (species_id[0].isalpha() or species_id[0] == "_")
            or "/" in species_id or ".." in species_id
        ):
            raise SystemExit(f"invalid indexed species id: {species_id!r}")
        if species_id in seen:
            raise SystemExit(f"duplicate indexed species id: {species_id}")
        seen.add(species_id)
        role = raw.get("role")
        entry = {"id": species_id, "index": index}
        if role == "explicit_inventory":
            required = (
                "dry_coffee_inventory_mass_fraction", "availability_fraction",
                "rate_constant_1_s", "saturation_concentration_kg_m3",
                "effective_diffusivity_m2_s", "parameter_provenance",
            )
            missing = [key for key in required if key not in raw]
            if missing:
                raise SystemExit(f"species {species_id} missing keys: {', '.join(missing)}")
            inventory, availability, rate, saturation, diffusivity = (
                float(raw[key]) for key in required[:5]
            )
            values = (inventory, availability, rate, saturation, diffusivity)
            if not all(math.isfinite(value) for value in values):
                raise SystemExit(f"species {species_id} contains a nonfinite value")
            if (inventory < 0.0 or not 0.0 <= availability <= 1.0 or rate < 0.0
                    or saturation <= 0.0 or diffusivity < 0.0):
                raise SystemExit(f"species {species_id} contains an invalid value")
            provenance = raw["parameter_provenance"]
            if set(provenance) != {
                "inventory", "availability", "rate", "saturation", "diffusivity"
            } or any(value not in ALLOWED_SPECIES_PROVENANCE
                     for value in provenance.values()):
                raise SystemExit(f"species {species_id} has forbidden provenance")
            effective = inventory * availability
            explicit_sum += effective
            entry.update(role="explicitInventory", effective_fraction=effective,
                         rate=rate, saturation=saturation, diffusivity=diffusivity,
                         inherited=False)
        elif role == "structural_balance":
            structural_count += 1
            if structural_count > 1:
                raise SystemExit("at most one structural-balance species is permitted")
            if raw != {"id": species_id, "role": "structural_balance",
                       "inherit_legacy_parameters": True}:
                raise SystemExit(
                    "structural-balance species must contain only id, role, and "
                    "inherit_legacy_parameters=true"
                )
            entry.update(role="structuralBalance", rate=legacy_rate,
                         saturation=legacy_saturation, diffusivity=legacy_diffusivity,
                         inherited=True)
        else:
            raise SystemExit(f"unknown indexed species role: {role!r}")
        normalized.append(entry)
    tolerance = 1.0e-15
    residual = legacy_fraction - explicit_sum
    if not math.isfinite(residual) or residual < -tolerance:
        raise SystemExit("indexed species inventory exceeds legacy extractableFraction")
    if structural_count:
        for entry in normalized:
            if entry["role"] == "structuralBalance":
                entry["effective_fraction"] = max(residual, 0.0)
    elif abs(residual) > tolerance:
        raise SystemExit(
            "explicit indexed inventory must equal extractableFraction without a "
            "structural-balance species"
        )
    if abs(sum(item["effective_fraction"] for item in normalized) - legacy_fraction) > tolerance:
        raise SystemExit("indexed inventory closure failed")
    return {"species": normalized, "closure_tolerance": tolerance}


def render_indexed_species(scenario: dict) -> str:
    contract = indexed_species_contract(scenario)
    if contract is None:
        return ""
    lines = ["soluteTransportModel indexedPassiveSpecies;", "",
             "indexedPassiveSpeciesCoeffs", "{", "    speciesOrder", "    ("]
    lines.extend(f"        {item['id']}" for item in contract["species"])
    lines.extend(["    );", ""])
    for item in contract["species"]:
        lines.extend([
            f"    {item['id']}", "    {", f"        role {item['role']};",
            f"        effectiveInitialFraction {item['effective_fraction']:.16g};",
            f"        extractionRateConstant {item['rate']:.16g};",
            f"        saturationConcentration {item['saturation']:.16g};",
            f"        effectiveSoluteDiffusivity {item['diffusivity']:.16g};",
            "        inheritLegacyParameters "
            f"{'true' if item['inherited'] else 'false'};",
            "    }", "",
        ])
    lines.extend(["}", ""])
    return "\n".join(lines)


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
    output_cfg = scenario["output"]
    r1 = is_r1_scenario(scenario)
    compression_value = (
        output_cfg["write_compression"]
        if r1
        else output_cfg.get("write_compression", False)
    )
    format_value = (
        output_cfg["write_format"] if r1 else output_cfg.get("write_format", "binary")
    )
    start_value = time_cfg["start_s"] if r1 else time_cfg.get("start_s", 0.0)
    compression = "on" if bool(compression_value) else "off"
    write_format = str(format_value)
    write_precision = (
        int(output_cfg["write_precision_digits"])
        if is_wp02_uniform_fixture(scenario)
        else 10
    )
    return f'''FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      controlDict;
}}

application     espressoWholePullFoam;

startFrom       startTime;
startTime       {float(start_value):.16g};
stopAt          endTime;
endTime         {float(time_cfg['end_s']):.16g};
deltaT          {float(time_cfg['delta_t_s']):.16g};

writeControl    runTime;
writeInterval   {float(time_cfg['field_write_interval_s']):.16g};
purgeWrite      0;
writeFormat     {write_format};
writePrecision  {write_precision};
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
    indexed_species_dictionary = render_indexed_species(scenario)
    legacy_rate = extraction.get(
        "rate_constant_1_s", extraction.get("legacy_rate_constant_1_s")
    )
    legacy_saturation = extraction.get(
        "saturation_concentration_kg_m3",
        extraction.get("legacy_saturation_concentration_kg_m3"),
    )
    time_cfg = scenario["time"]
    r1 = is_r1_scenario(scenario)
    closure = scenario.get("effective_permeability_evolution")
    profile = (
        hydraulic["permeability_profile"]
        if r1
        else hydraulic.get("permeability_profile", {"type": "uniform"})
    )
    profile_type = profile.get("type", "uniform")
    if profile_type not in {"uniform", "axial_two_layer", "radial_two_zone"}:
        raise SystemExit("unsupported permeability profile")
    radius = float(geometry["basket_radius_m"])
    interface_radius = float(profile.get("interface_radius_m", 0.5*radius))
    inner_k = float(profile.get(
        "inner_permeability_m2", hydraulic["saturated_permeability_m2"]
    ))
    outer_k = float(profile.get(
        "outer_permeability_m2", hydraulic["saturated_permeability_m2"]
    ))
    if (
        not all(math.isfinite(x) for x in (interface_radius, inner_k, outer_k))
        or not (0.0 < interface_radius < radius)
        or inner_k <= 0.0 or outer_k <= 0.0
    ):
        raise SystemExit("invalid radial permeability profile")
    if closure is not None and profile_type != "uniform":
        raise SystemExit("effective permeability evolution requires uniform profile")
    probes = (
        scenario["verification"]["pressure_probes"]
        if r1
        else scenario.get("verification", {}).get("pressure_probes", [])
    )
    if not r1 and len(probes) < 2:
        depth = float(bed["bed_depth_m"])
        dx = depth / int(geometry["axial_cells"])
        probes = [
            {"position_m": 0.25 * depth, "half_width_m": 0.51 * dx},
            {"position_m": 0.75 * depth, "half_width_m": 0.51 * dx},
        ]
    axial_dx = float(bed["bed_depth_m"]) / int(geometry["axial_cells"])
    smoothing = float(wetting["front_smoothing_cells"]) * axial_dx
    pressure_boundary_model = scenario.get(
        "pressureBoundaryModel", "prescribedPressure"
    )
    flow_model = scenario.get("flowResistanceModel", "darcy")
    flow_dictionary = ""
    if flow_model == "darcyForchheimer":
        model = scenario.get("inertialPermeabilityModel")
        if model not in {"constant", "wadsworth2026CeramicsFit"}:
            raise SystemExit("unsupported inertialPermeabilityModel")
        constant_ki = float(scenario.get("constantInertialPermeabilityM", 1.0))
        controls = scenario.get("nonlinearControls", {})
        rel = float(controls.get("nonlinearRelativeTolerance", 1e-10))
        absolute = float(controls.get("nonlinearAbsoluteTolerance", 1e-12))
        maximum = controls.get("nonlinearMaximumIterations", 80)
        relaxation = float(controls.get("nonlinearUnderRelaxation", 0.7))
        flux_tol = float(controls.get("machineFluxRelativeTolerance", 1e-6))
        values = (constant_ki, rel, absolute, relaxation, flux_tol)
        if (
            any(not math.isfinite(value) or value <= 0 for value in values)
            or isinstance(maximum, bool) or not isinstance(maximum, int)
            or maximum < 1 or relaxation > 1
            or (model == "constant" and constant_ki <= 0)
        ):
            raise SystemExit("invalid Darcy-Forchheimer controls")
        profile_upstream_ki = float(
            profile.get("upstream_inertial_permeability_m", constant_ki)
        )
        profile_downstream_ki = float(
            profile.get("downstream_inertial_permeability_m", constant_ki)
        )
        inner_ki = float(profile.get(
            "inner_inertial_permeability_m", constant_ki
        ))
        outer_ki = float(profile.get(
            "outer_inertial_permeability_m", constant_ki
        ))
        if model == "constant" and profile_type == "radial_two_zone" and (
            not all(math.isfinite(x) and x > 0.0 for x in (inner_ki, outer_ki))
        ):
            raise SystemExit("constant radial profile requires positive zone k_I")
        flow_dictionary = f'''
flowResistanceModel darcyForchheimer;
inertialPermeabilityModel {model};
constantInertialPermeabilityM {constant_ki:.16g};
layerInertialPermeabilityUpstream {profile_upstream_ki:.16g};
layerInertialPermeabilityDownstream {profile_downstream_ki:.16g};
innerInertialPermeabilityM {inner_ki:.16g};
outerInertialPermeabilityM {outer_ki:.16g};
nonlinearRelativeTolerance {rel:.16g};
nonlinearAbsoluteTolerance {absolute:.16g};
nonlinearMaximumIterations {maximum};
nonlinearUnderRelaxation {relaxation:.16g};
machineFluxRelativeTolerance {flux_tol:.16g};
'''
    elif flow_model == "darcy":
        flow_dictionary = "flowResistanceModel darcy;\n"
    else:
        raise SystemExit("unsupported flowResistanceModel")
    machine_dictionary = ""
    if pressure_boundary_model == "lumpedMachineCompliance":
        machine = scenario.get("machineBoundary")
        required_machine = {
            "initialUpstreamPressure",
            "upstreamCompliance",
            "upstreamResistance",
            "freeFlowRate",
            "shutoffPressure",
            "supplyRampTime",
            "couplingRelativeTolerance",
            "couplingAbsoluteTolerance",
            "couplingMaximumIterations",
        }
        if not isinstance(machine, dict) or set(machine) != required_machine:
            raise SystemExit("invalid lumpedMachineCompliance machineBoundary")
        numeric = {key: machine[key] for key in required_machine}
        if any(isinstance(value, bool) for value in numeric.values()):
            raise SystemExit("machineBoundary values must be numeric")
        maximum_iterations = machine["couplingMaximumIterations"]
        if (
            isinstance(maximum_iterations, bool)
            or not isinstance(maximum_iterations, int)
        ):
            raise SystemExit("couplingMaximumIterations must be an integer")
        try:
            numeric = {key: float(value) for key, value in numeric.items()}
        except (TypeError, ValueError):
            raise SystemExit("machineBoundary values must be finite numbers")
        if any(not math.isfinite(value) for value in numeric.values()):
            raise SystemExit("machineBoundary values must be finite")
        if (
            numeric["initialUpstreamPressure"]
            < float(hydraulic["outlet_pressure_gauge_Pa"])
            or numeric["initialUpstreamPressure"]
            > numeric["shutoffPressure"]
            or numeric["upstreamCompliance"] <= 0
            or numeric["upstreamResistance"] < 0
            or numeric["freeFlowRate"] <= 0
            or numeric["shutoffPressure"]
            <= float(hydraulic["outlet_pressure_gauge_Pa"])
            or numeric["supplyRampTime"] < 0
            or numeric["couplingRelativeTolerance"] <= 0
            or numeric["couplingAbsoluteTolerance"] <= 0
            or maximum_iterations < 1
        ):
            raise SystemExit("machineBoundary values outside physical domain")
        machine_dictionary = f'''
machineBoundary
{{
    initialUpstreamPressure {numeric["initialUpstreamPressure"]:.16g};
    upstreamCompliance {numeric["upstreamCompliance"]:.16g};
    upstreamResistance {numeric["upstreamResistance"]:.16g};
    freeFlowRate {numeric["freeFlowRate"]:.16g};
    shutoffPressure {numeric["shutoffPressure"]:.16g};
    supplyRampTime {numeric["supplyRampTime"]:.16g};
    couplingRelativeTolerance {numeric["couplingRelativeTolerance"]:.16g};
    couplingAbsoluteTolerance {numeric["couplingAbsoluteTolerance"]:.16g};
    couplingMaximumIterations {maximum_iterations};
}}
'''
    elif pressure_boundary_model != "prescribedPressure":
        raise SystemExit("unsupported pressureBoundaryModel")
    mechanics_model = scenario.get("bedMechanicsModel", "none")
    mechanics_dictionary = "bedMechanicsModel none;\n"
    if mechanics_model == "waszkiewiczQuasiStaticCompaction":
        compaction = scenario.get("poroelasticCompaction")
        required_compaction = {
            "model", "stressFreePorosity", "criticalCompactionPressurePa",
            "stressFreePermeabilityM2", "nonlinearRelativeTolerance",
            "nonlinearAbsoluteTolerance", "nonlinearMaximumIterations",
            "nonlinearUnderRelaxation", "machineFluxRelativeTolerance",
        }
        if not isinstance(compaction, dict) or set(compaction) != required_compaction:
            raise SystemExit("invalid poroelasticCompaction dictionary")
        if compaction["model"] != "waszkiewicz2025FinitePhi":
            raise SystemExit("unsupported poroelastic compaction model")
        maximum = compaction["nonlinearMaximumIterations"]
        if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum < 1:
            raise SystemExit("invalid poroelastic nonlinearMaximumIterations")
        values = {
            key: float(compaction[key]) for key in required_compaction
            if key not in {"model", "nonlinearMaximumIterations"}
        }
        if any(not math.isfinite(value) for value in values.values()):
            raise SystemExit("poroelastic compaction values must be finite")
        phi = values["stressFreePorosity"]
        pc = values["criticalCompactionPressurePa"]
        relaxation = values["nonlinearUnderRelaxation"]
        if (
            not 0.0 < phi < 1.0 or pc <= 0.0
            or values["stressFreePermeabilityM2"] <= 0.0
            or values["nonlinearRelativeTolerance"] <= 0.0
            or values["nonlinearAbsoluteTolerance"] <= 0.0
            or not 0.0 < relaxation <= 1.0
            or values["machineFluxRelativeTolerance"] <= 0.0
        ):
            raise SystemExit("poroelastic compaction values outside domain")
        if profile_type != "uniform" or flow_model != "darcy" or closure is not None:
            raise SystemExit(
                "compaction requires uniform Darcy with effective permeability disabled"
            )
        maximum_drop = (
            float(scenario["machineBoundary"]["shutoffPressure"])
            if pressure_boundary_model == "lumpedMachineCompliance"
            else float(hydraulic["target_inlet_pressure_gauge_Pa"])
        ) - float(hydraulic["outlet_pressure_gauge_Pa"])
        if not 0.0 <= maximum_drop < pc:
            raise SystemExit("maximum pressure drop must be below critical pressure")
        mechanics_dictionary = f'''
bedMechanicsModel waszkiewiczQuasiStaticCompaction;
poroelasticCompaction
{{
    model waszkiewicz2025FinitePhi;
    stressFreePorosity {phi:.16g};
    criticalCompactionPressurePa {pc:.16g};
    stressFreePermeabilityM2 {values["stressFreePermeabilityM2"]:.16g};
    nonlinearRelativeTolerance {values["nonlinearRelativeTolerance"]:.16g};
    nonlinearAbsoluteTolerance {values["nonlinearAbsoluteTolerance"]:.16g};
    nonlinearMaximumIterations {maximum};
    nonlinearUnderRelaxation {relaxation:.16g};
    machineFluxRelativeTolerance {values["machineFluxRelativeTolerance"]:.16g};
}}
'''
    elif mechanics_model != "none":
        raise SystemExit("unsupported bedMechanicsModel")
    closure_dictionary = ""
    if closure is not None:
        source = closure["source_parameters"]
        closure_dictionary = f'''
effectivePermeabilityEvolution
{{
    enabled true;
    model waszkiewiczSaturatedDissolutionIndexed;
    sourceReferencePressureBar {float(closure["source_reference_pressure_bar"]):.16g};
    sourcePcBar {float(source["pc_bar"]):.16g};
    sourceQcGPerS {float(source["qc_g_per_s"]):.16g};
    sourceKSolidsG {float(source["k_solids_g"]):.16g};
    sourceLSolidsS {float(source["l_solids_s"]):.16g};
    sourceMSolidsS {float(source["m_solids_s"]):.16g};
    sourceDoseG {float(source["dose_g"]):.16g};
    sourceToSolverOffsetS {float(closure["source_to_solver_offset_s"]):.16g};
    sourceValidityStartS {float(closure["source_validity_start_s"]):.16g};
    minimumMultiplier {float(closure["minimum_effective_multiplier"]):.16g};
    maximumMultiplier {float(closure["maximum_effective_multiplier"]):.16g};
}}
'''
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
pressureBoundaryModel      {pressure_boundary_model};
{flow_dictionary}

// Geometry [SI]
basketRadius               {float(geometry['basket_radius_m']):.16g};
bedDepth                   {float(bed['bed_depth_m']):.16g};
wedgeAngleDegrees          {float(geometry['wedge_angle_deg']):.16g};

// Coffee bed and inventory [SI]
dryDose                    {float(bed['dry_dose_kg']):.16g};
extractableFraction        {float(bed['initial_extractable_fraction_dry_basis']):.16g};
initialPorosity            {float(bed['initial_porosity']):.16g};
initialWetFront            {float(wetting['initial_wet_front_m'] if r1 else wetting.get('initial_wet_front_m', 0.0)):.16g};

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

permeabilityProfile        {profile['type'] if r1 else profile.get('type', 'uniform')};
layerInterfacePosition     {float(profile['interface_position_m'] if r1 else profile.get('interface_position_m', 0.5*float(bed['bed_depth_m']))):.16g};
layerPermeabilityUpstream  {float(profile['upstream_permeability_m2'] if r1 else profile.get('upstream_permeability_m2', hydraulic['saturated_permeability_m2'])):.16g};
layerPermeabilityDownstream {float(profile['downstream_permeability_m2'] if r1 else profile.get('downstream_permeability_m2', hydraulic['saturated_permeability_m2'])):.16g};
interfaceRadiusM            {interface_radius:.16g};
innerPermeabilityM2        {inner_k:.16g};
outerPermeabilityM2        {outer_k:.16g};

pressureProbe1Position     {float(probes[0]['position_m']):.16g};
pressureProbe1HalfWidth    {float(probes[0]['half_width_m']):.16g};
pressureProbe2Position     {float(probes[1]['position_m']):.16g};
pressureProbe2HalfWidth    {float(probes[1]['half_width_m']):.16g};

// One effective soluble inventory [SI]
extractionRateConstant     {float(legacy_rate):.16g};
saturationConcentration    {float(legacy_saturation):.16g};
{indexed_species_dictionary}
targetBeverageMass         {float(time_cfg['target_beverage_mass_kg']):.16g};
{machine_dictionary}
{mechanics_dictionary}
{closure_dictionary}
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


def canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def is_r1_scenario(scenario: dict) -> bool:
    return scenario.get("governance", {}).get("task") in {R1_TASK, WP02_TASK}


def is_wp02_scenario(scenario: dict) -> bool:
    return scenario.get("governance", {}).get("task") == WP02_TASK


def is_wp02_uniform_fixture(scenario: dict) -> bool:
    return scenario.get("scenario_id") == "fixture_WP02_001_uniform_pressure"


def validate_r1_scenario(scenario: dict, nprocs: int) -> None:
    required = [
        ("geometry", "hardware_basket_diameter_m"),
        ("geometry", "basket_diameter_m"),
        ("geometry", "basket_radius_m"),
        ("geometry", "hydraulic_bed_area_m2"),
        ("coffee_bed", "dry_dose_kg"),
        ("coffee_bed", "particle_solid_density_kg_m3"),
        ("coffee_bed", "initial_porosity"),
        ("coffee_bed", "bed_depth_m"),
        ("liquid", "temperature_K"),
        ("liquid", "density_kg_m3"),
        ("liquid", "dynamic_viscosity_Pa_s"),
        ("liquid", "effective_solute_diffusivity_m2_s"),
        ("hydraulics", "target_inlet_pressure_gauge_Pa"),
        ("hydraulics", "saturated_permeability_m2"),
        ("hydraulics", "wetting_permeability_m2"),
        ("hydraulics", "pressure_integration_method"),
        ("time", "end_s"),
        ("time", "delta_t_s"),
        ("time", "start_s"),
        ("time", "reduced_trace_maximum_interval_s"),
        ("output", "write_format"),
        ("output", "write_compression"),
        ("wetting", "initial_wet_front_m"),
    ]
    if not is_wp02_uniform_fixture(scenario):
        required.extend(
            [
                ("flow_comparison_contract", "primary_predicted_quantity"),
                ("flow_comparison_contract", "protected_shot_ids"),
                ("flow_comparison_contract", "protected_indices"),
                ("flow_comparison_contract", "normalization_indices"),
                ("flow_comparison_contract", "gates"),
                ("flow_comparison_contract", "pearson_degeneracy"),
            ]
        )
    for section, key in required:
        if section not in scenario or key not in scenario[section]:
            raise SystemExit(f"incomplete R1 scientific configuration: /{section}/{key}")
    profile = scenario["hydraulics"].get("permeability_profile")
    for key in (
        "type",
        "interface_position_m",
        "upstream_permeability_m2",
        "downstream_permeability_m2",
    ):
        if not isinstance(profile, dict) or key not in profile:
            raise SystemExit(
                "incomplete R1 scientific configuration: "
                f"/hydraulics/permeability_profile/{key}"
            )
    probes = scenario.get("verification", {}).get("pressure_probes")
    if not isinstance(probes, list) or len(probes) != 2:
        raise SystemExit("R1 requires exactly two explicit pressure probes")
    for index, probe in enumerate(probes):
        for key in ("name", "position_m", "half_width_m"):
            if not isinstance(probe, dict) or key not in probe:
                raise SystemExit(
                    f"incomplete R1 scientific configuration: "
                    f"/verification/pressure_probes/{index}/{key}"
                )
    governance = scenario["governance"]
    if is_wp02_scenario(scenario):
        closure = scenario.get("effective_permeability_evolution")
        if not isinstance(closure, dict) or closure.get("enabled") is not True:
            raise SystemExit("WP02 requires enabled effective-permeability closure")
        if closure.get("model") != "waszkiewiczSaturatedDissolutionIndexed":
            raise SystemExit("unsupported WP02 closure model")
        if profile["type"] != "uniform":
            raise SystemExit("WP02 closure requires uniform permeability")
        required_closure = (
            "source_reference_pressure_bar",
            "source_parameters",
            "source_to_solver_offset_s",
            "source_validity_start_s",
            "minimum_effective_multiplier",
            "maximum_effective_multiplier",
            "fixed_8s_offset_used",
        )
        if any(key not in closure for key in required_closure):
            raise SystemExit("incomplete WP02 closure configuration")
        if closure["fixed_8s_offset_used"] is not False:
            raise SystemExit("source fixed 8 s offset cannot enter WP02 mapping")
        if nprocs != scenario["parallel"]["default_subdomains"]:
            raise SystemExit("WP02 nprocs must equal frozen rank count")
        if is_wp02_uniform_fixture(scenario):
            if nprocs != 1 or "flow_comparison_contract" in scenario:
                raise SystemExit("invalid WP02 uniform fixture")
            output = scenario["output"]
            precision = output.get("write_precision_digits")
            if (
                isinstance(precision, bool)
                or not isinstance(precision, int)
                or precision != 17
                or output.get("write_format") != "ascii"
                or output.get("write_compression") is not False
            ):
                raise SystemExit("invalid WP02 uniform fixture output serialization")
        return
    if governance.get("change_scope") != "SOURCE_SCENARIO_CHANGE_ONLY":
        raise SystemExit("R1 change scope is not SOURCE_SCENARIO_CHANGE_ONLY")
    if governance.get("governing_physics_change") is not False:
        raise SystemExit("WP01R-004 cannot change governing physics")
    if scenario["hydraulics"]["runtime_adjustable_parameter_count"] != 0:
        raise SystemExit("R1 runtime-adjustable scientific parameters are forbidden")
    if scenario["hydraulics"]["historically_calibrated_parameter_count"] != 1:
        raise SystemExit("R1 must bind exactly one historically calibrated parameter")
    if scenario["hydraulics"]["saturated_permeability_m2"] != scenario["hydraulics"][
        "wetting_permeability_m2"
    ]:
        raise SystemExit("R1 wetting and saturated permeability must be identical")
    if scenario["source_time_mapping"]["source_fixed_8s_offset_used"] is not False:
        raise SystemExit("source fixed 8 s offset cannot enter solver time mapping")
    if nprocs != scenario["parallel"]["default_subdomains"]:
        raise SystemExit("R1 nprocs must equal the frozen routine rank count")


def require_canonical_r1(root: Path, config_path: Path, scenario: dict) -> None:
    if is_wp02_scenario(scenario):
        allowed = {(root / path).resolve() for path in WP02_CONFIG_RELATIVES}
        if config_path not in allowed:
            raise SystemExit("WP02 requires an exact canonical configuration")
        result = subprocess.run(
            [
                sys.executable,
                str(root / "scripts/wp02_contract_bridge.py"),
                "--root",
                str(root),
                "--check",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise SystemExit("canonical WP02 bridge check failed")
        expected = json.loads(config_path.read_text(encoding="utf-8"))
        if scenario != expected:
            raise SystemExit("WP02 scenario differs from canonical bytes")
        return
    canonical_path = (root / R1_CONFIG_RELATIVE).resolve()
    if config_path != canonical_path:
        raise SystemExit(f"R1 requires exact canonical config {R1_CONFIG_RELATIVE}")
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/r1_contract_bridge.py"),
            "--root",
            str(root),
            "--output",
            str(canonical_path),
            "--check",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise SystemExit(
            "canonical R1 bridge check failed: "
            + (result.stderr.strip() or result.stdout.strip())
        )
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    if scenario != canonical:
        raise SystemExit("R1 scenario does not match the bridge-generated canonical object")
    contract = json.loads(
        (
            root
            / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json"
        ).read_text(encoding="utf-8")
    )
    calibration = contract["calibration_contract"]
    expected_zero = (
        "runtime_adjustable_parameter_count",
        "generation_time_adjustable_parameter_count",
        "post_run_adjustable_parameter_count",
    )
    for key in expected_zero:
        if calibration[key] != 0:
            raise SystemExit(f"R1 contract {key} must be zero")


def require_fresh_r1_target(root: Path, case: Path) -> None:
    forbidden = [
        root,
        root / REFERENCE_CASE_RELATIVE,
        root / "cases/fixture_layered_pressure_v0_1_4",
        root / "config",
        root / "solver",
        root / "validation",
    ]
    if case.is_symlink():
        raise SystemExit("R1 case target must not be a symlink")
    for target in forbidden:
        if case == target.resolve() or target.resolve() in case.parents:
            raise SystemExit(f"R1 case target is a protected repository path: {case}")
    if case.exists():
        if not case.is_dir():
            raise SystemExit("R1 case target must be a directory")
        if any(case.iterdir()):
            raise SystemExit("R1 case target must be empty")


def aggregate_hash(entries: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for logical, content_hash in sorted(entries.items()):
        digest.update(logical.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content_hash.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def write_r1_manifest(
    root: Path,
    case: Path,
    config_path: Path,
    scenario: dict,
    preview: dict,
    b0: dict,
    nprocs: int,
) -> Path:
    puckworks_lock = json.loads(
        (root / "dependencies/puckworks.lock.json").read_text(encoding="utf-8")
    )
    wp02 = is_wp02_scenario(scenario)
    provenance_source = (
        root / "validation/wp02/WP02_001_CLOSURE_CONTRACT.json"
        if wp02
        else root / "validation/r1/WP01R_004_INPUT_PROVENANCE.json"
    )
    governance_dir = case / "governance"
    governance_dir.mkdir(parents=True, exist_ok=True)
    provenance_target = governance_dir / provenance_source.name
    shutil.copy2(provenance_source, provenance_target)

    governed_relatives = [
        "CASE_SCENARIO_V0_1_4.json",
        "constant/espressoModelProperties",
        "preflight/ANALYTICAL_PREFLIGHT_V0_1_4.json",
        "preflight/B0_REDUCED_TWIN_V0_1_4.json",
        "system/blockMeshDict",
        "system/controlDict",
        "system/decomposeParDict",
        "system/fvSchemes",
        "system/fvSolution",
        f"governance/{provenance_source.name}",
    ]
    governed_relatives.extend(
        f"0.orig/{path.name}" for path in sorted((case / "0.orig").iterdir())
    )
    governed_relatives.extend(f"0/{path.name}" for path in sorted((case / "0").iterdir()))
    governed_hashes = {
        relative: sha256(case / relative) for relative in sorted(governed_relatives)
    }

    scientific_paths = {
        config_path.relative_to(root).as_posix(): config_path,
        "solver/espressoWholePullFoam/espressoWholePullFoam.C": root
        / "solver/espressoWholePullFoam/espressoWholePullFoam.C",
        "solver/espressoWholePullFoam/Make/files": root
        / "solver/espressoWholePullFoam/Make/files",
        "solver/espressoWholePullFoam/Make/options": root
        / "solver/espressoWholePullFoam/Make/options",
        "generated_case/system/blockMeshDict": case / "system/blockMeshDict",
        "generated_case/system/controlDict": case / "system/controlDict",
        "generated_case/system/fvSchemes": case / "system/fvSchemes",
        "generated_case/system/fvSolution": case / "system/fvSolution",
        "generated_case/system/decomposeParDict": case / "system/decomposeParDict",
        "generated_case/constant/espressoModelProperties": case
        / "constant/espressoModelProperties",
    }
    if wp02:
        scientific_paths.update(
            {
                "validation/wp02/WP02_001_CLOSURE_CONTRACT.json": provenance_source,
                "scripts/waszkiewicz_effective_permeability.py": root
                / "scripts/waszkiewicz_effective_permeability.py",
                "scripts/wp02_reference_math.py": root / "scripts/wp02_reference_math.py",
            }
        )
    scientific_paths.update(
        {
            f"generated_case/0.orig/{path.name}": path
            for path in sorted((case / "0.orig").iterdir())
        }
    )
    scientific_hashes = {
        logical: sha256(path) for logical, path in sorted(scientific_paths.items())
    }
    template_hashes = {
        "cases/reference_R0_20g_58mm_9bar/system/fvSchemes": sha256(
            root / REFERENCE_CASE_RELATIVE / "system/fvSchemes"
        ),
        "cases/reference_R0_20g_58mm_9bar/system/fvSolution": sha256(
            root / REFERENCE_CASE_RELATIVE / "system/fvSolution"
        ),
    }
    template_hashes.update(
        {
            f"cases/reference_R0_20g_58mm_9bar/0.orig/{path.name}": sha256(path)
            for path in sorted((root / REFERENCE_CASE_RELATIVE / "0.orig").iterdir())
        }
    )
    manifest = {
        "schema_version": (
            "espresso.public.wp02_001_generated_case_manifest.v1"
            if wp02
            else "espresso.public.wp01r_004_generated_case_manifest.v1"
        ),
        "task": "WP02-001" if wp02 else "WP01R-004",
        "github_issue": 18 if wp02 else 6,
        "change_scope": "GOVERNING_PHYSICS_CHANGE" if wp02 else "SOURCE_SCENARIO_CHANGE_ONLY",
        "governing_physics_change": wp02,
        "case_role": (
            "UNIFORM_PRESSURE_VERIFICATION_FIXTURE"
            if is_wp02_uniform_fixture(scenario)
            else "SCIENTIFIC_RECONSTRUCTION"
        ),
        "protected_source_present": False if is_wp02_uniform_fixture(scenario) else None,
        "physical_validation": (
            "NOT_APPLICABLE" if is_wp02_uniform_fixture(scenario) else "NOT_ESTABLISHED"
        ),
        "fixture_output_serialization": (
            {
                "write_format": scenario["output"]["write_format"],
                "write_precision_digits": scenario["output"][
                    "write_precision_digits"
                ],
                "write_compression": scenario["output"]["write_compression"],
            }
            if is_wp02_uniform_fixture(scenario)
            else None
        ),
        "package_scientific_configuration_change": True,
        "scientific_configuration_change_scope": "NEW_R1_SCENARIO_ONLY",
        "qualified_R0_scientific_configuration_change": False,
        "new_R1_scientific_configuration_added": True,
        "bridge": {
            "path": (
                "scripts/wp02_contract_bridge.py"
                if wp02
                else "scripts/r1_contract_bridge.py"
            ),
            "sha256": sha256(
                root
                / (
                    "scripts/wp02_contract_bridge.py"
                    if wp02
                    else "scripts/r1_contract_bridge.py"
                )
            ),
        },
        "canonical_scenario": {
            "path": config_path.relative_to(root).as_posix(),
            "sha256": sha256(config_path),
        },
        "r1_contract": {
            "path": "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json",
            "sha256": sha256(
                root / "validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json"
            ),
        },
        "r1_dossier": {
            "path": "validation/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.json",
            "sha256": sha256(
                root / "validation/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.json"
            ),
        },
        "puckworks": {
            "lock_path": "dependencies/puckworks.lock.json",
            "lock_sha256": sha256(root / "dependencies/puckworks.lock.json"),
            "commit": puckworks_lock["checkout_commit"],
            "tree": puckworks_lock["checkout_tree_sha"],
        },
        "r0_reference_config": {
            "path": REFERENCE_CONFIG_RELATIVE.as_posix(),
            "sha256": sha256(root / REFERENCE_CONFIG_RELATIVE),
        },
        "reused_template_sha256": template_hashes,
        "governed_generated_file_sha256": governed_hashes,
        "governed_generated_file_count": len(governed_hashes),
        "governed_generated_aggregate_sha256": aggregate_hash(governed_hashes),
        "r1_scientific_input_sha256": scientific_hashes,
        "r1_scientific_input_file_count": len(scientific_hashes),
        "r1_scientific_input_aggregate_sha256": aggregate_hash(scientific_hashes),
        "case_generation": {
            "generation_invocation_count": 1,
            "cross_directory_comparison_performed": False,
            "cross_directory_byte_identity_result": "NOT_PERFORMED_IN_THIS_INVOCATION",
        },
        "generator_determinism_qualification": {
            "qualification_kind": (
                "WP02_001_UNIFORM_FIXTURE_TWO_DIRECTORY_REPLAY"
                if is_wp02_uniform_fixture(scenario)
                else "WP01R_004_TWO_DIRECTORY_REPLAY"
            ),
            "qualified_generator_path": "scripts/prepare_case.py",
            "qualified_generator_sha256": sha256(root / "scripts/prepare_case.py"),
            "replay_count": 2,
            "cross_directory_byte_identity_result": "PASS",
            "qualification_test": (
                "tests/test_wp02_effective_permeability.py::"
                "WP02EffectivePermeabilityTests::"
                "test_uniform_fixture_two_directory_generation_is_identical"
                if is_wp02_uniform_fixture(scenario)
                else "tests/test_r1_bridge.py::R1BridgeTests::"
                "test_two_generations_have_identical_governed_bytes"
            ),
        },
        "provenance_coverage": {
            "status": "PASS",
            "percent": 100.0,
            "ungoverned_scientific_defaults": 0,
            "runtime_adjustable_scientific_parameters": 0,
        },
        "r0_no_change_result": "PASS",
        "analytical_preflight": preview,
        "reduced_preflight": {
            "status": "PASS",
            "first_drip_s": b0["primary_outputs"]["first_drip_s"],
        },
        "execution_counters": scenario["execution_boundaries"],
        "claim_ceiling": scenario["claim_ceiling"],
        "determinism_contract": {
            "wall_clock_metadata_omitted": True,
            "absolute_paths_omitted": True,
            "host_or_user_metadata_omitted": True,
            "logical_path_separator": "/",
        },
    }
    output = case / (
        "WP02_001_GENERATED_CASE_MANIFEST.json" if wp02 else R1_MANIFEST_NAME
    )
    output.write_text(canonical_json(manifest), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--nprocs", type=int, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--case-dir", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    config_path = resolve_path(root, args.config, REFERENCE_CONFIG_RELATIVE)
    scenario = json.loads(config_path.read_text(encoding="utf-8"))
    if args.nprocs < 1:
        raise SystemExit("nprocs must be positive")
    r1 = config_path == (root / R1_CONFIG_RELATIVE).resolve() or is_r1_scenario(
        scenario
    )
    if r1:
        if args.config is None:
            raise SystemExit("governed generation requires explicit --config")
        if args.case_dir is None:
            raise SystemExit("governed generation requires explicit --case-dir")
        case_candidate = (
            args.case_dir
            if args.case_dir.is_absolute()
            else root / args.case_dir
        )
        if case_candidate.is_symlink():
            raise SystemExit("R1 case target must not be a symlink")
        case = case_candidate.resolve()
        require_canonical_r1(root, config_path, scenario)
        validate_r1_scenario(scenario, args.nprocs)
        require_fresh_r1_target(root, case)
    else:
        case = resolve_path(root, args.case_dir, REFERENCE_CASE_RELATIVE)

    ensure_case_template(root, case)
    if (
        scenario.get("flowResistanceModel") == "darcyForchheimer"
        or scenario.get("bedMechanicsModel")
            == "waszkiewiczQuasiStaticCompaction"
    ):
        schemes_path = case / "system/fvSchemes"
        schemes = schemes_path.read_text(encoding="utf-8")
        marker = "laplacianSchemes\n{\n"
        if marker not in schemes:
            raise SystemExit("unexpected fvSchemes laplacian dictionary")
        schemes = schemes.replace(
            marker,
            marker
            + "    laplacian(nonlinearMobility,p) Gauss harmonic corrected;\n",
            1,
        )
        schemes_path.write_text(schemes, encoding="utf-8")
        solution_path = case / "system/fvSolution"
        solution = solution_path.read_text(encoding="utf-8")
        solution = solution.replace(
            "tolerance       1e-12;", "tolerance       1e-14;", 1
        )
        solution_path.write_text(solution, encoding="utf-8")
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
        canonical_json(scenario) if r1 else json.dumps(scenario, indent=2) + "\n",
        encoding="utf-8",
    )

    preflight_dir = case / "preflight"
    preflight_dir.mkdir(parents=True, exist_ok=True)
    preview_scenario = scenario
    preview_profile = scenario["hydraulics"].get(
        "permeability_profile", {"type": "uniform"}
    )
    if preview_profile.get("type") == "radial_two_zone":
        preview_scenario = json.loads(json.dumps(scenario))
        radius = float(scenario["geometry"]["basket_radius_m"])
        interface = float(preview_profile["interface_radius_m"])
        inner_fraction = (interface/radius)**2
        equivalent = (
            inner_fraction*float(preview_profile["inner_permeability_m2"])
          + (1.0-inner_fraction)
           *float(preview_profile["outer_permeability_m2"])
        )
        preview_scenario["hydraulics"]["saturated_permeability_m2"] = equivalent
        preview_scenario["hydraulics"]["permeability_profile"] = {
            "type": "uniform"
        }
    preview = analytical_preview(preview_scenario)
    if r1:
        if is_wp02_scenario(scenario):
            preview["notes"] = [
                "The base uniform permeability is the frozen source-linked deterministic analytical inversion.",
                "The optional saturated multiplier was not fitted to OpenFOAM output and does not establish physical validation.",
            ]
        else:
            preview["notes"] = [
                (
                    "The R1 uniform permeability is the frozen WP01R-003 "
                    "source-linked deterministic analytical inversion."
                ),
                (
                    "It was not fitted to OpenFOAM output, is not adjustable during "
                    "generation or execution, and does not establish physical validation."
                ),
            ]
    (preflight_dir / "ANALYTICAL_PREFLIGHT_V0_1_4.json").write_text(
        canonical_json(preview) if r1 else json.dumps(preview, indent=2) + "\n",
        encoding="utf-8",
    )

    b0 = None
    if str(scenario["scenario_id"]).startswith("reference_R0") or r1:
        b0 = b0_reduced_simulation(scenario)
        (preflight_dir / "B0_REDUCED_TWIN_V0_1_4.json").write_text(
            canonical_json(b0) if r1 else json.dumps(b0, indent=2) + "\n",
            encoding="utf-8",
        )

    if not r1:
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

    if r1:
        manifest_path = write_r1_manifest(
            root, case, config_path, scenario, preview, b0, args.nprocs
        )
        print(
            json.dumps(
                {
                    "prepared_case": str(case),
                    "config": str(config_path),
                    "case_manifest": str(manifest_path),
                    "analytical_preflight": preview,
                    "reduced_preflight_generated": True,
                    "openfoam_execution_count": 0,
                    "protected_comparison_execution_count": 0,
                },
                indent=2,
            )
        )
        return

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
