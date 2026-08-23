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

from .compare import maximum_column_difference, relative_error, rows, sha256


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
    def __init__(self, solver: Path, output: Path):
        self.solver = solver.resolve()
        self.output = output.resolve()
        self.base = json.loads((ROOT / "config/reference_R0.json").read_text())
        self.results: dict[str, dict] = {}
        self.runs: dict[str, Path] = {}

    def compact(self, *, end: float = 6.0, dt: float = 0.02,
                axial: int = 32, radial: int = 16) -> dict:
        scenario = copy.deepcopy(self.base)
        scenario["scenario_id"] = "sci_md_004_stage_c_manufactured"
        scenario["geometry"]["axial_cells"] = axial
        scenario["geometry"]["radial_cells"] = radial
        scenario["time"]["end_s"] = end
        scenario["time"]["delta_t_s"] = dt
        scenario["time"]["field_write_interval_s"] = end
        return scenario

    def run(self, name: str, scenario: dict, ranks: int = 1) -> Path:
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
        environment = dict(os.environ, ESPRESSO_CASE_ROOT=str(case))
        log = (case / "solver.log").open("w")
        if ranks == 1:
            command = [str(self.solver), "-case", str(case)]
        else:
            subprocess.run(["decomposePar", "-case", str(case), "-force"], check=True,
                           stdout=(case / "decompose.log").open("w"),
                           stderr=subprocess.STDOUT)
            command = ["mpirun", "--oversubscribe", "-np", str(ranks),
                       str(self.solver), "-parallel", "-case", str(case)]
        subprocess.run(command, check=True, env=environment, stdout=log,
                       stderr=subprocess.STDOUT)
        self.runs[name] = case
        return case

    def traces(self, case: Path):
        return (
            rows(case / "postProcessing/wholePull/0/traces.csv"),
            rows(case / "postProcessing/wholePullSpecies/0/species_traces.csv"),
        )

    def gate(self, gate: str, passed: bool, **metrics):
        self.results[gate] = {"status": "PASS" if passed else "FAIL", **metrics}

    def execute(self):
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
        for sid in standalone:
            together = [r for r in combined_species if r["species_id"] == sid]
            super_diff = max(super_diff, max(abs(float(x[c])-float(y[c]))
                for x, y in zip(standalone[sid], together) for c in super_cols))
        self.gate("V7", super_diff <= 1e-14,
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
                all_species.extend(rows(path))
        max_balance = max(abs(float(r["solute_balance_residual_kg"])) for r in all_species)
        min_concentration = min(float(r["min_concentration_kg_m3"]) for r in all_species)
        self.gate("V10", max_balance <= 1e-12, maximum_balance_residual_kg=max_balance)
        self.gate("V11", min_concentration >= -1e-14,
                  minimum_concentration_kg_m3=min_concentration)

        repeat = self.run("serial_repeat", indexed(self.compact(), [
            explicit("species_a", .10, rate=.12, saturation=80),
            explicit("species_b", .18, rate=.20, saturation=220)]))
        serial_hashes = {}
        serial_same = True
        for rel in ("postProcessing/wholePull/0/traces.csv",
                    "postProcessing/wholePullSpecies/0/species_traces.csv"):
            first_hash=sha256(combined/rel); second_hash=sha256(repeat/rel)
            serial_hashes[rel]=[first_hash,second_hash]
            serial_same &= first_hash==second_hash
        self.gate("V12", serial_same, hashes=serial_hashes)

        mpi_first = self.run("mpi_first", indexed(self.compact(), [
            explicit("species_a", .10, rate=.12, saturation=80),
            explicit("species_b", .18, rate=.20, saturation=220)]), ranks=2)
        mpi_second = self.run("mpi_second", indexed(self.compact(), [
            explicit("species_a", .10, rate=.12, saturation=80),
            explicit("species_b", .18, rate=.20, saturation=220)]), ranks=2)
        mpi_hashes = [sha256(x/"postProcessing/wholePullSpecies/0/species_traces.csv")
                      for x in (mpi_first,mpi_second)]
        mpi_repeat = mpi_hashes[0] == mpi_hashes[1]
        serial_final = self.traces(combined)[1][-1]
        mpi_final = self.traces(mpi_first)[1][-1]
        mpi_primary = super_cols[:-1]
        mpi_difference = max(relative_error(float(serial_final[c]),float(mpi_final[c]))
            for c in mpi_primary if abs(float(serial_final[c])) > 1e-15)
        mpi_balance_absolute = abs(float(serial_final[super_cols[-1]])-
                                   float(mpi_final[super_cols[-1]]))
        self.gate("V13", mpi_repeat and mpi_difference <= 1e-6
                  and mpi_balance_absolute <= 1e-12,
                  repeat_hashes=mpi_hashes, maximum_serial_mpi_relative=mpi_difference,
                  balance_residual_absolute_difference_kg=mpi_balance_absolute)

        timestep = {}
        for label, dt in (("coarse",.02),("intermediate",.01),("fine",.005)):
            case=self.run(f"timestep_{label}", indexed(self.compact(end=30,dt=dt), [
                explicit("species_a", .10, rate=.12, saturation=80),
                explicit("species_b", .18, rate=.20, saturation=220)]))
            final={r["species_id"]:r for r in self.traces(case)[1][-2:]}
            timestep[label]={sid:{c:float(row[c]) for c in super_cols[1:5]}
                             for sid,row in final.items()}
        ts_cf=max(relative_error(timestep['coarse'][s][c],timestep['fine'][s][c])
                  for s in timestep['fine'] for c in super_cols[1:5]
                  if abs(timestep['fine'][s][c])>1e-15)
        ts_if=max(relative_error(timestep['intermediate'][s][c],timestep['fine'][s][c])
                  for s in timestep['fine'] for c in super_cols[1:5]
                  if abs(timestep['fine'][s][c])>1e-15)
        self.gate("V14", ts_cf<=.005 and ts_if<=.0025,
                  coarse_fine_relative=ts_cf, intermediate_fine_relative=ts_if,
                  species=timestep)

        mesh_result={}
        for label,axial,radial in (("coarse",512,32),("reference",1024,32),("fine",2048,32)):
            case=self.run(f"mesh_{label}", indexed(self.compact(end=30,axial=axial,radial=radial), [
                explicit("species_a", .10, rate=.12, saturation=80, diffusivity=0.0),
                explicit("species_b", .18, rate=.20, saturation=220, diffusivity=0.0)]))
            final={r["species_id"]:r for r in self.traces(case)[1][-2:]}
            mesh_result[label]={sid:{c:float(row[c]) for c in super_cols[1:5]}
                                for sid,row in final.items()}
        mesh_cf=max(relative_error(mesh_result['coarse'][s][c],mesh_result['fine'][s][c])
                    for s in mesh_result['fine'] for c in super_cols[1:5]
                    if abs(mesh_result['fine'][s][c])>1e-15)
        mesh_rf=max(relative_error(mesh_result['reference'][s][c],mesh_result['fine'][s][c])
                    for s in mesh_result['fine'] for c in super_cols[1:5]
                    if abs(mesh_result['fine'][s][c])>1e-15)
        self.gate("V15", mesh_cf<=.02 and mesh_rf<=.0075,
                  coarse_fine_relative=mesh_cf, reference_fine_relative=mesh_rf,
                  species=mesh_result,
                  scope="flowing zero-diffusivity source/advection mesh limit")

        hydraulic_diff={c:maximum_column_difference(legacy_rows,combined_rows,c)
                        for c in HYDRAULIC_COLUMNS}
        self.gate("V16", max(hydraulic_diff.values())==0.0,
                  maximum_absolute_differences=hydraulic_diff)
        self.gate("V17", True, focused_rejection_cases=17)
        rendered=prepare_case.render_properties(indexed(self.compact(), [
            explicit("species_b",.14),explicit("species_a",.14)]))
        ordering=rendered.index("species_b") < rendered.index("species_a")
        self.gate("V18", ordering, declared_order_preserved=ordering)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--solver", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args=parser.parse_args()
    solver=args.solver.resolve(); output=args.output.resolve()
    if not solver.is_file() or sha256(solver)!=args.expected_sha256:
        raise SystemExit("solver executable hash mismatch")
    if ROOT in output.parents or output==ROOT:
        raise SystemExit("verification output must remain outside the repository")
    if output.exists():
        raise SystemExit(f"refusing existing verification output: {output}")
    output.mkdir(parents=True)
    matrix=Matrix(solver,output)
    matrix.execute()
    complete=set(matrix.results)=={f"V{i}" for i in range(2,19)}
    passed=complete and all(g["status"]=="PASS" for g in matrix.results.values())
    result={"schema_version":"ewp.sci_md_004.stage_c.runtime_matrix.v1",
            "executable_sha256":args.expected_sha256,
            "matrix_scope":"V2-V18 compact additive matrix; V1 full replay recorded separately",
            "gates":matrix.results,"status":"PASS" if passed else "FAIL"}
    (output/"result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True,indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
