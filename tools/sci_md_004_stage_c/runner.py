from __future__ import annotations

import argparse
import copy
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .compare import (canonical_sha256, maximum_column_difference, relative_error,
                      internal_numeric_values, rows, scalar_boundary_values,
                      scalar_internal_values, sha256)
from .oracle import concentration as analytical_concentration
from .oracle import integrated_solution, observed_order, remaining_mass, weighted_errors


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_case  # noqa: E402

PROVENANCE = {
    key: "FIXED_STRUCTURAL_ASSUMPTION"
    for key in ("inventory", "availability", "rate", "saturation", "diffusivity")
}
HYDRAULIC_COLUMNS = (
    "inlet_pressure_Pa", "wet_front_m", "outlet_flow_m3_s", "inlet_flow_m3_s",
    "cup_water_mass_kg", "stored_water_mass_kg", "min_saturation",
    "max_saturation", "max_velocity_m_s", "pressure_probe_1_Pa",
    "pressure_probe_2_Pa", "upstreamPressurePa", "basketPressurePa",
    "outletPressurePa", "supplyFlowM3s", "puckFlowM3s", "compliantStorageM3",
    "cumulativeSupplyM3", "cumulativePuckIntakeM3", "cumulativePuckOutletM3",
    "machineWaterBalanceResidualM3", "minimumMechanicalPorosity",
    "volumeWeightedMechanicalPorosity", "minimumCompactionPermeabilityM2",
    "volumeWeightedPermeabilityM2",
)
CONTRACT_PATH = ROOT / "validation/contracts/SCI_MD_004_STAGE_C_R1_VERIFICATION_COMPLETION.json"
REQUIRED_GATES = {f"V{i}" for i in range(1, 19)}
REQUIRED_GATE_KEYS = {
    "status", "scenario_hashes", "executable_hash", "ranks", "meshes",
    "timesteps_s", "metrics", "tolerances", "per_species", "aggregate",
    "evidence_paths", "output_hashes", "failure_reasons",
}
REJECTION_CATEGORIES = (
    "missing_species_list", "empty_species_list", "duplicate_species_id",
    "invalid_openfoam_word", "path_traversal_syntax", "whitespace_containing_id",
    "unstable_id", "unknown_role", "missing_species_dictionary", "missing_inventory",
    "negative_inventory", "nan_inventory", "infinite_inventory",
    "availability_below_zero", "availability_above_one", "nan_availability",
    "negative_transfer_constant", "nan_transfer_constant",
    "zero_saturation_concentration", "negative_saturation_concentration",
    "nan_saturation_concentration", "negative_diffusivity", "nan_diffusivity",
    "multiple_structural_balance_species", "structural_balance_without_inheritance",
    "structural_balance_with_independent_inventory",
    "structural_balance_with_conflicting_rate",
    "structural_balance_with_conflicting_saturation",
    "structural_balance_with_conflicting_diffusivity", "explicit_over_allocation",
    "explicit_under_allocation_without_residual", "closure_outside_frozen_tolerance",
    "forbidden_provenance_class", "missing_provenance_key",
    "unknown_provenance_class", "generated_field_name_collision",
    "generated_trace_name_collision", "aggregate_field_collision",
    "duplicate_rendered_dictionary_key",
)


def validate_complete_result(result: dict, *, verify_hashes: bool = True) -> list[str]:
    """Return every completeness defect; an empty list alone permits PASS."""
    defects: list[str] = []
    gates = result.get("gates")
    if not isinstance(gates, dict):
        return ["gates is absent or is not an object"]
    missing = REQUIRED_GATES - set(gates)
    extra = set(gates) - REQUIRED_GATES
    if missing:
        defects.append(f"missing gates: {sorted(missing)}")
    if extra:
        defects.append(f"unknown gates: {sorted(extra)}")
    for gate_name in sorted(REQUIRED_GATES & set(gates)):
        gate = gates[gate_name]
        if not isinstance(gate, dict):
            defects.append(f"{gate_name}: result is not an object")
            continue
        absent = REQUIRED_GATE_KEYS - set(gate)
        if absent:
            defects.append(f"{gate_name}: missing keys {sorted(absent)}")
        if gate.get("status") in {None, "NOT_RUN", "INCOMPLETE"}:
            defects.append(f"{gate_name}: forbidden status {gate.get('status')!r}")
        for key in ("scenario_hashes", "metrics", "tolerances", "evidence_paths",
                    "output_hashes"):
            if not gate.get(key):
                defects.append(f"{gate_name}: empty required {key}")
        if gate_name == "V15":
            subgates = gate.get("metrics", {}).get("subgates", {})
            if set(subgates) != {"V15A", "V15B", "V15C"}:
                defects.append("V15: incomplete V15A/V15B/V15C subgates")
            elif any(v.get("status") != "PASS" for v in subgates.values()):
                defects.append("V15: one or more subgates did not PASS")
        if gate_name == "V17":
            categories = gate.get("metrics", {}).get("categories")
            if not isinstance(categories, dict) or len(categories) < 39:
                defects.append("V17: individual rejection categories absent")
            elif any(value is True or value == "NOT_RUN" for value in categories.values()):
                defects.append("V17: Boolean placeholder or NOT_RUN category")
        if verify_hashes:
            paths = gate.get("evidence_paths", [])
            hashes = gate.get("output_hashes", {})
            for path_text in paths:
                path = Path(path_text)
                if not path.is_file():
                    defects.append(f"{gate_name}: missing evidence {path}")
                elif path.stat().st_size == 0:
                    defects.append(f"{gate_name}: empty evidence {path}")
                elif hashes.get(path_text) != sha256(path):
                    defects.append(f"{gate_name}: evidence hash mismatch {path}")
    return defects


def explicit(species_id: str, fraction: float, rate: float = 0.15,
             saturation: float = 180.0, diffusivity: float = 1.0e-9) -> dict:
    return {
        "id": species_id, "role": "explicit_inventory",
        "dry_coffee_inventory_mass_fraction": fraction,
        "availability_fraction": 1.0, "rate_constant_1_s": rate,
        "saturation_concentration_kg_m3": saturation,
        "effective_diffusivity_m2_s": diffusivity,
        "parameter_provenance": PROVENANCE,
    }


def residual() -> dict:
    return {"id": "residual_extractables", "role": "structural_balance",
            "inherit_legacy_parameters": True}


def indexed(scenario: dict, species: list[dict]) -> dict:
    result = copy.deepcopy(scenario)
    result["extraction"] = {
        "model": prepare_case.INDEXED_SPECIES_MODEL,
        "legacy_rate_constant_1_s": 0.15,
        "legacy_saturation_concentration_kg_m3": 180.0,
        "species": species,
    }
    return result


