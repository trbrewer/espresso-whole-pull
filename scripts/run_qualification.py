#!/usr/bin/env python3
"""Run and aggregate the WP-0.1H mesh/time-step/rank qualification matrix."""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

PACKAGE_VERSION = "0.1.4"
STANDARD_REPORT_NAME = "ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json"
STANDARD_RUNS_CSV_NAME = "ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_RUNS_V0_1_4.csv"
SMOKE_REPORT_NAME = "ESPRESSO_WHOLE_PULL_NUMERICAL_SMOKE_V0_1_4.json"
SMOKE_RUNS_CSV_NAME = "ESPRESSO_WHOLE_PULL_NUMERICAL_SMOKE_RUNS_V0_1_4.csv"
PRIMARY_KEYS = (
    "first_drip_s",
    "outlet_flow_final_m3_s",
    "cup_water_mass_at_end_kg",
    "cup_solute_mass_at_end_kg",
    "cup_beverage_mass_at_end_kg",
    "time_to_40g_s",
    "cumulative_tds_mass_fraction",
    "extraction_yield_mass_fraction",
    "retained_water_mass_kg",
    "retained_dissolved_solute_mass_kg",
    "remaining_extractable_mass_kg",
)


class QualificationFailure(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def gate(status: bool, metric: Any, limit: str, details: str = "") -> Dict[str, Any]:
    return {
        "status": "PASS" if status else "FAIL",
        "metric": metric,
        "limit": limit,
        "details": details,
    }


def relative_error(actual: float, reference: float) -> float:
    return abs(actual - reference) / max(abs(reference), 1.0e-30)


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_mpi_launcher() -> str:
    configured = os.environ.get("MPI_LAUNCHER", "").strip()
    if configured:
        return configured
    for candidate in ("mpirun", "mpiexec"):
        found = shutil.which(candidate)
        if found:
            return found
    raise QualificationFailure("Neither mpirun nor mpiexec was found")


def stream_command(
    command: Sequence[str],
    cwd: Path,
    log_path: Path,
    environment: Dict[str, str],
    label: str,
) -> Dict[str, Any]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"\n=== {label} ===", flush=True)
    print("$ " + " ".join(command), flush=True)
    start = time.perf_counter()
    start_utc = utc_now()
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            list(command),
            cwd=str(cwd),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            log.write(line)
        code = process.wait()
    duration = time.perf_counter() - start
    result = {
        "label": label,
        "command": list(command),
        "cwd": str(cwd),
        "log": str(log_path),
        "log_sha256": sha256(log_path),
        "start_utc": start_utc,
        "end_utc": utc_now(),
        "duration_s": duration,
        "exit_code": code,
        "status": "PASS" if code == 0 else "FAIL",
    }
    if code != 0:
        raise QualificationFailure(
            f"Stage {label!r} failed with exit code {code}; inspect {log_path}"
        )
    return result


def run_definition(
    run_id: str,
    kind: str,
    axial_cells: int,
    radial_cells: int,
    delta_t_s: float,
    ranks: int,
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "kind": kind,
        "axial_cells": axial_cells,
        "radial_cells": radial_cells,
        "delta_t_s": delta_t_s,
        "ranks": ranks,
    }


def matrix(profile: str) -> List[Dict[str, Any]]:
    if profile == "smoke":
        return [
            run_definition("smoke_reference", "reference", 64, 128, 0.05, 1),
            run_definition("smoke_layered_serial", "layered", 32, 64, 0.02, 1),
        ]
    return [
        run_definition("dt_0p020_ref_r32", "reference", 256, 512, 0.020, 32),
        run_definition("dt_0p010_ref_r32", "reference", 256, 512, 0.010, 32),
        run_definition("dt_0p005_ref_r32", "reference", 256, 512, 0.005, 32),
        run_definition("mesh_128x256_dt0p010_r16", "reference", 128, 256, 0.010, 16),
        run_definition("mesh_512x1024_dt0p010_r64", "reference", 512, 1024, 0.010, 64),
        run_definition("rank_1_ref_dt0p010", "reference", 256, 512, 0.010, 1),
        run_definition("rank_16_ref_dt0p010", "reference", 256, 512, 0.010, 16),
        run_definition("rank_64_ref_dt0p010", "reference", 256, 512, 0.010, 64),
        run_definition("layered_rank_1", "layered", 64, 128, 0.020, 1),
        run_definition("layered_rank_16", "layered", 64, 128, 0.020, 16),
    ]


def make_config(base: Dict[str, Any], definition: Dict[str, Any]) -> Dict[str, Any]:
    cfg = copy.deepcopy(base)
    cfg["scenario_id"] = f"{base['scenario_id']}__qualification__{definition['run_id']}"
    cfg["geometry"]["axial_cells"] = definition["axial_cells"]
    cfg["geometry"]["radial_cells"] = definition["radial_cells"]
    cfg["time"]["delta_t_s"] = definition["delta_t_s"]
    cfg["parallel"]["default_subdomains"] = definition["ranks"]
    cfg["time"]["field_write_interval_s"] = cfg["time"]["end_s"]
    cfg["qualification"] = {
        "run_id": definition["run_id"],
        "profile_role": definition["kind"],
    }
    depth = float(cfg["coffee_bed"]["bed_depth_m"])
    dx = depth / int(cfg["geometry"]["axial_cells"])
    cfg.setdefault("verification", {})["pressure_probes"] = [
        {
            "name": "quarter_depth",
            "position_m": 0.25 * depth,
            "half_width_m": 0.51 * dx,
        },
        {
            "name": "three_quarter_depth",
            "position_m": 0.75 * depth,
            "half_width_m": 0.51 * dx,
        },
    ]
    return cfg


def run_one(
    root: Path,
    runs_root: Path,
    definition: Dict[str, Any],
    base_reference: Dict[str, Any],
    base_layered: Dict[str, Any],
    mpi_launcher: str,
    mpi_extra: List[str],
    solver_executable: str,
) -> Dict[str, Any]:
    run_id = definition["run_id"]
    run_root = runs_root / run_id
    if run_root.exists():
        shutil.rmtree(run_root)
    run_root.mkdir(parents=True)
    config_path = run_root / "scenario.json"
    base = base_reference if definition["kind"] == "reference" else base_layered
    cfg = make_config(base, definition)
    config_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    case = run_root / "case"
    environment = dict(os.environ)
    environment["ESPRESSO_CASE_ROOT"] = str(case)
    stages: List[Dict[str, Any]] = []

    def execute(label: str, command: Sequence[str], cwd: Path) -> None:
        stages.append(
            stream_command(
                command,
                cwd,
                run_root / f"log.{label}",
                environment,
                f"{run_id}: {label}",
            )
        )

    execute(
        "prepareCase",
        [
            sys.executable,
            str(root / "scripts/prepare_case.py"),
            "--root",
            str(root),
            "--nprocs",
            str(definition["ranks"]),
            "--config",
            str(config_path),
            "--case-dir",
            str(case),
        ],
        root,
    )
    execute("blockMesh", ["blockMesh"], case)
    execute("checkMesh", ["checkMesh", "-allGeometry", "-allTopology"], case)
    if definition["ranks"] == 1:
        execute("solver", [solver_executable], case)
    else:
        execute("decomposePar", ["decomposePar", "-force"], case)
        execute(
            "solver",
            [
                mpi_launcher,
                *mpi_extra,
                "-np",
                str(definition["ranks"]),
                solver_executable,
                "-parallel",
            ],
            case,
        )
        execute("reconstructPar", ["reconstructPar", "-latestTime"], case)
        for processor in case.glob("processor*"):
            if processor.is_dir():
                shutil.rmtree(processor)

    if definition["kind"] == "reference":
        execute(
            "postprocess",
            [
                sys.executable,
                str(root / "scripts/postprocess.py"),
                "--root",
                str(root),
                "--config",
                str(config_path),
                "--case-dir",
                str(case),
            ],
            root,
        )
        acceptance_path = case / "ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json"
    else:
        execute(
            "postprocess",
            [
                sys.executable,
                str(root / "scripts/postprocess_layered_fixture.py"),
                "--root",
                str(root),
                "--config",
                str(config_path),
                "--case-dir",
                str(case),
            ],
            root,
        )
        acceptance_path = case / "ESPRESSO_LAYERED_PRESSURE_FIXTURE_ACCEPTANCE_V0_1_4.json"

    acceptance = load_json(acceptance_path)
    if acceptance.get("status") != "PASS":
        raise QualificationFailure(f"Acceptance failed for {run_id}")
    total_duration = sum(float(stage["duration_s"]) for stage in stages)
    solver_duration = next(
        (float(stage["duration_s"]) for stage in stages if str(stage.get("label", "")).endswith(": solver")),
        None,
    )
    return {
        **definition,
        "status": "PASS",
        "case": str(case.relative_to(root)),
        "config": str(config_path.relative_to(root)),
        "acceptance": str(acceptance_path.relative_to(root)),
        "acceptance_sha256": sha256(acceptance_path),
        "primary_outputs": acceptance.get("primary_outputs", {}),
        "acceptance_summary": {
            "all_required_numerical_gates_pass": acceptance.get(
                "all_required_numerical_gates_pass"
            ),
            "all_required_b0_parity_gates_pass": acceptance.get(
                "all_required_b0_parity_gates_pass"
            ),
            "all_required_gates_pass": acceptance.get("all_required_gates_pass"),
        },
        "total_stage_duration_s": total_duration,
        "solver_stage_duration_s": solver_duration,
        "stages": stages,
    }