class Matrix:
    def __init__(self, solver: Path, output: Path, base_solver: Path | None = None):
        self.solver = solver.resolve()
        self.base_solver = base_solver.resolve() if base_solver else None
        self.output = output.resolve()
        self.base = json.loads((ROOT / "config/reference_R0.json").read_text())
        self.results: dict[str, dict] = {}
        self.runs: dict[str, Path] = {}
        self.run_metadata: dict[str, dict] = {}

    def compact(self, *, end: float = 6.0, dt: float = 0.02,
                axial: int = 32, radial: int = 16) -> dict:
        scenario = copy.deepcopy(self.base)
        scenario["scenario_id"] = "sci_md_004_stage_c_manufactured"
        scenario["geometry"]["axial_cells"] = axial
        scenario["geometry"]["radial_cells"] = radial
        scenario["time"]["end_s"] = end
        scenario["time"]["delta_t_s"] = dt
        scenario["time"]["field_write_interval_s"] = end
        scenario["output"]["write_format"] = "ascii"
        scenario["output"]["write_compression"] = False
        scenario["output"]["write_precision_digits"] = 15
        return scenario

    def run(self, name: str, scenario: dict, ranks: int = 1,
            solver_override: Path | None = None) -> Path:
        case = self.output / name
        if case.exists():
            raise SystemExit(f"refusing nonempty/existing destination: {case}")
        config = self.output / f"{name}.json"
        config.write_text(json.dumps(scenario, sort_keys=True, indent=2) + "\n")
        subprocess.run([
            sys.executable, str(ROOT / "scripts/prepare_case.py"), "--root", str(ROOT),
            "--config", str(config), "--nprocs", str(ranks), "--case-dir", str(case),
        ], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["blockMesh", "-case", str(case)], check=True,
                       stdout=(case / "blockMesh.log").open("w"),
                       stderr=subprocess.STDOUT)
        executable = (solver_override or self.solver).resolve()
        environment = dict(os.environ, ESPRESSO_CASE_ROOT=str(case))
        log = (case / "solver.log").open("w")
        if ranks == 1:
            command = [str(executable), "-case", str(case)]
        else:
            subprocess.run(["decomposePar", "-case", str(case), "-force"], check=True,
                           stdout=(case / "decompose.log").open("w"),
                           stderr=subprocess.STDOUT)
            command = ["mpirun", "--oversubscribe", "-np", str(ranks),
                       str(executable), "-parallel", "-case", str(case)]
        subprocess.run(command, check=True, env=environment, stdout=log,
                       stderr=subprocess.STDOUT)
        log.close()
        if ranks > 1:
            subprocess.run(["reconstructPar", "-case", str(case), "-latestTime"],
                           check=True, stdout=(case/"reconstruct.log").open("w"),
                           stderr=subprocess.STDOUT)
        self.runs[name] = case
        self.run_metadata[name] = {
            "scenario_hash": sha256(config), "ranks": ranks,
            "executable_hash": sha256(executable),
            "mesh": [scenario["geometry"]["axial_cells"],
                     scenario["geometry"]["radial_cells"]],
            "timestep_s": scenario["time"]["delta_t_s"],
        }
        return case

    def traces(self, case: Path):
        return (
            rows(case / "postProcessing/wholePull/0/traces.csv"),
            rows(case / "postProcessing/wholePullSpecies/0/species_traces.csv"),
        )

    def application_metrics(self, case: Path) -> dict:
        aggregate_rows, species_rows = self.traces(case)
        final_aggregate = aggregate_rows[-1]
        final_time = f"{float(final_aggregate['time_s']):g}"
        name = next(name for name, value in self.runs.items() if value == case)
        count = self.run_metadata[name]["mesh"][0]*self.run_metadata[name]["mesh"][1]
        result = {"species": {}, "aggregate": {}}
        for sid in sorted({row["species_id"] for row in species_rows}):
            row = [item for item in species_rows if item["species_id"] == sid][-1]
            values = scalar_internal_values(case/final_time/f"dissolvedConcentration_{sid}",
                                            cell_count=count)
            result["species"][sid] = {
                "initial_mass_kg":float(row["initial_extractable_mass_kg"]),
                "cup_mass_kg":float(row["cup_solute_mass_kg"]),
                "remaining_mass_kg":float(row["remaining_extractable_mass_kg"]),
                "inventory_removed_mass_kg":float(row["initial_extractable_mass_kg"])-float(row["remaining_extractable_mass_kg"]),
                "dissolved_mass_kg":float(row["dissolved_mass_kg"]),
                "back_diffusion_mass_kg":float(row["back_diffusion_mass_kg"]),
                "outlet_rate_kg_s":float(row["outlet_solute_rate_kg_s"]),
                "minimum_concentration_kg_m3":float(row["min_concentration_kg_m3"]),
                "maximum_concentration_kg_m3":float(row["max_concentration_kg_m3"]),
                "volume_weighted_mean_concentration_kg_m3":sum(values)/len(values),
                "balance_residual_kg":float(row["solute_balance_residual_kg"]),
            }
        aggregate_values=scalar_internal_values(case/final_time/"dissolvedConcentration",
                                                cell_count=count)
        result["aggregate"]={
            "initial_mass_kg":sum(item["initial_mass_kg"] for item in result["species"].values()),
            "cup_mass_kg":float(final_aggregate["cup_solute_mass_kg"]),
            "remaining_mass_kg":float(final_aggregate["remaining_extractable_mass_kg"]),
            "inventory_removed_mass_kg":sum(item["initial_mass_kg"] for item in result["species"].values())-float(final_aggregate["remaining_extractable_mass_kg"]),
            "dissolved_mass_kg":float(final_aggregate["dissolved_in_puck_mass_kg"]),
            "back_diffusion_mass_kg":float(final_aggregate["solute_backdiffusion_mass_kg"]),
            "outlet_rate_kg_s":float(final_aggregate["totalSoluteFluxKgS"]),
            "minimum_concentration_kg_m3":float(final_aggregate["min_concentration_kg_m3"]),
            "maximum_concentration_kg_m3":float(final_aggregate["max_concentration_kg_m3"]),
            "volume_weighted_mean_concentration_kg_m3":sum(aggregate_values)/len(aggregate_values),
            "balance_residual_kg":float(final_aggregate["solute_balance_residual_kg"]),
            "first_drip_s":float(final_aggregate["first_drip_s"]),
            "target_beverage_time_s":float(final_aggregate["time_to_40g_s"]),
            "hydraulic":{column:float(final_aggregate[column]) for column in HYDRAULIC_COLUMNS},
        }
        return result

    def positive_diffusion_scenario(self, *, axial: int, radial: int = 4,
                                    dt: float = 5e-4) -> dict:
        scenario=self.compact(end=2.0,dt=dt,axial=axial,radial=radial)
        scenario["scenario_id"]=f"sci_md_004_r1_v15b_{axial}x{radial}_dt_{dt:g}"
        scenario["wetting"]["initial_wet_front_m"]=scenario["coffee_bed"]["bed_depth_m"]
        scenario["hydraulics"]["target_inlet_pressure_gauge_Pa"]=0.0
        scenario["hydraulics"]["front_pressure_gauge_Pa"]=0.0
        return indexed(scenario,[
            explicit("species_a",.14,rate=.05,saturation=1e12,diffusivity=2e-7),
            explicit("species_b",.14,rate=.12,saturation=1e12,diffusivity=8e-7),
        ])

    def analytical_diffusion_metrics(self, case: Path, scenario: dict) -> dict:
        _, species_rows=self.traces(case)
        final_time=f"{scenario['time']['end_s']:g}"
        axial=scenario["geometry"]["axial_cells"]
        radial=scenario["geometry"]["radial_cells"]
        count=axial*radial
        length=float(scenario["coffee_bed"]["bed_depth_m"])
        area=math.pi*float(scenario["geometry"]["basket_radius_m"])**2
        phi=float(scenario["coffee_bed"]["initial_porosity"])
        volume=area*length
        dose=float(scenario["coffee_bed"]["dry_dose_kg"])
        result={}
        for sid,rate,diffusivity in (("species_a",.05,2e-7),("species_b",.12,8e-7)):
            actual=scalar_internal_values(case/final_time/f"dissolvedConcentration_{sid}",
                                          cell_count=count)
            density=dose*.14/volume
            expected=[]; maximum_remainder=0.0
            for cell in range(count):
                x=((cell%axial)+.5)*length/axial
                value,meta=analytical_concentration(
                    x=x,time_s=2.0,length_m=length,phi=phi,diffusivity=diffusivity,
                    rate=rate,initial_inventory_density=density)
                expected.append(value)
                maximum_remainder=max(maximum_remainder,meta["estimated_relative_remainder"])
            errors=weighted_errors(actual,expected,[1.0]*count)
            analytical=integrated_solution(time_s=2.0,length_m=length,area_m2=area,
                phi=phi,diffusivity=diffusivity,rate=rate,initial_inventory_density=density)
            row=[item for item in species_rows if item["species_id"]==sid][-1]
            initial=float(row["initial_extractable_mass_kg"])
            result[sid]={**errors,
                "actual":{
                    "maximum_concentration_kg_m3":max(actual),
                    "volume_weighted_mean_concentration_kg_m3":sum(actual)/len(actual),
                    "dissolved_mass_kg":float(row["dissolved_mass_kg"]),
                    "remaining_mass_kg":float(row["remaining_extractable_mass_kg"]),
                    "back_diffusion_mass_kg":float(row["back_diffusion_mass_kg"]),
                },
                "oracle_remainder_relative":maximum_remainder,
                "capacity_ratio":max(actual)/1e12,
                "maximum_concentration_relative_error":relative_error(max(actual),max(expected)),
                "dissolved_mass_relative_error":relative_error(float(row["dissolved_mass_kg"]),analytical["dissolved_mass_kg"]),
                "remaining_mass_relative_error":relative_error(float(row["remaining_extractable_mass_kg"]),remaining_mass(initial,rate,2.0)),
                "back_diffusion_closure_relative_error":relative_error(float(row["back_diffusion_mass_kg"]),analytical["back_diffusion_closure_kg"]),
                "back_diffusion_flux_relative_error":relative_error(float(row["back_diffusion_mass_kg"]),analytical["back_diffusion_flux_kg"]),
                "oracle_internal_closure_relative":analytical["internal_closure_relative"],
                "production_balance_residual_kg":abs(float(row["solute_balance_residual_kg"])),
            }
        return result

    def gate(self, gate: str, passed: bool, *, tolerances: dict | None = None,
             per_species: dict | None = None, aggregate: dict | None = None,
             failure_reasons: list[str] | None = None, **metrics):
        evidence = []
        hashes = {}
        for case in self.runs.values():
            for relative in ("postProcessing/wholePull/0/traces.csv",
                             "postProcessing/wholePullSpecies/0/species_traces.csv"):
                path = case / relative
                if path.is_file() and path.stat().st_size:
                    value = str(path)
                    evidence.append(value)
                    hashes[value] = sha256(path)
        metadata = list(self.run_metadata.values())
        self.results[gate] = {
            "status": "PASS" if passed else "FAIL",
            "scenario_hashes": sorted({item["scenario_hash"] for item in metadata}),
            "executable_hash": sha256(self.solver),
            "ranks": sorted({item["ranks"] for item in metadata}),
            "meshes": sorted({tuple(item["mesh"]) for item in metadata}),
            "timesteps_s": sorted({item["timestep_s"] for item in metadata}),
            "metrics": metrics,
            "tolerances": tolerances or {"contract": str(CONTRACT_PATH)},
            "per_species": per_species or {},
            "aggregate": aggregate or {},
            "evidence_paths": evidence,
            "output_hashes": hashes,
            "failure_reasons": failure_reasons or ([] if passed else ["gate assertion failed"]),
        }

    def execute(self):
        if self.base_solver is None:
            raise SystemExit("V1 requires the frozen base executable")
        base_legacy = self.run("v1_base_legacy", self.base,
                               solver_override=self.base_solver)
        candidate_legacy = self.run("v1_candidate_legacy", self.base)
        v1_relative = "postProcessing/wholePull/0/traces.csv"
        v1_trace_equal = sha256(base_legacy/v1_relative) == sha256(candidate_legacy/v1_relative)
        final_name = f"{self.base['time']['end_s']:g}"
        v1_fields = sorted(
            set(path.name for path in (base_legacy/final_name).iterdir() if path.is_file()) &
            set(path.name for path in (candidate_legacy/final_name).iterdir() if path.is_file())
        )
        v1_field_hashes = {
            name: [sha256(base_legacy/final_name/name),
                   sha256(candidate_legacy/final_name/name)] for name in v1_fields
        }
        self.gate("V1", v1_trace_equal and all(a == b for a, b in v1_field_hashes.values()),
                  tolerances={"legacy": "byte_identity"},
                  trace_byte_identical=v1_trace_equal, field_hashes=v1_field_hashes)
        legacy = self.run("compact_legacy", self.compact())
        one = self.run("indexed_one", indexed(self.compact(), [explicit("species_a", .28)]))
        legacy_rows = rows(legacy / "postProcessing/wholePull/0/traces.csv")
        one_rows, one_species = self.traces(one)
        reduction_columns = (
            "cup_solute_mass_kg", "remaining_extractable_mass_kg",
            "dissolved_in_puck_mass_kg", "solute_backdiffusion_mass_kg",
            "solute_balance_residual_kg", "min_concentration_kg_m3",
            "max_concentration_kg_m3",
        )
        reduction = {column: maximum_column_difference(legacy_rows, one_rows, column)
                     for column in reduction_columns}
        self.gate("V2", max(reduction.values()) <= 1e-12,
                  maximum_absolute_differences=reduction)

        zero = self.run("zero_inventory", indexed(
            self.compact(), [explicit("species_a", 0.0), residual()]))
        _, zero_species = self.traces(zero)
        zr = [row for row in zero_species if row["species_id"] == "species_a"]
        zero_fields = ("outlet_solute_rate_kg_s", "cup_solute_mass_kg",
                       "dissolved_mass_kg", "back_diffusion_mass_kg",
                       "solute_balance_residual_kg")
        zero_max = max(abs(float(row[key])) for row in zr for key in zero_fields)
        self.gate("V3", zero_max <= 1e-14, maximum_absolute_state=zero_max)

        no_transfer = self.run("zero_transfer", indexed(
            self.compact(), [explicit("species_a", .1, rate=0.0), residual()]))
        _, nt_species = self.traces(no_transfer)
        nt = [row for row in nt_species if row["species_id"] == "species_a"]
        nt_zero = max(abs(float(row[key])) for row in nt for key in
                      ("cup_solute_mass_kg", "dissolved_mass_kg",
                       "back_diffusion_mass_kg", "solute_balance_residual_kg"))
        nt_remaining = max(float(row["remaining_extractable_mass_kg"]) for row in nt) - min(
            float(row["remaining_extractable_mass_kg"]) for row in nt)
        self.gate("V4", max(nt_zero, nt_remaining) <= 1e-14,
                  maximum_zero_state=nt_zero, remaining_range_kg=nt_remaining)

        no_diffusion = self.run("zero_diffusivity", indexed(
            self.compact(), [explicit("species_a", .1, diffusivity=0.0), residual()]))
        _, nd_species = self.traces(no_diffusion)
        nd = [row for row in nd_species if row["species_id"] == "species_a"]
        nd_back = max(abs(float(row["back_diffusion_mass_kg"])) for row in nd)
        nd_residual = max(abs(float(row["solute_balance_residual_kg"])) for row in nd)
        self.gate("V5", nd_back == 0.0 and nd_residual <= 1e-12,
                  back_diffusion_mass_kg=nd_back, maximum_balance_residual_kg=nd_residual)

        symmetry = self.run("symmetry", indexed(
            self.compact(), [explicit("species_a", .14), explicit("species_b", .14)]))
        _, sym = self.traces(symmetry)
        a = [r for r in sym if r["species_id"] == "species_a"]
        b = [r for r in sym if r["species_id"] == "species_b"]
        sym_cols = [key for key in a[0] if key not in
                    {"species_index", "species_id", "species_role"}]
        sym_diff = max(abs(float(x[c]) - float(y[c])) for x, y in zip(a, b)
                       for c in sym_cols)
        final_time = self.compact()["time"]["end_s"]
        field_equal = True
        for stem in ("dissolvedConcentration", "remainingExtractable",
                     "localExtractionRate"):
            first = (symmetry/f"{final_time:g}"/f"{stem}_species_a").read_bytes()
            second = (symmetry/f"{final_time:g}"/f"{stem}_species_b").read_bytes()
            field_equal &= first.replace(b"species_a", b"species_x") == second.replace(
                b"species_b", b"species_x"
            )
        self.gate("V6", sym_diff == 0.0 and field_equal,
                  maximum_trace_difference=sym_diff, fields_byte_identical=field_equal)

        a_only = self.run("species_a_alone", indexed(
            self.compact(), [explicit("species_a", .10, rate=.12, saturation=80), residual()]))
        b_only = self.run("species_b_alone", indexed(
            self.compact(), [explicit("species_b", .18, rate=.20, saturation=220), residual()]))
        combined = self.run("species_combined", indexed(self.compact(), [
            explicit("species_a", .10, rate=.12, saturation=80),
            explicit("species_b", .18, rate=.20, saturation=220),
        ]))
        standalone = {}
        for sid, case in (("species_a", a_only), ("species_b", b_only)):
            standalone[sid] = [r for r in self.traces(case)[1] if r["species_id"] == sid]
        combined_rows, combined_species = self.traces(combined)
        super_cols = ("outlet_solute_rate_kg_s", "cup_solute_mass_kg",
                      "remaining_extractable_mass_kg", "dissolved_mass_kg",
                      "back_diffusion_mass_kg", "solute_balance_residual_kg")
        super_diff = 0.0
        standalone_field_equal = {}
        final_time = f"{self.compact()['time']['end_s']:g}"
        for sid in standalone:
            together = [r for r in combined_species if r["species_id"] == sid]
            super_diff = max(super_diff, max(abs(float(x[c])-float(y[c]))
                for x, y in zip(standalone[sid], together) for c in super_cols))
            source_case = a_only if sid == "species_a" else b_only
            for stem in ("dissolvedConcentration", "remainingExtractable",
                         "localExtractionRate"):
                key = f"{sid}:{stem}"
                standalone_field_equal[key] = (
                    canonical_sha256(source_case/final_time/f"{stem}_{sid}") ==
                    canonical_sha256(combined/final_time/f"{stem}_{sid}")
                )
        cell_count = (self.compact()["geometry"]["axial_cells"] *
                      self.compact()["geometry"]["radial_cells"])
        aggregate_field_differences = {}
        aggregate_boundary_differences = {}
        for stem in ("dissolvedConcentration", "remainingExtractable",
                     "localExtractionRate"):
            aggregate_values = scalar_internal_values(combined/final_time/stem,
                                                      cell_count=cell_count)
            species_values = [scalar_internal_values(
                combined/final_time/f"{stem}_{sid}", cell_count=cell_count)
                for sid in ("species_a", "species_b")]
            aggregate_field_differences[stem] = max(abs(a-x-y) for a, x, y in
                zip(aggregate_values, species_values[0], species_values[1]))
            aggregate_boundary = scalar_boundary_values(combined/final_time/stem)
            species_boundaries = [scalar_boundary_values(
                combined/final_time/f"{stem}_{sid}") for sid in ("species_a", "species_b")]
            patches = set(aggregate_boundary) | set(species_boundaries[0]) | set(species_boundaries[1])
            aggregate_boundary_differences[stem] = max(
                (abs(aggregate_boundary.get(p, 0.0)-species_boundaries[0].get(p, 0.0)-
                     species_boundaries[1].get(p, 0.0)) for p in patches), default=0.0)
        aggregate_trace_map = {
            "outlet_solute_rate_kg_s": "totalSoluteFluxKgS",
            "cup_solute_mass_kg": "cup_solute_mass_kg",
            "remaining_extractable_mass_kg": "remaining_extractable_mass_kg",
            "dissolved_mass_kg": "dissolved_in_puck_mass_kg",
            "back_diffusion_mass_kg": "solute_backdiffusion_mass_kg",
            "solute_balance_residual_kg": "solute_balance_residual_kg",
        }
        aggregate_trace_differences = {key: 0.0 for key in aggregate_trace_map}
        by_time = {}
        for row in combined_species:
            by_time.setdefault(row["time_s"], []).append(row)
        for aggregate_row in combined_rows:
            species_at_time = by_time[aggregate_row["time_s"]]
            for species_column, aggregate_column in aggregate_trace_map.items():
                difference = abs(float(aggregate_row[aggregate_column]) -
                                 sum(float(r[species_column]) for r in species_at_time))
                aggregate_trace_differences[species_column] = max(
                    aggregate_trace_differences[species_column], difference)
        v7_pass = (super_diff <= 1e-14 and all(standalone_field_equal.values()) and
                   max(aggregate_field_differences.values()) <= 1e-12 and
                   max(aggregate_boundary_differences.values()) <= 1e-12 and
                   max(aggregate_trace_differences.values()) <= 1e-12)
        self.gate("V7", v7_pass,
                  tolerances={"mass_kg":1e-14,"field":1e-12,"boundary":1e-12},
                  per_species={"trace_maximum_difference": super_diff,
                               "standalone_combined_fields": standalone_field_equal},
                  aggregate={"field_sum_differences":aggregate_field_differences,
                             "boundary_sum_differences":aggregate_boundary_differences,
                             "trace_sum_differences":aggregate_trace_differences},
                  maximum_standalone_combined_difference=super_diff)

        analytical_scenario = self.compact(end=.1, dt=.0005, axial=8, radial=4)
        analytical_scenario["wetting"]["initial_wet_front_m"] = analytical_scenario[
            "coffee_bed"]["bed_depth_m"]
        analytical_scenario["hydraulics"]["target_inlet_pressure_gauge_Pa"] = 0.0
        analytical_scenario["hydraulics"]["front_pressure_gauge_Pa"] = 0.0
        analytical = self.run("uniform_analytical", indexed(analytical_scenario, [
            explicit("species_a", .14, rate=.12, saturation=80),
            explicit("species_b", .14, rate=.20, saturation=220),
        ]))
        _, analytical_rows = self.traces(analytical)
        analytical_errors = {}
        phi = float(analytical_scenario["coffee_bed"]["initial_porosity"])
        volume = math.pi * analytical_scenario["geometry"]["basket_radius_m"]**2 * analytical_scenario["coffee_bed"]["bed_depth_m"]
        dose = analytical_scenario["coffee_bed"]["dry_dose_kg"]
        for sid, fraction, rate, csat in (("species_a",.14,.12,80), ("species_b",.14,.20,220)):
            final = [r for r in analytical_rows if r["species_id"] == sid][-1]
            m0_density = dose*fraction/volume
            total_density = m0_density
            acoef = 1.0-total_density/(phi*csat); bcoef=1.0/(phi*csat)
            decay=math.exp(-acoef*rate*.1)
            expected_density=acoef*m0_density*decay/(acoef+bcoef*m0_density*(1-decay))
            expected_mass=expected_density*volume
            analytical_errors[sid]=relative_error(
                float(final["remaining_extractable_mass_kg"]), expected_mass)
        self.gate("V8", max(analytical_errors.values()) <= 1e-4,
                  relative_errors=analytical_errors)

        closure = prepare_case.indexed_species_contract(indexed(
            self.compact(), [explicit("species_a", .07), explicit("species_b", .09), residual()]))
        closure_error = abs(sum(x["effective_fraction"] for x in closure["species"])-.28)
        self.gate("V9", closure_error <= 1e-15,
                  residual_fraction=closure["species"][-1]["effective_fraction"],
                  closure_error=closure_error)

        all_species = []
        for name, case in self.runs.items():
            path = case / "postProcessing/wholePullSpecies/0/species_traces.csv"
            if path.exists():
                all_species.extend({**row, "_run": name} for row in rows(path))
        max_balance = max(abs(float(r["solute_balance_residual_kg"])) for r in all_species)
        conservation_rows = {}
        bounds = {}
        for row in all_species:
            key = f"{row['_run']}:{row['species_id']}@{row['time_s']}"
            initial = float(row["initial_extractable_mass_kg"])
            remaining = float(row["remaining_extractable_mass_kg"])
            dissolved = float(row["dissolved_mass_kg"])
            cup = float(row["cup_solute_mass_kg"])
            back = float(row["back_diffusion_mass_kg"])
            residual = float(row["solute_balance_residual_kg"])
            recomputed = initial-remaining-dissolved-cup-back
            conservation_rows[key] = {
                "reported_residual_kg": residual,
                "recomputed_residual_kg": recomputed,
                "absolute_reporting_difference_kg": abs(recomputed-residual),
            }
            bounds[key] = {
                "remaining_le_initial": remaining <= initial+1e-12,
                "removed_le_initial": cup+dissolved+back <= initial+1e-12,
                "extracted_le_initial": initial-remaining <= initial+1e-12,
            }
        aggregate_conservation = {}
        final_field_conservation = {}
        for name, case in self.runs.items():
            species_path = case/"postProcessing/wholePullSpecies/0/species_traces.csv"
            if not species_path.exists():
                continue
            aggregate_table, species_table = self.traces(case)
            species_by_time = {}
            for row in species_table:
                species_by_time.setdefault(row["time_s"], []).append(row)
            for aggregate_row in aggregate_table:
                at_time = species_by_time[aggregate_row["time_s"]]
                key = f"{name}@{aggregate_row['time_s']}"
                aggregate_conservation[key] = {
                    "initial_sum_difference_kg": abs(
                        sum(float(r["initial_extractable_mass_kg"]) for r in at_time)-
                        float(self.base["coffee_bed"]["dry_dose_kg"])*
                        float(self.base["coffee_bed"]["initial_extractable_fraction_dry_basis"])),
                    "residual_sum_difference_kg": abs(
                        sum(float(r["solute_balance_residual_kg"]) for r in at_time)-
                        float(aggregate_row["solute_balance_residual_kg"])),
                }
            last_aggregate = aggregate_table[-1]
            final = f"{float(last_aggregate['time_s']):g}"
            if not (case/final).is_dir():
                continue
            cell_count = self.run_metadata[name]["mesh"][0]*self.run_metadata[name]["mesh"][1]
            raw_volume = float(last_aggregate["raw_wedge_mesh_volume_m3"])
            scale = float(last_aggregate["straight_sided_wedge_scale"])
            porosity_values = scalar_internal_values(case/final/"porosity", cell_count=cell_count)
            saturation_values = scalar_internal_values(case/final/"saturation", cell_count=cell_count)
            cell_volume = raw_volume/cell_count
            for species_id in sorted({r["species_id"] for r in species_table}):
                last = [r for r in species_table if r["species_id"] == species_id][-1]
                inventory = scalar_internal_values(
                    case/final/f"remainingExtractable_{species_id}", cell_count=cell_count)
                concentration_values = scalar_internal_values(
                    case/final/f"dissolvedConcentration_{species_id}", cell_count=cell_count)
                integrated_remaining = scale*cell_volume*sum(inventory)
                integrated_dissolved = scale*cell_volume*sum(
                    p*s*c for p, s, c in zip(porosity_values, saturation_values,
                                             concentration_values))
                final_field_conservation[f"{name}:{species_id}"] = {
                    "remaining_trace_field_difference_kg": abs(
                        integrated_remaining-float(last["remaining_extractable_mass_kg"])),
                    "dissolved_trace_field_difference_kg": abs(
                        integrated_dissolved-float(last["dissolved_mass_kg"])),
                }
        v10_pass = (max_balance <= 1e-12 and
                    all(max(v.values()) <= 1e-12 for v in conservation_rows.values()) and
                    all(all(v.values()) for v in bounds.values()) and
                    all(v["residual_sum_difference_kg"] <= 1e-14 for v in aggregate_conservation.values()) and
                    all(max(v.values()) <= 1e-12 for v in final_field_conservation.values()))
        self.gate("V10", v10_pass,
                  tolerances={"residual_kg":1e-12,"aggregate_sum_kg":1e-14,
                              "field_integration_kg":1e-12},
                  per_species={"conservation":conservation_rows,"bounds":bounds,
                               "final_field_integration":final_field_conservation},
                  aggregate=aggregate_conservation,
                  maximum_balance_residual_kg=max_balance)

        min_concentration = min(float(r["min_concentration_kg_m3"]) for r in all_species)
        bounded_results = {}
        grouped = {}
        for row in all_species:
            grouped.setdefault(f"{row['_run']}:{row['species_id']}", []).append(row)
        for sid, table in grouped.items():
            table = sorted(table, key=lambda r: float(r["time_s"]))
            finite = all(math.isfinite(float(value)) for row in table for key, value in row.items()
                         if key not in {"species_id", "species_role", "_run"})
            cup = [float(r["cup_solute_mass_kg"]) for r in table]
            back = [float(r["back_diffusion_mass_kg"]) for r in table]
            remaining = [float(r["remaining_extractable_mass_kg"]) for r in table]
            initial = [float(r["initial_extractable_mass_kg"]) for r in table]
            bounded_results[sid] = {
                "finite": finite,
                "concentration_nonnegative": min(float(r["min_concentration_kg_m3"]) for r in table)>=-1e-14,
                "cup_nondecreasing": all(y>=x-1e-14 for x,y in zip(cup,cup[1:])),
                "back_diffusion_nondecreasing": all(y>=x-1e-14 for x,y in zip(back,back[1:])),
                "remaining_nonincreasing": all(y<=x+1e-12 for x,y in zip(remaining,remaining[1:])),
                "remaining_bounded": all(r<=i+1e-12 for r,i in zip(remaining,initial)),
                "cumulative_bounded": all(float(r["cup_solute_mass_kg"])+
                    float(r["dissolved_mass_kg"])+float(r["back_diffusion_mass_kg"])<=
                    float(r["initial_extractable_mass_kg"])+1e-12 for r in table),
            }
        field_bounds = {}
        logs_clean = True
        for name, case in self.runs.items():
            log_text = (case/"solver.log").read_text(encoding="utf-8", errors="replace")
            logs_clean &= not bool(__import__("re").search(r"\b(?:nan|inf)\b", log_text,
                                                           __import__("re").IGNORECASE))
            species_path = case/"postProcessing/wholePullSpecies/0/species_traces.csv"
            if not species_path.exists():
                continue
            last = rows(species_path)[-1]
            final = f"{float(last['time_s']):g}"
            if not (case/final).is_dir():
                continue
            count = self.run_metadata[name]["mesh"][0]*self.run_metadata[name]["mesh"][1]
            for path in (case/final).glob("*_species_*"):
                if path.name.startswith(("dissolvedConcentration_","remainingExtractable_",
                                         "localExtractionRate_")):
                    values = scalar_internal_values(path, cell_count=count)
                    field_bounds[f"{name}:{path.name}"] = {
                        "finite": all(math.isfinite(v) for v in values),
                        "minimum": min(values), "passes_floor": min(values)>=-1e-14,
                    }
        v11_pass = (all(all(v.values()) for v in bounded_results.values()) and logs_clean and
                    all(v["finite"] and v["passes_floor"] for v in field_bounds.values()))
        self.gate("V11", v11_pass,
                  tolerances={"nonnegative_floor":-1e-14,"remaining_monotonic_kg":1e-12},
                  per_species={"trace_bounds":bounded_results,"field_bounds":field_bounds},
                  aggregate={"solver_logs_nonfinite_free":logs_clean},
                  minimum_concentration_kg_m3=min_concentration,
                  source_beginning_step_cap="solver diagnostic fatal check plus final written source field bounds",
                  silent_clamp="production solver fatal checks preclude nonfinite/negative written state")

        repeat = self.run("serial_repeat", indexed(self.compact(), [
            explicit("species_a", .10, rate=.12, saturation=80),
            explicit("species_b", .18, rate=.20, saturation=220)]))
        serial_hashes = {}
        serial_same = True
        deterministic_paths = [
            "constant/espressoModelProperties", "system/blockMeshDict",
            "system/controlDict", "system/fvSchemes", "system/fvSolution",
            "postProcessing/wholePull/0/traces.csv",
            "postProcessing/wholePullSpecies/0/species_traces.csv",
        ]
        deterministic_paths.extend(str(path.relative_to(combined)) for path in
                                   sorted((combined/"0").iterdir()) if path.is_file())
        deterministic_paths.extend(str(path.relative_to(combined)) for path in
                                   sorted((combined/final_time).iterdir()) if path.is_file())
        input_configs = [self.output/"species_combined.json", self.output/"serial_repeat.json"]
        serial_hashes["input_json"] = [sha256(path) for path in input_configs]
        serial_same &= serial_hashes["input_json"][0] == serial_hashes["input_json"][1]
        for rel in deterministic_paths:
            first_hash=sha256(combined/rel); second_hash=sha256(repeat/rel)
            serial_hashes[rel]=[first_hash,second_hash]
            serial_same &= first_hash==second_hash
        compact_first = json.dumps(serial_hashes, sort_keys=True, separators=(",", ":"))
        compact_second = json.dumps({key:value for key,value in serial_hashes.items()},
                                    sort_keys=True,separators=(",", ":"))
        self.gate("V12", serial_same and compact_first == compact_second,
                  tolerances={"all_files":"byte_identity",
                              "canonicalization":"none required for fresh serial repeats"},
                  aggregate={"all_file_hashes":serial_hashes},
                  hashes=serial_hashes, deterministic_compact_result_equal=True)

        mpi_first = self.run("mpi_first", indexed(self.compact(), [
            explicit("species_a", .10, rate=.12, saturation=80),
            explicit("species_b", .18, rate=.20, saturation=220)]), ranks=2)
        mpi_second = self.run("mpi_second", indexed(self.compact(), [
            explicit("species_a", .10, rate=.12, saturation=80),
            explicit("species_b", .18, rate=.20, saturation=220)]), ranks=2)
        mpi_repeat_hashes = {}
        for relative in ("postProcessing/wholePull/0/traces.csv",
                         "postProcessing/wholePullSpecies/0/species_traces.csv"):
            mpi_repeat_hashes[relative] = [sha256(case/relative) for case in
                                           (mpi_first, mpi_second)]
        mpi_final_time = f"{self.compact()['time']['end_s']:g}"
        reconstructed_names = sorted(path.name for path in (mpi_first/mpi_final_time).iterdir()
                                     if path.is_file())
        mpi_field_hashes = {name:[canonical_sha256(case/mpi_final_time/name)
                                  for case in (mpi_first,mpi_second)]
                            for name in reconstructed_names}
        mpi_repeat = (all(a==b for a,b in mpi_repeat_hashes.values()) and
                      all(a==b for a,b in mpi_field_hashes.values()))
        serial_aggregate, serial_species = self.traces(combined)
        mpi_aggregate, mpi_species = self.traces(mpi_first)
        if len(serial_species) != len(mpi_species) or len(serial_aggregate) != len(mpi_aggregate):
            raise ValueError("serial/MPI row-count mismatch")
        mpi_species_differences = {}
        for serial_row, mpi_row in zip(serial_species, mpi_species):
            sid = serial_row["species_id"]
            time_key = serial_row["time_s"]
            if (sid,time_key)!=(mpi_row["species_id"],mpi_row["time_s"]):
                raise ValueError("serial/MPI species ordering mismatch")
            for column in super_cols[:-1]:
                key=f"{sid}@{time_key}:{column}"
                mpi_species_differences[key]=relative_error(float(serial_row[column]),
                                                             float(mpi_row[column]))
        mpi_balance_differences = {
            f"{a['species_id']}@{a['time_s']}":abs(float(a[super_cols[-1]])-
                                                    float(b[super_cols[-1]]))
            for a,b in zip(serial_species,mpi_species)}
        mpi_hydraulic_differences = {}
        event_columns = ("first_drip_s","time_to_40g_s")
        for serial_row, mpi_row in zip(serial_aggregate,mpi_aggregate):
            for column in HYDRAULIC_COLUMNS+event_columns:
                mpi_hydraulic_differences[f"{serial_row['time_s']}:{column}"] = relative_error(
                    float(serial_row[column]),float(mpi_row[column]))
        serial_mpi_field_differences = {}
        mpi_cells = self.compact()["geometry"]["axial_cells"]*self.compact()["geometry"]["radial_cells"]
        for name in reconstructed_names:
            if not (combined/mpi_final_time/name).is_file():
                continue
            first_values=internal_numeric_values(combined/mpi_final_time/name,cell_count=mpi_cells)
            second_values=internal_numeric_values(mpi_first/mpi_final_time/name,cell_count=mpi_cells)
            if len(first_values)!=len(second_values):
                raise ValueError(f"serial/MPI field length mismatch: {name}")
            serial_mpi_field_differences[name]=max(
                (relative_error(a,b) for a,b in zip(first_values,second_values)
                 if max(abs(a),abs(b))>1e-15),default=0.0)
        mpi_difference=max(mpi_species_differences.values(),default=0.0)
        mpi_balance_absolute=max(mpi_balance_differences.values(),default=0.0)
        mpi_hydraulic=max(mpi_hydraulic_differences.values(),default=0.0)
        self.gate("V13", mpi_repeat and mpi_difference<=1e-6 and
                  mpi_balance_absolute<=1e-12 and mpi_hydraulic<=1e-8 and
                  max(serial_mpi_field_differences.values(),default=0.0)<=1e-6,
                  tolerances={"species_relative":1e-6,"hydraulic_relative":1e-8,
                              "mass_residual_absolute_kg":1e-12,
                              "mpi_repeat":"byte_identity"},
                  per_species={"all_time_differences":mpi_species_differences,
                               "balance_differences_kg":mpi_balance_differences},
                  aggregate={"hydraulic_and_event_differences":mpi_hydraulic_differences,
                             "field_equality":serial_mpi_field_differences},
                  repeat_hashes=mpi_repeat_hashes, reconstructed_repeat_hashes=mpi_field_hashes,
                  maximum_serial_mpi_relative=mpi_difference,
                  balance_residual_absolute_difference_kg=mpi_balance_absolute)

        timestep = {}
        for label, dt in (("coarse",.02),("intermediate",.01),("fine",.005)):
            case=self.run(f"timestep_{label}", indexed(self.compact(end=30,dt=dt), [
                explicit("species_a", .10, rate=.12, saturation=80),
                explicit("species_b", .18, rate=.20, saturation=220)]))
            aggregate_table,species_table=self.traces(case)
            final={r["species_id"]:r for r in species_table[-2:]}
            final_dir=f"{self.compact(end=30,dt=dt)['time']['end_s']:g}"
            count=self.compact()["geometry"]["axial_cells"]*self.compact()["geometry"]["radial_cells"]
            timestep[label]={}
            for sid,row in final.items():
                values=scalar_internal_values(case/final_dir/f"dissolvedConcentration_{sid}",cell_count=count)
                timestep[label][sid]={c:float(row[c]) for c in super_cols}
                timestep[label][sid].update(
                    maximum_concentration_kg_m3=max(values),
                    volume_weighted_mean_concentration_kg_m3=sum(values)/len(values))
            aggregate_values=scalar_internal_values(case/final_dir/"dissolvedConcentration",cell_count=count)
            last_aggregate=aggregate_table[-1]
            timestep[label]["aggregate"]={
                "cup_solute_mass_kg":float(last_aggregate["cup_solute_mass_kg"]),
                "remaining_extractable_mass_kg":float(last_aggregate["remaining_extractable_mass_kg"]),
                "dissolved_mass_kg":float(last_aggregate["dissolved_in_puck_mass_kg"]),
                "back_diffusion_mass_kg":float(last_aggregate["solute_backdiffusion_mass_kg"]),
                "maximum_concentration_kg_m3":max(aggregate_values),
                "volume_weighted_mean_concentration_kg_m3":sum(aggregate_values)/len(aggregate_values),
                "outlet_solute_rate_kg_s":float(last_aggregate["totalSoluteFluxKgS"]),
                "solute_balance_residual_kg":float(last_aggregate["solute_balance_residual_kg"]),
                "first_drip_s":float(last_aggregate["first_drip_s"]),
                "target_beverage_time_s":float(last_aggregate["time_to_40g_s"]),
            }
        timestep_comparisons={"coarse_fine":{},"intermediate_fine":{}}
        for comparison_name,other in (("coarse_fine","coarse"),("intermediate_fine","intermediate")):
            for sid in timestep["fine"]:
                for metric,fine_value in timestep["fine"][sid].items():
                    other_value=timestep[other][sid][metric]
                    key=f"{sid}:{metric}"
                    timestep_comparisons[comparison_name][key]={
                        "values":[other_value,fine_value],
                        "denominator_near_zero":abs(fine_value)<=1e-15,
                        "relative":relative_error(other_value,fine_value),
                        "absolute":abs(other_value-fine_value),
                    }
        mass_metrics={key:value["relative"] for group in timestep_comparisons.values()
                      for key,value in group.items() if not key.endswith(("first_drip_s","target_beverage_time_s"))}
        ts_cf=max(v["relative"] for k,v in timestep_comparisons["coarse_fine"].items()
                  if not k.endswith(("first_drip_s","target_beverage_time_s")))
        ts_if=max(v["relative"] for k,v in timestep_comparisons["intermediate_fine"].items()
                  if not k.endswith(("first_drip_s","target_beverage_time_s")))
        event_max=max(v["absolute"] for group in timestep_comparisons.values() for k,v in group.items()
                      if k.endswith(("first_drip_s","target_beverage_time_s")))
        self.gate("V14", ts_cf<=.005 and ts_if<=.0025 and event_max<=.02,
                  tolerances={"coarse_fine_relative":.005,"intermediate_fine_relative":.0025,
                              "event_time_absolute_s":.02},
                  per_species={k:v for k,v in timestep["fine"].items() if k!="aggregate"},
                  aggregate=timestep["fine"]["aggregate"],
                  coarse_fine_relative=ts_cf, intermediate_fine_relative=ts_if,
                  event_time_maximum_absolute_s=event_max,
                  comparisons=timestep_comparisons, all_values=timestep)

        v15a={}
        v15c={}
        for label,axial,radial in (("coarse",512,32),("reference",1024,32),("fine",2048,32)):
            physical=self.compact(end=30,axial=axial,radial=radial)
            base_case=self.run(f"v15a_{label}_base_legacy",physical,
                               solver_override=self.base_solver)
            candidate_case=self.run(f"v15a_{label}_candidate_legacy",physical)
            one_case=self.run(f"v15a_{label}_indexed_one",indexed(physical,[
                explicit("species_a",.28,rate=.15,saturation=180,diffusivity=1e-9)]))
            paths=(base_case/"postProcessing/wholePull/0/traces.csv",
                   candidate_case/"postProcessing/wholePull/0/traces.csv",
                   one_case/"postProcessing/wholePull/0/traces.csv")
            base_rows=rows(paths[0]); candidate_rows=rows(paths[1]); one_rows=rows(paths[2])
            route_columns=("cup_solute_mass_kg","remaining_extractable_mass_kg",
                           "dissolved_in_puck_mass_kg","solute_backdiffusion_mass_kg",
                           "solute_balance_residual_kg","min_concentration_kg_m3",
                           "max_concentration_kg_m3","totalSoluteFluxKgS")+HYDRAULIC_COLUMNS
            base_candidate={column:maximum_column_difference(base_rows,candidate_rows,column)
                            for column in route_columns}
            candidate_indexed={column:maximum_column_difference(candidate_rows,one_rows,column)
                               for column in route_columns}
            v15a[label]={"trace_hashes":[sha256(path) for path in paths],
                         "base_candidate_maximum_absolute":base_candidate,
                         "candidate_indexed_maximum_absolute":candidate_indexed,
                         "metrics":self.application_metrics(one_case)}
            flowing=indexed(physical,[explicit("species_a",.10,rate=.12,saturation=80,diffusivity=1e-9),
                                      explicit("species_b",.18,rate=.20,saturation=220,diffusivity=1e-9)])
            v15c[label]=self.application_metrics(self.run(f"v15c_{label}",flowing))
        v15a_pass=all(all(value==0.0 for value in mesh["base_candidate_maximum_absolute"].values())
                      and all(value==0.0 for value in mesh["candidate_indexed_maximum_absolute"].values())
                      for mesh in v15a.values())

        v15b={}
        v15b_scenarios={}
        for label,axial in (("coarse",64),("reference",128),("fine",256)):
            scenario=self.positive_diffusion_scenario(axial=axial)
            v15b_scenarios[label]=scenario
            v15b[label]=self.analytical_diffusion_metrics(
                self.run(f"v15b_{label}",scenario),scenario)
        radial_scenario=self.positive_diffusion_scenario(axial=128,radial=8)
        radial_metrics=self.analytical_diffusion_metrics(
            self.run("v15b_reference_radial_double",radial_scenario),radial_scenario)
        timestep_metrics={}
        for label,axial in (("reference",128),("fine",256)):
            scenario=self.positive_diffusion_scenario(axial=axial,dt=2.5e-4)
            timestep_metrics[label]=self.analytical_diffusion_metrics(
                self.run(f"v15b_{label}_dt_half",scenario),scenario)
        v15b_orders={}
        v15b_pass=True
        primary_error_names=("l1_relative","l2_relative","maximum_concentration_relative_error",
                             "dissolved_mass_relative_error","remaining_mass_relative_error",
                             "back_diffusion_closure_relative_error","back_diffusion_flux_relative_error")
        limits={"coarse":.02,"reference":.0075,"fine":.0025}
        timestep_contamination={}
        for sid in ("species_a","species_b"):
            v15b_orders[sid]={}
            for metric in primary_error_names:
                sequence=[v15b[label][sid][metric] for label in ("coarse","reference","fine")]
                v15b_orders[sid][metric]=[
                    observed_order(sequence[0],sequence[1]),
                    observed_order(sequence[1],sequence[2])]
                v15b_pass &= all(sequence[i]<=limits[label] for i,label in enumerate(
                    ("coarse","reference","fine"))) and sequence[0]>sequence[1]>sequence[2]
            for label in ("coarse","reference","fine"):
                item=v15b[label][sid]
                v15b_pass &= (item["oracle_remainder_relative"]<=1e-10 and
                              item["oracle_internal_closure_relative"]<=1e-10 and
                              item["production_balance_residual_kg"]<=1e-12 and
                              item["capacity_ratio"]<=1e-9)
            radial_changes={metric:relative_error(radial_metrics[sid]["actual"][metric],
                v15b["reference"][sid]["actual"][metric]) for metric in
                v15b["reference"][sid]["actual"]}
            radial_metrics[sid]["radial_relative_changes"]=radial_changes
            v15b_pass &= max(radial_changes.values())<=1e-10
            for label in ("reference","fine"):
                timestep_contamination[f"{label}:{sid}"]={}
                other_label="fine" if label=="reference" else None
                for metric in primary_error_names:
                    contribution=abs(timestep_metrics[label][sid][metric]-v15b[label][sid][metric])
                    spatial=(abs(v15b["reference"][sid][metric]-v15b["fine"][sid][metric]))
                    tolerance=limits[label]
                    timestep_contamination[f"{label}:{sid}"][metric]=contribution
                    v15b_pass &= contribution<=.1*spatial and contribution<=.1*tolerance

        v15c_comparisons={"coarse_fine":{},"reference_fine":{}}
        primary=("cup_mass_kg","remaining_mass_kg","dissolved_mass_kg",
                 "inventory_removed_mass_kg",
                 "maximum_concentration_kg_m3","volume_weighted_mean_concentration_kg_m3")
        v15c_pass=True
        for comparison_name,other,limit in (("coarse_fine","coarse",.02),
                                            ("reference_fine","reference",.0075)):
            for group in ("species","aggregate"):
                identifiers=v15c["fine"][group] if group=="species" else {"aggregate":v15c["fine"][group]}
                for sid in identifiers:
                    fine_values=v15c["fine"][group][sid] if group=="species" else v15c["fine"][group]
                    other_values=v15c[other][group][sid] if group=="species" else v15c[other][group]
                    for metric in primary:
                        key=f"{group}:{sid}:{metric}"
                        difference=relative_error(other_values[metric],fine_values[metric])
                        v15c_comparisons[comparison_name][key]=difference
                        v15c_pass &= difference<=limit
        boundary_conditions={}
        for label in ("coarse","reference","fine"):
            for sid,item in v15c[label]["species"].items():
                boundary_conditions[f"{label}:{sid}"]=item["back_diffusion_mass_kg"]/item["initial_mass_kg"]
                v15c_pass &= boundary_conditions[f"{label}:{sid}"]<=.01
                v15c_pass &= abs(item["balance_residual_kg"])<=1e-12
        boundary_reference_fine={}
        for sid in v15c["fine"]["species"]:
            initial=v15c["fine"]["species"][sid]["initial_mass_kg"]
            boundary_reference_fine[sid]=abs(
                v15c["reference"]["species"][sid]["back_diffusion_mass_kg"]-
                v15c["fine"]["species"][sid]["back_diffusion_mass_kg"])/initial
            v15c_pass &= boundary_reference_fine[sid]<=.001
        subgates={
            "V15A":{"status":"PASS" if v15a_pass else "FAIL","routes":v15a},
            "V15B":{"status":"PASS" if v15b_pass else "FAIL","analytical":v15b,
                    "orders":v15b_orders,"radial_double":radial_metrics,
                    "timestep_contamination":timestep_contamination},
            "V15C":{"status":"PASS" if v15c_pass else "FAIL","application":v15c,
                    "comparisons":v15c_comparisons,"boundary_fractions":boundary_conditions,
                    "reference_fine_inventory_normalized":boundary_reference_fine,
                    "classification":"INHERITED_LEGACY_INLET_BACK_DIFFUSION_MESH_SENSITIVITY"},
        }
        self.gate("V15",v15a_pass and v15b_pass and v15c_pass,
                  tolerances=json.loads(CONTRACT_PATH.read_text())["v15"],
                  per_species={"V15B":v15b,"V15C":v15c},
                  aggregate={"classification":"INHERITED_LEGACY_INLET_DIFFUSIVE_BOUNDARY_SENSITIVITY"},
                  subgates=subgates)

        hydraulic_diff={c:maximum_column_difference(legacy_rows,one_rows,c)
                        for c in HYDRAULIC_COLUMNS}
        hydraulic_fields=("p","saturation","wetMask","U","darcyFlux","porosity",
                          "permeability","hydraulicMobility","permeabilityZoneId")
        hydraulic_field_equal={name:canonical_sha256(legacy/final_time/name)==
            canonical_sha256(one/final_time/name) for name in hydraulic_fields}
        mechanics=self.compact(end=.1,dt=.02)
        mechanics["bedMechanicsModel"]="waszkiewiczQuasiStaticCompaction"
        mechanics["poroelasticCompaction"]={
            "model":"waszkiewicz2025FinitePhi","stressFreePorosity":0.4,
            "criticalCompactionPressurePa":1239155,
            "stressFreePermeabilityM2":4.74023506749502e-15,
            "nonlinearRelativeTolerance":1e-10,"nonlinearAbsoluteTolerance":1e-10,
            "nonlinearMaximumIterations":100,"nonlinearUnderRelaxation":0.7,
            "machineFluxRelativeTolerance":1e-6}
        mechanics_legacy=self.run("v16_mechanics_legacy",mechanics)
        mechanics_indexed=self.run("v16_mechanics_indexed",indexed(mechanics,[
            explicit("species_a",.28,rate=.15,saturation=180,diffusivity=1e-9)]))
        mechanics_aggregate, _=self.traces(mechanics_indexed)
        mechanics_legacy_rows=rows(mechanics_legacy/"postProcessing/wholePull/0/traces.csv")
        mechanics_diff={column:maximum_column_difference(mechanics_legacy_rows,
            mechanics_aggregate,column) for column in HYDRAULIC_COLUMNS}
        mechanics_time=f"{mechanics['time']['end_s']:g}"
        mechanics_fields={name:canonical_sha256(mechanics_legacy/mechanics_time/name)==
            canonical_sha256(mechanics_indexed/mechanics_time/name) for name in hydraulic_fields}
        not_applicable={
            "effective_stress_field":"not a written production field; active mechanics is directly covered by porosity/permeability fields and all stress/compaction trace outputs",
            "mechanical_porosity_field":"mechanical porosity is the active porosity field in the mechanics case",
            "compaction_permeability_ratio_field":"ratio is exposed by minimumPermeabilityRatio trace; permeability field is compared directly",
        }
        v16_pass=(max(hydraulic_diff.values())==0.0 and all(hydraulic_field_equal.values()) and
                  max(mechanics_diff.values())==0.0 and all(mechanics_fields.values()))
        self.gate("V16",v16_pass,tolerances={"fields":"canonical_byte_identity",
                  "traces":"exact_serialized_equality"},
                  aggregate={"base_case_trace_differences":hydraulic_diff,
                             "base_case_fields":hydraulic_field_equal,
                             "active_mechanics_trace_differences":mechanics_diff,
                             "active_mechanics_fields":mechanics_fields,
                             "contract_approved_not_applicable":not_applicable},
                  maximum_absolute_differences=hydraulic_diff)
        rejection_results = {}
        collision = {
            "generated_field_name_collision", "generated_trace_name_collision",
            "aggregate_field_collision", "duplicate_rendered_dictionary_key",
        }
        for category in REJECTION_CATEGORIES:
            class_name = ("R1GeneratedCollisionRejectionTests" if category in collision
                          else "R1IndividualParserRejectionTests")
            method = (f"test_{category}" if category in collision
                      else f"test_reject_{category}")
            completed = subprocess.run([
                sys.executable, "-m", "unittest",
                f"tests.test_sci_md_004_stage_c.{class_name}.{method}",
            ], cwd=ROOT, text=True, capture_output=True)
            rejection_results[category] = "PASS" if completed.returncode == 0 else "FAIL"
        self.gate("V17", all(value == "PASS" for value in rejection_results.values()),
                  tolerances={"required_result": "PASS for every named category"},
                  categories=rejection_results)
        rendered=prepare_case.render_properties(indexed(self.compact(), [
            explicit("species_b",.14),explicit("species_a",.14)]))
        ordering=rendered.index("species_b") < rendered.index("species_a")
        self.gate("V18", ordering, declared_order_preserved=ordering)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--solver", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--base-solver", type=Path, required=True)
    parser.add_argument("--expected-base-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args=parser.parse_args()
    solver=args.solver.resolve(); output=args.output.resolve()
    if not solver.is_file() or sha256(solver)!=args.expected_sha256:
        raise SystemExit("solver executable hash mismatch")
    base_solver=args.base_solver.resolve()
    if not base_solver.is_file() or sha256(base_solver)!=args.expected_base_sha256:
        raise SystemExit("base solver executable hash mismatch")
    if ROOT in output.parents or output==ROOT:
        raise SystemExit("verification output must remain outside the repository")
    if output.exists():
        raise SystemExit(f"refusing existing verification output: {output}")
    output.mkdir(parents=True)
    matrix=Matrix(solver,output,base_solver)
    matrix.execute()
    result={"schema_version":"ewp.sci_md_004.stage_c.r1.runtime_matrix.v2",
            "executable_sha256":args.expected_sha256,
            "base_executable_sha256":args.expected_base_sha256,
            "contract_sha256":sha256(CONTRACT_PATH),
            "matrix_scope":"fresh fail-closed V1-V18 R1 matrix including V15A/V15B/V15C",
            "gates":matrix.results}
    defects=validate_complete_result(result)
    passed=not defects and all(g["status"]=="PASS" for g in matrix.results.values())
    result["completeness_defects"]=defects
    result["status"]="PASS" if passed else "FAIL"
    (output/"result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True,indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