def compare_outputs(
    current: Dict[str, Any],
    reference: Dict[str, Any],
    keys: Iterable[str],
    relative_tolerance: float,
    first_drip_absolute_tolerance: float = 1.0e-8,
) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}
    passed = True
    for key in keys:
        actual = current["primary_outputs"].get(key)
        expected = reference["primary_outputs"].get(key)
        if actual is None or expected is None:
            metric = {"status": "SKIP", "actual": actual, "reference": expected}
        elif key == "first_drip_s":
            error = abs(float(actual) - float(expected))
            metric = {
                "status": "PASS" if error <= first_drip_absolute_tolerance else "FAIL",
                "actual": actual,
                "reference": expected,
                "absolute_error": error,
                "limit": first_drip_absolute_tolerance,
            }
        else:
            error = relative_error(float(actual), float(expected))
            metric = {
                "status": "PASS" if error <= relative_tolerance else "FAIL",
                "actual": actual,
                "reference": expected,
                "relative_error": error,
                "limit": relative_tolerance,
            }
        if metric["status"] == "FAIL":
            passed = False
        metrics[key] = metric
    return {"status": "PASS" if passed else "FAIL", "metrics": metrics}


def aggregate_standard(results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    convergence_keys = (
        "first_drip_s",
        "outlet_flow_final_m3_s",
        "cup_beverage_mass_at_end_kg",
        "time_to_40g_s",
        "cumulative_tds_mass_fraction",
        "extraction_yield_mass_fraction",
        "retained_dissolved_solute_mass_kg",
        "remaining_extractable_mass_kg",
    )
    gates: Dict[str, Dict[str, Any]] = {}
    all_accept = all(result.get("status") == "PASS" for result in results.values())
    gates["all_individual_runs_accepted"] = gate(
        all_accept,
        {name: result.get("status") for name, result in results.items()},
        "all matrix runs PASS their own acceptance reports",
    )

    dt_ref = results["dt_0p005_ref_r32"]
    dt20 = compare_outputs(results["dt_0p020_ref_r32"], dt_ref, convergence_keys, 0.005)
    dt10 = compare_outputs(results["dt_0p010_ref_r32"], dt_ref, convergence_keys, 0.0025)
    gates["time_step_0p020_vs_0p005"] = gate(
        dt20["status"] == "PASS", dt20["metrics"], "<=0.5% relative; first drip <=1e-8 s"
    )
    gates["time_step_0p010_vs_0p005"] = gate(
        dt10["status"] == "PASS", dt10["metrics"], "<=0.25% relative; first drip <=1e-8 s"
    )

    mesh_fine = results["mesh_512x1024_dt0p010_r64"]
    mesh_coarse = compare_outputs(
        results["mesh_128x256_dt0p010_r16"], mesh_fine, convergence_keys, 0.02
    )
    mesh_reference = compare_outputs(
        results["dt_0p010_ref_r32"], mesh_fine, convergence_keys, 0.0075
    )
    gates["mesh_coarse_vs_fine"] = gate(
        mesh_coarse["status"] == "PASS",
        mesh_coarse["metrics"],
        "<=2% relative; first drip <=1e-8 s",
    )
    gates["mesh_reference_vs_fine"] = gate(
        mesh_reference["status"] == "PASS",
        mesh_reference["metrics"],
        "<=0.75% relative; first drip <=1e-8 s",
    )

    rank_reference = results["rank_1_ref_dt0p010"]
    rank_keys = PRIMARY_KEYS
    for rank_id in (
        "rank_16_ref_dt0p010",
        "dt_0p010_ref_r32",
        "rank_64_ref_dt0p010",
    ):
        comparison = compare_outputs(
            results[rank_id], rank_reference, rank_keys, 1.0e-6, 1.0e-10
        )
        gates[f"parallel_equivalence_{rank_id}_vs_rank1"] = gate(
            comparison["status"] == "PASS",
            comparison["metrics"],
            "<=1e-6 relative; first drip <=1e-10 s",
        )

    layered_serial = results["layered_rank_1"]
    layered_parallel = results["layered_rank_16"]
    layered_metrics: Dict[str, Any] = {}
    layered_pass = True
    for key in ("outlet_flow_m3_s", "pressure_probe_1_Pa", "pressure_probe_2_Pa"):
        actual = float(layered_parallel["primary_outputs"][key])
        expected = float(layered_serial["primary_outputs"][key])
        error = relative_error(actual, expected)
        layered_metrics[key] = {
            "actual": actual,
            "reference": expected,
            "relative_error": error,
            "limit": 1.0e-8,
            "status": "PASS" if error <= 1.0e-8 else "FAIL",
        }
        layered_pass = layered_pass and error <= 1.0e-8
    gates["layered_fixture_serial_parallel_equivalence"] = gate(
        layered_pass,
        layered_metrics,
        "<=1e-8 relative for flow and both pressure probes",
    )
    return gates


def rank_performance_summary(results: Dict[str, Dict[str, Any]], configured_default: int) -> Dict[str, Any]:
    mapping = {
        1: "rank_1_ref_dt0p010",
        16: "rank_16_ref_dt0p010",
        32: "dt_0p010_ref_r32",
        64: "rank_64_ref_dt0p010",
    }
    timings: Dict[str, Any] = {}
    serial_time: Optional[float] = None
    for ranks, run_id in mapping.items():
        result = results.get(run_id, {})
        duration = result.get("solver_stage_duration_s")
        if duration is not None:
            duration = float(duration)
            if ranks == 1:
                serial_time = duration
        timings[str(ranks)] = {
            "run_id": run_id,
            "solver_stage_duration_s": duration,
            "status": result.get("status"),
        }
    fastest_ranks = None
    fastest_time = None
    measured = [
        (int(ranks), float(item["solver_stage_duration_s"]))
        for ranks, item in timings.items()
        if item["solver_stage_duration_s"] is not None and item.get("status") == "PASS"
    ]
    if measured:
        fastest_ranks, fastest_time = min(measured, key=lambda item: item[1])
    for ranks_text, item in timings.items():
        duration = item["solver_stage_duration_s"]
        ranks = int(ranks_text)
        item["speedup_vs_1_rank"] = (
            serial_time / duration if serial_time is not None and duration not in (None, 0.0) else None
        )
        item["parallel_efficiency_vs_1_rank"] = (
            item["speedup_vs_1_rank"] / ranks
            if item["speedup_vs_1_rank"] is not None
            else None
        )
    return {
        "status": "OBSERVATION_ONLY",
        "configured_routine_default_ranks": configured_default,
        "fastest_measured_ranks": fastest_ranks,
        "fastest_solver_stage_duration_s": fastest_time,
        "timings": timings,
        "interpretation": (
            "This is a single-run operational comparison for the 131,072-cell R0 case, "
            "not a universal strong-scaling law. Numerical equivalence is gated separately."
        ),
    }


def write_runs_csv(path: Path, results: Dict[str, Dict[str, Any]]) -> None:
    columns = [
        "run_id",
        "kind",
        "axial_cells",
        "radial_cells",
        "delta_t_s",
        "ranks",
        "status",
        "total_stage_duration_s",
        "solver_stage_duration_s",
        *PRIMARY_KEYS,
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for run_id in results:
            result = results[run_id]
            row = {key: result.get(key) for key in columns}
            primary = result.get("primary_outputs", {})
            for key in PRIMARY_KEYS:
                row[key] = primary.get(key)
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--profile", choices=("standard", "smoke"), default="standard")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--runs-csv", type=Path)
    parser.add_argument("--runs-root", type=Path)
    parser.add_argument(
        "--solver-executable",
        type=Path,
        help="Absolute executable path; standard Allverify supplies the exact Allrun binary",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    qualification_dir = root / "qualification"
    qualification_dir.mkdir(parents=True, exist_ok=True)
    default_report = STANDARD_REPORT_NAME if args.profile == "standard" else SMOKE_REPORT_NAME
    default_runs_csv = STANDARD_RUNS_CSV_NAME if args.profile == "standard" else SMOKE_RUNS_CSV_NAME
    report_path = args.report or (qualification_dir / default_report)
    runs_csv_path = args.runs_csv or (qualification_dir / default_runs_csv)
    report_path = report_path if report_path.is_absolute() else root / report_path
    runs_csv_path = runs_csv_path if runs_csv_path.is_absolute() else root / runs_csv_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    runs_csv_path.parent.mkdir(parents=True, exist_ok=True)
    runs_root = args.runs_root or (root / "qualification_runs" / args.profile)
    runs_root = runs_root if runs_root.is_absolute() else root / runs_root
    if runs_root.exists():
        shutil.rmtree(runs_root)
    runs_root.mkdir(parents=True)

    definitions = matrix(args.profile)
    available = os.cpu_count() or 1
    maximum_requested = max(item["ranks"] for item in definitions)
    if maximum_requested > available and os.environ.get("ALLOW_OVERSUBSCRIBE") != "1":
        raise SystemExit(
            f"Qualification requests {maximum_requested} ranks but only {available} logical CPUs are visible"
        )

    base_reference = load_json(root / "config/reference_R0.json")
    base_layered = load_json(root / "config/fixture_layered_pressure.json")
    mpi_launcher = find_mpi_launcher()
    mpi_extra = os.environ.get("MPI_ARGS", "").split()
    if args.solver_executable is not None:
        solver_path = args.solver_executable.expanduser().resolve()
    else:
        discovered = shutil.which("espressoWholePullFoam")
        if not discovered:
            raise SystemExit("espressoWholePullFoam was not found in PATH")
        solver_path = Path(discovered).resolve()
    if not solver_path.is_file() or not os.access(solver_path, os.X_OK):
        raise SystemExit(f"Solver executable is missing or not executable: {solver_path}")
    solver_executable = str(solver_path)
    solver_executable_sha256 = sha256(solver_path)
    results: Dict[str, Dict[str, Any]] = {}
    failure: Optional[str] = None

    for definition in definitions:
        run_id = definition["run_id"]
        try:
            results[run_id] = run_one(
                root,
                runs_root,
                definition,
                base_reference,
                base_layered,
                mpi_launcher,
                mpi_extra,
                solver_executable,
            )
        except Exception as exc:
            failure = f"{type(exc).__name__}: {exc}"
            results[run_id] = {
                **definition,
                "status": "FAIL",
                "error": failure,
            }
            break

    gates: Dict[str, Dict[str, Any]] = {}
    if failure is None:
        if args.profile == "standard":
            gates = aggregate_standard(results)
        else:
            gates["smoke_cases_accepted"] = gate(
                all(result.get("status") == "PASS" for result in results.values()),
                {key: value.get("status") for key, value in results.items()},
                "all smoke cases PASS",
            )
    else:
        gates["matrix_execution_completed"] = gate(False, failure, "no run-stage failures")

    all_pass = failure is None and all(item["status"] == "PASS" for item in gates.values())
    write_runs_csv(runs_csv_path, results)
    report = {
        "schema_version": "espresso.whole_pull.numerical_qualification.v0.1.4",
        "generated_at_utc": utc_now(),
        "qualification_completed_at_utc": utc_now(),
        "package_version": PACKAGE_VERSION,
        "profile": args.profile,
        "status": "PASS" if all_pass else "FAIL",
        "execution_status": "COMPLETED" if failure is None else "FAILED",
        "all_required_gates_pass": all_pass,
        "gate_summary": {
            "pass": sum(item["status"] == "PASS" for item in gates.values()),
            "fail": sum(item["status"] == "FAIL" for item in gates.values()),
            "total": len(gates),
        },
        "gates": gates,
        "matrix": definitions,
        "runs_root": str(runs_root.relative_to(root)),
        "runs": results,
        "failure": failure,
        "performance_observations": (
            rank_performance_summary(
                results,
                int(base_reference.get("parallel", {}).get("default_subdomains", 32)),
            )
            if args.profile == "standard" and failure is None
            else None
        ),
        "environment": {
            "available_logical_cpus": available,
            "mpi_launcher": mpi_launcher,
            "mpi_args": mpi_extra,
            "wm_project": os.environ.get("WM_PROJECT"),
            "wm_project_version": os.environ.get("WM_PROJECT_VERSION"),
            "wm_options": os.environ.get("WM_OPTIONS"),
            "solver_executable": solver_executable,
            "solver_executable_bytes": solver_path.stat().st_size,
            "solver_executable_sha256": solver_executable_sha256,
        },
        "artifacts": {
            "runs_csv": {
                "path": str(runs_csv_path.relative_to(root)),
                "bytes": runs_csv_path.stat().st_size,
                "sha256": sha256(runs_csv_path),
            }
        },
        "claim": (
            "PASS qualifies the v0.1.4 implementation numerically across the declared "
            "time-step, mesh, decomposition, layered-pressure, analytical, and B0 gates. "
            "It does not establish physical validation."
        ),
    }
    temporary = report_path.with_name(report_path.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(report_path)
    print(
        json.dumps(
            {
                "status": report["status"],
                "profile": args.profile,
                "qualification_report": str(report_path),
                "runs_csv": str(runs_csv_path),
                "gate_summary": report["gate_summary"],
            },
            indent=2,
        )
    )
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
